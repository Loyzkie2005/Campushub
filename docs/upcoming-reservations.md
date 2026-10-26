# Upcoming Reservations — Super Admin Dashboard

Implemented 2026-10-07. UI/UX Pro Max was used for the design check. The existing dashboard card foundations are reused; the rest of the dashboard is not redesigned.

## Sample preview update — 2026-10-07

The user subsequently requested samples for **Most Booked Facilities and Upcoming Reservations**. The existing Sales Overview **Show sample / Use real data** button now previews both. This explicit request changes the earlier real-only preview behavior; real mode and backend queries remain unchanged.

### Implementation report

1. **Reason:** The sample button previously populated marketplace/utilization cards but did not populate these two facility cards.
2. **Exact files changed:** Paths are relative to the project root; see the table below. Existing card styles are reused without modifying CSS.
3. **Changes:** Most Booked previews Covered Court 24, Function Hall 18, Hostel 12, Training / Assessment Center 8. Upcoming previews four Approved reservations 5/8/11/14 days ahead of today's Manila date, including a two-night Hostel stay. A short Sample preview label appears only in this mode. No laboratory service request or commercial lease is invented as a standard reservation.
4. **How it works:** Save original DOM nodes and visibility, render fixtures through the existing renderer, and restore the snapshot on Use real data. Upcoming dates are calculated from the current Manila calendar date. Real Refresh replaces fixtures with actual API rows.
5. **Backend/API:** Unchanged and always real. Chart grouping leaves samples unchanged; global dates/Refresh clear samples. No sample endpoint.
6. **Database/migrations:** None; no live bookings or approvals are created.
7. **Tests performed:** Two existing Django template/API integration tests passed with fresh isolated exports; both card integration scripts passed. Tests verify populated and empty restoration, row identity, future dates across a year boundary, grouping isolation, Refresh, error/Retry, Calendar URL and safe text. Both application scripts and the fixture exporter passed Node syntax checks. Two Chrome sample checks at 1200px/500px passed for four rows per card, preview labels, navy titles and no horizontal overflow. The desktop PNG was visually inspected. The exporter preservation check ran in memory with writes intercepted. The previous full 67-test backend run belongs to the original implementation; it was not repeated for this frontend-only update.
8. **Limitations:** Sample counts are illustrative, not period-based calculations. Samples never create Calendar events. Signed-in live interaction remains a manual check.

| Changed file | Current line / nearby code anchor | Purpose |
| --- | --- | --- |
| `backend/templates/dashboard/partials/sales_sample_data.html` | 172, `facility_samples` | Add explicitly requested UI examples. |
| `backend/static/components/js/admin_most_booked_facilities.js` | 41, `clearSample`; 51, sample listener | Save/restore real rows and render example counts. |
| `backend/static/components/js/admin_upcoming_reservations.js` | 34, `clearSample`; 44, `sampleRows`; 67, sample listener | Save/restore real rows and calculate future example dates. |
| `backend/templates/dashboard/partials/most_booked_facilities.html` | 1, card ID; 4, sample note | Add control target and hidden-by-default preview label. |
| `backend/templates/dashboard/partials/upcoming_reservations.html` | 1, card ID; 6, sample note | Add control target and hidden-by-default preview label. |
| `backend/templates/dashboard/partials/sales_overview.html` | 11, `aria-controls` | Include both cards in the sample button's accessible targets. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 577–578, sample script versions | Ensure browsers load the changed JavaScript. |
| `scratch/sales-overview-system-test/export-sample-data.cjs` | 13, preservation comment; 15, `existing.facility_samples` | Preserve facility examples when marketplace sample data is regenerated. |
| `scratch/upcoming-reservations/check-card.cjs` | 1, integration harness | Verify sample restoration, grouping, date boundaries and exporter preservation. |
| `scratch/upcoming-reservations/check-sample-browser.cjs` | 1, Chrome harness | Render both sample cards and check desktop/narrow layouts. |
| `docs/upcoming-reservations.md`; `docs/most-booked-facilities.md`; `docs/dashboard-global-date-filter.md`; `CAMPUSHUB_CONTEXT.md` | Sample update / current preference notes | Record current behavior, learning guidance and debugging. |

### Functions, inputs/outputs and data flow

The existing toggle sends `campushub:marketplace-sample` with the JSON fixture as input. Each card saves real nodes before calling its existing `render(rows)`; the output is preview DOM, never database records. `clearSample(restore)` takes a boolean: true restores saved nodes/visibility/busy state; either value clears the snapshot and preview label. `sampleRows(rows)` takes facility names plus positive day offsets and optional times/stay lengths, validates them, and returns `{facility, when, status, status_label}` display rows using the actual Approved status.

Upcoming dates use `Intl.DateTimeFormat` with `Asia/Manila` to obtain today's date. UTC date arithmetic then adds calendar days without the browser's local timezone shifting the date. Month/year-crossing stays show both endpoints. Refresh and global failures clear labels and return to real loading/error states.

```javascript
children: [...list.childNodes] // Save actual nodes, including template whitespace.
list.replaceChildren(...realSnapshot.children); // Restore the exact nodes after preview.
```

Data flow: fixture JSON → existing sample event → snapshot → existing card renderer → Use real data restores the snapshot, or Refresh loads fresh backend data. This reuses the control and renderers instead of adding filters or inserting test bookings.

### Manual checks, debugging and safe practice

Hard-refresh, click **Show sample** in Sales Overview, then scroll to the two facility cards. Check four rows and preview labels. Change chart grouping: rows must stay. Click **Use real data**: original real rows or exact empty states must return. Repeat and press Refresh: samples must clear. Calendar still displays only actual reservations.

If a preview does not appear, check that `salesSampleData` contains `facility_samples`, both updated scripts loaded, and the dashboard is not busy/in an error state. If rows remain after exiting, inspect `clearSample()` and the inactive sample event's `restore` flag. If dates are unexpected, check the browser clock and Manila date conversion; these are display examples, not saved dates. The exporter preservation check protects facility fixtures from being discarded during marketplace regeneration.

Safe exercise: in a local branch, change only the first sample count from 24 to 25 in `sales_sample_data.html`. Hard-refresh, verify 25 appears in sample mode, then Use real data and verify the database count is unchanged. Revert the example. Never modify live bookings or approval rules to populate a preview.

## 1. Cause / Reason

Confirmed by inspection: the old Super Admin card selected six Approved bookings using only `booking_date >= today`. It omitted stays represented by check-in/check-out dates, included already-started timed bookings today, displayed requester information instead of status, and did not receive reservation rows through the global dashboard API. Its generic booking links did not select the clicked reservation.

The replacement shows the nearest five real Approved reservations, including valid future stays. It uses compact name/date/status rows and the existing Calendar action. No live sample reservations are inserted.

## 2. Exact Files Changed

Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Line numbers reflect this implementation; use the nearby anchor if they move.

| File | Current line / anchor | Change and reason |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_bookings.py` | 14, `upcoming_reservations` | Add one bounded query and truthful date/time formatting for events and stays. Existing ranking/trend functions remain. |
| `backend/core/modules/reports/dashboard_periods.py` | 16, helper import; 267, `upcoming_reservations=` | Add current upcoming rows to the shared initial-page/API payload. |
| `backend/core/modules/reports/views.py` | 1214, `not is_marketplace_admin and not global_dashboard` | Skip the superseded initial-page reservation query for Super Admin; domain dashboards retain their existing query. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 23, new CSS; 336, partial include; 578, new JS | Replace only the global dashboard's old card and load its scoped assets. |
| `backend/templates/dashboard/partials/upcoming_reservations.html` | 1, `data-upcoming-reservations`; 4, Calendar link; 7, list | Add the title, name/date/status rows, exact empty message and loading/error/Retry states. Remove the old requester row and bottom View All link from this Super Admin card. |
| `backend/static/components/css/admin_upcoming_reservations.css` | 2, card; 4, header; 7, list; 17, focus | Reuse shared white/border/radius/title styling, with 16px padding, navy rows, subtle dividers, hidden-scrollbar scrolling and visible keyboard focus. |
| `backend/static/components/js/admin_upcoming_reservations.js` | 10, `state`; 17, `render`; 34, `clearSample`; 44, `sampleRows`; 67, sample listener; 76, global listeners | Update real rows on global requests, preview requested examples and restore snapshots; Retry uses global Refresh. |
| `backend/core/modules/reports/test_upcoming_reservations.py` | 20, `UpcomingReservationsTests` | Add seven targeted cases using isolated test records; also retain inherited domain dashboard checks. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 269, `test_query_count_is_not_proportional_to_orders`; 279, budget | Change the previous 24-query limit to 25 for this one new bounded query. Keep the assertion that adding orders cannot increase query count. |
| `CAMPUSHUB_CONTEXT.md` | Current Upcoming Reservations note | Remember the accepted real-data snapshot and filter behavior. |
| `docs/upcoming-reservations.md` | This guide | Explain implementation, testing, debugging and safe practice. |
| `docs/dashboard-global-date-filter.md` | Update note near the top | Explain why current upcoming rows are not limited to historical reporting dates; link this guide. |
| `docs/most-booked-facilities.md` | File table | Refresh moved function/template line references after adding this helper and card. Its ranking behavior is unchanged. |

Verification tools added under `scratch/upcoming-reservations/`: `check-card.cjs`, `build-preview.cjs`, and `check-browser.cjs`, starting at line 1. Exported HTML/JSON/PNG files contain isolated test fixtures, not live records. They are verification artifacts, not application data.

## 3. Changes Made / UI

The card uses the existing `marketplace-summary-card` foundation from `admin_marketplace_overview.css`: white background, subtle border, 12px corners, 14px semibold title, navy text and no decorative shadow. Scoped CSS adds 16px padding and compact rows without nested mini-cards, charts, extra filters or KPIs. Names wrap rather than being cut off. Status is plain navy semibold text.

The existing facility grid position is retained. The card has a 380px minimum height and fills its grid row; longer lists scroll inside it with hidden scrollbar tracks, matching the accepted dashboard behavior. Focus the list and use keyboard scrolling, a touch gesture, or the mouse wheel to see remaining rows. Header wrapping keeps the Calendar link usable in narrower cards; its target height is 44px.

Only the global Super Admin card is replaced. Existing domain-specific pages are not restyled here.

## 4. How It Works / Functions and Data Flow

| Function or structure | Input | Output / job |
| --- | --- | --- |
| `upcoming_reservations(today=None, now=None)` | Optional local date and timezone-aware instant; defaults to the current Manila date/time | Zero to five dictionaries containing `id`, `facility`, `when`, `status`, `status_label`. One database query including facility details. |
| `build_dashboard_data(params, today=None)` | Existing authorized dashboard period/grouping parameters | Adds the list under `facilities.upcoming_reservations`, alongside the other facility cards. |
| Django partial | `facility_analytics.upcoming_reservations` | Escaped initial rows, or the exact empty message. Calendar URL is reversed server-side. |
| Browser `render(rows)` | The upcoming list from a successful global response | Validates the response, builds DOM nodes using `textContent`, and replaces the list. Facility names cannot become executable HTML. |
| Browser `state(value, hasRows)` | `ready`, `loading`, or `error` plus row availability | Controls which content is visible and the card's `aria-busy` state. Loading/error messages use accessible status/alert roles. |
| Existing global filter `load(...)` | Global period/Refresh or chart-only grouping action | Global requests dispatch dashboard events; chart-only requests dispatch separate chart events. This card listens only to the global events. |

Data travels through **Booking/Facility database records → query/helper → shared dashboard payload → Django initial HTML or authenticated API JSON → card renderer**. `select_related("facility")` loads facility names in the same SQL query. Reading five rows never requires a separate facility query per row.

Annotated selection example:

```python
Booking.objects.filter(
    stays | events,                   # Actual future reservation dates, not request creation dates.
    status=Booking.STATUS_APPROVED,    # The only current active accepted Booking status.
    facility__isnull=False,            # Do not invent names for deleted/unassigned facilities.
).select_related("facility")          # Join facility data once, avoiding N+1 queries.
```

The remaining code annotates one sorting date and time, orders them ascending, then applies `[:5]` before reading the result. Formatting happens in Python for those five records only. This approach keeps the query bounded, handles both event and stay fields, and gives initial HTML and refresh the same rules.

### Actual statuses and selection rules

- Include **Approved** (`Booking.STATUS_APPROVED`). The model currently has no Confirmed or Reserved booking status. Facility availability states are different fields and do not qualify a booking.
- Exclude **Pending, Rejected, Cancelled and Completed**. No Under Review status exists in this Booking model.
- Events with both stay fields absent qualify when `booking_date > today`, or when the date is today and the start time has not passed. A missing start time qualifies today because the model does not record an exact start; the UI shows the date without inventing one.
- Timed bookings that have already started today, including currently ongoing ones, are excluded from this future-start list.
- Stays qualify when `check_in_date >= today` and `check_out_date > check_in_date`. Stay fields take precedence if an older record also has a `booking_date`.
- Already-started stays from prior dates, missing date pairs, reversed/zero-length stays, missing event dates and missing facility links are excluded.
- Same-day stays qualify by date because the model has no stay arrival time. Do not interpret this as proof that the guest has not checked in.
- Sort by effective start date, then known event start time; date-only reservations sort first on that date. Use booking primary key as a stable final tie-breaker. The SQL limit is five. With fewer records, show only those records.
- This list does not erase Approved future reservations merely because the facility's current maintenance/archive setting changes. Availability/conflict enforcement remains the booking workflow's responsibility.

### Date/time formatting

Show both actual event times only when both are recorded: `Oct 12, 2026 · 1:00 PM – 5:00 PM`. Otherwise show just the recorded date. Never display a invented default time or requester name in place of status.

Stay ranges use recorded check-in/check-out dates, for example `Oct 18–20, 2026`; crossing a month/year includes both month/year boundaries as needed. These are display examples, not hardcoded reservation rows. Both default selection and time cutoffs use Asia/Manila.

## 5. Backend / API Behavior

Reuse the existing protected `/api/admin/dashboard/` endpoint. Authentication and Super Admin authorization remain in that endpoint; no new API/page route is added.

Preserve the old upcoming list's **current future snapshot** behavior: historical global periods do not restrict it. Global date changes and Refresh fetch its latest snapshot from the database, while the other historical analytics use their selected range. Daily/Weekly/Monthly grouping in Sales Trend or Booking Trend does not update, rebuild or put this card into loading state. By the subsequent explicit request, Show sample previews this card in memory; Use real data restores its actual list.

The Calendar link uses `{% url 'admin_calendar_page' %}` → **`/admin-calendar/`**, defined in `backend/core/core/urls.py:122`. It uses the existing Facilities Calendar page.

The exact empty state is **No approved upcoming reservations.** A failed request shows an error and Retry, not an empty result. Retry clicks the existing dashboard Refresh button and therefore refreshes the global dashboard. No stale rows are presented as newly loaded data after a failed request.

## 6. Database / Migration Impact

No model/table/schema changes, migrations, live reservation insertion, live deletion, or database seed operation. The feature reads the existing unmanaged Booking and Facility models. Tests create and delete fixtures only in the separate Django test database.

## 7. Tests Performed

- Final command: `venv\Scripts\python.exe manage.py test modules.reports.test_upcoming_reservations modules.reports.test_most_booked_facilities modules.reports.test_dashboard_bookings modules.reports.test_dashboard_periods --keepdb --noinput`, run from `backend/core`: **67 passed**, Django system check reported no issues.
- New checks cover actual status exclusions, missing/past dates, same-day time cutoff, mixed event/stay sorting, top-five limit, one-query facility loading, invalid/started stays, authoritative stay dates, missing times, month/year boundaries, Manila midnight, stable ties, all global presets/custom dates, all chart groupings, initial/API parity and existing Calendar URL.
- The first combined run had one failure: the old dashboard query-budget assertion expected 24, while the new card adds one query. The helper's single-query assertion already passed. Updated the documented bound to 25 and reran the suite successfully; the order-growth assertion is retained.
- `node --check backend/static/components/js/admin_upcoming_reservations.js`: passed.
- `node scratch/upcoming-reservations/check-card.cjs`: passed using the actual exported Django page and API fixtures. Checks grouping/sample isolation, global period/Refresh, loading/error/Retry, empty state, Calendar URL, safe text rendering and malformed responses.
- `node scratch/upcoming-reservations/build-preview.cjs` then `node scratch/upcoming-reservations/check-browser.cjs`: all four actual Chrome checks passed, empty/populated at 1200px and 500px viewport widths. Shared border/radius/title, 16px padding, navy title, 44px Calendar target and no horizontal overflow were verified. The populated narrow PNG was visually inspected; scrolling exposes remaining rows.
- The running local Django server returned HTTP 200 for both new CSS and JavaScript assets. `git diff --check` passed for the changed tracked view/template files.

The browser previews use actual template output with test records and local styles, not an authenticated live user session. The integration test uses a stubbed fetch response from real isolated API exports. Live interactive Calendar navigation remains a manual check; do not confuse the route/link check with a signed-in navigation test.

### Manual test steps

1. Use a development/test database and log in as Super Admin. Open the dashboard and hard-refresh once to load the new assets.
2. With no future Approved reservations, verify the exact empty sentence. Pending/Rejected/Cancelled/Completed records must not appear.
3. Through existing booking tools, create/approve future reservations with actual dates/times. Create more than five across different facilities; verify nearest-first ordering and at most five rows. Scroll inside the card if needed.
4. Add a valid stay using the existing stay workflow; verify its check-in/out range without fake event times. A completed/past stay must be absent. For missing time data, the display must remain date-only.
5. Switch Sales and Booking chart grouping. The upcoming list must stay unchanged. Show sample should preview illustrative future rows; Use real data must restore real rows or the empty state.
6. Change global dates to Previous Month, then Refresh. The list must still show nearest current future reservations, while historical cards follow their reporting period.
7. Click **View Calendar →** and verify the existing Facilities Calendar opens. Tab to the link/list; check focus and keyboard scrolling.
8. In browser DevTools, switch Network to Offline and click Refresh. Verify an error rather than the empty state; return Online and Retry to recover.

### Debugging / Troubleshooting

| Symptom | Confirm first | Relevant anchor / next step |
| --- | --- | --- |
| Expected booking missing | Current status is exactly Approved; facility link exists; reservation has a usable future date | `dashboard_bookings.py:14`: inspect `stays`/`events`. Do not approve real bookings just to make a chart/card look populated. |
| Today's record missing | Its actual start may already have passed in Manila | `local_now` and same-day `start_time__gte`; this is intentional future-start selection. |
| Stay missing | Both dates must exist and checkout must follow check-in; prior-date arrivals are excluded | `stays` condition. Correct source data through the actual booking workflow if it is wrong. |
| Times absent | Both time fields must be present for a pair | Helper's `if booking.start_time and booking.end_time`; do not add default times. |
| Rows do not refresh | Check `/api/admin/dashboard/` response has `facilities.upcoming_reservations`; inspect status/authorization and browser console | Payload at `dashboard_periods.py:267`; event listener at `admin_upcoming_reservations.js:78`; template script at line 578. |
| Card appears empty during a failure | Check whether error state is visible and whether an old cached script is loaded | `state()` and the `20261006-upcoming` asset version; hard-refresh. Never turn API failures into fabricated rows. |
| Grouping changes the list | Confirm only chart-specific events were sent; inspect custom code added later | This card must not subscribe to `sales-trend-data` or `booking-trend-data`. Its sample listener is for the explicit preview toggle only. |

These are investigation steps, not claims that every listed problem is present. Use `docs/DEBUGGING_GUIDE.md` to record the actual symptom, evidence, cause, change and verification.

### Safe learning exercise

In a local branch, change only the error button text in `upcoming_reservations.html` from `Retry` to `Try again`. This teaches template presentation without changing booking rules. Hard-refresh the development dashboard, simulate Offline, and verify that the new button still invokes Refresh after reconnecting. Revert the wording when finished. Leave the data attribute `data-upcoming-retry` unchanged: JavaScript uses that attribute, not the visible button text, to find the control.

## 8. Remaining Limitations

- Optional row navigation is omitted: the existing `admin_bookings_page` reads a status query, but does not cleanly accept a reservation/facility preset. Plain rows avoid sending users to an unfiltered list when they expected a selected booking. No new route is created.
- Confirmed/Reserved are not invented statuses. If the actual model/workflow later adds them, update the ORM selection, response validation and exclusion tests together.
- This card lists Booking records, not separate laboratory job orders or lease service requests that do not exist as bookings. It does not invent records for those workflows.
- Date-only reservations have no precise start-time cutoff. Same-day stays are eligible by date. There is no timer polling: initial load, global date requests and Refresh fetch current results.
- Existing domain dashboards retain their legacy Upcoming card; this request targets Super Admin. Mobile app screens are outside this change.
