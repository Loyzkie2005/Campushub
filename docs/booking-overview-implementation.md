# Super Admin Facilities Overview implementation

## Current: Booking Summary KPI cards only - November 11, 2026

### 1. Cause / reason

The three Super Admin summary cards had long labels, repeated descriptions, comparison text and no top-right icons. Their compact override used 11px labels, 22px values, 10px padding and 8px corners. The requested finish uses only Label + Value + Icon. Inspection also confirmed that removing the comparison paragraph without updating `render()` would cause a null-element error during initial rendering and AJAX refresh.

### 2. Exact files changed / current lines and anchors

| File / current line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/super_facilities_overview.html:11` | `booking-overview__metrics`: retain three cards and the original bindings/links; use Total Requests, Approved and Pending; remove the three paragraphs; add decorative calendar, calendar-check and clock SVGs. Total/clock reuse `booking_overview_icon.html`; calendar-check uses the same inline SVG pattern within this partial. |
| `backend/static/components/css/admin_booking_overview.css:370` | Super Admin `#bookingOverviewCard .booking-overview__metrics`: update the existing summary-only overrides to equal-height white cards, 14px padding, 1px `#DCE2EE` borders, 10px corners, 12px gaps, 12px semibold labels and 26px bold values in Montserrat/navy. Line 401 styles 32px icon containers; line 417 restores three equal columns when the booking container is at least 480px wide. |
| `backend/static/components/js/admin_booking_overview.js:105` | `const comparison` / `if (comparison)`: update comparison text only when that optional element exists. All numeric rendering and chart logic remain as before. |
| `backend/templates/dashboard/pages/admin_dashboard.html:20` | Booking CSS cache version becomes `20261111-booking-summary-kpis`; the corresponding booking script version changes at line 627. No header or page-layout markup changes. |
| `backend/core/modules/reports/tests/test_dashboard_executive.py:124` | `test_facilities_layout_summary_charts_and_booking_links`: update the existing expected labels to the requested three labels. |
| `docs/booking-overview-implementation.md:3` | This implementation, troubleshooting and learning report. Earlier entries describe historical changes. |

### 3. Changes made

The Total Requests card remains a non-interactive total. Approved/Pending retain their existing booking-status navigation. Each card places its icon at the top right and its value beneath the label. The icon background is `#E8EEFF`, border `#DAE3FA`, and stroke `#1A1851`. Values and labels are navy. No new metric, badge, subtitle, comparison indicator, dependency, shadow or gradient is added. Narrow containers stack the cards rather than squeeze the label/icon row; existing grid auto-rows keep heights equal.

Only summary selectors were changed in the booking stylesheet. `admin_executive_refinement.css` was inspected and left unchanged; the existing more-specific booking selectors own this refinement. Booking Trend, ranking, reservations, attention, other dashboard sections, header and sidebar keep their existing code and styling.

### 4. How it works / functions, inputs, outputs and data flow

The existing Django overview provider supplies actual selected-period counts. The template renders `overview.total`, `overview.approved` and `overview.pending` directly into the same `strong` elements. Initial JSON then enters `render(overview, chartOnly)` in `admin_booking_overview.js`; later global date/Refresh events enter the same function through `campushub:dashboard-data`. Status rows keep `data-booking-status`, so the existing loop updates each value and its real destination URL. Grouping-only events still use `chartOnly=true` and preserve summary values.

The only JavaScript change makes the removed paragraph optional:

```javascript
const comparison = card.querySelector('[data-booking-comparison]');
if (comparison) {
    // Existing comparison updates run only in templates that still display it.
}
```

Input: the existing validated overview response. Output: the same updated counts, navigation and chart, with comparison text updated only where its element exists. This keeps the shared controller compatible with other templates while allowing a minimal Super Admin summary. CSS uses the existing named `booking-overview` container so the available card width, rather than just the screen width, determines stacking.

### 5. Backend / API behavior

Unchanged: no provider, calculation, query, status definition, permission or endpoint changes. Global dates, Refresh, grouping, status links, session-aware URLs and the existing error/Retry path remain. The API may still return comparison data; the three cards do not display it.

### 6. Database / migration impact

None. No models, migrations, settings or application records changed. Django verification used the existing guarded runner with a disposable PostgreSQL test database on loopback port 5432, which was destroyed afterward. Browser responses came from those test-record exports; no sample records were added to the application database.

### 7. Tests performed

- Six focused existing Django tests passed in 7.442s: actual status counts, global date presets/custom dates, supported status-filter navigation, endpoint permissions, independent grouping, and the empty/populated executive layout with booking links. System check reported no issues. The layout/export test was rerun after the final calendar-check SVG adjustment and passed in 3.880s.
- `node scratch/booking-summary-kpis-20261111/review.cjs`: **355 browser assertions passed**, zero JavaScript errors and zero mutating requests. Actual rendered empty/populated dashboard exports were checked at 280, 320, 390, 600, 768, 1024, 1440 and 1920px. Checks cover exactly three cards, actual counts, labels, links, colors/borders/padding/type/icons, equal dimensions, mobile stacking, desktop columns, no page/text overflow, date filtering, refresh to empty/populated states, independent grouping, errors/Retry, keyboard focus/Enter and missing-chart fallback.
- At 390/1440px, before/after stylesheet/script comparisons confirmed unchanged surrounding section dimensions/styles and Booking Trend drawing dimensions/type/data/options. Desktop populated and mobile empty screenshots were visually inspected; the final desktop screenshot confirms the calendar-check stroke is visible. Browser evidence and screenshots: `scratch/booking-summary-kpis-20261111/`. Django reports: `scratch/test-organization-20261109/booking-summary-kpis-results.json` and `booking-summary-kpis-render-results.json`.
- JavaScript syntax and scoped Git whitespace checks passed. The optional design skill kit is absent (`.agents/tokens` and `.agents/scripts/accuracy_report.mjs` do not exist), so its quality gate was unavailable; no score is claimed for it.

### 8. Remaining limitations / troubleshooting / safe practice

Verification used local Chrome with exported Django test responses, rather than a signed-in physical-device session or a deployed site. The full application suite, other browser engines and full accessibility certification were not run. This change is prepared as a scoped Git commit; no deployment was performed. Other existing working-tree changes were preserved.

If old styling remains, hard-refresh and inspect the booking CSS/JS URLs for `v=20261111-booking-summary-kpis`. If cards disappear on refresh, inspect the existing dashboard GET response and browser console; the missing comparison paragraph should no longer throw an error. A narrow Facilities column deliberately stacks cards even on a wider device.

Safe practice exercise: choose an existing date range, inspect `executive.booking_overview` in the dashboard GET response, and compare `total`, `approved` and `pending` with the three visible values. Press Refresh, change Daily to Weekly, and verify the totals still match. Resize to 390px to verify stacking, then use Tab and Enter on Approved to verify the existing status destination. This exercise needs no booking creation or editing. For CSS practice, temporarily change only the summary padding from 14px to 16px, inspect the three cards at both widths, then restore 14px.

## Current: Complete daily calendar order and responsive chart spacing - November 10, 2026

### 1. Cause / reason

The latest explicit brief supersedes the earlier screenshot-based custom tick selection and44px width. Inspection confirmed that Django already creates chronological, zero-filled buckets with `range(period.days)` in `build_booking_overview()`; there was no confirmed backend omission or count-based trend sorting. The previous frontend `bookingDateTicks()` deliberately showed fewer labels even when a short range had space, and `bookingBarThickness()` used populated dates rather than ordinary category spacing. Both custom functions were removed in favor of the requested Chart.js label skipping and46px maximum. Skipping a visible label does not combine dates or remove a bar.

### 2. Exact files changed / current lines and anchors

| File / current line | Anchor and change |
| --- | --- |
| `backend/static/components/js/admin_booking_overview.js:81` | `trendRows = overview.trend`: one backend-ordered array supplies descriptions, labels, counts, tooltip dates and keyboard inspection. No frontend sorting, filtering, deduplication or regrouping. |
| `backend/static/components/js/admin_booking_overview.js:111` | Dataset map reads `trendRows`; executive maximum46, category0.88/bar0.95. Removed the fixed-width callback. Other roles retain maximum28 and category0.8/bar0.9. |
| `backend/static/components/js/admin_booking_overview.js:145` | X ticks use automatic label skipping, executive limit8, horizontal11px labels and8px skip padding. Removed the custom tick hook. Other-role limit6/font12/default3px skip padding remain. |
| `backend/templates/dashboard/pages/admin_dashboard.html:623` | Existing Booking script cache version becomes `20261110-booking-daily-order`. |
| `docs/booking-overview-implementation.md:3`, `CAMPUSHUB_CONTEXT.md:3` | Current implementation report and project reference. |

Only these four tracked files were changed for this task. The requested `dashboard_bookings.py`, chart CSS and `super_facilities_overview.html` were inspected and retained. Source hashes also confirm no change to the ranking renderer/CSS/partial or global AJAX controller. Booking Summary and Most-Booked Facilities were compared with the exact pre-task local implementation, including their content and dimensions.

### 3. Changes made

Daily keeps one category and count for every selected calendar day, including zeros, oldest first. A wide November4–10 view shows all seven labels. A thirty-day view retains all30 categories and bars; Chart.js can hide only some tick labels when space is limited. Labels stay centered on their original bucket positions. Weekly and Monthly retain Django's consecutive periods, clipped range boundaries and existing aggregation rules. Exact ISO dates, including years, remain in tooltips.

Super Admin bars remain navy `#1A1851`, capped at46px with the existing3px rounding. Category/bar percentages let bars narrow naturally for dense daily ranges, including empty dates, rather than forcing44px bars across those categories. Existing desktop220px/mobile210px chart heights remain. Label spacing was increased after browser verification found a collision in a90-day phone view using only the initial requested settings.

### 4. How it works / functions, inputs, outputs and data flow

`build_booking_overview(period, totals, comparison, grouping=...)` remains unchanged. Its inputs are the selected reporting period, existing totals/comparison and requested grouping. It creates empty buckets by iterating every calendar day, then adds the database's submission-date/status counts to them. Daily uses each date; Weekly uses successive seven-day blocks anchored at the selected start; Monthly uses calendar months clipped to the selected range. Dictionary insertion order preserves chronology. The output includes `trend`, grouped ISO start/end dates, labels and existing totals/status/navigation fields.

The template serializes that object into `bookingOverviewData`. Existing initial-load, dashboard-data and booking-trend-data handlers call `render(overview, chartOnly)`. After the existing validation, `trendRows` references the exact provider array. The description loop and chart label/value maps now explicitly read that same reference. Existing tooltip callbacks and keyboard handlers already read `trendRows`, so index3 refers to the same date everywhere. The frontend does not need to sort an already chronological backend response.

Annotated example: Daily November4–10 has seven rows. A zero on November5 stays at index1 even if a narrow screen hides the printed `Nov 05` tick. The bar/data slot, ISO tooltip date and keyboard description still refer to November5. `autoSkip` changes visible ticks only; `maxTicksLimit: 8` is not an eight-record limit. Chart.js calculates each width from its category slot and applies the46px ceiling.

### 5. Backend / API behavior

Unchanged: booking population, submission-date basis, date/status calculations, totals, permissions, Weekly/Monthly rules, global filters and AJAX refresh/retry behavior. The backend's existing daily generation is preserved byte-for-byte. No application server restart or deployment was performed.

### 6. Database / migration impact

No model, migration, application-record, dependency or configuration changes. Django verification used guarded, uniquely named disposable local PostgreSQL test databases and destroyed them afterward. Additional calendar exports use test-only booking fixtures in that disposable database; they do not insert sample records into the application database. The browser replayed these exported HTML/API responses and made no mutating requests.

### 7. Tests performed

- **Three existing Django tests passed** in3.017s: all global date presets/custom/zero ranges; selected grouping/partial buckets; grouping independence from Sales/global dates. Guarded runner: `scratch/test-organization-20261109/run_local_tests.py`, with the three named methods in `modules.reports.tests.test_dashboard_bookings.DashboardBookingOverviewTests`. Result: `scratch/test-organization-20261109/booking-daily-order-results.json`.
- **One additional calendar/export test passed** in3.473s: exact November4–10 seven-day daily range; October12–November10 thirty-day Daily/Weekly/Monthly; December28–January5 Daily/Weekly/Monthly; consecutive boundaries, zero dates, exact database counts and selected endpoints. Test: `booking_daily_order_exports.BookingCalendarExports.test_calendar_buckets_and_export`, run through the same guarded runner. Both disposable databases were destroyed.
- **2,923 actual Chart.js Chrome checks passed**: seven widths280–1440px, all groupings,7/30/90-day periods, month/year transitions, zeros/empty/single/multiple data, all labels/values/tooltips, centered tick/bar positions, no bar or label overlap, unchanged compact heights and surrounding content. Added exact all-bucket tooltip comparisons, ordered descriptions, keyboard first/final positions, seven labels when wide enough and the actual Last30Days selector/API refresh path. Existing refresh/error/Retry/loading/resize/no-library cases passed. No JavaScript errors or mutating requests. Command: `node scratch/booking-daily-order-20261110/review.cjs`; results/screenshots in that folder.
- JavaScript syntax and scoped Git whitespace checks passed. Seven protected source hashes remained unchanged. Desktop and phone screenshots were visually inspected, including seven daily labels and the dense30-day phone view.

### 8. Remaining limitations / troubleshooting / safe practice

46px is a maximum; thirty-day daily bars are intentionally narrower so each date retains its own position. Narrow screens skip some printed labels, including potentially the final tick, while preserving every underlying date and exact tooltip. Existing all-zero empty presentation is retained. Local only; not committed, pushed or deployed. No physical-device or production-account verification was performed.

If an older chart remains, hard-refresh and confirm the Booking script requests `v=20261110-booking-daily-order`. Inspect `executive.booking_overview.trend` in the existing dashboard GET response: Last7Days must contain seven consecutive ISO dates and Last30Days thirty. Do not diagnose label skipping alone as missing records. If counts differ, compare the submission date rather than the scheduled reservation date; backend date semantics were not changed.

Safe practice exercise: select Last7Days and Daily, inspect all seven response rows, then use Home/RightArrow/End on the focused chart to compare dates/counts with tooltips. Select Last30Days and verify thirty response rows, including zeros. Resize to390px and confirm labels may skip while the row count remains30. Switch Weekly/Monthly and compare bucket start/end dates; a custom December-to-January range can verify year order without editing or creating bookings.

Latest chart-sizing follow-up: Booking Trend keeps the existing combined Summary/Trend card and vertical bars, with a 320px drawing area at screen widths 600px+ and 260px below. Only wrapper sizing and control alignment changed; existing Django counts/date/grouping inputs still feed the same responsive chart renderer. Safe check: change grouping/Refresh and compare counts, then resize without editing a booking. The [dashboard guide](dashboard-analytics-operations-update.md) contains the current eight-part report, exact files/lines, measured checks and troubleshooting for this update, Sales Trend and Users by Type.

## Latest: Booking Summary inside Booking Trend — October 31, 2026

The latest request moves Booking Summary and the same three KPI cards inside the Booking Trend article, above its heading/grouping/vertical bars, matching Marketplace's summary-then-trend arrangement. Most-Booked Facilities stays independent. The unchanged `#bookingOverviewCard` host and existing renderer inputs/outputs keep actual Django totals, selected dates/grouping, Refresh and retry behavior intact. Component spacing is in `admin_booking_overview.css` under the executive-only combined-card comment.

Safe practice: compare `executive.booking_overview` with the displayed summary and bars before/after a grouping change, then resize without editing a booking. The full current eight-part report, exact files/lines, functions/data flow, tests and troubleshooting for this follow-up and Recent Orders are in the [dashboard guide](dashboard-analytics-operations-update.md). The independent-card report below describes the preceding arrangement; the summary's new position supersedes its outside-card placement.

## Current: Independent Facilities Overview cards — October 31, 2026

### 1. Cause / reason

Facilities Overview still used a shared `executive-overview-body` border around all content. The extra Facility management navigation and a `<details>` wrapper around Most-Booked Facilities added another navigation/expansion layer. The latest request removes these surrounds and keeps the existing content in independent cards.

| Before | After | Why |
| --- | --- | --- |
| Large bordered wrapper around the section content | Transparent section with its heading outside independent cards | Remove the redundant outer boundary. |
| Facilities / Bookings / Calendar shortcut row | Existing specific Analytics, booking and reservation actions remain | Remove only the requested shortcut row. |
| Collapsed ranking with another summary heading | One always-visible Most-Booked Facilities card | Make the actual ranking directly available without duplicate headings. |
| Mixed 8/12/16px internal gaps | 16px between KPI cards and independent containers | Keep consistent spacing on desktop and phones. |

### 2. Exact files changed

Paths are relative to the project root; named anchors remain useful if later edits move lines.

| File / current line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/super_facilities_overview.html:6` | Remove the shared outer wrapper and its shortcut navigation. Retain the unbordered `#bookingOverviewCard` controller host, three summary cards and the existing trend article. Line 28 includes Most-Booked Facilities directly without `<details>/<summary>`. Line 32 retains upcoming reservations/attention after the chart cards. |
| `backend/static/components/css/admin_executive_refinement.css:295` | Give the controller host a 16px layout gap, set KPI/chart/operations gaps to 16px, and remove the metrics' redundant bottom margin. Line 299 applies the shared 16px padding, 10px radius and full subtle white-card border to trend, ranking and the existing operations cards. Selectors affect only Super Admin Facilities. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | Version the refinement CSS as `20261031-facilities-independent`; executable scripts and their versions remain. |
| `backend/core/modules/reports/test_dashboard_executive.py:121` | Update the existing facilities layout test to assert no shared outer wrapper, shortcut navigation or accordion, and exactly one ranking heading. Existing actual-data, detail-link and optional fixture exports remain. |
| `docs/booking-overview-implementation.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:17` | Record the latest layout, implementation/data flow, real checks, troubleshooting and safe practice. |

### 3. Changes made / expected behavior

Facilities Overview remains an outside heading with its existing subtitle and View Analytics action. Booking Summary retains three separate real-data KPI cards. Booking Trend keeps its navy vertical bars and grouping controls in one bordered card; Most-Booked Facilities is always visible in a second bordered card. Both span the existing Facilities column and stack with a 16px gap.

Upcoming Reservations and Facility Attention keep all their existing data, columns and actions, with their own card boundaries after removal of the shared surround. The existing View Calendar, View All Bookings, exact reservation-detail and status links remain. Only the redundant top shortcut row and ranking expander were removed. Other dashboard sections retain their layouts. On phones, summary cards stack naturally and the existing reservation table keeps its contained horizontal scrolling.

### 4. How it works / functions, inputs, outputs and data flow

This follow-up changes template structure and scoped spacing/borders; no executable JavaScript or application Python function changed. `#bookingOverviewCard` remains a **controller host**, not a bordered outer card, so existing queries for summary, trend, grouping, loading/error, retry and the JSON seed continue finding the same nodes.

```text
Facilities Overview section heading / subtitle / View Analytics
  #bookingOverviewCard (unbordered controller host)
    Booking Summary -> three separate KPI cards
    Booking Trend -> existing vertical bar chart and grouping
    Most-Booked Facilities -> existing ranking card, always visible
  Upcoming Reservations and Facility Attention -> existing independent cards
```

The unchanged Django context supplies `executive.booking_overview`, `facility_analytics.most_booked_facilities`, upcoming reservations and facility attention. `render(overview, chartOnly)` in `admin_booking_overview.js` continues mapping request-submission buckets to bars. `draw(rows)` / `render(rows)` in `admin_most_booked_facilities.js` still maps the actual top-five facility ranking to its existing chart and accessible list. Removing `<details>` makes that same canvas visible initially; it does not introduce a second chart, ranking query or record source.

Existing dashboard events retain selected periods, Daily/Weekly/Monthly, chart-only regrouping, global Refresh, Retry, empty states, keyboard announcements and no-library text fallbacks. Ranking remains based on approved/completed **scheduled usage**, while Booking Trend remains based on **request submission**. Upcoming reservations and facility attention remain their established current snapshots.

Safe practice: reload Dashboard and check that the Facilities heading has no enclosing white card. Count the three KPI cards; confirm Most-Booked Facilities is visible without clicking an expander. Select Last 7 Days, change Booking Trend grouping, then Refresh. Compare trend counts and facility names/counts with the existing API fields. Open an existing reservation detail or View Calendar and return without approving or editing anything. In DevTools, temporarily change only the Facilities grid gap from 16px to 20px; resize to phone width, then reload to restore 16px. No data writes are required.

### 5. Backend / API behavior

Unchanged: same Django/PostgreSQL data, protected endpoints, permissions, request/response fields, filters/defaults, ranking calculations and date bases. No booking, availability, approval, payment, reporting or other domain workflow was modified. The removed top shortcuts had no backend operation; specific functional links remain.

### 6. Database / migration impact

None. No schema/migrations, credentials, environment, live data writes or deployment changes. Verification used disposable localhost PostgreSQL test databases and intercepted read-only browser requests. The user-controlled application process was not restarted.

### 7. Tests performed

- **57/57 focused Django tests passed in 23.473 seconds** across existing executive, booking-overview, most-booked-facilities and upcoming-reservations suites. Includes updated structure assertions, actual dates/counts/statuses, grouping, permissions, rankings and working reservation destinations. System checks reported no issues.
- **2003/2003 Chromium checks passed across 11 renders/eight widths (280–1920px)** using current actual Django fixture HTML/API responses. Verified no outer border/nav/accordion; outside heading; three separate KPI cards; independent trend/ranking/operations borders, aligned widths and exact 16px gaps; one visible ranking heading; actual chart/summary/reservation/attention values; grouping/selected dates/Refresh/retry; pointer/keyboard inspection; empty/text fallback states; no page overflow or browser write requests. Desktop/phone populated and empty layouts were inspected.
- Evidence: `scratch/facilities-independent-20261031/django.log`, `browser.log`, `browser-result.json` and full Facilities PNG captures. Scoped syntax, whitespace and current-report path/line checks are in `file-checks.log` and `whitespace.log`.

### 8. Remaining limitations / troubleshooting

Refresh Dashboard to load `20261031-facilities-independent`. If a user-controlled local Django process caches the old template, restart it locally and refresh. If the large border or ranking expander remains, inspect the current `super_facilities_overview.html` and confirm its shared wrapper/navigation/details are absent. Do not remove the unbordered controller host or existing chart/data IDs to remove a visual border.

Full width means the existing Facilities column; the Marketplace/Facilities dashboard grid is unchanged. Long facility names keep the existing compact chart labels and full accessible names/keyboard announcements. Verification used Chromium and isolated source-rendered fixtures, not production data, other browsers or physical devices. The optional design-kit gates remain unavailable; no new accessibility certification is claimed.

## Previous: Booking Trend vertical bars — October 31, 2026

### 1. Cause / reason

The requested Booking Trend was still explicitly configured as a line chart in executive mode. The shared executive card reset also removed its individual border, despite the existing trend `<article>` being a separate component. This update changes that presentation while preserving the existing booking calculations and date/grouping requests.

| Before | After | Why |
| --- | --- | --- |
| Single navy line | Single navy vertical bar series | Match the requested period-by-period booking count presentation. |
| Trend card border flattened by shared styling | Full subtle border, white surface, 10px radius and 16px padding | Keep Booking Trend in its own container within Facilities Overview. |
| Repeated total text in executive tooltip | Full period dates and one booking count | Make the actual reporting interval and value clear. |

### 2. Exact files changed

Paths are relative to the project root; use the anchors if later edits move lines.

| File / current line | Anchor and change |
| --- | --- |
| `backend/static/components/js/admin_booking_overview.js:90` | `canvas.setAttribute('aria-label', ...)`: announce a vertical bar chart. Lines 109–123 remove line-only options and draw bars. Lines 129–136 format executive tooltips. Lines 104 and 151 hide the blank executive canvas wrapper when text fallback is needed. Existing validation, grouping, axes, keyboard navigation and chart reuse remain. |
| `backend/templates/dashboard/partials/super_facilities_overview.html:22` | `facilityBookingOverviewChart`: initial accessible label names the bar chart and arrow-key inspection. Preserve the existing independent article, heading, select, period, empty/error states and View All Bookings. |
| `backend/static/components/css/admin_executive_refinement.css:295` | `.executive-facilities .facilities-trend`: restore this card's own border, 16px padding, white surface and shared 10px radius. Other cards retain their styling. |
| `backend/templates/dashboard/pages/admin_dashboard.html:619` | Version the booking renderer as `20261031-booking-bars`. Preserve the current shared stylesheet cache version and other script versions. |
| `backend/core/modules/reports/test_dashboard_executive.py:134` | Extend the existing `FACILITIES_REVIEW_DIR` export guard to save actual Today/Last 7 Days API responses in all three groupings. No new test case, application behavior or live data is added. |
| `docs/booking-overview-implementation.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:15` | Preserve this choice, functions/data flow, measured verification, debugging and safe practice. |

### 3. Changes made / expected behavior

Booking Trend shows one vertical bar per returned reporting period, in chronological order, using CampusHub navy `#1A1851`. The x-axis keeps Django's date/period labels; the y-axis retains a zero baseline and whole-number tick precision. Daily, Weekly and Monthly remain available and retain the applied dashboard dates. No replacement filter, sample toggle or booking operation was introduced.

The independent bordered trend card remains inside the existing Facilities Overview content area. Summary cards, Most Booked Facilities, upcoming reservations, navigation and the surrounding dashboard layout are unchanged. Empty results keep the clean No Booking Data Yet message and hide the chart footprint while retaining grouping and View All. If Chart.js is unavailable, actual text values remain visible without a blank canvas area.

### 4. How it works / functions, inputs, outputs and data flow

The unchanged Django `executive_overview(period, metadata)` uses the physical-booking queryset, excluding schedule blocks and service resources. `build_booking_overview(period, totals, comparison, grouping=..., records=physical)` counts actual requests by **submission date (`created_at`)** inside the selected range. It returns chronological `trend` rows with `label`, integer `count`, status totals and the bucket's actual `start_date`/`end_date`. This is request activity, not scheduled utilization or availability.

The existing JSON seed invokes `render(overview)`. The same function validates and maps each `trend` row to the navy dataset, now using Chart.js `type: 'bar'`. `beginAtZero: true` and `ticks.precision: 0` keep booking counts readable. Existing chart instances update rather than accumulating on Refresh. The non-executive branch remains a stacked status bar chart.

```javascript
// Each source row comes from the existing Django response.
labels: overview.trend.map(row => row.label)  // Reporting periods on x.
data: overview.trend.map(row => row.count)    // Actual booking counts on y.
```

The executive tooltip uses the row's full bucket dates and the hovered integer count, for example one saved request yields `1 booking`; no totals are manufactured. ArrowLeft/ArrowRight/Home/End still reveal the same values through a live announcement and tooltip. The text description remains available to assistive technology and becomes visible if the library cannot draw.

The existing `load(..., bookingOnly=true)` in `admin_dashboard_filter.js` sends `booking_grouping` plus the already-applied dates to the same protected dashboard API. Its `campushub:booking-trend-data` event calls `render(overview, true)` without rebuilding unrelated sections or summary values. Global date changes and Refresh still use the ordinary dashboard response. Retry preserves the current date range.

Safe practice: select Last 7 Days, then try Daily, Weekly and Monthly. In Network, compare `executive.booking_overview.trend` with the visible bars and hover/keyboard tooltips; verify the displayed start/end dates stay unchanged while grouping changes. Press Home/End on the canvas to inspect first/last periods. Refresh and confirm grouping/range persist. Use an existing empty date range to check No Booking Data Yet. These checks require no booking creation, approval or payment action.

### 5. Backend / API behavior

No application Python query, endpoint, response contract, permission, default selection, booking workflow or status/payment rule changed. Django/PostgreSQL remains the data source. Submission-date totals, service/schedule exclusions and grouping boundaries retain their existing rules. Historical periods need not match scheduled-usage rankings or current upcoming reservations.

### 6. Database / migration impact

None. No schema, migrations, credentials, environment, live booking writes or deployment changes. The optional fixture export runs only when its explicit test environment variable is set. Verification used disposable localhost PostgreSQL databases and read-only intercepted browser requests. The user-controlled application runtime was not restarted.

### 7. Tests performed

- **70/70 existing Django tests passed in 36.441 seconds** across `test_dashboard_bookings`, `test_dashboard_executive` and `test_dashboard_periods`. Coverage includes real request dates/counts/statuses, zero buckets, independent grouping/global ranges, permissions, layout, service exclusions and query bounds. System checks reported no issues.
- After adding the optional grouped-fixture export, the existing facilities layout/link test was rerun: **1/1 passed in 4.980 seconds**. This is a rerun, not an additional distinct test.
- **830/830 Chromium checks passed across 11 renders/eight widths (280–1920px)** using actual Django-rendered HTML/API fixtures. Verified independent card borders/padding, vertical navy bars, chronological labels, exact database counts, whole-number ticks (including single-request buckets), selected ranges/grouping, pointer/keyboard tooltips, chart reuse, local error/retry, global Refresh, empty state, no-library text fallback and no page overflow. No browser write requests or page errors occurred. Desktop/phone populated, empty and fallback screenshots were inspected.
- Evidence: `scratch/booking-trend-bars-20261031/django.log`, `fixtures.log`, `browser.log`, `browser-result.json` and PNG captures. Scoped syntax/whitespace/path-reference checks are recorded in `file-checks.log` and `whitespace.log`.
- The optional design kit's token/gate scripts are not installed in this workspace; no kit gate, measured contrast or cross-browser accessibility certification is claimed. Project checks and actual browser checks above were used.

### 8. Remaining limitations / troubleshooting

Refresh Dashboard to load the versioned CSS and booking script; restart the user-controlled local Django process only if it retains old templates. If a line still appears, inspect the loaded booking script version and `Chart.getChart('facilityBookingOverviewChart').config.type`, which should be `bar`. If its border is absent, inspect the scoped `.facilities-trend` rule rather than changing all dashboard cards.

If no bars appear, first distinguish a genuine zero total from an API error or missing chart library. Empty dates show the honest empty state; failures retain error/Retry or actual text fallback. Do not add sample bookings to fill the card. Long ranges still use the existing bounded bucket generation and sparse x-axis tick labels; every period remains in the data and keyboard inspection. Verification used Chromium/source-rendered fixtures, not live production records, other browsers or physical devices.

## Previous update — October 22, 2026

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

### Publication scope - November 11, 2026

The Git commit contains only the Booking Summary template, summary CSS, optional-comparison guard, two booking asset cache versions, expected labels and this report. Earlier uncommitted chart, attention, dashboard and other work remains in the local folder. The detailed test results above describe the complete local working tree at implementation time. Source line numbers in that report refer to that local tree; use the named anchors when reviewing this isolated commit.
