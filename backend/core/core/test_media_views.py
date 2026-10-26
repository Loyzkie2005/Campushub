"""Real ORM permission checks using an isolated database and temporary images."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from PIL import Image

from accounts.models import User
from api.models import CampusHubUser, Facility, Product


@override_settings(ROOT_URLCONF='core.urls_production', ALLOWED_HOSTS=['testserver'],
                   SECURE_SSL_REDIRECT=False)
class CatalogImageTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.directory.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.admin = User.objects.create_superuser(username='media-test-admin', role='Super Admin')
        self.seller = CampusHubUser.objects.create(
            username='media-test-seller', email='media-test@example.invalid',
            first_name='Test', last_name='Seller', password_hash='not-a-login',
            profile_photo='profile-photos/test/avatar.jpg',
        )

    def image(self, name):
        path = Path(self.directory.name, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (2, 2), 'white').save(path, format='JPEG')
        return '/media/' + name

    def product(self, path, status='approved', **kwargs):
        return Product.objects.create(name='Isolated image fixture', price=10, stock=1,
                                      mobile_seller=self.seller, approval_status=status,
                                      image_url='/media/' + path, **kwargs)

    def assert_image(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'\xff\xd8'))

    def test_approved_gallery_and_variant_images_are_public(self):
        first = 'upload/products/main.jpg'
        second = 'upload/products/second.jpg'
        variant = 'products/variant.jpg'
        product = self.product(first, customization_options=[{'name': 'Size', 'options': [
            {'label': 'L', 'image_url': '/media/' + variant}]}])
        product.image_url = json.dumps(['/media/' + first, '/media/' + second])
        product.save(update_fields=['image_url'])
        for path in (first, second, variant):
            self.assert_image(self.image(path))

    def test_unpublished_and_archived_product_images_remain_private(self):
        for status in ('pending', 'rejected'):
            name = f'upload/products/{status}.jpg'
            self.product(name, status)
            self.assertEqual(self.client.get(self.image(name)).status_code, 404)
        name = 'upload/products/archived.jpg'
        self.product(name, is_archived=True)
        self.assertEqual(self.client.get(self.image(name)).status_code, 404)

    def test_existing_product_admin_can_view_pending_image(self):
        name = 'upload/products/review.jpg'
        self.product(name, 'pending')
        url = self.image(name)
        self.client.force_login(self.admin)
        self.assert_image(url)

    def test_non_admin_cannot_view_pending_image(self):
        name = 'upload/products/private.jpg'
        self.product(name, 'pending')
        reader = User.objects.create_user(username='media-test-reader')
        self.client.force_login(reader)
        self.assertEqual(self.client.get(self.image(name)).status_code, 404)

    def test_facility_image_requires_non_archived_catalog_reference(self):
        name = 'upload/facilities/public.jpg'
        facility = Facility.objects.create(id='MEDIA-TEST', facility_name='Test facility',
                                           image_url='/media/' + name)
        url = self.image(name)
        self.assert_image(url)
        facility.is_archived = True
        facility.save(update_fields=['is_archived'])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_only_seller_avatar_already_published_in_catalog_is_public(self):
        url = self.image(self.seller.profile_photo.name)
        self.assertEqual(self.client.get(url).status_code, 404)
        product = self.product('upload/products/listing.jpg')
        self.assert_image(url)
        product.approval_status = 'rejected'
        product.save(update_fields=['approval_status'])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_pending_applicant_photo_requires_review_permission_and_scope(self):
        from django.contrib.auth.models import Permission
        from accounts.models import Department
        from api.models import SellerRequest
        program = Department.objects.create(code='AVATAR-IN', name='Avatar In', is_program=True)
        outside = Department.objects.create(code='AVATAR-OUT', name='Avatar Out', is_program=True)
        self.seller.department = program
        self.seller.save(update_fields=['department'])
        SellerRequest.objects.create(mobile_user=self.seller, student_id=self.seller.username,
            full_name='Photo Applicant', status='pending')
        reader = User.objects.create_user(username='avatar-reviewer', role='Marketplace Admin', department=program)
        reader.groups.clear()
        reader.user_permissions.clear()
        reader.user_permissions.add(Permission.objects.get(codename='can_view_sellers'))
        url = self.image(self.seller.profile_photo.name)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(reader)
        self.assert_image(url)
        reader.department = outside
        reader.save(update_fields=['department'])
        self.assertEqual(self.client.get(url).status_code, 404)
        reader.department = program
        reader.save(update_fields=['department'])
        reader.user_permissions.clear()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_unreferenced_files_and_private_documents_cannot_be_downloaded(self):
        for name in ('upload/products/unlisted.jpg', 'bookings/private.jpg', 'private.env'):
            self.assertEqual(self.client.get(self.image(name)).status_code, 404)

    def test_traversal_and_symlink_cannot_escape_media_root(self):
        self.assertEqual(self.client.get('/media/upload/products/%2e%2e/private.jpg').status_code, 404)
        outside = Path(self.directory.name).parent / (Path(self.directory.name).name + '-outside.jpg')
        Image.new('RGB', (2, 2), 'white').save(outside, format='JPEG')
        self.addCleanup(outside.unlink)
        link = Path(self.directory.name, 'upload/products/link.jpg')
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(outside)
        self.product('upload/products/link.jpg')
        self.assertEqual(self.client.get('/media/upload/products/link.jpg').status_code, 404)
