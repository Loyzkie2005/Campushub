from accounts.role_permissions import admin_read_permissions
from modules.marketplace.services.fifo import order_request as fifo_order_request
from modules.marketplace.services.fulfillment import fulfillment_buyer_guard
from modules.facilities.services.activity import facility_activity_row, facility_snapshot, record_facility_activity
import base64
import binascii
import json
import logging
import random
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_variables
import jwt
from jwt import InvalidTokenError

from accounts.admin_tab_auth import (
    append_tab_token_to_url,
    create_admin_tab_token,
    get_tab_token_from_request,
    revoke_admin_tab_token,
)
from accounts.activity_logging import log_account_activity, log_marketplace_event, log_seller_event
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
    get_product_inventory_snapshot,
    get_product_quantity_status,
    product_variant_items,
    validate_low_stock_threshold,
    InventoryThresholdError,
    InventoryStockError,
    validate_stock_quantity,
    validate_inventory_option_changes,
    get_variant_stock_summary,
    customization_has_stock_tracking,
    sync_product_inventory_fields,
    is_perishable_category,
    is_marketplace_available,
    low_stock_threshold,
    parse_expiry_date,
    PERISHABLE_CATEGORIES,
)
from .product_images import (
    validate_product_images,
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
    from accounts.academic import academic_labels
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
        **academic_labels(user.department, user.major),
        "is_active": user.is_active,
        "is_suspended": user.is_suspended,
        "institutional_id": user.institutional_id,
        "contact_number": user.contact_number,
        "year_section": user.year_section,
        "profile_photo_url": user.profile_photo.url if user.profile_photo else "",
        "profile_completed": user.profile_completed,
        "email_verified": user.email_verified,
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
    # Reuse verified claims for consumers such as push registration expiry.
    request.mobile_auth_claims = claims
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


def serialize_product(product, request=None, *, include_inventory=False):
    from modules.marketplace.services.bundles import is_bundle, bundle_inventory
    from accounts.academic import product_academic
    from modules.marketplace.services.inventory import inventory_sku
    image_url = ""
    images = []
    seller_photo = getattr(product.owner, "profile_photo", None)
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

    payload = {
        "id": product.id,
        "product_code": product.product_code or f"PRD-{product.pk:04d}",
        "sku": inventory_sku(product),
        **product_academic(product),
        "seller_id": product.owner_key,
        "seller_ref": product.owner_ref,
        "seller_photo_url": seller_photo.url if seller_photo else "",
        "seller": product.owner.get_full_name().strip()
        or product.owner.username,
        "department": str(product.department) if product.department_id else (str(product.owner.department) if getattr(product.owner, "department_id", None) else ""),
        "name": product.name,
        "department_id": product.department_id,
        "tags": product.tags,
        "product_type": product.product_type,
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
        "low_stock_threshold": None if is_bundle(product) or product_variant_items(product) else low_stock_threshold(product),
        **get_variant_stock_summary(product),
        "quantity_status": get_product_quantity_status(product),
        "is_perishable": is_perishable_category(product.category),
        "perishable_categories": sorted(PERISHABLE_CATEGORIES),
        "image_url": image_url,
        "images": images,
        "seller_contact": product.owner.email,
        "approval_status": product.approval_status,
        "rejection_reason": product.rejection_reason,
        "submitted_at": product.submitted_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
        "customization_enabled": bool(product.customization_enabled),
        "customization_options": product.customization_options or [],
        "is_archived": bool(getattr(product, "is_archived", False)),
    }
    if is_bundle(product):
        payload["bundle"] = bundle_inventory(product)
    if include_inventory:
        payload["inventory"] = get_product_inventory_snapshot(product)
        payload["can_view_stock_movements"] = request is None or any(request.user.has_perm("accounts." + code) for code in ("can_manage_products", "can_approve_products", "can_view_stock_movements"))
    if include_inventory and (request is None or request.user.has_perm("accounts.can_manage_products") or request.user.has_perm("accounts.can_approve_products") or request.user.has_perm("accounts.can_view_stock_movements")):
        from modules.marketplace.services.inventory_monitor import inventory_movements
        payload["stock_movements"] = []
        for sku in product.inventory_skus.all():
            for event in inventory_movements(sku):
                payload["stock_movements"].append({**event, "date": event["date"].isoformat(), "sku": sku.code})
        payload["stock_movements"] = sorted(payload["stock_movements"], key=lambda event: event["date"], reverse=True)[:100]
    return payload


def manageable_products_for(user):
    from modules.marketplace.services.product_access import admin_product_queryset

    return admin_product_queryset(user)


def serialize_marketplace_order(order):
    from modules.marketplace.services.fulfillment import presentation
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
        **presentation(order),
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
        "is_suspended": seller_request.is_suspended,
        "seller_access": "suspended" if seller_request.is_suspended and seller_request.status == "approved" else seller_request.status,
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
    # Older installed clients omit this optional field; preserve their saved value.
    year_section = data.get("year_section", user.year_section)
    if not isinstance(year_section, str) or len(year_section.strip()) > 120:
        return JsonResponse({"error": "Year / Section must be text of up to 120 characters."}, status=400)
    year_section = year_section.strip()
    validation_error = _validate_mobile_profile(
        user_type,
        profile_id,
        contact_number,
    )
    if validation_error:
        return JsonResponse({"error": validation_error}, status=400)

    from accounts.academic import resolve_account_academic
    try:
        program, major = resolve_account_academic("User", user_type,
            data.get("program_id", data.get("department_id", user.department_id)),
            data.get("major_id", user.major_id),
            existing=user if user.profile_completed and user.user_type == user_type else None)
    except (ValueError, TypeError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

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
    user.year_section = year_section
    user.department, user.major = program, major
    user.profile_completed = True
    user.save(
        update_fields=[
            "user_type",
            "student_id",
            "institutional_id",
            "contact_number",
            "year_section",
            "department",
            "major",
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
@never_cache
def mobile_profile_photo(request):
    """Read the current profile or replace only the authenticated owner's photo."""
    if request.method not in {"GET", "POST"}:
        return JsonResponse({"error": "GET or POST required."}, status=405)
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    if request.method == "GET":
        return JsonResponse({"user": serialize_campushub_user(user)})

    from uuid import uuid4
    from .profile_photos import normalize_profile_photo
    try:
        content = normalize_profile_photo(request.FILES.get("photo"))
    except ValidationError as exc:
        return JsonResponse({"error": exc.messages[0]}, status=400)

    storage = user.profile_photo.storage
    saved_name = None
    try:
        with transaction.atomic():
            user = CampusHubUser.objects.select_for_update().get(pk=user.pk)
            if not user.is_active or user.is_suspended:
                return JsonResponse({"error": "This account is inactive or suspended."}, status=403)
            old_name = user.profile_photo.name
            saved_name = storage.save(f"profile-photos/{user.pk}/{uuid4().hex}.jpg", content)
            user.profile_photo = saved_name
            user.save(update_fields=["profile_photo", "updated_at"])

            def remove_previous():
                if old_name and old_name.startswith(f"profile-photos/{user.pk}/"):
                    try:
                        storage.delete(old_name)
                    except Exception:
                        logging.getLogger(__name__).warning("Could not remove the previous profile photo.", exc_info=True)

            transaction.on_commit(remove_previous)
    except Exception:
        if saved_name:
            storage.delete(saved_name)
        raise
    return JsonResponse({"message": "Profile picture updated.", "user": serialize_campushub_user(user)})


def mobile_academic_options(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET required."}, status=405)
    from accounts.academic import academic_options
    programs, majors = academic_options()
    return JsonResponse({"programs": list(programs.values("id", "code", "name")),
                         "majors": list(majors.values("id", "program_id", "code", "name"))})


@csrf_exempt
def seller_submit_product(request):
    from modules.marketplace.services.seller_applications import applicant, latest
    if request.method not in {"GET", "POST"}:
        return JsonResponse({"error": "Invalid request method"}, status=405)
    # Existing web administrators keep their established product-management access.
    is_web_manager = request.user.is_authenticated and request.user.is_active and (
        request.user.is_superuser or request.user.has_perm("accounts.can_manage_products"))
    if is_web_manager:
        account, source = request.user, "admin"
    else:
        account, source, error = applicant(request, allow_seller=True)
        if error is not None:
            return error
        application = latest(account, source)
        if not application or application.status != "approved" or application.is_suspended:
            return JsonResponse({"error": "Approved active seller access is required."}, status=403)
    owned = Product.objects.filter(mobile_seller=account) if source == "mobile" else Product.objects.filter(seller=account)
    if request.method == "GET":
        return JsonResponse({"products": [serialize_product(row, request) for row in owned.select_related(
            "seller", "seller__department", "seller__major", "mobile_seller", "mobile_seller__department", "mobile_seller__major", "department", "major").order_by("-submitted_at")]})
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError("Submit a valid product form.")
        # Bundles use the same recipe validator/approval model as web products.
        from modules.marketplace.services.bundles import validate_recipe
        from api.models import BundleComponent
        product_type = data.get("product_type", Product.TYPE_SINGLE)
        if product_type not in {Product.TYPE_SINGLE, Product.TYPE_BUNDLE}:
            raise ValueError("Select a valid product type.")
        is_bundle_product = product_type == Product.TYPE_BUNDLE
        if is_bundle_product and (data.get("stock") not in (None, "", 0, "0") or
                data.get("low_stock_threshold") not in (None, "") or data.get("customization_options") or data.get("customization_enabled")):
            raise ValueError("Bundle availability comes from components. Do not enter standalone stock, threshold, or variants.")
        name = (data.get("name") or "").strip()
        price = Decimal(str(data.get("price", "")))
        stock = validate_stock_quantity(data.get("stock", 0))
        threshold = validate_low_stock_threshold(data.get("low_stock_threshold"), stock=stock) if data.get("low_stock_threshold") is not None else None
        category = (data.get("category") or "").strip()
        expiry_date = parse_expiry_date(data.get("expiry_date"))
        if not name or len(name) > 150 or not price.is_finite() or price < 0 or price > Decimal("99999999.99") or price != price.quantize(Decimal("0.01")):
            raise ValueError("Enter a product name and a valid non-negative price with at most two decimal places.")
        if source == "mobile":
            from modules.marketplace.services.seller_applications import categories
            if category not in categories():
                raise ValueError("Select an existing marketplace category.")
        from accounts.academic import resolve_academic
        program, major = resolve_academic(account.department_id or (application.application_data.get("program_id") if not is_web_manager else None), account.major_id or (application.application_data.get("major_id") if not is_web_manager else None), required=True)
        raw_tags = data.get("tags")
        if raw_tags:
            if isinstance(raw_tags, str):
                raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            tags = list(dict.fromkeys(str(t).strip()[:60] for t in raw_tags if str(t).strip()))[:30]
        else:
            tags = []
        # New gallery payload shares the admin image storage helper. Keep the
        # legacy single-image field available to existing callers.
        raw_images = validate_product_images(data["images"]) if "images" in data else None
        raw_image = ""
        if raw_images is None:
            raw_image = data.get("image_url") or ""
            if not isinstance(raw_image, str):
                raise ValueError("Select a valid product image.")
            raw_image = raw_image.strip()
            # Older callers can encode galleries in this existing text field.
            # Apply the same gallery limit instead of accepting a bypass.
            if raw_image.startswith("["):
                raw_images = validate_product_images(json.loads(raw_image))
        with transaction.atomic():
            # Serialize application review/revocation against listing creation.
            if not is_web_manager:
                application = SellerRequest.objects.select_for_update(of=("self",)).get(pk=application.pk)
                if application.status != "approved" or application.is_suspended:
                    return JsonResponse({"error": "Approved active seller access is required."}, status=403)
            recipe = validate_recipe(data.get("bundle_components"), f"mobile:{account.pk}" if source == "mobile" else account.pk) if is_bundle_product else []
            if is_bundle_product and source == "mobile":
                from modules.marketplace.services.bundle_suggestions import build_bundle_suggestions
                try:
                    pair_ids = sorted(int(value) for value in str(data.get("suggestion_id", "")).split("|"))
                except ValueError:
                    raise ValueError("Choose a current bundle suggestion.")
                if len(pair_ids) != 2 or len(set(pair_ids)) != 2 or set(pair_ids) != {row["product"].pk for row in recipe}:
                    raise ValueError("Use both products from the selected suggestion.")
                result = build_bundle_suggestions(None, mobile_seller=account)
                if result["error"]:
                    return JsonResponse({"error": "Unable to verify this suggestion. Retry."}, status=503)
                if not any(sorted(int(product["id"]) for product in row["products"]) == pair_ids for row in result["rows"]):
                    raise ValueError("This suggestion no longer qualifies. Refresh Suggested Product Bundles.")
            product = Product.objects.create(
                seller=account if source == "admin" else None,
                mobile_seller=account if source == "mobile" else None,
                department=program, major=major, name=name,
                description=(data.get("description") or "").strip(), category=category,
                price=price, product_type=product_type, stock=0 if is_bundle_product else stock,
                low_stock_threshold=None if is_bundle_product else threshold,
                tags=tags,
                expiry_date=expiry_date if not is_bundle_product and is_perishable_category(category) else None,
                approval_status=Product.STATUS_APPROVED if is_web_manager else Product.STATUS_PENDING,
                approved_by=request.user if is_web_manager else None,
                approved_at=timezone.now() if is_web_manager else None)
            if recipe:
                BundleComponent.objects.bulk_create([BundleComponent(bundle=product, **row) for row in recipe])
            if is_bundle_product and source == "mobile":
                from modules.marketplace.services.bundle_monitoring import link_created_bundle
                link_created_bundle(request, product, pair_ids)
            if raw_images is not None:
                urls = persist_product_images(raw_images, product.pk, name)
                product.image_url = json.dumps(urls) if urls else ""
                product.save(update_fields=["image_url", "updated_at"])
            elif raw_image:
                product.image_url = persist_product_image(raw_image, product.pk, name)
                product.save(update_fields=["image_url", "updated_at"])
            log_marketplace_event(request, account=account, source=source, activity_type="PRODUCT_SUBMITTED",
                activity=f"Product submitted: {product.name}", metadata={"product_id": product.pk})
        return JsonResponse({"message": "Product submitted for marketplace approval.", "product": serialize_product(product, request)}, status=201)
    except (ValueError, TypeError, InvalidOperation, ValidationError) as error:
        return JsonResponse({"error": str(error)}, status=400)


def approved_products(request):
    from modules.marketplace.services.bundles import prime_bundle_inventory
    today = timezone.localdate()
    products = Product.objects.filter(
        approval_status=Product.STATUS_APPROVED,
        is_archived=False,
    ).filter(
        Q(product_type=Product.TYPE_BUNDLE) | Q(stock__gt=0),
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    )
    return JsonResponse(
        {"products": [serialize_product(product, request) for product in prime_bundle_inventory(products.select_related("mobile_seller", "mobile_seller__department", "mobile_seller__major", "seller", "seller__department", "department")) if is_marketplace_available(product)]}
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
@transaction.atomic
def admin_save_product(request):
    from django.http import Http404
    from uuid import uuid4
    from modules.marketplace.services.admin_product_validation import ProductInputError, validate_admin_product_input
    from modules.marketplace.services.bundles import BundleError, validate_recipe, recipe_rows
    from api.models import BundleComponent
    from accounts.models import Department
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    if not request.user.has_perm("accounts.can_manage_products"):
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        data = validate_admin_product_input(json.loads(request.body))
        product_id = data.get("id")
        seller_id = data.get("seller_id")
        existing_product = get_object_or_404(manageable_products_for(request.user).select_for_update(of=("self",)), id=product_id) if product_id else None
        product_type = data.get("product_type", existing_product.product_type if existing_product else Product.TYPE_SINGLE)
        if product_type not in {Product.TYPE_SINGLE, Product.TYPE_BUNDLE}:
            raise BundleError("Select a valid product type.")
        is_bundle_product = product_type == Product.TYPE_BUNDLE

        # Verify if a specific seller_id was provided to assign the listing to
        target_seller = None
        if seller_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            target_seller = CampusHubUser.objects.filter(pk=str(seller_id).split(":", 1)[1]).first() if str(seller_id).startswith("mobile:") else User.objects.filter(id=seller_id).first() if str(seller_id).isdecimal() else User.objects.filter(username=str(seller_id)).first()
            if not target_seller:
                target_seller = User.objects.filter(username=str(seller_id)).first()
            if not target_seller or not target_seller.is_active:
                return JsonResponse({"error": "Selected seller could not be found."}, status=400)
        owner = target_seller or (existing_product.owner if existing_product else request.user)
        from accounts.academic import resolve_academic, scope_users
        from accounts.models import User
        if not (existing_product and existing_product.mobile_seller_id and owner == existing_product.owner) and not scope_users((CampusHubUser if isinstance(owner, CampusHubUser) else User).objects.filter(pk=owner.pk), request.user).exists():
            return JsonResponse({"error": "The selected owner is outside your program/major scope."}, status=403)
        
        name = (data.get("name") or "").strip()
        price = Decimal(str(data.get("price", "")))
        if not price.is_finite() or price < 0 or price > Decimal("99999999.99") or price != price.quantize(Decimal("0.01")):
            raise ValueError("Price must be a non-negative amount with at most two decimal places.")
        stock = 0  # Parent stock is derived after options are inspected.
        category = (data.get("category") or "").strip()
        expiry_date = parse_expiry_date(data.get("expiry_date"))

        if not name:
            return JsonResponse({"error": "Product name is required"}, status=400)

        raw_image = (data.get("image_url") or "").strip()
        raw_images = data.get("images")  # JSON array of base64 strings
        customization_enabled = bool(data.get("customization_enabled"))
        if is_bundle_product and (data.get("customization_options") or data.get("customization_enabled") or data.get("low_stock_threshold") not in (None, "") or data.get("stock") not in (None, "", 0, "0")):
            raise BundleError("Bundle availability comes from components. Do not enter standalone stock, threshold, or variants.")
        customization_options = normalize_customization_options(
            data.get("customization_options")
        )
        if not customization_enabled:
            customization_options = []
        elif customization_options:
            customization_enabled = True

        old_options = {
            ((group.get("name") or ""), (option.get("name") or "")): option
            for group in (existing_product.customization_options or [] if existing_product else [])
            for option in group.get("options") or []
        }
        for group in customization_options:
            for option in group["options"]:
                old = old_options.get((group["name"], option["name"]), {})
                if "low_stock_threshold" not in option and "low_stock_threshold" in old:
                    option["low_stock_threshold"] = old["low_stock_threshold"]
                if "image" not in option and "image" in old:
                    option["image"] = old["image"]
                if "low_stock_threshold" in option:
                    option["low_stock_threshold"] = validate_low_stock_threshold(
                        option["low_stock_threshold"], stock=option["stock"],
                        initial=not existing_product or not old,
                    )

        recipe = validate_recipe(data.get("bundle_components"), f"mobile:{owner.pk}" if isinstance(owner, CampusHubUser) else owner.pk, bundle_id=product_id) if is_bundle_product else []
        if existing_product:
            structural_change = existing_product.product_type != product_type or existing_product.owner != owner
            if structural_change:
                from modules.marketplace.services.inventory import active_inventory_reservations
                if any(active_inventory_reservations(existing_product)):
                    raise BundleError("Complete or cancel component reservations before changing this product's owner or type.")
            old_recipe = [(row.product_id, row.required_quantity, sorted((s["group"], s["option"]) for s in row.selections)) for row in recipe_rows(existing_product)]
            new_recipe = [(row["product"].pk, row["required_quantity"], sorted((s["group"], s["option"]) for s in row["selections"])) for row in recipe]
            recipe_change = sorted(old_recipe) != sorted(new_recipe)
            active_orders = MarketplaceOrder.objects.filter(product=existing_product, inventory_deducted=True, inventory_restored=False, status__in=(MarketplaceOrder.STATUS_PENDING, MarketplaceOrder.STATUS_PROCESSING, MarketplaceOrder.STATUS_READY_FOR_PICKUP))
            if (structural_change or recipe_change) and active_orders.exists():
                raise BundleError("Complete or cancel reserved orders before changing the product type, owner, or bundle components.")
            if structural_change and existing_product.used_in_bundles.filter(bundle__is_archived=False).exists():
                raise BundleError("Update the referencing bundles before changing this component's owner or product type.")
            validate_inventory_option_changes(existing_product, customization_options)
        if not customization_options and not is_bundle_product:
            stock = validate_stock_quantity(data.get("stock", 0))
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
            "product_type": product_type,
            "name": name,
            "description": (data.get("description") or "").strip(),
            "category": category,
            "price": price,
            "stock": max(stock, 0),
            "expiry_date": expiry_date if is_perishable_category(category) else None,
            "customization_enabled": customization_enabled,
            "customization_options": customization_options,
        }
        if stock > 2147483647:
            raise ProductInputError("Combined variant stock exceeds the supported inventory limit.", "customization_options")
        program_id = data.get("program_id", data.get("department_id", existing_product.department_id if existing_product and existing_product.department_id else owner.department_id))
        major_id = data.get("major_id", existing_product.major_id if existing_product and existing_product.department_id else owner.major_id)
        program, major = resolve_academic(program_id, major_id, required=True)
        if owner.department_id and (program.pk != owner.department_id or (owner.major_id and (not major or major.pk != owner.major_id))):
            raise ValueError("Product program and major must match its assigned seller.")
        if not request.user.is_superuser and (program.pk != request.user.department_id or (request.user.major_id and (not major or major.pk != request.user.major_id))):
            return JsonResponse({"error": "This program/major is outside your assigned scope."}, status=403)
        fields.update(department=program, major=major)
        if "tags" in data:
            tags = data["tags"]
            if isinstance(tags, str):
                tags = tags.split(",")
            if not isinstance(tags, list) or len(tags) > 30:
                raise ValueError("Tags must be a list with at most 30 entries.")
            fields["tags"] = list(dict.fromkeys(str(tag).strip()[:60] for tag in tags if str(tag).strip()))
        if is_bundle_product:
            fields.update(stock=0, low_stock_threshold=None, expiry_date=None, customization_enabled=False, customization_options=[])
        elif customization_options:
            fields["low_stock_threshold"] = None  # Inventory is tracked by option, not parent.
        elif "low_stock_threshold" in data:
            fields["low_stock_threshold"] = validate_low_stock_threshold(
                data["low_stock_threshold"], stock=stock, initial=not existing_product,
            )

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

        image_name = f"{name}_{uuid4().hex}"  # Failed saves must not overwrite already referenced files.
        if product_id:
            product = existing_product
            for field, value in fields.items():
                setattr(product, field, value)
            product.stock = fields["stock"]
            product.expiry_date = fields["expiry_date"]
            if raw_images is not None:
                urls = persist_product_images(raw_images, product.id, image_name)
                product.image_url = json.dumps(urls) if urls else ""
            elif raw_image and _should_update_product_image(raw_image):
                product.image_url = persist_product_image(raw_image, product.id, image_name)
                
            if target_seller:
                product.seller = None if isinstance(target_seller, CampusHubUser) else target_seller
                product.mobile_seller = target_seller if isinstance(target_seller, CampusHubUser) else None
                
            product._inventory_actor = request.user.get_full_name().strip() or request.user.username
            product.save()
            status_code = 200
            message = "Product updated."
        else:
            product = Product.objects.create(
                seller=None if isinstance(owner, CampusHubUser) else owner,
                mobile_seller=owner if isinstance(owner, CampusHubUser) else None,
                created_by=request.user,
                image_url="",
                **fields,
            )
            if raw_images is not None:
                urls = persist_product_images(raw_images, product.id, image_name)
                if urls:
                    product.image_url = json.dumps(urls)
                    product.save(update_fields=["image_url", "updated_at"])
            elif raw_image:
                product.image_url = persist_product_image(raw_image, product.id, image_name)
                product.save(update_fields=["image_url", "updated_at"])
            status_code = 201
            message = "Product added."

        # Keep each uploaded option image attached to that exact option.
        if customization_options:
            for group_index, group in enumerate(customization_options):
                for option_index, option in enumerate(group["options"]):
                    if option.get("image"):
                        option["image"] = persist_product_image(option["image"], product.pk,
                            f"{image_name}_variant_{group_index}_{option_index}")
            product.customization_options = customization_options
            product.save(update_fields=["customization_options", "updated_at"])
        product.bundle_components.all().delete()
        if is_bundle_product:
            BundleComponent.objects.bulk_create([BundleComponent(bundle=product, **row) for row in recipe])
        return JsonResponse(
            {
                "message": message,
                "product": serialize_product(product, request),
            },
            status=status_code,
        )
    except ProductInputError as error:
        transaction.set_rollback(True)
        return JsonResponse({"error": str(error), "field": error.field}, status=400)
    except Http404:
        transaction.set_rollback(True)
        return JsonResponse({"error": "Product not found in your assigned scope."}, status=404)
    except json.JSONDecodeError:
        transaction.set_rollback(True)
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except BundleError as e:
        transaction.set_rollback(True)
        return JsonResponse({"error": str(e), "field": "bundle_components"}, status=400)
    except InventoryThresholdError as e:
        transaction.set_rollback(True)
        return JsonResponse({"error": str(e), "field": "low_stock_threshold"}, status=400)
    except InventoryStockError as e:
        transaction.set_rollback(True)
        return JsonResponse({"error": str(e), "field": "stock"}, status=400)
    except (InvalidOperation, ValueError) as e:
        transaction.set_rollback(True)
        return JsonResponse({"error": f"Valid price, stock, and expiry date are required: {e}"}, status=400)
    except Exception as e:
        transaction.set_rollback(True)
        return JsonResponse({"error": "Could not save product. No database changes were saved. Reload the record before retrying."}, status=500)


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
@transaction.atomic
def admin_update_product_stock(request, product_id):
    """Update product stock only (not full edit form)."""
    from modules.marketplace.services.bundles import is_bundle
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user).select_for_update(of=("self",)), id=product_id
    )
    if is_bundle(product):
        return JsonResponse({"error": "Bundle availability is derived. Update the component inventory instead."}, status=400)
    try:
        data = json.loads(request.body or "{}")
        if not isinstance(data, dict):
            raise ValueError("Send a stock update object.")
        stock = validate_stock_quantity(data.get("stock", 0))
        if stock > 2147483647:
            raise ValueError("Stock exceeds the supported inventory limit.")
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Valid stock quantity is required"}, status=400)

    if stock < 0:
        return JsonResponse({"error": "Stock cannot be negative"}, status=400)

    # A tracked product must update one exact option, never only its parent sum.
    options = product.customization_options or []
    variants = product_variant_items(product)
    if variants:
        key = data.get("variant_key")
        if not key and len(variants) == 1:
            key = variants[0]["variant_key"]
        item = next((item for item in variants if item["variant_key"] == key), None)
        if not item:
            return JsonResponse({"error": "Select the variant whose stock you want to update."}, status=400)
        group_index, option_index = map(int, item["variant_key"].split(":"))
        options[group_index]["options"][option_index]["stock"] = stock
        product.customization_options = options
        sync_product_inventory_fields(product)
    else:
        product.stock = stock

    product._inventory_actor = request.user.get_full_name().strip() or request.user.username
    product.save(update_fields=["stock", "customization_options", "updated_at"])
    log_marketplace_event(request, account=product.owner, source="mobile" if product.mobile_seller_id else "admin", activity_type="INVENTORY_UPDATED",
        activity=f"Inventory updated: {product.name}", metadata={"product_id": product.pk, "program_id": product.department_id or product.owner.department_id,
            "major_id": product.major_id if product.department_id else product.owner.major_id})
    return JsonResponse({
        "message": "Stock updated.",
        "product": serialize_product(product, request, include_inventory=True),
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
    log_marketplace_event(request, account=product.owner, source="mobile" if product.mobile_seller_id else "admin", activity_type="PRODUCT_ARCHIVED",
        activity=f"Product archived: {product.name}", metadata={"product_id": product.pk, "program_id": product.department_id or product.owner.department_id,
            "major_id": product.major_id if product.department_id else product.owner.major_id})
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
    log_marketplace_event(request, account=product.owner, source="mobile" if product.mobile_seller_id else "admin", activity_type="PRODUCT_RESTORED",
        activity=f"Product restored: {product.name}", metadata={"product_id": product.pk, "program_id": product.department_id or product.owner.department_id,
            "major_id": product.major_id if product.department_id else product.owner.major_id})
    return JsonResponse({"message": "Product restored.", "id": product.id})


@csrf_exempt
def seller_access_request(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    from modules.marketplace.services.seller_applications import submit
    return submit(request)


def seller_access_status(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    from modules.marketplace.services.seller_applications import state
    return state(request)


@login_required(login_url="admin_login_page")
@admin_read_permissions("can_manage_sellers", "can_view_sellers")
def marketplace_seller_requests(request):
    from accounts.academic import scope_users, scope_seller_requests
    seller_requests = scope_seller_requests(SellerRequest.objects.select_related("user", "reviewed_by"), request.user)
    return JsonResponse({
        "seller_requests": [
            serialize_seller_request(seller_request)
            for seller_request in seller_requests
        ]
    })


@login_required(login_url="admin_login_page")
@admin_read_permissions("can_manage_products", "can_approve_products", "can_view_products", "can_view_inventory", "can_view_stock_movements")
def seller_products_monitor(request):
    from modules.marketplace.services.bundles import prime_bundle_inventory
    product_id = request.GET.get("product_id")
    if product_id and not product_id.isdecimal():
        return JsonResponse({"error": "Valid product ID is required."}, status=400)
    products = (
        manageable_products_for(request.user)
        .select_related("mobile_seller", "mobile_seller__department", "mobile_seller__major", "seller", "seller__department", "seller__major", "approved_by", "department", "major").prefetch_related("inventory_skus")
        .order_by("-submitted_at")
    )
    # A scoped details request can inspect archived records without changing the list.
    products = products.filter(pk=product_id) if product_id else products.filter(is_archived=False)
    owner_id = request.GET.get("bundle_owner_id")
    if owner_id:
        mobile_owner = owner_id.startswith("mobile:")
        raw_id = owner_id.split(":", 1)[1] if mobile_owner else owner_id
        if not raw_id.isdecimal():
            return JsonResponse({"error": "Select a valid product owner."}, status=400)
        owner_filters = {"mobile_seller_id" if mobile_owner else "seller_id": raw_id,
                         "mobile_seller__is_active" if mobile_owner else "seller__is_active": True}
        products = products.filter(**owner_filters,
            product_type=Product.TYPE_SINGLE, approval_status=Product.STATUS_APPROVED, is_archived=False)
    products = prime_bundle_inventory(products)
    if owner_id:
        products = [product for product in products if is_marketplace_available(product)]
    return JsonResponse({"products": [
        serialize_product(product, request, include_inventory=bool(product_id))
        for product in products
    ]})


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_approve_products", raise_exception=True)
@transaction.atomic
def marketplace_approve_product(request, product_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user).select_for_update(of=("self",)), id=product_id
    )
    if product.is_archived or product.approval_status != Product.STATUS_PENDING:
        return JsonResponse({"error": "Only pending, active listings can be reviewed. Reload the product before retrying."}, status=409)
    product.approve(request.user)
    log_marketplace_event(request, account=product.owner, source="mobile" if product.mobile_seller_id else "admin", activity_type="PRODUCT_APPROVED",
        activity=f"Product approved: {product.name}", metadata={"product_id": product.pk, "program_id": product.department_id or product.owner.department_id,
            "major_id": product.major_id if product.department_id else product.owner.major_id})
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "product_id": product.id})
    return redirect(request.META.get("HTTP_REFERER") or "admin_dashboard_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_approve_products", raise_exception=True)
@transaction.atomic
def marketplace_reject_product(request, product_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    product = get_object_or_404(
        manageable_products_for(request.user).select_for_update(of=("self",)), id=product_id
    )
    if product.is_archived or product.approval_status != Product.STATUS_PENDING:
        return JsonResponse({"error": "Only pending, active listings can be reviewed. Reload the product before retrying."}, status=409)
    reason = (request.POST.get("rejection_reason") or "").strip()
    if not reason:
        return JsonResponse({"error": "Enter a rejection reason."}, status=400)
    product.reject(request.user, reason)
    log_marketplace_event(request, account=product.owner, source="mobile" if product.mobile_seller_id else "admin", activity_type="PRODUCT_REJECTED",
        activity=f"Product rejected: {product.name}", metadata={"product_id": product.pk, "program_id": product.department_id or product.owner.department_id,
            "major_id": product.major_id if product.department_id else product.owner.major_id})
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "product_id": product.id})
    return redirect("admin_products_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_sellers", raise_exception=True)
@transaction.atomic
def marketplace_approve_seller_request(request, request_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    from accounts.academic import scope_users, scope_seller_requests
    seller_request = get_object_or_404(scope_seller_requests(SellerRequest.objects.select_for_update(of=("self",)), request.user), id=request_id)
    if seller_request.status != "pending":
        return JsonResponse({"error": "Only pending applications can be reviewed."}, status=409)
    seller_request.approve(request.user)
    log_seller_event(request, seller_request, "SELLER_APPROVED")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "status": seller_request.status, "message": "Seller application approved successfully."})
    messages.success(request, 'Seller application approved successfully.', fail_silently=True)
    return redirect(request.META.get("HTTP_REFERER") or "admin_dashboard_page")


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_sellers", raise_exception=True)
@transaction.atomic
def marketplace_reject_seller_request(request, request_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    from accounts.academic import scope_users, scope_seller_requests
    seller_request = get_object_or_404(scope_seller_requests(SellerRequest.objects.select_for_update(of=("self",)), request.user), id=request_id)
    if seller_request.status != "pending":
        return JsonResponse({"error": "Only pending applications can be reviewed."}, status=409)
    reason = (request.POST.get("rejection_reason") or "").strip()
    if request.POST.get("decision") == "needs_revision":
        if not reason:
            return JsonResponse({"error": "Provide applicant-visible revision notes."}, status=400)
        seller_request.request_revision(request.user, reason)
        log_seller_event(request, seller_request, "SELLER_REVISION_REQUESTED")
    else:
        seller_request.reject(request.user, reason)
        log_seller_event(request, seller_request, "SELLER_REJECTED")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "status": seller_request.status, "message": "Seller application review recorded."})
    messages.success(request, 'Seller application review recorded.', fail_silently=True)
    return redirect(request.META.get("HTTP_REFERER") or "admin_dashboard_page")


def serialize_facility(facility):
    from modules.facilities.services.operating_schedule import workflow_for_display
    from modules.facilities.services.rental_configuration import capacity_label, pricing_label
    from modules.facilities.services.job_order import default_job_order_service

    from modules.facilities.services.service_configuration import is_service, service_pricing_label
    rate = facility.rate or 0
    facility_type = getattr(facility, "facility_type", None) or Facility.TYPE_OTHER
    if not hasattr(facility, "configured_room_count"):
        facility.configured_room_count = facility.rooms.count() if not facility._state.adding else 0
    return {
        "id": str(facility.id),
        "name": facility.facility_name,
        "facility_type": facility_type,
        "facility_type_label": facility.get_facility_type_display(),
        "job_order_service": default_job_order_service(facility),
        "custom_facility_type": facility.custom_facility_type,
        "location": facility.location or "",
        "description": facility.description or "",
        "capacity": facility.capacity,
        "rate": str(rate),
        "price_type": facility.price_type or "hour",
        "price_label": service_pricing_label(facility) if is_service(facility) else pricing_label(facility),
        "capacity_label": capacity_label(facility),
        "booking_mode": facility.booking_mode or "room",
        "rooms_units": facility.rooms_units,
        "configured_room_count": facility.configured_room_count,
        "room_type": facility.room_type or "",
        "amenities": list(facility.amenities or []),
        "status": normalize_facility_status(facility.availability_status),
        "is_archived": facility.is_archived,
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
    facilities = Facility.objects.filter(is_archived=False).annotate(configured_room_count=Count("rooms"))
    if request.GET.get('resource_type') == 'facility':
        from modules.facilities.services.catalog import service_resources_q
        facilities = facilities.exclude(service_resources_q())
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
        with transaction.atomic():
            facility.save(force_insert=True)
            raw_images = data.get("images") or data.get("image_url") or ""
            if raw_images:
                saved_images = persist_facility_images(raw_images, facility_id, cleaned["name"])
                if saved_images:
                    facility.image_url = json.dumps(saved_images) if len(saved_images) > 1 else saved_images[0]
                    facility.save(update_fields=["image_url"])
            event = record_facility_activity(request, facility, action="facility_added")

        return JsonResponse(
            {
                "message": "Facility added.",
                "facility": serialize_facility(facility),
                "activity": facility_activity_row(event),
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
        before = facility_snapshot(facility)
        with transaction.atomic():
            _apply_facility_payload(facility, cleaned)
            raw_images = data.get("images") or data.get("image_url") or ""
            if raw_images:
                saved_images = persist_facility_images(raw_images, facility_id, cleaned["name"])
                facility.image_url = json.dumps(saved_images) if len(saved_images) > 1 else (saved_images[0] if saved_images else "")
            elif "images" in data or "image_url" in data:
                facility.image_url = ""
            facility.save()
            event = record_facility_activity(request, facility, before=before)

        return JsonResponse(
            {
                "message": "Facility updated.",
                "facility": serialize_facility(facility),
                "activity": facility_activity_row(event),
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

    with transaction.atomic():
        facility = get_object_or_404(Facility.objects.select_for_update(), id=facility_id)
        event = None
        if not facility.is_archived:
            facility.archive()
            event = record_facility_activity(request, facility, action="facility_archived")
    return JsonResponse({"message": "Facility archived.", "id": facility.id, "success": True, "activity": facility_activity_row(event)})


@csrf_exempt
@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_facilities", raise_exception=True)
def facilities_restore(request, facility_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    with transaction.atomic():
        facility = get_object_or_404(Facility.objects.select_for_update(), id=facility_id)
        event = None
        if facility.is_archived:
            facility.unarchive()
            event = record_facility_activity(request, facility, action="facility_reactivated")
    return JsonResponse({"message": "Facility restored.", "id": facility.id, "success": True, "activity": facility_activity_row(event)})


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
    type_match = re.match(r"^\[(class|reservation|maintenance|assessment|official|hold|other|blocked)\]\s*", purpose, re.I)
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

    from modules.facilities.services.schedules import metadata
    details = metadata(booking)
    schedule = details.get("schedule", {})
    attachment = details.get("attachment")
    return {
        "id": str(booking.id),
        "type": event_type,
        "facility_id": str(booking.facility_id or ""),
        "facility": booking.facility.facility_name if booking.facility_id else "Facility",
        "date": (booking.booking_date or booking.check_in_date).isoformat() if booking.booking_date or booking.check_in_date else "",
        "end_date": booking.check_out_date.isoformat() if booking.check_out_date else "",
        "schedule": schedule,
        "source": "Facility Schedule" if schedule or event_type != "reservation" else ("Admin / Walk-in" if details.get("source") == "admin" else "Mobile App" if details else "Not recorded"),
        "quote": details.get("quote", {}),
        "attachment_url": f"/api/facility-schedules/{booking.pk}/attachment/" if attachment else "",
        "attachment_name": attachment.get("name", "") if attachment else "",
        "total_amount": str(booking.total_amount),
        "created_at": booking.created_at.isoformat(),
        "start": booking.start_time.strftime("%H:%M") if booking.start_time else "",
        "end": booking.end_time.strftime("%H:%M") if booking.end_time else "",
        "reserved_by": reserved_by,
        "purpose": purpose,
        "status": booking.status,
    }


def bookings_create(request):
    from modules.facilities.admin_booking_views import create
    return create(request)


def _parse_json(request):
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return None


@sensitive_variables()
def _recovery_api(request, operation):
    """JSON transport only; all recovery rules live in accounts.recovery_codes."""
    from accounts.recovery_codes import (find_account, send_code, verify_code,
                                        confirm_password, RecoveryError, mask_email)
    from django.core.cache import cache
    from django.core.validators import validate_email
    from django.utils.crypto import salted_hmac
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    data = _parse_json(request)
    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    # Bound unauthenticated traffic, including unknown emails. Do not store raw identifiers.
    key = "recovery-ip:" + salted_hmac("recovery-ip", request.META.get("REMOTE_ADDR", "")).hexdigest()
    cache.add(key, 0, 900)
    try:
        attempts = cache.incr(key)
    except ValueError:
        attempts = 1
        cache.set(key, attempts, 900)
    if attempts > 60:
        return JsonResponse({"error": "Too many requests. Please try again later."}, status=429)
    purpose = data.get("purpose", "password")
    if not isinstance(purpose, str) or purpose not in {"password", "username", "email_verification"}:
        return JsonResponse({"error": "Unsupported recovery purpose."}, status=400)
    # First-login verification uses the recorded email from the authenticated account.
    if request.headers.get("Authorization"):
        account, error = _mobile_user_from_bearer(request)
        if error is not None:
            return error
        source, email = "mobile", account.email
        if purpose != "email_verification":
            return JsonResponse({"error": "Use the account recovery screen."}, status=400)
    else:
        email = data.get("email", "")
        if not isinstance(email, str):
            return JsonResponse({"error": "Enter a valid email address."}, status=400)
        email = email.strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"error": "Enter a valid email address."}, status=400)
        source, account = find_account(email)
    # Request responses do not disclose whether an account exists/is verified.
    if account is None or not account.is_active or account.is_suspended or (operation == "send" and purpose != "email_verification" and not account.email_verified):
        if operation == "send":
            return JsonResponse({"message": "If that email is eligible, check your inbox for the code.",
                                 "email_sent": True, "masked_email": mask_email(email),
                                 "step": 2, "resend_after": 60, "expires_in": 900})
        return JsonResponse({"error": "Invalid verification code."}, status=400)
    account = type(account).objects.select_for_update().get(pk=account.pk)
    try:
        if operation == "send":
            result = send_code(request, source, account, purpose)
        elif operation == "verify":
            result = verify_code(request, source, account, data.get("code"), purpose)
        else:
            password, confirmation = data.get("new_password", ""), data.get("confirm_password", "")
            if not isinstance(password, str) or not isinstance(confirmation, str):
                raise RecoveryError("Enter a valid password.")
            result = confirm_password(request, source, account, data.get("recovery_grant", ""), password, confirmation)
    except RecoveryError as exc:
        return JsonResponse({"error": exc.message}, status=exc.status)
    if purpose == "email_verification" and operation == "verify" and request.headers.get("Authorization"):
        result["user"] = serialize_campushub_user(account)
    response = JsonResponse(result)
    response["Cache-Control"] = "no-store"
    return response


@csrf_exempt
@never_cache
@transaction.atomic
def mobile_password_reset(request):
    return _recovery_api(request, "send")


@csrf_exempt
@never_cache
@transaction.atomic
def mobile_password_reset_verify(request):
    return _recovery_api(request, "verify")


@csrf_exempt
@never_cache
@transaction.atomic
def mobile_password_reset_confirm(request):
    return _recovery_api(request, "confirm")


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
    personalized_only = request.GET.get("personalized_only") == "1"

    products = get_recommended_products(
        user_id=uid,
        limit=limit_n,
        seed_product_id=pid,
        personalized_only=personalized_only,
    )

    return JsonResponse(
        {
            "products": [serialize_product(p, request) for p in products],
            "engine": "scikit-learn-tfidf-cosine",
            "user_id": uid,
            "seed_product_id": pid,
            "personalized_only": personalized_only,
        }
    )


@csrf_exempt
@never_cache
@fulfillment_buyer_guard
@fifo_order_request
def marketplace_orders(request):
    if request.method == "GET":
        if request.headers.get("Authorization"):
            buyer, error = _mobile_user_from_bearer(request)
            if error is not None: return error
            # Legacy Django/mobile IDs share a numeric namespace; require the saved email too.
            orders = MarketplaceOrder.objects.filter(buyer_user_id=buyer.pk, buyer_email__iexact=buyer.email) if buyer.email else MarketplaceOrder.objects.none()
        elif request.user.is_authenticated:
            from modules.marketplace.services.order_access import admin_order_queryset
            orders = admin_order_queryset(request.user)
        else:
            return JsonResponse({"error": "Sign in to view authorized orders."}, status=401)
        orders = orders.select_related("product")
        return JsonResponse({"orders": [serialize_marketplace_order(o) for o in orders]})

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    data = _parse_json(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    from modules.marketplace.services.fulfillment import creation_fields
    try:
        fulfillment = creation_fields(data)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    product_id = data.get("product_id")
    quantity = max(int(data.get("quantity") or 1), 1)
    option = (data.get("option") or "").strip()
    buyer_user_id = data.get("buyer_user_id")
    buyer_name = (data.get("buyer_name") or "").strip()
    buyer_email = (data.get("buyer_email") or "").strip()
    verified_buyer = getattr(request, "fulfillment_buyer", None)
    if verified_buyer is not None:
        buyer_name = verified_buyer.get_full_name().strip() or verified_buyer.username
        buyer_email = verified_buyer.email or ""
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
            product = Product.objects.select_for_update(of=("self",)).select_related("seller").filter(
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

            from modules.marketplace.services.bundles import is_bundle, reserve_bundle
            if is_bundle(product):
                customization_payload = reserve_bundle(product, quantity)
                option_summary = customization_payload["summary"]
                unit_price = base_price
            elif product.customization_enabled or customization_has_stock_tracking(product.customization_options):
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

            if not is_bundle(product):
                adjust_product_stock(product, selections, quantity)
                product.save(update_fields=["stock", "customization_options", "updated_at"])
            total_price = (unit_price * quantity).quantize(Decimal("0.01"))
            seller_name = product.owner.get_full_name() or product.owner.username

            order = MarketplaceOrder.objects.create(
                product=product,
                buyer_user_id=resolved_buyer_id,
                buyer_name=buyer_name or "Unknown customer",
                buyer_email=buyer_email,
                product_name=product.name,
                category=product.category,
                seller_name=seller_name,
                seller_contact=product.owner.email,
                message_to_seller=message_to_seller,
                option=option_summary,
                customization=customization_payload,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                image_url=serialize_product(product, request).get("image_url", ""),
                inventory_deducted=True,
                **fulfillment,
            )

            from modules.marketplace.services.inventory_records import attach_reservation_movements
            attach_reservation_movements(product, order)

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
