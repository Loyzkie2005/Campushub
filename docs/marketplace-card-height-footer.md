# Equal marketplace card heights and footer removal

Latest update: categories now sit below products in the right column. Sales Overview matches the **combined right-column height**, superseding the earlier single-product-card alignment described below. See `marketplace-right-stack.md`. The footer removal remains in effect.

## 1. Cause / Reason

The user asked to remove the Sales Overview payment-basis sentence and make the Top Best-Selling Products container match Sales Overview, including when there are no products. The existing desktop grid aligned cards at the top, which left the shorter product card with unused space below it.

## 2. Exact Files Changed

| Folder / file | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/sales_overview.html` | 96, `<footer class="sales-overview__footer">` | Render the footer only for the existing non-global dashboard; the Super Admin global card no longer includes its sentence, icon or divider. |
| `backend/static/components/js/admin_sales_overview.js` | 84, `realSnapshot.text` | Removed the deleted footer from the sample restoration selector. |
| `backend/static/components/css/admin_marketplace_overview.css` | 217, `Match the two marketplace cards` | Added desktop-only grid stretching at marketplace content width 960px and above. Removed the earlier sample-only footer hiding rule, because the global template now omits the footer altogether. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 and 562, CSS/JavaScript asset URLs | Updated cache versions for the changed styles and sample script. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 357, `test_empty_layout_keeps_chart_footprint_and_writes_review_artifacts` | The existing empty/populated page test now checks that the Super Admin payment-basis sentence and footer are absent. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 13, `cardHeights` | Measures both card heights, their vertical positions and whether a footer exists. |
| `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs` | 12, `result.salesFooterPresent` | Checks footer removal, equal desktop heights, and stacked mobile layout. |
| `CAMPUSHUB_CONTEXT.md` | 15 and 17, `Current sample copy preference` / `Current marketplace height preference` | Records the current footer and height decisions. |
| `docs/marketplace-card-height-footer.md` | 1 | Added this beginner-friendly implementation report. |

Regenerated HTML previews, isolated test renders, browser measurements and screenshots in `scratch/sales-overview-system-test/`.

## 3. Changes Made

Removed the Super Admin Sales Overview footer in both real and sample mode. Matched the two side-by-side card heights without assigning a fixed pixel height. Kept the honest **No completed product sales yet.** message and its icon; the existing flexible empty-state area centers them inside the taller card.

## 4. How It Works

CSS Grid's `align-items: stretch` makes both columns fill the same row height. The row grows to fit whichever card needs more space, so product names and chart content are not clipped. The product sidebar already contains one grid item, which stretches with its parent.

The rule uses a named container query: it checks the marketplace section's width, rather than the whole browser window. It applies only at 960px and above, where the cards appear beside each other. Below that width, existing rules stack the cards and allow their natural heights.

The footer is omitted by Django's `{% if not global_dashboard %}` condition, rather than leaving an empty footer container in the Super Admin HTML.

## 5. Backend / API Behavior

No API, ranking, aggregation, payment, permission or sample-switch behavior changed. Real rankings still derive from completed and paid Cash on Pickup orders. No-products and zero-sales states remain honest and visible.

## 6. Database / Migration Impact

No production database records were changed. No schema migration is needed.

## 7. Tests Performed

- Two targeted existing Django tests passed: sample fixture/grouping/render and empty/populated dashboard layout. Django reported no system-check issues.
- JavaScript syntax and the sample integration checks passed, including real-data restoration and refresh/failure handling.
- Seven actual Chrome scenarios passed: Daily, Weekly, Monthly, return to empty real data, refresh exit, mobile and a 320px content frame. Desktop card heights matched within one pixel; all cases omitted the global footer and fit their available width.
- Inspected the populated and empty desktop screenshots visually.

Manual check: press **Ctrl+F5**, find Marketplace Analytics, and check that both desktop cards end at the same vertical position. Use **Show sample** and **Use real data** to test populated and empty states. Narrow the browser to check that stacked cards have natural heights. The quoted footer sentence should be absent in both modes.

## 8. Remaining Limitations

Equal heights apply while the cards are side by side; stacked cards intentionally do not match heights. The existing non-global dashboard footer is preserved. Sample mode remains a development preview; no fake records were inserted into production.
