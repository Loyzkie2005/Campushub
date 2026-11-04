"""Read-only identity and purchased-item presentation for seller order previews."""
import json

from accounts.models import User
from api.models import CampusHubUser


def buyer_full_names(orders):
    """Resolve names in two batch queries; overlapping account IDs need evidence."""
    ids = {order.buyer_user_id for order in orders if order.buyer_user_id}
    if not ids:
        return {order.pk: order.buyer_name.strip() for order in orders}
    fields = ("pk", "first_name", "last_name", "email", "username")
    mobile = {user.pk: user for user in CampusHubUser.objects.filter(pk__in=ids).only(*fields)}
    web = {user.pk: user for user in User.objects.filter(pk__in=ids).only(*fields)}
    result = {}
    for order in orders:
        candidates = [user for user in (mobile.get(order.buyer_user_id), web.get(order.buyer_user_id)) if user]
        email = order.buyer_email.strip().casefold()
        matches = [user for user in candidates if user.email.strip().casefold() == email] if email else candidates
        buyer = matches[0] if len(matches) == 1 else None
        full_name = buyer.get_full_name().strip() if buyer else ""
        recorded = order.buyer_name.strip()
        if any(recorded.casefold() == user.username.casefold() for user in candidates):
            recorded = ""
        result[order.pk] = full_name or recorded
    return result


def product_preview(order, items):
    """Use purchased snapshots, not current prices, names or bundle ingredients."""
    first = items[0] if items else {}
    data = order.customization if isinstance(order.customization, dict) else {}
    raw_items = data.get("items")
    raw = raw_items[0] if not data.get("bundle_components") and isinstance(raw_items, list) and raw_items and isinstance(raw_items[0], dict) else {}
    image = raw.get("image_url") or raw.get("thumbnail_url") or order.image_url or ""
    if not image and order.product_id:
        images = order.product.get_image_list()
        image = images[0] if images else ""
    if isinstance(image, str) and image.lstrip().startswith("["):
        try:
            image = json.loads(image)
        except (TypeError, ValueError):
            image = ""
    if isinstance(image, list):
        image = next((value for value in image if isinstance(value, str) and value.strip()), "")
    return {
        "product_name": first.get("product_name") or order.product_name,
        "quantity": first.get("quantity") if items else order.quantity,
        "thumbnail_url": image if isinstance(image, str) else "",
        "additional_items": max(0, len(items) - 1),
    }
