"""Existing Department is the program; a linked Major is a separate dimension."""
from django.db.models import Q

from .models import Department, ProgramMajor


def academic_options():
    return Department.objects.filter(is_program=True).order_by("code"), ProgramMajor.objects.select_related("program").order_by("code")


def academic_labels(program, major=None):
    code = (program.code or program.name) if program else "Unassigned"
    valid_major = major if major and program and major.program_id == program.pk else None
    return {"program_id": program.pk if program else None, "program": code,
            "major_id": valid_major.pk if valid_major else None, "major": valid_major.name if valid_major else "",
            "program_major": f"{code}-{valid_major.code}" if valid_major else code}


def product_academic(product):
    program = product.department or product.owner.department
    major = product.major if product.department_id else product.owner.major
    return academic_labels(program, major)


def resolve_academic(program_id, major_id=None, *, required=False):
    if not program_id:
        if required or major_id:
            raise ValueError("Select a program.")
        return None, None
    program = Department.objects.filter(pk=program_id, is_program=True).first()
    if program is None:
        raise ValueError("Select a valid program.")
    major = ProgramMajor.objects.filter(pk=major_id, program=program).first() if major_id else None
    if major_id and major is None:
        raise ValueError("Select a major belonging to the selected program.")
    if required and program.majors.exists() and major is None:
        raise ValueError("Select a major for this program.")
    return program, major


def resolve_account_academic(role, account_type, program_id, major_id=None, *, existing=None):
    """Validate administrative scope independently of a student's affiliation."""
    normalized = (role or "").strip().casefold()
    if account_type == "admin" and normalized in {"super admin", "facilities admin"}:
        return None, None  # Ignore hidden/overposted academic fields for global roles.
    if account_type == "guest":
        return None, None
    required = normalized == "marketplace admin" or account_type == "student"
    legacy_unassigned = bool(existing and getattr(existing, "user_type", None) == account_type and not existing.department_id and not program_id
                             and not major_id and normalized != "marketplace admin")
    program, major = resolve_academic(program_id, major_id, required=required and not legacy_unassigned)
    if program and program.code not in {"BSIT", "BFPT", "BTLED"}:
        raise ValueError("Select BSIT, BFPT, or BTLED as the program.")
    if program and program.code != "BTLED" and major:
        raise ValueError("A major is only applicable to BTLED.")
    if program and program.code == "BTLED" and major is None:
        raise ValueError("Select a BTLED major.")
    return program, major


def has_valid_marketplace_scope(user):
    """Fail closed for legacy BTLED admins missing their required major."""
    program = getattr(user, "department", None)
    if not program:
        return False
    major = getattr(user, "major", None)
    if major and (major.program_id != program.pk or program.code != "BTLED"):
        return False
    return program.code != "BTLED" or major is not None


def unrestricted_marketplace(user):
    return bool(getattr(user, "is_superuser", False))


def scope_users(queryset, user, *, prefix=""):
    if unrestricted_marketplace(user):
        return queryset
    if not has_valid_marketplace_scope(user):
        return queryset.none()
    queryset = queryset.filter(**{prefix + "department_id": user.department_id})
    if getattr(user, "major_id", None):
        queryset = queryset.filter(**{prefix + "major_id": user.major_id})
    return queryset


def scope_seller_requests(queryset, actor):
    """Scope linked sellers and existing mobile applications without a Django FK."""
    if unrestricted_marketplace(actor):
        return queryset
    from django.db.models import Exists, OuterRef
    from api.models import CampusHubUser
    from .models import User
    django_users = scope_users(User.objects.filter(role__iexact="User", is_staff=False, is_superuser=False), actor)
    identities = CampusHubUser.objects.filter(
        Q(username__iexact=OuterRef("student_id")) | Q(student_id__iexact=OuterRef("student_id")))
    eligible = scope_users(identities.filter(role__iexact="User").exclude(user_type__iexact="admin"), actor)
    # A collision across account identities must not reveal another program's application.
    permitted_ids = scope_users(CampusHubUser.objects.filter(role__iexact="User").exclude(user_type__iexact="admin"), actor).values("pk")
    conflicting = identities.exclude(pk__in=permitted_ids)
    application_scope = Q(pk__in=[])
    if has_valid_marketplace_scope(actor):
        application_scope = Q(mobile_user__role__iexact="User") & (
            Q(mobile_user__department_id=actor.department_id) |
            Q(mobile_user__department__isnull=True, application_data__program_id=actor.department_id))
        if actor.major_id:
            application_scope &= (Q(mobile_user__major_id=actor.major_id) |
                Q(mobile_user__major__isnull=True, application_data__major_id=actor.major_id))
    return queryset.annotate(_eligible_mobile=Exists(eligible), _conflicting_identity=Exists(conflicting)).filter(
        Q(user_id__in=django_users.values("pk")) |
        Q(mobile_user_id__in=permitted_ids) | application_scope | Q(user__isnull=True, mobile_user__isnull=True, _eligible_mobile=True, _conflicting_identity=False)).exclude(student_id="")


def scope_products(queryset, user, *, prefix=""):
    if unrestricted_marketplace(user):
        return queryset
    program_id = getattr(user, "department_id", None)
    if not has_valid_marketplace_scope(user):
        return queryset.none()
    direct = Q(**{prefix + "department_id": program_id})
    inherited = Q(**{prefix + "department_id__isnull": True, prefix + "seller__department_id": program_id})
    inherited_mobile = Q(**{prefix + "department_id__isnull": True, prefix + "mobile_seller__department_id": program_id})
    if getattr(user, "major_id", None):
        direct &= Q(**{prefix + "major_id": user.major_id})
        inherited &= Q(**{prefix + "seller__major_id": user.major_id})
        inherited_mobile &= Q(**{prefix + "mobile_seller__major_id": user.major_id})
    return queryset.filter(direct | inherited | inherited_mobile)


def filter_product_academic(queryset, program_id=None, major_id=None):
    if program_id:
        queryset = queryset.filter(Q(department_id=program_id) | Q(department_id__isnull=True, seller__department_id=program_id))
    if major_id:
        queryset = queryset.filter(Q(department_id__isnull=False, major_id=major_id) | Q(department_id__isnull=True, seller__major_id=major_id))
    return queryset
