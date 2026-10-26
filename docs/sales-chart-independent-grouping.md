# Sales Overview: independent chart grouping

Updated 2026-10-05.

## 1. Cause / Reason

Daily / Weekly / Monthly was wired to the same loader as the global dashboard filter. Changing chart grouping therefore showed loading across the dashboard and rebuilt the product list and category donut. Sample grouping also emitted the event that re-rendered those two cards. Backend totals already remained independent of chart grouping; the frontend needed to respect that separation.

## 2. Exact Files Changed

| Folder / file | Current line / nearby anchor | What changed and why |
| --- | --- | --- |
| `backend/static/components/js/admin_dashboard_filter.js` | 24, `salesRetryOnly` | Remembers whether an error came from a chart-only request so Retry uses the correct scope. |
| Same JS file | 217, `renderSalesTrend(payload)` | Moved existing chart subtitle, empty state, accessibility label and detailed-analytics link updates into a helper. Both global and chart-only responses reuse it. |
| Same JS file | 408, `load(period, salesOnly)` | Added a chart-only branch. It keeps the applied date range, skips dashboard-wide loading and unrelated renderers, and updates only the Sales Trend response. Requests still use the existing authentication handling and cancellation/stale-response guard. |
| Same JS file | 473, scoped error handling; 532, `salesOverviewRetry` | Keeps chart request failures/retries inside Sales Overview. Global errors retain their existing behavior. |
| Same JS file | 536, `salesOverviewFilters`; 540, `salesGroupingSelect` | Changed Sales Overview submission/grouping handlers to request chart-only updates. Global date and Refresh handlers remain global. |
| `backend/static/components/js/admin_sales_overview.js` | 105, `updateSampleTrend()`; 118, grouping listener | Separated sample chart updates from entering sample mode. Grouping no longer emits the product/category replacement event or rewrites sample KPIs. |
| Same JS file | 115, sample-toggle guard | Prevents switching sample mode during a pending real chart update. |
| Same JS file | 156, `campushub:sales-trend-data` | Added a chart-only event listener that updates chart arrays, hidden descriptions and chart visibility without resetting other analytics cards. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 562 and 563, JS URLs | Updated both script cache versions so a reload uses the new behavior. |
| `scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` | 21, request tracking; 47, sample nodes; 115, unchanged-card checks; 148, delayed responses | Extended the existing integration verification for sample/real node preservation, unchanged values, scoped loading/retry and out-of-order responses. Also verifies that global dates still refresh the other cards. |
| `scratch/sales-overview-system-test/build-preview.cjs` | 10, font import removal | Corrected offline-preview import removal to handle font URLs containing semicolons without accidentally swallowing CSS variables. This affects scratch previews only. |
| `CAMPUSHUB_CONTEXT.md` | 13, current Sales Overview filter scope | Saved the accepted independent-grouping behavior. |
| This document | 1 | Added this beginner-friendly implementation report. Existing scratch previews/screenshots were regenerated. |

No cards, menu items or chart markers were removed in this change.

## 3. Changes Made

Daily / Weekly / Monthly now updates only Sales Trend. Top Best-Selling Products and Sales by Product Categories keep their existing DOM nodes and data, preserving product scroll position and avoiding donut/list flicker. Sales Overview KPI values also remain unchanged. The global date filter and Refresh retain their whole-dashboard behavior. Show sample / Use real data still switches all three marketplace analytics cards.

## 4. How It Works

The loader receives a `salesOnly` flag. For a chart-only request it sends the already-applied start/end dates as a custom range, changing only grouping. That keeps a relative range such as Last 30 Days from drifting during regrouping. It marks Sales Overview busy, announces loading to screen readers, and leaves the dashboard root out of its global loading state. A successful response updates the chart helper and emits `campushub:sales-trend-data`, which only the sales chart consumes. The URL's grouping value is updated without replacing the selected global period.

In sample mode, `updateSampleTrend()` chooses the Daily/Weekly/Monthly sample series locally. Product/category sample rendering runs only when entering sample mode, rather than on every grouping change.

To test: Ctrl+F5 on the Super Admin dashboard, select Weekly and Monthly, and observe that only the Sales Trend buckets/labels change. Product ranks, units, category percentages, donut total and KPI values should stay unchanged. Repeat with Show sample. Scroll the product list before changing grouping; the position should remain. Then change the global date range or click Refresh to update all real-data cards.

## 5. Backend / API Behavior

No backend implementation changes. Real chart grouping still calls the existing authenticated dashboard API, with the same applied start/end dates and requested grouping. The API's completed-and-paid Cash on Pickup filtering and aggregations remain unchanged. Only the chart portion of that response is rendered for this action. Requests are cancelled when superseded, and an older response cannot overwrite the newest chart.

## 6. Database / Migration Impact

No production database writes or migrations. The Django verification test uses the isolated test database.

## 7. Tests Performed

- Existing Django test `DashboardMarketplaceTests.test_period_controls_both_summaries_and_grouping_preserves_them` passed. It confirms that global periods affect summaries while Daily/Weekly/Monthly preserves product/category summaries and order totals. Django system checks reported no issues.
- Extended frontend integration checks passed for all three real/sample groupings, unchanged product/category/donut nodes and KPI values, preserved sample scroll position, no global loading, scoped chart failure/retry, delayed out-of-order responses, global date updates, sample restoration and refresh recovery.
- Seven actual Chrome preview scenarios passed: sample Daily/Weekly/Monthly, return to real data, refresh, mobile and narrow layouts. Existing chart keyboard, sizing, colors, values and no-overflow checks passed.
- Both changed production JavaScript files passed syntax checks. Targeted `git diff --check` passed.

## 8. Remaining Limitations

The existing API still calculates and returns its full dashboard payload, even though a grouping-only response updates only the chart. This preserves the existing authenticated endpoint without adding a second backend route. Real records added while regrouping can affect the fetched chart; other cards intentionally wait for a global refresh/date change. Real-mode frontend request checks use mocked API responses; the backend contract is covered by the Django test. Browser checks use isolated actual-template previews rather than a signed-in production session. This change applies to the Super Admin global dashboard; legacy non-global Sales Overview pages retain their form behavior.
