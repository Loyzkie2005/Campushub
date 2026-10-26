"""Real-record admin workflow separation; fixtures stay in the test database."""
import json
import os
from datetime import date, time, timedelta
from pathlib import Path

from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, FacilityFeedback, FacilityPayment, Room
from modules.facilities.services.catalog import service_resources_q


class ServiceNavigationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        existing = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment, FacilityFeedback):
                if model._meta.db_table not in existing:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.owner = User.objects.create_superuser(username="service-owner", role="Super Admin")
        self.facilities_admin = User.objects.create_user(username="service-facilities", role="Facilities Admin", is_staff=True)
        self.marketplace_admin = User.objects.create_user(username="service-marketplace", role="Marketplace Admin", is_staff=True)
        sync_user_admin_permissions(self.facilities_admin)
        sync_user_admin_permissions(self.marketplace_admin)
        self.requester = CampusHubUser.objects.create(username="service-requester", first_name="Real", last_name="Requester", password_hash="unused", user_type="student", role="User")
        self.physical = Facility.objects.create(id="PHYSICAL", facility_name="Physical Test Court", facility_type="covered_court", booking_mode="slot")
        self.lab = Facility.objects.create(id="LAB", facility_name="Lab Test Service", facility_type="food_analysis", booking_mode="service", price_type="service")
        self.training = Facility.objects.create(id="TRAINING", facility_name="Training Test Service", facility_type="training_kitchen", booking_mode="assessment")
        self.lease = Facility.objects.create(id="LEASE", facility_name="Lease Test Service", facility_type="lease_space", booking_mode="lease", price_type="monthly")
        for facility in (self.physical, self.lab, self.training, self.lease):
            Booking.objects.create(id=f"REQUEST-{facility.pk}", facility=facility, user=self.requester,
                booking_date=date.today(), start_time=time(9), end_time=time(10), purpose="[reservation] Real request details", status="pending")
        self.client.force_login(self.owner)

    def test_catalog_and_normal_bookings_are_separate(self):
        services = self.client.get(reverse("admin_services_page"))
        self.assertEqual(services.status_code, 200)
        self.assertEqual({f.pk for f in services.context["facilities"]}, {"LAB", "TRAINING", "LEASE"})
        for label in ("Service Name", "Service Category", "Pricing", "Request Type", "Assessment Registration", "Add Service"):
            self.assertContains(services, label)
        physical = self.client.get(reverse("admin_facility_page"))
        self.assertEqual({f.pk for f in physical.context["facilities"]}, {"PHYSICAL"})
        self.assertNotContains(physical, '<option value="food_analysis">')
        bookings = self.client.get(reverse("admin_bookings_page"))
        self.assertEqual([row["id"] for row in bookings.context["booking_requests"]], ["REQUEST-PHYSICAL"])
        calendar = self.client.get(reverse("admin_calendar_page"))
        self.assertEqual({f.pk for f in calendar.context["facilities"]}, {"PHYSICAL"})
        self.assertEqual([row["facility_id"] for row in calendar.context["calendar_data"]["events"]], ["PHYSICAL"])

    def test_request_list_filters_and_details_use_real_data(self):
        response = self.client.get(reverse("admin_service_requests_page"))
        self.assertEqual({b.pk for b in response.context["request_page"]}, {"REQUEST-LAB", "REQUEST-TRAINING", "REQUEST-LEASE"})
        self.assertContains(response, "Real Requester")
        self.assertContains(response, "Real request details")
        self.assertContains(response, "Assigned Office / Personnel")
        self.assertNotContains(response, "REQUEST-PHYSICAL")
        filtered = self.client.get(reverse("admin_service_requests_page"), {"q": "Lab Test", "status": "pending"})
        self.assertEqual([b.pk for b in filtered.context["request_page"]], ["REQUEST-LAB"])
        self.assertContains(self.client.get(reverse("admin_service_requests_page"), {"status": "completed"}), "No service requests found.")
        self.assertEqual(self.client.post(reverse("admin_service_requests_page")).status_code, 405)

    def test_final_sidebar_structure_and_active_services(self):
        response = self.client.get(reverse("admin_services_page"))
        sidebar = response.content.decode().split('<nav class="sidebar-nav">')[1].split('</nav>')[0]
        expected = ["Marketplace", "User Management", "Facilities", "Services", "Reports", "System Settings"]
        import re
        self.assertEqual(re.findall(r'<span class="nav-group-title">([^<]+)</span>', sidebar), expected)
        self.assertIn(reverse("admin_sellers_page"), sidebar)
        self.assertNotIn("Backup &amp; Restore", sidebar)
        self.assertNotIn("Backup & Restore", sidebar)
        self.assertIn('href="/admin-services/" class="sidebar-item active" aria-current="page"', sidebar)

    def test_role_visibility_and_server_authorization(self):
        for user, allowed in ((self.facilities_admin, True), (self.marketplace_admin, False)):
            self.client.force_login(user)
            for route in ("admin_services_page", "admin_service_requests_page"):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200 if allowed else 403)
        read_only = User.objects.create_user(username="services-readonly", role="Service Reader", is_staff=True)
        read_only.user_permissions.add(Permission.objects.get(codename="can_view_facilities", content_type__app_label="accounts"))
        self.client.force_login(read_only)
        response = self.client.get(reverse("admin_services_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="addFacilityBtn" hidden')
        sidebar = response.content.decode().split('<nav class="sidebar-nav">')[1].split('</nav>')[0]
        self.assertIn(reverse("admin_services_page"), sidebar)
        self.assertNotIn(reverse("admin_service_requests_page"), sidebar)
        self.assertEqual(self.client.get(reverse("admin_service_requests_page")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("admin_services_page")).status_code, 302)

    def test_service_cannot_be_created_as_normal_reservation(self):
        payload = {"facility_id": self.lab.pk, "type": "reservation", "date": date.today().isoformat(), "start": "09:00", "end": "10:00", "reserved_by": "Requester"}
        before = Booking.objects.count()
        response = self.client.post(reverse("bookings_create"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("service request workflow", response.json()["error"])
        self.assertEqual(Booking.objects.count(), before)
        payload["facility_id"] = self.physical.pk
        self.physical.slots = "11:00-12:00"
        self.physical.save()
        payload.update(start="11:00", end="12:00", date=(date.today() + timedelta(days=3)).isoformat(),
                       client_id=self.requester.pk, contact_number="09171234567", purpose="Client practice", attendees=10)
        self.assertEqual(self.client.post(reverse("bookings_create"), data=json.dumps(payload), content_type="application/json").status_code, 201)

    def test_legacy_modes_and_types_are_not_misclassified(self):
        legacy = Facility.objects.create(id="LEGACY", facility_name="Legacy Service", facility_type="other", booking_mode="direct")
        self.lab.booking_mode = "room"
        self.lab.save()
        self.assertTrue(Facility.objects.filter(service_resources_q(), pk=legacy.pk).exists())
        self.assertTrue(Facility.objects.filter(service_resources_q(), pk=self.lab.pk).exists())
        self.assertFalse(Facility.objects.filter(service_resources_q(), pk=self.physical.pk).exists())

    def test_empty_catalog_and_paginated_requests(self):
        for index in range(21):
            Booking.objects.create(id=f"EXTRA-{index}", facility=self.lab, user=self.requester, status="approved")
        response = self.client.get(reverse("admin_service_requests_page"), {"status": "approved"})
        self.assertEqual(len(response.context["request_page"]), 20)
        self.assertTrue(response.context["request_page"].has_next())
        next_page = self.client.get(reverse("admin_service_requests_page"), {"status": "approved", "page": "2"})
        self.assertEqual(len(next_page.context["request_page"]), 1)
        Booking.objects.exclude(facility=self.physical).delete()
        Facility.objects.filter(service_resources_q()).delete()
        self.assertContains(self.client.get(reverse("admin_services_page")), "No services added yet.")
        self.assertContains(self.client.get(reverse("admin_service_requests_page")), "No service requests found.")

    def test_export_isolated_browser_fixtures(self):
        destination = os.environ.get("SERVICE_REVIEW_DIR")
        if not destination:
            return
        root = Path(destination)
        root.mkdir(parents=True, exist_ok=True)
        for route, filename in (("admin_services_page", "services.html"), ("admin_service_requests_page", "requests.html")):
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 200)
            (root / filename).write_bytes(response.content)
