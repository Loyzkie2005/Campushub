from .models import AccountActivity


def _without_credentials(value, depth=0):
    """Keep useful event context, but never persist credentials in metadata."""
    if depth > 6:
        return None
    if isinstance(value, dict):
        return {key: _without_credentials(item, depth + 1)
                for key, item in value.items()
                if isinstance(key, str) and not any(part in key.lower() for part in ("password", "token", "secret", "credential", "session", "authorization"))
                and key.lower() not in {"code", "otp", "verification_code", "reset_code", "recovery_code"}}
    if isinstance(value, list):
        return [_without_credentials(item, depth + 1) for item in value]
    return value


def _client_ip(request):
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",", 1)[0].strip()
    return forwarded or request.META.get("REMOTE_ADDR") or None


def log_account_activity(
    request,
    *,
    source,
    activity_type,
    activity,
    result,
    account=None,
    identifier="",
    session_identifier="",
    module="Authentication",
    metadata=None,
):
    """Persist a real account event without storing credentials or tokens."""
    account_id = getattr(account, "pk", None)
    username = getattr(account, "username", "") or identifier
    first_name = getattr(account, "first_name", "") or ""
    last_name = getattr(account, "last_name", "") or ""
    full_name = f"{first_name} {last_name}".strip()
    if source == AccountActivity.SOURCE_ADMIN:
        account_type = "admin"
    elif account is not None:
        account_type = (getattr(account, "user_type", "") or "guest").lower()
    else:
        account_type = ""

    metadata = _without_credentials(metadata or {})
    if not isinstance(metadata, dict):
        metadata = {}
    actor = getattr(request, "user", None)
    if module != "Authentication" and getattr(actor, "is_authenticated", False):
        metadata.setdefault("actor_admin_id", actor.pk)
        metadata.setdefault("actor_username", actor.username)
    return AccountActivity.objects.create(
        account_source=source,
        account_id=account_id,
        account_ref=f"{source}:{account_id}" if account_id else "",
        username=username,
        full_name=full_name,
        email=getattr(account, "email", "") or "",
        account_type=account_type,
        role=getattr(account, "role", "") or "",
        activity_type=activity_type,
        metadata=metadata,
        activity=activity,
        module=module,
        result=result,
        ip_address=_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:1000],
        # Retain the old function argument for callers; raw session IDs are secrets.
        session_identifier="",
    )


def log_marketplace_event(request, *, account, source="admin", activity_type, activity, metadata=None):
    """Record a real marketplace change against its owner/customer, not just its actor."""
    if account is None:
        return None  # Do not invent an account identity for unmatched legacy rows.
    return log_account_activity(request, source=source, account=account, activity_type=activity_type,
        activity=activity[:180], module="Marketplace", result=AccountActivity.RESULT_SUCCESS,
        metadata={"actor_admin_id": getattr(request.user, "pk", None), **(metadata or {})})


def log_seller_event(request, application, activity_type):
    account, source = (application.mobile_user, "mobile") if application.mobile_user_id else (application.user, "admin")
    if account is None:
        from django.db.models import Q
        from api.models import CampusHubUser
        matches = list(CampusHubUser.objects.filter(Q(username__iexact=application.student_id) |
            Q(student_id__iexact=application.student_id))[:2])
        if len(matches) != 1:
            return None
        account, source = matches[0], "mobile"
    return log_marketplace_event(request, account=account, source=source, activity_type=activity_type,
        activity=activity_type.replace("_", " ").title(), metadata={"seller_request_id": application.pk})
