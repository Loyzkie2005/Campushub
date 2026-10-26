"""FCM installation ownership uses the existing Django mobile bearer identity."""
import hashlib
import json
import re
from datetime import datetime, timezone

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from api.models import PushDeviceRegistration


def session_digest(request):
    token = request.headers["Authorization"].partition(" ")[2].strip()
    return hashlib.sha256(token.encode()).hexdigest()


@csrf_exempt
@never_cache
@require_http_methods(["POST", "DELETE"])
def device_registration(request):
    from api.views import _mobile_user_from_bearer
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    try:
        data = json.loads(request.body)
        fid = data.get("installation_id") if isinstance(data, dict) else None
        if not isinstance(fid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{20,160}", fid):
            raise ValueError
    except (ValueError, TypeError, UnicodeDecodeError):
        return JsonResponse({"error": "Enter a valid Firebase installation ID."}, status=400)
    digest = session_digest(request)
    if request.method == "DELETE":
        # An old logout must never deactivate a different account/new login.
        PushDeviceRegistration.objects.filter(installation_id=fid, user=user,
                                               session_digest=digest).update(is_active=False)
    else:
        with transaction.atomic():
            PushDeviceRegistration.objects.update_or_create(installation_id=fid, defaults={
                "user": user, "session_digest": digest, "is_active": True,
                "valid_until": datetime.fromtimestamp(request.mobile_auth_claims["exp"], timezone.utc),
            })
    return JsonResponse({"ok": True})
