# CampusHub Dashboards: Analytics and Operations

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
