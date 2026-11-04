# Marketplace Analytics: ranked products, category sales and persistent chart layout

Implemented October 4, 2026 for the CampusHub Super Admin Dashboard.

Latest operations follow-up: Recent Orders and Inventory Alerts now have separate full-width cards within the existing Marketplace column, 16px apart. They follow this unchanged independent ranking card; its placement, title, ranking data and refresh behavior remain. The older shared operations wrapper described below has been removed. Current files, functions/data flow, verification, troubleshooting and safe practice are in the [dashboard operations report](dashboard-analytics-operations-update.md).

## Current: Independent ranking card outside Sales Overview — October 31, 2026

### 1. Cause / reason

The latest follow-up requests a separate Top-Selling Products card under Marketplace Overview, outside Sales Overview. Although its accordion was already removed, its include still lived inside `super_marketplace_sales.html`, making it a descendant of `#sales-overview-card` and the same surrounding content container. This update moves the existing include to the Marketplace section itself.

### 2. Exact files changed

- `backend/templates/dashboard/partials/super_marketplace_sales.html:35`: remove the product-card include from the sales chart row. Keep the existing Sales Summary/Trend and all their hooks.
- `backend/templates/dashboard/partials/executive_dashboard.html:31`: give Sales Overview its own `marketplace-sales-card` wrapper. Line 34 includes Top-Selling Products as a direct Marketplace Overview child. Line 35 retains Recent Orders/Inventory in `marketplace-operations-card`, preserving their content and original order below rankings.
- `backend/static/components/css/admin_executive_refinement.css:163`: use the shared 10px radius for the standalone ranking card. Lines 167–168 set 16px between Sales, Rankings and Operations and remove the now-redundant inner operations top margin. Ranking header/body/empty styles remain.
- `backend/templates/dashboard/pages/admin_dashboard.html:29`: version CSS as `20261031-products-independent`.
- `docs/dashboard-marketplace-ranked-sales.md:5`, `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:11`: record the independent placement and verification. Prior reports remain history.
- `docs/dashboard-attention-required-4.md:27`: maintain shifted CSS line references only; its card behavior remains unchanged.

### 3. Changes made

Marketplace Overview now contains its outside section heading, a Sales Overview content card, one independent Top-Selling Products card, and the existing operations content card. Rankings retain their single internal title/subtitle, compact empty state, chart and fallback. No accordion or duplicate heading returns. All three content cards use the existing white surface, subtle border/radius and consistent 16px separation. Other dashboard sections retain their layout.

### 4. How it works / functions, inputs, outputs and data flow

Only the template include position and container styling change. The same `dashboard_marketplace.top_products` input is available in the Marketplace parent context, so moving the partial does not require a new query or response. It still outputs the same `topSellingProductsData`, canvas, empty/error/retry and accessible-description IDs.

Existing `top_selling_products()` aggregation → existing Django context/API → the same ranking partial → the same chart listener remains the data flow. The global `load()`/`render()` functions and ranking script find their existing IDs in the dashboard, independent of whether the card is inside Sales Overview. Sales grouping continues affecting the sales chart, while global period/Refresh continues supplying actual rankings. No executable JavaScript changes were needed.

Safe structure example:

```text
Marketplace Overview section
  section heading
  marketplace-sales-card: existing Sales Overview
  #topSellingProductsCard: one independent ranking card
  marketplace-operations-card: existing Recent Orders and Inventory
```

Safe practice: inspect `document.getElementById('topSellingProductsCard').closest('#sales-overview-card')` in DevTools; it should return `null`. Its direct parent should be the Marketplace section. Select Last 30 Days and Refresh, then compare chart names/quantities with `marketplace.top_products` in the existing response. Resize to phone width and inspect the independent borders/gaps. No data edits are required.

### 5. Backend / API behavior

Unchanged. Actual completed/paid-sales eligibility, selected-period filtering, top-five ordering, parent grouping, permissions, response fields, query count, keyboard inspection, chart fallback and retry behavior remain. The include still uses the actual Django values once.

### 6. Database / migration impact

None. No live records, schema, migrations, environment, runtime restart or remote deployment changed. Tests used disposable localhost PostgreSQL records and blocked browser non-GET requests.

### 7. Tests performed

- **48/48 existing Django marketplace/executive/empty-state tests passed in 24.200 seconds**, covering actual ranking calculations, sales eligibility/dates, variants, query bounds, destinations/role isolation and current-template rendering.
- **1560/1560 Chromium checks passed across 14 actual fixture renders/eight widths (280–1920px)**. New measurements verify a direct Marketplace parent, no Sales Overview ancestor, 16px gaps before/after the card and the matching 10px radius. Existing single-heading/no-accordion, actual chart labels/quantities, empty height, keyboard, date/Refresh, product retry, library fallback, priority-card heights and outside overview headings also passed. No browser writes occurred. Full desktop hierarchy and phone ranking screenshots were inspected.
- Evidence: `scratch/dashboard-independent-products-20261031/django.log`, `browser.log`, `browser-result.json`, `ranked-1440.png` and phone/card captures. Scoped file/whitespace checks accompany the results.

### 8. Remaining limitations / troubleshooting

Restart the user-controlled Django process if templates are cached, then refresh Dashboard to load `20261031-products-independent`. If the card remains nested, confirm the include exists only in `executive_dashboard.html`, after the sales wrapper closes. If spacing doubles above Recent Orders, inspect the operations wrapper's 16px external gap and zero inner row top margin. Long labels and phone text continue to wrap under the existing rules. No deployment or other-browser/physical-device certification is claimed.

## Previous: Always-visible Top-Selling Products card — October 31, 2026

### 1. Cause / reason

The latest request removes the unnecessary Top Selling Products accordion and its duplicate label. The existing inner partial already supplied the correct Top-Selling Products title, subtitle, actual ranking chart, empty/error states and refresh hooks. Shared styles also added more padding than this compact card needs. The implementation therefore reuses that partial directly and adds card-specific spacing; no ranking service is rewritten.

| Before | After | Why |
| --- | --- | --- |
| Accordion summary plus inner product heading | One always-visible Top-Selling Products card | Remove duplicate navigation/heading and make rankings immediately available. |
| Shared chart-card/empty padding | 12px header/body padding, 8px empty-message padding | Keep an empty result compact without a reserved chart area. |

### 2. Exact files changed

| File / current line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/super_marketplace_sales.html:36` | Include `super_marketplace_products.html` directly. Remove only the Top Selling Products `details`/`summary` wrapper. Other expandable summaries remain. |
| `backend/templates/dashboard/partials/super_marketplace_products.html:2` | Name the existing internal header `marketplace-products-header`. Line 3 wraps the existing JSON/chart/empty/error/accessibility content in `marketplace-products-body`. Keep the single h3 title, subtitle and all IDs/data hooks. |
| `backend/static/components/css/admin_executive_refinement.css:163` | Scope the border/radius/natural height to `#topSellingProductsCard`. Header styles at 167 and body at 170 use 12px padding. Empty styles at 171–172 remove extra wrapper spacing and use 8px message padding. Other dashboard cards retain their styling. |
| `backend/templates/dashboard/pages/admin_dashboard.html:29` | CSS cache version becomes `20261031-products-card`. No executable JavaScript or script version changes. |
| `docs/dashboard-marketplace-ranked-sales.md:5`, `docs/dashboard-analytics-operations-update.md:3`, `CAMPUSHUB_CONTEXT.md:3`, `docs/web-ui-ux-guidelines.md:9` | Record this presentation decision, data flow, verification and safe practice. Earlier reports remain as history. |
| `docs/dashboard-attention-required-4.md:27` | Update only shifted CSS line references after the new ranking styles; no priority-card implementation change. |

### 3. Changes made

Marketplace Overview now contains one visible Top-Selling Products card, with its title/subtitle inside a bordered header and rankings or the existing specific empty state below. It has no expand/collapse control or duplicate accordion heading. Empty content uses natural height; the existing hidden chart remains absent when there are no eligible sales. Populated chart sizing and the other dashboard sections remain unchanged.

### 4. How it works / functions, inputs, outputs and data flow

The unchanged `top_selling_products(orders, limit=5)` service receives the existing selected-period eligible completed/paid sales queryset. It groups variants by parent product identity, sums quantities and recorded sales, orders by units sold, then sales amount and stable identity, and returns up to five actual product projections. Bundles remain sellable transactions rather than being expanded into physical component sales. Current/historical product-name fallbacks and other snapshot rules remain.

Initial Django output passes `dashboard_marketplace.top_products` to the same `topSellingProductsData` JSON script and accessible quantity description. The existing `admin_marketplace_products_chart.js` reads that array, renders the same ordered bar chart, and responds to `campushub:dashboard-data` after the existing global date/Refresh request. Removing `details` changes visibility only; the IDs, payload keys and callbacks remain.

Example flow, without invented numbers:

```text
Actual eligible orders in selected period
  -> existing top_selling_products() aggregation and top-five ordering
  -> marketplace.top_products / initial Django JSON
  -> existing chart labels and units-sold dataset
  -> single visible card body, or the existing honest empty state
```

The chart's existing failure path still shows the actual product quantities as text if Chart.js cannot load. The existing global API error path keeps the header visible and offers the same Top Products Retry button. All record text continues to use Django escaping/JSON script handling and the existing safe client renderer.

Safe practice: open the dashboard and verify Top-Selling Products is visible without expanding anything. Select a reporting period and Refresh, then compare its names/units with `marketplace.top_products` in the existing response. Use the chart's arrow/Home/End keys to inspect full names and quantities. For a local styling exercise, change only this card's empty-message padding in DevTools, then reload to restore the saved 8px. No data edits are required.

### 5. Backend / API behavior

Unchanged. No new endpoint, aggregation, sales eligibility, date default, permissions, query count, ranking order, response field or Apriori behavior. Existing completed/paid-sales rules and Django/PostgreSQL integration remain the source of truth. Refresh, date filters, retry, keyboard inspection and the chart-library fallback retain their implementations.

### 6. Database / migration impact

None. No model/migration, schema, live data, environment, server/app restart or deployment changes. Test fixtures were confined to disposable localhost PostgreSQL databases. Browser non-GET requests were blocked.

### 7. Tests performed

- **48/48 existing Django marketplace, executive and empty-state tests passed in 24.574 seconds**. They cover top-five ranking, quantity/sales tie-breaking, parent variants/renames, actual selected-period eligibility, workflow exclusions, zero/empty sales, bounded queries, permissions and current-template rendering.
- **1494/1494 Chromium checks passed across 14 actual current-template renders/eight widths (280–1920px)**. Verified one immediately visible card/h3, no surrounding `details`, original internal title/subtitle, 12px header/body padding, borders, no empty chart footprint and a compact empty card below 240px on desktop. Actual five-product chart labels/values match the Django response. Keyboard rank inspection, Refresh/date changes, product-specific retry, visible error headers and library-unavailable quantity fallback passed. Existing priority-card heights/headers and Marketplace/Facilities outside headings remain verified. No browser writes occurred. Empty, populated and phone card screenshots were inspected.
- Evidence: `scratch/dashboard-products-card-20261031/django.log`, `browser.log`, `browser-result.json`, `products-1440-empty-initial.png`, `products-1440-ranked-initial.png`, phone and fallback captures. Populated quantities come from actual isolated Django fixtures, not live/example application records.
- Scoped file/whitespace checks accompany the results. No executable JavaScript was changed.

### 8. Remaining limitations / troubleshooting

Restart the user-controlled Django process if it retains the old templates, then refresh Dashboard to load `20261031-products-card`. If the accordion remains, inspect `super_marketplace_sales.html` and confirm the product partial is included directly. If the chart/empty state does not update, inspect the existing `marketplace.top_products` response and preserved element IDs before changing any backend query. Long labels retain the existing chart abbreviation/full-tooltip/keyboard behavior. On very narrow screens explanatory text wraps naturally; no fixed empty height clips it.

Verification used Chromium and source-rendered fixtures, not a live deployment or physical-device certification. Other facility/service expandable summaries were intentionally retained. The older full-Sales-Trend footprint requirement below is history for that separate component; this follow-up changes only Top-Selling Products.

## Cause / reason

The existing empty sales state hid the chart container, the product summary showed only one leader, and category distribution counted current listings. The requested behavior preserves the full Sales Trend layout, ranks up to five products, and makes categories represent completed, paid sales within the selected date range.

## Exact files changed

| File | Approximate line / code anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_marketplace.py` | 9 `top_selling_products`; 37 `sales_by_product_category` | Database aggregates for the ranked top five and category sales distribution. |
| `backend/core/modules/reports/dashboard_periods.py` | 15 import; 237 summaries; 264 marketplace response | Use the selected-period qualifying orders for both summaries and return `top_products`. |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 10 Top 5 title; 20 category-sales title | Ranked ordered list, requested subtitles, transaction-share labels and honest empty messages. |
| `backend/templates/dashboard/partials/sales_overview.html` | 68 chart container | Preserve the chart footprint; put empty and chart-unavailable messages inside it. |
| `backend/static/components/css/admin_marketplace_overview.css` | 6 grid; 33 placeholder; 44 product list | Align the desktop columns, style product rows, maintain the 260px chart area, keep grouping top-right, and reflow on smaller screens. |
| `backend/static/components/js/admin_dashboard_filter.js` | 126 chart state; 143 ranked products | Refresh the top-five rows, category sales/counts/shares and canvas state without removing the section/container. |
| `backend/static/components/js/admin_sales_overview.js` | 35 sales state; 37 visibility | Toggle the canvas itself for the global page, keeping its container visible even without data or Chart.js. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 stylesheet; 592 scripts | Update asset versions to `20261004-marketplace-ranking`. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 21 `DashboardMarketplaceTests` | Selected-period ranking, category semantics, workflow exclusions, performance and persistent-layout tests. |

Local QA helpers added: `scratch/dashboard-global-review/check-ranking.cjs`, `prepare-ranking-visual.cjs`, and `verify-ranking-visual.cjs`. Generated ranking HTML, JSON, DOM measurements and screenshots are isolated review artifacts.

## Changes made / how it works

Sales Overview retains its title, the subtitle “Completed and paid Cash on Pickup orders,” Marketplace Sales, Completed Orders and Average Order Value. Values remain prominent and bold; the Daily/Weekly/Monthly selector stays at the top-right, including narrow screens.

Sales Trend retains its divider, title, subtitle and 260px chart container at all times. Without qualifying sales, that area shows the requested two messages and View Orders. With sales, it shows the real chart. While loading, the same area shows a skeleton. If Chart.js is unavailable, the footprint remains with an explanatory message, real summary values and the chart data table.

Top 5 Best-Selling Products uses an ordered list showing rank, product name, total units sold and total sales amount. Only available qualifying products are shown; fewer than five does not create placeholder products. The empty card says “No completed product sales yet.”

Sales by Product Categories shows category name, completed paid transaction count, share and a navy horizontal bar. The requested subtitle remains “Distribution of completed sales by category.” A small “Share of completed paid orders” label makes the denominator explicit. The empty card says “No category sales data yet.”

Desktop sales and right-column outer edges align. Below 960px of section width, the two summary cards move below sales in a row; below 560px they stack. Existing navy, gold, white, flat borders and consistent padding/radius are preserved.

## Backend / API behavior

The existing Django `/api/admin/dashboard/` endpoint and server-side Super Admin authorization are reused. Only `MarketplaceOrder.status='completed'` and `payment_status='paid'` qualify. Pending, processing, ready-for-pickup, cancelled and unpaid transactions are excluded from every sales summary.

- Marketplace Sales remains `Sum(total_price)` over qualifying selected-period transactions.
- Completed Orders remains the qualifying row count.
- Average Order Value remains sales divided by that count, or zero when the count is zero.
- Top five groups by parent Product ID, sums quantity and sales, sorts by quantity descending, then revenue descending, and limits to five. Variants and renamed products combine under their parent. Current product name/image metadata uses the same aggregate join, avoiding a query per product. Historical deleted-product names remain available without pretending the product still exists.
- Category performance groups the same qualifying selected-period orders. It uses the category recorded on the transaction, falling back to the surviving Product category for older blank snapshots and then Uncategorized. `Count(pk)` supplies each sales count; `Sum(quantity)` and `Sum(total_price)` are also returned. Percentage is category completed paid count divided by the total qualifying count, rounded to one decimal.

The response adds `marketplace.top_products`. The existing `top_selling_product` field remains an alias of the first ranked row for compatibility. `product_categories` now explicitly returns `is_snapshot: false`, `kind: completed_paid_category_sales`, and `share_basis: completed_paid_order_count`. This intentional meaning change follows the new request.

Both summaries follow the global Today/Last 7 Days/Last 30 Days/This Month/This Year/Custom Range selection. Daily/Weekly/Monthly changes chart grouping while preserving the selected date range, sales totals and rankings. Existing comparison-period rules remain unchanged.

## Database / migration impact

No database schema changes or migrations. No production records, inventory, payment state or order lifecycle were modified. FastAPI remains dedicated to chat.

## Tests performed

- 75 backend tests passed across dashboard periods, health, sales overview, marketplace summaries and dedicated domain dashboards. Django system checks found no issues.
- Tests cover top-five limits, quantity/revenue ranking, parent variants/renames, workflow exclusions, category historical snapshots and archived products, deleted-product/blank-category fallbacks, all six date presets with all three groupings, and zero/empty layout behavior.
- Product ranking and category performance use one query each, both empty and after adding 30 transactions. The existing dashboard query-count regression passes.
- JavaScript syntax checks and CSS parsing passed. DOM integration verifies five ranked rows, category counts/shares, preserved chart layout, top-right grouping requests, authentication parameters, empty-to-populated transitions, loading skeletons, failure retention/Retry, safe product/category text and missing Chart.js.
- Existing global-controls, Attention Required and System Status frontend checks passed.
- Headless Chrome verified actual templates/CSS/chart code and Chart.js in desktop, a 950px laptop content frame and a 390px narrow frame. Populated, empty and loading states retain the 260px chart area. Measurements confirm desktop edge alignment, responsive columns, top-right grouping, fitting values/tooltips and no horizontal overflow.
- The optional design detector returned no regex findings but reported degraded parser support. Browser measurements and screenshots provide the layout evidence.

## Manual test steps

1. Hard refresh the Super Admin Dashboard to load the updated assets. Verify all section titles, subtitles and the top-right grouping selector.
2. Select a date range without completed paid orders. Sales Trend and its framed chart area must remain, with both requested messages. Both right-hand cards should show their empty messages.
3. Select a range with qualifying transactions. Verify sales/count/average, ranked product quantities and sales amounts, and category counts/shares. A product’s variants should combine under one parent.
4. Change the global date range; both rankings and category performance should recalculate. Switch Daily/Weekly/Monthly; chart buckets should change while summaries stay consistent for that range.
5. Verify pending, ready-for-pickup, cancelled and unpaid orders do not contribute.
6. Inspect loading and simulate a network failure. Existing values should remain after failure and Retry should recover. Without Chart.js, keep the chart footprint and real data table.
7. Resize the page to confirm aligned desktop edges and stacked narrow-screen cards.

## Remaining limitations

The existing model represents one sellable-product transaction per MarketplaceOrder row; counts and averages retain that meaning. Category percentages represent transaction share, not revenue or unit share. Rounded shares can total slightly above/below 100%.

Old blank category snapshots can only fall back to the current surviving product category; a deleted product with no category snapshot becomes Uncategorized. Deleted products with identical historical names cannot be distinguished without surviving parent identifiers.

Browser QA used isolated test records and available font fallbacks, not an authenticated live browser session against the user’s database. The application retains its configured Montserrat font request. No demonstration records were added to the live system.
