# Web gold accent update ? October 17, 2026

1. **Cause / reason:** the user explicitly changed the web gold from `#FCB316` to `#FCB315`. This is a one-step reduction of the blue channel (22 ? 21), not a layout or workflow redesign. Existing Flutter colors retain their previous value.
2. **Exact files changed:** the table below lists all 53 changed web source files, current first matching line and nearby anchor. All existing line endings were preserved. Also updated the web brand rule in `AGENTS.md` and the current preference in `CAMPUSHUB_CONTEXT.md`. This existing guide records the change rather than adding a duplicate guide.

| File | Current line | Anchor |
| --- | --- | --- |
| `backend/static/components/js/admin_booking_overview.js` | 15 | `{ key: 'pending', label: 'Pending', color: '#FCB315' },` |
| `backend/static/components/js/admin_dashboard.js` | 6 | `gold: paletteStyle.getPropertyValue('--dashboard-gold').trim() \|\| '#FCB315',` |
| `backend/static/components/js/admin_facility_status.js` | 10 | `const colors = ['#1A1851', '#FCB315', 'rgba(26,24,81,.55)', 'rgba(26,24,81,.2)'];` |
| `backend/static/components/css/admin_alerts.css` | 96 | `border-left-color: #FCB315;` |
| `backend/static/components/css/account_password_reset.css` | 77 | `outline: 3px solid #FCB315;` |
| `backend/static/components/js/admin_facility_revenue.js` | 64 | `pointHoverBackgroundColor: '#FCB315', pointHitRadius: 10, tension: 0, fill: false}]},` |
| `backend/static/assets/img/samples/facility-training.svg` | 1 | `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" fill="#f8fafc"/><rect` |
| `backend/static/assets/img/samples/facility-hostel.svg` | 1 | `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" fill="#f8fafc"/><rect` |
| `backend/static/assets/img/samples/facility-hall.svg` | 1 | `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" fill="#f8fafc"/><path` |
| `backend/static/assets/img/samples/facility-court.svg` | 1 | `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" fill="#f8fafc"/><path` |
| `backend/templates/dashboard/partials/sales_sample_data.html` | 102 | `"color": "#FCB315",` |
| `backend/static/components/css/admin_booking_overview.css` | 104 | `background: #FCB315;` |
| `backend/static/components/css/admin_booking.css` | 48 | `.bk-completion-checks .is-outstanding svg { color: #FCB315; }` |
| `backend/static/components/css/admin_backup.css` | 58 | `background: rgba(252, 179, 21, 0.14);` |
| `backend/static/components/css/admin_analytics.css` | 3 | `--analytics-gold: #fcb315;` |
| `backend/static/components/css/admin_facility.css` | 3 | `--campushub-gold: #FCB315;` |
| `backend/static/components/css/admin_data_export.css` | 3 | `--export-gold: #fcb315;` |
| `backend/static/components/css/admin_dashboard_palette.css` | 4 | `--dashboard-gold: #FCB315;` |
| `backend/static/components/css/admin_dashboard_filter.css` | 52 | `background: #FCB315;` |
| `backend/static/components/css/admin_login.css` | 5 | `--navy-card-border: rgba(252, 179, 21, 0.28);` |
| `backend/static/components/js/admin_super_dashboard.js` | 36 | `const gold = '#FCB315';` |
| `backend/static/components/css/admin_layout.css` | 9 | `--campushub-gold: #FCB315;` |
| `backend/static/components/css/admin_header_menus.css` | 138 | `border-bottom: 2px solid #FCB315;` |
| `backend/static/components/js/admin_sales_overview.js` | 96 | `const gold = '#FCB315';` |
| `backend/static/components/css/admin_facility_utilization.css` | 14 | `.facility-utilization-type[data-state="unavailable"] > b::before { content: ''; display: inline-block; width: ` |
| `backend/static/components/css/admin_monitoring.css` | 3 | `--monitor-gold: #FCB315;` |
| `backend/static/components/css/admin_messages.css` | 170 | `background: #FCB315;` |
| `backend/static/components/css/admin_marketplace_overview.css` | 29 | `.dashboard-marketplace .sales-sample-toggle:hover, .dashboard-marketplace .sales-sample-toggle[aria-pressed="t` |
| `backend/static/components/css/admin_products.css` | 3 | `--campushub-gold: #FCB315;` |
| `backend/static/components/css/admin_orders.css` | 4 | `--campushub-gold: #FCB315;` |
| `backend/static/components/css/admin_notifications.css` | 3 | `--campushub-gold: #FCB315;` |
| `backend/static/components/css/admin_roles.css` | 2 | `:root { --roles-navy:#1A1851; --roles-gold:#FCB315; --roles-white:#fff; --roles-soft:#f8fafc; --roles-border:r` |
| `backend/static/components/js/admin_marketplace_analytics.js` | 5 | `const GOLD = '#FCB315';` |
| `backend/static/components/css/admin_reports.css` | 121 | `border-color: #fcb315;` |
| `backend/static/components/css/admin_facility_status.css` | 11 | `.operational-dot--unavailable { background: #FCB315; }` |
| `backend/static/components/css/admin_product_details.css` | 171 | `border: 1px solid #FCB315;` |
| `backend/static/components/css/admin_super_dashboard.css` | 4 | `--overview-gold: #fcb315;` |
| `backend/static/components/css/admin_sellers.css` | 3 | `--campushub-gold: #FCB315;` |
| `backend/static/components/css/admin_settings.css` | 10 | `.settings-nav-item.active { background: #1A1851; color: #FCB315; font-weight: 600; }` |
| `backend/static/components/css/job_order.css` | 19 | `.beu-job-export :focus-visible { outline: 2px solid #FCB315; outline-offset: 2px; }` |
| `backend/static/components/css/admin_sales_overview.css` | 3 | `Clean Flat Minimalist UI Design (Institutional Navy #1A1851 & Gold #FCB315)` |
| `backend/static/components/css/admin_system_status.css` | 112 | `background: #FCB315;` |
| `backend/static/components/css/booking_slip.css` | 34 | `.bk-slip-toolbar a:focus-visible, .bk-slip-toolbar button:focus-visible, .bk-form-toolbar a:focus-visible, .bk` |
| `backend/static/components/css/admin_users.css` | 3 | `--users-gold: #fcb315;` |
| `backend/core/modules/marketplace/static/marketplace/css/bundle_suggestions.css` | 25 | `.bundle-pair--cross-sell .bundle-pair-plus { color: #FCB315; font-size: 21px; font-weight: 600; }` |
| `backend/core/modules/marketplace/static/marketplace/js/admin_marketplace_dashboard.js` | 23 | `backgroundColor: ["#FCB315", "#1A1851", "#1A1851", "#1A1851", "#e5e7eb"],` |
| `backend/core/modules/marketplace/static/marketplace/css/admin_marketplace_dashboard.css` | 2 | `/* Brand Colors: Navy #1A1851, Gold #FCB315, Neutral Light #f8fafc */` |
| `backend/core/modules/facilities/static/facilities/css/admin_facilities_dashboard.css` | 2 | `/* Brand Colors: Navy #1A1851, Gold #FCB315, Neutral Light #f8fafc */` |
| `backend/core/modules/facilities/static/facilities/css/admin_services.css` | 4 | `.service-catalog .facility-status-unavailable, .service-catalog .facility-status-maintenance { color:#1A1851; ` |
| `backend/core/modules/facilities/static/facilities/css/facility_form_controls.css` | 68 | `border: 1px solid #FCB315;` |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 529 | `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColo` |
| `backend/core/modules/reports/dashboard_marketplace.py` | 73 | `colors = ("#1A1851", "#FCB315", "#69717E", "#939AA5", "#BDC2CB", "#E0E3E8")` |
| `backend/core/modules/reports/views.py` | 37 | `CATEGORY_COLORS = ("#1A1851", "#FCB315", "#626781", "#9396ac", "#d5d7e0")` |

3. **Changes made:** replaced 263 case-insensitive hex occurrences and 71 equivalent RGB occurrences, including transparent backgrounds/borders. Shared and module CSS, JavaScript chart fallback colors, web templates, four existing sample SVG illustrations, and two Python chart-palette sources now use the requested web gold. No sample values or records were added. Existing sample assets remain available only where already used; this change does not enable sample dashboard data.
4. **Functions and data flow:** CSS custom properties such as `--campushub-gold`, `--analytics-gold` and `--dashboard-gold` feed existing component styles. For example, `--campushub-gold: #FCB315` produces `rgb(252, 179, 21)` in the browser; `rgba(252, 179, 21, 0.16)` keeps the existing opacity while matching the new accent. Existing Chart.js configuration reads the same custom properties or its matching fallback hex. Category presentation builders in `dashboard_marketplace.py` and `views.py` attach palette colors to real chart results; only those color strings changed. Inputs (orders/categories) and outputs (counts, totals and shares) retain their existing behavior. Replacing every representation was chosen because changing only one root variable would leave hard-coded legacy accents and chart fallbacks inconsistent.
5. **Backend / API behavior:** existing queries, authentication, permissions, URLs, payment/booking workflows and calculations are unchanged. Category chart color metadata uses the new hex; response structure is unchanged.
6. **Database / migration impact:** none. No records, migrations, packages or settings changed. Flutter application sources were excluded; the mobile dashboard checksum was verified unchanged during the replacement.
7. **Verification:** all changed JavaScript files passed Node syntax checks and both changed Python files passed AST parsing. Targeted `git diff --check` passed, with existing Windows line-ending notices only. A case-insensitive scan found no old hex or equivalent RGB values in the searched first-party backend web sources (excluding dependencies, collected files, migrations, uploaded media and logs). Chrome verified the shared root gold, Analytics root gold and active sidebar background at 1440, 768, 390, 320, 844 and 390px: all matched `#FCB315` / `rgb(252, 179, 21)`. Existing responsive navigation assertions also passed in the isolated shell. The initial browser harness stripped a Google Fonts import incorrectly because its URL contained semicolons; fixing that scratch-only stylesheet preparation made the root-token checks pass. This was a harness issue, not a production stylesheet defect. Run `node scratch/web-gold-check.cjs` to repeat; no physical-device/live-auth check was performed. These are presentation checks; the Django business regression suite was not rerun for color-string-only edits.
8. **Limitations / debugging / learning exercise:** hard-refresh web pages with Ctrl+F5 if an old cached stylesheet remains. Production deployments that serve collected assets require their normal `collectstatic`/deployment step; this task does not alter deployment settings. Raster logos and uploaded images were not recolored; their pixels are not source hex strings. Historical docs/research/scratch fixtures retain their recorded colors. Safe exercise: inspect `--analytics-gold` in browser DevTools, confirm `#fcb315`, then inspect an active sidebar item's computed background and confirm `rgb(252, 179, 21)`. Temporarily override the variable in DevTools and refresh to revert without changing a file or production data.

---

# Dashboard reduced palette — 2026-10-05

1. **Cause / Reason**

   Activity types, facility chart series, KPI comparisons, and service states used several unrelated colors. The dashboard now follows the requested CampusHub palette: navy `#1A1851`, gold `#FCB316`, white/light surfaces, neutral chart grays, and light blue `#EAF3FF` for small icon containers.

2. **Exact Files Changed**

   Application files for this change:

   - `backend/static/components/css/admin_dashboard_palette.css` — new scoped palette and component overrides.
   - `backend/templates/dashboard/pages/admin_dashboard.html` — palette scope, stylesheet inclusion, and changed asset cache versions.
   - `backend/static/components/css/admin_dashboard_filter.css` — navy KPI comparisons and gold attention markers.
   - `backend/static/components/css/admin_marketplace_overview.css` — navy marketplace comparisons.
   - `backend/static/components/css/admin_system_status.css` — navy normal service indicators and gold warning/failure indicators.
   - `backend/static/components/js/admin_dashboard.js` — facility chart datasets read the shared palette.
   - `backend/core/modules/reports/views.py` — shared category presentation colors use navy, gold, and neutral grays.

   Verification files updated: `scratch/dashboard-global-review/check-controls.cjs`, `check-system-status.cjs`, `check-ranking.cjs`, and `prepare-ranking-visual.cjs`.

   Verification files added: `scratch/dashboard-global-review/prepare-palette-visual.cjs`, `render-palette.ps1`, and `verify-palette-visual.cjs`. This document is the implementation report. Generated HTML, JSON, screenshots, logs, the existing Bootstrap dependency copy, and browser profiles stay in the scratch review directory.

3. **Changes Made**

   - Every Recent Activities icon uses navy with the same light-blue background.
   - KPI cards remain white with navy values and light-blue icon containers.
   - Healthy service indicators use navy; warnings, failures, and attention indicators use gold markers with readable navy text.
   - Order status labels use navy. Pending, processing, and ready-for-pickup labels have a gold border and a subtle gold background; completed and cancelled labels use a light neutral background.
   - Facility booking chart colors: approved navy, pending gold, completed gray, rejected/cancelled light gray. The visible legends use the same mapping.
   - Facility availability colors: available navy, occupied gray, maintenance gold, blocked light gray. Facility revenue uses a navy line with no gradient fill.
   - Navigation links and secondary actions use navy. The selected menu and primary Apply action retain gold. The secondary View All Activities hover remains navy.
   - Approval icons, empty-state icons, utilization bars, and low-stock values also follow the reduced palette.

4. **How It Works**

   The dashboard main element carries `data-dashboard-palette`. Its CSS variables define the palette, and the final stylesheet overrides existing dashboard colors without changing page structure. Facility Chart.js datasets read those variables, so chart series and CSS legends stay consistent. Status names, counts, trend text, and chart labels remain visible; meaning does not depend on color alone. Changed asset versions prevent cached styles from keeping the old colors.

5. **Backend / API Behavior**

   Queries, totals, completed-and-paid analytics rules, filters, grouping, authorization, and live health checks are unchanged. Only the shared category color metadata in `views.py` changes. No endpoints or response fields were added or removed.

6. **Database / Migration Impact**

   None. No model changes, migrations, or production record updates. Verification uses the existing isolated Django test database.

7. **Tests Performed**

   - 62 existing Django tests passed across `test_dashboard_periods`, `test_dashboard_health`, and `test_dashboard_marketplace`.
   - Existing DOM integration checks passed for global controls, health status, ranking/category rendering, and attention items, including authenticated requests, races, loading, failure, and retry behavior.
   - Headless Chrome checked the complete rendered dashboard at 1600px and 500px. Computed colors verified all eight KPI cards/icons, activity icons, normal and warning order badge states, service state markers, links, selected navigation, facility chart datasets, and matching legends. No JavaScript errors or page overflow.
   - Nine existing analytics browser cases passed: desktop, laptop, medium, mobile, 375px mobile, empty desktop/mobile, loading, and error. The persistent chart footprint, product labels, tooltips, and card alignment were preserved.
   - JavaScript syntax and CSS parsing passed. Desktop and narrow dashboard screenshots were visually reviewed.

   Screenshots: [desktop](../scratch/dashboard-global-review/palette-desktop.png), [narrow layout](../scratch/dashboard-global-review/palette-mobile.png). Screenshots show isolated test records and mocked test health responses; they do not describe the running system's health.

8. **Remaining Limitations**

   The new component overrides are scoped to the dashboard. Other module screens keep their existing styles; the shared category presentation palette also applies wherever that metadata is used. Existing analytics sections, charts, layout, and honest empty states remain intact. No new limitations were introduced to data or booking behavior.

   Reload the dashboard with **Ctrl+F5** to see the current assets immediately.
