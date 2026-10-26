# Marketplace Analytics: ranked products, category sales and persistent chart layout

Implemented October 4, 2026 for the CampusHub Super Admin Dashboard.

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
