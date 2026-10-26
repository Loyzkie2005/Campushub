"""Read-only monitoring helpers. Never serialize credentials or token identifiers."""
from datetime import timedelta

from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.utils import timezone

from .activity_service import display_role
from .models import AccountActivity, AdminTabToken, Role, User


def monitoring_load_guard(view):
    """A failed database read must show Retry, never fabricated zero metrics."""
    from functools import wraps
    from django.db import DatabaseError
    from django.shortcuts import render
    @wraps(view)
    def guarded(request):
        try:
            return view(request)
        except DatabaseError:
            return render(request, "user_management/pages/admin_user_monitoring.html",
                          {"monitoring_error": True}, status=503)
    return guarded


def timestamp(value):
    return timezone.localtime(value).strftime("%b %d, %Y %I:%M %p") if value else ""


def presence_age(value, now):
    if value is None:
        return ""
    seconds = max(0, int((now - value).total_seconds()))
    if seconds < 30:
        return "Active now"
    if seconds < 60:
        return "Just now"
    minutes = seconds // 60
    return f"{minutes} min ago"


def tracked_sessions(now, admin_ids):
    """Count the existing authenticated tab tokens, not anonymous Django rows.

    A token is usable only for an enabled account, before expiry, with recorded
    use in the last 12 hours (the existing ordinary admin token lifetime).
    Long-lived remembered tokens without recent use are not current sessions.
    """
    return AdminTabToken.objects.filter(
        user_id__in=admin_ids, user__is_active=True, user__is_suspended=False,
        expires_at__gt=now, created_at__lte=now,
        last_seen_at__gte=now - timedelta(hours=12), last_seen_at__lte=now,
    ).exclude(key="")


def recent_per_account(queryset, limit=20, partition="account_ref"):
    """Bound history in SQL instead of reading every audit row into Python."""
    return queryset.annotate(monitor_row=Window(
        expression=RowNumber(), partition_by=[F(partition)],
        order_by=[F("created_at").desc(), F("pk").desc()],
    )).filter(monitor_row__lte=limit).order_by("-created_at", "-pk")


def event_rows(events, *, scoped=False):
    """Keep the existing table contract, using the shared safe detail formatter."""
    from .activity_service import format_activities
    events = list(events)
    formatted = format_activities(events, scoped=scoped)
    rows = []
    for event, detail in zip(events, formatted):
        affected = detail["affected_record"]
        connection = detail["connection"] or {}
        rows.append({
            "id": str(event.pk), "time": timestamp(event.created_at),
            "actor": detail["performed_by"]["name"],
            "target": affected["name"] if affected else "\u2014",
            "action": detail["action"], "module": detail["module"],
            "result": detail["result"] or "\u2014",
            "result_value": event.result if event.result in dict(AccountActivity.RESULT_CHOICES) else "unknown",
            "ip": connection.get("ip_address") or "",
            "device": connection.get("device") or "",
            "detail": detail,
            # Drawer history retains its recorded description, not raw metadata.
            "activity": event.activity, "type": event.activity_type,
            "user": event.full_name or event.username or "Unknown",
            "role": display_role(event.role),
            "account_type": dict(AccountActivity.SOURCE_CHOICES).get(event.account_source, "Unknown") if event.account_type == "admin" else event.account_type.title(),
        })
    return rows
