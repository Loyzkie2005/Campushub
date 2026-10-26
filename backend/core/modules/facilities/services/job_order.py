"""Official BEU Job Order presentation on the existing booking JSON record."""
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from api.models import Booking, FacilityBookingRequest

from .booking_slip import local_stamp
from .booking_workflow import booking_row, text, time_label
from .catalog import SERVICE_MODES, SERVICE_TYPES
from .schedules import metadata

SERVICE_CHOICES = ('Equipment Rental', 'Facility Rental', 'Hotel Accommodation',
                   'Training Center', 'Laboratory Analysis', 'BPP NCII Assessment')
GENDER_CHOICES = ('Male', 'Female', 'Prefer not to say')


def default_job_order_service(facility):
    """One system mapping for the mobile request summary and the actual draft."""
    if (facility is None or facility.facility_type in SERVICE_TYPES
            or facility.booking_mode in SERVICE_MODES):
        return ''
    return {'covered_court': 'Facility Rental', 'function_hall': 'Facility Rental',
            'hostel': 'Hotel Accommodation'}.get(facility.facility_type, '')


def draft_eligible(booking, details):
    return (booking.status in (Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED)
        and booking.facility is not None
        and booking.facility.facility_type not in SERVICE_TYPES
        and booking.facility.booking_mode not in SERVICE_MODES
        and details.get('source') != 'schedule'
        and not details.get('schedule'))


def add_job_order_draft(booking, details):
    """Prepare only missing drafts inside existing creation/approval transactions."""
    if details.get('job_order') or not draft_eligible(booking, details):
        return False
    selected = default_job_order_service(booking.facility)
    row = booking_row(booking)
    specifics = []

    def known(label, value):
        if value is not None and str(value).strip() and value not in ('Not recorded', '\u2014', 'N/A'):
            specifics.append(f'{label}: {value}')

    known('Facility', booking.facility.facility_name)
    known('Activity', details.get('event_name'))
    known('Purpose', details.get('purpose') or row.get('purpose'))
    if booking.check_in_date:
        schedule = booking.check_in_date.strftime('%b %d, %Y')
        if booking.check_out_date:
            schedule += ' to ' + booking.check_out_date.strftime('%b %d, %Y')
        known('Stay', schedule)
    elif booking.booking_date:
        schedule = booking.booking_date.strftime('%b %d, %Y')
        if booking.start_time and booking.end_time:
            schedule += ' - ' + time_label(booking.start_time) + ' to ' + time_label(booking.end_time)
        known('Schedule', schedule)
    known('Room / Unit', row.get('room'))
    known('Expected Guests' if booking.check_in_date else 'Expected Participants', details.get('attendees'))
    saved_requirements = details.get('additional_requirements') or []
    if isinstance(saved_requirements, list):
        requirements = [value for value in saved_requirements if isinstance(value, str) and value.strip()]
    elif isinstance(saved_requirements, str):
        requirements = [saved_requirements]
    else:
        requirements = []
    other = details.get('other_requirements')
    if isinstance(other, str) and other.strip():
        requirements.append(other)
    known('Additional Requirements', ', '.join(requirements))
    details['job_order'] = {
        'number': '', 'date': timezone.localdate().isoformat(), 'document_status': 'draft',
        'auto_generated': True, 'prepared_at': timezone.now().isoformat(),
        'service_types': [selected] if selected else [], 'service_other': '',
        'service_requested': selected or '', 'specifics': '\n'.join(specifics),
        'items': '\n'.join(requirements), 'gender_preference': '', 'turnaround_time': '',
        'received_at': '', 'required_at': '',
    }
    return True


def ensure_job_order_draft(booking):
    """Idempotent lazy backfill after access checks; lock before merging old JSON."""
    details = metadata(booking)
    if details.get('job_order') or not draft_eligible(booking, details):
        return
    with transaction.atomic():
        # Use the same Booking serialization boundary as transaction writers.
        locked = Booking.objects.select_for_update(of=('self',)).select_related('facility', 'user').get(pk=booking.pk)
        sidecar = FacilityBookingRequest.objects.select_for_update().filter(booking=locked).first()
        current = dict(sidecar.details or {}) if sidecar else {}
        locked.mobile_request = sidecar if sidecar else FacilityBookingRequest(details=current)
        if add_job_order_draft(locked, current):
            if sidecar:
                sidecar.details = current
                sidecar.save(update_fields=['details'])
            else:
                import uuid
                sidecar = FacilityBookingRequest.objects.create(booking=locked, request_key=uuid.uuid4(), details=current)
        booking.status = locked.status
        if sidecar:
            booking.mobile_request = sidecar


def refresh_unedited_draft(booking, details):
    """Keep untouched generated text current when its source reservation is edited."""
    original = details.get('job_order') or {}
    if not original:
        return add_job_order_draft(booking, details)
    if not original.get('auto_generated') or original.get('updated_at'):
        return False
    candidate = {key: value for key, value in details.items() if key != 'job_order'}
    if not add_job_order_draft(booking, candidate):
        return False
    fields = ('service_types', 'service_other', 'service_requested', 'specifics', 'items')
    details['job_order'] = {**original, **{key: candidate['job_order'][key] for key in fields}}
    return True


def job_order_available(booking):
    # Preserve recorded terminal history; Pending never exposes a Job Order.
    return booking.status != Booking.STATUS_PENDING and bool(metadata(booking).get('job_order'))


def service_selection(record):
    """Keep legacy free text as an explicit write-in, without guessing its meaning."""
    if isinstance(record.get('service_types'), list):
        selected = [value for value in SERVICE_CHOICES if value in record['service_types']]
        return selected, record.get('service_other') or ''
    saved = record.get('service_requested') or ''
    return ([saved], '') if saved in SERVICE_CHOICES else ([], saved)


def validated_selection(data):
    """New checkbox submissions also populate the existing service_requested key."""
    selected = data.get('service_types')
    if not isinstance(selected, list) or any(value not in SERVICE_CHOICES for value in selected):
        raise ValidationError('Select a valid job or service requested.')
    selected = [value for value in SERVICE_CHOICES if value in selected]
    other = text(data, 'service_other')
    requested = '; '.join([*selected, *([other] if other else [])])
    if not requested:
        raise ValidationError('Select a job or service requested, or specify another service.')
    if len(requested) > 2000:
        raise ValidationError('Keep the job or service requested within 2000 characters.')
    return {'service_types': selected, 'service_other': other, 'service_requested': requested}


def job_order_data(booking, *, row=None):
    """Saved client and Job Order data in; plain Word field values out."""
    details = metadata(booking)
    record = details.get('job_order') or {}
    row = booking_row(booking) if row is None else row
    selected, other = service_selection(record)
    saved_date = record.get('date') or ''
    try:
        saved_date = date.fromisoformat(saved_date).strftime('%B %d, %Y')
    except (ValueError, TypeError):
        pass
    gender = record.get('gender_preference') or ''
    def paper_value(value):
        return '' if value in (None, 'Not recorded', '\u2014', 'N/A') else value

    return {'number': record.get('number') or '', 'date': saved_date,
        'client': client_data(booking, details, row),
        'gender_choices': [{'label': value, 'checked': gender.casefold() == value.casefold()}
                           for value in GENDER_CHOICES],
        'legacy_gender': gender if gender.casefold() not in ('', *(value.casefold() for value in GENDER_CHOICES)) else '',
        'service_choices': [{'label': value, 'checked': value in selected} for value in SERVICE_CHOICES],
        'service_other': other, 'specifics': record.get('specifics') or '', 'items': record.get('items') or '',
        'turnaround_time': record.get('turnaround_time') or '',
        'received_at': paper_value(local_stamp(record['received_at'])) if record.get('received_at') else '',
        'required_at': paper_value(local_stamp(record['required_at'])) if record.get('required_at') else ''}


def client_data(booking, details, row):
    name = details.get('full_name') or row['reserved_by']
    return {
        'name': '' if name in ('Not recorded', '\u2014', 'N/A') else name,
        'address': details.get('address') or '',
        'phone': details.get('contact_number') or (booking.user.contact_number if booking.user else ''),
        'email': details.get('email') or (booking.user.email if booking.user else ''),
    }


def job_order_form_data(booking, *, row=None):
    row = booking_row(booking) if row is None else row
    return {'client': client_data(booking, metadata(booking), row), 'service_choices': list(SERVICE_CHOICES),
            'gender_choices': list(GENDER_CHOICES)}
