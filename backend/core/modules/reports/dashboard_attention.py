"""Current operational shortcuts, independent of dashboard reporting dates."""
from urllib.parse import urlencode

from django.db.models import Count, F, Q, Value
from django.db.models.functions import Coalesce, Trim
from django.urls import reverse

from api.models import MarketplaceOrder, Product
from modules.marketplace.services.inventory import (
    INVENTORY_STATUS_LOW_STOCK, INVENTORY_STATUS_OUT_OF_STOCK,
    PERISHABLE_CATEGORIES, get_product_inventory_status, low_stock_threshold, iter_product_low_stock,
)


def super_admin_created_products():
    # Legacy listings may have no creator audit; use their owner only in that case.
    return (Q(created_by__is_superuser=True) | Q(created_by__role__iexact="Super Admin")
            | (Q(created_by__isnull=True)
               & (Q(seller__is_superuser=True) | Q(seller__role__iexact="Super Admin"))))


def inventory_attention_counts(today, products=None):
    products = Product.objects.all() if products is None else products
    active = products.filter(is_archived=False, product_type=Product.TYPE_SINGLE)
    simple = active.filter(customization_options=[]).annotate(inventory_category=Trim("category"),
        effective_threshold=Coalesce("low_stock_threshold", Value(low_stock_threshold())))
    expired = Q(inventory_category__in=PERISHABLE_CATEGORIES, expiry_date__lt=today)
    counts = simple.aggregate(
        low_stock_products=Count("pk", filter=Q(stock__gt=0, stock__lte=F("effective_threshold")) & ~expired),
        out_of_stock_products=Count("pk", filter=Q(stock=0) & ~expired),
    )
    # Option inventory is JSON, with per-option stock/expiry rules. Stream only the
    # fields needed by the existing classifier; no related-object queries or cache.
    variants = active.exclude(customization_options=[]).only(
        "stock", "category", "expiry_date", "customization_enabled", "customization_options", "low_stock_threshold", "product_type",
    ).order_by().iterator(chunk_size=500)
    keys = {INVENTORY_STATUS_LOW_STOCK: "low_stock_products",
            INVENTORY_STATUS_OUT_OF_STOCK: "out_of_stock_products"}
    for product in variants:
        if any(iter_product_low_stock(product, today=today)):
            counts["low_stock_products"] += 1
            continue
        key = keys.get(get_product_inventory_status(product, today=today))
        if key:
            counts[key] += 1
    return counts


def build_attention_required(*, today, pending_products, pending_sellers, pending_bookings,
                             booking_conflicts, maintenance_facilities, unavailable_facilities,
                             products=None, pending_orders=0, pending_services=0):
    counts = inventory_attention_counts(today, products=products)
    counts.update(pending_products=pending_products, pending_sellers=pending_sellers,
                  pending_bookings=pending_bookings, booking_conflicts=booking_conflicts,
                  maintenance_facilities=maintenance_facilities,
                  unavailable_facilities=unavailable_facilities, pending_orders=pending_orders,
                  pending_services=pending_services)
    definitions = (
        ("low_stock_products", "Low Stock Product", "Low Stock Products", "View Inventory", "admin_products_page", {"view": "inventory", "inventory_status": "low_stock"}, "attention"),
        ("out_of_stock_products", "Out of Stock Product", "Out of Stock Products", "View Inventory", "admin_products_page", {"view": "inventory", "inventory_status": "out_of_stock"}, "serious"),
        ("pending_products", "Pending Product Review", "Pending Product Reviews", "Review Products", "admin_products_page", {"status": "pending"}, "attention"),
        ("pending_sellers", "Pending Seller Application", "Pending Seller Applications", "Review Sellers", "admin_sellers_page", {"status": "pending"}, "attention"),
        ("pending_orders", "Pending Order", "Pending Orders", "Review Orders", "admin_orders_page", {"status": MarketplaceOrder.STATUS_PENDING}, "attention"),
        ("pending_bookings", "Pending Booking Request", "Pending Booking Requests", "Review Bookings", "admin_bookings_page", {"status": "pending"}, "attention"),
        ("pending_services", "Pending Service Request", "Pending Service Requests", "Review Requests", "admin_service_requests_page", {"status": "pending"}, "attention"),
        ("booking_conflicts", "Booking Conflict", "Booking Conflicts", "Resolve", "admin_calendar_page", {}, "serious"),
        ("maintenance_facilities", "Facility Under Maintenance", "Facilities Under Maintenance", "View Facilities", "admin_facility_page", {"status": "maintenance"}, "neutral"),
        ("unavailable_facilities", "Temporarily Unavailable Facility", "Temporarily Unavailable Facilities", "View Facilities", "admin_facility_page", {"status": "unavailable"}, "neutral"),
    )
    items = []
    for key, singular, plural, action, route, params, severity in definitions:
        count = counts[key]
        if count > 0:
            url = reverse(route) + ("?" + urlencode(params) if params else "")
            items.append({"key": key, "count": count, "label": singular if count == 1 else plural,
                          "action": action, "url": url, "severity": severity})
    return {**counts, "items": items}
