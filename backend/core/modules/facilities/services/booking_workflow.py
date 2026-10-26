"""Transaction presentation and transitions on the existing Booking/JSON/payment tables."""
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.role_permissions import user_has_admin_access
from api.models import Booking, FacilityBookingRequest, FacilityPayment, Room
from .schedules import metadata, validated_attachment

READ_PERMISSIONS = ('can_view_bookings', 'can_manage_bookings', 'can_approve_bookings',
                    'can_record_facility_payment', 'can_book_facilities')
VERIFICATION_METHODS = ('Student ID', 'Faculty / Staff ID', 'University Office Verification',
                        'Recognized Student Organization', 'Immediate Family Proof', 'Other')
ACTION_PERMISSIONS = {'approve': 'can_approve_bookings', 'reject': 'can_approve_bookings',
    'cancel': 'can_manage_bookings', 'complete': 'can_manage_bookings', 'edit': 'can_manage_bookings',
    'job_order': 'can_manage_bookings', 'inspection': 'can_manage_bookings', 'assign_personnel': 'can_manage_bookings',
    'document': 'can_manage_bookings', 'payment': 'can_record_facility_payment',
    'archive': 'can_manage_bookings', 'restore': 'can_manage_bookings'}
CANCELLED_READ_ONLY = 'Cancelled bookings are read-only and can no longer be edited.'


def require_writable_booking(booking, action):
    """Archive changes record visibility only; all cancelled workflow writes stay locked."""
    if booking.status == Booking.STATUS_CANCELLED and action not in ('archive', 'restore'):
        raise ValidationError(CANCELLED_READ_ONLY)


def actor(user):
    return {'id': user.pk, 'name': user.get_full_name() or user.username}


def time_label(value):
    """Read-only 12-hour presentation; keep actual stored times unchanged."""
    if not value:
        return ''
    from .operating_schedule import parse_time
    from django.utils.formats import time_format
    try:
        parsed = parse_time(value) if isinstance(value, str) else value
        return time_format(parsed, 'g:i A')
    except ValidationError:
        return str(value)


def save_details(booking, details):
    # Legacy bookings may have no sidecar. Add metadata, never a second Booking.
    existing = FacilityBookingRequest.objects.filter(booking=booking).values_list('request_key', flat=True).first()
    FacilityBookingRequest.objects.update_or_create(booking=booking,
        defaults={'details': details, 'request_key': existing or uuid.uuid4()})
    if hasattr(booking, '_state'):
        booking._state.fields_cache.pop('mobile_request', None)


def paid_summary(booking):
    records = list(booking.payments.all())
    valid = [p for p in records if p.payment_status == FacilityPayment.PAYMENT_PAID]
    paid = sum((p.paid_amount for p in valid), Decimal('0'))
    return {'paid_amount': str(paid), 'amount_due': str(max(booking.total_amount - paid, Decimal('0'))),
            'payment_status': 'paid' if valid and paid >= booking.total_amount else 'unpaid'}


def payment_summary_query(records):
    """SQL equivalent of paid_summary, without joining and multiplying booking rows."""
    from django.db.models import DecimalField, Exists, OuterRef, Subquery, Sum, Value
    from django.db.models.functions import Coalesce
    paid = FacilityPayment.objects.filter(booking_id=OuterRef('pk'), payment_status=FacilityPayment.PAYMENT_PAID)
    totals = paid.order_by().values('booking_id').annotate(total=Sum('paid_amount')).values('total')[:1]
    return records.annotate(has_paid=Exists(paid),
        paid_total=Coalesce(Subquery(totals),Value(Decimal('0')),output_field=DecimalField(max_digits=14,decimal_places=2)))


def booking_kpi_conditions(now=None):
    """One definition shared by KPI aggregation and its table filters."""
    from django.db.models import F, Q
    now = timezone.localtime(now or timezone.now())
    fully_paid = Q(has_paid=True, paid_total__gte=F('total_amount'))
    active_slots = Q(check_out_date__isnull=True) & (Q(booking_date__gt=now.date()) |
        Q(booking_date=now.date(), end_time__gt=now.time().replace(tzinfo=None)))
    active_stays = Q(check_out_date__gt=now.date()) | Q(check_out_date=now.date(),
        checkout_clock__regex=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$', checkout_clock__gt=now.strftime('%H:%M'))
    return {'pending':Q(status=Booking.STATUS_PENDING),
        'upcoming':Q(status=Booking.STATUS_APPROVED) & fully_paid & (active_slots | active_stays),
        'unpaid':Q(status=Booking.STATUS_APPROVED) & ~fully_paid}


def booking_kpi_query(records):
    from django.db.models import Case, CharField, Value, When
    from django.db.models.fields.json import KeyTextTransform
    from django.db.models.functions import Coalesce, NullIf
    saved = KeyTextTransform('check_out_time','mobile_request__details')
    snapshot = KeyTextTransform('check_out_time',KeyTextTransform('workflow_snapshot','mobile_request__details'))
    current = KeyTextTransform('check_out_time','facility__workflow_config')
    fallback = Case(When(mobile_request__details__workflow_snapshot__isnull=False,then=snapshot),default=current,output_field=CharField())
    return payment_summary_query(records).annotate(checkout_clock=Coalesce(
        NullIf(saved,Value('')),NullIf(fallback,Value('')),Value('00:00'),output_field=CharField()))


def booking_kpis(records, now=None):
    from django.db.models import Count
    conditions = booking_kpi_conditions(now)
    return booking_kpi_query(records).aggregate(total=Count('pk'),
        **{key:Count('pk',filter=condition) for key,condition in conditions.items()})


def filter_booking_kpi(records, key, now=None):
    conditions = booking_kpi_conditions(now)
    return booking_kpi_query(records).filter(conditions[key]) if key in conditions else records


def status_label(booking, summary=None):
    if booking.status == Booking.STATUS_PENDING:
        return 'Pending Approval'
    if booking.status == Booking.STATUS_APPROVED and (summary or paid_summary(booking))['payment_status'] == 'paid':
        return 'Reserved / Confirmed'
    return booking.get_status_display()


def rules(booking):
    details = metadata(booking)
    return details.get('workflow_snapshot', (booking.facility.workflow_config or {}) if booking.facility else {})


def has_permission(user, code):
    return user.is_authenticated and user_has_admin_access(user) and user.has_perm('accounts.' + code)


def allowed_actions(booking, user):
    if booking.status == Booking.STATUS_CANCELLED:
        action = 'restore' if (metadata(booking).get('archive') or {}).get('is_archived') else 'archive'
        return [action] if has_permission(user, ACTION_PERMISSIONS[action]) else []
    paid = paid_summary(booking)
    active = booking.status in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED)
    approved = booking.status == Booking.STATUS_APPROVED
    result = []
    if booking.status == Booking.STATUS_PENDING:
        result += ['approve', 'reject']
    if active:
        if cancellation_readiness(booking)['eligible']:
            result += ['cancel']
        if paid['payment_status'] == 'unpaid' and Decimal(paid['paid_amount']) == 0 and has_permission(user, 'can_book_facilities'):
            result += ['edit']
    if approved and paid['payment_status'] == 'unpaid':
        result += ['payment']
    if approved:
        result += ['job_order']
    from .inspections import can_record_inspection
    if approved and can_record_inspection(user):
        result += ['assign_personnel']
        if inspection_actions(booking):
            result += ['inspection']
    if active:
        result += ['document']
    if approved and completion_readiness(booking, summary=paid)['eligible']:
        result += ['complete']
    return [key for key in result if has_permission(user, ACTION_PERMISSIONS[key])]


def booking_row(booking, user=None, room_names=None):
    from api.views import _serialize_booking_event
    result = _serialize_booking_event(booking)
    summary = paid_summary(booking)
    details = metadata(booking)
    from .rental_configuration import PRICING_METHODS
    if room_names is None:
        room_names = dict(Room.objects.filter(pk=booking.room_id, facility_id=booking.facility_id).values_list('pk', 'room_name')) if booking.room_id else {}
    method = details.get('pricing_method') or (details.get('quote') or {}).get('price_type')
    if not method and booking.facility:
        method = booking.facility.price_type
    permitted = allowed_actions(booking, user) if user else []
    from .inspections import inspection_shortcuts
    result.update(summary, status_label=status_label(booking, summary), room=room_names.get(booking.room_id) or '\u2014',
        approved_by=details.get('approval', {}).get('by', {}).get('name', ''),
        approved_at=details.get('approval', {}).get('at', ''), attendees=details.get('attendees'),
        pricing_method_label=PRICING_METHODS.get(method, ''),
        has_job_order=bool(details.get('job_order')),
        actions=permitted, cancellation=cancellation_readiness(booking),
        is_archived=bool((details.get('archive') or {}).get('is_archived')),
        inspection_shortcuts=inspection_shortcuts(booking, permitted) if user else [])
    return result


def timestamp(value, label, *, future_message=None):
    try:
        parsed = datetime.fromisoformat(str(value))
        # datetime-local has no offset: use CampusHub's Philippine default,
        # rather than a viewer-specific activated timezone. Preserve explicit offsets.
        parsed = timezone.make_aware(parsed, timezone.get_default_timezone()) if timezone.is_naive(parsed) else parsed
    except (ValueError, TypeError):
        raise ValidationError(f'Enter a valid {label}.')
    if parsed > timezone.now():
        raise ValidationError(future_message or f'Enter a valid {label}, not in the future.')
    return parsed


def text(data, key, *, required=False, maximum=2000):
    value = str(data.get(key) or '').strip()
    if len(value) > maximum or required and not value:
        raise ValidationError(f'Enter {key.replace("_", " ")} (maximum {maximum} characters).')
    return value


def decimal_amount(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount > Decimal('99999999.99') or amount != amount.quantize(Decimal('.01')):
            raise ValueError
        return amount
    except (ValueError, TypeError, InvalidOperation):
        raise ValidationError('Enter a valid amount with at most two decimal places.')


def reservation_end(booking):
    if booking.check_out_date:
        from .operating_schedule import parse_time
        saved = metadata(booking).get('check_out_time') or rules(booking).get('check_out_time')
        if not saved:
            return None
        return timezone.make_aware(datetime.combine(booking.check_out_date, parse_time(saved)), timezone.get_default_timezone())
    if not booking.booking_date or not booking.end_time:
        return None
    return timezone.make_aware(datetime.combine(booking.booking_date, booking.end_time), timezone.get_default_timezone())


def ended(booking):
    finish = reservation_end(booking)
    return bool(finish and finish <= timezone.now())


def reservation_start(booking):
    from .operating_schedule import parse_time
    if booking.check_in_date:
        saved = metadata(booking).get('check_in_time') or rules(booking).get('check_in_time')
        day, clock = booking.check_in_date, parse_time(saved) if saved else None
    else:
        day, clock = booking.booking_date, booking.start_time
    return timezone.make_aware(datetime.combine(day, clock), timezone.get_default_timezone()) if day and clock else None


def cancellation_readiness(booking):
    """Payment-independent policy shared by admin and owner cancellation paths."""
    if booking.status not in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED):
        return {'eligible': False, 'reason': 'Completed, cancelled or rejected bookings cannot be cancelled.'}
    try:
        start = reservation_start(booking)
    except (ValidationError, ValueError, TypeError):
        start = None
    if start is None:
        return {'eligible': False, 'reason': 'Record a valid reservation start date and time before cancelling this booking.'}
    if timezone.now() >= start:
        return {'eligible': False, 'reason': 'This booking cannot be cancelled because the scheduled use has already started.'}
    return {'eligible': True, 'reason': ''}


def completion_issues(details, post=None):
    """Detect recorded review needs, never infer that narrative text resolves them."""
    if post is None:
        post = (details.get('inspections') or {}).get('post') or {}
    from .inspections import damage_state, has_issue_text
    issues = damage_state(post) is True or any(has_issue_text(post.get(key)) for key in ('missing_items', 'overtime'))
    try:
        deposit = Decimal(str((details.get('quote') or {}).get('deposit_amount') or '0'))
        has_deposit = deposit.is_finite() and deposit > 0
    except InvalidOperation:
        has_deposit = False  # Missing/unreadable history cannot invent a deposit.
    required = bool(has_deposit or issues)
    resolved = bool(required and str(post.get('deposit_decision') or '').strip()
                    and post.get('issues_resolved_confirmed') is True)
    return {'required': required, 'resolved': resolved, 'has_deposit': has_deposit, 'has_issues': issues}


def inspection_actions(booking):
    """Never offer a retrospective pre-use inspection; reuse post-use for real review."""
    if booking.status != Booking.STATUS_APPROVED:
        return []
    config, details = rules(booking), metadata(booking)
    try:
        start = reservation_start(booking)
    except (ValidationError, TypeError, ValueError):
        start = None
    try:
        finish = reservation_end(booking)
    except (ValidationError, TypeError, ValueError):
        finish = None
    now = timezone.now()
    actions = []
    if config.get('requires_pre_use_inspection') and start and now < start:
        actions.append('pre')
    if finish and finish <= now and (config.get('requires_post_use_inspection') or completion_issues(details)['required']):
        actions.append('post')
    return actions


def completion_readiness(booking, *, summary=None):
    """One read-only checklist for permitted actions, detail UI and locked completion."""
    details, config = metadata(booking), rules(booking)
    paid = paid_summary(booking) if summary is None else summary
    try:
        finish = reservation_end(booking)
    except (ValidationError, ValueError, TypeError):
        finish = None
    inspections = details.get('inspections') or {}
    checks = []

    def check(key, label, satisfied, message, *, blocking=True, pending_label=None):
        checks.append({'key': key, 'label': label, 'satisfied': bool(satisfied), 'message': message,
                       'blocking': blocking, 'pending_label': pending_label or message})

    schedule_ended = bool(finish and finish <= timezone.now())
    check('approved', 'Booking approved', booking.status == Booking.STATUS_APPROVED,
          'Only an approved, reserved booking can be completed.')
    check('schedule', 'Scheduled use ended', schedule_ended,
          'Booking schedule has not ended yet.' if finish else 'Record a valid reservation end date and time first.')
    check('payment', 'Payment settled', paid['payment_status'] == 'paid',
          'Payment must be settled before this booking can be completed.')
    for kind, label in (('pre', 'pre-use'), ('post', 'post-use')):
        required = config.get(f'requires_{kind}_use_inspection')
        record = inspections.get(kind) or {}
        recorded = bool(record.get('condition') and record.get('inspector') and record.get('inspected_at'))
        if required or recorded:
            missed = kind == 'pre' and schedule_ended and not recorded
            check(kind + '_inspection', f'{label.capitalize()} inspection completed', recorded,
                  'Pre-use inspection was not recorded.' if missed else f'Complete the {label} inspection before completing this booking.',
                  blocking=not missed, pending_label='Pre-use inspection was not recorded.' if missed else f'{label.capitalize()} inspection required')
    resolution = completion_issues(details)
    if resolution['required']:
        check('resolution', 'Damage / deposit resolved', resolution['resolved'],
              'Record and confirm the damage / deposit resolution in the post-use review before completing this booking.',
              pending_label='Damage / deposit resolution required')
    outstanding = [item for item in checks if item['blocking'] and not item['satisfied']]
    eligible = not outstanding
    return {'eligible': eligible, 'checks': checks,
            'reason': outstanding[0]['message'] if outstanding else '', 'remaining_count': len(outstanding),
            'requires_issue_confirmation': resolution['required']}


def transition(request, booking, data):
    """Called only inside a Facility + Booking lock; return the real audit event code."""
    action = data.get('action')
    require_writable_booking(booking, action)
    if action in ('archive', 'restore'):
        if action not in allowed_actions(booking, request.user):
            raise ValidationError('Only cancelled bookings can be archived or restored in their current record state.')
        details = dict(metadata(booking))
        details['archive'] = {'is_archived': action == 'archive', 'by': actor(request.user),
                              'at': timezone.now().isoformat()}
        save_details(booking, details)
        return 'booking_archived' if action == 'archive' else 'booking_restored'
    if action == 'cancel' and has_permission(request.user, ACTION_PERMISSIONS['cancel']):
        cancellation = cancellation_readiness(booking)
        if not cancellation['eligible']:
            raise ValidationError(cancellation['reason'])
    if action == 'complete' and has_permission(request.user, ACTION_PERMISSIONS['complete']):
        readiness = completion_readiness(booking)
        if not readiness['eligible']:
            raise ValidationError(readiness['reason'])
    if action not in allowed_actions(booking, request.user):
        raise ValidationError('This action is not permitted for the current booking state.')
    details = dict(metadata(booking))
    old_job = details.get('job_order', {})
    old_inspection = {}
    now = timezone.now().isoformat()
    by = actor(request.user)
    if action == 'approve':
        # Reuse the same availability engine, ignoring only this exact booking.
        from .admin_reservations import reservation_schedule
        if not booking.facility:
            raise ValidationError('The facility is not open for booking.')
        schedule = {**details, 'date':str(booking.booking_date or ''), 'start':booking.start_time.strftime('%H:%M') if booking.start_time else '',
            'end':booking.end_time.strftime('%H:%M') if booking.end_time else '', 'check_in_date':str(booking.check_in_date or ''),
            'check_out_date':str(booking.check_out_date or ''), 'room_id':str(booking.room_id or '')}
        reservation_schedule(booking.facility, schedule, check_capacity=bool(details.get('attendees')), exclude_booking=booking.pk)
        booking.status = Booking.STATUS_APPROVED
        details['approval'] = {'by': by, 'at': now}
    elif action in ('reject', 'cancel'):
        reason = text(data, 'reason', required=True)
        booking.status = Booking.STATUS_REJECTED if action == 'reject' else Booking.STATUS_CANCELLED
        details[action] = {'by': by, 'at': now, 'reason': reason}
    elif action == 'complete':
        review_required = completion_readiness(booking)['requires_issue_confirmation']
        if review_required and data.get('issues_resolved_confirmed') is not True:
            raise ValidationError('Confirm that damage, deposit and additional charge issues are resolved before completing this booking.')
        booking.status = Booking.STATUS_COMPLETED
        details['completion'] = {'by': by, 'at': now,
            **({'issues_resolved_confirmed': True} if review_required else {})}
    elif action == 'payment':
        method = text(data, 'payment_method', required=True, maximum=40)
        if method != 'Cash':
            raise ValidationError('Select Cash for the recorded cashier payment.')
        amount = decimal_amount(data.get('amount_paid'))
        if amount <= 0:
            raise ValidationError('Amount Paid must be greater than zero.')
        due = Decimal(paid_summary(booking)['amount_due'])
        if amount != due:
            raise ValidationError('Amount Paid must equal the outstanding amount. Partial payments are not enabled.')
        receipt = text(data, 'official_receipt_no', required=True, maximum=100)
        # Serialize receipt-number checks across facilities without a new payment table.
        from django.db import connection
        if connection.vendor == 'postgresql':
            import hashlib
            lock = int.from_bytes(hashlib.sha256(('facility-or:' + receipt.casefold()).encode()).digest()[:8], 'big', signed=True)
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_advisory_xact_lock(%s)', [lock])
        if FacilityPayment.objects.filter(official_receipt_no__iexact=receipt, payment_status='paid').exists():
            raise ValidationError('That Official Receipt number is already recorded.')
        paid_at = timestamp(data.get('paid_at'), 'payment date/time',
                            future_message='Payment date and time cannot be in the future.')
        payment = FacilityPayment.objects.create(id='FP-' + uuid.uuid4().hex[:24].upper(), booking=booking,
            paid_amount=amount, payment_status='paid', official_receipt_no=receipt, paid_at=paid_at)
        records = dict(details.get('payment_records', {}))
        records[payment.pk] = {'method': method, 'by': by, 'at': now, 'notes': text(data, 'notes'),
                               'attachment': validated_attachment(data.get('attachment'))}
        details['payment_records'] = records
    elif action == 'job_order':
        old = old_job
        from .job_order import GENDER_CHOICES, service_selection, validated_selection
        job = {key: text(data, key, required=key == 'service_requested',
                         maximum=12000 if key in ('specifics', 'items') else 2000) for key in (
            'service_requested', 'specifics', 'items', 'turnaround_time', 'gender_preference',
            'received_at', 'required_at') if key != 'service_requested' or 'service_types' not in data}
        if 'service_types' in data:
            job.update(validated_selection(data))
        else:
            job['service_types'], job['service_other'] = service_selection(job)
        gender = job['gender_preference']
        if gender and gender not in GENDER_CHOICES and gender != old.get('gender_preference'):
            raise ValidationError('Select a valid gender preference.')
        if job['received_at']:
            job['received_at'] = timestamp(job['received_at'], 'received date/time').isoformat()
        if job['required_at']:
            try:
                required_at = datetime.fromisoformat(job['required_at'])
                if timezone.is_naive(required_at):
                    required_at = timezone.make_aware(required_at, timezone.get_default_timezone())
                job['required_at'] = required_at.isoformat()
            except ValueError:
                raise ValidationError('Enter a valid required date/time.')
        if 'number' in data:
            job['number'] = text(data, 'number', maximum=100)
        else:
            job['number'] = old.get('number', '')
        job.update(date=old.get('date') or timezone.localdate().isoformat(), document_status='draft',
            filled_out_by=old.get('filled_out_by') or by, assisted_by=by, updated_at=now,
            approved_by=details.get('approval', {}).get('by', {}), verified_by=by)
        job = {**old, **job}
        details['job_order'] = job
    elif action == 'assign_personnel':
        from .inspections import authorized_inspectors
        if not authorized_inspectors().filter(pk=request.user.pk).exists():
            raise ValidationError('Only authorized facilities personnel can assign personnel.')
        selected = authorized_inspectors().filter(pk=data.get('personnel_id')).first()
        if not selected or not has_permission(selected, 'can_manage_bookings'):
            raise ValidationError('Select active authorized personnel.')
        if (details.get('assigned_personnel') or {}).get('id') == selected.pk:
            return None
        details['assigned_personnel'] = {**actor(selected), 'by': by, 'at': now}
    elif action == 'inspection':
        from .inspections import authorized_inspectors, can_record_inspection
        if not can_record_inspection(request.user) or not authorized_inspectors().filter(pk=request.user.pk).exists():
            raise ValidationError('Only authorized facilities personnel can record inspections.')
        kind = data.get('kind')
        if kind not in inspection_actions(booking):
            raise ValidationError('Pre-use inspections must be recorded before scheduled facility use.' if kind == 'pre'
                                  else 'This post-use inspection or review is not available for the current schedule.')
        inspector = authorized_inspectors().filter(pk=data.get('inspector_id')).first()
        if not inspector or not has_permission(inspector, 'can_manage_bookings'):
            raise ValidationError('Select an active authorized inspector.')
        if kind == 'post' and not ended(booking):
            raise ValidationError('Record a post-use inspection only after the stay/reservation ends.')
        old_inspection = (details.get('inspections') or {}).get(kind) or {}
        from .inspections import same_inspection, validate_condition
        record = {**old_inspection, **validate_condition(data), 'remarks': text(data, 'remarks')}
        if kind == 'pre':
            record['existing_damage'] = text(data, 'existing_damage')
        else:
            if not isinstance(data.get('has_damage'), bool):
                raise ValidationError('Select Yes or No for Damage Found.')
            record['has_damage'] = data['has_damage']
            record['damage_found'] = text(data, 'damage_found', required=data['has_damage']) if data['has_damage'] else ''
        inspected_at = timestamp(data.get('inspected_at'), 'inspection date/time')
        if kind == 'pre' and inspected_at >= reservation_start(booking):
            raise ValidationError('Pre-use inspection date/time must be before scheduled facility use.')
        if kind == 'post' and reservation_end(booking) and inspected_at < reservation_end(booking):
            raise ValidationError('Post-use inspection date/time must follow the reservation.')
        decision = text(data, 'deposit_decision', maximum=100) if 'deposit_decision' in data else old_inspection.get('deposit_decision', '')
        resolution = completion_issues(details, record)
        historical_decision = decision == old_inspection.get('deposit_decision')
        if decision and (kind != 'post' or not resolution['required']) and not historical_decision:
            raise ValidationError('A damage / deposit decision applies only to a post-use review with a recorded deposit or issue.')
        confirmed = data.get('issues_resolved_confirmed') is True
        if confirmed and resolution['required'] and not decision:
            raise ValidationError('Record the damage / deposit decision before confirming resolution.')
        record.update(inspector=actor(inspector), inspected_at=inspected_at.isoformat(), recorded_by=by,
            at=now, deposit_decision=decision,
            attachment=validated_attachment(data['attachment']) if data.get('attachment') else old_inspection.get('attachment'),
            **({'issues_resolved_confirmed': confirmed} if kind == 'post' and resolution['required'] else {}))
        if not old_inspection:
            record['created_at'] = now
        if same_inspection(old_inspection, record):
            return None
        inspections = dict(details.get('inspections', {})); inspections[kind] = record
        details['inspections'] = inspections
    elif action == 'document':
        docs = list(details.get('documents', []))
        if len(docs) >= 10:
            raise ValidationError('A maximum of ten supporting documents can be added.')
        attachment = validated_attachment(data.get('attachment'))
        if not attachment:
            raise ValidationError('Select a supporting document.')
        docs.append({'id': uuid.uuid4().hex, 'title': text(data, 'title', required=True, maximum=150),
                     'by': by, 'at': now, 'attachment': attachment})
        details['documents'] = docs
    booking.save(update_fields=['status', 'updated_at'])
    from .job_order import add_job_order_draft
    add_job_order_draft(booking, details)
    save_details(booking, details)
    labels = {'approve':'booking_approved', 'reject':'booking_rejected', 'cancel':'booking_cancelled',
        'complete':'booking_completed', 'payment':'facility_payment_recorded',
        'job_order':'job_order_updated' if old_job else 'job_order_created',
        'inspection': f'{data.get("kind")}_use_inspection_' + ('updated' if action == 'inspection' and old_inspection else 'completed'),
        'document':'booking_document_added', 'assign_personnel':'booking_personnel_assigned'}
    return labels[action]


def public_client_details(details):
    """Mobile returns only client-facing reservation data, never internal evidence or staff notes."""
    allowed = ('full_name', 'organization', 'contact_number', 'email', 'event_name', 'purpose', 'notes',
               'other_requirements', 'additional_requirements', 'attendees', 'adults', 'children',
               'check_in_time', 'check_out_time', 'source')
    result = {key: details[key] for key in allowed if key in details}
    quote = details.get('quote') or {}
    result['quote'] = {key: quote[key] for key in ('base_amount','total_amount','rental_total','rental_amount',
        'discount_amount','fee_amount','deposit_amount','hours','nights','form_label','rate','price_type',
        'additional_requirements_note','fees','guests','adults','children') if key in quote}
    return result
