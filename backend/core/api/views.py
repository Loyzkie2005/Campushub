import base64
import binascii
import json
import random
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import jwt
from jwt import InvalidTokenError

from accounts.admin_tab_auth import (
    append_tab_token_to_url,
    create_admin_tab_token,
    get_tab_token_from_request,
    revoke_admin_tab_token,
)
from accounts.activity_logging import log_account_activity
from accounts.models import AccountActivity, User
from accounts.role_permissions import (
    ADMIN_PERMISSION_CODENAMES,
    get_admin_home_url,
    sync_user_admin_permissions,
    user_has_admin_access,
    user_has_facility_module_access,
)
from modules.messages.auth import mobile_chat_token
from modules.facilities.services.facility_configuration import (
    normalize_facility_status,
    validate_facility_payload,
)

from modules.marketplace.services.customization import (
    build_order_customization_payload,
    is_food_category,
    normalize_customization_options,
    parse_order_selections,
    validate_order_selections,
)
from modules.marketplace.services.recommendation import get_recommended_products
from .email_service import is_gmail_configured, send_password_reset_email
from .inventory import (
    InsufficientStockError,
    adjust_product_stock,
    count_customization_options,
    get_inventory_status_label,
    get_product_total_stock,
    is_perishable_category,
    low_stock_threshold,
    parse_expiry_date,
    PERISHABLE_CATEGORIES,
)
from .product_images import (
    persist_product_image,
    persist_product_images,
    persist_facility_image,
    persist_facility_images,
)


def _should_update_product_image(raw: str) -> bool:
    value = (raw or "").strip()
    if not value:
        return False
    if value.startswith("/api/products/"):
        return False
    return True
from .models import (
    Booking,
    CampusHubUser,
    Facility,
    MarketplaceOrder,
    PasswordResetCode,
    Product,
    ProductInteraction,
    SellerRequest,
)
FEATURE_PERMISSIONS = [
    f"accounts.{codename}" for codename in ADMIN_PERMISSION_CODENAMES
]


def get_admin_redirect_url(user):
    return get_admin_home_url(user)


def serialize_mobile_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.get_full_name(),
        "role": user.role,
    }


def serialize_campushub_user(user):
    user_type = (user.user_type or "").strip().lower()
    return {
        "id": user.id,
        "username": user.username,
        "student_id": user.student_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}".strip(),
        "role": user.role or "User",
        "account_type": user_type,
        "user_type": user_type,
        "department": user.department.name if user.department else None,
        "is_active": user.is_active,
        "is_suspended": user.is_suspended,
        "institutional_id": user.institutional_id,
        "contact_number": user.contact_number,
        "profile_completed": user.profile_completed,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def _mobile_user_from_bearer(request):
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None, JsonResponse({"error": "Bearer token required."}, status=401)

    try:
        claims = jwt.decode(
            token.strip(),
            settings.CHAT_JWT_SECRET,
            algorithms=[settings.CHAT_JWT_ALGORITHM],
            issuer="campushub-django",
            audience="campushub-chat",
            options={"require": ["sub", "exp", "iss", "aud"]},
        )
    except InvalidTokenError:
        return None, JsonResponse(
            {"error": "Invalid or expired login token."},
            status=401,
        )

    subject = claims.get("sub", "")
    if not isinstance(subject, str) or not subject.startswith("mobile:"):
        return None, JsonResponse({"error": "Invalid mobile user token."}, status=401)

    try:
        user_id = int(subject.removeprefix("mobile:"))
    except ValueError:
        return None, JsonResponse({"error": "Invalid mobile user token."}, status=401)

    user = CampusHubUser.objects.filter(pk=user_id).first()
    if user is None:
        return None, JsonResponse({"error": "User account not found."}, status=404)
    if not user.is_active or user.is_suspended:
        return None, JsonResponse({"error": "This account is inactive or suspended."}, status=403)
    return user, None


def _validate_mobile_profile(user_type, institutional_id, contact_number):
    valid_types = {
        CampusHubUser.USER_TYPE_STUDENT,
        CampusHubUser.USER_TYPE_FACULTY,
        CampusHubUser.USER_TYPE_GUEST,
    }
    if user_type not in valid_types:
        return "Select Student, Faculty, or Guest."
    if user_type != CampusHubUser.USER_TYPE_GUEST and len(institutional_id) < 5:
        return "Enter a valid student or faculty ID."
    if not re.fullmatch(r"(?:\+63|0)9\d{9}", contact_number):
        return "Enter a valid Philippine contact number."
    return None


def serialize_product(product, request=None):
    image_url = ""
    images = []
    if product.image_url:
        raw = product.image_url.strip()
        # Check if it's a JSON array
        if raw.startswith("["):
            try:
                images = json.loads(raw)
                image_url = images[0] if images else ""
            except (json.JSONDecodeError, IndexError):
                image_url = raw
                images = [raw] if raw else []
        else:
            image_url = raw
            images = [raw] if raw else []

    return {
        "id": product.id,
        "seller_id": product.seller_id,
        "seller": product.seller.get_full_name().strip()
        or product.seller.username,
        "department": str(product.seller.department)
        if getattr(product.seller, "department_id", None)
        else "",
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": str(product.price),
        "price_display": product.get_price_display(),
        "stock": get_product_total_stock(product),
        "variant_count": (
            count_customization_options(product.customization_options)
            if product.customization_enabled
            else 0
        ),
        "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
        "inventory_status": product.get_inventory_status(),
        "inventory_status_label": product.get_inventory_status_label(),
        "low_stock_threshold": low_stock_threshold(),
        "is_perishable": is_perishable_category(product.category),
        "perishable_categories": sorted(PERISHABLE_CATEGORIES),
        "image_url": image_url,
        "images": images,
        "seller_contact": product.seller.email,
        "approval_status": product.approval_status,
        "rejection_reason": product.rejection_reason,
        "submitted_at": product.submitted_at.isoformat(),
        "customization_enabled": bool(product.customization_enabled),
        "customization_options": product.customization_options or [],
        "is_archived": bool(getattr(product, "is_archived", False)),
    }


def manageable_products_for(user):
    from modules.marketplace.services.product_access import admin_product_queryset

    return admin_product_queryset(user)


def serialize_marketplace_order(order):
    return {
        "id": order.id,
        "order_code": order.order_code or "",
        "product_id": order.product_id,
        "product_name": order.product_name,
        "category": order.category,
        "buyer_user_id": order.buyer_user_id,
        "buyer_name": order.buyer_name,
        "buyer_email": order.buyer_email,
        "seller_name": order.seller_name,
        "seller_contact": order.seller_contact,
        "message_to_seller": order.message_to_seller,
        "option": order.option,
        "customization": order.customization or {},
        "quantity": order.quantity,
        "unit_price": str(order.unit_price),
        "total_price": str(order.total_price),
        "image_url": order.image_url,
        "status": order.status,
        "status_label": order.get_status_display(),
        "payment_status": order.payment_status,
        "official_receipt_no": order.official_receipt_no,
        "pickup_location": order.pickup_location,
        "pickup_scheduled_at": (
            order.pickup_scheduled_at.isoformat() if order.pickup_scheduled_at else None
        ),
        "cancellation_reason": order.cancellation_reason,
        "created_at": order.created_at.isoformat(),
    }


def serialize_seller_request(seller_request):
    return {
        "id": seller_request.id,
        "student_id": seller_request.student_id,
        "full_name": seller_request.full_name,
        "course_section": seller_request.course_section,
        "contact_number": seller_request.contact_number,
        "product_type": seller_request.product_type,
        "message": seller_request.message,
        "status": seller_request.status,
        "rejection_reason": seller_request.rejection_reason,
        "created_at": seller_request.created_at.isoformat(),
    }


@csrf_exempt
def admin_login(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Invalid request method"},
            status=405
        )

    try:
        data = json.loads(request.body)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return JsonResponse(
                {"error": "Username and password are required"},
                status=400
            )

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            sync_user_admin_permissions(user)
            if not user_has_admin_access(user):
                log_account_activity(
                    request,
                    source=AccountActivity.SOURCE_ADMIN,
                    account=user,
                    activity_type="login_failed",
                    activity="Failed login attempt",
                    result=AccountActivity.RESULT_FAILED,
                )
                return JsonResponse(
                    {"error": "This account does not have admin access."},
                    status=403,
                )

            remember_me = bool(data.get("remember_me"))
            tab_token = create_admin_tab_token(user, remember_me=remember_me)
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])
            log_account_activity(
                request,
                source=AccountActivity.SOURCE_ADMIN,
                account=user,
                activity_type="login_success",
                activity="Logged in",
                result=AccountActivity.RESULT_SUCCESS,
            )
            redirect_url = append_tab_token_to_url(
                get_admin_redirect_url(user),
                tab_token,
            )
            return JsonResponse({
                "message": "Login successful",
                "user_id": user.id,
                "username": user.username,
                "tab_token": tab_token,
                "redirect_url": redirect_url,
            })

        attempted_user = User.objects.filter(username__iexact=username).first()
        log_account_activity(
            request,
            source=AccountActivity.SOURCE_ADMIN,
            account=attempted_user,
            identifier=username,
            activity_type="login_failed",
            activity="Failed login attempt",
            result=AccountActivity.RESULT_FAILED,
        )
        return JsonResponse(
            {"error": "Invalid username or password."},
            status=401
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON format"},
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@login_required(login_url="admin_login_page")
def admin_session_status(request):
    user = request.user
    if not user_has_admin_access(user):
        return JsonResponse({"authenticated": False}, status=401)

    return JsonResponse(
        {
            "authenticated": True,
            "user_id": user.id,
            "username": user.username,
            "home_url": get_admin_home_url(user),
        }
    )


def _normalize_person_name(value):
    normalized = " ".join((value or "").strip().split())
    return normalized[:1].upper() + normalized[1:]


def _password_validation_error(password):
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if re.search(r"\s", password):
        return "Password cannot contain spaces."
    if not re.search(r"[A-Z]", password):
        return "Password must include an uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must include a lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must include a number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Password must include a special character."
    return None


@csrf_exempt
def mobile_signup(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    first_name = _normalize_person_name(data.get("first_name"))
    last_name = _normalize_person_name(data.get("last_name"))
    student_id = (data.get("student_id") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not all([first_name, last_name, student_id, email, password, confirm_password]):
        return JsonResponse({"error": "All fields are required."}, status=400)

    if len(student_id) < 3:
        return JsonResponse({"error": "Username must be at least 3 characters."}, status=400)

    if "@" not in email or "." not in email:
        return JsonResponse({"error": "Enter a valid email address."}, status=400)

    password_error = _password_validation_error(password)
    if password_error:
        return JsonResponse({"error": password_error}, status=400)

    if password != confirm_password:
        return JsonResponse({"error": "Passwords do not match."}, status=400)

    if (
        CampusHubUser.objects.filter(username__iexact=student_id).exists()
        or User.objects.filter(username__iexact=student_id).exists()
    ):
        return JsonResponse({"error": "Username already exists."}, status=409)

    if (
        CampusHubUser.objects.filter(email__iexact=email).exists()
        or User.objects.filter(email__iexact=email).exists()
    ):
        return JsonResponse({"error": "Email already exists."}, status=409)

    try:
        user = CampusHubUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=student_id,
            email=email,
            password_hash=make_password(password),
            profile_completed=False,
        )
    except IntegrityError:
        return JsonResponse({"error": "Username or email already exists."}, status=409)

    return JsonResponse(
        {
            "message": "Account created successfully.",
            "user": serialize_campushub_user(user),
        },
        status=201,
    )


@csrf_exempt
def mobile_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    identifier = (data.get("student_id_or_email") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return JsonResponse({"error": "Username/email and password are required."}, status=400)

    user = CampusHubUser.objects.filter(username__iexact=identifier).first()
    if user is None and "@" in identifier:
        user = CampusHubUser.objects.filter(email__iexact=identifier).first()

    if user is None or not check_password(password, user.password_hash):
        log_account_activity(
            request,
            source=AccountActivity.SOURCE_MOBILE,
            account=user,
            identifier=identifier,
            activity_type="login_failed",
            activity="Failed login attempt",
            result=AccountActivity.RESULT_FAILED,
        )
        return JsonResponse({"error": "Invalid Username or Password"}, status=401)
    if not user.is_active or user.is_suspended:
        log_account_activity(
            request,
            source=AccountActivity.SOURCE_MOBILE,
            account=user,
            activity_type="login_failed",
            activity="Failed login attempt",
            result=AccountActivity.RESULT_FAILED,
        )
        return JsonResponse({"error": "This account is inactive or suspended."}, status=403)

    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    log_account_activity(
        request,
        source=AccountActivity.SOURCE_MOBILE,
        account=user,
        activity_type="login_success",
        activity="Logged in",
        result=AccountActivity.RESULT_SUCCESS,
    )

    return JsonResponse(
        {
            "message": "Login successful.",
            "user": serialize_campushub_user(user),
            "chat_token": mobile_chat_token(user),
        }
    )


@csrf_exempt
def mobile_complete_profile(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    user, error_response = _mobile_user_from_bearer(request)
    if error_response is not None:
        return error_response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    user_type = (data.get("user_type") or "").strip().lower()
    student_id = (data.get("student_id") or "").strip()
    institutional_id = (data.get("institutional_id") or "").strip()
    # Accept the previous mobile payload while installed builds are upgraded.
    if user_type == CampusHubUser.USER_TYPE_STUDENT and not student_id:
        student_id = institutional_id
    profile_id = (
        student_id
        if user_type == CampusHubUser.USER_TYPE_STUDENT
        else institutional_id
    )
    contact_number = re.sub(r"[\s-]", "", data.get("contact_number") or "")
    validation_error = _validate_mobile_profile(
        user_type,
        profile_id,
        contact_number,
    )
    if validation_error:
        return JsonResponse({"error": validation_error}, status=400)

    if (
        user_type == CampusHubUser.USER_TYPE_STUDENT
        and CampusHubUser.objects.filter(student_id__iexact=student_id)
        .exclude(pk=user.pk)
        .exists()
    ):
        return JsonResponse({"error": "This student ID is already in use."}, status=400)

    user.user_type = user_type
    user.student_id = (
        student_id if user_type == CampusHubUser.USER_TYPE_STUDENT else None
    )
    user.institutional_id = (
        institutional_id if user_type == CampusHubUser.USER_TYPE_FACULTY else ""
    )
    user.contact_number = contact_number
    user.profile_completed = True
    user.save(
        update_fields=[
            "user_type",
            "student_id",
            "institutional_id",
            "contact_number",
            "profile_completed",
            "updated_at",
        ]
    )

    return JsonResponse(
        {
            "message": "Profile completed successfully.",
            "user": serialize_campushub_user(user),
            "chat_token": mobile_chat_token(user),
        }
    )


@csrf_exempt
def seller_submit_product(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
        name = (data.get("name") or "").strip()
        price = Decimal(str(data.get("price", "")))
        stock = int(data.get("stock", 0))
        category = (data.get("category") or "").strip()
        expiry_date = parse_expiry_date(data.get("expiry_date"))

        if not name:
            return JsonResponse({"error": "Product name is required"}, status=400)

        is_admin_user = (
            request.user.is_superuser
            or request.user.is_staff
            or request.user.has_perm("accounts.can_approve_products")
            or getattr(request.user, "role", "").lower() in ("admin", "marketplace admin")
        )
        approval_status = Product.STATUS_APPROVED if is_admin_user else Product.STATUS_PENDING
        product = Product.objects.create(
            seller=request.user,
            name=name,
            description=(data.get("description") or "").strip(),
            category=category,
            price=price,
            stock=max(stock, 0),
            expiry_date=expiry_date if is_perishable_category(category) else None,
            image_url=(data.get("image_url") or "").strip(),
            approval_status=approval_status,
            approved_by=request.user if is_admin_user else None,
            approved_at=timezone.now() if is_admin_user else None,
        )

        return JsonResponse(
            {
                "message": "Product submitted for marketplace approval.",
                "product": serialize_product(product, request),
            },
            status=201,
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except (InvalidOperation, ValueError):
        return JsonResponse({"error": "Valid price and stock are required"}, status=400)


def approved_products(request):
    today = timezone.localdate()
    products = Product.objects.filter(
        approval_status=Product.STATUS_APPROVED,
        is_archived=False,
        stock__gt=0,
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    )
    return JsonResponse(
        {"products": [serialize_product(product, request) for product in products]}
    )


def product_image(request, product_id):
    """Serve product image through the API (works on mobile over LAN)."""
    from modules.marketplace.services.product_access import image_visible_product_queryset

    product = get_object_or_404(
        image_visible_product_queryset(request.user), id=product_id
    )
    images = product.get_image_list()
    if not images:
        return HttpResponse(status=404)

    index = 0
    index_param = request.GET.get("index")
    if index_param is not None:
        try:
            index = max(0, int(index_param))
        except (TypeError, ValueError):
            index = 0
    if index >= len(images):
        return HttpResponse(status=404)

    raw = (images[index] or "").strip()
    if not raw:
        return HttpResponse(status=404)

    if raw.startswith("data:image/"):
        match = re.match(r"^data:image/\w+;base64,(.+)$", raw, re.DOTALL)
        if not match:
            return HttpResponse(status=404)
        try:
            data = base64.b64decode(match.group(1), validate=False)
        except (ValueError, binascii.Error):
            return HttpResponse(status=404)
        return HttpResponse(data, content_type="image/jpeg")

    if raw.startswith("http://") or raw.startswith("https://"):
        return redirect(raw)

    rel = raw
    if rel.startswith("/media/"):
        rel = rel[len("/media/") :]
    elif rel.startswith("media/"):
        rel = rel[len("media/") :]

    path = Path(settings.MEDIA_ROOT) / rel
    if not path.is_file():
        return HttpResponse(status=404)

    suffix = path.suffix.lower()
    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    content_type = content_types.get(suffix, "image/jpeg")
    return FileResponse(path.open("rb"), content_type=content_type)


@login_required(login_url="admin_login_page")
@csrf_exempt
def admin_save_product(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    if not request.user.has_perm("accounts.can_manage_products"):
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        data = json.loads(request.body)
        product_id = data.get("id")
        seller_id = data.get("seller_id")

        # Verify if a specific seller_id was provided to assign the listing to
        target_seller = None
        if seller_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            target_seller = User.objects.filter(id=seller_id).first()
            if not target_seller:
                target_seller = User.objects.filter(username=str(seller_id)).first()
            if not target_seller and not product_id:
                return JsonResponse({"error": "Selected seller could not be found."}, status=400)
        
        name = (data.get("name") or "").strip()
        price = Decimal(str(data.get("price", "")))
        stock = int(data.get("stock", 0))
        category = (data.get("category") or "").strip()
        expiry_date = parse_expiry_date(data.get("expiry_date"))

        if not name:
            return JsonResponse({"error": "Product name is required"}, status=400)

        raw_image = (data.get("image_url") or "").strip()
        raw_images = data.get("images")  # JSON array of base64 strings
        customization_enabled = bool(data.get("customization_enabled"))
        customization_options = normalize_customization_options(
            data.get("customization_options")
        )
        if not customization_enabled:
            customization_options = []
        elif customization_options:
            customization_enabled = True

        if customization_options:
            stock = sum(
                max(int(opt.get("stock", 0) or 0), 0)
                for group in customization_options
                for opt in (group.get("options") or [])
            )
            expiry_values = []
            for group in customization_options:
                for opt in (group.get("options") or []):
                    parsed = parse_expiry_date(opt.get("expiry_date"))
                    if parsed:
                        expiry_values.append(parsed)
            if is_perishable_category(category) and expiry_values:
                expiry_date = min(expiry_values)
            elif not is_perishable_category(category):
                expiry_date = None

        fields = {
            "name": name,
            "description": (data.get("description") or "").strip(),
            "category": category,
            "price": price,
            "stock": max(stock, 0),
            "expiry_date": expiry_date if is_perishable_category(category) else None,
            "customization_enabled": customization_enabled,
            "customization_options": customization_options,
        }

        raw_status = (
            data.get("approval_status")
            or data.get("product_status")
            or Product.STATUS_PENDING
        )
        approval_status = str(raw_status).strip().lower()
        valid_statuses = {
            Product.STATUS_PENDING,
            Product.STATUS_APPROVED,
            Product.STATUS_REJECTED,
        }
        if approval_status not in valid_statuses:
            approval_status = Product.STATUS_PENDING

        can_approve = (
            request.user.is_superuser
            or request.user.has_perm("accounts.can_approve_products")
            or getattr(request.user, "role", "").lower() in ("admin", "marketplace admin")
        )
        if can_approve:
            if not product_id:
                # When admin creates a new product, auto-approve it
                approval_status = Product.STATUS_APPROVED
            fields["approval_status"] = approval_status
            if approval_status == Product.STATUS_APPROVED:
                fields["rejection_reason"] = ""
                fields["approved_by"] = request.user
                fields["approved_at"] = timezone.now()
            elif approval_status == Product.STATUS_PENDING:
                fields["rejection_reason"] = ""
                fields["approved_by"] = None
                fields["approved_at"] = None
            else:
                fields["approved_by"] = None
                fields["approved_at"] = None
                fields["rejection_reason"] = (data.get("rejection_reason") or "").strip()
        elif not product_id:
            fields["approval_status"] = Product.STATUS_PENDING
            fields["rejection_reason"] = ""
            fields["approved_by"] = None
            fields["approved_at"] = None

        if product_id:
            product = get_object_or_404(
                manageable_products_for(request.user), id=product_id
            )
            for field, value in fields.items():
                setattr(product, field, value)
            product.stock = fields["stock"]
            product.expiry_date = fields["expiry_date"]
            if raw_images and isinstance(raw_images, list):
                urls = persist_product_images(raw_images, product.id, name)
                if urls:
                    product.image_url = json.dumps(urls)
            elif raw_image and _should_update_product_image(raw_image):
                product.image_url = persist_product_image(raw_image, product.id, name)
                
            if target_seller:
                product.seller = target_seller
                
            product.save()
            status_code = 200
            message = "Product updated."
        else:
            product = Product.objects.create(
                seller=target_seller if target_seller else request.user,
                created_by=request.user,
                image_url="",
                **fields,
            )
            if raw_images and isinstance(raw_images, list):
                urls = persist_product_images(raw_images, product.id, name)
                if urls:
                    product.image_url = json.dumps(urls)
                    product.save(update_fields=["image_url", "updated_at"])
            elif raw_image:
                product.image_url = persist_product_image(raw_image, product.id, name)
                product.save(update_fields=["image_url", "updated_at"])
            status_code = 201
            message = "Product added."

        return JsonResponse(
            {
                "message": message,
                "product": serialize_product(product, request),
            },
            status=status_code,
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except (InvalidOperation, ValueError) as e:
        return JsonResponse({"error": f"Valid price, stock, and expiry date are required: {e}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {e}"}, status=500)


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_products", raise_exception=True)
def admin_delete_product(request, product_id):
    return JsonResponse(
        {
            "error": (
                "Permanent product deletion is disabled. "
                "Archive the product to preserve order history."
            )
        },
        status=405,
    )


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_products", raise_exception=True)
def admin_update_product_stock(request, product_id):
    """Update product stock only (not full edit form)."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user), id=product_id
    )
    try:
        data = json.loads(request.body or "{}")
        stock = int(data.get("stock", 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Valid stock quantity is required"}, status=400)

    if stock < 0:
        return JsonResponse({"error": "Stock cannot be negative"}, status=400)

    product.stock = stock
    # Keep a single-option variant in sync when product uses simple variants
    options = product.customization_options or []
    if product.customization_enabled and isinstance(options, list) and len(options) == 1:
        group = options[0] if isinstance(options[0], dict) else None
        opts = (group or {}).get("options") or []
        if len(opts) == 1 and isinstance(opts[0], dict):
            opts[0]["stock"] = stock
            product.customization_options = options

    product.save(update_fields=["stock", "customization_options", "updated_at"])
    return JsonResponse({
        "message": "Stock updated.",
        "product": serialize_product(product, request),
    })


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_products", raise_exception=True)
def admin_archive_product(request, product_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user), id=product_id
    )
    product.archive()
    return JsonResponse({"message": "Product archived.", "id": product.id})


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_products", raise_exception=True)
def admin_restore_product(request, product_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user), id=product_id
    )
    product.unarchive()
    return JsonResponse({"message": "Product restored.", "id": product.id})


@csrf_exempt
def seller_access_request(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        student_id = (data.get("student_id") or "").strip()
        full_name = (data.get("full_name") or "").strip()
        product_type = (data.get("product_type") or "").strip()
        allowed_product_types = {
            "Rice Meals",
            "Snacks",
            "Desserts",
            "Beverages",
            "Combo Meals",
            "Breakfast",
        }

        if not student_id or not full_name or not product_type:
            return JsonResponse(
                {"error": "Student ID, full name, and product type are required"},
                status=400,
            )

        if not re.fullmatch(r"\d{10}", student_id):
            return JsonResponse(
                {"error": "Student ID must be exactly 10 numbers"},
                status=400,
            )

        normalized_full_name = re.sub(r"\s+", " ", full_name).strip()
        if not re.fullmatch(r"[A-Za-z]+(?:[ '-][A-Za-z]+)+", normalized_full_name):
            return JsonResponse(
                {"error": "Full name must include first and last name"},
                status=400,
            )

        course_section = (data.get("course_section") or "").strip()
        if not course_section:
            return JsonResponse(
                {"error": "Course / section is required"},
                status=400,
            )

        if product_type not in allowed_product_types:
            return JsonResponse(
                {"error": "Select a valid product type"},
                status=400,
            )

        seller_request = SellerRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            student_id=student_id,
            full_name=normalized_full_name,
            course_section=course_section,
            contact_number=(data.get("contact_number") or "").strip(),
            product_type=product_type,
            message=(data.get("message") or "").strip(),
        )

        return JsonResponse(
            {
                "message": "Seller access request submitted.",
                "seller_request": serialize_seller_request(seller_request),
            },
            status=201,
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)


def seller_access_status(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    student_id = (request.GET.get("student_id") or "").strip()
    if not student_id:
        return JsonResponse({"error": "Student ID is required"}, status=400)

    seller_request = (
        SellerRequest.objects.filter(student_id=student_id)
        .order_by("-created_at")
        .first()
    )
    if not seller_request:
        return JsonResponse({
            "status": "none",
            "is_approved_seller": False,
        })

    return JsonResponse({
        "status": seller_request.status,
        "is_approved_seller": seller_request.status == SellerRequest.STATUS_APPROVED,
        "seller_request": serialize_seller_request(seller_request),
    })


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_sellers", raise_exception=True)
def marketplace_seller_requests(request):
    seller_requests = SellerRequest.objects.select_related("user", "reviewed_by").all()
    return JsonResponse({
        "seller_requests": [
            serialize_seller_request(seller_request)
            for seller_request in seller_requests
        ]
    })


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_products", raise_exception=True)
def seller_products_monitor(request):
    products = (
        manageable_products_for(request.user)
        .filter(is_archived=False)
        .select_related("seller", "seller__department", "approved_by")
        .order_by("-submitted_at")
    )
    return JsonResponse({"products": [serialize_product(product, request) for product in products]})


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_approve_products", raise_exception=True)
def marketplace_approve_product(request, product_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user), id=product_id
    )
    product.approve(request.user)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "product_id": product.id})
    return redirect(request.META.get("HTTP_REFERER") or "admin_dashboard_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_approve_products", raise_exception=True)
def marketplace_reject_product(request, product_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user), id=product_id
    )
    product.reject(request.user, request.POST.get("rejection_reason", ""))
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "product_id": product.id})
    return redirect("admin_products_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_sellers", raise_exception=True)
def marketplace_approve_seller_request(request, request_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    seller_request = get_object_or_404(SellerRequest, id=request_id)
    seller_request.approve(request.user)
    return redirect(request.META.get("HTTP_REFERER") or "admin_dashboard_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_sellers", raise_exception=True)
def marketplace_reject_seller_request(request, request_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    seller_request = get_object_or_404(SellerRequest, id=request_id)
    seller_request.reject(request.user, request.POST.get("rejection_reason", ""))
    return redirect(request.META.get("HTTP_REFERER") or "admin_dashboard_page")


def serialize_facility(facility):
    from modules.facilities.services.operating_schedule import workflow_for_display

    rate = facility.rate or 0
    facility_type = getattr(facility, "facility_type", None) or Facility.TYPE_OTHER
    type_labels = dict(Facility.TYPE_CHOICES)
    return {
        "id": str(facility.id),
        "name": facility.facility_name,
        "facility_type": facility_type,
        "facility_type_label": type_labels.get(facility_type, "Other"),
        "location": facility.location or "",
        "description": facility.description or "",
        "capacity": facility.capacity,
        "rate": str(rate),
        "price_type": facility.price_type or "hour",
        "price_label": f"\u20b1{rate:,.0f} / {facility.price_type or 'hour'}",
        "booking_mode": facility.booking_mode or "room",
        "rooms_units": facility.rooms_units,
        "room_type": facility.room_type or "",
        "amenities": list(facility.amenities or []),
        "status": normalize_facility_status(facility.availability_status),
        "slots": facility.slots or "",
        "requirements": facility.requirements or "",
        "terms_conditions": facility.terms_conditions or "",
        "workflow_config": workflow_for_display(facility),
        "image_url": facility.get_first_image_url(),
        "images": facility.get_image_list(),
        "created_at": facility.created_at.isoformat() if facility.created_at else "",
    }


def _facility_validation_response(error):
    errors = {
        field: messages[0] if isinstance(messages, list) else str(messages)
        for field, messages in error.message_dict.items()
    }
    first_error = next(iter(errors.values()), "Facility details are invalid.")
    return JsonResponse({"error": first_error, "errors": errors}, status=400)


def _apply_facility_payload(facility, cleaned):
    facility.facility_name = cleaned["name"]
    facility.facility_type = cleaned["facility_type"]
    facility.location = cleaned["location"]
    facility.description = cleaned["description"] or None
    facility.capacity = cleaned["capacity"]
    facility.rate = cleaned["rate"]
    facility.price_type = cleaned["price_type"]
    facility.booking_mode = cleaned["booking_mode"]
    facility.rooms_units = cleaned["rooms_units"]
    facility.room_type = cleaned["room_type"]
    facility.amenities = cleaned["amenities"]
    facility.requirements = cleaned["requirements"] or None
    facility.terms_conditions = cleaned["terms_conditions"] or None
    facility.workflow_config = cleaned["workflow_config"]
    facility.availability_status = cleaned["availability_status"]


def facilities_list(request):
    """Public list endpoint used by the mobile app."""
    facilities = Facility.objects.filter(is_archived=False)
    return JsonResponse(
        {"facilities": [serialize_facility(f) for f in facilities]}
    )


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_facilities", login_url="admin_login_page")
def facilities_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        import uuid
        from datetime import date

        data = json.loads(request.body)
        cleaned = validate_facility_payload(data)

        # Generate ID: CAMFACIL + YYYYMMDD + 4 random hex chars
        today = date.today().strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:4].upper()
        facility_id = f"CAMFACIL{today}{random_suffix}"

        creator = None
        if request.user.is_authenticated:
            creator = CampusHubUser.objects.filter(
                username__iexact=request.user.username
            ).first()
            if creator is None and request.user.email:
                creator = CampusHubUser.objects.filter(
                    email__iexact=request.user.email
                ).first()

        facility = Facility(
            id=facility_id,
            slots=None,
            image_url="",
            created_by_id=creator.id if creator else None,
        )
        _apply_facility_payload(facility, cleaned)
        facility.save(force_insert=True)

        # Save images as files if provided
        raw_images = data.get("images") or data.get("image_url") or ""
        if raw_images:
            saved_images = persist_facility_images(raw_images, facility_id, cleaned["name"])
            if saved_images:
                facility.image_url = json.dumps(saved_images) if len(saved_images) > 1 else saved_images[0]
                facility.save(update_fields=["image_url"])

        return JsonResponse(
            {
                "message": "Facility added.",
                "facility": serialize_facility(facility),
            },
            status=201,
        )
    except ValidationError as error:
        return _facility_validation_response(error)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except (InvalidOperation, ValueError) as error:
        return JsonResponse({"error": f"Facility values are invalid: {error}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_facilities", login_url="admin_login_page")
def facilities_update(request, facility_id):
    if request.method not in ("POST", "PUT", "PATCH"):
        return JsonResponse({"error": "Invalid request method"}, status=405)

    facility = get_object_or_404(Facility, id=facility_id)

    try:
        data = json.loads(request.body)
        cleaned = validate_facility_payload(data, facility=facility)
        _apply_facility_payload(facility, cleaned)

        # Save images as files if provided
        raw_images = data.get("images") or data.get("image_url") or ""
        if raw_images:
            saved_images = persist_facility_images(raw_images, facility_id, cleaned["name"])
            facility.image_url = json.dumps(saved_images) if len(saved_images) > 1 else (saved_images[0] if saved_images else "")
        elif "images" in data or "image_url" in data:
            facility.image_url = ""

        facility.save()

        return JsonResponse(
            {
                "message": "Facility updated.",
                "facility": serialize_facility(facility),
            }
        )
    except ValidationError as error:
        return _facility_validation_response(error)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except (InvalidOperation, ValueError) as error:
        return JsonResponse({"error": f"Facility values are invalid: {error}"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_facilities", raise_exception=True)
def facilities_archive(request, facility_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    facility = get_object_or_404(Facility, id=facility_id)
    facility.archive()
    return JsonResponse({"message": "Facility archived.", "id": facility.id, "success": True})


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_facilities", raise_exception=True)
def facilities_restore(request, facility_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    facility = get_object_or_404(Facility, id=facility_id)
    facility.unarchive()
    return JsonResponse({"message": "Facility restored.", "id": facility.id, "success": True})


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_facilities", raise_exception=True)
def facilities_delete(request, facility_id):
    return JsonResponse(
        {
            "error": (
                "Permanent facility deletion is disabled. "
                "Archive the facility to preserve booking history."
            )
        },
        status=405,
    )


def _serialize_booking_event(booking):
    import re

    purpose = (booking.purpose or "").strip()
    event_type = "reservation"
    type_match = re.match(r"^\[(class|reservation|maintenance|assessment)\]\s*", purpose, re.I)
    if type_match:
        event_type = type_match.group(1).lower()
        purpose = purpose[type_match.end():].strip()

    reserved_by = ""
    reserved_match = re.search(r"(?:^|\n)Reserved by:\s*(.+)$", purpose, re.I | re.M)
    if reserved_match:
        reserved_by = reserved_match.group(1).strip()
        purpose = re.sub(r"(?:^|\n)Reserved by:\s*.+$", "", purpose, flags=re.I | re.M).strip()
    elif booking.user_id:
        user = booking.user
        full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        reserved_by = full_name or getattr(user, "username", "") or ""

    return {
        "id": str(booking.id),
        "type": event_type,
        "facility_id": str(booking.facility_id or ""),
        "facility": booking.facility.facility_name if booking.facility_id else "Facility",
        "date": booking.booking_date.isoformat() if booking.booking_date else "",
        "start": booking.start_time.strftime("%H:%M") if booking.start_time else "",
        "end": booking.end_time.strftime("%H:%M") if booking.end_time else "",
        "reserved_by": reserved_by,
        "purpose": purpose,
        "status": booking.status,
    }


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_book_facilities", login_url="admin_dashboard_page")
def bookings_create(request):
    """
    Create a facility booking/schedule entry.
    Requires authenticated admin with facility module access.
    CSRF protected (send X-CSRFToken).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if not user_has_facility_module_access(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        import uuid
        from datetime import date, datetime

        data = json.loads(request.body or "{}")
        facility_id = (data.get("facility_id") or "").strip()
        event_type = (data.get("type") or "reservation").strip().lower()
        booking_date_raw = (data.get("date") or "").strip()
        start_raw = (data.get("start") or "").strip()
        end_raw = (data.get("end") or "").strip()
        purpose_text = (data.get("purpose") or data.get("description") or "").strip()
        reserved_by = (data.get("reserved_by") or "").strip()

        valid_types = {"class", "reservation", "maintenance", "assessment"}
        if event_type not in valid_types:
            event_type = "reservation"

        if not facility_id:
            return JsonResponse({"error": "Facility is required."}, status=400)
        if not booking_date_raw or not start_raw or not end_raw:
            return JsonResponse({"error": "Date, start time, and end time are required."}, status=400)
        if event_type == "reservation" and not reserved_by:
            return JsonResponse({"error": "Reserved by is required for reservations."}, status=400)

        facility = Facility.objects.filter(id=facility_id).first()
        if facility is None:
            return JsonResponse({"error": "Facility not found."}, status=404)

        try:
            booking_date = date.fromisoformat(booking_date_raw)
            start_time = datetime.strptime(start_raw[:5], "%H:%M").time()
            end_time = datetime.strptime(end_raw[:5], "%H:%M").time()
        except ValueError:
            return JsonResponse({"error": "Invalid date or time format."}, status=400)

        if start_time >= end_time:
            return JsonResponse({"error": "End time must be later than start time."}, status=400)

        purpose_parts = [f"[{event_type}]"]
        if purpose_text:
            purpose_parts.append(purpose_text)
        if reserved_by:
            purpose_parts.append(f"Reserved by: {reserved_by}")
        purpose = "\n".join(purpose_parts)

        today = date.today().strftime("%Y%m%d")
        booking_id = f"CAMBOOK{today}{uuid.uuid4().hex[:4].upper()}"

        booking = Booking(
            id=booking_id,
            facility=facility,
            purpose=purpose,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            status=Booking.STATUS_APPROVED if event_type != "reservation" else Booking.STATUS_PENDING,
            total_amount=0,
        )
        from modules.facilities.services.mobile_booking import conflicting_bookings
        with transaction.atomic():
            Facility.objects.select_for_update().get(pk=facility.pk)
            if conflicting_bookings(facility, booking_date, start_time, end_time).exists():
                return JsonResponse({"error": "This schedule conflicts with an existing booking or blocked period."}, status=409)
            booking.save(force_insert=True)
        booking = Booking.objects.select_related("facility", "user").get(id=booking_id)
        return JsonResponse(
            {"message": "Booking saved.", "event": _serialize_booking_event(booking)},
            status=201,
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def _parse_json(request):
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return None


def _generate_reset_code() -> str:
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def _get_active_reset(email: str):
    return (
        PasswordResetCode.objects.filter(
            email__iexact=email,
            used=False,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )


@csrf_exempt
def mobile_password_reset(request):
    """POST { email } — generate code and send via Gmail SMTP."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    data = _parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return JsonResponse({"error": "Enter a valid email address."}, status=400)

    user = CampusHubUser.objects.filter(email__iexact=email).first()
    if user is None:
        # Do not reveal whether email exists (security)
        return JsonResponse(
            {
                "message": "If that email is registered, check Gmail for the 6-digit code.",
                "email_sent": True,
                "step": 2,
            }
        )

    code = _generate_reset_code()
    PasswordResetCode.objects.filter(email__iexact=email, used=False).update(used=True)
    PasswordResetCode.objects.create(
        email=email,
        code_hash=make_password(code),
        expires_at=timezone.now()
        + timedelta(minutes=settings.PASSWORD_RESET_CODE_MINUTES),
    )

    full_name = f"{user.first_name} {user.last_name}".strip()
    email_sent = False
    email_error = ""
    try:
        email_sent = send_password_reset_email(
            to_email=email,
            code=code,
            full_name=full_name,
        )
    except Exception as exc:
        email_sent = False
        email_error = str(exc)

    if not email_sent:
        if not is_gmail_configured():
            return JsonResponse(
                {
                    "error": (
                        "Gmail is not set up. Open backend/core/core/gmail_local.py "
                        "and paste your 16-character Google App Password, then restart Django."
                    ),
                },
                status=503,
            )
        detail = email_error or "Check App Password and 2-Step Verification on Gmail."
        return JsonResponse(
            {"error": f"Could not send email to Gmail. {detail}"},
            status=503,
        )

    return JsonResponse(
        {
            "message": "A 6-digit code was sent to your Gmail. Check Inbox and Spam.",
            "email_sent": True,
            "step": 2,
        }
    )


@csrf_exempt
def mobile_password_reset_verify(request):
    """POST { email, code } — verify 6-digit code."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    data = _parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or len(code) != 6 or not code.isdigit():
        return JsonResponse({"error": "Email and 6-digit code are required."}, status=400)

    reset_row = _get_active_reset(email)
    if reset_row is None or not check_password(code, reset_row.code_hash):
        return JsonResponse({"error": "Invalid or expired code."}, status=400)

    return JsonResponse({"message": "Code verified. You may set a new password."})


@csrf_exempt
def mobile_password_reset_confirm(request):
    """POST { email, code, new_password, confirm_password } — update password."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    data = _parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not email or len(code) != 6:
        return JsonResponse({"error": "Email and code are required."}, status=400)

    password_error = _password_validation_error(new_password)
    if password_error:
        return JsonResponse({"error": password_error}, status=400)

    if new_password != confirm_password:
        return JsonResponse({"error": "Passwords do not match."}, status=400)

    reset_row = _get_active_reset(email)
    if reset_row is None or not check_password(code, reset_row.code_hash):
        return JsonResponse({"error": "Invalid or expired code."}, status=400)

    user = CampusHubUser.objects.filter(email__iexact=email).first()
    if user is None:
        return JsonResponse({"error": "Account not found."}, status=404)

    user.password_hash = make_password(new_password)
    user.save(update_fields=["password_hash", "updated_at"])
    reset_row.used = True
    reset_row.save(update_fields=["used"])

    return JsonResponse({"message": "Password updated successfully."})


@csrf_exempt
def recommended_products(request):
    """
    GET ?user_id=1&limit=8&product_id=5
    ML-powered product recommendations (TF-IDF + cosine similarity).
    """
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    user_id = request.GET.get("user_id")
    seed_product_id = request.GET.get("product_id")
    limit = request.GET.get("limit", "8")

    try:
        limit_n = max(1, min(int(limit), 20))
    except ValueError:
        limit_n = 8

    uid = int(user_id) if user_id and str(user_id).isdigit() else None
    pid = int(seed_product_id) if seed_product_id and str(seed_product_id).isdigit() else None

    products = get_recommended_products(
        user_id=uid,
        limit=limit_n,
        seed_product_id=pid,
    )

    return JsonResponse(
        {
            "products": [serialize_product(p, request) for p in products],
            "engine": "scikit-learn-tfidf-cosine",
            "user_id": uid,
            "seed_product_id": pid,
        }
    )


@csrf_exempt
def marketplace_orders(request):
    if request.method == "GET":
        user_id = request.GET.get("user_id")
        orders = MarketplaceOrder.objects.select_related("product").all()
        if user_id and str(user_id).isdigit():
            orders = orders.filter(buyer_user_id=int(user_id))
        return JsonResponse({"orders": [serialize_marketplace_order(o) for o in orders]})

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    data = _parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    product_id = data.get("product_id")
    quantity = max(int(data.get("quantity") or 1), 1)
    option = (data.get("option") or "").strip()
    buyer_user_id = data.get("buyer_user_id")
    buyer_name = (data.get("buyer_name") or "").strip()
    buyer_email = (data.get("buyer_email") or "").strip()
    message_to_seller = (data.get("message_to_seller") or "").strip()

    if len(message_to_seller) > 300:
        return JsonResponse(
            {"error": "Message to seller must be 300 characters or fewer."},
            status=400,
        )

    resolved_buyer_id = int(buyer_user_id) if str(buyer_user_id).isdigit() and int(buyer_user_id) > 0 else None
    if not resolved_buyer_id:
        return JsonResponse({"error": "A valid buyer account is required."}, status=400)

    campus_buyer = CampusHubUser.objects.filter(id=resolved_buyer_id).first()
    django_buyer = User.objects.filter(id=resolved_buyer_id).first()
    if not campus_buyer and not django_buyer:
        return JsonResponse({"error": "Buyer account not found."}, status=400)

    if not buyer_name and resolved_buyer_id:
        if campus_buyer:
            buyer_name = f"{campus_buyer.first_name} {campus_buyer.last_name}".strip() or campus_buyer.username
            if not buyer_email:
                buyer_email = campus_buyer.email or ""
        elif django_buyer:
            buyer_name = (
                django_buyer.get_full_name().strip()
                or django_buyer.username
                or ""
            )
            if not buyer_email:
                buyer_email = django_buyer.email or ""

    try:
        with transaction.atomic():
            product = Product.objects.select_for_update().select_related("seller").filter(
                id=product_id,
                approval_status=Product.STATUS_APPROVED,
                is_archived=False,
            ).first()
            if product is None:
                return JsonResponse({"error": "Product not found."}, status=404)

            base_price = Decimal(product.price)
            selections: list[dict] = []
            customization_payload: dict = {}
            option_summary = option

            if product.customization_enabled:
                raw_selections = data.get("customization")
                if raw_selections is None and option:
                    raw_selections = [{"group": "Option", "option": option, "extra_price": "0"}]
                selections = parse_order_selections(raw_selections)
                validated, extra_total, error = validate_order_selections(
                    product.customization_options or [], selections
                )
                if error:
                    return JsonResponse({"error": error}, status=400)
                customization_payload = build_order_customization_payload(validated)
                option_summary = customization_payload.get("summary") or option
                unit_price = (base_price + extra_total).quantize(Decimal("0.01"))
                selections = validated
            else:
                unit_price = base_price

            adjust_product_stock(product, selections, quantity)
            product.save(update_fields=["stock", "customization_options", "updated_at"])
            total_price = (unit_price * quantity).quantize(Decimal("0.01"))
            seller_name = product.seller.get_full_name() or product.seller.username

            order = MarketplaceOrder.objects.create(
                product=product,
                buyer_user_id=resolved_buyer_id,
                buyer_name=buyer_name or "Unknown customer",
                buyer_email=buyer_email,
                product_name=product.name,
                category=product.category,
                seller_name=seller_name,
                seller_contact=product.seller.email,
                message_to_seller=message_to_seller,
                option=option_summary,
                customization=customization_payload,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                image_url=serialize_product(product, request).get("image_url", ""),
                inventory_deducted=True,
            )

            ProductInteraction.objects.create(
                user_id=order.buyer_user_id,
                product=product,
                interaction_type=ProductInteraction.INTERACTION_PURCHASE,
            )
    except InsufficientStockError as exc:
        return JsonResponse({"error": str(exc)}, status=409)

    return JsonResponse(
        {
            "message": "Order placed.",
            "order": serialize_marketplace_order(order),
        },
        status=201,
    )


@csrf_exempt
def track_product_interaction(request):
    """POST { user_id, product_id, interaction_type } — feeds ML model."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    data = _parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    user_id = data.get("user_id")
    product_id = data.get("product_id")
    interaction_type = (data.get("interaction_type") or ProductInteraction.INTERACTION_VIEW).strip()

    if not user_id or not product_id:
        return JsonResponse({"error": "user_id and product_id are required."}, status=400)

    valid_types = {c[0] for c in ProductInteraction.INTERACTION_CHOICES}
    if interaction_type not in valid_types:
        return JsonResponse({"error": "Invalid interaction_type."}, status=400)

    product = Product.objects.filter(
        id=product_id,
        approval_status=Product.STATUS_APPROVED,
    ).first()
    if product is None:
        return JsonResponse({"error": "Product not found."}, status=404)

    ProductInteraction.objects.create(
        user_id=int(user_id),
        product=product,
        interaction_type=interaction_type,
    )

    return JsonResponse({"message": "Interaction recorded."}, status=201)


@csrf_exempt
def remove_product_background(request):
    """
    AI-powered background removal endpoint.
    Accepts multipart/form-data ('image' or 'file') or JSON ({'image_data': 'data:image/...;base64,...'}).
    Returns {'success': True, 'image_data': 'data:image/png;base64,...'}.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        from modules.marketplace.services.image_processing import (
            is_rembg_available,
            remove_background_from_bytes,
            remove_background_from_data_url,
        )

        if not is_rembg_available():
            return JsonResponse(
                {"error": "Background removal engine (rembg) is not available on this server."},
                status=503,
            )

        # Check if multipart file uploaded
        if "image" in request.FILES or "file" in request.FILES:
            uploaded = request.FILES.get("image") or request.FILES.get("file")
            image_bytes = uploaded.read()
            png_bytes, _ = remove_background_from_bytes(image_bytes)
            b64_output = base64.b64encode(png_bytes).decode("ascii")
            return JsonResponse({
                "success": True,
                "image_data": f"data:image/png;base64,{b64_output}",
            })

        # Otherwise parse JSON payload
        data = _parse_json(request)
        if not data or "image_data" not in data:
            return JsonResponse({"error": "No image or image_data provided in request."}, status=400)

        raw_data_url = data.get("image_data", "").strip()
        if not raw_data_url:
            return JsonResponse({"error": "Empty image_data provided."}, status=400)

        result_data_url = remove_background_from_data_url(raw_data_url)
        return JsonResponse({
            "success": True,
            "image_data": result_data_url,
        })

    except Exception as exc:
        return JsonResponse({
            "success": False,
            "error": f"Background removal failed: {str(exc)}"
        }, status=500)
