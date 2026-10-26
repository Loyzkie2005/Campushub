# Product headings and dashboard folders

## 1. Cause / Reason

The Product, Units sold and Sales headings needed a clearer weight. Semibold (`600`) distinguishes a column heading from secondary text without competing with bold numeric values. The existing 12px size, muted text color and alignment remain appropriate for the compact card.

You also asked whether the dashboard folder belongs inside a module. The dashboard is a feature, but `backend/templates/dashboard/` is a template namespace, not a registered Django app. Its Python logic already belongs to the Reports module. Keep this structure for now; moving templates would be an optional organization refactor rather than a functionality fix.

## 2. Exact Files Changed

Paths are relative to the project root. Line numbers refer to this change and can shift after later edits.

| File | Line / nearby anchor | Purpose |
| --- | --- | --- |
| `backend/static/components/css/admin_marketplace_overview.css` | 86, `.marketplace-product-columns` | Add `font-weight: 600` to the column heading row. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18, `admin_marketplace_overview.css` | Update the stylesheet version to `20261005-product-headings` so the browser requests the new CSS. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 57, `productHeadingWeights` inside `measure()` | Record computed heading weights in the existing local browser preview. |
| `docs/product-headings-and-dashboard-folders.md` | 1, this document | Explain the change, folder ownership and a safe practice exercise. |

The preview tools also regenerated local HTML artifacts in `scratch/sales-overview-system-test/`. These files are development previews, not application templates.

## 3. Changes Made

- Added one font-weight declaration to the shared product heading selector.
- Updated the dashboard's CSS cache version.
- Added a browser measurement to check the resulting weight.
- No folders were moved. No products, order values, labels or column arrangements were changed.

The sample layout has three headings: Product, Units sold and Sales. The existing real-data layout has Product and a combined Units Sold / Sales heading. Both inherit the same semibold rule.

## 4. How It Works

### Understand the folders

| Location | What it contains |
| --- | --- |
| `backend/core/modules/reports/` | The registered Django Reports app: Python views, reporting and dashboard aggregation helpers. |
| `backend/templates/dashboard/pages/` | Full dashboard HTML page templates. |
| `backend/templates/dashboard/partials/` | Reusable pieces of dashboard HTML, such as analytics cards. |
| `backend/static/components/css/` | Styles loaded by those templates. |

`ReportsModuleConfig` in `backend/core/modules/reports/apps.py:4` registers the app as `modules.reports`. `core/settings.py:101` enables it. The `TEMPLATES` configuration also searches the shared `backend/templates/` directory and enables app template discovery through `APP_DIRS`.

It would be possible to put the dashboard templates under `backend/core/modules/reports/templates/dashboard/` while keeping the `dashboard/...` template names. That requires auditing template discovery, duplicate names, includes and all role-specific dashboard routes. There is no need to perform that refactor for a font change. If you later request it, move the files with their references verified rather than creating another dashboard app solely to hold HTML.

### Functions, inputs and outputs

| Function / rule | Input | Output / responsibility |
| --- | --- | --- |
| `admin_dashboard_page(request)`, `modules/reports/views.py:914` | Authenticated request and dashboard filters | Builds the appropriate dashboard context and renders the correct page for the user's role. The Super Admin render uses `dashboard/pages/admin_dashboard.html` at line 1529. |
| Django template rendering | Dashboard context containing product summaries | Creates heading spans and real product rows in `dashboard/partials/marketplace_analytics.html:13`. |
| `.marketplace-product-columns` CSS rule | Elements matching that class | Applies 12px, semibold heading text. The child spans inherit the weight, including headings inserted for sample mode. |
| `measure()`, preview script line 4 | The rendered browser DOM | Collects computed styles and sizing into the hidden `qa-results` JSON used for verification. It does not change production analytics. |

Data flows from the existing Django dashboard view into the HTML template. The browser loads the stylesheet and applies the heading rule to the rendered elements. The existing sample switch can replace the heading spans; their parent keeps the same class, so they receive the same style. Changing CSS affects presentation rather than database data.

### Small annotated example

```css
.marketplace-product-columns {
    font-size: 12px; /* Keep headings compact. */
    font-weight: 600; /* Semibold: stronger than regular 400. */
}
```

This is an excerpt of the existing selector, not a second rule you need to paste. `400` generally means regular, `600` semibold and `700` bold; the appearance also depends on the loaded font. Putting the weight on the shared parent avoids repeating declarations on every heading or maintaining different rules for sample and real data.

## 5. Backend / API Behavior

Unchanged. The dashboard still uses the Reports module and existing permission checks. Product rankings, units sold and revenue still come from the existing analytics logic. This change does not add a route, request parameter or API response field.

## 6. Database / Migration Impact

None. No models, records, schema or migrations were changed. Verification used existing isolated preview fixtures and did not insert live orders.

## 7. Tests Performed

- Rebuilt local previews using the existing rendered Django fixtures and current CSS/JavaScript.
- Checked two headless Chrome scenarios: sample mode and returning to real mode. All heading spans computed to `font-weight: 600`; rows and cards fit without horizontal overflow; no browser errors were recorded.
- Parsed the updated stylesheet successfully with the existing CSS parser.
- Backend tests were not repeated because this change only affects font styling and asset caching.

To check in the system, reload `/admin-dashboard/`, use Ctrl+F5 if needed and inspect Top Best-Selling Products. Use Show sample to see all three separate column headings. In browser Developer Tools, select a heading span and check Computed → font-weight: `600`.

### Safe practice exercise

1. Locate `.marketplace-product-columns` at CSS line 86. Change only its `font-weight` from `600` to `400` locally.
2. Save, reload with Ctrl+F5 and compare the heading against the product names and numbers. Inspect its computed weight to verify that the change applied.
3. Restore `600`, save and reload again. Confirm the computed weight returns to `600`.

This teaches the connection between a CSS selector, an inherited property and the actual browser result. Do not change database records for this exercise. If nothing changes, first check that you edited the matching selector and that the browser loaded the current stylesheet.

## 8. Remaining Limitations

The real-data layout still uses its existing combined Units Sold / Sales heading. Separating that layout into three columns would require a separate markup/layout change. The real-mode preview used an empty dataset, so its heading weight was inspected while the headings were hidden; the sample-mode headings were visible. Font rendering can vary slightly by device or available font. Dashboard folder reorganization was discussed only and was not performed.
