"""Permission-scoped booking transaction API and private documents; no duplicate models."""
import base64
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.models import AccountActivity
from api.models import Booking, Facility, FacilityBookingRequest, Room
from .admin_booking_views import access, audit, error_response, payload
from .services.booking_workflow import (ACTION_PERMISSIONS, READ_PERMISSIONS, actor, allowed_actions,
    booking_row, booking_kpis, completion_readiness, filter_booking_kpi, has_permission, inspection_actions, paid_summary, require_writable_booking, rules, save_details, time_label, transition)
from .services.catalog import service_resources_q
from .services.booking_slip_pdf import BookingSlipPDFError
from .services.schedules import PRIVATE_ATTACHMENT_TYPES, metadata, schedule_blocks_q
from .services.inspections import (CONDITION_CHOICES, authorized_inspectors, can_record_inspection,
    condition_display, damage_state, default_inspector_id)


def read_access(request):
    permission = next((p for p in READ_PERMISSIONS if has_permission(request.user, p)), 'can_view_bookings')
    return access(request, permission)


def physical_bookings():
    return Booking.objects.exclude(schedule_blocks_q()).exclude(service_resources_q('facility__')).select_related(
        'facility', 'user', 'mobile_request').prefetch_related('payments')


def row_set(query, user):
    records = list(query)
    room_names = dict(Room.objects.filter(pk__in=[b.room_id for b in records if b.room_id]).values_list('pk', 'room_name'))
    return [booking_row(b, user, room_names) for b in records]


def list_data(params, user):
    scope = physical_bookings()
    # Exclude only positively archived IDs: NOT JSON=True loses missing/NULL keys.
    archived = FacilityBookingRequest.objects.filter(details__archive__is_archived=True).values('booking_id')
    record_status = params.get('record_status', 'current')
    if record_status == 'archived':
        scope = scope.filter(pk__in=archived)
    elif record_status != 'all':
        scope = scope.exclude(pk__in=archived)
    now = timezone.now()
    totals = booking_kpis(scope, now)
    records = filter_booking_kpi(scope, params.get('kpi'), now).order_by('-created_at', '-pk')
    search = (params.get('q') or '').strip()[:100]
    if search:
        records = records.filter(Q(pk__icontains=search) | Q(purpose__icontains=search) |
            Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) |
            Q(facility__facility_name__icontains=search))
    status = params.get('status')
    if status and status != 'all':
        records = records.filter(status=status)
    facility = params.get('facility')
    if facility and facility != 'all':
        records = records.filter(facility_id=facility)
    page = Paginator(records, 20).get_page(params.get('page', 1))
    return {'bookings': row_set(page.object_list, user), 'kpis':totals, 'page': page.number, 'pages': page.paginator.num_pages,
            'total': page.paginator.count, 'start_index': page.start_index(), 'end_index': page.end_index(),
            'has_previous': page.has_previous(), 'has_next': page.has_next()}


@require_GET
def listing(request):
    denied = read_access(request)
    return denied if denied is not None else JsonResponse(list_data(request.GET, request.user))


def without_attachments(value):
    if isinstance(value, dict):
        return {k: without_attachments(v) for k, v in value.items() if k not in ('attachment', 'data')}
    if isinstance(value, list):
        return [without_attachments(v) for v in value]
    return value


def documents_for(booking):
    from .services.job_order import job_order_available
    details = metadata(booking)
    result = [{'title': 'Booking Slip', 'url': f'/admin-bookings/{booking.pk}/slip/',
               'section': 'BookingForm',
               'pdf_url': f'/api/bookings/{booking.pk}/documents/slip/?format=pdf'}]
    if job_order_available(booking):
        result.append({'title': 'Job Order', 'url': f'/api/bookings/{booking.pk}/documents/job-order/',
                       'section': 'JobOrder',
                       'pdf_url': f'/api/bookings/{booking.pk}/documents/job-order/?format=pdf'})
    for kind in ('pre', 'post'):
        record = details.get('inspections', {}).get(kind)
        if record:
            result.append({'title': f'{kind.title()}-Use Inspection Report',
                'section': 'Inspection', 'kind': kind,
                'url': f'/api/bookings/{booking.pk}/documents/{kind}-inspection/',
                'pdf_url': f'/api/bookings/{booking.pk}/documents/{kind}-inspection/?format=pdf'})
            if record.get('attachment'):
                result.append({'title': record['attachment']['name'], 'section': 'Inspection', 'kind': kind,
                               'url': f'/api/bookings/{booking.pk}/attachments/{kind}/'})
    for key, record in details.get('payment_records', {}).items():
        if record.get('attachment'):
            result.append({'title': 'Receipt: ' + record['attachment']['name'],
                           'section': 'Payment',
                           'url': f'/api/bookings/{booking.pk}/attachments/{key}/',
                           'view_url': f'/api/bookings/{booking.pk}/attachments/{key}/?inline=1'
                               if record['attachment'].get('type') in PRIVATE_ATTACHMENT_TYPES else None})
    for doc in details.get('documents', []):
        result.append({'title': doc['title'], 'section': 'BookingForm',
                       'url': f'/api/bookings/{booking.pk}/attachments/{doc["id"]}/'})
    return result


def detail_data(request, booking):
    """One authorized booking payload reused by the existing API and full page."""
    from .services.job_order import ensure_job_order_draft, job_order_available
    ensure_job_order_draft(booking)
    details = metadata(booking)
    activity = AccountActivity.objects.filter(module='Facility Bookings', metadata__booking_id=booking.pk).order_by('-created_at')[:50]
    staff = []
    permitted = allowed_actions(booking, request.user)
    if any(action in permitted for action in ('inspection', 'assign_personnel')):
        staff = [actor(u) for u in authorized_inspectors()]
    records = details.get('payment_records', {})
    payments = []
    for payment in booking.payments.all():
        record = records.get(payment.pk, {})
        attachment = record.get('attachment')
        payments.append({'id': payment.pk, 'amount': str(payment.paid_amount), 'status': payment.payment_status,
            'official_receipt_no': payment.official_receipt_no or '',
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else '',
            **without_attachments(record),
            'receipt_attachment': {'name': attachment['name'],
                'url': f'/api/bookings/{booking.pk}/attachments/{payment.pk}/',
                'view_url': f'/api/bookings/{booking.pk}/attachments/{payment.pk}/?inline=1'
                    if attachment.get('type') in PRIVATE_ATTACHMENT_TYPES else None} if attachment else None})
    from .services.rental_configuration import booking_slip_label
    row = booking_row(booking, request.user)
    row['booking_form_label'] = booking_slip_label(booking.facility, details.get('quote'), details.get('workflow_snapshot'))
    from django.template.loader import render_to_string
    from .services.booking_slip import booking_slip_data
    from .services.job_order import job_order_form_data
    slip_html = render_to_string('facilities/partials/official_booking_slip.html', {'slip': booking_slip_data(booking, row=row)})
    job_url = f'/api/bookings/{booking.pk}/documents/job-order/'
    job_document = {'pdf_url': job_url + '?format=pdf&inline=1',
                    'docx_url': job_url + '?format=docx'} if job_order_available(booking) else None
    return {'booking': row, 'details': {**without_attachments(details),
        'client_id':booking.user_id, 'room_id':str(booking.room_id or '')},
        'rules': {key: rules(booking).get(key, False) for key in ('requires_pre_use_inspection', 'requires_post_use_inspection')},
        'payments': payments, 'documents': documents_for(booking), 'staff': staff, 'booking_form_html': slip_html,
        'job_order_document': job_document, 'job_order_form': job_order_form_data(booking, row=row),
        'job_order_status': 'Draft' if job_document else '',
        'completion': {**completion_readiness(booking, summary=row),
                       'can_manage': has_permission(request.user, 'can_manage_bookings')},
        'inspection_actions': inspection_actions(booking) if 'inspection' in row['actions'] else [],
        'inspection_defaults': {kind: default_inspector_id((details.get('inspections') or {}).get(kind) or {}, staff,
                                                         details.get('assigned_personnel'))
                                for kind in ('pre', 'post')},
        'inspection_condition_choices': list(CONDITION_CHOICES),
        'inspection_conditions': {kind: condition_display((details.get('inspections') or {}).get(kind) or {})
                                  for kind in ('pre', 'post')},
        'inspection_damage': damage_state((details.get('inspections') or {}).get('post') or {}),
        'recording_user': actor(request.user) if has_permission(request.user, 'can_record_facility_payment') else None,
        'activity': [{'at': a.created_at.isoformat(), 'by': a.full_name or a.username, 'role': a.role,
                      'code': a.activity_type, 'action': a.activity_type.replace('_', ' ').title(), 'result': a.result} for a in activity]}


@require_GET
def detail(request, booking_id):
    denied = read_access(request)
    if denied is not None:
        return denied
    booking = get_object_or_404(physical_bookings(), pk=booking_id)
    response = JsonResponse(detail_data(request, booking))
    response['Cache-Control'] = 'private, no-store'
    return response


@require_GET
def detail_page(request, booking_id):
    denied = read_access(request)
    if denied is not None:
        return denied
    booking = get_object_or_404(physical_bookings(), pk=booking_id)
    from accounts.views import get_notification_context
    response = render(request, 'facilities/pages/admin_booking_details.html', {
        'booking_detail': detail_data(request, booking), 'booking_id': booking.pk,
        'facilities': [booking.facility] if booking.facility else [],
        'can_book_facilities': has_permission(request.user, 'can_book_facilities'),
        'can_manage_schedules': False, 'active_page': 'bookings',
        'page_title': 'Bookings', 'breadcrumb_page': 'Booking Details',
        **get_notification_context(user=request.user),
    })
    response['Cache-Control'] = 'private, no-store'
    return response


@require_POST
def update(request, booking_id):
    try:
        data = payload(request)
        action = data.get('action')
        if action not in ACTION_PERMISSIONS:
            raise ValidationError('Select a supported booking action.')
        denied = access(request, ACTION_PERMISSIONS[action])
        if denied is not None:
            return denied
        if action in ('inspection', 'assign_personnel') and (not can_record_inspection(request.user)
                or not authorized_inspectors().filter(pk=request.user.pk).exists()):
            return JsonResponse({'error': 'Only authorized facilities personnel can record inspections.'}, status=403)
        # Same lock order as admin/mobile create: Facility, then Booking.
        original = get_object_or_404(physical_bookings(), pk=booking_id)
        with transaction.atomic():
            if original.facility_id:
                get_object_or_404(Facility.objects.select_for_update(), pk=original.facility_id)
            booking = get_object_or_404(Booking.objects.select_for_update(), pk=booking_id)
            require_writable_booking(booking, action)
            if action == 'edit':
                if action not in allowed_actions(booking, request.user):
                    raise ValidationError('Only active unpaid bookings can be edited.')
                from .services.admin_reservations import client_details, reservation_quote
                if str(data.get('facility_id')) != str(booking.facility_id):
                    raise ValidationError('Keep the same facility when editing this booking.')
                user, client = client_details(data, booking.facility)
                fields, quote = reservation_quote(booking.facility, data, exclude_booking=booking.pk)
                if str(data.get('quoted_amount')) != quote['total_amount']:
                    raise ValidationError('Review the updated quote before saving.')
                details = dict(metadata(booking)); client.pop('source', None); details.update(client)
                for key in ('attendees','adults','children','shared_rate','discount_index','discount_reason','fee_quantities',
                            'verification_method','verification_other','verification_notes'):
                    details[key] = data.get(key)
                details.update(quote=quote, attendees=quote['guests'], adults=quote['adults'], children=quote['children'])
                booking.user = user
                for key in ('booking_date','start_time','end_time','check_in_date','check_out_date','room_id'):
                    setattr(booking, key, fields.get(key))
                booking.purpose = f'[reservation]\n{details["purpose"]}\nReserved by: {details["full_name"]}'
                booking.total_amount = Decimal(quote['total_amount']); booking.save()
                from .services.job_order import refresh_unedited_draft
                refresh_unedited_draft(booking, details)
                save_details(booking, details); event = 'booking_updated'
            else:
                from .services.booking_workflow import completion_issues
                previous_issues = completion_issues(metadata(booking)) if action == 'inspection' else {}
                event = transition(request, booking, data)
            if event:
                audit(request, booking, event)
                if action == 'inspection' and data.get('kind') == 'post':
                    current_issues = completion_issues(metadata(booking))
                    if current_issues['has_issues'] and not previous_issues['has_issues']:
                        audit(request, booking, 'booking_damage_recorded')
                    if current_issues['resolved'] and not previous_issues['resolved']:
                        audit(request, booking, 'booking_resolution_completed')
            if action == 'payment':
                audit(request, booking, 'booking_reserved')
        return JsonResponse({'message': 'No changes to save.' if not event else
            'Payment recorded successfully.' if action == 'payment' else 'Booking updated.', 'changed': bool(event),
            'booking': booking_row(booking, request.user)})
    except (ValidationError, ValueError, TypeError, ArithmeticError, KeyError) as error:
        return error_response(error)


def document_values(booking, kind):
    if kind == 'slip':
        from .services.booking_slip import booking_slip_data, slip_values
        slip = booking_slip_data(booking)
        return slip['title'], slip_values(slip)
    details = metadata(booking)
    row = booking_row(booking)
    common = [('Booking ID', booking.pk), ('Client', details.get('full_name') or row['reserved_by']),
        ('Organization / Office', details.get('organization', '')), ('Address', details.get('address', '')),
        ('Phone', details.get('contact_number', '')), ('Email', details.get('email', '')),
        ('Facility', row['facility']), ('Room / Unit', row['room']),
        ('Reservation Date / Stay', row['date'] + (' to ' + row['end_date'] if row['end_date'] else '')),
        ('Time', time_label(booking.start_time) + ' to ' + time_label(booking.end_time) if row['start'] else 'Not applicable'),
        ('Booking Status', row['status_label'])]
    if kind in ('pre-inspection', 'post-inspection'):
        record = details.get('inspections', {}).get(kind.split('-')[0])
        if not record:
            raise ValidationError('No inspection has been recorded.')
        title = kind.replace('-', ' ').title() + ' Report'
        extra = [('Inspector', (record.get('inspector') or {}).get('name', '')),
                 ('Inspection Date & Time', record.get('inspected_at')),
                 ('Facility Condition', condition_display(record)['label'])]
        if kind == 'pre-inspection':
            extra.append(('Existing Damage / Issues', record.get('existing_damage')))
        else:
            damaged = damage_state(record)
            extra.append(('Damage Found', 'Yes' if damaged is True else 'No' if damaged is False else 'Not recorded'))
            if damaged is True:
                extra.append(('Damage Description', record.get('damage_found')))
        extra += [('Remarks', record.get('remarks')),
                  ('Recorded / Updated By', (record.get('recorded_by') or {}).get('name', '')),
                  ('Created At', record.get('created_at')), ('Updated At', record.get('at'))]
        # Historical findings remain accessible; the simplified forms do not overwrite them.
        extra += [(key.replace('_', ' ').title() + ' (previously recorded)', record[key])
                  for key in ('cleanliness', 'missing_items', 'overtime') if record.get(key)]
        if record.get('deposit_decision'):
            extra.append(('Damage / Deposit Decision', record['deposit_decision']))
            extra.append(('Resolution Confirmed', 'Yes' if record.get('issues_resolved_confirmed') is True else 'No'))
    else:
        raise ValidationError('Select a recorded booking document.')
    values = []
    from django.utils.dateparse import parse_datetime
    for label,value in common + extra:
        if value in (None,''):continue
        rendered=str(value)
        if label in ('Date / Time Received','Date / Time Required','Inspected At','At',
                     'Inspection Date & Time', 'Created At', 'Updated At'):
            stamp=parse_datetime(rendered)
            if stamp:
                stamp=timezone.make_aware(stamp) if timezone.is_naive(stamp) else stamp
                rendered=timezone.localtime(stamp).strftime('%b %d, %Y Â· %I:%M %p')
        values.append((str(label),rendered))
    return title, values


def pdf_response(title, values, filename, *, slip=None, job_order=None):
    if job_order is not None:
        from .services.job_order_docx import job_order_pdf
        content = job_order_pdf(job_order)
    elif slip is not None:
        from .services.booking_slip_pdf import booking_slip_pdf
        content = booking_slip_pdf(slip)
    else:
        # Other workflow documents keep their existing ReportLab renderer.
        from io import BytesIO
        from xml.sax.saxutils import escape
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        stream = BytesIO(); styles = getSampleStyleSheet()
        for key in ('Heading2','Title'):
            styles[key].textColor = colors.HexColor('#1A1851')
        body = styles['BodyText']; body.textColor = colors.HexColor('#1A1851'); body.leading = 15
        items = [Paragraph('CampusHub - USTP Oroquieta', styles['Heading2']), Paragraph(escape(title), styles['Title']), Spacer(1,12)]
        rows = [[Paragraph(escape(k), body), Paragraph(escape(v).replace('\n','<br/>'), body)] for k,v in values]
        table = Table(rows, colWidths=[150, 365])
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('BOTTOMPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),8), ('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#e2e8f0'))]))
        items += [table, Spacer(1,18), Paragraph('Generated from recorded CampusHub data. This is not an Official Receipt.', body)]
        SimpleDocTemplate(stream, pagesize=A4, leftMargin=40,rightMargin=40,topMargin=40,bottomMargin=40).build(items)
        content = stream.getvalue()
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    response['Cache-Control'] = 'private, no-store'
    return response


@require_GET
def document(request, booking_id, kind):
    denied = read_access(request)
    if denied is not None:
        return denied
    booking = get_object_or_404(physical_bookings(), pk=booking_id)
    try:
        slip = job_order = None
        if kind == 'slip':
            from .services.booking_slip import booking_slip_data, slip_values
            slip = booking_slip_data(booking)
            title, values = slip['title'], slip_values(slip)
        elif kind == 'job-order':
            from .services.job_order import ensure_job_order_draft, job_order_available, job_order_data
            ensure_job_order_draft(booking)
            if not job_order_available(booking):
                raise ValidationError('Job Order is available after booking approval.')
            job_order = job_order_data(booking)
            title, values = 'Job Order Request', []
        else:
            title, values = document_values(booking, kind)
        if job_order is not None and request.GET.get('format') == 'docx':
            from .services.job_order_docx import job_order_docx
            response = HttpResponse(job_order_docx(job_order),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename="{booking.pk}-job-order.docx"'
            response['Cache-Control'] = 'private, no-store'
            response['X-Content-Type-Options'] = 'nosniff'
            return response
        if request.GET.get('format') == 'pdf':
            response = pdf_response(title, values, f'{booking.pk}-{kind}', slip=slip, job_order=job_order)
            if job_order is not None and request.GET.get('inline') == '1':
                response['Content-Disposition'] = f'inline; filename="{booking.pk}-job-order.pdf"'
                response['X-Frame-Options'] = 'SAMEORIGIN'
            response['X-Content-Type-Options'] = 'nosniff'
            return response
        template = 'facilities/pages/job_order.html' if job_order else 'facilities/pages/booking_slip.html' if slip else 'facilities/pages/booking_document.html'
        response = render(request, template, {'title':title,'values':values,'slip':slip,'job_order':job_order,
            'pdf_url': request.path + '?format=pdf',
            'preview_url': request.path + '?format=pdf&inline=1', 'docx_url': request.path + '?format=docx'})
        response['Cache-Control'] = 'private, no-store'
        return response
    except BookingSlipPDFError as error:
        response = JsonResponse({'error': str(error)}, status=503)
        response['Cache-Control'] = 'private, no-store'
        return response
    except ValidationError as error:
        return error_response(error)


@require_GET
def attachment(request, booking_id, key):
    denied = read_access(request)
    if denied is not None:
        return denied
    booking = get_object_or_404(physical_bookings(), pk=booking_id)
    details = metadata(booking)
    record = details.get('inspections', {}).get(key) or details.get('payment_records', {}).get(key)
    if not record:
        record = next((d for d in details.get('documents', []) if d.get('id') == key), {})
    file = record.get('attachment')
    if not file:
        return JsonResponse({'error':'Document not found.'},status=404)
    response = HttpResponse(base64.b64decode(file['data']), content_type=file['type'])
    inline = (request.GET.get('inline') == '1' and key in details.get('payment_records', {})
              and file.get('type') in PRIVATE_ATTACHMENT_TYPES)
    response['Content-Disposition'] = ('inline' if inline else 'attachment') + '; filename="' + file['name'].replace('"','') + '"'
    response['Cache-Control'] = 'private, no-store'; response['X-Content-Type-Options'] = 'nosniff'
    return response
