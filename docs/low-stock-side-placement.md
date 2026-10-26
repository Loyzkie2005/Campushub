# Low Stock Products placement update

The separate half-width Low Stock Products row left an unused area to its right. On 2026-10-05 the user approved moving it directly below Top Selling Products, in the right column beside Sales Overview.

## Exact edits

| File | Current line / anchor | Change |
|---|---|---|
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 24, `dashboard-low-stock` | Moved the existing stock-card partial into `.dashboard-marketplace-side`, immediately after Top Selling Products. Removed its former separate `.marketplace-inventory-row`. There is still one `lowStockSlot`. |
| `backend/static/components/css/admin_marketplace_overview.css` | 7, `.dashboard-marketplace-side` | Uses `grid-template-rows: 1fr auto` with a 16px gap. The stock card takes its natural height; Top Selling Products fills the remaining space beside Sales Overview. Removed the obsolete inventory-row layout rules. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18, marketplace stylesheet | Updated the asset version to `20261005-stock-side-stack` so browsers fetch the new CSS. |
| `CAMPUSHUB_CONTEXT.md` | 11, Current dashboard placement | Saves the new accepted position for future work. |
| `scratch/dashboard-global-review/prepare-ranking-visual.cjs` | 40, `lowStockSide` | Measures right-column placement, stock position below Top Selling Products and above Categories, uniqueness and content fitting. |
| `scratch/dashboard-global-review/verify-ranking-visual.cjs` | 22, `lowStockSide` | Checks those conditions across the existing browser cases. |
| `docs/low-stock-dashboard-implementation.md` | 22, file/anchor table | Updates the stock partial's current location and line number. |
| `docs/order-cleanup-marketplace-placement.md` | 5, later layout update | Points the earlier cleanup report to this newer placement guide. |
| `docs/low-stock-side-placement.md` | 1, this guide | Explains the change and its verification. |

`1fr auto` means the first card can fill extra vertical room, while the second card is sized by its content. The natural minimum size of the first row keeps product rows from being compressed out of view. Existing narrow-layout rules stack Sales Overview, Top Selling Products, Low Stock Products, Categories and Recent Orders.

Sales by Product Categories and Recent Orders retain equal 50/50 widths on wide screens. The former isolated inventory row and its empty neighboring area are gone.

## Backend/API and database impact

None. This is a template/CSS placement change. Stock thresholds, inventory calculations, actual data, refresh, View All/detail links, loading/error/Retry behavior and permissions continue to use the same code. No database records were written or deleted, and no migration was added for this task.

## Verification and manual check

- Three existing Django render tests passed: stock-card rendering, marketplace empty-state layout and the global dashboard.
- Nine Chrome analytics cases passed for populated/empty desktop, laptop, medium, mobile, 375px mobile, empty mobile, loading and error states. They verify right-column placement, the preserved 50/50 row and responsive fitting.
- Complete-dashboard desktop/mobile palette checks passed without JavaScript errors or page overflow.
- The desktop empty-sales rendering was visually inspected. Review artifacts use isolated test records rather than live marketplace records.

Reload Dashboard. On desktop, Low Stock Products should sit below Top Selling Products beside Sales Overview. On mobile, it should follow Top Selling Products in the vertical stack. View All, refresh and Retry should behave as before.

## Limitations

Narrow screens intentionally use a single-column stack. Top Selling Products can still contain normal empty-state spacing when there are no sales; the separate unused area beside the former inventory row has been removed.
