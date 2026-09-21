from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
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
    get_product_inventory_status,
    low_stock_threshold,
)
from accounts.admin_tab_auth import get_tab_token_from_request, revoke_admin_tab_token
from accounts.activity_logging import log_account_activity
from accounts.models import AccountActivity, AdminTabToken, Role, User
from accounts.role_permissions import (
    ADMIN_PERMISSION_CODENAMES,
    PERMISSION_MODULES,
    get_admin_home_url,
    permission_labels_for_role,
    permission_set_label_for_role,
    set_role_permissions,
    sync_user_admin_permissions,
    sync_users_for_role,
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

PROTECTED_ADMIN_ROLES = frozenset({"Super Admin", "Marketplace Admin", "Facilities Admin", "User"})
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
            or request.user.has_perm("accounts.can_approve_products")
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


def get_notification_context(limit=5):
    seller_requests = SellerRequest.objects.select_related("user", "reviewed_by").filter(
        status=SellerRequest.STATUS_PENDING
    )[:limit]
    pending_seller_requests = SellerRequest.objects.filter(
        status=SellerRequest.STATUS_PENDING
    ).count()
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

    all_products = admin_product_queryset(request.user)
    active_products = all_products.filter(is_archived=False)
    departments = Department.objects.all().order_by("name")

    from accounts.models import User
    approved_sellers = User.objects.filter(
        Q(role__iexact="Seller") | Q(seller_access_requests__status="approved")
    ).distinct().order_by("first_name", "last_name")
    seller_products = list(
        all_products.select_related(
            "seller", "seller__department", "approved_by"
        ).order_by("-submitted_at")
    )
    today = timezone.localdate()
    for product in seller_products:
        product.admin_total_stock = max(0, product.get_total_stock() or 0)
        product.admin_variant_count = (
            count_customization_options(product.customization_options)
            if product.customization_enabled
            else 0
        )
        product.admin_inventory_status = get_product_inventory_status(product, today=today)
    low_stock_count = sum(
        1
        for product in active_products
        if get_product_inventory_status(product, today=today) == INVENTORY_STATUS_LOW_STOCK
    )
    product_stats = {
        "total": active_products.count(),
        "pending": active_products.filter(approval_status=Product.STATUS_PENDING).count(),
        "approved": active_products.filter(approval_status=Product.STATUS_APPROVED).count(),
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
            "approved_sellers": approved_sellers,
            "can_manage_products": user_can_manage_products(request.user),
            "can_approve_products": request.user.has_perm(
                "accounts.can_approve_products"
            ),
            "can_add_products": request.user.is_superuser or _is_marketplace_admin(request.user),
            **get_notification_context(),
        },
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_sellers", raise_exception=True)
def admin_sellers_page(request):
    """Review existing seller-access requests without duplicating user records."""
    search_query = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip().lower()
    seller_requests = SellerRequest.objects.select_related(
        "user", "user__department", "reviewed_by"
    ).order_by("-created_at")

    if search_query:
        seller_requests = seller_requests.filter(
            Q(full_name__icontains=search_query)
            | Q(student_id__icontains=search_query)
            | Q(product_type__icontains=search_query)
            | Q(user__email__icontains=search_query)
        )
    valid_statuses = {
        SellerRequest.STATUS_PENDING,
        SellerRequest.STATUS_APPROVED,
        SellerRequest.STATUS_REJECTED,
    }
    if status_filter in valid_statuses:
        seller_requests = seller_requests.filter(status=status_filter)

    paginator = Paginator(seller_requests, 10)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    query_without_page = request.GET.copy()
    query_without_page.pop("page", None)
    status_counts = {
        "total": SellerRequest.objects.count(),
        "pending": SellerRequest.objects.filter(status=SellerRequest.STATUS_PENDING).count(),
        "approved": SellerRequest.objects.filter(status=SellerRequest.STATUS_APPROVED).count(),
        "rejected": SellerRequest.objects.filter(status=SellerRequest.STATUS_REJECTED).count(),
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
            **get_notification_context(),
        },
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_access_notifications", login_url="admin_dashboard_page")
def admin_notifications_page(request):
    return render(
        request,
        "notifications/pages/admin_notifications.html",
        get_notification_context(limit=100),
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_access_messages", login_url="admin_dashboard_page")
def admin_messages_page(request):
    return render(
        request,
        "messages/pages/admin_messages.html",
        get_notification_context(),
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_orders", raise_exception=True)
def admin_orders_page(request):
    from api.models import CampusHubUser

    orders_queryset = (
        admin_order_queryset(request.user)
        .select_related("product", "product__seller", "product__seller__department")
        .prefetch_related("status_history")
    )

    orders = list(orders_queryset)
    buyer_ids = [order.buyer_user_id for order in orders if order.buyer_user_id]
    django_users = {
        user.id: user
        for user in User.objects.filter(id__in=buyer_ids).only(
            "id", "role", "first_name", "last_name", "username", "email", "contact_number"
        )
    }
    campus_users = {
        user.id: user
        for user in CampusHubUser.objects.filter(id__in=buyer_ids).only(
            "id", "first_name", "last_name", "username", "email", "contact_number"
        )
    }

    for order in orders:
        if not order.order_code or len(order.order_code) != 12 or not order.order_code.startswith("2026"):
            order.ensure_order_code(force=True)
            order.save(update_fields=["order_code"])

        django_user = django_users.get(order.buyer_user_id) if order.buyer_user_id else None
        campus_user = campus_users.get(order.buyer_user_id) if order.buyer_user_id else None

        name = (order.buyer_name or "").strip()
        if not name and campus_user:
            name = (
                f"{campus_user.first_name} {campus_user.last_name}".strip()
                or campus_user.username
            )
        if not name and django_user:
            name = django_user.get_full_name().strip() or django_user.username
        order.display_buyer_name = name or "Unknown customer"

        email = (order.buyer_email or "").strip()
        if not email and campus_user:
            email = getattr(campus_user, "email", "") or ""
        if not email and django_user:
            email = getattr(django_user, "email", "") or ""
        order.display_buyer_email = email

        phone = ""
        if django_user and getattr(django_user, "contact_number", None):
            phone = django_user.contact_number
        elif campus_user and getattr(campus_user, "contact_number", None):
            phone = campus_user.contact_number
        order.display_buyer_phone = phone

        if django_user:
            order.buyer_user_type = (django_user.role or "User").strip() or "User"
        elif campus_user:
            order.buyer_user_type = "Student"
        else:
            order.buyer_user_type = ""

        # Multi-item and total quantity handling
        customization = order.customization or {}
        items_list = customization.get("items")
        if isinstance(items_list, list) and len(items_list) > 0:
            first_name = items_list[0].get("product_name") or order.product_name
            extra_count = len(items_list) - 1
            if extra_count > 0:
                order.display_items = f"{first_name} + {extra_count} more"
            else:
                order.display_items = first_name
            order.display_qty = sum(int(it.get("quantity", 1) or 1) for it in items_list)
            order.items_json = json.dumps(items_list)
        else:
            order.display_items = order.product_name
            order.display_qty = order.quantity
            order.items_json = json.dumps([{
                "product_name": order.product_name,
                "variant": order.option or "Standard",
                "quantity": order.quantity,
                "unit_price": str(order.unit_price),
                "subtotal": str(order.total_price),
            }])

        order.status_history_json = json.dumps(
            [
                {
                    "previous_status": item.previous_status,
                    "new_status": item.new_status,
                    "new_status_label": dict(MarketplaceOrder.STATUS_CHOICES).get(
                        item.new_status, item.new_status.replace("_", " ").title()
                    ),
                    "changed_by": item.changed_by or "System",
                    "notes": item.notes,
                    "created_at": timezone.localtime(item.created_at).strftime(
                        "%b %d, %Y at %I:%M %p"
                    ),
                }
                for item in order.status_history.all()
            ]
        )

    order_stats = {
        "total": len(orders),
        "completed": sum(1 for o in orders if o.status == MarketplaceOrder.STATUS_COMPLETED),
        "pending": sum(1 for o in orders if o.status == MarketplaceOrder.STATUS_PENDING),
        "processing": sum(1 for o in orders if o.status == MarketplaceOrder.STATUS_PROCESSING),
        "ready_for_pickup": sum(
            1 for o in orders if o.status == MarketplaceOrder.STATUS_READY_FOR_PICKUP
        ),
        "cancelled": sum(1 for o in orders if o.status == MarketplaceOrder.STATUS_CANCELLED),
    }

    return render(
        request,
        "marketplace/pages/admin_orders.html",
        {
            "orders": orders,
            "order_stats": order_stats,
            **get_notification_context(),
        },
    )


@permissions_required_any("can_view_users", "can_manage_admin_accounts")
def admin_users_page(request):
    return render(
        request,
        "user_management/pages/admin_user_access_control.html",
        {
            **get_user_management_context(request),
            **get_notification_context(),
        },
    )


def _active_super_admin_count():
    return User.objects.filter(is_active=True, is_suspended=False).filter(
        Q(is_superuser=True) | Q(role__iexact="Super Admin")
    ).count()


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
def admin_users_save(request):
    """Create or update an account without changing its owning account store."""
    if request.method != "POST":
        return redirect("admin_users_page")

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
            "Add User can create only Super Admin, Marketplace Admin, or Facilities Admin accounts.",
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

    department = None
    if department_id:
        department = Department.objects.filter(pk=department_id).first()
        if department is None:
            messages.error(request, "Choose a valid department.")
            return redirect("admin_users_page")
    if role.lower() == "marketplace admin" and department is None:
        messages.error(request, "Marketplace Admin requires a department.")
        return redirect("admin_users_page")

    source, existing_user = resolve_account(account_reference) if account_reference else (None, None)
    if account_reference and existing_user is None:
        messages.error(request, "User not found.")
        return redirect("admin_users_page")
    expected_source = "admin" if account_type == "admin" else "mobile"
    if existing_user and source != expected_source:
        messages.error(request, "Account type cannot be changed between mobile and admin storage.")
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
        and (not is_active or role.lower() != "super admin")
        and _active_super_admin_count() <= 1
    ):
        messages.error(request, "The final active Super Admin cannot be deactivated or demoted.")
        return redirect("admin_users_page")

    with transaction.atomic():
        if source == "admin":
            user = existing_user
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.contact_number = contact_number
            user.role = role
            user.department = department
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
            user.contact_number = contact_number
            user.user_type = account_type
            user.role = role
            user.department = department
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
                is_active=is_active,
                profile_completed=bool(contact_number),
            )

    messages.success(request, f'User "{username}" {"updated" if existing_user else "created"}.')
    return redirect("admin_users_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_admin_accounts", login_url="admin_dashboard_page")
def admin_users_action(request):
    if request.method != "POST":
        return redirect("admin_users_page")

    source, account = resolve_account(request.POST.get("account_ref", "").strip())
    action = request.POST.get("action", "").strip().lower()
    if account is None:
        messages.error(request, "User not found.")
        return redirect("admin_users_page")

    protected_change = action in {"deactivate", "suspend"}
    if source == "admin" and account == request.user and protected_change:
        messages.error(request, "You cannot deactivate or suspend your own account.")
        return redirect("admin_users_page")
    if protected_change and _is_super_admin(account) and _active_super_admin_count() <= 1:
        messages.error(request, "The final active Super Admin cannot be deactivated or suspended.")
        return redirect("admin_users_page")

    if action in {"activate", "deactivate", "suspend"}:
        account.is_active = action == "activate"
        account.is_suspended = action == "suspend"
        account.save(update_fields=["is_active", "is_suspended"])
        state = {"activate": "activated", "deactivate": "deactivated", "suspend": "suspended"}[action]
        messages.success(request, f'Account "{account.username}" was {state}.')
    elif action == "reset_password":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        errors = strict_password_errors(password)
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if errors:
            messages.error(request, " ".join(errors))
            return redirect("admin_users_page")
        if source == "admin":
            account.set_password(password)
            account.save(update_fields=["password"])
        else:
            account.password_hash = make_password(password)
            account.save(update_fields=["password_hash"])
        messages.success(request, f'Password reset for "{account.username}".')
    elif action == "seller_access":
        if source == "admin":
            messages.error(request, "Seller access does not apply to administrator accounts.")
            return redirect("admin_users_page")
        seller_status = request.POST.get("seller_status", "").strip().lower()
        valid_statuses = {
            SellerRequest.STATUS_PENDING,
            SellerRequest.STATUS_APPROVED,
            SellerRequest.STATUS_REJECTED,
        }
        if seller_status not in valid_statuses:
            messages.error(request, "Choose a valid seller access status.")
            return redirect("admin_users_page")
        seller_request = seller_request_for(source, account)
        if seller_request is None:
            seller_request = SellerRequest(
                user=account if source == "admin" else None,
                student_id=getattr(account, "student_id", "") or account.username,
                full_name=(
                    account.get_full_name().strip()
                    if source == "admin"
                    else f"{account.first_name} {account.last_name}".strip()
                ) or account.username,
                contact_number=getattr(account, "contact_number", ""),
                product_type="Campus marketplace products",
            )
        seller_request.status = seller_status
        seller_request.reviewed_by = request.user
        seller_request.reviewed_at = timezone.now()
        seller_request.rejection_reason = (
            "Suspended by Super Admin" if seller_status == SellerRequest.STATUS_REJECTED else ""
        )
        seller_request.save()
        messages.success(request, f'Seller access updated for "{account.username}".')
    else:
        messages.error(request, "Unsupported user action.")

    return redirect("admin_users_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_admin_accounts", login_url="admin_dashboard_page")
def admin_users_delete(request):
    """Compatibility endpoint for old forms; user records are not hard-deleted."""
    messages.error(request, "Permanent user deletion is disabled. Deactivate the account instead.")
    return redirect("admin_users_page")


@facility_module_required
def admin_facility_page(request):
    from api.models import Booking, Facility, Room
    from modules.facilities.services.operating_schedule import workflow_for_display
    from modules.facilities.services.facility_configuration import (
        BOOKING_MODE_LABELS,
        STATUS_CHOICES,
        facility_form_configuration,
    )

    facilities_qs = Facility.objects.all()
    facilities = list(facilities_qs)
    for facility in facilities:
        facility.form_workflow = workflow_for_display(facility)
    can_manage = user_can_manage_facilities(request.user)
    configured_units = sum(
        max(int(units or 0), 0)
        for units in facilities_qs.values_list("rooms_units", flat=True)
    )
    room_records = Room.objects.count()

    recent_activities = []
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
                    f"{facility.facility_name} facility details updated."
                    if was_updated
                    else f"{facility.facility_name} added."
                ),
                "description": "Facility update" if was_updated else "New facility",
                "occurred_at": occurred_at,
            }
        )

    booking_activity_labels = {
        "class": "class schedule recorded",
        "maintenance": "maintenance schedule recorded",
        "assessment": "assessment schedule recorded",
        "reservation": "reservation updated",
    }
    for booking in Booking.objects.select_related("facility", "user").order_by("-updated_at")[:8]:
        occurred_at = booking.updated_at or booking.created_at
        if not occurred_at:
            continue
        event_type, _, purpose = _booking_display_fields(booking)
        facility_name = booking.facility.facility_name if booking.facility_id else "Facility"
        recent_activities.append(
            {
                "kind": event_type,
                "title": f"{facility_name} {booking_activity_labels.get(event_type, 'booking updated')}.",
                "description": purpose or booking.get_status_display(),
                "occurred_at": occurred_at,
            }
        )

    recent_activities.sort(key=lambda item: item["occurred_at"], reverse=True)
    active_facilities_qs = facilities_qs.filter(is_archived=False)
    context = {
        "facilities": facilities,
        "facilities_total": active_facilities_qs.count(),
        "facilities_archived_total": facilities_qs.filter(is_archived=True).count(),
        "open_for_booking_count": active_facilities_qs.filter(
            availability_status=Facility.STATUS_AVAILABLE
        ).count(),
        "under_maintenance_count": active_facilities_qs.filter(
            availability_status=Facility.STATUS_MAINTENANCE
        ).count(),
        "rooms_units_total": max(configured_units, room_records),
        "facility_type_choices": Facility.TYPE_CHOICES,
        "booking_mode_choices": tuple(BOOKING_MODE_LABELS.items()),
        "facility_status_choices": STATUS_CHOICES,
        "facility_form_configuration": facility_form_configuration(),
        "calendar_events": _bookings_calendar_events(),
        "recent_facility_activities": recent_activities[:8],
        "can_manage_facilities": can_manage,
        "can_book_facilities": user_can_book_facilities(request.user),
        **get_notification_context(),
    }


    if can_manage:
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

    type_pattern = re.compile(r"^\[(class|reservation|maintenance|assessment)\]\s*", re.I)
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


def _bookings_calendar_events():
    """Build calendar events from real facility bookings only (no placeholders)."""
    from api.models import Booking

    events = []

    bookings = (
        Booking.objects.select_related("facility", "user")
        .filter(booking_date__isnull=False)
        .exclude(status__in=(Booking.STATUS_CANCELLED, Booking.STATUS_REJECTED))
        .order_by("booking_date", "start_time")[:300]
    )
    for booking in bookings:
        facility_name = booking.facility.facility_name if booking.facility_id else "Facility"
        event_type, reserved_by, purpose = _booking_display_fields(booking)
        events.append(
            {
                "id": booking.id,
                "type": event_type,
                "facility_id": booking.facility_id or "",
                "facility": facility_name,
                "date": booking.booking_date.isoformat(),
                "start": booking.start_time.strftime("%H:%M") if booking.start_time else "",
                "end": booking.end_time.strftime("%H:%M") if booking.end_time else "",
                "reserved_by": reserved_by,
                "purpose": purpose,
                "status": booking.status,
            }
        )

    return events


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_orders", raise_exception=True)
def admin_order_update(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)

    allowed_transitions = {
        MarketplaceOrder.STATUS_PENDING: {
            MarketplaceOrder.STATUS_PROCESSING,
            MarketplaceOrder.STATUS_CANCELLED,
        },
        MarketplaceOrder.STATUS_PROCESSING: {
            MarketplaceOrder.STATUS_READY_FOR_PICKUP,
            MarketplaceOrder.STATUS_CANCELLED,
        },
        MarketplaceOrder.STATUS_READY_FOR_PICKUP: {
            MarketplaceOrder.STATUS_COMPLETED,
            MarketplaceOrder.STATUS_CANCELLED,
        },
        MarketplaceOrder.STATUS_COMPLETED: set(),
        MarketplaceOrder.STATUS_CANCELLED: set(),
    }

    with transaction.atomic():
        order_query = admin_order_queryset(request.user).select_for_update()

        order = get_object_or_404(order_query, id=order_id)

        current_status = order.status
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

        payment_status = (
            payload.get("payment_status") or order.payment_status
        ).strip().lower()
        if payment_status not in {
            MarketplaceOrder.PAYMENT_UNPAID,
            MarketplaceOrder.PAYMENT_PAID,
        }:
            return JsonResponse({"error": "Invalid payment status."}, status=400)

        receipt_no = (payload.get("official_receipt_no") or "").strip()
        cash_confirmed = bool(payload.get("cash_confirmed"))

        # Cash on Pickup Completion verification
        if requested_status == MarketplaceOrder.STATUS_COMPLETED:
            if not cash_confirmed and payment_status != MarketplaceOrder.PAYMENT_PAID and order.payment_status != MarketplaceOrder.PAYMENT_PAID:
                return JsonResponse(
                    {"error": "Cash payment receipt must be confirmed before completing the order."},
                    status=409,
                )
            payment_status = MarketplaceOrder.PAYMENT_PAID

        cancellation_reason = (payload.get("cancellation_reason") or "").strip()
        if (
            requested_status == MarketplaceOrder.STATUS_CANCELLED
            and requested_status != current_status
            and not cancellation_reason
        ):
            return JsonResponse({"error": "Cancellation reason is required."}, status=400)

        pickup_raw = (payload.get("pickup_scheduled_at") or "").strip()
        pickup_scheduled_at = None
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
        order.official_receipt_no = (
            receipt_no if payment_status == MarketplaceOrder.PAYMENT_PAID else ""
        )
        order.pickup_location = (payload.get("pickup_location") or "").strip()
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
            order.picked_up_at = now
            update_fields.update({"completed_at", "picked_up_at"})

        if (
            requested_status == MarketplaceOrder.STATUS_CANCELLED
            and current_status != requested_status
        ):
            order.cancelled_at = now
            update_fields.add("cancelled_at")
            if order.product_id and order.inventory_deducted and not order.inventory_restored:
                product = Product.objects.select_for_update().get(id=order.product_id)
                selections = (order.customization or {}).get("selections") or []
                adjust_product_stock(product, selections, order.quantity, restore=True)
                product.save(update_fields=["stock", "customization_options", "updated_at"])
                order.inventory_restored = True
                update_fields.add("inventory_restored")

        order.save(update_fields=sorted(update_fields))

        if requested_status != current_status:
            MarketplaceOrderStatusHistory.objects.create(
                order=order,
                previous_status=current_status,
                new_status=requested_status,
                changed_by=changed_by,
                notes=cancellation_reason,
            )

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


def _booking_request_rows():
    """Build the complete booking request list used by the admin table."""
    from api.models import Booking, Room

    bookings = list(
        Booking.objects.select_related("facility", "user")
        .prefetch_related("payments")
        .order_by("-created_at")[:300]
    )
    room_ids = {booking.room_id for booking in bookings if booking.room_id}
    rooms = {
        room.id: (room.room_name or room.room_type or "Room")
        for room in Room.objects.filter(id__in=room_ids)
    }

    rows = []
    for booking in bookings:
        event_type, reserved_by, purpose = _booking_display_fields(booking)
        payments = list(booking.payments.all())
        latest_payment = payments[0] if payments else None
        rows.append(
            {
                "id": booking.id,
                "type": event_type,
                "facility_id": booking.facility_id or "",
                "facility": booking.facility.facility_name if booking.facility_id else "Facility",
                "room": rooms.get(booking.room_id, "-") if booking.room_id else "-",
                "date": booking.booking_date.isoformat() if booking.booking_date else "",
                "start": booking.start_time.strftime("%H:%M") if booking.start_time else "",
                "end": booking.end_time.strftime("%H:%M") if booking.end_time else "",
                "reserved_by": reserved_by,
                "purpose": purpose,
                "total_amount": str(booking.total_amount or 0),
                "payment_status": latest_payment.payment_status if latest_payment else "unpaid",
                "status": booking.status,
                "created_at": booking.created_at.isoformat() if booking.created_at else "",
            }
        )

    return rows


@permissions_required_any(
    "can_manage_bookings",
    "can_approve_bookings",
    "can_record_facility_payment",
)
def admin_bookings_page(request):
    from api.models import Facility

    context = {
        "calendar_events": _bookings_calendar_events(),
        "booking_requests": _booking_request_rows(),
        "facilities": Facility.objects.filter(is_archived=False).order_by("facility_name")[:100],
        "can_manage_facilities": user_can_manage_facilities(request.user),
        "can_book_facilities": user_can_book_facilities(request.user),
        "can_approve_bookings": request.user.has_perm("accounts.can_approve_bookings"),
        "can_record_facility_payment": request.user.has_perm(
            "accounts.can_record_facility_payment"
        ),
        "page_title": "Bookings",
        "breadcrumb_page": "Bookings",
        "active_page": "bookings",
        **get_notification_context(),
    }
    return render(request, "facilities/pages/admin_bookings.html", context)


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_schedules", login_url="admin_dashboard_page")
def admin_calendar_page(request):
    from api.models import Facility

    context = {
        "calendar_events": _bookings_calendar_events(),
        "facilities": Facility.objects.filter(is_archived=False).order_by("facility_name")[:100],
        "can_manage_facilities": user_can_manage_facilities(request.user),
        "can_book_facilities": user_can_book_facilities(request.user),
        "calendar_only": True,
        "page_title": "Calendar",
        "breadcrumb_page": "Calendar",
        "active_page": "calendar",
        **get_notification_context(),
    }
    return render(request, "facilities/pages/admin_bookings.html", context)


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_roles_permissions", login_url="admin_dashboard_page")
def admin_roles_page(request):
    """Display database-backed roles with filters and pagination."""
    search_query = request.GET.get("q", "").strip()
    role_type = request.GET.get("type", "").strip().lower()
    status_filter = request.GET.get("status", "").strip().lower()

    roles_qs = Role.objects.prefetch_related("granted_permissions").annotate(
        role_display_order=Case(
            When(role_name="Super Admin", then=Value(0)),
            When(role_name="Marketplace Admin", then=Value(1)),
            When(role_name="Facilities Admin", then=Value(2)),
            When(role_name="User", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by("role_display_order", "role_name")
    if search_query:
        roles_qs = roles_qs.filter(
            Q(role_name__icontains=search_query) | Q(description__icontains=search_query)
        )
    if role_type == "system":
        roles_qs = roles_qs.filter(role_name__in=PROTECTED_ADMIN_ROLES)
    elif role_type == "custom":
        roles_qs = roles_qs.exclude(role_name__in=PROTECTED_ADMIN_ROLES)
    if status_filter == "active":
        roles_qs = roles_qs.filter(is_active=True)
    elif status_filter == "inactive":
        roles_qs = roles_qs.filter(is_active=False)

    paginator = Paginator(roles_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    roles_data = []
    for role in page_obj.object_list:
        role_users_qs = User.objects.filter(role=role.role_name).order_by("first_name", "last_name", "username")
        assigned_perms = list(
            role.granted_permissions.filter(
                codename__in=ADMIN_PERMISSION_CODENAMES
            ).values_list("codename", flat=True)
        )
        if role.role_name.casefold() == "super admin":
            assigned_perms = list(ADMIN_PERMISSION_CODENAMES)
        perm_labels = permission_labels_for_role(role.role_name)
        role_users = [
            {
                "id": u.id,
                "username": u.username,
                "full_name": (u.get_full_name() or "").strip() or u.username,
                "email": u.email or "",
                "is_active": u.is_active,
                "initials": (
                    f"{(u.first_name[:1] if u.first_name else '')}{(u.last_name[:1] if u.last_name else '')}".upper()
                    or u.username[:2].upper()
                ),
            }
            for u in role_users_qs
        ]

        permission_count = len(assigned_perms)
        roles_data.append({
            "id": str(role.id),
            "role_name": role.role_name,
            "display_name": "Standard User" if role.role_name == "User" else role.role_name,
            "description": role.description,
            "user_count": len(role_users),
            "assigned_permissions": assigned_perms,
            "permission_labels": perm_labels,
            "role_users": role_users,
            "permission_count": permission_count,
            "permission_summary": permission_set_label_for_role(
                role.role_name, assigned_perms
            ),
            "is_protected": role.role_name in PROTECTED_ADMIN_ROLES,
            "role_type": "System Role" if role.role_name in PROTECTED_ADMIN_ROLES else "Custom Role",
            "is_active": role.is_active,
            "status_label": "Active" if role.is_active else "Inactive",
            "created_at": timezone.localtime(role.created_at).strftime("%b %d, %Y"),
        })

    permission_groups = [
        {
            "name": module_name,
            "key": module_name.lower().replace(" ", "-"),
            "permissions": [
                {"codename": codename, "label": label}
                for codename, label in permissions
            ],
        }
        for module_name, permissions in PERMISSION_MODULES
    ]
    all_role_names = list(Role.objects.values_list("role_name", flat=True))
    # Django User records are the administrator account store. Mobile users are
    # held separately in CampusHubUser and must never appear in role assignment.
    admin_accounts = User.objects.all()
    assignable_admins = [
        {
            "id": user.id,
            "full_name": (user.get_full_name() or "").strip() or user.username,
            "username": user.username,
            "email": user.email or "",
            "role": user.role or "User",
            "display_role": "Standard User" if (user.role or "User") == "User" else user.role,
            "department_id": user.department_id,
            "is_active": user.is_active and not user.is_suspended,
        }
        for user in admin_accounts.select_related("department").order_by(
            "first_name", "last_name", "username"
        )
    ]
    query_without_page = request.GET.copy()
    query_without_page.pop("page", None)

    return render(
        request,
        "user_management/pages/admin_roles.html",
        {
            "roles": roles_data,
            "roles_json": roles_data,
            "permission_groups": permission_groups,
            "assignable_admins": assignable_admins,
            "page_obj": page_obj,
            "query_without_page": query_without_page.urlencode(),
            "search_query": search_query,
            "role_type_filter": role_type,
            "status_filter": status_filter,
            "total_roles": Role.objects.count(),
            "assigned_admins": admin_accounts.filter(role__in=all_role_names).count(),
            "unassigned_admins": admin_accounts.exclude(role__in=all_role_names).count(),
            "total_permission_count": len(ADMIN_PERMISSION_CODENAMES),
            **get_notification_context(),
        },
    )


def _serialize_admin_role(role):
    assigned_perms = list(
        role.granted_permissions.filter(
            codename__in=ADMIN_PERMISSION_CODENAMES
        ).values_list("codename", flat=True)
    )
    if role.role_name.casefold() == "super admin":
        assigned_perms = list(ADMIN_PERMISSION_CODENAMES)
    role_users_qs = User.objects.filter(role=role.role_name).order_by("first_name", "last_name", "username")
    role_users = [
        {
            "id": u.id,
            "username": u.username,
            "full_name": (u.get_full_name() or "").strip() or u.username,
            "email": u.email or "",
            "is_active": u.is_active,
            "initials": (
                f"{(u.first_name[:1] if u.first_name else '')}{(u.last_name[:1] if u.last_name else '')}".upper()
                or u.username[:2].upper()
            ),
        }
        for u in role_users_qs
    ]
    permission_count = len(assigned_perms)
    return {
        "id": str(role.id),
        "role_name": role.role_name,
        "display_name": "Standard User" if role.role_name == "User" else role.role_name,
        "description": role.description or "",
        "user_count": len(role_users),
        "assigned_permissions": assigned_perms,
        "permission_labels": permission_labels_for_role(role.role_name),
        "role_users": role_users,
        "permission_count": permission_count,
        "permission_summary": permission_set_label_for_role(
            role.role_name, assigned_perms
        ),
        "is_protected": role.role_name in PROTECTED_ADMIN_ROLES,
        "role_type": "System Role" if role.role_name in PROTECTED_ADMIN_ROLES else "Custom Role",
        "is_active": role.is_active,
        "status_label": "Active" if role.is_active else "Inactive",
        "created_at": timezone.localtime(role.created_at).strftime("%b %d, %Y"),
    }




def _roles_ajax_request(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _roles_json_response(request, *, success, message, role=None, role_id=None, status=200):
    msg_str = str(message)
    if _roles_ajax_request(request):
        payload = {"success": success, "message": msg_str}
        if role is not None:
            payload["role"] = _serialize_admin_role(role)
        if role_id is not None:
            payload["role_id"] = str(role_id)
        return JsonResponse(payload, status=status if success else status)
    if success:
        messages.success(request, msg_str)
    else:
        messages.error(request, msg_str)
    return redirect("admin_roles_page")


def _parse_assigned_admin_ids(request):
    if request.POST.get("assigned_users_present") != "1":
        return None
    try:
        return {
            int(raw_id)
            for raw_id in request.POST.getlist("assigned_users")
            if raw_id.strip()
        }
    except (TypeError, ValueError):
        raise ValidationError("Choose valid administrator accounts to assign.")


def _apply_role_assignments(role, selected_user_ids):
    """Replace a role's admin assignments while preserving RBAC invariants."""
    if selected_user_ids is None:
        return

    current_users = list(
        User.objects.select_for_update().filter(role=role.role_name).order_by("id")
    )
    selected_users = list(
        User.objects.select_for_update().filter(pk__in=selected_user_ids).order_by("id")
    )
    if len(selected_users) != len(selected_user_ids):
        raise ValidationError("One or more selected administrator accounts no longer exist.")

    current_ids = {user.id for user in current_users}
    newly_assigned_ids = selected_user_ids - current_ids
    if (
        selected_user_ids
        and not role.granted_permissions.exists()
        and (role.is_active or newly_assigned_ids)
    ):
        raise ValidationError("Assign at least one permission before assigning administrators.")
    if not role.is_active and newly_assigned_ids:
        raise ValidationError("Inactive roles cannot be assigned to new administrators.")
    if role.role_name == "Marketplace Admin":
        missing_department = [user.username for user in selected_users if not user.department_id]
        if missing_department:
            raise ValidationError(
                "Marketplace Admin assignments require a department: "
                + ", ".join(missing_department)
                + "."
            )

    active_super_ids = set(
        User.objects.filter(is_active=True, is_suspended=False)
        .filter(Q(is_superuser=True) | Q(role__iexact="Super Admin"))
        .values_list("id", flat=True)
    )
    demoted_super_ids = set()
    if role.role_name == "Super Admin":
        demoted_super_ids.update(current_ids - selected_user_ids)
    else:
        demoted_super_ids.update(active_super_ids & selected_user_ids)
    promoted_super_ids = {
        user.id
        for user in selected_users
        if role.role_name == "Super Admin" and user.is_active and not user.is_suspended
    }
    if not ((active_super_ids - demoted_super_ids) | promoted_super_ids):
        raise ValidationError("The final active Super Admin assignment cannot be removed.")

    fallback_role, _ = Role.objects.get_or_create(
        role_name="User",
        defaults={"description": "Standard CampusHub user.", "is_active": True},
    )
    removed_users = [user for user in current_users if user.id not in selected_user_ids]
    for user in removed_users:
        user.role = fallback_role.role_name
        user.save(update_fields=["role"])
        sync_user_admin_permissions(user)
    for user in selected_users:
        if user.role != role.role_name:
            user.role = role.role_name
            user.save(update_fields=["role"])
        sync_user_admin_permissions(user)


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_roles_permissions", login_url="admin_dashboard_page")
def admin_roles_save(request):
    """Create or update a role."""
    if request.method != "POST":
        return redirect("admin_roles_page")

    role_id = request.POST.get("role_id", "").strip()
    role_name = request.POST.get("role_name", "").strip()
    description = request.POST.get("description", "").strip()
    role_status_submitted = request.POST.get("role_status_present") == "1"
    requested_active = request.POST.get("is_active") == "on"
    try:
        assigned_admin_ids = _parse_assigned_admin_ids(request)
    except ValidationError as exc:
        return _roles_json_response(
            request,
            success=False,
            message=" ".join(exc.messages),
            status=400,
        )
    selected_perms = [
        codename
        for codename in request.POST.getlist("permissions")
        if codename in ADMIN_PERMISSION_CODENAMES
    ]

    if not role_name:
        return _roles_json_response(
            request,
            success=False,
            message="Role name is required.",
            status=400,
        )

    if role_id:
        try:
            with transaction.atomic():
                role = Role.objects.select_for_update().get(id=role_id)
                previous_name = role.role_name
                if previous_name in PROTECTED_ADMIN_ROLES and role_name != previous_name:
                    return _roles_json_response(
                        request,
                        success=False,
                        message="Built-in roles cannot be renamed.",
                        status=400,
                    )
                if Role.objects.filter(role_name__iexact=role_name).exclude(id=role.id).exists():
                    return _roles_json_response(
                        request,
                        success=False,
                        message=f'Role "{role_name}" already exists.',
                        status=400,
                    )
                role.role_name = role_name
                role.description = description
                role.is_active = (
                    True
                    if previous_name in PROTECTED_ADMIN_ROLES
                    else requested_active if role_status_submitted else role.is_active
                )
                role.save(update_fields=["role_name", "description", "is_active"])
                if role_name == "Super Admin":
                    selected_perms = list(ADMIN_PERMISSION_CODENAMES)
                set_role_permissions(role, selected_perms)
                if previous_name != role_name:
                    User.objects.filter(role=previous_name).update(role=role_name)
                _apply_role_assignments(role, assigned_admin_ids)
                sync_users_for_role(role_name)
            return _roles_json_response(
                request,
                success=True,
                message=f'Role "{role_name}" updated.',
                role=role,
            )
        except Role.DoesNotExist:
            return _roles_json_response(
                request,
                success=False,
                message="Role not found.",
                status=404,
            )
        except ValidationError as exc:
            return _roles_json_response(
                request,
                success=False,
                message=" ".join(exc.messages),
                status=400,
            )
    else:
        if Role.objects.filter(role_name__iexact=role_name).exists():
            return _roles_json_response(
                request,
                success=False,
                message=f'Role "{role_name}" already exists.',
                status=400,
            )
        try:
            with transaction.atomic():
                role = Role.objects.create(
                    role_name=role_name,
                    description=description,
                    is_active=requested_active if role_status_submitted else True,
                )
                set_role_permissions(role, selected_perms)
                _apply_role_assignments(role, assigned_admin_ids)
        except ValidationError as exc:
            return _roles_json_response(
                request,
                success=False,
                message=" ".join(exc.messages),
                status=400,
            )
        return _roles_json_response(
            request,
            success=True,
            message=f'Role "{role_name}" created.',
            role=role,
        )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_roles_permissions", login_url="admin_dashboard_page")
def admin_role_permissions_save(request):
    """Update only a role's permission bundle from the permissions workspace."""
    if request.method != "POST":
        return redirect("admin_roles_page")

    role_id = request.POST.get("role_id", "").strip()
    selected_perms = [
        codename
        for codename in request.POST.getlist("permissions")
        if codename in ADMIN_PERMISSION_CODENAMES
    ]
    try:
        with transaction.atomic():
            role = Role.objects.select_for_update().get(id=role_id)
            if role.role_name == "Super Admin":
                selected_perms = list(ADMIN_PERMISSION_CODENAMES)
            elif not selected_perms and User.objects.filter(role=role.role_name).exists():
                return _roles_json_response(
                    request,
                    success=False,
                    message="A role assigned to administrators must keep at least one permission.",
                    status=400,
                )
            set_role_permissions(role, selected_perms)
            sync_users_for_role(role.role_name)
        return _roles_json_response(
            request,
            success=True,
            message=f'Permissions for "{role.role_name}" updated.',
            role=role,
        )
    except (Role.DoesNotExist, ValidationError):
        return _roles_json_response(
            request,
            success=False,
            message="Role not found.",
            status=404,
        )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_roles_permissions", login_url="admin_dashboard_page")
def admin_roles_status(request):
    """Activate or deactivate a custom role and resync assigned users."""
    if request.method != "POST":
        return redirect("admin_roles_page")

    role_id = request.POST.get("role_id", "").strip()
    action = request.POST.get("action", "").strip().lower()
    if action not in {"activate", "deactivate"}:
        return _roles_json_response(
            request,
            success=False,
            message="Choose a valid role status action.",
            status=400,
        )

    try:
        with transaction.atomic():
            role = Role.objects.select_for_update().get(id=role_id)
            if role.role_name in PROTECTED_ADMIN_ROLES and action == "deactivate":
                return _roles_json_response(
                    request,
                    success=False,
                    message="Built-in system roles cannot be deactivated.",
                    status=400,
                )
            role.is_active = action == "activate"
            role.save(update_fields=["is_active"])
            sync_users_for_role(role.role_name)
        return _roles_json_response(
            request,
            success=True,
            message=f'Role "{role.role_name}" {"activated" if role.is_active else "deactivated"}.',
            role=role,
        )
    except Role.DoesNotExist:
        return _roles_json_response(
            request,
            success=False,
            message="Role not found.",
            status=404,
        )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_roles_permissions", login_url="admin_dashboard_page")
def admin_roles_delete(request):
    """Delete a role."""
    if request.method != "POST":
        return redirect("admin_roles_page")

    role_id = request.POST.get("role_id", "").strip()
    if role_id:
        try:
            role = Role.objects.get(id=role_id)
            name = role.role_name
            if name in PROTECTED_ADMIN_ROLES:
                return _roles_json_response(
                    request,
                    success=False,
                    message="Built-in roles cannot be deleted.",
                    status=400,
                )
            with transaction.atomic():
                fallback_role, _ = Role.objects.get_or_create(
                    role_name="User",
                    defaults={"description": "Standard CampusHub user."},
                )
                User.objects.filter(role=name).update(role=fallback_role.role_name)
                role.delete()
                sync_users_for_role(fallback_role.role_name)
            return _roles_json_response(
                request,
                success=True,
                message=f'Role "{name}" deleted. Affected users reset to "Standard User".',
                role_id=role_id,
            )
        except Role.DoesNotExist:
            return _roles_json_response(
                request,
                success=False,
                message="Role not found.",
                status=404,
            )
        except Exception as e:
            return _roles_json_response(
                request,
                success=False,
                message=f"Error deleting role: {e}",
                status=500,
            )

    return _roles_json_response(
        request,
        success=False,
        message="Role ID is required.",
        status=400,
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_view_user_monitoring", login_url="admin_dashboard_page")
def admin_user_monitoring_page(request):
    """Monitor real authentication activity across admin and mobile accounts."""
    if not _is_super_admin(request.user):
        raise PermissionDenied

    from datetime import datetime, time, timedelta

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
    account_refs = [row["ref"] for row in all_rows]
    latest_events = AccountActivity.objects.filter(account_ref__in=account_refs).order_by(
        "account_ref", "-created_at"
    ).distinct("account_ref")
    latest_event_by_ref = {event.account_ref: event for event in latest_events}

    online_admin_ids = set(
        AdminTabToken.objects.filter(
            expires_at__gt=now,
            last_seen_at__gte=online_cutoff,
            user__is_active=True,
            user__is_suspended=False,
        ).values_list("user_id", flat=True)
    )
    online_mobile_ids = set(
        AccountActivity.objects.filter(
            account_source=AccountActivity.SOURCE_MOBILE,
            activity_type="login_success",
            result=AccountActivity.RESULT_SUCCESS,
            created_at__gte=online_cutoff,
            account_id__isnull=False,
        ).values_list("account_id", flat=True)
    )
    online_refs = {f"admin:{pk}" for pk in online_admin_ids} | {
        f"mobile:{pk}" for pk in online_mobile_ids
    }

    for row in all_rows:
        event = latest_event_by_ref.get(str(row["ref"]))
        row["role_label"] = "Standard User" if row["role"] == "User" else row["role"]
        if row["is_suspended"]:
            row["monitor_status"] = "suspended"
            row["monitor_status_label"] = "Suspended"
        elif row["ref"] in online_refs:
            row["monitor_status"] = "online"
            row["monitor_status_label"] = "Online"
        else:
            row["monitor_status"] = "offline"
            row["monitor_status_label"] = "Offline"
        row["last_activity"] = event.activity if event else ""
        row["last_activity_at"] = event.created_at if event else None

    online_users = sorted(
        (row for row in all_rows if row["ref"] in online_refs),
        key=lambda row: row["last_activity_at"] or row["last_login"] or row["date_joined"],
        reverse=True,
    )[:5]
    for row in online_users:
        row["online_activity"] = row["last_activity"] or "Active session"

    events_in_range = AccountActivity.objects.filter(
        created_at__gte=range_start,
        created_at__lt=range_end,
    )
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
            (not query or query in searchable)
            and (not account_type or row["account_type"] == account_type)
            and (not role or row["role"].lower() == role)
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
    for event in AccountActivity.objects.filter(account_ref__in=page_refs).order_by("-created_at"):
        if len(drawer_events[event.account_ref]) < 20:
            drawer_events[event.account_ref].append({
                "time": timezone.localtime(event.created_at).strftime("%b %d, %Y %I:%M %p"),
                "activity": event.activity,
                "type": event.activity_type,
                "module": event.module,
                "result": event.get_result_display(),
                "ip": event.ip_address or "",
                "device": event.user_agent or "",
            })
    session_map = {ref: [] for ref in page_refs}
    page_admin_ids = [row["id"] for row in page_obj.object_list if row["source"] == "admin"]
    for session in AdminTabToken.objects.filter(user_id__in=page_admin_ids).order_by("-last_seen_at", "-created_at"):
        ref = f"admin:{session.user_id}"
        if len(session_map[ref]) < 10:
            session_map[ref].append({
                "created": timezone.localtime(session.created_at).strftime("%b %d, %Y %I:%M %p"),
                "last_seen": timezone.localtime(session.last_seen_at).strftime("%b %d, %Y %I:%M %p") if session.last_seen_at else "",
                "expires": timezone.localtime(session.expires_at).strftime("%b %d, %Y %I:%M %p"),
                "active": session.expires_at > now,
            })

    users_json = []
    for row in page_obj.object_list:
        events = drawer_events[row["ref"]]
        latest = events[0] if events else {}
        users_json.append({
            "ref": row["ref"],
            "initials": row["initials"],
            "fullName": row["full_name"],
            "username": row["username"],
            "email": row["email"],
            "accountType": row["account_type_label"],
            "role": row["role_label"],
            "status": row["monitor_status_label"],
            "lastLogin": timezone.localtime(row["last_login"]).strftime("%b %d, %Y %I:%M %p") if isinstance(row.get("last_login"), datetime) else "",
            "lastActivity": row["last_activity"],
            "lastActivityAt": timezone.localtime(row["last_activity_at"]).strftime("%b %d, %Y %I:%M %p") if isinstance(row.get("last_activity_at"), datetime) else "",
            "ip": latest.get("ip", ""),
            "device": latest.get("device", ""),
            "events": events,
            "sessions": session_map[row["ref"]],
        })

    successful_logins = events_in_range.filter(
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

    online_total = len(online_refs)

    hourly_login_counts = [0] * 24
    for logged_at in events_in_range.filter(
        activity_type="login_success",
        result=AccountActivity.RESULT_SUCCESS,
    ).values_list("created_at", flat=True):
        hourly_login_counts[timezone.localtime(logged_at).hour] += 1
    def hour_label(hour):
        return datetime.combine(local_today, time(hour=hour)).strftime("%I %p").lstrip("0")

    account_type_labels = {**dict(ACCOUNT_TYPES), "admin": "Admin"}
    recent_activities = []
    for event in events_in_range.order_by("-created_at")[:10]:
        role_label = "Standard User" if event.role == "User" else (event.role or "-")
        recent_activities.append({
            "id": str(event.pk),
            "time": timezone.localtime(event.created_at).strftime("%b %d, %Y %I:%M %p"),
            "user": event.full_name or event.username or "Unknown",
            "identity": event.email or event.username or "Unknown account",
            "account_type": account_type_labels.get(event.account_type, event.account_type.title() or "Unknown"),
            "account_type_value": event.account_type or "unknown",
            "role": role_label,
            "activity": event.activity,
            "module": event.module,
            "ip": event.ip_address or "",
            "device": event.user_agent or "",
            "result": event.get_result_display(),
            "result_value": event.result,
        })
    query_without_page = request.GET.copy()
    query_without_page.pop("page", None)
    role_choices = sorted({str(row["role"]) for row in all_rows if row.get("role")}, key=str.casefold)
    active_sessions = AdminTabToken.objects.filter(
        expires_at__gt=now,
        user__is_active=True,
        user__is_suspended=False,
    ).count()
    monitor_chart_data = {
        **login_trend_data,
        "peakHours": {
            "labels": [hour_label(hour) for hour in range(24)],
            "values": hourly_login_counts,
        },
    }

    return render(request, "user_management/pages/admin_user_monitoring.html", {
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
        "account_types": ACCOUNT_TYPES,
        "role_choices": role_choices,
        "activity_types": (("login_success", "Successful Login"), ("login_failed", "Failed Login"), ("logout", "Logout")),
        "filters": {
            "q": request.GET.get("q", ""),
            "type": account_type,
            "role": request.GET.get("role", ""),
            "status": status,
            "activity": activity_type,
            "period": monitoring_period,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
        **get_notification_context(),
    })


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_settings", login_url="admin_dashboard_page")
def admin_settings_page(request):
    """System settings page."""
    return render(
        request,
        "user_management/pages/admin_settings.html",
        get_notification_context(),
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
            **get_notification_context(),
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
            **get_notification_context(),
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
            **get_notification_context(),
        },
    )
