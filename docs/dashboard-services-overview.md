# Super Admin Services Overview — October 22, 2026

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
