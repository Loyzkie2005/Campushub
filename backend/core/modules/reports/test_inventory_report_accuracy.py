import csv
from io import StringIO
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import User
from api.models import Product, BundleComponent
from .reporting import build_report


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class InventoryReportAccuracyTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="inventory-report-accuracy", role="Super Admin")
        self.a = Product.objects.create(seller=self.admin, name="Component A", price=10, stock=30, approval_status="approved")
        self.b = Product.objects.create(seller=self.admin, name="Component B", price=10, stock=40, approval_status="approved")
        self.bundle = Product.objects.create(seller=self.admin, name="Derived Bundle", price=20, stock=0, product_type="bundle", approval_status="approved")
        BundleComponent.objects.create(bundle=self.bundle, product=self.a, required_quantity=1)
        BundleComponent.objects.create(bundle=self.bundle, product=self.b, required_quantity=2)
        self.client.force_login(self.admin)

    def test_current_physical_and_derived_quantities_are_separate(self):
        report = build_report("products", user=self.admin)
        summary = {row["label"]: row["value"] for row in report["summary"]}
        self.assertEqual(summary["Available Physical Units"], 70)
        self.assertEqual(summary["Derived Bundles Available"], 20)
        self.assertNotIn("Total Stock", summary)
        self.assertEqual(sum(report["chart"]["values"]), 70)
        self.assertNotIn(self.bundle.name, report["chart"]["labels"])
        self.assertEqual(next(row for row in report["rows"] if row["Product"] == self.bundle.name)["Quantity Basis"], "Derived bundles")
        self.assertIn("current available inventory snapshot", report["description"].lower())

    def test_preview_csv_pdf_and_latest_login_description(self):
        for kind in ("products", "user_activity"):
            data = build_report(kind, user=self.admin)
            preview = self.client.get(reverse("admin_report_preview"), {"report_type": kind})
            self.assertEqual(preview.status_code, 200)
            self.assertEqual(preview.json(), data)
            csv_response = self.client.get(reverse("admin_report_download"), {"report_type": kind, "format": "csv"})
            rows = list(csv.reader(StringIO(csv_response.content.decode())))
            self.assertEqual(rows[0][2], data["description"])
            self.assertEqual(rows[1], data["columns"])
            pdf = self.client.get(reverse("admin_report_download"), {"report_type": kind, "format": "pdf"})
            self.assertEqual(pdf.status_code, 200); self.assertTrue(pdf.content.startswith(b"%PDF-"))
            import os
            from pathlib import Path
            directory = os.environ.get("FIFO_REVIEW_DIR")
            if directory:
                root = Path(directory); root.mkdir(parents=True, exist_ok=True)
                (root / f"{kind}.csv").write_bytes(csv_response.content)
                (root / f"{kind}.pdf").write_bytes(pdf.content)
        self.assertIn("not a complete login history", build_report("user_activity")["description"])
