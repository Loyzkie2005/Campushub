# Roles & Permissions: implementation, debugging and learning guide

## Current update: final administrator role structure (October 10, 2026)

This update supersedes the visible Standard User row and Access Scope wording in older sections. The previous three-dot implementation remains the source of the menu layout; it was not redesigned.

### 1. Cause / reason

Confirmed: the administrator table and Total Roles KPI included the internal `User` role, even though ordinary user capabilities are not administrator RBAC. The heading said Access Scope, Super Admin's value said Full System Access, and the row/drawer called editable built-in administrators protected. The setter accepted management permissions without their matching View permissions. Administrator reassignment logged the new assignment but did not link a removal event to the previous role's history.

The read-only live inspection found five roles: User, Super Admin, Marketplace Admin, Facilities Admin and one custom role. User has four existing ordinary capability grants. Four Django administrator accounts are assigned to built-in admin roles; three mobile accounts retain User. All built-in admin roles are active. Nothing was deleted or normalized in the live database.

### 2. Exact files, current lines and code anchors

| File | Line / anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/accounts/role_management.py` | 25 `BASE_ROLE_NAMES`, 28 `SCOPE_LABELS`, 34 `managed_admin_roles` | Hide User/Standard User aliases from the admin dataset without deleting their records. Use Full Access / Marketplace Access / Facilities Access / Custom Access. |
| Same file | 39 `eligible_admin_queryset`, 49 `admin_data`, 63 `serialize_role` | Count actual eligible administrators only. An existing eligible admin awaiting a role shows Unassigned in this workflow, not Standard User. Ordinary accounts remain excluded. |
| Same file | 139 `role_history_response`, 164 `admin_roles_page` | Use the same filtered admin dataset for table, search/type/status filters, configure links, history and Total Roles. Preserve real custom roles and existing batching/pagination. Pass one shared dependency map to JS. |
| Same file | 208 `assign_admins`, 231 `previous_roles`, 246 `ADMIN_REMOVED_FROM_ROLE`, 255 `admin_roles_save` | Add previous-role removal activity during real reassignment, update the real affected role timestamps and log an actual status transition made through the information form. Use the existing audit writer/table. |
| `backend/core/accounts/role_permissions.py` | 106 `PERMISSION_DEPENDENCIES`, 123 `include_permission_dependencies`, 335 `set_role_permissions` | Reuse existing permission codes. Add required View capabilities when saving dependent actions, after filtering invalid/out-of-domain codes. No new permission definitions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_roles.html` | 89 table headings, 93 role label, 161 `.permission-dependency-note`, 272 `permissionDependenciesData` | Rename Access Scope to Access Level. Reserve Protected System Role for the read-only Super Admin row. Add small explanatory dependency copy. Remove the ordinary-user capability section; keep the five admin modules and seven columns. Refresh assets with `20261010-admin-role-structure`. |
| `backend/static/components/js/admin_roles.js` | 20 `permissionDependencies`, 96 `sync`, 128 `openPanel` | Automatically check/lock a required View control while a dependent action is enabled. Explain why. Unlock it after dependent actions are removed. Remove base-user drawer handling and correct built-in drawer labels. |
| `backend/static/components/css/admin_roles.css` | 85 `.permission-dependency-note` | Small supporting explanation using existing typography/colors; remove unused base-user drawer styles. The compact three-dot/menu styling remains. |
| `backend/core/accounts/test_roles_permissions.py` | 56 KPI test, 244 menu test, 327 hidden-role/login test, 355 labels, 365 dependencies, 386 reassignment audit | Update old visible-base expectations; add hidden-role safety, actual student/guest mobile login, direct-POST dependency, scope, timestamps and old-role audit coverage. |
| `backend/core/accounts/tests.py` | 981 page expectations, 1069/1093/1145 saved grants, 1329 save/reload test | Update existing regression expectations for requested labels and the new required View grants; preserve unrelated security assertions. |
| `scratch/roles-review/check-structure.cjs` | 43 viewport loop, 99 dependency exercise | Browser review of the actual isolated Django render; no live browser POSTs. Check hidden User, Access Level, dependencies and retained menus/drawers at six widths. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest final-Roles policy | Save these rules for future tasks. This existing guide is the detailed implementation/debugging reference. |

### 3. Changes made / final display

| Role | Role Type | Access Level | Actions |
| --- | --- | --- | --- |
| Super Admin | System Role | Full Access | View Permissions only, read-only, all admin permissions Allowed. |
| Marketplace Admin | System Role | Marketplace Access | View/Edit Permissions, View Assigned Administrators, eligible Assignment, View Permission History. |
| Facilities Admin | System Role | Facilities Access | Same applicable built-in admin actions. |
| Existing custom roles | Custom Role | Custom Access | Editable-role actions plus Edit Role Information and Deactivate/Reactivate. |

Only one vertical three-dot button appears per row. Existing eligibility is preserved: inactive/unconfigured roles cannot be assigned and their assignment item remains hidden. No UI delete, built-in identity edit or system-role deactivate. Super Admin retains full access regardless of its grant selection and cannot be modified through these endpoints.

Final columns: Role, Role Type, Assigned Admins, Access Level, Status, Last Updated, Actions. The real live role count for the inspected database is four visible admin roles; this number is calculated, not a configured constant. The four existing KPI cards remain. Total Roles describes the managed admin catalog; search/type/status select table rows while catalog-wide KPIs retain their existing behavior. Assigned/Unassigned Admins use eligible Django administrator accounts, never the separate mobile-user population.

Program/Major remains on the administrator account, not Role. Existing Marketplace assignment requires the real Program and BTLED Major. Facilities assignment clears inapplicable academic scope and remains global. No academic role variants were created. Last Updated uses the real `updated_at`; missing historical dates still show a dash, not today's date.

### 4. Functions, inputs/outputs and data flow

`managed_admin_roles()` returns a Django queryset excluding case-insensitive User/Standard User names. It makes no writes. `admin_roles_page(request)` uses this source before filtering and pagination, so a hidden base role cannot reappear through search, `configure=<id>` or history. Ordinary account records and base grants are separate from that display decision and remain intact.

The dependency map pairs a real action code with existing read codes. `include_permission_dependencies(codenames)` accepts selected codes and returns the existing administrative selection plus read prerequisites. `set_role_permissions(role, codenames)` first retains valid/domain-permitted codes, then adds those prerequisites, saves the existing M2M grant set/timestamp and uses the existing account synchronization path. A view-only selection never gains Manage authority. The editor endpoint still preserves normal/mobile and unrelated historical grants outside its administrative scope.

Dependency pairs: Manage/Approve Products -> View Products; View Stock Movements -> View Inventory; Manage Orders -> View Orders; Manage Sellers -> View Sellers; Manage Facilities -> View Facilities; Manage/Approve Bookings, Schedules and Record Facility Payment -> View Bookings; Assist Account Recovery, User Monitoring and Manage Admin Accounts -> View Users. All are existing definitions; forbidden cross-domain actions are removed before normalization, so they cannot smuggle their View dependency into a built-in role.

Annotated example:

```python
selected = {"can_manage_orders"}           # Administrator chose an action.
normalized = include_permission_dependencies(selected)
# Result: {"can_manage_orders", "can_view_orders"}.
# Selecting only can_view_orders still returns only can_view_orders.
```

Django passes the map as escaped `json_script` data. JS `sync()` receives the current role, editor mode and checked boxes, computes required reads, checks and disables those reads and shows Required by an enabled action. Disabling Manage leaves its View selected but editable; the administrator may keep read access or turn it off. View mode remains read-only. Cancel never saves. If an old role has an incomplete combination, Edit shows the required correction as an unsaved change; merely opening it does not update the database. Save enables only if the actual normalized selection differs from the stored selection. Backend normalization also protects direct POSTs that omit View.

`assign_admins(request, role)` retains existing eligible-account checks, academic validation, confirmations, transaction locks and final-active-Super protection. For a real move between managed roles, it now writes ADMIN_REMOVED_FROM_ROLE under the old role UUID, then the existing role-change/assignment events under the destination UUID. This lets both history views explain the move. It never deletes history or logs an ordinary User role as an admin-role removal. Both affected role modification timestamps reflect the actual assignment change. Custom information-form status transitions now also record the same ROLE_ACTIVATED/ROLE_DEACTIVATED event types used by the existing status endpoint.

### 5. Backend / API behavior

Existing `/admin-roles/`, `/admin-roles/permissions/save/`, `/admin-roles/save/` and `/admin-roles/status/` routes are reused. Roles reads/writes remain Super Admin-only; server-side protected-role, built-in domain, account eligibility and final-Super rules remain. Hidden base-role mutations are still rejected; a base-role history GET returns 404 and its configure link does not open a drawer. The existing history reader, no-cache JSON, paging, empty/error/Retry and menu keyboard/viewport behavior remain.

Student/Guest login and buyer/booking permissions remain outside this admin editor. No mobile app code, authentication endpoint or account-type policy was changed. Account Recovery remains information-only under the latest recovery policy; adding its View Users prerequisite does not restore admin code sending.

### 6. Database / migration impact and safety

No schema, migration, new role or new permission definition. User remains internally with its existing grants. Existing custom roles, administrator assignments and academic scopes are preserved. The live inspection records a fingerprint of role IDs/names/status/timestamps, grant links, Django role/account flags/scope, mobile role identities and audit count in `scratch/roles-review/structure-before.json`. The after-inspection in `structure-after.json` has the identical SHA-256 fingerprint `7ac97f295d306a8dd3aaec297757417c622125b6549e91ae0754efc5b4f2ee02`: all five roles, grant links, four assigned administrator accounts, three User mobile accounts and 287 audit records are unchanged in that snapshot.

Future authorized saves apply the requested dependency normalization and normal existing audit/timestamp writes. There is no automatic rewrite of historical grants or role activation/deactivation. Test roles/accounts exist only in the isolated test database, and browser requests are intercepted.

### 7. Tests performed / manual checks

Actual verification:

- Broad command: `manage.py test accounts.test_roles_permissions accounts.test_user_management accounts.test_marketplace_support accounts.tests api.tests --noinput`. Initial run: 146/149 passed; three new assertions had assumed exactly four isolated roles, but existing migrations also seed custom roles. Fixed the expectation to preserve/count all actual custom roles.
- Broad rerun: 148/149 passed in 103.165 seconds. One new test looked for Standard User anywhere in HTML while deliberately searching that text; the search input correctly echoed its query. Fixed the assertion to inspect the actual role label/dataset rather than forbid the search input's value. No application change was necessary.
- Final focused run: all 27 `accounts.test_roles_permissions` tests passed in 4.897 seconds. Thus the 27 final Roles cases and other 122 broad regression cases passed across these runs; a third complete 149-case command was not run. Logs: `scratch/role-structure-regression.log`, `role-structure-regression-final.log` and `role-structure-roles-final.log`.
- Actual isolated Student and Guest mobile-login POSTs succeeded; internal base grants/accounts remain. Direct dependency POSTs, forbidden cross-domain additions, view-only behavior, assignment removal history, timestamps and protection tests passed.
- `manage.py check`: zero issues. `makemigrations --check --dry-run`: no changes. `node --check backend/static/components/js/admin_roles.js` and browser harness syntax check: passed.
- Headless Chrome: all six widths 1920/1440/1024/768/375/320 passed hidden base role, correct Access Level/drawer labels, required View check/lock/unlock/note, retained role-specific menus, keyboard/viewport behavior, unchanged-only Save, assignment/account status, history/error/Retry, custom confirmation/cancel and filters. Every browser POST was mocked; no application writes. Desktop table and phone menu screenshots were visually inspected. Final log: `scratch/role-structure-browser-final.log`.
- Read-only live before/after database inspection: fingerprints match, as recorded above.

The browser harness needed a local variable reused safely between Runtime evaluations; that was an automation-script issue, not application JS. No confirmed application defect remains from these checks.

Manual checks:

1. Hard-refresh Roles & Permissions. Verify User/Standard User is absent, Total Roles excludes it and every existing custom role remains. Search User and use the System/Custom and Active/Inactive filters; hidden base roles must not reappear.
2. Check all seven headings and Access Level values above. Only Super Admin has the Protected System Role note. Built-in administrator View/Edit drawers use System Role plus their real access label.
3. Open Super Admin's menu: View Permissions only; all Allowed, no editable controls/Save/assignment. Existing built-in and custom menu restrictions should match the action table.
4. On a disposable test role, enable Manage Orders. View Orders automatically checks and displays the required note. It cannot be turned off until Manage Orders is disabled. Save then reload to verify both grants. Use Cancel for experiments on real assigned roles.
5. Repeat for Manage Facilities and Approve Bookings. A Marketplace role cannot enable Facilities grants. A view-only custom role must not gain its matching management permission.
6. Verify real assigned-administrator counts and details. Existing Marketplace admins retain individual Program/Major; Facilities is global. Reassign a disposable administrator between test roles with confirmation; both histories should show the actual change and old-role removal. Never experiment with the final active Super Admin.
7. Test normal Student and Guest mobile login and existing browsing/booking access. User accounts, base role and normal capability grants must remain intact.
8. At narrow widths, scroll the retained table to Actions, open the last menu, test outside click/Escape/Enter/Space/arrows and focus restoration. Search, filters and existing pagination should retain their behavior.

### 8. Remaining limitations / debugging and learning

- Older audit events without stable role metadata cannot be reconstructed. Removal events appear for future authorized reassignment; no fabricated backfill was created.
- Inactive/unconfigured custom roles intentionally cannot receive new assignments. Configure and activate first.
- Existing incomplete permission combinations are normalized when editing/saving; this task does not silently rewrite live historical grants. A required View addition can legitimately enable Save in Edit before any manual click because the shown correction differs from saved data.
- If User still appears, confirm the page uses `managed_admin_roles()` and hard-refresh the `20261010-admin-role-structure` assets. Do not delete the User record to fix a display issue.
- If a View control is locked, read its required note and disable the related actions first. Investigate the existing built-in domain rules before changing the dependency map.
- Mobile login regression tests use real Django endpoints in an isolated database; they do not replace a physical-phone end-to-end check.

Safe practice exercise: use a local test role's drawer, record its current permission count, enable Manage Orders and observe View Orders/required-note/Save. Turn Manage off, return View to its original state, and verify Save disables. Cancel and reopen; the original set must remain. Then read `PERMISSION_DEPENDENCIES` and `sync()` to connect the selected input, computed prerequisite and visible output. This teaches how UI state differs from a database save without changing an administrator's live access.

## Earlier update: three-dot-only role actions (October 10, 2026)

This section describes the latest action-menu update. The original implementation notes below are historical; their action layout and line numbers may differ from the current files. No example roles or accounts were added to the live database.

### 1. Cause / reason

Confirmed: the current table had separate View and Edit buttons alongside More. The user requested one vertical three-dot button for each row, with only applicable actions inside it. Existing backend rules already make Super Admin and Standard User read-only and prevent assigning administrators to inactive or unconfigured roles. Those rules remain authoritative.

The previous menu had no usable permission-history action. Existing `AccountActivity` records already contain role IDs, so the update reads those records rather than creating another log system. Assigned administrators also needed an explicit account-status label.

### 2. Exact files, current lines and anchors

These line numbers belong to this update; use the anchor to find the code after later edits.

| File | Current line / anchor | What changed and why |
| --- | --- | --- |
| `backend/core/modules/user_management/templates/user_management/pages/admin_roles.html` | 100 `.role-row-actions.dropdown`, 101 `roleAction-` | Replace separate inline View/Edit/More controls with one vertical-dot button. Keep all seven table columns. |
| Same template | 104 `roleMenu-`, 106 `not role.is_readonly`, 109 `not role.can_assign` | Render role-specific menu actions; hide unavailable assignment rather than displaying a disabled action. |
| Same template | 254 `roleHistoryModal`, 262 `roleStatusModal` | Add compact history and custom-role confirmation modals using the existing modal styling. Asset version `20261010-role-actions` refreshes the changed CSS/JS. |
| `backend/static/components/js/admin_roles.js` | 19 `roleTriggers`, 21 dropdown initialization | Temporarily move the open menu to the document body so the table cannot clip it. Restore it when closed. Keep a stable row button for returning keyboard focus. |
| Same JS | 76 `remember`, 117 `openPanel`, 137 `openAssignment`, 146 `openInfo` | Reuse the existing drawer and assignment/information modals; update hidden assignment availability after permission configuration. Preserve changed-only Save behavior. |
| Same JS | 155 `loadHistory`, 186 `roleStatusForm` submit | Read paginated history with loading/empty/error/Retry handling; send confirmed status changes to the existing status endpoint. |
| Same JS | 196 document click handler, 206 `.js-view-assigned-users`, 225 `.js-role-status` | Close menus before opening another component. Show real assigned-account status and applicable Program/Major. Replace native confirmation with the requested custom-role modal. |
| `backend/static/components/css/admin_roles.css` | 42 `.role-icon-action`, 46 `.dropdown-item`, 47 `.dropdown-divider`, 51 `.is-floating`, 54 `.role-history-list` | Keep the icon compact with a 44px target; explicitly preserve menu padding/divider after portaling; constrain menu to the viewport and show gold keyboard focus. Add compact history rows. |
| `backend/core/accounts/role_management.py` | 43 `admin_data`, 52 `account_status` | Serialize Suspended/Active/Inactive from existing account flags; do not invent another account status field. |
| Same Python | 133 `role_history_response`, 158 `admin_roles_page` | Read existing role audit events, newest first, 20 per page, only after existing Super Admin authorization. Return safe display fields with `Cache-Control: no-store`. |
| `backend/core/accounts/test_roles_permissions.py` | 240 `test_single_action_menu...`, 268 `test_assigned_administrators...`, 276/299 history tests, 312 browser fixture export | Verify actions, status, history isolation/paging/read-only behavior and authorization. Export real test-rendered HTML only when the optional scratch directory is configured. |
| `scratch/roles-review/check-actions.cjs` | 11 browser harness, 43 viewport loop | Reproducible headless Chrome review at six widths, with every POST intercepted. Scratch fixtures/screenshots are verification artifacts, not application data. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest Roles policy | Preserve the current action and backend rules for future tasks. This guide is the explanation/debugging reference. |

### 3. Changes made: menu contents

| Role | Visible actions |
| --- | --- |
| Super Admin | View Permissions only. All permissions remain allowed and read-only. |
| Standard User (stored name `User`) | View Permissions only. Existing protected base-role behavior retained. |
| Marketplace Admin / Facilities Admin | View Permissions; Edit Permissions; View Assigned Administrators; Assign Administrators when eligible; View Permission History. |
| Active custom role | The editable-role actions above, then Edit Role Information and Deactivate Role. |
| Inactive custom role | View/Edit Permissions, View Assigned Administrators, View Permission History, Edit Role Information and Reactivate Role. Assignment remains hidden until active and configured. |

No menu exposes Delete Role. Built-in roles have no identity edit or status mutation action. Existing server-side protections remain in place; hiding an action alone would not be sufficient authorization.

### 4. How it works: functions and data flow

`serialize_role(role)` already supplies `is_readonly`, `is_protected`, `can_assign`, existing grants and eligible assigned administrators. Django passes that data to the row template and `rolesData` JSON. The template chooses the initial menu; JS updates it after successful permission saves. `admin_data(user)` adds the status label using `is_suspended` first, then `is_active`, while keeping the existing applicable academic scope.

Click a row's three dots -> Bootstrap opens the menu -> JS moves the menu outside the table -> Popper positions it beside the button and flips upward when necessary. Clicking outside, Escape, selecting an action or scrolling the table closes it. The menu returns to its original row when closed. Explicit padding and divider CSS are necessary because the floating menu temporarily drops Bootstrap's `dropdown-menu` class to avoid its sibling-based keyboard assumptions.

The toggle supports Enter/Space. Arrow keys, Home/End and Escape navigate/close menu items. Buttons retain a visible focus indicator. Closing a drawer/modal returns focus to the stable three-dot button; Add Custom Role returns to its Add button. On small screens the existing seven-column table still scrolls horizontally, while the menu stays within the screen.

`openPanel(role, mode, ...)` reuses the permission drawer. View mode is read-only even for editable roles. Edit mode keeps existing module/domain restrictions and enables Save only after the selected permissions differ from the saved set. `openAssignment(role)` retains the current eligible-administrator selector, confirmation, scope validation and existing POST workflow. It does not make ordinary buyers eligible.

History flow: select View Permission History -> `loadHistory(role, pageNumber)` makes an authenticated GET to the existing page URL -> `admin_roles_page` checks Super Admin access -> `role_history_response` reads existing audit records -> JSON display fields -> safe DOM `textContent` rows. The request sequence ignores late responses after the modal closes or changes role. Inputs are the stable role UUID and page number; outputs are events, total and page/navigation flags. Loading, actual empty history and failed/session-expired requests have distinct messages; Retry makes another GET.

Annotated backend example:

```python
# A role name can change; its saved UUID remains stable.
events = AccountActivity.objects.filter(
    module="Roles & Permissions",       # Keep unrelated account activity out.
    metadata__role_id=str(role.pk),      # Reuse the existing audit association.
).order_by("-created_at", "-pk")        # Latest event first, stable tie-breaker.
page = Paginator(events, 20).get_page(request.GET.get("history_page"))
```

The response includes event ID, human-readable event name, recorded activity text and Manila date/time. It omits raw audit metadata, passwords, codes and grants. Reading history makes no writes. This approach preserves historical role IDs across renames and avoids fetching all history into the page.

For custom roles, the confirmation form passes the existing role ID/action/CSRF token to `admin_roles_status`. Deactivation text states the requested new-assignment restriction and also explains the existing backend effect: assigned administrators lose the inactive role's permissions until reactivation. Assignment and activity history are preserved. Cancel makes no request.

### 5. Backend / API behavior

| Operation | Existing route / behavior |
| --- | --- |
| History | GET `/admin-roles/?history_role=<uuid>&history_page=1`; authenticated Super Admin only, no-cache JSON, 20 events/page. Invalid role -> 404; non-GET history request -> 405; unauthorized admin -> 403. |
| Save permissions | POST `/admin-roles/permissions/save/`; unchanged authorization/domain rules and audit writing. |
| Assign / role information | POST `/admin-roles/save/`; unchanged operation separation, eligibility, final-Super protections and audit writing. |
| Deactivate / reactivate | POST `/admin-roles/status/`; unchanged custom-role-only status rules and existing history. |

The history GET preserves existing page query parameters, including tab authorization. No new URL entry or duplicate permission endpoint was created. Existing audit mutations continue using `audit`; the history viewer never creates its own event log.

### 6. Database / migration impact

No model, schema, migration, permission definition, role grant or live account changes. The new JSON account-status property is computed from existing fields. Tests create/delete isolated test databases; browser fixtures come from those tests, and browser POSTs are mocked. No production sample roles, assignments or histories were inserted.

### 7. Tests performed and manual verification

- Broad regression run: `accounts.test_roles_permissions accounts.test_user_management accounts.test_marketplace_support accounts.tests` ran 131 cases; 130 passed. One new fixture incorrectly saved a stale user object after assignment. This was a test setup error, not a confirmed application defect: fixed by `refresh_from_db()` and saving only `is_suspended`.
- Final Roles regression after that correction: all 23 tests passed. The other broader-suite cases passed in the previous run; the full 131-case command was not rerun. Logs: `scratch/role-actions-regression.log` and `scratch/role-actions-roles-final.log`.
- `manage.py check`: zero issues. `makemigrations --check --dry-run`: no changes. `node --check backend/static/components/js/admin_roles.js`: passed.
- Chrome: six widths (1920, 1440, 1024, 768, 375, 320) passed role-specific menus, viewport bounds/upward positioning, outside/select/Escape closure, native Enter/Space, arrow/Home/End focus, protected/view/edit drawers, changed-only Save, assignment visibility, account status, history loading/error/Retry/empty, custom confirmation/cancel and filters. No real browser writes; no JS errors. Screenshots were inspected for floating-menu and history layout. After explicit menu padding/divider styling, all six widths passed again; the final phone menu screenshot confirms compact padding and a visible divider. Final log: `scratch/role-actions-browser-final.log`.

An initial browser harness clicked while a queued horizontal-table scroll was still settling; the existing scroll-to-close handler hid the just-opened menu. Awaiting completed scrolling fixed the automation sequence. No change to role authorization or actual dropdown behavior was needed. Chrome Enter dispatch also needs its native carriage-return text, which the harness now supplies.

Manual steps (use a local test account/role, never the final active Super Admin for experiments):

1. Hard-refresh the Roles page as Super Admin. Confirm seven columns and one three-dot button per row; compare each role to the action table above.
2. Open Super Admin and Standard User View Permissions. Controls are read-only, no Save/assignment. For an editable role, View remains read-only; Edit Save starts disabled, enables after a checkbox change, disables again after successful save.
3. Open an editable role's Assigned Administrators. Check recorded name/username, applicable Program/Major and actual account status; ordinary student/guest accounts are absent. Existing assignment should list only eligible administrators.
4. View history for a role with real changes. Confirm newest-first events and paging if there are more than 20. A role without linked events shows the honest empty message. In browser network tools, temporarily block the history GET: error + Retry must appear, never fake zero history.
5. For a disposable custom role, open Deactivate, read the impact, Cancel, then confirm if intended. Refresh: Reactivate replaces Deactivate. History and assignments remain. Assignment is hidden while inactive or before configuring permissions.
6. Test the last row's menu, outside click and Escape. Tab to the toggle, open with Enter/Space, use arrows/Home/End, select a view, close it and check focus returns. At phone widths, scroll the table to Actions and ensure menu visibility.
7. Search and change existing filters; confirm the page dataset/pagination remains correct. Unauthorized roles must still be blocked from direct Roles/history requests.

To rerun focused tests from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test accounts.test_roles_permissions --noinput
```

### 8. Remaining limitations / debugging

- Older audit rows lacking `metadata.role_id` cannot be reliably attached to a role; the viewer does not guess by role name. No recorded events is an honest state, not a reconstructed history.
- Assign Administrators is intentionally hidden for inactive/unconfigured roles because the backend already rejects that operation. Activate and configure permissions first.
- Assigned-account data is the authorized page snapshot; refresh to see external account/assignment changes. Successful assignment/status workflows already reload.
- Browser checks use isolated HTML and mocked writes; they complement the real Django endpoint tests and are not a production deployment or physical-phone test.
- If old View/Edit icons remain after deployment, hard-refresh and verify the CSS/JS URL version `20261010-role-actions`. If the menu clips, inspect `is-floating` and its document-body placement; do not remove table overflow to fix it.
- If history fails, inspect the authenticated GET status/JSON response (403 access, redirect/session expiry, 404 invalid role, server error); never bypass authorization or expose raw audit metadata as a workaround.

Safe learning exercise: in a temporary branch, change only the custom-role information menu label to `Edit Role Details`, then hard-refresh. Verify the label, matching keyboard action and unchanged modal/API behavior; run the focused tests to see that action-label expectations detect the change. Restore the wording and rerun. This teaches the difference between presentation text, JS selector classes and server-authorized behavior without changing grants or live accounts.

## Earlier implementation reference

Latest policy update: Marketplace Admin has View Users, Reset User Password and scoped User Monitoring. The editor now has 34 administrative definitions. Roles & Permissions reads and mutations are Super Admin-only, including for old custom grants. See [Marketplace Admin support](marketplace-admin-support.md) for the new scope/reset migration and current line map. Earlier verification counts below describe the original Roles implementation.


Updated October 9, 2026. This update uses the existing Django `Role`, `User`, `auth.Permission`, role grants and account activity tables. It does not introduce a second RBAC system. Browser examples were rendered from an isolated test database; no example roles or accounts were added to the application database.

## Cause / reason

Confirmed in the previous implementation: the five-column table combined role type with role name, called administrator counts “Users”, and had no role modification timestamp. Its assignment selector included every Django account, including ordinary users. Role information, permissions and assignments could be saved in one request, so changing a description could replace grants. The initial modal allowed assignment before permission configuration. The delete endpoint reset assigned accounts to the base role and deleted their role. Buyer/mobile capabilities appeared alongside admin permissions.

The update separates those operations and uses the existing Products/Users page layout. UI/UX Pro Max guidance for multi-step forms informed the visible step labels, associated input labels and saving/error feedback. CampusHub’s existing palette and components remain the design source.

## Exact files, current lines and anchors

Line numbers are starting points; use the named anchor if later edits move them.

| File / folder | Line and nearby anchor | Added, changed, moved or removed; expected behavior |
| --- | --- | --- |
| `backend/core/accounts/models.py` | 63 `class Role`, 69 `updated_at`, 80 `Meta.permissions`, 172 `metadata` | Add nullable role modification time, seven read permission definitions and structured audit metadata. Reuse existing role grants. |
| `backend/core/accounts/migrations/0026_role_management_audit.py` | 6 `READ_GRANTS`, 16 `preserve_read_access` | Add the two fields and materialize read definitions. Carry existing management access forward without removing any grants. |
| `backend/core/accounts/role_management.py` | 33 `eligible_admin_queryset`, 56 `serialize_role`, 134 `admin_roles_page` | Move the existing Roles page orchestration out of the large accounts view file. Batch role grants and eligible administrators; build real KPIs and seven-column rows. |
| Same file | 83 `audit`, 105 `role_post`, 175 `assign_admins` | Shared authorization, transaction/input handling, confirmations, academic scope validation, final Super Admin protection and audit records. |
| Same file | 217 `admin_roles_save`, 251 `admin_role_permissions_save`, 275 `admin_roles_status`, 291 `admin_roles_delete` | Separate information/assignment from permissions. Protect built-in identities and prevent deleting protected, assigned or historical roles. |
| `backend/core/accounts/views.py` | 110 `products_module_required`, 167 `admin_products_page`, 320 `admin_orders_page`, 1127 `admin_bookings_page`, 1169 `from .role_management import` | Existing URL names remain bound to the extracted role views. Read pages accept their specific read permissions; operational write checks remain unchanged. |
| `backend/core/accounts/role_permissions.py` | 10 `admin_read_permissions`, 37 `PERMISSION_MODULES`, 98 `ADMIN_UI_PERMISSION_CODENAMES`, 307 `set_role_permissions`, 384 `sync_user_admin_permissions`, 415 `get_admin_home_url` | Five admin permission groups, separate ordinary capability labels, real read rights, role modification time and home navigation for readers. Super Admin retains full access. |
| `backend/core/accounts/activity_logging.py` | 9 `log_account_activity` | Optional `metadata` input, empty by default. Existing authentication callers still work. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_roles.html` | 30 `roles-page-intro`, 35 `roles-stats-grid`, 72 `rolesFilterForm`, 89 table headings, 143 `rolePermissionPanel`, 196 `roleFormModal`, 238 `assignAdminModal` | Shared header/KPI/list layout, seven columns, role-dependent actions, read-only drawer, information-only initial modal and separate assignment modal. Remove duplicate, destructive delete and initial assignment controls. |
| `backend/static/components/js/admin_roles.js` | 18 `isolatePanel`, 66 `sync`, 88 `openPanel`, 108 `openAssignment`, 116 `openInfo` | Open the correct view/edit state, show Allowed text instead of editable switches for protected roles, contain keyboard focus, make background content inert and restore it on close. |
| Same file | `permissionPanelForm` submit, `infoForm` submit, `assignmentForm` submit, `rolesFilterForm` | Save through existing URLs, show saving/errors, direct new roles to configuration, assign only after configuration, and auto-apply GET filters. |
| `backend/static/components/css/admin_roles.css` | 1 tokens, 19 `.roles-toolbar`, 57 `.role-permission-panel`, 87 `.permission-panel-feedback`, 117 responsive rules | Replace obsolete/competing Roles-only CSS with compact navy/gold/white styling. Shared page/KPI spacing comes from `admin_layout.css`. Drawer feedback does not cover footer buttons. |
| `backend/templates/partials/admin_sidebar.html` | 32 Marketplace group, 39 Products, 47 Inventory, 55 Orders, 63 Sellers, 110 Facilities | Expose the existing routes to read-only administrators. Preserve Super Admin’s existing seller navigation through Users. |
| `backend/core/modules/marketplace/services/product_access.py` | 6 `user_can_administer_products` | Read permissions use the same academically scoped product dataset. This helper selects data; it does not authorize writes. |
| `backend/core/modules/marketplace/services/order_access.py` | 6 `admin_order_queryset` | View Orders uses the existing order dataset/scope. Keep ambiguous legacy multi-item restrictions. |
| `backend/core/api/views.py` | 204 `serialize_product`, 268 inventory payload, 1296 seller requests, 1309 product monitor | Allow scoped reads through real permissions. Only authorized readers receive recorded stock movement history; write endpoints retain management/approval checks. |
| `backend/core/modules/marketplace/services/inventory_monitor.py` | 16 `inventory_monitor_context`, 44 `can_view_movements`, 84 `inventory_detail` | Inventory read access is distinct from movement-history access. Omit unauthorized history queries, links and data. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 79 inventory actions | Hide unsupported View Product and Stock Movements links for an inventory-only reader. |
| `backend/core/modules/marketplace/templates/marketplace/partials/inventory_detail.html` | 22 `item.can_view_movements` | Render movement history only when authorized. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 1000 `admin_products.js` | Bump the script version so browsers receive the history visibility change. |
| `backend/static/components/js/admin_products.js` | 3298 `populateInventoryHistory` | Hide unavailable history and its heading when the server explicitly says the current reader lacks access. Avoid misleading loading/error messages. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_sellers.html` | 61 pending actions | Read-only seller viewers see requests without Approve/Reject controls. Backend write checks also remain enforced. |
| `backend/core/accounts/tests.py` | 897 access synchronization; 927 onward `RolePermissionsManagementTests` (search class anchor) | Update old assertions to the staged workflow and retained ordinary capabilities. Keep protection/domain/access tests. |
| `backend/core/accounts/test_roles_permissions.py` | 22 `RolesWorkflowTests` | Add isolated workflow, real count, scope, direct-request, audit, migration preservation and query batching regressions. Create empty legacy unmanaged tables only in the test database. |
| `docs/user-management.md`, `CAMPUSHUB_CONTEXT.md` | top update note | Link this guide and record the current Roles behavior. |

The preview scripts, screenshots, test logs and migration integrity snapshot are in `scratch/roles-review/`. They are verification artifacts, not runtime code or application records.

## Required implementation report

| Requested item | Implemented behavior |
| --- | --- |
| 1–3. Folder/file, line, anchor | See the file map above. |
| 4. KPI labels | Total Roles, Assigned Admins, Total Permissions, Unassigned Admins. |
| 5. Table columns | Role, Role Type, Assigned Admins, Access Scope, Status, Last Updated, Actions. |
| 6. Role Type | Existing Super Admin, Marketplace Admin, Facilities Admin and stored `User` are System Roles. Other existing roles remain Custom Roles; no role is renamed by migration. |
| 7. Assigned Admins | Count existing administrator identities: staff/superusers, accounts explicitly assigned to non-base roles, or accounts with actual admin permissions. Ordinary `User` accounts and the separate mobile user table do not inflate this count. Inactive assignments remain assignments, although access is disabled. |
| 8. Access Scope | Full System Access / Marketplace Access / Facilities Access / Custom Access / Base User Access. Program/Major stays on the individual account. |
| 9. Last Updated | Actual role, permission or assignment changes update `Role.updated_at`. Display Philippine time. Unknown legacy modification time remains a dash. Migration time is recorded only for roles whose grants actually change. |
| 10. Super Admin | View only, all available admin definitions show Allowed, protected notice, actual total in the footer and no Save. Direct edits/rename/status/delete/assignment attempts through this workspace are rejected. Shared permission synchronization also maintains full access. |
| 11. Standard User | The stored name remains `User`, displayed as Standard User. Assigned Admins is a dash; base capabilities are read-only; no admin assignment, editing, renaming or deletion. The Standard User name is reserved against duplicate custom creation. |
| 12. Marketplace | Real view/manage product, inventory/movements, view/manage orders, view/manage sellers and approval permissions. Ordinary browsing/buying is removed from this admin editor, not erased from existing grants. No new direct admin stock-edit permission. |
| 13. Facilities | Real View Facilities / View Bookings added. Reuse manage facilities/bookings, approval, schedules and payment/OR rights. Ordinary browse/book capabilities stay outside this editor. |
| 14. User Management | Reuse View Users, Manage Admin Accounts, Manage Roles & Permissions and View User Monitoring. Keep existing endpoint restrictions, including Super Admin-only monitoring. No speculative reset/deactivation permissions. |
| 15. Reports | Analytics is grouped into Reports in the permission drawer. Existing analytics, domain report and generic report permissions remain; existing `can_generate_reports` governs Generate / Export Reports. Navigation still has separate Analytics and Generate Reports pages. |
| 16. System | Reuse Messages, Notifications, Settings, domain exports and separate backup/restore permissions. Built-in Marketplace/Facilities domain restrictions remain. Existing explicit custom backup/restore grants are preserved rather than retroactively revoked. |
| 17. Creation | Save information first with no initial admin selection or grants. Redirect to `?configure=<role UUID>` and open Configure Permissions; after saving usable permissions, Assign Administrators becomes available. |
| 18. Assignment | Eligible accounts only; name, username, current role and Program/Major shown. Confirmation required for changed roles. Inactive roles/accounts and roles with no admin permissions cannot receive new assignments. Marketplace academic validation reuses existing functions. Global Facilities assignment clears inapplicable Program/Major. |
| 19. Enforcement | Existing routes retained. Every role POST requires Manage Roles & Permissions and a transaction. Protected-role/domain checks run server-side. Read rights never substitute for management rights on writes. Final active Super Admin demotion is rejected. |
| 20. Logs | Existing AccountActivity records ROLE_CREATED, ROLE_UPDATED, ROLE_ACTIVATED, ROLE_DEACTIVATED, PERMISSIONS_CHANGED, ADMIN_ROLE_CHANGED and ADMIN_ASSIGNED_TO_ROLE. Structured metadata contains actor, target role/admin, previous and new values. No passwords or tokens. |
| 21. Tests | 126 Django regressions passed, plus two final page/render checks; browser checks at six widths; migration integrity verification passed. Details below. |
| 22. Remaining issues | Existing policies and unrecorded historical dates are described below. No production examples inserted or unrelated mobile flows redesigned. |

## How functions and data flow work

### Reading the page

`admin_roles_page(request)` accepts existing GET search/type/status/page parameters. It loads actual roles and prefetched grants, loads eligible administrators with Program/Major in one batch, groups admins by role name and builds rows using `serialize_role`. Pagination shows ten rows, but KPIs describe the full role/admin dataset. Permission definitions are read from Django’s real Role permission records and filtered to the definitions offered by the administrator editor.

`serialize_role(role, admins)` returns JSON-safe values for both the template and JavaScript: display name/type/scope, real admin count, saved grant codes, allowed domain codes, modification date and action eligibility. Receiving the already grouped admin list avoids a query per role. Reading a role never invents a modification timestamp.

Total Permissions currently counts the 34 available **administrative** definitions in this editor. Ordinary buyer/mobile capabilities, retired compatibility aliases and Django’s generic model CRUD permissions are not presented as additional editable admin actions.

### Saving information

`admin_roles_save(request)` without `operation=assign` accepts name, description and active status. It rejects protected identities and case-insensitive duplicate names. Creating a role leaves its permission relation empty; submitted premature administrator assignments are rejected. Editing information preserves grants. Renaming a custom role updates its existing account role-name references in the same transaction.

The browser uses the existing save URL, includes Django’s CSRF field and redirects a newly created role to Configure Permissions. It preserves the tab-auth query token. A configuration link still works if filtering/pagination would otherwise hide the new row.

### Saving permissions

`admin_role_permissions_save(request)` accepts a real role UUID and administrator permission codes. Super Admin/base edits are rejected. Existing Marketplace/Facilities domain boundaries constrain submitted grants. Assigned roles must retain at least one administrator permission. Ordinary capabilities and unrelated historical role grants are preserved outside this editor.

`set_role_permissions` updates the existing role-to-Permission relation and modification timestamp. `sync_users_for_role` calls the existing `sync_user_admin_permissions` to keep assigned accounts in step with the role. The view writes one PERMISSIONS_CHANGED audit event with previous/new codes.

Annotated example of the important distinction:

```python
# Selecting data and changing data are different permissions.
@admin_read_permissions("can_manage_orders", "can_view_orders")
def admin_orders_page(request):
    ...  # Existing scoped order read.

# The existing update endpoint still requires can_manage_orders.
# Giving someone View Orders does not let their POST change an order.
```

### Assigning administrators

`admin_roles_save` with `operation=assign` delegates to `assign_admins`. Inputs are the role UUID, administrator IDs and confirmation. It validates eligibility, role/account activity, configured admin permissions, current assignments, existing academic rules and the final active Super Admin before changing accounts. Relevant account rows are locked in a consistent order during the transaction. Assignment does not silently turn ordinary students into administrators.

Existing members cannot simply be unchecked and dropped into Standard User. To remove a member from one administrator role, assign that person to another configured role. This keeps administrator identity/access changes explicit. The Users module remains the place for applicable academic scope edits and Super Admin account assignment.

An invalid selection raises `ValidationError`; the shared `role_post` wrapper rolls the transaction back and returns a clear error. The browser keeps the modal open with the message. An authorized successful assignment returns updated role data and refreshes counts.

### Activity records

`audit` passes an event and safe previous/new values to the existing `log_account_activity` function. For an administrator assignment, the activity account is the target administrator, consistent with existing Users activity history, while metadata explicitly identifies the acting admin. General role events belong to the actor’s activity account. `AccountActivity.created_at` supplies the real event timestamp; metadata does not duplicate a fabricated time.

### Read-only inventory access

Specific read permissions use existing Products/Orders academic query scope. Inventory quantity reads and movement-history reads are separate. `inventory_monitor_context` omits movement queries/links when unauthorized. `serialize_product` returns an inventory snapshot but omits movement records and sets `can_view_stock_movements=false` for an inventory-only reader. `populateInventoryHistory` hides that subsection instead of showing misleading loading/error text. Product approvals, saves, stock/order operations and seller approvals retain their existing backend write decorators.

## Backend / API behavior

Existing routes remain `/admin-roles/`, `/admin-roles/save/`, `/admin-roles/permissions/save/`, `/admin-roles/status/` and the legacy delete URL. Resolve names through `reverse()`/Django `{% url %}`, rather than copying literal paths into new code.

Role mutations are POST-only operations with normal CSRF protection. Unauthorized authenticated callers receive 403; malformed/invalid/protected changes return 400; unknown valid role UUIDs return 404. AJAX uses the existing success/message/role JSON contract. Regular forms receive the existing page redirect and Django messages. No new pages, mobile API architecture or authentication system were added.

## Database / migration impact

Applied **accounts.0026_role_management_audit** to the configured `campushub` database. It adds nullable `Role.updated_at`, `AccountActivity.metadata` defaulting to `{}`, and seven real permission definitions. Read grants are added only where corresponding management/approval rights already exist, or to Super Admin. Historical timestamps are not fabricated.

The before/after integrity check confirmed unchanged role identities/descriptions/activity status, user role assignments/account flags/academic scope, product stock/customizations/thresholds and Product/Order/Facility/Booking/AccountActivity counts. All old role/user grants remained; the migration added 14 role read grants and 14 account read grants in this database. No sample accounts, roles, products or transactions were inserted.

The data migration reverse operation deliberately does not revoke grants. A schema rollback is not a way to reconstruct missing historical modification dates. Test changes on a development database before considering migration reversal.

## Tests performed

- `manage.py check`: passed, no issues.
- `manage.py makemigrations --check --dry-run`: passed, no missing model migrations.
- `node --check` for `admin_roles.js` and `admin_products.js`: passed.
- 126 Django tests across `accounts.test_roles_permissions`, `accounts.tests`, `accounts.test_user_management` and `modules.marketplace.test_program_inventory`: passed on a fresh isolated test database.
- Two final role page/filter/query-batching/render checks after the drawer feedback adjustment: passed.
- Chrome at **1920, 1440, 1024, 768, 375 and 320px**: four KPIs, seven columns, contained table scrolling, no page overflow, protected Allowed display, editable domain boundaries, permission save, information-only creation modal, autofocus and auto filters passed. Browser POSTs were intercepted; actual backend mutations were tested separately in Django’s isolated database.
- Actual database migration and before/after integrity verification: passed.

Regression tests cover failed direct protected requests, premature assignments, administrator eligibility/confirmation, final Super Admin protection, Program/BTLED Major validation, inactive role restoration, ordinary capability preservation, auditable changes, scoped data reads, denied operational writes, honest unknown timestamps and additive migration behavior. Query growth is bounded when adding more role rows, instead of growing per row.

## Manual test steps

1. Open Roles & Permissions as Super Admin. Check the description, four KPI labels and seven column headings. Compare actual assigned admin counts with Users.
2. View Super Admin: every offered definition is Allowed, the protected notice appears, the footer uses the actual count and Save is absent. View Standard User: base capabilities only, assigned admins is a dash and no editable/assignment actions.
3. Open Marketplace/Facilities Edit Permissions. Check domain restrictions. Save a safe permission change using a test role/account; refresh and verify it persists. Confirm normal browsing/buying remains unaffected.
4. Add a custom role in a development environment. The first modal has no administrator selector. Save, configure useful permissions, then open Assign Administrators. Confirm ordinary accounts are absent.
5. Attempt assignment without confirmation, to an inactive role, or with no configured permissions. Expect an error with no account change. Attempt final active Super Admin demotion; it must fail.
6. For Marketplace Admin, try missing Program and BTLED missing Major. Update real account scope in Users before assigning. Facilities Admin remains global.
7. Give a test admin only View Inventory or View Orders. Verify scoped reads work and direct save/approve/update requests are forbidden. Movement history needs its own right or an existing product management/approval right.
8. Deactivate a custom role with a test assignment. Verify grants stop working while the role, assignment and audit history remain. Reactivate to restore configured access.
9. Check search, role type, status, Clear Filters and pagination. They auto-apply and combine; no Apply button is needed.
10. On a narrow screen, scroll the table internally; open the permission drawer, switch modules, close with Escape and verify keyboard focus returns. Saving feedback must stay above, rather than on top of, footer actions.

## Debugging / troubleshooting

| Symptom | Check and verified explanation |
| --- | --- |
| New column or metadata missing | Run the accounts migration with the project interpreter from `backend/core`. Do not create a second status or audit table. |
| Role permission save fails | Check Network response status/message, real role UUID, session/CSRF, protected role, existing domain boundaries and whether assigned admins would lose all admin permissions. |
| Assignment list lacks a person | Confirm the account is already an eligible administrator. Normal base/mobile users are intentionally excluded. Check role/account active status and real configuration before assigning. |
| Marketplace reader sees no records | Check the individual account’s real Program/Major and `accounts.academic.scope_products`. Missing/invalid scope fails closed; role names do not supply academic scope. |
| Last Updated shows a dash | The old database did not record a modification timestamp. A dash is honest; the next actual change records a time. Do not substitute creation time or today. |
| Stock movements absent | Verify `can_view_stock_movements`, product management/approval rights and the same academically scoped product. View Inventory alone intentionally does not expose movements. |
| Python object says a restored permission is false | Django caches permissions on a User instance. Test a fresh request or reload a new User object; `refresh_from_db()` does not necessarily clear the permission cache. This was confirmed in test debugging. |
| Repeated `--keepdb` run reports missing Program master records | Migration tests can flush the reused isolated database. The previous reusable database had lost seeded Program data; a fresh test database resolved it. Use the fresh command below, not manual master records in production. |
| Fresh tests lack `campushub_rooms` | Legacy unmanaged models are not created by ordinary Django migrations. RolesWorkflowTests creates empty model-accurate unmanaged tables only in the isolated test database. It does not patch application counts or insert fake room usage. |
| Old symbols/style after refresh | Confirm the new asset version URLs and hard-refresh. Broken checkmark/separator encoding was corrected with JavaScript Unicode escapes and an HTML entity. |

Run the main regression set from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test accounts.test_roles_permissions accounts.tests accounts.test_user_management modules.marketplace.test_program_inventory --noinput
```

## Safe practice exercise

Practice a presentation-only change before trying an RBAC change:

1. Find `rolesFilterForm` in the Roles template; locate the search input placeholder.
2. Temporarily change its placeholder wording. Keep `name="q"`, the form ID, action and method unchanged.
3. Run the page filter test, open the page and type a role name. Verify the URL still has `q=...`, results still filter and the description/KPIs remain unchanged.
4. Restore the original wording and repeat the check.

This demonstrates the data contract: **input name → GET parameter → `admin_roles_page` → serialized records → table**, while the placeholder is only a hint. Changing a permission code, form name or route can break that contract; always inspect the consumer and test before changing it.

## Remaining limitations / policy choices

- Global User Monitoring remains Super Admin-only. Marketplace Admin now has the permitted Program/Major marketplace view described in marketplace-admin-support.md; custom monitoring readers remain denied.
- Existing explicit custom backup/restore grants remain supported by current policy. Marketplace/Facilities built-ins cannot receive those system permissions. A new Super Admin-only backup policy would require a separate authorized policy change.
- No independent Export Reports or Recommendations permission was invented: report export reuses Generate Reports, and no matching administrator recommendations page was found for this UI request.
- Unknown pre-migration modification times and missing pre-existing audit events cannot be reconstructed. Newly recorded events carry structured targets and previous/new values.
- Assign Administrators does not create admin identities or drop removed members into Standard User. Use existing Users account management for administrator creation, applicable academic edits and Super Admin assignment.
- Existing academically scoped custom marketplace roles still need valid individual Program/Major data; a role label alone grants no dataset scope.
- Browser verification used actual test-rendered HTML, local assets and intercepted writes. This task did not rebuild or test Flutter on a physical phone, and does not claim every unrelated CampusHub workflow is fully tested.
