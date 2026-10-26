# Donut segment hover zoom — learning guide

## 1. Cause / Reason

You requested a zoom effect when pointing at the category donut. The existing interaction already identified the category and showed its sales and Sales share. This change makes the selected segment grow by 5.5%, while keeping the donut frame, table and card dimensions steady.

The UI/UX Pro Max skill's targeted interaction guidance recommends supporting tapping and respecting reduced-motion settings. The same effect therefore works with the existing tap and keyboard-focus handlers; reduced-motion users receive an immediate size change without animation.

## 2. Exact Files Changed

Paths are relative to the project root. Current line numbers may shift after subsequent edits.

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/static/components/js/admin_dashboard_filter.js` | 31, `activeCategorySegment`; 32, `hideCategoryTooltip()`; 37, `showCategoryTooltip()`; 51, `categoryAtPointer()` | Track one selected SVG circle, clear its class on dismissal, and retain selection over its enlarged outer edge. |
| `backend/static/components/css/admin_marketplace_overview.css` | 177, `[data-category-segments] circle` | Define a centered transform, a 160ms transition, scale `1.055` for `.is-active`, and a reduced-motion override. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 and 563, stylesheet and script links | Set both affected asset versions to `20261005-donut-zoom`. |
| `scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` | 53, `circle.is-active` assertions inside `checkCategoryTooltip()` | Verify only the correct segment is active, its enlarged edge remains active, and Escape clears it. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 4, `measure()`; 19–32, zoom inspection | Record active count, computed scale and transition. Finish transitions only inside the virtual-time preview inspection so the final computed state can be checked deterministically. |
| `CAMPUSHUB_CONTEXT.md` | 11, current category donut interaction | Preserve the accepted behavior for future work. |
| `docs/category-donut-hover-zoom.md` | 1 | This explanation and implementation report. |

Local preview HTML and browser verification artifacts were also regenerated under `scratch/sales-overview-system-test/`. They are not application data or deployed templates.

## 3. Changes Made

- Added the `is-active` class to the hovered, tapped or focused segment.
- Remove the previous segment's class when selecting another category. Remove the active class when the tooltip is dismissed.
- Scale only the selected circle around the SVG's center. Do not change the card width/height or donut's allocated space.
- Extend hit detection to the active segment's enlarged outer edge to avoid flickering as the cursor moves outward.
- Retain category names, sales, Sales share, colors, table and existing empty states.

No application functions, chart sections, database fields or routes were removed or moved.

## 4. How It Works

### Function inputs and outputs

| Function / rule | Input | Output / responsibility |
| --- | --- | --- |
| `categoryAtPointer(event)` | Pointer coordinates and the existing segment metadata | Returns the category circle at that angle, or no match for the center/outside area. An outer-edge match is accepted only for the already active segment. |
| `showCategoryTooltip(segment, x, y)` | Matching circle and pointer/focus coordinates | Selects that circle, applies `is-active`, and fills and positions the existing tooltip. |
| `hideCategoryTooltip()` | Existing dismissal events such as Escape, leaving the chart, outside tap, resize or data refresh | Hides the tooltip, removes the active class and resets the stored segment reference. |
| CSS circle rules | Whether the circle has `is-active`, plus the user's motion preference | Displays its normal scale or `1.055`; animates normally and skips the transition under reduced motion. |
| Preview `measure()` | Rendered browser elements | Collects sizing and computed-style results for development verification. It never updates live sales records. |

### Data flow

The existing Django aggregation supplies category sales, percentage and segment ranges to the template/API. Pointer position is converted into a donut angle, which identifies a segment using those ranges. JavaScript then applies a presentation class and populates the tooltip from that segment's existing metadata. CSS renders the zoom. The underlying sales totals and percentages are not recalculated by the animation.

The ring uses a `240 × 240` SVG coordinate system, radius `88` and stroke width `38`. Its normal outer radius is `107`; scaling by `1.055` makes that approximately `112.9`. The JavaScript outer bound of `113` allows the pointer to stay over the enlarged edge. The enlarged ring still fits inside the SVG's half-width of `120`.

### Annotated example

```css
[data-category-segments] circle {
    transform-box: view-box;          /* Measure the origin against the SVG frame. */
    transform-origin: 50% 50%;        /* Grow from the donut's center. */
    transition: transform 160ms ease-out; /* Smoothly approach the selected size. */
}
[data-category-segments] circle.is-active {
    transform: scale(1.055);          /* 105.5% of the normal size. */
}
```

The selector matches category circles in both initial real-data rendering and dynamically created sample/API rendering. Reusing the tooltip selection avoids a second independent hover system. Transform changes affect the drawing rather than rearranging the surrounding layout.

## 5. Backend / API Behavior

Unchanged. Existing authentication, analytics aggregation and global date filtering still apply. Daily/Weekly/Monthly still changes only Sales Trend grouping. No additional API requests are made to animate the donut.

## 6. Database / Migration Impact

None. No schema, models, migrations or live records were changed. Verification used existing isolated preview fixtures.

## 7. Tests Performed

- Production JavaScript syntax check passed.
- Existing integrated frontend verification passed: correct tooltip/category activation, enlarged outer-edge behavior, keyboard/Escape dismissal, sample switching, restoration, independent Sales Trend grouping, error/retry and refresh recovery.
- The stylesheet parsed successfully.
- Chrome normal/reduced-motion previews confirmed scale `1.055`, transition durations `0.16s` / `0s`, exactly one active segment, stable card sizes and no card overflow. The virtual-time preview finishes its CSS transitions before measuring because virtual time can pause compositor animation.
- A separate Chrome check dispatched an actual browser mouse movement and waited in real time. Electronics enlarged, the tooltip showed Sales `₱750.00` and Sales share `19.2%`, the category card stayed `320px` high, and moving away cleared selection and the tooltip. The screenshot was visually inspected: `scratch/sales-overview-system-test/donut-zoom-real-hover.png`.
- Backend tests were not repeated for this presentation-only change.

To verify in the system: reload with Ctrl+F5, hover a populated donut segment and move around its edge. Move away or press Escape to reset. Tab to a segment to check keyboard behavior. If the database has no completed paid sales, use the existing Show sample control; no live transactions are inserted by that control.

### Safe practice exercise

1. Find CSS line 177 and change only `160ms` to `240ms` locally.
2. Save and reload with Ctrl+F5. Hover several segments and compare how quickly each grows and returns.
3. Check Developer Tools → Computed → `transition-duration`: it should read `0.24s`. Under an emulated reduced-motion preference it should remain `0s`.
4. Restore `160ms` and verify the normal duration returns to `0.16s`.

This teaches the difference between the visual target (`scale`) and the animation speed (`transition`). Leave scale and hit-detection bounds alone during this exercise: they work together, so changing only the scale could introduce edge flicker or clipping.

## 8. Remaining Limitations

The effect is intentionally subtle and requires category sales data to display the donut. It enlarges one segment rather than the entire chart. Physical touch devices were not tested; they use the existing pointer-down path. The card remains fixed in size, and the tooltip temporarily overlaps nearby chart/table content while inspecting a category.
