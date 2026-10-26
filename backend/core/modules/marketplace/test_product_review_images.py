"""Pending review controls and private image access; isolated fixtures only."""
import base64
import json
import os
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.admin_tab_auth import create_admin_tab_token
from accounts.models import Department, User
from api.models import Product


class ProductReviewButtonsTests(SimpleTestCase):
    def render(self, status="pending", archived=False, approve=True):
        return render_to_string("marketplace/partials/product_actions.html", {
            "product": SimpleNamespace(approval_status=status, is_archived=archived),
            "can_manage_products": True, "can_approve_products": approve,
        })

    def test_pending_has_named_check_and_cross_with_existing_management(self):
        html = self.render()
        for action in ("approve", "reject", "archive"):
            self.assertIn(f'aria-label="{action.capitalize()} product"', html)
        self.assertIn('aria-label="View Details"', html)
        self.assertNotIn('btn-edit-product', html)
        self.assertNotIn("product-review-menu", html)
        self.assertIn('d="m5 12 4 4L19 6"', html)
        self.assertIn('d="m6 6 12 12M18 6 6 18"', html)

    def test_decision_controls_require_pending_active_and_permission(self):
        for args in ({"status": "approved"}, {"status": "rejected"},
                     {"archived": True}, {"approve": False}):
            with self.subTest(args=args):
                html = self.render(**args)
                self.assertNotIn("btn-approve-product", html)
                self.assertNotIn("btn-reject-product", html)


class PendingProductImageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="review-image-admin", role="Super Admin", email="review-image@example.edu",
        )
        cls.program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name":"BSIT", "is_program":True})
        source = Path(settings.BASE_DIR).parent / "static/assets/img/icon.png"
        cls.image_bytes = source.read_bytes()
        cls.data_url = "data:image/png;base64," + base64.b64encode(cls.image_bytes).decode()
        cls.pending = Product.objects.create(seller=cls.admin, department=cls.program,
            name="Pending Test Listing", category="School Supplies", price=50, stock=8,
            approval_status="pending", image_url=cls.data_url)
        cls.approved = Product.objects.create(seller=cls.admin, department=cls.program,
            name="Approved Test Listing", category="School Supplies", price=25, stock=5,
            approval_status="approved", image_url=cls.data_url)

    def test_pending_image_requires_authorized_tab_but_approved_image_remains_public(self):
        url = reverse("product_image", args=[self.pending.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        token = create_admin_tab_token(self.admin)
        response = self.client.get(url, {"__at": token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.image_bytes)
        self.assertEqual(self.client.get(url, {"__at": "invalid-test-token"}).status_code, 404)
        self.assertEqual(self.client.get(reverse("product_image", args=[self.approved.pk])).status_code, 200)

    def test_initial_thumbnail_preserves_admin_tab_without_referrer_and_exports_optional_fixture(self):
        token = create_admin_tab_token(self.admin)
        response = self.client.get(reverse("admin_products_page"), {"__at": token})
        self.assertEqual(response.status_code, 200)
        image_url = reverse("product_image", args=[self.pending.pk])
        self.assertContains(response, f'src="{image_url}?__at={token}"')
        self.assertContains(response, 'referrerpolicy="no-referrer"')
        self.assertContains(response, 'class="product-table-image product-table-image-empty" hidden')
        self.assertNotContains(response, 'class="product-review-menu"')
        for element_id in ("productDecisionModal", "productDecisionModalLabel",
                           "productDecisionReason", "confirmProductDecisionButton"):
            self.assertContains(response, f'id="{element_id}"')
        root = os.environ.get("PRODUCT_REVIEW_CAPTURE_DIR")
        if root:
            # No production credentials/rows: export an isolated test page only.
            from api.views import serialize_product
            root = Path(root)
            root.mkdir(parents=True, exist_ok=True)
            self.client.force_login(self.admin)
            page = self.client.get(reverse("admin_products_page"))
            root.joinpath("products.html").write_bytes(page.content)
            root.joinpath("products.json").write_text(json.dumps([
                serialize_product(self.pending), serialize_product(self.approved),
            ]), encoding="utf-8")

    def test_existing_review_endpoints_keep_permissions_and_rejection_reason(self):
        approve = reverse("marketplace_approve_product", args=[self.pending.pk])
        reject = reverse("marketplace_reject_product", args=[self.pending.pk])
        reader = User.objects.create_user(username="review-image-reader", role="User")
        self.client.force_login(reader)
        self.assertEqual(self.client.post(approve).status_code, 403)
        self.client.force_login(self.admin)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.approval_status, "pending")
        self.assertEqual(self.client.post(reject, {"rejection_reason": "Test review reason"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 200)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.approval_status, "rejected")
        self.assertEqual(self.pending.rejection_reason, "Test review reason")
