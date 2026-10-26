"""Orders monitoring, scope, snapshot preservation and operational confirmations."""
import json
import os
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from accounts.admin_tab_auth import create_admin_tab_token
from accounts.models import AccountActivity, Department, ProgramMajor, User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import MarketplaceOrder, Product


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class OrdersAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.btled, _ = Department.objects.get_or_create(code="BTLED", defaults={"name":"Technology and Livelihood Education", "is_program":True})
        cls.bsit, _ = Department.objects.get_or_create(code="BSIT", defaults={"name":"Information Technology", "is_program":True})
        cls.he, _ = ProgramMajor.objects.get_or_create(program=cls.btled, code="HE", defaults={"name":"Home Economics"})
        cls.ia, _ = ProgramMajor.objects.get_or_create(program=cls.btled, code="IA", defaults={"name":"Industrial Arts"})
        cls.admin = User.objects.create_superuser(username="orders-review-super", password="CampusHub1!", role="Super Admin")
        cls.scoped = User.objects.create_user(username="orders-he-admin", is_staff=True, role="Marketplace Admin", department=cls.btled, major=cls.he)
        sync_user_admin_permissions(cls.scoped)
        cls.seller = User.objects.create_user(username="orders-he-seller", first_name="Campus", last_name="Seller", department=cls.btled, major=cls.he)
        cls.other = User.objects.create_user(username="orders-ia-seller", department=cls.btled, major=cls.ia)
        cls.buyer = User.objects.create_user(username="orders-buyer", first_name="Student", last_name="Buyer", email="orders-buyer@example.test", department=cls.bsit)
        cls.product = Product.objects.create(seller=cls.seller, department=cls.btled, major=cls.he, name="Campus Uniform", price=250, stock=15, approval_status="approved")
        cls.foreign = Product.objects.create(seller=cls.other, department=cls.btled, major=cls.ia, name="Private IA", price=90, stock=15, approval_status="approved")

    def setUp(self):
        self.client.force_login(self.admin)

    def order(self, product=None, **changes):
        product = product or self.product
        values = {"product": product, "product_name": product.name, "buyer_user_id": self.buyer.pk,
                  "buyer_name": "Student Buyer", "buyer_email": self.buyer.email,
                  "seller_name": "Campus Seller", "quantity": 2, "unit_price": "50", "total_price": "100"}
        values.update(changes)
        return MarketplaceOrder.objects.create(**values)

    def page(self, **params):
        response = self.client.get(reverse("admin_orders_page"), params)
        self.assertEqual(response.status_code, 200, response.content[:300])
        return response

    def update(self, order, **payload):
        return self.client.post(reverse("admin_order_update", args=[order.pk]), json.dumps(payload), content_type="application/json")

    def test_scope_follows_product_owner_not_customer_and_cannot_be_bypassed(self):
        allowed = self.order()
        forbidden = self.order(self.foreign)
        self.client.force_login(self.scoped)
        page = self.page()
        self.assertEqual([o.pk for o in page.context["orders"]], [allowed.pk])
        self.assertContains(page, 'data-buyer-program="BSIT"')
        self.assertContains(page, 'data-seller-major="Home Economics"')
        self.assertEqual(self.page(program=self.btled.pk, major=self.ia.pk).context["order_stats"]["total"], 0)
        self.assertEqual(self.update(forbidden, status="processing").status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.page().context["order_stats"]["total"], 2)

    def test_kpis_use_all_matching_orders_before_pagination(self):
        for index in range(23):
            self.order(status="pending" if index % 2 else "completed", payment_status="unpaid" if index % 2 else "paid")
        page = self.page(status="pending", payment="unpaid", page=2)
        self.assertEqual(page.context["order_stats"]["total"], 11)
        self.assertEqual(page.context["order_stats"]["pending"], 11)
        self.assertEqual(page.context["order_stats"]["completed"], 0)
        self.assertEqual(len(page.context["orders"]), 1)
        self.assertContains(page, "status=pending&amp;payment=unpaid")
        self.assertContains(page, "Showing 11 to 11 of 11 orders")

    def test_ambiguous_legacy_multi_item_snapshot_is_super_admin_only(self):
        order = self.order(customization={"items":[{"product_name":"Local","quantity":1},
                                                   {"product_name":"Other seller","quantity":1}]})
        self.client.force_login(self.scoped)
        self.assertEqual(self.page().context["order_stats"]["total"], 0)
        self.assertEqual(self.update(order,status="processing").status_code,404)
        self.client.force_login(self.admin)
        self.assertEqual(self.page().context["order_stats"]["total"], 1)

    def test_single_item_subtotal_uses_snapshot_unit_price_not_discounted_final_total(self):
        order = self.order(quantity=2,unit_price=50,total_price=80)
        row = self.page().context["orders"][0]
        self.assertEqual(row.items_subtotal,"100.00")
        self.assertEqual(row.total_price,Decimal("80"))

    def test_filters_combine_and_clear_preserves_tab_authorization(self):
        self.order(status="ready_for_pickup")
        self.order(self.foreign, status="completed", payment_status="paid")
        page = self.page(search="Uniform", status="ready_for_pickup", payment="unpaid", program=self.btled.pk, major=self.he.pk)
        self.assertEqual(page.context["order_stats"]["total"], 1)
        token = create_admin_tab_token(self.admin)
        page = self.page(search="nothing", __at=token)
        self.assertContains(page, "No orders match the selected filters.")
        self.assertEqual(page.context["orders_reset_url"], reverse("admin_orders_page") + "?__at=" + token)
        self.assertContains(page, 'name="__at"')

    def test_invalid_program_major_dates_and_status_fail_gracefully(self):
        self.order()
        for params in ({"program":"invalid"}, {"program":self.bsit.pk,"major":self.he.pk},
                       {"date":"custom", "date_from":"2026-02-30", "date_to":"2026-03-10"},
                       {"date":"custom", "date_from":"2026-10-10", "date_to":"2026-10-01"},
                       {"status":"fake"}, {"payment":"fake"}):
            page = self.page(**params)
            self.assertTrue(page.context["filter_error"])
            self.assertEqual(page.context["order_stats"]["total"], 0)

    def test_seven_day_boundary_previous_month_and_custom_final_day(self):
        today = timezone.localdate()
        current = self.order()
        before = self.order()
        MarketplaceOrder.objects.filter(pk=current.pk).update(created_at=timezone.make_aware(datetime.combine(today-timedelta(days=6), time(0))))
        MarketplaceOrder.objects.filter(pk=before.pk).update(created_at=timezone.make_aware(datetime.combine(today-timedelta(days=7), time(23,59))))
        self.assertEqual(self.page(date="7days").context["order_stats"]["total"], 1)
        prior = today.replace(day=1)-timedelta(days=1)
        MarketplaceOrder.objects.filter(pk=before.pk).update(created_at=timezone.make_aware(datetime.combine(prior, time(23,59))))
        self.assertIn(before.pk, [o.pk for o in self.page(date="previous_month").context["orders"]])
        page = self.page(date="custom", date_from=prior.isoformat(), date_to=prior.isoformat())
        self.assertIn(before.pk, [o.pk for o in page.context["orders"]])

    def test_snapshot_total_old_code_and_exact_variant_sku_are_preserved(self):
        variant = Product.objects.create(seller=self.seller, name="Variant Uniform", price=900, stock=0, customization_enabled=True,
            customization_options=[{"name":"Size", "options":[{"name":"Medium", "stock":4}, {"name":"Large", "stock":7}]}])
        order = self.order(variant, option="Medium", customization={"selections":[{"group":"Size", "option":"Medium"}]})
        MarketplaceOrder.objects.filter(pk=order.pk).update(order_code="OLD-REF")
        order.refresh_from_db()
        sku = variant.inventory_skus.get(variant_name="Medium")
        before = (order.order_code, order.total_price, variant.customization_options)
        page = self.page(search=sku.code)
        items = json.loads(page.context["orders"][0].items_json)
        self.assertEqual((items[0]["sku"], items[0]["variant"], items[0]["unit_price"], items[0]["subtotal"]), (sku.code, "Medium", "50.00", "100.00"))
        self.assertEqual(self.page(search=variant.inventory_skus.get(variant_name="Large").code).context["order_stats"]["total"], 0)
        self.assertEqual(self.update(order, status="processing").status_code, 200)
        order.refresh_from_db(); variant.refresh_from_db()
        self.assertEqual((order.order_code, order.total_price, variant.customization_options), before)

    def test_bundle_and_legacy_items_use_purchased_snapshots(self):
        bundle = self.order(product_name="Super Meal", customization={"bundle_components":[{"product_id":self.product.pk,"required_quantity":3}], "items":[{"product_name":"Ingredient","quantity":3,"unit_price":10,"subtotal":30}]})
        legacy = self.order(customization={"items":[{"product_name":"Product A","quantity":1,"unit_price":100,"subtotal":100},
                   {"product_name":"Product B","quantity":2,"unit_price":200,"subtotal":400}]}, total_price=450)
        page = self.page()
        rows = {o.pk:o for o in page.context["orders"]}
        self.assertEqual(json.loads(rows[bundle.pk].items_json)[0]["product_name"], "Super Meal")
        self.assertEqual(len(json.loads(rows[bundle.pk].items_json)), 1)
        self.assertEqual(rows[legacy.pk].display_qty, 3)
        self.assertEqual(rows[legacy.pk].display_items, "Product A + 1 more")
        self.assertEqual(rows[legacy.pk].items_subtotal, "500.00")
        self.assertEqual(rows[legacy.pk].total_price, Decimal("450"))
        self.assertEqual(self.page(search="Product B").context["order_stats"]["total"], 1)
        self.assertEqual(self.page(search="400").context["order_stats"]["total"], 0)

    def test_legacy_blank_customer_name_is_searchable(self):
        self.order(buyer_name="")
        self.assertEqual(self.page(search="Student Buyer").context["order_stats"]["total"], 1)

    def test_completion_requires_actual_pickup_and_payment_and_preserves_receipt(self):
        order = self.order(status="ready_for_pickup", payment_status="paid", official_receipt_no="OR-SAVED",
                           pickup_location="Campus counter", pickup_scheduled_at=timezone.now(), paid_at=timezone.now(), payment_encoded_by="Original Cashier")
        self.assertEqual(self.update(order,status="completed",payment_status="paid").status_code,409)
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True,pickup_confirmed=False).status_code,409)
        self.assertEqual(self.update(order,status="completed",pickup_confirmed=True).status_code,200)
        order.refresh_from_db()
        self.assertEqual((order.official_receipt_no,order.pickup_location,order.payment_encoded_by), ("OR-SAVED","Campus counter","Original Cashier"))
        self.assertIsNotNone(order.picked_up_at)
        self.assertIsNotNone(order.pickup_scheduled_at)
        picked = order.picked_up_at
        self.assertEqual(self.update(order,official_receipt_no="OR-EDITED").status_code,200)
        order.refresh_from_db()
        self.assertEqual(order.picked_up_at,picked)
        self.assertEqual(self.update(order,payment_status="unpaid").status_code,409)
        self.assertEqual(AccountActivity.objects.filter(module="Marketplace Orders").count(),1)

    def test_unpaid_completion_needs_cash_confirmation_and_does_not_skip_lifecycle(self):
        order = self.order()
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True,pickup_confirmed=True).status_code,409)
        self.update(order,status="processing")
        self.update(order,status="ready_for_pickup")
        self.assertEqual(self.update(order,status="completed",pickup_confirmed=True).status_code,409)
        self.assertEqual(self.update(order,status="completed",cash_confirmed="false",pickup_confirmed=True).status_code,409)
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True,pickup_confirmed=True).status_code,200)
        order.refresh_from_db()
        self.assertEqual(order.payment_status,"paid")
        self.assertEqual(order.status_history.count(),3)

    def test_cancellation_preserves_history_and_releases_exact_variant_once(self):
        variant = Product.objects.create(seller=self.seller,name="Reserved Uniform",price=50,stock=0,approval_status="approved",customization_enabled=True,
            customization_options=[{"name":"Size","options":[{"name":"Medium","stock":4,"low_stock_threshold":1},{"name":"Large","stock":8,"low_stock_threshold":2}]}])
        response=self.client.post(reverse("marketplace_orders"),json.dumps({"product_id":variant.pk,"buyer_user_id":self.buyer.pk,"quantity":2,
            "customization":[{"group":"Size","option":"Medium"}]}),content_type="application/json")
        self.assertEqual(response.status_code,201,response.content)
        order=MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(self.update(order,status="cancelled",cancellation_reason="Buyer request").status_code,200)
        self.assertEqual(self.update(order,status="cancelled").status_code,200)
        variant.refresh_from_db(); order.refresh_from_db()
        self.assertEqual([o["stock"] for o in variant.customization_options[0]["options"]],[4,8])
        self.assertTrue(order.inventory_restored)
        self.assertEqual(order.status_history.count(),1)
        self.assertEqual(order.cancellation_reason,"Buyer request")
        self.assertEqual(self.page(status="cancelled").context["order_stats"]["completed"],0)

    def test_empty_states_and_compact_actions(self):
        self.assertContains(self.page(),"No orders found yet.")
        self.order()
        self.assertContains(self.page(search="unmatched"),"No orders match the selected filters.")
        page=self.page()
        self.assertNotContains(page,'order-more-btn')
        self.assertContains(page,'id="btnModalStepOrder"')
        self.assertContains(page,'id="ordersProgramFilter"')
        self.assertContains(page,'id="ordersMajorFilter"')
        self.assertContains(page,'Previous Month')

    def test_unpaid_receipt_is_preserved_and_cancelled_order_cannot_accept_new_payment(self):
        order = self.order(official_receipt_no="ISSUED-NOT-PAID")
        self.assertEqual(self.update(order,status="processing").status_code,200)
        order.refresh_from_db()
        self.assertEqual((order.official_receipt_no,order.payment_status),("ISSUED-NOT-PAID","unpaid"))
        self.assertEqual(self.update(order,status="cancelled",cancellation_reason="Buyer request").status_code,200)
        self.assertEqual(self.update(order,payment_status="paid",cash_confirmed=True).status_code,409)
        self.assertEqual(self.update(order,status=[]).status_code,400)

    def test_related_query_count_does_not_grow_per_row(self):
        self.order()
        with CaptureQueriesContext(connection) as small:
            self.page()
        for _ in range(9): self.order()
        with CaptureQueriesContext(connection) as large:
            self.page()
        self.assertLessEqual(len(large),len(small)+1)

    def test_details_links_and_pagination_preserve_combined_filters(self):
        from html.parser import HTMLParser
        from urllib.parse import parse_qs, urlparse

        class Links(HTMLParser):
            def __init__(self):
                super().__init__(); self.links = []
            def handle_starttag(self, tag, attrs):
                if tag == "a": self.links.append(dict(attrs))

        for _ in range(11): self.order()
        token = create_admin_tab_token(self.admin)
        today = timezone.localdate().isoformat()
        params = {"search":"Campus", "status":"pending", "payment":"unpaid", "program":str(self.btled.pk),
                  "major":str(self.he.pk), "date":"custom", "date_from":today, "date_to":today, "__at":token}
        for number in (1, 2):
            page = self.page(**params, page=number)
            self.assertEqual(len(page.context["orders"]), 10 if number == 1 else 1)
            self.assertEqual(page.context["order_stats"]["total"], 11)
            parser = Links(); parser.feed(page.content.decode())
            detail = next(link for link in parser.links if "order-id-link" in link.get("class", ""))
            query = parse_qs(urlparse(detail["href"]).query)
            for key, value in params.items(): self.assertEqual(query[key], [value])
            selected = page.context["orders"][0]
            self.assertEqual(query["order"], [str(selected.pk)])
            self.assertEqual([order.pk for order in self.client.get(detail["href"]).context["orders"]], [selected.pk])
            navigation = [link for link in parser.links if link.get("class") == "page-btn"]
            self.assertEqual(len(navigation), 1)
            query = parse_qs(urlparse(navigation[0]["href"]).query)
            for key, value in params.items(): self.assertEqual(query[key], [value])
            self.assertEqual(query["page"], ["2" if number == 1 else "1"])
            disabled = "Previous page" if number == 1 else "Next page"
            self.assertContains(page, f'aria-label="{disabled}" title="{disabled}" disabled')
            if os.environ.get("ORDERS_REVIEW_DIR"):
                (Path(os.environ["ORDERS_REVIEW_DIR"])/f"page{number}.html").write_bytes(page.content)
        header_page = self.client.get(reverse("admin_orders_page"), {"search":"Campus"}, HTTP_X_ADMIN_TAB_TOKEN=token)
        parser = Links(); parser.feed(header_page.content.decode())
        detail = next(link for link in parser.links if "order-id-link" in link.get("class", ""))
        self.assertEqual(parse_qs(urlparse(detail["href"]).query)["__at"], [token])

    def test_view_only_details_preserve_read_access_and_forbid_updates(self):
        from django.contrib.auth.models import Permission
        viewer = User.objects.create_user(username="orders-read-only", is_staff=True, department=self.btled, major=self.he)
        viewer.user_permissions.add(Permission.objects.get(codename="can_view_orders", content_type__app_label="accounts"))
        self.assertFalse(viewer.has_perm("accounts.can_manage_orders"))
        orders = [self.order(status=status, payment_status="paid" if status == "completed" else "unpaid")
                  for status in ("pending", "ready_for_pickup", "completed")]
        foreign = self.order(self.foreign)
        self.client.force_login(viewer)
        page = self.page()
        self.assertContains(page, 'data-can-manage-orders="false"')
        self.assertEqual({order.pk for order in page.context["orders"]}, {order.pk for order in orders})
        for order in orders:
            self.assertEqual([row.pk for row in self.page(order=order.pk).context["orders"]], [order.pk])
            self.assertEqual(self.update(order, status="cancelled", cancellation_reason="Must be denied").status_code, 403)
        self.assertFalse(self.page(order=foreign.pk).context["orders"])
        for order in orders:
            original = order.status; order.refresh_from_db(); self.assertEqual(order.status, original)
        if os.environ.get("ORDERS_REVIEW_DIR"):
            (Path(os.environ["ORDERS_REVIEW_DIR"])/"viewer.html").write_bytes(page.content)

    def test_export_actual_orders_for_browser_review(self):
        directory=os.environ.get("ORDERS_REVIEW_DIR")
        if not directory: return
        for index in range(14):
            status=("pending","processing","ready_for_pickup","completed","cancelled")[index%5]
            self.order(status=status,payment_status="paid" if status=="completed" else "unpaid",
                       official_receipt_no="OR-REVIEW" if status=="completed" else "")
        # Test XSS-safe text rendering and explicit unpaid legacy completion display.
        self.order(product_name="Uniform <img src=x onerror=alert(1)>",status="completed",payment_status="unpaid")
        path=Path(directory); path.mkdir(parents=True,exist_ok=True)
        for name,params in (("orders",{}),("filtered",{"program":self.btled.pk,"major":self.he.pk,"status":"ready_for_pickup"}),
                            ("empty",{"search":"nonexistent"}),("custom",{"date":"custom","date_from":timezone.localdate().isoformat(),"date_to":timezone.localdate().isoformat()})):
            (path/f"{name}.html").write_bytes(self.page(**params).content)
