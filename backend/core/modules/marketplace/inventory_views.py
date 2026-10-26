import json

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services.fifo import FIFOError, receive


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_products", raise_exception=True)
@require_POST
def receive_stock(request):
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("Send a receiving form object.")
        data = receive(payload.get("sku"), payload.get("quantity"), payload.get("reference"), request.user, payload.get("key"))
        return JsonResponse(data)
    except (FIFOError, ValueError, TypeError) as exc:
        return JsonResponse({"error": str(exc)}, status=409)
