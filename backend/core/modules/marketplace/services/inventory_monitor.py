"""Inventory monitoring filters, summaries, detail links and recorded history."""
from urllib.parse import urlencode

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .inventory import build_inventory_table, INVENTORY_STATUS_LABELS
from .inventory_records import order_allocations


def inventory_url(params):
    return reverse("admin_products_page") + "?" + urlencode(params)


def inventory_monitor_context(request, products):
    """Intersect metadata filters, then exact expanded-row search/status filters."""
    from accounts.models import Department, User
    from api.models import CampusHubUser
    from accounts.academic import academic_options, filter_product_academic, scope_users
    from accounts.admin_tab_auth import get_tab_token_from_request
    base = products.filter(is_archived=False)
    params = {"view": "inventory"}
    token = get_tab_token_from_request(request)
    if token:
        params["__at"] = token
    for key in ("search", "inventory_status", "program", "major", "department", "seller", "category", "product_id", "page", "inventory_section", "batch"):
        value = request.GET.get(key, "").strip()
        if value:
            params[key] = value
    scoped = base
    if params.get("department") and not params.get("program"):
        params["program"] = params.pop("department")  # Preserve older Inventory links.
    for key in ("seller", "product_id", "program", "major"):
        value = params.get(key)
        if value:
            if key == "seller" and value.startswith("mobile:") and value.split(":", 1)[1].isdecimal():
                scoped = scoped.filter(mobile_seller_id=value.split(":", 1)[1])
            elif not value.isdecimal():
                scoped = scoped.none()
            elif key in ("program", "major"):
                scoped = filter_product_academic(scoped, **{key + "_id": value})
            else:
                scoped = scoped.filter(**{("seller_id" if key == "seller" else "pk"): value})
    if params.get("category"):
        scoped = scoped.filter(category=params["category"])
    can_view_movements = any(request.user.has_perm("accounts." + code) for code in ("can_manage_products", "can_approve_products", "can_view_stock_movements"))
    rows = build_inventory_table(scoped.order_by("name", "pk"))
    if params.get("batch"):
        from api.models import InventoryBatch
        ids = list(InventoryBatch.objects.filter(pk=params["batch"], sku_id__in=[row.get("sku_id") for row in rows]).values_list("sku_id", flat=True)) if params["batch"].isdecimal() else []
        rows = [row for row in rows if row.get("sku_id") in ids]
    search = params.get("search", "").casefold()
    batch_search = None
    movement_search = None
    if search:
        if params.get("inventory_section") == "fifo":
            from .fifo_presentation import search_batches
            batch_search = search_batches(rows, search)
            matching_skus = set(batch_search.values_list("sku_id", flat=True).distinct())
            rows = [row for row in rows if row.get("sku_id") in matching_skus]
        elif params.get("inventory_section") == "movements" and can_view_movements:
            from .fifo_presentation import search_movements
            movement_search = search_movements(rows, search)
            matching_skus = set(movement_search.values_list("sku_id", flat=True).distinct())
            rows = [row for row in rows if row.get("sku_id") in matching_skus]
        else:
            rows = [row for row in rows if any(search in str(row[field]).casefold()
                for field in ("product_name", "name", "sku", "seller_name"))]
    status_options = [(key, INVENTORY_STATUS_LABELS[key]) for key in ("in_stock", "low_stock", "out_of_stock")]
    if any(row["status"] == "unavailable" for row in rows) or params.get("inventory_status") == "unavailable":
        status_options.append(("unavailable", "Unavailable"))
    if params.get("inventory_status") in dict(status_options):
        rows = [row for row in rows if row["status"] == params["inventory_status"]]
    elif params.get("inventory_status"):
        scoped = scoped.none()
        rows = []  # Invalid explicit filters must not silently display all inventory.
    known_reserved = [row["reserved"] for row in rows if not row.get("derived")]
    summary = {"total": len(rows), "low_stock": sum(row["status"] == "low_stock" for row in rows),
               "out_of_stock": sum(row["status"] == "out_of_stock" for row in rows),
               "reserved": None if any(value is None for value in known_reserved) else sum(known_reserved)}
    for row in rows:
        row["inventory_url"] = inventory_url({**params, "inventory_item": row["sku_id"]}) if row["sku_id"] else ""
        row["movements_url"] = row["inventory_url"] + "#inventory-movements" if row["inventory_url"] and can_view_movements else ""
        if token:
            row["details_url"] += "&" + urlencode({"__at": token})
    page_params = {key: value for key, value in params.items() if key != "page"}
    detail = inventory_detail(request.GET.get("inventory_item"), products, include_movements=can_view_movements) if request.GET.get("inventory_item") else None
    if detail and token:
        detail["details_url"] += "&" + urlencode({"__at": token})
    programs, majors = academic_options()
    from .fifo_presentation import workspace
    return {**workspace(request, products, rows, params, batch_search=batch_search, movement_search=movement_search), "inventory_rows": rows, "inventory_summary": summary, "inventory_detail": detail,
            "inventory_return_url": inventory_url(params), "page_query": urlencode(page_params),
            "inventory_tab_token": token, "inventory_reset_url": inventory_url({"view": "inventory", **({"__at": token} if token else {})}),
            "inventory_search": params.get("search", ""), "inventory_status": params.get("inventory_status", ""),
            "inventory_product_id": params.get("product_id", ""), "inventory_department": params.get("program", ""),
            "inventory_program": params.get("program", ""), "inventory_major": params.get("major", ""),
            "inventory_seller": params.get("seller", ""), "inventory_category": params.get("category", ""),
            "inventory_status_options": status_options, "inventory_departments": programs, "programs": programs, "majors": majors,
            "inventory_sellers": scope_users(User.objects.filter(pk__in=base.values("seller_id")), request.user).order_by("first_name", "last_name", "username"),
            "inventory_mobile_sellers": scope_users(CampusHubUser.objects.filter(pk__in=base.values("mobile_seller_id")), request.user).order_by("first_name", "last_name"),
            "inventory_categories": list(base.exclude(category="").order_by("category").values_list("category", flat=True).distinct())}


def inventory_detail(sku_id, products, *, include_movements=True):
    from api.models import InventorySKU
    if not str(sku_id).isdecimal():
        from django.http import Http404
        raise Http404
    sku = get_object_or_404(InventorySKU.objects.select_related("product", "product__seller", "product__department", "product__major", "product__seller__department", "product__seller__major"),
                            pk=sku_id, product__in=products)
    product = sku.product
    rows = build_inventory_table([product])
    row = next((row for row in rows if row["sku_id"] == sku.pk), None)
    if row is None:
        department = product.department or product.owner.department
        row = {"product_name": product.name, "name": sku.variant_name, "group": sku.group_name,
               "sku": sku.code, "sku_id": sku.pk, "seller_name": product.owner.get_full_name().strip() or product.owner.username,
               "department_name": str(department) if department else "Not assigned", "category": product.category,
               "on_hand": None, "reserved": None, "available": None, "threshold": None,
               "status": "unavailable", "status_label": "Variant no longer in current inventory", "updated_at": product.updated_at,
               "details_url": inventory_url({"product_id": product.pk})}
        from accounts.academic import product_academic
        row.update(product_academic(product))
    row["archived"] = product.is_archived
    row["can_view_movements"] = include_movements
    row["movements"] = inventory_movements(sku) if include_movements else []
    return row


def inventory_movements(sku):
    """The same persisted ledger used by the global movements tab."""
    query = sku.movements.select_related("order").prefetch_related(
        "fifo_allocations__batch", "order__fifo_allocations__batch", "received_batches")
    recorded = list(query[:100])
    from .fifo_presentation import movement_allocations, movement_reference
    events = []
    for row in recorded:
        events.append({"date": row.created_at, "kind": row.get_kind_display(), "quantity": row.quantity_change,
            "balance": row.get_balance_display(), "before": row.available_before, "after": row.available_after,
            "reference": movement_reference(row), "actor": row.actor or "—", "notes": row.notes,
            "received_at": row.received_at, "allocations": movement_allocations(row)})
    return events
