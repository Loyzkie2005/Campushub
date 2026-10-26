"""Lightweight, read-only health summaries for the existing dashboard API."""
import json
import logging
import os
from calendar import monthrange
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import connection
from django.utils import timezone

from accounts.models import AccountActivity

logger = logging.getLogger(__name__)
CHAT_HEALTH_TIMEOUT = 1.5


def _timestamp(value):
    return timezone.localtime(value, timezone=dt_timezone(timedelta(hours=8))).isoformat() if value else None


def _state(status, message, **details):
    return {"status": status, "message": message, "checked_at": _timestamp(timezone.now()), **details}


def database_status():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                return _state("unknown", "Unable to verify database status.")
        return _state("online", "Django database connection verified.")
    except Exception:
        logger.warning("Dashboard database health check failed.", exc_info=True)
        return _state("unavailable", "The database connection is unavailable.")


def chat_service_status():
    try:
        base = (getattr(settings, "CHAT_SERVICE_HTTP_URL", "") or "").rstrip("/")
        parsed = urlsplit(base)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return _state("unknown", "Unable to verify chat service status.")
        # Use only the server's configured origin; never a browser-supplied host.
        request = Request(f"{base}/health", headers={"Accept": "application/json"})
        with urlopen(request, timeout=CHAT_HEALTH_TIMEOUT) as response:
            if response.status != 200:
                return _state("unavailable", "Real-time messaging is currently unavailable.")
            raw = response.read(4097)
        if len(raw) > 4096:
            return _state("unknown", "Unable to verify chat service status.")
        payload = json.loads(raw)
        if isinstance(payload, dict) and payload.get("status") == "ok":
            return _state("online", "Real-time messaging health endpoint available.")
        if isinstance(payload, dict) and payload.get("status") == "degraded":
            return _state("degraded", "The messaging service reports degraded health.")
        return _state("unknown", "Unable to verify chat service status.")
    except (HTTPError, URLError, TimeoutError, ConnectionError, OSError) as error:
        # Offline services are an expected health result, not a dashboard crash.
        # Log the exception type only; URLs and connection details may be private.
        logger.warning("Dashboard chat health endpoint is unavailable (%s).", type(error).__name__)
        return _state("unavailable", "Real-time messaging is currently unavailable.")
    except Exception:
        logger.warning("Dashboard chat health response could not be verified.", exc_info=True)
        return _state("unknown", "Unable to verify chat service status.")


def _backup_deadline(completed_at, frequency):
    if frequency in {"daily", "weekly"}:
        return completed_at + timedelta(days=1 if frequency == "daily" else 7)
    if frequency == "monthly":
        year, month = (completed_at.year + 1, 1) if completed_at.month == 12 else (completed_at.year, completed_at.month + 1)
        return completed_at.replace(year=year, month=month, day=min(completed_at.day, monthrange(year, month)[1]))
    return None


def backup_status():
    last_successful = None
    try:
        from accounts.backup_service import BACKUP_DIR, get_auto_backup_config

        latest_file = None
        latest_successful = None
        # Reuse the Backup module's matching files and nonempty=Completed rule.
        # Read metadata only, retaining two candidates instead of loading all logs/files.
        with os.scandir(BACKUP_DIR) as files:
            for entry in files:
                if not (entry.name.startswith("campushub_") and entry.name.endswith(".sql") and entry.is_file(follow_symlinks=False)):
                    continue
                stat = entry.stat(follow_symlinks=False)
                candidate = (stat.st_mtime, stat.st_size)
                if latest_file is None or candidate[0] > latest_file[0]:
                    latest_file = candidate
                if stat.st_size > 0 and (latest_successful is None or candidate[0] > latest_successful[0]):
                    latest_successful = candidate
        if latest_successful:
            last_successful = datetime.fromtimestamp(latest_successful[0], tz=dt_timezone.utc)
        attempt = AccountActivity.objects.filter(
            account_source=AccountActivity.SOURCE_ADMIN, activity_type="system_backup", module="Backup & Restore",
        ).order_by("-created_at", "-pk").values("result", "created_at").first()
        details = {"last_successful_backup": _timestamp(last_successful)}
        if ((attempt and attempt["result"] == AccountActivity.RESULT_FAILED
             and (last_successful is None or attempt["created_at"] >= last_successful))
                or (latest_file and latest_file[1] == 0
                    and (latest_successful is None or latest_file[0] >= latest_successful[0]))):
            return _state("failed", "The latest recorded backup attempt failed.", **details)
        if last_successful is None:
            return _state("no_backup_available", "No completed backup file is available.", **details)
        config = get_auto_backup_config(strict=True)
        enabled = config.get("enabled")
        frequency = config.get("frequency")
        if not isinstance(enabled, bool) or frequency not in {"daily", "weekly", "monthly"}:
            return _state("unknown", "Backup files found; schedule preferences could not be verified.", **details)
        deadline = _backup_deadline(last_successful, frequency)
        if enabled and timezone.now() > deadline:
            return _state("warning", f"Last completed backup is older than the {frequency} preference.", **details)
        message = "Completed backup file available." if enabled else "Completed backup file available; automatic backup preference is disabled."
        return _state("healthy", message, **details)
    except Exception:
        logger.warning("Dashboard backup health could not be verified.", exc_info=True)
        return _state("unknown", "Unable to verify backup status.", last_successful_backup=_timestamp(last_successful))


def build_system_status():
    return {"database": database_status(), "chat_service": chat_service_status(), "backup": backup_status()}
