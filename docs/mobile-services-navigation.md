# Flutter mobile Services tab and live catalog

## Product-focused Recent Orders and existing details workflow — November 7, 2026

1. **Cause / reason:** Latest user attachment/reference requests purchased product information in Recent Orders, superseding the earlier decision to hide it. Confirmed additional gaps: individual item images missing from the mobile payload, unknown legacy receiving methods labelled Cash on Pickup in details, and denied fulfillment leaving stale details open.
2. **Exact files / current anchors:** `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart:15` (empty state), `:209` (`_height`), `:320` (product region), `:392` (payment/date), `:559` (full-width action); `seller_workspace_content.dart:366` (401/403 recheck), `:1254` (item image/fallback), `:1282` (same existing details route); `backend/core/modules/marketplace/services/mobile_order_previews.py:30` (`item_thumbnail`); `mobile_seller_views.py:128` (optional item thumbnail field). Updated three Flutter test files, two Django test files, the new mobile feature guide, this guide and `CAMPUSHUB_CONTEXT.md`. Complete file paths, functions/data flow and verification commands: [Recent Orders guide](../campushub/docs/seller-recent-orders.md).
3. **Changes:** Preserve the header/status and carousel. Add real first-product image/name/quantity, recorded receiving method, extra-item count, explicitly labelled Order Total, payment/date region and navy View Order Details button. Keep existing type/brand/12px styling and neutral Completed/Cancelled badges. Measure the tallest page for uniform scaled card height. Show No recent orders yet and the existing image fallback honestly.
4. **How it works:** PostgreSQL snapshots → approved-owner Django workspace → existing buyer/product/fulfillment helpers → bearer Flutter service → `homeRecentOrders` → same carousel/details callback. Add only `items[].thumbnail_url`, preserving each item's own snapshot and never copying item one's photo onto later items. Multi-item card amounts remain whole-order totals. Existing details retains all item fields, customer/payment/receiving/date/destination and eligible actions. Opening details does not reload; successful fulfillment closes/reloads through the existing callback, while 401/403 also rechecks access. See the mobile guide's annotated multi-item example and safe exercise.
5. **Backend / API:** No duplicate endpoint/order model, status transition or payment rule. Per-item thumbnail is backward-compatible/read-only. Existing seller scoping/newest ordering and legacy mixed-item exclusion remain. Fulfillment never records payment implicitly.
6. **Database / migration:** None; no live record writes. A working PostgreSQL read-only check verified the selected approved seller's two recent rows, owner scope/order, stored amounts/status/payment and image-field contract.
7. **Tests:** 83 Flutter tests and 32 Django tests passed. Whole-app analysis clean (13.7s); formatting/whitespace checks passed. Covered actual API projections, owner/foreign denial, latest reads after actions, payment separation, details callback/reopen, ordinary/authorization errors, all displayed fields, multi-item total labels, missing images, carousel/dots/See All and responsive/scaled layouts. Inspected refreshed card render. Evidence: `scratch/seller-recent-orders-20261107/`.
8. **Limitations / practice:** No phone install/live fulfillment action. Current workspace snapshots refresh after confirmed changes or normal refresh; opening details adds no redundant fetch. Missing historical images use fallbacks and compact long names remain available in details. Inspect existing orders or alter isolated test fixtures; do not create real paid orders/change stock to populate the UI. Deploy the compatible backend projection with the mobile changes to receive every recorded item image.

## Fit sales filter labels on one line — November 7, 2026

1. **Cause / reason:** User requested a filter design whose label and other options fit in one row. Labels allowed wrapping and the header used a fixed stacking threshold rather than checking its rendered title/control width.
2. **Files / anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:1603` (header measurement), `:1959` (consistent label style), `:1962` (shared width), `:2028` / `:2051` (single-line menu/control text); `campushub/test/seller_home_layout_test.dart:483`, `:518`, `:608`; mobile `docs/seller-sales-refresh.md`, this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes:** Keep Daily/Weekly/Monthly on one line, allow sufficient measured width and keep the header title/filter together when space permits. Retain right-aligned accessibility stacking, current colors/radii/icons, banner, bundles position and existing refresh behavior.
4. **Functions / data flow:** `_salesPeriodWidth` measures actual label style/text scale, including icon/gap/padding/rounding space. The same width sizes trigger and popup; title measurement determines whether one header row fits. No report data is calculated or altered by this measurement. Selection still uses the same callback/API. Full explanation/example: [mobile refresh guide](../campushub/docs/seller-sales-refresh.md).
5. **Backend / API:** Unchanged; in-place sales updates, last-successful caption/amount and authorization handling preserved.
6. **Database / migration:** None.
7. **Checks:** 75 Flutter seller tests passed; whole-app analysis clean (6.9s), formatting/whitespace checks passed. Extended existing selector cases to 280dp normal and verified intrinsic label width, single-line layout and header-row fit. Inspected normal/enlarged open-menu renders. Evidence: `scratch/seller-filter-one-line-20261107/`.
8. **Limitations / safe practice:** No phone install. Header stacks only when the title and filter cannot fit at the actual text size. Exercise: switch each period at normal/enlarged text, inspect full labels and verify the dashboard stays visible; do not edit order/payment data for a text-layout check.

## Sales period changes refresh in place — November 7, 2026

1. **Cause / reason:** Confirmed `_changePeriod()` called `_load()`, setting full `_loading` and unmounting the seller content for a sales-only operation. This replaces the earlier full-period-loading behavior documented below.
2. **Exact files changed / anchors:** `campushub/lib/module_app/screens/seller_dashboard_page.dart:92` (`_load` full-refresh supersession), `:157` (`_changePeriod`), `:165` (`_readAnalytics`), `:183` (`_refreshSales`); `seller_workspace_content.dart:32` (optional sales refresh properties), `:1745` (banner progress), `:1824` (local feedback). Updated five seller test files and added the mobile repository's `campushub/docs/seller-sales-refresh.md`; this root guide and `CAMPUSHUB_CONTEXT.md` link that report. Exact test names and reproducible commands are in the mobile guide.
3. **Changes made:** Use separate sales loading/error/request state. Keep the Home content, full-width banner, existing selector/card layout, all-time order counts and other sections mounted. Show a small spinner inside Sales Overview. Ordinary failures retain successful figures/caption and show local Retry. Update only analytics on success.
4. **How it works / functions, inputs, outputs and data flow:** The menu still emits `day`/`7`/`month`. `_refreshSales` calls the existing bearer-authenticated workspace API and `_readAnalytics` validates the returned period/figures. It merges only the analytics map, keeping other data references unchanged. Generation checks ignore older sales replies and replies superseded by a full reload. Amount and label always come from the same successful map; Retry requests the last attempted period. 401/403 clears data/access even if an older request reports denial, preventing later replies from restoring it. Full data-flow details, inputs/outputs and an annotated delay example are in [the mobile refresh guide](../campushub/docs/seller-sales-refresh.md).
5. **Backend / API behavior:** No endpoint, service contract, Django business rule, revenue calculation or seller authorization change. `seller_application_service.dart` was inspected and reused without edits. The existing endpoint authorizes each period request; full loads retain the separate access-status read.
6. **Database / migration impact:** None. No Django/PostgreSQL changes, migrations or working-record writes.
7. **Tests performed:** All **74 Flutter tests passed** in the working tree and in the exact staged snapshot on a clean detached worktree. Whole-app analysis clean in both; snapshot analysis completed in 13.6s. Verified retained widget/scroll/non-analytics data, all sections, rapid selection, localized failure/retry, stale response handling, full-refresh supersession, existing pull-to-refresh, bearer transport and 401/403 clearing. Formatting/scoped whitespace checks passed. Evidence: `scratch/seller-sales-inplace-20261107/` logs and `review/` isolated worktree. No phone installation/live network check claimed.
8. **Remaining limitations / safe practice:** The reused endpoint still computes a full payload; Flutter only consumes analytics for a period change. Full refreshes and authorization failures intentionally retain their full-screen handling. Follow the mobile guide's delayed-response test exercise, or switch periods on an existing seller account and inspect the small progress/error state without editing orders/payments. Pushed mobile commit `5d66cca` to `Loyzkie2005/CampusHub-Mobile` main, including that branch's pre-existing committed `0b51008`; unrelated backend/booking working changes remain local.

## Sales period filter button radius 50 — November 7, 2026

1. **Cause / reason:** The user explicitly requested a 50px radius for the filter. This latest choice supersedes the earlier 12px/no-pill requirement for the button itself.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:1953` (period-control BoxDecoration), `campushub/test/seller_home_layout_test.dart:512` (button radius expectation), this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Change only the Sales Overview period filter button's border radius from 12 to 50. The popup menu keeps its current 12px corners. Preserve the shared width/alignment, white/navy styling, gray border, height, chevron and period labels.
4. **How it works / inputs, outputs and data flow:** `salesPeriod(compact: true)` still builds the same button and checked popup. Flutter's BoxDecoration now rounds the button with `BorderRadius.circular(50)`; the unchanged `onSelected` callback still passes `day`, `7` or `month` to the existing page reload/API flow. For example, tapping Monthly still requests the same reporting period; only the button outline changes.
5. **Backend / API behavior:** Unchanged. No authorization, reporting or sales-calculation change.
6. **Database / migration impact:** None. No schema or working-record changes.
7. **Tests performed:** Both existing selector cases passed, each covering all three labels at normal and 2x text, menu alignment/placement and the new radius. Targeted Dart analysis of the changed source/test reported No issues found. Formatting and scoped whitespace checks passed. Inspected the actual normal-size Daily/open-menu render. Evidence: `scratch/seller-filter-radius-20261107/tests.log` and exported selector/menu PNGs.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device install. Reload/rebuild Flutter if the old button shape remains. Safe exercise: open seller Home, inspect the rounded filter button and switch periods; confirm the menu still aligns and the reporting caption updates. No order or payment edit is needed to verify a corner-radius change.

## Align the open Sales Overview menu with its selector — November 7, 2026

1. **Cause / reason:** The user's screenshot showed Flutter's wider default popup beneath the compact selector. The trigger already followed the requested shape; the popup still used default minimum/intrinsic width, default corner/shadow treatment and a generous checked-item leading column. Match the menu to the selector rather than leaving a wider floating panel.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:1894` (`controlWidth`), `:1912` (local checked-item layout theme), `:1928` (zero elevation), `:1930` (menu width), `:1947` (same trigger width). `campushub/test/seller_home_layout_test.dart:562` (menu/trigger edge checks), `:577` (menu surface), `:591` (open-overlay capture). Documentation: this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Give the popup and trigger one shared width, at least 94px, sized to the longest period/current label at the actual text scale. Preserve the 48px trigger minimum height, white background, 12px corners, navy text/chevron and gray border. Apply matching corners/border and zero elevation to the popup. Compact its leading checkmark column so all three 12px menu labels align and fit. Keep the existing 8px gap below the control. Preserve the KPI banner and bundles placement.
4. **How it works / functions, inputs, outputs and data flow:** `salesPeriod(compact: true)` measures the three period labels plus any existing longer current label with `TextPainter` using the actual style, direction and text scale. It chooses the greater of 94px and the measured label width plus 46px (24px horizontal padding + 16px chevron + 6px gap), then disposes the painters. That shared width feeds both the trigger and `PopupMenuButton.constraints`. A locally scoped Theme reduces the checked item's leading area to 14px plus a 6px gap; it does not change the app theme. The existing `CheckedPopupMenuItem` retains checked semantics, selection and animation. Example: Weekly remains checked when opening the menu, and selecting Monthly still invokes the same `onPeriod('month')` callback and existing Django reload.
5. **Backend / API behavior:** Unchanged. Reporting periods, bearer authorization, validation, loading/error/retry behavior and sales calculations are untouched. The separate Sales Analytics dropdown keeps its existing implementation.
6. **Database / migration impact:** None. No dependency, record or schema change.
7. **Tests performed:** **45 Flutter tests passed** across `seller_home_layout_test.dart`, `seller_workspace_test.dart`, `seller_sales_overview_test.dart`. Whole-app `flutter analyze --no-pub`: **No issues found**, 8.7 seconds. Extended the existing selector cases to check both popup edges equal the trigger edges, consistent label-column positions, 12px popup corners, zero popup elevation and retained below-trigger placement, for all three selections at normal and 2x text. Existing transport/selection tests still pass. Formatting/scoped whitespace checks passed. Captured and inspected actual open-menu renders for Daily at 375dp/normal text and Weekly at 320dp/2x text. Evidence: `scratch/seller-menu-alignment-20261107/` (`tests.log`, `analyze.log`, `menu-*.png`).
8. **Remaining limitations / troubleshooting / safe practice:** No phone build/install. Large text can increase the common width; it is not fixed to 94px when that would clip a label. Safe exercise: open the selector for each period and compare both menu edges with the control; check that all labels line up and only the selected period has a check. Select another period, verify the caption changes, then dismiss with Back/outside tap without changing orders. If the old wide panel remains, reload/rebuild the running Flutter app. Render exports use isolated fixtures and can include Flutter's test-app debug ribbon; that ribbon was not added to application code.

## Preserve the original Sales Overview period selector — November 7, 2026

1. **Cause / reason:** The user explicitly requested preserving the original white rounded-rectangle Daily/Weekly/Monthly selector while improving surrounding Sales Overview content. Inspection confirmed the existing control already had 12px corners, a subtle gray border and 48px minimum height. Its natural width varied by label, and the enlarged-text stacked header placed it on the left.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:1603` (right-align the stacked selector), `:1909` (`seller-sales-period-control`), `:1910` (94px minimum width / 48px minimum height), `:1918` (row space-between); `campushub/test/seller_home_layout_test.dart:484` (existing menu geometry/interaction test expanded). Updated this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Preserve the existing white background, 12px radius, thin `HomeAppColors.border` border, navy text/16px downward chevron and popup interaction. Add a 94px minimum width and distribute label/chevron toward opposite sides. Retain normal top-right header placement; in the existing narrow/large-text stacked layout, right-align the selector beneath the title. No pill shape, gradient or shadow was added to the selector. The KPI banner and bundle position were retained.
4. **How it works / functions, inputs, outputs and data flow:** `salesPeriod(compact: true)` still reads `analytics.period`, maps `day`/`7`/`month` to Daily/Weekly/Monthly and builds the same `PopupMenuButton` with checked selection. `onSelected` still calls `widget.onPeriod`, which reaches `_changePeriod()` and the existing authenticated Django workspace request; the resulting totals/period caption follow the same validated response. The control's minimum dimensions keep short Daily labels approximately as wide as Monthly, while allowing enlarged text or an existing longer API label to grow. Example: choosing Daily still requests `period=day`; only its trigger's minimum width/spacing changed.
5. **Backend / API behavior:** Unchanged. Existing endpoints, seller authorization, report intervals, revenue calculations, loading/errors/retry and Sales Analytics dropdown remain intact.
6. **Database / migration impact:** None. No record, schema, migration or dependency changed.
7. **Tests performed:** **45 Flutter tests passed** across `seller_home_layout_test.dart`, `seller_workspace_test.dart`, `seller_sales_overview_test.dart`. Whole-app `flutter analyze --no-pub`: **No issues found**, 7.8 seconds. After adding optional render exports, the **2 existing selector cases passed again**, each checking all three period labels at 375dp/normal text and 320dp/2x text. Verified white fill, radius 12, border, no gradient/shadow, minimum dimensions, approximately 94px width and 48px height at normal text, right alignment and menu placement below the trigger. Formatting/scoped whitespace checks passed. Inspected normal Monthly and enlarged Daily actual renders. Evidence: `scratch/seller-period-selector-20261107/` (`tests.log`, `analyze.log`, `render-check.log`, `selector-*.png`).
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device installation. The 94px width and 48px height are minimums, permitting readable accessibility text rather than clipping it into a fixed box. A narrow/enlarged header still stacks, with the selector on the right beneath its title. Safe exercise: open seller Home, select Daily/Weekly/Monthly and confirm the trigger remains a white rounded rectangle at the header's right while the caption changes. Increase system text size and check the label/menu remain reachable. Do not edit sales records to test the selector. Reload/rebuild the app if the old Daily width or left-aligned stacked placement remains.

## Suggested Product Bundles directly below Sales Overview — November 7, 2026

1. **Cause / reason:** The user requested moving Suggested Product Bundles below Sales Overview. It previously followed Recent Orders and Inventory Alerts.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:1708` (recommendations `sectionHeader` followed by `suggestions(context, preview: true)`); `campushub/test/seller_home_layout_test.dart:835` (section-order assertion); `campushub/test/seller_workspace_test.dart:431` (ordered section-navigation exercise); `campushub/test/seller_home_entry_test.dart:386` (integrated Home geometry). Documentation: this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Move the existing bundle heading and preview as one block. Final order: Sales Overview including its KPI banner/order statistics → Suggested Product Bundles → Recent Orders → Inventory Alerts → Sales Trend. The promotional banner remains after Sales Trend. No extra section or duplicate suggestion widget was added.
4. **How it works / functions, inputs, outputs and data flow:** `homeHighlights(context)` returns its widgets in display order. It now calls `sectionHeader('Suggested Product Bundles', SellerDestination.recommendations)` and `suggestions(context, preview: true)` before `_recentOrdersHeader()`. The same Django recommendation data still enters through `widget.data`; the same preview builder creates the existing cards/empty/error message and callbacks. Example: selecting See All still opens the existing recommendations destination even though the section appears earlier. No data was reordered or recalculated on the server.
5. **Backend / API behavior:** Unchanged. Existing seller authorization, recommendation qualification, view/create-bundle actions, sales figures and reporting filters remain.
6. **Database / migration impact:** None. No schema or working-record change.
7. **Tests performed:** **68 Flutter tests passed** across `seller_home_layout_test.dart`, `seller_workspace_test.dart`, `seller_home_entry_test.dart`. Updated their existing order/geometry/navigation expectations to the requested arrangement. Whole-app `flutter analyze --no-pub`: **No issues found**, 8.2 seconds. Formatting and scoped whitespace checks passed. Inspected the refreshed actual seller Home render. Evidence: `scratch/seller-bundle-position-20261107/final-tests.log`, `analyze.log`, `overview-light.png` and the existing responsive render exports. No new test was added for this widget-only move.
8. **Remaining limitations / troubleshooting / safe practice:** Hot reload/restart or rebuild an installed app to see the order change. No physical-device installation was performed. Safe exercise: open seller Home, scroll past the Sales Overview cards and confirm Suggested Product Bundles comes next. Use See All, return, then verify Recent Orders/Inventory Alerts still follow. Empty recommendations should remain an honest empty state; do not create working orders just to populate it.

## Full-width seller Total Sales banner and verified sales flow — November 7, 2026

### 1. Cause / reason

The user requested a full-width navy Total Sales KPI above the order statistics, with the existing Daily/Weekly/Monthly filters and real authorized seller figures. The existing Home implementation placed all four KPIs in an equal two-column grid. Data tracing confirmed the backend already calculates and scopes sales correctly, so it was reused. A confirmed validation gap was also addressed: `_load()` checked only that analytics was a map. Missing/non-finite values or a mismatched reporting period could reach formatting/dropdown code; missing order fields could use presentation fallbacks. These responses now show the existing unreadable-response error instead of appearing as successful figures.

### 2. Exact files changed / current lines and code anchors

| File | Line / anchor | Actual change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 1617 `_salesOverviewBanner()`, 1620 All-time order counts, 1627 column selection, 1737 banner, 1796 `_overviewMetricCard` | Full-width revenue banner, period/basis caption, explicit zero-sales state, adaptive order cards below; reuse Analytics/Orders destinations. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 112 analytics extraction, 120 response guard, 136 unreadable-response exception | Validate the returned period, nonempty label, finite nonnegative revenue and nonnegative integer counts before publishing data. |
| `campushub/test/seller_home_layout_test.dart` | 75 `reviewFonts`, 521 title weight, 733 responsive KPI case | Use real bundled fonts for measured geometry, assert full banner width and order cards below, stress large values/text, export responsive evidence. |
| `campushub/test/seller_sales_overview_test.dart` | 18 `salesResponse`, 85 transport workflow, 221 malformed-response recovery | New HTTP-to-widget integration checks; optionally consume the actual isolated Django response fixtures. |
| `backend/core/api/test_mobile_seller_workspace.py` | 135 sales contract regression, 173 empty contract regression | Add decimal/timestamp/status/ownership/all-time/empty-state checks and optional JSON exports from PostgreSQL test records. No backend production logic changed. |
| `docs/mobile-services-navigation.md`, `CAMPUSHUB_CONTEXT.md` | Leading November 7 section | Record verified flow, decisions, testing, troubleshooting and practice. |

### 3. Changes made

Total Sales now fills the content width with the existing navy surface, gold wallet icon, white label/value, 16px corners and 18px padding. The caption uses Django's actual period label followed by Completed and paid orders. Zero qualifying orders add No completed paid sales in this period; a genuine completed paid zero-price order is still a sale and does not trigger that message. No Design preview wording or generated metric is included.

Total Orders, Completed Orders and Pending Orders appear below an All-time order counts label. Normally they share one row on a phone with sufficient width; narrower layouts use two columns or a single column. Enlarged text can stack them. Labels/values can grow rather than being clipped into a fixed aspect ratio. Reuse current typography, currency formatting and card styling. Tapping Total Sales still opens Sales Analytics; each order card still opens the existing Orders workspace, without inventing a new status filter or destination. Inventory, recent-order detail/progress, bundles, chart behavior and surrounding Home/header layouts are retained.

### 4. How it works: PostgreSQL → Django → Flutter → UI

| Stage / existing code | Inputs and work | Output / next stage |
| --- | --- | --- |
| `api/models.py`: `Product`, `MarketplaceOrder` | PostgreSQL owns product-to-mobile-seller relationships and stored order amount, quantity, payment/status and timestamps. | Actual historical order records, not current price × current stock. |
| `services/seller_applications.py:13` `applicant`; `mobile_seller_views.py:24` `approved_seller` | Verify bearer identity, active/non-suspended regular mobile account and its latest approved, non-suspended seller application. | Authorized account, or 401/403. A query-string seller ID cannot select another account. |
| `services/order_access.py:24` `seller_order_queryset` | Filter orders through `product__mobile_seller=account`; retain the existing exclusion of legacy mixed-item orders. | Only that seller's orders. Historic sales from archived owned listings remain included. |
| `services/analytics.py:64` `parse_analytics_period`; `:114` `valid_sales_queryset` | Period bounds use the configured local date. Qualifying revenue rows are Completed **and** Paid, with quantity > 0. Timestamp is `completed_at`, otherwise `paid_at`, otherwise `created_at`. | Canonical qualified orders and date range. |
| `mobile_seller_views.py:88` `workspace`, `:100`–`:105`, `:145`, `:153` | Scope the shared sales queryset to owned orders and the selected date range; use Decimal `Sum(total_price)`, count and quantity aggregate. Reuse existing trend/top-products helpers. Separately count all-time owned orders and statuses. | Existing JSON contract: `analytics.revenue/period/label/start/end/completed_orders/...`, `order_count`, `overview.completed_orders/pending_orders`, order rows and other existing workspace fields. Private/no-store response. |
| `core/urls.py:101`; `seller_application_service.dart:94` `workspace` | GET `/api/mobile/seller/workspace/?period=7&orders_page=1` with the existing SessionService bearer token. Decode JSON and existing HTTP errors. | Data map to the page; no duplicate endpoint or client-side revenue calculation. |
| `seller_dashboard_page.dart:89` `_load`, `:162` `_changePeriod` | Recheck seller status, fetch the workspace, validate required sales fields, and publish only the latest request's successful response. | Loading spinner; successful data; or error/Retry. A 401/403 clears approved access/data. Old totals are hidden during loading/errors. |
| `seller_workspace_content.dart:1588` `homeHighlights`, `:1737` `_salesOverviewBanner` | Format the server's amount through existing `money()`, read period label and all-time counts, lay out cards and call existing navigation callbacks. | Full-width banner and actionable order cards. |

Reporting behavior remains unchanged:

| Control | API key | Revenue interval |
| --- | --- | --- |
| Daily | `day` | Today in the configured Philippine timezone. |
| Weekly (existing initial selection) | `7` | Today plus the preceding six calendar days. |
| Monthly | `month` | First day of this month through today. |

The shared API's legacy Last 30 Days option remains available to existing callers; the normal seller page still starts Weekly and offers its existing three controls. Order counts remain all-time, not period totals. Revenue is not calculated from the currently loaded/paginated order list. For example, the isolated database test has four qualifying sales of 19.95 + 0.10 + 0.20 + 0.00 = **20.25**, including the timestamp fallbacks. Its nine all-time orders include seven Completed status rows, one Pending and one Cancelled; unpaid/zero-quantity Completed rows do not earn revenue. A different seller's 999 sale is excluded. These are test fixtures, not added working records.

### 5. Backend / API behavior

Existing Django JSON endpoints, bearer authentication, seller authorization, status rules, calculations, PostgreSQL query boundaries and pagination were preserved. No business logic moved to FastAPI or Flutter. Backend edits are tests only. Frontend validation requires the response period to match the requested period, a nonempty label, valid revenue and explicit integer counts. It rejects missing revenue, NaN, negative/unparseable revenue, fractional counts and unexpected periods through the existing error/Retry state. No cached value is presented as a fresh result after an error. The existing request-generation guard continues preventing older requests from replacing newer state.

### 6. Database / migration impact

No schema, table, migration, account approval, payment, order, inventory or working catalog changes. Django regressions used a disposable PostgreSQL test database. A separate working-database smoke check ran inside `SET TRANSACTION READ ONLY`, selected an actual approved active seller internally and called the existing bearer-authenticated view for all three periods. That checked seller had **two all-time orders and zero completed/paid qualifying sales** for each interval, returning 0.00 correctly. No account identity/token is printed or stored in the smoke result. Evidence: `scratch/seller-sales-overview-20261107/read_only_workspace.py` and `read-only-result.json`.

### 7. Tests performed

- **22 Django seller-workspace tests passed**, no system-check issues. Cover actual decimal sums, completion/payment/creation fallback priority, local midnight/weekly/monthly boundaries, zero-price/zero-quantity/unpaid/cancelled rows, archived listings, forged seller selection, foreign ownership, authentication/approval/suspension/inactive denial, all-time counts, pagination and read-only empty results. The existing date-boundary tests verify different totals for the three periods.
- **70 Flutter tests passed** across `seller_home_layout_test.dart`, `seller_workspace_test.dart`, `seller_home_entry_test.dart`, `seller_sales_overview_test.dart`. These include real bearer transport consuming JSON exported by the PostgreSQL tests, period requests and captions, deferred loading without stale totals, Analytics/Orders callbacks and existing order details/actions, HTTP 503 Retry, HTTP 403 data hiding, malformed response isolation and successful recovery.
- Whole-app `flutter analyze --no-pub`: **No issues found**, 10.7 seconds. Dart formatting and scoped whitespace checks passed.
- Responsive cases include 280/320dp at 2x text, 414dp, 600dp at 1.3x and 844×390 landscape, with a large currency stress value. Inspected normal, enlarged-text and landscape actual widget renders. Existing light/dark-surroundings render evidence was also produced. No accessibility score or performance benchmark is claimed.

Evidence/logs are under `scratch/seller-sales-overview-20261107/`: `backend-tests.log`, `final-flutter-tests.log`, `final-analyze.log`, `sales-day/7/month.json`, `overview-light/dark.png` and responsive `sales-*.png`. Exported JSON comes only from isolated test records. Test-harness issues found and corrected: JSON mock responses need UTF-8 content headers for the peso symbol; map fixtures need explicit mutable types; geometric badge checks need the real bundled fonts instead of Flutter's square test font. No working production API was changed to accommodate a fixture.

To reproduce the verified integration chain from the project root using this session's disposable PostgreSQL runner:

```powershell
$env:SELLER_SALES_REVIEW_DIR = (Resolve-Path 'scratch/seller-sales-overview-20261107').Path
backend/core/venv/Scripts/python.exe -B scratch/schedule-policy-20261105/run_tests.py api.test_mobile_seller_workspace
# The preceding test exports the three actual test API responses.
Set-Location campushub
$env:SELLER_HOME_REVIEW_DIR = $env:SELLER_SALES_REVIEW_DIR
flutter test --no-pub test/seller_home_layout_test.dart test/seller_workspace_test.dart test/seller_home_entry_test.dart test/seller_sales_overview_test.dart --reporter expanded
flutter analyze --no-pub
```

### 8. Remaining limitations, troubleshooting and safe practice

No APK release/install or physical-phone verification. The cross-layer integration uses actual PostgreSQL-backed Django response fixtures transported through Flutter's mocked HTTP client; it is not a live network/device test. The working-database check exercised the authenticated Django view in a read-only transaction, not deployed middleware/network connectivity. Extreme amounts can wrap at enlarged text sizes so the complete value stays visible. The checked live seller currently has no qualifying sales; that is data, not a failed calculation.

If totals look wrong, compare **completed-and-paid** stored orders by the fallback timestamp and selected bounds; do not compare the revenue banner with all-time Completed status counts or just the first order page. If data is unavailable or malformed, Retry shows an error rather than a fabricated empty-success result. If an installed app still shows four equal KPI tiles, reload/rebuild it from the updated Flutter source.

Safe practice: sign in as an existing approved seller, note the Weekly caption and total, switch Daily then Monthly and check each caption. Tap Total Sales to inspect existing Sales Analytics and return; tap Total Orders and inspect actual records without changing status/payment. Increase system text size and verify the banner/cards remain readable. Do not create test sales, mark unpaid orders paid or approve a seller merely to fill this screen. For a safe code exercise, change only the banner padding in a local branch, rerun the responsive tests, inspect the screenshots and restore 18px; the database totals must remain identical.

## Seller-style identity header across all regular Dashboard tabs — November 6, 2026

1. **Cause / reason:** The user requested copying the seller dashboard header to the non-seller/regular Dashboard across every section. Inspection confirmed the background, outlined avatar, notification action and search bar were already shared, but regular users had an extra hamburger button, no greeting above their name and a separate welcome in the Home body. Their header identity also opened Profile instead of the drawer.
2. **Exact files changed / current lines and anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:319` (shared identity-row padding), `:323` (`HeaderProfileButton`), `:426` (`showWelcomeGreeting: false`); `campushub/test/dashboard_header_test.dart:103` (greeting placement/absence of separate hamburger), `:244` (identity opens drawer), `:251` (Profile through bottom navigation); `campushub/test/dashboard_search_appbar_test.dart:125` (shared greeting/drawer on all five tabs); `campushub/test/seller_home_entry_test.dart:634`, `:775` (regular-user greeting expectations); `campushub/test/dashboard_chat_startup_test.dart:50` (startup greeting expectation). Updated this guide and `CAMPUSHUB_CONTEXT.md`. Other unpushed changes were preserved.
3. **Changes made:** Use the seller's existing 14px left identity-row inset and avatar + “Welcome Back,” + authenticated full-name arrangement for everyone. Remove the regular-only hamburger. Tapping the avatar/name opens the existing drawer with the accessible Open menu action. Show this same header above Home, Marketplace, Services, Facilities and Profile. Suppress the duplicate Home-body welcome through the existing `showWelcomeGreeting` option. Keep regular users' five navigation destinations and Home promotional banners.
4. **How it works / functions, inputs, outputs and data flow:** `DashboardScreen.build()` reads the existing `_user` and supplies it to `HeaderProfileButton`, which derives the actual profile photo/name or its existing fallback; it does not invent identity data. The common `header` sits above the PageView, so `_goToTab(index)` changes the content while the identity layout remains. The identity callback calls `_scaffoldKey.currentState?.openDrawer()`. Profile remains reachable from bottom navigation and the drawer's profile entry. Example: a regular account opens Services, taps its avatar, closes the drawer with Android Back and stays on Services with the same header. Seller approval is still read separately and only controls seller workspace/tools and Add Product; matching header appearance grants no permissions.
5. **Backend / API behavior:** No endpoints, permissions, seller approval checks, profile saving, searches or notification behavior changed. Existing regular/seller drawer filtering remains. The separate Messages route and nested detail-page headers were outside this shared Dashboard-tab layout request and retain their existing layouts.
6. **Database / migration impact:** None. This task changes Flutter presentation and associated tests/documentation only. No accounts, seller access, catalog records or schema were modified.
7. **Tests performed:** **50 Flutter tests passed** across `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart`, `dashboard_chat_startup_test.dart`, `header_profile_button_test.dart`, `dashboard_center_add_button_test.dart`, `services_screen_test.dart`. Covered all five regular tabs, avatar drawer opening/Back preserving the tab, Profile via bottom navigation, search/notifications, regular/seller access and approval/revocation. Existing responsive captures cover regular headers at 320/375/390/844dp and 320dp with 2x text; inspected the 390dp and enlarged 320dp actual renders. `flutter analyze --no-pub`: **No issues found**. Dart formatting passed. Logs/renders are in `scratch/regular-dashboard-header-20261106/`; test fixtures did not mutate working records.
8. **Remaining limitations / troubleshooting / safe practice:** Hot reload/restart the source app, or rebuild an installed app, to see the new layout. No APK install or physical-device verification was run. Long names keep the existing single-line ellipsis; enlarged search text can wrap. Safe exercise: sign in with a regular account, visit each of the five bottom tabs, tap the avatar and press Back; verify the same tab remains. Open Profile using the bottom tab, then return Home and confirm only the header has the welcome greeting. Do not approve an account as a seller merely to test the shared styling. If a hamburger remains on one of these tabs, check that the running build includes the shared `DashboardScreen.build()` changes rather than changing drawer permissions.

## Transparent Home banner surround and no Marketplace item count — November 6, 2026

1. **Cause / reason:** The user identified the Home banner as the white rectangle to remove and requested removing Marketplace's “7 items”/item-count label. The banner's enclosing Material explicitly painted white around the rounded slides and their dots. Marketplace's heading rendered a second Text with the filtered product count.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/widgets/home/campus_home_banners.dart:268` (`MaterialType.transparency`); `campushub/lib/module_app/screens/dashboard_screen.dart:861` (Marketplace heading Row); `campushub/test/campus_home_banners_test.dart:57` (outer Material assertion), `:167` (current bundled Inter font for optional render exports); `campushub/test/dashboard_search_appbar_test.dart:100` (Marketplace count absence). Updated this guide and `CAMPUSHUB_CONTEXT.md`. The associated web form/database changes are documented in the leading sections of `docs/service-configuration.md` and `docs/product-record-cleanup.md`.
3. **Changes made:** Make only the Home carousel's outer Material transparent. Remove the product-count Text beside the Marketplace category heading. Keep banner slides, photographs, rounded corners, existing colors, dots, actions, swipe/timing behavior and actual product sections/category filters. Extend existing tests; load the current bundled Inter font when the optional banner screenshot export runs so text is readable in evidence.
4. **How it works / functions, inputs, outputs and data flow:** `CampusHomeBanners.build()` still builds the same Column, PageView and indicators, but its Material no longer paints a white surrounding rectangle. The underlying Home background shows around the rounded slide/dots. `_MarketplacePageState.build()` still passes `_filteredCategoryProducts` to `_buildProductsSection()`; it simply omits the count presentation beside Products/the selected category. Example: seven returned products still render through the same product cards, but there is no “7 items” label. There is no change to fetching, sorting, category selection or a record's stock quantity.
5. **Backend / API behavior:** No Flutter service/API contract changed. Normal product loading and service navigation remain. The separately authorized catalog cleanup now returns no services, and Hyyy is excluded from active product results by the backend's existing archived filter.
6. **Database / migration impact:** These two Flutter presentation changes perform no database writes and require no migration or dependency. Separately, the approved cleanup deleted the single Food Analysis service and archived Hyyy while preserving inventory/history; see the two cleanup guides for exact IDs, backup and verification.
7. **Tests performed:** **20 Flutter tests passed** across `campus_home_banners_test.dart`, `dashboard_search_appbar_test.dart`, `home_page_test.dart`, `services_screen_test.dart`. Whole-app `flutter analyze --no-pub` reported **No issues found**. After adding the optional render font, all **4 banner tests passed again**, exporting actual renders at 320dp with normal and 2x text. Inspected the normal render and web Add Service desktop/phone renders. Dart formatting passed. Evidence/logs: `scratch/service-form-cleanup-20261106/`. The initial test finder used an unsupported Flutter API; corrected it to `find.byWidgetPredicate` and reran successfully.
8. **Remaining limitations / troubleshooting / safe practice:** Source changes need a Flutter hot reload/restart or rebuilt installed app before a phone shows them. The rounded photo slide itself keeps its existing surface/overlay; only its outer rectangle was removed. The item-count removal does not remove quantity/stock data elsewhere. Safe exercise: open Home and inspect the slide corners/dots, swipe and tap its existing destination; open Marketplace, choose a category and verify the heading/cards update without an item count. Do not add/delete products to test a label. The browser verification used isolated exported fixtures; no physical-device release build or live checkout was performed.

## Remove the duplicate Services-tab search field - November 6, 2026

1. **Cause / reason:** The user requested removal of the extra search bar inside Services. Dashboard already provides the shared Search CampusHub header entry, so Services displayed two search controls.
2. **Exact files changed / anchors:** `campushub/lib/module_app/screens/services_screen.dart:48` (`build`), `:72` (Available Services), `:97` (catalog iteration); `campushub/test/services_screen_test.dart:73` (no duplicate field / details access), `:109` (loading/empty/retry), `:162` (retained tab state and shared search); this guide; `CAMPUSHUB_CONTEXT.md:3`. Profile onboarding files changed for the same request; see the leading section of `docs/mobile-profile.md`.
3. **Changes made:** Remove the local Search services TextField, its spacing, `_query`, local filtering and search-miss state, plus its unused Lucide import. Render the loaded services directly. Keep the Services/Available Services headings, existing catalog cards, pull-to-refresh, loading/error/empty states, retry and details/request guidance. Keep the shared header search unchanged.
4. **How it works / functions, inputs, outputs and data flow:** `_load()` still reads `ServiceCatalog.fetchServices()` and stores actual records in `_services`, or sets the existing error/loading state. `build()` now iterates `_services` without a second local query. Selecting a card still pushes Service Details with the existing ID/catalog, where the active service is revalidated. Dashboard's header search still opens the existing cross-catalog Search page; returning preserves the current Services tab and loaded catalog. Example: two real services returned by the catalog both appear; there is no stale local text silently filtering one out. This avoids maintaining a redundant search field without creating another route or API.
5. **Backend / API behavior:** None changed. Existing catalog/search/detail services, authenticated office messaging and service-request guidance remain. No service workflow, facility logic, permission or account changes.
6. **Database / migration impact:** None. No schema, migration, dependency, record, rate or deployment changes.
7. **Tests performed:** Shared final run: `flutter test --no-pub test/services_screen_test.dart test/profile_academic_test.dart test/onboarding_preview_test.dart test/dashboard_search_appbar_test.dart test/food_preferences_test.dart --reporter expanded`: **30 tests passed in 10 seconds**. Checks no duplicate field, service details at 320/390/844px, empty/loading/error/retry, retained catalog across tab changes, actual shared-header Search navigation and onboarding behavior. `flutter analyze --no-pub`: **No issues found**, 17.0 seconds. Formatting/scoped whitespace checks passed. Inspected actual Services capture at `scratch/services-onboarding-bottom-20261106/services-390.png` (isolated fixture); enlarged-text captures also available at 320px. First capture lacked some fonts; capture-only font loading was corrected and the final run/captures repeated.
8. **Remaining limitations / safe practice:** No physical-phone, live-catalog, screen-reader or full-suite verification. Standalone ServicesPage has no local search; use Dashboard's shared header for searching. Safely run the fixtures, visit Services, open a service, return, switch tabs and verify the catalog stays loaded. Tap header Search and return to Services; ensure no second search field appears. Do not create actual laboratory, assessment or lease requests for this presentation check.

## Same continuous navy/gold background across the five main tabs - November 6, 2026

1. **Cause / reason:** The extended background was gated by seller approval and Home selection. The user requested the same color across every section. This change covers Dashboard's Home, Marketplace, Services, Facilities and Profile tabs. Other independently pushed screens retain their existing surfaces.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:309` (`dashboard-brand-header`), `:401` (body backdrop), `:476` (embedded Profile); `campushub/lib/module_app/screens/profile_page.dart:28`, `:42`, `:387` (`transparentBackground`); `campushub/test/dashboard_header_test.dart:148`, `campushub/test/dashboard_search_appbar_test.dart:125`, `campushub/test/seller_home_entry_test.dart:287`; this guide. The accompanying requestor and Job Order changes are documented in the newest section of [the booking guide](booking-module-chatgpt-context.md).
3. **Changes made:** Always paint the existing extended navy `#1A1851` / gold `#FCB316` / white background behind Dashboard's original header and PageView. Remove the tab/seller condition and redundant header-local backdrop. Opt embedded Profile into transparency so its opaque background cannot hide the shared color. Preserve all white cards, search surface, spacing, controls and navigation. No new dependency or redesign of the tab contents.
4. **How it works / data flow:** `_NavyGoldHeaderBackground(extended: true)` remains a paint-only `IgnorePointer` layer: the existing navy stops, central translucent gold and white fade produce the same background for every selected tab. Tab selection still changes PageView and existing actions. `ProfilePage(transparentBackground: true)` renders a transparent outer ColoredBox; the default is `false`, preserving Profile's standalone background. Example: opening Profile from the drawer still uses the existing callback and data loading; only the outer paint becomes transparent. The gradient follows viewport height rather than measured card positions.
5. **Backend / API behavior:** No API, permission, messaging, notification, search, profile or seller-state contract changes. Existing real records and callbacks remain authoritative.
6. **Database / migration impact:** None. No model, schema, migration, dependency or working-record changes.
7. **Tests performed:** Final six-file suite (`dashboard_header_test`, `dashboard_search_appbar_test`, `seller_home_entry_test`, `facility_booking_flow_test`, `covered_court_booking_test`, `profile_page_test`): **57 tests passed in 30 seconds**. This is one shared run, not an additional 57 beyond the booking guide's result. Final `flutter analyze --no-pub`: **No issues found**, 14.6 seconds. Dart formatting and scoped whitespace checks passed. Inspected actual Services and Profile tab captures plus normal/enlarged-text requestor captures in `scratch/shared-tabs-requestor-20261106/`. The seller tab check visits Profile through the existing drawer identity action; seller navigation intentionally uses its center slot for Add Product. Earlier failed attempts were corrected: solid-header expectations, a lazy review-list lookup and the test's incorrect Profile entry assumption.
8. **Remaining limitations / safe practice:** No physical-phone verification or full-suite pass claim. Existing unrelated Recent Orders badge-width failures from the earlier work were not rerun or fixed. To verify safely, use the isolated fixture tests and visit all five main tabs, open the drawer's Profile identity, then return Home; check that one gradient remains visible and each original action still works. Compare default standalone Profile with its embedded version. Tune only the existing paint stops if needed, without changing metrics, permissions or records.

## Continuous top navy and FCB316 blend into the overview - November 6, 2026

1. **Cause / reason:** The user clarified that the requested color runs continuously from the top navy header toward the center of the four cards, rather than being a separate central glow. Their latest explicit color is `#FCB316`; this follow-up uses that value for the background blend. Existing unrelated local edits were preserved.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:308` (`extendOverviewGradient`), `:407` (shared body backdrop) and `:521` (`_NavyGoldHeaderBackground`, extended mode); `campushub/lib/module_app/screens/seller_workspace_content.dart:1672` (`homeHighlights` grid restored without the separate glow wrapper); this guide. No test source or other application file changed in this follow-up.
3. **Changes made:** On approved Seller Home, paint one navy/gold background behind both the original header and content Column. Make that header transparent so the gradient has no seam below Search. The navy softens down toward the central overview area, with translucent FCB316 gold, then fades to white. Remove the separate grid-only radial decoration. White card/search Materials, measured grid geometry, header actions, typography and Cart removal remain. Other main tabs retain the shared header-only gradient using the same background gold value.
4. **How it works / data flow:** Existing seller approval and selected-tab state determine `extendOverviewGradient`. `_NavyGoldHeaderBackground(extended: true)` uses viewport-based navy fade stops `[0, .12, .3, .55, 1]`, a central gold radial layer and a final white fade by 58% of the visible body. Positioned.fill/IgnorePointer paints behind the original header/PageView Column without changing layout or intercepting input. The same helper defaults to its shorter header-only fade on other tabs. `homeHighlights(context)` still calculates the four KPI cards from existing server data; it now returns its original grid Column. Example: switching to Services removes the extended overview backdrop but keeps the existing header controls and short gradient.
5. **Backend / API behavior:** None changed. Actual metric values, permissions, profile/sidebar, Search, notifications, seller access, cart data and refresh use their existing callbacks/services.
6. **Database / migration impact:** None. No dependencies, models, migrations, API routes or working records changed.
7. **Tests performed:** Existing `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart`, `header_profile_button_test.dart`, `seller_workspace_test.dart`, `dashboard_center_add_button_test.dart`, `search_page_test.dart` and `system_navigation_surface_test.dart`: **67 tests passed in 35 seconds**. Final `flutter analyze --no-pub`: **No issues found**, 16.9 seconds. Formatting and scoped whitespace checks passed. Inspected actual 390px and 320px/200% Seller Home captures in `scratch/navy-gold-header-to-cards-20261106/`: continuous navy-to-warm-gold-to-white background, retained white cards/search and original spacing/actions. Existing large-text, shared-tab, drawer, seller-state and navigation checks passed.
8. **Remaining limitations / safe practice:** No physical-phone or live-record verification. The extended fade follows viewport height, so its position relative to the grid changes with text scale and scrolling; it is not a measured attachment to the grid center. The two separate Recent Orders badge-width failures documented below were not rerun or fixed in this color-only follow-up. Safely use the existing fixture/capture suites to inspect normal and enlarged text, scroll and switch tabs; confirm the profile row remains dark enough for its white text and card contents remain unchanged. Tune paint stops only, without changing actual metrics or grid dimensions.

## Faint gold centered behind the four Sales Overview cards - November 6, 2026

1. **Cause / reason:** The user requested a color suggestion behind the center of the four cards, then asked to continue. Applied a faint FCB315 gold glow to complement the existing navy header. Inspected local source and preserved unrelated pending edits.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_workspace_content.dart:1588` (`homeHighlights`), specifically the grid wrapper at `:1672` (`seller-overview-center-glow`); this guide. Dart formatting also compacted the existing `_banner` getter and banner widget list in that file without changing behavior. No header, card implementation or test source changed in this follow-up.
3. **Changes made:** Wrap the original two-by-two KPI grid in a paint-only DecoratedBox with a centered gold radial gradient: 20% -> 8% -> transparent. Preserve opaque white cards, the original 12px gaps, measured card sizes, typography, values and taps. No border, shadow, extra padding, blur or dependency was added.
4. **How it works / functions and data flow:** `homeHighlights(context)` still reads actual workspace overview/analytics values, measures text and builds the existing grid. Its new DecoratedBox sizes from that same grid Column, so `Alignment.center` follows the center of the four cards rather than the screen viewport. RadialGradient radius `.6` and stops `[0, .45, 1]` feather FCB315 into transparency. Example: increasing text scale grows the existing cards and their parent; the glow remains centered in the grid. The decoration paints behind the white Materials, allowing color to show in the central gaps while card content and InkWell navigation remain unchanged. The reused grid also receives the same treatment in the existing dedicated overview.
5. **Backend / API behavior:** None changed. Actual metrics, permissions, refresh, order/payment semantics and navigation remain in their existing services. No sample business values were added to application code.
6. **Database / migration impact:** None. No models, migrations, dependencies, API routes or working records changed.
7. **Tests performed:** `flutter analyze --no-pub`: **No issues found**, 20.0 seconds. Combined `seller_home_entry_test.dart`, `seller_home_layout_test.dart` and `seller_workspace_test.dart`: **66 passed, 2 failed** in 30 seconds. The failures are the independent Recent Orders badge-width assertions for `ready_for_pickup` and `unclassified` at `seller_home_layout_test.dart:460`, measuring 201px and 190.75px against a required width below 154.5px. An isolated `--plain-name recent-order` run reproduced both failures while rendering the unchanged SellerRecentOrders widget directly (four other badge cases passed), without mounting the modified grid. The affected Home/workspace suites alone then **passed all 40 tests in 21 seconds**. Formatting and scoped whitespace checks passed. Inspected actual 390px and 320px/200% captures in `scratch/overview-centered-gold-20261106/`: centered faint gold, white cards, unchanged navy header and retained spacing.
8. **Remaining limitations / safe practice:** The two separate Recent Orders badge tests remain failing and were not changed as part of this color task. No physical-device install, live metric edits or performance benchmark. Safely use existing fixtures to change text scale or amounts, rerun the Home/workspace suites and inspect the central grid gap; confirm card taps still reach their existing destinations. Tune only radial alpha if needed, keeping the final transparent stop and no added grid padding. Never alter live dashboard records to test decoration.

## Restored pure navy and FCB315 header gradient - November 6, 2026

1. **Cause / reason:** The latest instruction restores a gradient using official navy `#1A1851` and gold `#FCB315`. This supersedes the solid-navy intermediate treatment and the earlier muted/light-blue palette. Inspected current local changes and preserved unrelated work.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:308` (`header`), `:337` (dark-surface identity), `:378` (status-bar styling), `:402` (white body/original Column) and `:506` (`_NavyGoldHeaderBackground`); `campushub/lib/module_app/widgets/navigation/header_profile_button.dart:19` (`onDarkSurface`, name color at 50 and greeting color near 108); `campushub/test/dashboard_header_test.dart:141` (navy base, white identity/body, restored gradient); `campushub/test/dashboard_search_appbar_test.dart:110` (all-tab header checks); `campushub/test/seller_home_entry_test.dart:158` (gradient/identity expectations and section checks); `campushub/test/header_profile_button_test.dart:88` (dark/default text and photo preservation); this guide. These include the readable-text changes from the interrupted solid-header step.
3. **Changes made:** Restore a header-only navy gradient with a restrained FCB315 radial glow and a white lower fade. All gradient color inputs derive from those brand colors and the existing white page surface; no muted-blue/lavender presets remain. Smooth the dark-to-white transition with a navy-derived intermediate tint instead of a flat dark block. Keep the search surface white, display white identity/greeting/menu/bell glyphs over the dark header, and use light status-bar icons on navy. The dashboard/cards below stay white. Header spacing, profile image/outline, search/navigation and Cart removal remain.
4. **How it works / data flow:** Dashboard paints `_NavyGoldHeaderBackground` through Positioned.fill/IgnorePointer behind the original SafeArea controls. The helper paints navy -> an opaque 85%-navy blend -> the actual page white, then the gold glow and white fade. The decoration cannot intercept taps or add layout height. `HeaderProfileButton(onDarkSurface: true)` only changes its name/greeting text to white; the default remains unchanged for other callers, and the same actual `AuthUser` photo/name/callback are reused. Example: a seller identity tap still opens the existing drawer; changing the gradient does not change approval or selected-tab state. The full-page color backdrop is removed, so the original body Column and white Scaffold host the unchanged dashboard cards.
5. **Backend / API behavior:** None changed. Profile/sidebar, notifications, Search, cart data, seller permissions, metrics and refresh retain their existing services and recorded data.
6. **Database / migration impact:** None. No dependencies, models, migrations, API routes or working records changed.
7. **Tests performed:** Final **67 widget tests passed in 46 seconds** across `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart`, `header_profile_button_test.dart`, `seller_workspace_test.dart`, `dashboard_center_add_button_test.dart`, `search_page_test.dart` and `system_navigation_surface_test.dart`. Final `flutter analyze --no-pub`: **No issues found**, 32.3 seconds. Formatting and scoped whitespace checks passed. Inspected actual Seller Home captures at 390px and 320px/200% text under `scratch/shared-header-navy-gold-20261106/`: dark navy/gold header, readable white identity/bell, white search, smooth lower transition and white dashboard/card area. Tests preserve shared-tab behavior, drawer/Search/Notifications, seller state, spacing, actual image/default identity behavior and no Cart header control. The first restored fade was refined to remove its flat dark band, then checks/captures were rerun.
8. **Remaining limitations / safe practice:** No physical-phone verification, live data edits, or measured contrast/performance claim. The gold is translucent over navy rather than a large solid-yellow panel. Safely run the fixture suites, inspect regular/enlarged text, switch through the main tabs and tap the existing header actions. Verify the body remains white and the status icons stay light. When tuning the fade, keep the profile row dark enough for its white text and preserve the final page-white endpoint; do not modify real accounts or metrics for styling tests.

## Stronger muted blue after the navy reduction - November 6, 2026

1. **Cause / reason:** The user found the navy treatment too dark, then requested more visible blue after the initial lightening. The current gradient stops were already opaque, so this follow-up increases blue saturation/intensity rather than opacity. Inspected local source and preserved unrelated pending changes.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:521` (`_DashboardBackdrop`, base gradient around 538 and navy ambient layer around 555); this guide. No test source or other application file changed in this follow-up.
3. **Changes made:** Strengthen the opaque blue stops from `#CDDCF2`/`#E9F0FA` to **`#B7CFF0` -> `#DCE9F9`**, followed by the existing white page surface. Retain the reduced navy ambient layer, FCB315 gold, existing fade positions, white cards/search, shared headers across the main tabs and the removed Cart action. This follow-up changes only those two color values, with no layout or callback changes.
4. **How it works / data flow:** `_DashboardBackdrop(headerOnly)` uses the same existing header-only/overview fade stops and now supplies the new opaque blue colors to LinearGradient. Its navy/gold radial layers still paint behind controls, followed by the white fade. Example: changing the first blue stop adjusts the visible top color without changing header height, card placement, catalog data or selected tab. Opaque stops retain the smooth interpolation established by the previous fix.
5. **Backend / API behavior:** None changed. Profile/sidebar, notifications, Search, seller access, metrics, cart data and refresh continue through their existing services.
6. **Database / migration impact:** None. No dependencies, models, migrations, API routes or working records changed.
7. **Tests performed:** Existing `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart` and `dashboard_center_add_button_test.dart`: **34 tests passed in 27 seconds**, with actual header captures enabled. Final `flutter analyze --no-pub`: **No issues found**, 12.0 seconds. Formatting and scoped whitespace checks passed. Inspected the actual 390px Seller Home capture under `scratch/shared-header-stronger-blue-20261106/`: stronger blue header, retained central gold blend, white cards and smooth lower fade. Existing shared-tab, drawer, large-text, search, notification and no-Cart assertions passed.
8. **Remaining limitations / safe practice:** No physical-phone verification or contrast/performance measurement. To safely tune the shade, adjust only these two opaque stops, rerun the fixture/capture suites and compare normal/large-text headers; keep the existing white fade, actions and actual records unchanged.

## Smooth official-navy tint replaces the light-blue base - November 6, 2026

1. **Cause / reason:** The user requested smooth navy blue instead of the current light-blue background. Inspected the latest local state and preserved all unrelated pending changes.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:521` (`_DashboardBackdrop`, base colors at 540); this guide. No test source, card, navigation or backend file changed in this follow-up.
3. **Changes made:** Replace the `DDE8FF`/`EFF5FF` base stops with soft tints derived from official navy `#1A1851` over the existing white page surface. Retain the FCB315 gold, existing shared-header coverage, overview fade extent, white cards/search and removed Cart action. No layout, typography, button or callback changes.
4. **How it works / data flow:** `_DashboardBackdrop(headerOnly)` still selects its existing short-header or overview fade stops. `Color.alphaBlend` combines approximately 24% and 8% navy with `HomeAppColors.appBackground` before supplying opaque colors to LinearGradient. The input is the existing page surface; the output is an opaque navy-tinted color. Example: the first stop uses `0x3D1A1851` blended over white; the next uses `0x141A1851`, followed by the unchanged white stops. Pre-blending avoids the faint alpha-interpolation band observed with directly transparent gradient stops. The original navy/gold radial accents and final white fade still paint behind the controls.
5. **Backend / API behavior:** None changed. Profile/sidebar, notifications, Search, account/seller access, cart data and dashboard processing use their existing services/actions.
6. **Database / migration impact:** None. No dependencies, models, migrations, API routes or working records changed.
7. **Tests performed:** Existing `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart` and `dashboard_center_add_button_test.dart`: **34 tests passed in 16 seconds**, with actual header capture harnesses enabled. Final `flutter analyze --no-pub`: **No issues found**, 6.6 seconds. Formatting and scoped whitespace checks passed. Inspected Seller Home and Services header captures in `scratch/shared-header-soft-navy-20261106/`: smooth navy tint, retained gold/white surfaces, Cart absent and original geometry preserved. The initial transparent-color attempt was refined to opaque pre-blended colors after visual review, then the tests/analysis/captures were rerun.
8. **Remaining limitations / safe practice:** No physical-phone verification or measured contrast/performance claim. The navy is intentionally tinted for the existing dark text rather than a solid dark background. Safely rerun the fixture suites, inspect the shared header at normal/enlarged text and switch tabs; confirm the same actions and white fade remain. Tune only the navy blend alpha values if needed, then render again; do not alter live records or unrelated screen styles.

## Shared main-tab header and removal of its Cart action - November 6, 2026

1. **Cause / reason:** The user requested the top header on every section and removal of Cart. Applied this to the five existing Dashboard tabs: Home, Marketplace, Services, Facilities and Profile. Inspected existing pending changes before editing and preserved unrelated work.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:309` (`header`, shared profile/search styling), `:341` (`outlinedAvatar`), `:345` (seller greeting/drawer action), `:370` (shared search prompt/font) and `:521` (`_DashboardBackdrop`); `campushub/test/dashboard_header_test.dart:141` (common header and no Cart), `campushub/test/dashboard_search_appbar_test.dart:110` (all-five-tab checks), `campushub/test/seller_home_entry_test.dart:223` (no Cart) and `:285` (seller section switching, drawer checks and captures); this guide.
3. **Changes made:** All five main tabs use the outlined profile, Montserrat **Search CampusHub...** bar and soft blue/navy/FCB315 palette. Seller identity/greeting and its profile-to-drawer action are consistent across these tabs. Regular accounts retain their existing menu and profile destination. Remove the main header Cart button, its local key and unused widget/icon imports. CartService is still used by existing marketplace add-to-cart behavior and was not edited. The approved Seller Home keeps its extended glow around the overview; the other tab headers fade to white before their existing page content, avoiding a rectangular seam.
4. **How it works / data flow:** Dashboard still uses actual `_user`, approved seller state and selected tab. The common header passes existing callbacks to HeaderProfileButton and HeaderSearchButton. `_DashboardBackdrop(headerOnly: true)` reuses the same colors with a shorter fade inside non-overview headers; Seller Home uses the existing full backdrop behind its original content. No new header route or duplicate search controller was added. Example: select Services -> shared outlined identity/search/notification header remains -> tapping seller identity opens the existing drawer -> Back closes it and leaves Services selected. Search continues through `_openSearch()` and the existing SearchPage; Notifications still opens its current permission sheet.
5. **Backend / API behavior:** None changed. Existing account identity, seller approval, catalog loading, chat, notification, cart data and transactions retain their current services/permissions. Other dedicated detail/checkout/workspace app bars and bottom-navigation configuration were not redesigned.
6. **Database / migration impact:** None. No new dependency, migration, schema, API route or working-record change.
7. **Tests performed:** Final **67 Flutter tests passed in 26 seconds** across `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart`, `header_profile_button_test.dart`, `seller_workspace_test.dart`, `dashboard_center_add_button_test.dart`, `search_page_test.dart` and `system_navigation_surface_test.dart`. Final `flutter analyze --no-pub`: **No issues found**, 10.4 seconds. Formatting and scoped whitespace checks passed. Assertions verify all five regular-account tabs retain the gradient/outline/search and have no Cart tooltip; seller Marketplace/Services/Facilities retain greeting, header and working drawer access. Existing status/refresh, navigation, large-text and Sales Overview spacing checks remain. Inspected header regions in actual Seller Home, Services and Facilities captures under `scratch/shared-header-no-cart-20261106/`; Cart is absent and the non-overview headers blend into white. Initial tests still expected the old alternate seller hamburger/profile header and were updated to exercise the requested uniform header instead.
8. **Remaining limitations / safe practice:** No physical-device install or live catalog verification. Captures use isolated fixture/offline data; body default-font placeholders in that harness are not a claim about production content rendering. Safely run the suites, switch through the five main tabs, confirm one Search bar and Notifications action, verify Cart is absent from the top header, and open/close the drawer from seller identity on another tab. Keep existing profile/cart records unchanged. The unrelated previously deleted `test_add_icon_test.dart` was left untouched.

## Corrected FCB315 gold blend toward the four-card center - November 6, 2026

1. **Cause / reason:** The user requested more gold/color reaching the central area of the four Sales Overview cards, then explicitly corrected the requested gold from `#FCB316` to **`#FCB315`**. This supersedes the preceding header-only fade extent. Inspected the current pending changes; unrelated work was preserved.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:313` (transparent Seller Home header), `:410` (background behind the original body Column) and `:525` (`_SellerOverviewBackdrop`); this guide. No card component, test source, service or backend file changed in this follow-up.
3. **Changes made:** Keep the soft-blue/ice-blue palette and official navy. Move the paint layer behind the shared header/content again, and place a stronger, feathered **FCB315** radial glow toward the overview's central area. The base reaches white at 52% of viewport height; a final fade covers residual glow by 55%, keeping lower content white. The 390px render shows the gold blend at the central gap between the four white cards. No lavender/pink, whole-header frame, shadow or new dependency was added. Search/cards, spacing, labels, values and navigation remain unchanged.
4. **How it works / data flow:** Existing `isSellerHome` mounts a Positioned.fill/IgnorePointer backdrop beneath the original header/PageView Column. `_SellerOverviewBackdrop` paints blue -> low-opacity navy -> gold -> white fade. Gold uses `RadialGradient(center: Alignment(0, -.22), radius: .75)` with alpha `0x33` -> `0x14` -> zero and the corrected RGB **FCB315** throughout. For example, the glow is strongest near 39% of the visible body height and softly disappears below the overview; it cannot intercept card taps. Existing white card Materials stay opaque. Other tabs keep their prior white background.
5. **Backend / API behavior:** None changed. Profile/sidebar, notifications, cart, Search, seller eligibility, metrics, orders and refresh keep their existing records and callbacks.
6. **Database / migration impact:** None. No migrations, model/schema changes, dependencies, API routes or working records changed.
7. **Tests performed:** Existing `seller_home_entry_test.dart`, `dashboard_search_appbar_test.dart` and `dashboard_center_add_button_test.dart`: **29 tests passed in 25 seconds**, with real seller captures enabled. Final `flutter analyze --no-pub`: **No issues found**, 15.9 seconds. Formatting and scoped whitespace checks passed. Inspected `scratch/seller-blue-gold-center-20261106/seller-header-390-1.0.png`: continuous blue/gold blend through the central card gap, white cards and lower content, original Sales Overview geometry/actions retained. Source inspection confirms all new gold gradient stops use FCB315.
8. **Remaining limitations / safe practice:** No physical-phone install or performance benchmark. This is a viewport-based ambient glow, not a measured anchor to the grid; its relationship to the cards changes with large text, viewport size and scrolling. To practice safely, run the existing fixture/capture suites, inspect the 390px central gap, scroll Home and switch tabs, then confirm no tap behavior or card spacing changed. Tune radial alpha only if needed; keep actual card data and services untouched.

## Reduced soft-blue and gold header; white Sales Overview - November 6, 2026

1. **Cause / reason:** The latest instruction replaces the lavender page-wide accent with official soft/ice blue, restrained navy/gold glows and a shorter fade ending before the Sales Overview cards. This supersedes the previous request to extend color behind those cards. Existing uncommitted changes were inspected and preserved.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:313` (`header` background wiring), `:419` (original body Column restored) and `:523` (`_SellerHeaderBackdrop`); this guide. No test source, card layout or backend file changed in this follow-up.
3. **Changes made:** Remove the page-wide lavender base/central accent. Paint only the Seller Home header with `#DDE8FF` -> `#EFF5FF` -> the actual white page background; use stops `[0, .48, .9, 1]`, leaving the final 10% white. Add feathered upper-left official-navy and upper-right official-gold radial glows at approximately 4% and 8% starting opacity. Fade these to white too. No blur filter, dependency, shadow, whole-header border or rounded panel is added. Keep the search surface/border white, preserve its layout and leave Sales Overview/cards on white.
4. **How it works / data flow:** Existing `isSellerHome` decides whether the header mounts the private `_SellerHeaderBackdrop`. The helper returns paint layers only: blue base -> navy radial -> gold radial -> transparent-to-page-white fade. A Positioned.fill/IgnorePointer places those layers behind the unchanged SafeArea/profile/actions/search content. The original body Column owns header and PageView layout, so no card spacing or business processing changes. Example: below 90% of the header's height, the final decoration is opaque `HomeAppColors.appBackground`; any remaining glow is covered before the header meets the white body. Other tabs retain their existing white header/default presentation.
5. **Backend / API behavior:** None changed. Profile/sidebar, notifications, cart, SearchPage/catalog, seller eligibility, refresh and Sales Overview metrics retain their existing callbacks/services and actual records.
6. **Database / migration impact:** None. No models, migrations, dependencies, API routes or working records changed.
7. **Tests performed:** `flutter analyze --no-pub`: **No issues found**, 7.8 seconds. Existing `seller_home_entry_test.dart`, `dashboard_search_appbar_test.dart` and `dashboard_center_add_button_test.dart`: **29 tests passed in 12 seconds**, with actual seller captures enabled. These check responsive header/action behavior, Sales Overview spacing, search/cart routes, seller state, drawer, refresh and navigation. Inspected 390px and 320px/200% captures in `scratch/header-blue-gold-fade-20261106/`: restrained blue at the top, no lavender/pink, white cards/surrounding area and no horizontal header boundary. At 2x resolution, rows 302-305 across the entire 390px capture contained zero non-white pixels at the header/body transition. Formatting and scoped whitespace checks passed; a source search confirmed the previous lavender gradient codes were removed from this screen.
8. **Remaining limitations / safe practice:** No physical-device install or performance benchmark. Gold is deliberately faint. To verify safely, run the existing fixture suites with `SELLER_HEADER_REVIEW_DIR` pointing to an ignored scratch folder, inspect normal and enlarged-text captures, and compare the header's lower edge with the white card area. Tune only the radial alpha values if needed; preserve the final white fade and never edit real dashboard records to test colors.

## More visible central color behind Seller Home cards - November 6, 2026

1. **Cause / reason:** The user's latest screenshot/request asks for more visible color extending down the center behind the cards. The previous treatment deliberately faded to white before the header ended, so it could not color the Sales Overview background. This update supersedes that header-only fade while preserving a continuous surface without a horizontal boundary.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:315` (transparent Seller Home header) and `:410` (body Stack, background gradient at 417 and central radial accent at 431); this guide. Existing unrelated working-tree edits were preserved. No card component or test source changed in this follow-up.
3. **Changes made:** Move the decorative background behind the complete Seller Home body, including its original header/content Column. Add a restrained lavender-to-white base and a stronger, soft central radial accent visible around and between the white cards. Use the radial gradient's natural feathering instead of an independently clipped blur; remove the former header-only blur/fade and its now-unused ImageFilter import. The header is transparent only on Seller Home. Search, cards and bottom navigation retain their existing surfaces, dimensions, padding and actions; other tabs retain their original background.
4. **How it works / data flow:** Dashboard `build` still derives `isSellerHome` from existing approval and tab state. Its body Stack paints the input-transparent background first, then the unchanged header/PageView Column. `RadialGradient(center: Alignment(0, -.1), radius: .85)` positions the accent around the center of the visible page; alpha decreases from `0x33` through `0x14` to zero, creating a soft edge without a rectangular cutoff. Existing Home and embedded seller content expose this background through their transparent gaps while the original opaque white card Materials remain white. Example: scrolling changes visible content as before; the backdrop remains stationary behind the viewport and cannot intercept taps.
5. **Backend / API behavior:** None changed. Real profile/cart/catalog data, notifications, search navigation, seller permissions, orders, metrics and refresh processing remain unchanged.
6. **Database / migration impact:** None. No dependencies, models, migrations, API routes or working records changed.
7. **Tests performed:** Existing `seller_home_entry_test.dart`, `dashboard_search_appbar_test.dart` and `dashboard_center_add_button_test.dart`: **29 tests passed in 19 seconds**, with seller header captures enabled. Confirmed Sales Overview gap, responsive headers, retained seller state, navigation, drawer, Search/Cart routes, refresh and center action behavior. `flutter analyze --no-pub`: **No issues found**, 13.1 seconds. Formatting and scoped whitespace checks passed. Inspected real Flutter captures at 390px and 320px/200% in `scratch/seller-center-accent-20261106/`: visible lavender behind the cards, continuous header/body color, white cards/search and retained spacing.
8. **Remaining limitations / safe practice:** No physical-device install or performance benchmark. The accent is viewport-based, so its position does not follow individual cards while scrolling. Safely use the existing fixture suites/capture harness to compare normal and enlarged text, scroll Home, switch tabs and return; confirm all actions remain reachable and no header boundary appears. To tune visibility later, adjust only the radial colors' alpha and inspect another real capture; do not tint the white cards or modify actual dashboard records.

## Seller header fades seamlessly into Sales Overview - November 6, 2026

1. **Cause / reason:** The previous diagonal gradient left lavender along the lower-left header edge; the independently blurred accent could also contribute color at the clipped lower edge. The actual page behind Sales Overview uses `HomeAppColors.appBackground`, currently opaque white. This combination produced the visible horizontal boundary reported by the user.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:323` (`seller-header-gradient` in Dashboard `build`) and `:365` (`seller-header-bottom-fade`); this guide. No test source or dashboard content was edited in this follow-up; existing pending changes were preserved.
3. **Changes made:** Use a top-to-bottom lavender/near-white/page-white gradient with stops `[0, .38, .85, 1]`. Add an input-transparent background fade above the decorative accent and below SafeArea/controls, becoming fully page-white at 85% of header height. Keep the final 15% white so neither blur nor clipping can leave a colored bottom edge. No card, divider, shadow, border or rounded wrapper was added around the header. The search bar retains its own white rounded surface/border.
4. **How it works / data flow:** Dashboard `build` still selects this decoration only through the existing `isSellerHome` condition. Background gradient -> decorative blur -> transparent-to-page-white fade -> original header controls. Both fade endpoints read the same `HomeAppColors.appBackground` constant as the Scaffold. Example: at `y / headerHeight >= .85`, the foreground decoration is opaque page-white and covers any remaining accent color. Positioned paint layers add no layout height; the original SafeArea, padding, search dimensions, profile/notification/cart callbacks and Sales Overview gap remain unchanged.
5. **Backend / API behavior:** None changed. No notification, cart, profile, search, seller access or other business processing changes.
6. **Database / migration impact:** None. No dependencies, models, migrations or working records changed.
7. **Tests performed:** `flutter analyze --no-pub`: **No issues found**, 20.8 seconds. Existing `seller_home_entry_test.dart` and `dashboard_search_appbar_test.dart`: **27 tests passed in 30 seconds**, with the existing seller capture harness enabled. These retain the Sales Overview spacing, responsive header, drawer, search/cart navigation, seller-state and refresh checks. Inspected actual 390px and 320px/200% seller renders in `scratch/header-seamless-fade-20261106/`. At the 390px capture's 2x resolution, rows 280, 302, 303, 304, 305 and 316 contained zero non-white pixels across the image width; the prior left-edge pixel at row 302 was `#F2F0FB`, now `#FFFFFF`. This verifies white before, at and after the old boundary. Formatting and scoped whitespace checks passed.
8. **Remaining limitations / safe practice:** No physical-device install or performance benchmark. Safely rerun the two fixture suites with `SELLER_HEADER_REVIEW_DIR` pointing to an ignored scratch folder, inspect the lower search-bar/header area at regular and 200% text, and confirm Sales Overview still starts at its original gap. If a future theme changes the actual page background, keep both background fade endpoints and the page surface aligned; do not compensate by adding a divider or changing real dashboard records.

## Home profile outline, replacement Cart glyph and soft Seller header - November 6, 2026

1. **Cause / reason:** The latest user request asks for a combined navy and `#FCB315` profile outline and a different Cart icon. The accompanying pasted brief requests a restrained lavender/navy gradient and blurred background accent on Seller Home, Montserrat and the existing search bar below the identity row. The latest explicit gold value takes precedence over the brief's `#FCB316`. Inspected the current source and pending changes first; earlier Facility Details/search/cart work and the unrelated deleted test remain intact.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:314` (`header`), `:385` (`outlinedAvatar`), `:409` (`LucideIcons.shoppingCart`) and `:421` (Home search hint/font); `campushub/lib/module_app/widgets/navigation/header_profile_button.dart:9` (`HeaderProfileButton`) and `:120` (`_ProfileAvatarOutline`); `campushub/lib/module_app/widgets/navigation/header_search_button.dart:9` (`HeaderSearchButton`, hint/font inputs, text style near 59); `campushub/test/dashboard_header_test.dart:141` (Home outline, cart glyph and regular white background assertions); `campushub/test/dashboard_search_appbar_test.dart:39` (Home prompt, later tab-scope assertions); `campushub/test/header_profile_button_test.dart:101` (optional ring and actual photo preservation); `campushub/test/seller_home_entry_test.dart:65` (capture fonts) and `:158` (Seller background/outline/font and sharp-text assertions); and this guide. No cart service or CartIconButton implementation was changed in this follow-up.
3. **Changes made:** On the shared Home header, surround the existing 36px avatar with a 2px navy/gold circular gradient and a 2px white gap, producing a 44px outlined avatar. Preserve the actual photo, initials and accessible action. The outline is opt-in and disabled on other tabs/dedicated app bars. Replace the root header's Cart glyph with the installed Lucide `shoppingCart` outline while keeping its existing badge/button/route. Seller Home alone receives a pale lavender-to-white background plus a clipped, low-opacity blurred accent behind the controls. Text and icons are outside the ImageFiltered subtree. Home search now says **Search CampusHub...** in Montserrat; other tabs keep their existing prompt/font. The search label has an explicit 400 variable-font weight to avoid the thin default axis observed during rendering. Existing Sales Overview remains directly below the header.
4. **How it works / functions and data flow:** Dashboard `build` uses the existing seller approval and selected-tab state to choose the Seller background; `_currentIndex == 0` opts into the avatar outline and Home search presentation. `HeaderProfileButton(user, onPressed, outlinedAvatar)` continues reading `AuthUser`'s real name/photo and invoking the supplied callback. `_ProfileAvatarOutline(enabled, child)` decorates that same CircleAvatar without loading or replacing its image. `HeaderSearchButton(onPressed, asSearchBar, hint, fontFamily)` changes presentation only; taps still call `_openSearch()` and reuse the existing SearchPage/catalog futures. Cart still uses CartIconButton -> existing CartService count -> CartScreen. No extra search, drawer, notification or cart controller was introduced.
5. **Backend / API behavior:** None changed. Seller Home profile taps still open the existing drawer; regular Home profile taps still select Profile. Notification permission-sheet behavior, Cart navigation, real account identity, catalog loading, seller access and bottom navigation remain unchanged. Existing dependencies supply the icons and Flutter supplies the gradient/blur.
6. **Database / migration impact:** None. No database/model/migration, image storage, API route, permission or working-record changes.
7. **Tests performed:** Final **67 widget tests passed in 29 seconds** across `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart`, `header_profile_button_test.dart`, `seller_workspace_test.dart`, `dashboard_center_add_button_test.dart`, `search_page_test.dart` and `system_navigation_surface_test.dart`. Final `flutter analyze --no-pub`: **No issues found**, 14.6 seconds. Formatting and scoped whitespace checks passed. Existing capture harnesses produced actual bundled-font renders in `scratch/home-gradient-profile-20261106/`; inspected regular Home at 390px, Seller Home at 390px and Seller Home at 320px/200% text. Confirmed the replacement cart glyph is visible, avatar ring surrounds the original avatar, search text remains readable, controls do not overlap and the Seller accent does not filter text. Updated the seller capture font list to include the existing Lucide font after its initial render showed a missing-glyph box; no runtime icon workaround was needed.
8. **Remaining limitations / troubleshooting / safe practice:** No APK installation, physical Android device, live Cart submission or performance benchmark was run. Long actual usernames retain the existing ellipsis; enlarged search text wraps inside the existing growing surface. For a safe exercise, use the profile test's fixture image/name and compare `outlinedAvatar: false` and `true`; verify the foreground image URL is identical and only the circular decoration changes. Run the suites below, open the captured 320px/200% header, then tap the profile, Search, Notifications and Cart in fixtures to verify the existing destinations. A missing icon only in a screenshot harness requires loading that package's bundled font, not changing live cart data. Do not modify real accounts, approvals or cart items to test this styling.

Reproduce verification from `campushub/`:

```powershell
flutter analyze --no-pub
flutter test test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/seller_home_entry_test.dart test/header_profile_button_test.dart test/seller_workspace_test.dart test/dashboard_center_add_button_test.dart test/search_page_test.dart test/system_navigation_surface_test.dart --reporter expanded
```

## Dashboard search bar below the header and Cart after Notifications - November 5, 2026

1. **Cause / reason:** The user requested moving the existing header search icon down into a rounded search bar, using their supplied photo as a shape/placement reference, and placing Cart after Notifications. Inspected the local Git state and existing Dashboard, search, CartIconButton and CartService implementations first; the preceding Facility Details edits and unrelated test deletion were preserved.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:74` (`_headerCartKey`), `:309` (`build` header), `:354` (`CartIconButton`) and `:366` (`dashboard-search-bar`); `campushub/lib/module_app/widgets/navigation/header_search_button.dart:9` (`HeaderSearchButton`); `campushub/lib/module_app/widgets/cart_icon_button.dart:7` (`CartIconButton`); `campushub/test/dashboard_header_test.dart:134` (search below header and Cart ordering); `campushub/test/dashboard_search_appbar_test.dart:39` (existing Cart route); `campushub/test/seller_home_entry_test.dart:160` (seller header geometry, with scroll-state assertion near 425); and this guide.
3. **Changes made:** Replace the main Dashboard's inline search icon with a full-width white pill beneath the identity/action row, using the existing navy icon, neutral border, 20px side insets, 48px minimum height and **Search anything** prompt. Text grows/wraps for accessibility. Keep the existing profile/menu and notification actions; Cart is immediately to the notification bell's right. Reuse CartIconButton with an optional Iconsax cart glyph and accessible Cart tooltip. Its default bag glyph and callers remain supported. Search controls on separate Messages/seller workspaces retain their compact default presentation.
4. **How it works / functions and data flow:** `HeaderSearchButton(onPressed, asSearchBar)` returns either its original compact icon or the rounded tappable bar; both call the same callback. The Dashboard bar calls `_openSearch()` at line 169 -> `HomePageState.openSearch()` -> existing SearchPage with Home's loaded catalog futures; a direct launch into another tab retains the existing fallback SearchPage route and loaders. CartIconButton continues listening to `CartService.instance.itemCount` and opening `CartScreen`; persisted cart loading remains in `main.dart` and CartScreen. The header has its own stable `_headerCartKey`, avoiding reuse of the Products screen's global cart animation key when retained pages coexist. No search/category/cart business data is manufactured by the new presentation.
5. **Backend / API behavior:** No changes. Existing catalog search, cart ownership/checkout validation, notifications, authentication, seller access and messaging remain authoritative in their existing services. The photo's extra right-hand symbol is not added as a nonfunctional filter/scanner action.
6. **Database / migration impact:** None. No model, migration, API route or working record changed.
7. **Tests performed:** Final **58 Flutter tests passed in 27 seconds** across `dashboard_header_test.dart`, `dashboard_search_appbar_test.dart`, `seller_home_entry_test.dart`, `dashboard_center_add_button_test.dart`, `search_page_test.dart` and `seller_workspace_test.dart`, with existing real-font header capture harnesses enabled. Confirmed search entry/filtering/back navigation, entry before Home has loaded, CartScreen navigation/back, Notifications, profile/menu, seller access, retained navigation and responsive header ordering. Final `flutter analyze --no-pub`: **No issues found**, 14.0 seconds. Formatting and scoped whitespace checks passed. Inspected actual 390px regular and 320px/200% seller renders in `scratch/dashboard-search-cart-20261105/`. During review, gave the new prompt the explicit existing `AppTypography.family` to avoid a test-font fallback; updated old horizontal-search assertions and replaced a fixed gesture-slop expectation with bounded scroll movement while retaining state/refresh checks.
8. **Remaining limitations / debugging / safe practice:** No APK build/install or physical-device verification. The rounded bar opens the existing focused SearchPage; typing still happens there. The existing notification permission sheet remains the notification destination. A zero-item cart correctly has no count badge. Safe exercise: run the search/header suites using their isolated fixtures, tap Search anything, type Chocolate, return, open Cart and return again; verify the selected tab and header remain. At 320px/200% text, confirm the prompt wraps inside the pill without clipping and both top-right actions remain reachable. Do not add real cart items or edit working catalog records for a layout test.

Reproduce checks from `campushub/`:

```powershell
flutter analyze --no-pub
flutter test test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/seller_home_entry_test.dart test/dashboard_center_add_button_test.dart test/search_page_test.dart test/seller_workspace_test.dart --reporter expanded
```

## Iconsax Add Product navigation icon - November 5, 2026

1. **Cause / reason:** The user rejected the raster icon's appearance and requested Iconsax.
2. **Exact files changed:** `campushub/lib/module_app/widgets/navigation/add_product_navigation_icon.dart:5` (`AddProductNavigationIcon`), `campushub/test/test_add_icon_test.dart:7` (Iconsax assertion) and this guide. Other unpushed navigation changes were preserved.
3. **Changes made:** Replace the embedded PNG, base64 decoding and image fallback with the installed `Iconsax.box_add_copy` outline glyph. Keep the current size, navy foreground, gold button, position, labels and action.
4. **How it works / inputs and outputs:** The widget still accepts optional `size` and reads `IconTheme`. `build` returns a sized Flutter `Icon` using the existing Iconsax font. The navbar retains ownership of its tap callback, tooltip and semantics. No image bytes or network request are needed. Example: the existing 26px IconTheme produces a 26px product box with a small add symbol.
5. **Backend / API behavior:** None changed; product forms, submission and permissions remain in their existing flow.
6. **Database / migration impact:** None. No package installation, model or record changes.
7. **Tests performed:** **15 Flutter tests passed in 4 seconds** across `test_add_icon_test.dart`, `floating_bottom_navbar_test.dart` and `dashboard_center_add_button_test.dart`, with `CAPTURE_FLOATING_NAV=true`. Targeted Dart analysis: **No issues found**. Inspected the regenerated seller navigation render: crisp outline product-add icon, retained gold circle and label. Whitespace checks passed.
8. **Remaining limitations / safe practice:** No phone build/install performed. The PNG implementation below is historical and superseded. Run the three existing fixture suites and inspect `scratch/floating-navbar-no-selection-20261030/nav-390.0-1.0-true-rest.png`; tap Add Product in a fixture and verify its callback fires without selecting a navigation tab. Do not submit a working product just to verify the icon.

## Supplied PNG for the Add Product navigation icon - November 5, 2026

1. **Cause / reason:** The user supplied a new PNG data URL for Add Product. The current unpushed navigation widget already used an embedded PNG, so only that image and its rendering color needed replacement.
2. **Exact files changed:** `campushub/lib/module_app/widgets/navigation/add_product_navigation_icon.dart:7` (`_kProductBoxIconBase64`, image tint at 31) and this guide. Existing navigation, dashboard, upload-form icon, asset files and `pubspec.yaml` were not edited in this task.
3. **Changes made:** Use the exact supplied 24x24 PNG bytes. Its original white silhouette is tinted using the current navigation icon color, keeping it visible on the light/gold action surface. Existing sizing, action placement, tooltip, semantics and tap callbacks remain.
4. **How it works / inputs, outputs and data flow:** The embedded base64 constant decodes once into the existing exported `kProductBoxIconBytes` (`Uint8List`). `AddProductNavigationIcon.build` accepts its optional size and inherited `IconTheme`, then returns the existing sized `Image.memory`. `BlendMode.srcIn` applies the inherited foreground color through the PNG's alpha mask; missing theme color retains the existing navy fallback. The navbar continues owning the Add Product callback. No image generation, network image request or package is involved.
5. **Backend / API behavior:** None changed. Rendering or tapping the icon does not change product submission, permissions or API payloads.
6. **Database / migration impact:** None. No working accounts, products, prices or PostgreSQL records were changed.
7. **Tests performed:** **15 Flutter tests passed in 5 seconds** with `flutter test --no-pub --dart-define=CAPTURE_FLOATING_NAV=true test/test_add_icon_test.dart test/floating_bottom_navbar_test.dart test/dashboard_center_add_button_test.dart --reporter expanded`. Targeted Dart analysis reported **No issues found**. Decoded the supplied PNG successfully (788 bytes), inspected it and the regenerated seller navbar render, and checked whitespace. Existing tests cover Add Product action behavior and narrow/landscape/large-text navigation. Review output: `scratch/floating-navbar-no-selection-20261030/nav-390.0-1.0-true-rest.png`.
8. **Remaining limitations and safe practice:** The source is a 24px raster image, so enlarged sizes can appear softer than vector icons. No phone build/install or deployment verification was performed. To practice safely, rerun the existing icon/navbar fixtures and inspect the seller action; verify its Add Product tap callback fires without changing the selected tab. If the icon is invisible, inspect `IconTheme.color` and the image alpha/tint before modifying navigation or submitting a working product.

## Current Facility Details: pure white, gray controls and labeled Chat - October 29, 2026

This is the current direction. Older blur and frosted-control reports below are historical.

### 1. Cause / reason

Confirmed in the screen: _FacilityInformationBackdrop painted blurred gold/navy circles behind the information, and _FrostedPhotoSurface added blur and a gold border to photo controls. The user requested pure white, gray or transparent arrow/heart containers, and Chat text to the right of its icon. Solid light gray keeps controls readable over uploaded photos.

### 2. Exact files changed

| File | Current line / code anchor | Change |
|---|---|---|
| campushub/lib/module_app/screens/facility_details_screen.dart | 424 `final chat`; 523 `_FacilityInformationSurface`; 694 `_PhotoControlSurface`; 715 `_GalleryButton` | Labeled Chat, opaque white information, neutral gray photo controls; removed blur implementations and unused ImageFilter import |
| campushub/test/facility_details_test.dart | 168 continuous-page test; 1018 white/gray test; 1179 capture folder | Updated existing expectations for Chat placement, no filters, white surface and gray controls; new capture folder |
| docs/mobile-services-navigation.md | 3 current report | Explanation, verification, troubleshooting and exercise |
| CAMPUSHUB_CONTEXT.md | 3 latest record | Current steering supersedes blur guidance |
| campushub/DESIGN.md | Facility Details current direction | Current surface/control/action specification |
| campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md | Scope and mode | Updated direction |
| .impeccable/review/facility-details/surface-brief-body.md | Scope and mode | Matching direction |

### 3. Changes made

Replaced the decorative background stack with a white ColoredBox. Removed the frosted-control filter and gold edge. Back, Favorite, photo arrows and counter share opaque #F5F6FA backing. Chat uses TextButton.icon: chat icon followed by Chat text, keeping the tooltip, minimum48dp target and native feedback. Existing large-text layout puts Chat on its own row. Original saved-photo carousel, sections, pale cards, navy text and gold booking action remain.

### 4. How it works

Data flow: Django catalog -> FacilityItem -> FacilityDetailInformation -> existing saved image/rate/text widgets. No additional data is fetched for styling.

_FacilityInformationSurface accepts a child widget and returns an opaque white surface behind it. _PhotoControlSurface accepts child and optional corner radius (default24dp) and returns a clipped gray backing. _GalleryButton passes existing icon/selected state/callback into that surface. Favorites still use _toggleFavorite and the original facility-specific SharedPreferences key.

_overview passes the same callback to TextButton.icon: messageFacilitiesAdmin(context, facility.id). Example: tapping Chat passes the currently displayed facility's ID to the existing contact helper. Displaying the label sends no message. This button keeps icon and label together with normal button semantics and feedback.

### 5. Backend / API behavior

No edits. Existing contact helper, status guard, slot/non-slot route, quotes, conflicts, authentication and permissions remain intact.

### 6. Database / migration impact

None. No models, records, packages or image assets changed. Favorite remains a local preference keyed by facility ID.

### 7. Tests performed

Final focused Facility Details + booking suite: 32/32 tests passed (14 seconds), including 20 actual widget captures. Two-file Flutter analysis: No issues found (5.2 seconds). Formatting and scoped whitespace checks passed. Inspected top-390.0-1.0.png and top-320.0-2.0.png in scratch/facility-details-plain-white-20261029: white background, neutral controls, visible Chat on the right of its icon, and large-text fallback. Initial sandboxed runners stalled without output and were interrupted; the completed run outside the sandbox passed. No failed/stalled run is counted as a pass.

Commands from campushub:

    flutter test --no-pub --reporter expanded test/facility_details_test.dart test/facility_booking_flow_test.dart --dart-define=CAPTURE_FACILITY_DETAILS=true
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

### 8. Remaining limitations / troubleshooting / safe exercise

No app build, install, launch or restart; user retains Ctrl+F5. No physical-device or TalkBack verification is claimed. Actual uploaded photos retain their original colors; the removed color was decorative background.

If an old blur remains visible, use the existing development refresh workflow and confirm this screen is the opened route. Search the screen for ImageFiltered/BackdropFilter: neither should remain. Chat below the name at large text size is the intentional accessibility layout.

Safe exercise: inspect _PhotoControlSurface's default radius and the counter's radius:8 override. Switch highContrast in the isolated white/gray test and run that named test. Both settings should show white information, gray controls and no filters. Restore the fixture; no live records or bookings are needed.

## Current Facility Details: white with navy/gold blur behind the carousel — October 29, 2026

Latest request: change to white, with the blurred navy/gold overlay behind the photo while keeping the carousel visible. This supersedes the intermediate navy page and the prior edge-to-edge gallery. It keeps the original facility photos sharp and the selected content/booking hierarchy.

Plan, reviewed against the request: white #FFFFFF page/footer, navy #1A1851 text, pale #F5F6FA cards, muted #667085 secondary text, #E3E5ED borders and mobile gold #FCB315. Retain Montserrat, 620 dp content measure, 20 dp gutters, rate accordion, circular amenities and gold booking action. Confine decorative blur to the background behind a large rounded gallery; a white wash softens the color. The photo itself never receives that blur or overlay.

    navy/gold background blur -> white wash -> sharp rounded photo carousel
    white information -> pale saved-rate accordion -> circular saved amenities
    About -> operating schedule -> guidelines -> terms -> reviews
    white safe footer: [local bookmark] [gold Request Booking]

### 1. Cause / reason

Confirmed: the intermediate navy design put blurred accents behind the information. The latest request asks for white again and places the colored effect behind the photo. Moving the effect into its own gallery frame makes it visible around the photo without hiding the actual image or putting a navy tint over it.

### 2. Exact files changed

All paths are repository-relative. Lines are current; anchors identify the component if future edits move them.

| File | Current line / nearby anchor | Change |
|---|---|---|
| campushub/lib/module_app/screens/facility_details_screen.dart | 17 local tokens; 87 build; 281 _rentalRates; 375 _overview | White theme, navy copy, pale surfaces, #FCB315 action/selection; original data/handlers |
| same screen | 506 _FacilityGalleryBackdrop; 582 _FacilityHeroGallery | Blurred navy/gold shapes and white wash behind a sharp framed PageView |
| same screen | 741 _FrostedPhotoSurface; 770 _GalleryButton; 1226 _FacilityBookingBar | Clipped white blur controls/gold edge, same native actions, white safe footer |
| campushub/test/facility_details_test.dart | 505 responsive loop; 777 actual images; 956 rate/bookmark; 1007 frosted controls; 1126 captures | Frame geometry, clear image/swipe/count, current colors, high-contrast fallback and captures |
| docs/mobile-services-navigation.md | 3 current report | Eight-part guide, data flow, checks, troubleshooting and exercise |
| CAMPUSHUB_CONTEXT.md | 3 latest carousel-background record | Current request replaces earlier white/navy records |
| campushub/DESIGN.md | Colors / Layout / Facility Details component | Current white layout and behind-photo material |
| campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md | 8 Scope and mode | Matching current surface brief |
| .impeccable/review/facility-details/surface-brief-body.md | 1 Scope and mode | Matching review brief |

No other runtime screen, shared navbar or notification-product test was modified. The existing booking-flow test is run without further edits.

### 3. Changes made

Restored white page/footer and navy text/icons with muted supporting copy and pale gray rates/amenities. Gold is now exactly #FCB315, as requested, including the booking button and active carousel pill. Original section order, disclosures, pricing and navigation remain.

The new gallery frame reserves the existing responsive overall height. Photos are inset 12 dp horizontally, begin 8 dp below the safe top inset and end 20 dp above the frame bottom, with 24 dp rounded corners. The colored background therefore shows around the frame. Native controls remain at least 48 dp, fully inside the photo and clear of safe insets. Centered BoxFit.cover preserves proportions; no stretching, replacement photography or thumbnail strip.

Behind the photo are two decorative 240 dp circles: navy at 42% alpha and #FCB315 at 45%, each blurred with sigma 40, then softened by a 55% white wash. They are clipped to the gallery region, excluded from semantics and cannot receive pointer events. PageView sits above this wash and is not inside either ImageFiltered layer.

Small photo-control/counter backgrounds retain their own clipped sigma-10 BackdropFilter and 82% white backing with a subtle gold edge. This intentionally blurs only their backing. High contrast removes both decorative background filters and the control filters, and uses solid white controls.

### 4. How it works: functions, inputs/outputs and data flow

    existing Django catalog -> FacilityItem -> FacilityDetailInformation
      -> saved images/rates/amenities/hours/text -> existing screen components
      -> original _requestAction -> existing booking form or category contact path

build creates the route-scoped light theme and places the gallery before the separate information column. It does not change any app-wide theme or navbar.

_FacilityHeroGallery takes real allImageUrls, PageController/current index, favorite state and original callbacks. It passes its clear PageView/controls to _FacilityGalleryBackdrop with a height based on viewport width and the current safe top inset. The frame reserves space before image loading finishes, so decoding does not move the content.

_FacilityGalleryBackdrop takes child, height and topInset. It paints the decorative background first, then the white wash, then the padded/rounded child. ImageFiltered applies only to the colored circles; ProductImage remains outside every image/backdrop filter. The visible original image is therefore sharp. _FrostedPhotoSurface remains a separate helper for the small controls only.

Annotated example: topInset=24 puts the photo at y=32. On a 390 dp viewport it is 366 dp wide, preserving the full-sized swipe target while exposing a 12 dp colored frame on each side. The source photo uses BoxFit.cover, so its ratio is preserved rather than stretched.

_rentalRates toggles only local _ratesExpanded and renders original FacilityDetailInformation fields. The heart/bookmark still share facility_favorite_ID in SharedPreferences. _requestAction retains its existing facility-status guard and original slot versus non-slot destination. No styling interaction submits or confirms a booking.

### 5. Backend / API behavior

Unchanged. No endpoints, serializers, authentication, RBAC, quote/conflict, approval, chat, form validation or request-submission edits. Only real saved information is displayed. No reviews, amenities, rates or location are fabricated. Unsupported Share is not added.

### 6. Database / migration impact

None. No models, schema, migrations, working records, packages or image assets changed. Tests use isolated fixtures/preferences. The only user-triggered favorite behavior remains the original local preference.

### 7. Tests performed

Final focused Facility Details + booking suite: **32/32 tests passed** in 26 seconds, including 20 actual widget captures. Two-file Flutter analysis: **No issues found**, 29.9 seconds. Final formatting: 2 files, 0 changes, 0.28 seconds. Scoped whitespace check passed.

Focused coverage includes 320/375/390 dp phones, 844 dp wide/landscape, 2x text, surrounding light/dark themes, reduced motion, high contrast, safe footer clearance, saved billing methods and original conflict/form/submission flows. Gallery checks verify actual image decoding, cover sizing, swipe/count/selection, no image tint/gradient/filter, frame bounds and information below the complete frame. Blur checks verify the nearest control clip is 48x48 dp, decorative filters never descend into the photo, and high contrast disables filtering.

Actual RepaintBoundary fixture captures are saved in ignored scratch/facility-details-white-blur-20261029. These are real widget renders with isolated content and an existing campus asset, not generated mockups or live facility records. The 390 dp and 320 dp 2x top captures were inspected: colored blur is behind the clear rounded photo, with white content below.

Commands from campushub:

    flutter test --no-pub test/facility_details_test.dart test/facility_booking_flow_test.dart --dart-define=CAPTURE_FACILITY_DETAILS=true
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

Confirmed test-only corrections: the action is an existing FilledButton, so its color check uses the shared ButtonStyleButton type. The rounded gallery adds a second clip ancestor; the blur test now checks the nearest 48x48 control clip rather than assuming only one clip exists. Neither correction changes app behavior.

Commands from campushub:

    flutter test --no-pub --reporter expanded test/facility_details_test.dart test/facility_booking_flow_test.dart --dart-define=CAPTURE_FACILITY_DETAILS=true
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

### 8. Remaining limitations / troubleshooting / safe exercise

No separate new reference image was visible; this follows the latest written direction without claiming exact pixel matching. No application build, install, launch, restart, physical performance measurement or TalkBack session was performed. User retains Ctrl+F5 control. Cover fitting can crop an image but does not distort it.

If the photo looks blurred, confirm that PageView/ProductImage is a sibling above the background shapes, never a child of ImageFiltered or BackdropFilter. If blur is absent, inspect highContrast: disabling it is intentional there. If a control seems opaque, high contrast uses solid white for readability. Keep background color alpha separate from the actual uploaded-image widget.

Safe exercise: change highContrast only in the isolated frosted-controls fixture and run that named test. Verify false retains the behind-photo color filters and true removes them; in both cases the clear carousel, count, favorite and booking button remain. Restore the fixture afterward. No live facility record or booking submission is needed.

## Dark navy Facility Details from the attached brief — October 29, 2026

Historical dark implementation: the current white/frosted report above supersedes its colors, image overlay, information placement and gold active-dot directions. Its saved-data, accordion and booking behavior remain relevant.

Reference limitation: the supplied attachment directory contains only Pasted text.txt, with the detailed dark-layout instructions. No separate dark reference image was available. Implemented its stated hierarchy/colors/components directly; exact image/pixel matching is unverified. No alternative design or generated image was created. The instruction not to rebuild the application was preserved.

Design plan: an Operate screen for campus users reading saved facility conditions and opening the existing request flow. Use Montserrat, navy #1A1851 page, lighter navy #24225F cards/controls, white #FFFFFF primary text, muted blue-gray #C6CADF, border #454574 and gold #FCB316. The requested navy photo gradient is functional text contrast and an image-to-page blend, rather than unrelated decoration. Keep one 620 dp reading measure and 20 dp gutters; large text wraps without clipping.

    actual photo + navy overlay/fade + saved-image PageView
    category pill -> white title + existing Chat -> location -> rating/capacity
    expandable saved rate card
    circular saved amenities -> About / Read More
    schedule/status -> booking rules -> terms -> reviews
    [saved bookmark]                     [Request Booking]

### 1. Cause / reason

Confirmed: the prior screen used a white panel, plain rates, a two-column amenity grid and footer price. The new brief explicitly requires an immersive dark layout, expandable rate card, circular amenities before About, and bookmark-plus-booking footer. These are UI changes; existing facility and booking data do not need an integration change.

### 2. Exact files changed

Repository-relative paths and current lines; anchors identify functions if lines move.

| Folder / file | Current line / anchor | Change |
|---|---|---|
| campushub/lib/module_app/screens/facility_details_screen.dart |15–18 local colors;85 build;278 _rentalRates;345 _rateDetails;372 _overview | Scoped dark theme, new order, rate accordion, saved summary hierarchy |
| same screen |502 _FacilityHeroGallery;920 _RentalPrice;1026 _ExpandableDetailText;1098 _Amenities;1157 _FacilityBookingBar | Blended real-photo hero, price/unit hierarchy, wrapping disclosure, horizontal circles, shared saved bookmark/footer |
| campushub/test/facility_details_test.dart |166 continuous order;497 responsive loop;686 pricing methods;889 bookmark/accordion;940 normal motion;966 amenities;988 captures | Adapt prior light-layout expectations; cover new interactions, data boundaries and motion modes |
| campushub/test/facility_booking_flow_test.dart |157 FacilityDetailsScreen renders image-first sections | Update capacity presentation assertion; keep original form/conflict/submission tests |
| docs/mobile-services-navigation.md |3 current dark report | Eight-part report, functions/inputs/outputs, debugging and exercise |
| CAMPUSHUB_CONTEXT.md |3 latest dark-layout record | New accepted scope and checks |
| campushub/DESIGN.md | Facility Details / Layout / Colors | Current dark route specification; other surfaces unchanged |
| campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md | Direction / hierarchy | Current route brief |
| .impeccable/review/facility-details/surface-brief-body.md | Scope and mode | Matching direction and verification limits |

### 3. Changes made

Removed the white photo-sheet edge and white page/footer surfaces. The actual image PageView now has a navy overlay fading into the page; category/name/location/review/capacity occupy its lower region. A minimum header measure plus a naturally growing column prevents long/scaled titles from colliding with following sections. Chat stays beside the normal title and moves below it at large text sizes so a word is not split unnecessarily.

Back, local Favorite, real counter and previous/next retain their existing actions. Multiple images use an elongated gold indicator and translucent inactive dots, bounded to five. No thumbnails or unsupported Share action. Missing photos retain the real fallback state.

The16 dp outlined lighter-navy rate card initially shows the actual amount and billing basis with a right chevron. Expanding reveals the same primary rate, configured extra-hour charge, actual alternatives/custom notes and existing pricing explanation. Normal expansion uses 200 ms ease-out size/chevron feedback; reduced motion updates the details directly. No quote calculation occurs here.

Saved amenities appear in 52 dp dark circles with white outline icons and labels. Up to four fit across at normal text size; more than four, or large text, scroll horizontally. No features are invented. About follows amenities, previews four lines and uses Read More with an arrow; original text expands/collapses. Terms retain their original wording and disclosure.

Schedule, status badge, booking requirements/restrictions, terms and honest reviews remain below on navy. No tabs, Details calendar, Check Availability, discount section or mandatory admin-message section. Existing Chat remains a compact supported action.

Footer now has a bookmark and a large gold Request Booking. The bookmark uses the exact same local favorite preference as the hero heart, including synchronized selection. The primary price is now in the rate card instead of duplicated in the footer, as required by the attached footer specification. Scaffold reserves footer height; SafeArea protects its controls.

### 4. How it works: functions, inputs/outputs and data flow

Unchanged backend/catalog flow:

    saved Django facility -> existing catalog service -> FacilityItem
      -> FacilityDetailInformation -> dark screen widgets
      -> original _requestAction -> existing booking form or category contact flow

- build takes the existing FacilityItem/service and creates a scoped dark Theme. It passes _overview into the gallery, then renders rates, amenities, About and the saved lower sections. The app-wide theme/navbar remain separate.
- _FacilityHeroGallery takes resolved actual URLs, page controller/index, favorite callbacks and a header widget. Its background PageView sits behind an IgnorePointer navy gradient. The growing content column places the saved summary over the lower image and continues into the same navy page.
- _overview takes FacilityDetailInformation and renders the existing category, name, location, valid reviewSummary or No reviews yet, and saved capacity. It does not invent a campus location or rating.
- _rentalRates takes the read-only information formatter and toggles local _ratesExpanded. _rateDetails returns only formatted saved primary/options/custom notes. _RentalPrice renders the amount and billing basis separately while preserving one full spoken price.
- _Amenities takes nonblank saved names; LayoutBuilder chooses fit-four widths or a horizontal scrolling width that grows with text scale.
- _ExpandableDetailText measures four lines with the actual TextScaler, then changes only local preview state. Flexible labels allow lengthy Read Full Terms to wrap at 2 x.
- _toggleFavorite writes the existing facility_favorite_ID SharedPreferences key. Both heart and footer bookmark call it; no new remote saved-facility API exists.
- _FacilityBookingBar takes favorite state/toggle and the original request handler. Unavailable facilities retain a null booking handler. Supported slot categories still open FacilityBookingScreen; non-slot categories retain the original contact path.

Annotated isolated example: price_type=base_hour, saved rate 3000, base_duration4 and additional_hour_rate500 produce the spoken summary ₱3,000 / first 4 hours. Expansion adds Additional hour:₱500 / hour; an alternative only appears if configured. These are test fixture inputs, not runtime constants. All other existing formatter methods remain supported without adding billing logic.

### 5. Backend / API behavior

No backend, endpoint, authentication, RBAC, quote, conflict, payment or approval changes. The original form still loads slots/retries failures, obtains server quotes, validates and submits the original request. Opening/toggling the card or bookmark never confirms a reservation or submits a booking. Current facility serialization does not supply review totals or individual feedback, so real records honestly show No reviews yet.

### 6. Database / migration impact

None. No models, schema, migrations, working records, dependencies or image assets changed. Only the original local favorite preference changes on an explicit favorite/bookmark tap.

### 7. Tests performed

Final focused suite: **31/31 tests passed** in 8 s. Analysis reported **No issues found** for 3 files in 2.3 s. Final formatting checked3 files with 0 changes in 0.10 s. The final render-only test passed in 9 s and refreshed 20 captures. Scoped whitespace verification also passed. Tests retain all earlier data/booking regressions and add collapsed/expanded prices,200 ms normal expansion, direct reduced-motion expansion, footer/heart preference synchronization and more-than-four amenities scrolling.

Responsive coverage includes320/375/390 dp phones,844 dp widths/landscape,2 x text, surrounding light/dark themes,48 dp+ photo actions,56 dp+ booking action and safe footer/body clearance. Actual RepaintBoundary captures are in ignored scratch/facility-details-dark-20261029, using clearly isolated fixtures and an existing campus asset to exercise image decoding. These are actual widget renders, not a mockup or evidence of live facility records.

Confirmed/fixed during checks: zero-duration AnimatedSize triggered a layout mutation assertion, so reduced motion now bypasses that layout animation. Enlarged disclosure labels required Flexible inside their action row. Tests now scroll back before inspecting the lazily disposed hero heart, and count only mounted review text after scrolling. These fixes did not alter booking rules.

The local skill's accordion search returned no match. A narrowed Flutter responsive-layout query returned applicable LayoutBuilder/Row/Column guidance; native Flutter animation/state primitives implement the accordion. No external UI package was added.

Commands from campushub:

    flutter test --no-pub test/facility_details_test.dart test/facility_booking_flow_test.dart
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart test/facility_booking_flow_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart test/facility_booking_flow_test.dart

Commands from campushub:

    flutter test --no-pub --reporter expanded test/facility_details_test.dart test/facility_booking_flow_test.dart --dart-define=CAPTURE_FACILITY_DETAILS=true
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

### 8. Remaining limitations / troubleshooting / safe exercise

No separate dark reference screenshot was supplied, so exact image alignment/pixel comparison is unverified. The previous light screenshot is not a dark-reference substitute. No application rebuild, install, launch, restart or native device commands were performed. OS bars, physical touch performance and TalkBack are not certified by widget tests.

If extra charges/options appear absent, expand the card first, then inspect saved pricing configuration. If a feature is missing, inspect the actual saved amenity list rather than adding example items. For an unavailable booking button, inspect the stored facility status and preserve _requestAction. The footer bookmark is a local favorite, not a newly created database record. Review feedback/monthly billing remain limited to existing backend support.

Safe exercise: in detailFixture only, remove pricing.hourly_rate and run the accordion test with its corresponding expected-option assertion updated. Verify the base summary/additional-hour rate remain while the alternative row disappears. Restore the fixture/assertion afterward. Never practice on live facility rates or submit a booking to verify this presentation change.

## Facility Details gray arrow and heart containers with review header — October 29, 2026

This refinement supersedes the earlier white photo buttons, stemmed Back arrow, labeled Chat, wrapped unlimited dots and horizontal-divider instructions below. Latest request: keep arrow controls gray, restore the gray Favorite container, and show the existing star/review summary above the facility name. This supersedes the transparent Favorite override; the star/review summary stays above the name. The no-tabs layout and original data/booking workflow remain current.

Design plan: campus facility guide, calm and minimal. Keep navy #1A1851, white #FFFFFF, gold #FCB316, supporting text #66687A and existing borders #E2E4EC; introduce one route-local control surface #EEF0F3. Retain bundled Montserrat and the existing type/spacing scale. Left-aligned facts and text follow the actual image; gray controls recede into the photo. No added entrances, gradients, shadows, assets or unrelated screens.

    photo: [<]                           [favorite]
           [previous]   swipe photo      [next]    (multiple photos only)
                                           count
                        at most five dots
    star + honest review summary
    name/category                        [chat icon]
    actual information and sections, separated by spacing
    configured price                     Request Booking

| Before | After | Why |
|---|---|---|
| Stemmed Back arrow / white circle | Simple chevron / soft gray circle | Match the requested shape and quieter surface |
| Transparent Favorite background | Same gray container as Back | Restore the requested heart container while retaining48dp target |
| No empty review row above name | Star + No reviews yet above name, or genuine supplied totals | Make review status visible without invented ratings |
| Chat icon above its label | One labeled-for-accessibility chat icon | Remove label/spacer height while preserving contact |
| One dot per photo, wrapping | Five-dot moving window, real count and previous/next | Keep large uploaded galleries compact |
| Rates/schedule rules and footer top line | Spacing, without divider widgets/footer line | Match the requested line-free treatment |

### 1. Cause / reason

Confirmed in source: Back used arrow_back_rounded, Chat was a Column with label/spacer, dots grew with image count, and explicit horizontal lines appeared in rates, schedule and footer. Back/Favorite already belonged to the scrolling gallery; that behavior is preserved and also applies to previous/next controls. Confirmed for the latest request: Favorite inherited the same gray background, and _overview omitted No reviews yet while placing valid ratings below the title. The subsequent transparent-heart revision added an explicit override. The current correction removes the override and now-unused optional surface parameter, restoring the shared gray surface; the existing review formatter still renders above the name.

### 2. Exact files changed

Repository-relative paths, current lines and stable anchors:

| Folder / file | Line / anchor | Change |
|---|---|---|
| campushub/lib/module_app/screens/facility_details_screen.dart | 16 _facilityControlSurface; 273 _rentalRates; 317 _overview | Matching pale gray arrow / Favorite containers; review row above name; existing icon-only Chat |
| same screen | 412 _FacilityHeroGallery; 600 _GalleryButton | Chevron Back, gray photo controls/counter, bounded dots, previous/next |
| same screen | 706 _OperatingScheduleCard; 1012 _FacilityBookingBar | Remove schedule divider/footer top rule; safe booking action retained |
| campushub/test/facility_details_test.dart | 94 iconButton; 149 continuous page; 225 supplied reviews; 782 large galleries; 869 optional captures | Correct native-control finder, assert icon/no dividers, 23-photo window/navigation/scroll-away coverage |
| docs/mobile-services-navigation.md | 3 current refinement | Eight-part report, functions/data flow, debugging and exercise |
| CAMPUSHUB_CONTEXT.md | 3 latest record | Current control decisions and measured checks |
| campushub/DESIGN.md | Facility Details / latest control refinement | Current gray/icon/carousel specification |
| campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md | Direction / latest refinement | Scoped current behavior |
| .impeccable/review/facility-details/surface-brief-body.md | Direction / latest refinement | Matching review direction |

### 3. Changes made

Back is a simple less-than-shaped Material chevron. Back, photo counter and carousel controls use the opaque pale gray token; Favorite now uses that same default gray surface; it stays readable over different photos without a blur/glass treatment. Every photo button retains a48dp minimum native target, tooltip and native press/focus feedback, including Favorite in both saved states. _overview now starts with facility-header-review: an outline star and FacilityDetailInformation.reviewSummary, with8dp below it before the name/Chat row. Invalid or absent rating/count displays No reviews yet; genuine valid totals display unchanged. The separate Reviews section stays intact.

Chat is one chat_outlined IconButton, with Chat with Facilities Admin as its accessible tooltip. It calls the exact original contact handler. The visible label, internal spacer, outline and taller layout were removed.

Two or more uploaded photos show previous/next controls; endpoints disable the unavailable direction. Swiping remains supported. At most five dots surround the current image, while the real counter communicates the full gallery size. Empty/single-photo fallbacks stay honest. All photo controls scroll out with the gallery; only the original booking bar stays fixed.

Removed Divider widgets from rates/hours and the footer's top border. Existing operating-card outline and section spacing remain. No photo thumbnails or tabs were added.

### 4. How it works

Data flow remains Django catalog -> FacilityItem.allImageUrls -> _FacilityHeroGallery. Its inputs are actual resolved URLs, currentIndex, PageController and original favorite/page-change callbacks. A swipe or controller.jumpToPage changes the existing index, which redraws count/dots; it never writes facility data.

dotCount=min(imageCount,5). firstDot clamps currentIndex-2 into0..imageCount-dotCount. Example:23 isolated fixture photos with currentIndex11 display12/23 and the five indicators with indices9..13. At the first/last page the window clamps to remain within actual URLs. Previous/next buttons call jumpToPage directly, with no keyboard-triggered animation or auto-rotation. Existing160ms ease-out dot feedback becomes zero under reduced motion.

_GalleryButton takes tooltip/icon/nullable onPressed/selected and applies the same shared gray background to Back and Favorite. After the override was removed, analysis confirmed the optional backgroundColor parameter had no callers; removed that now-unused parameter/field too. Only the surface changes; _toggleFavorite still reads/writes the existing local preference. A null callback exposes a disabled endpoint. _overview takes FacilityDetailInformation, reads its existing reviewSummary and renders that text plus a star above the same saved name/category/facts and48dp chat action. It moves the former valid-rating row rather than duplicating it below the name. Example: missing rating/count produces No reviews yet in the header and Reviews section; the isolated4.8/count12 fixture produces4.8 (12 reviews) in both. No runtime rating is hardcoded. _rentalRates and _OperatingScheduleCard still render the same formatter outputs; only separators changed. _FacilityBookingBar still takes the existing configured price and request handler, with Scaffold/SafeArea clearance.

### 5. Backend / API behavior

Unchanged. Saved images, prices, hours, status and restrictions still come from existing data. Contact, favorite, unavailable-state disabling, request navigation, quotes, conflicts and approval flow are preserved. No messages or bookings were submitted for this refinement.

### 6. Database / migration impact

None. No models, endpoints, migrations, records, dependencies or image assets changed. Favorite remains the existing local preference.

### 7. Tests performed

Final correction checks:28/28 tests passed9s; two-file analysis No issues found4.5s; formatting2files0changes. The initial correction passed28 tests; analysis then reported unused_element_parameter for backgroundColor, so the unused optional parameter/field was removed; the latest additions assert review text above the name for empty and valid supplied reviews, and the matching gray Favorite/arrow surfaces. Scoped git whitespace check passed. Initial new test assertions incorrectly cast a Tooltip to IconButton; the iconButton helper now finds the native control by its tooltip property. No production code was changed to accommodate that test error.

The preceding review-header revision rendered20 actual fixture captures to ignored scratch/facility-details-review-header-20261029. Prior render inspection:390dp normal and320dp2x header show transparent heart, gray chevron and star/review text above the name. The existing capture harness also rendered375dp/landscape and lower sections. The first position assertions measured the outer Padding bottom (which equals the next row top); corrected the tests to measure the review Text bottom, verifying the8dp gap. Production layout was unchanged for that test fix. The23-photo regression verifies five dots, actual count, moving window, previous/next, disabled endpoints, gray surfaces,48dp targets, scroll-away controls and retained visible booking action. Existing tests retain swipe/favorite/back behavior, saved data boundaries and original booking checks.

Commands from campushub:

    flutter test --no-pub test/facility_details_test.dart test/facility_booking_flow_test.dart
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

Latest gray-heart correction is a surface-only edit verified by the existing color assertion and facility regressions; no fresh emulator build/installation, native gestures or live-chat check was performed for this small change. The previous gray-control Android17 check is historical evidence only. No message or booking was submitted.

### 8. Remaining limitations / troubleshooting

This keeps the inherited white details surface in surrounding dark mode. Current API still lacks genuine review aggregates/feedback. No full TalkBack, performance or physical-device pass is claimed. Native large-gallery coverage requires a live facility with multiple saved photos; fixture tests cover that state without modifying records.

If arrows/dots are absent, inspect allImageUrls:zero/one photo intentionally has no carousel navigation. Gray previous/next endpoints are disabled at their bounds. If Chat has no label, that is intentional; its tooltip/semantics name remains. If a photo button appears fixed, verify it belongs to _FacilityHeroGallery rather than placing it in a Scaffold overlay. If the heart still looks transparent after a reload, check that its _GalleryButton call has no transparent backgroundColor override and uses the default gray surface. If No reviews yet is absent above the title, inspect _overview/facility-header-review and the current screen build rather than adding fabricated data.

Safe exercise: inspect detailFixture without changing live data. Run the continuous-page and supplied-review tests: the empty record must show No reviews yet above the name; the existing4.8/count12 fixture must show4.8 (12 reviews) there. Temporarily remove the supplied count from that isolated fixture and confirm the formatter safely falls back to No reviews yet, then restore it. Verify the arrow surface is #EEF0F3 and Favorite also resolves to #EEF0F3 with the existing gallery test.

## Continuous Facility Details without tabs — October 29, 2026

This is the current specification. It supersedes the tab, split Overview, above-name status, hidden photo counter, facts/rates cards and terms-chevron instructions in historical records below.

Design plan: an Operate surface for campus users reading a venue and requesting it. Calm, compact and photo-led, with one left-aligned column and a persistent booking action. Palette: navy #1A1851, brief-specific gold #FCB316, white #FFFFFF, secondary #66687A, border #E2E4EC and fallback #F8FAFC. Keep bundled Montserrat, 23sp venue title, 16sp headings, 14sp body and 24dp section rhythm. The reading column and footer use the existing 620dp measure; enlarged text wraps and the footer stacks. Gallery dots retain reduced-motion support.

    uploaded photos + counter/dots
    name/category + existing Chat
    location/capacity + genuine rating, if supplied
    rates -> about -> features -> schedule + status
    booking guidelines -> terms -> reviews
    [configured price] [Request Booking]  (safe fixed footer)

Brief review: flatten the facts/rates instead of making every section a card. Retain the saved-hours card and rounded gallery edge from the incumbent design. No decorative entrances, generated assets or unrelated changes. UI/UX Pro Max's local Flutter search returned relevant LayoutBuilder, Row/Column and SizedBox guidance. Impeccable's source detector returned no findings, but cannot verify native layout. The generic HTML accuracy kit is absent; no HTML-gate or accessibility certification is claimed.

### 1. Cause / reason

Confirmed: TabController and conditional content prevented reading all details in one scroll. Wide Overview also reordered About/Terms before Rates. The new attached brief explicitly requires no tabs and one consistent section order.

Confirmed in render review: the shared amenity matcher searches for "air", so "Chairs" showed an air-conditioning icon. This screen checks chairs first, retaining the shared matcher for other features.

### 2. Exact files changed

Paths are relative to the repository root; anchors remain useful as lines move.

| Folder / file | Current line and anchor | Change |
|---|---|---|
| campushub/lib/module_app/screens/facility_details_screen.dart | 15 _facilityDetailGold; 28 state; 81 build; 272 _rentalRates; 316 _overview | Continuous sections, plain facts/rates, scoped gold; remove tab and inline slot-preview state |
| same screen | 424 _FacilityHeroGallery; 602 _DetailSection; 897 _ExpandableDetailText; 951 _Amenities; 983 _FacilityBookingBar | Counter/dots, status badge, named disclosures, chair icon and safe footer |
| campushub/test/facility_details_test.dart | 145 continuous page; 441 responsive cases; 512 disclosures; 557 deferred slots; 629 billing methods | Section order/data, footer clearance, loading/retry, rate units and captures |
| campushub/test/facility_booking_flow_test.dart | 156 FacilityDetailsScreen renders image-first sections | Continuous-scroll expectations and original request navigation |
| docs/mobile-services-navigation.md | 3 Continuous Facility Details without tabs | Current eight-part report and learning guide |
| CAMPUSHUB_CONTEXT.md | 3 latest record | Current decision and checks |
| campushub/DESIGN.md | Facility Details / Layout / Elevation / Shapes | Replace superseded specifications |
| campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md | Confirmed hierarchy / Direction | Current surface specification |
| .impeccable/review/facility-details/surface-brief-body.md | Scope and mode | Matching review direction and limits |

### 3. Changes made

Removed TabBar, TabController, selected-tab state and the wide Overview split. Applicable saved sections now coexist in the requested order. Blank description/features/terms are omitted. Missing operating hours remain explicitly unconfigured.

Restored a counter only for supplied photo URLs, including a single image. Kept PageView, navy/gray animated dots, loading/error fallback, Back and local Favorite; dots wrap for long image lists. No thumbnails or generated images.

Status appears once as a neutral badge beside Operating Schedule, wrapping when needed. Saved seven-day hours and weekend restrictions remain. Name/category, location, capacity and a genuine supplied rating appear directly on white. Reviews shows No reviews yet or valid supplied totals, without sample feedback.

Four-line descriptions/terms expand with Read More / Read Less or Read Full Terms. Original wording stays unchanged. Booking Guidelines contains only saved requirements and existing formatted mode/restrictions/minimum duration/advance-payment/client-eligibility rows. Check-in/out and operating hours remain in Schedule. Removed the inline today-slot preview/prefetch; date and slot selection belong to Request Booking.

### 4. How it works

    Django Facility -> serialize_facility -> existing catalog service
      -> FacilityItem -> FacilityDetailInformation -> ordered screen Column
      -> _requestAction -> FacilityBookingScreen or existing admin contact

Inspected backend/core/api/views.py:1488, serialize_facility: it already supplies the required photos, rates, workflow configuration, hours, features, requirements and terms. It supplies no ratings/counts or individual feedback. No serializer change was needed.

Functions and inputs/outputs:

- build takes widget.facility and returns the gallery, ordered saved sections and a separate Scaffold bottomNavigationBar.
- _rentalRates takes FacilityDetailInformation and renders primaryRate, actual extra-hour/alternative rates and custom notes; it never calculates quotes.
- _overview takes the same formatter and renders actual name/category/Chat, location, capacity and optional valid rating.
- _FacilityHeroGallery takes uploaded URLs, index and PageController. Swiping updates only the counter/dots; ProductImage retains progress/error fallbacks.
- _DetailSection takes heading, content and optional status. Its Wrap prevents enlarged headings/badges from overflowing; decorative icons do not repeat spoken text.
- _ExpandableDetailText takes saved text and optional terms label. TextPainter measures four lines at actual width/text scale. Local expanded state changes the preview and native button semantics only.
- _Amenities takes nonblank saved strings and returns two columns or a single narrow/large-text column.
- _requestAction returns null for unavailable status, _book for supported slots, or the original admin-contact action. _book passes the same FacilityItem and service to FacilityBookingScreen.
- _FacilityBookingBar takes primaryRate and that handler. Scaffold reserves footer height outside the scroll; SafeArea clears navigation insets. The footer stacks below 330dp content width or above 1.3x text scale.

Annotated isolated example: price_type=base_hour, rate=3000, pricing.base_duration=4 and additional_hour_rate=500. The existing formatter produces "₱3,000 / first 4 hours" in both rate locations, plus a separate "Additional hour: ₱500 / hour". These are test fixture inputs; runtime always uses the supplied catalog record.

### 5. Backend / API behavior

No backend, endpoint or authorization changes. Details no longer prefetches today's slots. Request Booking opens the original form, which loads/retries slots, checks conflicts, gets server quotes and submits the original request. Non-slot categories retain contact routing. Django retains eligibility, availability, payment and approval enforcement.

### 6. Database / migration impact

None. No schema, migrations, live rates, fees, reviews or bookings were changed. Favorite retains its existing local SharedPreferences storage. Test fixtures never enter the application/database.

### 7. Tests performed

Final result: **27/27 focused tests passed (7 seconds)**. Analysis reported **No issues found (4 seconds)**. Final formatting checked **3 files with 0 changes**; the scoped git whitespace check reported no errors. Commands run from campushub:

    flutter test --no-pub test/facility_details_test.dart test/facility_booking_flow_test.dart
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart test/facility_booking_flow_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart test/facility_booking_flow_test.dart

CAPTURE_FACILITY_DETAILS=true writes actual RepaintBoundary captures to ignored scratch/facility-details-continuous-20261029 at repository root. A clearly named fixture uses an existing campus asset to exercise image decoding. These are widget captures, not fabricated live facilities or Android screenshots.

Rendered20 fixture captures covering375/390dp phones,320dp at2x text and844x500 landscape. Inspected top/rates, schedule, terms/reviews, enlarged-text wrapping and landscape. The first capture run had a test-only lazy-list assertion failure; final suite is green after fixing scrolling in that test. The final UI code was included in the second capture run; no extra visual polish cycle was added.

Built and installed the debug APK on the connected Android17/API37 emulator, opened the actual saved Covered Court from Facilities and scrolled through the continuous page. Native screenshots android-details-top.png and android-details-bottom.png in the same ignored scratch folder show the actual uploaded1/1 photo, saved base/extra/alternative rates, weekend hours, booking restrictions, terms preview and genuine empty reviews state. The sticky price/action remains visible above system navigation at both ends. No booking was submitted. The debug session was detached, leaving the app open. Native landscape, large text and TalkBack were not separately exercised; those responsive cases were checked by widget tests/captures.

### 8. Remaining limitations / troubleshooting

Current API supplies neither review totals nor individual feedback, so live records show No reviews yet. Existing conditional month display does not introduce monthly billing/quote support. The inherited white Details surface remains white in surrounding dark mode. No full screen-reader, performance or physical-device certification.

If hours say Not configured, inspect saved operating_hours: missing days are never invented as open/closed. Invalid ranges stay Schedule needs review. For Contact Admin / Pricing needs review, inspect saved rate/type/base-duration instead of hardcoding. Missing optional sections mean blank saved fields. Disabled Request Booking reflects saved status; never bypass _requestAction.

The first adapted loading/retry checks looked for lazy booking-list items before scrolling to them. The tests now scroll to each item; booking-screen logic was unchanged. Removed one obsolete test import reported by analysis.

Safe practice: change base_duration from 4 to 3 in detailFixture only and update its expected primary label. Run both focused test files. Verify both primary-rate locations say first 3 hours while the extra-hour charge stays separate. Restore the fixture/expectation afterward. Never practice on live rates or booking records.

## Internet-inspired booking sheet layout - October 29, 2026

Design brief before implementation: replace the previous venue-guide composition with a photo-led booking sheet for the same campus audience and existing Flutter route. Considered a floating sheet, a magazine-like split view and a compact booking ticket; selected the sheet on phones plus a description/rates split on wide screens. Keep navy `#1A1851`, gold `#FCB315`, white `#FFFFFF`, pale surface `#F8FAFC`, secondary `#66687A` and border `#E2E4EC`; bundled Montserrat and native controls remain. Use one rounded sheet edge at the photo, one pale facts group, one light rate card and existing flat sections. No new booking steps, thumbnails, images, reviews or example records.

Internet references: [Airbnb's listing guidance](https://www.airbnb.com/resources/hosting-homes/a/how-to-set-up-an-effective-listing-page-12) supports photos plus clear title/description/amenities/rules; [Poula Adel's booking concept description](https://dribbble.com/shots/26620197-Hotel-Booking-App-UI-Reimagining-the-Way-You-Book-Your-Stay) emphasizes clear prices/actions and balanced minimal layout. These inspire principles; this is not a pixel reproduction or a claim to have inspected a current Airbnb app. Pallo's booking-concept result was found but its page fetch failed, so it is not used as primary evidence. Dribbble's extracted image link pointed to an advertisement, which was not used as a design reference or asset.

```text
phone: photo -> rounded white sheet edge -> status/name/Chat
       pale facts -> four tabs -> light rates -> about -> terms
wide:  photo -> bounded sheet/facts -> four tabs
       about + terms                 light rates
both:  sticky configured price + existing Request Booking
```

Brief review: preserve the latest status/name/category4dp, reviews directly above Location, one Capacity row, gold underlined four tabs, saved-days Schedule, centered Reviews empty state, removed fee UI and scrolling Back/Favorite. UI/UX Pro Max's initial booking query returned irrelevant mobile-browser/keyboard advice; a narrowed Flutter adaptive-layout search returned applicable LayoutBuilder and Row/Column guidance. Followed the latter. Emil motion decision: no new entrance/tab/scroll animation; preserve direct native interactions and reduced-motion-aware gallery dots. Make the layout change visible through grouping and responsive placement instead of decorative motion.

### 1. Cause / reason

The user requested a different modern booking layout researched across the internet and then asked to continue. The preceding change mainly adjusted typography/colors; this revision changes grouping and responsive placement in the existing screen. All source data and handlers remain the same.

### 2. Exact files changed

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facility_details_screen.dart` | 162 max width; 336 `_overviewContent`; 408/418 split/stack keys; 426 `_overview`; 508 facts panel; 691 gallery IgnorePointer sheet edge; 795 `_DetailSection` | Wider adaptive reading region, description/rates split, grouped metadata and light rate card |
| `campushub/test/facility_details_test.dart` | 486 wide2× case; 515 split/stack geometry assertions; 808 render harness Overview capture | Verify wide/stacked layouts, add wide2× fallback case and full Overview previews |
| `docs/mobile-services-navigation.md` | 3 this section | Sources, design brief, implementation report, functions/data flow and safe practice |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Latest layout scope and actual verification |
| `campushub/DESIGN.md` | Facility Details / Facts Before Rates / rates panel | Current sheet, facts and adaptive Overview specifications |
| `campushub/.impeccable/design.json` | `extensions.facilityDetails.reading`, `type`, `gallery`, `verification` | Keep existing companion consistent |
| `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md` | Direction | Persist latest layout and data/interaction boundaries |

Seven project files: one runtime Dart file, one existing test file and five existing guides/design records. No unrelated changes were reset.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Straight photo/content boundary | 24dp rounded white sheet edge over the last20dp of the gallery | Visually connects the photo to the reading surface without pinning controls |
| Separate fact rows | One pale16dp-padded facts panel | Groups actual reviews, location and capacity while preserving order |
| Navy rate block with a scoped inverse theme | White outlined rate card with a gold title accent | Gives the main photo more visual emphasis and simplifies rate text roles |
| Single620dp reading column everywhere | Up to960dp content; at720dp content width and <=1.3× text, description/terms left and320dp rates right with28dp gap | Uses tablet space while keeping readable lines and the current phone ordering |
| Same layout at large text | Single-column fallback above1.3× text | Gives labels and long configuration values room to wrap |

Phone order remains rates, About This Facility, then Terms & Guidelines. In wide Overview, About/Terms stay together and the rates card aligns with their top. Empty description/terms keep rates in a single column. The footer remains independently bounded at620dp, with the existing gold Request Booking action. No rates, reviews, schedules, facilities or actions were added. Exactly four gold-underlined tabs and all recent status/Chat/metadata/Schedule/Reviews choices remain.

### 4. How it works: functions, inputs/outputs and data flow

```text
Existing API -> FacilityItem -> FacilityDetailInformation
  -> _overview: status/name/category/Chat + grouped real metadata
  -> _overviewContent(information)
       rates = original configured-price/options widgets
       description = original saved About + Terms widgets
       LayoutBuilder constraints + TextScaler
         wide: description | 28dp | 320dp rates
         narrow/large text: rates -> description
  -> same sticky price and original request handler
```

`_overviewContent(information)` returns one Row or Column; it never requests or calculates data. Its local widgets reuse the former Overview branches, including saved Additional hour immediately below the primary rate and its divider. The old inverse rate-panel theme and two obsolete navy-panel constants were removed; semantic text roles now read the screen's navy/muted-on-white scheme.

The sheet edge is an IgnorePointer decoration within the existing gallery Stack, so it cannot capture swipes or Back/Favorite presses. It is visual only, not a draggable bottom sheet. The PageView's actual image list and controls still scroll together. No new controller or animation was needed.

Annotated example: if usable content width is804dp and text scale1, `_overviewContent` places the rates card in the right column. With the same width at2× text, it returns the stacked layout. Missing descriptions do not create an empty left column. This constraint-based approach avoids device-name checks and preserves the native user's text settings.

### 5. Backend / API behavior

Unchanged. Facility loading, uploaded images, original booking/contact navigation, live slot checks, review validation, configured prices, eligibility, approvals and payment behavior retain their existing implementation. No endpoint or permission was added. Internet references supply layout ideas only; their content/booking rules are not copied into CampusHub.

### 6. Database / migration impact

None. No schema, migrations, working records, rates, dependencies, font assets or images changed. The capture photo remains the pre-existing isolated test fixture. No device launch/install/reload or deployment was performed.

### 7. Tests performed and visual review

Final commands from `campushub/`:

```powershell
flutter test --no-pub --dart-define=CAPTURE_FACILITY_DETAILS=true test/facility_details_test.dart test/facility_booking_flow_test.dart
flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
dart format --output=none --set-exit-if-changed lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
```

**25 tests passed (12 seconds)**; analysis found no issues (2 seconds); final formatting verified two files with zero changes. Existing tests retain tabs/content isolation, Back/Favorite scrolling/navigation, saved data boundaries, Schedule errors/Retry, terms expansion and actual request/conflict behavior. Updated responsive checks verify the split key and equal top/right-side geometry on normal wide layouts; the new844dp/2× case verifies a stacked fallback without overflow.

Refreshed20 actual Flutter fixture captures in ignored `scratch/facility-details-tabs-20261029`: top/overview/schedule/amenities/reviews at375/390dp,320dp2× and844×500 landscape. Inspected390dp top/Overview/Reviews,844dp top/Overview and320dp2× Overview. Checks covered rounded photo edge, name/category/Chat alignment, facts order, rate text and divider legibility, side-by-side column position, enlarged-text wrapping, tabs and sticky action. No generated images, current live-app screenshot, physical-device or full accessibility pass is claimed. The unchanged text pairs remain navy/white16.24:1, navy/gold8.97:1 and muted/white5.49:1; the pale facts surface uses the existing functional neutral.

Commands from campushub:

    flutter test --no-pub --reporter expanded test/facility_details_test.dart test/facility_booking_flow_test.dart --dart-define=CAPTURE_FACILITY_DETAILS=true
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

### 8. Remaining limitations / troubleshooting / safe exercise

No live authenticated chat, browser or physical-device run. Native widget rendering supplies visual evidence; the user's running app workflow remains under their control. The sheet edge is intentionally not draggable and adds no new interaction. Existing review/backend/monthly-pricing limitations remain. Earlier screenshots and navy-panel specs below are historical.

Reload through your normal workflow, then inspect Overview on a phone and a wider device. The latter should show About/Terms beside rates; enlarged text should restore the vertical flow. If columns do not appear, inspect content width (not physical display width), text scale and whether description/terms exist. As a safe exercise, trace the existing844dp responsive fixture into LayoutBuilder and change only its test scale from1 to2; verify the split key is replaced by the stacked key and rerun both existing test files without changing real facility records.

## Modern venue-guide visual direction - October 29, 2026

Design brief before implementation: Facility Details helps campus users judge an actual venue and enter its existing request flow. Compared a venue guide (photo and clear facts), a booking ticket (denser transaction emphasis) and soft hospitality (more cards/curves). Chose the venue guide for the campus audience. Its single strong visual focus after the photo is the configured rate on navy, complemented by a gold booking action. Kept the user's current information architecture and actual data.

Local palette: navy `#1A1851`, Flutter gold `#FCB315`, white `#FFFFFF`, existing quiet surface `#F8FAFC`, secondary ink `#66687A`, outline `#E2E4EC`. Two named navy-panel tones support readable secondary copy/dividers. Typography remains bundled Montserrat: compact strong venue title, 16sp section headings, 13–14sp data, native scaled controls. Layout remains left-aligned, bounded at 620dp independently of the viewport-wide photo; 4/8dp details and 24dp section rhythm. Existing interaction-driven dots/disclosures remain; no entrance effects or generated assets.

```text
saved photo + Back/Favorite (scroll with photo)
saved status
venue name / category                 Chat
review summary / location / capacity
Overview   Amenities   Schedule   Reviews
navy rates panel -> description -> terms
sticky configured price       gold Request Booking
```

Brief review: retained white, fonts, exactly four gold-underlined tabs, status above name, 4dp category gap, review above Location, saved-days schedule, centered review empty state and removed fee UI. Avoided a new font, generic gradients, repeated card grids or fictional venue content. Local UI/UX Pro Max search returned Flat Design and Material 3 Expressive; adopted flat/no-shadow structure and native LayoutBuilder/Semantics guidance while preserving CampusHub's palette rather than the search's unrelated expressive colors. Native Flutter widget renders and interaction tests are the appropriate evidence here; the user's device workflow remains under their control.

### 1. Cause / reason

The user invoked ui-ux-pro-max, frontend-design and frontend-design-codex and requested modern design inspiration. Applied one coherent visual treatment directly to the existing Flutter Facility Details screen. This visual refinement keeps the user's recent content placement and existing functionality rather than creating another route or prototype.

### 2. Exact files changed

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facility_details_screen.dart` | 14–15 named navy tones; 166 content gutters; 184 underline; 415 `_overview`; 752 `_DetailSection`; 936 `_RentalPrice`; 997 `_DetailLine`; 1045 `_ExpandableDetailText`; 1140 `_FacilityBookingBar` | Venue-guide palette, typography, density, navy rates surface and gold primary action |
| `docs/mobile-services-navigation.md` | 3 this section | Design alternatives/brief, local system, implementation report and verification |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Persist latest visual direction and actual results |
| `campushub/DESIGN.md` | Facility Details / Facts Before Rates / rate panel | Current component treatment and existing font/content boundaries |
| `campushub/.impeccable/design.json` | `extensions.facilityDetails.reading`, `type`, `verification`; Facts Before Rates narrative | Existing design companion updated to current treatment |
| `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md` | Direction | Persist the native visual direction in the existing surface record |

Six project files: one runtime Dart file and five existing documentation/design records. Models, tests, assets, dependencies and unrelated screens were not changed.

### 3. Changes made

The page stays white with the full-width uploaded-photo carousel. Tighter photo-to-content spacing and a 23sp/700 venue title give the saved facts a clearer hierarchy. The status text remains above the name with a small decorative gold rule; it does not encode a new availability state. Name/category retain the 4dp gap beside the now outlined, lightly surfaced icon-over-Chat control. Metadata is 14sp, and section rhythm is 24dp. Native tabs retain exactly four labels with a slightly stronger 3dp gold underline.

Rental Rates becomes the one navy content panel, with white primary amounts and `#DEDEEB` secondary copy. Additional hour remains directly below the main rate with its divider, now `#6E6C94` for contrast against navy; remaining configured options/notes retain their order. The sticky action becomes `#FCB315` gold with navy text. Disabled behavior, actual rate text and the original booking/contact callback remain. Schedule, Amenities and centered Reviews empty-state structures remain as requested.

### 4. How it works: functions, inputs/outputs and data flow

`FacilityItem` and `FacilityDetailInformation` still supply the same saved strings. `_overview(information)` only changes typography, spacing and Chat styling. `_DetailSection(panel: true)` now paints navy and scopes a native Theme to its child, so `_RentalPrice`, `_DetailLine` and `_ExpandableDetailText` read `ColorScheme.onSurface` and `onSurfaceVariant`. Outside that panel, those roles remain navy/muted on white. This avoids copied pricing logic and keeps the panel theme from recoloring the rest of the page.

```dart
// Only the existing rates panel supplies this local surface treatment.
colorScheme.copyWith(
  surface: bookingNavy,
  onSurface: Colors.white,                 // amounts and values
  onSurfaceVariant: _detailOnNavySecondary, // labels and billing basis
);
// _RentalPrice still renders the same saved `price` and spoken semanticsLabel.
```

`_FacilityBookingBar(price, label, onPressed)` returns the same safe-area footer and responsive row/column layout; only its enabled button colors change. Example: changing tabs still shows the identical configured rental amount and original Request Booking action, now with the gold treatment. No rate, review, schedule or status is generated by the design.

### 5. Backend / API behavior

Unchanged: existing facility loading, saved photos/hours/reviews, slot checks, contact routing and booking form remain. No endpoint, serializer, permissions, quote calculation, approval, fee, discount, deposit or payment logic was changed. No message was sent.

### 6. Database / migration impact

None. No schema, migrations, records, rate configuration, assets or dependencies changed. No app launch, installation, device reload or deployment was performed.

### 7. Tests performed and visual review

Final run:

```powershell
flutter test --no-pub --dart-define=CAPTURE_FACILITY_DETAILS=true test/facility_details_test.dart test/facility_booking_flow_test.dart
flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart
dart format --output=none --set-exit-if-changed lib/module_app/screens/facility_details_screen.dart
```

**24 tests passed (9 seconds)**; analysis found no issues (1.2 seconds); formatting verified one file with zero changes. Existing tests cover four-tab navigation, content isolation, gallery swipe/Back/Favorite, reduced motion, enlarged text, Schedule saved data/loading/Retry and the original request/validation/conflict flow. No new test that merely mirrors the visual implementation was added.

Refreshed 16 native Flutter fixture renders in ignored `scratch/facility-details-tabs-20261029`. Inspected 390dp Overview, 375dp Reviews, 844×500 landscape Overview and 320dp/2× Schedule, then the final 390dp Overview after improving the divider. Visual checks included photo crop, name/category/Chat alignment, metadata order, active tab, white/navy rate legibility, sticky footer safe area and enlarged-text wrapping. These are actual widget renders using the existing bundled photo only in test fixtures. No browser URL applies to this native Flutter verification; no browser/device screenshot is claimed.

Calculated opaque-color contrast: white/navy **16.24:1**, panel secondary/navy **12.18:1**, navy/gold **8.97:1**, secondary/white **5.49:1**, panel divider/navy **3.27:1**. The initial divider was 2.91:1; lightened its named tone, rerendered and reran the focused suite. These calculations verify the listed pairs, not every state or a full accessibility audit.

Ten design checks applied: preserved white background; preserved the bundled font; no gradients; no shadows/glows; no unrelated colors; no repeated decorative card grid; no invented content; native working controls; readable measured text pairs; responsive/reduced-motion behavior retained. Motion remains limited to the existing interaction feedback and carousel/disclosure behavior.

Commands from campushub:

    flutter test --no-pub --reporter expanded test/facility_details_test.dart test/facility_booking_flow_test.dart --dart-define=CAPTURE_FACILITY_DETAILS=true
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

### 8. Remaining limitations / troubleshooting / safe exercise

No physical-device, TalkBack/VoiceOver, live authenticated chat or browser run. The page intentionally remains a light surface even under a dark surrounding theme. Existing review/API and monthly billing limitations remain. Long names can wrap beside Chat at large text sizes; no clipping or shrinking was introduced.

Reload through your own normal workflow. Verify status/name/category/reviews/location order, switch all four tabs, expand/collapse terms and open the original Request Booking flow. If panel text appears dark, inspect whether that widget reads the scoped `ColorScheme.onSurface` rather than a fixed navy color. If the footer price becomes white, check that the panel Theme still wraps only its child. As a safe exercise, trace one existing rate fixture through `primaryRate` into both `_RentalPrice` instances, compare their inherited surfaces, and rerun the two existing test files without changing real prices or records.

## Saved status above name and small category gap - October 29, 2026

1. **Cause / reason:** The user requested a little spacing between name/category and the facility status above the name.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:418` (`_overview`, saved status Text and 6dp gap; name/category Column with 4dp gap); this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; and existing header specifications in `campushub/DESIGN.md` (Facts Before Rates), `campushub/.impeccable/design.json` (reading) and the Facility Details surface brief (Direction).
3. **Changes made:** Added the existing nonempty `facility.status` as plain navy text above the name/Chat row, with 6dp separation. Added 4dp between the name and its saved category inside their shared column, keeping spacing independent of Chat's height.
4. **How it works:** Existing API status is already normalized by `FacilityItem.fromJson`; `_overview(information)` displays that same `facility.status`, without inventing availability. For example, the existing available status displays Open for Booking; maintenance displays Under Maintenance. Empty status omits this label. The same value still controls the original booking action and remains in Schedule.
5. **Backend / API behavior:** Unchanged; presentation only, with original status validation, booking, favorite and chat callbacks.
6. **Database / migration impact:** None; no records, migrations or schema changes.
7. **Tests performed:** All 24 existing Facility Details/booking tests passed (4 seconds), including responsive text layouts and unavailable booking behavior. Scoped screen analysis found no issues (1.2 seconds); formatting verified one file with zero changes. No new tests were added for these presentation changes.
8. **Remaining limitations:** No fresh rendered screenshot or physical-device check. Long status/name/category text retains natural wrapping. Earlier captures show the previous spacing/status revision.

**Troubleshooting / safe exercise:** Reload through your normal workflow. Confirm the saved status appears above the name and the category has a small gap beneath the name. If the status looks wrong, trace the actual API status through `FacilityItem.fromJson` before changing presentation; do not hardcode Open for Booking. Safely read the existing available/maintenance test fixtures and their model mapping, then rerun the two existing test files without changing real records.

## Compact facility name and category - October 29, 2026

1. **Cause / reason:** The user requested removal of the extra space between the facility name and its Court/Sports category. The category previously followed the entire name/Chat Row, so the taller icon-over-Chat button added empty height beneath a short name, plus an explicit 6dp gap.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:422`, anchor `_overview` / Expanded name-and-category Column; this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; and existing header specifications in `campushub/DESIGN.md` (Facts Before Rates), `campushub/.impeccable/design.json` (`extensions.facilityDetails.reading`) and the Facility Details surface brief (Direction).
3. **Changes made:** Moved the existing category Text into the same left-aligned Column as the name, inside the Row's Expanded child. Removed the explicit 6dp spacer. Chat stays beside that column with its existing touch area.
4. **How it works:** `_overview(information)` reads the same `facility.name` and nonempty `facility.facilityTypeLabel`. The name and category now determine their own vertical flow rather than waiting for Chat's full height. Example: a one-line Covered Court name is immediately followed by its saved Sports Facility category; long names still wrap before the category. Reviews remain directly above Location.
5. **Backend / API behavior:** Unchanged; display-only widget nesting, with existing chat, booking and data-loading handlers retained.
6. **Database / migration impact:** None; no records, migrations or schema changes.
7. **Tests performed:** Existing two-file Facility Details/booking run with local captures passed all 24 tests (11 seconds). Scoped screen analysis found no issues (1.5 seconds); formatting reported one file with zero changes. Inspected refreshed 390dp normal and 320dp/2× header renders in `scratch/facility-details-tabs-20261029`. No new test was added for this spacing change.
8. **Remaining limitations:** No physical-device run. Enlarged text and long saved names retain natural wrapping; this change does not shrink or truncate text.

**Troubleshooting / safe exercise:** Reload through your normal app workflow and confirm the category follows the name closely while Chat stays at the right. If a gap remains in an older build, inspect whether the category Text is inside the Expanded Column at this anchor. As a safe exercise, compare that nesting with the previous category-after-Row arrangement in this explanation, then run the two existing test files; do not alter real facility names/categories to practice.

## Operating-days card, Reviews empty state and gallery scrolling - October 29, 2026

### 1. Cause / reason

The user requested review metadata immediately above Location, a Schedule card matching their reference, removal of Additional Fees, and a centered Reviews empty state with an icon above the message. They confirmed that Back/Favorite should scroll away with the photo. Source inspection found these controls already inside the scrolling gallery, so their existing implementation was retained and directly regression-tested rather than adding pinned controls.

### 2. Exact files changed

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facility_details_screen.dart` | 111 `operatingDayLabels`; 283 Operating Schedule; 342 `facility-reviews-empty`; 411 `_overview`; 723 `_DetailSection`; 776 `_OperatingScheduleCard` | Saved-days card, weekday grouping, review placement/container, remove the entire Additional Fees & Discounts display and its unused expansion state |
| `campushub/lib/module_app/models/facility_detail_information.dart` | 68 `operatingDays` | Read-only seven-day display states derived from existing validated schedule/configuration |
| `campushub/test/facility_details_test.dart` | 163 tab/header/empty-state test; 280 gallery route/scroll/toggle test; 323 weekend card; 355 missing/invalid days; 720 render harness | Verify layout, real configuration boundaries, scroll-away controls, Back route and favorite toggle; capture Schedule instead of removed charges section |
| `docs/mobile-services-navigation.md` | 3 this section | Eight-part report, data flow, debugging and safe practice |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Persist the user's latest choices and actual verification |
| `campushub/DESIGN.md` | Facility Details / Facts Before Rates | Update current metadata order, schedule, removed fee display, empty state and scrolling behavior |
| `campushub/.impeccable/design.json` | `extensions.facilityDetails.gallery`, `tabs`, `verification`; Facts Before Rates narrative | Keep the existing companion record consistent |
| `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md` | Direction | Current layout and real-data boundaries |

Eight project files: two runtime Dart files, one existing test file and five existing documentation/design records. No unrelated source was reset or changed.

### 3. Changes made

- Header order: name with labeled Chat, category, actual review summary, saved Location, inline Capacity. No duplicate location, summary divider or photo counter was added.
- Schedule: calendar icon/title, outlined Operating Days container, Monday–Sunday initials, navy active days, optional Weekend Only label from the saved flag, divider and saved hours. Consecutive weekdays with the same displayed value share one row; Saturday/Sunday stay separate. Rules/status/eligibility/requirements, live slots and their existing Retry/request behavior remain beneath it.
- The Additional Fees & Discounts section is removed from Facility Details, including the former deposit/discount rows in that section. The formatter and actual backend fee/discount/deposit rules remain intact; booking financial behavior is not changed.
- Reviews without validated aggregates show an outlined container with a centered star icon above No reviews yet. Supplied valid aggregates retain their existing actual summary and honest feedback-unavailable text.
- Back/Favorite remain inside the gallery and scroll offscreen with it. Existing Back navigation and local favorite persistence/toggling remain.

### 4. How it works: functions, inputs/outputs and data flow

```text
Existing API workflow_config.operating_hours + weekend_only
  -> FacilityItem.workflowConfig
  -> FacilityDetailInformation.schedule (existing time validation/formatting)
  -> operatingDays: seven label/value/isOpen records
  -> _OperatingScheduleCard: day markers + grouped weekday/time rows

Existing rating/reviews -> reviewSummary
  -> metadata above Location
  -> Reviews aggregate summary OR centered empty container

Existing ListView -> gallery Stack -> Back/Favorite
  -> original Navigator.maybePop / SharedPreferences callbacks
```

`operatingDays` returns no day records if hours are not a structured map; the existing free-text Operating hours row remains available in the rules list. For a map, configured valid hours yield `isOpen: true`, explicit closed days yield false, missing days yield `Not configured`/null, and invalid ranges yield `Schedule needs review`/null. Saved weekend-only restrictions make weekdays `Unavailable`/false; weekend hours still need actual configuration. The screen filters weekday rows out of the old flat list to avoid repeating them below the card.

Example using only the isolated test fixture: saved Saturday/Sunday 08:00–17:00 plus `weekend_only: true` produces inactive weekdays, active S/S, Monday–Friday Unavailable and the two actual weekend-hour rows. Those values are never hardcoded into the application. A missing Wednesday remains Not configured rather than inventing closure/open hours. The card is presentation, not availability/conflict validation.

### 5. Backend / API behavior

Unchanged. No endpoint, serializer, permission, quote, fee, discount, deposit, approval or payment logic was modified. Existing booking requests still use server schedule/conflict checks. No review records or hours were created; current API limitations around review data remain.

### 6. Database / migration impact

None. No schema, migrations, working records, rates, assets or dependencies changed. Back/Favorite use their existing route/local-preference behavior; test preferences are isolated. No app installation, launch or device reload was performed.

### 7. Tests performed

From `campushub/`, ran:

```powershell
flutter test --no-pub --dart-define=CAPTURE_FACILITY_DETAILS=true test/facility_details_test.dart test/facility_booking_flow_test.dart
```

**24 tests passed (10 seconds).** Three-file analysis found no issues (1.5 seconds); final formatting verified three files with zero changes. Tests cover saved weekend restrictions/hours, unknown/invalid states, removed fee UI, review metadata order, centered icon/message, Back closing a pushed route, both favorite states, controls scrolling out of the hit area and returning, existing booking/conflict behavior, responsive widths, enlarged text and reduced motion.

The existing isolated render harness refreshed captures in ignored `scratch/facility-details-tabs-20261029`; Schedule now uses `schedule-*` filenames. Visually inspected 390dp Schedule and Reviews plus 320dp/2× Schedule. These are real Flutter widget-fixture renders, not native screenshots or generated images. Older `charges-*` files are historical and do not depict the current UI.

Commands from campushub:

    flutter test --no-pub --reporter expanded test/facility_details_test.dart test/facility_booking_flow_test.dart --dart-define=CAPTURE_FACILITY_DETAILS=true
    flutter analyze --no-pub lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart
    dart format lib/module_app/screens/facility_details_screen.dart test/facility_details_test.dart

### 8. Remaining limitations / troubleshooting / safe exercise

No physical-device, live authenticated chat or full screen-reader audit was performed. Day markers describe saved operating hours; they do not assert that a bookable slot is free. Unknown configuration stays explicit. The financial section's removal does not waive charges calculated in the existing booking workflow.

Reload in your normal workflow. Verify reviews appear above Location; open Schedule to compare each row against Facilities Admin's saved hours. If no days highlight, inspect missing/invalid hours rather than adding defaults. Open Reviews without aggregate data to check the centered empty state. Scroll the photo offscreen and return; Back should close a pushed detail route and Favorite should toggle normally. As a safe exercise, inspect the existing weekend fixture, change one test-only weekend to null, and verify its open marker disappears while the displayed closed state remains accurate. Run the two test files; do not edit real facility schedules to practice.

## Additional hour directly below the rental price - October 29, 2026

1. **Cause / reason:** The user requested Additional hour immediately below the Rental Rates price with a horizontal line beneath it.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:198` (`_RentalPrice`, followed by Additional hour at 200, Divider at 207 and remaining options at 219); this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; and `campushub/DESIGN.md` (Facility Details rate-panel specification). Companion Home/filter changes and exact file inventory are in `docs/mobile-seller-application.md` top.
3. **Changes made:** Render the configured Additional hour option first after the main rate, then a neutral Divider with 24dp total height. Custom notes and alternative/shared-room options follow. Exclude Additional hour from the later option loop so it appears once. No divider is added when Additional hour is not configured.
4. **How it works:** Existing `FacilityDetailInformation.rateOptions` formats Admin configuration into label/value records. The widget selects the existing `Additional hour` record for the first position; remaining records keep their original relative order. For example, an existing base-duration package with a configured additional-hour amount displays the primary price, that saved extra-hour rate, divider, then the saved alternative rate. Inputs, formatting and outputs retain the same actual amounts; no rate or quote is computed here.
5. **Backend / API behavior:** Unchanged; Django remains responsible for configured pricing, quotes, eligibility and approvals. The sticky primary rate and Request Booking use the original handlers.
6. **Database / migration impact:** None; no rates, records, migrations or dependencies changed.
7. **Tests performed:** The combined Home/seller/facility run passed 74 tests (15 seconds), including existing configured-rate, responsive-details and booking tests. Seven changed Dart files passed analysis (2.1 seconds) and formatting (zero changes). The companion guide records the test-only gesture correction discovered in that run.
8. **Remaining limitations:** No fresh screenshot/device run. This remains a conditional saved rate; facilities without Additional hour do not receive an invented amount or empty divider.

**Troubleshooting / safe exercise:** Reload through your normal workflow and inspect an existing facility with Additional hour configured. Confirm it appears once immediately below the primary price, with the divider beneath it. If missing, trace `workflow_config.pricing.additional_hour_rate` through `FacilityDetailInformation.rateOptions` before inspecting the widget. Use the existing isolated rate fixture to compare configured/missing options safely, then run the two facility test files without editing production rates.

## Review-first header, labeled chat and Overview guidelines - October 29, 2026

1. **Cause / reason:** The user requested reviews above the facility name, removal of the duplicate location, a Chat label below the icon, and Terms & Guidelines below About This Facility with a chevron instead of Read Full Terms.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:243` (Overview Terms & Guidelines), 384 (`_overview`, review at 393, chat at 416), 835 (`_ExpandableDetailText`, optional `disclosureLabel`, chevron at 866); `campushub/test/facility_details_test.dart:169` (review/header/single location), 434 (terms expansion/collapse and request route); `campushub/test/facility_booking_flow_test.dart:206` (single location and Overview-only terms); this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; and existing current specs in `campushub/DESIGN.md` (Facts Before Rates/Overview), `campushub/.impeccable/design.json` (tabs/reading/narrative) and its Facility Details surface brief at line 18.
3. **Changes made:** Order is now review summary, name with icon-over-Chat button at right, category, saved location and inline capacity. Removed only the second Location section from Overview. Moved saved terms from Schedule to Overview immediately after About This Facility and titled them Terms & Guidelines. Removed Read Full Terms; long terms show a centered down-chevron control underneath, changing to an up chevron while expanded. Schedule retains saved operating rules, requirements and charges.
4. **How it works:** `_overview(information)` still receives existing saved data; the chat TextButton calls the same `messageFacilitiesAdmin(context, facility.id)`. `_ExpandableDetailText(text, disclosureLabel)` measures saved text against four lines. With `disclosureLabel: 'terms and guidelines'`, overflowing text gets a 48dp IconButton with Expand/Collapse tooltip and expanded semantics. Tapping changes only local `expanded` state and `Text.maxLines` between 4 and unlimited. Short terms need no expansion control. Other existing description/requirements/pricing text retains Read more/Show less. Example: a long saved terms record initially displays four lines plus a down chevron; tapping reveals the rest and changes the chevron upward.
5. **Backend / API behavior:** Unchanged; saved reviews, location and terms use existing fields. Chat retains its original contact/conversation flow; no message is automatically sent. No approval/payment/rate change.
6. **Database / migration impact:** None; no records, migrations or schema changes.
7. **Tests performed:** Final focused details/booking run passed all 21 tests (3 seconds). Checks include review above name, labeled 48dp chat, one location, Overview-only terms, expanded and collapsed text, responsive cases and booking actions. Three-file analysis found no issues (1.6 seconds) after removing the unused legacy expansion-label parameter. Dart formatting applied to the final source. No new screenshot or physical-device run.
8. **Remaining limitations:** Live authenticated chat and native accessibility behavior were not exercised. Missing saved terms still omit the section; no example guidelines were invented. Earlier captures/layout sections are historical.

**Troubleshooting / safe exercise:** Reload in your normal app workflow. Confirm the new header order and one location, then open Overview and expand/collapse a long saved terms record through the chevrons. If no chevron appears, check whether the configured text already fits within four lines. Safely trace the existing test fixture's `terms_conditions` input through `FacilityItem` to the new Overview section and local disclosure state; rerun both existing test files rather than editing production records.

## Facility name, review summary and header chat - October 29, 2026

1. **Cause / reason:** The user requested removal of the summary line, moving the review summary beneath the facility name, and placing chat to the right of that name.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:392` (`_overview`; name/chat Row, chat key at 416, review summary at 430, capacity at 453); `campushub/test/facility_details_test.dart:169` (header geometry/order, no divider, 48dp target and relocated tooltip); `campushub/test/facility_booking_flow_test.dart:264` and 268 (existing chat locator); this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; current facts specs in `campushub/DESIGN.md:277`, `campushub/.impeccable/design.json:332`, and `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md:18`.
3. **Changes made:** Removed the divider and its extra 20dp spacing. Placed the name in an Expanded child beside a 48dp navy outlined chat IconButton. Moved the existing Message Admin action from the bottom of the content into that button, avoiding duplicate chat controls. Display order is name/chat, actual review summary, category, location and inline capacity.
4. **How it works:** `_overview(information)` renders the same saved `facility.name` and validated `information.reviewSummary`. The icon's `onPressed` calls the unchanged `messageFacilitiesAdmin(context, facility.id)`. Its tooltip supplies the accessible name `Message Admin`; long names wrap in the remaining row width. No new review data or destinations are introduced.
5. **Backend / API behavior:** No backend changes. The existing helper in `booking_widgets.dart:663` reads the existing Facilities contact endpoint, initializes the signed-in chat service and opens the existing facility-context conversation. Its sign-in/error feedback remains. Tapping the chat icon intentionally opens that existing flow; no message is sent automatically.
6. **Database / migration impact:** None; no records or schema were changed during implementation.
7. **Tests performed:** Final 21 Facility Details/booking tests passed (4 seconds), including header geometry/order, no summary divider, 48dp target, narrow screens, enlarged text, carousel and booking regressions. Three-file analysis found no issues (1.7 seconds); final format check reported three files, zero changes. Initial runs caught two old text-button locators in the booking test; both now find the relocated button through its tooltip, and the final run passed.
8. **Remaining limitations:** No fresh screenshot, physical-device run or live authenticated chat request was performed. Chat still requires the existing backend contact and signed-in chat configuration. Earlier captures and layout reports are historical.

**Troubleshooting / safe exercise:** In your normal running app, reload and confirm name/chat share a row, the review summary sits directly below and no divider remains beneath Capacity. For a safe code exercise, trace the icon callback to `messageFacilitiesAdmin` and read its existing contact/conversation inputs and error handling without contacting a real admin. Run the two existing test files to verify layout locally. To manually verify navigation when appropriate, use your normal signed-in test environment and open chat without sending a message.

## Carousel without a counter and summary divider - October 29, 2026

1. **Cause / reason:** The user requested removal of the numeric photo count (including `1 / 1`) and a horizontal line beneath Capacity.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:452` (`_overview`, Divider below Capacity), line 549 (`_FacilityHeroGallery`, removed counter overlay; dots at 634); `campushub/test/facility_details_test.dart:523` and 547 (existing two-photo swipe assertions); this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; `campushub/DESIGN.md:277` and 279; `campushub/.impeccable/design.json:239` and 332; and `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md:18`.
3. **Changes made:** Removed the numeric overlay for every gallery size. Retained uploaded images, PageView swiping, Back/Favorite and animated dots for multiple images. Added a 1dp neutral Divider with 20dp spacing below the final summary row, before the four tabs.
4. **How it works:** `_FacilityHeroGallery` receives the existing image list and current index. PageView updates that index, which still selects the active dot; the index no longer renders as a numeric badge. Photo accessibility labels retain their contextual position. `_overview(information)` renders the saved capacity followed by the divider; if capacity is absent, the divider still separates the summary from tabs. No new inputs or records are introduced.
5. **Backend / API behavior:** Unchanged; uploaded-photo and booking data still use existing paths.
6. **Database / migration impact:** None; no records or schema changes.
7. **Tests performed:** All 21 existing Facility Details/booking tests passed (3 seconds), including the two-photo swipe, active dots, responsive layouts and booking actions. Two-file Flutter analysis found no issues (1.9 seconds); formatting verified two files with zero changes. Numeric count expectations now assert absence.
8. **Remaining limitations:** No fresh screenshot or physical-device run; older captures below show previous revisions.

**Troubleshooting / safe exercise:** Reload through your normal app workflow. Open a facility with one saved photo, then one with multiple photos: neither should show a numeric counter. Swipe the latter and confirm the active dot changes. Confirm the horizontal line appears below Capacity and above the tabs. To learn the flow safely, trace `PageView.onPageChanged` to `_currentImageIndex` and the dot color/width without editing saved photo data. The existing two-photo test provides an isolated fixture for verification.

## Facility Details capacity row - October 29, 2026

1. **Cause / reason:** The user requested removal of the separate Facility type fact and a single Capacity row. Previously `_FacilityFacts` put the capacity label above its value beside a type column.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:404` (`_overview`, capacity text at 448, retained `_IconDetail` at 781); `campushub/test/facility_details_test.dart:214` (saved custom type assertion); `campushub/test/facility_booking_flow_test.dart:209` (capacity assertion); this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; and the current facts specifications in `campushub/DESIGN.md`, `campushub/.impeccable/design.json` and `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md`.
3. **Changes made:** Removed the separate type fact and now-unused `_FacilityFacts` grid. Reused `_IconDetail` for the people icon and inline `Capacity: [saved value]` text. Updated existing assertions and current design records.
4. **How it works:** `_overview(information)` receives the existing `FacilityDetailInformation`; its `capacity` getter formats the configured capacity/range. A nonempty value renders one full-width icon/text row. For example, saved bounds 300 and 500 yield `Capacity: 300–500 persons`. Missing capacity omits the row. `_IconDetail` uses an Expanded text child so unusually large text can wrap safely instead of clipping. Category beneath the name remains a separate existing label.
5. **Backend / API behavior:** Unchanged; the type field remains in the model/API for existing workflow decisions. This removes only its separate summary display.
6. **Database / migration impact:** None; no records, schema or migrations changed.
7. **Tests performed:** Existing Facility Details and booking test files passed all 21 tests (4 seconds), including narrow screens, 2× text, landscape, request flow and removed type assertions. Three-file Flutter analysis found no issues (2.3 seconds). Dart format verified three files with zero changes.
8. **Remaining limitations:** No fresh screenshot or physical-device run. Capacity is one metadata row with inline label/value; enlarged text may wrap naturally for readability.

**Troubleshooting / safe exercise:** In your normal app workflow, reload and open a facility with a saved capacity. Confirm the people icon and `Capacity: value` share a row, with no separate Facility type fact. If capacity is missing, inspect the actual Admin capacity settings and the existing `FacilityDetailInformation.capacity` getter; do not substitute sample values. As a safe exercise, inspect the existing test fixture's minimum/maximum capacity and trace those inputs through the getter to `_overview`, then run the two test files above. Earlier sections describe historical revisions.

## Facility Details gold tab underline - October 29, 2026

1. **Cause / reason:** The user requested the selected tab accent shown in their reference to use `#FCB315`, superseding the earlier navy underline.
2. **Exact files changed:** `campushub/lib/module_app/screens/facility_details_screen.dart:178`, anchor `TabBar.indicatorColor`; this guide at line 3; `CAMPUSHUB_CONTEXT.md:3`; and the existing tab specifications in `campushub/DESIGN.md` (Facts Before Rates) and `campushub/.impeccable/design.json` (`extensions.facilityDetails.tabs` and Facts Before Rates narrative).
3. **Changes made:** Replaced only `indicatorColor: bookingNavy` with `indicatorColor: bookingGold`. The existing shared constant in `campushub/lib/module_app/widgets/facilities/booking_widgets.dart:9` already equals `Color(0xFFFCB315)`; that file was not edited. Labels retain navy/muted colors and existing weights. Updated the current design records to match.
4. **How it works:** `build(context)` returns the existing screen. The native `TabController` supplies the selected index to `TabBar`; `indicatorColor: bookingGold` paints the underline beneath that selected tab. It does not change any inputs, data loading, layout or navigation. Example: selecting Amenities moves the same gold underline from Overview to Amenities.
5. **Backend / API behavior:** Unchanged; this is a presentation property only.
6. **Database / migration impact:** None; no records or schema changed.
7. **Tests performed:** Scoped Flutter analysis passed with no issues (1.1 seconds). Dart formatting verified one file with zero changes. No new tests were added or widget tests rerun for this single color property.
8. **Remaining limitations:** No fresh rendered or physical-device check. The user controls app reload. This change does not claim a full accessibility audit.

**Troubleshooting and safe practice:** In your normal running app, reload, open Facility Details and tap all four tabs. Verify the gold underline follows selection, navy text stays readable and Request Booking stays visible. If the underline remains navy, confirm the running build includes `indicatorColor: bookingGold` at the anchor above. For a safe learning exercise, inspect the shared color constant and trace its reference to this property without editing any rate, API or booking handler. Earlier verification totals below belong to the prior layout revision.

## Four-tab Facility Details and carousel pagination - October 29, 2026

### 1. Cause / reason

The user explicitly requested the existing Airbnb-inspired Facility Details design with exactly **Overview / Amenities / Schedule / Reviews**, a swipeable carousel with animated dots/counter, a persistent configured price and Request Booking, and removal of Check Availability. Source inspection confirmed that the current gallery already used`PageView` and had no thumbnail strip, but lacked pagination dots; its information was one continuous document and included Check Availability. This update reorganizes that screen without changing the broader app design or backend.

Applied the explicitly invoked frontend-design and ui-ux-pro-max skills. Kept the existing Montserrat, navy/white, typography hierarchy, single rates panel, spacing and native controls; this screen's gold accent is the requested`#FCB316`. Local skill searches returned no applicable tab-navigation recommendation (the retry found a performance-tab entry), so native Flutter TabBar behavior and the skill's general touch/responsive guidance were used as the fallback. No new visual direction, image-generation step or approval checkpoint was introduced.

### 2. Exact files changed and current anchors

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facility_details_screen.dart` | 29 ticker mixin; 34 `_tabIndex`; 47 controller listener; 76 `_loadSlots`; 85 `_tabChanged`; 166 `TabBar`; 190/249/260/353 selected content; 396 Request Booking; 404 `_overview`; 562 `_FacilityHeroGallery`; 671 pagination `AnimatedContainer`; 989 booking bar | Four tabs, content placement, pagination, removed availability action, saved facility type and stable request action |
| `campushub/lib/module_app/models/facility_item.dart` | 35 optional `customFacilityType`; 105 JSON parsing; 142 field | Preserve the existing serializer's`custom_facility_type` for display, with backward-compatible empty default |
| `campushub/test/facility_details_test.dart` | 150 `selectTab`; 164 tab-isolation regression; 201 real aggregate/empty amenities; 335 responsive cases; 502 swipe/dots; 555 captures; 597 settled capture helper | Verify exactly four tabs, isolated content, persistent action, custom type, real-data boundaries, responsive selection and carousel indicators |
| `campushub/test/facility_booking_flow_test.dart` | 157 existing details/booking regression | Select Amenities and Schedule to inspect relocated content; expect removed action and retained existing booking flow |
| `docs/mobile-services-navigation.md` | 3 this section | Current eight-part report, data flow, troubleshooting and safe exercise |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Preserve this explicit structure and actual verification |
| `campushub/DESIGN.md` | `Facility Details — October 29, 2026` / Facts Before Rates rule | Update the existing component spec to the four tabs, dots/counter and removed action |
| `campushub/.impeccable/design.json` | `extensions.facilityDetails.gallery`, new`tabs`, `verification`, Facts Before Rates narrative rule | Keep the existing design companion consistent; no new preview asset |
| `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md` | Confirmed hierarchy / Direction / data boundaries | Record the user's latest exact structure in the existing scoped record |

Nine project files: two runtime Dart files, two existing test files and five documentation/context/design records. Unrelated screens and working changes remain intact. Previous implementation sections are historical; their continuous-section layout, multiple-image-only counter and Check Availability behavior are superseded here. Previous independent-review verdicts do not certify this new tabbed revision.

### 3. Changes made

| Area | Implemented behavior |
| --- | --- |
| Carousel | Existing viewport-width PageView and uploaded-image URL/loading/error handling retained. Nonempty galleries show the real counter, including`1 / 1`. Multiple images add an18×6dp navy active indicator and6×6dp gray circles, with160ms ease-out transitions after a swipe and zero duration under reduced motion. No thumbnails, automatic rotation or generated/replacement photos. |
| Information | Saved name, category, location and validated rating/review summary, then capacity and facility type. A nonempty saved custom type takes precedence; otherwise use the actual type code's existing display label. No fabricated purpose or new booking-mode fact is added. |
| Overview | Saved primary rental rate/billing basis, configured additional-hour/alternative/shared-room options, custom pricing notes, description and location information. |
| Amenities | Existing enabled`amenities` list rendered by the current responsive icon grid. This list already contains configured equipment/features and normalized Other Feature text. Empty list:`No amenities listed.` No separate equipment configuration is introduced. |
| Schedule | Saved operating days/hours, booking mode/status/restrictions, eligibility and advance-payment conditions; existing date-specific live slot/error/Retry output; active fees/discounts, applicable deposits, requirements and terms. The Check Availability button/key is removed. Existing slot selection still uses the original request handler. |
| Reviews | The existing validated summary or`No reviews yet`. If supplied aggregate data is valid but no individual comments exist in the response, show`Customer feedback is not available.` No sample comments, review distribution, View All action or new review endpoint. |
| Sticky bar | Remains outside the scrolling/tabbed body and repeats the same configured price on every tab. The visible label is always`Request Booking`. Existing status disabling and category-specific booking-form/admin-contact handler remain unchanged. |

Native TabBar has exactly four horizontally arranged labels, a navy active underline, scalable text and native focus/selection behavior. It scrolls horizontally when the device width or enlarged text requires it. Only the active content is mounted; tabs do not create another booking or quote calculation. The controller has zero transition duration; user-requested carousel dot motion remains independently enabled unless reduced motion is set.

### 4. How it works: functions, inputs/outputs and data flow

```text
Existing Django serialize_facility -> existing API/facility loader
  -> FacilityItem.fromJson
       existing rate, price_type, workflow_config, images, amenities and terms
       additionally retain existing custom_facility_type
  -> existing FacilityDetailInformation: display labels only
  -> FacilityDetailsScreen
       PageView.onPageChanged -> current image index -> counter/dot appearance
       native TabController.index -> _tabChanged -> _tabIndex
         0 Overview | 1 Amenities | 2 Schedule | 3 Reviews
       unchanged sticky formatted primary rate + _requestAction
  -> original FacilityBookingScreen / admin-message route
```

`_tabChanged()` has no inputs and updates only the selected index from the four-entry controller; it never touches a record. Its listener and controller are removed/disposed with the existing page controller. `customFacilityType` is an optional string whose parser reads an already-existing API response field; old constructors still work without supplying it.

`_FacilityHeroGallery(images, currentIndex, ...)` renders only the saved list and existing fallback. Its AnimatedContainer dots change size/color in response to the index. `_overview(information)` reads saved values; `_RentalPrice` still styles the same primary rate for body/footer. No billing calculation was moved out of Django.

The existing `_slots` request can finish while Schedule is not mounted. `_loadSlots()` attaches`Future.ignore()` to prevent an unhandled asynchronous error in that interval; this does **not** replace the Future or turn failure into an empty/successful schedule. The Schedule FutureBuilder reads that same Future and presents its existing error/Retry state, including a failure before the tab is opened. Returning from the existing booking form still refreshes these slot results.

Annotated selection example:

```dart
// Native controller is constructed with length: 4.
if (_tabIndex == 0) ...[/* configured rates, description, location */];
if (_tabIndex == 1) /* saved amenities or honest empty state */;
if (_tabIndex == 2) ...[/* saved rules, schedule, charges and terms */];
if (_tabIndex == 3) /* actual supplied review summary or empty state */;
// The sticky booking bar is outside these branches, so its price/action persist.
```

The actual runtime branches are ordinary widget lists; the example comments explain the data grouping rather than supplying application records. This approach preserves natural content height without an unbounded TabBarView or an additional horizontal swipe competing with the photo carousel.

### 5. Backend / API behavior

Unchanged: no endpoint, serializer, permission, request/response schema, pricing formula, discount verification, payment or approval workflow was edited. The model now retains the serializer's existing custom type. The original saved rate/method formatter supports the same hourly/base-duration/day/night/person/person-night/fixed/custom values and conditional monthly text as before; this task does not enable monthly admin billing. Non-slot facilities keep their original admin-contact request process under the unified Request Booking label. The booking form retains backend schedule rechecks and quote/create behavior.

### 6. Database / migration impact

None. No schema/migration/model/table/working-record/rate configuration/dependency/image asset change. The local favorite key is unchanged. No install, app launch, device reload, permission reset or deployment was performed.

### 7. Tests performed

From`campushub/`, ran:

```powershell
flutter test --no-pub --reporter expanded --dart-define=CAPTURE_FACILITY_DETAILS=true test/facility_details_test.dart test/facility_booking_flow_test.dart test/resource_catalog_cards_test.dart test/services_screen_test.dart test/service_catalog_test.dart test/home_page_test.dart test/seller_home_layout_test.dart
```

**72 tests passed; Flutter reported10seconds.** Final four-file static analysis reported **No issues found** in1.5seconds; formatting verification reported **4 files, 0 changed**. Tests cover exact tab count/order/selection, isolated content, persistent price/action, empty amenities, supplied/invalid review values, custom type, removed Check Availability, slot loading/Retry and failure before tab visibility, existing favorite/booking validation/conflicts, photo fill/swipe/counter/dot sizes, reduced motion,320/375/390/844dp,2× text and landscape. Existing Home/service/card regressions remain in the run.

The first focused run had one test-helper failure:`pumpAndSettle` could never finish while a deliberately pending Schedule spinner remained active. Replaced the tab helper's unbounded animation wait with bounded frame advancement; the subsequent21-test focused run passed. This does not disable loading or hide runtime failures.

Current actual Flutter widget captures are under ignored`scratch/facility-details-tabs-20261029/`: top/Overview, Amenities, Schedule/charges and Reviews at375/390dp,320dp/2× and844dp landscape (16 PNGs). Initial capture inspection found image-decoding/tap-ripple timing artifacts after tab selection; the harness now allows real fixture-photo decoding and native feedback to settle. The final capture-only test passed(7seconds), with representative refreshed phone, enlarged-text and landscape images inspected. The two-photo fixture repeats an existing bundled image solely for pagination/layout verification; it is never used by runtime as a facility-photo replacement or seeded as a record. No AI images or visual mockup substitutes were created. No native-device/full-accessibility pass is claimed.

### 8. Remaining limitations, troubleshooting and safe exercise

The current facility serializer has no individual customer-feedback rows, review aggregates or separate facility-purpose field. Optional rating/count fields already supported by the model are validated if supplied, but live responses normally produce`No reviews yet`. No review comments or purpose are inferred from names, booking purpose, description, other records or the design example. Adding missing backend fields/endpoints remains outside this UI-only request. Existing monthly/custom-price limitations remain honest.

If a custom type is missing, inspect`custom_facility_type` in the existing response. Missing amenities require saved enabled features; additional fees do not prove equipment is provided. If Schedule errors after reopening its tab, use its existing Retry and inspect the actual availability response. On small screens/large text, swipe the tab row horizontally to reach all four labels; there are still exactly four tabs. Images must come from saved Facilities Admin uploads. Use the normal user-controlled Flutter reload/rebuild workflow to see the saved changes.

Safe practice: modify only`detailFixture()` to supply a custom type and empty amenities, run`flutter test --no-pub test/facility_details_test.dart`, and check the saved type/empty state. Switch each tab and confirm the footer rate is identical. In the image fixture, swipe from the first to second photo and verify the counter and elongated dot move together. Restore the fixture; do not change working rates, comments or bookings to test presentation.

## Professional minimalist Facility Details refinement - October 29, 2026

### 1. Cause / reason

The user requested another modern, professional, minimalist treatment using impeccable and other inspiration beyond the supplied example image. In the preference check, the user chose **facility name and key facts first, rental rates next**. The existing identity, full-width photo, titleless Back/Heart header, saved information and real booking flow remain the foundation. This is a scoped refinement, not a replacement app design.

The direction draws on a quiet hospitality information sheet and native task-oriented details: measured typography, aligned facts and a distinct rate decision area. No named external product is being reproduced, no new image was generated, and the reference's sample map, prices, reviews, thumbnails and approval-preview controls are not application data.

| Before | After | Why |
| --- | --- | --- |
| Category above the name | Facility name leads; category follows as secondary information | Match the user's selected priority |
| Capacity as another metadata row | Capacity and the existing booking mode share a plain responsive fact grid | Make key facts easier to scan without decorative tiles |
| Entire price uses the same large text | Amount is prominent; the billing basis is smaller but readable | Distinguish the rental amount from its charging condition |
| Rates flow like every other section | One light, fully outlined rates panel; remaining sections stay flat | Give the rate decision a clear boundary without nesting cards |
| Every label/value uses equal left alignment | Values align to the right on normal widths and stack for long content/large text | Keep compact numbers aligned and preserve long conditions |
| Gold outline star even when no rating exists | Muted outline star with the honest empty summary | Avoid giving absent feedback a rated appearance |

### 2. Exact files changed and current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facility_details_screen.dart` | 11 direction contract; 130 viewport-width scroll/gallery; 149 content gutter; 157 `panel: true`; 338 `_overview`; 630 `_DetailSection`; 668 `_FacilityFacts`; 721 `_RentalPrice`; 778 `_DetailLine`; 893 `_FacilityBookingBar` | Scoped hierarchy, facts, rate typography/panel and responsive alignment; existing state and handlers retained |
| `campushub/test/facility_details_test.dart` | 104 `height`; 106 `reducedMotion`; 260 viewport cases; 457 optional captures; 505 capture directory | Add375dp and landscape coverage, reduced-motion inputs and current fixture captures |
| `docs/mobile-services-navigation.md` | 3 this section | Current report, source/data map, checks, troubleshooting and practice exercise |
| `CAMPUSHUB_CONTEXT.md` | newest entry | Preserve the accepted direction and results |
| `campushub/DESIGN.md` | 50 scoped Montserrat roles; 190 overview; 249 independent gallery/reading widths; 275 component; 283 functions; 287 evidence | Additive record of the built Facility Details component; unrelated rules retained |
| `campushub/.impeccable/design.json` | 235 scoped extension; 330 narrative rule | Required machine-readable companion for the same built spec; no new preview asset |
| `campushub/.impeccable/surfaces/ib-module-app-screens-facility-details-screen-dart.md` | 1 target mapping; 8 Scope and mode | Persist the confirmed Operate-mode hierarchy and route-specific constraints |

Seven project files: one runtime Dart file, one existing test file and five documentation/context/design records. The shipped impeccable documenter merged the scoped design record without replacing the existing design system. Temporary review fixtures/captures are not shipping assets. Historical sections remain implementation history; this section supersedes their ordering, rate typography, gallery width and content-spacing descriptions only.

### 3. Changes made

The photo/gallery behavior and48dp Back/Heart controls remain. The gallery now sits outside the620dp reading-width constraint and fills the viewport even in landscape; dossier content and footer retain their bounded measure. Below the photo, the name has a deliberate24sp/600 leading role, followed by category, review summary and saved location. Capacity and booking mode appear as two unboxed facts, stacking when width or text scaling requires it. No purpose, capacity, location or rating is inferred from the reference image.

The content uses20dp side gutters,28dp section separation and16sp/600 section headings. Rental Rates is the only tonal panel, with16dp inset/radius and the existing subtle outline/light-surface tokens. The amount uses26sp/700 and the billing basis13sp; the sticky footer uses19sp/700 and12sp. The text remains one complete rate label for assistive technology. Amounts use tabular figures; whole/cents formatting, custom pricing and the saved charging method remain supplied by the existing presentation helper. Additional-hour, alternative-hourly and shared-room conditions remain separate.

Long fee/deposit/discount values and enlarged text stack label over value instead of forcing narrow columns. Ordinary rows align values to the right. The footer keeps its native navy Request Booking button and bottom safe area, stacking at the existing narrow/large-text threshold. Description/terms expansion, active charges, amenities, schedule loading/error/Retry/empty states, disabled unavailable facilities, Message Admin and non-slot contact guidance remain.

### 4. How it works: functions, inputs/outputs and data flow

```text
Existing API -> unchanged FacilityItem / FacilityDetailInformation
  -> _overview: saved name, category, reviews, location, capacity and booking mode
       _FacilityFacts(facts) -> responsive plain icon/label/value rows
  -> _DetailSection(panel: true) -> one rates panel
       _RentalPrice(price, compact) -> one Text.rich label with amount/basis styles
  -> _DetailLine(label, value) -> right-aligned row or stacked readable pair
  -> existing gallery, information, availability, terms and contact sections
  -> _FacilityBookingBar -> compact _RentalPrice + original request handler
```

`_FacilityFacts` receives existing typed display records and returns layout only. It never reads the database or changes booking modes. `_RentalPrice` receives the existing formatted label, splits the first` / ` only for a numeric peso label, and styles the amount separately; unfamiliar/custom labels remain complete text. It supplies the unchanged full string as its semantics label. It never parses a price into a booking charge. `_DetailSection` adds a surface only when its new optional`panel` flag is true. `_DetailLine` uses width, text scaling and long value length to select a stacked or horizontal composition. The original `_requestAction`, `_book`, `_loadSlots`, favorite storage and service calls are unchanged.

Annotated layout example:

```dart
// Existing configured label; no price calculation or new request occurs.
_RentalPrice(price: information.primaryRate);
// For '₱3,000 / first 4 hours': emphasize ₱3,000, retain the full billing basis.
// The footer reads the same input with compact: true.
```

This keeps presentation choices separate from Django calculations and avoids a second price source. The new fact grid joins existing data to the selected hierarchy rather than adding a new feature or category.

### 5. Backend / API behavior

Unchanged. No endpoint, request, response field, authentication, permission, quote, payment, approval, eligibility rule or business calculation changed. Review aggregates remain unavailable in the current serializer, with the existing honest empty summary. The actual booking form still rechecks availability and quotes through Django; custom/monthly/non-slot limitations from the preceding sections remain.

### 6. Database / migration impact

None. No model, schema, migration, production record, stored rate, dependency or asset changed. Existing favorites still use the same local preference. No device app was launched, installed or reloaded; the user's selected-device workflow remains theirs to control.

### 7. Tests performed

Ran the same seven test files as the preceding implementation, with`--no-pub --reporter expanded --dart-define=CAPTURE_FACILITY_DETAILS=true`. **70 tests passed**, first in9seconds and again in8seconds after the finish review's photo-width correction. Corrected-source analysis of the two changed Dart files reported **No issues found** in1.6seconds. Final post-correction formatting verification reported **2 files, 0 changed**. Tracked source whitespace check found no errors, only the existing LF/CRLF conversion notice. New/updated guide, harness and surface brief have no trailing whitespace; the documenter verified its JSON parsing and single Markdown frontmatter structure.

The updated cases cover320/375/390/844dp,320dp at2× text,844×500 landscape, reduced-motion/accessibility-navigation inputs, top image/control geometry, footer safe area and52dp minimum action, favorite persistence, real navigation, price/data preservation, valid/invalid images, expansion and live-schedule states. Existing card/service/Home/booking regression cases remain in the run.

One batched render inspection covered all eight fixture PNGs under ignored`.impeccable/review/facility-details/`: top/charges at375dp,390dp,320dp/2× and844dp landscape. The finish reviewer identified that the landscape gallery still shared the620dp text constraint; the correction moved it outside that constraint and refreshed the same eight captures for a bounded second review. The harness loads actual bundled Montserrat/icons; photos, fees and names are isolated test fixtures and never seed application records or replace facility images. A node calculation of the actual sRGB tokens measured navy/white16.24:1, muted/white5.49:1, muted/light-panel5.25:1 and white/navy16.24:1. These measure these pairs only, not a full accessibility audit or system-bar contrast over arbitrary photos.

### 8. Remaining limitations, troubleshooting and safe exercise

The independent impeccable finish reviewer returned **ship at the two-fix verdict scope**: the viewport-wide photo and design persistence were both scored resolved. All eight refreshed captures were rechecked with no fix-induced visual regressions observed. This is not a whole-app or physical-device approval.

Review and captures are scoped to source, automated behavior and Flutter widget renders. They are not native device/emulator or live-record screenshots. OS bars, TalkBack/VoiceOver, physical gestures, actual device text rendering and full dark-mode behavior have not been certified. The established white details surface remains white in a dark surrounding theme; this task does not add an app-wide theme. No web detector ran because it does not analyze native Dart widgets. The impeccable native screenshot gate cannot be claimed from these fixture captures.

If a fact is missing, inspect its saved API value or supported booking mode before adding labels. If a long rate wraps, check the complete billing basis at the actual text size; do not clip it or substitute the screenshot's example value. The full-width gallery still needs real uploaded photos; its missing/error fallback is unchanged. Use the user's normal Flutter refresh/rebuild workflow to see source changes; no preview-state switch is needed.

Safe practice: change only the long facility name or additional-fee condition in`detailFixture()` and rerun`flutter test --no-pub test/facility_details_test.dart`. Check that text wraps, the original rate string remains complete and the sticky action stays above the bottom inset. Compare375dp normal text with320dp/2× and landscape; restore the fixture afterward. Do not edit production rates or create bookings to practice layout work.

## Image-first Facility Details - October 29, 2026

### 1. Cause / reason

The user supplied a Facility Details brief and demonstration screenshots, then clarified that the image should fill the top, only back/heart controls should appear there, the `Facility Details` title should disappear and preview-state buttons should not be implemented. The existing application had a separate title bar, an inset gallery, repeated bordered/shadowed cards, a raw `per base_hour` pricing basis and a two-button footer. No `Preview Submitted Screen` or `Preview Approved State` buttons existed in the Flutter application; the screenshots are references, not an instruction to simulate approval.

Applied the explicitly invoked `emil-design-eng` skill to the existing implementation. The screen uses deliberate spacing, native interaction feedback and the existing swipe behavior; no decorative entrance, stagger, scale or spring animation was added.

| Before | After | Why |
| --- | --- | --- |
| Separate Facility Details app bar above an inset image | Full-width top gallery with back/heart overlays and no title bar | Give the actual facility image the top of the screen |
| Category overlay, gradient and decorative indicators | Category below the photo; a counter only for multiple saved images | Keep the photo clear and avoid redundant chrome |
| Multiple nested bordered/shadowed cards and amenity tiles | Flat sections and simple icon/text amenities | Improve hierarchy with spacing rather than containers |
| Raw rate plus `per price_type` | Saved primary pricing, distinct additional-hour/alternative/shared-room conditions | Explain configured pricing without adding mutually exclusive options |
| Message Admin and Book Now equally prominent in the footer | Sticky rate and Request Booking; admin contact remains inline | Keep the next action clear and retain existing contact access |
| Poppins in this screen | Scoped bundled Montserrat, as specified by this brief | Apply the requested typography without changing the app-wide font |

### 2. Exact files changed and current anchors

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facility_details_screen.dart` | 13 `FacilityDetailsScreen`; 47 `_loadFavorite`; 57 `_toggleFavorite`; 63 `_loadSlots`; 69 `_book`; 79 `_requestAction`; 321 `_overview`; 359 `_availability`; 450 `_FacilityHeroGallery`; 665 `_ExpandableDetailText`; 736 `_FacilityBookingBar` | Replace the details presentation, retain favorite/navigation/contact behavior, and render configured information |
| `campushub/lib/module_app/models/facility_item.dart` | 34 optional `workflowConfig`; 99 `fromJson` mapping; 138 `workflowConfig` | Retain the existing API workflow object for read-only display; existing constructors and raw fields remain compatible |
| `campushub/lib/module_app/models/facility_detail_information.dart` | 4 `FacilityDetailInformation`; 11 `primaryRate`; 15 `capacity`; 25 `reviewSummary`; 39 `rateOptions`; 67 `schedule`; 145 `charges`; 243 `money`; 254 `_time` | New presentation helper for structured saved rates, schedule and charge conditions |
| `campushub/test/facility_booking_flow_test.dart` | 156 image-first details test | Update old title/footer expectations and assert the existing favorite preference and retained sections/contact |
| `campushub/test/facility_details_test.dart` | 146 saved configuration; 187 invalid/shared configuration; 262 responsive cases; 307 expansion/route; 331 loading/Retry; 355 unavailable/non-slot; 397 immediate error; 409 image fill/swipe; 444 optional captures | Isolated information, layout and interaction verification |
| `docs/mobile-services-navigation.md` | 3 this section | Current report, data flow, troubleshooting and safe exercise |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Save accepted behavior and measured verification |

Seven project files: three runtime Dart files, two test files and two existing documentation/context files. Other workspace changes remain intact. This section supersedes the preceding card-pricing section's statement that Facility Details still uses its old rate presentation; card pricing behavior itself is retained.

### 3. Changes made / expected behavior

- The gallery fills its content width, starting at the top. The photo area is220–260 logical pixels plus the status-bar inset, within the existing620dp maximum content width on wider screens. `ProductImage` uses `BoxFit.cover`, existing uploaded-image URL resolution, bounded decoding, loading and failure/missing-image fallback. Back and heart have48dp targets and tooltips, positioned below the status-bar inset. Only multiple actual saved images produce a counter, such as`1 / 2`; no photo count is invented for an empty gallery.
- Category, prominent facility name, validated review summary, saved location and saved capacity follow the gallery. `capacity_label` takes precedence; otherwise the helper uses a valid configured minimum/maximum or positive maximum. It no longer adds an assumed campus location when the saved location is missing. Status is plain information in the schedule section.
- Rental Rates uses the existing card pricing mapping with `hours` expanded for this details view. Base duration, additional-hour and optional alternative hourly rates remain separate. Shared-room pricing includes the configured required guest count in one room. Custom notes appear only for saved custom pricing. No rental total, discount amount or deposit amount is calculated locally.
- Saved description, requirements and terms preview four rendered lines. `TextPainter` checks the actual width and text scaling before offering Read more / Read Full Terms; Show less collapses the text. Amenity rows use only saved amenities, with two columns where practical and one at large text sizes.
- Operating information displays saved hours/closed days, booking mode, minimum duration, weekend restriction, check-in/out, advance payment days and eligible-client configuration when present. Missing weekdays are not inferred to be closed or open. Invalid structured time ranges say`Schedule needs review`. Existing backend availability provides today's actual slot statuses, with distinct loading/error/Retry/empty output. Check Availability and available slot rows reuse the existing booking destination and honor the facility status.
- Active configured fees display their charging basis. Applicable saved deposits remain separate, including fixed/percentage basis and conditional refund wording. Active discount rules include client type, amount/percentage and scope, with eligibility verification required. More than three charge entries can expand. Inactive/malformed entries do not become invented charges.
- The sticky white footer has the primary rate and navy Request Booking action, with a safe bottom inset. It stacks at narrow widths or enlarged text. Request Booking opens the existing slot request form; non-slot facility categories retain Contact to Request and their existing admin-message path. Unavailable facilities cannot activate booking/schedule actions. Message Admin remains an inline action. No preview-state buttons, duplicate booking flow, immediate approval, new rate editor or new review-submission/list route was added.

### 4. How it works: functions, inputs/outputs and data flow

```text
Existing Django serialize_facility(facility)
  -> saved rate/method, capacity, description, images, amenities, terms
  -> existing workflow_config pricing / hours / fees / deposit / discounts
  -> FacilityItem.fromJson(json) retains workflowConfig, existing fields/labels
  -> FacilityDetailInformation(facility)
       primaryRate/reviewSummary/capacity -> display strings
       rateOptions/schedule/charges -> lists of (label, value) records
  -> FacilityDetailsScreen -> top gallery / flat sections / sticky booking bar

Existing FacilityBookingService.slots(id, today's date)
  -> protected Django availability endpoint -> loading/error/empty/slot rows
Request Booking -> existing FacilityBookingScreen -> unchanged quote/create flow
Heart -> existing SharedPreferences key facility_favorite_<id>
Message Admin / non-slot request -> existing messageFacilitiesAdmin helper
```

`workflowConfig` is an optional map whose top-level parsed mapping is unmodifiable; widgets read it without editing saved data. The helper deliberately handles formatted presentation separately from backend financial calculations. `money(raw)` returns a peso string only for a finite nonnegative supported amount, or null for invalid input. `_time(raw)` formats valid24-hour clock strings without interpreting an operating day as availability. `rateOptions` and `charges` return conditions, not an itemized booking quote. `_loadSlots()` issues the existing request only for supported slot/assessment categories; non-slot categories now avoid the unnecessary hidden availability request. `_book()` returns from the existing form and reloads the details availability. `_requestAction` keeps the existing status/category-based destination selection.

Annotated example using **isolated test values**, not production defaults:

```dart
final facility = FacilityItem.fromJson({
  'rate': '3000.00', 'price_type': 'base_hour',
  'workflow_config': {
    'pricing': {
      'base_duration': '4',
      'additional_hour_rate': '500',
      'hourly_rate': '700',
    },
  },
});
final information = FacilityDetailInformation(facility);
// primaryRate: '₱3,000 / first 4 hours'
// rateOptions: 'Additional hour' -> '₱500 / hour',
//              'Alternative hourly rate' -> '₱700 / hour'.
// These values are not added; Django still determines the actual quote.
```

### 5. Backend / API behavior

No server, endpoint, serializer, request schema, authentication, permission, quote, approval or payment calculation changed. All fields used were already supplied by the existing facility API. The existing mobile schedule/quote/create workflow remains authoritative. Facility Details itself does not submit a booking. An available slot remains date-specific and is rechecked by the existing form/backend. Hostel, laboratory and lease workflows retain contact guidance rather than becoming generic slot bookings. Main navigation and Marketplace/Service screens are unchanged.

The facility API still does not supply review aggregates in the current serializer. The summary validates any supplied rating/count, otherwise showing`No reviews yet`. No review rows, ratings, View All Reviews or review-posting route are fabricated; there is no separate duplicate empty reviews panel.

### 6. Database / migration impact

None. No Django model, schema, migration, working record, price setting, permission, dependency or image asset changed. The existing local favorite key/storage behavior remains. No app installation, device restart, reload or deployment was performed.

### 7. Tests performed

Final resumed run from `campushub/`:

```powershell
flutter test --no-pub --reporter expanded --dart-define=CAPTURE_FACILITY_DETAILS=true test/facility_details_test.dart test/facility_booking_flow_test.dart test/resource_catalog_cards_test.dart test/services_screen_test.dart test/service_catalog_test.dart test/home_page_test.dart test/seller_home_layout_test.dart
```

**68 tests passed; Flutter reported12seconds.** Focused analysis of the five changed Dart files reported **No issues found** in4.2seconds. Final formatting verification reported **5 files, 0 changed**. Scoped tracked-file whitespace checking found no errors; Git noted only future LF/CRLF conversion. The earlier interrupted final command is not used as passing evidence.

Coverage includes320/390/844dp and320dp at2× text with a dark surrounding theme; top gallery width/position;48dp overlay controls;52dp minimum action and bottom safe area; local heart persistence; saved pricing/fee/discount/deposit separation; missing/malformed configuration; shared-room conditions; expandable description/terms; schedule loading/error/Retry and immediate failure before scrolling; status-disabled actions; non-slot contact path; actual image decoding/fill/swipe with invalid-image fallback; existing booking conflict/validation/submission and Home/service/card regressions. Initial analyzer brace-style findings were fixed before the final clean analysis.

Actual Flutter-rendered PNGs were refreshed in ignored `scratch/facility-details-20261029/`: `top-390.0-1.0.png`, `top-320.0-2.0.png`, `charges-390.0-1.0.png` and `charges-320.0-2.0.png`. Final390dp top and320dp/2× charge captures were inspected; earlier top/charge renders were also inspected. The harness loads the actual bundled Montserrat/icons and disables its debug banner. Its campus-entrance asset is explicitly an isolated photo fixture for decoding/layout, not a runtime replacement for a facility photo. No AI images were created. Web design-kit scripts are absent; no web-kit, full accessibility, live-database or physical-device pass is claimed.

### 8. Remaining limitations, troubleshooting and safe exercise

Facilities need saved uploaded photos to show a real image. Empty/failed images retain the existing icon fallback; the app never substitutes the fixture entrance photo. This screen displays the fetched facility snapshot; admin configuration changes require the normal catalog refresh/reopen workflow. The existing authenticated slot endpoint supplies today's schedule; a network failure shows Retry and a selected booking date is checked in the original form. Review listing/submission and server-supplied aggregate integration remain unavailable. Favorites remain local to the device. Conditional monthly label support does not add a Django monthly billing method. Large text makes the page longer and deliberately stacks the footer/metadata instead of truncating essential text. Native system-bar contrast over different real photos, physical gestures and screen-reader behavior still need device verification.

For an unexpected rate, inspect`rate`, `price_type` and `workflow_config.pricing` in the existing API response before changing widgets. For missing fees, verify their saved active flags, amounts and units. For missing/incorrect hours, inspect the structured operating-hours configuration rather than assuming availability. For missing photos, verify the saved URLs and existing media hosting. If the old title remains, use normal hot reload/rebuild; no separate preview screen needs enabling.

Safe practice: edit only`detailFixture()` in `test/facility_details_test.dart` to change the optional hourly rate, then run the focused test and verify that the primary base package stays unchanged while the alternative row updates. Set one fee inactive and verify it disappears without changing the base rate. Add a second fixture image, swipe and check the actual counter. Restore the fixture and rerun the tests; never change working rates or create real bookings for this exercise.

## Mobile facility pricing labels - October 29, 2026

### 1. Cause / reason

Confirmed in the existing source: `FacilityPreviewCard` displayed `FacilityItem.priceLabel`, which preferred the API's admin-oriented `price_compact_label`. That could show `pax / night`, `fixed`, a base package without `first`, or custom notes instead of the user's supplied mobile wording. This update changes facility card text on Home and Facilities. It preserves the wider vertical card arrangement documented below.

### 2. Exact files changed and current anchors

| File | Current line / nearby code anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/models/facility_item.dart` | 33 `this.baseDurationHours`; 95 JSON parsing; 129 `baseDurationHours`; 138 `cardPriceLabel` | Retain the saved package duration and provide a separate mobile card label |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 373 `price: facility.cardPriceLabel` | Both existing facility card destinations use the new display getter |
| `campushub/test/resource_catalog_cards_test.dart` | 50 `pricingExamples`; 63 `pricingFixture`; 304 mobile pricing; 317 incomplete configuration; 378 responsive pricing | Verify each method, saved values, fallback behavior and actual widget wiring; render fixture hostel with a person/night rate |
| `docs/mobile-services-navigation.md` | 3 this section | Current implementation report, debugging and safe exercise |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Preserve scope and verification results |

Five project files: two runtime Dart files, one existing test file and two existing documentation/context files. No other working changes were reverted.

### 3. Changes made

The following are **isolated examples**, not new records or default prices. Each actual amount comes from the saved `rate`.

| Admin method / API key | Mobile card example |
| --- | --- |
| Per Hour / `hour` | `₱700 / hour` |
| Base Duration + Additional Hour / `base_hour` | `₱3,000 / first 4 hrs` |
| Per Day / `day` | `₱1,500 / day` |
| Per Person / `person` | `₱125.50 / person` |
| Per Person / Per Night / `person_night` | `₱800 / person / night` |
| Per Night / `night` | `₱1,200 / night` |
| Fixed Rate / `session` | `₱2,500 / booking` |
| Custom / `custom` | `Price varies / See Rates` |
| Conditional monthly input / `month` or legacy `monthly` | `₱1,500 / month` |

Whole amounts omit `.00`; cents remain visible and thousands use commas. A one-hour package uses `first 1 hr`; fractional saved durations remain visible. Custom text has no numeric rate assumption. `See Rates` is display wording; the existing View Details button remains the action, with no new rate link or editor.

### 4. How it works: functions, inputs, outputs and data flow

```text
Existing Django serialize_facility(facility)
  -> rate, price_type, workflow_config.pricing.base_duration, existing labels
  -> existing FacilityService.fetchFacilities() / Home catalog fetch
  -> FacilityItem.fromJson(json)
       retain optional baseDurationHours from the existing workflow JSON
       preserve raw rate, priceType and catalogPriceLabel
  -> FacilityPreviewCard reads facility.cardPriceLabel
  -> existing ResourceCatalogCard renders the label
  -> existing View Details callback and booking flow
```

`FacilityItem.fromJson(Map<String, dynamic>)` returns a model and safely handles absent/non-map workflow or pricing containers for the new field. The constructor's optional `double? baseDurationHours` preserves existing direct constructor calls. `cardPriceLabel` takes the model's saved rate/method/duration and returns presentation text; it performs no rental, additional-hour, discount, deposit or payment calculation. `catalogPriceLabel` and the existing `priceLabel` getter remain unchanged for their existing consumers, including service-specific labels.

Annotated input/output example:

```dart
// Existing API fields; no extra request is needed.
final facility = FacilityItem.fromJson({
  'rate': '3000.00',
  'price_type': 'base_hour',
  'workflow_config': {
    'pricing': {'base_duration': '4', 'additional_hour_rate': '500'},
  },
});
// facility.cardPriceLabel returns '₱3,000 / first 4 hrs'.
// It does not multiply hours or add the additional-hour charge.
```

A separate card getter keeps mobile wording consistent without rewriting Django's admin labels or service prices. The package duration is read from structured data rather than guessed from a formatted string.

### 5. Backend / API behavior

Unchanged. Existing `backend/core/api/views.py` `serialize_facility` already sends all required fields; `workflow_for_display` retains saved pricing JSON. No endpoint, request, permission, validation, quotation, approval, payment or booking behavior changed. Django remains responsible for actual charges. The backend's physical rental method choices currently exclude monthly; recognizing monthly text on the client does **not** add an admin choice or enable a new booking calculation. Laboratory and other service card pricing are unchanged.

### 6. Database / migration impact

None. No models, schema, migrations, working records, configured rates, dependencies, assets, deployment or device installation changed.

### 7. Tests performed

Formatted the three changed Dart files; final format verification reported **3 files, 0 changed**. Scoped Git whitespace checks found no whitespace errors (only an LF/CRLF conversion notice); the updated guide and card test have no trailing whitespace. Focused static analysis reported **No issues found** (3.4 seconds). Ran from `campushub/`:

```powershell
flutter test --no-pub --reporter expanded --dart-define=CAPTURE_RESOURCE_CARDS=true test/resource_catalog_cards_test.dart test/services_screen_test.dart test/service_catalog_test.dart test/home_page_test.dart test/seller_home_layout_test.dart test/facility_booking_flow_test.dart
```

**56 tests passed** (Flutter reported 6 seconds). The run covers every pricing mapping, preserved raw/server fields, malformed/missing package duration, fractional/singular duration, invalid/nonfinite/nonpositive rates, unknown-method fallback, card text at390dp/light and320dp/dark with2× text, restored vertical layout, overlays, routes, service prices, Home and booking regressions. The initial sandbox run produced no output and was stopped; these results come from the successful SDK-access rerun.

Actual Flutter fixture captures were refreshed under ignored `scratch/facility-service-cards-20261029/`. Visually inspected `cards-414.0-1.0.png`: whole-amount hourly and person/night wording is readable, the image remains above content, and location/review overlays and View Details remain in place. These are isolated fixture captures, not live-record or physical-device evidence. This successful run also verifies the corrected vertical card arrangement that the preceding section had left pending. Web design-kit scripts are absent and no web-kit pass is claimed.

### 8. Remaining limitations, troubleshooting and safe exercise

For known numeric methods, invalid/nonfinite/nonpositive rates display `Contact Admin`, retaining the prior unpriced-card behavior. Base pricing requires a finite duration greater than0 and at most24 hours, consistent with Django's existing duration validation; missing/invalid duration displays `Pricing needs review` instead of inventing4 hours. Unknown/service-specific methods retain the configured server label, or `Contact Admin` if none exists. Custom and unknown methods can therefore display text without a positive numeric rate.

If a base card says `Pricing needs review`, inspect the saved `workflow_config.pricing.base_duration` in the existing API response and correct the configuration through the existing admin workflow. A formatted `price_label` alone is not a source for reconstructing duration. If the app shows old wording, use the normal Flutter hot reload/rebuild workflow; no reload or installation was performed here. Facility Details still has its existing rate presentation; this request only changes cards. Shared-room conditions, additional charges and client-specific eligibility remain outside the short primary card label.

Safe practice: edit only `pricingFixture` in the isolated test to use a base duration of`2.5` and expect `first 2.5 hrs`; run the focused card test. Remove the duration and expect `Pricing needs review`. Restore the fixture and rerun. Verify `record.rate` and `catalogPriceLabel` are unchanged, and use the existing action test to confirm View Details still works. Do not change production rates or booking records to try the formatter.

## Restore card arrangement and retain wider sizing - October 29, 2026

The user's latest correction is interpreted as restoring the **card** arrangement, not modifying a shopping-cart action. The image is again above the content. Reviews remain at the image's top-left and saved location at its bottom-left. This supersedes the interrupted side-by-side image/details experiment; only wider sizing is retained. The user explicitly limited scope to cards, so the long attachment's admin form, pricing preview and booking-flow changes were not implemented.

1. **Cause / reason:** the previous step turned the card into an image-left/details-right row; the user asked to revert positioning and only add width.
2. **Exact files / anchors:** `campushub/lib/module_app/widgets/facilities/resource_catalog_card.dart:42` (`Column`/`AspectRatio`) restores the image-above-body layout; `ResourceCardGrid` retains the732dp content breakpoint for two columns with360dp minimum width. `campushub/lib/module_app/widgets/home/home_preview_cards.dart:359` and`:391` retain320dp defaults; `campushub/lib/module_app/screens/home_page.dart:285` and`:298` allocate320dp Home previews before existing scaling/clamping. `campushub/test/resource_catalog_cards_test.dart:107` and the service-card assertions check the restored vertical geometry. `docs/mobile-services-navigation.md:3`, `campushub/DESIGN.md` (`resource-catalog-card`) and `CAMPUSHUB_CONTEXT.md:3` record the final decision. These are seven project files across the interrupted change and correction; scratch helpers/logs are not production files.
3. **Changes made:** restored4:3 image above category/name/information, then price and View Details. Preserved the image overlays, existing callbacks and320dp Home preview sizing. Listings remain full-width on phones, with two columns only at732dp content width or more. No new card controls or images were added.
4. **How it works:** existing API record -> unchanged `FacilityItem`/`ServiceItem` -> existing preview wrapper -> `ResourceCatalogCard`'s vertical `Column`. The `AspectRatio` bounds the existing `ProductImage` and overlay `Stack`. `ResourceCardGrid(children)` uses available width to choose one/two intrinsic-height rows; its finite height supports each card's footer spacer. Price/review helpers and all navigation callbacks are unchanged. Example: a390dp viewport with16dp page insets displays a358dp-wide card; the image uses that full width at4:3, while the body's name is below the image rather than beside it.
5. **Backend / API behavior:** unchanged. No requests, authentication, permissions, approval, quotation, payment, service guidance or shopping-cart behavior was modified. The previously documented missing review aggregates remain a limitation.
6. **Database / migration impact:** none. No model/schema/migration/record/configuration/dependency/asset change, deployment, device installation or reload.
7. **Checks performed:** read the saved widget and updated geometry assertions; checked that the image uses4:3, the body is below it, both overlays remain, the732dp breakpoint and320dp preview sizes remain, and the guide/design links agree. **The corrected layout's Dart formatting, static analysis, Flutter tests and fresh renders are pending.** The command was not executed because automatic approval review hit an account usage limit. Earlier52-test results and horizontal-layout screenshots belong to earlier revisions and are not evidence that this corrected revision passed. Source inspection is not a substitute for running Flutter.
8. **Remaining limitations:** runtime verification needs to resume when command approval is available. No physical-device verification was performed. At large text sizes the cards can be tall; names and billing text remain readable rather than being forced into short fixed heights. Long location previews remain two lines with the full tooltip/accessibility text.

| Before | After | Why |
| --- | --- | --- |
| Image beside the body | Image above the body | Restore the user's intended card arrangement |
| Earlier260dp Home previews | Retained320dp previews, clamped by existing Home layout | Add width without moving card content |

Safe practice and pending verification: run the existing card tests with isolated fixtures at320/390/600/844dp and320dp/2× text. Verify the image fills card width at4:3, category/name start below it, reviews and location remain inside opposite image corners, View Details still invokes the existing callback, and no overflow is raised. Use the four-file format/analyze and six-test-file commands from the sections below, optionally adding `--dart-define=CAPTURE_RESOURCE_CARDS=true` for actual widget captures. Do not treat the old side-by-side captures in scratch as current output or change working records to verify layout.

## Wider cards and bottom-left image location - October 29, 2026

This follow-up implements the user's request to make Facilities/Services cards wider and move the saved location to the image's bottom-left. It supersedes the earlier two-columns-on-every-phone layout and body location row. The review badge stays at the top-left; the 4:3 image, existing data, prices, actions and detail destinations are retained.

### 1. Cause / reason

Confirmed in the shared card source: two columns left only 138dp per card at a 320dp viewport with the existing page padding and gap. Location appeared below the name/information rather than over the image. Home previews used 204dp facility / 196dp service widths. The latest request explicitly asks for more width and a different location position.

| Before | After | Why |
| --- | --- | --- |
| Two narrow columns on all phone widths | Full content width on small screens; two columns only when each card can have at least 240dp | Give text and images meaningful additional width |
| Location in the card body | Saved location at the image's bottom-left, inset 8dp | Put location where the user requested without duplicating it |
| Different narrow Home preview widths | Both facility and service previews start at 260dp, with existing text scaling/viewport clamping | Keep the shared design wider and consistent |

### 2. Exact files changed and current anchors

| File | Current line / code anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/resource_catalog_card.dart` | 10 `ResourceCatalogCard`; 155 `ResourceLocationLabel`; 255 `ResourceCardGrid`, 262 column selection | Move location into the image Stack; add its readable label; choose one/two columns from available width |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 355 `FacilityPreviewCard`, 359 width; 386 `ServicePreviewCard`, 391 width | Default preview widths are now 260dp |
| `campushub/lib/module_app/screens/home_page.dart` | 285 facility strip; 298 service strip | Existing Home strips now allocate 260dp before scaling/clamping |
| `campushub/test/resource_catalog_cards_test.dart` | 107 responsive cases; 177 missing/long location test | Verify actual wider geometry, location coordinates, nonoverlap, missing locations, full tooltip value and original action/image behavior |
| `docs/mobile-services-navigation.md` | 3 this section | Updated explanation, source anchors, checks and exercise |
| `campushub/DESIGN.md` | `resource-catalog-card.content`, `.layout`, `.location` | Record the latest placement and width behavior |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Save the accepted follow-up and verification |

Seven project files: three runtime Dart files, one test file and three existing documentation/context files. The earlier review/price helpers remain in the same shared file at current lines197 (`ResourceReviewBadge`),289 (`facilityCardInformation`) and298 (`serviceCardPrice`). Earlier section line references below are historical snapshots.

### 3. Changes made

The listings now use one full-width card when content width is below492dp. At492dp or above, they use two columns with a12dp gap: `(492 - 12) / 2 = 240dp` minimum per card. With the existing16dp page insets, the viewport breakpoint is approximately524dp. This intentionally updates the previous always-two-column phone layout in response to the latest request. Two-column rows retain equal content-driven height and aligned View Details actions.

Home keeps its horizontal previews and original navigation. Both preview types are now260dp wide before the existing text-scale adjustment and viewport clamp, so narrow screens do not overflow. Marketplace preview widths are unchanged.

The location is shown only for a nonempty saved value. A bottom-left `Positioned` label uses an existing Material location icon, readable white text on a nearly opaque navy surface, and an8dp image inset. It is constrained inside the image, previews up to two lines and preserves the complete text in its tooltip and accessible label. It does not resize the image or duplicate location below it. Names, capacity/service information, rate and View Details continue in the body. No new motion, favorites, assets, styles for unrelated screens or data was introduced.

### 4. How it works: inputs outputs and data flow

```text
Existing API -> existing FacilityItem.location / ServiceItem.facility.location
  -> ResourceCatalogCard
  -> existing image Stack
       top-left: unchanged ResourceReviewBadge
       bottom-left: ResourceLocationLabel(saved location), if nonempty
  -> unchanged card body price and View Details callback

Listing's available width -> ResourceCardGrid LayoutBuilder -> one/two columns
Home preview -> existing horizontal strip -> scaled/clamped 260dp card
```

`ResourceLocationLabel(location)` receives a string and renders a non-editing location overlay; it does not resolve a new campus address, infer a location or call an API. `ResourceCardGrid(children)` now measures its available width before building intrinsic-height rows. The existing row measurement still gives the cards finite height for their footer spacers.

Annotated example from the image Stack:

```dart
Positioned(
  bottom: 8, left: 8, right: 8, // Inset and constrain within the existing image.
  child: Align(
    alignment: Alignment.bottomLeft,
    child: ResourceLocationLabel(location: resource.location), // Saved text only.
  ),
)
```

### 5. Backend / API behavior

Unchanged. No new query, endpoint, request, permission or approval/payment behavior is added. Existing price labels, review validation, real image loading/fallback, detail screens and main navigation remain. The previously documented absence of API review aggregates is unchanged; the card still uses the honest `No reviews yet` fallback rather than fabricated values.

### 6. Database / migration impact

None. This follow-up does not change models, schema, migrations, records, configurations, dependencies or assets. It changes widget placement and sizing only.

### 7. Tests performed

From `campushub/`, formatted and analyzed `resource_catalog_card.dart`, `home_preview_cards.dart`, `home_page.dart` and `resource_catalog_cards_test.dart`. **All four files pass static analysis; final formatting requires no changes.** Ran:

```powershell
flutter test --no-pub --reporter expanded --dart-define=CAPTURE_RESOURCE_CARDS=true test/resource_catalog_cards_test.dart test/services_screen_test.dart test/service_catalog_test.dart test/home_page_test.dart test/seller_home_layout_test.dart test/facility_booking_flow_test.dart
```

**52 tests passed; Flutter reported7seconds.** Responsive cases cover320/390/600/844dp plus320dp at2× text. They assert full-width phone cards, aligned wider-screen rows, preserved4:3 images and top-left reviews, bottom-left location coordinates, separation between overlays, one location occurrence, missing/long location handling,48dp actions and existing detail callbacks. Prior service/catalog/Home/seller/booking regressions remain in the run. Each fixture render starts with a fresh widget tree so retained scroll position does not distort the capture.

Actual widget viewport captures at320dp/1×,414dp/1× and320dp/2× and the log are under ignored `scratch/facility-service-cards-20261029/`; the latest run is `wider-location-tests.log`. These are Flutter-rendered isolated test fixtures, not live-record screenshots or generated illustrations. The414dp render was visually inspected for full width, location placement/readability, review placement, image ratio, body hierarchy and footer spacing. Native device/emulator testing was not performed.

### 8. Remaining limitations troubleshooting and safe exercise

Long locations intentionally preview at most two lines over the image; the complete saved value remains in the tooltip, screen-reader label and existing Details view. An empty/whitespace location produces no overlay or invented campus fallback. Long descriptions/names and large text can make a scrollable card taller. No application reload, installation, deployment or device action was performed.

If a listing still looks narrow, inspect the available content width and use the existing Flutter reload/rebuild workflow. A phone should now have one card per row; wider layouts use two. On Home, verify the existing horizontal strip rather than expecting a full listing. If location is missing, inspect the actual record's `location` field before changing the widget.

Safe practice: in the isolated card test, compare320dp and600dp widths, then set a fixture location to whitespace and verify the overlay disappears. Restore a long fixture location, verify the two-line preview stays above the image's bottom inset and does not touch the rating, and inspect the tooltip's full text. Run the targeted tests without writing records, changing API fields or replacing photos.

## Facilities and Services cards with image review overlays - October 29, 2026

This section supersedes the earlier single-column service tiles, horizontal facility list cards and status rows on Home preview cards. It changes the existing Flutter application directly. No AI images, replacement photos or static mockups were created. The user's attached reference supplies the card hierarchy; its example names, ratings and prices are not application records.

### 1. Cause / reason

Confirmed by source inspection: Facilities used horizontal cards with a colored status pill and an inline rating. Services used icon/text tiles without the shared image treatment. Home had separate preview layouts, including a facility status row. `FacilityItem` discarded the API's already-formatted `price_label` / `price_compact_label`, which could lose base-duration or per-person/night wording when it rebuilt a label from the raw rate.

The user requested matching compact cards, a rating/review badge at the image's top-left, actual content and correct billing labels, two-column listings and existing detail navigation. No approval, billing calculation, request workflow or data ownership changes were requested.

| Before | After | Why |
| --- | --- | --- |
| Different facility, service and Home card layouts | One `ResourceCatalogCard` with thin border, white surface and existing bundled Inter | Keep the information hierarchy consistent |
| Inline/missing reviews | Small navy badge, gold star and readable white text, 8dp from the image's top-left | Review information stays attached to the image |
| Fixed image height or icon-only tile | Existing `ProductImage` inside a 4:3 `AspectRatio` and `Stack` | Preserve loading/fallback behavior without displacing the image |
| Single-column listing and status-heavy card | Two columns with natural, equal row height; category/name/information/location/rate/action | Support scanning without guessed heights or internal dividers |
| Client reconstructed all rental price labels | Prefer the existing server-formatted label; retain the legacy fallback | Preserve the configured billing basis |

### 2. Exact files changed and current anchors

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/resource_catalog_card.dart` | 10 `ResourceCatalogCard`; 149 `ResourceReviewBadge`; 207 `ResourceCardGrid`; 235 `facilityCardInformation`; 244 `serviceCardPrice` | New shared image/body/footer, validated review display, equal-height rows and read-only presentation helpers |
| `campushub/lib/module_app/models/facility_item.dart` | 32 constructor default; 89 JSON parsing; 120 `catalogPriceLabel`; 128 `priceLabel` | Backward-compatible optional display label from existing response fields; existing IDs, rates, booking fields and constructor arguments remain |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 355 `FacilityPreviewCard`; 386 `ServicePreviewCard` | Existing wrappers now render the shared card and retain their detail destinations; optional callback lets listings retain their exact routing |
| `campushub/lib/module_app/screens/facility_screen.dart` | 10 `FacilitiesPage`; 16 `loadFacilities`; 39 loader call; 106 `ResourceCardGrid` | Two-column list; default loader remains `FacilityService.fetchFacilities`; optional injected loader supports isolated verification; My Bookings and detail callback remain |
| `campushub/lib/module_app/screens/services_screen.dart` | 122 `ResourceCardGrid`; 128 `onDetails` | Two-column cards retain the existing detail route name, selected ID, catalog and destination |
| `campushub/test/resource_catalog_cards_test.dart` | 104 responsive cases; 160 review validation; 190 pricing-label test; 213 service prices; 271 facility route; 305/321 images; 345 optional captures | Isolated fixtures verify geometry, data boundaries, semantics, image decoding/fallback and route selection |
| `campushub/test/services_screen_test.dart` | 75/84/106 visible-action handling; 110 existing back arrow | Scroll and settle before tapping taller cards/sheets; use the actual custom booking-header back control instead of the outdated generic BackButton finder |
| `docs/mobile-services-navigation.md` | 3 this section | Current explanation, checks, troubleshooting and practice exercise |
| `campushub/DESIGN.md` | `components.resource-catalog-card` and current card scope | Record the shared card specification and scoped star color |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Preserve accepted behavior and verification record |

Ten project files: five runtime Dart files, two test files and three existing documentation/context files. Temporary backups, logs and actual widget render captures are under ignored `scratch/facility-service-cards-20261029/`. Marketplace product card code, bottom navigation, assets, manifests and dependencies were not changed.

### 3. Changes made / expected UI

- Both listing pages render two cards per row. Each pair measures its content before layout; titles, capacity, location and billing labels wrap rather than overflowing a fixed-height tile. Cards in the same row have equal height, with View Details aligned at the bottom. An odd final card retains half-row width.
- The image remains 4:3. A `Stack` positions the compact badge over the image instead of inserting another row or changing its size. Existing resolved URLs, actual image decoding and icon fallbacks use `ProductImage`.
- Facility content is category, name, configured capacity label (or positive capacity in pax), optional saved location, configured rate and View Details. Service content uses its category, name, saved description, optional location, configured price and the same action. Card-level availability/status pills are removed; detail-screen status and booking validation remain unchanged.
- The badge displays a one-decimal average and count only when both existing fields contain a finite rating in 1–5 and a positive integer review count. Missing counts, zero/invalid scores and booking counts cannot produce a rated badge. The empty label is `No reviews yet`. Screen readers receive the full rating/count explanation.
- Cards use navy `#1A1851`, white, the existing border/secondary text and scoped Inter. The star uses the explicitly requested `#FCB316`; the app-wide mobile gold `#FCB315` is unchanged. There are no internal divider lines, gradients, animated entrances or heavy shadows. View Details has at least a 48dp target and native pressed/focus behavior.
- No new favorite feature was added. The old listing/preview cards had no favorite action to preserve; the existing local favorite behavior inside Facility Details is untouched.
- Home's existing horizontal preview strips keep their placement, scrolling and See All actions. They now use the same card design. The listings use the requested two-column layout; Home was not converted into another full listing. Marketplace, seller KPIs/bundles, main navigation and unrelated screens keep their existing design and behavior.

### 4. Functions inputs outputs and data flow

```text
Existing Django facility serializer / public services catalog
  -> existing FacilityService or ServiceCatalog GET
  -> existing FacilityItem / ServiceItem
       FacilityItem additionally retains the supplied formatted price label
  -> FacilityPreviewCard / ServicePreviewCard
       category, capacity or saved description, location, price and detail callback
  -> ResourceCardGrid (listing) / existing intrinsic Home preview row
  -> ResourceCatalogCard
       4:3 ProductImage + ResourceReviewBadge + text + bottom View Details
  -> original FacilityDetailsScreen / ServiceDetailsScreen
```

`ResourceCatalogCard` receives a resource, category, optional information, formatted price and callback. It outputs presentation only; it cannot create a booking, charge a client or approve a request. `ResourceReviewBadge` reads `resource.rating` and `resource.reviews`; it does not query or reinterpret booking totals. `ResourceCardGrid` measures each pair with `IntrinsicHeight` and stretches its `Row`; that finite height lets each card's spacer keep actions aligned. Use the grid or the existing bounded Home preview row rather than putting a flex card directly into an unbounded vertical list.

`facilityCardInformation` prefers the actual backend capacity label, including configured rooms/occupancy wording. `serviceCardPrice` reads existing catalog information. For laboratory prices, it compares only numeric configured analysis entries using the same `sample` or `analysis` billing unit. It displays `From` only when compatible amounts differ. A single/equal price has no `From`; mixed units retain the configured Pricing label rather than being compared. Non-laboratory services keep their actual configured Pricing/display label. Missing prices say to contact the office; the helper invents no fee, discount, eligibility or analysis type.

Annotated read-only example:

```dart
final facility = FacilityItem.fromJson(responseRow); // Existing API record.
final label = facility.priceLabel; // Supplied compact/full label, else legacy fallback.
// The card displays label; raw rate and booking calculations are not rewritten.
```

### 5. Backend / API behavior and review integration gap

No endpoint, serializer, permission, aggregation or booking/payment rule changed. The default Facilities loader still reads `/api/facilities/?resource_type=facility`; Services still uses the existing public catalog/detail endpoints and active-service filtering. Service cards open the existing information/guidance flow, not a new online submission or physical reservation workflow.

Confirmed limitation: `backend/core/api/views.py:1488` (`serialize_facility`) supplies rental labels but no rating/review aggregate. `backend/core/modules/facilities/mobile_services.py:20` (`serialize_service`) also does not publish review aggregates in its allowlist. An existing unmanaged `FacilityFeedback` model is not proof of a complete mobile review-submission, completed-booking verification or service-review integration. The UI therefore normally receives no aggregates and displays `No reviews yet`; that fallback is not an assertion that the database has been audited and contains zero feedback. Numeric review display is verified with isolated fixtures only. Supplying verified real aggregates requires a separate backend integration; no fake aggregate or model was created here.

### 6. Database / migration impact

None. No Django model/table, migration, working record, price configuration, permission or stored review was changed. The existing Flutter model retains all old fields and constructor behavior while optionally carrying a display string the API already sends. No live database connection, booking, review submission, deployment, app installation or device operation was needed.

### 7. Tests performed and visual evidence

Final commands, run from `campushub/`:

```powershell
dart format --output=none --set-exit-if-changed lib/module_app/widgets/facilities/resource_catalog_card.dart lib/module_app/models/facility_item.dart lib/module_app/widgets/home/home_preview_cards.dart lib/module_app/screens/facility_screen.dart lib/module_app/screens/services_screen.dart test/resource_catalog_cards_test.dart test/services_screen_test.dart
dart analyze lib/module_app/widgets/facilities/resource_catalog_card.dart lib/module_app/models/facility_item.dart lib/module_app/widgets/home/home_preview_cards.dart lib/module_app/screens/facility_screen.dart lib/module_app/screens/services_screen.dart test/resource_catalog_cards_test.dart test/services_screen_test.dart
flutter test --no-pub --reporter expanded test/resource_catalog_cards_test.dart test/services_screen_test.dart test/service_catalog_test.dart test/home_page_test.dart test/seller_home_layout_test.dart test/facility_booking_flow_test.dart
```

Results: **7 Dart files formatted, 0 changes required; static analysis: No issues found; 50 tests passed in the final run (5 seconds reported by Flutter).** Tests cover two columns at 320/390/844dp, 2× text at 320dp, equal row/action alignment, 4:3 images, overlay position, valid/missing/invalid reviews, booking-count rejection, semantic rating text, compatible/mixed-unit service prices, canonical rental labels, image failure fallback and actual image decoding from an existing bundled asset. Existing Home/search/tab state, service detail/guidance and booking conflict/form regressions also pass.

Actual `RenderRepaintBoundary` captures were produced by the new optional test with `--dart-define=CAPTURE_RESOURCE_CARDS=true`, at 320dp/1×, 414dp/1× and 320dp/2×. They are Flutter widget output with isolated fixtures, not generated mockups or screenshots of working records. Load Inter and MaterialIcons for the capture so test-font boxes are not mistaken for app icons. Source/layout inspection and representative rendered views check badge placement, glyphs, information order, wrapping, borders/spacing and footer alignment. A viewport capture may show only part of a long scrollable page; scrolling is tested separately. These captures are not a physical-device or emulator acceptance test.

Early failures are retained in scratch logs: off-screen taps needed a layout frame after `ensureVisible`, the generic back finder did not match the existing custom arrow, the semantics check needed to inspect the merged accessible label, and a route-only fixture initially mounted the authenticated slot loader. The final tests fix their harness/targets without bypassing runtime permissions, removing flow assertions or changing the booking implementation. The facility route test inspects the real selected destination before mounting its network loader; booking flow tests retain their isolated service fixtures.

### 8. Remaining limitations troubleshooting and safe practice

- Review aggregation/verified review submission is the missing integration described above. Do not substitute booking counts or hardcoded scores to make the badge look populated.
- Native device/emulator behavior and live records were not exercised. Use the user's ordinary Flutter workflow to inspect the real account and catalogs; no automatic hot reload, restart or device installation was performed.
- Full saved names/locations wrap, so unusually long content or large text can make a pair taller. This preserves readable content rather than truncating it into a guessed height. Each row shares its maximum height; an absent description/location can leave natural alignment space.
- When the price looks wrong, compare the API's existing compact/full label and service `information` first. Mixed billing units and absent rates must not be collapsed into an invented cheapest fee. The legacy rate fallback remains for older payloads without formatted labels.
- If the badge is empty despite stored feedback, inspect what the API actually returns. Missing mobile aggregates are not fixed by adding default values in a widget. Image failures retain the existing icon fallback and badge placement.

Safe exercise: change only an isolated fixture in `test/resource_catalog_cards_test.dart`. First remove `reviews` while retaining `rating` and `booking_count`; run the review test and verify `No reviews yet`. Then supply both valid fixture fields and verify the rating/count and semantic label. Finally run the 320dp/2× case and verify equal action alignment and no rendering exception. Do not edit a live rating, seed records, change an API, apply migrations or replace production image assets for this exercise.

Updated October19,2026. Regular-user navigation remains Home | Marketplace | Services | Facilities | Profile. Approved sellers retain their existing Add Product center action.

## Banner swipe, centered dots and compact gradient action - October 19, 2026

This follow-up supersedes the earlier visible Previous/Next/Pause controls and IndexedStack described below. The user's explicit request permits a gradient on this banner button; the photograph retains its solid navy tint.

### 1. Cause / reason

The user requested centered dots instead of arrows/playback controls, a real automatic swipe, a slightly taller photo and a smaller button at the lower left with a smooth gradient. The earlier implementation changed IndexedStack pages instantly and displayed a count plus three icon buttons.

### 2. Exact files, current lines and anchors

| File | Current line / anchor | What changed |
|---|---|---|
| `campushub/lib/module_app/widgets/home/campus_home_banners.dart` |49 `_slideDuration`,61 `_buttonGradient`,104 `_schedule`,134 `_move`,159 `_bannerHeight`,187 `_action`,292 `PageView.builder`,302 indicator Semantics | Native horizontal swipe, centered dots, stable taller layout and compact lower-left gradient button. |
| `campushub/test/campus_home_banners_test.dart` |47 rotation test,57 banner/button bounds,82 fractional page position,101 lifecycle/actions test,151 narrow/large-text cases | Verify a real animated transition, looping, dots, button position, retained48dp hit area, manual swipes, accessibility pause, lifecycle and destinations. |
| `campushub/test/dashboard_search_appbar_test.dart` |27 `final tabs` | Select the outer PageView in the existing test; the nested banner may swipe while bottom-navigation tabs retain NeverScrollableScrollPhysics. |
| `docs/mobile-services-navigation.md`, `campushub/DESIGN.md`, `CAMPUSHUB_CONTEXT.md` |this section / campus-home-banner / latest entry | Record current presentation, functions/data flow, user-authorized gradient exception, checks and safe practice. |

The photo, banner wording, Home placement, seller KPI/filter logic, backend and API are unchanged.

### 3. Changes made / expected UI

The photo now slides horizontally every five seconds using a450ms easeInOutCubic transition. Three small dots stay centered beneath it, with the current dot gold and outlined in navy. Remove the visible counter, arrow buttons and Play/Pause buttons. Users can also swipe just the banner. The button is anchored at the lower left: its gold-to-soft-gold background is visually34dp tall, with readable navy12sp text and a full48dp touch area. This uses only the existing gold/white/navy palette. Reserve24dp additional photo space and a minimum188dp card height, growing for larger text. No extra shadows or decorative panels.

### 4. Functions, inputs/outputs and data flow

The same `CampusHomeBanners` inputs remain the three tab callbacks and `active`. `_schedule()` owns the existing five-second timer. It now calls `_move(1)`, which animates the dedicated PageController to the next physical page. `onPageChanged` updates `_page`; `_page % 3` identifies the visible copy and dot. The builder starts at a multiple of three, lazily constructing nearby pages so forward looping and backward manual swipes work without reversing the last-to-first animation. Example: five seconds -> swipe Marketplace to Facilities -> second dot selected -> View Facilities calls the unchanged Home callback for tab3.

`_bannerHeight(context, width)` measures the longest slide text with the current Poppins style/text scaler, reserving padding, button target and extra photo space. Each page uses Spacer above `_action(index)` so the button stays at the same lower-left position across different messages. `_action` paints a small gradient plate behind an existing semantic TextButton; the entire48dp button remains tappable. The background image is still the same local asset and decoded-width limit.

Manual drag cancels the timer until scrolling ends, then starts a fresh interval. Background/inactive Home, focus, hover, covering routes and reduced motion retain their existing pause behavior. Reduced motion also uses an instant manual page change for accessibility actions. The passive dots expose current/next/previous values and a screen-reader Pause/Resume action without adding visible playback buttons. `dispose()` releases the PageController, timer and lifecycle observer.

### 5. Backend / API behavior

Unchanged. The three buttons reuse the existing Marketplace/Facilities/Services tab callbacks. No additional requests, product records, sales calculations, seller permissions or catalog behavior.

### 6. Database / migration / running app

No migration, model, dependency or asset change. No app/phone/backend/worker launch, reload, restart, APK build or installation was performed; the user retains control of Ctrl+F5.

### 7. Verification results

All22 focused Flutter tests passed:9 in campus_home_banners_test/home_page_test and13 in dashboard_search_appbar_test/seller_home_entry_test. Three-file analysis returned No issues found; formatting passed. The tests confirm movement through a fractional PageController position halfway through the transition, looping, dot alignment/selection, lower-left button geometry,48dp target, manual swipe destinations, reduced motion, lifecycle,320dp at1x/2x, existing Home dark/landscape cases and retained regular tabs/search/seller approval behavior. The first verification exposed a missing explicit semantics import and Flutter's requirement for next/previous values on adjustable controls; both were corrected before the passing run. No backend tests rerun for this presentation-only follow-up.

Native production-widget previews inspected: `scratch/mobile-home-banners/swipe-dots/banner-320-1.0.png`, `banner-320-2.0.png`, `shared-home-seller-sections.png`. Checked centered dots, exact photo crop, readable text wrapping, compact gradient/button alignment and clearance from header/bottom navigation. The data in the full-Home preview is isolated fixture data. Existing peso-font fallback in the test renderer is outside this change. Verification commands: `flutter analyze --no-pub lib/module_app/widgets/home/campus_home_banners.dart test/campus_home_banners_test.dart test/dashboard_search_appbar_test.dart`; `flutter test --no-pub test/campus_home_banners_test.dart test/home_page_test.dart`; `flutter test --no-pub test/dashboard_search_appbar_test.dart test/seller_home_entry_test.dart`. There is no browser URL: this is native Flutter widget rendering, preserving the user's instruction not to run/restart the app.

### 8. Troubleshooting, limitations and safe practice

No new physical-phone/browser run or platform screen-reader test. Dots are position indicators, with manual navigation available through swiping and accessibility actions. Automatic rotation intentionally stops under reduced motion or when Home is inactive. The local Flutter skill searches returned no verified animation-specific match; the implementation uses native PageView and existing app tokens as the fallback, tested directly.

Safe exercise: from `campushub`, run `flutter test --no-pub test/campus_home_banners_test.dart test/dashboard_search_appbar_test.dart`. Confirm the first banner stays for four seconds, begins sliding at five, reaches the second dot, and loops after the third. Manually swipe the banner and confirm the regular selected bottom tab remains Home. To learn animation timing, temporarily change `_slideDuration`450ms to600ms, inspect the transition, then restore450ms and rerun the tests. Do not change the five-second timer or launch the user's running app to perform the isolated tests; mocks/callbacks write no live records.

## Campus photo banners below Welcome - October 19, 2026

### 1. Cause / reason

The user supplied the USTP Oroquieta Campus Entrance photo and three exact promotional messages, asking for banners below Welcome that switch every five seconds. Inspection confirmed that Home already receives working callbacks for Marketplace, Facilities and Services; no new route, catalog API or fabricated listing is needed. The associated visible Daily/Weekly/Monthly sales selector is documented in the newest section of `docs/mobile-seller-application.md`.

### 2. Exact files, current lines and anchors

| File | Current line / anchor | Change / reason |
|---|---|---|
| `campushub/lib/module_app/widgets/home/campus_home_banners.dart` |10 `CampusHomeBanners`,28 `_slides`,78 `_schedule`,90 five-second timer,134 white Material,160 `IndexedStack` | One reusable banner widget containing the requested copy, supplied photo, existing tab callbacks, controls and lifecycle handling. |
| `campushub/lib/module_app/screens/home_page.dart` |35 `active`,214 `CampusHomeBanners` | Insert directly after Welcome, before seller sections and the normal catalogs. Pass the existing three navigation callbacks. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` |438 `active: _currentIndex == 0` | Tell the existing Home when its bottom tab is visible, so hidden Home does not rotate. |
| `campushub/assets/img/ustp_oroquieta_entrance.png` |Bundled photo | Copy the supplied `Downloads/USTP Oroquieta Campus Entrance.png` unchanged. File hashes match. Existing pubspec assets/img directory registration includes it. |
| `campushub/test/campus_home_banners_test.dart` |47 rotation,72 pause/lifecycle/actions,106 narrow/large-text layout | New meaningful timer/lifecycle/action/reduced-motion checks and optional rendered previews. |
| `campushub/test/home_page_test.dart` |56 banner-placement assertion | Existing Home tests now verify the banner is below Welcome, retaining catalog loads/search/error states. |
| `campushub/test/seller_home_entry_test.dart` |`workspace`, approved-Home renderer | Mock the requested period correctly; load actual Poppins/Iconsax fonts and precache the banner photo for the existing full-Home preview. |
| `docs/mobile-services-navigation.md`, `campushub/DESIGN.md`, `CAMPUSHUB_CONTEXT.md` |this section / component specification / latest entry | Record implementation, design, verification and safe practice. |

Other changed selector/backend files are listed in `docs/mobile-seller-application.md`; no unrelated sidebar or product-form source was changed.

### 3. Changes made / expected UI

All Home users see the three banners in order: Shop on Campus / Browse Products; Explore Campus Facilities / View Facilities; Campus Services Made Easy / View Services. The descriptions are exactly those provided by the user. Each uses the same real campus photograph with a solid navy tint, white Poppins text and a gold button; no gradient or stock image. Below the photo are the current slide count, Previous, Next and Pause/Play controls. Approved sellers still see Sales Overview beneath the banners and retain their normal navigation/catalogs.

### 4. Functions, inputs/outputs and data flow

`CampusHomeBanners` takes `onMarketplace`, `onFacilities`, `onServices` and `active`, and returns the banner/control UI. `_slides` stores only the user-authored promotional copy, not products, availability, sales or recommendations. `_open(index)` calls the corresponding existing Home callback. Example: Browse Products -> Home.onMarketplace -> DashboardScreen._goToTab(1); Facilities uses tab3 and Services tab2. Existing seller Add Product navigation remains separate.

`_schedule()` cancels any previous timer, then starts one five-second periodic timer when allowed. It pauses for inactive Home, background lifecycle, keyboard focus, pointer hover, a covering route, disabled ticker or reduced-motion preference. Each tick skips content changes when the banner is outside the screen. `_move(step)` provides manual wraparound and resets the interval; Pause/Play controls explicit playback. `dispose()` cancels the timer and removes the lifecycle observer. The IndexedStack sizes to the tallest slide, avoiding vertical jumps and allowing larger text to grow naturally. The photo is a local asset decoded at a bounded1280px width, not fetched from the network. Its neutral fallback retains readable copy/actions if loading fails.

### 5. Backend / API behavior

Banners call no new API and write no records. They open the existing catalog tabs, whose existing real-data eligibility, permissions and loading/errors remain authoritative. This is promotional navigation, not a claim that a particular product, service or reservation slot is available.

### 6. Database / migration / running app

No migration, model, package or pubspec change. The supplied photo is the only new production asset. No phone/app/backend/worker launch, reload, restart, APK build or installation was performed; the user retains control of Ctrl+F5.

### 7. Verification results

Nine-file scoped Flutter analysis returned No issues found. All37 focused tests passed across campus_home_banners_test, home_page_test, seller_workspace_test, seller_home_entry_test, dashboard_header_test and dashboard_search_appbar_test. Coverage includes exact five-second cycling/wraparound, stable height, pause/resume, background/inactive Home, three callback destinations, reduced motion,320dp at1x/2x, placement below Welcome, retained authentication/seller gates/search/tab state. All23 isolated Django seller tests also passed; see the sales-selector guide for Philippine midnight/week/month boundaries. A final explicit white Material surface keeps the control row readable under dark device settings and the banner button minimum is48dp; all9 affected banner/Home tests passed again and final banner analysis was clean.

Visual review: `scratch/mobile-home-banners/banner-320-1.0.png`, `banner-320-2.0.png` and `shared-home-seller-sections.png`. The final full-Home render preloads actual fonts/photo; the first capture lacked that test preparation. Initial analysis/test compilation also exposed a test-only ResizeImage getter typo and three source lint findings; these were corrected before the final clean run. Fixture names/sales remain test-only. The existing renderer's peso fallback glyph is outside this banner change; no live monetary values were changed.

### 8. Troubleshooting / limitations / safe learning exercise

No new physical-phone test. With reduced motion enabled, banners stay manual; this is intentional. A paused or hidden banner also does not auto-advance. If the photo is missing, verify its exact asset path and existing assets/img registration; the original photo remains in Downloads. Do not change catalog APIs to fix an asset issue.

Safe exercise: from `campushub`, run `flutter test --no-pub test/campus_home_banners_test.dart`. Verify slide1 persists for four seconds, changes at five, reaches slide3 then loops; Pause stops it, and all three buttons call the expected tab callbacks. To learn the timing, temporarily change the timer from five to six seconds, observe the timing test fail, then restore five and rerun. These tests use callbacks/fixtures and create no live records. When ready to inspect the running source, confirm the same banners appear between Welcome and Sales Overview without changing the regular bottom navigation.

## Header Search and Notifications swapped - October 19, 2026

1. **Cause / reason:** the user requested swapping the two existing header icons. The previous order was Notifications then Search.
2. **Exact files / current anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:235,298` `HeaderSearchButton` in Messages/shared header; `campushub/lib/module_app/screens/seller_dashboard_page.dart:286` seller-header `HeaderSearchButton`; `campushub/test/dashboard_header_test.dart:110` `searchButton` geometry; `campushub/test/seller_workspace_test.dart:305` header order assertion; this guide and `CAMPUSHUB_CONTEXT.md` latest note.
3. **Changes made:** place Search first and Notifications at the far right in all three existing headers. Keep their current icons, tooltips, sizes, white/SugarPie styling and actions.
4. **How it works:** reorder existing children in the header Row and AppBar.actions lists. Inputs are the same `_openSearch`, `_openNotifications` and seller callbacks; outputs remain the existing Search route and notification panel. Example: tapping the left action opens Search; tapping the right bell opens Notifications. No new state, routes or copied handlers.
5. **Backend / API behavior:** unchanged; existing search/catalog and notification flows remain.
6. **Database / migration impact:** none. No app/device launch, reload, restart, build or installation performed.
7. **Tests performed:** five-file analysis clean; all26 tests in dashboard_header_test, seller_workspace_test and seller_home_entry_test passed, including updated responsive non-overlap/order and existing action callbacks. Seller375dp fixture preview visually confirms Search left of Notifications. The associated Sales Overview filter follow-up is documented in mobile-seller-application.md.
8. **Troubleshooting / limitations / safe practice:** hot reload when ready if the old order remains. No native phone check for this source-only swap. Run `flutter test --no-pub test/dashboard_header_test.dart`; verify the brand ends before Search, Search ends before the bell and the bell retains its48dp target at320dp/2x text. This uses fixtures and writes no records.

## Search replaces the header profile action — October19,2026

This supersedes the historical below-greeting Search placement described later in this guide.

### 1. Cause / reason

The user requested removing Profile from the shared mobile header and moving Search into that position. Before this change, the shared Home, Messages and seller-tool headers used HeaderProfileButton, while the read-only catalog search entry lived below the Home greeting. Removing the header avatar also needed to preserve sellers' existing access to their personal profile.

### 2. Exact files, current lines and nearby anchors

| File | Line / anchor | What changed and why |
|---|---|---|
| `campushub/lib/module_app/widgets/navigation/header_search_button.dart` |8 `HeaderSearchButton` | Shared compact Iconsax Search action with a48dp minimum touch target, navy icon and Search tooltip; default opens the existing SearchPage. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` |69 `_homeKey`,160 `_openSearch`,213 `onSearch`,240 and307 `HeaderSearchButton`,337 drawer `onProfile`,437 keyed HomePage | Replace header Profile in the regular shell and Messages; connect seller tools to the same Search handler; keep cached catalog reuse and a working fallback before Home is mounted. Drawer avatar opens the existing Profile tab. |
| `campushub/lib/module_app/screens/home_page.dart` |48 `HomePageState`,108 `openSearch`,194 `home-scroll` | Expose the existing cached Search navigation to the shell and remove the search TextField below the greeting. Catalog loaders, previews, refresh, sorting and error states remain. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` |27 `onSearch`,139 `_openProfile`,254 drawer `onProfile`,288 `HeaderSearchButton` | Seller-tool header uses Search, retains white SugarPie branding and bell, and moves the existing profile callback to the drawer avatar. |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` |65 `onProfile`,193 avatar IconButton | Existing identity avatar becomes a56dp Profile action; no new menu row or duplicate Profile screen. |
| `campushub/test/dashboard_header_test.dart` |15 responsive cases,99 Search expectations | Header geometry, no header Profile, five widths/scales and optional headless captures with bundled Poppins/SugarPie/Iconsax fonts. |
| `campushub/test/dashboard_search_appbar_test.dart` |55 header Search tap,104 direct-tab regression | Existing tab/drawer/search return test updated; new regression checks Search before Home has been visited. |
| `campushub/test/home_page_test.dart` |19 section layout,121 cached openSearch | Verify no duplicate Home input while retaining sections/data and cached Search/autofocus/query/Back behavior. |
| `campushub/test/home_card_background_test.dart` |29 removed search assertion | Keep the existing surface test aligned with the new location. |
| `campushub/test/seller_workspace_test.dart` |285 `onSearch`,310 Search tap,372 persistent header,699 and755 drawer-avatar visibility | Preserve seller sections, header callbacks, drawer Profile return, center Add Product and retained regular Home navigation. |
| `docs/mobile-services-navigation.md`, `CAMPUSHUB_CONTEXT.md` |this section / latest header entry | Record current behavior, functions/data flow, verification and limitations. |

### 3. Changes made / expected behavior

The white shared header is now menu/back, the existing CampusHub SugarPie wordmark, a compact outlined Search icon, and Notifications at the far right (latest icon-swap follow-up). The header Profile avatar is removed from the regular shell, seller tools and Messages. The search input below the Home welcome is removed, making the catalog/seller content begin sooner. Tapping Search opens the current dedicated Search page with its full input automatically focused. Navy/gold#FCB315/white styling, labels, notifications, bottom navigation and seller data remain intact.

Profile stays reachable: regular users retain the Profile bottom tab and drawer entry; approved sellers tap their existing seller-drawer avatar. Its current identity information and menu structure remain. This reuses the existing root Profile page rather than introducing another account screen.

### 4. How it works / functions, inputs and outputs

`HeaderSearchButton(onPressed?)` renders a native IconButton. With a supplied callback it delegates to the shell; without one, a standalone seller page pushes the existing SearchPage. It owns no query state and makes no API call itself. Its tooltip supplies an accessible name; touch bounds stay at least48dp even though the icon is smaller.

`_DashboardScreenState._openSearch()` checks the keyed HomePageState. If Home is mounted, `HomePageState.openSearch()` passes Home's existing products/facilities/services futures and loaders to SearchPage, preserving loaded data and avoiding another catalog read. If a direct launch starts at another retained tab before Home is built, the handler opens the same SearchPage with the shell's existing injected loaders/catalog; the button is never silently inactive.

The seller-tool page receives that same `_openSearch` callback from the root shell. Search is pushed over the current route, so Back returns to the same seller tool/tab. The Messages header uses the same callback. SearchPage still owns its own input, matching, recommendations, filters, loading/errors and detail navigation; none of that business logic was copied into a header.

`SellerDrawer.onProfile` is a navigation callback only. The root closes the drawer and selects its existing tab4. In a seller-tool page, `_openProfile()` closes the drawer and invokes the existing root Profile callback; standalone usage keeps its existing ProfilePage fallback. No sign-out or account/seller status change occurs.

Annotated example: after Home loads products once, tap the header Search and type a matching product name. Search receives the same product future, focuses the current Search input and shows the real matching record. Back returns to Home without replacing its retained state. Starting directly at Services uses the loader fallback and returns to Services after Back. Both paths are covered by isolated fixtures.

### 5. Backend / API behavior

Unchanged. Reuse current ProductService, FacilityService, ServiceCatalog and SearchPage recommendation/search behavior. No endpoint, permission, eligibility, recommendation algorithm, API payload or live record was changed. The injected-loader fallback only supplies existing catalog reads when no Home cache exists yet.

### 6. Database / migration / running app

No migration, dependency or database change. No APK build/install, phone operation, app launch, reload or restart was performed for this header update. The user's Ctrl+F5 session remains under their control; hot reload when ready to view these source changes.

### 7. Tests performed and results

-  Scoped Flutter analysis of five source and five updated test files: No issues found.
- 29 headless tests passed across dashboard_header_test, dashboard_search_appbar_test, home_page_test, home_card_background_test, seller_workspace_test, seller_drawer_test and dashboard_center_add_button_test.
-  Covered header Search/autofocus/query/Back, catalog reuse, Search before Home is mounted, retained tab navigation without swipes, regular five-tab navigation, approved seller Add Product, seller drawer Profile, unchanged shell and approval checks.
-  Header renders exercised320/375/390/844dp widths and2x text; Home also covers landscape and dark theme; seller tests cover320dp/landscape at2x text. Optional captured PNGs are in scratch/mobile-header-search. The375dp and320dp/2x header previews were visually inspected with bundled fonts. Images and product records in captures are isolated test fixtures, not live dashboard values.
-  The first run had25 passes and one failure while an existing Add Product heading changed during concurrent edits. Current files were preserved; the rerun against the current Information heading passed all29. No Add Product production code was changed by this task.

### 8. Troubleshooting, safe practice and limitations

If the old avatar or Home search remains visible, hot reload the current Flutter source when ready and confirm DashboardScreen uses HeaderSearchButton. The compact header control is a search icon; the full search input stays on SearchPage. Native keyboard/device presentation was not rerun for this source-only update. Existing fixture captures can show fallback product images or font glyph differences outside the header; they are not evidence of a new live catalog issue.

Safe exercise: run `flutter test --no-pub test/dashboard_search_appbar_test.dart test/home_page_test.dart` from campushub. Verify that Search works from a directly opened Services tab, auto-focuses the existing input, and Back restores Services. Then test from Home and confirm mocked product call count stays1. To practice icon sizing, temporarily set the header icon size to22 while retaining48dp constraints; verify no overflow at320dp, then restore. These tests use mocks and do not write records.

## Compact Home search and white Search background - October 18, 2026

1. **Cause / reason:** user requested removing the Home filter, a smaller search entry, and white Search/Profile backgrounds. Confirmed sources: Home's52dp search row and `_HomeFilter` controls; Search's explicit #F7F8FC Scaffold; Profile's shared light background token.
2. **Exact files / current anchors:** `campushub/lib/module_app/screens/home_page.dart:105` `_openSearch`,120 `_section`,209 `ConstrainedBox(minHeight: 48)`,224 `isDense`; `campushub/lib/module_app/screens/search_page.dart:332` `backgroundColor: Colors.white`; `campushub/lib/module_app/widgets/profile/profile_widgets.dart:8` `ProfileStyle.background`. Existing tests updated: `test/home_page_test.dart` compact search/all sections, `test/search_page_test.dart` discovery background, `test/profile_page_test.dart` Profile/Personal Information white surfaces. Documentation: this guide, `docs/mobile-profile.md`, `CAMPUSHUB_CONTEXT.md`, `campushub/DESIGN.md` search component and `campushub/.impeccable/design.json` search excerpt.
3. **Changes made:** remove Home-only filter enum/state/modal/button/Reset and conditional section visibility. All real Marketplace/Facilities/Services previews remain visible. Simplify `_section` to its actual loading/error/empty/data states because it no longer filters. Search now has48dp minimum height instead of52, a12sp hint,20dp icon and10dp vertical padding. Keep its pill outline, exact placeholder and below-welcome position. Search and shared Profile page backgrounds are white; Profile behavior is described in its existing guide. Submitted Search result category filters remain supported.
4. **How it works:** `HomePage.build(context)` renders greeting, compact read-only search entry and the three catalog sections. `_openSearch()` still passes the existing catalog futures/loaders to the same dedicated SearchPage. `_section<T>()` takes a title, future, navigation/retry callbacks, empty text and content builder; it returns loading, recoverable error, real empty state or catalog content. Removing the obsolete `matches` input eliminates dead Home-only filtering. SearchPage still matches typed queries and routes to existing details; only its Scaffold surface changed.
5. **Backend / API behavior:** unchanged. No additional calls per keystroke, recommendation algorithm changes, catalog visibility changes, seller/business changes or live writes.
6. **Database / migration impact:** none; no dependencies, migration, rebuilt APK or installation for this follow-up. Hot reload to see the updated source.
7. **Verification:** all31 targeted Home/Search/Profile/header/navigation widget tests passed. Six-file Dart analysis returned No issues found; scoped git diff --check passed. Log: `scratch/mobile-navbar/white-search-profile-tests.log`. Test-only fixtures remain isolated. An initial Profile background assertion expected an explicit Scaffold color, but detail pages inherit it from ProfileTheme; the assertion now checks the effective theme fallback correctly.
8. **Remaining limitations:** no new native screenshot/physical-phone run. Minimum height allows the entry to grow with large text; it is not clipped to48dp. White surfaces retain readable navy/gold content and thin neutral boundaries. This removes Home's filter control, not the Search page's existing result categories.

**Troubleshooting:** if the old button or gray surface persists, hot reload/restart the current Flutter build. Do not edit backend filters or catalog eligibility to change a visual surface. Profile details use `ProfileStyle.background`, not a separate color per page.

**Safe practice exercise:** temporarily change the search hint font from12 to13, preview at normal and2x system text, then restore12. Run `flutter test test/home_page_test.dart test/search_page_test.dart` and verify the same real search route still opens, all Home catalog headings remain and no filter button appears. This exercise does not write database records.

## Welcome text top spacing - October 18, 2026

1. **Cause / reason:** user approved reducing the Home top gap so the welcome sits higher below the shared header.
2. **Exact files / anchors:** `campushub/lib/module_app/screens/home_page.dart:276`, `EdgeInsets.fromLTRB(16, 8, 16, 32)` inside `HomePage.build`; this guide, `CAMPUSHUB_CONTEXT.md` latest note and `campushub/DESIGN.md` Layout paragraph.
3. **Changes made:** reduce only ListView top padding from20 to8 logical pixels; welcome and following Home content move12dp higher. Keep existing horizontal/bottom padding, font, section gaps and search below the welcome.
4. **How it works:** `HomePage.build(context)` receives the existing first name/catalog state and returns the same RefreshIndicator/ListView. `fromLTRB(left, top, right, bottom)` applies the four edge insets; the second input controls the space before the first welcome Text. This is layout only; catalog functions and routes do not change.
5. **Backend / API behavior:** unchanged; no new requests or data writes.
6. **Database / migration impact:** none. Hot reload to see the change; no new APK build or install for this small follow-up.
7. **Tests performed:** `dart analyze lib/module_app/screens/home_page.dart` returned No issues found; scoped `git diff --check` passed. No new tests for this reversible single-value spacing adjustment.
8. **Remaining limitations:** no new device/screenshot verification. If the greeting is scrolled away, return Home to the top before comparing.

**Debugging and safe practice:** if the old gap remains, verify the running source is home_page.dart and hot reload. Temporarily try a top inset of12, observe the welcome move4dp lower, then restore8. Confirm left/right margins and search still match their previous layout; this exercise changes no records.

## Notification bell left inset - October 18, 2026

1. **Cause / reason:** the user requested moving the bell left. The shared header's Expanded brand region previously pushed the button against the normal right padding. Interpreted as a small inset toward the wordmark, preserving the menu and brand order.
2. **Exact files / anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:265`, `SizedBox(width: 12)` immediately after the Notifications IconButton; `campushub/test/dashboard_header_test.dart:84`, `notificationButton`; `CAMPUSHUB_CONTEXT.md` latest note; this guide. DESIGN.md's header description also clarifies the existing Messages location.
3. **Changes made:** add 12 logical pixels of trailing space. The button moves left by 12dp, with its full 48dp target retained; no negative transform or overlap.
4. **How it works:** `_DashboardScreenState.build(context)` lays out menu, Expanded brand, Notifications and the new spacer in a Row. The spacer takes 12dp from the flexible brand region, leaving the button 16dp from the safe content edge (existing 4dp padding plus new 12dp). Pressing the same button still calls `_openNotifications()` and opens the same honest availability notice.
5. **Backend / API behavior:** unchanged; no new requests, data or notification feed.
6. **Database / migration impact:** none. Hot reload shows this layout-only change; no APK rebuild or installation was performed for this follow-up.
7. **Tests performed:** all3 header widget tests passed at320/390dp widths including2x text, and two-file Dart analysis returned No issues found. Log: `scratch/mobile-navbar/notification-inset-tests.log`. The first geometry assertion measured the inner Tooltip instead of the full IconButton; the finder was corrected to validate the actual touch target.
8. **Remaining limitations:** no new native screenshots/device run. This small inset does not move the bell to the far-left menu position. Other tabs share this same header.

**Debugging and safe practice:** if the bell does not move, hot reload the running app and confirm it is using this shared dashboard header. Do not reduce IconButton constraints to move only the artwork. For practice, temporarily change the spacer from12 to16, verify the button shifts4dp without overlap, then restore12 and run `flutter test test/dashboard_header_test.dart`. This modifies no database records.

## Dedicated catalog Search and header actions - October 18, 2026

### 1. Cause / reason

Confirmed: Home previously filtered its previews inline. The project has Navigator/PageController/retained tabs, not GetX, and no standalone catalog Search page or search-query popularity store. Existing TF-IDF recommendations use recorded product interactions but also fall back to general catalog products. That fallback must not be labeled personalized in Search. The latest instruction keeps Search below the greeting; it supersedes the earlier request to put Search in the header. The preceding request to simplify the header and improve the bell is retained: Messages remains accessible in drawer/Profile.

### 2. Exact files and current anchors

| File | Approximate current line and nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/search_page.dart` | 26 `SearchPage`; 73 `initState`; 93 `_submit`; 124 `_catalog`; 247 `_productContent`; 313 `build` | Dedicated Search, autofocus/Back, discovery, suggestions, submitted results and catalog filters; independent loading/errors/Retry. |
| `campushub/lib/module_app/screens/home_page.dart` | 116 `_openSearch`; 298 `home-search` | Read-only search entry below greeting opens Search with the already-loaded futures. Existing Home category filter and preview ordering remain. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 263 `LucideIcons.bell`; 103 `_openMessages` | Refined outlined bell, remove Messages from header only; existing drawer/Profile navigation and notifications behavior remain. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 108 `openMarketplaceProduct`; 150 `MarketplacePreviewCard` | Extract the existing details-navigation/tracking handler for reuse by suggestions; preserve existing cart/favorites/product details. |
| `campushub/lib/module_app/models/product_item.dart` | 27/96/122 `submittedAt` | Parse existing `submitted_at` for chronological recent-product sorting. |
| `campushub/lib/module_app/services/product_service.dart` | 110 `personalizedOnly`; 147 `fetchSearchRecommendations` | Opt into history-only results using existing session and recommendation endpoint. |
| `backend/core/modules/marketplace/services/recommendation.py` | 46 `get_recommended_products`; 106 `if personalized_only` | Optional flag returns no personal results when history/similarity is insufficient, preserving default legacy fallback. Explicit detail-page seed is ignored in this opt-in mode. |
| `backend/core/api/views.py` | 1746 `personalized_only` | Forward opt-in query flag to the same helper; no new endpoint. |
| `backend/core/api/test_search_recommendations.py` | `SearchRecommendationTests` | History/no-history, no-similarity, legacy fallback, opt-in endpoint and eligibility regressions. |
| `campushub/test/search_page_test.dart` | `openSearch`, `captureSearch`, `void main` | Search behavior, independent errors/retry, honest labels, details navigation and responsive layouts. Optional widget PNG capture uses isolated test fixtures only. |
| `campushub/test/home_page_test.dart` | `Home opens focused dedicated search` | Entry placement, autofocus, cached catalog reuse and return to Home; retain loading/filter tests. |
| `campushub/test/dashboard_header_test.dart` | `discovery header` | Updated header expectations and spacing. |
| `campushub/test/dashboard_search_appbar_test.dart` | `drawer routes` | Search entry/return plus retained tab/drawer regressions. |
| `campushub/test/dashboard_center_add_button_test.dart` | `retains Messages` | Messages via drawer, five unchanged tabs and no visible plus. |
| `campushub/DESIGN.md`, `campushub/.impeccable/design.json`, `CAMPUSHUB_CONTEXT.md`, this guide | `Dedicated Search`, `refersTo: search`, latest context note | Record current UI, sources and learning guide. |

### 3. Changes made

- Home retains the exact placeholder **Search products, facilities, services...** below the greeting, in the existing pill outline beside the Home filter. Tapping opens a full page with Back and a focused input.
- Empty input shows qualified **Recommended for You** or honest **Recently Added Products**, then **Explore Available Products**. Cards reuse real image/name/price/seller, favorites and cart behavior. Recent sorting uses saved submission timestamps, not sales. Missing dates sort last; no invented dates.
- Typing replaces discovery with compact query-matching product suggestions (image, name, price). Selecting a suggestion opens existing Product Details. Search all categories or keyboard Search submits the query; All/Products/Facilities/Services chips then filter the submitted results.
- Keep white Home/header, navy and mobile gold; only the requested Search page gets #F7F8FC background. Compact white rows/cards, Montserrat, no gradients/new dependencies.

### 4. Functions, inputs/outputs and data flow

`HomePage._openSearch()` takes the current loaded Product/Facility/Service futures and pushes `MaterialPageRoute(SearchPage(...))`. Search observes them without refetching on entry. For standalone use or Retry, injected loaders default to the existing catalog services. Failures are observed even if a section is hidden, avoiding unhandled asynchronous errors.

`SearchPage.initState()` stores those futures and starts an independent personal-recommendation read. `_matches(value)` compares a trimmed, case-insensitive query against real names and existing category/seller/description/location fields. Typing updates only local state; no HTTP request per character and no new search records. `_submit()` closes the keyboard and switches to result mode. Clearing restores discovery and focus. `_catalog<T>()` renders loading, load failure/Retry or the actual data, with failures independent per catalog.

`ProductService.fetchSearchRecommendations()` loads the current saved account ID and calls the existing `/api/products/recommended/?user_id=<id>&personalized_only=1` flow. The existing helper seeds similarity from the same ProductInteraction history (view/click/purchase). The server acknowledges `personalized_only: true` in its response; if an older server omits that acknowledgment, Flutter rejects the potentially generic list and uses recent products. Search intersects returned IDs with the current public product catalog before displaying cards. If none survive, history is missing, similarity is unavailable, or the existing client returns no recommendations on connection failure, show Recently Added Products. No interest fields, fake recommendations, popularity statistics, synthetic rows or duplicate recommendation algorithm are introduced. This update does not change Apriori bundles or seller dashboards.

`openMarketplaceProduct(context, product)` is the previous card handler moved into one shared function: load current session, record the existing view interaction when IDs exist, then push the existing ProductDetailsScreen with the same saved product fields. FacilityDetailsScreen and ServiceDetailsScreen remain the destinations for their result rows; service-specific guidance stays unchanged.

**Annotated example:** query `cho` checks `name.toLowerCase().contains('cho')` (as well as the existing other searchable product fields). A matching saved product becomes a suggestion, without creating a product. `personalized_only=1` stops before the helper's general popularity/catalog fallback; old callers omit this parameter and keep their original behavior.

### 5. Backend / API behavior

Reuse GET `/api/products/approved/`, GET `/api/facilities/?resource_type=facility`, GET `/api/mobile/services/` and existing GET `/api/products/recommended/`. Products remain subject to server approval/archive/expiry/availability eligibility. The Search page receives only this public catalog; recommended IDs are rejoined to it to exclude stale/unavailable results. Services remain active-only. Physical facilities keep existing catalog visibility/status rules, not invented free-slot promises. No Seller Dashboard, order, inventory, pricing, permission, authentication or transaction writes changed. Existing product view tracking is reused, not duplicated.

### 6. Database / migration impact

No model/schema change or migration. No live records created, edited or deleted by implementation/testing. `submitted_at` already exists in the product response. Restart Django if automatic reload is disabled so it recognizes the optional recommendation flag, and rebuild/restart Flutter to install the new screen. Normal debug APK: `campushub/build/app/outputs/flutter-apk/app-debug.apk` (not automatically installed on the phone).

### 7. Verification and manual testing

- **37 Flutter tests passed** across Search, Home, header, drawer/tab navigation, five-item navbar, ProductItem and Services. **7 Django tests passed** for the opt-in helper/API and existing recommendation endpoint. Initial retry callback failure was corrected with synchronous setState block callbacks; lazy-list checks now scroll before finding offscreen sections. No claim that the first test run passed.
- Targeted **11-file Dart analysis: No issues found**. Normal `flutter build apk --debug --target lib/main.dart` succeeded; Gradle 18.4 seconds. Logs: `scratch/mobile-navbar/search-flutter-tests.log`, `search-django-tests.log`, `search-main-build.log`.
- Three additional screenshot/layout checks passed after the final visual refinements. Layout widget checks cover 375x812, 320x844 at 2x text under dark app theme, 844x390 landscape at 2x text, reduced motion and scrolling. This Search surface intentionally remains light/navy in both theme settings. Optional fixture-only PNGs for discovery/suggestions are saved in `scratch/mobile-search/`; the phone-size discovery/suggestions and 2x-text portrait images were inspected. The initial capture used the square test font; the capture helper now preloads the bundled typeface before building. These are widget renders, not native keyboard screenshots.

Manual checks:

1. Open Home: greeting is above search; no header search. Tap search and confirm Back plus focused input/keyboard. Back returns to unchanged Home/tab state.
2. With a real public catalog, verify images/names/prices/sellers. With no interaction history, verify Recently Added Products and no Popular Searches. With qualifying existing history, verify Recommended for You contains only currently available approved records.
3. Type part of an actual product name: discovery disappears and matching suggestions appear. Tap one and check existing Product Details/cart/favorites behavior.
4. Submit an actual facility/service term using keyboard Search or Search all categories. Switch all four filters and verify real results; open Facility/Service Details. Services retain their own workflow guidance.
5. Try a term absent from the catalogs. Expect explicit no-match text. Disconnect Django and retry a failed catalog; expect error then recovery, while other successful catalogs remain usable. Clear search to restore discovery.
6. Test small phone, landscape, 2x text, keyboard open, screen reader Back/Clear/filters and returning from details. No real purchase/application is needed.

### 8. Limitations, debugging and practice

- Local matching covers the fetched public catalogs. There is no new paginated/server full-text/fuzzy search; large catalogs may eventually need that extension. Existing APIs remain authoritative and are reused.
- Popular Searches is intentionally omitted: no recorded search-popularity source was found. A purchase/interest model was not invented. Personalization uses the existing interaction helper only; missing/ineligible seeds or unavailable similarity produce recent products instead.
- No real phone keyboard/network/personalized-account flow was exercised in this change. Widget fixtures never enter production. Optional widget images do not prove native keyboard behavior.
- If products cannot load, inspect the existing approved-products request/connection and use Retry, not fabricated rows. If personalization is unexpectedly absent, check saved account ID, existing ProductInteraction rows, scikit-learn availability and matching currently public product IDs. If recommendations remain absent against an older server, deploy/reload the updated opt-in backend; the client safely rejects responses without the history-only acknowledgment.

**Safe practice exercise:** add a temporary test-only product with a distinctive name and saved submission timestamp in `search_page_test.dart`, then type part of that name. Verify suggestions contain that record, nonmatches are absent and Clear restores discovery. Restore the fixture and run `flutter test test/search_page_test.dart test/home_page_test.dart`. Do not add demonstration products to the live database.

## Full-width bottom navigation and navy tap feedback - October 18, 2026

This follow-up supersedes the floating geometry and gold feedback described in the earlier reference implementation below.

1. **Cause / reason:** the user requested that the bar fill the bottom, left and right edges and remove the light-yellow click color. Confirmed sources were the outside padding/maximum-width floating wrapper and gold default selection feedback.
2. **Exact files / current anchors:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart:51` (`selectionColor` default), line211 (`splashColor`), line213 (`focusColor`), line343 (`floating-navbar-pill`), line350 (`SafeArea`). `campushub/test/floating_bottom_navbar_test.dart:181` (`pillFinder`) checks edge alignment and line190 checks navy feedback. `campushub/DESIGN.md:68` (`bottom-navigation`), `campushub/.impeccable/design.json` (`refersTo: bottom-navigation`), `CAMPUSHUB_CONTEXT.md:3` and this guide record the current design.
3. **Changes made:** removed outside insets, width cap, rounded floating corners and shadow. The white surface fills the viewport width and bottom safe area, with a thin top separator. Replaced yellow press/focus colors with translucent navy. Kept labels, icons and selection animation.
4. **How it works / data flow:** `build(context)` receives the selected index, items and callback from the existing dashboard. It builds a full-width white Container, then SafeArea around the controls. SafeArea keeps controls above system gestures while the outer white surface reaches the bottom. `_buildNavItem(context, index, item)` derives selected appearance and invokes the existing `onTap(index)` callback. Dashboard changes its existing tab state; no records are fetched by this widget. The existing reduced-motion behavior remains.
5. **Backend / API behavior:** unchanged. No new requests, endpoints, seller data, authentication or permissions.
6. **Database / migration impact:** none. No package installation or migration command is needed. Hot reload should show this widget-only adjustment; use the rebuilt APK for installation.
7. **Tests performed:** all **11** tests passed across `floating_bottom_navbar_test.dart`, `dashboard_center_add_button_test.dart` and `system_navigation_surface_test.dart`. Coverage includes five labels, selection, rapid interrupted animation, reduced motion, safe-area alignment at narrow/wide sizes, navy feedback, hidden plus and dashboard integration. `dart analyze` for the changed widget and test returned **No issues found**. Log: `scratch/mobile-navbar/docked-nav-tests.log`. `flutter build apk --debug --target lib/main.dart` succeeded (Gradle 27.2 seconds); output: `campushub/build/app/outputs/flutter-apk/app-debug.apk`, build log: `scratch/mobile-navbar/docked-main-build.log`. Scoped `git diff --check` reported no whitespace errors.
8. **Remaining limitations:** native device screenshots were not repeated for this small follow-up; the emulator screenshots in the earlier section show the earlier floating geometry. This does not install the APK on the physical phone. The public widget name and existing test key retain `floating` for compatibility, even though the surface is now flush.

**Troubleshooting:** if yellow feedback persists, check whether a caller explicitly supplies `selectionColor`; this change sets the default to navy. If old outer gaps persist after hot reload, restart the app and confirm the current build is installed. Do not change the OS gesture inset to zero: keep controls safely above it.

**Annotated example:** `selectionColor.withValues(alpha: 0.08)` means the navy input color supplies an 8%-opacity tap ripple; it does not change the selected tab or navigation callback. `SafeArea(top: false)` adds device clearance around the controls inside the painted surface.

**Safe practice exercise:** temporarily change ripple opacity from `0.08` to `0.06`, tap several destinations and observe only the feedback change. Restore `0.08`, then run `flutter test test/floating_bottom_navbar_test.dart`; verify all assertions pass and labels/tab order remain unchanged. This exercise changes no backend records.

## Floating navigation reference, refined icons and selection motion - October 18, 2026

1. **Cause / reason:** user supplied a white rounded floating-bar photo and requested refined icons/animation while explicitly preserving every existing label. The prior component was full-width with a top separator and immediate icon swaps. This is a scoped navigation refinement, not a new dashboard or routing system.
2. **Exact files/current anchors:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart:70`, default5Items; line179 `_buildNavItem`; line186 reduced-motion duration; line219 TweenAnimationBuilder; line255 AnimatedDefaultTextStyle; line330 adaptive height; line351 floating-navbar-pill. `campushub/test/floating_bottom_navbar_test.dart`, motion/rapid-interruption, icon pairs, contrast, labels/semantics, inset/width and safe-area assertions. `campushub/DESIGN.md` bottom-navigation component and overview; `campushub/.impeccable/design.json` bottom-navigation label excerpt; this guide and CAMPUSHUB_CONTEXT.md. QA-only `scratch/mobile-navbar/verify_reference_nav.py` exercises the existing `campushub/tool/qa/navbar_preview.dart` on emulator-5554; no application source imports that script/preview.
3. **Changes made:** a white floating surface,24dp reference-specific corner radius,12dp horizontal inset,8dp bottom gap above system safe area,68dp minimum content height and640dp maximum width. One restrained offset shadow replaces the top separator; no border/shadow stacking. Default labels remain exactly Home, Marketplace, Services, Facilities, Profile. Icons use consistent rounded Material outline/filled pairs: home, shopping bag, briefcase, campus building and person. Navy selected icon/text replaces the reference's purple to preserve CampusHub branding; gold remains pressed/focus feedback. No always-visible dot, extra pill or chart icon was added. Legacy reusable center-action code remains dormant and is not enabled on Dashboard.
4. **How it works / functions and data flow:** existing Dashboard currentIndex → FloatingBottomNavbar → _buildNavItem(index,item). onTap(index) still invokes the original parent callback/PageController immediately. The selected state chooses item.effectiveActiveIcon rather than the idle outline. TweenAnimationBuilder animates the icon2dp upward and to1.08x over220ms easeOutCubic; AnimatedSwitcher crossfades glyphs over140ms; label weight/color transitions share the220ms duration. Values retarget from their current position on a rapid tap; there is no idle animation, navigation delay or new animation package. Reduced Motion sets durations to zero and keeps the selected state legible. Outer bounds stay stable while only the icon transforms. Labels retain the existing Material-style noScaling convention, with complete names in scalable tooltips and selected/button semantics; FittedBox prevents a long Marketplace label from turning into an ellipsis on narrow phones.
5. **Backend/API behavior:** none changed. All five destinations, labels, order, tab state, saved session, seller permissions, existing Messages and Services routing remain. No network request or record is created by icon animation. No plus/FAB was restored. No new icon/font dependency; Material is already available and the existing Lucide plus helper is retained for compatibility.
6. **Database / migration / commands:** no migration or backend command. Hot reload can show the source change; install the final normal `campushub/build/app/outputs/flutter-apk/app-debug.apk` to update a separately installed app. Native QA used a copied fixture preview APK only on the emulator; the final standard output was rebuilt from lib/main.dart and is the normal app, not that fixture target. Physical phone app/data/settings were untouched by this navbar task.
7. **Tests / actual evidence:** `flutter test test/floating_bottom_navbar_test.dart test/dashboard_center_add_button_test.dart test/system_navigation_surface_test.dart test/services_screen_test.dart --reporter expanded` passed **19 tests**, log `scratch/mobile-navbar/reference-nav-tests.log`. Checks include exact labels, outline/filled glyphs, navy contrast, one selected accessible destination, instant reduced-motion state,48dp touch height, body clearance,320/390/768px widths, dark host, large text, rapid interrupted selection, Services state retention and dormant center-action compatibility. Two-file targeted Dart analysis reported No issues found. Preview APK build passed; final main.dart APK build passed (23.3s Gradle task), log `reference-main-build.log`. **Nine Pixel10a Android emulator scenes passed:** all five selected destinations, dark Services, dark/2x-text Services, successive Marketplace→Profile taps, and landscape/large Profile. UI Automator verified unchanged labels and exactly one selected clickable destination in each scene. PNG/XML/JSON evidence is in `scratch/mobile-navbar/reference-native/`, with results in verification.json and reference-native-verification.log. Home, dark-large Services and landscape-large Profile images were visually inspected together for shape, spacing, contrast, glyphs, labels, selection and system-bar clearance. A cold-boot System UI busy dialog was dismissed with Wait before the capture batch; it was not an app crash or accepted screenshot. No UI defects were observed in that bounded pass; no further cosmetic iteration/rebuild was performed. The task-started headless emulator was closed afterward, rotation unlocked, and normal app APK output retained.
8. **Remaining limitations / debugging:** the supplied picture is the structural/icon reference, not permission to rename tabs or use purple. Profile/campus records and routes stay existing. Desktop-style animations, decorative artwork, gradients and physics libraries do not belong in this small Operate surface. Icon glyphs are from the included Material family, not a paid external asset set. Current nav labels keep existing native fixed-size behavior while full accessibility names remain. No native iPhone/tablet hardware or live account workflow was tested for this UI-only change. Old app installations require the rebuilt APK. Earlier sections below describe historical navbar appearances and are superseded here.

**Skills and rationale:** ui-ux-pro-max's two narrowly scoped motion searches returned no database matches; motion guidance therefore comes from the supplied Impeccable Android/animate playbooks and existing Flutter primitives, not a claimed search result. Frontend-design-codex and design-taste-frontend preserve-brand guidance informed the compact typography/spacing and restrained state feedback. An existing brand and explicit photo dictated the answer, so no generated image, marketing layout, React dependency or alternate label was introduced.

**Annotated example:** tapping Services still sends index2 to the parent. Its existing page is selected immediately; the briefcase fills/navy label strengthens while the icon travels2dp. Quickly tapping Profile retargets the transitions and ends with only Profile selected. Backend state is not involved.

**Safe learning exercise:** in floating_bottom_navbar_test.dart only, shorten the pump interval in the interrupted-selection test and verify the final selected semantics still match Profile and the bar rectangle stays unchanged. Restore your test edit and rerun the file. Follow currentIndex → isSelected → tween end → Transform in the production source to understand why the bar itself does not jump. Never rename a production tab to mimic the sample photo.

## Preview import diagnostics fix - October 18, 2026

1. **Cause / reason (confirmed):** all seven reported diagnostics were reproduced by running `dart analyze scratch/mobile-home/native_preview.dart`. That temporary preview lived outside the Flutter package, so the analyzer could not find `package:flutter/material.dart` or `package:campushub/...`. Missing runApp, MaterialApp, ThemeData, Color and DashboardScreen were consequences of those unresolved imports. The actual `lib/main.dart` and DashboardScreen analyzed cleanly before this fix; Flutter was installed and the app package configuration already existed. This was not a missing-widget implementation.
2. **Exact files/current lines/anchors:** move `scratch/mobile-home/native_preview.dart` to `campushub/tool/qa/home_preview.dart:2` (Flutter import), line4 (fixture import), line6 (`main`). Move the analogous scratch navbar preview to `campushub/tool/qa/navbar_preview.dart:2`, with `main` at5 and NavbarPreview at7. This guide and CAMPUSHUB_CONTEXT.md record the corrected locations. Older screenshot sections below refer to the locations used at the time of capture; these new paths supersede those paths for future runs.
3. **Changes made:** preserve both QA entry points inside the existing app package, update Home's fixture import to `../../test/home_test_fixtures.dart`, and apply Dart formatting. Keep previews outside production `lib/`. No fake SDK files, duplicate dependency setup or suppressed diagnostics.
4. **How it works / functions, inputs and outputs:** Dart resolves package imports using the containing package's `.dart_tool/package_config.json`, generated from pubspec.yaml. Inside `campushub/tool/qa`, both previews inherit the existing campushub/Flutter dependencies. Home preview `main()` passes isolated HomeTestCatalog/homeProducts/homeFacilities loaders to the real DashboardScreen and runApp displays that widget. Navbar preview `main()` displays NavbarPreview; its local state selects a tab, theme and text scale for QA. These preview inputs are test fixtures/local controls, not live catalog changes. Normal app startup remains `campushub/lib/main.dart`.
5. **Backend / API behavior:** no backend, authenticated workflow or API changes. The relocated files are optional QA launch targets, not new application routes. Existing fixtures/production widgets remain unchanged.
6. **Database / migration impact:** none. No new package or pubspec change; package configuration was already valid. Run normal development from `campushub`. Optional QA commands from that folder are `flutter run -t tool/qa/home_preview.dart` or `flutter run -t tool/qa/navbar_preview.dart`; normal app run is `flutter run -t lib/main.dart`. Do not distribute a preview APK as the normal app.
7. **Verification:** before relocation, the original Home preview produced the exact seven reported errors; normal main/dashboard analysis reported No issues found. After relocation, `dart analyze lib/main.dart lib/module_app/screens/dashboard_screen.dart tool/qa/home_preview.dart tool/qa/navbar_preview.dart` reported **No issues found**. Both relocated files were formatted. No widget tests, APK rebuild, emulator or physical-phone run was performed for this source relocation and import-path correction.
8. **Remaining limits / debugging:** VS Code may retain a diagnostic for a now-moved file until its old editor tab is closed and Dart: Restart Analysis Server is run from the Command Palette. Open the new path or the actual `lib/main.dart`. If unresolved imports occur in production later, check the nearest pubspec and run `C:\flutter\bin\flutter.bat pub get` from `campushub`; do not create a replacement material.dart or change Flutter APIs to silence the errors. This fix does not alter an unrelated SDK installation or global PATH.

**Safe learning exercise:** open `home_preview.dart`, follow `package:flutter/material.dart` to its SDK definition, then follow the fixture import to the existing test data. Compare with `lib/main.dart`, which loads the real session/router. Run `C:\flutter\bin\dart.bat analyze tool/qa/home_preview.dart tool/qa/navbar_preview.dart lib/main.dart` from `campushub`. The expected result is resolved imports and no undefined widget names. Use the existing fixture data only; no database edit is needed.

## 1. Cause / reason and scope

The mobile shell used four PageView pages plus a center Add Product action. Services had an existing Django catalog/editor and service-configured Facility records, but no mobile catalog/detail screen or mobile service request endpoint. The project uses MaterialApp, AppRouter, Navigator and PageController, not GetX routes/controllers, so this change preserves that actual architecture. No GetX dependency or parallel routing system was added.

The user clarified that this update should show service-specific requirements and contact-office guidance rather than build submission workflows. The drawer was already removed in the preceding request; it remains removed. No new Quick Actions are introduced.

## 2. Exact files changed, current lines and code anchors

The following table includes all application and test files changed in this feature. Line numbers refer to the final source at verification time; use the anchor if subsequent edits move them.

| File | Current lines / anchors |
| --- | --- |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 23: `class DashboardScreen`; 79: `void _goToTab`; 340: `ServicesPage(catalog`; 359: `bottomNavigationBar:` |
| `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` | 65: `default5Items =`; 144: `Widget _buildNavItem`; 93: `buildCenterAddButton` |
| `campushub/lib/module_app/widgets/navigation/retained_tab.dart` | 4: `class RetainedTab` |
| `campushub/lib/module_app/routes/app_routes.dart` | 7: `static const String services` |
| `campushub/lib/module_app/routes/app_router.dart` | 24: `AppRoutes.services` |
| `campushub/lib/module_app/models/service_item.dart` | 5: `class ServiceItem` |
| `campushub/lib/module_app/services/service_catalog.dart` | 14: `class ServiceCatalog {`; 24: `Future<Map<String, dynamic>> _get`; 75: `fetchServices`; 83: `fetchService(String` |
| `campushub/lib/module_app/services/facility_service.dart` | 29: `resource_type=facility` |
| `campushub/lib/module_app/screens/services_screen.dart` | 9: `class ServicesPage`; 27: `Future<void> _load`; 48: `Widget build` |
| `campushub/lib/module_app/screens/service_details_screen.dart` | 7: `class ServiceDetailsScreen`; 27: `void _requirements`; 98: `Widget build` |
| `backend/core/modules/facilities/mobile_services.py` | 13: `def active_services`; 20: `def serialize_service`; 85: `def service_list`; 90: `def service_detail` |
| `backend/core/core/urls.py` | 193: `path("api/mobile/services/` |
| `backend/core/api/views.py` | 1470: `def facilities_list` |
| `backend/core/modules/facilities/test_mobile_services.py` | 8: `class MobileServiceCatalogTests` |
| `campushub/test/service_catalog_test.dart` | 9: `void main` |
| `campushub/test/services_screen_test.dart` | 51: `void main` |
| `campushub/test/dashboard_center_add_button_test.dart` | 7: `void main` |
| `campushub/test/dashboard_search_appbar_test.dart` | 8: `void main` |
| `campushub/test/floating_bottom_navbar_test.dart` | 6: `void main` |

Documentation: this guide (`docs/mobile-services-navigation.md`), the current preference in `CAMPUSHUB_CONTEXT.md`, and a follow-up pointer in `docs/sidebar-navigation-white-all.md`.

## 3. Changes made

- Five ordinary, consistently styled Lucide navigation items replace the visible center action. Services uses the briefcase icon and its own selected state at index 2. Facilities moves to index 3 and Profile to index 4; the Home facility shortcut was adjusted to index 3.
- The reusable center-action builder, center-action widget branch and `ProductsScreen.showAddProductSheet` remain. Dashboard no longer supplies the center callback, and its now-unused private callback/import were removed. No visible + or floating replacement exists.
- `RetainedTab` keeps visited screens alive, preserving loaded data, search and scroll state while tabs change. Services also has a PageStorageKey. Reduced-motion settings use immediate tab changes and suppress the nav icon scale animation.
- Services has a search field, active real-record cards, loading, honest empty/search-miss, error/Retry and pull-to-refresh states. Card names, descriptions and categories come from the backend, not the example service names in the request.
- Details reload the selected service before enabling its request action. The page displays actual images, description, office/location, configured rate information, office availability, requirements, terms and applicable laboratory/assessment/lease information. Removed/inactive services have no enabled request action.
- Request Service / Request Assessment / Apply for Lease open different guidance based on the actual configured service workflow. They explicitly state that no request has been submitted. Message Office reuses the existing authenticated Facilities Admin contact/chat path. No generic physical-booking form is used for service intake.
- The Facilities client explicitly requests physical resources via an optional existing-list filter. This stops service resources appearing in the mobile physical-facility list/Home preview without breaking the original unfiltered API response contract.

## 4. Functions, inputs/outputs and data flow

### Navigation

`DashboardScreen(initialTab: 0, serviceCatalog: ...)` accepts an initial tab and an injectable catalog for tests. In production the default catalog reads Django. AppRouter maps `/services` to `DashboardScreen(initialTab: 2)`. `/services/details` identifies the MaterialPageRoute pushed by a service card, with the selected record ID in route settings; it is not a separately implemented deep-link parser. This follows the existing facility detail pattern.

`_goToTab(index)` updates `_currentIndex` and the same PageController. It closes the header search, dismisses keyboard focus and either animates or jumps according to reduced-motion settings. The existing PageView-to-selected-index callback remains. `RetainedTab.build` calls `super.build(context)` with `wantKeepAlive = true`, so leaving a visited page does not destroy its state. The bottom icon is chosen by `currentIndex`, not by a second controller.

```dart
// Index order must agree in the page list and navbar configuration.
// 0 Home, 1 Marketplace, 2 Services, 3 Facilities, 4 Profile
_goToTab(2); // Selects Services without replacing the navigator stack.
```

### Catalog transport and model

`ServiceCatalog._get(path)` sends read-only GET requests using the existing `ApiConfig.serverBaseUrls`. Fallback hosts are attempted concurrently with a four-second timeout per host, so old addresses do not add a long sequential delay. The first valid response wins, updates the working-host cache, and late results cannot replace it. An owned HTTP client is closed; an injected test client remains caller-owned. Invalid/missing JSON and API failures throw rather than fabricate an empty success.

`fetchServices()` returns `Future<List<ServiceItem>>` from the `services` array and excludes non-active rows defensively. `fetchService(id)` returns a freshly validated selected record from the `service` object. `ServiceItem.fromJson` reuses FacilityItem's image URL handling and catalog fields, including multiple images, without sending a service to the normal facility reservation UI. It derives action wording from the stored category or legacy service mode; those are classification labels, not hard-coded service records or prices.

### Django source and public projection

`active_services()` reads the existing Facility model, uses the existing `service_resources_q()` type/mode condition, excludes archives, and requires stored `available` (the service editor's Active status). Laboratory, training/assessment, lease and legacy service modes share that existing classification. `Count('rooms')` supplies the shared serializer's count in the same query, avoiding per-record room queries.

`serialize_service(resource)` reuses `serialize_facility` and existing `service_labels`/`service_pricing_label`, then publishes only allowed catalog fields and customer-facing configured information. Raw workflow JSON, internal notes, staff configuration and inactive analysis rates are excluded. `online_requests_available` is false because this change does not implement intake. Output names, amounts, units and schedules remain recorded values; missing office arrangements use contact-office guidance rather than invented hours.

Data flow:

`Django Facility + configured workflow ? active_services ? serialize_service ? GET JSON ? ServiceCatalog ? ServiceItem ? ServicesPage ? ServiceDetailsScreen ? requirements / Message Office`.

Example: an existing active laboratory with an active saved Moisture rate returns that rate; an inactive rate is omitted. Archiving the laboratory removes it from the catalog and makes its detail endpoint return 404. Nothing is copied into a new services table.

## 5. Backend / API behavior

| Endpoint | Behavior |
| --- | --- |
| `GET /api/mobile/services/` | Public active catalog, consistent with existing public facility browsing. Returns `{services: [...]}`. |
| `GET /api/mobile/services/<id>/` | Same eligibility checks; returns `{service: {...}}` or 404. |
| `GET /api/facilities/?resource_type=facility` | Existing endpoint with optional physical-resource filtering. Without this parameter, its existing contract remains. |

New catalog endpoints are GET-only; POST returns 405. No mutation, request creation, approval, payment, document, stock or booking API behavior changed. Existing administrator RBAC and authenticated chat remain in force. Message Office uses the existing contact selection (active Facilities Admin, with the existing Super Admin fallback); it does not invent assigned personnel. Messaging requires the normal login/chat connection and shows existing errors if no contact is available.

Deploy the updated Django code alongside the updated app. There is no existing mobile service intake API to reuse; authenticated application submission, sample acceptance, resource checks, assessment allocation and lease processing remain separate future work, as explicitly selected by the user.

## 6. Database / migration impact

No new tables, models, stock fields, service records, rates, schedules, migrations, dependencies or live database writes. Existing Facility service settings remain authoritative. No operational or research sample data was installed. Test records exist only in isolated test fixtures.

## 7. Tests performed and manual checks

Actual successful verification:

- **23 Flutter tests passed** across dashboard header, tab/search behavior, dormant center-action reuse, five-item navigation, catalog transport and service screens.
- **26 Django tests passed** across `modules.facilities.test_mobile_services`, `modules.facilities.test_service_navigation` and `api.test_mobile_facility_booking`; Django system checks reported no issues. The catalog test confirmed one database query, active/archive/physical exclusions, real configured pricing, no private workflow exposure, legacy modes, honest empty results, GET-only behavior, and compatibility of the original facility endpoint.
- `flutter analyze` on all ten changed application files and five changed/new test files reported **No issues found**.
- Widget checks cover 320/390px phone widths, 844x390 landscape, five selected tab states, retained Services search/data, service detail revalidation/failure/Retry, distinct guidance for all three workflows, no drawer, no visible quick action, existing Messages navigation, error versus empty versus search miss, 1.5x text and reduced-motion behavior on Services. Navbar checks also include 768px and bottom safe-area insets.
- Services review images: `scratch/mobile-services-review/services-320.png` and `services-390.png`. The 390px capture was visually inspected. They are widget fixtures, not live catalog screenshots; screenshot-only Material icon font rendering is incomplete. The in-app icons use the existing icon assets. There was no physical Android or live authenticated end-to-end test.
- Initial checks found outdated drawer/center-action expectations, an ambiguous test finder matching search text as well as a card title, a retry callback returning a Future to setState, and a reduced-motion helper missing its BuildContext parameter. These were corrected before the successful final runs.

Repeat from `campushub`:

```powershell
flutter test test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart test/floating_bottom_navbar_test.dart test/service_catalog_test.dart test/services_screen_test.dart
```

Repeat from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_mobile_services modules.facilities.test_service_navigation api.test_mobile_facility_booking --keepdb --noinput
```

Manual verification:

1. Restart the Flutter app (or rebuild/deploy the APK) and deploy/reload Django. Confirm the exact five-tab order and no + button, FAB or drawer.
2. Tap every tab and swipe between pages; confirm selection follows the actual page. Tap Home's facility shortcut and confirm Facilities, not Services.
3. In Services, search for an actual configured active record, switch to another tab and return; check query, loaded results and scroll position remain.
4. Open its details. Verify recorded images, description, location, rates, availability, requirements and terms. Open its service-specific request action and verify no submission/approval is claimed.
5. Use Message Office while signed in, or verify the existing honest login/contact/chat error. Do not assume a successful live conversation from widget tests.
6. Check an empty catalog and stop the server temporarily in development to distinguish empty from error; restore the server and Retry. Never add fake service cards to hide an error.
7. In an isolated development database, deactivate or archive a service after opening the list, then open its details. Its request action must not remain enabled.

## 8. Debugging, remaining limitations and safe practice

Confirmed limitation outside this feature: switching into the existing Home carousel with 1.5x text exposed a fixed-height carousel overflow (60px at 320 width, 20px at 390). Normal-size Home header/navigation regression checks pass. The final large-text tests focus on the new Services tab; this update does not claim the entire existing app supports every dynamic-text size. No unrelated Home carousel redesign was performed.

If Services is empty, first verify an actual unarchived service exists and its stored status is `available`; the record must match the existing service category/mode classifier. Inactive, unavailable and maintenance resources are intentionally excluded. Category labels are not automatic seeded records.

If loading fails, verify the PC address in ApiConfig, Django listening on `0.0.0.0:8000`, phone/PC network access and the new API routes. A successful old facility API does not prove the newly deployed Services endpoint exists. If detail stops working, the service may have been archived/deactivated; Retry must not create a booking or restore the service.

If a price is absent, correct its actual configured service pricing in the authorized admin editor. Do not hard-code a mobile fee. If office hours are absent, contact-office guidance is intentional; office hours never confirm an assessment date, sample acceptance or lease approval.

Safe learning exercise: modify only an isolated test fixture's laboratory name, then run `flutter test test/service_catalog_test.dart`. Update the expected fixture value and rerun. Trace how the JSON `name` flows into ServiceItem and the card title. Next change the fixture status to inactive and verify it is filtered out. Restore the fixture afterward; no production request or service record is needed.


## Bottom-navigation selection styling - October 18, 2026

1. **Reason:** the user requested a clearer CampusHub palette and filled icons after selecting a tab. Previously the same Lucide outline glyph was merely recolored, so selection had little shape difference.
2. **Files:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` (constructor palette, `default5Items`, `_buildNavItem`, adaptive bar height and decoration); `campushub/test/floating_bottom_navbar_test.dart` (outline/filled pairs, selection, contrast and large-text/reduced-motion checks); `campushub/lib/module_app/screens/services_screen.dart` (the View Service label can wrap inside its row at large text sizes). This guide and `CAMPUSHUB_CONTEXT.md` record the change. Current anchors: constructor palette at lines 49-51; `default5Items` at 68; `_buildNavItem` at 177; `AnimatedContainer` at 204; adaptive `navHeight` at 304; bar separator at 320. The test entry is `void main` near line 5, and the wrapping label is the `Flexible` around View Service in `services_screen.dart` near line 175.
3. **Changes:** white flat bar; navy filled selected icon over a compact gold `#FCB316` indicator; quieter navy outline idle icons and navy labels. The main bar shadow was removed, leaving its subtle separator. One consistent Material icon family supplies real outline/filled variants; Lucide has no matching solid font variants in the current package. The existing five labels/order and hidden reusable center-action branch remain. Focus/hover/splash colors use the same palette.
4. **How it works:** `FloatingBottomNavbarItem.icon` supplies the idle outline and its existing `activeIcon` field supplies the filled glyph. `_buildNavItem(context, index, item)` receives the current index and renders the filled glyph plus gold indicator only when `index == currentIndex`. `onTap(index)` still calls the same Dashboard/PageController navigation. `selectionColor` is a reusable constructor parameter; default gold remains the existing Flutter color, independent of the changed web-only shade. The 180ms indicator transition and small icon scale honor reduced motion. Bar height follows scaled label height with a 60px minimum; SafeArea still protects the system inset. Example: selecting Services sets index 2, fills its briefcase icon and moves the gold selection treatment there; no record or API request is created by this styling code. Shape, label weight and selected semantics accompany color, so selection is not color-only. The outer Semantics node supplies a single full label and accessible onTap; child icon/text semantics are excluded to prevent duplicate announcements.
5. **Backend / API:** unchanged. No route, state-controller, service data source, authentication, permission or request-submission logic changed.
6. **Database / migration:** none. No dependency or image asset was added; built-in Material icons are already available. No web gold or Flutter service rates changed.
7. **Verification:** 20 Flutter tests passed across navbar, dashboard header/search, dormant center action and Services UI. They exercise all five selected states at 320/390/768px, filled/outline glyphs, gold indicators, preserved layout, content clearance, dark-theme context, bottom safe-area insets, 2x label text and reduced motion. Computed palette contrast checks passed at least 4.5:1 for selected navy on gold and idle navy-on-white after alpha blending. The existing Services large-text test exposed an over-wide View Service text row with Flutter's test font; making only that label Flexible resolved it. Targeted Flutter analysis of the component, Services label and navbar test reported No issues found. Native verification also passed seven Pixel 10a Android emulator scenes: Home, Marketplace, Services, Facilities and Profile selected in light context, then Services in dark context and at 2x text. UI Automator confirmed exactly one accessible name per destination and the correct selected flag. The first native inspection exposed duplicate label semantics; the final component excludes duplicate child semantics while preserving a labelled accessible tap action. An emulator System UI busy dialog during cold boot was dismissed with Wait; it was not an application crash. Native captures and machine-readable results are in `scratch/mobile-navbar/` (`native-verification.json`). Home and dark/large Services captures were visually inspected. These screenshots use `scratch/mobile-navbar/native_preview.dart`, which imports the actual production widget and never loads accounts, catalog records or APIs. They verify the component rather than a signed-in full app workflow. The normal `lib/main.dart` debug APK was rebuilt successfully after the temporary preview build, so `build/app/outputs/flutter-apk/app-debug.apk` is the normal app artifact, not the preview. The connected physical phone was left untouched.
8. **Limitations / debugging / safe exercise:** the bar intentionally remains branded white in the existing light and dark screen contexts; this is not a whole-app dark-theme redesign. Very large labels may ellipsize horizontally, while full labels remain available to accessibility/tooltip output. Original navigation and screen state are covered by existing widget checks. To learn safely, change only `selectionColor` temporarily in a local widget-test fixture and rerun `flutter test test/floating_bottom_navbar_test.dart`; observe that the icon shape still follows currentIndex and the gold default assertions stay unchanged. Restore the fixture; no database or server interaction is needed. Restart/rebuild the mobile app to see the updated component.


Final verification commands for the October 18 selection styling:

```powershell
# From campushub:
flutter test test/floating_bottom_navbar_test.dart test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart test/services_screen_test.dart
flutter analyze lib/module_app/widgets/navigation/floating_bottom_navbar.dart lib/module_app/screens/services_screen.dart test/floating_bottom_navbar_test.dart
flutter build apk --debug --target lib/main.dart
```

The complete 20-test run passed after the application changes. The navbar tests were rerun after replacing a deprecated test-only semantics accessor and passed again; final analyzer output reported No issues found with that rerun. Targeted whitespace checks passed. The first semantics-test run needed its test handle disposed before Flutter's end-of-test checks; that test harness cleanup is now explicit. Existing web, API and mobile submission limitations described above remain unchanged.

## Mobile header and discovery Home - October 18, 2026

This update supersedes the earlier drawer-removal, rotating Home banner, separate Home facility model, and service request-button wording in this guide. The five bottom destinations and their current icon-selection styling remain; compact labels now follow native Material text-scaling behavior.

### Reason and confirmed causes

The old Home started with a large rotating promotional carousel and had no Services preview. Header search switched to Marketplace without passing its query. The drawer had been removed in an earlier update. A separate private Home facility model displayed different status/rating information from the existing FacilityItem. The Notifications button had an empty callback: this checkout has no mobile notification feed, model, API client or notification screen. This is a confirmed implementation limitation, not evidence of zero unread notifications.

### Files, current lines and nearby anchors

Paths below are relative to the repository root. Lines describe this implementation; use the named anchor if later edits move a line.

| File | Current line / nearby anchor | Change |
|---|---|---|
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 25 `class DashboardScreen`; 82 `_goToTab`; 101 `_openMessages`; 130 `_openNotifications`; 166 `_drawerDestination`; 182 `dashboard-brand-header`; 356 `HomePage`; 919 `_compactCard` | Reuse the existing shell, restore drawer, replace header search with one Home search, real chat badge, compact product presentation |
| `campushub/lib/module_app/screens/home_page.dart` | 20 `class HomePage`; 58 `_observed`; 64 `_load`; 70 `_readProducts`; 82 `_readFacilities`; 89 `_readServices`; 95 `_refresh`; 112 `_matches`; 115 `_section`; 253 `home-search`; 399 `_FacilityDiscoveryCard`; 502 `_ServiceDiscoveryRow` | New focused Home implementation using existing catalog services, models and detail screens |
| `campushub/lib/module_app/models/facility_item.dart` | 24 `this.capacityLabel`; 61 `capacity_label`; 85 `final String capacityLabel` | Read the existing backend's formatted capacity range; optional constructor field preserves existing callers |
| `campushub/lib/module_app/models/service_item.dart` | 37 `actionLabel` | Use `How to Request This Service`; no submission implied |
| `campushub/test/dashboard_header_test.dart` | `void main` | Phone widths 320/390, double-size text, real production card layout, header controls, notification limitation |
| `campushub/test/dashboard_search_appbar_test.dart` | `drawer routes to existing tabs` | Drawer destinations, selected tab and retained Home search |
| `campushub/test/home_page_test.dart` | `search covers all three catalogs` | Full fetched-catalog search, capacity/status rendering, service details navigation, loading/empty/error/Retry |
| `campushub/test/home_test_fixtures.dart` | `HomeTestCatalog` | Isolated test data and loaders; never imported by production screens |
| `campushub/test/dashboard_center_add_button_test.dart` | `dashboard uses five tabs` | Expect the restored drawer while keeping the center action hidden |
| `campushub/test/service_catalog_test.dart`, `campushub/test/services_screen_test.dart` | `actionLabel`, `details revalidate active state` | Match truthful guidance wording and preserve category-specific instructions |

### What changed and how it works

1. **Header:** white surface, navy Material icons, existing logo and Montserrat wordmark. Menu opens the restored drawer. Messages opens the existing MessagesPage from both header and drawer. An AnimatedBuilder listens to the existing ChatService singleton and sums actual conversation `unreadCount` values; only a positive count displays a badge. No alternate chat connection/service was created. Notifications opens an honest availability sheet without a fabricated unread badge.
2. **Navigation:** existing MaterialApp/AppRouter/Navigator/PageController and RetainedTab remain. This checkout does not use GetX for this shell; no GetX package/controller was added. Drawer indexes: Home 0, Marketplace 1, Facilities Booking 3, Services 2, Profile & Account 4. Messages and My Cart push their existing screens. Back uses the existing Navigator behavior. The bottom bar remains Home, Marketplace, Services, Facilities, Profile; no center plus or quick actions.
3. **Home:** greeting reads the logged-in first name through SessionService. An unknown/missing name produces `Welcome to CampusHub`. The promotional carousel, its timer, duplicate private facility model and obsolete Home preview classes were removed. My Activity and Recent Activity were already absent; their backend records/pages were not deleted. Seller-specific screens and permissions are unchanged.
4. **Marketplace:** ProductService.fetchApproved supplies actual products. Home stably sorts by real `soldCount`, preserving API order for ties; no Hot/New/Recommended label is added. Up to six cards appear in the normal preview. The compact branch of the existing product card reuses its favorite, product-details interaction tracking and CartService.quickAdd methods. Existing Marketplace card presentation remains the default outside Home.
5. **Facilities:** FacilityService.fetchFacilities still requests physical resources through `/api/facilities/?resource_type=facility`. Results are parsed by the existing FacilityItem; no new facility model. Home shows the recorded image, name, backend capacity_label and operational status. For older responses without a range, a positive recorded capacity is shown; absent capacity is omitted. Open for Booking does not claim a selected time slot is conflict-free. Tapping opens FacilityDetailsScreen with that exact record. Home omits rates and empty review stars.
6. **Services:** the existing ServiceCatalog and ServiceItem provide actual active service records. Up to three show in the normal Home preview. A row opens the existing ServiceDetailsScreen, which revalidates its active state. The guidance action now says `How to Request This Service` and retains different sample-analysis, assessment and lease instructions, actual requirements/location and Message Office. There is no new submission workflow.
7. **Search:** TextEditingController supplies a trimmed, case-insensitive query. `_matches(text)` returns true when the query occurs in the product name/seller/category, facility name/category/location or service name/category/description. All fetched rows are searched, including those outside the normal preview limit. Typing updates local results and does not call another API. This is catalog discovery, not a new server-wide search endpoint. See All opens the existing unfiltered destination tab; tapping a result opens its actual details.
8. **States:** each catalog has its own FutureBuilder. A failed service catalog does not hide working products. Loading shows a small navy progress indicator; successful empty catalogs use the requested exact copy; failed loads show Unable to load plus Retry. Search misses are different from empty catalogs. Pull-to-refresh starts each existing catalog read once and reloads the greeting. `_observed(future)` attaches an immediate error handler so an offscreen section can safely attach its FutureBuilder later; the original future still exposes its error to that section.
9. **Layout:** navy `#1A1851`, mobile gold `#FCB316`, white/light surfaces and restrained navy-derived borders/text. No gradients or decorative shadows. Sections use 20px side spacing and 24px separation. Horizontal lists scroll naturally. At larger text sizes section headings and See All stack, and card heights follow TextScaler so titles/status do not overflow. Icon actions keep tooltips and Material touch behavior.

### Function inputs, outputs and data flow

```text
DashboardScreen -> SessionService -> firstName -> compact greeting
                -> existing ChatService -> conversation unread counts -> Messages badge
HomePage._load()
  -> ProductService.fetchApproved() -> List<ProductItem> -> sort -> product cards
  -> FacilityService.fetchFacilities() -> FacilityServiceResult
       -> FacilityItem.fromJson() -> capacityLabel/status -> facility cards
  -> ServiceCatalog.fetchServices() -> List<ServiceItem> -> active rows -> service rows
TextEditingController.text -> _matches(record text) -> filtered existing rows
Tap result -> existing detail screen; cart/favorite -> existing services
```

`_readProducts()` returns a Future of real ProductItems; `_readFacilities()` converts a failed transport result into an error instead of a fake empty success; `_readServices()` retains active rows. `_section<T>` receives a future, matching function, empty message, Retry callback and content builder, then chooses the correct visible state. Each Retry callback uses a block inside setState: assigning a Future with an arrow callback returns that Future and triggers Flutter's debug assertion. Tests caught that issue during implementation; the callbacks now synchronously assign state and let FutureBuilder observe completion.

Annotated example: if the backend sends `capacity: 500` and `capacity_label: "300-500 pax"`, FacilityItem stores the label, and the Home card uses that label rather than concatenating or inventing a range. Search `court` tests the recorded facility text and shows the matching card. No booking is created by search or by opening its details.

### Backend, database and deployment

No Django/FastAPI endpoint, permission, model, migration, payment, order or reservation workflow changed. Products use `/api/products/approved/`; physical facilities use `/api/facilities/?resource_type=facility`; Services uses existing `/api/mobile/services/` and `/api/mobile/services/<id>/`; Messages uses existing authenticated chat APIs/WebSocket. Capacity label was already in the facility payload. No new package or generated image was added. Rebuild/restart Flutter to see this UI; no migration command is required. The app still needs the configured reachable Django server and existing Services APIs.

### Verification and manual checks

27 Flutter tests passed across header, drawer/search, discovery, dormant center action, bottom navigation, ServiceCatalog and Services UI. Targeted analysis of the changed application/test Dart files reported `No issues found!`. Tests cover 320/390px phones, double text, existing 844px service landscape checks, retained tab state, search beyond the preview limit, actual formatted capacity, loading/empty/error/Retry and category-specific contact guidance. Fixtures are test-only; these checks do not claim successful live authenticated transactions, unread-message delivery or physical-phone performance.

Commands from `campushub/`:

```powershell
flutter test test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/home_page_test.dart test/dashboard_center_add_button_test.dart test/floating_bottom_navbar_test.dart test/service_catalog_test.dart test/services_screen_test.dart
flutter analyze lib/module_app/screens/dashboard_screen.dart lib/module_app/screens/home_page.dart lib/module_app/models/facility_item.dart lib/module_app/models/service_item.dart test/home_page_test.dart test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/home_test_fixtures.dart test/service_catalog_test.dart test/services_screen_test.dart test/dashboard_center_add_button_test.dart
flutter build apk --debug --target lib/main.dart
```

Manual checks:

1. Sign in as an existing normal user. Verify the actual first name, menu/brand/Messages/bell header and absence of the top-right search icon and rotating banner.
2. Search a real product, facility and service in turn. Open each result. Clear search; switch tabs and return to confirm retained state. See All should activate the corresponding bottom tab.
3. Open drawer destinations and Messages from both entry points. Open My Cart. On actual unread chat data verify the badge changes; with zero unread messages there is no badge.
4. Verify facility capacity ranges/status against saved records; no Home pricing formula or invented rating should appear.
5. Open each active service and its How to Request guidance. Check actual requirements and contact/visit-office instructions; no request should be submitted.
6. Test an empty catalog, stop/restart a development server and Retry, then pull to refresh. Distinguish no records from connection failure. Increase the phone text size and scroll all three Home sections.

### Debugging, limitations and safe learning exercise

If the UI is unchanged, restart/rebuild the running Flutter application; a Django refresh alone cannot update Dart code. If a section cannot load, check the existing ApiConfig address, Django binding/firewall/network and the real API response; do not replace it with sample rows. If a service disappears, check its real active/archived state. If a capacity range is missing, inspect `capacity_label`; do not infer a minimum from the maximum. Products without recorded sales keep the server order, without claiming to be popular or recently added. Mobile notifications remain unavailable, and service intake remains office guidance. Home stays white in a dark-theme app context by this brand-specific scope; other screens are not a whole-app dark-theme redesign.

Safe exercise: in `test/home_test_fixtures.dart` only, change the laboratory description. Run `flutter test test/home_page_test.dart`, then search a word from that description in an isolated widget test and verify it finds that service without increasing `catalog.calls`. Next set the fixture service inactive and verify it is excluded. Restore the fixture. This teaches JSON-to-model-to-filter-to-widget data flow without creating or changing real service records.

Native verification: five valid Pixel 10a Android emulator captures show the top Home, facility/service section, drawer, and top/lower Home at OS night mode with 1.3x system text. Captures are in `.impeccable/review/mobile-home/`; `scratch/mobile-home/native_preview.dart` imports the production DashboardScreen with test-only catalog loaders. The preview reads the emulator's existing saved greeting but does not create accounts, submit requests or mutate live catalogs. There is no synthetic production fallback. A cold-boot System UI busy dialog and transient theme-change/launcher frames were excluded and recaptured only after the expected Home semantics were present. This does not establish real handset performance, a signed-in live transaction, a complete dark-theme app or iOS/tablet verification. The connected physical phone was not modified. The final default debug APK was rebuilt from `lib/main.dart`, not the scratch preview.

Reviewer correction: the independent design review found crowded bottom labels at 320px with 2x text. Only the destination Text now uses `TextScaler.noScaling`, matching Flutter SDK Material NavigationBar behavior (`C:/flutter/packages/flutter/lib/src/material/navigation_bar.dart`, navigation-label and height documentation). All five names remain visible at normal native label size; full tooltip text still follows system scaling and Semantics preserves every full destination name, selected flag and tap action. Home content continues to honor the user's text size. Files: `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart`, near `Text(item.label)` / `textScaler`; `campushub/test/floating_bottom_navbar_test.dart`, large-text test. The working tree received separate navbar icon/indicator edits during this task; this Home update preserves the current appearance rather than restoring an older pill or indicator. Only destination-label scaling was changed here. Existing tap callbacks, order and safe-area behavior remain. The Services reduced-motion test checks any implicit animations actually present inside a destination; a static destination also honors reduced motion without requiring a removed AnimatedScale or indicator widget.


## Revert latest Home search refinement - October 18, 2026

- **Reason:** user requested Revert. Undo only the immediately preceding greeting/search/filter refinement; keep the broader discovery redesign and unrelated concurrent header/navbar/card changes.
- **Files:** `campushub/lib/module_app/screens/home_page.dart` (`Greeting section`, `fontSize: 22`, `Search input field`, `home-search`); `campushub/lib/module_app/widgets/home/home_preview_cards.dart` (`HomeSectionHeader`, `View service`); `campushub/test/home_page_test.dart` (`void main`).
- **Restored:** the previous GoogleFonts welcome at 22sp, existing greeting/supporting copy, 16dp spacing and original full-width 52dp search container. Removed the new filter icon/button, filter sheet, filter state, section gating, explicit font-variation additions and the filter-specific test. The small shared heading/action layout edits from that refinement were also undone to restore its prior implementation.
- **Functions/data flow:** `_section<T>` once again shows each existing catalog without an extra scope condition. `_matches` still receives the current search query and record text and returns the existing case-insensitive match. Catalog futures, actual records and existing routes/actions remain. No new controller or replacement search logic is added by the revert.
- **Backend/API/database:** unchanged; no migration or server command. The real catalog data and permissions were not reset.
- **Verification:** formatted affected Dart files; targeted analysis of the two source files and discovery test reported No issues found. The full widget suite was not rerun for this restoration; earlier compact/filter test results do not describe the reverted UI. Prior shared-card large-text limitations are restored with the previous layout.
- **Safe exercise:** search an existing product name, clear the query and confirm all three catalog sections return. Verify no Filter search button or sheet exists. Restart/hot-reload Flutter to load the restored source; no database change is needed.

Final revert anchors: `home_page.dart:194` Greeting section, `:213` fontSize22, `:231` Search input field, `:247` home-search; `home_preview_cards.dart:41` HomeSectionHeader and `:556` View service. The normal `flutter build apk --debug --target lib/main.dart` succeeded after the revert. Whitespace checks passed. The temporary emulator preview was restarted with the restored source, then closed; the connected physical phone was untouched.


## White mobile header and welcome-only greeting - October 18, 2026

1. **Reason:** the user requested the mobile header return to white and removal of Good morning and What are you looking for today. This is a small presentation change after the prior search/filter revert.
2. **Exact files/anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:203` (`dashboard-brand-header`) and `:303` (`statusBarColor`); `campushub/lib/module_app/screens/home_page.dart:194` (welcome Text), `:200` (`fontSize: 22`) and `:223` (`home-search`). This guide and CAMPUSHUB_CONTEXT.md record the change.
3. **Changes:** header background and status bar are white; menu, message and notification icons use navy. Campus uses navy and Hub keeps the existing gold accent, so the wordmark is visible on white. Android status icons use dark brightness; the corresponding iOS status-bar brightness is light. Removed the two extra greeting/supporting Text widgets and their internal gaps. Existing welcome size, full-width search and catalog sections remain.
4. **How it works:** DashboardScreen.build supplies header and SystemUiOverlayStyle colors. HomePage.build still receives the saved first name from DashboardScreen; for example, a recorded first name of Ana renders Welcome Back, Ana, while a missing name keeps Welcome to CampusHub. No new text controller, search filter, route or data calculation was added. The search controller and matching flow are unchanged.
5. **Backend/API:** unchanged; the same session, catalog, messages and navigation handlers remain.
6. **Database/migrations:** none. Hot-reload/restart Flutter to load the source change; no Django command or data edit is required. No APK rebuild was performed for this small follow-up.
7. **Verification:** Dart formatting and targeted analysis of both modified source files succeeded with No issues found. Source inspection confirmed white header/status colors, navy foregrounds and removal of both requested strings. The existing 390px normal-text dashboard widget check was run and failed with a RenderFlex right overflow of 10px. The same overflow had also been observed before this follow-up. Its exact child was not isolated here; this is not claimed as a passing render check. No physical-device or new native screenshot check was performed.
8. **Limits/debugging/practice:** remaining layout overflow is separate pending verification work, not hidden by zero/fake data or weakened assertions. To verify this presentation, restart Flutter and check the white header, visible navy controls, welcome and search. Safe learning exercise: inspect the header color and SystemUiOverlayStyle together; changing a header surface without matching status-icon brightness can make system icons unreadable. Try color changes only in an isolated preview and restore the recorded white/navy values. No production account or database change is needed.


## Light container palette - October 18, 2026

1. **Reason:** the user requested a better light/light-gray container treatment. White cards on a very light neutral page give clear separation without heavy shadows or gray text blending into gray cards.
2. **Files/current anchors:** `campushub/lib/module_app/widgets/home/home_preview_cards.dart:18` HomeAppColors; `:25` appBackground; `:26` surfaceTint; `:171` first cardBorder and equivalent facility/service card decorations. `campushub/lib/module_app/screens/home_page.dart:207` Search input field. This guide, CAMPUSHUB_CONTEXT.md and scoped mobile design files record the palette.
3. **Changes:** page background `#F8FAFC`; cards/search/header white `#FFFFFF`; image/fallback containers `#F1F5F9`; subtle shared borders `#E2E8F0`; primary text CampusHub navy `#1A1851`; secondary text `#475569`; quieter metadata token `#64748B`. Removed the three catalog-card shadows and the search shadow for a flat resting surface. Existing geometry, content, navigation and real-data states remain.
4. **How it works:** HomeAppColors is the shared constant palette consumed by DashboardScreen.build, HomePage.build and the three preview-card build methods. `appBackground` colors the page; `white` colors the card body; `surfaceTint` colors the recorded-image region/fallback container; `cardBorder` aliases `border` so all cards share the same outline. Inputs are existing record/image/text fields; output is the same widgets rendered with the updated palette. Example: a product without a saved image shows its existing navy fallback icon on the light-gray image container, while its real price/seller remain on the white card body. No sample record is introduced.
5. **Backend/API:** unchanged. Catalog requests, search, cart, favorites, facility/service details and permissions keep the existing implementations.
6. **Database/migrations:** none. No dependency, image asset or server command required. Hot-reload Flutter to load the new constants; no APK rebuild performed for this color-only change.
7. **Verification:** formatted both edited Dart files; targeted Dart analysis including DashboardScreen reported No issues found. Computed sRGB contrast: navy on white 16.24:1; secondary text on white 7.58:1 and page 7.24:1; metadata on white 4.76:1 and page 4.55:1. Navy fallback icons on image tint are 14.82:1. The metadata token is not intended for body text on the darker image tint (4.34:1); use secondary/navy there. No new widget tests were written for constant palette/shadow changes, and the full UI suite/native render was not rerun. The previously recorded 10px layout overflow remains outside this color-only verification.
8. **Debugging/learning exercise:** if a container still looks unchanged, restart Flutter and inspect which HomeAppColors token it uses before adding local colors. Safely change only a test-preview surfaceTint to white, compare fallback image separation against card bodies, then restore `#F1F5F9`. Verify the actual data and tap destinations remain identical. Keep secondary/body text dark enough for its actual surface; a light border is separation, not a text color.


## Smaller Home welcome - October 18, 2026

1. **Reason:** user requested a smaller Welcome Back heading.
2. **Exact files/anchors:** `campushub/lib/module_app/screens/home_page.dart:200`, `fontSize` beneath `Welcome Back`; `campushub/DESIGN.md:18`, `greeting`; `CAMPUSHUB_CONTEXT.md:3`, latest welcome sizing; this guide, `Smaller Home welcome`.
3. **Changes:** reduce only the welcome's base font size from22sp to20sp; align its documented typography with the existing Montserrat family. Color, weight, wording and spacing remain.
4. **How it works:** `HomePage.build` reads `widget.firstName`, trims it and renders the personalized welcome or existing generic fallback. Its `GoogleFonts.montserrat` style now uses20sp; Flutter still applies device text scaling. Example: saved name Ana renders Welcome Back, Ana at the smaller base size. No user-data calculation changes.
5. **Backend/API:** unchanged; no endpoint, controller or permission changes.
6. **Database/migrations:** none. Hot reload Flutter to see this source-only style change; no dependency command required.
7. **Tests performed:** `dart analyze lib/module_app/screens/home_page.dart` passed with No issues found. No new tests, APK build or device screenshot for this reversible font-size adjustment.
8. **Limitations/debugging/exercise:** the previously documented Home card overflow is not claimed fixed. If the heading is unchanged, confirm the running Flutter app uses this checkout and hot reload/restart. Safe exercise: in a disposable preview, compare20sp and22sp with the phone's larger-text setting enabled, verify the real first name remains visible, then restore20sp. Keep system text scaling enabled.

## Sugar Pie header wordmark - October 18, 2026

1. **Reason:** the user supplied Sugar-Pie-W00-Regular.ttf and requested that exact typeface for CampusHub in the mobile header. Earlier attempts could not apply it because only Montserrat was present.
2. **Files/current anchors:** new `campushub/assets/fonts/Sugar-Pie-W00-Regular.ttf`; `campushub/pubspec.yaml:75` (`family: SugarPie`) and `:77` (asset path); `campushub/lib/module_app/screens/dashboard_screen.dart:246` (`dashboard-brand-name`) and `:248` (`fontFamily: 'SugarPie'`); `campushub/test/dashboard_header_test.dart:44` (`FontLoader('SugarPie')`). This guide, CAMPUSHUB_CONTEXT.md and the scoped mobile design documents record the font.
3. **Changes:** copy the user-provided font unchanged into Flutter assets, register its SugarPie family alias, then use that family only on the shared header Text.rich wordmark. Keep the current navy Campus/gold Hub spans, white header, logo and navigation. Set regular weight400 and natural letterSpacing0 at the existing24sp size; the supplied font is Regular, so synthetic extra-bold weight/tight Montserrat tracking is inappropriate for its brush lettering. Existing FittedBox.scaleDown and Flexible still protect narrow headers. Drawer, welcome/body text, cards and other screens keep their configured fonts.
4. **How it works:** the pubspec family declaration maps SugarPie to the local TTF. Flutter bundles that asset, TextStyle selects its family alias, and both colored TextSpans inherit it. The internal font name is SugarPieW00-Regular; the alias does not have to match the internal name, but TextStyle and pubspec must match each other exactly. Example: `fontFamily: 'SugarPie'` selects the bundled file rather than downloading a Google Font. The existing FontLoader capture helper also loads the asset when dashboard screenshot captures are requested, preventing test screenshots from silently showing a fallback face.
5. **Backend/API:** unchanged. This is local asset/text styling, with no new network request, controller, route, data or permissions.
6. **Database/migration/deployment:** none. `flutter pub get` was run to refresh Flutter's asset configuration. A new bundled font requires stopping and running/rebuilding Flutter; hot reload alone may keep the old asset/font manifest. No additional package was installed or upgraded for this task. The normal debug APK build is verified separately below.
7. **Verification:** a standard-library SFNT/name-table check recognized the file as a TrueType/OpenType font, read family/style SugarPieW00-Regular/Regular and OS/2 weight400. Dart formatting and targeted analysis of DashboardScreen and its existing header test reported No issues found. `flutter build apk --debug --target lib/main.dart` passed (39.9 seconds); the normal APK is `campushub/build/app/outputs/flutter-apk/app-debug.apk`. The two existing Services-tab large-text/reduced-motion widget checks passed at320px and390px (`flutter test test/services_screen_test.dart --plain-name 'Services tab fits large text and reduced motion' --reporter expanded`). An APK ZIP check verified the SugarPie FontManifest entry and confirmed its129,796-byte TTF exactly matches the copied source (SHA-256 `524e3773576cba2df7fa3cb687be96e6fba592770c947c615b23c4dc68a8b5c7`). The full Home suite/physical phone was not used to claim the earlier unrelated10px layout issue fixed. No new native screenshot was taken for this font change.
8. **Limits/debugging/safe exercise:** if Montserrat still appears, confirm the TTF path, exact SugarPie alias and a full app restart after pub get. Do not change the global app theme to apply a wordmark-only font. In an isolated preview or disposable branch, try wordmark fontSize26, check that menu/Messages/bell remain visible at320px, then restore24. This teaches local typography scope and FittedBox behavior without changing accounts or records. Keep the supplied font file in source assets for other checkouts/builds; it is not ignored by Git.


## Simple Home naming and pill search - October 18, 2026

1. **Cause / reason:** user requested simpler file names, a search bar with fully rounded ends (50% radius appearance), and a contained filter icon to its right. Inspection also found an existing16sp welcome, which this change preserves. Initial tests confirmed unbounded Home section headings and service action text overflowed on narrow/large-text layouts; these were layout issues, not API failures.
2. **Exact files / current anchors:**
   - Rename `campushub/lib/module_app/screens/home_discovery_page.dart` to `campushub/lib/module_app/screens/home_page.dart:29` (`HomePage`); enum at18; `_showFilters` at125; scaled service width at262; search row at285; filter button at352; Showing/Reset at376; conditional catalog sections at394/420/447.
   - `campushub/lib/module_app/screens/dashboard_screen.dart:16` imports the new file; `:407` instantiates `HomePage`.
   - `campushub/lib/module_app/widgets/home/home_preview_cards.dart:54` (`HomeSectionHeader.build`) uses flexible heading/action widths; `:542` makes View service text flexible.
   - Rename `campushub/test/home_discovery_test.dart` to `campushub/test/home_page_test.dart:16` (new responsive filter tests); existing search and loading/error/empty checks remain at94 and156.
   - `campushub/test/dashboard_header_test.dart:115` and125 use renamed `home-scroll` key.
   - This guide, `CAMPUSHUB_CONTEXT.md` latest entry, `campushub/DESIGN.md` greeting/search/Reading Space Rule and `campushub/.impeccable/design.json` source/homeSearch metadata. Earlier guide references now point to the renamed source/test; earlier visual descriptions remain historical.
3. **Changes made:** renamed the class/state alongside the source, with no duplicate Home implementation. Search uses an OutlineInputBorder with a large clamped radius so the ends form a pill at any field height; it can grow with system text size. Beside it is a52dp white container with navy tune icon and8dp gap. It turns gold for an active category filter and exposes selected semantics. A visible Showing label and Reset communicate selection without color alone. The sheet has All/Marketplace/Facilities/Services ChoiceChips, accessible native controls, a close button, safe areas and scrolling for landscape/large text. Selecting applies and closes; dismissing preserves current selection. Responsive shared-heading/CTA fixes keep full labels wrapping, and service-card height/width accommodates scaled text.
4. **How it works / inputs and outputs:** `_showFilters()` removes keyboard focus and awaits an optional `_HomeFilter` result from the native modal sheet. A selection updates `_filter` only while the widget is mounted. Cancel returns null and changes nothing. `build()` shows the chosen catalog sections; existing `_matches(String)` continues searching actual record text using `_search`. `_load` and `_readProducts`/`_readFacilities`/`_readServices` keep their existing futures and API calls; choosing a filter never calls them again. Example: type Chocolate, choose Marketplace; only matching loaded products display. Choose Services and the same query is retained; Reset shows all catalogs without erasing the query. Clear search remains a separate action. Existing RetainedTab/PageController navigation continues preserving this state while tabs change.
5. **Backend / API behavior:** unchanged. Approved products, physical facilities and active service catalogs use their existing endpoints and permission rules. Filtering is local to records already fetched; it is not a new server-wide paginated search. No fake products or services are introduced; fixture records are test-only. See All still opens its existing destination.
6. **Database / migration impact:** none. No dependency or asset changes. Fully restart the running Flutter app after the source/class rename; no Django or migration command required. No new APK was built for this update.
7. **Tests performed / results:** final `flutter test test/home_page_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart test/dashboard_header_test.dart --reporter expanded` passed all11 tests. New filter cases cover375px,320px with2x text/dark theme/reduced motion, and844x390 landscape; they verify search preservation, selected state, reset, dismiss, non-overlapping controls,48dp minimum button target and unchanged catalog request counts. Existing tests cover catalog failure/Retry, empty states, drawer/retained search, all-catalog search beyond preview limits, native destinations and production-card layouts at320/390px and2x text. Targeted Dart analysis of source, Dashboard, shared cards and both changed tests reported No issues found. First runs exposed actual heading/CTA overflows; final successful run followed their fixes. A separate390px widget capture test passed; its screenshot confirms pill/button geometry and SugarPie brand, but GoogleFonts test loading emitted font-fetch warnings and body text used test glyphs, so it is not evidence of final native typography. No physical phone/emulator run or live transaction test was performed.
8. **Debugging / remaining limits / safe practice:** if an editor still shows the old file, close that stale tab and open home_page.dart; saving the old tab can recreate the obsolete source. Check Dashboard imports the new file before restarting. If a result seems missing, inspect both the search query and Showing label, then Reset and clear search. Filters cover catalog type only; they do not add price, availability or service-request submission rules. Practice safely with existing test fixtures: in home_page_test.dart choose Facilities instead of Services and assert Showing Facilities plus the same one-call counts. Run that test, restore the assertion, and manually check320px/large text without editing real records.


## White mobile surfaces - October 18, 2026

1. **Reason:** user requested white backgrounds and containers instead of gray on the recently updated mobile interface.
2. **Files/current anchors:** `campushub/lib/module_app/widgets/home/home_preview_cards.dart:25`, appBackground, and26, surfaceTint. Supporting palette/reference changes: `campushub/DESIGN.md` colors.light/image-surface; `campushub/.impeccable/design.json` surfacePalette and component preview backgrounds; `CAMPUSHUB_CONTEXT.md` latest white mobile surfaces; this guide and mobile-seller-application.md follow-up.
3. **Changes:** both shared surface constants now alias the existing white constant. This changes the Dashboard/Home background (also hosting Profile), seller introduction/form backgrounds, and Home product/facility/service image fallbacks to white. Existing white fields/cards remain white. Thin boundaries and readable navy/gold content remain.
4. **How it works:** DashboardScreen and SellerApplicationPage/Form read appBackground; preview cards read surfaceTint for image/fallback regions. Changing their shared inputs updates those rendered surfaces without local overrides or duplicate color logic. Example: a service without a saved image now has its existing navy icon on white instead of gray; its record and tap destination stay identical.
5. **Backend/API:** unchanged; no request or seller submission behavior changes.
6. **Database/migrations:** none. Hot reload Flutter; no package/server command needed.
7. **Verification:** targeted Dart analysis of shared cards, HomePage, DashboardScreen and both seller screens reported No issues found. No new widget tests, native screenshot, phone check or APK build for this reversible two-constant style change. Prior functional test results do not constitute new visual verification.
8. **Limits/debugging/practice:** this is scoped to shared Home surfaces and seller pages; unrelated modules with independent palettes are not a whole-app theme rewrite. If gray persists, inspect whether that widget consumes these shared tokens before adding overrides. Safe exercise: inspect one no-image fixture and confirm its fallback icon remains visible against white, then compare a recorded image; never replace a real image with a white rectangle. No live data change is needed.


## Marketplace category and seller names - October 18, 2026

1. **Reason:** user requested the category above the seller name and removal of the Seller: prefix from Home marketplace cards.
2. **Exact files/current anchors:** `campushub/lib/module_app/widgets/home/home_preview_cards.dart:270`, conditional product.category, and287, product.seller; `campushub/lib/module_app/screens/home_page.dart:248`, productHeight; `campushub/test/home_test_fixtures.dart:41` and51, test-only categories. Supporting documents: this guide, CAMPUSHUB_CONTEXT.md latest note and campushub/DESIGN.md Layout.
3. **Changes:** card order is product name -> price -> category -> seller name. Category uses a small plain-text line with no label or badge. Seller name keeps the existing secondary text style but loses the Seller: prefix. Removed the unsupported Campus seller fallback; absent seller data stays blank, and missing category does not produce a fake category. White surfaces, card actions and navigation remain.
4. **How it works:** ProductItem.fromJson already maps the real category and seller fields from approved products. MarketplacePreviewCard.build consumes those existing strings; it adds no query or category lookup. The Home productHeight formula now reserves two scaled metadata lines plus their gap so the new category does not overflow the fixed-height horizontal preview. Example: a real category of School Supplies and seller of Ana Student render as two separate lines, in that order. Test fixture category values are isolated rendering inputs, not production catalog rows.
5. **Backend/API:** unchanged. No serializer, endpoint, stock, favorite/cart, seller identity or product-detail logic changed.
6. **Database/migrations:** none. Hot reload Flutter; no server command, dependency or APK rebuild required.
7. **Verification:** `flutter test test/dashboard_header_test.dart test/home_page_test.dart test/dashboard_search_appbar_test.dart --reporter expanded` passed all9 existing tests, including production-card layout at320/390px and2x text, search/filter/retained navigation and empty/error states. Existing isolated fixtures now include categories to exercise the extra line. Targeted Dart analysis of shared cards, HomePage and fixtures reported No issues found. No new test case or physical-device screenshot was created for this small presentation update.
8. **Limitations/debugging/learning:** the change targets Home's MarketplacePreviewCard, not every unrelated product-list/detail layout. Long category/seller strings retain one-line ellipsis; opening product details still shows existing recorded information. If category is absent, inspect the actual API category field instead of adding sample text. Safe exercise: temporarily use a longer category in the existing test fixture, rerun dashboard_header_test.dart and verify no overflow at2x text, then restore the fixture. No real product data needs editing.
