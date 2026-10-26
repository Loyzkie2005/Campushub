# Marketplace Analytics: trial right-hand stack

Current sizing update: the donut is now 180–200px and the right cards reserve consistent space between empty and sample states. See [the latest implementation report](marketplace-stable-large-donut.md). The smaller sizes below are historical.

## Latest update: fit the donut in the lower-right card

This update replaces the horizontal-bar category design described in the earlier trial report below.

1. **Cause / Reason:** the user wanted the donut to fit in the existing lower-right category card.
2. **Exact Files Changed:** `backend/static/components/css/admin_marketplace_overview.css:205` (`marketplace-category-content` inside `dashboard-marketplace-side`) and `:271` (`@container category-sales (max-width: 360px)`); `backend/templates/dashboard/partials/category_sales_card.html:31` (category row); `backend/static/components/js/admin_dashboard_filter.js:335` (`heading.append(line)`); `backend/templates/dashboard/pages/admin_dashboard.html:18` and `:563` (cache versions); `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs:20` (`donutVisible`); `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs:17` (donut checks); `CAMPUSHUB_CONTEXT.md:17` (current height/design choice); and this report at line 3. Regenerated the existing scratch previews/test renders/screenshots.
3. **Changes Made:** restored the existing donut at 120px beside the category list, restored matching legend dots, reduced center-label typography, removed the trial category bars from the template, renderer and CSS, and hid tiny percentages inside the ring. Exact percentages and sales amounts remain in the adjacent table. No cards moved in this step.
4. **How It Works:** a two-column CSS Grid uses `120px` for the donut and the remaining width for the category table, with a 12px gap. Below 360px of card-content width, it becomes one column and uses a 140px donut above the list. The existing backend-calculated SVG segments, sample switch and real-data restoration already supply the chart; no new chart library is needed. To check: Ctrl+F5 → Show sample, inspect the lower-right donut/list, then narrow the browser and switch back to real data.
5. **Backend / API Behavior:** unchanged. Category shares, colors, amounts, total sales and real completed/paid Cash on Pickup filtering use the existing calculations.
6. **Database / Migration Impact:** no production writes or migrations.
7. **Tests Performed:** two targeted Django fixture/render tests passed. Sample integration checks and JavaScript syntax passed. Seven actual Chrome scenarios passed, verifying 120–140px donut fit, matching legend/segment colors, populated/empty states, combined desktop heights, mobile order, no horizontal overflow and no JavaScript errors. Desktop and narrow screenshots were visually inspected; CSS parsing passed.
8. **Remaining Limitations:** the compact ring does not contain tiny percentage labels; readable percentages appear in the list. Many categories still scroll and long names can truncate visually, with full names preserved in the text/title. Large totals may wrap in the small donut center. No sample product photos were applied to real product records.

Screenshot: `scratch/sales-overview-system-test/in-dashboard-daily.png`. The current category visualization is the compact donut; earlier horizontal-bar descriptions below are historical.

## 1. Cause / Reason

The user asked to try Sales Overview on the left, with Top Best-Selling Products above Sales by Product Categories on the right. Compact product rows and labeled horizontal bars make the category card fit within that narrower column.

## 2. Exact Files Changed

| Folder / file | Current line / nearby anchor | What changed |
| --- | --- | --- |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 25, include of `category_sales_card.html` | Moved categories inside `dashboard-marketplace-side`, directly after the product card. Removed the separate full-width category wrapper. |
| `backend/templates/dashboard/partials/category_sales_card.html` | 31, category table row | Added a share bar under each category name and a full-name title for long labels. |
| `backend/static/components/js/admin_dashboard_filter.js` | 332–342, category renderer inside `render` | Creates those same bars from actual API/sample `category.chart.share` values and supplies the full-name title. |
| `backend/static/components/css/admin_marketplace_overview.css` | 10, `dashboard-marketplace-side` | The right column contains two grid rows with the existing 16px gap. |
| Same CSS file | 193, `Compact right column` | Compact product rows/photos, category typography/table spacing, navy share bars and a scrollable category list. The large donut is not displayed in this placement. |
| Same CSS file | 245, `Match Sales Overview to the combined right-column cards` | Desktop stretch applies to Sales Overview and the whole right column. The Sales Trend chart uses the available height; mobile retains its existing chart size. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 and 563, CSS/filter-script URLs | Updated browser cache versions. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 15, `cardHeights` | Measures Sales Overview against the combined sidebar, verifies category placement, and captures bar widths/colors. |
| `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs` | 14, combined right-column assertion | Checks desktop height alignment, categories below products, navy bars and the compact chart display. |
| `CAMPUSHUB_CONTEXT.md` | 7, 17 and 21, current UI/height/placement decisions | Records the trial placement, replacing the previous full-width category decision. |
| `docs/marketplace-card-height-footer.md` | 3, latest update | Points the earlier single-product-card height report to this newer combined-column layout. |
| `docs/marketplace-right-stack.md` | 1 | Added this learning guide. |

Regenerated scratch previews, isolated test renders, browser measurements and screenshots under `scratch/sales-overview-system-test/`.

## 3. Changes Made

- Kept Sales Overview, its KPI cards, Sales Trend and grouping selector on the left.
- Kept Top Best-Selling Products at the upper right and moved Sales by Product Categories directly beneath it.
- Kept approximately two-thirds/one-third desktop column widths, using the existing `2fr / 1fr` grid.
- Reduced product row padding and photo size in the narrow right column.
- Displayed categories as a compact table with navy horizontal share bars, percentage and peso amount.
- Kept both honest empty states and the existing sample/real-data controls.
- Removed the unused CSS rule for the former full-width category wrapper.

## 4. How It Works

The Django include determines placement: putting the category include inside `dashboard-marketplace-side` makes it the second right-hand card.

CSS Grid stacks the two right cards with a 16px gap. At marketplace content widths of 960px and above, the outer grid stretches Sales Overview to the combined right-column height. Its chart container can grow from a 280px base, letting the graph use that extra space. Below the breakpoint, the three cards stack in reading order with natural heights.

Each category bar represents its share of **completed paid sales amount**, on a consistent 0–100% scale. The template uses the existing backend-calculated share; the refresh/sample renderer uses that same field and clamps its visual width to 0–100%. The adjacent percentage and amount remain the readable data, so color alone is not required.

The existing donut markup and renderer hooks are retained during this trial, but CSS hides the large donut in the right-hand placement. This preserves the existing sample snapshot/restoration flow. It does not add a second visible chart or an extra container. Category tables remain keyboard-focusable and scrollable when many categories exist; their scrollbar is hidden.

## 5. Backend / API Behavior

No endpoint, query, payment rule, ranking or aggregation changed. Real analytics still derive from completed and paid Cash on Pickup orders. The five-product limit and period filters remain unchanged. Sample mode uses the existing verified fixtures; switching back restores the original actual category row nodes, including their bars.

## 6. Database / Migration Impact

No production records were added, modified or deleted. No migration is required. Sample fixture verification runs in the separate Django test database.

## 7. Tests Performed

- All **20 marketplace dashboard Django tests passed**, covering actual rankings/categories, empty/populated rendering and sample fixture calculations. Django reported no system-check issues.
- Existing sample integration checks passed: all grouping choices, exact values, real-node restoration, unrelated metrics, no sample API requests, and refresh/failure recovery.
- **Seven actual Chrome scenarios passed**: Daily, Weekly, Monthly, return to empty real data, refresh exit, mobile and 320px content width. Confirmed right-column placement, equal combined desktop heights, navy bars, no horizontal overflow and no JavaScript errors.
- Final measured sample desktop heights were approximately **705px** for both Sales Overview and the whole right column; the graph used approximately **359px**. Empty desktop heights matched at approximately **655px**. These are observations, not hardcoded card heights.
- Inspected desktop populated/empty and mobile screenshots. JavaScript syntax and CSS parsing passed.

### Manual check

1. Press **Ctrl+F5** on the Super Admin dashboard.
2. Find Marketplace Analytics: Sales Overview should be on the left, with Products above Categories on the right.
3. Click **Show sample** to inspect five product rows and six category bars.
4. Try Daily, Weekly and Monthly; the sales chart updates while product/category totals still describe the same selected period.
5. Click **Use real data**, then Refresh. Actual data or honest empty states should return without moving the cards.
6. Narrow the browser: the order becomes Sales Overview → Top Best-Selling Products → Sales by Product Categories.

Actual screenshot: `scratch/sales-overview-system-test/in-dashboard-daily.png`. Offline preview: `scratch/sales-overview-system-test/index.html`.

## 8. Remaining Limitations

This is a reversible layout trial applied to real and sample card placement. Sample product photographs remain sample-only. Long category names can truncate visually in the narrow column; the full text remains in the table/accessibility tree and title. Many categories scroll inside the compact table rather than making the dashboard indefinitely tall. The existing donut markup remains hidden during the trial and can be restored later if the user chooses that visual again.
