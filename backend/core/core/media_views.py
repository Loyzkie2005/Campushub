"""Production catalog images with the same visibility as their database records."""

from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe

from api.models import Facility
from modules.marketplace.services.product_access import image_visible_product_queryset


IMAGE_TYPES = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.jpe': 'image/jpeg',
    '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif',
    '.avif': 'image/avif', '.bmp': 'image/bmp',
}


def _media_path(value):
    """Normalize a stored image URL; never fetch an external URL."""
    if not isinstance(value, str):
        return None
    try:
        path = unquote(urlsplit(value.strip()).path).lstrip('/')
    except ValueError:
        return None
    if path.startswith('media/'):
        path = path[len('media/'):]
    if not path or any(part in ('', '.', '..') for part in path.split('/')):
        return None
    if '\\' in path or '\x00' in path or '%' in path:
        return None
    return path


def _variant_images(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('image_url', 'image', 'images'):
                yield from item if isinstance(item, list) else [item]
            elif isinstance(item, (list, dict)):
                yield from _variant_images(item)
    elif isinstance(value, list):
        for item in value:
            yield from _variant_images(item)


def _is_visible(request, path):
    products = image_visible_product_queryset(request.user)
    needle = Path(path).name
    if path.startswith(('products/', 'upload/products/')):
        candidates = products.filter(
            Q(image_url__contains=needle) | Q(customization_options__icontains=needle)
        ).only('image_url', 'customization_options')
        return any(
            _media_path(image) == path
            for product in candidates
            for image in [*product.get_image_list(), *_variant_images(product.customization_options)]
        )
    if path.startswith('upload/facilities/'):
        # Matches the existing public facilities endpoint, including services.
        facilities = Facility.objects.filter(
            is_archived=False, image_url__contains=needle,
        ).only('image_url')
        return any(_media_path(image) == path
                   for facility in facilities for image in facility.get_image_list())
    if path.startswith('profile-photos/'):
        # Pending applicants need not have a catalog listing. Reuse the exact
        # Seller Applications scope for authorized reviewers, never publicize
        # an applicant's photo merely because a file exists.
        if request.user.is_authenticated and (
            request.user.has_perm('accounts.can_view_sellers')
            or request.user.has_perm('accounts.can_manage_sellers')
        ):
            from accounts.academic import scope_seller_requests
            from api.models import SellerRequest
            if scope_seller_requests(SellerRequest.objects.all(), request.user).filter(
                mobile_user__profile_photo=path,
            ).exists():
                return True
        # Public catalog payloads already publish these sellers' avatar URLs.
        return products.filter(mobile_seller__profile_photo=path).exists()
    return False


@require_safe
def catalog_image(request, image_path):
    """Serve a referenced, visible raster image; reject arbitrary/private files."""
    path = _media_path(image_path)
    if path != image_path or Path(path).suffix.lower() not in IMAGE_TYPES:
        raise Http404
    if not _is_visible(request, path):
        raise Http404
    root = Path(settings.MEDIA_ROOT).resolve()
    target = (root / path).resolve()
    if target != root / path or not target.is_relative_to(root) or not target.is_file():
        raise Http404
    try:
        stream = target.open('rb')
    except OSError:
        raise Http404
    response = FileResponse(stream, content_type=IMAGE_TYPES[target.suffix.lower()])
    response['X-Content-Type-Options'] = 'nosniff'
    # Approval/archive changes must be checked again instead of cached publicly.
    response['Cache-Control'] = 'private, no-store'
    response['Vary'] = 'Cookie, Authorization'
    return response
