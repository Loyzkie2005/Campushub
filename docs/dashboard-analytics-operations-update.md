# CampusHub Dashboards: Analytics and Operations

## Standalone Admin Notifications page retired; header bell retained - November 5, 2026

### 1. Cause / reason and dependency audit

The user requested removing the separate `/admin-notifications/` page and sidebar entry, retaining the existing header bell. Inspected latest local/unpushed source before editing. The page used the same scoped pending seller-request context as the bell, with a larger limit. It was not a persistent notification-history view: it listed pending requests, not an independent stored notification inbox.

Confirmed page-only controls: **Send Notification** had no event handler, form, composer or sending endpoint; category tabs/checklists filtered existing DOM rows; **Mark all as read** changed DOM classes; **Clear all** hid rows without deleting records. The real seller approval/rejection forms also exist in the shared header and Sellers module, where existing application details, filters, status and history remain available. No essential sending/history backend is removed. The optional page-only category filtering is removed with the page; no replacement filter UI is added.

Important existing limitations: the current bell shows pending **seller requests**, not an implemented booking/order notification feed. It has a pending indicator (`notif-dot`) backed by `pending_seller_requests`, not a persistent numeric unread counter. Mark as seen is browser-DOM state and resets on reload; no existing admin read-state API/model was found. Header rows do not have booking/order detail links or a seller detail link; their existing seller action forms are preserved. This task does not invent those missing features, create tables or change mobile/FCM notification logic. Do not report persistent unread behavior or booking/order deep links as verified functionality.

### 2. Exact files changed / current anchors

| File | Current line / code anchor | Change |
| --- | --- | --- |
| `backend/templates/partials/admin_sidebar.html` | 202 System Settings group | Remove Notifications anchor and its obsolete active-page/empty-group conditions; Messages/Settings retain existing permission gates. |
| `backend/core/accounts/views.py` | 372 `admin_notifications_page` | Replace rendering with a dashboard redirect; retain login/notification-permission decorators. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 453 activity shortcut; 467/478/517 seller shortcuts | Route former notifications links to existing User Monitoring or pending Sellers, retaining text/layout and destination permissions. |
| `backend/templates/dashboard/partials/super_admin_overview.html` | 118 Recent Activity shortcut | Use existing User Monitoring link and its permission instead of the retired page. |
| `backend/static/components/js/admin_notifications.js` | 37 mark-seen; 58 filter branch | Remove only old `data-page-*`/category-input handlers. Existing bell and shared chat handlers remain unchanged. |
| `backend/core/modules/notifications/templates/notifications/pages/admin_notifications.html` | deleted file | Remove unused standalone page after retiring its render path. |
| `backend/static/components/css/admin_notifications.css` | deleted file | Its only runtime consumer was the removed template; shared header styles remain in `admin_header_menus.css`. |
| `backend/core/accounts/tests.py` | 161 retired-route assertion; 274 sidebar assertion | Update existing expectations for redirect and absent navigation. |
| `backend/core/accounts/test_admin_notifications.py` | `AdminNotificationsTests` | Add isolated role-scoped context/render, bookmark/auth, record preservation and existing Sellers API tests; optionally export real role templates for browser checks. |
| `backend/core/accounts/admin_notification_browser_checks.cjs` | role loop | Check actual Bootstrap dropdown/All/Unread/mark-seen behavior on exported isolated Django fixtures, no HTTP writes. |
| `docs/dashboard-analytics-operations-update.md`; `CAMPUSHUB_CONTEXT.md` | this entry / current summary | Explain the dependency audit, function/data flow, tests and limits. |

### 3. Changes made

Remove the sidebar item, standalone template, its private stylesheet and unused page-only JS. Keep `core/urls.py`'s named route as a compatibility redirect rather than breaking bookmarks or internal reverse lookups. Requests to the old URL still pass the existing authentication/permission checks and then redirect to the existing role-aware dashboard. No permanent redirect is cached. A final template reference scan found legacy dashboard shortcuts that would otherwise return users to their dashboard: pending seller review now targets the existing Sellers pending filter; activity shortcuts target existing User Monitoring and use its permission. No labels/layouts or backend grants changed. Shared header markup/styles and its bell controls remain intact, as do all notification/FCM models, endpoints, queues, records and automatic generation.

### 4. How it works: functions, inputs / outputs and data flow

`admin_notifications_page(request)` now returns HTTP302 to `admin_dashboard_page`, without querying/rendering the old page. Login-required and `can_access_notifications` checks execute first, preserving the existing denied-user behavior. `get_admin_home_url` and the named route remain compatible; no role grant changes.

Existing bell data flow is unchanged: `get_notification_context(limit=5, user=actor)` in `accounts/views.py:159` -> `scope_seller_requests()` -> pending-request queryset/count -> `partials/admin_header.html`. The header renders up to three of those requests and the existing indicator. Shared JS handles more-menu, mark-as-seen and All/Unread by changing the existing classes/`hidden` attributes. The same JS file is used by many pages and has chat filtering, so it was retained rather than deleted.

Annotated example: two pending requests visible to Super Admin render two unseen rows. Click Unread, then one row's existing Mark as seen: its DOM class changes to `is-seen` and it hides in Unread. Click All: both rows are visible again. This does **not** update PostgreSQL or decrement a persistent unread count. A Marketplace Admin sees only its allowed program's applications; the existing scope function still controls that query. Existing seller form actions point to the exact application ID; no action was submitted during browser verification.

### 5. Backend / API behavior

Only the old HTML page response changes, from200/render to302/dashboard. API routes/behavior, seller review authorization/scoping, automatic notifications, FCM dispatch and messaging remain unchanged. No bookmark can access a removed template. No new booking/order notification source, sending feature or read-state endpoint is added. Sellers remains the existing destination for full application review/history; unrelated booking/order screens are untouched.

### 6. Database / migration impact

No business-record writes, notification deletions, model changes, migrations or new dependencies. Tests use a created/destroyed guarded local PostgreSQL database. Exported bell fixtures contain isolated test applicants only and live outside the repository. Flutter/Firebase/messaging runtime code is unchanged.

### 7. Tests performed

- **29/29 Chrome interaction checks passed**, with no page errors or HTTP mutations. Covers actual Django-exported Super/Marketplace/Facilities header/sidebar partials, real Bootstrap dropdown open/close, All/Unread, mark seen, existing pending indicator, scoped row counts, empty state and exact seller action URLs. This is fixture browser verification, not an external production login or submitted approval. Captures inspected; shared pre-existing bell styling was not redesigned.
- Initial broader Django run: **135 passed / 137 run in102.133s**, with two failures in unchanged `accounts.test_roles_permissions`. Both reproduced against a separate exported **untouched Git HEAD** in an independently created/destroyed test database: `test_history_reads_existing_role_audit_only_with_pagination_and_no_writes` expects `Cache-Control: no-store` but existing middleware sends `private, no-store, no-cache, must-revalidate, max-age=0`; `test_page_batches_role_permissions_and_admins_and_exports_browser_fixture` expects the group `Reports`, while existing role configuration uses `Reports & Analytics`. Neither source/test was changed for this removal. The isolated baseline lacked its unused static directory and emitted a staticfiles warning; both failures had the same assertions as the working run. Do not claim the complete existing suite passed.
- Final relevant rerun: **111/111 Django tests passed in74.562s**, system checks clean, test database destroyed. Labels: `accounts.tests accounts.test_admin_notifications accounts.test_marketplace_support modules.notifications.test_product_push`. All five new notification tests passed, including repointed dashboard review/activity links and permission gating. This final selection excludes the separately verified pre-existing Roles-suite failures; it does not erase the broader137-test result. Existing product-push tests use mocked dispatch and include intentional failed/unregistered-delivery logs; no real FCM notification was sent.
- JavaScript syntax and scoped whitespace checks pass; final reference searches found no runtime consumers of the removed template, stylesheet or `data-page-*` controls and no template link to the retired page. Existing named route/view/home-fallback references deliberately remain for compatibility. Shared header and chat code were retained.

Run the existing guarded local PostgreSQL runner with `accounts.tests accounts.test_admin_notifications accounts.test_roles_permissions accounts.test_marketplace_support modules.notifications.test_product_push`. Optional `ADMIN_BELL_REVIEW_DIR` exports role fixtures externally. Run `node backend/core/accounts/admin_notification_browser_checks.cjs` with that directory and the existing `CAMPUSHUB_PLAYWRIGHT_MODULE`; copied Bootstrap assets must be in the fixture directory. This installs no new packages and never contacts the working database. Evidence directory: `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261105/admin-notifications-removal/`.

### 8. Remaining limitations / troubleshooting / safe exercise

Existing missing booking/order feeds, record-opening links, persistent unread count and read-state storage are explicitly outside this removal task's no-new-features restriction. Do not mistake the old Send button for a functioning notification composer. Browser fixture testing exercises real rendered partials/Bootstrap/JS but does not establish a live multi-page read-state backend. No mobile/device testing or production login/send/review is performed.

Safe practice: run the isolated tests/browser fixture, open the bell, switch All/Unread, mark a fixture row seen and switch back. Inspect that no non-GET HTTP request occurs. Test an old bookmark while signed in and verify the dashboard redirect; use the isolated runner, not a real applicant approval, for permission/record experiments. If a stale browser still shows the sidebar item, refresh the server-rendered page; no JavaScript redesign or permission grant is required.

## Current: compact shared Attention Required styling - November 3, 2026

### 1. Cause / reason

The user requested compact, consistent Attention Required cards for Super Admin and Marketplace Admin. Confirmed causes: Super Admin's generic priority-card header reserves 112px/144px minimum heights and a divider even though this header now contains only a title; Marketplace's separate header/body padding adds a different gap. Existing role-specific CSS also differs in icon color, row height and action placement. This change affects only Attention Required.

### 2. Exact files changed / current lines and anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `backend/static/components/css/admin_dashboard_attention.css` |3 compact scope/tokens;15 header;25 title;38 body;47 list;56 row;67 icon;75 summary;100 count;112 action;132 hover;138 focus;144 container query | New shared presentation for the existing two cards. Override their older fixed heights/padding within an explicit compact scope. |
| `backend/templates/dashboard/partials/attention_required.html` |1 `dashboard-attention--compact` | Opt in only for `global_dashboard` or the existing Marketplace `executive_attention` flag. Existing loops, IDs, error/empty/loading hooks and label/count/action output stay unchanged. |
| `backend/templates/dashboard/pages/admin_dashboard.html` |30 `admin_dashboard_attention.css` | Load the shared stylesheet after existing Super Admin refinements, only for the global dashboard. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` |19 `admin_dashboard_attention.css` | Load the same stylesheet after existing Marketplace and bundle styles. |
| `backend/core/modules/reports/test_dashboard_periods.py` |401/402 compact marker and stylesheet assertions | Extend the existing Super Admin attention regression. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` |366/367 compact marker and stylesheet assertions | Extend the existing Marketplace attention regression. |
| `docs/dashboard-analytics-operations-update.md`; `docs/dashboard-marketplace-design.md`; `CAMPUSHUB_CONTEXT.md` |Newest compact-attention entries | Explain implementation, verification and a safe practice exercise. |

### 3. Changes made

Both cards now use a natural-height top-left heading with 16px top, 12px side and 12px bottom padding. The body uses 12px side/bottom padding and no header/inner divider. Rows have white surfaces, subtle borders, 12px corners, 8px vertical spacing and a 52px minimum height. The icon is 16px gold `#FCB316`; titles, counts and actions use navy `#1A1851`. Every text element inherits the page's existing bundled Montserrat UI token. Counts keep a small neutral background.

At card widths of at least 460px, the existing three children form icon → grouped title/count → right-aligned action. Below that card width, the action occupies a second row and remains right-aligned. Titles and actions wrap rather than overflowing. The breakpoint uses the card's width, so it also works in the two different dashboard grids. Adjacent cards, dashboard grids, bundle content and welcome headers are unchanged.

### 4. How it works / functions, inputs, outputs and data flow

No runtime function was added or changed. Existing authorized Django attention builders produce `attention_required.items`, each containing its real `key`, `severity`, `label`, `count`, `url` and `action`. The existing shared partial renders those values. Its new class selects the shared stylesheet, which changes geometry and presentation only. Super Admin's existing `renderAttention(attention)` in `admin_dashboard_filter.js` still rebuilds the same row/icon/summary/action classes after refresh, so refreshed rows receive the same styling automatically.

For example, a real low-stock item with count2 still renders `Low Stock Products`, `2` and its existing inventory URL. The stylesheet places the action in column3 when the card is wide enough; it never changes the value or constructs another destination. The narrowly scoped shared file was chosen instead of editing generic `.executive-card-header` rules, because those rules also size unrelated cards. Its container name excludes the generic priority-header height query for this card, and its explicit header reset overrides the existing viewport-based heights.

### 5. Backend / API behavior

Unchanged. Role-specific alert types, academic scope, current inventory rules, permission checks, counts, API payloads, update events and navigation targets are preserved. Loading, error and empty-state visibility remains controlled by existing code. There are no new requests or business rules.

### 6. Database / migration impact

None. No model, migration or working-record changes. Verification used a disposable local PostgreSQL test database and locally rendered fixtures.

### 7. Tests performed

- **12/12 targeted Django tests passed in 5.213 seconds**, with no system-check issues. Coverage includes Super Admin's actual issues/routes, pending-product creator exclusions, inventory/expiry/reservation rules, empty/archived states, schedule conflicts, bounded queries/error handling and destination filters; Marketplace counts, missing scope, action permissions and fixture export; and existing Super Admin section order/header/saved-bundle behavior.
- **777 Chromium checks passed across 32 renders**: populated and empty cards for both roles at 280/320/414/768/1024/1280/1440/1920px. Measured identical header/body padding, zero minimum header height and dividers, 12px heading-to-first-row gap, 52px desktop rows, gold icons, navy Montserrat text, contained content, role-specific counts/URLs, right-aligned actions and responsive wrapping. Existing destination clicks, keyboard focus and hover passed; no JavaScript errors, missing assets or write requests were observed.
- Inspected actual desktop captures for both roles, phone Marketplace, narrow Super Admin and empty Super Admin. Logs, measurements and captures: `scratch/attention-compact-20261103/`. Tracked-change whitespace check passed; Git emitted only the existing line-ending conversion notice.

### 8. Remaining limitations / troubleshooting / safe practice

Browser checks used Django-rendered local fixtures with local request interception, not a live signed-in deployment or physical device. Narrow cards intentionally become taller when labels/actions wrap. The outer grid can still stretch this card to match its neighbor; no unrelated grid or bundle height was changed. No full application suite or unrelated vendor demonstration gate is claimed.

Safe practice: open each authorized dashboard, confirm gold icons and a compact gap under Attention Required, then follow an existing alert link and confirm its destination/filter. Resize to 390px: the action should stay right-aligned inside its row, below the title/count when necessary. Refresh Super Admin and confirm the rebuilt rows retain the same layout. Use existing records and GET navigation only. If old spacing remains, confirm the stylesheet URL ends in `20261103-compact` and loads after the role-specific styles; inspect the compact class and computed header `min-height` before changing any backend count or permission code.

## Current: remove gray descriptions from Super Admin priority headers - November 3, 2026

1. **Cause / reason:** The user clarified that "remove gray" means removing the description text beneath the Attention Required and Suggested Product Bundles headings. The screenshot's background, borders and empty-state explanation are outside this change.
2. **Exact files changed:** `backend/templates/dashboard/partials/attention_required.html:4` (`dashboardAttentionTitle`, in the `global_dashboard` header); `backend/core/modules/marketplace/templates/marketplace/partials/super_recommendation_preview.html:3` (`marketplaceRecommendationsTitle`); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Removed the two static paragraph elements: "Items requiring administrator review or action." and "Current saved recommendations. Evidence and source details are available in Bundle Suggestions." No CSS, heading, View All link, alert row, count, icon or empty-state text changed. The Marketplace Admin header branch and its separate compact bundle partial remain unchanged.
4. **How it works / inputs, outputs and data flow:** Django still renders the existing shared attention partial with `global_dashboard` and `attention_required.items`, and the Super Admin preview with `bundle_analysis.monitor_rows` / `monitor_error`. Only two constant output paragraphs were removed. Existing queryset/context -> template conditions/loops -> actual alerts or saved suggestions remains. For example, a low-stock count2 still renders2 with the same inventory action; an empty bundle list still shows No Bundle Suggestions Yet and its explanation. Template removal was chosen over hiding gray elements broadly so other descriptions/status messages remain readable.
5. **Backend / API behavior:** Unchanged. No permission, query, period, inventory, audit, Apriori, seller-response or endpoint changes.
6. **Database / migration impact:** None. No models, migrations, dependencies, assets or working records changed. Verification used a disposable local PostgreSQL database.
7. **Tests performed:** **4/4 existing Super Admin card/layout checks passed in1.790 seconds**, with no Django system-check issues. These cover priority-section order/saved-bundle refresh, error-versus-empty states, product images/recorded seller response, and limiting saved previews to two without mutating context. Log: `scratch/marketplace-dashboard-layout-20261103/super-card-subtitles.log`. No new tests were added for two static paragraph removals; no new browser render, device or deployment check was performed.
8. **Remaining limitations / troubleshooting / safe practice:** Existing header padding/grid and backgrounds remain; this only removes the requested header descriptions. Refresh a local Super Admin dashboard and confirm both headings and View All remain, the two gray header paragraphs are absent, and alert actions/empty-bundle text still appear. Use existing records or disposable fixtures rather than creating suggestions. If the old descriptions persist, refresh the Django-served page and check these two templates; do not remove every `.executive-section-subtitle` or change global muted colors, because other dashboard sections still use them.

## Current: System Overview inline activity trends - November 3, 2026

This is the accepted System Overview trend behavior. It supersedes percentage badges, neutral N/A/0% indicators and neutral New Activity text. Only Total Users, Total Orders, Total Bookings and Marketplace Sales have trend hooks; the other four cards keep their existing summaries.

### 1. Cause / reason

The original implementation already compared some period metrics, but displayed comparison text below the number and did not calculate registration growth independently of the lifetime account count. The first implementation in this task added database-backed equal-length KPI comparisons. The user's subsequent instructions replace its badge presentation with inline text and hide indicators that do not describe a valid nonzero change.

Confirmed during verification: ordinary SVG `hidden` property assignment did not control an SVG attribute, and a wrapped currency/trend pair can increase natural row height on narrow cards. The final requested text presentation removes the SVG entirely, keeps the original card/grid sizing declarations, and permits normal text wrapping instead of clipping. The actual main values, icons, titles, explanatory basis text and other four summaries remain.

### 2. Exact files changed, current lines and code anchors

Paths are relative to the project root. These are current anchors; older entries below retain historical line numbers.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_kpi_trends.py` | 6 `comparison_dates`; 13 `activity_trend`; 40 `attach_kpi_trends` | Creates the four KPI trend results from existing aggregates. Final presentation outputs blank/hidden for zero activity or rounded-zero percentages, green New Activity for a zero baseline, signed labels and a `visible` flag. Formula and period boundaries are unchanged by the final display refinement. |
| `backend/core/modules/reports/dashboard_periods.py` | 152 KPI dates; 165 account aggregates; 203 prior orders; 209 prior revenue; 295 physical booking comparison; 312 attach | Adds equal-length prior counts to the existing aggregate queries and attaches only the four requested trend results. Existing lifetime values and other sections' comparison fields remain intact. |
| `backend/core/modules/reports/account_metrics.py` | 8 `account_population`; 15 `previous_new` | Optional prior-registration aggregate in the existing web/mobile queries. Other callers retain their previous output when the argument is absent. |
| `backend/core/modules/reports/dashboard_executive.py` | 106 `executive_overview`; 113 `kpi_previous`; 121 `kpi_previous_total` | Reuses the existing physical booking aggregate for the equal-length KPI baseline. Its booking chart/comparison calculation stays separate. |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 19, 64, 94, 109 `kpi_value.html` includes | Wraps only the four requested values with their inline trend partial. Other card markup, destinations, icons and descriptions remain. |
| `backend/templates/dashboard/partials/kpi_value.html` | 1 conditional value row | Keeps the original main value/currency formatting and places the trend immediately after it in a baseline-aligned flex row. |
| `backend/templates/dashboard/partials/kpi_trend.html` | 1 `data-dashboard-trend` | Plain signed text or New Activity; no badge, SVG, border or colored container. Hidden results occupy no layout space. |
| `backend/templates/dashboard/partials/kpi_secondary.html` | 1 conditional comparison caption | Shows `vs. previous period` only for visible trends. Other four metrics retain their previous descriptive/zero-state text. |
| `backend/static/components/css/admin_executive_refinement.css` | 21 trend color variables; 208 value row; 223 plain trend; 252 hidden elements | Baseline flex layout with compact spacing and wrapping; 11px semibold text; explicit transparent/background-free styling; scoped hidden override. Card dimensions, padding, grid and shared typography declarations are untouched. |
| `backend/static/components/js/admin_dashboard_filter.js` | 420 trend lookup; 423 response validation; 427 visible state; 707 failed-report cleanup | Refresh updates adjacent trend text safely, hides absent/invalid/zero values and captions, and hides old trends after a failed full reporting request. No client percentage calculation is introduced. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 29 stylesheet cache key; 621 controller cache key | Loads `20261103-kpi-trends-activity`. |
| `backend/core/modules/reports/test_dashboard_kpi_trends.py` | 21 math cases; 47 database fixtures; 159 equal nonzero visibility | New formula/date/actual-database/API/render/visibility regressions. |
| `backend/core/modules/reports/test_dashboard_kpi_cards.py` | 41 account-basis assertion | Updates a stale expectation from All-time web accounts to the already-existing All web and mobile accounts wording. Does not change production copy. |
| `docs/dashboard-analytics-operations-update.md`; `CAMPUSHUB_CONTEXT.md` | This report / newest KPI entry | Records final behavior, calculations, exact source anchors, verification, limitations and safe practice. |

### 3. Changes made

| Current / previous activity | Visible text | Styling |
| --- | --- | --- |
| Current > 0, previous = 0 | `↗ New Activity` | Green `#15803D`, plain text |
| Positive nonzero percentage | `+X%` | Green `#15803D`, plain text |
| Negative percentage | `−X%` | Red `#B91C1C`, plain text with a true minus sign |
| Both zero, equal nonzero activity, or percentage rounded to exactly 0.00% | Nothing | Trend and caption use display:none; no flex gap for a hidden item |
| Missing/null/invalid reporting data or failed full request | Nothing | No N/A or invented percentage; existing stale-data/error behavior remains |

The main number remains large, bold navy `#1A1851`, with Montserrat inherited from the existing Super Admin scope. The trend sits immediately to its right and aligns to its baseline. `vs. previous period` stays below only when a trend is visible. Active Sellers, Total Products, Total Facilities and Pending Approvals receive no percentages or new visibility logic. Main values continue to describe their existing snapshot or selected-period basis.

### 4. How it works: functions, inputs, outputs and data flow

`comparison_dates(period)` receives the selected AnalyticsPeriod and returns inclusive prior dates of exactly the same number of days, ending the day before the current range begins. For example, March 1-31 compares against January 29-February 28, rather than comparing 31 days against a 28-day month. Existing non-KPI charts retain their previous comparison metadata. `build_dashboard_data` already runs inside the Asia/Manila timezone override, so account registration, order submission, booking submission and recognized revenue boundaries all use Philippine local dates.

`account_population(..., previous_range=...)` adds prior web `date_joined` and mobile `created_at` counts to its existing two aggregate queries. Orders use `created_at`. Physical bookings use the existing booking population that excludes academic schedule blocks and specialized service requests. Sales reuse the canonical completed AND paid queryset and its existing completed/paid/created timestamp precedence. No stock, payment, approval or booking workflow is changed.

`attach_kpi_trends` receives those current/prior aggregates, including Decimal sales amounts, and makes no database queries. `activity_trend` retains the existing formula `((current - previous) / previous) * 100`, returns a two-decimal numeric `percentage_change` or null for a zero denominator, and prepares the display fields `label`, `direction`, `visible` and an explanation naming the population, actual dates and values. A display rounded to zero is hidden consistently in server HTML and refresh. A zero baseline with positive activity is a labelled first-activity state, never an invented percentage.

```text
Existing period controls -> authorized Django view/API -> existing aggregates
  -> equal-length KPI baselines -> four optional metric.trend results
  -> value partial + plain inline trend + conditional comparison caption
Refresh -> same API -> validate received trend fields -> show/hide text and caption
Full request failure -> keep actual last loaded main values/stale message -> hide trends
```

The browser consumes server-supplied percentages/labels; it does not compute growth. It checks finite current/prior values and a valid nonzero percentage, with the explicit New Activity exception. Hidden elements are retained in the DOM for later refresh but have zero rendered width and no caption/placeholder. Recovery can show a valid indicator again. The final refinement's source hashes confirm `dashboard_periods.py`, `account_metrics.py` and `dashboard_executive.py` were not altered while changing the visibility rules.

Annotated example, documentation/test data only: a lifetime account count of 11 can display `11  +600%` when seven accounts registered in the selected period and one registered in the prior period. The 600% compares 7 with 1; it does not claim the lifetime total grew from 1 to 11. If both periods register seven, the main count remains 11 with no trend/caption. If the prior period has zero and the selected period has seven, show `11  ↗ New Activity`. These example values are not hardcoded into the application.

### 5. Backend / API behavior

The existing Dashboard API URL, authentication, tab-token integration, role gates and refresh/filter requests remain. Only four existing KPI objects gain a nested `trend`; their original value, secondary text, percentage/comparison fields remain for compatibility. The nested trend carries exact current/prior activity values, percentage/null, selected/prior dates, day count, timezone and display fields. The other four KPI objects do not gain trends.

Total Users remains all recorded web/mobile accounts, including disabled records, while growth compares registration events. No web/mobile identities are merged. Active Sellers remains a current approved-access snapshot with recorded approvals; Products remains current catalog plus products added; Facilities retains its current status summary; Pending Approvals retains its current queue count. Green/red indicates activity direction, not an automatic judgement that every operational increase/decrease is beneficial.

### 6. Database / migration impact

None. No models, migrations, working records, business workflows, dependencies or API endpoints changed. New trend baselines reuse existing aggregates rather than adding per-record or extra queries; the existing dashboard query-budget regression passes. PostgreSQL verification runs only in a uniquely named disposable local test database, which is destroyed afterward. No backend restart, production deployment, mobile edit or user-facing app launch was performed.

### 7. Tests performed

- **58/58 Django tests passed** in 23.805 seconds across `test_dashboard_kpi_trends`, `test_dashboard_periods`, `test_dashboard_marketplace_parity` and `test_dashboard_kpi_cards`. Django system checks were clean, and the disposable PostgreSQL database was destroyed. Coverage includes exact current/prior populations, disabled/mobile registrations, lifetime separation, completed-and-paid eligibility, submission versus completion dates, service exclusion, zero/new/equal/declining states, rounded-zero visibility, month-end/leap/custom ranges, Manila midnight, permissions and the unchanged query budget.
- JavaScript syntax checks passed for the application controller and isolated browser harness. Three upstream reporting-source hashes match the state before the final visibility refinement. The browser harness uses actual isolated Django-rendered pages and JSON; deliberately malformed/missing transport cases are test-only clones used to verify hiding rather than fabricated application data.
- **1,496/1,496 headless Chrome checks passed across 20 renders**, with screenshot inspection recorded in `scratch/dashboard-kpi-trends-20261103/browser.log`, `browser-results.json` and the actual render PNGs. It checks eight cards, four eligible trend hooks, plain colors/no badge styling, navy main values, inline baseline layout, hidden zero-width indicators/captions, zero/equal/new/declining states, recovery, malformed data, request errors, retained tab auth and responsive layouts from 280 through 1920px. Desktop card geometry and original sizing rules are compared against the saved pre-change presentation; narrow cards may naturally wrap text while retaining the same grid and sizing rules. Actual mixed, equal-growth and New Activity captures were visually inspected.
- The optional design-kit command was attempted and reported **`RESULT: 0/52 checks passed  =  0%`**. It could not verify its own examples because `python3`, Playwright/modules and example files are unavailable in that kit installation. This is not an application pass or a WCAG score. The complete failure list is in `optional-web-kit-gate.log`; no unrelated kit installation or application-rule suppression was performed.

Reproduce from the project root:

```powershell
# Disposable local PostgreSQL only; the runner verifies localhost:5432.
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_dashboard_kpi_trends modules.reports.test_dashboard_periods modules.reports.test_dashboard_marketplace_parity modules.reports.test_dashboard_kpi_cards
node --check backend/static/components/js/admin_dashboard_filter.js
# Set KPI_TREND_REVIEW_DIR to scratch/dashboard-kpi-trends-20261103 before the
# Django run to regenerate real fixture HTML/JSON, then run the local harness:
node scratch/dashboard-kpi-trends-20261103/check.cjs
```

### 8. Remaining limitations, troubleshooting and safe practice

No production deployment/live-account write or complete accessibility audit was performed. The optional kit gate remains unavailable. The original card dimensions/minimum sizes, grid, icons and font rules remain; responsive text wrapping can increase natural content height when a currency value and trend cannot fit together. Values are not clipped or reduced to make a misleading fixed-height claim. A missing report hides its trend rather than treating it as zero activity. A failed full refresh preserves the existing last-loaded main numbers with the stale notice and removes their trends until recovery.

If N/A or 0% persists, first check that the latest stylesheet/controller cache key loaded and inspect the server's `trend.visible`; do not change the reporting totals. If a caption remains after hiding a trend, inspect both elements' hidden attributes and the scoped hidden CSS override. If a user-total percentage seems different from the lifetime count, inspect the registration values in the trend explanation. If a month-end comparison differs from another chart, verify its explicitly separate equal-length KPI dates before changing unrelated analytics.

Safe exercise: run the new math test and change its test-only `(150, 100)` pair to `(200, 100)`, updating the expected visible label to `+100%`. Restore it afterward. Then run `test_equal_nonzero_activity_hides_trends_and_captions_without_na` and inspect its saved `steady.html`: all eight values remain, the four trend/caption elements are hidden, and the other summaries remain visible. Refresh between the real `mixed`, `steady`, `empty` and `new` fixture payloads with the harness and verify indicators reappear only for meaningful changes. Do not create working users, orders, bookings or sales for this exercise.

## Current: Dashboard / Marketplace metric reconciliation - November 2, 2026

### 1. Cause / reason and confirmed discrepancies

Read-only reconciliation against the **currently configured Django PostgreSQL connection** confirmed the user's Last 30 Days figures for October 4–November 2, 2026: **3 submitted orders, ₱0.00 recognized revenue, no qualifying completed-paid orders, and 1 low-stock product**. Those records and definitions are preserved.

| Metric | Confirmed previous behavior | Refined behavior |
| --- | --- | --- |
| Dashboard Active Sellers | 0: web-only current access; omitted two approved mobile sellers | 2 current web/mobile seller accounts; basis label explicitly describes current access |
| Marketplace seller KPI | 1: approved sellers with listing activity or completed-paid sales in selected dates | Same 1; renamed **Sellers Active in Period**, preserving the existing period-activity definition |
| Dashboard Total Users | 4 web records; secondary count 1 new web registration | 11 records = 4 web + 7 mobile; secondary count 7 new registrations = 1 web + 6 mobile |
| Users Overview / Users Analytics registrations | Already counted 7 registrations across both sources | Unchanged; now agrees with the System Overview secondary count |
| Average Order Value | Dashboard API returned 0 for no qualifying orders; executive summary hid AOV and repeated Active Sellers | Shared undefined-denominator handling returns null and shows N/A. The existing third Marketplace summary slot now displays AOV; Active Sellers stays in System Overview |
| View Analytics destinations | Already carried correct module and exact custom dates | Preserved and verified through all four real destinations |

Active seller **access** is a current snapshot, while seller **activity** depends on selected dates; forcing these two values to agree would erase a useful distinction. Total Users is a count of account records, including disabled records, not a deduplicated count of people. New Users means records registered within the applied dates, not currently enabled users. No identities were merged by name, email or equal numeric primary keys.

### 2. Exact files changed, current lines and anchors

| File relative to project root | Current line / anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/reporting_metrics.py` | 5 `average_order_value`; 10 `approved_seller_request_filter`; 17 `seller_access_snapshot` | Shared Decimal AOV and approved-owner predicates; current seller snapshot reuses account aggregates and preserves the Dashboard's legacy enabled Seller-role fallback. These are reporting helpers, not permission grants. |
| `backend/core/modules/reports/account_metrics.py` | 8 `account_population`; nested `fields` | Two source-aware aggregates supply total/new/enabled records and optional seller counts. Correlated Exists predicates avoid duplicating accounts with multiple requests and keep web/mobile IDs separate. |
| `backend/core/modules/reports/dashboard_periods.py` | 163 population; 168 seller snapshot; 211 AOV; 246 undefined comparison branch; `marketplace.average_order_value` output | Corrects web/mobile coverage, uses shared AOV, and emits explicit N/A/null without inventing a percentage for a missing average. Keeps the existing query budget. |
| `backend/core/modules/reports/analytics_sections.py` | 393–396 Super Admin account population | Reuses the same account definitions for Users Analytics, including suspension-aware enabled counts for both sources. Legacy-role branch remains. |
| `backend/core/modules/marketplace/services/analytics.py` | 384/395 approved-owner helpers; 734 AOV KPI | Reuses approval predicates and AOV. Super Admin refined output uses null with no qualifying orders; legacy non-refined formatting remains compatible. |
| `backend/core/modules/reports/superadmin_analytics.py` | 68/69 current/prior AOV | Uses the same helper for the detailed equal-length comparison; actual zero-value qualifying orders remain zero. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 5 seller KPI label | Names the existing metric Sellers Active in Period on Super Admin only, retaining its existing explanatory subtitle. |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 18 user basis; 33 seller basis | Clarifies web/mobile populations under existing values. |
| `backend/templates/dashboard/partials/sales_overview.html` | 48 metric loop; 69 comparison; removed executive seller duplicate | Restores the already-calculated AOV in the existing three-card Marketplace summary and supports undefined comparison text. Sales trend and product ranking structures are unchanged. |
| `backend/static/components/js/admin_dashboard_filter.js` | 439 comparison rendering | Keeps the server's undefined-average explanation through API refresh/filter changes. Existing value/currency rendering shows N/A without a peso prefix. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 621 controller cache key | Loads `20261102-metric-parity`. |
| `backend/core/modules/reports/test_dashboard_marketplace_parity.py` | parity test class and named tests | Tests source collisions, suspension, snapshots versus registrations, undefined/true-zero AOV, date-preserving tab destinations, permissions and Philippine midnight boundaries. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 107 empty-average expectation | Updates the intended undefined-AOV regression expectation to N/A. |
| This guide, `docs/superadmin-analytics-module.md`, `CAMPUSHUB_CONTEXT.md` | Current parity entries | Documents definitions, verification evidence, troubleshooting and safe learning steps. |

### 3. Changes made

Dashboard retains quick system-wide monitoring, eight System Overview KPIs, compact sales trend and its existing top-five product chart. Its Marketplace summary still contains three cards: sales, completed-paid orders and the existing AOV metric. Detailed category, seller, submission, payment/receiving and prior-period analysis stay in Analytics. The duplicated Marketplace Active Sellers card is removed because that snapshot remains in System Overview.

No CSS, palette, type family, chart dimensions, product-ranking limit, workflow or permission was redesigned. The shared population includes web and Flutter account records. Enabled counts exclude both inactive and suspended records. Dashboard's current seller access now includes eligible mobile sellers; Marketplace's seller performance/ranking remains period-specific and keeps stable account-source IDs.

### 4. Functions, inputs/outputs and data flow

`account_population(period, include_sellers=False)` takes the existing period object and returns separate `web` and `mobile` count dictionaries. Web registration uses `User.date_joined`; Flutter registration uses `CampusHubUser.created_at`. Both use the selected application-local date interval. `total` is a current record snapshot; `new` is selected-period registrations; `active` is currently enabled and not suspended. Users Analytics reuses these dictionaries. Existing `registration_daily_counts()` still feeds Dashboard daily registration trends and Users Analytics monthly buckets, using the same source dates.

Dashboard requests `include_sellers=True`. Each source aggregate uses Exists over approved, nonsuspended requests and active, nonsuspended owners. `approved_seller_request_filter(owner)` is also used by Marketplace Analytics' approved seller-ID helpers, preserving their existing academic/user scope. Web and mobile keys are evaluated in their own tables, so web ID 4 and mobile ID 4 count as two account records. The Dashboard's prior enabled legacy Seller-role fallback remains for compatibility; it does not assign seller status or change account type. Seller approval-date secondary counts remain based only on recorded review timestamps.

`seller_access_snapshot(period, population=...)` reuses those already-loaded counts instead of adding account-by-account queries. Dashboard access remains current even for sellers with no period activity. Analytics `_seller_performance()` retains its listing-update/submission or eligible-sale activity rule and source-prefixed identities; only its KPI label changes. A current idle approved seller is therefore included in Dashboard access but excluded from period activity.

`average_order_value(revenue, qualifying_orders)` returns a Decimal division when the denominator exists, otherwise None. Both pages already share `valid_sales_queryset()` for eligible completed-paid, positive-quantity records and recognized timestamps; that rule is untouched. Dashboard current/prior average formatting and Analytics' comparison reuse the AOV helper. No qualifying orders yields API null / visible N/A; a real completed-paid zero-price order yields a real ₱0.00 average. An empty current period never becomes an invented -100% AOV change. The executive summary reuses its existing AOV card/template and refresh hooks.

Annotated isolated example: a web record and mobile record with the same numeric ID count as two records. Two current seller-access records with no selected-period listing/sale activity produce Dashboard access 2 and Analytics activity 0. Three unpaid submissions produce order volume 3, recognized revenue 0 and AOV N/A. One additional eligible zero-price order makes AOV 0, not N/A. These examples are covered by disposable tests, not hardcoded working figures.

### 5. Backend / API behavior

No endpoint, permission, account type, seller approval workflow, order/payment/delivery lifecycle, inventory calculation, forecast or migration changed. The existing Super Admin Dashboard API now returns null for undefined AOV; its server-rendered and refreshed card handle that value. Existing non-refined Marketplace/legacy formatting remains compatible. All four View Analytics links retain their existing `module`, `date_from` and `date_to` mapping. Global counts remain protected by the existing Super Admin guard; actor-scoped Analytics queries keep existing server enforcement.

The account and seller population work is combined into two aggregate queries. The existing ≤39-query Dashboard regression and constant query count as transaction volume grows still pass; the limit was not relaxed. Initial verification exposed an over-budget draft, which was corrected by folding seller counts into the account aggregates.

### 6. Database / migration impact

No model, schema or migration changes. The configured working PostgreSQL audit uses `SET TRANSACTION READ ONLY` and verifies unchanged row counts for accounts, orders, products, seller requests, bookings, SKUs and movements. It reconciles old web-only definitions against the same unchanged records rather than reconstructing historical status. No production restart, deployment, permanent environment edit or working-record repair was needed.

Regression and real-browser HTTP tests create/destroy disposable **local test databases**. Sessions and fixture records used by that browser belong only to those databases. No real account or order was created to force a screenshot.

### 7. Tests performed

- **148/148 Django regression tests passed** in 75.796 seconds across Super Admin Analytics, Marketplace Analytics, Dashboard periods/marketplace/executive summaries and cross-page parity tests. Covers eligibility, source IDs, suspensions, zero-price versus undefined AOV, grouping/date scopes, records, links, role denial and the existing query budget. A separate added Philippine-midnight regression passed in 0.292 seconds: 00:30 local belongs to today, 23:30 belongs to yesterday, consistently for submitted orders, recognized sales and web/mobile registrations.
- **54/54 authenticated real HTTP browser checks passed** in a disposable PostgreSQL-backed Django LiveServer test at 1440px and 390px; the test took 24.624 seconds. All application pages, static files and APIs were real server requests; only vendor CDN assets used existing local copies. Checks cover initial N/A, populated AOV, populated-to-empty API filtering, Refresh, actual sales/ranking chart values, current user/seller populations, four real View Analytics destinations and 403 responses for an unrelated admin role. Final desktop/phone screenshots were produced; the desktop render was visually inspected. Evidence: `scratch/dashboard-marketplace-parity-20261102/live-result.json`, `live_browser.cjs`, `test_live_parity.py`, `run_live.py`, and `live-dashboard-*.png`.
- **Configured working PostgreSQL under READ ONLY:** Dashboard HTML/API and all four linked Analytics views returned HTTP 200. A non-Super Admin Dashboard API request was denied. Today, Last 7 Days and Last 30 Days share user populations/registration counts and matching current submission/revenue cohorts. Last 30 Days preserves 3 submitted orders, zero recognized sales and 1 low-stock product, and now reports 11 accounts, 7 registrations, current seller access 2 and period seller activity 1. Evidence: `audit.py` and `after.json` in the same scratch folder. Unchanged table counts and READ ONLY protection confirm no working writes.
- Static validation: controller `node --check` and scoped `git diff --check` passed. No CSS change required a new contrast claim; no accessibility certification is claimed.

Run the regression suite from the project root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests modules.reports.test_dashboard_periods modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_executive modules.reports.test_dashboard_marketplace_parity
```

For the real HTTP/browser test, run `backend/core/venv/Scripts/python.exe -B scratch/dashboard-marketplace-parity-20261102/run_live.py`. It verifies the disposable database name before fixture writes and uses cascade-aware cleanup for the project's unmanaged test tables. For the current configured database, `audit.py` is read-only and records its explicit November 2 reporting date; update that audit date intentionally for a later reconciliation rather than treating this report's figures as permanent constants.

### 8. Remaining limitations, troubleshooting and safe practice

Account records are not deduplicated people. There is no verified cross-source identity mapping authorizing an email/name merge. Seller access and period activity intentionally differ; existing legacy enabled Seller-role compatibility is retained on Dashboard. Registration counts describe recorded account creation dates, not daily active people. Current status fields do not reconstruct historical state changes.

The live-browser check used a real disposable server, not the deployed authenticated production site. Configured working data was verified read-only through the actual views/API and metric builders. Future records can legitimately change these dated figures. Deployment was not performed.

If the Dashboard still shows old AOV formatting after Refresh, reload and inspect the `20261102-metric-parity` controller key. If seller totals differ, compare the current-access basis against Sellers Active in Period and verify account source, approval, enabled/suspended status and actual listing/sale dates. For user differences, compare the same exact local dates and both registration fields. Do not change records merely to make two different cohort definitions agree.

Safe exercise: select a read-only custom range on Dashboard and follow each View Analytics link. Verify the tab and exact dates; compare current submissions and completed-paid revenue separately. Inspect Total Users as the current combined account total and New Users as only selected-date registrations. Choose an empty-sales period and confirm AOV N/A, then a populated period and compare revenue / qualifying completed-paid orders. For code practice, trace `include_sellers=True` through `account_population()` into `seller_access_snapshot()`, and trace a None average into the existing card and refresh renderer. Temporarily shorten only the user KPI basis label locally, inspect both widths, then restore it. No working-record edits are necessary.

## Current: Activity row context and semantic status — November 1, 2026

### 1. Cause / reason

The existing compact preview displayed action, time, result and an icon-only details button. Its existing server-provided `module` and responsible `user` fields were validated but omitted from the visible rows. Success/Failed shared a neutral badge reset in the refinement stylesheet. The first and last rows also had different vertical padding from middle rows.

The latest request explicitly permits semantic Success/Failed colors in this card. This narrow exception supersedes the earlier neutral-only badge preference for the activity preview; it does not restyle statuses elsewhere.

### 2. Exact files changed, current lines and nearby anchors

| File and current line | Anchor / change |
| --- | --- |
| `backend/templates/dashboard/partials/system_activity_preview.html:10` | `audit-event-icon`: add a decorative audit-record SVG, group action/module/time/responsible user, then render status and the existing details button with a visible View label. Lines 14–18 contain the optional user and permission-gated controls. Existing card location, header, View All, empty/error states and dialog remain. |
| `backend/static/components/js/admin_dashboard_activities.js:26` | `render(rows)`: build the same row structure for initial JSON rendering and Refresh. Lines 34–50 build the icon and real audit context; lines 51–65 build status and labeled View. Keep text-node rendering and existing validation. |
| `backend/static/components/css/admin_dashboard_operations.css:12` | Add card-scoped semantic color variables. Lines 24–40 define uniform 13px row padding, dividers, responsive content/controls and scoped green/red badges. Line 45 adds the View label's button sizing; lines 52–56 keep the wide-column row alignment. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Version operations CSS as `20261101-activity-context`; line 623 versions the matching activity script. |
| `backend/core/modules/reports/test_dashboard_operations.py:110` | Extend an existing rendering assertion to verify the icon, Services module and resolved actor. Lines 154–156 optionally export each real fixture activity's own protected detail response for browser verification. No new runtime query/API behavior. |
| `scratch/activity-context-20261101/check.cjs:1` | Browser harness for actual isolated Django fixture exports, row geometry/colors and every View destination/timestamp. |
| `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3` | Record this current implementation, data flow, tests and safe practice. |

### 3. Changes made

Wide rows read left to right: event icon → action with module/date and responsible user → result badge → View action. The neutral clipboard icon means a recorded audit event; it does not invent an event category or result. The responsible user comes from the existing server-resolved actor field, not the affected account's name. Empty or `Unknown` identities are omitted from the preview's By line; their original data remains in the response/details.

Every row has 13px top/bottom padding, including the first and last. Resting backgrounds are uniform and transparent against the card surface, with subtle separators. Hover/focus uses the existing quiet neutral highlight. Success uses dark green text on a pale green surface; Failed uses dark red on pale red. Result text stays explicit, and an unrecorded result retains the neutral Not recorded state. The high-specificity color rules are restricted to this card and override the shared neutral reset without changing that shared stylesheet.

At a card content width of at least 480px, icon, content, badge and View align across the row. Narrow cards place controls below the text, with wrapping when needed. No fields are hidden to fit. The existing card remains directly below Users by Type with its existing external 16px gap and View All Activities route.

### 4. How it works / functions, inputs, outputs and data flow

Unchanged server flow: permission-checked dashboard view/API → `executive_overview()` in `backend/core/modules/reports/dashboard_executive.py:98` → selected-period `AccountActivity` query → `format_activities()` allowlist → `executive.activities` → initial Django template / refreshed JavaScript list. The query still returns up to five eligible actual events, newest first, and retains the existing routine sign-in/sign-out exclusion from this oversight preview. Full history remains in the existing activity table.

`render(rows)` takes the unchanged fields `time`, `user`, `activity`, `module`, `result` and `details_url`. It creates DOM elements with text nodes, shows the available server-resolved actor and appends the same recorded result. Neither the renderer nor CSS writes audit data or infers a missing actor.

```javascript
// Values already resolved and allowlisted by Django.
const module = element('span', row.module); // Existing module, e.g. Services.
const user = element('span', `By ${row.user}`); // Only for an available identity.
time.dateTime = row.time; // Original timestamp, unchanged.
button.dataset.activityDetailUrl = row.details_url; // Exact existing record URL.
```

`timeLabel()` still formats the same recorded timestamp in the section's application timezone. `detailURL()` still validates the same-origin protected audit endpoint and attaches the existing tab token. `showDetails(button)` still fetches that particular button's record, renders allowlisted details, handles failures and restores focus when closed. Only the button's visible label and surrounding row presentation changed.

### 5. Backend / API behavior

No runtime Python, audit projection, sorting, selected-period, authentication, permission, endpoint or audit-writing change. The existing `can_view_user_monitoring` condition still gates View All, View buttons and the dialog, while the detail API independently enforces authorization. Full activity-table behavior is unchanged. The two semantic outcomes are presentation of existing recorded values, never a recalculation of success/failure.

### 6. Database / migration impact

None. No PostgreSQL records, models or migrations changed. Tests used the existing disposable local PostgreSQL runner and destroyed its test database afterward. Browser responses came from those isolated ORM fixtures; all non-GET browser requests were blocked. No live events, environment, deployment or application server restart were changed.

### 7. Tests performed

- **17/17 Django tests passed in 7.679 seconds**: existing `modules.reports.test_dashboard_operations` and `modules.reports.test_dashboard_services`, run with `backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py`. Django system checks were clean. Coverage includes newest-first five-event limits, preserved history, responsible actor resolution, application-local timestamps, allowlisted detail fields, denied unauthorized requests and read-only detail methods.
- **845/845 Chromium checks passed across 12 renders**, run with `node scratch/activity-context-20261101/check.cjs`, at widths 280, 320, 390, 768, 1024, 1280, 1440 and 1920px. Checked exact record values/order/URLs, module/responsible user, event icon and View label, uniform 13px padding, dividers, consistent resting surfaces, semantic badge colors, measured badge text contrast of at least 4.5:1, hover, wide-row alignment, narrow wrapping, no page overflow, populated/empty states, Refresh/error/retry and no-JavaScript rendering.
- Opened **all five** View actions by keyboard at desktop and phone widths. For each, checked the exact requested detail URL and its own real actor/action/module/result/timestamp, then verified focus returned on close. No browser writes or page errors occurred. The harness waits for each matching detail response and dialog cleanup to avoid treating a prior dialog's content as the next record.
- Inspected final desktop/phone activity screenshots. Evidence: `scratch/activity-context-20261101/browser-result.json`, `activities-populated-1440.png`, `activities-populated-390.png`, isolated `activity-details.json` and the harness. Screenshots contain test-fixture records, not production examples.
- JavaScript syntax and scoped whitespace checks passed. Generic skill-kit gates/full accessibility certification and other browsers/devices were not verified.

### 8. Remaining limitations / troubleshooting / safe practice

The preview retains the existing selected-period eligibility rules and five-record maximum. Narrow rows grow vertically to keep all available text and controls readable. A missing/unknown actor cannot be reconstructed by presentation code. The generic event icon deliberately avoids guessing an event subtype.

If the old icon-only layout or neutral badges persist, reload and verify both operations CSS and activity JavaScript URLs use `20261101-activity-context`. Inspect the actual computed card-scoped badge styles because the shared refinement stylesheet still has its older neutral reset. If View fails, inspect that row's `data-activity-detail-url`, tab session and the existing API error; preserve authorization failures instead of bypassing them. Never modify an audit record to fix a display problem.

Safe practice: choose a period with existing events, compare each visible action/module/time/By line with the full activity table, and open the first and last View buttons. Verify each detail timestamp and result matches its own row. Close using the keyboard and confirm focus returns, then resize to phone width and Refresh. These checks require no saved data changes.

## Current: Recent System Activities in the Users column — October 31, 2026

### 1. Cause / reason

Confirmed in the template: `system_activity_preview.html` was included after the entire two-column domain grid. This placed a full-width activity table below both Services and Users, leaving the shorter Users column empty beside Services. Its six-column table was also too dense for the requested right-column position.

The preview now follows Users by Type inside the existing Users stack. This reuses the available right-column space without changing the Services cards, Marketplace, Facilities, chart sizes or domain-grid structure. The existing horizontal Services/Users gap was already 16px and remains 16px; no claim is made that this already-small gutter was reduced. The relocated preview removes the separate full-width section and its extra section spacing. Both columns keep natural content heights.

### 2. Exact files changed, current lines and nearby anchors

| File and current line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/executive_dashboard.html:43` | After the Services and Users includes, remove the old standalone activity include. |
| `backend/templates/dashboard/partials/super_users_overview.html:40` | Add the existing `system_activity_preview.html` include immediately after the Users by Type article. |
| `backend/templates/dashboard/partials/system_activity_preview.html:7` | Keep `data-activities-table` as the existing visibility hook; replace its table with an ordered `audit-preview-list`. Lines 9–12 render action, date/time, result and the existing permission-gated detail button. The header, View All route, empty/error states and dialog remain. |
| `backend/static/components/js/admin_dashboard_activities.js:26` | `render(rows)` now creates matching `li`, `strong`, metadata and result nodes instead of table rows/cells. Lines 33–58 contain the presentation changes; the existing validation, event hooks and detail controller remain. |
| `backend/static/components/css/admin_dashboard_operations.css:19` | Replace obsolete audit-table rules with wrapping list rows, quiet separators and neutral result text. Line 295 begins the scoped Users-column card rules: 16px padding, zero external margin and the shared border/radius/surface tokens. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Version the operations CSS as `20261031-activities-list`; line 623 versions the matching activity script. |
| `backend/core/modules/reports/test_dashboard_operations.py:108` | Update existing presentation expectations to the semantic list and result label; line 127 checks Users by Type precedes Activities. Existing audit/history/permission tests remain. |
| `scratch/dashboard-activities-column-20261031/check.cjs:1` | Local browser verification harness using actual isolated Django fixture exports; no production records or invented dashboard values. |
| `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3` | Record this implementation, verification, data flow and current layout decision. |

### 3. Changes made

Each activity shows its readable action first, then recorded local date/time and the recorded result. Success, Failed and Not recorded remain explicit text. The existing eye button opens the same Activity Details dialog; performed-by and module remain in its existing response and detail fields. View All Activities still opens the existing full system activity table for authorized users.

The preview uses one bordered card with compact rows and no fixed-height filler or internal scrolling. Long values wrap. Its header action wraps below the title on narrow screens. The Users stack supplies the existing 16px card gap; the audit card has no additional top/bottom section margin. Services/Users retain equal-width desktop columns and the existing responsive breakpoint. This fills space beside Services rather than stretching either column to match its neighbor.

### 4. How it works / functions, inputs, outputs and data flow

Unchanged server flow: permission-checked `admin_dashboard_page()` / `admin_dashboard_api()` → `executive_overview()` in `backend/core/modules/reports/dashboard_executive.py:98` → selected-period `AccountActivity` query → existing `format_activities()` allowlist → `executive.activities` → initial Django list or refreshed JavaScript list.

`executive_overview()` still returns at most five eligible records, newest first. Routine successful sign-ins/sign-outs still remain in full history and are excluded from this oversight preview under the existing rule. The selected global reporting period remains authoritative; this change does not turn the preview into an all-time feed.

`render(rows)` takes the existing array containing `time`, `user`, `activity`, `module`, `result` and `details_url`. It validates the same inputs, creates text nodes safely and replaces only `[data-executive-activities]` children. The output is now a semantic ordered list. `timeLabel()` still formats timestamps in the section's application timezone. `fail()` still hides the list/empty state and shows the real error message. `showDetails(button)` still fetches the protected existing detail URL, renders allowlisted fields, and restores keyboard focus when closed.

Annotated example of the existing data mapping:

```javascript
// row is one real server-provided activity, not a hardcoded dashboard record.
const action = element('strong', row.activity); // Human-readable recorded action.
const time = element('time', timeLabel(row.time));
time.dateTime = row.time; // Preserve the original machine-readable timestamp.
// The recorded result stays explicit; null displays "Not recorded".
```

This approach keeps the existing data contract and protected details flow while fitting the narrow column. The legacy `data-activities-table` name is intentionally retained as an internal visibility hook so the change needs no new controller/API contract.

### 5. Backend / API behavior

No runtime Python, queries, endpoint, audit-writing, ordering, reporting-period, authentication or permission changes. The `can_view_user_monitoring` template condition still controls View All, detail buttons and the dialog. The detail API still independently enforces access; hiding controls is not the permission boundary. The full activity table and its functionality are unchanged.

### 6. Database / migration impact

None. No models, fields or migrations changed, and no live audit records were edited/deleted. Django verification used the existing runner's disposable local PostgreSQL test database, which it destroyed after testing. Browser checks served isolated test exports and blocked all non-GET requests. No deployment, environment change or application server restart was performed.

### 7. Tests performed

- **33/33 Django tests passed in 12.491 seconds**: `modules.reports.test_dashboard_operations`, `modules.reports.test_dashboard_executive`, `modules.reports.test_dashboard_empty_states`, run with `backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py`. Django system checks reported no issues. These cover bounded/newest-first previews, preserved history, timezone formatting, safe detail fields, unauthorized detail requests, read-only detail methods and dashboard rendering.
- **332/332 Chromium checks passed across 12 renders** using `node scratch/dashboard-activities-column-20261031/check.cjs`. Widths: 280, 320, 390, 768, 1024, 1280, 1440 and 1920px. Checked exact sibling placement, 16px spacing, aligned equal-width desktop Services/Users columns, 16px responsive Services-to-Users gap, actual values/URLs, populated/empty states, Refresh/error/retry, keyboard-open details and restored focus, no-JavaScript initial rendering, no page overflow, no browser errors and no browser writes.
- Inspected populated desktop/phone activity screenshots and the empty desktop Users stack. Evidence: `scratch/dashboard-activities-column-20261031/browser-result.json`, `activities-populated-1440.png`, `activities-populated-390.png` and `users-empty-1440.png`.
- `node --check backend/static/components/js/admin_dashboard_activities.js` and scoped `git diff --check` passed. The generic design-skill kit gates are unavailable in this workspace; these results are the measured project checks, not a full WCAG or cross-browser certification.

### 8. Remaining limitations / troubleshooting / safe practice

The columns have natural heights determined by actual records. They are not forced to equal height, so a long Services list can still be taller than Users plus Activities. The preview continues showing at most five eligible activities in the chosen period. Full history remains available through View All Activities. Verification used Chromium and isolated source-rendered fixtures, not production deployment or physical devices.

If the old full-width table persists, reload and confirm both assets use `20261031-activities-list`. Check that `system_activity_preview.html` appears only inside `super_users_overview.html`, after the Users by Type article. If refreshed rows revert to a table, inspect the loaded activity script version. If the preview shows an error, use Refresh/retry and inspect the existing dashboard API response; do not replace missing data with fake records. A denied detail request must remain denied by the server.

Safe practice: open Dashboard, choose a period containing existing activity, and compare one action/date/result with the full activity table. Open and close its eye button using the keyboard, then confirm focus returns. Resize to phone width and verify the activity card stays directly below Users by Type with readable wrapped text. Refresh and confirm the list retains the selected period. These checks require no account, booking or audit-record edits.

## Current: Taller User Registration Trend and compact Users by Type — October 31, 2026

### 1. Cause / reason

The latest request makes User Registration Trend larger like Booking Trend and makes Users by Type smaller so its donut and account table fit the Users column. Inspection confirmed that the shared refinement stylesheet limited the registration drawing area to 200px while Booking Trend used 320px on desktop. The distribution card reserved 240–280px for the donut and only allowed a side-by-side table from 520px of card content width.

| Before | After | Why |
| --- | --- | --- |
| Registration drawing area 200px | Matches Booking Trend: 320px at screen widths of 600px and above; 260px below | Give registration trends the same readable vertical space. |
| Donut 240–280px with a 520px side-by-side threshold | Donut 160–200px beside the table from 400px of card content width | Give the table more room inside the Users column. |
| Narrow cards used a donut up to 260px | Centered donut up to 180px, shrinking further when necessary | Keep compact cards responsive without overflow. |

### 2. Exact files changed, current lines and nearby anchors

- `backend/static/components/css/admin_dashboard_operations.css:277`, scoped chart-sizing selector: add the existing Users registration wrapper to the 260px base and line 299's 320px desktop rule. Line 288 sets the narrow donut size; lines 294–296 set its 400px container breakpoint and 160–200px side-by-side sizing.
- `backend/templates/dashboard/pages/admin_dashboard.html:27`, operations stylesheet link: use `20261031-users-chart-balance` so browsers request the updated CSS.
- `docs/dashboard-analytics-operations-update.md:3`, this current report: record the cause, sizing, inputs/outputs, verification and safe practice.
- `CAMPUSHUB_CONTEXT.md:3`, current Users sizing decision: preserve the latest request for later work.
- `docs/web-ui-ux-guidelines.md:23`, latest chart-sizing request: supersede the earlier larger-donut and 200px registration choices.

### 3. Changes made

The registration line chart now has the same drawing height as Booking Trend. The existing title, subtitle, grouping dropdown and chart type remain. Users by Type keeps its own bordered card: its smaller donut sits to the left of the vertically centered table when the card has enough room, and centers above the full-width table on narrow screens. Counts, shares, account-type names and the untyped-account note remain visible.

The outside Users heading, View Analytics action, separate Services/Users columns, 16px card/content gaps and natural card heights remain. Services cards still stack at full width. Sales/Booking heights, neighboring sections and application behavior are unchanged by this follow-up. No fixed-height filler was added.

### 4. How it works / functions, inputs, outputs and data flow

The unchanged Django projection supplies `executive.users.trend`, `new_registrations`, `distribution` and related totals to `super_users_overview.html` and the existing snapshot response. `renderUsers()` in `admin_dashboard_executive.js` still passes the same records to `chart()` for the registration line and account-type donut. Existing Chart.js responsive sizing reads the CSS wrapper dimensions and resizes each canvas; CSS does not transform data.

```css
/* Card content width, rather than the whole browser width, decides the layout. */
@container users-distribution (min-width: 400px) {
    /* Smaller square chart + flexible table; the existing gap is 16px. */
    /* grid-template-columns: clamp(160px, 36cqi, 200px) minmax(0, 1fr); */
}
```

The input is the unchanged database-derived snapshot plus available screen/card width. The output is the same chart values and table cells in differently sized wrappers. Daily/Weekly/Monthly registration grouping still runs through the existing controller, and global dates/Refresh still use the existing endpoint. Empty/error/fallback handling continues to hide unavailable canvases, so a larger drawing height does not create a blank chart in an empty period. The approach reuses existing scoped rules rather than changing shared chart logic or creating another renderer.

### 5. Backend / API behavior

No changes. Queries, response fields, dates/grouping, routes, permissions, recorded account types, counts/shares and workflows remain. Only CSS and its cache version changed in application code.

### 6. Database / migration impact

None. No model/schema/migration, live record, environment, deployment or runtime restart changes.

### 7. Tests performed, troubleshooting and safe practice

- **1196/1196 Chromium checks passed across 15 renders and nine widths, 280–1920px.** The harness used previously exported actual Django test fixtures, current workspace CSS and read-only intercepted responses. It covered populated/empty data, actual registration canvas height/counts, Daily/Weekly/Monthly grouping, selected dates, Refresh/error/retry, actual donut values and table counts/shares, compact responsive sizing/alignment, unchanged stacked Services cards, missing-library fallbacks and no page overflow/browser writes/page errors.
- Measured registration/Booking heights were 320px at widths 600px and above, 260px below. Example donut widths: 200px at 1920px, 187.5px at 1440px, 160px at 1280px, and 180px at 390px. At 280px it shrank to 150px to fit its card. Desktop Users-column and phone distribution screenshots were visually inspected.
- CSS brace balance, intended scoped selectors/container rules, unchanged Services asset versions and source whitespace checks passed. `git diff --check` passed for both application files. No backend tests were rerun for this CSS-only application change.
- Evidence: `scratch/users-chart-balance-20261031/browser.log`, `browser-result.json`, PNG captures, `file-checks.log` and `whitespace.log`.

Troubleshooting: hard-refresh and confirm the operations stylesheet URL ends with `v=20261031-users-chart-balance`. If registration remains 200px, inspect the loaded version and `[data-user-trend-wrap]` computed height. If the donut/table stack, check the card's content width; below 400px this is intentional. Keep the actual account table and untyped note instead of hiding data to reduce height.

Safe practice: inspect the registration wrapper's height beside Booking Trend, change Group by to Weekly and Monthly, then Refresh and confirm the totals remain correct for the selected range. Narrow the browser to confirm that all account-type columns remain readable and the donut stays square and centered. Temporarily change its 180px cap to 170px in DevTools, observe the layout, then reload to restore the saved value. This exercise changes no account or request records.

### 8. Remaining limitations

Card height follows actual text/table content; the side-by-side dashboard columns are not forced to equal height. Very narrow cards stack chart and table and may use a donut below 160px. Verification used Chromium and Django fixture exports rather than a physical-device or cross-browser certification. This sizing decision supersedes the older large-donut/200px registration notes below and in earlier feature reports.

## Previous: Vertically stacked Services cards — October 31, 2026

The latest request supersedes the empty-panel compaction below: Requests by Service, Recent Service Requests and Service Attention now each fill the Services column and stack vertically with 16px gaps in empty and populated states. Recent Service Requests keeps View All at the top right and all five fields; narrow cards use labelled rows without sideways scrolling. Empty icons/messages are centered with compact padding. The separate, equal-width Services/Users columns, outside Users heading and large responsive Users by Type donut remain.

Only Services CSS, the initial table's labels/roles, matching refresh-rendered labels/roles and paired asset versions changed. Django values, requests, routes, filters, permissions and database schema remain. Verified 24/24 Django tests and 2289/2289 Chromium checks across 22 renders/nine widths. The [Services guide](dashboard-services-overview.md) contains the current eight-part report, exact files/current lines, inputs/outputs/data flow, troubleshooting and safe practice. It supersedes the earlier multi-column CSS references and gap measurements below.

## Previous: Outside Users heading and compact empty service panels — October 31, 2026

### 1. Cause / reason

The screenshot showed Users Overview inside its white surround and a large gap below Users by Type. The user confirmed that the title/subtitle should sit outside the bordered content, like Services Overview, with the action shortened to View Analytics. The gap came from three empty Services panels stacking in the adjacent column.

| Before | After | Why |
| --- | --- | --- |
| Users heading inside the content border | Outside heading above a bordered KPI/trend body | Apply the confirmed heading position. |
| View User Analytics | View Analytics, same URL | Match other overview actions. |
| Three stacked empty service panels | Responsive compact rows for genuine empty states | Reduce the lower gap without stretching the donut or compressing real tables. |

### 2. Exact files changed

- `backend/templates/dashboard/partials/super_users_overview.html:5`: shorten the link text while preserving its Django URL/hook. Line 7 wraps existing KPI/registration/error nodes in `users-overview-body`; heading and separate donut remain outside that body.
- `backend/static/components/css/admin_dashboard_operations.css:308`, `Users heading sits outside`: transparent Users section, white bordered content body, 16px gaps and responsive 16px/20px padding.
- `backend/static/components/css/admin_services_overview.css:85`, `Compact genuine empty service panels`: two empty operations cards can share a row from 480px container width. From 560px, all three empty auxiliary cards can share a row below the full-width summary/trend. Populated request tables stay full width.
- `backend/templates/dashboard/pages/admin_dashboard.html:26`: Services CSS version `20261031-compact-empty-services`; line 27: operations CSS `20261031-users-header-layout`.
- `backend/core/modules/reports/test_dashboard_executive.py:308`: update the existing label expectation and check the Users hook and single new body wrapper.
- `docs/dashboard-analytics-operations-update.md:3`, `docs/dashboard-services-overview.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:27`: preserve this decision, data flow, measured checks and practice. The Services guide's stray Windows-encoded punctuation was normalized to UTF-8 so it could be updated safely. Use code anchors if later edits move lines.

### 3. Changes made

Users Overview's title/subtitle and View Analytics now sit outside its bordered KPI/registration body. Users by Type keeps its separate card and current 240–280px responsive donut/table sizing. No fixed-height filler or enlarged registration chart was added.

Services retains all four cards, headings/actions and DOM/data order. Its summary/trend stays full width. Genuinely empty auxiliary panels compact into two- or three-column rows where space permits; narrow screens stack naturally. Actual request/attention content retains its full-width presentation. This shortens the column that caused the excessive gap below the donut.

### 4. How it works / functions, inputs, outputs and data flow

The unchanged Django context supplies `executive.users`, `executive.services` and selected-period analytics URLs. The existing `data-users-overview` host, both `data-users-content` regions, chart/table IDs and error hooks remain. `renderUsers()` and registration grouping still find the same nodes after the new wrapper is added.

The existing service renderer sets `hidden` on its actual empty-state messages. CSS `:has(...:not([hidden]))` reads those states to choose the compact layout. When records return after Refresh, the empty marker becomes hidden and that empty-only layout stops applying. `display: contents` flattens only the two structural grid wrappers in the three-empty-panel case; labelled article cards and their content remain intact. No new data calculation or executable application JavaScript was added.

Safe practice: inspect the Users heading above its content border, then follow View Analytics and verify the selected dates and `module=users` remain. Return, change registration grouping and Refresh. Compare an empty Services period with one containing requests; all five table columns and request links must remain. Resize without editing accounts or requests to verify compact rows and mobile stacking.

### 5. Backend / API behavior

Unchanged: protected routes, analytics destination, queries/counts, dates/defaults, permissions, registration/account types, service workflows and response fields. Only the action text and presentation changed.

### 6. Database / migration impact

None. No schema/migrations, live records, credentials, environment, deployment or application restart changes. Verification used disposable localhost PostgreSQL records and intercepted read-only browser requests.

### 7. Tests performed

- **24/24 existing executive/Services Django tests passed in 17.740 seconds**; system checks reported no issues. Coverage includes real counts/date boundaries, account-type rules, role isolation and actual navigation.
- **808/808 Chromium checks passed across 16 renders/nine widths (280–1920px)**: outside heading/border/padding, action text/route, actual chart/count/request data and five columns/URLs, empty-only compaction, unchanged populated layouts, grouping/dates/Refresh/error/retry, narrow screens, fallbacks and no overflow/writes/page errors. Desktop/phone screenshots were inspected.
- Temporarily restoring the old stacked empty-service layout in the test browser measured the difference: the gap fell from about **262px to 0px at 1920px** and **303px to 18px at 1440px** in the actual fixture data, without stretching the donut card.
- Evidence: `scratch/users-header-service-spacing-20261031/django.log`, `browser.log`, `browser-result.json` and PNG captures. Final scoped checks are in `file-checks.log` and `whitespace.log`.

### 8. Remaining limitations / troubleshooting

Refresh to load both versioned stylesheets. If the old surround remains, inspect `users-overview-body` and the parent section reset. If panels do not compact, inspect their real `hidden` states and container width. Keep actual tables/data intact. Populated panels retain natural content height; small screens stack. Verification used Chromium/source-rendered fixtures, not production records, other browsers or physical devices. No accessibility certification is claimed.

## Current: Larger donut, Booking Trend and Sales Trend — October 31, 2026

### 1. Cause / reason

The user explicitly reverted the interrupted Services/Users height-balancing attempt and requested sizing changes for only three charts. That attempt's stretching, taller registration chart and remaining-space allocation were removed. The existing shared chart reset limited Booking/Sales drawing areas to 200px, while Users by Type used a 190px donut.

| Before | After | Why |
| --- | --- | --- |
| Forced Services/Users height matching from the interrupted attempt | Original intrinsic column/card sizing and registration-chart height restored | Apply the user's explicit revert. |
| 200px Booking/Sales drawing areas | Matching 320px areas at 600px and wider, 260px below | Improve readability while keeping proportional charts. |
| 190px donut | 240–280px beside the table when space permits; centered, responsive stacking otherwise | Enlarge the actual chart without a fixed-height empty card. |

### 2. Exact files changed

- `backend/static/components/css/admin_dashboard_operations.css:276`, `Super Admin chart sizing only`: replace the interrupted balance block with scoped chart sizing. Lines 277–281 enlarge Booking/Sales and keep their controls right aligned. Lines 282–297 size/center the donut and keep its table responsive. Lines 298–300 set the matching desktop trend heights.
- `backend/templates/dashboard/pages/admin_dashboard.html:27`: version this existing stylesheet as `20261031-chart-sizing`. No script or template data hook changed.
- `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:23` and `docs/booking-overview-implementation.md:3`: preserve the latest sizing/revert, exact inputs/outputs, measured checks and safe practice. Use the named source anchors if subsequent edits move a line.

### 3. Changes made

Booking Trend and Sales Trend have equal drawing heights: 320px on desktop/tablet and 260px on narrow phones. Their existing period/grouping controls remain at the right edge of each header, wrapping naturally when needed. Booking keeps its vertical bars; Sales keeps its existing line chart.

Users by Type has a larger square donut. When its actual card content is at least 520px wide, a container query places the donut left and the account-type table right, vertically centered. Its width clamps between 240px and 280px. Narrow cards stack the chart/table with a 16px gap; the centered chart uses up to 260px and shrinks to the available width on very narrow screens. The table still includes Type, Accounts and Share, plus the existing untyped-account note.

Card heights remain natural; no stretching or minimum-height filler was added. The body gap is 16px and its top margin is 12px to keep space around the donut compact. The previous registration chart height and Services/Users column sizing are restored. Other sections, white cards, navy/gold colors and existing spacing remain.

### 4. How it works / functions, inputs, outputs and data flow

Only CSS and its cache version changed. Existing Chart.js renderers already use `responsive: true` and `maintainAspectRatio: false`, so they respond to the new wrapper dimensions. The donut wrapper's `aspect-ratio: 1` keeps the canvas square. A card-width container query chooses side-by-side versus stacked presentation, rather than assuming that a wide viewport always gives each dashboard card enough room.

The data flow stays Django/PostgreSQL → existing context/API → existing chart datasets. `marketplace.sales_trend.sales` supplies numeric sales values, `executive.booking_overview.trend` supplies integer booking counts, and `executive.users.distribution` supplies recorded account-type counts/shares. CSS never recalculates these values. Form IDs, grouping/date handlers, global Refresh, retry and navigation remain unchanged.

```css
/* Presentation input: available screen width. Output: matching plot height. */
height: 260px;
/* At the existing 600px screen breakpoint: height: 320px. */
```

Safe practice: select a real reporting period and compare all three plots with their API values. Change Sales/Booking grouping, then Refresh; counts and selected values should remain correct. Resize to phone width and inspect the centered donut/table stack. In DevTools, temporarily change only a plot's height to 300px and observe the chart resize; reload to restore the saved rule. This needs no account, order or booking edits.

### 5. Backend / API behavior

Unchanged. No executable JavaScript, Python, query, response field, permission, filter/default, registration, order or booking workflow changed. Existing `[hidden]` behavior keeps empty/failed charts from reserving an enlarged blank drawing area; existing empty/fallback messages and actual tables remain available.

### 6. Database / migration impact

None. No schema, migrations, live records, environment, credentials, deployment or user-controlled application restart changed. Verification used disposable localhost PostgreSQL databases and intercepted read-only browser requests.

### 7. Tests performed

- **57/57 existing Django executive, booking-overview and marketplace dashboard tests passed in 26.222 seconds**. Includes actual date/status/ranking/account-type values and existing permissions/data boundaries. System checks reported no issues. No new application test was written for this reversible CSS change.
- **653/653 Chromium checks passed across 17 renders/nine widths (280–1920px)** using current ORM-backed fixture HTML/JSON. Verified plot/canvas sizes, square responsive donut, side-by-side vertical centering or centered stacking, no surplus card-bottom space, right-aligned controls, actual chart/table values, restored registration height and column sizing, grouping/selected dates/Refresh/error/retry, empty/no-library states and no page overflow. No browser write requests or page errors occurred. Populated desktop/phone and empty renders were inspected.
- Evidence: `scratch/dashboard-chart-sizing-20261031/django.log`, `browser.log`, `browser-result.json` and chart PNG captures. Scoped file/whitespace/reference checks are recorded in `file-checks.log` and `whitespace.log`.

### 8. Remaining limitations / troubleshooting

Refresh to load `20261031-chart-sizing`. If an old size remains, inspect the stylesheet version and the scoped chart-sizing block. On cards narrower than 240px, the donut shrinks to avoid overflow; it remains square. Empty data stays an honest empty state. Verification used Chromium and isolated source-rendered data, not production records, other browsers or physical devices. No measured accessibility certification is claimed.

## Current: Users by Type Side-by-Side (Pie Chart Left, Table Right) — October 31, 2026

### 1. Cause / reason
The user provided a screenshot of the "Users by Type" card and requested: `"arrange this left is piechart then toight is the table just move the layout position"`. Previously, the doughnut chart and table rendered vertically stacked because `.users-type-layout` did not have explicit flex row styling inside the standalone `.users-by-type-card`.

### 2. Exact files changed
| File / line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/super_users_overview.html:26` | Inside `.users-by-type-card`, grouped `.users-data-table` and `[data-user-untyped-note]` in `.users-type-table-wrap` beside `.users-chart` within `.users-type-layout`. |
| `backend/static/components/css/admin_executive_refinement.css:1091` | Configured `.users-by-type-card .users-type-layout` as a flex row with `gap: 24px; align-items: center;`. Left `.users-chart` given `flex: 0 0 190px; width: 190px; height: 190px;`. Right `.users-type-table-wrap` given `flex: 1 1 0; min-width: 0;`. Added column alignments (Type left, Accounts center, Share right). Responsive stacking below 640px. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | Bumped CSS cache version to `?v=20261031-users-by-type-pie-table`. |

### 3. Changes made
Inside the standalone "Users by Type" card, the doughnut/pie chart is positioned on the LEFT (190px square) and the accounts breakdown table (`Type`, `Accounts`, `Share`) is positioned on the RIGHT. The unavailable accounts note sits directly under the table. On screens narrower than 640px, the layout smoothly stacks vertically.

### 4. How it works
The existing Chart.js initialization in `admin_dashboard_executive.js` attaches to `#usersByTypeChart` inside `.users-chart`. With `maintainAspectRatio: false` and responsive options enabled, Chart.js conforms to the 190px square container on the left. The table fills the remaining width on the right. Data hooks, queries, and empty states remain untouched.

### 5. Backend / database impact
None. No views, models, permissions, or migrations were modified.

### 6. Tests performed
Ran 48 dashboard tests across `test_dashboard_executive`, `test_dashboard_empty_states`, and `test_dashboard_marketplace`; all 48 tests passed in 25.582s.

### 7. Remaining limitations
Requires a hard browser refresh if the previous stylesheet is cached in the browser.

## Current: Booking Summary inside Booking Trend and Recent Orders fit — October 31, 2026

### 1. Cause / reason

The latest request puts Booking Summary inside the same card as Booking Trend, following Marketplace's summary-then-trend arrangement. The supplied Recent Orders screenshot shows its ID running into Buyer. Confirmed causes were a 14% ID column with unbroken text, visible overflow, and a header rule targeting every `th`, including body row headers. Narrow widths also could not fit seven unbroken values without clipping.

| Before | After | Why |
| --- | --- | --- |
| Summary outside the trend card | Three existing summary KPIs above the chart inside one bordered card | Match the requested Marketplace arrangement. |
| ID text overflows into Buyer; body IDs inherit a header background | Rebalanced columns, contained text and transparent body row headers | Keep each field distinct without sideways scrolling. |
| Fixed columns become unreadable on compact cards | Labelled responsive rows retaining every field and action | Preserve data without ellipses, hidden fields or an internal scrollbar. |

### 2. Exact files changed

Paths are relative to the project root. Line numbers describe this update; use the named anchor if subsequent edits move them.

| File / current line | Nearby anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/super_facilities_overview.html:8` | Start the existing `.facilities-trend` article before `data-booking-content`, so Booking Summary/KPIs are inside it. Keep all IDs, the separate ranking and existing operations content. |
| `backend/static/components/css/admin_booking_overview.css:325` | Executive-only combined-card spacing, 12px below the summary title, 16px before the trend heading, retained independent ranking/operations borders and consistent metric-link styling. |
| `backend/templates/dashboard/partials/recent_orders.html:7` | Preserve all seven headers/cells. Add explicit table roles and `data-label` values to executive rows for responsive presentation. Other-role markup stays unchanged. |
| `backend/static/components/css/dashboard_recent_orders.css:54` | Scoped no-scroll table widths/wrapping and body-header correction. Line 128 starts compact labelled rows; line 184 uses four columns on medium cards, with extra width for IDs; line 189 starts the very narrow single-column refinement. |
| `backend/static/components/js/admin_dashboard_filter.js:303` | `renderRecentOrders()`: read existing header labels once; line 365 adds matching roles/labels to refreshed executive cells. Existing text values, URLs, filtering, tokens and eye action remain. |
| `backend/templates/dashboard/pages/admin_dashboard.html:19` | Version booking CSS as `20261031-summary-in-trend`; line 621 versions the existing filter renderer as `20261031-booking-summary-orders`. Other dashboard asset versions remain current. |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_order_modals.html:3` | Version its existing Recent Orders stylesheet as `20261031-no-scroll`; modal markup/controllers are unchanged. |
| `backend/core/modules/reports/test_dashboard_executive.py:125` | Existing layout test now checks that the trend article begins before Booking Summary and that summary precedes the trend heading. |
| `backend/core/modules/reports/test_dashboard_marketplace.py:241`, `backend/core/modules/marketplace/test_orders_admin.py:143` | Keep existing header/plain-reference/eye expectations while allowing additional accessible attributes. The Marketplace reference may retain its existing small date after the code. |
| `docs/dashboard-analytics-operations-update.md:30`, `docs/booking-overview-implementation.md:3`, `CAMPUSHUB_CONTEXT.md:8`, `docs/web-ui-ux-guidelines.md:21` | Record this latest arrangement, functions/data flow, real checks and safe practice. |

The task's scoped rules were consolidated into the existing booking/order component styles. The shared executive stylesheet retains current unrelated dashboard work; it is no longer responsible for this task's new responsive row rules.

### 3. Changes made

Booking Summary and its three real KPI cards are inside Booking Trend, above its existing heading, Daily/Weekly/Monthly control and navy vertical bar chart. Most-Booked Facilities stays separate. The outside section headings, 32px overview separation and existing booking/ranking/operations data remain.

Recent Orders retains **Order ID, Buyer, Order Date, Total, Order Status, Payment Status and Actions** in the same order. Wide tables use 20/17/15/11/15/13/9 percent sizing, smaller horizontal padding and natural text wrapping. Status words remain intact. Body IDs no longer look like separate header blocks. No value is replaced with ellipses.

At card widths up to 680px, each record uses labelled fields instead of squeezing seven columns across a narrow card. Cards from 520–680px use four grid columns, with Order ID spanning two; smaller cards use two columns, then one at 260px or less. Every original field and eye action remains visible, with no internal horizontal or vertical table scrolling. The page can still scroll normally.

### 4. How it works / inputs, outputs and data flow

The unchanged Django context supplies `executive.booking_overview` and `operations.recent_orders`. Moving the existing summary node inside the article leaves the unbordered `#bookingOverviewCard` controller host and all summary/chart IDs intact. The booking renderer still updates the same counters, period labels, chart, empty/error/retry state and links.

Initial order markup now carries each column's existing label in `data-label`. On Refresh, `renderRecentOrders(orders)` gets those labels from `thead th`, appends the same seven actual cells, and sets their labels and table roles. For example, an actual saved code remains `reference.textContent = order.code`; its responsive label is `Order ID`. No data is inferred from the visual layout.

Component-scoped container queries change only presentation. The native headers remain available to assistive technology while their labels appear beside the same data in compact rows. Explicit table/rowgroup/row/header/cell roles preserve relationships when CSS changes their display. Current row URLs still pass the same same-origin validation and tab-token handling; the eye still opens the existing authorized Django fragment/modal.

Safe practice: reload Dashboard, confirm Booking Summary is inside the chart card, and change grouping/Refresh without changing dates. Compare one order's six values and eye destination with `operations.recent_orders`. Resize from a wide table to compact labelled rows and confirm all seven fields remain visible without sideways scrolling. Open/close the eye to verify saved details and restored focus; do not approve, pay or edit an order. No record changes are needed.

### 5. Backend / API behavior

Unchanged: existing Django/PostgreSQL values, queries, endpoints, selected/default filters, date bases, rankings, permissions and order/booking workflows. The only executable renderer additions are labels/roles; values continue using safe `textContent` assignments. No new button, filter or API was added.

### 6. Database / migration impact

None. No migrations, schema, live records, credentials, environment, deployment or application restart changed. Tests used disposable localhost PostgreSQL databases; browser non-GET requests were blocked.

### 7. Tests performed

- **85/85 focused Django tests passed in 34.088 seconds** across executive, booking, marketplace, ranking, upcoming-reservation and existing order-fragment/modal/permission checks. Initial strict HTML assertions were updated to tolerate added accessible attributes while retaining their original content/action checks. No application behavior was changed to satisfy those assertions.
- **3902/3902 Chromium checks passed across 22 renders/nine widths (280–1920px)**. Checks compare actual ORM-backed values, all seven fields/labels, text bounds, no internal scroll, responsive layouts, combined-card nesting, dates/grouping/Refresh/retry, keyboard/chart/text fallbacks and canonical order-detail open/close/focus. Desktop/phone booking and order screenshots were inspected. Results are in `scratch/booking-summary-orders-20261031/browser.log` and `browser-result.json`.
- **708/708 additional targeted browser checks passed across four renders** after refreshing populated orders in wide/compact layouts and opening the refreshed eye action. Saved customer details and returned focus remain correct. Results are in `refresh.log` and `refresh-result.json` in the same evidence folder.
- Evidence also includes actual desktop/phone PNG captures and `django-final.log`. Component/renderer syntax and scoped whitespace/reference checks are in `file-checks.log` and `whitespace.log`.

### 8. Remaining limitations / troubleshooting

Refresh to load booking CSS `20261031-summary-in-trend`, Recent Orders CSS `20261031-no-scroll` and filter JS `20261031-booking-summary-orders`. If old markup remains in a user-controlled local Django process, restart that process and refresh. If labels disappear only after Refresh, inspect the new renderer version and `data-label` on the refreshed cells.

Compact layouts deliberately use labelled rows, so their height can grow rather than clipping data or adding internal scrolling. Very long values can wrap naturally. Full Orders navigation and ordinary page scrolling remain. Verification uses Chromium/source-rendered fixtures rather than production records, other browsers or physical devices; no cross-browser accessibility certification is claimed.

## Current: Users by Type moved out of the Users Overview container - October 31, 2026

### 1. Cause / reason
Request: "Users by Type ... move down, not belong to the big container." It was an inner card of the bordered `executive-users` section, so it shared the big container's border.

### 2. Exact files changed
| File / line | Anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/super_users_overview.html` (whole file) | `executive-users-stack` | New unbordered wrapper that keeps `data-users-overview` and `aria-busy`. Inside: the bordered `<section class="executive-users">` (header, KPI cards, User Registration Trend, error message) and, after it, the standalone `<article class="users-by-type-card" data-users-content>`. IDs, data hooks, charts and Django variables are unchanged. |
| `backend/static/components/js/admin_dashboard_executive.js` ~lines 44 and 57 | `[data-users-content]` | `querySelector(...).hidden` became `querySelectorAll(...).forEach(...)` because two elements now carry `data-users-content` (trend grid and Users by Type), so both hide/show together on error/success. |
| `backend/static/components/css/admin_executive_refinement.css` ~lines 1051-1062 | comment `Users Overview: bordered container...` | Wrapper = column with 16px gap; section and Users by Type card each have border, radius, 16px padding (20px at 1280px+); trend grid is one column. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | CSS and `admin_dashboard_executive.js` links | Version `?v=20261031-users-by-type-card`. |

### 3. Changes made / how it works
The JS still finds everything through `users = root.querySelector('[data-users-overview]')`; that element is now the wrapper, so the distribution chart, table and untyped note are still inside it. Data flow is unchanged: `executive.users` -> template/JSON -> `renderUsers()` fills metrics, chart and rows. Layout is Users Overview card on top, Users by Type card 16px below it, both in the same grid column.

Practice: in DevTools, set `display:none` on `.users-by-type-card` and confirm the Overview still works; revert. Change the period and check Users by Type values update.

### 4. Backend / database
None.

### 5. Tests performed
`test_dashboard_executive`, `test_dashboard_empty_states`, `test_dashboard_marketplace`: 48 ran, all OK. `node -c` on the executive JS passed. Not checked in a browser.

### 6. Remaining limitations
Hard refresh if the old CSS/JS is cached. If you wanted Users by Type to leave the Users section entirely (separate dashboard section), say so.


## Current: Super Admin Users Overview inner containers - October 31, 2026

### 1. Cause / reason
`[data-global-dashboard] .dashboard-executive .executive-domain-grid :is(.dash-card, .marketplace-chart-card)` in `admin_executive_refinement.css` (~line 155) strips border, radius and side padding (`padding: 12px 0; border: 0`) from every `.dash-card` in the domain grid. In Users Overview this removed the boundaries of User Registration Trend and Users by Type, so they looked like loose content instead of separate inner containers. Confirmed from the CSS cascade; the HTML in `super_users_overview.html` already had the correct order (header inside the section, KPI row, then two chart articles), so no markup or data hooks changed.

### 2. Exact files changed
| File / line | Anchor | Change |
| --- | --- | --- |
| `backend/static/components/css/admin_executive_refinement.css` ~315-327 | comment `Users Overview: header + KPI row...` | New scoped `.executive-users` rules: section is a flex column with 16px gap; header margin 0; KPI cards and both chart cards get 1px `--executive-border`, `--executive-radius`, 16px padding, white surface; chart grid gap 16px. |
| `backend/templates/dashboard/pages/admin_dashboard.html` line 29 | `admin_executive_refinement.css` link | Cache version `?v=20261031-users-overview-containers`. |

### 3. Changes made
Users Overview header (title, subtitle, View User Analytics) stays inside the bordered section. New Users and Verified Users cards sit below it in two equal columns. User Registration Trend and Users by Type are each their own bordered inner card, 16px apart, equal height on desktop, stacked on narrow screens (existing 800px breakpoint). No other section selector was touched; every rule is prefixed with `.executive-users`.

### 4. How it works / data flow
`executive.users` (Django context) fills the same template hooks (`data-user-metric`, `data-user-trend-wrap`, `userRegistrationView`, `data-user-distribution-*`). `admin_dashboard_executive.js` still finds the same IDs and data attributes, so charts, Group-by filter, Refresh and empty states work unchanged. CSS only changes boundaries and spacing. Selectors use `.executive-users .users-chart-grid > .dash-card`, which is more specific than the generic domain-grid reset, so the reset no longer wins here.

Practice: in DevTools, uncheck `border` on `.executive-users .users-chart-grid > .dash-card` and watch the boundary disappear; re-enable it. Reload the dashboard with Last 7 Days and confirm values are unchanged.

### 5. Backend / API behavior
Unchanged.

### 6. Database / migration impact
None.

### 7. Tests performed
`test_dashboard_marketplace`, `test_dashboard_executive`, `test_dashboard_empty_states`: 48 run, 47 passed, 1 failed (`test_analytics_operations_layout_and_removed_chart_tables`, expects `<th scope="col">Order Status</th>`). That failure comes from a separate, concurrent edit to `dashboard/partials/recent_orders.html` that adds `role="columnheader"` to the headers; it is unrelated to Users Overview and was left untouched. Visual result was not checked in a browser here.

### 8. Remaining limitations
Needs a hard refresh if the old stylesheet is cached. Fix for the failing Recent Orders test belongs with whoever owns that `role` change (update the test expectation or the markup).


## Current: Space above Marketplace and Facilities Overview — October 31, 2026

### 1. Cause / reason

The user clarified that the extra space belongs above **Marketplace Overview and Facilities Overview**, not inside Booking Summary or between its cards. The existing gap from Attention/Bundles into the overview row was 16px; stacked Facilities also followed Marketplace by 16px.

| Before | After | Why |
| --- | --- | --- |
| 16px above the overview row and stacked Facilities | 32px above the requested sections | Make the section boundaries clearer while preserving internal card spacing. |

### 2. Exact files changed

- `backend/static/components/css/admin_executive_refinement.css:308`, `.executive-priority-grid`: double the existing 16px spacing token below the priority row. Line 309 adds 16px above stacked Facilities; line 311 resets that margin at the existing 1280px two-column breakpoint.
- `backend/templates/dashboard/pages/admin_dashboard.html:29`: version CSS as `20261031-overview-spacing`.
- `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:19`: save this clarification, data flow, checks and practice steps.

### 3. Changes made

Marketplace and Facilities have 32px separation from the preceding content. Desktop headings remain aligned on their shared row. On tablet/phone widths, Facilities gets 32px above it after Marketplace. Internal cards and the gaps leading to other domain sections retain their existing spacing. No heading, card, filter, data or action was added or removed.

### 4. How it works / functions, inputs, outputs and data flow

This changes two scoped CSS margins only. The existing `--executive-gap: 16px` supplies the input: the priority row's margin becomes twice that token. Stacked Facilities adds one token to the domain grid's existing 16px row gap, yielding 32px. At 1280px and wider its extra margin returns to zero so both headings align.

No runtime function or data mapping changed. Existing Django context/API values still flow through the same templates and JavaScript renderers. Safe practice: use DevTools to measure the bottom of Attention/Bundles to Marketplace, then resize below 1280px and measure Marketplace's bottom to Facilities. Both should be 32px. Temporarily change the token multiplier, inspect the gap, then reload to restore the saved value. This needs no record edits.

### 5. Backend / API behavior

Unchanged: no query, endpoint, response, permission, date/grouping, Refresh or workflow changes.

### 6. Database / migration impact

None. No migrations, live writes, environment, runtime restart or deployment changes.

### 7. Tests performed

**2147/2147 Chromium checks passed across 11 renders/eight widths (280–1920px)** using the preceding implementation's actual Django fixture exports and the current stylesheet. New geometry checks verify both 32px gaps, aligned desktop headings and unchanged 16px domain-grid gaps. Existing independent cards, real chart/summary/reservation/attention values, dates/grouping/Refresh/retry, keyboard inspection and empty/text fallbacks also passed. No browser writes occurred. This CSS-only follow-up did not rerun Django tests or create new application tests.

Evidence: `scratch/overview-heading-spacing-20261031/browser.log`, `browser-result.json` and captures; final scoped file/whitespace checks are in `file-checks.log` and `whitespace.log`.

### 8. Remaining limitations / troubleshooting

Refresh Dashboard to load `20261031-overview-spacing`. If the old gap persists, inspect the loaded CSS version and computed priority-row margin. Keep the Facilities margin reset at the existing desktop breakpoint to avoid misaligned headings. Verification used Chromium/source-rendered fixtures, not a production deployment or other-browser/device certification.

## Previous: Super Admin Recent Orders Visual Alignment & Header Separation — October 31, 2026

### 1. Cause / reason

The user provided a screenshot demonstrating three visual issues in the Recent Orders table on the Super Admin dashboard:
1. **Header Collision (`Payment StatusActions`)**: The "Payment Status" and "Actions" headers were colliding into `Payment StatusActions` with zero spacing between them because `orders-col-payment` was only allocated 13% width, which was too narrow for the 14-character header text.
2. **Buyer Name Vertical Misalignment & Rogue Underline**: `td.recent-orders-person` was previously styled with `display: block;`. In HTML tables, applying `display: block` on a `<td>` breaks table-cell layout, collapsing the cell height and creating an awkward gray underline right below the buyer's name, while rendering it higher than the rest of the row.
3. **Disproportionate Gaps**: Giant whitespace gaps separated Buyer from Order Date and Order Date from Total, while the rightmost status columns were compressed together.

### 2. Exact files changed

| File / current line | Anchor and change |
| --- | --- |
| `backend/static/components/css/admin_executive_refinement.css:227` | Removed `display: block` from `.recent-orders-person` and applied `vertical-align: middle !important;` to ensure native table-cell baseline alignment and eliminate the rogue underline. Increased padding to `10px 8px` on `th` and `12px 8px` on `td`. Rebalanced column percentages to: Order ID 14%, Buyer 18%, Order Date 14%, Total 11%, Order Status 14%, Payment Status 17%, Actions 12% (100% total). Centered headers and cells for columns 5, 6, and 7. |
| `backend/static/components/css/admin_marketplace_overview.css:381` | Updated `.recent-orders-table` th to `padding: 10px 8px; font-size: 12px; vertical-align: middle !important;` and td to `padding: 12px 8px; font-size: 13px; vertical-align: middle !important;`. Centered columns 5, 6, and 7. |
| `backend/templates/dashboard/pages/admin_dashboard.html:17, 29, 621` | Bumped cache version query strings to `?v=20261031-recent-orders-balanced`. |

### 3. Changes made

1. **Header Separation**: Increased `Payment Status` column to 17% and `Actions` to 12%, centering both headers and cells. "Payment Status" and "Actions" now have a wide, distinct margin with zero collision.
2. **Proper Table-Cell Baseline Alignment**: Removed `display: block` from `.recent-orders-person`. The buyer's name now aligns perfectly on the exact vertical middle baseline with the Order ID, Date, Amount, and Badges. The rogue horizontal line under the buyer's name is completely eliminated.
3. **Harmonious Column Distribution (100% total)**:
   - `Order ID`: 14% (left-aligned)
   - `Buyer`: 18% (left-aligned, comfortable spacing)
   - `Order Date`: 14% (left-aligned)
   - `Total`: 11% (right-aligned)
   - `Order Status`: 14% (centered pill)
   - `Payment Status`: 17% (centered pill, ample room)
   - `Actions`: 12% (centered action icon)
4. **Single-Row & Zero Scroll**: All rows remain strictly on a single line per order without horizontal scrollbars.

### 4. How it works / functions, inputs, outputs and data flow

Table rendering continues to draw from `operations.recent_orders` through `recent_orders.html`. The updated `<col>` percentage distribution and `vertical-align: middle !important;` rule enforce balanced spacing and cell alignment across the entire table.

### 5. Backend / API behavior

Unchanged: permissions, data retrieval, serialization, and order status transitions remain identical.

### 6. Database / migration impact

None. No database migrations or model schema alterations.

### 7. Tests performed

1. `backend/core/modules/reports/test_dashboard_marketplace.py`: All 24 tests passed.
2. `backend/core/modules/reports/test_dashboard_executive.py`: All 16 tests passed.
3. Verified 40/40 tests in 17.099s with `--keepdb`.

### 8. Remaining limitations

On very narrow viewports (< 480px), columns compress proportionally without scrolling. Buyer names with extreme character length (> 25 characters) truncate gracefully with an ellipsis (`...`) and reveal the full name on hover or in modal inspection.

## Previous:  Super Admin Recent Orders Column Arrangement & Ellipsis Fix — October 31, 2026

### 1. Cause / reason

The user reported: `"Order ID Buyer Order Date Total Order Status Payment Status AcFIX THE .... OR ARRANGE"`.
When the 7 columns were previously fitted into the Super Admin executive layout with `table-layout: fixed`:
1. Cell padding was set to `padding: 10px 12px;` (24px horizontal padding per cell * 7 columns = 168px consumed purely by whitespace).
2. Table headers (`th`) inherited `overflow: hidden; text-overflow: ellipsis;`. With the Actions column allocated only 7% width, the word "Actions" was truncated to "Ac...".
3. Status badges and cells were constrained by the remaining width, causing excessive ellipses ("....") across multiple columns.
4. Additionally, a template string interpolation issue in `admin_dashboard_filter.js` line 363 (`cell(\u20b1, 'text-end')`) caused a client-side JavaScript syntax error during dynamic updates.

### 2. Exact files changed

| File / current line | Anchor and change |
| --- | --- |
| `backend/static/components/css/admin_executive_refinement.css:227` | Removed ellipsis truncation from `th`; set `th` to `padding: 8px 6px; font-size: 11.5px; font-weight: 600; white-space: nowrap; overflow: visible; text-overflow: clip;`. Reduced cell padding to `padding: 8px 6px; font-size: 12px; line-height: 1.4;`. Rebalanced column percentages to 15%, 21%, 15%, 12%, 14%, 13%, 10% summing to 100%. Compacted status badges with `padding: 2px 6px; font-size: 11px;`. |
| `backend/static/components/css/admin_marketplace_overview.css:381` | Updated `.recent-orders-table th` to `overflow: visible; text-overflow: clip; padding: 8px 6px; font-size: 11.5px; font-weight: 600;` and cells to `padding: 8px 6px; font-size: 12px;`. Added center alignment for columns 5, 6, and 7. |
| `backend/templates/dashboard/partials/recent_orders.html:8` | Preserved clean `<th>Actions</th>` header and added `text-center` class on status and action cells. |
| `backend/static/components/js/admin_dashboard_filter.js:340, 363` | Fixed JavaScript syntax error on line 363 (`cell(`₱${order.total}`, 'text-end')`). Added `text-center` alignment to dynamically rendered status, payment, and action cells. |
| `backend/templates/dashboard/pages/admin_dashboard.html:17, 29, 621` | Updated cache-busting version strings to `?v=20261031-recent-orders-arranged`. |

### 3. Changes made

1. **Header Truncation Eliminated**: "Actions" header now has 10% width with `overflow: visible`, completely preventing any cutoff to "Ac...". All 7 column headers are fully visible and readable.
2. **Reclaimed 84px Usable Width**: Reduced horizontal cell padding from 24px to 12px per cell (8px 6px), recovering 84px of space across the 7 columns.
3. **Ellipsis Removal on Known Values**: Order ID, Order Date, Total, and Status Badges render their complete values cleanly without `....`. Only unusually long buyer names retain ellipsis protection with tooltip discovery on hover.
4. **Clean Column Proportions (100% total)**:
   - `Order ID`: 15% (e.g. `ORD-202610-001`)
   - `Buyer`: 21% (e.g. `Lester Bulay`)
   - `Order Date`: 15% (e.g. `Oct 31, 2026`)
   - `Total`: 12% (e.g. `₱1,250.00`, right-aligned)
   - `Order Status`: 14% (e.g. `Completed`, centered)
   - `Payment Status`: 13% (e.g. `Paid`, centered)
   - `Actions`: 10% (Centered view icon button)
5. **No Horizontal Scrollbar**: Retained `overflow-x: hidden; scrollbar-width: none;` on the wrapper. Every row strictly renders on a single line.

### 4. How it works / functions, inputs, outputs and data flow

The Django view passes recent orders to `recent_orders.html`. The table uses `table-layout: fixed` with calibrated `<col>` percentage widths. By reducing cell padding and setting `th` overflow to visible, all headers and values fit comfortably in the available space. On client-side refresh or date filtering, `admin_dashboard_filter.js` renders the table body dynamically, formatting amounts with `₱${order.total}` and assigning centered classes to status and action cells.

### 5. Backend / API behavior

No backend logic, models, serializers, permissions, or database queries were modified.

### 6. Database / migration impact

None. No database migrations or schema alterations.

### 7. Tests performed

1. `backend/core/modules/reports/test_dashboard_marketplace.py`: All 24 tests passed.
2. `backend/core/modules/reports/test_dashboard_executive.py`: All 16 tests passed.
3. Total: 40/40 tests passed in 14.417s.
4. Node syntax validation on `admin_dashboard_filter.js`: Passed with 0 errors.

### 8. Remaining limitations / safe practice

On viewports below 480px, fixed table layout will compress column space proportionally while keeping single-line alignment without horizontal scrollbars. Exceptionally long buyer names continue to provide full name discoverability via hover tooltip and modal details.

## Previous:  Super Admin Recent Orders One-Row Fit and No-Scroll Layout — October 31, 2026

### 1. Cause / reason

The user requested: `"Order ID Buyer Order Date Total Order Status Payment Status Actions IT ASHOULD ONE ROW FROM ASUPER ADMIN THEN REMOVE SCROLLUNG"`.
Previously on the Super Admin Executive Dashboard (`data-global-dashboard`):
1. `.recent-orders-table` had `min-width: 800px;` with `overflow-x: auto;` on its container (`.recent-orders-table-wrap`), causing horizontal scrollbars to appear.
2. Cells allowed multi-line text wrapping (`white-space: normal; overflow-wrap: anywhere;`), so buyer names and status pills wrapped onto 2 or 3 lines instead of staying on a clean single line per order.

Confirmed presentation cause: table layout was dynamic with minimum pixel threshold and wrapped typography.

### 2. Exact files changed

| File / current line | Anchor and change |
| --- | --- |
| `backend/static/components/css/admin_executive_refinement.css:180` | Scoped `#recentOrdersSlot .recent-orders-table-wrap` to `overflow-x: hidden; overflow-y: hidden; scrollbar-width: none;` and webkit scrollbar hidden. |
| `backend/static/components/css/admin_executive_refinement.css:222` | Configured `.recent-orders-table` with `min-width: 0; width: 100%; table-layout: fixed;` and all `th, td` with `padding: 10px 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: middle;`. Set proportional column distribution: 16%, 22%, 16%, 12%, 16%, 11%, 7% summing to 100%. |
| `backend/static/components/css/admin_marketplace_overview.css:377` | Updated `.marketplace-operations-row .recent-orders-table` to `min-width: 0; width: 100%; table-layout: fixed;` and nowrap ellipsis on cells. |
| `backend/templates/dashboard/partials/recent_orders.html:8` | Added `title="{{ order.buyer_name }}"` to `<td class="recent-orders-person">` so full buyer names are accessible on hover. |
| `backend/static/components/js/admin_dashboard_filter.js:360` | Added `buyerCell.title = order.buyer_name;` for dynamically rendered filtered orders. |
| `backend/templates/dashboard/pages/admin_dashboard.html:17, 29, 621` | Bumped asset versions for `admin_marketplace_overview.css`, `admin_executive_refinement.css`, and `admin_dashboard_filter.js` to `?v=20261031-recent-orders-one-row`. |

### 3. Changes made

1. **One-Row Row Layout**: Every order row now strictly occupies exactly one line. Multi-line wrapping of buyer names, dates, or badges is prevented with `white-space: nowrap`. Long names cleanly truncate with ellipsis and provide full name tooltip via `title`.
2. **Horizontal Scrolling Removed**: Removed horizontal scrollbars on `#recentOrdersSlot .recent-orders-table-wrap` (`overflow-x: hidden; scrollbar-width: none; display: none;`).
3. **Calibrated Column Widths**:
   - `Order ID`: 16% (e.g. `ORD-202610-001`)
   - `Buyer`: 22% (Buyer name with ellipsis + tooltip)
   - `Order Date`: 16% (e.g. `Oct 31, 2026`)
   - `Total`: 12% (e.g. `₱1,250.00`)
   - `Order Status`: 16% (Badge, single line)
   - `Payment Status`: 11% (Badge, single line)
   - `Actions`: 7% (Centered view icon button)
   Total: 100% fixed table width fitting the container edge-to-edge.

### 4. How it works / functions, inputs, outputs and data flow

The Django view `backend/core/modules/reports/views.py` passes `operations.recent_orders` to the dashboard template. When the template renders `backend/templates/dashboard/partials/recent_orders.html`, each row emits the 7 cells. With `table-layout: fixed` and `width: 100%`, the browser computes exact column widths based on the `<colgroup>` percentages without measuring inner cell text widths, ensuring instant layout calculation without horizontal overflow.

When date filters are updated via `admin_dashboard_filter.js`, `renderRecentOrders(orders)` generates row elements and sets `buyerCell.title = order.buyer_name;`, preserving tooltips and single-line layout dynamically.

### 5. Backend / API behavior

No backend views, models, permissions, or API endpoints were changed. All existing order retrieval logic, security scopes, and modal action bindings remain identical.

### 6. Database / migration impact

None. No database migrations or model schema alterations.

### 7. Tests performed

1. `backend/core/modules/reports/test_dashboard_marketplace.py`: Ran 24 tests; all 24 passed in 11.366s.
2. `backend/core/modules/reports/test_dashboard_executive.py`: Ran 16 tests; all 16 passed in 5.148s.
3. Verified table rendering and column percentage sum (16% + 22% + 16% + 12% + 16% + 11% + 7% = 100%).

### 8. Remaining limitations / safe practice

In extremely narrow viewports (e.g. under 600px width), fixed layout will truncate longer buyer names or order IDs with ellipses (`...`). The full buyer name is always accessible via the hover tooltip or by clicking the action button to open the full order details modal.

## Previous:  Independent Recent Orders and Inventory Alerts — October 31, 2026

### 1. Cause / reason

Both tables were inside one `marketplace-operations-card` surround. Shared executive styles removed the inner cards' borders and padding, so they did not read as two independent containers. The older column-position rule also right-aligned Order Date, and the Inventory table hid its horizontal scrollbar. These are confirmed presentation causes; no missing data or backend failure was found.

| Before | After | Why |
| --- | --- | --- |
| Shared outer card around both tables | Two white bordered cards, each filling the existing Marketplace column | Give Recent Orders and Inventory Alerts independent boundaries without changing the adjacent Facilities section. |
| Different header spacing | Internal title, subtitle and existing View All with 16px padding and divider | Keep a consistent compact card header. |
| Narrow columns and hidden Inventory scrollbar | Planned column widths, aligned values and native horizontal scrolling | Preserve every field and action on narrow screens. |

### 2. Exact files changed

Paths are relative to the project root. Use the nearby anchor if subsequent edits move a line.

| File / current line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/executive_dashboard.html:35` | `marketplace-operations-row`: remove only its shared outer card; keep Recent Orders first and `lowStockSlot` second. |
| `backend/templates/dashboard/partials/recent_orders.html:3` | Executive `marketplace-operation-header`; line 6 adds seven named columns for sizing. All existing headers, values, row actions and non-executive markup remain. |
| `backend/templates/dashboard/partials/low_stock_card.html:2` | Add the shared header class only for `global_dashboard`; line 9 adds three global-only sizing columns. Keep product/variant details, availability, statuses, destinations and empty/error hooks. |
| `backend/static/components/css/admin_executive_refinement.css:167` | Scope independent cards, 16px gaps, 16px headers and visible native scrolling to Super Admin. Line 222 starts the Orders sizing/alignment rules; line 237 starts Inventory sizing. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | CSS cache version becomes `20261031-operation-cards`; executable scripts and their versions remain unchanged. |
| `backend/core/modules/marketplace/test_orders_admin.py:68` | Existing canonical-fragment comparison now compares every `data-*` attribute used by the controller, rather than unrelated structural attributes. Line 85 optionally exports actual test-rendered dashboard/API/order detail fixtures via `DASHBOARD_OPERATIONS_REVIEW_DIR`. Keep the existing no-write assertions. |
| `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:13` | Record this layout, data flow, checks and safe practice. Related ranking/priority guides receive a current-layout note or shifted-line-reference maintenance only. |

### 3. Changes made

Recent Orders and Inventory Alerts now have separate full-width cards within the existing Marketplace Overview column, with exactly 16px between them. Marketplace remains beside Facilities at wide desktop sizes; unrelated sections retain their layout. Each card has the existing white surface, navy text, subtle border, 10px radius, and its own title/subtitle/View All inside the header.

All seven Recent Orders columns remain: **Order ID, Buyer, Order Date, Total, Order Status, Payment Status, Actions**. All three Inventory Alerts columns remain: **Product, Available, Status**. No column, value, image, variant detail, action or link was removed.

Orders uses an 800px minimum table width with relative column widths of 18/20/15/12/15/12/8 percent. References and dates remain on one line, buyer names can wrap, totals align right, and the existing eye action is centered. Inventory uses a 420px minimum and 60/16/24 percent columns; quantity and status align right. These are automatic-layout width hints, so long content can expand the table. Native horizontal scrolling stays inside each focusable, labelled table region. Preview rows remain vertically visible; no nested vertical table scrolling was added.

### 4. How it works / functions, inputs, outputs and data flow

The same Django context supplies `recent_orders` and `dashboard_low_stock.products` to the existing partials. Named `<col>` elements control presentation without adding cells or changing data. The parent grid stacks two independent cards; each table wrapper contains its own horizontal overflow.

On date changes/Refresh, the unchanged dashboard API supplies `operations.recent_orders` and `low_stock`. Existing `renderRecentOrders(orders)` (`admin_dashboard_filter.js:299`) and `renderLowStock(snapshot)` (`:246`) rebuild the table bodies from these actual records. Their existing header, column group, caption and scroll-region nodes stay in place. Empty/error/retry behavior still uses the original hooks.

```text
Actual Django records -> existing dashboard context/API
  operations.recent_orders -> seven existing cells + canonical order eye
  low_stock.products       -> three existing cells + inventory destination
  CSS column hints         -> alignment and contained horizontal scrolling
```

The delegated listener in `dashboard_recent_orders.js` still fetches the authorized `format=dashboard-order` fragment for the clicked order. The existing canonical order controller opens the saved details and restores focus when closed. No business-action request is needed to view an order. The test export writes only disposable test output files when its explicit environment variable is set; normal test/application behavior does not export files.

Safe practice: open Dashboard, select Last 30 Days and Refresh. Compare one displayed order's six values and eye URL with `operations.recent_orders`, and one alert's product/quantity/status/URL with `low_stock.products` in Network. Resize to phone width, focus each table region and scroll right to Actions or Status. Open and close an order's eye action without confirming any operation; verify the saved customer details and restored focus. Follow View All to the existing Orders/Inventory pages, then return. This exercise does not change application records.

### 5. Backend / API behavior

No application backend, API contract, query, ranking/count, filter/default, authentication, permission or order/inventory workflow changed. The existing latest-five previews, selected-period Orders behavior and current Inventory snapshot remain. Full Orders and scoped Inventory destinations are unchanged.

### 6. Database / migration impact

None. No migrations, schema changes, live record writes, environment changes or deployment. Django verification used disposable localhost PostgreSQL databases. Browser non-GET requests were blocked. The user-controlled Django/app runtime was not restarted.

### 7. Tests performed

- **70/70 focused Django tests passed in 26.675 seconds**: existing marketplace, executive, empty-state and low-stock dashboard suites plus existing canonical order-fragment, view-only permission, modal integration and seven-column/eye-template checks. System checks reported no issues. Actual fixture HTML/JSON was exported for browser verification.
- The initial run exposed an existing test assumption: full Orders rows include `role="row"`, while the canonical detail fragment omits that structural attribute. The comparison now verifies every controller-consumed `data-*` attribute; no production row semantics were changed. The final run passed with the original no-write checks retained.
- **2740/2740 Chromium checks passed across 20 actual Django fixture renders and eight widths (280–1920px)**. Checks cover separate full-column cards, exact 16px spacing, internal headers, all seven/three columns, actual row values and URLs, matching header/cell alignment, horizontally reachable final columns, vertically visible rows, Refresh/error/recovery and the actual canonical order-details modal with restored focus. Existing surrounding dashboard behavior also passed. Desktop and phone table screenshots were inspected; order references stay on one line. No browser write request occurred. No claim of a full cross-browser accessibility gate is made.
- Evidence folder: `scratch/dashboard-operation-cards-20261031/`; results are `django-final.log`, `browser.log` and `browser-result.json`, with desktop/phone Orders and Inventory captures. Browser fixtures come from ORM-backed tests, not invented sales/alert data. Final scoped syntax/whitespace/reference checks are recorded in `file-checks.log` and `whitespace.log`.

### 8. Remaining limitations / troubleshooting

Refresh Dashboard to load stylesheet `20261031-operation-cards`. If a user-controlled Django process caches old templates, restart it locally and refresh. If the cards still appear joined, check that the old outer `marketplace-operations-card` is gone and each card has its own border. If columns seem absent, scroll inside the table region: the design intentionally retains all columns rather than hiding fields at phone widths. Do not remove a `<th>`/`<td>` to make the table fit.

Full width means the width of the existing Marketplace column; changing the overall Marketplace/Facilities grid would be unrelated scope. Width hints may expand for unusually long content, which remains reachable through the table's native scroll area. Verification uses source-rendered Django fixtures and Chromium, not a deployed site, other browsers or physical devices. No live production records were exercised.

Latest Top-Selling Products follow-up: one independent bordered ranking card is a direct Marketplace Overview child, outside Sales Overview, with 16px separation from the sales and existing operations containers. Keep its single internal title/subtitle, actual rankings or compact empty state, with no accordion/duplicate heading. Ranking queries, refresh and other dashboard sections are unchanged. Exact files, eight-part report, functions/data flow, measured tests, troubleshooting and safe practice are in the [ranked-sales guide](dashboard-marketplace-ranked-sales.md).

Latest priority-card refinement: Attention Required and Suggested Product Bundles have matching internal headers, subtitles, optional action and subtle dividers with 16px padding. Their cards share the taller content height when side by side; warning rows keep 12px padding, 8px spacing and actual name/count/action values. Marketplace and Facilities headings are outside separately bordered white content bodies. No backend data rule or unrelated section changed. The complete eight-part report, exact files/lines, renderer/data flow, measured verification, troubleshooting and safe practice are in the [Attention Required guide](dashboard-attention-required-4.md). The Welcome/toolbar reports below remain the current reference for those unchanged sections.

## Previous: Reduced Welcome and restored System Overview — October 31, 2026

### 1. Cause / reason

The latest user request reduces the enlarged Welcome container and brings back the visible System Overview heading. The previous follow-up used a 160px minimum height/28px padding and kept the KPI heading visually hidden.

### 2. Exact files changed

- `backend/static/components/css/admin_executive_refinement.css:50`: `.executive-toolbar` now uses a 120px minimum height and 20px padding, retaining its border, white surface, centered content and 16px bottom spacing.
- `backend/templates/dashboard/partials/system_overview_summary.html:3`: remove the conditional `visually-hidden` utility so the existing System Overview heading and subtitle are visible above the unchanged KPI cards.
- `backend/templates/dashboard/pages/admin_dashboard.html:29`: version the stylesheet as `20261031-welcome-compact`.
- `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3` and `docs/web-ui-ux-guidelines.md:9`: persist the latest layout, superseding the prior height/hidden-heading choice.

### 3. Changes made

Welcome is 40px shorter at its minimum desktop height, with less internal padding. Long names/text can still increase its height naturally. System Overview and its original supporting description are visible again. The inline right-aligned date/Refresh row, selected values, 12px control gap and other dashboard sections remain unchanged. The 16px gap now leads into the visible System Overview section; its heading sits before the cards.

### 4. How it works / inputs, outputs and data flow

The same authenticated Django context renders Welcome text and the existing KPI partial. Removing a presentation utility changes the heading's visibility without changing its id, accessible region label, KPI values or JavaScript hooks. CSS changes only minimum height/padding. Existing `load()`/`render()` functions continue passing selected periods to the same API and displaying its actual data.

Safe practice: select Last 30 Days, Refresh, and verify the selected value persists. Resize to phone width and confirm Welcome text wraps without clipping and System Overview remains visible. Temporarily adjust `min-height` in DevTools, then reload to restore the saved 120px minimum. No data edits are required.

### 5. Backend / API behavior

Unchanged: no JavaScript logic, request/response, date default, permissions, aggregate or business-rule changes.

### 6. Database / migration impact

None. No live writes, migrations, environment changes, server/app restart or deployment. Test records were confined to disposable localhost PostgreSQL databases.

### 7. Tests performed

- **24/24 focused Django executive/empty-state tests passed in 10.912 seconds**, exporting actual current-template fixtures.
- **385/385 Chromium checks passed across ten renders/eight widths (280–1920px)**. Verified visible System Overview, Welcome's minimum height of 120px/reduced desktop height, preserved border/spacing, inline desktop toolbar, Last 30 Days, Refresh/custom dates, loading/error/retry, menus, responsive layout and no browser writes. Desktop rendering was inspected.
- Evidence: `scratch/dashboard-welcome-compact-20261031/django.log`, `browser.log`, `browser-result.json` and `last30-1440.png`. Scoped file/whitespace checks accompany these results.

### 8. Remaining limitations / troubleshooting

Refresh Dashboard to load `20261031-welcome-compact`; restart the user-controlled Django process if it retains the older template. If System Overview remains absent, check that its header no longer has `visually-hidden`. On phones, long text can make Welcome taller than 120px; the height is deliberately a minimum. Verification used Chromium/source-rendered tests, not a live deployment or physical-device certification.

## Previous: Single-row controls and taller Welcome — October 31, 2026

### 1. Cause / reason

The user's screenshot shows the selected range and update time on separate lines beneath the controls. The latest follow-up asks for one row and more Welcome container height. The scoped controls wrapper was still a single-column grid, while Welcome used only 20px padding without a minimum height.

### 2. Exact files changed

- `backend/static/components/css/admin_executive_refinement.css:38`: `.dashboard-global-controls` becomes a right-aligned, vertically centered flex row with a 12px gap. At line 41 the existing form follows the metadata, keeping the selector/Refresh at the far right. At line 50, `.executive-toolbar` gains a 160px minimum height, 28px padding and centered content.
- `backend/templates/dashboard/pages/admin_dashboard.html:29`: change only the CSS version to `20261031-controls-inline`.
- `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3` and `docs/web-ui-ux-guidelines.md:9`: record this follow-up and its verification. Earlier reports below are history.

### 3. Changes made

The selected date range, update time, period selector and Refresh now share one desktop row. The existing controls remain far right, outside the header and Welcome. Their 12px gap and the 16px spacing before Welcome/KPIs remain. Welcome is taller, with its text centered vertically inside the same bordered white container. Content can increase its height naturally; no fixed height clips long names or enlarged text. Other dashboard sections remain unchanged.

### 4. How it works / inputs, outputs and data flow

CSS flex alignment replaces the grid that previously placed each child on a new line. The existing form is visually ordered last; the two preceding text nodes are not keyboard controls, so the selector/Refresh keyboard order remains natural. Responsive wrapping prevents narrow-screen page overflow.

The existing Django period/update-time values still render the same form IDs and metadata. The existing `load()` request and `render()` callbacks continue updating those values; CSS changes only their position. Example: selecting Last 30 Days still submits `period=last_30_days`, and the response's dates/update time appear alongside the same selector and Refresh button.

Safe practice: select Last 30 Days, click Refresh and inspect the existing Network request. Resize from desktop to phone width; verify one desktop row, natural phone wrapping and no page overflow. In DevTools, temporarily increase Welcome's `min-height`, then reload to restore 160px. No data changes are needed for this exercise.

### 5. Backend / API behavior

Unchanged. No JavaScript behavior, selected value, default period, endpoint, permission, query, request or response changes.

### 6. Database / migration impact

None. No live writes, schema changes, migrations, environment changes, server restart or deployment.

### 7. Tests performed

**380/380 Chromium checks passed across ten renders and eight widths (280–1920px)** using existing actual Django fixture exports with the current stylesheet. Checks include vertically aligned single-row desktop metadata/controls, Welcome height of at least 160px, retained 12px/16px spacing, right alignment, borders, no page overflow, Last 30 Days, Refresh, custom dates, keyboard cancel/focus, loading/error/retry and navigation. Browser writes were blocked. Desktop and phone renders were inspected. Evidence is in `scratch/dashboard-controls-inline-20261031/browser.log`, `browser-result.json` and `last30-1440.png`/`last30-390.png`.

No new backend test run was needed for this two-file CSS/cache-version change. The preceding follow-up's 24 focused Django results remain historical, not a claim of rerunning them. Scoped whitespace/file checks are recorded with this follow-up.

### 8. Remaining limitations / troubleshooting

Refresh the dashboard to load `20261031-controls-inline`. On narrow screens the toolbar wraps to preserve readability rather than forcing horizontal page scrolling. Long Welcome content can make the container taller than 160px. Verification used Chromium and existing server-rendered fixtures; no server deployment or physical-device certification is claimed. If the metadata remains stacked on desktop, confirm the new stylesheet version and computed `display: flex` on the controls wrapper.

## Previous: Controls row and bordered Welcome Back — October 31, 2026

### 1. Cause / reason

The latest request moves the existing period selector and Refresh out of the main header into their own far-right row above Welcome Back. Previously the controls were in the header, their gap was 8px, Welcome had no border, and its bottom margin was 20px. This update supersedes those positions in the earlier report below.

### 2. Exact files changed

| File / current line | Anchor and change |
| --- | --- |
| `backend/templates/partials/admin_header.html:26` | Remove only the global date-controls include; retain title, notification/chat/profile and session components. |
| `backend/templates/dashboard/partials/executive_dashboard.html:2` | Add `executive-controls-row` containing the existing `global_date_filter.html` include. Welcome stays in its own sibling `executive-toolbar` at line 5; its copy now refers to the controls above. |
| `backend/templates/dashboard/partials/system_overview_summary.html:3` | Keep the existing System Overview heading/id for screen readers using the shared `visually-hidden` utility on Super Admin. This allows the actual KPI cards to begin exactly 16px below Welcome. No KPI values, labels, links or grid rules change. |
| `backend/static/components/css/admin_executive_refinement.css:35` | New controls-row positioning, 12px control gap and retained right-aligned date/update metadata. Line 49 gives Welcome the existing white surface, neutral border, 10px radius, 20px inner padding and 16px bottom spacing. Remove obsolete header-control placement rules; preserve other section styles. Controls wrap to the right only when the available width cannot fit both. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | CSS cache version becomes `20261031-controls-row` so the revised layout loads. |
| `backend/static/components/js/admin_dashboard_filter.js:4` | Correct the layout comment; executable filtering/Refresh/custom-range/token/request logic is unchanged. |
| `backend/core/modules/reports/test_dashboard_executive.py:201` | Update the existing layout expectation: one date/Refresh component outside the header and before Welcome. Line 274 optionally exports a real Last 30 Days fixture for browser verification. |
| `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:9` | Record the latest layout and verification. Earlier implementation reports are retained as history. |

### 3. Changes made

The existing date selector (including Last 30 Days) and Refresh sit at the content area's far-right edge, outside both the main header and Welcome card. Their gap is 12px. The row ends 16px above the bordered Welcome card, and the first KPI cards start 16px below it. Welcome's text stays inside the white bordered container. The System Overview heading still names the KPI region for assistive technology while taking no visible layout space. Selected period, date options and default behavior remain unchanged.

Other dashboard sections, KPIs, permissions, typography, navigation and backend calculations retain the earlier implementation. The controls remain usable on narrow screens; date-range/update metadata is preserved below them and custom dates remain clear of the sidebar.

### 4. How it works / functions, inputs, outputs and data flow

This is a template/CSS placement change. `executive_dashboard.html` includes the same `global_date_filter.html` once, using the existing `dashboard_period` and `dashboard_updated_at` inputs. It outputs the same form, select, Refresh button, metadata and custom-date IDs. The existing `load()` controller in `admin_dashboard_filter.js` continues sending period/grouping parameters to the existing dashboard endpoint. The response goes to the same `render()` functions and dashboard data listeners. Moving the form does not change these inputs or outputs because the controller finds `[data-global-dashboard]` independently of the form's position.

The row uses flex alignment to the end; its action group uses `gap: 12px`. Margins of 16px separate the row, Welcome and KPI group. The shared hidden-heading utility removes the extra visual heading height while preserving its accessible label.

Safe practice example: select Last 30 Days and inspect Network for `period=last_30_days`; click Refresh and confirm the same selected period is requested without a page reload. Then resize to a phone width and use Custom Range, Cancel/Escape and Apply. Verify that the controls remain outside Welcome and do not cover the sidebar. To practice styling locally, change only the controls' gap in browser DevTools, measure the changed distance, then reload to restore the saved 12px value. This exercise writes no application records.

### 5. Backend / API behavior

No executable JavaScript, endpoint, query, authentication, date validation, default period, Refresh, abort/retry, tab-token or business-rule change. Existing Django API responses and actual data sources remain in use. No new button or filter was added.

### 6. Database / migration impact

None. No schema/migration, live data, environment or remote deployment changes. Verification used disposable localhost test databases and intercepted read-only browser requests; non-GET browser requests were blocked. No server/app/device was launched or restarted.

### 7. Tests performed

- **24/24 focused Django tests passed in 8.352 seconds**: existing executive/empty-state suites, including the updated placement expectation, saved-bundle refresh, selected dates, role isolation and real-data rendering.
- **364/364 Chromium checks passed across ten actual Django fixture renders**, at widths 1920, 1440, 1280, 1024, 768, 390, 320 and 280. Measurements verify the 12px control gap, right alignment, separate containers, all four Welcome borders, 16px row-to-Welcome spacing and 16px Welcome-to-actual-KPI spacing. Existing Refresh, duplicate-request prevention, Last 30 Days, custom dates, keyboard cancel/focus, error/retry, charts, menus, selected-period URL and narrow-screen behavior also passed. Desktop/phone screenshots were inspected. No browser write requests occurred.
- Changed JavaScript syntax and scoped whitespace checks are recorded alongside the results.
- Evidence: `scratch/dashboard-controls-row-20261031/django.log`, `browser.log`, `browser-result.json`, `last30-1440.png` and `last30-390.png`. The browser harness consumes the environment-gated ORM exports from the existing tests, not fabricated dashboard values.

### 8. Remaining limitations / troubleshooting

Refresh the dashboard to load the versioned CSS; restart the user-controlled Django process if its template loader retains the old markup. If controls still appear in the header, confirm the old include has been removed and only one `dashboardGlobalControls` exists. If the gap is wrong, inspect the computed `.dashboard-global-actions` gap and the versioned refinement asset. On exceptionally narrow widths the controls wrap with the same gap and right alignment. Existing KPI comparison text can make individual cards taller, but the measured distance above the first KPI row remains 16px.

This task was verified in Chromium and source-rendered Django tests; it does not claim a deployment or other-browser/device certification. The earlier broad Bundle Monitoring test expectation mismatches are documented in the previous report; that unrelated suite was not rerun for this layout-only follow-up.

## Previous: Super Admin minimalist SaaS dashboard — October 31, 2026

### 1. Cause / reason

The user approved using the written dashboard brief and existing CampusHub styling because no reference image was supplied. Inspection confirmed that the existing backend already calculates the eight KPIs, paid marketplace sales, physical bookings, service requests, users and audit activity. The main presentation problem was full-width stacked domain sections, with global date controls below the header. Confirmed integration gaps were that Recent Orders ignored the reporting period and the saved bundle preview did not participate in AJAX Refresh. Routine successful sign-ins could also crowd administrative work out of the five-row activity preview.

The rendered review found two further concrete causes: an old sales metric grid still reserved an empty icon column, splitting short currency values; and narrow custom-date/notification panels could extend underneath the persistent sidebar. The changes below address those causes within the Super Admin dashboard. Existing Products, other administrator dashboards and Flutter are outside this change.

### 2. Exact files changed

Paths below are relative to the project root. Line numbers refer to this implementation; use the named anchor if later edits move them.

| File / current line | Nearby anchor and change |
| --- | --- |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | Version the changed refinement stylesheet and four changed scripts with `20261031-saas-dashboard`; line 34 adds `super-admin-dashboard` only for the global dashboard. |
| `backend/templates/partials/admin_header.html:26` | `header-dashboard-controls`: render the existing global date filter only when `global_dashboard` is true. Notification, chat, profile and authentication components remain the existing shared components. |
| `backend/templates/dashboard/partials/executive_dashboard.html:1` | Welcome stays first; remove its duplicate date-control include. `executive-priority-grid` at line 13 holds Attention and Bundles; `executive-domain-grid` at line 25 holds Marketplace, Facilities, Services and Users. Activities remain outside that grid. Bundle loading/error hooks are at lines 16–20. |
| `backend/templates/dashboard/partials/system_overview_summary.html:1` | Remove the old left/right summary wrapper and nested Attention/Bundles includes. The eight cards now occupy the available width. Basis labels begin at line 18; Facilities/Bookings precede Marketplace Sales, and Pending Approvals links to Attention. Canonical values and secondary comparison hooks remain. |
| `backend/templates/dashboard/partials/recent_orders.html:1` | Executive branch uses Order ID, Buyer, Order Date, Total, Order Status, Payment Status and the existing Details action. Seller/item details remain in the existing authorized detail flow. Selected-submission-period wording replaces the all-date snapshot wording. The non-executive branch remains. |
| `backend/templates/dashboard/partials/super_marketplace_sales.html:16` | Describe completed, paid sales precisely; keep all three actual sales metrics and the line chart. Line 36 puts the existing Top Selling Products chart inside an expandable summary. |
| `backend/templates/dashboard/partials/super_facilities_overview.html:6` | Add existing Facilities/Bookings/Calendar destinations. Line 29 retains Most Booked Facilities inside an expandable summary. Selected-submission counts and all-date upcoming reservations retain their distinct meanings. |
| `backend/templates/dashboard/partials/super_services_overview.html:30` | Existing Requests by Service and Service Attention content become expandable summaries; line 50 starts the latter. Summary metrics, request trend and recent requests remain immediately visible. All existing renderer IDs/data hooks remain. |
| `backend/templates/dashboard/partials/system_activity_preview.html:9` | Rename Time to Date and Time. Existing five-row preview, result, permission-gated detail dialog and full-history link remain. |
| `backend/core/modules/marketplace/templates/marketplace/partials/super_recommendation_preview.html:5` | Explain the current saved snapshot and link View All to `bundle_monitor_list`. Keep two eligible stored pairs, actual seller responses, photos/fallbacks, error and empty states. |
| `backend/static/components/css/admin_executive_refinement.css:1` | Replace this dashboard-only refinement layer with local Montserrat and scoped navy/gold/neutral tokens. Header starts at line 23, KPI grid at 56, priority/domain grids at 79, currency icon-space fix at 105, table containment/intact amounts at 130, neutral audit results at 136, and responsive rules at 146. Other pages do not receive the body scope or this stylesheet. |
| `backend/static/components/js/admin_dashboard_filter.js:5` | Find the live main region independently of the controls' new header position. `positionCustomRange` at 148 clamps the panel to the content area. `renderRecentOrders` at 296 matches the seven-column executive table. `render` at 390 replaces the escaped server bundle fragment and retains tab authentication on its links. Existing abortable request/date/refresh/retry controller remains. |
| `backend/static/components/js/admin_dashboard_executive.js:2` | Scope Chart.js default Montserrat to this dashboard. Existing user chart font at line 84 also uses Montserrat; registration grouping/data calculations remain. |
| `backend/static/components/js/admin_services_overview.js:56` | Read chart tick font from the page's computed font so the dashboard uses Montserrat and existing other pages retain their own font. |
| `backend/static/components/js/admin_marketplace_products_chart.js:54` | Same computed-font approach for the existing product ranking chart. |
| `backend/core/modules/reports/dashboard_periods.py:321` | `build_dashboard_data`: apply the selected campus-local submission dates before taking the latest five Recent Orders. Canonical paid-sales, inventory, booking/service and KPI calculations remain. |
| `backend/core/modules/reports/dashboard_executive.py:115` | `executive_overview`: exclude routine `login_success`/`logout` events from the bounded preview, retaining newest-first ordering and failed authentication. Full `AccountActivity` history remains stored and accessible. |
| `backend/core/modules/reports/views.py:1359` | Existing `admin_dashboard_api`: preserve GET/authentication/Super Admin gate/date/error handling; line 1376 adds `bundle_preview_html` using the same permission-checked saved-pair getter and escaped template as the first render. Import at line 17. |
| `backend/core/modules/reports/test_dashboard_executive.py:201` | New header placement, layout hooks, saved-fragment/no-Apriori and role-isolation regression. Update earlier layout assertions for the requested View All link. |
| `backend/core/modules/reports/test_dashboard_marketplace.py:137` | Change the old all-date Recent Orders assertion to the new selected-period requirement. Line 212 verifies Manila midnight boundaries, unpaid-order inclusion in recent activity, paid-sales exclusion, and unchanged orders/stock. |
| `backend/core/modules/reports/test_dashboard_operations.py:79` | Verify meaningful admin work and failed authentication survive a flood of routine sign-ins without deleting history. |
| `backend/core/modules/reports/test_dashboard_empty_states.py:70` | Explicitly set the isolated order's submission date to the fixture date; required now that recent orders correctly filter by submission. |
| `backend/core/modules/reports/test_dashboard_kpi_cards.py:19` | Update requested KPI ordering, actual destinations, approval anchor and basis labels; keep large-currency and no-mining checks. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:798` | Update preview wording/View All expectations; line 811 verifies API Refresh returns two saved pairs without mining or changing records. Existing image, response and error/empty checks remain. |
| `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:9` | Record this implementation, data definitions, verification, current layout and scoped typography choice. Historical reports below remain as history. |

### 3. Changes made

Desktop uses four KPI columns/two rows, Attention beside saved bundle suggestions, then Marketplace beside Facilities and Services beside Users. Activities use the full content width. Tablet stacks the domain panels; phones stack all main sections and adapt KPIs to the available width. Native expandable summaries keep the secondary product ranking, most-booked ranking, service distribution and service attention available without extending every panel on first load.

The header contains the existing period choices, Refresh, notification/chat controls and profile. The same existing custom-date form still supports Apply, Cancel and Escape. Its panel now fits to the right of the sidebar. Narrow header dropdowns also anchor within that content area. Controls retain keyboard focus feedback, reduced-motion behavior and suitable touch heights. Tables scroll within focusable regions on narrow screens rather than causing page overflow. Currency values no longer lose width to an unused icon column.

The palette is navy `#1A1851`, gold `#FCB316`, white, `#F7F8FC`, `#E8EAF0` borders and existing readable text colors. Audit result chips use neutral navy/surface styling with their actual result words. Bundled Montserrat applies only to the Super Admin dashboard, including its shared shell while this page is open. The CampusHub wordmark remains SugarPie. No new framework, dependency, image generation or replacement asset was introduced.

### 4. How it works / functions, inputs, outputs and data flow

Initial page: existing authenticated `admin_dashboard_page(request)` resolves the period, obtains actual Django ORM projections and saved recommendation rows, then renders the existing partials. `global_dashboard` determines the scoped layout and header controls.

AJAX: changing a preset, submitting custom dates or clicking Refresh calls the existing `load()` controller. It preserves the tab token, aborts superseded requests, disables Refresh while active and updates loading feedback. The protected dashboard endpoint calls `build_dashboard_data(params)`, adds the saved bundle HTML when authorized, and returns the established JSON plus that one additional property. `render(payload)` updates the same KPIs/tables/charts, replaces only the bundle preview's contents and dispatches the existing dashboard data event. Existing chart/user/service/activity listeners consume that event. Date/grouping choices, selected-range text, update time and URL remain synchronized. Errors show retry/stale feedback; they are not interpreted as successful empty results.

`positionCustomRange()` receives current element/viewport geometry and outputs CSS `maxWidth` and `left` values. It uses the main wrapper's left edge, which matters because the sidebar occupies usable screen width. Moving the filter to the header also required changing the old `controls.closest(...)` lookup: the controls are no longer descendants of the live main region.

`build_dashboard_data()` receives existing period/grouping query parameters and returns read-only aggregates. Recent orders now filter `MarketplaceOrder.created_at` by that period before sorting/limiting. Sales still use canonical `valid_sales_queryset()` and its recognized sales date. Submission date and paid-sales date therefore remain different concepts.

Metric definitions are intentionally different:

| Region | Population / time basis |
| --- | --- |
| Total Users KPI | All recorded web `accounts.User` rows, including administrators. No joins to duplicate profiles. |
| Active Sellers KPI | Current eligible active, unsuspended web seller access under the existing rules. Seller is permission status, not a new account type. |
| Total Products KPI | Current non-archived product catalog, under the existing counting rule. |
| Total Facilities KPI | All recorded Facility rows under the existing rule; the supporting availability text is current. |
| Orders / Bookings KPIs | Selected submission period; physical bookings exclude service requests and schedule blocks. |
| Marketplace Sales / Completed Orders / AOV | Actual eligible completed, paid transactions recognized in the selected sales period. AOV is sales divided by those eligible orders; no platform-profit claim. |
| Pending Approvals / Attention / Inventory | Current queues/snapshots independent of the reporting period. Low stock remains positive available stock at/below the configured threshold; zero is out of stock. Virtual bundles do not become independent physical inventory. |
| Upcoming Reservations | Next approved scheduled reservations across dates. Submission counts, scheduled use and recorded payment remain distinct; approval does not imply full payment. |
| Services | Selected submission-period request counts/trend/recent rows; Active Services and Service Attention are current snapshots. |
| Users Overview | New registrations combine recorded web/mobile account rows within the period. Verified Users combines recorded verified accounts as a current snapshot. Type distribution uses current typed mobile accounts and reports untyped records separately. These populations need not match the web-only Total Users KPI. |
| Activity preview | Latest five non-routine recorded events in the selected period. Full audit history, details permissions and sanitization remain. |
| Suggested Bundles | At most two current eligible saved pairs. This dashboard does not run Apriori, create/send/approve bundles, mix synthetic research into a live result or invent missing original evidence. Actual Support/Confidence/Lift and unavailable provenance remain in the existing detailed/research workflows. |

Safe annotated request example:

```text
GET /api/admin/dashboard/?period=custom&start_date=2026-10-01&end_date=2026-10-04
1. Existing session/Super Admin checks run.
2. Recent Orders uses submission dates in this inclusive Manila-local range.
3. Sales uses eligible completed/paid sales recognition dates in that range.
4. Current inventory/approval queues keep their snapshot meaning.
5. The existing browser renderers consume actual returned values.
```

Safe practice exercise: sign in locally as an authorized Super Admin, open browser Network tools, choose Last 7 Days, then Refresh. Inspect the existing `/api/admin/dashboard/` request and compare `period` with the Recent Orders caption and KPI basis labels. Expand Top Selling Products and switch Users grouping to Weekly; grouping reuses the already returned daily registration series. Verify no order, stock, booking or recommendation action was submitted. To practice a visual edit, change only `--executive-gap` in this scoped CSS on a local branch, refresh at phone/desktop widths, inspect the diff, then revert that exercise edit.

### 5. Backend / API behavior

Reused endpoint: GET `/api/admin/dashboard/`. Its existing Django JSON response remains the integration point; no duplicate DRF endpoint or business service was created. Unauthenticated users receive 401; unauthorized/inactive users receive 403; invalid ranges receive 400; database failures receive the existing non-sensitive 503 response. Existing no-cache/session behavior remains. The additive `bundle_preview_html` property is present only when `can_view_bundle_suggestions(user)` allows it. Django escapes record values in that server fragment; links reuse the existing tab-token helper.

The only aggregate behavior change is period-filtered recent transactions and the non-routine audit preview. Stored orders, approvals, stock/FIFO, bundle ownership/eligibility, payment/fulfillment, service/laboratory workflows, booking conflict rules, notifications and role permissions are preserved. Saved-pair refresh is read-only and does not invoke Apriori. Synthetic research remains a separate explicitly identified workflow; incomplete stored provenance is not reconstructed.

### 6. Database / migration impact

No model or migration changes. No data backfill, live order/inventory/booking/user/recommendation write, environment change, remote deployment or Kamatera action. Tests created/destroyed disposable localhost PostgreSQL test databases. An additional source-level localhost render/API check used `SET TRANSACTION READ ONLY`; actual counts, recent transactions and eligible sales matched their database queries. No server/app/device was launched or restarted.

### 7. Tests performed

- Full affected dashboard and bundle exploration: **264 Django tests run in 60.856 seconds; 262 passed, two unrelated existing expectation mismatches remained**. All 140 dashboard tests passed within this run. Covered period presets/validation, Manila boundaries, role gates, actual paid-sales calculations, physical/service separation, inventory/variants/bundles, empty states, bounded query behavior, saved-preview/no-mining behavior and audit privacy/order/detail permissions.
- Two remaining failures are in untouched behavior: `BundleMonitoringTests.test_source_tabs_dataset_never_mines_or_reads_live_recommendations` compares the exact ordering of equivalent Cache-Control directives; existing `accounts/middleware.py:26` emits the same directives in another order. `test_workspace_empty_saved_and_filtered_states_ignore_incidental_parameters` supplies `__at=irrelevant` while expecting authenticated content; existing middleware at line 39 correctly treats an invalid explicit token as anonymous and redirects. No authentication/cache behavior was weakened to satisfy these assertions.
- Chromium: **286/286 checks passed across ten actual Django fixture renders**, covering widths 1920, 1440, 1280, 1024, 768, 390, 320 and 280, populated/one/empty states, loaded local font, no duplicate IDs/page overflow, requested desktop pairings and responsive KPIs, actual chart initialization, order columns/intact amounts, expanders, loading/duplicate Refresh prevention, token preservation, preset/custom Apply/Cancel/Escape, weekly/monthly user grouping, 503/stale/retry recovery, bundle/activities/services errors, notification/profile menus and preserved Logout navigation. All non-GET requests were blocked. Source screenshots were inspected at desktop and phone sizes. These are isolated database fixtures, not production example numbers.
- Actual localhost source render/API: both 200 under a PostgreSQL read-only transaction; counts, selected-period Recent Orders, eligible paid sales and saved bundle preview matched actual source queries. No running-server reload was assumed.
- All four changed JavaScript files passed `node --check`. Python syntax and trailing whitespace checks passed across all 27 intentionally edited application/test/guide files; all 27 documented file/line references exist. Scoped Git whitespace checking passed with CRLF line endings recognized (`core.whitespace=cr-at-eol`); no bulk line-ending conversion was performed. Results: `file-checks.json` and `whitespace.log` alongside the browser/database evidence.

Reproducible local test command (uses the existing disposable PostgreSQL runner):

```powershell
backend/core/venv/Scripts/python.exe -u -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_dashboard_periods modules.reports.test_dashboard_executive modules.reports.test_dashboard_operations modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_bookings modules.reports.test_dashboard_services modules.reports.test_dashboard_low_stock modules.reports.test_dashboard_empty_states modules.reports.test_dashboard_kpi_cards modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions
node scratch/super-admin-saas-20261031/check.cjs
backend/core/venv/Scripts/python.exe -B scratch/super-admin-saas-20261031/verify_local.py
```

Artifacts: `scratch/super-admin-saas-20261031/django-verified.log`, `browser-result.json`, `browser.log`, `localhost-result.json` and actual rendered screenshots. The browser harness requires the environment-gated Django fixture exports and existing local Chromium/Playwright support. The generic design-skill kit scripts are not installed in this workspace; no kit-gate, full WCAG conformance or cross-browser/device certification is claimed.

### 8. Remaining limitations / troubleshooting

Restart the user-controlled Django process, then refresh the Super Admin dashboard to load changed Python and versioned assets. No restart/deployment was performed automatically. If controls seem inactive, inspect the browser's first JavaScript error and confirm the new filter asset version loaded; the live region lookup must be independent of the header. If Apply is covered, inspect `positionCustomRange()` and the main wrapper's left edge rather than hiding the sidebar. If amounts split unnecessarily, check that `.sales-overview__metric-value` has one content column and the new refinement stylesheet loaded.

The two unrelated Bundle Monitoring test expectation mismatches described above remain. Existing unknown bundle provenance is still unknown; missing data remains an honest empty/unavailable state. Charts retain the existing Chart.js CDN dependency and existing fallback text. Verification used Chromium and source renders; physical mobile devices, other browser engines, notification delivery and live deployment were not exercised. The large pre-existing worktree was preserved; only the files/anchors listed for this implementation were intentionally edited.

## Current: Daily / Weekly / Monthly registration grouping - October 24, 2026

### 1. Cause / reason

The user replaced the prior Daily/Cumulative requirement with calendar time grouping. Inspection confirmed the existing API supplies chronological daily registration counts, including zero days, restricted to the global reporting period. The minimal implementation groups that existing response locally. Weekly follows Monday–Sunday calendar weeks, consistent with the existing marketplace calendar-week convention, rather than seven-day windows starting on the selected date.

### 2. Exact files changed

| File / current line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/super_users_overview.html:14` | Existing dropdown becomes Group by: Daily (default), Weekly, Monthly; remove Cumulative. Reuse the same ID, label association, form class and responsive control. |
| `backend/templates/dashboard/partials/super_users_overview.html:20` | Existing exact-value table's Date column gains `data-user-trend-date-column` so it can become Week or Month. Other table hooks/disclosure remain. |
| `backend/static/components/js/admin_dashboard_executive.js:16` | `groupRegistrations(trend, grouping)`: copy daily rows, or sum them into Monday-start/calendar-month buckets; retain zero buckets and calendar years. |
| `backend/static/components/js/admin_dashboard_executive.js:48` | Existing input validation also requires valid ISO source dates before grouping. Invalid source data follows the existing unavailable/error behavior. |
| `backend/static/components/js/admin_dashboard_executive.js:71` | Existing `chart` helper now takes grouping metadata instead of a cumulative flag. Restore normal line styling/count labels, set X-axis unit to Date/Week/Month, and shorten visible weekly ticks while retaining full dates in tooltip/table labels. |
| `backend/static/components/js/admin_dashboard_executive.js:103` | Existing `renderTrend` callback groups the original daily payload and updates subtitle, canvas description, table headers/caption/rows and the same line chart. Cumulative calculation and wording are removed. |
| `backend/templates/dashboard/pages/admin_dashboard.html:623` | Executive JS cache version becomes `20261024-registration-grouping`. CSS is unchanged and retains its existing version. |
| `backend/core/modules/reports/test_dashboard_executive.py:243` | Existing environment-gated ORM exports gain a month-spanning calendar fixture; initial render assertions at line 266 expect the three grouping options and no Cumulative option. |
| `backend/core/modules/reports/test_dashboard_executive.py:283` | New source/API regression case creates isolated web/mobile registration dates crossing a year and Monday boundary; verifies actual daily counts and optionally exports browser fixtures. |
| `docs/dashboard-analytics-operations-update.md:3` | Current report, verification, debugging and learning guide. |
| `CAMPUSHUB_CONTEXT.md:3` | Persist this replacement of the cumulative view. |

### 3. Changes made

Daily shows the original per-day counts and dates. Weekly shows totals by Monday-start calendar week; Monthly shows totals by calendar month. The table's first column and X-axis title change to Date, Week or Month. Subtitles explicitly say grouped totals are limited to the selected reporting period. Weekly table/tooltip labels identify the Monday and year; compact axis ticks show month/day with at most four visible ticks to stay readable on phones. Monthly labels retain month/year.

Existing title, form style, 280px/240px chart drawing area, card height behavior, integer Y ticks, palette, tooltips, disclosure and responsive layout remain. The existing global period is unchanged. Grouping choices persist across period changes/Refresh within the page; reload defaults to Daily. Switching grouping makes no API request or page reload and does not redraw Users by Type.

### 4. How it works / functions, inputs, outputs and data flow

Unchanged flow: actual web/mobile registration records -> `users_overview(period)` -> zero-filled `executive.users.trend` inside the selected period -> existing `renderUsers` callback -> `groupRegistrations` -> existing chart/table renderer. There is no new endpoint or server grouping parameter.

The helper uses each row's ISO date, interpreted with UTC calendar operations solely to preserve the already campus-local date in browsers with other time zones. Weekly keys subtract `(getUTCDay() + 6) % 7` days to reach Monday; monthly keys use day one. Each selected daily count is added exactly once to its bucket. The original response remains unchanged, so repeatedly switching groupings cannot double-count.

Annotated example using actual isolated test records:

```text
Selected range: September 1–October 4, 2026.
Recorded nonzero dates: September 1 = 2; October 2 = 1; October 4 = 2.
Weekly: Week of August 31 = 2; September 7/14/21 = 0; September 28 = 3.
Monthly: September = 2; October = 3. All groupings total 5.
```

August 31 identifies the calendar week; no August registration is fetched or fabricated. First/last weeks and months include only supplied selected dates. Zero-count buckets remain because the backend already supplies every selected day. The separate year-boundary fixture verifies December 31 and January 1 share the Monday-start week of December 29, while January 5 starts a new week; months and years remain separate.

### 5. Backend / API behavior

No runtime Python, database query, API response, authentication, permission, registration logic or reporting-period changes. Cumulative behavior is replaced rather than retained as another feature. Existing loading/error/recovery disables stale grouping changes; missing Chart.js leaves the real grouped table usable. Five protected source hashes verify the registration projection, global filter script, operations/refinement CSS and executive section layout are unchanged. Other chart helper callers keep their existing defaults.

### 6. Database / migration impact

None: no fields, models, migrations, production records or sample production data. New dated records exist only in Django's isolated test database. Browser QA uses exported actual ORM results and intercepted GET responses. No deployment or service restart was performed.

### 7. Tests performed

- **57 Django tests passed**: executive dashboard, dashboard empty states and reporting periods. Includes actual source dates/counts, zero days, custom range, year/week boundary, permissions and initial grouping options. System check reported no issues. Log: `scratch/registration-grouping-review/django.log`.
- **3237/3237 Chromium browser/source checks passed across 24 renders**, at 1920, 1366, 1024, 800, 768, 390 and 320px, plus separate year-boundary scenarios at 1366, 390 and 320px. Real Chart.js verification uses month-spanning, single-day, week, year-boundary and empty ORM exports. The measured result and screenshots are in `scratch/registration-grouping-review/browser.log` and `measurements.json`. It verifies all three groupings, literal expected calendar buckets, preserved period totals, partial/zero buckets, year boundaries, repeated changes, matching chart/table/axis/tooltip labels, compact weekly ticks, keyboard selection/disclosure, responsive fitting, unchanged type-chart instance, no switch request, global Today/Last 7 Days/custom range, Refresh, loading/error/recovery and chart-library fallback. Five protected source hashes remain unchanged.
- Inspected final laptop and mobile screenshots. JavaScript/harness syntax and scoped whitespace checks completed without errors. The final served executive JavaScript request succeeded and its SHA-256 matched the workspace. CSS was not changed. No optional design-kit gate or full accessibility certification is claimed.

### 8. Remaining limitations / troubleshooting / safe practice

Grouping is local page state; full reload resets Daily. Partial calendar buckets are intentionally partial when the global range cuts through a week or month. Their calendar labels do not authorize fetching dates outside that range. The earlier unrelated narrow-screen header/Inventory overflow and custom-date popover/sidebar overlap remain outside scope; narrow custom-form submission is checked with the keyboard. Browser verification uses isolated exports rather than a live signed-in session. No complete WCAG certification is claimed.

If old Cumulative options remain, reload and verify the executive script URL ends in `20261024-registration-grouping`. Check that the initial template and loaded JavaScript come from the same workspace. If grouping becomes unavailable during refresh, use the existing Refresh/retry behavior; never substitute fabricated counts.

Safe practice: select an existing range beginning midweek and spanning two months. Compare the Daily table sum with Weekly and Monthly sums; all must equal New Users in Selected Period. Check that weeks begin Monday, months include years, and zero buckets remain. Change the global period and confirm the selected grouping persists with newly calculated buckets. This requires no account creation or edits.

## Current: Daily and Cumulative Registration chart views - October 24, 2026

### 1. Cause / reason

The existing registration trend supported daily counts only. The approved enhancement adds a local chart-view choice while retaining the existing global reporting-period filter and API. Inspection confirmed `users_overview(period)` already supplies every selected date in chronological order, with zero counts for dates without registrations. A client-side running sum is sufficient; no new query, account-total metric or endpoint is needed.

The user also clarified standing approval: proceed with requested, agreed scoped changes without repeating approval questions. This clarification supersedes the wait-for-approval boilerplate for this task; unrelated or destructive actions are not authorized by it.

### 2. Exact files changed

| File / current line | Anchor, change and reason |
| --- | --- |
| `backend/templates/dashboard/partials/super_users_overview.html:12` | `.user-trend-heading`: group the existing title with one labeled native `#userRegistrationView` dropdown, reusing `.dash-select`. Daily is the default. `aria-controls` references the existing chart and newly identified existing table. |
| `backend/templates/dashboard/partials/super_users_overview.html:16` | Subtitle gains a data hook; table at line 20 gains an ID/caption/column hook for matching selected-view labels. Existing rows, disclosure, empty/fallback messages and Users by Type remain. |
| `backend/static/components/js/admin_dashboard_executive.js:14` | `trendView` / `renderTrend`: retain the current local view and a redraw callback for the latest valid daily payload. |
| `backend/static/components/js/admin_dashboard_executive.js:16` | `failUsers`: clear the callback and disable view changes while existing user content is unavailable. `renderUsers` validates nonnegative safe integer counts and the aggregate before displaying a series. |
| `backend/static/components/js/admin_dashboard_executive.js:49` | Existing nested `chart` helper accepts an optional cumulative flag. Only the line chart uses its dynamic dataset/Y-axis/tooltip labels and zero tension; the doughnut keeps the existing defaults. |
| `backend/static/components/js/admin_dashboard_executive.js:80` | `renderTrend` derives fresh selected-view entries, updates labels/canvas description/table and redraws only the registration chart. The change listener at line 101 invokes that callback without fetching data or redrawing Users by Type. |
| `backend/static/components/js/admin_dashboard_executive.js:131` | Existing global loading event clears the callback and disables the dropdown, preventing changes based on stale period data until the normal response arrives. |
| `backend/static/components/css/admin_dashboard_operations.css:207` | Local heading/control styles: right-side compact control, normal wrapping and existing form styling; within the existing 800px breakpoint (line 228), stack it below the title. Preserve the 280px desktop / 240px stacked chart and content-driven card. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Operations CSS and executive JS (line 623) receive cache version `20261024-registration-views`. Other assets retain their versions. |
| `backend/core/modules/reports/test_dashboard_executive.py:229` | Extend the existing actual-registration test with custom-range API assertions. Environment-gated exports at line 243 supply actual four-day/week pages and responses for browser verification. Existing empty-render test at line 263 checks the accessible two-option control. |
| `docs/dashboard-analytics-operations-update.md:3` | Current implementation, verification, troubleshooting and safe exercise. |
| `CAMPUSHUB_CONTEXT.md:3` | Persist view behavior and the clarified standing approval preference. |

### 3. Changes made

One Chart View dropdown offers Daily Registrations (initial default) and Cumulative Registrations. The title and Daily subtitle remain; Cumulative shows “Running total of new registrations within the selected period, starting from zero.” Switching updates the single line chart, Y-axis title, tooltip wording, canvas description, exact-value table heading/caption/rows immediately. The existing View chart data disclosure stays open or closed as the user left it.

There is no new date filter, chart or dashboard section. Switching views makes no API request, page reload or Users by Type redraw. The current choice survives global period changes and Refresh within the page; a full page load starts at Daily. The existing registration chart height, intrinsic card sizing, palette, integer ticks and dates remain. Small cards wrap the control naturally; the existing mobile breakpoint places it below the heading.

### 4. How it works / functions, inputs, outputs and data flow

Unchanged backend flow: actual web `date_joined` and mobile `created_at` records -> `users_overview(period)` -> chronological zero-filled `executive.users.trend` -> existing protected page/API -> `renderUsers(data)`. That function keeps a callback closing over the newest valid original daily payload. The callback maps it to new objects for each redraw, so the original response is never turned into cumulative values or accumulated twice.

Annotated example using the isolated ORM fixture from the existing registration test:

```javascript
// Four selected dates have actual fixture counts [0, 1, 0, 2].
let total = 0;
const entries = data.trend.map(row => ({
    ...row,
    count: cumulative ? (total += row.count) : row.count,
}));
// Daily: [0, 1, 0, 2]. Cumulative: [0, 1, 1, 3].
```

The accumulator begins at zero and counts only registrations inside the current period. Points represent totals through each displayed date: if the first date has registrations, its end-of-day point includes them. No artificial extra date/record is inserted, and prior accounts are not included. Linear segments in Cumulative mode avoid smoothing overshoot on otherwise flat/increasing totals; Daily retains its existing tension. Y-axis titles are respectively Number of new registrations and Cumulative registrations. The subtitle/caption/tooltip explicitly establish the selected-period basis.

The existing `campushub:dashboard-data` event installs a fresh callback for the new period while retaining the dropdown value. The existing loading/error events clear it and disable the control; successful recovery re-enables the same selected mode. A missing chart library still leaves the selected-view table working through the existing fallback. A valid all-zero period retains the honest empty chart state and real zero table rows.

### 5. Backend / API behavior

No runtime Python, query, API response, reporting-period calculation, authentication, registration, permission or recommendation changes. Only existing frontend rendering uses the optional view. The global filter script remains unchanged; no view parameter is sent to the API or added to the URL. Source hashes protect the actual data projection, global filter script, executive section layout and unrelated refinement CSS. Users by Type retains its data, chart instance and DOM during view-only changes.

### 6. Database / migration impact

None: no models, fields, migrations, live data writes or sample production records. Django tests use the isolated PostgreSQL test database; browser responses come from those actual exported fixtures. No deployment or server restart was performed.

### 7. Tests performed

- **56 Django tests passed**: `modules.reports.test_dashboard_executive`, `modules.reports.test_dashboard_empty_states` and `modules.reports.test_dashboard_periods`. Covers actual source counts/zero dates, custom-range API, authorization, period boundaries, query behavior, empty states and accessible initial control. System check reported no issues. Log: `scratch/user-registration-views-review/django.log`.
- **2162/2162 Chromium browser/source checks passed across 21 renders** at 1920, 1366, 1024, 800, 768, 390 and 320px. Verification runs real Chart.js using actual isolated multi-day, single-day, week and empty exports. The measured result and responsive screenshots are recorded in `scratch/user-registration-views-review/browser.log` and `measurements.json`. Checks cover both modes, repeated toggles/no double accumulation, zero baseline/days, monotonic cumulative data, matching table/labels/tooltip, integer ticks, keyboard focus/disclosure, no view-switch request or period change, unchanged type-chart instance/content, Today/Last 7 Days/custom date form, Refresh, loading/error/recovery, empty/chart-library fallback and four protected source hashes.
- Inspected laptop and mobile screenshots. The multi-day ORM fixture has Daily `[0, 1, 0, 2]` and Cumulative `[0, 1, 1, 3]`; a Today refresh correctly resets the period sum to that day's two registrations. JavaScript and harness syntax checks and scoped whitespace checks completed without errors. Both served CSS and JavaScript requests succeeded and SHA-256 matched final workspace files. Optional design-kit gate scripts remain unavailable; no kit gate or full accessibility result is claimed.

### 8. Remaining limitations / troubleshooting / safe practice

The chart view is local page state, not a saved account preference: reload returns to Daily by design. Cumulative means new registrations within the selected range, never the total existing account population. Browser verification uses isolated fixture responses, not a live authenticated session or live registration writes. The earlier unrelated header/Inventory overflow at 320px remains outside scope. The existing custom-date popover can also overlap the sidebar at narrow widths; QA uses keyboard submission on those widths and pointer submission on desktop, leaving that unrelated filter unchanged. The new view-control wrapper explicitly caps its width to the chart card, including at 320px. No full WCAG certification is claimed.

If the control is disabled, wait for the existing dashboard request or use its existing Refresh action after an error. A failed request never becomes invented zero data. If labels/controls do not match after an upgrade, verify both operations CSS and executive JS URLs use `20261024-registration-views`. Do not alter the database aggregates or create another endpoint to fix local chart-view state.

Safe practice: choose an existing multi-day period, open View chart data, compare Daily values with successive Cumulative totals, then switch back. A zero day should be zero in Daily and flat in Cumulative. Change the existing global period and verify accumulation starts over for that range while the selected mode remains. Confirm the type chart stays unchanged during mode switches. This exercise needs no account creation or edits.

## Current: Users by Type chart beside its table - October 24, 2026

### 1. Cause / reason

Users by Type previously rendered a full-width 240px chart wrapper followed by its account distribution table in ordinary block flow. The user requested a compact donut on the left and the existing table on the right, with mobile stacking. No data or chart calculation defect was found.

### 2. Exact files changed

| File / current line | Anchor, change and purpose |
| --- | --- |
| `backend/templates/dashboard/partials/super_users_overview.html:21` | Add one plain `.users-type-layout` wrapper around the existing distribution chart, empty/fallback messages and table. Existing IDs, data hooks, cells and conditional visibility remain unchanged. The unclassified-account note remains outside the wrapper at line 27, beneath both columns. |
| `backend/static/components/css/admin_dashboard_operations.css:212` | `.users-type-layout`: wrapping Flexbox row with 16px gap and vertical centering. The existing donut wrapper is 180px square; the table fills the remaining width and uses automatic column sizing. Empty/fallback messages occupy their own full-width row. |
| `backend/static/components/css/admin_dashboard_operations.css:218` | Scoped distribution table cell override: 4px horizontal padding and normal word wrapping keep existing labels/counts/shares readable beside the donut. Vertical padding remains 8px. |
| `backend/static/components/css/admin_dashboard_operations.css:225` | Inside the existing 800px breakpoint, switch the wrapper to block flow: centered chart above the full-width table with 16px separation. Narrow desktop/tablet cards also wrap naturally when both columns cannot fit. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Operations CSS version `20261024-users-type-layout` requests the updated stylesheet. |
| `docs/dashboard-analytics-operations-update.md:3` | Current implementation, data-flow, verification and troubleshooting report. |
| `CAMPUSHUB_CONTEXT.md:3` | Record the latest scoped card layout. |

### 3. Changes made

Only the contents of the existing Users by Type card are rearranged. The chart appears left and the table right when space permits, centered vertically as a pair. The 180px donut is within the requested 180–220px range. The outer card remains content-driven and keeps its existing heading, subtitle, navy/gold colors, counts, percentages, labels, accessible table caption and unclassified-account note. Mobile shows the chart above the table. The existing Users Overview 60/40 outer grid, User Registration Trend sizing/data toggle and all other dashboard sections remain unchanged.

An initial laptop screenshot exposed fragmented Accounts/Student/percentage text with the original 8px horizontal cells. The targeted 4px horizontal padding and normal word wrapping resolved that readability issue without changing shared tables.

### 4. How it works / functions, inputs, outputs and data flow

The existing `users_overview(period)` projection supplies recorded mobile account counts, labels, percentages and unknown-type counts through `executive.users`. `super_users_overview.html` emits the same chart canvas/table rows/note. Existing `renderUsers(data)` continues to locate those elements by their unchanged descendant data attributes and redraw the same Chart.js doughnut on refresh. It already uses `responsive: true` and `maintainAspectRatio: false`, so the 180px canvas wrapper needs no JavaScript change.

Annotated layout example:

```css
/* Production rules are scoped to executive Users Overview. */
.users-type-layout { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; }
/* Fixed drawing size, rather than a fixed outer card height. */
.users-type-layout .users-chart { width: 180px; height: 180px; }
```

Inputs are the existing DOM, actual account distribution and available card width. Output is the same chart/table content arranged in two columns or stacked. Flex wrapping avoids a forced narrow table inside the existing outer dashboard proportions. The note stays beneath the wrapper; hiding an empty/unavailable chart does not reserve a blank chart column, and the real table remains available when the chart library fails.

### 5. Backend / API behavior

No Python, JavaScript, query, API, permission, chart calculation, registration-data or recommendation workflow changes. Existing canvas/table selectors, response contracts, count/percentage formatting and state toggles are preserved. Source hashes protect both dashboard scripts, the data projection, the executive section template and unrelated refinement CSS.

### 6. Database / migration impact

None: no fields, models, migrations, sample production records or live writes. Browser verification uses isolated ORM-generated pages/payloads and intercepted GET responses. No deployment or service restart was performed.

### 7. Tests performed

- **20 Django executive/empty-state tests passed**, including real registration/type projections, existing authorization and empty-state coverage. System check reported no issues. Log: `scratch/users-type-layout-review/django.log`.
- **599/599 Chromium browser/source checks passed across 28 renders (21 current, seven baseline)** at 1920, 1366, 1024, 800, 768, 390 and 320px. The measured result and screenshots are recorded in `scratch/users-type-layout-review/browser.log` and `measurements.json`. Checks cover donut dimensions, chart-left/table-right geometry, vertical centering, responsive stacking, exact table labels/counts/shares/note, unchanged chart values/colors/tooltips, registration-card height and disclosure behavior, refresh, honest empty states, chart-library fallback and five protected source hashes.
- Inspected final laptop and mobile screenshots. At 1920 and 1366px, the isolated populated Users by Type fixture shrank from 526px to 309px while User Registration Trend stayed 425px tall. The donut is 180px square and the table is centered beside it; current fixture labels/values fit without fragmented words. On mobile the donut is centered above the same table.
- Scoped `git diff --check` and QA script syntax check completed without errors. The local operations CSS request succeeded and SHA-256 matched the workspace. No optional design-kit gate or complete accessibility certification is claimed.

### 8. Remaining limitations / troubleshooting / safe practice

The existing 40% outer column is narrow at tablet widths such as 1024px, so the contents wrap naturally rather than compressing the table. The earlier unrelated header/Inventory overflow at 320px remains outside scope; the Users grid itself is checked there. Browser QA uses isolated exported fixtures rather than a live authenticated session. No full WCAG certification is claimed.

If the card remains stacked on a wide screen, confirm the loaded operations stylesheet URL ends in `20261024-users-type-layout`; inspect the available card width before widening unrelated dashboard columns. If a chart-library failure occurs, the existing fallback message and actual distribution table should remain visible without an empty left column.

Safe practice: resize the dashboard between desktop and mobile, verify the 180px donut moves above the table when narrow, and compare every account label/count/share and the unclassified note before and after Refresh. Also open and close the neighboring registration data toggle to confirm its layout is unaffected. Do not modify or create users for this exercise.

## Current: content-driven User Registration Trend card - October 24, 2026

### 1. Cause / reason

The user reported excessive space below View chart data in Users Overview. The confirmed source was `.users-chart-grid` in the operations stylesheet: its two-column CSS Grid used default vertical stretching. The always-visible type-count table makes Users by Type taller, so the adjacent registration card acquired the same height even with its own data table collapsed. Neither chart card has `h-100`, and the executive shared card rule already has `min-height: 0`; removing shared card styles would not address the grid cause.

### 2. Exact files changed

| File / current line | Anchor, change and reason |
| --- | --- |
| `backend/static/components/css/admin_dashboard_operations.css:205` | `.users-chart-grid`: add `align-items: start` so each existing card follows its own content. Preserve 60/40 columns, 16px gap and existing 800px stacking breakpoint. |
| `backend/static/components/css/admin_dashboard_operations.css:206` | Existing registration card identified by `aria-labelledby="userRegistrationTrendTitle"`: explicit `height: auto`, `min-height: 0`, 16px padding. This also overrides the unrelated shared mobile card padding of 12px without changing other cards. |
| `backend/static/components/css/admin_dashboard_operations.css:211` | `[data-user-trend-wrap]`: 280px desktop chart area and 8px space immediately before the existing data toggle. The original shared 240px chart rule remains for Users by Type. |
| `backend/static/components/css/admin_dashboard_operations.css:219` | Within the existing 800px breakpoint, only the registration chart becomes 240px high. Outer card height remains intrinsic. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Operations CSS version changes to `20261024-users-trend-sizing` so the browser requests the updated styles. |
| `docs/dashboard-analytics-operations-update.md:3` | Current implementation report, debugging and learning notes. |
| `CAMPUSHUB_CONTEXT.md:3` | Persist this approved scoped layout decision. |

### 3. Changes made

Both Users Overview chart cards top-align rather than forcing equal heights. The registration card ends after its own content and normal 16px bottom padding; opening View chart data naturally expands it. Its chart stays readable at 280px desktop / 240px stacked, with 8px between chart and toggle. The existing chart labels, gridlines, points, tooltips, date range, navy/gold/white styling, data table and neighboring Users by Type chart/table stay intact. No new card, section, control, chart, data or workflow is introduced.

### 4. How it works / functions, inputs, outputs and data flow

Unchanged data flow: `users_overview(period)` aggregates actual web/mobile registration dates and recorded account types -> existing `executive.users` page/API payload -> `super_users_overview.html` and existing `renderUsers(data)` -> Chart.js and the existing exact-value tables. `renderUsers` already sets `responsive: true` and `maintainAspectRatio: false`, so Chart.js responds to the changed wrapper height without JavaScript edits. The outer article remains content-driven; a bounded chart drawing area is retained because canvas charts need usable dimensions.

Annotated CSS example:

```css
/* Separate card heights, preserving the existing two-column grid. */
.users-chart-grid { align-items: start; }
/* Only the existing registration canvas wrapper receives this drawing height. */
[data-user-trend-wrap] { height: 280px; margin-block: 12px 8px; }
```

The production selectors are scoped to `.dashboard-executive .executive-users`. Inputs are the existing card DOM, chart data and available viewport width. Output is the same chart/table content in an independently sized card. Users by Type keeps its original 240px drawing area and its naturally taller visible table.

### 5. Backend / API behavior

No Python, JavaScript, calculations, queries, endpoints, date filters, authorization or recommendation changes. The template and refresh renderer are unchanged. QA source hashes protect both dashboard scripts, the user/executive templates, existing registration data projection and unrelated executive refinement CSS.

### 6. Database / migration impact

None: no fields, models, migrations or live-record writes. Browser verification uses actual isolated ORM-generated page/payload exports and intercepted GET responses. No deployment or server restart is required for the source change.

### 7. Tests performed

- **20 Django tests passed**: `modules.reports.test_dashboard_executive` and `modules.reports.test_dashboard_empty_states`, including actual registration dates/types, existing permission checks and empty states. Django system check reported no issues. Log: `scratch/users-trend-sizing-review/django.log`.
- **527/527 Chromium browser/source checks passed across 28 renders (21 current, seven baseline)** at 1920, 1366, 1024, 800, 768, 390 and 320px. The actual final result, measurements and screenshots are recorded in `scratch/users-trend-sizing-review/browser.log` and `measurements.json`; it checks card bottom spacing, chart/toggle gap, canvas height, unchanged columns/stacking, keyboard disclosure, growth on opening the data table, unchanged adjacent-card content/height, exact data parity, chart tooltip/axis settings, refresh, empty/library-failure states, overflow and seven protected source hashes.
- At both 1920 and 1366px, the populated isolated fixture's registration card changed from **526px to 425px**, while its drawing area increased from 240px to 280px. Space from the closed toggle's bottom to the card border changed from **154px to 17px** (16px padding plus border). Users by Type stayed **526px** tall. At mobile widths, the existing stack remains and the chart area is 240px; opening the exact-value table expands only the registration card.
- Inspected laptop and mobile screenshots with real Chart.js rendering. The local operations stylesheet request succeeded and SHA-256 matched the workspace. Scoped `git diff --check` and QA script syntax check completed without errors. Optional design-skill kit gate scripts remain unavailable; no kit gate result is claimed.

### 8. Remaining limitations / troubleshooting / safe practice

Verification uses isolated exported Django fixtures rather than a live authenticated session. The earlier unrelated header/Inventory overflow at 320px is outside scope; the Users chart grid is checked separately at that width. A chart-library failure intentionally preserves real tables and hides the unavailable chart wrapper. No complete screen-reader or WCAG certification is claimed.

If old spacing remains, confirm the operations CSS URL ends in `20261024-users-trend-sizing` and inspect `align-items` on `.users-chart-grid`: it should compute to `start`. Check that no local override reintroduces `height: 100%` on the registration article. Do not remove the bounded canvas wrapper height or alter data calculations to fix whitespace.

Safe practice: resize the dashboard from laptop to mobile, verify the cards stack at the existing breakpoint, focus View chart data and press Enter. The registration card should expand with its existing rows, collapse back to normal bottom padding and leave the adjacent chart's content unchanged. Refresh and compare the same dates/counts; no record creation or edits are needed.

## Current: restore one horizontal row per order - October 24, 2026

### 1. Cause / reason

The user clarified with a screenshot that each order must occupy one horizontal table row. The preceding scroll-removal change converted `tbody tr` into three/two/one-column grids below 1100px of card width and visually hid the shared header. That produced the rejected multi-line field layout. This correction supersedes that layout.

### 2. Exact files changed

| File / current line | Code anchor and change |
| --- | --- |
| `backend/static/components/css/admin_executive_refinement.css:108` | `Keep all nine fields in one table row`: remove all three order-container grid rules, generated field labels and header hiding. Retain native table rows. |
| `backend/static/components/css/admin_executive_refinement.css:109` | Scoped wrapper uses native horizontal access only when the table exceeds available width; the table at line 112 has a 720px readability minimum. |
| `backend/static/components/css/admin_executive_refinement.css:117` | Compact 8px vertical / 4px horizontal cell padding, with proportional header widths at line 124. All nine width percentages total 100. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | Cache version `20261024-orders-row` loads the corrected stylesheet. |
| `docs/dashboard-analytics-operations-update.md:3` | Current report and verification notes. |
| `CAMPUSHUB_CONTEXT.md:3` | Record the clarified single-row requirement. |

### 3. Changes made

One visible shared header now labels Order ID, Date, Buyer, Seller, Items, Total, Order Status, Payment and Action. Each order has nine cells aligned in one native table row. Names and longer values may wrap inside their own cells. The repeated per-field labels and stacked grids are removed. The existing five-record limit, View All, View Details, focus/hover treatments, palette, natural card height and neighboring Inventory Alerts layout remain.

An initial fit-to-card trial broke labels into fragments at the 1366px laptop width. Keeping the approved nine fields readable therefore requires horizontal access in narrow cards. The 720px table minimum is smaller than the original 1080px; wide desktop/tablet cards fit without scrolling. No content is clipped or hidden to make the scrollbar disappear.

### 4. How it works / functions, inputs, outputs and data flow

The unchanged `recent_marketplace_orders` helper reads the same actual order data. The existing template and `renderRecentOrders` function both emit the same nine-cell rows. Only the stylesheet changes their presentation: without `display: grid` on the rows, browser table layout aligns every record under the shared headings. Widths reserve more space for the identifier, statuses and details action, and less for the item count. The named container in the shared stylesheet remains available to other existing rules; that stylesheet is unchanged.

Annotated example of the current approach:

```css
/* Preserve one native row; narrower cards can expose every column. */
.recent-orders-table { width: 100%; min-width: 720px; table-layout: fixed; }
/* The production selectors scope these rules to Super Admin Recent Orders. */
.recent-orders-table-wrap { overflow-x: auto; }
```

Inputs are the existing table DOM and card width; output is one aligned row per existing order. No JavaScript recalculation or alternative data representation is introduced.

### 5. Backend / API behavior

Unchanged: Python, JavaScript, API payloads, sorting, reporting periods, authorization, order processing, recommendation generation and revenue calculations. Protected source hashes verify the order helper, refresh script, executive template and Inventory Alerts partial stayed unchanged.

### 6. Database / migration impact

None. No model, schema, migration or live-record changes. QA uses existing isolated ORM-generated exports and intercepted GET responses.

### 7. Tests performed

The targeted **29 Django dashboard/empty-state tests passed** and Django system check reported no issues. **1056/1056 Chromium browser/source checks passed across 21 renders**, using five-order, one-order and empty states at 3000, 2560, 1920, 1366, 1024, 390 and 320px; the measured result is recorded in `scratch/recent-orders-single-row-review/browser.log`. Checks explicitly verify native `table-row` display, equal vertical positions for all nine cells, visible shared headers, no generated field labels, actual-value/link/refresh parity, scrolling only when necessary, keyboard focus, error/loading/retry/recovery and protected source hashes. Screenshots and accessibility snapshot are in the same QA folder. Laptop and desktop screenshots were inspected. Scoped whitespace checks passed; the served stylesheet matched the workspace SHA-256.

### 8. Remaining limitations / troubleshooting / safe practice

Narrow cards, including the unchanged half-width laptop card, need horizontal scrolling to preserve readable nine-column rows. This is the explicit tradeoff from replacing the rejected stacked layout. The earlier unrelated 320px header/Inventory overflow remains outside scope. QA uses isolated exported fixtures rather than a live signed-in session; no complete WCAG certification is claimed.

If stacked fields remain after refresh, confirm the loaded refinement URL ends in `20261024-orders-row`, and inspect computed row display: it should be `table-row`. Safe practice: resize the existing dashboard, verify one order's nine cells stay on the same row, focus its Order ID and View Details links, and use the focusable table region to reach all columns when narrow. Compare its displayed data before and after dashboard refresh without modifying any record.

## Current: Recent Orders without internal scrolling - October 24, 2026

### 1. Cause / reason

The user's latest request removes scrolling from Super Admin Recent Orders and supersedes the earlier horizontal-scroll requirement. The executive refinement stylesheet enforced a 1080px table minimum inside a narrower card, while the existing responsive wrapper provided horizontal overflow. Nine columns therefore required scrolling even on laptops. Removing overflow alone would clip information or spill into Inventory Alerts, so the existing table now adapts to its actual card width.

### 2. Exact files changed

| File / current line | Anchor and purpose |
| --- | --- |
| `backend/static/components/css/admin_executive_refinement.css:108` | `Executive orders fit the card`: remove the 1080px minimum, use full available width, allow text/status wrapping and remove the internal overflow area. |
| `backend/static/components/css/admin_executive_refinement.css:173` | `@container recent-orders`: below 1100px of card content, present each existing table row as three columns of labeled fields. Below 440px use two columns, with Order ID spanning the row (line 227); below 240px use one column (line 230). |
| `backend/templates/dashboard/partials/recent_orders.html:5` | Executive table gains explicit `role="table"`, preserving its table semantics when CSS changes its display. Existing caption, column headings, row headings and navigation remain. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | Refinement CSS cache version becomes `20261024-orders-fit`. |
| `docs/dashboard-analytics-operations-update.md:3` | This current implementation and learning report supersedes the earlier scrolling presentation below. |
| `CAMPUSHUB_CONTEXT.md:3` | Record the latest presentation decision. |

### 3. Changes made

All nine fields, their order, latest-five limit, real values, statuses and existing links remain. Wide cards retain the conventional table. Narrow cards show labeled fields inside each existing row, separated by the existing subtle row boundary; no additional cards or records are created. Money stays right aligned. Headers become visually hidden in this layout but remain in the accessibility tree. Order IDs, hover/focus styles, navy/gold/white theme, card padding, natural height and neighboring sections are preserved. No internal horizontal or vertical scrolling is introduced.

### 4. How it works / functions, inputs, outputs and data flow

The unchanged `recent_marketplace_orders` helper supplies the same database projection to the template and existing `renderRecentOrders` refresh function. CSS changes only the presentation of their identical nine-cell rows. It reuses the existing `container: recent-orders / inline-size` declaration in `admin_marketplace_overview.css:134` (that file is unchanged), so the available card width determines the layout rather than a device assumption. The same selectors also match rows recreated during refresh.

Annotated example of the presentation rule:

```css
/* Same existing order row, three labeled fields per line in a narrow card. */
@container recent-orders (max-width: 1099px) {
    /* Scoped production selector also includes the executive dashboard/card. */
    .recent-orders-table tbody tr {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
```

Input: the existing nine-cell order row and available container width. Output: the same values and links presented without an internal scrollbar. Content determines the row/card height. Labels are CSS-generated from the fixed approved column order; update these labels if that order changes in a future task.

### 5. Backend / API behavior

No Python, JavaScript, query, API, permission, reporting-period, order-processing, recommendation or revenue-rule changes. Source hashes confirmed the recent-order data helper, refresh script, executive section template and Inventory Alerts partial were unchanged during this task. This presentation change does not regenerate recommendations or perform record writes.

### 6. Database / migration impact

No fields, models, migrations or production-record changes. Browser verification used isolated Django test exports and intercepted read-only responses. No live database mutation or deployment was performed.

### 7. Tests performed

- **29 Django tests passed**: `modules.reports.test_dashboard_marketplace` and `modules.reports.test_dashboard_empty_states`; system check reported no issues. Covers actual ORM projections, latest-five behavior, initial/refresh contracts and empty states. Log: `scratch/recent-orders-no-scroll-review/django.log`.
- **1026/1026 browser/source checks passed across 21 renders** at **3000, 2560, 1920, 1366, 1024, 390 and 320px**, using five-order, one-order and empty exports. Final measured result and screenshots: `scratch/recent-orders-no-scroll-review/browser.log` and `measurements.json`. Checks cover all nine values/labels, no Recent Orders internal scrolling or clipped fields, table/card sizing, right-aligned money, existing destinations, navy links, hover/focus, long names and Ready for Pickup, refresh parity, authorization-token preservation, loading/error/retry/recovery, and no browser writes/script errors.
- Chromium accessibility snapshot at 390px retains table, caption, all nine column headings, row heading, cells and named links: `accessibility.txt`. This is a structural check, not a full assistive-technology audit.
- Screenshots inspected at laptop, mobile and wide-table sizes. Only the scoped recent-order presentation changes; protected source hashes are checked by the browser harness.
- Local static CSS request succeeded and its SHA-256 matched the workspace file. Scoped `git diff --check` and browser harness syntax check completed without errors.

### 8. Remaining limitations / troubleshooting / safe practice

The page already overflowed at 320px before this edit: the existing Refresh control and Inventory Alerts extend past the viewport. A baseline render using the saved previous stylesheet confirms this in populated, one-order and empty states (`baseline.log`). Recent Orders itself fits at 320px. Other sections were kept outside this scoped change. At the wider tested sizes, whole-page overflow checks passed.

The full dashboard still needs normal page scrolling as content grows. Nine fields without horizontal scrolling occupy additional vertical space in narrow cards. Browser screenshots use actual isolated ORM fixtures, not a live authenticated user session; no new live-record audit was needed for unchanged data logic. The optional installed design-skill kit scripts are absent, so no kit gate or complete WCAG result is claimed.

If the old scrollbar persists, refresh the page and confirm the refinement CSS URL ends in `20261024-orders-fit`; inspect the loaded rule at the line-108 anchor before changing shared styles. If a future column changes, update the nine `::before` labels together with the template/refresh order.

Safe practice: open the dashboard, resize from laptop to mobile width, compare one existing order's nine displayed values with its existing View Details page, then refresh. Verify the values and order links stay the same, every field remains visible, and no scrollbar appears inside Recent Orders. Do not create or modify orders for this exercise.

## Current: nine-column Super Admin Recent Orders - October 24, 2026

### 1. Cause / reason

The user requested nine accurate transaction columns in the existing Super Admin Marketplace Overview card. The previous executive branch exposed only Order Number, Customer, Total Amount, Status and Date. The common read helper already supplied payment and purchased quantity but omitted seller presentation and legacy item totals. Existing CSS also targeted numeric positions in the five-column table and left Order ID links with browser-blue styling. The approved change extends the existing read projection and both initial/refresh renderers; it does not introduce an order model, endpoint, checkout workflow or dashboard section.

### 2. Exact files changed

| File / current line | Anchor and change |
| --- | --- |
| `backend/core/modules/reports/dashboard_marketplace.py:12` | `_recent_order_items(order)`: return purchased unit count and whether a legacy multi-item array has ambiguous ownership. |
| `backend/core/modules/reports/dashboard_marketplace.py:35` | `_recent_order_seller(order, ambiguous_items)`: use the recorded seller snapshot, then actual web/mobile product owner, or honest missing/ambiguous labels. |
| `backend/core/modules/reports/dashboard_marketplace.py:47` | `recent_marketplace_orders`: add `seller_name` / `item_count` to the existing payload and join the two existing owner relationships in the same bounded query. Existing fields, filters and sort remain. |
| `backend/templates/dashboard/partials/recent_orders.html:6` | Executive-only nine-column header and corresponding row at line 7. Keep View All, real order deep links, empty/loading/error states and the shared non-executive branch. |
| `backend/static/components/js/admin_dashboard_filter.js:324` | Executive branch of `renderRecentOrders`: matching nine cells, row heading semantics, independent status/payment spans, validated same-origin details links and preserved tab authorization. |
| `backend/static/components/css/admin_executive_refinement.css:108` | `Nine-column executive orders`: scope all overrides to `#recentOrdersSlot` inside the global executive dashboard; readable 1080px minimum table width, wrapping buyer/seller cells, natural card height, navy links, quiet badges and hover/focus states. Existing card padding and 8px cells remain. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | Refinement stylesheet version becomes `20261024-orders-nine`; the existing filter script at line 620 receives the same version. |
| `backend/core/modules/reports/test_dashboard_marketplace.py:137` | Existing latest-five/date/payment/link test gains projection checks and optional isolated page/payload exports. New tests at lines 174 and 192 cover snapshots, web/mobile/deleted owners, one-query rendering, legacy ambiguity, incomplete quantities, bundles and true zero quantities. Existing column assertions at line 220 follow the new labels. |
| `docs/dashboard-analytics-operations-update.md:3` | This implementation, debugging, data-flow and verification report. |
| `docs/orders-module.md:3` | Clarify the separate dashboard table and reuse of authorized Orders details. |
| `CAMPUSHUB_CONTEXT.md:3` | Record this current layout/data decision and approval preference. |

QA-only scripts, source baselines, test exports, screenshots, hashes and logs live in `scratch/recent-orders-nine-review/`. They are not application routes, dependencies, production records or migrations.

### 3. Changes made

Columns are exactly **Order ID, Date, Buyer, Seller, Items, Total, Order Status, Payment, Action**. Order ID and View Details use the same existing `/admin-orders/?order=<id>` destination. Django selects that order within the authorized Orders queryset, and existing Orders JavaScript opens its details modal. The established View All link remains. Order status uses existing labels, including Processing; payment displays its independent actual Paid/Unpaid value.

The card remains beside Inventory Alerts. At most five orders render. Money aligns right and item quantities center; names may wrap while identifiers, dates and statuses stay readable. The table scrolls horizontally inside the existing keyboard-focusable region when its columns exceed the card width, including on laptops. Required columns are not hidden or compressed away. Order links are navy with clear hover/focus treatment, and all status/payment badges use restrained navy/neutral styling. No fixed card height, new action, table, section or chart was added.

**Reporting-period behavior is deliberately unchanged:** Super Admin Recent Orders is the latest five records across all dates, sorted by `-created_at, -pk`. The selected reporting period still applies to its existing analytics, not to this operational snapshot. The Marketplace Admin caller retains its own existing scope/date filtering and its current table presentation.

### 4. How it works / functions, inputs, outputs and data flow

Existing authorized page/API request -> unchanged `build_dashboard_data` -> the existing `recent_marketplace_orders(queryset, limit=5)` call -> one joined PostgreSQL read -> the same initial template or existing dashboard refresh JSON -> the same card. Two fields are added to each existing row object; old `quantity`, amounts, status/payment, date, URL, product and image fields remain compatible. Product and both owner namespaces are selected together, so five rows do not require five owner queries. No full Orders-page decoration, inventory/history lookup or duplicate API is introduced.

`_recent_order_items` reads existing `customization.items` quantities only when a nonempty legacy item array is present. It returns `(count, ambiguous_items)`. Valid integer quantities are summed as purchased units, matching the Orders quantity convention; if any quantity is missing, malformed, boolean or negative, the count is `None` and the UI displays Not recorded rather than a fabricated zero. A genuine recorded zero remains 0. Ordinary product rows use their recorded `quantity`. Purchased bundles also use their own quantity; ingredient/component quantities are not additional purchased items.

`_recent_order_seller` returns a saved nonblank seller snapshot first, preserving checkout history. Otherwise, for an ordinary transaction, it follows the existing product's actual `mobile_seller` or `seller` relationship. A missing relationship returns Not recorded. Legacy arrays with more than one item have no guaranteed item-owner relationships, so they return Not fully recorded instead of attributing every item to the primary product owner. This model has no invented multi-seller parent order/suborder structure. Buyer text continues to use the existing saved buyer name, with the existing dash for a missing name.

Annotated payload example (illustrative structure, not a production record):

```python
{
    "quantity": 9,       # Original stored transaction quantity stays available.
    "item_count": 5,     # Two valid saved legacy quantities, 3 + 2.
    "seller_name": "Not fully recorded",  # No reliable owner for every legacy item.
}
```

`renderRecentOrders(orders)` receives this existing row array, limits executive output to five, creates text nodes safely, and keeps all nine cell positions identical to the template. It validates the existing `/admin-orders/` destination and retains `__at` tab authorization before cloning that link for View Details. The row identifier is a `th scope="row"` on both initial render and refresh. An API `null` count becomes Not recorded; zero stays zero. Loading, empty, HTTP-error and recovery use the original regions and handlers.

### 5. Backend / API behavior

Only the existing read-only presentation helper changes: its query joins owner relationships and its row dictionaries gain two fields. No data selection predicate, sort, route, endpoint, permission, order-processing action or Cash on Pickup rule changes. The Orders page continues to authorize and filter exact-order links server-side; a link does not grant access. Pending/unpaid orders may appear in Recent Orders, but revenue still comes from the unchanged completed + paid + positive-quantity eligibility helper. No Apriori or other dashboard component is changed. Hash verification confirms 139 protected service/assets/other dashboard partials remain unchanged.

### 6. Database / migration impact

No fields, models, schema or migrations. No live records were created, updated or deleted. The live verification script used a PostgreSQL transaction explicitly set to **READ ONLY** and verified that setting. Isolated regression test records and required academic test fixtures were created only inside Django's separate test database. No environment file, service restart, deployment or application dependency changes.

### 7. Tests performed

- **119 Django tests passed**, with no system-check issues, across reports' marketplace, periods, executive, empty-state and Marketplace Admin tests plus `modules.marketplace.test_orders_admin`. Log: `scratch/recent-orders-nine-review/django-final.log`. Existing Orders tests verify scoped/foreign and ambiguous-legacy access, tab tokens, separate payment state, Cash on Pickup confirmations, exact deep-link selection and bounded queries. New read-helper tests verify one joined query and accurate ownership/item fallbacks. Revenue tests retain exclusion of pending/unpaid/zero-quantity transactions.
- Initial combined run completed the 102 dashboard tests but stopped during Orders test-class setup because the reused test database lacked its expected BTLED/BSIT and HE/IA academic fixtures. `run_regression.py` supplies those prerequisites inside the existing Orders TestCase setup transaction, then runs the unchanged complete suite. No production seed or application-test fixture file was changed. The resulting complete run passed all 119 tests.
- **711/711 browser/source checks passed** across 12 actual-template/JavaScript Chromium renders at **1920, 1366, 1024 and 390px**, covering five-row, one-row and empty states. Verified exact column order and row values, maximum five rows, original/refreshed parity, separate badges, right-aligned totals, navy links, hover/focus, keyboard horizontal scrolling, exact same-origin order destinations, tab tokens, loading, HTTP-error, retry/empty and populated recovery. Other KPI values remain unchanged. Log: `browser-final.log`; results: `measurements.json`; verifier: `browser.cjs`.
- Visually inspected laptop and mobile captures, including both ends of the horizontally scrollable table: [laptop left](../scratch/recent-orders-nine-review/populated-1366-left.png), [laptop right](../scratch/recent-orders-nine-review/populated-1366-right.png), [mobile left](../scratch/recent-orders-nine-review/populated-390-left.png), [mobile right](../scratch/recent-orders-nine-review/populated-390-right.png).
- **Actual PostgreSQL result:** the live database contained **one order, Pending / Unpaid** at verification. Its projected order code/link, placed date, buyer, seller, unit count, total and independent statuses matched the stored record. It was excluded from recorded revenue. No additional live rows were inserted to make the table look populated. Results: `live-results.json` and `live-audit.log`; script: `live_audit.py`. The five-row browser cases came from isolated ORM tests.
- Production filter JavaScript passed `node --check`; scoped whitespace checks passed. Initial QA script syntax was corrected before the passing browser run. The final capture run parks focus before screenshots; separate checks still exercise visible keyboard focus and scrolling.
- Final local HTTP checks returned **200** for both versioned CSS and filter JavaScript, with bytes identical to the workspace sources. Protected hashes were checked again and the task-only diff was saved as `approved-changes.diff`. Log: `scratch/recent-orders-nine-review/final-checks.log`.

### 8. Remaining limitations, troubleshooting and safe practice

Legacy multi-item ownership cannot be reconstructed when not recorded. Not fully recorded is intentional; adding a complete multi-seller model is outside scope. The Items column means purchased units, not distinct product types or bundle ingredients. Some historical buyer/product metadata can remain missing. Browser checks use actual application assets with isolated ORM fixtures in headless Chromium; live database fields were checked separately in a read-only transaction. This is not certification of every browser or every historical record. The existing details destination is the authorized Orders workspace/modal, not a newly created standalone details page.

Use Ctrl+F5 if a refresh still shows five columns. Confirm both the refinement CSS and `admin_dashboard_filter.js` links use `v=20261024-orders-nine`. A correct initial table followed by misplaced refreshed cells indicates mismatched cached template/script versions. Inspect the nine header/cell positions together. If a details link shows no order, investigate existing role scope, the `order` parameter and tab token; do not weaken authorization. Horizontal scrolling is expected within the existing half-width card.

**Safe practice exercise:** open one existing order from Recent Orders and compare its placed date, item quantity, seller snapshot, amount, order status and payment status with the existing Details modal. Resize the browser, focus the table region and use arrow keys to reach Payment and View Details. Refresh and repeat without changing the order or payment. For an unknown legacy value, inspect its saved snapshot read-only rather than filling it with an assumed seller/count.

## Current: Marketplace heading hierarchy - October 24, 2026

1. **Cause / reason.** The user requested keeping Marketplace Overview as the main heading, renaming the subordinate Sales Overview to Sales Summary and removing its repetitive subtitle. Browser measurement also confirmed a specificity conflict: the shared `#salesOverviewTitle` rule in `admin_sales_overview.css:109` overrode the existing class-based subsection rule, producing an 18.4px subsection beneath an 18px main heading. The shared ID is retained for accessibility and script compatibility; a Super Admin-scoped selector now applies the already intended 15px subsection styling.
2. **Exact files changed.** `backend/templates/dashboard/partials/super_marketplace_sales.html:2` (`executive-kpi-heading`) changes the visible h3 label to Sales Summary and removes only its paragraph. `backend/static/components/css/admin_dashboard_operations.css:246` adds the scoped `#salesOverviewTitle` selector to the existing subsection typography rule. `backend/templates/dashboard/pages/admin_dashboard.html:27` updates that stylesheet's cache version to `20261024-sales-summary`. Existing assertions in `backend/core/modules/reports/test_dashboard_marketplace.py:354` check the new h3 and absence of its redundant subtitle; `backend/core/accounts/tests.py:545` updates the inherited Super Admin label expectation. This report and `CAMPUSHUB_CONTEXT.md:3` record the change. Marketplace Admin's separate Sales Overview label remains unchanged.
3. **Changes made.** Marketplace Overview and its subtitle stay outside the content cards. The smaller Sales Summary label precedes the same three cards: Marketplace Sales, Completed Orders and Average Order Value. Its redundant subtitle is removed. Existing 16px heading-to-card spacing remains. Sales Trend, Top-Selling Products, Recent Orders, Inventory Alerts, other dashboard areas, section order, data and controls are unchanged.
4. **How it works / inputs, outputs and data flow.** The existing `executive_mode` branch in `sales_overview.html:1` includes `super_marketplace_sales.html`. The latter receives the same `sales_overview.metrics` iterable; each metric supplies its existing label, value, currency and comparison text to the unchanged card loop. Only static heading output changes. No runtime function is added or modified, and JavaScript continues to find `salesOverviewTitle` by the same ID. The scoped selector wins over the shared ID selector without affecting other roles. Annotated example: `<h3 id="salesOverviewTitle">Sales Summary</h3>` keeps the accessibility reference while shortening the visible label; the following KPI loop remains responsible for all recorded values.
5. **Backend / API behavior.** No view, query, metric calculation, API, permission, workflow or JavaScript change. The two Python edits are existing test expectations only. Shared Marketplace Admin sales content retains its original title and subtitle.
6. **Database / migration impact.** None. No schema, migrations, production records, environment files, deployment or restart changes. Tests used the separate PostgreSQL test database with `--keepdb --noinput`; browser previews used its exported isolated fixtures.
7. **Tests performed.** **44 Django tests passed** across `modules.reports.test_dashboard_marketplace` and `modules.reports.test_marketplace_admin_dashboard`; system check reported no issues. Log: `scratch/dashboard-sales-summary-review/django-final.log`. The first run identified the inherited old-title assertion, which was corrected before the complete passing run. **11/11 source/browser checks passed** at 1366px and 390px: Sales Summary remains h3, its subtitle is absent, three KPI cards remain, the page fits, and Chromium measures main heading **18px** versus subsection **15px**. Source comparison confirms the sales partial differs only in the requested heading/subtitle. Log: `browser-final.log`; verifier: `check.cjs` in the same scratch folder. The first browser check exposed the 18.4px shared-ID override described above; the final scoped selector resolved it. Visually inspected the [laptop heading](../scratch/dashboard-sales-summary-review/heading-1366.png).
8. **Remaining limitations / troubleshooting / safe exercise.** Browser checks use headless Chromium with actual application assets and isolated Django fixtures, not an authenticated live production session or a full accessibility audit. Refresh with Ctrl+F5 if the old label or heading size remains; confirm the operations stylesheet query is `v=20261024-sales-summary`. Safe practice: inspect Marketplace Overview and Sales Summary in development DevTools, confirm h2 then h3 and computed sizes of 18px and 15px, and verify all three recorded KPI values stay unchanged. Do not create sales records to test a wording change.

---

## Current: Attention Required inside the System Overview left column - October 24, 2026

1. **Cause / reason.** The user approved grouping the existing Attention Required section below the eight KPIs in the left column, with the existing recommendation companion on the right. The standalone include in `executive_dashboard.html` placed Attention below the entire two-column overview. Inspection confirmed the existing CSS already supports the requested placement; no new grid or stylesheet is necessary. This decision supersedes earlier full-width Attention placement notes below.

2. **Exact files changed.** Current paths, lines and anchors:

   | File / line | Change and reason |
   | --- | --- |
   | `backend/templates/dashboard/partials/executive_dashboard.html:12` | Next to the `system_overview_summary.html` include, remove the standalone Attention include so it is not duplicated. Remaining module includes stay in their original order. |
   | `backend/templates/dashboard/partials/system_overview_summary.html:123` | Immediately after the KPI grid's closing `</section>`, include `attention_required.html` inside `.dashboard-summary-left`, guarded by existing `global_dashboard`. The recommendation aside remains the next column. |
   | `backend/core/modules/reports/test_dashboard_executive.py:159` | Existing executive layout test expects Attention before the recommendation title in document order; line 166 also requires exactly one Attention title. |
   | `backend/core/modules/reports/test_dashboard_operations.py:114` | Existing operations layout test follows the same updated reading order. |
   | `backend/core/modules/marketplace/test_bundle_monitoring.py:200` | Existing saved-preview test expects Attention before the right-side aside; its no-mining, unchanged-record-count, preview and link assertions remain intact. |
   | `docs/dashboard-analytics-operations-update.md:3` | This implementation, data flow, verification and troubleshooting report. |
   | `docs/campushub-system-overview.md:65` - `Super Admin dashboard` | Explain Attention's position inside the left column and the narrow-screen order at line 72. |
   | `docs/web-ui-ux-guidelines.md:9` - `Latest explicit page choices` | Replace the previous full-width Attention placement instruction with the approved nested placement. |
   | `CAMPUSHUB_CONTEXT.md:3` | Record this latest explicit layout choice and point to this report. |

3. **Changes made.** Move the existing section, including its heading, subtitle, list, actions, empty/loading/error states and JSON, without copying or rewriting it. All eight KPI cards remain untouched. Saved recommendation previews, activity counts and View Recommendations stay in the right aside. Existing CSS supplies a 70/30 desktop grid from 1200px, `align-items: start`, and a 16px gap above Attention. Smaller widths stack the left column before the aside. No CSS, palette, typography, spacing tokens, chart sizing, sidebar or remaining dashboard section changed.

4. **How it works / functions and data flow.** Existing Django context enters `executive_dashboard.html`, which includes `system_overview_summary.html`. That partial renders the KPI grid, then the same Attention partial, then the recommendation aside. Its `global_dashboard` input decides whether the moved section renders in this shared summary; no new variable or function is introduced. The Attention partial receives the same `attention_required` object, creates the same IDs and actions, and keeps its heading outside the white content surface. The unchanged `renderAttention(attention)` function in `backend/static/components/js/admin_dashboard_filter.js:189` finds `dashboardAttentionItems` by ID, replaces its rows and toggles `dashboardAttentionEmpty`; moving the DOM parent does not change those inputs or outputs. Example of the actual layout:

   ```html
   <!-- Inside dashboard-summary-left, after the existing eight-card section: -->
   {% if global_dashboard %}{% include 'dashboard/partials/attention_required.html' %}{% endif %}
   <!-- The existing recommendation aside follows the left column. -->
   ```

   This approach reuses the existing component and source order instead of using CSS visual ordering. Keyboard navigation therefore follows KPIs -> Attention actions -> View Recommendations at every width. Intrinsic columns can have different heights; no filler height or stretching was added.

5. **Backend / API behavior.** No runtime Python, JavaScript, API, database query, route, permission, analytics or recommendation workflow changes. The three Python edits affect test expectations only. The existing saved-preview test still patches the mining function to reject dashboard GET mining and verifies unchanged recommendation/product/activity counts. Existing chart and other module markup, KPI text/data, and the entire recommendation aside matched the pre-move browser baseline.

6. **Database / migration impact.** None. No production data, schema, migrations, environment files, deployment or server processes changed. Django regression tests ran against the separate existing PostgreSQL test database with `--keepdb --noinput`. Browser previews use exported isolated ORM test fixtures and locally intercepted assets, not fabricated production records.

7. **Tests performed.** **99 Django tests passed**, with no system-check issues, across reports' executive, operations, period, empty-state and KPI-card tests plus marketplace bundle-monitoring tests. Log: `scratch/dashboard-attention-column-review/django-final.log`. The initial run found one additional saved-preview test asserting the superseded layout order; only that expectation was corrected before the complete final run. **3446/3446 Chromium browser/source checks passed across 20 renders** at **1920x1080 desktop, 1366x768 laptop, 1024x768 tablet and 390x844 mobile**. Cases cover populated attention, empty attention, actual saved recommendation previews and missing-panel mode. Checks confirm exactly one Attention region inside the left column, placement directly after the eight KPIs, existing 16px spacing, 70/30 desktop proportions, natural narrow stacking, intrinsic heights, outside-card headings, no page overflow, keyboard Tab order, and in-place refresh updates. Compared unchanged KPI data, canvas heights, recommendation markup and all remaining module sections against a pre-move baseline at each width. **2217 protected Python/JavaScript/CSS source hashes remain unchanged**, excluding the three intentionally updated test files. Browser log, `measurements.json`, source baselines, hash manifest and `browser.cjs` live in the same scratch folder. Representative screenshots were visually inspected: [desktop with saved previews](../scratch/dashboard-attention-column-review/saved-1920.png), [laptop](../scratch/dashboard-attention-column-review/multiple-1366.png), [tablet](../scratch/dashboard-attention-column-review/saved-1024.png), [mobile](../scratch/dashboard-attention-column-review/multiple-390.png).

8. **Remaining limitations / troubleshooting / safe exercise.** Browser verification uses actual application templates, styles and scripts with isolated test fixtures in headless Chromium rather than a live authenticated production session. Other browser engines are not certified. On narrow screens all eight KPI cards appear before Attention, so scrolling to it is expected. Natural unused space under a shorter desktop column is retained instead of forcing equal heights. If the old placement remains visible, refresh the page and confirm the running checkout includes both edited templates; there is no new CSS asset to clear. In DevTools, verify that `.dashboard-summary-left > .dashboard-attention` exists once and the recommendation aside is its parent's next column. Safe learning exercise: resize a development dashboard between 1366px and 390px, then Tab from the last linked KPI through the Attention action to View Recommendations. Confirm the records and counts remain unchanged; no orders, bookings or recommendations need to be created.

---

## Current: content-driven Super Admin operational cards - October 24, 2026

This is the approved presentation-only sizing fix. It preserves the restored dashboard design documented below, including eight KPIs, saved recommendations, existing chart alignment, outside-card major headings, section order and responsive breakpoints.

### 1. Cause / reason

Confirmed in the existing cascade: `admin_marketplace_overview.css:341` explicitly stretches marketplace grid items. `low_stock_card.html` and `upcoming_reservations.html` also applied Bootstrap's `h-100`, making those cards fill the surrounding row. Facilities and Services operational grids inherited CSS Grid's default stretch behavior. Short attention lists and empty states therefore expanded to match unrelated longer siblings.

Recent Orders already had `height: auto` and an effective `min-height: 0`; its excess height came from stretching, not an active fixed height. The older 380px upcoming-reservation minimum was already overridden for the executive dashboard. KPI minimum rows and 240px chart areas serve meaningful alignment and remain intact.

Spacing also had confirmed conflicts: marketplace cards used 18px padding versus 16px in the other module cards; the more specific marketplace table rule overrode the earlier 8px compact cell rule. Inventory Alerts uses a `div.dash-card-header`, so the old `header p` selector missed its subtitle and left a different margin. Chromium screenshots exposed the resulting table-header misalignment.

### 2. Exact files changed

Current paths, lines and searchable anchors:

| File / line | Anchor and change |
| --- | --- |
| `backend/static/components/css/admin_executive_refinement.css:8` | `--executive-card-padding` / `--executive-table-padding`: local 16px card and 8px cell spacing values. |
| `backend/static/components/css/admin_executive_refinement.css:81` | `Operational cards follow their own content`: top-align the three operational grids; allow their cards to use natural height; standardize their padding and 12px corners. Marketplace chart-card padding also becomes 16px; chart canvas heights stay unchanged. |
| `backend/static/components/css/admin_executive_refinement.css:93` | Operational table selector: all four existing table families receive 8px cell padding. |
| `backend/static/components/css/admin_executive_refinement.css:96` | `recent-orders-table-wrap`: remove its redundant top margin; retain the card header's existing bottom gap. |
| `backend/static/components/css/admin_executive_refinement.css:99` | `.dash-card-header p`: match the two marketplace subtitles' margins, secondary text and typography so their table headers align. |
| `backend/static/components/css/admin_executive_refinement.css:105` | Operational `.ch-dashboard-empty`: use 16px vertical message padding without nesting extra horizontal padding inside a padded card. |
| `backend/templates/dashboard/partials/low_stock_card.html:1` | Keep `h-100` only when `global_dashboard` is false. Inventory Alerts uses intrinsic height in the Super Admin dashboard. |
| `backend/templates/dashboard/partials/upcoming_reservations.html:1` | Keep `h-100` only when `executive_mode` is false. Shared domain-dashboard callers retain their original markup. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | Existing global-only stylesheet URL changes to `v=20261024-intrinsic` so a refresh requests the updated asset. |
| `docs/dashboard-analytics-operations-update.md:3` | This implementation, debugging and verification guide. |
| `CAMPUSHUB_CONTEXT.md:3` | Current decision and pointer to this report. |

QA-only files live in `scratch/dashboard-intrinsic-review/`: original source copies, `browser.cjs`, `protected-before.json`, exported test pages/payloads, measurements, screenshots and logs. The Playwright Core package is local to that scratch folder; application dependencies were not changed. These artifacts are not application routes or new dashboard features.

### 3. Changes made

Recent Orders, Inventory Alerts, Upcoming Reservations, Facility Attention, Recent Service Requests and Service Attention now follow their own content heights. Their parent grids keep the same columns and gaps and align items at the top. Shorter cards can end earlier than longer neighbors. Operational cards use 16px padding, 12px corners and 8px table cell padding. Both marketplace table headings now begin on the same horizontal line.

Attention Required remains compact with its existing 40px minimum rows and 36px actions. Its markup, spacing and data are unchanged. The system KPI geometry, chart canvas heights, chart-grid alignment, navy/gold/white palette, shared Inter font, heading placement, existing responsive rules and actual content remain intact. No cards, sections, charts, records, functionality or production scripts were added.

### 4. How it works / functions, inputs, outputs and data flow

Existing authorized Django dashboard request -> unchanged reporting helpers and database records -> existing template context -> the same executive partials -> existing JavaScript renderers. CSS takes the resulting DOM and controls its spacing and height; it does not change records or calculate analytics.

The only template inputs used differently are existing booleans: `global_dashboard` decides whether Inventory Alerts keeps `h-100`, and `executive_mode` does the same for Upcoming Reservations. Both default/shared modes keep their original full-height class. Their HTML output otherwise matches the pre-change templates exactly in isolated render checks.

No runtime function was added or edited. Existing `renderRecentOrders(orders)` in `admin_dashboard_filter.js:291` receives an order array, replaces table rows and toggles the existing empty state. Existing `renderLowStock(snapshot)` at line 238 receives the current inventory state/products, replaces its rows and toggles empty/error visibility. The CSS automatically resizes after either renderer updates the content. Neither renderer assigns a card height.

Annotated CSS example from the implementation:

```css
/* Same grid columns; a short list no longer fills its taller sibling's row. */
[data-global-dashboard] .dashboard-executive :is(.marketplace-operations-row, .facilities-operations-grid, .services-operations) {
    align-items: start;
}
```

The final existing refinement stylesheet owns these scoped overrides because it loads after component styles. This avoids changing shared role dashboards or rewriting their layout rules. Chart and KPI rows are deliberately excluded from the intrinsic-height grid selector.

### 5. Backend / API behavior

No view, query, API, payload, permission, route, business rule, filter, analytics calculation or JavaScript source changed. SHA-256 comparison verified all **360 protected Python/JavaScript files** match the task's pre-edit snapshot. Shared partial output is unchanged outside the executive/global mode.

### 6. Database / migration impact

None. No schema, migrations, live records, deployment, environment files or services changed. Existing regression tests used Django's separate PostgreSQL test database with `--keepdb --noinput`; their fixtures were exported only to `scratch/`. Browser requests were intercepted and served those isolated ORM-generated fixtures and local application assets; no production records were added to fill the dashboard.

### 7. Tests performed

- **90 Django tests passed**, with no system-check issues: `modules.reports.test_dashboard_executive`, `test_dashboard_operations`, `test_dashboard_periods`, `test_dashboard_empty_states`, `test_dashboard_kpi_cards`, `test_dashboard_low_stock` and `test_dashboard_services`. Log: `scratch/dashboard-intrinsic-review/django-regression.log`.
- **8/8 shared/executive partial checks passed**. Both shared partials render byte-identically to their original output in domain mode. In executive mode only the approved `h-100` class disappears. Log: `partial-checks.log` in the same QA folder.
- **1107/1107 Chromium browser/source checks passed across 23 renders**, including baseline comparisons at 1920, 1440, 1366 and 1280px and empty, one-record and multiple-record states. Additional widths: 1100, 1099, 991, 990, 800, 599 and 375px. Checked page overflow, table spacing, independent card heights, major headings, section order, original column widths, KPI geometry, unchanged chart heights, compact attention rows, script errors and protected hashes. Run `node scratch/dashboard-intrinsic-review/browser.cjs`; output: `browser.log` and `measurements.json`.
- Exercised the actual existing Refresh/Retry handlers in Chromium with intercepted fixture responses: loading, successful refresh, HTTP 503 errors, empty refresh and populated recovery. Existing error/empty regions remained usable. Confirmed keyboard focus and ArrowRight scrolling on the narrow Recent Orders table region.
- Visually inspected desktop and laptop screenshots for Marketplace, Facilities and Services; also inspected System Overview, Attention Required, error and refreshed-empty states. Representative captures: [desktop marketplace](../scratch/dashboard-intrinsic-review/marketplace-1920.png), [laptop marketplace](../scratch/dashboard-intrinsic-review/marketplace-1366.png), [laptop facilities](../scratch/dashboard-intrinsic-review/facilities-1366.png), [laptop services](../scratch/dashboard-intrinsic-review/services-1366.png), [attention](../scratch/dashboard-intrinsic-review/attention-1366.png), [error](../scratch/dashboard-intrinsic-review/error-1366.png), [refreshed empty](../scratch/dashboard-intrinsic-review/refreshed-empty-1366.png).
- Final source checks: scoped `git diff --check` and browser harness syntax check passed. The existing local server returned **HTTP 200** for the versioned refinement stylesheet with bytes identical to the workspace file. Log: `scratch/dashboard-intrinsic-review/final-checks.log`; the task-only application diff is `approved-changes.diff` in that folder.

Measured multiple-record fixture heights, rounded to whole CSS pixels:

| Card | 1920px before -> after | 1366px before -> after |
| --- | --- | --- |
| Recent Orders | 229 -> 213 | 229 -> 213 |
| Inventory Alerts | 229 -> 185 | 229 -> 185 |
| Upcoming Reservations | 277 -> 265 | 316 -> 304 |
| Facility Attention | 277 -> 229 | 316 -> 229 |
| Recent Service Requests | 250 -> 238 | 289 -> 277 |
| Service Attention | 250 -> 229 | 289 -> 229 |

Verification corrections: the first SQLite attempt could not execute an existing PostgreSQL-specific `DO` migration, so it was not a test pass. An initial PostgreSQL command used a nonexistent `test_dashboard_kpis` module; the corrected complete run above passed. Browser inspection revealed a stronger existing 14px corner rule and the inventory subtitle margin; the final scoped CSS fixes both. A keyboard-scroll assertion was updated to await the browser's asynchronous scrolling rather than sampling immediately after keypress. No production JavaScript was altered for these checks.

### 8. Remaining limitations, troubleshooting and safe practice

Screenshots use the actual application CSS, scripts and Django-rendered isolated test fixtures in headless Chromium, rather than an authenticated live production browser session. This verifies the requested desktop/laptop geometry and state transitions; it is not a complete cross-browser, accessibility or full-application certification. Existing horizontal table scrolling is retained when columns cannot fit. Long content can still produce a taller individual card, as intended. Space under the shorter side of an existing two-column row is expected; cards are not stretched to fill it. Chart rows and the original overview/recommendation layout remain unchanged.

If the old spacing appears, use Ctrl+F5 and inspect the refinement stylesheet link for `v=20261024-intrinsic`. In DevTools, check the operational grid's computed `align-items: start`, card `height: auto`, 16px padding and 8px cells. A new high-specificity override or a restored `h-100` class can reintroduce stretching. A blank data region must still be debugged through its existing empty/loading/error state, not populated with made-up records.

**Safe practice exercise:** at a development dashboard with unequal list lengths, temporarily switch `.facilities-operations-grid` from `align-items: start` to `stretch` in DevTools. Observe Facility Attention expand to the reservation card's height without changing any record or count. Restore `start` and confirm independent heights, matching top edges and unchanged chart dimensions. Re-run the browser harness for the saved fixture comparison; do not create live orders or bookings for this exercise.

---

## Latest decision: revert compact dashboard changes ? October 24, 2026

1. **Cause / reason.** The user cancelled the compact six-KPI dashboard update and requested a revert. The previous dashboard layout is restored; earlier product-management work and the earlier System Health removal are preserved.
2. **Exact files restored.** `backend/templates/dashboard/partials/executive_dashboard.html:2` restores the welcome/filter toolbar and previous section includes; `backend/templates/dashboard/pages/admin_dashboard.html:620` restores existing filter/chart scripts; `backend/templates/dashboard/partials/system_activity_preview.html` restores its caption. Backend restoration: `backend/core/modules/reports/dashboard_periods.py:145` (`build_dashboard_data`), `backend/core/modules/reports/views.py:685` and `:1289` (existing callers), and `backend/core/modules/reports/dashboard_executive.py:115` (latest activity selection). Related assertions restored in `backend/core/accounts/tests.py` and reports `test_dashboard_periods.py`, `test_dashboard_executive.py`, `test_dashboard_operations.py`.
3. **Changes removed.** Deleted only this task's new `backend/core/modules/reports/dashboard_compact.py`, `test_dashboard_compact.py`, `backend/templates/dashboard/partials/executive_summary.html`, `compact_chart.html`, `backend/static/components/js/admin_dashboard_compact.js`, and `backend/static/components/css/admin_dashboard_compact.css`. No broad Git reset was used.
4. **How it works / data flow.** Existing request filters enter `build_dashboard_data`; existing projections populate the executive template, whose section includes and original scripts render/update the dashboard. The extra `executive.compact` projection is removed. For example, `period=today` again feeds the existing sales/booking controls without a second compact rendering path.
5. **Backend / API behavior.** Restored existing dashboard function signatures, protected API calls and newest-first five-event selection. Routes, authorization and existing business workflows remain intact.
6. **Database / migrations.** None. No live records changed.
7. **Verification.** All **56 tests passed** across `modules.reports.test_dashboard_periods`, `test_dashboard_executive`, and `test_dashboard_operations`, including isolated Django renders and the inherited Marketplace/Facilities Admin template regressions. Log: `scratch/dashboard-revert-tests.log`. Django system check reported no issues.
8. **Limitations / safe exercise.** No browser screenshot certification is claimed. Refresh the dashboard with Ctrl+F5; verify the previous eight KPI bindings and detailed module sections are present, and the removed System Health strip stays absent. No production data needs to be created for this check. Isolated QA snapshots in `scratch/` are not application pages.

---

## Latest decision: remove dashboard System Health — October 24, 2026

The user explicitly requested removal of the System Health heading, Database/Chat/Backup states and Check status control. `backend/templates/dashboard/partials/executive_dashboard.html:2` now starts with the existing welcome/filter toolbar and no longer includes the health partial. This supersedes earlier instructions below to show a top health strip. The shared partial and protected health API stay available to their existing callers; `admin_system_status.js:3` already returns safely when its region is absent. No replacement status container was added. **65 final overlapping product/executive/KPI/operations/period tests passed** (`scratch/products-health-final.log`).

Reason: remove the requested dashboard display. Change/data flow: Django renders the same executive context and component sequence, omitting one include. Backend/API/RBAC and monitoring calculations remain intact; no model/migration/live-data change. Existing executive, operations, KPI and period tests now assert the new absent display while retaining their data/filter checks; combined results are in `scratch/products-health-final.log`. [About CampusHub](campushub-system-overview.md) now lists Welcome first. Browser pixels remain unverified. Safe practice: inspect rendered HTML for absence of `dashboardSystemStatus`, `systemStatusTitle`, and `systemStatusRetry`, and confirm the unchanged Welcome/System Overview content; do not disable real services to test removal.

---

## Current: Super Admin flat institutional refinement — October 24, 2026

1. **Cause / reason.** The user requested modern minimalist refinement using impeccable and frontend-design. Inspection confirmed that the existing executive template already renders health, reporting controls, eight system KPIs, saved recommendations, attention, marketplace/facilities/services/users analytics and activity. Preserve that structure. The brief ends at “Pri use modern inspirational dashboard premium”; no additional unwritten requirements are assumed.
2. **Exact files.** `backend/static/components/css/admin_executive_refinement.css:1` adds the scoped visual finish. `backend/templates/dashboard/pages/admin_dashboard.html:29` loads it only for `global_dashboard`, after existing component/empty styles and before shared typography. Existing `executive_dashboard.html`, reporting views/services/APIs/chart scripts, recommendation services, data bindings and section content were inspected and retained. This guide and `CAMPUSHUB_CONTEXT.md` record the decision. The concurrently completed Marketplace action improvements are documented separately in [Shared action feedback](admin-action-alerts.md).
3. **Changes.** Flat white surfaces with 12px corners and subtle existing neutral borders; restrained navy text and icons; Inter hierarchy with compact welcome typography; aligned welcome/filter toolbar with a quiet divider; table headings in functional secondary text on the existing pale background; consistent tabular numerals and visible focus. Linked KPI hover changes only the border. Existing 70/30 layout, charts, empty states, section titles outside cards, recommendation preview limit, operational tables and small-screen stacking remain. No new cards, placeholder metrics, charts, gradients, page animation or sidebar changes.
4. **How it works / data flow.** Existing authorized Django request → existing reporting-period helpers and actual PostgreSQL records → dashboard context → `admin_dashboard.html` and executive partials → existing Chart.js renderers. The new stylesheet applies only under `[data-global-dashboard] .dashboard-executive`. Its scoped CSS custom properties name existing ink/secondary/border/navy/gold values; they carry presentation, not calculations. For example a missing sales cohort still selects the original empty-state branch; the stylesheet cannot manufacture a revenue line. Shared typography loads afterward to preserve the global bundled Inter policy. The small-screen rule changes toolbar wrapping only.
5. **Backend / API behavior.** No Super Admin query, API, filter behavior, permission, route, status, workflow or saved recommendation generation changes. Actual analytics charts remain historical summaries, not forecasts. Explicit recommendation actions and research modes remain in their existing workspaces.
6. **Database / migrations.** None. No live records, migrations, deployment, environment or service restart. Render fixtures came from the existing isolated Django test.
7. **Verification.** The 135-test action/dashboard regression included executive behavior; 16 further report/KPI/empty-state tests passed. A separate executive fixture render test passed (`scratch/executive-flat-render.log`). `node scratch/verify_executive_flat.cjs` passed **27 rendered structure/style checks**: stylesheet order, eight KPIs, seven major headings, original chart hooks and analytics navigation, oversight-only recommendations, flat surfaces and small-screen rule. JavaScript syntax checks and Django system check passed. The CSS verification uses jsdom; native responsive layout/canvas rendering is not claimed. Initial verifier assertions incorrectly expected the local stylesheet after global typography and used guessed chart IDs; the verifier now checks the observed cascade and actual existing IDs. Application structure was not changed to satisfy those assumptions.
8. **Limits / troubleshooting / safe exercise.** Connected browser inventory is empty, so screenshots, browser interactions, visual contrast against every rendered state and responsive pixels need a device walkthrough. No full application certification. Ctrl+F5 requests `admin_executive_refinement.css?v=20261024-flat`; inspect that link if styling appears stale. Safe exercise: inspect the eight `data-dashboard-kpi` bindings and compare them with the rendered isolated fixture; then run the Node verifier. Change only a local CSS padding value for practice and restore it. Never insert fake production orders to fill charts. Existing data eligibility and schema limitations in earlier reports remain.

---

For a plain-language explanation of the system, read [About CampusHub](campushub-system-overview.md). This document keeps the implementation history, exact code locations, debugging and verification reports.

## Current: Super Admin UI hierarchy — October 24, 2026

This presentation-only update supersedes earlier header-position and spacing descriptions below. The saved recommendation previews from October 23 remain intact. Existing dashboard order, data and workflows are unchanged.

### 1. Cause / reason

Inspection confirmed that most major headings were already outside cards. However, System Overview's heading lived inside the left column of the 70/30 row, so it did not introduce the full KPI/recommendation group. System Overview and Attention Required lacked subtitles, and header margins/type treatments differed across sections. Sales Overview had no supporting subtitle.

The Marketplace sales wrapper was **already transparent** in `admin_marketplace_overview.css`; no backend or card rebuild was needed. This change preserves that existing flat layout instead of adding or removing data components.

### 2. Exact files changed

Paths below are relative to the repository root. Current lines and searchable anchors identify each change.

| File / line | Anchor / purpose |
| --- | --- |
| `backend/templates/dashboard/partials/system_overview_summary.html:2` | `executive-system-overview`: light semantic section with title/subtitle before the existing 70/30 row; eight original KPI cards and recommendation include retained. |
| `backend/templates/dashboard/partials/attention_required.html:1` | Super Admin-only `executive-section` / `executive-section-header` classes and subtitle. Existing attention records, actions and state hooks retained. |
| `backend/templates/dashboard/partials/executive_dashboard.html:17` | Marketplace major header adopts the shared hierarchy classes; existing Analytics URL retained. |
| `backend/templates/dashboard/partials/super_marketplace_sales.html:2` | `executive-kpi-heading`: Sales Overview heading/subtitle above individual KPI cards, within the existing transparent wrapper. |
| `backend/templates/dashboard/partials/super_facilities_overview.html:2` | Facilities outside header adopts shared heading/subtitle classes. |
| `backend/templates/dashboard/partials/super_services_overview.html:2` | Services outside header adopts shared heading/subtitle classes. |
| `backend/templates/dashboard/partials/super_users_overview.html:2` | Users outside header adopts shared heading/subtitle classes. |
| `backend/templates/dashboard/partials/system_activity_preview.html:3` | Recent System Activities outside header adopts shared heading/subtitle classes; action permissions retained. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Operations stylesheet cache version becomes `20261023-section-hierarchy` (asset identifier, not the report date). |
| `backend/static/components/css/admin_dashboard_operations.css:222` | `Page > major section > individual component`: scoped transparent section wrappers, consistent header type/spacing, responsive action wrapping and Sales KPI header. |
| `docs/dashboard-analytics-operations-update.md:3` | This implementation report, verification and practice exercise. |
| `CAMPUSHUB_CONTEXT.md:3` | Latest hierarchy decision and reference to this report. |

Verification artifacts, not application assets: `scratch/super-hierarchy-review/verify.cjs`, baseline template copies, isolated rendered fixtures and protected-source hash manifest in the same folder; logs `scratch/super-hierarchy-tests.log` and `scratch/super-hierarchy-dom.log`.

### 3. Changes made

All seven major areas now use one outside-header pattern: **System Overview, Attention Required, Marketplace Overview, Facilities Overview, Services Overview, Users Overview and Recent System Activities**. Each has a title and short subtitle; existing module Analytics and activity actions remain alongside the appropriate header. No duplicate major titles were added.

Section wrappers stay transparent, borderless and without shadows. Major sections use 28px separation on desktop, 24px on narrow screens, with 16px between each header and its content. Existing Inter typography and CampusHub palette are preserved: 18px/600 navy major headings and 13px secondary subtitles. The shared web typography token also resolves to the existing 18px section size.

Component titles remain inside their individual cards, including all requested sales, booking, services and user chart/list titles. The Sales Overview KPI-group heading stays outside its individual cards. Bundle Recommendations & Activity keeps its title inside the companion card, with actual saved previews, three activity counts and its existing navigation link. System Health remains one compact strip; neither receives a duplicate outside major header.

### 4. How it works — inputs, outputs and data flow

No production function or JavaScript handler changed. The existing Django dashboard view still supplies the same context. The same partials render the same values, chart JSON, forms, named-route links and `data-*` hooks. `executive_dashboard.html` keeps its existing include order. The System Overview partial now adds a plain semantic section around the existing two-column layout and places its header before that row.

The new `executive-section-header` class connects these seven headers to scoped CSS. The selector starts with `[data-global-dashboard] .dashboard-executive`, so these rules target the Super Admin dashboard. In the shared attention partial, the new styling and subtitle are conditional on `global_dashboard`; Marketplace Admin keeps its own presentation. Existing chart/list card selectors and responsive grids remain in use.

Annotated example:

```html
<!-- Outside header: introduces the whole major section. -->
<header class="dashboard-section-heading executive-section-header">
  <div><h2>System Overview</h2><p class="executive-section-subtitle">...</p></div>
</header>
<!-- Existing individual KPI cards and recommendation card follow. -->
```

At widths up to 599px, the header copy takes a full row and existing actions wrap beneath it. Labels may wrap rather than forcing horizontal page overflow. The existing 70/30 desktop KPI/companion layout and card-grid breakpoints are preserved. This is a hierarchy adjustment, not a new dashboard architecture.

### 5. Backend / API behavior

No models, views, queries, aggregation helpers, permissions, URLs, API payloads, statuses, filters, Apriori processing or JavaScript sources changed. Actual health checks, saved recommendation reads, selected-period data and action access remain as before. Verification compared **68 protected backend/JavaScript/recommendation-source hashes** and confirmed them unchanged. Template data expressions, URL tags and `data-*` bindings also match their pre-change copies.

### 6. Database / migration impact

None. No migrations, schema updates, production/demo records, environment settings, deployment changes or server restarts were made. Existing tests use the isolated Django test database; exported fixtures are test artifacts only.

### 7. Tests performed

- **116 existing Django tests passed** across reports' executive, KPI, empty-state and Marketplace dashboard tests, plus marketplace bundle monitoring/suggestion tests. Log: `scratch/super-hierarchy-tests.log`. Django system check reported no issues.
- **189/189 DOM/source/style checks passed** using `node scratch/super-hierarchy-review/verify.cjs`. Five isolated fixtures cover empty, populated and missing-recommendation-panel states. Checks verify all seven outside headers, subtitles, unique IDs, 14 component titles inside their cards, eight retained system KPIs, four existing Analytics routes, recommendation/health exceptions, flat surfaces, original data hooks and protected source hashes.
- The DOM verifier passed Node syntax checking. It accounts for jsdom returning unresolved CSS custom properties rather than pretending they are measured pixels.
- Updated CSS served locally with **HTTP 200** and SHA-256 identical to the workspace source at its new versioned URL.
- Scoped whitespace check found no trailing whitespace or missing final newline in all **13 touched files**, including documentation and the DOM verifier.
- Responsive CSS wrapping and existing grid breakpoints were inspected. Real browser screenshots and viewport measurements were **not** performed: computer-use inventory returned no available apps/browsers.

### 8. Remaining limitations, troubleshooting and safe practice

Visual pixel accuracy, real small-screen overflow and keyboard focus in a browser remain unverified; jsdom checks structure/styles but does not lay out a real viewport. There is no claim of a screenshot or complete visual accessibility audit. Existing horizontal table regions and chart interactions were preserved.

If the page looks unchanged, hard-refresh with **Ctrl+F5** and confirm the loaded operations CSS URL ends in `v=20261023-section-hierarchy`. Confirm the running checkout includes the changed templates. A missing-data state is still an honest reflection of the database, not evidence of a CSS fault.

**Safe practice exercise:** in a development checkout, temporarily change only the subtitle next to `systemOverviewTitle` in `system_overview_summary.html`. Reload and verify that the caption changes while KPI values, chart data and recommendation previews do not. Undo the text edit. For verification, run `node scratch/super-hierarchy-review/verify.cjs` against the exported fixtures; regenerate fixtures through the existing tests if you change live templates. This teaches the distinction between template copy/layout and the unchanged backend calculations.

Latest explicit Super Admin panel update (October 23, 2026): **Bundle Recommendations & Activity** now shows up to two real saved product-pair previews with names, photos/placeholders, seller and saved response/delivery state, followed by three separate activity counts and one View Recommendations link. This supersedes only the count-only recommendation layout described below; the rest of the eight-area dashboard remains unchanged. Exact files/current lines, data flow, tests, troubleshooting and safe practice: [saved recommendation preview report](suggested-product-bundles.md#current-super-admin-saved-product-pair-previews--october-23-2026).

## Current: eight-area Super Admin Dashboard with Users Overview ? October 23, 2026

This report supersedes the earlier recommendation preview-list layout below. The existing Marketplace Admin Dashboard remains separate. No extra major dashboard areas were added beyond the user's requested eight.

### 1. Cause / reason

Inspection confirmed that System Health, the eight System Overview KPIs, Attention, Marketplace, Facilities, Services and Recent System Activities already had real helpers, permissions and chart components. The missing major area was Users Overview. The old recommendation panel contained two nested preview/activity sections instead of four compact saved counters. A service-attention projection also relabelled all non-open services as Temporarily Unavailable, including maintenance records.

The update adds a read-only user projection over existing fields, simplifies the recommendation panel and corrects that status label. It retains the working revenue, stock, booking, service-request and audit workflows.

### 2. Exact files changed, current lines and anchors

Paths below are relative to the repository root.

| File | Current line / nearby anchor | Purpose |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_executive.py` | 19 `users_overview`; 47 `service_overview`; 129 executive result | Four bounded user aggregate queries, actual service availability labels/links, user data in existing executive payload |
| `backend/core/modules/marketplace/services/bundle_suggestions.py` | 62?68, Super Admin saved-counter block | Current saved suggestion count plus existing sent/awaiting/created summary; errors produce unknown values |
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html` | 3 optional title | Reuse existing compact four-count component for Super Admin; default Marketplace Admin title is unchanged and headings are escaped |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 123 shared summary include | Replaces nested suggestion/activity previews with one count card and existing View Recommendations link |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 17 Marketplace subtitle; 29 Users include | Exact requested Marketplace subtitle; Users placed after Services and before Activities |
| `backend/templates/dashboard/partials/super_users_overview.html` | 1, new section | External heading and existing Analytics link; new/verified counters; daily registration line; type donut, tables, empty/error states |
| `backend/templates/dashboard/partials/super_marketplace_sales.html` | 7 metric heading | Marketplace Sales UI label; underlying existing sales field/calculation unchanged |
| `backend/templates/dashboard/partials/super_facilities_overview.html` | Facility Attention empty description | Removes an unsupported Restricted-state implication; retains actual maintenance/unavailable sources |
| `backend/static/components/js/admin_dashboard_executive.js` | 12 Users root; 14 failure; 21 rendering | Renders existing response data on initial load and date-filter events, chart lifecycle, accessible tables and unavailable/error handling |
| `backend/static/components/js/admin_dashboard_filter.js` | 355 sales canvas label | Refreshed accessible label correctly describes the existing single revenue series |
| `backend/static/components/css/admin_dashboard_operations.css` | 179 oversight/Users styles | One recommendation surface, individual user cards, 60/40 charts and responsive stacking; scoped to Super Admin executive UI |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 23 / 27 / 619 / 622 asset links | Cache version `20261023-users-overview` for relevant existing assets |
| `backend/core/modules/reports/test_dashboard_executive.py` | 199 / 235 / 259 new tests | Real registration dates/types/verification, four-query bound, section order, safe fields and actual service status |
| `backend/core/modules/reports/test_dashboard_periods.py` | 359 query budget | Existing query count remains independent of order volume; allows the four explicit Users aggregates (39 total maximum) |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | Marketplace layout assertions | New exact subtitle; Marketplace chart-table assertion scoped to Marketplace instead of unrelated Users data tables |
| `backend/core/modules/reports/test_dashboard_kpi_cards.py` | Recommendation component assertion | Existing eight KPI/destination/no-mining checks retained; expects compact summary rather than removed preview |
| `backend/core/modules/reports/test_dashboard_empty_states.py` | Dashboard empty checks | Empty recommendations are now honest zero counters rather than separate preview sections |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | Saved-count/read-only/navigation/error tests | Exact saved global counts, one existing destination, no mutations/mining/actions, unknown counts on both admin-role error paths |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | Super Admin summary assertions | Removes obsolete per-product preview expectations; retains actual saved/live boundaries and algorithm tests |
| `backend/core/accounts/tests.py` | Super Admin dashboard subtitle assertion | Exact requested copy, preserving dedicated-role template checks |
| `docs/dashboard-analytics-operations-update.md` | This current report | Data flow, evidence, source limitations and safe learning exercise |
| `CAMPUSHUB_CONTEXT.md` | Latest Super Admin note | Stores this final eight-area decision |

### 3. Changes made and sections retained

Final order is System Health; System Overview + Bundle Recommendations & Activity; Attention Required; Marketplace Overview; Facilities Overview; Services Overview; Users Overview; Recent System Activities. The Welcome/date toolbar remains a control row, not another dashboard area.

System Health retains the existing compact real-check strip. The backend verifies database connection, chat health endpoint and completed-backup metadata. The existing status renderer requires a checked timestamp before presenting a verified status, and displays Unknown when unverified. No hard-coded healthy/connected values were added.

System Overview retains its existing eight real KPIs and 70/30 desktop grid. The recommendation card now shows only Suggested Product Bundles, Sent to Sellers, Awaiting Seller Response and Bundles Created, plus the existing View Recommendations link. It has one white surface and no per-pair action, technical rule metric or approval control. Super Admin's existing read-only action restrictions remain server-enforced.

Marketplace retains its three sales/AOV KPIs, single-series revenue line, existing top-five product bars, latest-five five-column orders and three-column inventory alerts. Facilities retains physical booking KPIs/trend, top-five ranking, upcoming-five reservations and actual maintenance/unavailable attention. Services retains its four counters, actual request trend/service names, recent-five requests and existing attention records. Major headings remain outside these content cards; their existing light section wrappers are preserved.

Users Overview adds two supported metrics: New Users in Selected Period and Verified Users. It does not duplicate Total Users and does not invent an Active Users definition. It adds a daily registration line and current recorded mobile-account-type donut using existing Chart.js. Exact chart values are available in tables, including library-failure paths. Unsupported/unrecorded types are not assigned to Student/Guest or inferred from admin roles.

Recent System Activities remains the existing latest-five selected-period feed with original protected eye/details action, year-aware timestamp format and secret sanitization. It is still last, after Users Overview.

### 4. Existing models/helpers and data flow

No model, database field, status, route, role, permission, approval workflow or Apriori algorithm was created or changed.

`users_overview(period)` takes the existing validated AnalyticsPeriod. It counts actual `accounts.User.date_joined` and `api.CampusHubUser.created_at` records inside the selected date range, grouped by local date with TruncDate. Missing dates are zero-filled for the chart, and an entirely empty period shows the requested honest empty state. Registration counts refer to account records across those two existing sources, following the detailed Users Analytics registration convention; no undocumented person-identity deduplication is invented.

It uses four queries regardless of the number of days or account records: one grouped daily registration query per source; one current mobile user_type aggregate including verified-email counts; and one verified-email count for web accounts. `email_verified` exists on both models, so Verified Users is a current verified-email snapshot. It is not an activity metric. Types come directly from CampusHubUser.USER_TYPE_CHOICES (Student, Faculty, Guest). Their donut denominator is current mobile accounts with a supported recorded type. Blank/unknown values are excluded from slices and reported as an unavailable-type count. The web User model has no user-type field, so admin roles are not converted into invented types.

A compact projection was necessary because the existing detailed Users Analytics builder extends its monthly trend beyond short reporting windows and uses role/default-type assumptions. That detailed page is unchanged; this dashboard uses exact selected dates and recorded type values instead of importing those assumptions. The existing System Overview Total Users queryset also remains unchanged; it currently counts web User records. No new Total Users metric or identity-reconciliation policy is introduced here.

`executive_overview` places the new projection in `executive.users` alongside the existing physical booking/service summaries. Both initial Django HTML and the existing protected dashboard API receive that dictionary. The existing global-date controller emits `campushub:dashboard-data`; `renderUsers` updates counters, date rows and type rows and redraws the two charts. It destroys prior chart instances before redrawing, disables animation and uses the shared Inter/navy/gold/neutral visual system. Failure hides stale user charts and displays unavailable values plus an error; a chart-library failure leaves real tables visible.

`dashboard_bundle_suggestions` still reads saved BundleRecommendation data. The existing `recommendations_for` scopes records; a current-record count supplies Suggested Product Bundles. Existing `activity_summary` supplies sent, awaiting and actual linked-created bundle product counts. Those saved activity counters are independent of the reporting date filter, as before. No mining or saving occurs on dashboard GET. Existing preview fields remain in the internal helper for compatibility, but are no longer shown in the dashboard panel.

Service attention now uses `Facility.STATUS_CHOICES` for each record's actual availability label and passes that actual status to the existing catalog URL. Maintenance no longer appears as Temporarily Unavailable. This is a display/link correction over existing supported states, not a new workflow.

Data flow: PostgreSQL ? existing User / CampusHubUser / Product / MarketplaceOrder / Booking / Facility / BundleRecommendation / AccountActivity models ? existing permissions and summaries plus the compact Users projection ? existing dashboard context/API ? scoped templates/styles and existing Chart.js ? high-level dashboard. Full exploration remains under existing Reports ? Analytics tabs and the existing saved recommendation workspace.

### 5. Unsupported metrics intentionally omitted; backend/API behavior

Active Users is intentionally omitted: enabled-account flags alone do not establish recent activity, and no new activity window/definition was invented. No Restricted facility status or web-account user type was invented. Missing types are not treated as Students. Synthetic Apriori data is not read by any new user query or operational KPI.

Existing URLs, scope helpers, Cash on Pickup eligibility, AOV calculation, booking/service separation, audit permissions, final Super Admin protection, and recommendation oversight restrictions remain intact. The existing API only gains an aggregated `executive.users` dictionary; no new endpoint or polling system exists. Marketplace Admin retains its own title and unchanged summary behavior.

### 6. Database / migration impact

None. All new projections are SELECT aggregates over existing fields. No migrations, live writes, sample production records, inventory adjustments, secret/environment changes, deployment, mobile build or server restart occurred. Populated/empty fixtures were generated only in Django's isolated test database. No credentials, hashes, verification codes or identifying user records are returned in the Users summary.

### 7. Verification performed

- **381 broad Django tests passed**: all `modules/reports/test_*.py`, saved recommendation monitoring/suggestions, order administration and account activity/Monitoring tests. Log: `scratch/super-users-overview-regression.log` (Ran 381 / OK).
- **14 final targeted tests passed** after the small error-state/copy refinements: full executive dashboard tests and the shared summary error test for both Marketplace and Super Admin. Log: `scratch/super-users-overview-final-targeted.log`. These overlap the broad run; they are not 14 additional unique test cases.
- **38/38 DOM/chart configuration checks passed**: eight-area order, eight top KPIs, four saved summary items/one action, actual registration/type values, no Active/duplicate Total Users, date-filter update, chart destruction, zero-data states, failed refresh/unavailable values, recovery and Chart.js-missing table fallback. Run `node scratch/super-users-overview-review/verify.cjs`. Actual isolated-test HTML/JSON is used; Chart is stubbed.
- Django `manage.py check`: no issues. Both changed JS files pass `node --check`. Scoped whitespace checks clean.
- Updated operations CSS, executive JS, filter JS and the existing shared recommendation CSS all return HTTP 200 from the already-running localhost server; their raw-byte SHA256 values match workspace files. No service was restarted for this check.
- CUA reports no available apps/browsers. Actual screenshot, responsive-pixel, canvas appearance and native keyboard/pointer checks were unavailable and are not claimed.

### 8. Remaining limitations, troubleshooting and safe practice

User Registration Trend is daily within the existing selected reporting range; detailed Users Analytics keeps its existing longer monthly exploration. Types are a current mobile account snapshot, and verified-email counts are a current two-source account snapshot. These bases are stated in the UI. Separate web/mobile accounts are counted as recorded accounts, not inferred unique people. Existing detailed Users Analytics and System Overview source conventions remain as described above; this update does not silently rewrite their identity/type definitions.

Existing refund/demo-record provenance limitations and the separately documented legacy detailed Analytics copy/permission/source-string test failures are unchanged. No fake data is used to mask a missing source. Browser visual verification remains pending.

If stale styling appears, Ctrl+F5 loads the `20261023-users-overview` assets. If user data fails, the dashboard's existing Refresh control retries the same protected endpoint; charts do not fall back to made-up counts. If no recorded types exist, the correct distribution empty state appears, even when registrations exist.

Safe learning exercise:

```powershell
cd backend/core
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_executive.ExecutiveDashboardTests.test_users_summary_uses_registration_dates_and_recorded_types_not_roles --keepdb --noinput
```

Read the test's date fixtures and `assertEqual(len(queries), 4)`. Change only one isolated fixture's created_at date across the selected-period boundary, adjust the expected chart bucket accordingly, rerun, then restore it. This demonstrates why registrations use actual timestamps rather than role/activity flags. Do not create practice accounts through the live admin site.

---


## Current: final Super Admin summary dashboard — October 23, 2026

This report implements the user's final dashboard brief. It supersedes older instructions to remove System Health or place Attention Required inside the left KPI column. The Marketplace Admin summary is documented separately in [Suggested Product Bundles](suggested-product-bundles.md); these are distinct role surfaces.

### 1. Cause / reason

Inspection found that the requested eight KPI order, Average Order Value, chart/operational cards, honest empty states, live accounting helpers and Analytics module tabs already existed. The actual gaps were the missing top health strip, Attention inside the left column, a hidden order-count dataset still retained by the executive revenue chart, missing recent-order links and missing Client in upcoming reservations. No dashboard rebuild or new analytics calculator was needed.

### 2. Exact files changed: current lines and anchors

| File | Line / nearby anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 2 `system_status.html`; 14 `attention_required.html` | Restore one compact health include before Welcome; render Attention after the full top grid; standardize Marketplace View Analytics wording |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 120 end of KPI grid | Remove nested Attention include; existing eight cards and recommendation aside remain |
| `backend/templates/dashboard/partials/attention_required.html` | 16 `No Items Require Attention` | Match the final inventory-alert empty-state wording |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html` | 5 `bundle-preview-count` | Show the actual eligible preview length, explicitly labeled Available in this preview |
| `backend/templates/dashboard/partials/super_facilities_overview.html` | 4 analytics action; 37 Facility Attention | Consistent analytics action; facility attention displays availability issues, with pending bookings left in the existing summary/top queue |
| `backend/templates/dashboard/partials/super_services_overview.html` | 6 analytics action | One View Analytics action rather than duplicate section-header links |
| `backend/templates/dashboard/partials/super_marketplace_sales.html` | 26 legend; 32 accessible description | Revenue-only terminology and accessible chart description |
| `backend/templates/dashboard/partials/recent_orders.html` | 8 order reference | Clickable order number, no new Actions column |
| `backend/templates/dashboard/partials/upcoming_reservations.html` | 9 table headings | Booking No., Facility, Client, Date / Time, Status |
| `backend/core/modules/reports/dashboard_marketplace.py` | 19 `url` | Add existing Orders deep-link URL to the read-only projection |
| `backend/core/modules/reports/dashboard_bookings.py` | 18 shared formatter import; 29 `select_related`; 52 `requester` | Reuse `_booking_display_fields()` and join the user for an actual client name without an extra query per row |
| `backend/static/components/js/admin_sales_overview.js` | 57 `describe`; 122 dataset; 132 conditional spread; 185 update | Exactly one executive revenue dataset; preserve non-executive chart behavior; revenue-only tooltip/text/keyboard summary |
| `backend/static/components/js/admin_booking_overview.js` | 19 `displayedSeries`; 21 `describe` | One facility-booking series and matching text summary; detailed status series remain in other modes |
| `backend/static/components/js/admin_services_overview.js` | 42 dataset label | Explicit Number of Service Requests label on the existing single trend series |
| `backend/static/components/js/admin_dashboard_filter.js` | 324 recent order reference | Render the existing local Orders URL with tab token, same-origin/path validation and text nodes |
| `backend/static/components/js/admin_upcoming_reservations.js` | 34 table cells | Keep refreshed five-column reservations aligned with server HTML |
| `backend/static/components/js/admin_dashboard_executive.js` | 21 `attentionKeys` | Facility Attention uses maintenance/unavailable, not pending requests |
| `backend/static/components/css/admin_dashboard_operations.css` | end: `bundle-preview-count`, top health and mobile rules; `min-width: 1800px` | Preserve 70/30 at large widths, 44px compact desktop health, mobile wrapping and restrained preview-count text |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 27, 616–622 versioned assets | Changed CSS/JS use `20261023-final` to avoid stale assets |

Relevant existing tests were updated in `test_dashboard_operations.py`, `test_dashboard_executive.py`, `test_dashboard_periods.py`, `test_dashboard_kpi_cards.py`, `test_dashboard_low_stock.py`, `test_sales_overview.py`, `test_upcoming_reservations.py`, `test_dashboard_marketplace.py` and `modules/marketplace/test_bundle_monitoring.py`. Nearby anchors are the existing layout/health assertions, mixed-year dates, upcoming client test and newest-order snapshot test. This guide, the status guide, global UI guide and project context record the final decisions.

### 3. Final layout and retained components

1. **System Health:** one existing horizontal component above Welcome, with real Database/Chat/Backup checks, readable outcomes and retry/Refresh. No bottom health section or invented Operational state.
2. **Welcome + dates + Refresh:** existing name, requested subtitle and central period controls.
3. **System Overview + Bundle Recommendations & Activity:** existing eight KPI cards in requested order; existing 70/30 desktop grid and saved live recommendation preview/activity. Four-by-two cards on desktop, smaller grids/stacking at existing breakpoints.
4. **Attention Required:** one full-width existing queue after the combined top region.
5. **Marketplace:** three sales KPIs, revenue-only line, top-five product bars, five recent orders and inventory alerts.
6. **Facilities:** existing period-specific bookings/approved/pending summary, one booking-count line, top-five facility bars, five upcoming reservations and availability attention.
7. **Services:** existing four KPIs, one request-count line, actual service-name bars, five requests and supported actionable states.
8. **Recent System Activities:** keep the recently polished five-row preview, dates, details, outcome labels and safe API unchanged.

Marketplace, Facilities and Services remain conceptual section wrappers with individual cards. Existing Inter, wordmark-only SugarPie, modest navy/gold styling, focus states, wrapped text and standard empty-state component are reused. Desktop health is compact; below 700px its labels wrap without widening the page. No decorative animation or chart was added.

### 4. Functions, inputs/outputs and data flow

The existing protected dashboard query/period helpers still feed the same HTML and `admin_dashboard_api` response. `valid_sales_queryset`, existing sales-summary/AOV calculation, booking/service resource predicates, payment rules, inventory helper, `executive_overview`, `dashboard_bundle_suggestions` and health helpers remain the data sources. Chart.js is the existing rendering library.

The executive sales renderer now constructs `[revenueDataset]`, while other dashboard modes retain their existing sales/order datasets. `updateChart` only updates an order dataset where that mode actually has one. Both the keyboard description and tooltip describe the revenue unit. Booking and Service trends retain their already-correct single series, now with explicit labels. Empty series stay hidden; valid zero-value paid orders remain real records rather than fabricated sales.

`recent_marketplace_orders(orders, limit)` still returns a bounded list from its authorized order queryset. Its new `url` is the existing `admin_orders_page` plus `?order=<id>`. That parameter is already used by `admin_orders.js` to open an authorized rendered row. The dashboard renderer validates the destination, preserves tab authentication and renders the order code as a link. No new details endpoint is introduced.

`upcoming_reservations(today, now)` keeps the same physical-facility, future-approved and maximum-five predicates. The new `requester` comes from `_booking_display_fields(booking)`, which already resolves recorded Reserved by information or the actual linked user. `select_related('user')` keeps the entire projection at one query in its regression test.

```python
# Read-only projection; actual recorded requester, no sample identity.
'requester': _booking_display_fields(booking)[1] or 'Not recorded'
# Existing Orders workspace; authorization stays in that destination view.
'url': reverse('admin_orders_page') + f'?order={order.pk}'
```

Restoring the health DOM activates the existing independent health script again. It performs the existing checks on load and Refresh/Check status. An absent or unverifiable timestamp yields Unknown; no successful status is fabricated. Backup health remains the existing metadata-based assessment, not a restore certification.

### 5. KPI, recommendation and Analytics boundary decisions

- No new KPI formula. Existing System Overview order already matches the final brief. Marketplace AOV is already reliable and retained. Pending Bookings remains the existing accurate facilities fallback; no new collected-revenue estimate is invented.
- Super Admin recommendations remain oversight-only, with the existing named detailed route and no permanent Super Admin sidebar entry. Technical Apriori metrics and operational send/create/approval actions remain absent from this panel.
- The small available count is explicitly **Available in this preview**, bounded to the actual one/two returned eligible rows. It is not presented as an unverified marketplace-wide total.
- Category sales, additional order trends, utilization/occupancy/revenue details, FBT/cross-sell detail and status breakdowns remain under the existing permission-checked Analytics module tabs. No routes/views/tabs were duplicated or removed.
- System activities and standard empty states retain their existing source and safe details behavior. No synthetic research rows are added to live orders, payments, KPIs, inventory or revenue.

### 6. Backend / API / database impact

API changes are additive read-only presentation fields: order `url` and reservation `requester`. Query eligibility, calculations, logging, payments, booking workflows, Apriori algorithm and role grants do not change. No models or migrations, environment/deployment/Flutter changes, production records, server restarts, notification sends or remote operations were performed.

The later Marketplace Admin request adds a mobile-seller fallback to the existing academic-scope helper; see the separate bundle guide for that explicit role-scoping change and its tests.

### 7. Verification results and debugging

- **367 focused Django tests passed** across dashboard/report test modules, Activity API/Monitoring, bundle monitoring/suggestions and Orders administration. Log: `scratch/dashboard-final-focused-tests.log`. Django system check: no issues.
- **13/13 audit/health DOM scenarios passed:** one top strip, order, live returned check timestamps, independent health during dashboard errors, retries, denied/safe detail display and cleanup. Harness: `scratch/dashboard-final-review/verify_operations.cjs`.
- **26/26 summary chart/layout DOM checks passed:** exact single revenue/facility/service trend datasets, vertical product/service bars, five-product limit, refresh, empty canvases hidden, unified Analytics actions, Attention outside the left column and no footer status. Harness: `scratch/dashboard-final-review/verify_summary_charts.cjs`. Chart.js is stubbed in this harness, so this verifies configuration and interaction wiring, not canvas pixels.
- All six changed production JavaScript files passed `node --check`.
- Both updated stylesheets and all six changed JavaScript assets returned HTTP 200 locally and matched the workspace (raw-byte hashes for JavaScript). An initial PowerShell decoded-string comparison misread existing UTF-8 punctuation; raw-byte comparison confirmed no served-file mismatch.
- Initial full discovery ran 384 tests and found 15 failures: one exact-dictionary assertion needed the new requester field, eleven dashboard presentation assertions still referenced old panels/copy/filters, and three separate legacy Analytics expectations failed. Updated the relevant dashboard assertions and added actual-client/no-extra-query and actual-order-link checks. The focused final run is green.
- The separate untouched `modules.reports.tests` module was rerun: **18 tests, 3 failures**. These concern existing detailed Analytics copy, Marketplace Admin Monitoring access after explicitly granting permission, and a source-string assertion expecting literal peso characters in `admin_marketplace_analytics.js`. These files/production behaviors were not changed to force a pass. Log: `scratch/dashboard-legacy-analytics-tests.log`. No full-suite pass is claimed.
- Browser inventory and an attempted local in-app browser were unavailable. Responsive CSS and DOM were reviewed; after-state screenshots, native focus behavior and actual chart pixels remain unverified.

Safe practice: open the local dashboard and press Ctrl+F5. Check the health strip above Welcome, the recommendation aside beside KPIs, then the full-width Attention queue. Change the reporting period and one chart grouping, verify cards/data change together, select an existing order number, and open Analytics for each module. Check a period with no genuine records and confirm the matching empty states instead of a blank chart. This creates no demo records or operational actions.

Troubleshooting: confirm changed assets use `v=20261023-final`. A status starting Unknown is intentional until the real request finishes. No booking-revenue card is intentional because the existing accurate fallback is Pending Bookings. A recommendation preview count is limited to the preview, not the entire saved workspace. Existing Overview totals and per-period metrics have deliberately different scopes explained by their supporting text.

### 8. Remaining limitations

The three legacy Analytics test failures remain outside this UI update, and browser visual acceptance is still outstanding. Existing single-product checkout history may be insufficient for reliable bundle suggestions; honest empty results remain. The Super Admin preview count is bounded, while the separate Marketplace Admin summary counts its existing qualified live result. No deployment or broad font/palette rewrite was performed.

## Remove the stock shortcut below Recent Orders — 2026-10-20

1. **Reason:** The user requested removal of the redundant `Low Stock Products →` link below Recent Orders.
2. **Files:** `backend/templates/dashboard/partials/executive_dashboard.html:23` (`executive-orders`) removes that anchor; `backend/static/components/css/admin_dashboard_executive.css` removes the unused `executive-stock-shortcut` rule. `scratch/dashboard-executive/verify_live_layout.py` adds a rendered-output absence assertion. This guide records the change.
3. **Changes:** Removed only the shortcut and its unused CSS. The actual Low Stock Products panel remains directly below Top Best-Selling Products.
4. **How it works:** The existing Recent Orders include still renders its table and View All link; its surrounding block no longer renders the separate stock anchor. Existing stock IDs and refresh hooks remain intact.
5. **Backend/API:** No view, endpoint, query, permission or data behavior changes.
6. **Database/migrations:** None.
7. **Checks:** Database-free production-template rendering passed: shortcut absent, stock/top-products/recent-orders placement retained, unique IDs and permission visibility preserved. Local versioned CSS returned HTTP 200 with exact current bytes. Scoped whitespace check passed. No browser test or database-backed suite was needed or run for this small link removal.
8. **Limits/practice:** The signed-in tab was not directly inspected. Refresh Dashboard and confirm Recent Orders has no stock shortcut, then confirm the real stock panel still appears under top sellers. No account edits, record changes or server restart needed.

## Header status dots, stock placement and stacked attention — 2026-10-20

1. **Reason:** The user requested header placement for live statuses, colored dots, Low Stock Products below Top Best-Selling Products, and attention items stacked in one container rather than side by side.
2. **Files:** `backend/templates/dashboard/pages/admin_dashboard.html:38` opts this Super Admin page into the shared header status row; line 25 sets CSS version `20261020-header-status-stock`. `backend/templates/partials/admin_header.html:3` adds the opt-in header marker; the `header-system-status` anchor includes the existing compact status partial between the title and action controls. `backend/templates/dashboard/partials/executive_dashboard.html` removes the status above Welcome and, at `executive-product-stack`, places the existing `lowStockSlot` directly under `topSellingProductsCard`, removing its old Operational Attention placement. `backend/static/components/css/admin_dashboard_executive.css:17` enforces a one-column attention list; the `dashboard-system-inline`, `data-inline-system-status`, `executive-product-stack` and `executive-operational-grid` rules style the requested positions. Existing executive test assertions and `scratch/dashboard-executive/verify_live_layout.py` / `verify_live_layout_browser.js` track these changes. This guide records the correction.
3. **Changes:** Statuses now appear in the white page header, alongside the title/actions on wide screens and in a wrapping second header row on smaller screens. The compact root remains transparent and borderless, with supporting descriptions/timestamps/icons/actions hidden. Small navy dots identify online/healthy states; gold identifies warning/degraded/unavailable/failed states, with text still stating the actual status. Unknown retains the existing neutral state styling. Attention Required is one vertical list with its existing subtle row divider. Low Stock Products shares the right product column with Top Best-Selling Products. The stock shortcut now targets `#lowStockSlot`; the remaining two operational cards use two columns.
4. **How it works:** The dashboard passes `system_status_inline=global_dashboard` to its existing shared header. Other header consumers default to no status include. This renders `dashboardSystemStatus` only once, so the existing live check/refresh script still updates the same IDs. Low-stock data stays inside `data-global-dashboard`, where the existing filter script finds and updates its data hooks; only the include's parent changes. Example: a dashboard refresh still updates stock rows in `lowStockSlot`, now below the top-products panel, and updates each status dot through the existing `data-system-state` value.
5. **Backend/API:** No endpoint, permission, status computation, inventory calculation or action destination changed except the local stock scroll shortcut. Existing authentication and filter behavior are preserved. No fake healthy status or seeded chart data.
6. **Database/migrations:** None; no records were added or changed.
7. **Checks:** Database-free production rendering verified a single status include in the opt-in header, none in an ordinary header, permission-controlled recommendations, unique IDs and top-products/stock/recent-order ordering. Live CSS returned HTTP 200 and exact workspace bytes. Isolated Chrome checks passed at 1536, 1024, 390 and 320px for header placement, transparent status appearance, actual navy/gold pseudo-element colors, one-column attention rows sharing a parent, stock directly below top sellers, preserved left-KPI attention alignment and no page overflow. The actual status script still passed mocked success and failed-refresh checks. Scoped whitespace check passed. Database-backed executive test assertions were updated but that database suite was not run.
8. **Limits/practice:** These checks exercise isolated rendering with mocked status responses, not the signed-in browser's actual health response or Bootstrap dropdown interactions. Existing header actions were retained. Refresh the real Dashboard; if stale, use browser Ctrl+Shift+R. Safe practice: resize the browser and verify the status labels remain in the header, attention items remain stacked, and the stock shortcut scrolls to the panel under top sellers. Use Refresh to verify actual values; no production record editing or service shutdown is needed. No app/server/worker restart was performed.

## Plain system status above the welcome greeting — 2026-10-20

1. **Reason:** The user requested status text above Welcome back, without a container or supporting copy.
2. **Files:** `backend/templates/dashboard/partials/executive_dashboard.html:2` renders the existing status partial with `compact=True`, before the welcome toolbar; its old sales-side status include is removed and Sales Overview/Top Products again share the existing grid. `backend/templates/dashboard/partials/system_status.html:1` adds the optional compact presentation with a visually hidden accessible heading; line 6 selects the inline root class. `backend/static/components/css/admin_dashboard_executive.css` at `#dashboardSystemStatus.dashboard-system-inline` supplies plain wrapping text and hides supporting content. `backend/static/components/js/admin_system_status.js:25` labels a verified online database as Connected in inline mode. `backend/templates/dashboard/pages/admin_dashboard.html:25` and the status script link use cache version `20261020-text-status`. The existing executive test's order assertion and both `scratch/dashboard-executive/verify_live_layout*` helpers were updated. This guide records the change.
3. **Changes:** The visible row contains only Database, Chat Service and Backup labels with their current state. No visible System Status heading, icons, dots, borders, filled background, descriptions, checked times, backup dates or action button. Text wraps on narrow screens. The full card presentation remains the default for other uses of the shared partial.
4. **How it works:** The include still renders all existing data hooks, but compact CSS hides the supporting elements so the existing script can safely update them. A visually hidden heading labels the section for assistive technology. `render(statuses)` keeps the same validated state mapping; only inline Database + online becomes Connected. Example input `{database: {status: 'online'}}` yields the visible pair `Database: Connected`; a failed check yields Unknown, not a guessed healthy value. Refresh and retry still call the existing check function.
5. **Backend/API:** The existing `system_status_only=1` request, session handling, timeout, abort behavior and status event remain unchanged. No monitoring result or timestamp is hardcoded. No new endpoint, database query or permission change.
6. **Database/migrations:** None. Mock responses exist only inside isolated browser QA; no production data is inserted.
7. **Checks:** Production-template rendering and unique hooks/order passed without database access. The versioned live CSS URL returned HTTP 200 and exact workspace bytes. Isolated Chrome checked text-only appearance, transparent/no-border root, hidden supporting copy, positioning above Welcome, left attention alignment and no page overflow at 1536, 1024, 390 and 320px. The actual status script was executed with local mocked responses: Connected/Unavailable/Healthy rendered correctly, then a failed Refresh check reset all three to Unknown. Scoped whitespace check passed. The database-backed executive test assertion was updated but its database suite was not run.
8. **Limits/practice:** QA verified actual rendering logic with mocked network responses, not live service health in an authenticated browser. Refresh the real dashboard; if stale, browser Ctrl+Shift+R loads the new CSS/JS versions. The system-check API determines the displayed states. Safe practice: use the existing Refresh button and confirm that the row changes from Unknown to verified statuses while descriptions and dates remain invisible. Do not shut down a real service to test this; use the isolated QA script for failure cases. No app/server restart or database edit is required.

## Attention Required under the left KPI column — 2026-10-20

1. **Cause / reason:** The screenshot confirmed unused space under the eight left KPI cards because the full-width attention strip followed the entire two-column row, waiting for the taller recommendations column to finish.
2. **Exact files:** `backend/templates/dashboard/partials/system_overview_summary.html:119` now includes the existing attention partial inside `dashboard-summary-left`; `backend/templates/dashboard/partials/executive_dashboard.html:12` retains only the summary include rather than a duplicate attention include. `backend/static/components/css/admin_dashboard_executive.css:11` removes the summary bottom margin, line 12 places attention 16px below the KPIs, and line 13 sets the next overview's top gap to 16px. `backend/templates/dashboard/pages/admin_dashboard.html:25` changes the CSS query version to `20261020-left-attention`. The existing section-order assertion in `backend/core/modules/reports/test_dashboard_executive.py` and the two `scratch/dashboard-executive/verify_live_layout*` helpers follow the new position. This guide records the correction.
3. **Changes:** Attention Required now fills the left column directly under its KPI grid. Recommendations remain in the right column. Marketplace Overview starts below the combined row with a smaller gap. Mobile retains one-column wrapping, with Attention Required before the recommendations.
4. **How it works:** Moving the existing include changes its grid parent; it is no longer a full-width sibling after the summary row. The same `dashboardAttentionItems` and `dashboardAttentionEmpty` IDs occur once, so the existing refresh script continues updating the same list. Example: two attention items now sit under the KPI cards while the right column can display all three recommendation panels independently.
5. **Backend/API:** No endpoint, alert calculation, action URL, permissions or filtering changes. The `global_dashboard` condition keeps this placement specific to the executive dashboard.
6. **Database/migrations:** None. No seeded data, production record writes or migrations.
7. **Checks:** Database-free production-template verification passed, including recommendation permission visibility, unique attention ID and revised ordering. The running local server returned HTTP 200 for the new CSS URL, with bytes matching the workspace file. Isolated Chrome checks passed at 1536, 1024, 390 and 320px; the attention panel's left edge and width match the KPI grid, its top sits exactly 16px below the grid, and no page overflow occurred. Existing recommendation/status layout checks also passed. Scoped whitespace check passed. The database-backed test assertion was updated but that database suite was not run.
8. **Limits/troubleshooting/practice:** Full authenticated interaction remains untested; the existing scripts and data flow were not modified. No app/server restart. Refresh Dashboard in the browser; use Ctrl+Shift+R if a tab still shows stale styling. Safe practice: resize the browser and confirm Attention Required stays under the KPIs, then narrow below 992px and confirm recommendation panels stack after it. Use the existing alert links to verify their destinations without modifying records.

## Apply the layout to the actual Django dashboard — 2026-10-20

1. **Cause / reason:** Confirmed: the latest interactive design changes lived only in `output/visualizations/campushub-admin-test-preview.html`. Django's `/admin/dashboard/` uses `dashboard/pages/admin_dashboard.html` and `executive_dashboard.html`, which still had the older arrangement. This was a preview-versus-application mismatch; a broken CSS URL was not confirmed. The current local server successfully serves the corrected versioned stylesheet.
2. **Exact files changed:** `backend/templates/dashboard/partials/system_overview_summary.html:123` adds the existing Frequently Bought Together partial and line 124 adds Cross-Selling Opportunities directly after Suggested Product Bundles. `backend/templates/dashboard/partials/executive_dashboard.html:18` groups existing sales/top-product content; line 22 places the existing System Status partial beside Marketplace Overview, after Attention Required. `backend/static/components/css/admin_dashboard_executive.css:13` starts the compact attention rules; line 21 starts the new content/status layout. `backend/templates/dashboard/pages/admin_dashboard.html:25` sets stylesheet version `20261020-live-dashboard-layout`. `backend/core/modules/reports/test_dashboard_executive.py:93` updates the existing section-order expectation and recommendation uniqueness/order assertions. `scratch/dashboard-executive/verify_live_layout.py:1` and `verify_live_layout_browser.js:1` provide database-free template/static/browser checks. This guide records the correction.
3. **Changes made:** Existing recommendation panels now stack in the right overview column. Attention rows use a compact two-column desktop list and wrap normally on mobile. Marketplace Overview follows Attention Required; System Status sits beside its sales content, with Facilities Overview next. Existing status descriptions, last-checked timestamps and Backup destination are retained. Styles are scoped to the Super Admin executive dashboard. No sample-chart toggle, sample series or frozen preview status is copied into the application.
4. **How it works:** Existing `admin_dashboard_page(request)` supplies the page context. `global_dashboard` selects the executive partial and `show_bundle_suggestions` still controls all three recommendation panels. The includes render the same database-derived data with the same IDs. Existing dashboard/filter, bundle, chart and status scripts continue finding those IDs. System Status begins as Unknown / Not checked yet, then its existing script fills actual messages and timestamps. The stylesheet query version tells browsers to request the changed CSS. Moving includes changes presentation only.
5. **Backend / API behavior:** No endpoint, permission, query, link destination or business calculation changed. Recommendation actions retain the existing review dialogs/API; status retains the existing dashboard API and Backup link. No request was made to approve products, modify inventory, send messages/notifications or create records.
6. **Database / migration impact:** None. The QA renderer configures Django's template engine without database settings or installed application models. Its two attention rows exist only in a saved QA HTML fixture, never in PostgreSQL or application source data.
7. **Tests performed:** Actual production templates rendered with recommendations enabled/disabled; checked unique panel IDs, correct include order and status hooks/Unknown initial states. Verified the live local static URL returns HTTP 200 and its SHA-256 matches the edited CSS bytes. Isolated Chrome checked 1536, 1024, 390 and 320px: compact desktop rows, stacked status, recommendation order, overviews after Attention Required and no horizontal page overflow. Mobile action links may wrap instead of being clipped. The standalone fixture reproduces Bootstrap's existing `table-responsive` overflow utility because it does not load the CDN; this corrected a fixture-only table overflow. Desktop screenshot inspected and scoped `git diff --check` passed. The updated database-backed executive test was not executed in this database-free check.
8. **Remaining limitations / troubleshooting:** The signed-in browser session and live API refresh responses were not exercised by these checks. The local server's CSS delivery was verified directly. Refresh `/admin/dashboard/` in the browser; if an already-open tab still shows old styling, use browser Ctrl+Shift+R or Ctrl+F5. This is a browser reload, not VS Code's Run Without Debugging. No app/server/worker restart or collectstatic was run. Safe practice: use the dashboard's existing date dropdown and confirm that the three recommendation panels update in their new location; click a real recommendation's existing Review action when one exists, without changing any record. Confirm System Status displays a real last-check time rather than the test preview's fixed 11:29 AM label.

## Super Admin welcome greeting — 2026-10-20

1. **Cause / reason:** The Super Admin overview had no personal welcome. Add a compact greeting above its existing controls.
2. **Exact files changed:** `backend/templates/dashboard/partials/executive_dashboard.html:2` (`executive-toolbar`) groups the heading and original date controls; `backend/static/components/css/admin_dashboard_executive.css:3` styles the toolbar, line 4 styles `executive-welcome`, and line 5 removes the old controls margin within this toolbar; `backend/templates/dashboard/pages/admin_dashboard.html:25` updates the executive stylesheet version to `20261020-welcome-spacing`. This guide records the change. `scratch/dashboard-executive/verify_welcome_spacing.js` and its HTML fixture provide isolated layout verification.
3. **Changes made:** Display `Welcome back, [name]!` in navy with the existing web font and responsive 20–26px sizing. Follow-up spacing correction: the screenshot showed the date controls on a separate right-aligned row, leaving unused space below the greeting. A wrapping flex toolbar places greeting left and controls right in one desktop row, with 16px below the entire row instead of separate heading/control margins. It wraps with a 12px vertical gap when space is limited. No extra card or decorative container.
4. **How it works:** Existing `admin_dashboard_page(request)` supplies the dashboard and Django's authentication context supplies `user`. The template expression `user.first_name|default:user.username` takes the actual first name, falls back to the username when empty, and produces escaped HTML text. Example: first name `Lester` produces `Welcome back, Lester!`. The `global_dashboard` branch includes this executive partial, keeping the greeting specific to the Super Admin overview.
5. **Backend / API behavior:** No view, query, endpoint, permissions, dashboard data or filter behavior changed. No new function or API call is needed.
6. **Database / migration impact:** None; existing account fields are read only.
7. **Tests performed:** Rendered the actual heading with Django's template engine using first-name, empty-name/username fallback and HTML-escaping cases: all three passed without database access. Follow-up isolated headless Chrome check used actual toolbar/filter markup and the production filter/summary/executive styles at 1536, 1024, 390 and 320px: desktop row aligned, narrow layouts wrapped, no horizontal overflow, zero extra controls bottom margin. Desktop screenshot inspected. Scoped `git diff --check` passed. No app/server restart or live authenticated browser check performed.
8. **Remaining limitations / troubleshooting:** This uses the first name rather than the full name. If the username appears, check the account's saved first name. If styling is stale, refresh the browser; the stylesheet URL has a new cache version. Safe practice: edit only the isolated fixture greeting to a long name and rerun `node scratch/dashboard-executive/verify_welcome_spacing.js`; confirm wrapping without overlap. No database account edits are needed. To verify the full page, sign in as Super Admin and open Dashboard; confirm one greeting beside the date controls on desktop and above them on mobile. Filter IDs and their existing JavaScript listeners remain unchanged; this CSS/markup correction does not test API refresh responses.

## Suggested Product Bundles: section only — 2026-10-14

### 1. Cause / reason

The user narrowed the larger Apriori/seller-workflow request to adding the section first. This change implements the presentation only, directly after Product Performance and before Marketplace Operations. Existing Attention Required and Seller Overview stay in place.

### 2. Exact files changed and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 14 stylesheet version; 98 new section; 100 `bundleSuggestionsTitle` | Card, terminology, disclosure, eight-column table and honest empty state; subsequent section comments renumbered. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 436 synthetic label; 437 notice; 440 empty helper; 441 focus styling | Scoped navy/gold/white label/notice styles and keyboard-visible scroll-region focus. |
| `scratch/marketplace-admin-dashboard/check.cjs` | near `document.fonts.ready` comment in the existing review loop | Wait for actual shared chart initialization instead of assuming 400 ms is always sufficient. |
| `docs/dashboard-analytics-operations-update.md` | this section | Implementation/verification/learning guide. |
| `CAMPUSHUB_CONTEXT.md` | Suggested Product Bundles section only | Current narrowed scope remembered. |

### 3. Changes made

Added Suggested Product Bundles with Apriori Association-Rule Mining wording, a SYNTHETIC label and the requested Synthetic Dataset Notice. Table headings: Bundle, Seller, Support, Confidence, Lift, Data Source, Status, Action. The table currently shows No qualifying bundle suggestions found, with a short note that results are not yet available. There are no invented product rows, metrics or nonfunctional action buttons.

### 4. How it works: inputs, outputs and data flow

This is a Django template/CSS change, without a new application function. The existing `admin_dashboard_page()` selects the dedicated Marketplace Admin template; its shared Product Performance include renders first, followed by the new section and the existing Operations heading. The new section reads no transaction, rule or suggestion dataset yet. Existing sales queries and context remain independent.

```html
<section aria-labelledby="bundleSuggestionsTitle">
  <h2 id="bundleSuggestionsTitle">Suggested Product Bundles</h2>
</section>
<!-- aria-labelledby connects the section to its visible title for assistive technology. -->
```

The existing `dash-card`, `dashboard-table` and `table-responsive` styles provide card/row layout and internal scrolling. New rules are scoped to `.marketplace-dashboard`, protecting other dashboards. A focusable, named table region allows keyboard scrolling when its eight columns exceed phone width. Shared Chart.js initialization waits for browser fonts; the QA helper now polls that actual ready state to avoid a timing-only false failure.

### 5. Backend / API behavior

No backend or API change. Existing RBAC, Program/Major scoping, real sales, inventory, activities and approval behavior remain. No suggestion is generated, sent, accepted or converted into a product by this section-only step.

### 6. Database / migration impact

No models, migrations, data import, rules, bundles or live records created/changed. No synthetic transactions enter the marketplace sales tables. A synthetic dataset path is not required for this presentation-only step.

### 7. Verification, debugging and practice

- **Two existing Django tests passed**: actual dashboard rendering/permissions and isolated browser fixture export; system check reported no issues.
- Rendered DOM inspection confirmed placement between Product Performance and Operations, eight headings and no action buttons/forms.
- **15 browser cases passed across five widths**: populated/empty dashboard and existing Order Details at 1440/1024/768/390/320 px, with card/chart containment and no JavaScript exceptions. The initial 320px check ran before asynchronous chart initialization; waiting for the real ready state resolved that QA timing issue. Production chart code was unchanged.
- Scoped changed-file whitespace checks passed.

Manual check: Ctrl+F5 Marketplace Admin Dashboard. Confirm the section's position, synthetic disclosure, table headings and empty state. Scroll the table inside its card on narrow screens. Existing sales values must remain unchanged; clicking elsewhere must not create/send a suggestion.

Debugging: if the new notice is unstyled, verify asset `20261014-bundle-section` and hard-refresh. An empty table is intentional at this stage, not a failed Apriori calculation: no rule integration was included. Do not insert example metrics into the template to make the table look populated.

Safe practice: on a local branch, change only the helper sentence inside the empty-state `<small>` element. Refresh Marketplace Admin and confirm heading order, eight columns and sales values stay unchanged. Revert the sentence. This teaches presentation edits without changing business logic or database records.

### 8. Remaining limitations

Apriori calculation/storage, dataset ingestion, admin sending, seller review/decline and bundle-form prefill are deferred by the user's latest instruction. The label/notice establishes the intended synthetic demonstration context; no generated results are displayed yet. Browser phone sizes are simulated, not physical-device deployment testing.

## Marketplace Admin: Attention Required — 2026-10-13

### 1. Cause / reason

The user requested Attention Required on the newly refined Marketplace Admin dashboard. Its overview/operations already had scoped counts and lists, but no compact actionable summary near the top. This update adds one below Marketplace Overview, before Sales Overview, while retaining the existing seven main sections.

### 2. Exact files changed and current anchors

| File, relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_attention.py` | 22 `inventory_attention_counts`; 49 `build_attention_required`; 62 `pending_orders` | Accept an optional authorized product queryset and pending-order count; reuse existing stock classification, positive-only rows, grammar and links. Default global behavior remains. |
| `backend/core/modules/reports/views.py` | 522 `attention =`; 549 context key | Pass scoped products and already computed product/seller/order counts. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 14 stylesheet version; 92 shared include | Reuse `dashboard/partials/attention_required.html` below overview; no duplicate attention template. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 436 attention styles | Compact white section, navy text/action links, small gold warning icons, phone wrapping; scoped to Marketplace Admin. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | 182 scoped-count test; 203 empty-scope test | Full counts beyond preview limit, routes, dates/grouping independence, zero hiding and missing-major checks. |
| `scratch/marketplace-admin-dashboard/check.cjs` | 51 shared-section assertion; 57 positive rows | Verify position, actual rows and empty state at five widths. |
| `docs/dashboard-analytics-operations-update.md` | this section | Functions, data flow, testing/debugging and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | Marketplace Admin Attention Required | Remember the current placement and scope. |

### 3. Changes made

Show only positive current counts: Low Stock Products, Out of Stock Products, Pending Product Reviews, Pending Seller Applications and Pending Orders. Each row has an existing filtered route/action. Singular labels are used for a count of one. No urgent items require attention is shown when the list is empty.

No Facilities, Services, system-health or backup rows are populated on this dedicated dashboard. Existing detail lists and overview KPIs remain; the attention rows are quick links to actionable queues.

### 4. How it works: functions, inputs, outputs and data flow

`inventory_attention_counts(today, products=None)` takes today's date and an optional Product queryset. A supplied queryset is already authorized by `scope_products`; the helper applies existing active/single-product, configured threshold, expiry and variant rules to that exact dataset. If omitted, it retains the existing global Super Admin source. The explicit `is None` test matters: an empty scoped queryset must stay empty, rather than fall back to global products.

`build_attention_required(..., products=None, pending_orders=0)` receives current counts and outputs a dictionary containing counters and an `items` display list. It creates a row only when its count is greater than zero. Products are counted once if a variant is low, according to the existing helper; these are product counts, not variant-row counts. Bundles use component warnings, not invented standalone stock.

The Marketplace view reuses its existing pending-product, pending-seller and order-status aggregates. Inventory attention is counted over the complete scoped dataset, not the bounded six-row preview; nine qualifying products produce a count of nine even if only six are listed below. No second threshold or reservation formula is added.

```python
products = scope_products(Product.objects.filter(is_archived=False), actor)
# Pass this queryset into the shared builder. Even products.none() remains empty.
attention = build_attention_required(
    today=today, products=products, pending_products=product_counts['pending'],
    pending_sellers=seller_counts['pending'], pending_orders=status_counts.get(MarketplaceOrder.STATUS_PENDING, 0),
    pending_bookings=0, booking_conflicts=0, maintenance_facilities=0, unavailable_facilities=0,
)
# items contains only positive marketplace rows; no facility queries are run.
```

Flow: authenticated actor -> existing academic scope -> current aggregate/classifier -> positive rows -> existing shared template -> protected filtered module page. Current attention is independent of Sales Overview's reporting period and chart grouping, because pending work/current stock should not disappear when viewing older sales.

### 5. Backend / API behavior

No new endpoint or permission. Reuse Inventory `view=inventory&inventory_status=low_stock` / `out_of_stock`, Products `status=pending`, Sellers `status=pending` and Orders `status=pending`. Target pages retain their server-side RBAC/academic checks. The global builder's optional pending-order default is zero, so its existing visible rows are unchanged; its inventory source remains global when no queryset is supplied. Dedicated sales AJAX behavior is unchanged; attention renders on the normal page GET.

### 6. Database / migration impact

No model, migration, grant or production-data change. This is read-only aggregation and presentation. Test records exist only in the isolated Django database.

### 7. Tests, manual verification and debugging

- **52 focused Django tests passed** for the dedicated Marketplace Admin dashboard and global dashboard periods/attention. New checks confirm nine scoped low-stock products are not truncated to six, other-major records are excluded, action filters are correct, reporting dates do not alter attention, zero rows disappear and missing BTLED major fails closed.
- **15 Chrome cases passed**, covering populated/empty pages and existing Order Details at 1440/1024/768/390/320 px. They also confirm one shared Attention Required section below overview/before Sales Overview, only positive rows, visible empty state, fitting cards and no JavaScript exceptions.
- System checks reported no issues; scoped whitespace checks passed. One initial test fixture unintentionally created its eight low-stock products as Pending (the real model default); the fixture now explicitly approves those records so only the intended review submission is pending.

Manual test: Ctrl+F5 the Marketplace Admin dashboard. Compare attention counts with the corresponding filtered Products/Inventory/Sellers/Orders page. Click each action; confirm its filter is active. Change the sales period/grouping; current attention should stay the same. In an isolated environment with no actionable records, expect the no-urgent-items message and no zero-count rows.

From `backend/core`:

```powershell
$env:MARKETPLACE_DASHBOARD_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/marketplace-admin-dashboard'
venv/Scripts/python.exe manage.py test modules.reports.test_marketplace_admin_dashboard modules.reports.test_dashboard_periods --keepdb --noinput
# From project root, with the existing local browser QA dependencies:
node scratch/marketplace-admin-dashboard/check.cjs
```

Debugging: if the section is unstyled, hard-refresh and check asset `20261013-marketplace-attention`. For unexpected counts, inspect the passed authorized queryset and actual product/variant thresholds, never replace the helper with a fixed five-unit test or global Product query. A preview shorter than the attention count is expected. Missing scope must yield no rows; it must never trigger a global fallback.

Safe practice: change only the visible action wording in the existing shared attention definitions on a local branch, keeping its key and route intact. Refresh both dashboards and verify scoped counts/links remain identical; run the focused tests and revert the wording. This teaches separation of display labels from data and navigation. Shared-label edits affect both dashboards, so review both before keeping them.

### 8. Remaining limitations

Counts use the existing product-level attention classifier and application records; this task does not redefine variant warning totals or rewrite application history. Attention updates on page reload, without a new polling/push service. Browser phone widths were simulated in Chrome; no deployed physical-device testing is claimed.

## Marketplace Admin refinement — 2026-10-13

This section applies to the dedicated Marketplace Admin dashboard. It does not replace the Super Admin template or its global analytics. Older sections below describe their own historical changes.

### 1. Cause / reason

Inspection confirmed the dedicated dashboard was the right base, but Pending Listings used older terminology, orders/sales/rankings mixed all-time and selected-period sources, low-stock rows used a fixed five-unit test and truncated the first 100 products, seller counts depended on the old Seller role, and no scoped marketplace audit feed existed. Product/category highlights were combined with Sales Overview rather than the requested seven sections.

The requested result is a marketplace-only operational dashboard using existing business rules and the same academic scope as Products, Inventory, Orders and Sellers. No sample records were added to the application.

### 2. Exact files changed, lines and anchors

Paths are relative to project root. Use the anchors when later edits shift lines.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/views.py` | 257 `_resolve_sales_period`; 459 `_marketplace_operational_dashboard_data`; 483 `valid_sales_queryset`; 496 inventory shortlist; 515 seller aggregate; 525 audit selection | Add 90-day compatibility; assemble dedicated scoped metrics, operations and activities from canonical helpers. |
| `backend/core/accounts/support_scope.py` | 114 `scope_marketplace_activity` | New read-only resource-based boundary for the existing audit table; existing support/monitoring scope stays unchanged. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 35 Marketplace Overview; 95 Marketplace Operations; 174 Seller Overview; 193 Recent Orders; 217 Recent Marketplace Activities | Seven-section ordering, labels, submission/threshold columns, scoped links and real feed. |
| `backend/templates/dashboard/partials/marketplace_overview_row.html` | 1 marketplace branch; 5 Product Performance; 9 Top-Selling Products; 22 Product Categories | Reuse existing partial with dedicated ranked-table/category presentation; preserve other dashboard branch. |
| `backend/templates/dashboard/partials/sales_overview.html` | 9 hidden-days condition; 17 90-day option | Marketplace period selection has one source; other dashboard controls unchanged. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 435 dedicated rules; 461 comparison wrapping; 474 narrow header | Scoped navy/neutral presentation, card/table containment, wrapping and tiny-screen header fit. |
| `backend/core/modules/marketplace/static/marketplace/js/admin_marketplace_dashboard.js` | 1 existing DOM-ready handler | Keep actual Order Status donut; remove unused second sales-chart implementation and unused period listener. |
| `backend/core/modules/marketplace/services/orders.py` | 25 `selected_order` | Optional exact-order GET filter intersects the already authorized queryset. |
| `backend/static/components/js/admin_orders.js` | 449 `requestedOrder` | Open existing Order Details only for an authorized rendered row. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html` | 418 script version | Refresh deep-link JavaScript cache. |
| `backend/core/accounts/tests.py` | 468 dedicated dashboard assertions | Update old expected KPI labels to the requested names. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | 18 test class; named test methods | Scope, dates, stock, audit evidence, seller status, query growth and existing-route tests; isolated browser fixtures. |
| `scratch/marketplace-admin-dashboard/check.cjs` | 1 fixture-only browser review | Actual Chart.js, dashboard rendering and existing Order Details checks at five widths. |
| `docs/dashboard-analytics-operations-update.md` | this section | Implementation report, data flow, troubleshooting and learning exercise. |
| `CAMPUSHUB_CONTEXT.md` | Marketplace Admin dashboard refinement | Current scope and dashboard behavior remembered. |

### 3. Changes made / requested feature report

1. **Components reused:** the dedicated marketplace page, shared sidebar/header, Sales Overview partial/JavaScript, existing dashboard cards/tables/icons, existing category-count helper and Order Status donut. No second dashboard template was created.
2. **Analytics reused:** `valid_sales_queryset`, `_sales_time_series`, `_sales_overview_summary`, `top_selling_products`, `sales_by_product_category` and `recent_marketplace_orders`. No second payment, stock or sales formula.
3. **Marketplace Overview:** four KPIs: Total Products, Pending Product Approvals, Total Orders, Marketplace Sales. Product/approval counts are current active listings; orders are submissions in the selected period; revenue is valid sales in that period.
4. **Sales Overview:** Total Sales, Completed Orders, Average Order Value and the existing trend chart. Today/7/30/90 days, month/year/custom and Daily/Weekly/Monthly reuse the existing period/grouping path. No sample toggle or sample JSON is included.
5. **Product Performance:** top five by actual units sold, then revenue and stable identity; variants remain under their parent and bundle components are not exploded. Category donut shows current product counts; table adds completed-sale revenue/share for the selected period. Product counts and sales are distinct measures, explicitly described above the table.
6. **Marketplace Operations:** up to six pending product rows now include Submitted and exact product review links. Up to six low-stock rows use saved product/variant thresholds and show variant, seller, available and threshold. Order Status uses existing Pending/Processing/Ready for Pickup/Completed/Cancelled constants and current scoped totals.
7. **Seller Overview:** counts come from the same scoped SellerRequest source as Sellers, using approved/non-suspended, pending and approved/suspended states, rather than the account's role. View All Sellers uses the existing permission-protected route.
8. **Recent Orders:** newest eight selected-period scoped transactions; customer, quantity, total, order status, payment, date and View. View opens the existing Orders modal through an exact authorized GET selection; it does not create another detail page.
9. **Recent Marketplace Activities:** newest eight resource-authorized AccountActivity records. Existing action/actor formatting supplies type and Performed By; recorded message/date remain factual. No second logger, fabricated event or unrestricted global activity feed.
10. **Excluded widgets:** no global Users, Facilities/Bookings, Services, utilization, reservation/revenue/status, database/chat/backup status or warnings. Dedicated branch does not load Super Admin dashboard data/API or sample widgets.
11. **Academic scope:** reuse `scope_products`, `scope_seller_requests`, `scope_users` and `admin_order_queryset`. BTLED requires its assigned major; missing/invalid assignment returns no data. Explicit product program/major overrides inherited seller scope. Removed redundant seller-department restrictions that could wrongly hide an explicitly scoped product.
12. **RBAC/sidebar:** no grants or sidebar redesign. Existing server-side page/API checks remain. Marketplace has explicit scoped Users/Monitoring support permissions in current role defaults; those links are retained because this request permits explicitly granted access. Facilities and global dashboard API remain denied. Optional View All Activities was omitted to avoid linking to a differently scoped monitoring feed.
13. **Query/performance:** aggregate product and seller counters, group status once, bound table/feed queries, shared analytics aggregations and one batched seller lookup for stock rows. Audit entity/identity checks use SQL subqueries before ordering/limiting. Regression checks confirm adding 20 low-stock products/events does not create per-row query growth.
14. **Responsive checks:** KPI wrapping, real charts, table scroll containment, card edges, honest empty messages and existing Order Details at 1440/1024/768/390/320 px. Very narrow header/comparison wrapping is scoped to this page.

### 4. How it works: inputs, outputs and data flow

`_marketplace_operational_dashboard_data(request, user)` takes an authenticated dashboard actor and GET period/grouping inputs. It outputs the existing `marketplace` context dictionary and sales payload. Products use academic scope; orders use the canonical authorized Orders queryset, which also excludes unenforceable legacy multi-item snapshots for scoped admins.

Revenue uses `valid_sales_queryset(user)`: Completed + Paid + positive quantity, timestamp `completed_at`, otherwise `paid_at`, otherwise `created_at`. It is intersected with authorized orders, then restricted to the selected dates. Revenue = sum of `total_price`; Completed Orders = count; Average Order Value = revenue / count, or zero when no orders exist. The existing equal-length previous-period comparison avoids division by zero. AJAX `period_sales_sum` keeps its plain decimal string format for compatibility.

Products and approvals are current catalog state. Stock and seller access are current operational state. Total Orders/recent orders use creation date; sales/rankings use the canonical sale timestamp. This distinction means an order created earlier and completed now can count as current sales without being a newly submitted order.

`low_stock_inventory_rows(products, limit=6)` reads canonical remaining inventory and every tracked variant's threshold. This repository already deducts stock when reserving: do not subtract reservations again. Zero/expired stock and bundles are excluded by this existing positive-low-stock helper; bundle alerts belong to component inventory. The dashboard does not invent standalone bundle stock. Seller names are loaded in one batch after the shortlist.

`scope_marketplace_activity(queryset, actor)` filters the existing audit queryset, not a new log. It permits marketplace event types/modules only, requires real scoped resource evidence, and gives order references precedence over product references, then seller applications, then seller-only account identities. Mismatched saved program/major metadata fails closed. Missing resource/evidence is omitted rather than guessed from whoever performed the action. `format_activities(..., scoped=True, include_targets=False)` resolves actor names in a batch without exposing connection/metadata fields.

```python
orders = admin_order_queryset(actor)  # Already authorized product/program/major boundary.
sales = valid_sales_queryset(actor).filter(pk__in=orders.values('pk'))
# A cross-major product cannot enter sales merely because its buyer is in this major.
# Chart grouping changes buckets; it does not change the authorized queryset.
```

Flow: authenticated request -> existing scope helpers -> authoritative records -> grouped/bounded read queries -> existing page context -> shared templates/chart. A period change submits GET and re-renders all period-aware sections; chart grouping keeps dates and operational counts. The removed Marketplace-only hidden `sales_days` prevents an old value from overriding a newly chosen 90-day period.

Order link flow: dashboard `/admin-orders/?order=<id>` -> `admin_order_queryset` -> `filter_orders` intersects ID -> existing rendered row -> `openOrderDetail(row)`. A forged out-of-scope ID produces no matching row; JavaScript cannot open absent data. Existing write permissions, status transitions and Cash on Pickup logic remain authoritative.

### 5. Backend / API behavior

Reuse `/admin-dashboard/` HTML and its existing X-Requested-With sales response; no new unrestricted REST endpoint. `/api/admin/dashboard/` remains Super Admin-only. The centralized Django audit models/logging and existing DRF monitoring endpoints are unchanged. Adding a dashboard audit reader does not broaden User Monitoring's existing account-support reader. No business logic moves to FastAPI.

Existing sidebar/menu permissions and notification sources are preserved. Review and Inventory links use existing `status=pending`, `product_id`, `view=inventory` and `inventory_status=low_stock` filters. Existing Orders GET selected ID is a narrowing filter, never an authorization bypass.

### 6. Database / migration impact

No models, fields, migrations, grant rewrites or live writes. `makemigrations --check --dry-run`: No changes detected. Tests/QA artifacts use isolated test records only. No deployment seed or sample dashboard dataset was added.

### 7. Tests performed, debugging and commands

- **128 regression tests passed** on a fresh isolated test database: dedicated dashboard, global marketplace/period dashboards, shared Sales Overview, Marketplace account support, Orders and Program inventory scope. Tests cover conflicting audit references/snapshots, absent major, explicit/inherited scope, invalid sales, individual variant thresholds, unlinked mobile seller requests, forged links and bounded query growth.
- A preliminary reused-test-DB run failed because unrelated existing fixtures expected seeded Program records that were absent. The fresh runner recreated only `test_campushub`, applied migrations and passed; it did not seed or modify the application database. Two obsolete KPI-label assertions were updated; test fixture email and permission-redirect expectations were corrected.
- **15 browser cases passed**: populated/empty dashboard and actual Order Details deep link at five widths, real Chart.js, no JavaScript exceptions, no whole-page overflow, period/grouping form values and zero-sales baseline. Initial 320px header/comparison overflow was corrected with page-scoped CSS.
- Read-only rendering with an existing active Marketplace Admin returned HTTP 200. No account names/credentials or response contents were printed.
- Final focused compatibility test passed after preserving ungrouped AJAX decimal strings: a displayed `1,200.00` total is returned as machine-readable `1200.00` in `period_sales_sum`; legacy multi-item exclusions remain enforced.
- Django system check, changed JavaScript syntax and scoped whitespace checks passed; no migrations detected.

For normal local use, restart the Django server only if your setup does not auto-reload, and Ctrl+F5. No migration or package-install command is needed.

Reproduce tests from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.reports.test_marketplace_admin_dashboard modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_periods modules.reports.test_sales_overview accounts.test_marketplace_support modules.marketplace.test_orders_admin modules.marketplace.test_program_inventory.ProgramInventoryTests --noinput
# Optional fixture export (isolated test DB only):
$env:MARKETPLACE_DASHBOARD_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/marketplace-admin-dashboard'
venv/Scripts/python.exe manage.py test modules.reports.test_marketplace_admin_dashboard --keepdb --noinput
# From project root, using existing local QA dependencies:
node scratch/marketplace-admin-dashboard/check.cjs
```

Manual tests:

1. Sign in with an assigned Marketplace Admin. Confirm seven sections in order, four overview cards and no facility/service/system/global-user widgets.
2. Compare Products/Orders/Sellers with the dashboard for the same account. An admin in BTLED-ICT must not see HE/IA or other-program rows. Test missing assignments in an isolated test environment, not by modifying a live administrator.
3. Choose Last 7 Days, Last 90 Days, then a custom range. Sales, rankings and recent orders follow those dates; current stock, approvals and seller/status totals remain current. Weekly/Monthly keeps the same selected dates and ranking totals.
4. Review a saved low-stock variant: its own available quantity/threshold/name must match Inventory. No bundle standalone stock should appear.
5. Click Recent Orders View. The existing Order Details modal should open the exact order, with unchanged actions. A foreign order ID must not expose a row.
6. Verify real recent product/inventory/order/seller events and honest empty messages. No unrelated recovery, role, facilities or backup events should appear.

Debugging: unexpected zero data often means missing or mismatched assignment—inspect `has_valid_marketplace_scope`, never remove the scope check. Inspect `period`, `sales_days` and sale timestamp when revenue differs from order submission totals. An old KPI label or missing deep-link behavior usually means cached scripts; dashboard assets use `20261013-scoped-dashboard`, Orders uses `20261013-dashboard-order-link`. SQL/debug tools should inspect counts/query plans without printing credentials or whole audit metadata.

Safe practice: in a local branch, change only the Top-Selling Products subtitle in the shared partial's marketplace branch. Refresh Marketplace and Super Admin; confirm only the dedicated text changes and all metrics remain identical. Revert it, then run the scoped dashboard tests. This teaches template branches and role-boundary verification without modifying records.

### 8. Remaining limitations

Old events without verifiable scoped resources/seller identity are omitted; no history is fabricated or backfilled. The feed only shows actions already recorded by the existing logger. Deleted/unscoped resources and conflicting historical metadata fail closed. Seller counters follow existing application records; this task does not rewrite duplicate/legacy applications.

Category counts describe current non-archived listings while revenue uses sale snapshots, so historical categories/renames need not exactly match the current catalog chart. Low Stock follows the existing positive-stock helper; Out of Stock remains available in Inventory rather than being mislabeled Low Stock. Period changes reload the dedicated page; no new live push refresh was introduced. Wide tables scroll inside their cards on narrow screens. Browser widths were simulated in Chrome; no deployed physical-phone testing was claimed.

Update 2026-10-06: Most Booked Facilities now replaces the Super Admin single highlight with a real top-five count list using existing product-card styles. Booking Trend grouping now updates only Booking Overview, and the shared global selector includes Previous Month. See [the current feature report](most-booked-facilities.md) for exact lines, query/status/date rules, verification and debugging practice. Earlier asset versions below describe their stated historical updates.

The latest Recent Orders arrangement is documented below. The original 2026-10-05 implementation is retained afterward as historical context; later feature guides and current explicit preferences take precedence over its older layouts and labels. Line numbers are current for the stated update; search by nearby anchors after later edits.

## Recent Orders column arrangement — 2026-10-06

### 1. Cause / Reason

You asked to arrange the dashboard's Recent Orders columns. Items now appear directly after Order ID, followed by Customer. Totals align right, order/payment statuses align center, and text/date columns align left. Initial rendering and refresh must match so a refresh cannot put customer names under Items.

The previous narrow-card rule depended on a populated order-code cell. Empty tables therefore lost the minimum-width protection and could squeeze their seven headings together. The new minimum width applies in both states.

### 2. Exact Files Changed

Paths are relative to the project root. The anchors remain useful when line numbers shift.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/recent_orders.html` | 9, `colgroup`; 12–18, headings; 25 and 35, Items/Customer cells | Move Items before Customer in column definitions, headings and server-rendered rows. Add semantic cell classes for items, customer and order status. |
| `backend/static/components/js/admin_dashboard_filter.js` | 236, `renderRecentOrders()`; 249, `const items`; 266, `const status`; 269, `row.append()` | Match the initial template's cell order and classes when refreshing rows. |
| `backend/static/components/css/admin_marketplace_overview.css` | 138, `.recent-orders-table`; 159, product-name rule; 323, `Preserve readable` | Keep a 760px minimum width in all states; use 12px readable text, consistent padding, left/right/center alignment and semibold navy key values. Locations reflect the later stylesheet recovery. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 and 563, asset links | CSS now uses `20261006-marketplace-layout-recovery`; the existing JavaScript version remains `20261006-recent-order-columns`. See `top-products-sample-photo-layout.md` for the recovery report. |
| `CAMPUSHUB_CONTEXT.md` | 13, current Recent Orders arrangement | Preserve the accepted layout for future changes. |
| `docs/dashboard-analytics-operations-update.md` | This latest section | Update the existing guide with the report, function explanation and debugging exercise. |

Existing isolated Django fixture HTML/JSON files were regenerated under `scratch/sales-overview-system-test/`. Operations-only browser previews and four screenshot/DOM/log cases were generated under `scratch/dashboard-global-review/recent-columns-*`. These are development artifacts, not live orders.

### 3. Changes Made

The order is **Order ID → Items → Customer → Total → Order Status → Payment Status → Date**. The three parallel structures—`colgroup`, headings and row cells—are reordered together. Refresh-generated rows use the same arrangement.

Totals use right alignment and tabular numerals. Both status headings and their values are centered. Text and dates are left-aligned, with natural wrapping for dates and longer names. Headings retain the navy/white/semibold palette; key codes and totals use semibold, while supporting row text uses regular weight.

No columns or order data were removed. The seven-cell empty-state span, newest-first records, separate payment status, View All, Retry and internal hidden-scrollbar behavior remain.

### 4. How It Works

| Function / structure | Input | Output / responsibility |
| --- | --- | --- |
| Existing Django dashboard view and recent-order snapshot | Actual marketplace order records and the user's permitted dashboard request | Supplies `recent_orders` with code, product, customer, total, order status, payment status and date. Unchanged. |
| `recent_orders.html` | That context list | Renders each order's seven cells under matching headings on first load. |
| `renderRecentOrders(orders)` at JavaScript line 236 | `operations.recent_orders` from the existing dashboard API | Builds seven cells in the same order and replaces the table body. Handles the existing empty state. |
| Table CSS | Header/cell classes and available card width | Applies alignment, padding, typography and the minimum readable table width. |

Data flows from actual database orders → Django snapshot → initial template or API JSON → table cells → CSS. Only the position and appearance of cells change; totals, quantities, dates and statuses retain their existing meanings.

```javascript
// Excerpt of the renderer: cell position must match the header position.
row.append(
    cell(order.code, 'recent-order-code'), // First column: Order ID.
    items,                               // Second column: product and quantity.
    cell(order.buyer_name, 'recent-order-customer') // Third column: Customer.
    // The actual code then appends total, order status, payment status and date.
);
```

This is an explanatory excerpt, not replacement code. The renderer's local `cell(text, className)` helper takes text and an optional class name, creates a `<td>` and returns it. `textContent` displays the supplied text safely. The `items` element includes the existing actual product name, quantity and available image.

The table has `min-width: 760px` in both populated and empty states. When its card is narrower, the existing focusable wrapper scrolls horizontally. The page itself stays within the viewport. No conditional switch based on existing row content is needed.

### 5. Backend / API Behavior

Unchanged. No endpoint, permission, query ordering, payload field or transaction logic changed. Both initial render and refresh read the existing real-data snapshot. Recent Orders remains the newest six records across dates, separate from period-based analytics.

### 6. Database / Migration Impact

None. No models, schema, migrations or live records were changed. Verification records stayed in the isolated Django test database.

### 7. Tests Performed

- Two existing Django tests passed: `test_sales_overview_system_preview_values_and_grouping` regenerated current template fixtures; `test_analytics_operations_layout_and_removed_chart_tables` verified the dashboard's sections and separate status headings.
- A DOM check verified all seven heading positions and matching order-code/product/customer/status/payment/date cells in both the actual Django render and the JavaScript refresh output.
- JavaScript syntax, stylesheet parsing and the existing integrated marketplace sample/filter/tooltip/refresh verification passed.
- Four Chrome cases passed: populated/empty × desktop/mobile. Header and populated-row alignments matched left/left/left/right/center/center/left; all headings were navy semibold. Desktop tables fit their wrappers; narrow tables scrolled internally and the page did not overflow. The scroll region retained `tabindex="0"`.
- The populated desktop screenshot was visually inspected. Evidence: `scratch/dashboard-global-review/recent-columns-populated-desktop.png`, the other three matching PNGs and their `.dom.html` measurements.

#### Debugging steps

1. Use Ctrl+F5 to load both updated assets. Verify the CSS and JavaScript versions in Network if an old layout persists.
2. Compare the first load with Refresh. If values move into the wrong columns only after Refresh, inspect `renderRecentOrders()`; if the first load is wrong, inspect the template.
3. Check the `colgroup`, header sequence and cell sequence together. Width definitions alone do not move values.
4. If text appears misaligned, inspect Computed → `text-align`, including Bootstrap's `.text-end` for totals and the status-cell selectors.
5. For narrow or empty states, inspect the table's `min-width` and the wrapper's `overflow`. Scroll inside the table region; a hidden scrollbar does not mean scrolling is disabled.

See [the reusable debugging guide](DEBUGGING_GUIDE.md) for recording confirmed issues and test evidence.

#### Safe practice exercise

In browser Developer Tools, select a total cell and temporarily change `text-align` from right to left. Observe how the values stop lining up with the Total heading. Restore right alignment or reload to discard the temporary edit. Check the computed value and compare the initial page with Refresh. This teaches alignment and how CSS differs from data ordering without changing source files or database records.

### 8. Remaining Limitations

Seven columns require internal horizontal scrolling on narrow screens, including the empty state. Long names may wrap. The centered status-heading selectors refer to positions five and six; any future reordering must update those selectors too. Physical touch devices and other browser engines were not tested. Browser screenshots use isolated fixture transactions rather than live user orders.

## Historical implementation — 2026-10-05

Implemented from your “UPDATE CAMPUSHUB SUPER ADMIN DASHBOARD FROM SALES OVERVIEW TO BOOKING OVERVIEW” attachment. The following report describes that original change; newer sections and feature guides supersede its older labels, positions and line numbers.

## 1. Cause / Reason

You asked to separate historical analytics from current marketplace operations, remove visible chart-data tables and the booking availability caution, and let each chart independently group the globally selected date range. The implementation reuses Django, the existing global dashboard endpoint, Inventory, Orders, Bookings and Chart.js.

## 2. Exact Files Changed

Application files:

| Folder / file | Current line | Nearby anchor | Added, changed, moved or removed |
| --- | --- | --- | --- |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 10 | `Top 5 Best-Selling Products` | Renamed the ranked card to the requested title. Its rank, product, units and sales amount remain connected to real data. |
| Same file | 26, 30 | `marketplace-category-row`, `marketplace_operations.html` | Moved category sales into its own full-width analytics row. Removed Low Stock and Recent Orders from the former analytics slots; includes the new Operations section after Analytics. |
| `backend/templates/dashboard/partials/marketplace_operations.html` | 1 | `marketplaceOperationsTitle` | Added the section heading and layout row. Reuses the existing Low Stock and Recent Orders partials; no new management page. |
| `backend/templates/dashboard/partials/recent_orders.html` | 9, 17, 21 | column group, `Payment Status`, `data-recent-order-rows` | Changed to seven columns: Order ID, Customer, Items, Total, Order Status, Payment Status and Date. Items include the actual quantity. Added a target for refreshing rows, truthful empty state and loading/error/Retry controls. |
| `backend/templates/dashboard/partials/sales_overview.html` | 79, 84 | `salesOverviewChart`, `salesTrendDescription` | Removed the visible View chart data toggle/table/caption from the Super Admin branch. Added keyboard focus and an invisible accessible list instead. Updated the chart-library failure message to point to Detailed Analytics. The domain dashboard branch retains its prior table. |
| `backend/templates/dashboard/partials/booking_overview.html` | 20 | `booking-overview__trend-header` | Added the Daily/Weekly/Monthly selector beside Booking Trend. Removed the availability caution paragraph. The existing stacked chart and invisible accessible breakdown remain. |
| `backend/static/components/css/admin_marketplace_overview.css` | 3, 6, 99 | operations section, category row, operations row | Styled the moved cards, compact Top 5 height, full-width category card, and wider Recent Orders column. Moved hidden-scrollbar rules into Operations and added Recent Orders loading/error styles. Removed obsolete category/recent paired-row styles. |
| Same file | 134 | `@container recent-orders` | Keeps seven-column tables readable by allowing internal horizontal scrolling on narrow cards. Tracks/thumbs remain hidden and the table region stays keyboard-focusable. |
| `backend/static/components/css/admin_booking_overview.css` | 18, 22 | attention, trend header | Removed caution styles and styled the grouping selector with a subtle border, 44px height and visible keyboard focus. |
| `backend/static/components/js/admin_dashboard_filter.js` | 170 | `renderRecentOrders` | Added safe DOM rendering of real recent orders; separate payment text, quantities, product images and empty state. Uses textContent for database text. |
| Same file | 383, 464 | `booking_grouping`, `bookingGroupingSelect` | Sends both chart groupings through the existing API. Changing either chart preserves the active/requested global range. Existing abort/last-response handling prevents old requests overwriting newer selections. |
| Same file | 411, 458 | recent-orders error, `recentOrdersRetry` | Hides stale recent-order rows on request failure and connects Retry. Removed the old visible sales-table row renderer and table-dependent accessibility text. |
| `backend/static/components/js/admin_sales_overview.js` | 39, 42, 169 | `describe`, `updateDescriptions`, `keydown` | Supplies exact sales/order values to an invisible list and keyboard-accessible tooltip. Refresh clears old active points. Existing navy bars and gold line are retained. |
| `backend/static/components/js/admin_booking_overview.js` | 48 | `bookingGroupingSelect` | Synchronizes the selector with the backend's accepted booking grouping on each response. Existing four common-stack datasets and exact tooltip are retained. |
| `backend/core/modules/reports/dashboard_bookings.py` | 11 | `build_booking_overview(... grouping="daily")` | Replaced automatic grouping selection with an explicitly supplied Daily/Weekly/Monthly grouping. Reuses the existing one-query date/status aggregation and zero buckets. |
| `backend/core/modules/reports/dashboard_periods.py` | 137, 254, 261 | `booking_grouping`, `booking_overview`, `operations` | Parses booking grouping independently from sales grouping, passes it to the existing booking summary and adds a bounded recent-orders snapshot to the existing payload. |
| `backend/core/modules/reports/dashboard_marketplace.py` | 12 | `recent_marketplace_orders` | Added one presentation helper shared by initial page and refresh. Uses one joined query, newest first, capped at six records. Existing Top 5 and category calculations are unchanged. |
| `backend/core/modules/reports/views.py` | 1378 | `recent_orders = global_data` | Initial Super Admin page reuses the API helper's result, avoiding a second recent-orders query. Legacy/domain paths retain their existing query. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18, 20, 561 | updated stylesheet/script version strings | Bumped versions for the changed assets so refreshes load the new layout and behavior. |

Tests, review tools and saved guidance:

| Folder / file | Anchor / purpose |
| --- | --- |
| `backend/core/modules/reports/test_dashboard_bookings.py:78`, `:128`, `:155` | Selected grouping and independent sales/booking grouping tests; removed-caution markup assertion; real grouped fixtures. |
| `backend/core/modules/reports/test_dashboard_marketplace.py:68`, `:92`, `:287` | Newest-first six-record snapshot, separate payment status, layout order, table/caution removal and updated Top 5 title. |
| `backend/core/modules/reports/test_dashboard_periods.py:273` | Bounded query budget now allows the one added Operations snapshot query; remains independent of order count. |
| `scratch/dashboard-global-review/check-controls.cjs:69` | Existing global-filter DOM suite now checks Sales tooltip/keyboard access and Recent Orders refresh/error/recovery. |
| `scratch/dashboard-global-review/check-booking-overview.cjs:55` | Checks three real booking grouping responses, independent sales selection, no caution/table and existing status/tooltips. |
| `scratch/dashboard-global-review/prepare-booking-visual.cjs:8` | `measure` adds grouping measurements; state generation adds actual weekly/monthly chart previews. |
| `scratch/dashboard-global-review/render-booking.ps1:8` | Nine Booking Overview browser cases, including weekly and monthly. |
| `scratch/dashboard-global-review/verify-booking-visual.cjs:5` | Verifies grouping options, zero baseline, chart totals, no caution and responsive layout. |
| `scratch/dashboard-global-review/prepare-palette-visual.cjs:58` | `bookingLayout` and Operations measurements check complete-dashboard placement, columns, scrolling and removed chart tables. |
| `scratch/dashboard-global-review/verify-palette-visual.cjs:32` | Checks those complete-dashboard measurements on desktop and mobile. |
| `CAMPUSHUB_CONTEXT.md:7` | Saves the latest accepted placement, independent groupings and removed caution. |
| `docs/booking-overview-stacked-kpis.md:3`, `docs/booking-overview-status-colors.md:3` | Links these older guides to the current behavior. |
| `docs/dashboard-analytics-operations-update.md:1` | This implementation/learning guide. |

## 3. Changes Made

**Sales Overview:** kept Marketplace Sales, Completed Orders, Average Order Value, the grouping selector, the completed-paid Cash on Pickup note and zero-data chart. Removed its visible chart-data toggle, table and “Sales and orders by period” caption on Super Admin. Exact values remain in tooltips; keyboard users can focus the chart and press Left/Right/Home/End.

**Top 5:** renamed to Top 5 Best-Selling Products and kept it compact rather than stretching an empty/list card to the entire Sales Overview height. Rank number, product name, units sold and sales amount are present. No Apriori was added.

**Category Sales:** moved to one full-width card below the Sales/Top 5 row. The existing donut, category list, revenue percentage and sales amount remain. No listing counts or extra ranking cards were introduced.

**Low Stock:** moved from below Top Selling Products into Marketplace Operations. Its existing five-row limit, Available/Threshold columns, inventory logic and Low Stock shortcut remain.

**Recent Orders:** moved from beside Category Sales into Marketplace Operations, beside Low Stock. It receives approximately two-thirds of the desktop row because it has seven columns; Low Stock receives one-third. On narrower layouts both stack. Added quantity and a separate Payment Status column, plus live refresh/loading/error/Retry support.

**Booking Overview:** kept the full-width five-KPI card and one stacked bar per period. Added the grouping selector and removed the requested availability caution. Real pending-review attention remains conditional on pending requests. Completed green and Rejected/Cancelled red retain your explicit prior color choice.

## 4. How It Works

The global date filter decides **which dates** both analytics charts use. Each chart's selector decides **how those dates are grouped**. The request carries sales `grouping` and independent `booking_grouping`. Both accept only daily, weekly and monthly; neither selector includes Custom Range. Invalid API grouping values fall back to daily, following the existing sales convention.

Changing Booking Trend to Weekly during Last 30 Days keeps the last 30 days; it does not change the Sales chart grouping. A global date change retains each selected chart grouping. Reloading the page preserves the selections in the URL. Both default to Daily when omitted; Booking Overview no longer automatically changes grouping based on range length.

Existing booking grouping partitions the selected range into daily dates, seven-day blocks starting at the selected range's start, or calendar months clipped to selected dates. Existing Sales grouping uses its current calendar-week/month rules. No extra date filter or duplicate booking query was added.

Booking chart datasets share `stack: 'bookings'`, and both axes remain stacked. Thus four statuses produce one combined bar, not four side-by-side bars. The tooltip reports Total Bookings and all four exact status values for the period. Empty series retain real zero values and the chart baseline.

Operations are **current snapshots**: Low Stock reflects current inventory; Recent Orders shows the six newest recorded transactions across all dates, including pending/unpaid orders. They refresh alongside a global date/grouping change but are not historical snapshots of the selected analytics range.

## 5. Backend / API Behavior

Reuses the existing Super Admin `/api/admin/dashboard/` GET endpoint and its server-side authentication/permissions. New additive payload: `operations.recent_orders`. No new routes or management pages.

The new presentation helper uses `MarketplaceOrder.objects.select_related("product")`, sorts by creation time then ID descending, and reads up to six records. Actual model display labels supply order and payment status separately. Product names, quantities, customer names, totals and dates come from records; images use the existing protected product-image route. JavaScript retains the tab's authentication token for requests/images/navigation.

Existing analytics rules were verified and reused:

- Sales: completed **and paid** Cash on Pickup order records through the existing canonical sales timestamp.
- Top 5: quantity descending, then sales amount descending, maximum five. Variants aggregate by parent product; a sellable bundle recorded as its own product ranks as that product. One qualifying sale is sufficient.
- Categories: completed-paid sales amount by the recorded category, with existing fallback for older snapshots; revenue determines percentage share.
- Low Stock: conceptually available stock equals on-hand minus reserved. In this system, stored product/variant stock is already reduced when orders reserve inventory, so the existing Inventory helper reads that net available value; subtracting reserved orders again would double-count the deduction. Only positive available quantities at or below the configured threshold qualify; out-of-stock rows are excluded from this card. The shortcut uses the existing Inventory implementation in Products: `/admin-products/?inventory_status=low_stock`; it activates the current Low Stock filter.
- Bookings: creation date in Asia/Manila; current pending, approved, completed, rejected/cancelled mapping unchanged. Other facility usage analytics keep their reservation-date basis.

View All Orders and View All Bookings retain the existing `admin_orders_page` and `admin_bookings_page` routes. No booking workflow, calendar, approval, conflict detection, inventory deduction, payment recording or RBAC logic changed.

## 6. Database / Migration Impact

No schema change, migration or live database mutation. The new Operations data adds one bounded read query, and the initial Super Admin page reuses it rather than repeating the query. Dashboard tests confirm query count does not grow with order count and remains within the 21-query budget. Test records exist only in the isolated Django test database.

## 7. Tests Performed

Passed **113 Django tests** across dashboard bookings, global periods, marketplace summaries, low stock, Sales Overview and reports. Coverage includes all date presets/custom ranges, zero data, previous comparisons, timezone boundaries, exact stacked totals, independent groupings, Top 5 quantity/revenue ordering, parent variants, category revenue, available stock/thresholds, newest-first separate-status Operations snapshots and server-side permissions. The selected grouping test was rerun once to regenerate final real browser fixtures with both selectors supplied.

Passed JavaScript syntax checks, CSS parsing, the two DOM regression suites, and **11 Chrome render cases**: nine Booking Overview cases (desktop/laptop/mobile, weekly/monthly, empty/loading/error/no chart library) plus complete-dashboard desktop/mobile. Checked no page overflow, full-width Booking Overview, real totals, shared stack, three grouping options, removed caution/tables, moved Operations cards and hidden-but-scrollable table regions. Sales tooltip and keyboard values and Recent Orders failure/recovery were also checked. Desktop and mobile screenshots were visually inspected.

Evidence is in `scratch/dashboard-global-review/analytics-operations-django-tests.log`, `booking-overview-*.dom.html`, `palette-desktop.dom.html`, `palette-mobile.dom.html` and the matching PNGs. Preview values come from isolated test records.

Manual testing:

1. Press Ctrl+F5 on the Super Admin dashboard. Confirm Analytics, then Operations, then Facilities Analytics. Category Sales should be in Analytics; Low Stock and Recent Orders should be in Operations.
2. Keep Last 30 Days selected; choose Weekly for Sales and Monthly for Booking Trend. Each chart should group differently while keeping the same date range. Reload and check both selections remain.
3. Change the global range to Today or a custom range. Check both analytics charts' totals/dates update and the two groupings remain selected. Hover a booking bar and verify total equals its four status counts.
4. Pick an empty analytics period. Keep the zero baselines and exact empty messages; no chart-data toggle/table or booking availability caution should appear.
5. Check Recent Orders against Orders. Pending/Completed and Unpaid/Paid must appear in different columns. Quantity and amounts must match the actual transaction. Click View All to use the existing module.
6. Click Low Stock View All. The current Inventory/Products page should open with Low Stock selected. Current available inventory must remain on-hand minus reserved, with at most five dashboard rows.
7. Tab to either chart and use arrows/Home/End to inspect exact values. Narrow the browser and scroll the Recent Orders table horizontally if needed; the page should not overflow, and the internal scrollbar remains hidden.
8. Block the dashboard API request in developer tools and change a filter. Confirm error/Retry rather than false zeros or stale Recent Orders rows. Unblock and Retry should restore actual data.

## 8. Remaining Limitations

- Verified in Chrome/DOM tests; Firefox, Safari, physical touch devices and screen-reader software were not separately tested.
- Recent Orders represents the model's sellable-product transaction records, not a newly invented multi-item cart/order aggregation. It is a six-row snapshot across all dates.
- Seven-column Recent Orders tables require internal horizontal scrolling on small screens. Native scrolling and keyboard focus remain; hidden tracks/thumbs follow your prior preference.
- The shared Sales Overview partial retains its visible data table for non-Super-Admin domain dashboards, outside this request's scope.
- Rejected and Cancelled remain one booking segment. The existing Bookings page has no combined filter, so that KPI remains informational. View All does not carry the analytics creation-date range.
- Existing Sales and Booking weekly bucket conventions differ as described above; their selected overall range and totals remain consistent.

---

# Upcoming Reservations Single-Row Layout & Scrollbar Removal (October 31, 2026)

## 1. Problem & Root Cause
On the Super Admin Dashboard (`super_admin_dashboard.html` / `executive_dashboard.html`), the **Upcoming Reservations** card (`#upcomingReservationsCard` inside `.executive-facilities .facilities-operations-grid`) exhibited two issues:
1. **Unwanted Scrollbar**: `.facilities-table-scroll` had `overflow-x: auto;` with `min-width: 520px;` on the table. In CSS standards, setting `overflow-x: auto` automatically calculates `overflow-y` to `auto`. When combined with flex/grid containers, a native vertical scrollbar with arrows rendered along the right edge of the card, even for single or few rows.
2. **Multi-line Wrapping ("Straight One Row" failure)**: In `admin_facilities_overview.css`, table cells used `overflow-wrap: anywhere;` and lacked column widths. This caused long booking numbers such as `BK-2026-2786ED550F1C4A57` to wrap across 3 lines (`BK-2026-` / `2786ED550F1C4` / `A57`) and date/time strings like `Nov 06, 2026 · 7:00 AM – 5:00 PM` to break across 2 lines.

## 2. Changes Made
1. **Markup (`backend/templates/dashboard/partials/upcoming_reservations.html`)**:
   - Added a dedicated `<colgroup>` defining 5 column classes: `.upcoming-col-id`, `.upcoming-col-facility`, `.upcoming-col-client`, `.upcoming-col-when`, and `.upcoming-col-status`.
   - Added `title` attributes on the booking link and data cells to provide accessible, native hover tooltips when text is truncated.
2. **CSS Foundations (`backend/static/components/css/admin_facilities_overview.css`)**:
   - Replaced `overflow-x: auto;` on `.facilities-table-scroll` with `overflow: hidden; max-width: 100%; scrollbar-width: none;` and `::-webkit-scrollbar { display: none; width: 0; height: 0; }`.
   - Changed `.facilities-reservations-table` from `min-width: 520px;` to `min-width: 0; width: 100%; table-layout: fixed; border-collapse: collapse;`.
   - Replaced `overflow-wrap: anywhere;` with `white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: middle !important;` on all table headers and cells.
   - Assigned proportional column widths ($25\%$, $20\%$, $17\%$, $26\%$, $12\%$).
   - Centered column 5 (Status) and styled `.upcoming-reservation-status` with institutional neutral styling (`#1A1851` Navy text, `#F7F8FC` surface, `#E8EAF0` border).
3. **Executive Scope Refinement (`backend/static/components/css/admin_executive_refinement.css`)**:
   - Enforced `#upcomingReservationsCard { height: auto; min-height: 0; overflow: visible; }`.
   - Applied specific `.dashboard-executive #upcomingReservationsCard` rules ensuring priority over global table defaults.
4. **Dynamic JavaScript Updates (`backend/static/components/js/admin_upcoming_reservations.js`)**:
   - Updated DOM generation in `render()` so dynamically fetched reservations via API/date-filter include `title` tooltips and wrap `status_label` in `<span class="upcoming-reservation-status">`.
5. **Cache Invalidation (`backend/templates/dashboard/pages/admin_dashboard.html`)**:
   - Bumped CSS query version strings to `?v=20261031-upcoming-reservations-one-row`.

## 3. Data Flow & Verification Exercise
- **Data Flow**: `upcoming_reservations()` helper in `dashboard_bookings.py` queries future approved bookings $\rightarrow$ passed into context as `facility_analytics.upcoming_reservations` $\rightarrow$ rendered server-side via `upcoming_reservations.html` $\rightarrow$ dynamic date updates delivered via `campushub:dashboard-data` event $\rightarrow$ handled in `admin_upcoming_reservations.js`.
- **Safe Practice Exercise**:
  1. Navigate to `/admin-dashboard/`.
  2. Inspect the **Upcoming Reservations** card.
  3. Verify that all cells (`Booking No.`, `Facility`, `Client`, `Date / Time`, `Status`) fit horizontally on a single unbroken row.
  4. Confirm that no scrollbar (horizontal or vertical) appears on the table container.
  5. Hover over a long booking code to verify that the native browser tooltip displays the complete ID.

---

# Super Admin Registration Trend: "View chart data" Removal (October 31, 2026)

## 1. Problem & Root Cause
In the Super Admin Dashboard (`super_admin_dashboard.html`), the **User Registration Trend** card within **Users Overview** contained an expandable disclosure widget `<details><summary>View chart data</summary>...</details>`.
Consistent with previous decisions on the executive dashboard (e.g., in Booking Overview and Marketplace Sales where `<details><summary>View chart data</summary>` was removed to eliminate redundant visual clutter), the user requested that "View chart data" be removed from the Super Admin registration trend.

## 2. Changes Made
1. **Markup (`backend/templates/dashboard/partials/super_users_overview.html`)**:
   - Replaced `<details><summary>View chart data</summary>...</details>` with `<div class="visually-hidden"><table class="users-data-table" id="userRegistrationData">...</table></div>`.
   - The interactive disclosure toggle (`<summary>View chart data</summary>`) is completely eliminated from the visual UI.
   - Screen readers and assistive tools continue to have access to the tabular data structure (`id="userRegistrationData"`), preserving accessibility and `aria-controls="userRegistrationTrendChart userRegistrationData"`.
   - Simplified the canvas `aria-label` to omit `"Exact values follow in the chart data table."`.
2. **Client-side Scripting (`backend/static/components/js/admin_dashboard_executive.js`)**:
   - Updated dynamic `aria-label` formatting on `#userRegistrationTrendChart` to omit `Exact values follow in the chart data table.`.
   - Maintained DOM updates for `data-user-trend-rows`, `data-user-trend-date-column`, `data-user-trend-column`, and `data-user-trend-caption`.
3. **Automated Testing (`backend/core/modules/reports/test_dashboard_executive.py`)**:
   - Added `self.assertNotContains(page, 'View chart data')` to `test_executive_dashboard_populated_and_empty_views()`.
4. **Cache Invalidation (`backend/templates/dashboard/pages/admin_dashboard.html`)**:
   - Bumped `admin_dashboard_executive.js` version to `?v=20261031-remove-user-trend-view-chart-data`.

## 3. Data Flow & Verification
- **Data Flow**: Executive dashboard API / SSR passes `executive.users.trend` $\rightarrow$ rendered in `super_users_overview.html` $\rightarrow$ Chart.js renders the trend line chart $\rightarrow$ background tabular data remains available to screen readers via `.visually-hidden`.
- **Verification**:
  1. Navigate to `/admin-dashboard/`.
  2. Scroll to the **Users Overview** section and locate the **User Registration Trend** card.
  3. Verify that the line chart renders cleanly without any "View chart data" dropdown or button beneath it.
  4. Change the grouping (`Daily`, `Weekly`, `Monthly`) and verify the chart updates smoothly with zero JavaScript console errors.


