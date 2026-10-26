"""Real tab/CSRF transport and mocked SMTP; never sends mail to application users."""
import json
from unittest.mock import patch

from django.core.mail.backends.smtp import EmailBackend
from django.db import connection
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from api.models import CampusHubUser, GmailConfig, PasswordResetCode
from .admin_tab_auth import create_admin_tab_token
from .models import User
from .test_marketplace_support import MarketplaceSupportTests
from modules.notifications.services import email_service


class RecoveryTransportTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    setUp = MarketplaceSupportTests.setUp

    def payload(self, client):
        return {"account_ref": f"mobile:{self.local.pk}", "action": "assist_recovery",
                "recovery_purpose": "password", "confirm_reset": "1",
                "csrfmiddlewaretoken": client.cookies["csrftoken"].value}

    @patch("modules.notifications.services.email_service.send_account_recovery_email")
    def test_tab_authenticated_page_has_information_only_modal(self, mail):
        token = create_admin_tab_token(self.actor)
        browser = Client(enforce_csrf_checks=True)
        page = browser.get(reverse("admin_users_page"), {"__at": token})
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'id="recoveryMethods"')
        self.assertNotContains(page, 'id="accountRecoveryForm"')
        self.assertNotContains(page, "Send Verification Code")
        self.assertNotIn("sessionid", browser.cookies)
        mail.assert_not_called(); self.assertFalse(PasswordResetCode.objects.exists())

    @patch("modules.notifications.services.email_service.send_account_recovery_email")
    def test_valid_tab_and_csrf_cannot_issue_admin_code(self, mail):
        token = create_admin_tab_token(self.actor)
        browser = Client(enforce_csrf_checks=True)
        browser.get(reverse("admin_users_page"), {"__at": token})
        result = browser.post(reverse("admin_users_action"), self.payload(browser),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_X_ADMIN_TAB_TOKEN=token)
        self.assertEqual(result.status_code, 403)
        self.assertIn("information-only", result.json()["error"])
        mail.assert_not_called(); self.assertFalse(PasswordResetCode.objects.exists())

    def test_forbidden_target_returns_json_and_does_not_reach_smtp(self):
        with patch("modules.notifications.services.email_service.send_account_recovery_email") as mail:
            result = self.client.post(reverse("admin_users_action"), {"account_ref": f"admin:{self.super.pk}",
                "action": "assist_recovery", "confirm_reset": "1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(result.status_code, 403)
        self.assertIn("information-only", result.json()["error"])
        mail.assert_not_called(); self.assertFalse(PasswordResetCode.objects.exists())

    def test_missing_csrf_still_denied_even_for_valid_tab(self):
        token = create_admin_tab_token(self.actor)
        with patch("modules.notifications.services.email_service.send_account_recovery_email") as mail:
            result = Client(enforce_csrf_checks=True).post(reverse("admin_users_action"), {
                "action": "assist_recovery", "account_ref": f"mobile:{self.local.pk}", "confirm_reset": "1"},
                HTTP_X_ADMIN_TAB_TOKEN=token, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(result.status_code, 403); mail.assert_not_called()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_USE_TLS=True, EMAIL_USE_SSL=False, EMAIL_TIMEOUT=15)
    def test_tls_and_ssl_are_exclusive_and_smtp_timeout_is_passed(self):
        with patch.object(email_service, "EmailMessage") as message:
            message.return_value.send.return_value = 1
            for ssl_mode, port in ((False, 587), (True, 465)):
                config = email_service._SmtpConfig("sender@example.com", "private-test-credential", smtp_port=port, use_ssl=ssl_mode)
                email_service._send_with_config(config, to_email="owner@example.com", subject="Test", body="Mocked body")
                backend = message.call_args.kwargs["connection"]
                self.assertIsInstance(backend, EmailBackend)
                self.assertEqual(backend.use_ssl, ssl_mode)
                self.assertEqual(backend.use_tls, not ssl_mode)
                self.assertEqual(backend.timeout, 15)
                message.return_value.send.assert_called_with(fail_silently=False)

    def test_database_port_465_selects_ssl_without_changing_existing_fields(self):
        GmailConfig.objects.create(gmail_user="sender@example.com", gmail_app_password="private-test-credential", smtp_port=465)
        config = email_service._from_database()
        assert config is not None, "Stored Gmail configuration was not loaded."
        self.assertTrue(config.use_ssl)

    def test_zero_accepted_email_cannot_report_delivery_success(self):
        with patch.object(email_service, "EmailMessage") as message:
            message.return_value.send.return_value = 0
            with self.assertRaises(RuntimeError):
                email_service._send_with_config(email_service._SmtpConfig("sender@example.com", "private-test-credential"),
                    to_email="owner@example.com", subject="Test", body="Mocked body")

    @patch("modules.notifications.services.email_service.send_account_recovery_email", side_effect=RuntimeError("private SMTP response"))
    def test_delivery_exception_logs_type_only_and_invalidates_code(self, mail):
        with self.assertLogs("accounts.recovery_codes", level="WARNING") as logs:
            result = self.client.post(reverse("mobile_password_reset"), json.dumps({"email": self.local.email}), content_type="application/json")
        self.assertEqual(result.status_code, 503)
        self.assertIn("RuntimeError", str(logs.output))
        self.assertNotIn("private SMTP response", str(logs.output))
        self.assertTrue(PasswordResetCode.objects.get().used)
        self.assertEqual(PasswordResetCode.objects.get().code_hash, "")
