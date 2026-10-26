"""Admin views over existing service-configured facilities and requests."""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.http import require_GET

from accounts.role_permissions import admin_read_permissions
from api.models import Booking, Facility
from modules.facilities.services.catalog import service_labels, service_resources_q


@login_required(login_url="admin_login_page")
@admin_read_permissions("can_view_facilities", "can_manage_facilities")
def admin_services_page(request):
    # Reuse the existing editor, archive/restore actions and validated write API.
    from accounts.views import admin_facility_page
    return admin_facility_page(request, services=True)


@login_required(login_url="admin_login_page")
@admin_read_permissions("can_view_bookings", "can_manage_bookings", "can_approve_bookings", "can_record_facility_payment")
@require_GET
def admin_service_requests_page(request):
    from accounts.views import _booking_display_fields, get_notification_context

    requests = Booking.objects.filter(service_resources_q("facility__")).select_related("facility", "user")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().lower()
    service_id = request.GET.get('service', '').strip()
    if service_id:
        requests = requests.filter(facility_id=service_id)
    if query:
        from django.db.models import Q
        requests = requests.filter(Q(id__icontains=query) | Q(facility__facility_name__icontains=query)
            | Q(user__username__icontains=query) | Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query))
    if status in dict(Booking.STATUS_CHOICES):
        requests = requests.filter(status=status)
    page = Paginator(requests.order_by("-created_at", "id"), 20).get_page(request.GET.get("page"))
    for booking in page:
        _, booking.requester_display, booking.purpose_display = _booking_display_fields(booking)
        _, booking.request_type_display = service_labels(booking.facility)
    return render(request, "facilities/pages/admin_service_requests.html", {
        "page_title": "Service Requests", "active_page": "service_requests", "request_page": page,
        "q": query, "status_filter": status, "status_choices": Booking.STATUS_CHOICES,
        'service_filter': service_id,
        'selected_service': Facility.objects.filter(service_resources_q(),pk=service_id).first() if service_id else None,
        **get_notification_context(user=request.user),
    })
