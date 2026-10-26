# Suggested Product Bundles - monitoring and research

## Current: source-separated Bundle Recommendations tabs, October 26, 2026

### 1. Cause / reason
The user approved the minimal two-tab UI after inspection identified a data-access blocker. The existing synthetic helper uses process-local `lru_cache`, which executes Apriori when a key is missing. It is not a durable, safely scoped saved snapshot, and it has no read-only lookup contract. Marketplace Admin has no authorized synthetic execution path. Therefore, this approved iteration separates sources without pretending cached or newly calculated research output is safely saved evidence.

### 2. Exact files changed
Paths and current code anchors for this iteration:

| File | Current lines / anchor | Beginner-friendly explanation |
| --- | --- | --- |
| `backend/core/modules/marketplace/bundle_monitoring_views.py` | 72 `suggestion_list`; 75-87 source selection; 156 live context | Adds a presentation-only `view` selector after the existing permission check. Dataset requests return before live queries or analysis helpers. Live requests keep the existing scoped query and workflows. |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` | 10 stylesheet version; 33-40 source navigation; 72 hidden live selector; 89 source branch close | Adds both exact tab names and subtitles, keeps live content inside its own branch, and preserves the existing Dataset & Analysis link at line 21. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_dataset_recommendations.html` | 1 subtitle; 3 source label; 5-10 metrics; 11 unavailable explanation; 12-14 table | New presentation-only partial with four explicitly unavailable metrics and the requested six-column table structure. No invented rows, disabled fake detail links or seller actions. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css` | 497 source navigation comment; 498-511 local selectors | Reuses existing navy/white controls, focus treatment, source label, metric cards and scrolling tables. Stacks source links and metrics on narrow screens. Dataset values sit beneath labels to avoid broken words. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 52 no-execution regression; 79 live navigation regression; 95 permission regression; 106 optional browser export | Tests both authorized roles, unchanged cache and recommendation/audit counts, preserved live counts/search state, forbidden access and disposable browser fixtures. |
| `docs/suggested-product-bundles.md` | This section, `Current: source-separated Bundle Recommendations tabs` | Records implementation, data flow, verification and limitations without overwriting previous feature history. |

Local verification artifacts are under `scratch/bundle-source-tabs-20261026/`, including `verify.cjs`, four disposable HTML fixtures, screenshots and `browser-results.json`. The real HTTP acceptance runner is `run-http.py:1-8`, which loads `source_http_acceptance.py:14-39`. Its test uses existing isolated-server setup/teardown, creates disposable authorized users and a saved record, passes the server origin/record key to `http-browser.cjs:1-77`, and verifies persisted counts afterward. The browser driver accepts those environment inputs, authenticates via the real API, drives normal links/forms/drawer requests, and writes `http-browser-results.json` plus screenshots/logs. It never substitutes application response bodies. Reusing the existing server test base avoids new application dependencies and unsafe working-database fixture setup. These fixtures use test-only products and are never marketplace evidence.

### 3. Changes made
The existing module now has **Dataset-Based Recommendations** followed by **Live Recommendations**. Exact requested subtitles appear within the selected source. Existing links without a source selector default to Live Recommendations so bookmarks, live filters and detail return links preserve their previous behavior. The dataset view displays a small **Synthetic Dataset** label, all four requested metric names, and the six requested table headers. Values say **Not available**, not zero. There are no result records to open, so View Details is explained rather than attached to an invented record.

Live keeps Total Suggestions, Sent to Sellers, Suggestions with Bundles Created and Awaiting Seller Response, plus the saved table, role-specific existing analysis sections, filters, pagination, details and seller workflow. No imported dataset transactions are attached to real products or sellers.

### 4. How it works: functions, inputs, outputs and data flow
`GET /admin-bundle-suggestions/` -> `suggestion_list(request)` -> existing `can_view_bundle_suggestions(user)` -> source selection -> `page(request)` -> existing page template -> source-specific content.

- **Input:** authenticated user plus optional `view`, existing live filters and `page`. Only the exact value `view=dataset` selects dataset presentation. Missing, `live` or unknown values use the live branch.
- **Dataset output:** the source-navigation context and unavailable-state partial only. No `build_bundle_suggestions`, `_cached_synthetic`, CSV loader, live recommendation query or snapshot-writing function is called by this branch.
- **Live output:** the unchanged `annotated(user)`/`status_records_for(user)` scoped records, existing KPI calculations, paginator and presentation. The source context is added to that output, not substituted for it.
- **Navigation:** source links copy current query parameters, replace `view` and remove `page`, preserving applied live filter inputs for a round trip while preventing stale pagination. The live filter form includes `view=live`. Existing Reset still returns to the default live view. Parameters are URL-encoded and Django escapes rendered attributes.
- **Accessibility:** ordinary server-rendered navigation links have `aria-current="page"`, not incomplete JavaScript tab roles. Keyboard focus remains visible, links have at least 40px height, and tables retain labelled focusable local scrolling regions.

Annotated example: `/admin-bundle-suggestions/?view=dataset&q=Coffee` selects the dataset unavailable state. `q=Coffee` is retained in the Live Recommendations link but is not used to query research or live records while the dataset branch renders. Changing `run=1` in this URL cannot execute analysis. The explicit existing research route has its own unchanged role-specific behavior.

This approach was chosen instead of calling the current cache because a cache miss would silently execute analysis during ordinary navigation, and there is no reliable mapping from synthetic seller/product identifiers to live Program/Major authorization. A new snapshot reader is not implied by these template fields.

### 5. Backend / API behavior
No new route, REST API, execution permission or management action. The existing list GET checks authorization before either source branch. Super Admin does not gain highlight/manage actions. Marketplace Admin retains scoped live management and is not allowed to execute synthetic analysis through either the new tab or existing run endpoint. Both-product live scope, existing detail authorization, history, drawer behavior and saved-record semantics are unchanged. Private/no-store caching remains. The existing View Dataset & Analysis link, research GET, explicit run POST and Dataset & Analysis routes remain intact, including existing Super Admin research calculation behavior. The no-execution promise applies to this recommendation list and its source tabs, not an unrelated rewrite of the existing research route.

### 6. Database / migration impact
None. No models, migrations, snapshot storage, imported datasets, Apriori formulas/thresholds, checkout records, saved recommendations or seller responses were changed. No working-database analysis or fixture insertion was performed. Tests create and destroy Django's disposable test database. No automatic seller notification, publication, analysis or persistence is introduced.

### 7. Tests performed
- Initial full bundle regression run: **114 tests passed in 34.449 seconds**, with no Django system-check issues.
- Final full bundle regression run after adding the optional fixture exporter: **115 tests passed in 37.827 seconds**, with no Django system-check issues. Suites: `modules.marketplace.test_bundle_monitoring` and `modules.marketplace.test_bundle_suggestions`.
- Source-specific tests patch the analysis builder, synthetic miner, calculate-on-miss cache and live-list accessor to raise if invoked for dataset navigation. Both authorized roles still render successfully, keep the cache unchanged, and preserve recommendation/audit counts. Existing regressions cover live scope, role restrictions, details, highlighting and research behavior.
- Chromium fixture verification renders both source views for both roles at 320, 390, 768, 1024, 1280, 1440 and 1920px. Initial 324 assertions passed. Visual inspection identified an awkward split of the words Not available on narrow metric cards, so the dataset-only values were moved beneath their labels and a no-broken-word browser assertion was added. Final **338 assertions passed across 28 renders**, with no page overflow, JavaScript errors or missing assets. Results are recorded in `scratch/bundle-source-tabs-20261026/browser-results.json`.
- **Real authenticated HTTP acceptance subsequently passed:** one `StaticLiveServerTestCase` in **87.318 seconds**, **237 browser assertions across 72 real navigations** at all seven widths. Actual `/api/admin_login/` issued per-tab tokens for Super Admin, Marketplace Admin and a different-program admin. Real browser clicks applied a product filter, switched to Dataset-Based Recommendations, returned with Enter through Live Recommendations, retained the filter and saved record, opened the actual authorized drawer, and restored focus on Escape. Dataset HTTP responses showed four explicit unavailable values, no execution/management forms and the six requested columns. The scoped outsider saw zero live records and received HTTP 404 for the foreign detail. Existing mutation URLs returned HTTP 403. No application HTML, API or application static response was mocked. Only third-party Bootstrap assets were served from an existing local cache. There were no JavaScript errors, missing application assets or page overflow. Products, saved recommendations and Marketplace audit counts were unchanged, `sent_at` remained empty, and no analysis-completion event was created. Mining was instrumented to raise if triggered, not replaced with fake results. Disposable ORM records were used only in Django's isolated PostgreSQL test database, never as working marketplace evidence.
- **Observed improvement:** source changes now actually navigate to distinct server responses instead of mixing synthetic and live content. Both roles can distinguish the unavailable research source from the retained live record, return without losing their applied search, and still inspect authorized seller evidence. This closes acceptance for the approved minimal UI, not the original populated-dataset objective. Safely saved synthetic results remain a separate blocker.
- Browser fixtures use actual Django-rendered test responses and local assets, with zero working-database browser requests. They check source selection, labels, keyboard focus, target heights, retained four live KPIs, live details links, six-column tables, unavailable metrics, page overflow, missing assets and JavaScript errors. This is not signed-in working-server end-to-end acceptance and not a full WCAG audit.

Reproduce from the repository root using Windows cmd.exe:

```text
set BUNDLE_SOURCE_PREVIEW_DIR=scratch\bundle-source-tabs-20261026\rendered
backend\core\venv\Scripts\python.exe -B scratch\synthetic-notice-20261026\run-tests.py modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions
node scratch\bundle-source-tabs-20261026\verify.cjs
backend\core\venv\Scripts\python.exe -B scratch\bundle-source-tabs-20261026\run-http.py
```

### 8. Remaining limitations, troubleshooting and safe practice
**Dataset result population is intentionally not implemented in this minimal approval.** There is no safely authorized saved synthetic snapshot, so actual metric values, result rows and functioning dataset View Details cannot be displayed without separately designed persistence/retrieval and dataset visibility scope. This does not claim that the source CSV has no qualifying associations. Do not reuse real `BundleRecommendation` rows as synthetic records, infer supporting counts from rounded percentages, or invoke the current calculate-on-miss cache to fill this empty state. Future work must distinguish directional rule count from deduplicated combination count and retain the original exact supporting-transaction count.

If an old layout remains, reload the page to fetch stylesheet version `20261026-source-tabs`. If access is denied, inspect existing analytics permission and role boundaries, not the tab label. Unknown `view` values deliberately fall back to Live Recommendations. Research-only results remain on the existing authorized Dataset & Analysis route. Source switching drops pagination while retaining filter inputs. No live filter is applied to synthetic data.

Safe learning exercise: sign in with an already authorized account, open the existing list, note its live KPI values, apply an ordinary product search, then choose Dataset-Based Recommendations. Verify all four metrics say Not available and no Run/Send/Highlight control exists. Return through Live Recommendations and confirm the search is retained. At 390px, use Tab to focus each source link and the scrolling table. Do not create transactions or run analysis for this exercise. In code, trace `view=dataset` from `suggestion_list` to the new partial and identify the early return that prevents the live query path.

A pre-existing `.git/index.lock` dated October 9, 2026 and extensive overlapping dirty/untracked user work prevent a safe scoped commit. The lock and unrelated work were left untouched. No broad staging or commit was attempted.

## Current: remove visible Dataset Details, October 26, 2026

### 1. Cause / reason
The user approved removing the optional Dataset Details disclosure and its File/Data Source presentation, not the CSV, metadata or dataset KPIs. The active disclosure was between the three cards and tabs. Removing it makes the primary views immediately follow their statistics.

### 2. Exact files changed
- `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html:10,89-94`: cache version `20261026-no-dataset-details`; remove the single details/summary/File/Data Source element. Three existing dynamic KPI cards now immediately precede the tabs at line 94. The native arrow disappears with its summary.
- `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css:419,433-439`: retain `.bm-dataset-stats dt`, remove unused `.bm-dataset-details` selectors, preserve the existing three-column/mobile grid and 12px tabs margin. No new spacing override is necessary.
- `backend/core/modules/marketplace/test_bundle_monitoring.py:1218`, `test_research_reads_csv_but_does_not_touch_live_records`: require absent details/File/Data Source markup, retained filename in context, unchanged three actual KPI values and direct KPI-to-tab order on both research tabs. Existing missing-file HTTP 503 behavior remains tested.
- This guide and `CAMPUSHUB_CONTEXT.md` record the update. `scratch/remove-dataset-details-20261026/` contains saved source baseline, browser helper, screenshots and comparison evidence, not production code.

### 3. Changes made
Removed only the visible disclosure, heading/arrow and optional filename/source fields. Kept Synthetic Dataset and exact short description, Transactions/Order Items/Unique Products, both tabs, existing run action/search/table/pagination and shared header. Earlier guidance to retain an optional details disclosure is superseded.

### 4. How it works: functions, inputs/outputs and data flow
No runtime function changed. The existing authorized `research(request)` still reads the configured CSV, calculates through the same service, applies the existing GET tab/query/page and passes metadata to the template. `filename` remains in view context at `bundle_monitoring_views.py:221`; it is simply no longer displayed in this research header. KPI outputs still bind to `result.transaction_count`, `result.item_count` and `distinct_products`.

```django
{# Existing value from the view/service, not a replacement constant. #}
<div><dt>Transactions</dt><dd>{{ result.transaction_count }}</dd></div>
```

The tabs are now the next element after `dl.bm-dataset-stats`. Existing margins collapse naturally to a measured 12px gap. This avoids an unnecessary new container, JavaScript or backend change.

### 5. Backend / API behavior
Unchanged routes, permissions, metadata generation, CSV loading, Apriori calculations/thresholds, result caching, search, pagination, form actions and saved-only Marketplace Admin branch. Tests confirm metadata remains available despite its removed presentation. No live analysis action was run for verification.

### 6. Database / migration impact
None. No CSV/model/migration/working-record edits. Django tests use their isolated test database. Nine protected backend/service/calculator/CSV/script/partial/header SHA-256 fingerprints match the pre-existing baseline.

### 7. Tests performed
- 111 Django tests passed in 22.919 seconds across bundle monitoring and bundle suggestions, including permissions, real CSV/results consistency, three KPI values, metadata retention and no-live-record-write checks. System checks found no issues.
- Chromium passed 235 assertions across 28 before/after renders, both tabs at 320/390/768/1024/1280/1440/1920px. Details count decreased from 1 to 0. Tabs are directly after KPIs, moved up 39.5px, and have a 12px KPI-to-tab gap. Heading/description, all KPI labels/values, search markup, full table/rule text, pagination text, header text and tab targets match the prior fixtures. No page overflow, JavaScript errors or missing assets.
- All nine protected fingerprints match, including the CSV. Browser checks made zero working-database requests. Desktop screenshot was visually reviewed.
- Evidence and reproducible script: `scratch/remove-dataset-details-20261026/browser-results.json`, `verify.cjs`. Generate fixtures via existing `BUNDLE_MONITOR_PREVIEW_DIR` hook with the project venv and existing isolated runner before running `node scratch/remove-dataset-details-20261026/verify.cjs`.

### 8. Remaining limitations / troubleshooting / safe practice
Browser verification uses isolated real-template fixtures, not a signed-in working-server session. The preview-only explanatory line in screenshots comes from the test exporter and is not added to the production page. Hard-refresh if cached CSS persists. Dataset missing-file errors still indicate the configured CSV problem and are not hidden or fabricated into empty success. Existing untracked user-owned files were already present, so avoid broad staging of their unrelated contents.

Practice: open both authorized research tabs, verify exactly three cards and no Dataset Details disclosure, then use the existing search and Reset. At 390px confirm cards retain their current stacking and the transaction table scrolls internally. To learn metadata retention safely, inspect the existing `filename=path.name` view binding without modifying it or deleting the CSV.

## Current: three dataset KPIs and optional details, October 26, 2026

### 1. Cause / reason

The current research page already grouped its notice, metadata, tabs and table inside one white panel and had removed Demo Only. However, its five metadata fields were still one wrapping row. The approved change gives the three useful numeric totals compact KPI presentation and moves file/source into an optional disclosure, without adding another outer container or changing data.

### 2. Exact files changed, current lines and code anchors

| File | Current line / anchor | Change and expected behavior |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` | 10 stylesheet version; 86 Synthetic Dataset description; 89 `bm-dataset-stats`; 94 `bm-dataset-details`; 95 existing tabs | Use exact Apriori analysis wording, bind Transactions/Order Items/Unique Products to existing context values, and move actual filename/Synthetic source into one collapsed native details element before the unchanged tabs. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css` | 402 statistics grid; 408 card; 433 details; 445 focus; 462 responsive rule | Replace the obsolete five-field row styles with research-specific KPI/disclosure rules. Three balanced columns above 700px; compact stacked label/value rows below. Natural card heights, existing colors/radii, keyboard focus outline and wrapping filenames. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 1218 `test_research_reads_csv_but_does_not_touch_live_records`; following missing-dataset test | Update existing regression assertions for approved copy, reading order, three dynamic fields, optional file/source, single panel, no badge and unchanged unavailable-dataset behavior. Preserve existing dataset/results/no-live-write and permission coverage. |
| `docs/suggested-product-bundles.md` | This current report | Record cause, exact implementation, functions/data flow, tests, troubleshooting and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | Latest three-KPI entry | Preserve the final role/page-specific UI decision and verified boundaries. |

Five feature/test/documentation files. Verification artifacts live in `scratch/dataset-kpis-20261026/`; they are not runtime modules. The current shared header/breadcrumb implementation is preserved.

### 3. Changes made

The single existing `bm-research-panel` now contains, in order: Synthetic Dataset heading and exact description; three compact statistics cards; Dataset Details, collapsed by default; existing Dataset Preview / Apriori Results tabs; existing analysis action when applicable; search; unchanged table and pagination. No Demo Only badge or duplicate file/source row was added. The existing flask and explicit statement that these are not actual customer purchases remain.

Cards use **Transactions**, **Order Items**, **Unique Products**. The current CSV supplies 1,000 transactions, 2,027 item rows and 150 seller/product identities. These are verified file contents, not constants embedded in the template. The grid is local to the research metadata and does not restyle recommendation KPIs or dashboards.

### 4. How it works: functions, inputs/outputs and data flow

No Python function changed. Existing authorized `research(request)` reads the configured synthetic file and existing analysis output, then sends `filename`, `result.transaction_count`, `result.item_count`, `distinct_products`, tab/search/page state and actual rows through the unchanged `page(request)` renderer. The template changes only how the existing values are arranged.

```django
{# Existing context count is displayed; no dataset count is hardcoded here. #}
<div><dt>Transactions</dt><dd>{{ result.transaction_count }}</dd></div>
```

The `dl` associates each label with its actual value. `bm-dataset-stats` uses one column by default and three `minmax(0, 1fr)` columns above the existing 700px breakpoint family. On narrow screens each card aligns its label/value horizontally to remain compact. No fixed or minimum height was introduced.

Native `<details>` has no `open` attribute, so it starts collapsed. Its `<summary>` supports keyboard toggling without JavaScript. The inner definition list displays `filename` and the existing Synthetic source classification. CSS supplies a visible focus outline and safe filename wrapping. The disclosure neither submits a form nor reloads/executes analysis. Selecting an existing tab still uses its original route/query behavior and starts the disclosure collapsed on the newly loaded page.

### 5. Backend / API behavior

Unchanged: routes, authorization, Super Admin research functionality, Marketplace Admin saved-only analysis access, synthetic/live separation, Apriori formulas and cache behavior, search, table records and server-side pagination. Missing-dataset errors retain their existing status and show neither misleading counts nor file/source details. The page-specific stylesheet version is `20261026-dataset-kpis`; no JavaScript or shared CSS changed.

### 6. Database / migration impact

None. No models, migrations, CSV edits, data initialization, production/working-record writes or environment changes. Regression fixture writes and schema setup run only in Django's disposable test database. Nine protected source/data fingerprints match after implementation: views, recommendation services, calculator, CSV, drawer JavaScript, Marketplace read-only partial, bundle breadcrumb partial and shared header.

### 7. Tests performed: actual results

- **111 Django regressions passed in 32.929s** across `modules.marketplace.test_bundle_monitoring` and `modules.marketplace.test_bundle_suggestions`; Django system checks reported no issues. Existing role/scope, Super highlight prohibition, Marketplace management, synthetic research, recommendations and missing-dataset coverage remains intact. Updated assertions compare displayed values to actual view context for both Dataset Preview and Apriori Results.
- **376 Chromium assertions passed across 14 renders**, both tabs at **320, 390, 768, 1024, 1280, 1440, 1920px**. Verified exactly three real metadata values, one outer research panel, exact description, source identification, correct heading/cards/details/tabs order, hidden initial details, keyboard focus/Enter/Space toggling, actual file/source display, no disclosure navigation/reload, retained search/tabs/table, horizontal columns on larger widths and stacked mobile rows. No page overflow, JavaScript errors or missing assets.
- Measured card heights were content-driven: **74px** on larger widths, **52px** for stacked mobile rows. No CSS height rule enforces those measurements. Desktop and expanded mobile screenshots were visually inspected.
- Browser verification used HTML exported by the existing isolated Django test and intercepted local assets. It made **zero working-database requests** and does not claim signed-in working-server end-to-end coverage. Search/pagination processing remains in unchanged, protected Python and existing regressions; the layout browser check does not pretend that a static fixture filters database records.
- Final checks compare unchanged backend/CSV/shared files and confirm that template changes are limited to approved metadata/copy/cache version, while CSS changes are limited to replacing the research metadata styles. Added-line whitespace and Python test syntax are checked separately.

Reproduce from project root:

```powershell
$env:BUNDLE_MONITOR_PREVIEW_DIR = Join-Path (Get-Location) 'scratch/dataset-kpis-20261026/rendered'
backend/core/venv/Scripts/python.exe -B scratch/dataset-kpis-20261026/run-logged.py regression-tests.txt modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions
node scratch/dataset-kpis-20261026/verify.cjs
```

Before-copies, scoped diffs, logs, metadata checks, browser measurements and screenshots: `scratch/dataset-kpis-20261026/`.

### 8. Remaining limitations, troubleshooting and safe practice

No new functional issue was found within this UI scope. Existing restrictions on safely saved synthetic analysis for Marketplace Admin remain unchanged. Original research GET/execution behavior is preserved. File changes can change the displayed counts; the UI continues to use actual metadata. On mobile the three cards stack instead of squeezing labels/values. The existing wide data table can still scroll inside its own wrapper.

If the previous five-field row remains visible, reload to fetch the new page-specific stylesheet/template. If Dataset Details does not open, check that the browser loaded the native summary/details markup; do not add a custom click script or bypass permissions. Missing-dataset errors intentionally do not display fabricated zero counts.

Safe practice exercise: on an authorized research page, compare the three visible totals with actual dataset metadata, then focus Dataset Details and press Enter. Verify the actual filename and Synthetic source, press Space to close, resize to 390px and confirm cards stack without page overflow. Switch the existing tab and confirm the same order with details initially collapsed. Do not edit the CSV or click Run Demo Analysis merely to test this disclosure.

---

## Current: match other sections' shared breadcrumb UI, October 26, 2026

### 1. Cause / reason
Confirmed: the previous relocation introduced custom 12px text, gaps, wrapping, colors and expanded header height. The user wants the same UI as other sections, not a bundle-specific breadcrumb design. This section supersedes that custom presentation below.

### 2. Exact files changed
- `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css:55`, nearby `.bm-title`: removed all three custom header/breadcrumb override blocks. No shared CSS changed.
- `backend/core/modules/marketplace/templates/marketplace/partials/bundle_header_breadcrumb.html:1-3`: use existing `breadcrumb-link`, `breadcrumb-sep`, `breadcrumb-text`, `breadcrumb-current` classes.
- `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html:10,12`: stylesheet version `20261026-shared-breadcrumb` and existing `admin-module-shell` body class, reusing the same responsive header rules as other sections at `admin_layout.css:2603-2607`.
- `backend/core/modules/marketplace/test_bundle_monitoring.py:744-752,1193`, navigation/header tests: require shared classes, existing module shell and retain placement/navigation checks.
- This guide and `CAMPUSHUB_CONTEXT.md` record the correction. Existing scratch fixture verification now compares computed breadcrumb styles with the bundle body class enabled/disabled, checking that bundle-specific styling does not change shared typography, gap, wrapping, line height or child colors/weights.

### 3. Changes made
Breadcrumb remains in the existing header with > separators, existing links and current-page label. Shared `admin_layout.css` now controls its appearance exactly as for other sections. Removed the custom font/spacing/wrapping/link color/header-height decisions rather than adding replacement styling. Dataset panel and main title/actions remain untouched.

### 4. How it works: inputs/outputs and data flow
The existing authorized view still passes `mode` and `heading` to the bundle page and optional shared-header partial. Named routes output the same links. The partial's shared classes select existing CSS rules from `backend/static/components/css/admin_layout.css:1284-1330`. No new function or data transformation is needed.

```django
{# Same shared class as other sections, not a custom bundle style. #}
<span class="breadcrumb-sep" aria-hidden="true">&gt;</span>
```

### 5. Backend / API behavior
Unchanged routes, authorization, search, tabs, pagination, dataset records, Apriori calculations and menu behavior. Shared header fallback is unchanged.

### 6. Database / migration impact
None. No model, migration, CSV or working-record changes.

### 7. Tests performed
111 Django regressions passed in 25.824 seconds before adding the final module-shell assertion. The isolated final-template exporter passed in 0.469 seconds. Chromium passed 331 assertions across 28 renders/four states/seven widths (320-1920px), including computed font/gap/weight/wrapping/line-height/child-color equivalence with bundle styling disabled, correct header placement, preserved dataset panel and controls, and no page overflow/JavaScript errors/missing assets. Desktop screenshot was reviewed. Initial runs caught old HTML assertions lacking the new shared classes, which were updated. A browser check then caught 320px overflow because the page was missing other sections' existing `admin-module-shell` class; reusing that class fixed it without custom CSS or global changes. Final full rerun passed all 111 tests in 22.678 seconds and all 331 Chromium assertions. Persisted `browser-results.json` includes computed/shared arrays for each render: at 320px both are 9.92px text, 4px gap, 500 weight, shared wrapping and 14.88px line height, with matching per-element colors/weights. This is observed shared-style equivalence, not just a source-code inspection. Reproduce using the existing isolated test runner for `modules.marketplace.test_bundle_monitoring` and `modules.marketplace.test_bundle_suggestions`, followed by `scratch/dataset-contained-20261026/render.py` and `node scratch/dataset-contained-20261026/verify.cjs` with the project Python environment.

### 8. Remaining limitations / troubleshooting / practice
Browser checks use isolated real-template fixtures, not a signed-in live server. This task deliberately does not redesign shared headers or change other sections. Hard-refresh if the removed custom styling is cached. Existing uncommitted user work is preserved without broad staging.

Safe practice: compare Bundle Suggestions' header with another section, identifying the same four `breadcrumb-*` classes in browser developer tools. Confirm > separators, original navigation destinations and no main-content duplicate. Verify computed font size/gap come from shared `admin_layout.css`, not a bundle-specific rule. Do not change global CSS while practicing.

## Current: Bundle Suggestions breadcrumb in header, October 26, 2026

### 1. Cause / reason
The breadcrumb was in the main content using slash separators, while the existing shared header already had a breadcrumb region. The user explicitly approved moving Dashboard > Marketplace > Bundle Suggestions into that header with greater-than separators. Deeper pages retain their current-page segment.

### 2. Exact files changed
- `backend/templates/partials/admin_header.html:8`, `header_breadcrumb_template`: optional included breadcrumb content. The existing default branch remains unchanged for other callers.
- `backend/core/modules/marketplace/templates/marketplace/partials/bundle_header_breadcrumb.html:1-3`: new small partial reusing the original Dashboard and Bundle Suggestions URLs, contextual heading and `aria-current`; separators are `&gt;` and decorative for assistive technology.
- `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html:10,18-20`: cache version, opt-in header include and removal of the duplicate main-content breadcrumb. Page title, subtitle, actions and dataset panel remain in their existing locations.
- `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css:55-73`: replace unused `.bm-breadcrumb` rules with bundle-scoped header text, wrapping and natural header height so long paths fit narrow screens.
- `backend/core/modules/marketplace/test_bundle_monitoring.py:1193`, `test_bundle_breadcrumb_is_once_in_header_with_greater_than_separators`: list/research/activity placement, separators, navigation and shared fallback checks. Existing research test now starts at line 1214.
- This guide, `CAMPUSHUB_CONTEXT.md` and the existing scratch browser verification helper record/check the approved change. Prior section line references are historical after this update.

### 3. Changes made
One breadcrumb now appears under the existing Bundle Recommendations header title, not above the main-content title. The list shows Dashboard > Marketplace > Bundle Suggestions. Research adds > Dataset & Apriori Analysis. Existing detail/activity/saved-only pages use their actual heading. Other application headers keep their existing breadcrumb behavior.

### 4. How it works: inputs/outputs and data flow
Existing authorized view context (`mode`, `heading`) flows into `bundle_monitoring.html`, which supplies a constant trusted template path to the shared header. The header includes that partial only for opted-in callers. The partial outputs existing named-route links and escaped text. No user-provided template path, new endpoint, Python function or JavaScript interaction is introduced. CSS is scoped to `.bundle-monitoring` and affects only presentation.

```django
{# The list is current here; deeper pages link back to that same route. #}
{% if mode == 'list' %}<span aria-current="page">Bundle Suggestions</span>{% endif %}
```

The optional shared slot avoids copying header menus or changing unrelated pages. Header height can grow to fit wrapped breadcrumbs instead of clipping them.

### 5. Backend / API behavior
Unchanged permissions, URLs, queries, forms, search, pagination, dataset statistics, Apriori calculations, actions, account menus and notifications. Dataset container consolidation remains intact.

### 6. Database / migration impact
None. No models, migrations, CSV or working records changed. Django tests use isolated test databases.

### 7. Tests performed
Four Django modules passed 166 tests in 85.824 seconds: bundle monitoring, bundle suggestions, Marketplace Admin dashboard and executive dashboard. A separate actual-template fixture export test passed in 0.554 seconds. Responsive verification checks one breadcrumb inside the header, no duplicate in main, correct greater-than path and measured containment above the main content. Chromium passed 303 assertions across 28 renders at seven widths (320-1920px), covering dataset/results/empty/error states, with no page overflow, JavaScript errors or missing assets. Each render measured that the breadcrumb fits inside the header above main content, and verified exactly one breadcrumb with the requested path. Narrow-screen screenshot was visually reviewed. No working-database browser requests were made. Additional before/after Chromium comparison on both tabs observed an empty prior header breadcrumb becoming the exact requested four-part greater-than path, while main-content breadcrumbs decreased from 1 to 0. Back to Suggestions still resolves to the same route after explicitly normalizing the saved baseline fixture's `index.html` alias. Reproduce with `node scratch\dataset-contained-20261026\compare-header.cjs`; observations are in `header-comparison-results.json` alongside the helper. This directly confirms the requested placement improvement, not a claim of measured human usability gains. The first browser text assertion exposed inline DOM whitespace between separators; the harness now explicitly normalizes separator whitespace, without changing the expected path or application code.

### 8. Remaining limitations / troubleshooting / practice
Browser verification uses intercepted real-template fixtures and local assets, not signed-in working-server acceptance. The changed files contain pre-existing uncommitted work, so do not stage unrelated full-file contents. Hard-refresh for stylesheet version `20261026-header-breadcrumb` if the old layout persists. Do not change global breadcrumb styles to fix a bundle-only issue.

Safe practice: open Bundle Suggestions, follow its existing dataset link, and verify the header changes from the three-part path to the four-part path. Use the Dashboard or Bundle Suggestions breadcrumb link to return. At 390px confirm wrapping stays inside the header with no horizontal page scrolling. To learn the data flow safely, locate `mode == 'list'` in the new partial without changing any route or permission.

## Current: single dataset container, October 26, 2026

This approved update supersedes the older standalone notice and Demo Only badge described below.

### 1. Cause / reason
Confirmed in the active research template: the notice and dataset statistics were siblings before the white dataset panel. The user requested one common region, not a second card or duplicated information.

### 2. Exact files changed
- `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html`: line 10 CSS version, lines 85-99 `mode == 'research'` / `bm-research-panel`. The existing panel now starts before the notice and ends after the existing success/error conditional. Title and Back to Suggestions remain outside at lines 23-24.
- `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css`: line 378 `.bm-disclosure`, line 409 `.bm-dataset-meta`, line 422 `.bm-research-panel>.bm-tabs`. Remove notice card decoration and unused badge styling, align internal content with 20px horizontal padding, use compact vertical spacing and allow long metadata to wrap.
- `backend/core/modules/marketplace/test_bundle_monitoring.py`: line 1193 `test_research_reads_csv_but_does_not_touch_live_records` and line 1225 `test_missing_dataset_is_an_error_not_empty_success`. Check both tab responses for one panel, one notice/statistics row, correct order, outside title/Back and no badge. Error assertions ensure missing data is not shown as empty success.
- `docs/suggested-product-bundles.md`: this implementation report. `CAMPUSHUB_CONTEXT.md`: current presentation summary.
- Reproducible local verification helpers and screenshots: `scratch/dataset-contained-20261026/`. They are test artifacts, not application code.

### 3. Changes made
Moved the entire existing Synthetic Dataset notice and all five existing metadata fields into the existing white panel. Order is heading/description, statistics, tabs, existing controls/table/pagination. Removed Demo Only and standalone banner styling. No new white container or duplicate information was introduced. The error notice shares the same panel but still omits unavailable metadata and tabs.

### 4. How it works: functions, inputs/outputs and data flow
No application Python or JavaScript function changed. Existing permission-checked `research(request)` receives the current GET tab/query/page inputs, reads the same synthetic data and returns the same template context. The template continues rendering `filename`, `result.transaction_count`, `result.item_count` and `distinct_products`; only their parent element changed. The existing calculator and its output are untouched. `analysis_readonly` uses its unchanged partial and is unaffected.

```django
{# Existing service output, never a hardcoded statistic. #}
<span>Transactions <strong>{{ result.transaction_count }}</strong></span>
```

The original `.bm-panel` supplies the single white surface and border. `.bm-disclosure` is now an unboxed internal header. Wrapping metadata avoids forcing a wide page on a narrow screen. This is simpler than adding a nested card or moving business logic.

### 5. Backend / API behavior
Unchanged routes, permissions, search, tabs, pagination, CSV records, Apriori thresholds/calculations, run action and caching. The missing-dataset response still returns HTTP 503 with Retry. Existing form methods/actions, field names and link URLs are unchanged.

### 6. Database / migration impact
None. No models, migrations, CSV edits or working-record writes. Verification uses isolated Django test databases and intercepted browser fixtures.

### 7. Tests performed
The two existing Django modules passed all 110 tests in 26.755 seconds, with no system-check issues. A separate isolated fixture-export test passed in 0.616 seconds. The first command used system Python without Django and failed before tests ran; rerunning with `backend/core/venv/Scripts/python.exe` resolved that environment issue without installing anything. Responsive Chromium verification passed 219 assertions across 28 renders: dataset, results, empty search and missing-dataset error at seven widths from 320 to 1920px. Verified one panel, exact internal order, title/Back outside, no badge or header border, preserved controls and no page/metadata overflow. No JavaScript errors or missing assets. Desktop and mobile screenshots were visually inspected. These were intercepted test fixtures with zero working-database browser requests, not signed-in production acceptance. Additional Chromium before/after DOM comparison passed on both tabs: notice/statistics blocks outside the dataset panel decreased from 2 to 0, badge count decreased from 1 to 0, and panel count remained exactly 1. Statistics text, search input markup, full dataset/rule table text and pagination text matched the prior fixtures exactly. Tab targets matched after normalizing the prior fixture exporter’s `dataset.html`/`results.html` aliases to the unchanged query URLs. The initial raw URL comparison correctly flagged that fixture-only alias difference, then the explicitly normalized comparison passed. Evidence: `scratch/dataset-contained-20261026/comparison-results.json`; reproduce with `node scratch\dataset-contained-20261026\compare.cjs`. This confirms the requested grouping improvement without claiming measured usability gains.

Commands from the project root:
```text
backend\core\venv\Scripts\python.exe scratch\synthetic-notice-20261026\run-tests.py modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions
backend\core\venv\Scripts\python.exe scratch\dataset-contained-20261026\render.py
node scratch\dataset-contained-20261026\verify.cjs
```

### 8. Remaining limitations and troubleshooting
Browser fixtures verify real Django-rendered output and local styles, not an authenticated working-server end-to-end session. Hard-refresh if old CSS persists; the stylesheet cache version is now `20261026-dataset-contained`. Missing-dataset messages indicate the existing configured CSV problem, not a failed layout relocation. Do not invent counts or expose hidden research tabs to work around a 503. Files already contained substantial uncommitted user work before this task, so avoid staging their entire prior contents as though this update created them.

Safe practice exercise: open both authorized research tabs without running analysis, confirm one Synthetic Dataset heading and one statistics row inside the panel, then search for a term that has no matches. Verify the same header/statistics remain and the existing empty state appears. At a 390px viewport, confirm metadata wraps and the table scrolls internally. Restore the query using the existing Reset link.

## Current: compact synthetic dataset notice, October 26, 2026

### 1. Cause / reason

The research template used a long heading and paragraph inside `.bm-disclosure`, with 18px vertical padding and a prominent gold border. This made the identification notice occupy excessive space above otherwise useful dataset metadata. The approved change replaces only that notice and its local styles.

### 2. Exact files changed

| File | Current line / code anchor | Change, reason and expected behavior |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` | 10 stylesheet version; 86 `syntheticNoticeTitle`; 91 `bm-dataset-meta` | Replace the research-only notice with a decorative flask, Synthetic Dataset heading, Demo Only badge and exact short explanation. Associate the notice with its heading. Keep metadata immediately underneath and update the page-specific CSS cache version. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css` | 378 `.bm-disclosure`; 388 icon; 393 content; 396 heading; 406 badge; 415 paragraph | Horizontal flex layout with 10px gap, 12px padding, light neutral border, 14px heading, 13px explanation and a small navy-on-gold badge. Natural text and heading wrapping support narrow screens without fixed heights. Existing dataset metadata styles remain unchanged at line 421. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 1193 `test_research_reads_csv_but_does_not_touch_live_records` | Update the existing notice assertion to require the new heading, badge and explanation and exclude the old paragraph. Preserve the test's real dataset/results and no-live-record-write assertions. |
| `docs/suggested-product-bundles.md` | This current section | Record the approved UI change, functions/data flow, verification and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | Latest compact-notice entry | Preserve the approved presentation and unchanged behavior for future work. |

Five feature/test/documentation files. No new runtime template, dependency or JavaScript was introduced.

### 3. Changes made

The research notice now reads **Synthetic Dataset** with **Demo Only**, followed by: **Simulated marketplace transactions for Apriori testing. Not actual customer purchases.** The small flask is decorative (`aria-hidden`), while the heading and explanatory text convey its meaning. The notice uses the existing navy, gold and white design and a lighter neutral border. Dataset Preview, Apriori Results, query form, pagination and all dataset statistics remain as before.

### 4. How it works: functions and data flow

No Python function changed. The existing permission-checked `research(request)` reads the configured synthetic CSV, receives analysis metadata from the existing service, applies the existing tab/search/page parameters, and passes the same dictionary to `page(request)` and the existing template. The synthetic notice appears only in `mode == 'research'`; Marketplace Admin's saved-only `analysis_readonly` partial is unchanged.

The metadata row still renders `filename`, `result.transaction_count`, `result.item_count` and `distinct_products`. No statistical value is embedded as a constant in the template. The current supplied CSV was checked without running mining: **1,000 distinct transaction IDs, 2,027 item rows, 150 seller/product identities**, file `synthetic_order_items.csv`. These are current file contents, not promised future constants.

Annotated existing binding:

```django
{# The service/view supplies this count; editing the notice does not calculate it. #}
<span>Transactions <strong>{{ result.transaction_count }}</strong></span>
```

The icon is a fixed 20px flex item beside a `min-width:0` text column. The heading and badge can wrap, and the paragraph wraps naturally. This keeps the notice readable without JavaScript, fixed heights or a new component system.

### 5. Backend / API behavior

Unchanged: permissions, existing research execution/cache behavior for Super Admin, saved-only Marketplace Admin branch, routes, search, tab selection, pagination, calculations and actions. The template stylesheet version is `20261026-synthetic-notice`. Existing loading/error handling remains intact; missing datasets still use the existing error response.

### 6. Database / migration impact

None. No models, migrations, dataset edits, activation or working-record writes. Django tests create and destroy only their isolated test database. Seven before/after SHA-256 fingerprints verify unchanged views, services, calculator, synthetic CSV, drawer JavaScript and Marketplace Admin read-only partial.

### 7. Tests performed

- **110 Django tests passed in 24.329s** for `modules.marketplace.test_bundle_monitoring` and `modules.marketplace.test_bundle_suggestions`. Django system checks reported no issues. Existing permission, dataset, recommendation, research and workflow coverage remains intact.
- Chromium fixture verification: **220 assertions passed across 28 before/after renders**, covering both Dataset Preview and Apriori Results at **320, 390, 768, 1024, 1280, 1440 and 1920px**. Verified exact copy, associated heading, decorative icon, horizontal layout, 12px padding, unchanged five metadata fields immediately below, preserved search/tabs, and no page/notice overflow. No JavaScript errors or missing assets.
- Measured notice height: at **1440px**, **112.58px ? 69.5px**; at **390px**, **223.34px ? 108.5px**; at **320px**, **312.02px ? 152.5px**. Before rendering used the saved original notice/CSS; after used the current CSS and HTML generated by the existing isolated Django render test. Desktop/mobile screenshots were visually inspected.
- Browser checks used intercepted test-generated HTML and local assets; they made **zero working-database requests**. They do not claim signed-in working-server end-to-end testing. Existing Django tests verify actual permission-checked view behavior.

Commands from the project root:

```powershell
$env:BUNDLE_MONITOR_PREVIEW_DIR = Join-Path (Get-Location) 'scratch/synthetic-notice-20261026/rendered'
backend/core/venv/Scripts/python.exe -B scratch/synthetic-notice-20261026/run-logged.py regression-tests.txt modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions
node scratch/synthetic-notice-20261026/verify.cjs
```

Evidence: `scratch/synthetic-notice-20261026/` contains scoped originals/diffs, test log, rendered fixtures, browser results, measurements, screenshots and protected-source fingerprints.

### 8. Remaining limitations / troubleshooting / safe practice

This is a presentation-only change. Existing research/saved-data limitations described below remain. Metadata values can change if the configured synthetic dataset changes; the UI continues to display its actual values. On narrow screens the explanation wraps and tables retain their existing horizontal scrolling. If the old border/padding remains visible, reload to obtain the versioned page-specific stylesheet; do not change dataset records or permission guards to fix styling.

Safe practice exercise: open the authorized research page, confirm Synthetic Dataset and Demo Only remain visible, then resize to 390px and check that the explanation wraps while all five metadata fields remain visible below. Switch Dataset Preview/Apriori Results and verify that the same notice remains. Do not select Run Demo Analysis or edit the CSV merely to test the notice. To learn the data binding, locate `result.transaction_count` beside the notice and trace it to the unchanged view/service output.

---

## Current: approved shared Bundle Recommendations improvements, October 26, 2026

This report supersedes older statements below that deny Super Admin the details drawer or deny Marketplace Admin all Dataset & Analysis GET access. Existing routes, dashboards, calculators and seller actions are preserved.

### 1. Cause / reason

Confirmed: role-specific title branches used inconsistent names; the Super Admin empty state treated any query string (including `page=1`) as a search. The existing drawer was limited to Marketplace Admin even though Super Admin already had authorized full-page details. Reversed generated-date ranges silently returned no rows. Display and database date boundaries depended on the active timezone. Finally, the existing Super Admin research GET calculates/caches synthetic results, so merely removing its permission guard would not provide safe read-only Marketplace Admin access.

### 2. Exact files changed, current lines and anchors

Seven application/test/documentation files changed in this approved phase. Paths are relative to the project root; named anchors remain useful when line numbers move.

| File | Current line / anchor | Minimal change and expected behavior |
|---|---|---|
| `backend/core/modules/marketplace/bundle_monitoring_views.py` | 63 `page`; 72 `suggestion_list`; 119 `dates`; 157 `suggestion_detail`; 199 `research`; 229 `readonly_analysis` | Manila rendering/filter boundaries, reversed-range validation, unified list heading, shared scoped details, and a separate saved-only Marketplace Admin analysis branch. |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` | 13 timezone; 23 title; 64 saved table; 77 empty states; 82 drawer; 83 read-only analysis; 98 detail fallback | Exact approved wording, shared eye/drawer shell and full-page content, explicit PHT timestamps, existing analysis link for both authorized roles. Removed unreachable legacy details markup after sharing the existing partial. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_analysis_readonly.html` | New: 2 source navigation; 7 Synthetic Demo; 16 saved Marketplace analysis; 31 saved evidence | Clearly separate live saved evidence from unavailable synthetic snapshots. Reuse actual stored pair metrics, scoped seller/academic labels, search and server-side pagination. No raw order rows or inferred dataset. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css` | 499 `.bundle-monitoring .bm-detail-drawer` | Extend the existing drawer width/style selector to either authorized role. No new layout system, shared CSS or dashboard changes. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 273 `test_phase2_naming...` through 441 error-state test; 852 saved-scope/cache test; existing role assertions | Nine new regressions plus corrected expectations for explicitly approved access and wording. Preserve existing dashboard, seller-management and permission coverage. |
| `docs/suggested-product-bundles.md` | This current report | Cause, functions, exact files, verification, limitations and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | Latest shared-module entry after title | Record the finalized role boundaries and preserved functionality. |

The existing sidebar already said Bundle Suggestions, used the correct route, expanded Marketplace and highlighted the active item. It required no edit. The existing `bundle_monitor_details.html` partial and `bundle_monitoring.js` are reused without modification; their actual product images, evidence, history, escaped content, loading/error handling, Escape/focus management and full-page links remain intact.

### 3. Changes made

- Page/header: **Bundle Recommendations**. Description: **Review suggested product combinations and seller responses across the marketplace.** Table: **Saved Bundle Suggestions**. Analysis navigation: **View Dataset & Analysis**. Sidebar stays **Bundle Suggestions**.
- Zero saved records in authorized scope: **No Saved Bundle Suggestions Yet** / **Saved product recommendations will appear here when available.** Existing saved records excluded by active filters: **No Matching Suggestions** / **Try a different search or reset your filters.** Pagination, authentication and unknown parameters do not count as filters. Blank filter values are normalized consistently.
- Super Admin receives the same authorized read-only details fragment and full-page fallback as Marketplace Admin. This does not add Marketplace operational overview panels to Super Admin or enable highlighting.
- Marketplace Admin's existing research URL returns scoped saved completion metadata and saved recommendation evidence. Synthetic Demo explicitly says that a safely scoped saved result snapshot is unavailable. No demo calculation, cache population, live refresh or command execution is exposed.
- Generated from later than Generated through displays a validation message and no matching rows; it does not silently swap dates. Filters compare the Manila calendar date, and displayed event/recommendation dates explicitly use PHT.

### 4. How it works: functions, inputs, outputs and data flow

`suggestion_list(request)` takes the authenticated user plus existing GET search, scope, seller, response, date and page parameters. The unchanged `status_records_for(user)` first limits records to authorized products, including both sides of a pair. KPI counts still precede table filtering. Recognized nonblank filters determine empty-state wording; `Paginator(..., 20)` still limits each page. A local `Asia/Manila` override ensures `generated_at__date` uses the same calendar as the display. Nothing updates stored timestamps.

`suggestion_detail(request, pk, section)` resolves the scoped recommendation before considering drawer format. Only the details section accepts `format=drawer`; unrelated sections remain 404 for that format. The unchanged `recommendation_evidence(row)` validates saved original direction/metrics; it does not mine or infer provenance. The existing partial receives actual product/seller/history data and renders private/no-store HTML. The existing JavaScript opens the drawer with lazy GET, keyboard focus containment, Escape closing, opener-focus restoration and an ordinary full-page fallback on error. Super Admin's existing explicit highlight denial remains in the unchanged service.

`research(request)` retains the Super Admin calculation/research path. For a permission-checked Marketplace Admin, it returns early through `readonly_analysis(request)` before the synthetic executor, CSV loader or cache. Inputs are optional `tab`, `q` and `page`. Output is the existing page template in `analysis_readonly` mode with persisted metadata and up to 20 authorized saved pairs. `workspace_analysis_summary(user)` requires exact saved live Program/Major scope; unrelated global, other-program and synthetic metadata cannot substitute for it. Unknown counts/dates/rules remain unknown. `recommendations_for(user)` supplies both-product scope for evidence rows, seller references and links. The Synthetic Demo tab supplies no result rows. Query parameters such as `run=1`, `source=synthetic` or `tab=results` cannot activate execution.

Annotated example, not a real marketplace result:

```python
# Existing manager GET -> early saved-only branch, not build_bundle_suggestions.
# ?tab=marketplace&q=Coffee&page=2
analysis = workspace_analysis_summary(request.user)  # Exact saved scope only.
records = recommendations_for(request.user)         # Both products authorized.
# Search existing names; paginate records; render original evidence.
# No completed event => Not recorded, never a guessed analysis date/count.
```

This split was chosen because Super Admin's existing research GET intentionally executes synthetic analysis, while the approved Marketplace access must never execute it.

### 5. Backend / API behavior

One deliberately limited access change: authorized Marketplace Admin may GET the existing Dataset & Analysis URL through a separate saved-only branch. Facilities Admin, anonymous and missing-permission users remain denied. Cross-program/major details remain 404. Super Admin keeps system-wide authorized visibility and its existing research execution functionality, but cannot highlight seller suggestions. Marketplace Admin's normal explicit highlight action, revalidation, seller response and bundle workflows are unchanged. Research POST remains 405 and run POST remains 403 for Marketplace Admin. No new API or URL was created; cache-control remains private/no-store. Dashboard GET behavior and all four recommendation KPIs remain unchanged.

### 6. Database / migration impact

No model, migration, new persistence, activation, stock, payment, order or working-record changes. PostgreSQL schema setup and generated fixture records in tests were confined to Django's disposable `test_` database. All 13 protected working-table row fingerprints matched before/after verification. Six protected source fingerprints also matched: recommendation services/calculator, drawer JavaScript, Reports views and shared sidebar.

### 7. Tests performed: actual results

- Targeted: **68 passed in 11.977s** (`targeted-tests.txt`). An initial new test used an incorrect audit fixture field; it was corrected to the existing actor snapshot fields before this passing run.
- Broader regressions: **286 passed in 74.567s** across recommendation monitoring/suggestions, mobile seller workspace, bundles, FIFO, orders, Marketplace dashboard, executive dashboard, Sales Overview and Super Admin Analytics (`regression-tests.txt`). Django system checks reported no issues.
- Actual authenticated Django HTTP/Chromium acceptance: **1 passed in 48.214s**, **375 measured browser assertions**, **29 navigations**, seven widths **320, 390, 768, 1024, 1280, 1440, 1920px**. Both roles' drawers, manager analysis source views, empty/filter/reset states, keyboard opening/Escape/focus restoration, network-error fallback and actual cross-program 404 were verified. No page overflow, JavaScript errors or missing application assets. HTML/API responses were not mocked; only external Bootstrap assets used a local cache. GET-triggered mining was patched to raise in the test server. Browser fixture setup was corrected to assign the existing Super Admin role explicitly and scope its content heading selector; no application permission logic was altered to make the test pass.
- Existing isolated tests verify actual Manila date conversion/filter boundaries, reversed dates, filtered pagination, Super highlight prohibition, existing manager highlighting, exact Program/Major isolation, rejected anonymous/facility access, zero-history states, error503 and no synthetic execution/CSV reads/cache changes. Saved-scope regression verifies count 17 and actual saved completion time win over newer global/foreign/synthetic count999 fixture metadata; these are disposable test values, not live analytics.
- Actual local working records: **15 permission-checked view scenarios passed inside `SET TRANSACTION READ ONLY`**, across Super Admin, BSIT and BFPT Marketplace Admin. Saved recommendations and completed analysis events were both **0**, so the correct live result is the saved-empty/unrecorded state. Synthetic cache information was unchanged. Authentication/browser coverage came from the separate disposable-database HTTP test, not a signed-in working-server session.
- Screenshots reviewed at desktop/mobile, including Super list/drawer and manager saved analysis. Source syntax, touched-line whitespace, protected fingerprints and unchanged Super research body checked separately. No unavailable design-kit gate is counted as passing.

Commands (PowerShell from the project root; all ORM fixture writes use disposable test databases):

```powershell
backend/core/venv/Scripts/python.exe -B scratch/bundle-phase2-20261026/run-logged.py targeted-tests.txt modules.marketplace.test_bundle_monitoring
backend/core/venv/Scripts/python.exe -B scratch/bundle-phase2-20261026/run-logged.py regression-tests.txt modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions api.test_mobile_seller_workspace modules.marketplace.test_bundles modules.marketplace.test_fifo_inventory modules.marketplace.test_orders_admin modules.reports.test_marketplace_admin_dashboard modules.reports.test_dashboard_executive modules.reports.test_sales_overview modules.reports.test_superadmin_analytics
backend/core/venv/Scripts/python.exe -B scratch/bundle-phase2-20261026/run-logged.py http-tests.txt bundle_http_acceptance
backend/core/venv/Scripts/python.exe -B scratch/bundle-phase2-20261026/working-data-check.py
```

Verification scripts, before-copies, scoped diffs, JSON results and screenshots: `scratch/bundle-phase2-20261026/`.

### 8. Remaining limitations, troubleshooting and safe practice

Marketplace Admin read-only access is implemented for safely scoped saved evidence. **Synthetic result viewing is blocked by absent safely scoped persisted snapshots**; the tab explains this without running or caching anything. Full original basket membership, complete raw rules, historical thresholds and pair-to-run provenance are not stored. The page cannot reconstruct these from today's orders, recommendation dates or rounded metrics. Unknown legacy evidence stays Not recorded. No unverified workbook export was added. Super Admin's existing authorized research GET can still calculate/cache its separate synthetic demonstration, as explicitly preserved.

If a manager sees Not recorded, inspect matching successful live completion audit metadata for that exact Program/Major; do not substitute global counts or infer a run from recommendation creation. A synthetic unavailable message is expected and is not a reason to grant execution rights. For drawer errors, use the existing full-page fallback and verify scope/permissions rather than bypassing 403/404. For apparent date differences, compare the stored aware UTC timestamp with Manila (+08:00); the source timestamp remains unchanged. Reload normally to fetch the page-specific CSS version `20261026-phase2`.

Safe practice exercise: sign in as a scoped Marketplace Admin and open Bundle Suggestions. Use `?page=1&unrelated=1` and confirm it does not create a false filtered-empty state. Search a missing name, reset, then submit a reversed generated-date range and confirm the validation message. Open Dataset & Analysis, switch to Synthetic Demo and confirm there is no Run button. If an actual authorized saved suggestion exists, open its eye link, press Tab and Escape, and verify focus returns to that link. Do not create live suggestions or invoke Super Admin research merely to fill an empty state.

---

## Current: Marketplace Admin saved-evidence Apriori workspace, October 26, 2026

This is the approved A/B implementation on the existing `/admin-bundle-suggestions/` page. It supersedes older guidance hiding technical metrics from Marketplace Admin details, but not the simple seller presentation or either dashboard. Transaction capture, analysis schema, new business rules and real-analysis workbook generation remain separately approval-gated. Dated reports below describe their own earlier changes.

### 1. Cause / reason

Confirmed causes: the existing list managed saved recommendations without explaining analysis provenance. `BundleRecommendation.metrics` can contain original directional Support, Confidence and Lift. Refresh updates verification, not those original metrics. Successful `BUNDLE_ANALYSIS_COMPLETED` audit JSON stores scoped basket/multi-product counts, completion time and saved-recommendation outcome, not the complete rule snapshot, raw rule count or analyzed basket membership. Generated/verified dates cannot substitute for completed analysis time.

The live adapter builds one distinct purchased product per eligible order. There is no verified shared checkout identifier linking separate product orders. Quantity, matching buyer/date and bundle components do not establish independent co-purchases. Real Frequently Bought Together results and a trustworthy four-sheet analysis workbook cannot be manufactured from this evidence.

### 2. Exact files changed, current lines and anchors

Paths are relative to the project root. Lines describe this implementation. Named anchors remain useful after future edits.

| File | Current lines / anchor | Change and expected behavior |
|---|---|---|
| `backend/core/modules/marketplace/bundle_monitoring_views.py` | 28 `DETAIL_TEMPLATE`; 31 `uses_analysis_workspace`; 134 list context; 149 `suggestion_detail` | Opt actual Marketplace Admin into the presentation, add saved context/filter-state detection, and return an authorized `format=drawer` fragment from the existing detail URL. |
| `backend/core/modules/marketplace/services/bundle_monitoring.py` | 96 `_saved_analysis_summary`; 156 `saved_analysis_summary`; 161 `workspace_analysis_summary`; 191 `recommendation_evidence` | Preserve the dashboard contract, project stricter saved-only workspace metadata and validate original metric values/directional identities. No mining or writes. |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` | 12 `bm-workspace`; 35 overview; 41 analysis summary; 53 associations; 63 saved table; 75 eye action; 76 empty states; 79 export; 80 drawer; 95 full-detail fallback | Keep existing KPIs, filters and table. Add scoped sections, truthful missing evidence, formulas, Manila dates, drawer shell and unavailable export, not a fake download. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_monitor_details.html` | New file, 3 `data-bundle-record`; 17 evidence; 32 seller; 41 history; 61 action links | Reuse read-only product, evidence, seller and actual event content in drawer/full details. Separate algorithm verification from human review and analysis completion. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css` | 463 `.bm-workspace`; 473 analysis layout; 499 `.bm-detail-drawer`; 535 mobile rules | Compact cards, responsive metadata/filters, local table scrolling and visible drawer focus. No shared dashboard CSS changes. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_monitoring.js` | 39 initializer; 49 close cleanup; 59 click handler; 69 `AbortController`; 81 `fetch`; 99 failures | Lazy protected GET, loading/error announcements, stale-request cancellation, normal-navigation fallback and focus/scroll restoration. Existing filter/confirmation behavior stays. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 52-175 saved evidence; 176-273 workspace routes/presentation | Eleven added tests for unknown/invalid metadata, actual direction, exact scope, synthetic separation, PHT dates, empty states, drawer/fallback and unchanged Super/research behavior. |
| `docs/suggested-product-bundles.md` | This current report | Confirmed cause, functions, data flow, tests, troubleshooting and practice exercise. |
| `CAMPUSHUB_CONTEXT.md` | Latest workspace entry after title | Preserve approved scope and remaining backend requirements. |

Nine feature files. Separate verification scripts, before-copies, fingerprints, logs and screenshots are under `scratch/bundle-workspace-20261026/`. No dashboard, model, URL configuration, order writer, Apriori calculator, seller-mobile workflow or migration file changed in this task.

### 3. Changes made and approval classification

| Improvement | Classification | Delivered boundary |
|---|---|---|
| Section order, existing compact KPIs, explanations, eye link and honest empty/export states | UI-only with existing data | Marketplace Admin on the existing page only. |
| Saved summary projection and original metric validation | Backend enhancement using existing models | Read-only. Unknown raw rule count remains unknown, not zero. |
| Lazy details fragment on existing URL | Backend enhancement using existing models | Existing scope checks first. No new route, permission or mutation action. |
| Shared checkout capture, complete basket/rule/config snapshots and run-to-recommendation link | Requires separate database/business-rule approval | Not implemented. No invented multi-product orders. |
| Real four-sheet `.xlsx` analysis export | Requires separately approved trustworthy persistence | Unavailable state only. No CSV substitute, silent recomputation or synthetic replacement. |

Order is Recommendation Overview, Apriori Analysis Summary, Frequently Bought Together, Saved Bundle Suggestions and Excel Analysis Export. The drawer holds recorded workflow history and existing-action links instead of a duplicate management dashboard.

The original four KPIs remain unfiltered authorized saved-recommendation counts: total records, records with `sent_at`, records with linked bundles, and sent records without a linked bundle or dismissal. Multiple linked bundles still count as one suggestion. These are not raw rules or synthetic research counts. Existing search, Program, Major, seller, response, generated-date filters and pagination retain their semantics.

An empty authorized database shows **No Saved Suggestions Yet**. Saved records excluded by active filters show **No Matching Suggestions**. Blank parameters, pagination and authentication parameters do not create a false search-empty state. Genuine zero counts remain zero. Unknown counts remain unavailable. No qualifying saved suggestions does not mean zero raw Apriori rules.

### 4. How it works: functions, inputs, outputs and data flow

1. `suggestion_list(request)` receives the existing authenticated GET. `status_records_for(user)` and `recommendations_for(user)` retain server-side product/Program/Major scope. KPIs are calculated before table filters. `uses_analysis_workspace(user)` changes presentation, not authorization.
2. `workspace_analysis_summary(user)` calls `_saved_analysis_summary(user, workspace=True)`. Input: authorized user. Output: dictionary of matching persisted completion evidence plus explicit unavailable values. It validates run identity, version, live source, exact scope, aware time, counts and supported outcomes. Synthetic, unrelated or malformed metadata cannot become live success. Database failures remain distinct from absent history.
3. `saved_analysis_summary(user)` keeps the original dashboard output keys and Super Admin `None` behavior. Scoped basket values remain saved subsets of a marketplace-wide run, never a separately mined denominator. The scope note is shown only when completion evidence exists.
4. `recommendation_evidence(row)` accepts an already-authorized recommendation and returns valid original metrics with the stored antecedent/consequent direction. Missing/foreign/Boolean/floating/malformed IDs and nonnumeric/nonfinite/out-of-range values are rejected. Direction is not guessed from sorted pair foreign keys. Supporting count, original dataset/source snapshot and completed-run date stay unknown without a provenance link.
5. With Bootstrap available, the eye link requests the same detail URL with `format=drawer`. Existing admin-session infrastructure carries per-tab authentication. `suggestion_detail` resolves the scoped recommendation first, then returns escaped Django HTML with private/no-store caching. Cross-program records return 404. Super Admin does not gain a Marketplace drawer or highlight permission.
6. JavaScript imports only expected `data-bundle-record` content. It announces loading/failure, cancels stale requests, offers full-page fallback and restores opener focus/scroll on close. Bootstrap provides dialog semantics, focus containment and Escape handling. The ordinary Marketplace detail page uses the same partial.
7. Existing seller-response, bundle and history links open normal authorized pages. No drawer form sends a message, approves a suggestion or creates/publishes a product. Highlight still requires the unchanged explicit POST and current same-seller/eligibility checks.

Annotated shape example, not actual marketplace findings:

```python
# Unknown evidence is not a measured zero.
workspace = {
    'state': 'unrecorded',
    'basket_count': None,
    'multi_item_basket_count': None,
    'rule_count': None,
    'completed_at': None,
}
# Source/time display Not recorded. Counts display unavailable values.
# A saved recommendation can exist separately from completion history.
```

Support = baskets containing both sides / all eligible analyzed baskets. Confidence = baskets containing both sides / baskets containing the antecedent. Lift = Confidence / the consequent's basket share, using consistent fractional units. The existing calculator and thresholds are unchanged. The page neither recomputes these from current filters nor back-solves counts from rounded saved metrics. Association is not causation or purchase sequence.

This read-only projection was chosen to explain evidence without silently changing its dataset, schema, algorithm or seller workflow.

### 5. Backend / API behavior

Workspace and details GETs do not mine Apriori, refresh recommendations, recount current baskets or write completion history. `format=drawer` is limited to Marketplace Admin details, not arbitrary sections or Super Admin monitoring. The existing GET-only decorator rejects mutation attempts. Scope and analytics permission are enforced before content is returned.

No new API/export endpoint exists. Existing synthetic research access and explicit demo action remain separate and unchanged. Existing unrelated report CSV/PDF behavior stays. A workspace highlight does not prove email/push delivery. Last verification is algorithm verification, not human approval or completed-analysis provenance.

### 6. Database / migration impact

None. No model, migration, checkout field, historical backfill or working analysis/recommendation record was added. All **13** protected working marketplace/inventory/audit table fingerprints match before/after, including orders, recommendations and activity logs. All **10** protected source fingerprints match, including models, order API, academic scope, URLs, Apriori/live adapters, seller-mobile/report views and both dashboard templates.

At verification the working database has **zero saved recommendations and zero completion events**, so honest empty states are correct. Populated screenshots use explicitly isolated test products/itemsets inside Django's disposable PostgreSQL test database, not artificial production orders or live evidence.

### 7. Tests performed and actual results

- **189 Django regression tests passed in 58.039s** across `modules.marketplace.test_bundle_monitoring`, `modules.marketplace.test_bundle_suggestions`, `api.test_mobile_seller_workspace`, `modules.marketplace.test_bundles`, `modules.reports.test_marketplace_admin_dashboard` and `modules.reports.test_dashboard_executive`. Eleven tests were added. The final run log is `scratch/bundle-workspace-20261026/regression-tests.txt`.
- **Actual HTTP acceptance passed: one StaticLiveServerTestCase in 27.323s, 253 browser assertions, twelve navigations, seven widths: 1920, 1440, 1280, 1024, 768, 390 and 320px.** Real login issued per-tab authentication, real list/details returned 200 and a cross-program details request returned 404. Checks covered search/reset, preserved KPIs, original evidence/history/PHT, read-only content, failed-network fallback, keyboard focus containment, Escape/focus restoration, settled drawer geometry and no page overflow. There were zero JS errors and zero missing application assets. No HTML/application API response was mocked. Existing external Bootstrap assets were cached locally.
- The real calculator was patched to raise on workspace/detail mining, not to supply made-up rules. Test product/recommendation/marketplace-audit counts matched before/after, no completion event appeared and `sent_at` stayed unset. Authentication/session writes were confined to the disposable test database.
- Six permission-checked view scenarios used actual BSIT/BFPT accounts/records under PostgreSQL `SET TRANSACTION READ ONLY`. All returned 200 with correct saved-empty, missing-analysis and unavailable-export states. This working-data view check is separate from the disposable-database authenticated HTTP/browser test.
- Template compilation, JavaScript syntax and Django system checks passed. Desktop/tablet/phone screenshots were inspected, including the fully opened 320px drawer. Source/database fingerprints match as described above.
- The first HTTP attempt passed browser checks but failed test cleanup because unmanaged tables reference managed users. The scratch test now allows cascade only during guarded `test_` database cleanup. Reruns including cleanup passed. Browser checks were also strengthened to wait for Bootstrap's opening transition before geometry/screenshots. These are test-artifact fixes, not runtime/schema changes.

Reproduce from the repository root with the existing environment/browser:

```text
backend\core\venv\Scripts\python.exe -B scratch\bundle-workspace-20261026\run-tests.py modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions api.test_mobile_seller_workspace modules.marketplace.test_bundles modules.reports.test_marketplace_admin_dashboard modules.reports.test_dashboard_executive
backend\core\venv\Scripts\python.exe -B scratch\bundle-workspace-20261026\run-tests.py bundle_http_acceptance
```

The HTTP test exercises real project routes with migrated disposable PostgreSQL and isolated ORM fixtures. It is not mocked HTML, but it is also not a signed-in run against the working-data server. No real populated analysis or workbook correctness is claimed where evidence does not exist.

### 8. Remaining limitations, troubleshooting and safe practice

**Separately approval-gated backend requirements:** trustworthy shared checkout/basket capture, persisted eligible basket membership/transaction dates, complete directional rules/counts/supporting counts, execution-time thresholds/reporting bounds and durable recommendation/run provenance. Only then can the requested authorized four-sheet `.xlsx` use exactly the analyzed dataset. No workbook was generated or verified in this phase. Original pair metrics are historical stored values, not a fully reproducible dataset.

The association table intentionally remains empty without a verified raw rule snapshot. It cannot honestly show completed-with-zero-rules or filtered-rule rows from saved-pair counts. Missing history, database failure and insufficient baskets have distinct messages. Recommendation date filters do not define an analysis reporting period. No new sorting or fabricated approval history was added. The drawer shows an existing 25-event page and links to full paginated history.

Troubleshooting:

- Missing analysis: inspect successful matching completion metadata, exact scope/version/source. Never backfill from recommendation dates, current orders or synthetic research.
- Missing metrics: inspect original JSON direction IDs. Old metrics lacking direction remain unavailable instead of guessed. A genuine numeric zero remains zero.
- No access/records: check existing analytics permission and product/Program/Major scope. Do not broaden queries or copy Super Admin permissions.
- Drawer failure: use its full-detail fallback, verify the current per-tab session and static assets, then retry. Normal navigation remains when Bootstrap enhancement is unavailable. The existing app's authentication may itself depend on JavaScript, so complete no-JavaScript login is not newly promised.
- Export unavailable: this is an evidence limitation, not an openpyxl installation problem. Do not substitute CSV, current settings, synthetic examples or fresh analysis.

Safe practice exercise: sign in as Marketplace Admin, open Marketplace > Bundle Suggestions and compare the four totals before/after applying a search. An empty scope should say **No Saved Suggestions Yet**, source/time **Not recorded**, unknown rules and export **Unavailable**. Reset filters and resize to 390px. For populated details use the disposable HTTP test, then verify Tab, Escape, focus restoration and original/missing evidence labels. Do not create working suggestions or click a real highlight just to test presentation.

Version control: a pre-existing `.git/index.lock` dated October 9, 2026 and overlapping dirty/untracked feature files block safe isolated committing. The lock was not removed and prior user work was not staged. Changes remain in the working tree with evidence/before-copies under the scratch folder.


## Current: Super Admin saved-preview card only — October 26, 2026

This approved presentation change supersedes earlier Super Admin dashboard activity-counter/footer guidance. The separate Marketplace Admin card, management workspace and backend capabilities remain unchanged.

### 1. Cause / reason

Super Admin already used its own `super_recommendation_preview.html`, but that partial still displayed Recommendation Activity, three operational counters and a footer. Its subtitle described seller activity, and the template allowed three previews despite the dashboard view requesting only two. Removing this markup makes the card a compact, read-only saved-recommendation overview without changing data or authority.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change and expected behavior |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/partials/super_recommendation_preview.html` | 4 subtitle; 8 error; 11 preview loop; 29 empty description | Exact approved text, template maximum two, retained preview fields; removed activity section and footer. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 179 dashboard preview; 227 recorded preview states; 268 error/empty; 298 explicit template limit; 324 navigation | Update affected UI assertions while retaining actual counters, saved-status, permission, no-mining/no-write and sidebar/detail checks; add a three-record input/two-preview output test. Optional exports stay confined to isolated test fixtures. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 280 saved dashboard; 334 independent activity error | Stop expecting removed counters/activity error text in the card. Continue verifying backend activity errors, actual saved previews, summary values and authorized destinations. |
| `backend/core/modules/reports/test_dashboard_executive.py` | 253 `test_final_major_section_order_and_users_empty_states` | Assert approved empty wording and no controls/counters/footer, while retaining section order, chart grouping and other existing coverage. |
| `docs/suggested-product-bundles.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Explain finalized role-specific presentation, verification, data flow and limitations. |

The additional `test_bundle_suggestions.py` edit was necessary because inspection found assertions expecting the removed UI. This task changes no Marketplace Admin template, shared CSS, JavaScript, runtime Python service/view, URL, permission, API, model or migration. Source/CSS fingerprints verify that the protected card implementation stayed unchanged. An unrelated `backend/static/components/css/admin_users.css` change was observed during verification and preserved; it is outside this task and is not loaded by this dashboard. Reversible verification artifacts are under `scratch/super-bundle-preview-20261026/`.

### 3. Changes made

The card retains **Suggested Product Bundles** and now says **Overview of marketplace product bundle recommendations.** It renders at most two genuine saved previews, retaining both product images/names, missing-photo fallback, seller and recorded status. Its empty state remains **No Bundle Suggestions Yet**, with **Saved product combinations will appear here when available.** A failed load remains a distinct alert: **Unable to load bundle suggestions. Reload the dashboard to retry.**

The Recommendation Activity heading, all three activity counters, activity-empty/error messages and View Recommendations footer are absent from this Super Admin card. A recorded preview status can still say Awaiting Seller Response; that existing record label is preserved and is not an activity counter. No substitute buttons, cards or features were added.

### 4. How it works — functions, inputs/outputs and data flow

The existing permission-checked dashboard view in `modules/reports/views.py` calls `dashboard_bundle_suggestions(request.user, limit=2)`. The unchanged service reads current saved recommendations through `recommendations_for(user)`, checks existing eligibility via `presentation(row)` and supplies `monitor_rows`, `monitor_error`, activity and summary context. Dashboard loading does not run Apriori or save recommendations.

The unchanged `system_overview_summary.html` includes the dedicated Super Admin partial. The template uses `monitor_error` to distinguish failure from an empty list, then loops over `monitor_rows|slice:':2'`. It no longer renders activity/summary fields, but those fields are still returned and tested. Marketplace Admin continues to use its separate `admin_recommendation_summary.html`, with all four counters, rates, Analysis Summary and bottom link intact.

Annotated example: if the saved projection contains three eligible records, `slice:':2'` renders the first two without editing the input list or database. An empty list with no error renders the honest empty state; `monitor_error=True` renders the reload instruction instead. Existing order and eligibility rules remain authoritative.

Existing CSS already supplies `height:auto`, `min-height:0`, 16px padding, 14px radii, 12px section gaps and parent grid `align-items:start`. These rules live in `bundle_suggestions.css`, `admin_dashboard_summary.css` and `admin_dashboard_operations.css`; they need no changes. Removing markup reduces card height naturally while preserving the 70/30 top layout, KPI/Attention arrangement and responsive breakpoints.

### 5. Backend / API behavior

No runtime backend or API changes. Saved counters, rates, analysis metadata, Apriori Support/Confidence/Lift, Excel export, seller workflows and authorized scope remain available exactly as before. Super Admin can still access the existing Bundle Suggestions sidebar/list/details where authorized and remains unable to highlight recommendations by direct POST. Marketplace Admin's management permissions and UI remain unchanged. Removing the dashboard footer does not remove its destination or route.

### 6. Database / migration impact

None. No migrations, working data edits, analysis runs, receipt/stock operations or historical records were created. All 13 protected working marketplace/inventory/audit table fingerprints match before and after. New/updated tests use Django's disposable PostgreSQL test database. Working saved-summary checks run inside read-only PostgreSQL transactions, with mining patched to fail if invoked.

### 7. Tests performed — actual results

- Final regression: **134 tests passed in 37.092s**, covering `modules.marketplace.test_bundle_monitoring`, `modules.marketplace.test_bundle_suggestions`, `modules.reports.test_dashboard_executive` and `modules.reports.test_marketplace_admin_dashboard`. The first regression identified an obsolete navigation test expecting the removed Super Admin footer; its sidebar/direct-route coverage was retained and the final run passed.
- Browser: **1,774 assertions passed across 99 renders** (98 role/state/width renders plus one original-card baseline), with no missing assets, JavaScript errors or working-database requests. Full evidence is in `scratch/super-bundle-preview-20261026/browser-results.json` and `validation-summary.json`. Tests render full isolated Django dashboards at **1920, 1440, 1280, 1024, 768, 390 and 320px**. Super Admin states cover two previews, empty, error, unsent, awaiting response, dismissed and bundle created. Checks verify exact text, images/names/seller/status, no operational counters/footer/controls, no card overflow or blank trailing height and no neighbor stretching. The existing seven Marketplace Admin state/keyboard/rate/metadata checks are also rerun unchanged.
- The 320px page check discovered a pre-existing **13px overflow from the global dashboard Refresh button**. Rendering the original card in the same empty dashboard reproduces it. All updated card states retain the same unrelated overflow; the card itself fits. This is recorded separately rather than counted as fixed or changing shared CSS without approval.
- Django system check passed with no issues. Changed Python files compile; all relevant templates compile; added-line whitespace checks pass. Desktop/mobile card screenshots were inspected. No browser request reaches the working database; no mutation request is sent.

Reproduce the isolated regressions with `backend/core/venv/Scripts/python.exe scratch/super-bundle-preview-20261026/run-tests.py modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions modules.reports.test_dashboard_executive modules.reports.test_marketplace_admin_dashboard`. After exports exist, run `prepare-browser.py`, then `node scratch/super-bundle-preview-20261026/verify.cjs`. Browser fixtures come only from isolated test records; none populate the working dashboard.

### 8. Remaining limitations / troubleshooting / safe practice

The unrelated global Refresh control still overflows slightly at 320px; shared CSS and unrelated dashboard sections were intentionally left unchanged. Preview eligibility, sorting and any existing fewer-than-two results remain unchanged. An actual error should continue to display its alert instead of a fabricated empty state.

If operational counters still appear inside the Super Admin card, verify that the page includes `super_recommendation_preview.html`; do not edit the Marketplace Admin partial or remove service calculations. If the card is hidden, check the existing analytics permission/role guard rather than bypassing it. Authorized details remain accessible through the existing Marketplace sidebar.

Safe practice exercise: open Super Admin Dashboard and inspect the preview card, then follow Marketplace → Bundle Suggestions and verify read-only access. Compare Marketplace Admin: its activity, rates and Analysis Summary should still exist. Resize to 390px and confirm the preview is compact. Use the isolated test suite for populated/error/three-record limit cases; do not create working recommendations simply to demonstrate a visual state.

## Current: compact Marketplace dashboard card presentation — October 26, 2026

This approved UI update supersedes the previous visible missing-history wording only. Saved analysis metadata, calculations, source separation and authorization remain unchanged.

### 1. Cause / reason

The card already had the correct structure, centered icon, intrinsic height, collapsed native rates disclosure and footer link. Remaining clutter came from 12px subsection gaps, repeated outcome explanations in the preview and analysis area, two rate-explanation paragraphs, and the older No Analysis Yet / Analysis history not recorded display labels. Missing historical evidence must not imply that no analysis ever occurred.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html` | 19 empty description; 41 rates explanation; 46–53 Analysis Summary | Exact requested empty-state text; one concise, correctly pluralized rate explanation; presentation-only Not recorded labels and helper; preserve verified dates/counts/outcomes and scope explanation. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css` | 2–9 Marketplace-only compact selectors | 10px card/subsection spacing, reduced preview padding, 4px counter-row padding and right-aligned 14px activity values. Existing analysis typography, padding, borders, focus and intrinsic sizing stay. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 18 stylesheet version | Updated only the bundle-card CSS version for reliable cache refresh. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 613 optional state fixtures; 648/671 presentation regressions | Cover unknown/error/verified/no-rule/insufficient states, unavailable versus genuine zero rates, retained calculations/context and no dashboard writes/mining. |
| `docs/suggested-product-bundles.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Record current copy, scope, actual verification and safe exercise. |

No recommendation service, model, API, JavaScript, permission, Super Admin template, unrelated CSS or dashboard section changed. Verification-only tools and artifacts live in `scratch/bundle-card-ui-20261026/`.

### 3. Changes made

Reading order remains Suggested Product Bundles → saved recommendations/empty state → Recommendation Activity → optional rates → Analysis Summary → View Recommendations. The empty state now says **Eligible saved recommendations will appear here.** All four actual counters remain. The native rates disclosure has no open attribute, keeps both computed percentages and uses one short explanation retaining the all-dates/sent denominator and created-or-dismissed response definition.

Unverified history displays **— / Not recorded / Not recorded**, with **No completed analysis record is available for your scope.** Verified runs retain their actual count, Philippine-local timestamp and Marketplace Orders source. Zero-result/insufficient outcomes remain visible once in Analysis Summary. A successful populated run avoids a redundant Analysis completed sentence; the important authorized-subset explanation remains. Unavailable history retains its distinct alert instead of being relabelled as unrecorded. The bottom link keeps its existing label-left/arrow-right arrangement and destination.

### 4. How it works — functions, inputs/outputs and data flow

The unchanged `_marketplace_operational_dashboard_data(request, user)` → `dashboard_bundle_suggestions(user)` → `saved_analysis_summary(user)` pipeline supplies the same scoped saved preview, counters, rates and validated analysis fields. The partial changes only their visible representation. In particular, the backend still returns its existing unrecorded state/labels; the template checks `analysis_summary.state == 'unrecorded'` and prints the new UI copy without rewriting history or changing the data contract.

Annotated example: `{state: 'unrecorded', basket_count: None, completed_at: None}` renders an em dash and two Not recorded values. A verified `basket_count: 0` still renders **0** with its saved completion time. Likewise, rates whose denominator is absent remain **—**, whereas zero responses from an actual sent recommendation remain **0.0%**. These are different data conditions, not values replaced for appearance.

Marketplace-scoped selectors override the existing dashboard cascade without affecting Super Admin. Counter and footer components, centered shared empty state and native `<details>/<summary>` are reused. Native Enter/Space interaction and existing visible focus indicators require no new JavaScript or duplicate controls.

### 5. Backend / API behavior

No service or calculation changes. Existing analytics/Program/Major permissions, same-seller restrictions, saved-only dashboard loading, recommendation previews/activity/rates, live-versus-synthetic separation, completion metadata and zero-result semantics remain. `bundle_monitor_list` still resolves to `/admin-bundle-suggestions/`; its sidebar page and access rules are preserved. Super Admin receives no Analysis Summary or restored activity counters.

### 6. Database / migration impact

None. No working analysis execution, audit write, recommendation generation or historical backfill occurred. All **13** protected marketplace/inventory/audit table fingerprints match before/after. Test data and completion fixtures were confined to Django's disposable test database. Read-only working projection checks still show unrecorded history for the actual Marketplace Admin scopes and no added summary for Super Admin.

### 7. Tests performed — actual results

- **133 regression tests passed in 35.801s** across bundle monitoring/suggestions, Marketplace Admin dashboard and Super Admin executive behavior. Includes existing scope, source, completion metadata, calculation, workflow, navigation and permission regressions plus the new UI-only assertions.
- After the final singular/plural wording refinement, **2 focused presentation tests passed in 0.937s**. These verify the exact new labels/helper, unchanged backend context, no writes/mining, real counters and genuine zero percentages.
- **1,018 browser assertions  / 49 renders** at **1920, 1440, 1280, 1024, 768, 390, 320px** passed for completed, no-rule, insufficient, unrecorded, no-saved-recommendations, unavailable and sent-recommendation states. Checked exact text, four counters/three analysis fields, retained source/time/count, scope/outcome notes, 10px spacing, right alignment, bottom link/arrow route, no page overflow, collapsed disclosure, focus indicators, Enter opening, Space closing, unavailable-rate dashes and genuine 0.0% values. No missing assets, JavaScript errors, mutation requests or working-database browser requests. Desktop/mobile screenshots were inspected.
- Template compilation, Django system check and scoped added-line whitespace verification passed. The current working saved-only projection was checked under PostgreSQL read-only transaction enforcement with mining patched to fail if called.

Reproduction/evidence: `scratch/bundle-card-ui-20261026/run-tests.py`, `verify.cjs`, `live-read-check.py`, `snapshot.py`, test logs, isolated HTML, screenshots and `browser-results.json`. Run the test helper with `modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions modules.reports.test_dashboard_executive modules.reports.test_marketplace_admin_dashboard`, then run `node scratch/bundle-card-ui-20261026/verify.cjs`.

### 8. Remaining limitations / troubleshooting / safe practice

The operational reader still supports persisted live analysis only. Separate synthetic research is neither merged nor relabelled as completed operational analysis. Missing historical runs remain unverifiable; changing visible labels does not create records or prove that analysis never occurred. Existing single-product basket/insufficient-data limitations remain. A taller right-hand card can still determine the top grid's overall height, but Attention itself is not stretched; layout proportions/breakpoints were preserved.

If old wording/styles remain, reload the page to obtain the updated stylesheet. Do not change backend historical labels or fabricate events to match UI text. Check the actual unrecorded versus unavailable state when diagnosing missing values. Native disclosure should start closed on a fresh load while remaining operable with keyboard; browser history may preserve a user's own interaction state.

Safe practice exercise: open the card, focus Seller response and bundle rates, press Enter and then Space, and verify visible focus plus preserved page layout. Use the isolated empty and sent fixtures to compare **—** with legitimate **0.0%**. Resize to 390px and confirm no page overflow. Do not send working recommendations, edit audit rows or run analysis merely to populate a visual example.

## Current: saved live Analysis Summary — October 25, 2026

The approved Analysis Summary is confined to the Marketplace Admin dashboard card. It does not add analysis to Super Admin's simplified preview or change Apriori, seller workflows, permissions, models or migrations.

### 1. Cause / reason

The existing explicit live refresh returned processed-basket counts but saved only pair evidence. Its generated/verified dates could not establish a completed analysis, especially when no recommendations qualified. Synthetic research kept separate cached results with no durable run completion record. Therefore dashboard loading could not truthfully infer a historical count, completion date or source from saved pairs/current order totals/CSV file dates.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
|---|---|---|
| `backend/core/modules/marketplace/services/bundle_suggestions.py` | 101 `saved_analysis_summary`; 190 `basket_scopes`; 213 scope increment; 232 `_analysis_basket_scopes` | Attach a saved-only summary in the Marketplace Admin branch and count academic cohorts from the exact existing baskets sent to the unchanged calculator. Private cohort evidence is excluded from the ordinary API projection. |
| `backend/core/modules/marketplace/services/bundle_monitoring.py` | 24 `_analysis_outcome`; 33 `_record_analysis_completion`; 95 `saved_analysis_summary`; 243 completion call | Append atomic run/scope completion snapshots, validate reconciliation/identity, read only the reader's matching saved scope and format timestamps in Manila. |
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html` | 19 completed-empty preview; 49 `marketplace-analysis-summary` | Add the three requested fields beneath activity/rates and distinguish completed insufficient/no-rule runs from unrecorded history. Existing previews/counters/navigation stay. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css` | 2–6 summary selectors | Subtle divider, compact typography, left labels/right values and wrapping without fixed card heights. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 18 bundle stylesheet version | Refresh the existing CSS asset reference so cached styles do not hide the new presentation. No layout or context logic change here. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 457–638 completion/scope/failure/history tests and optional fixtures | Verify successful/zero-rule runs, rollback, duplicate identities, scopes, timestamps, historical fallback, no dashboard mining and unchanged Super Admin. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 489/509 isolated multi-item evidence; 557 actual processed-basket test | Supply the exact test basket provenance when mocking the existing missing multi-item boundary; test real eligible single-product counting and exclusion of private evidence from API output. |
| `docs/suggested-product-bundles.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Explain current functions, data flow, safeguards, actual verification and limitations. |

There are nine feature files, including the necessary stylesheet cache-version update. Verification-only tools and generated fixtures are in `scratch/bundle-analysis-summary/`. No unrelated source was reset.

### 3. Changes made

The existing card now reads Suggested Product Bundles → saved preview/empty state → Recommendation Activity and its existing rates → Analysis Summary → existing View Recommendations. Analysis Summary contains only Analyzed Baskets, Last Analysis and Data Source. Successful live runs use Marketplace Orders; actual timestamps display in Asia/Manila. Missing historical evidence shows an em dash, Analysis history not recorded and No Analysis Yet, with explanatory text. Loading failures are an unavailable state rather than a fake empty result.

Completed runs producing zero baskets or insufficient multi-product evidence retain a real count/time and insufficient-data explanation. A successful sufficiently populated run with no qualifying rules has a separate no-qualifying-suggestions outcome. No synthetic research count or timestamp is displayed as operational live analysis.

### 4. How it works — functions, inputs/outputs and data flow

1. The unchanged command `refresh_bundle_recommendations --actor <existing authorized Super Admin username>` calls `refresh_live(actor)`. It remains explicit, privileged and separate from ordinary page loading; no new button, scheduler or endpoint is added.
2. The existing live builder selects eligible Completed AND Paid records, approved sellers/products, academic/order boundaries and actual supported baskets. `analyze_live` increments `_analysis_basket_scopes` only when appending an actual basket to the calculator input. Existing single-product baskets have zero multi-item baskets. No grouping is invented from names, dates, variants or bundle recipes, and no formulas/thresholds change.
3. `refresh_live` retains its PostgreSQL transaction/advisory lock and existing pair persistence. Only after those writes succeed does `_record_analysis_completion(actor, result, seen)` validate that integer cohort counts reconcile with the calculator count. Missing/conflicting evidence raises ValidationError and rolls back the entire refresh.
4. A UUID identifies the actual execution. One `BUNDLE_ANALYSIS_COMPLETED` AccountActivity event is appended for the global scope and each existing Program/Major scope, including genuinely empty cohorts. All share the same completion timestamp/run ID and identify source=live, analysis_scope=marketplace, outcome and scope-specific counts. Existing audit logging records the real operator. A repeated run identity is rejected under the existing advisory lock. Separate explicit executions may legitimately have different run IDs even if their inputs are unchanged.
5. Each scoped record describes the authorized product-resource subset of the marketplace-wide analysis, not a separately recalculated per-program algorithm. The UI explicitly says **Baskets in your scope from the saved marketplace-wide analysis**. No scoped record includes the global basket total. Current Program/Major access selects only its exact scope; global/other-major/synthetic entries are never fallback evidence. Counts for qualified saved pairs likewise require both products to match the scope.
6. `saved_analysis_summary(user)` reads at most the latest matching successful live event. It validates schema, aware timestamp, run ID, count types and recorded outcome, then returns only display fields. It never mines, counts current orders, serializes audit metadata or exposes global totals. Historical outcomes remain tied to their recorded execution even if thresholds change later. The output uses JSON-safe strings; Manila formatting is generated from the saved aware timestamp, leaving its stored timezone semantics intact.

Annotated test example: a completion stored as `2026-10-17T19:10:15+00:00` displays **Oct 18, 2026 · 3:10 AM**. A scoped six-basket result stays six if orders change afterward. This is isolated test evidence, not a historical event inserted into the working database.

### 5. Backend / API behavior and safeguards

Completion events and recommendation persistence commit or roll back together. Failure/interruption cannot leave a committed success marker from a partially persisted run; the rollback regression fails the second scope write to verify this. Scoped completion entries are distinct parts of one run, not duplicate analyses. The existing schema has no new unique constraint; duplicate prevention covers the serialized application writer and rejects repeated run identities. It does not attempt to protect against arbitrary out-of-band audit-table edits.

Marketplace Admin needs its existing analytics/admin access and valid Program/Major scope. Super Admin's dashboard branch returns before adding summary data. Existing recommendation preview bounds, activity/rates calculations, navigation, same-seller eligibility, seller actions and Super Admin read-only web authority remain unchanged. Existing monitoring event queries do not count completion snapshots as seller responses or created bundles. Synthetic CSV research/cache and public/live/seller projections remain separate; private cohort metadata is not added to their UI/API payloads.

### 6. Database / migration impact

No models, migrations, settings, working product/seller/order/inventory records or historical audits changed. Future explicit successful refreshes append metadata using the existing AccountActivity JSON field. This task did not run a working live refresh or seed completion records. All **13** protected table fingerprints, including AccountActivity, match before/after. The working database still has **zero** recorded completion events, so both actual Marketplace Admin scopes correctly display historical information as unrecorded; it was not backfilled from pair dates.

### 7. Tests performed — actual final results

- Broader overlapping regression selection: **326 tests passed in110.405s**, including bundle monitoring/suggestions, seller permissions, dashboard/Analytics/report exports, Orders, exact inventory variants, bundles, FIFO and PostgreSQL FIFO concurrency.
- Final focused rerun after historical-outcome validation: **131 tests passed in37.922s** across monitoring/suggestions, Super Admin executive and Marketplace Admin dashboard. Verifies completed runs with recommendations, zero baskets, sufficient baskets/no rules, missing/invalid history, exact counts, fixed UTC→Manila conversion, source separation, Program/Major isolation, missing permissions, no global fallback, duplicate run IDs, reconciliation failures, partial audit-write rollback, no dashboard mining/writes and unchanged Super Admin/workflows. Existing mocked multi-item tests now supply their actual isolated input cohorts instead of treating present single-product checkout as multi-item capture.
- Browser: **409 assertions /28renders** at **1920,1440,1280,1024,768,390,320px** for completed, no-rule, insufficient and unrecorded states. Checked field order, scope count/source, Manila timestamp against Intl.DateTimeFormat, activity-before-summary placement, existing counters/link, divider/alignment, no new controls/charts, no page overflow/missing assets/JavaScript errors/mutation requests. Desktop/mobile screenshots were inspected.
- Read-only working verification: saved projections for actual Marketplace Admin actors9/14 are unrecorded, Super Admin1 has no added summary, and zero working completion records remain. The verification patches mining to fail if called and runs under PostgreSQL-enforced read-only transactions. Django system check, template compilation and scoped whitespace checks passed.

Reproduce with `backend/core/venv/Scripts/python.exe scratch/bundle-analysis-summary/run-tests.py` for the broader selection or pass `modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions modules.reports.test_dashboard_executive modules.reports.test_marketplace_admin_dashboard` for focused tests. Then run `node scratch/bundle-analysis-summary/verify.cjs`. Logs, fixtures, screenshots, browser results and hashes are in that directory. `live-read-check.py` reads saved projections only; `snapshot.py` fingerprints existing tables without writes.

### 8. Remaining limitations / troubleshooting / safe practice

Historical executions without completion records cannot be recovered reliably; the approved fallback remains. The current live builder has single-product baskets, so it generally cannot produce qualifying multi-product associations and may honestly report insufficient data. Adding verified shared checkout baskets is separate work. A scoped count is the processed subset of a marketplace-wide run, not its global Apriori denominator or an independently executed scoped analysis. Existing settings/permissions and basket semantics were preserved rather than relabelled.

Analysis Summary is live-only. Merely opening/re-running synthetic research never supplies operational history. No separate real-data XLSX export, dataset selector or new analysis trigger is added. Existing preview eligibility can change after analysis; that does not rewrite the saved run count/time. A newly introduced Program/Major with no matching snapshot shows unrecorded history until a future successful refresh includes it.

If the summary is unknown, check for a matching versioned successful live completion with the current scope; do not substitute recommendation generated_at, current order totals or CSV modification time. If a refresh reports count reconciliation or duplicate-identity failure, investigate the input evidence and existing run before retrying; do not delete audits or bypass validation. The dashboard stylesheet reference was updated for cache consistency.

Safe practice exercise: run `test_completion_records_exact_counts_timestamp_source_and_scope`, `test_completed_run_without_qualifying_rules_is_not_unknown_history` and `test_zero_basket_run_is_completed_without_inventing_suggestions` in Django's disposable test database. Compare their summary values and Manila timestamp. Then run the saved-summary isolation test and confirm ICT/HE counts differ while the global count stays hidden. Use generated browser fixtures to inspect the card at390px. Do not run a working refresh just to populate the demonstration or fabricate historical completion events.

## Current: consistent Bundle Suggestions navigation — October 25, 2026

This approved request supersedes the earlier dashboard-only Super Admin navigation rule. The existing monitoring workspace is reused; no duplicate page, permission grant or Apriori change was introduced.

### 1. Cause / reason

`admin_sidebar.html` explicitly required `not request.user.is_superuser` and the Marketplace Admin role for the existing Bundle Suggestions item. This intentionally implemented an older rule, also asserted by the navigation test. The dashboard's View Recommendations link and `bundle_monitor_list` route correctly admitted authorized Super Admin accounts, so the sidebar contradicted the actual destination. The existing breadcrumb omitted Marketplace and used role-specific workspace headings rather than a consistent module label.

### 2. Exact files changed / current anchors

| File | Current line / code anchor | Change |
|---|---|---|
| `backend/templates/partials/admin_sidebar.html` | 70 analytics/active/suspension guard; 71 normalized role check; 72 `bundle_monitor_list` | Expose the existing item to authorized Super Admin and Marketplace Admin; retain existing analytics permission and active-account requirements; add `aria-current="page"` only when active. |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` | 19–21 `bm-breadcrumb` | Dashboard / Marketplace / Bundle Suggestions; details/activity/research retain a named-route link back to the same list and their own current-page suffix. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py` | 290 consistent-navigation test; 341 authorization test; 363 optional browser fixtures | Replace the obsolete exclusion assertions, test both authorized roles, active/open state, denied roles/missing permission and read-only data preservation; export isolated browser records. |
| `docs/suggested-product-bundles.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Record current navigation, actual verification, data flow and limits. |

No runtime Python, URL, permission configuration, CSS or JavaScript changed. QA-only scripts and evidence are under `scratch/bundle-navigation-consistency/`.

### 3. Changes made

Marketplace now includes the same Bundle Suggestions navigation item for authorized Super Admin and Marketplace Admin accounts. The existing `active_page='bundle_suggestions'` marks it active on all workspace pages. The existing group-expansion script detects that active link and opens Marketplace even when session storage previously recorded the group as closed. The whole-sidebar collapse preference and responsive icon rail remain unchanged. Existing role-specific headings remain: Super Admin's Marketplace Recommendations and Marketplace Admin's Suggested Product Bundles. Breadcrumbs consistently identify their shared Bundle Suggestions module.

### 4. How it works — functions, inputs/outputs and data flow

The existing named route `bundle_monitor_list` resolves to `/admin-bundle-suggestions/` and `suggestion_list(request)`. Its unchanged `can_view_bundle_suggestions(actor)` checks authenticated/active administrative access, eligible role and `can_view_marketplace_analytics`. The sidebar retains that permission and eligible normalized roles; it does not grant access. The unchanged view reads saved authorized recommendations and renders the same `bundle_monitoring.html` through `page(request, **context)`.

The template includes the shared sidebar with `active_page='bundle_suggestions'`. The sidebar outputs one active link and `aria-current="page"`; its existing script gives active children precedence over saved group-closed state, synchronizes `aria-expanded` and makes navigation accessible. No new state machine is added. Example: visiting an existing suggestion detail keeps Bundle Suggestions active and renders Dashboard / Marketplace / Bundle Suggestions / Suggestion Details. The module crumb returns to the original list URL.

### 5. Backend / API behavior

Super Admin's canonical `is_super_monitor` and server-side mutation denial remain unchanged. Direct Highlight POSTs still return403 for Super Admin; Marketplace Admin retains its existing permission-gated action and ownership/Program/Major limits. Facilities Admin, regular users, anonymous users and readers lacking analytics permission do not gain access. No recommendation is generated, highlighted, sent or published through navigation. Existing research and seller workflows are untouched.

### 6. Database / migration impact

None. No models, migrations, role grants, environment settings, working recommendations or inventory records changed. All twelve protected table fingerprints match before and after. Actual-route rendering used PostgreSQL `SET TRANSACTION READ ONLY`; browser checks used isolated rendered test records and never reached working records.

### 7. Tests performed — actual results

- **121 tests passed in41.571s**, including bundle monitoring, saved suggestions, Super Admin executive dashboard and Marketplace Admin dashboard regressions. Covers both navigation roles, analytics permission/role denials, direct URL access, Super Admin direct-POST denial, existing manager actions, scoping, no mining on dashboard GET and unchanged records.
- **389 browser assertions /38renders** at **1440,1280,1024,768,390,320px**. Checked list/detail/activity for both roles, exactly one sidebar item, active state/`aria-current`, Marketplace expansion despite a saved closed preference, accessible icon-rail label, breadcrumb hierarchy/back-link, read-only Super Admin versus existing manager action, keyboard navigation and no page overflow. No missing assets, JavaScript errors or mutation requests. Desktop screenshots were inspected.
- Actual read-only direct-route checks: Super Admin actor1 and Marketplace Admin actors9/14 return200; Facilities Admin actor10 and anonymous requests return403. The route resolves to the existing `suggestion_list`, and the permitted rendered pages contain the new sidebar item and breadcrumb. Django system check passed.

Reproduce: `backend/core/venv/Scripts/python.exe scratch/bundle-navigation-consistency/run-tests.py modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions modules.reports.test_dashboard_executive modules.reports.test_marketplace_admin_dashboard`, then `node scratch/bundle-navigation-consistency/verify.cjs`. `live-read-check.py` checks current records without allowing database writes. Logs, isolated HTML, screenshots, browser results and protected-table hashes are in that directory.

### 8. Remaining limitations / troubleshooting / safe practice

No recommendation title, filter layout, analytics calculation or management workflow was redesigned. Whole-sidebar collapse preferences remain respected; an expanded Marketplace group does not force a user-collapsed sidebar to become wide. Missing analytics permission should hide the item and produce403 at the destination; do not grant broad permissions merely to make a link visible.

If the item is absent for an authorized active account, inspect the active root sidebar template, actual role/analytics permission and current application process. If the group closes on entry, confirm the link has `active` and the page passes the existing active-page key before changing shared JavaScript. An absent record may still legitimately return404 on a detail route.

Safe practice exercise: open the existing list, confirm the gold Bundle Suggestions item and Dashboard / Marketplace / Bundle Suggestions breadcrumb, then open a detail and use its module crumb to return. Collapse Marketplace, reload the current Bundle Suggestions page and confirm active-item precedence reopens the group. Use the isolated permission tests for denied/direct-POST cases; do not change working roles or send live recommendations to test navigation.

## Current: Suggested Product Bundles Card Positioning and UI Consistency Across Dashboards - October 25, 2026

1. **Cause / reason.** The Suggested Product Bundles card in the Marketplace Admin dashboard (`/admin-dashboard/` for Marketplace Admins using `admin_marketplace_dashboard.html`) exhibited visual and layout inconsistencies when compared to the clean Super Admin reference card (`super_recommendation_preview.html`). Specifically, the card subtitle was separated outside the header, the empty state used a left-aligned plain text div without an institutional shopping bag icon, metric counters were oversized (22px vs. institutional 16px), and spacing between the empty state and the Recommendation Activity section lacked a consistent divider (`border-top: 1px solid #E8EAF0; padding-top: 12px;`).
2. **Exact files changed.**
   - [admin_recommendation_summary.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html): Lines 2-5 moved the subtitle inside `<header>` as `<p class="marketplace-recommendation-subtitle super-recommendation-subtitle">`. Lines 16-20 integrated `dashboard/partials/empty_state.html` with `icon='bag'` for centered empty states. Lines 23-46 wrapped activity metrics in `<div class="marketplace-recommendation-activity super-recommendation-activity">` with `<h3>Recommendation Activity</h3>`, preserving all 4 scoped operational counts (`Saved Suggestions`, `Sent to Sellers`, `Awaiting Seller Response`, `Bundles Created`) and the expandable rates disclosure details block.
   - [bundle_suggestions.css](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css): Lines 2-32 unified card container rules (`display: grid; align-content: start; gap: 12px; padding: 16px; border-radius: 14px; height: auto;`), title `h2` (`16px; font-weight: 600; color: #1A1851;`), subtitle (`12px; color: #667085;`), centered `.ch-dashboard-empty` with 24px icon, activity divider (`border-top: 1px solid #E8EAF0; padding-top: 12px;`), compact activity metrics (`padding: 5px 0; dt: 12px, #667085; dd: 16px, #1A1851, font-weight 600, tabular-nums;`), and 40px action link with gold hover underline (`text-decoration-color: #FCB316`).
   - [admin_marketplace_dashboard.css](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css): Lines 613-615 synchronized `.bundle-dss.marketplace-recommendation-summary` to `border-radius: 14px; padding: 16px;` and counts row padding to `5px 0;` to eliminate conflicting overrides.
   - [admin_marketplace_dashboard.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html): Lines 15-16 bumped stylesheet cache versions to `?v=20261025-bundle-sync`.
   - [admin_dashboard.html](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/templates/dashboard/pages/admin_dashboard.html): Line 23 bumped stylesheet cache version to `?v=20261025-bundle-sync`.
3. **Changes made.** Aligned the Marketplace Admin card with the Super Admin visual benchmark while preserving respective roles: Marketplace Admin retains its 4 operational counts and expandable rates details block; Super Admin retains its 3 oversight counts and `slice:':3'` preview limit. Replaced raw empty divs with the standardized centered `empty_state.html` partial (displaying the Lucide bag icon, "No Bundle Suggestions Yet" or "No Eligible Preview" heading, and descriptive copy). Replaced oversized metrics with compact, accessible left-aligned `dt` labels and right-aligned tabular `dd` numbers. Ensured a clean divider separates the preview/empty region from the activity block.
4. **How it works / functions, inputs, outputs and data flow.** Data flows from `dashboard_bundle_suggestions(user)` through `marketplace_data['bundle_analysis']` into the template context. In `admin_recommendation_summary.html`, if `monitor_rows` are present, preview items render in a clean compact list; if empty, `empty_state.html` renders with the shopping bag SVG icon. Below the preview region, `.marketplace-recommendation-activity` renders the `<h3>Recommendation Activity</h3>` heading followed by `<dl class="marketplace-recommendation-counts">` mapping each metric key to its integer value or `&mdash;` dash fallback. Slicing tests remain green because the activity container uses `<div class="marketplace-recommendation-activity">` rather than a nested `<section>`, ensuring automated substring slicing from `<section class="dash-card bundle-dss marketplace-recommendation-summary"` to `</section>` captures the full card including the single `<a class="marketplace-recommendation-action">` link.
5. **Backend / API behavior.** Zero changes to backend APIs, mining algorithms, Apriori calculation parameters (Support, Confidence, Lift), suggestion persistence, or seller notification workflows. Both dashboard views continue reading saved records in read-only mode on GET without invoking synthetic mining or database mutations.
6. **Database / migration impact.** None. No database schema changes, model alterations, migrations, or data alterations were performed.
7. **Tests performed.**
   - **89 unit tests passed in 14.96s** across `modules.marketplace.test_bundle_monitoring`, `modules.marketplace.test_bundle_suggestions`, and `modules.reports.test_dashboard_executive` (`.\venv\Scripts\python.exe manage.py test modules.marketplace.test_bundle_monitoring modules.marketplace.test_bundle_suggestions modules.reports.test_dashboard_executive --keepdb`).
   - **7 empty-state tests passed in 1.14s** across `modules.reports.test_dashboard_empty_states` (`manage.py test modules.reports.test_dashboard_empty_states --keepdb`).
   - **14 executive dashboard tests passed in 3.16s** across `modules.reports.test_dashboard_executive`.
   - **Live HTML verification script execution** (`verify_dashboard_bundle_cards.py`) confirmed:
     - Super Admin `/admin-dashboard/`: Status 200, contains `.super-recommendation-preview`, centered empty state with bag icon, 3 activity counts, View Recommendations link.
     - Marketplace Admin `/admin-dashboard/`: Status 200, contains `.marketplace-recommendation-summary`, subtitle inside header, centered `ch-dashboard-empty` with bag icon, Recommendation Activity heading, 4 activity metrics, rates disclosure details, View Recommendations link.
8. **Remaining limitations / troubleshooting / safe practice exercise.**
   - Live browser testing: Ensure hard-refresh (`Ctrl+F5`) to clear cached CSS files if styles do not immediately update in an active browser session.
   - Troubleshooting: If the activity counts show dashes (`—`), confirm that `dashboard_bundle_suggestions` can query `BundleRecommendation` without database connectivity interruptions.
   - Safe practice exercise: To verify responsiveness without touching production data, open the Marketplace Admin dashboard at `/admin-dashboard/`, resize the browser window to mobile width (375px), and verify that the card adapts neatly with no horizontal overflow, with activity labels left-aligned and counts right-aligned.

---

## Historical: Super Admin panel wording and one navigation action - October 24, 2026

1. **Cause / reason.** The user requested one clear Suggested Product Bundles heading instead of Bundle Recommendations & Activity followed by another Suggested Product Bundles heading. Recommendation Activity names a distinct group of read-only counts and remains. The dashboard keeps its oversight role and one View Recommendations action. This supersedes the older Super Admin panel-name and empty-copy descriptions below.
2. **Exact files changed.** `backend/core/modules/marketplace/templates/marketplace/partials/super_recommendation_preview.html:3` changes the main title while keeping `marketplaceRecommendationsTitle`; line 4 uses Saved product combinations and seller responses. Line 6 replaces the formerly titled inner section with a plain div and removes its duplicate h3, avoiding a reference to a deleted heading ID. Line 29 uses Eligible saved recommendations will appear here. Recommendation Activity at line 34 and the sole existing action at line 52 remain. Existing assertions in `backend/core/modules/marketplace/test_bundle_monitoring.py:235` verify one new main title and absence of the removed inner heading ID; dashboard title expectations at line 299 and `backend/core/modules/marketplace/test_bundle_suggestions.py:302` follow the new wording. This guide, `docs/campushub-system-overview.md:64` and `CAMPUSHUB_CONTEXT.md:3` record the current panel name.
3. **Changes made.** One main heading and concise subtitle introduce the same saved product pairs, photos/fallbacks, seller and response/delivery status. No Bundle Suggestions Yet remains, with shorter explanatory text. Recommendation Activity retains Sent to Sellers, Awaiting Seller Response and Bundles Created as read-only counts with their existing values and independent errors. View Recommendations opens the same workspace. No Approve, Reject, Send, Create Bundle or optional Details action was added. CSS, layout and JavaScript are unchanged.
4. **How it works / functions, inputs, outputs and data flow.** The unchanged dashboard view calls `dashboard_bundle_suggestions(user, limit=2)` after its access check. It supplies saved `bundle_analysis.monitor_rows`, response/delivery presentations, activity state and `dashboard_summary` counts. The same template loop renders those records; only static copy and the redundant inner heading wrapper change. `presentation(row)` and `activity_summary(user)` continue providing existing values. Main-panel and activity accessibility references still resolve. Example: `<h2 id="marketplaceRecommendationsTitle">Suggested Product Bundles</h2>` changes the visible name while retaining the parent aside's accessible name reference. No runtime function, query or calculator changed.
5. **Backend / API behavior.** APIs, permissions, eligibility, saved-state handling, preview limits, seller workflows and analytics remain unchanged. Existing tests verify dashboard GET does not run Apriori mining or write recommendation/product/activity records. Python edits affect existing presentation-test expectations only. SHA-256 checks confirm 129 runtime service/report/JavaScript/CSS files remain unchanged.
6. **Database / migration impact.** None. No schema, migrations, live records, environment, deployment or restart changes. Regression tests used the separate PostgreSQL test database. Browser panels were exported by the existing isolated tests, not inserted into production.
7. **Tests performed.** **87 Django tests passed** across `modules.marketplace.test_bundle_monitoring`, `modules.marketplace.test_bundle_suggestions` and `modules.reports.test_dashboard_executive`, with no system-check issues. Log: `scratch/bundle-panel-copy-review/django.log`. Coverage includes no-mining/read-only dashboard GET, saved previews, responses, empty/error distinction and existing access/navigation. **189/189 browser/source checks passed** across ten Chromium renders at 1366px and 390px, covering populated saved pairs, unsent, sent, created and dismissed states. Checked one Suggested Product Bundles heading, retained Recommendation Activity and three counts, exactly one View Recommendations link, zero buttons/forms, valid accessible references, no panel overflow and 129 protected hashes. Log: `browser.log`; harness: `check.cjs` in the same scratch folder. Visually inspected [laptop](../scratch/bundle-panel-copy-review/panel-1366.png) and [mobile](../scratch/bundle-panel-copy-review/panel-390.png) screenshots.
8. **Remaining limitations / troubleshooting / safe exercise.** Browser checks use actual application assets and isolated Django fixtures in headless Chromium, not an authenticated live session or every browser engine. Existing photo fallbacks remain. Refresh the dashboard if old wording remains; there is no stylesheet cache change. Safe exercise: inspect the panel in development, confirm one main heading, three read-only counts and a single View Recommendations link, then follow that link without sending or creating anything. Inspect the `bundle_analysis.monitor_rows` loop to see why changing its heading cannot change saved recommendations.

---

## Current: Super Admin saved product-pair previews — October 23, 2026

This update supersedes the earlier **Super Admin count-only panel**. Marketplace Admin keeps its existing four-count summary. Only the Super Admin **Bundle Recommendations & Activity** panel changes; the rest of both dashboards remains as implemented.

### 1. Cause / reason

Confirmed in the existing code: the Super Admin view already requested two saved recommendation presentations, but `system_overview_summary.html` included the Marketplace Admin numeric summary instead. Product names, photos, seller and response data were available but hidden. No new recommendation calculation or workflow was necessary.

### 2. Exact files changed

Paths are relative to the CampusHub root; anchors make these locations searchable if lines move.

| File / current line | Anchor and change |
| --- | --- |
| `backend/templates/dashboard/partials/system_overview_summary.html:123` | Include `super_recommendation_preview.html` instead of the shared numeric summary for the existing Super Admin aside. |
| `backend/core/modules/marketplace/templates/marketplace/partials/super_recommendation_preview.html:1` | New presentation-only partial: requested title/subtitle, product pairs, seller, saved-state badge, three activity counts, independent errors, requested empty copy and one existing workspace link. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:53` | `dashboard_bundle_suggestions`: expose the existing `presentation()` delivery string alongside response; no new query, field or status. |
| `backend/static/components/css/admin_dashboard_operations.css:182` | `.super-recommendation-preview` rules: Inter, compact 36px photos, quiet navy/neutral status badge, 14px card radius, separated activity rows, readable wrapping and a 44px action target. Scoped to this panel. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` | Changed operations CSS cache key to `20261023-bundle-preview` so the browser fetches this stylesheet revision. Other asset keys remain unchanged. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:133` | Latest two saved pairs, saved response lifecycle, image fallback, empty/error distinction, no dashboard mining/writes or operational actions. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:280` | Super Admin empty-state expectations; later populated case expects two real pair previews. Marketplace Admin assertions remain. |
| `backend/core/modules/reports/test_dashboard_executive.py:246` | Extract the complete aside when checking navigation and activity labels; nested semantic sections no longer truncate the test's panel. |
| `docs/dashboard-analytics-operations-update.md:3` | Current-layout note points to this report and supersedes only the count-only recommendation layout. |
| `CAMPUSHUB_CONTEXT.md:3` | Record this latest explicit Super Admin preview decision for future work. |

### 3. Changes made

**Suggested Product Bundles** now means actual saved pair previews, not a numeric KPI. Each preview displays both product names and first photos, a plus sign, seller name and a textual status badge. The existing view requests **two**, and the template also defensively caps output at three. There are no internal scrolling regions or tables.

**Recommendation Activity** contains only Sent to Sellers, Awaiting Seller Response and Bundles Created. Zero activity counts remain honest zeros. If pairs exist without activity, the requested **No Recommendation Activity Yet** explanation appears below them. No records produces **No Bundle Suggestions Yet** with the exact requested purchasing-pattern explanation. Database failures have separate error messages rather than pretending records are absent or counts are zero.

### 4. How it works — functions and data flow

1. Existing `modules/reports/views.py:1207` calls `dashboard_bundle_suggestions(request.user, limit=2)` after the existing access check. Input is the authenticated actor; output is presentation data for the dashboard template.
2. The helper at `services/bundle_suggestions.py:40` reads current saved `BundleRecommendation` rows through `recommendations_for(user)`. Existing model ordering is newest `generated_at`, then newest primary key. Existing product/seller eligibility checks are retained.
3. Existing `services/bundle_monitoring.py:123`, `presentation(row)`, reads actual related Product records and owner. `Product.get_image_list()` supplies each first image. Existing `bundle_photo.html:1` supplies the product placeholder if absent; the already-loaded `bundle_monitoring.js` reveals that placeholder on image load failure.
4. `presentation()` derives response from existing persisted facts: an actual linked bundle, saved seller dismissal, or `sent_at`. The display expands **Awaiting Response** to **Awaiting Seller Response**. Where response is **Not Applicable**, the badge uses the existing delivery label **Not Sent to Seller**. These are presentation labels, not new database statuses.
5. Existing `activity_summary(user)` at `bundle_monitoring.py:61` supplies actual saved sent/awaiting counts and real linked bundle-product counts. The preview helper returns them separately in `dashboard_summary`; only three are rendered as activity counts.
6. Django escapes names and seller text. One bottom link resolves the existing `bundle_monitor_list` route (`/admin-bundle-suggestions/`). No operational forms or buttons are rendered.

Annotated example from the template:

```django
{# row.products contains real Product presentation values, never example merchandise. #}
{% include 'marketplace/partials/bundle_photo.html' with product=row.products.0 %}
<span>{{ row.products.0.name }}</span>
{# Activity remains a separate persisted-workflow count. #}
<dt>Bundles Created</dt><dd>{{ bundle_analysis.dashboard_summary.created }}</dd>
```

This approach reuses existing records, permissions, image fallback and aggregation. A separate Super Admin partial prevents this explicit oversight layout from changing the Marketplace Admin operational summary.

### 5. Backend / API behavior

No route, permission, scope, algorithm, view action, API contract or business workflow was changed. Dashboard GET still reads saved live recommendations and never invokes Apriori or writes recommendations/audits/products. The existing saved-record workflow contains no import from synthetic research data on this path. Support, Confidence and Lift are not rendered. Super Admin remains oversight-only; the existing detailed workspace and server-side restrictions are retained.

### 6. Database / migration impact

No models, fields, migrations, schema updates or development/production records were added or changed. Test products and recommendations are created only in Django's isolated test database, with normal rollback.

### 7. Tests performed

- **96 Django tests passed** across `test_bundle_monitoring`, `test_bundle_suggestions`, `test_dashboard_executive`, `test_dashboard_kpi_cards` and `test_dashboard_empty_states`. Log: `scratch/super-bundle-preview-tests.log`.
- The two existing-in-that-run preview/image tests were then rerun to export isolated fixtures; **2 passed**, overlapping the 96 rather than two additional unique tests. Log: `scratch/super-bundle-preview-fixtures.log`.
- **32/32 DOM, image-error fallback, response-state, navigation and scoped-style checks passed** with `node scratch/super-bundle-preview-review/verify.cjs`. These are markup/JS checks, not browser screenshots.
- Django `manage.py check`: no issues. Changed operations CSS served locally with HTTP 200 and a SHA-256 matching the workspace file.
- Workspace-wide `git diff --check` found an unrelated existing trailing blank line in `backend/static/components/css/admin_analytics.css:1103`; that file was left untouched. See final scoped whitespace verification for this change below.
- Final scoped scan of all **12 touched files** found no trailing whitespace or missing final newline. The DOM verification script also passed Node's syntax check.

### 8. Remaining limitations / troubleshooting / safe practice

No connected browser is available (`apps: []`, `browsers: []`), so real viewport, photo rendering and pixel-level review remain unverified. There was no deployment, server restart, environment edit or live-data creation. The existing helper checks eligibility after limiting the latest candidates; an ineligible candidate can make the panel show fewer than two. This existing eligibility policy was not changed.

If you still see only four numbers, open the **Super Admin** dashboard and hard-refresh with Ctrl+F5. Inspect the loaded operations CSS URL for `20261023-bundle-preview`; confirm the running checkout includes the new partial. Marketplace Admin intentionally keeps its previous summary. A legitimate empty state is not a CSS failure: it means there are no current eligible saved pairs in the selected candidates. Do not populate production with demonstration records to hide an empty state. An error message instead requires investigating database connectivity without exposing credentials.

**Safe practice:** in the new Super Admin partial, temporarily change the subtitle in a development checkout, reload and confirm only this panel's subtitle changes; undo that text edit afterward. Then run `python manage.py test modules.marketplace.test_bundle_monitoring --keepdb --noinput` from `backend/core` with the project's Python interpreter. Verify the tests pass and the Marketplace Admin panel still uses `admin_recommendation_summary.html`. This exercise teaches the include boundary without changing transactions, recommendation generation or permissions.

Latest October 23 source change: Marketplace Admin Dashboard now reads **saved** scoped BundleRecommendation results via the existing `recommendations_for` / `activity_summary` helpers. It no longer runs Apriori on dashboard GET. Suggested counts current saved records; sent/awaiting/created use actual saved history/linked bundle products. Earlier live-mining summary descriptions below are historical and superseded. The existing explicit live/research analysis endpoints and algorithm remain unchanged. Current complete files/line anchors, data flow, test results, error behavior and safe learning exercise: [Marketplace dashboard guide](dashboard-marketplace-design.md).


## Current: Marketplace Admin recommendation summary — October 23, 2026

### 1. Cause / reason

The Marketplace Admin dashboard still rendered separate Frequently Bought Together and Cross-Sell preview panels. These did not provide the requested compact operational summary or a single entry to the saved recommendation workspace. Inspection confirmed that the existing live Apriori presentation and saved activity-summary helper already supply the necessary data; no new calculator, controller or recommendation page is needed.

The final dashboard naming is role-specific: **Marketplace Recommendations** for Marketplace Admin; **Bundle Recommendations & Activity** for Super Admin; **Suggested Product Bundles** for sellers. Summary item names can still describe suggested bundles; the Marketplace Admin section itself does not use the Super Admin title.

### 2. Exact files changed

| File / current line | Anchor / purpose |
| --- | --- |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:62` | Existing `dashboard_bundle_suggestions`: attach existing saved activity summary and four scalar dashboard values to the Marketplace Admin live result |
| `backend/core/accounts/academic.py:114` | Existing `scope_products`: preserve explicit Product scope and add the missing mobile-seller fallback at lines 122–127 when Product Program is absent |
| `backend/templates/dashboard/partials/marketplace_overview_row.html:7` | Replace the old FBT include with the compact summary; remove the separate Cross-Sell include |
| `backend/core/modules/marketplace/templates/marketplace/partials/admin_recommendation_summary.html:1` | New small presentation partial: requested name/subtitle, four counts, independent empty/error states and one named-route action |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:2` | Scoped `.bundle-dss.marketplace-recommendation-summary` styles: Inter, simple rows, subtle border, readable values and 44px action |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:16` | Version bundle CSS as `20261023-summary`; near the existing footer remove obsolete dashboard bundle dialogs/preview script |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:57` / `82` / `98` | New scoped summary/read-only GET, safe error state and mobile Program/Major fallback tests |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:230` / `268` | Update old preview expectations; verify buyer Program does not scope recommendations and the live count uses actual qualifying rows |
| `docs/suggested-product-bundles.md:3`, `CAMPUSHUB_CONTEXT.md:3` | This guide and current project context |

### 3. Changes made

One compact card now shows:

- Suggested Product Bundles
- Sent to Sellers
- Awaiting Seller Response
- Bundles Created

Its subtitle is “Monitor suggested product bundles and seller responses within your marketplace scope.” Its only action is **View Recommendations →**, using existing `bundle_monitor_list` (`/admin-bundle-suggestions/`). There is no recommendations table, per-record action, duplicated search or extra nested card.

The exact requested two empty messages are supported independently. Request failures show an em dash and a useful error message rather than pretending the failed count is zero or showing a successful empty state. The new card has no Support/Confidence/Lift, approval/rejection language, trained-model claim or send/create button.

### 4. How it works: functions, inputs/outputs and data flow

The existing permission-checked `_marketplace_operational_dashboard_data(request, user)` still calls `dashboard_bundle_suggestions(user)`. For Marketplace Admin this retains the existing `build_bundle_suggestions(user, source='live')` → `recommendation_presentation(...)` path. The summary adds existing `activity_summary(user)` to that public result and passes only the four values into the partial.

| Value | Actual source / meaning |
| --- | --- |
| Suggested Product Bundles | `len(result['rows'])`: complete eligible qualified live association results, not the truncated preview length or synthetic CSV count |
| Sent to Sellers | Existing saved recommendation aggregate where `sent_at` is recorded |
| Awaiting Seller Response | Existing sent records without a linked created bundle or recorded dismissal |
| Bundles Created | Existing count of actual linked bundle Product records whose owner matches the recommendation |

These are scoped summaries, not new analytics formulas. Suggested count reflects current qualified live patterns; activity is historical saved delivery/response activity, so the values need not match. The dashboard does not generate/save recommendation records or send anything merely by loading the page. Existing Marketplace Admin live analysis behavior is retained; Super Admin's saved-results GET branch remains unchanged and does not mine on GET.

`activity_summary()` reuses `status_records_for()`, `linked_bundles_for()` and `recommendations_for()`. The latter scopes **both** products using `scope_products(queryset, actor, prefix='')`. Prefix support is also reused for existing order querysets (`prefix='product__'`). Neither helper filters recommendations by the buyer's academic affiliation.

`scope_products()` first honors explicit Product Program/Major. If Product Program is absent, it falls back to the linked web seller or mobile seller Program/Major. Invalid/missing Marketplace Admin scope still returns an empty queryset. A valid explicit Product scope cannot be replaced by a conflicting seller fallback. Superusers retain their existing global branch. The database's existing one-owner product constraint prevents ambiguous simultaneous seller owners.

```python
# Example only: Admin scope BTLED/ICT; no live record is inserted.
# Product Program=BTLED, Major=HE -> excluded even if seller is BTLED/ICT.
# Product Program absent, mobile seller=BTLED/ICT -> included.
# The buyer's Program/Major is not part of either decision.
'suggested': None if result['error'] else len(result['rows'])
# None is shown as an unknown value, not a fabricated zero.
```

The existing dashboard page refresh/filter submission produces fresh server HTML. There is no extra API poll or client-side summary calculator. Removed modal scripts belonged to the old per-pair preview; operational actions still live in the existing detailed workspace.

### 5. Backend / API behavior and permissions

Existing analytics permission and role checks control whether the summary is included. Existing detailed page, routes, filters, seller-response/history handling, send/highlight permission checks and idempotence remain. Highlight still requires an eligible scoped recommendation and eligible seller. No Approve Recommendation or Reject Recommendation workflow is added.

The only shared scope correction is the missing mobile-seller fallback described above, within the administrator's already authorized Program/Major. No role is granted broader permissions. Existing web-seller fallback, explicit Product scope, out-of-scope denial and buyer independence remain tested. Raw credentials/metadata and technical Apriori metrics are not added to ordinary UI.

Where technical explanation is useful, the correct wording is **Association rules generated using the Apriori algorithm.** This is not a trained AI model. The Apriori processing, thresholds, algorithm and research-only CSV flow are unchanged.

### 6. Database / migration impact

No models, migrations, source datasets, recommendation deliveries, seller responses, bundles, orders, payments, inventory or other application records were changed. New test records exist only inside Django's isolated test database. No environment, server service, deployment or Flutter files changed.

### 7. Tests performed, troubleshooting and safe practice

- **147 focused Django tests passed:** bundle monitoring/suggestions, scoped Marketplace Admin dashboard, account management/Monitoring and Activity API. New checks cover four counts, one destination, no table/technical metrics, unchanged records after GET, independent failure states, mobile seller fallback, explicit Product priority, cross-major exclusion and an out-of-program buyer contributing to an in-scope seller's eligible transactions. Log: `scratch/marketplace-recommendation-summary-tests.log`.
- **33 additional regression tests passed:** existing domain analytics permissions, dedicated role dashboards, Marketplace Admin order access and Orders administration. Log: `scratch/marketplace-summary-scope-regression.log`.
- **38/38 DOM/CSS checks passed** over actual isolated empty/populated/error renders, including exact labels, single destination, no old panels/dialogs, actual five-rule fixture count, unknown error value, preserved Super Admin heading and CSS parsing. Harness: `scratch/marketplace-recommendation-summary/verify_summary.cjs`.
- Django system check reported no issues; scoped whitespace check passed.
- The versioned Marketplace summary stylesheet returned HTTP 200 with content matching the workspace. It introduces no new runtime JavaScript.
- Browser inventory was empty and the in-app browser unavailable. No responsive pixel, screenshot, full keyboard or native-browser claim is made.

Earlier assertions referenced removed FBT/Cross-Sell copy, previews and dialogs; those were updated to test the explicitly requested summary. Backend eligibility/permission assertions were retained. An initial placement of a new test split an existing method; it was corrected before the successful final run.

Safe practice: open the Marketplace Admin dashboard with an already authorized account, find the four summary labels and open View Recommendations. Review an existing record/history without sending or changing it. Compare the seller/product Program/Major with the assigned admin scope; do not use buyer affiliation as a scope filter. Then view Super Admin and confirm its title remains Bundle Recommendations & Activity. These checks require no sample live transactions or permission edits.

Troubleshooting: use Ctrl+F5 and confirm `bundle_suggestions.css?v=20261023-summary`. Zero live suggestions can be correct when qualifying completed multi-item history is insufficient. Existing checkout/history limitations are not bypassed with research CSV data. A failed count is an em dash with an error, while a verified empty result is zero with its relevant empty-state text. The full detailed page remains the place for operational actions and history.

### 8. Remaining limitations

Suggested live-pattern count and historical saved activity intentionally represent different facts; sending activity is not a count of current qualifying patterns. Current operational history may be sparse, so empty states remain expected. The existing detailed workspace retains its established labels and filters; this request changes the dashboard section name. Actual browser/responsive visual acceptance is outstanding. The separate three legacy Reports Analytics test failures documented in the final-dashboard guide remain outside this recommendation update. Nothing was deployed or restarted.

## Current recommendation navigation — October 22, 2026

This section owns the Super Admin navigation cleanup. Older sidebar-entry descriptions below are superseded. Current dashboard positioning is documented in [the dashboard layout guide](dashboard-system-status-design.md); its compact two-group recommendation panel is retained.

### 1. Cause / reason

The shared sidebar previously included Bundle Suggestions for either a superuser or a Marketplace Admin. Super Admin already has a Dashboard recommendation summary and View Recommendations action, so the permanent sidebar item duplicated that entry point. The full recommendation page also used Suggested Product Bundles as its main title despite the broader oversight purpose.

### 2. Exact files changed

| File / current line | Nearby code anchor / change |
| --- | --- |
| `backend/templates/partials/admin_sidebar.html:71` | `not request.user.is_superuser` restricts the existing analytics-permission-gated Bundle Suggestions link to the existing Marketplace Admin role |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html:4` | Super Admin listing document title is Marketplace Recommendations |
| Same template, lines 19–20 | Dashboard / Marketplace Recommendations breadcrumb; detail/activity parent link uses the same name |
| Same template, line 21 | Super Admin list heading and requested subtitle; Marketplace Admin wording retained |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:110` | `test_recommendation_navigation_is_dashboard_led_for_super_admin_only` verifies role-specific sidebar, dashboard entry, title/breadcrumb, route access and unchanged record counts |

This guide and `CAMPUSHUB_CONTEXT.md:3` record the current behavior. No routes, stylesheets, scripts, views or mobile files were changed.

### 3. Changes made

The Super Admin Marketplace sidebar now has Products, Inventory, Orders and Sellers, subject to its existing permissions, without a permanent recommendation item. The Dashboard's Bundle Recommendations & Activity panel and its named-route View Recommendations link remain unchanged, including its maximum two previews, actual activity counts and requested empty-state descriptions. No unsupported suggestion total was introduced.

The existing full listing at `/admin-bundle-suggestions/` now shows **Marketplace Recommendations** in its Super Admin browser title, page heading and breadcrumb, with **Review suggested product combinations and seller responses across the marketplace.** as the subtitle. Super Admin detail/activity breadcrumbs point back to Marketplace Recommendations. Existing authorized Dataset & Analysis navigation remains available separately.

Marketplace Admin keeps the existing Bundle Suggestions sidebar label, destination and list wording. Seller navigation was not edited. Existing Inter and SugarPie wordmark styling are reused without new CSS.

### 4. How it works: inputs, outputs and data flow

The sidebar takes the existing `request.user` and `perms` inputs. Its outer analytics permission check remains. The inner template condition now renders the recommendation link only when the user is not a superuser and already has the Marketplace Admin role. This changes visible navigation only; it grants or revokes no endpoint permissions. A superuser with a Marketplace Admin role string still has no permanent recommendation sidebar item.

The full page still receives `heading`, `mode` and `super_monitor` from the existing monitoring view/context. When `super_monitor` is true and the heading is Suggested Product Bundles, the template displays Marketplace Recommendations instead. This also keeps the listing error page context consistent. The existing flag, defined by `is_super_monitor(user)`, remains the authority for Super Admin monitoring presentation; no role-to-superuser conversion or new permission logic was introduced.

Flow: existing dashboard context → saved live recommendation preview/activity → `{% url 'bundle_monitor_list' %}` → existing `suggestion_list` → existing scoped queryset, filters and pagination → the same monitoring template with clearer Super Admin labels. Product/detail/history/response/created-bundle navigation still uses the existing stable-ID routes.

Example: a Super Admin opens Dashboard and follows View Recommendations. The destination is the existing list, with Dashboard / Marketplace Recommendations above it; the sidebar has no second link to that list. A Marketplace Admin opens the same named route from Bundle Suggestions and retains the existing operational context and scope.

### 5. Backend / API and permissions

Unchanged. Reused routes include `bundle_monitor_list` (`/admin-bundle-suggestions/`), `bundle_monitor_detail`, `bundle_monitor_section`, `bundle_monitor_activity` and the separately authorized research routes. No page was deleted or duplicated.

Existing query functions remain unchanged: `dashboard_bundle_suggestions(user, limit=2)` reads saved eligible live previews; `activity_summary(user)` supplies actual activity totals; `suggestion_list` uses `status_records_for`/`recommendations_for`, existing search/program/major/seller/response/date filters and pagination. No mining, Apriori thresholds, stock calculation or synthetic/live boundary changed.

Super Admin remains read-only and existing direct operational POST attempts remain forbidden. Marketplace Admin retains Program/Major scope and authorized highlighting. Seller permissions and own-product recommendation logic remain unchanged. Support, Confidence and Lift remain absent from normal monitoring views; authorized research views retain their existing separation.

### 6. Database / migration impact

None. No application records, model, migration, environment, credentials or server deployment changes. The regression fixtures are isolated Django TestCase records, not inserted marketplace data. The navigation test checks that recommendation, activity and product counts do not change during these GETs.

### 7. Tests, troubleshooting and practice

**93 targeted Django tests passed** across bundle monitoring, bundle suggestions, bundle products/seller workflow and existing domain analytics/sidebar permissions. Log: `scratch/recommendation-navigation-tests.log`. Coverage includes the exact four-item Super Admin Marketplace sidebar, preserved Dashboard entry, list/detail/activity access, title/breadcrumb/subtitle, manager sidebar retention, program scope, filters, direct-action denial, research authorization and read-only record counts. `manage.py check` passed; scoped whitespace checks passed.

To repeat the new integration test from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_bundle_monitoring.BundleMonitoringTests.test_recommendation_navigation_is_dashboard_led_for_super_admin_only --keepdb --noinput
```

Manual check at `http://127.0.0.1:8000/admin-dashboard/`: sign in as Super Admin, confirm the four Marketplace sidebar items, and follow View Recommendations. Verify the existing filters, details and research permissions. With an authorized Marketplace Admin test account, confirm Bundle Suggestions remains. Do not change a real user's role or add live orders merely to test navigation.

If an old sidebar item remains, reload the HTML and verify that Django is rendering `partials/admin_sidebar.html`. CSS cache changes are unnecessary. If the listing returns 403, inspect existing permissions rather than removing its view guard; hiding a link does not authorize a route. If the panel is empty, keep its honest no-data state—this edit does not generate recommendations.

Safe practice exercise: locate `View Recommendations` at `backend/templates/dashboard/partials/system_overview_summary.html:127` and follow the `bundle_monitor_list` name to `backend/core/core/urls.py:126`. Confirm that it still resolves to `suggestion_list`; no URL edit is needed. Repeat the focused test to verify navigation without changing application records.

### 8. Remaining limitations

This is a server-rendered navigation/copy update. No actual browser click-through, screenshots, responsive pixel checks or phone runtime verification was performed; the tests verify rendered HTML, authorization and existing route responses. No full repository test-suite pass or deployment is claimed. Existing page-load-only Dashboard recommendation refresh behavior is retained.

Current global web typography (October 22, 2026): Inter now applies to these web cards through the shared `web_typography.html` include, local `InterVariable.woff2` and `web_typography.css`. SugarPie remains the wordmark only. Older Montserrat/Roboto descriptions below are historical. See [the current global typography and Marketplace Overview report](dashboard-marketplace-design.md) for exact files, functions/data flow, tests, troubleshooting and safe exercises. Flutter typography is unchanged.

Current Super Admin read-path update (October 22, 2026): `dashboard_bundle_suggestions(user, limit)` now reads saved live recommendation rows and activity directly for Super Admin; it no longer invokes Apriori while rendering that page. Existing explicit refresh persists live results; Marketplace Admin and Analytics keep their calculator. Inputs/outputs, exact files, verification, troubleshooting and safe practice exercise are documented in [the current KPI implementation report](dashboard-kpi-refinement.md). Older statements below about Super Admin GET mining are superseded.

## Latest dashboard refinement: Bundle Recommendations & Activity (October 22, 2026)

This is the current Super Admin dashboard layout. The foundation report below still explains the monitoring models, seller workflow and research page; its earlier dashboard-card descriptions and line numbers are historical where they differ from this section.

### 1. Cause / Reason

The dashboard still displayed Suggested Product Bundles, Frequently Bought Together and Cross-Selling Opportunities in the recommendations area. The user requested exactly two cards: **Suggested Product Bundles** and **Recommendation Activity**, under **BUNDLE RECOMMENDATIONS & ACTIVITY**. Existing persisted recommendations, seller choices, bundle provenance and activity audits can supply accurate activity monitoring without another model or mining implementation.

### 2. Exact Files Changed / Current Lines and Anchors

| File, approximate current line | Anchor | Change and reason |
| --- | --- | --- |
| `backend/templates/dashboard/partials/system_overview_summary.html:122` | `marketplaceRecommendationsTitle` | Renames the section and includes exactly the suggested and activity cards. Removes only the Super Admin frequent/cross-sell includes. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html:1` | `bundleSuggestions` | Requested description, package-search icon/empty copy, existing View All/detail routes, maximum existing preview limit, seller and response. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_activity.html:1` | `recommendationActivity` | New second card with View Activity, actual totals or separate empty/error states. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_activity_metrics.html:1` | `bundle-activity-metrics` | Shared two-column totals for the card and activity page. Zero is rendered as zero whenever metrics are shown. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_state_icon.html:1` | `bundle-state-icon` | Lightweight decorative package-search/clipboard SVG icons, hidden from screen readers because the headings already explain the state. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:2` | `.bundle-dashboard-card` | Scoped Montserrat, compact copy, icons, real-pair content and two-column activity totals. Narrow screens stack images/text; existing Marketplace cards retain their styles. |
| `backend/core/modules/marketplace/services/bundle_monitoring.py:32` | `status_records_for` | Shared existing choice/bundle-status annotation, reused by the listing and new summary. Exists checks prevent multiplying recommendations by their child records. |
| Same service, `:40` | `linked_bundles_for` | Reads real bundle products with an explicit source recommendation and matching seller. Counts actual products, not bundle-created audit entries. |
| Same service, `:46` | `activity_events_for` | Matches successful highlight/create/choice audit events to authorized stable recommendation IDs, or the exact legacy seller/product pair. No product-name matching and no duplicated query joins. |
| Same service, `:61` | `activity_summary` | Real sent/awaiting/created/dismissed totals and activity detection; generation alone is not a seller action. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:44` | Super Admin `activity_summary` call | Adds the activity presentation to the existing dashboard context. A retrieval failure is flagged separately, with no fabricated zero totals. |
| `backend/core/modules/marketplace/bundle_monitoring_views.py:28`, `:34` | `annotated`, `recommendation_activity` | Reuses the shared status helper and adds the read-only, permission-scoped activity page with 20 events per page. |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html:24` | `mode == 'activity'` | Uses the existing shell, summary partial, real event table, actor/timestamp and stable-ID View Details links. |
| `backend/core/core/urls.py:127` | `bundle_monitor_activity` | Adds GET `/admin-bundle-suggestions/activity/` before the integer-ID routes. Existing list/detail/history/research routes remain. |
| `backend/templates/dashboard/pages/admin_dashboard.html:24`, around `:600` | feature CSS / global script branch | CSS cache key is `20261022-activity`; Super Admin uses the existing image-fallback script and no longer ships obsolete frequent/cross-sell dialogs. Marketplace branches retain the existing script/dialogs. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:17`; monitoring page `:10` | shared CSS URL | Updates the shared stylesheet cache version only. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:204` | generation/activity/counting/legacy/error tests | Verifies source records, no duplicate totals, scoped legacy events, independent errors and authorization. Optional render fixtures include the activity route. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:273`, `:333` | Super Admin dashboard tests | Exactly two cards, correct copy/links, populated real-record activity, independent retrieval failure, no metrics/old dialogs; Analytics retains Frequently Bought Together. |
| This guide and `CAMPUSHUB_CONTEXT.md` top note | latest dashboard policy | Current functions/data flow, verification, troubleshooting and safe practice. |

### 3. Changes Made

The Super Admin area now has exactly two consistent white cards. Suggested Product Bundles uses the requested description and empty-state wording, keeps View All available when empty, and links qualifying saved results to their existing detail page. Recommendation Activity shows real status totals in a compact two-column layout when activity exists. Otherwise, it displays the requested clipboard icon, No Recommendation Activity Yet and its explanatory copy. Retrieval errors show Retry and an error message instead of the empty state or invented zero values.

Frequently Bought Together and Cross-Selling Opportunities are removed from this dashboard only. Their algorithms, existing APIs, history and Marketplace Admin UI remain. Reports > Analytics > Marketplace already has Frequently Bought Together, and it was left there. Super Admin still has no Send to Seller, Highlight or Create Bundle control in this area.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

```text
Existing dashboard_bundle_suggestions(Super Admin)
  -> existing persisted eligible preview
  -> activity_summary(user)
       -> permission-scoped recommendations + saved/dismissed choices
       -> actual source-linked bundle products
       -> existing successful recommendation audit events
  -> two server-rendered cards

View Activity GET
  -> same authorization / summary
  -> existing matching AccountActivity records, newest first
  -> paginated table + existing stable-ID Suggestion Details route
```

`status_records_for(user)` returns one row per authorized recommendation with existence flags for an actual linked bundle and a current dismissal. `activity_summary(user)` returns a dictionary containing `summary`, `has_activity` and `error`. Its counters mean:

- **Sent to Sellers:** distinct recommendation records with a recorded workspace highlight timestamp. This remains a workspace fact, not a claim of push/email delivery; the visible footnote says so.
- **Awaiting Response:** highlighted recommendations with no linked bundle and no current dismissal.
- **Bundles Created:** actual source-linked bundle Product records belonging to the recommendation's seller. Two real submissions count as two bundles; duplicate audit entries do not create extra bundles.
- **Dismissed:** current dismissed seller choices with no linked bundle, consistent with the existing Bundle Created response taking precedence.

`activity_events_for(user)` accepts only existing successful highlight, bundle-submission and seller-choice events. PostgreSQL JSON matching correlates a stable recommendation ID without unsafe numeric casts. Older choice events are correlated using both the exact seller account reference and ordered product IDs. The query does not combine product-name similarities or infer notifications from generation. A generation event alone therefore leaves the activity empty; a genuine saved/removed choice may produce recorded activity with zero values in the four final-status counters.

Annotated example:

```python
summary['created'] = linked_bundles_for(records).count()
# Count actual bundle products. Repeated BUNDLE_CREATED audit entries cannot inflate the total.
```

The activity page maps its current event page back to the authorized recommendation records, then uses their current product/seller identity and the audit's recorded actor/time. It writes no event on a view. Existing per-suggestion history remains available through Suggestion Details.

### 5. Backend / API Behavior

New route: `bundle_monitor_activity`, GET `/admin-bundle-suggestions/activity/`. It uses the existing analytics/admin access check, both-product academic scope, private/no-store responses and read-only method restriction. Regular users are denied; Marketplace Admin gets only their authorized scope; Super Admin can monitor system-wide. The existing `bundle_monitor_list` and `bundle_monitor_detail` routes are reused by View All and View Details.

The live recommendation API, association thresholds, research-only dataset isolation, seller actions and approval/inventory/payment behavior are unchanged. Technical association metrics are absent from the Super Admin dashboard. Errors in the activity query are independent of the suggestion preview; one working card can still display its actual results when the other cannot be retrieved.

### 6. Database / Migration Impact

No model, migration, database-setting or business-record changes. This update only reads the existing `BundleRecommendation`, `SellerBundleSuggestion`, Product and AccountActivity records. No sample transactions, notifications or bundles were added to the application database. The previous foundation migration 0045 remains the prerequisite; there is no new migration to apply and no new worker/scheduler to run. Development remains local; Kamatera was not changed.

### 7. Tests Performed / Troubleshooting / Safe Practice

**117 scoped Django tests passed** across monitoring, bundle suggestions, mobile seller workspace, bundles and marketplace dashboard reports. Log: `scratch/bundle-activity-regression.log`. Two targeted render/navigation-fixture tests also passed after adding the activity-page snapshots (`scratch/bundle-activity-render.log`). After making the activity error page's Retry link return to its own route, its targeted error/authorization test passed again (`scratch/bundle-activity-retry.log`). Tests cover exactly two Super Admin cards, populated/empty/error states, actual-count semantics, duplicate audit entries, generated-only records, legacy saved actions, permissions/scopes, stable links and preserved Marketplace Analytics/Seller behavior. Django system checks were clean, migration drift reported No changes detected, JavaScript syntax and targeted tracked-file whitespace checks passed.

Browser review used clearly labelled isolated TestCase HTML snapshots in `scratch/bundle-activity-preview/`. Empty and populated cards were visually inspected. View Activity was clicked through to actual test-record events, then View Details reached the corresponding suggestion. View All points to the existing listing route and is also asserted by Django tests. Natural desktop, 1024px, 768px and 390px layouts were checked. At the latter three sizes, document client/scroll widths respectively matched at 1009/1009, 753/753 and 375/375 pixels (excluding the vertical scrollbar). Narrow populated suggestions stack their images/text; activity totals stay in two columns. These are isolated preview checks, not a claim of a live authenticated browser session or formal accessibility certification.

Troubleshooting:

- Old title, three cards or stale styling: Ctrl+F5 and verify `bundle_suggestions.css?v=20261022-activity`. Deploy the changed dashboard include and matching stylesheet together.
- No activity after generation: expected. Generation is not sharing or a seller action. Check actual highlight timestamps, source-linked bundles, existing choices and audits.
- Activity totals differ from the number of event rows: expected when there are multiple real actions on one recommendation. Status counters come from unique source records and actual bundles, not the number of audit log entries.
- Activity unavailable: use Retry and inspect database/application logs. Do not replace a retrieval error with the empty state or static zero totals.
- Unexpectedly empty live suggestions: existing singleton-checkout limitation remains; synthetic CSV results are never a fallback.

Safe practice: open the local Super Admin dashboard, verify the new heading and exactly two cards, then use View All and View Activity and return with browser Back. Do not create test orders to populate the real dashboard. With no real activity, the honest empty message is the correct result; the isolated fixture tests exercise the populated view safely.

### 8. Remaining Limitations

Current checkout still lacks verified multi-product baskets, live persistence refresh remains explicit, and workspace highlighting does not prove external push/email delivery. Existing legacy activity without a matching saved recommendation cannot safely appear in the new recommendation-specific activity table; it remains in the original account activity logs. No new inference or backfill was performed. A full-project suite, live authenticated browser flow, deployed-server check and formal accessibility audit were not run.

## Monitoring foundation implementation: October 22, 2026

This section supersedes the older dashboard-only descriptions below. Open **Marketplace > Bundle Suggestions**, or **Dashboard > Suggested Product Bundles > View All**. The local URL is `http://127.0.0.1:8000/admin-bundle-suggestions/`. Sign in with an authorized administrator account first.

### 1. Cause / Reason

The existing calculator already mines product-pair association rules and keeps live orders separate from the synthetic CSV. However, recommendations were calculated on demand with no stored generation date, delivery fact, or source link to a seller-created bundle. The existing `SellerBundleSuggestion` only stores a mobile seller's saved/dismissed choice and can be removed by that seller; it cannot safely serve as an immutable generation record for all sellers.

The requested monitoring screens therefore require one new persistent live recommendation model. Existing seller choices, product/bundle records, association calculations, academic permissions, and account activity logs remain the sources for their respective facts. There is no second mining implementation or second bundle editor.

### 2. Exact Files Changed / Current Lines and Anchors

Paths are relative to the project root. Line numbers identify this update and can move in later work; use the anchor to find the function again.

| File and current line | Nearby anchor | What changed |
| --- | --- | --- |
| `backend/core/api/models.py:136` | `Product.source_recommendation` | Optional protected source link from an actual product to a persisted recommendation. |
| `backend/core/api/models.py:990` | `BundleRecommendation` | Ordered unique product pair, original generation timestamp/metrics, last verification, current flag, workspace highlight timestamp and actor. No synthetic source is accepted by its generation service. |
| `backend/core/api/migrations/0045_bundle_recommendation_monitoring.py:11` | `Migration` | Creates that table and adds the nullable product link. Reuses `AccountActivity`; no new history or research table. |
| `backend/core/modules/marketplace/services/bundle_monitoring.py:16` | `is_super_monitor` / `recommendations_for` | Canonical Super Admin recognition, scoped reads of both products, shared presentation. |
| Same service, `:39` | `refresh_live` | Explicit, transaction-locked generation using the existing live calculator. Retains stable IDs and original timestamps across refreshes. Records one generation event per new pair. |
| Same service, `:69`, `:83`, `:109` | `eligible_pair`, `presentation`, `history_for` | Reuses component eligibility, actual seller response and bundle links; reads existing activity history without inventing events. |
| Same service, `:121`, `:141` | `highlight`, `link_created_bundle` | Scoped Marketplace Admin workspace highlight; provenance link during the existing validated mobile bundle submission. |
| `backend/core/modules/marketplace/bundle_monitoring_views.py:46` | `suggestion_list` | Real summary counts, search, Program/Major/seller/response/date filters, 20-row pagination. |
| Same views file, `:122`, `:140` | `suggestion_detail`, `suggestion_highlight` | Stable-ID detail, response, created-bundle and history views; explicit POST/CSRF enforcement on highlighting. |
| Same views file, `:152`, `:180` | `research`, `run_research` | Super Admin-only CSV preview and directional rules, independent search/pagination and research-only cache refresh. |
| `backend/core/core/urls.py:126` | `admin-bundle-suggestions/` | List, research, research-run, stable-ID detail, highlight and section routes. |
| `backend/core/modules/marketplace/management/commands/refresh_bundle_recommendations.py:7` | `Command` | Explicit live refresh command requiring an existing authorized Super Admin actor. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:40` | `dashboard_bundle_suggestions` | Maximum three persisted eligible preview rows, using safe product-only JSON fields. Existing frequent/cross-sell calculations remain shared. |
| Same service, around `:229` | synthetic `directional_rows` | Research table can show both qualifying rule directions from the same calculator. |
| `backend/core/api/views.py:852` | `link_created_bundle` | Links a successful mobile bundle submission to the matching persisted live suggestion inside its existing transaction. |
| `backend/core/modules/marketplace/mobile_seller_views.py:35` | `live_suggestions` | Prioritizes highlighted own pairs only while they still qualify under the existing live calculator. |
| `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html:1` | monitoring page | Shared navigation, Montserrat, compact summary/filter table, details/response/bundles/history and separate research tabs. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_monitor_pagination.html:1` | result pages | Preserves current filters in Previous/Next links. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html:1` | `data-monitor-preview` | Dashboard preview and ordinary links to full list/details; requested honest empty state. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_monitoring.css:1` | `.bm-page` | Scoped navy/white surfaces, neutral text/borders, 12px panels, responsive table overflow and narrow-header fix. No gradients. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_monitoring.js:1` | image error / submit / `updateMajors` | Image fallback, loading feedback, browser-back restoration and applicable-major filtering. Search remains ordinary server GET filtering. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_suggestions.js:6` | `suggestedPanel` | Existing retry renderer leaves the persistent preview alone; frequent/cross-sell retry remains unchanged. |
| `backend/templates/partials/admin_sidebar.html:33` | Marketplace group / `Bundle Suggestions` | Adds one permission-aware child link using the existing sidebar architecture and active state. |
| `backend/templates/dashboard/pages/admin_dashboard.html:24`; Marketplace dashboard template `:17` | shared feature asset URLs | Cache versions changed to `20261022-monitor`. No unrelated dashboard rearrangement. |
| `backend/core/modules/marketplace/test_bundle_monitoring.py:1` | `BundleMonitoringTests` | Real isolated ORM tests for source separation, permissions, filters, history, response and bundle provenance. |
| `backend/core/api/test_mobile_seller_workspace.py:191` | bundle submission test | Verifies the existing mobile submission writes its real source link and one activity event. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:297`, around `:470` | dashboard assertions / isolated generation | Replaces obsolete modal expectations with stable-ID monitoring links and explicit test-only generation. |
| `backend/core/modules/reports/test_dashboard_marketplace.py:170` | `anchors` | Updates a stale assertion to the existing low-stock position beneath top-selling products. No application layout was moved for this assertion. |
| This guide; `CAMPUSHUB_CONTEXT.md` top note | current monitoring policy | Current behavior, commands, verification, troubleshooting, limitations and practice. |

### 3. Changes Made

- Dashboard preview: two persisted rows on the existing Super Admin dashboard, at most three when another caller requests that limit. View All is available even when empty so research remains discoverable. Each populated row uses real names/photos, seller, seller Program/Major, response and View Details. No association metrics or operational buttons appear here.
- Full list: compact summary values from saved live records; product/seller/ID search; supported academic, seller, response and generated-date filters; paginated product-pair table.
- Detail navigation: separate Details, Seller Response, Created Bundles and History views. Product prices remain individual prices. Only actual linked bundle records supply a bundle price, status, components, images and creation date.
- Super Admin monitoring is read-only. No recommendation edit/delete/approve, seller response submission, send/highlight or create-bundle action is available to that role, including direct HTTP POST attempts.
- Marketplace Admin can highlight a current qualifying mobile seller pair within their permitted scope, with the existing seller-management permission. This prioritizes it in that seller's workspace. It does not claim external notification delivery.
- Research is a separate Super Admin-only page with Dataset Preview and Apriori Results. It reads the existing synthetic CSV, displays its actual columns and directional rules, and never imports research records into production tables.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

Live flow:

```text
Explicit refresh command + authorized actor
  -> existing build_bundle_suggestions(actor, source='live')
  -> shared calculate_market_basket and current seller/product checks
  -> unique BundleRecommendation record + existing AccountActivity generation event
  -> read-only dashboard/list/detail views

Marketplace Admin highlight POST
  -> permission + both-product scope + fresh live qualification checks
  -> recorded workspace highlight + existing AccountActivity event
  -> seller's already-qualifying own suggestion moves to the front

Existing validated seller bundle submission
  -> existing recipe and approval workflow
  -> actual Product.source_recommendation link + existing AccountActivity event
  -> monitoring displays the real bundle and its real price/status
```

`refresh_live(actor)` accepts only a live result and uses a PostgreSQL advisory transaction lock to serialize explicit refreshes across administrators. It returns created/current/eligible-order counts. Existing pair IDs, generation dates and initial rule evidence remain stable. A successful refresh marks absent pairs non-current without deleting history; an analysis failure rolls back and preserves existing records. It never combines separate single-product orders into fabricated baskets.

`presentation(row)` returns display values from the linked products, their actual seller, existing saved/dismissed choices and explicitly linked bundles. A saved choice is not treated as bundle creation. Bundle Created takes precedence when an actual linked bundle exists; otherwise a recorded dismissal is Dismissed, a highlighted pair without a final response is Awaiting Response, and an unhighlighted unanswered pair is Not Applicable. Dates come only from the relevant stored records.

`history_for(row)` reads existing marketplace activity events matching the recommendation ID, plus existing seller-choice audit events matching that exact seller/pair. It does not add events on a page view. No earlier sent/viewed/dismissed/generated timestamps are inferred from product creation dates or current page load time.

Research flow:

```text
Existing synthetic_order_items.csv
  -> existing validated analyze_synthetic / shared calculate_market_basket
  -> actual dataset metadata and paginated CSV records / directional rule results
  -> research-only UI with disclosure
```

The existing core implementation calculates two-product association rules using support, confidence and lift. This update does not introduce a trained predictive model or a generalized larger-itemset Apriori implementation. The user-facing Apriori label refers to the existing association-analysis feature. Thresholds remain configurable through `CAMPUSHUB_BUNDLE_MIN_SUPPORT`, `CAMPUSHUB_BUNDLE_MIN_CONFIDENCE` and `CAMPUSHUB_BUNDLE_MIN_LIFT`. Only the research table displays them or the calculated metrics.

Annotated example:

```python
product.source_recommendation = row  # Source is an explicit saved live record, not a matching name.
product.save(update_fields=['source_recommendation', 'updated_at'])
# Product approval, actual bundle price and component inventory still belong to their existing services.
```

### 5. Backend / API Behavior

The existing `/api/marketplace/bundle-suggestions/` stays live-only and GET-only. Existing normal dashboard payloads still omit research metrics. The new list/detail/history routes are also GET-only; the research-run and Marketplace Admin highlight actions require POST and CSRF. Authentication, active administrator access, analytics permission and both-product academic scope are checked in Django. Research additionally requires canonical global Super Admin access. A scoped-out ID returns 404, an unauthorized role returns 403, and database/dataset failures display separate 503 states.

Delivery status and response are independent. **Sent to Sellers currently counts recorded workspace highlights**, as stated directly below the summary. No push/email receipt, seller-view event or historical bundle provenance is invented. Existing seller save/dismiss/remove semantics, Cash on Pickup, approval, inventory and prices are unchanged. Multiple actual bundle submissions may reference one source recommendation; the summary counts suggestions with at least one bundle, not duplicate submissions.

### 6. Database / Migration Impact

Migration `api.0045_bundle_recommendation_monitoring` was applied to **local** `campushub` at `127.0.0.1:5432`. It adds one live recommendation table and one nullable FK on Product. No research table, OrderItem schema, checkout conversion or data import is included. Existing activity and seller-choice tables are reused. Referenced products/recommendations are protected from destructive cascading deletion; normal product deletion was already disabled in favor of archiving.

Before applying it, the existing backup service created `backend/backups/campushub_postgres_20261022_000657.sql` and its verification JSON: 361,487 bytes, 42 table definitions/data sections, pg_dump exit 0 and completion marker verified. SHA256: `c8e5a612effcc9afb30f80de753c3d86c69d9f1bbfa4f5f065887cf3acc9086e`. The backup has not been restore-tested and does not include media files. No Kamatera configuration or deployment was changed.

For another checkout/environment, after its own backup, run from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py migrate api 0045 --noinput
.\venv\Scripts\python.exe manage.py check
```

When genuine multi-product checkout history is available, an authorized operator can explicitly refresh live records:

```powershell
.\venv\Scripts\python.exe manage.py refresh_bundle_recommendations --actor YOUR_EXISTING_SUPER_ADMIN_USERNAME
```

Replace the username with an existing authorized account. Do not create a dummy account or orders to populate the normal dashboard. No scheduler or worker was installed/started. Browser GETs do not invoke this command.

### 7. Tests Performed / Troubleshooting / Safe Practice

Actual final scoped run: **111 Django tests passed**, covering `modules.marketplace.test_bundle_monitoring`, `modules.marketplace.test_bundle_suggestions`, `api.test_mobile_seller_workspace`, `modules.marketplace.test_bundles` and `modules.reports.test_dashboard_marketplace`. Evidence: `scratch/bundle-monitoring-regression.log`. Django system checks reported no issues; migration drift check reported No changes detected. Both changed JavaScript files passed `node --check`; targeted tracked-file whitespace checks passed.

Initial test-only failures were corrected: the new fixture initially attempted to recreate seeded BSIT/BFPT programs; old dashboard tests expected modal actions and the superseded low-stock position. Fixtures now reuse seeded programs and assertions match the requested persistent monitoring navigation/current unchanged layout. One initial regression command named a nonexistent test module; the final run uses the actual `api.test_mobile_seller_workspace` module. No failed run is represented as passing.

Browser inspection used explicitly labelled isolated TestCase render snapshots under `scratch/bundle-monitoring-preview/`, not production fixture inserts. List-to-detail and research-tab links were clicked; details and research layouts were visually inspected. Viewports 1265px, 1024px, 768px, 390px and 320px were inspected, with the narrow header overflow found and fixed. After sidebar transitions settled, the 390px viewport measured document client/scroll widths both 375px, and the 320px viewport measured both 305px (excluding the vertical scrollbar). Tables retain their own horizontal scroll when necessary. The Program control was changed to BSIT and the Major control disappeared. A complete formal accessibility audit, live authenticated browser workflow and physical-device verification were not performed; functional requests/filters/roles were exercised by Django tests.

The research file measured 1,000 distinct transactions, 2,027 item rows and 150 distinct seller/product identities. These are synthetic file metadata, not real marketplace KPIs. After migration/tests, the local application database contained **0 persisted recommendations**, **15 products**, and **1 order**. Test records were not inserted into that application database.

Troubleshooting:

- Missing table or `source_recommendation_id` column: apply migration 0045 to the database used by that Django process; do not switch DATABASE_URL merely to hide the error.
- Old dashboard modal or stale styles: Ctrl+F5 and check that shared feature assets use `20261022-monitor`; deploy the matching templates/JS together.
- Empty normal suggestions: inspect actual checkout capture first. Research results are never a live fallback. More singleton orders alone cannot establish co-purchases.
- Missing response/bundle/history: only recorded choices, audits and explicit provenance links can populate those views. A similarly named manual bundle is not proof that a suggestion caused it.
- Research unavailable: check the existing configured CSV path and required columns/data-origin tags. The UI shows only its filename, never the server's private absolute path.
- Marketplace Admin cannot highlight: check active role, analytics and seller-management permissions, both product scopes, approved seller access, mobile workspace support and fresh live qualification. Super Admin is intentionally denied this action.

Safe learning exercise: sign in locally, open Bundle Suggestions, search for a nonexistent product and verify No matching suggestions, then Reset. Open View Dataset & Analysis and switch the two research views; verify the synthetic disclosure remains visible and ordinary marketplace totals do not change. This exercise does not require creating orders, modifying thresholds or submitting seller actions.

### 8. Remaining Limitations

- Current checkout stores one product per order and lacks verified shared multi-product OrderItems. Consequently, normal live associations remain honestly empty. This task preserves that generation boundary; a future checkout-capture change is needed before genuine live pairs can be generated.
- Live persistence refresh is explicit through the management command; it is not automatically scheduled. Monitoring reads never create recommendations or generation history.
- External notification delivery and seller-view tracking are not implemented. Highlighting is supported for existing mobile seller workspaces only; it is not presented as a web-seller or push/email delivery success.
- Old manually created bundles are not retrospectively linked, and old unknown generation/sent dates are not backfilled. Original metrics are internal snapshots; normal monitoring deliberately hides them.
- Only local migration/development was changed. Production deployment requires its own backup, migration and matching code/static deployment. No full-project suite, complete browser/a11y certification or real phone test is claimed.

## Historical dashboard-only notes

Updated October 16, 2026. Current policy: Super Admin has Suggested Product Bundles restored beside the KPIs, plus Frequently Bought Together and Cross-Sell Suggestions beside Sales Overview. Marketplace Admin keeps its two-card layout and its Marketplace Overview heading above Sales Overview. All recommendations remain live-only, with no synthetic fallback or visible research metrics. Older two-card-only Super Admin and synthetic-display descriptions below are historical.

## Super Admin Suggested Product Bundles restored (October 16, 2026)

### 1. Cause / Reason

The user explicitly requested restoring Suggested Product Bundles on Super Admin while keeping Frequently Bought Together and Cross-Sell Suggestions. Marketplace Admin retains its existing two recommendation cards. Restoration reuses the live qualifying rows already available; it does not restore the former CSV demonstration.

### 2. Exact Files Changed / Current Lines and Anchors

| File / approximate line | Anchor | Change |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:63` | `suggested_rows` / `suggested_has_more` | Adds the small preview and conditional View All flag to the existing product-only presentation. No second mining query or new calculation. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html:1` | `bundleSuggestions` | Restored card with real product images/placeholders, names, seller, View and conditional View All. |
| `backend/templates/dashboard/partials/system_overview_summary.html:122` | bundle card include | Restores Suggested Product Bundles beside eight Super Admin KPIs, under the existing recommendations heading. |
| `backend/templates/dashboard/partials/marketplace_analytics.html:9` | `dashboard-recommendations-stack` | Keeps Frequently Bought Together and Cross-Sell Suggestions in a compact stack beside Sales Overview. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_pair.html:1` | `view_action` | Optional Suggested row style and read-only View action. The other two modes remain informational. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_empty.html:1` | `kind == 'suggested'` | Restores the honest bundle empty/helper message and its separate error copy. Other card messages remain. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_dialogs.html:3` | `global_dashboard` / `bundleReviewDialog` | Restores a Super Admin-only, read-only product-pair dialog; no badges or metrics. Shared View All remains. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_suggestions.js:6`, `:26`, `:39`, `:62` | optional suggested panel, `rowsFor`, `pair`, `review` | Adds the optional mode, correct result ordering and View/dialog rendering. Existing live-only Retry updates every present panel. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:2`, `:15`, `:32`, `:39` | recommendation stack, suggested row, helper, product dialog | Natural-height stacked cards, existing navy/white View buttons, phone stacking and two separate product images in View. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27`, `:600`; `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:17`, `:240` | feature asset versions | Shared assets now use `20261016-super-bundles-restored`; the Marketplace template receives no third-card include. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | existing presentation, Super Admin rendering and populated-fixture tests | Checks restored previews/actions and all three Super Admin cards, while preserving Marketplace's absence assertions. |
| This guide / final matching entry in `CAMPUSHUB_CONTEXT.md` | restored-card policy | Current explanation, verification, debugging and learning exercise. |

### 3. Changes Made

Suggested Product Bundles is back at the top right of Super Admin. Frequently Bought Together and Cross-Sell Suggestions remain, stacked beside Sales Overview. The stack aligns its contents to the top so empty cards do not stretch to the chart's height. Marketplace Admin still has its existing two cards and Sales heading.

A qualifying suggested pair has two actual product photos or the existing missing-photo placeholders, its combined name, seller and View. View opens separate Product A/Product B cards, the Suggested Bundle combination and seller, with Close only. View All uses the existing shared numbered-page dialog and allows read-only View from its suggested rows. No Create Bundle or Send to Seller action is added.

With no qualifying live rows, show No bundle suggestions available yet. and Suggestions will appear after sufficient completed marketplace transactions are recorded. Failed analysis has its own error/Retry state. No synthetic badges, sellers, products or technical metrics return.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

`existing live analysis -> product-only public rows -> suggested preview -> Super Admin-only card -> View / View All`

`recommendation_presentation(result, limit)` already receives the qualified live rows in the original strongest-rule ranking. It now supplies `suggested_rows = rows[:limit]` and a derived `suggested_has_more` Boolean. This uses the same result as both existing panels. Frequently Bought Together keeps its separate frequency ordering; Cross-Sell keeps its ordered rules and Inventory target checks. No algorithm is copied.

The Super Admin summary includes the restored card; the Marketplace layout never includes it. JavaScript detects which panels are present. `rowsFor('suggested')` uses the existing public `rows` array. `pair(row, 'suggested')` creates the optional View control, while `review(row)` fills the read-only dialog from that same selected row. Both server templates and JavaScript use escaped/text-only product names, existing photo fallbacks and the current native-dialog focus behavior. Retry uses the existing live-only endpoint and updates all present panels with the same preview limit.

Annotated example:

```python
public['suggested_rows'] = public['rows'][:limit]  # Presentation slice, not new recommendations.
public['suggested_has_more'] = len(public['rows']) > limit
```

### 5. Backend / API Behavior

Only two presentation fields were added. Existing live data eligibility, Product/Seller identity mapping, Apriori calculations, thresholds, public metric-field filtering, URL, permissions, academic scope, GET-only restriction and synthetic-source rejection remain. The card cannot create a live bundle, notify a seller or alter stock/orders/revenue. The CSV remains internal research/test data; no dashboard reads it.

### 6. Database / Migration Impact

No model, schema, dependency, migration or database-write change. No migration command is needed. Deploy the shared CSS/JavaScript and updated templates together, then Ctrl+F5 for `20261016-super-bundles-restored`.

### 7. Tests Performed / Manual Checks / Debugging / Practice

59 focused Django tests passed. After the final layout adjustment, the existing Super Admin empty/placement and populated-renderer tests passed again (two targeted tests). Django reported no system-check issues. The unchanged Marketplace assertions confirm it still lacks Suggested Product Bundles and a per-pair View dialog.

Chrome checks passed for both roles at 1440, 1024, 768 and 390px: three Super Admin versus two Marketplace cards, correct live previews, restored View/Close and nested View from View All, product identities, no technical metrics/badges, existing direction/equal-pair behavior, pagination/Escape/focus, loading/error/Retry and no page overflow. The eight Retry requests all used GET with `source=live`; an injected synthetic response was rejected. An initial harness assertion assumed three preview rows for Super Admin Retry; it was corrected to the existing two-row limit, without changing application limits. Final checks also verify compact empty cards beside the taller Sales chart.

Populated verification reuses the earlier isolated TestCase Product/Seller records and calculated multi-item basket fixture at the missing capture boundary. It is not a production sample or fallback. The live-source fixture remains honestly empty. Final empty desktop, populated card and phone View previews were inspected. JavaScript syntax and targeted whitespace checks passed. Logs: `scratch/dashboard-super-bundles-restored-tests.log`, `scratch/dashboard-super-bundles-restored-layout-tests.log`, `scratch/dashboard-super-bundles-restored-browser.log`; harness/screenshots: `scratch/super-bundles-restored/`.

Manual check: open Super Admin and reload; confirm Suggested Product Bundles beside the KPIs and both other cards beside Sales Overview. With genuine qualifying results, open View, check both products/seller and close; use View All when available. Open Marketplace Admin and confirm its two cards remain. If a title/action is missing or duplicated, check the role-specific includes and current asset version rather than enabling a CSV fallback.

Safe practice: in DevTools, inspect `#bundleSuggestions` and its row ID, then compare that ID with the product-only seed's `rows` list. Temporarily edit only the visible heading, verify data does not change, and reload. Never insert test transactions or change thresholds in production merely to populate the restored card.

### 8. Remaining Limitations

Current checkout still has one product per order, with no verified multi-item OrderItem/shared-basket capture. Real associations therefore remain unavailable under that schema; restoration changes presentation, not checkout history. Physical/deployed-device verification remains manual. A full-project test-suite success is not claimed.

## Marketplace Admin Sales section heading (October 16, 2026)

1. **Cause / Reason:** The user requested Marketplace Overview immediately above Sales Overview in the Marketplace Admin dashboard.
2. **Exact Files Changed:** `backend/templates/dashboard/partials/marketplace_overview_row.html:4`, anchor `marketplaceSalesOverviewTitle`; this guide's current heading note; the final matching entry in `CAMPUSHUB_CONTEXT.md`.
3. **Changes Made:** Added one H2 inside the existing Sales column. It reuses `marketplace-section-title`, which supplies the established Montserrat weight, navy color and 12px bottom spacing. The existing KPI-area heading keeps its separate ID.
4. **How It Works:** The existing Marketplace dashboard view supplies context, includes `marketplace_overview_row.html`, then renders the new static label before the original Sales Overview partial. No function, query, input/output or chart data changed. Example: changing the H2's visible text changes the label; changing `sales_overview` data changes the original chart/card values independently. Reusing the existing class avoids a second typography rule.
5. **Backend / API Behavior:** Existing live analytics, recommendation calculations, permissions, routes and filtering are unchanged. The heading is inside the existing Marketplace-specific branch; Super Admin uses its own analytics partial.
6. **Database / Migration Impact:** No schema or migration change; no command needed. Reload the dashboard to receive the updated template.
7. **Tests / Debugging / Practice:** The existing `BundleSuggestionAccessTests.test_marketplace_two_rows_reuse_live_orders_and_live_totals` passed (one test), with no Django system-check issues. A parser check of that actual rendered response confirmed a unique H2 with the exact text, existing class, correct Sales-column parent and ordering before `salesOverviewTitle`. Log: `scratch/marketplace-overview-header-test.log`; fixture: `scratch/marketplace-overview-header/dashboard.html`. Manual check: open Marketplace Admin, confirm the heading sits above Sales Overview and retains the normal section style. If missing, deploy the updated partial and reload the page. Safe exercise: temporarily change only this heading's text in DevTools, verify the chart data stays the same, then reload to restore.
8. **Remaining Limitations:** No new browser/device run or full-suite rerun for this small template-only label addition. The prior two-card browser evidence below belongs to that earlier implementation.

## Current Frequently Bought Together / Cross-Sell Suggestions (October 16, 2026)

### 1. Cause / Reason

The previous two cards presented equal product pairs in both positions and discarded reverse directions before any Cross-Sell UI could use them. That loses the distinction between A + B and the qualifying rule A -> B. The user selected exactly two cards and requested separate empty messages, informational results, short previews, conditional View All, existing CampusHub styling and no research metrics in the normal interface.

The existing Apriori calculator already emits directional rules. Reusing those rules avoids a second algorithm, inferred reverse suggestions or a new recommendation database. The real-order source limitation described below remains; no sample transactions were inserted to fill the cards.

### 2. Exact Files Changed / Current Lines and Anchors

| File / approximate line | Nearby anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:39` | `dashboard_bundle_suggestions` | One live analysis, then shared presentation for both cards; previews remain three per Marketplace card and two per Super Admin card. |
| Same service, line 44 | `recommendation_presentation` | New product-field whitelist and server-side ranking. Omits Support, Confidence, Lift and thresholds from card JSON and the normal API. Independent preview/has-more values for each relationship type. Rejects synthetic presentation input. |
| Same service, line 79 | `_recommendation_rows(... directional=False)` | Equal pairs collapse reverse duplicates. Directional mode preserves actual source/target order and distinct IDs, without automatically adding a reverse rule. Existing same-seller checks remain. |
| Same service, line 101 | `analyze_live` | Reuses one existing calculation and actual Product/Seller catalog. Adds directional results and checks target availability through Inventory. Bundle recipes are prefetched for qualified bundle targets. |
| `backend/core/modules/marketplace/bundle_suggestion_views.py:20` | `recommendation_presentation(...)` | Existing live-only, protected GET endpoint now shares the same public-data whitelist. Internal analysis retains full metrics. |
| `backend/core/modules/marketplace/templates/marketplace/partials/frequently_bought_together.html:1` | `frequentlyBoughtTogether` | Equal-pair preview and independent View All; exact frequent-pair empty state. |
| `backend/core/modules/marketplace/templates/marketplace/partials/cross_sell_suggestions.html:1` | `crossSellSuggestions` | New directional card, Recommended with, its own preview and View All state. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html` | removed obsolete partial | Removes the replaced Suggested Product Bundles card. All former includes now use one of the two selected cards. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_pair.html:1` | `directional` | Shared row uses + with equal product names or an arrow with source/Recommended with/target. Removes per-row View actions; rows are informational. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_empty.html:1` | `kind` | Exact one-line empty/error text per card; removes the former long helper paragraph. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_dialogs.html:3` | `bundleAllDialog` | Keeps only the shared View All dialog with Close and numbered pages. Removes the obsolete per-pair Review/View dialog. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_suggestions.js:6` | `panels` / `isLiveResult` | Two current cards; validates live-only product arrays. No browser sorting/calculation using research metric fields. |
| Same JavaScript, lines 39 / 51 / 63 / 83 | `pair`, `renderPanels`, `renderAll`, `load` | Renders the correct relationship, uses the selected list for View All, preserves pagination/loading/Retry, and never introduces seller mutation actions. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:20` onwards | `.bundle-relation-label` / `.bundle-pair--cross-sell` | Stacked equal names versus the directional label and decorative gold arrow. Keeps compact navy/white rows, responsive images and visible gold keyboard focus; removes obsolete review-product/footer styles. |
| `backend/templates/dashboard/partials/system_overview_summary.html:122` | recommendation include | Super Admin: Frequently Bought Together occupies the previous Suggested Product Bundles position beside eight KPIs. Existing section header remains. |
| `backend/templates/dashboard/partials/marketplace_analytics.html:9` | recommendation include | Super Admin: Cross-Sell Suggestions occupies the second card position beside Sales Overview. |
| `backend/templates/dashboard/partials/marketplace_overview_row.html:4` and `:8` | two existing row includes | Marketplace Admin: Sales/Frequently Bought Together, then Product Performance/Cross-Sell Suggestions. Other layout/content remains. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27`, `:600`; `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:17`, `:240` | feature assets | Both CSS/JS versions updated to `20261016-frequent-cross-sell`. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:52`, `:71`, `:403`, `:418` | directional/presentation/availability/populated-fixture tests | Verifies orientation and qualification, public-data filtering, independent limits, existing inventory behavior and both renderer branches. Existing source/RBAC tests updated for the current UI. |
| This guide / `CAMPUSHUB_CONTEXT.md`, final two-card entry | current policy | Beginner explanation, actual evidence, debugging, safe practice and remaining limitations. |

### 3. Changes Made

The two cards show actual product names, their current stored photos or the existing honest placeholder, and the actual seller. Frequently Bought Together presents equal pairs with +. Cross-Sell Suggestions presents a source product, a decorative right arrow, Recommended with and the target product. Both reuse the existing cards, type, borders and navy/gold/white palette. The visible directional label explains the relationship without relying on gold color or an icon alone; the symbols are hidden from assistive technology and equal names include an off-screen "and" separator for screen readers.

Rows have no Create Bundle, Send to Seller, Accept, Decline or per-row View/Review action. View All appears only when that card has additional results, and opens only that relationship list in the existing shared native dialog. No graph, extra KPI or new page was added. Both empty messages match the request exactly:

- No frequently bought together products yet.
- No cross-sell suggestions available yet.

Loading and failures remain separate from an honest empty result. Each card has its own error text and the existing read-only Retry action. The old Suggested Product Bundles card and its per-pair dialog are removed from these dashboards. Existing manual bundle creation elsewhere is unchanged.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

`eligible completed/paid orders -> actual Product/Seller catalog -> existing calculate_market_basket once -> same-seller qualified rules -> equal-pair and directional projections -> product-only presentation -> two shared card templates / View All`

`_recommendation_rows` receives calculated rules and the catalog that belongs to that source. With `directional=False`, its identity sorts the two product IDs and collapses reverse duplicates, retaining the strongest existing rule for that equal pair. With `directional=True`, it keeps the ordered source/target IDs. A reverse rule appears only if the calculator itself returned it after applying the configured thresholds. Synthetic identities never resolve to live Product records.

`analyze_live(user, limits)` still filters Completed + Paid + positive quantities using canonical sales and order access helpers. Product approval/archive state, linked approved active seller access and the admin's Program/Major scope remain. It builds both views from one mining result. Current cross-sell targets must pass the existing Inventory status helper: Out of Stock and Expired targets are removed. Low Stock targets remain eligible. Variant and bundle availability stay in Inventory; bundle component relations are prefetched. Frequently Bought Together is historical/informational, so an existing equal pair is not erased merely because its current target stock changed.

`recommendation_presentation(result, limit)` accepts only live analysis. It sorts equal pairs using the already-calculated metrics on the server, retains directional ordering, selects small previews and derives separate View All flags. Its output contains actual names, product IDs/photos, seller identity and UI state, not research metric/threshold fields. The raw internal result is not mutated.

Annotated contract example:

```python
internal = build_bundle_suggestions(user, source='live')  # Full qualified research fields remain here.
public = recommendation_presentation(internal, limit=3)  # Product-only rows, ranked on the server.
# public['frequent_results'] is the full equal-pair list for View All.
# public['directional_rows'] is the full ordered rule list for Cross-Sell View All.
# public['frequent_rows'] / public['cross_sell_rows'] are the small server previews.
```

The template `bundle_pair.html` and JavaScript `pair(row, kind)` produce equivalent informational rows. `renderPanels()` slices each list independently. `renderAll()` uses the selected mode, title and numbered page; it does not reverse or invent a rule. `load()` refreshes both panels through the existing live-only GET and rejects non-live or incompatible responses. Native dialog keyboard focus and Escape behavior remain.

### 5. Backend / API Behavior

The existing URL, authentication, Marketplace/Super Admin visibility, analytics permission, academic scope, GET-only restriction and private/no-store behavior remain. The endpoint still rejects `source=synthetic` or unknown sources with HTTP 400 and writes nothing. It now returns the same product-only presentation used by dashboard seeds. Support, Confidence, Lift, threshold values and research-only fields no longer need to reach the browser; direct internal analysis still contains them for evaluation. Existing basic response metadata such as eligible counts remains available but is not rendered by the cards.

The original CSV and its explicit internal research/testing functions are unchanged. Its SHA256 remains `a768c0d31a671e3bd30ed907300aa027a749a05be8ee000ee677efc35538415d`. No synthetic seller/product mapping, fallback, notification, order, stock, revenue, real bundle creation or seller recommendation write was introduced.

The current schema still has one product per MarketplaceOrder and no verified OrderItem/shared multi-product checkout identity. The adapter therefore produces singleton baskets and correctly has no real co-purchase rules. It never combines separate orders by buyer/date, expands predefined bundles into organic purchases or trusts legacy item-name snapshots as OrderItems. This UI change does not solve missing checkout capture by fabricating groups.

### 6. Database / Migration Impact

No model, schema, migration or dependency changes. No migration command is required. Deploy the changed templates, Python and static assets together and Ctrl+F5 to load `20261016-frequent-cross-sell`. The API's public payload intentionally no longer contains research metrics/thresholds; any research script that used the UI endpoint should call the existing internal analysis helper instead.

### 7. Tests Performed / Manual Checks / Debugging / Practice

Actual verification:

- **59 focused Django tests passed**: `modules.marketplace.test_bundle_suggestions` and `modules.reports.test_dashboard_marketplace`. The first run exposed two old test assertions expecting the removed synthetic disclosure field in the public API; those were corrected to verify absence, then all 59 passed. No production-code failure was hidden by weakening a security/data assertion.
- Tests verify a qualifying A -> B and B -> A can coexist, reverse duplicates collapse only for equal pairs, a stricter configured confidence allows only the qualifying direction, cross-seller pairs stay excluded, raw backend metrics remain intact, public JSON omits them, and each mode has its own preview/has-more behavior.
- Existing source isolation, real-catalog/photo/seller mapping, permissions, approved/active eligibility, unchanged live stock/totals, singleton/bundle non-expansion and bounded query checks still pass. A stock test removes an unavailable cross-sell target while retaining its historical equal pair.
- **Chrome checks passed** for both roles at 1440, 1024, 768 and 390px: exactly two cards, requested empty copy, server and JavaScript +/arrow rows, distinct labels, product placeholders, no metric keys/text or synthetic UI, no unsupported row actions, independent View All lists, numbered cross-sell pagination, Escape/focus restoration and no page horizontal overflow. Failed Retry remains an error; an injected synthetic response is rejected; successful live-test and empty-live retries render the correct current format. All four network requests were GET with `source=live`.
- Populated-state verification uses actual isolated Django test Product/Seller/Inventory records with associations calculated from explicitly isolated multi-item basket fixtures at the missing capture boundary. These fixtures are never loaded by the application or inserted into production. They verify formatters, stock checks and UI branches; they do **not** prove today's checkout saves multi-item orders. Normal live-source fixtures exercise the honest empty state.
- Desktop equal-pair cards, phone directional cards, live empty state and the Cross-Sell View All dialog were visually inspected. JavaScript syntax and targeted Git whitespace checks passed. Django system checks reported no issues. No full-project/physical/deployed-device test claim is made.

Evidence: `scratch/dashboard-frequent-cross-sell-tests.log`, `scratch/dashboard-frequent-cross-sell-browser.log`, `scratch/frequent-cross-sell/check.cjs` and the empty/card/dialog screenshots in that scratch folder. These are local verification artifacts, not application data sources.

Manual check:

1. Reload both admin dashboards. Confirm exactly Frequently Bought Together and Cross-Sell Suggestions; no third Suggested Product Bundles card or synthetic badge. Verify their separate empty messages when genuine co-purchase data is absent.
2. In an isolated populated renderer test, confirm equal names use + and directional names use an arrow plus Recommended with. Photos must come from the selected real Product record or the existing placeholder; seller must match the actual owner.
3. When enough qualifying results exist, open each View All. Confirm the correct title/list and page through results; close with Escape and verify focus returns to that card's View All.
4. Inspect the normal API/seed: source must be live; research metric/threshold keys must be absent. Internal `build_bundle_suggestions` results must still retain their calculations. Do not use a synthetic API source to fill a live card.
5. Review actual checkout persistence before expecting real pairs. More singleton orders or more units of one product cannot create evidence of two different products in one transaction.

Troubleshooting:

- Old title or missing card: deploy all three layout include changes and remove the obsolete card partial; verify one `frequentlyBoughtTogether` ID and one `crossSellSuggestions` ID per page. Do not add a third duplicate include.
- Loading error after deployment: update backend and frontend together. The client expects the current `frequent_results` and `directional_rows` product-only arrays; stale responses are rejected rather than treated as synthetic/live fallbacks.
- Cross-sell direction reversed: trace `product_a_id` as source and `product_b_id` as target through the calculator, ordered formatter, image order and names. Do not sort a directional ID pair or create a reverse rule in JavaScript.
- One card has more results than the other: expected. Equal pairs collapse reverse duplicates; directional results may contain both qualifying orientations, and unavailable targets can be removed. Each card needs its own View All limit.
- Empty live cards: inspect eligible Completed/Paid records and actual multi-item checkout identity. Current schema has none; this is a confirmed structural limitation, not evidence that a threshold should be reduced or fake rows added.

Safe practice exercise: run `test_equal_pair_deduplication_does_not_erase_cross_sell_direction` in the isolated Django test suite. Compare the two directional IDs with the one equal-pair ID, then inspect the companion presentation test to see how technical fields are omitted without changing the internal result. Do not edit production thresholds/data. Verify the normal dashboard remains live-only and empty rather than acquiring test products.

### 8. Remaining Limitations

Genuine multi-item checkout/OrderItem capture is still absent, so current real transactions cannot generate these associations. The live cards correctly remain empty until a real capture workflow exists. Populated test fixtures validate UI and relationship handling only; they do not represent production recommendations. Existing manual bundle creation and mobile/seller workflows remain unchanged. Physical/deployed-device checks remain manual.

---

## Previous live-only Suggested Product Bundles (October 16, 2026; card replaced)

### 1. Cause / Reason

The normal dashboards called a helper whose default source was synthetic; Retry explicitly requested that same source. The JSON seed and View dialogs therefore contained CSV recommendations even after technical metrics were hidden. Changing only the badge would leave the underlying synthetic dependency intact.

Inspection confirmed that the current `MarketplaceOrder` at `backend/core/api/models.py:768` stores one `product` foreign key and a unique `order_code` per sellable-product order. The checkout at `backend/core/api/views.py:1822` creates one such row. There is no OrderItem model or durable shared multi-product checkout identity. The existing `order_items()` presentation helper at `services/orders.py:114` reads display snapshots; those are not verified item-owner relations. Predefined bundle components are recipes, not separately purchased organic items.

Consequently, this change connects the live eligible records to the existing Apriori calculation and shows the requested empty state. It does not invent baskets by buyer/date, combine order codes, infer product IDs from names, or create an unrelated checkout schema migration.

### 2. Exact Files Changed / Current Lines and Anchors

| File / approximate line | Nearby code anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:39` | `dashboard_bundle_suggestions` | Explicitly requests live data for both existing dashboard consumers. Preview limits and internal frequent-pair sorting remain. |
| Same service, line 61 | `_recommendation_rows` | Extracts the existing result formatter, retaining qualification, reverse-pair deduplication and same-seller checks. Each source uses its own catalog; live IDs never resolve against CSV IDs. |
| Same service, line 82 | `analyze_live` | Reuses completed/paid order scope, existing approved-seller logic, Product foreign keys and the original Apriori calculator. Loads products/sellers in one related query. |
| Same service, line 184 | `build_bundle_suggestions` | Defaults to live. Explicit internal `source='synthetic'` remains research-only. Invalid sources fail rather than silently selecting CSV. Errors do not fall back. |
| `backend/core/modules/marketplace/bundle_suggestion_views.py:17` | source validation | Existing protected GET endpoint defaults to live and rejects synthetic/unknown source requests with HTTP 400. URL and role/permission gates remain. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html:2` | `bundle-panel-heading` | Removes the SYNTHETIC badge and includes the shared honest empty state. |
| `backend/core/modules/marketplace/templates/marketplace/partials/frequently_bought_together.html:2` | `bundle-panel-heading` | Same live-only presentation; no alternate CSV-backed card remains. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_dialogs.html:4` and `:13` | dialog headers | Removes badges from both View and View All. Product-only row/dialog design remains ready for qualified live results. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_empty.html:1` | `bundle-empty` | New shared two-line empty message. API errors have their own honest error text. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_suggestions.js:9` | `isLiveResult` | Rejects non-live seeds/responses. Retry around line 103 requests `?source=live`; the controller never renders an unexpected synthetic response. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:27` | `.bundle-empty-detail` | Adds compact helper text and removes unused synthetic-badge styling. Existing navy/gold/white layout remains. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` and `:600` | feature assets | Cache version `20261016-live-recommendations`. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:17` and `:240` | feature assets | Same version for Marketplace Admin. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:119` onwards | live API/dashboard and research tests | Updates prior CSV/UI expectations and tests source isolation, eligibility, actual catalog mapping, safe empty/error states and retained research calculations. |
| `docs/suggested-product-bundles.md:5`; `CAMPUSHUB_CONTEXT.md`, final live-only entry | current policy | Cause, functions/data flow, source boundaries, verification, debugging and learning exercise. |

The Reports dashboard views already use `dashboard_bundle_suggestions`, so their existing calls at `modules/reports/views.py:554` and `:1386` now receive live data without duplicate view logic. Those views, the models, original CSV, original calculator and detailed Analytics template were not changed in this step.

Local verification artifacts: `scratch/live-bundle-suggestions/check.cjs`, `scratch/dashboard-live-recommendations-tests.log`, `scratch/dashboard-live-recommendations-catalog-test.log`, `scratch/dashboard-live-recommendations-browser.log`, and the role/width screenshots in `scratch/live-bundle-suggestions/`. Fixtures are isolated test responses, not production records.

### 3. Changes Made

Removed every synthetic badge from the recommendation cards/dialogs and removed the normal dashboard's CSV call path, including hidden JSON seeds and Retry. Synthetic Seller labels and CSV product rows are no longer returned to the normal UI. The original CSV and its explicit research functions remain available.

Both recommendation cards now show these exact sentences when no genuine qualifying pairs exist:

> No bundle suggestions available yet.
>
> Suggestions will appear after sufficient completed marketplace transactions are recorded.

Empty cards show no invented product rows, View results or View All. On an analysis failure, show Unable to load bundle suggestions with the existing JavaScript Retry action. No fake zero count replaces a failed API analysis. The existing View renderer still contains only two product images/placeholders, product names/combination and real seller text; metrics remain hidden.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

Current live path:

`real MarketplaceOrder -> valid_sales_queryset + admin_order_queryset -> approved current Product + approved active seller -> actual purchased Product identity -> calculate_market_basket -> qualified same-seller result formatter -> dashboard context / protected live API -> shared product-only cards`

`analyze_live(user, limits)` takes the requesting administrator and the existing configured Support/Confidence/Lift thresholds. It returns calculated rows, eligible transaction count, multi-item count, sufficiency and derived preview/count metadata. It reuses `valid_sales_queryset` for Completed + Paid + positive quantity and `admin_order_queryset` for permissions and academic scope. Products must still be approved and unarchived; existing `_approved_seller_ids(user)` requires a linked approved, unsuspended SellerRequest and an active, unsuspended seller account. No new seller approval rule/store is created.

Product names and images come from the actual `order.product` relation and `Product.get_image_list()`. Seller ID and display name come from `Product.seller`, using the account's full name or recorded username. The existing seller approval relation establishes seller access; no account type or seller identity is guessed from a CSV code, text label or unrelated mobile account ID.

The query uses `select_related('product', 'product__seller')`; the test confirms two data queries after Django permission caching, rather than one query per order. An unordered product pair is kept only once and only when both actual product owners match. The original strongest directional rule and metric calculations are preserved.

Important schema limit: each current order contributes exactly one purchased product identity. Quantity 10 is ten units of one product, not ten different basket items. A predefined bundle contributes its bundle product identity, not its recipe components. Legacy `customization.items` snapshots are skipped because they do not establish verified OrderItem relations. Null legacy order codes do not combine purchases; each persisted order remains its own transaction.

Annotated example from the live adapter:

```python
key = str(product.pk)                     # Real Product foreign-key identity.
transactions.append([(key, product.name)])  # One sellable item in this stored order.
# Never group two orders just because their buyer or date matches.
```

`calculate_market_basket` still calculates Support, Confidence and Lift and applies configured thresholds. With only singleton baskets, its multi-item requirement is unmet and it returns no rules. More current single-product rows alone cannot solve that structural limitation. Genuine multi-item checkout capture would need a separate coordinated checkout/OrderItem change before real pair recommendations can appear. No completed historical orders were rewritten here.

### 5. Backend / API Behavior

`GET /api/marketplace/bundle-suggestions/` and `?source=live` return live results only. The existing authenticated Marketplace/Super Admin, administrator access and analytics permission checks remain. Normal users and Facilities Admin remain denied. A synthetic or unknown source parameter returns HTTP 400 before any CSV analysis; POST remains HTTP 405. Responses retain private/no-store caching.

Research is explicit internal code only, for example in a Django shell:

```python
from modules.marketplace.services.bundle_suggestions import DATASET, analyze_synthetic, thresholds
evaluation = analyze_synthetic(DATASET, thresholds())  # Reads the original CSV in memory.
research_rules = evaluation['rows']                    # Retains support/confidence/lift.
```

This does not insert products, notify sellers or create bundles. The CSV checksum remains `a768c0d31a671e3bd30ed907300aa027a749a05be8ee000ee677efc35538415d`. Its S01-S05/P01-P30 identities remain entirely separate from live catalog/account IDs. Live data is not cached using the CSV cache, so order/payment/catalog changes are reflected on the next analysis. All recommendation reads remain read-only.

No dates or chart-grouping controls were added. The recommendation helper keeps its existing all-history behavior and remains independent of Sales Overview grouping. Revenue, inventory, orders, seller performance and real bundle creation were not changed.

### 6. Database / Migration Impact

No model or migration changes, no dependency installation and no production data writes. No migration command is required. Ctrl+F5 loads `20261016-live-recommendations` assets after deploying the changed templates/static files through the existing process. This update intentionally does not add an OrderItem table or alter checkout/payment/stock workflows.

### 7. Tests Performed / Manual Checks / Debugging / Practice

Actual verification for this step:

- **54 focused Django tests passed** in `modules.marketplace.test_bundle_suggestions` plus `modules.reports.test_dashboard_marketplace`. After adding the explicit catalog/photo/seller mapping assertion, **that additional test passed separately**: 55 distinct focused tests passed across the two runs. Django reported no system-check issues. Logs are listed above.
- Tests verify default-live API data, rejected synthetic/unknown sources, preserved GET-only/role/scope gates, no CSV calls from dashboards/Analytics, missing CSV independence, Completed/Paid eligibility, excluded pending/cancelled/unpaid/out-of-scope records, approved/unarchived products, active approved seller access, current product names/photos and actual seller identities, unchanged live sales/stock, honest error/empty states, bounded query count and retained explicit research metrics/cache/threshold behavior.
- Separate real single-product orders, quantities, null codes, bundle recipes and unverified legacy item snapshots do not generate false co-purchase pairs. Test data is confined to the Django test database; no live records were seeded.
- **Chrome checks passed** for both admin roles at 1440, 1024, 768 and 390px: live-only JSON seed, exact two-line empty copy, no synthetic badge/labels/pairs, no technical metric text, no fake View/View All results, preserved KPI/header/layout and no page overflow. Network-failure Retry remains an error, an intentionally injected synthetic research response is rejected without rendering its products, and a successful live Retry restores the honest empty state. All three requests were GET with `source=live`.
- Browser fixtures came from actual isolated Django responses. Desktop and phone screenshots were visually inspected. JavaScript syntax and targeted whitespace checks were checked. No full-project suite or physical-device deployment verification is claimed.

Manual check:

1. Open both authorized dashboards and Ctrl+F5. Confirm no synthetic badge, CSV seller labels, CSV product images/names or View results. Confirm the exact empty sentences when no valid live pairs exist.
2. Inspect the recommendation JSON seed or a Retry request in DevTools: source must be `live`; it must not contain synthetic rows/disclosure. Technical metric keys may remain backend fields but must not be rendered in the interface.
3. Request the existing endpoint with `?source=synthetic` while authenticated. Expect HTTP 400, not research rows. Check normal-user/Facilities restrictions separately without changing grants.
4. Change a test order between Completed/Paid and an ineligible status in an isolated test database. Its eligible count should change on the next analysis. No synthetic fallback should appear.
5. Do not expect a pair from repeated single-product orders, even for the same buyer/date. Verify actual persisted multi-item checkout support before investigating recommendation thresholds.

Troubleshooting:

- Old badges/pairs persist: confirm both Django templates and versioned feature JavaScript were deployed. A stale page may still call `source=synthetic`; the updated endpoint intentionally rejects it. Reload the updated page; do not re-enable the research source.
- Empty despite completed orders: inspect payment status, positive quantity, Product foreign key/current approval/archive state, existing seller approval/account state and requesting admin scope. Then inspect whether a genuine multi-item transaction exists; current checkout does not store one.
- No seller/product match: follow the actual Product.seller foreign key and linked SellerRequest. Never map S01/P01 or guess by matching names/overlapping mobile IDs.
- Load error: inspect the live API response and database/configuration error. Counts become unavailable on analysis failure; Retry must never invoke CSV.
- Missing image in a future qualified result: inspect `Product.get_image_list()` and the configured media URL. Keep the existing honest placeholder when no real photo exists.

Safe practice exercise: trace an existing order from its `product_id` to `Product.seller_id` using read-only inspection, then locate the corresponding linked approved SellerRequest. Compare the live API's eligible count with that order's status/payment eligibility. In an isolated test, change only payment status and confirm the count changes while synthetic analysis is never called. Run the focused test command to verify; do not edit historical production orders or thresholds to manufacture a suggestion.

### 8. Remaining Limitations

The current checkout has no verified multi-item OrderItem relation/shared basket identity. Real qualified pairs therefore cannot arise from its singleton transactions; adding more singleton orders alone does not enable Apriori pair generation. A genuine multi-item checkout data model and capture workflow is separate future work, not a migration concealed in this UI/source change. The View design and source-specific real catalog formatter are preserved, but no successful real pair end-to-end claim is made under the current schema. Physical/deployed-device verification remains manual.

---

## Previous actionable recommendations (October 16, 2026; synthetic UI superseded)

### 1. Cause / Reason

The shared dashboard cards, recommendation dialog and detailed Analytics table exposed research metrics to normal users. The user now wants those values reserved for Apriori qualification and research evaluation. Both the server-rendered HTML and the JavaScript-generated HTML needed changing: hiding the initial labels alone would let View All, pagination or Retry display them again.

Confirmed inventory: Super Admin and Marketplace Admin use the same recommendation partials and controller. A repository search found no separate Apriori component in a seller dashboard or Flutter screens. Existing manual seller bundle creation is a separate feature; synthetic results must not create live bundles or seller notifications.

### 2. Exact Files Changed / Current Lines and Anchors

Paths are relative to the project root. Line numbers describe this update; anchors are more durable.

| File / approximate line | Nearby code anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_pair.html:1` | `bundle-pair` | Removes the metric definition list; each pair shows two images/placeholders, dynamic product names, seller and View. |
| `backend/core/modules/marketplace/templates/marketplace/partials/frequently_bought_together.html:8` | include `bundle_pair.html` | Reuses the same actionable row, including View, without a support-only variant. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_dialogs.html:4` | `bundleReviewTitle` / `bundleReviewCombination` | Removes dialog metrics; displays Suggested Product Bundle, separate product cards, their combination, seller and SYNTHETIC. Existing dialog IDs remain compatible. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_suggestions.js:32` | `pair(row)` | Builds product/seller/View rows only; removed metric-formatting and metric-rendering helpers. |
| Same JavaScript, line 43 | `review(row)` | Populates product cards and Suggested Bundle text from the selected calculated result. No metric values are rendered. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:12` | `.bundle-pair` / `.bundle-pair-footer` | Removes obsolete metric styles, puts View beside the image area on desktop, and retains the existing stacked phone layout. No new palette or page redesign. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html:172` | Frequently Bought Together | Removes Support, Confidence and Lift columns from the existing recommendation table. Keeps its dynamic Product A and Product B columns and existing source. |
| `backend/templates/dashboard/pages/admin_dashboard.html:27` and `:600` | feature stylesheet / script | Cache versions updated to `20261016-actionable-recommendations`. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:17` and `:240` | feature stylesheet / script | Same cache versions for Marketplace Admin. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:115` | `test_api_get_is_readonly_and_does_not_affect_live_sales` | Confirms research metric keys remain in calculated API results. Existing dashboard tests around lines 168/207 now check View and absence of visible metric markup. |
| Same test file, line 242 | `test_analytics_recommendation_table_displays_products_without_technical_metrics` | Exercises the populated Analytics table with actual mined CSV pairs, checks names remain and metric headings disappear. |
| `docs/suggested-product-bundles.md:1`; `CAMPUSHUB_CONTEXT.md`, final actionable-recommendations entry | Current policy | Documents the change, preserved calculations, debugging, verification and limitations. |

Local verification artifacts: `scratch/bundle-suggestions/actionable-recommendations-check.cjs`, `scratch/dashboard-actionable-recommendations-focused-tests.log`, `scratch/dashboard-actionable-recommendations-tests.log`, `scratch/dashboard-actionable-recommendations-browser.log` and the `actionable-recommendations-*.png` screenshots. These are test/preview evidence, not application data.

### 3. Changes Made

Suggested Product Bundles and Frequently Bought Together now show the two product images or honest missing-image placeholders, the product combination, seller and View. Both retain the small SYNTHETIC badge. View opens the existing dialog with Product A, Product B, their names, Suggested Bundle combination and seller. The dialog has only Close; no synthetic seller action was introduced.

View All and numbered pages use the same simplified row. Loading, empty results, dataset errors and Retry retain existing behavior. The detailed Analytics recommendation table shows only the two product names. Its existing live source is unchanged and is not falsely labelled synthetic. Dashboard layout, KPIs and unrelated analytics remain unchanged by this update.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

The existing flow is:

`original synthetic CSV -> build_bundle_suggestions -> calculate_market_basket -> configured qualification thresholds -> dashboard context / protected API -> product-only HTML`

The unchanged `calculate_market_basket` calculates Support, Confidence and Lift. The unchanged `build_bundle_suggestions` validates the synthetic source, selects qualifying same-seller pairs, normalizes reverse pairs and returns cached calculated rows. `dashboard_bundle_suggestions` supplies the existing preview limits. Metric keys stay in the result for ranking and research evaluation.

Server rendering passes each calculated `row` into `bundle_pair.html`. After interaction, JavaScript `pair(row)` accepts that same result shape and returns an `article` DOM element containing product images, names, seller and View. `review(row)` fills the existing dialog from the selected row. `renderAll()` applies the existing pagination and calls `pair`; `load()` fetches the protected synthetic endpoint and calls `renderPanels()` after success or failure. These functions do not save records.

Annotated example from the controller:

```js
// Input: the selected qualified result, including its retained research fields.
byId('bundleReviewCombination').textContent =
    `Suggested Bundle: ${row.product_a} + ${row.product_b}`;
// Output: user-visible product names only. textContent also keeps names as text.
// No support/confidence/lift property is rendered into this interface.
```

`rowsFor('frequent')` still sorts internally using the calculated metrics, as before. Sorting with a value does not require displaying that value. Keeping the existing result shape avoids a second mining helper, duplicate qualification logic or changes to research output.

### 5. Backend / API Behavior

No Apriori service, CSV, configured threshold, API route or permission changes were made for this update. The protected GET-only `/api/marketplace/bundle-suggestions/?source=synthetic` still returns Support, Confidence and Lift in its JSON for evaluation. The existing non-visible JSON seed also retains calculated fields. This is a presentation change, not a claim that research fields are secret or removed from network responses.

Both dashboards continue to use the same calculated result set with their existing preview limits and ordering. The SHA256 of the source CSV remains `a768c0d31a671e3bd30ed907300aa027a749a05be8ee000ee677efc35538415d`. No S01-S05/P01-P30 mapping, order/inventory/revenue mutation, seller notification or live bundle creation occurs. No additional seller Create Bundle/Dismiss feature was found or added.

### 6. Database / Migration Impact

No models, schema, dependencies or database changes. No migration or management command is needed. Reload the page with Ctrl+F5 to load the versioned CSS/JavaScript; deploy the changed templates and static files using the existing deployment process.

### 7. Tests Performed / Manual Checks / Debugging / Practice

Actual results for this update:

- **47 focused Django tests passed:** `modules.marketplace.test_bundle_suggestions` and `modules.reports.test_dashboard_marketplace`. Includes calculated metrics/thresholds, synthetic isolation, API permissions/read-only behavior, both dashboard renderings and the new populated Analytics-table check. Log: `scratch/dashboard-actionable-recommendations-focused-tests.log`.
- **Broader run: 64 of 65 passed.** Adding `modules.reports.tests.MarketplaceAnalyticsTests` exposed one unrelated failure: `test_marketplace_admin_cannot_open_user_monitoring_even_if_permission_is_added` expects HTTP 403 but gets 200. The same test fails when run alone. Inspection confirms the existing `accounts/views.py:1195` monitoring view explicitly allows scoped Marketplace Admin monitoring, with support grants in migration `accounts/0027_marketplace_user_support.py`. The test expectation conflicts with that existing workflow; neither was changed here. Logs: `scratch/dashboard-actionable-recommendations-tests.log` and `scratch/dashboard-unrelated-monitoring-access-test.log`.
- **Chrome checks passed** for both admin roles at 1440, 1024, 768 and 390px: actual CSV pair identities/order, two photos/placeholders per row, no visible technical labels/metrics, View/dialog/Escape/focus restoration, View All from both cards, numbered pagination, loading, empty/error states, failed/successful Retry, SYNTHETIC badges, preserved layout and contained overflow. Retry and pagination do not reintroduce metrics. Pagination uses 579 actual CSV-derived pairs at isolated lower test thresholds; production configuration is unchanged.
- Existing Super Admin Refresh still updates the captured real test-domain summaries while preserving isolated synthetic pairs. Browser fixtures come from Django test responses and captured API payloads, not a production login.
- Desktop card, phone card and View dialog screenshots were visually inspected. JavaScript syntax and targeted Git whitespace checks passed. Django reported no system-check issues.

Manual checks:

1. Open each authorized admin dashboard. Verify Suggested Product Bundles and Frequently Bought Together show combinations, seller and View, with SYNTHETIC inside each card header.
2. Open View from both cards and from View All. Confirm the correct two names/combination and seller, no visible Support, Confidence, Lift or thresholds, and no live seller actions. Press Escape and confirm focus returns to View.
3. When more results exist, use numbered pages and repeat the visibility check. Refresh or retry a failed load; metrics must remain absent after JavaScript rebuilds the rows.
4. Open detailed Marketplace Analytics. When genuine association results exist, its recommendation table should contain only Product A and Product B. An honest empty state remains valid when live multi-product checkout data is unavailable.
5. In browser Network tools, inspect an authorized recommendation GET response: research metric keys should still exist, and the source should remain synthetic. Do not POST synthetic IDs to live product/bundle endpoints.

Troubleshooting:

- Metrics remain after deployment: confirm both template and JavaScript changes were deployed; reload the `20261016-actionable-recommendations` assets. Inspect the card DOM rather than the JSON script, which intentionally retains backend fields.
- Metrics return only after View All/Retry: inspect `pair(row)` and `review(row)` in the loaded JavaScript. Do not remove fields or change thresholds in the backend to fix a renderer.
- Images show the product placeholder: the original CSV has no image column. This is expected. Do not borrow real catalog photos by matching synthetic IDs.
- No recommendations: check the dataset path, validation/error state and genuinely qualifying results. Do not insert fixed fallback product pairs.
- The broader monitoring test fails: compare its old deny expectation with the existing scoped monitoring implementation. This update does not settle or modify unrelated RBAC requirements.

Safe practice exercise: open View and inspect `#bundleReviewCombination` in DevTools. Temporarily edit only its visible text, observe that the dialog changes while the Network result still contains its calculated metrics, then reload to restore the actual product names. Verify the next View uses the selected calculated pair again. This demonstrates the difference between presentation and qualification without modifying records or thresholds.

### 8. Remaining Limitations

The synthetic CSV contains no product photos, so existing placeholders are used. No separate seller recommendation UI or recommendation-specific Create Bundle/Dismiss workflow was found. Physical/deployed-device verification remains manual; browser checks used isolated fixtures. One older User Monitoring access expectation remains inconsistent with the current scoped support workflow, as described above. No claim is made that the complete project test suite passes.

---

## Latest recommendations header and card swap (October 15, 2026)

### 1. Cause / Reason

The user requests a small MARKETPLACE RECOMMENDATIONS section label above the Super Admin right-hand bundle card, matching SYSTEM OVERVIEW exactly, and asks to swap the Top Selling Products / Product Categories area with Frequently Bought Together. This updates hierarchy and placement only. The removed Marketplace Decision Support heading remains removed.

### 2. Exact Files Changed / Current Anchors

| File / approximate line | Anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/pages/admin_dashboard.html:46` | `dashboard-overview-controls` | Keeps the existing global date controls in a shared row above the two section headers. Non-global header behavior is preserved. CSS versions updated in the head. |
| `backend/templates/dashboard/partials/system_overview_summary.html:4` | `systemOverviewTitle` | Left column now owns its existing System Overview header. |
| Same partial, line 121 | `marketplaceRecommendationsTitle` | Adds MARKETPLACE RECOMMENDATIONS above the right bundle card, using the same `dashboard-section-heading--first` wrapper and H2 styles. |
| `backend/templates/dashboard/partials/marketplace_analytics.html:10` | `show_bundle_suggestions` | Places existing Frequently Bought Together beside Sales Overview for authorized Super Admin. Original product stack is the permission-safe fallback. |
| `backend/templates/dashboard/partials/marketplace_product_stack.html:1` | `dashboard-marketplace-side` | Extracts the original live top-selling/category markup once; all IDs and renderer hooks are preserved. |
| `backend/templates/dashboard/partials/marketplace_decision_support.html:1` | `dashboard-product-performance` | Internal filename retained for compatibility; now places the existing live product stack in the former Frequently Bought Together location, before Operations. No visible decision-support heading. |
| `backend/static/components/css/admin_dashboard_summary.css:5` | `.dashboard-overview-controls` | Shared date toolbar alignment. Existing header classes supply typography/spacing/navy color. |
| `backend/static/components/css/admin_marketplace_overview.css:11` | `.dashboard-marketplace-side--relocated` | Relocated live cards use two columns on wide screens, one below 992px, without changing their data. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:7` | removed unused decision-grid selectors | Removes the former lower frequent-pair layout rules, since that card now uses the upper right slot. Marketplace Admin rows remain intact. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:224` | `marketplaceRecommendationsTitle` assertions | Existing rendering test checks the new header, card order and one copy of each live card. |
| This guide / `CAMPUSHUB_CONTEXT.md` | Latest hierarchy entry | Current explanation, evidence, debugging and learning exercise. |

### 3. Changes Made

Super Admin top area: shared date controls, then SYSTEM OVERVIEW over the left eight KPIs and MARKETPLACE RECOMMENDATIONS over the right Suggested Product Bundles card. The two headings use identical existing font family, size, weight, uppercase transform, line height, spacing and navy color. Suggested Product Bundles keeps its title, SYNTHETIC badge, calculated rows and actions.

The next Marketplace Analytics area now has Sales Overview left and Frequently Bought Together right. The original Top Best-Selling Products and Sales by Product Categories cards move into the former lower frequent-pair area, side by side on wide screens and stacked on smaller screens. Marketplace Admin keeps its previously requested layout.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

No application function or backend input/output changed. Existing context -> shared partials -> existing DOM IDs remains the data path. The new `marketplace_product_stack.html` receives the same `dashboard_marketplace` context and optional `relocated=True` layout flag; it does not query or calculate anything. The original markup is included in one position at a time, so there are no duplicate chart IDs or metric lists.

For example, `id="categorySalesCard"` and its data hooks still identify the live category card after moving it. The existing global filter controller finds the same ID anywhere within the dashboard and refreshes it from live data. Frequently Bought Together still receives the separate synthetic CSV result through the existing shared Apriori service. No source data crosses between these renderers.

The global filter stays in the dashboard root with its original ID, URL, events and values. Moving its visual wrapper above both headings allows their top edges and following cards to align without overlapping the date controls.

### 5. Backend / API Behavior

Unchanged CSV, Apriori helper, calculated pairs/metrics, thresholds, preview limits, image placeholders, permissions, API routes and live analytics. Review, View All, Retry and Refresh continue through existing controllers. No mapping of synthetic sellers/products to real accounts or catalog records.

### 6. Database / Migration Impact

No model, database, dependency or migration changes. Refresh with Ctrl+F5 to load `20261015-recommendations-hierarchy` and `20261015-marketplace-card-swap` CSS versions.

### 7. Tests Performed / Debugging / Practice

46 existing Django feature/dashboard tests passed after the placement assertions were updated. Chrome checks passed for both roles at 1440, 1024, 768 and 390px, including identical computed header typography, aligned desktop header positions, eight KPIs/four-by-two on wide screens, actual CSV metrics, exactly one live product/category card, the swapped positions, contained overflow, Review/Escape/focus/View All/pagination/Retry, and the existing Refresh controller. Desktop header, phone layout and relocated live-card screenshots were visually inspected.

Evidence: `scratch/dashboard-recommendations-hierarchy-tests.log`, `scratch/dashboard-recommendations-hierarchy-browser.log`, `scratch/bundle-suggestions/recommendations-hierarchy-check.cjs`, and `recommendations-hierarchy-super-1440.png` / `recommendations-hierarchy-product-cards-1440.png` in that scratch folder. These are isolated Django test fixtures; no production writes. Syntax and targeted whitespace checks passed.

Manual check: reload Super Admin; verify matching section labels and the card title/badge inside the right card; verify Sales/Frequent pairs above the relocated live product cards. Change the global period and check live product/category values refresh, then review a synthetic suggestion. On a narrow screen verify the right recommendation area follows the KPIs and lower live cards stack.

Troubleshooting: mismatched heading style -> inspect that both use the same `dashboard-section-heading dashboard-section-heading--first` wrappers instead of introducing a second font rule. Stale placement -> verify template deployment and new CSS versions, then reload. Missing/duplicate live updates -> check original IDs occur once and that the card partial is not rendered in both fallback and relocated positions. Do not change data calculations to repair layout.

Safe practice: inspect both heading elements in DevTools and compare their computed font size, weight, color and text transform. Temporarily change a margin in DevTools, observe only the spacing change, then reload to restore. Do not rename data-hook IDs when changing visible headings.

### 8. Remaining Limitations

Physical/deployed-device verification remains manual. Browser checks use the existing isolated fixture server, not a live authenticated user session. This is a layout refinement and does not claim a full dashboard design audit.

---

## Previous heading cleanup (October 15, 2026)

1. **Cause / reason:** The user requested removal of the visible Marketplace Decision Support heading.
2. **Exact files / anchors:** `backend/templates/dashboard/partials/marketplace_decision_support.html:1` (`dashboard-decision-support`); `backend/core/modules/marketplace/templates/marketplace/partials/frequently_bought_together.html:4` (`marketplace-synthetic-label`); `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:8` (removed unused `bundle-decision-heading` rule); `backend/core/modules/marketplace/test_bundle_suggestions.py:205` (`test_super_admin_same_data_and_kpi_area_suggestions`); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Removes only the extra heading row. Frequently Bought Together remains, with SYNTHETIC moved into its own card header. Suggested Bundles beside the KPIs is unchanged.
4. **How it works / data flow:** At that stage the outer heading wrapper became a plain div, avoiding a dangling `aria-labelledby` reference; the newer hierarchy update above has since swapped its content. The inner card retains its existing accessible heading. No function, input or output changes: CSV -> existing Apriori helper -> dashboard context -> existing card partials remains the flow.
5. **Backend / API:** Unchanged. Genuine calculated results, permissions and read-only actions are preserved.
6. **Database / migration:** No changes or migration.
7. **Verification / debugging:** The existing Super Admin render/placement test passed (one test). It checks that the heading text and deleted ID are absent while existing cards and computed results remain. Log: `scratch/dashboard-remove-decision-heading-tests.log`. Earlier 46-test/browser results below belong to the preceding functional update, not a rerun for this small cleanup. Manual check: reload Super Admin, find Frequently Bought Together, confirm its SYNTHETIC badge and no extra section heading. If the old text persists, restart a stale Django worker and reload the page. Safe practice: inspect the card's `aria-labelledby` in DevTools and find the matching title ID; do not alter metric data to change a heading.
8. **Remaining limitations:** A fresh browser/device visual run was not needed for this template-only heading change and was not performed.

## Shared Apriori implementation reference

The calculations, permissions and controllers below still apply. Placement descriptions in this older implementation record are superseded by the latest recommendations hierarchy/card-swap section above.

### 1. Cause / Reason

The prior update already calculated genuine CSV results, but placed Super Admin Suggested Product Bundles below Marketplace Analytics. The latest clarification moves that card back to the right of the eight KPIs. Inspection confirmed the displayed pairs, sellers and metrics are calculated; they are retained. There were no manually populated pair/metric fallback arrays to remove. UI/UX Pro Max guidance was used for visible keyboard focus, compact layouts and contained responsive content. No Apriori graphs, source controls, disclosure paragraphs or new seller actions were added.

### 2. Exact Files Changed / Current Lines and Anchors

Paths below are relative to the project root. Lines are approximate and anchors are more durable when files grow.

Latest clarification changed only: `services/bundle_suggestions.py:36` (preview-limit argument), `reports/views.py:1386` (Super Admin limit), `system_overview_summary.html:119` (right aside), `bundle_suggestions.html:4` (badge), `marketplace_decision_support.html:6` (remove duplicate panel), both scoped CSS files, both dashboard CSS cache links, and `test_bundle_suggestions.py:205` (placement assertions). The original CSV, mining function, seller/product handling, API writes policy and JavaScript controller were not changed. The full current feature file inventory follows for context.

| File / line | Nearby anchor | What changed |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:27` | `can_view_bundle_suggestions` | Shares the existing endpoint authorization with dashboard rendering. |
| Same file, line 36 | `dashboard_bundle_suggestions` | One existing CSV result with a presentation limit: three per panel for Marketplace, two per panel for Super Admin; derived View All flag. |
| `backend/core/modules/marketplace/bundle_suggestion_views.py:11` | `bundle_suggestions_api` | Reuses the shared permission guard; GET-only behavior and result shape remain. |
| `backend/core/modules/reports/views.py:538` | `show_bundle_suggestions` | Authorized Marketplace context receives the shared presentation result. |
| Same view, lines 791 / 1386 | `bundle_analysis` | Both role templates use the same helper/result source. Super Admin domain summary context follows at line 1392. |
| `backend/core/modules/reports/dashboard_periods.py:151` | `users = User.objects.aggregate` | Adds enabled-account count to the existing aggregate. |
| Same file, lines 185 / 197 / 286 | `services`, `pending_services`, `services_overview` | Adds service counts to existing Facility/Booking aggregates and exposes read-only domain snapshots. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:17` | `bundle_suggestions.css` | Loads feature assets only when authorized; existing overview partial at line 95, shared dialogs at line 239. |
| `backend/templates/dashboard/partials/marketplace_overview_row.html:2` | `marketplace-insight-grid` | Sales/bundles first row, Product Performance/frequent pairs second row. |
| `backend/templates/dashboard/partials/marketplace_product_performance.html:1` | `productPerformanceTitle` | Existing top-selling/category markup extracted without a second data calculation. |
| `backend/templates/dashboard/pages/admin_dashboard.html:201` | `marketplace_decision_support.html` | Remaining Frequently Bought Together follows analytics, then existing Operations at line 202; domain overviews at line 406; dialogs at line 595. Suggested Bundles is now in the System Overview partial. |
| `backend/templates/dashboard/partials/marketplace_analytics.html:1` | `marketplaceAnalyticsTitle` | Operations include moved to the page so Decision Support fits between the two existing sections. |
| `backend/templates/dashboard/partials/system_overview_summary.html:2` | `dashboard-summary-layout` | Restores the shared dynamic bundle card in a right aside at line 119; eight KPI cards and their existing hooks remain on the left. |
| `backend/static/components/css/admin_dashboard_summary.css:2` | `.dashboard-summary-layout` | Approximately 2:1 KPI/bundle split, four-by-two wide-desktop KPIs, responsive stacking and existing small icon containers. |
| `backend/templates/dashboard/partials/marketplace_decision_support.html:1` | `marketplaceDecisionSupportTitle` | Retains Super Admin Frequently Bought Together below analytics without duplicating Suggested Bundles or displaying an extra section heading. Its two preview pairs sit side by side on wide screens. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html:1` | `bundleSuggestions` | Calculated pair cards, SYNTHETIC badge on both dashboards and conditional View All. |
| Same partial folder, `frequently_bought_together.html:1` | `frequentlyBoughtTogether` | Simpler support-only pair cards. |
| Same folder, `bundle_pair.html:1` | `data-pair-id` | Shared server-rendered row structure, metrics and optional Review. |
| Same folder, `bundle_photo.html:1` | `bundle-photo-placeholder` | Separate image slots, reusing the existing inventory product icon when no image exists. |
| Same folder, `bundle_dialogs.html:1` | `bundleSuggestionsData` | Escaped JSON plus shared native Review and View All dialogs. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_suggestions.js:57` | `review(row)` | Separate product cards and actual metrics, only Close. |
| Same controller, lines 68 / 82 / 102 | `renderPanels`, `renderAll`, `load` | Shared Retry, support sorting, conditional View All and eight-row numbered pages. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:2` | `.marketplace-insight-grid` | Scoped 65/35 placement, compact pair cards, dialogs and breakpoints. |
| `backend/templates/dashboard/partials/domain_overviews.html:1` | `servicesOverviewTitle` | Real service and account snapshots before Recent Activities. |
| `backend/static/components/js/admin_dashboard_filter.js:332` | `for (const group of ...)` | Existing Refresh/global filter response also updates the two current domain snapshots. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:166` | `test_marketplace_two_rows...` | Replaces superseded label-only assertions and checks current layout/data isolation/RBAC/states/API snapshots. |
| This guide / `CAMPUSHUB_CONTEXT.md` | Current two-panel update | Records current behavior, tests, data flow and debugging. |

### 3. Changes Made / Final Placement

Marketplace Admin retains its four real Marketplace Overview KPIs. Immediately below them, desktop uses approximately 65% Sales Overview / 35% Suggested Product Bundles. The next row uses 65% Product Performance / 35% Frequently Bought Together. Existing Attention Required is retained after these rows, followed by Operations, Seller Overview, Recent Orders and Recent Marketplace Activities. Existing marketplace charts remain unchanged. The Apriori panels have a title and small SYNTHETIC badge, without subtitles or source controls.

Super Admin keeps all eight small icon-container KPIs on the left, across four columns/two rows at wide desktop widths. Suggested Product Bundles sits in the right aside with a SYNTHETIC badge, two calculated results and conditional View All. Attention Required and System Status follow. Marketplace Analytics, the existing Frequently Bought Together summary, Operations, Facilities Analytics, Services/User summaries and Recent Activities remain below. Suggested Bundles appears exactly once; the lower section no longer duplicates it.

Marketplace panels show at most three rows; Super Admin panels show at most two. Only the preview limit differs: both roles retain the same complete calculated result set. Suggestions keep the existing qualifying-rule order (Lift, then Confidence, then Support); Frequently Bought Together sorts those same qualifying pairs by descending Support, with deterministic tie breakers. The simpler panel has Support only and no Review action. Suggestions have Support, Confidence, Lift and Review. View All is visible only when more qualifying pairs exist than that role's preview limit, opens a read-only native dialog, and uses the existing eight-row page size and numbered arrow navigation. No new page is created.

Desktop pair rows put two distinct 52px images/placeholders beside product names and seller, with metrics underneath. On phones they stack cleanly. Marketplace rows stack below 1200px; Super Admin's right bundle card moves below all eight KPI cards below 992px. The remaining Frequently Bought Together summary uses two columns on wide screens and stacks below 1200px. Product Performance uses its container width to stack its existing child cards when the narrower left column cannot comfortably fit both. Wide tables retain contained scrolling instead of overflowing the page.

### 4. How It Works / Functions, Inputs, Outputs and Data Flow

`can_view_bundle_suggestions(user)` takes the existing authenticated user and returns a Boolean using the same allowed roles, administrator-access check and analytics permission formerly written in the endpoint. Unauthorized dashboard requests do not load or embed CSV results. Legacy dashboard aliases that the API already denied do not advertise an unavailable feature.

`dashboard_bundle_suggestions(user, limit=3)` calls `build_bundle_suggestions(user)` once. Marketplace uses the default limit; Super Admin passes `limit=2`. This changes only slicing and the View All boundary, never the mining result or thresholds. The output contains all original rows plus `dashboard_limit`, `suggested_rows`, `frequent_rows` and `has_more`. It only slices and sorts presentation lists; it does not recalculate Support, Confidence or Lift. Each role calls this same helper. The helper's file-revision/size/threshold cache and independent-copy behavior remain unchanged.

Data flow: configured synthetic CSV -> `analyze_synthetic(path, limits)` validates transaction/seller/product identities and forms item sets -> existing `calculate_market_basket(...)` produces qualifying directional rules -> existing service normalizes seller/product pairs and retains the strongest direction -> one dashboard presentation context -> shared Django partials and escaped `json_script` -> view-only browser dialogs. Retry performs GET against the existing protected `/api/marketplace/bundle-suggestions/?source=synthetic` endpoint and updates both panels from the same response.

Existing formulas, where N is the number of actual CSV transaction baskets:

- Support = transactions containing A and B / N x 100.
- Confidence A -> B = transactions containing A and B / transactions containing A x 100.
- Lift A -> B = confidence as a fraction / B's support as a fraction.

The UI formats already calculated values to two decimals; it does not mine rules in JavaScript. Confidence retains its actual A -> B direction in the data and title tooltip. Pair normalization includes seller-qualified product identities, so reversed rules cannot become duplicate cards for the same seller/pair. Default configured thresholds remain Support >= 2%, Confidence >= 30%, Lift > 1. Nothing is changed in the mining function or supplied CSV.

Annotated example of presentation-only code:

```python
result = build_bundle_suggestions(user)       # Existing CSV mining/cache, real computed metrics.
result['suggested_rows'] = result['rows'][:3] # A display limit, not an invented result count.
result['has_more'] = len(result['rows']) > 3  # View All follows actual qualifying results.
```

`review(row)` renders the selected two products, seller and metrics using text nodes. `renderAll()` paginates either existing ranking without modifying it. `load()` sets loading/aria-busy states, fetches only synthetic GET results, and shows an honest error when loading fails. Native dialogs supply keyboard focus containment/Escape/return-to-opener; the UI has one Close action in Review and no seller/product write controls.

Product image handling: the supplied CSV has no photo column, and its existing catalog entries have empty `image_url` values. Each product therefore uses the **existing** `inventory_kpi_icon.html` product placeholder, separately. Synthetic IDs are never looked up in the live product database to borrow names, photos or sellers. A real image URL in a future legitimate source uses a reserved image slot; broken images restore the placeholder. Seller labels continue deriving from the actual CSV seller ID through the existing service; no real seller identities are invented.

The new service/account summaries complete the requested system-wide section order using existing aggregates. Configured/open services reuse `service_resources_q()` with non-archived Facility records and existing operational status. Pending requests reuse Booking's actual Pending status and service relation. Enabled accounts have `is_active=True` and `is_suspended=False`; restricted count = total minus enabled. These are **current snapshots**, independent of chart grouping, and refresh through the existing dashboard JSON response. Pending service requests preserve the existing Services Requests route's historical scope, including requests whose facility may later be archived.

### 5. Backend / API Behavior and Data Isolation

Same Django backend, CSV loader, Apriori helper, thresholds and protected GET API for both roles. No second algorithm, new endpoint, duplicate inventory logic, seller notification, real bundle creation or persistent suggestion records. Synthetic data does not enter live Products, Orders, sales, revenue, inventory, low-stock or seller-performance queries. Existing real metrics and marketplace date/grouping calculations are preserved. Date changes do not filter the independent supplied synthetic dataset.

The existing global dashboard API additionally returns the read-only `services_overview` and `accounts_overview` dictionaries. The existing date/Refresh controller updates their six text hooks when those fields are present; its sample-only rendering branch does not change these real snapshots. Services/User links use existing routes and permission gates. No role grants are changed.

### 6. Database / Migration Impact

No model changes, new tables, migration, new package or dataset mutation. No production records were added, edited or removed. Normal static deployment remains necessary on a deployed server. Locally use Ctrl+F5 to load CSS version `20261015-summary-dynamic-bundles`; the existing read-only pair controller and domain-summary refresh controller remain. No migrate command is required.

### 7. Tests Performed / Manual Tests / Debugging

**46 Django tests passed** for the feature and existing marketplace dashboard regressions. They cover actual supplied CSV metrics, unrounded threshold filtering, reverse-pair normalization, malformed/missing input, isolation from live sales, caching, same results across roles, allowed/denied GET access, no write methods, both layout orders, honest empty/error states, and real service/account summaries in HTML and the existing refresh API. Run from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.marketplace.test_bundle_suggestions modules.reports.test_dashboard_marketplace --keepdb --noinput
```

Chrome verification passed for Marketplace and Super Admin at **1440, 1024, 768 and 390px**. It checked actual CSV row IDs/metrics, support ranking, two separate image slots, no Apriori canvas/source dropdown, conditional View All, read-only Review, Escape/focus return, nested Review from View All, both responsive placements and no page horizontal overflow. Empty/error states, loading, failed Retry and successful Retry were checked. The existing Super Admin Refresh controller restored all six domain-summary text values from the real isolated dashboard API payload while leaving Apriori rows unchanged. Numbered pagination was exercised using 579 rules calculated from the same CSV at isolated lower **test-only** thresholds; no manufactured pairs or metrics were injected. Production thresholds remain unchanged. Desktop, phone and Review screenshots were visually inspected. JavaScript syntax and targeted whitespace checks passed.

Latest evidence: `scratch/dashboard-kpi-dynamic-bundles-tests.log`, `scratch/dashboard-kpi-dynamic-bundles-browser.log`, and `scratch/bundle-suggestions/kpi-dynamic-bundles-check.cjs`. The original CSV SHA-256 was independently checked and remains `a768c0d31a671e3bd30ed907300aa027a749a05be8ee000ee677efc35538415d`. The browser uses isolated Django-rendered test fixtures and actual CSV-derived API JSON; it does not sign into or write to production. Logos/profile image resources are not part of this isolated preview.

Confirmed debugging outcomes: an initial account-count test expected four users but its setup created three; the assertion was corrected. A phone preview initially reported overflow because the harness had not initialized the existing Order Status canvas (default 300px width), rather than a confirmed application layout defect. Loading the existing chart controller fixed that preview; no application chart behavior was changed to mask it.

Manual steps:

1. Sign in as Marketplace Admin with analytics permission. Verify KPI row -> Sales/bundles -> Product Performance/frequent pairs -> existing operations sections.
2. Sign in as Super Admin. Verify eight KPIs on the left (four top/four below on wide desktop), Suggested Bundles on the right with SYNTHETIC and two computed rows. Verify no duplicate Suggestions below Analytics; Frequently Bought Together is beside Sales Overview, while live Top Selling Products / Product Categories follow below.
3. Compare the two roles' pair metrics; they should match the same CSV output. Check Frequently Bought Together has Support only.
4. Review a suggestion: verify two distinct product slots, actual names/seller/metrics, SYNTHETIC, one Close action. Escape and Close should restore focus.
5. Open View All if additional qualifying rows exist. Review from there, return to the list, then Close. It must not offer creating/sending/accepting bundles.
6. Change marketplace date/grouping filters: live sales/product data may change; synthetic Apriori results remain independent. Super Admin Refresh also refreshes current service/account snapshots.
7. Resize to tablet/phone and confirm the specified stacking order and contained table scrolling. For an unavailable CSV or no qualifying rules in an isolated development configuration, confirm the exact empty/error messages and no fake rows.

Troubleshooting: missing panels -> check role/admin-access/analytics permission together; do not bypass the API guard. Old label-only or graph UI -> check both updated templates and the three cache versions, then Ctrl+F5. No photos -> expected for this CSV; do not attach unrelated live photos. Dataset unavailable -> check configured path, file access, required header/data-origin/date values and threshold configuration, then Retry. Both roles disagree -> compare settings/path/file revision and ensure both call the shared presentation helper; avoid a second calculator. No View All -> compare actual qualifying-row length with the role preview limit (two for Super Admin, three for Marketplace), rather than adding placeholder rows. Right bundle card missing -> inspect the shared overview aside include and analytics permission, then verify the new CSS cache version. More rows after Retry -> check that the JSON seed carries the same role preview limit; the unchanged controller retains that limit while rendering the shared GET response.

Safe practice exercise: open DevTools, inspect a pair and change `.bundle-pair-images` gap from 10px to 8px. Verify both product slots still remain separate and the displayed metrics remain identical; reload to restore. For a read-only calculation check, inspect the first row in `bundleSuggestionsData` and compare `100 * together_count / transaction_count` with Support, allowing the displayed two-decimal rounding. This separates presentation changes from backend calculations without editing live records.

### 8. Remaining Limitations

The supplied CSV provides no real catalog-photo or seller-account mapping, so current results correctly use placeholders and synthetic seller-ID labels. Synthetic suggestions remain demonstration evidence and cannot create/contact real seller bundles. Physical/deployed-device checks and live authenticated interactive Refresh remain manual; server API snapshots, preserved selectors and interactive browser Refresh with the actual test API payload were verified. Large result sets are paginated in the read-only View All dialog; initial JSON still contains the existing full qualifying result set. This localized update does not claim a complete dashboard accessibility/performance audit or alter unrelated chart colors/controls.

---

## Previous Super Admin summary layout: four-by-two KPIs, small icon containers and larger bundle panel (2026-10-15)

### 1. Cause / Reason

The latest refinement asks for small containers around the eight KPI icons, four cards on top and four below on wide desktop, and a bigger Suggested Product Bundles panel. This supersedes the previous transparent 24px icons and narrow, natural-height bundle card. UI/UX Pro Max responsive guidance was used to keep the content inside the viewport. Existing real numbers, metric keys and permission boundaries are preserved.

### 2. Exact Files Changed / Current Anchors

| File / approximate line | Anchor | Purpose |
| --- | --- | --- |
| `backend/templates/dashboard/pages/admin_dashboard.html:26` | `admin_dashboard_summary.css` | Loads the scoped final summary stylesheet, version `20261015-summary-icon-containers`. |
| Same page, line 54 | `system_overview_summary.html` | Global Super Admin overview uses the new shared metric layout; non-global legacy markup remains. |
| Same page, around line 266 | `show_bundle_suggestions and not global_dashboard` | Avoids rendering a second copy lower down. |
| `backend/templates/dashboard/partials/system_overview_summary.html:2` | `dashboard-summary-layout` | Existing eight real metric cards reordered into the left grid, with the existing bundle partial in the right aside at line 119. |
| `backend/static/components/css/admin_dashboard_summary.css:2` | `.dashboard-summary-layout` | Scoped columns, compact cards, uniform icons and responsive stacking. Card/icon rules are lines 7-14; bundle rules are lines 16-19; breakpoints are lines 20-30. |
| `scratch/bundle-suggestions/summary-check.cjs:1` | isolated browser harness | Checks ordering, all eight metric hooks, uniform icon styles, card sizing, and right/below placement at six widths. This scratch harness verifies layout only. |
| This guide / `CAMPUSHUB_CONTEXT.md` | latest layout entry | Explanation, verification, troubleshooting and learning exercise. |

### 3. Changes Made

Super Admin left-side order: Total Products, Total Facilities, Marketplace Revenue, Pending Approvals, Total Users, Active Sellers, Total Orders, Total Bookings. All eight remain. At 1280px and above, the left grid has four columns and two rows. Below 1280px it uses two columns; below 600px it uses one column. Suggested Product Bundles now takes approximately one-third of the overview width (2:1 columns), with a minimum width of 280px, and matches the left grid height. At 991px and below it moves under the KPI grid with a 180px minimum height.

All eight KPI cards use white surfaces and navy text. Each top-right icon has a 32px square light-navy container, 8px rounded corners, a subtle border and an 18px navy outline glyph. The palette and sizes are identical across cards. Values and helper text span the full card width below the label/icon row. Card padding is 14px, grid gaps are 12px, values are 24px and minimum card height is 104px. Real text can increase height instead of clipping. The larger bundle card uses 24px padding, an 18px title and a 13px supporting label. Decorative SVGs remain aria-hidden; metric cards do not lift on hover.

The Suggested Product Bundles card still shows only its title and Apriori Algorithm / Market Basket Analysis label. No values, graph, result rows or Review UI were restored. Marketplace Admin keeps its existing section position: the four facility-related names identify this layout request as Super Admin, and no extra facility KPIs are added to the Marketplace dashboard.

### 4. How It Works / Inputs, Outputs, Functions and Data Flow

No new application function. `admin_dashboard_page(request)` continues building the existing real `dashboard_stats` and `dashboard_kpis` dictionaries. Global Super Admin rendering includes `system_overview_summary.html`; that partial outputs the existing value expressions and `kpi_secondary.html` calls. Every `data-dashboard-kpi` and `data-dashboard-secondary` hook is preserved, so the existing `admin_dashboard_filter.js` can still refresh each metric by its key after a date-filter request. Changing visual order does not change the key or calculation.

Flow: protected dashboard request -> existing metric helpers -> existing context dictionaries -> overview partial -> CSS grid. The existing `show_bundle_suggestions` permission Boolean includes the existing label-only bundle partial in the right aside. If permission is absent, CSS gives the metric area full width. The separate protected CSV/Apriori API remains independent.

Annotated example: `<strong data-dashboard-kpi="total_products">...</strong>` stays the same metric hook when moved. The surrounding grid decides position; the view/API decides its real number. Avoid changing a metric key merely to change where the card appears.

### 5. Backend / API Behavior

No new endpoint, altered formula, duplicate count, changed global date filter or permission bypass. All eight KPI values/helper messages come from the existing backend. Suggested-bundle visibility follows its existing analytics permission. The CSV and Apriori backend remain available; no synthetic values feed real KPIs.

### 6. Database / Migration Impact

No model, migration, database mutation or extra dependency. Deploy the new stylesheet alongside existing static files through the usual deployment process. Reload Django if templates are stale, then Ctrl+F5. No migrate command is needed.

### 7. Tests Performed / Debugging / Learning Exercise

For this visual refinement, one existing Django test passed: `BundleSuggestionAccessTests.test_super_admin_label_only_section_retains_api_algorithm`. It checks the rendered dashboard and retained protected API and regenerates the isolated browser fixture. The earlier layout had 41 passing feature/marketplace dashboard tests; those were not rerun for this CSS-only refinement. To repeat the current focused test from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.marketplace.test_bundle_suggestions.BundleSuggestionAccessTests.test_super_admin_label_only_section_retains_api_algorithm --keepdb --noinput
```

Chrome checks passed at 1920, 1440, 1280, 1024, 768 and 390px: all eight unique keys in the requested order, exactly one label-only bundle card, uniform 32px icon containers/18px glyphs, white cards, no clipped KPI content, four top/four below at the three wide desktop widths, enlarged right panel and smaller-screen stacking. At 1440px the bundle card measured about 370px wide by 257px tall; at 1920px it was about 530px wide by 240px tall. Desktop and phone screenshots were visually reviewed. Logs: `scratch/dashboard-summary-icons-render.log`, `scratch/dashboard-summary-icons-browser.log`. Browser evidence uses isolated rendered Django test fixtures with scripts removed for a layout check, not live authentication or production writes. Targeted whitespace and harness syntax checks also passed.

Manual check: Super Admin -> Dashboard -> System Overview -> Ctrl+F5. At 1280px or wider, confirm four cards on top and four below, matching icon containers, and a bigger bundle card on the right. Change the global date range and verify real values/helpers refresh. Resize below 992px: the bundle moves below the KPIs; at phone widths the KPIs stack. Confirm the Marketplace Admin dashboard retains its own existing scope/layout.

Troubleshooting: old plain icons or narrow bundle card -> verify stylesheet `20261015-summary-icon-containers` loads after the existing dashboard styles and Ctrl+F5. Duplicate bundle card -> check the lower include is restricted to `not global_dashboard`. Missing/incorrect values -> inspect backend context and preserved metric hooks, not CSS; never replace them with sample values. Larger rows with long currency/helper text are intentional wrapping, not a new stock/revenue calculation.

Safe practice: in browser DevTools change `.dashboard-stat-icon` border radius from 8px to 4px. Verify that all eight icon containers change equally while their numbers and metric keys remain identical. Reload to restore the saved design. The label/icon CSS grid row controls placement; `display: contents` lets the existing text wrapper participate in that same grid. This teaches the separation between data, markup hooks and presentation.

### 8. Remaining Limitations

Physical/deployed-device testing remains manual. The browser layout harness does not exercise AJAX filter interaction; existing Django period/data regressions passed and metric selectors were preserved. Very long live values can grow rows beyond their minimum height to preserve readability. This change targets Super Admin System Overview; other dashboard sections and unrelated legacy icon styles remain outside its scope.

---

## Previous label-only implementation record

## 1. Cause / Reason

The user clarified that the desired result is a label-only section rather than restoring the former table or removing the entire feature. Inspection found partial reversion: the new template still expected graph/row markup while the older controller expected a removed source dropdown. A missing row-template reference could also break page rendering. Replacing the section markup and unloading its value controller resolves those incompatible references without deleting the algorithm or synthetic data.

## 2. Exact Files Changed / Current Anchors

| File / approximate line | Nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html:2` | `id="bundleSuggestions"` | Shared compact card with heading and supporting algorithm label only. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:98` | `marketplace.show_bundle_suggestions` | Reuses the shared partial; removes feature CSS/JS loads. |
| `backend/templates/dashboard/pages/admin_dashboard.html:259` | `show_bundle_suggestions` | Same label-only section for authorized Super Admin; removes feature CSS/JS loads. |
| `backend/core/modules/reports/views.py:535` | `show_bundle_suggestions` | Marketplace context uses existing analytics permission, not a CSV result payload. |
| Same view, around line 1375 | Super Admin `show_bundle_suggestions` | Keeps role/permission gating and stops mining for a label-only page. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:146` | `test_failure_is_not_fabricated_zero_metrics` | Aligns the error assertion with the retained synthetic loader error text. |
| Same test file, around line 167 | `test_dashboard_placement_view_only_disclosure_and_real_totals` | Verifies section position, removed UI/assets, unchanged live totals and no dashboard loader call. The old method name is retained for compatibility. |
| Same test file, around line 190 | `test_super_admin_label_only_section_retains_api_algorithm` | Verifies Super Admin labels and retained protected API output. |
| `scratch/bundle-suggestions/labels-check.cjs:1` | `prepare(file)` | Local browser verification using isolated Django-rendered fixtures. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current update | Documents the clarified display and verification. |

## 3. Changes Made

Both dashboard cards now contain exactly:

```text
Suggested Product Bundles
Apriori Algorithm / Market Basket Analysis
```

Removed from these cards: transaction and pair counts, support/confidence/lift values, graph, result rows, source control, source/status badges, disclosure block, Review dialog, pagination and JSON result seed. With no synthetic results displayed, the card does not represent a live or synthetic recommendation. The old feature stylesheet/controller files remain in the repository but are not loaded by either dashboard. The partial no longer includes the missing row template. Existing dashboard card/heading/subtitle classes supply the compact layout and responsive spacing.

## 4. How It Works / Functions, Inputs, Outputs and Data Flow

`_marketplace_operational_dashboard_data(request, user)` continues calculating real sales and other existing dashboard data. Its new `show_bundle_suggestions` Boolean comes from `user.has_perm('accounts.can_view_marketplace_analytics')`. The dashboard template uses that Boolean to include a static shared partial. Super Admin uses the same permission plus its existing role/superuser boundary. No product names, metrics or CSV payload are sent to this section.

Dashboard flow: authorized request -> existing dashboard view -> permission Boolean -> shared partial -> two visible text labels. No feature JavaScript is needed.

Algorithm flow remains separate: authenticated GET `/api/marketplace/bundle-suggestions/` -> existing role/analytics permission checks -> `build_bundle_suggestions(user, source)` -> validated CSV loader/cache -> `calculate_market_basket(...)` -> calculated JSON result. The CSV remains `backend/core/modules/marketplace/data/synthetic_order_items.csv`; its content is unchanged. Support/confidence/lift calculation and threshold configuration are retained, including existing live-mode compatibility behavior. These calculated values are no longer dashboard display content.

Annotated example:

```django
{% if marketplace.show_bundle_suggestions %}
    {% include 'marketplace/partials/bundle_suggestions.html' %}
{% endif %}
```

The condition controls visibility using a permission Boolean. It does not request, seed, or render recommendation records. Sharing the partial keeps the two dashboards' labels consistent.

## 5. Backend / API Behavior

No calculation API, CSV, algorithm, access permission or real marketplace workflow was removed. The API remains GET-only and protected. Dashboard views no longer call the bundle loader solely to display static labels; this avoids unnecessary analysis and prevents hidden result JSON from remaining in page source. Existing sales/orders/inventory and unrelated dashboard sections keep their behavior. No seller notifications or real bundle products are created.

## 6. Database / Migration Impact

No model, migration or database write. No new dependency. The bundled CSV is unchanged (SHA256 `a768c0d31a671e3bd30ed907300aa027a749a05be8ee000ee677efc35538415d`). Restart/reload Django if it does not pick up the view/template changes, then hard-refresh the dashboard with Ctrl+F5. No migrate command is needed for this change.

## 7. Tests Performed / Manual Checks / Learning Exercise

Ran 37 feature/scoped dashboard tests successfully. Two dashboard tests were then rerun successfully after strengthening the mock to prove the entire bundle loader is not called on page rendering. Django system checks reported no issues in those runs. Logs: `scratch/bundle-suggestions-labels-tests.log` and `scratch/bundle-suggestions-labels-final.log`.

Chrome browser verification passed Marketplace Admin and Super Admin at 1440px and 390px: exactly the two requested labels, no table/canvas/source button/Review dialog/JSON seed, and section bounds inside the viewport. Fixtures are test-only local HTML; they do not mutate production records. Log: `scratch/bundle-suggestions-labels-browser.log`. One initial QA assertion escaped a whitespace regex incorrectly; fixing the harness escaping produced the passing results above. It was a QA-script issue, not missing application labels.

From `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.marketplace.test_bundle_suggestions modules.reports.test_marketplace_admin_dashboard --keepdb --noinput
```

Manual check: sign in with an authorized Marketplace Admin -> Dashboard -> find the section after Product Performance. Confirm only the heading and algorithm label are visible. Repeat as Super Admin. Confirm sales/orders still show real existing values and other sections work. If checking the retained algorithm, use an authorized session to inspect the existing GET endpoint separately; do not import synthetic rows into live orders.

Troubleshooting: old values remain -> reload Django and Ctrl+F5, and verify the shared partial is the current five-line template. JavaScript complains about `bundleDataSource` -> confirm neither dashboard loads bundle_suggestions.js. Missing template error for bundle_suggestion_row.html -> stale shared partial; the current label-only version contains no row include. Section missing -> inspect role/analytics permission first; do not bypass RBAC or fill it with fake records.

Safe practice exercise: on a local branch change only the supporting label in the shared partial, reload both dashboards and observe that both use the same wording. Restore `Apriori Algorithm / Market Basket Analysis`, rerun the two dashboard tests, and confirm the protected calculation API still returns results. This demonstrates the difference between presentation text and backend calculation. Do not alter live payments/orders to test a label.

## 8. Remaining Limitations

No calculated recommendations, graph or Review interaction are available on the dashboard now; this is the requested display. The old detailed UI assets are retained but inactive, and earlier browser harnesses for that UI do not validate this label-only layout. Algorithm/data accuracy and live transaction-basket limitations remain as documented in the historical record. Browser checks used isolated fixtures; deployed sessions, physical devices and assistive-technology checks remain manual. No whole-dashboard redesign or cleanup of unrelated workspace changes was performed.

---

## Historical implementation record (superseded dashboard UI)

# Suggested Product Bundles — read-only Apriori demonstration

Updated October 15, 2026. This guide describes the shipped implementation and the user's final clarification: the supplied CSV is an isolated, **view-only synthetic demonstration**. Review never contacts a real seller, changes inventory, creates a bundle, or imports synthetic transactions into the database. This clarification supersedes the send/accept/decline workflow in the original pasted brief.

## 1. Cause / Reason

The Marketplace Admin dashboard needed an explainable decision-support section after Product Performance and before Marketplace Operations. The existing `calculate_market_basket` helper already calculates pair association rules, so the feature extends it rather than adding another algorithm, Product model, or seller bundle system.

Two confirmed implementation facts determine the behavior:

- The supplied CSV has synthetic seller/product identifiers, not foreign keys to CampusHub accounts or products. It contains no real seller name, Program/Major mapping, or photo. Mapping an `S01` or `P01` to a database row with a similar ID would invent an ownership relationship.
- Current live checkout records one sellable product per unique order code. It does not retain a shared multi-product checkout transaction identifier. Grouping unrelated purchases by buyer/date, or expanding the ingredients of an existing bundle, would fabricate purchase baskets.

Consequently, the section can show computed synthetic association rules and a protected count of eligible live orders. Live mode honestly shows no suggestions until the application has genuine multi-product transaction baskets. This is Apriori association-rule mining for product pairs, not AI, a trained model, or proof of real purchasing behavior.

## 2. Exact Files Changed

Paths are relative to the project root. Lines below were checked against the final implementation; use the named anchor if later edits move a line. These are the files changed for this feature, not the other pre-existing workspace changes.

| File / current line | Nearby anchor | Reason and expected behavior |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/analytics.py:505` | `calculate_market_basket` | Adds optional threshold/detail/limit arguments to the existing pair calculation. Default callers retain their original row shape, rounding, limit, and threshold behavior. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py:18` | `DISCLOSURE`, `DATASET` | Defines the explicit disclosure and separate CSV location. |
| Same service, line 27 | `thresholds` | Reads and validates support, confidence, and strict lift configuration. |
| Same service, line 36 | `analyze_synthetic` | Validates CSV rows, builds transaction sets, mines rules, rejects cross-seller pairs, and removes reverse-direction duplicates. |
| Same service, line 99 | `_cached_synthetic` | Reuses results for an unchanged path/file revision/threshold tuple, with up to four cached analyses per Python process. |
| Same service, line 104 | `build_bundle_suggestions` | Returns independent synthetic/live payloads, honest empty states, and recoverable errors; copies cached results before returning them. |
| `backend/core/modules/marketplace/data/synthetic_order_items.csv:1` | CSV column header | Stores the supplied source unchanged outside live models. It is data for the demonstration, not an import or seed script. |
| `backend/core/modules/marketplace/bundle_suggestion_views.py:12` | `bundle_suggestions_api` | Adds an authenticated, role/permission-protected GET endpoint; rejects write requests. |
| `backend/core/core/urls.py:117` | `bundle_suggestions_api` path | Names `/api/marketplace/bundle-suggestions/` for service and browser reuse. The import is at line 3. |
| `backend/core/core/settings.py:210` | `CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH` | Adds optional dataset-path configuration and three environment-backed thresholds at lines 211–213. |
| `backend/core/modules/reports/views.py:535` | `build_bundle_suggestions` import | Adds the payload to the existing Marketplace operational dashboard only when the analytics permission is present; the return key is at line 552. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html:100` | `include 'marketplace/partials/bundle_suggestions.html'` | Inserts the existing-card section in the requested position; loads feature CSS at line 18 and JS at line 246. |
| `backend/core/modules/marketplace/templates/marketplace/partials/bundle_suggestions.html:8` | `id="bundleSuggestions"` | Renders title/source control, disclosure, real calculated counts, eight-column table, independent pagination, and review dialog. |
| Same partial, line 26 | `id="bundleReviewDialog"` | Provides separate Product A and Product B evidence cards, metrics and rule direction, disclosure, and close-only actions. |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css:3` | `.bundle-dss` | Adds local navy/gold/light styles; contains the wide table inside its own scroll region. Dialog rules begin at line 32 and mobile adjustments at line 63. |
| `backend/core/modules/marketplace/static/marketplace/js/bundle_suggestions.js:2` | `DOMContentLoaded` | Reads the server seed, renders text safely, paginates rows, opens/closes the native dialog, and fetches source changes with loading/error/race handling. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py:20` | `AprioriDemonstrationTests` | Tests formulas, thresholds, default compatibility, CSV validity, and separation. Access/integration tests begin at line 102. |
| `scratch/bundle-suggestions/browser-check.cjs:20` | `for(const width of [1440,390])` | Local browser QA harness using rendered Django test fixtures and mocked GET responses; it is not application runtime code or production data. |
| `docs/suggested-product-bundles.md:1` | This guide | Explains files, functions, evidence, debugging, limitations, and safe practice. |
| `CAMPUSHUB_CONTEXT.md:2114` | `Suggested Product Bundles (2026-10-15)` appended entry | Preserves the final view-only boundary and points to this guide; supersedes the earlier presentation-only feature note where behavior differs. |

## 3. Changes Made

The dashboard has the requested columns: **Bundle, Seller, Support, Confidence, Lift, Data Source, Status, Action**. It has no Strength column. The default source is Synthetic demonstration, with a visible SYNTHETIC label and the full disclosure. Each calculated row says Synthetic / Generated / Review. `Generated` means the displayed calculation produced that pair; it is not a stored workflow status.

Review opens a native HTML dialog with two separate product cards, prices and categories from the supplied CSV, synthetic seller labels, the directional rule, and its metrics. Both image areas explicitly say **No photo provided**. There are no invented photos or real shop names, and no send, dismiss-as-status, accept, decline, approval, or create-bundle action. Close Review and the close button only close the dialog. Escape and native focus restoration support keyboard use.

Source changes update only this section. Sales Overview dates/grouping continue controlling their existing live widgets; they do not filter the synthetic baskets. Pagination uses eight suggestions per page and remains independent of the rest of the dashboard. The actual supplied data currently produces four unique seller-qualified pairs, so no pagination is needed for that source at default thresholds.

### Local design record

This is an extension of the existing operational dashboard, not a new global design system. No global `DESIGN.md`, sidecar, or replacement product brief was created.

- Navy (`#1A1851`) identifies headings, text, controls, and selected page state; gold (`#FCB316`) marks disclosure and focus; white/light (`#FFFFFF`, `#f8fafc`) provide surfaces. Semi-transparent navy supplies borders and the dialog backdrop. No new gradient, glass surface, or decorative chart was added.
- Montserrat headings use 16px in the section and 18px in review; the compact table/body labels are 11–13px, with 14–15px product content and 18–20px review metrics. Arial/body fallbacks follow the incumbent surface rather than introducing another display face.
- Evidence appears in order: source/disclosure, counts and factual table, then two-product review and close. Bordered cards and contained scrolling provide structure. The table stays at least 950px wide inside its own horizontal scroll region; the source control stacks below the heading at 600px and below.
- Controls use 44px minimum height, visible gold keyboard focus, accessible table headings, and a labelled native dialog. The product cards remain distinct and side by side at the checked desktop/phone widths.
- The redundant decorative eyebrow was removed during final review. It is not recorded as a pattern for future screens. Gold disclosure borders and body-font fallbacks are incumbent conventions, not evidence of a full contrast audit or permission to expand the palette.

## 4. How It Works

### Inputs, functions, and outputs

`thresholds()` takes no arguments. It converts the configured settings to numeric values and returns `(minimum_support, minimum_confidence, minimum_lift)`. Support/confidence must be fractions between 0 and 1. Lift must be finite and at least 1; qualification is strictly greater than the configured lift floor.

`analyze_synthetic(path, limits)` accepts a CSV path and that threshold tuple. Required columns are `transaction_id`, `date`, `seller_id`, `product_id`, `product_name`, `category`, `quantity`, `unit_price_php`, and `data_origin`. Dates use `%m/%d/%Y`; quantities must be positive; prices must be finite and nonnegative; origin must explicitly be SYNTHETIC. Identifiers allow letters, digits, underscores and hyphens, with 1–80 characters. The reader rejects incomplete data, conflicting catalog entries, mixed sellers/dates inside one transaction, over 100,000 rows, or over 100 distinct products per basket.

The reader forms one **set of distinct seller-qualified products per transaction**. For example, a product key is `S04:P01`, not just `P01`. A quantity of 3 or a repeated line still means that product appears once in the purchase basket; association support is about transactions, not item units. Qualifying pairs must have the same seller. Names, category, and price remain CSV attributes; `image_url` is empty.

`calculate_market_basket(transactions, ...)` receives lists of `(product_id, product_name)` tuples. It counts single-product occurrences and two-product combinations, then evaluates both directions for each pair. The existing minimum evidence requirement remains three nonempty baskets and two baskets containing multiple products. The demonstration calls it with configured thresholds, `detailed=True`, and `limit=None`. Detailed rows include identities and `together_count`, `source_count`, and `target_count`; default legacy callers still receive just the original five metric/name keys.

For total baskets `N`, baskets containing both `nAB`, baskets containing A `nA`, and baskets containing B `nB`:

```text
support(A,B)    = nAB / N
confidence(A→B) = nAB / nA
lift(A→B)       = (nAB / nA) / (nB / N)
```

Thresholds apply to the unrounded numbers. Displayed support/confidence are percentages rounded to two decimals in detailed mode; lift is rounded to two decimals. Rules sort by descending lift, confidence, then support. The service treats A+B and B+A as one unordered seller/product pair and keeps the first qualifying direction in that order. The review explicitly names Product A → Product B so confidence is understandable.

**Annotated example from the supplied data:** Synthetic Seller S04 has 20 baskets containing Pancit Canton and Boiled Egg, 22 containing Pancit Canton, and 25 containing Boiled Egg, among 1,000 total synthetic baskets. Support is `20/1000 = 2.00%`; confidence for Pancit Canton → Boiled Egg is `20/22 = 90.91%`; lift is `(20/22)/(25/1000) = 36.36`. The pair meets support ≥ 2%, confidence ≥ 30%, and lift > 1. The high lift describes this constructed dataset only; it is not a real seller's forecast or a promise of sales.

### Source provenance and calculated output

The copied source is the user-supplied `Synthetic-dataset-Order-items (1).csv`. Its SHA-256 is:

```text
a768c0d31a671e3bd30ed907300aa027a749a05be8ee000ee677efc35538415d
```

The unchanged source contains 2,027 item rows, 1,000 transaction baskets, and 792 multi-product baskets dated July 1–September 28, 2026. `S01`–`S05` and `P01`–`P30` are synthetic identities, not live database IDs. At the default thresholds its four unique pairs are:

| Direction shown | Synthetic seller | Support | Confidence | Lift |
| --- | --- | ---: | ---: | ---: |
| Siomai Rice → Gulaman | S01 | 2.10% | 87.50% | 36.46 |
| Pancit Canton → Boiled Egg | S04 | 2.00% | 90.91% | 36.36 |
| Cucumber Lemonade → Burger | S02 | 2.00% | 86.96% | 29.99 |
| Boiled Egg → Pancit Canton | S03 | 2.00% | 80.00% | 29.63 |

These are calculations from the CSV, not hardcoded UI examples. The two similarly named Pancit Canton/Boiled Egg pairs belong to different synthetic sellers and therefore remain separate identities.

### Service → dashboard → browser

`build_bundle_suggestions(user, source)` normalizes the source to `live` only for that exact value; other values select synthetic. It returns `source`, `rows`, `read_only`, `error`, `disclosure`, transaction count, page size, endpoint, and threshold display values. Synthetic success also includes row/multi-item counts, date range, and sufficiency information. Rows include the product cards and computed metric details.

The synthetic cache key includes path, file modification time in nanoseconds, file size, and thresholds. A changed key recomputes analysis; a restart also clears the process-local cache. A deep copy prevents a caller from mutating cached product data. Refreshing an unchanged dataset reuses the calculation and creates no database records. This small local cache was chosen because the dataset is fixed and small; no new queue or scheduler is necessary.

The dashboard seeds the payload through Django `json_script`; the partial initially escapes template values. `render()` in the JS rebuilds table rows and pagination with text nodes. `review(row)` also inserts CSV names/categories/seller text with `textContent`; only the fixed decorative SVG placeholder uses `innerHTML`. Dataset text is never treated as HTML.

`load()` performs a GET when the source changes or Retry is pressed. It marks the section busy, replaces stale rows with a loading message, and accepts only the latest request version. A slower old live response cannot overwrite a newer synthetic selection. Network/access errors show an error message and Retry. Missing/invalid CSV or settings also produce an honest error payload rather than fabricated zero-valued association metrics.

## 5. Backend / API Behavior

`GET /api/marketplace/bundle-suggestions/?source=synthetic` returns the isolated demonstration. `?source=live` returns the eligible live count and the current explanatory empty state. The source is independent of Sales Overview date/grouping parameters. The dashboard's optional initial parameter is `bundle_source=live`; the API uses `source=live`.

The Django JSON endpoint requires authentication, Marketplace Admin or Super Admin role (or `is_superuser`), existing administrative access, and `accounts.can_view_marketplace_analytics`. An unauthenticated endpoint request returns 401; an unauthorized user returns 403; POST and other non-GET methods return 405. Existing middleware/session and admin-tab authentication remain in force; normal redirect/auth behavior can apply before a request reaches this function. Successful responses are private/no-store. Dataset/configuration errors have `error: true`, empty rows, and a visible recoverable message.

Marketplace Admin is the dashboard operator. The existing Marketplace dashboard includes the section only with the analytics grant. Super Admin can access the endpoint when authorized; the full review UI was not added to the Super Admin overview. Normal accounts and Facilities Admin are denied, even if they can reach a URL directly. No permission grants or existing role records were rewritten.

Synthetic data has no academic ownership mapping. Authorized demonstration viewers see the **separate synthetic dataset**, not claimed in-scope real sellers. Live counting intersects existing `valid_sales_queryset(user)` (`analytics.py:95`) with protected `admin_order_queryset(user)` (`order_access.py:6`). It therefore requires completed, paid, positive-quantity orders and canonical product Program/Major scope plus existing order access/protection. Missing Marketplace scope fails closed. Pending, cancelled, and unpaid orders do not count. There is no separate refund lifecycle introduced by this feature.

Because real shared baskets are absent, live mode returns no fabricated rule rows. Its message is “No bundle suggestions available yet.” and explains the shared transaction identifier limitation. Synthetic data with no qualifying pairs uses “No qualifying bundle suggestions found.” A source/configuration failure uses “Unable to load bundle suggestions.”

No notification, FastAPI chat, audit-event creation, product approval, stock deduction, payment, manual seller bundle creation, or persistent suggestion workflow is invoked. Existing seller-created bundles and their existing approval rules remain independent of this demonstration.

## 6. Database / Migration Impact

No models, fields, migrations, recommendation status tables, or foreign keys were added or changed. The CSV stays on the filesystem; it is never inserted into `MarketplaceOrder`, Product, sales, revenue, demand forecasting, or seller analytics. “Generated” is calculated display text, not a database record. The API performs reads only.

**Do not run `migrate` for this feature.** The implementation's migration dry run reported no model changes. Django tests create/use isolated test fixtures and the test database; that is distinct from writing application demonstration records to the live database.

## 7. Tests Performed

Recorded implementation verification, not an assertion that every project test or deployed device was exercised:

- **36 focused feature/scoped-dashboard tests passed.** The saved output is `scratch/bundle-suggestions-tests.log`. Formula and threshold tests cover correct support/confidence/lift, strict positive lift, insufficient baskets, preserved legacy return shape, same-seller validation, malformed/conflicting CSV data, source labelling, completed-paid scope, denial, read-only GET/405, no live sales/order/stock mutation, cache reuse, copied results, and requested dashboard placement.
- **41 existing marketplace/dashboard/bundle regressions passed.** The saved output is `scratch/bundle-suggestions-regression.log`. Together these two runs contain 77 passing tests. A final rendering/placement fixture test was rerun and passed after the final presentation correction; its output is `scratch/bundle-suggestions-final-render.log`.
- **Headless Chrome checks passed at 1440px and 390px.** The harness checked the real rendered template fixture, the supplied four pairs, and a separate 13-row browser-only pagination fixture. It exercised eight columns, separate product cards/placeholders, native dialog close/focus restoration, source loading, live empty state, failure/Retry, late-response protection, GET-only calls, and HTML-like names rendered as text. Final checks explicitly verified that the new section fit the viewport and its wide table overflow stayed inside its own scroll region. The temporary pagination/name fixture was not added to the supplied CSV or database.
- Final `table-1440.png`, `table-390.png`, `review-1440.png`, and `review-390.png` in `scratch/bundle-suggestions/` were visually reviewed. A stale Django HTML fixture was regenerated before final capture. The reviewer requested removal of the redundant eyebrow; that specific finding was fixed and rechecked. The final disposition is limited to that correction, not a whole-dashboard usability endorsement.
- New Python files compiled, `node --check` passed for application JS and the QA harness, and Django system checks passed. New-file UTF-8/trailing-whitespace checks and targeted `git diff --check` passed. `makemigrations --check --dry-run` reported no changes. No physical-device or deployed-session end-to-end run is claimed.

Exact recorded test commands, run from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_bundle_suggestions modules.reports.test_marketplace_admin_dashboard --keepdb --noinput
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_marketplace modules.marketplace.test_bundles --keepdb --noinput
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_bundle_suggestions.BundleSuggestionAccessTests.test_dashboard_placement_view_only_disclosure_and_real_totals --keepdb --noinput
```

The first and final command used the optional `BUNDLE_REVIEW_DIR` environment variable pointing to the absolute `scratch/bundle-suggestions` directory to export rendered test HTML/JSON for browser QA. The browser harness consumes these local fixtures; it does not log in to or mutate a deployed application.

### Commands and manual verification

From the project root in PowerShell, restart the existing Django server after changing settings. If starting it yourself:

```powershell
Set-Location C:\Users\leste\Desktop\CAMPUSHUB\backend\core
.\venv\Scripts\python.exe manage.py runserver
```

Reload the dashboard with **Ctrl+F5** so CSS/JS version `20261015-readonly-apriori` is fetched. No database command is required. To run feature checks separately from a running server:

```powershell
Set-Location C:\Users\leste\Desktop\CAMPUSHUB\backend\core
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_bundle_suggestions --keepdb
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

1. Sign in with an existing Marketplace Admin that has dashboard access and the marketplace analytics grant. Confirm the section sits between Product Performance and Marketplace Operations, with eight columns and the full disclosure.
2. Synthetic demonstration should show 1,000 transactions and four pairs at the shipped default thresholds. Open each Review. Check two separate products, “No photo provided,” directional metrics, and close-only actions.
3. Tab through the source control/table/buttons. Open Review, press Escape, and confirm focus returns to Review. At a narrow width, scroll the table within its own region and confirm the disclosure and source control remain readable.
4. Select Live transactions. Expect an eligible scoped order count and an honest empty state with no synthetic badge. Record existing live sales/order totals before and after; they should not change because of source selection.
5. In an authorized development session, simulate an offline/failed request using browser developer tools. Confirm an error and Retry, then restore connectivity. Quickly change sources to check that the latest selection wins.
6. Check the endpoint with existing ordinary/Facilities accounts and a Marketplace Admin lacking the analytics grant. They should be denied. Do not alter live role assignments just to conduct this check; use the isolated tests when suitable accounts are unavailable.

### Troubleshooting

| Symptom | Confirmed mechanism / checks | Safe next step |
| --- | --- | --- |
| Section absent | The dashboard payload is omitted when the analytics permission is absent; Super Admin overview is not the Marketplace review surface. | Check existing role grants and dashboard route using authorized administration; do not grant broad rights to make a widget appear. |
| Live source has no pairs despite sales | Live checkout has no shared multi-product transaction ID. Completed paid count is not sufficient proof of a purchase basket. | Keep the honest empty state; future basket support requires a deliberate checkout/schema design. |
| Synthetic count differs | Configured path/thresholds may point elsewhere; current reader uses the entire CSV, not the Sales Overview period. | Check `.env` names below and restart Django. Verify file hash before assuming a formula defect. |
| “Unable to load bundle suggestions” | Missing/unreadable path, invalid column/row/catalog data, or invalid threshold configuration is caught by the service; network/access failures are caught by JS. | Check source existence and validation, endpoint response/status, and settings; fix the actual issue, then Retry. The generic message alone does not identify which cause occurred. |
| Old layout after reload | Static assets can remain cached. | Ctrl+F5 and confirm the feature's asset version; restart the server if settings changed. |
| Dataset edits seem cached | Cache keys use path/modification time/size/thresholds, not a content hash on every request. | Restore the source and restart Django to clear the local cache; do not replace the authoritative source as an experiment. |
| Whole phone page still scrolls sideways | The browser harness observed a pre-existing 50px overflow from Product Performance. The new table remained contained. | Treat that older surface as a separate verified issue; this local feature did not redesign the whole dashboard. |

Optional `.env` settings read by `core/settings.py`:

```dotenv
CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH=
CAMPUSHUB_BUNDLE_MIN_SUPPORT=0.02
CAMPUSHUB_BUNDLE_MIN_CONFIDENCE=0.30
CAMPUSHUB_BUNDLE_MIN_LIFT=1
```

A blank path uses the shipped separate CSV. An override should be an absolute path to an explicitly synthetic CSV. Values are **fractions**, so `0.02` means 2%; `2` is invalid support. Lift `1` means rules must exceed 1, not equal it. These settings affect this demonstration; existing analytics helper callers retain their defaults.

### Safe practice exercise

Practice the helper without changing files, settings, roles, or database rows. In `backend/core`, open a Django shell:

```powershell
.\venv\Scripts\python.exe manage.py shell
```

Then run:

```python
from modules.marketplace.services.analytics import calculate_market_basket
# Four baskets; A+B occur together twice, A appears three times, B twice.
baskets = [[('A', 'Practice A'), ('B', 'Practice B')],
           [('A', 'Practice A'), ('B', 'Practice B')],
           [('A', 'Practice A')], [('C', 'Practice C')]]
result = calculate_market_basket(baskets, minimum_support=.02,
    minimum_confidence=.30, minimum_lift=1, detailed=True, limit=None)
rule = next(row for row in result['rows'] if row['product_a_id'] == 'A')
print(rule['support'], rule['confidence'], rule['lift'])  # 50.0, 66.67, 1.33
# Requiring support above 50% removes this pair.
print(calculate_market_basket(baskets, minimum_support=.51,
    detailed=True)['rows'])  # []
```

Verify the printed values using the formulas above, then `exit()` the shell. These are in-memory practice baskets passed to a pure calculation, not demonstration records added to CampusHub. For same-seller/data validation practice, read `test_cross_seller_transaction_is_rejected` at `test_bundle_suggestions.py:75`; it uses a temporary CSV and cleans it up.

## 8. Remaining Limitations

- Genuine live association recommendations require a shared multi-product transaction identity and enforceable item ownership. No buyer/date grouping or existing bundle recipe can replace that evidence.
- The supplied synthetic identities lack real catalog/account/academic mappings and photos. Its products cannot be sent to real sellers or linked to live bundle creation. A future real recommendation workflow would require separate authorization, mapping, lifecycle, notification, audit, and approval design.
- The local analysis is for two-product associations; it is not a general multi-item Apriori engine, demand forecast, causal recommendation, or trained model. Thresholds and minimal basket counts do not establish statistical reliability in real commerce.
- Cached analysis is process-local, up to four entries, invalidated by file revision/size/settings. Workers may each compute their own first load; there is no shared scheduled cache. CSV limits deliberately bound the supported demonstration input.
- Current browser evidence uses rendered test fixtures/mocked GET responses on desktop Chrome. Physical phones, deployed authentication/asset delivery, real authorized sessions, other browsers, and assistive-technology testing remain manual. The detector was limited to regex-based checks; no complete contrast/accessibility or whole-dashboard audit is claimed.
- Existing unrelated dashboard overflow and other pre-existing workspace changes remain outside this local extension. Real sales/revenue/order data and seller-controlled manual bundle creation retain their existing behavior.
