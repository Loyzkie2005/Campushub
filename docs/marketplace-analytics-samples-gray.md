# Clear gray comparisons and samples across Marketplace Analytics

## 1. Cause / Reason

You requested returning the Sales Overview increase text to light/neutral gray while keeping it clear. You also requested sample data in Top Selling Products and Sales by Product Categories. The existing sample toggle previously populated only Sales Overview, so it now controls all three analytics cards together.

## 2. Exact Files Changed

Line numbers describe this update. Nearby anchors are more stable after later edits.

| Folder / file | Current line | Nearby anchor | Change and reason |
| --- | --- | --- | --- |
| `backend/static/components/css/admin_marketplace_overview.css` | 45 | `.sales-comparison-change` | Replaced green with neutral gray `#6B7280`, retaining 13px and semibold 600 for visibility. |
| Same file | 46 | `.marketplace-sample-note` | Added a small gold-edged testing label for each product/category card. |
| `backend/static/components/js/admin_sales_overview.js` | 77, 107 | `campushub:marketplace-sample` | Notifies the existing dashboard renderer when entering/leaving the shared sample mode. |
| `backend/static/components/js/admin_dashboard_filter.js` | 216 | `render(payload, sampleOnly = false)` | Reuses the existing product-list/category-donut code in a mode that changes only those two cards. |
| Same file | 360 | `breakdownSnapshot` | Keeps the actual product/category DOM nodes and visibility, then restores them when leaving sample mode. This retains real-image handlers. |
| `backend/templates/dashboard/partials/sales_overview.html` | 11 | `aria-controls` | The toggle now identifies all three cards it controls. |
| Same file | 44 | `salesSampleNote` | Updated the notice to identify the three sample cards and the unrelated real sections. |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 9, 12 | `topSellingProductsCard` | Added a stable card ID and a sample-only label. |
| `backend/templates/dashboard/partials/category_sales_card.html` | 3, 5 | `categorySalesCard` | Added a stable card ID and sample-only label. |
| `backend/templates/dashboard/partials/sales_sample_data.html` | 36, 73 | `top_products`, `product_categories` | Added the calculated top-five results and six category results to the test JSON fixture. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18, 562, 563 | marketplace CSS / scripts | Updated versions of the modified assets so browsers fetch them. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 72 | `sample_products` | Added six named products and varied order quantities in the isolated test scenario. |
| Same file | 115 | populated fixture assertions | Verifies five ranked results, six categories, matching totals and exact agreement between included fixtures and actual API results. |
| `CAMPUSHUB_CONTEXT.md` | 11, 13 | current testing/styling choices | Saved the shared sample mode and gray styling; supersedes the earlier Sales Overview green exception. |
| `scratch/sales-overview-system-test/export-sample-data.cjs` | 8, 9 | fixture fields | Exports calculated ranking/categories while omitting test product IDs, live product links and image URLs. |
| `scratch/sales-overview-system-test/build-preview.cjs` | 13 | `filterCode` | Extends the offline preview to all three real card templates, using the existing renderer. Other dashboard controls remain hidden in the test context. |
| `scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` | 37 | grouping checks | Checks five products, six rows/segments, matching totals, labels, unrelated-card isolation and exact restoration of existing actual nodes. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 18 | product/category measurements | Extends actual Chrome reports to the two additional cards. |
| `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs` | 13 | gray color check | Verifies gray 13px/600 text, ranked quantities, six category rows/segments, labels and layout. |
| `scratch/sales-overview-system-test/render-in-dashboard-sample.ps1` | 6 | `taskSize` | Uses taller captures so all three analytics cards can be inspected. |
| `scratch/dashboard-global-review/check-controls.cjs` | 85, 196 | comparison color assertions | Updates old navy-only expectations to match the requested gray period styling. |
| `scratch/sales-overview-system-test/README.md` | 3 | normal dashboard instructions | Updates the guide for all three sample cards. |
| Earlier sample/green guides in `docs` | 3 | superseding update notes | Link their historical reports to this current feature. |
| This document | 1 | title | Current implementation report and learning guide. |

The test-generated payloads, source HTML, offline preview files and seven Chrome screenshots/DOM reports under `scratch/sales-overview-system-test` were regenerated. Backend logs are `marketplace-fixture-export.log` and `marketplace-samples-django-tests.log`.

## 3. Changes Made

The increase text is neutral gray with the stronger 13px semibold style. Period wording remains muted gray and regular, with navy KPI values. Gray `#6B7280` has a calculated 4.83:1 contrast ratio against the white card.

Show sample now fills Sales Overview, the five-product ranking and the six-category donut/table. Each card displays a testing notice. No live dashboard section was moved or removed.

The sample ranking shows CampusHub Hoodie (15 units), Iced Spanish Latte (12), Spiral Notebook (9), Canvas Tote Bag (6), and USB Flash Drive (3), with their calculated sales amounts. The category card shows Electronics, Sports, Accessories, Apparel & Uniforms, Food & Beverages, and School Supplies.

## 4. How It Works

The fixture still contains 18 completed paid test orders totaling ₱3,900, with a ₱216.67 average. Those same orders now refer to six products with varied quantities. Django's existing ranking and category aggregation calculate the sample results; the exporter copies their output into the JSON template. Test IDs and live links are omitted.

Sales Overview emits a browser event when sample mode changes. The existing global dashboard renderer accepts `sampleOnly = true` to update the product/category results without touching top dashboard KPIs, operations, bookings, date metadata or other sections. It keeps the actual DOM nodes before replacing them, so Use real data can restore even an already populated actual list exactly. A live refresh restores actual cards before requesting updated real data.

All six products contribute to the ₱3,900 total. The top-five subtotal is ₱3,175; Basketball, the sixth product, contributes the remaining ₱725. Units sold represent quantity, while Completed Orders counts order records, so those numbers need not match.

To test:

1. Open the normal Super Admin dashboard and press Ctrl+F5.
2. Click Show sample beside Daily in Sales Overview.
3. Check the ₱3,900 sales, 18 orders, five ranked products and six category rows.
4. Compare the category donut's ₱3,900 center total with Marketplace Sales.
5. Try Daily/Weekly/Monthly. Chart buckets change; ranking and categories describe the same fixed sample period.
6. Click Use real data, or global Refresh. All three analytics cards return to actual records. Other sections remain actual throughout.

## 5. Backend / API Behavior

No application endpoint, permission, order lifecycle, inventory calculation or API schema changed. Live analytics still use completed and paid marketplace orders. The expanded fixtures are exported from the isolated test database, not generated by a live request. Switching sample mode makes no API request; the existing live filter/refresh flow remains responsible for actual data.

## 6. Database / Migration Impact

No live orders, products, payments or stock changed. No migration is needed. The named products and sample orders exist only in the isolated Django test database and are rolled back by the test framework.

## 7. Tests Performed

Passed the fixture-export scenario, then 65 Django tests across dashboard marketplace, periods and Sales Overview. They verify real calculations match the included metrics, grouping arrays, product ranking and category data. Django reported no system-check issues.

Passed the expanded sample interaction check: all groupings, exact totals, five ranked products, six category rows/donut, testing labels, no sample API requests, unrelated-card isolation, restoration of empty/populated actual cards, refresh and error/retry. Existing global-controls and Booking Overview checks passed. The old global-controls color assertion was updated to reflect the requested gray period styling rather than the earlier navy styling.

Seven actual Chrome checks passed: Daily, Weekly, Monthly, returning to real data, refresh exit, mobile and a 320px frame. They check computed gray color, 13px/600 weight, all three cards' contents, labels, chart values/tooltips and no overflow/JavaScript errors. Desktop/mobile screenshots were visually inspected. Changed JavaScript passed syntax checks, CSS passed the controls-suite parser, and tracked-file whitespace checks passed with the existing line-ending warning.

## 8. Remaining Limitations

Samples use fixed September 29–October 5, 2026 dates, independent of the global date filter. Sample products have no thumbnail photos or live product links. Reload or live refresh exits sample mode. This is an analytics UI/testing example, not a checkout/payment/stock workflow. Actual empty periods still show honest zero states. Physical devices and Firefox/Safari were not separately tested.
