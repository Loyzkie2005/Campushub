# Marketplace Admin Dashboard: final flat section layout ? October 23, 2026

## Current: one-row reporting controls and first-name welcome, October 26, 2026

### 1. Cause / reason

The user requested one row for the reporting controls/dates and removal of the last name from the Marketplace welcome. The prior reporting wrapper explicitly used `flex-direction: column`, which stacked metadata even on wide screens. The previous greeting used the full-name method. These are confirmed presentation causes, not backend filtering problems.

### 2. Exact files changed

- `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:16` updates the CSS cache version to `20261026-header-row`; line 40 (`marketplaceWelcomeTitle`) now reads `user.first_name|default:user.username`.
- `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css:1461` (`marketplace-reporting-controls`) uses a horizontally aligned wrapping flex row; line 1524 (`sales-overview__custom-dates`) orders the optional custom-date editor below the row with full flex basis; line 1533's mobile rule retains left alignment and wrapping. No shared stylesheet changed.
- `backend/core/modules/reports/test_marketplace_admin_dashboard.py:59` verifies the escaped first name appears without the fixture's last name. Existing username-fallback assertion remains.
- `docs/dashboard-marketplace-design.md` (this section) and `CAMPUSHUB_CONTEXT.md` (latest entry) record this refinement. Earlier full-name/stacked-header guidance below is superseded.

### 3. Changes made

The period dropdown, Refresh button, selected dates and Last Updated timestamp share one row when sufficient width exists. Small viewports wrap naturally without horizontal page overflow. The optional custom-date editor stays on its own row so it remains usable. The welcome includes the account's recorded first-name field, not its last-name field. Accounts without a first name still display their actual username.

### 4. How it works

No new function was added. The existing authenticated Django request still passes `user` and resolved period/time data to the same template. The template outputs only `first_name` with ordinary escaping and fallback. CSS changes only where existing rendered elements are placed. Inputs/outputs and data flow of the GET form, chart script and Refresh reload are unchanged.

Example: an account with first name `Lester` and last name `Bulay` now sees `Welcome back, Lester!`. The Last 30 Days value, Refresh, selected dates and timestamp line up on desktop. On a narrow phone they wrap instead of forcing the page sideways. This reuses the existing controls rather than creating another selector or reporting API.

### 5. Backend / API behavior

Unchanged: permissions, queries, date presets/custom validation, sales recognition, comparisons, snapshots, grouping, Refresh behavior, Apriori and all seven sections. No Super Admin or unrelated Marketplace page changed.

### 6. Database / migration impact

None. No models, migrations or working records were modified. Real working-account verification ran inside a PostgreSQL transaction explicitly reporting `transaction_read_only=on`.

### 7. Tests performed

- **63 Marketplace/shared Sales Overview tests passed in 49.325 seconds**, including the revised first-name/last-name/fallback assertions.
- Actual permission-checked dashboard view verified with the two existing Marketplace Admin account scopes (BSIT/BFPT), 18 period/grouping scenarios and **36 successful view responses**, including repeated GETs representing Refresh's server boundary. Real first-name output, one selector, selected dates/grouping, PHT and unchanged current snapshots passed. Existing recorded totals/chart data reconciled. Evidence: `scratch/marketplace-header-row-20261026/real-data-view-results.json`.
- **5,403 browser assertions passed across 93 page loads at seven widths (320–1920px)**, with no page overflow, missing assets or JavaScript errors. The harness directly measured overlapping vertical positions of the dropdown, Refresh, dates and timestamp at 1280/1440/1920px, confirming a shared desktop row rather than inferring it from CSS. Custom Apply, grouping and Refresh checks also passed. Final desktop screenshot was visually reviewed. Evidence: `scratch/marketplace-header-row-20261026/browser-results.json`.

### 8. Remaining limitations / troubleshooting / safe practice

The single row is responsive, not forced at widths where content cannot fit. Usernames are not guessed or split into names. A compound recorded first name remains intact. If old styles appear, reload and confirm the `header-row` asset version. If a last name still appears, inspect whether it was entered into the account's first-name field before assuming the template is wrong.

Real-data checks use Django RequestFactory with the actual permission-checked view and accounts, not authentication middleware. Signed-in real-server browser acceptance remains unavailable because the browser bridge is not installed and anonymous HTTP redirects to login. Fixture-browser checks do not replace that path. No overlapping pre-existing user work was staged or committed.

Safe practice: in a test account, set a distinct first and last name, open Marketplace Dashboard and confirm only the first appears. Resize from desktop to 390px and check the controls wrap without page scrolling sideways. Change Last 7 Days and grouping, then Refresh, confirming selected values survive without editing order or inventory records.

## Previous: approved Marketplace header and reporting controls, October 26, 2026

This approved presentation update supersedes earlier instructions placing reporting dates inside Sales Overview or displaying full Revenue comparison explanations inside the overview KPI. The seven sections, existing top grid, authorized data and business rules remain intact. The user approved the read-only inspection's nine-file plan before implementation.

### 1. Cause / reason

Confirmed: the Marketplace page started directly with Marketplace Overview, its date selector lived in the shared Sales Overview form, and Revenue's multiple supporting lines increased its Bootstrap row height alongside Total Orders. Super Admin provides the requested welcome/control presentation, but its global controller uses a different API/parameter format and depends on booking/services elements. Its presentation is reused, not its controller or permissions.

### 2. Exact files changed / current lines and anchors

| File | Current line / nearby anchor | Change and expected behavior |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 1 `load static tz`; 16 asset version; 38 `marketplace-dashboard-toolbar`; 40 welcome; 46 `salesPeriodSelect`; 49 conditional legacy option; 62 `salesCustomDates`; 67 selected dates; 68 `marketplaceUpdatedAt`; 147 compact comparison; 188–189 script versions | Authenticated welcome, relocated controls, actual dates/PHT response time, Refresh, one short Revenue supporting line. |
| `backend/templates/dashboard/partials/sales_overview.html` | 6 recognition subtitle; 13/32 `not marketplace_compact`; unchanged 25 grouping and 46/66 comparison details | Compact Marketplace alone omits its old date controls. Daily/Weekly/Monthly and full comparison information remain here. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 1433 header comment; 1434 toolbar; 1477 select; 1490 Refresh; 1509 focus; 1529 mobile breakpoint | Marketplace-only flex wrapping, executive-style Inter/navy text, white controls, metadata and mobile stacking. |
| `backend/core/modules/marketplace/static/marketplace/js/admin_marketplace_dashboard.js` | 2 Refresh lookup; 8 `window.location.reload()` | Reveals Refresh and reloads applied URL state. Existing chart functions remain below. |
| `backend/static/components/js/admin_sales_overview.js` | 5 comment; 6 `form.elements.namedItem` | Includes external form-associated controls without changing chart or submission behavior for existing callers. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | 52 real-name/single-filter test; 83 PHT test; 93 presets/grouping/snapshot test | Adds actual Django-response coverage for header, escaped authenticated identity/fallback, dates, period/grouping independence and compact KPIs. |
| `backend/core/modules/reports/test_sales_overview.py` | 161 `test_only_compact_marketplace_moves_date_controls_out_of_shared_sales_header` | Protects default, noncompact Marketplace and global shared-template callers. |
| `docs/dashboard-marketplace-design.md`; `CAMPUSHUB_CONTEXT.md` | This current section / latest entry | Required implementation, verification, troubleshooting and learning record. |

Verification scripts, before-file copies, fixture HTML/JSON, logs, screenshots and the session-only patch are under `scratch/marketplace-header-20261026/`, not runtime application code.

### 3. Changes made

The main-content header now shows the authenticated full name, falling back to username, and the requested Marketplace subtitle. Its controls use the existing values and Super Admin Refresh SVG/presentation. There is only one reporting-period selector. Revenue retains its prominent value, label and short percentage comparison, with the existing `&mdash;` entity for unavailable changes. Full prior amounts, dates, inclusive duration and explanations remain in the existing Sales Overview comparison area. Its subtitle explicitly retains completed-and-paid eligibility and recognition in the selected period.

The normal presets remain Today, Last 7 Days, Last 30 Days, Last 90 Days, This Month, This Year and Custom. Last 14 Days appears only if an already supported legacy 14-day request is active, avoiding an incorrect Today label. No resolver rule or new default preset was added. Existing date validation and legacy parameter precedence remain intact.

### 4. How it works: functions, inputs/outputs and data flow

The unchanged `admin_dashboard_page(request)` enters its authorized Marketplace branch and calls `_marketplace_operational_dashboard_data(request, user)`. This resolves the existing GET parameters and queries scoped data using Asia/Manila boundaries. The same `sales_period`, `sales_period_key`, `sales_grouping`, preserved hidden parameters and `dashboard_updated_at` reach the template. Django's inherited `user.get_full_name` supplies escaped real identity, or the actual username when names are empty.

The header displays resolved `sales_period.start/end`. The explicit `{% timezone "Asia/Manila" %}` block renders the existing response-generation timestamp in PHT with an ISO `datetime` ending `+08:00`. Its title states that this is response-generation time, not live synchronization or the time of the last underlying transaction.

The original GET form stays inside Sales Overview, preserving the chart script's `form.closest('.sales-overview')` dependency. Relocated fields use `form="salesOverviewFilters"`. The shared DOMContentLoaded handler now finds them through `form.elements.namedItem('period')`, rather than descendant-only lookup. Presets call the same `form.requestSubmit()`. Custom reveals the same inputs, focuses From and submits the same names through Apply. Grouping stays inside the form, so changing it includes the external reporting controls and preserved hidden parameters.

Marketplace's existing DOMContentLoaded handler reveals Refresh and registers a click listener calling `window.location.reload()`. This reloads applied URL state, including dates, grouping, unrelated parameters and any tab token. It does not submit unfinished edits, invoke a global API, trigger mining or announce success. Without JavaScript, normal Apply/Refresh fallbacks are provided and the JS button remains hidden.

Annotated example: `?period=custom&date_from=2026-10-01&date_to=2026-10-26&grouping=weekly` is the applied selection. Typing October 5 into From without Apply does not change that URL. Refresh still requests October 1–26 with weekly grouping. Apply instead submits the edited fields to the existing validator. This approach was chosen to keep one existing form and ordinary authorized navigation, rather than introduce another reporting pipeline.

### 5. Backend / API behavior

No runtime Python view/service, endpoint, permission or business-logic file changed. Total Orders, recent orders and completion-rate analytics retain their created-order cohort. Revenue, Marketplace Sales, Completed Orders, Average Order Value, Sales Trend and Top Products retain completed AND paid orders with positive quantity in the existing authorized sales queryset. Recognition remains completed_at, then paid_at, then created_at. Prior comparisons remain the immediately preceding equal-length period, including undefined averages and zero baselines.

Total Products, Pending Product Approvals, current inventory/attention, saved suggestions and all-time recommendation/activity information remain independently scoped. Explicit custom-date HTTP 400/fallback feedback stays visible. Super Admin files/global refresh, Apriori, forecasts, FIFO and fulfillment/payment workflows were not modified.

### 6. Database / migration impact

None. No model, migration, backfill, working-record edit, recommendation refresh or inventory operation was added or performed. Django tests used an isolated test database. Browser routes served test-rendered pages/local assets with zero working-database browser requests. A new working-table fingerprint audit was not performed and is not claimed.

### 7. Tests performed and observed results

- Initial regression run: **135 tests passed in 70.927 seconds**.
- Wider regression run: **276 tests passed in 110.263 seconds**. Coverage: Marketplace Admin, shared Sales Overview, Super executive/period/marketplace dashboards, FIFO inventory/concurrency, Orders, bundle monitoring/suggestions and inventory-report accuracy.
- After the final conditional legacy 14-day display adjustment: **4 focused header/shared-caller tests passed in 8.868 seconds**, including all preset/legacy/custom cases across Daily/Weekly/Monthly.
- Final Chromium harness: **5,364 assertions across 93 page loads**, using 13 real isolated Django-rendered states at **320, 390, 768, 1024, 1280, 1440 and 1920px**. Empty, zero-price/populated sales, grouping, comparisons, invalid dates and Top 5 were covered. No page overflow, missing assets or JavaScript errors. Browser interactions exercised custom Apply, preset/grouping submission, visible keyboard focus, and Refresh preserving applied URL/tab token rather than unfinished edits.
- Visually reviewed final 1440px desktop and 320px mobile screenshots. Four compact cards, balanced desktop bottom row, wrapped controls and all seven sections remain. Tables retain local scrolling. Long-name stress checks did not edit user records.
- Both changed JS files passed `node --check`. `backend/core/manage.py check` reported no issues. Source/diff checks and actual-result aggregation are in `scratch/marketplace-header-20261026/validation-summary.json`.

Reproduce with the existing environment:

```text
backend\core\venv\Scripts\python.exe scratch\marketplace-header-20261026\run-tests.py modules.reports.test_marketplace_admin_dashboard modules.reports.test_sales_overview modules.reports.test_dashboard_executive modules.reports.test_dashboard_periods modules.reports.test_dashboard_marketplace modules.marketplace.test_fifo_inventory modules.marketplace.test_fifo_concurrency modules.marketplace.test_orders_admin modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions modules.reports.test_inventory_report_accuracy
node scratch\marketplace-header-20261026\verify.cjs
```

### 8. Remaining limitations, debugging and safe practice

- Refresh is deliberately full-page navigation, not live/AJAX synchronization. New values/time appear when the server returns. The code does not label a failed navigation successful.
- Browser checks use actual test-rendered pages, local assets and Chromium viewport emulation, not a signed-in working-server session or physical devices. Fixture responses do not dynamically re-render backend data after each navigation. Actual backend filtering is tested separately with Django. Screen readers and an exhaustive accessibility audit were not exercised.
- The initial machine-wide Python command lacked Django. No dependency was installed. Use the existing `backend/core/venv/Scripts/python.exe`.
- If presets stop submitting, inspect the unique `salesPeriodSelect` ID, its `form` association and `form.elements.namedItem('period')`. Do not move the original form out of Sales Overview: the chart ancestor lookup depends on it. Check new asset versions if styles/scripts appear stale.
- Read existing custom-date errors and the explicit fallback label instead of assuming the requested range succeeded. Large names/amounts can still wrap naturally. No fixed clipping heights or unrelated grid redesign were added.
- No commit was created because the approved files overlap extensive pre-existing tracked and untracked user work. Nothing unrelated was staged/reset. `scratch/marketplace-header-20261026/session-only.patch` records only changes relative to the immediate pre-implementation copies.

Safe practice exercise: in a disposable test session choose Last 7 Days, then Weekly. Verify one reporting selector in the header and grouping inside Sales Overview, with both values in the GET URL. Choose Custom and edit From without Apply, then Refresh: applied dates should remain. Apply next and verify the displayed dates change while current product/approval counts do not. Do not run Apriori or change order records for this exercise.

## Previous: approved Marketplace Admin comparisons and validation — October 26, 2026

This update is confined to the existing Marketplace Admin Dashboard. All seven sections, 2×2 overview KPIs, Attention beneath them, right-hand saved recommendations, Sales Trend / Top 5, Recent Orders / Inventory Alerts and final activity feed remain in their existing order. It supersedes earlier Marketplace-only guidance that displayed an undefined average as zero or labelled an equal-length comparison as the previous calendar month/year.

### 1. Cause / reason

The existing average calculation safely returned a numeric zero for an empty denominator, but its display did not distinguish an undefined average from a genuine zero-price sale. The existing prior-period aggregate was already correct for an immediately preceding equal number of days, while presentation called it the previous month/year for those presets. Marketplace's custom-date resolver could raise uncaught calendar errors, silently swap reversed dates, and accept future or unbounded ranges. Top 5 already computed revenue and seller snapshots, but its accessible disclosure displayed only product and units.

Read-only inspection also confirmed that the top grid already avoids stretching. Its taller recommendations panel determines the row height, leaving natural space below the shorter left column. No structural change or forced equal card height is made.

### 2. Exact files changed / current lines and anchors

| File | Current line / code anchor | Purpose |
|---|---|---|
| `backend/core/modules/reports/views.py` | 178 `_sales_overview_summary`; 327 `_resolve_marketplace_sales_period`; 496 `_marketplace_operational_dashboard_data`; 564 `top_records`; 681 error response / 718 render status | Opt-in comparison metadata using the existing aggregate; Marketplace-specific date validation, Philippine timezone and authorized bounded seller lookup. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 16 CSS cache version; 62/78/94 snapshot/cohort notes; 112 revenue explanation and prior comparison | Explain current catalog, current approval queue, created-order cohort and recognized revenue without adding cards. |
| `backend/templates/dashboard/partials/sales_overview.html` | 7 `marketplaceDateRangeError`; 46 actual prior dates; 63 undefined-value guard; 66 comparison branch | Marketplace-only error, dates/duration, previous values, percentage and undefined-average display. |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_top_products.html` | 7 `if marketplace_compact`; 8 `marketplace-top-products-table` | Enrich the same disclosure with seller, units, revenue and authorized product link; keep other callers' two-column output. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 1393 `Compact context for the existing Marketplace metrics` | Scoped note spacing, readable comparison rows, inline error and horizontally scrollable disclosure. Override shared `column-reverse` only for these overview text containers so explanations follow their primary values. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | `test_marketplace_average_distinguishes_undefined_from_real_zero_and_positive`; comparison/date/boundary/Top 5 tests below | Isolated actual orders exercise empty, zero-price, positive and prior-period cases, invalid dates, local midnight, scope and ownership. Existing fixture exporter adds expected metadata for browser checks. |
| `backend/core/modules/reports/test_sales_overview.py` | 161 `test_marketplace_comparison_opt_in_preserves_legacy_summary_and_shared_output` | Verify default helper output and normalized shared-template output against saved originals; preserve Super Admin behavior. |
| `docs/dashboard-marketplace-design.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Record finalized behavior, verification, troubleshooting and limitations. |

No JavaScript, shared stylesheets, recommendation partial/service, Super Admin template, revenue service, permissions, order workflow or inventory service was modified. Verification helpers and artifacts live in `scratch/marketplace-analytics-enhancement-20261026/`.

### 3. Changes made

Marketplace Revenue and the three Sales Overview metrics show the previous amount/count and change. The actual comparison dates and inclusive duration are visible. A zero prior baseline displays an em dash instead of a growth percentage, with an explanation. Average Order Value displays an em dash when no eligible orders exist; a genuine completed-and-paid zero-value order still displays PHP 0.00. The existing mathematical formulas and legacy numeric fields remain unchanged.

Invalid custom ranges return HTTP 400 with readable feedback. The existing dashboard renders an explicitly labelled safe Last 30 Days fallback; its controls, labels and calculations all use that fallback. The message states that the requested range was not applied. Existing AJAX requests receive HTTP 400 and an `error` message. Valid presets, custom ranges and legacy `sales_days` precedence stay intact.

Validation reuses `resolve_dashboard_period`, whose already documented bounds are at most **3,661 inclusive days**, starting in **1900 or later**, with no future end date. It rejects missing/impossible dates and reversed ranges. It does not silently truncate, swap or interpret the invalid request as a valid custom range. This is the existing dashboard policy; the separate detailed Analytics parser's 3,651-day clamp is not changed here.

The existing Top 5 disclosure now shows Product, Seller, Units Sold and Sales Revenue, with right-aligned numbers. The chart, ranking and qualifying sales remain unchanged. Product links and missing-snapshot ownership fallbacks require an actual authorized product. Recorded seller names are preserved, even when the recorded name happens to be the literal text `Not Assigned`; absent ownership is never invented. Deleted product information is not reconstructed.

### 4. How it works — functions, inputs/outputs and data flow

`_resolve_marketplace_sales_period(request, today)` receives GET parameters and a Philippine-local date. For an effective custom request it invokes the existing dashboard validator, then delegates valid inputs to the original resolver. It returns `(period, key, days, error)`. Invalid input returns the safe 30-day period plus the validation message. This wrapper is called only by the Marketplace helper; the shared resolver remains unchanged for other roles.

`_marketplace_operational_dashboard_data(request, user)` retains canonical `scope_products`, `admin_order_queryset` and `valid_sales_queryset` calls. Its explicit Asia/Manila override keeps recognition and creation-date boundaries aligned with Philippine local days. It passes `marketplace=True` into `_sales_overview_summary`; other callers use the unchanged default.

`_sales_overview_summary(orders, period, total, count, marketplace=False)` still runs its single prior-period aggregate. With the opt-in flag it additionally returns `comparison.start/end/days` and each metric's `comparison.defined`, formatted `previous`, nullable percentage `change`, and explanatory `note`. The template uses this metadata; no second aggregate is added. Undefined average comparison is unavailable even if prior sales exist. Sales/count can still show a legitimate -100% when current activity is zero and the prior baseline is positive.

Example: current revenue PHP 300 from one eligible order, versus PHP 100 from two prior eligible orders, gives revenue +200%, order count -50%, and average PHP 300 versus PHP 50 (+500%). With zero current eligible orders, the average is undefined. An October 1–26 selection compares with September 5–30 (26 days), not September 1–26 or the entire previous calendar month.

Top 5 continues to use `top_selling_products(period_revenue)`. One additional authorized product query, capped by those five IDs, selects both web/mobile owners and checks saved seller evidence with `Exists` inside that SQL query. It does not issue queries for each row. No raw buyer information or out-of-scope product lookup is added. Django context flows into the existing page and partials; unchanged Chart.js scripts consume the same chart data.

### 5. Backend / API behavior

Revenue still requires Completed AND Paid with positive quantity and recognition timestamp `completed_at`, then `paid_at`, then `created_at`. Order totals and completion rate still use the creation-date cohort; completion includes cancelled orders in the denominator and remains independent of payment. Attention, saved recommendation counts/rates/analysis metadata, inventory, reservations, fulfillment/payment separation and recorded activities retain their existing services and datasets. Ordinary dashboard GET requests do not mine Apriori.

Valid AJAX payloads keep their existing fields, with additive Marketplace comparison metadata inside `sales_overview`. Invalid Marketplace custom requests now return HTTP 400 instead of an exception or silently changed range. Authorization, routes, scope and unrelated dashboards are preserved. The shared template guards use the existing Marketplace compact context; the helper opt-in is false elsewhere.

### 6. Database / migration impact

No models, migrations, activation, working stock/order writes or production data changes. Test orders/products live only in Django's disposable test database, which is destroyed after the run. Working-data verification uses PostgreSQL `SET TRANSACTION READ ONLY`. Protected source and database fingerprints are recorded beside the test/browser evidence.

### 7. Tests performed — actual results

- Initial targeted run: 59 tests, two errors because the optional `bs4` package was absent. Replaced those two new HTML checks with standard-library regular expressions plus Django's HTML assertions; no dependency was installed and no existing test coverage was removed.
- Final broader regression: **245 tests passed in 90.098s**, including `test_marketplace_admin_dashboard`, `test_sales_overview`, `test_dashboard_marketplace`, `test_dashboard_executive`, `test_dashboard_periods`, bundle monitoring, FIFO inventory, order administration and Super Admin Analytics. Django system check passed. The comparison test confirms one prior aggregate query; existing query-growth and scope tests remain intact.
- Final browser verification: **4,188 assertions passed across 93 renders** using only disposable-test-record HTML/JSON and local assets. Seven widths: 1920, 1440, 1280, 1024, 768, 390 and 320px. No page overflow, missing assets, JavaScript errors, mutation requests or working-database browser requests. Checks cover values, previous-period metadata, all seven sections, preserved recommendation controls, empty/populated charts, date/grouping controls, product disclosure keyboard behavior and inner scrolling. An initial successful geometry run missed the shared `column-reverse` text ordering; screenshot inspection caught it, and a scoped CSS correction plus explicit visual-order assertions were added. Final browser results are recorded in `browser-results.json`; desktop/mobile screenshots were inspected.
- All **231 protected source fingerprints** and **13 protected working-table fingerprints** match their pre-change values. Python syntax and added-line whitespace checks passed. No complete-project-suite, physical-phone or deployed-browser verification is claimed.
- Actual working scopes remain BSIT: 1 product, 0 created orders, PHP 0.00, unavailable completion rate; BFPT: 11 products, 1 created order, PHP 0.00, 0% completion rate. Both render HTTP 200; both averages and percentage changes are correctly unavailable. These checks are read-only and do not manufacture sales or analysis history.

Reproduce regression with `backend/core/venv/Scripts/python.exe scratch/marketplace-analytics-enhancement-20261026/run-tests.py` followed by the nine module labels above. Prepare and run the fixture browser checks with `prepare-browser.py` and `node scratch/marketplace-analytics-enhancement-20261026/verify.cjs`. Final totals and fingerprints are in `validation-summary.json`; logs retain initial failures separately.

### 8. Remaining limitations / troubleshooting / safe practice

Neither actual Marketplace Admin scope currently has eligible recorded sales, so positive/prior-baseline behavior is verified with isolated real model records, not invented working transactions. The top-row gap is retained intentionally; do not stretch cards or remove recommendation information to fill it. Missing historical seller/product evidence is not reconstructed. Unrelated detailed Analytics date-limit policy, workflow changes and other dashboards remain separate work.

If average shows zero instead of an em dash, check `comparison.defined` and the actual eligible count before changing the formula. If the KPI note appears above the value, inspect shared `.dashboard-stat-card > div { flex-direction: column-reverse; }` and the Marketplace-only override. If filters return HTTP 400, read the visible error, then select a valid preset or correct the custom range. Refresh cached CSS if comparison rows still clip.

Safe practice: on your authorized dashboard, select This Month and identify the displayed prior start/end and day count. Switch Daily to Weekly and verify the same reporting range and totals. Expand Top-Selling Products using Enter, inspect an existing authorized product, then collapse with Space. Do not create sales or alter stock to fill an empty chart. For comparison calculations, use the disposable test database and verify the PHP 300 / PHP 100 example above.

## Current: Marketplace Admin Sales Trend legend and empty data disclosure — October 26, 2026

This approved update applies only to the existing Marketplace Admin compact sales component. It supersedes earlier guidance that displayed its single-series legend or empty-period chart data table. Other dashboard components and the Super Admin sales component retain their existing output.

### 1. Cause / reason

The shared Sales Overview template rendered its HTML legend unconditionally and rendered the data disclosure for every non-global caller, even when the selected period had no qualifying orders. The backend correctly supplied zero-filled date buckets for empty periods, so expanding the disclosure exposed a redundant all-zero table. The actual chart already remained hidden and uninstantiated when there were no qualifying revenue orders. The centered empty state and requested wording already existed.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change |
|---|---|---|
| `backend/templates/dashboard/partials/sales_overview.html` | 80 legend guard; 94 disclosure guard | Wrap existing legend in `if not marketplace_compact`; render existing disclosure when `not marketplace_compact or sales_overview.has_sales`. No data or chart code changes. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | 459 review export; 466 empty/excluded case; 497 populated/grouping case; 530 zero-price case | Verify actual isolated order records, preserved shared-caller output, mixed zero/positive buckets, reporting boundaries, currency, chronological data and genuine zero-price sales. Optional HTML/JSON exports support browser verification without populating working data. |
| `backend/core/accounts/tests.py` | 477 shared `test_marketplace_admin_loads_dedicated_template_and_isolates_facilities` assertion | Replace the obsolete legend-presence expectation with absence; retain the existing revenue, product/order, role/scope and facilities-isolation assertions. This test is inherited by multiple dashboard test classes. |
| `docs/dashboard-marketplace-design.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Document finalized behavior, exact code/data flow, verification and safe exercise. |

Only two presentation conditions changed in runtime code. No CSS, JavaScript, asset versions, runtime Django views/services, APIs, permission rules, models, migrations, order/payment/FIFO workflows or unrelated sections changed. The shared test assertion was the sole necessary edit beyond the four originally proposed files.

### 3. Changes made

Marketplace Admin Sales Trend keeps its heading, date/grouping-aware subtitle, existing empty-state icon/title/text and populated chart. Its redundant **Marketplace Revenue** HTML legend is absent. For periods without qualifying orders, the **View chart data** disclosure and its table are absent. For qualifying periods, the same native disclosure remains collapsed initially and exposes the actual dates and peso amounts, including legitimate zero-revenue dates. The chart itself remains the existing one-series line chart with unchanged axes and tooltips.

The hidden canvas remains in the document in an empty period because the existing shared script uses it while binding reporting-period/grouping controls. It is neither displayed nor instantiated as an empty chart. This avoids unnecessary JavaScript changes and preserves the existing filter behavior.

### 4. How it works — functions, inputs/outputs and data flow

`_marketplace_operational_dashboard_data(request, user)` in `modules/reports/views.py` receives the authorized admin and selected period/grouping. Its unchanged `valid_sales_queryset(user)` selects scoped orders whose status is Completed, payment is Paid and quantity is positive. Its canonical timestamp uses completed time, then paid time, then creation time. The view applies the existing reporting boundaries and passes qualifying orders to `_sales_time_series()` and `_sales_overview_summary()`.

`_sales_time_series()` outputs ordered labels, revenue amounts and qualifying-order counts for each daily/weekly/monthly bucket, including zero days inside the selected period. The view formats table amounts with two decimal places and thousands separators. `_sales_overview_summary()` outputs `has_sales = count > 0`. That test is deliberately about qualifying orders, rather than positive revenue.

The Marketplace Admin template already passes `marketplace_compact=True`. The new guards use this existing caller flag and `has_sales` to control markup only. Super Admin enters the existing `executive_mode` branch, which includes its separate `super_marketplace_sales.html`. Other shared callers with the compact flag absent/false keep their legend/disclosure, including multi-series legends. No new flag, API or query is introduced.

Annotated example: a four-day selected period with one zero-price completed/paid order and one completed/paid sale of PHP 1,250.50 can produce revenue `[0, 0, 0, 1250.5]` and order counts `[0, 1, 0, 1]`. Its chart/table stay available and show **₱0.00** on legitimate zero days. A period with no qualifying orders has `has_sales=False`, so it shows the honest empty state instead of the table. Completed/unpaid, pending or processing/paid, cancelled/paid, delivered/unpaid and outside-period orders remain excluded.

Existing CSS supplies the intrinsic chart card, parent `align-items:start`, centered empty component and existing responsive stacking. The readable populated canvas height remains unchanged. The native `<details>/<summary>` retains its table caption and row/column header scopes; no additional interaction code is needed.

### 5. Backend / API behavior

Unchanged. Completed AND Paid eligibility, timestamp/date filters, Program/Major/seller scope, daily/weekly/monthly grouping, revenue sums, table ordering and numeric formatting are reused. The existing renderer still controls chart visibility and tooltip/axis formatting. Period/grouping controls continue to submit the selected GET parameters. No mining, order processing, payment, inventory or permission functionality was added or removed.

### 6. Database / migration impact

None. Regression records exist only in Django's disposable PostgreSQL test database. No working orders, recommendations, stock, audit history or other records are changed. Read-only before/after fingerprints cover 13 marketplace/inventory/audit tables. All 99 protected source fingerprints match, including the renderer, styles, views, analytics service and Super Admin partial; all 13 table fingerprints also match.

### 7. Tests performed — actual results

- **137 regression tests passed in 60.125s** across `modules.reports.test_marketplace_admin_dashboard`, `modules.reports.test_sales_overview`, `modules.reports.test_dashboard_marketplace`, `modules.reports.test_dashboard_executive` and `modules.marketplace.test_bundle_monitoring`. Tests cover role/scope boundaries, revenue exclusions, selected dates, populated/empty/zero-price cases and unchanged Super Admin/recommendation behavior. The initial run exposed an obsolete inherited legend expectation and an unformatted-total expectation in the new test; these were corrected without changing calculations or unrelated coverage.
- **804 browser assertions passed across 37 renders** (35 state/width combinations, plus daily loading and weekly navigation). Full results are recorded in `scratch/sales-trend-compact-20261026/browser-results.json` and `validation-summary.json`. Checks use isolated record-backed full dashboards for empty, zero-price, daily, weekly and monthly scenarios at **1920, 1440, 1280, 1024, 768, 390 and 320px**. They verify no empty Chart.js instance/table, exact empty text, populated chart data/labels, peso tooltips including zero, date tooltip, table values/header semantics, native collapsed disclosure, keyboard Enter/Space, focus, zero-date preservation, overflow and existing reporting/grouping controls. No fake working data or browser database requests are involved.
- Django system check passed. Template/Python compilation, scoped added-line whitespace, protected-source fingerprints and working-table fingerprints are checked by `final-check.py`. Desktop/mobile screenshots were inspected.

Reproduce: run `backend/core/venv/Scripts/python.exe scratch/sales-trend-compact-20261026/run-tests.py` with the five module labels above. After fixture export, run `prepare-browser.py`, then `node scratch/sales-trend-compact-20261026/verify.cjs`. Logs preserve initial and final outcomes; do not treat failed initial runs as successful tests.

### 8. Remaining limitations / troubleshooting / safe practice

No business-logic inconsistency was found in the inspected revenue path. Existing chart dimensions, date boundaries, rounding and grouping semantics remain. A completed/paid zero-price order intentionally keeps the chart/table available; an all-zero revenue line alone is insufficient evidence of an empty period. Existing unrelated Super Admin Refresh-button overflow at 320px is outside this Marketplace-only update.

If the legend remains visible, verify the caller passes `marketplace_compact=True` rather than hiding every legend globally. If a populated period lacks the disclosure, inspect the actual qualifying-order count and selected scope/date range. Do not replace `has_sales` with `total_sales > 0` or change revenue eligibility to fix presentation. If the chart fails to load, the existing error message and table fallback remain for qualifying periods.

Safe practice exercise: open Marketplace Admin Dashboard and compare two existing reporting periods, one empty and one populated. The empty period should have no chart disclosure; the populated one should open with Enter, list chronological peso values including zero days, and close with Space. Change daily grouping to weekly while retaining the date range. Use the isolated tests for zero-price and excluded-order cases; do not create working orders for a UI demonstration.

## Approved final compact dashboard — October 25, 2026

This section supersedes the earlier approval-statistics disclosure and category-chart dashboard presentation. It applies only to Marketplace Admin; Super Admin's existing output and functionality are preserved.

### 1. Cause / reason

Product Approval Statistics duplicated Products management. Seller Overview was already removed and was not recreated. Sales chart CSS at lines 1027–1086 overrode the original 70/30 rule with three chart columns, then made Sales Trend span a whole laptop row. The shared sales component rendered redundant No change comparisons when both periods were empty. Its two chart empty states also used different treatments. Recent Orders already received actual `item_count` values but did not display them.

### 2. Exact files changed / current anchors

| File | Current line / code anchor | Change |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 115 KPI closing block; 127 `marketplace_compact=True` | Remove only Product Approval Statistics HTML; pass a presentation flag to the existing sales partial. |
| `backend/templates/dashboard/partials/sales_overview.html` | 2 compact class; 54 sales label; 64 comparisons; 73 shared empty message; 86 empty state; 101 category include guard | Marketplace Sales label, one accurate empty-period message, preserve meaningful comparisons, reuse the shared empty-state component and omit category-chart display for this caller. |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_top_products.html` | 8 `marketplace_compact` | Match the Sales Trend empty-state component without changing ranking data. |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_order_inventory.html` | 13 headers; 19 `item_count` | Display existing Items values, use Buyer heading, preserve grouped order/date and product/seller, fulfillment, payment and existing links; empty row spans nine columns. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 1363 `.sales-overview--compact` | Scoped 65/35 chart grid, intrinsic height/alignment, centered compact empty states, existing 1199px stacking breakpoint. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | 378/391 category-output assertions; 409/425 new presentation/comparison regressions | Preserve category calculations while checking removed display, shared message, real percentage comparisons, item projection and unchanged component behavior for other callers. |
| `docs/dashboard-marketplace-design.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Current implementation, actual verification and limitations. |

No backend service, JavaScript, permission, model, migration, configuration or Super Admin template was edited. Verification-only scripts, isolated HTML, screenshots and logs are under `scratch/marketplace-compact-final/`.

### 3. Changes made

The existing seven sections remain. Four 2×2 Marketplace Overview KPIs lead directly into Attention on the left, with saved bundles on the right. Sales Overview contains three KPIs followed by Sales Trend / Top-Selling Products at 65/35 desktop proportions. Empty chart cards fit their actual content; narrow-screen text can wrap and the cards stack naturally. Recent Orders / Inventory Alerts keep their existing 70/30 proportions. Activities remain last. The existing category calculations and detailed Analytics remain available; only this dashboard's category-chart display is omitted.

### 4. How it works — functions, inputs/outputs and data flow

The unchanged `_marketplace_operational_dashboard_data(request, user)` receives actor scope and reporting/grouping parameters and returns the same real `marketplace` dictionary. `_sales_overview_summary(orders, period, total, count)` supplies metrics, comparison strings and `has_sales = count > 0`. The dashboard passes `marketplace_compact=True` only into the sales include. That flag changes presentation, not calculations or authorization. Other callers retain the previous branch; the Super Admin executive branch still renders its original dedicated partial.

For an empty selected period, the template displays **No completed and paid orders in the selected period.** once below the KPI group. It suppresses only redundant No change comparisons when no eligible orders exist. Annotated example: previous-period sales of PHP 100 versus zero current sales legitimately produce **-100.0%**, which remains visible. Conversely, a genuine zero-price Completed AND Paid order still counts as an eligible order; it does not receive the no-orders message. Offset/date handling remains with the existing backend and renderer.

`recent_marketplace_orders(...)` already returns `item_count`; the table reads it directly. Unknown/unresolvable counts display an em dash. No quantity is inferred from product names or fabricated. Existing chart JSON, date/grouping controls, chart data disclosures, payment/fulfillment separation and saved-only Apriori readers remain unchanged.

### 5. Backend / API behavior

Revenue still requires Completed AND Paid through the existing canonical queryset. Product approval calculations, pending approval KPI/attention links, seller management, actor/Program/Major boundaries, recommendation rates/workflows, order/payment statuses and FIFO remain unchanged. Category data stays in the existing context for current consumers; no service is deleted. No new endpoint or dashboard-loading mining operation was added.

### 6. Database / migration impact

None. Before/after fingerprints match all 12 protected marketplace/inventory tables. Read-only real-page rendering returned 200 for current Marketplace Admin actors 9 and 14. The current database retains 14 batches, 344 available units and 1 reserved unit, with FIFO enabled. No working transactions, opening balances or sample records were created. Test fixtures ran only in Django's disposable test database.

### 7. Tests performed — actual final results

- **105 tests passed in 40.600s:** Marketplace dashboard, saved recommendations, sales overview and Super Admin executive regressions. Covers the shared no-sales message, preserved -100% comparisons, true zero-price eligible orders, unchanged category calculations and original shared-component behavior.
- **88 tests passed in 36.187s:** FIFO inventory, Orders, inventory-report accuracy, dashboard marketplace data and reports. These selections may overlap inherited tests; they are not reported as a unique combined count.
- **556 browser assertions / 29 renders**, widths **1920, 1440, 1280, 1024, 768, 390 and 320px**. Verified the seven-section layout, removed disclosures, direct KPI/Attention spacing, 70/30 overview, 65/35 sales charts, responsive stacking, actual sales-series values, separate fulfillment/payment, Items header, saved previews, one shared empty message, centered empty states, chart-data keyboard access, retained grouping/period and focus indicators. No horizontal page overflow, missing assets or JavaScript errors. Browser requests used isolated rendered fixtures and never reached the working database. Desktop and mobile screenshots were inspected.
- Django system check passed. Real scoped rendering and PostgreSQL read-only inventory checks passed. Initial test/harness failures were corrected: ContextList extraction, zero-price-order expectations, CSS-transformed header text and an arbitrary mobile height threshold. Final empty-card checks measure actual unused height rather than penalizing necessary readable text wrapping.

Reproduce: `backend/core/venv/Scripts/python.exe scratch/marketplace-compact-final/run-tests.py modules.reports.test_marketplace_admin_dashboard modules.marketplace.test_bundle_suggestions modules.reports.test_sales_overview modules.reports.test_dashboard_executive`, followed by `node scratch/marketplace-compact-final/verify.cjs`. Test logs, fixtures, screenshots, protected-table fingerprints, `live-read-results.json` and `browser-results.json` are in that directory.

### 8. Remaining limitations / troubleshooting / safe practice

Wide Recent Orders and Inventory Alerts tables retain contained horizontal scrolling. A taller populated recommendation card can determine the top group's overall height; Attention itself stays intrinsic and is not stretched to fill it. Missing historical fulfillment and unknown item counts stay honest. Existing actual activity types and actor information are preserved; unsupported events are not invented. Synthetic recommendation research stays separate.

If changes do not appear, refresh the page to pick up the updated dashboard CSS version. Verify that only the Marketplace Admin include passes `marketplace_compact=True`; do not change global sales styles or Super Admin templates to resolve a local layout issue. Keep Django expressions on one physical line when formatting the HTML.

Safe practice exercise: open the dashboard at 1440px and 390px; verify Attention follows KPIs and the charts move from 65/35 to stacked. Open View chart data with Enter and compare the existing values with the plot. Use the isolated regression to exercise empty/current-versus-previous periods; do not create working orders or alter payments to populate charts.

## Approved seven-section dashboard and template repair — October 25, 2026

This report supersedes the earlier eight-topic layout below. Only Marketplace Admin presentation was changed; Super Admin remains the visual reference and retains its own content.

### 1. Cause / reason

Confirmed by template compilation: several Django `{% ... %}` and `{{ ... }}` expressions had been split across physical lines. Django raised `TemplateSyntaxError: Invalid block tag on line 65: 'endif'`. The KPI/statistics region also sat outside the existing 70/30 Attention/recommendations grid. Bootstrap `col-xl-3` created four desktop KPI columns. Seller Overview repeated application information already accessible in Seller Applications; pending applications already feed Attention Required.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 44 `marketplace-dashboard-top`; 45 `marketplace-summary-left`; 49 `col-12 col-sm-6`; 148 `marketplaceActivityTitle` | Repair broken template expressions, group KPIs/statistics/Attention on the left, retain saved bundles on the right, remove Seller Overview markup. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 1184 top margin; 1188 left Attention; 1351 `marketplace-summary-left` | Intrinsic left-column sizing, consistent 16px internal gap, remove redundant bottom margin. Existing 70/30 proportions and 1199px stacking breakpoint stay intact. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | `test_widgets_navigation_empty_states_and_super_api_protection`; `test_final_layout_orders_sections_and_links_existing_destinations` | Check the seven-section order and absence of Seller Overview; preserve assertions for actual scoped application data and existing links. |
| `docs/dashboard-marketplace-design.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Record current behavior, verification and limitations. |

The combined approved task also changes Seller Applications files; its complete file list and implementation explanation are in the latest section of `docs/mobile-seller-application.md`.

### 3. Changes made

Desktop now groups the four KPI cards in two rows, with closed-by-default Product Approval Statistics and Attention Required directly below. Suggested Product Bundles occupies the right column. On narrower screens the existing grid stacks KPIs/statistics, Attention, then bundles. Sales Overview follows the intrinsic height of the top group. Recent Orders / Inventory Alerts retain their existing 70/30 grid, followed by Recent Marketplace Activities. Seller Applications management and backend seller counts were retained.

### 4. How it works — functions, inputs/outputs and data flow

`_marketplace_operational_dashboard_data(request, user)` in `modules/reports/views.py:463` continues to accept the authenticated actor and current reporting/grouping GET parameters. Existing scope helpers select actual products, orders, application counts and audit events. It outputs the same `marketplace` dictionary; `valid_sales_queryset(user)` still requires Completed AND Paid and supplies the existing recognition timestamp. The template only rearranges where that dictionary is rendered. Saved Apriori previews continue through `dashboard_bundle_suggestions(user)` without running mining during dashboard GET.

Example: a saved delivered/unpaid order still appears with independent delivery and Unpaid information in Recent Orders. Moving Attention above Sales never changes its reservation, payment, completion or recognized revenue. CSS `align-items: start` keeps the recommendations card at its natural height when Product Approval Statistics opens.

### 5. Backend / API behavior

No dashboard service, endpoint, chart renderer, filter calculation, recommendation workflow or permission rule changed. Existing scoped product/order/analytics/Inventory links remain. Seller Overview was removed from HTML only; its shared data/services were not deleted.

### 6. Database / migration impact

No models, migrations, settings, opening balances or working records changed. Real-page rendering was performed inside `SET TRANSACTION READ ONLY`. Fingerprints for all 12 protected marketplace/inventory tables match before and after: 14 batches, 344 available units and 1 reserved unit; FIFO remains enabled. The available balance already excludes held stock and must not have the reservation subtracted again.

### 7. Tests performed — actual results

- Targeted seller/dashboard/recommendation selection: **88 tests passed in 28.664s**.
- Broader overlapping regression selection: **311 tests passed in 127.281s**, including reporting/exports, orders, seller permissions, variants, bundles, receiving, cancellation restoration and PostgreSQL FIFO concurrency.
- Combined browser verification: **685 assertions / 74 renders**, widths **1920, 1440, 1280, 1024, 768, 390 and 320px**. Verified 2-column KPI placement, desktop 70/30 top proportions, narrow-screen ordering, no horizontal page overflow, existing chart rendering/data/tooltips, filters, links, empty states and Seller Applications drawer behavior. No missing static resources or browser JavaScript errors. Both review POST checks were intercepted; no browser request reached working records. Desktop/mobile screenshots were inspected.
- Both current Marketplace Admin actors (9 and 14) render Dashboard and Seller Applications with status 200 using real records under PostgreSQL-enforced read-only transactions. Django system check and seller JavaScript syntax check passed.

Reproduce with `backend/core/venv/Scripts/python.exe scratch/seller-dashboard-drawer-final/run-tests.py` and `node scratch/seller-dashboard-drawer-final/verify.cjs`. Logs, isolated HTML, screenshots, hashes and browser results are in `scratch/seller-dashboard-drawer-final/`. Test records exist only in the disposable Django test database.

### 8. Remaining limitations / troubleshooting / safe practice

No new activity types, recorded receipt events, sales or recommendations were invented. Empty production scopes remain honestly empty. Wide preview tables retain contained horizontal scrolling. A sidebar or header link remains subject to the original backend permission rules. Matching actor names do not establish account identity; see the seller guide's findings.

If `Invalid block tag` returns after formatting, inspect the preceding `{% if %}`/`{% include %}` and keep each complete Django expression on one physical line. Do not alter permissions to mask template errors. If styles appear stale, reload the page; asset query versions changed only for the touched styles.

Safe practice exercise: open Product Approval Statistics, observe actual counts, and verify the Suggested Product Bundles card does not stretch. Close it and resize to 390px; KPIs, Attention and bundles should stack in that order. Do not submit orders, reviews or receiving transactions for this layout exercise.

## Approved final dashboard integration ? October 25, 2026

This section supersedes earlier two-by-two KPI placement, recommendation-summary wording and sales-report creation-date expectations below. The eight existing topics are retained; no module was rebuilt.

### 1. Cause / reason

The old top grid placed two-by-two KPIs beside recommendation counts and put Attention Required afterward, including on mobile. Recent Orders omitted existing fulfillment/payment information. Inventory Alerts omitted held quantities. The saved-recommendation summary lacked a product preview. Its shared renderer could still describe sales as pickup-only after Seller Delivery was introduced. Sales Reports dated revenue by placement while dashboard/Analytics used completion/payment, so an order crossing reporting periods could disagree.

### 2. Exact files and current anchors

| File | Current line / anchor | Purpose |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 41 `marketplace-kpis`; 106 `marketplace-dashboard-top`; 122 seller caption; 129 `event.url` | Four desktop KPIs, existing permission-aware links, Attention before saved bundles, truthful seller-count explanation, authorized activity links. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 610 `Final operational dashboard` | Reuse the 70/30 grid with `align-items:start`; contained table scrolling, navy badges and focus; charts retain existing sizes. |
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html` | 5 `dashboard_preview` | Marketplace-only saved preview, explicit empty/unavailable states, existing counts/rates and one View Recommendations action. Other callers keep their existing presentation. |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_order_inventory.html` | 11 `marketplace-table-scroll` | Maximum-five order preview with ID, customer, product/seller, total, fulfillment, order status, payment, date and existing Details link; Available and Reserved inventory columns. |
| `backend/core/modules/reports/views.py` | 463 `_marketplace_operational_dashboard_data`; 506 `alert_products`; 574 `event_reference` | Reuse canonical inventory snapshots; attach links only to existing authorized records. |
| `backend/core/modules/reports/dashboard_marketplace.py` | 47 `recent_marketplace_orders` | Add the existing fulfillment presentation under a new `fulfillment` key; preserve older fields consumed elsewhere. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py` | 40 `dashboard_bundle_suggestions`; 84 `preview` | Read at most the latest three saved scoped suggestions; reuse eligibility; emit only JSON-safe product ID/name/image and existing response information. Never mine during GET. |
| `backend/templates/dashboard/partials/sales_overview.html` | 6 marketplace subtitle | Cover both recorded fulfillment methods; other branches retain existing text. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 48 sales subtitle | Correct pickup-only explanatory wording; no Analytics calculations or layout changes. |
| `backend/core/modules/reports/reporting.py` | 150 `_order_report`; 484 sales description | Sales preview/CSV/PDF reuse `valid_sales_queryset` and its recognition timestamp; Orders Report remains dated by placement. |
| Existing tests | `test_marketplace_admin_dashboard.py`, `tests.py`, `test_sales_overview.py`, marketplace `test_bundle_monitoring.py` / `test_bundle_suggestions.py`, `accounts/tests.py` | Delivery/payment independence, exact-variant holds, saved-only previews, scope, links, recognition-date exports, approved labels/order and existing permission behavior. |

### 3. Changes made

Desktop now reads four KPIs, Attention / Suggested Product Bundles, Sales Overview, Recent Orders / Inventory Alerts, Seller Overview, then Activities. The existing 1199px stacking threshold is retained. At smaller sizes, KPIs precede Attention, then bundles. Unlike KPI alignment, content cards are not forced to equal heights. The date is grouped under its order ID to keep all requested information in a compact preview. Wide tables scroll within their own regions, with visible keyboard focus. Inventory headers use the existing smaller header scale; two seller-review controls remain on one line rather than artificially doubling row height.

A historical blank fulfillment method displays **Not recorded**. A delivered/unpaid order shows its actual delivery progress plus **Unpaid / Awaiting payment**; rendering never completes or pays it. Approved dashboard applications continue to exclude suspended access; the caption explicitly distinguishes this from all reviewed-approved applications in the application-management page.

### 4. Functions, inputs/outputs and data flow

`_marketplace_operational_dashboard_data(request, user)` accepts existing reporting filters and the authenticated actor. Existing scope helpers select products/orders/applications first. The five alert rows determine a bounded product set. `active_inventory_reservations(product_ids=...)` expands real recorded bundle-component holds; `get_product_inventory_snapshot(product, reservation_rows=...)` returns available/reserved totals and exact variant rows. Matching `variant_key` supplies each alert's Reserved cell. Unresolvable historical selections return `None`, displayed as an em dash rather than a fabricated zero.

`recent_marketplace_orders(orders, limit=5)` continues to sort by placement and primary key. Its additional `fulfillment` dictionary comes from the shared `presentation(order)` reader. Existing order-status values are unchanged; the new table uses the presenter's delivery-aware label. Order IDs and Details reuse `admin_orders_page?order=<actual ID>`.

`dashboard_bundle_suggestions(user)` reads saved live records. It checks the latest three through existing `presentation` / same-owner eligibility. Names/IDs/images are explicitly projected, avoiding Decimal/internal evidence leakage. A saved count with no eligible recent preview says **No Eligible Preview**, not that no saved recommendations exist. The detailed workspace remains the destination for all saved suggestions.

`_order_report('sales', start, end, user)` now filters the canonical completed-and-paid, positive-quantity, scoped queryset on `analytics_at = Coalesce(completed_at, paid_at, created_at)`. The row Date, chart and range use that same timestamp. `build_report` feeds the unchanged preview/export routes, so CSV and PDF inherit identical eligible rows. `_order_report('orders', ...)` still uses `created_at`.

Annotated example: an order placed September 30 and completed/paid October 2 belongs to October recognized revenue. It remains a September placement in Orders Report. A delivered but unpaid October order belongs to neither recognized-revenue total nor its export.

### 5. Backend / API behavior

No new endpoint, date filter, approval operation or recommendation-generation request was added. Existing Django permissions, academic scope, seller ownership, FIFO allocation/restoration and payment/fulfillment transitions remain unchanged. Activity URLs use existing scoped records; unsupported receiving/delivery event types are not invented or backfilled into AccountActivity.

### 6. Database / migration impact

No models, migrations, activation settings or working marketplace records are changed. Verification uses a PostgreSQL test database or explicit read-only transactions. Existing starting-stock unknown receipt dates are preserved. Test fixtures and intercepted browser writes do not reach the working database.

### 7. Verification

Final executed results are recorded in the verification record below. Evidence directory: `scratch/marketplace-sellers-final/`. This includes before-edit copies, protected-table fingerprints, test logs, isolated HTML fixtures, browser assertions and desktop/mobile screenshots. A reused test database had lost seeded roles/programs after previous transactional tests; the final broader run recreates only the verified `test_campushub` database so seeded assumptions can be tested honestly.

### Final executed verification record

- **Django regression:** 309 tests passed in 124.197 seconds; process exit code 0. Includes marketplace dashboard/Analytics, seller applications, reports/CSV/PDF, orders/permissions, exact variants, bundle components, stock receiving, original-batch cancellation restoration, seller isolation, idempotency and PostgreSQL FIFO concurrency.
- **Final focused rerun:** 7 tests passed in 4.111 seconds after the final table grouping/copy changes; process exit code 0. These also regenerated browser fixtures from actual isolated Django records.
- **Browser:** 439 assertions passed across 60 renders at 1920, 1440, 1280, 1024, 768, 390 and 320px. Checked populated/empty and weekly/monthly dashboard states, seller pagination/filter states, no horizontal page overflow, KPI/section layout, existing charts, actual chart-series/tooltip/table values, grouping-period preservation, keyboard disclosure/focus, debounced search, combined filters, retained pagination query and failed-review recovery. Both approval/rejection POSTs were intercepted; working-database browser requests: 0. No missing static resources or browser JavaScript errors. Desktop/mobile screenshots were inspected.
- **Working read-only checks:** both actual Marketplace Admin scopes returned HTTP 200 for Dashboard and Seller Applications. BFPT has 11 products / 1 period order / PHP 0.00 recognized revenue; BSIT has 1 product / 0 period orders / PHP 0.00. Their Sales Reports match the dashboard. Zero saved recommendations is actual data.
- **Preservation:** before/after fingerprints match all 12 protected product/application/order/inventory/bundle tables: 15 products, 1 application, 1 pending/unpaid order, 14 batches, 1 allocation, 16 SKUs and 12 stock movements. Batch `remaining_quantity` is already available stock; summing it gives **344 available**, with **1 reserved** tracked separately in allocations. Do not subtract reserved allocations from that available total again. Order `2026BSKJHRNM`, its one-unit reservation and all unknown opening receipt dates remain intact. FIFO stays active; no working migrations or cutover ran.
- **Checks:** Django system check and seller JavaScript syntax check passed. Scoped added-line whitespace check passed. Local Django restarted with the existing FIFO configuration and normal read/write transaction default; no working transactions were submitted.
- **Test setup:** fresh isolated runs recreate `test_campushub`, never `campushub`. Existing recommendation tests now prepare the real unmanaged Room/Booking/Payment/Feedback model tables outside their class transaction so Super Admin navigation tests work from a fresh test database. This is test preparation, not an application schema or Facilities workflow change.

Reproduction: `backend/core/venv/Scripts/python.exe scratch/marketplace-sellers-final/run-tests.py` runs the 309-test selection and exports isolated HTML. `node scratch/marketplace-sellers-final/verify.cjs` runs browser checks with local bundled assets and blocked real mutations. Test logs and `browser-results.json` contain the actual results; no test production records are needed.

### Complete changed-file inventory for both approved requests

This inventory is relative to the user's working files before this task, not to Git's existing large dirty state. The inactive module seller template is unchanged. Lines identify the first changed anchor; the feature tables above explain behavior.

| File | Current line / first changed anchor |
|---|---|
| `CAMPUSHUB_CONTEXT.md` | 2 `approved update` |
| `backend/core/accounts/tests.py` | 470 `self.assertContains(response, "Marketplace Revenue")` |
| `backend/core/accounts/views.py` | 258 `"user", "user__department", "user__major", "mobile_user", "mobile_user__department", ` |
| `backend/core/api/test_mobile_seller_application.py` | 2 `import os` |
| `backend/core/modules/marketplace/services/bundle_suggestions.py` | 70 `from .bundle_monitoring import activity_summary, recommendations_for, presentation` |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 609 `approved update` |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 15 `<link rel="stylesheet" href="{% static 'marketplace/css/admin_marketplace_dashboard.c` |
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html` | 5 `{% if dashboard_preview %}` |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_order_inventory.html` | 11 `<div class="marketplace-table-scroll" role="region" aria-label="Recent marketplace or` |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 23 `# Super Admin navigation tests read these existing unmanaged models too.` |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 235 `anchors = ['id="marketplaceOverviewTitle"', 'id="dashboardAttentionTitle"', 'id="mark` |
| `backend/core/modules/reports/dashboard_marketplace.py` | 49 `from modules.marketplace.services.fulfillment import presentation` |
| `backend/core/modules/reports/reporting.py` | 151 `if report_type == "sales":` |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 48 `<p>Completed and paid marketplace orders</p>` |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | 262 `self.order_pending.fulfillment_method='seller_delivery'` |
| `backend/core/modules/reports/test_sales_overview.py` | 74 `def test_sales_recognition_date_filter_keeps_orders_report_on_creation_date(self):` |
| `backend/core/modules/reports/tests.py` | 248 `def test_sales_chart_page_serializes_actual_eligible_series(self):` |
| `backend/core/modules/reports/views.py` | 470 `from modules.marketplace.services.inventory import (` |
| `backend/static/components/css/admin_sellers.css` | 1 `/* Seller Applications: existing institutional surfaces and intrinsic table rows. */` |
| `backend/static/components/js/admin_sellers.js` | 2 `const filters = document.querySelector('.seller-filters');` |
| `backend/templates/dashboard/partials/sales_overview.html` | 6 `<p>{% if marketplace %}Completed and paid marketplace orders{% else %}Completed and p` |
| `backend/templates/marketplace/pages/admin_sellers.html` | 8 `<title>CampusHub  /  Seller Applications</title>` |
| `backend/templates/partials/admin_sidebar.html` | 67 `<span class="item-label">Seller Applications</span>` |
| `docs/dashboard-marketplace-design.md` | 2 `approved update` |
| `docs/mobile-seller-application.md` | 2 `approved update` |
| `docs/web-ui-ux-guidelines.md` | 9 `Latest explicit page choices still apply. The October 24 request removes the Super Ad` |

QA-only tools: `scratch/marketplace-sellers-final/snapshot.py` hashes actual protected tables in a read-only transaction; `run-tests.py` runs Django only against its verified disposable `test_campushub`; `verify.cjs` serves isolated exported HTML/static assets, intercepts mutation requests and saves screenshots. None is imported by the application. Generated logs/JSON/HTML/PNG files are verification artifacts.


### 8. Limitations and troubleshooting

No eligible sales or saved recommendations in the working scope is a legitimate empty state; do not seed production to populate the dashboard. The bounded preview examines the latest three saved suggestions; the workspace exposes the full authorized list. Existing AccountActivity remains the activity source, so seller progress recorded solely in order-status history and FIFO receipts recorded solely in stock history are not synthesized into audit events.

If recognition totals disagree, compare actor scope, completed **and** paid status, positive quantity and recognition dates. Orders count uses placement dates and is intentionally a different cohort. A Reserved em dash means existing selections could not establish a trustworthy hold; inspect existing Stock Movements rather than manually adjusting quantities. Inspect `marketplaceSalesChartData` on the detailed Analytics page and `revenueChartData` on the operational dashboard; they are different existing data elements.

Safe practice: run the recognition-date regression in the isolated test database, find the `RECOGNIZED-NOW` row in its generated report, and compare it with the Orders Report exclusion. Then inspect the dashboard's read-only `fulfillment` dictionary and confirm that changing the dropdown/grouping does not write payment, fulfillment or stock fields. Use test fixtures only; never submit demonstration receipts/orders against working inventory.


## Current: final operational and analytics audit — October 24, 2026

### 1. Cause / reason and existing working features

The requested audit found a largely complete dashboard. Its six existing areas already cover the requested eight topics: product performance is in Sales Overview, recommendations are in the top companion card, and recent orders share a row with inventory. Creating eight separate new sections would duplicate working components.

| Requested capability | Existing implementation / outcome |
| --- | --- |
| Marketplace Overview | Four scoped KPIs: products, pending product approvals, placed orders and eligible sales. Retained. |
| Attention Required | Actual pending products/orders/seller applications, low/out-of-stock inventory and unshared saved suggestions. Existing filtered management links retained. |
| Sales Analytics | Completed/paid revenue, completed paid transaction count, AOV and selected-period revenue line. Retained. |
| Product Performance | Top-five product bars and table, quantities/revenue, category revenue donut/table, exact variant stock alerts. Retained. |
| Seller Management | Existing approved/pending/suspended application counts and Sellers navigation. Labels clarified because these count application rows, not distinct people. |
| Suggested Product Bundles | Saved current suggestions and sent/awaiting/created activity, one detailed-workspace link. Actual pairs, seller, response and existing authorized operations remain on that workspace. Dashboard GET does not mine. |
| Recent Orders | Five actual authorized orders; each opens the existing Orders page filtered to that order. Retained. |
| Recent Marketplace Activities | Five latest authorized marketplace audit events, including supported recommendation events. Authentication/Facilities events are excluded by existing scope helpers. Retained. |

Confirmed gaps were missing visible order-status/completion and recommendation response/conversion summaries, plus incomplete current product-approval statistics. These use existing data without new workflows. Confirmed data-display bugs: pending/inventory seller labels read only the web seller relationship, so mobile-owned products could show Unknown Seller; Seller Overview called application-row counts Approved/Suspended Sellers.

### 2. Exact files changed

Paths are relative to the repository root; anchors remain useful when lines move.

| File / current line | Anchor / change |
| --- | --- |
| `backend/core/modules/reports/views.py:463` | `_marketplace_operational_dashboard_data`: extend existing product aggregate; expose a period-specific order-status/completion projection; resolve labels with existing `Product.owner` and both seller joins. |
| `backend/core/modules/marketplace/services/bundle_monitoring.py:61` | `activity_summary(..., include_rates=False)`: optional distinct sent-recommendation rate counts folded into the existing aggregate; default response contract retained. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:80` | Marketplace Admin branch requests optional rate data from the existing saved-record helper. Super Admin branch unchanged. |
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html:12` | Expandable response/creation rates, actual numerator/denominator and all-dates basis. Existing four counts/action/errors retained. |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_order_inventory.html:4` | Expandable selected-period order status counts and completion rate inside Recent Orders. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:97` | Expandable current product approvals, honest application labels and all-dates seller/activity captions; CSS cache key at line 13. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css:600` | Compact native details/summary styling scoped to Marketplace Admin, Inter inheritance, 44px summary targets, wrapping and keyboard focus. |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py:65` | Period/cohort/zero/scope/approval tests; mobile owner labels and actual management-link GETs at line 88. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:82` | Distinct-rate, multiple bundle, unsent, outside-scope, zero-denominator and default-caller compatibility tests; rendered rates checked. |
| `docs/dashboard-marketplace-design.md:3` | This audit/report, formulas, limitations and safe exercise. |
| `CAMPUSHUB_CONTEXT.md:3` | Latest scoped audit decision and guide reference. |

Review artifacts: `scratch/marketplace-final-audit-review/` contains isolated rendered pages, source data and `verify.cjs`; logs are named below. No live demonstration records were inserted.

### 3. Changes made

Preserved the six-area layout, outside headings, individual chart cards, existing navigation and recommendation names. Added three **collapsed native details controls**, not new major sections: product approvals under the existing top KPIs, order-status/completion inside Recent Orders, and response/bundle rates inside Marketplace Recommendations. No new decorative graph or operational button was added.

Seller Overview now says Approved Applications / Suspended Applications, matching `SellerRequest` row counts. A repeated application is not silently presented as an additional distinct seller. Existing aggregation and pending application behavior are unchanged.

### 4. How it works — formulas and data sources

All resources keep existing Seller/Product Program/Major scope. Buyer affiliation is not used. The dashboard view prepares context, templates display it, and unchanged Chart.js scripts render the same existing datasets. Reporting changes submit the existing GET form, re-rendering period-dependent data and charts together.

| Value | Source and formula / reporting basis |
| --- | --- |
| Revenue | `valid_sales_queryset(user)` in `services/analytics.py:109`: completed + paid + quantity > 0; sum recorded `total_price`, filtered by existing `analytics_at = Coalesce(completed_at, paid_at, created_at)`. |
| Completed Orders | Count eligible revenue rows in that revenue period; this is not every completed-but-unpaid record. |
| AOV | Revenue / eligible completed paid rows; zero rows returns PHP 0.00 via existing `_sales_overview_summary`. |
| Product/category performance | Existing shared helpers use that same eligible revenue queryset; category recorded snapshot falls back to surviving Product category. No current-price recalculation. |
| Placed orders / new status distribution | `admin_order_queryset(user)`, limited by `created_at` to the selected dates. Counts actual existing status choices. Existing lifetime `order_status` context remains compatible; the new display uses `period_order_status`. |
| Completion rate | Current completed-status rows among orders **placed** in the selected period / all orders placed in that period, including cancellations, times 100. This is fulfillment, not collected revenue. No orders returns an em dash. |
| Product approvals | Existing non-archived scoped Product aggregate gains approved/rejected alongside total/pending. Current snapshot, independent of reporting dates. |
| Seller application counts | Existing scoped SellerRequest approved/non-suspended, pending, approved/suspended row counts. Current status, all dates. |
| Seller Response Rate | Distinct sent recommendations with a saved dismissal or actual linked created bundle / distinct sent recommendations, times 100. Creation and dismissal together count once. |
| Bundle Creation Rate | Distinct sent recommendations with at least one actual linked bundle / distinct sent recommendations, times 100. Multiple bundles from one suggestion cannot inflate the percentage. |
| Bundles Created count | Existing actual linked bundle-product count; deliberately separate from converted recommendation count. |
| Recommendation rates / activities | Saved scoped history across all dates; no new response-time/date-cohort rule inferred. Zero sent means both rates are unavailable, not a fabricated 0% success rate. |

`activity_summary(user, include_rates=True)` takes the same authorized actor and existing status annotations (`_created`, `_dismissed`). It adds conditional counts to the existing aggregate and returns a separate `rates` dictionary. Its default remains False, so other saved-workspace and Super Admin callers keep their existing output. Existing database errors remain errors; the UI hides unavailable rates instead of inventing zero measurements.

Illustrative arithmetic only: three sent suggestions, one with two linked bundle products, one dismissed and one awaiting response yield response rate 66.7%, creation rate 33.3%, and Bundles Created = 2. This distinction is tested in the isolated database; no example is seeded into production.

This approach reuses saved records, eligibility, aggregation and scoped management routes. One grouped period-status query is added; rate and approval counts extend existing aggregates. Seller joins are batched, preserving bounded previews and avoiding per-row label lookups.

### 5. Backend / API behavior

No routes, roles, permissions, statuses, approval/sending/creation actions or Apriori algorithm changed. The HTML context gains the three supported summaries. Existing revenue AJAX response keys and the global dashboard API remain compatible. Saved recommendation reads remain read-only; explicit analysis endpoints retain their existing behavior. The generation path requires live results; the dashboard does not load the research CSV or trigger `build_bundle_suggestions`.

### 6. Database / migration impact

No models, fields, migrations, schema changes, application records, environment changes, deployment or restart. Tests use isolated Django records and rollback. Marketplace orders are existing sellable-product rows, not a newly invented OrderItems or checkout-group model.

### 7. Tests executed and results

- **352 regression Django tests passed** across every reports `test_*.py` module plus bundle monitoring/suggestions and Orders administration. Log: `scratch/marketplace-final-audit-regression.log`.
- **4 overlapping final targeted tests passed** after the final display-label/assertion edits: cohort/approval/zero-scope behavior, mobile-owner labels and management-link GETs, distinct recommendation rates/rendering, and fresh populated/empty fixture export. Log: `scratch/marketplace-final-audit-final-targeted.log`. These are not four additional unique tests beyond the regression set.
- **81/81 DOM/chart checks passed** in `scratch/marketplace-final-audit-review/verify.cjs`: preserved six areas/70-30/four KPIs/one recommendation action, three real chart configurations, period cohort/status/approval counts, native details placement/target size, paid-revenue/category reconciliation and chart-library-error/table fallbacks. Existing empty states remain covered.
- Django system check: no issues. Marketplace chart JS syntax check passed. Versioned Marketplace CSS served HTTP 200 with SHA-256 matching source.
- Native browser visual interaction and responsive pixels were not verified. Rendered HTML and Chart.js configuration tests do not prove canvas appearance or browser interaction.

### 8. Remaining blockers and safe practice

The current order schema has no refund ledger or universal demo/test provenance flag. Existing completed/paid rules cannot subtract an unrecorded refund or distinguish a manually inserted fake production row. Saved recommendation records also lack a source-provenance column: the existing live-only generation path is verified, but arbitrary manually imported rows cannot be independently classified by this dashboard. No source field, refund model or guessed filter was invented for this UI audit.

Recommendation response means saved dismissal or linked creation; there is no unsupported read/accepted event. These are current saved outcomes, not response latency or causal proof of a promotion's effectiveness. Product approvals and seller applications are current snapshots; activity and recommendations are all dates. The UI states these bases explicitly. Rounded percentages may differ from exact fractions.

Capstone readiness still requires a real-browser walkthrough on the defense device and a check of its actual deployment/data provenance. Automated checks cover the selected modules, not the entire CampusHub application. Existing application/workflow coverage is not a claim that every external integration is available.

Safe practice: expand the three new details controls in development and compare their displayed numerators/denominators with the period and labels. Use `python manage.py test modules.reports.test_marketplace_admin_dashboard modules.marketplace.test_bundle_monitoring --keepdb --noinput` with the project's interpreter from `backend/core` for isolated checks. Do not create fake live orders to populate screenshots. If styling is stale, Ctrl+F5 and check `admin_marketplace_dashboard.css?v=20261024-defense-audit`. If a rate is an em dash, first check whether any authorized recommendations were actually sent; zero is not a database or CSS failure.

---

## Earlier flat-layout report — October 23, 2026

The report below describes the preserved layout. The October 24 audit above is the latest feature and verification record.

## 1. Cause / reason

Inspection confirmed the existing dashboard already has the required real metrics, saved recommendation summary, academic scope, selected-period revenue/AOV, chart data and operational previews. The layout gaps were visual: Marketplace Overview's heading sat inside the left grid column, the shared Sales Overview component painted one large white outer surface, and recommendation subtitle/empty explanations made its summary unnecessarily tall.

Only the requested Marketplace Admin presentation is refined. The user's brief ends at ?Do not invent?; no additional unwritten requirements or sections are assumed.

## 2. Exact files changed and current anchors

| File | Line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 15, local stylesheet; 36, `.marketplace-overview` | Existing heading/subtitle moved above the 70/30 row, four existing cards retained in a 2?2 desktop grid. Local dashboard CSS loads after shared sales CSS. Asset version: `20261023-flat-sections`. |
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html` | 1, recommendation section | Keeps title, four saved counts and existing View Recommendations link; removes normal subtitle and verbose zero-state explanations. Existing unavailable/error messages remain. |
| `backend/templates/dashboard/partials/sales_overview.html` | 2, conditional `sales-overview--dashboard` class | Adds a Marketplace context marker to the existing component; existing metric loop, form, chart IDs and other branches are retained. |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 530, overview heading; 586, flat section styles | Transparent, borderless Sales Overview wrapper; external heading/filter row; individual white KPI/chart surfaces. Old inner separator borders replaced by whole chart-card borders. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 229 / 386, saved-summary and zero-summary tests | Updates only Marketplace Admin expectations for the newly compact card. Existing no-mining, totals, errors, permissions and separate Super Admin behavior stay tested. |
| `docs/dashboard-marketplace-design.md` | 1, this report | Current explanation, file map, tests and learning exercise. |
| `CAMPUSHUB_CONTEXT.md` | 3, latest layout note | Records this latest presentation decision. |

## 3. Changes made

Exactly six dashboard areas remain in order: Marketplace Overview; Attention Required; Sales Overview; Recent Orders + Inventory Alerts; Seller Overview; Recent Marketplace Activities. Sales Trend, Top-Selling Products and Sales by Product Category remain content cards within Sales Overview, not additional dashboard modules.

Marketplace Overview's heading is outside the content cards and above both columns. Its plain semantic wrapper adds no painted parent card. The desktop layout remains approximately 70/30, with four existing KPI cards in two columns and two rows; existing small-screen stacking remains.

Sales Overview is now a quiet section on the page background. Its heading, subtitle and existing right-side date/grouping controls are outside the white surfaces. Total Sales / Completed Orders / Average Order Value retain their individual cards; each existing chart now has its own white surface and subtle border. The existing responsive chart arrangement is preserved. The Sales wrapper adds no border, background, padding or shadow.

Marketplace Recommendations shows only its title, four requested summary counts and the existing navigation action during normal operation. Zero is an honest numeric state. Failed reads still show unavailable values and existing error text; errors are not disguised as zero.

## 4. How it works: existing functions and data flow

No backend function was added or edited. `_marketplace_operational_dashboard_data(request, user)` still supplies actual Product counts, scoped orders, SellerRequest summaries, inventory/attention, saved recommendations and AccountActivity rows. `valid_sales_queryset(user)` and `_sales_overview_summary` remain the existing revenue and AOV inputs. Sales = the existing eligible recorded paid totals in the selected period; Completed Orders = the count from those same records; AOV = Sales / Completed Orders, or zero when there are none.

Existing `scope_products`, `scope_seller_requests` and order-access helpers still use supported Seller/Product Program + Major relationships. No buyer affiliation is introduced into scope. `dashboard_bundle_suggestions` still reads saved recommendations/activity, without Apriori generation on GET.

The shared template receives the same context dictionary and emits the same metric values, form fields and chart-data IDs. It adds only a conditional CSS class. The local `.marketplace-dashboard` selectors make the wrapper transparent and style existing direct chart children. Existing JavaScript still locates the same sales form/canvas and draws the same real datasets; its source is unchanged. The ordinary recommendation template omits explanatory text but preserves all four saved values, em dashes for unknowns and error messages.

Data path remains PostgreSQL ? existing models/helpers/scope ? existing Django context ? existing shared template and local styles ? existing chart scripts. Super Admin, Analytics, Seller pages and Flutter receive no new selectors or behavior.

Example for understanding: when the existing helper returns no eligible completed orders, its Average Order Value remains ?0.00. The updated template only changes which surface contains that value; CSS does not calculate or replace it.

## 5. Backend / API behavior

Unchanged. Existing `/admin-dashboard/` and `/admin-bundle-suggestions/` URLs, authorization gates, filter submission, order links, recommendation actions, supported statuses and workflows are preserved. No models, fields, routes, roles, permissions, new charts, new KPIs, approval/rejection logic or new calculations were introduced. Shared Sales template markup changes are conditional, and the new styling requires the existing Marketplace Dashboard body class.

## 6. Database / migration impact

None. No schema changes, migrations, production data, sample records, inventory changes, environment edits, deployment or service restart. Render fixtures were produced through existing isolated Django tests.

## 7. Tests performed

- **117 Django tests passed**: scoped Marketplace Admin dashboard, sales overview, saved bundle monitoring/suggestions, web typography and domain Analytics permissions. Existing tests cover scope/other buyers, eligible totals, safe zero AOV, saved read-only recommendations, error values, route protection and Super Admin separation. Log: `scratch/marketplace-flat-sections-tests.log`.
- **70/70 Marketplace DOM/style/chart checks passed**: six-area order; heading outside the top row/cards; four top KPIs; four recommendation counts and one action; Sales heading/filter placement; sales/orders/average metric order; transparent, zero-border/padding Sales wrapper; three individual white chart surfaces; existing chart configs, empty states and failure tables. Run `node scratch/marketplace-flat-sections-review/verify.cjs`. Styles are checked against local/shared CSS in the actual intended cascade order.
- **26/26 existing Super Admin summary-chart DOM checks passed**, verifying its separate layout and shared chart behavior remain intact.
- `manage.py check`: no issues. Scoped whitespace checks clean. Localhost serves the versioned dashboard CSS with HTTP 200 and a raw-byte SHA256 matching the workspace.
- CUA inventory has no apps or browsers. DOM/computed-style tests use jsdom and Chart stubs; no actual browser screenshot, responsive pixel or canvas-rendering claim is made.

## 8. Remaining limitations, troubleshooting and safe practice

Browser appearance and native interactions still need visual verification. Existing schema/payment/provenance limitations documented in the earlier data report remain unchanged; this presentation update neither adds missing information nor invents replacement values.

If the old outer card persists, use Ctrl+F5 and inspect the `20261023-flat-sections` stylesheet URL. Marketplace-specific CSS is now loaded after the shared sales stylesheet and uses the explicit dashboard scope. If a recommendation read fails, follow the existing View Recommendations link to inspect the saved workspace; dashboard refresh intentionally does not run Apriori.

Safe learning exercise: inspect `sales-overview--dashboard` in the template and the matching CSS at line 586. Temporarily change only the individual chart-card padding from 20px to 18px, then run the DOM verifier and inspect the layout locally if a browser is available. Restore 20px afterward. Do not edit revenue, scope or database records to practice spacing. For data safety, run the existing zero-AOV test in Django's isolated test database rather than creating live orders.

---

# Marketplace Admin: Sales by Product Category ? October 23, 2026

This addition supersedes only the earlier instruction to omit a dashboard category chart. The old catalog-count donut remains removed; this is a selected-period **sales revenue** donut. The user's final layout code block was empty, so the existing sales performance area is reused rather than creating a separate dashboard module.

## 1. Cause / reason

The dashboard already calculated scoped category sales but did not display them. The detailed Analytics adapter separately grouped the raw category field and lacked the existing snapshot-to-product fallback. Reusing the existing revenue/category helpers keeps the new donut reconciled with the Sales KPI and Analytics.

## 2. Exact files changed, current lines and anchors

| File | Current line / code anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_marketplace.py` | 94, `category_sales_chart` | Pure presentation adapter over the existing category revenue summary; top five plus Others, bounded to six slices |
| `backend/core/modules/reports/views.py` | 474 import; 566 `category_sales_chart` context key | Exposes the existing selected-period eligible category sales through that adapter |
| `backend/core/modules/marketplace/services/analytics.py` | 258, `_category_sales` | Reuses `sales_by_product_category`, including recorded category / current Product fallback |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_category_sales.html` | 1, section | New small chart section, exact requested title/subtitle, always-available data table, empty/error states |
| `backend/templates/dashboard/partials/sales_overview.html` | 98, marketplace-only include | Places the new chart in the existing sales performance component |
| `backend/core/modules/marketplace/static/marketplace/js/admin_marketplace_dashboard.js` | 36, `renderCategorySales` | Existing Chart.js renders a donut; category, peso amount and share tooltip; independent failure handling |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 567, selected-period category styles | Three chart columns on wide screens; full-width trend with bar/donut pair on medium screens; stacked below 1200px |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 13 / 129, versioned asset links | Cache version `20261023-category-sales` |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py` | 286, category tests | Scope/eligibility/date/parity, bounded Others and zero-sales regressions |
| `docs/dashboard-marketplace-design.md` | 1, this report | Current explanation and verification |
| `CAMPUSHUB_CONTEXT.md` | 3, latest category note | Preserves the latest layout/source decision |

## 3. Changes made

Added **Sales by Product Category** with subtitle **Share of marketplace sales by product category for the selected period.** It uses the existing Inter/navy/gold/neutral palette, white chart surface, and no extra navigation action. The revenue line, top-product bars and category donut share the existing Sales Overview area. At narrower desktop widths the trend spans the row and bars/donut sit below; small widths stack.

Categories are ranked by actual eligible revenue, not catalog listing counts. Up to five positive-revenue categories are shown individually, with remaining revenue combined into Others when there are more than five. Maximum is six slices. A real catalog category named Others is folded into the one Others slice only when grouping is necessary, avoiding duplicate identical legend labels. Zero revenue produces **No Category Sales Yet**, not a 100% placeholder slice.

The tooltip contains the actual category name, formatted PHP amount and percentage. The table below the chart exposes the same values without relying on hover or color. If Chart.js fails, the table remains and the chart-unavailable message appears.

## 4. Functions, inputs / outputs and data flow

`valid_sales_queryset(admin)` remains the canonical completed + paid + positive-quantity revenue query. Its existing `scoped_marketplace_orders` / `scope_products` boundary uses Seller/Product Program + Major, never buyer affiliation. Dashboard filters its existing `analytics_at` timestamp by the selected period.

The existing `sales_by_product_category(period_revenue)` performs the aggregate query. Category comes from the recorded order category first, then the current Product category for legacy blank snapshots, then Uncategorized only if both are missing. This preserves the category recorded at sale time and avoids hard-coded catalog names.

`category_sales_chart(summary, limit=5)` accepts that already-grouped summary, does **zero database queries**, and returns bounded category rows plus Chart.js labels, numeric values, percentages and colors. It sums the remainder using Decimal, and divides each displayed amount by the **full eligible revenue**, not the top-five subtotal. Currency strings remain formatted server-side; chart numeric values are presentation values.

`_category_sales(period_orders)` now maps the same shared full category summary into the existing Analytics response structure. Analytics still receives all categories; the dashboard adapter alone applies the slice limit. The shared query/filter and revenue totals do not change.

Example for learning only: if isolated test orders contain revenue of 700, 600, 500, 400, 300, 200 and 100 across seven categories, total sales is 2,800. The donut shows five named categories and Others = 300, whose share is 10.7% of 2,800. This example is not inserted into the application database.

Schema detail: the existing checkout stores each sellable product on `MarketplaceOrder`; there is no separate authoritative OrderItem model. Each row has quantity, unit_price and recorded total_price. We preserve the existing recorded paid `total_price` used by Sales KPI/Analytics rather than recalculate a different amount from current catalog prices or incomplete legacy unit prices. For ordinary unchanged unit pricing this equals quantity ? selling price; recorded totals retain existing checkout pricing decisions. No new parallel revenue calculation was introduced.

Data flow: PostgreSQL order/product records ? existing scoped eligible revenue query ? selected dates ? shared category aggregation ? pure top-five/Others adapter ? Django JSON/table ? Chart.js tooltip and donut. Date/grouping changes use the existing form submission, so category totals update with the other dashboard values. No Apriori or CSV data is consulted.

## 5. Backend / API behavior

Existing routes, filters, role permissions and recommendation generation remain unchanged. The dashboard context gains one presentation dictionary. Analytics category rows gain the same legacy fallback and normalization already used by the shared category helper. No new endpoint, controller, polling system or frontend revenue calculator was added.

## 6. Database / migration impact

None: no models, migrations, live records, fixture imports, environment changes, deployments or server restarts. Tests use Django's isolated test database. Synthetic Apriori data remains separate from operational models. The existing order schema has no refund ledger or general demo/test-record flag; this chart applies the same existing eligibility rules as the KPI and cannot infer unrecorded refunds or distinguish manually inserted fake production rows.

## 7. Tests performed

- **86 focused Django tests passed**: Marketplace Admin dashboard, shared category/product summaries, sales overview, and bundle monitoring. Log: `scratch/marketplace-category-sales-tests.log`.
- **25 further Analytics/permission/typography tests passed**: existing Analytics calculation tests (excluding its three previously documented unrelated stale copy/permission/source-string assertions), domain Analytics access and web typography. Log: `scratch/marketplace-category-analytics-tests.log`. Combined: **111 tests passed**; no full-suite claim.
- **51/51 DOM/chart-configuration checks passed** against isolated test-rendered populated/empty pages: donut type, maximum slices, labels/amounts, reconciliation, tooltip name/PHP/share, accessible table, zero-data behavior, independent Chart.js failure fallback, and existing revenue/bar/table layout. Run `node scratch/marketplace-category-sales-review/verify.cjs`.
- `manage.py check`: no issues. Changed Marketplace JS passes `node --check`; scoped whitespace check is clean. Updated Marketplace CSS/JS served by the already-running localhost server return HTTP 200 with raw-byte SHA256 values matching the workspace.
- Actual browser/screenshot verification was unavailable: CUA inventory returned no apps/browsers. No server, app or worker was launched or restarted.

## 8. Remaining limitations, troubleshooting and safe practice

Browser inventory is empty, so responsive pixels, actual canvas appearance and native pointer/keyboard behavior were not visually verified. DOM checks inspect actual test-rendered HTML and stubbed Chart.js configuration, not screenshots. Rounded shares can sum to 99.9% or 100.1%; exact amounts in the table still reconcile.

If the chart is empty, check the selected period and recorded completion/payment status before changing categories. If blank order snapshots show Uncategorized, inspect the corresponding Product category. If the old layout persists, Ctrl+F5 uses the new versioned dashboard assets. A library/network error retains the category table and shows a clear message.

Safe exercise: run the isolated Others regression, then read its `assertNumQueries(0)` block to see that grouping is presentation-only:

```powershell
cd backend/core
.\venv\Scripts\python.exe manage.py test modules.reports.test_marketplace_admin_dashboard.MarketplaceAdminDashboardTests.test_category_donut_caps_slices_and_reconciles_others_without_extra_queries --keepdb --noinput
```

Change only a category name inside this test fixture and rerun it, then restore the test. Keep the expected total unchanged; this teaches why category labels must not control eligible revenue. Do not add practice orders through the live admin page.

---

# Marketplace Admin Dashboard ? real data and operational layout (October 23, 2026)

This report supersedes the older Marketplace Admin live-mining dashboard description. Historical Super Admin typography/layout notes below still apply to that separate page.

## 1. Cause / reason

Inspection confirmed that most dashboard numbers already used real models and academic scope. The gaps were specific: the recommendation helper ran Apriori on every Marketplace Admin dashboard GET; inventory preview omitted zero stock; previews contained 6?8 rows; dashboard donuts and tables repeated deeper Analytics; Analytics could include legacy multi-item snapshots excluded by Orders; and monthly Analytics silently used August?December instead of the selected reporting range.

The update uses existing services and the requested seven-part layout. It does not rebuild Marketplace, add a recommendation page, change Apriori, or create demonstration records.

## 2. Exact files changed and code anchors

Paths are relative to the repository. Current lines below point to the relevant function or component, rather than every edited line.

| File and current line | Nearby anchor / purpose |
| --- | --- |
| `backend/core/modules/marketplace/services/order_access.py:6` | `scoped_marketplace_orders(user)` shares the product-based order boundary; `admin_order_queryset` retains its permission gate |
| `backend/core/modules/marketplace/services/analytics.py:109` | `valid_sales_queryset` reuses that boundary for completed/paid revenue; `build_marketplace_analytics` at line 619 keeps all grouping within the selected period and uses the same order boundary for status counts |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:40` | `dashboard_bundle_suggestions` reads saved scoped recommendation counts; no Dashboard Apriori call |
| `backend/core/modules/reports/views.py:463` | `_marketplace_operational_dashboard_data` assembles scoped summaries, five-row previews, current inventory and bounded audit activity |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:36` | `marketplace-dashboard-top`: 70/30 KPI/recommendation row, then Attention, Sales, Orders/Inventory, Sellers, Activities |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_order_inventory.html:1` | Existing order URLs and stock rows rendered in five-column / three-column tables without a nested scrollbar |
| `backend/core/modules/marketplace/templates/marketplace/partials/dashboard_top_products.html:1` | Top-five vertical bar chart, honest empty state, exact accessible data table |
| `backend/templates/dashboard/partials/sales_overview.html:8` | Existing shared sales component gains `data-revenue-only` for this dashboard, retains AOV and date controls |
| `backend/templates/dashboard/partials/attention_required.html:15` | Marketplace-specific No Items Require Attention title and requested explanation |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css:528` | Scoped operational layout, Inter typography, neutral tables, wrapping and focus styles |
| `backend/core/modules/marketplace/static/marketplace/js/admin_marketplace_dashboard.js:1` | Existing Chart.js dependency now draws only the top-product vertical bar chart, with failure fallback |
| `backend/static/components/js/admin_sales_overview.js:11` | `revenueOnly` draws one Marketplace Revenue line and omits the order-count axis entirely |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html:8` | Marketplace Admin title becomes Marketplace Analytics; Super Admin retains Analytics |
| `backend/core/modules/reports/test_marketplace_admin_dashboard.py:232` | Database-backed revenue/grouping parity, unrelated buyer, legacy isolation, five-row stock/order/activity limits and timestamp tests |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:95` | Saved counters, no mining/writes on GET, recommendation audit visibility |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:229` | Dashboard expectations use saved records; live/research API algorithm tests retained |
| `backend/core/modules/reports/test_sales_overview.py:130` | Shared sales component still tested; obsolete donut layout expectations replaced |
| `backend/core/modules/reports/tests.py:232` | Monthly Analytics now explicitly tested against the selected reporting period |
| `backend/core/accounts/tests.py:479` | Dedicated Marketplace dashboard regression expects no Order Status donut |
| `docs/suggested-product-bundles.md:3` | Latest saved-dashboard-source note supersedes earlier live-summary description |
| `CAMPUSHUB_CONTEXT.md:3` | Latest implementation context and verification pointer |

## 3. Changes made

The KPI grid stays on the left (70%) and Marketplace Recommendations on the right (30%). The dashboard then shows Attention Required; Sales Overview; revenue trend beside top products; Recent Orders beside Inventory Alerts; Seller Overview; and Recent Marketplace Activities. At narrower widths the columns stack. White surfaces, existing Inter, navy, neutral borders and modest radii preserve the institutional design.

Removed dashboard-only category/order-status donuts, separate pending-product table, full-width Marketplace Reports button and extra deep-analysis previews. Detailed Analytics, sidebar Reports ? Analytics / Generate Reports and the existing recommendation workspace remain available. The saved summary still uses one View Recommendations action and the existing role-specific naming.

Recent Orders has Order Number, Customer, Total Amount, Status and Date, with the number opening the existing authorized Orders workspace. Inventory has Product, Available and Status, with zero-stock entries before low stock. Exact variant labels are retained. Both previews show at most five rows. Sales Trend has a single revenue series and Revenue (?) axis; top products use a vertical Units Sold bar chart. Empty ranges hide the chart instead of drawing invented activity.

## 4. How it works: functions, inputs, outputs and data flow

`scope_products(queryset, user, prefix=...)` in `accounts/academic.py:114` remains the shared academic boundary. Explicit Product Program/Major takes precedence; absent Product Program falls back to its web/mobile seller. Invalid/missing required scope fails closed. `scope_seller_requests` handles web/mobile applications. Buyer Program/Major is never used to decide ownership scope.

`scoped_marketplace_orders(user)` accepts an authenticated admin and returns the academically scoped order queryset. Non-superusers cannot see legacy multi-item JSON with no enforceable item-owner relation. `admin_order_queryset` still requires existing Orders permissions. Analytics uses the same resource boundary under its existing Analytics permission gate; neither route grants a new role or permission.

`valid_sales_queryset(user)` filters the shared order base to completed, paid and positive quantity. It annotates `analytics_at = completed_at ? paid_at ? created_at` using the existing fallback order. Dashboard and Analytics then filter the same selected dates and sum `total_price`, count eligible orders and bucket those records using `_sales_time_series`. Existing `_sales_overview_summary` supplies AOV and comparisons: AOV = revenue / eligible completed-order count, or ?0.00 when the denominator is zero. Monthly grouping no longer substitutes a separate semester range.

The existing schema stores one sellable product per `MarketplaceOrder`; there is no separate authoritative OrderItem table. `top_selling_products(period_revenue, limit=5)` sums `MarketplaceOrder.quantity` grouped by product, including variants under their parent. It does not treat unverified JSON snapshots as OrderItems or expand bundle components as additional sales.

`low_stock_inventory_rows(products, limit=5, include_out_of_stock=True)` reuses existing simple/variant inventory, expiry and configurable-threshold rules. No stock is deducted by dashboard reads. Seller counts come from scoped SellerRequest status and suspension flags. Product counts, seller counts and inventory/attention are current operational snapshots; order counts/revenue/rankings are selected-period values. The top caption makes this distinction explicit.

`dashboard_bundle_suggestions(user)` reads saved `BundleRecommendation` records through `recommendations_for(user)`. Suggested counts current saved pairs; sent/awaiting/created reuse `activity_summary` and real linked bundle products. These are saved workspace/history totals, independent of the sales date filter. They can remain visible when the selected sales period has no orders. Unshared current saved suggestions link to the existing review workspace in Attention. Generation remains an explicit existing operator action, and the live/research calculators themselves are unchanged. A failed recommendation read shows an unavailable value, never a fabricated zero.

Activities combine the existing resource-scoped marketplace audits and authorized saved-recommendation audits, newest first, limited to five. Authentication events stay excluded. Current-year timestamps use `Oct 23, 8:20 PM`; older years include the year. Recommendation-audit lookup failure preserves the normal scoped activity feed; recommendation errors remain visible in the summary.

Data path: PostgreSQL ? existing Product / MarketplaceOrder / SellerRequest / BundleRecommendation / AccountActivity models ? shared scope and eligibility helpers ? dashboard dictionaries / Analytics detail dictionaries ? Django templates ? existing Chart.js. No extra frontend revenue calculator or duplicate controller was introduced.

Annotated example: an eligible ?300 BSIT-seller order placed by a BFPT buyer contributes ?300 revenue, one completed order and ?300 AOV to the BSIT admin's selected period. Changing its payment status to unpaid in an isolated test removes it from all three sales metrics and the revenue/product charts, while it can still appear as an actual operational order.

## 5. Backend / API behavior

Existing page and AJAX endpoints, route names, seller highlight actions, order details, authorization and Apriori endpoints remain in place. Dashboard GET now reads saved recommendation results and performs no mining or writes. The Dashboard and Analytics share order scope and revenue eligibility. Existing Super Admin recommendation preview and seller workflows are preserved. Technical Support/Confidence/Lift values are not exposed in the ordinary dashboard.

## 6. Database / migration impact

No model changes, migrations, production/test-data seeding, inventory adjustments, environment changes, deployments or service restarts. Fixtures were created only in Django's isolated test database. Synthetic research data remains a separate CSV/calculator path and is never imported by Dashboard KPIs, counts or inventory.

The current MarketplaceOrder schema has no refund ledger or general-purpose demo/test-record flag. This change preserves the existing accounting rule (completed + paid); it cannot infer refunds or identify manually inserted fake operational rows without an authoritative record. Cancelled/unpaid orders are excluded. Do not insert demonstration orders into a production operational database; use the isolated test database or existing research CSV tools.

## 7. Verification

- **416 Django tests passed**, final broad run: all `modules/reports/test_*.py` modules; bundle monitoring/suggestions; order administration; domain Analytics permissions and Marketplace order access; account Activity API, Monitoring and user-management scope; and the updated selected-period monthly Analytics regression. Log: `scratch/marketplace-real-data-regression.log` (Ran 416 / OK). Old assertions expecting live mining, extra rows and removed donuts were updated to the explicit new requirements; calculation, scope, read-only and permission assertions remain.
- **37/37 Marketplace DOM/chart-configuration checks passed** using isolated rendered populated/empty fixtures, one revenue dataset, no second axis, product bar values, table columns/limits/links, empty states, and Chart.js-unavailable fallbacks. Run `node scratch/marketplace-real-data-review/verify.cjs`.
- **26/26 existing Super Admin summary-chart DOM checks passed**, verifying the shared chart change preserves its single revenue series and existing other charts. Run `node scratch/dashboard-final-review/verify_summary_charts.cjs`.
- Django `manage.py check`: no issues. Both changed JavaScript files passed `node --check`. Scoped whitespace checks passed.
- Changed Marketplace CSS, Marketplace chart JS and shared sales JS each returned HTTP 200 from the already-running localhost server, and their raw-byte SHA256 values matched the workspace. No server was started or restarted for verification.
- Browser inventory returned no available apps/browsers. No screenshot or responsive-pixel claim is made. Test fixtures and verification tools are under `scratch/marketplace-real-data-review/`; they are not production data.

## 8. Remaining limitations, troubleshooting and safe practice

Browser inventory is empty in this session, so no actual desktop/mobile screenshots, responsive pixels or native keyboard interactions were verified. DOM checks validate markup and chart configuration with Chart stubbed; they do not prove canvas rendering. The existing detailed Analytics legacy test module has three previously documented unrelated copy/permission/source-string failures; this change does not weaken permissions or change its detailed chart script to satisfy stale expectations.

If recommendations show zero, open the existing Recommendations workspace and check whether live results have previously been explicitly generated/saved. A dashboard refresh intentionally does not generate them. Confirm Program/Major assignments on products and sellers rather than changing buyer affiliations. If charts are unavailable, the exact data tables and summary values remain usable; check that the existing Chart.js resource loaded. If old layout persists, hard-refresh: changed dashboard CSS/JS URLs use `v=20261023-real-data`. Three served assets were checked against workspace bytes; see final verification results below.

Safe exercise: run the specific parity test in the isolated Django test database:

```powershell
cd backend/core
.\venv\Scripts\python.exe manage.py test modules.reports.test_marketplace_admin_dashboard.MarketplaceAdminDashboardTests.test_dashboard_analytics_share_revenue_scope_period_and_legacy_exclusion --keepdb --noinput
```

Read `metrics['average']` in that test and the existing `_sales_overview_summary` at `modules/reports/views.py:178`. Change only the test fixture's eligible order amount, then verify that Dashboard and Analytics still agree; restore the fixture afterward. Do not create practice records through the live admin site.

---

# Global web Inter typography and Super Admin Marketplace Overview - October 22, 2026

This is the current implementation report. The historical report below describes the older product-list layout and does not override this update.

## 1. Cause / reason

Web components had conflicting Roboto, Montserrat and Poppins rules. In particular, `admin_layout.css` forced Roboto with `!important`, while Facility Admin separately forced Poppins and the earlier KPI refinement forced Montserrat. Canvas charts also had hard-coded font settings, independent of CSS. This explained why declaring a font on a bundle card alone did not change its displayed text.

The existing Super Admin Marketplace area combined sales metrics/chart in a wide card, displayed a short product list, put low-stock alerts beside it, and placed a seven-column order table below. The requested layout uses the existing sales/order/inventory data in three rows, with a revenue line chart and a separate vertical product chart. Existing AOV is reliable: eligible recorded transaction revenue divided by eligible completed/paid transaction count.

## 2. Exact files changed, current line numbers and nearby anchors

The following map records this task's application/template/test changes. Full HTML pages share one include, rather than receiving separate role font systems. Template rows also cover removed obsolete Google font links and cache-version updates for changed assets.

| File | Current line | Change / nearby code anchor |
| --- | ---: | --- |
| `backend/core/accounts/tests.py` | 534 | Update only Super Admin copy/chart expectation; Marketplace Admin assertions retain its original copy/chart. Anchor: `test_super_admin_loads_untouched_original_template`. |
| `backend/core/modules/facilities/static/facilities/css/admin_facilities_dashboard.css` | 14 | Replace role-specific forced Poppins with the shared Inter token. Anchor: `.facility-admin-dashboard .fd-content *`. |
| `backend/core/modules/facilities/static/facilities/js/admin_facilities_dashboard.js` | 31 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 15 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facilities_dashboard.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 16 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility_booking.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_service_requests.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/booking_document.html` | 2 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 6 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 6 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/marketplace/services/inventory.py` | 137 | Optional depleted-stock entries; stable bounded ranking includes zero-threshold depletion. Default low-only behavior retained. Anchor: `def iter_product_low_stock`. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 18 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 22 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_sellers.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_user_seller.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` | 11 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/messages/templates/messages/pages/admin_messages.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/notifications/templates/notifications/pages/admin_notifications.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/reports/dashboard_low_stock.py` | 14 | Optional combined alert mode with actual statuses and existing inventory destinations. Anchor: `def build_low_stock_card`. |
| `backend/core/modules/reports/dashboard_periods.py` | 310 | Five recent orders; opt existing shortlist into depleted stock, same snapshot and formulas. Anchor: `recent_marketplace_orders(MarketplaceOrder`. |
| `backend/core/modules/reports/templates/reports/pages/admin_domain_analytics.html` | 7 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html` | 17 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/reports/templates/reports/pages/admin_generate_reports.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/reports/templates/reports/pages/admin_services_analytics.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/reports/templates/reports/pages/admin_users_analytics.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/reports/test_dashboard_executive.py` | 105 | Update order of the existing operations cards. Anchor: `id="recentOrdersSlot"`. |
| `backend/core/modules/reports/test_dashboard_low_stock.py` | 53 | Add zero/variant/expired/archived/zero-threshold tests and update current UI copy expectations. Anchor: `test_combined_alerts`. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 161 | Update obsolete layout assertions; preserve real ranking/accounting tests and assert exactly two Marketplace canvases. Anchor: `test_analytics_operations_layout`. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 518 | Third existing comparison now visible with Average Order Value; expectation increases by one. Anchor: `self.assertContains(today_page, "vs yesterday"`. |
| `backend/core/modules/reports/test_web_typography.py` | 15 | Real rendered Super/Marketplace/Facilities/Custom Admin + login font-shell coverage and local WOFF2/license checks. Anchor: `class WebTypographyTests`. |
| `backend/core/modules/user_management/templates/user_management/pages/account_recovery.html` | 6 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/account_recovery_start.html` | 8 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_backup.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_data_export.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_login.html` | 15 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_roles.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_settings.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_tab_bootstrap.html` | 7 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 14 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/core/modules/user_management/templates/user_management/pages/password_reset_confirm.html` | 9 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/static/components/css/admin_dashboard_summary.css` | 26 | Retarget existing forced font-family declarations to the shared UI token; preserve sizes/layout/behavior. Anchor: `font-family: var(--ch-font-ui`. |
| `backend/static/components/css/admin_layout.css` | 103 | Retarget existing forced font-family declarations to the shared UI token; preserve sizes/layout/behavior. Anchor: `font-family: var(--ch-font-ui`. |
| `backend/static/components/css/admin_marketplace_overview.css` | 331 | Three-row layout, balanced charts, readable operations, thumbnails and empty/error/focus states. Anchor: `Super Admin: shared accounting`. |
| `backend/static/components/css/admin_products.css` | 577 | Retarget existing forced font-family declarations to the shared UI token; preserve sizes/layout/behavior. Anchor: `font-family: var(--ch-font-ui`. |
| `backend/static/components/css/admin_sales_overview.css` | 51 | Retarget existing forced font-family declarations to the shared UI token; preserve sizes/layout/behavior. Anchor: `font-family: var(--ch-font-ui`. |
| `backend/static/components/css/admin_super_dashboard.css` | 21 | Retarget existing forced font-family declarations to the shared UI token; preserve sizes/layout/behavior. Anchor: `font-family: var(--ch-font-ui`. |
| `backend/static/components/css/booking_slip.css` | 103 | Retarget existing forced font-family declarations to the shared UI token; preserve sizes/layout/behavior. Anchor: `font-family: var(--ch-font-ui`. |
| `backend/static/components/css/web_typography.css` | 2 | Local variable Inter, shared scale/page surface, SugarPie exception and narrow header adjustment. Anchor: `@font-face`. |
| `backend/static/components/js/admin_analytics.js` | 44 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/static/components/js/admin_booking_overview.js` | 1 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/static/components/js/admin_dashboard.js` | 201 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/static/components/js/admin_dashboard_executive.js` | 60 | Guard obsolete optional Active Sellers hook after replacing the card with existing Average Order Value. Anchor: `data-executive-sellers`. |
| `backend/static/components/js/admin_dashboard_filter.js` | 222 | Reuse existing snapshot request, render status alerts and five-column/five-order rows; retain chart/date hooks. Anchor: `function renderLowStock`. |
| `backend/static/components/js/admin_facility_revenue.js` | 1 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/static/components/js/admin_marketplace_analytics.js` | 56 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/static/components/js/admin_marketplace_products_chart.js` | 1 | Vertical Chart.js renderer for existing top-products data; keyboard/tooltips/fallbacks and refresh listeners. Anchor: `document.addEventListener`. |
| `backend/static/components/js/admin_sales_overview.js` | 109 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/static/components/js/admin_super_dashboard.js` | 63 | Retarget existing chart fonts to Inter and 12px labels; retain data, scales, filtering and behavior. Anchor: `Inter, sans-serif`. |
| `backend/static/components/js/web_typography.js` | 3 | Shared Inter canvas defaults and redraw after local fonts load. Anchor: `Chart.defaults.font.family`. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 26 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/templates/dashboard/pages/admin_facilities_dashboard.html` | 15 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 14 | Rearrange only Super Admin Marketplace Overview and add exact section subtitle. Anchor: `marketplaceOverviewTitle`. |
| `backend/templates/dashboard/partials/low_stock_card.html` | 3 | Existing inventory component renamed, status column, thumbnail/placeholder, requested empty copy. Anchor: `Inventory Alerts`. |
| `backend/templates/dashboard/partials/recent_orders.html` | 1 | Super Admin five-column table; retain other role table in else branch. Anchor: `if executive_mode`. |
| `backend/templates/dashboard/partials/sales_overview.html` | 1 | Select new Super Admin presentation; retain separate Marketplace Admin presentation. Anchor: `if executive_mode`. |
| `backend/templates/dashboard/partials/super_marketplace_products.html` | 1 | Top-five chart, actual JSON, accessible full-name list and distinct failure states. Anchor: `topSellingProductsCard`. |
| `backend/templates/dashboard/partials/super_marketplace_sales.html` | 1 | Existing three sales metrics and revenue chart with compact honest empty state. Anchor: `marketplace-sales-summary`. |
| `backend/templates/marketplace/pages/admin_sellers.html` | 13 | `web_typography.html` include; removed obsolete remote font imports where present and refreshed changed-asset versions. |
| `backend/templates/partials/web_typography.html` | 2 | New shared font stylesheet and deferred chart-font adapter. Anchor: `web_typography.css`. |

Font assets: `backend/static/assets/fonts/InterVariable.woff2` (352240 bytes) and `Inter-LICENSE.txt` (SIL Open Font License 1.1) are bundled locally from the [Inter project's official font files](https://github.com/rsms/inter/tree/master/docs/font-files). No Inter web asset previously existed. The existing `Sugar-Pie-W00-Regular.ttf` and `campushub_brand.css` were reused unchanged. The local variable Inter face supplies weights 100-900; no external font download is needed at runtime.

Documentation updated: this guide, `docs/dashboard-kpi-refinement.md`, `docs/suggested-product-bundles.md`, and `CAMPUSHUB_CONTEXT.md` identify Inter as the current web UI font, superseding older Montserrat notes.

Scratch-only QA helpers/renderings live in `scratch/web-marketplace-review/`; they are isolated test output and are never imported into the application database. `scratch/web-typography-changed-files.txt` records the initial typography edit inventory; the comprehensive current map is above.

## 3. Changes made / expected behavior

### Shared web typography

`partials/web_typography.html` loads one local stylesheet and a deferred chart-font adapter. The same include appears once on all full web page templates, including authentication, Super Admin, Marketplace Admin, Facilities Admin, custom-admin modules, reports, notifications, messages and rendered booking documents. The SugarPie wordmark exception keeps existing dimensions, proportions and navy/gold colors. SVG/icon assets are unchanged. Flutter files were not changed.

The shared page surface uses #F7F8FC; the existing navy/gold/white identity is retained. The shared scale defines page titles 24/600, section titles 18/600, card titles 16/600, navigation 14/500, KPI values up to 30/700, labels 13/500, tables 13px, forms/buttons 14px, supporting copy 13px, and chart text 12px. Small cards may use 24px values for readable full currency. Existing marketing headline composition on the login page remains; its form title adopts the shared page scale. Financial/statistic text uses tabular numerals. Old module declarations that previously forced another family now resolve to `--ch-font-ui`; historical non-forced declarations are overridden by the shared system.

`web_typography.js` sets Chart.js defaults to Inter/12px and redraws existing chart instances once fonts load. Existing explicit chart-family settings were also updated, including inline Generate Reports chart configuration and the Facility Admin renderer. This keeps canvas labels consistent with HTML text.

### Super Admin Marketplace Overview

1. **Sales Overview** has three compact existing metrics: Marketplace Sales, Completed Orders, Average Order Value. No new counting logic.
2. **Visualizations** has exactly two Marketplace charts: Sales Trend is a navy revenue line, and Top-Selling Products is a navy vertical bar chart of the existing top five quantity-ranked products. Both canvases are 240px high. The existing Daily/Weekly/Monthly grouping remains. Full product names and quantities appear in tooltips and the accessible text list; visible labels can wrap to two short lines or ellipsize.
3. **Operations** has Recent Orders (latest five actual orders, five requested columns) on the left and Inventory Alerts on the right. Management routes and status values remain unchanged. Tables retain native horizontal scrolling where the full columns cannot fit; codes, amounts and status words are not split into fragments.

Empty sales ranges hide the chart canvas and use the requested honest message rather than a large flat-zero plot. Product, order and alert empty states use the requested copy. Existing load/retry hooks remain, with independent top-product failure handling. Requests do not convert failures into fictional zeros or an all-clear inventory state.

Other dashboard sections remain in their established positions. The System Overview layout from the previous update is preserved, with its font now Inter. Bundle Recommendations & Activity remains outside Marketplace Overview. Marketplace Admin retains its dedicated sales presentation and behavior, with only typography changed.

## 4. How it works: functions, inputs, outputs and data flow

### Sales and charts

`build_dashboard_data(params, today=None, legacy=False)` in `reports/dashboard_periods.py` remains the shared initial-page and JSON-refresh calculator. Date parameters select the existing reporting period. `valid_sales_queryset()` in `marketplace/services/analytics.py` filters real `MarketplaceOrder` rows to completed + paid + positive quantity and chooses the canonical completed/paid/created timestamp. Revenue sums stored `total_price` once per transaction, avoiding payment joins and double counting. Cancelled/unpaid/other ineligible records do not become revenue. Synthetic CSV analysis is separate and is not read for these metrics or charts.

Existing `top_selling_products(eligible_orders, limit=5)` in `reports/dashboard_marketplace.py` groups quantities by parent product identity, including existing historical-name fallback, and sorts by units then revenue. CampusHub currently stores a sellable-product transaction on each `MarketplaceOrder`; there is no separate live `OrderItems` relation to query. This implementation uses that canonical transaction quantity and does not invent child records, group separate orders into baskets, or expand bundle recipes into fictional sales.

The view passes existing `sales_overview.metrics`, `revenue_chart`, `dashboard_marketplace.top_products`, and operations into the template. `sales_overview.html` selects `super_marketplace_sales.html` only when `executive_mode` is true. The existing `admin_sales_overview.js` handles the same sales canvas and grouping events; its Super Admin presentation is now a line and hides the auxiliary completed-order series/scale. Other role chart behavior remains unchanged.

New `admin_marketplace_products_chart.js` is a renderer, not a second query/API/calculator. It reads the initial `topSellingProductsData` JSON and listens to the existing `campushub:dashboard-data` event. `sync()` updates visible/empty/error state, full-name descriptions and the Chart.js dataset. Arrow/Home/End keys inspect actual bars and announce full quantities. Chart-library failure exposes the real text quantities rather than fabricating bars.

Example: real eligible recorded transactions total PHP 3900 across 18 orders. Existing calculations yield Sales PHP 3900.00, Completed Orders 18, and AOV PHP 216.67. The line buckets and top products come from the same eligible queryset. This example was checked in isolated tests, never added to the application database.

### Orders and inventory

`recent_marketplace_orders(queryset, limit=5)` still supplies newest actual records independently of the sales reporting range. Super Admin now requests five rows and displays Order Number, Customer, Total Amount, Status and Date. The full management page still contains the detailed product/payment fields and existing actions; the compact preview does not change order processing.

`build_low_stock_card(today, include_out_of_stock=True)` retains its existing function/key for compatibility but now lets the Super Admin opt into combined alerts. It calls `low_stock_inventory_rows(..., limit=5, include_out_of_stock=True)`, which reuses `iter_product_low_stock()` and `get_inventory_status()` for real simple/variant stock, per-option/product thresholds, and expiry rules. Archived, expired and derived bundle inventory are excluded using existing policy. Stock is already reserved/deducted in the existing workflow; the card never subtracts orders again.

The optional flag defaults to false, preserving every existing low-only caller. Depleted stock ranks before positive low stock, including zero-threshold products. Two bounded-memory queries remain; variant JSON is streamed without seller/option N+1 queries. Each result carries the actual product, option key, quantity, threshold, image and status. The renderer presents a real image or a neutral placeholder when none exists. No stock is modified.

`admin_dashboard_filter.js` still fetches a single dashboard snapshot. It updates existing metrics, dates, chart events, recent orders and alert rows. It preserves per-tab authentication on existing internal links. Top-product chart loading/failure listens to the same existing event flow, so no per-card API requests were introduced.

## 5. Backend / API behavior

No route, permission, payment, approval, authentication or inventory-write behavior changed. Existing Super Admin guards and destination permissions still apply. The snapshot response keeps `marketplace`, `operations.recent_orders` and `low_stock` keys. In Super Admin the recent order list is now five rather than six records, and `low_stock.products` can include `out_of_stock`; its `view_all_url` opens the existing full inventory view. Existing attention counts retain their low/out separation and matching routes.

Navigation reused: `admin_marketplace_analytics_page`, `admin_orders_page`, and `admin_products_page?view=inventory`, plus the existing per-product inventory deep link. The dashboard's established API 400/401/403/503 handling, Cash on Pickup rules and persisted recommendation read path remain. No new API endpoints or competing queries.

## 6. Database / migration impact

No model or schema change; no migration needed. Only existing read queries and presentation changed. Tests ran in the separate Django test database with rolled-back fixtures. Read-only application verification after testing still shows **15 products, 1 order, 0 saved recommendations**. No `.env`, online deployment, server role, phone/APK, Flutter font or application record changes.

## 7. Tests performed

The following broad suite passed **209 tests**:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB
.\backend\core\venv\Scripts\python.exe backend\core\manage.py test modules.reports.test_web_typography modules.reports.test_dashboard_kpi_cards modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_periods modules.reports.test_dashboard_executive modules.reports.test_dashboard_low_stock modules.marketplace.test_bundle_suggestions modules.marketplace.test_bundle_monitoring accounts.test_roles_permissions accounts.test_recovery_information modules.reports.test_facility_admin_dashboard modules.marketplace.test_variant_inventory --keepdb --noinput
```

Log: `scratch/web-typography-marketplace-final.log`. After strengthening the exact two-chart/empty-state assertions, **7 final focused tests passed** (`scratch/web-typography-final-focused.log`). Earlier intermediate runs exposed only outdated UI assertions; those were updated without weakening revenue, quantity, query-count, variant, permission, service-isolation or other accounting checks. The new zero-threshold depleted-stock test also passes.

Django system check clean. `makemigrations --check --dry-run` reports no changes. `node --check` passed for all 12 changed script files.

Browser verification used clearly labelled HTML produced by isolated Django tests and real project CSS/JS/fonts through a loopback-only fixture server. Confirmed Inter computed styles on Super Admin/bundle cards, Marketplace Admin, Facilities Admin, Custom Admin, tables/inputs and login; confirmed SugarPie still on sidebar/login wordmarks, and local Inter reports loaded. Confirmed equal 240px chart heights, navy line/vertical bars, full-name keyboard tooltips, Weekly filter response, compact sales/product empty states without a visible zero-line canvas, and independent sales/products/orders/inventory failure messages with retained last-loaded KPI notice. No real authentication or business write was performed in the browser.

Responsive measurements: normal desktop client/scroll 1265/1265; tablet 768px viewport 753/753 with stacked charts/operations; phone 390px viewport 375/375 with stacked metrics/charts and no card overflow. At 320px, cards fit but header title/actions exceeded the remaining width. Added a scoped below-360px three-row header adjustment; the browser connection ended before this last fix and final label-wrap polish could be visually rechecked. Do not treat that exact width as a verified pass. The temporary preview server was stopped; preview records remain test artifacts only.

## 8. Remaining limitations, troubleshooting and learning exercise

- This is a local source update. It was not deployed to Kamatera and does not change any mobile build.
- Browser coverage is representative across roles, not an authenticated walkthrough of every module, modal, printed page or formal WCAG audit. The shared template/role tests and all modified JavaScript syntax were checked. The last 320px header adjustment needs a visual recheck when the browser is available.
- Inter is bundled locally; Chart.js still uses the project's existing CDN. If Chart.js is unavailable, real text fallbacks/error states remain. No replacement charting dependency was introduced.
- Recent Orders may scroll horizontally on narrow cards to preserve all five columns; this is intentional. Inventory alert preview remains bounded to five entries. View All opens full management.
- Existing web/mobile identity counting policies and marketplace transaction model are unchanged. Do not describe the singleton transaction storage as a new OrderItems implementation.
- A whole initial-page database outage still fails the request. The existing JSON refresh error handling prevents fake totals and exposes Retry; no offline cache or fabricated initial data was added.

If a font/style appears unchanged, press Ctrl+F5, inspect that `web_typography.css?v=20261022-inter` and local `InterVariable.woff2` return 200, and check that changed asset versions also use `20261022-inter`. A late rule with a hard-coded `font-family: ... !important` can override the shared font; convert it to `var(--ch-font-ui, 'Inter', sans-serif)` rather than adding another role-specific font system. Preserve the SugarPie exceptions. If charts appear empty, check eligible completed/paid records and selected dates before suspecting CSS; zero orders and failed requests have different messages.

Safe practice: temporarily change `--ch-type-support` in `web_typography.css` from 13px to 14px, then explicitly use that variable in the bundle description rule. Refresh a local page and confirm the bundle description changes while the wordmark still uses SugarPie and the backend totals stay unchanged. Restore the values. For a chart exercise, change only the top-products font size from 12 to 13, resize the page, use arrow keys to read full names, then restore 12. Never add fake production records to make a chart look populated.

---

# Marketplace Analytics design refinement

Implemented October 4, 2026 using the requested Impeccable skill.

## 1. Cause / reason

The empty product card used its natural height while the category card absorbed the remaining right-column height. That produced an uneven pair of blank cards. Metrics and empty states also lacked a consistent icon treatment. This refinement keeps the existing institutional layout and factual copy, improves scanning, and balances the empty states.

## 2. Exact files changed

| File | Change in this refinement |
| --- | --- |
| `backend/templates/dashboard/partials/marketplace_icon.html` | New shared, authored outline SVG partial for wallet, cart, receipt, trend, trophy, bag, categories, information and arrow icons. |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | Icons beside summary headings and the detailed analytics link; centered icon-and-message empty states. |
| `backend/templates/dashboard/partials/sales_overview.html` | Small global-dashboard metric/trend icons, SVG information controls, chart empty-state icon and button arrow. Render the older metric-icon blocks only on dedicated dashboards. |
| `backend/static/components/css/admin_marketplace_overview.css` | Scoped icon sizing, balanced empty right-column rows, centered messages, gold View Orders button, tabular numerals, themed selection/scrollbars and information-button focus targets. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | Marketplace stylesheet cache version changed to `20261004-marketplace-design`. |

Documentation added: this file. Local QA helper adjusted: `scratch/dashboard-global-review/check-ranking.cjs` trims incidental SVG-template whitespace when checking the Sales Trend heading text. Generated review HTML/JSON/screenshots remain under `scratch/dashboard-global-review/`.

## 3. Changes made

- Navy outline icons use one 24px drawing grid and 1.8px stroke weight. Visible sizes are 16px for metrics/actions, 20px for summary headings and 32px for empty states.
- Marketplace Sales remains the prominent 32px desktop value, with 20px supporting values and tabular numerals. The narrow-screen primary value remains 28px.
- Empty product and category cards share the available desktop height evenly. Populated cards retain the space needed by the ranked list.
- View Orders is a compact gold button with navy text and an SVG arrow. Detailed Analytics remains a text link.
- The Sales Trend divider, section heading, subtitle and 260px chart area remain present. No decorative chart data was added.
- Information controls retain their accessible labels and tooltip descriptions, with 24px targets and visible keyboard focus. Decorative SVGs are hidden from assistive technology.

## 4. How it works

The existing templates include the same SVG partial with an icon name. Styles are scoped to the global marketplace section, preserving dedicated-dashboard layout. A wide-container CSS rule detects the visible product empty state and gives the two right cards equal rows. Existing container breakpoints move the cards below Sales Overview, then stack them on narrow screens.

Existing frontend updates continue to target the same data attributes and value/list selectors. Empty-state wrappers still toggle through their `hidden` property. Loading hides the empty icons/messages and preserves the existing skeletons. Refresh failures retain the previous data and Retry restores the section.

## 5. Backend / API behavior

No Python service, API or JavaScript behavior changes in this refinement. The existing Django dashboard endpoint, authorization, global date range, Daily/Weekly/Monthly chart grouping, ranked top five and category aggregation remain intact. Metrics continue to use only completed marketplace orders with recorded paid status, following Cash on Pickup rules. FastAPI remains dedicated to chat.

## 6. Database / migration impact

None. No migrations, production records, inventory changes or payment changes.

## 7. Tests performed

- All 75 existing dashboard backend tests passed; Django reported no system-check issues.
- After final template cleanup, all 10 marketplace tests passed again.
- Rendered-template DOM integration passed for empty/populated transitions, five ranked rows, category sales/shares, grouping/authentication, loading, failed refresh/Retry, safe labels and missing Chart.js.
- Existing global-controls, Attention Required and System Status frontend checks passed.
- Headless Chrome checked six states: desktop populated/empty/loading, a 950px laptop content frame and 390px mobile populated/empty frames. Measurements verified a persistent 260px chart area, aligned desktop outer edges, top-right grouping, fitting values/tooltips and no horizontal page overflow. Desktop and mobile screenshots were visually inspected together.
- Text contrast: muted on white 5.56:1; muted on the light empty-state background 5.31:1; navy on gold 8.97:1; navy on white 16.24:1.
- The optional Impeccable detector returned no regex layout findings but reported missing HTML parser modules, so its scan is incomplete. Browser measurements and visual inspection supplied the layout evidence.
- `git diff --check` found no whitespace errors; Git emitted existing line-ending notices in other workspace files.

Review images: `scratch/dashboard-global-review/ranking-empty-desktop.png`, `ranking-empty-mobile.png`, `ranking-desktop.png` and `ranking-mobile.png`. Populated screenshots use isolated test fixtures, not production records.

## 8. Remaining limitations

Browser review isolated the actual templates, styles and chart code with test-database records; it did not use an authenticated browser session against the live database. Offline screenshot rendering used available font fallbacks. The live application's configured Montserrat request is preserved. Older browsers without CSS `:has()` retain the prior natural-height empty-card rows; messages and analytics remain available.

Temporary `browser-marketplace-design-*` profiles remain in `scratch/dashboard-global-review/`: the execution policy rejected recursive cleanup, including an attempt with explicitly verified literal paths. This does not affect the dashboard.

Hard refresh the dashboard with Ctrl+Shift+R to load the revised stylesheet.

## October 17, 2026 — Super Admin layout and live-only dashboard

This update supersedes the earlier placement and sample-preview descriptions in this guide. UI/UX Pro Max was used for hierarchy and responsive-layout guidance. The existing CampusHub navy, gold, white, fonts, real metrics, and compact card components remain in use.

### 1. Cause / reason

Confirmed from the templates: Suggested Product Bundles was beside the KPIs, while Frequently Bought Together and Cross-Sell Suggestions were farther down beside Sales Overview. Product performance then occupied a separate row. The sales sample button could inject fabricated values into sales, category, utilization, booking, ranking, upcoming-reservation, and revenue cards together. Several facility and category panels also forced large empty heights.

The 320px browser check additionally found the header title and actions extending the page to 369px. The fix shrinks the title's flex region and tightens header spacing on this dashboard only; it does not hide the header actions.

### 2. Exact files changed

Paths below are relative to the project root. Line numbers are approximate current locations; use the adjacent anchor if later edits move them.

| File | Current line / nearby anchor | Change and reason |
| --- | --- | --- |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 26 `admin_dashboard_summary.css`; 202 `marketplace_analytics.html`; 408 `domain_overviews.html`; 605 dashboard scripts | Remove duplicate standalone placements, move System Status before Recent Activities, and refresh changed asset versions. |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 2 `dashboard-summary-layout`; 119 `attention_required.html`; 121 `dashboard-summary-aside` | Eight existing KPIs and Attention Required on the left; all three live recommendation cards stacked on the right. |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 7 `dashboard-marketplace-grid` | Place Sales Overview beside the existing top-selling/category stack; render each card once. |
| `backend/templates/dashboard/partials/domain_overviews.html` | 1 `dashboard-domain-grid` | Put Services and User / Account summaries beside one another on wide screens. |
| `backend/core/modules/marketplace/templates/marketplace/partials/cross_sell_suggestions.html` | 2 `crossSellSuggestionsTitle` | Show “Cross-Selling Opportunities” on Super Admin; preserve the other dashboard's existing title. |
| `backend/templates/dashboard/partials/sales_overview.html` | 10 `sales-overview__controls-top`; 44 `sales-overview__metrics` | Remove the sample button and the sample JSON include, retaining Daily/Weekly/Monthly. |
| `backend/templates/dashboard/partials/marketplace_product_stack.html` and `category_sales_card.html` | 1 card wrapper / header | Remove the hidden sample notices. Actual products and category sales remain. |
| `backend/templates/dashboard/partials/booking_overview.html`, `facility_revenue.html`, `most_booked_facilities.html`, `upcoming_reservations.html` | 1 respective card wrapper | Remove sample labels while keeping real rows, charts, loading, errors, Retry, and links. |
| `backend/templates/dashboard/partials/facility_utilization.html` | 21 `data-utilization-loading` | Remove its sample notice and hard-coded capacity JSON; retain real capacity calculations and empty/unavailable states. |
| `backend/static/components/css/admin_dashboard_summary.css` | 1 Super Admin scope; 32 domain / marketplace grids; 57 responsive rules | Four KPI columns × two rows on desktop, compact icon containers, balanced facility grid, wider revenue chart, natural empty-card heights, and responsive stacking. |
| `backend/static/components/js/admin_dashboard_filter.js` | 315 `render(payload)`; 459 `load(...)` | Retain the real payload renderer; remove sample branches/listeners and obsolete sample-button references. Grouping still refreshes only its chart. |
| `backend/static/components/js/admin_sales_overview.js` | 37 `styleComparisons`; 74 dashboard-data listener | Remove sample snapshots, injected sample metrics, and sample toggling; keep real chart descriptions/tooltips and refresh rendering. |
| `backend/static/components/js/admin_booking_overview.js` | 31 `render`; 137 dashboard-data listener | Remove sample grouping/preview handlers; keep the existing real booking renderer and chart-only updates. |
| `backend/static/components/js/admin_facility_utilization.js` | 15 `render`; 46 loading listener | Remove fabricated-capacity preview handling; accept only existing real summary payloads. |
| `backend/static/components/js/admin_most_booked_facilities.js` | 17 `render`; 52 loading listener | Remove sample snapshots and sample ranking events; preserve real rows and broken-image fallback. |
| `backend/static/components/js/admin_upcoming_reservations.js` | 15 `render`; 32 loading listener | Remove generated sample future dates and preview events; keep backend reservation dates/statuses. |
| `backend/static/components/js/admin_facility_revenue.js` | 27 `render`; 95 loading listener | Remove sample payment/trend handling; report links always use the real selected date range. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 395 Attention order assertion; 502 global markup test | Accept the existing multi-class KPI wrapper and verify preview controls/payloads are absent from normal rendered HTML. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 132 preview-artifact assertions | Test fixtures may still be used in isolated tests, but must not be emitted into dashboard HTML. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 262 Super Admin layout test | Update expected section order; keep shared calculation, permission, result-limit, and real-source assertions. |
| This guide; `CAMPUSHUB_CONTEXT.md` | This dated section; “Super Admin live-only dashboard layout” | Preserve implementation, debugging, verification, and learning notes. |

`scratch/dashboard-real-layout/check.cjs` is the local browser verification helper, not application code. Its HTML/JSON/screenshots come from isolated Django test fixtures. Research CSVs and the old sales test-fixture template were retained; the live page no longer includes them.

### 3. Changes made

Desktop order:

1. Left: System Overview, eight KPIs in four columns and two rows, then Attention Required. Right: Marketplace Recommendations, Suggested Product Bundles, Frequently Bought Together, Cross-Selling Opportunities.
2. Sales Overview left, Top Best-Selling Products above Sales by Product Categories right.
3. Marketplace Operations: Low Stock Products and Recent Orders.
4. Facilities Analytics: Booking Overview full width; utilization, most booked, upcoming reservations; Facility Status beside the wider Facility Revenue card.
5. Services and User / Account summaries, System Status, then Recent Activities.

At narrower widths the KPI grid becomes two columns and the major regions stack. Below 360px the KPI grid becomes one column. Facility panels stack on phones. Existing wide tables retain their own horizontal scroll area instead of widening the page.

### 4. How it works — functions, inputs, outputs, data flow

`admin_dashboard_page(request)` still gets existing backend summaries and passes the same context to Django. Template includes decide **where** each component is placed. CSS Grid decides column width and responsive wrapping; it does not calculate counts.

The existing `dashboard_bundle_suggestions(user, limit=2)` remains unchanged. Its input is the authorized user and its display limit. Its output is the existing live result set used by all three recommendation panels. Product photos, names, sellers, View, and View All remain dynamic. Support, Confidence, Lift, and synthetic labels are not added to the normal interface.

`load(period, salesOnly, bookingOnly)` receives the selected global period, plus flags for isolated chart updates. It fetches the current dashboard API. For global updates, `render(payload)` updates real KPI values, Attention Required, orders, products, category shares, and summaries, then dispatches `campushub:dashboard-data`. Each facility script's `render(...)` consumes its own part of that payload. Sales/booking grouping dispatches the existing chart-specific update instead, so changing Daily/Weekly/Monthly does not replace the rest of the dashboard.

Annotated example:

```javascript
// Input: a successful, authorized response from the existing dashboard API.
document.dispatchEvent(new CustomEvent('campushub:dashboard-data', {
    detail: payload,
}));
// Each existing renderer reads its own real fields, such as:
// payload.facilities.revenue_overview or payload.facilities.upcoming_reservations.
// The removed marketplace-sample event has no dashboard preview listeners.
```

This approach reuses existing components and calculations instead of creating parallel card logic. Card placement is server-rendered in reading order; JavaScript does not move sections after the page loads.

### 5. Backend / API behavior

No new endpoints, ORM queries, status rules, permissions, date-range definitions, payment calculations, Apriori thresholds, seller/product mapping, or inventory behavior. Actual empty states remain when records or qualifying recommendations do not exist. API failures retain the existing error/Retry behavior, rather than injecting example values. Chart.js remains the existing chart library.

### 6. Database / migration impact

None. No models, migrations, live record writes, imports, deletions, or data seeding. No migration command is needed. In production, use the project's normal static-asset deployment process; in development, hard refresh with Ctrl+Shift+R if assets are cached.

### 7. Tests performed and manual verification

- **118 Django tests passed** across dashboard periods, marketplace analytics, booking summaries, utilization, facility ranking, upcoming reservations, and revenue. System check reported no issues.
- **39 recommendation tests passed**, including live-source isolation, permission checks, shared calculation, no research metrics in the normal UI, populated cards, and the revised Super Admin order.
- Node syntax checks passed for all seven changed JavaScript files.
- **24 headless Chrome scenarios passed**: empty, populated sales, overview, and populated recommendation fixtures, each at 1920, 1440, 1024, 768, 390, and 320px. Checks covered eight KPIs, section placement/uniqueness, no horizontal page overflow, no sample controls/payloads, chart grouping, refresh, and no JavaScript exceptions. Also checked API failure/Retry and populated recommendation View/View All. A dispatched obsolete sample event did not alter real KPI values.
- Visually inspected desktop and mobile captures. Artifacts are in `scratch/dashboard-real-layout/`.

Manual steps:

1. Sign in as Super Admin and open Dashboard. Verify four KPIs across and two rows on a desktop; Attention Required below. Verify the three recommendation cards on the right in the stated order.
2. Verify each top-selling/category card appears once. Check facility layout, wider revenue chart, compact domain summaries, and Recent Activities last.
3. Change the global date period and Refresh. Compare totals with eligible saved records. Change Sales and Booking grouping separately; confirm unrelated totals remain unchanged.
4. Use a period with no sales/bookings. Verify honest empty states, zero revenue where appropriate, and no “Show sample” or sample values.
5. If real qualifying product pairs exist, use View and View All. Otherwise verify the real empty messages; do not import synthetic data to populate the dashboard.
6. Use browser device mode at 390 and 320px. Check header actions, readable stacked cards, and native scrolling inside wide tables.
7. Temporarily simulate a failed dashboard request in browser developer tools, then restore connectivity and Retry. No fabricated data should appear.

### 8. Limitations, troubleshooting, and safe learning exercise

Browser checks used actual rendered templates/CSS/JS with isolated test-database records and mocked HTTP transport, not an authenticated production browser. Populated recommendations used the existing test-only mined multi-item fixture; this is not a claim that the live database currently has qualifying baskets. Production records were not altered. External font loading was replaced by available browser fonts during isolated captures; configured Montserrat remains unchanged in the app. Existing CSS container-query / `:has()` browser requirements remain.

If the old sample button appears, inspect the rendered page source and asset versions after a hard refresh; do not edit the database. If a real card fails, inspect the dashboard API response and the console first. A missing card/duplicate ID suggests a template-include issue; correct data in JSON but a stale chart suggests a renderer/event issue. These are debugging possibilities, not confirmed live failures.

Practice exercise: in a temporary local branch, change only `.dashboard-summary-aside`'s CSS `gap` from 16px to 20px. Verify spacing at 1440px and 390px and confirm the Network response and KPI values are unchanged. Restore 16px afterward. This demonstrates the separation between layout (CSS), structure (Django templates), and business data (backend/API).

## October 17, 2026 — Final executive / operational dashboard

This section supersedes the earlier October 17 layout above. It implements attachment `e8254627-6fcf-4aca-8d8a-46e051999e91`, including the user's final eight-section order. The earlier three-card recommendation column is replaced by Suggested Product Bundles alone beside System Overview. Frequently Bought Together and Cross-Sell Suggestions now belong to Marketplace Overview.

### 1. Cause / reason

Confirmed in the existing templates: the dashboard repeated detailed category, utilization, status, and revenue charts and used large panels. Services had only three summary numbers, and the activity feed was synthesized from several module records rather than showing the recorded audit feed with an actor column. Reports had Marketplace and Facilities destinations, but no Services/Users Analytics destinations.

Service applications and physical reservations share `Booking` storage. Treating every Booking as a physical reservation inflates physical booking totals and sends service applications to the wrong alert destination. The final summary uses the existing `service_resources_q()` classification, retains the actual stored statuses, and keeps service and physical reservation counts separate.

### 2. Exact files changed, current lines, and anchors

All paths are relative to the project root. Lines are approximate; search the named anchor after later changes.

| File | Current line / anchor | Change / expected behavior |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_executive.py` | 14 `service_overview`; 41 `executive_overview` | New bounded presentation helpers over existing models/queries; service-period summary, current pending queue, physical booking summary, audit rows, and date-preserving Analytics links. No new business model or workflow. |
| `backend/core/modules/reports/dashboard_periods.py` | 284 `executive = executive_overview` | Add `executive` to the existing response, reuse already aggregated service counts, assign the same physical booking overview to both existing/new response fields, and exclude service requests from Total Bookings. Pending Approvals still includes all pending work, with a separate service-request description. |
| `backend/core/modules/reports/dashboard_bookings.py` | 17 `upcoming_reservations`; 62 `most_booked_facilities`; 83 `build_booking_overview` | Apply the existing physical/service boundary to rankings/upcoming reservations. The chart helper accepts a supplied queryset instead of duplicating chart calculations. |
| `backend/core/modules/reports/dashboard_attention.py` | 49 `build_attention_required`; 65 `pending_services` | Add the real positive pending-service count and existing Service Requests pending-filter link. Physical pending bookings use their own count. |
| `backend/core/accounts/activity_service.py` | 26 `MODULE_LABELS` | Recognize actual Services and Service Requests events as Services; reuse shared actor/action formatting. |
| `backend/core/modules/reports/views.py` | 1388 `executive`; 1465 `admin_marketplace_analytics_page`; 1487 `admin_facility_analytics_page` | Supply the same executive payload to initial HTML; dispatch the existing Analytics route by module; retain the direct Facilities Analytics route and permission check. Marketplace keeps its existing analytics builder and academic scope. |
| `backend/core/modules/reports/analytics_sections.py` | 20 `analytics_period`; 33 `module_links`; 39 `render_facility_analytics`; 52 `render_domain_analytics` | Shared date-preserving module links and protected Facilities/Services/Users destinations. Services reuses the service summary plus one grouped status table; Users reuses `build_report('user_accounts', ...)`. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 25 executive CSS; 44 `executive_dashboard.html`; 612 executive script | Render the compact Super Admin branch and remove unused detailed facility chart scripts/styles from that dashboard. Other role templates remain separate. |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 1 `data-executive-dashboard` | The final eight sections, existing global filter, small trends, live lists, operational cards, and recorded activity table. |
| `backend/templates/dashboard/partials/executive_service_rows.html` | 1 `for row in rows` | Shared three-row service request presentation and honest empty message. |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 119 `dashboard-summary-aside` | Keep eight KPIs left and Suggested Product Bundles right. Attention is rendered afterward at full section width. |
| `backend/templates/dashboard/partials/sales_overview.html` | 46 `executive_mode`; 68 `data-executive-sellers` | Executive mode shows Marketplace Sales, Completed Orders, Active Sellers. Other pages retain their existing Average Order Value display. |
| `backend/templates/dashboard/partials/booking_overview.html` | 10 `executive_mode`; 12 `reserved_confirmed` | Executive mode shows four metrics. The Reserved / Confirmed label uses existing approved + paid logic, not a newly invented status. |
| `backend/templates/dashboard/partials/top_products_card.html` | 1 product card | Extract the existing ranked product card without its category sibling. Initial and refreshed executive lists show three products. |
| `backend/templates/dashboard/partials/marketplace_product_stack.html` | 2 `top_products_card.html` | Reuse the extracted product component for existing layouts; category functionality remains available outside the executive dashboard. |
| `backend/static/components/css/admin_dashboard_executive.css` | 1 executive-only scope | Compact two/three-column layouts, 155px sales chart, 150px booking chart, four service metrics, short lists, and responsive wrapping. Override the old fixed 260px canvas height so it cannot overlap the next card. |
| `backend/static/components/js/admin_dashboard_executive.js` | 9 `safeLink`; 16 `serviceRows`; 24 `fail`; 33 `render` | Update service metrics, request lists, activity rows, upcoming operational list, active sellers, and Analytics links from the same response. Failed requests show unavailable states rather than fake zeros. |
| `backend/static/components/js/admin_dashboard_filter.js` | 148 `serviceAttention`; 168 `renderAttention`; 265 orders; 327 `render` | Reuse global filters and chart-only updates; category DOM is optional after its removal. Keep three recent orders/products in executive mode. Health warnings use actual health responses and existing status/backup actions. |
| `backend/static/components/js/admin_booking_overview.js` | 11 `executiveMode`; 32 `render` | Read the same physical booking summary, validate the reserved count, skip absent detailed KPI cells, and retain keyboard-accessible chart grouping/errors. Use the institutional palette. |
| `backend/static/components/js/admin_sales_overview.js` | orders dataset `pointRadius` | Hide zero-value point markers in the small global chart while retaining the baseline, tooltip, and real values. |
| `backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html` | 1 document; `facility-detailed-grid` | Render the existing detailed Utilization, Facility Status, and Facility Revenue components in Analytics, with existing report links, retry controls, and real initial JSON. |
| `backend/core/modules/reports/templates/reports/pages/admin_domain_analytics.html` | 1 document; `Requests by Service`; `User Accounts` | Add protected Services/Users Analytics content within the existing Analytics route; bounded Users table pages. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 24 `analytics_modules.html` | Keep full Marketplace charts/breakdowns and add module navigation. |
| `backend/core/modules/reports/templates/reports/partials/analytics_modules.html` and `analytics_dates.html` | 1 nav / form | Permission-aware module links and custom date inputs. Normal admin role visibility is not expanded. |
| `backend/static/components/css/admin_analytics.css` | 1 shared Analytics module rules | Module navigation, detailed facility grid, existing typography and styled date controls, local table scrolling, wrapped action headers, and a 320px header fix. |
| `backend/core/modules/reports/test_dashboard_executive.py` | 42 service boundary; 66 payments; 75 audit; 87 layout/routes; 114 permissions | New regression coverage using isolated real model records. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 348 query budget; 395 Attention order; 502 render fixture | Verify bounded query counts and the revised executive markup/comparison count. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 160 executive layout; 219 category destination; 333 empty-state artifacts | Assert removed dashboard detail and retained full Analytics category calculations; preserve real data fixtures. |
| `backend/core/modules/reports/test_facility_revenue.py` and `test_facility_operational_status.py` | card markup/export tests | Verify detailed cards at their new Analytics destination, with existing calculation/empty/error coverage. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 262 Super Admin order | Preserve the one shared live calculation, row limits, permissions, and result content; update layout expectations. |
| This guide and `CAMPUSHUB_CONTEXT.md` | this final dated section | Preserve the implementation, debugging, verification, and learning notes. |

Scratch verification scripts are `scratch/dashboard-executive/check.cjs` and `check-analytics.cjs`; they are not production dependencies or data seeds.

### 3. Changes made — final order and removed detail

1. **System Overview:** eight existing compact KPIs, four across and two rows on wide desktops. **Suggested Product Bundles** is the only right-side recommendation card under Marketplace Recommendations. No synthetic results or research metrics are shown.
2. **Attention Required:** below the whole top area; positive pending product/seller/physical-booking/service-request counts and existing operational warnings. Verified database/chat issues and backup warnings come from the existing health request. Unknown health does not falsely clear a previously verified warning.
3. **System Status:** compact Database, Chat Service, and Backup cards with existing checks/timestamps/actions.
4. **Marketplace Overview:** three compact metrics, small Sales Trend, three top-selling products, Frequently Bought Together / Cross-Sell Suggestions, three recent orders, and View Marketplace Analytics. Low Stock Products has a shortcut to its single authoritative operational table below, avoiding another duplicate table.
5. **Facilities Overview:** Total Bookings, Pending Approval, Reserved / Confirmed, Completed; small Booking Trend; compact Most Booked Facilities / Upcoming Reservations and View Facilities Analytics.
6. **Services Overview:** Active Services, Open Requests, Pending Requests, Completed Requests; Most Requested Service and three recent requests; existing Services route and Services Analytics action.
7. **Operational Attention:** three equal desktop cards — Low Stock Products, nearest Upcoming Bookings, Pending Service Requests. Reuse the same query results, rather than repeating database queries for the operational copies.
8. **Recent Activities:** latest five recorded events in the selected period, with Time / Module / Activity / User, and View All Activities → existing User Monitoring.

Removed from the normal dashboard: category donut/table, detailed utilization/revenue/status charts, standalone User / Account Overview, and the large Marketplace Operations heading. Detailed Marketplace analysis stays in the existing Analytics page. The three detailed facility components are rendered in Facilities Analytics. Existing payment report and booking/inspection workflows remain accessible through their established pages; no new inspection-analysis or service-revenue numbers were invented.

### 4. How it works — functions, inputs/outputs, formulas, and flow

`build_dashboard_data(params)` is still the single initial/refresh data builder. It resolves the same date range, keeps existing sales/inventory/recommendation helpers, and adds `executive`. Already calculated service catalog/pending counts are passed to `executive_overview(...)` to avoid repeating those count queries. The physical booking trend is built once and shared by the old and new response locations.

`service_overview(period, current_counts=None)` accepts the resolved start/end dates and optional existing current-state counts. It returns four metrics, an approved/completed service leader, three recent submitted requests, and the current three-item pending queue. Its table queries use `select_related('facility', 'user')`; requester labels reuse `_booking_display_fields`, supporting the existing mobile `CampusHubUser` relationship and walk-in text. It does not assume Booking.user is Django's administrator User model.

Definitions:

| Value | Real source / rule |
| --- | --- |
| Active Services | Current unarchived service-configured Facility records with existing Open/Available status. |
| Open Requests | Service requests submitted in the selected period whose actual status is Pending or Approved. Pending Requests is a subset, not an additional count to add to Open Requests. |
| Pending / Completed Requests | Submitted-period service records with the corresponding stored status. |
| Most Requested Service | Group submitted-period Approved/Completed service requests by facility, count, sort descending with deterministic name/ID ties. No leader if no valid requests exist. |
| Pending operational queue / Attention | Current Pending service requests, including unresolved requests submitted before the selected reporting period. |
| Physical Total / Pending / Completed Bookings | Exclude existing service-resource classification and academic/schedule blocks; filter by request creation date in the selected period. The same physical total appears in System Overview and Facilities Overview. |
| Reserved / Confirmed | Approved physical bookings whose recorded Paid payment rows exist and sum to at least the booking amount. Reuses `payment_summary_query`, matching `booking_workflow.status_label`; no new status is stored. Part payments do not count. |
| Most Booked Facilities | Existing valid Approved/Completed ranking by actual scheduled use date, excluding service resources. |
| Upcoming reservations/bookings | Existing nearest future Approved physical reservations, independent of historical reporting range. |
| Recent Activities | Existing AccountActivity records by event timestamp in the selected period, newest first, limited to five. Shared formatting identifies the actor; unknown historical actors remain Unknown. No raw connection data or private metadata is exposed. |

`admin_dashboard_executive.js.render(data, payload)` receives only that protected response. It updates text using DOM `textContent`, renders bounded lists, retains same-origin links/tab authentication, and formats dates in Asia/Manila. `fail()` replaces unavailable service/audit content with honest error messages instead of manufacturing zero metrics. Existing global Retry restores the real response. The category renderer in `admin_dashboard_filter.js` now checks whether its DOM exists, so removing the donut cannot stop filtering the rest of the dashboard.

Example flow:

```text
Global date filter
  → existing Super Admin dashboard API (same authentication/RBAC)
  → build_dashboard_data
  → executive_overview + existing chart/inventory/service/audit helpers
  → existing dashboard-data event
  → small charts, service summaries, operational lists, real activity table

Sales/Booking Daily–Weekly–Monthly
  → existing chart-only event
  → only that trend changes; counts, other sections, and recommendation results stay intact
```

This approach was chosen to separate presentation from transaction logic. No order, payment, booking status, service fulfillment, or inventory write path is copied into a dashboard component.

### 5. Backend / API behavior and Analytics routes

The dashboard GET/API routes are unchanged, including inactive/unauthenticated/non-Super-Admin denial. The response adds `executive`; existing summary fields remain available. Total Bookings and the displayed booking breakdown now consistently mean physical reservations; service pending work has its own label/link. Existing live Apriori still runs once per authorized dashboard build and uses the same eligible real result set. It remains independent of the dashboard reporting range as before.

The existing `/admin-marketplace-analytics/` route now supports `module=marketplace|facilities|services|users`. Marketplace remains the default and keeps its existing permission and academic scope. Facilities delegates to the existing permission-protected Facility Analytics route. New Services/Users destinations require an active Super Admin and the corresponding existing permission; they do not grant global visibility to scoped administrators. Unknown module names or invalid date ranges reject rather than showing unrelated data.

`/admin-facility-analytics/` continues to work directly, including its existing AJAX shape. Custom links preserve the selected dates through `period=custom&date_from=...&date_to=...` (and the dashboard's start/end aliases). Services Analytics shows grouped actual request statuses. Users Analytics uses the existing User Accounts report and twenty-row table pages; account-level monitoring stays in User Management → User Monitoring.

No new endpoints, tables, duplicate activity logs, recommendation source, or synthetic fallback. No changes to payment recording, OR fields, booking completion/cancellation, inventory, or document generation.

### 6. Database / migration impact

No schema, models, migrations, permission grants, dependencies, or live record changes. No `migrate` command is needed. New files are Django helpers/templates and static CSS/JavaScript. Use the existing static deployment process when deploying; Ctrl+Shift+R refreshes cached development assets.

### 7. Tests performed, fixes during verification, and manual steps

- Final combined run: **231 Django tests passed in 66.024 seconds**, covering dashboard dates/analytics/empty states, physical/service separation, split paid payments, rankings, revenue/status/utilization, recommendations, Marketplace Admin scope, Services navigation, activity API and User Monitoring. Django system check reported no issues.
- After synchronizing the initial top-product list with its three-row refresh limit, the populated recommendation/render test plus executive tests passed again: **9 targeted tests in 3.720 seconds**. Other layouts keep their existing product-row limit.
- New tests confirm service requests do not inflate physical booking totals/rankings/upcoming lists, pending service links use Service Requests, approved+partial/full payment rules are preserved, audit actor formatting is reused, private connection data stays out, Analytics destinations work, and scoped/anonymous accounts cannot obtain new global access.
- Query regression checks verify the dashboard query count stays constant when twenty additional orders are added, within a 33-query fixture budget; queries are bounded rather than one per rendered request/product. This is a query-count check, not a production latency benchmark.
- Python compilation passed for the seven changed backend source files. Node syntax checks passed for the four changed scripts.
- **12 Chrome dashboard scenarios passed:** executive and populated recommendation fixtures at 1920, 1440, 1024, 768, 390, and 320px. Checks cover eight KPI cards, placement, no horizontal page overflow, the sales chart staying inside its card, no sample controls/data, chart grouping, Refresh, error/Retry, and recommendation View/View All. Obsolete sample events do not change live values.
- **16 Chrome Analytics scenarios passed:** Marketplace, Facilities, Services, Users at 1440, 768, 390, 320px; module links, no page overflow/JavaScript errors, and detailed facility cards present without chart errors. Desktop/phone captures were inspected.
- Confirmed issues corrected during implementation: the Booking user relation is CampusHubUser (reuse the existing requester formatter); the old 260px canvas rule overflowed the compact chart; a 320px header/actions and service Analytics action heading needed responsive wrapping. Old tests expecting detail cards on Dashboard were moved to verify their Analytics destination instead.
- Scoped `git diff --check` passed; Git's LF/CRLF notice for the existing Analytics stylesheet is not a whitespace error.

Test command (from `backend/core`):

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_periods modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_bookings modules.reports.test_dashboard_utilization modules.reports.test_most_booked_facilities modules.reports.test_upcoming_reservations modules.reports.test_facility_revenue modules.reports.test_facility_operational_status modules.reports.test_dashboard_executive modules.reports.test_marketplace_admin_dashboard modules.marketplace.test_bundle_suggestions modules.facilities.test_service_navigation accounts.test_activity_api accounts.test_monitoring --keepdb --noinput
```

Manual verification:

1. Open Super Admin Dashboard and check the eight sections in order. Confirm only Suggested Product Bundles sits beside the eight KPIs; Frequently Bought Together and Cross-Sell Suggestions are in Marketplace Overview.
2. Change global dates, Refresh, and test a no-data period. Sales, physical booking request counts, service-period counts, activity rows, and Analytics link dates should agree with eligible saved data. Current operational queues and upcoming reservations remain current.
3. Change Daily/Weekly/Monthly independently in each trend. Other totals must not change. Check chart axes and tooltips remain within their cards.
4. Open all three View … Analytics actions. Use the module navigation to reach Users. Confirm detailed categories stay in Marketplace Analytics and detailed utilization/status/revenue stay in Facilities Analytics. Apply a custom range and verify it persists between modules.
5. In a test database, compare an Approved booking with partial paid rows against one whose paid rows fully cover its amount. Only the second contributes to Reserved / Confirmed. Do not add live payments for testing.
6. Check a pending service request's action opens Service Requests with Pending/service scope; physical booking actions open Bookings. Check service requests do not appear in Most Booked Facilities or Upcoming Reservations.
7. Compare Recent Activities with User Monitoring's real event records. It should show the recorded actor or Unknown, not a guessed admin.
8. At 390/320px, check stacked sections, wrapped actions and local table scrolling. Simulate a failed dashboard request, then restore it and use Retry. No sample rows or fake zeros should appear.

### 8. Remaining limitations, troubleshooting, and learning exercise

Browser checks used actual Django-rendered templates/styles/scripts with isolated test records and mocked HTTP transport; they were not a live authenticated production or physical-phone test. Populated recommendations use the existing explicitly isolated mined fixture, not injected live orders. External fonts used available browser fallbacks in captures; configured CampusHub fonts remain unchanged. Existing modern CSS container-query / `:has()` requirements remain.

User Analytics currently describes accounts from the existing Django User Accounts report; it does not create a second mobile identity/reporting system. Most Requested Service requires actual Approved/Completed requests. Empty live recommendations remain empty until existing Apriori eligibility thresholds are met. No new inspection-analysis engine or automated service-payment/lease workflow is claimed.

Troubleshooting:

- Old long page or sample control: inspect loaded asset versions and rendered HTML after a hard refresh; do not delete database records.
- Correct API values but stale service/activity rows: inspect `executive` and the dashboard-data event handler. Failed requests should show the global Retry message and unavailable service content.
- Unexpected physical booking total: check `service_resources_q()` classification, schedule-block exclusion, creation-date period, and recorded payment rows. Never substitute service requests or the plain status text for payment eligibility.
- No actor: inspect the existing audit metadata/source through User Monitoring. Do not invent an actor from the affected user.
- Wrong Analytics dates: inspect the module link's custom dates and the server resolver; navigation should preserve the same resolved period.

Safe practice exercise: in a temporary local branch, change only the `executive-service-kpis` CSS gap from 12px to 16px. Verify desktop and phone layout, and confirm the API response and request counts are unchanged. Restore 12px. Next, run the service-isolation test in the test database and explain why a Pending service request appears in the operational queue but not in the Approved/Completed most-requested ranking. This teaches the difference between layout, query scope, and workflow eligibility without changing production data.
