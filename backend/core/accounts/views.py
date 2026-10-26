from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db.models.functions import ExtractHour, TruncDay, TruncMonth, TruncWeek
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_POST
import json

from api.models import (
    CampusHubUser,
    MarketplaceOrder,
    MarketplaceOrderStatusHistory,
    Product,
    SellerRequest,
)
from api.inventory import (
    INVENTORY_STATUS_LOW_STOCK,
    adjust_product_stock,
    count_customization_options,
    customization_has_stock_tracking,
    get_inventory_status,
    get_product_quantity_status,
    get_product_inventory_status,
    iter_product_low_stock,
    low_stock_threshold,
    get_variant_stock_summary,
    build_inventory_table,
)
from accounts.admin_tab_auth import get_tab_token_from_request, revoke_admin_tab_token
from accounts.activity_logging import log_account_activity
from accounts.monitoring import monitoring_load_guard
from accounts.models import AccountActivity, AdminTabToken, Role, User
from accounts.role_permissions import (
    admin_read_permissions,
    get_admin_home_url,
    sync_user_admin_permissions,
    user_can_book_facilities,
    user_can_manage_facilities,
    user_can_manage_products,
    user_has_admin_access,
    user_has_facility_module_access,
)
from accounts.user_management import (
    ACCOUNT_TYPES,
    build_account_rows,
    get_user_management_context,
    is_admin_role,
    resolve_account,
    seller_request_for,
    strict_password_errors,
)
from modules.marketplace.services.product_access import admin_product_queryset
from modules.marketplace.services.order_access import admin_order_queryset

CREATABLE_ADMIN_ROLES = frozenset({"super admin", "marketplace admin", "facilities admin"})


def can_access_dashboard(user):
    return user_has_admin_access(user)


def dashboard_required(view_func):
    return login_required(login_url="admin_login_page")(
        user_passes_test(can_access_dashboard, login_url="admin_login_page")(view_func)
    )


def permissions_required_any(*permission_codenames):
    """Require at least one CampusHub permission while preserving admin redirects."""
    def _decorator(view_func):
        @login_required(login_url="admin_login_page")
        def _wrapped(request, *args, **kwargs):
            if any(
                request.user.has_perm(f"accounts.{codename}")
                for codename in permission_codenames
            ):
                return view_func(request, *args, **kwargs)
            if user_has_admin_access(request.user):
                return redirect(get_admin_home_url(request.user))
            return redirect("admin_login_page")

        return _wrapped

    return _decorator


def facility_module_required(view_func):
    @login_required(login_url="admin_login_page")
    def _wrapped(request, *args, **kwargs):
        if user_has_facility_module_access(request.user):
            return view_func(request, *args, **kwargs)
        if user_has_admin_access(request.user):
            return redirect(get_admin_home_url(request.user))
        return redirect("admin_login_page")

    return _wrapped


def products_module_required(view_func):
    @login_required(login_url="admin_login_page")
    def _wrapped(request, *args, **kwargs):
        if (
            user_can_manage_products(request.user)
            or request.user.has_perm("accounts.can_view_products") and request.GET.get("view") != "inventory"
            or request.user.has_perm("accounts.can_approve_products")
            or request.GET.get("view") == "inventory" and (request.user.has_perm("accounts.can_view_inventory") or request.user.has_perm("accounts.can_view_stock_movements"))
        ):
            return view_func(request, *args, **kwargs)
        if user_has_admin_access(request.user):
            return redirect(get_admin_home_url(request.user))
        return redirect("admin_login_page")

    return _wrapped


def admin_login_page(request):
    return render(request, "user_management/pages/admin_login.html")


def admin_logout_page(request):
    token = get_tab_token_from_request(request)
    if request.user.is_authenticated:
        log_account_activity(
            request,
            source=AccountActivity.SOURCE_ADMIN,
            account=request.user,
            activity_type="logout",
            activity="Logged out",
            result=AccountActivity.RESULT_SUCCESS,
        )
    revoke_admin_tab_token(token)
    logout(request)
    return redirect(reverse("admin_login_page"))


def get_notification_context(limit=5, *, user=None):
    from accounts.academic import scope_users, scope_seller_requests
    pending = scope_seller_requests(SellerRequest.objects.filter(status=SellerRequest.STATUS_PENDING), user)
    seller_requests = pending.select_related("user", "reviewed_by")[:limit]
    pending_seller_requests = pending.count()
    return {
        "seller_requests": seller_requests,
        "pending_seller_requests": pending_seller_requests,
    }


def _is_marketplace_admin(user):
    return (getattr(user, "role", "") or "").strip().lower() == "marketplace admin"


def _is_facilities_admin(user):
    return (getattr(user, "role", "") or "").strip().lower() == "facilities admin"


@products_module_required
def admin_products_page(request):
    from accounts.models import Department
    from modules.marketplace.services.bundles import is_bundle, prime_bundle_inventory, bundle_inventory

    all_products = admin_product_queryset(request.user)
    if request.GET.get("view") == "inventory":
        from modules.marketplace.services.inventory_monitor import inventory_monitor_context
        context = inventory_monitor_context(request, all_products)
        context["inventory_page"] = Paginator(context.pop("inventory_rows"), 30).get_page(request.GET.get("page"))
        context.update(get_notification_context(user=request.user))
        return render(request, "marketplace/pages/admin_inventory.html", context)
    active_products = all_products.filter(is_archived=False)
    from accounts.academic import academic_options, product_academic, scope_users
    from modules.marketplace.services.inventory import inventory_sku
    departments, majors = academic_options()

    from accounts.models import User
    approved_sellers = scope_users(User.objects.filter(
        Q(role__iexact="Seller") | Q(seller_access_requests__status="approved")
    ), request.user).select_related("department", "major").distinct().order_by("first_name", "last_name")
    seller_products = prime_bundle_inventory(
        all_products.select_related(
            "mobile_seller", "mobile_seller__department", "mobile_seller__major", "seller", "seller__department", "seller__major", "approved_by", "department", "major"
        ).prefetch_related("inventory_skus").order_by("-submitted_at")
    )
    today = timezone.localdate()
    for product in seller_products:
        product.admin_academic = product_academic(product)
        product.admin_sku = inventory_sku(product)
        product.admin_total_stock = max(0, product.get_total_stock() or 0)
        variant_summary = get_variant_stock_summary(product)
        product.admin_variant_count = (
            variant_summary["variant_count"]
            if customization_has_stock_tracking(product.customization_options)
            else count_customization_options(product.customization_options)
            if product.customization_enabled
            else 0
        )
        product.admin_inventory_status = get_product_inventory_status(product, today=today)
        # Parent quantity state, independent of approval and individual option alerts.
        product.admin_quantity_status = get_product_quantity_status(product)
        product.admin_threshold = None if is_bundle(product) or customization_has_stock_tracking(product.customization_options) else low_stock_threshold(product)
        product.admin_bundle_json = json.dumps(bundle_inventory(product)) if is_bundle(product) else "{}"
        product.admin_tags_json = json.dumps(product.tags)
        product.admin_has_low_stock = any(iter_product_low_stock(product, today=today))
        product.admin_low_stock_variant_count = variant_summary["low_stock_variant_count"]
    low_stock_count = sum(
        1
        for product in seller_products
        if not product.is_archived and product.admin_has_low_stock
    )
    product_stats = {
        "total": all_products.count(),
        "pending": all_products.filter(approval_status=Product.STATUS_PENDING).count(),
        "approved": all_products.filter(approval_status=Product.STATUS_APPROVED).count(),
        "rejected": active_products.filter(approval_status=Product.STATUS_REJECTED).count(),
        "low_stock": low_stock_count,
        "archived": all_products.filter(is_archived=True).count(),
    }
    return render(
        request,
        "marketplace/pages/admin_products.html",
        {
            "seller_products": seller_products,
            "product_stats": product_stats,
            "low_stock_threshold": low_stock_threshold(),
            "expiry_warning_days": getattr(settings, "CAMPUSHUB_EXPIRY_WARNING_DAYS", 7),
            "departments": departments,
            "programs": departments, "majors": majors,
            "product_categories": all_products.exclude(category="").order_by("category").values_list("category", flat=True).distinct(),
            "approved_sellers": approved_sellers,
            "approved_mobile_sellers": scope_users(CampusHubUser.objects.filter(seller_access_requests__status="approved", seller_access_requests__is_suspended=False, is_active=True), request.user).distinct(),
            "can_manage_products": user_can_manage_products(request.user),
            "can_approve_products": request.user.has_perm(
                "accounts.can_approve_products"
            ),
            "can_add_products": request.user.is_superuser or _is_marketplace_admin(request.user),
            **get_notification_context(user=request.user),
        },
    )


@login_required(login_url="admin_login_page")
@admin_read_permissions("can_manage_sellers", "can_view_sellers")
def admin_sellers_page(request):
    """Review existing seller-access requests without duplicating user records."""
    search_query = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip().lower()
    from accounts.academic import scope_users, scope_seller_requests
    seller_requests = scope_seller_requests(SellerRequest.objects.select_related(
        "user", "user__department", "user__major", "mobile_user", "mobile_user__department", "mobile_user__major", "reviewed_by"
    ), request.user).order_by("-created_at", "-pk")

    if search_query:
        seller_requests = seller_requests.filter(
            Q(full_name__icontains=search_query)
            | Q(student_id__icontains=search_query)
            | Q(product_type__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(mobile_user__email__icontains=search_query)
            | Q(mobile_user__username__icontains=search_query)
        )
    valid_statuses = {
        SellerRequest.STATUS_PENDING,
        SellerRequest.STATUS_APPROVED,
        SellerRequest.STATUS_REJECTED,
        SellerRequest.STATUS_NEEDS_REVISION,
    }
    if status_filter in valid_statuses:
        seller_requests = seller_requests.filter(status=status_filter)

    paginator = Paginator(seller_requests, 10)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    # Only read audit events for applications already authorized on this page.
    # Bound each application's history separately so a busy record cannot hide
    # another record's events or cause an unbounded dashboard query.
    from django.db.models import F, Window
    from django.db.models.functions import RowNumber
    from django.db.models.fields.json import KeyTextTransform
    from accounts.activity_service import format_activities
    from accounts.support_scope import scope_marketplace_activity
    from accounts.models import AccountActivity

    applications = list(page_obj)
    history = {application.pk: [] for application in applications}
    events = list(scope_marketplace_activity(AccountActivity.objects.all(), request.user).filter(
        metadata__seller_request_id__in=list(history),
        activity_type__in=("SELLER_REQUESTED", "SELLER_RESUBMITTED", "SELLER_APPROVED",
                           "SELLER_REJECTED", "SELLER_REVISION_REQUESTED"),
    ).annotate(_application_event_rank=Window(
        expression=RowNumber(), partition_by=[KeyTextTransform("seller_request_id", "metadata")],
        order_by=[F("created_at").desc(), F("pk").desc()],
    )).filter(_application_event_rank__lte=10).order_by("-created_at", "-pk")) if history else []
    for event, detail in zip(events, format_activities(events, scoped=True, include_targets=False)):
        actor = detail["performed_by"]
        history[event.metadata["seller_request_id"]].append({
            "action": detail["action"], "recorded_at": event.created_at,
            "actor": actor["name"] if actor["name"] != "Unknown" else "Not recorded",
            "username": actor["username"],
        })
    for application in page_obj:
        application.review_events = history[application.pk]
        account = application.mobile_user if application.mobile_user_id else application.user
        application.display_username = account.username if account else ""
        application.display_department = account.department if account else None
        application.display_major = account.major if account else None
        # An application snapshot is historical context, never an authorization input.
        snapshot = application.application_data if isinstance(application.application_data, dict) else {}
        application.snapshot_program = snapshot.get("program") if not application.display_department else None
        # Application Details drawer values: display only, never saved or used for scope.
        application.display_email = (account.email if account else "") or snapshot.get("email") or ""
        try:
            confirmed_at = parse_datetime(str(snapshot.get("confirmed_at") or ""))
        except ValueError:
            confirmed_at = None
        # Only an offset-aware stored value can be converted to Manila time honestly.
        application.confirmed_at_value = confirmed_at if confirmed_at and timezone.is_aware(confirmed_at) else None
        application.program_snapshot = snapshot.get("program_major") or snapshot.get("program") or ""
        confirmations = snapshot.get("confirmations") if isinstance(snapshot.get("confirmations"), dict) else {}
        application.confirmation_rows = [
            (label, confirmations.get(key) is True)
            for key, label in (("accuracy", "Information Accuracy"), ("rules", "Marketplace Rules"), ("approval", "Approval Requirement"))
        ]
    query_without_page = request.GET.copy()
    query_without_page.pop("page", None)
    clear_query = query_without_page.copy()
    clear_query.pop("q", None)
    clear_query.pop("status", None)
    status_counts = {
        "total": scope_seller_requests(SellerRequest.objects.all(), request.user).count(),
        "pending": scope_seller_requests(SellerRequest.objects.filter(status=SellerRequest.STATUS_PENDING), request.user).count(),
        "approved": scope_seller_requests(SellerRequest.objects.filter(status=SellerRequest.STATUS_APPROVED), request.user).count(),
        "rejected": scope_seller_requests(SellerRequest.objects.filter(status=SellerRequest.STATUS_REJECTED), request.user).count(),
    }
    return render(
        request,
        "marketplace/pages/admin_sellers.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
            "status_filter": status_filter,
            "status_counts": status_counts,
            "query_without_page": query_without_page.urlencode(),
            "seller_filter_parameters": [(key, value) for key, value in request.GET.items()
                                         if key not in {"q", "status", "page"}],
            "seller_clear_query": clear_query.urlencode(),
            **get_notification_context(user=request.user),
        },
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_access_notifications", login_url="admin_dashboard_page")
def admin_notifications_page(request):
    return render(
        request,
        "notifications/pages/admin_notifications.html",
        get_notification_context(limit=100, user=request.user),
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_access_messages", login_url="admin_dashboard_page")
def admin_messages_page(request):
    return render(
        request,
        "messages/pages/admin_messages.html",
        get_notification_context(user=request.user),
    )


@login_required(login_url="admin_login_page")
@admin_read_permissions("can_manage_orders", "can_view_orders")
def admin_orders_page(request):
    from modules.marketplace.services.orders import orders_page_context

    return render(request, "marketplace/pages/admin_orders.html", {
        **orders_page_context(request.user, request.GET),
        "orders_tab_token": get_tab_token_from_request(request) or "",
        "orders_reset_url": reverse("admin_orders_page") + ("?__at=" + get_tab_token_from_request(request) if get_tab_token_from_request(request) else ""),
        "order_status_options": MarketplaceOrder.STATUS_CHOICES,
        "payment_status_options": MarketplaceOrder.PAYMENT_STATUS_CHOICES,
        "date_options": (("today", "Today"), ("7days", "Last 7 Days"), ("30days", "Last 30 Days"),
                         ("month", "This Month"), ("previous_month", "Previous Month"), ("custom", "Custom Range")),
        **get_notification_context(user=request.user),
    })


@permissions_required_any("can_view_users", "can_manage_admin_accounts")
def admin_users_page(request):
    return render(
        request,
        "user_management/pages/admin_user_access_control.html",
        {
            **get_user_management_context(request),
            **get_notification_context(user=request.user),
        },
    )


def _active_super_admin_count():
    return len(list(User.objects.select_for_update().filter(is_active=True, is_suspended=False).filter(
        Q(is_superuser=True) | Q(role__iexact="Super Admin")
    ).order_by("pk")))


def _is_super_admin(account):
    return isinstance(account, User) and (
        account.is_superuser or (account.role or "").strip().lower() == "super admin"
    )


def _duplicate_account(username, email, source=None, account_id=None):
    admin_names = User.objects.filter(username__iexact=username)
    mobile_names = CampusHubUser.objects.filter(username__iexact=username)
    admin_emails = User.objects.filter(email__iexact=email) if email else User.objects.none()
    mobile_emails = (
        CampusHubUser.objects.filter(email__iexact=email) if email else CampusHubUser.objects.none()
    )
    if source == "admin":
        admin_names = admin_names.exclude(pk=account_id)
        admin_emails = admin_emails.exclude(pk=account_id)
    elif source == "mobile":
        mobile_names = mobile_names.exclude(pk=account_id)
        mobile_emails = mobile_emails.exclude(pk=account_id)
    if admin_names.exists() or mobile_names.exists():
        return f'Username "{username}" already exists.'
    if admin_emails.exists() or mobile_emails.exists():
        return f'Email "{email}" is already in use.'
    return ""


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_admin_accounts", login_url="admin_dashboard_page")
@transaction.atomic
def admin_users_save(request):
    """Create or update an account without changing its owning account store."""
    if request.method != "POST":
        return redirect("admin_users_page")
    list(User.objects.select_for_update().filter(Q(is_superuser=True) | Q(role__iexact="Super Admin")).order_by("pk"))
    active_super_admins = _active_super_admin_count()

    account_reference = request.POST.get("account_ref", "").strip()
    username = request.POST.get("username", "").strip()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    contact_number = request.POST.get("contact_number", "").strip()
    account_type = request.POST.get("account_type", "").strip().lower()
    role = request.POST.get("role", "").strip()
    department_id = request.POST.get("department", "").strip()
    password = request.POST.get("password", "")
    confirm_password = request.POST.get("confirm_password", "")
    is_active = request.POST.get("is_active") == "on"

    if not all((first_name, last_name, username, email, account_type, role)):
        messages.error(request, "Complete all required user fields.")
        return redirect("admin_users_page")
    if account_type not in dict(ACCOUNT_TYPES):
        messages.error(request, "Choose a valid account type.")
        return redirect("admin_users_page")

    from accounts.models import Department

    role_record = Role.objects.filter(role_name__iexact=role).first()
    if role_record is None:
        messages.error(request, "Choose a valid role.")
        return redirect("admin_users_page")
    if not role_record.is_active:
        messages.error(request, "Inactive roles cannot be assigned to users.")
        return redirect("admin_users_page")
    role = role_record.role_name
    admin_access = is_admin_role(role)
    if not account_reference and (
        account_type != "admin" or role.lower() not in CREATABLE_ADMIN_ROLES
    ):
        messages.error(
            request,
            "Add Admin can create only Super Admin, Marketplace Admin, or Facilities Admin accounts.",
        )
        return redirect("admin_users_page")
    if account_type == "admin" and not admin_access:
        messages.error(request, "Admin accounts require an approved administrator role.")
        return redirect("admin_users_page")
    if account_type != "admin" and admin_access:
        messages.error(request, "Administrator roles require the Admin account type.")
        return redirect("admin_users_page")
    if role.lower() == "super admin" and not request.user.is_superuser:
        messages.error(request, "Only a Super Admin can assign the Super Admin role.")
        return redirect("admin_users_page")

    source, existing_user = resolve_account(account_reference) if account_reference else (None, None)
    if existing_user is not None:
        existing_user = type(existing_user).objects.select_for_update().get(pk=existing_user.pk)
    if account_reference and existing_user is None:
        messages.error(request, "User not found.")
        return redirect("admin_users_page")
    if existing_user and _is_super_admin(existing_user) and not request.user.is_superuser:
        raise PermissionDenied("Only a Super Admin can modify a Super Admin account.")
    from accounts.academic import resolve_account_academic
    if existing_user:
        from .support_scope import can_manage_account, is_super_admin
        if not can_manage_account(request.user, existing_user):
            raise PermissionDenied("This account is outside your account-editing scope.")
        if password:
            messages.error(request, "Use Assist Account Recovery; the account owner must choose their password.")
            return redirect("admin_users_page")
        if role != existing_user.role and not is_super_admin(request.user):
            raise PermissionDenied("Only Super Admin can change administrator roles.")
    try:
        department, major = resolve_account_academic(role, account_type, department_id, request.POST.get("major"), existing=existing_user)
    except (ValueError, TypeError) as exc:
        messages.error(request, str(exc))
        return redirect("admin_users_page")
    expected_source = "admin" if account_type == "admin" else "mobile"
    if existing_user and source != expected_source:
        messages.error(request, "Account type cannot be changed between mobile and admin storage.")
        return redirect("admin_users_page")
    try:
        validate_email(email)
        account_model = User if expected_source == "admin" else CampusHubUser
        for name, value in (("username", username), ("first_name", first_name), ("last_name", last_name), ("email", email), ("contact_number", contact_number)):
            account_model._meta.get_field(name).clean(value, existing_user)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return redirect("admin_users_page")

    duplicate_error = _duplicate_account(
        username,
        email,
        source=source,
        account_id=getattr(existing_user, "pk", None),
    )
    if duplicate_error:
        messages.error(request, duplicate_error)
        return redirect("admin_users_page")
    if not existing_user and not password:
        messages.error(request, "Password is required for new users.")
        return redirect("admin_users_page")
    if password:
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("admin_users_page")
        password_errors = strict_password_errors(password)
        if password_errors:
            messages.error(request, " ".join(password_errors))
            return redirect("admin_users_page")
        password_user = existing_user if isinstance(existing_user, User) else User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        try:
            validate_password(password, password_user)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
            return redirect("admin_users_page")

    if isinstance(existing_user, User) and existing_user == request.user:
        if not is_active:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect("admin_users_page")
        if not admin_access:
            messages.error(request, "You cannot remove your own administrator role.")
            return redirect("admin_users_page")
    if (
        existing_user
        and _is_super_admin(existing_user)
        and existing_user.is_active and not existing_user.is_suspended
        and (not is_active or role.lower() != "super admin")
        and active_super_admins <= 1
    ):
        messages.error(request, "The final active Super Admin cannot be deactivated or demoted.")
        return redirect("admin_users_page")

    previous = {field: getattr(existing_user, field, None) for field in ("role", "department_id", "major_id", "is_active", "email")}

    with transaction.atomic():
        if source == "admin":
            user = existing_user
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            if previous["email"].casefold() != email.casefold():
                user.email_verified = False
            user.contact_number = contact_number
            user.role = role
            user.department = department
            user.major = major
            user.is_active = is_active
            if is_active:
                user.is_suspended = False
            user.is_staff = admin_access
            user.is_superuser = role.lower() == "super admin"
            if password:
                user.set_password(password)
            user.save()
            sync_user_admin_permissions(user)
        elif source == "mobile":
            user = existing_user
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            if previous["email"].casefold() != email.casefold():
                user.email_verified = False
            user.contact_number = contact_number
            user.user_type = account_type
            user.role = role
            user.department = department
            user.major = major
            user.is_active = is_active
            if is_active:
                user.is_suspended = False
            if account_type == "student":
                user.student_id = user.student_id or username
            if password:
                user.password_hash = make_password(password)
            user.save()
        elif account_type == "admin":
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                department=department,
                major=major,
                contact_number=contact_number,
                is_active=is_active,
                is_staff=admin_access,
                is_superuser=role.lower() == "super admin",
            )
            sync_user_admin_permissions(user)
        else:
            CampusHubUser.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                contact_number=contact_number,
                user_type=account_type,
                student_id=username if account_type == "student" else None,
                institutional_id=username if account_type in {"student", "faculty"} else "",
                password_hash=make_password(password),
                role=role,
                department=department,
                major=major,
                is_active=is_active,
                profile_completed=bool(contact_number),
            )

    from accounts.user_management import log_management_event
    log_management_event(request, source=source or "admin", account=user,
                         action="USER_UPDATED" if existing_user else "ADMIN_CREATED")
    if existing_user:
        for field, event in (("role", "ADMIN_ROLE_CHANGED"), ("department_id", "ADMIN_SCOPE_CHANGED"), ("major_id", "ADMIN_SCOPE_CHANGED"), ("is_active", "ACCOUNT_REACTIVATED" if is_active else "ACCOUNT_DEACTIVATED")):
            if previous[field] != getattr(user, field):
                log_management_event(request, source=source, account=user, action=event)
        if password:
            log_management_event(request, source=source, account=user, action="PASSWORD_RESET")
    messages.success(request, f'User "{username}" {"updated" if existing_user else "created"}.')
    return redirect("admin_users_page")


@login_required(login_url="admin_login_page")
@admin_read_permissions("can_manage_admin_accounts", "can_reset_user_password", "can_manage_sellers")
@transaction.atomic
def admin_users_action(request):
    if request.method != "POST":
        return redirect("admin_users_page")
    if request.POST.get("action") in {"reset_password", "assist_recovery", "verify_email"}:
        from .password_support import initiate_reset
        return initiate_reset(request)
    list(User.objects.select_for_update().filter(Q(is_superuser=True) | Q(role__iexact="Super Admin")).order_by("pk"))
    active_super_admins = _active_super_admin_count()

    source, account = resolve_account(request.POST.get("account_ref", "").strip())
    action = request.POST.get("action", "").strip().lower()
    if account is None:
        messages.error(request, "User not found.")
        return redirect("admin_users_page")
    from .support_scope import can_manage_account, can_manage_seller
    if action == "seller_access":
        if not can_manage_seller(request.user, source, account):
            raise PermissionDenied("Seller access is outside your authorized scope.")
    elif not can_manage_account(request.user, account):
        raise PermissionDenied("Account management is outside your authorized scope.")
    account = type(account).objects.select_for_update().get(pk=account.pk)
    if _is_super_admin(account) and not request.user.is_superuser:
        raise PermissionDenied("Only a Super Admin can modify a Super Admin account.")

    protected_change = action in {"deactivate", "suspend"}
    if source == "admin" and account == request.user and protected_change:
        messages.error(request, "You cannot deactivate or suspend your own account.")
        return redirect("admin_users_page")
    if protected_change and _is_super_admin(account) and account.is_active and not account.is_suspended and active_super_admins <= 1:
        messages.error(request, "The final active Super Admin cannot be deactivated or suspended.")
        return redirect("admin_users_page")

    if action in {"activate", "deactivate", "suspend"}:
        account.is_active = action == "activate"
        account.is_suspended = action == "suspend"
        account.save(update_fields=["is_active", "is_suspended"])
        state = {"activate": "activated", "deactivate": "deactivated", "suspend": "suspended"}[action]
        messages.success(request, f'Account "{account.username}" was {state}.')
        event = "ACCOUNT_REACTIVATED" if action == "activate" else "ACCOUNT_DEACTIVATED"
    elif action == "seller_access":
        if source == "admin":
            messages.error(request, "Seller access does not apply to administrator accounts.")
            return redirect("admin_users_page")
        seller_status = request.POST.get("seller_status", "").strip().lower()
        valid_statuses = {
            SellerRequest.STATUS_PENDING,
            SellerRequest.STATUS_APPROVED,
            SellerRequest.STATUS_REJECTED,
            "suspended",
        }
        if seller_status not in valid_statuses:
            messages.error(request, "Choose a valid seller access status.")
            return redirect("admin_users_page")
        seller_request = seller_request_for(source, account)
        if seller_request is None:
            messages.error(request, "No seller application exists. The user must apply first.")
            return redirect("admin_users_page")
        from .academic import scope_seller_requests
        if not scope_seller_requests(SellerRequest.objects.filter(pk=seller_request.pk), request.user).exists():
            raise PermissionDenied("This seller application is outside your authorized scope.")
        seller_request = SellerRequest.objects.select_for_update().get(pk=seller_request.pk)
        if (request.user.role or "").casefold() == "marketplace admin" and not (
            seller_request.status == SellerRequest.STATUS_APPROVED and seller_status in {"suspended", "approved"}
        ):
            raise PermissionDenied("Use the Sellers module for application reviews.")
        was_suspended = seller_request.is_suspended
        if seller_status == "suspended":
            if seller_request.status != SellerRequest.STATUS_APPROVED:
                messages.error(request, "Only approved seller access can be suspended.")
                return redirect("admin_users_page")
            seller_request.is_suspended = True
        elif seller_status == "approved" and seller_request.is_suspended:
            seller_request.is_suspended = False  # Preserve the original approval date/reviewer.
        else:
            seller_request.status = seller_status
            seller_request.is_suspended = False
            seller_request.reviewed_by = request.user
            seller_request.reviewed_at = timezone.now()
            seller_request.rejection_reason = request.POST.get("reason", "").strip() if seller_status == "rejected" else ""
        seller_request.save()
        messages.success(request, f'Seller access updated for "{account.username}".')
        event = {"approved": "SELLER_RESTORED" if was_suspended else "SELLER_APPROVED", "suspended": "SELLER_SUSPENDED", "rejected": "SELLER_REJECTED", "pending": "SELLER_PENDING"}[seller_status]
    else:
        messages.error(request, "Unsupported user action.")
        return redirect("admin_users_page")

    from accounts.user_management import log_management_event
    log_management_event(request, source=source, account=account, action=event)

    return redirect("admin_users_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_admin_accounts", login_url="admin_dashboard_page")
def admin_users_delete(request):
    """Compatibility endpoint for old forms; user records are not hard-deleted."""
    messages.error(request, "Permanent user deletion is disabled. Deactivate the account instead.")
    return redirect("admin_users_page")


@facility_module_required
def admin_facility_page(request, *, services=False):
    from api.models import Booking, Facility, Room
    from modules.facilities.services.operating_schedule import workflow_for_display
    from modules.facilities.services.rental_configuration import PRICING_METHODS, capacity_label, pricing_label
    from modules.facilities.services.facility_configuration import (
        BOOKING_MODE_LABELS,
        FACILITY_TYPE_CONFIG,
        STATUS_CHOICES,
        facility_form_configuration,
    )

    from modules.facilities.services.catalog import SERVICE_TYPES, service_labels, service_resources_q

    facilities_qs = Facility.objects.all()
    facilities_qs = facilities_qs.filter(service_resources_q()) if services else facilities_qs.exclude(service_resources_q())
    facilities_qs = facilities_qs.annotate(configured_room_count=Count("rooms"))
    facilities = list(facilities_qs)
    for facility in facilities:
        facility.form_workflow = workflow_for_display(facility)
        facility.capacity_display = capacity_label(facility)
        from modules.facilities.services.service_configuration import service_pricing_label
        facility.pricing_display = service_pricing_label(facility) if services else pricing_label(facility)
        facility.price_method_display = PRICING_METHODS.get(facility.price_type, f"Per {facility.price_type}")
        facility.service_type_display, facility.request_type_display = service_labels(facility)
        facility.service_status_display = {"available": "Active", "inactive": "Inactive"}.get(facility.availability_status, "Temporarily Unavailable")
    from modules.facilities.services.service_configuration import service_configuration_choices, CATEGORIES, STATUSES
    can_manage = user_can_manage_facilities(request.user)
    configured_units = sum(
        max(int(units or 0), 0)
        for units in facilities_qs.values_list("rooms_units", flat=True)
    ) if services else 0
    room_facilities = facilities_qs if services else facilities_qs.filter(is_archived=False)
    room_records = Room.objects.filter(facility__in=room_facilities).count()

    recent_activities = []
    if services:
        for facility in facilities_qs.order_by("-updated_at")[:8]:
            occurred_at = facility.updated_at or facility.created_at
            if not occurred_at:
                continue
            was_updated = bool(
                facility.created_at
                and facility.updated_at
                and (facility.updated_at - facility.created_at).total_seconds() > 1
            )
            recent_activities.append(
                {
                    "kind": "facility",
                    "title": (
                        f"{facility.facility_name} {'service' if services else 'facility'} details updated."
                        if was_updated
                        else f"{facility.facility_name} added."
                    ),
                    "description": ("Service update" if services else "Facility update") if was_updated else ("New service" if services else "New facility"),
                    "occurred_at": occurred_at,
                }
            )

        booking_activity_labels = {
            "class": "class schedule recorded",
            "maintenance": "maintenance schedule recorded",
            "assessment": "assessment schedule recorded",
            "reservation": "reservation updated",
        }
        for booking in Booking.objects.filter(facility__in=facilities_qs).select_related("facility", "user").order_by("-updated_at")[:8]:
            occurred_at = booking.updated_at or booking.created_at
            if not occurred_at:
                continue
            event_type, _, purpose = _booking_display_fields(booking)
            facility_name = booking.facility.facility_name if booking.facility_id else "Facility"
            recent_activities.append(
                {
                    "kind": event_type,
                    "title": f"{facility_name} {'request updated' if services else booking_activity_labels.get(event_type, 'booking updated')}.",
                    "description": purpose or booking.get_status_display(),
                    "occurred_at": occurred_at,
                }
            )

        from modules.facilities.services.activity import recent_facility_activities
        service_events = recent_facility_activities(services=True)
        if service_events:
            recent_activities = service_events
        recent_activities.sort(key=lambda item: item["occurred_at"], reverse=True)
    else:
        from modules.facilities.services.activity import recent_facility_activities
        recent_activities = recent_facility_activities()
    active_facilities_qs = facilities_qs.filter(is_archived=False)
    context = {
        "facilities": facilities,
        "facilities_total": active_facilities_qs.count(),
        "facilities_archived_total": facilities_qs.filter(is_archived=True).count(),
        "open_for_booking_count": active_facilities_qs.filter(
            availability_status=Facility.STATUS_AVAILABLE
        ).count(),
        "under_maintenance_count": active_facilities_qs.filter(availability_status__in=("unavailable", "maintenance", "reserved", "occupied") if services else ("maintenance",)).count(),
        "rooms_units_total": active_facilities_qs.filter(availability_status="inactive").count() if services else max(configured_units, room_records),
        "service_configuration": service_configuration_choices() if services else {},
        'can_view_service_requests': any(request.user.has_perm('accounts.'+code) for code in (
            'can_view_bookings','can_manage_bookings','can_approve_bookings','can_record_facility_payment')),
        "facility_type_choices": tuple(CATEGORIES.items()) if services else tuple((value, FACILITY_TYPE_CONFIG.get(value, {}).get("label", label)) for value, label in Facility.TYPE_CHOICES if (value in SERVICE_TYPES) == services),
        "booking_mode_choices": tuple((value, label) for value, label in BOOKING_MODE_LABELS.items() if (value in {"service", "assessment", "lease"}) == services),
        "facility_status_choices": tuple(STATUSES.items()) if services else STATUS_CHOICES,
        "facility_status_filter": (request.GET.get("status") or "").strip().lower(),
        "facility_form_configuration": facility_form_configuration(),
        "calendar_events": [] if services else _bookings_calendar_events(),
        "recent_facility_activities": recent_activities[:8],
        "can_view_facility_activity_history": not services and _is_super_admin(request.user) and request.user.has_perm("accounts.can_view_user_monitoring"),
        "can_manage_facilities": can_manage,
        "can_book_facilities": user_can_book_facilities(request.user),
        "can_manage_schedules": request.user.has_perm("accounts.can_manage_schedules"),
        "service_catalog": services,
        "page_title": "Services" if services else "Facilities",
        "active_page": "services" if services else "facilities",
        **get_notification_context(user=request.user),
    }


    if can_manage or services:
        return render(request, "facilities/pages/admin_facility.html", context)

    context.update(
        {
            "available_count": active_facilities_qs.filter(availability_status="available").count(),
            "facilities_total": active_facilities_qs.count(),
        }
    )
    return render(request, "facilities/pages/admin_facility_booking.html", context)


def _booking_display_fields(booking):
    """Extract the schedule type, requester, and public purpose from a booking."""
    import re

    type_pattern = re.compile(r"^\[(class|reservation|maintenance|assessment|official|hold|other|blocked)\]\s*", re.I)
    reserved_pattern = re.compile(r"(?:^|\n)Reserved by:\s*(.+)$", re.I | re.M)

    purpose = (booking.purpose or "").strip()
    event_type = "reservation"
    type_match = type_pattern.match(purpose)
    if type_match:
        event_type = type_match.group(1).lower()
        purpose = purpose[type_match.end():].strip()

    reserved_by = ""
    reserved_match = reserved_pattern.search(purpose)
    if reserved_match:
        reserved_by = reserved_match.group(1).strip()
        purpose = reserved_pattern.sub("", purpose).strip()
    elif booking.user_id:
        user = booking.user
        full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        reserved_by = full_name or getattr(user, "username", "") or ""

    return event_type, reserved_by, purpose


def _bookings_calendar_events(first=None, last=None):
    """Compatibility entry point for the shared, read-only calendar projection."""
    from datetime import timedelta
    from modules.facilities.services.calendar import calendar_events
    first = first or timezone.localdate().replace(day=1)
    last = last or first + timedelta(days=366)
    return calendar_events(first, last)


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_orders", raise_exception=True)
def admin_order_update(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Send an order update object."}, status=400)
    if "fulfillment_action" in payload:
        if set(payload) != {"fulfillment_action"}:
            return JsonResponse({"error": "Record fulfillment progress separately from payment updates."}, status=400)
        from modules.marketplace.services.fulfillment import advance
        return advance(admin_order_queryset(request.user), order_id, payload["fulfillment_action"],
            request.user.get_full_name().strip() or request.user.username)
    for field in ("status", "payment_status", "official_receipt_no", "pickup_location", "pickup_scheduled_at", "cancellation_reason"):
        if payload.get(field) is not None and not isinstance(payload[field], str):
            return JsonResponse({"error": f"{field.replace('_', ' ').title()} must be text."}, status=400)

    from modules.marketplace.services.fulfillment import ORDER_TRANSITIONS
    allowed_transitions = ORDER_TRANSITIONS

    with transaction.atomic():
        order_query = admin_order_queryset(request.user).select_for_update(of=("self",))

        order = get_object_or_404(order_query, id=order_id)

        current_status = order.status
        seller_delivery = order.fulfillment_method == "seller_delivery"
        previous_payment_status = order.payment_status
        requested_status = (payload.get("status") or current_status).strip().lower()
        valid_statuses = {choice[0] for choice in MarketplaceOrder.STATUS_CHOICES}
        if requested_status not in valid_statuses:
            return JsonResponse({"error": "Invalid order status."}, status=400)
        if (
            requested_status != current_status
            and requested_status not in allowed_transitions.get(current_status, set())
        ):
            return JsonResponse(
                {
                    "error": (
                        f"Order cannot move from {order.get_status_display()} to "
                        f"{dict(MarketplaceOrder.STATUS_CHOICES)[requested_status]}."
                    )
                },
                status=409,
            )

        if requested_status == "cancelled" and order.delivered_at:
            return JsonResponse({"error": "A delivered order cannot be cancelled. Returns and refunds are not supported here."}, status=409)

        payment_status = (
            payload.get("payment_status") or order.payment_status
        ).strip().lower()
        if payment_status not in {
            MarketplaceOrder.PAYMENT_UNPAID,
            MarketplaceOrder.PAYMENT_PAID,
        }:
            return JsonResponse({"error": "Invalid payment status."}, status=400)

        receipt_no = (payload.get("official_receipt_no", order.official_receipt_no) or "").strip()
        cash_confirmed = payload.get("cash_confirmed") is True
        # Legacy combined Cash on Pickup confirmation also acknowledges collection.
        # An explicit false pickup confirmation must never be overridden.
        pickup_confirmed = payload.get("pickup_confirmed", cash_confirmed) is True

        if previous_payment_status == MarketplaceOrder.PAYMENT_PAID and payment_status != previous_payment_status:
            return JsonResponse({"error": "Recorded payments cannot be reverted through order status updates."}, status=409)
        if requested_status == MarketplaceOrder.STATUS_CANCELLED and payment_status != previous_payment_status:
            return JsonResponse({"error": "Cancelled orders cannot accept a new payment."}, status=409)

        # Cash on Pickup Completion verification
        if requested_status == MarketplaceOrder.STATUS_COMPLETED:
            if seller_delivery and not order.delivered_at:
                return JsonResponse({"error": "Record seller delivery before completing the order."}, status=409)
            if not seller_delivery and current_status != requested_status and not pickup_confirmed:
                return JsonResponse({"error": "Confirm that the buyer has collected the order before completion."}, status=409)
            if not cash_confirmed and payment_status != MarketplaceOrder.PAYMENT_PAID and order.payment_status != MarketplaceOrder.PAYMENT_PAID:
                return JsonResponse(
                    {"error": "Cash payment receipt must be confirmed before completing the order."},
                    status=409,
                )
            payment_status = MarketplaceOrder.PAYMENT_PAID

        cancellation_reason = (payload.get("cancellation_reason", order.cancellation_reason) or "").strip()
        if (
            requested_status == MarketplaceOrder.STATUS_CANCELLED
            and requested_status != current_status
            and not cancellation_reason
        ):
            return JsonResponse({"error": "Cancellation reason is required."}, status=400)

        pickup_raw = (payload.get("pickup_scheduled_at") or "").strip()
        pickup_scheduled_at = order.pickup_scheduled_at if "pickup_scheduled_at" not in payload else None
        if pickup_raw:
            pickup_scheduled_at = parse_datetime(pickup_raw)
            if pickup_scheduled_at is None:
                return JsonResponse({"error": "Invalid pickup date and time."}, status=400)
            if timezone.is_naive(pickup_scheduled_at):
                pickup_scheduled_at = timezone.make_aware(pickup_scheduled_at)

        now = timezone.now()
        changed_by = request.user.get_full_name().strip() or request.user.username
        update_fields = {
            "status",
            "payment_status",
            "official_receipt_no",
            "pickup_location",
            "pickup_scheduled_at",
            "cancellation_reason",
            "updated_at",
        }

        order.status = requested_status
        order.payment_status = payment_status
        # A receipt reference is metadata, not payment confirmation by itself.
        order.official_receipt_no = receipt_no
        order.pickup_location = (payload.get("pickup_location", order.pickup_location) or "").strip()
        order.pickup_scheduled_at = pickup_scheduled_at
        order.cancellation_reason = (
            cancellation_reason
            if requested_status == MarketplaceOrder.STATUS_CANCELLED
            else ""
        )

        if payment_status == MarketplaceOrder.PAYMENT_PAID:
            if previous_payment_status != MarketplaceOrder.PAYMENT_PAID or not order.paid_at:
                order.paid_at = now
                order.payment_encoded_by = changed_by
            update_fields.update({"paid_at", "payment_encoded_by"})
        elif current_status != MarketplaceOrder.STATUS_COMPLETED:
            order.paid_at = None
            order.payment_encoded_by = ""
            update_fields.update({"paid_at", "payment_encoded_by"})

        if (
            requested_status == MarketplaceOrder.STATUS_COMPLETED
            and current_status != requested_status
        ):
            order.completed_at = now
            update_fields.add("completed_at")
            if not seller_delivery:
                order.picked_up_at = now
                update_fields.add("picked_up_at")

        if (
            requested_status == MarketplaceOrder.STATUS_CANCELLED
            and current_status != requested_status
        ):
            order.cancelled_at = now
            update_fields.add("cancelled_at")
            if order.inventory_deducted and not order.inventory_restored:
                from modules.marketplace.services.bundles import restore_bundle
                from modules.marketplace.services.inventory import InsufficientStockError
                try:
                    with transaction.atomic():
                        if (order.customization or {}).get("bundle_components"):
                            restore_bundle(order, changed_by)
                        elif order.product_id:
                            product = Product.objects.select_for_update().get(id=order.product_id)
                            selections = (order.customization or {}).get("selections") or []
                            product._inventory_order_id = order.pk
                            product._inventory_actor = changed_by
                            adjust_product_stock(product, selections, order.quantity, restore=True)
                            product.save(update_fields=["stock", "customization_options", "updated_at"])
                        else:
                            raise InsufficientStockError("Original inventory is unavailable; reconcile this order before cancellation.")
                except InsufficientStockError as exc:
                    return JsonResponse({"error": str(exc)}, status=409)
                order.inventory_restored = True
                update_fields.add("inventory_restored")

        order.save(update_fields=sorted(update_fields))

        if requested_status == MarketplaceOrder.STATUS_COMPLETED and current_status != requested_status and order.inventory_deducted:
            from modules.marketplace.services.inventory_records import record_completed_sale
            record_completed_sale(order, changed_by)

        if requested_status != current_status:
            MarketplaceOrderStatusHistory.objects.create(
                order=order,
                previous_status=current_status,
                new_status=requested_status,
                changed_by=changed_by,
                notes=cancellation_reason,
            )

        if requested_status != current_status or payment_status != previous_payment_status:
            log_account_activity(request, source=AccountActivity.SOURCE_ADMIN,
                account=request.user, activity_type="order_updated", module="Marketplace Orders",
                activity=f"Order {order.order_code or order.pk}: {current_status} -> {requested_status}; payment {previous_payment_status} -> {payment_status}",
                result=AccountActivity.RESULT_SUCCESS, metadata={"order_id": order.pk})
            from .activity_logging import log_marketplace_event
            buyer = CampusHubUser.objects.filter(pk=order.buyer_user_id).first() if order.buyer_user_id else None
            event_product = order.product
            log_marketplace_event(request, account=buyer, source="mobile", activity_type="ORDER_UPDATED",
                activity=f"Order {order.order_code or order.pk}: {order.get_status_display()}",
                metadata={"order_id": order.pk, "previous_status": current_status, "new_status": requested_status,
                    "program_id": (event_product.department_id or event_product.owner.department_id) if event_product else None,
                    "major_id": (event_product.major_id if event_product.department_id else event_product.owner.major_id) if event_product else None})

    return JsonResponse(
        {
            "message": "Order updated.",
            "order": {
                "id": order.id,
                "status": order.status,
                "status_label": order.get_status_display(),
                "payment_status": order.payment_status,
                "payment_status_label": order.get_payment_status_display(),
                "official_receipt_no": order.official_receipt_no,
                "pickup_location": order.pickup_location,
                "pickup_scheduled_at": (
                    timezone.localtime(order.pickup_scheduled_at).isoformat()
                    if order.pickup_scheduled_at
                    else ""
                ),
                "cancellation_reason": order.cancellation_reason,
            },
        }
    )


def _booking_request_rows(user=None):
    """Bounded first page; use the same serializer as transaction API responses."""
    from modules.facilities.booking_workflow_views import physical_bookings, row_set
    return row_set(physical_bookings().order_by("-created_at", "-pk")[:20], user)


@permissions_required_any(
    "can_manage_bookings",
    "can_approve_bookings",
    "can_record_facility_payment",
    "can_view_bookings",
)
def admin_bookings_page(request):
    from api.models import Facility
    from modules.facilities.booking_workflow_views import list_data, physical_bookings
    from modules.facilities.services.catalog import service_resources_q
    if request.GET.get('booking'):
        selected = get_object_or_404(physical_bookings(), pk=request.GET['booking'])
        target = reverse('admin_booking_details_page', kwargs={'booking_id': selected.pk})
        token = get_tab_token_from_request(request)
        if token:
            from urllib.parse import urlencode
            target += '?' + urlencode({'__at': token})
        return redirect(target)
    page_data = list_data(request.GET, request.user)
    kpi_filter = request.GET.get('kpi', '')

    context = {
        "booking_requests": page_data['bookings'],
        "booking_total": page_data['total'],
        'booking_page':page_data['page'], 'booking_pages':page_data['pages'],
        'booking_start':page_data['start_index'], 'booking_end':page_data['end_index'],
        'booking_has_previous':page_data['has_previous'], 'booking_has_next':page_data['has_next'],
        'booking_kpis':page_data['kpis'],
        'booking_kpi_filter':kpi_filter if kpi_filter in ('pending','upcoming','unpaid') else '',
        'booking_facility_filter':request.GET.get('facility',''),
        'booking_record_filter':request.GET.get('record_status','current'),
        'booking_search':(request.GET.get('q') or '').strip()[:100],
        "booking_status_filter": (request.GET.get("status") or "").strip().lower(),
        "facilities": Facility.objects.filter(is_archived=False).exclude(service_resources_q()).order_by("facility_name")[:100],
        "can_manage_facilities": user_can_manage_facilities(request.user),
        "can_book_facilities": user_can_book_facilities(request.user),
        "can_manage_schedules": request.user.has_perm("accounts.can_manage_schedules"),
        "can_approve_bookings": request.user.has_perm("accounts.can_approve_bookings"),
        "can_record_facility_payment": request.user.has_perm(
            "accounts.can_record_facility_payment"
        ),
        "page_title": "Bookings",
        "breadcrumb_page": "Bookings",
        "active_page": "bookings",
        **get_notification_context(user=request.user),
    }
    return render(request, "facilities/pages/admin_bookings.html", context)


@login_required(login_url="admin_login_page")
def admin_calendar_page(request):
    from datetime import timedelta
    from modules.facilities.services.calendar import calendar_data, calendar_facilities
    from accounts.role_permissions import user_has_admin_access
    if not user_has_admin_access(request.user) or not any(request.user.has_perm("accounts." + code)
            for code in ("can_manage_schedules", "can_view_bookings")):
        raise PermissionDenied
    first = timezone.localdate().replace(day=1)
    last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    data = calendar_data(first, last)
    context = {
        "calendar_data": data,
        "facilities": calendar_facilities(),
        "can_manage_facilities": user_can_manage_facilities(request.user),
        "can_book_facilities": False,  # Calendar reuses only the schedule editor.
        "can_manage_schedules": request.user.has_perm("accounts.can_manage_schedules"),
        "calendar_only": True,
        "page_title": "Calendar", "breadcrumb_page": "Calendar", "active_page": "calendar",
        **get_notification_context(user=request.user),
    }
    return render(request, "facilities/pages/admin_bookings.html", context)


# Existing URLs retain their names; role edits reuse the shared RBAC store.
from .role_management import (
    admin_roles_page, admin_roles_save, admin_role_permissions_save,
    admin_roles_status, admin_roles_delete,
)


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_view_user_monitoring", login_url="admin_dashboard_page")
@monitoring_load_guard
def admin_user_monitoring_page(request):
    """Monitor real authentication activity across admin and mobile accounts."""
    from .support_scope import is_marketplace_admin, support_activity
    scoped_monitor = is_marketplace_admin(request.user)
    if not _is_super_admin(request.user) and not scoped_monitor:
        raise PermissionDenied

    from datetime import datetime, time, timedelta
    from .monitoring import display_role, event_rows, presence_age, recent_per_account, timestamp, tracked_sessions
    from .activity_service import action_label, connection_summary

    now = timezone.now()
    local_today = timezone.localdate(now)
    monitoring_period = (request.GET.get("period") or "last7").strip().lower()
    if monitoring_period not in {"today", "last7", "last30", "custom"}:
        monitoring_period = "last7"
    requested_from = parse_date(request.GET.get("date_from", ""))
    requested_to = parse_date(request.GET.get("date_to", ""))
    if monitoring_period == "today":
        date_from = date_to = local_today
    elif monitoring_period == "last30":
        date_from, date_to = local_today - timedelta(days=29), local_today
    elif monitoring_period == "custom":
        date_from = requested_from or (local_today - timedelta(days=6))
        date_to = requested_to or local_today
    else:
        date_from, date_to = local_today - timedelta(days=6), local_today
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    if (date_to - date_from).days > 366:
        date_from = date_to - timedelta(days=366)
    current_tz = timezone.get_current_timezone()
    range_start = timezone.make_aware(datetime.combine(date_from, time.min), current_tz)
    range_end = timezone.make_aware(datetime.combine(date_to + timedelta(days=1), time.min), current_tz)
    online_cutoff = now - timedelta(minutes=5)

    all_rows = build_account_rows(request.user)
    selected_account_ref = (request.GET.get("account_ref") or "").strip()
    if selected_account_ref and not any(row["ref"] == selected_account_ref for row in all_rows):
        from django.http import Http404
        raise Http404("Account not found.")
    account_refs = [row["ref"] for row in all_rows]
    activity_source = support_activity(AccountActivity.objects.all(), request.user)
    latest_events = activity_source.filter(account_ref__in=account_refs).order_by(
        "account_ref", "-created_at", "-pk"
    ).distinct("account_ref")
    latest_event_by_ref = {event.account_ref: event for event in latest_events}

    enabled_refs = {row["ref"] for row in all_rows if row["is_active"] and not row["is_suspended"]}
    valid_sessions = tracked_sessions(now, [row["id"] for row in all_rows if row["source"] == "admin"])
    seen_by_ref = {}
    for session in valid_sessions.order_by("user_id", "-last_seen_at").distinct("user_id"):
        seen_by_ref[f"admin:{session.user_id}"] = session.last_seen_at
    # Mobile currently has login audit events, not a heartbeat/session registry.
    # A latest logout invalidates that recent-login presence estimate.
    mobile_presence = AccountActivity.objects.filter(
        account_source=AccountActivity.SOURCE_MOBILE, account_ref__in=enabled_refs,
        activity_type__in=["login_success", "logout"], result=AccountActivity.RESULT_SUCCESS,
        created_at__gte=online_cutoff, created_at__lte=now,
    ).order_by("account_ref", "-created_at", "-pk").distinct("account_ref")
    for event in mobile_presence:
        if event.activity_type == "login_success":
            seen_by_ref[event.account_ref] = event.created_at
    online_refs = {ref for ref, seen in seen_by_ref.items() if ref in enabled_refs and seen >= online_cutoff}
    latest_logins = activity_source.filter(
        account_ref__in=account_refs, activity_type="login_success", result=AccountActivity.RESULT_SUCCESS,
        created_at__lte=now,
    ).order_by("account_ref", "-created_at", "-pk").distinct("account_ref")
    login_by_ref = {event.account_ref: event.created_at for event in latest_logins}
    for row in all_rows:
        event = latest_event_by_ref.get(str(row["ref"]))
        row["role_label"] = display_role(row["role"])
        row["monitor_status"] = "online" if row["ref"] in online_refs else "offline"
        row["monitor_status_label"] = row["monitor_status"].title()
        row["last_activity"] = action_label(event) if event else ""
        row["last_activity_at"] = event.created_at if event else None
        row["last_seen"] = seen_by_ref.get(row["ref"])
        row["online_activity"] = presence_age(row["last_seen"], now)
        stored_login = row.get("last_login")
        audit_login = login_by_ref.get(row["ref"])
        row["last_login"] = max(filter(None, (stored_login, audit_login)), default=None)
    online_users = sorted(
        (row for row in all_rows if row["ref"] in online_refs),
        key=lambda row: row["last_seen"], reverse=True,
    )[:5]

    events_in_range = activity_source.filter(
        created_at__gte=range_start,
        created_at__lt=range_end,
    )
    if selected_account_ref:
        events_in_range = events_in_range.filter(account_ref=selected_account_ref)
    query = (request.GET.get("q") or "").strip().lower()
    account_type = (request.GET.get("type") or "").strip().lower()
    role = (request.GET.get("role") or "").strip().lower()
    status = (request.GET.get("status") or "").strip().lower()
    activity_type = (request.GET.get("activity") or "").strip().lower()
    activity_refs = None
    if activity_type:
        activity_refs = set(
            events_in_range.filter(activity_type=activity_type)
            .exclude(account_ref="")
            .values_list("account_ref", flat=True)
        )

    def row_matches(row):
        searchable = " ".join(
            f"{row.get(key) or ''}"
            for key in ("full_name", "username", "email", "role_label", "account_type_label")
        ).lower()
        return (
            (not selected_account_ref or row["ref"] == selected_account_ref)
            and (not query or query in searchable)
            and (not account_type or row["account_type"] == account_type)
            and (not role or row["role_label"].lower() == display_role(role).lower())
            and (not status or row["monitor_status"] == status)
            and (activity_refs is None or row["ref"] in activity_refs)
        )

    filtered_rows = [row for row in all_rows if row_matches(row)]
    filtered_rows.sort(
        key=lambda row: row["last_activity_at"] or row["last_login"] or row["date_joined"],
        reverse=True,
    )
    page_size = 10
    paginator = Paginator(filtered_rows, page_size)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    page_refs = [row["ref"] for row in page_obj.object_list]
    drawer_events = {ref: [] for ref in page_refs}
    history_page_obj = None
    event_query = activity_source.filter(account_ref__in=page_refs).exclude(activity="").order_by("-created_at", "-pk")
    if selected_account_ref and selected_account_ref in page_refs:
        # The deep link opens complete all-time history, twenty actual events per page.
        history_page_obj = Paginator(event_query, 20).get_page(request.GET.get("history_page"))
        event_query = history_page_obj.object_list
    if not history_page_obj:
        event_query = recent_per_account(event_query)
    login_history = recent_per_account(activity_source.filter(
        account_ref__in=page_refs, activity_type__in=["login_success", "login_failed"],
    )) if not scoped_monitor else []
    logins_by_ref = {ref: [] for ref in page_refs}
    for event in login_history:
        logins_by_ref[event.account_ref].append({
            "time": timestamp(event.created_at), "activity": event.activity,
            "type": event.activity_type, "module": event.module,
            "result": event.get_result_display(), "ip": event.ip_address or "",
        })
    for event in event_query:
        if len(drawer_events[event.account_ref]) < 20:
            drawer_events[event.account_ref].append({
                "time": timezone.localtime(event.created_at).strftime("%b %d, %Y %I:%M %p"),
                "activity": event.activity,
                "type": event.activity_type,
                "module": event.module,
                "result": event.get_result_display(),
                "ip": "" if scoped_monitor else event.ip_address or "",
                "device": "" if scoped_monitor else connection_summary(event.user_agent),
            })
    session_map = {ref: [] for ref in page_refs}
    page_admin_ids = [row["id"] for row in page_obj.object_list if row["source"] == "admin"]
    for session in recent_per_account(valid_sessions.filter(user_id__in=[] if scoped_monitor else page_admin_ids), limit=10, partition="user_id"):
        ref = f"admin:{session.user_id}"
        if len(session_map[ref]) < 10:
            session_map[ref].append({
                "created": timestamp(session.created_at), "last_seen": timestamp(session.last_seen_at),
                "expires": timestamp(session.expires_at), "active": True,
            })

    users_json = []
    for row in page_obj.object_list:
        events = drawer_events[row["ref"]]
        latest = latest_event_by_ref.get(row["ref"])
        users_json.append({
            "ref": row["ref"],
            "initials": row["initials"],
            "fullName": row["full_name"],
            "username": row["username"],
            "email": row["email"],
            "accountType": row["account_type_label"],
            "role": row["role_label"],
            "status": row["monitor_status_label"],
            "accountStatus": row["status_label"],
            "lastSeen": timestamp(row["last_seen"]),
            "presenceNote": "Mobile presence uses recent successful login; no mobile heartbeat is recorded." if row["source"] == "mobile" else "",
            "sessionNote": "Mobile session mapping is not recorded." if row["source"] == "mobile" else "Only recently used authenticated admin tab sessions are tracked.",
            "logins": logins_by_ref[row["ref"]],
            "lastLogin": timezone.localtime(row["last_login"]).strftime("%b %d, %Y %I:%M %p") if isinstance(row.get("last_login"), datetime) else "",
            "lastActivity": row["last_activity"],
            "lastActivityAt": timezone.localtime(row["last_activity_at"]).strftime("%b %d, %Y %I:%M %p") if isinstance(row.get("last_activity_at"), datetime) else "",
            "ip": (latest.ip_address or "") if latest and not scoped_monitor else "",
            "device": connection_summary(latest.user_agent) if latest and not scoped_monitor else "",
            "events": events,
            "sessions": session_map[row["ref"]],
        })

    successful_logins = events_in_range if scoped_monitor else events_in_range.filter(
        activity_type="login_success",
        result=AccountActivity.RESULT_SUCCESS,
    )

    def grouped_login_counts(trunc_expression):
        grouped = (
            successful_logins
            .annotate(bucket=trunc_expression("created_at", tzinfo=current_tz))
            .values("bucket")
            .annotate(total=Count("id"))
            .order_by("bucket")
        )
        return {
            timezone.localtime(item["bucket"], current_tz).date(): item["total"]
            for item in grouped
        }

    def short_date_label(value):
        return f"{value.strftime('%b')} {value.day}"

    def full_date_label(value):
        return f"{value.strftime('%b')} {value.day}, {value.year}"

    def week_label(week_start, include_year=False):
        week_end = week_start + timedelta(days=6)
        separator = "\u2013"
        if week_start.year != week_end.year:
            return (
                f"{short_date_label(week_start)}, {week_start.year}{separator}"
                f"{short_date_label(week_end)}, {week_end.year}"
            )
        if week_start.month == week_end.month:
            label = f"{short_date_label(week_start)}{separator}{week_end.day}"
        else:
            label = f"{short_date_label(week_start)}{separator}{short_date_label(week_end)}"
        return f"{label}, {week_start.year}" if include_year else label

    def complete_series(bucket_dates, counts, label_builder, tooltip_builder):
        return {
            "labels": [label_builder(bucket) for bucket in bucket_dates],
            "tooltipLabels": [tooltip_builder(bucket) for bucket in bucket_dates],
            "success": [counts.get(bucket, 0) for bucket in bucket_dates],
        }

    daily_buckets = [
        date_from + timedelta(days=offset)
        for offset in range((date_to - date_from).days + 1)
    ]

    first_week = date_from - timedelta(days=date_from.weekday())
    last_week = date_to - timedelta(days=date_to.weekday())
    weekly_buckets = []
    current_week = first_week
    while current_week <= last_week:
        weekly_buckets.append(current_week)
        current_week += timedelta(days=7)

    monthly_buckets = []
    current_month = date_from.replace(day=1)
    last_month = date_to.replace(day=1)
    while current_month <= last_month:
        monthly_buckets.append(current_month)
        if current_month.month == 12:
            current_month = current_month.replace(
                year=current_month.year + 1,
                month=1,
            )
        else:
            current_month = current_month.replace(month=current_month.month + 1)

    login_trend_data = {
        "daily": complete_series(
            daily_buckets,
            grouped_login_counts(TruncDay),
            short_date_label,
            full_date_label,
        ),
        "weekly": complete_series(
            weekly_buckets,
            grouped_login_counts(TruncWeek),
            week_label,
            lambda bucket: week_label(bucket, include_year=True),
        ),
        "monthly": complete_series(
            monthly_buckets,
            grouped_login_counts(TruncMonth),
            lambda bucket: bucket.strftime("%b %Y"),
            lambda bucket: bucket.strftime("%B %Y"),
        ),
    }

    online_refs.intersection_update(account_refs)
    online_total = len(online_refs)

    hourly_login_counts = [0] * 24
    for bucket in successful_logins.annotate(hour=ExtractHour("created_at", tzinfo=current_tz)).values("hour").annotate(total=Count("pk")).order_by("hour"):
        hourly_login_counts[bucket["hour"]] = bucket["total"]
    def hour_label(hour):
        return datetime.combine(local_today, time(hour=hour)).strftime("%I %p").lstrip("0")

    # Keep chart totals tied to the period; table filters only narrow the log.
    filtered_events = events_in_range
    if query or account_type or role or status or activity_type:
        matching_refs = [row["ref"] for row in filtered_rows]
        filtered_events = filtered_events.filter(account_ref__in=matching_refs)
        if query and not (account_type or role or status):
            # Failed attempts for unknown identifiers do not have an account_ref.
            filtered_events = events_in_range.filter(
                Q(account_ref__in=matching_refs) | Q(username__icontains=query)
            )
        if activity_type:
            filtered_events = filtered_events.filter(activity_type=activity_type)
    activity_module_filter = "Facilities" if (request.GET.get("module") or "").strip().casefold() == "facilities" else ""
    if activity_module_filter:
        filtered_events = filtered_events.filter(module__iexact=activity_module_filter)
    activity_page_obj = Paginator(filtered_events.order_by("-created_at", "-pk"), 20).get_page(request.GET.get("activity_page"))
    recent_activities = event_rows(activity_page_obj.object_list, scoped=scoped_monitor)
    activity_query = request.GET.copy()
    activity_query.pop("activity_page", None)
    query_without_page = request.GET.copy()
    query_without_page.pop("page", None)
    history_query = request.GET.copy()
    history_query.pop("history_page", None)
    role_choices = sorted({display_role(row["role"]) for row in all_rows if row.get("role")}, key=str.casefold)
    active_sessions = valid_sessions.count() if not scoped_monitor else None
    monitor_chart_data = {
        **login_trend_data,
        "peakHours": {
            "labels": [hour_label(hour) for hour in range(24)],
            "values": hourly_login_counts,
        },
    }

    return render(request, "user_management/pages/admin_user_monitoring.html", {
        "scoped_monitor": scoped_monitor,
        "marketplace_activity_count": events_in_range.count(),
        "accounts_with_activity": events_in_range.values("account_ref").distinct().count(),
        "users": page_obj.object_list,
        "users_json": users_json,
        "page_obj": page_obj,
        "paginator": paginator,
        "page_size": page_size,
        "query_without_page": query_without_page.urlencode(),
        "total_active_users": sum(1 for row in all_rows if row["is_active"] and not row["is_suspended"]),
        "online_now": online_total,
        "failed_login_attempts": events_in_range.filter(activity_type="login_failed", result=AccountActivity.RESULT_FAILED).count(),
        "active_sessions": active_sessions,
        "online_users": online_users,
        "monitor_chart_data": monitor_chart_data,
        "recent_activities": recent_activities,
        "activity_page_obj": activity_page_obj,
        "activity_module_filter": activity_module_filter,
        "activity_query": activity_query.urlencode(),
        "monitor_config": {"scoped": scoped_monitor, "selectedAccount": selected_account_ref},
        "session_coverage": "Tracked admin tab sessions only; mobile sessions are not recorded.",
        "presence_coverage": "Admin presence uses last seen. Mobile presence uses recent successful login.",
        "selected_account_ref": selected_account_ref,
        "history_page_obj": history_page_obj,
        "history_query": history_query.urlencode(),
        "account_types": ACCOUNT_TYPES,
        "role_choices": role_choices,
        "activity_types": [(kind, kind.replace("_", " ").title()) for kind in sorted(set(activity_source.values_list("activity_type", flat=True)))],
        "filters": {
            "q": request.GET.get("q", ""),
            "type": account_type,
            "role": request.GET.get("role", ""),
            "status": status,
            "activity": activity_type,
            "account_ref": selected_account_ref,
            "period": monitoring_period,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
        **get_notification_context(user=request.user),
    })


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_settings", login_url="admin_dashboard_page")
def admin_settings_page(request):
    """System settings page."""
    return render(
        request,
        "user_management/pages/admin_settings.html",
        get_notification_context(user=request.user),
    )


@login_required(login_url="admin_login_page")
def admin_marketplace_export_page(request):
    """Show the marketplace-only structured data export page."""
    if not _is_super_admin(request.user) or not request.user.has_perm("accounts.can_export_marketplace_data"):
        raise PermissionDenied

    from .export_service import EXPORT_FORMAT, export_record_counts

    return render(
        request,
        "user_management/pages/admin_data_export.html",
        {
            "export_scope": "marketplace",
            "page_title": "Marketplace Data Export",
            "subtitle": "Create a downloadable copy of authorized marketplace records.",
            "scope_label": "Marketplace records",
            "export_format": EXPORT_FORMAT,
            "record_counts": export_record_counts("marketplace", request.user),
            "download_url": reverse("admin_marketplace_export_download"),
            **get_notification_context(user=request.user),
        },
    )


@login_required(login_url="admin_login_page")
def admin_facility_export_page(request):
    """Show the facilities-only structured data export page."""
    if not _is_super_admin(request.user) or not request.user.has_perm("accounts.can_export_facility_data"):
        raise PermissionDenied

    from .export_service import EXPORT_FORMAT, export_record_counts

    return render(
        request,
        "user_management/pages/admin_data_export.html",
        {
            "export_scope": "facilities",
            "page_title": "Facility Data Export",
            "subtitle": "Create a downloadable copy of authorized facility records.",
            "scope_label": "Facility records",
            "export_format": EXPORT_FORMAT,
            "record_counts": export_record_counts("facilities", request.user),
            "download_url": reverse("admin_facility_export_download"),
            **get_notification_context(user=request.user),
        },
    )


def _export_date_range(request):
    start_raw = request.POST.get("date_from", "").strip()
    end_raw = request.POST.get("date_to", "").strip()
    start_date = parse_date(start_raw) if start_raw else None
    end_date = parse_date(end_raw) if end_raw else None
    if start_raw and start_date is None:
        raise ValidationError("Enter a valid start date.")
    if end_raw and end_date is None:
        raise ValidationError("Enter a valid end date.")
    if start_date and end_date and start_date > end_date:
        raise ValidationError("The start date cannot be after the end date.")
    return start_date, end_date


def _record_export_activity(request, scope, result):
    label = "marketplace" if scope == "marketplace" else "facility"
    log_account_activity(
        request,
        source=AccountActivity.SOURCE_ADMIN,
        activity_type="data_export",
        activity=f"Created {label} data export",
        result=result,
        account=request.user,
        module="Data Export",
    )


def _download_scoped_export(request, scope, permission_codename, page_name):
    if not _is_super_admin(request.user) or not request.user.has_perm(f"accounts.{permission_codename}"):
        raise PermissionDenied
    try:
        start_date, end_date = _export_date_range(request)
        from .export_service import build_scoped_export

        filename, content = build_scoped_export(
            scope,
            user=request.user,
            start_date=start_date,
            end_date=end_date,
        )
        _record_export_activity(request, scope, AccountActivity.RESULT_SUCCESS)
    except ValidationError as exc:
        _record_export_activity(request, scope, AccountActivity.RESULT_FAILED)
        messages.error(request, " ".join(exc.messages))
        return redirect(page_name)
    except Exception:
        _record_export_activity(request, scope, AccountActivity.RESULT_FAILED)
        messages.error(request, "The export could not be created. Try again or contact the system administrator.")
        return redirect(page_name)

    response = HttpResponse(content, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Content-Length"] = len(content)
    return response


@login_required(login_url="admin_login_page")
@require_POST
def admin_marketplace_export_download(request):
    return _download_scoped_export(
        request,
        "marketplace",
        "can_export_marketplace_data",
        "admin_marketplace_export_page",
    )


@login_required(login_url="admin_login_page")
@require_POST
def admin_facility_export_download(request):
    return _download_scoped_export(
        request,
        "facilities",
        "can_export_facility_data",
        "admin_facility_export_page",
    )


@login_required(login_url="admin_login_page")
def admin_backup_page(request):
    """Backup & Restore page."""
    if not _is_super_admin(request.user) or not request.user.has_perm(
        "accounts.can_system_backup"
    ):
        raise PermissionDenied

    from accounts.backup_service import (
        get_backup_list, get_backup_stats, create_backup, delete_backup,
        get_latest_backup, restore_from_upload, get_auto_backup_config,
        save_auto_backup_config, BACKUP_DIR,
    )
    from django.http import FileResponse

    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "create_backup":
            backup_type = request.POST.get("backup_type", "full")
            result = create_backup(backup_type)
            if result["success"]:
                log_account_activity(
                    request,
                    source=AccountActivity.SOURCE_ADMIN,
                    activity_type="system_backup",
                    activity=f'Created system backup {result["filename"]}',
                    result=AccountActivity.RESULT_SUCCESS,
                    account=request.user,
                    module="Backup & Restore",
                )
                messages.success(request, f'Backup created: {result["filename"]} ({result["size_display"]})')
            else:
                log_account_activity(
                    request,
                    source=AccountActivity.SOURCE_ADMIN,
                    activity_type="system_backup",
                    activity="System backup creation failed",
                    result=AccountActivity.RESULT_FAILED,
                    account=request.user,
                    module="Backup & Restore",
                )
                messages.error(request, f'Backup failed: {result["error"]}')
            return redirect("admin_backup_page")

        elif action == "delete_backup":
            filename = request.POST.get("filename", "")
            if delete_backup(filename):
                messages.success(request, f'Backup "{filename}" deleted.')
            else:
                messages.error(request, "Backup file not found.")
            return redirect("admin_backup_page")

        elif action == "download_backup":
            filename = request.POST.get("filename", "")
            filepath = (BACKUP_DIR / filename).resolve()
            if (
                filename == filepath.name
                and filepath.parent == BACKUP_DIR.resolve()
                and filepath.suffix.lower() == ".sql"
                and filepath.exists()
            ):
                return FileResponse(open(filepath, "rb"), as_attachment=True, filename=filename)
            messages.error(request, "Backup file not found.")
            return redirect("admin_backup_page")

        elif action == "download_latest":
            latest = get_latest_backup()
            if latest:
                filepath = BACKUP_DIR / latest["filename"]
                if filepath.exists():
                    return FileResponse(open(filepath, "rb"), as_attachment=True, filename=latest["filename"])
            messages.error(request, "No successful backup available to download.")
            return redirect("admin_backup_page")

        elif action == "restore_upload":
            if not request.user.has_perm("accounts.can_restore_system_backup"):
                raise PermissionDenied
            uploaded_file = request.FILES.get("backup_file")
            if not uploaded_file:
                log_account_activity(
                    request,
                    source=AccountActivity.SOURCE_ADMIN,
                    activity_type="system_restore",
                    activity="System restore failed: no backup file provided",
                    result=AccountActivity.RESULT_FAILED,
                    account=request.user,
                    module="Backup & Restore",
                )
                messages.error(request, "No file uploaded.")
            else:
                result = restore_from_upload(uploaded_file)
                if result["success"]:
                    log_account_activity(
                        request,
                        source=AccountActivity.SOURCE_ADMIN,
                        activity_type="system_restore",
                        activity=f"Restored system backup {uploaded_file.name}",
                        result=AccountActivity.RESULT_SUCCESS,
                        account=request.user,
                        module="Backup & Restore",
                    )
                    messages.success(request, str(result.get("message") or "System restored successfully."))
                else:
                    log_account_activity(
                        request,
                        source=AccountActivity.SOURCE_ADMIN,
                        activity_type="system_restore",
                        activity=f"System restore failed for {uploaded_file.name}",
                        result=AccountActivity.RESULT_FAILED,
                        account=request.user,
                        module="Backup & Restore",
                    )
                    messages.error(request, f'Restore failed: {result["error"]}')
            return redirect("admin_backup_page")

        elif action == "save_auto_backup":
            enabled = request.POST.get("auto_enabled") == "on"
            frequency = request.POST.get("frequency", "daily")
            save_auto_backup_config(enabled, frequency)
            messages.success(request, f'Auto backup settings saved: {"Enabled" if enabled else "Disabled"} ({frequency})')
            return redirect("admin_backup_page")

    stats = get_backup_stats()
    backups = get_backup_list()
    latest = get_latest_backup()
    auto_config = get_auto_backup_config()

    return render(
        request,
        "user_management/pages/admin_backup.html",
        {
            "stats": stats,
            "backups": backups,
            "latest_backup": latest,
            "auto_config": auto_config,
            **get_notification_context(user=request.user),
        },
    )
