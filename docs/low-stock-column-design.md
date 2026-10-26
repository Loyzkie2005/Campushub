# Low Stock Products column refinement

## 1. Cause / Reason

The user approved refining the Low Stock Products columns to fit the card, while keeping its existing flat design. Percentage widths previously assigned 44% of the table to the two numeric columns even on wide cards, reducing room for product names unnecessarily.

## 2. Exact Files Changed

| Folder / File | Current line | Nearby anchor | Change |
| --- | --- | --- | --- |
| `backend/static/components/css/admin_dashboard_filter.css` | 95 | `.low-stock-table-wrap` | Explicit full-width wrapper/table, compact columns, aligned headings/values, matching cell padding and name wrapping. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 16 | `admin_dashboard_filter.css` | Stylesheet version changed to `20261005-stock-column-fit` so browsers fetch the new rules. |
| `scratch/dashboard-global-review/prepare-low-stock-visual.cjs` | 17 | `tableFillsWrapper` | Added browser measurements for full table width, equal numeric columns, and header/value alignment. |
| `scratch/dashboard-global-review/verify-low-stock-visual.cjs` | 9 | `if (!['loading', 'error']...)` | Added checks for those measurements in visible table states. |
| `CAMPUSHUB_CONTEXT.md` | 15 | `Current Low Stock table design` | Saved the accepted column treatment. |
| `docs/low-stock-column-design.md` | 1 | This guide | Documents this implementation and how to check it. |

Review HTML, DOM output, and screenshots were regenerated in `scratch/dashboard-global-review`. These use isolated test records, not live inventory.

## 3. Changes Made

- Replaced Product's 56% width with `auto`, so it takes the remaining space.
- Replaced both 22% numeric widths with equal 80px widths (CSS line 100).
- Explicitly right-aligned numeric headers and values and kept tabular numerals for easy scanning (line 101).
- Made header padding and body padding consistent within their respective rows and vertically centered the cells (lines 97, 102, 104).
- Allowed full product names to wrap instead of retaining the old clipping/ellipsis behavior (line 107). Existing variant text already wraps.

The title, View All link, image sizes, navy values, light table header, border, card position, padding, actual records, and hidden-scrollbar behavior remain intact. No new icons, fake images, or placeholder records were added.

## 4. How It Works

`table-layout: fixed` lets the browser use the header's specified column widths. Each numeric column takes 80px; Product receives the remainder of the table's 100% width. This makes the numeric columns compact even on wide cards. Matching alignment and cell padding keep each number under its heading. Longer product and variant names wrap inside Product's available space.

## 5. Backend / API Behavior

Unchanged. Inventory calculations, variants, thresholds, filtering, refresh, actual product images, detail links, View All, and loading/error/Retry continue through the existing Django implementation. No backend or JavaScript application logic was changed.

## 6. Database / Migration Impact

None. No records were created, updated, or deleted for this visual refinement. No migrations are needed.

## 7. Tests Performed

- Six isolated Chrome card cases passed: desktop, mobile, 375px content width, empty, loading, and error.
- Visible table cases confirmed full wrapper width, fitting cells, equal compact numeric columns, right-aligned headings/values and matching column edges.
- Nine integrated Marketplace Analytics browser cases passed: desktop, empty desktop, laptop, medium, mobile, small mobile, empty mobile, loading, and error. Existing card placement, responsive stacking, 50/50 Categories/Orders row, and chart area remained intact.
- CSS parsing and tracked-template whitespace checks passed.
- Desktop and small-screen card screenshots were visually inspected. Screenshots contain isolated test records rather than live product names.

Manual check: reload Dashboard and inspect Low Stock Products below Top Selling Products. Product should have the most room. Available and Threshold should have equal widths with right-aligned headings and numbers. Resize to a narrow screen; longer names should wrap without widening the page. View All and inventory refresh should behave as before.

## 8. Remaining Limitations

Long product/variant names can increase row height on narrow screens. The two numeric columns reserve 160px together, so extremely narrow cards may require the existing scrollable wrapper. Browser checks were performed in Chrome; Firefox/Safari were not exercised in this task. No full backend test suite was rerun for this CSS-only behavior change.
