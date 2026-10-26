# Top Best-Selling Products: sample photo layout

## Layout recovery — 2026-10-06 (current implementation)

The original implementation report below is historical. This update restores its missing stylesheet rules and the later accepted stacked layout.

### 1. Cause / Reason

Confirmed: the current marketplace stylesheet lacked the sample button, five-column sample rows, photo sprite and compact right-column rules that the existing JavaScript still used. Five sample row elements were being placed in a two-column grid. This caused wrapped names/prices, invisible photos and a native-looking button. The missing height rules let the product card grow and stretch Sales Overview into a large blank area. The earlier working offline render contained these rules. We cannot establish which edit removed them.

The pasted chat timeout log is a separate service issue; it does not explain these CSS failures. See [the health-check guide](dashboard-system-status-5.md).

### 2. Exact Files Changed

| File | Current line / code anchor | Purpose |
| --- | --- | --- |
| `backend/static/components/css/admin_marketplace_overview.css` | 9 `.dashboard-marketplace-grid`; 10 `.dashboard-marketplace-side` | Restore the desktop left/right layout and stable product/category heights. |
| Same stylesheet | 26 `.sales-sample-toggle`; 101 `Photo mockup preview`; 109 `.marketplace-sample-thumbnail` | Restore the button, five-column photo rows and existing bundled sprite. |
| Same stylesheet | 138 `.recent-orders-table`; 204 `Compact right column`; 261 `Match Sales Overview`; 323 `Preserve readable` | Restore compact cards, desktop chart filling, and current seven-column recent-order sizing/alignment. |
| Same stylesheet | 174 `.marketplace-category-tooltip`; 177 `[data-category-segments] circle` | Restore the existing tooltip and segment-hover zoom presentation. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 `admin_marketplace_overview.css` | Set cache version to `20261006-marketplace-layout-recovery` so browsers fetch the repaired stylesheet. |
| `docs/top-products-sample-photo-layout.md` | This update | Cause, current locations, checks and learning exercise. |
| `docs/dashboard-analytics-operations-update.md` | Recent Orders file table | Refresh stylesheet locations/cache-version notes. |
| `scratch/dashboard-global-review/restore-marketplace-css.cjs` | 1, recovery helper | Extract local sprite reference from the prior component snapshot and preserve current table sizing. A one-time recovery artifact, not an application dependency. |
| `scratch/dashboard-global-review/check-layout-recovery.cjs` | 1, Chrome capture loop | Capture current renders for the seven existing browser verification scenarios. |

Scratch recovery/capture scripts and regenerated HTML/PNG/DOM files live under `scratch/dashboard-global-review/` and `scratch/sales-overview-system-test/`. They are verification artifacts rather than application code.

### 3. Changes Made

Restored the scoped marketplace component stylesheet from the earlier working component rules, keeping the current 760px minimum Recent Orders table width in both populated and empty states. Text/date cells align left, totals right and status cells center. Sample rows show rank, photo, product details, units and sales. The right column keeps Top Best-Selling Products above Sales by Product Categories. Smaller screens stack the columns. Internal scrolling remains available with hidden scrollbar tracks and keyboard focus.

### 4. How It Works

The existing `render(payload, sampleOnly)` function in `backend/static/components/js/admin_dashboard_filter.js:298` receives the dashboard payload and a boolean indicating sample-only rendering. Its product branch at line 328 creates the sample rows and marks the card with `data-product-sample`. CSS uses that attribute to select the sample grid; it does not calculate quantities or revenue. The real-data branch and sample restoration continue using the existing code.

Data flow: Django records or explicitly selected UI sample fixture → existing JavaScript renderer → DOM elements/classes → component CSS → browser layout. The sprite background displays one photo region per rank, using the existing PNG asset. No new images or JavaScript behavior were added.

```css
/* Five tracks correspond to rank, photo, details, units and sales. */
grid-template-columns: 14px 36px minmax(0, 1fr) 54px 70px;
/* The details track takes remaining space and may shrink without overflowing. */
```

The container queries respond to the card's available width, rather than assuming that every desktop browser has a wide right-hand column. Stable right-card sizes prevent sample/empty switches from changing the whole dashboard height.

### 5. Backend / API Behavior

No analytics query, endpoint, ranking limit or sample fixture changed. Daily/Weekly/Monthly still changes only Sales Trend grouping; it leaves the KPI totals, products and categories unchanged. Global date filtering and Refresh keep their existing behavior. No sample records are inserted into the live database.

### 6. Database / Migration Impact

None. No models, migrations, production orders, inventory or product images changed. Verification used Django's separate test database.

### 7. Tests Performed

- Seven targeted Django tests passed: six service-health tests and the marketplace fixture/grouping/export test. System checks reported no issues.
- Existing JavaScript integration check passed: grouping isolation, preserved product/category DOM, sample switching/restoration, no extra sample API requests and refresh/error recovery.
- Seven actual headless Chrome scenarios passed: Daily, Weekly, Monthly, Use real data, refresh exit, 500px viewport and 320px content frame. Assertions cover stable heights, card/row fit, five photo positions, donut sizing, values, keyboard chart inspection and no JavaScript errors.
- Inspected the regenerated desktop screenshot visually. Screenshot: `scratch/sales-overview-system-test/in-dashboard-daily.png`.
- CSS parser accepted the recovered rules. The offline preview embeds the existing sprite; application CSS points to the bundled static PNG.
- Live Django static requests returned HTTP 200 for the repaired stylesheet and photo sprite. The served CSS contains the restored sample button, local image reference and compact row rules. Git whitespace validation passed for the selected changed paths.

Manual verification: press **Ctrl+F5** on the dashboard, select **Show sample**, check the styled button/photos and numeric columns, change chart grouping, then select **Use real data**. Resize the browser and scroll the product list if needed. The real empty state should return without a tall product card.

Debugging: if a photo or button loses its styling again, inspect its classes/data attribute and matching stylesheet rule first. In DevTools Network, confirm the marketplace CSS URL has the recovery version and a successful response. If the response still lacks the rules, check which working copy/static directory Django serves before editing the renderer. Do not clear order data to solve a CSS problem.

Safe practice exercise: temporarily change only the sample grid's `gap: 6px` to `8px` in DevTools Styles. Observe that spacing changes but units and sales remain unchanged. Test a narrow width, then reload to discard the experiment. This teaches that CSS controls presentation, while the renderer/backend provide data.

### 8. Remaining Limitations

The authenticated live dashboard was not driven interactively; browser checks used fresh actual Django test renders with the current local CSS/JavaScript. Compact lists may require internal scrolling for five rows or long names. A 500px viewport and 320px content frame were tested, not a 320px device viewport. Photos remain sample-only, as previously requested.

---

## 1. Cause / Reason

The user approved building the pictured product card in sample mode first. The preview now has small product photos and separate Units sold and Sales columns, making each number easier to understand. The existing real-data layout remains available.

## 2. Exact Files Changed

Paths are relative to the CampusHub project folder. Line numbers describe this implementation; the anchors help you find the code later if those numbers move.

| Folder / file | Line / nearby anchor | What changed |
| --- | --- | --- |
| `backend/static/components/js/admin_dashboard_filter.js` | 252, `const productCard` inside `render` | Sample-only card marker, three column labels, five photo/rank rows. |
| Same JavaScript file | 385, `breakdownSnapshot.contents`; 394, sample event exit | Saves/restores original heading nodes along with existing real rows; removes sample styling on exit. |
| `backend/static/components/css/admin_marketplace_overview.css` | 101, `Photo mockup preview` | White flat layout, aligned numeric columns, compact photos, navy numbers, row spacing and narrow-card rules. |
| `backend/static/components/images/samples/top-products-sprite.png` | Image file; no code line | Added one generated photo sheet: hoodie, latte, notebook, tote and USB drive. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 and 563, CSS/JavaScript asset URLs | Updated cache versions so the browser loads the new styles and renderer. |
| `CAMPUSHUB_CONTEXT.md` | 13, `Current Top Best-Selling Products sample design` | Remembers that this design currently applies only to sample mode. |
| `docs/top-best-selling-title-design.md` | 3, `Update` | Links the earlier title-only report to this later implementation. |
| `docs/top-products-sample-photo-layout.md` | 1 | Added this learning guide. |
| `scratch/sales-overview-system-test/build-preview.cjs` | 8, `sampleSprite` | Bundles the photo sheet into the offline preview, so it works without a server. |
| `scratch/sales-overview-system-test/check-in-dashboard-sample.cjs` | 33, `originalProductHeading` | Checks three headers, five photo positions, separate number cells and restoration of real headings/rows. |
| `scratch/sales-overview-system-test/prepare-in-dashboard-sample.cjs` | 24, `productSample` | Captures real Chrome sample marker, headers, photo positions and row overflow measurements. |
| `scratch/sales-overview-system-test/verify-in-dashboard-sample.cjs` | 29, `result.productSample` | Verifies the new measurements for desktop, mobile and restoration cases. |
| `scratch/sales-overview-system-test/README.md` | 3 | Explains how to open the new sample layout. |

Regenerated scratch HTML previews, exported test renders, screenshots and browser measurement files are in `scratch/sales-overview-system-test/`. These are review artifacts, not application database records.

## 3. Changes Made

- Added five small sample product photos and a separate gray rank at the left.
- Changed sample headers from **Product / Units Sold / Sales** with stacked numbers to three clear columns: **Product**, **Units sold**, **Sales**.
- Kept product names navy and semibold, categories muted, units bold, sales right-aligned, and thin dividers between rows.
- Kept the trophy icon in its existing light-blue container, the flat white card and the gold sample notice.
- Added narrower column and photo sizes for small cards. Long names can wrap.
- No dashboard cards were moved or removed.

## 4. How It Works

Clicking **Show sample** already sends a `campushub:marketplace-sample` event. The product renderer now adds a `data-product-sample` attribute to the card and creates sample rows with five parts: rank, photo, product details, units and sales.

CSS Grid is the alignment tool: its column sizes keep every units value under Units sold and every peso amount under Sales. The new CSS selectors require the sample attribute, so they do not restyle the real-product rows.

The photo sheet is a **sprite**: one image contains several product photographs. CSS displays a different small section for each rank. This needs only one bundled image and no external image provider. Photos are decorative; the product name and its numbers remain readable text for assistive technology.

Before sample mode starts, the code retains the actual original row and heading nodes. **Use real data** puts those same nodes back and removes the sample attribute. Refresh or a real dashboard request also exits sample mode. Existing real-image authentication handling stays in the real-data branch.

## 5. Backend / API Behavior

No backend endpoint, model, ranking query, payment rule or result limit changed. Sample mode continues to use the previously verified fixtures calculated from isolated Django test orders: quantities **15, 12, 9, 6, 3** and sales **₱600.00, ₱600.00, ₱600.00, ₱625.00, ₱750.00**. Sample switching/grouping makes no dashboard API request. Real analytics still use completed and paid Cash on Pickup orders.

## 6. Database / Migration Impact

No production products, orders, inventory or image fields were changed. No database migration is needed. The bundled photographs are demo artwork, not images attached to actual product records. Django verification used its separate test database.

## 7. Tests Performed

- Two targeted existing Django tests passed: fixture calculations/grouping and populated/empty dashboard rendering. Django reported no system-check issues.
- The existing sample integration check passed with added checks for the new columns/photos, original DOM-node restoration, unchanged unrelated metrics, no sample API calls, refresh and failure/retry handling.
- Seven actual Chrome scenarios passed: Daily, Weekly, Monthly, Use real data, refresh exit, 500px mobile and a 320px content frame. Verified photo positions, row/card fit, labels, graph values and no JavaScript errors. Inspected desktop and mobile screenshots visually.
- JavaScript syntax and CSS parsing passed. Git whitespace validation passed; existing line-ending warnings do not indicate a test failure.
- Django static-file discovery found the bundled photo asset.

### Manual test

1. Open the Super Admin dashboard and press **Ctrl+F5**.
2. Click **Show sample** beside Sales Overview's grouping selector.
3. Find **Top Best-Selling Products**. It should show five product photos and separate **Units sold** and **Sales** columns with the sample notice.
4. Change Daily / Weekly / Monthly. The sample graph updates and the five product rows remain consistent.
5. Click **Use real data**. The sample photos disappear and actual rows or the honest empty state return.
6. Repeat sample mode and click global **Refresh** to check restoration through the real API.

Offline preview: open `scratch/sales-overview-system-test/index.html`, then click **Show sample**. Actual browser screenshot: `scratch/sales-overview-system-test/in-dashboard-daily.png`.

## 8. Remaining Limitations

The new photo layout is intentionally limited to sample mode at the user's request. The generated photographs illustrate the existing fixtures and are not actual seller uploads. Very long names wrap at narrow widths. This matches the approved design within the existing compact dashboard card rather than enlarging it to the mockup picture's dimensions. The existing sample date range remains September 29–October 5, 2026.

Photo asset provenance: generated with the built-in image-generation tool, then copied into the project. Prompt: a precise 3-by-2 white-background catalog photo sheet with a gray hoodie, iced Spanish latte, kraft spiral notebook, cream tote bag, silver USB drive and one blank cell; no text or UI. Final saved asset: `backend/static/components/images/samples/top-products-sprite.png`.
