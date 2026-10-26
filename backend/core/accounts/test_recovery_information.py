"""Read-only assistance, honest method state and all retired mutation aliases."""
from unittest.mock import patch

from django.db import connection
from django.test import RequestFactory, TestCase
from django.urls import reverse

from api.models import CampusHubUser, PasswordResetCode
from .models import AccountActivity, User
from .recovery_codes import RecoveryError, send_code
from . import test_marketplace_support as fixtures
from .user_management import build_account_rows, mask_recovery_phone


class RecoveryInformationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    setUp = fixtures.MarketplaceSupportTests.setUp

    def test_phone_mask_and_missing_short_malformed_numbers(self):
        self.assertEqual(mask_recovery_phone('09817149863'), '09*****863')
        self.assertEqual(mask_recovery_phone('+63 981 714 9863'), '63*****863')
        self.assertEqual(mask_recovery_phone('123'), '***')
        self.assertEqual(mask_recovery_phone(''), 'Not recorded')
        self.assertEqual(mask_recovery_phone('not a number'), 'Not recorded')

    def test_read_only_information_uses_real_fields_without_sms_verification(self):
        self.local.contact_number = '09817149863'; self.local.save()
        with patch('modules.notifications.services.email_service.send_account_recovery_email') as mail:
            response = self.client.get(reverse('admin_users_page'))
            row = response.context['users'][0]
            self.assertTrue(row['can_assist_recovery'])
            self.assertEqual(row['masked_email'], 'lo***@example.com')
            self.assertEqual(row['masked_phone'], '09*****863')
            self.assertTrue(row['email_verified'])
            self.assertFalse(row['sms_verified'])
            self.assertFalse(row['sms_recovery_available'])
            self.assertContains(response, 'SMS recovery is not currently configured')
            for retired in ('accountRecoveryForm', 'recoverySent', 'continueRecovery', 'recoveryOptions'):
                self.assertNotContains(response, 'id="' + retired + '"')
            mail.assert_not_called()
        self.assertFalse(PasswordResetCode.objects.exists())
        self.assertFalse(AccountActivity.objects.filter(activity_type__contains='RECOVERY').exists())

    def test_no_email_no_verified_method_still_has_information_and_marketplace_referral(self):
        self.local.email = ''; self.local.email_verified = False; self.local.save()
        row = build_account_rows(self.actor)[0]
        self.assertTrue(row['can_assist_recovery'])
        self.assertFalse(row['email_verified']); self.assertFalse(row['sms_verified'])
        self.assertTrue(row['recovery_referral'])
        super_rows = {row['ref']: row for row in build_account_rows(self.super)}
        self.assertFalse(super_rows[f'mobile:{self.local.pk}']['recovery_referral'])

    def test_every_admin_alias_for_normal_target_denied_without_password_or_audit_changes(self):
        before = self.local.password_hash
        with patch('modules.notifications.services.email_service.send_account_recovery_email') as mail:
            for actor in (self.actor, self.super):
                self.client.force_login(actor)
                for action in ('assist_recovery', 'reset_password', 'verify_email'):
                    response = self.client.post(reverse('admin_users_action'), {
                        'account_ref': f'mobile:{self.local.pk}', 'action': action,
                        'password': 'AdminChooses7!', 'confirm_password': 'AdminChooses7!', 'confirm_reset': '1'},
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    self.assertEqual(response.status_code, 403)
                # Plain POST cannot bypass the JSON path either.
                self.assertEqual(self.client.post(reverse('admin_users_action'), {
                    'account_ref': f'mobile:{self.local.pk}', 'action': 'assist_recovery'}).status_code, 403)
            mail.assert_not_called()
        self.local.refresh_from_db(); self.assertEqual(self.local.password_hash, before)
        self.assertFalse(PasswordResetCode.objects.exists())
        self.assertFalse(AccountActivity.objects.filter(activity_type__contains='RECOVERY').exists())

    def test_shared_service_denies_assisted_issuance_for_normal_and_admin_targets(self):
        request = RequestFactory().post('/admin-users/action/'); request.user = self.super
        with patch('modules.notifications.services.email_service.send_account_recovery_email') as mail:
            for source, target in (('mobile', self.local), ('admin', self.actor)):
                with self.assertRaises(RecoveryError) as failure:
                    send_code(request, source, target, 'password', assisted=True)
                self.assertEqual(failure.exception.status, 403)
            mail.assert_not_called()
        self.assertFalse(PasswordResetCode.objects.exists())

    def test_foreign_program_major_and_administrator_recovery_information_hidden(self):
        for target in (self.other, self.foreign, self.actor, self.super):
            response = self.client.get(reverse('admin_users_page'), {'q': target.username})
            self.assertEqual(response.context['users'], [])
            self.assertNotContains(response, 'class="dropdown-item assist-recovery"')

    def test_facilities_actor_cannot_read_users_page(self):
        from .role_permissions import sync_user_admin_permissions
        actor = User.objects.create_user(username='facilities-read-test', role='Facilities Admin')
        sync_user_admin_permissions(actor); self.client.force_login(actor)
        self.assertNotEqual(self.client.get(reverse('admin_users_page')).status_code, 200)
