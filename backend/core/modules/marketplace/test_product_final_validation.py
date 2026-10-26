"""Admin product validation, persisted outcomes and rollback regressions."""
import base64
import json
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import Department, User
from api.models import Product


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ProductFinalValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        program, _ = Department.objects.get_or_create(code='BSIT', defaults={'name':'BSIT','is_program':True})
        cls.admin = User.objects.create_superuser(username='final-product-admin', role='Super Admin', department=program)

    def setUp(self):
        self.client.force_login(self.admin)
        self.payload = {'name':'Actual test item','price':'12.50','stock':10,'low_stock_threshold':2,'category':'Clothing'}

    def save(self, **changes):
        return self.client.post(reverse('admin_save_product'), json.dumps({**self.payload, **changes}), content_type='application/json')

    def image(self):
        buffer=BytesIO(); Image.new('RGB',(2,2),'white').save(buffer,format='PNG')
        return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()

    def test_invalid_inputs_are_readable_and_write_nothing(self):
        cases=[{'name':' '},{'name':'x'*151},{'category':''},{'category':'x'*81},{'price':'NaN'},{'program_id':{}},
               {'price':'-1'},{'price':'1.234'},{'stock':1.5},{'low_stock_threshold':-1},
               {'images':['data:image/png;base64,YmFk']},{'images':[self.image()]*7},
               {'customization_enabled':True,'customization_options':[]},
               {'customization_enabled':True,'customization_options':[{'name':'Size','options':[{'name':'Large','extra_price':'-2','stock':10}]}]}]
        for changes in cases:
            with self.subTest(changes=changes):
                response=self.save(**changes)
                self.assertEqual(response.status_code,400,response.content)
                self.assertIn('error',response.json())
                self.assertFalse(Product.objects.exists())
        for data in ([],None,'wrong'):
            response=self.client.post(reverse('admin_save_product'),json.dumps(data),content_type='application/json')
            self.assertEqual(response.status_code,400)

    def test_stock_adjustment_rejects_wrong_shape_and_overflow(self):
        product=Product.objects.create(seller=self.admin,name='Stock item',price=10,stock=8)
        for data in ([],None,{'stock':2147483648}):
            result=self.client.post(reverse('admin_update_product_stock',args=[product.pk]),json.dumps(data),content_type='application/json')
            self.assertEqual(result.status_code,400)
        product.refresh_from_db()
        self.assertEqual(product.stock,8)

    def test_gallery_validates_and_can_be_cleared_without_approval_change(self):
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response=self.save(images=[self.image()])
            self.assertEqual(response.status_code,201,response.content)
            product=Product.objects.get()
            self.assertEqual(product.approval_status,'approved')  # Existing authorized admin-create rule.
            self.assertTrue(product.get_image_list())
            response=self.save(id=product.pk,images=[],approval_status=product.approval_status)
            self.assertEqual(response.status_code,200,response.content)
            product.refresh_from_db()
            self.assertEqual(product.get_image_list(),[])
            self.assertFalse(product.is_archived)

    def test_image_write_failure_rolls_back_product_and_stock(self):
        with patch('api.views.persist_product_images',side_effect=OSError('storage failed')):
            response=self.save(images=[self.image()])
        self.assertEqual(response.status_code,500)
        self.assertFalse(Product.objects.exists())
        product=Product.objects.create(seller=self.admin,name='Original',price=10,stock=8)
        with patch('api.views.persist_product_images',side_effect=ValueError('invalid image')):
            response=self.save(id=product.pk,images=[self.image()],name='Changed',stock=40)
        self.assertEqual(response.status_code,400)
        product.refresh_from_db()
        self.assertEqual((product.name,product.stock),('Original',8))

    def test_pending_only_review_reason_and_archive_independence(self):
        product=Product.objects.create(seller=self.admin,name='Review me',price=10,stock=8,approval_status='pending')
        reject=reverse('marketplace_reject_product',args=[product.pk]);approve=reverse('marketplace_approve_product',args=[product.pk])
        self.assertEqual(self.client.post(reject).status_code,400)
        self.assertEqual(self.client.post(approve,HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code,200)
        self.assertEqual(self.client.post(reject,{'rejection_reason':'Stale review'}).status_code,409)
        self.assertEqual(self.client.post(reverse('admin_archive_product',args=[product.pk])).status_code,200)
        product.refresh_from_db();self.assertTrue(product.is_archived);self.assertEqual(product.approval_status,'approved')
        self.assertEqual(self.client.post(approve).status_code,409)
        self.assertEqual(self.client.post(reverse('admin_restore_product',args=[product.pk])).status_code,200)
        product.refresh_from_db();self.assertFalse(product.is_archived);self.assertEqual(product.approval_status,'approved')

    def test_single_option_group_and_saved_options_round_trip(self):
        options = [{'name':'Size','selection':'single','required':True,'options':[
            {'name':'Small','stock':10,'low_stock_threshold':2,'extra_price':'3.00'}]}]
        created = self.save(customization_enabled=True, customization_options=options)
        self.assertEqual(created.status_code, 201, created.content)
        product = Product.objects.get()
        self.assertEqual(product.get_total_stock(), 10)
        self.assertEqual(str(product.price), '12.50')
        self.assertEqual(product.customization_options[0]['options'][0]['extra_price'], '3.00')
        options[0]['options'].extend([
            {'name':'Medium','stock':0,'low_stock_threshold':0,'extra_price':'0.00'},
            {'name':'Large','stock':8,'low_stock_threshold':1,'extra_price':'5.00'},
        ])
        updated = self.save(id=product.pk, customization_enabled=True, customization_options=options)
        self.assertEqual(updated.status_code, 200, updated.content)
        product.refresh_from_db()
        self.assertEqual([row['name'] for row in product.customization_options[0]['options']], ['Small','Medium','Large'])
        self.assertEqual(product.get_total_stock(), 18)
        import os
        from pathlib import Path
        from api.views import serialize_product
        directory = os.environ.get('PRODUCT_FINAL_REVIEW_DIR')
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            page = self.client.get(reverse('admin_products_page'))
            self.assertEqual(page.status_code, 200)
            (target/'products-variants.html').write_bytes(page.content)
            (target/'products-variants.json').write_text(json.dumps([serialize_product(product)]), encoding='utf-8')

    def test_list_statistics_match_records_and_export_isolated_fixture(self):
        import os
        from pathlib import Path
        from api.views import serialize_product
        for index in range(23):
            Product.objects.create(seller=self.admin, department=self.admin.department, name=f'Isolated item {index:02}',
                category='Clothing' if index % 2 else 'School Supplies', price='12.50', stock=10,
                approval_status='pending' if index % 3 == 0 else 'approved', is_archived=index >= 21)
        page=self.client.get(reverse('admin_products_page'))
        self.assertEqual(page.status_code,200)
        stats=page.context['product_stats']
        self.assertEqual(stats['total'],Product.objects.count())
        self.assertEqual(stats['pending'],Product.objects.filter(approval_status='pending').count())
        self.assertEqual(stats['approved'],Product.objects.filter(approval_status='approved').count())
        directory=os.environ.get('PRODUCT_FINAL_REVIEW_DIR')
        if directory:
            target=Path(directory);target.mkdir(parents=True,exist_ok=True)
            (target/'products-list.html').write_bytes(page.content)
            (target/'products-list.json').write_text(json.dumps([serialize_product(p) for p in Product.objects.all()]),encoding='utf-8')
