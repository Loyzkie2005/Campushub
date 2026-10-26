# Super Admin Facilities Overview implementation

## Current update — October 22, 2026

This report supersedes the historical Booking Overview/sample-mode notes below **for the Super Admin dashboard**. This update adds no sample records or sample-mode controls. Detailed Facilities Analytics and Facility Admin pages keep their existing presentations and workflows.

### 1. Cause / Reason

The executive section previously placed four status cards above a full-width stacked chart, then showed separate ranked and upcoming lists. The requested section needs three compact summary cards, equal chart columns, an upcoming table, and a current attention list.

Confirmed accounting limitation: `modules/facilities/revenue.py`, `valid_facility_payments` / `facility_revenue_summary`, sums positive paid collections on approved/completed bookings. Its existing query does not separate physical bookings from service resources. `api.models.FacilityPayment` has paid/unpaid/failed statuses and receipt information, but no structured net-refund amount. Deposit decisions also appear in workflow inspection metadata. This update therefore uses the explicitly allowed **Pending Bookings** fallback rather than introducing a new interpretation of collected/net facility revenue. Existing accounting calculations are unchanged.

### 2. Exact Files Changed

Paths are relative to the repository root. Line numbers identify the current code anchor, not the entire change range.

| File | Line / nearby anchor | Change and reason |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_periods.py` | 195, `physical_maintenance`; 299, `executive['facility_attention']` | Adds physical-only maintenance/unavailable columns to the existing facility aggregate; exposes current attention counts using that result and the existing pending-request totals. No additional queries for facility attention. |
| `backend/core/modules/reports/dashboard_bookings.py` | 51, `admin_booking_details_page` | Adds a server-generated `url` to each of the existing five upcoming rows. Selection, ordering, status, date and limit rules stay unchanged. |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 32, `super_facilities_overview.html` | Replaces the old executive Facilities block with one scoped presentation include; the later operations update places bundles before it. |
| `backend/templates/dashboard/partials/super_facilities_overview.html` | 1, `executive-facilities` | New section layout: header/subtitle/Analytics action, three summary cards, chart row, upcoming/attention row. Reuses existing data and partials. |
| `backend/templates/dashboard/partials/most_booked_facilities.html` | 2, `executive_mode`; 5, `data-facility-ranking-chart` | Adds an executive-only vertical chart and JSON seed; retains the existing ranked list for assistive technology and chart failure. Nonexecutive list markup remains. |
| `backend/templates/dashboard/partials/upcoming_reservations.html` | 6, `executive_mode` | Adds an executive-only table with booking link, facility, schedule and status; retains the original list in other contexts. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 25, `admin_facilities_overview.css`; 614, renderer scripts | Loads scoped CSS and versions facility scripts with `20261022-facilities`; the shared executive script now uses `20261022-audit`. |
| `backend/static/components/css/admin_facilities_overview.css` | 1, `Super Admin only` | Scoped navy/gold/white surfaces, existing Inter inheritance, compact cards, responsive grids, table scrolling and visible focus. |
| `backend/static/components/js/admin_booking_overview.js` | 19, `displayedSeries`; 92, `textFallback` | Uses a single navy total-request line in executive mode, retains the original status-series branch elsewhere, and exposes readable text when Chart.js fails. Summary/trend errors leave the independent ranking visible. |
| `backend/static/components/js/admin_most_booked_facilities.js` | 20, `draw(rows)` | Draws vertical bars from the existing top-five ranking, with full-name tooltips, keyboard inspection and the original list fallback. Reuses existing dashboard events and Retry. |
| `backend/static/components/js/admin_upcoming_reservations.js` | 25, `list.tagName === 'TBODY'` | Projects the same upcoming rows into table cells; validates local booking URLs and preserves the current tab token. Other contexts keep list rendering. |
| `backend/static/components/js/admin_dashboard_executive.js` | 18, `const attention` | Validates and refreshes three current counts; shows a dash/error on failed refresh instead of a false all-clear. Services and audit preview have their own renderers; see [Services](dashboard-services-overview.md) and [final operations](dashboard-system-status-design.md). |
| `backend/core/modules/reports/test_dashboard_executive.py` | 75, `test_facilities_attention...`; 100, `test_facilities_layout...` | Tests service/archive/schedule exclusions, period versus current queues, layout, real booking-detail destinations and optional isolated preview fixtures. |
| `backend/core/modules/reports/test_most_booked_facilities.py` | 133, `Most-Booked Facilities` | Updates the executive heading assertion to the requested wording. Ranking rules/tests remain. |
| `backend/core/modules/reports/test_upcoming_reservations.py` | 78, `admin_booking_details_page` | Updates the exact serialized row expectation for the new additive URL field. |
| `CAMPUSHUB_CONTEXT.md` | 7, latest Facilities Overview note | Preserves the accepted scope and verification for future work. |
| `docs/booking-overview-implementation.md` | 3, `Current update` | This current implementation/learning report; earlier reports are explicitly historical. |
| `scratch/facilities-overview-review/verify_renderers.cjs` | 1, `DOM integration test` | Local verification harness using isolated Django fixtures and the already-installed scratch jsdom dependency; not an application dependency or production data seeder. |

### 3. Changes Made / Expected UI

- **Facilities Overview** now has the requested subtitle and **View Facility Analytics** action.
- **Booking Summary** shows **Bookings in Selected Period**, **Approved Bookings**, and **Pending Bookings**. The first label makes its reporting-period basis explicit beside System Overview.
- **Booking Trend** is a line chart of submitted requests. Daily/Weekly/Monthly still uses the existing chart-only request path.
- **Most-Booked Facilities** is a vertical bar chart of up to five actual facilities, from the existing ranking query.
- **Upcoming Reservations** lists at most five actual approved reservations with working detail links. Approved is not relabeled as paid/confirmed.
- **Facility Attention** lists current pending booking requests, active physical facilities under maintenance, and active physical facilities temporarily unavailable. Counts of zero are genuine counts, not an inferred availability guarantee.
- Charts and operations stack on small screens; three summary columns start at 600px and paired charts/operations at 1100px. The four-column table scrolls inside its own region when narrow.
- Missing Chart.js reveals text/ranked-list alternatives. A failed grouping request keeps the independent ranking displayed. Full-refresh errors replace attention counts with dashes and show retry guidance.

### 4. How It Works / Inputs, Outputs and Data Flow

1. `build_dashboard_data(params)` resolves the existing reporting period and loads the existing aggregate queries. Two extra `Count` expressions use `~service_resources_q()` and `is_archived=False`; they add columns, not queries.
2. `executive_overview(period, metadata)` still calls `build_booking_overview(..., records=physical)`. Its output provides `total`, `approved`, `pending`, `trend`, `grouping`, comparison and navigation values. No second booking counter or chart API is introduced.
3. `most_booked_facilities(period)` still produces `{name, bookings, rank, ...}` rows from approved/completed bookings by scheduled usage date. `draw(rows)` maps names to the x-axis and actual booking counts to the y-axis.
4. `upcoming_reservations()` keeps its current future-approved selection and five-row limit. Django `reverse('admin_booking_details_page', booking_id=...)` adds a URL. The renderer creates text cells and a same-origin link, preserving per-tab admin authentication.
5. Both initial HTML and the protected dashboard JSON include `executive.facility_attention`. The existing full-refresh event updates that list; changing only chart grouping does not change current attention or upcoming snapshots.

Date bases are intentionally explicit: summary/trend use **request submission date**; ranking uses **scheduled usage date**, including existing overlapping-stay rules; upcoming and attention are **current snapshots** across dates. Therefore these values need not match one another.

Annotated example from the real implementation:

```python
physical_maintenance=Count(
    "pk",
    filter=~service_resources_q()  # Existing classifier excludes service resources.
        & Q(is_archived=False, availability_status=Facility.STATUS_MAINTENANCE),
)
```

The input is the existing Facility table; the output is one aggregate count. It does not inspect or modify booking time slots. Food Analysis, training/assessment and lease resources are excluded through the shared type/mode predicate, without duplicating its classification rules.

### 5. Backend / API Behavior

The same protected dashboard endpoint, date parameters, chart-grouping event, Django models and permissions remain. The only response additions are `executive.facility_attention` and `url` on existing upcoming rows. No public endpoint or new availability controller was added.

Existing Analytics URLs retain the selected dates and `module=facilities`. Booking/status actions use the existing booking page/filter; upcoming links open the exact existing detail route. Facility attention links use the existing facility status filter. Status-list destinations retain their established all-date behavior; no unsupported date filtering was invented.

Official approval, job-order, payment, deposit, inspection, reservation conflict and calendar code is unchanged. The existing legacy summary policy for unassigned booking requests is also unchanged; ranking/upcoming still require a linked facility.

### 6. Database / Migration Impact

No models, migrations, credentials, environment settings, SSH tunnels or deployment files changed. Application records were not inserted or updated. Automated fixtures are created only inside Django's isolated test database. Optional HTML/JSON files under `scratch/facilities-overview-review/` contain that test output, not production records.

### 7. Tests Performed / Troubleshooting

- **116 Django tests passed** across executive dashboard, booking trends/grouping, most-booked ranking, upcoming reservations, dashboard periods/query bounds, facility revenue, Marketplace Overview and KPI cards. See `scratch/facilities-overview-tests-final.log`.
- After separating the trend error region from the ranking, the focused layout/link/Analytics fixture test was rerun and passed; see `scratch/facilities-overview-fixtures.log`.
- **9/9 DOM integration scenarios passed**: actual data/chart types, booking links/tab token, keyboard tooltips, grouping requests, isolated grouping failure/retry, full outage, empty-state recovery, populated refresh without duplicate charts, and missing Chart.js fallback. See `scratch/facilities-overview-dom-final.log`.
- `manage.py check`: no issues. `makemigrations --check --dry-run`: no changes detected. Four modified production JavaScript files passed `node --check`.
- Browser automation inventory returned no available browser. Screenshots, actual canvas rendering, visual responsive layout and measured accessibility contrast are **not verified** by the DOM harness.

From the project root, repeat the Django checks safely:

```powershell
cd backend/core
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_executive modules.reports.test_dashboard_bookings modules.reports.test_most_booked_facilities modules.reports.test_upcoming_reservations modules.reports.test_dashboard_periods modules.reports.test_facility_revenue modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_kpi_cards --keepdb --noinput
```

To regenerate DOM-test fixtures, set `FACILITIES_REVIEW_DIR` to the absolute `scratch/facilities-overview-review` directory before running `test_facilities_layout_summary_charts_and_booking_links`, then run `node scratch/facilities-overview-review/verify_renderers.cjs` from the project root. The harness needs the existing `scratch/bundle-qa/node_modules/jsdom`; it is not installed into the application.

If changes do not appear, use Ctrl+F5 and check that the dashboard loads `admin_facilities_overview.css?v=20261022-facilities` and the matching script versions. A blank ranking with a populated submission trend can be correct: their date bases and status requirements differ. A grouping error should show Retry in the trend card while leaving ranking visible; full-refresh errors affect all cards. Never replace those errors with fabricated zero counts.

Safe learning exercise: in browser DevTools, temporarily change only `.facilities-chart-grid`'s `gap` from `16px` to `20px`. Inspect desktop and narrow widths, then change it back. Verify that card spacing changes, the table stays inside its scroll region, grouping still works, and the database counts remain unchanged. This needs no booking creation or payment action.

### 8. Remaining Limitations

The third card intentionally remains Pending Bookings until a separately agreed, reliable physical-facility net-revenue policy exists. Request totals use current statuses, not a historical status-change timeline. Current attention is a work queue, not a live slot-availability or conflict calculation. Empty data stays empty. Visual browser QA remains outstanding because no browser surface was available; no deployment or APK build was part of this web-only update.

---

## Historical Booking Overview notes

Update 2026-10-07: the later explicit sample request connects this card to Sales Overview's existing Show sample toggle. `sales_sample_data.html:179` supplies seven daily status vectors. `admin_booking_overview.js:151`, `sampleForGrouping(grouping)`, validates that input and returns the existing overview shape: 42 total, Pending 6 / Approved 18 / Completed 14 / Rejected-Cancelled 4, plus daily/weekly/monthly bars. `clearSample` at line 145 restores the saved real object. A capture-phase grouping listener handles preview rows locally, avoiding a real API request; global dates/Refresh clear previews. `booking_overview.html:3` labels the preview, and booking links are disabled during it. Backend request/date/status logic and database are unchanged. The [latest Facility Revenue guide update](facility-revenue.md) lists every changed file/current line, functions/data flow, confirmed causes, actual tests, debugging and limits. Verification: 42 Django checks, combined preview DOM checks and two actual Chrome sample layouts passed. Safe practice: change only the preview's `previous_total` to 42, confirm the comparison says No change with the same chart/KPI totals, then restore 35 and run the preview harness. Earlier implementation notes below describe real mode/history.

Update 2026-10-06: Daily/Weekly/Monthly now uses a Booking Overview-only request/render path. The existing global filter still sets its dates. Grouping failures and Retry stay local to Booking Overview; Most Booked Facilities and other cards retain their rows and values. See [Most Booked Facilities](most-booked-facilities.md) for the current filter code, inputs/outputs, tests and learning exercise. The older global-Retry limitation below is historical.

Historical first version. The current full-width KPI cards, stacked chart, removed visible chart-data table and caution are documented in [Booking Overview stacked KPI update](booking-overview-stacked-kpis.md). Follow that newer guide for the current UI.

## 1. Cause / Reason

The original card displayed a small status legend and a stacked chart based on reservation dates. It lacked an explicit total, booking navigation, pending-review context, and an individual API error state. The user's attached Booking Overview request calls for an actionable dashboard summary of actual booking requests, following the global date filter.

The new Super Admin overview counts request creation dates, matching the existing Total Bookings KPI. This is distinct from reserved-time usage, utilization, upcoming reservations, facility payment revenue, or facility availability.

## 2. Exact Files Changed

Current line numbers can move; use the nearby anchor to find the change.

| Folder / File | Line | Nearby code anchor | Added / changed / removed |
| --- | --- | --- | --- |
| `backend/core/modules/reports/dashboard_bookings.py` | 11 | `build_booking_overview` | Added presentation data, one grouped request trend query, real zero buckets, status links and automatic grouping. |
| `backend/core/modules/reports/dashboard_periods.py` | 169 | `bookings = Booking.objects.aggregate` | Extended the existing KPI query with period-specific status counts; no separate repeated total query. |
| Same file | 251 | `booking_overview=build_booking_overview` | Replaced the old reservation-status alias with the request-based overview. |
| `backend/templates/dashboard/partials/booking_overview.html` | 1 | `data-booking-overview` | Added the Super Admin card: total, comparison, statuses, pending note, chart/data table, empty/loading/error states, Retry and View All. |
| `backend/static/components/css/admin_booking_overview.css` | 1 | `Scoped to the Super Admin Booking Overview` | Added flat styling, a compact two-column status layout, 150px chart, focus outlines and loading skeleton. |
| `backend/static/components/js/admin_booking_overview.js` | 20 | `render(overview)` | Added safe text rendering, chart creation/update, zero baseline, validation, status links, authentication-token preservation and chart-library fallback. |
| `backend/static/components/js/admin_dashboard.js` | 236 | `facilityBookingCanvas && !document.querySelector` | Keeps the old stacked chart for legacy dashboards; avoids creating a duplicate chart on the new Super Admin card. |
| `backend/static/components/js/admin_dashboard_filter.js` | 326 | `campushub:dashboard-loading` | Announces loading to the new card, announces errors at line 372 and connects its Retry button at line 417 to the existing global loader. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 20 | `admin_booking_overview.css` | Loads the new scoped stylesheet. At line 280, includes the new card only for the global dashboard. At lines 560–563, loads the new script and refreshes changed script versions. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 97 | `option value="approved"` | Makes the existing Approved query parameter select the status control. The same fix is at line 100 for Completed. Pending already worked. |
| `backend/core/modules/reports/test_dashboard_bookings.py` | 22 | `DashboardBookingOverviewTests` | Added nine Booking Overview tests using the existing isolated Django fixtures. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 148 | `booking_overview` assertions | Checks creation-based overview counts separately from unchanged reservation-based totals. Lines 273 and 424 update the bounded query budget and page-wide comparison count for the added query/UI/JSON. |
| `scratch/dashboard-global-review/check-booking-overview.cjs` | 1 | `Real server-rendered test markup` | Added interaction checks for refresh, authenticated links, failure, Retry, loading, missing payloads and chart fallback. |
| `scratch/dashboard-global-review/prepare-booking-visual.cjs` | 1 | Actual rendered fixture loader | Added isolated desktop/mobile/empty/loading/error/chart-failure previews and browser measurements. |
| `scratch/dashboard-global-review/render-booking.ps1` | 1 | `$reviewDirectory` | Runs six Chrome review cases. |
| `scratch/dashboard-global-review/verify-booking-visual.cjs` | 1 | Browser assertions | Checks responsive fit, counts, baseline chart, pending context and honest states. |
| `scratch/dashboard-global-review/check-controls.cjs` | 11 | `scriptNames` | Includes the new script in global filter regression checks and supports chart resizing in the stub. |
| `scratch/dashboard-global-review/prepare-palette-visual.cjs` | 18 | Stylesheet list | Includes the new card's CSS/script and checks its links in the full-dashboard preview. |
| `scratch/dashboard-global-review/verify-palette-visual.cjs` | 30 | Booking Overview legend comment | Updates the palette check to reflect the new single-series chart; the separate facility availability legend remains intact. |
| `CAMPUSHUB_CONTEXT.md` | 17 | `Current Super Admin Booking Overview` | Saves the accepted behavior for future development. |
| `docs/booking-overview-implementation.md` | 1 | This report | Adds the learning guide and manual test steps. |

Generated HTML/JSON/DOM/log/PNG files in `scratch/dashboard-global-review` are local verification artifacts. Preview bookings are isolated test records, never inserted into the live marketplace/facility database.

## 3. Changes Made / UI Behavior

- Replaced the old Super Admin status legend and stacked chart with an explicit Total Bookings value, previous-period comparison, four compact status rows, and a single navy bar series for total request activity.
- Pending uses a small gold marker when its count is positive, with the note “Pending requests may need review.”
- Status text and counts remain navy. The attachment's optional red/positive colors were not adopted because AGENTS.md and the accepted reduced palette require navy/gold/white.
- Kept one card, its existing position in Facilities Analytics, restrained spacing, flat surfaces and visible keyboard focus.
- Added an expandable chart-data table for screen-reader/keyboard access and when the chart library is unavailable.
- Kept the other Facilities Analytics cards and the legacy domain dashboard behavior.

## 4. How It Works / Model and Status Mapping

Reuses `api.models.Booking` (`campushub_booking`), its existing `created_at` timestamp, and its current `status` field. No new booking status names or model fields were invented.

| Display | Existing model value(s) |
| --- | --- |
| Pending | `Booking.STATUS_PENDING` → `pending` |
| Approved | `Booking.STATUS_APPROVED` → `approved` |
| Completed | `Booking.STATUS_COMPLETED` → `completed` |
| Rejected / Cancelled | `Booking.STATUS_REJECTED` + `Booking.STATUS_CANCELLED` |

There is no separate Under Review or Confirmed status in this model. The count represents each request's **current status**, for requests created within the selected period. It does not reconstruct what a status was on a historical date.

Request counts include records with future reservations, hostel dates or a missing/deleted facility association if their creation timestamp falls within the selected period. They are actual requests and remain part of the KPI total. Payment status is not a requirement for counting requests.

The existing KPI aggregate now also counts the four status groups in the same query. A single additional query groups creation timestamps by date, using database aggregation instead of loading booking instances. The helper then groups those day totals into chart buckets and fills missing dates with real zero counts. The full dashboard query count remains bounded and does not grow with record count.

### Date filter and trend grouping

The existing global period resolver handles Today, Last 7 Days, Last 30 Days, This Month, This Year and Custom Range. Default remains Last 30 Days. All overview counts and trend buckets use the same inclusive date range in Asia/Manila.

- Up to 31 days: daily buckets.
- 32–120 days: seven-day buckets starting at the selected range's start.
- Longer ranges: calendar-month buckets, clipped to the selected range.

Grouping is automatic for this card and is independent of Sales Overview's Daily/Weekly/Monthly control. The existing Total Bookings KPI supplies the same previous-period comparison rules, including Yesterday for Today, and safe zero-baseline handling. No hardcoded dates or invented growth percentages were added.

## 5. Backend / API Behavior

The existing protected global dashboard API now returns an expanded `facilities.booking_overview` object with:

`total`, `pending`, `approved`, `completed`, `rejected_cancelled`, `date_basis`, `start_date`, `end_date`, `grouping`, `statuses`, `trend`, `chart`, `comparison`, and `view_all_url`.

`cancelled` is retained as a combined-count compatibility alias for `rejected_cancelled`. Existing `facilities.status_totals` and `facilities.chart` remain based on reservation dates and are not repurposed. Utilization, most-booked facility, payment revenue, calendar/conflict logic and approval actions stay unchanged.

No new endpoint or duplicate Bookings page was added. Super Admin API access enforcement remains unchanged; unauthenticated requests return 401 and domain admins cannot use the global endpoint (403).

### Navigation

View All Bookings opens the existing `admin_bookings_page` route. Pending, Approved and Completed open the same page with `?status=pending`, `?status=approved` or `?status=completed`. The existing client-side booking table filter uses the selected control. Current tab authentication is preserved when links refresh.

The combined Rejected / Cancelled row is informational because the existing control accepts a single status, not a combined filter. Full management and approval/rejection stay on the Bookings page. Status links filter the full management list by status; they do not carry the dashboard's creation-date range.

### Empty, loading and error states

- Valid zero data: shows 0 counts, genuine zero buckets with axes/baseline, and “No bookings in selected period.”
- Loading: the existing global `aria-busy` state hides the figures and shows the card skeleton. Stored figures are not replaced with zero.
- Failed dashboard request: hides overview figures/chart and displays “Unable to load booking overview.” plus Retry.
- Retry: calls the existing global loader using its requested period. No separate competing fetch process was added.
- Missing/invalid overview payload: treated as an error rather than silently substituting zero.
- Chart library unavailable: preserves valid totals, statuses and chart-data table, and displays a chart-specific fallback message.

## 6. Database / Migration Impact

No migrations, schema changes, new statuses or live database writes. The implementation is read-only. Booking approval, rejection, conflict checking, payment tracking and facility availability rules were not changed. Tests use the existing isolated Django test database.

## 7. Tests Performed / Manual Steps

- **61 Django tests passed** across `test_dashboard_bookings`, `test_dashboard_periods`, and `modules.reports.tests`.
- The nine new overview tests cover the specified five-record example, rejected/cancelled mapping, creation-vs-reservation dates, orphan/hostel requests, all presets/custom ranges, real zero buckets, partial weekly/monthly buckets, Philippine midnight, comparisons, one grouped trend query, status navigation, permissions and actual page rendering.
- Two DOM interaction suites passed: the existing global-filter regression checks and the new Booking Overview checks for date refresh, failed API, Retry, loading, missing payloads, authentication links and chart fallback.
- Six Chrome card cases passed: populated desktop, 375px content width, empty, loading, error and unavailable chart library.
- Two full-dashboard Chrome cases passed: desktop/mobile with no page overflow or JavaScript errors and the accepted reduced palette preserved.
- JavaScript syntax checks, CSS parsing and targeted tracked-file whitespace checks passed. Desktop/mobile card screenshots were visually inspected.

Manual test:

1. Reload the Super Admin Dashboard and inspect Booking Overview in Facilities Analytics.
2. Change the global date range. Its total should agree with the top Total Bookings KPI, and chart counts should sum to the total.
3. For actual records created in a selected period with statuses Pending, Pending, Approved, Completed, Cancelled, expect Total 5; Pending 2; Approved 1; Completed 1; Rejected/Cancelled 1.
4. Select a period with no requests. Check the 0 counts and visible chart baseline/empty note.
5. Open View chart data. Check its counts against the bars. Tab to links and use Enter.
6. Click Pending, Approved or Completed. Check that the existing Bookings page opens with the correct status selected. View All should open the complete page.
7. With browser developer tools, block the existing dashboard API request and click Refresh. The card must show its error and Retry instead of visible zero figures. Unblock the request and click Retry.
8. Resize to a small screen and confirm labels stay inside the card. Check that the other facilities cards, Bookings page and Calendar still work.

## 8. Remaining Limitations

- Status counts describe current statuses for requests created in the range, not past status-transition history.
- The existing full Bookings page supports status filtering, but not this dashboard date-range handoff or a combined Rejected/Cancelled status link.
- Chart grouping is automatic; there is no separate Booking Overview grouping dropdown.
- A dashboard API failure uses the shared global refresh/Retry request, so Retry refreshes the other dashboard summaries too.
- Chrome was exercised; Firefox/Safari and physical touch hardware were not tested in this task. Screenshots use isolated test fixtures, not live booking totals.
