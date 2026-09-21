"""Authentication bridge and contact discovery for FastAPI chat."""

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse

from api.models import CampusHubUser

from .auth import admin_chat_token


def _chat_service_config(request):
    http_url = settings.CHAT_SERVICE_HTTP_URL
    ws_url = settings.CHAT_SERVICE_WS_URL

    # Loopback is valid for a browser on the same PC, but not for a browser
    # opened from another device on the LAN.
    host = request.get_host().split(":", 1)[0]
    if host not in {"127.0.0.1", "localhost", "[::1]"}:
        http_url = f"http://{host}:8001"
        ws_url = f"ws://{host}:8001/ws"
    return {
        "http_url": http_url,
        "ws_url": ws_url,
    }


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_access_messages", login_url="admin_dashboard_page")
def chat_token(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    return JsonResponse(
        {
            "token": admin_chat_token(request.user),
            "actor_key": f"admin:{request.user.id}",
            "display_name": request.user.get_full_name().strip()
            or request.user.username,
            **_chat_service_config(request),
        }
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_access_messages", login_url="admin_dashboard_page")
def chat_contacts(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    query = (request.GET.get("search") or "").strip()
    users = CampusHubUser.objects.all().order_by("first_name", "last_name", "username")
    if query:
        from django.db.models import Q

        users = users.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
        )

    contacts = [
        {
            "actor_key": f"mobile:{user.id}",
            "display_name": (
                f"{user.first_name} {user.last_name}".strip() or user.username
            ),
            "username": user.username,
            "role": "Student",
        }
        for user in users[:50]
    ]
    return JsonResponse({"contacts": contacts})
