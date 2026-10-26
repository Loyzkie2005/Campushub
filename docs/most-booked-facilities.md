# Most Booked Facilities — Super Admin Dashboard

Latest update 2026-10-07: rows now include the first saved Facility image. `dashboard_bookings.py:65` adds `facility_image=Max('facility__image_url')` to the existing grouped ranking query; line 69 calls the existing `Facility.get_first_image_url()` parser on an unsaved object. Input is the stored plain URL/JSON image list; output is `image_url` in each ranked row, with no additional query. `most_booked_facilities.html:9` and `admin_most_booked_facilities.js:28` show a compact 40px thumbnail beside rank/name; missing or failed images show the existing calendar icon. The four sample rows use local navy/gold SVG illustrations, not claimed photos of actual facilities. Valid booking counts/date rules are unchanged. See [the latest preview/image file map and learning guide](facility-revenue.md) for all changed files/current anchors, tests, debugging and limits. The image-selection/initial-markup test and one-query checks passed within the 42-check backend run; DOM fallback/restoration and two real Chrome sample layouts also passed. Safe practice: add two test image URLs to a facility fixture, run `test_images_reuse_first_uploaded_image_in_one_query_and_initial_html`, and verify only the first URL appears while the query count remains one; never edit real uploads for this exercise. Earlier line references below belong to the prior implementation.

Implemented 2026-10-06. UI/UX Pro Max was the only design skill used. This card reuses the existing Top Best-Selling Products visual structure rather than introducing a new design.

Update 2026-10-07: the user requested sample previews. Show sample now displays four illustrative counts (24/18/12/8); Use real data restores the exact real list/visibility. `sales_sample_data.html:172` supplies `facility_samples.most_booked`; `admin_most_booked_facilities.js:41` defines `clearSample(restore)` and line 51 handles the existing sample event. Input is the fixture list; output is preview DOM through `render(rows)`. Original `childNodes`, hidden states and busy state are stored in memory; previews never become database bookings. Global requests/errors clear samples; chart grouping leaves them unchanged. `most_booked_facilities.html:4` adds the preview note and the page's script version at line 577 is updated. Backend queries and database are unchanged. See [Upcoming Reservations — sample update](upcoming-reservations.md) for every changed file/current line, functions/data flow, debugging, manual checks and a safe sample-count exercise. Two template/API tests, both integration checks, two Chrome sample layouts and Node syntax checks passed for this frontend update. Earlier verification results below describe the original implementation.

## 1. Cause / Reason

The Super Admin dashboard previously showed a single Most Booked Facility highlight. You requested up to five facilities ranked by real valid booking counts, with the existing product ranking card's typography, spacing and rows. Inspection also confirmed that Booking Trend grouping refreshed all dashboard cards; this now has a chart-only response path. Previous Month was absent from the existing global selector and is now available there.

## 2. Exact Files Changed

Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Search by the nearby anchor if line numbers move.

| Folder / file | Current line / nearby anchor | Added, changed or removed |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_bookings.py` | 54, `most_booked_facilities(period)` | Add one grouped ORM query returning up to five ranked facilities. Line moved after the Upcoming helper was added; ranking logic is unchanged. |
| `backend/core/modules/reports/dashboard_periods.py` | 22, `PERIOD_LABELS`; 45 and 75, `previous_month`; 266, `most_booked_facilities=` | Add Previous Month resolution and include ranking in the existing dashboard payload. |
| `backend/templates/dashboard/partials/most_booked_facilities.html` | 1, `data-most-booked-facilities`; 6, ordered list | Add the real-data ranking, exact title/subtitle, empty/loading/error states and Retry. |
| `backend/templates/dashboard/partials/global_date_filter.html` | 11, `previous_month` option | Add the requested preset to the existing global filter. No duplicate filter. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 22, ranking CSS; 320, partial include; 577, ranking script; 579 and 581, grouping scripts | Replace the single highlight only on the global Super Admin dashboard. Add scoped assets and update grouping-script cache versions. Existing domain dashboards retain their previous card. |
| `backend/static/components/css/admin_most_booked_facilities.css` | 1, `[data-most-booked-facilities]` | Reuse shared product styles; scope compact sizing, hidden states, scrolling and focus. |
| `backend/static/components/js/admin_most_booked_facilities.js` | 12, `state`; 19, `render`; 41, `clearSample`; 51, sample listener; 60, global listeners | Update real rows from global responses, preview requested examples and restore actual rows. Distinguish empty, loading and error results. |
| `backend/static/components/js/admin_dashboard_filter.js` | 25, `bookingRetryOnly`; 481, `load`; 538, `campushub:booking-trend-data`; 636, Retry; 645, dropdown listener | Add chart-only Booking Trend requests using applied global dates. Preserve other cards and localize retry failures. |
| `backend/static/components/js/admin_booking_overview.js` | 30, `render(overview, chartOnly)`; 138, `campushub:booking-trend-data`; 139, error listener | Receive the separate booking-chart response/error and preserve the KPI snapshot while regrouping. |
| `backend/core/modules/reports/test_most_booked_facilities.py` | 19, `MostBookedFacilitiesTests` | Test actual ORM ranking, status/date exclusions, stays, ties, filters, grouping, empty markup and isolated preview exports. |
| `CAMPUSHUB_CONTEXT.md` | Current Most Booked Facilities note | Remember the accepted card and date/grouping behavior. |
| `docs/most-booked-facilities.md` | This guide | Beginner explanations, debugging and implementation report. |
| `docs/dashboard-global-date-filter.md`; `docs/booking-overview-implementation.md`; `docs/dashboard-analytics-operations-update.md` | Update note near the beginning | Link earlier behavior to the new preset/grouping path. |

Verification helpers: `scratch/most-booked-facilities/check-ranking.cjs`, `build-preview.cjs` and `check-browser.cjs` (line 1 in each). Generated source HTML, JSON, browser DOM and PNG files in this folder use isolated Django test records, not live records.

## 3. Changes Made / Design Reused

The card keeps the shared `marketplace-summary-card`, `marketplace-card-symbol`, `marketplace-card-note`, `marketplace-product-columns`, `marketplace-product-list`, `marketplace-product-details`, `marketplace-product-rank`, `marketplace-product-stats`, `marketplace-product-units` and `marketplace-card-empty` classes. Their existing definitions in `admin_marketplace_overview.css` remain unchanged.

This preserves the white flat card, subtle border, 12px radius, 14px semibold title, small trophy icon container, 16px compact padding, 48px minimum rows, navy text and right-aligned numbers. The rank appears inline before the name, just like the existing real-product rows. The count reads `1 booking` or `N bookings`. Facilities do not receive invented product photos, categories, charts or progress bars. Long names wrap; lists can scroll internally with hidden scrollbars and visible keyboard focus.

Title: **Most Booked Facilities**. Subtitle: **Facilities ranked by valid booking count**. With no valid rows, the matching icon/text empty state reads **No booked facilities in selected period.** No numbered placeholders are rendered. Fewer than five valid facilities produce only that many rows.

## 4. How It Works / Functions and Data Flow

| Function / structure | Input | Output / responsibility |
| --- | --- | --- |
| `resolve_dashboard_period(params, today)` | Existing global period key/custom dates and local date | Validated `AnalyticsPeriod` and comparison metadata. Previous Month spans the full prior calendar month. |
| `most_booked_facilities(period)` | That period's start/end | List of `{rank, id, name, bookings}` dictionaries; zero to five records, one database query. |
| `build_dashboard_data(params)` | Existing authorized dashboard request parameters | Adds the list under `facilities.most_booked_facilities`. Both initial page and API use this data. |
| New Django partial | `facility_analytics.most_booked_facilities` | Initial real rows or the honest empty state. Django escapes facility names. |
| Browser `render(rows)` | The ranking list from a global response | Validates positive integer counts/consecutive ranks, creates safe text nodes and replaces the ordered list. Malformed data produces an error state. |
| Browser `state(value, hasRows)` | `ready`, `loading` or `error`, and whether rows exist | Shows the correct heading/list/message and updates `aria-busy`. |
| Existing `load(period, salesOnly, bookingOnly)` | Selected/applied period and chart-only flags | Global requests dispatch dashboard data; Booking Trend requests dispatch only booking-trend data. |

Data flow: actual PostgreSQL Bookings + joined Facility name → date/status filter → grouped count → top-five list → initial Django template or existing dashboard JSON → DOM rows → shared product CSS.

### Ranking query and statuses

The actual Booking model defines Pending, Approved, Rejected, Cancelled and Completed. Only `Booking.STATUS_APPROVED` and `Booking.STATUS_COMPLETED` count. Pending, Rejected and Cancelled are excluded. Confirmed, Reserved and Under Review are not invented as Booking statuses; similarly named facility availability states are not booking approval states.

```python
Booking.objects.filter(
    usage_dates,                         # Selected reservation/stay dates.
    facility__isnull=False,              # A real facility must be assigned.
    status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
).values("facility_id", "facility__facility_name") \
 .annotate(booking_count=Count("pk")) \
 .order_by("-booking_count", "facility__facility_name", "facility_id")[:5]
```

`values()` selects grouping fields. `Count("pk")` counts booking records in each facility group. Descending counts choose the leaders; name and ID make ties stable and prevent facilities with the same name from merging. `[:5]` limits the database result. Joining the name inside this query avoids a separate facility lookup per row.

Dates follow existing facility usage analytics, not request creation dates:

- A dated reservation counts when `booking_date` is within the inclusive global start/end dates.
- A stay with no `booking_date` counts once when check-in/check-out overlaps the selected period. Checkout is exclusive: checkout on the range's first day does not count. Zero-length/reversed stays are excluded.
- A booking with no usable dates or no assigned facility does not qualify.
- Hostel counts are bookings, not room-nights. This card is a count ranking rather than utilization.
- Current facility maintenance/archive state does not erase historical valid bookings; this ranking counts historical usage rather than currently available capacity.

### Filter and refresh behavior

Today, Last 7 Days, Last 30 Days, This Month, Previous Month, This Year and Custom Range all use the existing global control. Changing it or pressing Refresh recalculates the ranking. Previous Month uses the entire previous calendar month and compares it with the entire month before that, including year/leap-month boundaries.

Booking Trend Daily/Weekly/Monthly fixes the request to the already applied dates, dispatches `campushub:booking-trend-data`, and updates only Booking Overview. It does not dispatch global loading/data events, rebuild ranking rows, alter their counts, or switch other cards out of their existing sample modes. Booking chart failures use its own Retry; global failures show this card's error state. Ranking Retry clicks the existing global Refresh.

## 5. Backend / API Behavior

No new page or endpoint was created. The existing authorized `GET /api/admin/dashboard/` response adds `facilities.most_booked_facilities`. Existing Super Admin access checks remain. The old singular fields remain for existing consumers/domain dashboards.

Only real records supply this card in real mode. The subsequently requested Show sample mode previews illustrative counts in memory; it never changes the API/database. Its optional row navigation was left out because the current Bookings route does not accept a facility preset—the facility selector is client-side. No duplicate booking page was created.

## 6. Database / Migration Impact

None. No production names, bookings, approvals, quantities or sample records were added/changed. No migration is required. All fixtures and test-only ranking names were created in Django's separate test database.

## 7. Tests Performed and Manual Steps

- **57 Django tests passed** across the new ranking module and existing dashboard booking/period modules. They cover top-five limits, actual approval statuses, out-of-range/orphan exclusion, one-query grouping, overlapping stays/checkout boundaries, stable duplicate-name ties, all global presets/custom dates, grouping independence, empty/populated markup and calendar boundaries. Django system checks reported no issues.
- Actual-render JavaScript integration passed: ranking nodes/counts and booking KPI snapshots preserved during booking grouping (including a response with newly recorded activity), local failure/Retry, global refresh to empty, invalid responses reported as errors, and facility names safely rendered as text.
- Existing marketplace sample/independent-sales integration passed after the shared filter change.
- Four actual headless Chrome checks passed: empty/populated at 1200px and 500px viewport widths. Verified no card/row/page overflow, five real test rows, empty visibility, shared border/radius/title size, 16px padding and right-aligned counts. Visually inspected the populated narrow screenshot.
- JavaScript syntax checks passed for the three affected browser scripts.
- The new CSS parsed successfully. Live Django static requests returned HTTP 200 for the new CSS and JavaScript.

### Manual test steps

1. Open the Super Admin dashboard and press **Ctrl+F5**.
2. Under Facilities Analytics, find Most Booked Facilities. Check its title/subtitle, matching product-card design and actual counts. If there are no qualifying bookings, check the exact empty message.
3. In Bookings, identify an existing Approved or Completed record and its reservation/stay dates. Select a global range containing those dates. Check that the facility appears with the correct count, then choose a range that excludes it.
4. Check Today, Last 7 Days, Last 30 Days, This Month, Previous Month, This Year and a valid Custom Range. Compare counts with the corresponding valid booking records.
5. Change Booking Trend Daily/Weekly/Monthly. Its chart grouping should change while facility rows/counts remain unchanged.
6. Press global Refresh. The ranking should reflect current real records. Pending/Rejected/Cancelled records must never raise the count.
7. Resize the browser and tab to the ranking list. Long names should wrap without pushing the count outside the card; scrolling remains possible when needed.
8. For network-error testing, use DevTools to block/offline the dashboard API temporarily. Global Refresh should show Unable to load booked facilities, not a fake zero ranking. Restore connectivity and select Retry. A grouping-only failure should affect only Booking Overview.

### Debugging and a safe learning exercise

If a facility is missing, first check its actual status, facility assignment and reservation dates—not only when the request was submitted. Check the API's `facilities.most_booked_facilities` list in DevTools Network. Correct JSON but wrong appearance points to the template/CSS; wrong counts point to the query/date filter. Check the new asset version and HTTP response when styles appear stale.

Safe exercise: in DevTools Styles, temporarily change this card's row `padding: 4px 0` to `6px 0`. Observe taller rows without changing any count. Resize and verify wrapping/scrolling, then reload to discard the experiment. For backend practice, run the isolated top-five test and read its expected `[6, 5, 4, 3, 2]` counts; never insert example bookings into the live database to make the card look populated.

## 8. Remaining Limitations

The authenticated live dashboard was not driven interactively; browser checks used fresh actual Django test renders with current local assets. A 500px viewport was checked, not every mobile device. Grouping still requests the existing full dashboard JSON, but only Booking Overview consumes its chart-only response. Historical valid records follow their current recorded status; the Booking model does not provide a separate historical status timeline.
