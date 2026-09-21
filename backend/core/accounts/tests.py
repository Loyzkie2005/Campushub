import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from api.models import (
    CampusHubUser,
    MarketplaceOrder,
    MarketplaceOrderStatusHistory,
    Product,
    SellerRequest,
)
from accounts.models import AccountActivity, AdminTabToken, Department, Role, User
from accounts.role_permissions import (
    ADMIN_PERMISSION_CODENAMES,
    BUILTIN_ROLE_PERMISSIONS,
    permissions_for_role,
    set_role_permissions,
    sync_user_admin_permissions,
    sync_users_for_role,
    user_has_admin_access,
)
from django.db import connection
from modules.reports.models import GeneratedReport
from modules.marketplace.services.order_access import seller_order_queryset


class DomainAnalyticsPermissionTests(TestCase):
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
                CREATE TABLE IF NOT EXISTS campushub_facility_feedback (
                    id varchar(30) PRIMARY KEY,
                    facility_id varchar(30) NULL,
                    user_id bigint NULL,
                    rating integer DEFAULT 0,
                    comment text NULL,
                    created_at timestamp with time zone DEFAULT NOW(),
                    updated_at timestamp with time zone DEFAULT NOW()
                );
                """
            )

    def setUp(self):
        self.marketplace_role = Role.objects.get(role_name="Marketplace Admin")
        self.facilities_role = Role.objects.get(role_name="Facilities Admin")
        self.marketplace_admin = User.objects.create_user(
            username="2023304612",
            password=self.password,
            role="Marketplace Admin",
            is_staff=True,
        )
        self.facilities_admin = User.objects.create_user(
            username="2023304610",
            password=self.password,
            role="Facilities Admin",
            is_staff=True,
        )
        sync_user_admin_permissions(self.marketplace_admin)
        sync_user_admin_permissions(self.facilities_admin)

    def test_builtin_domain_permissions_are_separated(self):
        self.assertTrue(
            self.marketplace_admin.has_perm("accounts.can_view_marketplace_analytics")
        )
        self.assertFalse(
            self.marketplace_admin.has_perm("accounts.can_view_facility_analytics")
        )
        self.assertTrue(self.marketplace_admin.has_perm("accounts.can_manage_sellers"))
        self.assertTrue(
            self.facilities_admin.has_perm("accounts.can_view_facility_analytics")
        )
        self.assertFalse(
            self.facilities_admin.has_perm("accounts.can_view_marketplace_analytics")
        )

    def test_marketplace_admin_routes_and_sidebar_are_permission_scoped(self):
        self.client.force_login(self.marketplace_admin)
        marketplace = self.client.get(reverse("admin_marketplace_analytics_page"))
        facility = self.client.get(reverse("admin_facility_analytics_page"))
        sellers = self.client.get(reverse("admin_sellers_page"))
        seller_api = self.client.get(reverse("marketplace_seller_requests"))
        products = self.client.get(reverse("admin_products_page"))

        self.assertEqual(marketplace.status_code, 200)
        self.assertEqual(facility.status_code, 403)
        self.assertEqual(sellers.status_code, 200)
        self.assertEqual(seller_api.status_code, 200)
        self.assertEqual(products.status_code, 200)

        # Marketplace admin sidebar has domain items
        self.assertContains(products, reverse("admin_products_page"))
        self.assertContains(products, reverse("admin_orders_page"))
        self.assertContains(products, reverse("admin_sellers_page"))
        self.assertContains(products, reverse("admin_marketplace_analytics_page"))
        self.assertContains(products, "Marketplace Reports")
        self.assertContains(products, "System")

        # Marketplace admin sidebar does NOT have facilities, users, or backup
        self.assertNotContains(products, reverse("admin_facility_page"))
        self.assertNotContains(products, reverse("admin_bookings_page"))
        self.assertNotContains(products, reverse("admin_calendar_page"))
        self.assertNotContains(products, reverse("admin_facility_analytics_page"))
        self.assertNotContains(products, reverse("admin_users_page"))
        self.assertNotContains(products, reverse("admin_roles_page"))
        self.assertNotContains(products, reverse("admin_user_monitoring_page"))
        self.assertNotContains(products, reverse("admin_backup_page"))

        self.assertEqual(self.client.get(reverse("admin_messages_page")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin_notifications_page")).status_code, 200)

    def test_facilities_admin_routes_and_sidebar_are_permission_scoped(self):
        self.client.force_login(self.facilities_admin)
        facility = self.client.get(reverse("admin_facility_analytics_page"))
        marketplace = self.client.get(reverse("admin_marketplace_analytics_page"))
        seller_api = self.client.get(reverse("marketplace_seller_requests"))
        facilities_page = self.client.get(reverse("admin_facility_page"))

        self.assertEqual(facility.status_code, 200)
        self.assertEqual(marketplace.status_code, 403)
        self.assertEqual(seller_api.status_code, 403)
        self.assertEqual(facilities_page.status_code, 200)

        # Facilities admin sidebar has domain items
        self.assertContains(facilities_page, reverse("admin_facility_page"))
        self.assertContains(facilities_page, reverse("admin_bookings_page"))
        self.assertContains(facilities_page, reverse("admin_calendar_page"))
        self.assertContains(facilities_page, reverse("admin_facility_analytics_page"))
        self.assertContains(facilities_page, "Facility Reports")
        self.assertContains(facilities_page, "System")

        # Facilities admin sidebar does NOT have marketplace, users, or backup
        self.assertNotContains(facilities_page, reverse("admin_products_page"))
        self.assertNotContains(facilities_page, reverse("admin_orders_page"))
        self.assertNotContains(facilities_page, reverse("admin_sellers_page"))
        self.assertNotContains(facilities_page, reverse("admin_marketplace_analytics_page"))
        self.assertNotContains(facilities_page, reverse("admin_users_page"))
        self.assertNotContains(facilities_page, reverse("admin_roles_page"))
        self.assertNotContains(facilities_page, reverse("admin_user_monitoring_page"))
        self.assertNotContains(facilities_page, reverse("admin_backup_page"))

    def test_disabling_analytics_permission_hides_link_and_blocks_url(self):
        permission = Permission.objects.get(
            codename="can_view_marketplace_analytics",
            content_type__app_label="accounts",
        )
        self.marketplace_role.granted_permissions.remove(permission)
        sync_users_for_role(self.marketplace_role.role_name)
        self.marketplace_admin.refresh_from_db()
        self.client.force_login(self.marketplace_admin)

        response = self.client.get(reverse("admin_sellers_page"))
        blocked = self.client.get(reverse("admin_marketplace_analytics_page"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("admin_marketplace_analytics_page"))
        self.assertEqual(blocked.status_code, 403)

    def test_disabling_facility_analytics_hides_link_and_blocks_url(self):
        permission = Permission.objects.get(
            codename="can_view_facility_analytics",
            content_type__app_label="accounts",
        )
        self.facilities_role.granted_permissions.remove(permission)
        sync_users_for_role(self.facilities_role.role_name)
        self.facilities_admin.refresh_from_db()
        self.client.force_login(self.facilities_admin)

        response = self.client.get(reverse("admin_facility_page"))
        blocked = self.client.get(reverse("admin_facility_analytics_page"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("admin_facility_analytics_page"))
        self.assertEqual(blocked.status_code, 403)

    def test_super_admin_sidebar_and_backend_access(self):
        super_admin = User.objects.create_superuser(
            username="analytics-super-admin",
            email="super@example.com",
            password=self.password,
        )
        super_admin.role = "Super Admin"
        super_admin.save(update_fields=["role"])
        sync_user_admin_permissions(super_admin)
        self.client.force_login(super_admin)

        # Super admin keeps all permissions
        self.assertTrue(super_admin.has_perm("accounts.can_view_marketplace_analytics"))
        self.assertTrue(super_admin.has_perm("accounts.can_view_facility_analytics"))
        self.assertTrue(super_admin.has_perm("accounts.can_manage_sellers"))

        # Super admin has full backend route access
        self.assertEqual(
            self.client.get(reverse("admin_marketplace_analytics_page")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("admin_facility_analytics_page")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("admin_sellers_page")).status_code,
            200,
        )

        dashboard_res = self.client.get(reverse("admin_dashboard_page"))
        self.assertEqual(dashboard_res.status_code, 200)

        users_page = self.client.get(reverse("admin_users_page"))
        self.assertEqual(users_page.status_code, 200)

        # Super Admin sidebar MUST contain standard items
        self.assertContains(users_page, reverse("admin_products_page"))
        self.assertContains(users_page, reverse("admin_orders_page"))
        self.assertContains(users_page, reverse("admin_users_page"))
        self.assertContains(users_page, reverse("admin_roles_page"))
        self.assertContains(users_page, reverse("admin_user_monitoring_page"))
        self.assertContains(users_page, reverse("admin_facility_page"))
        self.assertContains(users_page, reverse("admin_bookings_page"))
        self.assertContains(users_page, reverse("admin_calendar_page"))
        self.assertContains(users_page, reverse("admin_generate_reports_page"))
        self.assertContains(users_page, reverse("admin_messages_page"))
        self.assertContains(users_page, reverse("admin_notifications_page"))
        self.assertContains(users_page, reverse("admin_settings_page"))
        self.assertContains(users_page, reverse("admin_backup_page"))
        self.assertContains(users_page, "Generate Reports")
        self.assertContains(users_page, "System Settings")

        # Super Admin sidebar MUST NOT contain specialized Sellers or Analytics links
        self.assertNotContains(users_page, reverse("admin_sellers_page"))
        self.assertNotContains(users_page, reverse("admin_marketplace_analytics_page"))
        self.assertNotContains(users_page, reverse("admin_facility_analytics_page"))


class DedicatedDomainDashboardTests(TestCase):
    databases = {"default"}
    password = "CampusHubTest123!"

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
                CREATE TABLE IF NOT EXISTS campushub_facility_feedback (
                    id varchar(30) PRIMARY KEY,
                    facility_id varchar(30) NULL,
                    user_id bigint NULL,
                    rating integer DEFAULT 0,
                    comment text NULL,
                    created_at timestamp with time zone DEFAULT NOW(),
                    updated_at timestamp with time zone DEFAULT NOW()
                );
                """
            )

    def setUp(self):
        from api.models import Booking, Facility, FacilityPayment, MarketplaceOrder, Product, SellerRequest

        self.marketplace_admin = User.objects.create_user(
            username="2023304612",
            password=self.password,
            role="Marketplace Admin",
            is_staff=True,
        )
        self.facilities_admin = User.objects.create_user(
            username="2023304610",
            password=self.password,
            role="Facilities Admin",
            is_staff=True,
        )
        self.super_admin = User.objects.create_superuser(
            username="super-admin-dedicated",
            email="superadmin@example.com",
            password=self.password,
        )
        self.super_admin.role = "Super Admin"
        self.super_admin.save(update_fields=["role"])

        sync_user_admin_permissions(self.marketplace_admin)
        sync_user_admin_permissions(self.facilities_admin)
        sync_user_admin_permissions(self.super_admin)

        self.seller = User.objects.create_user(
            username="seller-student",
            password=self.password,
            role="Seller",
        )
        self.prod_approved = Product.objects.create(
            seller=self.seller,
            name="USTP Lanyard",
            category="Merchandise",
            price=Decimal("150.00"),
            stock=20,
            approval_status=Product.STATUS_APPROVED,
        )
        self.prod_low = Product.objects.create(
            seller=self.seller,
            name="USTP Notebook",
            category="Stationery",
            price=Decimal("45.00"),
            stock=3,
            approval_status=Product.STATUS_APPROVED,
        )

        self.order_completed = MarketplaceOrder.objects.create(
            product=self.prod_approved,
            order_code="2026ORDER001",
            buyer_name="Kent Nicolas",
            product_name="USTP Lanyard",
            quantity=2,
            unit_price=Decimal("150.00"),
            total_price=Decimal("300.00"),
            status=MarketplaceOrder.STATUS_COMPLETED,
            payment_status=MarketplaceOrder.PAYMENT_PAID,
        )
        self.order_pending = MarketplaceOrder.objects.create(
            product=self.prod_low,
            order_code="2026ORDER002",
            buyer_name="Pending Buyer",
            product_name="USTP Notebook",
            quantity=1,
            unit_price=Decimal("45.00"),
            total_price=Decimal("45.00"),
            status=MarketplaceOrder.STATUS_PENDING,
            payment_status=MarketplaceOrder.PAYMENT_UNPAID,
        )

        self.fac_court = Facility.objects.create(
            id="fac-court-1",
            facility_name="Covered Court",
            facility_type="court",
            availability_status=Facility.STATUS_AVAILABLE,
            rate=Decimal("500.00"),
            capacity=200,
        )
        self.ch_user = CampusHubUser.objects.create(
            id=self.seller.id,
            first_name="Seller",
            last_name="Student",
            username=self.seller.username,
            email=self.seller.email,
        )
        today = timezone.localdate()
        self.booking_upcoming = Booking.objects.create(
            id="book-1",
            user=self.ch_user,
            facility=self.fac_court,
            purpose="Basketball Tournament",
            booking_date=today + timedelta(days=2),
            start_time=timezone.datetime.strptime("08:00", "%H:%M").time(),
            end_time=timezone.datetime.strptime("12:00", "%H:%M").time(),
            total_amount=Decimal("2000.00"),
            status=Booking.STATUS_APPROVED,
        )

    def test_marketplace_admin_loads_dedicated_template_and_isolates_facilities(self):
        self.client.force_login(self.marketplace_admin)
        response = self.client.get(reverse("admin_dashboard_page"))
        self.assertEqual(response.status_code, 200)

        # Asserts dedicated template used
        self.assertTemplateUsed(response, "marketplace/pages/admin_marketplace_dashboard.html")
        self.assertTemplateNotUsed(response, "dashboard/pages/admin_dashboard.html")
        self.assertTemplateNotUsed(response, "facilities/pages/admin_facilities_dashboard.html")
        self.assertContains(response, "marketplace/css/admin_marketplace_dashboard.css")
        self.assertContains(response, "marketplace/js/admin_marketplace_dashboard.js")
        self.assertNotContains(response, "facilities/css/admin_facilities_dashboard.css")
        self.assertNotContains(response, "components/css/admin_domain_dashboards.css")

        # Marketplace operational content
        self.assertNotContains(
            response,
            "Monitor marketplace products, orders, sellers, and sales activity",
        )
        self.assertContains(response, "Total Products")
        self.assertContains(response, "Pending Listings")
        self.assertContains(response, "Total Orders")
        self.assertContains(response, "Total Sales (Cash on Pickup)")
        self.assertContains(response, "300.00")
        self.assertNotContains(response, "345.00")
        self.assertContains(response, "2026ORDER001")
        self.assertContains(response, "USTP Notebook")
        self.assertContains(response, "Sales Overview")
        self.assertContains(response, "Completed and paid Cash on Pickup orders")
        self.assertContains(response, "sales-chart-legend")
        self.assertNotContains(response, "sales-summary")
        self.assertContains(response, "Order Status")

        # Must NOT contain facilities content
        self.assertNotContains(response, "Facilities Dashboard")
        self.assertNotContains(response, "Upcoming Reservations")
        self.assertNotContains(response, "Pending Booking Requests")

        # AJAX period switch
        ajax_res = self.client.get(
            reverse("admin_dashboard_page") + "?sales_days=14",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(ajax_res.status_code, 200)
        json_data = ajax_res.json()
        self.assertEqual(json_data.get("sales_days"), 14)
        self.assertIn("sales_chart", json_data)
        self.assertEqual(json_data.get("period_completed_count"), 1)

    def test_facilities_admin_loads_dedicated_template_and_isolates_marketplace(self):
        self.client.force_login(self.facilities_admin)
        response = self.client.get(reverse("admin_dashboard_page"))
        self.assertEqual(response.status_code, 200)

        # Asserts dedicated template used
        self.assertTemplateUsed(response, "facilities/pages/admin_facilities_dashboard.html")
        self.assertTemplateNotUsed(response, "dashboard/pages/admin_dashboard.html")
        self.assertTemplateNotUsed(response, "marketplace/pages/admin_marketplace_dashboard.html")
        self.assertContains(response, "facilities/css/admin_facilities_dashboard.css")
        self.assertContains(response, "facilities/js/admin_facilities_dashboard.js")
        self.assertNotContains(response, "marketplace/css/admin_marketplace_dashboard.css")
        self.assertNotContains(response, "components/css/admin_domain_dashboards.css")

        # Facilities operational content
        self.assertContains(response, "Facilities Dashboard")
        self.assertContains(response, "Monitor facilities, reservations, schedules, and booking activity")
        self.assertContains(response, "Total Facilities")
        self.assertContains(response, "Pending Bookings")
        self.assertContains(response, "Upcoming Reservations")
        self.assertContains(response, "Covered Court")

        # Must NOT contain marketplace content
        self.assertNotContains(response, "Marketplace Dashboard")
        self.assertNotContains(response, "Pending Listings")
        self.assertNotContains(response, "Top Selling Products")

        # AJAX period switch
        ajax_res = self.client.get(
            reverse("admin_dashboard_page") + "?booking_days=14",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(ajax_res.status_code, 200)
        json_data = ajax_res.json()
        self.assertEqual(json_data.get("booking_days"), 14)
        self.assertIn("booking_chart", json_data)

    def test_super_admin_loads_untouched_original_template(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("admin_dashboard_page"))
        self.assertEqual(response.status_code, 200)

        # Asserts original untouched template used
        self.assertTemplateUsed(response, "dashboard/pages/admin_dashboard.html")
        self.assertTemplateNotUsed(response, "marketplace/pages/admin_marketplace_dashboard.html")
        self.assertTemplateNotUsed(response, "facilities/pages/admin_facilities_dashboard.html")

        self.assertContains(response, "System Overview")
        self.assertContains(response, "Sales Overview")
        self.assertContains(response, "Completed and paid Cash on Pickup orders")
        self.assertContains(response, "sales-chart-legend")
        self.assertNotContains(response, "dashboard-sales-summary")


class AdminOrderWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="workflow-admin",
            email="workflow@example.com",
            password="CampusHub1!",
        )
        self.client.force_login(self.admin)
        self.order = MarketplaceOrder.objects.create(
            buyer_name="Campus Buyer",
            product_name="Test Product",
            quantity=1,
            unit_price="50.00",
            total_price="50.00",
        )

    def update_order(self, **payload):
        return self.client.post(
            reverse("admin_order_update", args=[self.order.id]),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_order_moves_through_pickup_workflow_and_records_history(self):
        response = self.update_order(status="processing", payment_status="unpaid")
        self.assertEqual(response.status_code, 200)

        response = self.update_order(
            status="ready_for_pickup",
            payment_status="unpaid",
            pickup_location="Campus cashier",
        )
        self.assertEqual(response.status_code, 200)

        response = self.update_order(
            status="completed",
            payment_status="paid",
            official_receipt_no="OR-1001",
            pickup_location="Campus cashier",
        )
        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, MarketplaceOrder.STATUS_COMPLETED)
        self.assertEqual(self.order.payment_status, MarketplaceOrder.PAYMENT_PAID)
        self.assertEqual(self.order.official_receipt_no, "OR-1001")
        self.assertIsNotNone(self.order.completed_at)
        self.assertEqual(
            MarketplaceOrderStatusHistory.objects.filter(order=self.order).count(),
            3,
        )

    def test_completed_order_requires_recorded_payment(self):
        self.order.status = MarketplaceOrder.STATUS_READY_FOR_PICKUP
        self.order.save(update_fields=["status", "updated_at"])

        response = self.update_order(status="completed", payment_status="unpaid")

        self.assertEqual(response.status_code, 409)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, MarketplaceOrder.STATUS_READY_FOR_PICKUP)

    def test_cancellation_requires_reason(self):
        response = self.update_order(status="cancelled", payment_status="unpaid")

        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, MarketplaceOrder.STATUS_PENDING)

    def test_cash_on_pickup_completion_with_confirmation(self):
        self.order.status = MarketplaceOrder.STATUS_READY_FOR_PICKUP
        self.order.save(update_fields=["status", "updated_at"])

        response = self.update_order(
            status="completed",
            payment_status="paid",
            cash_confirmed=True,
            official_receipt_no="OR-2026-88",
        )
        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, MarketplaceOrder.STATUS_COMPLETED)
        self.assertEqual(self.order.payment_status, MarketplaceOrder.PAYMENT_PAID)
        self.assertEqual(self.order.official_receipt_no, "OR-2026-88")
        self.assertIsNotNone(self.order.completed_at)
        self.assertIsNotNone(self.order.paid_at)
        self.assertEqual(self.order.payment_encoded_by, self.admin.username)

    def test_admin_orders_page_renders_summary_cards_and_columns(self):
        response = self.client.get(reverse("admin_orders_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Orders")
        self.assertContains(response, "Ready for Pickup")
        self.assertContains(response, "ORDER ID")
        self.assertContains(response, "CUSTOMER")
        self.assertContains(response, "ITEMS")
        self.assertContains(response, "QTY")
        self.assertContains(response, "TOTAL")
        self.assertContains(response, "ORDER STATUS")
        self.assertContains(response, "PAYMENT STATUS")
        self.assertContains(response, "ORDER DATE")
        self.assertContains(response, "ACTIONS")

    def test_facilities_admin_blocked_from_orders_page(self):
        fac_admin = User.objects.create_user(
            username="fac-admin",
            email="fac@example.com",
            password="CampusHub1!",
            role="Facilities Admin",
            is_staff=True,
        )
        self.client.force_login(fac_admin)
        response = self.client.get(reverse("admin_orders_page"))
        self.assertIn(response.status_code, [302, 403])


class MarketplaceAdminOrderAccessTests(TestCase):
    password = "CampusHub1!"

    def setUp(self):
        admin_department = Department.objects.create(
            name="Marketplace Order Operations",
            code="MKT-ORD",
        )
        seller_department = Department.objects.create(
            name="Marketplace Sellers",
            code="MKT-SEL",
        )
        other_department = Department.objects.create(
            name="Other Marketplace Sellers",
            code="MKT-OTH",
        )
        self.marketplace_admin = User.objects.create_user(
            username="marketplace-orders-admin",
            password=self.password,
            role="Marketplace Admin",
            department=admin_department,
            is_staff=True,
        )
        sync_user_admin_permissions(self.marketplace_admin)
        self.super_admin = User.objects.create_superuser(
            username="super-orders-admin",
            email="super-orders@example.com",
            password=self.password,
        )
        self.super_admin.role = "Super Admin"
        self.super_admin.save(update_fields=["role"])
        self.seller = User.objects.create_user(
            username="orders-seller",
            password=self.password,
            role="Seller",
            department=seller_department,
        )
        self.other_seller = User.objects.create_user(
            username="other-orders-seller",
            password=self.password,
            role="Seller",
            department=other_department,
        )
        self.product = Product.objects.create(
            seller=self.seller,
            name="Campus Meal",
            category="Rice Meals",
            price=Decimal("75.00"),
            stock=10,
            approval_status=Product.STATUS_APPROVED,
        )
        self.other_product = Product.objects.create(
            seller=self.other_seller,
            name="Campus Drink",
            category="Beverages",
            price=Decimal("25.00"),
            stock=10,
            approval_status=Product.STATUS_APPROVED,
        )
        self.pending_order = MarketplaceOrder.objects.create(
            product=self.product,
            order_code="2026ORDERAAA",
            buyer_name="Student Buyer",
            buyer_email="buyer@example.com",
            product_name=self.product.name,
            category=self.product.category,
            quantity=1,
            unit_price=Decimal("75.00"),
            total_price=Decimal("75.00"),
            status=MarketplaceOrder.STATUS_PENDING,
            payment_status=MarketplaceOrder.PAYMENT_UNPAID,
        )
        self.cancelled_order = MarketplaceOrder.objects.create(
            product=self.other_product,
            order_code="2026ORDERBBB",
            buyer_name="Faculty Buyer",
            buyer_email="faculty@example.com",
            product_name=self.other_product.name,
            category=self.other_product.category,
            quantity=2,
            unit_price=Decimal("25.00"),
            total_price=Decimal("50.00"),
            status=MarketplaceOrder.STATUS_CANCELLED,
            payment_status=MarketplaceOrder.PAYMENT_UNPAID,
            cancellation_reason="Buyer cancelled",
        )

    def _orders_page(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("admin_orders_page"))

    def test_super_and_marketplace_admin_share_the_same_order_records(self):
        marketplace_response = self._orders_page(self.marketplace_admin)
        super_response = self._orders_page(self.super_admin)

        self.assertEqual(marketplace_response.status_code, 200)
        self.assertEqual(super_response.status_code, 200)
        expected_ids = {self.pending_order.id, self.cancelled_order.id}
        self.assertEqual(
            {order.id for order in marketplace_response.context["orders"]},
            expected_ids,
        )
        self.assertEqual(
            {order.id for order in super_response.context["orders"]},
            expected_ids,
        )

    def test_kpis_and_table_use_the_same_authorized_queryset(self):
        response = self._orders_page(self.marketplace_admin)

        self.assertEqual(len(response.context["orders"]), 2)
        self.assertEqual(
            response.context["order_stats"],
            {
                "total": 2,
                "completed": 0,
                "pending": 1,
                "processing": 0,
                "ready_for_pickup": 0,
                "cancelled": 1,
            },
        )
        self.assertContains(response, "2026ORDERAAA")
        self.assertContains(response, "2026ORDERBBB")
        self.assertContains(response, "Student Buyer")
        self.assertContains(response, "Campus Meal")

    def test_search_and_filter_fields_have_real_row_values(self):
        response = self._orders_page(self.marketplace_admin)

        self.assertContains(response, 'id="ordersSearchInput"')
        self.assertContains(response, 'id="ordersStatusFilter"')
        self.assertContains(response, 'id="ordersPaymentFilter"')
        self.assertContains(response, 'id="ordersDatePresetFilter"')
        self.assertContains(response, 'data-order-code="2026ORDERAAA"')
        self.assertContains(response, 'data-buyer-name="Student Buyer"')
        self.assertContains(response, 'data-product-name="Campus Meal"')
        self.assertContains(response, 'data-payment-status="unpaid"')
        self.assertContains(response, 'data-created-date=')

    def test_marketplace_admin_can_update_an_order_from_another_department(self):
        self.client.force_login(self.marketplace_admin)

        response = self.client.post(
            reverse("admin_order_update", args=[self.pending_order.id]),
            data=json.dumps(
                {
                    "status": MarketplaceOrder.STATUS_PROCESSING,
                    "payment_status": MarketplaceOrder.PAYMENT_UNPAID,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.pending_order.refresh_from_db()
        self.assertEqual(self.pending_order.status, MarketplaceOrder.STATUS_PROCESSING)
        self.assertEqual(self.pending_order.payment_status, MarketplaceOrder.PAYMENT_UNPAID)

    def test_unauthorized_user_cannot_modify_order_status(self):
        ordinary_user = User.objects.create_user(
            username="ordinary-orders-user",
            password=self.password,
            role="User",
        )
        self.client.force_login(ordinary_user)

        response = self.client.post(
            reverse("admin_order_update", args=[self.pending_order.id]),
            data=json.dumps({"status": MarketplaceOrder.STATUS_PROCESSING}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.pending_order.refresh_from_db()
        self.assertEqual(self.pending_order.status, MarketplaceOrder.STATUS_PENDING)

    def test_seller_queryset_excludes_other_sellers_orders(self):
        own_ids = set(
            seller_order_queryset(self.seller).values_list("id", flat=True)
        )

        self.assertEqual(own_ids, {self.pending_order.id})
        self.assertNotIn(self.cancelled_order.id, own_ids)

        self.client.force_login(self.seller)
        response = self.client.get(reverse("admin_orders_page"))
        self.assertEqual(response.status_code, 403)


class AdminAccessControlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="access-admin",
            email="access@example.com",
            password="CampusHub1!",
            role="Super Admin",
        )
        self.client.force_login(self.admin)

    def test_current_superuser_cannot_be_deleted(self):
        response = self.client.post(
            reverse("admin_users_delete"),
            {"user_id": self.admin.id},
        )

        self.assertRedirects(response, reverse("admin_users_page"))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_builtin_role_cannot_be_deleted(self):
        role, _ = Role.objects.get_or_create(role_name="Marketplace Admin")

        response = self.client.post(
            reverse("admin_roles_delete"),
            {"role_id": role.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Role.objects.filter(pk=role.pk).exists())

    def test_role_permission_changes_sync_to_assigned_users(self):
        role = Role.objects.create(
            role_name="Department Reviewer",
            description="Reviews marketplace records.",
        )
        assigned_user = User.objects.create_user(
            username="department-reviewer",
            email="reviewer@example.com",
            password="CampusHub1!",
            role=role.role_name,
        )

        response = self.client.post(
            reverse("admin_roles_save"),
            {
                "role_id": role.id,
                "role_name": role.role_name,
                "description": role.description,
                "permissions": ["can_manage_orders", "can_view_reports"],
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        assigned_user.refresh_from_db()
        self.assertTrue(assigned_user.has_perm("accounts.can_manage_orders"))
        self.assertTrue(assigned_user.has_perm("accounts.can_view_reports"))
        self.assertFalse(assigned_user.has_perm("accounts.can_manage_products"))


class RolePermissionsManagementTests(TestCase):
    password = "R7!vQ2#zLm9"

    def setUp(self):
        self.roles = {
            name: Role.objects.get_or_create(
                role_name=name,
                defaults={"description": f"Built-in {name} role.", "is_active": True},
            )[0]
            for name in ("Super Admin", "Marketplace Admin", "Facilities Admin", "User")
        }
        set_role_permissions(self.roles["Super Admin"], list(ADMIN_PERMISSION_CODENAMES))
        for role_name, codenames in BUILTIN_ROLE_PERMISSIONS.items():
            set_role_permissions(self.roles[role_name], list(codenames))
        self.super_admin = User.objects.create_superuser(
            username="roles-super-admin",
            email="roles-super@example.com",
            password=self.password,
            role="Super Admin",
        )
        self.client.force_login(self.super_admin)

    def role_payload(self, role=None, **overrides):
        payload = {
            "role_id": str(role.id) if role else "",
            "role_name": role.role_name if role else "Custom Reviewer",
            "description": role.description if role else "Reviews selected CampusHub records.",
            "permissions": ["can_manage_orders", "can_view_reports"],
            "is_active": "on",
        }
        payload.update(overrides)
        return payload

    def save_role(self, role=None, **overrides):
        return self.client.post(
            reverse("admin_roles_save"),
            self.role_payload(role, **overrides),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_page_shows_real_permissions_search_filters_and_pagination(self):
        for index in range(12):
            Role.objects.create(
                role_name=f"Custom Reviewer {index:02d}",
                description="Custom filtered role.",
                is_active=index != 11,
            )

        page = self.client.get(reverse("admin_roles_page"))
        filtered = self.client.get(
            reverse("admin_roles_page"),
            {"q": "Reviewer 11", "type": "custom", "status": "inactive"},
        )

        self.assertContains(page, "Full Access")
        self.assertContains(page, "Base User Access")
        self.assertContains(page, "Standard User")
        self.assertContains(page, "Access Type")
        self.assertContains(page, "Manage system roles, assigned users, and access permissions.")
        self.assertContains(page, "Available system permissions")
        self.assertContains(page, "Add Custom Role")
        self.assertNotContains(page, "Permission Rules")
        self.assertContains(page, 'class="modal-content roles-modal" id="roleForm"')
        self.assertContains(page, 'id="saveRoleButton">Save Role</button>')
        self.assertContains(page, 'class="roles-rbac-layout"')
        self.assertContains(page, 'class="roles-table"')
        self.assertContains(page, 'id="rolePermissionPanel"')
        self.assertContains(page, 'id="permissionPanelSaveButton"')
        self.assertContains(page, 'data-module="system"')
        self.assertNotContains(page, 'class="role-avatar"')
        self.assertNotContains(page, "Select group")
        self.assertEqual(page.context["roles"][0]["role_name"], "Super Admin")
        self.assertContains(page, "page=2")
        self.assertContains(filtered, "Custom Reviewer 11")
        self.assertNotContains(filtered, "Marketplace Admin")
        self.assertContains(filtered, "Inactive")

    def test_marketplace_and_facilities_permissions_are_editable(self):
        marketplace_user = User.objects.create_user(
            username="market-role-user",
            email="market-role@example.com",
            password=self.password,
            role="Marketplace Admin",
            is_staff=True,
        )
        facilities_user = User.objects.create_user(
            username="facility-role-user",
            email="facility-role@example.com",
            password=self.password,
            role="Facilities Admin",
            is_staff=True,
        )
        sync_user_admin_permissions(marketplace_user)
        sync_user_admin_permissions(facilities_user)

        marketplace_response = self.save_role(
            self.roles["Marketplace Admin"],
            permissions=["can_manage_orders"],
        )
        facilities_response = self.save_role(
            self.roles["Facilities Admin"],
            permissions=["can_manage_facilities", "can_view_reports"],
        )

        self.assertEqual(marketplace_response.status_code, 200)
        self.assertEqual(facilities_response.status_code, 200)
        marketplace_user.refresh_from_db()
        facilities_user.refresh_from_db()
        self.assertTrue(marketplace_user.has_perm("accounts.can_manage_orders"))
        self.assertFalse(marketplace_user.has_perm("accounts.can_manage_products"))
        self.assertTrue(facilities_user.has_perm("accounts.can_manage_facilities"))
        self.assertFalse(facilities_user.has_perm("accounts.can_book_facilities"))

    def test_super_admin_permissions_are_enforced_by_shared_helper(self):
        role = self.roles["Super Admin"]

        set_role_permissions(role, ["can_manage_orders"])
        role.refresh_from_db()

        self.assertSetEqual(
            set(role.granted_permissions.values_list("codename", flat=True)),
            set(ADMIN_PERMISSION_CODENAMES),
        )
        self.assertSetEqual(
            set(permissions_for_role(role.role_name)),
            set(ADMIN_PERMISSION_CODENAMES),
        )

    def test_marketplace_system_permissions_reject_restricted_grants(self):
        role = self.roles["Marketplace Admin"]
        restricted = {"can_export_marketplace_data", "can_export_facility_data", "can_system_backup", "can_restore_system_backup"}
        allowed = {"can_access_messages", "can_access_notifications", "can_manage_settings"}
        user = User.objects.create_user(
            username="marketplace-system-permissions", role=role.role_name,
        )
        response = self.client.post(
            reverse("admin_role_permissions_save"),
            {"role_id": str(role.id), "permissions": list(allowed | restricted | {"can_manage_orders"})},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertSetEqual(
            set(role.granted_permissions.values_list("codename", flat=True)),
            allowed | {"can_manage_orders"},
        )
        user.refresh_from_db()
        for codename in restricted:
            self.assertFalse(user.has_perm(f"accounts.{codename}"))
        for codename in allowed:
            self.assertTrue(user.has_perm(f"accounts.{codename}"))

    def test_facilities_system_permissions_reject_restricted_grants(self):
        role = self.roles["Facilities Admin"]
        restricted = {"can_export_marketplace_data", "can_export_facility_data", "can_system_backup", "can_restore_system_backup"}
        allowed = {"can_access_messages", "can_access_notifications", "can_manage_settings"}
        user = User.objects.create_user(
            username="facilities-system-permissions", role=role.role_name,
        )
        response = self.client.post(
            reverse("admin_role_permissions_save"),
            {"role_id": str(role.id), "permissions": list(allowed | restricted | {"can_manage_bookings"})},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertSetEqual(
            set(role.granted_permissions.values_list("codename", flat=True)),
            allowed | {"can_manage_bookings"},
        )
        user.refresh_from_db()
        for codename in restricted:
            self.assertFalse(user.has_perm(f"accounts.{codename}"))
        for codename in allowed:
            self.assertTrue(user.has_perm(f"accounts.{codename}"))

    def test_system_restrictions_leave_custom_and_super_admin_roles_unchanged(self):
        permissions = ["can_export_facility_data", "can_system_backup", "can_restore_system_backup"]
        custom_role = Role.objects.create(role_name="Custom System Role")
        set_role_permissions(custom_role, permissions)
        self.assertSetEqual(set(permissions_for_role(custom_role.role_name)), set(permissions))
        self.assertTrue(set(permissions).issubset(permissions_for_role("Super Admin")))

    def test_super_admin_drawer_is_locked_and_save_is_hidden(self):
        page = self.client.get(reverse("admin_roles_page"))

        self.assertContains(
            page,
            "Super Admin is a protected system role and always retains full CampusHub access.",
        )
        self.assertContains(page, 'id="permissionPanelSaveButton" hidden')

    def test_permissions_workspace_updates_only_permissions(self):
        role = self.roles["Marketplace Admin"]
        original_description = role.description
        assigned_user = User.objects.create_user(
            username="workspace-admin",
            email="workspace-admin@example.com",
            password=self.password,
            role=role.role_name,
            is_staff=True,
        )
        sync_user_admin_permissions(assigned_user)

        response = self.client.post(
            reverse("admin_role_permissions_save"),
            {
                "role_id": role.id,
                "permissions": ["can_manage_products", "can_manage_orders"],
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        role.refresh_from_db()
        assigned_user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(role.description, original_description)
        self.assertTrue(role.is_active)
        self.assertSetEqual(
            set(role.granted_permissions.values_list("codename", flat=True)),
            {"can_manage_products", "can_manage_orders"},
        )
        self.assertTrue(assigned_user.has_perm("accounts.can_manage_products"))
        self.assertFalse(assigned_user.has_perm("accounts.can_view_reports"))

        empty_response = self.client.post(
            reverse("admin_role_permissions_save"),
            {"role_id": role.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(empty_response.status_code, 400)

    def test_custom_role_creation_assignment_and_duplicate_rejection(self):
        assignable_admin = User.objects.create_user(
            username="custom-role-admin",
            email="custom-role@example.com",
            password=self.password,
            role="User",
        )
        response = self.save_role(
            role_name="Department Auditor",
            assigned_users_present="1",
            assigned_users=[str(assignable_admin.id)],
        )

        self.assertEqual(response.status_code, 200)
        created_role = Role.objects.get(role_name="Department Auditor")
        assignable_admin.refresh_from_db()
        self.assertEqual(assignable_admin.role, created_role.role_name)
        self.assertTrue(assignable_admin.has_perm("accounts.can_manage_orders"))
        self.assertTrue(assignable_admin.has_perm("accounts.can_view_reports"))

        duplicate = self.save_role(role_name="department auditor")
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(Role.objects.filter(role_name__iexact="Department Auditor").count(), 1)

    def test_inactive_role_cannot_receive_a_new_assignment(self):
        inactive_role = Role.objects.create(
            role_name="Inactive Auditor",
            description="Temporarily disabled.",
            is_active=False,
        )
        set_role_permissions(inactive_role, ["can_manage_orders"])
        candidate = User.objects.create_user(
            username="inactive-role-candidate",
            email="inactive-role@example.com",
            password=self.password,
            role="User",
        )

        response = self.save_role(
            inactive_role,
            is_active="",
            permissions=["can_manage_orders"],
            assigned_users_present="1",
            assigned_users=[str(candidate.id)],
        )

        self.assertEqual(response.status_code, 400)
        candidate.refresh_from_db()
        self.assertEqual(candidate.role, "User")
        self.assertFalse(candidate.has_perm("accounts.can_manage_orders"))

    def test_protected_roles_and_final_super_admin_assignment_are_guarded(self):
        delete_response = self.client.post(
            reverse("admin_roles_delete"),
            {"role_id": self.roles["Super Admin"].id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        status_response = self.client.post(
            reverse("admin_roles_status"),
            {"role_id": self.roles["Super Admin"].id, "action": "deactivate"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        remove_assignment_response = self.save_role(
            self.roles["Super Admin"],
            permissions=list(ADMIN_PERMISSION_CODENAMES),
            assigned_users_present="1",
            assigned_users=[],
        )

        self.assertEqual(delete_response.status_code, 400)
        self.assertEqual(status_response.status_code, 400)
        self.assertEqual(remove_assignment_response.status_code, 400)
        self.super_admin.refresh_from_db()
        self.assertEqual(self.super_admin.role, "Super Admin")
        self.assertTrue(self.super_admin.is_superuser)

    def test_permission_change_changes_server_side_access(self):
        role = Role.objects.create(
            role_name="Order Desk",
            description="Handles order records.",
            is_active=True,
        )
        set_role_permissions(role, ["can_manage_orders"])
        user = User.objects.create_user(
            username="order-desk-user",
            email="order-desk@example.com",
            password=self.password,
            role=role.role_name,
        )
        sync_user_admin_permissions(user)
        self.client.force_login(user)
        allowed = self.client.get(reverse("admin_orders_page"))

        self.client.force_login(self.super_admin)
        update = self.save_role(role, permissions=[])
        self.client.force_login(user)
        denied = self.client.get(reverse("admin_orders_page"))

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(update.status_code, 200)
        self.assertEqual(denied.status_code, 403)

    def test_facilities_admin_can_buy_without_marketplace_management(self):
        role = self.roles["Facilities Admin"]
        set_role_permissions(role, list(BUILTIN_ROLE_PERMISSIONS["Facilities Admin"]))
        facilities_admin = User.objects.create_user(
            username="facilities-buyer",
            email="facilities-buyer@example.com",
            password=self.password,
            role=role.role_name,
            is_staff=True,
        )
        sync_user_admin_permissions(facilities_admin)

        self.assertTrue(facilities_admin.has_perm("accounts.can_browse_products"))
        self.assertTrue(facilities_admin.has_perm("accounts.can_buy_products"))
        self.assertFalse(facilities_admin.has_perm("accounts.can_manage_products"))
        self.assertFalse(facilities_admin.has_perm("accounts.can_approve_products"))

        self.client.force_login(facilities_admin)
        response = self.client.get(reverse("admin_products_page"))
        self.assertEqual(response.status_code, 302)

    def test_normal_capabilities_do_not_grant_admin_authority(self):
        role = Role.objects.create(
            role_name="Campus Buyer",
            description="Ordinary browsing, buying, and booking only.",
        )
        set_role_permissions(
            role,
            [
                "can_browse_products",
                "can_buy_products",
                "can_browse_facilities",
                "can_book_facilities",
            ],
        )
        buyer = User.objects.create_user(
            username="campus-buyer",
            email="campus-buyer@example.com",
            password=self.password,
            role=role.role_name,
        )
        sync_user_admin_permissions(buyer)

        self.assertTrue(buyer.has_perm("accounts.can_buy_products"))
        self.assertTrue(buyer.has_perm("accounts.can_book_facilities"))
        self.assertFalse(user_has_admin_access(buyer))

    def test_role_table_uses_database_counts_status_and_builtin_records(self):
        User.objects.create_user(
            username="second-facilities-admin",
            email="second-facilities@example.com",
            password=self.password,
            role="Facilities Admin",
            is_staff=True,
        )
        custom = Role.objects.create(
            role_name="Inactive Custom Role",
            description="Database-backed inactive role.",
            is_active=False,
        )

        response = self.client.get(reverse("admin_roles_page"))
        role_data = {role["role_name"]: role for role in response.context["roles"]}

        self.assertEqual(response.status_code, 200)
        for role_name in ("Super Admin", "Marketplace Admin", "Facilities Admin"):
            self.assertIn(role_name, role_data)
        self.assertEqual(role_data["Facilities Admin"]["user_count"], 1)
        self.assertEqual(role_data[custom.role_name]["status_label"], "Inactive")
        self.assertContains(response, "Marketplace Access")
        self.assertContains(response, "Facilities Access")

    def test_marketplace_and_facilities_permissions_save_and_reload(self):
        role = Role.objects.create(
            role_name="Cross Module Coordinator",
            description="Uses selected marketplace and facility features.",
            is_active=True,
        )
        selected = [
            "can_browse_products",
            "can_buy_products",
            "can_manage_orders",
            "can_browse_facilities",
            "can_book_facilities",
            "can_manage_bookings",
        ]

        save_response = self.client.post(
            reverse("admin_role_permissions_save"),
            {"role_id": role.id, "permissions": selected},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        reload_response = self.client.get(
            reverse("admin_roles_page"),
            {"q": role.role_name},
        )
        saved_role = reload_response.context["roles"][0]

        self.assertEqual(save_response.status_code, 200)
        self.assertSetEqual(set(saved_role["assigned_permissions"]), set(selected))
        self.assertContains(reload_response, "Browse Products")
        self.assertContains(reload_response, "Manage Bookings")
        self.assertContains(reload_response, 'data-module="marketplace"')
        self.assertContains(reload_response, 'data-module="facilities"')


class AdminUserManagementTests(TestCase):
    password = "R7!vQ2#zLm9"

    def setUp(self):
        self.roles = {
            name: Role.objects.get_or_create(role_name=name)[0]
            for name in ("User", "Super Admin", "Facilities Admin", "Marketplace Admin")
        }
        self.department = Department.objects.create(name="Information Technology", code="IT")
        self.admin = User.objects.create_superuser(
            username="users-admin",
            email="users-admin@example.com",
            password=self.password,
            role="Super Admin",
        )
        self.client.force_login(self.admin)

    def user_payload(self, **overrides):
        payload = {
            "first_name": "Campus",
            "last_name": "User",
            "username": "campus-user",
            "email": "campus-user@example.com",
            "contact_number": "09171234567",
            "account_type": "admin",
            "role": "Facilities Admin",
            "password": self.password,
            "confirm_password": self.password,
            "is_active": "on",
        }
        payload.update(overrides)
        return payload

    def save_user(self, **overrides):
        return self.client.post(
            reverse("admin_users_save"),
            self.user_payload(**overrides),
            follow=True,
        )

    def test_add_user_rejects_non_admin_account_types(self):
        student_response = self.save_user(
            account_type="student",
            role="User",
        )
        faculty_response = self.save_user(
            first_name="Faculty",
            username="faculty-user",
            email="faculty-user@example.com",
            account_type="faculty",
            role="User",
        )

        self.assertContains(student_response, "Add User can create only Super Admin")
        self.assertContains(faculty_response, "Add User can create only Super Admin")
        self.assertFalse(CampusHubUser.objects.filter(username="campus-user").exists())
        self.assertFalse(CampusHubUser.objects.filter(username="faculty-user").exists())

    def test_admin_roles_derive_staff_access_and_marketplace_department(self):
        self.save_user(
            username="facility-admin",
            email="facility-admin@example.com",
            account_type="admin",
            role="Facilities Admin",
        )
        self.save_user(
            username="market-admin",
            email="market-admin@example.com",
            account_type="admin",
            role="Marketplace Admin",
            department=str(self.department.pk),
        )
        self.save_user(
            username="second-super-admin",
            email="second-super-admin@example.com",
            account_type="admin",
            role="Super Admin",
        )

        facilities_admin = User.objects.get(username="facility-admin")
        marketplace_admin = User.objects.get(username="market-admin")
        self.assertTrue(facilities_admin.is_staff)
        self.assertFalse(facilities_admin.is_superuser)
        self.assertTrue(marketplace_admin.is_staff)
        self.assertEqual(marketplace_admin.department, self.department)
        self.assertTrue(check_password(self.password, marketplace_admin.password))
        self.assertTrue(User.objects.get(username="second-super-admin").is_superuser)

    def test_duplicate_identity_across_stores_and_invalid_password_are_rejected(self):
        CampusHubUser.objects.create(
            first_name="Existing",
            last_name="Mobile",
            username="shared-user",
            email="mobile@example.com",
            password_hash=make_password(self.password),
        )

        duplicate_response = self.save_user(
            username="shared-user",
            email="new@example.com",
        )
        invalid_response = self.save_user(
            username="weak-user",
            email="weak@example.com",
            password="weakpass",
            confirm_password="weakpass",
        )

        self.assertContains(duplicate_response, "Username &quot;shared-user&quot; already exists.")
        self.assertContains(invalid_response, "Password must include an uppercase letter.")
        self.assertFalse(CampusHubUser.objects.filter(username="weak-user").exists())

    def test_activate_deactivate_and_super_admin_protection(self):
        mobile = CampusHubUser.objects.create(
            first_name="State",
            last_name="Test",
            username="state-user",
            email="state@example.com",
            password_hash=make_password(self.password),
            is_active=True,
        )

        self.client.post(
            reverse("admin_users_action"),
            {"account_ref": f"mobile:{mobile.pk}", "action": "deactivate"},
        )
        mobile.refresh_from_db()
        self.assertFalse(mobile.is_active)
        self.client.post(
            reverse("admin_users_action"),
            {"account_ref": f"mobile:{mobile.pk}", "action": "activate"},
        )
        mobile.refresh_from_db()
        self.assertTrue(mobile.is_active)

        protected_response = self.client.post(
            reverse("admin_users_action"),
            {"account_ref": f"admin:{self.admin.pk}", "action": "deactivate"},
            follow=True,
        )
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertContains(protected_response, "You cannot deactivate or suspend your own account.")

    def test_seller_access_does_not_apply_to_admin_accounts(self):
        SellerRequest.objects.create(
            user=self.admin,
            student_id=self.admin.username,
            full_name="Users Admin",
            product_type="Legacy request",
            status=SellerRequest.STATUS_PENDING,
        )

        page = self.client.get(reverse("admin_users_page"))
        response = self.client.post(
            reverse("admin_users_action"),
            {
                "account_ref": f"admin:{self.admin.pk}",
                "action": "seller_access",
                "seller_status": SellerRequest.STATUS_APPROVED,
            },
            follow=True,
        )

        admin_row = next(
            user
            for user in page.context["users"]
            if user["ref"] == f"admin:{self.admin.pk}"
        )
        self.assertEqual(page.context["pending_sellers"], 0)
        self.assertEqual(admin_row["seller_access"], "not_applicable")
        self.assertContains(page, '<nav aria-label="Users pagination">')
        self.assertContains(page, '<span class="active">1</span>', html=True)
        self.assertContains(page, "Seller access does not apply to administrator accounts")
        self.assertNotContains(page, 'class="dropdown-item seller-access"')
        self.assertContains(response, "Seller access does not apply to administrator accounts.")
        self.assertEqual(
            SellerRequest.objects.get(user=self.admin).status,
            SellerRequest.STATUS_PENDING,
        )

    def test_unified_page_uses_real_cards_filters_sorting_and_pagination(self):
        for number in range(12):
            CampusHubUser.objects.create(
                first_name="Mobile",
                last_name=f"User {number:02d}",
                username=f"mobile-{number:02d}",
                email=f"mobile-{number:02d}@example.com",
                password_hash=make_password(self.password),
                user_type="student" if number < 11 else "faculty",
                is_active=number != 10,
            )
        SellerRequest.objects.create(
            student_id="mobile-00",
            full_name="Mobile User 00",
            product_type="Campus goods",
            status=SellerRequest.STATUS_PENDING,
        )

        page = self.client.get(reverse("admin_users_page"))
        filtered = self.client.get(
            reverse("admin_users_page"),
            {"q": "mobile-11", "type": "faculty", "status": "active"},
        )
        second_page = self.client.get(reverse("admin_users_page"), {"page": 2})

        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["total_users"], 13)
        self.assertEqual(page.context["active_users"], 12)
        self.assertEqual(page.context["pending_sellers"], 1)
        self.assertEqual(page.context["admin_accounts"], 1)
        self.assertContains(page, "mobile-11")
        self.assertContains(filtered, "mobile-11")
        self.assertNotContains(filtered, "mobile-00")
        self.assertEqual(second_page.context["page_obj"].number, 2)
        self.assertEqual(second_page.context["paginator"].per_page, 10)
        self.assertContains(second_page, "mobile-00")

    def test_hard_delete_endpoint_keeps_user_record(self):
        mobile = CampusHubUser.objects.create(
            first_name="Keep",
            last_name="Record",
            username="keep-record",
            email="keep@example.com",
            password_hash=make_password(self.password),
        )

        response = self.client.post(
            reverse("admin_users_delete"),
            {"account_ref": f"mobile:{mobile.pk}"},
            follow=True,
        )

        self.assertContains(response, "Permanent user deletion is disabled.")
        self.assertTrue(CampusHubUser.objects.filter(pk=mobile.pk).exists())


class UserMonitoringTests(TestCase):
    password = "CampusHub1!"

    def setUp(self):
        self.now = timezone.now()
        self.super_admin = User.objects.create_superuser(
            username="monitor-super",
            email="monitor-super@example.com",
            password=self.password,
            first_name="Monitor",
            last_name="Super",
            role="Super Admin",
        )
        self.marketplace_admin = User.objects.create_user(
            username="monitor-marketplace",
            email="monitor-marketplace@example.com",
            password=self.password,
            first_name="Market",
            last_name="Admin",
            role="Marketplace Admin",
            is_staff=True,
        )
        self.facilities_admin = User.objects.create_user(
            username="monitor-facilities",
            email="monitor-facilities@example.com",
            password=self.password,
            first_name="Facilities",
            last_name="Admin",
            role="Facilities Admin",
            is_staff=True,
        )
        self.student = self.create_mobile("student-one", "student")
        self.faculty = self.create_mobile("faculty-one", "faculty")
        self.guest = self.create_mobile("guest-one", "guest")
        self.client.force_login(self.super_admin)

        AdminTabToken.objects.create(
            key="monitoring-active-tab",
            user=self.super_admin,
            created_at=self.now,
            last_seen_at=self.now,
            expires_at=self.now + timedelta(hours=1),
        )
        self.create_event(
            self.student,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        self.create_event(
            self.faculty,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_failed",
            result=AccountActivity.RESULT_FAILED,
            activity="Failed login attempt",
        )

    def create_mobile(self, username, user_type):
        return CampusHubUser.objects.create(
            first_name=user_type.title(),
            last_name="Monitor",
            username=username,
            email=f"{username}@example.com",
            password_hash=make_password(self.password),
            user_type=user_type,
            role="User",
            is_active=True,
        )

    def create_event(self, account, *, source, activity_type, result, activity):
        return AccountActivity.objects.create(
            account_source=source,
            account_id=account.pk,
            account_ref=f"{source}:{account.pk}",
            username=account.username,
            full_name=f"{account.first_name} {account.last_name}",
            email=account.email,
            account_type="admin" if source == AccountActivity.SOURCE_ADMIN else account.user_type,
            role=account.role,
            activity_type=activity_type,
            activity=activity,
            module="Authentication",
            result=result,
            ip_address="192.168.10.25",
            user_agent="CampusHub test client",
        )

    def set_event_date(self, event, event_date, hour=9):
        event_time = timezone.make_aware(
            datetime.combine(event_date, time(hour=hour)),
            timezone.get_current_timezone(),
        )
        AccountActivity.objects.filter(pk=event.pk).update(created_at=event_time)

    def chart_for_range(self, date_from, date_to):
        response = self.client.get(
            reverse("admin_user_monitoring_page"),
            {
                "period": "custom",
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)
        return response, response.context["monitor_chart_data"]

    def test_page_uses_all_account_types_and_real_monitoring_counts(self):
        response = self.client.get(reverse("admin_user_monitoring_page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_active_users"], 6)
        self.assertEqual(response.context["online_now"], 2)
        self.assertEqual(response.context["failed_login_attempts"], 1)
        self.assertEqual(response.context["active_sessions"], 1)
        self.assertSetEqual(
            {row["account_type"] for row in response.context["users"]},
            {"admin", "student", "faculty", "guest"},
        )
        self.assertContains(response, "Peak Login Hours")
        self.assertContains(response, "Online Users Now")
        self.assertContains(response, "Last 30 Days")
        self.assertContains(response, "Custom Date Range")
        self.assertNotContains(response, "Peak hour:")
        self.assertNotContains(response, "Login Success vs Failed")
        self.assertNotContains(response, "Online Users by Account Type")
        self.assertSetEqual(
            {row["username"] for row in response.context["online_users"]},
            {"monitor-super", "student-one"},
        )
        self.assertContains(response, "Student Monitor")
        self.assertContains(response, "Marketplace Admin")
        self.assertContains(response, "Facilities Admin")
        self.assertNotContains(response, "Real account and authentication data")
        self.assertNotContains(response, 'id="monitorPageSize"')
        self.assertNotContains(response, "10 / page")
        self.assertContains(response, "Recent User Activity Log")
        self.assertContains(response, "Account Type / Role")
        self.assertContains(response, 'class="monitor-view js-activity-view"')

    def test_peak_period_filter_supports_today_last_30_days_and_custom_dates(self):
        today = timezone.localdate()
        today_response = self.client.get(
            reverse("admin_user_monitoring_page"),
            {"period": "today"},
        )
        month_response = self.client.get(
            reverse("admin_user_monitoring_page"),
            {"period": "last30"},
        )
        custom_response = self.client.get(
            reverse("admin_user_monitoring_page"),
            {
                "period": "custom",
                "date_from": (today - timedelta(days=2)).isoformat(),
                "date_to": today.isoformat(),
            },
        )

        self.assertEqual(today_response.context["filters"]["date_from"], today.isoformat())
        self.assertEqual(today_response.context["filters"]["date_to"], today.isoformat())
        self.assertEqual(
            month_response.context["filters"]["date_from"],
            (today - timedelta(days=29)).isoformat(),
        )
        self.assertEqual(custom_response.context["filters"]["period"], "custom")
        self.assertEqual(
            custom_response.context["filters"]["date_from"],
            (today - timedelta(days=2)).isoformat(),
        )

    def test_search_type_role_status_activity_and_pagination_are_server_side(self):
        for number in range(11):
            self.create_mobile(f"page-student-{number:02d}", "student")

        searched = self.client.get(
            reverse("admin_user_monitoring_page"),
            {"q": "faculty-one", "type": "faculty", "role": "User", "status": "offline"},
        )
        activity_filtered = self.client.get(
            reverse("admin_user_monitoring_page"),
            {"activity": "login_failed"},
        )
        second_page = self.client.get(
            reverse("admin_user_monitoring_page"),
            {"type": "student", "page": 2, "page_size": 10},
        )

        self.assertEqual(searched.context["paginator"].count, 1)
        self.assertEqual(searched.context["users"][0]["username"], "faculty-one")
        self.assertEqual(activity_filtered.context["paginator"].count, 1)
        self.assertEqual(activity_filtered.context["users"][0]["username"], "faculty-one")
        self.assertEqual(second_page.context["page_obj"].number, 2)
        self.assertEqual(second_page.context["paginator"].per_page, 10)
        self.assertEqual(len(second_page.context["users"]), 2)

    def test_charts_drawer_and_recent_log_only_use_recorded_events(self):
        response = self.client.get(reverse("admin_user_monitoring_page"))
        chart_data = response.context["monitor_chart_data"]
        drawer_user = next(
            row for row in response.context["users_json"] if row["username"] == "student-one"
        )

        self.assertEqual(sum(chart_data["daily"]["success"]), 1)
        self.assertEqual(len(chart_data["daily"]["labels"]), 7)
        self.assertNotIn("failed", chart_data["daily"])
        self.assertEqual(sum(chart_data["peakHours"]["values"]), 1)
        self.assertEqual(len(chart_data["peakHours"]["labels"]), 24)
        self.assertEqual(drawer_user["events"][0]["activity"], "Logged in")
        self.assertEqual(drawer_user["events"][0]["ip"], "192.168.10.25")
        recent_event = response.context["recent_activities"][0]
        self.assertIn(recent_event["account_type"], {"Student", "Faculty"})
        self.assertEqual(recent_event["role"], "Standard User")
        self.assertEqual(recent_event["ip"], "192.168.10.25")
        self.assertContains(response, 'id="activityDetailModal"')
        self.assertContains(response, 'id="recentActivityData"')
        self.assertNotContains(response, "Browsing Products")
        self.assertNotContains(response, "\u00e2")
        self.assertContains(response, "No recorded sessions for this account.")

    def test_daily_login_trend_fills_missing_date_and_counts_only_successes(self):
        AccountActivity.objects.all().delete()
        start = date(2026, 8, 30)
        end = date(2026, 9, 1)

        first_login = self.create_event(
            self.student,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        second_login = self.create_event(
            self.student,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        third_login = self.create_event(
            self.faculty,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        failed_login = self.create_event(
            self.guest,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_failed",
            result=AccountActivity.RESULT_FAILED,
            activity="Failed login attempt",
        )
        self.set_event_date(first_login, start)
        self.set_event_date(second_login, end, hour=10)
        self.set_event_date(third_login, end, hour=11)
        self.set_event_date(failed_login, start + timedelta(days=1))

        _response, chart_data = self.chart_for_range(start, end)

        self.assertEqual(chart_data["daily"]["labels"], ["Aug 30", "Aug 31", "Sep 1"])
        self.assertEqual(
            chart_data["daily"]["tooltipLabels"],
            ["Aug 30, 2026", "Aug 31, 2026", "Sep 1, 2026"],
        )
        self.assertEqual(chart_data["daily"]["success"], [1, 0, 2])

    def test_daily_login_trend_handles_one_day_seven_days_and_empty_ranges(self):
        AccountActivity.objects.all().delete()
        one_day = date(2026, 8, 30)

        _response, one_day_chart = self.chart_for_range(one_day, one_day)
        _response, seven_day_chart = self.chart_for_range(
            one_day,
            one_day + timedelta(days=6),
        )

        self.assertEqual(one_day_chart["daily"]["labels"], ["Aug 30"])
        self.assertEqual(one_day_chart["daily"]["success"], [0])
        self.assertEqual(len(seven_day_chart["daily"]["labels"]), 7)
        self.assertEqual(seven_day_chart["daily"]["success"], [0] * 7)

    def test_weekly_login_trend_includes_zero_activity_weeks(self):
        AccountActivity.objects.all().delete()
        start = date(2026, 8, 24)
        end = date(2026, 9, 13)

        first_week_login = self.create_event(
            self.student,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        third_week_login = self.create_event(
            self.faculty,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        self.set_event_date(first_week_login, start)
        self.set_event_date(third_week_login, date(2026, 9, 7))

        _response, chart_data = self.chart_for_range(start, end)

        self.assertEqual(
            chart_data["weekly"]["labels"],
            ["Aug 24\u201330", "Aug 31\u2013Sep 6", "Sep 7\u201313"],
        )
        self.assertEqual(chart_data["weekly"]["success"], [1, 0, 1])

    def test_monthly_login_trend_includes_zero_activity_months(self):
        AccountActivity.objects.all().delete()
        start = date(2026, 8, 1)
        end = date(2026, 10, 1)

        august_login = self.create_event(
            self.student,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        october_login = self.create_event(
            self.faculty,
            source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            activity="Logged in",
        )
        self.set_event_date(august_login, date(2026, 8, 31))
        self.set_event_date(october_login, end)

        _response, chart_data = self.chart_for_range(start, end)

        self.assertEqual(chart_data["monthly"]["labels"], ["Aug 2026", "Sep 2026", "Oct 2026"])
        self.assertEqual(chart_data["monthly"]["success"], [1, 0, 1])

    def test_login_trend_date_filter_and_tooltip_configuration(self):
        AccountActivity.objects.all().delete()
        start = date(2026, 8, 30)
        one_day_response, one_day_chart = self.chart_for_range(start, start)
        _three_day_response, three_day_chart = self.chart_for_range(
            start,
            start + timedelta(days=2),
        )

        self.assertEqual(len(one_day_chart["daily"]["labels"]), 1)
        self.assertEqual(len(three_day_chart["daily"]["labels"]), 3)
        self.assertContains(one_day_response, "Number of Successful Logins")
        self.assertContains(one_day_response, 'value === 1 ? "login" : "logins"')

    def test_admin_and_mobile_login_endpoints_record_success_and_failure(self):
        AccountActivity.objects.all().delete()

        failed_admin = self.client.post(
            reverse("admin_login"),
            data=json.dumps({"username": self.super_admin.username, "password": "wrong"}),
            content_type="application/json",
        )
        successful_admin = self.client.post(
            reverse("admin_login"),
            data=json.dumps({"username": self.super_admin.username, "password": self.password}),
            content_type="application/json",
        )
        failed_mobile = self.client.post(
            reverse("mobile_login"),
            data=json.dumps({"student_id_or_email": self.student.username, "password": "wrong"}),
            content_type="application/json",
        )
        successful_mobile = self.client.post(
            reverse("mobile_login"),
            data=json.dumps({"student_id_or_email": self.student.username, "password": self.password}),
            content_type="application/json",
        )

        self.assertEqual(failed_admin.status_code, 401)
        self.assertEqual(successful_admin.status_code, 200)
        self.assertEqual(failed_mobile.status_code, 401)
        self.assertEqual(successful_mobile.status_code, 200)
        self.assertEqual(AccountActivity.objects.filter(activity_type="login_failed").count(), 2)
        self.assertEqual(AccountActivity.objects.filter(activity_type="login_success").count(), 2)
        self.assertFalse(
            AccountActivity.objects.exclude(session_identifier="").exists(),
            "Authentication logs must not store raw or partial tokens.",
        )


class AdminReportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="report-admin",
            email="reports@example.com",
            password="CampusHub1!",
            role="Super Admin",
        )
        self.client.force_login(self.admin)
        MarketplaceOrder.objects.create(
            buyer_name="Campus Buyer",
            product_name="Report Product",
            quantity=2,
            unit_price="25.00",
            total_price="50.00",
            payment_status=MarketplaceOrder.PAYMENT_PAID,
        )

    def test_report_page_exports_pdf_or_csv_without_custom_modal(self):
        response = self.client.get(reverse("admin_generate_reports_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="btnOpenExportPreview"')
        self.assertContains(response, 'id="reportExportFormat"')
        self.assertContains(response, '<option value="pdf" selected>Print PDF</option>', html=True)
        self.assertContains(response, '<option value="csv">Download CSV</option>', html=True)
        self.assertNotContains(response, 'id="reportExportModal"')
        self.assertNotContains(response, 'value="xlsx"')
        self.assertContains(response, 'id="reportChartEmpty"')
        self.assertNotContains(response, 'suggestedMax: 5')
        self.assertContains(response, 'function openNativePrintPreview')
        self.assertNotContains(response, "window.open('', 'campushubReportPrint'")
        self.assertContains(response, "printReport.id = 'nativePrintReport'")
        self.assertContains(response, 'window.print()')
        self.assertNotContains(response, "document.createElement('iframe')")
        self.assertContains(response, "exportFormat.value === 'pdf'")

    def test_report_selector_groups_marketplace_facilities_and_system_reports(self):
        response = self.client.get(reverse("admin_generate_reports_page"))

        self.assertEqual(response.status_code, 200)
        for group in ("Marketplace", "Facilities", "System"):
            self.assertContains(response, f'<optgroup label="{group}">')
        for label in (
            "Sales Report",
            "Orders Report",
            "Product &amp; Inventory Report",
            "Low Stock Report",
            "Facility Booking Report",
            "Facility Utilization Report",
            "Facility Payments &amp; OR Report",
            "User Accounts Report",
            "User Login Activity Report",
        ):
            self.assertContains(response, label)

    def test_non_facility_report_previews_use_report_specific_columns(self):
        expected_reports = {
            "sales": ("Sales Report", "Order ID", "Payment"),
            "orders": ("Orders Report", "Customer", "Status"),
            "products": ("Product & Inventory Report", "Inventory Status", "Approval"),
            "low_stock": ("Low Stock Report", "Stock", "Expiry Date"),
            "user_accounts": ("User Accounts Report", "Username", "Last Login"),
            "user_activity": ("User Login Activity Report", "Activity", "Last Login"),
        }

        for report_type, (title, first_column, second_column) in expected_reports.items():
            with self.subTest(report_type=report_type):
                response = self.client.get(
                    reverse("admin_report_preview"),
                    {"report_type": report_type},
                )
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["title"], title)
                self.assertIn(first_column, payload["columns"])
                self.assertIn(second_column, payload["columns"])

    def test_preview_rejects_reversed_date_range(self):
        response = self.client.get(
            reverse("admin_report_preview"),
            {"report_type": "sales", "date_from": "2026-08-22", "date_to": "2026-08-01"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("start date", response.json()["error"].lower())

    def test_pdf_and_csv_report_formats_download_and_are_recorded(self):
        expected_types = {
            "csv": "text/csv",
            "pdf": "application/pdf",
        }

        for file_format, content_type in expected_types.items():
            with self.subTest(file_format=file_format):
                response = self.client.get(
                    reverse("admin_report_download"),
                    {"report_type": "sales", "format": file_format},
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response["Content-Type"].startswith(content_type))

        self.assertEqual(GeneratedReport.objects.count(), 2)

    def test_excel_report_format_is_rejected(self):
        response = self.client.get(
            reverse("admin_report_download"),
            {"report_type": "sales", "format": "xlsx"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("csv or pdf", response.json()["error"].lower())
        self.assertEqual(GeneratedReport.objects.count(), 0)


class UserDeactivationAndHistoryPreservationTests(TestCase):
    password = "CampusHub1!"

    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username="super-admin-user",
            password=self.password,
            email="super-admin@example.com",
        )
        self.super_admin.role = "Super Admin"
        self.super_admin.save()

        self.student = User.objects.create_user(
            username="test-student-deact",
            password=self.password,
            email="student-deact@example.com",
            role="Student",
            is_active=True,
        )

    def test_deactivated_user_displays_deactivated_status_label(self):
        from accounts.user_management import USER_STATUS_LABELS, _row_from_admin
        self.student.is_active = False
        self.student.save()

        row = _row_from_admin(self.student, {}, self.super_admin)
        self.assertEqual(row["status"], "inactive")
        self.assertEqual(row["status_label"], "Deactivated")
        self.assertFalse(row["is_active"])

    def test_admin_access_control_page_lists_deactivated_status(self):
        self.client.force_login(self.super_admin)
        self.student.is_active = False
        self.student.save()

        response = self.client.get(reverse("admin_users_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Deactivated")
        self.assertContains(response, ">Activate Account<")

    def test_deactivating_user_preserves_orders(self):
        from api.models import MarketplaceOrder, Product
        seller = User.objects.create_user(
            username="test-seller-preserve",
            password=self.password,
            role="Seller",
        )
        product = Product.objects.create(
            seller=seller,
            name="Snack Pack",
            price=Decimal("25.00"),
            stock=10,
            approval_status=Product.STATUS_APPROVED,
        )
        order = MarketplaceOrder.objects.create(
            buyer_user_id=self.student.id,
            buyer_name=self.student.username,
            seller_name=seller.username,
            product=product,
            product_name=product.name,
            quantity=1,
            unit_price=product.price,
            total_price=product.price,
            status=MarketplaceOrder.STATUS_COMPLETED,
        )

        # Deactivate user
        self.student.is_active = False
        self.student.save()

        # Verify historical order remains intact
        order.refresh_from_db()
        self.assertEqual(order.buyer_user_id, self.student.id)
        self.assertEqual(order.product_id, product.id)
        self.assertEqual(order.status, MarketplaceOrder.STATUS_COMPLETED)
