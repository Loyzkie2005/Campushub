"""Shared, read-only audit presentation for Django and DRF.

Identifiers are used only for batched lookups. Public details never serialize
metadata, raw user agents, session identifiers, or entity database keys.
"""
import re
import uuid

from django.utils import timezone

from .models import AccountActivity, Role, User


AUTH_EVENTS = {"login_success", "login_failed", "logout"}
ACTION_LABELS = {
    "admin_scope_changed": "Program/Major Updated",
    "login_success": "Logged In", "login_failed": "Login Failed", "logout": "Logged Out",
    "role_permissions_updated": "Permissions Changed",
    "permissions_updated": "Permissions Changed",
}
MODULE_LABELS = {
    "authentication": "Authentication", "user management": "User Management",
    "roles & permissions": "Roles & Permissions", "roles": "Roles & Permissions",
    **{name: "Marketplace" for name in ("marketplace", "products", "inventory", "orders", "sellers")},
    **{name: "Facilities" for name in ("facilities", "bookings", "calendar")},
    "reports": "Reports", "system": "System",
    "services": "Services", "service requests": "Services",
    "marketplace orders": "Marketplace", "data export": "Reports",
    "backup & restore": "System", "system backup": "System",
}


def display_role(value):
    """Normalize the existing ordinary-role alias for display, never RBAC."""
    value = (value or "").strip()
    return "User" if value.casefold() in {"", "user", "standard user"} else value


def action_label(event):
    """Use the recorded event code, not its verbose '... by actor' description."""
    code = event.activity_type.lower()
    return ACTION_LABELS.get(code, event.activity_type.replace("_", " ").strip().title() or "Recorded Event")


def parse_connection(user_agent, ip_address=None):
    """Recognize stored UA signatures; never infer Windows 11 from NT 10.0."""
    agent = user_agent or ""
    device = "Unknown"
    if "Android" in agent:
        device = "Android Device"
    elif "iPhone" in agent:
        device = "iPhone"
    elif "iPad" in agent:
        device = "iPad"
    elif "Windows NT" in agent:
        device = "Windows Desktop"
    elif "Macintosh" in agent:
        device = "Mac Desktop"
    elif "Linux" in agent:
        device = "Linux Device"
    browser = "Unknown"
    # Edge/Opera include Chrome; order the more specific signatures first.
    for pattern, label in (
        (r"(?:Edg|EdgA|EdgiOS)/([0-9]+)", "Microsoft Edge"),
        (r"OPR/([0-9]+)", "Opera"),
        (r"(?:Chrome|CriOS)/([0-9]+)", "Google Chrome"),
        (r"(?:Firefox|FxiOS)/([0-9]+)", "Mozilla Firefox"),
        (r"Version/([0-9]+).*Safari/", "Safari"),
    ):
        match = re.search(pattern, agent)
        if match:
            browser = label
            break
    return {"ip_address": ip_address or None, "device": device, "browser": browser}


def connection_summary(user_agent):
    connection = parse_connection(user_agent)
    known = [connection[key] for key in ("device", "browser") if connection[key] != "Unknown"]
    return " / ".join(known) or "Unknown"


def format_activities(events, *, scoped=False, include_targets=True):
    """Format one bounded page with batch queries, not a query per audit row.

    Scope must already have been enforced by the caller. Scoped support readers
    retain the existing prohibition on connection/IP information.
    """
    from api.models import Booking, Facility, MarketplaceOrder, Product, SellerRequest
    events = list(events)
    metadata = {event.pk: event.metadata if isinstance(event.metadata, dict) else {} for event in events}

    def ids(key, numeric=True):
        values = {str(data[key]) for data in metadata.values() if data.get(key) is not None}
        if numeric:
            return {value for value in values if value.isdigit() and len(value) < 19}
        return {value for value in values if 0 < len(value) <= 30}

    actor_ids = ids("actor_admin_id")
    target_ids = ids("target_admin_id") if include_targets else set()
    admins = {str(user.pk): user for user in User.objects.filter(pk__in=actor_ids | target_ids)}
    products = facilities = bookings = orders = sellers = roles = {}
    if include_targets:
        products = dict((str(pk), name) for pk, name in Product.objects.filter(pk__in=ids("product_id")).values_list("pk", "name"))
        facilities = dict((str(pk), name) for pk, name in Facility.objects.filter(pk__in=ids("facility_id", False)).values_list("pk", "facility_name"))
        # Booking.id is the existing public booking reference, not an integer FK.
        bookings = dict((str(pk), str(pk)) for pk in Booking.objects.filter(pk__in=ids("booking_id", False)).values_list("pk", flat=True))
        orders = dict((str(pk), code) for pk, code in MarketplaceOrder.objects.filter(pk__in=ids("order_id")).values_list("pk", "order_code"))
        sellers = dict((str(pk), name) for pk, name in SellerRequest.objects.filter(pk__in=ids("seller_request_id")).values_list("pk", "full_name"))
        role_ids = []
        for data in metadata.values():
            try:
                role_ids.append(uuid.UUID(str(data.get("role_id"))))
            except (ValueError, TypeError):
                pass
        roles = dict((str(pk), name) for pk, name in Role.objects.filter(pk__in=role_ids).values_list("pk", "role_name"))

    def record(kind, name):
        return {"type": kind, "label": f"Affected {kind.title()}", "name": name} if name else None

    def recorded_text(data, key):
        # Historical JSON can be malformed. Never stringify an object/list
        # containing nested credentials into an apparently harmless name.
        value = data.get(key)
        if not isinstance(value, str) or value.strip().casefold() in {"", "null", "none", "undefined", "n/a"}:
            return None
        return value.strip()[:250]

    details = []
    for event in events:
        data = metadata[event.pk]
        code = event.activity_type.lower()
        identity = event.full_name or event.username or None
        actor = admins.get(str(data.get("actor_admin_id")))
        if actor:
            performed_by = {"name": actor.get_full_name().strip() or actor.username,
                            "username": actor.username, "role": display_role(actor.role) if actor.role else None}
        elif data.get("system_generated") is True:
            performed_by = {"name": "CampusHub System", "username": None, "role": "System"}
        elif recorded_text(data, "actor_username"):
            name = recorded_text(data, "actor_username")
            performed_by = {"name": name, "username": name, "role": None}
        elif code in AUTH_EVENTS or event.module == "Authentication":
            performed_by = {"name": identity or "Unknown", "username": event.username or None,
                            "role": display_role(event.role) if event.role else None}
        else:
            performed_by = {"name": "Unknown", "username": None, "role": None}
        affected = None
        if include_targets and code not in AUTH_EVENTS:
            if data.get("target_admin_id") and code.startswith("admin_"):
                target = admins.get(str(data["target_admin_id"]))
                name = target.get_full_name().strip() or target.username if target else (
                    identity if event.account_source == "admin" and str(event.account_id) == str(data["target_admin_id"]) else None)
                affected = record("user", name)
            elif data.get("role_id"):
                affected = record("role", roles.get(str(data["role_id"])) or recorded_text(data, "role_name"))
            elif data.get("product_id"):
                affected = record("product", products.get(str(data["product_id"])) or recorded_text(data, "product_name"))
            elif data.get("booking_id"):
                affected = record("booking", bookings.get(str(data["booking_id"])))
            elif data.get("facility_id"):
                affected = record("facility", facilities.get(str(data["facility_id"])) or recorded_text(data, "facility_name"))
            elif data.get("order_id"):
                affected = record("order", orders.get(str(data["order_id"])))
            elif data.get("seller_request_id"):
                affected = record("seller", sellers.get(str(data["seller_request_id"])))
            elif event.account_id:
                affected = record("seller" if code.startswith("seller_") else "user", identity)
        details.append({
            "id": event.pk,
            "date_time": timezone.localtime(event.created_at).isoformat(),
            "performed_by": performed_by,
            "affected_record": affected,
            "action": action_label(event),
            "module": MODULE_LABELS.get(event.module.strip().lower(), "System"),
            "result": dict(AccountActivity.RESULT_CHOICES).get(event.result),
            "connection": None if scoped else parse_connection(event.user_agent, event.ip_address),
        })
    return details
