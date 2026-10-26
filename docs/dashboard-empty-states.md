# Super Admin dashboard empty states

Current implementation: October 22, 2026. This guide owns the empty-state presentation update. Existing Marketplace, Facilities, Services, bundle, and operations guides still describe their data definitions and workflows; their older empty-state wording is superseded here.

Latest placement update: see [the current top-layout report](dashboard-system-status-design.md). System Health is now a compact row above Welcome; the two bundle groups are in the right-side top panel; Attention Required follows the combined area. The health row uses compact text instead of the larger shared empty component, while retaining checking/unavailable/verified states. Other empty-state behavior described here remains in effect.

## 1. Cause / reason

Confirmed by inspecting the templates and refresh handlers: empty cards used different titles, sizes and spacing; Recent Orders and Inventory Alerts retained empty table headers; some chart renderers constructed zero-only charts even when their canvas was hidden. Facility Attention showed three zero warning rows. Missing health responses showed individual Unknown labels instead of explaining that health information was unavailable.

The change standardizes presentation without inventing transactions or changing eligibility, aggregation, availability, approval or payment rules. Existing Inter, navy `#1A1851`, muted `#626781`, white surfaces, card borders and filters are reused. SugarPie remains a wordmark font.

## 2. Exact files changed

Paths below are relative to the project root. Current line numbers and nearby anchors identify the relevant code; later edits may move them.

| File | Current line / nearby anchor |
| --- | --- |
| `backend/templates/dashboard/partials/empty_state.html` | 2 `ch-dashboard-empty` |
| `backend/static/components/css/admin_dashboard_empty.css` | 1 `One quiet`; 11 `Remove legacy`; 16 `Request regions`; 28 `@media` |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 28 `admin_dashboard_empty.css`; 619 `admin_dashboard_filter.js`; 623 `admin_system_status.js` |
| `backend/templates/dashboard/partials/super_marketplace_sales.html` | 33 `sales-overview__empty` |
| `backend/templates/dashboard/partials/super_marketplace_products.html` | 7 `data-products-empty` |
| `backend/templates/dashboard/partials/recent_orders.html` | 4 `aria-labelledby="recentOrdersTitle"`; 10 `data-recent-orders-empty` |
| `backend/templates/dashboard/partials/low_stock_card.html` | 7 `class="low-stock-table"`; 25 `data-low-stock-empty` |
| `backend/templates/dashboard/partials/attention_required.html` | 14 `dashboardAttentionEmpty`; 15 `dashboard-attention-error` |
| `backend/templates/dashboard/partials/super_facilities_overview.html` | 20 `facility-booking-chart-wrap`; 21 `data-booking-empty`; 41 `data-facility-attention-empty` |
| `backend/templates/dashboard/partials/most_booked_facilities.html` | 5 `data-facility-ranking-chart-wrap`; 23 `data-facility-ranking-empty` |
| `backend/templates/dashboard/partials/upcoming_reservations.html` | 23 `data-upcoming-empty` |
| `backend/templates/dashboard/partials/super_services_overview.html` | 24 `data-service-trend-empty`; 34 `data-service-distribution-empty`; 47 `data-service-recent-empty`; 52 `data-service-attention-empty` |
| `backend/templates/dashboard/partials/system_activity_preview.html` | 12 `data-activities-empty` |
| `backend/templates/dashboard/partials/system_status.html` | 8 `dashboard-service-list`; 57 `data-system-unavailable`; 58 `dashboard-system-checking` |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 17 `zero_copy=` |
| `backend/templates/dashboard/partials/kpi_secondary.html` | 1 `suppress_zero_copy` |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html` | 18 `empty_state.html` |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_activity.html` | 7 `empty_state.html` |
| `backend/static/components/js/admin_dashboard_filter.js` | 23 `const regions`; 29 `function regionState`; 289 `lowStockContent.querySelector`; 334 `data-recent-orders-empty`; 367 `recordedFreeSales`; 527 `regionState('loading` |
| `backend/static/components/js/admin_dashboard_executive.js` | 12 `function fail`; 16 `data-facility-attention-empty`; 30 `closest('li` |
| `backend/static/components/js/admin_sales_overview.js` | 69 `function updateChartVisibility`; 98 `function ensureChart` |
| `backend/static/components/js/admin_marketplace_products_chart.js` | 16 `function sync`; 51 `function createChart` |
| `backend/static/components/js/admin_booking_overview.js` | 98 `canvas.parentElement.hidden = overview.total` |
| `backend/static/components/js/admin_most_booked_facilities.js` | 25 `if (!rows.length)` |
| `backend/static/components/js/admin_system_status.js` | 6 `footerLabels`; 17 `function render`; 27 `verified =` |
| `backend/core/modules/reports/test_dashboard_empty_states.py` | 18 `class EmptyComponentTests`; 51 `class DashboardEmptyStatesTests`; 65 `test_initial_zero` |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 363 `No Sales Data Yet`; 382 `test_zero_value_paid` |
| `backend/core/modules/reports/test_dashboard_services.py` | 123 `No Service Request Data Yet` |
| `backend/core/modules/reports/test_dashboard_periods.py` | 455 `No Items Require Attention` |
| `backend/core/modules/reports/test_upcoming_reservations.py` | 125 `No Upcoming Reservations` |

The guide itself is `docs/dashboard-empty-states.md`; the latest context note is at `CAMPUSHUB_CONTEXT.md:3`. The isolated DOM harness is `scratch/dashboard-empty-review/verify_empty.cjs:1`. Scratch fixtures and logs are verification artifacts, not application data or dashboard sources.

## 3. Changes made

The shared `dashboard/partials/empty_state.html` partial takes `title`, `description`, `icon`, and optional `left`. It reuses the existing `marketplace_icon.html` outline SVGs. The SVG is decorative (`aria-hidden`, not focusable); the title and explanation remain real text. The caller retains the original `data-*` hook and `hidden` state so existing renderers can show/hide the component without rebuilding its contents.

The shared executive-only stylesheet supplies 28px icons, Inter 15px/600 titles and 13px/400 descriptions, a 48-character description width, compact padding, wrapping, and a small-screen padding adjustment. It removes old minimum-height spacing from empty wrappers and respects `hidden` even where legacy classes set `display`. No new decorative containers, gradients, or action buttons were added.

Updated cards and states:

| Area | Empty-state title | Behavior |
| --- | --- | --- |
| Sales Trend | No Sales Data Yet | Hide canvas and legend; preserve grouping |
| Top-Selling Products | No Top-Selling Products Yet | Hide canvas; no fake product bars |
| Recent Orders | No Recent Orders | Hide the whole empty table, preserve card header |
| Inventory Alerts | No Inventory Alerts | Hide table including column headers |
| Suggested Product Bundles | No Bundle Suggestions Yet | Preserve permission gate and server-rendered error branch |
| Recommendation Activity | No Recommendation Activity Yet | Preserve real activity totals and error branch |
| Booking Trend | No Booking Data Yet | Hide zero-only chart; retain grouping and summary |
| Most-Booked Facilities | No Booked Facilities Yet | Hide ranking chart and list when no eligible rankings |
| Upcoming Reservations | No Upcoming Reservations | Preserve existing future/approved eligibility and hidden table |
| Facility Attention | No Facility Attention Needed | Hide zero warning rows; retain positive actionable rows |
| Service Request Trend | No Service Request Data Yet | Retain existing no-data chart guard |
| Requests by Service | No Service Request Activity Yet | Retain existing no-data distribution guard |
| Recent Service Requests | No Recent Service Requests | Preserve hidden empty table |
| Service Attention | No Service Attention Needed | Preserve existing actual attention items |
| Attention Required | No Items Require Attention | Separate refreshing/error messages; no empty-success message on error |
| Recent System Activities | No Recent System Activities | Preserve hidden table and protected details action |
| System Status | System Status Unavailable | Show only when no verified check result is available |

All supporting descriptions use the requested wording. KPI zeros use the requested short, context-specific explanations. A completed paid order worth zero remains real activity: the revenue KPI retains the existing “No marketplace revenue” explanation instead of falsely claiming there were no completed paid sales.

## 4. How it works: functions, inputs, outputs, and data flow

1. Existing Django dashboard queries build the same context and protected JSON snapshot as before. Initial templates choose `hidden` based on those values. Empty table bodies contain no invented rows.
2. `empty_state.html` turns caller-supplied labels into escaped HTML. It never queries the database or decides whether a booking/order qualifies.
3. The existing `admin_dashboard_filter.js` request still owns refresh, date filters, grouping, aborts, retry, history and tab authentication. `regionState(state, chart)` takes `loading`, `ready` or `error`, plus an optional chart-region key; it updates presentation attributes on existing cards. A small status paragraph marks refreshing; CSS suppresses empty-success copy during loading and errors. Existing populated data may remain visible while updating, with the existing busy/stale indicators.
4. `renderRecentOrders(orders)` builds actual order rows using text nodes and toggles the persistent empty component and entire table wrapper. `renderLowStock(snapshot)` keeps its existing ready/error checks and toggles the table separately from the empty component. Neither changes stock calculations.
5. KPI refresh reads `metric.value`, `metric.secondary_text`, and each template's `data-zero-copy`. Only displayed zero copy changes. The existing `sales_overview.has_sales` guards the free-sale exception on initial load and refresh.
6. Sales `ensureChart()` and product `createChart()` lazily create the existing Chart.js instance when eligible rows arrive. Booking/ranking renderers return before drawing for an empty result. Existing charts are retained hidden when changing to an empty period and reused on recovery. Services already guarded zero-only data; that behavior is retained. Chart-library failures remain separate from empty-data states, with the existing text fallbacks.
7. Facility Attention's existing renderer validates its three counts, hides individual zero rows, and shows the shared component only when all valid counts are zero. Invalid/missing counts show the existing error, not an all-clear message.
8. System Status still calls the existing `system_status_only=1` endpoint. `render(statuses, checking)` accepts only existing allowed internal status keys with valid check timestamps. Pending/unverified values remain Unknown and cannot clear a previously verified warning through the status event. The footer hides unverified rows behind the shared unavailable message. Verified failures remain visible health results, rather than being confused with missing data. Footer labels are Operational / Degraded / Unavailable; underlying keys and status-dot styling remain unchanged. Other contexts retain their prior labels.

Example: after a period refresh, an actual empty orders array causes `renderRecentOrders([])` to clear the body, hide `.recent-orders-table-wrap`, and reveal `[data-recent-orders-empty]`. A failed HTTP request instead hides that empty component and shows the existing Retry error. It does not turn the failure into an empty successful response.

Bundle cards retain their existing server-rendered snapshot lifecycle and server error handling. They are not silently refreshed by date/grouping requests; no duplicate bundle API, mining request or synthetic fallback was introduced. Reload the page to refresh those snapshots.

## 5. Backend / API behavior

No Django views, models, queries, routes, calculations or permission classes changed. Existing dashboard API, Activity Detail API, Analytics destinations, bundle monitoring permissions and existing health checks remain authoritative. FastAPI remains messaging only. No new forecast, revenue interpretation, booking stage, stock rule or recommendation algorithm was added.

The health timestamp validation is frontend validation of existing responses. It does not perform a new health check or change server health calculations. An individually checked unavailable service still appears as Unavailable, with its real check time and message.

## 6. Database / migration impact

None. No application records were added, deleted or updated. The ORM fixtures used below run in the isolated Django test database and roll back. They are never imported into the development database. No schema/migration, `.env`, credentials, server deployment, SSH tunnel, mobile build or remote database changes were made.

## 7. Tests performed and how to verify

- **240 Django regression tests passed**, covering dashboard summaries/eligibility/query bounds, Facilities/Services separation, ranking/upcoming logic, health checks, activity permissions/privacy, bundle suggestions/monitoring and the new empty-state tests. Log: `scratch/dashboard-empty-final-tests.log`.
- After the final shared-template scope review, **13 focused tests also passed**, covering the new empty-state tests, existing domain dashboards and KPI integration. The Marketplace Admin attention partial keeps its prior presentation and does not show the Super Admin-only error message. Log: `scratch/dashboard-empty-scope-tests.log`.
- New isolated ORM test exports zero, one and multiple actual test records to `scratch/dashboard-empty-review/`. It checks the initial hidden chart/table wrappers, all requested titles, real API counts, future reservations and decorative/escaped shared component output. Bundle server failures are explicitly tested as errors, not empty successes.
- **53 DOM scenarios passed**: 20 empty-state, 13 audit/status, 11 Services and 9 Facilities scenarios. Log: `scratch/dashboard-empty-final-dom.log`. These execute production handlers against isolated Django responses, including empty-to-populated-to-empty, chart reuse, loading, HTTP 503, retry, grouping, missing Chart.js, private detail handling and missing/verified health results. Ranking remains empty when bookings are scheduled outside the ranking period; the separate Facilities scenarios exercise actual eligible ranking data. No chart values were forced into the application.
- `manage.py check`: no issues. `manage.py makemigrations --check --dry-run`: no changes detected.
- Seven changed JavaScript files passed `node --check`.
- The new CSS and all seven changed scripts returned HTTP 200 from the running local server, with bytes matching workspace files. Cache query versions were updated in the template.
- Calculated sRGB contrast on white: navy **16.24:1**, description gray **5.56:1**. This checks the specified text colors, not every existing page element or full WCAG conformance.

To repeat focused UI verification from the project root:

```powershell
node .\scratch\dashboard-empty-review\verify_empty.cjs
```

For the new Django tests, from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_empty_states --keepdb --noinput
```

Manual browser checks: open the existing Super Admin dashboard, hard-refresh once, select an empty reporting period and compare with a populated one. Verify the filters, View All links, small outline icons, wrapped descriptions and hidden table headers. Refresh during an empty result: it should say Updating rather than claiming a new empty result. On a real error, use Retry; do not clear or insert production records to force a visual state. Check at desktop, tablet and narrow browser widths.

Troubleshooting:

- Old text: confirm the Super Admin executive branch is active, reload the HTML, and inspect the `20261022-empty` script/CSS URLs. A browser-cached HTML page can still reference old scripts.
- Old-looking wrapper spacing: inspect whether `admin_dashboard_empty.css` loaded after the older card styles; the shared message must be inside the existing wrapper. Do not globally remove card styles.
- Missing chart but real data: check whether this is an empty eligible projection or a Chart.js error. Existing chart-error messages/text summaries are intentionally different from empty states.
- Health unavailable: check the health-only HTTP response and actual per-component timestamps. Do not set a hardcoded Operational label to suppress an outage.
- Bundles do not change with dates: they retain their existing page-load snapshot lifecycle; reload the page. Date filters still affect the existing period-based sections only.

Safe practice exercise: change only the shared component's description `max-width` in `admin_dashboard_empty.css:9` from `48ch` to `44ch`. Reload a narrow dashboard and confirm descriptions wrap without horizontal scrolling, then restore `48ch`. Run the focused DOM test afterward. This teaches a presentation-only change; do not edit query counts or create live records to test spacing.

## 8. Remaining limitations

No enabled browser surface was available (`apps: [], browsers: []`), so actual screenshot layout, responsive pixels, native dialog keyboard behavior, screen-reader output and Chart.js canvas drawing were not visually verified in this update. DOM tests use a chart stub; they verify the data, lifecycle and visibility, not rendering fidelity. The numerical contrast check is not an accessibility certification.

The initial HTML page still requires successful existing server queries. The update improves existing rendered cards and API error/retry states; it does not invent a successful initial dashboard during a full server/database outage. Existing bundle snapshots remain page-load based. No online deployment was performed.
