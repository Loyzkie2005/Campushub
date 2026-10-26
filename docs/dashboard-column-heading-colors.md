# Dashboard column heading colors

Updated: 2026-10-06.

## 1. Cause / Reason

You requested removing gray from dashboard columns, including Sales share. This change treats that as column heading text and header backgrounds: navy semibold text on white creates a consistent, clearer table header. Existing chart grays, body descriptions and dividers retain their separate purposes.

## 2. Exact Files Changed

Paths are relative to the project root. Current line numbers can change after later edits.

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/static/components/css/admin_dashboard_palette.css` | 14, dashboard column heading comment | Add a dashboard-scoped rule for `thead th` and `.marketplace-product-columns`. |
| `backend/static/components/css/admin_marketplace_overview.css` | 86, `.marketplace-product-columns`; 191, category `thead th` | Replace gray header text with navy; category headings become semibold. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18–19, the two stylesheet links | Update their cache versions to `20261006-navy-columns`. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 65, `columnHeadingStyles`; 82, palette attribute | Measure header color/background/weight and match the production dashboard's palette scope in the preview. |
| `CAMPUSHUB_CONTEXT.md` | 9, learning preference | Preserve the heading choice and debugging documentation preference. |
| `docs/dashboard-column-heading-colors.md` | 1 | This implementation and learning report. |
| `docs/DEBUGGING_GUIDE.md` | 1 | Reusable debugging workflow, troubleshooting and issue-record template. |

The existing preview build also regenerated local HTML/DOM verification files under `scratch/sales-overview-system-test/`. Those files are development artifacts.

## 3. Changes Made

Product, Units sold, Sales, Category, Sales share, Low Stock headers and Recent Orders headers now use navy `#1A1851`, white `#FFFFFF` and semibold `600`. The dashboard-scoped rule also applies to any other table header inside the same dashboard root. Low Stock's light-gray header strip is overridden with white. The existing Sales share label remains unchanged because it was already correct.

No columns, functions, records or sections were moved or removed. Sizes, alignment, scrolling and the donut hover behavior remain in place.

## 4. How It Works

The dashboard's `<main>` element at template line 36 has `data-dashboard-palette`. CSS selects only headings beneath that element. A column heading is either a table header inside `<thead>` or the existing product-list heading row. The shared palette rule gives both structures the same presentation, including after JavaScript replaces rows during refresh or sample switching.

```css
[data-dashboard-palette] thead th,
[data-dashboard-palette] .marketplace-product-columns {
    color: var(--dashboard-navy) !important; /* Text uses the existing brand token. */
    background: var(--dashboard-white) !important; /* Remove gray header strips. */
    font-weight: 600 !important; /* Semibold. */
}
```

The existing component styles already contain important heading declarations and legacy table styling. A narrowly scoped palette override establishes the common heading policy without changing each unrelated module stylesheet. The marketplace component's own heading rules are also updated so they no longer explicitly request gray.

| Function / rule | Input | Output / role |
| --- | --- | --- |
| `admin_dashboard_page(request)`, Reports `views.py:914` | Authenticated request and filters | Supplies the dashboard context and renders the page. Unchanged. |
| Dashboard templates | Context values | Render real headings and rows. Unchanged. |
| `render(payload, sampleOnly)`, `admin_dashboard_filter.js:298` | Existing API or sample payload | Updates dashboard elements; their styles still come from the same selectors. Unchanged. |
| New palette rule | Matching header elements | Applies navy text, white background and weight 600. |
| Preview `measure()`, preview script line 4 | Rendered DOM and computed styles | Adds header measurements to the existing QA JSON. |

Data flow remains database → Django aggregation/context or API → template/JavaScript elements → browser CSS. Color changes affect the final presentation, not the input records or aggregation results.

## 5. Backend / API Behavior

Unchanged. No requests, authentication, permissions, filters or payload fields were added or removed.

## 6. Database / Migration Impact

None. No schema or live records changed; no migration is required.

## 7. Tests Performed

- Chrome sample and return-to-real preview cases passed: all inspected heading elements computed to navy `rgb(26, 24, 81)`, white `rgb(255, 255, 255)` and weight `600`.
- Checked 16 heading elements in sample mode and 15 in real mode, covering products, categories, low stock and recent orders. The operations tables came from the real rendered fixture context but were hidden in this isolated preview; their computed styles were checked, not their visible full-page layout.
- No browser errors; analytics cards fit and retained their heights.
- Both updated stylesheets parsed successfully. No backend tests were repeated for these CSS-only behavior changes.

### Debugging and practice

If a heading still looks gray, use Ctrl+F5, inspect its Computed color in browser Developer Tools, and check that the new stylesheet versions loaded. A crossed-out declaration means another CSS rule wins; investigate that rule before adding another override. See [the debugging guide](DEBUGGING_GUIDE.md).

Safe exercise: select Sales share in Developer Tools and temporarily disable the winning `color` declaration. Observe which rule becomes active. Re-enable it and confirm navy returns. These Developer Tools changes are temporary and disappear on reload; do not save another code change for this exercise.

## 8. Remaining Limitations

The rule applies to heading text and header surfaces, not every gray body label, border or chart segment. It is scoped to dashboards with `data-dashboard-palette`, not all module tables across the system. Real-data product units and sales still use the existing combined heading; separate sample headings are preserved. Font appearance can vary by device.
