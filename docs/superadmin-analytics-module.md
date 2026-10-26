# CampusHub Super Admin Analytics Module Guide

## Current approved Super Admin Analytics improvements — October 26, 2026

This section supersedes earlier Super Admin Analytics captions, date-window, assumed utilization and unknown-account fallback guidance. It does not change the executive dashboard or other administrator interfaces.

### 1. Cause / reason

The four-tab Analytics architecture already existed. Confirmed problems were inconsistent preset resolution when stale custom inputs were submitted, Facilities/Users trends extending beyond the selected range, unknown mobile types being added to Students, an eight-hours-per-day utilization assumption, unconditional empty charts/status rows, missing accessible chart tables and obsolete Cash-on-Pickup-only wording. Revenue already used Completed AND Paid; changing its business rules was neither needed nor authorized.

Browser verification also confirmed a 320px Sales Performance header overflow and an unbounded retained Facility Status donut. The final styles constrain these within Super Admin Analytics only. Shared-role output remains on its existing branches.

### 2. Exact modified files / current lines and code anchors

| Exact file | Current anchor | Change |
|---|---|---|
| `backend/core/modules/reports/views.py` | 1345 `is_super_analytics` / `enrich_marketplace` | Opt into enrichment only after existing Marketplace Analytics permission checks. |
| `backend/core/modules/reports/analytics_sections.py` | 49 `analytics_period`; 105 Facilities; 220 monthly aggregation; 376 Users; 414 monthly aggregation; 458 Web Accounts; 490 review-date aggregate; 515/550 renderers | Super-only preset precedence, bounded trends, verified capacity projection, honest classification and dated/snapshot context. |
| `backend/core/modules/reports/superadmin_analytics.py` (new) | 15 `is_super_analytics`; 21 `chart_table`; 25 `enrich_marketplace`; 90 `facility_capacity_rows` | Small read-only presentation projection around existing services; comparisons, authorized links, table alternatives and batched configured-capacity reuse. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | `super_analytics` branches, KPI grid, Sales Performance, category/buyer/inventory/DSS blocks | Accurate labels, comparisons, empty/populated states, existing links and accessible data without removing sections. |
| `backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html` | `super-admin-analytics` body; chart includes; Facility Utilization table | Preserve booking/status/ranking/revenue features; show verified hours/slots/nights/units and unavailable capacity rather than assumptions. |
| `backend/core/modules/reports/templates/reports/pages/admin_services_analytics.html` | Registered Services and Completed Requests subtitles | Distinguish current catalog from submission-period requests; never infer receipt/payment/results release from Completed alone. |
| `backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html` | KPI subtitles, User Distribution, seller-statistic notes | Current account status, honest Unclassified/Web Accounts, real submission/review-date counts and actual application-share bars. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart.html` (new) | 1 `has_data` | Reuse existing chart IDs/renderers with accessible labels and data alternatives, or a compact honest empty state. |
| `backend/core/modules/reports/templates/reports/partials/analytics_chart_data.html` (new) | 1 native `details` | Collapsed, captioned, horizontally scrollable data table with row/column scopes. |
| `backend/templates/dashboard/partials/facility_revenue.html` | 13 `data-revenue-table` | Add the alternative only when opted into Super Admin Analytics; other dashboard markup is unchanged. |
| `backend/static/components/js/admin_marketplace_analytics.js` | 5 role flag; 21 peso formatting; 160 scoped axis options | Super-only navy/gold presentation, Philippine formatting and readable adaptive axes; calculations and datasets unchanged. |
| `backend/static/components/js/admin_analytics.js` | 5 `GOLD` | Correct web gold only for the opted-in Super Admin body; retain other roles' existing rendering. |
| `backend/static/components/js/admin_super_analytics.js` (new) | 1 DOMContentLoaded | Disable irrelevant custom inputs and add keyboard-operable local sorting to bounded existing tables; chart tables retain chronological order. |
| `backend/static/components/js/admin_facility_revenue.js` | 4 role flag; 51 scoped validated-data branch | Preserve existing validation/refresh/keyboard/report link behavior; hide/destroy empty Super Analytics revenue chart and refresh its accessible table from the validated series. |
| `backend/static/components/css/admin_analytics.css` | 1104 `.super-admin-analytics` block | Scoped intrinsic cards, compact empty states, navy/gold links/badges, wrapped headers, 180px status donut, bounded table scrolling and focus indicators. No global redesign. |
| `backend/core/modules/reports/test_superadmin_analytics.py` | 286 onward approved regression cases; optional browser fixture export | Extend existing tests for boundaries, comparisons, scopes, unknown types, capacity, bundles, revenue reconciliation and shared-role identity. |
| `docs/superadmin-analytics-module.md` | This report | Causes, exact files, functions/data flow, test evidence, limits and safe exercise. |
| `CAMPUSHUB_CONTEXT.md` | Latest entry | Persist finalized role-specific behavior and verification references. |

The two new template partials and new Super-specific script/projection keep repeated chart markup and shared-role effects contained. The retained facility-revenue partial/script required a guarded change after browser inspection verified its empty-chart problem. These are presentation/read-only projection changes, not new features or database entities. The inspected `analytics_dates.html` needed no edit: Super-only server precedence and disabled irrelevant inputs resolve its problem. Existing dirty working-tree changes were preserved.

### 3. Fixes and improvements completed

- All four existing tabs and Reports → Analytics / Generate Reports navigation remain. Presets win over stale custom inputs for Super Admin; intentional custom ranges, Philippine timezone and existing maximum-range handling remain. Tab links retain the selected period.
- Facilities/Users trends query only selected dates and bucket them chronologically. Monthly aggregates use one grouped booking query or two grouped account queries rather than one query per month. The Facilities trend explicitly measures currently approved/completed reservations **submitted** in the selected period; its booking/stay-date KPIs retain their different, clearly labelled date basis.
- Unknown mobile account types remain **Unclassified**. Django web-account rows are labelled **Web Accounts (recorded roles)** rather than inferring a mobile account type from access roles. These are account records, not deduplicated people. Seller remains an independent privilege. Active Users describes enabled accounts, not recent use; inactive/disabled count is the complement of the existing enabled-account calculation.
- Per-facility utilization reuses verified operating-schedule/slot/room-night/unit calculators. Booking intervals are clipped to configured openings, overlapping usage is unioned, stays use checkout-exclusive nights within the selected period and unavailable configuration stays unavailable. Current configuration cannot reconstruct historical configuration changes. No eight-hour denominator is inferred.
- Sales Performance keeps Daily/Weekly/Monthly and its existing revenue/order datasets. Equivalent previous-period revenue/order comparisons are added to the existing surface. A zero baseline never creates a growth percentage. Active Sellers and Repeat Buyers keep their original definitions. Approved Products and stock are clearly current snapshots.
- Empty sales, booking/registration trends and zero-order status sections show compact messages. Qualifying zero-price orders keep the sales chart/table; all-zero category revenue is shown in the table rather than an empty donut. No positive revenue means no invented peak period.
- Existing charts gain labelled canvases and native collapsed chart-data alternatives. Valid zero dates remain. Existing facility revenue keeps its paid-transaction source, keyboard interaction, refresh validation and report link, with a read-only table; empty periods have neither a visible/instantiated revenue chart nor an exposed all-zero table.
- Order-status links use existing authorized Orders filters and **creation dates**, matching that metric. Product rankings link to surviving authorized product records. Inventory links reuse existing search; seller names link to the existing seller-application search rather than claiming an invented unique identity. Existing ranking order remains the default. Local keyboard sorting affects only bounded existing non-chart tables and makes no additional data requests.
- Inventory explanations distinguish available quantities from component-derived bundle availability. No physical-plus-derived stock sum is introduced. Days remaining/daily averages are labelled observed-rate estimates, not reliable forecasts from sparse history. Existing algorithm thresholds and insufficient-data messages remain.
- Services retain real request statuses and submission-date cohorts. Completed does not imply cash collection or results release. Current seller application status is distinguished from dated application submissions and recorded approved/rejected reviews; no historical decisions are reconstructed.

### 4. How it works — inputs, outputs, functions and data flow

Existing permission-checked views → unchanged module services → optional Super Admin enrichment → existing role-specific templates/Chart.js renderers. `is_super_analytics(user)` chooses presentation for an authenticated, active Super Admin identity; it grants no permissions and is used only after the existing view checks. Other roles keep the previous presentation. Shared Marketplace Admin and Facilities Admin HTML was rendered against the exact pre-change templates and compared after whitespace normalization.

`enrich_marketplace(analytics, user)` receives an already authorized dictionary from `build_marketplace_analytics`. It preserves its metrics/forecast/Apriori output, computes a previous-period aggregate from the same `valid_sales_queryset(user)`, adds links only where existing permissions allow them, and creates read-only table rows. The existing service still requires Completed AND Paid, positive quantity, original scope and canonical recognition timestamp (completed time, then paid time, then creation time). **No revenue eligibility or recognition rule changed.** Category/product/seller calculations remain the existing ones.

For selected start S, end E and inclusive duration D, comparison dates are S−D through S−1. `comparison_metric` is reused: current 80 / previous 40 gives **100%**; current 80 / previous 0 gives **New activity**, with no percentage; both zero gives **No change**. Comparisons use the same recognition semantics and authorized scope as current revenue.

`facility_capacity_rows(period, facilities)` performs two batched reads (bookings and rooms) and delegates to the existing `_hours_or_slots` / `_rooms_or_units` functions from `dashboard_utilization.py`. It does not copy their business formulas or modify them. Inputs are the selected dates and actual facility configuration; outputs are verified usage/capacity/unit/percentage or an explanatory unavailable state. Example verified by tests: a 07:00–11:00 booking clipped to configured 08:00–18:00 contributes three hours; across two ten-hour days this is **3/20 = 15%**. A stay from September 29 to October 2 in an October 1–2 window occupies one checkout-exclusive night, giving **1/2 = 50%** for one configured room.

`chart_table(headers, rows)` is a data adapter only. `analytics_chart.html` receives the existing chart ID, label, actual table rows and a verified has-data flag. It retains the original renderer when meaningful data exists; otherwise it produces a compact empty message. `analytics_chart_data.html` provides native keyboard disclosure, caption and scoped headers. Forecast history gaps remain em dashes, not invented values. The new script sorts existing rendered rows locally, with stable ties and `aria-sort`; it does not load additional records or alter rankings in the backend.

### 5. Backend / API / permission behavior

Existing routes, sidebar items, four tabs, view permission checks, Program/Major scope and report authorization remain. Analytics is still read-only monitoring; Generate Reports owns export creation. The Sales Report still reuses the same completed-paid queryset and recognition dates; isolated reconciliation tests compare its rows with Analytics. No new API or duplicate Analytics page exists.

Super enrichment is additive; the source Marketplace Admin and Facilities Admin presentation is preserved. Existing direct-access permission tests remain, and newly exposed drilldowns intersect the destination's existing authorization. No individual buyer identities are exposed. Active Sellers still means approved eligible sellers with listing submission/update activity or qualifying sales in the period. Repeat Buyers still means identified buyers with more than one qualifying order within the period; New Buyers may overlap. Buyer charts count all qualifying purchases, including records without an identifiable buyer, and state this explicitly.

The existing forecasting algorithm, thresholds, Apriori calculation, saved recommendation workflow, synthetic/live separation, order/payment/fulfillment/FIFO and cancellation behavior were not modified. The original analytics service, reporting builder, configured-capacity service and protected marketplace workflow files retain their pre-change fingerprints.

### 6. Database / migration impact

No model, migration, schema, environment, inventory activation, stock writer or working record was changed. All new test orders/users/bookings/payments exist only in Django's disposable PostgreSQL test database. Before/after fingerprints of **13 protected marketplace/inventory/audit tables match**. Working projections for all four modules were checked inside a PostgreSQL `SET TRANSACTION READ ONLY` transaction; no operational refresh/mining persistence was triggered.

The actual working seven-day projection was empty revenue/orders, zero new registrations and zero requests; Users trend matched its zero registration count, and one mobile account remained honestly Unclassified. A configured facility capacity row was verifiable. These are verification observations, not hardcoded UI values or created historical records.

### 7. Tests performed — actual results

- **253 broader regression tests passed in 74.434s** across Super Admin Analytics, facility revenue/utilization, sales/report reconciliation, marketplace/executive dashboards, reports, bundle monitoring, bundles, FIFO inventory and FIFO concurrency. All prior tests were retained and extended.
- **21 final focused Analytics tests passed in 3.898s** after the final Web Accounts label refinement. Covers four-tab preset/custom parsing, stale input precedence, Philippine midnight boundaries, equivalent comparison windows, zero baselines, genuine zero-price sales, report reconciliation, filtered status drilldowns, month clipping, unknown types, bundle-derived availability, unchanged algorithms and role isolation. The normalized shared-role HTML comparisons passed.
- Capacity tests assert **two batched queries** independent of the number of supplied facilities. Users tests bound the projection to **at most 18 queries**, with month aggregation independent of the number of displayed buckets. No speculative whole-application performance score is claimed.
- **1,354 browser assertions passed across 62 renders**, with no page overflow, missing assets, JavaScript errors, mutation requests or working-database requests. Final screenshots and machine-readable results are recorded in `scratch/super-analytics-20261026/browser-results.json`. Verification covers empty/populated states across all four tabs at **1920, 1440, 1280, 1024, 768, 390 and 320px**, valid zero-price and weekly/monthly states, shared-role isolation, canvas labels, actual chart values/axes/peso tooltips, authorized link parameters, collapsed/expanded captioned tables, Enter/Space/focus, sorting/aria-sort, custom controls, no page overflow and bounded status-donut height. Requests are intercepted into isolated record-backed HTML/static assets; no browser request reaches the working database or mutates records.
- Django system check passed. Changed Python/JS syntax, all changed/new template compilation and added-line whitespace are checked in final validation. Desktop/mobile screenshots were inspected. Earlier test-fixture failures (incorrect model/context field names and an assumed unknown-count baseline) were corrected using the actual model/context; no unrelated assertions were removed to obtain a pass.

Evidence/reproduction: `scratch/super-analytics-20261026/run-tests.py` accepts the Django module labels; final broad labels are in `regression-tests.txt`, while the final focused run is `targeted-tests.txt`. `prepare-browser.py` generates the Playwright verification; run `node scratch/super-analytics-20261026/verify.cjs` after isolated fixtures exist. `live-read-check.py`, `snapshot.py`, original scoped copies, screenshots and `validation-summary.json` record reproducible evidence. The exact modified-file manifest is in `validation-summary.json`.

### 8. Remaining limits / troubleshooting / separate approval

- Real shared checkout identifiers are not captured in the current per-product order model. Frequently Bought Together therefore retains its honest insufficient-data state. No baskets were inferred from buyer/day or bundle components. New capture would require a separate task/approval.
- Historical physical inventory and facility configuration cannot be reconstructed from current snapshots. Bundle availability is derived, and shelf-life/FEFO/Returns/Refunds were not added.
- Services lack verified completion-event/payment/results-release history sufficient for a new completion-time or cashier-revenue trend. Current statuses of submission-period requests remain useful; no events or fees were invented.
- Active Sellers and Repeat Buyers definitions remain the existing definitions. Person-level deduplication across web/mobile accounts and a changed buyer/seller definition require a separate decision, not an undocumented inference.
- There are no new analytics exports, models, dependencies or algorithms. Existing report exports and administration pages are reused. Tables retain existing server-side bounds; local sorting is not a new unbounded dataset or pagination API.

Troubleshooting: if a preset seems overridden, inspect `period` plus disabled custom inputs and the Super Admin flag. If utilization is unavailable, inspect actual facility type, operating ranges, room assignments and configured slots; never fill in an assumed capacity. If revenue is empty, check both status/payment, positive quantity, authorized scope and recognition date rather than order creation date. Zero-price qualifying orders intentionally keep the chart. If another role unexpectedly receives new markup, inspect `super_analytics` and the body class before altering permissions. Failed/unverifiable reads must not be replaced with fabricated zeros.

Safe practice exercise: select a custom period, switch tabs, then select a seven-day preset. Confirm the dates and per-module cohort explanations. Open View chart data with Enter and close with Space; compare a peso total with Generate Reports using the same recognition dates. Use isolated test fixtures to verify zero-price, month-boundary and unavailable-capacity states. Do not create working sales, payments, inventory batches or audit events merely to fill charts for a demonstration.

October25,2026 inventory/report follow-up: [FIFO guide](fifo-inventory.md) covers the complete approved implementation, exact file/line map, functions/data flow, actual tests, troubleshooting and separate cutover gate. `build_report('products')` now outputs Quantity Basis and separate physical/derived summaries; its chart uses physical rows only. Product/Low Stock descriptions identify current snapshots with submission-date filtering, and User Login Activity states latest login per web account. Existing preview/CSV/serverPDF/nativeprint consume the same description/rows; Completed AND Paid Sales eligibility remains. Safe exercise: run `InventoryReportAccuracyTests` in the isolated database and verify70physical units and20derived bundles stay separate; never adjust live stock to match a report. No working database migration or stock change occurred.

## October 25, 2026: Sales Report recognizes completed AND paid orders

### 1. Cause / reason

The evaluator-readiness audit confirmed that the Sales Report used `Paid OR Completed`, while the dashboard's `_revenue_orders` requires both. This could recognize a paid pending/processing/ready/cancelled order, or an unpaid completed legacy record, as revenue. The correction changes only Sales Report eligibility and its matching summary label; it does not change how an order becomes paid or completed.

### 2. Exact files changed / current lines and anchors

| File / current line | Anchor and change |
| --- | --- |
| `backend/core/modules/reports/reporting.py:150` | `_order_report`: keep the original authorized query/date filtering, but the `sales` branch at line 158 now filters `status=STATUS_COMPLETED, payment_status=PAYMENT_PAID` together. |
| Same file, line 176 | Summary label now reads `Completed & Paid Orders`, matching the actual intersection. |
| `backend/core/modules/reports/test_sales_overview.py:18` | `SalesReportRevenueTests`: six isolated tests for the status matrix, monetary aggregates/chart, dashboard eligibility/total, original date behavior, Orders Report, preview/page, CSV/PDF, empty revenue, permissions and program scope. Optional exports under `SALES_REPORT_REVIEW_DIR` support artifact/browser checks. |
| `docs/superadmin-analytics-module.md:3` | This current implementation, verification, troubleshooting and learning report. |
| `CAMPUSHUB_CONTEXT.md:3` | Record the corrected eligibility and current verification/limitations. |

No other runtime file was changed for this fix. Earlier unrelated working-tree changes remain. Review artifacts and the original source snapshot are under `scratch/sales-report-revenue-review/`.

### 3. Changes made

The Sales Report now includes Completed + Paid and excludes Completed + Unpaid, Pending + Paid, Processing + Paid, Ready for Pickup + Paid and Cancelled + Paid. `Processing` is the existing stored status used for the confirmed/processing stage; no new Confirmed status is added. Revenue, eligible-order count, products sold, average order value, chart values and exported rows all derive from that filtered set. The ordinary Orders Report continues to show the excluded status/payment combinations as order records.

### 4. How it works / functions, inputs, outputs and data flow

`build_report(report_type, date_from, date_to, user=...)` in `reporting.py:453` calls `_order_report` for Sales/Orders. Its inputs are the existing selected report, optional dates and authenticated user. `_scope_marketplace` still restricts the dataset by existing Program/Major rules; `_filter_dates` still applies the selected range to `created_at`. Only then does the Sales branch require both existing status constants. The same filtered rows generate the summary and chart. `build_report` returns the original columns/rows/summary/chart structure, serializing Decimal row amounts as strings.

The existing page and preview endpoint consume `build_report`. CSV download calls the same builder and writes its rows. Server PDF download renders the same rows through ReportLab. The current browser Print PDF action uses the already-loaded report preview and native print layout, rather than requesting the server PDF endpoint. Both PDF paths were checked; no print/export route or template changed.

Annotated isolated example:

```text
Completed + Paid, total PHP106.50, quantity3 -> included
Completed + Paid, total PHP213.50, quantity1 -> included
Five orders covering the other requested combinations -> excluded
Revenue = 106.50 + 213.50 = PHP320.00
Recognized orders = 2; units = 4; average order value = PHP160.00
```

The tests compare eligible order IDs and aggregated `total_price` against the existing dashboard helper `_revenue_orders`. Using two keyword conditions gives the required SQL AND without adding another revenue service, changing global order queries or altering reporting-period semantics.

### 5. Backend / API behavior

The report builder's Sales eligibility changes intentionally; page/preview/download contracts, date filters, permission checks, report history logging, CSV/PDF formats and Orders Report behavior remain. No inventory, reservation, completion, Cash on Pickup, payment recording, cancellation, seller ownership, FIFO, Returns or Refunds workflow changes. No runtime JavaScript, UI layout, dashboard query or unrelated module changes.

### 6. Database / migration impact

No models, migrations, schema changes or production data writes. Tests create simulated legacy/status combinations only in the separate Django test database. Export endpoint tests create their normal `GeneratedReport` audit records there; browser checks intercept requests and never send production writes. The generated codes are actual codes assigned by the existing model to isolated test orders.

### 7. Tests performed / actual results

- The final **six new `SalesReportRevenueTests` passed** after adding an explicit dashboard monetary-total comparison. Tests confirm PHP320.00 recognized revenue, four units, two orders and PHP160.00 average; all five ineligible fixtures are absent.
- A broader **54-test run completed: 51 passed and 3 failed** across `modules.reports.test_sales_overview`, `accounts.tests.AdminReportTests`, `modules.reports.tests` and `modules.reports.test_facility_revenue`. All six new tests passed in that run. The three failures were reproduced with the original `_order_report` loaded only in memory from its pre-edit snapshot: missing old analytics subtitle text, old mixed-chart/dual-axis JavaScript expectations, and the existing user-monitoring permission test expecting403 but receiving200. No application file was reverted, and no unrelated test or access rule was changed to hide these failures. Logs: `regression.log`, `baseline-failures.log`, `final-focused.log`.
- Parsed the actual generated PDF with installed `pypdf`: both eligible order IDs and their PHP106.50/PHP213.50 values were present; all five ineligible IDs were absent. Parsed actual CSV amounts totaled PHP320.00. The permanent tests verify actual PDF creation plus its table rows matching CSV; no PDF-parser dependency was added to application requirements.
- **30/30 Chromium browser checks passed** at1366px/390px: corrected preview summary, two eligible rows, existing native print invocation/data/cleanup, excluded IDs absent, print amounts totaling320, matching CSV download bytes and no JavaScript errors. This checks print content before the operating-system print dialog; physical printing was not tested.
- Scoped `git diff --check` passed. No production transaction was submitted for verification.

Reproduce the six focused checks from `backend/core`:

```powershell
./venv/Scripts/python.exe manage.py test modules.reports.test_sales_overview.SalesReportRevenueTests --keepdb --noinput
```

### 8. Remaining reporting inconsistencies / troubleshooting / safe practice

The **status/payment eligibility** is now consistent with the dashboard; identical period totals are not promised because the original date semantics are deliberately preserved. Sales Report filters order `created_at`, while marketplace analytics uses completion/payment/creation fallback. An order created before the period but completed inside it can still produce different period totals. Analytics' `valid_sales_queryset` additionally excludes zero-quantity legacy rows; this task did not add that extra filter to Sales Report or modify dashboard helpers.

Other audit observations remain outside this fix: User Login Activity shows each account's latest login rather than full login history; Product & Inventory shows current stock filtered by product submission date and can sum derived bundle availability alongside component quantities. The three baseline failures above also remain; the permission failure needs a separate access-policy review. Historical exported files are unchanged and must be regenerated to reflect corrected eligibility.

If totals seem wrong, check the report's date range, product-owner scope, stored order/payment statuses and whether the order falls inside the creation-date range. Do not mark an unpaid order paid or complete it just to make a report match. Refresh the report preview or reopen it after deployment; native printing uses the currently loaded preview.

Safe practice exercise: run only the focused test class against the isolated test database. Read `test_status_matrix_totals_chart_and_dashboard_eligibility`, predict which fixture orders contribute and verify the 320/2/4/160 results. Read `test_creation_date_filter_and_orders_report_remain_unchanged` to explain why an outside-period creation remains excluded even when its completion date is inside. Do not create or change production orders for this exercise.

## October 20: separate row immediately below the header (current)

1. **Reason:** user clarifies the toolbar must sit below, outside the header, while retaining inline tabs/date controls.
2. **Files and anchors:** `backend/templates/partials/admin_header.html:3` restores its ordinary class; after `</header>` near line 98 the Super Admin-only `analytics_subheader` flag renders the toolbar as a sibling. `reports/partials/analytics_toolbar.html:1` accepts `below_header=True` to add `analytics-subheader`. `backend/static/components/css/admin_analytics.css:711` replaces header-grid rules with 12px vertical/24px horizontal row padding (16px horizontally below 599px). Five analytics templates rename the header presentation flag and refresh the CSS version: Marketplace line 20, Facilities 23, Services 19, Users 20, legacy domain 9. Existing context, scratch template check and this guide updated.
3. **Changes:** ordinary white header stays separate. Immediately below it, the toolbar aligns tabs to the title's left edge and dates to the right. Navy segments, Poppins and small gold accent are unchanged; no additional card or gradient.
4. **Data flow:** Analytics page passes `analytics_subheader=True`; existing shared header partial outputs the closed header, then the existing toolbar partial with its modifier. The HTML toolbar is outside `<header>` even though the same template composes both siblings. Original module/date inputs and links are reused, and the non-Super-Admin body condition prevents duplicate navigation/forms.
5. **Backend/API:** unchanged views, permissions, filter scripts and chart data.
6. **Database/migrations:** none.
7. **Checks:** isolated template render passed eight module/period cases, two scoped-role cases and compilation of five analytics pages. Verified exactly one toolbar after the closing header. Headless desktop/mobile checks passed at 1280/390/320px for preset/custom dates: matching title/tab left edges, non-overlap, no page overflow and correct active navy. Desktop screenshot inspected; no app/server restart.
8. **Limits and practice:** signed-in full-page QA remains pending. Refresh Analytics and verify the header ends before the tabs row; select Facilities and a date preset to confirm the same filtering. If duplicated, inspect the complementary Super Admin header/body conditions. Do not change backend views to fix layout.

## Earlier October 20: align the toolbar as the header's second row

1. **Reason:** user now asks to align the existing toolbar with the header as a second row. This supersedes the content-toolbar placement below; the refined segmented styling remains.
2. **Files / anchors:** `backend/templates/partials/admin_header.html:3` conditionally adds `analytics-header-with-toolbar`; line 97 includes the existing toolbar after the title/actions row. `backend/static/components/css/admin_analytics.css:711–720` defines a two-column header grid with 12px row spacing and a full-width second row. The five analytics page templates pass `analytics_second_row=True` in their existing header include (`admin_marketplace_analytics.html:20`, `admin_facility_analytics.html:23`, `admin_services_analytics.html:19`, `admin_users_analytics.html:20`, legacy `admin_domain_analytics.html:9`). Their original body toolbar includes (24/27/23/24/11 respectively) now render only for non-Super-Admin roles; CSS cache versions use `20261020-second-row`. Context, this guide and existing scratch verification scripts were updated.
3. **Changes:** Super Admin title/breadcrumb/actions remain row one. Segmented tabs and date controls form row two, using the same left/right header padding. Current navy `#1A1F71`, Poppins, gold accent and responsive wrapping remain. Other pages retain their ordinary header; scoped admin analytics retain content navigation.
4. **How it works:** page include passes a presentation flag; shared header checks the existing Super Admin flag/role before including `analytics_toolbar.html`. That partial still reuses original module/date partials. Example: Facilities remains selected through `analytics_module='facilities'`; its same GET form and period inputs now render inside the header. The complementary body condition prevents duplicate forms or IDs.
5. **Backend/API:** no view, permission, calculation, URL, chart data or filter-script changes.
6. **Database/migrations:** none; no records changed.
7. **Verification:** isolated template checks passed eight module/period cases, two scoped-role cases and five page compilations; checked one second-row toolbar after action markup. Headless previews at exact 1280/390/320px preset/custom states passed matching title/tab left edges, non-overlapping rows, no page overflow, correct active color and desktop left/right layout. Desktop screenshot inspected. Preview uses production header/toolbar/CSS and local equivalents for Bootstrap hidden-dropdown utilities; it does not load signed-in account data. No app/server restart.
8. **Limits / practice:** signed-in full-page visual verification remains pending. Refresh Super Admin Analytics and confirm tabs start directly under the title, date dropdown ends at the header's right padding, and switching tabs/dates keeps the existing selection and charts. On a narrow screen confirm controls wrap without covering the heading. If navigation appears twice, inspect the complementary Super Admin header/body conditions rather than changing Django views.

## October 20: refined segmented appearance (current styling)

1. **Reason:** user requests softer segmented styling and explicitly overrides the tab navy to `#1A1F71`.
2. **Files / current anchors:** `backend/static/components/css/admin_analytics.css:711` (`.analytics-toolbar`) defines scoped `--analytics-tab-navy`; line 728 uses 4px container padding and line 731 uses 14px outer corners. Link rules near 733 use 10px corners, Poppins 13px/500, white inactive surfaces and navy text. Active rules at 749 and 753 use solid navy/white and a centered 14×2px gold accent. The five analytics page templates (`admin_marketplace_analytics.html:13`, `admin_facility_analytics.html:13`, `admin_services_analytics.html:13`, `admin_users_analytics.html:13`, `admin_domain_analytics.html:7`) only update the stylesheet version to `20261020-segments`. Existing scratch template/browser verification scripts track that version and the new expected active color. This guide and the context note record the update.
3. **Changes:** rounded white segmented container, subtle gray border, soft padding, flat medium-weight tabs and a tiny gold active underline. Solid fill was selected; a gradient was optional and unnecessary.
4. **How it works:** existing module links retain `aria-current="page"`; CSS uses that attribute to apply the active fill and decorative pseudo-element. The scoped custom property affects only these tab colors. Example: selecting Facilities changes which existing link carries `aria-current`, so the navy segment and gold accent follow it automatically. Toolbar placement, responsive wrapping, keyboard focus, 44px targets and date form remain.
5. **Backend/API:** no changes to views, permissions, scripts, data or URLs.
6. **Database/migrations:** none.
7. **Verification:** isolated template checks again passed eight module/period cases, two scoped roles and all five page compilations. Exact browser viewports 1280/390/320px passed preset/custom layouts with no page overflow, active color `rgb(26,31,113)` and retained desktop alignment. Desktop screenshot inspected. No app/server restart.
8. **Limitations / safe exercise:** signed-in full-page verification remains pending. Refresh Analytics, switch each tab and check one navy segment with a small gold mark. Use keyboard Tab to verify focus remains visible and choose a date preset to confirm the original filter still operates. If old colors persist, check the updated stylesheet version before editing backend code. The earlier toolbar section below explains the unchanged inputs, outputs and date data flow.

## October 20: compact content toolbar above KPIs

1. **Cause / reason:** the user now requests tabs outside the global header, grouped with the existing date dropdown directly above KPIs. This supersedes the header placement below. An older mobile rule also stacked custom-date labels with a 100px flex basis; the toolbar overrides its direction to avoid large gaps.
2. **Exact files changed:**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/templates/partials/admin_header.html` | 3 `dashboard-header`; closing header near 97 | Removed the Analytics-only class and module include; original title, breadcrumb and action controls retained. |
| `backend/core/modules/reports/templates/reports/partials/analytics_toolbar.html` | 1 `analytics-toolbar` | New composition of the existing navigation and date partials; no duplicate navigation/filter logic. |
| `backend/static/components/css/admin_analytics.css` | 710 compact toolbar comment; 711 `.analytics-toolbar`; 759 responsive rules | Left/right layout, navy selected segment, white surface, subtle border, Poppins, focus styles, 44px targets and narrow-screen wrapping. Removed superseded header-tab rules. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 10 fonts; 13 stylesheet; 20 header; 24 toolbar | Added Poppins to existing font request, refreshed CSS version, removed header opt-in and replaced separate tabs/date includes with toolbar. |
| Same folder: `admin_facility_analytics.html` | 23 header; 27 toolbar | Same composition, font and stylesheet updates. |
| Same folder: `admin_services_analytics.html` | 19 header; 23 toolbar | Same updates. |
| Same folder: `admin_users_analytics.html` | 20 header; 24 toolbar | Same updates. |
| Same folder: `admin_domain_analytics.html` | 9 header; 11 toolbar | Same updates; removed redundant inner title/date row so the toolbar sits above KPIs. |
| `CAMPUSHUB_CONTEXT.md` | latest toolbar note | Records accepted layout. |
| This guide | current section | Reason, behavior, verification and learning steps. |

3. **Changes made:** compact segmented navigation appears on the left of the content toolbar, existing date dropdown on the right. Active segment is navy `#1A1851` with white text. No gradients, shadow or extra toolbar card. On narrow screens tabs can scroll within their strip and dates wrap underneath; custom fields stay usable. Header/sidebar retain their original roles. Poppins is scoped to toolbar labels and controls; existing chart typography remains.
4. **How it works / inputs and outputs:** each page includes `analytics_toolbar.html`; it renders the unchanged `analytics_modules.html` and `analytics_dates.html`. `analytics_module` controls the selected link and hidden form module; `analytics_links` supplies URLs carrying the active period/date range; `analytics_period` sets the dropdown and custom dates. The existing GET form IDs remain, so existing JavaScript still shows Custom fields and submits preset selections once. Example: Facilities + Last 7 Days submits the existing `module=facilities&period=7` parameters; only the layout around that form changed. Composition avoids creating another controller or search/filter system.
5. **Backend/API behavior:** existing Django views, permission checks, chart JSON and aggregation logic are unchanged. Link visibility still uses the original module partial's permissions. No JavaScript, API or chart-data changes.
6. **Database / migration impact:** none; no records, schemas or migrations changed.
7. **Tests performed:** isolated Django render passed eight module/period cases, two scoped-role cases and compilation of all five page templates. Checked one toolbar before KPIs, one active link, preserved module/date parameters/form IDs and no navigation in the global header. Both existing filter scripts passed a DOM check: Custom reveals date inputs, preset selection submits once, repeat selection prevents duplicate submission. Headless Chrome verified exact 1280/390/320px viewports for preset and custom states: no page overflow, correct navy active color, desktop tabs left/dates right. Desktop and narrow-screen toolbar screenshots were inspected. No database or running app was used; no app/server restart.
8. **Limitations / learning exercise:** visual QA used the actual rendered toolbar in an isolated preview, not a signed-in live page with charts. Existing Google Fonts loading needs network access; fallback is sans-serif. Safely open Reports → Analytics, switch all four sections, choose Last 7 Days then Custom, apply a harmless date range, and verify the selected module/date range and existing charts. Narrow the browser and keyboard-tab through links, dropdown and dates. Refresh if old header styling is cached. If filtering fails, inspect the preserved `analyticsPeriodForm`, `analyticsPeriod`, `analyticsCustomDates` IDs and existing script loading before changing backend code.

Verification artifacts: `scratch/verify_analytics_toolbar.py`, `scratch/verify_analytics_toolbar_browser.js`, `scratch/analytics-toolbar-browser.log` and `scratch/analytics-toolbar-{1280,390,320}[-custom].png`. The superseded header diagnostic was removed.

## Historical October 19: Super Admin tabs inside the Analytics header

1. **Reason:** user confirmed the four module links belong inside the Analytics header. They previously appeared in the page content below it.
2. **Exact files and anchors:** `backend/templates/partials/admin_header.html:3` adds the scoped `analytics-dashboard-header` class; line 97 includes the existing module navigation. `backend/static/components/css/admin_analytics.css:711` scopes the two-row header layout and underline tabs. The five templates under `backend/core/modules/reports/templates/reports/pages/` opt in through the existing header include: `admin_marketplace_analytics.html:20`, `admin_facility_analytics.html:23`, `admin_services_analytics.html:19`, `admin_users_analytics.html:20`, and `admin_domain_analytics.html:9`. Their body includes (lines 24, 27, 23, 24, 11 respectively) now serve non-Super-Admin users only. All five refresh the analytics stylesheet cache version. `scratch/verify_analytics_header.py` is the isolated verification artifact; this guide records the implementation.
3. **Changes:** Marketplace, Facilities, Services and Users now form the bottom row of the Super Admin header, below title/breadcrumb and existing account controls. Navy labels, gold active underline, white background, 44px targets, focus outlines, and horizontal tab scrolling on narrow screens. Sidebar retains one Analytics destination.
4. **Functions and data flow:** page include supplies `analytics_header=True`; shared header checks Super Admin flag/role, then renders the existing `analytics_modules.html`. Its `analytics_links` input retains period/date parameters; `analytics_module` selects `aria-current="page"`. Example: `analytics_module='facilities'` highlights Facilities while its existing URL still selects the facility backend view. Non-Super-Admin analytics retain their previous content navigation, preventing duplicates. Other shared headers do not opt in.
5. **Backend/API:** existing views, permissions, analytics calculations and navigation URLs reused. No new endpoint or business logic.
6. **Database/migrations:** none; no records changed.
7. **Verification:** isolated Django template render passed eight Super Admin role/module cases, two exclusion cases, and compilation of all five page templates. Checks confirm one header navigation row, one selected link, date parameters and valid stylesheet references. No database accessed; no app/server restarted.
8. **Limitations/practice:** browser/device visual verification remains pending. Safe exercise: open Reports → Analytics as Super Admin; select each tab and verify the underline and retained dates, then narrow the browser and use keyboard Tab to reach each link. Other admin pages should retain their original one-row header. Refresh if the browser retains older CSS. Runtime analytics/database calculations were outside this layout-only check.

## Earlier October 19 correction: sidebar move reverted

The requested sidebar move was misunderstood and reverted. `backend/templates/partials/admin_sidebar.html` (Reports / Analytics link, around line 180) retains its single Analytics link. `reports/partials/analytics_modules.html` (line 1, `analytics-module-nav`) retains the existing horizontal Marketplace, Facilities, Services and Users links. The five `backend/core/modules/reports/templates/reports/pages/admin_*analytics.html` templates include it above their controls (Marketplace line 24, Facilities 27, Services 23, Users 24, legacy domain 11). The temporary submenu stylesheet and diagnostic script were removed.

The existing `analytics_links` input supplies URLs with the selected date period; `analytics_module` selects the active tab. Clicking a link still loads the existing authorized Django view and database-derived analytics. No backend/API, database or migration change. Static inspection confirms all five includes and no sidebar submenu; browser rendering and runtime tests were not completed during this interrupted change. Safe practice: open Analytics, choose Facilities, then Services and check the selected tab and date period remain correct. If the old submenu remains visible, refresh the page.

## 1. Overview and Purpose
The **Super Admin Analytics** module delivers a unified, data-driven analytical dashboard across four core domains:
1. **Marketplace** (`?module=marketplace`)
2. **Facilities** (`?module=facilities`)
3. **Services** (`?module=services`)
4. **Users** (`?module=users`)

The module is accessible from a single **Reports &rarr; Analytics** sidebar item in the Django Super Admin web panel. It adheres strictly to the Institutional Design System:
- **Primary Navy Blue**: `#1A1851`
- **Accent Gold**: `#FCB315`
- **Light Neutral**: `#FFFFFF` / `#F8FAFC`
- **Subtle Institutional Border**: `#E8EAF0`
- **Zero AI-Slop**: No gradients, 3D slop, glowing cards, or fabricated metrics.

All metrics originate directly from real PostgreSQL database records through the Django ORM.

---

## 2. Architecture and Data Flow

```
HTTP Request (?module=...&period=...&date_from=...&date_to=...)
                         │
                         ▼
     [views.py: admin_marketplace_analytics_page]
                         │
        ┌────────────────┴────────────────┐
        │                                 │
(module == 'marketplace')     (module in facilities/services/users)
        │                                 │
        ▼                                 ▼
[build_marketplace_analytics]     [render_domain_analytics]
        │                                 │
        │                       ┌─────────┼─────────┐
        │                       │         │         │
        │                   facilities services   users
        │                       │         │         │
        ▼                       ▼         ▼         ▼
[admin_marketplace_     [admin_facility_ [admin_services_ [admin_users_
 analytics.html]         analytics.html]  analytics.html]  analytics.html]
```

### Shared Global Date Range Filter
Each tab shares a unified date range filter:
- `7`: Last 7 Days
- `30`: Last 30 Days (Default)
- `90`: Last 90 Days
- `year`: This Year (Jan 1 to today)
- `custom`: Custom Date Range (`date_from` to `date_to`)

When switching between horizontal tabs, active date parameters are preserved via `module_links(period)` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L72-L85).

---

## 3. Detailed Tab Implementation

### 3.1 Marketplace Analytics
- **Template**: [admin_marketplace_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html)
- **Data Builder**: `build_marketplace_analytics` in [analytics.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/services/analytics.py#L617-L713)
- **KPI Cards**:
  1. *Total Sales Revenue*: Sum of `total_price` from qualifying completed and settled Cash-on-Pickup orders (`STATUS_COMPLETED` and `PAYMENT_PAID`).
  2. *Completed Orders*: Count of completed, paid orders within the period.
  3. *Active Sellers*: Sellers with at least one active listing or sale.
  4. *Approved Products*: Count of active catalog products with `approval_status='approved'`.
- **Main Bar Graph**: Monthly/Weekly/Daily sales performance rendered via Chart.js with Navy `#1A1851` bars and currency tooltips.
- **Top-Selling Products**: Ranked table of completed order items showing product name, seller, units sold, and revenue.
- **Order Status Breakdown**: Visual distribution of all orders submitted in the period across `pending`, `processing`, `ready_for_pickup`, `completed`, and `cancelled`.

### 3.2 Facilities Analytics
- **Template**: [admin_facility_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html)
- **Data Builder**: `build_facility_tab_analytics` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L104-L269)
- **Physical Isolation**: Filters out service booking facilities (e.g. Food Analysis Lab) using `service_resources_q("facility__")` and academic blocks via `schedule_blocks_q()`.
- **KPI Cards**:
  1. *Total Bookings*: Total physical facility reservations requested in the period.
  2. *Approved Bookings*: Reservations with status `approved` or `completed`.
  3. *Pending Bookings*: Active reservation requests awaiting administrative review.
  4. *Cancelled / Rejected*: Terminated or disapproved reservations.
- **Main Bar Graph**: Bookings by Physical Facility (Covered Court, Function Hall, Mock Hotel) rendered with navy bars.
- **Monthly Booking Trend**: Historical monthly progression of approved reservations.
- **Booking Status Breakdown**: Proportional status bars.
- **Facility Utilization Table**: Physical facility breakdown with capacity hours, approved counts, total reserved duration, and estimated utilization rate.

### 3.3 Services Analytics
- **Template**: [admin_services_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_services_analytics.html)
- **Data Builder**: `build_services_tab_analytics` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L271-L358)
- **Authentic Operational Model**: Services operate primarily as specialized informational and offline ISO procedures:
  - *Food Analysis Hub*: ISO Document `DPM-USTP-Oro-BEU-004` (Focal person: Conmar C. Malmis, BEU).
  - *BPP NC II Assessment Center*: Technical assessment reservation.
  - *Commercial Spaces*: Campus business lease application.
- **Honest Empty States**: If no electronic service requests have been submitted, displays an authentic informational overview of registered facilities and ISO guidelines without fabricating artificial transactions or synthetic graphs.

### 3.4 Users Analytics
- **Template**: [admin_users_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html)
- **Data Builder**: `build_users_tab_analytics` in [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L360-L472)
- **KPI Cards**:
  1. *Total Users*: Sum of registered mobile (`CampusHubUser`) and administrative (`User`) accounts.
  2. *New Registrations*: Accounts created within the active date period window.
  3. *Active Accounts*: Un-suspended accounts with `is_active=True`.
  4. *Approved Sellers*: Sellers with approved `SellerRequest` records.
- **Main Bar Graph**: User Registrations by Month showing account acquisition trends.
- **User Distribution**: Proportional breakdown across student, employee, guest, and administrator accounts.
- **Seller Application Statistics**: Total seller privilege requests grouped by Approved, Pending, Rejected, and Suspended.

---

## 4. Key Functions and Data Types

| Function | File | Input | Output | Description |
| :--- | :--- | :--- | :--- | :--- |
| `analytics_period(request)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L48-L70) | `HttpRequest` | `tuple[dict, AnalyticsPeriod]` | Resolves preset (`7`, `30`, `90`, `year`) or custom range; validates bounds |
| `module_links(period)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L72-L85) | `AnalyticsPeriod` | `dict[str, str]` | Builds tab URLs preserving the active date filter |
| `build_marketplace_analytics(...)` | [analytics.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/services/analytics.py#L617-L713) | `params: dict, user=None` | `dict` | Aggregates settled marketplace revenue, orders, inventory, and status breakdown |
| `build_facility_tab_analytics(...)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L104-L269) | `period, params, user=None` | `dict` | Aggregates physical facility bookings, charts, utilization, and trends |
| `build_services_tab_analytics(...)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L271-L358) | `period, params, user=None` | `dict` | Returns registered BEU services, ISO workflows, and real request counts |
| `build_users_tab_analytics(...)` | [analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L360-L472) | `period, params, user=None` | `dict` | Computes account creations, role distributions, and seller privilege stats |

---

## 5. Debugging and Troubleshooting

### 1. Inverted Date Range Error (HTTP 400)
- **Symptom**: User selects custom dates where `date_from > date_to` (e.g. from Oct 20 to Oct 10).
- **Cause**: [parse_analytics_period](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/services/analytics.py#L91-L92) checks `if start > end: raise ValueError("Start date must be on or before end date.")`.
- **Handling**: `admin_marketplace_analytics_page` catches `ValueError` and returns `HttpResponseBadRequest(str(error))`.
- **Resolution**: Ensure the frontend date picker sets `min` and `max` constraints, or correct the parameters in the query string.

### 2. Scoped Administrator Authorization (HTTP 403)
- **Symptom**: A Marketplace Admin attempts to access `?module=facilities`, `?module=services`, or `?module=users` and receives a 403 Forbidden.
- **Cause**: Super Admin Analytics restricts domain-specific access via role-based permissions in [render_domain_analytics](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L514-L525). Marketplace Admins only hold `can_view_marketplace_analytics`.
- **Verification**: Ensure Super Admin credentials (`is_superuser=True` or `role='Super Admin'`) are used when evaluating all four tabs.

---

## 6. Safe Practice Exercise

To test adding a new metric to the Users Analytics tab:
1. Open [backend/core/modules/reports/analytics_sections.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/analytics_sections.py#L365).
2. Locate `build_users_tab_analytics`.
3. Add a verified email count:
   ```python
   verified_users = mobile_qs.filter(email_verified=True).count()
   ```
4. Include `"verified_users": verified_users` in the `"kpis"` sub-dictionary.
5. In [backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html), render the new card:
   ```html
   <article class="analytics-kpi">
       <span>Verified Emails</span>
       <strong>{{ users_tab.kpis.verified_users }}</strong>
       <small>Accounts with confirmed institutional email</small>
   </article>
   ```
6. Run the test suite:
   ```powershell
   backend\core\venv\Scripts\python.exe backend\core\manage.py test modules.reports.test_superadmin_analytics
   ```
