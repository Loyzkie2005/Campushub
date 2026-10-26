# Sales Overview test values and preview

Later update: sample mode is now also available inside the normal Super Admin Sales Overview card. See [the in-dashboard sample guide](sales-overview-in-dashboard-sample.md). This report describes the original separate preview.

## 1. Cause / Reason

You requested values or placeholders to test Sales Overview. A clearly labeled, isolated test preview lets you inspect the real UI and calculations while retaining honest live metrics. No fake totals were inserted into the live dashboard. The optional location question had no reply before completion, so the stated separate-preview default was used.

## 2. Exact Files Changed

| Folder / file | Current line | Nearby anchor | Change |
| --- | --- | --- | --- |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 68 | `test_sales_overview_system_preview_values_and_grouping` | Added a scenario using actual order records in the isolated Django test database. Existing API and rendering calculate all visible values. |
| Same file | 71 | `daily_cases` | Added varied daily sales, an honest zero-sales day, and previous-period records. Completed-unpaid and pending-paid records test the eligibility rule. |
| `scratch/sales-overview-system-test/build-preview.cjs` | 1 | actual Django test renders | Added the builder for six offline HTML cases, using the real card, existing styles and Chart.js/Sales Overview script. Adds a visible test label, populated/empty links and grouping navigation. |
| `scratch/sales-overview-system-test/check-preview.cjs` | 5 | `measure` | Added browser review measurements and assertions for totals, chart types, grouping, tooltip/keyboard feedback, empty state and overflow. |
| `scratch/sales-overview-system-test/render-preview.ps1` | 1 | `taskReviewDirectory` | Added headless Chrome rendering of the six cases plus mobile. |
| `scratch/sales-overview-system-test/README.md` | 1 | document title | Added beginner-friendly open/regenerate/testing instructions. |
| `docs/sales-overview-system-test-preview.md` | 1 | document title | This guide. |

Generated files include `scratch/sales-overview-system-test/index.html`, the six `populated/empty-daily/weekly/monthly.html` previews, matching Django source HTML and JSON payloads, browser reports, screenshots and `django-tests.log`. `index.html` opens the populated Daily case.

## 3. Changes Made

The existing Sales Overview component now has a separate test preview with meaningful values and an empty case. No application template, runtime JavaScript, route, production setting or live dashboard placeholder was changed. This is a testing addition.

The populated preview contains ₱3,900.00 Marketplace Sales, 18 Completed Orders and ₱216.67 Average Order Value. They are calculated from the test records, not hardcoded into the component. Its previous equivalent period has ₱900 from nine qualifying orders, so the existing comparison text is exercised too.

## 4. How It Works

The Django test creates 18 qualifying order records across six active days within 2026-09-29 through 2026-10-05. One day has no orders. It also creates previous-period records and two excluded transactions: completed but unpaid, and paid but pending.

The test calls the existing Super Admin API and dashboard view for Daily, Weekly and Monthly groupings, exporting their actual data and HTML. The preview builder extracts the real Sales Overview card and chart JSON and embeds the existing styles and chart code. All three groupings reconcile to the same totals.

The No sales scenario uses 2026-09-01 through 2026-09-07, where the test database has no qualifying sales. It retains the real zero chart baseline and empty message. Grouping changes navigate between pre-rendered files rather than querying a live server. Hover tooltips and keyboard inspection use the existing chart code.

Open `scratch/sales-overview-system-test/index.html` in a browser. Choose With sales or No sales, then Daily/Weekly/Monthly. Focus the chart and press arrows/Home/End to check exact values. No local web server is required.

## 5. Backend / API Behavior

Reuses the existing `DashboardMarketplaceTests.order` helper, completed-and-paid analytics query, dashboard period logic, API and template. The application endpoint is unchanged. The exported offline files make no live API requests and do not authenticate as your live account.

## 6. Database / Migration Impact

Records are created only inside the isolated Django test database and rolled back by the test framework. No live database records, migrations, checkout stock reservations or actual payment records were changed. The test database may be retained by `--keepdb`, as with the project's other tests.

## 7. Tests Performed

Passed the new Django test for all six populated/empty grouping combinations, exact totals, previous-period revenue and exclusion of nonqualifying orders. Passed seven actual Chrome checks: the six cases and mobile. Verified navy sales bars plus gold orders line, actual totals, empty baselines, correct grouping, two-value tooltip, keyboard descriptions, visible test label and no horizontal overflow or JavaScript errors. The desktop preview was visually inspected.

Evidence: `scratch/sales-overview-system-test/django-tests.log`, the seven `*.dom.html` reports and matching PNG screenshots. No broad backend rerun was needed because runtime application logic was not changed.

## 8. Remaining Limitations

This preview is separate from `127.0.0.1:8000/admin-dashboard/`; it does not add test orders to your live database. Dates are fixed to the documented scenario. It tests analytics rendering and eligibility, not checkout, cash collection or an actual order lifecycle. Firefox/Safari and physical devices were not separately tested. Offline fonts fall back to the system sans-serif if Montserrat is unavailable. Keep all six scenario HTML files in the same folder for grouping navigation.
