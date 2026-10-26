# Today comparison and floating custom dates

## Cause / reason

The API already resolves Today against yesterday. However, Sales Overview comparison text stayed visible during pending requests, and changing grouping while a preset request was pending could request the previously applied period and supersede the preset request. A failed preset request also left the selector showing the requested period while the displayed cards still belonged to the previous period. Sales comparison text was constrained to a single clipped line.

The prior custom-date layout occupied normal document flow. Opening it enlarged the header and shifted the KPI cards. The user requested a floating panel over the KPI area.

## Exact files changed

- `backend/static/components/css/admin_dashboard_filter.css`
- `backend/static/components/js/admin_dashboard_filter.js`
- `backend/templates/dashboard/pages/admin_dashboard.html`
- `backend/core/modules/reports/test_dashboard_periods.py`
- `scratch/dashboard-global-review/check-controls.cjs`
- `scratch/dashboard-global-review/dashboard.html`
- `scratch/dashboard-global-review/payload.json`
- `scratch/dashboard-global-review/payload-today.json`
- `docs/dashboard-period-popup-fix.md`

## Changes made / how it works

- Custom dates use absolute positioning relative to the filter form, beneath the selector. The panel is excluded from header height and overlays the KPI area. Its horizontal position is constrained within 16px of the viewport edges on opening and resizing. Its fields wrap on narrow screens. Cancel and Escape close it and restore the applied period.
- Grouping changes and the Sales Overview form use the pending requested period while a dashboard request is active, then the applied period after completion. Superseded responses remain ignored.
- Comparison lines become transparent during loading, along with the metric values, rather than showing an old period beside a new selection.
- Failed requests restore the selector and dates to the last successfully displayed period. Retry retains the failed requested period.
- Sales comparison text wraps to show the full previous-period label and returns to green after loading.
- Stylesheet and script versions were updated.

## Backend / API behavior

No business logic, endpoint, authorization, or aggregation changes. Today remains compared with yesterday using the existing API. Added regression assertions verify both API comparison text and server-rendered Today markup. The test-generated Today payload also drives frontend verification.

## Database / migration impact

No migrations or production database writes. Review artifacts use existing isolated Django test fixtures.

## Tests performed

- Django global dashboard markup/review test passed, including all six Today comparison lines and absence of previous 30 days in Today markup. Django system check passed.
- DOM integration check passed with all five dashboard stylesheets: real API Today payload displayed as yesterday; grouping during a Today request retains Today; stale responses are ignored; failed requests restore the displayed period; custom popover positioning is checked against simulated 1024px and 360px viewport bounds.
- Existing refresh, authentication parameter preservation, KPI/chart updates, custom validation/apply/cancel, error/retry, loading, and missing-chart-library checks passed.
- CSS parsing, JavaScript syntax, and scoped whitespace checks passed.

## Remaining limitations

An interactive browser was unavailable. DOM checks and simulated bounds verify state and positioning calculations, but do not prove the final pixel layout or native date-picker appearance. The original persistent Today issue was not reproduced in a live browser; the identified stale-display and request-state paths are now corrected and covered. The design detector used its degraded regex fallback because parser dependencies were unavailable.
