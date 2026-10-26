# Shared admin action alerts and Bookings menu — 2026-10-14

## Current: Marketplace Admin action feedback — October 24, 2026

### 1. Cause / reason

Audit confirmed existing product save/approval/archive/restore/stock modals, order completion/cancellation confirmations, bundle component validation, scoped GET filters and shared action alerts. Preserve these components. Confirmed gaps: seller approval submitted immediately; seller conflict responses could replace the page with JSON; several product/order handlers accepted unreadable 200 responses; report previews could arrive out of order; CSV navigation could not report a server failure; recommendation highlighting redirected without explicit outcome feedback.

### 2. Exact files changed / anchors

| File | Current line or anchor | Purpose |
| --- | --- | --- |
| `backend/static/components/js/admin_action_feedback.js` | 4 `json`, 16 `lock`, `unlock`, submit listener | Read confirmed JSON, preserve disabled states, opt-in GET progress. |
| `backend/templates/partials/admin_alerts.html` | 4, new deferred script | Load shared helpers; existing alert renderer stays authoritative for presentation. |
| `backend/static/components/js/admin_sellers.js` | 1, DOM ready | Confirm reviews, retain reason, lock sibling decisions, POST once, refresh only after confirmed success. |
| `backend/core/api/views.py` | 1429 / 1455, AJAX review responses | Add JSON success contract after existing approval/rejection/revision and audit logging. Normal form redirects retained. |
| `backend/static/components/js/admin_products.js` | 2263 / 2571 / 3844 / 3909 / 3972, `CampusHubActions.json` | Reject login HTML/unreadable responses; require existing product/decision/id payload; use existing error toast. |
| `backend/static/components/js/admin_orders.js` | 43 `actionPending`, `finishOrderAction`, four mutation handlers | Guard concurrent actions, require actual order response, one post-refresh success notification. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_monitoring.js` | submit / pageshow | Confirmation and operation loading for existing highlight action, guarded resubmission and disabled-state restoration. |
| `backend/core/modules/marketplace/bundle_monitoring_views.py` | 164, `messages.success` | Confirm workspace highlight after the existing service succeeds; accurately states no email/push sent. |
| `backend/core/modules/marketplace/templates/marketplace/pages/` | `admin_sellers.html`, `admin_user_seller.html`, `admin_inventory.html`, `admin_orders.html`, `admin_products.html`, `bundle_monitoring.html` | Version touched assets; mark existing GET filters; retain query inputs; highlight consequence text. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | GET forms | Opt into filter progress. |
| `backend/templates/dashboard/partials/sales_overview.html` | 8, existing filter form | Opt-in progress for native submission; prevented AJAX submissions remain owned by their existing handler. |
| `backend/core/modules/reports/templates/reports/pages/admin_generate_reports.html` | 140, 320 `refreshPreview`, `exportReport` | Ignore stale previews, gate exports on current preview, fetch complete CSV before requesting browser download, readable failures. |
| `backend/core/api/test_mobile_seller_application.py` | `test_ajax_review_*`, `test_ajax_revision_*`, `setUp` | Saved result/conflict/validation regressions; self-contained Program fixture so tests also run individually. |

### 3. Changes made

Navigation remains navigation, without success popups. Seller reviews now ask for confirmation and preserve entered rejection/revision notes on failed requests. All decision buttons in that row lock during submission. Successful reviews refresh the existing URL so counts, filters, pagination and rows stay consistent. Existing product modals and bundle forms stay in place. Orders permit one in-flight mutation and display success once after refresh. GET progress keeps inputs enabled because disabling them would omit selected query parameters.

### 4. Functions, inputs/outputs and data flow

`CampusHubActions.json(response, fallback)` receives a Fetch response and returns parsed successful JSON or throws a readable error. Redirected login, HTML, permission/conflict responses and invalid bodies cannot become success. `lock(root, label, activeButton)` returns false for a repeated lock; otherwise records original button states, disables buttons and adds aria-busy. `unlock(root)` restores those exact states. Helpers do not infer transaction success or change records.

Seller form + existing CSRF token → existing permission/scoped Django review view → existing model method and audit log → `{ok, status, message}` → shared remembered alert and current-page refresh. JSON is returned only for AJAX callers. Failed requests keep the form and notes. Product actions validate their actual existing contracts: decision `ok`, save/stock `product`, archive/restore `id`. Orders require `order` before confirming success.

Reports: controls → versioned preview request → newest response only → existing renderer. CSV export uses the existing download endpoint, checks HTTP/type, reads the complete blob, then asks the browser to download it. The text says download **requested**, because browser save completion cannot be observed. PDF remains the existing native print flow. Example: a delayed old preview cannot replace the newer selected report; no data is fabricated.

### 5. Backend / API behavior

Seller views gain an opt-in response representation; existing permissions, transactions, statuses, model calls, scope and non-AJAX redirects stay intact. Highlight success uses Django messages after the existing service. No new workflow, action URL, recommendation generation or data calculation. Default HTML permission/server error responses become readable frontend failures where fetch is used. Existing server transition/row locking remains the defense against stale writes; no unsupported optimistic-version field was invented.

### 6. Database / migration impact

None. No model/schema/migration, live records, synthetic imports, environment/deployment changes or service restart. Only isolated Django test records were written.

### 7. Tests performed

- **135 Django tests passed**: mobile seller application, orders, bundles, recommendation monitoring, academic inventory scope, Marketplace dashboard and executive dashboard (`scratch/action-feedback-tests.log`).
- **16 further Django checks passed**: report preview/export/date/format tests plus dashboard KPI and empty states (`scratch/action-reports-super-tests.log`).
- **2 final overlapping seller contract tests passed** individually (`scratch/action-feedback-final-test.log`). The first standalone attempt exposed a test fixture dependency on BSIT seeded by another suite; `setUp` now gets or creates its isolated Program and both pass independently.
- **25 action interaction checks passed**, including JSON failures/redirects, row lock, repeated submission, retained reason and original disabled states: `node scratch/verify_action_feedback.cjs`.
- **10 report interaction checks passed**, including failed CSV/no download, complete CSV/requested download, duplicate export lock and latest preview wins: `node scratch/verify_report_feedback.cjs`.
- Django system check and JavaScript syntax checks passed. These are selected regression/DOM checks, not a complete browser certification of every existing action.

### 8. Limitations, troubleshooting and safe exercise

Browser inventory returns no apps/browsers: native confirmations, modal focus, actual file save/print dialogs and responsive pixels remain unverified. Existing no-JS form paths use server redirects/error pages. A network failure after server commit is inherently ambiguous: reload the record before retrying; there is no new idempotency service. Existing permission/data provenance limitations remain. No claim that every external integration is healthy.

Safe exercise: use the isolated seller test command above rather than changing live applications. In the test, observe pending + missing revision notes → HTTP 400 with unchanged record; valid notes → HTTP 200 with persisted needs_revision. For UI debugging use Ctrl+F5; inspect `admin_action_feedback.js?v=20261024-actions` and the failing response status. A failed 403/409 should retain input and produce an error, never a success alert. To confirm disabled-field behavior safely, run the Node action verifier; it asserts search inputs remain enabled during GET progress.

---

## 1. Cause / reason

The user requested removal of Inspection, Documents and Record Payment from the Bookings action dropdown, plus smooth pale-green top-right feedback across **all web admin pages**. Existing feedback used several separate toast styles; booking creation/edit/status changes also did not consistently emit that feedback. This update reuses existing module outcomes through one shared presentation component.

Green success feedback is an explicit user-requested exception to the usual navy/gold/white brand palette. Main cards, tables, sidebar, inventory rules and approval statuses are not recolored.

## 2. Exact files changed, current lines and anchors

Paths are relative to project root. Search by anchors if later edits shift lines.

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/templates/partials/admin_header.html` | 2 shared include | Load alerts through the existing common admin header. |
| `backend/templates/partials/admin_alerts.html` | 1 new partial | Versioned CSS/deferred JavaScript and escaped Django flash messages with their recorded severity. |
| `backend/static/components/css/admin_alerts.css` | 2 region; 3 card; final media queries | Fixed top-right, pale-green success, amber errors, neutral information, dismiss/focus styling, phone bounds, print hiding and reduced motion. |
| `backend/static/components/js/admin_alerts.js` | 4 `initialize`; 17 `show`; 41 `remember`; 47 flash messages; 53 legacy selector | One safe renderer, deduplicated/bounded stack, timers, dismissal/pause, actor-bound reload feedback and adapters for existing toast nodes. |
| `backend/static/components/js/admin_bookings.js` | 284 action label map | Remove three menu shortcuts; filter still prevents unsupported API action names from rendering. |
| `backend/static/components/js/admin_booking_forms.js` | 234 `notify`; 284 schedule feedback | Add creation/edit success after confirmed save; reuse existing schedule success emitter. |
| `backend/static/components/js/admin_booking_workflow.js` | 134 actual update result; 137 `notify` | Notify approved/rejected/cancelled/completed/payment/inspection/document outcomes after the protected update succeeds. |
| `backend/static/components/js/admin_roles.js` | 52 notification region exception; 59 `toast`; 199/257/264 `remember` | Typed permission feedback; retain field errors; notifications stay accessible outside the isolated panel; store confirmed success across role/assignment reloads. |
| `backend/core/api/views.py` | 1386 / 1400 seller application messages | Add Django success feedback after existing authorized approval/rejection, before the existing redirect. |
| `backend/static/components/js/admin_messages.js` | 730 success; 740 error | Conversation deletion feedback after actual API acceptance; errors remain errors. No send-message toast on every chat bubble. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_settings.html` | 201 localStorage success | Truthful profile-image feedback after local browser storage succeeds. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 225 scripts | Booking assets now `20261014-booking-alerts`. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_roles.html` | 273 script | Updated role-controller cache version. |
| `backend/core/modules/messages/templates/messages/pages/admin_messages.html` | 102 script | Updated message-controller cache version. |
| `scratch/admin-alerts/check.cjs` | 1 shared state/security review | Server flash, existing emitters, safe text, error types, deduplication, bounds, dismissal and queued-message isolation. |
| `scratch/admin-reservations/workflow-check.cjs` | script loading / payment tests | Menu removal and existing payment path through Details; actual green shared notification after intercepted confirmed payment. |
| `scratch/admin-reservations/check.cjs` | script loading / schedule-save tests | Actual creation/schedule feedback, phone bounds and reduced motion. |
| `scratch/roles-review/check.cjs` | CSS/script loading / permission save | Actual shared permission feedback while panel isolation stays active; align obsolete QA assumptions with current dependency/protected-role rules. |
| `docs/facility-configuration.md` | latest Bookings menu/alerts note | Link booking-specific behavior to this full guide. |
| `docs/admin-action-alerts.md` | this document | Beginner-friendly implementation, verification and debugging report. |
| `CAMPUSHUB_CONTEXT.md` | shared admin action alerts | Remember scope and the requested green feedback exception. |

## 3. Changes made

Bookings' three-dot menu now shows only supported View Booking Details, Approve, Reject, Edit, Cancel and Complete actions permitted by the server's current workflow. Record Payment, Inspection and Documents shortcuts are removed from that menu. The existing Details tabs/actions, records, exports, payment permissions and mandatory inspection requirements remain available. For payment, use View Booking Details -> Payment -> Record Payment.

All pages using the shared admin header load the same alert component. Existing Products/stock, Orders, Facilities/Services, Users, Backup and Export feedback is adapted rather than replacing their business logic. Roles uses typed success/error feedback and confirmed messages survive necessary reloads. Seller review redirects now include real success flashes. Bookings/Calendar add/edit/schedule/status saves emit success only after accepted API responses.

Alerts have a check icon, clear text, subtle border/shadow and 180 ms opacity/position transition. Success uses background `#F0FDF4`, text `#14532D` and accent `#15803D`; errors use amber/gold and navy. Show at most three distinct alerts; identical messages reuse their card. Success/information lasts 4.5 seconds, errors 6 seconds. Hover/focus pauses dismissal; the close button dismisses immediately. Reduced-motion preference removes animation. Long messages wrap and the region can scroll inside the viewport.

## 4. How it works: functions, inputs, outputs and data flow

`initialize()` runs after the DOM is ready, creates one body-level notification region, and finds the existing admin identity/header and feedback nodes. It adds `has-admin-alerts` so obsolete visual toast boxes are hidden only when the new renderer is actually running. If the script cannot load, those existing emitters keep their original fallback behavior.

`show(message, {type})` takes plain text and success/error/warning/info severity; it returns the displayed card. It uses `textContent` for supplied text, so a product name containing HTML cannot execute scripts. Decorative SVG markup is authored static code. Each alert has role status or alert, atomic announcement semantics and a labelled dismissal button; showing it does not move focus from the user's form.

The compatibility adapter observes **only existing feedback nodes**, not every fetch or table mutation. A visible old toast forwards its real message/type into `show()`. That lets current and cached Products/Orders/Facilities scripts share the new design without duplicating their save calculations or pretending every HTTP response is a successful mutation. Server-side Django messages are escaped into the shared partial and displayed using their recorded severity; duplicate visible feedback is suppressed by the renderer.

`remember(message, type)` stores one confirmed message for a subsequent page reload in sessionStorage, keyed to the current admin ID. The next page consumes it once, discards values older than 30 seconds or malformed data, and does not read another admin's key. No credentials, tokens, permissions or database records are stored by the component. This is short-lived presentation state, not proof of an operation or an audit record.

```javascript
const result = await existingSaveAPI(data); // Caller must validate actual API success first.
window.CampusHubAlerts.success(result.message); // One green notification; no database action.
// For a required reload:
window.CampusHubAlerts.remember(result.message);
window.location.reload(); // Same actor sees the accepted outcome once after rendering.
```

For an existing module with a toast emitter, keep using that emitter: its visible message is forwarded automatically. New features may call `CampusHubAlerts.success/error/info` or dispatch `campushub:notify` with `{message,type}` after their existing outcome checks. Do not attach success feedback to a save-button click before its API response.

Flow: authorized user action -> existing server validation/write -> accepted result or Django flash -> shared renderer -> optional user dismissal/automatic fade. Failure paths retain current field/modal errors and are not styled green. Bookings still refreshes its actual list/KPIs through the existing event and fetch path; feedback does not calculate a replacement value.

## 5. Backend / API behavior

No new API, permission, authentication, inventory, payment, booking, role or chat business rules. Menu filtering is presentation only; it does not revoke backend capabilities. Seller approval/rejection adds a Django flash after its existing scope/RBAC and write/audit handling, preserving the redirect; `fail_silently=True` preserves compatibility with callers without message middleware. Role writes still use their existing protected APIs. Conversation deletion still uses the existing chat API and authorization, with feedback after acceptance rather than fabricated success.

Settings profile-image feedback explicitly says saved **in this browser** because the existing operation is localStorage, not a server profile update. Unimplemented Settings Save buttons were not given false saved messages. Read-only chart/filter/page loading is not reported as a record save. Downloads/printing are not labelled completed merely because their browser request started.

## 6. Database / migration impact

No model, field, migration, seed, role grant rewrite or live database modification during implementation. Existing actions continue to write their existing records when an authorized user intentionally performs them. `makemigrations --check --dry-run`: No changes detected. Browser POSTs were intercepted; exported fixtures use the isolated Django test database. No real emails or chat messages were sent by QA.

## 7. Tests performed, manual checks and debugging

- **70 booking tests passed** for reservation creation/edit, transactions, protected documents/payments/inspection, Calendar and mobile availability.
- **147 admin regression tests passed** for Roles, Users, marketplace account support, data exports, dedicated/global dashboards, Orders and bundles. Existing scope/final-Super/stock checks remain passing.
- **Two chat-token tests passed**, plus one existing isolated role fixture-export test. Django system check clean; new assets resolved through findstatic; JavaScript syntax and scoped whitespace checks passed.
- Shared state/security QA passed: Django flash adaptation, old cached emitter forwarding, error semantics, duplicate suppression, max-three stack, HTML-injection safety, dismissal, same-actor reload, different-actor isolation, stale and malformed queued messages.
- **Four transaction browser cases and four creation/schedule cases passed** at 1440/768/390/320 px. Checks confirm the removed menu shortcuts, payment still works through Details, soft-green confirmed feedback, viewport bounds, reduced motion and no JavaScript exceptions.
- **Six Roles browser cases passed** at 1920/1440/1024/768/375/320 px, including shared success while the permission panel is isolated. The old QA tried to uncheck a required View prerequisite and inspect the removed User-role UI; QA was updated to a valid write-permission change and current protected-Super view. Application permission dependencies were not weakened.
- Phone alert screenshot was visually reviewed: pale green, dark readable text, right-corner placement, wrapping and close controls.

Manual checks:

1. Ctrl+F5 Bookings. Open the three-dot menu: Inspection, Documents and Record Payment should be absent. View Details -> Payment must still offer permitted recording; configured Inspection and Documents stay in their detail tabs.
2. On intentionally saving a real reservation/edit/schedule/status change, expect one success alert after the server accepts it. Invalid/conflicting submissions must not show green success; current inline validation remains.
3. Save/edit an intended Product/stock value or Facility/Service; the old feedback emitter should appear in the new top-right style. Verify actual records in the appropriate module, not from toast text alone.
4. Save a role/assignment in an isolated environment and confirm feedback survives the reload, with unchanged permissions. Do not modify production roles merely to test a popup.
5. Verify normal Users/Seller review/Backup redirect messages, amber failure feedback, duplicate suppression, close, hover/focus pause and reduced motion. Narrow the viewport: messages must wrap inside the screen.

From project root:

```powershell
node scratch/admin-alerts/check.cjs
node scratch/admin-reservations/workflow-check.cjs
node scratch/admin-reservations/check.cjs
node scratch/roles-review/check.cjs
```

For isolated Django regression commands, run from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py test accounts.test_roles_permissions accounts.test_user_management accounts.test_marketplace_support accounts.test_data_exports modules.reports.test_marketplace_admin_dashboard modules.reports.test_dashboard_marketplace modules.marketplace.test_orders_admin modules.marketplace.test_bundles --keepdb --noinput
venv/Scripts/python.exe manage.py check
```

Debugging: look for the shared header include and asset `20261014-shared-alerts`; hard-refresh. `CampusHubAlerts` should exist after DOM readiness. For an old emitter, inspect its visible show/is-show/is-visible class and is-error/type class; no broad fetch interception is used. For a missing booking alert, inspect whether the existing save API actually returned success. Menu scripts use `20261014-booking-alerts`. If a queued message does not reappear, inspect the same-user sessionStorage key and 30-second TTL; never use that cache to infer database status. An error in its malformed cache must not break the page.

Safe practice: on a local branch, change only the notification border radius in `admin_alerts.css`. In the browser console, call `CampusHubAlerts.info('Local style practice only.')`; this displays UI and performs no API call. Inspect the shape at desktop/phone widths, verify keyboard dismissal and reduced motion, then revert the CSS. This teaches shared styling without changing accounts, products or bookings.

## 8. Remaining limitations

The shared header establishes feedback availability across web admin pages; only existing supported operations and their explicit emitters/confirmed hooks report outcomes. It does not implement missing save workflows. Settings' current profile picture remains local-only. Legacy emitters created dynamically after initialization need an explicit shared helper call; current known feedback nodes are initialized from the rendered page. Up to three distinct notices are shown at once; repeated identical feedback extends its timer. Existing inline reservation View Booking Details and field/modal errors remain useful and are preserved. Mobile checks used Chrome viewport emulation, not physical-device deployment testing.
