"""Code-only transport/security regression tests; no real emails or user edits."""
import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.db import connection
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from api.models import CampusHubUser, PasswordResetCode
from .models import AccountActivity, AdminTabToken
from . import test_marketplace_support as fixtures


class RecoveryCodeFlowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    setUp = fixtures.MarketplaceSupportTests.setUp

    def api(self, name, payload, **headers):
        return self.client.post(reverse(name), json.dumps(payload), content_type="application/json", **headers)

    def send(self, purpose="password", *, account=None):
        target = account or self.local
        headers = {}
        if purpose == "email_verification":
            from modules.messages.auth import mobile_chat_token
            headers["HTTP_AUTHORIZATION"] = "Bearer " + mobile_chat_token(target)
        with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True) as mail:
            response = self.api("mobile_password_reset", {"email": target.email, "purpose": purpose}, **headers)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(mail.called)
            self.assertNotIn("link", mail.call_args.kwargs)
            code = mail.call_args.kwargs["code"]
        return response, code

    def verify(self, code, purpose="password", account=None):
        return self.api("mobile_password_reset_verify", {"email": (account or self.local).email, "code": code, "purpose": purpose})

    def complete(self, grant, account=None, **extra):
        return self.api("mobile_password_reset_confirm", {"email": (account or self.local).email,
            "recovery_grant": grant, "new_password": "OwnerChooses7!", "confirm_password": "OwnerChooses7!", **extra})

    def test_owner_json_success_masks_destination_without_admin_audit(self):
        response, code = self.send()
        self.assertNotIn("Location", response)
        self.assertEqual(response.json()["masked_email"], "lo***@example.com")
        self.assertNotIn(code, response.content.decode())
        self.assertNotIn("recovery_grant", response.json())
        self.assertEqual(response.json()["resend_after"], 60)
        self.assertTrue(AccountActivity.objects.filter(activity_type="ACCOUNT_RECOVERY_CODE_SENT").exists())
        self.assertFalse(AccountActivity.objects.filter(metadata__actor_admin_id=self.actor.pk).exists())

    def test_super_admin_self_service_completes_in_app(self):
        self.client.force_login(self.super)
        self.super.email = "super-recovery@example.com"; self.super.email_verified = True; self.super.save()
        _, code = self.send(account=self.super)
        self.assertTrue(AccountActivity.objects.filter(activity_type="SELF_SERVICE_RECOVERY_INITIATED").exists())
        grant = self.verify(code, account=self.super).json()["recovery_grant"]
        AdminTabToken.objects.create(user=self.super, key="test-tab-token", expires_at=timezone.now()+timedelta(hours=1))
        self.assertEqual(self.complete(grant, account=self.super).status_code, 200)
        self.super.refresh_from_db(); self.assertTrue(self.super.check_password("OwnerChooses7!"))
        self.assertFalse(AdminTabToken.objects.filter(user=self.super).exists())

    def test_code_consumed_on_verification_then_grant_consumed_on_completion(self):
        _, code = self.send()
        row = PasswordResetCode.objects.get()
        self.assertTrue(check_password(code, row.code_hash))
        response = self.verify(code); self.assertEqual(response.status_code, 200)
        row.refresh_from_db(); self.assertTrue(row.used); self.assertFalse(check_password(code, row.code_hash))
        self.assertEqual(self.verify(code).status_code, 400)
        grant = response.json()["recovery_grant"]
        self.assertEqual(self.complete(grant).status_code, 200)
        self.assertEqual(self.complete(grant).status_code, 400)
        self.local.refresh_from_db(); self.assertTrue(check_password("OwnerChooses7!", self.local.password_hash))

    def test_direct_confirm_with_code_is_no_longer_allowed(self):
        _, code = self.send()
        self.assertEqual(self.complete("", code=code).status_code, 400)
        self.assertFalse(PasswordResetCode.objects.get().used)

    def test_username_only_revealed_after_proof_without_password_change(self):
        previous = self.local.password_hash
        response, code = self.send("username")
        self.assertNotIn("username", response.json())
        self.assertEqual(self.verify("000bad", "username").status_code, 400)
        result = self.verify(code, "username")
        self.assertEqual(result.json()["username"], self.local.username)
        self.assertNotIn("recovery_grant", result.json())
        self.assertEqual(self.verify(code, "username").status_code, 400)
        self.local.refresh_from_db(); self.assertEqual(self.local.password_hash, previous)
        self.assertTrue(AccountActivity.objects.filter(activity_type="USERNAME_RECOVERED").exists())

    def test_expired_code_has_explicit_message(self):
        _, code = self.send()
        PasswordResetCode.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.verify(code).json()["error"], "This verification code has expired.")

    def test_wrong_and_malformed_guesses_lock_code_persistently(self):
        _, code = self.send()
        for bad in ("bad", "１２３４５６", "", "11111", "1234567"):
            self.assertEqual(self.verify(bad).json()["error"], "Invalid verification code.")
        row = PasswordResetCode.objects.get(); self.assertEqual(row.attempts, 5); self.assertTrue(row.used)
        self.assertEqual(self.verify(code).status_code, 400)

    def test_cross_purpose_and_cross_account_proof_rejected(self):
        _, code = self.send("username")
        self.assertEqual(self.verify(code, "password").status_code, 400)
        PasswordResetCode.objects.all().delete()
        _, code = self.send()
        grant = self.verify(code).json()["recovery_grant"]
        self.foreign.email_verified = True; self.foreign.save()
        self.assertEqual(self.complete(grant, account=self.foreign).status_code, 400)
        self.assertEqual(self.complete(grant + "tampered").status_code, 400)

    def test_expired_changed_email_disabled_account_or_changed_password_blocks_grant(self):
        _, code = self.send(); grant = self.verify(code).json()["recovery_grant"]
        self.local.is_active = False; self.local.save()
        self.assertEqual(self.complete(grant).status_code, 400)
        self.local.is_active = True; self.local.email = "changed@example.com"; self.local.save()
        self.assertEqual(self.complete(grant).status_code, 400)
        self.local.email = "local@example.com"; self.local.save()
        PasswordResetCode.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.complete(grant).status_code, 400)

    def test_mismatch_and_weak_password_do_not_consume_completion_grant(self):
        _, code = self.send(); grant = self.verify(code).json()["recovery_grant"]
        self.assertEqual(self.complete(grant, confirm_password="Mismatch7!").status_code, 400)
        self.assertEqual(self.complete(grant, new_password="short", confirm_password="short").status_code, 400)
        self.assertEqual(self.complete(grant).status_code, 200)

    def test_resend_supersedes_old_code_and_verified_grant(self):
        _, old = self.send()
        grant = self.verify(old).json()["recovery_grant"]
        response = self.api("mobile_password_reset", {"email": self.local.email})
        self.assertEqual(response.status_code, 429)
        PasswordResetCode.objects.update(created_at=timezone.now()-timedelta(minutes=2))
        _, new = self.send()
        self.assertEqual(self.complete(grant).status_code, 400)
        self.assertEqual(self.verify(new).status_code, 200)

    def test_initial_email_verification_uses_recorded_authenticated_email(self):
        from modules.messages.auth import mobile_chat_token
        self.local.email_verified = False; self.local.save()
        bearer = {"HTTP_AUTHORIZATION": "Bearer " + mobile_chat_token(self.local)}
        payload = {"email": "attacker@example.com", "purpose": "email_verification"}
        with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True) as mail:
            response = self.api("mobile_password_reset", payload, **bearer)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(mail.call_args.kwargs["to_email"], self.local.email)
            code = mail.call_args.kwargs["code"]
        result = self.api("mobile_password_reset_verify", {**payload, "code": code}, **bearer)
        self.assertEqual(result.status_code, 200); self.assertTrue(result.json()["user"]["email_verified"])
        self.assertNotIn("recovery_grant", result.json())
        self.local.refresh_from_db(); self.assertTrue(self.local.email_verified)
        self.assertEqual(self.api("mobile_password_reset_verify", {**payload, "code": code}, **bearer).status_code, 400)

    def test_unverified_recovery_blocked_but_email_proof_available(self):
        self.local.email_verified = False; self.local.save()
        with patch("modules.notifications.services.email_service.send_account_recovery_email") as mail:
            response = self.api("mobile_password_reset", {"email": self.local.email})
            self.assertEqual(response.status_code, 200); self.assertFalse(mail.called)
            response = self.client.post(reverse("admin_users_action"), {"account_ref": f"mobile:{self.local.pk}",
                "action": "assist_recovery", "confirm_reset": "1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertEqual(response.status_code, 403); self.assertFalse(mail.called)
        _, code = self.send("email_verification")
        from modules.messages.auth import mobile_chat_token
        response = self.api("mobile_password_reset_verify", {"email": self.local.email, "code": code, "purpose": "email_verification"},
            HTTP_AUTHORIZATION="Bearer " + mobile_chat_token(self.local))
        self.assertEqual(response.status_code, 200)

    def test_scoped_admin_forbidden_and_csrf_required(self):
        for target in (self.other, self.foreign, self.super, self.actor):
            response = self.client.post(reverse("admin_users_action"), {"account_ref": f"{'admin' if hasattr(target, 'password') else 'mobile'}:{target.pk}",
                "action": "assist_recovery", "confirm_reset": "1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertEqual(response.status_code, 403)
        csrf = Client(enforce_csrf_checks=True); csrf.force_login(self.actor)
        self.assertEqual(csrf.post(reverse("admin_users_action"), {"action": "assist_recovery"}).status_code, 403)

    def test_unknown_ambiguous_email_has_no_delivery(self):
        with patch("modules.notifications.services.email_service.send_account_recovery_email") as mail:
            self.assertEqual(self.api("mobile_password_reset", {"email": "unknown@example.com"}).status_code, 200)
            self.super.email = self.local.email; self.super.save()
            self.assertEqual(self.api("mobile_password_reset", {"email": self.local.email}).status_code, 200)
            self.assertFalse(mail.called)

    def test_request_and_json_type_validation_does_not_crash(self):
        self.assertEqual(self.client.get(reverse("mobile_password_reset")).status_code, 405)
        self.assertEqual(self.api("mobile_password_reset", []).status_code, 400)
        self.assertEqual(self.api("mobile_password_reset", {"email": [1]}).status_code, 400)
        self.assertEqual(self.complete([]).status_code, 400)

    def test_account_audit_has_no_code_password_or_completion_secret(self):
        _, code = self.send(); grant = self.verify(code).json()["recovery_grant"]
        self.complete(grant)
        records = str(list(AccountActivity.objects.values()))
        for secret in (code, grant, "OwnerChooses7!"):
            self.assertNotIn(secret, records)
        for action in ("ACCOUNT_RECOVERY_INITIATED", "ACCOUNT_RECOVERY_CODE_SENT", "ACCOUNT_RECOVERY_CODE_VERIFIED", "PASSWORD_RESET_COMPLETED"):
            self.assertTrue(AccountActivity.objects.filter(activity_type=action).exists())

    def test_real_email_template_has_code_only_and_distinct_subjects(self):
        from modules.notifications.services.email_service import send_account_recovery_email
        with patch("modules.notifications.services.email_service.get_smtp_config", return_value=object()), \
             patch("modules.notifications.services.email_service._send_with_config") as smtp:
            for purpose in ("password", "username", "email_verification"):
                send_account_recovery_email(to_email="owner@example.com", code="123456", purpose=purpose, full_name="Campus Student")
                body = smtp.call_args.kwargs["body"]
                self.assertIn("123456", body); self.assertIn("15 minutes", body); self.assertIn("once", body)
                for forbidden in ("127.0.0.1", "localhost", "/account/recovery/", "http://", "https://"):
                    self.assertNotIn(forbidden, body)
                self.assertEqual(smtp.call_args.kwargs["subject"], "CampusHub Email Verification Code" if purpose == "email_verification" else "CampusHub Account Recovery Code")
