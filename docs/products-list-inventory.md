# Products List — quantity-first Inventory column

Current October25,2026 FIFO follow-up: the existing Inventory page gains Stock Overview/Stock Movements/FIFO Batches views and a manage-permission receiving form; the eye/history/package actions and destinations remain. `fifo.receive` → Product.save/audit → `fifo.sync_change` records actual receipt batches; order/cancellation events expose original batch allocations. Runtime activation and existing-stock cutover remain blocked pending separate approval. [FIFO guide](fifo-inventory.md) contains the complete eight-part implementation/file-line map, inputs/outputs/data flow, backup, actual tests and limits. Safe exercise: use the isolated browser/test fixtures to open batch allocations and check0/25balances; do not create demonstration stock on the working database.

## Current: Inventory actions and retained pricing/variant improvements — October 24, 2026

### 1. Cause / reason

The follow-up request asks for three visible Inventory actions and compact, accurate pricing/variant entry. Read-only inspection confirmed that `admin_inventory.html` used a native `<details>` ellipsis menu. The shared stylesheet gave its trigger 44px dimensions and displayed the links as a vertical list. The existing service already supplies all three destinations and the required permission gates; no endpoint or controller is missing.

The requested Add Product work is already implemented in the preceding update below: one initial empty option, aligned labeled fields, neutral incomplete-option guidance, compact pricing, and separate component-derived bundle availability. These working changes were retained and regression-tested instead of rewritten. Current initial-threshold validation requires threshold below stock, except stock/threshold both zero; this UI update does not weaken that rule.

### 2. Exact files changed / current lines and anchors

| File / line | Change and nearby anchor |
| --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html:12` | Refresh the existing CSS cache key to `20261024-inventory-actions`. |
| Same template, line 84, `inventory-row-actions` | Replace only the ellipsis wrapper/text links with the existing three destination links represented by eye/history/package SVGs. Retain the original URL and permission conditions. Each link has its existing action name as `title` plus a contextual screen-reader label; SVGs are decorative. |
| `backend/static/components/css/admin_products.css:4977`, `.inventory-monitor-actions` | Replace obsolete menu-only styles with an intrinsic-width cell, an inline flex group, 6px gaps, 36px outlined links, navy focus outline, gold hover/focus border and restrained active background. Existing table padding, 1270px minimum width, scrolling, typography and other components remain. |
| `backend/core/modules/marketplace/test_inventory_monitor.py:167`, optional bundle export | Export an existing isolated component-derived bundle fixture for browser inspection. |
| Same test file, line 202, `inventory-product.html` | Export the product page and API response from the same isolated fixture as the Inventory list, keeping actual test-record IDs consistent for navigation QA. |
| Same test file, line 205, `test_visible_actions_keep_existing_destinations_and_permission_gates` | Verify all rendered destinations, contextual labels, disappearance of the ellipsis, successful authorized GETs, Inventory-only restrictions and separately granted movement access. |
| `docs/products-list-inventory.md:3` | This implementation and verification report. |
| `CAMPUSHUB_CONTEXT.md:3` | Record the current scoped Inventory presentation decision. |

Scratch artifacts are in `scratch/inventory-actions-review/`: the original template/CSS, browser scripts, isolated HTML/JSON fixtures, screenshots, measurements, protected-source hashes and logs. They are development evidence, not new application modules or records.

### 3. Changes made

Each fully authorized Inventory row now exposes **View Details**, **Stock Movements**, and **View Product** directly in that order. Each uses a compact outlined icon, native descriptive tooltip and contextual accessible name. Controls stay on one row without overlapping adjacent columns. Measurements show a 144px Actions cell containing three 36px links, two 6px gaps and the existing horizontal cell padding. Small screens retain the original focusable table scroll region.

No Edit, Delete, Approve or other action was added. Inventory-only accounts still receive only View Details. Movement access exposes the existing history action; product-view/manage/approve permissions retain their original gate. Missing inventory identities still do not acquire invented details/history links.

### 4. How it works / functions, inputs, outputs and data flow

`admin_products_page(request)` in `accounts/views.py:168` still checks module access and starts with `admin_product_queryset(request.user)`. For `view=inventory`, `inventory_monitor_context(request, products)` in `services/inventory_monitor.py:16` applies the existing filters, computes real row context and creates the same URLs. `inventory_url(params)` at line 12 preserves filter, page and tab-auth parameters. The template turns those authorized row values into ordinary navigation links; CSS only changes their presentation.

For a real SKU, the existing Inventory URL plus `#inventory-details` opens its read-only detail section. The movement URL adds `#inventory-movements` only when movement access is allowed. `details_url` retains the existing Products route and product ID, where the existing renderer opens Product Details. Example, using symbolic existing IDs rather than fake records:

```text
existing SKU row -> inventory_url + #inventory-details -> existing detail section
same row + movement permission -> movements_url -> existing recorded history
same row + product permission -> details_url -> existing product detail renderer
```

Pricing and variant flow remains the preceding section's implementation: saved base price plus option extra price produces the full option price; named valid stock/threshold input produces the preview; the original validators decide whether saving is allowed. A new blank option remains neutral; valid named zero/zero shows Out of Stock; saved stock at its threshold shows Low Stock. A bundle reads component availability and has no independent editable stock quantity. The current tests cover these existing calculations, not new replacement calculations.

### 5. Backend / API behavior

No runtime Python, API, JavaScript, query, seller/Program/Major permissions, product approval, stock mutation, price calculation or bundle workflow changed. Runtime changes are confined to the Inventory template and its action-specific CSS. Existing unused menu-close listeners remain harmless because no menu elements exist on this page; changing filter JavaScript is unnecessary. **154 protected runtime file hashes remained unchanged**; the intentionally edited shared CSS is excluded from that protected set.

### 6. Database / migration impact

No fields, models or migrations; no production product, variant, inventory or order writes. Django write tests use the separate test database. Browser tests load HTML/JSON exported from actual isolated Django records and refuse write requests. No fake records were inserted into the running application, and no live stock/pricing corrections were performed.

### 7. Tests performed

- **84 Django regression tests passed** across `test_inventory_monitor`, `test_program_inventory`, `test_thresholds`, `test_variant_inventory`, `test_bundles` and `test_product_final_validation`; system checks reported no issues. After correcting the same-fixture export, its individual test and then all **18 InventoryMonitorTests** passed. Logs: `django.log`, `django-final-focused.log` and the direct one-test command output.
- **1967/1967 Inventory browser/source checks passed across 23 renders**: populated, detail and empty views at 1920, 1366, 1280, 1024, 768, 390 and 320px, plus bundle details at 1366/390px. Verified horizontal alignment, exact target dimensions, compact action width, tooltips/names, tab order/focus, gold hover, existing navigation/product detail/history, page overflow, scroll access and no JavaScript errors.
- **505/505 Products browser/source checks passed across 10 renders**, including saved options, one blank new option, neutral invalid states, true zero-stock warning, existing price offsets, single/bundle switching, component availability, images, duplicate-save/error recovery, filters and pagination. **21 existing DOM form checks** and the existing review/authorization/decision harness passed.
- Visually inspected laptop and mobile Inventory screenshots. The mobile screenshot must be captured at the far right of its internal scroll region to show all three actions; focusing/hovering an earlier link can legitimately scroll it back into view.
- Scoped `git diff --check` and browser-script syntax checks passed. The CSS fetched from the existing local server with the new cache key matched the workspace SHA-256. No whole-project accessibility certification or unrelated-screen visual certification is implied by these checks.

### 8. Remaining limitations / troubleshooting / safe practice

Tooltips use native `title` behavior, with accessible link names available independently. Mobile users scroll the existing wide table to access all columns; this request explicitly retains scrolling. Browser QA uses headless Chromium rather than a physical phone. The existing decorative option reorder handle has no implemented drag-sort handler; this update preserves saved order and does not invent that new feature. Real AI image inference was not exercised; the prior original-on-failure behavior remains.

If the old ellipsis persists, refresh Inventory and confirm the CSS URL contains `20261024-inventory-actions` and the template contains `inventory-row-actions`. If an icon is missing, inspect its existing URL/permission condition before treating it as a layout defect. Never relax permissions to make every account display all three icons. If a bundle shows unexpected availability, inspect its existing component demand/reservations rather than editing parent stock.

Safe practice exercise: open Inventory using an authorized account, scroll to Actions, and Tab through the three links. Open View Details and Stock Movements, confirm the same SKU and real recorded history, then open View Product and confirm the matching product. Resize to mobile and verify all three links remain reachable. In Add Product, add a draft option, enter a name/stock 10/threshold 2, then test zero/zero and cancel without saving. Verify neutral draft guidance and the real zero-stock warning; do not change live inventory for this exercise.

## Current: compact Products list and Add Product layout — October 24, 2026

### 1. Cause / reason and read-only audit

The user requested improvements to the existing Products management page, prioritizing variant-entry spacing. The audit read the project rules/context, global UI guide, existing feature documentation, product template/styles/scripts, Product model, admin views/input validation, academic scope and bundle/customization/inventory helpers. The reported changes below extend the existing components; they do not replace the module or the earlier validation fixes.

Confirmed causes:

- `createCustomizationGroupElement` and the Add Variant handler each supplied three empty option records. Blank options had stock 0 / threshold 5, and `updateVariantState` immediately labeled them Out of Stock without checking whether a named, valid option existed.
- The option grid reserved one narrow stock/threshold column with vertically stacked inputs. Three automatic rows amplified its height. Mobile lost the shared column header's context, so each field now has its own nearby label.
- `.create-product-row` stretched the image section to the taller basic-information section. The uploader had 180px minimum height/30px padding, while Description started at six rows with a 120px minimum.
- The products table's outer region allowed horizontal scrolling, but its inner bordered `.products-table-container` used `overflow: hidden` without sharing the table's minimum width. This clipped rightmost columns and crowded fixed-width headings. The filter layout also did not reserve enough search space consistently.
- Switching a draft with variants to Bundle left the Single Product base-price helper visible, although the existing bundle renderer correctly changed the price label and uses component inventory. Only helper visibility is corrected.

**15 versus 13 is not a data defect.** `admin_products_page` uses all authorized products for Total Products and the table defaults to Listing Status = Active. A PostgreSQL transaction explicitly marked READ ONLY confirmed **15 total, 13 active approved, 2 archived approved** (`scratch/products-layout-review/live-counts.json`). No record or eligibility rule was changed. Pending/Approved retain their existing approval-state counts; Low Stock Alerts retains its existing active-product/per-option eligibility.

Existing reusable behavior retained: four KPI filter buttons; nine table columns; actual thumbnails/fallbacks; icon action labels/tooltips; product-detail/Edit navigation; academic controls; combined filters and pagination; six-image validation/gallery/primary controls; AI-removal timeout/original fallback; per-option images; native/server validation; duplicate-submit guard; variants' Single/Multiple selection; bundle component picker, price summaries and derived availability. Inspection found the existing decorative reorder handle but no implemented option drag-sort handler. No new reorder workflow was invented.

### 2. Exact files changed

| File / current line | Anchor and purpose |
| --- | --- |
| `backend/static/components/css/admin_products_refinement.css:25` | Existing product-page refinement: balanced filter grids/search span, reachable scrolling table and proportional fixed column widths. |
| `backend/static/components/css/admin_products_refinement.css:46` | Existing form sections: top alignment, 16px section rhythm, plain-field padding, readable controls, compact uploader/gallery, pricing/helper alignment, 96px resizable description and aligned Cancel/Add Product actions. |
| `backend/static/components/css/admin_products_refinement.css:70` | Existing option rows: inline labels, side-by-side Stock/Low Stock Threshold, aligned Price/Image/Delete and focus indicators. At line 87, the existing row switches to a narrow layout below 1200px so controls fit tablet content widths. |
| `backend/static/components/js/admin_products.js:1025` | `createCustomizationGroupElement`: one default option instead of three; supplied saved options still load completely. The Add Variant handler at line 1257 likewise starts with one option. |
| `backend/static/components/js/admin_products.js:1070` | `updateVariantState`: neutral Enter valid option details until the option name, numeric validity/bounds and existing initial-stock threshold rule allow a real stock preview. Existing saved zero-stock rows retain their warning. |
| `backend/static/components/js/admin_products.js:1098` | `toggleStockExpiryFields`: hide the single-variant price helper in Bundle mode without changing labels/prices/component rules. |
| `backend/static/components/js/admin_products.js:1669` | Existing dropzone gains Enter/Space activation of the same file input; no alternate upload or save workflow. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:23` | Refinement CSS and product JS (line 1026) cache version `20261024-product-layout`. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:95` | Existing products-table region becomes keyboard focusable/named; index col gets a reusable class at line 99. No column added/removed. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:250` | Existing uploader becomes keyboard focusable with a meaningful label/help association; line 348 accurately states existing JPG/PNG/WebP/GIF, six-image and 5MB support. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:511` | Description starts with three rows, preserving maxlength, counter and vertical resizing. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:533` | Group name/Selection gain accessible names. Existing option inputs at line 560 and image picker at line 567 gain simple nearby labels/wrappers for desktop/mobile alignment; selectors/actions remain. |
| `backend/core/modules/marketplace/test_product_final_validation.py:94` | New actual-endpoint regression proves a one-option group is supported, original base/extra price is retained, and a subsequent three-option edit preserves order/stock. Optional isolated HTML/JSON exports support browser QA. |
| `docs/products-list-inventory.md:3` | This current implementation/audit/verification guide supersedes older browser-unavailable notes for this scope. |
| `CAMPUSHUB_CONTEXT.md:3` | Store the current presentation decisions, count explanation and limits. |

QA-only exports, baselines, screenshots, scripts, source hashes and logs are under `scratch/products-layout-review/`; none is an application endpoint or production record.

### 3. Changes made

The four existing KPI cards remain aligned with their existing values/actions. Search receives more width, the same filters wrap into balanced desktop/laptop/tablet/mobile rows, and Clear Filters retains its existing semantics. The table keeps all nine columns, consistent thumbnails, readable seller/program and inventory hierarchy, approval badges and right-aligned prices. Its original named scrolling region now exposes the rightmost Actions column without leaking width to the page.

The Add Product form retains its numbered sections and fields. Image controls follow their content height; six consistent slots remain, with original AI processing/removal/primary behavior. Basic controls retain required markers and academic restrictions. Pricing uses the same fields: Single Product variants still show a base price and full per-option prices; Bundle shows Bundle Price and component-derived availability with no independent stock inputs.

New variant groups start with one blank option. Add Option/Add Variant/Single or Multiple Select/images/remove and saved-option order remain. Stock and threshold sit next to one another; option name, price, image and actions align at desktop sizes. Narrow layouts keep field labels next to their controls without clipping. Invalid or unnamed rows display neutral guidance; real named valid zero-stock options still show Out of Stock. All displayed warnings continue to derive from existing numeric/threshold rules.

Description starts smaller and remains resizable with the same character limit/counter. Footer actions stay together and wrap naturally. The existing submission-state guard remains the only duplicate-save mechanism. No new button, feature, module, animation, endpoint or workflow is added. Existing Montserrat product-content choice and shared navigation fonts/branding are preserved.

### 4. How it works / functions, inputs, outputs and data flow

`admin_products_page(request)` still obtains `admin_product_queryset(request.user)`, decorates actual products using academic/inventory/bundle helpers and supplies KPI/filter/table context. The original JavaScript filters those rows and initializes the existing ten-row pagination. CSS affects layout only; filters/counts/sorting/backend scope are untouched.

`appendCustomizationGroup(group)` passes a saved or blank group to `createCustomizationGroupElement(group)`. A supplied `options` array is rendered in full and in its original order. Only the absent-options default and explicit Add Variant draft change from three blank options to one. `readCustomizationFromForm` at line 1193 continues to collect named groups/options, calculate stored option extra price from full price minus base price, and submit the same payload. `validateThresholdForm` and server validation remain authoritative and unchanged.

`updateVariantState(row)` reads the name, stock, threshold, native validity and whether this is a new/saved option. Its output is only the row's preview text/class. A new valid threshold must be lower than initial stock, except existing zero/zero allowance; existing-option thresholds retain their original stock-level semantics. Negative, fractional, out-of-range, blank or unnamed inputs produce guidance rather than a misleading inventory label. The preview does not change input values, reject a save or alter stock calculations.

Annotated safe example:

```text
New blank option: name empty, stock 0, threshold 5 -> Enter valid option details.
Named new option: stock 10, threshold 2 -> existing In Stock preview.
Named new option: stock 0, threshold 0 -> existing Out of Stock preview.
Price: base ₱12.50 + saved extra ₱3.00 -> full option price ₱15.50.
Changing base to ₱13.00 retains the extra -> full option price ₱16.00.
```

The existing `toggleStockExpiryFields`/`CampusHubBundles.syncType` still separate Single and Bundle. Bundle availability remains component demand, not parent quantity, and Bundle Price is not recalculated from this UI change. The helper-text visibility now agrees with that existing mode.

Image data follows the same file input/drop handler -> existing file validation -> existing FileReader/optional AI request -> existing six preview slots -> existing saved payload. Enter/Space now activates that same file input. The server image validators, async safeguards, rollback, gallery persistence and variant image mapping from the previous implementation remain untouched.

### 5. Backend / API behavior

No runtime Python, API, query, permission, approval/rejection, owner/Program/Major scope, pricing or inventory calculation changes. **155 protected runtime files** were hashed before and after, including backend Python services/views/models and bundle/academic/shared feedback scripts. Existing approval decision colors/actions were preserved rather than redesigned. The actual create/update tests run against existing authorized endpoints in the isolated database; browser save/error and AI-failure transport are intercepted, not production writes.

### 6. Database / migration impact

None: no fields, models, migrations, fake live products, import/cleanup, approval/archive/stock mutations, deployment or service restart. The live count audit used `SET TRANSACTION READ ONLY` and verified it was on. All mutation tests used the separate Django test database, with temporary image storage. Production counts remain unchanged.

### 7. Tests performed

- **88 Django tests passed** across `test_product_final_validation`, `test_thresholds`, `test_variant_inventory`, `test_bundles`, `test_program_inventory`, `test_product_review_images` and `test_inventory_monitor`; system check reported no issues. This covers actual creation/update, one/multiple options, base/extra prices, exact variant stock/reservations, threshold errors, bundle availability, image validation/rollback, academic scope, review and archived-list behavior. Log: `scratch/products-layout-review/django.log`.
- Existing **21 DOM list/form interaction checks passed**: pagination, filters, decimal validity, image preview/primary/removal, invalid-file preservation, AI fallback, duplicate-submit and retained server-error input. Log: `form-check.log` in the QA folder.
- **506/506 Chromium browser/source checks passed across 10 renders**, using actual isolated list and saved-three-option exports. The measured result is recorded in `browser.log` and `measurements.json`. Tested widths are **1920, 1366, 1280, 1024, 800, 768, 390 and 320px**, plus saved-option edit scenarios at 1366/390px. Checks cover page/row fitting, scroll-region Actions access, filters/pagination/KPIs, accessible group controls, one-option default, valid/invalid/zero preview states, price-offset math, full saved option loading/order, field alignment, Description counter, keyboard file chooser, drag/drop, six-image cap/removal, invalid-image and AI-error fallback, variant image, one guarded save/error recovery, bundle component price/quantity/availability and 155 unchanged protected runtime files.
- Existing review interaction harness passed named decision controls, authorized image fallback/recovery, blank-reason validation and confirmed approve/reject response handling (`review-check.log`). Screenshots were inspected at laptop, tablet and mobile sizes. At 1366px, the variant section screenshot shrank from **923px** (three automatic blank rows) to **434px** (one populated option); the desktop option row itself measures about **103px**. Saved-option data/order are verified separately, rather than removed for compactness.
- JavaScript/QA harness syntax and scoped `git diff --check` completed without errors. Local refinement CSS and product JS requests succeeded and SHA-256 matched the final workspace. Optional design-kit scripts are unavailable, so no kit gate or full accessibility certification is claimed.

### 8. Remaining limitations / troubleshooting / safe practice

The 1300px readable table scrolls within its existing region on smaller viewports; no columns are hidden or compressed away. Browser mutation responses use intercepted fixture transport; real persistence is verified separately by Django tests. Real AI inference/model availability was not exercised; its failure/original-image behavior was. No complete WCAG or physical-device certification is claimed.

The pre-existing option reorder icon had no implemented drag-sort handler in this module. Its markup is retained, and saved array order is preserved; this task neither claims a working drag-sort feature nor invents one. Additional ordering functionality remains outside scope. Product action labels/tooltips and existing four KPI eligibility were already supported and were retained. Very long real-data content can still need wrapping or the existing details view; it is not replaced with fabricated data.

For stale spacing, reload and verify both `admin_products_refinement.css` and `admin_products.js` use `20261024-product-layout`. If the list shows fewer entries than Total Products, inspect Listing Status and active filters before editing data: archived products legitimately remain in the total. If a new option is invalid, use the actual field/native/server message; a neutral preview is not a successful save. Never change quantity/price calculations to force a visual state.

Safe practice: in the isolated test environment, run `test_single_option_group_and_saved_options_round_trip`, then the browser harness. Add one named option with stock 10/threshold 2 and full price 15.50 over base 12.50; verify the API preserves extra 3.00 and stock 10. Open its saved edit and confirm every option remains. Test Bundle component quantity 2 against stock 10: existing availability should be 5. This exercise uses test fixtures only; no live product creation is needed.

## Current: product management validation and usability — October 24, 2026

### 1. Cause / reason

Audit reused the existing Product model, admin save/stock/review endpoints, academic scope, SKU/movement helpers, bundle recipes and list/form components. Confirmed defects: admin image writes bypassed the existing byte validator; variant extra prices could be silently normalized; caught exceptions inside the atomic save could commit earlier writes; gallery saving mixed variant photos into the six product-gallery images; removing all images restored old images; upload callbacks could restore removed uploads; initial pagination could run before the active-list filter.

### 2. Exact files changed and anchors

| File | Line / code anchor | Change |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/admin_product_validation.py` | 15, `validate_admin_product_input` | Validate request shape, text/model lengths, IDs, prices, quantity bounds, variant structure and existing image validator before writes. |
| `backend/core/api/views.py` | 948, `admin_save_product`; 1248, `admin_update_product_stock`; `marketplace_approve_product` / `marketplace_reject_product` | Preflight, explicit rollback, unique upload names, explicit gallery clearing, readable validation errors, stock request bounds, locked pending-only review and required rejection reason. |
| `backend/static/components/js/admin_products.js` | `validProductImageFile`, `requestServerAiBgRemoval`, `renderProductImageSlots`, save handler, `initializeProductPagination` | Upload feedback, timeout/original fallback, primary image selection, stale callback protection, separate gallery/variant images, native validity, inline server error, duplicate-save guard and pagination timing. |
| `backend/static/components/js/admin_action_feedback.js` | JSON error path | Preserve backend `field` hint on thrown error so product UI can focus the right field. Existing callers still receive an Error. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 23, local CSS; 234, `productFormError`; `productName`, `productPrice`, image input | Version `20261024-products`, inline alert, model-length/name and decimal-price constraints, supported upload types, clearer approval/listing explanation. |
| `backend/static/components/css/admin_products_refinement.css` | 1, font-face and page scope | Requested Montserrat for product content/modals, aligned pricing labels/fields, compact image controls, one-column narrow pricing layout. |
| `backend/static/assets/fonts/Montserrat-VariableFont_wght.ttf` | local font asset | Reuses the existing Flutter-bundled Montserrat file; no font download. Sidebar/header keep shared typography. |
| `backend/core/modules/marketplace/test_product_final_validation.py` | validation/rollback/gallery/review/stock/list cases | New isolated regression cases and real test-record render export. |
| `backend/core/modules/marketplace/test_variant_inventory.py` | option-image test | Generate a valid tiny PNG with Pillow instead of the old corrupt PNG fixture rejected by byte validation. |
| `backend/core/modules/marketplace/test_product_review_images.py`, `backend/core/api/test_mobile_seller_application.py` | Program fixture setup | Create needed Programs/Major inside isolated tests; remove dependence on master data left by another test suite. |

These line numbers identify the current entry points; use the named anchors if later changes shift lines. Source UI scripts and test fixtures under `scratch/products-final-review/` support verification only; they do not populate production.

### 3. Implemented changes and preserved behavior

Gallery accepts JPEG/PNG/WebP/GIF, maximum six images, 5 MB each; server uses the existing content/MIME/pixel verification (20 megapixels). Variant photos use their exact options and do not consume product-gallery slots. A Make primary control reorders the existing gallery; first image remains its canonical primary. Clearing all gallery images persists an empty gallery. Existing stored/remote references retain the shared validator's compatibility behavior.

Auto Remove BG now has a bounded 20-second browser request. Failure keeps the original and explains that outcome instead of silently applying the old local heuristic. Remove/reset cancels the effect of stale callbacks; processing slots cannot be replaced while an older read is unresolved. Native decimal price validity and server field errors preserve inputs. Save stays guarded while pending, and validation failure restores it. The existing list View/Edit-via-details/Archive/Restore controls, permission checks, confirmations and movement tracking remain.

List pagination now initializes after initial filters. Combined filtering and Clear Filters keep rows/counts/pages synchronized. Summary totals remain over complete authorized rows, independent of visible pagination: total includes archived rows; pending/approved count approval state separately; Low Stock Alerts remains the existing active-product helper using available option quantities and configured thresholds. Bundles continue deriving availability from component demand with no independent base stock.

### 4. Functions, inputs / outputs and data flow

`validate_admin_product_input(data)` accepts decoded JSON, returns validated input or raises `ProductInputError(message, field)`. It uses Product model text lengths, existing inventory validation, and `validate_product_images`; it performs no database/file writes. Existing `resolve_academic`, owner scope and bundle validation still determine authorized relationships. Variant price validation runs before the existing normalizer so negative/nonfinite/sub-cent values cannot silently become a different saved price.

Form → existing admin endpoint → input validation → existing scoped owner/Program/Major/recipe/inventory checks → existing Product/SKU/movement persistence → existing serializer → confirmed row update. Caught save failures explicitly mark the transaction for rollback. Each uploaded file uses a fresh prefix, preventing a failed edit from overwriting an already referenced file. Database rollback cannot remove orphan files left by an interrupted storage write; cleanup remains a separate reviewed operation.

Example for learning: a new single product with stock 10 and threshold 2 persists those values; a variant product instead derives its parent quantity from options and uses per-option thresholds; a bundle uses its component recipe. These are existing inventory rules, not three independent quantities to add together. A rejected invalid upload creates no Product record. A stale approval after another reviewer already decided returns 409 without changing the saved decision.

### 5. Backend / API behavior

No new route, model, role or business workflow. Existing authorized admin-create auto-approval is retained; manage-only accounts still follow their existing permission behavior. Seller submissions retain their separate pending workflow. Approval endpoints now enforce the same pending/non-archived condition already shown by the UI and require the UI's rejection reason. Stock adjustments reject malformed objects/overflow before writes. All seller/product academic and inventory reservation restrictions remain.

### 6. Database / migration impact and live-record review

No migration/schema change, production mutation, sample import, deployment or restart. A read-only PostgreSQL snapshot on October 24 found **15 products: 13 active approved and 2 archived approved**, one without explicit product Program and one without a gallery. Missing explicit Program can legitimately inherit the seller's assignment; these counts are review findings, not proof of corruption or demonstration origin. No reliable universal demo marker exists, so records were not classified or silently repaired by their names. The disabled legacy test-product loader remains disabled. All mutation verification used Django's isolated test database.

### 7. Verification

- **101 Django tests passed** across final product validation, thresholds, bundle workflows, exact variant inventory, review images, academic scope, inventory monitor, mobile seller application and the dashboard health-removal render. Log: `scratch/products-final-tests.log`.
- **17 overlapping targeted tests passed** for validation, threshold boundaries and dashboard render after further request-shape/boundary handling (`scratch/products-final-targeted.log`). **65 final overlapping product/executive/KPI/operations/period regressions passed** after the unique-upload-name change and health removal (`scratch/products-health-final.log`).
- **21 list/form interaction checks passed** in `node scratch/products-final-review/check-form.cjs`: initial/next pagination, combined search/category/status, empty/clear, authoritative total, decimal validity, previews, primary selection, invalid file preservation, BG-failure fallback, double-save suppression and retained server validation input.
- Existing review harness passed authorized singular image fallback/recovery, accessible decision controls, blank rejection blocking and both confirmed transitions against current isolated fixtures (`scratch/products-final-review/check-review.cjs`). JavaScript syntax and Django system checks passed.
- Initial regression run caught a threshold field-hint mismatch, the corrupt legacy image fixture and missing independent Program/Major fixtures. Those were corrected; checks were rerun. No full-application or native-browser certification is claimed.

### 8. Remaining issues, troubleshooting and safe practice

Actual rembg inference/model availability and visual output were not exercised; graceful failure is tested. Connected browser inventory is empty, so responsive pixels, native file chooser, actual image decoding/canvas appearance and physical pointer/keyboard interactions need a browser walkthrough. Existing remote image URLs are references, not downloaded and byte-audited. Storage may retain orphan files after rollback; none were deleted automatically.

Safe exercise: run the isolated validation test class, not live product creates. Inspect `test_image_write_failure_rolls_back_product_and_stock`: mocked storage failure must leave zero new products and an unchanged existing stock/name. Then run the Node form checks to see retained input and primary reordering without production writes. For stale UI, Ctrl+F5 and inspect `admin_products.js?v=20261024-products` plus `admin_products_refinement.css`. If save fails, read the inline field message first; do not reset the form or create duplicate live products to test it.

---

## Four row actions and decision colors — 2026-10-19 follow-up

1. **Reason:** the user explicitly requested only View Details (eye), Approve (green check), Reject (red cross) and Archive. This overrides the earlier navy/gold-only treatment for these two decision icons.
2. **Files / anchors:** `backend/core/modules/marketplace/templates/marketplace/partials/product_actions.html:2` (`btn-view-product`) removes the row Edit button and renames View Details. `backend/static/components/js/admin_products.js:1705` (`renderProductActionsCell`) matches the same four controls after hydration. `backend/static/components/css/admin_products.css:4983` (`#productsTable .table-col-action`) uses 176px for four icons and scoped green `#15803D` / red `#B91C1C` decision styles with light surfaces. The Products template asset links at lines 14/1024 use `20261019-review-icons-v2`. Existing tests in `test_product_review_images.py:27` and `scratch/product-review-images/check-review.cjs` verify the final controls; this guide and project context record the follow-up.
3. **Changes:** remove Edit from list rows, retain the eye/check/cross/archive icons, accessible labels, confirmations and keyboard focus. Existing archived records retain Restore rather than an inappropriate Archive action.
4. **How it works:** the Django partial receives product state and permission flags; the JavaScript renderer receives status/archived state and uses the same permission flags. Both return the same row actions. For example, an authorized pending active product returns eye + check + cross + archive; an approved product returns eye + archive. CSS colors the existing decision classes; it does not change approval data or other status badges.
5. **Backend/API:** unchanged permissions, approve/reject endpoints, rejection dialog, image authentication and audit behavior. Removing the row Edit shortcut does not delete the existing product editing implementation.
6. **Database/migrations:** none; no live product state was modified. Refresh Products to load the new asset version.
7. **Verification:** five focused Django tests passed, JavaScript syntax passed, and the isolated DOM harness passed the four-action count, missing Edit, View Details label, rejection validation, both confirmed transitions and image fallback checks. Manual check: refresh Products, hover/focus each pending-row icon, cancel both dialogs, then use disposable test products to confirm decisions. Safe practice: change a fixture status to approved and rerender; expect check/cross to disappear while eye/archive remain. Restore the fixture afterward.
8. **Limitations/troubleshooting:** browser visual verification remains unavailable in this session. Check the asset version if old gold icons/Edit persist. Approve/Reject intentionally remain restricted to authorized pending non-archived rows; this is not a missing-action defect.

## Pending approval icons and protected product photos — 2026-10-19

### 1. Cause / reason

Pending rows used a text Review menu instead of direct check/cross controls. The decision JavaScript already existed, but its expected confirmation modal markup was missing. The affected Hyyy image file exists in local storage; the confirmed problem is authentication: pending product photos are private, and browser image requests do not receive the admin-tab header applied to `fetch`. Both initial thumbnails and JavaScript gallery hydration could request the image without the tab token.

### 2. Exact files changed and code anchors

| File | Approximate current line / anchor | Change |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/partials/product_actions.html` | 3 `can_approve_products` | Pending-only check/cross buttons replace Review text menu |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 150 `product_image`; 964 `productDecisionModal`; 14/1024 asset versions | Authenticated initial thumbnail, fallback, confirmation markup and cache refresh |
| `backend/static/components/js/admin_products.js` | 45 `productGalleryImageSrc`; 217 `setProductImageFallback`; 238 `initProductTableImageCycle`; 1705 `renderProductActionsCell`; 1807 `applyImageToRow`; 3676 `renderDetailsGallery` | Authenticated gallery sources, singular-image initialization, fallback/recovery and matching dynamic actions |
| `backend/static/components/css/admin_products.css` | 4983 `#productsTable .table-col-action` | 216px action space, compact gold/navy states, keyboard focus, hidden fallback and modal styling |
| `backend/core/modules/marketplace/test_product_review_images.py` | 18 `ProductReviewButtonsTests`; 42 `PendingProductImageTests` | Five isolated permission, markup and image-access tests |
| `scratch/product-review-images/run_tests.py`, `check-review.cjs` | dedicated test database; DOM interaction assertions | Repeatable fixture-only verification; no live product decisions |
| `docs/products-list-inventory.md`, `CAMPUSHUB_CONTEXT.md` | this dated section / latest product review note | Implementation and learning record |

### 3. Changes made

Pending, non-archived products show View, Approve (check), Reject (cross), Edit and Archive according to existing permissions. Approve has a subtle gold surface; Reject stays navy/white. Tooltips and accessible names explain each icon. Controls stay on one line with room for all five buttons. Approved/rejected rows lose the decision buttons. Existing View/Edit/Archive behavior remains.

The shared small confirmation dialog is restored. Approval asks for confirmation; rejection reveals a reason field and prevents an empty submission in the current UI. Photos retain the admin-tab token when initially rendered, hydrated, cycled, edited or viewed in the gallery. Failed table images show the existing initial-letter fallback; successful loading restores the photo. No sample image replaces actual product data.

### 4. How it works: functions, inputs, outputs and data flow

`productGalleryImageSrc(productId, index)` returns the existing same-origin image URL, authorized through `CampusHubAdminSession.urlWithToken` (or the current page's tab query token). It never appends credentials to an arbitrary external image URL. Image elements use `no-referrer` so the tab-bearing page/image URL is not sent as a referrer. `initProductTableImageCycle(row)` initializes even one-photo products before optionally starting the existing gallery cycle. `setProductImageFallback(image, failed)` toggles the image and its adjacent initial-letter span without changing stored photos.

`renderProductActionsCell(status, archived)` produces the same authorized controls as the Django partial, including after API hydration. Existing delegated clicks call `openProductDecision(row, action)`, populate the restored modal and retain the selected row. Confirmation sends the existing CSRF-protected approve/reject POST. Success updates the displayed status/actions; errors leave the decision uncommitted and report the existing error toast.

Example: an authorized admin opens a pending listing → its image URL includes that tab's token → the existing endpoint validates scope and serves the saved photo. Clicking cross → enter a reason → confirm → existing rejection endpoint persists the decision and audit activity → row no longer shows check/cross. This reuses the endpoint and approval flow rather than weakening photo access or creating a second workflow.

### 5. Backend / API behavior

No production backend endpoint or permission code changed. `/api/products/<id>/image/` still restricts pending images; public approved images remain public. Existing `/api/marketplace/products/<id>/approve/` and `/reject/` keep their server-side permission/scope enforcement and audit behavior. A rejection reason is required by this UI; the pre-existing endpoint itself still accepts an empty reason from other clients. No broader backend validation change is claimed.

### 6. Database / migration impact

No model or migration change, and no live product was approved, rejected, replaced or deleted. Tests use the separate `test_campushub_product_review_images` database. No application restart, mobile run, APK build or data-cleanup command is required. Refresh the web Products page to load asset version `20261019-pending-actions-images`.

### 7. Verification and manual steps

- Five Django tests passed; system check reported no issues. They cover pending controls/permissions, required modal markup, tab-authorized pending image bytes, anonymous/invalid-token denial, public approved photos and the existing rejection permission/reason persistence.
- `node --check backend/static/components/js/admin_products.js` passed.
- `node scratch/product-review-images/check-review.cjs` passed against isolated Django fixtures with mocked network transport: authenticated singular thumbnail, error/load recovery, accessible icons, empty rejection blocked, and both confirmed status transitions. This is a DOM interaction check, not a rendered Chrome layout check.
- Browser visual verification could not run: both configured in-app browser and Chrome control returned Browser is not available. Physical-device/live authenticated approval flows were not tested.

From project root, rerun `backend/core/venv/Scripts/python.exe scratch/product-review-images/run_tests.py`, then the Node command above. The wrapper selects the dedicated test database and exports only isolated fixtures. Do not substitute a production database.

Manual checks: refresh Products; inspect a pending product with a real photo; verify check/cross tooltips and keyboard focus. Open each dialog and Cancel first. On a disposable test product, confirm approval; on another, try blank rejection then a written reason. Verify the resulting status and removed decision icons. Confirm View/Edit/Archive, filters and pagination still work. Check approved/rejected and unauthorized views have no approval controls. Resize to confirm horizontal scrolling stays within the existing table region.

Safe practice: in the isolated fixture, deliberately dispatch an image error and verify the initial-letter fallback appears; dispatch load and verify recovery. Then change the fixture status from pending to approved and rerender its actions: check/cross must disappear. Restore fixture values afterward. This teaches display state versus saved database state without editing live records.

### 8. Remaining limitations / troubleshooting

Missing/deleted media files still need the original uploaded image restored; authentication cannot recreate a file. If a pending thumbnail is blank, inspect its image request status and authorized tab scope, then confirm the actual file exists. Do not make private images public to bypass a 404. Do not share URLs containing tab tokens. If controls look stale, verify the new CSS/JS asset versions. Visual alignment and real authenticated browser operation remain manual checks because browser control was unavailable.

## Inventory Filters heading and product pictures — 2026-10-13

### 1. Cause / reason

The user requested a visible Filters heading and pictures in Inventory. Inspection confirmed the existing filter labels/search/dropdowns and twelve-column ledger were already functional, but its Product cell contained only a name. Variant inventory already carried each exact option's saved `image_url`; simple products and bundles could reuse the existing Product gallery/image endpoint. No images needed to be generated or stock logic replaced.

### 2. Exact files changed, current lines and nearby anchors

| File, relative to project root | Current line / anchor | Change |
|---|---|---|
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 13 CSS asset; 28 `inventoryFilterHeading`; 69 `inventory-product-cell` | Add Filters heading/accessible form name and thumbnails inside the existing Product column |
| `backend/core/modules/marketplace/services/inventory.py` | 538 `parent_image`; 543 unavailable variant image; 552 `thumbnail_url` | Select exact variant image first, otherwise the existing protected product-image route; supply one-time fallback metadata |
| `backend/static/components/css/admin_products.css` | 4974 `.inventory-filter-heading`; 4975 `.inventory-product-cell`; 4977 `.inventory-thumbnail` | Inventory-only heading, compact 40px contained images, neutral placeholder and hidden-state styles |
| `backend/core/modules/marketplace/test_inventory_monitor.py` | 179 fixture export; 199 `test_inventory_thumbnails_use_exact_variant_then_product_and_preserve_stock` | Test image choice, parent endpoint, empty placeholder, heading and unchanged stock; export isolated image fixtures |
| `scratch/inventory-monitor/check-ui.cjs` | search `inventoryFilterHeading`, `brokenImageFallback`, `loadedPictures` | Browser tests for heading, actual thumbnail loading, source/fallback handling and existing responsive ledger behavior |
| `docs/products-list-inventory.md` | this section | Change report, functions/data flow, verification/debugging and safe practice |
| `CAMPUSHUB_CONTEXT.md` | final `Inventory Filters heading/photos` entry | Remember scope, test results and remaining test limitations |

No Products List template, Inventory filter JavaScript, route, model, migration, permission or image-processing/upload code changed. The shared stylesheet changes are scoped to the new Inventory classes. The Inventory CSS URL uses `20261013-inventory-images`.

### 3. Changes made

Inventory now shows Filters above its current Search, Inventory Status, Program, Major, Seller and Category controls. The form references that heading through `aria-labelledby`; filter behavior/GET values, Clear, page size and pagination remain.

The existing Product column contains a 40 × 40 rounded thumbnail beside its name link. The exact saved variant picture is preferred; if absent, the parent gallery is served through the current permission-aware product-image endpoint. Simple and bundle rows use their own Product gallery. Missing photos show the existing navy package icon on a light surface. A broken variant image tries the parent once; if that fails too, the image is hidden and the placeholder revealed. No stock, approval, variant, bundle or inventory action was added or removed.

### 4. How it works: functions, inputs/outputs and data flow

`build_inventory_table(products)` still receives the server-authorized product queryset and returns expanded inventory rows with existing batched stock/hold/SKU data. It now adds two display-only keys: `thumbnail_url` and `thumbnail_fallback_url`. It reads `product.get_image_list()` and current option images already present in the rows; it adds no metadata SQL query for each row. Parent thumbnail URLs use `reverse("product_image", args=[product.pk])`, reusing the current image-serving/visibility behavior, including legacy gallery formats. Variant URLs remain their actual saved uploaded source.

`inventory_monitor_context()` continues filtering/searching the same rows and preserving tokens/links. `admin_products_page()` still paginates them and renders Inventory. The template uses the new keys inside the Product cell; the existing product link remains. Its static image-error handler consumes and clears the fallback URL before retrying, then reveals the placeholder, preventing an error loop.

```python
# Display selection only; not a stock update or image upload.
thumbnail = row.get("image_url") or parent_image_route
# A specific Large image is never assigned to Small by gallery position.
```

The `width`/`height` attributes reserve space while `loading="lazy"` and `decoding="async"` allow pictures to load as rows approach the viewport. CSS uses `object-fit: contain` to retain the full image. Repeated product/variant names already identify each row, so thumbnail/placeholder accessibility avoids redundant name announcements.

Data flow: authorized Product + variant JSON -> existing inventory expansion -> image display keys -> existing GET filters/pagination -> template -> saved image/parent route -> one-time fallback/icon. The backend still calculates Available, Reserved, On Hand, thresholds and derived bundles exactly as before. This approach was chosen to reuse actual image storage and keep twelve columns instead of adding another image column or fake sample pictures.

### 5. Backend / API behavior

Existing Inventory URL (`admin_products_page?view=inventory`), metadata filters, program scope, tab authentication, actions and RBAC remain. Parent pictures use the existing `/api/products/<id>/image/` route, which already permits authorized Inventory viewers and enforces the authorized product queryset. No new endpoint or permission grant. Browser image requests use this existing endpoint normally; metadata expansion remains batched.

### 6. Database / migration impact

None. Existing stored images/variant JSON are read, not rewritten. No product photos, records, prices, stock or reservations were inserted into production. Test-only images/records were created solely in Django's separate test database; exported screenshot fixtures map the real test product-image routes to their actual fixture bytes.

### 7. Verification, debugging and commands

- **64 focused Django tests passed** across current Inventory monitor, variant inventory, Program inventory and bundle behavior. The new test checks exact Large image versus parent Small/Medium images, heading/accessible form naming, missing-image placeholder, image route response and preserved stock/threshold JSON.
- **Nine Chrome checks passed:** Inventory, Inventory Details and empty state at requested desktop 1440px, tablet 1024px and actual phone 375 CSS pixels. All populated fixture thumbnails loaded after scrolling into view; broken-image fallback, 40px size, twelve columns, internal table scrolling/keyboard focus, numeric right alignment and filter containment passed. Desktop/phone screenshots were visually inspected.
- Read-only Inventory rendering against existing local data returned HTTP 200 with the heading and image cells. Django system check clean; migration dry run reported No changes detected. No physical-phone/deployment check.

The first broader command included an incorrectly named bundle test module; it was corrected to the actual `test_bundles.py`. That run also exposed unchanged historical migration-test failures: the old SKU migration state did not supply the newer required User `email_verified` column, and the Program migration test's intermediate state lacked that current column. The successful current-feature run explicitly selected the normal test classes and excluded these historical migration tests. They were not repaired as part of this UI change. The separate old filter-spacing harness also failed its Products-at-1440px one-row assumption; this refinement did not change Products markup/selectors, and the Inventory browser review passed. Do not describe those broader checks as passing.

Re-run current feature checks from `backend/core`:

```powershell
$env:INVENTORY_MONITOR_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/inventory-monitor'
venv/Scripts/python.exe manage.py test modules.marketplace.test_inventory_monitor.InventoryMonitorTests modules.marketplace.test_variant_inventory modules.marketplace.test_program_inventory.ProgramInventoryTests modules.marketplace.test_bundles --keepdb --noinput
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
# From project root:
node scratch/inventory-monitor/check-ui.cjs
```

Manual checks: Ctrl+F5 on Inventory. Verify Filters heading and the existing controls. Compare a variant with its own picture to a variant without one; each should use the correct source. Check a product without photos, search/status combinations, Clear and pagination. Resize or open phone browser: filters stack, table scrolls inside its region, and product images remain compact. Verify actual stock before/after viewing; browsing must not modify it.

If styling is old, inspect CSS version `20261013-inventory-images`. If a variant shows the wrong picture, inspect its own saved `option.image` and the row's thumbnail keys; do not assign photos by gallery index. If the parent fails, check the existing image endpoint response/authorized scope and actual stored file, rather than inserting a test image into production. A missing image produces a placeholder; it does not mean quantity is zero. For migration-test errors, inspect the historical model state and migration dependencies separately from these display fields.

Safe practice: on a local branch, change only `.inventory-thumbnail` dimensions and matching template width/height from 40 to 44, run the isolated review and predict which size assertion fails. Restore 40 afterward. Then compare a variant's explicit source with its parent fallback in the captured test page. This teaches how CSS dimensions, image metadata and stock calculations have separate responsibilities without changing real products or reservations.

### 8. Remaining limitations

Only Inventory received the Filters heading/pictures in this request. Photos must already exist in the product gallery or exact variant; no new asset or photo-upload workflow was created. Historical migration-test schema errors and the older Products layout assertion remain separate unresolved verification issues as described above. No physical-phone or production deployment claim is made.

## Products / Users shared page layout - 2026-10-09

Products now uses the shared page description/action, KPI/list spacing and responsive header styles in `backend/static/components/css/admin_layout.css:2460`, with the same layout classes as Users. Its template at `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:36` places Add Product above the KPIs; `productsListSection` at line 78 keeps its original filters, table and pagination but gains the requested list subtitle. The Product-only rule in `admin_products.css:4984` reads the existing list's hidden state so the relocated action still hides during form/loading/details views.

No stock calculation, variant/bundle behavior or backend function was changed. Data still flows through the existing Products view and API into the existing template and `admin_products.js`; the same `addProductButton` ID invokes the original create-product functions. Presentation classes only change the rendered layout. Inventory is outside this shared-layout change.

See [the current implementation and learning report](user-management.md#latest-update-shared-products--users-page-layout-october-9-2026) for all changed files/lines, verification results, debugging and a safe CSS practice exercise. Quick verification: open Add Product, use the existing back action and confirm the page-level action returns. If styling is stale, inspect the updated stylesheet version and computed CSS before changing data or duplicating rules.

## Products and Inventory filter spacing - 2026-10-08

### 1. Cause / reason

Confirmed in the shared CSS: `padding: 0 20px 20px` left no space between the header divider and filter labels. Inventory also inherited an older bottom margin and 42px controls, whereas Products used 40px controls. These competing rules made the two toolbars inconsistent. This change improves presentation only.

### 2. Exact files changed and anchors

| File | Current line | Nearby code anchor | Change |
| --- | --- | --- | --- |
| `backend/static/components/css/admin_products.css` | 4919 | `Keep filter labels clear` | Shared 20px padding, 8px label/input gap, 16px gap between wrapped rows, wider status field and consistent 44px controls. |
| Same CSS file | 4948 | `.product-catalog-filters > .catalog-clear-filters` | Compact outlined Clear Filters control on both pages; navy text and a visible gold keyboard focus outline. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 53 | `inventory_reset_url` | Apply the shared Clear Filters class to the existing reset link. Its destination stays unchanged. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 13 | `20261008-filter-spacing` | Refresh the CSS URL version so browsers request the updated stylesheet. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 14 | `20261008-filter-spacing` | Same CSS refresh for Products. Existing filter markup/IDs are retained. |
| `scratch/inventory-monitor/check-filter-spacing.cjs` | 1 | `Read-only review` | Local verification helper using exported isolated test templates and the actual stylesheet. No production fixtures. |
| `docs/products-list-inventory.md` | 3 | `Products and Inventory filter spacing` | This explanation, debugging notes, test evidence and practice exercise. |

### 3. Changes made

Search remains first and has more width than ordinary dropdowns. Status is next, followed by the existing filters in their current order. Clear Filters aligns with the inputs on wide screens. The existing breakpoints at CSS line 4980 produce three columns below 1280px, two below 768px and one below 576px. No filters, KPI cards, table columns or actions were removed or moved to another page.

### 4. How it works: functions, inputs, outputs and data flow

CSS receives the rendered labels/controls and available viewport width; its output is spacing and placement, not new data. `padding: 20px` creates space INSIDE the toolbar, including above the labels. `margin: 0` removes the older Inventory outer gap. `align-items: end` aligns each control at the bottom of its grid row. More specific Clear Filters selectors prevent the older Inventory link rule from reducing its height.

```css
padding: 20px;     /* Distance from the divider/card edges to the filters. */
gap: 16px 12px;    /* First: vertical row gap. Second: horizontal column gap. */
```

The existing Products function `applyInlineFilters` (`admin_products.js:2652`) takes current search/status/program/major/category values and shows matching authorized rows using AND. Inventory's existing `submit` helper (`admin_inventory_filters.js:17`) calls `form.requestSubmit()` when dropdown values change; search submits after 300ms. Django receives those GET parameters and returns filtered real inventory rows. Products' Clear button retains its existing event handler; Inventory's Clear link retains the backend-generated `inventory_reset_url`. Neither script was edited.

### 5. Backend / API behavior

Unchanged. Real record queries, permissions, stock formulas, Program/Major dependency, search debounce and reset behavior are reused. Styling does not recalculate inventory or send additional requests.

### 6. Database / migration impact

None. No models, migrations or production records were changed. The one Django export test created and destroyed its separate test database.

### 7. Tests performed and manual verification

- Ran the isolated `ProgramInventoryTests.test_export_isolated_catalog_and_inventory_for_browser_review`: 1 test passed; Django system check reported no issues.
- Ran `node scratch/inventory-monitor/check-catalog-behavior.cjs`: passed search debounce, combined filters, Clear, Program/Major behavior, archive/restore, refreshed counts and existing keyboard/action behavior.
- Ran `node scratch/inventory-monitor/check-filter-spacing.cjs`: eight real Chrome page/viewport checks completed (Products and Inventory at requested 1920, 1440, 1024 and actual 375 CSS pixels). Filter controls stayed within their labels/viewport, divider gap was 20px, inputs and Clear were 44px, and Clear had visible keyboard focus. Wide layouts aligned in one row; narrower layouts wrapped. Nine Products and twelve Inventory columns remained.
- Inspected both 1440px screenshots visually. Offline review uses local styles and test-database HTML; it does not execute the authenticated production session.

Manual steps: open Products and Inventory, press Ctrl+F5, confirm space below each divider and aligned inputs. Search a known product; combine Program/Major and status filters; Clear should restore the existing defaults. Resize the browser and Tab to Clear Filters to check wrapping and its gold focus outline. Inventory KPI cards should remain above the table.

### 8. Remaining limitations and debugging

The Products offline fixture still has global `.header-right` overflow at 375px with application scripts removed. Its filter toolbar fits; Inventory's whole page fits. The shared header was not edited, and live mobile header behavior was not verified in this task. Wide tables retain their existing horizontal scrolling.

If labels still touch the divider, inspect the computed padding in browser DevTools and check that the stylesheet URL ends in `20261008-filter-spacing`. Hard-refresh first. If Clear differs in height, inspect competing `.inventory-page-filters > a` styles; the shared direct-child class selector intentionally takes precedence. Do not change stock calculations to fix spacing.

Safe practice: in DevTools only, temporarily change the filter `padding` from `20px` to `24px`. Predict that all four edges gain 4px while inventory values stay unchanged, then measure the first label's distance below the divider. Reload to discard the experiment. Find the original CSS anchor before making a saved change, and run the spacing check after any saved adjustment.

---

## Current catalog consistency update - 2026-10-08

The current Products/Inventory changes are documented in [variant-inventory.md](variant-inventory.md). This supersedes earlier department-only filters and archive/query-count notes below. Products keeps nine columns, with Product + actual SKU and Seller & Program; Inventory has twelve columns and four matching KPI cards ABOVE the table.

Functions/data flow: `accounts/views.py:170` (`admin_products_page`) accepts the request, obtains the server-authorized Product queryset, and returns rows/real totals/master choices. `accounts/academic.py:56` (`scope_products`) applies Program/Major before any records reach the browser. `admin_products.js:2652` (`applyInlineFilters`) combines search/approval/listing/program/major/category with AND; `:2406` (`syncProductStatsFromRows`) refreshes summaries after real mutations, without treating filtered-out/archived rows as deleted. `api/views.py:792` (`admin_save_product`) validates owner/program/major and returns the saved payload; `admin_products.js:2297` merges it so new rows retain real SKU and assignment.

Why: inventory quantity/status and product approval/listing remain separate, while the same underlying records power all views. Confirmed debugging fixes include scoped access instead of global admin access and lost saved Program/SKU fields. Main migration preserved stock/orders/SKUs/movements; two records remain unassigned because their owners have no assignment. Full test evidence and limitations are in the linked eight-part report: 209 Django tests passed, with final overlapping follow-ups of 32 analytics/program and 7 user-management tests; responsive/browser interaction checks passed.

Safe practice: with the isolated browser fixture, select Archived and All and predict visible row counts; verify the Total Products KPI stays unchanged. Then locate `syncProductStatsFromRows` and explain why it reads all authorized rows rather than only visible rows. Verify using `node scratch/inventory-monitor/check-catalog-behavior.cjs`; no production edits are made. For actual stock formulas and permission test exercises, use the linked guide.

---

Current bundle behavior (2026-10-07): [component-bundles.md](component-bundles.md) supersedes older unsupported-bundle statements/tests in this guide. Lists show actual derived bundles available; ingredient alerts remain separate. Inventory shows a derived bundle row with no fake On Hand/Reserved/Threshold. The linked guide explains the functions, data flow, files/lines, debugging, verification and safe practice.

Latest variant follow-up (2026-10-07): [variant-inventory.md](variant-inventory.md) documents the current files/lines/anchors and shared calculation. Tracked products show aggregate available quantity, actual variant count and positive low-variant count on compact separate lines; each option uses its own level. Simple products retain the small threshold line. Inventory now uses view=inventory to show separate On Hand/Reserved/Available/Threshold/Status rows from real holds and JSON. No second stock store was added. See the new guide for functions, inputs/outputs/data flow, verified checks, debugging and a safe test practice exercise. Earlier maps/results below describe the preceding presentation step.

Latest threshold update (2026-10-07): the user confirmed a small `Threshold: <number>` line inside the existing Inventory cell, or `Threshold: per variant` for tracked options. Keep nine columns and the existing quantity/status styling. Simple products now use their saved level; positive tracked options use their own saved levels, with the existing setting as the legacy fallback. Healthy stock still has no status badge/dot. Earlier global-only rules and test results below describe prior steps. See [product-low-stock-threshold.md](product-low-stock-threshold.md) for current files/lines, functions, API/data flow, applied migration 0031, debugging, verification and a safe practice exercise.

Related update (2026-10-07): Product Details now labels Approval Status, Listing Status and Inventory Status separately and reads its On Hand/Reserved/Available/Threshold from the canonical Django snapshot. The list's compact display and its filters remain unchanged. See [product-details-status-inventory.md](product-details-status-inventory.md) for current files/lines, functions and data flow, the double-subtraction fix, variant/bundle handling, debugging, checks and safe practice.

Updated 2026-10-07. Scope: the existing Products List Inventory cell. Keep all nine columns, search, filters, pagination, approval statuses and product actions. This does not build a new Inventory page or bundle workflow.

## Latest update: status dots, exact colors and singular unit — 2026-10-07

### 1. Cause / Reason

Confirmed: quantity text always used `pcs`; Out of Stock had no dot; Low Stock text used darker gold. The general `.seller-products-table td span { display: block; }` selector also overrode the weaker `.inventory-warning` display rule, putting the existing gold dot above its text. Fix the cell's presentation without changing its stock calculations.

### 2. Exact Files Changed / Lines / Anchors

| File relative to project root | Current line / anchor | Presentation change |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 177 quantity; 183 Out of Stock; 14/1012 asset versions | Use Django `pluralize` for pc/pcs, add the red-state dot and refresh cached CSS/JS. |
| `backend/static/components/js/admin_products.js` | 510 `renderInventorySummary`; 518 out-of-stock markup; 520 unit | Match the initial template after edit/save and Save Stock, including singular units and both warning dots. |
| `backend/static/components/css/admin_products.css` | 4699 summary; 4705 warning; 4714 gold override; 4736 dot | Reserve a consistent compact 32px summary height; align dot and label horizontally; use 600-weight, 0.70rem secondary text, exact gold, and a 5px circular dot inheriting status color. |
| `backend/core/modules/marketplace/tests.py` | 429 inventory regression | Extend the existing isolated fixture with one available unit and verify `1 pc`. |
| `scratch/products-inventory/check-column.cjs` | initial row assertions; singular renderer check; Chrome metrics | Verify units, warning-only dots, exact text/dot colors, circular size, smaller status font and alignment. |
| This guide and `CAMPUSHUB_CONTEXT.md` | latest presentation note | Preserve accepted styling and explain debugging and verification. |

### 3. Changes Made

Healthy stock stays visually quiet: quantity only, with no healthy-status label/dot. Existing variant metadata is preserved. Low Stock dot and text use `#FCB316`; Out of Stock dot and text use the existing muted red `#B42318`. Navy quantity remains 700-weight and larger than the warning's 600-weight text. Both warnings remain plain compact text, without a badge. `1 pc`, `0 pcs` and larger plural quantities are consistent across initial and refreshed rows.

### 4. How It Works / Functions, Inputs and Outputs

Input remains the real `admin_total_stock` and `admin_quantity_status` from the existing view. Django chooses a suffix with `pluralize`; JavaScript's `renderInventorySummary(totalStock, variantCount)` chooses the same unit when returning markup after saves. No backend function changes in this update. CSS only controls presentation; it cannot change quantities or stock states.

```javascript
// Presentation only: singular for exactly one available unit.
const unit = safeStock === 1 ? 'pc' : 'pcs';
// The status dot uses background: currentColor to match its label automatically.
```

The scoped warning selector has higher specificity than the general table-span rule. `inline-flex` puts the dot and label on one line; `align-items: center` centers the 5px dot vertically. The common summary height and spacing keep healthy and warning rows aligned while retaining narrow-cell wrapping.

### 5. Backend / API Behavior

Unchanged. Saved stock is already net of reservations, tracked variants retain the existing sum, and the configured low-stock threshold still controls classification. No product-name, seller, category, price, approval, date, action, search, filter or pagination behavior was changed.

### 6. Database / Migration Impact

No migrations, model changes or production data writes. The added one-unit example exists only in the isolated test database.

### 7. Tests / Manual Verification

- Existing database-backed inventory regression passed: **1 Django test**, including a one-unit product, configured threshold 10 and separate approval states. System check found no issues.
- DOM integration passed initial and JS-rendered singular/plural units, warning-only dots, existing edit/save and Save Stock updates, and variant metadata.
- Two current Chrome layouts passed at 1440px and 500px: exact matching text/dot colors, 5px circles, vertically centered dot/label, smaller status font, navy quantities, nine retained columns and no cell/page overflow. A first browser assertion expected computed `inline-flex`; browsers correctly compute flex children as `flex`, so the harness now accepts both and verifies geometry. Application behavior was unchanged for that test correction.
- JS syntax and targeted whitespace checks passed.

Manual: refresh Products List, inspect a healthy, low, one-unit and zero-unit product, and confirm quantity remains navy. Low Stock must have matching gold dot/text; Out of Stock must have matching muted-red dot/text. Edit/save a product or use the existing Save Stock action in a test environment and verify the same grammar/styles remain. Compare the other columns and filters to confirm they are unchanged. Tests use isolated records and browser fixtures, not a logged-in production editing session.

### 8. Debugging / Safe Practice / Limitations

If a dot stacks above its label, inspect the scoped `display` on `.inventory-warning`: the CSS sets `inline-flex`; inside a flex parent the browser can compute it as `flex`. Both keep the dot and label horizontally aligned. If colors or `1 pc` do not update, inspect the CSS `20261007-inventory-dots` and current JS `20261007-details-status` asset URLs and refresh. Check both the template and JS renderer, because one handles initial HTML and the other handles saved rows.

Safe practice: call `CampusHubAdminProducts.renderInventorySummary(1, 0)` and `(0, 0)` in an isolated preview. Inspect the returned strings for `1 pc` and `0 pcs`; verify the appropriate warning dot. Do not save real stock to practice formatting. Existing bundle and seller-label-test limitations documented below remain outside this presentation change.

---

## Previous quantity-first implementation

## 1. Cause / Reason

Confirmed: the view already supplied `admin_total_stock` and `admin_variant_count`, but the template and JS row renderer displayed only an inventory pill. An unused summary renderer also hardcoded a threshold of five and treated the worst variant state as the parent state. This could label a parent out of stock even when another variant had available units.

Inspection also confirmed that order placement deducts stock through `adjust_product_stock` before saving a pending order. Therefore the saved stock is already remaining availability. Subtracting reserved quantities a second time in this column would undercount. Bundle saving is explicitly blocked by the existing form; the Product model has no bundle-component relation to calculate derived bundle availability.

During verification, the existing stock-save handler called `showProductSaveToast` from a different JavaScript scope and threw a ReferenceError after a successful response. Its existing notification is now exposed through the same helper object and called safely.

## 2. Exact Files Changed / Lines / Nearby Anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/accounts/views.py` | 31–32 imports; 187 `admin_total_stock`; 188 `admin_variant_count`; 195 `admin_quantity_status` | Reuse remaining total stock and configured stock classifier. Include tracked legacy options in variant count even if the customization flag is off. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 14 CSS version; 147/152 row data; 176 `inventory-summary-clean`; 1012 JS version | Replace Inventory pill with quantity, optional variant count and low/zero warning; export existing quantities to row attributes and update cache versions. |
| `backend/static/components/js/admin_products.js` | 442 `computeTotalStock`; 461 `countProductVariants`; 510 `renderInventorySummary`; 1632 row metadata; 1665 Inventory cell; 1932 row variant metadata | Match canonical backend totals and render the same compact summary after edits. Never treat option count as stock. |
| Same JS | 2648–2651 helper exports; 3657 stock response; 3683 toast | Reuse the same quantity renderer after Save Stock; use returned stock/options rather than assuming the entered quantity represents every variant; fix the stock-save notification scope. |
| `backend/static/components/css/admin_products.css` | 4718 `inventory-secondary`; 4736 `inventory-warning-dot` | Scope wrapping/alignment and gold warning dot to table summaries. Existing muted-red Out of Stock styling is reused. |
| `backend/core/modules/marketplace/tests.py` | 429 `test_inventory_column_uses_remaining_parent_quantity_and_separate_approval` | Verify reservations, configurable threshold, simple/variant/legacy/untracked quantities and separate approval state; optional isolated export for browser checks. |
| `scratch/products-inventory/check-column.cjs` | Initial DOM assertions, edit/save assertions and Chrome loop | Check actual fixture markup, helper parity, existing edit and stock-save rendering, and wide/narrow layouts. |
| `CAMPUSHUB_CONTEXT.md`; this guide | Latest Products List note | Save accepted behavior, explain functions/data flow, tests and practice. |

The stock service and API serializers were inspected and reused, not changed. Line numbers may move later; search the named anchors.

## 3. Changes Made

Healthy simple products display only **20 pcs**, without a green badge or redundant In Stock label. Low stock displays quantity with a smaller Low Stock warning; zero shows **0 pcs** and Out of Stock. Tracked variant quantities are summed at parent level and their count remains visible, for example **8 pcs** followed by **3 variants · Low Stock**. Secondary information may wrap inside a narrow cell; no column is added or widened.

Quantities use navy. The latest explicit request uses exact brand gold `#FCB316` for Low Stock text and dot, replacing the earlier darker text tone. Out of Stock reuses muted red `#B42318` for text and dot. Approval status remains in the separate Status column. Its existing styles and workflow are untouched.

## 4. How It Works / Inputs, Outputs and Formulas

### Available stock

Conceptually, `Available = On Hand - Reserved`. In the existing workflow that subtraction happens when the order reserves stock:

```python
# Illustration using an unsaved Product, not a production database write.
product = Product(stock=20)
adjust_product_stock(product, [], 7)  # Existing reservation helper deducts seven.
# product.stock is now 13; the Products List must show 13, not 13 - 7.
```

`Product.get_total_stock()` delegates to `get_product_total_stock(product)` in `modules/marketplace/services/inventory.py`. Simple products use remaining `stock`; tracked option stock is summed, clamping invalid/negative values safely. Existing restoration returns quantities on cancellation. No additional reservation query is introduced.

### Quantity status and threshold

The view uses `get_inventory_status(stock=admin_total_stock)` without expiry/category arguments to classify this compact parent quantity:

- Available ≤ 0 → Out of Stock.
- 0 < Available ≤ `low_stock_threshold()` → Low Stock.
- Available > threshold → healthy; quantity only.

The threshold comes from `CAMPUSHUB_LOW_STOCK_THRESHOLD`, currently defaulting to five. JavaScript reads the same existing page meta value and uses `computeInventoryStatus(total)` without expiry inputs. The stock summary does not use product approval or the worst individual option status.

Existing inventory filter attributes and variant-level alerts retain their broader stock/expiry classification. A parent can have 21 units while one option is empty or low; its parent quantity is healthy, while the existing low-stock filter can still flag the affected option. This distinction prevents an empty size from labeling the entire product Out of Stock.

### Functions and data flow

1. `admin_products_page(request)` receives the authenticated request, selects products through the existing permission-scoped queryset, and supplies quantities/counts/quantity states to the template. Added attributes are transient Python values, not database fields.
2. Django renders each quantity-first cell and writes remaining quantity/variant count into the row's `data-*` attributes.
3. Existing product save APIs return serialized products whose `stock` is already `get_product_total_stock(product)`. `computeTotalStock(product)` mirrors canonical tracked-option aggregation; non-stock options never become fake units when product stock is zero.
4. `countProductVariants(product)` counts tracked options first, including legacy saved options; otherwise it reuses existing metadata. Untracked options can have a variant count, but their count never contributes to available quantity.
5. `renderInventorySummary(totalStock, variantCount)` accepts numeric quantity/count, returns escaped compact markup, and chooses quantity warnings using the configured threshold. `renderProductRow` uses it after the existing edit/create save flow.
6. The existing Save Stock handler reads `data.product`, recomputes its canonical total/count, updates the Inventory cell and row stock/options metadata, then calls the existing toast via `CampusHubAdminProducts`. This also preserves a correct parent total if the endpoint returns a variant aggregate different from the entered stock value.

## 5. Backend / API Behavior and Bundle Handling

No new API, route, business workflow or permission rule. Existing `serialize_product` already supplies remaining stock, variant metadata, options, inventory state and threshold. Approval statuses remain independent. Search/status/category filtering, Add Product, pagination and View/Edit/Archive controls remain in their existing locations.

Bundles cannot be derived from component inventory because that structure does not exist in the current backend. `Product` has no component foreign keys, quantities-per-bundle or persisted bundle type. The UI already blocks saving Bundle Product with “Bundle setup is not available yet.” This change preserves that block and adds no fake standalone bundle stock. A listing in the category **Combo Meals** is not evidence of a component-managed bundle; category text alone cannot identify components or required quantities. Derived bundle availability remains unavailable until an actual bundle workflow exists.

The optional Inventory link was not added: this task updates the cell display and retains the existing product actions without introducing navigation or another Inventory feature.

## 6. Database / Migration Impact

No model/schema changes or migrations. No production product/order writes were made for verification. Tests create and edit isolated records only. No extra stock/reservation query is added by the presentation summary.

## 7. Tests Performed / Manual Test Steps

- Full `modules.marketplace.tests` run: **24 passed, 1 failed**. The unrelated existing `test_listing_owner_shows_only_approved_sellers` expects `label="Approved Sellers"`, which the unchanged seller-owner control does not render. This update does not modify that control or loosen its test.
- Focused stock/price/inventory suites plus the new real-page regression: **14 passed**, with zero Django system-check issues. These checks include existing stock reservation/restoration and quantity/status independence.
- Node DOM integration passed initial real quantities, threshold **10** rather than a hardcoded five, all tracked option totals, no invented units from untracked options, separate approval, and existing edit/save rendering for simple and variant products.
- Existing Save Stock integration passed the returned quantity update and notification. Initial harness timing was shorter than the existing 900ms save delay; waiting for the actual save flow corrected that harness issue. The stock-toast ReferenceError was confirmed and fixed as described above.
- Two actual Chrome renders passed at 1440px and 500px: nine columns remain, Inventory content fits its cells, quantities are navy, and the narrow table scrolls inside its container without page overflow. Wide screenshot inspected. JS syntax and targeted whitespace checks passed.

Manual:

1. Refresh Products List; verify a healthy product shows quantity only, a low product has a warning, and a zero-stock product shows Out of Stock.
2. Compare the quantity with the canonical saved product/options after a real reservation: it should already reflect reserved units, with no second subtraction.
3. Check a product with several tracked options: the parent number sums every option, and the variant count is visible. A zero-stock size must not force the whole parent's quantity to zero.
4. Verify Pending/Approved/Rejected/Archived still belong to Status. Use the existing search, status/category filters and pagination.
5. Edit an isolated test product's stock, save, and verify the row changes without a reload. Also use the existing Save Stock control for a simple product and verify its cell and notification.
6. Check the Bundle form still refuses unsupported component setup. Do not create fake bundle records for this test.

## 8. Remaining Limitations / Debugging / Safe Practice

Component-derived bundles are not implemented in this project. The later Product Details update fixes the separate inventory KPI double subtraction using a shared backend snapshot; see [product-details-status-inventory.md](product-details-status-inventory.md). The list and the details now use the same canonical remaining quantity; Details reconstructs On Hand from actual valid holds. Compare the scoped product response if they disagree, rather than subtracting holds from the list quantity again.

The unrelated seller-owner-label regression remains open. Browser tests use actual Django fixture markup and stubbed save responses, not a logged-in production editing session. Existing APIs do not push stock changes automatically to other open browsers; refreshing the list still obtains the current records.

Debugging: if a pill remains, inspect template line 176 and the updated JS/CSS cache versions. If quantity becomes the number of variants, inspect `computeTotalStock` and `customizationHasStockTracking`; option count is metadata, not units. If low-state boundaries differ after a save, compare the meta threshold with `low_stock_threshold()` and inspect whether the quantity is the parent total rather than an individual variant. If a save succeeds but reports an error, check notification scope and the returned `data.product` before repeating a database write.

Safe practice: in an unsaved shell/test Product, create tracked options with stock 4, 6 and 0. Call `get_product_total_stock` and verify the result is **10**, not 4 or three variants. Under an isolated `override_settings(CAMPUSHUB_LOW_STOCK_THRESHOLD=10)`, classify that total and verify Low Stock; add one unit and verify healthy. Restore the fixture/settings, rerun the focused tests and `node scratch/products-inventory/check-column.cjs`. Do not edit production stock to practice.

