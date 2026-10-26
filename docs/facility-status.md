# Facility Status — operational states on the Super Admin dashboard

Implemented 2026-10-07. UI/UX Pro Max was used to check the existing donut/legend layout and accessibility. This update targets the global Super Admin dashboard card.

## 1. Cause / Reason

Confirmed by inspection: `Facility.STATUS_CHOICES` already defines Open for Booking, Temporarily Unavailable, Under Maintenance and Inactive. The dashboard nevertheless used an old `availability` response and legend with Available/Occupied/Maintenance/Blocked. That mapping could omit Unavailable/Inactive records and its donut center could disagree with the initial total. Schedule conflicts were also displayed inside this operational-status card.

The new card reads real facility-level state, independently of reservation dates, room occupancy and time slots. No new database status field is introduced.

## 2. Exact Files Changed

Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Line numbers are current for this update; search by the nearby anchor when they move.

| File / folder | Current line / code anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_facility_status.py` | 6, `facility_operational_status(facilities)` | Add a helper deriving operational counts from the already-loaded Facility objects. |
| `backend/core/modules/reports/views.py` | 317, helper import; 435, `operational_status` | Include the helper output in shared facility analytics consumed by the initial page and existing API. |
| `backend/templates/dashboard/partials/facility_status.html` | 1, `data-facility-operational-status`; 3, layout; 8, legend; 14–18, states | Add the operational legend, current donut layout, total/unit, exact empty/error messages and Retry. No conflict footer. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 24, CSS; 358, partial; 589, JS | Replace only the Super Admin card with the new partial and load scoped assets. |
| `backend/static/components/css/admin_facility_status.css` | 2, card scope; 6, legend grid; 17, container query | Keep existing card/donut foundations; add navy/gold/navy-tint dots, readable aligned labels/counts, hidden-state rules, Retry focus and narrow-card stacking. |
| `backend/static/components/js/admin_facility_status.js` | 12, `state`; 17, `render`; 61–65, events/Retry | Validate real data, update chart/legend/total, distinguish empty/loading/error and refresh through existing controls. |
| `backend/core/modules/reports/test_facility_operational_status.py` | 19, `FacilityOperationalStatusTests` | Add selection/mapping/error/snapshot/template tests and isolated browser fixture exports. |
| `scratch/facility-operational-status/check-card.cjs` | 1, integration harness | Verify actual rendered-page interactions using isolated API fixtures. |
| `scratch/facility-operational-status/check-browser.cjs` | 1, actual Chrome harness | Check the real Chart.js donut, labels and states at desktop/narrow widths. |
| `CAMPUSHUB_CONTEXT.md` | Current Facility Status note | Preserve the accepted operational mapping and snapshot behavior. |
| `docs/facility-status.md` | This guide | Explain functions, data flow, troubleshooting, verification and safe practice. |
| `docs/dashboard-global-date-filter.md` | Update near the beginning | Link the operational current snapshot and its test/debugging guide. |

Existing sources inspected and reused, **not changed**: `api/models.py:329` (`Facility.STATUS_CHOICES`), `api/models.py:377` (`availability_status`, database column `status`), `api/models.py:380` (`is_archived`), `modules/facilities/services/facility_configuration.py:154` (`normalize_facility_status`), and the existing conflict handling in `dashboard_attention.py`.

## 3. Changes Made / Status Mapping

The old legend labels **Available, Occupied, Maintenance and Blocked** are removed from this Super Admin card. Legend labels now come directly from `Facility.STATUS_CHOICES`:

| Existing stored value | Card label | Meaning / handling |
| --- | --- | --- |
| `available` | Open for Booking | Non-archived facility currently accepts bookings; this does not mean every schedule slot is free. |
| `unavailable` | Temporarily Unavailable | Facility temporarily disabled. |
| `maintenance` | Under Maintenance | Facility disabled for maintenance. |
| `inactive` | Inactive | Facility retained in the system but disabled until reactivated. |
| Legacy `occupied` / `reserved` | Temporarily Unavailable | Reuse the existing normalization service; do not expose occupancy as a facility legend state. No database rewrite. |
| Any archived facility | Inactive | `is_archived` already prevents booking even if the old stored status was left `available`. Count it once as disabled/history. |
| Unknown/blank non-archived status | Error state | Do not silently invent an Open status or display made-up zero counts. |

Every stored facility is included in the center total, including retained inactive/archived records. The sum of the four operational counts equals that total. Zero records show **No facilities available.** instead of a zero donut. One record displays **1 / Facility**; two or more display **N / Facilities**.

The card preserves its existing flat white surface, border, spacing and donut dimensions, including 68% cutout, hidden built-in legend and disabled animation. It uses navy, gold and lighter navy tints; the textual legend provides the exact counts so color is not the only information. In narrow card containers the existing donut moves above the legend rather than clipping long labels. No additional graph or mini-card is added.

Schedule conflicts are removed from inside this card. Existing conflict calculation and the Attention Required item remain, with the existing Bookings/Calendar workflow handling resolution. Legacy domain dashboards and old response fields are retained for existing consumers; this request changes the Super Admin card.

## 4. How It Works / Functions, Inputs and Outputs

| Function / structure | Input | Output / responsibility |
| --- | --- | --- |
| `facility_operational_status(facilities)` | Already-loaded Facility objects | `{state, total, rows}` with four `{key, label, count}` rows, or `{state: 'error'}` for unsupported data. Adds no queries. |
| `normalize_facility_status(value)` — existing service | Stored legacy/current string | Trimmed lowercase operational value; reserved/occupied map to unavailable. |
| `_facility_dashboard_analytics(...)` | Reporting dates plus current Facility data | Adds `operational_status` to its existing result. Other usage/revenue/conflict computations keep their own rules. |
| Existing `build_dashboard_data(...)` | Authorized dashboard request | Exposes that result as `facilities.operational_status`. |
| Django partial | `facility_analytics.operational_status` | Escaped initial labels/counts, correct total/unit and honest empty/error state; JSON data for initialization. |
| Browser `render(data)` | The operational object from initial JSON or a real global response | Checks nonnegative integers, four expected keys, total/count consistency and valid state; renders safe text and updates Chart.js. |
| Browser `state(value)` | `ready`, `empty`, `loading` or `error` | Shows only the appropriate content and updates `aria-busy`. |

Data flows **existing Facility records → already-loaded list in report analytics → operational helper → shared Django context/API result → initial template or refresh renderer → donut + exact legend counts**. This is a response dictionary, not a second model field.

Annotated core example:

```python
counts = dict.fromkeys(dict(Facility.STATUS_CHOICES), 0)  # Same allowed statuses as the model.
status = Facility.STATUS_INACTIVE if facility.is_archived else normalize_facility_status(raw)
counts[status] += 1                                    # Count this actual facility once.
```

The real helper checks raw/unknown values before incrementing. These zeros are aggregation starting values, not fake facility records. Empty database results and failures are separate states. Reusing the existing loaded list avoids an extra SQL count query per status or per facility.

### Frontend validation and accessibility

The renderer requires keys in the model order `available`, `unavailable`, `maintenance`, `inactive`, with safe integer counts whose sum matches the total. Unsupported payloads show the error message and hide the data layout. Names/labels use `textContent`, not HTML injection.

The canvas has a readable summary of all labels/counts, and the visible text legend provides the same exact data. Retry is a native button with a visible focus ring and 44px target height. Loading and error messages use status/alert roles. If Chart.js cannot load/draw, the genuine center total and labelled counts remain available; the chart itself is hidden when drawing fails. A chart-library issue does not become a fabricated API zero total.

## 5. Backend / API Behavior

No new endpoint or route. Existing authentication/Super Admin authorization for `/api/admin/dashboard/` remains. Successful responses include `facilities.operational_status`; both initial HTML and refresh use the same helper.

Facility Status is a **current operational snapshot**, independent of historical reporting dates and chart grouping. Creating a Pending/Approved/Completed booking does not change an Open facility into Occupied. Slot availability remains in the booking/schedule workflow. Global dates and Refresh fetch the current snapshot again; Sales/Booking grouping and Show sample do not modify this card.

Network/API failure triggers **Unable to load facility status.** with **Retry**. The old data layout is hidden rather than replaced with zero values. Retry uses the existing global dashboard Refresh button. A malformed/unknown stored status shows this card's error while other successful dashboard data can remain available; Retry cannot repair an invalid source status automatically.

## 6. Database / Migration Impact

No new field, migration, status rewrite, booking insertion, live archive operation or other database mutation. Existing `availability_status` (`campushub_facility.status`) and `is_archived` are read. Approved bookings and their dates are not used in this card's status selection. Tests write only isolated Django test fixtures.

## 7. Tests Performed

- From `backend/core`: `venv\Scripts\python.exe manage.py test modules.reports.test_facility_operational_status modules.reports.test_dashboard_periods modules.reports.test_upcoming_reservations modules.reports.test_most_booked_facilities modules.reports.test_dashboard_bookings --keepdb --noinput`: **75 passed**, system check clean.
- New tests cover the exact 3/1/1/0 five-record example from isolated fixtures, no extra helper queries, archive override, legacy normalization without rewriting records, unknown/blank error states, booking/date/grouping independence, preserved conflict counts, and initial empty/singular/populated/error markup. The existing fixed query-budget regression still passes.
- After simplifying the hidden error-state noun fallback, the template/API export test was rerun: **1 passed**.
- `node --check backend/static/components/js/admin_facility_status.js`: passed.
- `node scratch/facility-operational-status/check-card.cjs`: passed for actual template/payload fixtures, donut labels/counts, singular/plural, grouping/sample independence, global loading/empty/error/Retry, malformed payloads and no-Chart fallback. The harness uses a stubbed fetch/Chart for interaction checks, not a live signed-in session.
- Actual Chrome with local real Chart.js: empty, single, populated and error at 1200px/500px viewport widths — **eight checks passed**. The narrow preview uses a roughly 292px card to exercise container stacking. Real chart creation, legend fit, totals/nouns, exact states and no horizontal overflow were checked. The narrow populated PNG was visually inspected. Single/error cases were checked again after the final fallback/hidden noun adjustment.
- Running local Django served both new CSS/JS files with HTTP **200**. `git diff --check` passed for the changed tracked template/view files.

The sample chart image uses isolated test records, not hardcoded dashboard counts. A live authenticated dashboard/Calendar session was not driven in these checks.

### Manual test steps

1. Log in as Super Admin, open Dashboard and press **Ctrl+F5**. Verify the four new labels and no Schedule conflicts footer in this card.
2. Compare counts with existing facility operational states. In a development/test database, use the existing Facilities management form to change a facility through each allowed status; Refresh and verify the correct bucket changes.
3. Test one facility: the center must read **1 Facility**. With no facilities in a disposable test database, verify **No facilities available.** Do not delete live facilities for this check.
4. Create/approve a timed booking through the existing workflow. The facility must remain Open for Booking if its operational field was Open. The reserved time slot belongs in Bookings/Calendar.
5. Check a retained archived facility is counted Inactive. Restore it through the existing workflow, then confirm its current operational state after Refresh.
6. Switch global historical dates, Sales/Booking grouping and Show sample: this card stays a real current operational snapshot. Global requests may show loading and fetch current values again.
7. Switch browser DevTools Network to Offline, then Refresh. Verify the error/Retry state without a visible zero donut. Restore Online and Retry.
8. Check known schedule conflicts under Attention Required or Bookings/Calendar; their calculation is still present outside this card. Narrow the window and tab to Retry to check wrapping/focus.

### Debugging / Troubleshooting

| Symptom | Evidence to inspect | Code anchor / action |
| --- | --- | --- |
| Old legend still appears | Current role/page and loaded asset/template versions | New card is global Super Admin only; `admin_dashboard.html:357` selects it. Hard-refresh. |
| Counts are unexpected | Facility `status`, `is_archived`, legacy values; compare API rows, not booked slot counts | `dashboard_facility_status.py:6`. Archived is an inactive override; legacy occupied/reserved use the existing unavailable conversion. |
| Error after successful API response | `facilities.operational_status.state` and server-side field values | Unknown/blank states return error. Fix source data through the existing facility workflow; do not hide it by coercing to zero. |
| Counts fail to refresh | Dashboard API HTTP status, JSON payload and browser console | New response at `views.py:459`; listener at `admin_facility_status.js:63`; Refresh remains the existing protected request. |
| Donut missing but correct counts visible | Chart.js CDN/network and browser console | Real text fallback is intentional. Restore chart loading and Refresh/reload; do not fabricate chart data. |
| Totals disagree with slots/room occupancy | Whether the comparison is a facility count versus reservation/room usage | This card counts facility records; it never counts occupied rooms, bookings or slots as facility statuses. |

These are investigation steps, not claims that all such issues exist. Record actual evidence and results using `docs/DEBUGGING_GUIDE.md`.

### Safe learning exercise

In browser DevTools Styles, change this card's legend row padding from `10px 0` to `8px 0`. Observe tighter spacing while verifying all counts, the total and status labels stay identical. Resize the card, then reload to discard the experiment. This demonstrates that CSS changes presentation while the helper/API determine business data. Do not edit status keys, counts, or live facility records for a spacing exercise.

## 8. Remaining Limitations

- This targets Super Admin; existing domain dashboards/legacy `availability` consumers keep their earlier UI/data contract.
- The current model does not provide historical operational status timelines, so selecting a historical reporting range does not reconstruct past facility states.
- Legacy occupied/reserved values follow the existing unavailable conversion conservatively; changing their persisted meaning requires reviewing the actual facility through the normal management workflow. This update does not rewrite them as Open.
- Chart.js depends on its existing loaded library. The real labelled counts remain readable when drawing is unavailable.
- The existing Total Facilities KPI retains its own raw-field summary; this card's effective Inactive bucket also respects the archive flag. No KPI redesign was requested.
