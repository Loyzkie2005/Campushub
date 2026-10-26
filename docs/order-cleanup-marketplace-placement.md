# Marketplace order cleanup and dashboard placement

Completed on 2026-10-05 at the user's explicit request to clear all marketplace orders and move Low Stock Products into Marketplace.

Later layout update: Low Stock Products now sits below Top Selling Products in the right column, eliminating the separate inventory row. See [the latest placement guide](low-stock-side-placement.md). The database-cleanup record below remains unchanged.

## Cause and result

The Super Admin stock card was still included in the bottom dashboard row after Facilities Analytics. Recent Orders was inside a 50/50 row, but its old 720px minimum table width exceeded its card and clipped the visible right-hand columns. Card headings also had different padding and font sizes.

Low Stock Products is now inside Marketplace Analytics, below the equal-width categories/orders row. The Recent Orders card shares the category card's 24px padding and heading size. Its columns fit desktop cards; narrow populated tables can scroll inside a keyboard-accessible region. Empty tables fit their cards without forced scrolling. Pending Approvals uses the full former bottom row on the Super Admin dashboard.

## Exact files and anchors

| Folder/file | Line | Nearby anchor | Added/changed/moved/removed |
|---|---:|---|---|
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 30 | `marketplace-inventory-row` | Moved the existing Low Stock Products partial into Marketplace, with a single `lowStockSlot`. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 | marketplace stylesheet | Changed its version so browsers load the alignment changes. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 408 | Pending approvals row | Removed the global stock card from the bottom row; expanded Pending Approvals to fill that row. The legacy/non-global card remains conditional at line 472. |
| `backend/templates/dashboard/partials/recent_orders.html` | 6 | `recent-orders-table-wrap` | Added keyboard scrolling, an accessible table caption, column scopes and a six-column sizing group. Data still comes from the same real order queryset. |
| `backend/static/components/css/admin_marketplace_overview.css` | 98 | `dash-card-recent-orders` | Matches card padding/title alignment; replaces the global card's fixed table minimum with proportional columns and safe wrapping. Removes the old pill minimum width so labels fit medium layouts. |
| `backend/static/components/css/admin_marketplace_overview.css` | 118 | `marketplace-inventory-row` | Places the compact stock card in the left half on wide layouts and stacks it full width on narrow layouts. Categories and Recent Orders remain 50/50. |
| `backend/core/modules/reports/test_dashboard_low_stock.py` | 151 | `test_empty_and_populated_markup_and_review_artifacts` | Checks the card appears once and before Facilities Analytics. |
| `scratch/dashboard-global-review/prepare-ranking-visual.cjs` | 1 | browser measurements | Adds table-cell fitting, heading alignment and Marketplace stock-card placement checks. |
| `scratch/dashboard-global-review/verify-ranking-visual.cjs` | 1 | browser assertions | Verifies equal columns, aligned headings, fitting order cells and exactly one stock card inside Marketplace across nine cases. |
| `CAMPUSHUB_CONTEXT.md` | 11 | Current dashboard placement | Saves the accepted Marketplace placement for future work. |
| `docs/low-stock-dashboard-implementation.md` | 22 | file/anchor table | Updates the previous guide to point to the card's new Marketplace include. |
| `docs/order-cleanup-marketplace-placement.md` | 1 | this guide | Explains the reset, UI edits, verification and limitations. |
| `scratch/private-order-reset/clear_marketplace_orders.py` | 21 | `reset_orders` | Local, Git-ignored one-time maintenance script; dry-run default and explicit apply operation. No destructive web endpoint was added. |
| `scratch/private-order-reset/.gitignore` | 1 | `*` | Keeps recovery data and the maintenance script out of Git. |

## Database cleanup and stock handling

The inspected PostgreSQL database is `campushub`. Before the reset it contained four `MarketplaceOrder` records and three `MarketplaceOrderStatusHistory` records. The history model is the only reverse relation cascading from orders in the current schema.

The cleanup ran in a database transaction with order writes locked during the snapshot and deletion. A recovery JSON was written and flushed before any mutation. Two pending orders had `inventory_deducted=True` and `inventory_restored=False`. Their two reserved units were returned through the existing `adjust_product_stock(..., restore=True)` helper, using their recorded customization selections. Orders without deducted inventory were not restocked. Completed orders would not be restocked.

Result: **0 marketplace orders and 0 order status-history records**. Three products, one facility and zero facility bookings remained. No users, products, facilities or bookings were deleted. No stock quantities were invented.

The apply recovery snapshot is stored privately at:

`scratch/private-order-reset/marketplace-orders-apply-20261005-071330-044472.json`

It includes the deleted orders/history and the two affected products before stock restoration. A dry-run snapshot was also saved. These contain application records and are ignored by Git. They were not published or committed. Restoring them later must be treated as a separate requested operation; blindly importing old product snapshots could overwrite newer inventory changes.

## Backend/API behavior

No endpoint, model, migration, authentication rule or stock-editing permission was changed. Existing Orders queries and API responses now read the empty order table. Existing dashboard analytics naturally return zero orders/revenue and honest empty states. Low Stock Products still uses its shared inventory service and current stock snapshot.

The stock card was moved in templates; it was not duplicated. Normal product detail/filter links continue to use the existing Products/Inventory module. Product-interaction records and other independent audit records were not deleted as order rows.

## Verification

- Rehearsed the cleanup inside a rolled-back transaction, confirming exactly four orders, three history rows and two restored units.
- Applied the reset, then verified committed counts with fresh reads from `campushub`.
- Rendered the real Super Admin dashboard and Orders page using an existing admin user without creating accounts or new records: both returned HTTP 200. Dashboard/API order count and revenue were zero; Recent Orders showed its empty state. Two real low-stock entries remained.
- All 63 dashboard/marketplace/low-stock Django tests passed. The new card placement assertion was then run and passed.
- All nine Chrome analytics cases passed after checking the medium-width status-pill fit: desktop, empty desktop, laptop, medium, mobile, 375px mobile, empty mobile, loading and error.
- Complete dashboard desktop/mobile checks passed with no JavaScript errors or page overflow.
- Existing dashboard controls, ranking and low-stock DOM integration checks passed.
- Targeted whitespace checks passed; the maintenance script/recovery folder was verified as Git-ignored.

Browser test screenshots use isolated fixture records, so their populated sales numbers are not the cleared live database.

## Manual check and limitations

Reload Dashboard and Orders. Orders should be empty. Confirm categories and Recent Orders remain equal width; Low Stock Products should appear below them, before Facilities Analytics. View All should still open the existing Low Stock inventory filter.

An already open page can display old HTML until reloaded. New orders placed after this cleanup will appear normally; no permanent suppression or automatic future deletion was added. Small populated tables retain horizontal scrolling inside their cards. This operation removed current marketplace order records, not facility bookings or unrelated interaction/audit records.
