"""Shared code issuance and owner proof for self-service web/mobile recovery.

Callers hold the account lock inside an atomic transaction before code-row locks.
The existing code_hash stores a hashed code, then a hashed completion nonce.
No new inventory, identity, token table, or plaintext secret is needed.
"""
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from api.models import CampusHubUser, PasswordResetCode
from .models import User, AdminTabToken, AccountActivity
from .activity_logging import log_account_activity
from .reset_codes import verify_reset_code
from .user_management import strict_password_errors

logger = logging.getLogger(__name__)


class RecoveryError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status
        super().__init__(message)


def mask_email(email):
    local, separator, domain = (email or "").partition("@")
    return f"{local[:2]}***@{domain}" if separator else "No email recorded"


def find_account(email):
    """Fail closed if the recorded email identifies multiple account records."""
    matches = [(source, user) for source, model in (("mobile", CampusHubUser), ("admin", User))
               for user in model.objects.filter(email__iexact=email)[:2]]
    return matches[0] if len(matches) == 1 else (None, None)


def password_version(account):
    from django.utils.crypto import salted_hmac
    value = account.password if isinstance(account, User) else account.password_hash
    return salted_hmac("recovery-version", value).hexdigest()


def audit(request, source, account, action, purpose, *, assisted=False):
    metadata = {"purpose": purpose}
    if assisted:
        metadata["actor_admin_id"] = request.user.pk
    log_account_activity(request, source=source, account=account, activity_type=action,
                         activity=action.replace("_", " ").title(),
                         module="User Management" if assisted else "Authentication",
                         result=AccountActivity.RESULT_SUCCESS, metadata=metadata)


@sensitive_variables()
def send_code(request, source, account, purpose, *, assisted=False):
    from modules.notifications.services.email_service import send_account_recovery_email
    # Admin assistance is information-only, including legacy/internal callers.
    if assisted:
        raise RecoveryError("Recovery codes must be requested by the account owner through self-service recovery.", 403)
    if purpose not in {"password", "username", "email_verification"}:
        raise RecoveryError("Unsupported recovery purpose.")
    if not account.email or not account.is_active or account.is_suspended:
        raise RecoveryError("An active account and recorded email are required.")
    if purpose != "email_verification" and not account.email_verified:
        raise RecoveryError("Email not verified. Verify your recorded email before account recovery.")
    found_source, found = find_account(account.email)
    if found is None or found_source != source or found.pk != account.pk:
        raise RecoveryError("Recovery unavailable for ambiguous account records.")
    now, ref = timezone.now(), f"{source}:{account.pk}"
    rows = PasswordResetCode.objects.filter(email__iexact=account.email)
    if rows.filter(created_at__gte=now-timedelta(minutes=1)).exists():
        raise RecoveryError("Wait one minute before requesting another verification code.", 429)
    if rows.filter(created_at__gte=now-timedelta(hours=1)).count() >= 5:
        raise RecoveryError("Too many code requests. Please try again later.", 429)
    # Supersede both unused codes and already-issued completion grants.
    rows.update(used=True, code_hash="")
    code = f"{secrets.randbelow(1000000):06d}"
    row = PasswordResetCode.objects.create(email=account.email.lower(), account_ref=ref,
        purpose=purpose, code_hash=make_password(code),
        expires_at=now+timedelta(minutes=settings.PASSWORD_RESET_CODE_MINUTES))
    try:
        sent = send_account_recovery_email(to_email=account.email, code=code, purpose=purpose,
                                         full_name=account.first_name)
    except Exception as exc:
        # Never log SMTP response text: it can contain addresses or credentials.
        logger.warning("Recovery email delivery failed (%s). Check SMTP configuration/network.", type(exc).__name__)
        sent = False
    if not sent:
        row.used = True
        row.code_hash = ""
        row.save(update_fields=["used", "code_hash"])
        log_account_activity(request, source=source, account=account,
            activity_type="ACCOUNT_RECOVERY_DELIVERY_FAILED", activity="Recovery email delivery failed",
            module="User Management" if assisted else "Authentication", result=AccountActivity.RESULT_FAILED,
            metadata={"purpose": purpose, **({"actor_admin_id": request.user.pk} if assisted else {})})
        raise RecoveryError("Unable to send recovery instructions. Please try again later.", 503)
    kind = "EMAIL_VERIFICATION" if purpose == "email_verification" else "ACCOUNT_RECOVERY"
    from .support_scope import is_administrator_account
    initiated = "SELF_SERVICE_RECOVERY_INITIATED" if not assisted and purpose != "email_verification" and is_administrator_account(source, account) else f"{kind}_INITIATED"
    for action in (initiated, f"{kind}_CODE_SENT"):
        audit(request, source, account, action, purpose, assisted=assisted)
    # Preserve existing support reports that read these initiation types.
    if purpose in {"password", "username"}:
        audit(request, source, account, "PASSWORD_RESET_INITIATED" if purpose == "password"
              else "USERNAME_RECOVERY_INITIATED", purpose, assisted=assisted)
    return {"message": "Verification Code Sent", "email_sent": True,
            "masked_email": mask_email(account.email), "expires_in": settings.PASSWORD_RESET_CODE_MINUTES * 60,
            "resend_after": 60, "step": 2}


@sensitive_variables()
def verify_code(request, source, account, code, purpose):
    if purpose not in {"password", "username", "email_verification"}:
        raise RecoveryError("Unsupported recovery purpose.")
    ref = f"{source}:{account.pk}"
    row = PasswordResetCode.objects.select_for_update().filter(
        email__iexact=account.email, account_ref=ref, purpose=purpose).order_by("-created_at", "-pk").first()
    if row is None or row.used or not account.is_active or account.is_suspended:
        raise RecoveryError("Invalid verification code.")
    if row.expires_at <= timezone.now():
        raise RecoveryError("This verification code has expired.")
    if purpose != "email_verification" and not account.email_verified:
        raise RecoveryError("Email not verified. Verify your recorded email before account recovery.")
    if not isinstance(code, str) or len(code) != 6 or not code.isascii() or not code.isdigit():
        # Count malformed guesses too; do not let syntax bypass the attempt limit.
        verify_reset_code(row, "invalid")
        raise RecoveryError("Invalid verification code.")
    if not verify_reset_code(row, code):
        raise RecoveryError("Invalid verification code.")
    row.used = True  # A second verify request must fail immediately.
    nonce = secrets.token_urlsafe(32)
    row.code_hash = make_password(nonce) if purpose == "password" else ""
    row.save(update_fields=["used", "code_hash"])
    kind = "EMAIL_VERIFICATION" if purpose == "email_verification" else "ACCOUNT_RECOVERY"
    audit(request, source, account, f"{kind}_CODE_VERIFIED", purpose)
    if purpose == "username":
        audit(request, source, account, "USERNAME_RECOVERED", purpose)
        return {"message": "Username recovered.", "username": account.username}
    if purpose == "email_verification":
        account.email_verified = True
        account.save(update_fields=["email_verified"])
        audit(request, source, account, "EMAIL_VERIFIED", purpose)
        return {"message": "Email verified.", "email_verified": True}
    grant = signing.dumps({"id": row.pk, "ref": ref, "nonce": nonce,
                           "version": password_version(account)}, salt="campushub-recovery-completion")
    return {"message": "Code verified.", "recovery_grant": grant}


@sensitive_variables()
def confirm_password(request, source, account, grant, password, confirmation):
    if not isinstance(grant, str):
        raise RecoveryError("Invalid recovery proof.")
    try:
        proof = signing.loads(grant, salt="campushub-recovery-completion", max_age=900)
    except (signing.BadSignature, TypeError, ValueError):
        raise RecoveryError("Recovery expired or already used. Request a new code.")
    ref = f"{source}:{account.pk}"
    if not isinstance(proof, dict) or proof.get("ref") != ref:
        raise RecoveryError("Invalid recovery proof.")
    row = PasswordResetCode.objects.select_for_update().filter(pk=proof.get("id"),
        account_ref=ref, email__iexact=account.email, purpose="password", used=True).first()
    if (row is None or row.expires_at <= timezone.now() or not row.code_hash
            or not account.is_active or account.is_suspended or not account.email_verified
            or proof.get("version") != password_version(account)
            or not check_password(proof.get("nonce", ""), row.code_hash)):
        raise RecoveryError("Recovery expired or already used. Request a new code.")
    errors = strict_password_errors(password)
    if password != confirmation:
        errors.append("Passwords do not match.")
    try:
        validate_password(password, account)
    except ValidationError as exc:
        errors.extend(exc.messages)
    if errors:
        raise RecoveryError(" ".join(errors))
    if source == "admin":
        account.set_password(password)
        account.save(update_fields=["password"])
        AdminTabToken.objects.filter(user=account).delete()
    else:
        account.password_hash = make_password(password)
        account.save(update_fields=["password_hash", "updated_at"])
    PasswordResetCode.objects.filter(email__iexact=account.email).update(used=True, code_hash="")
    audit(request, source, account, "PASSWORD_RESET_COMPLETED", "password")
    return {"message": "Password Updated Successfully"}
