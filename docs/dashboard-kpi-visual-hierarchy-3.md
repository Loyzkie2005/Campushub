# CampusHub dashboard Improvement #3: KPI visual hierarchy

## Reason and before/after behavior

The existing KPI cards combined 13px labels, 48px icon containers, 24px SVGs, mixed icon colors, and a Bootstrap viewport breakpoint that could squeeze currency values into narrow columns. Hover lift and stronger hover shadows also competed with the numbers.

The eight cards now use one compact visual system: navy values are the strongest element; smaller uppercase labels identify the metric; neutral or semantic secondary lines support it; smaller navy icons remain supportive. The grid adapts to actual available content width, including the space remaining after the sidebar. No KPI meanings or calculations changed.

## Exact source files, approximate lines, and anchors

| Folder / file | Approximate line | Nearby anchor | Change |
| --- | ---: | --- | --- |
| `backend/static/components/css/admin_dashboard_filter.css` | 22 | `.dashboard-kpi-region` | Named inline-size container for KPI-specific responsiveness. |
| Same file | 23 | `.dashboard-stats-grid.row` | Scoped CSS grid, equal 120px rows, 16px gaps, and removal of Bootstrap column padding/width constraints within this KPI region. |
| Same file | 25 | `.dashboard-stat-card` | Montserrat preference, standard padding, border/radius, and flat styling without lift or shadow. |
| Same file | 27 | `.dashboard-stat-icon` | Consistent 42px icon containers, 22px SVGs, navy foreground, neutral tint, and subtle gold tint for Pending Approvals. |
| Same file | 32 | `.dashboard-stat-card > div… > span` | 12px uppercase semibold labels with consistent line height and spacing. |
| Same file | 33 | `.dashboard-stat-card strong` | 28px bold navy values, tabular numbers, and no wrapping. |
| Same file | 34 | `.dashboard-stat-card small` | 12px regular secondary text and 5px spacing below values. Existing semantic colors and clipped-text behavior retained. |
| Same file | 35 | `@container dashboard-kpis` | Four/two/one columns based on content width, plus viewport fallback for browsers without container queries. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 43 | `dashboard-kpi-region` | Wrapper around the existing eight-card section for Super Admin only. Its closing wrapper follows the KPI section. CSS version updated at line 16. |
| `scratch/dashboard-global-review/check-controls.cjs` | 48 | `checkKpis` | Existing UI verification updated for the new 5px secondary spacing. |
| `scratch/dashboard-global-review/prepare-kpi-visual.cjs` | 1 | Offline visual QA comment | Create an offline preview from the actual isolated Django-rendered KPI region and project stylesheets. |
| `scratch/dashboard-global-review/verify-kpi-visual.cjs` | 1 | Headless result verification | Validate measured card heights, type/icon sizes, alignment, column count, and value fit from Chrome-rendered DOM results. |
| `docs/dashboard-kpi-visual-hierarchy-3.md` | 1 | Report title | This implementation report. |

## Review artifacts created or refreshed

All files below are under `scratch/dashboard-global-review/`:

- `dashboard.html`
- `payload.json`
- `payload-today.json`
- `payload-decline.json`
- `kpi-visual.html`
- `kpi-desktop.html`
- `kpi-laptop.html`
- `kpi-mobile.html`
- `kpi-desktop.png`
- `kpi-laptop.png`
- `kpi-mobile.png`

The review page uses actual records from the isolated Django test database. It is not production dashboard data. The currency example `₱32,450.00` from the brief is used only momentarily as a layout stress string during measurement, then restored before capture.

## CSS classes and dimensions

All overrides are scoped beneath `[data-global-dashboard]`, so other role dashboards retain their existing presentation.

| Element | Final style |
| --- | --- |
| Card | 120px tall; 18px vertical / 20px horizontal padding; white background; 1px light navy border; 12px radius; no shadow or hover lift |
| Card gap | 16px between cards |
| Icon-to-content gap | 14px |
| Icon container | 42×42px; 8px radius; light neutral background; subtle gold tint for Pending Approvals |
| Icon SVG | 22×22px; navy |
| Label | 12px / 600; uppercase; navy; 1.25 line height; 0.04em letter spacing |
| Main value | 28px / 700; navy `#1A1851`; 1.15 line height; tabular numerals; nowrap |
| Secondary line | 12px / 400; 1.4 line height; existing neutral/positive/negative/attention semantics |
| Label-to-value / value-to-secondary | 5px / 5px |

The existing Montserrat import is reused; no font dependency or asset was added to the application. Existing compact arrows and secondary descriptions remain unchanged.

## Responsive behavior

- KPI region at least 1180px wide: four cards per row.
- KPI region 560–1179px wide: two cards per row.
- KPI region below 560px: one card per row.
- Browsers without container-query support use the scoped two-column default, four columns at viewport width 1480px+, and one column below 768px.

All rows use the same 120px card height. Labels, values, and secondary text remain aligned; long secondary descriptions retain their existing one-line ellipsis and conditional full-text hover help. Revenue values use the same 28px type as the other values and do not wrap.

## How it works / backend and API behavior

The additional wrapper supplies the width queried by the CSS. Existing Bootstrap column classes remain in the template; scoped KPI-grid styles determine their layout within this wrapper. All eight existing card contents, existing SVG artwork, metric attributes, semantic secondary component, loading/retry states, and date-filter behavior remain in use.

No Django service, ORM query, percentage calculation, date-period resolver, seller/approval definition, order/booking inclusion, or revenue logic was modified. The existing dashboard API and RBAC are unchanged.

## Database / migrations

No migrations, schema changes, or production data writes. The existing review test creates only isolated test fixtures.

## Tests and visual inspection

- Existing Django global dashboard render/review test passed; Django system check passed.
- Existing DOM integration check passed with all five dashboard stylesheets, including API-driven secondary fields, semantic colors, loading, Refresh, date filters, custom popover, request races, failure rollback/retry, authentication parameter preservation, charts, and missing Chart.js.
- Headless Chrome rendered desktop and laptop previews plus a constrained 390px mobile frame. All eight cards measured exactly 120px tall in each case; icons measured 42×42px; label/value/secondary fonts measured 12/28/12px; labels, values, and secondary baselines matched within each row.
- Measured column counts were four/two/one at respective content widths 1536px, 960px, and 342px. Existing values and labels fit, and the brief's `₱32,450.00` example fit without wrapping at all three widths.
- All three captures were visually inspected. Chrome's Windows headless minimum viewport caused the initial narrow capture to clip; the preview was constrained to a 390px frame and the final mobile capture was inspected again.
- CSS parsing, helper-script syntax, and scoped whitespace checks passed. The design detector's font warning was retained because the brief explicitly prefers Montserrat.

## Preview links

- [Desktop KPI preview](../scratch/dashboard-global-review/kpi-desktop.png)
- [Laptop KPI preview](../scratch/dashboard-global-review/kpi-laptop.png)
- [390px mobile-frame KPI preview](../scratch/dashboard-global-review/kpi-mobile.png)

## Manual checks

Refresh the dashboard, then compare expanded/collapsed sidebar widths and laptop/mobile window sizes. Confirm the grid uses four/two/one columns according to available content width, all eight cards align, values stay navy and prominent, and revenue remains on one line. Check neutral, positive, negative, empty, and attention descriptions against existing records. Open Custom Range and change periods/grouping; verify the surrounding dashboard and existing loading/Retry behavior still work.

## Remaining limitations

The screenshots are offline previews of the KPI region using isolated test records, not an authenticated full-page browser session. Remote webfont imports are omitted in offline previews, so the captures use system font fallback; the application retains its existing Montserrat loading. Native tooltip behavior and the full page with the live sidebar were not visually tested through the unavailable browser connector. The mobile capture uses a 390px content frame because Windows Chrome headless enforces a 500px minimum viewport.
