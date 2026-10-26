import json
import os
import tempfile
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AccountActivity, User
from .dashboard_health import backup_status, build_system_status, chat_service_status, database_status


class ServiceHealthTests(TestCase):
    def test_database_uses_only_a_lightweight_query(self):
        with patch("modules.reports.dashboard_health.connection.cursor") as cursor:
            cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
            data = database_status()
            cursor.return_value.__enter__.return_value.execute.assert_called_once_with("SELECT 1")
        self.assertEqual(data["status"], "online")
        self.assertTrue(data["checked_at"].endswith("+08:00"))

    def test_database_errors_are_unavailable_without_disclosing_exceptions(self):
        with patch("modules.reports.dashboard_health.connection.cursor", side_effect=DatabaseError("private connection detail")), self.assertLogs("modules.reports.dashboard_health", level="WARNING"):
            data = database_status()
        self.assertEqual(data["status"], "unavailable")
        self.assertNotIn("private", json.dumps(data))

    def test_unexpected_database_result_is_unknown(self):
        with patch("modules.reports.dashboard_health.connection.cursor") as cursor:
            cursor.return_value.__enter__.return_value.fetchone.return_value = None
            self.assertEqual(database_status()["status"], "unknown")

    @override_settings(CHAT_SERVICE_HTTP_URL="http://configured-chat:8001")
    def test_chat_validates_existing_health_body_and_uses_short_timeout(self):
        for body, expected in ((b'{"status":"ok"}', "online"), (b'{"status":"degraded"}', "degraded"),
                               (b'{"anything":"else"}', "unknown"), (b'[]', "unknown"), (b'x' * 4097, "unknown")):
            with self.subTest(body=body[:30]), patch("modules.reports.dashboard_health.urlopen") as opener:
                response = opener.return_value.__enter__.return_value
                response.status = 200
                response.read.return_value = body
                data = chat_service_status()
                self.assertEqual(data["status"], expected)
                request = opener.call_args.args[0]
                self.assertEqual(request.full_url, "http://configured-chat:8001/health")
                self.assertEqual(opener.call_args.kwargs["timeout"], 1.5)
                response.read.assert_called_once_with(4097)

    def test_chat_http_error_timeout_and_bad_json_are_isolated(self):
        for failure in (URLError("private host"), TimeoutError("private timeout")):
            with self.subTest(failure=failure), patch("modules.reports.dashboard_health.urlopen", side_effect=failure), self.assertLogs("modules.reports.dashboard_health", level="WARNING") as logs:
                data = chat_service_status()
                self.assertEqual(data["status"], "unavailable")
                self.assertNotIn("private", json.dumps(data))
                self.assertEqual(len(logs.records), 1)
                self.assertIsNone(logs.records[0].exc_info)
                self.assertIn(type(failure).__name__, logs.output[0])
                self.assertNotIn("private", logs.output[0])
        with patch("modules.reports.dashboard_health.urlopen") as opener, self.assertLogs("modules.reports.dashboard_health", level="WARNING"):
            opener.return_value.__enter__.return_value.status = 200
            opener.return_value.__enter__.return_value.read.return_value = b'not-json'
            self.assertEqual(chat_service_status()["status"], "unknown")
        with patch("modules.reports.dashboard_health.urlopen") as opener:
            opener.return_value.__enter__.return_value.status = 503
            self.assertEqual(chat_service_status()["status"], "unavailable")

    def test_invalid_chat_configuration_is_unknown(self):
        for url in ("", "file:///private/path", "http://["):
            with self.subTest(url=url), override_settings(CHAT_SERVICE_HTTP_URL=url), patch("modules.reports.dashboard_health.logger"):
                self.assertEqual(chat_service_status()["status"], "unknown")


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BackupHealthTests(TestCase):
    now = datetime(2026, 10, 4, 8, tzinfo=dt_timezone.utc)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="campushub-health-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for target, value in (("accounts.backup_service.BACKUP_DIR", self.directory),
                              ("accounts.backup_service.AUTO_BACKUP_CONFIG", self.directory / "auto_backup_config.json"),
                              ("modules.reports.dashboard_health.timezone.now", self.now)):
            patcher = patch(target, return_value=value) if target.endswith("timezone.now") else patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def file(self, name, age=timedelta(), content=b"isolated fixture"):
        path = self.directory / name
        path.write_bytes(content)
        stamp = (self.now - age).timestamp()
        os.utime(path, (stamp, stamp))
        return path

    def config(self, enabled=True, frequency="daily"):
        (self.directory / "auto_backup_config.json").write_text(json.dumps({"enabled": enabled, "frequency": frequency}), encoding="utf-8")

    def attempt(self, result, when=None, activity_type="system_backup"):
        row = AccountActivity.objects.create(account_source="admin", activity_type=activity_type,
                                             activity="Isolated backup test", result=result, module="Backup & Restore")
        AccountActivity.objects.filter(pk=row.pk).update(created_at=when or self.now)
        return row

    def test_empty_directory_has_no_successful_backup(self):
        data = backup_status()
        self.assertEqual(data["status"], "no_backup_available")
        self.assertIsNone(data["last_successful_backup"])

    def test_real_file_metadata_and_config_determine_health(self):
        self.file("campushub_postgres_recent.sql", timedelta(hours=1))
        self.config()
        data = backup_status()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["last_successful_backup"], "2026-10-04T15:00:00+08:00")
        self.assertNotIn("filepath", data)
        self.assertNotIn("filename", data)

    def test_saved_frequency_and_disabled_preference(self):
        self.file("campushub_postgres_old.sql", timedelta(days=3))
        self.config()
        self.assertEqual(backup_status()["status"], "warning")
        self.config(frequency="weekly")
        self.assertEqual(backup_status()["status"], "healthy")
        self.config(enabled=False)
        self.assertEqual(backup_status()["status"], "healthy")
        self.assertIn("disabled", backup_status()["message"])

    def test_monthly_preference_uses_calendar_month(self):
        from .dashboard_health import _backup_deadline
        start = datetime(2026, 1, 31, 8, tzinfo=dt_timezone.utc)
        self.assertEqual(_backup_deadline(start, "monthly"), start.replace(month=2, day=28))
        self.assertEqual(_backup_deadline(start.replace(month=12), "monthly"), start.replace(year=2027, month=1))

    def test_latest_zero_size_or_logged_failed_attempt_is_failed(self):
        self.file("campushub_postgres_success.sql", timedelta(hours=2))
        self.file("campushub_postgres_empty.sql", timedelta(hours=1), content=b"")
        data = backup_status()
        self.assertEqual(data["status"], "failed")
        self.assertIsNotNone(data["last_successful_backup"])
        (self.directory / "campushub_postgres_empty.sql").unlink()
        self.attempt("failed")
        self.assertEqual(backup_status()["status"], "failed")
        self.file("campushub_postgres_next.sql", timedelta())
        self.attempt("success", self.now + timedelta(seconds=1))
        self.assertEqual(backup_status()["status"], "healthy")

    def test_failure_without_any_success_and_unrelated_restore_are_distinct(self):
        self.attempt("failed", activity_type="system_restore")
        self.assertEqual(backup_status()["status"], "no_backup_available")
        self.attempt("failed")
        self.assertEqual(backup_status()["status"], "failed")

    def test_newer_completion_supersedes_old_failure_and_deleted_files(self):
        self.attempt("failed", self.now - timedelta(days=2))
        file = self.file("campushub_postgres_current.sql", timedelta(hours=1))
        self.assertEqual(backup_status()["status"], "healthy")
        file.unlink()
        self.assertEqual(backup_status()["status"], "failed")
        AccountActivity.objects.all().delete()
        self.attempt("success")
        self.assertEqual(backup_status()["status"], "no_backup_available")

    def test_invalid_config_or_unreadable_sources_are_unknown(self):
        self.file("campushub_postgres_good.sql")
        for config in ("broken-json", '{"enabled":true,"frequency":"invalid"}'):
            (self.directory / "auto_backup_config.json").write_text(config, encoding="utf-8")
            with patch("modules.reports.dashboard_health.logger"):
                self.assertEqual(backup_status()["status"], "unknown")
        with patch("modules.reports.dashboard_health.os.scandir", side_effect=PermissionError("private directory")), patch("modules.reports.dashboard_health.logger"):
            data = backup_status()
        self.assertEqual(data["status"], "unknown")
        self.assertNotIn("private", json.dumps(data))
        with patch("modules.reports.dashboard_health.AccountActivity.objects.filter", side_effect=DatabaseError("private log")), patch("modules.reports.dashboard_health.logger"):
            self.assertEqual(backup_status()["status"], "unknown")

    def test_metadata_scan_and_latest_attempt_are_bounded(self):
        for index in range(20):
            self.file(f"campushub_postgres_{index}.sql", timedelta(hours=index))
        self.file("restore_other.sql")
        self.file("not_a_backup.txt")
        with self.assertNumQueries(1):
            data = backup_status()
        self.assertEqual(data["status"], "healthy")

    def test_status_only_branch_is_authorized_and_independent_of_analytics(self):
        super_admin = User.objects.create_superuser(username="health-admin", role="Super Admin")
        self.client.force_login(super_admin)
        status = {"database": {"status": "unavailable"}, "chat_service": {"status": "online"}, "backup": {"status": "unknown"}}
        with patch("modules.reports.dashboard_health.build_system_status", return_value=status), patch("modules.reports.views.build_dashboard_data", side_effect=DatabaseError("analytics unavailable")) as analytics:
            response = self.client.get(reverse("admin_dashboard_api"), {"system_status_only": "1", "period": "bad", "chat_host": "http://untrusted"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"system_status": status})
        analytics.assert_not_called()
        self.assertEqual(self.client.post(reverse("admin_dashboard_api"), {"system_status_only": "1"}).status_code, 405)
        user = User.objects.create_user(username="health-student", role="Student")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("admin_dashboard_api"), {"system_status_only": "1"}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("admin_dashboard_api"), {"system_status_only": "1"}).status_code, 401)

    def test_combined_health_keeps_other_services_when_one_fails(self):
        with patch("modules.reports.dashboard_health.urlopen", side_effect=TimeoutError()), patch("modules.reports.dashboard_health.logger"):
            data = build_system_status()
        self.assertEqual(data["database"]["status"], "online")
        self.assertEqual(data["chat_service"]["status"], "unavailable")
        self.assertEqual(data["backup"]["status"], "no_backup_available")
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        if directory:
            target = Path(directory)
            target.mkdir(parents=True, exist_ok=True)
            (target / "payload-system-unavailable.json").write_text(json.dumps({"system_status": data}), encoding="utf-8")
            self.config()
            self.file("campushub_postgres_review.sql", timedelta(hours=1))
            with patch("modules.reports.dashboard_health.urlopen") as opener:
                response = opener.return_value.__enter__.return_value
                response.status = 200
                response.read.return_value = b'{"status":"ok"}'
                data = build_system_status()
            (target / "payload-system-healthy.json").write_text(json.dumps({"system_status": data}), encoding="utf-8")
            self.attempt("failed")
            with patch("modules.reports.dashboard_health.urlopen", side_effect=TimeoutError()), patch("modules.reports.dashboard_health.logger"):
                data = build_system_status()
            (target / "payload-system-failed.json").write_text(json.dumps({"system_status": data}), encoding="utf-8")
