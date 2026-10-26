# Marketplace Analytics: larger donut and stable cards

Updated 2026-10-05. This supersedes the 120–140px donut sizing in `marketplace-right-stack.md`.

## 1. Cause / Reason

The category donut was capped at 120px beside its table, so it looked small. The right-hand cards also relied on their content to determine height: an empty message took less space than five products and six category rows. Switching between empty real data and the sample could therefore change both card heights and the Sales Overview height.

## 2. Exact Files Changed

Current line numbers are navigation aids; use the nearby code anchors if later edits move them.

| Folder / file | Current line / nearby anchor | Change and reason |
| --- | --- | --- |
| `backend/static/components/css/admin_marketplace_overview.css` | 10, `.dashboard-marketplace-side` | Changed the right column to a 380px product row and a category row of at least 320px. Added a named size container for responsive rules. |
| Same CSS file | 66, `.sales-overview__empty[hidden]` | Added invisible reserved space for the no-sales message, keeping the desktop graph area stable when that message disappears. |
| Same CSS file | 196, `.dashboard-top-selling`; 197, `.marketplace-product-list` | Made long product lists scroll within the reserved card body. Hid scrollbar tracks and added a visible keyboard focus outline. |
| Same CSS file | 207, `--category-donut-size`; 210, `.marketplace-category-content` | Enlarged the normal donut to 180px, used a 16px gap, and kept the chart and list within one card. |
| Same CSS file | 214, `.marketplace-category-total` | Increased the center label to 12px and the total to 18px for easier reading. |
| Same CSS file | 259, `@container marketplace (max-width: 959px)` | Removed the automatic row-height reset so the right cards retain their reserved sizes when the page stacks. |
| Same CSS file | 276, `@container marketplace-side`; 279, `@container category-sales` | Narrow cards reserve at least 480px and place the 180px donut above the list. At 440px or more of category content width, the donut becomes 200px beside the list. |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 14, `data-marketplace-products` | Added `tabindex="0"` and a scrolling description so keyboard users can reach and scroll the product list. No cards moved. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18, stylesheet URL | Updated the CSS cache version so a reload fetches the new sizing rules. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 16, `stableRightCards`; 61, `window.qaBaseline` | Added baseline measurements of empty cards before switching sample mode, then compared their heights and positions afterward. |
| `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs` | 17, `stableRightCards`; 22, `donutWidth` | Added assertions for stable right cards, stable desktop Sales Overview height, and enlarged donut sizing. |
| `CAMPUSHUB_CONTEXT.md` | 17, current marketplace height preference | Updated the remembered sizing and scrolling behavior. |
| `docs/marketplace-right-stack.md` | 3, current sizing update | Linked this current report; retained earlier reports as history. |
| This document | 1 | Added the beginner-friendly implementation report. Existing scratch previews and screenshots were regenerated. |

## 3. Changes Made

Enlarged the donut and its center text, reserved consistent space for empty and populated right cards, and made overflowing product rows scroll inside the card. Kept the existing Sales Overview on the left and the product/category stack on the right. No analytics sections or data were removed. No new records or sample values were added.

## 4. How It Works

CSS Grid reserves the card heights before data arrives. The category chart uses the same existing SVG segments and backend-calculated shares; CSS changes only its display size. The named container queries respond to each card's actual width rather than assuming the browser width equals the card width. On desktop, Sales Overview stretches to the combined right-column height. When there are sales, the hidden empty-message space is invisible but still occupies its layout area.

To test: open the Super Admin dashboard and press Ctrl+F5. Click **Show sample**, inspect the larger donut and total, then click **Use real data**. The right cards should keep their heights even when real data is empty. Test Daily, Weekly and Monthly; narrow the browser to see the donut above its list. Scroll the product list with the mouse wheel or focus it with Tab and use arrow/Page Down keys.

The UI/UX skill's targeted layout-shift searches returned general font-loading guidance rather than a dashboard-card recipe. The reserved-space implementation follows the existing dashboard layout and CSS inspection.

## 5. Backend / API Behavior

Unchanged. Real analytics still use completed, paid Cash on Pickup orders. Existing local sample mode, period grouping, refresh and real-data restoration continue to work. No business logic was moved or changed.

## 6. Database / Migration Impact

No production database writes and no schema migrations. The Django verification fixture runs in the isolated test database.

## 7. Tests Performed

- One existing targeted Django test passed: `DashboardMarketplaceTests.test_sales_overview_system_preview_values_and_grouping`. Django system checks reported no issues.
- Existing sample integration checks passed: values, all three grouping options, five product ranks, six category rows, real-node restoration, refresh/error recovery and unchanged unrelated dashboard metrics.
- Seven actual headless Chrome preview scenarios passed: Daily, Weekly, Monthly, return to real data, refresh, mobile and narrow width. Checks include card sizing, ordering, no horizontal overflow, chart keyboard inspection, matching donut/legend colors, sample values and no JavaScript errors.
- Desktop sample and empty views both measured Sales Overview and the combined right column at 716px. Right-card height/relative-position checks passed in every scenario. The visible donut measured 180px in the inspected previews.
- CSS parsing passed. Desktop sample/empty and narrow screenshots were visually reviewed.

Preview: `../scratch/sales-overview-system-test/in-dashboard-daily.png`. Empty view: `../scratch/sales-overview-system-test/in-dashboard-return.png`.

## 8. Remaining Limitations

Long product lists may require scrolling, especially on narrow screens; their scrollbars remain hidden by the user's preference. Long category names can truncate visually, with full text retained in the DOM/title. Exact percentages stay in the list rather than inside the ring. Empty category data keeps its honest message and reserved card space; it does not display a fabricated donut. Mobile Sales Overview can still grow naturally when text wraps, while the right cards retain their reserved sizes. Verification used the actual templates/scripts in an isolated browser preview rather than a signed-in production browser session.
