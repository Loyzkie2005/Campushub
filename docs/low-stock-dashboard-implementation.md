# Low Stock Products dashboard card

Implemented on 2026-10-05 for the Super Admin dashboard.

The previous card displayed product-level totals, up to six unsorted rows, a blank Category column, and an unfiltered Products link. It did not refresh with the dashboard API. The replacement shows up to five actual inventory entries with Product, Available, and Threshold columns, plus real navigation and explicit loading/error states.

## Files and code anchors

Line numbers refer to this implementation; use the anchor if later edits move them.

| Folder/file | Line | Anchor | What changed and why |
|---|---:|---|---|
| `backend/core/modules/marketplace/services/inventory.py` | 81 | `flatten_customization_inventory` | Keeps option names, groups and JSON positions beside the existing normalized stock/expiry values. Existing stock calculations remain intact. |
| `backend/core/modules/marketplace/services/inventory.py` | 108 | `iter_product_low_stock` | Shared classifier for individual low-stock inventory entries, including variants. Reuses existing stock, threshold and expiry helpers. |
| `backend/core/modules/marketplace/services/inventory.py` | 127 | `low_stock_inventory_rows` | Two-query shortlist with simple products filtered/limited in SQL and JSON options streamed. Keeps at most five candidate entries in memory while ranking. |
| `backend/core/modules/reports/dashboard_low_stock.py` | 14 | `build_low_stock_card` | New presentation adapter: serializes five entries, real image/detail URLs and the existing filtered Inventory URL. Database errors produce an explicit error state. |
| `backend/core/modules/reports/dashboard_periods.py` | 253 | `low_stock` response key | Extends the existing dashboard response with current inventory data. Reporting dates do not alter stock. |
| `backend/core/modules/reports/views.py` | 1105 | `low_stock_count` | Global dashboard reuses its existing attention count rather than running another legacy classification loop. |
| `backend/core/modules/reports/views.py` | 1342 | `low_stock_products` | Old product-total card loop runs only for legacy/non-global dashboards. Super Admin uses the new shared service. |
| `backend/core/modules/reports/views.py` | 1571 | `dashboard_low_stock` | Passes the exact API snapshot to the initial server-rendered dashboard. |
| `backend/templates/dashboard/partials/low_stock_card.html` | 1 | `data-low-stock-card` | New compact card partial with actual thumbnails when present, variant labels, scoped table headers, empty/loading/error states and Retry. No fake thumbnails or product rows. |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 25 | `low_stock_card.html` | Super Admin stock card now belongs directly below Top Selling Products in the right Marketplace column. Categories/Recent Orders stay in their 50/50 row below. `admin_dashboard.html` retains the old location only for legacy/non-global dashboards. |
| `backend/static/components/css/admin_dashboard_filter.css` | 91 | `[data-low-stock-card]` | Scoped compact table, navy values, light header surface, keyboard focus, skeleton and error styles. No red stock values. |
| `backend/static/components/js/admin_dashboard_filter.js` | 120 | `renderLowStock` | Replaces rows when the existing dashboard refresh/filter succeeds. Uses safe text nodes and preserves tab authentication on detail, filter and image links. |
| `backend/static/components/js/admin_dashboard_filter.js` | 414 | `lowStockRetry` | Retry reloads the existing dashboard endpoint. Fetch failure hides healthy content and shows the explicit inventory error. |
| `backend/core/accounts/views.py` | 192 | `admin_has_low_stock` | Existing Products/Inventory page and its Low Stock count recognize any positive low option without changing the product's overall status. Reuses the shared classifier. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 147 | `data-has-low-stock` | Exposes that server-calculated flag to the existing filter. Updates the JS asset version at line 987. |
| `backend/static/components/js/admin_products.js` | 1643 | `lowStockItems` | Dynamically rendered product rows also derive the flag using existing JavaScript inventory helpers. |
| `backend/static/components/js/admin_products.js` | 2181 | `row.dataset.hasLowStock` | New-product Low Stock count includes low variants. |
| `backend/static/components/js/admin_products.js` | 2528 | `matchInventory` | Low Stock filter includes products with low options, even when their parent status is broader. Other filters retain their existing behavior. |
| `backend/core/modules/reports/test_dashboard_low_stock.py` | 20 | `DashboardLowStockTests` | New real-database tests for boundaries, stock adjustment, variants, archived/expired exclusion, ranking, queries, navigation, errors, refresh and RBAC. |
| `scratch/dashboard-global-review/check-low-stock.cjs` | 1 | DOM checks | Verifies real template/API fixture integration, loading/error/Retry, safe labels, tab authentication, broken images and existing Inventory filter behavior. |
| `scratch/dashboard-global-review/prepare-low-stock-visual.cjs` | 1 | review preparation | Uses actual Django-rendered fixture HTML and project CSS for isolated visual previews. |
| `scratch/dashboard-global-review/render-low-stock.ps1` | 1 | Chrome cases | Renders desktop, mobile, 375px, empty, loading and error previews. |
| `scratch/dashboard-global-review/verify-low-stock-visual.cjs` | 1 | browser assertions | Checks card/cell fitting, navy quantities and state visibility. |
| `docs/low-stock-dashboard-implementation.md` | 1 | this guide | Records the reason, exact edits, data behavior, testing and limitations for learning. |

## How inventory works

The real model is `api.models.Product`. Variants are JSON options on that model, not separate ProductVariant or Inventory records. No InventoryMovement or OrderItem model exists in this checkout. Marketplace orders use `MarketplaceOrder`.

The existing order placement path calls `adjust_product_stock` before saving the order, marking `inventory_deducted=True`. Stored simple/option stock already represents available inventory. For example, 10 available minus an order for 7 leaves stored stock 3. The card reads 3; it does not subtract the same reservation a second time. Restoration uses the same existing inventory service.

The threshold source is the existing `CAMPUSHUB_LOW_STOCK_THRESHOLD` setting in `backend/core/core/settings.py`, line 241. It is currently 5. There is no per-seller, product or variant threshold field, so this implementation adds none. Test overrides exercise threshold 20 without changing the live setting.

Low stock means `0 < available <= threshold`, with the existing perishable-expiry rules applied. Zero stock and expired perishable entries are excluded. Archived products are excluded. Approval filtering remains consistent with the existing Inventory page, which can monitor active products across approval states.

Variants appear separately, e.g. Campus Hoodie with `Size: Medium` underneath. Their JSON position is exposed as `variant_key`; it is not a fabricated database variant ID. A healthy Large option and a zero-stock Small option do not get merged into Medium's quantity. The parent product's existing status priority remains unchanged; the Low Stock filter can still find a low option even if the parent's overall status is Out of Stock.

Rows sort by available/threshold ratio, then available quantity, product ID and option position for deterministic ties. Since all entries currently share the same threshold, this is equivalent to lowest available first. The result is capped at five rows, not padded to five.

Simple products are filtered and limited in SQL. JSON-option products are streamed with required fields only. Ranking individual options requires inspecting their JSON because the current schema has no separate variant table; query count stays at two and there are no seller or order lookups per row.

## Backend/API and navigation

The existing `/api/admin/dashboard/` endpoint now includes `low_stock: {state, products, view_all_url}`. Existing Super Admin authentication/authorization stays enforced. No new endpoint, page, permission or stock-editing action was added.

Inventory remains a current snapshot when Today, Last 30 Days or other reporting periods are selected. Refresh reads current database quantities again. A service failure gives `state: error`; an entire dashboard request failure also gives the card an error with Retry. Neither becomes a healthy empty state.

View All opens the actual existing route: `/admin-products/?inventory_status=low_stock`. This repository's Inventory sidebar already points to the Products module. Its Low Stock filter is activated automatically and now includes products with low variants.

A product link opens `/admin-products/?product_id=<actual ID>`, using the existing product details view and its inventory/variant information. It opens the product, not a newly invented variant detail page. Existing permissions govern the target page. Tab-specific authentication is preserved on refreshed links/images.

## Database and migration impact

None. No models, fields, migrations or live stock records were changed. The sample records used in tests and screenshots exist only in the isolated Django test database.

## Tests performed

- Broad Django run: 87 tests, 86 passed. All dashboard/low-stock tests passed. The one failure is the existing `MarketplaceAdminProductAccessTests.test_listing_owner_shows_only_approved_sellers`, expecting `label="Approved Sellers"` in a template which does not contain that label. Reproduced with this task's product-template changes removed in memory to confirm it is pre-existing. That unrelated owner-picker issue was left unchanged.
- Low-stock DOM integration passed: five rows, actual links/filter, authentication, loading/empty/error/Retry, safe product text, variant labels and image failure handling.
- Existing dashboard control and marketplace-ranking DOM checks passed, including grouping/filter races, failure rollback and charts.
- Six Chrome visual cases passed: desktop, mobile, 375px, empty, loading, error. Inspected the compact desktop rendering. Screenshot records are test fixtures, not actual marketplace metrics.
- Complete-dashboard desktop and mobile Chrome checks also passed: no JavaScript errors, page overflow or regressions to the reduced palette.
- JavaScript syntax checks and targeted whitespace checks passed.

## Manual verification

Use a development/test database for stock changes. The live threshold remains 5.

1. Create active products with available stock 4, 5, 6 and 0. Refresh Dashboard. Only 4 and 5 should appear. Test setting override 20 verifies 10/20 appear and 21/0 do not.
2. Place a normal test order for 7 units from stock 10. Existing order reservation leaves stock 3. Refresh: the card must show 3. Cancel/restore through the existing workflow: the card should no longer show the product after stock returns to 10.
3. Create Medium 2, Large 20, Small 0 options. Only Medium appears. View All must still include the parent product, whose details show its options.
4. Archive a low product or give perishable inventory a past expiry. Refresh: it must disappear.
5. Create more than five low entries. Confirm only the five lowest quantities are shown, with stable ties.
6. Click View All: confirm Low Stock is active. Click a product: confirm its actual details/inventory opens. Normal non-low entries remain excluded from the filter.
7. Restock all active low entries. Refresh: no fake rows; the healthy empty text appears.
8. Throttle the dashboard request in browser developer tools, then refresh. Confirm a skeleton, not a temporary zero/healthy state.
9. Block `/api/admin/dashboard/`, then refresh. Confirm the inventory error and Retry. Unblock and click Retry: current rows return.
10. Select different reporting periods: stock stays current; sales analytics continue to follow the selected period.
11. Verify unauthenticated dashboard API access gives 401 and non-Super Admin accounts give 403. This monitoring card grants no restock permissions.

## Remaining limitations

- No actual bundle product/component model or component-derived stock service exists in the current checkout. Therefore bundle availability cannot honestly be calculated or tested here. No fake independent bundle stock was introduced. A future bundle implementation must expose canonical component-derived availability through the Inventory service before this card can monitor it.
- The shared setting is the only threshold source. Seller-specific thresholds need a separately scoped schema/workflow change.
- View All uses the existing Products/Inventory page and client-side filter; no separate Inventory page was created.
- JSON options require a streamed scan of option-bearing products. A future normalized variant table could support fully database-ranked option queries.
- The attention widget retains its existing product-level status counts; this card ranks individual low entries, so the two counts need not equal.
- If the entire Django page cannot load, no server-rendered card can appear. Once the dashboard is rendered, refresh failures show the card's explicit error state.
- The existing owner-picker label test above still fails and is outside this change.
