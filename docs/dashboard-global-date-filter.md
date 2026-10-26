# Super Admin global dashboard date filter

Latest explicit update 2026-10-07: Show sample now also previews Booking Overview and Facility Revenue. The existing sample event feeds their fixture data into their existing render functions; Use real data restores saved real objects and global dates/Refresh clear previews. Booking sample grouping is local and does not issue real-data fetches. Most Booked rows now reuse existing saved facility images in the same grouped query, with fallback icons; its sample thumbnails are illustrations. These are later overrides to earlier sample-isolation notes below; backend dates, eligibility and report logic remain real. See [Facility Revenue's current update](facility-revenue.md) for the complete file/line map, functions, actual verification, debugging and safe practice. Practice only in the sample fixture: set booking `previous_total` to 42, verify No change, restore 35, and rerun the preview harness; it demonstrates that a comparison input changes its label without changing global database counts.

Update 2026-10-07: Facility Revenue now consumes `facilities.revenue_overview` (`dashboard_periods.py:257`, `revenue =`). Global resolved current/previous dates feed `facility_revenue_summary(start, end, previous_range)` and its one grouped query over valid paid payments. Output includes real collected total, previous total/comparison, daily amounts and paid-transaction counts. The card updates through global data events, ignores local chart grouping/sample events, preserves its empty baseline, and links to the existing Facilities / Facility Revenue report with matching dates. Shared `valid_facility_payments` is the reason dashboard/report totals agree; it excludes invalid booking states and unpaid/failed/nonpositive records. See [Facility Revenue](facility-revenue.md) for exact file/line anchors, migration impact, actual tests and debugging. Safe practice: add an unpaid payment only in the isolated revenue test fixture, rerun the eligibility test, and verify the collected total does not change; trace query → summary → API → card rather than changing real data.

Update 2026-10-07: Facility Status now consumes `facilities.operational_status` (`views.py:435`) rather than occupancy-based legend buckets. The helper takes already-loaded Facility records and returns current operational counts; it adds no SQL queries. Global requests/Refresh refresh this current snapshot, while historical dates, chart grouping and sample mode do not infer past/occupied facility states. Unknown states and API failures show errors rather than fake zeros; conflict counts remain in Attention Required. See [Facility Status](facility-status.md) for the exact mapping, functions/data flow, current file/line anchors, actual tests, debugging and safe practice exercise.

Update 2026-10-07: Upcoming Reservations receives real rows in the global payload (`dashboard_periods.py:267`, `upcoming_reservations=`). It preserves its current future snapshot: a historical reporting range does not hide today's nearest future Approved reservations. Global requests/Refresh update the snapshot; chart-only grouping does not. The user subsequently requested UI-only samples for Upcoming and Most Booked through the existing sample toggle: fixtures flow from `sales_sample_data.html:172` to card listeners, which save/restore real DOM nodes. Global requests clear these previews; API data stays real. The backend helper's input is current Manila date/time and its output is up to five actual event/stay rows, read with one joined query. See [Upcoming Reservations](upcoming-reservations.md) for current functions/data flow, exact code anchors, actual sample verification results, debugging and safe practice.

Update 2026-10-06: the existing selector now also supports **Previous Month**, spanning the full prior calendar month and comparing with the month before that. `dashboard_periods.py:45` resolves the dates; `global_date_filter.html:11` adds the option. Booking Trend grouping now updates only Booking Overview while global dates/Refresh still update all cards, including Most Booked Facilities. See [the current implementation, functions, tests and debugging guide](most-booked-facilities.md).

Implemented October 4, 2026. The existing dashboard layout and sidebar remain in place. One global selector defaults to **Last 30 Days**, with Refresh, a validated custom-date form, loading placeholders, and an error message with Retry. Period changes and refreshes use fetch; no full-page reload is needed.

## Files and code anchors

All paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`.

| Exact file path | Changed code anchor / purpose |
| --- | --- |
| `backend/core/modules/reports/dashboard_periods.py` | `resolve_dashboard_period`, `comparison_metric`, `build_dashboard_data`: date boundaries, previous-period comparisons, aggregates, snapshot and period payloads |
| `backend/core/modules/reports/views.py` | `admin_dashboard_api`, Super Admin branch in `admin_dashboard_page`, `_facility_dashboard_analytics`, `_booking_reserved_hours`: API access, initial rendering, confirmed payment eligibility, clipped accommodation usage |
| `backend/core/core/urls.py` | `admin_dashboard_api` import and `api/admin/dashboard/` route |
| `backend/templates/dashboard/pages/admin_dashboard.html` | `data-global-dashboard`, `data-dashboard-kpi`, `data-dashboard-secondary`, header filter include, conditional removal of local facility period selector |
| `backend/templates/dashboard/partials/global_date_filter.html` | `dashboardGlobalControls`, `dashboardGlobalFilter`, `dashboardCustomRange`, `dashboardUpdatedAt` |
| `backend/templates/dashboard/partials/sales_overview.html` | Global-dashboard conditionals retain grouping and remove the second date filter; `dashboard-comparison` text |
| `backend/static/components/js/admin_dashboard_filter.js` | `load`, `render`, custom date handlers: fetch, abort superseded requests, refresh/retry, URL preservation and text updates |
| `backend/static/components/js/admin_dashboard.js` | `campushub:dashboard-data` listener updates facilities charts/text; text updates work even if Chart.js is unavailable |
| `backend/static/components/js/admin_sales_overview.js` | Global-mode filter handling and `campushub:dashboard-data` listener update the existing sales chart |
| `backend/static/components/css/admin_dashboard_filter.css` | Header controls, responsive custom-date form, comparison text, skeleton/loading and error styling in navy/gold/white |
| `backend/core/modules/reports/test_dashboard_periods.py` | `DashboardPeriodTests`, `GlobalDashboardTests`: boundaries, payment exclusions, snapshots, role enforcement, performance, midnight and accommodation tests |
| `scratch/dashboard-global-review/check-controls.cjs` | DOM integration verification using rendered test HTML, real frontend scripts and a Chart.js test double |
| `scratch/dashboard-global-review/dashboard.html` | Review snapshot generated only from the isolated Django test database |
| `scratch/dashboard-global-review/payload.json` | API response generated only from the isolated Django test database for DOM verification |
| `docs/dashboard-global-date-filter.md` | This implementation and testing report |

## Backend endpoint and behavior

`GET /api/admin/dashboard/?period=last_30_days`

Custom: `GET /api/admin/dashboard/?period=custom&start_date=2026-10-01&end_date=2026-10-04`

The endpoint returns `period`, `kpis`, `marketplace`, `facilities`, `pending_breakdown`, `grouping`, and `last_updated`. It requires an active authenticated Super Admin with dashboard access. Unauthenticated requests return 401; unauthorized users return 403; invalid periods/dates return 400; non-GET requests return 405. Existing dashboard and domain dashboard routes remain available.

Date boundaries and update timestamps use **Asia/Manila (UTC+8)** without changing the project's global UTC configuration. Custom dates are inclusive. Future end dates and reversed/missing/invalid ranges are rejected, rather than silently swapped.

## Filter-dependent and snapshot sections

| Follows selected period | Remains a current snapshot / independent list |
| --- | --- |
| Total Orders and Total Bookings, including comparisons | Total Users, Active Sellers, Total Products, Total Facilities, Pending Approvals |
| Marketplace Revenue; Sales Overview; Completed Orders; Average Order Value; Sales Trend; Top-Selling Product | Product Categories, which counts current products |
| Booking Overview; Facility Utilization; Most Booked Facility; Facility Revenue | Facility Status and current future schedule-conflict count |
| New users/products/facilities secondary text | Upcoming approved reservations, Recent Activities, Pending Approvals queue, Low Stock Products, Recent Orders |

Refresh fetches KPIs and analytics again using the applied filter. Operational lists retain the existing page's independently queried current records. API/network failures show **Unable to load dashboard data.** and Retry, preserving existing values rather than substituting zeroes. Requests superseded by a newer filter are ignored.

## Comparison rules and manual filter checks

For a reference date of October 4, 2026:

| Select | Current inclusive range | Previous comparison range |
| --- | --- | --- |
| Today | Oct 4 | Oct 3 |
| Last 7 Days | Sep 28–Oct 4 | Sep 21–27 |
| Last 30 Days (default) | Sep 5–Oct 4 | Aug 6–Sep 4 |
| This Month | Oct 1–4 | Sep 1–4 |
| This Year | Jan 1–Oct 4, 2026 | Jan 1–Oct 4, 2025 |
| Custom: Oct 1–4 | Oct 1–4 | Sep 27–30 |

Log in as Super Admin, open `/admin-dashboard/`, and select each option. Check the displayed range, KPI comparison labels, chart dates, and the request to `/api/admin/dashboard/` in browser Network tools. Snapshot totals must remain independent of the selected range. Try a custom range, apply it, and use Refresh: the range must persist and the updated timestamp must advance. Cancel an edited custom range: the applied range must remain unchanged. Reverse the dates: browser validation must block submission; a direct invalid API request must return 400.

Use an empty historical range to confirm the sales empty state. Block the dashboard API in browser tools and click Refresh to check the error/Retry state; unblock it and Retry. Slow the response to check loading placeholders without transient zero values. Change Daily/Weekly/Monthly sales grouping: the global range must remain applied.

Month comparisons clamp to the previous month's final valid day when needed. Year comparisons clamp February 29 to February 28 in non-leap years. A zero previous baseline returns a null percentage and an explicit value increase/no-baseline message; it never invents a percentage. Trend text includes arrows or a no-change marker and comparison wording.

## Revenue, database impact, and assumptions

Marketplace revenue counts only records with both `status=completed` and `payment_status=paid`, dated by `completed_at`, falling back to `paid_at`, then `created_at` for legacy records. Pending, processing, ready but unpaid, cancelled, and completed but unpaid orders do not contribute revenue. Order and booking KPI counts use `created_at` and preserve the existing per-record counting unit.

Facility revenue uses positive recorded `FacilityPayment` rows marked paid on Approved/Completed bookings assigned to a facility, dated by `paid_at` or legacy `created_at` in Philippine time. The shared query supplies daily sums/counts and equivalent-period comparisons for the card and matching Facility Revenue report. Booking amounts never substitute for failed/missing payment queries. Booking Overview and utilization use reservation dates; accommodation usage is clipped to the selected range. The later [Facility Utilization](facility-utilization.md) implementation requires actual configured capacities for each facility type instead of assuming eight hours, room-nights or service capacity.

User totals retain the dashboard's existing `accounts.User` source. Active Sellers includes active, non-suspended legacy Seller users and users with approved seller access, regardless of account type. The original global filter introduced no model/migration changes; the later Facility Revenue update registers one additional GeneratedReport choice through reports migration 0005. It does not edit payment or booking data. Review artifacts contain isolated test fixtures, not production dashboard records. Custom ranges are limited to 3,661 inclusive days and dates from 1900 onward to bound chart construction.

## Verification and remaining limitations

The results below describe the original global-filter implementation. Current Facility Revenue verification includes 93 passing Django checks and eight actual Chrome card renders, documented in [the feature guide](facility-revenue.md). This update also explains current functions, data flow, troubleshooting, migration impact and safe practice above.

- **34 Django tests passed**: new period/API tests, existing Sales Overview tests, and dedicated domain dashboard regression tests. Test database was isolated from production.
- Django system checks passed; JavaScript syntax checks passed; Git whitespace checks passed.
- DOM integration verification passed default selection, presets, tab authentication preservation, KPI/chart updates, custom validation/Apply/Cancel, refresh, loading, failure/Retry, and unavailable-chart-library behavior.
- The design detector reported no findings, but used its degraded regex fallback because HTML parser dependencies were unavailable.
- Live desktop/mobile screenshot verification could not run because no browser surface was available. The DOM test checks behavior, not actual browser layout or Chart.js rendering. No deployment was performed.

Re-run backend verification from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_periods modules.reports.test_sales_overview accounts.tests.DedicatedDomainDashboardTests --noinput --keepdb
```

Re-run the DOM check from the project root (requires the existing `scratch/bundle-qa/node_modules/jsdom` installation and generated review files):

```powershell
node scratch/dashboard-global-review/check-controls.cjs
```

## Dashboard naive datetime crash fix (2026-10-13)

### 1. Cause / reason

The reported `ValueError: localtime() cannot be applied to a naive datetime` was reproduced against the existing database using a read-only Super Admin dashboard request. The traceback reached `admin_dashboard_page()` -> booking activity -> `_format_activity_time(booking.created_at)` -> `timezone.localtime()`.

Read-only schema inspection confirmed Booking's existing `created_at` column is `timestamp without time zone`. Both returned booking timestamps in the inspected recent sample were naive (no timezone). Product/SellerRequest timestamp columns inspected were `timestamp with time zone` and their samples were aware. `USE_TZ=True` does not automatically change the type of an existing unmanaged database table.

Formatting was one issue; sorting activities directly by their original timestamps also mixed naive and aware values. Fixing only the `localtime()` call would leave that comparison vulnerable to a TypeError. The related Facilities Admin pending-request/receipt date formatting had the same unchecked conversion pattern.

### 2. Exact files changed, current lines and nearby anchors

| File, relative to project root | Line / code anchor | Change |
|---|---|---|
| `backend/core/modules/reports/views.py` | 58 `_aware_dashboard_datetime` | Add a read-only normalization helper using Django's configured default timezone |
| same file | 65 `_format_activity_time`; 68 `local` | Normalize before display conversion; keep existing today/yesterday/older label formats |
| same file | 782 pending request `submitted`; 867 recent receipt `date` | Use the helper for related Facilities Admin date labels |
| same file | 1477 `activities.sort` | Normalize the comparison key so mixed source dates sort chronologically |
| `backend/core/modules/reports/test_dashboard_periods.py` | 23 `DashboardDatetimeTests`; 117 legacy dashboard GET; 138 naive request/receipt GET | Three formatter/sort tests and two actual dashboard-render regression cases |
| `docs/dashboard-global-date-filter.md` | this section | Debugging evidence, functions/data flow, tests and learning exercise |
| `CAMPUSHUB_CONTEXT.md` | final `Dashboard legacy datetime fix` entry | Remember the verified cause, default-zone interpretation and scope |

No settings, models, migrations, templates, static assets, permissions or pricing/booking business rules were modified for this fix.

### 3. Changes made

Naive dates are interpreted using `timezone.get_default_timezone()` before calling `localtime()` or comparing activity sort keys. Existing aware dates are returned unchanged, avoiding double timezone conversion. `None` remains `None`; the activity formatter retains its existing blank label for no date. This does not invent timestamps or rewrite model attributes/DB rows.

The Super Admin dashboard activity formatter and sort now work with both legacy booking timestamps and normal aware product/seller/order dates. Related Facilities Admin request/receipt labels use the same helper rather than a second copy of timezone logic. Existing visible date/time formatting, dashboard layout, filters and metrics remain.

### 4. How it works: functions, inputs/outputs and data flow

`_aware_dashboard_datetime(value)` accepts a datetime or None. If naive, it returns a new timezone-aware value in the configured default zone. If already aware or None, it returns the input. It performs no SQL queries or writes. `_format_activity_time(dt)` converts the normalized instant to the current display timezone, then uses the existing Today/Yesterday/older formatting. The activity sorter uses the normalized instant only as a comparison key; original source dates remain untouched.

```python
# Conceptual read/display example; no model save or database update.
legacy = datetime(2026, 10, 13, 9, 0)  # no timezone information
aware = _aware_dashboard_datetime(legacy)
# With existing TIME_ZONE='UTC', aware is 09:00 UTC.
# If the active display zone is Manila, localtime(aware) shows 5:00 PM.
# legacy itself is still naive; no historical data was changed.
```

Data flow: existing PostgreSQL timestamp -> Django Booking object -> helper -> current display conversion / chronological activity sorting -> dashboard template. Analytics period queries and source records are not replaced. Using the configured default zone follows Django's existing interpretation of naive datetimes instead of guessing that every legacy value represents Manila wall time.

### 5. Backend / API behavior

Existing dashboard routes and RBAC remain. Initial `/admin-dashboard/` rendering now succeeds with the observed legacy rows. The same public-to-admin boundaries and period validation remain; invalid filters are not silently accepted and no exception is broadly swallowed to fabricate empty metrics. The dashboard data API uses its existing real queries and was separately verified to return 200.

### 6. Database / migration impact

None. No timestamp column altered, records updated, migration generated, timezone setting changed or seed data inserted. Read-only reproduction/schema checks used the live database. Regression fixture writes used only Django's separate test database.

The observed existing settings remain `TIME_ZONE='UTC'`, `USE_TZ=True`. A timezone-free value cannot tell us its original geographic timezone; the fix uses the configured default, without claiming to reconstruct missing historical information.

### 7. Tests performed, debugging and commands

- Before the change, the live read-only Super Admin dashboard GET reproduced the exact ValueError at booking activity formatting.
- After the change, authenticated read-only requests against the existing database returned **HTTP 200** for Super Admin, Facilities Admin and Marketplace Admin dashboards and `/api/admin/dashboard/`.
- **149 Django dashboard/report regression tests passed**, covering periods, booking summaries, upcoming/ranked facilities, revenue, system health, marketplace charts and utilization.
- Added three tests verify naive/default-zone interpretation without input mutation, aware/None preservation, current display timezone and existing label formats, and mixed-date sorting. Two dashboard-render tests emulate naive Booking/Payment reads from legacy SQL columns, checking actual template rendering, mixed activity sorting and Facilities Admin request/receipt labels.
- Django system check clean; migration dry run reported No changes detected. No UI/browser layout test was rerun because no template/CSS/JavaScript was changed.

During verification, a test initially expected the older-date label to omit its hour's leading zero. Inspection confirmed the existing formatter returns that zero for older dates, so the test expectation was corrected instead of changing unrelated display behavior.

Commands from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
venv/Scripts/python.exe manage.py test modules.reports.test_dashboard_periods modules.reports.test_dashboard_bookings modules.reports.test_upcoming_reservations modules.reports.test_facility_revenue modules.reports.test_dashboard_health modules.reports.test_dashboard_marketplace modules.reports.test_sales_overview modules.reports.test_most_booked_facilities modules.reports.test_dashboard_utilization --keepdb --noinput
```

No `migrate` is required. Django's development server should reload changed Python; restart it if it did not. Refresh `/admin-dashboard/`, verify Recent Activities loads and newest records remain first, then verify Facilities Admin pending requests/receipts and dashboard Refresh/date filters.

If the ValueError persists, inspect the application frame immediately above `django.utils.timezone.localtime()` in the full traceback. Confirm the running interpreter/workspace and helper change at line 68 rather than editing Django's installed timezone.py. Check `timezone.is_naive(value)` on the specific source timestamp; do not disable `USE_TZ` or delete bookings to hide the error. If a different page has another naive conversion, reproduce that specific path before broadening this fix.

Safe practice: in a local Python shell, create one naive datetime and one aware datetime with the same intended instant. Observe that direct comparison fails before normalization, then compare using the helper. Check that the original naive input stays unchanged. Next rerun `DashboardDatetimeTests`; experiment only with test inputs, not production columns or actual reservation dates.

### 8. Remaining limitations

This is a read/display compatibility fix, not a migration of all legacy timestamps. It does not infer unknown historical timezone intent or change unrelated modules' datetime handling. Existing legitimate aware dates preserve their meaning. No physical-phone or deployed-production check was performed; live local dashboard/API reads and regression tests were verified.
