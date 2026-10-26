# Facility Utilization — implementation and learning guide

Updated: 2026-10-06. Scope: the CampusHub **Super Admin dashboard** Facility Utilization card.

Latest change (2026-10-06): remove the empty-state building icon and the sentence **Utilization appears after valid usage and capacity are configured.** Keep only **No facility utilization data yet.** centered in the empty area. The existing sample preview and real-data behavior remain. Click Sales Overview's **Show sample** to preview this card; **Use real data** restores the actual display. Example capacities are not actual database measurements.

## 1. Cause / Reason

The previous card applied booked hours divided by a default eight-hour daily capacity to every facility. That cannot measure hostel room-nights, training slots, laboratory throughput or leased units correctly. This change uses each supported facility type's actual capacity and usage records. It does not copy the percentages in the requested design example.

The UI/UX Pro Max skill's verified empty-state guidance informed the visible unavailable, loading, empty and error states. The card stays flat and compact, with six named rows, navy progress bars, white/light surfaces and gold unavailable markers. Reasons remain accessible and appear as native tooltips when hovering a facility name; valid percentages have visible usage context.

The earlier problem was that a completely unused/unconfigured card repeated six unavailable labels. It now shows the centered **No facility utilization data yet.** message when no type has calculable positive usage. The user requested less decoration/text, so the icon include, helper sentence and their unused CSS rules were removed. If any type has usage, all six rows remain visible, preserving honest unavailable labels for the other types.

### Existing model audit

| Existing model / location | Relevant data | Meaning |
| --- | --- | --- |
| `api/models.py:319`, `Facility` | `facility_type`, `workflow_config`, `slots`, `rooms_units`, `availability_status`, `is_archived` | Type, operating schedule/slot configuration, configured unit count and current exclusions. `capacity` is attendance/person capacity, not laboratory throughput. |
| `api/models.py:433`, `Room` | Facility, room UUID and status | Actual room/unit inventory. Maintenance and other unavailable inventory is excluded. |
| `api/models.py:473`, `Booking` | Facility, room UUID, booking day/times, check-in/out dates, purpose and status | Valid reservations/occupancy assignments. Dates identify usage inside the chosen range. |
| `FacilityBookingRequest` | Mobile details JSON | Existing request metadata; it is not a defined service-throughput ledger and is not treated as one. |
| Facilities `operating_schedule.py` and `mobile_booking.py` | Validated weekly schedule parsing and `configured_slots()` | Reuse the same readable operating configuration as booking availability. |

There is no dedicated laboratory service-capacity/usage model or separate dated lease model in the inspected schema. The current Booking status choices are Pending, Approved, Rejected, Cancelled and Completed; a separate Confirmed state is not implemented. Approved and Completed are therefore the valid recorded usage states here.

## 2. Exact Files Changed

Paths are relative to the project root. Current approximate line numbers and anchors are supplied; search by the function/selector name if they shift.

This latest cleanup changes only `backend/templates/dashboard/partials/facility_utilization.html` (16, empty area), `backend/static/components/css/admin_facility_utilization.css` (4, empty-state alignment), `backend/templates/dashboard/pages/admin_dashboard.html` (21, CSS cache version), `backend/core/modules/reports/test_dashboard_utilization.py` (145, text-only expectation), `scratch/dashboard-global-review/check-facility-utilization.cjs` (51, text-only checks), `CAMPUSHUB_CONTEXT.md` (15) and this guide. No calculation or component JavaScript function changed. The table below documents the complete feature.

| File | Lines / nearby anchor | Added or changed |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_utilization.py` | 15–25, statuses/types; 74, `_hours_or_slots()`; 123, `_rooms_or_units()`; 166, `_snapshot()`; 216, `has_usage`; 222, `build_facility_utilization()` | Type-specific aggregation plus a real-data usage flag for initial empty-state rendering. |
| `backend/core/modules/reports/dashboard_periods.py` | 17; 256–260, `utilization_summary` | Connect aggregation to the resolved global dates and expose its rows/summary in the existing API context. |
| `backend/core/modules/reports/test_dashboard_utilization.py` | 44 onward; 145, `test_no_usage_renders_text_without_visible_rows()`; 160, API/export test | Formula tests plus pending-only usage, zero percentage, text-only empty/hidden list and no sample record inserts. Exports isolated QA fixtures only when its review environment variable is supplied. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 240, accommodation test; 269–279, query-count test | Replace the old hostel-as-hours expectation with actual assigned room-nights; allow at most three additional bounded capacity queries while retaining the no-growth-with-record-count check. |
| `backend/templates/dashboard/partials/facility_utilization.html` | 1, card; 6, conditional list; 16, empty state; 26, `facilityUtilizationSampleData` | Six-row card, centered empty message and explicit UI-only sample inputs. |
| `backend/templates/dashboard/partials/marketplace_icon.html` | 17, `icon == 'facilities'` | Add a shared decorative building SVG. |
| `backend/templates/dashboard/partials/sales_overview.html` | 11, `data-sales-sample-toggle` | Add Facility Utilization to the sample button's accessibility control list. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 21, CSS; 297, partial; 565–566, scripts | Use the new card/assets for the global Super Admin branch. Preserve the existing domain dashboard branch. |
| `backend/static/components/css/admin_facility_utilization.css` | 1–21; 4, `.facility-utilization-empty` | Scoped row styling plus centered message spacing; remove unused SVG/helper selectors and gap. |
| `backend/static/components/js/admin_facility_utilization.js` | 11, `clearSample()`; 16, `state()`; 22, `render()`; 53, sample event; 84–87, global events/Retry | Show empty state from actual usage, calculate preview percentages locally and restore the original real DOM on exit. |
| `backend/static/components/js/admin_dashboard.js` | 482–484, `updateFacilityUtilization()` | Prevent the legacy hours-based renderer from overwriting the new component. |
| `scratch/dashboard-global-review/check-facility-utilization.cjs` | 1 onward | Fixture-based frontend/state regression checks and browser preview generation. |
| `scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` | 31, scripts; 78 onward, sample assertions | Verify the real Show sample button also previews this card and restores its empty display. |
| `CAMPUSHUB_CONTEXT.md` | 15, current Facility Utilization decision | Preserve formulas, exclusions and honest configuration limitations. |
| `docs/facility-utilization.md` | 1 | This report, debugging workflow and practice exercise. |

Local test fixture HTML/JSON, preview HTML, screenshots and DOM/log measurements were regenerated in `scratch/dashboard-global-review/` and `scratch/sales-overview-system-test/`. No live records were seeded for these previews.

## 3. Changes Made

When there is calculable positive usage, the card displays these rows in a fixed order: Covered Court, Function Hall, Hostel, Food Analysis Hub, Training/Assessment Center, Commercial/Stall Lease. Other configured unused rows display **0%**; unknown or zero denominators display **Utilization unavailable**. When every row is unused/unavailable, the list is hidden and the icon empty state appears. Real API zeros and unavailable values remain distinct.

Normal rows, text-only empty state, loading, and error with Retry are distinct. Unclassified facilities are excluded and the card asks the administrator to set their type. Unsupported/missing data is not silently converted into percentages. The explicit sample mode shows 65%, 48%, 72%, 40%, 55%, 80%, calculated from the sample's used/capacity inputs. Refresh/global date changes leave sample mode; Sales grouping does not rebuild it.

The old default-hours utilization is replaced only in this Super Admin card/API utilization field. Other facility charts and dedicated domain dashboards retain their existing behavior. No models or workflows were moved to FastAPI.

## 4. How It Works

### Formulas and precise counting rules

All calculable percentages are `used ÷ available capacity × 100`, displayed to one decimal place with unnecessary decimals removed in initial HTML.

| Facility type | Numerator | Denominator / exclusions |
| --- | --- | --- |
| Covered Court / Function Hall | Union of approved/completed booked time intersecting configured available time, in hours | Actual configured operating/slot hours on the selected dates. Subtract approved/completed maintenance and academic blocks. Merge overlaps to prevent double counting. |
| Hostel | Distinct occupied `(room UUID, night)` pairs from valid dated reservations | Actual usable room count × selected nights, less dated maintenance/academic room blocks. Check-out is exclusive. Maintenance/inactive/unavailable rooms do not contribute. Missing assignments make the type unavailable rather than guessing rooms. |
| Training/Assessment Center | Distinct configured slots with at least one valid reservation overlap | Actual configured daily slot ranges, respecting configured weekdays; slots overlapping valid maintenance/class blocks are unavailable. No inferred slot count from attendance capacity. |
| Commercial/Stall Lease | Distinct leased unit UUIDs with a valid dated lease overlapping the selected range | Usable actual room/unit inventory when present; otherwise the explicitly configured `rooms_units` count. Units blocked during any part of the range are excluded from this unit-based metric. Over-capacity or missing assignments require review. |
| Food Analysis Hub | Not derivable from the current service data model | No configured service-throughput/usage ledger exists. Display unavailable. Do not substitute attendee capacity, booking count or turnaround text for laboratory throughput. |

For leases this is **units occupied at any point in the range**, not average unit-days or end-of-range occupancy. Different dates change which valid leases intersect the range. For time-based bookings, dates/times are reservation dates, not request creation dates. Booking Overview still counts request creation activity for its separate purpose.

Aggregate percentages for a type sum used capacity and denominators across its configured facilities; they do not average individual percentages. If any active facility of that type has missing/ambiguous configuration, the type is unavailable instead of presenting a misleading partial percentage. Archived facilities are excluded entirely; current Maintenance, Temporarily Unavailable and Inactive facilities contribute no usable capacity.

### Functions, inputs and outputs

| Function | Input | Output / responsibility |
| --- | --- | --- |
| `build_facility_utilization(period)` | Resolved global period (`start`, `end`, `days`) | Summary state, six rows and date metadata. Database errors return an error state, not false zeros. |
| `_snapshot(period)` | The same period | Reads facilities, qualifying bookings and relevant rooms in at most three bounded ORM queries, then aggregates by type. |
| `_union(intervals)` | Numeric start/end pairs | Non-overlapping merged intervals, excluding invalid end-before-start pairs. |
| `_subtract(intervals, blocked)` | Available intervals and blocked intervals | Remaining bookable intervals. |
| `_hours_or_slots(...)` | Facility configuration, valid booking records, days and metric mode | Used and available hours/slots; raises `CapacityUnavailable` for unknown configuration. |
| `_rooms_or_units(...)` | Facility, valid dated assignments, room inventory, days and lease mode | Occupied room-nights or distinct leased units and their available capacity. |
| Component `state(value)` | Ready/loading/error state | Controls content visibility, error/loading messages and `aria-busy`. |
| Component `render(summary)` | Existing API's utilization summary | Creates six rows and accessible meters, keeping null unavailable values separate from numeric zero. Invalid/missing summaries show error. |
| Component sample event handler | Existing `campushub:marketplace-sample` event and local sample JSON | Store real row nodes/visibility; calculate sample percentages; restore the original nodes and empty message on exit. No fetch or database write. |
| Component `clearSample()` | No arguments | Remove the preview flag, accessibility announcement and saved snapshot when real loading/data replaces the preview. |

Data flow: database records → Django global period → type-specific aggregation → initial Django partial or `facilities.utilization_summary` JSON → component renderer → CSS bars. API rows are also exposed as `facilities.utilization`; those rows now use `percentage`, `used`, `capacity`, `unit`, `state` and `context` rather than the old generic `booked_hours`/`util_pct` shape.

### Annotated calculation example

```python
available = _subtract(periods, blocks)  # Remove unavailable time first.
intersections = [
    (max(left, start), min(right, end)) # Clip each booking to valid operating time.
    for left, right in available
    for start, end in usage
]
used = sum(right - left for left, right in _union(intersections)) / 60
# _union prevents two overlapping bookings from counting the same minutes twice.
```

This is an explanatory excerpt of the hourly approach. The actual function totals usage across selected dates. Guarding missing configuration before dividing is preferable to a default denominator or artificially clamping incorrect records to 100%.

## 5. Backend / API Behavior

The existing authenticated `/api/admin/dashboard/` endpoint and resolved date parameters are reused. No new route or permission bypass is introduced. Global filters/Refresh emit loading/data/error events; Retry clicks Refresh. Sales Trend grouping does not update this card. The sample toggle now previews it locally; real requests clear the preview. The summary's additive `has_usage` boolean means any ready row has `used > 0`, allowing server-rendered HTML and JavaScript to agree on the empty state.

Preview data flow: explicit Show sample click → existing sample event → JSON inside the utilization partial → `used / capacity * 100` → the same row renderer. Example: `26 / 40 * 100 = 65%`. Use real data restores the saved real nodes and their visibility. No sample fields are submitted to Django.

The legacy dashboard script skips this component so it cannot replace type-aware values with its old hours renderer. The new renderer works even when Chart.js fails to load because horizontal meters do not depend on the chart library.

The query budget adds at most three capacity queries, independent of record count. The original full-dashboard cap of 21 becomes 24; the test still checks equal query counts before and after adding 20 orders. The existing permissions tests are included in the regression suite.

## 6. Database / Migration Impact

None. Models, schema, migrations and live records were not changed. A read-only audit found one live Covered Court with operating text `Monday-Saturday 8:30am`, no closing time, and no room records. The remaining requested types have no live facility records in that audit. The current real card therefore shows the text-only empty state; the API retains the actual unavailable reasons. Sample preview does not repair or overwrite these configurations.

To obtain a Covered Court percentage, use Facilities → edit the court → save its **actual** complete weekday opening and closing schedule. Do not invent a closing time for the purpose of making a chart appear. Hostel needs actual room inventory and dated room assignments; training needs actual slot ranges; leases need configured units and valid dated unit assignments. Food Analysis requires a separate future service-capacity/usage implementation following its laboratory workflow.

## 7. Tests Performed

- **Latest text-only cleanup: 15 existing Facility Utilization tests passed**, including refreshed actual-template fixtures. The existing empty-state test now checks the icon/helper are absent, main message remains, and pending usage does not become a real metric.
- Component Node checks passed for text-only empty rendering, sample percentages, real restoration, loading/error/Retry, independent grouping and CSS parsing. Chrome verified the empty message, no SVG/helper, and fitting card width; screenshot `scratch/dashboard-global-review/facility-utilization-empty-text.png` was visually inspected.

- **Preceding preview/empty-state change: 35 Django tests passed** in `modules.reports.test_dashboard_utilization` and `modules.reports.test_dashboard_marketplace`. Includes the pending-only/no-usage initial-render test and regenerated real template fixtures.
- Both Node component and full-dashboard integration checks passed: six sample percentages, no requests during preview, real restoration, zero/unavailable empty display, loading/error/Retry and independent Sales grouping.
- Five latest Chrome device-metrics cases passed: empty/sample/real at 800px, empty/sample at actual 360px. Screenshots were visually inspected. Evidence: `facility-utilization-empty-800.png`, `facility-utilization-sample-360.png` in `scratch/dashboard-global-review/`.
- **Before this follow-up, 81 Django tests passed** across global periods, Booking Overview, Marketplace Analytics and Facility Utilization. Coverage includes status exclusions, clipped dates/hours, union of overlapping usage, maintenance/academic blocks, room-night checkout, missing room assignments, slot deduplication, distinct leased units, zero/missing capacity, no fake food-service denominator, malformed schedules, empty/error states, query limits and global API dates.
- The prior hostel test now creates an actual hostel room/assignment and expects four room-nights, replacing its invalid 32-hours assumption. The query-growth test retains its independent row-count check under the documented 24-query budget.
- One existing fixture export test was rerun successfully after wiring the component into the complete dashboard template.
- Frontend regression checks passed for initial/refresh rendering, six types, loading/error/Retry/recovery, no-facilities empty state, invalid summaries, null versus zero, independent Sales grouping, marketplace samples and the legacy renderer guard. Existing global date/error/race/refresh integration also passed with the new script included.
- Five headless Chrome render cases passed: ready, empty, error, loading and narrow-window layout. A separate device-metrics check verified an actual **360px viewport**, six fitting rows and five real fixture-derived meters without page overflow. Desktop and true-360px screenshots were visually inspected.
- JavaScript syntax, CSS parsing and changed tracked-file whitespace checks passed. The live data audit and utilization calculation were read-only.

Real-mode QA evidence includes `scratch/dashboard-global-review/facility-utilization-ready.png`, `facility-utilization-mobile-360.png`, the state `.dom.html` files and the isolated `.source.html`/`.json` files. Those values are calculated from test database records. The newer `facility-utilization-sample-*.png` files intentionally show hypothetical UI preview inputs; they are not production measurements.

### How to test manually

1. Use Ctrl+F5 on the Super Admin dashboard and find FACILITY UTILIZATION.
2. Select Today, Last 7 Days, Last 30 Days and a custom range. For configured capacities, confirm context and percentage reflect valid usage **overlap** in that range.
3. Check a known Pending/Rejected/Cancelled booking: it must not increase usage. Approved/Completed overlapping reservations count the shared time/room-night/slot/unit only once.
4. With no calculable usage, confirm only the main empty message remains in the empty area. With any positive usage, check other unavailable rows' reasons by hovering their names; unused configured rows show 0%. The API still distinguishes unknown capacity from zero usage.
5. Narrow the viewport to 360px. Facility names, percentages, contexts and bars should fit.
6. In Developer Tools, block the dashboard API and press Refresh. Confirm the utilization error and Retry instead of stale percentages. Unblock, then Retry to restore real data.
7. Click Show sample: verify six bars at 65%, 48%, 72%, 40%, 55%, 80%. Daily/Weekly/Monthly should leave those bars unchanged. Use real data must restore the original real card. Refresh must clear preview and load actual values.

### Debugging

| Symptom | Evidence / code to inspect |
| --- | --- |
| Empty message instead of rows in real mode | Expected when all real `used` values are zero/unavailable. Inspect API `has_usage` and each row's `context`; this does not prove there are no pending bookings. |
| Preview missing | Check the new versioned script, `facilityUtilizationSampleData`, and the Show sample button. Reload with Ctrl+F5; inspect Console for malformed JSON. |
| Covered Court unavailable | Inspect its weekly opening/closing configuration. An opening time alone is insufficient. |
| Hostel unavailable despite a room count | Actual Room inventory and matching room UUID/date assignments are required; a bare counter is not invented occupancy. |
| Food Analysis unavailable | Expected until both service throughput capacity and its valid usage records exist. Attendee capacity is not an alternative. |
| Wrong or unexpectedly high percentage | Compare `used`/`capacity`, exclusions, assignments and the chosen dates; check the appropriate union/deduplication helper. Lease over-capacity is unavailable rather than clamped. |
| Refresh reverts to hours | Check that the updated `admin_dashboard.js` guard and new component asset loaded. |
| Blank/error card after fetch | Inspect `facilities.utilization_summary`, six rows and valid numeric percentages. Check Network status and Console. |

See [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) for the issue-record template. No new unresolved calculation failure remains after the listed checks; missing production configuration and unsupported service recording are the limitations below.

### Safe practice exercise

Use Developer Tools to temporarily change `.facility-utilization-meter` height from 6px to 8px. Observe that the bars become thicker but their percentage and usage context do not change. Reload to discard the edit. Then inspect the API's `used`, `capacity` and `percentage` to explain why changing CSS cannot correct a missing denominator. This exercise teaches the separation between presentation and backend calculation without writing live records.

For a second reversible exercise, in a local development copy change only Covered Court's **sample JSON** `used` from 26 to 20, keeping capacity 40. Reload and click Show sample: it should show 50%. Use real data must still restore the actual empty message/rows. Revert the sample change afterward. This teaches inputs → formula → UI without creating bookings.

For this cleanup, a simple practice exercise is to edit only the empty message text temporarily in Developer Tools. Verify Show sample still shows bars and Use real data restores the empty area. Reload to discard the text edit; it does not change database usage or capacity. If the old icon/helper still appears, reload with Ctrl+F5 and check the template source and CSS version at the paths above.

## 8. Remaining Limitations

- Preview values are deliberately hypothetical and displayed only after the explicit sample toggle. Food Analysis's sample 40% does not mean the production service ledger exists. Reload starts in real mode; the preview is not persisted.
- Completely unused or uncalculable cards use one empty state. Inspect API row contexts to distinguish missing configuration from valid zero usage; all per-type reasons remain visible once another type has positive usage.

- Food Analysis currently has no service-capacity/usage ledger, so a valid percentage cannot be supplied. This change deliberately does not build a substitute laboratory workflow.
- Configuration controls for additional capacity workflows were not added. Training calculations require stored valid slot ranges; hostel calculations require actual rooms; lease records require unit/date assignments. Missing data remains unavailable.
- Facility/Room statuses have no historical availability ledger. Current exclusions apply throughout the selected period; dated approved maintenance/class records allow more precise exclusions. Past state changes cannot be reconstructed.
- Lease occupancy means units used at any point in the range, not a time-weighted average. Any dated unit block removes that unit from this period-level metric.
- A separate Confirmed booking status is not part of the current model. If added later, update both the valid-status mapping and Booking Overview's status mapping with tests.
- Unknown/unclassified facility types are excluded and reported. A partially configured facility group remains unavailable rather than silently omitting its missing capacity.
- Firefox, Safari, physical touch devices and screen-reader software were not separately tested. No unrelated chart formulas or dedicated domain dashboard cards were redesigned.
