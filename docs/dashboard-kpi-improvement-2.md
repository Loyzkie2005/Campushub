# CampusHub dashboard Improvement #2

## Reason and result

Some KPI secondary lines were static, pending approvals had no queue breakdown, facilities showed additions rather than current status, and all six existing change lines were forced green. All eight System Overview cards now share one secondary component with structured descriptive or comparison data. The existing layout, icons, date filter, and primary-total definitions are preserved.

## Files, approximate lines, and nearby anchors

| Folder / file | Line | Nearby anchor | Change |
| --- | ---: | --- | --- |
| `backend/core/modules/reports/dashboard_periods.py` | 79 | `def comparison_metric` | Structured trend state, direction, semantics, comparison label, and secondary text; zero-baseline new activity. |
| Same file | 99 | `def descriptive_metric` | Shared snapshot context without a performance percentage. |
| Same file | 124 | `sellers = User.objects` | Current distinct active sellers plus recorded approvals in the selected period. |
| Same file | 141 | `facilities = Facility.objects.aggregate` | Current counts for Open for Booking, Temporarily Unavailable, Under Maintenance, and Inactive. |
| Same file | 185 | `kpis =` | Secondary information for all eight cards, including the pending queue breakdown. |
| `backend/templates/dashboard/partials/kpi_secondary.html` | 1 | `dashboard-kpi-secondary` | New reusable server-rendered secondary component and semantic attributes. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 55 | `kpi_secondary.html` | Reuse the component for every card; also lines 70, 84, 99, 114, 129, 158, and 172. Asset versions updated at lines 16 and 608. |
| `backend/static/components/css/admin_dashboard_filter.css` | 22 | `.dashboard-stat-card` | Label 13px/600, value 28px/700, secondary 12px/400; readable wrapping; scoped positive, negative, neutral, and attention styles. |
| `backend/static/components/js/admin_dashboard_filter.js` | 53 | `const secondary =` | Update text and semantic/direction/state attributes from the existing API after period changes. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 54 | `test_trend_states_and_semantics` | Trend edge-case regression coverage. |
| Same test file | 159 | `test_recorded_seller_approvals` | Distinct approval counts, inactive/suspended exclusion, missing-date fallback, facility statuses, pending queue snapshots, and review artifacts. |
| `scratch/dashboard-global-review/check-controls.cjs` | 48 | `checkKpis` | Verify all eight secondary fields, colors, regular weight, loading behavior, and subsequent negative/attention responses. |
| `scratch/dashboard-global-review/dashboard.html` | 1 | Rendered review HTML | Regenerated from isolated Django fixtures. |
| `scratch/dashboard-global-review/payload.json` | 1 | `kpis` | Regenerated seven-day API review response. |
| `scratch/dashboard-global-review/payload-today.json` | 1 | `kpis` | Regenerated Today API review response. |
| `scratch/dashboard-global-review/payload-decline.json` | 1 | `kpis` | New real isolated-test response with declining revenue, recorded seller approval, maintenance, and pending items. |
| `docs/dashboard-kpi-improvement-2.md` | 1 | Report title | This implementation and manual-testing report. |

## Backend calculations and API behavior

The existing `/api/admin/dashboard/` endpoint remains in use. Each KPI now provides `secondary_text`, `semantic_type`, `trend_state`, and `direction` alongside its existing values. No duplicate endpoint or authorization changes.

Snapshot KPIs:

- **Total Users:** current `accounts.User` total; selected-period additions use `date_joined`.
- **Active Sellers:** current distinct active, non-suspended users with Seller role or approved seller access. `approved_in_period` counts distinct current active sellers with approved requests whose `reviewed_at` falls within the selected range. Multiple requests for one user do not multiply this count. `activation_dates_missing` identifies active sellers without a dated approved request.
- **Total Products:** current non-archived products, preserving the previous dashboard definition, including pending/rejected records. Secondary additions use `submitted_at`. Pending product counts remain separate.
- **Total Facilities:** all current facilities, with stored `availability_status` counts. This does not infer facility status from booking occupancy. Unknown/legacy status values are counted as other statuses. No configured facilities receives an explicit empty description.
- **Pending Approvals:** current pending products + pending seller requests + pending bookings, with all three counts displayed and singular/plural labels. It is an attention queue, without a growth percentage.

Period KPIs:

- **Total Orders:** all orders created within the range, preserving existing status inclusion.
- **Total Bookings:** all bookings created within the range, preserving existing status inclusion.
- **Marketplace Revenue:** completed AND paid orders only, using completion time, then payment time, then creation time as the existing fallback.

The seller, facility, and queue details are calculated within existing aggregate queries. Query count remains independent of the number of orders; the existing query-count regression passed. No N+1 queries were added.

## Trends and edge cases

For a positive prior value: `(current - previous) / previous * 100`.

- Increase: upward arrow, real percentage, restrained green.
- Decrease: downward arrow, real percentage, restrained red. The percentage remains signed in API data and is displayed as an absolute magnitude with the downward arrow.
- Equal values: dash and No change, neutral navy-gray.
- Previous zero/current positive: New activity with an upward arrow; percentage is null.
- Both zero: No change; percentage is null.
- Current zero/previous positive: downward 100%.

No Infinity or NaN is emitted. Today compares against yesterday; seven/thirty-day ranges compare against the immediately preceding equal range; month/year/custom comparison behavior is unchanged.

Snapshot additions are descriptive and neutral, without fabricated percentages. Attention descriptions use a gold marker with navy text for readable contrast. No entire card is recolored. Arrows and text provide meaning alongside colors.

The existing loading skeleton hides all eight primary and secondary values until a response completes. Request failures retain the last successful values and the dashboard Retry action; they do not create zero values.

## Manual checks for every KPI

Use existing records or isolated test data, then select Today, Last 7 Days, Last 30 Days, and a custom range.

| Card | Expected check |
| --- | --- |
| Total Users | Main total stays fixed across filters; secondary additions match users created inside each inclusive range. |
| Active Sellers | Main total stays fixed; dated approved requests update the recorded-approval count. Duplicate requests count once per seller. Suspended/inactive users are excluded. Users without approval timestamps never receive invented activation dates. |
| Total Products | Main total stays fixed across filters and excludes archived products; additions match `submitted_at` within the range. Approval-status definitions remain unchanged. |
| Total Facilities | Current status counts remain fixed across date changes. Open/maintenance/unavailable/inactive counts reflect facility records, regardless of booked slots. |
| Total Orders | Value matches all orders created in the selected range. Compare with the preceding equivalent range; test increase, decrease, equal counts, and zero baseline. |
| Total Bookings | Value matches bookings created within the range, using the same comparison and edge cases as orders. |
| Marketplace Revenue | Only completed, paid orders contribute. Confirm unpaid/pending/processing/cancelled orders are excluded. A lower current total produces a red downward percentage; a zero prior total produces New activity. |
| Pending Approvals | The three displayed counts sum to the main value. Changing the date range does not change the current queue. Nonempty queues have a gold attention marker rather than green growth. |

Also check Refresh, grouping changes while a period request is pending, Custom Range Apply/Cancel/Escape, narrow screens, long secondary descriptions, and the dashboard Retry state after a failed request.

## Tests performed

- 38 Django tests passed across `modules.reports.test_dashboard_periods`, `modules.reports.test_sales_overview`, and `accounts.tests.DedicatedDomainDashboardTests`. Django system check passed.
- Updated isolated review-artifact test passed after adding the negative/attention response.
- DOM integration checks with all five dashboard stylesheets passed: all eight secondary fields and weights, neutral/new-activity/negative/attention states, API-driven updates, transparent loading values, date filters, request races, failure rollback/retry, refresh icon state, custom popover, authentication parameter preservation, charts, and missing Chart.js.
- JavaScript syntax, CSS parsing, and scoped whitespace checks passed.

## Database and migrations

No schema changes, migrations, or production data writes. Test review artifacts use isolated database records and are never served as dashboard data.

## Remaining limitations

- `reviewed_at` records approvals, not a complete activation/reactivation audit. The card therefore says approvals recorded rather than claiming every seller was newly activated. Legacy Seller accounts without approval timestamps use an honest current-access fallback; incomplete historical coverage is exposed through `activation_dates_missing`.
- Product totals retain the existing non-archived definition. This change does not redefine them to approved products only.
- An interactive browser was unavailable. DOM and stylesheet verification covers structure and state, but not final pixel geometry, native date pickers, or long-text card height in a live browser. Longer descriptions may wrap while the grid structure, padding, and card minimum height remain unchanged.
- The design detector ran in degraded regex mode because its parser dependencies were unavailable. It is not evidence of a complete visual audit.
