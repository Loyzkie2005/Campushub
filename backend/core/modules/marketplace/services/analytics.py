"""Marketplace analytics and decision-support calculations.

All sales metrics use completed and paid Cash-on-Pickup order records. The
functions in this module return presentation-ready dictionaries while keeping
query and calculation logic out of the Django template.
"""

from __future__ import annotations

from calendar import monthrange
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, time, timedelta
from decimal import Decimal
from math import ceil

from django.db.models import (
    Case,
    CharField,
    Count,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat, Lower, TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.models import User
from api.models import MarketplaceOrder, Product, SellerRequest
from modules.marketplace.services.inventory import (
    get_product_total_stock,
    low_stock_threshold,
)


FORECAST_MIN_DAYS = 14
FORECAST_MIN_NONZERO_DAYS = 3
FORECAST_MIN_UNITS = 7
SLOW_MOVING_MIN_DAYS = 30
SLOW_MOVING_MIN_ORDERS = 5
MARKET_BASKET_MIN_ORDERS = 3
MARKET_BASKET_MIN_MULTI_ITEM_ORDERS = 2


@dataclass(frozen=True)
class AnalyticsPeriod:
    key: str
    label: str
    start: date
    end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def parse_analytics_period(params, *, today: date | None = None) -> AnalyticsPeriod:
    """Parse the global analytics date filter with a bounded custom range."""
    today = today or timezone.localdate()
    key = (params.get("period") or "30").strip().lower()

    if key == "7":
        return AnalyticsPeriod("7", "Last 7 Days", today - timedelta(days=6), today)
    if key == "month":
        return AnalyticsPeriod("month", "This Month", today.replace(day=1), today)
    if key in {"semester", "aug-dec"}:
        return AnalyticsPeriod(
            "semester",
            "Aug - Dec (Semester 1)",
            date(today.year, 8, 1),
            date(today.year, 12, 31),
        )
    if key == "custom":
        start = parse_date((params.get("date_from") or "").strip())
        end = parse_date((params.get("date_to") or "").strip())
        if start and end and start <= end:
            end = min(end, today)
            start = min(start, end)
            if (end - start).days > 365:
                start = end - timedelta(days=365)
            return AnalyticsPeriod(
                "custom",
                f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}",
                start,
                end,
            )

    return AnalyticsPeriod("30", "Last 30 Days", today - timedelta(days=29), today)


def valid_sales_queryset():
    """Return completed and paid orders with one canonical analytics timestamp."""
    return MarketplaceOrder.objects.filter(
        status=MarketplaceOrder.STATUS_COMPLETED,
        payment_status=MarketplaceOrder.PAYMENT_PAID,
    ).annotate(
        analytics_at=Coalesce("completed_at", "paid_at", "created_at")
    )


def _period_sales(period: AnalyticsPeriod):
    return valid_sales_queryset().filter(
        analytics_at__date__range=(period.start, period.end)
    )


def _money(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _money_text(value) -> str:
    return f"{_money(value):,.2f}"


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _sales_time_series(orders, period: AnalyticsPeriod, grouping: str) -> dict:
    rows = list(
        orders.annotate(day=TruncDate("analytics_at"))
        .values("day")
        .annotate(sales=Sum("total_price"), orders=Count("id"))
        .order_by("day")
    )
    daily_sales = {row["day"]: _money(row["sales"]) for row in rows}
    daily_orders = {row["day"]: int(row["orders"] or 0) for row in rows}

    grouping = grouping if grouping in {"daily", "weekly", "monthly"} else "daily"
    buckets = []
    if grouping == "weekly":
        cursor = period.start - timedelta(days=period.start.weekday())
        while cursor <= period.end:
            bucket_end = cursor + timedelta(days=6)
            if cursor.month == bucket_end.month:
                label = f"{cursor.strftime('%b %d')}-{bucket_end.strftime('%d')}"
            else:
                label = f"{cursor.strftime('%b %d')}-{bucket_end.strftime('%b %d')}"
            buckets.append((cursor, bucket_end, label, f"Week of {cursor.strftime('%b %d, %Y')}"))
            cursor += timedelta(days=7)
    elif grouping == "monthly":
        cursor = period.start.replace(day=1)
        while cursor <= period.end:
            bucket_end = cursor.replace(day=monthrange(cursor.year, cursor.month)[1])
            label = cursor.strftime("%b %Y")
            tooltip = cursor.strftime("%B %Y")
            buckets.append((cursor, bucket_end, label, tooltip))
            cursor = _next_month(cursor)
    else:
        cursor = period.start
        while cursor <= period.end:
            buckets.append(
                (cursor, cursor, cursor.strftime("%b %d"), cursor.strftime("%b %d, %Y"))
            )
            cursor += timedelta(days=1)

    labels = []
    tooltip_labels = []
    sales_values = []
    order_values = []
    for bucket_start, bucket_end, label, tooltip in buckets:
        active_start = max(bucket_start, period.start)
        active_end = min(bucket_end, period.end)
        cursor = active_start
        sales = Decimal("0")
        order_count = 0
        while cursor <= active_end:
            sales += daily_sales.get(cursor, Decimal("0"))
            order_count += daily_orders.get(cursor, 0)
            cursor += timedelta(days=1)
        labels.append(label)
        tooltip_labels.append(tooltip)
        sales_values.append(float(sales))
        order_values.append(order_count)

    return {
        "grouping": grouping,
        "labels": labels,
        "tooltip_labels": tooltip_labels,
        "sales": sales_values,
        "orders": order_values,
    }


def _buyer_key_expression():
    return Case(
        When(
            buyer_user_id__isnull=False,
            then=Concat(Value("user:"), Cast("buyer_user_id", CharField())),
        ),
        When(
            ~Q(buyer_email=""),
            then=Concat(Value("email:"), Lower("buyer_email")),
        ),
        default=Value(""),
        output_field=CharField(),
    )


def _buyer_activity(period_orders, period: AnalyticsPeriod, time_series: dict) -> dict:
    buyer_rows = list(
        period_orders.annotate(buyer_key=_buyer_key_expression())
        .exclude(buyer_key="")
        .values("buyer_key")
        .annotate(order_count=Count("id"))
    )
    active_keys = {row["buyer_key"] for row in buyer_rows}
    prior_keys = set()
    if active_keys:
        prior_keys = set(
            valid_sales_queryset()
            .filter(analytics_at__date__lt=period.start)
            .annotate(buyer_key=_buyer_key_expression())
            .filter(buyer_key__in=active_keys)
            .values_list("buyer_key", flat=True)
            .distinct()
        )

    total = len(active_keys)
    repeat = sum(1 for row in buyer_rows if row["order_count"] > 1)
    return {
        "total": total,
        "new": len(active_keys - prior_keys),
        "repeat": repeat,
        "average_orders": f"{(sum(row['order_count'] for row in buyer_rows) / total):.2f}" if total else "0.00",
        "purchase_chart": {
            "labels": time_series["labels"],
            "values": time_series["orders"],
            "tooltip_labels": time_series["tooltip_labels"],
        },
    }


def _category_sales(period_orders) -> list[dict]:
    rows = list(
        period_orders.values("category")
        .annotate(sales=Sum("total_price"), units=Sum("quantity"))
        .order_by("-sales", "category")
    )
    total = sum((_money(row["sales"]) for row in rows), Decimal("0"))
    return [
        {
            "category": (row["category"] or "Uncategorized").strip() or "Uncategorized",
            "sales": _money_text(row["sales"]),
            "sales_value": float(_money(row["sales"])),
            "units": int(row["units"] or 0),
            "percent": round((float(_money(row["sales"]) / total) * 100), 1) if total else 0,
        }
        for row in rows
    ]


def _top_products(period_orders) -> list[dict]:
    rows = (
        period_orders.values("product_id", "product_name", "seller_name")
        .annotate(units=Sum("quantity"), sales=Sum("total_price"))
        .order_by("-units", "-sales", "product_name")[:8]
    )
    return [
        {
            "product_id": row["product_id"],
            "product": row["product_name"],
            "seller": row["seller_name"] or "Not Assigned",
            "units": int(row["units"] or 0),
            "sales": _money_text(row["sales"]),
        }
        for row in rows
    ]


def _product_inventory(products, period_orders, period: AnalyticsPeriod) -> dict:
    product_list = list(products)
    threshold = low_stock_threshold()
    sales_rows = period_orders.filter(product_id__isnull=False).values("product_id").annotate(
        units=Sum("quantity")
    )
    units_by_product = {row["product_id"]: int(row["units"] or 0) for row in sales_rows}

    from django.db.models import Max

    all_last_sales = {
        row["product_id"]: row["last_sale"]
        for row in valid_sales_queryset()
        .filter(product_id__in=[product.id for product in product_list])
        .values("product_id")
        .annotate(last_sale=Max("analytics_at"))
    }

    counts = {"low_stock": 0, "out_of_stock": 0, "total": len(product_list), "healthy": 0}
    rows = []
    product_stock = {}
    for product in product_list:
        stock = max(int(get_product_total_stock(product)), 0)
        product_stock[product.id] = stock
        units = units_by_product.get(product.id, 0)
        average = (units / period.days) if units else 0
        days_left = (stock / average) if average > 0 else None
        if stock == 0:
            counts["out_of_stock"] += 1
            state = "Out of Stock"
            action = "Restock before reopening sales"
        elif stock <= threshold:
            counts["low_stock"] += 1
            state = "Low Stock"
            action = "Review stock level"
        else:
            counts["healthy"] += 1
            state = "Healthy"
            action = "Monitor"
        rows.append(
            {
                "product_id": product.id,
                "seller_id": product.seller_id,
                "product": product.name,
                "stock": stock,
                "state": state,
                "average_daily_sales": f"{average:.2f}" if average else "No recent sales",
                "days_left": f"{days_left:.1f} days" if days_left is not None else "Not available",
                "action": action,
                "units": units,
                "last_sale": all_last_sales.get(product.id),
            }
        )

    rows.sort(
        key=lambda row: (
            0 if row["state"] == "Out of Stock" else 1 if row["state"] == "Low Stock" else 2,
            row["days_left"] == "Not available",
            row["stock"],
            row["product"].lower(),
        )
    )
    return {"summary": counts, "rows": rows[:10], "stock": product_stock, "all_rows": rows}


def _slow_moving_products(inventory: dict, period_orders, period: AnalyticsPeriod) -> dict:
    eligible_count = period_orders.count()
    sufficient = period.days >= SLOW_MOVING_MIN_DAYS and eligible_count >= SLOW_MOVING_MIN_ORDERS
    if not sufficient:
        return {
            "sufficient": False,
            "rule": f"Requires at least {SLOW_MOVING_MIN_DAYS} days and {SLOW_MOVING_MIN_ORDERS} completed paid orders.",
            "rows": [],
        }

    rows = []
    for item in inventory["all_rows"]:
        if item["stock"] <= 0 or item["units"] > 1:
            continue
        last_sale = item["last_sale"]
        rows.append(
            {
                **item,
                "last_sold": timezone.localtime(last_sale).strftime("%b %d, %Y") if last_sale else "Never",
            }
        )
    return {
        "sufficient": True,
        "rule": "Products with current stock and no more than 1 completed unit sold in the selected period.",
        "rows": rows[:8],
    }


def _approved_seller_ids() -> list[int]:
    return list(
        SellerRequest.objects.filter(
            status=SellerRequest.STATUS_APPROVED,
            user__isnull=False,
            user__is_active=True,
            user__is_suspended=False,
        )
        .values_list("user_id", flat=True)
        .distinct()
    )


def _seller_performance(period_orders, period: AnalyticsPeriod, inventory: dict) -> dict:
    seller_ids = _approved_seller_ids()
    if not seller_ids:
        return {"active_count": 0, "rows": []}

    active_product_rows = Product.objects.filter(
        seller_id__in=seller_ids,
        is_archived=False,
    ).values("seller_id").annotate(products=Count("id"))
    product_counts = {row["seller_id"]: int(row["products"] or 0) for row in active_product_rows}

    period_product_activity = set(
        Product.objects.filter(
            seller_id__in=seller_ids,
            is_archived=False,
        )
        .filter(
            Q(submitted_at__date__range=(period.start, period.end))
            | Q(updated_at__date__range=(period.start, period.end))
        )
        .values_list("seller_id", flat=True)
    )
    sales_rows = list(
        period_orders.filter(product__seller_id__in=seller_ids)
        .values("product__seller_id")
        .annotate(orders=Count("id"), units=Sum("quantity"), sales=Sum("total_price"))
    )
    sales_by_seller = {row["product__seller_id"]: row for row in sales_rows}
    active_ids = period_product_activity | set(sales_by_seller)

    low_stock = Counter()
    for item in inventory["all_rows"]:
        if item["state"] in {"Low Stock", "Out of Stock"}:
            if item["seller_id"] in seller_ids:
                low_stock[item["seller_id"]] += 1

    users = User.objects.filter(id__in=active_ids).select_related("department").order_by("first_name", "last_name", "username")
    rows = []
    for seller in users:
        sales = sales_by_seller.get(seller.id, {})
        rows.append(
            {
                "seller": (seller.get_full_name() or seller.username).strip(),
                "department": seller.department.name if seller.department_id else "Not Assigned",
                "products": product_counts.get(seller.id, 0),
                "orders": int(sales.get("orders") or 0),
                "units": int(sales.get("units") or 0),
                "sales": _money_text(sales.get("sales")),
                "sales_value": float(_money(sales.get("sales"))),
                "low_stock": low_stock.get(seller.id, 0),
            }
        )
    rows.sort(key=lambda row: (-row["sales_value"], -row["units"], row["seller"].lower()))
    return {"active_count": len(active_ids), "rows": rows[:10]}


def _forecast(product: Product | None, period: AnalyticsPeriod, horizon: int, stock: int) -> dict:
    horizon = 30 if horizon == 30 else 7
    if product is None:
        return {"sufficient": False, "message": "No approved products are available for forecasting.", "horizon": horizon}

    product_orders = _period_sales(period).filter(product_id=product.id)
    daily_rows = (
        product_orders.annotate(day=TruncDate("analytics_at"))
        .values("day")
        .annotate(units=Sum("quantity"))
    )
    demand_map = {row["day"]: int(row["units"] or 0) for row in daily_rows}
    dates = [period.start + timedelta(days=offset) for offset in range(period.days)]
    values = [demand_map.get(day, 0) for day in dates]
    nonzero_days = sum(1 for value in values if value > 0)
    total_units = sum(values)
    sufficient = (
        period.days >= FORECAST_MIN_DAYS
        and nonzero_days >= FORECAST_MIN_NONZERO_DAYS
        and total_units >= FORECAST_MIN_UNITS
    )
    base = {
        "product_id": product.id,
        "product": product.name,
        "horizon": horizon,
        "current_stock": stock,
        "sufficient": sufficient,
        "minimum": {
            "days": FORECAST_MIN_DAYS,
            "nonzero_days": FORECAST_MIN_NONZERO_DAYS,
            "units": FORECAST_MIN_UNITS,
        },
    }
    if not sufficient:
        return {
            **base,
            "message": "Insufficient historical data for reliable forecasting.",
            "history_days": period.days,
            "sales_days": nonzero_days,
            "units": total_units,
        }

    window = values[-min(7, len(values)) :]
    predicted = []
    rolling = [float(value) for value in window]
    for _ in range(horizon):
        next_value = sum(rolling[-7:]) / len(rolling[-7:])
        predicted.append(round(next_value, 2))
        rolling.append(next_value)

    forecast_total = ceil(sum(predicted))
    future_dates = [period.end + timedelta(days=offset + 1) for offset in range(horizon)]
    labels = [day.strftime("%b %d") for day in dates + future_dates]
    historical = values + [None] * horizon
    forecast_values = [None] * (len(values) - 1) + [values[-1]] + predicted
    return {
        **base,
        "method": "7-day moving average",
        "forecast_total": forecast_total,
        "suggested_preparation": max(forecast_total - stock, 0),
        "chart": {
            "labels": labels,
            "historical": historical,
            "forecast": forecast_values,
        },
    }


def calculate_market_basket(transactions) -> dict:
    """Calculate directional association rules from real transaction item sets."""
    normalized = []
    names = {}
    for transaction in transactions:
        item_set = set()
        for product_id, product_name in transaction:
            if product_id is None:
                continue
            item_set.add(product_id)
            names[product_id] = product_name
        if item_set:
            normalized.append(item_set)

    multi_count = sum(1 for item_set in normalized if len(item_set) > 1)
    if len(normalized) < MARKET_BASKET_MIN_ORDERS or multi_count < MARKET_BASKET_MIN_MULTI_ITEM_ORDERS:
        return {
            "sufficient": False,
            "message": "Insufficient transaction data for product association analysis.",
            "eligible_orders": len(normalized),
            "multi_item_orders": multi_count,
            "rows": [],
        }

    product_counts = Counter()
    pair_counts = Counter()
    for item_set in normalized:
        product_counts.update(item_set)
        ordered = sorted(item_set)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                pair_counts[(left, right)] += 1

    total = len(normalized)
    rows = []
    for (left, right), pair_count in pair_counts.items():
        support = pair_count / total
        for source, target in ((left, right), (right, left)):
            confidence = pair_count / product_counts[source]
            target_support = product_counts[target] / total
            lift = confidence / target_support if target_support else 0
            rows.append(
                {
                    "product_a": names.get(source, str(source)),
                    "product_b": names.get(target, str(target)),
                    "support": round(support * 100, 1),
                    "confidence": round(confidence * 100, 1),
                    "lift": round(lift, 2),
                }
            )
    rows.sort(key=lambda row: (-row["lift"], -row["confidence"], -row["support"]))
    return {"sufficient": bool(rows), "eligible_orders": total, "multi_item_orders": multi_count, "rows": rows[:8]}


def _market_basket(period_orders) -> dict:
    grouped = defaultdict(list)
    for row in period_orders.exclude(order_code="").values("order_code", "product_id", "product_name"):
        grouped[row["order_code"]].append((row["product_id"], row["product_name"]))
    return calculate_market_basket(grouped.values())


def _peak_sales_period(period_orders) -> dict:
    rows = list(period_orders.values("analytics_at", "total_price"))
    if not rows:
        return {
            "sufficient": False,
            "message": "Peak sales data is unavailable for this period.",
            "day": "Not available",
            "time": "Not available",
            "chart": {"labels": [], "values": []},
        }

    weekday_sales = Counter()
    hourly_sales = Counter()
    for row in rows:
        timestamp = row["analytics_at"]
        if timezone.is_aware(timestamp):
            timestamp = timezone.localtime(timestamp)
        amount = _money(row["total_price"])
        weekday_sales[timestamp.strftime("%A")] += amount
        hourly_sales[(timestamp.hour // 3) * 3] += amount

    day = max(weekday_sales, key=lambda key: (weekday_sales[key], key))
    peak_hour = max(hourly_sales, key=lambda key: (hourly_sales[key], -key))
    hour_labels = []
    hour_values = []
    for start_hour in range(0, 24, 3):
        end_hour = (start_hour + 3) % 24
        start_text = time(start_hour).strftime("%I %p").lstrip("0")
        end_text = time(end_hour).strftime("%I %p").lstrip("0")
        hour_labels.append(f"{start_text}-{end_text}")
        hour_values.append(float(hourly_sales.get(start_hour, Decimal("0"))))

    start_text = time(peak_hour).strftime("%I:%M %p").lstrip("0")
    end_text = time((peak_hour + 3) % 24).strftime("%I:%M %p").lstrip("0")
    return {
        "sufficient": True,
        "day": day,
        "day_sales": _money_text(weekday_sales[day]),
        "time": f"{start_text} - {end_text}",
        "time_sales": _money_text(hourly_sales[peak_hour]),
        "chart": {"labels": hour_labels, "values": hour_values},
    }


def build_marketplace_analytics(params, *, today: date | None = None) -> dict:
    """Build the complete Marketplace Analytics page context."""
    period = parse_analytics_period(params, today=today)
    grouping = (params.get("grouping") or "daily").strip().lower()
    horizon = 30 if str(params.get("forecast_horizon") or "7") == "30" else 7
    period_orders = _period_sales(period)
    products = Product.objects.filter(
        approval_status=Product.STATUS_APPROVED,
        is_archived=False,
    ).select_related("seller", "seller__department")

    if grouping == "monthly" and period.key != "custom":
        sales_chart_start = date(today.year, 8, 1)
        sales_chart_end = date(today.year, 12, 31)
        sales_chart_period = AnalyticsPeriod(
            "monthly",
            "Aug - Dec (5 Months)",
            sales_chart_start,
            sales_chart_end,
        )
        sales_chart_orders = valid_sales_queryset().filter(
            analytics_at__date__range=(sales_chart_start, sales_chart_end)
        )
        time_series = _sales_time_series(sales_chart_orders, sales_chart_period, grouping)
    else:
        time_series = _sales_time_series(period_orders, period, grouping)
    revenue = period_orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0")
    completed_orders = period_orders.count()
    buyer_activity = _buyer_activity(period_orders, period, time_series)
    categories = _category_sales(period_orders)
    inventory = _product_inventory(products, period_orders, period)
    sellers = _seller_performance(period_orders, period, inventory)

    selected_product_id = params.get("forecast_product")
    try:
        selected_product_id = int(selected_product_id) if selected_product_id else None
    except (TypeError, ValueError):
        selected_product_id = None
    selected_product = products.filter(id=selected_product_id).first() if selected_product_id else None
    if selected_product is None:
        top = period_orders.exclude(product_id__isnull=True).values("product_id").annotate(
            units=Sum("quantity")
        ).order_by("-units").first()
        selected_product = products.filter(id=top["product_id"]).first() if top else products.order_by("name").first()
    stock = inventory["stock"].get(selected_product.id, 0) if selected_product else 0

    return {
        "period": period,
        "grouping": time_series["grouping"],
        "kpis": {
            "sales": _money_text(revenue),
            "completed_orders": completed_orders,
            "active_buyers": buyer_activity["total"],
            "active_sellers": sellers["active_count"],
            "average_order_value": _money_text(revenue / completed_orders) if completed_orders else "0.00",
        },
        "sales_chart": time_series,
        "category_sales": categories,
        "category_chart": {
            "labels": [row["category"] for row in categories],
            "values": [row["sales_value"] for row in categories],
        },
        "top_products": _top_products(period_orders),
        "slow_moving": _slow_moving_products(inventory, period_orders, period),
        "buyer_activity": buyer_activity,
        "seller_performance": sellers,
        "inventory": inventory,
        "product_options": list(products.order_by("name").values("id", "name")),
        "forecast": _forecast(selected_product, period, horizon, stock),
        "market_basket": _market_basket(period_orders),
        "peak_sales": _peak_sales_period(period_orders),
    }
