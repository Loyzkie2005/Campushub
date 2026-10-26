# Category donut tooltip: implementation and programming guide

Updated 2026-10-05. Future code-related guides will explain functions and include a small exercise, as saved in `AGENTS.md`.

## 1. Cause / Reason

The donut showed a category distribution but had no way to inspect a segment's exact sales and percentage. The user requested that interaction and the clearer label **Sales share**, along with guides that teach how the code works. Hover alone would exclude keyboard/touch users, so focus and tap use the same tooltip information.

## 2. Exact Files Changed

| Folder / file | Current line / nearby anchor | Change |
| --- | --- | --- |
| `AGENTS.md` | 7, docs learning instruction | Saved the requirement to explain functions, data flow, examples and safe exercises in future code-related guides. |
| `CAMPUSHUB_CONTEXT.md` | 9, learning preference; 11, category interaction | Saved those learning and donut interaction decisions. |
| `backend/templates/dashboard/partials/category_sales_card.html` | 8, SVG; 14, segment circle | Added category metadata, keyboard focus and readable labels to initially rendered segments; described hover/tap/focus in the chart description. |
| Same template | 28, table header; 37, `data-category-tooltip` | Renamed Share to Sales share and added one hidden tooltip with separate name, sales and percentage fields. |
| `backend/static/components/js/admin_dashboard_filter.js` | 31, `hideCategoryTooltip`; 32, `showCategoryTooltip`; 41, `categoryAtPointer`; 56, `inspectCategoryPointer` | Added segment lookup, tooltip text/position and pointer/focus/touch/dismiss handling. |
| Same JS file | 381, category renderer; 414, circle metadata; 445, sample event; 476, global loading | Supplies the same metadata after API/sample renders and closes stale tooltips during data changes. Sales Trend grouping still leaves the right cards untouched. |
| `backend/static/components/css/admin_marketplace_overview.css` | 173, card position; 174, tooltip; 177, segment focus | Added a flat navy tooltip with white text and a keyboard focus outline. |
| Same CSS file | 282, narrow category card; 286, scrollable table | Kept the existing 480px narrow-card height definite and allowed the table to shrink/scroll. This prevents the longer Sales share heading from changing card height. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 and 563, CSS/JS links | Updated the cache versions to `20261005-category-hover`. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 243, category render assertions | Extended the existing real-data render test for Sales share and accessible category metadata. |
| `scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` | 39, `checkCategoryTooltip` | Added real/sample checks for each segment's values, focus, Escape, center/outside dismissal and unchanged grouping behavior. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 10, optional `inspect_category` check | Added actual-browser segment inspection and tooltip appearance measurements to the preview harness. |
| This document | 1 | Added the implementation report and learning walkthrough. |

Existing isolated fixture/previews/screenshots were regenerated. Added category tooltip screenshots, DOM dumps and logs under `scratch/sales-overview-system-test`; these are review artifacts, not production records.

## 3. Changes Made

Hovering a donut segment now shows its category, Sales amount and Sales share. The table heading uses Sales share too. Tab focus and tapping expose the same information. Escape, moving away or tapping outside dismisses it. The donut size, actual categories, aggregation and dashboard layout remain, with the narrow table retaining its internal scrolling.

## 4. How It Works — follow the data first

The existing Python function `sales_by_product_category(orders)` in `backend/core/modules/reports/dashboard_marketplace.py:62` takes the filtered completed/paid orders and returns category totals and chart geometry. It was inspected but not changed. A category's sales share is:

```text
category sales amount / total sales amount × 100
```

The Django template uses those values for the initial HTML. On a global Refresh, JavaScript receives the same category fields from the API. Sample mode uses the existing isolated sample payload. Both rendering paths place the name, amount, percentage and angle range on each SVG circle using `data-*` attributes.

| Function / handler | Inputs | Result / purpose |
| --- | --- | --- |
| `categoryAtPointer(event)` | Pointer coordinates; current SVG size; segment start/length metadata | Returns the matching segment, or no segment when the pointer is outside the ring or in its center. It calculates position only; it does not change totals. |
| `showCategoryTooltip(segment, x, y)` | Matched segment and pointer/focus coordinates | Reads metadata, fills the three tooltip fields and positions the box inside the category card. It changes the DOM, with no API/database write. |
| `hideCategoryTooltip()` | No arguments | Sets `hidden` so the existing tooltip disappears. Used for Escape, leaving, outside taps, resizing and data replacement. |
| `inspectCategoryPointer(event)` | Pointer move/down event | Calls the lookup, then shows the matching data or hides the tooltip. This connects browser input to the display functions. |
| Focus handlers | Focused SVG segment | Show the same tooltip without requiring a mouse. The segment's `aria-label` also contains its full values. |
| Existing `render(payload, sampleOnly)` | Real API or sample data | Builds table rows/SVG segments and supplies their metadata. Tooltip listeners are attached once to the parent SVG, so new segments work after refresh. |

Why calculate the angle? The visible donut uses overlapping circles with dashed strokes. Relying only on `event.target` could identify an overlapping circle rather than the visible sector. The helper normalizes the pointer into the SVG's 240×240 coordinate system, checks that it lies between radii 69 and 107, and converts its angle into a percentage around the ring. Those radii come from radius 88 and half of the 38px stroke width. It then finds the category whose cumulative start/length range contains that percentage.

Here is a small excerpt from the real display function:

```js
// Read the amount already calculated by Django; do not calculate new sales here.
const amount = segment.dataset.categorySales;

// querySelector finds the HTML field; textContent writes safe plain text into it.
categoryTooltip.querySelector('[data-category-tooltip-sales]').textContent =
    `Sales: \u20b1${amount}`; // \u20b1 is the peso character.

// Remove the hidden state so CSS can display the tooltip.
categoryTooltip.hidden = false;
```

`data-category-sales` in HTML becomes `dataset.categorySales` in JavaScript. The backend owns the value; JavaScript owns when/how it appears; CSS owns its color, spacing and position. Django auto-escapes initial metadata, and JavaScript uses `textContent` rather than interpreting product/category names as HTML.

The positioning function clamps coordinates with `Math.min` and `Math.max`, keeping the box within the card. The narrow-card rule uses a definite height, while `min-height: 0` lets the table fit its available space and scroll instead of forcing the card to grow.

## 5. Backend / API Behavior

No backend business-logic change. Actual completed-and-paid Cash on Pickup aggregation, revenue-based shares, real/sample switching and independent Sales Trend grouping remain. Hover/focus/tap creates no request and saves nothing. Global Refresh/date filters still load actual data.

## 6. Database / Migration Impact

No production writes or migrations. The Django tests use isolated test orders, and Show sample keeps its values outside the live database.

## 7. Tests Performed and how to test yourself

Two existing targeted Django tests passed: the sample fixture/grouping test and the category real-data/render test. Frontend integration checked every sector in real/sample mode, keyboard focus, Escape/outside/center dismissal, correct amounts/shares, preserved product/category nodes and chart-only grouping. Seven Chrome layout/grouping scenarios passed after fixing the longer heading's narrow-card height; a separate Chrome tooltip inspection checked each sector's matching values, visible navy tooltip styles and stable card height. JavaScript syntax, CSS parsing and targeted diff checks were used. No service/database logic changed.

To test manually: Ctrl+F5 → Show sample → hover different donut sectors. Compare the popup with the matching table row. Move into the center: no category tooltip should remain. Tab to a segment, press Escape, try a touch tap and then tap outside. Change Daily/Weekly/Monthly: the product/category cards should retain their data. Use real data or global Refresh: the tooltip must not keep old sample values.

### A safe practice exercise

1. Locate `showCategoryTooltip` using your editor's Find command. Read its three `textContent` assignments and predict which line controls each visible label.
2. Temporarily change only `Sales:` to `Sales amount:` in that function. This is a text change; do not edit the number or backend calculation.
3. Reload and hover a segment. Confirm the label changed while the amount, Sales share and table stayed the same. Existing strict text checks may fail until you either restore the label or intentionally update their expectation.
4. Restore the original label, then run `node scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` from the project root. It should pass.
5. Review your diff. You should be able to explain which function you touched, its input, its effect and how you verified it before asking for help.

For future tasks, practice this sequence: describe the expected behavior → find the existing code → follow the data → predict one small change → make it → verify → explain the diff. Ask for a hint or review of your attempt when you get stuck. Keep practice changes limited to UI text/spacing until you understand backend permissions and database effects.

## 8. Remaining Limitations

An empty category card has no segments to inspect. Zero-share categories stay in the table but have no visible ring sector. Touch behavior is implemented through pointer events and tested with browser events; physical-device testing remains useful. Long category names can wrap in the tooltip and truncate in the compact table. Browser verification uses actual code in isolated previews rather than a signed-in production session. The guide policy applies to future new/updated code documents; older guides have not all been rewritten.
