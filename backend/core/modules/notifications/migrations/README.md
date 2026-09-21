# Notifications migrations index

**Schema owner:** `api` app (`backend/core/api/migrations/`)

| Migration | What it adds |
|-----------|----------------|
| `0004_passwordresetcode_productinteraction.py` | Password reset codes |
| `0005_gmailconfig.py` | Gmail SMTP config |

**Models:** `api.models` — `GmailConfig`, `PasswordResetCode`

**Services:** `modules/notifications/services/email_service.py`

**Admin UI:** `modules/notifications/templates/`
