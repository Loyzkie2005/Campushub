"""Read-only mobile catalog over the existing service-configured facilities."""
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from api.models import Facility
from api.views import serialize_facility
from .services.catalog import service_labels, service_resources_q
from .services.service_configuration import LEASE_TYPES, PRICING, SCHEDULING_METHODS


def active_services():
    return Facility.objects.filter(
        service_resources_q(), is_archived=False,
        availability_status=Facility.STATUS_AVAILABLE,
    ).annotate(configured_room_count=Count('rooms')).order_by('facility_name', 'pk')


def serialize_service(resource):
    """Reuse catalog fields; publish an allowlist rather than internal workflow JSON."""
    source = serialize_facility(resource)
    result = {key: source[key] for key in (
        'id', 'name', 'facility_type', 'booking_mode', 'location', 'description',
        'requirements', 'terms_conditions', 'images', 'image_url', 'price_label',
    )}
    category, request_type = service_labels(resource)
    result.update(category_label=category, request_type=request_type, status='active')
    workflow = resource.workflow_config if isinstance(resource.workflow_config, dict) else {}
    config = workflow.get('service', {})
    config = config if isinstance(config, dict) else {}
    information = []

    def add(label, value):
        if value not in (None, '', [], {}):
            information.append({'label': label, 'value': str(value)})

    add('Pricing', result['price_label'])
    add('Pricing details', config.get('custom_pricing_description'))
    for item in config.get('pricing_items', []) if isinstance(config.get('pricing_items'), list) else []:
        if isinstance(item, dict) and item.get('active') is True:
            basis = 'sample' if item.get('charging_basis') == 'sample' else 'analysis'
            add(str(item.get('name', 'Analysis')), f"₱{item.get('fee', '')} per {basis}")
    add('Turnaround', workflow.get('turnaround_information'))
    if resource.facility_type == 'food_analysis' and config.get('sample_acceptance_required'):
        add('Sample submission', 'Sample submission is required. The office verifies acceptance.')
    add('Assessment', workflow.get('assessment_service_type'))
    add('Scheduling', SCHEDULING_METHODS.get(config.get('scheduling_method')))
    for item in config.get('assessment_dates', []) if isinstance(config.get('assessment_dates'), list) else []:
        if isinstance(item, dict):
            add('Assessment date', item.get('date'))
    spaces = config.get('lease_space_types', [])
    if isinstance(spaces, list):
        add('Lease spaces', ', '.join(LEASE_TYPES[key] for key in spaces if key in LEASE_TYPES))
    details = config.get('lease_space_details', {})
    if isinstance(details, dict):
        for key, item in details.items():
            if not isinstance(item, dict) or key not in LEASE_TYPES:
                continue
            title = LEASE_TYPES[key]
            add(title, item.get('location'))
            method = item.get('pricing_method')
            if method in PRICING:
                add(f'{title} pricing', f"₱{item['rate']} · {PRICING[method]}" if item.get('rate') else PRICING[method])
            for field, label in (('regular_term_rate', 'Regular term'), ('midyear_rate', 'Midyear'),
                                 ('available_area', 'Available area (sqm)'), ('standard_area', 'Standard area (sqm)'),
                                 ('electricity_arrangement', 'Electricity'), ('internet_arrangement', 'Internet'),
                                 ('water_charge', 'Water charge'), ('utility_conditions', 'Utilities'),
                                 ('pricing_description', 'Pricing details')):
                add(f'{title} — {label}', item.get(field))
    hours = workflow.get('operating_hours') if config.get('availability_enabled') else None
    if isinstance(hours, dict):
        for day, period in hours.items():
            if isinstance(period, dict) and period.get('open') and period.get('close'):
                add(day.title(), f"{period['open']} – {period['close']}")
    else:
        add('Availability', 'Contact the office for service arrangements.')
    result['information'] = information
    # Catalog availability never implies that a sample, assessment or lease is approved.
    result['online_requests_available'] = False
    return result


@require_GET
def service_list(request):
    return JsonResponse({'services': [serialize_service(row) for row in active_services()]})


@require_GET
def service_detail(request, service_id):
    return JsonResponse({'service': serialize_service(get_object_or_404(active_services(), pk=service_id))})
