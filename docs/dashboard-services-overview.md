# Super Admin Services Overview — October 22, 2026

## Current: Balanced Services card heights — November 1, 2026

### 1. Cause / reason

Confirmed in the template and styles: Requests by Service shared the first grid with Service Request Trend, while Recent Service Requests and Service Attention lived in a second grid. The outer domain grid used `align-items: start`, and both inner grids sized cards to their content. This prevented the three lower cards from sharing spare height beside the Users column and Recent System Activities.

The latest request explicitly supersedes the earlier natural-height-only choice for these three desktop cards. The Services column can now stretch to the existing row height, and the lower cards share its remaining space evenly. The summary/trend card retains its own content sizing. No unrelated dashboard section is restyled.

### 2. Exact files changed, current lines and nearby anchors

| File and current line | Anchor / change |
| --- | --- |
| `backend/templates/dashboard/partials/super_services_overview.html:35` | Close the trend-only grid, then open `services-grid services-operations services-support-grid` at line 36. Move the existing Requests by Service article into the same group as Recent Service Requests and Service Attention. Preserve all article contents, IDs and data hooks. |
| `backend/static/components/css/admin_services_overview.css:72` | Update the grid comment to describe the trend group and lower stack. |
| `backend/static/components/css/admin_services_overview.css:112` | `Share the desktop row's spare height`: add scoped flex/grid sizing from the existing 1280px two-column breakpoint. Lines 121–124 use three equal, content-safe grid rows. Lines 125–133 make card bodies flexible, center empty messages, keep their inner padding compact and allow the existing distribution chart to grow with its card. |
| `backend/templates/dashboard/pages/admin_dashboard.html:26` | Version the Services stylesheet as `20261101-services-balanced` so browsers fetch the matching layout rules. |
| `scratch/services-height-balance-20261101/check.cjs:1` | Local browser verification harness using isolated ORM-rendered dashboard/API exports. |
| `docs/dashboard-services-overview.md:3`, `CAMPUSHUB_CONTEXT.md:3` | This implementation report and the current layout decision. |

### 3. Changes made

Requests by Service, Recent Service Requests and Service Attention remain full-width cards in that order. Their shared grid keeps 16px gaps. On desktop, Services stretches within its own grid row, its content wrapper fills the remaining height, and the three lower cards divide the available space equally. This distributes spare space inside the cards instead of leaving a blank region below Service Attention.

The headings stay at the top. A visible empty-state body fills the remaining card space and centers its icon/message group vertically and horizontally. Its compact inner padding is 4px on desktop; the flexible body supplies the extra space. The distribution chart can grow within its card. No fixed card heights, viewport-height calculations, measuring JavaScript or hidden overflow were added. Below 1280px, the desktop flex/equal-row rules stop applying; cards keep natural heights with the existing 16px gaps and responsive request rows.

### 4. How it works / functions, inputs, outputs and data flow

The existing Django `service_overview()` projection still supplies the same `executive.services` counts, chart rows, recent requests and attention records. The template emits those values under the same IDs and `data-*` hooks. The unchanged `render(services)` in `backend/static/components/js/admin_services_overview.js:82` validates refreshed snapshots, fills those nodes and toggles their empty states. CSS then lays out whichever real content is visible; it never calculates or invents service metrics.

```css
/* Each row gets an equal share; its real content remains the minimum. */
grid-template-rows: repeat(3, minmax(min-content, 1fr));
/* The surrounding flex column supplies spare desktop row height. */
flex: 1 0 auto;
```

`1fr` means one equal share of the available grid space. `min-content` prevents a populated request table or attention list from being squeezed below the space it needs. Using the existing parent row as the sizing source means Refresh, different record counts and responsive widths trigger normal browser layout, without another API request or resize controller.

The input is unchanged server-rendered content or the existing dashboard JSON. The output is the same content in a balanced desktop stack. View All remains at the Recent header's top right; request references, timestamps, status text, attention destinations and Daily/Weekly/Monthly controls remain intact.

### 5. Backend / API behavior

No runtime Python or JavaScript changes. No queries, response fields, sorting, record limits, global dates, chart grouping, permissions, endpoints or workflow changes. Initial Django and refreshed JavaScript nodes use the same preserved hooks. Existing loading/error/retry logic still hides stale service content and displays the real error state.

### 6. Database / migration impact

None. No models, migrations or live records changed. Existing tests used disposable local PostgreSQL test databases, which were destroyed afterward. Browser verification intercepted actual isolated test exports and blocked all non-GET requests. No environment edits, application server restart or deployment occurred.

### 7. Tests performed

- **33/33 Django tests passed** using the existing `scratch/operating-schedule-20261029/run_tests.py` runner: 17 Services/Operations tests in 7.494 seconds, then 16 Executive tests in 9.257 seconds. Both runs reported clean Django system checks. Existing tests cover service-only projections, real request destinations, grouping, empty/populated rendering, audit history and permissions.
- **761/761 Chromium checks passed across 22 renders**, run with `node scratch/services-height-balance-20261101/check.cjs`. Widths: 280, 320, 390, 768, 1024, 1280, 1440 and 1920px. Checks include the exact three-card order, equal desktop heights, 16px gaps, full card widths, vertically centered empty messages, no unused space below Attention, actual request values/timestamps/routes, attention counts, Refresh/error/retry, no-JavaScript rendering, missing-chart-library fallback, no page overflow and no clipped lower cards. No browser errors or write requests occurred.
- In the populated-Users fixture, Service Attention and Recent System Activities had identical bottom coordinates at 1920, 1440 and 1280px. At 1440px, all three lower Services cards measured about **204.05px**, a computed result rather than a hardcoded height. Mobile retained natural heights.
- Inspected empty desktop, populated desktop and phone Services screenshots. Evidence is in `scratch/services-height-balance-20261101/browser-result.json` and its PNG files, including `executive-users-populated-1440.png`, `services-services-populated-1440.png` and `operations-populated-390.png`.
- Scoped `git diff --check` passed. Generic design-skill kit gates were not run; these are measured project checks, not full WCAG or cross-browser certification.

### 8. Remaining limitations / troubleshooting / safe practice

Real content sets the minimum height. If a populated Services table/list requires more height than the right column, the left column can grow beyond Recent System Activities rather than clipping records. Desktop equal-height cards may therefore make the row taller. On smaller screens the columns are stacked, so artificial cross-column height matching is intentionally disabled.

During browser debugging, equal empty cards initially exceeded a short right-column fixture by a few pixels because their repeated message padding established a larger content minimum. Compacting only that desktop inner padding to 4px allowed the available height to be shared while preserving every message. Populated tables continue to retain their real minimum size.

If the old layout persists, reload and verify the Services CSS URL ends in `20261101-services-balanced`. Inspect `.services-support-grid`: it must contain exactly the three lower card articles. At widths from 1280px, check Services `align-self: stretch`, the content wrapper's flex layout and the support grid's three equal rows. Below that breakpoint, natural card heights are expected. If data is unavailable, use the existing Refresh/retry controls; do not add fake service records to fill space.

Safe practice: open Dashboard at desktop width and select a reporting period with existing data. Inspect the three lower card heights and the bottom of Service Attention beside Activities. Resize to phone width, verify all five recent-request fields and View All remain reachable, then Refresh. Use a period with no requests to check centered empty states. This exercise requires no saved data edits.

## Current: Full-width vertical Services cards — October 31, 2026

### 1. Cause / reason

The preceding layout used container-width and empty-state rules to place the three auxiliary Services cards beside one another. The latest request replaces those rules with a vertical stack in every data state. Inspection also confirmed that the recent-request table's 570px minimum width caused sideways scrolling in narrower cards, and its wrapping flex header could move View All below the title.

| Before | After | Why |
| --- | --- | --- |
| Empty auxiliary cards could share two- or three-column rows | Requests by Service, Recent Service Requests and Service Attention each fill the Services column | Follow the requested vertical order and avoid narrow cards. |
| Fixed minimum table width with horizontal overflow | Five columns when space permits; labelled request rows on compact cards | Keep all fields readable without sideways scrolling. |
| Header action could wrap below the title | View All occupies the header's top-right grid cell | Keep navigation consistently positioned. |
| Empty-message spacing inherited broader rules | Centered icon/text with 8px vertical padding | Keep genuine empty states compact. |

### 2. Exact files changed, current lines and nearby anchors

Paths are relative to the project root. Use the named anchor if a later edit moves a line.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/static/components/css/admin_services_overview.css` | 81 media rule; 84 `Services always stacks`; 95 `@container service-request-card` | Remove the multi-column and empty-only flattening rules; enforce one full-width column with 16px gaps, compact empty states, top-right action and responsive request rows. |
| `backend/templates/dashboard/partials/super_services_overview.html` | 59 `table class="services-table"` | Add matching labels and explicit table roles to the same five initial Django fields. |
| `backend/static/components/js/admin_services_overview.js` | 95 `const labels`; 103 `item.setAttribute` | Apply the same labels and roles to request cells rebuilt after Refresh. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 26 Services CSS; 622 Services script | Set both asset versions to `20261031-services-vertical` so browsers load the paired presentation changes. |
| `docs/dashboard-services-overview.md` | 3 current report | Explain the cause, implementation, data flow, checks and safe practice. |
| `docs/dashboard-analytics-operations-update.md` | 3 current follow-up | Supersede the earlier empty-panel compaction while preserving the outside Users heading decision. |
| `CAMPUSHUB_CONTEXT.md` | 3 current Services decision | Save the accepted stack, preserved behavior and verified results. |
| `docs/web-ui-ux-guidelines.md` | 27 latest Users/Services clarification | Record the latest vertical-stack choice and unchanged Users layout. |

### 3. Changes made

Service Summary/Trend stays first, followed by Requests by Service, Recent Service Requests and Service Attention. All four cards use the full Services-column width with 16px gaps. The two equal-width Services and Users columns remain side by side at desktop widths of 1280px and above and stack below that breakpoint. Card heights follow their content rather than stretching to match the neighboring column.

Empty-state icons and messages are centered with 6px internal gaps and 8px vertical message padding. Recent Service Requests keeps View All at the top right. All five fields remain: Request No., Service, Client, Status and Date. At card widths up to 520px they become labelled, two-column request rows, with the request number spanning the row; up to 260px they stack into one column. Text wraps without clipping or a horizontal scrollbar. The native column headers remain available to assistive technology.

The outside Users Overview title/subtitle and View Analytics remain. Users by Type keeps its existing large, responsive 240–280px donut where space permits, centered on narrow cards with its account-type table. No unrelated dashboard layout, chart height or styling was changed in this follow-up.

### 4. How it works / functions, inputs, outputs and data flow

Django still supplies `executive.services.recent_requests` and all chart/count fields. The initial template renders the same five values and actual request URL. `render(services)` still validates the snapshot and constructs those five cells after a full refresh; it now reads the existing header labels and adds presentation metadata to each cell. CSS reads that metadata only when the card becomes narrow.

```javascript
entry.dataset.label = labels[index]; // e.g. the existing heading "Client"
entry.setAttribute('role', 'cell');  // preserve table semantics with responsive CSS
// The cell still contains the original row.requester; no value is recalculated.
```

The input is the unchanged Services snapshot; the output is the same linked request content with responsive labels. The date's existing formatted text and `datetime` value, URL validation, five-row limit and actual status labels stay intact. Chart-only grouping still updates only the trend. This uses the existing renderer and CSS rather than adding another request, data projection or table implementation.

### 5. Backend / API behavior

Unchanged. Actual Django counts, dates, Daily/Weekly/Monthly grouping, Refresh/error/retry handling, permissions, service/request destinations and workflows are preserved. No API fields, routes, queries or business rules were added or removed.

### 6. Database / migration impact

None. No schema/migrations, application records, configuration, environment, runtime restart or deployment changes. Verification used a disposable localhost PostgreSQL test database and intercepted read-only browser responses from its exported Django fixtures.

### 7. Tests performed, debugging and safe practice

- **24/24 existing executive and Services Django tests passed in 12.729 seconds**; Django system checks reported no issues. The isolated test database was destroyed afterward.
- **2289/2289 Chromium checks passed across 22 renders and nine widths from 280px to 1920px.** Checks covered full-width vertical order and 16px gaps for empty/populated cards, balanced columns, header action position, all five initial/refreshed request fields and actual links/timestamps, no overflow/clipping, actual chart data, donut size/alignment, global dates/grouping, Refresh/error/retry and missing-chart-library fallbacks. No browser writes or page errors occurred.
- `node --check backend/static/components/js/admin_services_overview.js` passed. Desktop empty-state and Users by Type screenshots were visually inspected; populated and narrow-screen bounds were checked by the browser harness.
- Evidence: `scratch/services-vertical-20261031/django.log`, `browser.log`, `browser-result.json` and PNG captures. Final source/whitespace checks are recorded in `file-checks.log` and `whitespace.log`.

Troubleshooting: hard-refresh if the old columns remain, then inspect that both Services asset URLs use `v=20261031-services-vertical`. If compact labels appear initially but disappear after Refresh, check the loaded renderer version and refreshed cells' `data-label`. A genuine empty period must show the existing message rather than fabricated records. Narrow requests intentionally change presentation while retaining all five fields and the original destinations.

Safe practice: compare empty and populated reporting periods, then Refresh and verify the same five fields, request links and dates. Narrow the browser and confirm every request stays inside its card. Follow View All without changing a request. Temporarily change the Services grid gap from 16px to 20px in DevTools, inspect the vertical spacing, then reload to restore the saved value. Confirm Users by Type remains responsive and centered. This exercise changes no saved data.

### 8. Remaining limitations

Real request text and record counts determine card height; the columns have equal available width rather than forced equal height. Normal page scrolling remains. Verification used Chromium and actual Django test-fixture exports, not a cross-browser or physical-device certification. No deployment was performed.

## Historical implementation reference

The following sections document the original implementation; the current report above supersedes their older layout, typography, asset-version and verification notes.

## 1. Cause / reason

The previous Services section had four KPI cards, one Most Requested Service sentence and a three-item request list. A separate Operational Attention section repeated pending services and upcoming facility bookings. The requested layout needs a service-only summary, useful request charts, five recent requests and one attention list, consistent with Marketplace and Facilities Overview.

Inspection confirmed there is no separate Service or ServiceRequest database model in this implementation. Service offerings reuse `api.models.Facility`; service requests reuse `api.models.Booking`, identified by the existing `service_resources_q()` helper. Its configured types cover Food Analysis, Training/Assessment and Lease, plus service/direct/assessment/lease modes. `schedule_blocks_q()` excludes structured schedules using the existing policy.

The current Service Requests page shows the five generic Booking statuses: Pending, Approved, Completed, Rejected and Cancelled. The catalog stores laboratory, assessment and lease configuration, but that is not proof that a request has reached a detailed laboratory/contract stage. This update therefore does not manufacture Awaiting Sample, For Payment, Reschedule Required or Contract Preparation Pending. It preserves those workflows and displays only supported pending requests and temporarily unavailable service offerings.

## 2. Exact files changed, current lines and nearby anchors

Paths are relative to the project root. Lines identify the relevant current anchor.

| File | Line / anchor | Change / purpose |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_executive.py` | 16 `service_overview`; 33 `rows`; 43 `series`; 67 `executive_overview` | Extends the existing projection with bounded charts, five recent rows and a current service-only attention list. Keeps the existing KPI definitions and compatibility fields. |
| `backend/core/modules/reports/dashboard_periods.py` | 158 `service_grouping`; 296 `executive_overview` call | Validates Daily/Weekly/Monthly and passes it through the existing dashboard builder. Global period and other chart parameters remain independent. |
| `backend/core/modules/reports/analytics_sections.py` | 272 `service_request_breakdown`; 333 call | Extracts the existing Services Analytics grouped query into a reusable helper. Analytics keeps grouping by name; the dashboard uses service ID plus name so distinct offerings with identical names are not merged. |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 34 `super_services_overview.html` | Uses the scoped Services include; removes the old Operational Attention block. Global audit/status sections follow it, as documented in [final operations](dashboard-system-status-design.md). |
| `backend/templates/dashboard/partials/super_services_overview.html` | 1 `data-services-overview` | New header/subtitle/actions, four summary cards, charts, five-column request table, attention list and honest empty/error states. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 26 CSS; 618–621 script anchors | Loads Services assets as `20261022-services`; the executive renderer now uses the later `20261022-audit` version. |
| `backend/static/components/css/admin_services_overview.css` | 1 executive scope; 32 responsive rules | Inter inheritance, white/navy styling, light borders, 14px corners, 60/40 desktop rows, responsive summary grid and contained table scrolling. |
| `backend/static/components/js/admin_services_overview.js` | 12 `localLink`; 29 `draw`; 71 `renderTrend`; 82 `render` | One Services renderer for the existing dashboard snapshot: chart data, KPI values, safe request links, table, attention, keyboard tooltips, empty states and missing-library fallback. |
| `backend/static/components/js/admin_dashboard_filter.js` | 27 `serviceRetryOnly`; 493 `load`; 684 service listeners | Extends the existing request controller with a chart-only Services branch, retry, cancellation cleanup and grouping URL state. No second fetch controller or endpoint. |
| `backend/static/components/js/admin_dashboard_executive.js` | 12 `fail`; 16 `render` | Keeps facility attention and Analytics navigation. Services has a single rendering owner; global activities now use the separate renderer described in [final operations](dashboard-system-status-design.md). |
| `backend/core/modules/reports/test_dashboard_services.py` | 46 service scope; 63 grouping; 86 distribution; 109 layout | New real ORM tests for supported states, physical/schedule exclusions, current versus selected dates, five-row limits, same-name service identities, destinations and optional isolated HTML/JSON fixtures. |
| `backend/core/modules/reports/test_dashboard_executive.py` | 53 recent row assertion; 160 section-order anchors | Expects four existing fixture requests rather than the former three-row truncation; removes the obsolete Operational Attention anchor from ordering. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 358 query-budget comment | Allows the three new bounded monitoring queries, while retaining the assertion that growing transaction data does not increase query count. The fixture now measures 35 queries. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 175 section-order anchors | Updates the shared page-order assertion for removal of Operational Attention. Marketplace data and presentation assertions remain. |
| `docs/dashboard-services-overview.md` | 1 | This implementation, data-flow, verification and learning report. |
| `docs/booking-overview-implementation.md` | current file map | Refreshes neighboring file anchors shifted by this update; the Facilities implementation is unchanged. |
| `CAMPUSHUB_CONTEXT.md` | 5 latest Services note | Saves the accepted design, current status limits and verified results for future work. |
| `scratch/services-overview-review/verify_renderers.cjs` | 1 | Local DOM integration harness over isolated Django fixtures; reuses the existing scratch jsdom dependency. It is not production code or a data seeder. |

## 3. Changes made / cards and responsive layout

The final section is:

```text
Services Overview                        View Services / View Services Analytics
Monitor service availability and request processing.

Service Summary
Active Services | Open Requests | Pending Requests | Completed Requests

Service Request Trend (line, 60%) | Requests by Service (vertical bars, 40%)
Recent Service Requests (60%)     | Service Attention (40%)
```

The requested sentence below the KPIs is retained: “Request counts use the selected submission period. Active Services reflects the current service catalog.”

- **Renamed/replaced:** Most Requested Service becomes Requests by Service. The original compatibility JSON value is retained, but there is no second visible popularity card.
- **Removed:** The duplicate Operational Attention / Upcoming Bookings / Pending Service Requests block. Upcoming reservations remain in Facilities Overview; no calendar information is repeated in Services.
- **Added:** Service Request Trend, grouped vertical distribution, maximum-five recent request table, and one current attention list.
- **Retained:** Global Recent Activities stays outside Services; catalog, Analytics and Service Requests destinations remain existing routes.
- **Responsive:** Below 600px, summary cards stack; from 600px they use two columns; from 1100px they use four. Charts and operations use one column below 1100px and a 3:2 split above it. The table scrolls inside its own region when its five columns need more width.
- **Style:** Existing local Inter UI type, navy `#1A1851`, white, light neutral surfaces, flat borders and restrained spacing. Requested gold `#FCB316` is limited to chart hover. SugarPie remains only the shared wordmark; no new fonts or image assets were added.

Empty periods do not construct or display a large flat zero service chart. Both charts show the exact requested explanatory empty states. Recent and attention cards also have explicit empty messages. Errors are separate from empty data; a failed service grouping request leaves distribution, recent rows and attention visible.

## 4. How it works / models, functions, inputs, outputs and data flow

### KPI definitions

| KPI | Existing source and definition | Date basis |
| --- | --- | --- |
| Active Services | Service-classified Facility rows, `is_archived=False`, status `available` (Active in the service catalog) | Current catalog, independent of reporting dates |
| Open Requests | Service-classified Booking rows currently Pending or Approved, excluding schedule blocks | Submitted in selected period |
| Pending Requests | Same scope, currently Pending | Submitted in selected period |
| Completed Requests | Same scope, currently Completed | Submitted in selected period |

The heading “Open” describes the current state of requests submitted in that period; it is not an all-date backlog. This preserves the previous implementation and the requested explanatory text. The attention list uses current requests across dates, so an older pending request can appear there when Pending Requests for the selected period is zero.

### Projection flow

1. `build_dashboard_data(params)` resolves existing dates and validates optional `service_grouping`. Unsupported grouping defaults to daily.
2. `service_overview(period, current_counts, grouping)` reuses the existing service request queryset and aggregate. Additional total/approved/closed columns share that same aggregate query. Current Active/Pending counts reuse the already-loaded dashboard aggregates when supplied.
3. `build_booking_overview(..., records=requests)` supplies existing daily/weekly/monthly bucketing and five-status validation. Only its total, trend rows, grouping and date fields are exposed as `request_trend`; physical-booking URLs are not exposed in this service trend.
4. `service_request_breakdown(selected, limit=5, by_id=True)` performs the existing Analytics count pattern, ordered highest total first, then name/ID. It counts submitted requests in all supported statuses, including rejected/cancelled, rather than silently treating them as nonexistent activity.
5. `rows(selected)` loads at most five requests with related service/user records in one query, newest submission first with a stable ID tie-break. It reuses `_booking_display_fields()` for the existing client display and exposes no email, phone, private request narrative or document contents.
6. Current pending rows are reused for attention. One bounded catalog query adds up to two unarchived unavailable offerings, including legacy maintenance/reserved/occupied values that the existing Services list presents as Temporarily Unavailable. Up to five attention items are returned; space is reserved for those catalog notices when present. Pending and unavailable reasons describe supported next actions, not inferred workflow stages.
7. The initial include embeds `servicesOverviewData`. `render()` uses it immediately. Existing full-refresh events update all cards; the existing request controller dispatches `campushub:service-trend-data` for chart-only grouping. That branch updates only the service trend.

Annotated example:

```python
service_request_breakdown(selected, limit=5, by_id=True)
# selected: the existing service-only request queryset, scoped to submitted dates.
# limit=5: dashboard-sized output; no hard-coded service names.
# by_id=True: two offerings with the same name remain separate records.
```

The output is actual grouped request counts, not demand forecasts or recommendations. The shared Analytics page calls the same helper without `by_id=True`, preserving its existing name-based breakdown and row fields.

`draw()` maps trend labels/counts to the existing Chart.js 4.4.1 line chart and actual service names/counts to vertical bars. Both charts reuse instances on refresh, allow Arrow/Home/End keyboard inspection, expose text descriptions, and reveal readable lists when the chart library fails. Long service names may be shortened on-axis; the tooltip and accessible list retain the full name. Animation is disabled, so there is no decorative motion or reduced-motion dependency.

## 5. Backend / API behavior, routes and workflow preservation

The protected Super Admin dashboard endpoint is unchanged. Its existing response gains `executive.services.request_trend`, `requests_by_service`, `attention` and supporting count fields. Existing `most_requested`, `pending_queue` and `pending_current` remain; recent/pending rows now allow five instead of three.

`service_grouping=daily|weekly|monthly` is the only new query parameter. It is independent of the existing sales `grouping` and `booking_grouping`. Dates, custom-range validation, tab authentication and permissions still use the existing shared controller. If another chart/full refresh supersedes a pending service request, the service selector returns to the last successfully rendered grouping instead of claiming the cancelled choice was applied.

Existing routes reused:

- `admin_services_page` → `/admin-services/` (View Services; unavailable attention links use its existing `status=unavailable` filter).
- `admin_service_requests_page` → `/admin-service-requests/` (View All; individual request links use existing `service` and `q` filters).
- `admin_marketplace_analytics_page` with `module=services` and selected dates → existing Services Analytics.

The Services request list's existing detail dialog remains the destination; a separate request-detail route or processing screen was not invented. Same-origin service URL validation and the existing tab token are used when refreshed links are built. No access grants, approval actions, workflow transitions, sample handling, assessment assignment, lease/contract changes or payment changes were introduced.

## 6. Database / migration impact

No schema, models or migrations changed. No production/application records, services, rates, requests or status values were seeded or updated. Test fixtures are written only in Django's isolated test database. Optional HTML/JSON under `scratch/services-overview-review/` contains those test responses.

No credentials, `.env`, SSH/tunnel, server services, Nginx, deployment or Flutter files changed. Development remains local. No APK or deployment step is required for this web-only update.

## 7. Tests performed, debugging and safe practice

- **174 Django tests passed**, covering the new service summaries plus executive dashboard, periods/query bounds, detailed Analytics, facility bookings/ranking/upcoming/revenue, Marketplace/KPIs, service navigation, mobile service catalog and service configuration. See `scratch/services-overview-tests-final.log`.
- **11/11 DOM integration scenarios passed**: real fixture KPI/chart values, linked five-row table and attention, keyboard tooltips, independent service grouping, cancellation by another request, isolated grouping error/retry, full outage/recovery, empty charts, repeated refresh without duplicate chart instances, and missing-library fallbacks. See `scratch/services-overview-dom-final.log`.
- `manage.py check`: no issues. `makemigrations --check --dry-run`: no changes detected. All three modified/new production JavaScript files passed `node --check`.
- Local Django returned **HTTP 200 with bytes matching workspace files** for the new stylesheet, renderer, shared date controller and executive renderer.
- Browser inventory returned no available browser. DOM checks do not verify pixels, actual canvas rendering, layout at viewport sizes or measured accessibility contrast. These visual checks remain outstanding.

The first run caught an invalid month-crossing date in a new test fixture and the previous query budget. The date now uses `timedelta`; the query-bound test now allows 35 queries for the three new bounded projections while still asserting identical query counts before/after transaction growth. A separate old layout test still expected Operational Attention and was corrected to the requested final section order. Final results above are passing runs, not the initial failures.

From `backend/core`, run relevant checks without activating the virtual environment:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_services modules.reports.test_dashboard_executive modules.reports.test_dashboard_periods modules.reports.test_superadmin_analytics modules.reports.test_dashboard_marketplace modules.facilities.test_service_navigation modules.facilities.test_mobile_services modules.facilities.test_service_configuration --keepdb --noinput
.\venv\Scripts\python.exe manage.py check
```

To regenerate DOM fixtures, set `SERVICES_REVIEW_DIR` to the absolute project `scratch/services-overview-review` directory and run `test_dashboard_services`. Then, from the project root, run `node scratch/services-overview-review/verify_renderers.cjs`. The harness uses the already-existing `scratch/bundle-qa/node_modules/jsdom`; it is not an application package dependency.

Troubleshooting:

- If old cards remain, press Ctrl+F5 and inspect that CSS/JS URLs end in `v=20261022-services`.
- If request KPIs are zero but attention shows a pending request, check its submission date: current attention is intentionally not restricted to the reporting period.
- If the service trend fails during grouping, use its Retry. Distribution and recent rows should remain visible. A full dashboard failure shows a distinct overview error, never fabricated zeros.
- Blank charts with the requested empty messages mean there are no eligible requests for the selected period. Do not insert demo records into the application database to fill them.
- An unavailable service link opens the existing filtered catalog; request links open the existing filtered request list and detail dialog.

Safe learning exercise: in browser DevTools, temporarily change `.services-grid` from `3fr 2fr` to `1fr 1fr` at desktop width, compare the two rows, then restore it. Narrow the window to confirm rows stack and the table scrolls within its card. Change service grouping and confirm facility/sales grouping and the request table do not change. This exercise edits no stored data.

## 8. Remaining limitations

Detailed laboratory, assessment or lease lifecycle attention cannot be displayed reliably until corresponding authoritative request stages and helpers exist; this monitoring update does not add them. Current attention is bounded to five items, with at most two catalog notices; the existing View Services and View All links lead to full lists. Historical requests remain counted even if their offering is now inactive/archived, as in the existing request summaries. Current status counts do not reconstruct a historical status timeline. Visual browser QA remains unverified; no deployment was performed.

## 9. Services Overview container flattening — October 31, 2026

### 1. Cause / reason

The Services Overview was the only domain still wrapped by the shared `.executive-domain-grid > .executive-section` container rule in `admin_executive_refinement.css` (padding, border, radius and surface). Marketplace and Facilities had already opted out of that outer box, so Services looked like one large panel around its heading, KPIs, charts and tables. Two cards were also hidden inside `<details class="executive-supplement">` summaries, which duplicated their `<h3>` titles and required an extra click. The requested treatment is the same card language as the rest of the executive dashboard: one plain section heading, then four independently bordered cards with 16px gaps.

### 2. Exact files changed, current lines and nearby anchors

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/super_services_overview.html` | 1 `data-services-overview`; 9–15 KPI block; 17–73 four cards | Removes both `<details>/<summary>` wrappers, adds `services-card` classes, and moves every title, subtitle and control into a `services-card-header`. All chart, table, filter, View All and data hooks are unchanged. |
| `backend/static/components/css/admin_services_overview.css` | 5–11 outer section; 20–27 card surface; 29–34 card header; 40–43 compact empty states; 60–62 grid gaps | Makes the section transparent, gives each monitoring card its own border/padding, constrains header layout, compacts empty states and fixes 16px gaps. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 26 `20261031-services-layout` | Cache-busts the changed Services stylesheet. |
| `backend/core/modules/reports/test_dashboard_services.py` | 128–131 | Regression checks: no `<details>` or `<summary>` inside Services, exactly four `dash-card services-card` containers. |
| `docs/dashboard-services-overview.md` | this section | Implementation, data-flow and verification notes. |
| `CAMPUSHUB_CONTEXT.md` | top entry | Records the accepted final layout. |

### 3. Changes made

- The outer `executive-services` section no longer draws a border, padding or background; it now only holds the **Services Overview** heading and the content stack.
- `Service Request Trend`, `Requests by Service`, `Recent Service Requests` and `Service Attention` are four `.dash-card.services-card` containers. Each has `1px solid #E8EAF0`, a 10px radius, 16px padding and a white surface.
- Each card header now contains its own title, subtitle and, where applicable, controls: the Daily/Weekly/Monthly grouping select on the trend card and the existing **View All** link on Recent Service Requests.
- The duplicated accordion summaries were removed. The real `<h3>` elements remain and still supply `aria-labelledby`.
- Empty states keep their existing messages and icons but lose the reserved 130px chart height and large padding, so an empty card ends close to its content.
- KPI, chart and table content, columns, destinations and JS hooks are unchanged.

### 4. How it works / functions and data flow

The template keeps `data-services-overview`, `data-services-content`, every `data-service-*` hook, both canvas IDs, `serviceGroupingSelect`, the five table columns, and `servicesOverviewData`. `admin_services_overview.js` still finds these nodes by ID/data attribute and still owns chart drawing, KPI text, table rows, attention rows and empty-state toggling. `admin_dashboard_filter.js` still dispatches `campushub:service-trend-data` and reads `data-rendered-grouping` from the section. No selector depended on the removed `<details>` elements.

CSS specificity note (beginner-friendly): the shared refinement rule `[data-global-dashboard] .dashboard-executive .executive-domain-grid > .executive-section` gives every domain section a border. The Services stylesheet now uses `.executive-section.executive-services` (one extra class) to win and make only this section transparent. The card rule uses `.services-card.dash-card` so it also outranks the generic `.executive-domain-grid .dash-card` border reset. This is why the layout changes without touching the other dashboard sections.

### 5. Backend / API behavior

Unchanged. No view, URL, permission, query, or JSON field was modified. The page still renders the same `executive.services` projection and the same `service_grouping` request parameter.

### 6. Database / migration impact

None. No models, migrations, records, fixtures, environment files or deployment settings changed.

### 7. Tests performed

- `manage.py test modules.reports.test_dashboard_services modules.reports.test_dashboard_executive modules.reports.test_dashboard_periods modules.reports.test_dashboard_empty_states --keepdb --noinput` ? **69 tests passed** before the new regression assertions were added.
- `manage.py test modules.reports.test_dashboard_services --keepdb --noinput` ? **8 tests passed** including the new no-accordion/four-card checks.
- `manage.py check` ? no issues. `makemigrations --check --dry-run` ? no changes detected.
- Not verified: pixel rendering, canvas drawing and responsive breakpoints in a real browser (no browser available in this session).

### 8. Remaining limitations

The visual result (actual spacing, wrapping and chart sizing at each viewport) still needs a browser check with Ctrl+F5 so the `20261031-services-layout` stylesheet is loaded. The executive domain grid still places Services in the same column as before; this change only flattens its outer box and gives each card its own boundary.

Safe learning exercise: open DevTools, select the Services section, and toggle its `executive-services` class off/on to see the shared outer border return and disappear. Then change `--service-border` in the `.executive-services` rule to another neutral color, confirm the four card outlines change together, and restore it. No stored data is edited.

## 10. Service Summary moved into Service Request Trend — October 31, 2026

### 1. Cause / reason

The previous flattening pass left the four Service Summary KPI cards in a separate block above the card grid. Marketplace and Facilities group their summary metrics with their main trend card, so Services looked inconsistent. The request was to place the Service Summary inside the Service Request Trend card, following the Marketplace Sales Summary arrangement.

### 2. Exact files changed and anchors

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/super_services_overview.html` | 10–34 trend card; 11–18 summary block | `Service Summary` title, four KPI cards and the explanatory note now live inside the `service-trend` article, directly above the `Service Request Trend` header and grouping select. |
| `backend/static/components/css/admin_services_overview.css` | 13–27 | Summary title/note spacing retained; KPI cards now use 16px padding, 14px radius, 13px labels and 28px values to match the Marketplace summary metrics. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 26 `20261031-services-summary-trend` | Cache-busts the Services stylesheet. |
| `backend/core/modules/reports/test_dashboard_services.py` | 131–136 | Asserts the Service Summary, grouping select and four metric hooks are inside the trend article. |
| `docs/dashboard-services-overview.md` | this section | Change record. |
| `CAMPUSHUB_CONTEXT.md` | top entry | Updated final Services arrangement. |

### 3. Changes made

- Removed the standalone summary block that sat above the `.services-grid`.
- The first card now renders, in order: **Service Summary** heading, four KPI cards, the period note, **Service Request Trend** heading/subtitle with the Daily/Weekly/Monthly select, then the chart and its states.
- The other three cards (`Requests by Service`, `Recent Service Requests`, `Service Attention`) are unchanged.
- KPI cards keep their data hooks and now match the Marketplace summary metric card sizing.
- Gaps stay at 16px between the summary cards and between card containers.

### 4. How it works / data flow

The KPI values still come from `executive.services` and are still written by `admin_services_overview.js` via `[data-service-metric="..."]`. Moving them inside the trend article does not change any selector: the script searches the whole `[data-services-overview]` root. The grouping select remains `#serviceGroupingSelect`, and `admin_dashboard_filter.js` still reads and updates it. The trend canvas and all empty/error/fallback hooks are unchanged.

### 5. Backend / API behavior

Unchanged. Same dashboard endpoint, same service projection, same `service_grouping` parameter.

### 6. Database / migration impact

None.

### 7. Tests performed

- `manage.py test modules.reports.test_dashboard_services --keepdb --noinput` ? **8 tests passed**, including the new assertion that the Service Summary and all four KPI hooks are inside the trend article.
- No browser visual verification was available.

### 8. Remaining limitations

Actual pixel spacing and chart resizing inside the taller trend card still need a browser check with Ctrl+F5. The trend card remains in the same executive grid column as before; only the summary placement and metric styling changed.

Safe practice: in DevTools, select the `service-trend` article and confirm `Service Summary` and `Service Request Trend` are both direct descendants. Temporarily set `.services-kpis { grid-template-columns: 1fr; }` in the stylesheet, compare the stacked and two-column layouts, then restore it.
