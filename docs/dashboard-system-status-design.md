# Recent System Activities and System Status

Current layout override, October 23, 2026: the final brief restores one compact health strip before Welcome and moves Attention below the full KPI/recommendation grid. See the [final dashboard implementation report](dashboard-analytics-operations-update.md). The activity-table typography/controls below remain in effect; older health-removal and left-column Attention notes are historical.

## Current: activity color hierarchy and alignment — October 23, 2026

This is a presentation refinement of the October 22 activity preview below. It does not replace that query, renderer, dialog, security or timestamp implementation.

### 1. Cause / reason and design references

The user's screenshot showed equally prominent navy text in every column and an Actions heading split into two lines. Inspection confirmed that the old last-column width was 56px; the global border-box rule and desktop 12px cell padding left only 32px for the label. Its inherited `overflow-wrap: anywhere` allowed the final letter to break off. This is a confirmed CSS sizing issue, not a missing stylesheet or backend failure.

The chosen direction is a calm university administration table: names and actions lead, time and module support them, and outcomes remain easy to recognize. Existing Inter, navy, white surfaces and the six-column information architecture remain. No illustrations, extra cards, gradients or entrance animations are useful for this audit task.

Internet references reviewed for this specific refinement:

- [IBM Carbon data-table guidance](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines): consistent table density/alignment and row hover feedback that helps follow related values.
- [Atlassian Lozenge guidance](https://atlassian.design/components/lozenge): compact labels with meaningful status semantics. CampusHub's previously authorized Success/Failed colors remain scoped exceptions; unrelated columns do not acquire colored badges.

The requested frontend-design, frontend-design-codex and UI/UX Pro Max skills were read. The local `table header label wraps` UX search returned applicable compact-label overflow and responsive-table guidance. The HTML/Tailwind stack search was used only for general label/alignment advice; CampusHub retains plain Django templates and CSS, without installing or adopting Tailwind.

### 2. Exact files changed

| File / current line | Anchor / change |
| --- | --- |
| `backend/static/components/css/admin_dashboard_operations.css:3` | `.executive-audit`: scoped semantic color/control tokens and the named inline-size container |
| Same CSS, line 23 | `.audit-table-scroll` / `.audit-preview-table`: neutral text hierarchy, header density, column widths, wrap rules and keyboard row feedback |
| Same CSS, line 46 | `.audit-icon-button`: preserved 44px control, quiet border, navy icon, gold-tinted press/hover feedback |
| Same CSS, line 91 | `@container activity-preview`: reveal User/Module only when the actual section is at least 680px wide; larger column gutters and stable result/action widths |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Existing CSS URL version changes to `20261023-audit-polish` |
| `docs/dashboard-system-status-design.md:3`, `CAMPUSHUB_CONTEXT.md:3` | Current implementation report and project context |

### 3. Changes made and applied UX principles

- **Visual hierarchy:** primary text `#17172A` for readable values, 600 weight for users, 500 for actions; secondary `#667085` for timestamps, modules, subtitle and header labels. Navy remains the control/link color.
- **Gestalt proximity/similarity:** consistent cell gutters and restrained row separators associate each audit record; hover and focus-within help trace the same row across columns. Rows remain non-clickable; only the eye performs the action.
- **Fitts's Law:** retain a 44px eye target and give its column explicit space. Actions is centered, nowrap, 64px on narrow layouts and 80px on wider layouts, with 6px side padding. The target does not shrink.
- **Hick's Law:** keep one existing row action. No extra menus, filters, edit or delete options were introduced.
- **Jakob's Law:** retain the familiar table, six desktop headings, tooltip, existing View All destination and details dialog.
- **Progressive disclosure / Miller's Law:** retain five real preview rows; extra information remains in details/full User Monitoring. At narrow section widths, Time/Action/Result/eye stay visible while User/Module remain available in details.
- **Visibility of outcome:** preserve text-labeled Success/Failed badges, including the prior explicit green/red semantic exception. Unknown results retain the existing Not recorded output rather than inventing a new status.

Header height is 48px and minimum body row height is 56px, with natural growth for wrapping content. That small difference preserves a 44px target plus vertical breathing room without an oversized header. No fixed table height or nested scrollbar is added. Gold appears only in the eye control's subtle hover/press feedback, with the existing navy focus outline retained.

### 4. How it works: inputs, outputs and data flow

No runtime function was added. Existing Django audit query → `format_activities()` → server HTML/JSON → existing `admin_dashboard_activities.js` renderer/dialog remains the complete data flow. Both initial and refreshed rows already use the same CSS classes, so one stylesheet refines both paths.

The `.executive-audit` wrapper defines semantic CSS custom properties. Descendants use `var(--audit-text)`, `var(--audit-muted)` and the existing brand/font foundations. These are local component tokens, avoiding a palette change on unrelated dashboard sections.

```css
/* Color assignment example: the timestamp supports the main action/name. */
.audit-preview-table td:first-child {
    color: var(--audit-muted);
    font-variant-numeric: tabular-nums;
}
```

The named CSS container checks available section width rather than the browser width. This accounts for an expanded sidebar or narrower dashboard pane: below 680px the established four priority columns remain; above it all six appear. Long values can wrap without changing stored text. Browsers without container-query support keep the usable four-column base and existing details access.

### 5. Backend / API behavior

Unchanged. No Python, audit logging, JavaScript, endpoint, query, permission, route, timestamp, record limit, authentication or details allowlist changed. System Health remains removed. Existing live data, loading/empty/error handling and read-only details continue to use their original code.

### 6. Database / migration impact

None. No schema, migration, live-data write, sample activity, environment, deployment, server process or Flutter change. Isolated test fixtures remain test-only.

### 7. Verification and learning exercise

- The existing `DashboardOperationsTests.test_final_layout_empty_populated_and_export` passed, rendering actual production templates for empty/populated isolated states. Django system check found no issues. Log: `scratch/dashboard-audit-polish-tests.log`.
- Existing `scratch/dashboard-activities-refinement/verify_activities.cjs`: **26/26 DOM/CSS checks passed**, including CSS parsing, fields, eye interactions, outcome labels, safe details, errors/empty recovery and dates. These are not pixel measurements.
- Scoped `git diff --check` passed, apart from the normal LF-to-CRLF notice.
- The versioned stylesheet returned HTTP 200 from localhost with content identical to the workspace.
- Contrast measured from actual CSS token pairs: primary text/white **17.61:1**; secondary text/white **4.97:1**; header or hovered-row secondary text **4.69:1**; navy eye/gold-tinted hover **15.22:1**; Success **6.81:1**; Failed **7.60:1**. These checks do not certify the entire UI for accessibility.
- Source-level review checked five visual concerns: text hierarchy, Actions padding/nowrap, consistent row spacing, container-based column priority, and control hover/focus treatment. The user screenshot supplied the before-state evidence. Browser inventory was empty and an attempt to open the local in-app browser reported unavailable. After-state screenshots, real responsive geometry and native-dialog behavior could not be verified.

Recheck the existing behavior from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_operations.DashboardOperationsTests.test_final_layout_empty_populated_and_export --keepdb --noinput
```

Safe practice exercise: open the existing local dashboard, press Ctrl+F5, inspect `.executive-audit` in DevTools and find `--audit-muted`. Trace its use on the timestamp and module. Temporarily change `--audit-hover` in DevTools to the existing `#F7F8FC`, hover an eye, then reload to discard the temporary change. Verify the eye opens existing details and the row itself does not become a misleading click target. Resize with the sidebar expanded/collapsed and confirm the column set follows the table's available space. This edits no saved data or source file.

Troubleshooting: if the old all-navy cells remain, inspect the loaded CSS URL for `v=20261023-audit-polish`. Do not change audit records or backend queries to fix presentation. Four columns on a constrained pane are intentional; User/Module are still in the details dialog. The semantic outcome colors are retained from the previous explicit request rather than applied throughout the product.

### 8. Remaining limitations

Browser access is unavailable, so the CSS implementation and automated DOM verification are complete but a live visual acceptance check remains outstanding. Container queries require a supporting browser for the six-column enhancement. Existing audit-source and period-filter limitations described below remain. Nothing was deployed or restarted.

## Current: compact Recent System Activities preview — October 22, 2026

This report supersedes older activity-table presentation notes below. Attention Required remains under the left System Overview; System Health remains removed. Other dashboard sections keep their existing layout.

### 1. Cause / reason

Inspection confirmed that the existing preview already uses the audit infrastructure, five newest records in the selected reporting period, six columns, protected read-only details and the requested empty state. The actual gaps were yearless timestamps for older records, text buttons repeated in each row, plain results, and mobile CSS hiding Result while retaining Module. A fixed 470px minimum table width also forced small-screen horizontal scrolling.

The refinement keeps one compact white table with a subtle border and 14px corners, Inter, an 18px section title, 13px rows, and a single eye control per row. Success/Failed colors are the user's explicit semantic exception to the normal navy/gold palette; visible outcome text accompanies them. No extra cards, animations, filters, logging models or charts were added.

### 2. Exact files changed

| File / current line | Nearby code anchor and purpose |
| --- | --- |
| `backend/core/modules/reports/dashboard_executive.py:86` | `current_year` / `activity_time_label`: preserve the year on records from a different local year |
| `backend/templates/dashboard/partials/system_activity_preview.html:1` | `get_current_timezone`, six table headings, `audit-result`, `audit-icon-button`: initial HTML, accessible eye icon, compact outcomes and mobile priorities |
| `backend/static/components/js/admin_dashboard_activities.js:6` | `Intl.DateTimeFormat` / `timeLabel`: application timezone, optional year in preview, mandatory year in details |
| Same JavaScript, line 37 / 44 / 86 | `badge.className`, eye SVG creation, details pairs: refreshed rows match server output and retain safe allowlisted details |
| `backend/static/components/css/admin_dashboard_operations.css:5` | Audit section typography, natural table height, mobile-first four-column presentation, labeled badges and 44px eye targets; desktop breakpoint at line 55 restores columns |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` / `621` | Existing CSS and JS URLs versioned `20261022-activities` to avoid stale cached assets |
| `backend/core/modules/reports/test_dashboard_operations.py:79` | `test_preview_dates_keep_other_year_and_use_application_timezone`: mixed-year HTML/API output, existing reporting timezone and compact markup |
| `docs/dashboard-system-status-design.md:3`, `CAMPUSHUB_CONTEXT.md:3` | This implementation/learning report and latest project note |

The isolated DOM verification harness is `scratch/dashboard-activities-refinement/verify_activities.cjs`; it is not application code or a data-seeding command.

### 3. Changes made

- Kept Time, User, Action, Module, Result, Actions on desktop, with the existing title, subtitle and User Monitoring destination. Added the requested small arrow to View All Activities.
- Current-year preview timestamps omit the year; older records retain it. Activity Details always includes the year.
- Replaced row text buttons with eye SVGs, a View Details tooltip, meaningful accessible labels, visible keyboard focus and a 44px target. Existing dialog Close control stays textual.
- Added compact Success/Failed badges. Null outcomes retain Not recorded; no unsupported Denied status was invented.
- On small screens, hide User and Module; retain Time, Action, Result and the details action. Removed fixed minimum table widths and internal table scrolling/height constraints. Long content wraps instead of being silently truncated.
- Preserved all loading/error/empty, permission, request-abort, dialog cleanup and focus-return behavior. The preview still has no Edit/Delete/Archive controls.

### 4. How it works: functions, inputs, outputs and data flow

`executive_overview(period, comparison, ...)` still queries `AccountActivity` within the selected period, ordered by `-created_at, -pk`, sliced to five. It passes those actual records through existing `format_activities(..., scoped=True, include_targets=False)`. Actor names, action/module labels and recorded outcomes continue to come from that formatter; no new event or inferred result is created.

The small `activity_time_label(value)` presentation function accepts an existing ISO timestamp, converts it to the current application timezone, compares its year with `timezone.localdate().year`, and returns the concise label. It does not compare the record's year with the reporting-period year, which could incorrectly omit a historical year.

```python
# Example only: when the current local year is 2026
# 2026-10-22T17:07:00+08:00 -> Oct 22, 5:07 PM
# 2025-12-30T16:20:00+08:00 -> Dec 30, 2025, 4:20 PM
```

The template emits the configured timezone as `data-time-zone`. In JavaScript, `timeLabel(value, full=false)` uses that timezone and compares calendar years in it, independent of the administrator's browser timezone. Its `full=true` output always contains the year. The existing reports pipeline explicitly uses Asia/Manila, matching this application's configured timezone; that reporting rule was not changed.

Initial HTML and refreshed rows share the same six-column shape and outcome classes. The refreshed renderer creates text nodes and fixed SVG elements; it never inserts arbitrary HTML. Selecting the eye still invokes `showDetails(button)` against the existing same-origin `activity_log_detail` API, with the existing tab authentication and eight-second timeout. The dialog displays only its established field allowlist. Arbitrary metadata, raw user agents, credentials and IDs remain excluded. Connection information is displayed only when the authorized API returns it.

### 5. Backend / API behavior

Only the dashboard's human-readable `time_label` presentation changes. Existing `admin_dashboard_api`, `admin_dashboard_page`, `admin_user_monitoring_page` and `activity_log_detail` routes, permissions, actor/target resolution, audit logging and API field allowlists remain. Details remain read-only and permission-checked server-side. Existing shared action/module vocabulary is reused. The full User Monitoring page is not recreated on the dashboard. System Health is not restored.

### 6. Database / migration impact

None. No models, migrations, logging hooks, application audit records, credentials, environments, deployment files, services or Flutter code changed. Tests write only to Django's isolated test database. No sample activities were added to the live dashboard.

### 7. Tests performed, debugging and safe practice

- **87 Django tests passed**: dashboard operations/executive summaries/periods, existing Activity API and User Monitoring. Includes five-row ordering, actual actor names, role gates, protected details, sensitive-field exclusion, mixed-year timestamps, initial HTML and unchanged audit counts. Log: `scratch/dashboard-activities-tests.log`. Django system check reported no issues.
- **26/26 DOM/CSS checks passed**: exact headings, mobile-priority classes, eye label/tooltip/SVG, existing View All destination, current/previous-year and local New Year boundary dates, configured timezone, full detail year, badges, same-origin token request, nested SVG click, focus return/cleanup, 403, text escaping, null/invalid/oversized rows, empty recovery and CSS parsing. Harness: `scratch/dashboard-activities-refinement/verify_activities.cjs`.
- JavaScript passed `node --check`; scoped `git diff --check` passed (with the existing LF-to-CRLF notice).
- Both versioned local static assets returned HTTP 200 and content matching the workspace.
- Measured badge text contrast: Success **6.81:1**, Failed **7.60:1**. These two checks do not constitute a complete accessibility audit.
- Browser inventory contained no connected browser. Actual responsive pixels, screenshots, hover rendering and native dialog keyboard/focus trapping remain unverified; jsdom's dialog methods are test stubs.

The first timezone assertion incorrectly expected a caller's UTC override to override the existing Manila reporting policy; inspection found the established `dashboard_periods` timezone decorator. The test was corrected to verify that policy without changing reporting. An initial DOM selector matched the sidebar User Monitoring link rather than the section's View All link; it was narrowed to the activity section and rerun. Both final suites passed.

From `backend/core`, repeat the relevant checks:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_operations modules.reports.test_dashboard_executive modules.reports.test_dashboard_periods accounts.test_activity_api accounts.test_monitoring --keepdb --noinput
```

Safe practice exercise: on the existing local dashboard, select a period with genuine audit records. Confirm at most five rows, select one eye, check that Date & Time includes its year, then close the dialog and confirm focus returns. Open View All Activities and verify it reaches User Monitoring. At a small viewport, Time/Action/Result/eye should remain readable while User/Module move into details. This exercise requires no account/product/booking edit and no sample audit records.

Troubleshooting: use Ctrl+F5 and confirm both asset URLs have `v=20261022-activities` if old text buttons remain. No records may be correct for the selected dates; widen the existing range or open User Monitoring rather than adding fake logs. Unknown actors/fields remain the existing Unknown/Not recorded when the audit source cannot safely identify them.

### 8. Remaining limitations

Only recorded Success/Failed outcomes currently exist; other outcomes need an actual audit source before being shown. The preview remains period-filtered rather than an all-time activity feed. Historical actor names/affected entities are limited to what the existing audit formatter can safely recover. No native-browser visual or physical-device claim is made. Nothing was deployed or restarted.

## Current: Attention Required below the left overview — October 22, 2026

### 1. Cause / reason

The user requested Attention Required directly below System Overview in the left column. It previously followed the entire two-column top area and therefore spanned the dashboard width.

### 2. Exact files changed

| File / current line | Anchor / change |
| --- | --- |
| `backend/templates/dashboard/partials/executive_dashboard.html:12` | Removed the separate attention include after the overview include |
| `backend/templates/dashboard/partials/system_overview_summary.html:120` | Includes `attention_required.html` inside `.dashboard-summary-left`, immediately after the KPI grid |
| `backend/core/modules/reports/test_dashboard_operations.py:89` | Existing layout-order assertion updated |
| `backend/core/modules/reports/test_dashboard_executive.py:159` | Existing section order/attention placement assertions updated |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:83` | Existing monitoring layout assertion now expects Attention before the right-side aside in document order |

This guide and `CAMPUSHUB_CONTEXT.md:3` record the placement. Older descriptions of full-width Attention Required below are historical.

### 3. Changes made

Moved the single existing attention include into the left column. The recommendation panel remains the right-hand sibling. Existing 16px top spacing from `admin_dashboard_executive.css:12` is reused; no new CSS or duplicate attention container was needed. System Health remains removed.

### 4. How it works

The existing dashboard view supplies the same `attention_required` context. `system_overview_summary.html` passes it unchanged to the existing partial inside `.dashboard-summary-left`, guarded by the existing global-dashboard condition. Its rows, links, loading/error and no-items states keep their original IDs/hooks, so the existing renderer continues updating them.

The input remains the existing actionable-item snapshot; output is the same HTML in a different parent. On desktop it occupies the left column below the eight KPI cards. When the grid stacks, the left-column content (KPIs then Attention) precedes the recommendation panel.

### 5. Backend / API behavior

No views, calculations, queries, routes, permissions, controllers or alert eligibility changed. Recommendation monitoring remains read-only. The System Health display/polling removal described in the next report remains in effect.

### 6. Database / migration impact

None. No application records, migrations, environment, deployment or mobile changes.

### 7. Verification and practice

Three focused existing Django tests passed: operations layout/export, executive layout/routes and read-only recommendation preview/permissions. Log: `scratch/dashboard-attention-left-tests.log`; test-time system check reported no issues. DOM inspection of both isolated empty and populated responses confirmed that Attention's parent is `.dashboard-summary-left`, its previous sibling is the KPI grid, the recommendations aside shares the outer grid, the attention ID appears once and System Health remains absent. No browser pixels were measured.

Refresh `http://127.0.0.1:8000/admin-dashboard/` and verify Attention is below the left KPI cards. If it still spans the full width, reload the HTML and inspect its parent; moving CSS alone cannot correct an include placed outside the left column.

Safe practice: trace the include at `system_overview_summary.html:120` into `attention_required.html` and locate the existing `dashboardAttentionItems` hook. Verify there is exactly one include in the rendered dashboard; do not duplicate it or create records to test its placement.

### 8. Remaining limitations

Actual desktop/mobile screenshots and responsive pixel geometry remain unverified. This is a template-placement update; no broader repository test-suite pass is claimed.

## Current: System Health removed from Super Admin — October 22, 2026

This supersedes all health-strip placement/styling notes below. Welcome is now the first visible section of the Super Admin dashboard.

### 1. Cause / reason

The user requested removal of the entire System Health display, including Database, Chat Service and Backup status text.

### 2. Exact files changed

| File / current line | Nearby anchor / change |
| --- | --- |
| `backend/templates/dashboard/partials/executive_dashboard.html:2` | Removed the top `system_status.html` include; `executive-toolbar` now appears first |
| `backend/core/modules/reports/test_dashboard_operations.py:89` | Section-order assertions and absence of `dashboardSystemStatus` |
| `backend/core/modules/reports/test_dashboard_executive.py:159` | Existing executive layout assertions updated |
| `backend/core/modules/reports/test_dashboard_kpi_cards.py:41` | Health component must be absent |
| `backend/core/modules/reports/test_dashboard_periods.py:398` | Removed health title expectation; line 526 verifies no status markup |
| `backend/core/modules/reports/test_dashboard_empty_states.py:85` | Removed expectation for a health empty state on this dashboard |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:282` | Existing recommendation section order no longer includes System Health |

This guide and `CAMPUSHUB_CONTEXT.md:3` record the current behavior. No new controller or test suite was added.

### 3. Changes made

Removed one template include from Super Admin only. The System Health title, all three service labels/statuses, dots, container and Check status button are no longer rendered. Welcome, filters, KPI cards, recommendation panel, Attention Required and module sections retain their existing layout.

### 4. How it works

Previously, `executive_dashboard.html` included `system_status.html` before `executive-toolbar`. Removing that include means the rendered dashboard has no `dashboardSystemStatus` element. The existing health script already checks for this element and returns immediately when it is absent; it makes no dashboard health-poll request in this state. Other dashboard JSON/refresh rendering continues through the existing controller.

The shared component, styles and underlying health implementation remain available to their other callers. No replacement hidden monitor was introduced. Consequently this removed component no longer dispatches fresh health-warning events into this page's Attention Required list; the existing server-provided attention items remain unchanged.

### 5. Backend / API behavior

No backend health-check functions, endpoints, views, permission rules, business queries or shared JavaScript changed. Existing health APIs remain available, while this page no longer starts the component's health-only request. Marketplace, booking, service and recommendation behavior is unchanged.

### 6. Database / migration impact

None. No application records, schema, migration, environment, deployment or mobile files changed. Existing Django test fixtures are isolated from application data.

### 7. Verification, troubleshooting and practice

The relevant existing Django tests were updated to expect no health markup and the revised section order. All 102 tests passed, including dashboard operations/layout, KPI/period data, empty states and recommendation access/rendering. Log: `scratch/dashboard-remove-health-tests.log`. Django's test-time system check also reported no issues. No new browser or DOM screenshot verification was performed.

Open `http://127.0.0.1:8000/admin-dashboard/`, refresh, and confirm Welcome appears first with no System Health strip or Check status button. If the strip remains, reload the HTML and confirm Django is using the edited executive template; CSS cache changes are unnecessary for an include removal.

Safe practice: inspect `executive_dashboard.html:2` and follow its `global_date_filter.html` include. Verify that the existing date form remains inside the Welcome toolbar and that no health component is included before it. This exercise needs no record creation or backend change.

### 8. Remaining limitations

Browser screenshot/pixel verification is not claimed. Earlier health-strip screenshots, DOM fixture checks and descriptions below are historical and intentionally no longer describe this Super Admin page. Live health-warning polling is absent from this page together with its removed UI; underlying health endpoints are retained.

## Current System Health container — October 22, 2026

This update replaces only the uncontained health-row styling in the top-layout report below. Its placement remains directly above Welcome on the Super Admin dashboard.

### 1. Cause / reason

The previous white health container stretched across the content area and had larger gaps. The user requested less spacing, a shorter container and all text on one line. The strip now fits its content above Welcome instead of stretching across the dashboard.

### 2. Exact files changed

| File / current line | Nearby anchor | Change |
| --- | --- | --- |
| `backend/static/components/css/admin_dashboard_operations.css:54` | `.dashboard-system-top` | Content-sized width, 100% maximum width, 40px minimum height, 4px/10px padding and 10px gaps |
| Same file, line 62 | `.dashboard-service-list` | Removes flexible expansion; retains a single scrollable status line with 8px service separators |
| Same file, line 63 | `.dashboard-service-list:focus-visible` | Existing keyboard focus retained |
| Same file, former `max-width: 899px` rule | Removed health wrapping override | Title, statuses and action stay on one line at every width |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | `20261022-health-compact` | Updates the stylesheet cache version |

Only the CSS and page cache version changed in this tightening step. The named focusable region in `system_status.html:9` remains unchanged. This guide and `CAMPUSHUB_CONTEXT.md:3` document the refinement. Existing `scratch/dashboard-top-review/verify_top.cjs` checks were updated for content-sized width, no wrapping and 40px minimum height; no new application test system was added.

### 3. Changes made

System Health is one content-sized container above Welcome, with Inter text, navy labels, existing actual-status dots, subtle gray dividers and the existing Check status action. The title, checks and action stay on one horizontal line. Narrow screens scroll the checks within the available space. Padding and separators are tighter; separate service cards, gradients and shadows remain absent.

### 4. How it works

The existing template still renders the same three `data-system-service` elements and named keyboard-focusable region. CSS `inline-flex` plus `width: fit-content` makes the container stop after its last control. `max-width: 100%` and border-box sizing keep it within its parent. `flex-wrap: nowrap` keeps all text on one line; the existing `overflow-x: auto` allows narrow screens to reach all three checks. The previous small-screen wrapping override was removed. The focused checks region retains its navy outline.

Data flow remains: existing health-only API response → existing `admin_system_status.js` validation/rendering → status text and dot keys in the same elements → container styling. Inputs are actual checked status values; output is the existing text/dot presentation. For example, a real `database.status='online'` with a valid check timestamp still becomes Connected; this CSS does not decide whether a database is reachable.

### 5. Backend / API behavior

Unchanged. Existing checks, unavailable/loading handling, time validation, Refresh/Check status listeners, permissions and Attention Required integration are reused. No new request, endpoint, controller or hardcoded healthy value was added.

### 6. Database / migration impact

None. No model, migration, application data, environment, deployment or mobile changes.

### 7. Verification and practice

For this CSS-only tightening, the existing top-layout DOM/CSS check passed 16 scenarios, including content-sized width, no wrapping, border, height, keyboard-region attributes and existing desktop/narrow layout declarations. The local server returned the changed CSS with HTTP 200 and exact workspace bytes. Django tests were not rerun for this styling-only change. The earlier 17 Django/29 DOM checks belong to the previous container update and remain historical verification, not new runs.

Open `http://127.0.0.1:8000/admin-dashboard/` and press Ctrl+F5. Confirm the shorter white strip above Welcome, one-line text, tight dividers and Check status. At a narrow width, focus the checks region and verify horizontal scrolling reaches Backup. Status words must follow actual check results.

Safe practice: change only `border-radius: 12px` in `.dashboard-system-top` to `10px`, reload and compare the corners, then restore 12px. Run `node scratch/dashboard-top-review/verify_top.cjs` after restoring. This changes the container shape without touching health logic.

If the wider container remains, verify the HTML references `20261022-health-compact` and reload the page. If text wraps, inspect the ID-qualified `flex-wrap: nowrap` rule and confirm the old 899px wrapping override is gone. Do not replace actual API data with static status labels to adjust layout.

### 8. Remaining limitations

Actual desktop/mobile screenshots, pixel geometry, native horizontal scrolling and keyboard behavior were not visually verified. The 16 DOM/CSS scenarios do not replace browser testing. Earlier screenshots and line maps below are historical for the health container; other dashboard behavior remains as described.

## Current top layout — October 22, 2026

This report supersedes the footer-status and full-width bundle placement described below. The empty-state behavior in [dashboard-empty-states.md](dashboard-empty-states.md) remains in effect, with a compact System Health presentation at the top. Older line numbers/layout notes below this report are historical.

### 1. Cause / reason

Inspection confirmed that System Status was the last section, Bundle Recommendations occupied its own full-width section below Marketplace, and Attention Required was nested inside the System Overview partial. That structure could not produce the requested combined 70/30 top area.

The latest layout is System Health, Welcome/controls, System Overview plus the permission-gated recommendation panel, Attention Required, Marketplace, Facilities, Services, and Recent System Activities. The global page header still contains the existing Dashboard title and action icons.

### 2. Exact files changed

Paths are relative to the project root. These are current line numbers and nearby code anchors for this update.

| File | Current line / nearby anchor |
| --- | --- |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 2 `system_status.html`; 4 `executive-welcome-copy`; 14 `attention_required.html` |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 2 `dashboard-top-layout`; 122 `executive-bundle-panel`; 126 `View Recommendations` |
| `backend/templates/dashboard/partials/system_status.html` | 1 `if top`; 7 `data-status-top`; 58 `System Status Unavailable`; 60 `Check system health` |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html` | 1 `bundle-summary-section`; 7 `forloop.counter <= 2` |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_activity.html` | 1 `bundle-summary-section` |
| `backend/static/components/css/admin_dashboard_operations.css` | 53 `Executive top`; 77 `dashboard-top-layout {`; 83 `executive-bundle-panel {`; 105 `min-width: 1200px`; 109 `min-width: 1800px`; 112 `max-width: 479px` |
| `backend/static/components/js/admin_system_status.js` | 38 `data-status-top` |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 27 `top-layout` |
| `backend/core/modules/reports/test_dashboard_operations.py` | 79 `test_final_layout` |
| `backend/core/modules/reports/test_dashboard_executive.py` | 153 `test_eight_sections` |
| `backend/core/modules/reports/test_dashboard_periods.py` | 398 `content.index('id="systemStatusTitle"` |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 57 `test_dashboard_top_panel` |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 282 section-order anchors; 311 single dashboard action / activity route remains available |

This guide owns the report; `CAMPUSHUB_CONTEXT.md:3` records the current layout, and `docs/dashboard-empty-states.md:5` links to this newer placement. DOM/CSS verification uses `scratch/dashboard-top-review/verify_top.cjs:1`, with existing audit/empty-state harness expectations updated for the new order and compact Connected label. Scratch HTML/JSON comes from the isolated test database, never from inserted development data.

### 3. Changes made

- Moved the single existing health component above Welcome. `top=True` selects a compact 44px minimum-height row with text and the existing semantic dots. Healthy Database reads Connected; healthy Backup reads Healthy. Loading and unavailable-check results remain distinct, with Check status and existing Refresh actions. Detailed messages/check timestamps remain in the component's existing DOM hooks, but their card-style display is hidden in this compact mode.
- Added “Here’s what’s happening across CampusHub today.” beneath the existing name greeting. The existing date-range form, Refresh, reporting dates and last-updated timestamp remain intact.
- Moved the existing bundle partials into a white, lightly bordered right-side panel within `dashboard-top-layout`. It has two groups only: Suggested Product Bundles and Recommendation Activity, with one primary View Recommendations action. Removed the old full-width bundle section and footer health include; each component appears once.
- Moved Attention Required outside System Overview so it follows the entire combined area. Its existing alert rows, health warning integration and empty/error states are retained.
- Added optional `compact=True` presentation to the existing bundle partials. The compact view hides large photos and redundant subsection actions/descriptions, shows up to two product-name links with seller/response text, and renders existing activity values as four quiet rows. Other callers retain the previous presentation.
- Preserved the existing eight KPI order: Users, Sellers, Products, Orders; Revenue, Facilities, Bookings, Pending Approvals. Desktop uses four columns/two rows with 28px values, 13px labels and 16px card padding. Currency wrapping and the free-sale zero explanation remain intact.

CSS is appended to the existing `admin_dashboard_operations.css`, rather than adding another stylesheet/controller. It reuses Inter, navy `#1A1851`, white, subtle borders, 14px panel corners, and the existing status dot colors. Gold `#FCB316` is only a small link underline accent. Health selectors include the component ID so older ID-based card styles cannot reintroduce icons, stacked headers or large spacing.

### 4. How it works: inputs, functions and data flow

The existing dashboard view still passes `show_bundle_suggestions`, `bundle_analysis`, canonical KPI values and selected-period data. `executive_dashboard.html` composes the sections in the new order. `system_overview_summary.html` takes the same context and places its original KPI grid beside an optional recommendations aside. Without permission/the aside, the existing fallback and new scoped grid expand System Overview to the full width.

`dashboard_bundle_suggestions(user, limit=2)` remains unchanged. For Super Admin it reads saved current live recommendations through `recommendations_for(user)` and `presentation(row)`, preserving eligibility/seller scope. It uses `activity_summary(user)` for actual sent, awaiting, created and dismissed values. GET rendering does not invoke Apriori or write recommendation records. Synthetic research data remains in its separate authorized view.

There is no reliable total-active-suggestions field in this bounded preview. Therefore the panel does not invent a primary total or label the preview length as the total number of active suggestions. Existing real activity counts remain visible when supported. Empty and error branches are reused, including the requested No Bundle Suggestions Yet and No Recommendation Activity Yet descriptions.

The `compact` input changes only HTML presentation. For example, including `bundle_suggestions.html` with `compact=True` uses a subsection heading, limits visible preview rows to two, and links the product names to the existing detail route. With `compact=False`/omitted, the normal card heading, photos and navigation remain.

`system_status.html` accepts `top=True` for its compact variant while retaining the same IDs, API URL and `data-system-*` hooks. Existing `admin_system_status.js` still validates allowed states and real check times, calls the same health-only API, dispatches the same attention event, and handles abort/retry. Its only new branch chooses the compact label for `data-status-top`; the backend status keys, validation, checking/unavailable behavior and other variants remain unchanged. A checked outage is never replaced with an invented healthy value.

### 5. Backend / API and permission behavior

No views, queries, model calculations, APIs, availability/payment workflows, Apriori thresholds or permission rules changed. Super Admin can monitor, follow the existing recommendation/detail/history pages, and inspect authorized research views. The compact dashboard has no Send to Seller, Create Bundle, approval or rejection forms. Existing direct endpoint permission tests still enforce this on the server; Marketplace Admin and Seller permissions remain unchanged.

Routes reused: `bundle_monitor_list` (`/admin-bundle-suggestions/`), each `bundle_monitor_detail`, and the existing `admin_dashboard_api?system_status_only=1`. The existing activity route still works; the compact dashboard now has one primary recommendations link instead of separate subsection navigation buttons. No duplicate mining service or data source was created.

The recommendation panel retains its existing page-load snapshot lifecycle. Date/grouping requests still refresh their existing sections, not the recommendation snapshot. Reload the page to refresh those saved previews.

### 6. Database / migration impact

None. No application data, schema, migration, environment, credentials, deployment, remote server or mobile files changed. ORM records created for verification are isolated Django TestCase fixtures and roll back; they are not loaded into the development database.

### 7. Responsive behavior, tests and troubleshooting

At 1200px viewport width and above, the top grid uses `minmax(0, 7fr) minmax(280px, 3fr)` and the KPI grid has four columns. Below 1200px the panel stacks below System Overview; KPI cards use two columns, then one below 480px. At 1800px and above the right panel is capped at 420px so it remains compact. Grid children can shrink, long text wraps, and the health row can wrap on smaller screens. No exact equal height is forced.

Verification results:

- 84 targeted Django tests passed for layout/order, dashboard periods/query bounds, domain separation, empty states, recommendation monitoring/eligibility, read-only GET behavior, permissions and links. Log: `scratch/dashboard-top-tests.log`.
- 80 broader Marketplace/KPI/health/recommendation regression tests passed. Log: `scratch/dashboard-top-regressions.log`. Together with the targeted suite, 164 Django tests passed; this is not the entire repository suite.
- 49 DOM/CSS scenarios passed: 16 top-layout, 13 audit/status and 20 empty-state scenarios. Log: `scratch/dashboard-top-dom.log`. These include empty/populated/no-panel output, section order, unique IDs, two-preview cap, real activity totals, no research metrics/actions, strong-selector overrides, request errors/recovery and health validation. CSS breakpoint branches were explicitly selected in jsdom; this is not a browser viewport geometry measurement.
- `manage.py check` passed; migration dry-run reported no changes; `node --check` passed for the changed health script.
- The changed stylesheet and health script returned HTTP 200 locally, with bytes matching the workspace. The template cache versions are `20261022-top-layout`.

To repeat the focused DOM/CSS check from the project root:

```powershell
node .\scratch\dashboard-top-review\verify_top.cjs
```

To repeat the new read-only/permission integration test from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_bundle_monitoring.BundleMonitoringTests.test_dashboard_top_panel_reuses_live_preview_and_is_readonly --keepdb --noinput
```

Manual check: hard-refresh the existing Super Admin dashboard. Confirm the health row is above the greeting, the two top areas share a row on desktop, Attention Required spans below them, and there is no second bundle section or footer health card. Test View Recommendations and product-name links, then resize to tablet/narrow widths. Do not create live records merely to fill empty cards.

Troubleshooting: if placement stays old, reload the HTML and confirm the `20261022-top-layout` CSS/JS URLs. If health icons or tall cards return, inspect the ID-qualified `.dashboard-system-top` rules; do not remove status validation. If no panel appears, check the existing `show_bundle_suggestions` permission result. If there are no suggestions, preserve the honest empty state; generation requires the existing eligible live transaction workflow. If the panel appears below Overview at a medium viewport width, that is the deliberate readability breakpoint, not a failed data request.

Safe practice exercise: in `admin_dashboard_operations.css`, find `.dashboard-top-layout` and change only its `gap: 24px` to `20px`. Reload desktop and narrow views, confirm that order/links/counts stay unchanged, then restore 24px and rerun the focused DOM check. This changes spacing only; no query, data or permission edit is needed.

### 8. Remaining limitations

No enabled browser surface was available, so screenshots, real responsive pixel geometry, text wrapping, native keyboard/screen-reader behavior and visual balance were not inspected in a browser. DOM/CSS checks verify structure and selected computed declarations, not actual rendering fidelity. Earlier footer screenshots below do not show this layout. No deployment or claim of full repository test coverage is made.

## Historical footer layout report

## Current implementation — October 22, 2026

This report supersedes the older status-card/header layout notes below for the Super Admin dashboard. Existing health checks, audit logging, User Monitoring and permissions are reused; their business rules are unchanged.

### 1. Cause / reason

The dashboard previously ended with a four-column Recent Activities table, while System Status appeared in the global header. Bundle Recommendations also appeared beside System Overview. The requested final order requires recommendations after Marketplace, followed by Facilities, Services, a compact activity preview, and a final status section.

Inspection confirmed that the existing audit formatter already supplies readable actors, actions, modules and recorded results. The existing Activity API provides authorized details with explicit field allowlists. The existing health implementation can meaningfully check Database, Chat Service and Backup; there are no equivalent checks that justify declaring Marketplace, Facilities, Services or Notifications operational merely because the page rendered.

### 2. Exact files changed, current lines and nearby anchors

Paths are relative to the project root. Line numbers identify current code anchors.

| File | Line / anchor | Change / reason |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_executive.py` | 84 selected audit query; 85 `activities` | Adds readable `time_label`, recorded `result` and existing detail URL to the same five-row safe preview. No new query or audit record creation. |
| `backend/templates/dashboard/partials/system_overview_summary.html` | 1 `dashboard-summary-layout` | Removes the recommendations aside from this include; KPI values and Attention Required remain. The existing no-aside CSS makes the overview span the content width. |
| `backend/templates/dashboard/partials/executive_dashboard.html` | 24 `executive-bundles`; 36 activity include; 37 final status | Moves the existing permission-gated bundle cards below Marketplace, adds the activity include and ends with System Status. |
| `backend/templates/dashboard/partials/system_activity_preview.html` | 1 `data-system-activities`; 17 dialog nearby | New six-column preview, honest empty/error states, existing monitoring link, and read-only native detail dialog. Controls are shown only with the existing monitoring permission. |
| `backend/templates/dashboard/partials/system_status.html` | 4 footer heading/action; 7 `data-status-footer` | Adds compact-footer presentation mode and Check status action while retaining existing service-row hooks and legacy modes. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 27 operations CSS; 41 header; 620 scripts | Stops passing inline status into the dashboard header; loads new scoped CSS/activity script and versions changed assets with `20261022-audit`. |
| `backend/static/components/css/admin_dashboard_operations.css` | 1 operations scope; 17 dialog nearby; 30 status nearby | Compact Inter table, detail dialog, two bundle columns on desktop, final status rows, mobile priority columns and contained scrolling. Semantic health dots are localized here. |
| `backend/static/components/js/admin_dashboard_activities.js` | 15 `detailURL`; 22 `render`; 50 `showDetails` | One activity-preview renderer, on-demand GET to the existing detail API, explicit field rendering, error states, abort handling, and focus return after close. |
| `backend/static/components/js/admin_dashboard_executive.js` | 12 `fail`; 16 `render` | Removes the old activity renderer so only one component owns the activity table. Keeps current facility attention and Analytics links. |
| `backend/static/components/js/admin_system_status.js` | 30 timestamp; 57 retry control; 85 listener | Shows full local check time in footer mode; Check status reuses the existing health request. Legacy display modes keep their compact-time behavior. |
| `backend/core/modules/reports/test_dashboard_operations.py` | 46 preview; 62 detail API; 79 layout | New tests for five newest rows, safe preview/details, real existing API permissions/read-only behavior, final order, empty states and optional isolated fixtures. |
| `backend/core/modules/reports/test_dashboard_executive.py` | 159 final section anchors | Updates section order and asserts footer status appears once, without header status. |
| `backend/core/modules/reports/test_dashboard_periods.py` | 398 status order; 403 activity heading | Updates the existing shared dashboard layout expectations. Counting/filter assertions remain. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 282 section order; 295 heading | Updates the moved recommendation section's order and title case; keeps its existing data, permission and no-render-time-mining checks. |
| `docs/dashboard-system-status-design.md` | 3 current report | This current implementation/data-flow/debugging/verification guide. Earlier material below is historical. |
| `docs/dashboard-services-overview.md` | current file map | Refreshes shared helper/renderer anchors after this update; Services logic is unchanged. |
| `docs/booking-overview-implementation.md` | current file map | Refreshes shared renderer/asset anchors; Facilities behavior is unchanged. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest operations note | Preserves the accepted order, reuse, privacy boundaries and verification limits. |
| `scratch/dashboard-operations-review/verify_operations.cjs` | 1 | Local integration harness using isolated Django response fixtures and the existing scratch jsdom dependency; not application code or a data seeder. |

### 3. Changes made / table, details and layout

The permission-appropriate dashboard order is now:

1. System Overview
2. Attention Required
3. Marketplace Overview
4. Bundle Recommendations & Activity
5. Facilities Overview
6. Services Overview
7. Recent System Activities
8. System Status

The bundle section still respects its existing visibility permission. Its two existing cards are reused, without recalculating Apriori during rendering or inserting records.

**Recent System Activities** has the requested subtitle and existing View All Activities destination. It shows Time, User, Action, Module, Result and Actions. There are at most five actual audit rows, newest first. Time is readable local time even in the initial server HTML; raw ISO values are retained only in the semantic `datetime` attribute. Actor names come from the established formatter, not an internal user ID or the affected person's identity. The only row control is View Details; there are no Edit/Delete controls.

The detail dialog displays Date & Time, Performed By, Role, the recorded affected entity when available, Action, Module, Result and authorized stored connection information. Missing information is labeled Not recorded rather than guessed. It has loading, permission/expired-login/not-found/timeout/error states. Native dialog behavior supplies modal interaction; closing aborts an outstanding request, clears details, and returns focus to the opener or section heading.

**System Status** is a small final section with its subtitle, Check status button and three existing checked systems. It uses existing terms such as Online, Healthy, Degraded, Warning, Failed, Unavailable and Unknown. Text accompanies every dot. Green/amber/red dots are the explicit requested exception to the ordinary navy/gold/white palette; other interface text remains navy/neutral. No charts, fake health rows or analytics follow this section.

The preview uses a white surface, subtle border, 14px corners, Inter, 13px table text and 14px action controls. On narrow screens User and Result are hidden as lower-priority columns; Time, Action, Module and View Details remain. The table scrolls inside its own region rather than widening the page. Status rows stack their check times on small screens. Bundle cards stack below 1000px. These are implemented CSS behaviors; actual viewport rendering remains unverified.

### 4. How it works / existing models and helpers reused

**Audit preview:** `executive_overview(period, comparison)` still reads `AccountActivity` by `created_at` within the selected reporting period, ordered by `-created_at, -pk`, limited to five. It calls the existing `format_activities(..., scoped=True, include_targets=False)`. This avoids connection data and target lookups in the summary. The presentation mapper emits only time, time label, actor name, action, module, result and a detail URL.

```python
'result': row['result'],  # Existing recorded Success/Failed label; no invented result.
'details_url': reverse('activity_log_detail', kwargs={'pk': row['id']}),
# The ID addresses the existing audit API; it is not displayed as the user's identity.
```

`render(rows)` consumes the same preview shape initially and after the existing dashboard refresh event. It accepts at most five rows, formats local time, creates text nodes, and distinguishes no records from request failure. Current generic audit results are Success and Failed; unknown/unrecorded results remain Not recorded. Module/action naming is whatever the existing formatter supports; the dashboard introduces no new event types or status enums.

**Details:** `showDetails(button)` calls the existing `/api/activity-logs/<pk>/` GET endpoint. `ActivityDetailView`, `CanReadActivity`, `support_activity()` and `ActivityDetailSerializer` remain unchanged. The API enforces the existing role, scope and `can_view_user_monitoring` permission before formatting details. It reuses batched actor/target lookups and `parse_connection()` for short Device/Browser labels.

The dashboard adds the existing tab token only to that same-origin request, uses `credentials: same-origin` and `cache: no-store`, and never copies the URL/token into visible fields. It renders an explicit list of known output fields using `textContent`; it never prints raw metadata, user agents, session identifiers, passwords/hashes, recovery/verification codes, keys or arbitrary API error bodies. IP/device/browser appear only in the authorized detail dialog. Extra response properties are ignored.

**Health:** the existing `admin_dashboard_api?system_status_only=1` path calls `build_system_status()` independently of analytics. `database_status()` performs the existing `SELECT 1`; `chat_service_status()` checks only the configured server-side `/health` origin with its existing timeout/body validation; `backup_status()` uses existing backup-file metadata, schedule configuration and recorded attempts. Backup Healthy is the existing metadata-based assessment, not proof of a restore test.

`admin_system_status.js` still starts an actual check on page load and Dashboard Refresh/Retry. The new Check status button calls that same function. Each displayed time is the respective helper's returned `checked_at`, formatted locally. Pending/unreachable/malformed responses show existing Unknown/unverified state and remove check times; no clock or continuously refreshed timestamp is fabricated.

### 5. Backend / API behavior and routes

- Existing `admin_dashboard_api`: same authentication, dates, counts, permissions and health-only branch. The five preview rows gain only `time_label`, `result` and `details_url`.
- Existing `admin_user_monitoring_page`: View All Activities. No duplicate management page, session analytics, login graph or online-user table was added.
- Existing `activity_log_detail`: on-demand read-only details; anonymous and unauthorized requests retain their original failures, and POST remains unsupported.
- Existing bundle partials and visibility rules: moved, not rebuilt.

No audit logging, User Monitoring templates/controllers, serializers, authentication, health algorithms, module workflows or permission grants changed. Preview dates keep their existing selected-reporting-period behavior; this is not an all-time audit search. Affected booking/order references can be shown by the existing formatter, but internal user/entity IDs are not added to the visible dashboard.

### 6. Database / migration impact

No models or migrations changed. No application audit rows, settings, credentials, data, backup files or subsystem states were written to populate the UI. Tests create audit records only inside Django's isolated test database; health scenarios use the existing temporary-file/network test mechanisms. Optional HTML/JSON in `scratch/dashboard-operations-review/` is isolated verification output.

No `.env`, Nginx, deployment, server services, SSH tunnel or Flutter files changed. This is a local web update; there is no APK or deployment step.

### 7. Tests performed / debugging / practice

- **234 Django tests passed**: new dashboard operations, executive summaries, periods/query bounds, health, Services, Marketplace/KPIs, physical booking/ranking/upcoming summaries, existing activity API, User Monitoring, bundle suggestions and bundle monitoring. See `scratch/dashboard-operations-tests-final.log`.
- **13/13 DOM integration scenarios passed**: bounded/readable table, final order, authorized detail fields/token, clearing/focus return, denied details, text/field allowlisting, returned check timestamps, failed backup state, missing health/removed timestamps, independent health during dashboard failure, empty recovery, repeated refresh and initial empty preview. See `scratch/dashboard-operations-dom-final.log`.
- `manage.py check`: no issues. `makemigrations --check --dry-run`: no changes detected. Three changed/new production JavaScript files passed `node --check`; scoped whitespace checks passed.
- Four versioned local static assets returned **HTTP 200 and bytes matching the workspace**: operations CSS, activity renderer, executive renderer and system-status renderer.
- Browser inventory returned no connected browser. jsdom needs a test-only dialog stub, so native dialog rendering, Escape/focus trapping, responsive pixels and measured contrast are not verified. No screenshot or WCAG claim is made.

From `backend/core`, repeat the primary audit/health checks safely:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_operations modules.reports.test_dashboard_executive modules.reports.test_dashboard_periods modules.reports.test_dashboard_health accounts.test_activity_api accounts.test_monitoring modules.marketplace.test_bundle_suggestions --keepdb --noinput
.\venv\Scripts\python.exe manage.py check
```

For DOM fixtures, set both `OPERATIONS_REVIEW_DIR` and `DASHBOARD_REVIEW_DIR` to the absolute `scratch/dashboard-operations-review` directory, then run the new operations tests and existing health tests. Run `node scratch/dashboard-operations-review/verify_operations.cjs` from the project root afterward. The harness reuses `scratch/bundle-qa/node_modules/jsdom`; it is not installed as an application dependency.

Troubleshooting: press Ctrl+F5 if the header still contains statuses or recommendations remain beside KPIs. Check asset URLs for `v=20261022-audit`. A blocked detail request must show the permission/expired-login message, not another user's data. A failed health request must remove unverified timestamps, not retain a seemingly fresh successful state. Empty activity data can be correct for the selected dates. Missing Marketplace/Facilities/Services/Notifications status rows are intentional because this update has no meaningful checks for them.

Safe practice: in DevTools, temporarily hide `.audit-secondary` at desktop width and compare the four critical columns with the full table, then restore it. Use View Details on a permitted existing record and close it; verify the opener regains focus. Click Check status and confirm the actual returned `checked_at` supplies the displayed time. These actions require no product/booking/account edits and create no sample logs.

### 8. Remaining limitations

Health reports only the three systems with existing checks; it is not comprehensive monitoring or proof that every module workflow is operational. Backup status remains metadata-based. Initial page loading still depends on the existing application/database path; the independent health endpoint cannot make an unavailable page render by itself. Activities remain limited to five records in the selected period; full audit analysis belongs to User Monitoring. Visual/native-dialog verification remains outstanding because no browser was available. Nothing was deployed.

---

## Historical System Status design refinement

## Cause / reason

The previous layout used small supporting text, placed status beneath each name, and left the check times and Backup action at different vertical positions. The new layout makes service health easier to scan while retaining the existing institutional dashboard styling.

## Exact files changed

| File | Approximate line / anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/system_status.html` | 7 `dashboard-service-header`; footer blocks | Group icon, name and status in a header; separate supporting details and footer. |
| `backend/static/components/css/admin_system_status.css` | 1 `#dashboardSystemStatus`; 5 header; 10 footer | Consistent icon wells, typography, spacing, footer alignment and outlined Backup action. |
| `backend/static/components/js/admin_system_status.js` | 10 `checkedTime`; 27 checked-time rendering; 40 last-backup visibility | Compact visible check time with complete date/time in tooltip and accessible label; hide unverified backup date. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 17 / 589 system CSS/JS includes | Bump asset versions to `20261004-system-design`. |
| `scratch/dashboard-global-review/prepare-system-visual.cjs` and `verify-system-visual.cjs` | Review generation / layout assertions | Review the updated markup, typography and real current backup warning. |
| `docs/dashboard-system-status-design.md` | This report | Changes and verification. |

## Changes made / how it works

- A 32px neutral icon well contains each 20px navy SVG.
- Service names use 14px semibold text; 12px semibold status text aligns at the right of the same header.
- Descriptions use 12px regular text. Backup's actual date is navy and easier to distinguish from explanatory text.
- Check times align in service footers. Visible text shows the actual time, such as “Last checked: 5:20 PM”; the complete original timestamp remains in `datetime`, tooltip and accessible label.
- Open Backup is a compact 32px outlined link with a focus outline and restrained gold hover border.
- Three equal columns share one white bordered surface. Below 760px of available container width, services stack with horizontal separators. Footer controls can wrap at tighter widths.
- Missing backup timestamps stay hidden instead of adding another unverified-date line. Unknown/error messages remain visible.

## Backend / API behavior

Existing live health checks, service classifications, endpoint, authentication, refresh, timeouts, stale-response protection and backup route continue to work. This refinement changes presentation and timestamp formatting only. It adds no service requests or polling.

## Database / migration impact

None. No model, query, migration, backup operation or saved setting changed.

## Tests performed

- Existing Django dashboard-render test passed with isolated records and the new markup.
- `check-system-status.cjs` passed live-state rendering, safe timestamps, healthy/warning/failed/unknown states, global Refresh/Retry, authentication, independent failures, races and timeout.
- `check-controls.cjs` passed existing KPI/date/refresh/chart behavior.
- JavaScript syntax and CSS parsing passed. Scoped `git diff --check` passed.
- Inspected offline Chrome screenshots together: desktop, narrow layout with the current real backup warning, and failed-service fixtures. No horizontal overflow; headers, messages, footers and action remained readable.
- Browser measurements: desktop 1536px and 960px section widths use three columns; a 342px section inside a 390px frame uses one column. Desktop section height is 156px for the reviewed healthy/warning states, compared with approximately 174px previously.
- The design detector used its limited regex fallback; actual browser/DOM checks supplement it.

## Remaining limitations

The functional health-source limitations from [Improvement #5](dashboard-system-status-5.md) still apply. The visible check time is compact; the full date is available by hovering or through assistive technology. Offline browser review used project CSS/JS and actual sanitized service data or isolated fixtures, with fallback fonts. It does not replace an authenticated interactive or physical mobile-device check.

## Manual check

Reload the dashboard. Verify service names and statuses share a header, descriptions remain readable, footers align and Open Backup leads to the existing module. Hover over Last checked to see the complete date/time. Click global Refresh to verify Unknown/checking changes back to real results. Resize the window to confirm vertical stacking and wrapping without clipping.

Screenshots: `scratch/dashboard-global-review/system-current.png`, `system-mobile.png`, and `system-failed.png`.
