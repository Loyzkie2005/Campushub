# Facility Revenue — implementation and learning guide

## Latest update: fill the space beside Facility Revenue — 2026-10-07

### 1. Cause / Reason

Confirmed in the template: five compact Facilities Analytics cards used three equal columns. Facility Status and Facility Revenue occupied only two columns on the last row, leaving the right third empty. This was a layout issue, not missing revenue data.

### 2. Exact Files Changed / Current Lines and Anchors

| File, relative to project root | Line / nearby anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 336 wrapper before `upcoming_reservations.html` | Upcoming Reservations fills a medium-width row; retains one third on wide screens. |
| Same template | 356 wrapper before `facility_status.html`; 380 wrapper before `facility_revenue.html` | Make these two cards equal halves of the final Super Admin row. |
| `scratch/facility-previews/check-spacing.cjs` | 1 browser verification harness | Verify the actual rendered five-card layout with empty and sample data. |
| `docs/facility-revenue.md` | 3 this update | Explain the confirmed cause, grid behavior and checks. |

### 3. Changes Made

The Super Admin layout is now three cards followed by two equal-width cards on wide screens. At medium widths, Utilization and Most Booked share a row, Upcoming Reservations fills the next row, then Status and Revenue share a row. Below 992px, cards stack. Card order and internal content remain the same. The existing domain-specific dashboard keeps its previous grid.

### 4. How It Works / Inputs, Outputs and Data Flow

Bootstrap divides a row into 12 columns. `col-lg-6` means half the row starting at 992px. The old `col-xl-4` overrode that at 1200px, making each card one third. Removing that override for the final two Super Admin cards gives **6 + 6 = 12**, filling the row.

```django
{# Input: global_dashboard from the existing Django view. #}
{# Super Admin: half-width at lg and above. Other dashboard: xl thirds. #}
<div class="col-12 col-lg-6{% if not global_dashboard %} col-xl-4{% endif %} d-flex">
```

The existing backend still supplies actual status/revenue objects to Django partials and global date refresh events. The existing JavaScript `render` functions display those objects, and Chart.js resizes its chart to the wider parent. This update changes the parent grid classes only; it adds no revenue calculation or API function. This approach fills the space without introducing a new container or duplicating styles.

### 5. Backend / API Behavior

No endpoint, date-filter, status, payment, sample-toggle or report behavior changed.

### 6. Database / Migration Impact

No schema changes, migrations, or production data writes.

### 7. Tests Performed / Manual Steps

- Existing Django `test_card_markup_export_empty_populated_and_single_day` passed: **1 test**, system check reported no issues.
- `node scratch/facility-previews/check-spacing.cjs` passed **6 actual Chrome renders**: empty and sample states at 1440px, 1100px and 500px. Checks verified the revenue row reaches the right edge, half-width cards align, medium-width Upcoming Reservations fills its row, narrow cards stack, charts initialize and content does not overflow.
- Targeted `git diff --check` passed.

Manual: refresh Dashboard and scroll to Facilities Analytics. On a wide screen, Facility Status and Facility Revenue should share the complete final row equally. Toggle Show sample / Use real data, hover the revenue line, then resize the browser to confirm the medium and stacked layouts.

### 8. Remaining Limitations / Debugging / Safe Practice

Chrome checks used actual Django-rendered fixture markup and local scripts, not a logged-in live dashboard session. If the space remains, inspect the Status/Revenue wrapper classes: on the Super Admin page they should contain `col-lg-6` without `col-xl-4`. Refresh the page to load the updated HTML. If a card appears wider but the chart does not, inspect its parent width and Chart.js resize handling before changing backend calculations.

Safe practice: in a copy of `scratch/facility-previews/spacing-sample.html`, temporarily change a final wrapper from `col-lg-6` to `col-lg-4`. Open the copy at a wide width and observe how two thirds leave space. Restore `col-lg-6`, verify both cards fill the row, then run the spacing harness again. Do not edit real records or the application template for this exercise.

---

## Previous update: requested facility previews and ranking images — 2026-10-07

This later explicit request permits temporary samples in Facility Revenue and Booking Overview. It overrides the earlier statement that Facility Revenue ignores sample events. Real backend payment eligibility and calculations remain unchanged.

### 1. Cause / Reason

The existing Show sample control previewed marketplace cards, utilization, rankings and upcoming reservations, but not Booking Overview or Facility Revenue. Most Booked Facilities also displayed names/counts without the existing Facility image field. Inspection confirmed these missing connections.

### 2. Exact Files Changed / Current Lines and Anchors

| File, relative to project root | Current approximate line / anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/sales_sample_data.html` | 172 `facility_samples`; 179 `booking_overview`; 191 `revenue` | Add preview booking vectors and revenue/date/count arrays; add four ranking thumbnail URLs. |
| `backend/static/components/js/admin_booking_overview.js` | 139 `previewLinks`; 145 `clearSample`; 151 `sampleForGrouping`; 185 `showSample`; 196 sample event | Save real overview, derive sample totals and grouping, disable navigation during previews, restore real state and clear previews on global requests. |
| `backend/static/components/js/admin_facility_revenue.js` | 9 `clearSample`; 34 `render`; 102 sample event | Save/restore the real revenue object; render the requested fixture through existing validated chart logic; disable the report link in sample mode. |
| `backend/templates/dashboard/partials/booking_overview.html` | 1 `bookingOverviewCard`; 3 sample note | Add control target ID and small Sample preview label. |
| `backend/templates/dashboard/partials/facility_revenue.html` | 2 `facilityRevenueCard`; 4 sample note | Add control target ID and label. |
| `backend/templates/dashboard/partials/sales_overview.html` | 11 `aria-controls` | Include both cards in the existing Show sample control's targets. |
| `backend/core/modules/reports/dashboard_bookings.py` | 54 `most_booked_facilities`; 65 `facility_image=Max(...)`; 69 `image_url` | Reuse the uploaded first Facility image without introducing another database query. |
| `backend/templates/dashboard/partials/most_booked_facilities.html` | 9 `facility-ranking-image` | Render the initial thumbnail and missing-image fallback. |
| `backend/static/components/js/admin_most_booked_facilities.js` | 28 thumbnail; 33 fallback; end-of-file initial image listeners | Build safe image/name/count DOM on refresh and preview; hide broken images and show the existing icon. |
| `backend/static/components/css/admin_most_booked_facilities.css` | 8 thumbnail grid | Align 40px thumbnail, name/rank and right-aligned count. |
| `backend/static/components/css/admin_booking_overview.css` | End-of-file `[aria-disabled="true"]` rule | Preserve existing card/KPI/bar styling and use a default cursor for disabled links. |
| `backend/static/components/css/admin_facility_revenue.css` | 16 disabled link; 17 sample sizing | Allow room for the short preview label and keep the footer inside the card. |
| `backend/static/assets/img/samples/facility-court.svg` | 1 SVG | Add a small court illustration, only used by sample ranking. |
| `backend/static/assets/img/samples/facility-hall.svg` | 1 SVG | Add sample hall illustration. |
| `backend/static/assets/img/samples/facility-hostel.svg` | 1 SVG | Add sample hostel illustration. |
| `backend/static/assets/img/samples/facility-training.svg` | 1 SVG | Add sample training/assessment illustration. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 20/22/25 CSS; 587/590/591 JS | Update cache versions so browsers load changed assets. |
| `backend/core/modules/reports/test_most_booked_facilities.py` | 68 `test_images_reuse_first_uploaded_image_in_one_query_and_initial_html` | Verify JSON-image selection, initial markup, blank images and one-query ranking. |
| `scratch/facility-previews/check-card.cjs` | 1 integration harness | Check toggles, local grouping, disabled links, exact restoration, images, failure/retry and previews from empty real data. |
| `scratch/facility-previews/check-browser.cjs` | 1 Chrome harness | Render actual controllers/Chart.js and all three cards with loaded SVG thumbnails. |
| `scratch/facility-revenue/check-card.cjs` | Sample-event assertions | Update earlier sample-isolation expectations to the newly authorized preview behavior. |
| `CAMPUSHUB_CONTEXT.md` and guides `docs/facility-revenue.md`, `docs/booking-overview-implementation.md`, `docs/most-booked-facilities.md`, `docs/dashboard-global-date-filter.md` | Latest preview/image notes | Preserve accepted behavior and explain functions, inputs/outputs, tests, debugging and safe practice. |

### 3. Changes Made

Click **Show sample** in Sales Overview. Facility Revenue shows **₱48,750.00**, an illustrative 14% comparison, a seven-day navy line and 17 paid transactions. Booking Overview shows **42** requests: Pending **6**, Approved **18**, Completed **14**, Rejected/Cancelled **4**, with a stacked bar chart. The previously requested Completed-green / Rejected-red chart exception is preserved. Most Booked Facilities displays four illustrative thumbnails and its existing counts 24/18/12/8. These thumbnails are local SVG illustrations, not claimed photographs of real facilities.

All preview cards show **Sample preview**. Use real data restores actual amounts/counts/rows and empty states. Global dates/Refresh clear previews and request actual records. Booking and report links are disabled while these two cards display samples so example values cannot become reports or open misleading real-record filters.

### 4. How It Works / Functions and Data Flow

`sales_sample_data.html` is the input fixture. The existing Sales toggle dispatches `campushub:marketplace-sample`, which passes `facility_samples` to each card. No sample API endpoint is added.

`sampleForGrouping(grouping)` takes the sample's date range and daily status vectors. It validates dates/counts, adds each day's statuses, groups into daily, seven-day or calendar-month buckets, then returns the same overview shape expected by the existing `render`. Status totals and the chart always add to 42. The capture-phase change handler stops the real API grouping handler while a preview is active; weekly/monthly grouping does not fetch or overwrite samples. `clearSample(restore)` resets preview state and renders the saved real object when requested.

Revenue stores its real object in `realSnapshot`, then passes the fixture into the existing `render` validator. Its daily values sum to 48,750 and daily transaction counts sum to 17. On exit, its actual chart/comparison and report access return. Global loading/errors discard the preview.

Ranking data now includes `image_url`. The existing grouped query adds `Max('facility__image_url')`, then the existing `Facility.get_first_image_url()` parses a plain URL or JSON image list in Python. Constructing this unsaved Facility object does not execute SQL. Initial Django markup and JS refresh both show 40px thumbnails; a missing/broken image shows a small existing calendar icon. Names use escaped template output or `textContent`, rather than untrusted HTML.

Annotated sample calculation:

```javascript
// The first sample day's request counts: 1 + 2 + 1 + 0 = 4.
const day = {pending: 1, approved: 2, completed: 1, rejected_cancelled: 0};
// Grouping sums these same values; it changes the bars, not the KPI totals.
const count = Object.values(day).reduce((sum, value) => sum + value, 0);
```

This approach reuses the actual card renderers and one existing toggle, rather than duplicating cards, routes or payment logic. Booking Overview counts request creation; Most Booked counts valid reservation usage. Their independently illustrated counts are not expected to sum to the same value.

### 5. Backend / API Behavior

Real revenue/status/date calculations and all permissions are unchanged. Most Booked's existing API rows gain `image_url`, drawn from the existing facility field. Its ranking still uses Approved/Completed usage and the global dates, limited to five, in one grouped query. Samples never enter this API or its report query. Real mode still uses normal server-side chart grouping; preview mode groups its fixture locally.

### 6. Database / Migration Impact

No migration, schema change, or production booking/payment/facility writes in this update. Existing report migration 0005 was part of the earlier revenue implementation. The image field is reused; nothing is copied into a new table or field.

### 7. Tests Performed / Manual Steps

- **42 Django tests passed** for Most Booked/image selection, global date rules and query budget; two focused current template-export tests also passed as part of the earlier 13-check targeted run.
- Node combined preview integration passed 42/status sums, ₱48,750/tooltip transaction counts, Daily/Weekly/Monthly grouping with zero preview fetches, disabled links, exact real restoration, empty-real restoration, global errors/Retry and image fallback.
- Existing revenue and upcoming preview DOM checks passed, including exporter preservation of `facility_samples`.
- Two actual Chrome sample layouts passed at 1200/500 viewport widths: all cards fit, actual bars/line sum correctly and all four sample thumbnails loaded. Wide screenshot inspected visually.
- JS syntax and targeted whitespace checks passed. All three changed JS assets and the four SVG thumbnails returned HTTP 200 from the local server.

Manual: refresh Dashboard, click Show sample in Sales Overview and scroll to Facilities Analytics. Verify values above and image thumbnails. Change Booking grouping; the total remains 42. Hover revenue on Oct 03, 2026: Revenue ₱12,500 / Paid Transactions 3. Click Use real data; values return to your database. Change global date/Refresh to verify previews clear. In real mode, a ranked facility's first uploaded image should appear. Remove its image only in an isolated test fixture to verify fallback.

### 8. Limitations / Debugging / Safe Practice

Sample dates are Sep 29–Oct 05, 2026, matching the existing marketplace preview, not the currently applied real reporting range. Missing real uploads cannot produce real photos; the icon fallback is intentional. Preview images are illustrations. Tests used actual Django fixture markup and local Chart.js in Chrome, not a logged-in live booking session.

If samples do not appear, confirm `facility_samples.booking_overview` / `.revenue` exists in the page JSON, check new JS requests and clear stale cached assets with a hard refresh. If grouping fetches while previewing, inspect `sampleSeed` and the capture-phase change listener before changing the global backend. If a real image is missing, check the facility's saved first URL and that its media request succeeds; do not substitute sample artwork for real records.

Safe practice: in the sample booking fixture only, change `previous_total` from 35 to 42. Toggle the preview and verify **No change** while all current counts/bar sums stay 42. Restore 35, rerun `node scratch/facility-previews/check-card.cjs`, then inspect `test_images_reuse_first_uploaded_image_in_one_query_and_initial_html` to learn how one saved image is selected without adding SQL queries. No real data is edited.

---

Updated 2026-10-07. Scope: the Super Admin Dashboard Facility Revenue card and an additional Facility Revenue option on the existing Generate Reports page. Amounts come from actual records; test examples are confined to the isolated test database and scratch browser files.

## 1. Cause / Reason

Confirmed by inspection: the old shared dashboard payment query checked `payment_status=paid` but did not exclude rejected/cancelled bookings. It returned only revenue values, without daily transaction counts or a previous-period comparison. The card's reports link did not select a report or dates. The existing Payments & OR report filtered creation dates and included unpaid/failed records for auditing; it therefore could not serve as a matching collected-revenue report.

The new shared eligibility function prevents divergent rules. The existing all-payment audit report remains available. UI/UX Pro Max's trend-over-time recommendation supports the simple line chart; CampusHub colors and the user's request to avoid a visible chart-data table take precedence over generic search recommendations.

## 2. Exact Files Changed

Paths below are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. These are current approximate lines; search the named anchor if later edits move them.

| File | Line / nearby anchor | Added, changed or removed |
| --- | --- | --- |
| `backend/core/modules/facilities/revenue.py` | 12 `valid_facility_payments`; 28 `facility_revenue_summary` | Add shared payment eligibility and one grouped query for current/previous revenue, daily amounts/counts and facility totals. |
| `backend/core/modules/reports/views.py` | 314 `_facility_dashboard_analytics`; 366 `revenue =`; 440 `revenue_overview` | Replace the previous payment loop with the shared summary; preserve legacy `period_revenue` and `revenue_chart` keys. |
| Same `views.py` | 1652 `_report_parameters`; 1717 `admin_generate_reports_page` | Validate report dates; honor a permitted report/date preset when opening the existing page. |
| `backend/core/modules/reports/dashboard_periods.py` | 255 `facility_analytics =`; 257 `revenue =` | Supply resolved comparison dates, reuse `comparison_metric`, and attach applied dates to the card payload. |
| `backend/core/modules/reports/reporting.py` | 36 `facility_revenue`; 346 `_facility_payment_report`; 456 report dispatch | Add Facilities → Facility Revenue. Reuse payment-row formatting with `revenue_only=True` and the shared valid-payment query. |
| `backend/core/modules/reports/models.py` | 16 `facility_revenue` | Register the report label in `GeneratedReport.REPORT_TYPES`. |
| `backend/core/modules/reports/migrations/0005_facility_revenue_report.py` | 8 `Migration`; 15 `AlterField` | Record the additional report choice in Django migration state. |
| `backend/core/modules/reports/templates/reports/pages/admin_generate_reports.html` | 38 selected option; 47–49 date inputs; 179 `isMoneyChart` | Display selected report/dates and treat revenue as a monetary chart. |
| `backend/templates/dashboard/partials/facility_revenue.html` | 2 card; 11 canvas; 13 keyboard description; 20 report link | Add the card's total/comparison, chart, honest empty state, loading/error/Retry and report link. No chart-data table. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 25 CSS; 382 partial; 590 JS | Load the new partial/assets only for the global Super Admin dashboard; preserve domain-card markup. |
| `backend/static/components/css/admin_facility_revenue.css` | 1 card scope; 5 total; 9 chart; 15 link | White existing card, navy typography, responsive chart and a sufficient minimum height to keep its footer inside the card. |
| `backend/static/components/js/admin_facility_revenue.js` | 8 `state`; 15 `inspect`; 27 `render`; 95–97 global events | Validate payload, update chart and tooltip, handle keyboard inspection, real refresh and loading/error states. |
| `backend/core/modules/reports/test_facility_revenue.py` | 24 `FacilityRevenueTests`; 48 eligibility; 73 boundaries; 92 presets; 125 query; 137 reports; 156 markup | Add money/status/date/comparison/report/security tests and isolated HTML/JSON exports. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 430 `vs yesterday` assertion | Update comparison occurrence count for the new visible revenue comparison and its JSON copy. |
| `scratch/facility-revenue/check-card.cjs` | 1 integration harness | Test actual rendered DOM and global-filter interactions against isolated fixtures. |
| `scratch/facility-revenue/check-browser.cjs` | 1 browser harness | Render actual Chart.js in Chrome and verify card fit, tooltip/counts, baseline and absence of tables. |
| `CAMPUSHUB_CONTEXT.md` | Current Facility Revenue note | Preserve current revenue rules and report behavior. |
| `docs/dashboard-global-date-filter.md` | Facility Revenue update / revenue section | Explain the new period-dependent summary and link this debugging/learning guide. |
| `docs/facility-status.md` | File map | Refresh nearby status-card line references after the revenue edits moved code. |
| `docs/facility-revenue.md` | This guide | Explain causes, functions, formulas, tests, limits and independent practice. |

Existing model sources inspected and reused: `api/models.py:473` Booking and `api/models.py:544` FacilityPayment. No duplicate payment or booking fields were created.

## 3. Changes Made

The card shows the real collected total as Philippine currency, an existing safe period comparison, the requested subtitle, and a navy revenue line. Gold highlights the active chart point. No persistent dots are shown on multi-day lines; a one-day range has one visible point so its real value is inspectable. The empty chart has a visible zero baseline, total `₱0.00`, and **No paid facility transactions in selected period.**

Mouse hover shows the full date, `Revenue: ₱…`, and `Paid Transactions: N`. Focus the canvas and press Left/Right or Home/End for the same daily values; a screen-reader description announces the value without adding a visible table. API failures hide the stale total/chart and show **Unable to load facility revenue.** with Retry. Retry uses the existing global Refresh control.

## 4. How It Works — Functions, Inputs, Outputs and Formulas

| Function | Input | Output / responsibility |
| --- | --- | --- |
| `valid_facility_payments(date_from, date_to)` | Optional inclusive dates | Lazy Django queryset containing eligible payments; annotate `revenue_date` in Asia/Manila. Both dashboard and revenue report reuse it. |
| `facility_revenue_summary(start, end, previous_range)` | Current inclusive dates plus optional prior dates | One `values(...).annotate(Sum, Count)` query grouped by facility/day. Return decimal-string totals, transaction count, daily chart and internal per-facility totals. No per-payment relation queries. |
| `resolve_dashboard_period(params)` — existing | Global preset or custom dates | Current and equivalent previous boundaries; preserves calendar-month/year rules. |
| `comparison_metric(current, previous, label)` — existing | Revenue totals and descriptive prior-period label | Direction, safe percentage or null, comparison text. |
| `_facility_dashboard_analytics` | Period dates and prior revenue dates | Uses the shared summary for existing facility revenue rows and new `revenue_overview` payload. |
| `_facility_payment_report(..., revenue_only=True)` | Selected report dates | The same eligible transactions formatted as report rows, summary and chart; reused by preview/CSV/PDF. |
| JS `render(data)` | `facilities.revenue_overview` | Validates finite/nonnegative totals, matching arrays and amount/count sums; updates DOM, chart and report dates. Invalid data shows an error rather than fake zeros. |
| JS `state` / `inspect` | State name / current selected index | Loading/ready/error visibility and accessible daily chart inspection. |

Eligibility uses the actual stored values:

- Payment must be `paid` and `paid_amount > 0`.
- Its booking must be `approved` or `completed` and assigned to a facility.
- Exclude `unpaid`, `failed`, unsupported payment states, `pending`/`rejected`/`cancelled` bookings, missing booking/facility links and nonpositive amounts.
- Do not invent `confirmed` or `reserved` booking statuses: the inspected model has neither.
- Effective collection date = `paid_at`, otherwise the existing legacy `created_at` fallback, converted to Philippine calendar date. Booking request/reservation dates and `total_amount` do not substitute for recorded payment amounts.
- An OR number is shown in the report when present; it is not an extra eligibility requirement because the existing payment model identifies recorded collection through `payment_status=paid`.
- Historical collections can count even if the facility is now inactive/archived; operational status is not a retroactive payment exclusion.

```python
# For each eligible recorded payment, paid_amount is collected money.
total = sum(payment.paid_amount for payment in current_period_payments)
# A daily tooltip counts payment records, not unique bookings.
paid_transactions = number_of_eligible_payment_records_on_that_day
# Only calculate a percentage if previous_total > 0.
change = (total - previous_total) / previous_total * 100
```

Two separate paid records for one booking count as two transactions and both amounts contribute. For current 114 and previous 100, display an increase of 14%. Current zero/previous positive gives a truthful 100% decrease; both zero gives No change; current positive/previous zero gives New activity with no invented percentage.

Data flows as follows: global controls → existing dashboard endpoint → period resolver → shared payment queryset and grouped summary → `facilities.revenue_overview` → initial Django partial / global data event → total, line, tooltip and dated report link. The reports page uses the same eligible queryset and dates, so collected amounts reconcile.

## 5. Backend / API Behavior and Report Route

The existing protected `/api/admin/dashboard/` endpoint now adds `facilities.revenue_overview`; old facility revenue keys remain compatible. All seven requested presets, including Previous Month and Custom Range, change current total, previous total/comparison and daily chart. This Month uses the same elapsed portion of the prior month, clamped to its last day; This Year uses the elapsed prior year; Previous Month compares full prior calendar months; rolling/custom ranges compare the preceding equal-length range.

Sales/Booking Daily–Weekly–Monthly dropdowns are chart-only and do not change this revenue card. The latest explicitly requested Show sample mode temporarily displays labeled examples; its API/payment/report logic still uses only real data, restored through Use real data or global refresh.

Navigation reuses `admin_generate_reports_page` (`core/urls.py:145`):

```text
/admin-generate-reports/?report_type=facility_revenue&date_from=2026-10-01&date_to=2026-10-07
```

Facilities is the existing report selector group; Facility Revenue is the new selected option. The chosen dates are prefilled. Preview and downloads use existing routes and report permissions; a Marketplace-only admin cannot open this facility report through a crafted query. The Payments & OR audit option still retains its existing all-payment behavior.

## 6. Database / Migration Impact

Applied `campushub_reports_module.0005_facility_revenue_report` locally after checking the migration plan. It changes report-type choices in Django state only, retaining the existing varchar field; no payment/booking values are inserted, deleted or edited. A migration-history entry is recorded. Normal CSV/PDF download continues to create an existing GeneratedReport audit record with the new report type. Test fixture payments were written only in the isolated test database.

For another checkout/database, run from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py migrate campushub_reports_module 0005 --noinput
```

## 7. Tests Performed and Manual Checks

Actual results:

- **69 Django tests passed** covering the new revenue tests, global periods/query budget, operational status, upcoming reservations and most-booked facilities, including inherited domain tests.
- **24 report tests passed** covering marketplace analytics and existing admin preview/export regressions.
- One final template-export test passed after keyboard feedback became visually hidden.
- Node DOM integration passed real refresh, tooltip revenue/counts, keyboard navigation, empty baseline, errors/Retry, invalid payloads, dated report link, and chart-grouping/sample independence.
- Eight actual headless Chrome renders passed: empty, populated, single-day and a long previous-year comparison label at 1200/500 viewport widths. The narrow card is 292px wide. Checked horizontal/vertical fit, real Chart.js, tooltip values, navy styling and absence of a table; screenshots inspected visually.
- Django system checks, report migration consistency, JS syntax and targeted whitespace checks passed. The local server returned HTTP 200 for both new CSS/JS assets.

Corrections made during verification: a test initially inserted unsupported booking statuses before building all dashboard cards, which Booking Overview properly rejects; those exclusion checks now test the payment service directly. The old markup test's text occurrence count needed the additional revenue comparison/JSON copy. An initial test command referenced a nonexistent class; corrected to `accounts.tests.AdminReportTests`, then all 24 checks passed. A browser test exposed the footer overflowing a forced short card; sufficient scoped minimum height and compact spacing now keep it inside. These are confirmed observations, not guesses.

Manual steps:

1. Log in as Super Admin and open Dashboard. Select each global preset and a valid Custom Range. The card and tooltip dates should follow the displayed global range.
2. For an existing known paid Approved/Completed booking, select its payment date; match the card total to recorded `paid_amount`, not booking amount due. Unpaid/Failed and rejected/cancelled records must not contribute.
3. Hover the trend; verify full date, amount and paid-record count. Press Tab to reach the chart and use arrow keys.
4. Select a date range with no eligible payments. Verify `₱0.00`, baseline and exact empty message; compare against previous positive revenue to check a decrease.
5. Click View Facility Reports →. Verify Facilities → Facility Revenue, matching dates/total, then preview/export CSV or PDF.
6. Change Sales/Booking chart grouping: this card retains its selected revenue. Show sample now previews the examples described above; Use real data or a global filter/Refresh restores recorded revenue.
7. In browser developer tools temporarily enable Offline, then Refresh. The error hides monetary content rather than showing zero. Disable Offline and Retry; the real card returns. Do this in a local test session.

Re-run backend checks from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_facility_revenue modules.reports.test_dashboard_periods modules.reports.test_facility_operational_status modules.reports.test_upcoming_reservations modules.reports.test_most_booked_facilities modules.reports.tests accounts.tests.AdminReportTests --keepdb --noinput
```

To recreate isolated browser fixtures, set `$env:FACILITY_REVENUE_TEST_DIR` to the absolute `scratch/facility-revenue` path, run the revenue test class, then run `node scratch/facility-revenue/check-card.cjs` and `node scratch/facility-revenue/check-browser.cjs` from project root. They use existing scratch jsdom, Bootstrap and Chart.js files.

## 8. Remaining Limitations / Debugging / Safe Practice

- This work reads existing payment records; it does not create a payment-entry workflow, validate cashier receipts, or fabricate lab/lease transactions that are not represented in FacilityPayment.
- The old Payments & OR report is an audit report and can have different totals because it includes other payment states; use Facility Revenue for reconciliation.
- Legacy paid records without `paid_at` use `created_at`; their original actual collection date cannot be reconstructed. Incorrect records should be reviewed through the existing authorized workflow.
- Chart.js still comes from the project's existing CDN. Missing/failed Chart.js shows the card error; restore the connection and reload the page. API Retry alone cannot redownload a failed script.
- Query failures are allowed to propagate to the existing global request error handler; the initial page also retains its existing server-error behavior. No bogus success payload is returned.
- Browser verification used actual Django-rendered fixture HTML and real Chart.js in offline Chrome, plus DOM integration. It was not a logged-in end-to-end test of the user's live payment records. Flutter and unrelated dashboards were not redesigned.

If the total seems wrong, inspect the dashboard response's `revenue_overview` first. Check payment status/amount, linked booking status, effective collection date in Manila, then selected current/prior bounds. If the response is correct but the UI differs, inspect the JS payload validation and console, confirm the new CSS/JS requests return 200, and hard refresh stale assets. Never fix a missing-payment query by substituting the booking amount.

Safe practice: in `test_facility_revenue.py:115`, change the isolated previous amount to `100` and current amount to `114`, keeping the expected percentage `14`. Explain why the denominator is the previous collected amount. Run that test alone and restore the original example afterward. Next, add a Pending booking with a paid record to the exclusion test and verify total remains unchanged. These exercises teach fixtures, query eligibility and regression testing without modifying real payments.
