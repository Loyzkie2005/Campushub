# Super Admin System Overview cards - October 22, 2026

Current global web typography (October 22, 2026): Inter now applies to these web cards through the shared `web_typography.html` include, local `InterVariable.woff2` and `web_typography.css`. SugarPie remains the wordmark only. Older Montserrat/Roboto descriptions below are historical. See [the current global typography and Marketplace Overview report](dashboard-marketplace-design.md) for exact files, functions/data flow, tests, troubleshooting and safe exercises. Flutter typography is unchanged.

This current report supersedes the older layout notes below. Only System Overview was restyled; the established dashboard sections and accounting definitions remain in place.

## 1. Cause / reason

The eight cards used the older ordering, 8px corners, and inconsistent text hierarchy. Shared `admin_layout.css` also forces Roboto on links, labels and numbers with `!important`, so merely declaring Montserrat on a card did not work. On narrow phones the shared sidebar left too little room for two cards and their icons. Super Admin additionally invoked live association mining before reading the saved recommendation preview.

Confirmed fixes: explicit DOM order, scoped Montserrat exception, 14px corners, a one-column narrow-phone breakpoint, and a saved-results-only Super Admin recommendation branch. No new KPI query/calculator/controller was introduced.

## 2. Exact files changed and current anchors

| File | Line / anchor | What changed |
| --- | --- | --- |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 5 `dashboardKpiStale`; 6 `dashboard-overview-kpis`; 8 first `dashboard-kpi-link` | Reordered the existing eight cards, put labels before values in reading order, reused SVGs and `kpi_secondary.html`, linked seven existing modules and added last-loaded notice. Revenue at 72 uses grouped two-decimal pesos. |
| `backend/static/components/css/admin_dashboard_summary.css` | 13 overview grid; 15 card; 25 typography exception; 27 links; 76 narrow breakpoint | Four/two/one columns, 132px minimum card height, 16px padding, 12px gaps, 14px corners, #E8EAF0 border, white/navy surface, visible 3px keyboard outline. Scoped to the existing global dashboard. |
| `backend/static/components/js/admin_dashboard_filter.js` | 13 `kpiStale`; 30 `wrapMoney`; 332 `render`; 575 failure branch | Reuses the existing request and refresh flow. Adds optional wrap points after currency grouping commas; identifies retained values after failed refresh and clears that notice after success. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 23 summary stylesheet; 615 filter script | Cache versions `20261022-kpi-cards` so changed CSS/JS can reload. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py` | 40 `dashboard_bundle_suggestions` | Super Admin GET reads existing saved live recommendations/activity without calling `build_bundle_suggestions`. Marketplace Admin and Analytics retain their existing calculator. |
| `backend/core/modules/reports/views.py` | 12 DatabaseError import; 1262 API exception | A database snapshot failure returns a generic HTTP 503 JSON error, without invented totals or private exception details. |
| `backend/core/modules/reports/test_dashboard_kpi_cards.py` | 17 `SystemOverviewCardsTests` | New isolated tests for order, all seven real destinations, initial/API value consistency, large legal aggregate, no render-time mining, and error response. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 273 saved-result dashboard test; 464 populated fixture | Updated Super Admin expectations from unused computed rows to saved preview rows; explicit test-only refresh still populates isolated fixtures. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 138 legacy timestamp test; 372 attention test | Updated older tests to current booking-row `date`, approved-booking receipt eligibility, and the previously requested header System Status position. No facility behavior was changed. |
| `backend/core/modules/reports/test_dashboard_executive.py` | 87 section test | Updated obsolete three-recommendation-card assertions to the established two-card recommendations/activity layout. |
| `docs/dashboard-kpi-refinement.md`, `docs/suggested-product-bundles.md`, `CAMPUSHUB_CONTEXT.md` | Start of file | Current report and project handoff note. |

The scratch `dashboard-kpi-cards/` directory contains clearly labelled isolated test renderings, captured test JSON, and a loopback-only preview helper. It is not an application feature or an imported dataset.

## 3. Changes made / expected behavior

Desktop row 1: **Total Users -> Active Sellers -> Total Products -> Total Orders**.

Desktop row 2: **Marketplace Revenue -> Total Facilities -> Total Bookings -> Pending Approvals**.

The existing four-column desktop rule becomes two columns below 1280px, and one below 480px. Cards share dimensions within each row and grow to contain long real content. Small icons support the label; navy numbers carry the strongest emphasis. No gradients, decoration, new charts, or card entrance animation were added. Gold remains the existing institutional #FCB315 attention accent.

Seven whole-card links use existing route names: `admin_users_page`, `admin_sellers_page`, `admin_products_page`, `admin_orders_page`, `admin_marketplace_analytics_page`, `admin_facility_page`, `admin_bookings_page`. These open their established module listings; existing destination RBAC and filters still apply. Pending Approvals stays informational because its aggregate spans product, seller, physical booking and service queues; existing Attention Required links reach each actual queue. No misleading single-queue link was added.

## 4. How it works: functions, inputs, outputs and data flow

`build_dashboard_data(params, today=None, legacy=False)` in `backend/core/modules/reports/dashboard_periods.py:145` remains the canonical source. Query/date parameters enter the existing period resolver; existing grouped ORM reads produce eight `kpis` objects, period metadata, trends and operational sections. The page adapter in `reports/views.py:720` maps those values to `dashboard_stats`; the partial renders them and retains every `data-dashboard-kpi` / `data-dashboard-secondary` hook. The unchanged `kpi_secondary.html` presents comparison/empty text.

The existing refresh request fetches one complete snapshot, not eight per-card endpoints. `render(payload)` updates the same elements. A successful zero remains a real zero. Request failure keeps the prior snapshot, displays Retry plus "Showing last loaded values", and never replaces values with zero. `wrapMoney(text)` adds invisible optional break positions after commas, retaining every digit and the decimal amount. For example, a legal aggregate of 130 isolated paid/completed orders of PHP 99,999,999.99 displays **PHP 12,999,999,998.70**; narrow cards can wrap between thousands groups.

Preserved counting definitions (these are not new reporting policies):

| KPI | Existing source and counting rule |
| --- | --- |
| Total Users | `accounts.User.objects.aggregate(Count('pk'))`, all stored accounts including admins and inactive/suspended accounts. This preserves the existing User-table scope; it does not newly merge the separate mobile identity table. |
| Active Sellers | Distinct active, nonsuspended `accounts.User` accounts with approved nonsuspended seller access, plus the established legacy `Seller` role compatibility. Suspended seller requests exclude the account. Multiple applications/products do not multiply the user count. Separate mobile identities are not newly merged. |
| Total Products | Nonarchived `api.Product` records. Existing bundle products are Product records and remain included once. Approval statuses retain the existing definition. |
| Total Orders | Real `MarketplaceOrder` records created in the selected reporting period, with the existing all-order-status policy. Synthetic research CSV rows are separate and never queried for these KPIs. |
| Marketplace Revenue | Existing `valid_sales_queryset()` at `marketplace/services/analytics.py:109`: completed + paid + positive quantity, sum stored order `total_price`, date by completed_at then paid_at then created_at. One order contributes once; no payment joins. Unpaid, cancelled and other ineligible statuses do not contribute. |
| Total Facilities | Existing all-record `Facility` aggregate, including stored inactive/archived records and service resources represented in that model. The separate service/physical operational summaries retain their existing boundaries. |
| Total Bookings | Existing executive physical-facility booking overview in the selected submission period, excluding service resources and academic schedule blocks. |
| Pending Approvals | Existing current snapshot of pending nonarchived products + pending seller request records + pending booking records. Shared Booking storage includes service requests, labelled separately in the secondary breakdown; each row is counted once. This is current workload, independent of reporting dates. |

The dashboard no longer mines bundles during Super Admin GET. `dashboard_bundle_suggestions(user, limit=2)` reads the existing `BundleRecommendation` rows and existing activity helper, respecting the existing scopes and separate failure states. Generating/updating saved recommendations still requires the established explicit refresh workflow. Support, Confidence and Lift are not exposed on this dashboard.

## 5. Backend / API behavior

No routes, permissions, approval transitions or accounting formulas changed. `admin_dashboard_api` retains authentication and Super Admin authorization. Database snapshot exceptions now return HTTP 503 with `{ "error": "Dashboard data is unavailable. Please retry." }`; no `kpis` object is returned on failure. Bad date parameters remain HTTP 400. Existing loading, date, chart, system-status, recommendations and other sections remain wired to their current services.

## 6. Database / migration impact

No models, migrations, schema changes or application record writes. Test records were created inside Django's isolated test database and rolled back. Read-only application count after testing: **15 products, 1 order, 0 saved recommendations**, matching the pre-change counts. No .env, server, deployment, APK or SSH changes.

## 7. Tests performed

Executed successfully after implementation:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\backend\core
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_kpi_cards modules.reports.test_dashboard_periods modules.reports.test_dashboard_executive modules.marketplace.test_bundle_suggestions modules.marketplace.test_bundle_monitoring modules.reports.test_dashboard_marketplace --keepdb --noinput
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

**131 tests passed**; Django system checks clean; no migration changes. `node --check backend/static/components/js/admin_dashboard_filter.js` also passed from the project root. Log: `scratch/dashboard-kpi-cards-tests.log`.

Browser QA used clearly labelled HTML rendered by isolated Django test records, the real CSS/JS, and a loopback fixture server; it did not impersonate an application user or import preview records. Verified four desktop columns (normal viewport), two at 768px, one at 390px and 320px; all eight KPI cards had zero horizontal overflow. At 390px document client/scroll widths were 375/375; tablet 753/753. Verified Montserrat, grouped long currency, keyboard navigation with 3px focus outline, visible loading, a simulated HTTP 503 retaining prior values, and a later successful refresh clearing both error/stale indicators. Preview server stopped; browser viewport reset and temporary tab closed.

## 8. Remaining limitations and troubleshooting

- Existing counts intentionally preserve their established scope, including the User-table-only account/seller snapshots and all-record Facility total. They are not a new deduplicated count across web/mobile identity tables. A future change to those reporting definitions must update the shared calculator and its tests rather than only changing the card.
- Live recommendations still require sufficient real multi-item history and explicit saved-result refresh; no scheduler or fabricated fallback was added. Marketplace Admin/Analytics behavior is unchanged.
- A full initial-page database outage still fails the server request; the graceful 503/retry behavior tested here applies to the existing dashboard JSON refresh. No fake initial totals are rendered.
- At a 320px viewport, the complete shared page measured 317px scroll width against 305px client width; KPI cards themselves had zero overflow. The extra shared-shell width outside the KPI grid was not changed in this scoped task. Wider tested layouts fit.
- No production deployment, authenticated live-browser session, full-project test suite or formal WCAG certification was performed.
- If CSS looks unchanged, hard-refresh with Ctrl+F5 and verify the page requests `admin_dashboard_summary.css?v=20261022-kpi-cards`. Check that the signed-in account uses the global dashboard, not the separate Marketplace/Facility Admin page.
- If totals look unexpected, compare the selected dates and counting table above with the existing API snapshot; do not replace backend failures with zeros. Bundle preview emptiness is independent of KPI loading.

### Safe learning exercise

In `admin_dashboard_summary.css:15`, temporarily change only card `padding: 16px` to `18px`. Refresh the local dashboard and resize to desktop/tablet/phone. Confirm all eight labels and amounts fit and keyboard focus remains visible. Restore 16px and refresh again. Do not edit database totals or add records to make the page look populated. This exercise changes presentation only; the request -> shared calculator -> template/refresh data flow stays unchanged.

---

# CampusHub KPI card refinement

## Cause / reason

The revised brief calls for compact, consistent secondary lines, meaningful zero states, neutral snapshot additions, and percentage text without unnecessary decimals. The previous implementation wrapped secondary text, displayed generic comparisons on empty booking/revenue periods, and listed all-zero pending categories.

## Exact files changed, approximate lines, and anchors

| Folder / file | Approximate line | Nearby anchor | Change |
| --- | ---: | --- | --- |
| `backend/core/modules/reports/dashboard_periods.py` | 79 | `def comparison_metric` | Percentage display trims redundant decimals; short New activity and both-zero secondary text. |
| Same file | 104 | `def period_metric` | New shared wrapper for neutral, card-specific empty-period wording while retaining actual previous values and calculated percentages. |
| Same file | 194 | `seller_text` | No-active-seller dash and neutral +count wording for recorded approvals. |
| Same file | 199 | `kpis =` | Neutral user/product +counts; no-pending empty state; specific orders/bookings/revenue empty states; concise unavailable facility label. |
| `backend/static/components/css/admin_dashboard_filter.css` | 22 | `.dashboard-stat-card > div` | Flexible text area, one-line secondary text, common minimum line height/spacing/alignment, and ellipsis for overflow. |
| `backend/static/components/js/admin_dashboard_filter.js` | 29 | `updateSecondaryTitles` | Full-text hover title only for clipped secondary lines; recalculate on data update, resize, and font readiness. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 156 | `data-dashboard-kpi="marketplace_revenue"` | Match requested currency spacing. Updated asset versions at lines 16 and 608. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 63 | `test_percentage_display` | Whole/fractional/tiny changes and zero-baseline wording tests. |
| Same test file | 188 | `test_kpi_specific_zero_states` | All eight descriptions, neutral zero states, and preservation of real previous values. |
| Same test file | 212 | `test_free_completed_sales` | A completed paid zero-value order is not described as missing sales. Today markup expectation updated for short KPI New activity text. |
| `scratch/dashboard-global-review/check-controls.cjs` | 48 | `checkKpis` | Verify single-line text, shared spacing, semantic updates, whole percentages, and conditional hover titles. |
| `scratch/dashboard-global-review/dashboard.html` | 1 | Review HTML | Regenerated server-rendered page from isolated Django test records. |
| `scratch/dashboard-global-review/payload.json` | 1 | `kpis` | Regenerated seven-day API review response. |
| `scratch/dashboard-global-review/payload-today.json` | 1 | `kpis` | Regenerated Today review response. |
| `scratch/dashboard-global-review/payload-decline.json` | 1 | `kpis` | Regenerated negative-revenue/attention review response. |
| `docs/dashboard-kpi-refinement.md` | 1 | Report title | This report and manual testing guide. |

## Changes made / expected behavior

All eight cards remain in the existing grid with the same labels, primary-total definitions, icons, padding, border, radius, and shadow. The existing reusable secondary component remains in use.

- Users/products: `+N new/added in selected period`; zero additions use a dash and 0. These are neutral descriptions, not percentage trends.
- Sellers: `— No active sellers` when zero; recorded approvals use neutral +count wording. Existing current-access fallback remains for sellers without recorded approval timestamps.
- Facilities: current stored status summary, such as `1 open for booking` or `5 open for booking · 1 unavailable`. Booking slots do not determine this status.
- Pending approvals: nonempty queue retains its real product/seller/booking breakdown and gold attention marker; empty queue shows `— No pending approvals`.
- Empty orders/bookings: `— No orders/bookings in selected period`, with neutral semantics.
- Empty revenue: `— No completed sales in selected period` when no completed paid orders exist. If valid completed paid orders exist but sum to zero, show `— No marketplace revenue in selected period` instead.
- Nonempty period metrics retain green upward and red downward comparisons. New activity receives the requested short wording. No-change descriptions remain neutral.

All secondary lines use the same 12px regular font, line height, 6px top spacing, and left alignment. A single-line ellipsis prevents long descriptions from increasing card height. Full text remains in the DOM; a native hover title is added only when measured text exceeds available width. No info icons or tooltips are added to every card.

## Trend formatting and edge cases

Formula remains `(current - previous) / previous * 100` when the previous value is nonzero.

- `100.0` displays as `100%`.
- `16.666` displays as `16.7%`.
- `8.53` displays as `8.5%`.
- A nonzero change smaller than 0.05% displays as `<0.1%`, preserving direction rather than implying an exact zero change.
- Previous zero/current positive: secondary text `↑ New activity`; percentage remains null.
- Both zero: generic helper secondary text `— No change`; applicable cards replace it with their meaningful empty-period description.
- Current zero/previous positive: the actual API percentage remains -100 and the actual previous value is retained. The card's visible secondary line describes the empty selected period neutrally, as requested.

`comparison_text` remains the full equivalent-period comparison for existing Sales Overview consumers. The shorter or empty-state card wording is provided in `secondary_text`. No Infinity or NaN is emitted.

## Backend / API behavior and query impact

The existing `/api/admin/dashboard/` endpoint, date resolver, authentication/RBAC, seller definition, order/booking inclusion, and completed-plus-paid revenue rules are unchanged. This revision modifies formatting and descriptive presentation after aggregation; it adds no database queries or N+1 patterns. The existing query-count regression passed.

Loading still masks real values and secondary text with the existing skeleton. Failed requests retain the last successful data and the dashboard Retry action rather than presenting zero values.

## Database / migration impact

No migrations, schema changes, or production data writes. Review artifacts are generated from isolated test records and are not used as production dashboard data.

## Manual testing by card

| Card | How to test |
| --- | --- |
| Total Users | Select a period with zero additions, then one with additions. Expect `— 0 new…` or `+N new…` in neutral text. Main current-user total remains fixed. |
| Active Sellers | Verify zero active users gives `— No active sellers`. Recorded approvals update the neutral +count. No timestamps means no invented activation dates. |
| Total Products | Select ranges with and without `submitted_at` additions. Expect neutral +count or zero-count text, with the current non-archived total unchanged. |
| Total Facilities | Check a single open facility, then real unavailable/maintenance/inactive records. Confirm actual stored status counts and no changes caused by occupied booking slots. |
| Total Orders | Check a nonempty range with a known 100% or fractional comparison. Expect 100% without .0, at most one decimal for fractional changes, and appropriate direction/color. An empty range uses the specific orders description. |
| Total Bookings | Check empty, increasing, decreasing, unchanged, and zero-prior ranges. Empty text is specific; nonempty trends use the equivalent previous range. |
| Marketplace Revenue | Verify completed AND paid eligibility. Empty periods show the sales description; zero-value valid completed paid transactions show the revenue description. Positive/negative comparisons retain real arithmetic. |
| Pending Approvals | Empty queue shows only No pending approvals. Nonempty queue shows real category counts summing to the main value, with gold attention rather than green growth. |

Also verify Refresh, Today against yesterday, custom Apply/Cancel/Escape, chart grouping during a pending request, Retry after failure, and narrow card widths. Overflow help should appear only on clipped descriptions and disappear after resizing wide enough.

## Tests performed

- All 41 Django tests passed across `modules.reports.test_dashboard_periods`, `modules.reports.test_sales_overview`, and `accounts.tests.DedicatedDomainDashboardTests`; Django system check passed.
- The isolated rendering/review test passed again after currency-spacing refinement.
- DOM integration with all five dashboard stylesheets passed: eight cards, secondary-line styles, neutral/positive/negative/attention states, conditional overflow titles, API updates, loading, filters, request races, failure rollback/retry, custom popover, auth parameter preservation, chart updates, and Chart.js absence.
- JavaScript syntax, CSS parsing, and scoped whitespace checks passed.

## Remaining limitations

An interactive browser was unavailable, so exact desktop/mobile pixel geometry and native hover/date-picker appearance were not verified. Narrow cards may visibly truncate a secondary description; the full text remains in the DOM and is available through hover help where clipped. Native title behavior varies across touch devices. Seller history remains limited to recorded approvals, rather than a complete activation/reactivation audit. The design detector used its degraded regex fallback, not a complete visual audit.
