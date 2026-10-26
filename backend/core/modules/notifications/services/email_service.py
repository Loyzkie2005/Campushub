"""Gmail SMTP — settings.py / gmail_local.py / optional PostgreSQL fallback."""

import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMessage, get_connection

from api.models import GmailConfig

logger = logging.getLogger(__name__)


@dataclass
class _SmtpConfig:
    gmail_user: str
    gmail_app_password: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    use_ssl: bool = False


def _from_settings() -> _SmtpConfig | None:
    user = (getattr(settings, "CAMPUSHUB_GMAIL_USER", "") or "").strip()
    password = (getattr(settings, "CAMPUSHUB_GMAIL_APP_PASSWORD", "") or "").replace(" ", "")
    if not user or not password:
        return None
    return _SmtpConfig(
        gmail_user=user,
        gmail_app_password=password,
        smtp_host=getattr(settings, "CAMPUSHUB_SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(getattr(settings, "CAMPUSHUB_SMTP_PORT", 587)),
        use_ssl=getattr(settings, "CAMPUSHUB_SMTP_USE_SSL", False),
    )


def _from_database() -> _SmtpConfig | None:
    row = GmailConfig.get_active()
    if row is None:
        return None
    return _SmtpConfig(
        gmail_user=row.gmail_user,
        gmail_app_password=row.gmail_app_password.replace(" ", ""),
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        use_ssl=row.smtp_port == 465,
    )


def get_smtp_config() -> _SmtpConfig | None:
    return _from_settings() or _from_database()


def is_gmail_configured() -> bool:
    return get_smtp_config() is not None


def _send_with_config(config: _SmtpConfig, *, to_email: str, subject: str, body: str) -> None:
    connection = get_connection(
        host=config.smtp_host,
        port=config.smtp_port,
        username=config.gmail_user,
        password=config.gmail_app_password,
        use_ssl=config.use_ssl,
        use_tls=not config.use_ssl,
        timeout=settings.EMAIL_TIMEOUT,
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=config.gmail_user,
        to=[to_email],
        connection=connection,
    )
    if email.send(fail_silently=False) != 1:
        raise RuntimeError("SMTP did not accept the recovery email.")


def send_password_reset_email(*, to_email: str, code: str, full_name: str = "") -> bool:
    """Compatibility sender: use the same code-only recovery template."""
    return send_account_recovery_email(to_email=to_email, code=code, purpose="password", full_name=full_name)


def send_account_recovery_email(*, to_email, code, purpose, full_name=""):
    """Deliver a code privately; never create or email recovery URLs."""
    config = get_smtp_config()
    if config is None:
        return False
    verification = purpose == "email_verification"
    subject = "CampusHub Email Verification Code" if verification else "CampusHub Account Recovery Code"
    label = "email verification" if verification else "account recovery"
    body = (f"Hi {full_name.split()[0] if full_name else 'CampusHub user'},\n\n"
            f"Your CampusHub {'email' if verification else label} verification code is:\n\n{code}\n\n"
            f"This code expires in {settings.PASSWORD_RESET_CODE_MINUTES} minutes and can only be used once.\n"
            f"Enter this code in the CampusHub app to continue {label}.\n\n"
            "If you did not request this, you may ignore this email.\n\nCampusHub")
    _send_with_config(config, to_email=to_email, subject=subject, body=body)
    return True
