"""Single source of truth for report previews and exported files."""

from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from api.models import Booking, FacilityPayment, MarketplaceOrder, Product
from modules.marketplace.services.inventory import low_stock_threshold


REPORT_GROUPS = OrderedDict(
    (
        (
            "Marketplace",
            OrderedDict(
                (
                    ("sales", "Sales Report"),
                    ("orders", "Orders Report"),
                    ("products", "Product & Inventory Report"),
                    ("low_stock", "Low Stock Report"),
                )
            ),
        ),
        (
            "Facilities",
            OrderedDict(
                (
                    ("bookings", "Facility Booking Report"),
                    ("facility_utilization", "Facility Utilization Report"),
                    ("facility_payments", "Facility Payments & OR Report"),
                )
            ),
        ),
        (
            "System",
            OrderedDict(
                (
                    ("user_accounts", "User Accounts Report"),
                    ("user_activity", "User Login Activity Report"),
                )
            ),
        ),
    )
)
REPORT_TITLES = OrderedDict(
    (value, label)
    for reports in REPORT_GROUPS.values()
    for value, label in reports.items()
)


def _date(value):
    if not value:
        return None
    return value.date() if hasattr(value, "date") else value


def _date_label(value):
    value = _date(value)
    return value.strftime("%b %d, %Y") if value else "-"


def _datetime_label(value):
    if not value:
        return "Never"
    return timezone.localtime(value).strftime("%b %d, %Y %I:%M %p")


def _time_label(value):
    return value.strftime("%I:%M %p") if value else "-"


def _time_range(start_time, end_time):
    if not start_time and not end_time:
        return "-"
    return f"{_time_label(start_time)} - {_time_label(end_time)}"


def _money(value):
    return f"PHP {Decimal(value or 0):,.2f}"


def _filter_dates(queryset, field, date_from, date_to):
    if date_from:
        queryset = queryset.filter(**{f"{field}__date__gte": date_from})
    if date_to:
        queryset = queryset.filter(**{f"{field}__date__lte": date_to})
    return queryset


def _filter_date_field(queryset, field, date_from, date_to):
    if date_from:
        queryset = queryset.filter(**{f"{field}__gte": date_from})
    if date_to:
        queryset = queryset.filter(**{f"{field}__lte": date_to})
    return queryset


def _chart_from_rows(rows, date_key, value_key):
    totals = OrderedDict()
    for row in rows:
        day = row.get(date_key)
        if not day:
            continue
        label = _date(day).strftime("%b %d")
        totals[label] = totals.get(label, Decimal("0")) + Decimal(str(row[value_key]))
    return {"labels": list(totals), "values": [float(value) for value in totals.values()]}


def _range_label(date_from, date_to):
    if date_from and date_to:
        return f"{_date_label(date_from)} to {_date_label(date_to)}"
    if date_from:
        return f"From {_date_label(date_from)}"
    if date_to:
        return f"Through {_date_label(date_to)}"
    return "All Time"


def _display_user(user):
    if not user:
        return "Walk-in"
    full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
    return full_name or getattr(user, "username", None) or "Walk-in"


def _booking_hours(booking):
    if not booking.start_time or not booking.end_time:
        return Decimal("0")
    day = booking.booking_date or timezone.localdate()
    start = datetime.combine(day, booking.start_time)
    end = datetime.combine(day, booking.end_time)
    if end < start:
        end += timedelta(days=1)
    return Decimal(str((end - start).total_seconds() / 3600)).quantize(Decimal("0.01"))


def _latest_payment(booking):
    payments = list(booking.payments.all())
    return payments[0] if payments else None


def _order_report(report_type, date_from, date_to):
    orders = _filter_dates(
        MarketplaceOrder.objects.select_related("product").order_by("created_at"),
        "created_at",
        date_from,
        date_to,
    )
    if report_type == "sales":
        orders = orders.filter(
            Q(payment_status=MarketplaceOrder.PAYMENT_PAID)
            | Q(status=MarketplaceOrder.STATUS_COMPLETED)
        )
        rows = [
            {
                "Order ID": order.order_code or str(order.pk),
                "Date": _date_label(order.created_at),
                "Product": order.product_name,
                "Quantity": order.quantity,
                "Amount (PHP)": order.total_price,
                "Payment": order.get_payment_status_display(),
                "_day": order.created_at,
            }
            for order in orders
        ]
        total = sum((Decimal(row["Amount (PHP)"]) for row in rows), Decimal("0"))
        summary = [
            ("Paid/Completed Orders", len(rows)),
            ("Products Sold", sum(row["Quantity"] for row in rows)),
            ("Revenue", _money(total)),
            ("Average Order Value", _money(total / len(rows) if rows else 0)),
        ]
        columns = ["Order ID", "Date", "Product", "Quantity", "Amount (PHP)", "Payment"]
    else:
        rows = [
            {
                "Order ID": order.order_code or str(order.pk),
                "Date": _date_label(order.created_at),
                "Customer": order.buyer_name or "Unknown customer",
                "Product": order.product_name,
                "Quantity": order.quantity,
                "Amount (PHP)": order.total_price,
                "Status": order.get_status_display(),
                "Payment": order.get_payment_status_display(),
                "_day": order.created_at,
            }
            for order in orders
        ]
        total = sum((Decimal(row["Amount (PHP)"]) for row in rows), Decimal("0"))
        summary = [
            ("Total Orders", len(rows)),
            ("Pending", sum(row["Status"] == "Pending" for row in rows)),
            ("Completed", sum(row["Status"] == "Completed" for row in rows)),
            ("Order Value", _money(total)),
        ]
        columns = [
            "Order ID", "Date", "Customer", "Product", "Quantity",
            "Amount (PHP)", "Status", "Payment",
        ]
    return rows, summary, _chart_from_rows(rows, "_day", "Amount (PHP)"), columns


def _product_report(report_type, date_from, date_to):
    products = _filter_dates(
        Product.objects.select_related("seller").order_by("submitted_at"),
        "submitted_at",
        date_from,
        date_to,
    )
    product_rows = [
        {
            "Product ID": product.product_code or str(product.pk),
            "Product": product.name,
            "Seller": product.seller.get_full_name() or product.seller.username,
            "Category": product.category or "Uncategorized",
            "Price (PHP)": product.price,
            "Stock": product.get_total_stock(),
            "Inventory Status": product.get_inventory_status_label(),
            "Expiry Date": _date_label(product.expiry_date),
            "Approval": product.get_approval_status_display(),
            "Archived": "Yes" if product.is_archived else "No",
        }
        for product in products
    ]
    if report_type == "low_stock":
        threshold = low_stock_threshold()
        rows = [
            row for row in product_rows
            if row["Stock"] <= threshold and row["Approval"] == "Approved" and row["Archived"] == "No"
        ]
        summary = [
            ("Low Stock Alerts", len(rows)),
            ("Out of Stock", sum(row["Stock"] == 0 for row in rows)),
            ("Low Stock", sum(0 < row["Stock"] <= threshold for row in rows)),
            ("Units Remaining", sum(row["Stock"] for row in rows)),
        ]
        columns = [
            "Product ID", "Product", "Seller", "Category", "Stock",
            "Inventory Status", "Expiry Date",
        ]
    else:
        rows = product_rows
        summary = [
            ("Total Products", len(rows)),
            ("Approved", sum(row["Approval"] == "Approved" for row in rows)),
            ("Pending", sum(row["Approval"] == "Pending" for row in rows)),
            ("Total Stock", sum(row["Stock"] for row in rows)),
        ]
        columns = [
            "Product ID", "Product", "Seller", "Category", "Price (PHP)",
            "Stock", "Inventory Status", "Expiry Date", "Approval", "Archived",
        ]
    chart = {"labels": [row["Product"] for row in rows[:12]], "values": [row["Stock"] for row in rows[:12]]}
    return rows, summary, chart, columns


def _booking_queryset(date_from, date_to):
    return _filter_date_field(
        Booking.objects.select_related("facility", "user").prefetch_related("payments").order_by("booking_date", "start_time"),
        "booking_date",
        date_from,
        date_to,
    )


def _booking_report(date_from, date_to):
    rows = []
    for booking in _booking_queryset(date_from, date_to):
        payment = _latest_payment(booking)
        rows.append(
            {
                "Booking ID": booking.id,
                "Date": _date_label(booking.booking_date),
                "Time": _time_range(booking.start_time, booking.end_time),
                "Requester": _display_user(booking.user),
                "Facility": getattr(booking.facility, "facility_name", None) or "-",
                "Room/Unit": str(booking.room_id or "-"),
                "Amount (PHP)": booking.total_amount,
                "Payment": payment.get_payment_status_display() if payment else "Unpaid",
                "Status": booking.get_status_display(),
                "_day": booking.booking_date,
            }
        )
    total = sum((Decimal(row["Amount (PHP)"]) for row in rows), Decimal("0"))
    summary = [
        ("Total Bookings", len(rows)),
        ("Pending", sum(row["Status"] == "Pending" for row in rows)),
        ("Approved", sum(row["Status"] == "Approved" for row in rows)),
        ("Booking Value", _money(total)),
    ]
    columns = [
        "Booking ID", "Date", "Time", "Requester", "Facility", "Room/Unit",
        "Amount (PHP)", "Payment", "Status",
    ]
    return rows, summary, _chart_from_rows(rows, "_day", "Amount (PHP)"), columns


def _facility_utilization_report(date_from, date_to):
    bookings = list(_booking_queryset(date_from, date_to))
    totals = OrderedDict()
    for booking in bookings:
        facility = booking.facility
        facility_id = getattr(facility, "pk", None) or "unassigned"
        if facility_id not in totals:
            totals[facility_id] = {
                "Facility": getattr(facility, "facility_name", None) or "Unassigned",
                "Type": facility.get_facility_type_display() if facility else "-",
                "Capacity": getattr(facility, "capacity", 0) or 0,
                "Total Bookings": 0,
                "Approved/Completed": 0,
                "Booked Hours": Decimal("0"),
            }
        item = totals[facility_id]
        item["Total Bookings"] += 1
        if booking.status in {Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED}:
            item["Approved/Completed"] += 1
        item["Booked Hours"] += _booking_hours(booking)

    total_bookings = len(bookings)
    rows = []
    for item in sorted(totals.values(), key=lambda row: (-row["Total Bookings"], row["Facility"])):
        item["Booking Share (%)"] = round(item["Total Bookings"] * 100 / total_bookings, 1) if total_bookings else 0
        rows.append(item)
    total_hours = sum((row["Booked Hours"] for row in rows), Decimal("0"))
    summary = [
        ("Facilities Used", len(rows)),
        ("Total Bookings", total_bookings),
        ("Booked Hours", f"{total_hours:,.2f}"),
        ("Most Booked", rows[0]["Facility"] if rows else "-"),
    ]
    chart = {"labels": [row["Facility"] for row in rows[:12]], "values": [row["Total Bookings"] for row in rows[:12]]}
    columns = [
        "Facility", "Type", "Capacity", "Total Bookings", "Approved/Completed",
        "Booked Hours", "Booking Share (%)",
    ]
    return rows, summary, chart, columns


def _facility_payment_report(date_from, date_to):
    payments = _filter_dates(
        FacilityPayment.objects.select_related("booking__facility", "booking__user").order_by("created_at"),
        "created_at",
        date_from,
        date_to,
    )
    rows = []
    for payment in payments:
        booking = payment.booking
        rows.append(
            {
                "Payment ID": payment.id,
                "Booking ID": getattr(booking, "id", None) or "-",
                "Date": _date_label(payment.paid_at or payment.created_at),
                "Requester": _display_user(getattr(booking, "user", None)),
                "Facility": getattr(getattr(booking, "facility", None), "facility_name", None) or "-",
                "Amount Due (PHP)": getattr(booking, "total_amount", 0) or 0,
                "Paid Amount (PHP)": payment.paid_amount,
                "Payment": payment.get_payment_status_display(),
                "OR No.": payment.official_receipt_no or "-",
                "_day": payment.paid_at or payment.created_at,
            }
        )
    collected = sum(
        (Decimal(row["Paid Amount (PHP)"]) for row in rows if row["Payment"] == "Paid"),
        Decimal("0"),
    )
    summary = [
        ("Payment Records", len(rows)),
        ("Paid", sum(row["Payment"] == "Paid" for row in rows)),
        ("Unpaid/Failed", sum(row["Payment"] != "Paid" for row in rows)),
        ("Collected", _money(collected)),
    ]
    columns = [
        "Payment ID", "Booking ID", "Date", "Requester", "Facility",
        "Amount Due (PHP)", "Paid Amount (PHP)", "Payment", "OR No.",
    ]
    return rows, summary, _chart_from_rows(rows, "_day", "Paid Amount (PHP)"), columns


def _user_report(report_type, date_from, date_to):
    if report_type == "user_accounts":
        users = _filter_dates(User.objects.order_by("date_joined"), "date_joined", date_from, date_to)
        rows = [
            {
                "Username": user.username,
                "Full Name": user.get_full_name() or "-",
                "Email": user.email or "-",
                "Role": user.role or "Unassigned",
                "Status": "Active" if user.is_active else "Inactive",
                "Joined": _date_label(user.date_joined),
                "Last Login": _datetime_label(user.last_login),
            }
            for user in users
        ]
        summary = [
            ("Total Users", len(rows)),
            ("Active", sum(row["Status"] == "Active" for row in rows)),
            ("Inactive", sum(row["Status"] == "Inactive" for row in rows)),
            ("Unassigned", sum(row["Role"] == "Unassigned" for row in rows)),
        ]
        role_counts = OrderedDict()
        for row in rows:
            role_counts[row["Role"]] = role_counts.get(row["Role"], 0) + 1
        chart = {"labels": list(role_counts), "values": list(role_counts.values())}
        columns = ["Username", "Full Name", "Email", "Role", "Status", "Joined", "Last Login"]
        return rows, summary, chart, columns

    users = User.objects.filter(last_login__isnull=False).order_by("last_login")
    users = _filter_dates(users, "last_login", date_from, date_to)
    rows = [
        {
            "Username": user.username,
            "Full Name": user.get_full_name() or "-",
            "Role": user.role or "Unassigned",
            "Activity": "Latest login",
            "Last Login": _datetime_label(user.last_login),
            "_day": user.last_login,
            "_count": 1,
        }
        for user in users
    ]
    now = timezone.now()
    all_users = User.objects.all()
    summary = [
        ("Users With Login", len(rows)),
        ("Last 24 Hours", all_users.filter(last_login__gte=now - timedelta(days=1)).count()),
        ("Last 7 Days", all_users.filter(last_login__gte=now - timedelta(days=7)).count()),
        ("Never Logged In", all_users.filter(last_login__isnull=True).count()),
    ]
    columns = ["Username", "Full Name", "Role", "Activity", "Last Login"]
    return rows, summary, _chart_from_rows(rows, "_day", "_count"), columns


def build_report(report_type, date_from=None, date_to=None):
    if report_type not in REPORT_TITLES:
        raise ValueError("Unsupported report type.")

    if report_type in {"sales", "orders"}:
        rows, summary, chart, columns = _order_report(report_type, date_from, date_to)
    elif report_type in {"products", "low_stock"}:
        rows, summary, chart, columns = _product_report(report_type, date_from, date_to)
    elif report_type == "bookings":
        rows, summary, chart, columns = _booking_report(date_from, date_to)
    elif report_type == "facility_utilization":
        rows, summary, chart, columns = _facility_utilization_report(date_from, date_to)
    elif report_type == "facility_payments":
        rows, summary, chart, columns = _facility_payment_report(date_from, date_to)
    else:
        rows, summary, chart, columns = _user_report(report_type, date_from, date_to)

    serial_rows = []
    for row in rows:
        serial_rows.append(
            {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in row.items()
                if not key.startswith("_")
            }
        )
    return {
        "report_type": report_type,
        "title": REPORT_TITLES[report_type],
        "range": _range_label(date_from, date_to),
        "columns": columns,
        "rows": serial_rows,
        "summary": [{"label": label, "value": value} for label, value in summary],
        "chart": chart,
    }
