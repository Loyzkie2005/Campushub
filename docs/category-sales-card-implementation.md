# Sales by Product Categories card — 2026-10-05

1. **Cause / Reason**

   Apply the approved single-card mockup to the dashboard. The previous sidebar card used progress bars and order-count percentages. The new card shows revenue distribution, an SVG donut, matching legend dots, and aligned percentage/sales columns.

2. **Exact Files Changed**

   - `backend/templates/dashboard/partials/category_sales_card.html` — new single-card component, donut, total, accessible table, empty/loading states.
   - `backend/templates/dashboard/partials/marketplace_analytics.html` — replace the old category sidebar card with the full-width component below Sales Overview and Top Selling Products.
   - `backend/static/components/css/admin_marketplace_overview.css` — chart/table layout, typography, navy/gold/neutral palette, subtle shadow, responsive stacking, scrolling/focus, loading visibility.
   - `backend/static/components/js/admin_dashboard_filter.js` — update total, rows, SVG segments, and chart labels when dashboard data changes.
   - `backend/core/modules/reports/dashboard_marketplace.py` — category revenue shares, total revenue, revenue ordering, SVG presentation metadata.
   - `backend/templates/dashboard/pages/admin_dashboard.html` — changed CSS/JS cache versions.
   - `backend/core/modules/reports/test_dashboard_marketplace.py` — updated category share expectations and regression coverage for revenue ranking, zero-value sales, six categories, and accessible markup; isolated review fixtures.

   QA files updated: `scratch/dashboard-global-review/check-ranking.cjs`, `verify-ranking-visual.cjs`.

   QA files added: `scratch/dashboard-global-review/prepare-category-visual.cjs`, `render-category.ps1`, `verify-category-visual.cjs`. This document records the implementation. Generated review artifacts remain in the scratch directory.

3. **Changes Made**

   - One white card with the exact title and subtitle, a subtle border/shadow, and no nested card surfaces.
   - The donut sits beside the category table on wide layouts; chart and table stack on narrow layouts.
   - The donut center displays total completed paid marketplace sales for the selected dates.
   - Each table row shows a matching legend dot, actual category name, revenue percentage, and peso sales amount.
   - Navy and gold lead the chart palette, followed by neutral grays. No extra bright category colors.
   - All real categories remain in the table. Long lists scroll with sticky column headings and a visible keyboard focus indicator.
   - Honest empty and zero-value states remain; loading and failed-request handling preserve the existing dashboard behavior.

4. **How It Works**

   Django aggregates the existing completed-paid queryset by the historical category, falling back to the current product category and then `Uncategorized`. Percentages are category revenue divided by total category revenue. Revenue determines descending order. SVG arc lengths use six-decimal precision; displayed shares round to one decimal and omit unnecessary trailing zeros. Labels for slices under 4% remain in the table to avoid crowding the donut.

   The initial page renders the complete component on the server. Existing date filters, grouping, Refresh, and Retry replace its table and SVG data using safe DOM methods. The donut does not depend on Chart.js. The existing Sales Trend section and chart remain intact.

5. **Backend / API Behavior**

   The existing dashboard endpoint and server-side permissions remain. Categories still use only completed, paid marketplace transactions. `product_categories.total` remains the completed order count; per-category counts and units remain available. `percentage` now represents revenue share, and `share_basis` is explicitly `completed_paid_sales_amount`. Added fields are `total_sales` and per-category `chart` presentation metadata. No new endpoint or client-side business query.

6. **Database / Migration Impact**

   None. No models, migrations, or production records changed. Six-category preview figures were created only inside the isolated test database; the running dashboard never receives hardcoded sample sales.

7. **Tests Performed**

   - Full dashboard regression run: 64 tests passed across periods, health, and marketplace suites.
   - Focused marketplace follow-up: 17 tests passed, including an additional six-category rendering case. This covers 65 distinct dashboard test cases across the two runs.
   - Existing global-control, health, attention, and ranking DOM checks passed, including authenticated filters, grouping, refresh, errors, Retry, request races, hostile category names, and unavailable Chart.js.
   - Eight category browser cases passed: desktop, tablet, 375px mobile, 30 categories on desktop/mobile, zero-value sales, empty, and loading. Confirmed matching legend colors, actual arc shares totaling 100%, correct total revenue, no nested cards, fitting text, keyboard scrolling, and no page overflow.
   - Nine analytics browser cases passed, preserving the Sales Trend footprint, product rows/tooltips, and responsive alignment.
   - Complete dashboard palette checks passed at desktop and narrow widths, with no JavaScript errors or overflow.
   - CSS parsing, JavaScript syntax, whitespace checks, and visual screenshot review passed.

   [Category card preview](../scratch/dashboard-global-review/category-desktop.png) · [375px card preview](../scratch/dashboard-global-review/category-mobile.png) · [Full dashboard preview](../scratch/dashboard-global-review/palette-desktop.png)

   Card previews contain isolated test records matching the approved sample figures. The full dashboard preview also uses isolated records and test health responses; it does not report production system health.

8. **Remaining Limitations**

   Rounded displayed percentages may sum to 99.9% or 100.1%; the donut uses precise revenue shares. The palette has six distinct colors; additional categories share the last neutral gray while their separate names and values remain visible in the table. Existing global dashboard date scope is preserved. No artificial categories or example orders were added to live data.

   Reload the dashboard with **Ctrl+F5** to load the changed CSS and JavaScript.
