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
    )


def get_smtp_config() -> _SmtpConfig | None:
    return _from_settings() or _from_database()


def is_gmail_configured() -> bool:
    return get_smtp_config() is not None


def _send_with_config(config: _SmtpConfig, *, to_email: str, subject: str, body: str) -> None:
    if config.use_ssl:
        connection = get_connection(
            host=config.smtp_host,
            port=config.smtp_port,
            username=config.gmail_user,
            password=config.gmail_app_password,
            use_ssl=True,
        )
    else:
        connection = get_connection(
            host=config.smtp_host,
            port=config.smtp_port,
            username=config.gmail_user,
            password=config.gmail_app_password,
            use_tls=True,
        )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=config.gmail_user,
        to=[to_email],
        connection=connection,
    )
    email.send(fail_silently=False)


def send_password_reset_email(*, to_email: str, code: str, full_name: str = "") -> bool:
    config = get_smtp_config()
    if config is None:
        logger.warning(
            "Gmail not configured. Edit backend/core/core/gmail_local.py "
            "and set CAMPUSHUB_GMAIL_APP_PASSWORD"
        )
        return False

    greeting = f"Hi {full_name}," if full_name else "Hi,"
    subject = "CampusHub Password Reset Code"
    body = (
        f"{greeting}\n\n"
        f"Your CampusHub password reset code is: {code}\n\n"
        f"This code expires in {settings.PASSWORD_RESET_CODE_MINUTES} minutes.\n"
        f"If you did not request this, you can ignore this email.\n\n"
        f"— CampusHub Team"
    )

    # Try STARTTLS on 587, then SSL on 465 (some networks block one port).
    attempts = [
        _SmtpConfig(
            config.gmail_user,
            config.gmail_app_password,
            config.smtp_host,
            587,
            use_ssl=False,
        ),
        _SmtpConfig(
            config.gmail_user,
            config.gmail_app_password,
            config.smtp_host,
            465,
            use_ssl=True,
        ),
    ]

    last_error = None
    for attempt in attempts:
        try:
            _send_with_config(attempt, to_email=to_email, subject=subject, body=body)
            logger.info("Password reset email sent to %s", to_email)
            return True
        except Exception as exc:
            last_error = exc
            logger.warning("Gmail send failed on port %s: %s", attempt.smtp_port, exc)

    if last_error:
        raise last_error
    return False
