"""Authenticated optional food preferences; never used as Apriori evidence."""
import json

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from .models import CampusHubUser, MobileFoodPreference
from modules.marketplace.services.customization import FOOD_CATEGORIES

# Presentation order only. The values/identifiers remain existing product categories.
FOOD_ORDER = ("Rice Meals", "Snacks", "Desserts", "Beverages", "Combo Meals", "Breakfast")


def preference_data(user):
    record = MobileFoodPreference.objects.filter(user=user).first()
    return {"preferred_category_ids": record.category_ids if record else [],
            "onboarding_stage": record.onboarding_stage if record else "complete"}


@csrf_exempt  # This endpoint accepts bearer authentication only, never cookie authority.
@never_cache
def mobile_food_preferences(request):
    from .views import _mobile_user_from_bearer, serialize_campushub_user
    if request.method not in ("GET", "POST"):
        return JsonResponse({"error": "Method not allowed."}, status=405)
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    if not user.profile_completed:
        return JsonResponse({"error": "Complete your profile first."}, status=409)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if not isinstance(data, dict) or set(data) - {"action", "category_ids"}:
                raise ValueError
            action = data.get("action")
            if action not in ("save", "skip", "finish"):
                raise ValueError
            ids = data.get("category_ids", [])
            if action == "save" and (not isinstance(ids, list) or any(
                    not isinstance(item, str) or item not in FOOD_CATEGORIES for item in ids)):
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({"error": "Select valid food categories."}, status=400)
        with transaction.atomic():
            # Same owner lock as first profile completion prevents skip/save races.
            CampusHubUser.objects.select_for_update().get(pk=user.pk)
            record, _ = MobileFoodPreference.objects.get_or_create(user=user)
            if action == "finish":
                if record.onboarding_stage == "preferences":
                    return JsonResponse({"error": "Continue or skip preferences first."}, status=409)
                record.onboarding_stage = "complete"
            else:
                if action == "save":
                    record.category_ids = [item for item in FOOD_ORDER if item in ids and item in FOOD_CATEGORIES]
                if record.onboarding_stage == "preferences":
                    record.onboarding_stage = "welcome"
            record.save()
    return JsonResponse({"categories": [{"id": item, "name": item} for item in FOOD_ORDER if item in FOOD_CATEGORIES],
                         "user": serialize_campushub_user(user)})
