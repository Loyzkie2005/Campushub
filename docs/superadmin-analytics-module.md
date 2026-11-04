# CampusHub Super Admin Analytics Module Guide

## Current: final Marketplace and Inventory verification - November 2, 2026

This entry implements the final Marketplace/Inventory brief and supersedes the older **Sellers Active in Period** heading below. The KPI is now **Active Sellers**, with its selected-period activity definition visible underneath. Its eligibility and count have not changed. Dashboard current seller access is still a different snapshot.

### 1. Cause / reason

Confirmed defects: the slow-moving rule checked the overall 30-day/5-order history but could classify a newly submitted or recently approved product after only one observed day. Its Last Sold query could also reveal a sale after the selected end date. In the Super Admin layout, Turnover and Variant Sales each occupied a full row, contrary to the requested five-card arrangement. Inventory wording did not clearly distinguish product counts from individual stock-pool alert rows.

The existing Sales/Orders layouts, recognized-sales calculations, stable seller identifiers, guarded forecasting/Apriori and optional FIFO workflows were already implemented. They were inspected and tested rather than rebuilt. No extra Analytics sections, academic-program sales chart, FIFO Analytics card or duplicate bundle suggestions were added.

### 2. Exact files changed, current lines and nearby anchors

All paths are relative to the project root. Use the named anchor if later edits move a line.

| File | Line / anchor | What changed and expected behavior |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/analytics.py` | 290 `_product_inventory`; 304 `analytics_at__date__lte`; 342 `observed_since`; 358 `_slow_moving_products` | Bound Last Sold by the selected end date; derive product observation start from the later recorded submission/approval date; exclude candidates without 30 observed days within the selected period. Existing global 30-day/5-eligible-order gate, stock and unit thresholds stay intact. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 5 `Active Sellers`; 72 Slow-Moving header; 77 `Insufficient history` | Restore the requested four-KPI title while exposing its existing period basis; avoid repeating the insufficiency rule in both header and body. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 37 `marketplace-product-grid`; 42 `marketplace-variant-sales` | Keep five components: paired Top/Slow, full-width Inventory, paired Turnover/Variant. Variant Sales shows Product, Variant, Units Sold and Revenue from the same existing records. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_refined_panels.html` | 10 Inventory subtitle; 12 available-stock note; 13 alerts; 16 `marketplace-turnover-card` | Explain current snapshots, product totals versus stock pools, and already-net available stock. Keep the existing alert sorting/data and remove only Turnover's full-width layout class. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 54 five-component comment; 55-57 `.marketplace-product-grid` | Allow independent natural card heights and readable tables without a fixed inner table height. Existing 16px grid gaps, breakpoints and native horizontal table access remain. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 `20261102-marketplace-inventory-final` | Refresh the existing stylesheet cache key. |
| `backend/core/modules/reports/tests.py` | 336 `test_slow_moving_products_use_documented_minimum_history_rule` | Give the historical test products explicitly recorded earlier submission/approval dates, matching the rule under test. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 638 `test_slow_moving_excludes_new_recently_approved_and_future_products` | Verify old/new/recent-approval eligibility, post-period Last Sold exclusion and insufficient product history. |
| `backend/core/modules/reports/test_marketplace_inventory_integration.py` | 17 `MarketplaceInventoryIntegrationTests`; 94 pickup flow; 110 delivery/cancellation flow | Add two API-to-PostgreSQL-to-Analytics integration tests using the Flutter checkout/receipt contract and isolated test records. |
| `docs/superadmin-analytics-module.md`; `docs/fifo-inventory.md`; `CAMPUSHUB_CONTEXT.md` | Current November 2 final verification entries | Document causes, functions/data flow, measured checks, remaining limits and safe practice. Scratch evidence is under `scratch/final-marketplace-inventory-20261102/`. |

### 3. Changes made / what was already working

The inventory section now follows the requested 50/50, full-width, 50/50 desktop rows, stacking on mobile. Empty lower cards retain compact natural heights. Inventory Insights explicitly says its four statistics count products while each alert identifies a product/variant stock pool. Available Stock is labeled as already excluding reservations; the backend quantity is not reduced again. Variant Sales retains actual selections and existing once-per-order revenue attribution.

Overview keeps Total Sales Revenue, Completed Orders, Active Sellers and Approved Products with existing Dashboard-style icons. Revenue/completed orders and seller activity are period-based; approved products/stock are current snapshots. Sales retains its 2:1 and 1:2 rows, Daily/Weekly/Monthly zero-filled recognized-sales line, AOV and growth N/A rules, and category donut/breakdown. Orders retains three KPI cards and four independent analytical cards, zero-filled submitted-order bars, actual status/payment/receiving buckets and compact previous-count comparison. The separate Historical Submission Comparison table remains absent.

Buyers/sellers retain source-prefixed stable IDs, real completed-paid performance and recorded fulfillment coverage. Forecast/Apriori continue to require genuine eligible history/transactions. Dashboard Suggested Product Bundles remains separate. Stock Turnover/Sell-Through continues to require verified opening stock and continuous ledger evidence; it does not reconstruct history from current stock.

### 4. How it works: functions, inputs/outputs and data flow

`build_marketplace_analytics(params, user=..., refined=...)` receives the existing authorized scope/date filters and builds recognized sales, product inventory and slow-moving results. `valid_sales_queryset(user)` is still the canonical completed-paid eligible population; unpaid submissions remain in the independent operational counts.

`_product_inventory(products, period_orders, period)` receives authorized approved products, selected eligible sales and an `AnalyticsPeriod`. It returns current stock summaries, pool-independent product rows and product stock totals. Each row now also carries `observed_since = max(recorded submission date, recorded approval date)` in the application timezone. The maximum eligible Last Sold timestamp is bounded by `period.end`, including legitimate earlier sales but excluding later records.

`_slow_moving_products(inventory, period_orders, period)` returns `{sufficient, rule, rows}` and, after the global history gate, `history_excluded`. It first requires at least 30 selected days and five eligible orders. An in-stock product then needs at least 30 inclusive days between `max(period.start, observed_since)` and `period.end`; only products with at most one eligible unit sold qualify. If all in-stock candidates are too new/undated it returns insufficient history instead of an unreliable ranking. No eligible in-stock candidates is an ordinary empty result.

Annotated example, using disposable test records only:

```text
30 selected days + 5 completed-paid orders -> overall history gate passes
Product approved yesterday -> 1 observed day -> excluded, even with zero sales
Product approved before the period + 0 selected units -> eligible candidate
Sale after selected end -> excluded from Last Sold
```

Mobile receipt/checkout integration follows the existing path: Flutter-shaped request -> authenticated Django API -> locked shared product/SKU/batch/movement records in PostgreSQL -> existing order/payment transition -> the same read-only Analytics builder. Test helpers `receive`, `place`, `verify_hold` and `analytics` in the new integration class assert each boundary. No alternative stock or revenue calculation was introduced. The [FIFO guide](fifo-inventory.md:3) explains the verified receipt/reservation/completion/release flow.

### 5. Backend / API behavior

Only read-only product-history eligibility and Last Sold date bounds changed. Existing date presets/comparisons, permission checks, role/academic scoping, seller identities, fulfillment/payment workflows and API payloads remain. Sales still requires completed **and** paid orders; submitting/delivering an unpaid order does not recognize revenue. AOV has no denominator without qualifying orders and growth has no rate without a positive previous baseline. Neither becomes a fabricated 0%.

FIFO remains optional per configured product, inside Inventory Stock Batches/Stock Movements and existing receipt/checkout paths. Oldest eligible batches, keyed retries, transaction rollback, simple-stock separation and expired-product/variant reservation checks were preserved. No batch-level FEFO scheduler is being claimed: the inspected schema has no batch expiry date, and existing expiry protection is product/variant based.

### 6. Database / migration impact

No models, schema, migrations, deployed release, stock writers or working records changed. Configured PostgreSQL audits used explicit READ ONLY transactions. For October 4-November 2 the confirmed working values remain **3 submitted orders, PHP 0.00 recognized revenue and 1 low-stock product**. AOV is unavailable; active-period sellers 1 and current seller access 2 retain different definitions. FIFO is enabled; 14 FIFO products/1 Simple product, 14 batches and 3 allocations reconcile across 14 stock pools. No available/reserved mismatch or active Simple-stock batch was found. These are dated observations, never application constants.

### 7. Tests performed and evidence

- Before changing code, 97/97 FIFO/concurrency/hybrid/checkout/fulfillment/variant/mobile-seller tests passed against disposable local PostgreSQL. The subsequent affected Analytics/Dashboard regression run passed 115/115.
- Final combined regression: **247/247 passed in 98.161 seconds**, system check reported no issues, and the disposable database was destroyed. This includes the two new API-flow tests, existing Analytics/Dashboard parity coverage, inventory-monitor/program-scoping tests and the concurrency/hybrid/checkout/fulfillment/variant/mobile-seller suites. `regression.log` retains the result; PowerShell's `NativeCommandError` formatting on the initial stderr progress line is not a test failure (runner exit code 0, final result OK).
- The new API flows verify keyed receipt and order retries, oldest-batch allocation, available/on-hand/reserved balances, mobile workspace/Admin inventory/Analytics agreement, stable mobile seller identity, pickup paid completion once, delivered-but-unpaid exclusion, delivered cancellation rejection, explicit payment recognition and cancellation release once.
- Flutter: 11/11 tests passed from `flutter test --no-pub test/checkout_workflow_test.dart test/order_fulfillment_test.dart test/seller_stock_receiving_test.dart`. These are HTTP-contract/widget tests, not a physical-device session against working data.
- Real authenticated HTTP/browser integration: 70/70 checks passed at 1440px and 390px against a disposable PostgreSQL-backed Django server. Checks cover five inventory cards/row widths/16px gaps/stacking/no page overflow, compact empties, Dashboard-to-Analytics links/date scopes, populated/empty AOV, actual charts/rankings and permission denial. Only vendor CDN assets were supplied locally. Both inventory screenshots were visually inspected.
- Configured working Dashboard HTML/API, all linked Analytics views and actual Stock Batches/Movements GETs returned 200 under READ ONLY; restricted Dashboard API access was denied. FIFO reconciliation required no change. Eight protected-source hashes passed; surrounding Sales/Orders/People/Insights markup matched the pre-change capture.
- Final scoped whitespace check passed for all 12 changed application/test/document files; tracked-file `git diff --check` passed. No universal accessibility or design-system certification is claimed by these functional/render checks.
- Scratch evidence: `after.json` (read-only audit), `live-result.json`, `products-1440.png`, `products-390.png`, `regression.log`, `protected.json`. The `run_live.py` harness uses a temporary server/test database; `audit_working.py` only reads configured records.

Reproduce backend checks with the existing disposable-local runner, never a working database:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests modules.reports.test_marketplace_admin_dashboard modules.reports.test_marketplace_inventory_integration modules.reports.test_dashboard_marketplace_parity modules.marketplace.test_fifo_inventory modules.marketplace.test_fifo_concurrency modules.marketplace.test_hybrid_inventory modules.marketplace.test_checkout modules.marketplace.test_order_fulfillment modules.marketplace.test_variant_inventory modules.marketplace.test_inventory_monitor modules.marketplace.test_program_inventory api.test_mobile_seller_workspace
```

The runner enforces localhost:5432, creates a timestamped test database, bootstraps existing unmanaged tables and destroys the database afterward. Do not copy fixtures into the working database.

### 8. Remaining limitations, troubleshooting and safe practice

The working database has no eligible recognized sales in this period, so populated-sales behavior is verified with isolated test records. Sparse genuine history cannot support reliable forecasts/Apriori; missing continuous ledger history cannot support turnover. Honest insufficient-history messages remain expected capstone behavior. Catalog/approval age is evidence of product observation, not proof of continuous availability or a stockout-adjusted demand model. Unknown historical receipts retain undated opening balances; no dates were invented.

If Slow-Moving is empty, first check selected days and eligible-order count, then recorded submission/approval dates, current stock and selected eligible units. If stock counts differ from alerts, remember four statistics count products while alerts list up to ten individual pools. If available stock looks smaller than on hand, inspect actual active reservations; do not subtract them a second time. Diagnose with scoped read-only queries and the named tests before changing rules.

Safe learning exercise: in a disposable test database, change the recent approval fixture in `test_slow_moving_excludes_new_recently_approved_and_future_products` from one observed day to 30. Verify that it becomes an eligible zero-sale candidate while the post-period Last Sold sale remains excluded. Run that test, restore the fixture and rerun. Then inspect the two receipt batches in the API integration test: 3 old + 4 new, reserve 4 -> allocations 3 + 1, available 3. Completion keeps available 3; cancelling an uncompleted hold releases it once. Never perform this exercise on working orders or stock.

## Current: Dashboard / Marketplace metric definitions - November 2, 2026

1. **Cause / reason:** Configured PostgreSQL reconciliation confirmed that Dashboard excluded mobile accounts from Total Users/current seller access, while Marketplace seller activity was already a different period-based KPI. Undefined Dashboard AOV was represented as zero and hidden in the executive summary. The detailed [cross-page report](dashboard-analytics-operations-update.md:3) records the confirmed discrepancies and all exact files/current anchors.
2. **Exact files changed:** Shared definitions are in `backend/core/modules/reports/account_metrics.py:8` (`account_population`) and `backend/core/modules/marketplace/services/reporting_metrics.py:5` (AOV), `:10` (approved-owner predicate), `:17` (seller snapshot). Analytics reuses them in `analytics_sections.py:395`, `services/analytics.py:384`, `:395`, `:734` and `superadmin_analytics.py:68`. The Super Admin seller label changes in `templates/reports/partials/marketplace_analytics_cards.html:5`. Paths without a leading module are under the existing reports/marketplace folders listed in the detailed report; no models or routes changed.
3. **Changes made:** Marketplace retains its activity count but labels it **Sellers Active in Period**. Dashboard current access now includes web/mobile sellers. Total Users/New Users share web/mobile definitions. Super Admin AOV is N/A when no completed-paid orders qualify; real zero-price qualifying orders retain ₱0.00. Dashboard keeps three compact summary cards by displaying its existing AOV instead of duplicating the System Overview seller snapshot. Detailed charts/comparisons stay here in Analytics.
4. **How it works:** `account_population(period)` returns separate source counts for current total/enabled records and selected-date registrations, using web `date_joined` and mobile `created_at`. Optional seller Exists aggregates share the approved-owner predicate with the existing seller-ID helpers and preserve source identity. `average_order_value(revenue, qualifying_orders)` returns Decimal revenue/count or None without a denominator; detailed current/prior AOV uses that same helper. Example: three unpaid submissions give volume 3, revenue 0 and AOV N/A; a completed-paid zero-price order gives a defined zero average. Source IDs and names are never used to merge web/mobile people.
5. **Backend / API behavior:** Existing permissions, academic scoping, date filters, order workflows, recognized-revenue eligibility, comparisons and the Dashboard's four correct tab destinations are preserved. Legacy non-refined AOV formatting and legacy enabled Seller-role reporting compatibility remain. The only API value-shape change is null for undefined Super Admin Dashboard/refined AOV, handled by its existing card renderer. Users Analytics' enabled count now consistently excludes suspension in both sources.
6. **Database / migration impact:** None. Working PostgreSQL verification used READ ONLY and unchanged row counts. For October 4–November 2, the confirmed figures remain 3 submissions, ₱0.00 recognized revenue and 1 low-stock product; corrected totals are 11 account records (4 web + 7 mobile), 7 registrations (1 web + 6 mobile), seller access 2 and period activity 1. These are dated observations, not application constants.
7. **Tests performed:** 148/148 Django regression tests passed, plus the added Philippine-midnight parity test. 54/54 authenticated real HTTP browser checks passed at 1440px/390px against a disposable PostgreSQL-backed Django server, including API refresh, populated-to-empty AOV, actual charts/rankings, four tab links and 403 role denial. Configured working Dashboard HTML/API and all four linked Analytics views returned 200 under READ ONLY; non-Super Admin Dashboard API access was denied. Existing ≤39-query Dashboard and constant-query-growth checks still pass. Static JS syntax/whitespace checks passed. Evidence and reproducible commands are in the linked detailed report and `scratch/dashboard-marketplace-parity-20261102/`.
8. **Remaining limitations / learning practice:** Account totals count records, not verified unique people; seller current access and selected-date activity intentionally differ. Working data was not modified or deployed; the authenticated browser used a real disposable server, while configured working records were reconciled read-only. Safe practice: select custom dates on Dashboard, follow View Analytics, verify the module/dates and compare submissions separately from recognized sales. Trace a None AOV from the shared helper to both cards, and compare a populated mean with revenue / qualifying orders. Keep all real records unchanged; do not import test fixtures into working analytics.

## Current: Orders & Payments KPI and chart layout - November 2, 2026

### 1. Cause / reason

The previous compact comparison was already inside Order Volume Trend and the redundant historical card was already removed. Remaining gaps were plain operational KPIs, the Processing Time label, a line chart that omitted empty dates, and full-width payment/receiving donuts above separate scrolling tables. The user requested Dashboard-style KPIs, grouped submitted-order bars, direct donut breakdowns and no unnecessary inner scrolling. The explicitly requested Sales & Revenue heading is also renamed to Sales & Revenue Analysis; the main page still says Analytics.

### 2. Exact files changed, current lines and nearby anchors

Paths are relative to the project root. The new partials isolate this section from legacy-role and other-tab markup.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 8 Sales heading; 20 `.marketplace-orders-section`; 22 KPIs; 27–32 card includes | Renames only the requested Sales section heading and assembles the three operational KPIs and two pairs of independent cards. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_order_kpis.html` | 1 reusable Dashboard card classes; 15 Average Fulfillment Time; 17 value | Three existing-metric cards use top-right SVG icons, actual counts, timing coverage and N/A when unavailable. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_order_volume.html` | 4 GET grouping form; 22 chart; 24 exact-data details | Keeps the compact comparison, adds independent grouping and preserves actual chart values behind a native expandable exact-data table. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_order_status.html` | 1 status card; 3 existing outcome loop | Reuses actual labels/counts/shares and permission-resolved status destinations in plain navy horizontal rows. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_order_distribution.html` | 1 shared distribution card; 4 donut/list layout; 7 rows | Renders the complete existing payment/receiving breakdown next to its donut, without a second table or duplicate chart legend. Receiving's last bucket is displayed as Not Recorded with an explicit missing/unclassified explanation. |
| `backend/core/modules/reports/superadmin_analytics.py` | 50 `enrich_marketplace`; 126 `enrich_marketplace_sections`; 160 demand call; 315 `request_demand` | Threads optional order grouping through enrichment; opts only Marketplace orders into zero-filled buckets. Existing operational aggregation remains unchanged. |
| `backend/core/modules/reports/views.py` | 1402 enrichment call | Passes the read-only `order_grouping` GET option after the existing permission/scope checks. |
| `backend/static/components/js/admin_marketplace_sections.js` | 5 order control; 18 fallback; 32 chart list | Auto-submits order grouping, preserves it across existing page forms, draws submitted-order bars, hides redundant donut legends and matches legend indicator colors. Other-tab controllers and the Sales line controller remain unchanged. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 117 Orders-only block; 132 status links; 134 distribution container; 147 desktop KPI row | Reuses existing KPI styling; aligns icons at the top right, keeps card padding, responsive donut/list layouts and plain navy status links, and removes volume-data height/overflow limits. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 CSS and 91 section controller cache keys | Updates both to `20261102-marketplace-orders-layout`. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 308 heading assertion; 409 grouping regression; 813 optional export cases | Updates intended presentation assertions and verifies zero-filled grouping, all-status counts, date bounds, independent Sales grouping, invalid-input fallback and unchanged default helper behavior. |
| `docs/superadmin-analytics-module.md`, `CAMPUSHUB_CONTEXT.md`, `docs/web-ui-ux-guidelines.md` | Current Orders & Payments entries | Records the current rules, data flow, verification and learning guidance. |

### 3. Changes made

The three KPIs retain the Dashboard-style navy icon containers, 16px padding and large values. Completion and cancellation use existing current-submission-cohort numerators and denominators. Average Fulfillment Time replaces the Processing Time label, preserving the existing hours calculation and showing timed/completed counts underneath. Missing values display N/A. Its scope is recorded submission-to-completion, not an inferred seller-delivery event.

The first equal-width pair contains Order Volume Trend and Order Status Breakdown. The second contains Payment Status Analysis and Receiving Method Analysis. From 1200px the pairs are two columns; narrower screens stack. KPIs share one horizontal row from 900px and stack below. Donuts appear to the left of their full text breakdown when card content is at least 320px wide; smaller cards stack the donut above the list. All rows, including real zero-count rows, remain readable. Shares retain the existing one-decimal rounding, so their displayed sum can differ slightly from 100%.

Volume retains only the current/prior total comparison. Its optional exact-value table expands naturally instead of reserving a scrolling plot/table area. Empty cards stay compact and text based. Native exact-data controls and a no-JavaScript Apply button preserve access without new dependencies. No unrelated card, navigation, role layout or sales calculation was redesigned.

### 4. How it works: functions, inputs/outputs and data flow

The authorized Marketplace view still builds the existing analytics projection. It now passes `request.GET.get('order_grouping')` to `enrich_marketplace()`, which passes it to `enrich_marketplace_sections()`. The existing scoped `created_at` submission cohort and operational aggregate are unchanged. Completion rate is completed/submitted × 100; cancellation rate is cancelled/submitted × 100. The existing duration filter accepts currently completed rows only when `completed_at` exists and is not before `created_at`; `processing_hours` remains the compatible internal field. The UI labels it Average Fulfillment Time and displays N/A for no usable timing, including no completed orders. Missing or invalid timestamps are not fabricated from update times.

`request_demand(queryset, period, grouping=None, include_empty=False)` retains its one date-aggregation query. The new optional grouping selects daily dates, Monday-based weeks, or calendar months. Marketplace requests `include_empty=True`, which seeds every in-range bucket with zero before adding real counts. Only dates within the scoped period contribute to partial first/last buckets. Invalid/absent grouping falls back to the existing duration-based choice: monthly above 90 days, weekly above 31, otherwise daily. Other Facilities/Services calls retain their original defaults and non-filled output; no extra grouping key is added to those existing outputs.

The new GET form sends the selected period/custom dates and existing Sales/forecast selections alongside `order_grouping`. Its script preserves the order selection when other page forms submit, and changes only the orders series grouping. The chart receives server JSON, renders navy bars and uses whole-count ticks. Narrow x-axis labels omit the year and use fewer ticks; full server labels remain in tooltips and exact data. No JavaScript estimates, random data or generated counts are used. Existing zero-baseline comparison wording remains server supplied: New activity for positive current/zero prior; No change for two zero counts.

Payment and receiving lists use the existing `operations.payment` and `operations.fulfillment` rows. Each row already supplies label, count and percentage. The same ordered navy/gold/neutral palette colors the donut and its list indicators. Receiving's fallback bucket still combines missing/other historical methods; its shorter Not Recorded label and explanatory subtitle do not reclassify any record. Pending/unpaid submissions remain operational counts and never become recognized sales. The existing eligible completed-paid recognition-date revenue builder is untouched.

Annotated actual regression example: six submitted orders yield three currently completed and one cancelled, so the KPIs show 50.0% and 16.7%. Two valid completion durations average 3.0 hours; the card discloses 2 timed / 3 completed. Payment counts are 2 paid, 3 unpaid, 1 other; receiving counts are 2 pickup, 2 delivery, 2 missing/other. Another isolated case has orders only on October 1 and 19: Daily includes 17 zero days; Weekly includes two empty calendar weeks; Monthly combines only the selected dates. These are disposable-test records, not working marketplace figures.

### 5. Backend / API behavior

The only new request option is `order_grouping` on the existing authorized GET view. No endpoint, permission, account scope, lifecycle, payment/receiving definition, recognized-revenue rule, comparison period, forecasting or inventory calculation changed. No additional database query is needed for zero filling or changing the aggregation interval. The existing processing-hours field and operational numerator/denominator aggregates remain compatible for other consumers.

### 6. Database / migration impact

None. No schema, model, migration, working-record write, persistent environment edit, deployment or restart. The PostgreSQL runner creates and destroys an isolated local test database. Generated HTML, JSON and actual browser screenshots live under `scratch/orders-payments-layout-20261102/` and do not supply production analytics.

### 7. Tests performed

- **63/63 affected Django tests passed** in 40.693 seconds across the Super Admin Analytics suite and Marketplace Analytics regressions, with no system-check issues. New grouping coverage verifies unpaid/pending/cancelled submissions, future-record exclusion, current/past bounds, zero days/weeks/months, grouping independence, invalid selection fallback and empty series. The first run exposed a mistaken test expectation for a four-calendar-week interval and an existing status empty-state wording assertion; both were corrected before the passing run.
- Three final focused checks passed in 5.104 seconds after adding a default-helper compatibility assertion and the native Apply styling; two additional capture/regression checks passed in 1.347 seconds to export current mixed/grouping responses. These tests use actual disposable records, not fabricated browser statistics.
- **2,345/2,345 Chromium and scope checks passed across 66 navigations**, covering 280, 320, 390, 768, 900, 1024, 1200, 1280, 1440 and 1920px; empty, populated, mixed-status and boundary-date states. Checks cover KPI values/counts/icons, grouping/date preservation, zero-filled bars, exact status/payment/receiving counts and shares, legend colors, responsive equal-width pairs, no inner vertical scrollbars, exact-data expansion, missing Chart.js and no-JavaScript Apply. Scope checks match six protected source fingerprints, the unchanged operational aggregate block, and all sections outside Orders except the explicit Sales heading rename. Facilities/Services fixture tables remain present. After the final navy-link, singular-label, no-JavaScript-button and compact phone-axis refinements, **505/505 additional checks passed across 12 navigations** using refreshed fixtures. Actual final mixed desktop and populated phone screenshots were visually inspected. Evidence: `scratch/orders-payments-layout-20261102/result.json`, `final-result.json`, `check.cjs`, `export_cases.py`, snapshots/fingerprints, fixture JSON/HTML and state/width PNGs. These are isolated rendered fixtures, not deployed live-browser claims.
- Static checks: `node --check` for the section controller and scoped `git diff --check` passed. The optional design skill's referenced bundled gate kit remains unavailable; no bundled score or accessibility certification is claimed.

Reproduce the affected Django suite from the project root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests
```

### 8. Remaining limitations, troubleshooting and safe practice

The charts describe current recorded outcomes for submission cohorts, not reconstructed historical status transitions. Average Fulfillment Time can be N/A even with completed orders when trustworthy timestamps are missing; the timed/completed count exposes coverage. It cannot prove individual delivery time. Unknown historical payment/method values retain their fallback grouping. Browser verification uses isolated Django-rendered responses rather than an authenticated deployed session.

If the old line, old labels or old layout appear, reload and check the CSS/controller `20261102-marketplace-orders-layout` cache keys. If a weekly label begins before the selected first date, it names the calendar week containing that date; only in-range submissions are counted. If current order counts differ from sales counts, reconcile created dates/all statuses against the separate completed-paid recognition cohort. Do not change status/payment records merely to make the metrics agree.

Safe exercise: select a read-only date range, add the exact Volume values and verify the current submission count. Divide completed and cancelled counts by submitted orders and compare the displayed rounded rates. Change Daily → Weekly → Monthly and confirm totals, rates, comparison, payment and receiving counts stay constant while bars regroup. Choose custom dates and confirm they remain after grouping. Expand View order volume data and inspect all rows without a nested scrollbar. Resize to a phone, then restore the original period. For a local code exercise, trace one receiving row from the unchanged aggregate into the new distribution partial, temporarily shorten only its subtitle, inspect both widths and restore it. No working-record edits are necessary.

## Current: Order Volume submission comparison - November 2, 2026

### 1. Cause / reason

Marketplace Orders & Payments displayed a full Historical Submission Comparison table in addition to the Order Volume Trend and Order Status Breakdown. The user requested removing that repeated outcome table and retaining only the essential current/prior order comparison inside the trend card. Inspection confirmed all required values and zero-baseline wording already exist in Django.

### 2. Exact files changed, current lines and anchors

| File relative to project root | Current line / code anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 28 payment JSON after volume JSON; 31 `.marketplace-order-volume`; 33 new include | Removes only the Marketplace shared comparison-table include and inserts the compact comparison inside Order Volume Trend. Existing charts, status breakdown and operational KPIs remain. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_order_comparison.html` | 1 existing total-row binding; 2 definition list; 7 comparison note | New partial renders current orders, previous orders, signed difference, server-provided change text and exact prior dates. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 99 `Order Volume owns`; 100 summary grid; 117 responsive rule | Adds styles only for the new summary: three compact columns from 600px, stacked label/value rows below, existing navy/neutral tokens, 8px gaps and readable wrapping. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 refinement cache key | Changes to `20261102-marketplace-order-comparison` to fetch the new stylesheet. |
| `docs/superadmin-analytics-module.md` | 3 this report | Records cause, functions/data flow, verification and safe learning steps. |

### 3. Changes made

The standalone Historical Submission Comparison card/table is removed from Marketplace presentation. The Order Volume Trend card now contains Current-period orders, Previous-period orders and Difference before its existing chart. Positive differences include a plus sign; zero and negative differences keep their actual values. A compact note shows the existing comparison wording and preceding equal-length dates. New activity is shown when current submissions exist and the previous count is zero; both counts zero retain the honest No change state. Empty chart periods still display the comparison summary, including any recorded prior activity.

Order completion/cancellation/processing rates, Order Volume Trend and its exact-value table, Order Status Breakdown, Payment Status Analysis and Customer Pickup vs. Seller Delivery remain. Shared Historical Submission Comparison markup is retained for Facilities and Services. The Sales section, Products, Buyers/Sellers, Insights, other tabs and legacy-role presentation are outside this change.

### 4. How it works: functions, inputs/outputs and data flow

No Python function changed. The authorized view still runs `build_marketplace_analytics()` and `enrich_marketplace_sections()`. The latter calls `submission_comparison(scoped_marketplace_orders(user), period, MarketplaceOrder.STATUS_CHOICES)`. That existing helper performs one aggregate for current/prior equal-length submission-date cohorts. Its output contains prior `start`/`end` dates and `rows`; `rows[0]` is All submissions, with `current`, `previous`, `difference` and `change`. The new partial binds exactly that existing first row, displaying its values rather than recalculating totals in JavaScript. `comparison_metric()` still determines percentage text when the prior count is positive; the helper already substitutes New activity when the baseline is zero and current activity is positive, or No change for two zero counts.

The existing chart independently receives `analytics.order_volume.chart`; its bucket counts and comparison current total use the same scoped submitted-order population. This is submission demand across all recorded statuses, not completed-paid recognized revenue. The existing GET date controls continue to select both current buckets and the preceding equal-length comparison window. Current statuses classify recorded outcomes; this presentation does not reconstruct historical status transitions.

Annotated examples: current 3 / previous 0 produces difference +3 and New activity, never an invented percentage. Current 4 / previous 2 produces difference +2 and the existing +100.0% text. Current 0 / previous 0 produces 0 and No change. These explain the unchanged helper; they are not working marketplace figures. Keeping the comparison inside the trend card removes the redundant status table while retaining the data needed to interpret demand.

### 5. Backend / API behavior

No query, function, aggregation, API, controller, route, permission, revenue rule or date filter changed. The full comparison dictionary still exists for existing consumers; only Marketplace's presentation of it is compacted. Receiving/fulfillment and payment definitions remain separate and unchanged. Unknown historical methods stay unclassified.

### 6. Database / migration impact

None. No schema, model, migration, working-record write, environment change, deployment or restart. The existing disposable local PostgreSQL runner produces isolated verification records. Browser fixtures, scope fingerprints and screenshots are under `scratch/order-volume-comparison-20261102/` and do not supply operational data.

### 7. Tests performed

- **62/62 existing affected Django tests passed** in 30.016 seconds, with no system-check issues, across `modules.reports.test_superadmin_analytics` and `modules.reports.tests.MarketplaceAnalyticsTests`. This includes existing population, eligibility, date, comparison and query-growth regressions. No new production tests were written for this presentation-only change.
- **451/451 Chromium and scope checks passed across 32 navigations**, covering widths 280, 320, 390, 768, 1024, 1200, 1280, 1440 and 1920px, populated/empty states, date presets/custom dates on desktop/phone, no-JS and missing-chart-library fallback. The three visible comparison values match Django, current totals reconcile with chart buckets, zero-baseline wording/prior dates are correct, all requested operational cards/rates remain, and summaries stay compact without overflow. Actual populated desktop and empty phone screenshots were visually inspected. Scope checks confirm unchanged Overview/Sales and Products-through-Insights assembly, unchanged status/payment/fulfillment assembly, all existing CSS unchanged outside the added block, and unchanged hashes for the comparison backend, shared comparison-table partial, shared Marketplace cards and other-tab section templates. Facilities/Services rendered fixtures retain their original comparison tables. Evidence: `scratch/order-volume-comparison-20261102/result.json`, `check.cjs`, `protected.json`, source snapshots and state/width PNGs. These are isolated verification fixtures, not deployed live-browser checks.
- Scoped `git diff --check` and browser-helper `node --check` passed. The optional design skill's referenced bundled gate remains unavailable; no bundled score or accessibility certification is claimed.

Reproduce the affected suite from the project root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests
```

### 8. Remaining limitations, troubleshooting and safe practice

Browser checks use isolated Django-rendered responses rather than an authenticated deployed browser session. Order submission counts deliberately differ from recognized-sales counts when pending, unpaid or cancelled orders exist. The removed table's per-outcome comparison rows are no longer displayed in Marketplace; the existing status breakdown remains authoritative for its selected-period outcomes. Long counts/labels wrap instead of being clipped.

If the old standalone comparison remains, reload and verify the deployed template as well as the `20261102-marketplace-order-comparison` CSS key. For unexpected counts, compare the current order submission dates and prior equal-length dates, not revenue-recognition timestamps. A zero prior count cannot support a percentage growth rate. No change is appropriate when both counts are zero.

Safe exercise: use a read-only date range and compare the summary current count with the sum of Order Volume Trend's exact values. Check that Difference equals current minus previous and that the displayed prior dates end one day before the selected range. Change to another date preset, then a custom range, and repeat without editing any records. Inspect phone/desktop layouts and restore the original range. For a small local code exercise, trace `rows.0.current` from `submission_comparison()` to the new partial; temporarily shorten only its Current-period orders label, render it, then restore the label. No database changes are needed.

## Current: Restored Analytics page heading - November 2, 2026

1. **Cause / reason:** The user requested reverting the preceding Analysis page-heading rename and retaining Sales & Revenue Analytics. This is a display-label restoration.
2. **Exact files changed:** `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html`, line 8 browser title and line 25 `admin_header.html` include; this guide, line 3 report. The Marketplace Admin branch retains its existing separate title.
3. **Changes made:** The Super Admin Marketplace page's main heading, matching current-page breadcrumb and browser title again say Analytics. The Sales & Revenue Analytics section heading was inspected and remains unchanged.
4. **How it works:** The existing authorized Django view renders the page template. The include passes `page_title='Analytics'` and `breadcrumb_page='Analytics'` into the shared `partials/admin_header.html`; that partial outputs them in its existing h1 and current breadcrumb. Example: `page_title='Analytics'` becomes `<h1 class="header-page-title">Analytics</h1>`. This uses the shared header without changing other pages or its behavior.
5. **Backend / API behavior:** No view, function, query, permission, route, chart, filter or calculation changes.
6. **Database / migration impact:** None. Test fixture exports use the existing disposable local PostgreSQL runner; no working-record writes, deployment or restart.
7. **Tests performed:** Three existing focused Django tests passed in 3.349 seconds: four-tab Super Admin access, Marketplace Admin tab restrictions, and isolated fixture export. No system-check issues. Rendered Marketplace HTML confirms Analytics in the h1, current breadcrumb and browser title, and Sales & Revenue Analytics in the section h2. Evidence: `scratch/analytics-heading-restored-20261102/fixtures/empty-marketplace-30.html`. Scoped `git diff --check` passed. No new tests were added for this copy-only change.
8. **Remaining limitations / troubleshooting:** This restores the current Super Admin Marketplace page header without renaming section headings or other pages. No browser visual review is needed for this text-only restoration. If Analysis persists, reload the Django page and confirm the current template is deployed. Safe practice: inspect the h1 and Sales & Revenue Analytics heading in the rendered page, then trace the h1 back to `page_title` at line 25 and the section title to `marketplace_analytics_sections.html` line 8. Neither requires editing backend data.

## Current: Compact Sales Growth card - November 2, 2026

### 1. Cause / reason

Sales Growth already used the correct prior-period dates and zero-baseline guard, but its small primary metric and stacked definition-list rows gave revenue amounts equal visual weight. The user requested a larger percentage and two subtle side-by-side revenue areas, confined to this card.

### 2. Exact files changed, current lines and anchors

| File relative to project root | Current line / nearby code anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/templates/reports/partials/marketplace_refined_panels.html` | 5 Growth revenue definition list | Labels become Current Revenue / Previous Revenue; existing values, title, subtitle and conditional note remain. Other card branches are unchanged. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 78 `Sales Growth alone`; 79 primary metric; 83 revenue grid; 86 metric areas; 98 note | Adds Growth-only rules: 32px navy primary metric; equal two-column areas with 8px gap/padding, subtle existing surface/border tokens, readable labels and tabular currency. Content can wrap and the card keeps natural height. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 refinement stylesheet cache key | Updates to `20261102-marketplace-growth-card` so browsers fetch the scoped styling. |
| `docs/superadmin-analytics-module.md` | 3 this report | Records implementation, data flow, checks, troubleshooting and a safe practice exercise. |

### 3. Changes made

Sales Growth keeps its previous reporting-period subtitle. The percentage, or N/A, now leads the card in navy `#1A1851`. Current and previous revenue appear in two equal compact metric areas. The existing concise note appears only when percentage growth cannot be calculated. No forced card height, large icon, chart, decorative color or other card styling was added. Initial narrow-width verification showed excessive wrapping at 280px; reducing inner metric padding/gap corrected the compactness without clipping or hiding data.

### 4. How it works: functions, inputs/outputs and data flow

No function or calculation changed. The authorized view still calls `build_marketplace_analytics()` and `enrich_marketplace(analytics, user)`. Their existing recognized completed-paid totals supply `analytics.kpis.sales`; the prior equal-length recognized-sales aggregate supplies `analytics.comparison.previous_sales`, `start` and `end`. `comparison_metric()` returns `percentage_change`, which is `None` when the previous revenue is zero. The template displays a one-decimal percentage only when the field is not `None`; otherwise it renders N/A and the zero-baseline explanation. This explicit check preserves a legitimate numeric zero while distinguishing an undefined percentage.

Annotated example: current revenue 100 / prior 100 yields a real 0.0%; current 100 / prior 50 yields 100.0%; prior zero yields N/A regardless of current revenue. These examples explain the existing formula; they are not operational records. CSS changes only layout and emphasis, not these values. The existing date/grouping GET forms remain untouched.

### 5. Backend / API behavior

Unchanged. No Python, query, controller, endpoint, permission, scope, recognized-revenue or date-filter changes. The existing N/A guard continues to prevent zero prior revenue from appearing as 0% growth. AOV and the neighboring Trend/Category cards retain their existing typography/layout.

### 6. Database / migration impact

None. No models, migrations, working-record writes, environment changes, restart or deployment. Verification uses disposable local PostgreSQL test records and isolated HTML fixtures under `scratch/sales-growth-card-20261102/`.

### 7. Tests performed

- Three focused existing Django tests passed in 3.125 seconds: recognized revenue/prior comparison, AOV denominator regression, and optional complete fixture export. Two existing numeric regressions were additionally run with an isolated response-capture wrapper (both passed in 1.053 seconds) to export actual positive, negative, true-zero and N/A growth states for rendering. No production tests were added for this presentation-only change.
- **1,210/1,210 Chromium checks passed across 32 renders** at 280, 320, 390, 768, 1024, 1280, 1440 and 1920px, covering actual positive, negative, true-zero and N/A test responses. Checks confirm exact title/dates/values, percentage versus N/A, conditional explanation, equal side-by-side areas, 32px navy emphasis, compact height below 360px for these fixtures, no page/metric overflow and unchanged neighboring 22px AOV sizing. Actual desktop/phone positive, true-zero and N/A screenshots were visually inspected. Evidence: `scratch/sales-growth-card-20261102/result.json`, `check.cjs`, `export_growth.py` and state/width PNGs. The captured records belong only to disposable tests.
- Scope checks verify all pre-existing CSS is byte-for-byte unchanged when the new Growth-only block is removed, and all non-Growth branches in the edited partial match their saved pre-edit text.
- Final scoped `git diff --check` and browser-helper `node --check` passed after the spacing refinement. No backend source or date-filter controller changed.

### 8. Remaining limitations, troubleshooting and safe practice

The card has natural height: very narrow screens or unusually long currency values may wrap rather than truncate financial information. The browser review uses isolated Django test responses and does not prove deployment or an authenticated live session. The optional design skill's referenced bundled gate remains unavailable; no bundled score or accessibility certification is claimed.

If the old stacked rows remain visible, hard-refresh and inspect the `20261102-marketplace-growth-card` CSS cache key. If N/A appears, inspect prior revenue before assuming a fault; zero is an invalid growth denominator. A genuine 0.0% is expected when equal current/prior revenues have a nonzero baseline.

Safe practice: view a read-only period with no prior revenue and confirm N/A plus the note. Choose a populated comparison and verify `(current - previous) / previous * 100` against the displayed one-decimal value. Resize to a phone and confirm both revenue areas remain side by side. For a local learning exercise, change only the Growth primary-metric size from 32px to 30px in the scoped rule at line 79, inspect the card, then restore 32px; AOV should remain 22px throughout. Do not modify orders to force test values.

## Current: Two-row Sales & Revenue Analytics - November 2, 2026

### 1. Cause / reason

The preceding implementation used a single 50/20/30 Trend/Growth/Category row and did not present the already-calculated AOV in this section. The user requested four independent cards in two desktop rows, with a current/prior AOV comparison and preserved revenue/date/empty-state rules. Current AOV already exists in the marketplace builder; the existing prior-period aggregate already supplies the matching revenue and order count.

### 2. Exact files changed, current lines and anchors

| File relative to project root | Current line / code anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 8 sales subtitle; 11 `marketplace-revenue-primary`; 15 `marketplace-revenue-secondary` | Splits only Sales & Revenue into Trend/Growth then AOV/Category. Updates its descriptive subtitle. All other section assembly stays intact. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_revenue_aov.html` | 1 `.marketplace-aov-card`; 4 current value; 6 prior value; 7 change; 10 guards | New summary card shows current AOV, prior AOV, percentage comparison, explicit prior dates and missing-baseline explanations. |
| `backend/core/modules/reports/superadmin_analytics.py` | 50 `enrich_marketplace`; 66 current order count; 69 `revenue_aov` | Adds only the AOV presentation object using existing recognized-sales values/counts and the already-issued prior aggregate, without another query. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 62 revenue rows; 86 legend max-height; 103 desktop media rule | Uses natural-height cards, 2:1 then 1:2 columns from 1200px, stacked cards below, existing 16px gaps, and a 240px keyboard-scrollable category list for balanced second-row content. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 stylesheet cache key | Loads `20261102-marketplace-two-revenue-rows` so browsers receive the current layout. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 586 existing revenue regression; 601 `test_revenue_aov_distinguishes_missing_orders_from_zero_value_orders` | Verifies AOV recognition/comparison, missing order denominators, zero-price qualifying orders, percent display and independence from time grouping. |
| `docs/superadmin-analytics-module.md`, `CAMPUSHUB_CONTEXT.md`, `docs/web-ui-ux-guidelines.md` | Current two-row entries | Preserve the latest layout choice, explanation, verification and learning guidance. |

### 3. Changes made

Desktop rows now have Sales Trend at approximately 67% and Growth at 33%, followed by AOV at 33% and Category at 67%, after the 16px gutter. All cards retain the existing 16px padding, full subtle border, rounded corners and typography. The grid aligns card tops but does not stretch Growth, AOV or empty charts to a tall neighboring plot. The section already supplies 16px row spacing; a duplicated margin found during browser verification was removed.

The historical revenue line, exact-value table, Daily/Weekly/Monthly order, existing Growth calculations and both centered empty states remain. Category still renders its actual recorded names, currency, shares and color-matched donut. It uses a left donut/right legend when card content has at least 240px reading width; narrower cards stack those elements. All categories remain accessible through the existing focusable list, with its height capped at 240px rather than extending the row indefinitely.

### 4. How it works: functions, inputs/outputs and data flow

The existing authorized view calls `build_marketplace_analytics()` and then `enrich_marketplace(analytics, user)`. The builder already divides recognized completed-paid revenue by its qualifying order count for `kpis.average_order_value`. Enrichment already queries the immediately preceding equal-length recognition-date period through `valid_sales_queryset(user)` and aggregates its revenue/count. The new `revenue_aov` dictionary reuses those inputs: `current` is the existing formatted AOV when the current count is positive; `previous` is the formatted prior revenue/count when that count is positive; absent counts yield `None`. `comparison_metric()` calculates percentage change from the unrounded Decimal averages only when both averages exist, retaining its existing zero-prior guard and rounding convention. Output is server-rendered HTML consumed only by the new card. No JavaScript calculation or extra database query was introduced.

Formula: `AOV = recognized revenue / qualifying completed-paid orders`; change is `(current AOV - previous AOV) / previous AOV * 100` when the previous AOV is nonzero and both periods have orders. An actual zero-price completed-paid order is a qualifying order and must produce a zero average, not N/A. An empty current period never produces a misleading -100% AOV change merely because prior sales exist.

Annotated isolated-test example: current recognized revenue 240 across three qualifying orders gives AOV 80; previous revenue 120 across one order gives AOV 120. Change is -33.33%, displayed as -33.3%. An unpaid 500 remains excluded. Current revenue zero across one qualifying order and prior AOV 50 gives AOV 0 and -100%; no current qualifying orders instead gives N/A. These are disposable-test examples, not live marketplace statistics.

### 5. Backend / API behavior

Only the read-only Super Admin presentation object is added. Existing Django/PostgreSQL aggregations, canonical recognized-sales eligibility, recognition timestamps, scoping, date filtering, comparisons and business workflows remain authoritative. Existing AOV KPI output is unchanged for its other consumers. No route, endpoint, controller, permission, model, other Analytics section or other-tab presentation changed. Existing query-growth regression coverage still applies because the AOV object reuses aggregates already loaded.

### 6. Database / migration impact

None. No schema, migration, working-record write, environment change, deployment or application restart. Regression tests use the existing disposable local PostgreSQL runner. Isolated browser exports and screenshots are under `scratch/marketplace-two-rows-20261102/`; they never supply operational metrics.

### 7. Tests performed

- Final affected suite: **62/62 Django tests passed** in 30.916 seconds, with no system-check issues. Includes explicit current-zero-value, rendered-percentage and missing-denominator assertions, plus existing eligibility/date/query-growth regressions. The initial suite also passed before those final assertions were added. The sandbox denied Python execution; the approved rerun used the disposable local PostgreSQL runner successfully.
- **2,331/2,331 Chromium checks passed across 60 navigations**, covering 280, 320, 390, 768, 1024, 1200, 1280, 1366, 1440 and 1920px; both populated/empty states, both row proportions, natural summary heights, padding/gaps, card order, no page overflow, donut/legend placement, keyboard access, exact data and AOV output. Daily/Weekly/Monthly, global date controls and forecast inputs were exercised on desktop/phone; no-JS, missing Chart.js and legacy-layout checks passed. A final subtitle update was then rendered against fresh Django exports: **201/201 additional checks passed across four desktop/phone navigations**. Actual desktop/phone empty and populated screenshots were visually inspected. Evidence: `scratch/marketplace-two-rows-20261102/result.json`, `final-render-result.json`, `check.cjs`, `final-review.cjs` and the sales PNGs. These are isolated rendered fixtures, not an authenticated deployed-site claim.
- Scope verification matched **58 unchanged protected source fingerprints**; the sole changed protected file is the intended AOV enrichment file. Orders-through-Insights assembly matches the saved pre-edit template exactly. Evidence: `scope-result.json` in the same scratch folder.
- Scoped `git diff --check` and browser-helper `node --check` passed. Backend functions/models outside the new read-only AOV presentation object were not edited.
- The optional design-doctrine bundled gate kit remains absent; no bundled gate score or accessibility certification is claimed.

Reproduce the affected Django suite from the project root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests
```

### 8. Remaining limitations, troubleshooting and safe practice

The desktop proportions start at 1200px; narrower screens intentionally stack all four cards in reading order. Summary heights remain natural, so their lower edges need not match a populated chart containing a full data table. Large category lists use contained keyboard scrolling; no category is silently discarded. Browser fixtures do not prove deployment or an authenticated live browser session. Percentages follow the existing helper's rounding and need not match a percentage recomputed from two already-rounded currency labels.

If the old three-card row remains, hard-refresh and inspect the new CSS cache key. If AOV is N/A, inspect the period's qualifying order count before treating it as a calculation failure. If prior AOV is zero, N/A percentage change is correct. Check recognition dates, not only creation dates, when reconciling sales and prior comparisons.

Safe exercise: open a populated period without editing records. Divide displayed recognized revenue by completed-paid orders and compare the rounded result with AOV; repeat for the displayed prior period. Change Daily to Weekly to Monthly and confirm the period totals, AOV and category shares stay constant while chart buckets change. Choose an empty date range and confirm AOV N/A, then inspect the four-card stack on a phone. Restore the original period. For a small code exercise, edit only the new card's descriptive subtitle locally, verify it on desktop and phone, and revert it without touching queries or records.

## Current: Marketplace revenue empty states - November 2, 2026

### 1. Cause / reason

Confirmed in the templates: the Marketplace branch of `analytics_chart.html` rendered only `empty_title`, discarding the supplied helper text. Category used a separate plain paragraph. The Sales Trend selector listed Monthly, Weekly, Daily. The user requested matching centered chart empty states, chronological selector options, and a compact Growth explanation.

### 2. Exact files changed

Paths are relative to the project root; line numbers refer to this update.

| File | Current line / nearby anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/modules/reports/templates/reports/partials/marketplace_chart_empty.html` | 1 `.marketplace-chart-empty` | New reusable partial renders a decorative line/pie SVG, title and helper text. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart.html` | 5 `marketplace_sections and empty_icon` | Opts the requested Marketplace chart into that partial; other chart-empty branches retain their presentation. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 21 grouping options; 27 sales chart include | Orders options Daily, Weekly, Monthly; supplies the exact Sales Trend helper and line icon. Existing selected grouping and GET inputs remain. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_revenue_category.html` | 14 empty branch | Uses the shared pie empty state with “No Category Sales Yet” and the requested helper text. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_refined_panels.html` | 5 revenue definition list; 6 missing denominator | Adds label colons and the exact “Previous revenue is zero, so growth cannot be calculated.” explanation. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 66 Sales Trend flex layout; 67 `.marketplace-chart-empty` | Centers the shared body and 28px icon, reuses existing colors, caps helper measure, and reserves no fixed drawing height. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 refinement stylesheet | Updates its cache key so browsers fetch the new CSS. |
| `docs/superadmin-analytics-module.md` | 3 this report | Records cause, data flow, verification, troubleshooting and practice. |

### 3. Changes made

Sales Trend and Sales by Category now share a centered title/helper/icon treatment. The period/grouping controls remain visible. Natural content height, modest padding and no empty canvas avoid a large blank plot. Existing desktop row alignment and responsive rearrangement stay intact. Growth keeps its value, current/prior revenue and explanation, without a large icon. Empty revenues are the actual formatted server values, not hardcoded placeholders.

### 4. How it works: functions, inputs/outputs and data flow

No Python function changed. The existing authorized view calls `build_marketplace_analytics()` and enrichment, supplying `has_sales`, `category_has_revenue`, `category_sales`, `kpis.sales` and `comparison`. `analytics_chart.html` still renders a canvas/table when `has_data` is true. When false, the explicit `empty_icon` parameter selects the new partial only inside `marketplace_sections`. Its inputs are `empty_icon`, `empty_title` and `empty_text`; output is ordinary server-rendered HTML, with decorative SVG hidden from assistive technology. Category calls the same partial when its existing no-category-sales branch is reached. Actual zero-price category records retain their distinct explanation and data table.

Annotated example: `has_sales=False` plus `empty_icon='line'` produces the line icon and sales message; it does not create a dataset. `percentage_change=None` displays N/A and the zero-baseline explanation. A current revenue of 100 with a prior revenue of zero must continue to show 100, rather than a fabricated zero. CSS flex alignment shares available card space without adding a minimum chart height. Existing GET submission sends `grouping=daily|weekly|monthly`, preserving selected dates and forecast inputs; option order does not change the backend default.

The shared partial was chosen so both requested cards use identical markup and spacing without changing unrelated analytical empty states.

### 5. Backend / API behavior

No query, calculation, route, controller, API, permission or sales-eligibility change. Completed-paid recognition and prior-period comparison remain authoritative. The shared selector also shows the chronological order on the legacy Marketplace Analytics layout; its behavior remains the same.

### 6. Database / migration impact

None. No model, migration, working-record write, deployment or server restart. Verification exports are isolated disposable-test records under `scratch/marketplace-empty-states-20261101/`, not operational data.

### 7. Tests performed

- 61/61 existing affected Django tests passed in 25.235 seconds, with no system-check issues. Used `scratch/operating-schedule-20261029/run_tests.py` for a disposable local PostgreSQL database; the sandbox initially denied Python execution and the approved rerun succeeded.
- 1,972/1,972 Chromium checks passed across 58 navigations. Empty and populated layouts cover 280, 320, 390, 768, 1024, 1280, 1366, 1440 and 1920px; focused empty checks verify exact wording, two decorative 28px icons, centered unclipped content, cards below 420px, no Growth icon, zero current/prior amounts and visible chronological options. Daily/Weekly/Monthly, global date and forecast controls were exercised on desktop and phone. Existing populated series/category totals, desktop proportions/heights, fallback rendering, legacy chart and other section checks passed. Desktop/phone empty screenshots and a populated desktop screenshot were visually inspected. Results: `scratch/marketplace-empty-states-20261101/result.json`; browser helper: `check.cjs` in that folder. These are isolated fixtures, not a deployed live-browser claim.
- Scoped `git diff --check` passed for changed tracked application files.
- The optional design skill's bundled token/gate kit is absent from this checkout. No bundled gate score or accessibility certification is claimed.

Reproduce Django checks from the root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests
```

### 8. Remaining limitations, troubleshooting and safe practice

The browser review uses isolated Django-rendered fixtures; it does not prove a deployment or authenticated live session. Zero-price category sales deliberately keep their distinct factual message/table. No changes to error/loading states or sales calculations were requested.

If old spacing appears, hard-refresh and inspect the `20261101-marketplace-empty-states` CSS URL. If an empty card appears unexpectedly, inspect completed/paid eligibility and recognition dates in the selected period before changing presentation code. N/A with previous revenue zero is expected even when current revenue is positive.

Safe practice: choose a date range with no eligible sales, confirm both exact helper messages and the compact N/A summary, then select Daily, Weekly and Monthly. Confirm the selection persists and dates remain unchanged. Choose a populated period and verify the real charts/table return. For a small local code exercise, edit only `empty_text` in the sales include at line 27, render the empty page to confirm that text reaches the shared partial, then revert it and restore the requested wording. This exercise requires no record changes.

## Current: Six-section Marketplace and sales/revenue row — November 1, 2026

### 1. Cause / reason

The current Marketplace implementation already had the requested operational, product, seller and recommendation calculations. Its opening group still combined Overview and sales analysis, used a mixed bar/order chart, placed Category below the sales row, lacked category color indicators/center total, and described an empty prior revenue baseline with words instead of N/A. This follow-up implements the new six-section layout and revenue-only line without rebuilding the module or changing recognition rules.

### 2. Exact files changed, current lines and anchors

| File, relative to project root | Current line / anchor | What changed and why |
| --- | --- | --- |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 3 Overview; 7 Sales & Revenue; 11 `marketplace-revenue-grid` | Separate the unchanged four Dashboard-style KPIs into Overview, then place Sales Trend, Growth and Category in one independent-card grid. Orders through Insights keep their original assembly. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 12 Sales Trend; 50 `marketplace_revenue_category.html` include | Rename only the opted-in Super Admin sales card and select the new category presentation. Keep the grouping form, JSON/chart IDs, exact sales table and legacy-role branches. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_revenue_category.html` | 1 category card; 6 center total; 9 ranked legend | New small presentation partial: actual category names, currency amounts and shares beside the donut; server-rendered total inside its center. Category list is keyboard-focusable and scrolls only when its real content exceeds the bounded height. Zero-price data retains its exact table; missing sales produces no invented segments. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_refined_panels.html` | 4 growth percentage; 5 current/prior revenue; 6 explanation | Show N/A with a zero previous revenue denominator. Remove the duplicated paid-order comparison row from Growth; current completed orders and exact sales-period order counts remain in Overview/the sales table. Other panel branches are unchanged. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 63 revenue grid and subsequent scoped rules | Use 5:2:3 columns from 1280px, equal card heights, 16px gaps and existing 24px section spacing. At 900–1279px, Trend spans above Growth/Category; narrower screens stack. Category container queries keep the donut left and a readable legend right when at least 240px of content width is available, otherwise stack them. Preserve the KPI styling and all other section layouts. |
| `backend/static/components/js/admin_marketplace_analytics.js` | 6 `refinedMarketplace`; 109 line chart; 117 responsive ticks; 232 category palette | Draw one revenue-only historical line on this Super Admin page. Keep zero values, actual labels/tooltips and existing controls. Match segment/indicator colors using the same ordered palette. Fit the existing numeric center label without altering its text. Other-role mixed charts retain their existing branch. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 CSS cache key; 90 controller cache key | Update Super Admin asset versions to `20261101-marketplace-revenue-row`; legacy-role cache references remain unchanged. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 308 section assertions; 571 `test_revenue_row_uses_paid_categories_zero_intervals_and_equivalent_growth`; optional exports | Verify six sections, paid recognition, category ordering/amount/share, zero intervals, equivalent growth and honest empties. Optional isolated fixtures cover many actual test-record categories, long names, more than six palette entries, grouping/date/horizon controls and the legacy layout. |
| `docs/superadmin-analytics-module.md`, `CAMPUSHUB_CONTEXT.md`, `docs/web-ui-ux-guidelines.md` | Current six-section entries | Preserve the latest requested layout and measured verification, with debugging and a safe learning exercise. |

Verification helpers and screenshots are in `scratch/marketplace-sales-row-20261101/`. They do not supply production data. The private existing `marketplace-five-sections` root class remains for compatibility with existing chart hooks; the visible page and section attributes now have six groups.

### 3. Changes made

Overview retains Total Sales Revenue, Completed Orders, Active Sellers and Approved Products with the Dashboard-matched top-right icons. Sales & Revenue contains the requested 50%/20%/30% card proportions, measured after the two 16px gutters. Trend is a navy line with dates, revenue axis, responsive tick spacing and exact tooltips. Growth uses the same server comparison and renders one decimal or N/A when the prior revenue is zero. Category keeps all real categories, sorted by the existing revenue calculation, with currency/share values and matching indicators; no product names are substituted for categories.

Cards share padding and desktop heights. No empty plotting surface is rendered when no qualifying sales exist. The category list gets a scrollbar only when its actual rows exceed 360px; all categories remain available rather than being silently omitted or renamed Others. Narrow exact-value tables retain columns through native overflow; chart headers and phone date ticks were adjusted after actual visual review to prevent crowded labels.

Orders & Payments retains all three performance KPIs, comparison, volume/status and payment/fulfillment pairs. Product & Inventory retains its five supported views and history guards. Buyers & Sellers retains Buyer Activity, the stable-ID sortable ranking and separate fulfillment table. Insights retains its four independent responsive 2×2 cards, actual forecasting/Apriori and restock guards, without Dashboard bundle cards. The Dashboard, Facilities, Services and Users pages were not redesigned.

### 4. Functions, inputs/outputs and data flow

The existing authorized view still calls `build_marketplace_analytics()` and Super Admin enrichment. `valid_sales_queryset()` supplies the existing eligible completed-paid positive-quantity records and recognition timestamp. `_sales_time_series()` already fills zero intervals for Daily/Weekly/Monthly; its arrays and exact-value table are unchanged. The template passes its JSON to the existing controller, whose new `.marketplace-refined` branch draws the one revenue line. Completed-order data remains available in the existing response/table; it is not relabeled as money or included in revenue.

`_category_sales()` still reuses `sales_by_product_category()`: recorded sale category first, surviving product category as a legacy fallback, then Uncategorized; recognized revenue descending, category name as a tie-breaker. Django renders the same category list into the new definition-list legend. Both donut and indicators use the same navy/gold/neutral palette index, cycling consistently for additional categories. The center uses the server's already-formatted recognized revenue total. The small `fitTotal()` callback changes only font sizing; it never calculates or replaces amounts.

Growth still receives `comparison_metric()` output for the immediately preceding equal-length recognition-date range. A zero previous amount yields no percentage denominator and is presented as N/A. Changing dates or grouping submits the existing GET forms and preserves forecast selections/custom dates. Category amounts sum to recognized revenue; one-decimal shares can have small rounding differences from 100%.

Annotated isolated verification example: selected paid category totals Books 160 and Food 80 produce recognized revenue 240 and shares 66.7%/33.3%; an unpaid 500 is excluded. Previous eligible revenue 120 produces +100% growth. A selected 19-day daily series has 18 zero intervals when all qualifying current sales occurred on one day. These are regression-test records, not working Marketplace statistics.

### 5. Backend / API behavior

No application Python calculation, API, route, permission, scope, recognition timestamp, inventory rule, Apriori rule or forecasting method changed. Operational submission analytics still include unpaid orders; recognized revenue still excludes them. Stable seller identities, historical comparison dates, current inventory labels, empty states and working links/actions remain intact. Only the Super Admin Marketplace marker selects the new visual chart branch; the Marketplace Admin mixed chart and existing category branch are retained and verified.

### 6. Database / migration impact

No model, migration, schema, working-record or audit-writing changes. Tests use the existing disposable PostgreSQL runner, and actual local database verification runs under `SET TRANSACTION READ ONLY`. No generated images, environment changes, server restart or deployment. Screenshot files are actual browser renders for verification, not application assets.

### 7. Tests performed

- **61/61 affected Django tests passed** across `modules.reports.test_superadmin_analytics` and `modules.reports.tests.MarketplaceAnalyticsTests`; final suite took 30.043 seconds, with no Django system-check issues. Two additional focused fixture/legacy-HTML checks passed after the final accessibility markup update.
- **1,248/1,248 Chromium checks passed across 34 navigations**, at widths 280, 320, 390, 768, 1024, 1280, 1366, 1440 and 1920px. Checks cover six headings, exact 50/20/30 proportions and equal heights, KPI icons/values, Daily/Weekly/Monthly, date presets/custom dates, forecast horizon, zero-inclusive revenue arrays, N/A/rounded growth, every category amount/share/order, palette cycling, center total, keyboard scrolling, no page overflow, retained operational/Insights cards, no-JS and missing-library fallback. The legacy-role mixed chart is also checked. Actual final phone/desktop and empty-state screenshots were inspected. These are isolated Django-rendered fixtures, not a deployed authenticated live-browser test.
- **Actual local PostgreSQL:** all four existing Analytics views return HTTP 200 under READ ONLY. Marketplace now renders six groups. Canonical revenue/orders, operational/payment/fulfillment totals, stock-health counts, seller identity uniqueness, historical comparisons and Users registration parity reconcile. Zero writes and unchanged record counts. Local query counts remain Marketplace 39, Facilities 52, Services 13, Users 19.
- **Scope:** all 59 captured protected source fingerprints match, covering backend definitions, Dashboard presentation, shared Analytics styles/controller and other-tab templates. Orders-through-Insights section assembly matches its exact pre-edit text.
- **Static:** `node --check` for the changed chart controller and scoped tracked-file `git diff --check` passed. Backend calculation source was not edited.

Run the affected suite from the project root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests
```

Measured results: `scratch/marketplace-sales-row-20261101/result.json`, `local-result.json`, `scope-result.json`. Optional fixture exports remain outside the application templates/static directories and never replace real records.

### 8. Limitations, troubleshooting and safe practice

The three-card desktop row begins at 1280px to protect chart/legend reading width. Smaller layouts intentionally rearrange rather than squeeze all three cards into a narrow row. Very long category lists require contained native scrolling; the focusable legend supports keyboard scrolling and a visible focus outline. Currency in the donut center can shrink to fit; the same full amount remains in the accessible description and legend. Modern container queries improve internal arrangement; older browsers fall back to a stacked category body without hiding data.

If a line appears empty, check eligible completed/paid records and recognition dates, not just submission dates. If growth says N/A, inspect the displayed prior revenue before interpreting it as a failure. If category colors or layout are stale, verify the updated CSS/controller cache keys; the DOM list and Chart.js datasets must use the same ordering. Missing Chart.js hides plotting containers while leaving actual labels/tables and the existing fallback messages. Forecast, Apriori and turnover reliability limits remain as documented in the earlier capstone section; no missing-data guard was weakened to fill a card.

Safe exercise: open Marketplace Analytics read-only on desktop, confirm four KPI cards and the three sales cards, then change grouping from Daily to Weekly to Monthly. Verify the recognized total/category amounts stay the same while time buckets change. Select another valid date range and verify Growth's prior dates move with it. On a phone, inspect the rearranged cards and full table columns; focus the category list and use End/Home when scrolling is needed. Restore Last 30 Days. For code learning, trace the unchanged `sales_chart.sales` JSON into the new line dataset and the same ordered `category_sales` into the legend; shorten one caption locally, run the command above, inspect both widths and revert it without touching order data.

## Previous: Capstone historical comparisons and planning reliability — November 1, 2026

The current six-section report above supersedes older Marketplace group names, sales chart presentation and category placement. Earlier reports retain their implementation-time line references and verification scopes; their backend definitions and reliability safeguards remain in force.

### 1. Cause / reason and what was already implemented

Inspection confirmed that the Dashboard already has the four historical trends requested: eligible paid/completed Sales, physical booking submissions, Service Request submissions and web/mobile User Registrations. None needed a forecast series. The four Analytics tabs already provide date filters, historical charts and detailed breakdowns; Marketplace already has equivalent-period sales growth, real seven-day moving-average forecasting and real pair-based Apriori calculations. Users already compares registration periods. Facilities already reuses verified capacity calculators rather than inventing utilization. Service timing already uses dedicated workflow timestamps.

Confirmed gaps were missing operational previous-period comparisons; duplicated booking/registration query definitions; forecast eligibility that counted the selected calendar span without checking the product's observed span or recent demand; an Analytics semester range extending into future dates; and Restock copy that mixed a current inventory snapshot with projections from past dates. Product-level stock sums also cannot safely prescribe a variant/component-specific quantity. No persisted-data corruption or statistical forecast-accuracy claim was established.

### 2. Exact files changed, current lines and anchors

| File, relative to project root | Current line / anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/analytics.py` | 1 module definition; 78 semester; 460 `_forecast`; 753 forecast call | Correct the description of fulfillment-independent eligible sales, cap semester observations to the most recently started historical semester, reuse the authorized sales queryset, verify observed/recent demand, expose training coverage and inventory-review flags. Preserve the original recursive seven-day moving-average arithmetic. |
| `backend/core/modules/reports/dashboard_bookings.py` | 16 `booking_request_records` | Shared physical/service submission populations, excluding structured schedule blocks while retaining archived historical facilities. No chart type or forecast added. |
| `backend/core/modules/reports/dashboard_executive.py` | 19 `registration_daily_counts`; 36 users; 57 services; 109 physical bookings | Extract the original two registration-date queries and reuse the shared booking populations. Dashboard trend payload definitions remain historical and numerically equivalent. |
| `backend/core/modules/reports/analytics_sections.py` | 107/130 facilities; 339/340 services; 436/437 registrations | Reuse those existing Dashboard definitions for Analytics. Aggregate shared daily account counts into existing monthly buckets without adding per-day queries. Preserve separately labeled booking/stay-date reservation KPIs and current-catalog filtering. |
| `backend/core/modules/reports/superadmin_analytics.py` | 26 `submission_comparison`; 153 Marketplace; 192 `restock`; 327 Facilities; 340 Services | Add one equal-length cohort comparison query per operational tab and read-only restock eligibility metadata. Keep existing rates, inventory, turnover and forecasts authoritative. |
| `backend/core/modules/reports/templates/reports/partials/analytics_submission_comparison.html` | 1 independent card | New reusable comparison table: recorded outcome, selected/previous count, absolute difference and percentage change. Actual dates and current-outcome cohort meaning are explicit. Both-empty periods use one compact message. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 22 comparison include | Show the operational order comparison separately from recognized-sales growth and the existing trend/status cards. |
| `backend/core/modules/reports/templates/reports/partials/analytics_domain_sections.html` | 24 Facilities; 44 Services | Place comparisons inside the appropriate existing sections. Users retains its existing registration-growth comparison. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 118 summary; 119 method/training note; 120 insufficient coverage | Show real training dates/counts, retain the dedicated Analytics forecast, label unsupported aggregate stock gaps and explain coverage, partial-current-day observations and stockout limitations. Four Performance KPI cards are unchanged. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_refined_panels.html` | 38–40 Restock | Clearly separate forecast-based quantities from threshold-based inventory reviews; suppress direct quantities for past projections and component/variant/expiry review cases. Link the existing consolidated inventory alerts. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 451 exact forecast; 471 coverage; 488 restock; 518 shared bookings; 545 registrations; 562 live associations | Add numerical, coverage, source-parity, historical-period and synthetic-isolation regressions. Extend only the optional isolated browser fixture to provide sufficient observed history. |
| `docs/superadmin-analytics-module.md`, `CAMPUSHUB_CONTEXT.md` | Current capstone entries | Record inspection, changes, functions/data flow, calculations, measured checks, limitations and safe practice. |

All Dashboard presentation templates/CSS, chart JavaScript, existing APIs, model files and migrations were left untouched by this follow-up. Verification helpers and rendered fixtures are under `scratch/analytics-reliability-20261101/`, separate from production data.

### 3. Changes made

- Marketplace, Facilities and Services now compare the selected submission cohort with the immediately preceding equal-length cohort, including their actual recorded outcome breakdowns. Positive counts after an empty prior period say New activity instead of inventing a percentage. Users retains its working registration comparison.
- Dashboard and Analytics now call the same physical/service population helper and the same registration-date helper. Sales already shared `valid_sales_queryset()` and retain it. No forecast was added to Sales, Bookings, Service Requests or User Registrations on the Dashboard.
- Demand Forecast still uses the existing recursive seven-day moving average. Eligibility now requires at least 14 observed days, three positive-sales days, seven eligible units and positive demand in the final seven days. Observation begins no earlier than selected dates and documented catalog/sales evidence, and stops at the selected end or today. Future-dated sales cannot enter training. Coverage, units and transaction counts are displayed; no accuracy percentage is invented.
- The Analytics semester filter uses the most recently started Aug–Dec semester and ends no later than today. Before August, that is the previous year's completed first semester. Custom ranges and the other working filters retain their definitions.
- Restock uses currently available inventory, which already reflects reservations. It never subtracts reserved orders twice. Forecast-based quantity is available only for sufficient demand through today and a directly usable simple-stock basis. Historical projections, separately tracked variants, component-derived bundles and expired stock require review; product-level sums cannot determine which variant/component to replenish.
- Threshold reviews remain based on actual product/variant stock at or below configured warning levels. The count describes the displayed shortlist, up to ten, not an invented global alert total. These reviews are explicitly not forecasts and do not prescribe a made-up order quantity.
- Product Association Analytics keeps its actual support, confidence, lift and transaction counters. Live analysis never imports the synthetic research cache. No association or recommendation is generated merely to fill an empty card.

### 4. Functions, inputs/outputs, calculations and data flow

The existing permission-checked views resolve selected dates and invoke their existing builders. Shared query helpers supply model-backed populations, builders supply historical chart series, and Super Admin enrichment supplies comparison/restock metadata. Django renders independent existing cards and the small new comparison partial. Existing JavaScript renders the supplied series and preserves date controls, sorting, navigation, exact-value tables and missing-library states. No new analytics API or database model was added.

| Calculation / function | Inputs and output | Verification and practical meaning |
| --- | --- | --- |
| `valid_sales_queryset()` | Completed, explicitly paid, positive-quantity orders; recognition time is completed time, otherwise paid time, otherwise creation time | Existing revenue regressions, midnight/zero-price cases and read-only PostgreSQL reconciliation remain green. Pickup/Delivery are separate fulfillment states; delivered/unpaid records never become revenue. |
| `booking_request_records(services=...)` | Existing Booking rows, existing service catalog classifier and schedule-block predicate | Both Dashboard trends and Analytics submission comparisons count the same population. Archived facilities remain part of submission history. A regression includes current/prior records and a structured block. |
| `registration_daily_counts(period)` | Web `date_joined` and mobile `created_at`, grouped in the configured local timezone | Dashboard daily trend and Analytics monthly totals reconcile with selected registrations. Both still count account records, not deduplicated people. Existing query budgets remain satisfied. |
| `submission_comparison()` | Current/prior `created_at` cohorts and the existing status choices | Absolute difference = current minus previous; change = difference / previous × 100 only with a positive prior count. A test checks 2 current versus 1 prior gives +1 and +100%. Unknown outcomes, if present, remain in an Other/unrecorded row. |
| Existing Facilities utilization | Verified slots/hours/room-nights and approved/completed usage in the selected schedule window | Existing utilization/capacity regression modules pass. Unknown capacity stays unavailable. Reservation KPIs use booking/stay dates in the current catalog; submission comparisons use created dates and retain archived history. Those different labels/populations are intentional, not silently interchangeable counts. |
| Existing processing/approval rates | Recorded current outcomes and valid dedicated approval/completion timestamps | Existing timing regressions pass, including missing/invalid timestamps. No `updated_at` substitution, payment inference or automatic results-release inference was introduced. |
| `_forecast()` | Authorized eligible product daily units, selected dates, catalog/sales evidence and current stock | Next day = mean of the final seven observations; recursively append that unrounded mean and repeat. Display each prediction rounded to two decimals; forecast total remains the ceiling of the sum of those displayed daily predictions. Original arithmetic is retained. |
| Forecast coverage | Observed span ≥14 days, positive-sales days ≥3, eligible units ≥7 and final-seven-day units >0 | New tests reject a fresh three-day history and stale demand even when a 30-day range is selected. A deliberately future-dated isolated test row is excluded. Thresholds are conservative project safeguards, not proof of forecast accuracy or historical stock availability. |
| Forecast stock gap / `restock` | `max(projected units − currently available units, 0)` plus operational/inventory-review guards | Fourteen observed days selling two units each yield a seven-day projection of 14; available 3 yields gap 11. A varying final week verifies recursive outputs 4.00, 4.43, 4.78 and a seven-day total of 34. These are isolated numerical fixtures, not production statistics. |
| Threshold review | Existing `low_stock_inventory_rows()` with actual available quantities and configured warning levels | Existing inventory tests plus new restock tests verify actual stock use, expiry review and variant totals. No lead time, safety stock, purchase cost or quantity is invented from a threshold. |
| Existing Apriori rules | Actual completed-paid transaction item sets | Support(A,B) = together / eligible transactions; confidence(A→B) = together / A transactions; lift = confidence / B's transaction share. Existing numerical tests verify these ratios and detailed counters. Confidence here is a descriptive association metric, not a statistical confidence interval. |

The Dashboard's monthly comparison policy may compare the same elapsed days of the previous calendar month, while Analytics explicitly labels its immediately preceding equal-length period. Current count definitions are shared; a different clearly labeled comparison policy should not be forced into identical date ranges. Likewise, Dashboard Users by Type describes recorded mobile types; Analytics separately includes web and unclassified account categories with its stated denominator.

### 5. Backend / API behavior

Permissions and existing routes remain unchanged. New comparison metadata is server-calculated and respects existing scoped order access. Shared helpers do not authorize requests; the existing views retain that responsibility. Date filters update historical observations/comparisons; inventory/product/account status values remain labeled current snapshots. Forecast product/horizon controls still work, and short selected windows honestly become insufficient. No marketplace order, cash payment, delivery, booking, service or account workflow changed.

### 6. Database / migration impact

No model/migration/schema changes and no production/synthetic data import. All application calculations are read-only. Automated records exist only in the disposable local PostgreSQL test database. Actual local database verification used `SET TRANSACTION READ ONLY`, confirmed no write queries and unchanged protected record counts. No environment edit, server restart, deployment or image generation was performed.

### 7. Tests performed and results

- **146/146 Django regression tests passed** across Super Admin Analytics, Marketplace calculations, executive/booking/marketplace/service/KPI Dashboard modules, utilization and inventory accuracy. The final broad run took 52.753 seconds and Django's system check reported no issues. Two additional focused reruns refreshed isolated fixtures and rechecked query scaling; both passed.
- **1,954/1,954 Chromium checks over 88 four-tab navigations**, plus **612/612 focused Marketplace checks over 22 navigations**, passed at eight widths from 280px through 1920px. Checks include exact comparison rows, actual chart arrays, date changes/tab preservation, responsive table overflow, no page overflow, honest forecast gating, distinct threshold/forecast copy, empty states, no-JS and missing-Chart.js fallback. Actual desktop/phone comparison and Insights screenshots were inspected. These are isolated Django-rendered fixtures, not a deployed authenticated browser test.
- **Actual local PostgreSQL reconciliation:** all four existing Analytics views returned HTTP 200 under READ ONLY. Revenue/counts match canonical eligible sales; order volume/payment/fulfillment reconcile; new submission comparisons reconcile in Marketplace/Facilities/Services; Users registrations match the Dashboard definition and monthly totals. Record counts unchanged, zero writes. View query counts on that local dataset were Marketplace 39, Facilities 52, Services 13 and Users 19, including rendering/permission/notification work.
- **Performance:** refined Marketplace builder/enrichment uses **34 queries with both 1 and 51 orders**. The new comparison adds one aggregate query; it does not add a query per order. Existing Users ≤18-query and capacity two-query tests still pass. This is query-count evidence, not a production latency guarantee.
- **Scope/static:** 46 stored Dashboard presentation fingerprints match the pre-existing baseline; no Dashboard template/CSS change. Six affected Python files pass AST parsing, and tracked Marketplace service `git diff --check` passes. No chart JavaScript was changed.

Run the focused suite from the project root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests modules.reports.test_dashboard_executive modules.reports.test_dashboard_bookings modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_services modules.reports.test_dashboard_kpi_cards modules.reports.test_dashboard_utilization modules.reports.test_inventory_report_accuracy
```

Measured artifacts are `scratch/analytics-reliability-20261101/browser-result.json`, `browser-services-result.json` (focused Marketplace run; inherited helper filename), `local-result.json`, `scope-result.json` and `query-fixtures/query-count.json`. Browser fixture records never feed live pages.

### 8. Limitations, debugging and safe practice

- Minimum forecast coverage is not a validated accuracy guarantee. Paid sales can understate unmet demand during stockouts; the current day may be partial. No seasonality, lead time, safety stock, confidence interval or backtested accuracy percentage was fabricated. A longer, representative real dataset is needed before claiming predictive accuracy.
- Catalog timestamps plus actual eligible sales bound the observed window; they do not reconstruct historical availability. Missing history cannot be fixed by widening dates to include days before any catalog/sales evidence. Past projections use current stock only as a labeled scenario, never as reconstructed past inventory.
- Product-level variant/component stock is not interchangeable. The forecast may describe aggregate sold product units, but operational variant/component replenishment is withheld until the relevant stock mix is reviewed. No expiry clearing or component adjustment happens automatically.
- Comparisons describe submission cohorts classified by currently recorded outcomes. They do not reconstruct each record's status at the old period end or measure status transitions during that period. Compare the displayed date basis before treating different reservation/submission counts as an error.
- Current order codes are unique per sellable-product order and therefore cannot establish genuine shared-checkout pairs. Product Association Analytics exposes actual eligible/multi-item coverage and remains insufficient when that evidence is absent. It never combines buyer/day records or imports synthetic research transactions. The real algorithm's sufficient-data branch is tested using explicit isolated item sets, not invented working transactions.
- If a forecast disappears, inspect observed days, positive-sales days, eligible units and the final seven days before changing any threshold. If a restock quantity is absent, check historical-date, component, variant and expiry guards. If a comparison seems inconsistent, check submission versus booking/stay dates, archived-history coverage and the explicitly displayed prior dates.

Safe practice exercise: choose the same explicit custom dates on Dashboard and Analytics. Compare sales revenue, physical/service submissions and new registrations using their stated date bases. Inspect the new current/prior rows, then select a short seven-day window: the historical charts should remain real while Demand Forecast shows insufficient coverage. Restore a supported range ending today, inspect Threshold-based versus Forecast-based guidance, and confirm that an old custom range produces historical planning copy instead of an operational restock quantity. Do not create orders, alter stock or import research data just to fill cards. For code learning, trace `booking_request_records()` → the existing builder → `submission_comparison()` → its Django partial, then run the command above after a safe local copy-only wording change and revert it.

## Previous: Marketplace Performance KPI styling — November 1, 2026

Earlier sections below retain their implementation-time line references and measured results. The capstone report above supersedes forecast coverage, Restock guidance and shared historical-definition details; the four KPI cards retain their Dashboard-matched styling.

### 1. Cause / reason

The four Marketplace Performance KPIs lacked the Super Admin Dashboard's title/icon arrangement. This follow-up changes only those four cards. Their existing labels, metric expressions, descriptions, date meaning and calculations remain intact. The final Dashboard cascade was inspected, including `admin_dashboard_summary.css`, `admin_dashboard_operations.css` and `admin_executive_refinement.css`; using only the earlier summary rules would miss later size overrides.

### 2. Exact files changed, current lines and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 2 `marketplace-performance-kpis`; 3–6 four `dashboard-stat-card` articles | Reuse Dashboard card/icon class names and insert decorative Wallet, Shopping Bag, Store and Package Check inline SVGs only when the existing `marketplace_sections` flag is set. All original Django metric expressions and description text are preserved. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 2 Dashboard reuse comment; 3–28 `.marketplace-performance-kpis` rules | Match the final Dashboard card's 16px padding, 10px radius, 144px minimum height, white surface, subtle border, navy title/value, 28px bold metric and 32px bordered light icon container. Keep the existing responsive one/two/four-column grid and 16px gaps; equal fractional rows allow longer content to grow without clipping. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 `20261101-performance-kpi-icons` | Bump only the Marketplace refinement stylesheet cache key so browsers load the changed card styles. |
| `docs/superadmin-analytics-module.md` | 3 current KPI report | Explain this focused change, data flow, verification and safe practice. |

Dashboard templates/styles, other KPIs, other Analytics tabs and backend modules were not edited in this follow-up. Verification material is in `scratch/marketplace-kpi-20261101/`.

### 3. Changes made

Each card keeps a title on the left and a small icon on the right in the same grid row. The large value spans the next row and the original description stays below it. Wallet identifies Total Sales Revenue; Shopping Bag identifies Completed Orders; Store identifies Active Sellers; Package Check identifies Approved Products. Icons are navy inside a 32px light container with a subtle full border. Card heights remain equal while accommodating wrapped titles/descriptions on phones.

### 4. How it works / inputs, outputs and data flow

The unchanged authorized view calls the existing analytics builder/enricher and passes `analytics.kpis` and `analytics.period` to Django. The existing Super Admin section partial supplies `marketplace_sections=True`, then includes the card partial with `card='kpis'`. That branch adds the scoped class names and SVG markup; CSS lays out the existing text and numbers. No JavaScript, icon library, external image or new calculation is required. For example, `{{ analytics.kpis.completed_orders }}` still prints the existing completed-order count; the Shopping Bag SVG beside its title neither reads nor changes that value. The icon containers use `aria-hidden="true"` because their visible titles already identify the metrics.

Dashboard CSS is guarded by Dashboard-specific ancestors. Importing the whole Dashboard stylesheet into Analytics would affect unrelated components, while changing its guards would expand this task's scope. This implementation reuses the card/icon class names and matches their final computed styles inside `.marketplace-performance-kpis` only. Keep that scope when adjusting these cards.

### 5. Backend / API behavior

No backend/API/query/permission/filter changes. The existing Django values, descriptions and eligible-sales definitions remain authoritative. Legacy Marketplace Admin rendering does not opt into the new classes or icons.

### 6. Database / migration impact

No models, migrations, records or audit paths changed. The four focused Django checks used the existing disposable PostgreSQL test runner; no working-database writes were needed for this presentation change.

### 7. Tests performed

- **4/4 focused Django checks passed**: optional isolated fixture rendering, Super Admin tab access, Marketplace Admin restrictions and settled/completed revenue calculations. Django system check reported no issues.
- **320/320 focused Chromium checks passed over 16 renders**, covering empty/populated states at 280, 320, 390, 600, 768, 1024, 1280 and 1440px. Checks compare card, title, value, description and icon computed styles against a separate reference using the actual Dashboard stylesheets. They also verify canonical values, exactly four requested icons, decorative accessibility, title/icon alignment, equal heights, left-aligned values, 16px gaps and no page overflow.
- Inspected the actual 1440px and 390px KPI screenshots. These are isolated Django-rendered fixtures, not a deployed live-browser test.
- **54 protected fingerprints remain unchanged**, including the Dashboard and other Analytics layout files/domain helper tail. Scoped tracked-file `git diff --check` passed.

Backend verification command from the project root:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics.SuperAdminAnalyticsTests.test_optional_marketplace_refinement_exports modules.reports.test_superadmin_analytics.SuperAdminAnalyticsTests.test_super_admin_can_access_all_four_tabs modules.reports.test_superadmin_analytics.SuperAdminAnalyticsTests.test_marketplace_admin_restricted_from_other_tabs modules.reports.test_superadmin_analytics.SuperAdminAnalyticsTests.test_marketplace_sales_revenue_derives_only_from_settled_completed_orders
```

### 8. Remaining limitations / troubleshooting and safe practice

No known issue remains in the verified states. Very large real values can wrap instead of overflowing, and the cards grow together. If icons or styling appear stale, confirm the new CSS cache key and the `marketplace-performance-kpis` class; no icon script needs initialization. Later Dashboard styling changes will need an intentional update to this scoped match. No deployment was performed.

Safe practice: open Marketplace Analytics at desktop and phone widths, confirm all four titles/values/descriptions, then change Last 30 Days to an existing supported range. The values should follow the unchanged filter while icon placement stays consistent. To learn the markup safely, locate `data-kpi-icon="shopping-bag"`, identify the nearby unchanged `analytics.kpis.completed_orders` expression, and inspect the corresponding grid-row rules in browser developer tools without editing order records. Restore Last 30 Days afterward.

## Previous: Marketplace refinement — November 1, 2026

The KPI styling report above supersedes the four performance cards' earlier visual details. The following refinement notes retain their implementation-time line references and verification scope.

### 1. Cause / reason

The five-section Marketplace page worked, but repeated comparisons, category summaries, inventory alerts and a separate seller ranking chart made it longer than necessary. Empty charts and repeated missing-history rows added little information. The operational section also needed an order-volume trend that remains useful when pending/unpaid orders exist and recognized revenue is zero.

No persisted duplicate seller records were confirmed. PostgreSQL enforces `product_one_account_owner`; do not assume a product can have two owners or merge accounts because their names match. The refined projections explicitly group by account source and ID, expose the username for disambiguation, and retain separate legitimate web/mobile accounts. No seller, order or audit record was merged or changed.

### 2. Exact files changed, current lines and nearby anchors

These are this follow-up's application changes, not all pre-existing dirty files in the workspace. Paths are relative to the project root; search the anchor if later edits move a line.

| File | Current line / anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/analytics.py` | 401 `seller_identity_annotations`; 415 `_seller_performance`; 602 `_market_basket`; 656 `build_marketplace_analytics` | Add optional source-qualified seller grouping/rank metadata and reuse existing detailed association counters. Defaults preserve legacy callers. |
| `backend/core/modules/reports/views.py` | 1387 `admin_marketplace_analytics_page` | Choose the internal `refined` option after the existing permission check and only for Super Admin. Other module dispatch remains unchanged. |
| `backend/core/modules/reports/superadmin_analytics.py` | 53 seller `search_url`; 92 `enrich_marketplace_sections`; 127 `order_volume`; 130 seller grouping; 167 `turnover_supported`; 173 `marketplace_variant_sales` | Reuse submission-demand aggregation, group seller fulfillment by effective source/ID, search sellers by recorded username, select supported turnover rows, and omit unrecorded variant groups from this analytical view. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 16 refinement CSS; 91 sections script | Load Marketplace-only styles and bump that script's cache version only in the Super Admin branch. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 1 `marketplace_sections=True`; 2 `marketplace-refined` | Preserve the five groups, pair wide Sales/Growth and equal operational cards, put category below sales, and replace repeated inventory/ranking panels with compact independent cards. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_refined_panels.html` | 1 growth; 8 inventory; 14 turnover; 19 sellers; 24 fulfillment; 30 association; 36 restock | New presentation partial for the compact panels. Seller ranking retains the previous six fields plus rank; fulfillment retains eight fields. Association analysis exposes genuine counters and metrics, without Dashboard bundle cards. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 1 KPIs; 8 sales; 49 category; 77 buyers | Keep four KPIs and all original data/actions. Move repeated sales comparison into Growth; shorten empty category copy; stop repeating category bars below Buyer Activity. Changes are conditional on the Marketplace section layout. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart.html` | 5 `marketplace_sections` empty branch | Give opted-in Marketplace charts one concise empty message and no empty drawing container. Other consumers keep their original branch. |
| `backend/static/components/css/admin_marketplace_refinement.css` | 1 scope; 19 seller stack; 27 responsive rules | Scope compact states, stock summary, readable scrollable seller cells, chart/table dimensions and responsive pairing to this page. Shared tab/layout CSS is unchanged. |
| `backend/static/components/js/admin_marketplace_sections.js` | 16 chart definitions; 18 order volume | Replace the separate seller bar chart with the submitted-order line. Keep payment/fulfillment donuts and exact counts; hide zero categories only from their visual legends, not tables or datasets. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 365 query count; 391 pending-only; 409 stable sellers; 438 association; 451 fixture export | Cover zero-sales order volume, distinct matching-name identities, existing Apriori math/counters and isolated browser fixtures. Exercise the actual refined path in the query-budget check. |
| `docs/superadmin-analytics-module.md` | 3 current refinement report | Record this change, data flow, measured verification, troubleshooting and practice steps. |
| `docs/web-ui-ux-guidelines.md` | Marketplace refinement paragraph under Scope and approach | Preserve the latest page choice and its explicit association-metric exception without changing ordinary Dashboard recommendation cards. |
| `CAMPUSHUB_CONTEXT.md` | 3 Marketplace refinement entry | Preserve the latest scope, layout and data constraints for future work. |

Review scripts, isolated fixture HTML/JSON, screenshots and result files are under `scratch/marketplace-refine-20261101/`. These helpers are verification material, not application modules or production data.

### 3. Changes made

- **Performance:** four existing KPIs; approximately 2:1 Sales Performance/Growth columns on large screens; category below. Growth owns the equivalent previous-period revenue/order comparison. Prior zero revenue remains an unavailable percentage baseline, never invented growth.
- **Orders:** the three existing performance KPIs; Order Volume Trend beside status; equal payment/fulfillment cards. Submission volume includes all recorded statuses, independently of recognized sales.
- **Products:** Top-Selling/Slow-Moving remain paired. Inventory Insights has four plain current-health values and one priority product/variant alert table. View Products / Inventory preserves access to the full records. Supported turnover rows retain their columns; unsupported coverage is explained once. Sales by Product Variant includes only recorded selections/options, or one empty message.
- **People:** Buyer Activity retains its actual counts and date series. Seller Performance becomes the sole sortable ranking table, retaining Products, Completed Orders, Units Sold, Sales and Low Stock. Distinct matching-name accounts remain separate. Seller Fulfillment remains its own card. The existing sorter activates when at least two data rows exist.
- **Insights:** keep Demand Forecast, Peak Sales Period and the original forecast-based restock calculation. Product Association Analytics replaces Frequently Bought Together and displays support, confidence, lift, eligible/multi-item transaction counts and exact directional pair counts when supported. Current stock alerts are linked rather than repeated in Restock. Dashboard Suggested Product Bundles is unchanged.

Cards use intrinsic heights, 16px content gaps and 24px section gaps. Actual sales charts use 240px on small screens, 280px from 600px and 300px for desktop Sales Performance; compact donuts use 200–220px. Missing sales do not reserve a chart area. Exact-value chart tables remain visible in bounded scrolling regions. Long seller names receive readable cells inside horizontal table scrolling. Flat tabs, date controls, Montserrat and navy/gold/white are retained.

### 4. How it works / functions, inputs, outputs and data flow

`admin_marketplace_analytics_page(request)` first performs existing module dispatch and permission checks. It passes a server-selected `refined=True` only for Super Admin into `build_marketplace_analytics(params, user=...)`. That builder still supplies the authoritative sales, buyers, products, slow movers, inventory, forecast and association data. The existing enrichment adds read-only comparisons and operational projections. Django renders the existing page and partials; JSON script elements feed the existing chart controller and Marketplace sections script. No browser calculation decides whether an order counts as sales.

| Function / projection | Inputs | Output / safeguard |
| --- | --- | --- |
| `seller_identity_annotations(include_names=False)` | Existing order → product owner foreign keys | Virtual SQL source/ID fields; optionally current name/username. No stored fields or identity migration. |
| `_seller_performance(..., stable_identities=True)` | Existing approved sellers, products, eligible sales and inventory | The same seller amounts/counts, grouped by effective account source/ID, plus rank and username. Equal names never imply equal accounts. Only the refined caller requests the additional metadata. |
| `enrich_marketplace_sections()` → `order_volume` | Existing authorized orders with `created_at` inside selected dates | Reuses `request_demand()` for observed date/week/month buckets, then labels its table Submitted orders. This adds one grouped query, not a query per order. Volume is separate from the Sales Performance grouping control and labels its automatic bucket unit. |
| Seller fulfillment | The same submitted-order queryset plus current effective owner identity | Per-identity submitted/completed/cancelled/pickup/delivery counts, completion rate and valid recorded timing; at most ten identities. Delivered alone still does not imply paid/completed. |
| `marketplace_variant_sales(..., recorded_only=True)` | Canonical eligible sales with recorded selections or historical option text | Up to ten actual selection combinations. Missing/malformed selections with no usable option are omitted from this view; a standard order does not become a made-up variant. Existing default behavior remains available to other callers. |
| `turnover_supported` / `turnover_unavailable` | Existing `marketplace_stock_turnover()` output | Presentation subsets and a coverage count; no change to ledger verification, time-weighted stock, physical unit movement, turnover or sell-through formulas. |
| `_market_basket(..., detailed=True)` | Actual eligible order item sets grouped by existing transaction identifier | Reuses `calculate_market_basket()` and its thresholds/math. Its existing detailed option supplies actual together/source/target counts and more precise percentages. Counts are never reverse-calculated from rounded support. |
| Chart scripts | Django-generated JSON and server-rendered empty-state decisions | Draw the selected real series, preserve exact-value tables, and show an honest library-unavailable fallback. Sorting only reorders already-authorized displayed table rows. |

For example, three pending unpaid orders submitted in the selected dates produce a volume total of `3` and recognized sales of `0.00`. The operational chart remains present while the empty sales drawing area is absent. This is covered by `test_marketplace_refinement_keeps_pending_volume_with_zero_recognized_sales`; it is an isolated test case, not production activity.

### 5. Backend / API behavior

Existing URLs, permissions, navigation, filter parameters and actions remain authoritative. The optional `refined` argument is selected by the authorized server view, not a new client permission or API. Presets/custom dates still update relevant selected-period metrics; sales keep the existing completed-paid positive-quantity eligibility and recognition timestamp. Operational metrics use submission dates. Previous comparison uses the immediately preceding equal-length period. Inventory/product counts are explicitly current snapshots. Seller links use the existing username-capable search, not a fabricated detail identifier. No new endpoint or marketplace workflow was introduced.

### 6. Database / migration impact

No model, migration, stored calculation, PostgreSQL record, audit-writing path or business workflow changed. The new owner annotations and coverage subsets are read-only. Automated fixtures are created only inside Django's disposable PostgreSQL test database. Verification of the actual local database runs inside `SET TRANSACTION READ ONLY` and confirms unchanged record counts. No environment edits, server restart, deployment or image generation was performed.

### 7. Tests performed and results

- **120/120 Django tests passed across two focused runs:** 54 for `modules.reports.test_superadmin_analytics` and `modules.reports.tests.MarketplaceAnalyticsTests` (27.359 seconds), plus 66 for `modules.reports.test_dashboard_marketplace` and `modules.reports.test_marketplace_admin_dashboard` (34.556 seconds). These cover role/date behavior, the affected calculations and preserved shared-builder consumers. Django system checks reported no issues.
- **1,027/1,027 Chromium checks passed across 32 fixture navigations**, using eight widths from 280px to 1920px, populated/empty/pending-only/no-recorded-variant states, date/grouping/horizon actions, seller sorting, exact datasets, 16px paired gaps, 24px section gaps, accessible chart labels, contained horizontal tables, no page overflow, no-JS and missing-Chart.js behavior. Real desktop/phone screenshots were inspected, including the corrected seller cells. These are Django-rendered isolated fixtures, not an authenticated live-browser deployment test.
- **Actual local PostgreSQL:** all four existing Analytics views returned HTTP 200 in a read-only transaction. Marketplace revenue/order counts match the canonical eligible-sales query; operational volume and payment/fulfillment totals match submitted records; seller keys are unique and stock-health subtotals reconcile. No writes; record counts unchanged. Marketplace rendered in 38 queries on that local dataset.
- **Query scaling:** the refined builder/enrichment used 33 queries with both 1 and 51 orders in the regression fixture. This verifies absence of per-order query growth, not an unlimited production performance guarantee.
- **Scope:** 54 pre-edit fingerprints match, including protected Dashboard files, shared Analytics layout/controller, other-tab templates and the unchanged domain-helper tail.
- **Static checks:** Node syntax check, four Python AST parses and scoped tracked-file `git diff --check` passed.

Run the affected backend suite from the project root with:

```powershell
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_dashboard_marketplace modules.reports.test_marketplace_admin_dashboard
```

Browser evidence: `scratch/marketplace-refine-20261101/browser-result.json`; local integration: `local-result.json`; scope: `scope-result.json`; query scaling: `fixtures/query-count.json`. The optional fixture-export variable is `MARKETPLACE_REFINEMENT_REVIEW_DIR`; exports never feed a production page.

### 8. Remaining limitations / debugging and troubleshooting

- **No sales but orders exist:** expected for pending/unpaid/noneligible orders. Check submission dates versus recognition dates before treating the difference as a defect. Do not widen the recognized-sales eligibility to fill charts.
- **Matching seller names:** inspect source-qualified key/username. Matching names may represent distinct legitimate accounts. The database owner constraint remains enforced; do not bypass it to simulate an assumed duplicate cause.
- **No associations:** current order codes are unique per sellable-product order, so they cannot establish real multi-product checkout pairs. The card reports actual eligible/multi-item counts and insufficient shared-checkout data. It never groups by buyer/date, imports research transactions or generates Dashboard bundle recommendations. A separate deterministic unit test checks the existing algorithm and sufficient-data table branch; no shared transaction was invented in the actual database.
- **Unavailable turnover:** a current stock number cannot replace an opening balance or continuous physical ledger. Missing, gapped or ambiguous history stays unavailable, with one coverage explanation. This remains unit turnover, not financial cost-of-goods turnover.
- **Missing variant rows:** inspect historical customization/option fields. Current catalog options are not evidence that a past order selected a variant.
- **Charts or stale layout:** confirm the Marketplace-only CSS/script cache version, inspect JSON script IDs and check the browser console. With Chart.js absent, exact tables remain available. Full seller columns are intentionally accessible by horizontal scrolling.
- **Verification boundary:** no production deployment or authenticated live-browser session was performed. The actual local Django/PostgreSQL checks and isolated responsive browser checks are reported separately.

### Safe learning exercise

1. Open Marketplace Analytics with an authorized read-only Super Admin account; record the current date range, revenue and submitted-order total.
2. Choose a narrower custom range without changing any order or stock record. Confirm the comparison moves to the equally sized preceding period and the order-volume total reconciles with submissions for those dates.
3. Compare Inventory Insights before/after. Its current stock snapshot should remain current even though historical sales change.
4. If the seller table has two or more rows, sort Sales Rank twice and scroll right to Sales/Low Stock. Confirm only row order changes, names stay readable and matching-name accounts retain distinct usernames/actions.
5. Restore Last 30 Days. Verify the original selected-period values return. For a code practice change, shorten only an empty-state sentence in `marketplace_refined_panels.html`, run the backend command above and check a narrow screen; revert the sentence afterward. Do not insert activity or change eligibility to make an empty chart look populated.

## Previous: Complete four-tab Analytics improvement — November 1, 2026

The following notes describe the preceding implementation and its line references at that step. The current Marketplace report above supersedes its Marketplace sizing, inventory, ranking and association presentation details; other-tab behavior remains as recorded below.

### 1. Cause / reason

The Marketplace page mixed its working analytics without the requested five-part hierarchy. The other tabs already had real booking, service and account data, but lacked the same visual structure and several supported operational insights. The shared tab navigation used boxed pills with a small active marker. Inspection also found that stock history, workflow timestamps and audit identities have different coverage; using a current stock value, `updated_at` or an enabled-account count as historical evidence would produce misleading metrics.

This continues the existing Django Analytics module. The Super Admin Dashboard, marketplace workflows, database models, forecasting algorithm and Apriori calculations are unchanged. Super Admin pages opt into one scoped stylesheet and additional read-only projections; other administrative roles keep their existing presentation and permission checks.

### 2. Exact files changed, current lines and nearby anchors

All paths below are relative to the project root. Use the named anchor if a subsequent edit moves a line.

| File | Current line / anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/modules/reports/superadmin_analytics.py` | 88 `enrich_marketplace_sections`; 92 definition | Extend the existing authorized Marketplace projection with operational metrics, payment/fulfillment distributions, seller fulfillment and inventory views. |
| Same file | 167 `marketplace_variant_sales` | Aggregate recorded selection combinations, counting each order's units/revenue once. |
| Same file | 187 `marketplace_stock_turnover` | Read up to ten current physical stock pools with verified opening balances and continuous on-hand history; calculate unit turnover and sell-through only when supported. |
| Same file | 242 `request_timing`; 267 `request_demand` | Reusable recorded-workflow timing and selected-submission-date demand projections. |
| Same file | 285 `enrich_facilities`; 298 `enrich_services`; 315 `enrich_users` | Add approval/request performance, service demand/timing, verification, account growth and observed engagement without creating new endpoints. |
| `backend/core/modules/reports/analytics_sections.py` | 288 `enrich_facilities`; 379 `enrich_services`; 395 `mobile_counts` | Call the new projections only for Super Admin. Batch the existing Users count definitions in two aggregate queries to retain the query budget. The `enrich_users` call follows the Users result dictionary. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 15 scoped stylesheet; 34 `marketplace_analytics_sections.html`; 89 scripts | Select the new five-section Super Admin layout while retaining the existing other-role layout. |
| `backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html` | 18 stylesheet; 32 `analytics_domain_sections.html`; 80 script | Select the organized Facilities layout and preserve the legacy-role branch. |
| `backend/core/modules/reports/templates/reports/pages/admin_services_analytics.html` | 14 stylesheet; 29 domain include; 51 script | Select the organized Services layout and load Chart.js only for the new Super Admin charts. |
| `backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html` | 15 stylesheet; 29 domain include; 58 script | Select the organized Users layout without changing its original role branch. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_cards.html` | 1 `card` selection | Extract and reuse twelve existing KPI/chart/table blocks. Initial working columns, actions, forecast controls and data hooks remain. |
| `backend/core/modules/reports/templates/reports/partials/marketplace_analytics_sections.html` | 1 `marketplace_sections=True` | Five outside section headings and independent content cards; includes the added operational/inventory/seller views and the renamed insights heading. |
| `backend/core/modules/reports/templates/reports/partials/analytics_domain_cards.html` | 1 `facility_kpis`; 161 `services_kpis`; 328 `users_kpis` | Reuse fifteen original card blocks across the new Super Admin and retained legacy layouts. New layouts use subordinate card headings. |
| `backend/core/modules/reports/templates/reports/partials/analytics_domain_sections.html` | 1 `analytics_flat=True` | Four Facilities sections, three Services sections and three Users sections with independent cards and preserved links. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart.html` | 3 chart description | Describe always-visible exact-value tables for the opted-in layouts. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart_data.html` | 1 conditional wrapper | Use a plain data-table container for new Analytics layouts; other consumers retain their original disclosure control. |
| `backend/core/modules/reports/templates/reports/partials/analytics_dates.html` | 18 forecast fields | Preserve the selected Marketplace forecast product/horizon across global date changes. Other modules do not receive those fields. |
| `backend/static/components/css/admin_super_analytics_layout.css` | 1 scope; 14 layout; 60 tab styles; 98 narrow header | Shared Montserrat/navy/gold/white styling, 16px card gaps, 24px section gaps, independent surfaces, readable charts/tables and unboxed inline tabs with a 3px gold underline. |
| `backend/static/components/js/admin_marketplace_sections.js` | 1 DOMContentLoaded | New payment/fulfillment donuts and seller revenue bar chart, with a genuine missing-library fallback. |
| `backend/static/components/js/admin_marketplace_analytics.js` | 57 font selection | Use Montserrat only for the opted-in Marketplace layout. Existing series, grouping and forecast rendering remain authoritative. |
| `backend/static/components/js/admin_analytics.js` | 44 font selection | Apply Montserrat to Super Admin Facilities/Users charts while preserving other-role fonts and existing chart data. |
| `backend/static/components/js/admin_super_analytics.js` | 13 `revealActiveTab`; 57 domain charts | Keep the active tab visible after font loading/resizing; retain sorting; initialize actual demand/account charts and missing-library states. Re-measure charts when the bundled font loads, and wrap long service-axis labels. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 281–460 named Marketplace/domain regression tests and fixture exports | Test calculations, coverage, read-only behavior, date semantics, stable query counts and isolated browser exports. Existing role/date/forecast/basket tests remain. |
| `docs/superadmin-analytics-module.md`, `docs/web-ui-ux-guidelines.md`, `CAMPUSHUB_CONTEXT.md` | Current November 1 entries | Record the implementation, current choices, measured checks, troubleshooting and learning exercise. |

Verification helpers and captured evidence are in `scratch/marketplace-sections-20261101/` and `scratch/analytics-complete-20261101/`. Their template-preparation scripts are development history, not application commands; do not rerun them over later manual edits. The temporary Marketplace-only stylesheet was consolidated into the single shared `admin_super_analytics_layout.css`; no runtime template references the temporary path.

### 3. Changes made

The Analytics title, breadcrumb, sidebar and existing four destinations remain. Tabs are horizontal text links with muted inactive text, a navy semibold active label, a full 3px gold underline and a thin divider. There is no pill background or boxed nav surround. The date filter stays on the right on desktop and wraps to its own right-aligned row when needed. The active link scrolls into view within the narrow navigation strip, without scrolling the page vertically.

All four tabs use bundled Montserrat, navy `#1A1851`, gold `#FCB316`, white cards, 16px card/content gaps and 24px section spacing. Group headings sit outside unbordered section wrappers. Chart drawing areas are 280px on phones, 320px on larger screens and 380px for large desktop charts; donuts/rankings have their own readable dimensions. Cards grow with real content. Existing long business tables retain every column through contained native horizontal scrolling. Exact-value chart tables stay visible, wrap their headings and retain chronological order. Other-role layouts and dashboard consumers do not opt into these changes.

Marketplace is organized into:

1. **Marketplace Performance:** the original revenue/completed-order/active-seller/approved-product KPIs, Sales Performance, Sales by Category and the existing equivalent previous-period comparison in Sales Growth.
2. **Orders & Payments Analytics:** original order-status distribution, completion/cancellation rates, payment status, recorded Pickup/Seller Delivery/unclassified choices, and average submission-to-recorded-completion time with coverage.
3. **Product & Inventory Analytics:** original top products, slow movers and inventory columns, current product/variant alerts, coverage-aware unit turnover/sell-through, plus recorded variant-combination sales. Existing product actions remain.
4. **Buyers & Sellers Analytics:** original buyer/new/repeat/average-order measures and seller table, the same seller revenue ranking visualized, and current seller-identity fulfillment outcomes for submitted orders.
5. **Marketplace Insights & Recommendations:** the original demand forecast, actual-transaction association calculation and peak period, plus observed stock reviews and the selected product's existing forecast-based preparation suggestion. Synthetic research transactions are explicitly excluded from operational metrics.

Facilities retains booking/stay-date KPIs, approved-booking charts, monthly submission trend, most-booked facility, verified capacity table, operational status, existing paid-revenue chart, keyboard behavior and report links. New sections add all-outcome submission demand, a clearly defined reviewed approval rate, recorded approval delay and pending submission counts. Availability remains a current catalog snapshot, never a promise that every slot is free.

Services retains its registered-service table, complete status breakdown, destinations and institutional procedure. Actual requests now support a dated trend, service distribution, local weekday pattern, completion rate, recorded processing/approval delays and an oldest-pending shortlist. A Completed status does not imply laboratory results release or payment.

Users retains registration charts, recorded types (including Unclassified), current enabled-account counts, seller privilege statistics and governance links. New cards show current email verification, comparable-period registration growth, successful sign-in event/account counts and distinct recorded mobile request submitters. These are observed records, not inferred monthly active users or deduplicated people.

### 4. How it works / functions, inputs, outputs and data flow

The existing routes and authorization remain the entry points. Marketplace still calls `build_marketplace_analytics()` and then the Super Admin `enrich_marketplace()` hook. Facilities/Services/Users still use the existing builders in `analytics_sections.py`; only their Super Admin branches call the new enrichment helpers. Django renders the same model-backed context through reusable card partials, JSON script elements and the existing chart controllers, plus the scoped additional charts. No second analytics API or duplicated model was introduced.

| Calculation / function | Inputs and date basis | Output and safeguards |
| --- | --- | --- |
| Existing canonical sales / comparison | Completed, paid, positive-quantity orders; existing `analytics_at = completed_at`, otherwise paid time, otherwise created time | Same eligible revenue/order series and previous equal-length period. Unpaid/delivered/open/cancelled orders never become recognized sales through the new helpers. No invented percent growth when prior revenue is zero. |
| `enrich_marketplace_sections()` | Existing scoped orders submitted in selected dates | Current completion/cancellation percentages; paid/unpaid/other counts; Pickup/Delivery/unclassified counts; exact recorded completion durations. Empty denominator/duration coverage produces unavailable values. |
| `marketplace_variant_sales()` | Eligible sales and recorded selections/option text | Up to ten selection combinations; a multiple-option order contributes its revenue once, not once per selected option. No current catalog option is substituted for missing historical data. |
| `marketplace_stock_turnover()` | Up to ten current physical SKUs, an observed pre-period on-hand baseline, and continuous physical changes through the observed end time | Time-weighted average on hand; eligible recorded physical units / average on hand; sell-through = those units / (verified opening on hand + recorded positive additions). Bundle-derived availability, reservation-only balances, missing baselines, ambiguous available-only physical changes and broken continuity do not become invented inventory history. This is unit analysis, not cost-based financial turnover. |
| `request_timing()` | Existing `FacilityBookingRequest.details.approval.at` / `.completion.at`, request creation and current status | Mean recorded hours plus count of timed records. Naive/invalid/future/pre-submission stamps and missing history are excluded; completion timing requires current Completed status. `Booking.updated_at` is never treated as completion. |
| `request_demand()` | Actual selected-period submissions, excluding schedule blocks in caller query | One grouped date query plus date/week/month buckets and local weekday totals. Weekly/monthly buckets aggregate only selected dates. These are observations, not forecasts. |
| `enrich_facilities()` | Physical request submissions | Accepted = current Approved/Completed; reviewed = accepted + Rejected. Pending/Cancelled are outside that approval denominator. Booking-date KPIs keep their original separate meaning. |
| `enrich_services()` | Existing service-only submission queryset and existing status totals | Completion rate, verified timing, demand charts, distribution and up to five pending actual request links. |
| `enrich_users()` | Current account verification flags, current/previous registration dates, successful sign-in audits and real request user IDs | Snapshot verification; comparable growth; valid source-qualified sign-in identities and events; distinct non-null mobile request submitters. Web/mobile identities remain distinct, even if their numeric IDs match. Unknown/failed sign-ins are excluded. |

Small annotated example:

```python
# Operational outcome: all submitted orders in the selected cohort.
completion_rate = completed_count / submitted_count * 100 if submitted_count else None
# Recognized revenue still comes from the original eligible completed-paid query.
# A delivered but unpaid order can affect fulfillment counts without adding revenue.
```

The response keeps formatted display values and chart/table dictionaries separate. Charts read only the supplied JSON; they never generate sample records. Existing sorting remains local to bounded business tables and leaves chronological chart tables untouched. Global dates reload the existing GET route; tab links preserve the chosen period. Sales grouping and forecast controls retain their existing form behavior, with the selected forecast settings preserved during global date changes.

### 5. Backend / API behavior

Existing Django permission checks, module routes, navigation and model ownership/scope rules remain. The new helpers are read-only additions to the existing Super Admin context, not workflow actions. No new write endpoint or automatic recommendation generation was added. Non-Super Admin Marketplace/Facilities rendered HTML was compared with pre-change templates and matched after whitespace normalization.

Forecasting retains the existing moving-average calculation and sufficiency thresholds. Apriori/association support, confidence and lift calculations remain in their existing helpers and tests. The page continues to require actual shared checkout evidence; it does not infer baskets from matching buyer/date, unique per-product references or bundle components, and does not fall back to synthetic data. Existing protected research/synthetic workflows elsewhere are unchanged.

### 6. Database / migration impact

No models, schema migrations, production/demo records, database configuration, environment settings, background jobs or deployment changed. Application GET paths issue no inserts/updates/deletes. PostgreSQL tests used disposable local test databases, which were destroyed afterward. Browser responses came from explicitly isolated ORM fixtures; all non-GET browser requests were blocked.

Separately, all four actual local PostgreSQL-backed views were rendered inside `SET TRANSACTION READ ONLY`. All returned HTTP 200, and counts of orders, products, SKU/movement records, bookings, facilities, payments, web/mobile accounts and account audits remained unchanged. This is source/view integration verification, not a claim that a production site was deployed or tested through a live authenticated browser session.

### 7. Tests performed and measured results

- **50/50 Django tests passed in 31.610 seconds** using `backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py modules.reports.test_superadmin_analytics modules.reports.tests.MarketplaceAnalyticsTests`. Django system checks reported no issues. Tests cover all four role gates, date boundaries, eligible paid revenue, existing forecasting/association math, new operational metrics, recorded variant aggregation, continuous/gapped/ambiguous stock history, sell-through, timing coverage, verification/growth/engagement and read-only GET behavior.
- **1/1 additional shared-role fixture comparison passed in 1.558 seconds**, explicitly loading the saved pre-change Marketplace and Facilities templates. This verifies the final shared partials preserve their non-Super Admin rendered HTML.
- **1,834/1,834 Chromium checks passed across 88 fixture navigations**, covering four modules, populated/empty states, widths 280/320/390/768/1024/1280/1440/1920px, preset/custom filtering, tab switching with retained dates, exact KPI/chart values, unique IDs, outside headings, inline-tab geometry/colors/3px underline, visible active narrow tabs, right-aligned filters, 24px section spacing, original table columns, wrapping chart-data headers, missing-chart-library/no-JavaScript states, no page overflow, no missing assets, no browser errors and no writes.
- After the final service-axis label wrapping adjustment, **430/430 focused Services Chromium checks passed across 22 additional navigations**. Final desktop/phone headers and content for all four tabs were visually inspected, including the narrow Services chart/data table.
- Query stability: the complete Marketplace projection used **32 queries for both 1 and 51 orders** in its isolated regression fixture. The original Users query-budget test initially caught added count queries; batching the existing definitions brought that builder within its established limit of **18 queries**. No query-budget assertion was relaxed.
- Actual local PostgreSQL read-only renders returned **200 for all four tabs**; measured view query counts were Marketplace **37**, Facilities **51**, Services **12**, Users **19**, including view/permission/notification context. These are different from projection-only test counts. Evidence: `scratch/analytics-complete-20261101/local-result.json`.
- JavaScript syntax and scoped whitespace checks passed. Generic design-kit gates, full WCAG conformance and other browsers/physical devices were not certified.

Main evidence: `scratch/analytics-complete-20261101/browser-result.json`, `browser-services-result.json`, `local-result.json`, the two verification scripts and actual rendered PNGs. The earlier Marketplace-specific tests/fixtures remain under `scratch/marketplace-sections-20261101/`, including `fixtures/query-count.json`. Fixture records are test-only PostgreSQL rows, never inserted into the working application database.

### 8. Remaining limitations / troubleshooting / safe practice

- Historical stock turnover/sell-through requires verified opening and continuous physical history. Missing history remains unavailable; current available stock alone is not a historical denominator. Only ten current stock pools are previewed, and no unrecorded unit cost is invented.
- Processing times depend on dedicated saved workflow timestamps; legacy Completed/Approved records without those timestamps cannot establish elapsed time. Coverage counts explain this rather than treating missing timestamps as zero-hour processing.
- Enabled-account status differs from observed engagement. Successful sign-ins and request submissions cover only recorded events/identities, not every visit, every session or unique person. Verification/catalog/status metrics are current snapshots rather than reconstructed historical states.
- The current per-product unique order references do not establish shared checkout baskets. An insufficient actual-transaction association state is expected until real basket evidence exists. Synthetic research data stays separate.
- Dense business tables retain native horizontal access on narrow screens. Chart tables have visible, bounded scroll regions for long date series; no columns are removed. Card heights follow actual content rather than forcing empty neighboring cards to match a long table.

Troubleshooting: reload the page and verify the shared stylesheet and Super Analytics script use `20261101-analytics-complete`. If an old boxed nav remains, inspect the opted-in `body.super-admin-analytics` and the scoped `.analytics-toolbar` rules. If data seems stale, check the selected GET period/module and distinguish submission, recognition and booking/stay dates. If timing/turnover is unavailable, inspect the recorded timestamp/baseline coverage; do not edit history to fill a metric. If charts cannot load, their real tables/summaries remain. Missing active tabs on small screens should be checked after bundled-font loading and within the horizontally scrollable nav, without hiding overflow at page level.

Safe practice exercise: open Analytics, select a custom two-day period, and switch through all four tabs. Verify the dates persist. Compare one Marketplace total with eligible paid orders; one Facilities submission count with its separately labeled booking-date KPI; one service completion duration with its saved workflow timestamp; and Users registration growth with the immediately preceding two days. Inspect a missing-history state, resize to phone width, and use existing table scrolling/sorting and management/report links. Do not approve, pay, change stock, generate recommendations or edit accounts. Reload to leave any temporary DevTools styling behind.

## Current approved Super Admin Analytics improvements — October 26, 2026

This section supersedes earlier Super Admin Analytics captions, date-window, assumed utilization and unknown-account fallback guidance. It does not change the executive dashboard or other administrator interfaces.

### 1. Cause / reason

The four-tab Analytics architecture already existed. Confirmed problems were inconsistent preset resolution when stale custom inputs were submitted, Facilities/Users trends extending beyond the selected range, unknown mobile types being added to Students, an eight-hours-per-day utilization assumption, unconditional empty charts/status rows, missing accessible chart tables and obsolete Cash-on-Pickup-only wording. Revenue already used Completed AND Paid; changing its business rules was neither needed nor authorized.

Browser verification also confirmed a 320px Sales Performance header overflow and an unbounded retained Facility Status donut. The final styles constrain these within Super Admin Analytics only. Shared-role output remains on its existing branches.

### 2. Exact modified files / current lines and code anchors

| Exact file | Current anchor | Change |
|---|---|---|
| `backend/core/modules/reports/views.py` | 1345 `is_super_analytics` / `enrich_marketplace` | Opt into enrichment only after existing Marketplace Analytics permission checks. |
| `backend/core/modules/reports/analytics_sections.py` | 49 `analytics_period`; 105 Facilities; 220 monthly aggregation; 376 Users; 414 monthly aggregation; 458 Web Accounts; 490 review-date aggregate; 515/550 renderers | Super-only preset precedence, bounded trends, verified capacity projection, honest classification and dated/snapshot context. |
| `backend/core/modules/reports/superadmin_analytics.py` (new) | 15 `is_super_analytics`; 21 `chart_table`; 25 `enrich_marketplace`; 90 `facility_capacity_rows` | Small read-only presentation projection around existing services; comparisons, authorized links, table alternatives and batched configured-capacity reuse. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | `super_analytics` branches, KPI grid, Sales Performance, category/buyer/inventory/DSS blocks | Accurate labels, comparisons, empty/populated states, existing links and accessible data without removing sections. |
| `backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html` | `super-admin-analytics` body; chart includes; Facility Utilization table | Preserve booking/status/ranking/revenue features; show verified hours/slots/nights/units and unavailable capacity rather than assumptions. |
| `backend/core/modules/reports/templates/reports/pages/admin_services_analytics.html` | Registered Services and Completed Requests subtitles | Distinguish current catalog from submission-period requests; never infer receipt/payment/results release from Completed alone. |
| `backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html` | KPI subtitles, User Distribution, seller-statistic notes | Current account status, honest Unclassified/Web Accounts, real submission/review-date counts and actual application-share bars. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart.html` (new) | 1 `has_data` | Reuse existing chart IDs/renderers with accessible labels and data alternatives, or a compact honest empty state. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart_data.html` (new) | 1 native `details` | Collapsed, captioned, horizontally scrollable data table with row/column scopes. |
| `backend/templates/dashboard/partials/facility_revenue.html` | 13 `data-revenue-table` | Add the alternative only when opted into Super Admin Analytics; other dashboard markup is unchanged. |
| `backend/static/components/js/admin_marketplace_analytics.js` | 5 role flag; 21 peso formatting; 160 scoped axis options | Super-only navy/gold presentation, Philippine formatting and readable adaptive axes; calculations and datasets unchanged. |
| `backend/static/components/js/admin_analytics.js` | 5 `GOLD` | Correct web gold only for the opted-in Super Admin body; retain other roles' existing rendering. |
| `backend/static/components/js/admin_super_analytics.js` (new) | 1 DOMContentLoaded | Disable irrelevant custom inputs and add keyboard-operable local sorting to bounded existing tables; chart tables retain chronological order. |
| `backend/static/components/js/admin_facility_revenue.js` | 4 role flag; 51 scoped validated-data branch | Preserve existing validation/refresh/keyboard/report link behavior; hide/destroy empty Super Analytics revenue chart and refresh its accessible table from the validated series. |
| `backend/static/components/css/admin_analytics.css` | 1104 `.super-admin-analytics` block | Scoped intrinsic cards, compact empty states, navy/gold links/badges, wrapped headers, 180px status donut, bounded table scrolling and focus indicators. No global redesign. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 286 onward approved regression cases; optional browser fixture export | Extend existing tests for boundaries, comparisons, scopes, unknown types, capacity, bundles, revenue reconciliation and shared-role identity. |
| `docs/superadmin-analytics-module.md` | This report | Causes, exact files, functions/data flow, test evidence, limits and safe exercise. |
| `CAMPUSHUB_CONTEXT.md` | Latest entry | Persist finalized role-specific behavior and verification references. |

The two new template partials and new Super-specific script/projection keep repeated chart markup and shared-role effects contained. The retained facility-revenue partial/script required a guarded change after browser inspection verified its empty-chart problem. These are presentation/read-only projection changes, not new features or database entities. The inspected `analytics_dates.html` needed no edit: Super-only server precedence and disabled irrelevant inputs resolve its problem. Existing dirty working-tree changes were preserved.

### 3. Fixes and improvements completed

- All four existing tabs and Reports → Analytics / Generate Reports navigation remain. Presets win over stale custom inputs for Super Admin; intentional custom ranges, Philippine timezone and existing maximum-range handling remain. Tab links retain the selected period.
- Facilities/Users trends query only selected dates and bucket them chronologically. Monthly aggregates use one grouped booking query or two grouped account queries rather than one query per month. The Facilities trend explicitly measures currently approved/completed reservations **submitted** in the selected period; its booking/stay-date KPIs retain their different, clearly labelled date basis.
- Unknown mobile account types remain **Unclassified**. Django web-account rows are labelled **Web Accounts (recorded roles)** rather than inferring a mobile account type from access roles. These are account records, not deduplicated people. Seller remains an independent privilege. Active Users describes enabled accounts, not recent use; inactive/disabled count is the complement of the existing enabled-account calculation.
- Per-facility utilization reuses verified operating-schedule/slot/room-night/unit calculators. Booking intervals are clipped to configured openings, overlapping usage is unioned, stays use checkout-exclusive nights within the selected period and unavailable configuration stays unavailable. Current configuration cannot reconstruct historical configuration changes. No eight-hour denominator is inferred.
- Sales Performance keeps Daily/Weekly/Monthly and its existing revenue/order datasets. Equivalent previous-period revenue/order comparisons are added to the existing surface. A zero baseline never creates a growth percentage. Active Sellers and Repeat Buyers keep their original definitions. Approved Products and stock are clearly current snapshots.
- Empty sales, booking/registration trends and zero-order status sections show compact messages. Qualifying zero-price orders keep the sales chart/table; all-zero category revenue is shown in the table rather than an empty donut. No positive revenue means no invented peak period.
- Existing charts gain labelled canvases and native collapsed chart-data alternatives. Valid zero dates remain. Existing facility revenue keeps its paid-transaction source, keyboard interaction, refresh validation and report link, with a read-only table; empty periods have neither a visible/instantiated revenue chart nor an exposed all-zero table.
- Order-status links use existing authorized Orders filters and **creation dates**, matching that metric. Product rankings link to surviving authorized product records. Inventory links reuse existing search; seller names link to the existing seller-application search rather than claiming an invented unique identity. Existing ranking order remains the default. Local keyboard sorting affects only bounded existing non-chart tables and makes no additional data requests.
- Inventory explanations distinguish available quantities from component-derived bundle availability. No physical-plus-derived stock sum is introduced. Days remaining/daily averages are labelled observed-rate estimates, not reliable forecasts from sparse history. Existing algorithm thresholds and insufficient-data messages remain.
- Services retain real request statuses and submission-date cohorts. Completed does not imply cash collection or results release. Current seller application status is distinguished from dated application submissions and recorded approved/rejected reviews; no historical decisions are reconstructed.

### 4. How it works — inputs, outputs, functions and data flow

Existing permission-checked views → unchanged module services → optional Super Admin enrichment → existing role-specific templates/Chart.js renderers. `is_super_analytics(user)` chooses presentation for an authenticated, active Super Admin identity; it grants no permissions and is used only after the existing view checks. Other roles keep the previous presentation. Shared Marketplace Admin and Facilities Admin HTML was rendered against the exact pre-change templates and compared after whitespace normalization.

`enrich_marketplace(analytics, user)` receives an already authorized dictionary from `build_marketplace_analytics`. It preserves its metrics/forecast/Apriori output, computes a previous-period aggregate from the same `valid_sales_queryset(user)`, adds links only where existing permissions allow them, and creates read-only table rows. The existing service still requires Completed AND Paid, positive quantity, original scope and canonical recognition timestamp (completed time, then paid time, then creation time). **No revenue eligibility or recognition rule changed.** Category/product/seller calculations remain the existing ones.

For selected start S, end E and inclusive duration D, comparison dates are S−D through S−1. `comparison_metric` is reused: current 80 / previous 40 gives **100%**; current 80 / previous 0 gives **New activity**, with no percentage; both zero gives **No change**. Comparisons use the same recognition semantics and authorized scope as current revenue.

`facility_capacity_rows(period, facilities)` performs two batched reads (bookings and rooms) and delegates to the existing `_hours_or_slots` / `_rooms_or_units` functions from `dashboard_utilization.py`. It does not copy their business formulas or modify them. Inputs are the selected dates and actual facility configuration; outputs are verified usage/capacity/unit/percentage or an explanatory unavailable state. Example verified by tests: a 07:00–11:00 booking clipped to configured 08:00–18:00 contributes three hours; across two ten-hour days this is **3/20 = 15%**. A stay from September 29 to October 2 in an October 1–2 window occupies one checkout-exclusive night, giving **1/2 = 50%** for one configured room.

`chart_table(headers, rows)` is a data adapter only. `analytics_chart.html` receives the existing chart ID, label, actual table rows and a verified has-data flag. It retains the original renderer when meaningful data exists; otherwise it produces a compact empty message. `analytics_chart_data.html` provides native keyboard disclosure, caption and scoped headers. Forecast history gaps remain em dashes, not invented values. The new script sorts existing rendered rows locally, with stable ties and `aria-sort`; it does not load additional records or alter rankings in the backend.

### 5. Backend / API / permission behavior

Existing routes, sidebar items, four tabs, view permission checks, Program/Major scope and report authorization remain. Analytics is still read-only monitoring; Generate Reports owns export creation. The Sales Report still reuses the same completed-paid queryset and recognition dates; isolated reconciliation tests compare its rows with Analytics. No new API or duplicate Analytics page exists.

Super enrichment is additive; the source Marketplace Admin and Facilities Admin presentation is preserved. Existing direct-access permission tests remain, and newly exposed drilldowns intersect the destination's existing authorization. No individual buyer identities are exposed. Active Sellers still means approved eligible sellers with listing submission/update activity or qualifying sales in the period. Repeat Buyers still means identified buyers with more than one qualifying order within the period; New Buyers may overlap. Buyer charts count all qualifying purchases, including records without an identifiable buyer, and state this explicitly.

The existing forecasting algorithm, thresholds, Apriori calculation, saved recommendation workflow, synthetic/live separation, order/payment/fulfillment/FIFO and cancellation behavior were not modified. The original analytics service, reporting builder, configured-capacity service and protected marketplace workflow files retain their pre-change fingerprints.

### 6. Database / migration impact

No model, migration, schema, environment, inventory activation, stock writer or working record was changed. All new test orders/users/bookings/payments exist only in Django's disposable PostgreSQL test database. Before/after fingerprints of **13 protected marketplace/inventory/audit tables match**. Working projections for all four modules were checked inside a PostgreSQL `SET TRANSACTION READ ONLY` transaction; no operational refresh/mining persistence was triggered.

The actual working seven-day projection was empty revenue/orders, zero new registrations and zero requests; Users trend matched its zero registration count, and one mobile account remained honestly Unclassified. A configured facility capacity row was verifiable. These are verification observations, not hardcoded UI values or created historical records.

### 7. Tests performed — actual results

- **253 broader regression tests passed in 74.434s** across Super Admin Analytics, facility revenue/utilization, sales/report reconciliation, marketplace/executive dashboards, reports, bundle monitoring, bundles, FIFO inventory and FIFO concurrency. All prior tests were retained and extended.
- **21 final focused Analytics tests passed in 3.898s** after the final Web Accounts label refinement. Covers four-tab preset/custom parsing, stale input precedence, Philippine midnight boundaries, equivalent comparison windows, zero baselines, genuine zero-price sales, report reconciliation, filtered status drilldowns, month clipping, unknown types, bundle-derived availability, unchanged algorithms and role isolation. The normalized shared-role HTML comparisons passed.
- Capacity tests assert **two batched queries** independent of the number of supplied facilities. Users tests bound the projection to **at most 18 queries**, with month aggregation independent of the number of displayed buckets. No speculative whole-application performance score is claimed.
- **1,354 browser assertions passed across 62 renders**, with no page overflow, missing assets, JavaScript errors, mutation requests or working-database requests. Final screenshots and machine-readable results are recorded in `scratch/super-analytics-20261026/browser-results.json`. Verification covers empty/populated states across all four tabs at **1920, 1440, 1280, 1024, 768, 390 and 320px**, valid zero-price and weekly/monthly states, shared-role isolation, canvas labels, actual chart values/axes/peso tooltips, authorized link parameters, collapsed/expanded captioned tables, Enter/Space/focus, sorting/aria-sort, custom controls, no page overflow and bounded status-donut height. Requests are intercepted into isolated record-backed HTML/static assets; no browser request reaches the working database or mutates records.
- Django system check passed. Changed Python/JS syntax, all changed/new template compilation and added-line whitespace are checked in final validation. Desktop/mobile screenshots were inspected. Earlier test-fixture failures (incorrect model/context field names and an assumed unknown-count baseline) were corrected using the actual model/context; no unrelated assertions were removed to obtain a pass.

Evidence/reproduction: `scratch/super-analytics-20261026/run-tests.py` accepts the Django module labels; final broad labels are in `regression-tests.txt`, while the final focused run is `targeted-tests.txt`. `prepare-browser.py` generates the Playwright verification; run `node scratch/super-analytics-20261026/verify.cjs` after isolated fixtures exist. `live-read-check.py`, `snapshot.py`, original scoped copies, screenshots and `validation-summary.json` record reproducible evidence. The exact modified-file manifest is in `validation-summary.json`.

### 8. Remaining limits / troubleshooting / separate approval

- Real shared checkout identifiers are not captured in the current per-product order model. Frequently Bought Together therefore retains its honest insufficient-data state. No baskets were inferred from buyer/day or bundle components. New capture would require a separate task/approval.
- Historical physical inventory and facility configuration cannot be reconstructed from current snapshots. Bundle availability is derived, and shelf-life/FEFO/Returns/Refunds were not added.
- Services lack verified completion-event/payment/results-release history sufficient for a new completion-time or cashier-revenue trend. Current statuses of submission-period requests remain useful; no events or fees were invented.
- Active Sellers and Repeat Buyers definitions remain the existing definitions. Person-level deduplication across web/mobile accounts and a changed buyer/seller definition require a separate decision, not an undocumented inference.
- There are no new analytics exports, models, dependencies or algorithms. Existing report exports and administration pages are reused. Tables retain existing server-side bounds; local sorting is not a new unbounded dataset or pagination API.

Troubleshooting: if a preset seems overridden, inspect `period` plus disabled custom inputs and the Super Admin flag. If utilization is unavailable, inspect actual facility type, operating ranges, room assignments and configured slots; never fill in an assumed capacity. If revenue is empty, check both status/payment, positive quantity, authorized scope and recognition date rather than order creation date. Zero-price qualifying orders intentionally keep the chart. If another role unexpectedly receives new markup, inspect `super_analytics` and the body class before altering permissions. Failed/unverifiable reads must not be replaced with fabricated zeros.

Safe practice exercise: select a custom period, switch tabs, then select a seven-day preset. Confirm the dates and per-module cohort explanations. Open View chart data with Enter and close with Space; compare a peso total with Generate Reports using the same recognition dates. Use isolated test fixtures to verify zero-price, month-boundary and unavailable-capacity states. Do not create working sales, payments, inventory batches or audit events merely to fill charts for a demonstration.

October25,2026 inventory/report follow-up: [FIFO guide](fifo-inventory.md) covers the complete approved implementation, exact file/line map, functions/data flow, actual tests, troubleshooting and separate cutover gate. `build_report('products')` now outputs Quantity Basis and separate physical/derived summaries; its chart uses physical rows only. Product/Low Stock descriptions identify current snapshots with submission-date filtering, and User Login Activity states latest login per web account. Existing preview/CSV/serverPDF/nativeprint consume the same description/rows; Completed AND Paid Sales eligibility remains. Safe exercise: run `InventoryReportAccuracyTests` in the isolated database and verify70physical units and20derived bundles stay separate; never adjust live stock to match a report. No working database migration or stock change occurred.

## October 25, 2026: Sales Report recognizes completed AND paid orders

### 1. Cause / reason

The evaluator-readiness audit confirmed that the Sales Report used `Paid OR Completed`, while the dashboard's `_revenue_orders` requires both. This could recognize a paid pending/processing/ready/cancelled order, or an unpaid completed legacy record, as revenue. The correction changes only Sales Report eligibility and its matching summary label; it does not change how an order becomes paid or completed.

### 2. Exact files changed / current lines and anchors

| File / current line | Anchor and change |
| --- | --- |
| `backend/core/modules/reports/reporting.py:150` | `_order_report`: keep the original authorized query/date filtering, but the `sales` branch at line 158 now filters `status=STATUS_COMPLETED, payment_status=PAYMENT_PAID` together. |
| Same file, line 176 | Summary label now reads `Completed & Paid Orders`, matching the actual intersection. |
| `backend/core/modules/reports/test_sales_overview.py:18` | `SalesReportRevenueTests`: six isolated tests for the status matrix, monetary aggregates/chart, dashboard eligibility/total, original date behavior, Orders Report, preview/page, CSV/PDF, empty revenue, permissions and program scope. Optional exports under `SALES_REPORT_REVIEW_DIR` support artifact/browser checks. |
| `docs/superadmin-analytics-module.md:3` | This current implementation, verification, troubleshooting and learning report. |
| `CAMPUSHUB_CONTEXT.md:3` | Record the corrected eligibility and current verification/limitations. |

No other runtime file was changed for this fix. Earlier unrelated working-tree changes remain. Review artifacts and the original source snapshot are under `scratch/sales-report-revenue-review/`.

### 3. Changes made

The Sales Report now includes Completed + Paid and excludes Completed + Unpaid, Pending + Paid, Processing + Paid, Ready for Pickup + Paid and Cancelled + Paid. `Processing` is the existing stored status used for the confirmed/processing stage; no new Confirmed status is added. Revenue, eligible-order count, products sold, average order value, chart values and exported rows all derive from that filtered set. The ordinary Orders Report continues to show the excluded status/payment combinations as order records.

### 4. How it works / functions, inputs, outputs and data flow

`build_report(report_type, date_from, date_to, user=...)` in `reporting.py:453` calls `_order_report` for Sales/Orders. Its inputs are the existing selected report, optional dates and authenticated user. `_scope_marketplace` still restricts the dataset by existing Program/Major rules; `_filter_dates` still applies the selected range to `created_at`. Only then does the Sales branch require both existing status constants. The same filtered rows generate the summary and chart. `build_report` returns the original columns/rows/summary/chart structure, serializing Decimal row amounts as strings.

The existing page and preview endpoint consume `build_report`. CSV download calls the same builder and writes its rows. Server PDF download renders the same rows through ReportLab. The current browser Print PDF action uses the already-loaded report preview and native print layout, rather than requesting the server PDF endpoint. Both PDF paths were checked; no print/export route or template changed.

Annotated isolated example:

```text
Completed + Paid, total PHP106.50, quantity3 -> included
Completed + Paid, total PHP213.50, quantity1 -> included
Five orders covering the other requested combinations -> excluded
Revenue = 106.50 + 213.50 = PHP320.00
Recognized orders = 2; units = 4; average order value = PHP160.00
```

The tests compare eligible order IDs and aggregated `total_price` against the existing dashboard helper `_revenue_orders`. Using two keyword conditions gives the required SQL AND without adding another revenue service, changing global order queries or altering reporting-period semantics.

### 5. Backend / API behavior

The report builder's Sales eligibility changes intentionally; page/preview/download contracts, date filters, permission checks, report history logging, CSV/PDF formats and Orders Report behavior remain. No inventory, reservation, completion, Cash on Pickup, payment recording, cancellation, seller ownership, FIFO, Returns or Refunds workflow changes. No runtime JavaScript, UI layout, dashboard query or unrelated module changes.

### 6. Database / migration impact

No models, migrations, schema changes or production data writes. Tests create simulated legacy/status combinations only in the separate Django test database. Export endpoint tests create their normal `GeneratedReport` audit records there; browser checks intercept requests and never send production writes. The generated codes are actual codes assigned by the existing model to isolated test orders.

### 7. Tests performed / actual results

- The final **six new `SalesReportRevenueTests` passed** after adding an explicit dashboard monetary-total comparison. Tests confirm PHP320.00 recognized revenue, four units, two orders and PHP160.00 average; all five ineligible fixtures are absent.
- A broader **54-test run completed: 51 passed and 3 failed** across `modules.reports.test_sales_overview`, `accounts.tests.AdminReportTests`, `modules.reports.tests` and `modules.reports.test_facility_revenue`. All six new tests passed in that run. The three failures were reproduced with the original `_order_report` loaded only in memory from its pre-edit snapshot: missing old analytics subtitle text, old mixed-chart/dual-axis JavaScript expectations, and the existing user-monitoring permission test expecting403 but receiving200. No application file was reverted, and no unrelated test or access rule was changed to hide these failures. Logs: `regression.log`, `baseline-failures.log`, `final-focused.log`.
- Parsed the actual generated PDF with installed `pypdf`: both eligible order IDs and their PHP106.50/PHP213.50 values were present; all five ineligible IDs were absent. Parsed actual CSV amounts totaled PHP320.00. The permanent tests verify actual PDF creation plus its table rows matching CSV; no PDF-parser dependency was added to application requirements.
- **30/30 Chromium browser checks passed** at1366px/390px: corrected preview summary, two eligible rows, existing native print invocation/data/cleanup, excluded IDs absent, print amounts totaling320, matching CSV download bytes and no JavaScript errors. This checks print content before the operating-system print dialog; physical printing was not tested.
- Scoped `git diff --check` passed. No production transaction was submitted for verification.

Reproduce the six focused checks from `backend/core`:

```powershell
./venv/Scripts/python.exe manage.py test modules.reports.test_sales_overview.SalesReportRevenueTests --keepdb --noinput
```

### 8. Remaining reporting inconsistencies / troubleshooting / safe practice

The **status/payment eligibility** is now consistent with the dashboard; identical period totals are not promised because the original date semantics are deliberately preserved. Sales Report filters order `created_at`, while marketplace analytics uses completion/payment/creation fallback. An order created before the period but completed inside it can still produce different period totals. Analytics' `valid_sales_queryset` additionally excludes zero-quantity legacy rows; this task did not add that extra filter to Sales Report or modify dashboard helpers.

Other audit observations remain outside this fix: User Login Activity shows each account's latest login rather than full login history; Product & Inventory shows current stock filtered by product submission date and can sum derived bundle availability alongside component quantities. The three baseline failures above also remain; the permission failure needs a separate access-policy review. Historical exported files are unchanged and must be regenerated to reflect corrected eligibility.

If totals seem wrong, check the report's date range, product-owner scope, stored order/payment statuses and whether the order falls inside the creation-date range. Do not mark an unpaid order paid or complete it just to make a report match. Refresh the report preview or reopen it after deployment; native printing uses the currently loaded preview.

Safe practice exercise: run only the focused test class against the isolated test database. Read `test_status_matrix_totals_chart_and_dashboard_eligibility`, predict which fixture orders contribute and verify the 320/2/4/160 results. Read `test_creation_date_filter_and_orders_report_remain_unchanged` to explain why an outside-period creation remains excluded even when its completion date is inside. Do not create or change production orders for this exercise.

## October 20: separate row immediately below the header (current)

1. **Reason:** user clarifies the toolbar must sit below, outside the header, while retaining inline tabs/date controls.
2. **Files and anchors:** `backend/templates/partials/admin_header.html:3` restores its ordinary class; after `</header>` near line 98 the Super Admin-only `analytics_subheader` flag renders the toolbar as a sibling. `reports/partials/analytics_toolbar.html:1` accepts `below_header=True` to add `analytics-subheader`. `backend/static/components/css/admin_analytics.css:711` replaces header-grid rules with 12px vertical/24px horizontal row padding (16px horizontally below 599px). Five analytics templates rename the header presentation flag and refresh the CSS version: Marketplace line 20, Facilities 23, Services 19, Users 20, legacy domain 9. Existing context, scratch template check and this guide updated.
3. **Changes:** ordinary white header stays separate. Immediately below it, the toolbar aligns tabs to the title's left edge and dates to the right. Navy segments, Poppins and small gold accent are unchanged; no additional card or gradient.
4. **Data flow:** Analytics page passes `analytics_subheader=True`; existing shared header partial outputs the closed header, then the existing toolbar partial with its modifier. The HTML toolbar is outside `<header>` even though the same template composes both siblings. Original module/date inputs and links are reused, and the non-Super-Admin body condition prevents duplicate navigation/forms.
5. **Backend/API:** unchanged views, permissions, filter scripts and chart data.
6. **Database/migrations:** none.
7. **Checks:** isolated template render passed eight module/period cases, two scoped-role cases and compilation of five analytics pages. Verified exactly one toolbar after the closing header. Headless desktop/mobile checks passed at 1280/390/320px for preset/custom dates: matching title/tab left edges, non-overlap, no page overflow and correct active navy. Desktop screenshot inspected; no app/server restart.
8. **Limits and practice:** signed-in full-page QA remains pending. Refresh Analytics and verify the header ends before the tabs row; select Facilities and a date preset to confirm the same filtering. If duplicated, inspect the complementary Super Admin header/body conditions. Do not change backend views to fix layout.

## Earlier October 20: align the toolbar as the header's second row

1. **Reason:** user now asks to align the existing toolbar with the header as a second row. This supersedes the content-toolbar placement below; the refined segmented styling remains.
2. **Files / anchors:** `backend/templates/partials/admin_header.html:3` conditionally adds `analytics-header-with-toolbar`; line 97 includes the existing toolbar after the title/actions row. `backend/static/components/css/admin_analytics.css:711–720` defines a two-column header grid with 12px row spacing and a full-width second row. The five analytics page templates pass `analytics_second_row=True` in their existing header include (`admin_marketplace_analytics.html:20`, `admin_facility_analytics.html:23`, `admin_services_analytics.html:19`, `admin_users_analytics.html:20`, legacy `admin_domain_analytics.html:9`). Their original body toolbar includes (24/27/23/24/11 respectively) now render only for non-Super-Admin roles; CSS cache versions use `20261020-second-row`. Context, this guide and existing scratch verification scripts were updated.
3. **Changes:** Super Admin title/breadcrumb/actions remain row one. Segmented tabs and date controls form row two, using the same left/right header padding. Current navy `#1A1F71`, Poppins, gold accent and responsive wrapping remain. Other pages retain their ordinary header; scoped admin analytics retain content navigation.
4. **How it works:** page include passes a presentation flag; shared header checks the existing Super Admin flag/role before including `analytics_toolbar.html`. That partial still reuses original module/date partials. Example: Facilities remains selected through `analytics_module='facilities'`; its same GET form and period inputs now render inside the header. The complementary body condition prevents duplicate forms or IDs.
5. **Backend/API:** no view, permission, calculation, URL, chart data or filter-script changes.
6. **Database/migrations:** none; no records changed.
7. **Verification:** isolated template checks passed eight module/period cases, two scoped-role cases and five page compilations; checked one second-row toolbar after action markup. Headless previews at exact 1280/390/320px preset/custom states passed matching title/tab left edges, non-overlapping rows, no page overflow, correct active color and desktop left/right layout. Desktop screenshot inspected. Preview uses production header/toolbar/CSS and local equivalents for Bootstrap hidden-dropdown utilities; it does not load signed-in account data. No app/server restart.
8. **Limits / practice:** signed-in full-page visual verification remains pending. Refresh Super Admin Analytics and confirm tabs start directly under the title, date dropdown ends at the header's right padding, and switching tabs/dates keeps the existing selection and charts. On a narrow screen confirm controls wrap without covering the heading. If navigation appears twice, inspect the complementary Super Admin header/body conditions rather than changing Django views.

## October 20: refined segmented appearance (current styling)

1. **Reason:** user requests softer segmented styling and explicitly overrides the tab navy to `#1A1F71`.
2. **Files / current anchors:** `backend/static/components/css/admin_analytics.css:711` (`.analytics-toolbar`) defines scoped `--analytics-tab-navy`; line 728 uses 4px container padding and line 731 uses 14px outer corners. Link rules near 733 use 10px corners, Poppins 13px/500, white inactive surfaces and navy text. Active rules at 749 and 753 use solid navy/white and a centered 14×2px gold accent. The five analytics page templates (`admin_marketplace_analytics.html:13`, `admin_facility_analytics.html:13`, `admin_services_analytics.html:13`, `admin_users_analytics.html:13`, `admin_domain_analytics.html:7`) only update the stylesheet version to `20261020-segments`. Existing scratch template/browser verification scripts track that version and the new expected active color. This guide and the context note record the update.
3. **Changes:** rounded white segmented container, subtle gray border, soft padding, flat medium-weight tabs and a tiny gold active underline. Solid fill was selected; a gradient was optional and unnecessary.
4. **How it works:** existing module links retain `aria-current="page"`; CSS uses that attribute to apply the active fill and decorative pseudo-element. The scoped custom property affects only these tab colors. Example: selecting Facilities changes which existing link carries `aria-current`, so the navy segment and gold accent follow it automatically. Toolbar placement, responsive wrapping, keyboard focus, 44px targets and date form remain.
5. **Backend/API:** no changes to views, permissions, scripts, data or URLs.
6. **Database/migrations:** none.
7. **Verification:** isolated template checks again passed eight module/period cases, two scoped roles and all five page compilations. Exact browser viewports 1280/390/320px passed preset/custom layouts with no page overflow, active color `rgb(26,31,113)` and retained desktop alignment. Desktop screenshot inspected. No app/server restart.
8. **Limitations / safe exercise:** signed-in full-page verification remains pending. Refresh Analytics, switch each tab and check one navy segment with a small gold mark. Use keyboard Tab to verify focus remains visible and choose a date preset to confirm the original filter still operates. If old colors persist, check the updated stylesheet version before editing backend code. The earlier toolbar section below explains the unchanged inputs, outputs and date data flow.

## October 20: compact content toolbar above KPIs

1. **Cause / reason:** the user now requests tabs outside the global header, grouped with the existing date dropdown directly above KPIs. This supersedes the header placement below. An older mobile rule also stacked custom-date labels with a 100px flex basis; the toolbar overrides its direction to avoid large gaps.
2. **Exact files changed:**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/templates/partials/admin_header.html` | 3 `dashboard-header`; closing header near 97 | Removed the Analytics-only class and module include; original title, breadcrumb and action controls retained. |
| `backend/core/modules/reports/templates/reports/partials/analytics_toolbar.html` | 1 `analytics-toolbar` | New composition of the existing navigation and date partials; no duplicate navigation/filter logic. |
| `backend/static/components/css/admin_analytics.css` | 710 compact toolbar comment; 711 `.analytics-toolbar`; 759 responsive rules | Left/right layout, navy selected segment, white surface, subtle border, Poppins, focus styles, 44px targets and narrow-screen wrapping. Removed superseded header-tab rules. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 10 fonts; 13 stylesheet; 20 header; 24 toolbar | Added Poppins to existing font request, refreshed CSS version, removed header opt-in and replaced separate tabs/date includes with toolbar. |
| Same folder: `admin_facility_analytics.html` | 23 header; 27 toolbar | Same composition, font and stylesheet updates. |
| Same folder: `admin_services_analytics.html` | 19 header; 23 toolbar | Same updates. |
| Same folder: `admin_users_analytics.html` | 20 header; 24 toolbar | Same updates. |
| Same folder: `admin_domain_analytics.html` | 9 header; 11 toolbar | Same updates; removed redundant inner title/date row so the toolbar sits above KPIs. |
| `CAMPUSHUB_CONTEXT.md` | latest toolbar note | Records accepted layout. |
| This guide | current section | Reason, behavior, verification and learning steps. |

3. **Changes made:** compact segmented navigation appears on the left of the content toolbar, existing date dropdown on the right. Active segment is navy `#1A1851` with white text. No gradients, shadow or extra toolbar card. On narrow screens tabs can scroll within their strip and dates wrap underneath; custom fields stay usable. Header/sidebar retain their original roles. Poppins is scoped to toolbar labels and controls; existing chart typography remains.
4. **How it works / inputs and outputs:** each page includes `analytics_toolbar.html`; it renders the unchanged `analytics_modules.html` and `analytics_dates.html`. `analytics_module` controls the selected link and hidden form module; `analytics_links` supplies URLs carrying the active period/date range; `analytics_period` sets the dropdown and custom dates. The existing GET form IDs remain, so existing JavaScript still shows Custom fields and submits preset selections once. Example: Facilities + Last 7 Days submits the existing `module=facilities&period=7` parameters; only the layout around that form changed. Composition avoids creating another controller or search/filter system.
5. **Backend/API behavior:** existing Django views, permission checks, chart JSON and aggregation logic are unchanged. Link visibility still uses the original module partial's permissions. No JavaScript, API or chart-data changes.
6. **Database / migration impact:** none; no records, schemas or migrations changed.
7. **Tests performed:** isolated Django render passed eight module/period cases, two scoped-role cases and compilation of all five page templates. Checked one toolbar before KPIs, one active link, preserved module/date parameters/form IDs and no navigation in the global header. Both existing filter scripts passed a DOM check: Custom reveals date inputs, preset selection submits once, repeat selection prevents duplicate submission. Headless Chrome verified exact 1280/390/320px viewports for preset and custom states: no page overflow, correct navy active color, desktop tabs left/dates right. Desktop and narrow-screen toolbar screenshots were inspected. No database or running app was used; no app/server restart.
8. **Limitations / learning exercise:** visual QA used the actual rendered toolbar in an isolated preview, not a signed-in live page with charts. Existing Google Fonts loading needs network access; fallback is sans-serif. Safely open Reports → Analytics, switch all four sections, choose Last 7 Days then Custom, apply a harmless date range, and verify the selected module/date range and existing charts. Narrow the browser and keyboard-tab through links, dropdown and dates. Refresh if old header styling is cached. If filtering fails, inspect the preserved `analyticsPeriodForm`, `analyticsPeriod`, `analyticsCustomDates` IDs and existing script loading before changing backend code.

Verification artifacts: `scratch/verify_analytics_toolbar.py`, `scratch/verify_analytics_toolbar_browser.js`, `scratch/analytics-toolbar-browser.log` and `scratch/analytics-toolbar-{1280,390,320}[-custom].png`. The superseded header diagnostic was removed.

## Historical October 19: Super Admin tabs inside the Analytics header

1. **Reason:** user confirmed the four module links belong inside the Analytics header. They previously appeared in the page content below it.
2. **Exact files and anchors:** `backend/templates/partials/admin_header.html:3` adds the scoped `analytics-dashboard-header` class; line 97 includes the existing module navigation. `backend/static/components/css/admin_analytics.css:711` scopes the two-row header layout and underline tabs. The five templates under `backend/core/modules/reports/templates/reports/pages/` opt in through the existing header include: `admin_marketplace_analytics.html:20`, `admin_facility_analytics.html:23`, `admin_services_analytics.html:19`, `admin_users_analytics.html:20`, and `admin_domain_analytics.html:9`. Their body includes (lines 24, 27, 23, 24, 11 respectively) now serve non-Super-Admin users only. All five refresh the analytics stylesheet cache version. `scratch/verify_analytics_header.py` is the isolated verification artifact; this guide records the implementation.
3. **Changes:** Marketplace, Facilities, Services and Users now form the bottom row of the Super Admin header, below title/breadcrumb and existing account controls. Navy labels, gold active underline, white background, 44px targets, focus outlines, and horizontal tab scrolling on narrow screens. Sidebar retains one Analytics destination.
4. **Functions and data flow:** page include supplies `analytics_header=True`; shared header checks Super Admin flag/role, then renders the existing `analytics_modules.html`. Its `analytics_links` input retains period/date parameters; `analytics_module` selects `aria-current="page"`. Example: `analytics_module='facilities'` highlights Facilities while its existing URL still selects the facility backend view. Non-Super-Admin analytics retain their previous content navigation, preventing duplicates. Other shared headers do not opt in.
5. **Backend/API:** existing views, permissions, analytics calculations and navigation URLs reused. No new endpoint or business logic.
6. **Database/migrations:** none; no records changed.
7. **Verification:** isolated Django template render passed eight Super Admin role/module cases, two exclusion cases, and compilation of all five page templates. Checks confirm one header navigation row, one selected link, date parameters and valid stylesheet references. No database accessed; no app/server restarted.
8. **Limitations/practice:** browser/device visual verification remains pending. Safe exercise: open Reports → Analytics as Super Admin; select each tab and verify the underline and retained dates, then narrow the browser and use keyboard Tab to reach each link. Other admin pages should retain their original one-row header. Refresh if the browser retains older CSS. Runtime analytics/database calculations were outside this layout-only check.

## Earlier October 19 correction: sidebar move reverted

The requested sidebar move was misunderstood and reverted. `backend/templates/partials/admin_sidebar.html` (Reports / Analytics link, around line 180) retains its single Analytics link. `reports/partials/analytics_modules.html` (line 1, `analytics-module-nav`) retains the existing horizontal Marketplace, Facilities, Services and Users links. The five `backend/core/modules/reports/templates/reports/pages/admin_*analytics.html` templates include it above their controls (Marketplace line 24, Facilities 27, Services 23, Users 24, legacy domain 11). The temporary submenu stylesheet and diagnostic script were removed.

The existing `analytics_links` input supplies URLs with the selected date period; `analytics_module` selects the active tab. Clicking a link still loads the existing authorized Django view and database-derived analytics. No backend/API, database or migration change. Static inspection confirms all five includes and no sidebar submenu; browser rendering and runtime tests were not completed during this interrupted change. Safe practice: open Analytics, choose Facilities, then Services and check the selected tab and date period remain correct. If the old submenu remains visible, refresh the page.

## 1. Overview and Purpose
The **Super Admin Analytics** module delivers a unified, data-driven analytical dashboard across four core domains:
1. **Marketplace** (`?module=marketplace`)
2. **Facilities** (`?module=facilities`)
3. **Services** (`?module=services`)
4. **Users** (`?module=users`)

The module is accessible from a single **Reports &rarr; Analytics** sidebar item in the Django Super Admin web panel. It adheres strictly to the Institutional Design System:
- **Primary Navy Blue**: `#1A1851`
- **Accent Gold**: `#FCB315`
- **Light Neutral**: `#FFFFFF` / `#F8FAFC`
- **Subtle Institutional Border**: `#E8EAF0`
- **Zero AI-Slop**: No gradients, 3D slop, glowing cards, or fabricated metrics.

All metrics originate directly from real PostgreSQL database records through the Django ORM.

---

## 2. Architecture and Data Flow

```
HTTP Request (?module=...&period=...&date_from=...&date_to=...)
                         │
                         ▼
     [views.py: admin_marketplace_analytics_page]
                         │
        ┌────────────────┴────────────────┐
        │                                 │
(module == 'marketplace')     (module in facilities/services/users)
        │                                 │
        ▼                                 ▼
[build_marketplace_analytics]     [render_domain_analytics]
        │                                 │
        │                       ┌─────────┼─────────┐
        │                       │         │         │
        │                   facilities services   users
        │                       │         │         │
        ▼                       ▼         ▼         ▼
[admin_marketplace_     [admin_facility_ [admin_services_ [admin_users_
 analytics.html]         analytics.html]  analytics.html]  analytics.html]
```

### Shared Global Date Range Filter
Each tab shares a unified date range filter:
- `7`: Last 7 Days
- `30`: Last 30 Days (Default)
- `90`: Last 90 Days
- `year`: This Year (Jan 1 to today)
- `custom`: Custom Date Range (`date_from` to `date_to`)

When switching between horizontal tabs, active date parameters are preserved via `module_links(period)` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L72-L85).

---

## 3. Detailed Tab Implementation

### 3.1 Marketplace Analytics
- **Template**: [admin_marketplace_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html)
- **Data Builder**: `build_marketplace_analytics` in [analytics.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/services/analytics.py#L617-L713)
- **KPI Cards**:
  1. *Total Sales Revenue*: Sum of `total_price` from qualifying completed and settled Cash-on-Pickup orders (`STATUS_COMPLETED` and `PAYMENT_PAID`).
  2. *Completed Orders*: Count of completed, paid orders within the period.
  3. *Active Sellers*: Sellers with at least one active listing or sale.
  4. *Approved Products*: Count of active catalog products with `approval_status='approved'`.
- **Main Bar Graph**: Monthly/Weekly/Daily sales performance rendered via Chart.js with Navy `#1A1851` bars and currency tooltips.
- **Top-Selling Products**: Ranked table of completed order items showing product name, seller, units sold, and revenue.
- **Order Status Breakdown**: Visual distribution of all orders submitted in the period across `pending`, `processing`, `ready_for_pickup`, `completed`, and `cancelled`.

### 3.2 Facilities Analytics
- **Template**: [admin_facility_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html)
- **Data Builder**: `build_facility_tab_analytics` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L104-L269)
- **Physical Isolation**: Filters out service booking facilities (e.g. Food Analysis Lab) using `service_resources_q("facility__")` and academic blocks via `schedule_blocks_q()`.
- **KPI Cards**:
  1. *Total Bookings*: Total physical facility reservations requested in the period.
  2. *Approved Bookings*: Reservations with status `approved` or `completed`.
  3. *Pending Bookings*: Active reservation requests awaiting administrative review.
  4. *Cancelled / Rejected*: Terminated or disapproved reservations.
- **Main Bar Graph**: Bookings by Physical Facility (Covered Court, Function Hall, Mock Hotel) rendered with navy bars.
- **Monthly Booking Trend**: Historical monthly progression of approved reservations.
- **Booking Status Breakdown**: Proportional status bars.
- **Facility Utilization Table**: Physical facility breakdown with capacity hours, approved counts, total reserved duration, and estimated utilization rate.

### 3.3 Services Analytics
- **Template**: [admin_services_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_services_analytics.html)
- **Data Builder**: `build_services_tab_analytics` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L271-L358)
- **Authentic Operational Model**: Services operate primarily as specialized informational and offline ISO procedures:
  - *Food Analysis Hub*: ISO Document `DPM-USTP-Oro-BEU-004` (Focal person: Conmar C. Malmis, BEU).
  - *BPP NC II Assessment Center*: Technical assessment reservation.
  - *Commercial Spaces*: Campus business lease application.
- **Honest Empty States**: If no electronic service requests have been submitted, displays an authentic informational overview of registered facilities and ISO guidelines without fabricating artificial transactions or synthetic graphs.

### 3.4 Users Analytics
- **Template**: [admin_users_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html)
- **Data Builder**: `build_users_tab_analytics` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L360-L472)
- **KPI Cards**:
  1. *Total Users*: Sum of registered mobile (`CampusHubUser`) and administrative (`User`) accounts.
  2. *New Registrations*: Accounts created within the active date period window.
  3. *Active Accounts*: Un-suspended accounts with `is_active=True`.
  4. *Approved Sellers*: Sellers with approved `SellerRequest` records.
- **Main Bar Graph**: User Registrations by Month showing account acquisition trends.
- **User Distribution**: Proportional breakdown across student, employee, guest, and administrator accounts.
- **Seller Application Statistics**: Total seller privilege requests grouped by Approved, Pending, Rejected, and Suspended.

---

## 4. Key Functions and Data Types

| Function | File | Input | Output | Description |
| :--- | :--- | :--- | :--- | :--- |
| `analytics_period(request)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L48-L70) | `HttpRequest` | `tuple[dict, AnalyticsPeriod]` | Resolves preset (`7`, `30`, `90`, `year`) or custom range; validates bounds |
| `module_links(period)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L72-L85) | `AnalyticsPeriod` | `dict[str, str]` | Builds tab URLs preserving the active date filter |
| `build_marketplace_analytics(...)` | [analytics.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/services/analytics.py#L617-L713) | `params: dict, user=None` | `dict` | Aggregates settled marketplace revenue, orders, inventory, and status breakdown |
| `build_facility_tab_analytics(...)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L104-L269) | `period, params, user=None` | `dict` | Aggregates physical facility bookings, charts, utilization, and trends |
| `build_services_tab_analytics(...)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L271-L358) | `period, params, user=None` | `dict` | Returns registered BEU services, ISO workflows, and real request counts |
| `build_users_tab_analytics(...)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L360-L472) | `period, params, user=None` | `dict` | Computes account creations, role distributions, and seller privilege stats |

---

## 5. Debugging and Troubleshooting

### 1. Inverted Date Range Error (HTTP 400)
- **Symptom**: User selects custom dates where `date_from > date_to` (e.g. from Oct 20 to Oct 10).
- **Cause**: [parse_analytics_period](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/services/analytics.py#L91-L92) checks `if start > end: raise ValueError("Start date must be on or before end date.")`.
- **Handling**: `admin_marketplace_analytics_page` catches `ValueError` and returns `HttpResponseBadRequest(str(error))`.
- **Resolution**: Ensure the frontend date picker sets `min` and `max` constraints, or correct the parameters in the query string.

### 2. Scoped Administrator Authorization (HTTP 403)
- **Symptom**: A Marketplace Admin attempts to access `?module=facilities`, `?module=services`, or `?module=users` and receives a 403 Forbidden.
- **Cause**: Super Admin Analytics restricts domain-specific access via role-based permissions in [render_domain_analytics](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L514-L525). Marketplace Admins only hold `can_view_marketplace_analytics`.
- **Verification**: Ensure Super Admin credentials (`is_superuser=True` or `role='Super Admin'`) are used when evaluating all four tabs.

---

## 6. Safe Practice Exercise

To test adding a new metric to the Users Analytics tab:
1. Open [backend/core/modules/reports/analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L365).
2. Locate `build_users_tab_analytics`.
3. Add a verified email count:
   ```python
   verified_users = mobile_qs.filter(email_verified=True).count()
   ```
4. Include `"verified_users": verified_users` in the `"kpis"` sub-dictionary.
5. In [backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html), render the new card:
   ```html
   <article class="analytics-kpi">
       <span>Verified Emails</span>
       <strong>{{ users_tab.kpis.verified_users }}</strong>
       <small>Accounts with confirmed institutional email</small>
   </article>
   ```
6. Run the test suite:
   ```powershell
   backend\core\venv\Scripts\python.exe backend\core\manage.py test modules.reports.test_superadmin_analytics
   ```
