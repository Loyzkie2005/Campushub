"""Current Inventory monitoring for the existing Super Admin dashboard endpoint."""
import logging
from urllib.parse import urlencode

from django.db import DatabaseError
from django.urls import reverse

from api.models import Product
from modules.marketplace.services.inventory import low_stock_inventory_rows

logger = logging.getLogger(__name__)


def build_low_stock_card(today=None, *, include_out_of_stock=False):
    url = reverse("admin_products_page")
    result = {"state": "ready", "products": [],
              "view_all_url": f"{url}?{urlencode({'view': 'inventory', 'inventory_status': 'low_stock'})}"}
    if include_out_of_stock:
        result['view_all_url'] = f"{url}?view=inventory"
    try:
        rows = low_stock_inventory_rows(Product.objects.all(), limit=5, today=today,
                                        include_out_of_stock=include_out_of_stock)
        for row in rows:
            product = row["product"]
            result["products"].append({
                "product_id": product.pk, "product_name": product.name,
                "variant_key": row["variant_key"], "variant_name": row["variant_name"],
                "group_name": row["group_name"], "available": row["available"],
                "threshold": row["threshold"], "status": row['status'],
                "image_url": row["image_url"] or (reverse("product_image", args=[product.pk]) if product.get_image_list() else ""),
                "url": f"{url}?{urlencode({'view': 'inventory', 'product_id': product.pk})}",
            })
    except DatabaseError:
        logger.exception("Unable to load dashboard low-stock inventory")
        result.update(state="error", products=[])
    return result
