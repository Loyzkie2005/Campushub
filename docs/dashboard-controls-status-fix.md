# Dashboard controls and status refinement

## Reason

The System Status heading was inside the service card. Custom dates were absolutely positioned against the entire toolbar, placing them toward Refresh and the update timestamp. Refresh had no icon or button-specific loading state. Sales Overview comparison text had its own navy override rather than the green used by KPI change text.

## Exact files changed

- `backend/templates/dashboard/pages/admin_dashboard.html`: move System Status and Manage Settings above the service card; update CSS and JavaScript versions.
- `backend/templates/dashboard/partials/global_date_filter.html`: add an accessible Refresh button with an SVG refresh icon.
- `backend/static/components/css/admin_dashboard.css`: apply the existing status-header spacing to the heading outside the card.
- `backend/static/components/css/admin_dashboard_filter.css`: place custom dates in normal flow beneath the selector, allow controls and fields to wrap, animate the refresh icon only while loading, respect reduced motion, and make the complete Sales Overview comparison text green.
- `backend/static/components/js/admin_dashboard_filter.js`: set and clear Refresh `aria-busy` alongside its existing disabled state, including failed requests.
- `scratch/dashboard-global-review/check-controls.cjs`: extend the existing verification script to load all five dashboard stylesheets and check structure, colors, and Refresh loading/reset behavior.
- `scratch/dashboard-global-review/dashboard.html`: regenerate the review page from the isolated Django test database.
- `scratch/dashboard-global-review/payload.json`: regenerate the corresponding isolated test API response.
- `docs/dashboard-controls-status-fix.md`: this implementation report.

## How it works

The section heading is a sibling immediately before the card. The custom date fields occupy space within the filter form rather than overlapping dashboard content. Refresh keeps its text and uses an SVG icon that spins while a request is pending. A scoped green rule covers the complete comparison line, including No change and the previous-period label, before and after AJAX updates.

## Backend and API behavior

No endpoint, authorization, aggregation, or service-health behavior changed. Refresh and date controls still use the existing global dashboard API and update the selected period without a page reload.

## Database and migrations

No schema changes, migrations, or production data writes. Review HTML and JSON use isolated test fixtures.

## Tests performed

- Django global dashboard rendering/review test passed; Django system check reported no issues.
- JavaScript syntax check passed.
- Existing DOM integration verification passed with all five dashboard stylesheets loaded: external System Status heading, custom date flow, green comparisons, refresh icon/loading/reset, period changes, authentication parameter preservation, KPI/chart updates, custom validation/apply/cancel, failure/retry, and Chart.js absence.
- All loaded dashboard CSS parsed successfully.

## Remaining limitations

An interactive browser was unavailable, so desktop/mobile pixel layout and the visible animation were not verified in a live browser. DOM and stylesheet checks verify structure and state, not rendered geometry. The design detector fell back to regex matching because its parser dependencies were unavailable.
