# Sales Overview sample values inside the dashboard

Current update: comparisons are gray again, and sample mode now populates all three Marketplace Analytics cards. See [the current guide](marketplace-analytics-samples-gray.md). This report describes the earlier Sales Overview-only sample implementation.

## 1. Cause / Reason

The first sample was a separate offline preview. Your screenshot was the real dashboard, which correctly remained at zero because it had no completed and paid sales in the selected period. You requested a visible example there, so the Super Admin Sales Overview card now has an explicit testing mode.

## 2. Exact Files Changed

Line numbers refer to this update; nearby anchors help you find code after later edits.

| Folder / file | Line | Nearby anchor | Change and purpose |
| --- | --- | --- | --- |
| `backend/templates/dashboard/partials/sales_overview.html` | 11 | `sales-overview__controls-top` | Added Show sample beside Daily/Weekly/Monthly. |
| Same file | 44 | `salesSampleNote` | Added a testing notice and included the sample JSON. The notice explains that other cards remain real. |
| `backend/templates/dashboard/partials/sales_sample_data.html` | 2 | `salesSampleData` | New JSON fixture with the three metrics and precomputed chart groupings from isolated test orders. |
| `backend/static/components/js/admin_sales_overview.js` | 44 | `leaveSample` | Restores actual chart data, grouping, metric text, empty state and accessible label. |
| Same file | 64 | `showSample` | Displays the sample metrics/chart and its accessible descriptions, with visible testing labels. |
| Same file | 94 | `if (sampleToggle && sample)` | Added button/grouping listeners; a live request exits sample mode. Failure disables the sample control until Retry succeeds. |
| Same file | 126 | `campushub:dashboard-data` | Clears testing state without overwriting newly rendered live metrics. |
| `backend/static/components/js/admin_dashboard_filter.js` | 463 | `salesGroupingSelect` listener | Sample grouping changes only this card; actual grouping still requests the existing API. |
| `backend/static/components/css/admin_marketplace_overview.css` | 26 | `sales-overview__controls-top` | Added flat navy button, gold testing indicator, keyboard focus and disabled styling. |
| Same file | 222 | `@container sales-overview (max-width: 439px)` | Stacks heading and controls on narrow cards so the new button fits. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 | marketplace CSS link | Updated the stylesheet version to avoid stale caches. |
| Same file | 562 | `admin_sales_overview.js` | Updated both changed JavaScript versions. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 69 | `test_sales_overview_system_preview_values_and_grouping` | Verifies all included sample groupings/metrics against the actual test API calculations. |
| `CAMPUSHUB_CONTEXT.md` | 11 | `Current Sales Overview testing choice` | Saved this testing decision for future work. |
| `scratch/sales-overview-system-test/export-sample-data.cjs` | 1 | export comment | Added exporter from actual isolated test payloads to the JSON template. |
| `scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` | 1 | integration setup | Added checks for sample/live switching, grouping, other-card isolation, refresh and error/retry. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 1 | browser preparation | Added actual Chrome review pages using the real rendered card and chart script. |
| `scratch/sales-overview-system-test/render-in-dashboard-sample.ps1` | 1 | `taskReviewDirectory` | Added seven Chrome captures, including mobile and a 320px frame. |
| `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs` | 1 | verification loop | Added assertions for actual chart values, visible notice, restoring zero, keyboard tooltips and layout. |
| `scratch/sales-overview-system-test/README.md` | 3 | in-dashboard instructions | Added steps for the new sample mode and fixture regeneration. |
| `docs/sales-overview-system-test-preview.md` | 3 | later update note | Links the original offline-preview report to this newer feature. |
| This document | 1 | document title | Implementation report and beginner testing guide. |

Generated scratch files were refreshed from the isolated test database: source HTML/JSON, offline previews, in-dashboard review screenshots/DOM reports and the test log.

## 3. Changes Made

Added a Show sample / Use real data toggle to the existing card. No dashboard section was removed or moved. Sample mode displays ₱3,900.00 Marketplace Sales, 18 Completed Orders and ₱216.67 Average Order Value. Navy sales bars, the gold orders line, exact tooltips and keyboard inspection remain. A gold-edged notice and sample subtitle/footer identify the example clearly.

## 4. How It Works

The fixture covers September 29–October 5, 2026. Daily sales are 350, 525, 0, 800, 450, 1,125 and 650 pesos. Completed-order counts are 2, 3, 0, 4, 2, 5 and 2. The sums are ₱3,900 and 18; ₱3,900 / 18 gives the ₱216.67 average.

The existing Django analytics also produced the weekly and monthly arrays. The browser selects a precomputed array, avoiding another aggregation rule. The existing Chart.js instance updates its data and axis scales.

The script keeps a temporary copy of the actual card before showing the sample. Use real data restores it. Refresh, global period changes and other live requests exit sample mode and load actual data. Sample grouping affects only this card; other dashboard cards continue showing actual data.

To try it:

1. Open your normal Super Admin dashboard and press Ctrl+F5 once.
2. Click Show sample beside Daily in Sales Overview.
3. Confirm ₱3,900.00, 18 and ₱216.67, with populated bars and a line.
4. Try Weekly or Monthly; totals stay consistent and chart buckets change.
5. Hover the graph, or focus it and press Left/Right/Home/End, to inspect exact values.
6. Click Use real data or the global Refresh button. Actual totals return; zero is correct when the selected period has no qualifying sales.

## 5. Backend / API Behavior

No application backend view, route, permission, order lifecycle or API response changed. Existing server-side dashboard access remains. Live analytics still count actual completed-and-paid marketplace orders. Sample mode makes no fetch and needs no new endpoint; its JSON fixture is included only in the global dashboard card.

## 6. Database / Migration Impact

No live orders, payments or stock reservations changed. No migration is needed. Sample source records exist only in the isolated Django test database.

## 7. Tests Performed

Passed 65 Django tests across dashboard marketplace, dashboard periods and Sales Overview. Included sample values/groupings match actual test API calculations. Django reported no system-check issues.

Passed the new integration check for three sample groupings, exact values, unchanged other-card totals, no sample API requests, restoring real grouping/zero values, refresh, failed-request disable behavior and Retry recovery. Existing global-controls and Booking Overview integration suites passed. Both changed JavaScript files passed Node syntax checks; the controls suite parsed the CSS successfully.

Seven actual Chrome cases covered Daily, Weekly, Monthly, Use real data, live-loading exit, mobile and a 320px frame. They verified values, bar/line types, sums, visible sample labels, grouping, tooltip/keyboard data and no card/page overflow or JavaScript errors. Desktop/mobile screenshots were visually inspected. Git whitespace checks passed with existing line-ending warnings.

Evidence: `scratch/sales-overview-system-test/in-dashboard-django-tests.log`, `in-dashboard-*.dom.html` and `in-dashboard-*.png`.

## 8. Remaining Limitations

Sample mode is opt-in and resets after reload or a live refresh. Dates/totals are fixed examples independent of the global date selector. This tests the visual card and grouping, not checkout, cash collection or stock deduction. Live totals remain zero until actual qualifying orders exist. Physical phones, Firefox and Safari were not separately tested. The sample fixture stays in the global dashboard until you request its removal.
