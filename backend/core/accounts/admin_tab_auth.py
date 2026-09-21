import secrets
from datetime import timedelta

from django.utils import timezone

from .models import AdminTabToken

ADMIN_TAB_QUERY = "__at"
ADMIN_TAB_HEADER = "X-Admin-Tab-Token"


def get_tab_token_from_request(request):
    token = request.GET.get(ADMIN_TAB_QUERY)
    if not token:
        token = request.headers.get(ADMIN_TAB_HEADER)
    token = (token or "").strip()
    return token or None


def create_admin_tab_token(user, remember_me=False):
    now = timezone.now()
    key = secrets.token_urlsafe(32)
    expires_at = now + (
        timedelta(days=30) if remember_me else timedelta(hours=12)
    )
    AdminTabToken.objects.create(
        key=key,
        user=user,
        last_seen_at=now,
        expires_at=expires_at,
        remember_me=remember_me,
    )
    return key


def get_user_for_tab_token(key):
    if not key:
        return None

    try:
        record = AdminTabToken.objects.select_related("user").get(key=key)
    except AdminTabToken.DoesNotExist:
        return None

    now = timezone.now()
    if record.expires_at <= now:
        record.delete()
        return None

    user = record.user
    if not user.is_active:
        return None
    if record.last_seen_at is None or record.last_seen_at <= now - timedelta(minutes=1):
        AdminTabToken.objects.filter(pk=record.pk).update(last_seen_at=now)
    return user


def revoke_admin_tab_token(key):
    if not key:
        return
    AdminTabToken.objects.filter(key=key).delete()


def append_tab_token_to_url(url, token):
    if not url or not token:
        return url
    separator = "&" if "?" in url else "?"
    if f"{ADMIN_TAB_QUERY}=" in url:
        return url
    return f"{url}{separator}{ADMIN_TAB_QUERY}={token}"
