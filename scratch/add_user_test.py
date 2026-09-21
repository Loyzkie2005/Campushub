def main():
    path = 'backend/core/accounts/tests.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    is_crlf = '\r\n' in content
    norm = content.replace('\r\n', '\n')

    addition = '''

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

        row = _row_from_admin(self.student, self.super_admin)
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
'''

    norm = norm + addition
    final = norm.replace('\n', '\r\n') if is_crlf else norm
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(final)

    print('accounts/tests.py updated successfully!')

if __name__ == '__main__':
    main()
