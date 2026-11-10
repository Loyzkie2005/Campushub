# Marketplace Analytics: ranked products, category sales and persistent chart layout

## Current: Compact three-column Top-Selling Products table - November 10, 2026

### 1. Cause / reason

The actual Super Admin component used a Chart.js canvas for populated rankings and a trophy empty state when no eligible sales existed. The latest request replaces that chart with a compact native **Rank | Product | Units Sold** table. Inspection confirmed that the existing `top_selling_products()` provider already returns at most five real, selected-period products in the correct order. No sales or ranking calculation needed correction.

This section supersedes the historical chart/keyboard-chart/description-list presentation below only for this card. The independent card placement, heading/subtitle, Marketplace width, global date/refresh/error/Retry workflow and every other dashboard component remain unchanged. Previously uncommitted work is preserved and excluded from this feature's commit.

### 2. Exact files changed / current lines and anchors

| File and current line | Anchor / targeted change |
| --- | --- |
| `backend/templates/dashboard/partials/super_marketplace_products.html:5` | Existing `data-products-content` wraps the native `topSellingProductsTable`: three column headers, native row headers, ranks and actual units; cap initial rows at five. Add existing bag-icon/photo thumbnails and focusable full-name text. Remove only the ranking canvas and its redundant chart-error/description-list fallback. Existing JSON, empty copy/trophy, load-error/Retry and live-region hooks remain. |
| `backend/static/components/css/admin_top_products.css:2` | New card-scoped stylesheet: white table, 38px/36px proportional photos, roughly 51–53px rows, thin separators, aligned tabular counts and safe truncated names that expand on focus. Empty-area rule at `:38` keeps the trophy/copy centered on white with a 160px minimum; narrow viewports can grow naturally for readable text. |
| `backend/static/components/js/admin_marketplace_products_chart.js:14`, `:24`, `:67` | Keep the existing asset path/event entry point while replacing chart drawing with authenticated image loading, safe native DOM row rendering and the existing global refresh/error events. Preserve Retry in the existing controller. No Chart.js dependency for rankings. |
| `backend/templates/dashboard/pages/admin_dashboard.html:31`, `:625` | Load the new scoped stylesheet after existing dashboard styles; change only the ranking script version to `20261110-top-products-table`. Earlier unrelated asset versions remain as found in the workspace. |
| `backend/core/modules/reports/tests/test_dashboard_marketplace.py:70`, `:131`, `:311`, `:420` | Add actual isolated-record cases for 0/1/3/7 products, top-five limit, exclusions, selected dates and equal-quantity/revenue deterministic ordering; update only obsolete ranking-chart assertions to the table. Optional ignored QA exports replay actual Django responses. |
| `backend/core/accounts/tests/test_admin_workflows.py:574` | The inherited Super Admin role/template assertion now requires the ranking table instead of the removed canvas. Permission/template-isolation checks are preserved. |
| `docs/dashboard-marketplace-ranked-sales.md:3`, `CAMPUSHUB_CONTEXT.md:3` | Current eight-part report, data flow, verification, troubleshooting and safe exercise. |

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Populated chart with visually shortened axis names | Three-column native table with ranks, photo/name and quantity | Make exact product rankings easier to scan and read accessibly. |
| Chart-specific keyboard/description fallback | Native column/row headers; full DOM names, title tooltip and focus expansion | Preserve access to complete names without depending on canvas or adding a visible column. |
| Shared compact message with no reserved area | White, borderless, centered trophy/title/description with a 160px minimum | Match the requested empty-state size without a gray inner panel. |

There are no progress bars, percentages, added metrics, rank badges or new actions. Ordinary row height is about 51–53px. Full long names are available to screen readers and expand when focused by keyboard/touch; that focused row can become taller as needed. The Units Sold heading may wrap on a narrow phone, while all three columns remain aligned without scrolling.

### 4. How it works / functions, inputs, outputs and data flow

Unchanged selected-date/paid-completed order eligibility feeds `dashboard_marketplace.top_selling_products(orders, limit=5)`. That function groups surviving product variants under the parent ID and retains existing historical fallbacks. Its deterministic ordering is descending `units_sold`, descending `sales_sum`, then `product_identity`. Revenue remains an internal tie-breaker; it is not displayed as another column. Existing initial Django context and dashboard GET JSON expose the same `marketplace.top_products` fields.

The partial initially renders those records into the table, including real `product_name`, `units_sold` and existing `image_url`. Rank is its returned position. A missing/deleted photo retains the shared bag SVG. `loadImage(image)` adds the existing tab token only to a same-origin image URL, loads the existing image endpoint and hides a failed image so the underlying placeholder remains. It never alters a product or order.

The unchanged global controller's `campushub:dashboard-data` event passes the selected-period response to `render(products)`. That function takes at most five records, builds cells with `textContent` (rather than interpreting names as HTML), formats integer quantities and replaces only this table's rows. It toggles the existing content/empty/error hooks and updates the existing invisible live announcement. Failed dashboard requests hide stale rows/empty content and reveal the existing error/Retry. No new fetch endpoint, global filter calculation or listener was added outside this component.

Annotated example: `products.slice(0, 5)` limits the displayed records without creating missing rows. For a response containing three eligible products, `render` creates three `<tr>` elements; an empty response creates none and shows the exact trophy empty state. Initial Django rows use the same five-item limit and remain readable if JavaScript is disabled. Existing `admin_marketplace_products_chart.js` keeps its filename to avoid unnecessary asset-path changes, but no longer creates a ranking chart.

### 5. Backend / API behavior

Unchanged provider, query counts, product identity, eligibility, sales/quantity aggregation, date range, deterministic secondary sorting, endpoint, permissions and image route. No fake/synthetic sales, fabricated image assets or extra products. The Super Admin card's display changes only; Marketplace Admin's separate ranking component is untouched. Sales Summary/Trend, Bundles, Inventory, Recent Orders, Facilities and Services files were protected against accidental changes during this task.

### 6. Database / migration impact

None. No database settings, production/application records, models, migrations or dependencies changed. New fixtures exist only in the guarded, unique disposable localhost PostgreSQL test database; that database was destroyed. Browser verification replayed those actual page/API/image exports and made only GET requests. Ignored exports, logs and screenshots are not part of the feature commit.

### 7. Tests performed / actual results

- **79 existing/new Django tests ran in 22.766s: 78 passed, one pre-existing unrelated assertion failed; no errors.** Command: `backend/core/venv/Scripts/python.exe -B scratch/test-organization-20261109/run_local_tests.py modules.reports.tests.test_dashboard_marketplace modules.reports.tests.test_dashboard_periods modules.reports.tests.test_dashboard_executive`. All table/ranking/image/exclusion/date/permission/role-isolation tests passed. The only failure is `GlobalDashboardTests.test_global_dashboard_markup_and_review_artifact`, which expects six `vs yesterday` occurrences but the earlier Booking comparison title produces a seventh. It was left unchanged to respect this task's scope. The first fixture run also caught an overlong test-only name; it was shortened to fit the existing 150-character schema, with no model/database change.
- **One isolated baseline audit passed in 0.499s**, rendering the saved original ranking component with the otherwise untouched workspace. It confirmed the original canvas and the same seven comparison occurrences. This proves the outstanding assertion predates the table change. Both local test databases were destroyed. Reports: `scratch/test-organization-20261109/top-products-table-results.json` and `top-products-baseline-audit-results.json`.
- **1,368 headless Chrome checks passed** using actual Chart.js 4.4.1 for surrounding charts. Seven widths (1440/1280/1024/768/390/320/280px), 0/1/3/7 eligible products, exact top-five names/units/ranks, existing trophy/copy, real image response/missing and failed-photo fallback, native three-column headers/row headers, compact rows/thumbnails, full-name focus expansion, actual date filtering, Refresh, error/Retry, populated-to-empty, no Chart.js ranking dependency and server-rendered rows without JavaScript. No uncaught JS/unexpected console errors, overlap or horizontal scrolling/overflow. Two expected resource errors came from deliberately failed photo/HTTP requests. No mutating requests. Command: `node scratch/top-products-table-20261110/review.cjs`.
- Empty area measured 160px at ordinary widths, growing to189.19px at the narrowest stress width for readable copy. Desktop/mobile populated and empty screenshots were visually inspected. Baseline comparisons preserved the card width and other cards' markup/dimensions/styles (apart from natural vertical flow caused by this card's changed height). Twelve protected source hashes remained unchanged, including ranking provider/views/date calculations, global filter, Sales/Booking renderers/styles, Attention, Bundles and executive layout. JavaScript syntax and scoped whitespace checks passed.

### 8. Remaining limitations / troubleshooting / safe practice

One unrelated comparison-count assertion remains as documented above; no ranking/UI test failure remains. Chart-library errors elsewhere cannot prevent this native table from displaying. Empty/focused-name rows may grow on very narrow screens to preserve essential text. Physical-device and deployed production-account checks were not performed. Commit/push is scoped to this feature; earlier unrelated uncommitted changes remain in the workspace. The final implementation reply records the actual commit/push result.

If the old chart remains, hard-refresh and confirm both ranking assets use `v=20261110-top-products-table`; check that the new CSS is collected during deployment. If a photo fails, inspect the existing image endpoint/session and confirm the bag placeholder remains; do not fabricate replacement images. If rankings are empty, compare `marketplace.top_products` in the existing dashboard GET response and verify selected dates and actual eligibility rather than adding sales.

Safe exercise: select an existing period with eligible products, compare the first row's name/units with the dashboard GET JSON and focus a truncated name to reveal it. Select an empty historical period and confirm no rows are shown and the exact trophy empty state returns. Resize to390px and confirm all three columns fit. Temporarily block one image request in developer tools, Refresh and confirm its existing placeholder appears while the name/count remain. Restore network conditions and reload. Do not create, edit or pay real orders to test styling.

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
