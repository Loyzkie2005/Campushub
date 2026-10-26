import re
from datetime import datetime

def _parse_academic_levels(year_section_str):
    if not year_section_str:
        return "", ""
    val = str(year_section_str).strip()
    m = re.match(r'^(?:(?:(\d)(?:st|nd|rd|th)?\s*Year)|Year\s*(\d))\s*(?:(?:-|–|,)\s*(?:Section\s*)?([A-Za-z0-9_-]+))?$', val, re.IGNORECASE)
    if m:
        yr = m.group(1) or m.group(2)
        sec = (m.group(3) or "").strip()
        yr_map = {"1": "1st Year", "2": "2nd Year", "3": "3rd Year", "4": "4th Year", "5": "5th Year"}
        return yr_map.get(yr, f"Year {yr}"), (f"Section {sec}" if sec and not sec.lower().startswith("section") else sec)
    m2 = re.match(r'^(\d)\s*[-]?\s*([A-Za-z0-9])$', val)
    if m2:
        yr, sec = m2.group(1), m2.group(2).upper()
        yr_map = {"1": "1st Year", "2": "2nd Year", "3": "3rd Year", "4": "4th Year", "5": "5th Year"}
        return yr_map.get(yr, f"Year {yr}"), f"Section {sec}"
    return val, ""

from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from api.models import CampusHubUser, SellerRequest

from .models import AccountActivity, Department, Role, User, ProgramMajor
from .academic import academic_labels
from .support_scope import support_accounts, support_activity, is_marketplace_admin


ADMIN_ROLE_NAMES = frozenset({"super admin", "marketplace admin", "facilities admin"})
ACCOUNT_TYPES = (
    ("student", "Student"),
    ("faculty", "Faculty"),
    ("guest", "Guest/External"),
    ("admin", "Admin"),
)
SELLER_STATUS_LABELS = {
    SellerRequest.STATUS_PENDING: "Pending Review",
    SellerRequest.STATUS_NEEDS_REVISION: "Needs Revision",
    SellerRequest.STATUS_APPROVED: "Approved",
    SellerRequest.STATUS_REJECTED: "Rejected",
    "suspended": "Suspended",
}
USER_STATUS_LABELS = {
    "active": "Active",
    "inactive": "Inactive / Disabled",
}

SORT_FIELDS = {
    "name",
    "username",
    "account_type",
    "role",
    "department",
    "program_major",
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


def log_management_event(request, *, source, account, action):
    """Existing audit row stores the target; the description identifies the actor."""
    from .activity_logging import log_account_activity
    return log_account_activity(request, source=source, account=account, activity_type=action,
        activity=f"{action.replace('_', ' ').title()} by {request.user.username}"[:180],
        module="User Management", result=AccountActivity.RESULT_SUCCESS,
        metadata={"actor_admin_id": request.user.pk})


def account_ref(source, account_id):
    return f"{source}:{account_id}"


def resolve_account(reference):
    try:
        source, raw_id = (reference or "").split(":", 1)
        account_id = int(raw_id)
    except (TypeError, ValueError):
        return None, None

    if source == "admin":
        return source, User.objects.select_related("department", "major").filter(pk=account_id).first()
    if source == "mobile":
        return source, CampusHubUser.objects.select_related("department", "major").filter(pk=account_id).first()
    return None, None


def seller_request_for(source, account):
    if source == "mobile":
        linked = SellerRequest.objects.filter(mobile_user=account).order_by("-created_at", "-pk").first()
        if linked:
            return linked
    if source == "admin":
        request = SellerRequest.objects.filter(user_id=account.pk).order_by("-created_at", "-pk").first()
        if request:
            return request
    identities = [value for value in (getattr(account, "student_id", ""), account.username) if value]
    if not identities:
        return None
    return SellerRequest.objects.filter(student_id__in=identities, user__isnull=True, mobile_user__isnull=True).order_by("-created_at", "-pk").first()


def _seller_requests_by_identity(actor):
    from .academic import scope_seller_requests
    latest = {}
    requests = SellerRequest.objects.all()
    if is_marketplace_admin(actor):
        requests = scope_seller_requests(requests, actor)
    for seller_request in requests.order_by("-created_at", "-pk"):
        keys = set()
        if seller_request.user_id:
            keys.add(f"admin:{seller_request.user_id}")
        elif seller_request.mobile_user_id:
            keys.add(f"mobile:{seller_request.mobile_user_id}")
        else:
            keys.add(f"student:{seller_request.student_id.lower()}")
        for key in keys:
            latest.setdefault(key, seller_request)
    return latest


def _latest_seller_request(source, account, latest_requests):
    request = latest_requests.get(f"admin:{account.pk}" if source == "admin" else f"mobile:{account.pk}")
    if request is None:
        identities = [getattr(account, "student_id", ""), account.username]
        for identity in identities:
            if identity:
                request = latest_requests.get(f"student:{identity.lower()}")
                if request:
                    break
    return request


def _seller_access(source, account, latest_requests):
    request = _latest_seller_request(source, account, latest_requests)
    if request is None:
        return "not_applied", "Not Applied"
    value = "suspended" if request.is_suspended and request.status == "approved" else request.status
    return value, SELLER_STATUS_LABELS.get(value, value.title())


def _row_from_admin(user, latest_requests, current_user):
    full_name = user.get_full_name().strip() or user.username
    status_value = "active" if user.is_active and not user.is_suspended else "inactive"
    return {
        "ref": account_ref("admin", user.pk),
        "source": "admin",
        "id": user.pk,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
        "initials": f"{user.first_name[:1]}{user.last_name[:1]}".upper() or user.username[:2].upper(),
        "username": user.username, "student_id": "", "institutional_id": "", "year_section": "", "year_level": "", "section": "",
        "email": user.email,
        "contact_number": user.contact_number,
        "account_type": "admin",
        "account_type_label": "Admin",
        "role": user.role or "User",
        "department_id": user.department_id or "",
        "major_id": user.major_id or "",
        "major": user.major.name if user.major_id else "",
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
    status_value = "active" if user.is_active and not user.is_suspended else "inactive"
    return {
        "ref": account_ref("mobile", user.pk),
        "source": "mobile",
        "id": user.pk,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": full_name,
        "initials": f"{user.first_name[:1]}{user.last_name[:1]}".upper() or user.username[:2].upper(),
        "username": user.username, "student_id": "", "institutional_id": "", "year_section": "", "year_level": "", "section": "",
        "email": user.email,
        "contact_number": user.contact_number,
        "account_type": account_type,
        "account_type_label": type_labels.get(account_type, account_type.title()),
        "role": user.role or "User",
        "department_id": user.department_id or "",
        "major_id": user.major_id or "",
        "major": user.major.name if user.major_id else "",
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


def _matches(row, query, account_type, role, status, department, major="", seller=""):
    haystack = " ".join(
        str(row.get(key) or "")
        for key in ("full_name", "username", "email", "contact_number", "role", "program_major", "student_id")
    ).lower()
    return (
        (not query or query in haystack)
        and (not account_type or row["account_type"] == account_type)
        and (not role or row["role"].lower() == role.lower())
        and (not status or row["status"] == status)
        and (not department or str(row["department_id"]) == department)
        and (not major or str(row["major_id"]) == major)
        and (not seller or row["seller_access"] == seller)
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
        return (value is None, value if isinstance(value, (int, float)) else str(value or "").lower())

    return sorted(rows, key=sort_key, reverse=direction == "desc")


def account_detail_fields(row, seller_application=None):
    """Present only applicable extra fields from the existing normalized row."""
    if row["scope"]:
        label = "System Scope" if row["scope"] == "All Modules" else "Facility Scope"
        return [{"label": label, "value": row["scope"]}]
    fields = []
    academic = (row["account_type"] == "student"
                or row["role"].casefold() == "marketplace admin"
                or (row["account_type"] != "guest" and bool(row["department_id"])))
    if academic:
        fields.append({"label": "Program", "value": row["program"]})
        if row["program"] == "BTLED":
            fields.append({"label": "Major", "value": row["major"] or "Unassigned"})
    # Existing applications are evidence of guest seller participation; do not
    # invent a guest eligibility policy or display admin seller access.
    seller = row["account_type"] != "admin" and (
        row["account_type"] in {"student", "faculty"} or seller_application is not None)
    if seller:
        fields.append({"label": "Seller Access", "value": row["seller_access_label"]})
        if seller_application is not None:
            fields.append({"label": "Application Status", "value": row["seller_application"]})
            if row["seller_approved_at"]:
                fields.append({"label": "Approval Date", "value": row["seller_approved_at"], "format": "date"})
    return fields


def mask_recovery_phone(value):
    """Display stored contact digits without claiming SMS verification/support."""
    digits = "".join(character for character in (value or "") if character.isascii() and character.isdigit())
    if not digits:
        return "Not recorded"
    if len(digits) <= 5:
        return "*" * len(digits)
    return digits[:2] + "*****" + digits[-3:]


def build_account_rows(current_user):
    """Return normalized rows for both Django admin and mobile accounts."""
    latest_requests = _seller_requests_by_identity(current_user)
    admin_users = User.objects.select_related("department", "major").all()
    mobile_users = CampusHubUser.objects.select_related("department", "major").all()
    if not current_user.is_superuser and current_user.role.casefold() == "marketplace admin":
        admin_users = support_accounts(admin_users, current_user)
        mobile_users = support_accounts(mobile_users, current_user, mobile=True)
    from .role_permissions import ADMIN_AUTHORITY_CODENAMES
    from .support_scope import is_administrator_account, can_view_recovery_info
    authority_ids = set(User.objects.filter(
        Q(user_permissions__codename__in=ADMIN_AUTHORITY_CODENAMES)
        | Q(groups__permissions__codename__in=ADMIN_AUTHORITY_CODENAMES)
    ).values_list("pk", flat=True))
    rows = [_row_from_admin(user, latest_requests, current_user) for user in admin_users]
    rows.extend(_row_from_mobile(user, latest_requests) for user in mobile_users)
    accounts = {account_ref("admin", user.pk): user for user in admin_users}
    accounts.update({account_ref("mobile", user.pk): user for user in mobile_users})
    for row in rows:
        account = accounts[row["ref"]]
        row["is_super_admin"] = bool(getattr(account, "is_superuser", False) or (account.role or "").strip().casefold() == "super admin")
        global_admin = row["source"] == "admin" and (row["is_super_admin"] or row["role"].casefold() == "facilities admin")
        labels = academic_labels(account.department, account.major)
        meaningful = (not global_admin and row["account_type"] != "guest"
                      and (row["account_type"] == "student"
                           or row["role"].casefold() == "marketplace admin"
                           or bool(account.department_id)))
        row.update(program=labels["program"] if meaningful else "—",
                   program_major=labels["program_major"] if meaningful else "—",
                   major=labels["major"] if meaningful else "",
                   scope="All Modules" if row.get("is_super_admin") else "All Facilities" if global_admin else "")
        if not meaningful:
            row["department_id"], row["major_id"] = "", ""
        request = _latest_seller_request(row["source"], account, latest_requests) if row["account_type"] != "admin" else None
        row["seller_application"] = request.get_status_display() if request else "—"
        row["seller_approved_at"] = request.reviewed_at if request and request.status == "approved" else None
        row["seller_applied_at"] = request.created_at if request else None
        row["seller_product_type"] = getattr(request, "product_type", "") if request else ""
        if row["source"] == "mobile":
            yr_level, sec = _parse_academic_levels(getattr(account, "year_section", ""))
            row["student_id"] = getattr(account, "student_id", "") or ""
            row["institutional_id"] = getattr(account, "institutional_id", "") or ""
            row["year_section"] = getattr(account, "year_section", "") or ""
            row["year_level"] = yr_level
            row["section"] = sec
        row["detail_fields"] = account_detail_fields(row, request)
        from .recovery_codes import mask_email
        from .support_scope import can_manage_account, can_manage_seller
        row["email_verified"] = account.email_verified
        row["email_verification_label"] = "Verified" if account.email_verified else "Email not verified"
        row["masked_email"] = mask_email(account.email)
        # Marketplace rows were already scoped in two batched account queries.
        row["is_administrator"] = is_administrator_account(row["source"], account,
            has_admin_authority=account.pk in authority_ids if row["source"] == "admin" else False)
        row["recovery_method"] = "Verified Email" if row["is_administrator"] else ""
        row["can_assist_recovery"] = can_view_recovery_info(current_user, row["source"], account,
            has_admin_authority=account.pk in authority_ids if row["source"] == "admin" else False)
        row["masked_phone"] = mask_recovery_phone(account.contact_number)
        # Neither account model has a persisted SMS verification field/provider.
        row["sms_verified"] = False
        row["sms_recovery_available"] = False
        row["recovery_referral"] = is_marketplace_admin(current_user)
        # Retired mutation capabilities must never be advertised to old clients.
        row["can_reset"] = row["can_recover"] = row["can_verify_email"] = False
        row["can_manage"] = can_manage_account(current_user, account)
        row["can_manage_role"] = row["can_manage"] and row["is_administrator"] and not row["is_super_admin"] and (current_user.is_superuser or current_user.role.casefold() == "super admin")
        seller_allowed = row["source"] == "mobile" and current_user.has_perm("accounts.can_manage_sellers") if is_marketplace_admin(current_user) else can_manage_seller(current_user, row["source"], account)
        row["can_manage_seller"] = not row["is_administrator"] and seller_allowed and row["seller_access"] in {"approved", "suspended"}
    return rows


def get_user_management_context(request):
    rows = build_account_rows(request.user)
    all_rows = rows[:]
    query = (request.GET.get("q") or "").strip().lower()
    account_type = (request.GET.get("type") or "").strip().lower()
    role = (request.GET.get("role") or "").strip()
    status = (request.GET.get("status") or "").strip().lower()
    department = (request.GET.get("department") or "").strip()
    major = (request.GET.get("major") or "").strip()
    seller = (request.GET.get("seller") or "").strip()
    rows = [row for row in rows if _matches(row, query, account_type, role, status, department, major, seller)]
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
        current_can_manage = row["can_manage"]
        row["can_deactivate"] = row["can_deactivate"] and current_can_manage and not row["is_super_admin"]

    # Fetch one extra event to detect older history without a per-account count.
    from django.db.models import F, Window
    from django.db.models.functions import RowNumber
    displayed = list(page_obj.object_list)
    events = support_activity(AccountActivity.objects.filter(account_ref__in=[row["ref"] for row in displayed]), request.user).exclude(activity="").annotate(
        rank=Window(expression=RowNumber(), partition_by=[F("account_ref")], order_by=[F("created_at").desc(), F("pk").desc()])
    ).filter(rank__lte=6).order_by("account_ref", "-created_at", "-pk")
    activity = {}
    for event in events:
        activity.setdefault(event.account_ref, []).append({"activity": event.activity, "date": event.created_at})
    can_monitor = (request.user.is_superuser or request.user.role.casefold() == "super admin" or is_marketplace_admin(request.user)) and request.user.has_perm("accounts.can_view_user_monitoring")
    from .admin_tab_auth import append_tab_token_to_url
    from urllib.parse import urlencode
    for row in displayed:
        recorded = activity.get(row["ref"], [])
        row["activities"] = recorded[:5]
        row["has_more_activity"] = len(recorded) > 5
        url = reverse("admin_user_monitoring_page") + "?" + urlencode({"account_ref": row["ref"]})
        row["monitoring_url"] = append_tab_token_to_url(url, getattr(request, "admin_tab_token", "")) if can_monitor else ""
        row["activity_url"] = row["monitoring_url"] if row["has_more_activity"] else ""

    query_params = request.GET.copy()
    query_params.pop("page", None)
    sort_params = request.GET.copy()
    sort_params.pop("page", None)

    return {
        "users": displayed,
        "page_obj": page_obj,
        "paginator": paginator,
        "roles": Role.objects.filter(role_name__iexact="User") if is_marketplace_admin(request.user) else Role.objects.order_by("role_name"),
        "assignable_roles": Role.objects.filter(is_active=True).order_by("role_name"),
        "departments": Department.objects.filter(pk=request.user.department_id, is_program=True) if is_marketplace_admin(request.user) else Department.objects.filter(is_program=True).order_by("code"),
        "majors": ProgramMajor.objects.filter(pk=request.user.major_id).select_related("program") if is_marketplace_admin(request.user) else ProgramMajor.objects.select_related("program").order_by("code"),
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
            "major": major,
            "seller": seller,
            "sort": sort_name,
            "dir": direction,
        },
        "query_without_page": query_params.urlencode(),
        "seller_options": (("not_applied", "Not Applied"), ("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("suspended", "Suspended")),
        "tab_token": getattr(request, "admin_tab_token", ""),
    }