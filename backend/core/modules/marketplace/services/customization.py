"""Simple food customization helpers for campus marketplace products."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

FOOD_CATEGORIES = frozenset(
    {
        "Rice Meals",
        "Snacks",
        "Desserts",
        "Beverages",
        "Combo Meals",
        "Breakfast",
    }
)


def is_food_category(category: str) -> bool:
    return (category or "").strip() in FOOD_CATEGORIES


def _to_decimal(value) -> Decimal:
    try:
        amount = Decimal(str(value if value not in (None, "") else "0"))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")
    if amount < 0:
        amount = Decimal("0")
    return amount.quantize(Decimal("0.01"))


def normalize_customization_options(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []

    groups: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        if not name:
            continue

        selection = (item.get("selection") or "single").strip().lower()
        if selection not in {"single", "multiple"}:
            selection = "single"

        options: list[dict] = []
        for opt in item.get("options") or []:
            if not isinstance(opt, dict):
                continue
            opt_name = (opt.get("name") or "").strip()
            if not opt_name:
                continue
            stock_raw = opt.get("stock", 0)
            try:
                stock = max(int(stock_raw), 0)
            except (TypeError, ValueError):
                stock = 0
            expiry_raw = (opt.get("expiry_date") or "").strip()
            option_payload = {
                "name": opt_name,
                "extra_price": str(_to_decimal(opt.get("extra_price", 0))),
                "stock": stock,
            }
            if expiry_raw:
                option_payload["expiry_date"] = expiry_raw
            options.append(option_payload)

        if not options:
            continue

        groups.append(
            {
                "name": name,
                "selection": selection,
                "required": bool(item.get("required")),
                "options": options,
            }
        )

    return groups


def parse_order_selections(raw) -> list[dict]:
    if isinstance(raw, dict):
        raw = raw.get("selections") or []
    if not isinstance(raw, list):
        return []

    selections: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        group = (item.get("group") or "").strip()
        option = (item.get("option") or "").strip()
        if not group or not option:
            continue
        selections.append(
            {
                "group": group,
                "option": option,
                "extra_price": str(_to_decimal(item.get("extra_price", 0))),
            }
        )
    return selections


def build_option_lookup(groups: list[dict]) -> dict[tuple[str, str], Decimal]:
    lookup: dict[tuple[str, str], Decimal] = {}
    for group in groups:
        group_name = group.get("name") or ""
        for opt in group.get("options") or []:
            lookup[(group_name, opt.get("name") or "")] = _to_decimal(
                opt.get("extra_price", 0)
            )
    return lookup


def validate_order_selections(
    groups: list[dict],
    selections: list[dict],
) -> tuple[list[dict], Decimal, str | None]:
    if not groups:
        return [], Decimal("0.00"), None

    lookup = build_option_lookup(groups)
    group_map = {group["name"]: group for group in groups}
    selected_by_group: dict[str, list[dict]] = {}

    validated: list[dict] = []
    for item in selections:
        group_name = item["group"]
        option_name = item["option"]
        key = (group_name, option_name)
        if key not in lookup:
            return [], Decimal("0.00"), f"Invalid customization option: {option_name}"

        group = group_map.get(group_name)
        if not group:
            return [], Decimal("0.00"), f"Invalid customization group: {group_name}"

        bucket = selected_by_group.setdefault(group_name, [])
        if group["selection"] == "single" and bucket:
            return [], Decimal("0.00"), f"Choose one option only for {group_name}"

        if any(row["option"] == option_name for row in bucket):
            continue

        extra_price = lookup[key]
        row = {
            "group": group_name,
            "option": option_name,
            "extra_price": str(extra_price),
        }
        bucket.append(row)
        validated.append(row)

    for group in groups:
        if not group.get("required"):
            continue
        if not selected_by_group.get(group["name"]):
            return [], Decimal("0.00"), f"{group['name']} is required"

    extra_total = sum(_to_decimal(row["extra_price"]) for row in validated)
    return validated, extra_total.quantize(Decimal("0.01")), None


def format_customization_summary(selections: list[dict]) -> str:
    parts: list[str] = []
    for row in selections:
        extra = _to_decimal(row.get("extra_price", 0))
        label = row.get("option") or ""
        if extra > 0:
            parts.append(f"{label} (+₱{extra})")
        else:
            parts.append(label)
    return ", ".join(parts)


def build_order_customization_payload(selections: list[dict]) -> dict:
    extra_total = sum(_to_decimal(row.get("extra_price", 0)) for row in selections)
    extra_total = extra_total.quantize(Decimal("0.01"))
    return {
        "selections": selections,
        "extra_total": str(extra_total),
        "summary": format_customization_summary(selections),
    }
