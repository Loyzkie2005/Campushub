# Dashboard table scrolling

## 1. Cause / Reason

The user wants Low Stock Products and Recent Orders to remain scrollable while hiding their internal scrollbar tracks and thumbs. This is a visual preference; the existing layout and inventory/order data stay intact.

## 2. Exact Files Changed

| Folder / File | Current line | Nearby code anchor | Change |
| --- | --- | --- | --- |
| `backend/static/components/css/admin_marketplace_overview.css` | 9 | `Keep native table scrolling` | Added scoped hidden-scrollbar rules and a Low Stock focus outline. |
| `backend/templates/dashboard/partials/low_stock_card.html` | 6 | `.low-stock-table-wrap` | Added `tabindex="0"`, `role="region"`, and `aria-labelledby="lowStockTitle"`. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 | `admin_marketplace_overview.css` | Changed the stylesheet version to `20261005-hidden-table-scrollbars`. |
| `CAMPUSHUB_CONTEXT.md` | 13 | `Current scrolling preference` | Saved the accepted scrolling preference for future work. |
| `scratch/dashboard-global-review/check-hidden-scrollbars.cjs` | 1 | `Uses isolated Django render artifacts` | Added a browser verification helper using isolated render fixtures. |
| `docs/dashboard-hidden-scrollbars.md` | 1 | `Dashboard table scrolling` | Added this beginner-friendly change guide. |

Generated review HTML and browser DOM output are local QA artifacts in `scratch/dashboard-global-review`; they are not dashboard data or application code.

## 3. Changes Made

Only the Low Stock and Recent Orders table wrappers inside the global dashboard's Marketplace Analytics section hide scrollbars. No cards, rows, heights, or existing scroll limits were removed. Recent Orders already had keyboard focus and a focus outline; Low Stock now has them too. The main page, category card, and other pages keep their existing scrollbar behavior.

## 4. How It Works

`overflow: auto` keeps native scrolling enabled when content exceeds the wrapper. `scrollbar-width: none` hides the bar in browsers supporting that property. The `::-webkit-scrollbar` rule covers WebKit-based browsers and Chromium fallback behavior.

This differs from `overflow: hidden`, which would prevent ordinary wheel and touch scrolling. No custom JavaScript scroll handler is needed. Mouse-wheel, trackpad, touch-swipe and native keyboard scrolling remain available where the table actually overflows. There is no new height restriction, so a short table may have nothing to scroll.

`tabindex="0"` lets the keyboard's Tab key focus the Low Stock wrapper. Arrow keys then use the browser's native scrolling. The navy focus outline stays visible. `aria-labelledby` gives the scrollable region the card's heading as its accessible name. View All links remain available for the complete lists.

## 5. Backend / API Behavior

Unchanged. The existing Django views, authenticated refresh endpoint, inventory computation, order records, and empty/loading/error states remain intact.

## 6. Database / Migration Impact

None. No database writes or migrations were performed for this change. The render tests use an isolated test database.

## 7. Tests Performed

- Three existing Django dashboard render tests passed, with no system-check issues.
- Two Chrome cases passed: desktop and a 375px content width. Chrome was run without its `--hide-scrollbars` flag, so the application CSS was responsible for hiding the bars.
- Browser checks confirmed `overflow: auto`, hidden scrollbar styling, scrollTop/scrollLeft movement under isolated overflow constraints, keyboard-focusable labeled regions, visible focus outlines, and an unchanged main-page scrollbar rule.
- Isolated constraints were applied only in the review HTML to exercise overflow without adding production records or changing production table dimensions.

Manual check: reload the Dashboard, hover over an overflowing table and use the mouse wheel or trackpad. Tab into the table and use arrow keys. On a phone, swipe inside the overflowing table. Use View All for the complete list.

## 8. Remaining Limitations

Hidden bars remove the visual cue that additional content is available, and their draggable handles are unavailable. Scrolling occurs only if the table overflows. Physical touch gestures and Safari/Firefox were not exercised; they retain native scrolling through standard CSS behavior. No fake orders or inventory were added to demonstrate scrolling.
