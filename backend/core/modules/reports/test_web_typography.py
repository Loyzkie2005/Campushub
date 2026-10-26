"""All web role shells share one font system; the mobile client is untouched."""
import os
from pathlib import Path

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from accounts import tests as fixtures
from accounts.models import Role, User
from accounts.role_permissions import set_role_permissions, sync_user_admin_permissions


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class WebTypographyTests(fixtures.DedicatedDomainDashboardTests):
    def test_shared_typography_loads_for_role_shells_and_login(self):
        role = Role.objects.create(role_name='Typography custom admin')
        set_role_permissions(role, ['can_view_products'])
        custom = User.objects.create_user(username='type-custom', role=role.role_name, is_staff=True)
        sync_user_admin_permissions(custom)
        directory = os.environ.get('DASHBOARD_REVIEW_DIR')
        for name, user, route in (
            ('super-admin', self.super_admin, 'admin_dashboard_page'),
            ('marketplace-admin', self.marketplace_admin, 'admin_dashboard_page'),
            ('facilities-admin', self.facilities_admin, 'admin_dashboard_page'),
            ('custom-admin', custom, 'admin_products_page'),
        ):
            with self.subTest(role=name):
                self.client.force_login(user)
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'components/css/web_typography.css', count=1)
                self.assertContains(response, 'components/css/campushub_brand.css', count=1)
                if directory:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    Path(directory, f'typography-{name}.html').write_bytes(response.content)
        self.client.logout()
        login = self.client.get(reverse('admin_login_page'))
        self.assertContains(login, 'components/css/web_typography.css', count=1)
        self.assertContains(login, 'login-brand-name')
        if directory:
            Path(directory, 'typography-login.html').write_bytes(login.content)
        # Font is self-hosted: the interface does not require a third-party font request.
        font = Path(settings.BASE_DIR).parent / 'static/assets/fonts/InterVariable.woff2'
        self.assertEqual(font.read_bytes()[:4], b'wOF2')
        self.assertTrue(font.with_name('Inter-LICENSE.txt').is_file())
