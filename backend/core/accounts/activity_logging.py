from .models import AccountActivity


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
        activity=activity,
        module=module,
        result=result,
        ip_address=_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:1000],
        session_identifier=(session_identifier or "")[:80],
    )
