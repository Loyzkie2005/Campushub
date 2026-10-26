# CampusHub dashboard Improvement #4: Attention Required

Implemented a compact current-operations list for the Super Admin dashboard, between System Overview and System Status. Counts come from Django database records and do not change when a historical reporting period is selected. The latest update below replaces the earlier decision to retain the bottom Pending Approvals card.

## Latest update: consolidate approvals into Attention Required — 2026-10-07

### 1. Cause / Reason

Confirmed by inspection: `build_attention_required` already supplied pending product reviews, seller applications and booking requests. The bottom `pendingApprovalsSlot` repeated these queues, while its links were less specific. Reuse the existing operational summary rather than adding approval queries or changing workflow rules.

### 2. Exact Files Changed / Lines / Nearby Anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 438 `{% if not global_dashboard %}`; 441 `pendingApprovalsSlot`; 595–596 scripts | Exclude the entire bottom approval row from the Super Admin page, preserve legacy dashboards, and update two JS cache versions. Recent Activities remains the final visible section. |
| `backend/core/modules/reports/dashboard_attention.py` | 44 `build_attention_required`; 54–58 definitions; 64 `if count > 0` | Reuse counts and routes; label Review Products / Review Sellers / Review Bookings / View Facilities explicitly; require positive counts. |
| `backend/templates/dashboard/partials/attention_required.html` | 21 `dashboardAttentionData` | Supply existing attention data as safely escaped Django JSON for the initial client snapshot. |
| `backend/static/components/js/admin_dashboard_filter.js` | 143 `attentionItems`; 145 system-status listener; 156 `renderAttention` | Merge the existing real health warning into the existing compact list; hide zero-count response rows and update all-clear correctly. |
| `backend/static/components/js/admin_system_status.js` | 15 `render`; 16 `campushub:system-status` | Publish the existing health result for Attention Required; no additional request. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 291 `test_attention_uses_current_issues_and_existing_routes`; 320 removal assertions | Verify removed bottom card, retained activities, positive counts and explicit action labels. |
| `scratch/dashboard-global-review/check-attention.cjs` | `dashboard` assertions and `health` helper | Verify real markup, refresh/zero/health transitions, authenticated routes and destination filters. |
| `scratch/dashboard-global-review/check-system-status.cjs` | fixture inputs, healthy/failed/unknown assertions | Use current fixture output; verify the actual health controller publishes warnings. Align its outdated green color expectation with the existing navy CSS; application colors were not changed. |
| `scratch/dashboard-global-review/verify-attention-visual.cjs` | Chrome invocation before assertions | Render current previews before checking them, rather than inspecting old browser dumps; align the old red-warning assertion with existing gold CSS. |
| `CAMPUSHUB_CONTEXT.md`; this guide | Latest consolidation note | Preserve the accepted layout and explain functions, debugging and testing. |

### 3. Changes Made

Remove the entire bottom Pending Approvals section on the global Super Admin dashboard. Keep the top Pending Approvals KPI because this request removes the separate bottom section, not that KPI. Keep Recent Activities last. No new cards, pages, styles or status fields are added.

Attention Required continues to show nonzero Low Stock, Out of Stock, pending reviews/applications/requests, conflicts, maintenance and temporary-unavailability counts. Singular/plural wording follows the count. One compact Backup Warning row appears only when the existing backup check reports `warning`, `failed` or `no_backup_available`. Its count represents one verified backup-service issue, not a fabricated number of backup records.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

`build_dashboard_data` supplies its existing current product/seller/booking/facility counts to `build_attention_required`. That function returns count fields plus `items` containing `key`, `count`, `label`, `action`, `url` and `severity`. It adds only positive-count items. The initial Django partial renders those rows and safely exports the same object through `json_script`; no approval query is duplicated.

The existing global dashboard refresh calls `renderAttention(attention)`. It stores positive operational items, combines them with any verified backup warning, and builds safe DOM nodes using `textContent`. It hides `No urgent items require attention.` whenever any row exists. The existing loading/error/Retry behavior remains; a dashboard request failure retains the previous successful rows.

System Status still makes its existing `system_status_only=1` request. Its `render(statuses)` publishes `campushub:system-status`. Attention listens to this result and reuses the existing Backup link: healthy removes the warning, warning/failed/no-backup adds one, and unknown retains any last verified warning rather than falsely clearing it. This prevents asynchronous health and dashboard responses from overwriting each other's rows. Date filters and sample previews do not fabricate operational or health counts.

Annotated example of the count rule:

```python
# Inputs: real aggregate counts, not example records inserted into the database.
count = counts[key]
if count > 0:  # Zero issues need no actionable row.
    items.append({"key": key, "count": count, "label": label, "url": url})
```

The example abbreviates the actual item fields. The chosen approach reuses one source of approval truth, existing template rows and existing health calls.

### 5. Backend / API Behavior / Existing Routes

No new endpoint or approval logic. API attention counts remain current operational snapshots, independent of historical global reporting ranges. Products needing review retain the existing exclusion of Super Admin-created listings. All permissions and route handling remain server-enforced.

| Action | Existing URL / filter |
| --- | --- |
| View Inventory | `/admin-products/?inventory_status=low_stock` — the existing Inventory destination |
| Review Products | `/admin-products/?status=pending` |
| Review Sellers | `/admin-sellers/?status=pending` |
| Review Bookings | `/admin-bookings/?status=pending` |
| View Facilities, maintenance | `/admin-facility/?status=maintenance` |
| Open Backup | `/admin-backup/` — reused from System Status |

Retain existing Out of Stock Inventory, Calendar conflict and temporarily-unavailable facility links as well. Initial session navigation and refreshed same-origin links preserve current authentication. Backup health is merged client-side from the existing separate health response; it is not added to the approval API's database counts.

### 6. Database / Migration Impact

No migrations, schema changes, production data writes or new query. Legacy role dashboards retain their bottom cards. Existing backend context keys remain compatible with other consumers.

### 7. Tests Performed / Manual Test Steps

- **31 Django tests passed**: `modules.reports.test_dashboard_periods`, including real counts, current/historical consistency, creator/archived exclusions, destination filters, access rules, removal assertions and query budget. System check found no issues.
- `check-attention.cjs` passed: removed card, Recent Activities last, positive-only rows, action links/authentication, real Products shortcut filters, refresh/loading/error/Retry and warning/failed/no-backup/healthy/unknown transitions without duplicate warning rows.
- `check-system-status.cjs` passed using both real controllers: existing health request, healthy/error states, timeout, races and independent dashboard/health responses. Its initial run found an obsolete color assertion in the harness; updating it to the existing navy CSS resolved that test issue without changing application styling.
- Four Chrome layout checks passed: desktop, narrow 342px content, empty and loading states; eight operational rows fit without horizontal overflow. JS syntax and targeted whitespace checks passed.

Manual: refresh Super Admin Dashboard. Confirm Attention Required is above System Status and Recent Activities is the last section, with no bottom Pending Approvals card. With real pending records, follow each Review action and confirm the corresponding Pending filter is active. Verify low stock and maintenance shortcuts activate their existing filters. Resolve a pending item through its normal workflow and click Refresh; its count updates or its row disappears. When all operational counts are zero and backup is healthy, the exact all-clear text appears. A verified backup warning keeps the list nonempty until a healthy result. Do not create fake production records solely to test these displays.

### 8. Remaining Limitations / Debugging / Safe Practice

Tests use isolated Django records, rendered HTML and browser/DOM harnesses; a logged-in production workflow was not clicked. Backup warning arrives after the existing asynchronous health request, not during initial Django rendering. If health becomes unknown, a previous verified warning remains until health is successfully rechecked; inspect System Status for current verification details. Operational rows remain the existing current snapshot, not historical queue counts.

If the bottom card remains, check you are on the global Super Admin page and refresh its HTML. If counts do not match expected reviews, inspect `pending_reviews` eligibility rather than copying `pending_breakdown` and creating a second rule. If a filter fails, check the action's query parameter and existing module filter before adding any route. If Backup duplicates, check that the health listener stores a single `backupAttention` object and that dashboard refresh merges it once.

Safe practice: in an isolated copy of the test response, set one item's `count` to zero and refresh the DOM harness. Verify that row disappears while other rows remain. Restore the fixture and rerun `node scratch/dashboard-global-review/check-attention.cjs`. Then read `test_attention_uses_current_issues_and_existing_routes` to connect saved records to API counts and visible links. Never edit production records or hardcode UI counts for this exercise.

---

## Original implementation reference

## Cause / reason

The dashboard had detailed operational information lower down, but no compact set of shortcuts near its KPIs. During verification, a real pending seller request also exposed an existing rendering error: the dashboard tried to read `SellerRequest.department_id`, although department belongs to its linked user. That lookup is corrected.

## Exact files changed

Approximate current lines and nearby anchors:

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_attention.py` | 15 `super_admin_created_products`; 22 `inventory_attention_counts`; 44 `build_attention_required` | New current-issue summary, stock queries, creator exclusion and existing-route shortcuts. |
| `backend/core/modules/reports/dashboard_periods.py` | 155 `pending_reviews`; 163 `active_maintenance`; 251 `attention_required` | Extend existing aggregates and dashboard response. |
| `backend/core/modules/reports/views.py` | 1273 pending seller loop; 1532 `attention_required` | Supply template context and read seller department through `user`, with `select_related`. |
| `backend/templates/dashboard/partials/attention_required.html` | 1 section; 5 item loop; 16 empty state | New compact list, labelled actions, SVG indicators, empty and loading states. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 179 include; 16/611 asset versions | Place section after KPIs; refresh cached CSS/JS versions. |
| `backend/static/components/css/admin_dashboard_filter.css` | 22 `.dashboard-attention` | Scoped layout, typography, severity icons, focus, loading and responsive rules. |
| `backend/static/components/js/admin_dashboard_filter.js` | 59 `renderAttention`; 101 render call | Refresh list with safe DOM/text construction and preserve tab authentication on links. |
| `backend/static/components/js/admin_products.js` | 2580 `shortcutParams` | Initialize the existing status/inventory filters from dashboard shortcut parameters. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 986 script include | Update JS cache version. |
| `backend/core/accounts/views.py` | 832 `facility_status_filter`; 1148 `booking_status_filter` | Pass requested filters to existing module controls. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 112 status option | Preselect the matching facility status before existing filtering runs. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 96 pending option | Preselect the existing Pending booking filter. |
| `backend/core/modules/reports/test_dashboard_periods.py` | `test_attention_*` methods | Database-backed counts, eligibility, routes, states, query bounds and review artifacts. |

QA scripts and generated isolated-fixture HTML/JSON/screenshots are in `scratch/dashboard-global-review/`: `check-attention.cjs`, `prepare-attention-visual.cjs`, and `verify-attention-visual.cjs`. They do not provide application metrics.

## Changes made / how it works

Only positive-count rows render. Each has an 18px bold count, 13px description and 12px semibold action, on one white bordered surface. Current CSS uses gold icons for stock/review attention, out-of-stock and booking conflicts; facility-status icons use navy. The label supplies meaning without relying on color.

| Item | Real source / eligibility | Existing route and filter |
| --- | --- | --- |
| Low Stock Products | Nonarchived products classified `low_stock` by existing stock/option/expiry rules and configured threshold. | `admin_products_page`, `inventory_status=low_stock`; this is also the existing sidebar Inventory destination. |
| Out of Stock Products | Nonarchived products classified `out_of_stock` by the same rules. | `admin_products_page`, `inventory_status=out_of_stock`. |
| Pending Product Reviews | Nonarchived, `approval_status=pending`, excluding Super Admin creators by `is_superuser` or role. For legacy missing creators, exclude Super Admin owners. | `admin_products_page`, `status=pending`. |
| Pending Seller Applications | Actual `SellerRequest.status=pending`. | `admin_sellers_page`, `status=pending`. |
| Pending Booking Requests | Actual `Booking.status=pending`. | `admin_bookings_page`, `status=pending`. |
| Booking Conflicts | Existing overlap-pair helper for pending/approved bookings dated today or later, on the same facility/date with intersecting times. | `admin_calendar_page`. |
| Facilities Under Maintenance | Nonarchived `availability_status=maintenance`. | `admin_facility_page`, `status=maintenance`. |
| Temporarily Unavailable Facilities | Nonarchived `availability_status=unavailable`. | `admin_facility_page`, `status=unavailable`. |

Singular/plural labels follow the count. The action link includes an accessible description, such as “Review: Pending Seller Application.” Existing Products, Bookings and Facilities UI filters are reused; no duplicate Inventory page is added. Initial links use the existing admin session navigation handler; refreshed links also preserve the current `__at` parameter.

## Backend / API behavior and queries

The existing Super Admin-only `GET /api/admin/dashboard/` now includes `attention_required`: eight integer counts and an `items` array containing only nonzero rows with `key`, `count`, `label`, `action`, `url`, and `severity`. The initial page uses the same service.

Existing product and facility aggregates now also count eligible pending reviews and nonarchived maintenance/unavailable facilities. Pending seller/booking counts and the existing current booking-conflict calculation are reused.

Inventory adds two queries per summary:

1. An ORM aggregate counts simple products with empty option JSON, respecting the configured low-stock threshold and existing perishable-category expiry precedence. Category whitespace is trimmed as in the classifier.
2. Nonempty option JSON products stream only stock/category/expiry/customization fields in chunks of 500 through `get_product_inventory_status`. JSON options require the existing per-option classifier; there are no per-product related queries and no whole model-table cache.

Stock is already decremented by `adjust_product_stock` when orders reserve it. No outstanding-order quantity is subtracted again. No inventory or approval business rules are changed. Other role dashboards, authentication, permissions, marketplace payment handling and FastAPI remain unchanged.

Database exceptions propagate through the existing endpoint failure path. They are not converted into zero issue counts.

## Empty, loading, error and responsive behavior

- **Empty:** show the compact check icon and “No urgent items require attention.” only after a successful zero-issue result, including initial server render.
- **Loading:** hide the previous list and all-clear message while `aria-busy=true`; show “Loading attention items…” using the existing refresh lifecycle.
- **Error:** keep the last successful data and use the dashboard-level error and Retry controls. Once loading ends, previous rows are visible again.
- **Refresh/filter changes:** replace the list from the new response, removing resolved items. Reporting dates never filter operational counts.
- **Desktop:** horizontal rows with right-aligned actions, approximately 48–49px high including separators.
- **Small screens:** actions stack under their labels; counts stay visible and labels can wrap. Borders and icons remain restrained.

## Database / migration impact

No schema, model, migration, or production-data change. No new endpoint, status field or inventory model. No fake operational data or backup-warning count.

## Tests performed

- **48 Django tests passed:** `modules.reports.test_dashboard_periods`, `modules.reports.test_sales_overview`, and `accounts.tests.DedicatedDomainDashboardTests`, using the isolated test database.
- New checks cover all eight real issue types; identical operational counts for Today and historical custom dates; Super Admin creator/legacy-owner exclusion; archived products/facilities; pending-only requests; threshold configuration; stock already reduced by reservation; JSON variants; expiry precedence; touching, cancelled and past bookings; all-clear; existing route filters; and inventory-query failure propagation.
- Inventory counting stays at **two queries** after adding 20 variant products. The existing full-dashboard query-bound test still passes below 20 queries and remains constant as orders grow.
- `check-controls.cjs` passed existing dashboard period, charts, grouping races, refresh, loading, error/Retry and authentication checks.
- `check-attention.cjs` passed real HTML/API list refresh, nonzero rows, empty/loading/failure states, retained last data, Retry, accessible links and actual Products filter/clear behavior.
- JavaScript syntax and CSS parsing passed; `git diff --check` passed. The design detector fell back to limited regex checks, so it is not treated as full visual verification.
- Offline headless Chrome screenshots were inspected for desktop, narrow layout, empty and loading states. Measured list content widths were 1536px desktop and 342px inside a 390px frame; no horizontal overflow. All eight supported rows rendered. Empty/loading sections stayed compact.

## How to manually test every item

Use a development/test database with real saved records. Log in as Super Admin, open Dashboard, and refresh after each change.

| Item | Manual check |
| --- | --- |
| Low stock | Set an active product's available stock to a positive quantity at or below the configured threshold (default 5). The row appears; View Inventory opens the Low Stock filter. Restock above the threshold and refresh to remove it. For variants, verify option stock using the existing inventory classification. |
| Out of stock | Set active stock to 0, or all tracked variant quantities to 0. Verify the red indicator and Out of Stock shortcut. Restock and refresh. An expired perishable follows the existing Expired status instead. |
| Pending products | Submit a product as a seller so it is genuinely pending. Verify Review opens Pending products. Approve/reject and refresh. New Super Admin-created products are autoapproved by the existing creation flow and do not add pending review attention; the regression test also covers old pending admin-created records. |
| Pending sellers | Submit an actual seller-access application. Verify its count and Review destination. Approve/reject the application and refresh to remove it. Check the dashboard loads even when department is unset. |
| Pending bookings | Submit a real pending facility booking. Verify Review opens the Pending filter. Complete its approval/rejection/cancellation workflow and refresh. |
| Booking conflicts | Use existing overlapping pending/approved time-slot records in a development database, or run `test_attention_uses_current_issues_and_existing_routes`, which creates the isolated overlap fixture. Verify Resolve opens Calendar. Resolve/cancel the overlapping record and refresh. Adjacent slots are not overlaps. Do not bypass production booking validation to manufacture a conflict. |
| Maintenance | Set a nonarchived facility to Under Maintenance. Verify View preselects that filter. Restore Open for Booking and refresh. |
| Temporarily unavailable | Set a nonarchived facility to Temporarily Unavailable. Verify View preselects that filter. Restore its status and refresh. |

Select Today, Last 30 Days and a historical Custom Range: the current attention items should stay identical unless records changed meanwhile. Resolve all supported issues and verify the all-clear message. With browser network throttling, click Refresh and confirm no all-clear message appears during loading. Simulate a failed request, confirm the previous list remains with dashboard Retry, then restore the connection and retry. Check a narrow window: actions stack without clipping.

## Remaining limitations

- Conflict attention intentionally inherits the existing same-day/time-slot overlap-pair detector. It does not add new room-night, resource, or other conflict algorithms; Calendar opens its existing default view.
- Backup/system warnings are omitted because this dashboard has no established warning summary to reuse.
- Legacy pending products with a missing creator are attributed conservatively using their owner; no creator history is fabricated and no old records are rewritten. The general Products Pending filter still represents that module's existing pending listing set.
- Variant JSON still requires a streamed classifier pass proportional to the number of option-bearing products. Database query count is bounded; this does not claim constant CPU time.
- Browser QA used isolated rendered fixtures and actual project CSS/JS. There was no connected authenticated interactive browser. The narrow check constrains a 390px frame in Windows headless Chrome; it is not a physical mobile-device test. External font imports were disabled for offline screenshots; the application retains its existing Montserrat font setup.

Local review images: `scratch/dashboard-global-review/attention-desktop.png`, `attention-mobile.png`, `attention-empty.png`, and `attention-loading.png`.
