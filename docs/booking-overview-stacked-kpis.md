# Booking Overview: full-width KPI cards and stacked trend

Current update: [Dashboard Analytics and Operations](dashboard-analytics-operations-update.md) adds independent booking grouping and removes the caution. Follow that guide where it supersedes the earlier behavior below.

Implemented on 2026-10-05. This guide covers the latest update, superseding the original single-series Booking Overview UI. File line numbers are current at this update; use the named anchor if later edits move them.

Later color update: the user explicitly requested green Completed and red Rejected/Cancelled chart segments and legend. See [Booking Overview status colors](booking-overview-status-colors.md) for the current colors; the original gray palette described below is superseded for those two series.

## 1. Cause / Reason

You asked for Booking Overview KPI cards to match Sales Overview, removal of the visible View chart data section, a caution message, and the attached final stacked-bar behavior. You then chose **full-width like the image**. Those current instructions take precedence over the attachment's narrow layout example. Your reduced brand palette takes precedence over its recommended red and green.

## 2. Exact Files Changed

Application files:

| Folder / file | Current line | Nearby anchor | What changed and why |
| --- | --- | --- | --- |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 278 | `col-12` inside `facility-analytics-grid` | Changed only the global Booking Overview column to full-width. Other facility card widths stay as configured. |
| Same file | 20, 561 | `admin_booking_overview.css`, `admin_booking_overview.js` | Bumped these asset versions to `20261005-booking-stacked-kpis`, so the browser requests the updated files. |
| `backend/templates/dashboard/partials/booking_overview.html` | 4 | `booking-overview__metrics` | Replaced the plain status summary with five white KPI cards; labels, numbers, icons and secondary text follow Sales Overview. |
| Same file | 18 | `data-booking-attention` | Added the pending count to a review notice, shown only when pending requests exist. |
| Same file | 22 | `booking-overview__legend` | Added four status labels matching the stacked chart. |
| Same file | 23, 26 | `canvas`, `bookingTrendDescription` | Removed the visible details/summary/table. Kept an invisible text list for screen readers and a keyboard announcement area. |
| Same file | 29 | `booking-overview__caution` | Added: “Caution: Booking counts do not confirm facility availability.” |
| `backend/templates/dashboard/partials/booking_overview_icon.html` | 1 | `<svg` | Added consistent decorative outline SVGs for the five metrics and caution. These are real UI icons, not emoji. |
| `backend/static/components/css/admin_booking_overview.css` | 7 | `booking-overview__metrics` | Added the five-column grid and white cards, 16px padding, 12px corners, 28px bold navy values, and right-side 44px light-blue icon containers. |
| Same file | 18, 24, 43 | caution/attention, chart wrapper, `@container` | Styled the gold warning icons and four-color legend; chart is 220px tall, 180px on small screens. Added responsive two-column and single-column layouts. Removed the former chart-table styles. |
| `backend/core/modules/reports/dashboard_bookings.py` | 11, 32 | `build_booking_overview`, `.values("day", "status")` | Changed the existing grouped query to include status, giving each time bucket four real counts and a total. No duplicate booking workflow was added. |
| Same file | 46, 61 | `trend.append`, `"chart"` | Added status counts to trend rows and chart arrays; preserved existing total `count` and `values` fields. |
| `backend/static/components/js/admin_booking_overview.js` | 12, 31 | `series`, `render` | Added the four series and checks that bucket totals and overall status totals agree before displaying data. Updated the five KPI cards and pending notice on filter changes. |
| Same file | 81, 97, 105 | `stack: 'bookings'`, tooltip, `stacked: true` | Replaced one total series with four datasets sharing one stack. Tooltip reports exact total plus four status counts. Both axes are stacked. |
| Same file | 61, 117 | `createDocumentFragment`, `keydown` | Removed visible table-row generation; updated the hidden text list. Added Left/Right/Home/End keyboard inspection of chart buckets. |
| `backend/core/modules/reports/test_dashboard_bookings.py` | 128, 154 | markup test, `test_one_stack_per_bucket_and_status_totals_reconcile` | Checked five cards, caution and no visible table. Added real test-record coverage for totals 7/4/10, empty series and unsupported stored status detection. |

Review scripts and documentation also changed:

| Folder / file | Current line | Anchor / purpose |
| --- | --- | --- |
| `scratch/dashboard-global-review/check-booking-overview.cjs` | 1 | DOM checks: four datasets, tooltip, keyboard, refresh, empty/error/loading and fallback. |
| `scratch/dashboard-global-review/check-controls.cjs` | 1 | Updated Chart test double for active-element reset during date changes. |
| `scratch/dashboard-global-review/prepare-booking-visual.cjs` | 8 | Browser measurements for card layout, stacks, icon alignment, colors and states. |
| `scratch/dashboard-global-review/render-booking.ps1` | 1 | Seven Chrome render cases across desktop/laptop/mobile and UI states. |
| `scratch/dashboard-global-review/verify-booking-visual.cjs` | 5 | Assertions against those seven browser reports. |
| `scratch/dashboard-global-review/prepare-palette-visual.cjs` | 58 | Added full-dashboard Booking Overview width and KPI column measurements. |
| `scratch/dashboard-global-review/verify-palette-visual.cjs` | 32 | Checks full-width placement and responsive columns in the actual dashboard template. |
| `CAMPUSHUB_CONTEXT.md` | 17 | Saved the accepted full-width stacked Booking Overview design for future work. |
| `docs/booking-overview-implementation.md` | 3 | Marked the original UI guide as historical and linked this current guide. |
| `docs/booking-overview-stacked-kpis.md` | 1 | Added this beginner-friendly implementation and testing guide. |

The project has other existing edits. The table describes this update, not all previously changed files.

## 3. Changes Made

Booking Overview now fills one dashboard row. On a wide screen all five KPI cards sit across the top. At a container width of 1059px or less the four status cards use two columns and Total Bookings spans both; at 459px or less every KPI uses one column. Icons are on the right of values, matching your Sales Overview example.

The chart has **one stacked bar per bucket**, with Approved in navy, Pending in gold, Completed in muted gray, and Rejected/Cancelled in light gray. There is no total-line overlay and no side-by-side group of status bars. Normal KPI values remain navy.

Only Booking Overview's visible View chart data toggle/table was removed. Its chart data remains in the backend. Sales Overview's chart-data control was not part of this request.

## 4. How It Works

The data path is: existing global dashboard date filter → existing Django dashboard payload → `build_booking_overview` → rendered partial and JSON → `admin_booking_overview.js` → Chart.js.

Each bucket starts with honest zero counts. The grouped database rows add counts into the matching date and status. For every bucket:

`total = approved + pending + completed + rejected_cancelled`

The browser verifies this equation and that all buckets reconcile with the displayed totals. An inconsistent payload shows the error state instead of false zeros.

Hovering a period shows its label, Total Bookings, Approved, Pending, Completed and Rejected/Cancelled, including zero counts. Focus the chart and press Left/Right, Home or End to inspect the same breakdown with keyboard and screen-reader feedback. A date refresh clears the previously active tooltip so it cannot point at a removed bucket.

The caution is an explanation: a count of requests does not prove a facility or time slot is free. It does not claim that a conflict exists. A separate review notice appears only when Pending is greater than zero.

If the previous equivalent period had zero requests and the current period has requests, the comparison says **New booking activity**, avoiding an infinite percentage. Otherwise it keeps the existing comparison text and equivalent-period calculation.

## 5. Backend / API Behavior

Reuses `api.models.Booking` and the existing Super Admin global dashboard endpoint/service. No new route or booking-management page was created. The added chart data is inside `facilities.booking_overview`.

Exact mapping of actual model constants:

| Stored status | Dashboard group |
| --- | --- |
| `pending` | Pending |
| `approved` | Approved |
| `completed` | Completed |
| `rejected` | Rejected / Cancelled |
| `cancelled` | Rejected / Cancelled |

There are no invented Under Review, Confirmed or Reserved statuses. An unsupported stored value raises an explicit error; it is not silently dropped from the chart. The existing endpoint handles the error rather than claiming there are zero requests.

The trend uses **`created_at` in Asia/Manila**, matching the global Total Bookings KPI. It shows current statuses of requests created within that range, not the historical time each request changed status. Other facility utilization/reservation analytics keep their existing reservation-date basis.

Grouping remains automatic: up to 31 days uses daily buckets, 32–120 days uses seven-day buckets from the selected start date, and longer ranges use monthly buckets. Partial first/last buckets include only selected dates. The existing total/status KPI aggregation is reused, plus one grouped date-and-status query; no Booking objects are loaded individually for this chart.

Existing field compatibility is retained: `trend[].count`, `chart.values`, and the combined `cancelled` alias remain; `trend[].total`, four per-row status counts and four chart arrays are additive. Existing global date validation and server-side permissions remain in place.

View All Bookings uses Django's existing `admin_bookings_page` route (`/admin-bookings/`). Pending, Approved and Completed link to that page with the existing `status` filter. The rejected/cancelled KPI remains informational because the page has no existing combined filter. JavaScript preserves the current tab's admin-session token when navigating.

## 6. Database / Migration Impact

No schema changes, migration, new model, new status or live database record changes. The application change reads and groups existing bookings. Test fixtures were created only in the isolated Django test database. Approval, conflicts, calendars, facility availability and payment workflows were not modified.

## 7. Tests Performed

Passed:

- **64 Django tests** across Booking Overview, global dashboard periods and report tests. Includes all date presets/custom ranges, Manila boundaries, grouping, status mapping, previous-period comparison, request-versus-reservation dates, permissions and bounded query count. New records produce three bucket totals **7, 4 and 10**, with all four status series reconciling.
- JavaScript syntax check and two DOM suites: Booking Overview and existing global dashboard controls.
- Seven actual headless Chrome renders: desktop, laptop, mobile, empty, loading, API error and unavailable chart library. Checked five KPI cards, right-side icons, responsive columns, no visible table, stacked axes, four common-stack datasets, caution and no overflow/errors.
- Two complete-dashboard Chrome renders: desktop and mobile. Confirmed full-width Booking Overview within Facilities Analytics, reduced palette, correct responsive KPI columns and no page overflow.
- Styles parsed successfully with the review script's CSS parser.

Evidence: `scratch/dashboard-global-review/booking-stacked-django-tests.log`; `booking-overview-desktop.png`; `booking-overview-mobile.png`; seven `booking-overview-*.dom.html` reports; `palette-desktop.dom.html` and `palette-mobile.dom.html`. Preview numbers are isolated test records, not fabricated production metrics.

Manual testing you can do:

1. Open the Super Admin dashboard and press **Ctrl+F5**. Booking Overview should fill the Facilities Analytics row, with five matching white KPI cards on a wide screen.
2. Change the global date filter to Today, Last 7 Days, Last 30 Days, This Month, This Year and a custom range. Check that totals, dates, comparisons and bars update together.
3. Pick a period with actual booking requests. Hover a bar and compare its total and four statuses with matching request creation dates on the Bookings page. The bar height must equal the sum of the segments.
4. Pick a period without requests. All values should be zero, the empty chart baseline should remain, and “No bookings in selected period.” should appear. Loading must show the skeleton rather than temporary zeros.
5. Tab to the chart and use arrow keys. Open Pending, Approved, Completed or View All Bookings and confirm the existing page/filter opens.
6. In browser developer tools, block the dashboard refresh request. Refresh the range: the error and Retry control should appear. Unblock it and Retry should restore actual data.
7. Narrow the browser: the KPIs should wrap into two columns, then one, without cutting off text. Confirm the caution remains visible and the Booking Overview chart-data toggle/table is absent.

The skill's chart search did not return an exact stacked-status-over-time match after one narrower retry. This implementation follows your explicit stacked-chart specification; the keyboard/text accessibility treatment follows general guidance rather than claiming a verified skill search match for this chart type.

## 8. Remaining Limitations

- Verified in Chrome and DOM tests; Safari, Firefox, physical touch devices and screen-reader software were not separately tested.
- Other facility cards retain their existing column widths; this change makes only Booking Overview full-width.
- View All Bookings does not carry the selected request-creation date range; use that module's existing filters. The combined rejected/cancelled KPI has no link.
- Current status is shown for requests created in the selected range. This is not a status-transition audit history or a facility availability forecast.
- If Chart.js is unavailable, the counts, caution, screen-reader breakdown and navigation remain, with a chart-specific unavailable message. There is intentionally no visible replacement data table.
- An unsupported stored booking status requires correcting the data or explicitly updating the actual workflow mapping; the dashboard will not guess its meaning.
