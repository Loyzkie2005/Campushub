"""Existing Job Order signing, private images, and a mobile-owner-only WebView handoff."""
import base64
from copy import deepcopy
from hashlib import sha256
from hmac import compare_digest
import secrets
import time

from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from api.models import CampusHubUser
from api.views import _mobile_user_from_bearer
from .admin_booking_views import payload
from .booking_workflow_views import physical_bookings, read_access, pdf_response
from .services.booking_workflow import save_details
from .services.job_order import ensure_job_order_draft, job_order_available, job_order_data
from .services.job_order_signatures import locked_booking, sign_or_prepare, status_data, MAX_AGE
from .services.schedules import metadata

COOKIE = 'campushub_job_order'
HANDOFF_SALT = 'campushub.job-order.handoff.v1'
OWNER_SALT = 'campushub.job-order.owner.v1'


def private(response):
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Referrer-Policy'] = 'no-referrer'
    response['Vary'] = 'Cookie, X-Admin-Tab-Token'
    return response


def result_error(error):
    return private(JsonResponse({'error': error.messages[0] if isinstance(error, ValidationError) else str(error)},
                                status=403 if isinstance(error, PermissionDenied) else 400))


@require_POST
def admin_sign(request, booking_id):
    denied = read_access(request)
    if denied is not None:
        return denied
    booking = get_object_or_404(physical_bookings(), pk=booking_id)
    try:
        return private(JsonResponse(sign_or_prepare(request, booking, payload(request), request.user)))
    except (ValidationError, PermissionDenied) as error:
        return result_error(error)
    except ValueError:
        return result_error(ValidationError('Send valid signing details.'))


def signature_response(booking, section):
    record = ((metadata(booking).get('job_order') or {}).get('signatures') or {}).get(section)
    if not record:
        from django.http import Http404
        raise Http404('Signature not found.')
    response = HttpResponse(base64.b64decode(record['attachment']['data'], validate=True), content_type='image/png')
    response['Content-Disposition'] = 'inline; filename="job-order-signature.png"'
    return private(response)


@require_GET
def admin_image(request, booking_id, section):
    denied = read_access(request)
    if denied is not None:
        return denied
    return signature_response(get_object_or_404(physical_bookings(), pk=booking_id), section)


def owner(request, booking_id):
    """This cookie grants only one client's one Job Order, never administrator access."""
    try:
        token = request.COOKIES.get(COOKIE, '')
        proof = signing.loads(token, salt=OWNER_SALT, max_age=MAX_AGE)
        if proof.get('booking') != booking_id or proof.get('expires', 0) <= time.time():
            raise signing.BadSignature
        user = CampusHubUser.objects.get(pk=proof['client'], is_active=True, is_suspended=False)
        booking = get_object_or_404(physical_bookings(), pk=booking_id, user=user)
        job = metadata(booking).get('job_order') or {}
        saved = job.get('_signing_private', {}).get('owner_session', '')
        if (not saved or not compare_digest(saved, sha256(token.encode()).hexdigest())
                or not job_order_available(booking) or booking.status not in ('approved', 'completed')):
            raise signing.BadSignature
        return booking, user
    except (signing.BadSignature, CampusHubUser.DoesNotExist, KeyError, TypeError, ValueError):
        raise PermissionDenied('Your Job Order session expired. Open it again from the mobile app.')


@csrf_exempt
@require_POST
def mobile_handoff(request, booking_id):
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    booking = get_object_or_404(physical_bookings(), pk=booking_id, user=user)
    ensure_job_order_draft(booking)
    if not job_order_available(booking) or booking.status not in ('approved', 'completed'):
        return private(JsonResponse({'error': 'The Job Order is available after approval.'}, status=409))
    with locked_booking(booking) as locked:
        if locked.status not in ('approved', 'completed') or not job_order_available(locked):
            return private(JsonResponse({'error': 'The Job Order is not available in this booking state.'}, status=409))
        expires = min(time.time() + MAX_AGE, request.mobile_auth_claims['exp'])
        grant = signing.dumps({'booking': booking_id, 'client': user.pk,
                              'expires': expires, 'nonce': secrets.token_urlsafe(32)}, salt=HANDOFF_SALT)
        details = deepcopy(metadata(locked))
        details['job_order'].setdefault('_signing_private', {})['handoff'] = sha256(grant.encode()).hexdigest()
        save_details(locked, details)
    return private(JsonResponse({'url': f'/api/mobile/bookings/{booking_id}/job-order/view/', 'handoff': grant}))


def exchange_handoff(request, booking_id):
    grant = request.headers.get('X-Job-Order-Handoff', '')
    try:
        proof = signing.loads(grant, salt=HANDOFF_SALT, max_age=60)
        if proof.get('booking') != booking_id or proof.get('expires', 0) <= time.time():
            raise signing.BadSignature
        user = CampusHubUser.objects.get(pk=proof['client'], is_active=True, is_suspended=False)
        booking = get_object_or_404(physical_bookings(), pk=booking_id, user=user)
        with locked_booking(booking) as locked:
            if locked.status not in ('approved', 'completed') or not job_order_available(locked):
                raise signing.BadSignature
            details = deepcopy(metadata(locked))
            secret = details.get('job_order', {}).get('_signing_private', {})
            if not compare_digest(secret.get('handoff', ''), sha256(grant.encode()).hexdigest()):
                raise signing.BadSignature
            secret.pop('handoff', None)
            token = signing.dumps({**proof, 'nonce': secrets.token_urlsafe(32)}, salt=OWNER_SALT)
            secret['owner_session'] = sha256(token.encode()).hexdigest()
            save_details(locked, details)
        return token
    except (signing.BadSignature, CampusHubUser.DoesNotExist, KeyError, TypeError, ValueError):
        raise PermissionDenied('This mobile signing link is invalid or expired. Open the Job Order again.')


@require_GET
@ensure_csrf_cookie
def mobile_view(request, booking_id):
    try:
        token = None
        try:
            booking, user = owner(request, booking_id)
        except PermissionDenied:
            if not request.headers.get('X-Job-Order-Handoff'):
                raise
            token = exchange_handoff(request, booking_id)
            request.COOKIES[COOKIE] = token
            booking, user = owner(request, booking_id)
        prefix = f'/api/mobile/bookings/{booking_id}/job-order/'
        status = status_data(booking, user, 'mobile')
        for row in status['sections']:
            row['image_url'] = prefix + 'signatures/' + row['section'] + '/' if row['signed'] else ''
        status['endpoint'] = prefix + 'sign/'
        response = private(render(request, 'facilities/pages/job_order.html', {
            'preview_url': prefix + 'document/?format=pdf&inline=1',
            'pdf_url': prefix + 'document/?format=pdf', 'docx_url': prefix + 'document/?format=docx',
            'job_order_signing': status, 'mobile_job_order': True}))
        if token:
            response.set_cookie(COOKIE, token, max_age=MAX_AGE, httponly=True,
                secure=not settings.DEBUG or request.is_secure(), samesite='Strict', path=prefix)
        return response
    except PermissionDenied as error:
        return result_error(error)


@require_POST
def mobile_sign(request, booking_id):
    try:
        booking, user = owner(request, booking_id)
        return private(JsonResponse(sign_or_prepare(request, booking, payload(request), user, 'mobile')))
    except (ValidationError, PermissionDenied) as error:
        return result_error(error)
    except ValueError:
        return result_error(ValidationError('Send valid signing details.'))


@require_GET
def mobile_image(request, booking_id, section):
    try:
        booking, _ = owner(request, booking_id)
        return signature_response(booking, section)
    except PermissionDenied as error:
        return result_error(error)


@require_GET
def mobile_document(request, booking_id):
    try:
        booking, _ = owner(request, booking_id)
        data = job_order_data(booking)
        if request.GET.get('format') == 'docx':
            from .services.job_order_docx import job_order_docx
            response = HttpResponse(job_order_docx(data), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename="{booking_id}-job-order.docx"'
        else:
            response = pdf_response('Job Order Request', [], booking_id + '-job-order', job_order=data)
            if request.GET.get('inline') == '1':
                response['Content-Disposition'] = f'inline; filename="{booking_id}-job-order.pdf"'
        return private(response)
    except PermissionDenied as error:
        return result_error(error)
    except Exception as error:
        from .services.booking_slip_pdf import BookingSlipPDFError
        if not isinstance(error, BookingSlipPDFError):
            raise
        return private(JsonResponse({'error': str(error)}, status=503))
