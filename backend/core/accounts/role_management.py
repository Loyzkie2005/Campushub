"""Role presentation and staged edits using the existing CampusHub RBAC store."""
from collections import defaultdict
from functools import wraps
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .activity_logging import log_account_activity
from .academic import academic_labels, resolve_account_academic
from .models import AccountActivity, Role, User
from .role_permissions import (
    ADMIN_UI_PERMISSION_CODENAMES, NORMAL_CAPABILITY_CODENAMES, PERMISSION_MODULES, PERMISSION_DEPENDENCIES,
    role_scope_permissions, set_role_permissions, sync_user_admin_permissions, sync_users_for_role,
)

BASE_ROLE_NAMES = {"user", "standard user"}
SYSTEM_NAMES = {"super admin", "marketplace admin", "facilities admin"} | BASE_ROLE_NAMES
READ_ONLY_NAMES = {"super admin"} | BASE_ROLE_NAMES
SCOPE_LABELS = {
    "super admin": "Full Access", "marketplace admin": "Marketplace Access",
    "facilities admin": "Facilities Access",
}


def managed_admin_roles():
    """Hide internal buyer roles without deleting records or altering grants."""
    return Role.objects.exclude(Q(role_name__iexact="User") | Q(role_name__iexact="Standard User"))


def eligible_admin_queryset():
    """Do not confuse the Django account store with administrator eligibility."""
    admin_roles = managed_admin_roles().values_list("role_name", flat=True)
    return User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(role__in=admin_roles)
        | Q(user_permissions__content_type__app_label="accounts",
            user_permissions__codename__in=ADMIN_UI_PERMISSION_CODENAMES)
    ).distinct()


def admin_data(user):
    applicable = (user.role or "").casefold() == "marketplace admin"
    return {
        "id": user.pk, "username": user.username,
        "full_name": user.get_full_name().strip() or user.username,
        "role": user.role, "display_role": "Unassigned" if user.role.casefold() in BASE_ROLE_NAMES else user.role,
        "program_major": academic_labels(user.department, user.major)["program_major"] if user.department_id else ("Unassigned" if applicable else "—"),
        "department_id": user.department_id, "major_id": user.major_id,
        "is_active": user.is_active and not user.is_suspended,
        "account_status": "Suspended" if user.is_suspended else "Active" if user.is_active else "Inactive",
        "initials": (user.first_name[:1] + user.last_name[:1]).upper() or user.username[:2].upper(),
    }


def serialize_role(role, admins=None):
    name = role.role_name.casefold()
    grants = {p.codename for p in role.granted_permissions.all()}
    allowed = role_scope_permissions(role.role_name)
    codes = set(ADMIN_UI_PERMISSION_CODENAMES) if name == "super admin" else grants.intersection(ADMIN_UI_PERMISSION_CODENAMES)
    if allowed is not None:
        codes.intersection_update(allowed)
    admins = list(eligible_admin_queryset().filter(role__iexact=role.role_name).select_related("department", "major")) if admins is None else admins
    rows = [] if name in BASE_ROLE_NAMES else [admin_data(u) for u in admins]
    updated = timezone.localtime(role.updated_at, ZoneInfo("Asia/Manila")) if role.updated_at else None
    return {
        "id": str(role.pk), "role_name": role.role_name,
        "display_name": role.role_name,
        "description": role.description or "", "role_type": "System Role" if name in SYSTEM_NAMES else "Custom Role",
        "is_protected": name in SYSTEM_NAMES, "is_readonly": name in READ_ONLY_NAMES,
        "assignment_applicable": name not in BASE_ROLE_NAMES, "can_assign": name not in READ_ONLY_NAMES and role.is_active and bool(codes),
        "is_active": role.is_active, "status_label": "Active" if role.is_active else "Inactive",
        "permission_summary": SCOPE_LABELS.get(name, "Custom Access"),
        "assigned_permissions": sorted(codes), "allowed_permission_codes": sorted(allowed.intersection(ADMIN_UI_PERMISSION_CODENAMES)) if allowed is not None else list(ADMIN_UI_PERMISSION_CODENAMES),
        "base_permissions": sorted(grants.intersection(NORMAL_CAPABILITY_CODENAMES)),
        "permission_count": len(codes), "role_users": rows, "user_count": len(rows),
        "updated_at": updated.isoformat() if updated else None,
        "updated_date": updated.strftime("%b %d, %Y") if updated else "—",
        "updated_time": updated.strftime("%I:%M %p").lstrip("0") if updated else "",
    }


def audit(request, event, role, previous, new, target_admin=None):
    log_account_activity(
        request, source=AccountActivity.SOURCE_ADMIN, account=target_admin or request.user,
        activity_type=event, activity=f"{event.replace('_', ' ').title()}: {role.role_name} by {request.user.username}"[:180],
        result=AccountActivity.RESULT_SUCCESS, module="Roles & Permissions",
        metadata={"actor_admin_id": request.user.pk, "actor_username": request.user.username,
                  "role_id": str(role.pk), "role_name": role.role_name,
                  "target_admin_id": target_admin.pk if target_admin else None,
                  "previous": previous, "new": new},
    )


def response(request, *, role=None, success=True, message="Saved.", status=200):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        payload = {"success": success, "message": str(message)}
        if role is not None:
            payload["role"] = serialize_role(role)
        return JsonResponse(payload, status=status)
    (messages.success if success else messages.error)(request, str(message))
    return redirect("admin_roles_page")


def role_post(view):
    """All role mutations share authorization, transaction and safe input errors."""
    @login_required(login_url="admin_login_page")
    @permission_required("accounts.can_manage_roles_permissions", raise_exception=True)
    @wraps(view)
    def wrapped(request):
        from .support_scope import is_super_admin
        from django.core.exceptions import PermissionDenied
        if not is_super_admin(request.user):
            raise PermissionDenied
        if request.method != "POST":
            return redirect("admin_roles_page")
        try:
            with transaction.atomic():
                return view(request)
        except Role.DoesNotExist:
            return response(request, success=False, message="Role not found.", status=404)
        except (ValidationError, ValueError, IntegrityError) as exc:
            message = " ".join(exc.messages) if isinstance(exc, ValidationError) else "Choose a valid, unique role and administrator selection."
            return response(request, success=False, message=message, status=400)
    return wrapped


def locked_role(request):
    return Role.objects.select_for_update().get(pk=request.POST.get("role_id", ""))


def role_history_response(request):
    """Read existing role audit records; caller enforces Roles workspace access."""
    if request.method != "GET":
        return JsonResponse({"error": "Use GET to view permission history."}, status=405)
    try:
        role = managed_admin_roles().get(pk=request.GET.get("history_role", ""))
    except (Role.DoesNotExist, ValueError, ValidationError):
        return JsonResponse({"error": "Role not found."}, status=404)
    events = AccountActivity.objects.filter(module="Roles & Permissions",
        metadata__role_id=str(role.pk)).order_by("-created_at", "-pk")
    page = Paginator(events, 20).get_page(request.GET.get("history_page"))
    labels = {"ADMIN_ASSIGNED_TO_ROLE": "Administrator Assigned",
              "ADMIN_ROLE_CHANGED": "Administrator Role Changed"}
    rows = [{"id": event.pk, "event": labels.get(event.activity_type, event.activity_type.replace("_", " ").title()),
             "activity": event.activity, "date": timezone.localtime(event.created_at, ZoneInfo("Asia/Manila")).strftime("%b %d, %Y %I:%M %p")}
            for event in page.object_list]
    response = JsonResponse({"role": str(role.pk), "events": rows, "page": page.number,
        "pages": page.paginator.num_pages, "total": page.paginator.count,
        "has_previous": page.has_previous(), "has_next": page.has_next()})
    response["Cache-Control"] = "no-store"
    return response


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_manage_roles_permissions", raise_exception=True)
def admin_roles_page(request):
    from .support_scope import is_super_admin
    from django.core.exceptions import PermissionDenied
    if not is_super_admin(request.user):
        raise PermissionDenied
    if "history_role" in request.GET:
        return role_history_response(request)
    from .views import get_notification_context
    q = request.GET.get("q", "").strip()
    kind, status = request.GET.get("type", ""), request.GET.get("status", "")
    all_roles = list(managed_admin_roles().prefetch_related("granted_permissions").order_by("role_name"))
    rank = {"super admin": 0, "marketplace admin": 1, "facilities admin": 2}
    all_roles.sort(key=lambda r: (rank.get(r.role_name.casefold(), 4), r.role_name.casefold()))
    admins = list(eligible_admin_queryset().select_related("department", "major").order_by("first_name", "last_name", "username"))
    by_role = defaultdict(list)
    for admin in admins:
        by_role[(admin.role or "").casefold()].append(admin)
    selected = [r for r in all_roles if
        (not q or q.casefold() in (r.role_name + " " + (r.description or "")).casefold())
        and (kind not in {"system", "custom"} or (r.role_name.casefold() in SYSTEM_NAMES) == (kind == "system"))
        and (status not in {"active", "inactive"} or r.is_active == (status == "active"))]
    page = Paginator(selected, 10).get_page(request.GET.get("page"))
    data = [serialize_role(r, by_role[r.role_name.casefold()]) for r in page.object_list]
    configure = next((serialize_role(r, by_role[r.role_name.casefold()]) for r in all_roles if str(r.pk) == request.GET.get("configure")), None)
    definitions = set(Permission.objects.filter(content_type__app_label="accounts", content_type__model="role", codename__in=ADMIN_UI_PERMISSION_CODENAMES).values_list("codename", flat=True))
    groups = [{"name": name, "key": name.lower().replace(" ", "-"), "permissions": [
        {"codename": c, "label": label} for c, label in permissions if c in definitions
    ]} for name, permissions in PERMISSION_MODULES]
    valid_names = {r.role_name.casefold() for r in all_roles}
    assigned = sum((a.role or "").casefold() in valid_names for a in admins)
    query = request.GET.copy()
    query.pop("page", None)
    query.pop("configure", None)
    return render(request, "user_management/pages/admin_roles.html", {
        "roles": data, "roles_json": data, "configure_role": configure,
        "permission_groups": groups, "permission_dependencies": PERMISSION_DEPENDENCIES,
        "assignable_admins": [admin_data(a) for a in admins],
        "page_obj": page, "query_without_page": query.urlencode(), "search_query": q,
        "role_type_filter": kind, "status_filter": status, "total_roles": len(all_roles),
        "assigned_admins": assigned, "unassigned_admins": len(admins) - assigned,
        "total_permission_count": len(definitions), **get_notification_context(user=request.user),
    })


def assign_admins(request, role):
    if role.role_name.casefold() in READ_ONLY_NAMES:
        raise ValidationError("This protected role cannot be assigned through the Roles workspace.")
    if not role.is_active:
        raise ValidationError("Inactive roles cannot be assigned to administrators.")
    if not serialize_role(role)["permission_count"]:
        raise ValidationError("Configure at least one administrator permission before assigning administrators.")
    ids = {int(v) for v in request.POST.getlist("assigned_users")}
    # Lock every active Super Admin as well as targets, preventing concurrent final-admin demotions.
    locked = list(User.objects.select_for_update().filter(Q(pk__in=ids) | Q(is_superuser=True) | Q(role__iexact="Super Admin")).order_by("pk"))
    eligible = set(eligible_admin_queryset().filter(pk__in=ids).values_list("pk", flat=True))
    if ids != eligible:
        raise ValidationError("Select existing eligible administrator accounts only.")
    current_ids = set(eligible_admin_queryset().filter(role__iexact=role.role_name).values_list("pk", flat=True))
    if current_ids - ids:
        raise ValidationError("To remove an administrator, assign them to another configured role first.")
    targets = [u for u in locked if u.pk in ids]
    changed = [u for u in targets if u.role != role.role_name]
    if changed and request.POST.get("confirm_role_changes") != "1":
        raise ValidationError("Confirm the administrator role changes before saving.")
    active_supers = {u.pk for u in locked if u.is_active and not u.is_suspended and (u.is_superuser or u.role.casefold() == "super admin")}
    if active_supers and not (active_supers - ids):
        raise ValidationError("The final active Super Admin assignment cannot be removed.")
    previous_roles = {r.role_name.casefold(): r for r in managed_admin_roles().filter(role_name__in=[u.role for u in changed])}
    for user in changed:
        if not user.is_active or user.is_suspended:
            raise ValidationError("Activate the administrator account before assigning a role.")
        try:
            program, major = resolve_account_academic(role.role_name, "admin", user.department_id, user.major_id)
        except ValueError as exc:
            raise ValidationError(f"{exc} Edit the administrator account in Users first.") from exc
        previous = user.role
        user.role = role.role_name
        user.department, user.major = program, major
        user.save(update_fields=["role", "department", "major"])
        sync_user_admin_permissions(user)
        previous_role = previous_roles.get(previous.casefold())
        if previous_role is not None and previous_role.pk != role.pk:
            audit(request, "ADMIN_REMOVED_FROM_ROLE", previous_role, previous, user.role, user)
        audit(request, "ADMIN_ROLE_CHANGED", role, previous, user.role, user)
        audit(request, "ADMIN_ASSIGNED_TO_ROLE", role, previous, user.role, user)
    if changed:
        Role.objects.filter(pk__in=[r.pk for r in previous_roles.values()]).update(updated_at=timezone.now())
        role.save(update_fields=["updated_at"])


@role_post
def admin_roles_save(request):
    if request.POST.get("operation") == "assign":
        role = locked_role(request)
        assign_admins(request, role)
        return response(request, role=role, message="Administrator assignments saved.")
    if request.POST.getlist("assigned_users"):
        raise ValidationError("Save role information, configure permissions, then assign administrators separately.")
    name = request.POST.get("role_name", "").strip()
    if not name or len(name) > 100:
        raise ValidationError("Enter a role name between 1 and 100 characters.")
    role = locked_role(request) if request.POST.get("role_id") else None
    if name.casefold() in SYSTEM_NAMES | {"standard user"} or (role and role.role_name.casefold() in SYSTEM_NAMES):
        raise ValidationError("Protected system-role information cannot be changed.")
    if Role.objects.filter(role_name__iexact=name).exclude(pk=role.pk if role else None).exists():
        raise ValidationError("A role with this name already exists.")
    previous = {"name": role.role_name, "description": role.description, "is_active": role.is_active} if role else None
    active = request.POST.get("is_active") == "on" if request.POST.get("role_status_present") == "1" else (role.is_active if role else True)
    if role is None:
        role = Role.objects.create(role_name=name, description=request.POST.get("description", "").strip(), is_active=active)
    else:
        old_name = role.role_name
        role.role_name, role.description, role.is_active = name, request.POST.get("description", "").strip(), active
        role.save(update_fields=["role_name", "description", "is_active", "updated_at"])
        if old_name != name:
            User.objects.filter(role__iexact=old_name).update(role=name)
        sync_users_for_role(name)
    audit(request, "ROLE_CREATED" if previous is None else "ROLE_UPDATED", role, previous,
          {"name": name, "description": role.description, "is_active": active})
    if previous is not None and previous["is_active"] != active:
        audit(request, "ROLE_ACTIVATED" if active else "ROLE_DEACTIVATED", role, previous["is_active"], active)
    if previous and previous["is_active"] != active:
        audit(request, "ROLE_ACTIVATED" if active else "ROLE_DEACTIVATED", role, previous["is_active"], active)
    return response(request, role=role, message="Role information saved. Configure permissions before assigning administrators.")


@role_post
def admin_role_permissions_save(request):
    role = locked_role(request)
    if role.role_name.casefold() in READ_ONLY_NAMES:
        raise ValidationError("This protected role's permissions are read-only.")
    original_permissions = list(role.granted_permissions.all())
    previous = {p.codename for p in original_permissions}
    submitted = set(request.POST.getlist("permissions"))
    if submitted - set(ADMIN_UI_PERMISSION_CODENAMES):
        raise ValidationError("Choose valid administrator permissions.")
    scope = role_scope_permissions(role.role_name)
    if scope is not None:
        submitted.intersection_update(scope)
    if not submitted and eligible_admin_queryset().filter(role__iexact=role.role_name).exists():
        raise ValidationError("A role assigned to administrators must keep at least one administrator permission.")
    # Ordinary user/mobile and unrelated historical grants are outside this editor.
    preserved = previous - set(ADMIN_UI_PERMISSION_CODENAMES)
    set_role_permissions(role, list(submitted | (preserved & NORMAL_CAPABILITY_CODENAMES)))
    role.granted_permissions.add(*(p for p in original_permissions if p.codename not in ADMIN_UI_PERMISSION_CODENAMES))
    sync_users_for_role(role.role_name)
    audit(request, "PERMISSIONS_CHANGED", role, sorted(previous), sorted(p.codename for p in role.granted_permissions.all()))
    return response(request, role=role, message="Permissions saved. Administrators can now be assigned.")


@role_post
def admin_roles_status(request):
    role = locked_role(request)
    action = request.POST.get("action")
    if role.role_name.casefold() in SYSTEM_NAMES:
        raise ValidationError("Built-in system-role status is protected.")
    if action not in {"activate", "deactivate"}:
        raise ValidationError("Choose Activate or Deactivate.")
    previous = role.is_active
    role.is_active = action == "activate"
    role.save(update_fields=["is_active", "updated_at"])
    sync_users_for_role(role.role_name)
    audit(request, "ROLE_ACTIVATED" if role.is_active else "ROLE_DEACTIVATED", role, previous, role.is_active)
    return response(request, role=role, message="Role status updated.")


@role_post
def admin_roles_delete(request):
    role = locked_role(request)
    historical = AccountActivity.objects.filter(Q(metadata__role_id=str(role.pk)) | Q(role__iexact=role.role_name)).exists()
    if role.role_name.casefold() in SYSTEM_NAMES or User.objects.filter(role__iexact=role.role_name).exists() or historical:
        raise ValidationError("Protected, assigned or historical roles cannot be deleted. Deactivate a custom role instead.")
    role.delete()
    return response(request, message="Unused custom role deleted.")
