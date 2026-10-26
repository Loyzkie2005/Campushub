# Super Admin dashboard interactive design preview

## Scope and design decisions

### Latest layout correction

1. **Reason:** The user wanted the overviews below Attention Required, a shorter attention container, fully visible bundle recommendation types and complete system-status details.
2. **Files:** Updated `output/visualizations/campushub-admin-test-preview.html` at `.ch-attention-compact`, `ch-module-heading`, `ch-health-title` and `.ch-recommendations`; extended `scratch/dashboard-executive/verify_test_preview.js` and this guide. These anchors supersede the original ordering described below.
3. **Changes:** Attention Required is now a compact full-width strip before the overviews, with two columns on desktop and stacked accessible rows on mobile. The Marketplace/Facilities/Services trend appears underneath. Facilities and Services summary cards follow. System Status sits beside the trend on desktop and below it on mobile. Suggested Product Bundles, Frequently Bought Together and Cross-Sell Opportunities are three visible consecutive rows, without an accordion hiding the latter two.
4. **How it works:** Existing native buttons, `draw()`, sample toggle, chart animation and module switching are reused. `draw()` also updates `data-module-heading` to match the selected module. The status rows display the requested descriptions and fixed `Last checked: 11:29 AM` labels. The enclosing `Snapshot` label makes clear that this is not an actual check or a refresh timestamp. No new request function was added.
5. **Backend/API:** Still disconnected; no application templates, routes, database queries or status checks changed.
6. **Database:** No writes, migrations or sample imports.
7. **Checks:** Reran the isolated Chrome verification successfully, including new assertions that the desktop attention strip is at most 120px high and precedes the trend and Facilities summary; all three recommendation titles occur in order; three status timestamps and both requested descriptions exist; selected module headings update. Existing chart, dialog, refresh, reduced-motion, menu and five-width overflow checks still passed. The new desktop screenshot was inspected. Scoped whitespace check passed.
8. **Limits/practice:** This update affects the preview only. Its statuses and timestamps remain illustrative snapshots. Toggle samples, switch to Facilities, then return to Marketplace; verify the overview remains below the attention strip and recommendation rows stay visible. On mobile, verify the attention rows stack and System Status follows the trend. No live data needs to be edited to practice.

This is an isolated design experiment requested on October 20, 2026. It does not replace the existing Django dashboard. The supplied screenshot is the reference; no application data is inserted or seeded.

Brief: university administration; experienced staff; precise, calm presentation; restrained response motion; compact overview followed by a dominant trend and attention column, recommendations, domain summaries and activity. CampusHub navy, gold and white remain the palette. Poppins is used only inside this mockup. The existing web theme is not changed.

The canonical kit used is `.agents/vendor/ux-ui-agent-skills/.claude/skills/redesign/SKILL.md`, with its doctrine, vanilla adapter, review/a11y guidance and checking scripts. Its whole-kit example self-test is not a CampusHub quality score and was not run for this preview.

| Screenshot finding | Preview treatment |
| --- | --- |
| Repeated equal-weight cards make scanning slow | Four primary metrics in one surface; secondary totals in a quiet text row |
| Tall empty charts dominate the page | One compact shared trend with Marketplace, Facilities and Services controls |
| Empty breakdowns occupy permanent space | Secondary empty details expand on request |
| Urgent items and system health are separated by long sections | Attention and status sit beside the trend on desktop |
| Testing populated graphs could be confused with real metrics | Explicit sample toggle, repeated sample labels, unchanged snapshot KPIs and no network/data writes |

## Implementation report

1. **Cause / reason:** The user requested an interactive visual design with motion and graphs for testing, without adding database data.
2. **Exact files:** `output/visualizations/campushub-admin-test-preview.html:3` defines the scoped mockup tokens; line 36 (`ch-shell`) contains the dashboard; line 54 (`data-samples`) exposes sample mode; line 85 (`draw`) builds the chart; line 111 (`setModule`) selects a domain; line 118 (`const dialog`) defines local destination previews. `scratch/dashboard-executive/verify_test_preview.js:1` owns isolated checks and generates its browser-only wrapper/screenshots. This document records the scope and verification.
3. **Changes made:** Created a separate preview with a white sidebar, gold active navigation, compact metrics, navy segmented chart controls, recommendations, domain summaries, attention, system health, recent orders and activity. Buttons give subtle press feedback. Chart transitions are interruptible and run for 260ms after user actions, with no looping or initial entrance animation. Reduced-motion users receive immediate updates.
4. **How it works:** The script starts with `state = {module: 'marketplace', period: 30, samples: false}`. Snapshot values and names come from the supplied screenshot and are labeled as such; they are not live account or API results. `draw(animate)` takes the selected module, period and sample flag, calculates seven chart values and draws axes, a line and accessible point buttons. `setModule(module)` validates the domain through its existing button values, resets the old series when units change and redraws. `remember()` stores only preview selections with the conversation host when that optional API exists. It never writes browser storage or application records. Local sample arrays are for inspecting motion, point interaction and empty-state transitions only. Refresh simulates a brief disabled/loading state, then redraws the same preview. Dialogs explain that destinations are not connected; they send no messages or notifications.
5. **Backend / API behavior:** No Django, Flutter, route, controller, permission or business-logic change. The fragment contains no fetch/XHR/WebSocket calls. Google Fonts is the only declared static external resource. Icons use the conversation host's Lucide placeholders. No live API call, phone operation, app/server/worker start or restart.
6. **Database / migration impact:** None. No seed, fixture import, account edit or migration. Sample arrays are local script constants. Toggling samples changes chart visuals only, while KPI totals remain the screenshot snapshot.
7. **Tests performed:** Headless Chrome verified the zero default, sample on/off, three domains, both periods, focusable point details, ten destination dialogs, Escape dismissal, refresh loading, reduced-motion styling, mobile menu and layouts at 1280, 1024, 736, 390 and 320px. No horizontal document overflow or JavaScript exceptions occurred. Poppins and white panel styles were checked. Desktop/mobile screenshots were inspected, then icon-container and legend spacing were corrected and the checks rerun successfully. The installed kit's `contrast.py` measured navy on white at 16.24:1, muted text on white at 5.69:1 and navy on gold at 8.97:1, passing normal-text AA for those specific pairs. `lint_hardcodes.py` reported no hardcoded values in its one-file scan; this is the tool's reported scope, not proof that every geometric constant is a project token. No complete WCAG/axe or full kit gate pass is claimed. Scoped whitespace check passed.
8. **Remaining limitations:** This is a light-theme design preview with sample-only chart interactions, not a connected admin application. Placeholder destinations do not exercise real permissions, date APIs or live chart responses. The seven illustrative period points do not reproduce production date aggregation. System statuses are frozen screenshot values. The local screenshot wrapper lacks the host's Lucide renderer; icons are initialized by the conversation host in the delivered preview. Native app behavior and live server behavior remain untested because they were not changed.

## Small annotated example

```text
Sample charts OFF -> seven zero chart values -> honest screenshot empty message
Sample charts ON  -> local illustrative series -> visible sample labels
Facilities       -> request-count units       -> no currency-unit carryover
30 days / 7 days -> local test series changes  -> no API request
```

`draw()` outputs visual SVG and point controls. It does not output orders, payments, bookings or stored records. Keeping the experiment isolated lets the user approve its interaction before production implementation.

## Safe practice and troubleshooting

1. Open the conversation preview. Confirm the snapshot label and original zero revenue.
2. Enable **Sample charts**. Switch Marketplace, Facilities and Services, then 7/30 days. Hover, tap or use Tab to focus chart points. Check that the units and point details follow the domain.
3. Disable samples. Confirm the graph returns to zero and the KPI cards have not changed.
4. Open an attention item, press Escape and check that focus returns to its trigger. Resize the preview to inspect wrapping.
5. Enable the operating system's reduced-motion preference and repeat a chart change; the path should update without tweening.

For repeatable local checking, run `node scratch/dashboard-executive/verify_test_preview.js` from the project root. It uses an isolated headless Chrome profile and closes that browser when finished; it does not run CampusHub. If Chrome is absent, the check cannot run. If Poppins fails in the conversation host, confirm its static font resource is allowed; the QA wrapper uses CampusHub's bundled Poppins files. Do not point these sample arrays at a production API or import them into PostgreSQL.
