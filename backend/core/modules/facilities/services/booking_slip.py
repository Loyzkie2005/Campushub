"""Read-only official slip content shared by embedded preview, print and PDF."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils import timezone

from accounts.models import AccountActivity, User
from api.models import FacilityPayment
from .booking_workflow import booking_row, time_label
from .rental_configuration import FORM_TYPES, booking_slip_label
from .schedules import metadata

INSTITUTION = ('UNIVERSITY OF SCIENCE AND TECHNOLOGY OF SOUTHERN', 'PHILIPPINES')
CAMPUS = 'USTP - OROQUIETA CAMPUS'
MISSING = 'Not recorded'


def local_stamp(value):
    if not value:
        return MISSING
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return MISSING
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_default_timezone())
    return timezone.localtime(value).strftime('%b %d, %Y - %I:%M %p')


def peso(value):
    """Absent quote fields are not assumed to be zero."""
    if value is None or value == '':
        return MISSING
    try:
        number = Decimal(str(value))
        return f'PHP {number:,.2f}' if number.is_finite() else MISSING
    except InvalidOperation:
        return MISSING


def booking_slip_data(booking, *, row=None):
    details = metadata(booking)
    quote = details.get('quote') or {}
    row = booking_row(booking) if row is None else row
    title = booking_slip_label(booking.facility, quote, details.get('workflow_snapshot'))
    rental = title == FORM_TYPES['rental']
    stay = bool(booking.check_in_date)
    requester = details.get('full_name') or row['reserved_by'] or MISSING

    def field(label, value=None):
        rendered = str(value) if value is not None and value != '' else MISSING
        return {'label': label, 'value': rendered, 'wide': len(rendered) > 160}

    def section(title, fields, choices=None):
        choices = choices or []
        # Render Others once: its saved description belongs beside the checkbox.
        if rental and any(choice['label'] == 'Others' for choice in choices):
            other_field = next((item for item in fields if item['label'] == 'Others'), None)
            for choice in choices:
                if choice['label'] == 'Others':
                    value = other_field['value'] if other_field else ''
                    choice.update(write_in=True, value=value if value != MISSING or choice['checked'] else '')
            fields = [item for item in fields if item['label'] != 'Others']
        return {'title': title, 'fields': fields, 'choices': choices}

    sections = [section('1. Client / Requestor Information', [
        field('Name of Requestor', requester), field('Organization / Office', details.get('organization')),
        field('Address', details.get('address')), field('Contact Number', details.get('contact_number') or (booking.user.contact_number if booking.user else '')),
        field('Email Address', details.get('email') or (booking.user.email if booking.user else '')),
    ])]
    purpose = details.get('purpose') or row['purpose']
    if rental:
        sections.append(section('2. Event Information', [field('Name of Event / Activity', details.get('event_name')),
            field('Nature of Event', purpose), field('Expected Number of Participants', details.get('attendees'))]))
        category = booking.facility.facility_type if booking.facility else ''
        sections.append(section('3. Facility Requested', [field('Others', row['facility'])] if category not in ('covered_court','function_hall') else [], [
            {'label': label, 'checked': category == code if code != 'other' else bool(category and category not in ('covered_court', 'function_hall'))}
            for code, label in (('covered_court', 'Covered Court'), ('function_hall', 'Hotel Function Hall'), ('other', 'Others'))]))
        sections.append(section('4. Schedule of Use', [
            field('Event Date', booking.booking_date.strftime('%b %d, %Y') if booking.booking_date else None),
            field('Start Time', time_label(booking.start_time)), field('End Time', time_label(booking.end_time))]))
        chosen = details.get('additional_requirements') or []
        sections.append(section('5. Equipment / Additional Requirements', [
            field('Others', details.get('other_requirements'))],
            [{'label': label, 'checked': label in chosen, 'detail': ''} for label in ('Sound System','Projector')]+[
                {'label':'Tables and Chairs','checked':bool({'Tables','Chairs'} & set(chosen)),
                 'detail': 'Chairs only' if 'Chairs' in chosen and 'Tables' not in chosen else 'Tables only' if 'Tables' in chosen and 'Chairs' not in chosen else ''},
                *[{'label':label,'checked':label in chosen,'detail':''} for label in ('Stage','Extension Cords','Others')]]))
    else:
        schedule = [field('Facility', row['facility']), field('Booking Status', row['status_label'])]
        if stay:
            schedule += [field('Check-in', booking.check_in_date.strftime('%b %d, %Y')),
                field('Check-out', booking.check_out_date.strftime('%b %d, %Y') if booking.check_out_date else None),
                field('Check-in Time', time_label(details.get('check_in_time'))),
                field('Check-out Time', time_label(details.get('check_out_time'))), field('Room / Unit', row['room']),
                field('Nights', quote.get('nights')), field('Guests', details.get('attendees')),
                field('Adults', details.get('adults')), field('Children', details.get('children'))]
        else:
            schedule += [field('Reservation Date', row['date']), field('Start Time', time_label(booking.start_time)),
                field('End Time', time_label(booking.end_time)), field('Participants', details.get('attendees'))]
        schedule += [field('Purpose of Stay' if stay else 'Purpose', purpose), field('Additional Notes', details.get('notes'))]
        sections.append(section('Reservation Schedule', schedule))
    if rental:
        # Quote fees are not typed as equipment. Do not guess a classification.
        sections.append(section('6. Rental Fees', [
            field('Facility Fee', peso(quote.get('rental_amount', quote.get('base_amount')))),
            field('Equipment Fee'), field('Other Charges', peso(quote.get('fee_amount'))),
            field('Total Amount', peso(quote.get('rental_total', booking.total_amount)))]))
    else:
        sections.append(section('Reservation Cost Summary', [
        field('Base Rental Fee', peso(quote.get('base_amount'))), field('Additional Charges', peso(quote.get('fee_amount'))),
        field('Discount', peso(quote.get('discount_amount'))), field('Rental Total', peso(quote.get('rental_total'))),
        field('Damage Deposit', peso(quote.get('deposit_amount'))), field('Total Amount', peso(booking.total_amount)),
        field('Remaining Balance', peso(row['amount_due']))]))
    if rental:
        configuration = settings.BOOKING_SLIP_SIGNATORIES
        reviewer, official = configuration.get('reviewer', {}), configuration.get('approver', {})
        official_title = official.get('title') or MISSING
        if str(official_title).strip().casefold() == 'super admin':
            official_title = MISSING
        signatories = [
            {'label':'Requested By','name':requester,'role':''},
            {'label':'Reviewed By (Campus Admin / Facility In-Charge)','name':reviewer.get('name') or MISSING,'role':reviewer.get('title') or ''},
            {'label':'Approved By','name':official.get('name') or MISSING,'role':official_title},
        ]
    else:
        approval = details.get('approval') or {}
        approver = approval.get('by') or {}
        approval_event = AccountActivity.objects.filter(module='Facility Bookings', metadata__booking_id=booking.pk,
            activity_type__in=('booking_approved', 'booking_auto_approved')).order_by('-created_at').first()
        approval_role = approval_event.role if approval_event and approver.get('name') else ''
        if not approval_role and isinstance(approver.get('id'), int):
            approval_role = User.objects.filter(pk=approver['id']).values_list('role', flat=True).first() or ''
        # No configured facility reviewer: do not infer one from payment/inspection staff.
        signatories = [
            {'label': 'Requested By', 'name': requester, 'role': (booking.user.get_user_type_display() or booking.user.role) if booking.user else 'Client'},
            {'label': 'Reviewed By', 'name': MISSING, 'role': 'Personnel In-charge'},
            {'label': 'Approved By', 'name': approver.get('name') or MISSING, 'role': approval_role or MISSING},
        ]
    payments = [p for p in booking.payments.all() if p.payment_status == FacilityPayment.PAYMENT_PAID]
    payments = sorted(payments, key=lambda p: (p.created_at, p.pk))
    if rental:
        # Paper form lists only OR/date/amount; financial status stays in Payment.
        payment_fields = []
        for payment in payments:
            payment_fields += [field('Official Receipt No.', payment.official_receipt_no),
                field('Date Paid', local_stamp(payment.paid_at)), field('Amount Paid', peso(payment.paid_amount))]
        if not payments:
            payment_fields = [field('Official Receipt No.'),field('Date Paid'),field('Amount Paid',peso(row['paid_amount']))]
    else:
        payment_fields = [field('Payment Status', 'Paid' if row['payment_status'] == 'paid' else 'Unpaid / Pending Payment'),
            field('Amount Paid', peso(row['paid_amount']))]
        if payments:
            for payment in payments:
                payment_fields += [field('Official Receipt No.', payment.official_receipt_no), field('Receipt Amount', peso(payment.paid_amount)),
                    field('Date Paid', local_stamp(payment.paid_at))]
        else:
            payment_fields += [field('Official Receipt No.'), field('Date Paid')]
    sections.append(section('8. Payment Details' if rental else 'Payment Details', payment_fields))
    return {'title': title, 'institution': INSTITUTION, 'campus': CAMPUS, 'id': booking.pk,
        'requested_at': local_stamp(booking.created_at), 'status': row['status_label'], 'sections': sections,
        'signatory_heading': '7. Approval' if rental else 'Approval / Signatories',
        'signatories': signatories, 'logo_url': '', 'rental': rental}


def slip_values(slip):
    """Compatibility flat values; all renderers read the same saved content."""
    values = [('Booking No.', slip['id']), ('Date of Request' if slip['rental'] else 'Date Requested', slip['requested_at'])]
    for section in slip['sections']:
        values += [(field['label'], field['value']) for field in section['fields']]
        values += [(choice['label'], 'Selected' if choice['checked'] else 'Not selected') for choice in section['choices']]
        values += [(section['title'] + ' - Other details', choice['value']) for choice in section['choices'] if choice.get('write_in')]
    values += [(s['label'], s['name'] + ' - ' + s['role']) for s in slip['signatories']]
    return values
