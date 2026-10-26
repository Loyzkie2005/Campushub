# Make Sales Overview increases easier to see

Superseded: the current comparison color is gray with the same stronger size/weight. See [the current Marketplace Analytics guide](marketplace-analytics-samples-gray.md). This report records the earlier dark-green refinement.

## 1. Cause / Reason

You reported that the green comparison text looked too faint. It used the same small 12px regular text as the period description. Darkening the green and increasing its size/weight makes the change easier to identify.

## 2. Exact Files Changed

| Folder / file | Current line | Nearby anchor | Change |
| --- | --- | --- | --- |
| `backend/static/components/css/admin_marketplace_overview.css` | 45 | `.sales-comparison-change` | Changed positive increases to dark green `#166534`, 13px and semibold 600. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 | marketplace stylesheet link | Changed its asset version to `20261005-sales-green-contrast`, so browsers fetch the new styling. |
| `CAMPUSHUB_CONTEXT.md` | 13 | `Current Sales Overview color exception` | Saved the stronger color, size and weight for future work. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 13 | `changeColors` | Extended the existing browser review to capture computed font weight and size too. |
| `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs` | 5 | `scenarios` | Allows selecting relevant review cases; verifies the new dark green, 600 weight and 13px size. |
| `docs/sales-overview-green-changes.md` | 3 | latest refinement note | Links the earlier color implementation to this visibility refinement. |
| This document | 1 | title | Beginner-friendly implementation report. |

The offline previews were regenerated, plus the desktop, mobile and 320px review screenshots/DOM reports under `scratch/sales-overview-system-test`.

## 3. Changes Made

Only the positive increase, such as “↑ 333.3%”, receives the stronger styling. The following period wording stays gray and regular. The three main KPI values remain navy. No sections were added, moved or removed.

## 4. How It Works

The existing comparison formatter already wraps the positive portion in a span. Its CSS now uses:

```css
color: #166534;
font-size: 13px;
font-weight: 600;
```

`color` darkens the green, `font-size` increases it slightly, and `font-weight` makes it semibold. The new green has a calculated 7.13:1 contrast ratio against the white card.

Press Ctrl+F5 on the Super Admin dashboard, then Show sample. Compare the stronger green increase with the muted period description. Try a narrow browser window; the comparison can wrap inside the card.

## 5. Backend / API Behavior

No backend, API, permission, metric classification or calculation changed. The same styling applies to actual positive changes and explicitly labeled sample values.

## 6. Database / Migration Impact

No database writes or migrations. Orders, payments and stock remain untouched.

## 7. Tests Performed

Three actual Chrome checks passed: desktop, mobile layout and a 320px frame. Computed colors are dark green `rgb(22, 101, 52)` for the increase and gray `rgb(98, 103, 129)` for the period. Computed increase text is 13px with weight 600. The existing graph values, keyboard tooltip and overflow checks passed too. The desktop screenshot was visually inspected. No backend test rerun was needed for this CSS-only refinement.

## 8. Remaining Limitations

This affects positive Sales Overview comparisons only. Actual zero/no-change states remain neutral. Physical devices and Firefox/Safari were not separately tested; screen appearance can vary slightly with font rendering.
