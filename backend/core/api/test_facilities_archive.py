from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, Facility


class FacilityArchiveAndRestoreAPITests(TestCase):
    password = "CampusHub1!"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS campushub_facility (
                    id varchar(30) PRIMARY KEY,
                    facility_name varchar(150) NOT NULL,
                    facility_type varchar(40) DEFAULT 'other',
                    location varchar(180) DEFAULT '',
                    description text NULL,
                    capacity integer DEFAULT 0,
                    rate numeric(10,2) DEFAULT 0,
                    price_type varchar(20) DEFAULT 'hour',
                    booking_mode varchar(20) DEFAULT 'room',
                    rooms_units integer NULL,
                    room_type varchar(120) NULL,
                    amenities jsonb DEFAULT '[]'::jsonb,
                    slot_details varchar(120) NULL,
                    requirements text NULL,
                    terms_conditions text NULL,
                    workflow_config jsonb DEFAULT '{}'::jsonb,
                    image_url text NULL,
                    status varchar(20) DEFAULT 'available',
                    is_archived boolean NOT NULL DEFAULT false,
                    created_by bigint NULL,
                    created_at timestamp with time zone DEFAULT NOW(),
                    updated_at timestamp with time zone DEFAULT NOW()
                );
                ALTER TABLE campushub_facility ADD COLUMN IF NOT EXISTS is_archived boolean NOT NULL DEFAULT false;
                CREATE TABLE IF NOT EXISTS campushub_booking (
                    id varchar(30) PRIMARY KEY,
                    user_id bigint NULL,
                    facility_id varchar(30) NULL,
                    room_id uuid NULL,
                    purpose text NULL,
                    booking_date date NULL,
                    start_time time NULL,
                    end_time time NULL,
                    check_in_date date NULL,
                    check_out_date date NULL,
                    total_amount numeric(10,2) DEFAULT 0,
                    status varchar(30) DEFAULT 'pending',
                    created_at timestamp with time zone DEFAULT NOW(),
                    updated_at timestamp with time zone DEFAULT NOW()
                );
                """
            )

    def setUp(self):
        dept = Department.objects.create(name="Facilities Operations", code="FAC-OPS")
        self.facility_admin = User.objects.create_user(
            username="facility-admin",
            password=self.password,
            role="Facilities Admin",
            department=dept,
            is_staff=True,
        )
        sync_user_admin_permissions(self.facility_admin)

        self.student = User.objects.create_user(
            username="student-user",
            password=self.password,
            role="Student",
        )
        sync_user_admin_permissions(self.student)

        self.facility = Facility.objects.create(
            id="FAC-TEST-01",
            facility_name="Function Hall Alpha",
            facility_type=Facility.TYPE_FUNCTION_HALL,
            location="Building A",
            rate=Decimal("1500.00"),
            price_type="hour",
            booking_mode="slot",
            availability_status=Facility.STATUS_AVAILABLE,
            is_archived=False,
        )

    def test_facility_archive_and_restore_workflow(self):
        self.client.force_login(self.facility_admin)

        # 1. Archive facility
        resp = self.client.post(reverse("facilities_archive", args=[self.facility.id]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.facility.refresh_from_db()
        self.assertTrue(self.facility.is_archived)

        # 2. Public API hides archived facility
        public_resp = self.client.get(reverse("facilities_list"))
        self.assertEqual(public_resp.status_code, 200)
        facility_ids = [f["id"] for f in public_resp.json().get("facilities", [])]
        self.assertNotIn(self.facility.id, facility_ids)

        # 3. Restore facility
        restore_resp = self.client.post(reverse("facilities_restore", args=[self.facility.id]))
        self.assertEqual(restore_resp.status_code, 200)
        self.facility.refresh_from_db()
        self.assertFalse(self.facility.is_archived)

        # 4. Public API shows restored facility
        public_resp2 = self.client.get(reverse("facilities_list"))
        facility_ids2 = [f["id"] for f in public_resp2.json().get("facilities", [])]
        self.assertIn(self.facility.id, facility_ids2)

    def test_permanent_facility_deletion_is_disabled(self):
        self.client.force_login(self.facility_admin)
        del_resp = self.client.post(reverse("facilities_delete", args=[self.facility.id]))
        self.assertEqual(del_resp.status_code, 405)
        self.assertTrue(Facility.objects.filter(id=self.facility.id).exists())

    def test_unauthorized_archive_and_restore_rejected(self):
        self.client.force_login(self.student)
        # Student cannot archive (HTTP 403)
        resp1 = self.client.post(reverse("facilities_archive", args=[self.facility.id]))
        self.assertEqual(resp1.status_code, 403)

        # Student cannot restore (HTTP 403)
        resp2 = self.client.post(reverse("facilities_restore", args=[self.facility.id]))
        self.assertEqual(resp2.status_code, 403)

    def test_archived_facility_preserves_historical_bookings(self):
        booking = Booking.objects.create(
            id="BKG-TEST-01",
            user_id=self.student.id,
            facility=self.facility,
            purpose="Annual Academic Symposium",
            total_amount=Decimal("3000.00"),
            status="confirmed",
        )

        self.client.force_login(self.facility_admin)
        resp = self.client.post(reverse("facilities_archive", args=[self.facility.id]))
        self.assertEqual(resp.status_code, 200)
        self.facility.refresh_from_db()
        self.assertTrue(self.facility.is_archived)

        # Historical booking is preserved and still links to the archived facility
        booking.refresh_from_db()
        self.assertEqual(booking.facility_id, self.facility.id)
        self.assertEqual(booking.facility.facility_name, "Function Hall Alpha")
        self.assertEqual(booking.status, "confirmed")
