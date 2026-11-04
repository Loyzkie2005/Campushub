"""Document-bound signatures in the existing private booking JSON, never public media."""
import base64
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from hmac import compare_digest
from io import BytesIO
import json
import secrets
import warnings

from PIL import Image, ImageChops
from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

from accounts.activity_logging import log_account_activity
from accounts.models import AccountActivity, User
from api.models import Booking, Facility
from .booking_workflow import READ_PERMISSIONS, has_permission, save_details
from .schedules import metadata

SECTIONS = (
    ('filled_out_by', 'Filled-out by', 'Client'),
    ('assisted_by', 'Assisted by', 'Administrative Aide'),
    ('verified_by', 'Verified by', 'Personnel In-Charge'),
    ('approved_by', 'Approved by', 'BEU Manager'),
)
SALT = 'campushub.job-order.signature.v1'
MAX_AGE = 300


@contextmanager
def locked_booking(booking):
    """Keep the existing Facility -> Booking serialization order for every writer."""
    with transaction.atomic():
        if booking.facility_id:
            Facility.objects.select_for_update().get(pk=booking.facility_id)
        locked = Booking.objects.select_for_update(of=('self',)).select_related('facility', 'user').get(pk=booking.pk)
        yield locked


def paper_data(booking):
    from .job_order import current_job_order_data
    job = metadata(booking).get('job_order') or {}
    return deepcopy(job.get('signed_snapshot') or current_job_order_data(booking))


def template_bytes(job):
    from .job_order_docx import TEMPLATE
    saved = job.get('template_attachment')
    return base64.b64decode(saved['data'], validate=True) if saved else TEMPLATE.read_bytes()


def revision_hash(booking, *, paper=None, template=None):
    job = metadata(booking).get('job_order') or {}
    content = {'booking': str(booking.pk), 'revision': job.get('revision', 1),
               'paper': paper_data(booking) if paper is None else paper,
               'template': sha256(template_bytes(job) if template is None else template).hexdigest()}
    return sha256(json.dumps(content, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def document_data(booking, current):
    """A signed paper uses its frozen fields and original template, not a live profile."""
    job = metadata(booking).get('job_order') or {}
    result = deepcopy(job.get('signed_snapshot') or current)
    result['signatures'] = deepcopy(job.get('signatures') or {})
    if job.get('template_attachment'):
        result['_template_bytes'] = template_bytes(job)
    return result


def assigned_admin(section):
    if section not in ('assisted_by', 'verified_by', 'approved_by'):
        return None
    roster = getattr(settings, 'JOB_ORDER_SIGNERS', {})
    if not isinstance(roster, dict):
        return None
    name = roster.get(section)
    # A configuration typo must never silently combine distinct office sign-offs.
    if not isinstance(name, str) or not name or list(roster.values()).count(name) != 1:
        return None
    user = User.objects.filter(username=name, is_active=True, is_suspended=False).first()
    return user if user and any(has_permission(user, code) for code in READ_PERMISSIONS) else None


def can_sign(booking, section, user, source):
    job = metadata(booking).get('job_order') or {}
    if (not isinstance(section, str) or booking.status != Booking.STATUS_APPROVED or not job
            or section not in dict((key, label) for key, label, _ in SECTIONS)
            or (job.get('signatures') or {}).get(section)):
        return False
    if source == 'mobile':
        permitted = (section == 'filled_out_by' and booking.user_id == user.pk
                     and user.is_active and not user.is_suspended)
    else:
        assigned = assigned_admin(section)
        permitted = source == 'admin' and assigned is not None and assigned.pk == user.pk
    if not permitted:
        return False
    if getattr(settings, 'JOB_ORDER_SIGNATURE_SEQUENCE', True):
        previous = [key for key, _, _ in SECTIONS][:next(i for i, item in enumerate(SECTIONS) if item[0] == section)]
        return all((job.get('signatures') or {}).get(key) for key in previous)
    return True


def status_data(booking, user, source='admin'):
    job = metadata(booking).get('job_order') or {}
    rows = []
    for index, (key, label, role) in enumerate(SECTIONS):
        signed = (job.get('signatures') or {}).get(key) or {}
        assigned = booking.user if key == 'filled_out_by' else assigned_admin(key)
        name = signed.get('name') or ((f'{assigned.first_name} {assigned.last_name}'.strip() or assigned.username) if assigned else '')
        current_signer = bool(assigned and assigned.pk == user.pk and (
            source == 'mobile' and key == 'filled_out_by' or source == 'admin' and key != 'filled_out_by'))
        eligible = can_sign(booking, key, user, source)
        reason = ''
        if not signed and not eligible:
            if booking.status != Booking.STATUS_APPROVED:
                reason = 'New signatures are available only while this booking is approved.'
            elif not assigned:
                reason = 'No client account is linked to this booking.' if key == 'filled_out_by' else f'No {role} signer has been assigned.'
            elif current_signer:
                pending = next((previous_role for previous_key, _, previous_role in SECTIONS[:index]
                    if not (job.get('signatures') or {}).get(previous_key)), None)
                reason = f'Waiting for the {pending} signature.' if pending else 'Signing is not available for this account.'
            else:
                reason = f'Only the assigned {role} may sign this section.'
        rows.append({'section': key, 'label': label, 'role': role, 'name': name,
                     'signed': bool(signed), 'at': signed.get('at', ''),
                     'can_sign': eligible, 'is_current_signer': current_signer,
                     'blocked_reason': reason,
                     'image_url': f'/api/bookings/{booking.pk}/job-order/signatures/{key}/' if signed else '',
                     'assigned': bool(assigned)})
    signed_count = sum(item['signed'] for item in rows)
    mine = [row for row in rows if row['is_current_signer']]
    notice = ''
    client_hint = ('A client account must first be linked to this booking.' if not booking.user else
        'The linked client account must be active before the client can sign.'
        if not booking.user.is_active or booking.user.is_suspended else
        'The client signs in Flutter: Bookings > Booking Details > View Job Order Request.')
    if signed_count < 4 and not any(row['can_sign'] for row in rows):
        if booking.status != Booking.STATUS_APPROVED:
            notice = 'This booking is read-only for new Job Order signatures.'
        elif any(not row['signed'] for row in mine):
            notice = next(row['blocked_reason'] for row in mine if not row['signed'])
            if not rows[0]['signed'] and source == 'admin':
                notice += ' ' + client_hint
        elif mine:
            notice = 'Your sign-off is recorded. Waiting for the remaining signers.'
        else:
            notice = ('Staff signing accounts have not been assigned.' if not any(row['assigned'] for row in rows[1:])
                      else 'This account is not assigned to a staff sign-off.')
            if not rows[0]['signed']:
                notice += ' ' + client_hint
    return {'revision': job.get('revision', 1), 'sections': rows,
            'signed_count': signed_count, 'notice': notice}


def validated_png(value):
    """Decode, bound, inspect ink, and re-encode PNG; client isEmpty is insufficient."""
    try:
        if not isinstance(value, str) or not value.startswith('data:image/png;base64,') or len(value) > 720000:
            raise ValueError
        raw = base64.b64decode(value.split(',', 1)[1], validate=True)
        if not raw or len(raw) > 512000:
            raise ValueError
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format != 'PNG' or not (100 <= image.width <= 2400 and 50 <= image.height <= 1200):
                    raise ValueError
                image.load()
                rgba = image.convert('RGBA')
                paper = Image.new('RGBA', rgba.size, 'white')
                paper.alpha_composite(rgba)
                ink = ImageChops.difference(paper.convert('RGB'), Image.new('RGB', rgba.size, 'white')).convert('L')
                if not ink.point(lambda p: 255 if p > 32 else 0).getbbox():
                    raise ValueError
                output = BytesIO()
                rgba.save(output, format='PNG')
        content = output.getvalue()
        if len(content) > 512000:
            raise ValueError
        return {'name': 'signature.png', 'type': 'image/png', 'data': base64.b64encode(content).decode('ascii')}
    except (ValueError, TypeError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError('Draw a non-empty signature using the signature pad.')


def sign_or_prepare(request, booking, data, user, source='admin'):
    section = data.get('section')
    with locked_booking(booking) as locked:
        if not can_sign(locked, section, user, source):
            raise PermissionDenied('You cannot sign this section in its current state.')
        details = deepcopy(metadata(locked))
        job = details['job_order']
        private = job.setdefault('_signing_private', {})
        actor_ref = f'{source}:{user.pk}'
        snapshot = paper_data(locked)
        template = template_bytes(job)
        digest = revision_hash(locked, paper=snapshot, template=template)
        if data.get('intent') == 'prepare':
            token = signing.dumps({'booking': locked.pk, 'section': section, 'actor': actor_ref,
                                   'revision': digest, 'nonce': secrets.token_urlsafe(32)}, salt=SALT)
            private.setdefault('challenges', {})[section] = sha256(token.encode()).hexdigest()
            save_details(locked, details)
            return {'challenge': token, 'revision': digest}
        if data.get('intent') != 'sign':
            raise ValidationError('Select a supported signing action.')
        token = data.get('challenge', '')
        try:
            proof = signing.loads(token, salt=SALT, max_age=MAX_AGE)
        except (signing.BadSignature, TypeError, ValueError):
            raise ValidationError('The signing request expired. Open the signature pad again.')
        expected = {'booking': locked.pk, 'section': section, 'actor': actor_ref, 'revision': digest}
        saved = private.get('challenges', {}).get(section, '')
        if any(proof.get(k) != v for k, v in expected.items()) or not compare_digest(saved, sha256(token.encode()).hexdigest()):
            raise ValidationError('The document or signing request changed. Reload and sign again.')
        attachment = validated_png(data.get('signature'))
        image_hash = sha256(base64.b64decode(attachment['data'])).hexdigest()
        # Serialize identical images across bookings without adding a schema constraint.
        if connection.vendor != 'postgresql':
            raise ValidationError('Secure Job Order signing requires PostgreSQL.')
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [int.from_bytes(bytes.fromhex(image_hash)[:8], signed=True)])
        from api.models import FacilityBookingRequest
        if FacilityBookingRequest.objects.filter(details__job_order__signature_image_hashes__contains=[image_hash]).exists():
            raise ValidationError('Draw a fresh signature for this Job Order. Saved images cannot be reused.')
        if not job.get('signed_snapshot'):
            job['signed_snapshot'] = snapshot
            job['template_attachment'] = {'name': 'job-order-template.docx', 'data': base64.b64encode(template).decode('ascii')}
        role = next(role for key, _, role in SECTIONS if key == section)
        name = f'{user.first_name} {user.last_name}'.strip() or user.username
        signed = {'actor_ref': actor_ref, 'account_id': user.pk, 'source': source, 'name': name,
                  'role': role, 'at': timezone.now().isoformat(), 'document_hash': digest,
                  'image_hash': image_hash, 'decision': 'signed', 'attachment': attachment}
        job.setdefault('signatures', {})[section] = signed
        job.setdefault('signature_image_hashes', []).append(image_hash)
        private.get('challenges', {}).pop(section, None)
        save_details(locked, details)
        log_account_activity(request, source=AccountActivity.SOURCE_MOBILE if source == 'mobile' else AccountActivity.SOURCE_ADMIN,
            account=user, module='Facility Bookings', activity_type='job_order_signed', activity='Job Order signed',
            result=AccountActivity.RESULT_SUCCESS, metadata={'booking_id': locked.pk, 'section': section,
                'signer_ref': actor_ref, 'document_hash': digest, 'image_hash': image_hash,
                'revision': job.get('revision', 1), 'designation': role, 'decision': 'signed',
                'actor_admin_id': user.pk if source == 'admin' else None})
        return {'message': 'Job Order signed successfully.'}


def reconcile_edit(booking, previous):
    """A real paper change starts a fresh revision and retains the signed original."""
    if not previous.get('signatures'):
        return
    from .job_order import current_job_order_data
    details = deepcopy(metadata(booking))
    job = details['job_order']
    if current_job_order_data(booking) == previous.get('signed_snapshot'):
        return
    history = list(previous.get('revisions') or [])
    history.append({k: deepcopy(v) for k, v in previous.items() if k not in ('revisions', '_signing_private')})
    for key in ('signatures', 'signed_snapshot', 'template_attachment', '_signing_private'):
        job.pop(key, None)
    job.update(revisions=history, revision=previous.get('revision', 1) + 1)
    save_details(booking, details)
