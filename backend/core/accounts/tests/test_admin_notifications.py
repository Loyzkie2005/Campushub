# Original location: backend/core/accounts/test_admin_notifications.py
"""Retired-page and existing bell checks; fixtures never use business records."""
import json
import os
from pathlib import Path

from django.contrib.auth.context_processors import PermWrapper
from django.db import connection
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from api.models import CampusHubUser, SellerRequest
from accounts.models import Department, User
from accounts.role_permissions import sync_user_admin_permissions
from accounts.views import get_notification_context


class AdminNotificationsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        self.program = Department.objects.get(code='BSIT')
        self.other_program = Department.objects.exclude(pk=self.program.pk).first()
        self.admins = {}
        for label, role in [('super', 'Super Admin'), ('market', 'Marketplace Admin'), ('facilities', 'Facilities Admin')]:
            actor = User.objects.create_user(username='bell-' + label, role=role,
                department=self.program if label == 'market' else None)
            sync_user_admin_permissions(actor)
            self.admins[label] = actor
        for label, program in [('scoped', self.program), ('other', self.other_program)]:
            applicant = User.objects.create_user(username='bell-applicant-' + label, role='User', department=program)
            SellerRequest.objects.create(user=applicant, student_id=applicant.username,
                full_name='Bell applicant ' + label, product_type='Fixture only', message='Isolated request')

    def test_old_bookmarks_redirect_for_all_admin_roles_without_changing_records(self):
        before = list(SellerRequest.objects.values())
        for actor in self.admins.values():
            with self.subTest(role=actor.role):
                self.client.force_login(actor)
                self.assertRedirects(self.client.get(reverse('admin_notifications_page')),
                    reverse('admin_dashboard_page'), fetch_redirect_response=False)
        self.assertEqual(list(SellerRequest.objects.values()), before)

    def test_legacy_route_keeps_authentication_and_permission_checks(self):
        url = reverse('admin_notifications_page')
        self.assertRedirects(self.client.get(url), reverse('admin_login_page') + '?next=' + url,
            fetch_redirect_response=False)
        ordinary = User.objects.create_user(username='bell-no-admin', role='User')
        self.client.force_login(ordinary)
        self.assertRedirects(self.client.get(url), reverse('admin_dashboard_page') + '?next=' + url,
            fetch_redirect_response=False)

    def test_bell_and_scoped_pending_context_survive_without_sidebar_entry(self):
        expected = {'super': 2, 'market': 1, 'facilities': 0}
        exported = {}
        for label, actor in self.admins.items():
            with self.subTest(role=actor.role):
                context = {**get_notification_context(user=actor), 'user': actor, 'perms': PermWrapper(actor)}
                self.assertEqual(context['pending_seller_requests'], expected[label])
                header = render_to_string('partials/admin_header.html', context)
                sidebar = render_to_string('partials/admin_sidebar.html', context)
                self.assertNotIn('/admin-notifications/', sidebar)
                self.assertNotIn(reverse('admin_messages_page'), sidebar)
                self.assertNotIn(reverse('admin_settings_page'), sidebar)
                self.assertNotIn('System Settings', sidebar)
                self.assertNotIn('>System<', sidebar)
                self.assertIn(f'href="{reverse("admin_messages_page")}" class="chat-header-see-all"', header)
                self.assertIn(f'href="{reverse("admin_settings_page")}"', header)
                self.assertIn(f'href="{reverse("admin_logout_page")}"', header)
                self.assertNotIn('href="#"', header)
                self.client.force_login(actor)
                self.assertEqual(self.client.get(reverse('admin_messages_page')).status_code, 200)
                self.assertEqual(self.client.get(reverse('admin_settings_page')).status_code, 200)
                self.assertIn('class="header-icon-btn notif-btn"', header)
                self.assertIn('data-notification-filter="all"', header)
                self.assertIn('data-notification-filter="unseen"', header)
                self.assertEqual(header.count('class="notification-menu-item is-unseen"'), expected[label])
                for application in context['seller_requests']:
                    if actor.is_superuser:
                        self.assertIn(reverse('marketplace_approve_seller_request', args=[application.pk]), header)
                folder = os.environ.get('ADMIN_BELL_REVIEW_DIR')
                if folder:
                    root = Path(folder)
                    root.mkdir(parents=True, exist_ok=True)
                    html = ('<!doctype html><html><head><link rel="stylesheet" href="/bootstrap.min.css">'
                        '<link rel="stylesheet" href="/static/components/css/admin_layout.css">'
                        '<link rel="stylesheet" href="/static/components/css/admin_header_menus.css"></head><body>'
                        + sidebar + '<div class="main-wrapper">' + header + '</div>'
                        '<script src="/bootstrap.bundle.min.js"></script>'
                        '<script src="/static/components/js/admin_notifications.js"></script></body></html>')
                    (root / (label + '.html')).write_text(html, encoding='utf-8')
                    exported[label] = {'count': expected[label], 'approve_actions': [
                        reverse('marketplace_approve_seller_request', args=[item.pk]) for item in context['seller_requests']]
                        if actor.is_superuser else []}
        if exported:
            (Path(os.environ['ADMIN_BELL_REVIEW_DIR']) / 'expected.json').write_text(json.dumps(exported), encoding='utf-8')

    def test_seller_review_module_and_api_keep_role_scoping(self):
        for label, actor in self.admins.items():
            self.client.force_login(actor)
            response = self.client.get(reverse('admin_sellers_page'))
            if label == 'facilities':
                self.assertNotEqual(response.status_code, 200)
            else:
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Bell applicant scoped')
                if label == 'market':
                    self.assertNotContains(response, 'Bell applicant other')
            self.assertEqual(self.client.get(reverse('marketplace_seller_requests')).status_code,
                403 if label == 'facilities' else 200)

    def test_dashboard_shortcuts_use_existing_review_and_activity_destinations(self):
        actor = self.admins['super']
        context = {'user': actor, 'perms': PermWrapper(actor), 'approval_items': [
            {'type': 'seller', 'title': 'Isolated seller review'}]}
        dashboard = render_to_string('dashboard/pages/admin_dashboard.html', context)
        self.assertNotIn('/admin-notifications/', dashboard)
        self.assertIn(reverse('admin_sellers_page') + '?status=pending', dashboard)
        self.assertIn(reverse('admin_user_monitoring_page'), dashboard)
        overview = render_to_string('dashboard/partials/super_admin_overview.html', context)
        self.assertNotIn('/admin-notifications/', overview)
        self.assertIn(reverse('admin_user_monitoring_page'), overview)
        denied = self.admins['facilities']
        overview = render_to_string('dashboard/partials/super_admin_overview.html',
            {'user': denied, 'perms': PermWrapper(denied)})
        self.assertNotIn(reverse('admin_user_monitoring_page'), overview)
