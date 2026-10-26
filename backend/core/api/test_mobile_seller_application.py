import base64
import os
import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
from decimal import Decimal
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from api.models import CampusHubUser, Product, SellerRequest, InventorySKU
from accounts.models import User, Department, AccountActivity
from accounts.role_permissions import sync_user_admin_permissions
from modules.messages.auth import mobile_chat_token


class MobileSellerApplicationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        self.program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name": "BSIT", "is_program": True})
        self.mobile = CampusHubUser.objects.create(username="seller-student", student_id="2026001234",
            first_name="Ana", last_name="Student", email="ana-seller@example.com", password_hash="unused",
            user_type="student", role="User", department=self.program, contact_number="09171234567", profile_completed=True)
        self.admin = User.objects.create_superuser(username="seller-reviewer", role="Super Admin", email="reviewer@example.com")
        self.seed = Product.objects.create(seller=self.admin, name="Existing category listing", category="School Supplies", price=10, stock=10, approval_status="approved")
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + mobile_chat_token(self.mobile)}
        self.payload = {"category": "School Supplies", "products_intended": "Notebooks and pens", "course_section": "2A",
            "contact_number": "09171234567", "message": "Campus supplies", "confirmations": {"accuracy": True, "rules": True, "approval": True}}

    def submit(self, payload=None):
        return self.client.post(reverse("seller_access_request"), json.dumps(payload or self.payload), content_type="application/json", **self.auth)

    def test_draft_has_no_status_record_and_identity_is_server_owned(self):
        result = self.client.get(reverse("seller_access_status"), {"student_id": "someone-else"}, **self.auth)
        self.assertEqual(result.json()["status"], "none")
        self.assertEqual(SellerRequest.objects.count(), 0)
        self.assertEqual(result.json()["applicant"]["user_id"], self.mobile.pk)
        response = self.submit({**self.payload, "student_id": "9999999999", "full_name": "Impostor Name"})
        self.assertEqual(response.status_code, 201, response.content)
        item = SellerRequest.objects.get()
        self.assertEqual(item.mobile_user, self.mobile)
        self.assertEqual(item.student_id, self.mobile.student_id)
        self.assertEqual(item.full_name, "Ana Student")
        self.assertEqual(item.application_data["program"], "BSIT")
        self.assertEqual(item.status, "pending")
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.submit().status_code, 409)
        self.assertEqual(SellerRequest.objects.count(), 1)

    def test_authentication_and_terms_are_required(self):
        self.assertEqual(self.client.get(reverse("seller_access_status")).status_code, 401)
        self.assertEqual(self.client.post(reverse("seller_access_request"), json.dumps(self.payload), content_type="application/json").status_code, 401)

    def test_optional_profile_year_section_is_saved_validated_and_preserved_for_old_clients(self):
        url = reverse('mobile_complete_profile')
        payload = {'user_type': 'student', 'student_id': self.mobile.student_id,
                   'program_id': self.program.pk, 'contact_number': self.mobile.contact_number,
                   'year_section': '  2nd Year - Section A  '}
        response = self.client.post(url, json.dumps(payload), content_type='application/json', **self.auth)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['user']['year_section'], '2nd Year - Section A')
        self.mobile.refresh_from_db()
        self.assertEqual(self.mobile.year_section, '2nd Year - Section A')
        del payload['year_section']
        response = self.client.post(url, json.dumps(payload), content_type='application/json', **self.auth)
        self.assertEqual(response.json()['user']['year_section'], '2nd Year - Section A')
        for invalid in ['x' * 121, 123, None]:
            response = self.client.post(url, json.dumps({**payload, 'year_section': invalid}), content_type='application/json', **self.auth)
            self.assertEqual(response.status_code, 400)
        response = self.client.post(url, json.dumps({**payload, 'year_section': ''}), content_type='application/json', **self.auth)
        self.assertEqual(response.json()['user']['year_section'], '')
        for missing in ("accuracy", "rules", "approval"):
            payload = {**self.payload, "confirmations": {**self.payload["confirmations"], missing: False}}
            self.assertEqual(self.submit(payload).status_code, 400)
        self.assertEqual(SellerRequest.objects.count(), 0)

    def test_revision_resubmits_same_record_and_approval_does_not_create_user(self):
        self.submit()
        item = SellerRequest.objects.get()
        self.client.force_login(self.admin)
        result = self.client.post(reverse("marketplace_reject_seller_request", args=[item.pk]),
            {"decision": "needs_revision", "rejection_reason": "Clarify the intended products."})
        self.assertEqual(result.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, "needs_revision")
        self.client.logout()
        self.assertEqual(self.client.get(reverse("seller_access_status"), **self.auth).json()["seller_request"]["revision_notes"], "Clarify the intended products.")
        result = self.submit({**self.payload, "products_intended": "A4 notebooks and blue pens"})
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(SellerRequest.objects.count(), 1)
        self.client.force_login(self.admin)
        before = User.objects.count()
        self.assertEqual(self.client.post(reverse("marketplace_approve_seller_request", args=[item.pk])).status_code, 302)
        self.assertEqual(User.objects.count(), before)
        self.mobile.refresh_from_db()
        self.assertEqual(self.mobile.role, "User")
        self.assertTrue(AccountActivity.objects.filter(activity_type="SELLER_APPROVED", account_ref=f"mobile:{self.mobile.pk}").exists())

    def test_ajax_review_confirms_persisted_status_and_duplicate_conflict(self):
        self.submit()
        item = SellerRequest.objects.get()
        self.client.force_login(self.admin)
        url = reverse('marketplace_approve_seller_request', args=[item.pk])
        result = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['ok'])
        item.refresh_from_db()
        self.assertEqual(result.json()['status'], item.status)
        self.assertEqual(item.status, 'approved')
        self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 409)
        self.assertEqual(AccountActivity.objects.filter(activity_type='SELLER_APPROVED').count(), 1)

    def test_ajax_revision_validation_preserves_pending_record(self):
        self.submit()
        item = SellerRequest.objects.get()
        self.client.force_login(self.admin)
        url = reverse('marketplace_reject_seller_request', args=[item.pk])
        result = self.client.post(url, {'decision': 'needs_revision'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(result.status_code, 400)
        item.refresh_from_db()
        self.assertEqual(item.status, 'pending')
        result = self.client.post(url, {'decision': 'needs_revision', 'rejection_reason': 'Clarify products.'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['ok'])
        item.refresh_from_db()
        self.assertEqual(result.json()['status'], 'needs_revision')
        self.assertEqual(item.status, 'needs_revision')

    def test_mobile_product_owner_and_inventory_use_existing_account(self):
        listing = {"name": "Student notebook", "price": "25.00", "stock": 10, "low_stock_threshold": 2, "category": "School Supplies"}
        url = reverse("seller_submit_product")
        self.assertEqual(self.client.post(url, json.dumps(listing), content_type="application/json", **self.auth).status_code, 403)

        self.submit()
        item = SellerRequest.objects.get()
        item.approve(self.admin)
        response = self.client.post(url, json.dumps(listing), content_type="application/json", **self.auth)
        self.assertEqual(response.status_code, 201, response.content)
        product = Product.objects.exclude(pk=self.seed.pk).get()
        self.assertIsNone(product.seller_id)
        self.assertEqual(product.mobile_seller_id, self.mobile.pk)
        self.assertEqual(product.approval_status, "pending")
        self.assertEqual(product.get_total_stock(), 10)
        self.assertTrue(InventorySKU.objects.filter(product=product).exists())
        self.assertEqual(response.json()["product"]["seller_ref"], f"mobile:{self.mobile.pk}")
        rows = self.client.get(url, **self.auth).json()["products"]
        self.assertEqual([row["id"] for row in rows], [product.pk])
        product.approve(self.admin)
        public = self.client.get(reverse("approved_products"))
        self.assertEqual(public.status_code, 200)
        self.assertTrue(any(row["seller"] == "Ana Student" for row in public.json()["products"]))
        item.is_suspended = True
        item.save(update_fields=["is_suspended"])
        self.assertEqual(self.client.post(url, json.dumps(listing), content_type="application/json", **self.auth).status_code, 403)

    def test_public_products_use_actual_owner_profile_photo_or_empty_fallback(self):
        self.mobile.profile_photo = "profile-photos/actual-owner.jpg"
        self.mobile.save(update_fields=["profile_photo"])
        product = Product.objects.create(mobile_seller=self.mobile,
            name="Photo-owned listing", category="School Supplies", price=10,
            stock=2, approval_status="approved")
        rows = self.client.get(reverse("approved_products")).json()["products"]
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id[product.pk]["seller_photo_url"], self.mobile.profile_photo.url)
        self.assertEqual(by_id[self.seed.pk]["seller_photo_url"], "")
        self.assertEqual(by_id[product.pk]["seller_ref"], f"mobile:{self.mobile.pk}")
        self.assertEqual(by_id[product.pk]["seller"], "Ana Student")

    def test_mobile_products_work_in_existing_admin_inventory_and_approval(self):
        self.submit()
        SellerRequest.objects.get().approve(self.admin)
        self.client.post(reverse("seller_submit_product"), json.dumps({"name": "Real mobile owner item", "price": "12.50", "stock": 8, "category": "School Supplies"}), content_type="application/json", **self.auth)
        product = Product.objects.get(mobile_seller=self.mobile)
        self.client.force_login(self.admin)
        inventory = self.client.get(reverse("admin_products_page"), {"view": "inventory", "seller": f"mobile:{self.mobile.pk}"})
        self.assertEqual(inventory.status_code, 200)
        self.assertContains(inventory, "Real mobile owner item")
        self.assertNotContains(inventory, self.seed.name)
        self.assertContains(self.client.get(reverse("admin_products_page")), "Ana Student")
        reviewed = self.client.post(reverse("marketplace_approve_product", args=[product.pk]))
        self.assertEqual(reviewed.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.approval_status, "approved")
        self.assertTrue(AccountActivity.objects.filter(activity_type="PRODUCT_APPROVED", account_ref=f"mobile:{self.mobile.pk}").exists())

    def test_bundle_component_owner_keys_do_not_mix_mobile_and_web_accounts(self):
        from modules.marketplace.services.bundles import validate_recipe, BundleError
        component = Product.objects.create(mobile_seller=self.mobile, name="Mobile component", category="School Supplies", price=2, stock=6, approval_status="approved")
        recipe = validate_recipe([{"product_id": component.pk, "required_quantity": 2}], f"mobile:{self.mobile.pk}")
        self.assertEqual(len(recipe), 1)
        with self.assertRaises(BundleError):
            validate_recipe([{"product_id": component.pk, "required_quantity": 2}], self.mobile.pk)

    @staticmethod
    def image_data_url(fmt="PNG", color=(25, 50, 75)):
        stream = BytesIO()
        Image.new("RGB", (4, 4), color).save(stream, format=fmt)
        mime = "jpeg" if fmt == "JPEG" else fmt.lower()
        return f"data:image/{mime};base64," + base64.b64encode(stream.getvalue()).decode()

    def gallery_listing(self, **extra):
        return {"name": "Test gallery product", "price": "25.00", "stock": 6,
                "category": "School Supplies", **extra}

    def post_gallery(self, **extra):
        return self.client.post(reverse("seller_submit_product"), json.dumps(self.gallery_listing(**extra)),
                                content_type="application/json", **self.auth)

    def test_six_mobile_images_persist_in_order_with_existing_owner_and_pending_status(self):
        SellerRequest.objects.create(mobile_user=self.mobile, status="approved")
        images = [self.image_data_url(color=(i * 30, 50, 75)) for i in range(6)]
        with TemporaryDirectory(prefix="campushub-gallery-test-") as media, self.settings(MEDIA_ROOT=media):
            response = self.post_gallery(images=images, seller_id=self.admin.pk, approval_status="approved")
            self.assertEqual(response.status_code, 201, response.content)
            product = Product.objects.get(pk=response.json()["product"]["id"])
            self.assertEqual(product.mobile_seller_id, self.mobile.pk)
            self.assertIsNone(product.seller_id)
            self.assertEqual(product.approval_status, "pending")
            stored = product.get_image_list()
            self.assertEqual(len(stored), 6)
            self.assertEqual(response.json()["product"]["images"], stored)
            for source, url in zip(images, stored):
                path = Path(media) / url.removeprefix("/media/")
                self.assertEqual(path.read_bytes(), base64.b64decode(source.split(",", 1)[1]))
            self.assertEqual(len(list(Path(media).rglob("*.png"))), 6)

    def test_gallery_supported_formats_and_legacy_single_image_remain_accepted(self):
        SellerRequest.objects.create(mobile_user=self.mobile, status="approved")
        images = [self.image_data_url(fmt) for fmt in ("JPEG", "PNG", "WEBP", "GIF")]
        with TemporaryDirectory(prefix="campushub-gallery-test-") as media, self.settings(MEDIA_ROOT=media):
            response = self.post_gallery(images=images)
            self.assertEqual(response.status_code, 201, response.content)
            self.assertEqual(len(response.json()["product"]["images"]), 4)
            legacy = self.post_gallery(image_url=images[0])
            self.assertEqual(legacy.status_code, 201, legacy.content)
            product = Product.objects.get(pk=legacy.json()["product"]["id"])
            self.assertFalse(product.image_url.startswith("["))
            self.assertEqual(product.get_image_list(), [product.image_url])
            legacy_gallery = self.post_gallery(image_url=json.dumps(images))
            self.assertEqual(legacy_gallery.status_code, 201, legacy_gallery.content)
            self.assertEqual(len(legacy_gallery.json()["product"]["images"]), 4)

    def test_invalid_gallery_is_rejected_before_product_or_file_creation(self):
        SellerRequest.objects.create(mobile_user=self.mobile, status="approved")
        image = self.image_data_url()
        invalid = ["not a list", None, [image] * 7, [None], [""],
                   ["data:image/svg;base64,PHN2Zy8+"], ["data:image/png;base64,bm90IGFuIGltYWdl"],
                   [image, "data:image/png;base64,!!!"],
                   [self.image_data_url("JPEG").replace("image/jpeg", "image/png")],
                   ["data:image/png;base64," + "A" * (((5 * 1024 * 1024 + 2) // 3) * 4 + 4)]]
        before = Product.objects.count()
        with TemporaryDirectory(prefix="campushub-gallery-test-") as media, self.settings(MEDIA_ROOT=media):
            for images in invalid:
                with self.subTest(kind=type(images).__name__, count=len(images) if isinstance(images, list) else None):
                    response = self.post_gallery(images=images)
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(Product.objects.count(), before)
                    self.assertEqual(list(Path(media).rglob("*")), [])
            for legacy in (json.dumps([image] * 7), {"invalid": "image"}):
                self.assertEqual(self.post_gallery(image_url=legacy).status_code, 400)
                self.assertEqual(Product.objects.count(), before)
                self.assertEqual(list(Path(media).rglob("*")), [])

    def test_program_and_terms_validation_cannot_be_bypassed(self):
        self.mobile.department, _ = Department.objects.get_or_create(code="BTLED", defaults={"name":"BTLED", "is_program":True})
        from accounts.models import ProgramMajor
        ProgramMajor.objects.get_or_create(program=self.mobile.department, code='HE', defaults={'name':'Home Economics'})
        self.mobile.major = None
        self.mobile.save(update_fields=["department", "major"])
        self.assertEqual(self.submit().status_code, 400)
        self.assertEqual(SellerRequest.objects.count(), 0)

    def test_admin_applications_display_real_mobile_identity_and_historical_program(self):
        self.assertEqual(self.submit().status_code, 201)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_sellers_page'), {'q': self.mobile.email})
        self.assertEqual(response.status_code, 200)
        row = list(response.context['page_obj'])[0]
        self.assertEqual(row.display_username, self.mobile.username)
        self.assertEqual(row.display_department.pk, self.program.pk)
        self.assertContains(response, 'Seller Applications')
        self.assertContains(response, 'Page 1 of 1')
        self.assertContains(response, 'View Application')
        self.mobile.department = None
        self.mobile.save(update_fields=['department'])
        response = self.client.get(reverse('admin_sellers_page'))
        self.assertContains(response, 'Application snapshot')
        self.assertEqual(list(response.context['page_obj'])[0].snapshot_program, 'BSIT')
        self.mobile.refresh_from_db()
        self.assertIsNone(self.mobile.department_id)

    def test_admin_application_filters_paginate_and_keep_scoped_counts(self):
        self.submit()
        SellerRequest.objects.bulk_create([SellerRequest(student_id=f'page-{i}', full_name=f'Paging applicant {i}',
            product_type='Supplies', status='approved' if i % 2 else 'pending') for i in range(12)])
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_sellers_page'), {'q':'Paging', 'page':2, 'origin':'review'})
        self.assertEqual(len(response.context['page_obj']), 2)
        self.assertTrue(all(not row.display_username for row in response.context['page_obj']))
        self.assertContains(response, 'Applicant ID:')
        self.assertEqual(response.context['status_counts'], {'total':13,'pending':7,'approved':6,'rejected':0})
        self.assertContains(response, 'Page 2 of 2')
        self.assertIn('q=Paging', response.context['query_without_page'])
        self.assertIn('origin=review', response.context['seller_clear_query'])
        self.assertNotIn('q=', response.context['seller_clear_query'])
        response = self.client.get(reverse('admin_sellers_page'), {'q':'Paging','status':'pending'})
        self.assertEqual(response.context['page_obj'].paginator.count, 6)
        self.assertEqual(response.context['status_counts']['total'], 13)
        if destination := os.environ.get('MARKETPLACE_DASHBOARD_REVIEW_DIR'):
            root = Path(destination).parent / 'sellers'; root.mkdir(parents=True,exist_ok=True)
            for name,params in [('populated',{}),('page2',{'q':'Paging','page':2}),('pending',{'q':'Paging','status':'pending'}),('empty',{'q':'no matching applicant'})]:
                root.joinpath(name+'.html').write_bytes(self.client.get(reverse('admin_sellers_page'),params).content)

    def test_application_drawer_formats_only_aware_confirmation_dates(self):
        self.submit()
        item = SellerRequest.objects.get()
        item.application_data['confirmed_at'] = '2026-10-17T19:10:15.650271+00:00'
        item.message = '<script>unsafe applicant text</script>'
        item.save(update_fields=['application_data', 'message'])
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_sellers_page'))
        self.assertContains(response, 'Oct 18, 2026 &middot; 3:10 AM')
        self.assertNotContains(response, '2026-10-17T19:10:15.650271+00:00')
        self.assertContains(response, '&lt;script&gt;unsafe applicant text&lt;/script&gt;')
        self.assertContains(response, 'title="View Application"')
        self.assertNotContains(response, '<span>View Application</span>')
        for invalid in ('2026-10-17T19:10:15', 'invalid', '2026-99-99T19:10:15Z', None):
            with self.subTest(confirmed_at=invalid):
                item.application_data['confirmed_at'] = invalid
                item.save(update_fields=['application_data'])
                response = self.client.get(reverse('admin_sellers_page'))
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.context['page_obj'][0].confirmed_at_value)

    def test_application_table_uses_existing_photo_and_accessible_eye_only_action(self):
        self.mobile.profile_photo = 'profile-photos/isolated-applicant.png'
        self.mobile.save(update_fields=['profile_photo'])
        self.submit()
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin_sellers_page'))
        self.assertContains(response, self.mobile.profile_photo.url)
        self.assertContains(response, 'data-seller-avatar')
        self.assertContains(response, 'title="View Application"')
        self.assertContains(response, 'aria-label="View Application for ')
        self.assertNotContains(response, '<span>View Application</span>')
        if destination := os.environ.get('MARKETPLACE_DASHBOARD_REVIEW_DIR'):
            root = Path(destination).parent / 'sellers'
            root.mkdir(parents=True, exist_ok=True)
            root.joinpath('photo.html').write_bytes(response.content)
        self.mobile.profile_photo = ''
        self.mobile.save(update_fields=['profile_photo'])
        response = self.client.get(reverse('admin_sellers_page'))
        self.assertNotContains(response, 'data-seller-avatar')
        self.assertContains(response, 'class="seller-avatar"')

    def test_application_drawer_history_is_scoped_bounded_and_read_only(self):
        from django.contrib.auth.models import Permission
        self.submit()
        item = SellerRequest.objects.get()
        sibling_user = User.objects.create_user(username='second-drawer-applicant', role='User', department=self.program)
        sibling = SellerRequest.objects.create(user=sibling_user, full_name='Second actual application',
            product_type='Supplies', student_id=sibling_user.username)
        outside_program = Department.objects.create(code='DRAWER-OUTSIDE', name='Outside', is_program=True)
        outside_user = User.objects.create_user(username='outside-drawer-applicant', role='User', department=outside_program)
        outside = SellerRequest.objects.create(user=outside_user, full_name='Outside Drawer Applicant', product_type='Food')
        reader = User.objects.create_user(username='drawer-reader', role='Marketplace Admin',
            is_staff=True, department=self.program)
        reader.groups.clear()
        reader.user_permissions.clear()
        reader.user_permissions.add(Permission.objects.get(codename='can_view_sellers'))
        for application in (item, sibling):
            for index in range(13):
                AccountActivity.objects.create(account_source='mobile', account_id=self.mobile.pk,
                    account_ref=f'mobile:{self.mobile.pk}', module='Marketplace', activity_type='SELLER_REVISION_REQUESTED',
                    activity='Recorded review', result='success',
                    metadata={'seller_request_id': application.pk, 'actor_admin_id': self.admin.pk})
        AccountActivity.objects.create(account_source='admin', account_id=outside_user.pk,
            account_ref=f'admin:{outside_user.pk}', module='Marketplace', activity_type='SELLER_REJECTED',
            activity='Outside private review', result='success', metadata={'seller_request_id': outside.pk})
        # Conflicting resource evidence must not leak through an in-scope application ID.
        AccountActivity.objects.create(account_source='mobile', account_id=self.mobile.pk,
            account_ref=f'mobile:{self.mobile.pk}', module='Marketplace', activity_type='SELLER_APPROVED',
            activity='Conflicting review', result='success',
            metadata={'seller_request_id': item.pk, 'product_id': 99999999, 'actor_username': 'outside-private-actor'})
        self.client.force_login(reader)
        before = list(SellerRequest.objects.values()), AccountActivity.objects.count()
        response = self.client.get(reverse('admin_sellers_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 2)
        for application in response.context['page_obj']:
            self.assertEqual(len(application.review_events), 10)
            self.assertTrue(all(event['action'] == 'Seller Revision Requested' for event in application.review_events))
            self.assertTrue(all(event['username'] == self.admin.username for event in application.review_events))
        self.assertNotContains(response, 'Outside Drawer Applicant')
        self.assertNotContains(response, 'outside-private-actor')
        self.assertNotContains(response, 'seller-action--approve')
        self.assertNotContains(response, 'Only the latest recorded review is stored')
        self.assertEqual(before, (list(SellerRequest.objects.values()), AccountActivity.objects.count()))
        if destination := os.environ.get('MARKETPLACE_DASHBOARD_REVIEW_DIR'):
            root = Path(destination).parent / 'sellers'
            root.mkdir(parents=True, exist_ok=True)
            root.joinpath('history.html').write_bytes(response.content)

    def test_admin_view_only_application_controls_and_latest_review(self):
        from django.contrib.auth.models import Permission
        self.submit()
        item = SellerRequest.objects.get()
        reader = User.objects.create_user(username='application-reader', role='Marketplace Admin', is_staff=True, department=self.program)
        reader.user_permissions.clear()
        reader.groups.clear()
        reader.user_permissions.add(Permission.objects.get(codename='can_view_sellers'))
        self.client.force_login(reader)
        response = self.client.get(reverse('admin_sellers_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Awaiting review')
        self.assertNotContains(response, 'seller-action--approve')
        response = self.client.post(reverse('marketplace_approve_seller_request', args=[item.pk]))
        self.assertIn(response.status_code, (302,403))
        item.refresh_from_db(); self.assertEqual(item.status, 'pending')
        self.client.force_login(self.admin)
        self.client.post(reverse('marketplace_approve_seller_request', args=[item.pk]))
        response = self.client.get(reverse('admin_sellers_page'))
        self.assertContains(response, 'Review Decision')
        self.assertContains(response, 'Review History')
        self.assertContains(response, 'id="sellerApplicationDrawer"')
        self.assertNotContains(response, '<details class="seller-application-details">')
        self.assertContains(response, self.admin.username)
        self.assertNotContains(response, 'seller-action--approve')
        self.mobile.refresh_from_db(); self.assertEqual(self.mobile.role, 'User')
