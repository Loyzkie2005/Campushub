# Facility Admin dashboard refinement

Updated October 27, 2026. This guide describes the dedicated Facility Admin dashboard at the existing `admin_dashboard_page` URL. The Super Admin dashboard and Flutter screens are separate and were not redesigned by this change.

## October 27, 2026 ? compact operational dashboard

This section describes the current implementation and supersedes the historical payment-card/layout notes below. The existing Facility Admin route uses the module template, not the similarly named legacy template under `backend/templates/dashboard/`.

### 1. Cause / reason

Inspection confirmed that `.fd-grid` used `align-items: stretch`, Schedule Overview was a long definition list, payment presentation occupied half a row, and activities used separate horizontal cards. Chart failures and zero data could leave a blank canvas. Grouping requests also discarded an explicit `booking_days` and the existing administrator-tab context, and Retry could retry the restored selection instead of the failed grouping.

| Before | After | Why |
| --- | --- | --- |
| Stretched grid cards and payment half-row | Intrinsic card heights; full-width Facility Status | Fit actual content without changing metrics |
| Long schedule list | Two-by-two metrics and existing Calendar action | Scan four actual operational counts together |
| Horizontal activity cards | Full-width vertical list with subtle dividers | Keep real references, actors and times readable |
| Blank zero/error chart | Compact message or recoverable error | Avoid implying zero bookings is a renderer failure |
| Narrow KPI labels overflow beside icons | Mobile value beside icon, label across card width | Keep two-column KPIs readable down to 320px |

### 2. Exact files changed

Paths are repository-relative; line anchors refer to this revision.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facilities_dashboard.html` | 30 `.fd-kpis`; 45 `.fd-schedule`; 65 `.fd-pending`; 77 `.fd-facilities`; 85 `.fd-activities` | Preserve four KPIs; rebuild schedule presentation; show booking IDs/actions; remove payment card; vertical real activity references and Manila times |
| `backend/core/modules/facilities/static/facilities/css/admin_facilities_dashboard.css` | 40 `.fd-grid`; 69 `.fd-schedule-grid`; 115 mobile KPI rules | Content-driven grid, compact schedule, local table scrolling, readable rows and mobile KPI alignment |
| `backend/core/modules/facilities/static/facilities/js/admin_facilities_dashboard.js` | 12 `announce`; 20 `draw`; 42 `refresh` | Hide empty/failed canvas, retain reporting/authentication context, retry failed grouping, no chart animation on frequent selection changes |
| `backend/core/modules/reports/dashboard_facilities.py` | 132 `activity_rows` | Read-only projection of validated references and authorized existing detail/calendar URLs |
| `backend/core/modules/reports/test_facility_admin_dashboard.py` | 128 workflow test; 165 activity test; 188 empty-state test | Retain calculation/payment tests and add presentation/link/fallback coverage |
| `docs/facility-admin-dashboard.md` | This section | Cause, implementation, verification, troubleshooting and practice |
| `CAMPUSHUB_CONTEXT.md` | Latest October 27 entry near line 3 | Final role-specific dashboard behavior |

### 3. Changes made

The row order is KPIs; Booking Trend and Schedule Overview; pending and upcoming bookings; full-width Facility Status; full-width Recent Activities. Wide screens retain the twelve-column grid with seven/five chart/schedule proportions. Existing 1200/900/600px breakpoints remain; schedule metrics switch from two columns to one at 520px. KPI cards align within each row; other cards keep independent heights.

Schedule Overview reuses `bookings_today`, `detected_conflicts`, `maintenance_count` and `unavailable_count`. Only maintenance/unavailable have accurate existing filtered facility destinations. Today/conflict metrics remain noninteractive. View Full Calendar uses Django's existing route and its existing schedule-or-booking-read permission gate. The conflict note describes the current next-30-day scope without promising availability. The facility status note still distinguishes operational readiness from free slots.

Pending requests retain Review Queue and Review actions. Upcoming rows add an explicit existing Booking Details action. Empty operational lists render ordinary viewport-width paragraphs outside scrolling tables, so a minimum-width empty table cannot push its message off a phone screen. Populated tables retain local horizontal scrolling and every field.

Payment Overview and its unused card CSS are removed only from this dashboard. `payment_stats`, the existing receipt projection, permissions and financial service remain available unchanged. No receipt/payment records are deleted.

### 4. How it works: functions and data flow

```text
Authenticated Facility Admin dashboard GET
  -> facility_admin_dashboard(request, user)
     -> existing physical-facility / booking / schedule / payment calculations
     -> latest six existing scoped audit records
     -> validate references against that same booking/facility scope
  -> existing module template and dedicated CSS
  -> saved chart JSON -> draw(data) -> existing Chart.js bar chart
Grouping change -> refresh() -> same authenticated GET -> same chart instance
```

`facility_admin_dashboard` accepts the existing request/user and returns the existing context dictionary. Its metric calculations, booking row projection, returned counts and payment calculations are byte-for-byte unchanged. Only activity display fields are enriched: real recorded reference, existing authorized URL and icon type. At most six referenced bookings are fetched together with their facility, avoiding per-row lookups. Deleted/unverified booking IDs never become invented detail links. Missing actor information says **Actor not recorded**; no administrator is invented. Timestamps use the stored instant displayed in `Asia/Manila`.

`draw(data)` accepts the existing labels/values arrays, checks lengths and nonnegative finite values, and reuses the chart. A zero total hides only the chart frame; a positive period retains legitimate zero-value dates. `announce(data)` updates the visible count, accessible label and empty message. `refresh()` preserves explicit `booking_days` and the existing `__at` context, sends the existing role-scoped AJAX GET, and retains AbortController/revision protection against stale responses. On failure it preserves the last successful chart and exposes Retry for the originally requested grouping. No new API or chart algorithm is introduced.

Example: a saved maintenance count of 2 displays **2 Under Maintenance** and links to the existing `?status=maintenance` filter. A zero conflict count still requires checking the requested slot in Calendar; it does not certify availability.

### 5. Backend / API behavior

The activity projection adds bounded read-only reference validation, not a new metric or permission. Existing dashboard AJAX response fields and route compatibility remain. Calendar, approval/cancellation, cashier, reporting, booking creation, document exports and availability validation are unchanged. Nine protected shared dashboard/navigation/permission/workflow files were fingerprinted before and after and remain identical. Super Admin and Marketplace Admin templates/styles are not modified.

### 6. Database / migration impact

No model, migration, working inventory, booking, payment or audit-record changes. Django verification creates and destroys disposable local PostgreSQL test databases. Browser fixtures are rendered by the real Django test client from isolated test records; unrelated session/notification scripts are omitted in that visual harness, and all requests are intercepted so it never sends requests to the working application.

### 7. Tests performed

- Targeted PostgreSQL dashboard/period/status suite: **56 passed** in 17.693s. Final empty-list rendering recheck: **3 passed** in 0.994s.
- Production chart JavaScript DOM checks: **27 passed**, including empty/positive/error states, actual totals, grouping, period/tab preservation, retry recovery, one reused renderer and integer ticks. Node syntax check passed.
- Chromium: **14 layouts passed** (populated and empty at 1920, 1536, 1366, 1024, 768, 390 and 320px). Verified section order, 4 KPI alignment, 2/1-column schedule metrics, content-driven sections, actual Chart.js initialization, compact empty charts, local table scrolling, existing Calendar href, visible keyboard focus, no page overflow, no runtime errors and no missing assets. Desktop/phone screenshots inspected.
- Initial broader run: **535 passed; 2 errors** among 537 tests. Both untouched Super Admin KPI tests lack unmanaged `campushub_booking` in their fresh test setup. This is a fixture/schema preparation issue, not an assertion failure in the changed dashboard. A guarded scratch runner reuses the existing dedicated dashboard fixture DDL only after confirming the disposable test database; it does not migrate the working database. Final guarded recheck: **536 passed; 1 failure** among 537 tests in **248.802s**. The remaining untouched `SystemOverviewCardsTests.test_card_order_real_destinations_and_no_render_time_mining` assertion at `test_dashboard_kpi_cards.py:40` expects Super Admin `marketplace-recommendation-counts`, removed by an earlier approved Super Admin change. Protected-file fingerprints confirm that dashboard was not changed here. The stale assertion is reported, not altered in this Facility Admin task.
- Explicit `manage.py check` passed with no issues; scoped Git whitespace check passed.
- Source-preservation checks confirm every existing dashboard metric/payment calculation and return projection is unchanged, along with the nine protected shared files.

Evidence: `scratch/facility-admin-refinement-20261027/` contains targeted logs, `dom-results.json`, `browser-results.json`, screenshots, `preservation-checks.json` and broader-run logs. These are ignored QA artifacts, not application assets or fake dashboard fallbacks.

### 8. Remaining limitations, troubleshooting and safe practice

- Browser checks use isolated Django-rendered fixtures and real CSS/Chart.js, not a live signed-in administrator session. Physical-device testing was not performed.
- No authorized scoped facility activity-history destination was confirmed; no artificial View All action was added. Events without stored references/actors retain honest fallbacks. Existing six-record limits remain.
- Calendar is the authoritative place to inspect actual slots and rules. Dashboard conflict detection still uses its existing horizon and algorithm.
- The upcoming KPI's existing approved-bookings link is broader than the upcoming time cohort. The Bookings `kpi=upcoming` filter also requires full payment, so substituting it would incorrectly hide unpaid approved reservations. That business rule was preserved.
- If styling is stale, verify the active module template loads the dedicated `?v=20261027-operations` assets. Do not edit the inactive legacy dashboard template or shared dashboard CSS to repair this role-specific layout.
- Safe exercise: change only `.fd-schedule-grid` gap from 10px to 12px, compare at 1366px and 390px, then restore 10px. Verify the four values and destination URLs do not change. Separately switch Daily/Weekly/Monthly and inspect the existing GET's `booking_grouping` and explicit `booking_days` in developer tools. Do not create bookings/payments merely to test spacing.

## Earlier implementation notes (historical)

### Latest correction: Add Reservation belongs in Bookings

1. **Cause / reason:** the user clarified that Add Reservation should be available in Bookings rather than on the Facility Admin dashboard. This supersedes the earlier dashboard-shortcut wording below.
2. **Exact files:** `backend/core/modules/facilities/templates/facilities/pages/admin_facilities_dashboard.html:25` (heading actions); `backend/core/modules/reports/test_facility_admin_dashboard.py:134` (workflow assertions); `scratch/facility-dashboard/verify_dom.js` (existing booking form checks); this guide and the project context note. The retained Bookings button is in `admin_bookings.html:95`.
3. **Changes made:** remove the dashboard Add Reservation shortcut. Keep Add Reservation in the Booking Requests header, the earlier removal of the Quick Actions box, and the existing dashboard schedule action.
4. **How it works:** normal `/admin-bookings/` entry shows the booking list; clicking its existing `bkOpenReservationBtn` calls the existing `admin_booking_forms.js` handler near line 106 and `show('bkReservationModal')`. The output is the same focused reservation dialog. No dashboard redirect or copied form is involved. Existing action-query support remains for compatibility but is no longer advertised on this dashboard.
5. **Backend / API behavior:** routes, authentication/permissions, reservation validation and save endpoints remain unchanged.
6. **Database / migration:** none. Tests use the existing isolated local test database; no live booking was created.
7. **Tests performed:** 20 existing Django dashboard/calendar tests passed, including dashboard shortcut absence and Bookings trigger presence; system checks were clean. Production-script DOM checks verified normal Bookings entry starts closed, the Bookings button opens the reservation dialog, and no POST is sent just by opening it. Existing query-entry, schedule, chart and calendar checks also passed.
8. **Remaining limits / safe practice:** live signed-in smoke testing remains pending. Refresh Dashboard and confirm Add Reservation is absent; choose Bookings in the sidebar, click Add Reservation, and cancel without saving. Check the existing booking permission if that button is missing. No app/server restart is needed.

### Latest correction: inline booking actions and direct dashboard entry

1. **Cause / reason:** the Bookings page displayed a separate Quick Actions heading and bordered container. The user requested their removal and direct reservation entry from Dashboard. Inspection confirmed the dashboard already uses the correct existing action URL; no broken backend route was established.
2. **Exact files:** `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html:14` (CSS cache version), `:88` (`bk-bookings-list-header`), `:94` (existing action buttons); `backend/static/components/css/admin_booking.css:1595` (`bk-side-actions`), `:1603` (responsive list header); this guide and `CAMPUSHUB_CONTEXT.md`. Scratch-only visual inspection: `scratch/facility-dashboard/inspect_booking_actions.js`.
3. **Changes made:** remove the Quick Actions heading/aside and move its existing permission-gated Add Reservation and Manage Facility Schedule buttons into the Booking Requests header. Remove the obsolete bookings-only aside styles. The header places actions on the right when space permits and wraps them below on narrow screens. CSS version is now `20261020-inline-booking-actions`.
4. **How it works:** keep the same unique `bkOpenReservationBtn` and `bkOpenUploadBtn` IDs, so existing event handlers continue working. `admin_booking_forms.js:106` listens for reservation button clicks and calls existing `show('bkReservationModal')`; its `dashboardAction` handling near line 350 reads the URL's `action` input and clicks the same permission-rendered button. Output is the existing focused dialog, not a second form or automatic submission. Example: `Dashboard Add Reservation -> /admin-bookings/?action=add-reservation -> existing button -> reservation dialog`. Schedule entry uses `action=upload-schedule` and the existing schedule form. Moving the triggers preserves this chain.
5. **Backend / API behavior:** existing Bookings route, permission checks, form validation, schedule workflow and save endpoints are unchanged. Normal entry to Bookings leaves dialogs closed. Users without the existing permission still do not receive the corresponding action button.
6. **Database / migration impact:** none. No model/migration change and no live data written. Verification uses existing isolated test fixtures only.
7. **Tests performed:** 20 existing dashboard/calendar tests passed and Django system checks were clean. Existing production-script DOM checks passed, including both action URLs opening their intended dialogs with zero POST writes. Headless browser inspection passed at 1536/1024/390px: no Quick Actions aside/title, both unique triggers inside the Booking Requests header, desktop inline alignment and no button overflow. Desktop/phone screenshots inspected. The visual preview deliberately disables application scripts; its booking table loading placeholder is not evidence of a production loading failure. Results: `scratch/facility-dashboard/inline-actions-tests.log`, `bookings-actions-results.json`, and `bookings-actions-{1536,1024,390}.png`.
8. **Remaining limits / safe exercise:** live signed-in smoke testing remains pending. Refresh Bookings, confirm the separate box is gone, then navigate to Dashboard and choose Add Reservation; the Bookings URL should include the action and the existing form should open. Close it without saving. Return to Bookings normally and open each header action once. On mobile verify buttons stack within the list header. If a button is absent, check its existing account permission rather than removing permission checks. No app/server restart is needed.

### Latest correction: restore the original sidebar colors

1. **Cause / reason:** the reference redesign introduced a dashboard-specific navy/white selected-sidebar override. The user requested the previous sidebar colors back.
2. **Exact files:** `backend/core/modules/facilities/static/facilities/css/admin_facilities_dashboard.css:19` (sidebar inheritance comment); `backend/core/modules/facilities/templates/facilities/pages/admin_facilities_dashboard.html:13` (stylesheet URL); this guide and the project context note.
3. **Change:** remove that selected-item override and update the stylesheet cache version to `20261020-sidebar-colors`.
4. **How it works:** the existing shared `.sidebar-item.active` rule in `backend/static/components/css/admin_layout.css:387` again supplies gold `#FCB315` behind navy `#1A1851` text/icons. No new function, input or output is introduced; the existing `active_page='dashboard'` template input still selects the same sidebar item. Example: Dashboard marked active -> shared CSS gold background/navy foreground.
5. **Backend / API:** existing links, roles, permissions, data and dashboard layout are preserved.
6. **Database / migration:** none; no records changed.
7. **Verification:** inspected the shared rule and removed override, checked the updated stylesheet URL and scoped diff whitespace. No runtime test was needed or run for this CSS-only correction; the earlier dashboard test results below refer to the full redesign.
8. **Limits / safe practice:** refresh the dashboard to load the new stylesheet. In browser developer tools, inspect the active Dashboard sidebar item and confirm its background comes from `admin_layout.css`, not a dashboard-specific rule. If stale, hard-refresh the browser. Do not change the shared palette to fix a local override. No app/server restart is required.

This correction supersedes the navy selected-sidebar styling described in the earlier redesign notes below.

The latest pass follows the user's **CampusHub Facility Admin Dashboard (1).png** reference. Only the active dashboard template, its scoped CSS, this guide, project context, and scratch layout verification were changed in this visual pass. The backend/helper/controller rows below document the earlier operational implementation, which this pass reuses unchanged.

## 1. Cause / reason

The latest request asks for the reference's more compact hierarchy: greeting and actions, four KPIs, trend beside schedule, paired booking tables, then facility status/payment/activity panels. The previous operational layout used full-width booking tables and a full-width payment panel; this visual pass changes their arrangement and styling while keeping their data and workflows.

Earlier operational fixes addressed booking links leading to the facility catalog, Weekly/Monthly selections drawing daily buckets, service resources in physical facility counts, missing OR checks, and missing facility-scoped activities. Those fixes remain in place.

Browser QA also confirmed that shared typography overrides defeated Poppins. On narrow screens, absolutely positioned screen-reader labels inside horizontally scrolling tables extended the document scroll area; positioning the table wrapper fixed that overflow. Long header titles now wrap safely as well.

## 2. Exact files changed

Paths below are relative to the project root. Line numbers refer to this implementation; nearby anchors remain useful as the project grows.

| File | Current line / anchor | What changed |
| --- | --- | --- |
| `backend/core/modules/reports/views.py` | 557 `_facilities_operational_dashboard_data`; 616 Facility Admin JSON response | Existing helper delegates to the focused read-only builder; AJAX adds grouping and period label while retaining its chart/total fields. Existing role routing and decorators remain. |
| `backend/core/modules/reports/dashboard_facilities.py` | 23 `_booking_row`; 38 `_conflict_count`; 62 `facility_admin_dashboard`; 119 payments; 127 activity query | New presentation/data builder replaces the old helper body, reusing existing classification, calendar, chart aggregation, receipt and status helpers. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facilities_dashboard.html` | 20 shared header; 23 greeting; 25 quick actions; 31 KPIs; 38 grid/permission class; 39 trend; 46 schedule; 51 pending; 57 upcoming; 63 facility status; 71 payments; 79 activities; 84 update time | Latest visual pass: reorders the actual sections to match the reference, retains context/IDs/workflows, links booking IDs and uses an honest mobile-safe receipt empty state. |
| `backend/core/modules/facilities/static/facilities/css/admin_facilities_dashboard.css` | 2 tokens; 12 Poppins scope; 18 header; 19 selected sidebar; 20 content; 30 KPIs; 40 grid; 55 table wrapper; 97 collections; 111/116/120 breakpoints; 141 reduced motion | Latest visual pass: scoped reference layout, compact typography, outline icons, navy selection, gold-tinted attention/collection details, responsive table containment and pointer feedback. |
| `backend/core/modules/facilities/static/facilities/js/admin_facilities_dashboard.js` | 1 existing controller; `draw`, `refresh` | Actual Chart.js bar chart, grouping refresh, loading/empty/error/retry feedback, request abort/revision guard, reduced-motion support and reuse of one chart instance. |
| `backend/static/components/js/admin_booking_forms.js` | 349 `dashboardAction` | Recognizes only `add-reservation` and `upload-schedule`, clicking existing permission-rendered form triggers. Opening a form does not submit it. |
| `backend/static/components/js/admin_facility_calendar.js` | 113 `requestedFacility` | Selects an existing matching facility option from a dashboard schedule link and invokes the existing calendar loader. Unknown IDs are ignored. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 206–207 controller references | Refreshes cache versions for the two changed existing controllers. Reservation/schedule forms were not duplicated. |
| `backend/core/modules/reports/test_facility_admin_dashboard.py` | 21 `FacilityAdminDashboardTests` | Regression cases using the existing unmanaged-table fixture setup; optional fixture-only HTML exports support browser QA. |
| `scratch/facility-dashboard/verify_browser.js` | 43 viewport loop; 49 layout assertions; permissionLayout/motion checks | Latest visual pass extends the existing fixture-only checker to six widths, new section arrangement, hidden-payments layout and reduced motion. The one-time scratch edit helper is `refine_layout.js`; it must not be rerun against the finished template. |
| `CAMPUSHUB_CONTEXT.md` | latest Facility Admin dashboard note | Saves the accepted scope, data rules, validation and limits. |
| `docs/facility-admin-dashboard.md` | this guide | Implementation report, data flow, troubleshooting and safe learning exercise. |

The similarly named legacy template under `backend/templates/dashboard/pages/` is not the template loaded by this role's route. It was left alone. No second dashboard route/controller was added.

## 3. Changes made

- The shared header reads Dashboard. The greeting uses the signed-in user's first name, falling back to "Welcome back!" when none is recorded. Existing header actions and branding stay in the shared include.
- Four physical-facility KPIs show value, label and helper text, with outlined icons and real existing destination links. Four columns on wide desktops, two on narrower screens. The maintenance KPI opens the facility list; it does not claim to apply an unsupported maintenance filter.
- Booking Trend and Schedule Overview form the first desktop row; Pending Booking Requests and Upcoming Reservations form the next. Pending rows remain oldest first, limited to six; Review Queue uses the existing pending filter and Review opens real booking details.
- Upcoming approved reservations show ID, facility, requester, date or stay and status. The booking ID itself opens existing details, avoiding a redundant Action column. Its management link opens the existing approved-filtered list, which may also include past approved bookings.
- Facility Status, Payment Overview and Recent Activities share the bottom desktop row. The collections total sits below the receipt list. No-receipt text is outside a wide table so it stays readable on phones. If existing permissions hide payments, the other two panels fill the row without a vacant payment area.
- Navy #1A1851, gold #FCB315 and neutral surfaces replace the reference's extra status colors. Poppins, restrained 10px panel corners, outlined icons, subtle borders and spacing provide the hierarchy; no decorative gradients, entry animations or sample runtime records were added. Pointer press feedback lasts 120ms, respects reduced motion and excludes keyboard-focused presses.
- At 1200px and below, KPIs use two columns and the large chart/booking sections stack. Below 900px all operational panels stack. Tables scroll within their own focusable regions; the document does not scroll sideways. The existing shared sidebar behavior and actual menu entries are retained.
- Existing Add Reservation and schedule editor workflows open from compact heading actions. The requested Upload Schedule label links to the current schedule editor with its existing attachment support.
- Actual facility records provide all names/types/statuses. The existing service classifier excludes Food Analysis, assessment and lease service records from physical facility statistics; it does not move or duplicate database records.

## 4. How it works: functions, inputs, outputs and data flow

### Existing entry point

`admin_dashboard_page(request)` keeps its existing role checks. Facility Admin delegates through `_facilities_operational_dashboard_data(request, user)` to `facility_admin_dashboard`. The builder reads current records and returns the same `facilities` template context, with additional grouping, activities and receipt visibility fields. Other admin roles retain their separate dashboards.

### Reference layout: template inputs and CSS output

The active template consumes the existing `user`, `perms`, `facilities` and `dashboard_updated_at` context. Django still escapes all displayed names. The CSS `.fd-grid` maps the actual sections to a twelve-column desktop grid; DOM order is also trend, schedule, pending, upcoming, facilities, payments, activities so keyboard/reading order follows the page. The template conditionally adds `.fd-grid-no-payments` from the same existing `can_view_payments` flag that hides the receipt panel.

```text
Existing Django context -> existing template values/permission checks
  user.first_name -> greeting (blank -> no invented name)
  facilities.pending_bookings -> KPI value -> existing ?status=pending route
  facilities.can_view_payments -> payment visibility + matching grid arrangement
  booking_chart JSON + unchanged canvas/select IDs -> existing draw()/refresh()
```

This keeps layout decisions in the template/CSS instead of adding another controller or API. The original Chart.js IDs, JSON script, Retry state and action URLs are preserved. The relative `.fd-table-wrap` still contains absolute screen-reader labels. A scoped font rule includes `.fd-content` itself as well as descendants because browser QA caught its inherited shared-layout font during this pass.

### Physical facilities and bookings

`service_resources_q()` is the existing shared classification predicate. Current operational counts exclude archived facilities, archived booking requests and schedule-block records. Inactive physical facilities remain physical records with their actual operational status. No product/marketplace data is used.

Historical chart requests and valid receipts still include archived physical facilities: archiving must not erase their recorded activity or collection history. Missing facility links and service requests do not become physical facility totals.

`_booking_row(booking)` receives an existing Booking with its facility, user, request metadata and payments prefetched. It returns display values and the real details URL. It uses `status_label`/`paid_summary`, so a fully settled approved reservation can retain the existing Reserved / Confirmed wording. Upcoming previews include approved future slots/stays, not already-started timed events. Missing dates/times show explicit missing-information text.

### Booking Trend

`booking_grouping` accepts `daily`, `weekly` or `monthly`; an invalid value falls back to daily. Defaults are the last 7 days, 84 days (12 weekly buckets), or 365 days respectively. Existing valid `booking_days` requests remain supported. The existing `build_booking_overview` groups actual request `created_at` dates, not facility-use dates, within the selected horizon. Zero buckets mean there were no recorded requests in that bucket; they are not fabricated activity.

Annotated example using actual records:

```text
GET /admin-dashboard/?booking_grouping=weekly
  -> existing Facility Admin role route
  -> physical Booking queryset, excluding schedule blocks
  -> build_booking_overview: count requests by submission date/week
  -> existing AJAX fields booking_chart.labels / booking_chart.values
  -> draw(): update the existing Chart.js bar chart
```

`refresh()` sends the normal authenticated GET with `X-Requested-With`. It aborts older requests and uses a revision guard so late responses cannot overwrite a newer selection. On failure it preserves the last loaded chart/selection and offers Retry. `draw()` validates array lengths and nonnegative finite values, creates only one chart instance, and announces the actual request count. No new API endpoint was introduced.

### Schedule Overview

The existing `calendar_events` projection expands stored academic, maintenance and other blocks, recurring dates and accommodation stays. `_conflict_count` compares occurrences on the same facility/date using the existing overlap counter; independent room units do not clash merely because they share a facility. The visible horizon is today plus the next 30 days. This is read-only detection, not a change to booking validation or approval rules. The dashboard shows Bookings Today, detected overlaps, maintenance/unavailable counts and an honest no-issues message.

### Receipts

`valid_facility_payments()` remains the source of valid positive paid collections on existing approved/completed bookings. The dashboard adds physical-resource/schedule-block scoping and requires a nonblank OR after trimming whitespace. Paid is the existing staff-recorded verification state; there is no new external financial verification service. Partial payments recorded as valid paid receipt entries count by their actual amount. Unpaid, failed, zero/negative, missing-link, service and missing-OR records are not displayed as verified collections. Existing cancelled/rejected booking exclusions are preserved through the shared revenue helper.

The total covers all qualifying recorded collections; the table shows the latest five. Financial visibility uses the existing record-payment/report/manage-booking permissions. Original financial records are never edited or deleted by this dashboard.

### Recent Activities and navigation

The existing `AccountActivity` table is filtered to Facilities/Facility Bookings and actual physical facility/booking IDs using JSON-text annotations and database subqueries. Six recent entries show recorded activity, actor and date; IPs, connection details and unrelated marketplace/service events are not exposed. No new audit storage or invented event fallback was added.

Quick actions carry `?action=add-reservation` or `?action=upload-schedule`. The existing forms script clicks a trigger only if that permission-rendered trigger exists. `View Schedule` carries a real facility ID; the existing calendar accepts it only when it matches an available selector option. Existing booking-list status filtering was already supported and was reused.

## 5. Backend / API behavior preserved

The original Django dashboard URL, login/role decorators, detail pages, booking approvals/rejections/cancellations, payment writes, calendar APIs, form validation, private documents and schedule save handlers remain. The chart JSON retains `booking_days`, `booking_chart`, `period_bookings_sum` and adds `booking_grouping`/`booking_period_label`. No marketplace logic was moved or copied. FastAPI and Flutter were not changed.

## 6. Database / migration impact

No model/schema changes and no migration required. No live records were written, classified, renamed or deleted. Tests use only `test_campushub_facility_dashboard_refine` on the configured local PostgreSQL host; the verification runner refuses a non-local host. Test data displayed in `scratch/` previews is isolated fixture data, not a dashboard fallback.

## 7. Tests performed

- Django system checks: no issues.
- **20 tests passed**: the new dedicated dashboard suite (including inherited role-isolation tests) plus the existing facilities calendar suite. Coverage includes physical/service and archive separation, pending/upcoming dates, actual daily/weekly/monthly aggregation, AJAX data, real block conflicts, operational status counts, paid/failed/unpaid/blank-OR exclusions, retained historical receipts, scoped activities, empty states, links and permissions.
- Production-script DOM checks passed: bar chart initialization, grouping request, failed refresh/retry, stale-response guard, no duplicate chart instance, both existing quick-action modals without POST writes, and facility-specific calendar loading.
- Latest full rendered-fixture browser checks passed at **1536, 1440, 1024, 768, 390 and 320px**: correct KPI columns, paired desktop rows, bottom-row alignment, real-route KPI links, unique IDs, payment-hidden grid arrangement, reduced-motion styling, actual Chart.js bar chart, Poppins, no document overflow and no browser runtime/console errors. Reference-size desktop and narrow-phone screenshots were inspected after the final refinements.
- Changed JavaScript files pass Node syntax checks; scoped diff whitespace check passes.

Commands from the project root (headless checks; do not start/install the app):

```powershell
.\backend\core\venv\Scripts\python.exe .\scratch\facility-dashboard\verify.py
node .\scratch\facility-dashboard\verify_dom.js
node .\scratch\facility-dashboard\verify_browser.js
```

The browser checker uses local copies of the exact Bootstrap 5.3.2 and Chart.js 4.4.1 assets already referenced by the application, and existing bundled Poppins fonts. These copies are scratch QA assets, not new application dependencies. The test runner can export fixture HTML for the two browser checks. Results: `scratch/facility-dashboard/django-tests.log`, `browser-results.json`, and `dashboard-{1536,1440,1024,768,390,320}.png`. The screenshots contain isolated test records, not sample data injected into the application.

## 8. Remaining limits and safe learning exercise

For a safe CSS practice change, temporarily change `.fd-content`'s `gap: 18px` to `20px`, refresh only the browser, and compare spacing between the KPI row and the chart row. It changes spacing, not data or chart queries. Restore 18px afterward. Verify at 1536px and 390px that cards still align and tables scroll inside their panels. If the new style appears stale, confirm the active module template loads `?v=20261020-reference-layout`; the similarly named legacy dashboard template is not used by this route.

- Live signed-in smoke testing remains pending. The app/server/phone/workers were not restarted.
- “Verified” means existing paid state plus an OR record; this does not introduce a new verification field or external payment check. Legacy payments missing an OR remain stored but are excluded from this dashboard's verified total.
- No new audit system was created. Historical maintenance/status changes without an existing linked audit event will not appear in Recent Activities.
- No Covered Court, Function Hall or Mock Hotel record is hardcoded or inserted. Missing/misconfigured database records must be managed through the existing Facilities/Services configuration. The dashboard displays the saved type/category rather than guessing it from a name.
- Conflict projection is limited to the stated next-30-day horizon; it does not replace the existing real-time reservation conflict validator. Long tables scroll inside their card on narrow screens.

Safe exercise: sign in as Facility Admin, open Dashboard, verify the four KPIs against the existing booking/facility lists, then click Review Queue and a Review link. Open each quick action and cancel it without saving. Switch Daily → Weekly → Monthly and compare the stated submission-date horizon. Open a facility's View Schedule link and confirm that facility is selected. Check the latest OR in the existing Payment tab, and narrow the browser to tablet width. If a chart request fails, use Retry and inspect the existing role-scoped dashboard GET before changing chart or payment rules. If a service appears among physical facilities, inspect its saved type/mode and the shared classifier; do not rename rows or add dashboard-only exceptions.
