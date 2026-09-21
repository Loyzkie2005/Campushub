"""
Notifications ORM models.

Gmail / password-reset config migrations live in `api/migrations/`.
See `migrations/README.md` in this folder for the migration index.
"""

from api.models import GmailConfig, PasswordResetCode

__all__ = [
    "GmailConfig",
    "PasswordResetCode",
]
