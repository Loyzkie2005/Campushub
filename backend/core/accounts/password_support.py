"""Information-only admin assistance and existing owner recovery compatibility."""
from django.conf import settings

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET

from api.models import CampusHubUser, PasswordResetCode
from .models import AccountActivity, AdminTabToken, User
from .activity_logging import log_account_activity
from .user_management import resolve_account, strict_password_errors


from .recovery_codes import mask_email


@require_GET
@never_cache
def account_recovery_start(request):
    """Owner entry page; JavaScript reuses the existing code-only JSON endpoints."""
    response = render(request, "user_management/pages/account_recovery_start.html")
    response["Referrer-Policy"] = "no-referrer"
    return response


def initiate_reset(request):
    """Deny retired admin mutation aliases; owners use the existing recovery API."""
    from django.http import JsonResponse
    message = "Assist Account Recovery is information-only. The account owner must use Forgot Username or Password in CampusHub."
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"error": message}, status=403)
    raise PermissionDenied(message)


def _password_version(account):
    from django.utils.crypto import salted_hmac
    password = account.password if isinstance(account, User) else account.password_hash
    return salted_hmac("recovery-version", password).hexdigest()


@sensitive_post_parameters("code", "new_password", "confirm_password")
@never_cache
@transaction.atomic
def account_recovery(request, token):
    """Owner-only verification and password form, independent of the admin session."""
    from django.core import signing
    from .reset_codes import verify_reset_code
    from django.contrib.auth.hashers import make_password
    reset, account, source = None, None, None
    try:
        pk = signing.loads(token, salt="campushub-account-recovery", max_age=settings.PASSWORD_RESET_CODE_MINUTES*60)
        reset = PasswordResetCode.objects.get(pk=pk)
        source, candidate = resolve_account(reset.account_ref)
        if candidate is not None:
            account = type(candidate).objects.select_for_update().get(pk=candidate.pk)
        reset = PasswordResetCode.objects.select_for_update().get(pk=pk)
    except (signing.BadSignature, PasswordResetCode.DoesNotExist, User.DoesNotExist, CampusHubUser.DoesNotExist, ValueError, TypeError):
        pass
    eligible = bool(reset and account and reset.expires_at > timezone.now() and account.is_active
        and not account.is_suspended and account.email.casefold() == reset.email.casefold()
        and (reset.purpose == "email_verification" or account.email_verified))
    grant = request.session.get("account_recovery_grant", {})
    proved = bool(eligible and reset and account and reset.used and reset.code_hash and reset.purpose == "password"
        and grant.get("id") == reset.pk and grant.get("version") == _password_version(account)
        and grant.get("expires", 0) > timezone.now().timestamp())
    valid = eligible and bool(reset and (not reset.used or proved))
    errors, complete, username = [], False, ""
    if request.method == "POST" and valid and reset is not None and account is not None:
        if not proved:
            code = request.POST.get("code", "").strip()
            if not verify_reset_code(reset, code):
                errors.append("Invalid or expired verification code.")
            else:
                reset.used = True
                reset.save(update_fields=["used"])
                # Proof applies only to the exact email captured when the code was sent.
                account.email_verified = True
                account.save(update_fields=["email_verified"])
                if reset.purpose == "password":
                    request.session.cycle_key()
                    request.session["account_recovery_grant"] = {"id": reset.pk,
                        "version": _password_version(account), "expires": reset.expires_at.timestamp()}
                    return redirect("account_recovery", token=token)
                complete = True
                if reset.purpose == "username":
                    username = account.username
                log_account_activity(request, source=source, account=account,
                    activity_type="USERNAME_RECOVERY_COMPLETED" if reset.purpose == "username" else "EMAIL_VERIFIED",
                    activity="Account owner completed email verification" if reset.purpose == "email_verification" else "Account owner recovered username",
                    module="Authentication", result=AccountActivity.RESULT_SUCCESS)
        else:
            password = request.POST.get("new_password", "")
            errors = strict_password_errors(password)
            if password != request.POST.get("confirm_password", ""):
                errors.append("Passwords do not match.")
            validator_user = account if isinstance(account, User) else User(username=account.username,
                email=account.email, first_name=account.first_name, last_name=account.last_name)
            try:
                validate_password(password, validator_user)
            except ValidationError as exc:
                errors.extend(exc.messages)
            if not errors:
                if source == "admin":
                    account.set_password(password)
                    account.save(update_fields=["password"])
                    AdminTabToken.objects.filter(user=account).delete()
                else:
                    account.password_hash = make_password(password)
                    account.save(update_fields=["password_hash", "updated_at"])
                request.session.pop("account_recovery_grant", None)
                PasswordResetCode.objects.filter(account_ref=reset.account_ref, used=False).update(used=True)
                log_account_activity(request, source=source, account=account, activity_type="PASSWORD_RESET_COMPLETED",
                    activity="Password reset completed by account owner", module="Authentication", result=AccountActivity.RESULT_SUCCESS)
                complete = True
    response = render(request, "user_management/pages/account_recovery.html", {
        "valid_link": valid, "proved": proved, "complete": complete, "errors": errors,
        "recovered_username": username, "masked_email": mask_email(reset.email) if reset else "",
        "purpose": reset.purpose if reset else "", "title": {"username": "Recover Username", "password": "Reset Password", "email_verification": "Verify Email"}.get(reset.purpose if reset else "", "Account Recovery")})
    response["Referrer-Policy"] = "no-referrer"
    return response


@sensitive_post_parameters("new_password", "confirm_password")
@never_cache
@transaction.atomic
def account_password_reset_confirm(request, uidb64, token):
    try:
        account = User.objects.select_for_update().get(pk=urlsafe_base64_decode(uidb64).decode())
    except (User.DoesNotExist, ValueError, TypeError, UnicodeDecodeError, OverflowError):
        account = None
    valid = bool(account and account.is_active and not account.is_suspended
                 and default_token_generator.check_token(account, token))
    errors, complete = [], False
    if request.method == "POST" and valid and account is not None:
        password = request.POST.get("new_password", "")
        errors = strict_password_errors(password)
        if password != request.POST.get("confirm_password", ""):
            errors.append("Passwords do not match.")
        try:
            validate_password(password, account)
        except ValidationError as exc:
            errors.extend(exc.messages)
        if not errors:
            account.set_password(password)
            account.save(update_fields=["password"])
            AdminTabToken.objects.filter(user=account).delete()
            log_account_activity(request, source="admin", account=account, activity_type="PASSWORD_RESET_COMPLETED",
                activity="Password reset completed by account owner", module="Authentication", result=AccountActivity.RESULT_SUCCESS)
            complete = True
    response = render(request, "user_management/pages/password_reset_confirm.html",
        {"valid_link": valid, "errors": errors, "complete": complete})
    response["Referrer-Policy"] = "no-referrer"
    return response
