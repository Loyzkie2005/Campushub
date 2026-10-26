# Marketplace Admin: scoped account support and monitoring

## Current implementation: information-only recovery assistance (October 10, 2026)

This section supersedes the earlier admin code-sending instructions below. SMTP fixes still apply to **owner self-service email delivery**. Earlier line numbers and code-sending screenshots describe historical versions, not the current modal.

### 1. Cause / reason

The latest requested workflow keeps code issuance and private password entry on the account owner's device. The existing admin modal had a form, recovery-action radios, send/resend controls and code-sent states. Those were a second entry point into owner recovery and are now removed. Hiding the button alone would leave callable POST aliases, so the server rejects them too.

**Confirmed model/flow inspection:** `accounts.User` and `api.CampusHubUser` both store `contact_number` and `email_verified`. Neither stores phone/SMS verification. The Flutter recovery dialog and shared recovery API are email-only; no SMS provider was found. A contact number is not proof of verification. Therefore SMS displays the masked stored contact plus **Not Verified**, and the modal explicitly says SMS recovery is not configured. The requested verified-SMS scenario cannot honestly be implemented without a separate SMS integration. No provider, verification flag or fictional status was added.

### 2. Exact files changed / current lines / nearby anchors

| Project-relative file | Current line / anchor | Added, changed or removed |
|---|---|---|
| `backend/core/accounts/user_management.py` | 283 `mask_recovery_phone`; 293 `build_account_rows`; 339 `can_assist_recovery` | Mask the stored contact number; serialize information-view eligibility, real email verification, honest SMS availability and Marketplace referral. Retire reset/recovery/verify mutation capabilities to False. Missing email does not hide assistance: the admin must be able to see the warning. |
| `backend/core/accounts/support_scope.py` | 51 `can_assist_recovery_actor`; 58 `can_view_recovery_info` | Rename the old reset eligibility helper to information-view authorization. Retain grants/Facilities exclusion/admin classification; match exact Program/Major using existing scope validation and loaded foreign keys, avoiding per-row account queries. |
| `backend/core/accounts/password_support.py` | 33 `initiate_reset` | Replace admin code sending with unconditional 403, JSON for AJAX and PermissionDenied for plain requests. Preserve legacy owner resolution and password-proof handling. |
| `backend/core/accounts/recovery_codes.py` | 63 `send_code`; 66 `if assisted` | Reject all assisted callers before code/mail/audit writes; keep owner code issuance, expiry, rates, verification, one-use completion proof and password validation. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 131 menu condition; 218 `accountRecoveryModal`; 241 JS version | Menu uses read eligibility. Modal has identity, Recovery Methods, guidance, warning/referral and only Close. The existing Bootstrap scrollable-dialog class keeps header/footer visible on short screens. Remove form, hidden mutation payload, radios, send/resend/code-sent states. Cache versions change for both assets. |
| `backend/static/components/js/admin_users.js` | 145 `recoveryModal`; 148 `.assist-recovery` | Build safe text-only details/method rows; show verified-method guidance or warning/referral. Remove recovery fetch/CSRF payload/timers entirely. Restore focus to the row's three-dot button on dismissal. Other actions retain their forms. |
| `backend/static/components/css/admin_users.css` | 463 `.recovery-methods-title` | Remove recovery radio styles, add a small navy heading, reuse existing detail rows/helper/warning styles. No whole-page redesign. |
| `campushub/lib/module_app/screens/components/account_recovery_dialog.dart` | 213 `Use your recorded, verified email` | Replace the obsolete admin-sent-code instruction with owner request guidance. No mobile state machine or endpoint changes. |
| `backend/core/accounts/test_recovery_information.py` | 15 `RecoveryInformationTests` | Add read-only/masking/no-email/scope/alias/service security regressions with isolated DB records and mocked mail. |
| `backend/core/accounts/test_recovery_transport.py` | 33 `test_tab_authenticated_page_has_information_only_modal` | Test read-only HTML, real tab/CSRF denial and retained mocked SMTP behavior. |
| `backend/core/accounts/test_recovery_eligibility.py` | 14 policy import; 92 ordinary-user information test | Retain admin exclusion, Program/Major, Facilities and owner-admin self-service tests; replace admin-code expectations with denial/no issuance. |
| `backend/core/accounts/test_recovery_code_flow.py` | 30 `send` | Owner APIs now create test codes; initial email verification uses an authenticated owner token. Keep proof, expiry, retries and private password-completion assertions. |
| `backend/core/accounts/test_account_recovery.py` | 36 `delivery` | Owner API supplies codes for legacy compatibility tests; retain scope/CSRF/owner-proof tests and render updated browser fixtures. |
| `backend/core/accounts/test_marketplace_support.py` | 106 mobile owner test; 126 failure test; 224 expiry test | First assert admin reset is denied, then exercise owner delivery/verification; retain unrelated support and seller tests. |
| `backend/core/accounts/test_user_management.py` | 184 `test_audit_records_changes_without_credentials_and_has_real_recent_activity` | Test initiation audit through owner API rather than retired admin send. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest recovery policy | Save current behavior for future coding work. |
| `docs/user-management.md` | 3 current recovery guidance | Explain current user-facing flow and link this full debugging/implementation guide. |
| `scratch/account-recovery/check.cjs` | information-only browser assertions | Development QA only: check keyboard/menu/modal layout, no fetch/submission, masked methods, warning/referral and owner recovery screens. Not shipped as application code. |

### 3. Changes made

Admin assistance now **reads and guides**. Normal eligible users get Assist Account Recovery in the existing three-dot menu. Super Admin sees ordinary users globally. Marketplace Admin sees only exact academic-scope ordinary users; BTLED must match Major and missing actor scope fails closed. Administrator targets (built-in/custom roles, staff/super flags or actual admin authority) are excluded before the action is shown. Facilities Admin remains OFF. Other view/activity/edit/seller/account actions are retained.

The modal shows User, Username / School ID, applicable Program / Major and masked Email/SMS. Email uses the existing `email_verified` field. A verified email shows ?Use a verified recovery method to continue.? Without a verified method it shows ?No verified recovery method is currently available for this account.? Marketplace additionally receives the Super Admin referral. No emergency reset is introduced. Opening or closing the modal sends no recovery request and creates no recovery audit event; ordinary viewing was not audited previously.

### 4. How it works: functions, inputs/outputs and data flow

1. Django `build_account_rows(actor)` reads the existing scoped account querysets and a batched administrator-authority query. Input: signed-in admin. Output: existing user rows plus masked recovery fields and the information-only action flag.
2. `can_view_recovery_info(actor, source, account, has_admin_authority=...)` checks the existing recovery permission, actor role, stored target identity/authority and Program/Major. The optional authority flag comes from the server's batched DB query, never from a browser. It authorizes **reading guidance**, not resetting a password.
3. `mask_email(email)` keeps the first two local-part characters and email domain. `mask_recovery_phone(contact)` keeps only ASCII digits, masks short numbers completely, and otherwise keeps the first two/last three digits. Missing/unusable contact gives ?Not recorded?. It does not verify or normalize the stored phone for SMS delivery.
4. The template renders only an eligible action. `admin_users.js` reads the authorized row, inserts values using the existing `appendField`/`textContent` helper, then opens Bootstrap's existing modal. No `fetch`, mutation form or code timer is involved. Bootstrap handles focus containment/Escape; the close handler returns focus to the original row button.
5. The account owner uses mobile ?Forgot Username or Password?? and the existing email API. Owner email proof still controls username release and password completion. Admins cannot read their codes/proofs through the Users modal.

Annotated example (display-only, not seeded into production):

```python
mask_recovery_phone("09817149863")  # -> "09*****863", not a verified SMS method
# An actual email_verified=True account gets verified-email guidance.
# An actual email_verified=False account gets a warning and, for Marketplace, referral.
```

### 5. Backend / API behavior

The existing `/admin-users/action/` handler (`accounts/views.py:618`, `admin_users_action`) still requires login, RBAC and CSRF. All three historical mutation aliases (`assist_recovery`, `reset_password`, `verify_email`) call `initiate_reset` and return 403 **for every actor and target**, including Super Admin. They create no code, send no message, log no recovery initiation and change no password/verification flag. `send_code(..., assisted=True)` independently returns a `RecoveryError` with status 403 before writes.

Existing owner request/verify/confirm APIs and initial authenticated email verification remain. Owner username/password codes are emailed only to an eligible recorded email; proof remains required before disclosure/change. Codes, password hashes, grants and credentials are never added to the admin assistance fields. The legacy permission codename `can_reset_user_password` is retained as an access grant for assistance information, not permission to set a password. No duplicate API, SMS workflow, read-audit action or emergency reset route is added.

### 6. Database / migration impact

No new account field, migration or production data writes. `sms_verified=False` and `sms_recovery_available=False` are **display capabilities**, not new database fields; they document the absence of a configured SMS workflow. Existing contact numbers, email flags, assignments and passwords are retained. Tests create isolated test records and mock all mail.

### 7. Tests performed / verification

Actual results (isolated test DB, all mail mocked):

- **204 Django regression tests passed**, 163.130 seconds: new recovery information, transport/SMTP, administrator eligibility, code flow, owner compatibility, Marketplace support, Users, roles/permissions, accounts and admin orders. Log: `scratch/recovery-information-regression-final.log`.
- **8 focused Django tests passed**, 4.644 seconds, after the final scrollable-modal template change: information security plus fresh browser fixture export. Log: `scratch/recovery-information-modal-final.log`.
- **10 real headless Chrome scenarios passed**, including Marketplace at 1440/768/375/320px, Super, unverified-email referral, legacy owner form and owner password/username/initial-email screens. Mobile height is 667px. Checked modal fit, masked text, no recovery fetch/form submission, zero JS errors, menu navigation, Escape/focus restoration and reopening. Log: `scratch/recovery-information-browser-final.log`; screenshots: `scratch/account-recovery/*-information.png`. Visually inspected the unverified mobile screenshot before and after making the body scrollable.
- **13 Flutter tests passed**: `recovery_code_input_test.dart` and `login_layout_test.dart`. Log: `scratch/recovery-information-flutter.log`.
- `node --check backend/static/components/js/admin_users.js` passed.
- `manage.py check` reported zero issues; `manage.py makemigrations --check --dry-run` reported no changes.

The initial Django run had nine errors from removing `resolve_account`, which the legacy owner route still needs. The import was restored; the final full suite above passed. Browser QA also found that a floating menu has no table-row ancestor at click time. Capture its row action button **when registering the handler**, before Bootstrap moves the menu to the document body; this now opens correctly and restores focus. QA waits for Bootstrap's fade to finish before testing Escape. These were confirmed test failures corrected during implementation, not unresolved defects.

Reproduce from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test accounts.test_recovery_information accounts.test_recovery_transport accounts.test_recovery_eligibility accounts.test_recovery_code_flow accounts.test_account_recovery accounts.test_marketplace_support accounts.test_user_management accounts.test_roles_permissions accounts.tests modules.marketplace.test_orders_admin --noinput
```

Manual checks on your own development accounts (not claimed as a live-phone or actual-mail test):

1. Open Users as a Marketplace Admin. An in-scope ordinary student shows Assist Account Recovery; a different Program/Major and any administrator do not. Facilities Admin has no Users access.
2. Open a verified-email ordinary user: masked Email says Verified; SMS says Not Verified/not configured; only Close appears. Tab and Escape work; after dismissal focus returns to the three-dot button.
3. Open an ordinary account with no verified email: see the no-method warning and Marketplace referral. As Super, view the same information without a Marketplace referral. Missing email must still show assistance information.
4. At a narrow/short viewport, scroll the modal body to read the referral; header/footer and Close remain visible. Network must show zero recovery POSTs from opening/closing this modal.
5. On the owner's mobile app use Forgot Username or Password with a genuinely recorded verified email; request/verify a code and recover the username or choose a private password. Unverified email must use the existing owner initial-verification flow first. Actual mail delivery requires a separate intentional end-to-end test.


### 8. Remaining limitations and debugging

- SMS verification/recovery is not implemented in this checkout. Do not treat any phone number as verified. The mobile chooser mentioned in the brief is not present in the inspected code. This update preserves the existing email flow rather than inventing SMS support.
- Email/verification info is a snapshot at page load. Refresh Users after the owner verifies or updates an email. No live poll/new recovery API is added.
- Accounts with no verified method need Super Admin assistance outside this modal. No emergency password-setting mechanism is supported here.
- No real email/SMS is sent during this task; mocked mail proves workflow behavior, not inbox delivery. Existing SMTP configuration/authentication findings in the earlier section remain separate from delivery.
- Old signed owner links remain compatible with their existing expiry/proof rules; no admin action creates or emails new links.

Troubleshooting:

1. Old send button still visible? Hard refresh after deploy/restart and confirm both assets use `20261010-recovery-info`. Do not weaken permissions or CSRF.
2. Action missing? Confirm actor grant and Program/Major, then inspect the stored target role/flags/admin authority. Missing email alone should not hide assistance.
3. SMS says Not Verified although phone exists? Expected: there is no SMS verification field/provider. Fixing display text cannot establish proof.
4. A stale client POST gets 403? Expected: admin mutations are retired. Guide the owner to mobile recovery.
5. Owner code fails? Debug the owner API, verification flag, cooldown/expiry and SMTP service. Never print codes, credentials, passwords or proofs in logs/docs.

Safe practice exercise: in a temporary local branch, change only the static owner-guidance sentence in the modal template. Refresh Users, open a normal-user modal, check that only Close remains, use Tab/Escape and reopen it. Watch the Network panel: opening/closing assistance should produce **zero recovery POSTs**. Restore the sentence and rerun `node --check backend/static/components/js/admin_users.js`. Do not change permissions, verification flags or passwords for this exercise.

## Historical implementation notes (superseded where they describe admin code sending)


## Current fix: assisted recovery request and Gmail SMTP (October 10, 2026)

### 1. Cause / reason

Confirmed in the Users template and Chrome: the recovery form contains a hidden `name="action"` input. In Chrome this named input shadows the native `form.action` property. The old `fetch(form.action, ...)` therefore supplied an input element instead of `/admin-users/action/`. A non-JSON response triggered the reported message, "Unable to send the code. Refresh the page and check your access." The corrected request reads the literal HTML action attribute. No backend recovery permission was loosened.

The current configuration already uses Gmail SMTP at `smtp.gmail.com`, port 587, TLS. A real connection/authentication check succeeded using configured credentials; no email was sent, no recovery code or account was created, and no credentials were printed. This proves SMTP connectivity/authentication, not final inbox delivery. The user's failing live HTTP response was not captured; the form property collision was reproduced in Chrome and is covered by the browser regression.

Additional confirmed weaknesses: the old form relied on the shared session script to add its tab token; the bare action redirects to login for a token-only login. Django prioritizes a nonempty posted CSRF token over its header, so a fresh header alone cannot repair a stale form token after another login. SMTP also had no configured timeout, and the SSL branch inherited global TLS=True, which is incompatible with SSL=True. These are covered by the new transport tests.

### 2. Exact files changed / current lines / nearby anchors

| Project-relative file | Line / anchor | Change |
|---|---|---|
| `backend/static/components/js/admin_users.js` | 179 `actionUrl`; 182 headers; 190 `payload`; 200 redirected response | Read `getAttribute('action')`, preserve rendered tab identity, copy current CSRF into both header and payload, distinguish expired session/HTML denial/server error from JSON mail failure. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 220 `accountRecoveryForm`; 250 script include | Put the current tab token in the form endpoint server-side; update JS asset version to `20261010-recovery-smtp`. |
| `backend/core/accounts/password_support.py` | 36 `initiate_reset`; 47 / 52 AJAX permission guards | Eligible-target denial is still 403, now JSON for AJAX so the modal can explain eligibility/scope. Regular form behavior and outer login/RBAC/CSRF guards remain. |
| `backend/core/core/settings.py` | 236 `EMAIL_TIMEOUT` | Bound each SMTP operation to 15 seconds. Existing Gmail credentials, port and TLS configuration are retained. |
| `backend/core/modules/notifications/services/email_service.py` | 37 `_from_database`; 58 `_send_with_config`; 76 `email.send` | Choose SSL for database port 465; explicitly disable the opposite security mode; pass timeout; require one accepted message before reporting success. |
| `backend/core/accounts/recovery_codes.py` | 63 `send_code`; 94 `logger.warning` | Log only the delivery exception class, never SMTP response text, recipient, credential, code or password. Existing failed-code invalidation/503/audit remain. |
| `backend/core/accounts/test_recovery_transport.py` | 18 `RecoveryTransportTests`; 34 rendered-form test; 53 CSRF/header test; 86 TLS/SSL test | Eight isolated tests covering actual token-only login, CSRF rejection/refresh, JSON denial, SMTP flags/timeout/zero acceptance and safe failure logging. SMTP sends are mocked. |
| `scratch/account-recovery/check.cjs`, `scratch/account-recovery/csrf-check.cjs` | request URL / header assertions | Chrome checks the real property collision, correct endpoint, rendered token, error states; JSDOM checks copying a rotated cookie into the submitted body as well as header. No real POST/email. |
| `docs/marketplace-admin-support.md`, `docs/user-management.md`, `CAMPUSHUB_CONTEXT.md` | current SMTP fix notes | Cause, functions/data flow, changed files, verification, troubleshooting, limitations and practice exercise. |

### 3. Changes made

Fixed the request URL without renaming the hidden action field, because the backend needs that field to choose `assist_recovery` or `verify_email`. The form now carries the server-rendered tab token independently. Fresh CSRF is submitted in the body and header, with CSRF checks preserved. Gmail stays the configured provider; passwords/configuration were not changed. Added bounded SMTP operations and correct mutually exclusive TLS/SSL handling.

### 4. How it works / functions and data flow

The recovery submit listener receives the form, reads the real endpoint attribute, builds FormData containing target/action/purpose/confirmation and current CSRF, and sends it with tab authentication. Its output is the existing success state or an actionable error. `initiate_reset(request)` checks the actor and real target under a lock, then calls `send_code(request, source, account, purpose, assisted=True)`.

`send_code` creates the existing hashed, expiring code and calls `send_account_recovery_email(to_email, code, purpose, full_name)`. The canonical mail service chooses the existing settings credentials or active GmailConfig fallback. `_send_with_config(config, to_email, subject, body)` builds Django's SMTP connection with exactly one security mode and timeout, then requires `EmailMessage.send(...) == 1`. A delivery exception keeps the existing 503 failure and invalidates the generated code; it never pretends the email was sent.

Annotated browser example:

```javascript
// Keep the hidden name="action" field: Django uses its submitted value.
const endpoint = form.getAttribute('action'); // Actual route string.
// form.action may be the hidden INPUT rather than a URL in Chrome.
const payload = new FormData(form);
payload.set('csrfmiddlewaretoken', currentCsrf); // POST field has priority.
// Send the route string plus existing tab/CSRF headers; never log their values.
```

This reuses the existing backend flow instead of creating a new recovery API or duplicate mailer. The shared session helper remains used elsewhere; recovery no longer depends on it to correct the endpoint or add the form token.

### 5. Backend / API behavior

- Valid ordinary-user assistance: existing JSON success after SMTP accepts one message; masked email, expiry and resend timing remain.
- Ineligible/out-of-scope target: 403 JSON for AJAX. Administrator exclusion, Marketplace Program/Major and Facilities OFF remain unchanged.
- Expired/absent tab login: existing login boundary remains; the frontend explains redirects/401 instead of mislabeling them as SMTP failure.
- CSRF failure: still denied. A current posted token repairs a stale form after legitimate cookie rotation; no CSRF exemption was added.
- Actual mail error: existing 503, failed audit and unusable code. Server log includes only a safe exception type such as SMTPAuthenticationError or TimeoutError.

Google's [Gmail SMTP settings](https://support.google.com/mail/answer/7104828?hl=en) document authenticated `smtp.gmail.com`, TLS/STARTTLS port 587 and SSL port 465. The existing app-password configuration is reused; never paste an app password into a guide, log or chat.

### 6. Database / migration impact

No schema or migration. No user/role/seller/password/email-verification records were changed. No Gmail credential was edited. Read-only SMTP authentication made no email/code row. Test records are isolated in the test database.

### 7. Tests performed and how to test

Actual verification for this fix:

- **197 Django tests passed** in 170.048 seconds. Includes eight new transport/SMTP tests plus recovery, roles, scope, seller/session/user and order regressions. Isolated PostgreSQL test database; all message sends mocked. Log: `scratch/recovery-smtp-regression-final.log`.
- **10 Chrome cases passed** at desktop/tablet/375px/320px. Assertions reproduce the hidden-input property collision and verify the corrected endpoint string, tab header, CSRF payload/header equality, JSON denial, HTML 403, login redirect and existing owner recovery. No network POST/email. Log: `scratch/recovery-smtp-browser-final.log`.
- **Rotated CSRF check passed** using the real JS in JSDOM: current cookie copied into both body/header, rendered tab identity kept, original DOM left unchanged. `scratch/account-recovery/csrf-check.cjs`.
- Django `check`: no issues. `makemigrations --check --dry-run`: no changes. Node syntax check passed.
- Real configured Gmail SMTP connection and authentication succeeded with a bounded diagnostic connection; no email sent and no secrets printed.
- Mobile files unchanged; Flutter tests not rerun.

 One initial SMTP-constructor assertion used Django's automatic in-memory test backend; the test now explicitly selects the SMTP constructor while mocking the message send. That fixture correction makes it check the intended TLS/SSL flags without sending real email.

Manual steps:

1. Let Django reload or restart it; hard-refresh Users with Ctrl+F5 so `20261010-recovery-smtp` loads.
2. For an eligible Student/Guest in scope, open three dots -> Assist Account Recovery -> Send Verification Code. Expect JSON success, masked destination and resend cooldown; check the recipient inbox/spam.
3. If inspecting Network, the POST route must be `/admin-users/action/`, not a URL containing `HTMLInputElement`. Do not copy authentication headers or recovery codes into screenshots/logs.
4. Owner completes recovery using their inbox code. No admin should enter the owner's code/password. Admin target assistance remains blocked.
5. If it fails, distinguish HTTP login/403/CSRF from JSON 503 mail failure. For the latter inspect the safe server exception class; confirm local Gmail configuration, network and app-password validity. Never disable permission or CSRF checks to make email work.

### 8. Remaining limitations / safe learning exercise

SMTP connection and authentication are verified; an actual recovery email/inbox delivery was not sent by the tools. Recipient delivery and inbox/spam placement must be checked using the authorized user flow. No mobile code changed. Existing mobile/chat token revocation limitation remains.

Safe exercise: in a scratch HTML page create `<form action="/example/"><input name="action" value="verify_email"></form>`. In Chrome compare `form.action` and `form.getAttribute('action')` without making a network request. The second should be the URL string even when the first is an input. Then run the isolated `accounts.test_recovery_transport` tests from `backend/core`; verify that valid tab/CSRF succeeds, missing CSRF fails, and no real mail is sent. This teaches DOM naming and request authentication without modifying real accounts.


## Current policy: normal-user assistance and administrator self-service (October 10, 2026)

This update supersedes any earlier examples that allowed Super Admin to initiate recovery for another administrator. The existing code-only recovery service remains the single source of recovery behavior. UI UX Pro Max guidance was used for the compact owner form, accessible digit labels, paste/focus behavior and responsive layout; the existing CampusHub card and palette were reused.

### 1. Cause / reason

Confirmed: the earlier `can_reset_account` returned True for Super Admin before checking the target's actual identity. Therefore administrator targets could receive assisted codes. A custom role with no grants or an inactive role could also escape the earlier role helper. The web login's recovery link was only `href="#"`, although the existing code service already supported owner recovery through the API. These findings come from the inspected implementation, not guesses about the user's account data.

### 2. Exact files changed, current lines and nearby anchors

Paths below are relative to the project root. Search the anchor if later edits move a line.

| File | Current line / anchor | What changed |
|---|---|---|
| `backend/core/accounts/support_scope.py` | 29 `is_administrator_account`; 51 `can_assist_recovery_actor`; 58 `can_reset_account`; 77 `can_manage_seller` | Added stored-identity classifier and Facilities actor exclusion; reject admin targets before the Super Admin allowance; keep administrator targets out of seller actions. |
| `backend/core/accounts/user_management.py` | 283 `build_account_rows`; 293 `authority_ids`; 303 `is_super_admin`; 326 `is_administrator`; 370 `can_deactivate` | One batched authority query supplies truthful recovery flags. Admins get Recovery Method; Super Admin rows have no role/scope/seller/deactivation menu actions; other contextual actions remain. |
| `backend/core/accounts/password_support.py` | 29 `account_recovery_start`; 36 `initiate_reset` | Added GET-only owner entry page; repeat eligibility after locking the target before sending any code. |
| `backend/core/accounts/recovery_codes.py` | 60 `send_code`; 102 `initiated` | Guard assisted calls at the service boundary; add administrator `SELF_SERVICE_RECOVERY_INITIATED` audit event. Code verification and password completion reuse existing logic. |
| `backend/core/core/urls.py` | 43 import; 112 `account_recovery_start` | Added `/account/recovery/` UI entry, retaining existing API and legacy owner URLs. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 131 `.assist-recovery`; 133 `Manage Role`; 250 script include | Defense against showing assisted recovery on administrator targets, contextual role label, refreshed asset version; keeps three-dot trigger. |
| `backend/static/components/js/admin_users.js` | 130 `Recovery Method`; 146 `.assist-recovery` handler | Admin User Details shows Verified Email; client click handler refuses admin targets. No recovery codes or password fields were added to the admin modal. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_login.html` | 141 `login-help` | Replaced placeholder Forgot password link with Forgot Username or Password and the owner route. |
| `backend/static/components/css/admin_login.css` | 308 `.login-options` | Wrap the longer recovery link with a consistent gap on narrow screens. |
| `backend/core/modules/user_management/templates/user_management/pages/account_recovery_start.html` | 10 `ownerRecovery`; 22 `ownerVerify`; 37 `ownerPassword` | New small owner form using existing stylesheet: email/action, six code boxes, private password/confirmation and success state. |
| `backend/static/components/js/account_recovery.js` | 12 `show`; 28 `post`; 53 identify submit; 65 digit handlers; 78 verify submit; 95 password submit | New UI adapter calls the three existing API endpoints, handles loading/error/resend and keeps completion proof in memory. |
| `backend/static/components/css/account_password_reset.css` | 14 `[hidden]`; 16 `.code-boxes`; 21 `#ownerNotice` | Added select, digit grid, restrained secondary controls, notice and small-screen styles; old owner pages keep their existing design. |
| `backend/core/accounts/test_recovery_eligibility.py` | 18 `RecoveryEligibilityTests`; 56 exclusion test; 135 self-service test | Eight new regression tests covering twelve target classifications, all action aliases, scope, menus, normal users, service guard and built-in admin owner recovery. |
| `backend/core/accounts/test_recovery_code_flow.py` | 64 `test_super_admin_self_service_completes_in_app` | Replace obsolete Super-assisted-admin example with owner recovery; verify audit and existing tab-token invalidation. |
| `backend/core/accounts/test_marketplace_support.py` | 141 `test_django_owner_link_expiry_replay_validation_and_csrf` | Legacy compatibility test now obtains the admin's code through owner self-service, never an assisted request. |
| `backend/core/accounts/test_account_recovery.py` | 231 `test_export_browser_fixtures` | Export the new owner page from Django for browser verification. |
| `scratch/account-recovery/check.cjs` | browser case loop / `selfService` | Extend existing read-only browser review to owner password/username/email verification and administrator menu exclusion. All POST requests mocked. |
| `docs/marketplace-admin-support.md`, `docs/user-management.md`, `CAMPUSHUB_CONTEXT.md` | current policy sections at top | Document actual rule, functions, files, data flow, debugging, validation and safe learning exercise. |

### 3. Changes made / visibility rules

- Super Admin assists eligible ordinary users globally, including Students, Faculty, Guests and Student Sellers.
- Marketplace Admin assists eligible ordinary users only in assigned Program/Major. BTLED requires exact Major; missing Major fails closed. BFPT/BSIT follow existing program scope.
- Facilities Admin assistance is OFF, even if a legacy direct recovery grant exists.
- Every administrator target is excluded: built-in/custom/unknown non-User role, staff/superuser flags, stored mobile Admin type, or direct/group admin authority. Inactive custom roles remain administrator targets. Unknown mobile account types fail closed.
- Normal means stored role User with no admin flags/authority and an ordinary mobile type where applicable. Existing blank mobile type remains compatible with registration. Active, non-suspended account and recorded email are still required. Recovery requires verified email; ordinary-user initial verification remains separate.
- The ordinary `User` role is not confused with the account table's synthetic Django-source `Admin` display label. Eligibility uses stored identity and permissions; no user rows or assignments were rewritten.
- Admin row menus keep View User/View Activity and permitted non-sensitive Edit. Marketplace Admin has Manage Role/Program-Major; Facilities has Manage Role without academic scope; Super has no assisted, seller or scope actions. Existing server protection for the last active Super Admin remains.

### 4. How it works: functions, inputs/outputs and data flow

`is_administrator_account(source, account, has_admin_authority=None)` accepts the actual model record and returns a boolean. The server checks actual direct/group authority when needed. For Users rendering, `build_account_rows(actor)` queries authority IDs once and supplies the same classifier with that flag; it returns row dictionaries including `is_administrator`, recovery visibility and Recovery Method. This avoids one authority query per row.

`can_assist_recovery_actor(actor)` returns whether the existing recovery permission is present and the actor is not Facilities Admin. `can_reset_account(actor, source, account)` then returns False for any administrator target before considering Super Admin or Marketplace scope. Denied direct POST requests return 403 with no email/code creation. `initiate_reset(request)` repeats this check after obtaining the target row lock. `send_code(..., assisted=True)` also checks authorization so another caller cannot bypass the transport guard.

Annotated policy example (no credentials):

```python
# Reject the target first: an actor's global role cannot override this rule.
if not can_assist_recovery_actor(actor) or is_administrator_account(source, target):
    return False
if is_super_admin(actor):
    return True  # Only an eligible ordinary target reaches this line.
# Marketplace then follows the existing scoped account query.
```

Owner flow: login link -> GET `account_recovery_start` -> `account_recovery.js` -> existing send/verify/confirm APIs -> `recovery_codes` -> real User or CampusHubUser/code/audit records. Email ownership, not another admin, authorizes owner recovery. The send request accepts email and purpose. Verify accepts email, purpose and six-digit code. Username is returned only after proof. Password verification returns the existing one-use completion proof; confirm accepts that proof, new password and confirmation. The UI keeps the proof only in its closure, never in markup, local storage or logs. Password fields remain hidden until successful verification. Emails contain only codes and instructions, not reset URLs.

The owner may use Verify Email first when an existing account's recorded email is not yet verified. This proves the inbox; it does not bypass verification or mark real accounts verified automatically. Duplicate emails, disabled accounts and malformed/replayed/expired codes still fail closed as before.

### 5. Backend / API behavior and activity logging

No new API business logic or permission grants. Existing endpoints:

- `mobile_password_reset`: `/api/mobile/password-reset/`
- `mobile_password_reset_verify`: `/api/mobile/password-reset/verify/`
- `mobile_password_reset_confirm`: `/api/mobile/password-reset/confirm/`

Existing action aliases `assist_recovery`, `reset_password`, `verify_email` all enter the guarded admin transport. UI hiding is an aid; server authorization is the boundary. Self-service APIs remain public proof-based endpoints with existing attempt/rate limits.

Assisted ordinary users still log `ACCOUNT_RECOVERY_INITIATED` and `ACCOUNT_RECOVERY_CODE_SENT`, with the initiating admin ID. Administrator owner recovery logs `SELF_SERVICE_RECOVERY_INITIATED`, and successful password completion logs `PASSWORD_RESET_COMPLETED`. Existing compatibility events and distinct email-verification events remain. Codes, hashes, completion proofs and passwords are never added to audit metadata. Old ordinary-account/session behavior is unchanged; owner password completion retains Django session/tab-token invalidation.

### 6. Database / migration impact

No new fields, tables or migration. No existing user, role assignment, permission, password, verification state or seller record was changed in the application database. Tests use isolated records. Reuses existing User/CampusHubUser, Role, permission relations, PasswordResetCode and AccountActivity.

### 7. Tests performed / manual verification

Actual checks for this update:

- 189 Django tests passed in 150.583 seconds: `accounts.test_recovery_eligibility`, `accounts.test_recovery_code_flow`, `accounts.test_account_recovery`, `accounts.test_marketplace_support`, `accounts.test_user_management`, `accounts.test_roles_permissions`, `accounts.tests`, `modules.marketplace.test_orders_admin`. Isolated PostgreSQL test database; SMTP mocked. Log: `scratch/admin-recovery-regression-final.log`.
- Django `check`: no issues. `makemigrations --check --dry-run`: no changes detected.
- Node syntax checks for both changed JS files passed. Targeted `git diff --check` passed (only standard Windows line-ending notices).
- 10 Chrome browser cases passed at 1440/768/375/320px: ordinary-user menu/assistance, admin menu exclusion, keyboard navigation, drawers, loading/error/cooldown, owner password/username/initial verification, digit paste/backspace, matching passwords, no proof in markup and no page overflow. All requests mocked. Log: `scratch/admin-recovery-browser-final.log`. The administrator details drawer displays Recovery Method: Verified Email. A 320px code-entry screenshot was visually inspected; the Back to Login link received matching spacing below the controls.
- Flutter files were not changed and Flutter tests were not rerun for this policy update. The prior code-flow update had its own mobile checks; those results are documented separately below.

 The first run had one test-fixture error: two new mobile admin examples used blank unique email values. The fix gives them distinct test emails; it does not change model constraints or application behavior.

Manual checks with test accounts:

1. Super Admin -> Users -> ordinary Student/Guest/Seller: three dots includes Assist Account Recovery. Sending a code stays in Users and reveals no owner password input.
2. Open Marketplace, Facilities, Super or custom admin row: no assistance. Marketplace has scope management; Facilities/Super do not. Details shows actual Email Verification Status and Verified Email recovery method.
3. Send a direct assisted POST for an admin target, including legacy reset/verification aliases: expect 403, no sent email/code. Facilities actor -> ordinary target is also denied.
4. Marketplace BFPT -> BFPT ordinary user succeeds; foreign program fails. BTLED-HE -> HE succeeds; IA/ICT/missing Major fail.
5. Log out -> Forgot Username or Password -> verified recorded email -> code from inbox -> owner sets matching valid password. Try username recovery separately; no username appears before code proof. New passwords appear only in the owner form.
6. Test unverified owner email using Verify Email, then return to password recovery. Try incorrect/expired code, resend cooldown and duplicate email: honest error states remain.
7. Check monitoring for appropriate initiation/completion events, never secrets. Confirm unchanged seller controls, scope and final-Super protection.

### 8. Remaining limitations, debugging and learning practice

Live SMTP delivery and a physical phone were not tested by this update; all test emails are mocked. New administrator accounts/legacy unverified emails need genuine inbox proof before password recovery. No account's verification flag was fabricated. Existing stateless mobile/chat JWT global revocation is still outside this change; Django password/session and tab-token behavior remains covered.

Debugging: if assistance is unexpectedly hidden, inspect the stored role/type, staff flags and direct/group authority plus actor scope, active/suspended state and email. Do not fix it by relabeling the UI or granting broad permissions. A 403 for an administrator target is expected. A generic send response for unknown/unverified/ambiguous email does not mean mail was sent; choose separate initial verification where appropriate. Delivery failure follows the existing 503 handling; no fake success. For stale menus, hard-refresh after the `20261010-normal-recovery` asset update. The code page requires JavaScript; noscript gives a clear message.

Safe practice exercise: add one additional custom-role target only inside `test_recovery_eligibility.py`, with a distinct test email. Assert classifier True, recovery flags False and POST 403. Run `venv/Scripts/python.exe manage.py test accounts.test_recovery_eligibility --noinput` from `backend/core`. Verify no code/email is created. This teaches server-first authorization without editing real users or loosening permissions. For UI practice, change one supporting sentence in a scratch copy, then review at 320px and confirm all six inputs fit and keyboard focus remains usable.


## Current implementation: code-only recovery in the app (October 10, 2026)

This section supersedes the earlier emailed owner-link flow. The Users table still has one three-dot trigger. Admins send a verification code and stay inside Users; the owner completes recovery in CampusHub. No temporary or admin-chosen permanent passwords were added. UI UX Pro Max guidance informed paste support, focus movement, accessible labels and compact loading/success feedback; existing navy/gold/white styling is reused.

### 1. Cause / reason

Confirmed from the old sender: `send_account_recovery_email` included an absolute signed recovery URL alongside the code. A localhost URL opened on a phone addresses that phone, so it could not reach the PC server. The old mobile verify endpoint also left the code unused until password confirmation, allowing repeated verification. Mobile had password-only recovery and no persisted email-verification flag in its saved user object. These confirmed causes are corrected; this change does not diagnose unrelated Wi-Fi/server connection problems.

### 2. Exact changed files, current lines and nearby code anchors

Paths are relative to `C:/Users/leste/Desktop/CAMPUSHUB`. Line numbers are current for this update; search the named anchor after future edits.

| File | Line / anchor | Change and purpose |
|---|---|---|
| `backend/core/accounts/recovery_codes.py` | 31 `mask_email`; 36 `find_account`; 60 `send_code`; 110 `verify_code`; 148 `confirm_password` | New shared service reusing the existing account/code/audit tables; issuance, email proof, username recovery and owner password completion. |
| `backend/core/accounts/password_support.py` | 26 `initiate_reset`; 60 `account_recovery` | Admin transport calls the shared service and returns JSON to the modal. Removed new signed-link generation and the origin builder. Older already-issued owner routes remain compatible; their proof is invalidated by resend. |
| `backend/core/accounts/reset_codes.py` | 6 `verify_reset_code` | Existing persistent attempt counter now accepts exactly six ASCII digits; callers consume successful codes. |
| `backend/core/accounts/support_scope.py` | 62 `SUPPORT_EVENTS` | Existing scoped monitoring includes code-sent events; existing account/seller/permission checks are retained. |
| `backend/core/api/views.py` | 126 `serialize_campushub_user`; 1740 `_recovery_api`; 1813 / 1820 / 1827 password-reset wrappers | Existing JSON URLs dispatch to the shared service. Adds real `email_verified` to mobile user data; authenticated initial verification uses the saved email, not the submitted replacement. |
| `backend/core/modules/notifications/services/email_service.py` | 85 `send_password_reset_email`; 90 `send_account_recovery_email` | One code-only email template, separate initial-verification subject; removed the unused link-email sender. Existing configured Gmail transport is reused. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 220 `accountRecoveryForm`; 231 `recoverySent` | Keeps the current modal and adds masked success state, Resend/Done controls and no owner-code/password inputs. |
| `backend/static/components/js/admin_users.js` | 144 `.assist-recovery`; 168 `recoveryTimer`; 169 form submit | CSRF-bearing asynchronous submit, errors/loading, successful in-place modal update and 60-second resend countdown. No navigation to an owner page. |
| `campushub/lib/module_app/services/auth_service.dart` | 7 `AuthUser`; 71 `AuthResult`; 176 `sendRecoveryCode`; 185 `verifyRecoveryCode`; 197 `confirmPasswordReset` | Parses actual verification state, masked email, username and short-lived completion proof; password completion sends proof rather than reused code. Recovery requests have a 20-second timeout. |
| `campushub/lib/module_app/session/session_service.dart` | 14 `_encodeUser` | Saves real `email_verified` with the existing profile; never saves codes or completion proofs. |
| `campushub/lib/module_app/widgets/six_digit_code_input.dart` | 5 `SixDigitCodeInput`; 33 `_changed`; 50 `build` | Reusable equal-width numeric boxes with paste distribution, focus advance, backspace navigation, code autofill and accessible digit labels. |
| `campushub/lib/module_app/screens/components/account_recovery_dialog.dart` | 9 `AccountRecoveryDialog`; 71 `_send`; 104 `_verify`; 137 `_save`; 181 `build` | One shared owner dialog for username, password and separate email verification. Includes existing-code entry, resend, matching/password-policy validation and completion messages. |
| `campushub/lib/module_app/screens/login_screen.dart` | 69 email-verification branch; 86 `_showAccountRecoveryDialog`; 559 link text | Replaces the old private password-only dialog with the shared flow and `Forgot Username or Password?`. Verified users retain existing login navigation. |
| `campushub/lib/module_app/screens/profile_setup_screen.dart` | 163 `if (!user.emailVerified)` | After saving actual additional information, offers email verification using the saved sign-up email and authenticated session. |
| `backend/core/accounts/test_recovery_code_flow.py` | 17 `RecoveryCodeFlowTests` | New isolated tests for code-only mail, permissions/CSRF, cross-account/purpose rejection, expiry, immediate single use, grant consumption and first-login verification. |
| `backend/core/accounts/test_account_recovery.py` | 35 `delivery`; 211 existing mobile contract test | Older signed URLs are now constructed only inside compatibility tests; mobile assertions use the returned completion proof. |
| `backend/core/accounts/test_marketplace_support.py` | 27 `setUp`; 106 hashed delivery test; 140 legacy route test | Keeps scope, monitoring and seller regressions; updates completion requests and clears test rate counters. |
| `campushub/pubspec.yaml` | 71 `fonts` / `family: Montserrat` | Registers the existing local font asset so the recovery dialog uses real Montserrat offline. |
| `campushub/test/recovery_code_input_test.dart` | 7 `main` | Tests numeric/paste/backspace input, semantics, 320px layout, existing admin-sent code and saved-email verification. |
| `docs/user-management.md` | 3 current recovery note | Summarizes the changed Users behavior and links this guide. |
| `CAMPUSHUB_CONTEXT.md` | 3 current recovery note | Preserves the new project behavior for future changes. |
| `scratch/account-recovery/check.cjs` | 26 mocked fetch; success/error assertions | Browser-only QA using test-rendered fixtures; all sends are intercepted, no real email/account mutation. |

### 3. Changes made / user behavior

Admin: Users -> three dots -> Assist Account Recovery. The modal uses actual name, username, applicable Program/Major, masked recorded email and truthful Verified Email / Email Not Verified. An unverified email must be verified first; the modal sends that separate-purpose code. For a verified account, retain the existing username/password choice and click **Send Verification Code**. Success shows **Verification Code Sent**, masked destination, 15-minute expiry and Resend Code / Done. No owner-code field, new-password field, email link or admin redirect is added.

Owner: login -> **Forgot Username or Password?** -> select Reset Password / Recover Username. Enter the recorded email. If an admin already sent the code, select the same recovery action and choose **I already have a code**. This avoids accidentally superseding the admin's code. Otherwise send a new code. Enter or paste the six digits, Verify Code, then see only the username or privately set matching new/confirmation passwords. The completion screen returns to login. **Verify Email** is a separate action for existing unverified records; it does not reveal a username or authorize password reset.

First login: Sign Up's email is reused after Additional Information. Authenticated verification has no email entry field. Cancelling verification does not falsely mark the email verified or block the existing profile/login flow; an unverified account is prompted again on a later login, and recovery still requires verification.

### 4. How it works: functions, inputs/outputs and data flow

`find_account(email)` looks in both existing account stores and returns `(source, account)` only for an unambiguous email. It never guesses which duplicated account is intended. Admin target selection still uses the existing exact `account_ref` and `can_reset_account` permission/scope check.

`send_code(request, source, account, purpose)` takes the locked real account and one existing purpose (`password`, `username`, `email_verification`). It validates eligibility, verified-email rules, one-minute cooldown and five requests per email per hour. Secure random digits are hashed with Django, saved to `PasswordResetCode`, emailed privately and audited. Older codes and completion proofs are invalidated. The response contains only masked destination, success message, expiry and cooldown; no code or recovery URL. SMTP failure invalidates the undelivered code and gives a generic error.

`verify_code(...)` locks the latest matching code row after the account lock. It requires the same account/email/purpose, active status, six ASCII digits, time before expiry and fewer than five wrong guesses. Wrong and malformed guesses increment the persistent existing counter. A valid code immediately becomes `used=True`.

For username recovery, the output contains the actual username only after that proof and records `USERNAME_RECOVERED`. For initial verification, the output marks `email_verified=True` and records `EMAIL_VERIFIED`, without password authority. For password recovery, the existing `code_hash` is replaced with a hash of a fresh completion nonce; a signed completion proof is returned only in the API response to the owner. The code itself no longer works.

`confirm_password(...)` validates the signed proof, original code expiry, locked account, unchanged email/password version and stored nonce hash. It applies existing CampusHub and Django password checks, hashes the owner's password, updates the correct existing account and invalidates every code/proof for that email. Invalid passwords leave the proof usable until its original expiry, so the owner can correct a typo. A successful completion cannot be replayed. Django password changes invalidate Django session authentication and delete existing admin tab tokens.

Why reuse `code_hash`? Before verification it proves the emailed code; afterward it proves the one-time completion nonce. The `used` flag still means the emailed code has been consumed. This keeps single-use enforcement in the existing database without a duplicate recovery table or migration. Neither nonce nor code is stored as plaintext.

Annotated example (transport shape only; no live credentials):

```python
# Owner enters the code from their inbox in CampusHub.
verify_payload = {"email": recorded_email, "purpose": "password", "code": entered_code}
# The server consumes the code and returns a short-lived recovery_grant.
# Only this owner's app keeps that proof, in memory; never log or persist it.
confirm_payload = {
    "email": recorded_email,
    "recovery_grant": verified_response["recovery_grant"],
    "new_password": owner_password,
    "confirm_password": owner_confirmation,
}
# A second successful confirmation fails: the database nonce hash is cleared.
```

Flutter data flow: `AuthService` posts JSON -> `_recovery_api` resolves/locks the real account -> shared service -> existing SMTP/code/audit stores -> JSON -> `AuthResult` -> `AccountRecoveryDialog`. The six-box widget only formats input; the backend always decides validity. The first-login bearer token fixes verification to the account's saved email even if a client submits another address. Actual verified user data is then saved by `SessionService`.

### 5. Backend / API behavior, authorization and audit

Existing routes retained:

- Admin POST `/admin-users/action/` via `{% url 'admin_users_action' %}`: login, existing Assist Account Recovery grant, real Super Admin/system-wide eligibility or Marketplace ordinary-account Program/Major scope, CSRF and confirmation. Unauthorized forged requests remain 403; Facilities Admin receives no new recovery grant.
- POST `/api/mobile/password-reset/`: `{email, purpose}`. For authenticated first-login verification, send the existing bearer header and `purpose=email_verification`; the submitted email is ignored.
- POST `/api/mobile/password-reset/verify/`: `{email, purpose, code}`. Returns username, email-verification completion, or password `recovery_grant` as appropriate.
- POST `/api/mobile/password-reset/confirm/`: `{email, recovery_grant, new_password, confirm_password}`. A raw code alone is no longer accepted for password completion.

The actual admin route spelling is defined by `admin_users_action` in `core/urls.py`; use the template's named route rather than inventing a URL. No new route was required. Daily/weekly/chart/seller behavior is unrelated and retained.

Public send responses deliberately avoid confirming whether an email exists, is duplicated or is verified. Such responses say **If that email is eligible...** and do not send a fake code. Real eligible delivery failures return 503; cooldown/limit returns 429; invalid or expired proof returns 400. Five persistent wrong-code attempts lock that code. A hashed-IP cache guard additionally allows at most 60 API requests in 15 minutes; use shared cache for a consistent guard across production workers. Responses are not cacheable.

Audit uses existing `AccountActivity`: `ACCOUNT_RECOVERY_INITIATED`, `ACCOUNT_RECOVERY_CODE_SENT`, `ACCOUNT_RECOVERY_CODE_VERIFIED`, `USERNAME_RECOVERED`, `PASSWORD_RESET_COMPLETED`, and separate email-verification events. Existing password/username initiation events remain for existing support reports. Actual target/source, timestamp, purpose and initiating admin ID are recorded; codes, nonce/proof, passwords and password hashes are not written to logs. Completion is an owner action, not an admin password choice.

### 6. Database / migration impact

**No new migration or field in this update.** Reuses previously applied `email_verified`, `PasswordResetCode.account_ref/purpose/attempts`, `code_hash`, `used`, timestamps and existing audit tables. No users, products, stock, historical orders or permission grants were created/deleted by implementation. Only deliberate runtime requests change real recovery rows, verification state or the owner's password. Tests use an isolated test database and mocked mail. `makemigrations --check --dry-run` reported **No changes detected**.

### 7. Verification results and manual test steps

Actual results:

- **181 Django tests passed** in 145.028 seconds: new code-only flow, existing owner-route compatibility, Marketplace support, Users, Roles/Permissions, account tests and admin Orders. Final log: `scratch/code-only-regression.log`. Earlier focused run: 79 passed.
- **18 Flutter tests passed**: new code input/dialog tests plus existing login layout, profile academic validation and password-policy regressions. Log: `scratch/code-only-flutter.log`.
- **Seven Chrome cases passed**: Marketplace widths 1440/768/375/320, Super Admin desktop, unverified mobile and legacy owner mobile. Checked unclipped three-dot menus, keyboard navigation, masked modal, successful send/loading/countdown/Done, resend error and no admin code/password fields. Every send was intercepted; fixture source was the isolated Django test render. Log: `scratch/code-only-browser.log`.
- Targeted **Flutter analysis: no issues** for six changed application files and the new widget test. Formatting, JavaScript syntax, changed-file diff check and Django system check passed; no migration changes detected.

No live Gmail email or physical Android phone was tested. Existing login layouts were checked in both app brightness modes; the recovery dialog deliberately uses the requested light CampusHub styling. Large-text/small-phone code input was tested, but real TalkBack and Android system code autofill remain manual checks.

Manual verification:

1. Restart Django and rebuild/restart the Flutter app together. Hard-refresh the Users page. The old mobile build posts a raw code during confirmation and must be updated.
2. Use an existing test user with a unique recorded email; do not blanket-set verification flags. For an unverified user, send/enter the separate verification code first. Wait out the shared resend cooldown.
3. Super Admin -> Users -> three dots -> Assist Account Recovery -> choose action -> Send Verification Code. Confirm no navigation, masked success state, expiry, disabled countdown and Done.
4. Inspect the received email: subject **CampusHub Account Recovery Code**, six digits, 15 minutes, app instructions, no clickable URL. Initial verification instead uses **CampusHub Email Verification Code**.
5. Owner app -> Forgot Username or Password? -> same action/email -> I already have a code -> paste code. Username-only recovery displays username without changing a password. Password recovery reveals new/confirm fields only after verification.
6. Verify the same code again: rejected immediately. Try a wrong code, five wrong/malformed attempts, and a code older than 15 minutes: rejected; expiry message and Resend remain visible.
7. Resend after the countdown: old code and prior unfinished completion proof no longer work. Correct mismatched/weak passwords and retry before expiry; after success the completion proof cannot be reused.
8. BFPT Marketplace Admin: BFPT ordinary users allowed, BSIT/admin users denied. BTLED-HE: HE allowed, IA/ICT denied; missing Major denied. Test direct POSTs as well as visible menu items. Verify original seller/login/role behavior is unchanged.
9. Sign up/login and finish Additional Information: Verify Email shows the saved masked address without another email input. Successful code proof updates true verification state; cancellation leaves it unverified.

### 8. Debugging / limitations / learning exercise

Confirmed problems found during implementation/testing:

- Removing the origin builder also removed a `settings` import still used by older owner-route compatibility. Legacy tests caught this; the import is restored. New code delivery does not need that origin.
- The existing Montserrat font file was present but not registered in Flutter. Added its font-family declaration; no font download or runtime font request is needed.
- At 320px the default Flutter dropdown's intrinsic width overflowed. Setting `isExpanded: true` keeps it inside the existing dialog; the small-phone test now passes.
- A code-send endpoint cannot display success if SMTP returns false. Failed sends mark the code unusable and return a generic error; the modal shows an error rather than claiming delivery.

Troubleshooting: receiving a code does not mean a PC Django server is reachable from the phone. Keep the existing phone-reachable API configuration and network setup. No emailed link or `CAMPUSHUB_PUBLIC_BASE_URL` is required for this new flow. Duplicate recorded emails across either account store are intentionally blocked; correct the real records instead of weakening the identity check. Select the same recovery purpose as the admin-sent code. If reset completion returns expired/already used, request a new code; never try to reuse the consumed code or expose a completion proof in a log.

Limits: live SMTP, Android keyboard/autofill and TalkBack still need device checks. Existing stateless mobile/chat JWTs are not globally revoked by a password reset; that requires a separate coordinated authentication change. Django sessions/admin tab tokens are invalidated. Initial verification remains optional to finish the existing profile navigation but is required before recovery. Already-issued legacy web reset routes remain for compatibility; new initiation never generates/sends them. Recovery remains code-first, with an internal short-lived API completion proof for safe password submission. There is no new production sample data.

Safe practice exercise: in a scratch branch, change only the recovery dialog's supporting text, then run `flutter test test/recovery_code_input_test.dart test/login_layout_test.dart` and `flutter analyze` for the changed file. Verify all six boxes and masked email still fit at 320px. Restore the text afterward. For backend learning, trace the mocked `test_code_consumed_on_verification_then_grant_consumed_on_completion`: identify the row state before verify, after verify and after completion. Do not print the code, password or grant while debugging; inspect booleans, purpose, expiry and response status instead.

## Previous implementation reference (October 9, 2026)

Updated October 9, 2026. This guide supersedes the older notes saying that every User Monitoring view is Super Admin-only. Global monitoring remains exclusive to Super Admin; Marketplace Admin now has a separate scoped result set inside the same page.

## 1. Cause / reason

Confirmed in the code: Marketplace Admin had no View Users grant, User Monitoring rejected every non-Super Admin, and its activity queries were global. Simply granting access would have exposed unrelated activity. The previous Reset Password action accepted a password chosen by the administrator. Some mobile seller applications also have no Django user foreign key, so the previous seller scope query silently omitted them.

The implementation reuses Django permissions, Department/ProgramMajor, both existing account models, SellerRequest and AccountActivity. It does not create another Users module or another permission store.

## 2. Exact files changed and code anchors

Paths are relative to the CampusHub project root. Lines refer to this update; search the anchor after later edits.

| File | Current line / anchor | Change and reason |
|---|---|---|
| `backend/core/accounts/models.py` | 105 `can_reset_user_password` | Add one permission definition, not another password or account field. |
| `backend/core/accounts/role_permissions.py` | 68 Reset User Password; 143 Marketplace grants; 197 `role_scope_permissions` | Add the support permission to the existing editor/default role. Marketplace gets View Users, Reset User Password and View User Monitoring; administrative account/role, facilities and backup rights remain outside its boundary. Facilities does not inherit these support rights. |
| `backend/core/accounts/migrations/0027_marketplace_user_support.py` | 6 `grant_support_permissions`; 42 `RunPython` | Materialize the permission and add support grants to existing roles/accounts. Existing account managers receive the reset permission to retain ordinary-account support. No existing grants are deleted. |
| `backend/core/accounts/support_scope.py` | 16 `support_accounts`; 29 `can_reset_account`; 48 `support_activity` | Central backend boundary for ordinary accounts, reset targets and permitted activity. Exclude administrators, missing/invalid scope and other Programs/Majors before rows are serialized. |
| `backend/core/accounts/academic.py` | 87 `scope_seller_requests` | Include existing mobile applications through their real username/school ID when no Django user link exists. Exclude conflicting identities rather than guessing which account owns the request. |
| `backend/core/accounts/user_management.py` | 109 `_seller_requests_by_identity`; 281 `build_account_rows`; 315 `get_user_management_context` | Scope accounts, seller summaries, KPIs, filters and the recent-activity preview. Compute Reset Password availability independently of Manage Admin Accounts. Keep filters, table and drawer. |
| `backend/core/accounts/views.py` | 148 scoped pending sellers; 250 `admin_sellers_page`; 602 `admin_users_action`; 1048 owner order event; 1177 `admin_user_monitoring_page` | Route resets to secure delivery. Other user mutations retain Manage Admin Accounts checks. Scope latest/recent/history/chart queries and exclude security details. Marketplace charts show actual marketplace activity, while Super Admin keeps login charts. |
| `backend/core/accounts/role_management.py` | 105 `role_post`; 134 `admin_roles_page` | Enforce the requested Super Admin-only role management policy on reads and every mutation, even if a custom account has an old grant. Preserve those stored grants. |
| `backend/core/accounts/password_support.py` | 26 `initiate_reset`; 84 `account_password_reset_confirm` | Verify permission, scope, account eligibility and confirmation; deliver instructions. The owner chooses the password. Lock records for reset initiation and web completion. |
| `backend/core/accounts/reset_codes.py` | 7 `verify_reset_code` | Reuse hashed mobile codes, bound incorrect guesses and reject expired/used codes. Five wrong six-digit guesses invalidate that code. |
| `backend/core/accounts/activity_logging.py` | 55 `log_marketplace_event`; 64 `log_seller_event` | Record real new product, inventory, seller and order changes against their owner/customer, with the actor in metadata. Do not manufacture past history or identities. |
| `backend/core/api/views.py` | 1153 inventory event; 1173 archive; 1190 restore; 1296 seller query; 1346 product approval; 1381 seller approval; 1741 `_get_active_reset`; 1828 verify; 1852 confirm | Use the shared seller query for list/approve/reject, append actual operation events and consume mobile reset codes inside a transaction. Preserve stock, order and approval workflows. |
| `backend/core/modules/notifications/services/email_service.py` | 137 `send_password_reset_link` | Reuse configured CampusHub SMTP delivery for Django account-owner links. Mobile accounts retain the existing six-digit email/app flow. |
| `backend/core/core/urls.py` | 112 `account_password_reset_confirm` | Add the owner-facing web reset form route. Existing Users, Monitoring, Products, Orders and Sellers routes remain. |
| `backend/core/core/settings.py` | 240 `PASSWORD_RESET_TIMEOUT` | Web reset links expire after one hour; existing mobile code lifetime remains 15 minutes. |
| `backend/templates/partials/admin_sidebar.html` | 89 Roles & Permissions; 97 User Monitoring; 174 Generate Reports | Use real permissions for Users/Monitoring visibility. Only Super Admin sees Roles & Permissions. Marketplace navigation keeps Products, Inventory, Orders, Sellers, Analytics, Reports and personal Settings. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 145 `user.can_reset`; 177 editor permission check; 223 `resetPasswordModal` | Reset action outside the admin-management-only actions. Confirmation shows name/username; no new-password inputs. Omit Add Admin form for unauthorized readers. |
| `backend/static/components/js/admin_users.js` | 22 `formatDate`; 29 `if (form)`; 120 `.reset-password` | Keep support actions working when the admin editor is absent. Shared drawer helpers remain available. Fill confirmation with textContent and preserve CSRF form submission. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 18 shared header class; 43 scoped KPI; 54 activity chart; 284 drawer tabs | Reuse current layout, show marketplace activity labels and hide security/session tabs and IP/device details for Marketplace Admin. |
| `backend/static/components/css/admin_monitoring.css` | 1079 `.drawer-tabs.scoped` | Use two equal tabs for Overview/Activity; reuse existing mobile header guards to fix header overflow. |
| `backend/core/modules/user_management/templates/user_management/pages/password_reset_confirm.html` | 1 document; 15 owner form | Compact CampusHub form with validation, expired-link and completed states. No external script or font requests on a token-bearing page. |
| `backend/static/components/css/account_password_reset.css` | 1 brand tokens; 14 focus ring | Navy/white compact layout, gold keyboard focus, normal-sized labels and 44px inputs/button. |
| `backend/core/accounts/test_marketplace_support.py` | 18 `MarketplaceSupportTests` | Isolated scope, permission, reset, delivery failure, expiry/replay/guess limit, audit and browser-fixture tests. |
| `backend/core/accounts/test_user_management.py` | 182 audit test | Replace the old administrator-chosen reset expectation with mocked email delivery and owner-controlled reset initiation. |
| `backend/core/accounts/tests.py` | 148 Marketplace sidebar expectations | Update the old rule that hid Users and Monitoring; retain assertions denying facilities, roles and backups. |
| `docs/user-management.md`, `docs/roles-permissions.md`, `CAMPUSHUB_CONTEXT.md` | latest Marketplace support note | Link this guide and explain the policy change without discarding earlier history. |

## 3. Changes made / final access rules

Marketplace Admin gets the existing nine marketplace permissions and three account-support permissions. It retains marketplace Analytics/Reports, Messages, Notifications and personal Settings. Facilities operations, administrator creation/editing, Roles & Permissions, backup/restore and unrestricted monitoring remain denied by the backend.

BFPT scope selects BFPT ordinary accounts. BTLED-HE scope selects only matching Program **and** Major. Missing BTLED Major or missing Program fails closed. Super Admin remains unrestricted. Facilities Admin remains global within facilities, with no new marketplace support scope. Existing Program/Major creation validation remains unchanged.

The scope excludes standard and custom administrator roles, staff/superusers and ordinary Django accounts with administrator permissions. Mobile accounts must have the ordinary User role and a non-admin account type. There is no optional limited-edit feature in this update.

Marketplace activity includes the recognized Marketplace/Products/Inventory/Orders/Sellers modules and selected User Management seller/reset-support events. Authentication, facilities, backup/restore and role/permission events are excluded. The restriction applies to chart data, latest activity, previews, recent activity, pagination, deep links and all-time history. IP/device information and session histories are not returned to Marketplace Admin. Existing online indicators only count eligible accounts.

## 4. How it works: functions, inputs, outputs and data flow

`support_accounts(queryset, actor, mobile=False)` receives a lazy Django queryset and the authenticated administrator. It returns another queryset with Program/Major and ordinary-account restrictions. The database executes it before `build_account_rows` produces normalized dictionaries. Users search/sort/pagination then operate on permitted rows; KPI totals describe that same permitted set.

```python
# Start with the actual table; do not send every user to JavaScript.
eligible = support_accounts(CampusHubUser.objects.all(), request.user, mobile=True)
# BTLED-HE actor: the database result contains only ordinary BTLED-HE accounts.
```

`support_activity(queryset, actor)` receives an activity query and actor, derives eligible source-qualified references such as `mobile:12`, and returns only permitted marketplace/support events. The Monitoring view reuses that source for all subsequent activity queries. Explicit Program/Major metadata on newly recorded product/order events also follows the product scope, even when its owner has a different affiliation. `admin:12` and `mobile:12` are different identities.

`initiate_reset(request)` consumes POST `account_ref`, `action=reset_password` and `confirm_reset=1`. It verifies actual permission and target scope, locks the target, checks active access/email and the one-minute retry limit, and returns a redirect with truthful success/failure feedback. Submitted `password` fields are ignored in this action.

Mobile flow: secure random code -> existing PasswordResetCode stores a hash/expiry -> existing email delivery -> user enters code in the app -> existing confirm API validates and consumes it -> password_hash changes. Failed delivery invalidates the undelivered code. Ambiguous email identities are rejected.

Django account flow: existing Django token generator -> emailed account-owner link -> CSRF-protected form -> existing validators -> set_password -> invalidate admin tab tokens -> audit completion. The token is invalid after password change or expiry. The response disables caching and sends a no-referrer policy. Neither link/code nor any password/hash is included in activity metadata or the admin response.

`log_marketplace_event` writes a new actual AccountActivity against the known seller/customer. Inputs include the target, real operation type and identifying metadata; output is the saved audit record, or None when no real account can be identified. Seller events resolve at most one existing mobile identity. Historic orders and logs are preserved; no retrospective events are invented.

## 5. Backend / API behavior

- Users: `/admin-users/`; support reset: POST `/admin-users/action/`.
- Monitoring: `/admin-user-monitoring/`; an out-of-scope `account_ref` returns 404.
- Roles: `/admin-roles/` and its save/permission/status/delete handlers remain Super Admin-only and permission checked.
- Forged Marketplace user mutations and unauthorized reset targets return 403. Products, Orders, Sellers and reports retain their existing permission/scoping gates.
- Mobile recovery retains `/api/mobile/password-reset/`, `/api/mobile/password-reset/verify/` and `/api/mobile/password-reset/confirm/`.
- Web owner reset: `/account/password-reset/<uidb64>/<token>/`. Invalid/expired links show an unavailable state and cannot change a password.

## 6. Database / migration impact

Applied **accounts.0027_marketplace_user_support** to the configured `campushub` database. It added **4 role grants and 4 account grants**. The before/after integrity snapshot confirmed unchanged role identity/details, account assignments/flags, academic scope, stock/configuration/thresholds, record counts and all prior grants. No sample users, orders, products, seller records or activity logs were inserted into the live database.

Role updated_at advances where grants actually change. No duplicate stock, Program, Major, password or permission-storage fields were created. When real users request resets, the existing reset-code/audit tables are used; actual owner completion changes only the existing credential field and applicable session tokens.

## 7. Tests performed and manual verification

The broad isolated Django regression suite passed **157 tests** across account support, Roles & Permissions, Users, account/authentication routes, Program inventory and order administration. Email delivery was mocked; these checks did not send real email or change live accounts. After the final scoped seller-summary and expiry-test refinements, another **15 focused tests passed**, including all 14 support tests and the Users query-growth check. The final **37 support, domain-permission and order tests passed** after refining the Generate Reports label and explicit product activity scope. Django check, migration consistency, JavaScript syntax and changed-file whitespace checks passed.

Chrome checks passed at Users widths **1440, 768, 375 and 320px**, and Monitoring widths **1440 and 375px**. They exercised the scoped drawer, absent Add Admin editor, owner-reset confirmation values and contained layouts. Browser submissions were intercepted. Actual mutation checks were performed separately in Django tests. Test-rendered HTML/screenshots and logs are under `scratch/marketplace-support/`.

Manual steps, using development accounts you control:

1. Sign in as BFPT Marketplace Admin; check Users, Monitoring and Sellers contain BFPT records only. Repeat with BTLED-HE and confirm IA/ICT are absent.
2. Open User Details and Reset Password. Check name/username, Cancel, and that there is no administrator-entered password field.
3. Send instructions to an eligible account with a configured mailbox. Verify the owner can complete the reset; the old password and used/expired code/link fail. Retry immediately and check the one-minute limit.
4. Test a forged reset reference to another Major or an administrator; expect 403. Test a foreign Monitoring deep link; expect 404. Check no data changed.
5. Approve a permitted seller/product or change a permitted order on test data. Check its actual marketplace event appears. Global security/facility/backup events must remain absent.
6. Check Super Admin still has complete Users/Monitoring/role access and Facilities Admin still manages facilities without Program/Major.
7. At phone width, open and close drawers/confirmation, tab through controls and scroll the existing wide tables internally.

## 8. Debugging and remaining limitations

| Symptom | What to inspect |
|---|---|
| New support links absent | Apply migration 0027, refresh/sign in again and inspect actual role/account permission assignments. Existing role reductions are still meaningful. |
| Empty Marketplace Users | Check the administrator's saved Program and linked BTLED Major, ordinary target role and staff/permission flags. Do not broaden scope to hide incomplete data. |
| Seller application omitted | Check its real Django user link or unique matching mobile username/school ID. Unknown or conflicting identities fail closed. |
| No marketplace activity | Only recorded permitted events appear. Old authentication events do not become marketplace records. New approval/archive/stock/seller/order hooks record actual subsequent changes; not every historic/mobile action has an AccountActivity hook. |
| Reset delivery error | Check configured CampusHub SMTP and the target's active state/email. Do not paste mail credentials, tokens, codes or password hashes into logs/docs. Mocked tests do not prove live mailbox delivery. |
| Old UI or missing reset action | Hard refresh; inspect the versioned admin_users.js and console. Shared drawer helpers must run even when userForm is absent. |
| Code no longer accepted | Check used/expiry and guess limit. Malformed input is rejected; five incorrect six-digit guesses invalidate a code. |

Live SMTP delivery and physical-phone reset completion still require manual verification. Email-less/disabled accounts cannot use this flow. Default Django cache is process-local; use a shared production cache for a uniform code-guess counter across workers. Persisted code invalidation and expiry still apply. Existing trusted account-manager edit-password behavior outside this support action remains unchanged. Existing User normalization represents Django back-office accounts as Admin; this update does not invent a missing account-type field for legacy records.

The recent-activity preview remains bounded and the existing account table remains shared. Larger datasets may warrant database-level pagination across the two account sources; this update preserves the established combined-table behavior.

### Safe practice exercise

Change only the confirmation sentence inside `resetPasswordModal` to clearer wording. Preserve its form action, CSRF tag, hidden field names and button type. Reload as Marketplace Admin, open Reset Password and cancel. Then run the focused tests below. This teaches the distinction between presentation text and the backend input contract without changing any real password.

```powershell
cd backend/core
.\venv\Scripts\python.exe manage.py test accounts.test_marketplace_support --noinput
```

Verify that the confirmation still supplies the correct account_ref and confirm_reset, and that forged/out-of-scope requests remain denied. Revert your wording if it is unclear; do not alter permission codes or remove scope checks as a UI exercise.
