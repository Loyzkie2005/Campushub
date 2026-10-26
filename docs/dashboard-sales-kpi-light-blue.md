# Sales Overview KPI cards — approved light-blue icon design

Implemented October 4, 2026 from the user's approved white-card mockup. This report describes the latest KPI appearance; the earlier Sales Overview report describes the existing chart and date-filter behavior.

1. **Cause / reason**

   The approved design uses white KPI backgrounds and light blue only behind the icons. The previous implementation placed smaller icons beside the labels and tinted the card backgrounds. This update matches the approved placement, colors and supporting text.

2. **Exact files changed**

   Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Line numbers are approximate.

   | File | Line / nearby anchor | Change |
   | --- | --- | --- |
   | `backend/templates/dashboard/partials/sales_overview.html` | 50, metric heading | Definitions for all three metrics, including Completed Orders |
   | Same template | 57, `sales-overview__metric-value` | Value and decorative icon share a row, with the icon on the right |
   | Same template | 61, `dashboard-comparison` | Shorter empty-period copy matching the mockup |
   | `backend/static/components/css/admin_marketplace_overview.css` | 20, `sales-overview__metric` | White backgrounds, 16px padding, thin borders, consistent 12px corners |
   | Same stylesheet | 24–29, metric value/symbol/comparison selectors | 44px light-blue icon containers, 22px navy icons, wrapping secondary text |
   | Same stylesheet | 40 / 125 / 132, definition and container-query rules | Tooltip alignment follows desktop, two-column and stacked layouts |
   | `backend/static/components/js/admin_dashboard_filter.js` | 123, empty comparison text | AJAX refresh uses the same short empty-period copy as initial rendering |
   | `backend/templates/dashboard/pages/admin_dashboard.html` | 18 / 593, asset URLs | CSS/filter-script cache versions changed to `20261004-kpi-light-blue` |
   | `backend/core/modules/reports/test_dashboard_marketplace.py` | 153 / 175, empty-period assertions | Existing tests expect the new copy and retain the zero-value paid-order safeguard |
   | `scratch/dashboard-global-review/check-ranking.cjs` | 113, empty comparison assertion | Existing frontend regression check expects the new copy |
   | `docs/dashboard-sales-kpi-light-blue.md` | 1 | This implementation report |

   Actual browser preview artifacts are saved in `scratch/sales-kpi-light-blue-review/desktop.png`, `mobile.png` and `medium.png`. That folder also contains before-edit snapshots of the four production files for review.

3. **Changes made**

   The three KPI cards remain equal-width. Each has a white surface, navy label/value, thin neutral border and no shadow. Light blue (`#EAF3FF`) is confined to the small rounded icon container, as explicitly approved by the user. All three containers are 44×44px with 8px corners and 22px outline icons using the existing CampusHub SVG set.

   Labels remain 12px semibold, values 28px bold and supporting text 12px regular. The value is on the left and the icon on the right. Empty copy reads `No completed sales this period.` or `No completed orders this period.` Existing populated-period comparison semantics are retained.

4. **How it works**

   The shared template wraps the global dashboard value and icon in `.sales-overview__metric-value`, a grid with one flexible text column and one fixed 44px icon column. Existing JavaScript still updates the value and comparison inside `.sales-overview__metric-content`. No interaction or calculation is attached to the decorative icons; they are hidden from assistive technology. Definition buttons have accessible names and linked descriptions.

   Existing responsive rules keep three KPI columns on wide cards, two columns at medium widths and one column on small screens. Long values and supporting text can wrap. Definition tooltips align inward at the right edge, switch alignment when Average Order Value moves to the left of the second row, and use compact positioning on small screens.

5. **Backend / API behavior**

   No production Python, endpoint, API schema, selected-date logic or completed-paid-order calculation changed. Django still supplies real metrics. Global filters, grouping, the Sales Trend chart, zero-data chart, loading/error/Retry behavior and the right-hand analytics cards keep their existing behavior. The dedicated Marketplace Admin styling is preserved by the global-dashboard conditions.

6. **Database / migration impact**

   None. No migrations and no production data changes. Review data is rendered from isolated Django test records.

7. **Tests performed**

   - 59 Django tests passed: marketplace dashboard summaries, Sales Overview, dashboard periods and dedicated-domain dashboard access.
   - Existing frontend ranking and global-control checks passed, covering refresh, empty/populated transitions, API errors, Retry, grouping, authentication parameters and concurrent date-filter requests.
   - JavaScript and stylesheet syntax checks passed; the changed files passed `git diff --check`.
   - Headless Chrome checks passed for eight cases: populated desktop, empty desktop, laptop, medium, populated mobile, empty mobile, loading and error. These checked card columns, value font sizes, chart dimensions/visibility, label fitting, tooltip bounds, grouping placement and desktop alignment. The two-column tooltip issue found during review was corrected and verified again.

   Manual verification: open the Super Admin Dashboard, press **Ctrl+F5**, and inspect the three Sales Overview KPIs. Confirm white card surfaces and light-blue boxes behind navy icons on the right. Switch the global date range and Daily/Weekly/Monthly grouping; verify the values update, zero data stays honest and the chart remains visible. Tab to each information button to read its definition. Resize to check the three/two/one-column layouts.

8. **Remaining limitations**

   Browser previews isolate Marketplace Analytics and use fallback fonts for offline review; the live dashboard retains its existing Montserrat import. A live authenticated production session was not exercised. The approved image is a concept rather than a pixel specification, so the implementation uses the existing compact 28px value scale and responsive dashboard dimensions.
