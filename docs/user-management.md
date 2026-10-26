# User Management: roles, academic scope, seller access and account safety

## Program/Major activity wording (October 11, 2026)

### Browser application names (October 11, 2026)

**Reason and change:** the Browser value included a version number because `parse_connection` appended the regex's numeric match to the application name. It now displays only the detected name: Google Chrome, Microsoft Edge, Mozilla Firefox, Safari or Opera.

**Files and anchors:** `backend/core/accounts/activity_service.py:71`, `browser = label`; `backend/core/accounts/test_activity_api.py:107`, expected connection dictionary, and `:268`, `test_browser_signatures_without_unjustified_windows_version`; `CAMPUSHUB_CONTEXT.md:3`, Current Activity Details; this guide's browser subsection at line 5. `scratch/monitoring-review/check-activity.cjs:37` now expects the name without its version; that local helper was syntax-checked but not rerun in a browser for this wording change. Tests retain realistic numeric user-agent inputs and verify name-only outputs, including Opera's Chrome-compatible signature.

**Functions and data flow:** `parse_connection(user_agent, ip_address)` reads the stored user-agent and returns a dictionary containing IP address, device and browser. Signature checks identify Edge/Opera before Chrome; only the returned browser label changed. `Chrome/155.0` now returns `Google Chrome`. `format_activities` uses this dictionary in Activity Details and DRF responses; `connection_summary` also reuses it in user summaries. No additional browser detection or separate JavaScript formatter was added.

**Backend/API and database:** existing routes, scope restrictions and response keys remain. No migration, data rewrite or stored user-agent change. Scoped Marketplace readers still receive no connection details.

**Verification:** all 20 activity API tests passed, including browser signatures, privacy and web/API consistency; Django system check reported no issues. Log: `scratch/monitoring-browser-name-tests.log`. Manually refresh User Monitoring and open an existing event's eye icon: Browser should show a name without a version.

**Debugging/limitations:** names come from existing recorded signatures, not an installed-app scan. Unknown signatures remain Unknown; clients whose user-agent does not identify a distinct browser cannot be distinguished reliably. If a version still appears, check the running backend checkout and restart it when auto-reload is disabled.

**Safe practice:** inspect the signature test's numeric inputs, predict each resulting application name, then run `venv/Scripts/python.exe manage.py test accounts.test_activity_api.ActivityAPITests.test_browser_signatures_without_unjustified_windows_version --keepdb --noinput` from `backend/core`. A passing test confirms versions do not leak into the display. Do not edit production user-agent records to test formatting.

### Cause, files and changes

Confirmed cause: `action_label` converted `ADMIN_SCOPE_CHANGED` directly into Admin Scope Changed. The event is recorded when Users account editing changes `department_id` (Program) or `major_id`, at `accounts/views.py:607`. It describes an academic assignment change, rather than a permission change.

Paths below are relative to the project root:

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/accounts/activity_service.py` | 16, `admin_scope_changed` in `ACTION_LABELS` | Added the readable label Program/Major Updated. |
| `backend/core/accounts/test_monitoring.py` | 117, `test_last_activity_is_action_only_without_rewriting_audit_history` | Checks the new table, drawer summary and modal label against an unchanged historical description. |
| `CAMPUSHUB_CONTEXT.md` | 5, `Current User Monitoring` | Records this production wording. |
| `docs/user-management.md` | 3, this section | Documents the cause, shared formatter and verification. |

### How it works and backend / API behavior

`action_label(event)` at `activity_service.py:38` receives an existing audit event and returns a display string. It lowercases the event code and looks it up in `ACTION_LABELS`; unmapped codes retain the existing fallback. The same helper supplies User Session Overview, its drawer summary, Recent User Activity Log, Activity Details and DRF activity responses. It performs no queries or writes. One shared mapping avoids inconsistent labels between web and API.

Example: an existing event with `activity_type="ADMIN_SCOPE_CHANGED"` and stored description `Admin Scope Changed by 2023304615` displays **Program/Major Updated** in monitoring summaries and details. The stored description remains unchanged. Detailed raw history can therefore still contain the original wording. Actual Roles & Permissions changes continue to display Permissions Changed.

### Database impact, verification and manual checks

No models, migrations, permissions, routes or production records changed. The earlier wording passed the focused monitoring label test and all 20 activity API tests (**21 tests**). The shortened Program/Major Updated wording passed the same focused monitoring test (1 test, including four action cases), with no Django system-check issues. Latest log: `scratch/monitoring-short-label-tests.log`. Earlier log: `scratch/monitoring-assignment-label-tests.log`.

Manual verification: refresh User Monitoring, find an existing Program/Major assignment event and open its eye-icon details. Confirm the new Action label and matching Last Activity summary. Check a permissions event still says Permissions Changed. Use existing events or isolated test accounts rather than changing a production user's academic assignment just to test text.

### Debugging, limitations and learning exercise

If the old wording remains in a monitoring summary, check the server is running this checkout and restart it if auto-reload is disabled. Confirm the event code is `ADMIN_SCOPE_CHANGED`; stored raw audit-history descriptions intentionally remain original. Other event codes keep their existing labels.

Safe practice: read the mapping at line 16, then trace `action_label` through `views.py:1282` and `format_activities` at `activity_service.py:82`. Run `venv/Scripts/python.exe manage.py test accounts.test_monitoring.MonitoringRefinementTests.test_last_activity_is_action_only_without_rewriting_audit_history --keepdb --noinput` from `backend/core`. The test verifies both the new display label and preservation of stored audit text. This demonstrates how to change presentation without rewriting recorded facts.

## Final User Monitoring labels and table (October 11, 2026)

This section is the latest refinement of User Monitoring. It supersedes older Time/Actor/Target table labels and the previous Active Sessions wording below. The page layout, charts, filters, colors, row spacing, pagination and existing data sources are preserved.

### 1. Cause / reason

Confirmed by inspection: Recent User Activity Log showed separate Actor and Target columns. User Session Overview used `AccountActivity.activity`, a stored narrative that may end with `by <username>`, for Last Activity. The session KPI said Active Sessions even though its existing count covers authenticated web administrator tab sessions. Activity Details grouped the actor's role under the name without a separate Role label.

The change makes the table compact and the scope of the session count clear. Detailed affected-record information stays in the eye-icon modal, while Last Activity uses the same concise action name as the DRF API. No historical audit descriptions are rewritten.

### 2. Exact files, current lines and nearby anchors

All paths are relative to the project root. These are current starting lines; searching the anchor is useful when later edits move code.

| File | Line / anchor | Changes made |
| --- | --- | --- |
| `backend/core/accounts/activity_service.py` | 32, `display_role` | Moved the existing ordinary-role display normalization into the shared service; User/Standard User displays as User, with administrator names preserved. |
| Same file | 38, `action_label` | Extracted the existing event-code action label into one reusable function used by web and DRF formatting. |
| Same file | 82, `format_activities` | Reuses the two helpers; normal-role aliases are normalized in `performed_by.role` too. |
| `backend/core/accounts/monitoring.py` | 8, `from .activity_service import display_role` | Re-exports the same helper for existing callers; no duplicated implementation or changed session calculation. |
| `backend/core/accounts/views.py` | 1217, `action_label` import; 1282, `row["last_activity"]` | Last Activity now takes the concise label from the real latest event. Both the table and drawer summary use this value. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 63, `Active Web Sessions` | Renamed the web KPI and its supporting description. The scoped Marketplace card remains Accounts with Activity. |
| Same file | 237, `<th>User</th>` | Recent log uses Time / User / Action / Module / Result / Actions. The User cell still displays the real performer from `activity.actor`; Target header/cell removed. |
| Same file | 260, `colspan="6"` | The empty recent-log row spans the new six columns. User Session Overview still uses seven columns. |
| Same file | 15 and 341, `20261011-monitoring-final` | Updated JS/CSS cache versions. |
| `backend/static/components/js/admin_monitoring.js` | 208, `Date & Time`; 210, `pairs.push(["Role"` | The modal shows Performed By and Role separately, followed by the existing dynamic affected-record and connection fields. Missing Role is hidden rather than fabricated. |
| `backend/static/components/css/admin_monitoring.css` | 725, `.recent-activity-table` | Adjusted six-column width assignments and Result/Actions alignment. Existing minimum width, typography, row height and colors remain. |
| `backend/core/accounts/test_monitoring.py` | 101, `test_final_log_columns_keep_target_in_details_only` | Tests six headers, performer identity, target retained in details, eye-only action and six-column empty state. |
| Same file | 117, `test_last_activity_is_action_only_without_rewriting_audit_history`; 133, `test_legacy_guest_role_is_user_in_activity_details` | Tests the requested action examples, unchanged stored descriptions and legacy normal-role display privacy. Existing KPI/action assertions were updated. |
| `backend/core/accounts/test_user_management.py` | 327, `lastActivity` | Expects User Updated in the summary while keeping the actual recorded history text. |
| `backend/core/accounts/test_marketplace_support.py` | 177, `lastActivity` | Expects Product Approved while preserving scoped-account and connection restrictions. |
| `backend/core/accounts/tests.py` | 1736, `<th>User</th>` | Existing monitoring assertion now requires User and rejects Actor/Target headers. |
| `CAMPUSHUB_CONTEXT.md` | 3 and 5, `Current Activity Details` / `Current User Monitoring` | Records the final labels, action-only summaries and unchanged authorization/session scope. |
| `docs/user-management.md` | 52, `Final User Monitoring labels and table` | Adds the monitoring implementation report, debugging steps, functions/data flow and safe learning exercise. |

Local verification helpers updated: `scratch/monitoring-review/check-ui.cjs` and `check-activity.cjs`. They check the new table/header/modal contract in headless Chrome using isolated test fixtures; they are not application code.

### 3. Changes made: final visible behavior

Recent User Activity Log:

```text
TIME | USER | ACTION | MODULE | RESULT | ACTIONS
```

Here User means the person who performed the action, preserving the previous Actor meaning. It does not silently replace the actor with the affected account. Affected User/Role/Product/Order/Booking/Facility/Seller stays in the existing eye-icon Activity Details modal.

User Session Overview remains:

```text
USER | ACCOUNT TYPE | ROLE | STATUS | LAST LOGIN | LAST ACTIVITY | ACTIONS
```

Last Activity displays only a readable event action such as Program/Major Updated, Email Verification Initiated, Email Verification Code Sent or Logged In. Both tables keep their single eye-icon button. Activity Details shows Date & Time, Performed By, a separate Role row, the applicable affected-record label, Action, Module, Result, and the existing authorized IP Address / Device / Browser rows. Missing values and scoped connection restrictions still apply.

The Super Admin KPI now reads **Active Web Sessions** / **Currently authenticated web sessions**. Marketplace Admin's existing fourth KPI is Accounts with Activity, which counts scoped activity rather than web sessions; it remains correctly named.

### 4. How it works: functions, inputs, outputs and data flow

`action_label(event)` receives the actual `AccountActivity` object. It reads `activity_type`, applies the existing special-case labels for login/logout/permission and academic-assignment changes, and otherwise converts the code to readable words. It returns a string and performs no database queries or writes. It does not trim a name out of the stored description with an unreliable text-splitting rule.

Annotated example:

```python
# Existing database event:
# activity_type = "ADMIN_SCOPE_CHANGED"
# activity = "Admin Scope Changed by 2023304615"
row["last_activity"] = action_label(event)
# Output: "Program/Major Updated"
# The original event.activity remains untouched for the audit history.
```

`display_role(value)` receives an existing role string and returns a display label. The legacy Standard User alias becomes User; real administrator names remain unchanged. This is presentation only: no role assignment, permission grant, account type or backend authorization rule is modified. `accounts.monitoring` imports the function to preserve existing `from accounts.monitoring import display_role` callers.

Data flow:

```text
Existing scoped latest audit event
    -> action_label(event)
    -> row.last_activity
    -> User Session Overview + drawer Last Activity summary

Existing scoped audit log page
    -> shared format_activities
    -> six-column table (performer + action)
    -> eye-icon modal (performer, Role, affected record, permitted connection)
    -> existing DRF serializers (same shared labels)
```

Detailed drawer history keeps the recorded narrative. The change is specifically to Last Activity summaries and the recent-log column layout. Stored event descriptions containing `by ...` are not erased from the database.

### 5. Backend / API behavior

Existing audit model, queryset scope, date filters, latest-event selection and pagination are reused. The existing DRF routes `/api/activity-logs/` and `/api/activity-logs/<id>/` are unchanged. DRF formatting shares `action_label` and `display_role`; its response keys, authentication, permissions and safe affected-record structure remain unchanged.

Super Admin global access and Marketplace Admin eligible-account / Program-Major / event restrictions still apply. Facilities Admin and ordinary accounts remain denied by the existing policy. Marketplace Admin still cannot see connection details. The UI changes do not grant new permissions.

The Active Web Sessions count still uses the existing `tracked_sessions` function: enabled, unsuspended administrators' unexpired, recently observed `AdminTabToken` records. This is not a count of all Django session rows or all mobile logins. No new session registry, duplicate count or fake monitoring record was introduced.

### 6. Database / migration impact

None. No model, migration, historical audit row, session record or production account was changed. Tests use isolated database records and browser fixtures only. Role aliases are converted only at display time.

### 7. Tests and manual verification

Actual verification results:

- **85 tests passed** across monitoring refinements, DRF activity reads, user-management history, Marketplace scope and existing monitoring tests (`scratch/monitoring-final-labels-verified.log`). This includes action-only summaries, unchanged stored audit text, legacy role normalization, six-column empty state and retained modal targets.
- Headless Chrome passed **1920, 1440, 1024, 768, 375 and 320** widths, plus chart-error/server-error cases. It checked both tables' exact headers, web-session wording, one recent-row action button, filter/chart behavior, loading, modal Role and keyboard focus (`scratch/monitoring-final-labels-browser.log`).
- Dedicated activity-modal checks passed for Super Admin and scoped Marketplace Admin at **1440, 375 and 320**; affected records remain visible and scoped connection details remain hidden (`scratch/monitoring-final-details-browser.log`). The 375px modal screenshot was visually inspected.
- JavaScript syntax and Django system checks passed. `makemigrations --check --dry-run` reported **No changes detected**.

The first 85-test run had one outdated assertion expecting the removed Actor header; that assertion was corrected to the final contract, then the complete selected suite passed. It was not an application failure. These checks used isolated test fixtures, not live sample data or emails.

Manual checks:

1. Hard-refresh User Monitoring (JS/CSS version `20261011-monitoring-final`). Verify six recent-log columns and seven User Session Overview columns.
2. Open an existing role/product/user activity with its eye icon. Check Role has its own label and the affected entity is visible only in the modal.
3. Check Last Activity on an existing verbose event: it should show its action without `by <username>`. Its audit history should still retain the original description.
4. Check Super Admin's Active Web Sessions label/subtitle and count. Verify that changing this text did not create another session source.
5. Open a Student or Guest/External activity: the normal Role should be User. Check administrator role labels still match their actual roles.
6. Change filters and pages, then resize the browser. Check the existing charts, table scrolling, pagination, eye buttons and modal keyboard behavior still work.
7. Repeat with Marketplace Admin: only existing permitted events should load, and connection information should remain hidden.

### Debugging and safe learning exercise

- Old header/KPI/modal labels: hard-refresh and inspect the asset version first; do not edit authentication to fix a cached JavaScript problem.
- Last Activity still has `by ...`: check `views.py:1282` uses `action_label(event)`, not `event.activity`. Do not rewrite historical audit rows.
- Result or eye button is misaligned: check the six-column CSS selectors around line 725. The Result column is now fifth; Actions is sixth.
- Unknown performer/role or no affected entity: some historical audit rows lack actor/target evidence, and login events intentionally have no affected target. Do not fabricate a name to fill the row.
- Different session count than mobile presence: Active Web Sessions uses the existing web tab tokens; mobile recent-login presence is a separate existing estimate, not this KPI.

Safe practice: in a temporary test fixture, create an `ADMIN_SCOPE_CHANGED` event whose description contains `by <test username>`. Assert that the monitoring summary is Program/Major Updated, while reloading the event still returns the original description. Run the existing focused test:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\backend\core
venv\Scripts\python.exe manage.py test accounts.test_monitoring.MonitoringRefinementTests.test_last_activity_is_action_only_without_rewriting_audit_history --keepdb --noinput
```

This exercise teaches the difference between a stored audit fact and a display label. Verification means both assertions pass; it does not require editing production data or copying the formatter into JavaScript.

### 8. Remaining limitations

Missing historical actor evidence remains Unknown; no current UI change can reconstruct a missing historical identity. Unknown connection signatures stay Unknown. Web-session coverage remains the existing tab-token tracking, not complete mobile session tracking. The scoped Marketplace fourth KPI is deliberately not renamed to a web-session count. No whole-page redesign or unrelated feature change was made.

## Shared Activity Details: Django web and DRF (October 11, 2026)

This is the current Activity Details implementation. It supersedes the older descriptions below about rendering metadata in the modal or returning a raw user-agent. Other User Monitoring calculations, existing routes, audit writes, account history, and RBAC remain in place.

### 1. Cause / reason

Confirmed by inspection: the modal used Time/Actor/Target, then printed whitelisted metadata including database IDs. Device / Browser was the full stored user-agent. The authoritative backend in `backend/core` had no DRF activity endpoint or DRF installation. The separate `campushub/backend` directory contains an incomplete DRF login scaffold using a different login model; it is not the current admin activity backend. No audit model or authentication business logic was copied into that scaffold.

The fix integrates DRF into the main Django project and formats existing `AccountActivity` records through one backend service. This keeps the web modal and API consistent without another activity table, duplicated event writes, or a second RBAC system.

### 2. Exact files, current lines, and nearby anchors

Paths below are relative to the project root. Line numbers are current starting locations, not fixed forever; search for the anchor if lines move.

| File | Line | Nearby anchor | Change and purpose |
| --- | ---: | --- | --- |
| `backend/core/accounts/activity_service.py` | 44 | `parse_connection` | Added recognized device/browser formatting, with honest Unknown fallbacks. |
| Same file | 82 | `format_activities` | Added shared actor, affected-record, action, module, result and connection formatting; resolves names in batches. |
| Same file | 120 | `recorded_text` | Accepts only readable string snapshots; rejects malformed objects/lists and null-like placeholder strings. |
| `backend/core/api/activity_api.py` | 25 | `ExistingCampusHubAuthentication` | Adapts existing tab authentication and existing mobile JWT identity verification. |
| Same file | 48 | `CanReadActivity` | Reuses Django monitoring permission and the existing allowed administrator roles. |
| Same file | 80 | `ActivityListSerializer` | Explicit safe output fields; detail serializer at line 90 adds the affected record and connection. |
| Same file | 95 | `ActivityPagination` | Twenty rows by default, maximum 100; numeric next/previous page references avoid echoing tab credentials in URLs. |
| Same file | 111 | `ActivityAPIView` | Applies existing scope before reads, consistent errors and `Cache-Control: no-store`. |
| Same file | 141 | `ActivityDetailView` | Reads one authorized existing audit row; list/filter view begins at line 148. |
| `backend/core/accounts/monitoring.py` | 65 | `event_rows` | Replaced duplicate actor/entity formatting with the shared formatter; removed metadata from frontend payloads entirely. |
| `backend/core/accounts/views.py` | 1217 | `connection_summary` import | Uses the shared parser for drawer history and latest-device summaries at lines 1365 and 1399. |
| `backend/core/core/urls.py` | 126 | `activity_log_list` | Adds list and detail routes, alongside the existing web monitoring route. |
| `backend/core/core/settings.py` | 88 | `'rest_framework'` | Registers DRF in the existing Django project. No global authentication defaults changed. |
| `backend/core/requirements.txt` | 2 | `djangorestframework` | Adds the DRF dependency; local verification used version 3.18.3. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 330 | `activityConnectionTitle` | Adds a small connection heading and definition list to the existing modal. Asset versions at lines 15 and 341 are updated. |
| `backend/static/components/js/admin_monitoring.js` | 118 | `details` | Supports a second line for the performer's role using safe DOM text nodes. |
| Same file | 205 | `.js-activity-view` | Uses Date & Time, Performed By and the dynamic affected-record label; hides missing values and restricted connection information. |
| `backend/static/components/css/admin_monitoring.css` | 826 | `#activityDetailList` | Reuses existing compact definition-list styling for connection rows. Role secondary text at line 856, connection heading at 863. |
| `backend/core/accounts/test_activity_api.py` | 26 | `ActivityAPITests` | Adds isolated API, privacy, identity, scope, pagination, browser parsing and web/API consistency tests. |
| `backend/core/accounts/test_monitoring.py` | 180 | `assertNotIn("metadata"` | Updates the historical-privacy assertion to the new, stricter output contract. |
| `backend/core/accounts/test_user_management.py` | 328 | `'device','Unknown'` | Updates an unrecognized-agent test: the drawer must show Unknown instead of returning the raw test agent. |
| `CAMPUSHUB_CONTEXT.md` | 3 | `Current Activity Details` | Records the shared-source architecture and current privacy/authentication behavior. |

Verification helpers live in `scratch/monitoring-review/check-ui.cjs` and `check-activity.cjs`. They are local browser checks, not shipped app functionality. Fixtures and example responses come from the isolated test database, not from inserting fake production records.

### 3. Changes made: modal and output privacy

- Kept the existing modal, navy/white styling, spacing, focus trap, Close actions, Escape behavior and responsive layout.
- Time becomes **Date & Time**. Actor becomes **Performed By**, with the actual name and role on separate lines.
- Target becomes **Affected User / Role / Product / Order / Booking / Facility / Seller**, according to the real event metadata and existing records. A login/logout event has no affected-record row.
- Added **Connection Information** with separate IP Address, Device and Browser rows. Missing IP is omitted; Marketplace Admin retains its existing prohibition on connection details.
- Removed raw metadata rendering and metadata payloads. IDs still exist internally for lookups, but actor/target IDs, role UUIDs, session identifiers, codes and tokens are not transmitted as detail fields.
- Removed the full user-agent from both Activity Details and user drawer summaries. JavaScript only displays backend-provided labels through `textContent`; it does not parse user-agents, identify actors or resolve entities itself.

### 4. How it works: functions, inputs, outputs and data flow

```text
Existing PostgreSQL AccountActivity records
    -> existing scope / permission checks
    -> one bounded page or authorized detail row
    -> activity_service.format_activities(...)
       -> existing Django event_rows -> Activity Details modal
       -> explicit DRF serializer -> JSON response
```

`AccountActivity` is unchanged (`backend/core/accounts/models.py`, line 148, table `campushub_account_activity`). The formatter is read-only: it never records another event.

`format_activities(events, scoped=False, include_targets=True)` receives existing audit objects and returns structured dictionaries. It collects actor/entity identifiers and performs batch lookups instead of one query per event. Product/facility/role names come from existing records, with safe recorded name snapshots as fallbacks. Orders use their existing public order code; bookings use their existing public booking reference. No integer order-ID fallback is exposed as a display name. Malformed historical UUIDs/keys do not crash the page.

The actual actor is resolved from `actor_admin_id`, independently of the affected account's snapshot. When an actor was deleted but a recorded username survives, the name can be shown but the role is null rather than invented. Authentication events use their recorded account identity. An unknown management actor stays Unknown. **CampusHub System / System** requires explicit `system_generated: true` evidence, rather than assuming every unknown actor is the system.

`parse_connection(user_agent, ip_address)` receives already-stored connection information and returns a small dictionary. Edge/Opera are recognized before Chrome because their agents also contain Chrome. Only the detected browser application name is displayed, without version numbers. `Windows NT 10.0` cannot distinguish Windows 10 and Windows 11, so the label is **Windows Desktop**, consistent with [Microsoft's browser detection guidance](https://learn.microsoft.com/en-us/microsoft-edge/web-platform/how-to-detect-win11). Unrecognized signatures become Unknown. No extra parser package or invented client IP is used.

`recorded_text` accepts only short string snapshots. A historical object such as `actor_username: {password: ...}` cannot be converted into a visible string. The public serializers allow only the named output fields, and neither web nor API sends the metadata object.

Annotated example:

```python
# These are EXISTING audit rows, already permission/scope-filtered.
details = format_activities(events, scoped=is_marketplace_admin(actor))
# actor metadata -> actual administrator name/role, not the target's role
# login_success -> "Logged In", affected_record -> None
# scoped=True -> connection=None (existing support privacy rule)
```

This approach was chosen because a serializer alone would not fix the Django modal, while two separate formatters could disagree about actors, targets or privacy.

### 5. Backend / API behavior and permission enforcement

Read-only routes:

- `GET /api/activity-logs/`
- `GET /api/activity-logs/<id>/`

Authenticate with the existing valid admin tab token in `X-Admin-Tab-Token`, or an authenticated Django session cookie. The existing `__at` query convention also works, but the header avoids placing credentials in request URLs. Never paste a real token into documentation or commit it. Invalid/expired supplied credentials fail closed, even if a valid cookie is also present.

DRF adapters reuse the project's current authentication functions. A valid mobile JWT can identify a mobile account, but **does not authorize administrative audit access**: normal mobile Student/Guest accounts receive 403. No new JWT issuance flow, SimpleJWT integration or DRF token table was added. DRF's distinction between authentication and permissions follows its [official authentication guide](https://www.django-rest-framework.org/api-guide/authentication/).

Authorization remains the existing policy:

| Caller | Behavior |
| --- | --- |
| Super Admin with monitoring permission | Global monitoring access. |
| Marketplace Admin with monitoring permission | Existing eligible-account, Program/Major and supported-event scope only; no IP/device/browser details. |
| Facilities Admin | Denied, including an old direct monitoring grant, matching the current web policy. |
| Ordinary Django user, mobile Student/Guest, unrelated custom administrator | Denied. |
| Anonymous or invalid/expired credentials | 401. |

`support_activity` runs **before** retrieval, pagination, totals and serialization. An out-of-scope detail returns 404; a scoped list excludes it. This prevents obtaining a foreign activity by guessing its ID.

List parameters: `search`, `actor` (username), `account_type`, `role`, `activity_type`, `module`, `result`, `date_from`, `date_to`, `page`, `page_size`. Actor filtering also handles historical rows carrying only `actor_admin_id`. Module filters match the normalized module and its existing aliases. Dates use inclusive calendar days implemented as a start-inclusive/end-exclusive datetime range; invalid/reversed dates return 400. No new filtering library was needed. Pagination uses DRF's [documented page-number mechanism](https://www.django-rest-framework.org/api-guide/pagination/).

Responses have `success` and `data`; paginated lists add `pagination`. Errors use `success: false`, `message`, `errors`, with 401/403/404/400 as appropriate. Database read failure returns a generic 503 Retry message, never fake zero data or database exception text. Writes are not supported (405).

Example response shape, from isolated test accounts:

```json
{
  "success": true,
  "data": {
    "id": 123,
    "date_time": "2026-10-10T11:00:00+08:00",
    "performed_by": {"name": "Audit Owner", "username": "audit-owner", "role": "Super Admin"},
    "affected_record": {"type": "user", "label": "Affected User", "name": "Student Example"},
    "action": "Account Recovery Initiated",
    "module": "User Management",
    "result": "Success",
    "connection": {"ip_address": "127.0.0.1", "device": "Windows Desktop", "browser": "Google Chrome"}
  }
}
```

The audit ID identifies the requested record. Internal actor/target keys are excluded. The actual ID/date comes from the database; the values above explain the shape and are not hardcoded by the endpoint. Existing configured timezone is respected. This checkout currently uses UTC; timezone tests explicitly exercise Asia/Manila (+08:00). No global timezone change was made.

### 6. Database / migration impact

No application model, schema, migration, permission grant, production account, historical audit row or live sample data was changed. DRF was installed in the existing backend virtual environment (3.18.3) and registered as an app. Another checkout must install the updated requirements before startup:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\backend\core
venv\Scripts\python.exe -m pip install -r requirements.txt
```

The existing token resolver may refresh last-seen timestamps or remove expired tokens when authenticating, as it already did. It is not new activity-log business logic. Test setup creates missing unmanaged legacy tables only in the test database, following existing project test practice.

### 7. Verification and manual testing

Actually run:

- 108 tests passed across the new activity API, monitoring, Users, Marketplace support, Roles & Permissions and existing monitoring tests (`scratch/activity-api-verified.log`).
- 60 focused API/recovery tests passed after formatter hardening (`scratch/activity-api-final-focused.log`).
- 14 final privacy/monitoring tests passed after removing web metadata payloads (`scratch/activity-api-final-privacy.log`). These runs overlap; they are not a claim of 182 distinct tests.
- Headless Chrome passed six widths: 1920, 1440, 1024, 768, 375 and 320; checked charts/filter behavior, loading, keyboard trap/focus return, login target omission, chart failure and server Retry (`scratch/activity-modal-browser.log`).
- Recovery modal checks passed for Super Admin and scoped Marketplace Admin at 1440/375/320; checked actual role/name, target, browser labels, connection privacy and viewport fit (`scratch/activity-modal-details-browser.log`). Mobile screenshot was visually inspected.
- JavaScript syntax, Django system check, `makemigrations --check --dry-run` and `pip check` passed; no migrations detected.

Initial test-fixture failures were corrected: the real order model uses `buyer_user_id` rather than a buyer FK, mobile test accounts require unique emails, and timezone expectations must follow configured timezone. These were test assumptions, not evidence that production models needed alteration. The final passing runs above are the evidence.

Manual steps:

1. Restart Django and hard-refresh User Monitoring (assets `20261011-monitoring-final`). Open an existing recovery activity: check Performed By is the administrator and Affected User is the actual target.
2. Open a role-change/deactivation event and a login event. The role event should show the correct affected entity; the login must omit it.
3. Inspect the detail and list GETs with your existing authenticated session or tab header. List output must be minimal, paginated and free of metadata; detail must omit IDs/secrets/raw user-agent.
4. Try a scoped Marketplace account. Own supported events should load; a foreign Program/Major record ID should return 404; connection information should be hidden.
5. Try an ordinary account and Facilities Admin: both must be denied. Logged-out/expired requests should be 401.
6. Try an invalid date and a page beyond the list: verify honest 400/404 envelopes. Do not deliberately stop the live database; error states are exercised through mocked failures in tests.
7. At a narrow window width, open/close the modal with mouse and keyboard; verify wrapping, Escape and focus return.

### Debugging / troubleshooting

| Symptom | Where to inspect | Meaning / safe action |
| --- | --- | --- |
| DRF import error on another machine | requirements line 2 / virtual environment | Install the updated requirements using that backend's Python. |
| 401 despite an open admin page | `ExistingCampusHubAuthentication`, line 25 | Check expiry and whether a stale tab token was supplied. Do not log the token value. |
| 403 for an admin | `CanReadActivity`, line 48 | Confirm actual stored role, active/suspended flags and `can_view_user_monitoring`; Facilities denial is intentional. |
| Marketplace gets 404 for a known audit ID | `ActivityAPIView.queryset`, line 117; `support_scope.support_activity` | The existing scope/event policy may exclude it. Do not remove the queryset guard to make it visible. |
| Unknown actor or no role | `format_activities`, line 81 | Historical actor metadata may be missing, or the actor was deleted. This is an honest limitation, not proof the target performed the action. |
| Unknown device/browser | `parse_connection`, line 43 | Stored signature is missing/unrecognized; add a tested recognition rule rather than returning raw UA. |
| Old Time/Actor/Target modal labels | template asset versions / browser cache | Hard-refresh and verify the new JS/CSS version was loaded. |
| Dates differ from a +08:00 example | existing `TIME_ZONE`, not audit IDs | Main settings currently use UTC. Both outputs respect configured timezone. |

### 8. Remaining limitations and learning exercise

Historical records without actor metadata cannot reconstruct a missing performer or that person's historical role. A resolved administrator role is the current recorded account role, not a fabricated historical snapshot. Device parsing recognizes common signatures; uncommon apps/browsers remain Unknown. API coverage added here is specifically audit reads; existing plain Django endpoints and the separate incomplete login scaffold were not converted wholesale. No Flutter Activity Details screen was added by this web/DRF task. The response is not a guarantee that every feature in the entire system has been tested.

Safe practice: add one **parser test first** for a recognizable Firefox or Edge agent in `test_browser_signatures_without_unjustified_windows_version`. Run only that test. If a new recognized signature is needed, update `parse_connection`, run the test again, and check that an unrelated/empty agent still returns Unknown. Never edit production audit rows to create practice examples.

```powershell
venv\Scripts\python.exe manage.py test accounts.test_activity_api.ActivityAPITests.test_browser_signatures_without_unjustified_windows_version --keepdb --noinput
```

The input is a stored agent string; output is readable device/browser information. Your verification is the test assertion, followed by the existing privacy test confirming no raw agent reaches the frontend. This teaches changing a small shared function without duplicating it in JavaScript or weakening scope checks.

## Current User Monitoring implementation (October 10, 2026)

This section supersedes older monitoring labels and session-count descriptions below. The existing page, account tables, audit table and routes are reused. Global authentication/security monitoring remains Super Admin-only. Marketplace Admin retains the existing Program/Major-scoped marketplace activity view; granting global security data would break its established access boundary.

### 1. Cause / reason

Confirmed in the previous implementation: online rows displayed audit actions instead of presence ages; ordinary roles displayed `Standard User`; active sessions counted all unexpired admin tokens without checking recorded recent use; the activity log combined the affected account and action instead of identifying the actor/target separately; its ten-row limit had no pagination. The period control was visually attached to Peak Login Hours even though it already affected other monitoring data. Several existing badge rules also used colors outside the current brand palette.

Final audit review also confirmed that the admin order-update event lacked structured `order_id` metadata, and role-assignment events carry both a role and affected admin. The existing order event now stores its real order ID without adding another event. Admin-assignment/removal actions use the affected admin as Target; role-wide actions use the affected role. Their other legitimate context remains available in safe details.

The change separates account state, presence, authentication sessions and audit events. It does not manufacture mobile session mapping: mobile login currently returns a chat JWT, without a persistent session registry or heartbeat. A recent mobile login is only the existing five-minute presence estimate.

### 2. Exact files, current lines and nearby anchors

Line numbers are approximate and refer to this revision; search the named anchor after later edits.

| File | Line / anchor | Change in this task |
| --- | --- | --- |
| `backend/core/accounts/views.py` | 1208 `admin_user_monitoring_page` | Keep existing authentication/RBAC, source-qualified account identity and shared period. Update presence, readable roles and drawer data. |
| Same file | 1074 `order_updated` | Attach the existing order's real ID to the existing admin audit event; no change to order/payment/stock workflow. |
| Same view | 1256 `valid_sessions`; 1270 `online_refs` | Enabled-account presence; expired, stale, missing-observation and future-observation session exclusion. |
| Same view | 1338 `event_query`; 1345 `login_history` | Bound drawer history and separate recent login history, rather than treating the latest twenty mixed events as login history. |
| Same view | 1499 `ExtractHour`; 1516 `activity_page_obj` | SQL hourly aggregation; twenty-event log pages preserving filters. |
| `backend/core/accounts/monitoring.py` | 11 `monitoring_load_guard`; 47 `tracked_sessions` | Read failure becomes a 503 Retry state; reuse existing authenticated admin tab records. |
| Same helper file | 61 `recent_per_account`; 78 `safe_metadata`; 92 `event_rows` | SQL window bounds; historical metadata whitelist; batched actor/target resolution. |
| `backend/core/accounts/activity_logging.py` | 4 `_without_credentials`; 49 `metadata`; 73 `session_identifier` | Remove credential fields recursively on new log writes, attach real admin actor metadata, stop persisting raw session identifiers. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 25 `monitoring_error`; 33 `monitorPeriod`; 48 `Active Accounts` | Existing page with Retry and honest KPI subtitles; global period control moved above KPIs. |
| Same template | 116 `monitorFilters`; 154 `User Session Overview`; 228 `recent-activity-panel` | Clear Filters, Online/Offline, eye-only details, Time/Actor/Target/Action/Module/Result/Actions, log pagination. |
| `backend/static/components/js/admin_monitoring.js` | 20 `submitFilters`; 51 `chartFailure`; 165 `openDrawer` | Move inline code into a readable static file. Auto-apply GET filters, grouping, chart Retry, safe DOM details, focus trap and return. |
| `backend/static/components/css/admin_monitoring.css` | 607 account type rules; 623 status rules; 769 result rules; 1080 refinement | Navy/neutral states, gold warning surfaces, responsive error canvas, focus rings and reduced motion. |
| `backend/core/accounts/test_monitoring.py` | 19 `MonitoringRefinementTests` | Eleven regression cases against isolated test records, plus optional browser fixture export. |
| `backend/core/accounts/tests.py` | 1705 monitoring tests; 1949 chart accessibility assertions | Update obsolete label/inline-script expectations without removing count, scope or grouping checks. |
| `docs/user-management.md` | This section | Beginner guide, debug steps, formulas, verified results and limitations. |
| `CAMPUSHUB_CONTEXT.md` | Current monitoring reference near the top | Preserve the new monitoring behavior for later development. |

### 3. Changes made

Super Admin KPIs are **Active Accounts**, **Online Now**, **Failed Login Attempts**, **Active Sessions**. The first card explains enabled accounts; the session card explains currently authenticated sessions and its tracking coverage. No failed attempts gets an explicit quiet empty message. The online card uses **Last Seen** with `Active now`, `Just now` or `3 min ago`, rather than an audit action.

The main table is **User Session Overview**; its Status is Online/Offline. Account enabled/disabled status appears separately in Account Info. Normal-role aliases display **User** on this page only, without altering stored roles or permission grants. Existing administrator names are preserved. The existing drawer shows account information, recent login history, recent activity and legitimate stored session timestamps; it has no edit/deactivate/recovery actions. Details and session data never include token keys or session identifiers.

The bottom log now has separate **Actor**, **Target**, **Action**. For example, an existing `ROLE_DEACTIVATED` event with `actor_admin_id` and `role_id` shows the recorded admin, affected role and `Role Deactivated`. Target names are resolved from existing entities in batched queries. Missing actor metadata on a management event remains Unknown; an unknown target is a dash. A failed login identifier is an attempted identity, not proof that the named account owner performed the attempt. Authentication results retain only actual Success/Failed values.

### 4. How it works: functions, inputs, outputs and data flow

`admin_user_monitoring_page(request)` receives authenticated GET parameters. `build_account_rows(actor)` supplies existing accounts already scoped for that actor. `support_activity(queryset, actor)` supplies only permitted audit events. The view builds period totals and chart series, applies table filters, paginates and renders the existing template with JSON produced by Django `json_script`. `admin_monitoring.js` reads that JSON and uses `textContent` to display details; it does not render metadata as HTML or make mutation requests.

- **Enabled accounts:** existing records where `is_active` is true and `is_suspended` is false. Deleted records cannot enter the queryset.
- **Admin presence:** latest last-seen time from a usable recorded tab session, within five minutes and not in the future.
- **Mobile presence:** latest successful `login_success`/`logout` event within five minutes; a latest logout or disabled account excludes presence. No heartbeat is inferred from unrelated audit actions.
- **Tracked admin sessions:** `tracked_sessions(now, admin_ids)` returns existing nonempty-key tokens for enabled accounts, created by now, expiring after now, with last seen between now minus twelve hours and now. Twelve hours is the existing ordinary admin token lifetime, used as this metric's stale-use boundary. Remembered tokens can remain usable for login after that interval but are not counted as currently observed sessions until used again. No auth expiry or revocation behavior changes.
- **Period counts:** successful login and failed login audit records use their actual result/type and timestamps. Daily/weekly/monthly totals use the existing date truncation; `ExtractHour` plus `Count` computes twenty-four hourly counts in the current timezone. Empty buckets are genuine zeros. Peak and trend use the same range.
- **Tables:** ten account rows per page; twenty activity records per page. `recent_per_account(queryset, limit, partition)` uses SQL `RowNumber` to fetch at most twenty recent events/logins per visible account, or ten session summaries per visible admin. The account deep link intentionally retains all-time, twenty-event paginated drawer history; the bottom log and charts retain the selected period.
- **Audit safety:** `_without_credentials(metadata)` strips password/token/secret/session/authorization/code fields recursively before new writes. `safe_metadata(value)` also whitelists data from historical rows before activity-detail serialization. Existing audit rows are not duplicated or bulk-rewritten. The logger's old session argument remains callable but is deliberately not saved.

Annotated example:

```python
sessions = tracked_sessions(now, [admin.pk])  # Existing auth records, not fake counters.
current = sessions.count()                  # Count only rows meeting the documented rule.
label = presence_age(last_seen, now)        # Formats a timestamp; never examines action text.
```

An enabled account can be Offline and still count toward Active Accounts. A remembered tab can be unexpired while excluded from current observed sessions. A login event can be historical while its account is currently Offline. These are separate facts.

### 5. Backend / API behavior

Keep `/admin-user-monitoring/` and its existing permission checks. This remains a Django-rendered GET page; no new REST endpoint or recovery operation is added. `period=today|last7|last30|custom`, `date_from` and `date_to` share one global range, bounded by existing date handling. `q`, `type`, `role`, `status`, `activity`, `page` and `activity_page` apply on the server. Chart grouping only selects already-computed series in the browser; it does not change the global period. Clear Filters opens the existing base route. Source-qualified `account_ref=mobile:12` cannot accidentally match `admin:12`, and inaccessible references remain 404.

Marketplace Admin keeps scoped marketplace KPIs/charts and no login history, IP/device details or admin sessions. Its role does not silently gain global security access because a page label changed. Existing logging callers for authentication, account changes, product/inventory/order events and role changes remain in use; this task does not add parallel event writes.

### 6. Database / migration impact

No new models, fields or migrations. Reuse `campushub_account_activity`, `campushub_admin_tab_token`, existing accounts and entity models. New audit metadata is safer and carries an actor where the request has a real authenticated admin. Historical rows remain stored as before but their details are filtered before browser serialization. No sample data or live users were created for this work.

### 7. Verification performed and manual checks

**Run results:** 89 Django tests passed across monitoring, User Management, marketplace support and Roles & Permissions. Another 38 account-recovery/code-flow tests passed to verify the shared audit logger, with mocked delivery and exit code 0: **127 regression tests passed across these runs**. After adding the zero-failed-attempt subtitle, all eleven focused monitoring tests passed again, exit code 0. `manage.py check` passed, `makemigrations --check --dry-run` reported no changes, and `node --check` passed. Real headless Chrome checked 1920, 1440, 1024, 768, 375 and 320px, plus missing Chart.js and server error fixtures. All passed without page overflow or JavaScript errors. Detail opening, Escape, focus trap/return, grouping, global-period form submission and loading were exercised. Browser submissions were intercepted; fixtures were rendered from isolated test database records.

An early regression expectation still looked for inline JavaScript; it was updated because the script moved to a static file. A new period test initially searched the entire page, including intentionally all-time drawer JSON; it now checks the period-bound log records. Missing Chart.js exposed a default-canvas phone-width overflow; `max-width: 100%` corrected it and both error states passed the rerun. After the final order-target/admin-assignment metadata refinement, all 25 focused monitoring/marketplace support tests passed again, exit code 0; Django system and migration checks also passed again.

Manual steps:

1. Sign in as Super Admin, open User Monitoring and check the four KPI labels and real counts. An enabled student/guest should display User, an administrator its stored admin role.
2. Change Monitoring Period to Today or Last 30 Days. For Custom, edit From/To. Confirm successful login trend, failed-attempt count, peak hours and bottom log share that period. Change trend grouping and confirm no new global range is selected.
3. On a test account, perform one correct and one incorrect login. Refresh Monitoring: only the correct login contributes to the trend/peak, and the failed attempt contributes to the failure KPI/log. Avoid repeated failed attempts on a live account.
4. Check Online Users Last Seen has a presence age, while the main table still shows recent audit activity. Disable a disposable test account through existing Users controls and verify it is not counted Online or Enabled.
5. Open both eye buttons. Account Info separates enabled status from presence. Activity Details separates actor and target. Tab should remain in the open panel; Escape closes it and restores focus. No passwords, codes or session/token keys should appear in JSON or details.
6. Use search/type/role/status/activity/date filters, then Clear Filters. Check both paginations retain the selected values. The account-specific View All Activity link retains its all-time drawer history.
7. On a disposable role in the test database, deactivate it through existing controls. Confirm the actual admin is Actor and that role is Target. Never use the final Super Admin role for this exercise.
8. Sign in as Marketplace Admin: verify exact Program/Major scope and absent global security/session details. Test an unrelated account deep link and expect 404.

Evidence: `scratch/monitoring-tests-verified.log`, `scratch/monitoring-tests-focused.log`, `scratch/monitoring-recovery-regressions.log`, `scratch/monitoring-audit-final.log`, and `scratch/monitoring-review/check-ui.cjs`. The browser fixture files and screenshots are verification artifacts, not application data.

### 8. Remaining limitations and debugging guide

- Mobile JWT issuance does not record durable sessions or authenticated heartbeats. Mobile sessions and untracked legacy Django cookie sessions cannot be added to the session KPI accurately. The displayed count explicitly covers tracked admin tab sessions only. This task does not introduce a duplicate tracking table.
- Online status updates on a fresh page request. It is not a continuously pushed presence feed. The admin middleware updates last seen at its existing interval.
- Historical management events without actor/target metadata cannot be reliably reconstructed. Show Unknown/dash rather than parsing a free-text description into an invented identity.
- The existing `build_account_rows` still loads the scoped account catalog before Python filtering/pagination. Serialized tables/history are bounded and entity resolution is batched, but very large account catalogs may need a separate database-pagination improvement later.
- The read-error guard applies after existing authentication/authorization. If the whole database is unavailable before authentication resolves, the site's existing global error handling still applies.

For a surprising count, check the stored account flags, exact source-qualified reference and selected timezone/date range first. For stale admin sessions, check recorded last-seen/expiry times without exposing token keys. A zero failure count means no matching failed events; it does not mean audit recording can be assumed healthy. For chart Retry, inspect Network for the existing Chart.js CDN and reload. For blank activity details, check whether the expected safe metadata key was actually recorded; do not expose the entire raw metadata object to work around the whitelist.

**Safe practice exercise:** in the test database only, add an assertion to `test_presence_age_is_presence_not_audit_action` that a two-minute-old timestamp formats as `2 min ago`. Run `venv/Scripts/python.exe manage.py test accounts.test_monitoring --noinput` from `backend/core` and verify all eleven tests pass. Then explain why a two-minute-old failed login does not prove the account is online. This teaches the difference between formatting a timestamp and validating authenticated presence without editing live records.

## Current recovery assistance: read and guide only (October 10, 2026)

The latest request supersedes admin code sending described in earlier notes. In Users, eligible normal-user three-dot menus open **Assist Account Recovery** with identity, applicable Program/Major, masked Email/SMS, verification labels and one **Close** button. There is no submit form, send/resend/code-sent state, temporary password, emergency reset or admin-side verification.

`build_account_rows(actor)` in `backend/core/accounts/user_management.py:293` supplies the scoped row and display fields (`can_assist_recovery` at 339). `mask_recovery_phone` at 283 returns a masked contact, such as `09*****863`; the existing `mask_email` hides the email local part. `support_scope.can_view_recovery_info` at 58 checks actor grant, stored admin-target classification and the exact Program/Major boundary using loaded keys, without N+1 reads. `admin_users.js` at 145 displays these values as safe DOM text and returns focus to the three-dot button on dismissal. The template modal begins at 218; its single footer Close button replaces the old form.

**Real-data limit:** both account models have `contact_number` and `email_verified`, but no SMS verification field/provider exists, and the current mobile recovery dialog is email-only. SMS is therefore masked and Not Verified with a not-configured explanation. Never mark SMS Verified merely because a phone number exists. A verified email gets owner-mobile guidance. No verified method gets the warning; Marketplace also gets the Super Admin referral. Super has the same information modal for ordinary users without the Marketplace referral. Missing email still permits viewing this honest warning. All administrator targets and Facilities actors remain excluded.

Data flow: scoped DB records -> server authorization/masking -> existing Users JSON -> read-only modal -> owner requests/verifies/completes recovery on their own device through existing APIs. Admin opening/closing creates no code, mail or recovery audit. The server retires all admin `assist_recovery`, `reset_password` and `verify_email` aliases with 403 (`password_support.py:33`), and the shared service rejects `assisted=True` before writes (`recovery_codes.py:66`). Other actions and owner recovery remain. Mobile line 213 removes the obsolete admin-sent-code instruction only. No schema or production record changes.

For the exact files/lines, annotated example, test results, debugging and safe exercise, see [the current support guide](marketplace-admin-support.md#current-implementation-information-only-recovery-assistance-october-10-2026).

Quick safe practice: modify only the modal's static guidance sentence in a temporary branch, refresh and open it, close with keyboard Escape and confirm focus returns to the row action. Verify zero recovery requests in Network, then restore the sentence. This teaches the difference between presentation and a backend action without touching user credentials.

Verification: 204 Django regression tests passed; 8 focused tests passed after the final responsive-modal template change; 10 Chrome scenarios passed at desktop/tablet/mobile widths; 13 Flutter recovery/login tests passed. Django system/migration checks and JS syntax passed. Mail was mocked; no live inbox/SMS delivery is claimed. Browser screenshots verified the short-screen modal body scroll with visible Close. The earlier missing legacy import and floating-menu focus bug were corrected and the final checks passed; see the full guide for logs and reproduction commands.

Historical notes below explain previous versions; admin sending is now retired. Existing SMTP fixes continue to serve owner email recovery.


## Current recovery transport fix: Gmail SMTP (October 10, 2026)

Confirmed: a hidden `name="action"` input shadows `form.action` in Chrome. The old recovery fetch used that input instead of the endpoint URL, producing HTML and the reported generic error. The submit listener now uses `getAttribute('action')`, keeps the rendered tab token, and copies fresh CSRF into both posted body and header. `initiate_reset` returns JSON for AJAX eligibility denial while preserving 403 and all role/scope/CSRF checks.

Data flow: form target/action/purpose -> authenticated existing POST -> guarded `send_code` -> canonical Gmail mail service -> existing masked JSON success or honest mail failure. Existing Gmail SMTP connection/authentication succeeded; no tool email was sent. SMTP now has a 15-second operation timeout, mutually exclusive TLS/SSL and acceptance verification. No credentials, user records, schema or permission grants were changed.

See [the complete current fix report](marketplace-admin-support.md#current-fix-assisted-recovery-request-and-gmail-smtp-october-10-2026) for exact files/current lines/anchors, function inputs/outputs, actual tests, debugging and remaining delivery checks. Safe practice: reproduce the `action` naming collision in a scratch form, compare the attribute and property in Chrome without sending a request, then run the mocked transport test module. To test the app, restart/reload Django, Ctrl+F5 Users, and send through an eligible Student/Guest recovery action; keep administrator targets excluded.


## Current policy: assisted recovery excludes administrators (October 10, 2026)

Confirmed cause: Super Admin's old recovery check returned before target classification. The new `support_scope.is_administrator_account(source, account)` uses stored roles, types, flags and actual admin authority. `can_reset_account(actor, source, account)` rejects administrator targets first; existing Program/Major checks still restrict Marketplace actors and Facilities actors remain OFF. `build_account_rows(actor)` returns guarded visibility plus administrator Recovery Method using one batched authority query. No users, assignments, permissions or schema were changed.

The three-dot menu remains. Ordinary users retain eligible assistance. Administrator User Details shows Email Verification Status and Recovery Method: Verified Email. Marketplace role/scope, Facilities role and Super activity/non-sensitive edit actions remain contextual. Super rows have no role, seller, scope or deactivation menu action; existing final-Super server protection remains.

Web login now links to `/account/recovery/`: owner email/action -> six-digit proof -> username or private new/confirm password. `account_recovery.js` sends inputs to the existing APIs; `send_code`, `verify_code`, `confirm_password` produce the existing masked response, username/one-use proof and password-completion result. The new owner form adds no duplicate recovery business logic. Example: Super Admin viewing an administrator gets `is_administrator=True` and `can_reset=False`; the owner can still recover using genuine email proof.

See [the complete current policy report](marketplace-admin-support.md#current-policy-normal-user-assistance-and-administrator-self-service-october-10-2026) for exact files/current lines/anchors, eight-part change report, backend guards, actual verification, debugging and remaining SMTP/device/JWT limitations. Safe learning exercise: create a new custom-role target inside the isolated eligibility test, assert POST 403 and no code row, then run only that test module. Do not modify production users or loosen a permission to make a test pass. If an action is hidden, inspect stored identity/scope and email state before changing the template.


## Current update: code-only account recovery (October 10, 2026)

One three-dot Actions trigger is retained. `initiate_reset` sends a six-digit code through `recovery_codes.send_code`; the admin stays in Users and sees Verification Code Sent, masked email, Resend and Done. The email contains no owner link. Existing permissions, Program/Major scope, seller access, account safety and table layout are retained.

The owner uses Flutter `AccountRecoveryDialog` -> `AuthService` -> existing password-reset API routes -> shared Django service. `verify_code` consumes a successful code immediately. Username recovery reveals the real username; password recovery returns a short-lived owner completion proof used once by `confirm_password`. Initial email verification is separate and reuses sign-up's saved email. `SessionService` saves only real verified profile state, not codes/proofs.

No new schema/migration or permission grants. See [the complete recovery guide](marketplace-admin-support.md#current-implementation-code-only-recovery-in-the-app-october-10-2026) for every changed file/current line/anchor, function inputs/outputs, data flow, tests, debugging and remaining device/session limitations. Safe practice: trace the three code-row states in the mocked single-use test without printing secrets; then make a scratch supporting-text edit and verify the 320px Flutter input test. Deploy backend and rebuilt mobile together because completion now uses proof rather than repeating a consumed code.

## Latest update: Marketplace Admin account support (October 9, 2026)

Marketplace Admin now uses this same Users page for ordinary accounts within its assigned Program/Major, with View, Reset Password and permitted Activity actions. User Monitoring has a scoped marketplace view; Super Admin retains global monitoring and exclusive Roles & Permissions access. Reset confirmation sends owner-controlled email instructions using the existing mobile code flow or a Django reset link. Facilities scope, existing assignments and history remain intact. Migration accounts.0027 added four role and four account grants, with no existing grants removed. See [Marketplace Admin support guide](marketplace-admin-support.md) for every changed file/current line, functions/inputs/outputs, data flow, security boundaries, actual tests, troubleshooting and a safe practice exercise. This supersedes the earlier Super Admin-only monitoring and administrator-entered reset descriptions below.


Updated October 9, 2026. This guide records the implementation for the final CampusHub User Management request. Application records were inspected before changing the code; examples in this guide are explanations, not seeded production users.

## Latest Roles & Permissions update (October 9, 2026)

Roles now shares the Products/Users page layout, with seven columns, real admin counts and modification times, protected Super Admin/base views, five permission groups and staged information/configuration/assignment. Existing RBAC, ordinary user capabilities and academic rules are preserved. Applied accounts.0026; actual integrity checks preserved assignments and existing grants. See [Roles & Permissions implementation and learning guide](roles-permissions.md) for exact files/current lines, functions/input-output/data flow, audit events, verification, troubleshooting, remaining policies and a safe practice exercise.

## Latest update: shared Products / Users page layout (October 9, 2026)

### Cause / reason

Confirmed in the templates: Add Product was inside Products List, Users had no list heading, and each page used separate spacing rules. Browser checks also confirmed legacy Products CSS overrode button typography/table padding, added 8px of content padding at tablet widths, and pushed the header profile beyond a 375px viewport. This change standardizes presentation while preserving existing form handlers, filters, queries and permissions.

### Exact files changed, current lines and anchors

| File | Line / nearby anchor | Added, moved or removed |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 25 `admin-module-shell`; 34 `admin-module-page`; 36 `admin-page-intro`; 78 `productsListSection` | Add the specified page description; move the single `addProductButton` above the KPIs; replace list subtitle; opt existing sections into shared layout classes. Preserve IDs/data attributes and form/table contents. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 15 `admin-module-shell`; 24 `admin-page-intro`; 72 `usersListHeading`; 159 `admin-list-footer` | Keep the requested page description and permission-controlled Add Admin; add Users List and its subtitle; share the KPI/list layout. Load Montserrat weight 400 for normal supporting text. |
| `backend/static/components/css/admin_layout.css` | 2460 `Products / Users opt into one page rhythm`; 2489 `admin-page-action`; 2550 `admin-list-heading`; 2603 `admin-module-shell` | One scoped spacing/button/section/grid system, shared mobile header guards and responsive breakpoints. Other modules do not opt in. |
| `backend/static/components/css/admin_products.css` | 4984 `The relocated list action` | Hide the new page description/action while the existing Products List is hidden for form/loading/details views. |
| `backend/static/components/css/admin_users.css` | 915 mobile media rule | Remove five duplicated mobile header rules now supplied by the shared layout stylesheet; retain Users-specific drawer/table/navigation rules. |
| `scratch/admin-module-layout/check.cjs` | browser cases / `metrics` | Review actual Django test-rendered pages in Chrome at six widths, intercept writes, compare spacing and exercise existing primary actions. |
| `docs/user-management.md`, `docs/products-list-inventory.md`, `CAMPUSHUB_CONTEXT.md` | latest layout notes | Explain behavior, current files/lines, data flow, debugging and safe practice. |

### Changes made

Both pages now follow **title/breadcrumb → description and action → four KPIs → list heading/subtitle → filters → table → pagination**. Products uses `Manage and monitor marketplace product listings, approvals, inventory availability, and listing status.` Its list subtitle is `Review, filter, and manage marketplace product listings.` Users keeps its longer page description and gains `Users List` plus `Review, filter, and manage CampusHub user accounts.` No duplicate page title or extra description card is added.

Shared layout values: 24px page padding on desktop, 14px on phones; 20px description-to-KPI and KPI-to-list gaps; 16px KPI gaps; 12px list radius; 18px list titles; normal 13px descriptions; 16px/20px section-header padding; 20px filter padding (14px mobile); 16px by 12px filter gaps. Table and footer insets use the same shared variable. Primary actions share 44px height, 18px horizontal padding, 13px semibold Montserrat, 6px radius, navy background and gold hover. Descriptions wrap instead of being clipped.

KPI grids use four columns, two below 1200px and one below 576px. Filters use the same wide/four/two/one-column breakpoints; mobile Search and Clear Filters span the row. Small-screen actions stay aligned right below the wrapping description. Existing table columns remain intact and horizontally scroll **inside the table region**. Users retains its existing extra KPI explanatory lines, so cards can grow naturally with content; no fixed height clips those lines.

### How it works: functions, inputs/outputs and data flow

The existing Products and Users views still supply the same database-backed context to their templates. New CSS classes are presentation markers, not new data fields. The existing shared `admin_header.html` still renders title/breadcrumb; the first content row renders each literal description and existing primary action. `perms.accounts.can_manage_admin_accounts` still controls Add Admin.

The Products JavaScript obtains Add Product by **the same `addProductButton` ID**. Its existing click handler calls `resetProductForm()`, `showProductLoading(showProductForm)` and the existing form flow. `showProductForm`, `showProductLoading`, `showProductsList` and details navigation already toggle `#productsListSection.d-none`. The new Products-only CSS `:has(> #productsListSection.d-none)` reads that existing visible state to hide the relocated action, just as its old parent previously did. Returning to the list restores it. No handler, route or save operation is replaced.

For Users, `admin_users.js` still opens the same `#userEditor` modal and submits the same form. The list heading sits before `#userFilters`; all its names, IDs, academic attributes, sorting controls and pagination links remain. Product KPI buttons still carry their existing filter attributes. There is no additional API request or recalculated KPI.

Annotated example:

```css
.dashboard-content.admin-module-page {
    --admin-page-gap: 20px; /* one setting reused by intro and KPI margins */
}
```

Only opted-in pages match this selector. Changing this spacing variable affects both pages consistently without copying rules. Shared selector specificity overrides older page rules where needed; the moved Add Product uses the shared action class instead of inheriting legacy `.primary-action !important` styles. Other Product form buttons keep their original styles. Stylesheet version strings are updated so the browser requests current assets.

### Backend / API behavior and database / migration impact

No Python application code, API endpoint, database model, permission condition, filter calculation or migration changed. Search, Program/Major logic, seller access, archive/restore, pagination and KPI values use the existing implementation. No production sample rows or live account/product edits were made. Browser API data comes from the isolated Django test fixtures, with all form writes intercepted.

### Tests performed and manual verification

- **40 Django tests passed:** `manage.py test accounts.test_user_management modules.marketplace.test_program_inventory.ProgramInventoryTests --noinput --verbosity 1`. They cover existing account validation/permissions/query behavior and Product academic/filter/archive/inventory behavior. Log: `scratch/user-management/module-layout-tests.log`.
- **Two focused fixture-rendering tests passed again after the final template changes:** the existing catalog exporter and Users query-count/export test. They produce actual template output from an isolated database for browser review.
- **12 Chrome cases passed:** both pages at 1920, 1440, 1024, 768, 375 and 320px. `node scratch/admin-module-layout/check.cjs` compares header-to-description gaps, intro/KPI/list gaps, card padding, grid spacing, list/filter/table/footer insets and action dimensions. It checks four KPIs, nine columns, unclipped descriptions, right-aligned 44px actions, navy/gold hover, no page overflow and existing form open/back behavior. Measurements: `scratch/admin-module-layout/metrics.json`. Desktop/phone screenshots were also visually inspected.
- **Existing catalog behavior check passed:** `node scratch/inventory-monitor/check-catalog-behavior.cjs` exercises search debounce/combined filters/reset, archive/restore handlers, preserved totals, SKU/history, API failure and auto GET behavior against isolated fixture/API responses.
- **Django system check, both template compilations, Node syntax check and targeted `git diff --check` passed.** No migration or production write was needed.

Manual steps: reload Products and Users; confirm the exact descriptions and list headings, and that Add Product is absent from Products List. Open Add Product and return using the existing back action; confirm the page-level action disappears/reappears. Open Add Admin as an authorized account. Change existing filters and test pagination, product archive/restore and User Details as usual. At desktop, tablet and phone widths, confirm wrapped descriptions, right-aligned primary actions and table-only horizontal scrolling. Check a Users viewer without management permission still gets no Add Admin action.

### Debugging and remaining limitations

If only one page has old spacing, first check its `admin-module-page`/`admin-module-shell` classes and stylesheet version in the response. Inspect computed CSS: older page rules with higher specificity or `!important` can defeat a shared style. Do not add global overrides to fix one component. If Add Product stops opening, check that there is exactly one `addProductButton`; its handler depends on the ID, not the removed visual class. If the action remains visible in form/details mode, inspect the existing list's `d-none` state and the Products-specific `:has` rule.

Scope is Products and Users. Inventory and other modules retain their current layouts. Existing table widths, individual KPI content/icon styling and module-specific controls are preserved, rather than redesigned. The view-state rule relies on modern CSS `:has`, verified in Chrome; an old unsupported browser would not hide the relocated action during the form view. Browser QA uses isolated fixtures and local assets, not a production authenticated end-to-end session or physical phone.

**Safe practice exercise:** use developer tools to temporarily change `--admin-page-gap` from `20px` to `24px` on each page. Confirm both the intro-to-KPI and KPI-to-list gaps change by 4px, while filters still work. Reload to undo the experiment. Read `metrics.json` in `scratch/admin-module-layout/` to compare the measured gaps at each width before proposing a permanent CSS change. Never edit live data to test layout.

## Previous update: Users supporting description (October 9, 2026)

- **Cause / reason:** the previous request removed the introduction. The new request adds a more complete supporting description directly below the existing Users title/breadcrumb, without restoring a second title.
- **Exact files changed:** `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html:24`, anchor `users-page-intro`; description at line 25. This guide's `Users supporting description` section records the change.
- **Old description:** none immediately before this update. The earlier removed text was `Manage CampusHub accounts, academic scope, and system access.`
- **New description:** `Manage and monitor CampusHub user accounts, roles, permissions, academic program assignments, seller access, account status, and overall system access.`
- **Changes made / how it works:** the template renders a plain paragraph as the first content below the shared header. It reuses the existing `.users-page-intro p` styling in `backend/static/components/css/admin_users.css:33`: 13px secondary text with the existing typography. The same intro row keeps the existing permission-controlled Add Admin button on the right; Bootstrap's `flex-shrink-0` keeps the button readable alongside wrapping text. The existing mobile rule at line 916 stacks this row on narrow screens. No new CSS or second heading is needed.
- **Functions and data flow:** the existing Users view supplies context and permissions to Django's template renderer. The description is static text; `perms.accounts.can_manage_admin_accounts` still controls only Add Admin. No new function, input field, output data structure or API request was introduced. KPI, filter and table markup stay unchanged.
- **Backend / API and database impact:** no query, validation, permission, schema, migration or saved-record changes.
- **Tests performed:** `manage.py check` reported no issues; Django template loading compiled the page successfully; targeted `git diff --check` passed. No new test or browser run for this supporting-text change.
- **Manual verification / limitations:** reload Users and confirm the exact paragraph appears below the title/breadcrumb and above the KPIs. At a phone width, confirm the text wraps naturally and Add Admin stacks beneath it. Without management permission, the description should still appear but Add Admin should not. Browser verification remains a manual step.

**Debugging:** if the sentence is absent, confirm the running process uses this template and reload the response. Inspect the existing `.users-page-intro p` and mobile rules if sizing or wrapping looks wrong; do not modify the shared header or KPI styles to fix this paragraph.

**Safe practice exercise:** find the paragraph at line 25 and trace its selector to `admin_users.css:33`. Explain which rule controls font size and which mobile rule changes row direction. Verify using browser developer tools at desktop and phone widths before attempting a styling edit; keep the live account data untouched.

## Previous update: remove the page introduction (October 9, 2026)

- **Cause / reason:** the requested extra `Users` heading and account-management subtitle were rendered together above the KPI cards. Remove this introduction from the page body.
- **Exact files changed:** `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html:32`, anchor `users-page-intro`; this guide, anchor `remove the page introduction`.
- **Changes made:** delete the heading/subtitle markup. Keep Add Admin aligned to the right with Bootstrap's existing `justify-content-end` utility. Wrap its entire row in the existing permission condition so viewers without Add Admin access do not get an empty introduction row. The navigation header and browser title still identify the page.
- **How it works / data flow:** Django receives the existing page context and `perms` object. The template checks `perms.accounts.can_manage_admin_accounts`; permitted viewers receive the Add Admin button targeting the existing `#userEditor` modal. Other viewers receive neither the button nor its wrapper. No Python function, JavaScript handler or CSS rule was added; Bootstrap handles alignment.
- **Backend / API behavior:** existing account queries, role checks, modal save route and validation continue as before. This is a rendered-template change only.
- **Database / migration impact:** no fields, migrations or saved records changed.
- **Tests performed:** `manage.py check` reported no issues; Django `get_template('user_management/pages/admin_user_access_control.html')` compiled successfully. Targeted `git diff --check` passed. No new automated test was written for this small markup removal; no browser inspection was performed for it.
- **Remaining limitations / manual verification:** reload Users and confirm the extra heading/subtitle are absent, Add Admin remains on the right, and the modal still opens. For a viewer without the management permission, confirm no empty button row appears. Do not confuse the retained navigation title with the removed introduction.

**Debugging:** if the removed text remains after reload, inspect the response and confirm the running Django process uses this workspace and template. Search the exact subtitle to locate a duplicate rather than changing account data.

**Safe practice exercise:** inspect the `if` condition at line 32 and find the matching `endif`. Explain why the wrapper is inside the permission condition: otherwise it could leave empty spacing for viewers without the button. Verify your understanding by reading the rendered HTML for permitted and non-permitted test accounts; no production permission changes are needed.

## Previous update: plain Unassigned labels (October 9, 2026)

### Cause / reason

Confirmed: three Users display paths still used `Unassigned (legacy record)`: the shared Program label, the missing BTLED Major fallback, and the edit-form notice. The table also treated every non-guest, non-global account as needing a Program, including faculty without a required or recorded affiliation. This refinement changes presentation, not saved assignments.

### Exact files changed, current lines and anchors

| File | Line / nearby anchor | Change |
|---|---|---|
| `backend/core/accounts/academic.py` | 11 `academic_labels` | Missing Program label becomes `Unassigned`; existing linked Program/Major labels remain intact. |
| `backend/core/accounts/user_management.py` | 250 `account_detail_fields`; 262 Major fallback; 292 `meaningful` | Missing applicable Major becomes `Unassigned`; table applicability matches the role-aware drawer. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 195 `legacyAcademicNotice` | Remove the parenthetical from the existing notice; Program choices still come from real master records. |
| `backend/core/accounts/test_user_management.py` | 71 legacy Student; 78 applicability matrix; 286 missing Major | Update label expectations and verify missing Student/Marketplace Program, dash roles, hidden Major and preserved faculty affiliation. |
| `docs/user-management.md`, `CAMPUSHUB_CONTEXT.md` | latest Unassigned update | Explain current behavior, data flow, verification and debugging. |

### Changes made and how it works

1. `academic_labels(program, major)` accepts the existing linked model objects and returns display strings plus their IDs. With no Program it returns `program: "Unassigned"`, but the ID remains `None`. This shared helper also supplies some product/mobile labels; its fallback wording is shared, not a new Program value.
2. `build_account_rows(current_user)` reads existing accounts with their Program/Major relationships. Students and Marketplace Admins need an academic label even when the relationship is missing. Other non-guest accounts display their recorded affiliation when present. Super Admin, Facilities Admin and Guest retain `—`; optional affiliation with no saved Program also uses `—`.
3. `account_detail_fields(row)` returns the existing drawer descriptors. An applicable missing Program becomes `Program: Unassigned`. Major is added only when Program is BTLED, so there is no Major row for a missing Program. A BTLED record with no valid linked Major shows `Major: Unassigned`.
4. The table renders `program_major`; the existing JavaScript renders `detail_fields` safely as text. No new frontend calculation or API request is needed.

Annotated example: a Student whose `department_id` is `None` produces `program_major = "Unassigned"` and a Program descriptor. Changing the **display string** does not save a Department, create a dropdown option or make this account valid for new registration.

### Backend / API behavior and database / migration impact

Existing validation is reused without weakening it. `resolve_account_academic` (accounts/academic.py:41) requires a Program for a new Student or Marketplace Admin, rejects non-master IDs, and requires a linked Major for BTLED. The mobile profile-completion endpoint has the same required affiliation checks. BSIT/BFPT do not accept a BTLED Major. The existing exception lets an already incomplete Student be edited without guessing an affiliation; it does not allow a new Student or Marketplace Admin to omit it.

`academic_options` continues returning the existing BSIT, BFPT, BTLED and IA/HE/ICT master records. No `Unassigned` option, missing-data filter, endpoint, database field or migration was added. No production account was edited. Existing API users of the shared label helper receive the shorter fallback text; IDs and authorization remain unchanged.

### Verification and manual test steps

Ran `manage.py test accounts.test_user_management accounts.tests.AdminUserManagementTests accounts.tests.UserMonitoringTests --noinput --verbosity 1` with the existing Django virtual environment: **44 tests passed**, and Django's system check reported no issues. Results are in `scratch/user-management/unassigned-tests.log`. The tests cover the new applicability matrix, missing Program/Major labels, legacy Student editing, Marketplace Program/BTLED Major validation, new Student profile completion, master-data options and existing role/history authorization. The tests use isolated database records, not live sample users. Targeted `git diff --check` also passed. No new browser session or physical-phone test was performed for this text refinement; the following steps are manual checks to perform, not reported browser results.

1. Open Users and view an existing Student missing Program: table and drawer say `Unassigned`; the drawer has no Major row.
2. View a Marketplace Admin missing Program: the same label appears. Saving without a valid Program must still fail.
3. Check Super Admin, Facilities Admin and Guest: table Program/Major is `—`, and the drawer hides academic fields.
4. Check BSIT, BFPT, BTLED-IA, BTLED-HE and BTLED-ICT accounts: existing assigned labels remain unchanged. Check a BTLED account missing Major: the drawer says `Major: Unassigned`.
5. Add a Marketplace Admin without Program, then with BTLED but no Major: both must be rejected. Complete a new Student profile without Program: it must be rejected too. Open Program dropdowns: no `Unassigned` option should exist.

### Debugging, limitations and safe practice

If old wording remains on the Users page, restart the Django process and reload the page, then inspect the actual response for `legacyAcademicNotice` and `usersData`. Program text originates in `academic_labels`; missing Major text originates in `account_detail_fields`. Do not replace null IDs with the string `Unassigned`: that would corrupt the distinction between a label and a saved relationship.

Existing incomplete accounts are intentionally not auto-assigned. Optional faculty affiliation stays visible when recorded. This task does not rewrite independent legacy-label fallbacks in the Products JavaScript or earlier unrelated feature guides.

Practice safely: read `test_missing_program_display_depends_on_academic_applicability`, then add a separate assertion for an existing BFPT Student using isolated test data. Verify that its table value is `BFPT` and its drawer has Program but no Major. Run that test before changing application code; never experiment by editing a real user's Program in the database.

## Previous update: role-aware User Details and complete activity history

This section is the implementation report for the subsequent User Details request. It supersedes earlier drawer examples that included academic/seller dash rows for administrators. The fixed nine-column Users table still uses dashes for inapplicable values.

### Cause / reason

Confirmed: `admin_users.js` previously appended Program, Major and Seller Access unconditionally. The existing five-event query did not detect older history, and User Monitoring had no exact-account deep link or pagination beyond its first twenty drawer events. No profile/status model needed replacing.

### Exact files changed, current lines and anchors

| File | Current anchor | Added / changed / removed |
|---|---|---|
| `backend/core/accounts/user_management.py` | 250 `account_detail_fields`; 302 `detail_fields`; 306 `get_user_management_context`; 344 window query | Build only applicable extra fields from existing normalized data; fetch six events to display five and detect older history; permission-checked exact-account activity URL. |
| `backend/static/components/js/admin_users.js` | 86 `.view-user`; 93 `user.detail_fields`; 96 empty activity; 98 `viewAllUserActivity` | Removed unconditional Program/Major/Seller rows; render server-selected extras with safe text nodes; exact empty message; reset link visibility/href for every selected account. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 13 CSS version; 214 activity link; 226 JS version | Added View All Activity within the existing drawer; changed cache versions. No table-column changes. |
| `backend/static/components/css/admin_users.css` | 913 `.users-activity-link` | Compact navy link with a 44px target; explicitly hide it when inapplicable. |
| `backend/core/accounts/views.py` | 1727 `admin_user_monitoring_page`; 1760 exact account validation; 1858 history pagination; 1887 current event metadata | Reuse the existing monitoring route; reject unknown references, filter the exact account, paginate twenty all-time events and keep current overview metadata on older pages. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 15 cache version; 111 hidden account filter; 296 history navigation; 415 `selectedAccount` | Preserve the account filter, show Previous/Next, auto-open that account's Activity Log tab and focus its tab button. |
| `backend/static/components/css/admin_monitoring.css` | 684 scoped history navigation rule | Only the new drawer pagination links get a minimum 44px target. Other monitoring styles are retained. |
| `backend/core/accounts/test_user_management.py` | 233 role matrix; 263 role changes; 277 paginated history; `test_activity_link_respects_existing_monitoring_permission` | Four added isolated tests cover the requested role cases, legacy values, newest-first history, exact account isolation, page two and monitoring authorization. |
| `scratch/user-management/check.cjs` | role/history browser cases | Extend reversible browser QA to inspect actual drawer labels, empty states, five-event preview, deep links and history tabs on desktop/phone widths. |
| `docs/user-management.md`, `CAMPUSHUB_CONTEXT.md` | latest update sections | Record behavior, functions/data flow, tests, debugging, limitations and learning exercise. |

### Changes made: role-specific fields

All drawers keep **Full Name, Username / School ID, Email, Account Type, Role, Account Status, Created Date and Last Login**. Guest uses the more appropriate Username label. These common fields remain visible even when an old record lacks a value. The profile header, existing drawer layout, table, filters, pagination, Add Admin and Edit User remain in place.

| Selected account | Extra drawer information | Completely hidden |
|---|---|---|
| Super Admin | System Scope: All Modules | Program, Major, Seller Access, Facility Scope |
| Facilities Admin | Facility Scope: All Facilities | Program, Major, Seller Access, System Scope |
| Marketplace Admin, BSIT/BFPT | Program | Major, Seller Access, both global scopes |
| Marketplace Admin, BTLED | Program: BTLED; full linked Major name | Seller Access, both global scopes |
| Student, BSIT/BFPT | Program; actual Seller Access, including Not Applied | Major, both global scopes |
| Student, BTLED | Program; full linked Major; actual Seller Access | Both global scopes |
| Faculty/normal mobile user | Recorded academic affiliation when applicable; actual seller access | Inapplicable Major/global scopes |
| Guest/External without an application | Common fields and activity only | Academic/global scopes and Seller Access |
| Guest/External with a real application | Actual Seller Access and Application Status | Academic/global scopes |

The current seller endpoint requires a ten-digit Student ID and course/section, but does not define a general guest eligibility policy. Accordingly, an existing real application is the only evidence used to show guest seller participation. This update does not create a new guest seller entitlement or remove historical applications.

BTLED alone makes Major applicable. If a legacy BTLED record lacks a valid linked major, show **Unassigned** rather than a fabricated name or dash. A new invalid BTLED assignment still fails the existing backend validation. Students retain their affiliation. Full Major names come from ProgramMajor; the main table retains compact BTLED-HE/IA/ICT labels. Admin seller access is never shown. Application Status appears only for a real application; Approval Date appears only when it was recorded.

### How it works: functions, inputs/outputs and data flow

1. `build_account_rows(current_user)` reads the existing User/mobile account, linked Program/Major and batched seller applications. It calculates the existing status/labels as before, then passes that normalized row to `account_detail_fields(row, seller_application)`.
2. `account_detail_fields` returns a list of display descriptors such as `{"label": "Program", "value": "BFPT"}`. Date descriptors carry `format: "date"`. It performs **no additional queries or saves** and does not recalculate permissions or seller decisions.
3. `get_user_management_context` runs one bounded window query with `rank <= 6`, ordered by timestamp and primary key. Five events enter the preview; the sixth answers whether older history exists without one COUNT query per user.
4. The template passes descriptors through the existing safe `json_script`. Clicking View clears previous fields and renders the eight common rows plus applicable descriptors using `textContent`. Switching from Student to Facilities Admin therefore removes prior academic/seller rows.
5. More than five events plus authorized monitoring access adds the existing route `/admin-user-monitoring/?account_ref=mobile%3A123` (123 illustrates the reference format, not a seeded user). The existing per-tab token is retained where needed. The selected source-qualified reference is checked against accessible real accounts.
6. User Monitoring filters that exact account and opens its existing Activity Log tab. Its history reads all dates, twenty records per page; `history_page=2` requests the next page. The main chart/date controls retain their existing date range. Targeted period charts/recent logs use the selected account, while the existing global account/session KPI summaries remain global.

The drawer's activity text is exactly **No recent activity available.** when none exists. Only real AccountActivity events with nonempty activity descriptions are used; no second audit table or placeholder event exists. Equal timestamps use descending primary key for stable newest-first ordering. Activity descriptors do not include passwords, password hashes, session identifiers or bearer tokens. The authorized navigation URL may carry the existing viewer's per-tab token; do not copy it into documentation.

**Annotated example:** for an existing Facilities Admin row, `account_detail_fields(row)` returns one extra descriptor: Facility Scope → the already-computed All Facilities value. For a BFPT Marketplace Admin it returns Program → BFPT; it never appends Major → dash. This is presentation logic layered on the shared profile data, not another role/profile system.

### Backend / API behavior and database impact

No new page or API endpoint. The existing monitoring GET route accepts `account_ref` and `history_page`. Unknown references return 404. Existing monitoring permissions and its Super Admin requirement are preserved; unauthorized viewers cannot bypass them by editing a URL. Users viewers without monitoring access keep the five-event preview but do not get a broken View All link. Existing account-save POST redirects reload fresh role descriptors immediately after a successful role change.

No model changes, migration, production fixtures, account edits or historical deletion were made for this drawer update. The earlier migrations described later in this guide belong to the preceding User Management implementation.

### Tests performed

Completed verification for this refinement:

- **43 Django tests passed:** the 26 User Management regressions, existing Add/Edit Admin tests and User Monitoring tests. The initial matrix fixture's duplicate blank email error was corrected with distinct test emails; the final suite passed.
- **11 history/monitoring tests passed after the final refinement:** stable timestamp/PK ordering and page-two overview metadata were rechecked alongside the existing monitoring behavior.
- **11 Chrome cases passed:** six existing page/form/filter layouts plus role matrices on desktop and 375px phone width, five-event preview/link, and monitoring history on desktop/phone. Final history styles/focus were rechecked in both history cases. Actual screenshots were visually inspected.
- Django system check: no issues. `makemigrations --check --dry-run`: no changes detected. JavaScript syntax and targeted Git whitespace checks passed; Git printed ordinary LF/CRLF conversion notices.

Tests use isolated Django data and browser POST interception; screenshot names beginning `drawer-`, `activity`, and `history` under `scratch/user-management/` are review artifacts, not production users. Browser history fixtures verify the rendered integration; production navigation and live account writes were not used for QA. Mobile browser width was checked; Flutter was not changed by this drawer update.

### Manual tests, debugging and remaining limitations

1. Ctrl+F5 Users; open Super Admin, Facilities Admin, BFPT Marketplace Admin and BTLED-HE Marketplace Admin. Compare the exact field matrix above. The main table must still contain nine columns.
2. Open a BSIT Student, BTLED-IA Student and Guest in succession. Check that fields from the previous account disappear, linked major names are full text, and Guest without an application has no academic/seller rows.
3. In a test database, change Facilities Admin to Marketplace Admin and assign Program/Major; save and reopen details. Then change back to Facilities Admin: academic fields should clear in the saved account and disappear in the drawer.
4. Open an account with no activity: exact empty text and no View All link. With five events, show five only. With six or more, authorized Super Admin sees View All Activity.
5. Follow that link: only the selected source-qualified account is listed, its Activity Log opens, and events older than the chart's default seven-day period remain accessible in its all-time history. Use Next/Previous and confirm order, retained account filter and latest overview metadata.
6. Test a read-only viewer and an unknown reference. Unauthorized monitoring must fail; changing only the numeric ID must not confuse mobile and web accounts with equal IDs.

| Symptom | Cause / diagnostic | Safe verification |
|---|---|---|
| Old Program/Major dash rows remain | Stale JS or old server-rendered descriptors | Ctrl+F5; check the `20261009-role-aware-details` asset version and `detail_fields` in the page's non-secret JSON. |
| View All is absent | At most five real events, or viewer lacks the existing monitoring authorization | Check real event count and actor permission; do not grant permissions merely to make a link visible. |
| BTLED Major says Unassigned | The legacy linked value is missing/invalid | Assign the true linked major through Edit User; never guess a major. |
| History starts with the wrong event | Missing timestamp/PK tie-breaker or stale page | Check `order_by("-created_at", "-pk")` and `history_page`; the overview must continue using the actual latest event. |
| A test's mobile fixture fails to create | Confirmed initial fixture error: blank emails violated the mobile table's unique email constraint | Give each isolated fixture a distinct email. No production user needed editing. |

**Remaining limitations:** general Guest seller eligibility is not defined by the existing workflow; the drawer uses real applications only. Full history navigation remains restricted by the current Super Admin monitoring policy. Legacy missing affiliation stays honest. Pagination fetches twenty events per history page; it does not load an unbounded history into the browser. No live-user mutations were made during browser QA.

**Safe practice exercise:** in an isolated test, create a BFPT Marketplace Admin fixture and inspect `row["detail_fields"]` returned by the Users response. Assert that its labels equal `["Program"]`, then change the fixture to BTLED with the real HE master record and assert `["Program", "Major"]`. Run the focused test below. Keep mutations inside TestCase so Django destroys them with the test database; do not seed the production database to test presentation.

```powershell
& backend/core/venv/Scripts/python.exe backend/core/manage.py test accounts.test_user_management.FinalUserManagementTests.test_drawer_fields_follow_real_roles_and_affiliation --noinput
```

## 1. Cause / reason

Confirmed issues: the Users form treated academic scope similarly for every administrator; a rejected seller application could be labelled Suspended; seller approval replaced the existing account role with Seller; details did not show real recent audit events. The mobile profile form did not collect the Program/Major needed for a new Student. Existing Django permissions also needed an upper boundary to stop built-in Facilities and Marketplace roles receiving cross-module grants.

The current project has two existing identity stores: `accounts.User` for web accounts and `api.CampusHubUser` for mobile accounts. This implementation keeps them, uses source-qualified references such as `admin:12` and `mobile:12`, and does not introduce another authentication, role, permission or audit system.

## 2. Exact files changed and current code anchors

Paths below are relative to the project root. Line numbers identify nearby anchors and can move after later edits.

| File | Line / anchor | Change and reason |
|---|---|---|
| `backend/core/accounts/academic.py` | 41 `resolve_account_academic`; 61 `has_valid_marketplace_scope`; 76 `scope_users`; 87 `scope_products` | Shared role/affiliation validation; BTLED scope fails closed without its major. |
| `backend/core/accounts/user_management.py` | 71 `log_management_event`; 97 `seller_request_for`; 276 `build_account_rows`; 306 `get_user_management_context` | Normalized rows, true seller access, combined filters, scope-wide KPIs, permissions and five actual audit events per displayed account. |
| `backend/core/accounts/views.py` | 351 `_active_super_admin_count`; 386 `admin_users_save`; 606 `admin_users_action` | Validate creation/editing; hash passwords; safe account and seller actions; audit changes; lock final active Super Admin checks. |
| `backend/core/accounts/forms.py` | 19 `AdminUserCreationForm`; 72 `AdminUserChangeForm` | Reuse academic validation in native Django admin; protect the final active Super Admin there too. |
| `backend/core/accounts/admin.py` | 9 `CustomUserAdmin` | Include Major, synchronize permissions, audit saves and disable permanent user deletion in native admin. |
| `backend/core/accounts/role_permissions.py` | 173 `role_scope_permissions`; 182 `permissions_for_role`; 285 `set_role_permissions`; 350 `user_has_admin_access` | Limit built-in roles to their existing domain; keep custom roles and existing Django grants. |
| `backend/core/accounts/authentication.py` | 9 `RoleScopeBackend` | Extend Django ModelBackend with suspended-account checks and built-in role boundaries, including stale direct/group grants. |
| `backend/core/accounts/admin_tab_auth.py` | 36 `get_user_for_tab_token` | Reject inactive/suspended accounts for per-tab authentication. |
| `backend/core/accounts/middleware.py` | 24 suspension check | Block suspended users whose existing sessions still reference the old ModelBackend. |
| `backend/core/core/settings.py` | 83 `AUTHENTICATION_BACKENDS` | Install the boundary backend first; retain ModelBackend for old session compatibility. |
| `backend/core/api/models.py` | 303 `SellerRequest.is_suspended`; 318 `approve` | Add seller-only suspension; approval/rejection retain the account's existing role. |
| `backend/core/api/views.py` | 124 `serialize_campushub_user`; 315 `serialize_seller_request`; 588 `mobile_complete_profile`; 670 `mobile_academic_options`; 680 `seller_submit_product`; 1255 `seller_access_status` | Academic API fields/options, Student validation, separate seller access and server-side seller submission enforcement. |
| `backend/core/core/urls.py` | 155 `mobile_academic_options` | One master-data GET route; existing Users mutation routes remain at 111–114. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 34 `Add Admin`; 73 `userFilters`; 87 `users-table`; 173 `userEditor`; 212 `userViewer`; 226 `admin_users.js` | Compact nine-column table, consistent KPIs, labelled auto filters, dynamic admin form, details/actions; external JS replaces the old inline controller. |
| `backend/static/components/js/admin_users.js` | 6 `syncFilterMajor`; 25 `syncAcademic`; 47 `resetEditor`; 86 `.view-user`; 114 `.seller-access`; 128 `validatePasswordUI` | Debounce, dependent fields, safe text rendering, applicable actions, password visibility/feedback and submit state. |
| `backend/static/components/css/admin_users.css` | 45 `.users-stat-card`; 123 `.users-toolbar`; 223 `.users-table-scroll`; 584 `.offcanvas-body`; 812 modal styles; 883 component matching | Navy/gold/light styling; restrained statuses; 44px controls; responsive filters/table; scrollable forms and drawers. |
| `backend/core/modules/marketplace/services/analytics.py` | 369 `_approved_seller_ids` | Exclude seller-only suspension from active seller analytics. |
| `backend/core/modules/reports/dashboard_periods.py` | 153 seller query | Exclude suspended seller access, including legacy Seller-role accounts, from the dashboard active-seller KPI. |
| `campushub/lib/module_app/services/auth_service.dart` | 7 `AuthUser`; 118 `completeProfile`; 141 `academicOptions`; 197 `_post` | Receive/store affiliation, load real master options, send numeric IDs in JSON. |
| `campushub/lib/module_app/session/session_service.dart` | 23 `program_id` | Persist the returned affiliation with the existing session. |
| `campushub/lib/module_app/screens/profile_setup_screen.dart` | 39 academic loader; 141 `completeProfile`; 360 Student academic fields | Require a new Student's Program and linked BTLED Major; loading/error/Retry; phone dropdown sizing. |
| `backend/core/accounts/migrations/0025_global_admin_academic_scope.py` | 6 `clear_global_scope` | Clear only web global administrators' invalid academic assignments. |
| `backend/core/api/migrations/0036_seller_access_suspension.py` | 14 `AddField` | Add the missing seller suspension flag, default false. |
| `backend/core/accounts/test_user_management.py` | 23 `FinalUserManagementTests` | 26 isolated regression tests, including the four role-aware drawer additions. |
| `backend/core/accounts/tests.py` | 1367 `AdminUserManagementTests`; 2108 `UserDeactivationAndHistoryPreservationTests` | Update old labels/master fixtures to the requested behavior; retain history checks. |
| `backend/core/modules/marketplace/test_program_inventory.py` | 70 scope test; 147 seller submission test | BTLED without Major expects no access; submission fixture includes actual approved seller access. |
| `backend/core/modules/marketplace/tests.py` | 703 seller submission test | Approved application fixture keeps ownership regression valid under the server-side gate. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 160 seller suspension test; 312 `expected_routes` | Verify seller-only suspension and correct an older Inventory link assertion to the existing `view=inventory` route. |
| `campushub/test/profile_academic_test.dart` | profile academic tests | Three mocked mobile tests: payload/session, phone Student validation, API failure/Retry. |
| `scratch/user-management/check.cjs` | browser harness | Reversible browser QA using Django test-rendered HTML and intercepted POST forms. |
| `CAMPUSHUB_CONTEXT.md` | latest User Management note | Preserve accepted behavior and point to this guide. |

## 3. Changes made: requested implementation report

1. **Folders/files and lines:** see the table above. Changes are limited to User Management, shared access/affiliation functions and the integrations required for those rules.
2. **Users table:** User, Username, Account Type, Role, Program / Major, Seller Access, Account Status, Last Login, Actions. Program/Major is plain compact text; nine columns remain in a horizontal scroll region when the screen is narrow.
3. **Add User → Add Admin:** moved administrator creation to the page introduction. Modal title is Add Administrator. First/Last Name remain separate existing fields instead of guessing how to split a full name. Only the three built-in admin roles can be newly created through this form.
4. **Role-dependent fields:** Super Admin and Facilities Admin hide, disable and clear Program/Major. Marketplace Admin requires Program. BTLED requires its linked Major; BSIT/BFPT store no Major. Django repeats validation independently of JavaScript.
5. **Facilities Admin:** existing facility permissions continue to cover all facilities; no academic filtering was added to facility queries. Out-of-domain Marketplace/User Administration permissions cannot be added to this built-in role.
6. **Super Admin:** retains unrestricted modules and marketplace queries. Details show All Modules and academic dashes. The final active, unsuspended Super Admin cannot be deactivated, suspended or demoted. Custom account managers cannot modify Super Admins.
7. **Marketplace Admin:** existing scope filters constrain products, orders and reports by Program and, for BTLED, Major. Missing/invalid BTLED scope returns no rows instead of broadening access. Existing role grants can be reduced within the domain but cannot cross into Facilities/User Administration.
8. **Student affiliation:** preserved independently of permissions. Mobile profile completion now requests Program and linked BTLED Major for a new Student. Admin editing rejects invalid combinations. Guest affiliation is not applicable.
9. **Seller access:** Not Applied, Pending, Approved, Rejected and Suspended stay separate from the account role. An approved application's `is_suspended` flag stops seller access without deactivating the buyer account. Restoring access keeps the original approval date/reviewer. No application is fabricated for a user who never applied. Admin rows display a dash.
10. **Account status:** Active or Inactive / Disabled derives from `is_active` and the existing account `is_suspended` flag. Deactivation retains the account and related records, and prevents authentication. Reactivation restores login eligibility according to the existing role.
11. **Filters:** labelled Search, Account Type, Role, Account Status, Program, linked Major and Seller Access combine using AND. Select changes submit immediately; search waits 350ms. Clear Filters resets all these fields while keeping the per-tab authentication token. No Apply button.
12. **KPIs:** Total Users counts normalized accounts in the permitted scope; Active Users counts active and unsuspended accounts; Pending Sellers counts actual latest pending applications associated with those rows; Admin Accounts uses the existing web/admin classification or equivalent admin role. KPI values remain scope snapshots while table filters/pagination change.
13. **Actions:** View/Edit/overflow. Account mutation requires the existing manage permission; read-only users retain View/Activity. Deactivate/Reactivate, Reset Password and applicable seller review/suspend/restore reuse existing routes. No permanent Delete action or new user-detail page.
14. **Details:** show common account information plus only applicable academic/scope/seller fields, recorded application/approval information, and up to five real target-account activity entries. The latest drawer section above defines the conditional rows, exact empty text and complete-history navigation.
15. **Audit:** existing AccountActivity records target/source, action, timestamp, request metadata and the actor's username in the description. Save records admin creation/user update and specific changed role/program/major/account state events. Reset records the action but never the password. Seller restore action is selected from actual prior suspension, not a client-supplied label.
16. **Backend validation:** required identity fields, model length limits, email/username validation, role/account-type compatibility, password validation and hashing, linked Program/Major, final Super Admin guards, account-store consistency and permission checks.
17. **Legacy records:** existing Student records with unknown affiliation may remain Unassigned. This is a display label, not a selectable Program. New scoped records cannot use it. No unknown affiliation is guessed from a name, username or email.
18. **Password handling:** Show/Hide toggles input visibility only. Existing stored hashes are not exposed in form fields, JSON or audit logs. Django hashing remains authoritative; mobile completion retains existing token authentication.
19. **Permission tests:** cover built-in cross-domain restrictions, stale grants, read-only POST rejection, academic scope, protected Super Admin mutations, suspended authentication/tab tokens and old-session compatibility.
20. **Limitations:** see section 8. The final verification results below distinguish checks that ran from manual checks still required.

## 4. How it works: functions, inputs/outputs and data flow

**Read path:** GET `/admin-users/` → existing login/permission checks → `get_user_management_context(request)` → batched account/application reads → `build_account_rows()` → filter/sort → ten-row pagination → one bounded window query detecting older history and displaying five audit events per account → template + safe `json_script` → `admin_users.js` displays details with `textContent`. Account source is included in every reference so equal numeric IDs from the two stores cannot be confused. Password hashes are not part of the row dictionary.

**Write path:** modal POST → `admin_users_save` or `admin_users_action` → permission checks and transaction → protected Super Admin row locks → validation → existing model save and permission synchronization → AccountActivity → redirect with Django messages. JavaScript hiding improves usability; it does not authorize a request.

**Affiliation function:** `resolve_account_academic(role, account_type, program_id, major_id, existing=...)` accepts role/type and database IDs. It returns `(Department, ProgramMajor)` or `(None, None)`, and raises ValueError for invalid selections. `Department` is the existing Program model; IA/HE/ICT remain linked majors, never standalone departments.

```python
# Practice in an isolated test, not the production database.
program = Department.objects.get(code="BTLED")
major = ProgramMajor.objects.get(program=program, code="HE")
scope = resolve_account_academic(
    "Marketplace Admin", "admin", program.pk, major.pk
)
assert scope == (program, major)  # A linked BTLED-HE assignment is valid.

scope = resolve_account_academic(
    "Facilities Admin", "admin", program.pk, major.pk
)
assert scope == (None, None)  # Global facility scope clears overposted fields.
```

**Permission function:** `role_scope_permissions(role_name)` returns the existing allowed permission set for a built-in domain role or `None` when no additional domain boundary applies. `RoleScopeBackend` uses Django's permissions inside that boundary. PermissionDenied stops the fallback backend from accepting a prohibited stale grant. Keeping ModelBackend configured allows old compatible sessions to continue; middleware separately refuses suspended sessions.

**Seller function:** `seller_request_for(source, account)` resolves a real application using an attached web user or unlinked mobile student identity. `SellerRequest.status` is the application decision; `SellerRequest.is_suspended` is the separate restriction on approved seller privileges. Neither replaces `User.role` nor flips buyer `is_active`.

**Mobile path:** profile screen → `AuthService.academicOptions()` GET real master records → Student chooses IDs → `completeProfile()` JSON with numeric IDs → Django validates with the same affiliation function → serialized AuthUser → SessionService persists returned IDs/labels. Failure shows Retry rather than dummy programs.

This approach was chosen to centralize validation and reuse the current schema. One small suspension field was necessary because Rejected and Suspended have different meanings and no equivalent seller-only flag existed.

## 5. Backend / API behavior and routes

| Route | Method | Behavior |
|---|---|---|
| `/admin-users/` | GET | Existing Users page, filters, sorting and pagination. Requires view permission. |
| `/admin-users/save/` | POST | Existing create/edit route; requires manage permission, CSRF and server validation. |
| `/admin-users/action/` | POST | Existing account/password/seller action route; requires manage permission and protects Super Admin/history. |
| `/admin-users/delete/` | POST | Existing permanent-delete endpoint remains disabled. |
| `/api/mobile/academic-options/` | GET | New read-only public master data; returns programs/linked majors, not personal accounts. |
| Existing mobile complete-profile route | POST | Existing bearer token flow; validates Student Program/Major and returns affiliation. |
| Existing seller submit/status routes | POST / GET | Submission checks approved, unsuspended seller access server-side; access response exposes suspension separately from application status. |

Do not copy a live per-tab token or password into screenshots, documentation or test fixtures. The existing session script maintains tab tokens across forms/links; this task does not replace that mechanism.

## 6. Database / migration impact

Applied successfully to the current database:

- `accounts.0025_global_admin_academic_scope`: clears Department/Major for existing Super Admin/Facilities Admin web accounts only. Their inspected assignments were already null. Student/Marketplace affiliations are retained. Its reverse is deliberately a no-op because invalid cleared values cannot safely be reconstructed.
- `api.0036_seller_access_suspension`: adds `SellerRequest.is_suspended`, default false. Existing pending/approved/rejected decisions remain unchanged.

No account, product, order, booking, payment or audit history was deleted. Browser review users existed only in Django's isolated test database; no sample users were saved to the application database. Passwords use the existing hashing fields.

For another installation, run its normal migration command before loading this version. Do not manually add a second suspension column or invent an account-type migration.

## 7. Tests performed and manual verification

Automated results as of this update:

- Earlier focused Django run: 55 tests passed.
- Expanded final run: 231 tests exercised; 230 passed. Its sole failure was an older test expecting Inventory attention links without the already-existing `view=inventory` parameter. The assertion was corrected; that exact test rerun passed. Application routing was not changed to accommodate the test.
- The expanded suite covers all accounts/API tests included in the command, facilities archive, marketplace program scope, product/inventory/order/bundle/variant regressions and dashboard period tests. It includes the 22 new User Management checks.
- Six final Chrome cases passed: 1440px desktop, collapsed sidebar, 1024px tablet, 375px phone, empty search and BTLED filter. Verified no page overflow, nine columns, four KPIs, control dimensions, role-dependent fields, major clearing/required state, Show/Hide, modal close, reachable overflow-menu items, actual details/activity and debounced GET submission. POSTs were intercepted; browser QA did not mutate live users. Screenshots were visually inspected. The harness waits for modal transitions and scrolls off-screen phone rows into view before testing clicks.
- Flutter analyze on the three changed library files plus the new test: no issues. All three new Flutter widget/service tests passed, including the 375px profile form and master-data Retry state.
- Django `check`: no issues. `makemigrations --check --dry-run`: no changes detected. `showmigrations` confirms both new migrations applied. JavaScript syntax and targeted Git whitespace checks passed (Git printed normal LF/CRLF conversion notices).

Reproduce the focused backend tests from the project root:

```powershell
& backend/core/venv/Scripts/python.exe backend/core/manage.py test accounts.test_user_management --noinput
```

Reproduce mobile checks from `campushub/`:

```powershell
flutter analyze lib/module_app/services/auth_service.dart lib/module_app/session/session_service.dart lib/module_app/screens/profile_setup_screen.dart test/profile_academic_test.dart
flutter test test/profile_academic_test.dart
```

Manual checks, using development/test accounts:

1. Refresh Users with Ctrl+F5. Confirm the four cards, nine columns, no Apply/Delete button and Add Admin label. On a narrow screen the table itself scrolls horizontally; the whole page should not overflow.
2. Create Facilities Admin and another Super Admin in a test database. Program/Major stay hidden; inspect saved null values. Facilities details show All Facilities; Super details show All Modules.
3. Create BSIT/BFPT Marketplace Admin: Program required, Major hidden. Select BTLED: Major appears and is required. Choose HE and confirm table label BTLED-HE.
4. Try an invalid BTLED missing-Major POST and BSIT+HE combination in an isolated test. Neither creates/updates an invalid scope. Overposted fields for a global admin are cleared.
5. Combine search, type, role, status, program, major and seller access; confirm intersection. Clear Filters returns the full permitted list. KPI values remain scope-wide snapshots.
6. View a user and View Activity. Confirm real dates, application decision, scope and recorded actions. A never-used account should have an honest empty activity message.
7. Suspend an approved Student seller. Account remains Active, buyer login works, seller access status is suspended and submission is denied. Restore and verify original approval date. A rejected application must read Rejected, not Suspended.
8. Deactivate a test user with historical transactions: authentication stops, related history remains. Reactivate and verify login. Never test deletion on production records.
9. Try self-deactivation/final active Super Admin demotion, plus a custom manager attempting a Super password reset: requests must be refused.
10. Log in as each admin role and try direct URLs outside its domain, not only hidden menu buttons. A BTLED-HE Marketplace Admin must not read IA products/orders/reports. Facilities Admin must access all facilities without academic assignment.
11. Rebuild/run the updated Flutter app; complete a new Student profile with BSIT and then a separate BTLED+HE test account. Check error/Retry when Django is unavailable. This phone/server integration still requires manual verification.

## Debugging / troubleshooting

| Symptom | Confirmed cause or diagnostic | Safe check / fix |
|---|---|---|
| Old Add User label or old colors | Browser may cache the old CSS/JS; cache suffix was changed in the template. | Ctrl+F5; verify `admin_users.js?v=20261009-role-aware-details` in Network. |
| Database complains that `is_suspended` is missing on SellerRequest | Code is newer than that installation's migration state. | Run `showmigrations api accounts`, then the normal migration command. Do not duplicate the field. |
| BTLED Marketplace Admin sees no marketplace rows | Deliberate fail-closed behavior when Major is missing/mismatched. | Super Admin edits the true linked Major; do not remove the scope filter. |
| Facilities form retains Program in an old record | Global assignment cleanup and backend save rule must be present. | Check accounts migration 0025 and `resolve_account_academic`, not only CSS hiding. |
| Seller is Rejected instead of Suspended | Rejected is the real application decision; the old display conflated them. | Review the actual application. Suspend only approved access; do not guess that a historical rejection meant suspension. |
| New Student profile fails from an older installed APK | Older client does not send the required academic IDs. | Rebuild/install the updated mobile app; keep server validation. |
| User menu action fails although a button was visible | Server permission checks are authoritative. | Confirm actor role, target reference and Django message; never bypass decorators to make a button work. |
| Drawer/form scrolling or phone header overlap | Review found incorrect scoped body selectors and shared modal padding, now corrected. | Inspect `.offcanvas-body`, `.modal-body`, 44px close control and reserved header padding in current CSS. |
| Search fires twice after Enter | A pending debounce can otherwise submit after native Enter. | Current submit handler clears its timer; verify one GET in Network. |

## 8. Remaining limitations and safe learning exercise

- Existing web User rows still use the project's established admin-store classification; mobile rows use their real `user_type`. A future account-store consolidation would need a separately planned migration and ownership mapping. This task does not guess types for historical web rows.
- Users combines both stores in Python before pagination. Related data is batched (including bounded audit events), and query-count tests pass, but very large account populations would benefit from database-level pagination across the stores.
- Actual actor identity is stored in the existing audit description alongside the existing target/request metadata; there is no new actor foreign key. Missing historical activities/approval dates are not backfilled with fictional events.
- An older rejected application is not automatically converted to Suspended. Unassigned student programs are not guessed. Existing custom roles remain supported under the existing permission mechanism; built-in roles get the final domain boundaries.
- Concurrent Super Admin mutation checks use ordered row locks. Automated tests validate outcomes, but no concurrent stress test was run.
- Browser QA used real Django test-rendered output with intercepted writes. Flutter widget/service tests used mocked HTTP. An updated APK was not built/installed or tested against a physical phone during this task.

**Practice exercise:** change only a label in an isolated checkout: replace the Search helper placeholder with `Search name, username or email...` in the Users template. Read how `q` flows from the GET form into `_matches()`; do not change permission checks, audit fields or identity references. Run the focused Django tests, refresh the browser and confirm typing still produces one debounced GET and Clear Filters still resets it. Undo the text change afterwards. This teaches template → JavaScript → request → Python → rendered result without risking stock, accounts or history.


---

## Super Admin User Management UI & Drawer Polish (October 26, 2026)

### 1. Cause / Reason
In previous iterations of `/admin-users/`, accessing user details required opening the three-dot context dropdown menu (`.more-action`) on each table row, making rapid reviews cumbersome. Furthermore, the `#userViewer` right-side drawer rendered all fields in a single flat list without clear categorization, and student academic details (`student_id`, `year_section`, parsed year level and section) from mobile accounts were not displayed in the drawer.

To resolve these issues while upholding CampusHub's university-grade design principles:
1. A direct, accessible **Eye icon button** (`.view-user-btn`) with tooltip "View User" was placed directly in the Actions column.
2. The redundant "View User" item was removed from the three-dot dropdown menu, keeping the three-dot menu focused exclusively on secondary and administrative operations (View Activity, Assist Account Recovery, Suspend/Restore Seller Access, Manage Role, Deactivate/Reactivate Account).
3. The right-side User Details Drawer was structured into 4 distinct semantic groups: **Account Information**, **Academic Information**, **Seller Information**, and **Additional Information**, followed by **Recent Activity**.
4. Academic attributes (`student_id`, `institutional_id`, `year_section`, parsed `year_level`, and `section`) were mapped from `CampusHubUser` models and integrated into search queries and drawer fields.

### 2. Exact Files Changed and Code Anchors

| File | Code Anchor | Changes Made |
| :--- | :--- | :--- |
| `backend/core/accounts/user_management.py` | Line 4, `def _parse_academic_levels` | Added helper to parse strings like `"4A"` or `"2nd Year - Section A"` into normalized `year_level` and `section`. |
| `backend/core/accounts/user_management.py` | Line 166, `_row_from_admin`<br>Line 204, `_row_from_mobile` | Normalized academic fields (`student_id`, `institutional_id`, `year_section`, `year_level`, `section`) across both admin and mobile rows. |
| `backend/core/accounts/user_management.py` | Line 230, `_matches` | Included `student_id` in the search `haystack`, enabling instant lookup by student ID. |
| `backend/core/accounts/user_management.py` | Line 350, `build_account_rows` | Added `seller_applied_at` and `seller_product_type`, and populated mobile academic fields. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | Line 125, `.user-actions` | Rendered direct Eye icon button (`.view-user-btn`) and removed "View User" duplicate from the three-dot menu. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | Line 213, `#userViewer` | Reorganized drawer markup into semantic `<section class="drawer-group">` containers with accessible heading associations. |
| `backend/static/components/js/admin_users.js` | Line 122, `bootstrap.Offcanvas` | Handled focus restoration on close, and populated the 4 structured drawer lists and visual identity badges. |
| `backend/static/components/css/admin_users.css` | Line 243, `.users-table th:nth-child(9)` | Widened Actions column to 115px to fit both the 44px Eye button and 44px More Actions button without clipping or wrapping. |
| `backend/static/components/css/admin_users.css` | Bottom of file | Added styles for `.view-user-btn`, `.drawer-group`, `.drawer-group-title`, and `.view-profile-meta`. |
| `backend/core/accounts/test_account_recovery.py` | Line 53, `test_action_triggers_and_context_menu` | Updated test to verify the 2 distinct triggers in the Actions column and confirm absence of unauthorized menu items. |

### 3. Functions, Inputs/Outputs, and Data Flow

1. **`_parse_academic_levels(year_section_str)`**:
   - **Input**: Raw string from `CampusHubUser.year_section` (e.g., `"4A"`, `"2nd Year - Section A"`, `"3B"`, `""`).
   - **Output**: Tuple `(year_level, section)` (e.g., `("4th Year", "Section A")`, `("2nd Year", "Section A")`, `("", "")`).
   - **Data Flow**: When `build_account_rows` iterates over mobile users, this helper parses the stored string into distinct values for the drawer.

2. **`_matches(row, query, ...)`**:
   - **Input**: Normalized row dictionary and filter criteria.
   - **Output**: Boolean `True` if the row matches all active criteria.
   - **Data Flow**: `student_id` is joined into the lowercase search string (`haystack`). When an admin enters a student ID in the search bar, the debounced GET request (`q=...`) filters the table rows server-side.

3. **Client-side Drawer Population (`admin_users.js`)**:
   - **Input**: Click event on `.view-user` button reading `data-user-ref`.
   - **Output**: Structured DOM nodes injected into `#accountInfoList`, `#academicInfoList`, `#sellerInfoList`, and `#additionalInfoList`.
   - **Data Flow**: Clicking `.view-user` retrieves the user row from `byRef[userRef]` (deserialized from `usersData`). Empty or missing historical values are labeled `"Not recorded"` or `"Not applicable"` rather than fabricated.

### 4. Backend / API and Database Impact

- **No Schema Changes or Migrations**: All displayed fields (`student_id`, `institutional_id`, `year_section`, `created_at`, `reviewed_at`) already existed on the `CampusHubUser` and `SellerRequest` models.
- **Strict Read-Only Drawer**: No state changes occur when viewing user details. Plaintext passwords, hashes, and session tokens remain completely excluded from serialized data.
- **RBAC Enforcement**: Server-side permission guards in `admin_users_action` and `support_scope.py` continue to authorize any state-changing actions.

### 5. Verification and Test Results

- **Automated Tests**:
  - `accounts.test_user_management`: 27 tests passed.
  - `accounts.test_roles_permissions`: 27 tests passed.
  - `accounts.test_account_recovery`: 34 tests passed.
  - **Total**: 88 tests passed in 66.3 seconds with 0 errors.
- **Manual / Visual Checks**:
  - Actions column cleanly displays both 44px Eye button and 44px Three-Dot button.
  - Tooltip "View User" appears on hover over Eye icon.
  - Clicking Eye icon opens offcanvas drawer without full page reload.
  - Drawer displays Account, Academic, Seller, and Additional Information cleanly separated with institutional navy/gold styling.
  - Closing drawer restores focus to the triggering Eye icon button.

### 6. Safe Practice Exercise

**Exercise**:
1. Open `backend/core/accounts/user_management.py`.
2. Inspect `_parse_academic_levels` at line 4.
3. Test how a new pattern (e.g. `"Year 1, Section C"`) is parsed.
4. Run `backend/core/venv/Scripts/python.exe backend/core/manage.py test accounts.test_user_management` to verify that all existing academic parsing assertions hold.

---

## 11. Table Header Alignment, Single-Line Columns, and Services-Matching Action Icons

### 1. Cause / Reason

1. **Vertical Action Button Stacking**:
   In previous iterations, the two action buttons (the Eye icon `.view-user-btn` and the Three-Dot icon `.more-action`) stacked vertically into a tall pill container inside the `ACTIONS` column. This was caused by an override rule in `backend/static/components/css/admin_users.css` setting `th:nth-child(9) { width: 80px; }`. With cell padding subtracted, the available width was insufficient for two 32px buttons with a 6px gap, forcing CSS flexbox to wrap them onto two lines.

2. **Column Header Multi-line Wrapping**:
   Column headers such as `Account Type` (110px width) and `Program / Major` (135px width) were constrained too tightly, causing their text and sort arrow indicators to break into a second line.

3. **Inconsistent Table Header Surface**:
   The table header required visual parity with the Services / Facilities module (`admin_facility.css`), featuring a `#f1f5f9` slate-gray background, a fixed 48px row height, a 1px `#e2e8f0` border, and uppercase bold typography (`0.78rem`, `#64748b`).

### 2. Exact Files Changed

| File | Code Anchor | Changes Made |
| :--- | :--- | :--- |
| `backend/static/components/css/admin_users.css` | `.users-table`, `.users-table th:nth-child(...)` | Removed redundant late-override block; set explicit proportional widths (`1: 210px`, `2: 125px`, `3: 140px`, `4: 120px`, `5: 150px`, `6: 130px`, `7: 135px`, `8: 125px`, `9: 96px`); enforced `white-space: nowrap;` so column headers never wrap into 2 lines. |
| `backend/static/components/css/admin_users.css` | `.users-table thead th` | Aligned header row to `#f1f5f9` background, 48px height, 1px `#e2e8f0` borders, `0.78rem` bold uppercase text, and `#64748b` color matching the Services table. |
| `backend/static/components/css/admin_users.css` | `.sort-button` | Configured inline flex button with `white-space: nowrap;`, `#64748b` label color, `#94a3b8` sort indicator, and `#1A1851` hover color. |
| `backend/static/components/css/admin_users.css` | `.user-actions`, `.icon-action` | Formatted action container as `display: inline-flex; flex-wrap: nowrap; gap: 6px;` and `.icon-action` as 32px × 32px squares with `border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff; color: #1A1851;` matching Services action buttons. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | `<link rel="stylesheet">` | Updated cache-buster version to `?v=20261026-services-gray-v4`. |
| `backend/core/accounts/test_account_recovery.py` | `test_action_triggers_and_context_menu` | Updated trigger count assertion to expect 2 authorized action buttons (`view-user-btn` and `more-action`). |

### 3. How It Works and Data Flow

```
[User Row Rendering]
        │
        ├─► thead: Fixed 48px height, #f1f5f9 slate background
        │     │
        │     └─► 9 Columns: Proportional min-widths, white-space: nowrap
        │           ├─ Col 1: USER (210px)
        │           ├─ Col 2: USERNAME (125px)
        │           ├─ Col 3: ACCOUNT TYPE (140px - zero wrapping)
        │           ├─ Col 4: ROLE (120px)
        │           ├─ Col 5: PROGRAM / MAJOR (150px - zero wrapping)
        │           ├─ Col 6: SELLER ACCESS (130px)
        │           ├─ Col 7: ACCOUNT STATUS (135px)
        │           ├─ Col 8: LAST LOGIN (125px)
        │           └─ Col 9: ACTIONS (96px centered)
        │
        └─► tbody td:last-child (.user-actions)
              │
              └─► flex-wrap: nowrap, gap: 6px
                    ├─► [Eye Icon Button] (32px × 32px) -> Opens User Details Offcanvas Drawer
                    └─► [Three-Dot Button] (32px × 32px) -> Opens Dropdown Context Menu
```

### 4. Verification and Visual Confirmation

- **Browser Verification**: Rendered via headless Chromium at 1680px and 1440px desktop resolutions:
  - Table header height: exactly 49px (48px box + 1px border).
  - Table header background: `rgb(241, 245, 249)` (`#f1f5f9`).
  - Column text: Single straight row across all 9 columns (`whiteSpace: nowrap`, button height 12–14px).
  - Action buttons: Both buttons sit on the same horizontal row (`top0 === top1`, e.g. `552px === 552px`, `sameRow: true`).
- **Automated Regression Suite**:
  - `python manage.py test accounts.test_account_recovery accounts.test_user_management accounts.test_roles_permissions`:
  - **88 of 88 tests PASSED** in 64.6s.

### 5. Safe Practice Exercise

**Exercise**:
1. Open `backend/static/components/css/admin_users.css`.
2. Inspect `.users-table thead th` and `.user-actions` at lines 480 and 804.
3. Observe how `flex-wrap: nowrap` together with the 96px column width guarantees that `.icon-action` elements never collapse into multiple rows.
4. Verify the page by inspecting `/admin-users/` in your browser.
