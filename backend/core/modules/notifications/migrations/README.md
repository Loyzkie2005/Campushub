# Notifications migrations index

**Schema owner:** `api` app (`backend/core/api/migrations/`)

| Migration | What it adds |
|-----------|----------------|
| `0004_passwordresetcode_productinteraction.py` | Password reset codes |
| `0005_gmailconfig.py` | Gmail SMTP config |
| `0043_product_approval_push.py` | Mobile FCM installation ownership and per-device approval delivery outbox |
| `0044_product_push_decision.py` | Add approval/rejection decision to that same outbox; preserve existing approval rows |

**Models:** `api.models` — `GmailConfig`, `PasswordResetCode`, `PushDeviceRegistration`, `ProductApprovalPush`. The module re-exports these models; it does not duplicate their schema.

**Services:** `modules/notifications/services/email_service.py`

**Admin UI:** `modules/notifications/templates/`

For product reviews, the existing bearer authenticator supplies the real mobile owner and verified login expiry to `mobile_views.device_registration`. `Product.approve` and `Product.reject` write deliveries inside the review transaction only on a real status transition. The separate `send_product_approval_pushes` command retains its deployment name, sees committed rows and calls `services.push_service.dispatch_delivery`, which rechecks ownership/session/current decision and sends using Firebase Admin. Inputs are an authenticated installation ID and a real review event; outputs are a stored binding and delivery state. Migration0044 defaults historical rows to approved; the legacy approved_at column remains the event timestamp for compatibility. No email-address identity mapping or duplicate activity log is created. See `docs/mobile-fcm.md` at the project root for current lines, configuration, testing and a safe practice exercise.
