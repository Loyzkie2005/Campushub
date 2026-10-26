"""Authenticated applications reuse SellerRequest and existing account/approval data."""
import json
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from accounts.academic import academic_labels, resolve_academic, academic_options
from accounts.activity_logging import log_marketplace_event
from accounts.user_management import seller_request_for
from api.models import CampusHubUser, Product, SellerRequest


def applicant(request, *, allow_seller=False):
    from api.views import _mobile_user_from_bearer
    if request.headers.get("Authorization"):
        account, error = _mobile_user_from_bearer(request)
        source = "mobile"
    elif request.user.is_authenticated:
        account, error, source = request.user, None, "admin"
    else:
        return None, None, JsonResponse({"error": "Sign in to manage your seller application."}, status=401)
    if error is not None:
        return None, None, error
    if (not account.is_active or account.is_suspended or
        (account.role or "User").casefold() not in ({"user", "standard user", "seller"} if allow_seller else {"user", "standard user"}) or
        getattr(account, "is_staff", False) or getattr(account, "is_superuser", False)):
        return None, None, JsonResponse({"error": "Seller applications are for active regular accounts."}, status=403)
    return account, source, None


def latest(account, source):
    if source == "mobile":
        linked = SellerRequest.objects.filter(mobile_user=account).order_by("-created_at", "-pk").first()
        if linked:
            return linked
    item = seller_request_for(source, account)
    if item and source == "mobile" and not item.mobile_user_id:
        # Never assign ambiguous legacy string identities to a different account.
        identities = CampusHubUser.objects.filter(Q(username__iexact=item.student_id) | Q(student_id__iexact=item.student_id))
        if list(identities.values_list("pk", flat=True)[:2]) != [account.pk]:
            return None
    return item


def categories():
    return list(Product.objects.exclude(category="").filter(is_archived=False)
        .order_by("category").values_list("category", flat=True).distinct())


def snapshot(account):
    return {"full_name": account.get_full_name(), "user_id": account.pk,
        "account_ref": f"mobile:{account.pk}" if isinstance(account, CampusHubUser) else f"admin:{account.pk}",
        "student_id": getattr(account, "student_id", "") or account.username,
        "email": account.email, "contact_number": account.contact_number,
        **academic_labels(account.department, account.major)}


def public_application(item):
    if item is None:
        return None
    return {"id": item.pk, "status": "suspended" if item.is_suspended and item.status == "approved" else item.status,
        "status_label": "Suspended" if item.is_suspended and item.status == "approved" else item.get_status_display(),
        "full_name": item.full_name, "student_id": item.student_id,
        "course_section": item.course_section, "contact_number": item.contact_number,
        "category": item.product_type, "message": item.message,
        "application_data": item.application_data,
        "rejection_reason": item.rejection_reason if item.status == "rejected" else "",
        "revision_notes": item.revision_notes if item.status == "needs_revision" else "",
        "created_at": item.created_at.isoformat()}


def state(request):
    account, source, error = applicant(request)
    if error is not None:
        return error
    item = latest(account, source)
    result = public_application(item)
    return JsonResponse({"status": result["status"] if result else "none",
        "is_approved_seller": bool(item and item.status == "approved" and not item.is_suspended),
        "seller_request": result, "applicant": snapshot(account), "categories": categories(),
        "supporting_document_required": False,
        "programs": list(academic_options()[0].values("id", "code", "name")),
        "majors": list(academic_options()[1].values("id", "program_id", "code", "name"))})


def submit(request):
    account, source, error = applicant(request)
    if error is not None:
        return error
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError("Enter a valid application.")
        category = str(data.get("category") or "").strip()
        intended = str(data.get("products_intended") or "").strip()
        contact = str(data.get("contact_number") or "").strip()
        section = str(data.get("course_section") or "").strip()
        reason = str(data.get("message") or "").strip()
        confirmations = data.get("confirmations")
        if not isinstance(confirmations, dict) or any(confirmations.get(key) is not True for key in ("accuracy", "rules", "approval")):
            raise ValueError("Confirm information accuracy, marketplace rules and administrator approval before submitting.")
        if category not in categories():
            raise ValueError("Select an existing marketplace category.")
        if not intended or len(intended) > 3000:
            raise ValueError("Describe the products you intend to sell (up to 3000 characters).")
        if not contact or len(contact) > 30:
            raise ValueError("Enter a contact number (up to 30 characters).")
        if len(section) > 120 or len(reason) > 3000 or len(category) > 120:
            raise ValueError("Some application fields exceed their maximum length.")
        if not account.get_full_name().strip() or not account.email or not getattr(account, "profile_completed", True):
            raise ValueError("Complete your account information before applying.")
        program_id = account.department_id or data.get("program_id")
        major_id = account.major_id or data.get("major_id")
        program, major = resolve_academic(program_id, major_id, required=True)
        with transaction.atomic():
            account._meta.model.objects.select_for_update().get(pk=account.pk)
            item = latest(account, source)
            if item and item.status in {"pending", "approved"}:
                return JsonResponse({"error": "An active seller application already exists.", "seller_request": public_application(item)}, status=409)
            revision = bool(item and item.status == "needs_revision")
            if revision:
                item = SellerRequest.objects.select_for_update().get(pk=item.pk)
            else:
                item = SellerRequest()
            item.user = account if source == "admin" else None
            item.mobile_user = account if source == "mobile" else None
            item.student_id = getattr(account, "student_id", "") or account.username
            item.full_name = account.get_full_name()
            item.course_section, item.contact_number = section, contact
            item.product_type, item.message = category, reason
            item.application_data = {**snapshot(account), **academic_labels(program, major),
                "products_intended": intended, "confirmations": {key: True for key in ("accuracy", "rules", "approval")},
                "confirmed_at": timezone.now().isoformat()}
            item.status = "pending"
            item.rejection_reason = ""
            # Preserve the last revision notes as history; only expose while revising.
            item.save()
            log_marketplace_event(request, account=account, source=source,
                activity_type="SELLER_RESUBMITTED" if revision else "SELLER_REQUESTED",
                activity="Seller application resubmitted" if revision else "Seller application submitted",
                metadata={"seller_request_id": item.pk})
        return JsonResponse({"message": "Application Submitted", "seller_request": public_application(item)}, status=200 if revision else 201)
    except (ValueError, TypeError) as error:
        return JsonResponse({"error": str(error)}, status=400)
