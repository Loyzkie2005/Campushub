"""Authorized, GET-only live recommendations; research CSV is not a UI source."""
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .services.bundle_suggestions import (build_bundle_suggestions, can_view_bundle_suggestions,
                                         recommendation_presentation)


@never_cache
@require_GET
def bundle_suggestions_api(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)
    if not can_view_bundle_suggestions(user):
        return JsonResponse({'error': 'Permission denied.'}, status=403)
    if request.GET.get('source', 'live') != 'live':
        return JsonResponse({'error': 'Only live marketplace recommendations are available.'}, status=400)
    response = JsonResponse(recommendation_presentation(build_bundle_suggestions(user, source='live')))
    response['Cache-Control'] = 'private, no-store'
    return response
