# Original location: backend/core/modules/marketplace/test_product_catalog.py
"""Actual catalog queries/fixtures in disposable PostgreSQL, never working records."""
import json
import base64
import os
from pathlib import Path
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import User, Department, ProgramMajor
from api.models import Product, BundleComponent, MarketplaceOrder, CampusHubUser


@override_settings(CAMPUSHUB_FIFO_ENABLED=False, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ProductCatalogTests(TestCase):
    def setUp(self):
        self.program = Department.objects.create(name='Catalog Program', code='CAT', is_program=True)
        self.other_program = Department.objects.create(name='Other Program', code='OTH', is_program=True)
        self.major = ProgramMajor.objects.create(program=self.program, name='Catalog Major', code='CM')
        self.admin = User.objects.create_superuser(username='catalog-admin', role='Super Admin')
        self.seller = User.objects.create_user(username='catalog-seller', first_name='Catalog', last_name='Seller', role='Seller', department=self.program, major=self.major)
        self.client.force_login(self.admin)
        self.url = reverse('admin_products_page')
        self.rows = [self.product(name=f'Catalog Product {i:02}', approval_status='approved' if i % 2 else 'pending') for i in range(23)]
        self.archived = self.product(name='Archived pending listing', is_archived=True, approval_status='pending')
        self.rejected = self.product(name='Rejected supplies', approval_status='rejected')
        self.low = self.product(name='Low stock item', stock=2, low_stock_threshold=3)
        self.variant = self.product(name='Flavored item', customization_enabled=True, stock=22, customization_options=[{
            'name':'Flavor','selection':'single','required':True,'options':[
                {'name':'Vanilla','stock':20,'extra_price':'0','low_stock_threshold':3},
                {'name':'Chocolate','stock':2,'extra_price':'5','low_stock_threshold':3}]}])
        self.bundle = self.product(name='Derived bundle', product_type='bundle', stock=0)
        BundleComponent.objects.create(bundle=self.bundle, product=self.rows[1], required_quantity=2)

    def product(self, **extra):
        values = dict(seller=self.seller, name='Catalog item', price='25.50', category='School Supplies', stock=20, approval_status='approved')
        values.update(extra)
        return Product.objects.create(**values)

    def get(self, **params):
        response = self.client.get(self.url, {'format':'json', **params})
        self.assertEqual(response.status_code, 200, response.content[:300])
        return response.json()

    def test_overall_kpis_are_independent_of_filters_and_active_default(self):
        initial = self.get()
        self.assertEqual(initial['stats'], {'total':28,'pending':13,'approved':14,'rejected':1,'archived':1,'low_stock':2})
        self.assertEqual(initial['total'], 27)
        self.assertNotIn(f'data-product-id="{self.archived.pk}"', initial['rows_html'])
        for params in ({'search':'no match'}, {'status':'approved'}, {'listing_status':'archived'}, {'page':2}):
            self.assertEqual(self.get(**params)['stats'], initial['stats'])

    def test_filters_pagination_actual_sku_and_selected_values(self):
        first, second = self.get(), self.get(page=2)
        self.assertEqual(first['rows_html'].count('<tr data-product-id='), 10)
        self.assertEqual(second['rows_html'].count('<tr data-product-id='), 10)
        self.assertEqual((second['start'], second['end'], second['page']), (11,20,2))
        self.assertEqual(self.get(page=999)['page'], 3)
        self.assertEqual(self.get(search='Catalog Seller')['total'], 27)
        sku = self.low.inventory_skus.get(variant_name='').code
        sku_result = self.get(search=sku)
        self.assertEqual(sku_result['total'], 1)
        self.assertIn(sku, sku_result['rows_html'])
        self.assertEqual(self.get(status='pending', listing_status='all')['total'], 13)
        self.assertEqual(self.get(listing_status='archived')['total'], 1)
        self.assertEqual(self.get(program=self.other_program.pk)['total'], 0)
        self.assertEqual(self.get(program=self.program.pk, major=self.major.pk, category='School Supplies')['total'], 27)
        self.assertEqual(self.get(category='Nonexistent')['total'], 0)
        self.assertEqual(self.get(search='Rejected', status='rejected')['total'], 1)
        html = self.client.get(self.url, {'status':'rejected','listing_status':'archived','search':'Saved query'}).content.decode()
        self.assertIn('value="Saved query"', html)
        self.assertIn('value="archived" selected', html)
        self.assertIn('value="rejected" selected', html)

    def test_approved_kpi_scope_includes_archived_without_changing_active_default(self):
        self.archived.approval_status = 'approved'; self.archived.save()
        active = self.get(status='approved')
        full = self.get(status='approved', listing_status='all')
        self.assertEqual((active['total'], full['total'], active['stats']['approved']), (14,15,15))

    def test_inventory_variants_bundle_and_reservation_values_are_preserved(self):
        self.assertEqual(self.get(inventory_status='low_stock')['total'], 2)
        result = self.get(search='Flavored')
        self.assertIn('22 pcs', result['rows_html'])
        self.assertIn('1 variant Low Stock', result['rows_html'])
        self.assertIn('₱25.50', result['rows_html'])
        self.assertIn('₱30.50', result['rows_html'])
        self.assertIn('Flavor', result['rows_html'])
        self.assertEqual(self.get(search='Derived bundle')['total'], 1)
        self.assertIn('10 bundles available', self.get(search='Derived bundle')['rows_html'])
        MarketplaceOrder.objects.create(product=self.low, product_name=self.low.name, quantity=3, inventory_deducted=True, status='pending')
        self.assertIn('2 pcs', self.get(search='Low stock item')['rows_html'])
        self.low.refresh_from_db(); self.assertEqual(self.low.stock, 2)

    def test_json_and_html_respect_read_manage_and_academic_permissions(self):
        reader = User.objects.create_user(username='catalog-reader', role='User', department=self.program)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_products'))
        self.client.force_login(reader)
        page = self.client.get(self.url)
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'id="addProductButton"')
        if os.environ.get('PRODUCT_CATALOG_REVIEW_DIR'):
            directory = Path(os.environ['PRODUCT_CATALOG_REVIEW_DIR']); directory.mkdir(parents=True, exist_ok=True)
            directory.joinpath('reader.html').write_bytes(page.content)
        for action in ('edit','archive','approve','reject'):
            self.assertNotIn(f'btn-{action}-product', self.get()['rows_html'])
        foreign = self.product(name='Other program listing', department=self.other_program)
        self.assertEqual(self.get(search=foreign.name)['total'], 0)
        facilities = User.objects.create_user(username='catalog-facilities', role='Facilities Admin', is_staff=True)
        self.client.force_login(facilities)
        self.assertNotEqual(self.client.get(self.url, {'format':'json'}).status_code, 200)
        self.assertEqual(self.client.post(reverse('admin_archive_product', args=[self.low.pk])).status_code, 403)

    def test_mobile_seller_academic_inheritance_and_explicit_override(self):
        owner = CampusHubUser.objects.create(username='catalog-mobile', first_name='Mobile', last_name='Seller', email='catalog-mobile@example.test', department=self.program, major=self.major, password_hash='unused')
        product = Product.objects.create(mobile_seller=owner, name='Mobile inherited listing', price=12, stock=8, approval_status='pending')
        self.assertEqual(self.get(search='Mobile Seller', program=self.program.pk, major=self.major.pk)['total'], 1)
        product.department = self.other_program; product.major = None; product.save()
        self.assertEqual(self.get(search='Mobile inherited', program=self.program.pk)['total'], 0)
        self.assertEqual(self.get(search='Mobile inherited', program=self.other_program.pk)['total'], 1)

    def test_query_count_is_bounded_for_page_and_export_browser_fixtures(self):
        before, after = [0], [0]
        def count_into(counter):
            def capture(execute, sql, params, many, context):
                counter[0] += 1
                return execute(sql, params, many, context)
            return capture
        with connection.execute_wrapper(count_into(before)):
            self.get()
        for i in range(20):
            photo = ''
            if i == 19:
                from django.conf import settings
                photo = 'data:image/png;base64,' + base64.b64encode((Path(settings.BASE_DIR).parent/'static/assets/img/icon.png').read_bytes()).decode()
            extra = self.product(name=f'Extra Catalog {i}', image_url=photo)
        with connection.execute_wrapper(count_into(after)):
            self.get()
        self.assertGreater(before[0], 0)
        self.assertLessEqual(after[0], before[0] + 2)
        capture = os.environ.get('PRODUCT_CATALOG_REVIEW_DIR')
        if not capture: return
        directory = Path(capture); directory.mkdir(parents=True, exist_ok=True)
        directory.joinpath('products.html').write_bytes(self.client.get(self.url).content)
        queries = [{'listing_status':listing,'page':page} for listing in ('active','all','archived') for page in range(1,6)]
        queries += [{'listing_status':'all','status':status,'page':1} for status in ('pending','approved')]
        queries += [{'listing_status':'all','inventory_status':'low_stock','page':1},
                    {'listing_status':'active','search':'no match','page':1},
                    {'listing_status':'active','search':'Low stock item','page':1},
                    {'listing_status':'active','program':str(self.program.pk),'major':str(self.major.pk),'page':1},
                    {'listing_status':'active','program':str(self.program.pk),'page':1},
                    {'listing_status':'active','category':'School Supplies','page':1}]
        cases = [{'params':params,'data':self.get(**params)} for params in queries]
        directory.joinpath('cases.json').write_text(json.dumps({'cases':cases,'program':self.program.pk,'major':self.major.pk,
            'photo_id':extra.pk,'query_counts':{'before':before[0],'after':after[0]}}), encoding='utf-8')
