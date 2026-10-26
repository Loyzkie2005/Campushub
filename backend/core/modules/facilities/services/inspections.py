"""Existing staff grants and inspection JSON: shared validation/presentation helpers."""
from django.db.models import Q, Subquery
from django.db.models.functions import Lower, Trim

from accounts.models import Role, User
from django.core.exceptions import ValidationError

INSPECTION_PERMISSION = 'can_manage_bookings'
CONDITION_CHOICES = ('Good Condition', 'Minor Issues', 'Damaged', 'Requires Maintenance', 'Other')
NON_INSPECTOR_ROLES = {'user', 'standard user', 'student', 'guest', 'guest/external',
                       'guest / external', 'external', 'marketplace admin'}
ABSENCE_VALUES = {'', 'none', 'no', 'n/a', 'na', 'nil', '0', '0.00', 'null', 'nonetype', '-', '\u2014',
                  'not recorded', 'no damage', 'no damage found', 'no damages', 'no damages found',
                  'none recorded', 'none reported', 'not applicable', 'no missing items', 'no overtime',
                  '0 hours', '0 hr', '0 hrs'}


def has_issue_text(value):
    return str(value or '').strip().rstrip('.').casefold() not in ABSENCE_VALUES


def damage_state(record):
    """Keep unknown legacy answers unknown; new records use an explicit boolean."""
    if isinstance(record.get('has_damage'), bool):
        return record['has_damage']
    value = record.get('damage_found')
    return has_issue_text(value) if str(value or '').strip() else None


def can_record_inspection(user):
    from .booking_workflow import has_permission
    return (str(getattr(user, 'role', '')).strip().casefold() not in NON_INSPECTOR_ROLES
            and has_permission(user, INSPECTION_PERMISSION))


def authorized_inspectors():
    """Filter before listing; reuse actual user/group grants and active custom roles."""
    grant = Q(user_permissions__codename=INSPECTION_PERMISSION, user_permissions__content_type__app_label='accounts')
    grant |= Q(groups__permissions__codename=INSPECTION_PERMISSION, groups__permissions__content_type__app_label='accounts')
    inactive = Role.objects.filter(is_active=False).annotate(key=Lower(Trim('role_name'))).values('key')
    return User.objects.filter(is_active=True, is_suspended=False).filter(grant | Q(is_superuser=True)).annotate(
        inspection_role=Lower(Trim('role'))).exclude(inspection_role__in=NON_INSPECTOR_ROLES).exclude(
        inspection_role__in=Subquery(inactive)).distinct().order_by('first_name', 'last_name', 'username')


def default_inspector_id(record, staff, assigned=None):
    """An edit keeps its actual inspector; only a new record defaults to assignment."""
    saved = (record.get('inspector') or {}).get('id') if record else (assigned or {}).get('id')
    return saved if any(str(person['id']) == str(saved) for person in staff) else None


def condition_display(record):
    """Read historical free text without silently changing a saved inspection."""
    value = str(record.get('condition') or '')
    other = str(record.get('condition_other') or '')
    selected = value if value in CONDITION_CHOICES else 'Other' if value else ''
    if value and value not in CONDITION_CHOICES:
        other = value
    return {'value': selected, 'other': other,
            'label': f'Other: {other}' if value == 'Other' and other else value or 'Not recorded'}


def validate_condition(data):
    from .booking_workflow import text
    condition = text(data, 'condition', required=True)
    if condition not in CONDITION_CHOICES:
        raise ValidationError('Select a valid facility condition.')
    other = text(data, 'condition_other') if condition == 'Other' else ''
    if condition == 'Other' and not other:
        raise ValidationError('Specify the facility condition when Other is selected.')
    return {'condition': condition, 'condition_other': other}


def inspection_shortcuts(booking, permitted):
    """Row-menu metadata reuses the same phase guards as the detail form."""
    from .booking_workflow import inspection_actions
    from .schedules import metadata
    saved = metadata(booking).get('inspections') or {}
    result = []
    if saved.get('pre') and saved.get('post'):
        result.append({'action': 'inspection_details', 'label': 'View Inspection'})
    elif saved.get('pre'):
        result.append({'action': 'pre_inspection_details', 'label': 'View Pre-Use Inspection'})
    elif saved.get('post'):
        result.append({'action': 'post_inspection_details', 'label': 'View Post-Use Inspection'})
    if 'inspection' in permitted:
        for kind in inspection_actions(booking):
            if not saved.get(kind):
                result.append({'action': f'inspection_{kind}', 'label': f'Record {kind.title()}-Use Inspection'})
    return result


def same_inspection(previous, candidate):
    """Compare user-edited content, not save timestamps/actors or offset spelling."""
    from django.utils.dateparse import parse_datetime
    keys = ('condition', 'condition_other', 'remarks', 'existing_damage', 'has_damage',
            'damage_found', 'deposit_decision', 'issues_resolved_confirmed', 'attachment')
    if not previous or any(previous.get(key, '' if key == 'condition_other' else None) != candidate.get(key) for key in keys):
        return False
    if (previous.get('inspector') or {}).get('id') != (candidate.get('inspector') or {}).get('id'):
        return False
    try:
        return parse_datetime(str(previous.get('inspected_at') or '')) == parse_datetime(candidate['inspected_at'])
    except ValueError:
        return False
