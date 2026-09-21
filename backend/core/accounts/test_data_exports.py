import io
import json
import uuid
import zipfile
from decimal import Decimal
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.template.loader import render_to_string
from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.models import Permission
from django.urls import reverse

from api.models import (
    Booking,
    Facility,
    FacilityPayment,
    MarketplaceOrder,
    Product,
    Room,
    SellerRequest,
)
from accounts.models import AccountActivity, Role, User
from accounts.role_permissions import (
    ADMIN_PERMISSION_CODENAMES,
    BUILTIN_ROLE_PERMISSIONS,
    set_role_permissions,
    sync_user_admin_permissions,
)


class RoleScopedDataExportTests(TestCase):
    password = "CampusHub1!"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS campushub_rooms (
                    id uuid PRIMARY KEY,
                    facility_id varchar(30) NULL,
                    room_name varchar(150) NULL,
                    room_type varchar(50) NULL,
                    descriptions text NULL,
                    capacity integer DEFAULT 0,
                    price numeric(10,2) DEFAULT 0,
                    status varchar(20) DEFAULT 'available',
                    created_at timestamp with time zone DEFAULT NOW(),
                    updated_at timestamp with time zone DEFAULT NOW()
                );
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
                CREATE TABLE IF NOT EXISTS campushub_facility_payment (
                    id varchar(30) PRIMARY KEY,
                    booking_id varchar(30) NULL,
                    paid_amount numeric(10,2) DEFAULT 0,
                    payment_status varchar(20) DEFAULT 'unpaid',
                    official_receipt_no varchar(100) NULL,
                    paid_at timestamp with time zone NULL,
                    created_at timestamp with time zone DEFAULT NOW(),
                    updated_at timestamp with time zone DEFAULT NOW()
                );
                """
            )

    def setUp(self):
        self.roles = {
            name: Role.objects.get_or_create(
                role_name=name,
                defaults={"description": f"Built-in {name} role."},
            )[0]
            for name in ("Super Admin", "Marketplace Admin", "Facilities Admin")
        }
        set_role_permissions(self.roles["Super Admin"], list(ADMIN_PERMISSION_CODENAMES))
        set_role_permissions(
            self.roles["Marketplace Admin"],
            list(BUILTIN_ROLE_PERMISSIONS["Marketplace Admin"]),
        )
        set_role_permissions(
            self.roles["Facilities Admin"],
            list(BUILTIN_ROLE_PERMISSIONS["Facilities Admin"]),
        )

        self.super_admin = User.objects.create_superuser(
            username="export-super",
            email="export-super@example.com",
            password=self.password,
            role="Super Admin",
        )
        self.marketplace_admin = User.objects.create_user(
            username="export-marketplace",
            email="export-marketplace@example.com",
            password=self.password,
            role="Marketplace Admin",
            is_staff=True,
        )
        self.facilities_admin = User.objects.create_user(
            username="export-facilities",
            email="export-facilities@example.com",
            password=self.password,
            role="Facilities Admin",
            is_staff=True,
        )
        sync_user_admin_permissions(self.super_admin)
        sync_user_admin_permissions(self.marketplace_admin)
        sync_user_admin_permissions(self.facilities_admin)

    @staticmethod
    def archive(response):
        return zipfile.ZipFile(io.BytesIO(response.content))

    def test_backup_permissions_and_sidebar_are_super_admin_only(self):
        for user in (self.marketplace_admin, self.facilities_admin):
            for code in ("can_export_marketplace_data", "can_export_facility_data",
                         "can_system_backup", "can_restore_system_backup"):
                self.assertFalse(user.has_perm(f"accounts.{code}"))
            sidebar = render_to_string("partials/admin_sidebar.html", {
                "user": user, "perms": PermWrapper(user),
            })
            self.assertNotIn(reverse("admin_backup_page"), sidebar)
            self.assertNotIn(reverse("admin_marketplace_export_page"), sidebar)
            self.assertNotIn(reverse("admin_facility_export_page"), sidebar)

    def test_backup_urls_are_blocked_even_with_stale_direct_grants(self):
        permissions = Permission.objects.filter(
            content_type__app_label="accounts", content_type__model="role",
            codename__in=("can_export_marketplace_data", "can_export_facility_data",
                          "can_system_backup", "can_restore_system_backup"),
        )
        for user in (self.marketplace_admin, self.facilities_admin):
            user.user_permissions.add(*permissions)
            self.client.force_login(user)
            for page in ("admin_marketplace_export_page", "admin_facility_export_page", "admin_backup_page"):
                self.assertEqual(self.client.get(reverse(page)).status_code, 403)
            for download in ("admin_marketplace_export_download", "admin_facility_export_download"):
                self.assertEqual(self.client.post(reverse(download)).status_code, 403)
            for action in ("create_backup", "restore_upload", "download"):
                self.assertEqual(self.client.post(reverse("admin_backup_page"), {"action": action}).status_code, 403)

    def test_marketplace_export_contains_only_whitelisted_domain_data(self):
        seller_request = SellerRequest.objects.create(
            user=self.marketplace_admin,
            student_id=self.marketplace_admin.username,
            full_name="Marketplace Export Admin",
            contact_number="09123456789",
            product_type="Campus supplies",
            status=SellerRequest.STATUS_APPROVED,
        )
        product = Product.objects.create(
            seller=self.marketplace_admin,
            name="Export Notebook",
            category="School Supplies",
            price=Decimal("45.00"),
            stock=12,
            customization_enabled=True,
            customization_options=[{
                "name": "Size",
                "options": [{"name": "A5", "stock": 12, "extra_price": "0.00"}],
            }],
            approval_status=Product.STATUS_APPROVED,
        )
        MarketplaceOrder.objects.create(
            product=product,
            buyer_name="Test Buyer",
            buyer_email="buyer@example.com",
            product_name=product.name,
            category=product.category,
            seller_name="Marketplace Export Admin",
            quantity=1,
            unit_price=product.price,
            total_price=product.price,
        )
        before = (Product.objects.count(), MarketplaceOrder.objects.count(), SellerRequest.objects.count())

        self.client.force_login(self.super_admin)
        response = self.client.post(reverse("admin_marketplace_export_download"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        with self.archive(response) as archive:
            names = set(archive.namelist())
            self.assertIn("products.json", names)
            self.assertIn("product_variants.csv", names)
            self.assertIn("orders.json", names)
            self.assertIn("order_items.json", names)
            self.assertIn("seller_requests.json", names)
            self.assertNotIn("facilities.json", names)
            self.assertNotIn("bookings.json", names)
            combined = b"".join(archive.read(name) for name in names).decode("utf-8")
            self.assertNotIn(self.marketplace_admin.password, combined)
            self.assertNotIn("password_hash", combined)
            manifest = json.loads(archive.read("manifest.json"))
            self.assertFalse(manifest["restorable"])
            self.assertEqual(manifest["export_scope"], "marketplace")

        self.assertEqual(
            before,
            (Product.objects.count(), MarketplaceOrder.objects.count(), SellerRequest.objects.count()),
        )
        self.assertTrue(
            AccountActivity.objects.filter(
                username=self.super_admin.username,
                activity_type="data_export",
                result=AccountActivity.RESULT_SUCCESS,
            ).exists()
        )
        self.assertEqual(seller_request.status, SellerRequest.STATUS_APPROVED)

    def test_facility_export_contains_only_whitelisted_domain_data(self):
        facility = Facility.objects.create(
            id="FAC-EXPORT-1",
            facility_name="Export Hall",
            facility_type=Facility.TYPE_FUNCTION_HALL,
            booking_mode="slot",
            availability_status=Facility.STATUS_AVAILABLE,
        )
        room = Room.objects.create(
            id=uuid.uuid4(),
            facility=facility,
            room_name="Main Hall",
            capacity=100,
            price=Decimal("1000.00"),
        )
        booking = Booking.objects.create(
            id="BKG-EXPORT-1",
            facility=facility,
            room_id=room.id,
            purpose="[maintenance] Lighting inspection",
            total_amount=Decimal("1000.00"),
            status=Booking.STATUS_APPROVED,
        )
        FacilityPayment.objects.create(
            id="PAY-EXPORT-1",
            booking=booking,
            paid_amount=Decimal("1000.00"),
            payment_status=FacilityPayment.PAYMENT_PAID,
            official_receipt_no="OR-1001",
        )
        before = (Facility.objects.count(), Booking.objects.count(), FacilityPayment.objects.count())

        self.client.force_login(self.super_admin)
        response = self.client.post(reverse("admin_facility_export_download"))

        self.assertEqual(response.status_code, 200)
        with self.archive(response) as archive:
            names = set(archive.namelist())
            self.assertIn("facilities.json", names)
            self.assertIn("rooms.csv", names)
            self.assertIn("bookings.json", names)
            self.assertIn("schedules.json", names)
            self.assertIn("facility_payments.json", names)
            self.assertNotIn("products.json", names)
            self.assertNotIn("orders.json", names)
            schedule_rows = json.loads(archive.read("schedules.json"))
            self.assertEqual(schedule_rows[0]["schedule_type"], "maintenance")

        self.assertEqual(
            before,
            (Facility.objects.count(), Booking.objects.count(), FacilityPayment.objects.count()),
        )

    @patch("accounts.backup_service.restore_from_upload")
    @patch("accounts.backup_service.create_backup")
    def test_super_admin_backup_and_restore_remain_available(self, create_backup, restore_upload):
        create_backup.return_value = {
            "success": True,
            "filename": "campushub_postgres_test.sql",
            "size_display": "1 KB",
        }
        restore_upload.return_value = {
            "success": True,
            "message": "Database restored successfully.",
        }
        self.client.force_login(self.super_admin)

        page = self.client.get(reverse("admin_backup_page"))
        backup_response = self.client.post(
            reverse("admin_backup_page"),
            {"action": "create_backup", "backup_type": "full"},
        )
        restore_response = self.client.post(
            reverse("admin_backup_page"),
            {
                "action": "restore_upload",
                "backup_file": SimpleUploadedFile("approved.sql", b"-- approved backup"),
            },
        )

        self.assertEqual(page.status_code, 200)
        self.assertEqual(backup_response.status_code, 302)
        self.assertEqual(restore_response.status_code, 302)
        create_backup.assert_called_once_with("full")
        restore_upload.assert_called_once()
        self.assertTrue(
            AccountActivity.objects.filter(
                username=self.super_admin.username,
                activity_type="system_restore",
                result=AccountActivity.RESULT_SUCCESS,
            ).exists()
        )
