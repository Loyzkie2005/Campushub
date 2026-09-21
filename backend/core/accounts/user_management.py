import re
from datetime import datetime

from django.core.paginator import Paginator
from api.models import CampusHubUser, SellerRequest

from .models import Department, Role, User


ADMIN_ROLE_NAMES = frozenset({"super admin", "marketplace admin", "facilities admin"})
ACCOUNT_TYPES = (
    ("student", "Student"),
    ("faculty", "Faculty"),
    ("guest", "Guest/External"),
    ("admin", "Admin"),
)
SELLER_STATUS_LABELS = {
    SellerRequest.STATUS_PENDING: "Pending",
    SellerRequest.STATUS_APPROVED: "Approved",
    SellerRequest.STATUS_REJECTED: "Suspended",
}
USER_STATUS_LABELS = {
    "active": "Active",
    "inactive": "Deactivated",
    "suspended": "Suspended",
}

SORT_FIELDS = {
    "name",
    "username",
    "account_type",
    "role",
    "department",
    "seller_access",
    "status",
    "last_login",
    "date_joined",
}


def is_admin_role(role_name):
    normalized = (role_name or "").strip().lower()
    if normalized in ADMIN_ROLE_NAMES:
        return True
    if not normalized or normalized == "user":
        return False
    role = Role.objects.filter(role_name__iexact=role_name, is_active=True).first()
    return bool(role and role.granted_permissions.exists())


def strict_password_errors(password):
    errors = []
    if len(password or "") < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password or ""):
        errors.append("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", password or ""):
        errors.append("Password must include a lowercase letter.")
    if not re.search(r"\d", password or ""):
        errors.append("Password must include a number.")
    if not re.search(r"[^A-Za-z0-9\s]", password or ""):
        errors.append("Password must include a special character.")
    if re.search(r"\s", password or ""):
        errors.append("Password must not contain spaces.")
    return errors


def account_ref(source, account_id):
    return f"{source}:{account_id}"


def resolve_account(reference):
    try:
        source, raw_id = (reference or "").split(":", 1)
        account_id = int(raw_id)
    except (TypeError, ValueError):
        return None, None

    if source == "admin":
        return source, User.objects.select_related("department").filter(pk=account_id).first()
    if source == "mobile":
        return source, CampusHubUser.objects.select_related("department").filter(pk=account_id).first()
    return None, None


def seller_request_for(source, account):
    if source == "admin":
        request = SellerRequest.objects.filter(user_id=account.pk).order_by("-created_at").first()
        if request:
            return request
    identities = [value for value in (getattr(account, "student_id", ""), account.username) if value]
    if not identities:
        return None
    return SellerRequest.objects.filter(student_id__in=identities).order_by("-created_at").first()


def _seller_requests_by_identity():
    latest = {}
    for seller_request in SellerRequest.objects.order_by("-created_at"):
        keys = {f"student:{seller_request.student_id.lower()}"}
        if seller_request.user_id:
            keys.add(f"admin:{seller_request.user_id}")
        for key in keys:
            latest.setdefault(key, seller_request)
    return latest


def _seller_access(source, account, latest_requests):
    request = latest_requests.get(f"admin:{account.pk}")
    if request is None:
        identities = [getattr(account, "student_id", ""), account.username]
        for identity in identities:
            if identity:
                request = latest_requests.get(f"student:{identity.lower()}")
                if request:
                    break
    if request is None:
        return "not_applied", "Not Applied"
    return request.status, SELLER_STATUS_LABELS.get(request.status, request.status.title())


def _row_from_admin(user, latest_requests, current_user):
    full_name = user.get_full_name().strip() or user.username
    status_value = "suspended" if user.is_suspended else ("active" if user.is_active else "inactive")
    return {
        "ref": account_ref("admin", user.pk),
        "source": "admin",
        "id": user.pk,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
        "initials": f"{user.first_name[:1]}{user.last_name[:1]}".upper() or user.username[:2].upper(),
        "username": user.username,
        "email": user.email,
        "contact_number": user.contact_number,
        "account_type": "admin",
        "account_type_label": "Admin",
        "role": user.role or "User",
        "department_id": user.department_id or "",
        "department": user.department.name if user.department else "-",
        "seller_access": "not_applicable",
        "seller_access_label": "Not applicable",
        "status": status_value,
        "status_label": USER_STATUS_LABELS.get(status_value, status_value.title()),
        "is_active": user.is_active,
        "is_suspended": user.is_suspended,
        "is_super_admin": user.is_superuser or (user.role or "").lower() == "super admin",
        "is_self": user.pk == current_user.pk,
        "date_joined": user.date_joined,
        "last_login": user.last_login,
        "activity_summary": "",
    }


def _row_from_mobile(user, latest_requests):
    seller_value, seller_label = _seller_access("mobile", user, latest_requests)
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    account_type = (user.user_type or "guest").lower()
    type_labels = dict(ACCOUNT_TYPES)
    status_value = "suspended" if user.is_suspended else ("active" if user.is_active else "inactive")
    return {
        "ref": account_ref("mobile", user.pk),
        "source": "mobile",
        "id": user.pk,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
        "initials": f"{user.first_name[:1]}{user.last_name[:1]}".upper() or user.username[:2].upper(),
        "username": user.username,
        "email": user.email,
        "contact_number": user.contact_number,
        "account_type": account_type,
        "account_type_label": type_labels.get(account_type, account_type.title()),
        "role": user.role or "User",
        "department_id": user.department_id or "",
        "department": user.department.name if user.department else "-",
        "seller_access": seller_value,
        "seller_access_label": seller_label,
        "status": status_value,
        "status_label": USER_STATUS_LABELS.get(status_value, status_value.title()),
        "is_active": user.is_active,
        "is_suspended": user.is_suspended,
        "is_super_admin": False,
        "is_self": False,
        "date_joined": user.created_at,
        "last_login": user.last_login,
        "activity_summary": "",
    }


def _matches(row, query, account_type, role, status, department):
    haystack = " ".join(
        str(row.get(key) or "")
        for key in ("full_name", "username", "email", "contact_number", "role", "department")
    ).lower()
    return (
        (not query or query in haystack)
        and (not account_type or row["account_type"] == account_type)
        and (not role or row["role"].lower() == role.lower())
        and (not status or row["status"] == status)
        and (not department or str(row["department_id"]) == department)
    )


def _sort_rows(rows, sort_name, direction):
    if sort_name not in SORT_FIELDS:
        sort_name = "date_joined"
    key_map = {
        "name": "full_name",
        "account_type": "account_type_label",
        "seller_access": "seller_access_label",
        "last_login": "last_login",
    }
    row_key = key_map.get(sort_name, sort_name)

    def sort_key(row):
        value = row.get(row_key)
        if isinstance(value, datetime):
            value = value.timestamp()
        return (value is None, str(value or "").lower())

    return sorted(rows, key=sort_key, reverse=direction == "desc")


def build_account_rows(current_user):
    """Return normalized rows for both Django admin and mobile accounts."""
    latest_requests = _seller_requests_by_identity()
    admin_users = User.objects.select_related("department").all()
    mobile_users = CampusHubUser.objects.select_related("department").all()
    rows = [_row_from_admin(user, latest_requests, current_user) for user in admin_users]
    rows.extend(_row_from_mobile(user, latest_requests) for user in mobile_users)
    return rows


def get_user_management_context(request):
    rows = build_account_rows(request.user)
    all_rows = rows[:]
    query = (request.GET.get("q") or "").strip().lower()
    account_type = (request.GET.get("type") or "").strip().lower()
    role = (request.GET.get("role") or "").strip()
    status = (request.GET.get("status") or "").strip().lower()
    department = (request.GET.get("department") or "").strip()
    rows = [row for row in rows if _matches(row, query, account_type, role, status, department)]
    sort_name = (request.GET.get("sort") or "date_joined").strip().lower()
    direction = "asc" if request.GET.get("dir") == "asc" else "desc"
    rows = _sort_rows(rows, sort_name, direction)

    paginator = Paginator(rows, 10)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    active_count = sum(1 for row in all_rows if row["status"] == "active")
    pending_sellers = sum(1 for row in all_rows if row["seller_access"] == SellerRequest.STATUS_PENDING)
    admin_count = sum(1 for row in all_rows if row["account_type"] == "admin" or is_admin_role(row["role"]))
    active_super_admins = sum(
        1
        for row in all_rows
        if row["source"] == "admin" and row["is_super_admin"] and row["status"] == "active"
    )
    for row in rows:
        row["can_deactivate"] = not row["is_self"] and not (
            row["is_super_admin"] and active_super_admins <= 1
        )

    query_params = request.GET.copy()
    query_params.pop("page", None)
    sort_params = request.GET.copy()
    sort_params.pop("page", None)

    return {
        "users": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "roles": Role.objects.order_by("role_name"),
        "assignable_roles": Role.objects.filter(is_active=True).order_by("role_name"),
        "departments": Department.objects.order_by("name"),
        "account_types": ACCOUNT_TYPES,
        "total_users": len(all_rows),
        "active_users": active_count,
        "pending_sellers": pending_sellers,
        "admin_accounts": admin_count,
        "filters": {
            "q": request.GET.get("q", ""),
            "type": account_type,
            "role": role,
            "status": status,
            "department": department,
            "sort": sort_name,
            "dir": direction,
        },
        "query_without_page": query_params.urlencode(),
    }
