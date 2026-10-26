# Variant inventory — implementation, debugging and practice

Current October25,2026: [FIFO implementation and gated cutover](fifo-inventory.md) adds exact-SKU batch allocations through `fifo.sync_change` inside the existing Product.save/audit transaction. `fifo.receive` takes a scoped SKU/quantity/reference/user/key and returns a real receipt reference; order attachment/completion/cancellation preserve the existing available/reserved counters and original bundle snapshots. The working database remains unmigrated/inactive pending explicit cutover approval. The linked eight-part report contains exact files/lines, tests, errors, backup/dry-run and limitations. Safe exercise: run the isolated FIFO variant test, reorder the options and verify the same SKU batch is allocated/restored; do not alter working stock.

## Variant image picker icon - October 20, 2026

1. **Cause / reason:** the user requested an image icon instead of the ambiguous plus sign in the web Add Product variant-image field.
2. **Exact files changed:** `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:14` (stylesheet cache key), `:567` (`customization-option-image-placeholder`); `backend/static/components/css/admin_products.css:3992` (hidden preview/placeholder rules), `:3997` (SVG alignment); this guide and the project context note.
3. **Changes made:** replace only the variant image placeholder's plus text with a 20px outlined image SVG. Keep the existing 42px picker, accessible file input and preview. Explicitly honor `[hidden]` for both preview and placeholder; the preview's existing `display:block` must not reveal it before an image is chosen. Use CSS cache version `20261020-variant-image-icon`.
4. **How it works:** the existing variant option template is cloned by the existing product form code. `bindOptionImageInput(row)` reads a selected file, then `setOptionRowImage(row, imageUrl)` stores the current image and toggles `preview.hidden`/`placeholder.hidden`. Example: empty image URL -> image icon; selected image URL -> actual preview and hidden icon; cleared image -> icon restored. The SVG is decorative (`aria-hidden`); the file input retains `aria-label="Upload variant image"`. No new upload function/controller was added. Add Option still creates an option; its plus label was not replaced.
5. **Backend / API behavior:** existing product create/edit payloads, variant-image serialization, approval, ownership and stock calculations remain unchanged.
6. **Database / migration impact:** none; no products/images were submitted or modified during verification.
7. **Tests performed:** inspected the actual template in a headless DOM with the actual CSS. Confirmed the SVG replaces plus text, the file input remains accessible, the empty preview is hidden, and preview/placeholder states switch correctly. Scoped whitespace checks passed. No full marketplace regression run was needed for this icon-only change; the 20 Django tests reported in the concurrent reservation guide cover that separate change.
8. **Remaining limits / safe practice:** a live native file-picker interaction was not performed. Open Products -> Add Product -> enable variants -> add an option, confirm the image icon, choose a local image and check the preview, then cancel without submitting. If the icon is stale, refresh and check the new CSS URL. Do not replace the file input or the existing option-image handler to change this icon.

## Catalog consistency and top Inventory KPI update - 2026-10-08

This is the current report. Earlier reports below remain as history; their eleven-column table, department-only filters, estimated history links and earlier query/test counts are superseded here. Stock still comes from the same Django inventory service.

### 1. Cause / Reason

Confirmed by code/database inspection:

- Inventory totals were inside the table card and used a separate presentation. They now sit above the table and share the Products KPI styling.
- Department records mixed programs with BTLED majors. The actual database had BFPT, BSIT and BTLED-HE; the BTLED-HE record had no users/products. New program/major master records make HE a BTLED major without deleting the old record.
- Admin product/order access previously returned all marketplace records after a permission check. Program/Major scope is now also enforced on the server, including writes and report exports.
- Three existing products had no saved product program. One seller had a reliable BFPT assignment and two sellers had no assignment. One product was backfilled; the other two remain explicitly **Unassigned (legacy record)**. There is no reliable evidence to guess their programs.
- Browser click testing confirmed Archive/Restore called list helpers from another JavaScript scope. Shared helper access now updates actions/filters/toasts correctly. A saved row also now copies the full server payload, including SKU/Program/Major, instead of losing those fields until reload.
- Product Details used Product ID as SKU and its stock-history display had estimated past values. Details now use the same SKU/movement records as Inventory and show unknown historical balances as a dash.

### 2. Exact files, current lines and code anchors

Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Lines are current for this update; search the nearby anchor after subsequent edits. This table describes this task, not unrelated changes already present in the working tree.

| File | Current line / anchor | Added, changed, moved or removed |
| --- | --- | --- |
| `backend/core/accounts/models.py` | 19, `class ProgramMajor` | Department is retained as Program; add separate major relation and master-data flag. |
| `backend/core/accounts/academic.py` | 7, `def academic_options` | New shared labels, validation, master choices and permission scope helpers. |
| `backend/core/accounts/migrations/0024_program_major_structure.py` | 7, `class Migration` | Schema for ProgramMajor, User.major and Department.is_program. |
| `backend/core/api/models.py` | 63, `class Product(` | Reuse Product.department; add Product.major and unmanaged CampusHubUser.major. |
| `backend/core/api/migrations/0034_program_major_structure.py` | 7, `class Migration` | Product major schema and unmanaged mobile model state. |
| `backend/core/api/migrations/0035_program_master_data.py` | 5, `def normalize_programs` | Known program/major normalization, reliable owner backfill, mobile major column. |
| `backend/core/accounts/views.py` | 170, `def admin_products_page` | Scoped list/KPIs, actual programs/categories/sellers; same inventory route; scoped seller reviews/notifications; user assignment saves. |
| `backend/core/accounts/user_management.py` | 239, `def get_user_management_context` | Program/Major choices and saved assignments for admin/mobile accounts; join relations in batches. |
| `backend/core/accounts/forms.py` | 17, `class AdminUserCreationForm` | Program choices and cross-program major validation for account creation. |
| `backend/core/api/views.py` | 200, `def serialize_product` | Actual Product ID/SKU/program/major, shared inventory and recorded movements; creation validation and scoped review/write APIs. |
| `backend/core/modules/marketplace/services/product_access.py` | 16, `def admin_product_queryset` | Central product authorization reused by pages, stock/edit/archive APIs and images. |
| `backend/core/modules/marketplace/services/order_access.py` | 6, `def admin_order_queryset` | Scope administrator orders by program/major; seller ownership query retained. |
| `backend/core/modules/marketplace/services/inventory.py` | 519, `def build_inventory_table` | Same stock snapshot, batched academic/SKU data and exact variant rows. |
| `backend/core/modules/marketplace/services/inventory_monitor.py` | 16, `def inventory_monitor_context` | Program/Major AND filters, filtered KPIs, read-only detail and existing real movement source. |
| `backend/core/modules/marketplace/services/bundles.py` | 109, `def prime_bundle_inventory` | Batch labels/SKUs and recipes; no change to component deduction or availability. |
| `backend/core/modules/marketplace/services/analytics.py` | 613, `def build_marketplace_analytics` | Scope revenue, inventory, buyer comparisons and seller performance; initialize default chart date safely. |
| `backend/core/modules/reports/reporting.py` | 452, `def build_report` | Optional authenticated admin scope for marketplace previews/CSV/PDF. |
| `backend/core/modules/reports/views.py` | 1584, `def admin_marketplace_analytics_page` | Pass authenticated scope into dashboards, analytics and report routes; scope recent report list. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 22, `inventory_kpis.html` | Move four KPIs above/outside table card; automatic filters, twelve columns and ellipsis actions. |
| `backend/core/modules/marketplace/templates/marketplace/partials/inventory_kpis.html` | 1, `inventory-kpis` | Four backend totals reuse Products card classes. |
| `backend/core/modules/marketplace/templates/marketplace/partials/inventory_kpi_icon.html` | 1, `kind ==` | Reusable existing-style SVG icons. |
| `backend/core/modules/marketplace/templates/marketplace/partials/inventory_detail.html` | 12, `Program` | Replace ambiguous department display with Program and Major. |
| `backend/core/modules/marketplace/templates/marketplace/partials/product_actions.html` | 1, `col-action` | View/Edit/Archive or Restore, with compact pending Review actions. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 83, `product-catalog-filters` | Nine columns, automatic filters, seller/program/SKU labels, dependent major form, details/history/actions. |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 206, `data-academic-pair` | Program/Major account editor; populate and reset the correct major. |
| `backend/static/components/css/admin_products.css` | 4912, `Shared compact` | Shared 92px KPI design, responsive filters, compact menus, restrained warning colors. |
| `backend/static/components/js/admin_academic_controls.js` | 2, `CampusHubAcademic` | Show/enable only majors belonging to the selected program. |
| `backend/static/components/js/admin_inventory_filters.js` | 2, `data-auto-filters` | GET submission on change, 300ms search debounce, Escape/outside-click menus. |
| `backend/static/components/js/admin_products.js` | 2652, `function applyInlineFilters` | Combined list filters, program/major save/edit, separate Product ID/SKU, real movement rows and paid-completed summary. |
| `backend/core/modules/marketplace/test_program_inventory.py` | 25, `class ProgramInventoryTests` | New permission, validation, migration preservation, report and archive integration tests; isolated browser fixtures. |
| `backend/core/modules/marketplace/tests.py` | 269, `class MarketplaceAdminProductAccessTests` | Existing access fixtures now use assigned program; bounded SKU snapshot query expectations. |
| `backend/core/modules/marketplace/test_inventory_monitor.py` | 19, `class InventoryMonitorTests` | Actual program-master filter fixtures and migration restoration target. |
| `backend/core/modules/marketplace/test_variant_inventory.py` | 24, `def setUpTestData` | Existing create fixtures now have reliable program assignment. |
| `backend/core/modules/marketplace/test_thresholds.py` | 26, `def setUpTestData` | Existing threshold fixtures use a real program; stock boundary checks retained. |
| `backend/core/modules/marketplace/test_bundles.py` | 21, `class BundleProductTests` | Bundle form program fixture and constant catalog-query expectation including SKUs. |
| `backend/core/accounts/tests.py` | 668, `class MarketplaceAdminOrderAccessTests` | Replace old cross-program access expectation with restricted access and foreign-order denial; assigned account/dashboard fixtures. |
| `backend/core/modules/reports/tests.py` | 20, `class MarketplaceAnalyticsTests` | Analytics administrator/seller fixtures have matching program assignments. |

Useful additional anchors: `accounts/models.py:10` (`Department.is_program`) and `:45` (`User.major`); `api/models.py:47` (`CampusHubUser.major`) and `:87` (`Product.major`); `api/views.py:655` (`seller_submit_product`), `:792` (`admin_save_product`), `:1264` (`seller_products_monitor`); `admin_inventory.html:22` (KPI include), `:28` (automatic GET form), `:58` (twelve-column table); `admin_products.js:3298` (`populateInventoryHistory`) and `:3316` (`populateInventoryKpis`); `accounts/academic.py:56` (`scope_products`).

### 3. Changes Made - requested implementation checklist

| Requirement | Implemented behavior |
| --- | --- |
| 1-3. Files, lines, anchors | Listed above; documentation and verification files are listed below. |
| 4. Products columns | Nine columns: #, Product, Seller & Program, Category, Price, Inventory, Approval Status, Date Added, Actions. Product includes its real SKU; seller includes compact program/major. |
| 5. Products filters | Search, Approval, Listing, Program, dependent Major, actual Category, Clear Filters. Filters combine with AND and preserve the admin tab token. Search waits 300ms. |
| 6. Approval | Existing `Product.approval_status`: Pending/Approved/Rejected, independent of stock and archive flag. Pending Review actions remain. |
| 7. Listing | Existing `Product.is_archived`: Active/Archived. Default Active; Archived/All remain available. |
| 8. Archive/Restore | Existing soft archive/restore APIs. View/Edit stay available for permitted pending/archived records. No physical product/order/SKU/movement deletion. |
| 9. Archived visibility | Products retains archived rows for the Listing filter; normal Inventory omits them. Authorized historical SKU details remain accessible. |
| 10. Product Details inventory | On Hand, Reserved, Available, Threshold, Inventory Status use the shared snapshot. Tracked variants show their own quantities, thresholds and SKUs. |
| 11. Product ID vs SKU | Preserve `product_code` as Product ID. Use independent `InventorySKU` records, with "Per variant" for a variant-controlled parent's SKU summary. |
| 12. Inventory table | Product, Variant, SKU, Seller, Program / Major, On Hand, Reserved, Available, Threshold, Status, Last Updated, Actions. Remove variant price/group extras. |
| 13. Inventory KPIs | Four compact white cards ABOVE and OUTSIDE the table card. Same height/radius/padding/icon size/type as Products. Navy totals, gold low-stock icon, muted red out-of-stock icon as explicitly requested. |
| 14. Apply removal | No visible Apply button; changes submit the existing GET route. A noscript Filter button is retained for browsers without JavaScript. |
| 15. Clear Filters | Clears search/status/program/major/seller/category/product target and pagination while preserving authorization token. Products defaults back to Active listings. |
| 16. Program/Major model | Existing Department represents Program; new ProgramMajor belongs to Department. Existing Product/User department FKs remain; major is separate. |
| 17. IA/HE/ICT migration | Recognized standalone/BTLED-prefixed old records map to BTLED plus linked major. Retain old department rows for historical references. |
| 18. Not Assigned cause | Confirmed missing product assignment and, for two records, missing seller assignment. Other hypothetical causes were not assumed. |
| 19. Backfill | One reliable BFPT owner-to-product assignment; no inferred assignments for the two unknown records. Only institutional master metadata was created. |
| 20. Super Admin | Actual `is_superuser` remains unrestricted across marketplace records. Final active Super Admin protection remains unchanged. |
| 21. Program Admin | Assigned program and optional major enforced in page/API/report querysets and owner validation; missing assignment returns no marketplace records. |
| 22. Seller visibility | Seller reviews/notifications follow assigned scope; existing seller order ownership stays unchanged. Seller submission copies its actual assigned program/major. |
| 23. Stock movement source | `inventory_movements(sku)` supplies both Inventory and Product Details from InventoryStockMovement and verifiable legacy order events. No estimated opening/restock quantities. |
| 24. Normal/Low/Out tests | Boundary and reservation tests retained; normal quantity is quiet, low positive quantity is gold, zero is muted red. |
| 25. Archive/Restore tests | Integration verifies stock, SKU, movement and order records unchanged; total/approval counts persist and active low-stock alerts update. |
| 26. Limits | Listed in Section 8 below; no claim of a complete system-wide audit. |

### 4. How It Works - functions, inputs/outputs and data flow

`academic_options()` takes no row activity as input and returns Program and Major querysets. It reads marked master records, so BSIT/BFPT/BTLED and BTLED IA/HE/ICT remain selectable even with zero products, sales or users.

`resolve_academic(program_id, major_id, required=...)` takes submitted IDs and returns actual model objects. It rejects unknown programs, a major attached to another program, and a missing required product major. Account assignments allow a program administrator with no major to cover the whole program; a saved HE assignment restricts that administrator to HE.

`scope_products(queryset, user, prefix="")` takes a queryset plus the authenticated administrator and returns a restricted queryset. Direct Product assignment takes priority; only a null Product.department falls back to the seller. For orders, `prefix="product__"` follows their Product relation. `scope_users()` applies the equivalent assignment rule to sellers. Permissions are checked by the existing page/API wrappers before these helpers run. Super Admin bypasses scope; an unassigned program admin gets no rows.

`admin_products_page()` and `inventory_monitor_context()` receive the HTTP request and an authorized Product queryset. They return template context: real records, choices, filtered inventory totals, URLs and pagination. Products list filters operate on those authorized rendered rows; Inventory dropdown/search changes submit GET and Django re-filters the records.

`get_product_inventory_snapshot(product)` returns the existing quantity/status information and actual SKU identity. `build_inventory_table(products)` expands real tracked JSON variants and batch-loads holds, academic metadata, SKUs and bundle recipes. These functions do not create a second stock store.

Important storage detail: CampusHub already deducts Available when an order is reserved. Therefore the implementation reconstructs `On Hand = stored Available + valid active holds`, and displays `Available = On Hand - Reserved`. Subtracting holds from stored stock again would be wrong. Example: saved Available 7 plus 3 reserved gives On Hand 10, Reserved 3, Available 7.

Each tracked variant uses its own saved threshold (existing setting only as legacy fallback). Low Stock means `0 < Available <= Threshold`; Out of Stock means `Available <= 0`. A parent summary adds tracked quantities and reports the variant count/positive low variants. Product approval is never used as stock status.

Bundles retain `min(floor(component Available / required quantity))`, combining repeated demands on the same stock pool. Exact component variants and purchased recipes still determine reservation, cancellation and sale handling. Bundles have a SKU identity but no fake standalone On Hand/Reserved/threshold. The bundle remains one sellable item in orders and analytics.

`serialize_product(..., include_inventory=True)` returns program/major/Product ID/SKU plus the shared inventory snapshot and recorded movements. `populateInventoryHistory()` consumes `date`, `kind`, `quantity`, `before`, `after`, `reference`, `actor`, `sku` to render seven columns. Inventory reads the same source per SKU. Failed detail loads show Unavailable and a history error rather than permanent Loading or fake zeros. `syncProductStatsFromRows()` at `admin_products.js:2406` refreshes the four Products totals from the complete server-authorized row dataset after save/review/archive/restore; listing filters and pagination do not count as deletion. A legacy sale with no known before/after balance displays a dash, not an estimate.

`prime_bundle_inventory()` batch-loads catalog metadata and recipes. The constant-query regression verifies 3 catalog reads (products with academic joins, SKUs, recipes) and 4 bundle inventory reads (those plus active holds). It avoids one program/SKU query per row.

Annotated read-only example:

```python
# An order has no direct Program FK: follow its Product relation.
orders = scope_products(MarketplaceOrder.objects.all(), request.user,
                        prefix="product__")
# Only the administrator's permitted orders reach reports/analytics.
```

### 5. Backend / API Behavior

- Existing routes are retained: `/admin-products/`, `/admin-products/?view=inventory`, existing save/stock/archive/restore/approval APIs, seller monitor and existing report preview/download routes. No new Inventory detail page or duplicate approval workflow.
- Inventory row ellipsis exposes View Details, Stock Movements and View Product. Product inventory navigation includes its real product ID; SKU detail links preserve filters and the authorized tab token. No Add Stock button in Super Admin Inventory/details.
- New/edited product Program and required Major are validated on the server; the assigned seller must match. Choosing another admin scope or owner is denied. Out-of-scope product writes return 404/403 without exposing that product.
- Admin seller selections are scoped and the selector is visible to permitted product managers, including program administrators. Account editors save/reset the real Major.
- Marketplace reports, dashboards, analytics, notifications and seller review actions receive authenticated scope. Existing facility/system report logic stays separate.
- Revenue/Sales Summary includes only completed AND paid Cash on Pickup orders. Grouping, archive visibility and inventory status do not replace the existing payment/order rules.
- Existing stock deduction/restoration remains transactional and acts on exact variants/components. No extra deduction at sale completion.

### 6. Database / Migration Impact

Applied to the current database: `accounts.0024_program_major_structure`, `api.0034_program_major_structure`, `api.0035_program_master_data`.

Schema: `Department.is_program`, `ProgramMajor` (unique program/code), nullable `User.major` and `Product.major`. No stock/threshold duplicates. The unmanaged PostgreSQL `campushub_user` table receives `major_id` if it exists; it is not converted into a managed model.

Data: create/mark the three explicitly required program masters and BTLED's three majors, normalize recognized legacy major assignments, and backfill reliable owner assignments. Retain unknown departments and old FK records. During the applied migration, before/after fingerprints of product stock/options/owner/archive/approval, orders, SKU records and movements matched. These were not cleared or replaced.

The data migration reverse operation is a no-op: automatic rollback does not guess original owner/program assignments or delete historical departments. Restoring an earlier academic assignment requires an explicit, reviewed data correction. If deploying into an installation where unmanaged `campushub_user` does not exist yet, ensure its eventual schema also has `major_id` before using account management.

### 7. Tests Performed, manual verification and debugging

Ran, not assumed:

- **209 Django tests passed** across `modules.marketplace`, `accounts`, `modules.reports.test_dashboard_low_stock` and `modules.reports.tests`. This includes normal/low/out boundaries, reservations/restoration, variants, bundles, archive/restore, SKU stability, real history, routes and permissions.
- **32 overlapping follow-up tests passed** for the final program/analytics changes; **7 overlapping account-management tests passed** after academic relation batching. Do not add these counts to 209 as unique tests.
- Nine real Chrome checks: Inventory populated/detail/empty states at 1440px, 1024px and 375px; contained horizontal scrolling, focusability, field fit, twelve columns and thirteen detail fields.
- Actual isolated Django HTML/API fixtures exercised the shipped JavaScript: nine Products columns; search debounce; AND Program/Major filters; Clear; archived/all listings; actual Archive/Restore clicks with unchanged total and updated low-stock KPI; saved row SKU/Program/Major; real SKU/history and API-failure states; Inventory auto GET; clearing Major on Program change; Escape/outside-click menus. No JavaScript errors in this check.
- Existing single/bundle form checks passed: selection, exact component variant, derived price/savings/availability, save/edit, details and retry; screenshots at 1440px, 500px and 375px.
- `manage.py check`, `makemigrations --check --dry-run`, JavaScript syntax checks passed. All three migrations show applied.

Verification artifacts: `scratch/inventory-monitor/catalog-regression.log`, `analytics-final.log`, `user-final.log`, `browser-layout.log`, `browser-form.log`; `check-ui.cjs`, `check-catalog-behavior.cjs`, and `scratch/component-bundles/check-form.cjs`. HTML/JSON/screenshots use isolated test database records, not invented production rows. Helper migration/fixture-update scripts in scratch are one-off QA artifacts; do not rerun editing scripts casually.

Manual steps:

1. Restart Django if needed, hard refresh with Ctrl+F5, open Marketplace > Inventory. Check four cards ABOVE the single table card; compare padding/icon/type to Products.
2. Select a program. BTLED enables IA/HE/ICT; BSIT/BFPT disable Major. Change stock/seller/category filters; type search and check the URL updates after the short delay. Clear Filters restores the complete authorized active inventory.
3. In Products, choose Active/Archived/All; search by real SKU/seller/name. Review pending records; archive then restore a development record. Verify its orders/history/SKU remain and totals do not count archive as deletion.
4. Open the same product in Products Details and Inventory Details. Compare SKU, Available, threshold and its actual recorded movement quantity/reference/user. For variants compare the exact variant, not its parent's total.
5. Create/edit a development product with an assigned seller. Verify saved Program/Major after reopening. Choose a mismatched major and confirm the server rejects it.
6. Sign in as a BTLED-HE admin. Check products/inventory/sellers/orders/analytics/report CSV contain HE only; try an IA product ID through save/archive/stock and confirm denial. Super Admin can inspect both.
7. For stock behavior, use isolated tests: 20 available/threshold 5 is normal; 3/5 low; 0/5 out. Reserve 3 from On Hand 10 and verify Available 7, then cancel and verify restoration. A low variant appears by name; a bundle availability follows its limiting component.

Debugging guide:

| Symptom | Confirmed cause or check | Where to look / verification |
| --- | --- | --- |
| Program unassigned on two old records | Seller AND product have null assignment; confirmed database evidence | Correct that owner's real Program/Major through User Management, then edit the listing; do not guess from product name. |
| Program admin sees no records | Missing assignment now fails closed, or the selected major has no records | User editor, `scope_products`/`scope_users`; verify actual FKs and permission separately. |
| Major belongs to another program | Invalid client selection or stale form state | `resolve_academic`; select BTLED before its major. Backend remains authoritative. |
| Old KPI position/Apply still visible | Browser may have cached prior assets; hypothesis if latest template is correct | Ctrl+F5; check `admin_inventory.html:22` and asset version `20261008-catalog-programs`. |
| Available looks too small | A second subtraction would double-count existing holds | Compare snapshot's saved Available and active holds; reservation regression proves 10/3/7. |
| Archive succeeds but actions do not refresh | Confirmed JavaScript scope mismatch; corrected through shared CampusHubAdminProducts helpers | Actual Archive/Restore click test, helper exports at `admin_products.js:2805`. |
| Newly saved row loses Program/SKU until refresh | Confirmed save code copied only older fields; now merges the full server response | `Object.assign(productData, savedProduct)` at `admin_products.js:2297`; form browser test verifies saved row metadata. |
| Old history has dashes | No verifiable before/after balances in legacy order records | `inventory_movements`; do not reconstruct opening stock by adding orders to current stock. |
| Query count rises with row count | Missing batch relation/recipe prefetch | `prime_bundle_inventory`, constant-query test. Standalone snapshots intentionally load SKU + holds. |
| Filtered KPI differs from all-products count | Inventory totals use filtered SKU/variant rows; Products total uses preserved product records | Clear filters, compare SKU count vs Product count; they measure different things. |

Learning practice (isolated test data only): open `test_program_inventory.py`, locate `test_program_and_major_filters_intersect`, change its selected program from BTLED to BSIT, and predict why its expected HE row becomes empty. Change the expectation to 0 and run just that test, then undo the practice edit. Next read `scope_products` and explain why an explicit Product program overrides seller fallback. Verification: the isolated test passes with your correct expectation; no real products or customer orders are edited.

```powershell
cd backend/core
venv/Scripts/python.exe manage.py test modules.marketplace.test_program_inventory.ProgramInventoryTests.test_program_and_major_filters_intersect --noinput
```

### 8. Remaining Limitations

- Two real legacy products remain unassigned because their sellers have no reliable program. A legitimate assignment is required, not a fabricated default.
- Old stock movements without audit balances cannot supply before/after values; the latest 100 events are shown. Direct SQL/QuerySet updates bypass Product.save's audit hook; use the existing inventory save/order workflows.
- Program admins with a program but no Major cover the whole program. Assign HE/IA/ICT when access should be limited to one major. Unknown legacy departments are retained for history and are not offered as program masters.
- Product list filtering is client-side over the already-authorized rendered dataset; large catalog server-side pagination/filtering optimization is outside this change. Inventory currently expands the scoped active inventory before filtering/pagination, preserving the established stock behavior.
- The native Inventory action menu expands within its row so it remains usable inside a horizontally scrolling table. Expanded rows are temporarily taller; closed rows remain compact.
- No Flutter UI or entire-system audit is included in this task. Backend product payloads expose Program/Major; account data uses the existing admin/mobile stores. The default Django account change form was not redesigned.

---

Historical Inventory monitoring report below: retained for earlier implementation details; the current catalog update above supersedes its UI/filter/query-count notes.

## Inventory monitoring update — 2026-10-08

### 1. Cause / Reason

Inspection confirmed three gaps: the SKU display reused `Product.product_code` (a Product ID), Inventory lacked department/seller/category filters and compact totals, and the old Product Details history estimated initial stock/restocks from orders. Those estimates could not prove a stock movement happened. The existing eleven-column layout and stock calculations were retained while these gaps were fixed.

CampusHub has no separate ProductVariant or Category model. Tracked variants live in `Product.customization_options`; categories are actual `Product.category` text; Product and Seller can each reference the existing Department model. New SKU identities and movement records describe that existing inventory, without moving quantities into another stock table.

### 2. Exact files, current lines and nearby anchors

Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Lines refer to this implementation; search the code anchor if later edits move them.

| File | Approximate line / anchor | Added, changed or removed |
| --- | --- | --- |
| `backend/core/api/models.py` | 132 `Product.save`; 865 `InventorySKU`; 886 `InventoryStockMovement` | Save observed stock changes atomically; persist a separate SKU identity and real movement metadata. Existing quantities and threshold fields remain the source. |
| `backend/core/api/migrations/0033_inventory_sku_and_movements.py` | 8 `create_existing_skus`; `CreateModel` | Create two metadata/audit tables and assign existing simple/variant/bundle identities. Do not invent past movements. |
| `backend/core/modules/marketplace/services/inventory_records.py` | 5 `sku_parts`; 24 `sync_inventory_records`; 58 `attach_reservation_movements`; 65 `order_allocations`; 101 `record_completed_sale` | Generate readable identities; compare persisted stock; connect order events to the exact stock pool, including retired variants and purchased bundle snapshots. |
| `backend/core/modules/marketplace/services/inventory_monitor.py` | 16 `inventory_monitor_context`; 78 `inventory_detail`; 101 `inventory_movements` | Combine filters, calculate totals, preserve navigation, authorize details and show genuine recorded/order history. |
| `backend/core/modules/marketplace/services/inventory.py` | 508 `inventory_sku`; 515 `build_inventory_table`; 560 `adjust_product_stock` | Read persisted SKUs in a batch; add actual metadata and mark existing reservation/release writes. |
| `backend/core/modules/marketplace/services/bundles.py` | 166 `reserve_bundle`; 190 `restore_bundle` | Attach component movement IDs to the purchased bundle order and record exact component releases. Recipe/deduction formulas remain unchanged. |
| `backend/core/accounts/views.py` | 178 `inventory_monitor_context`; 1083 `restore_bundle`; 1087 `_inventory_order_id`; 1101 `record_completed_sale` | Render the existing Inventory route, retain pagination and record order cancellation/completion events in the existing transaction. |
| `backend/core/api/views.py` | 977 and 1088 `_inventory_actor`; 1959 `attach_reservation_movements` | Use the actual stock editor's identity and associate checkout reservations with the created order. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 25 `inventory-monitor-summary`; 31 `inventory-page-filters`; 55 `inventory_detail`; 58 `<thead>`; 78 `View Details` | Add four compact totals, five labeled filters, details/history actions and the exact filter-empty state. Keep eleven columns and the current page shell. |
| `backend/core/modules/marketplace/templates/marketplace/partials/inventory_detail.html` | 2 `inventory-details`; 21 `inventory-movements`; 24 `inventory-component-links` | Read-only metadata/quantities and real movement history within the existing Inventory page; bundles link to their actual components. |
| `backend/static/components/css/admin_products.css` | 1285 `Inventory`; 1291 `inventory-monitor-summary`; 1297 `inventory-monitor-detail`; 1320 `inventory-ledger-table` | Desktop filter row, wrapping narrow filters, compact totals/details, internal table scrolling and dedicated numeric alignment. |
| `backend/static/components/js/admin_products.js` | 3277 `populateInventoryHistory` | Remove estimated opening/restock rows; link Product Details to real recorded history in Inventory. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 14 CSS version; 1054 script version | Refresh asset versions so browsers receive the new history function and styles. |
| `backend/core/modules/marketplace/test_inventory_monitor.py` | 19 `InventoryMonitorTests`; 221 retired-variant test; 245 `InventorySKUMigrationTests` | Test SKU identity, filters, totals, navigation/auth, audit correctness, rollback and migration safety. |
| `backend/core/modules/marketplace/test_variant_inventory.py` | 170 `test_inventory_batches_reservations_and_preserves_simple_legacy_stock`; 187 `test_inventory_variant_skus_survive_reordering_and_stock_changes` | Update real-page/query assertions for stored SKU identities and stability. |
| `backend/core/modules/marketplace/test_bundles.py` | 252 `test_batch_inventory_and_catalog_have_constant_queries` | Account for the batched SKU registry query; preserve derived availability checks. |
| `scratch/inventory-monitor/run-tests.py`; `scratch/inventory-monitor/check-ui.cjs` | test runner; Chrome viewport checks | Reproducible local QA, logs and isolated HTML/screenshots. These are not application features. |
| `docs/variant-inventory.md`; `docs/component-bundles.md`; `docs/product-details-status-inventory.md`; `CAMPUSHUB_CONTEXT.md` | current update at the beginning | Explain the implementation, supersede old SKU/history advice and preserve learning/debugging guidance. |

### 3. Changes made

The final table is **Product / Variant / SKU / Seller / On Hand / Reserved / Available / Threshold / Status / Last Updated / Actions**. Healthy stock stays quiet; no new status pills or primary Add Stock action were added. Low Stock is gold; normal and Out of Stock text are navy, with the wording identifying their different states. This Inventory styling follows the current navy/gold/white project rules, superseding the older muted-red text exception in the historical report below.

SKU is separate from Product ID. Its persisted short prefix comes from the product name, an optional variant abbreviation comes from that variant, and its sequence is the SKU registry's own primary key. Bundles use `BND`. For example, the format can be `ADI-001`, `UNI-M-002` or `BND-003`; these are format examples, not inserted products. The registry ID makes the complete code unique; padding expands after 999 rather than truncating. Renaming a product, changing Product ID, changing quantities or reordering options does not change existing SKUs. No seller SKU input was added. Renaming a variant creates a new identity and retains the old identity/history.

Actions are **View Details**, **Stock Movements**, and **View Product**. The first two open read-only information in the existing Inventory page, with an anchor to the requested section. View Product uses existing Product Details. Archived products are excluded from the default table but their authorized SKU details/history remain accessible.

### 4. How it works: functions, inputs, outputs and data flow

#### Filtering and row calculations

`inventory_monitor_context(request, authorized_products)` receives GET parameters and an already authorized Product queryset. It applies seller/category/product filters in SQL. Department uses the listing's Product.department when assigned, otherwise Seller.department. It calls `build_inventory_table` to expand each actual tracked option, then matches search/status on those exact rows. It returns template context, four totals, filter choices, detail data and URLs. `admin_products_page` paginates those rows, thirty at a time.

Search is case-insensitive and matches **Product Name, Variant Name, SKU and Seller Name**. Searching Medium returns that matching inventory row, rather than every sibling because Medium exists somewhere in the parent's JSON. Product ID is no longer treated as SKU.

Filters intersect with **AND**: Search + Inventory Status + Department + Seller + Category must all match. Status uses the existing classifier: Available <= 0 means Out of Stock; positive Available <= the row's threshold means Low Stock; Available > threshold means In Stock. Missing configuration/unknown allocation is displayed honestly as Unavailable when applicable. Department options load Department records; sellers are actual owners of scoped non-archived products; categories are distinct actual category values. Invalid explicit filter values return no matching rows.

Selections persist in GET parameters, pagination and View/Back links. Tab authorization (`__at`) is retained independently of filters. Reset/Clear Filters removes search/status/department/seller/category/product/page selections and preserves only Inventory mode and any tab authorization.

`build_inventory_table(products)` batches product/seller/department metadata, SKU identities, real active reservations and bundle recipes. Normal Inventory reads use three queries, or four when recipes are needed, rather than one extra query for each variant. It outputs one row per tracked stock pool. A parent identity for a variant product is metadata, not a displayed/countable additional stock row.

**Stock formula remains Available = On Hand - Reserved.** Existing CampusHub checkout already deducts the hold from saved `Product.stock`/option.stock; the saved amount represents Available. The view reconstructs On Hand = saved Available + actual Reserved. It must not subtract the hold a second time.

```python
# Learning example only; no production records are created by this snippet.
available = 1    # Large's saved JSON stock after reserving three units.
reserved = 3     # Its exact active deducted, unrestored order quantity.
on_hand = available + reserved  # 4 physical unsold units.
threshold = 2   # Large's own configured level.
# 4 - 3 = 1 available; 0 < 1 <= 2 -> Low Stock.
```

Tracked variants keep their own quantities, holds and thresholds. Legacy untracked customization choices do not acquire fake inventory. Simple products retain product-level quantities/thresholds. A bundle retains **derived availability = min(floor(component available / required demand))**, combining repeated demands against the same stock pool. Its physical On Hand/Reserved/Threshold are dashes. Exact selected component variants are used; no bundle quantity field or threshold was added.

#### Compact totals

Totals describe **all matching rows before pagination**, not just the current page:

- Total Inventory Items = number of displayed simple/variant/derived-bundle rows.
- Low Stock Items = rows classified Low Stock.
- Out of Stock Items = rows classified Out of Stock.
- Reserved Units = known physical simple/variant holds, excluding derived bundle rows to avoid double-counting their components. Unknown physical holds make this total Unavailable instead of a fabricated zero.

#### Actual movement history

`Product.save` locks the previous stock values and saves within `transaction.atomic`. `sync_inventory_records` reads the **persisted** after-values (important for partial saves and F expressions), ensures identities and records actual deltas. It receives the saved product, previous pool values and DB alias; its outputs are persisted metadata/events and movement IDs used by checkout. A failed transaction rolls back stock and audit together. Metadata-only partial saves do not generate stock changes.

`attach_reservation_movements(product, order)` links those reservation IDs after the existing order is created. Cancellation records a release on the exact simple/variant/component pool. `record_completed_sale(order, actor)` records a physical **On Hand** reduction once per SKU/order, without deducting Available again. Purchased bundle snapshots take precedence over the current recipe. `order_allocations` matches stored selections against retained SKU identities, so an old Small order remains Small history after the product is converted to simple inventory.

The distinction matters: a reservation of two changes Available by -2; completing it changes On Hand by -2 and releases the existing hold. These are different balances, not four physical units sold.

`inventory_detail(sku_id, authorized_products)` authorizes the requested identity and returns metadata/current quantities. Retired variants retain history but show current quantities as unavailable. `inventory_movements(sku)` returns the latest 100 actual audit events plus verifiable old deducted-order events. Old reservation dates come from order creation; old releases/sales require actual cancelled/completed timestamps. Covered audit events are not duplicated. Unknown historical before/after stock is never guessed. Actors are actual supplied identities or System for known workflow events; unrecorded actors remain a dash. Positive edits are called **Stock adjustment**, rather than asserting an unsupported restock reason.

Why this approach: Product/JSON stock and the existing order workflow stay authoritative; an audit records what actually changed. It replaces the previous JavaScript estimation, which could misinterpret outstanding holds, later restocks and incomplete history.

### 5. Backend / API behavior and existing routes

- Page and detail: existing `/admin-products/?view=inventory`; details add `inventory_item=<SKU registry id>` and preserve the current filters/page.
- Product: existing `/admin-products/?product_id=<Product id>`.
- Dashboard Low Stock **View All** already points to `/admin-products/?view=inventory&inventory_status=low_stock`. It was retained, and existing dashboard tests verify that connection; no duplicate dashboard counts or route were added.
- Existing server-side product-module permissions and product scope guard both listing and detail requests. Changing a URL does not bypass them. Invalid/unauthorized identities are not exposed.
- Existing save/stock/order APIs keep their request/response contracts and deduction/restoration logic. They now supply actual actor/order metadata to the audit. No new public API, Stock On Hand field, warehouse field or restock button was added.
- No Flutter code changed in this follow-up. Existing mobile checkout uses the same Django order path; device behavior was not retested.

### 6. Database / migration impact

**Applied `api.0033_inventory_sku_and_movements` to the configured database.** It adds `campushub_inventory_sku` and `campushub_inventory_stock_movement`, the product/group/variant identity constraint and movement lookup index. `create_existing_skus` assigns identities to existing simple products and tracked options, including archived products. It does not change Product IDs, quantities, JSON variants, thresholds, recipes or orders, and does not create fictional opening/restock history.

Verification compared Product stock/options/code/threshold/type and order stock-related fields before and after migration: **unchanged**. The configured database had three assigned identities and zero backfilled movement records. Tests create fixtures only in the separate test database; no sample products were added to live Inventory.

For another development installation, after updating code run from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

### 7. Tests performed and manual test steps

Actual verification for this follow-up:

- **92 targeted Django tests passed**: Inventory monitoring/migration, variant stock, bundles, thresholds, existing stock/pricing endpoints, dashboard low-stock and admin order workflow. The new monitoring suite includes rollback, partial saves, authorization tokens and retired-variant history. Output: `scratch/inventory-monitor/django-tests.log`.
- **Nine Chrome Inventory checks passed**: table/detail/empty states at actual 1440px, 1024px and 375px CSS viewports. Checks cover four totals, five ordered filters, eleven columns, desktop filter alignment, numeric alignment, detail fields and internal scrolling without page overflow. Exported Django test HTML uses the actual application styles. Screenshots are in `scratch/inventory-monitor/`.
- Existing Product form Chrome checks passed for single/bundle mode, real selection records, price/savings/availability, save/edit, derived details and Retry, including narrow layout. Log: `scratch/inventory-monitor/product-form-check.log`.
- Django system check returned zero issues; `makemigrations --check --dry-run` returned No changes detected; `showmigrations api` confirmed 0033 applied. Node syntax checking of `admin_products.js` and scoped `git diff --check` passed. This is targeted verification, not a claim that the entire application/device suite passed.

Repeat the feature tests from the repository root with `.\backend\core\venv\Scripts\python.exe scratch/inventory-monitor/run-tests.py`. Run browser layout review with `node scratch/inventory-monitor/check-ui.cjs` after tests export the isolated HTML fixtures. These helpers use test data, not production inserts.

Manual test on an isolated development installation:

1. Hard-refresh with **Ctrl+F5**, open Marketplace → Inventory, confirm eleven columns and compact totals. Compare SKU with Product ID: they should be separate identifiers.
2. Search an actual product, then a specific variant, then that row's SKU. Only matching stock rows should remain; try seller name too.
3. Combine actual Department + Seller + Category + Low Stock. Every result must match every selection. Test a product with its own department to verify it takes priority over the seller's department.
4. Test a row equal to its own threshold, above it and at zero. Confirm Low Stock / In Stock / Out of Stock respectively. No fake quantity should replace unknown data.
5. With more than thirty matching rows, visit Next, open View Details/Stock Movements and use Back. Filters and page remain selected. Reset clears all selections. A nonsense search shows the exact empty message and Clear Filters.
6. Dashboard → Low Stock Products → View All: Low Stock is visibly selected and every result is actually low stock.
7. In test data, reserve a specific variant, cancel it once, then complete a different order through the actual permitted workflow. Verify exact variant quantities and Reservation/Reservation released/Sale records; completion must not deduct Available twice.
8. Check a bundle: derived units and physical dashes, no standalone stock edits/movements. Follow component links to their actual inventory and verify purchased component quantities.
9. Edit test stock via the existing authorized editor. Verify the recorded delta, time and actor; other variants remain unchanged. Check a pre-migration product: old unrecorded restocks remain absent.
10. Archive a test product. It disappears from the default table, while an authorized saved detail link retains history. Check desktop/tablet/narrow screens and scroll the table internally to Actions.

### 8. Debugging, remaining limitations and safe practice

Confirmed findings and fixes:

- **SKU was Product ID:** replaced the display-only `product_code`/hash approach with its own registry identity. If Unassigned appears, confirm migration 0033 ran; do not substitute PRD again.
- **Estimated history was unreliable:** removed that JavaScript calculation. Product Details now links to Inventory's recorded history. Empty old history is expected when no evidence exists.
- **Partial-save audit could compare unsaved fields:** after-values now come from the persisted row. The test changes JSON in memory but saves only parent stock; no invented variant adjustment is logged.
- **Retired variants could be reassigned to parent history:** allocation now checks retained SKU keys before the current inventory shape. The test converts completed-order stock to simple inventory and verifies the original variant retains its order events.
- **Generic number CSS conflicts:** `.inventory-number` belongs to Products List and applies block/center rules. Inventory uses `.inventory-ledger-number` to keep proper table cells/right alignment.
- **Test-database cleanup failure:** a reused legacy facility table referenced the User fixture outside the installed model cleanup set. The migration test scopes `available_apps`, allowing test-only cascading cleanup; the full targeted run now passes. No production records were cleaned up to solve this.
- **Old browser assets:** template asset versions were advanced. Confirm the loaded script URL contains `20261008-inventory-history` before debugging an old estimated table.

Limits: historic restocks without records cannot be recovered; history is capped at 100 events. Raw SQL, `QuerySet.update` and `bulk_create` bypass `Product.save` and therefore its audit hook—maintenance/import tools must explicitly integrate recording if they change stock. Variant/group renaming creates a new identity, while reordering/stock changes retain it. Expanded rows are currently processed before pagination, so very large catalogs may need further SQL/indexed optimization. Each option shares its Product update timestamp; bundle Last Updated is the bundle listing update, not the latest component event. The eleven-column table intentionally scrolls inside its card at narrow widths. Full-system and mobile-device testing remain separate work.

**Safe learning exercise:** on a development branch, change only the Search placeholder in `admin_inventory.html` (anchor `name="search"`) to “Search product, variant, SKU or seller...”. Explain to yourself that `name` sends the GET key and `value` restores the selected text; `placeholder` is just help text. Do not change the `name` or stock functions. Run the Inventory tests, open the page, search an actual SKU and confirm the query string still contains `search=` and the result matches. Restore the original placeholder, then rerun the browser check if you changed layout. This teaches how one template field connects to a backend function without modifying inventory records.

## Previous Inventory table update — 2026-10-07 (historical)

This historical follow-up introduced the eleven-column Inventory page. Its display-only SKU approach was replaced by the current monitoring update above. The original report further below records earlier seven-column work.

### 1. Cause / Reason

Inspection confirmed that the active Inventory template **already said On Hand**, rather than Stock On Hand. It had seven columns and omitted SKU, Seller, Last Updated and Actions. Both Low Stock and Out of Stock were gold. The user requested the complete eleven-column table, retaining real inventory calculations and muted red only for the Out of Stock text.

### 2. Exact files, current lines and nearby anchors

All paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Search the code anchor if later changes move a line.

| Changed file | Current approximate line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/inventory.py` | 508 `inventory_sku`; 521 `build_inventory_table`; 550 `"sku"` | Generate read-only display SKUs and attach actual seller/update metadata to each existing stock row. Load sellers in a batch. Only a positive derived bundle gets the display label Available. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 12 stylesheet version; 41 `<thead>`; 52 `inventory-sku`; 59 `inventory-updated`; 60 `inventory-row-action`; 62 `colspan="11"` | Retain On Hand, add four requested columns, show Bundle/dashes/derived quantities, format real update timestamps in Philippine Time and link View to existing Product Details. |
| `backend/static/components/css/admin_products.css` | 1289 `inventory-table-scroll:focus-visible`; 1290 `inventory-ledger-table`; 1294 `inventory-ledger-number`; 1302 `inventory-ledger-status--out_of_stock` | Keep compact rows and internal scrolling. Align only numeric cells right; use gold Low Stock and muted red Out of Stock text without pills or green badges. |
| `backend/core/modules/marketplace/test_variant_inventory.py` | 137 `test_inventory_rows_list_summary_and_dashboard_use_same_variant`; 170 `test_inventory_batches_reservations_and_preserves_simple_legacy_stock`; 185 `test_inventory_variant_skus_survive_reordering_and_stock_changes` | Extend real page/order checks for headers, row metadata, the formula, seller batching and variant SKU stability. |
| `backend/core/modules/marketplace/test_bundles.py` | 252 `test_batch_inventory_and_catalog_have_constant_queries` | Verify derived quantities, absent physical stock, Bundle/Available rendering and the existing three-query bound. Export isolated fixture HTML only when the review environment variable is set. |
| `scratch/inventory-columns/check-layout.cjs` | 1 read-only review script; 21 generated metrics script | Render isolated Django fixture HTML with the real CSS in Chrome; check eleven columns, alignment, focus, scrolling and colors at desktop/375px. This is a QA helper, not application code. |
| `docs/variant-inventory.md` | 5 `Latest Inventory table update` | This current report, debugging guidance and learning exercise. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest Inventory table update` | Preserve the accepted column order, SKU behavior and unchanged inventory source for future work. |

Reused without modifying: `accounts/views.py` around 172 `admin_products_page`, `api/models.py` around 80 `product_code` and 104 `updated_at`, and the existing order/bundle stock services.

### 3. Changes made

The final order is **Product, Variant, SKU, Seller, On Hand, Reserved, Available, Threshold, Status, Last Updated, Actions**. The current On Hand wording is preserved; no Stock On Hand label remains on this page. SKU and seller are text columns; the four stock columns are right-aligned. The existing search, status/product filters, 30-row pagination, sidebar and card layout remain.

Tracked variants keep separate rows, actual option thresholds and reservation quantities. Simple products show — under Variant. Bundles show Bundle, — for On Hand/Reserved/Threshold, the actual derived quantity with bundle/bundles grammar, and Available when positive. The previous Derived from components helper stays. Zero bundle availability remains Out of Stock; components retain their own low-stock alerts.

Last Updated uses the product's actual `updated_at`, formatted in Asia/Manila with an ISO `<time>` attribute. View uses the existing `/admin-products/?product_id=<id>` route. No new page, stock editor or manual SKU input is added.

### 4. How it works — functions, inputs, outputs and data flow

| Function or field | Input → output / responsibility |
| --- | --- |
| `inventory_sku(product, group="", variant="")` | Existing Product plus the row's group/name → a read-only SKU string. Use saved `product_code`, falling back to `PRD-` plus the database ID padded to four digits. A variant adds `-V` plus ten uppercase SHA-256 characters from its JSON-encoded group/name pair. |
| `build_inventory_table(products)` | Already authorized queryset/list → flat dictionaries for the template. Querysets join the existing Seller; lists batch-load missing sellers. Reuse bundle preloading and one actual hold query, then add `sku`, `seller_name`, `updated_at` and the existing Details URL. |
| `get_product_inventory_snapshot(product, reservation_rows=...)` | Actual product/option stock plus supplied real holds → existing On Hand/Reserved/Available/threshold/status rows. Its calculation is unchanged. |
| `Product.seller` | Existing account → full name, falling back to username when blank. No seller values are fabricated. |
| `Product.updated_at` | Existing persisted timestamp → display date/time. There is no per-variant timestamp field. |

The variant SKU suffix uses names, rather than list positions, because rearranging Small/Medium/Large should not change their display codes. Changing quantity, threshold or price also leaves the suffix unchanged. Codes are generated on read; opening Inventory never saves them into a new field. Existing order selections and `variant_key` still determine stock changes, not this display SKU.

Data flow: permission-scoped products in `admin_products_page` → existing search/product filters → `build_inventory_table` → joined sellers, optional batch bundle recipes and actual order holds → existing stock snapshots → stock-status filter and 30-row pagination → eleven-column Django template → existing Product Details when View is clicked.

Available remains **On Hand − Reserved**. In this project orders already deduct holds from saved stock, so the snapshot reconstructs **On Hand = saved Available + Reserved**. Subtracting Reserved from saved stock again would double-count it.

Annotated example, using isolated test data rather than production records:

```python
# An order reserved 3 Large units from a physical quantity of 4.
available = 1          # Real saved option.stock after reservation.
reserved = 3          # Real active deducted/unrestored order units.
on_hand = available + reserved  # 4; 4 - 3 remains 1 available.
threshold = 2         # Large's own saved threshold, not the parent level.
# 0 < available <= threshold -> Low Stock.
```

The reused status rule is available <= 0 → Out of Stock; positive available <= threshold → Low Stock; available > threshold → In Stock. Bundles use the existing minimum of component stock divided by required quantity, with shared stock-pool demands already combined by the bundle service. No standalone bundle threshold is created.

### 5. Backend / API behavior

The existing authorized GET `/admin-products/?view=inventory` renders the enriched rows. Existing filters and authorization still apply. No API contract, order reservation/deduction, cancellation, bundle recipe, component stock or dashboard low-stock logic changed. Query checks confirm two queries for a normal queryset (joined products/sellers plus holds), three with bundles (add one recipe/component query). A supplied list loads missing sellers in one batch rather than one query per row.

### 6. Database / migration impact

None. This update reuses `product_code`, seller, timestamps and existing JSON inventory. It adds no persisted SKU, variant stock or bundle stock field and writes no production records. Django `makemigrations --check --dry-run` returned No changes detected.

### 7. Tests performed and manual verification

Actual results for this follow-up:

- **59 targeted Django tests passed:** variant inventory, component bundles, thresholds and dashboard low-stock tests. Tests use the isolated Django test database.
- After the final table-specific CSS class rename, the two real page/constant-query cases passed again and re-exported their HTML.
- Django system check passed with zero issues; migration check reported no model changes.
- Chrome checked real exported variant/bundle pages at desktop 1440px (1424px usable after scrollbar space) and a genuine **375px CSS viewport**. Both pages fit; eleven columns, numeric right alignment, left/start SKU alignment, focusable horizontal scrolling and actual navy/gold/muted-red styling were checked. The 375px document width was 360px after its vertical scrollbar.
- Inspected screenshots: `scratch/inventory-columns/inventory-1440.png`, `inventory-375.png`, `bundle-inventory-1440.png`, `bundle-inventory-375.png`. Fixtures are not production rows. The entire application suite and Flutter/device behavior were not rerun for this table update.
- The read-only Chrome QA helper passed Node syntax checking; scoped `git diff --check` passed for the modified tracked application files.

Run from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_variant_inventory modules.marketplace.test_bundles modules.marketplace.test_thresholds modules.reports.test_dashboard_low_stock --keepdb --noinput
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Manual steps on an isolated test installation:

1. Open Marketplace → Inventory. Confirm all eleven headings and On Hand. Scroll horizontally when space is limited to reach Actions.
2. Check an ordinary product with physical 10 and an active deducted reservation of 3: On Hand 10, Reserved 3, Available 7. Healthy stock has simple In Stock text and no green badge.
3. Check tracked Small/Medium/Large separately. Each uses its own threshold; a quantity equal to its threshold is Low Stock, and zero is muted-red Out of Stock.
4. Check a real bundle: Bundle, physical-stock dashes, derived count and Available when positive. Place/cancel an isolated bundle order and verify the exact components change/restock using the existing workflow.
5. Search a variant; try Low Stock and Out of Stock filters; select a nonexistent search to confirm the eleven-column empty row; Reset and pagination should still work.
6. Click View and the Product link. Both open existing Details; inspect actual seller/date/SKU values. Open the page on a narrow viewport and scroll/focus the table with keyboard/touch.

### 8. Remaining limitations, debugging and safe practice

Display SKUs reuse existing codes but are not a new persisted barcode registry. Renaming a group/variant changes its suffix; changing a saved product code changes the prefix. Existing held-name protections still apply. Each variant shares its product's update timestamp; a derived bundle's timestamp is its product update, not the newest component-stock event. The eleven-column table intentionally scrolls within its card when it cannot fit. The current catalog is still expanded before row pagination. Earlier unrelated test failures recorded below were not part of this targeted run.

Confirmed debugging findings in this follow-up:

- Reusing the generic `.inventory-number` class would conflict with an existing Products List rule that sets `display: block` and centers it with `!important`. The table uses **`.inventory-ledger-number`** so cells remain table cells and align right, without changing Products List styling.
- An initial check caught removal of the existing Derived from components helper. It was restored, and the targeted suite passed. Read failure names before changing stock logic.
- A browser returns `text-align: start` for ordinary text cells; that is left in this English page. The layout check accepts left/start rather than treating it as a data problem.
- If the table looks old, hard-refresh (`Ctrl+F5`), confirm the URL includes `view=inventory` and that CSS uses version `20261007-inventory-columns`.
- If On Hand/Reserved says Unavailable, compare existing held selections with actual current option names. Investigate corrupted historical associations; do not manufacture zeros or subtract reservations again.

Safe exercise: on a temporary local branch, change only `.inventory-ledger-table th, .inventory-ledger-table td` vertical padding from `10px` to `8px`. Hard-refresh and compare readability while checking that quantities, thresholds and filters remain identical. Tab to the scroll region and confirm every column is still reachable at 375px. Restore `10px` afterward. This teaches presentation changes separately from inventory calculations; do not change real stock to practice CSS.

Bundle follow-up (2026-10-07): real component bundles are now implemented. Exact selected variants reuse this service's inventory and holds; purchased recipes are saved on one bundle order. See [component-bundles.md](component-bundles.md) for the new schema, functions, current lines, formulas, verification and practice. This supersedes the original unsupported-bundle limitation below.

## 1. Cause / Reason

Confirmed by inspection: there is no separate ProductVariant or Inventory model. Variants already live in `Product.customization_options` JSON, with `stock`, `extra_price` and `low_stock_threshold`. Order placement already deducts the chosen option's stock, so saved stock represents **Available**. Subtracting reservations again would count a hold twice.

The missing pieces were separate per-option Reserved/On Hand quantities, an Inventory row view, and an exact-variant Save Stock action. Some UI calculations used the default instead of the option threshold. A sold-out option could block healthy siblings, and the single-option fallback could select a different option for an explicitly unknown name. These are inspected causes, not guesses.

## 2. Exact Files Changed / Current Lines / Nearby Anchors

Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Lines are starting points; search the anchor after later edits. The working tree also contains earlier unrelated changes.

| File / folder | Approximate current line / anchor | What changed and why |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/inventory.py` | 55 `validate_stock_quantity`; 108 `flatten_customization_inventory` | Validate whole nonnegative input; include only genuinely tracked options and their own level/image/position. |
| Same inventory service | 189 `get_availability_from_options`; 317 `get_variant_stock_summary` | Keep stocked sibling options purchasable; return actual variant/low/out counts without a parent threshold override. |
| Same inventory service | 351 `_selected_stock_options`; 377 `active_inventory_reservations`; 388 `validate_inventory_option_changes` | Share exact selection matching and actual hold queries; block changing held names/inventory type. Unknown names never select another option. |
| Same inventory service | 409 `get_product_inventory_snapshot`; 465 `build_inventory_table`; 492 `adjust_product_stock` | Reconstruct individual On Hand/Reserved; expand rows with one batch hold query; reserve/restore selected options and synchronize the aggregate. |
| `backend/core/modules/marketplace/services/customization.py` | 33 `normalize_customization_options`; `group.get("selection", "single")` in order validation | Validate stock and unique group/option names, preserve option levels/images and accept the existing legacy selection-mode default. |
| `backend/core/api/views.py` | 199 `serialize_product`; 239 `get_variant_stock_summary` | Return additive low/out counts and enrich the existing `inventory.variant_thresholds` response. |
| Same API file | 768 `admin_save_product`; 836 held-option validation; 957 option image persistence | Save existing JSON/image fields, preserve omitted saved levels/images and derive parent stock. Lock existing products for the save transaction. |
| Same API file | 999 `admin_update_product_stock`; 1779 `marketplace_orders` | Require an exact variant key for multiple tracked options; validate legacy tracked selections and deduct through the existing locked order workflow. |
| `backend/core/accounts/views.py` | 172 `admin_products_page`; 176 inventory branch; 211 `variant_summary` | Add Inventory through the existing route with authorized scope, filters and row pagination. Supply per-variant list warnings. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 14 Inventory body class; 25 filters; 39 `inventory-table-scroll` | New compact seven-column ledger, real quantities, empty/unavailable states and focusable internal scrolling. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 176 `.col-inventory`; 490 `productPriceLabel`; 527 helper; 594 option fields | Show quantity/variant count/low-variant count on separate lines; show individual full price, available stock, threshold, image and status preview. Disable duplicate parent stock/threshold fields. |
| Same Products template | 780 `pdInventoryHeading`; 784 `pdInventorySummary`; 806 `pdVariantThresholds`; 988 `updateStockVariantWrap` | Replace the parent inventory grid for tracked variants with real individual rows; add a selector to the existing Save Stock modal. Refresh asset versions. |
| `backend/static/components/js/admin_products.js` | 345 `flattenCustomizationInventory`; 522 `renderInventorySummary` | Mirror actual tracked totals and each option's own warning level after saves. Ignore untracked legacy choices instead of inventing zero inventory. |
| Same JavaScript file | 989 `applyImagesToVariantOptions`; 1001 `createCustomizationGroupElement`; 1068 `toggleStockExpiryFields`; 1097 `validateThresholdForm`; 1162 `readCustomizationFromForm` | Load/validate individual values, convert full price into existing additional price and retain explicit sparse image associations. |
| Same JavaScript file | 3069 `buildVariantRows`; 3165 `getVariantItemForIndex`; 3329 `populateInventoryKpis`; 3734 `openUpdateStockFromDetails`; `/stock/` POST | Use own thresholds, match associated photos, show actual hold rows and submit one selected stock key. Keep existing gallery layout/actions. |
| `backend/static/components/css/admin_products.css` | 1253 option inputs; 1272 price field; 1284 variant summary; 1285 Inventory styles | Fit fields, stack compact summaries, style the flat ledger and scope narrow header wrapping to Inventory. New Inventory warnings use the brand palette. |
| `backend/static/components/css/admin_product_details.css` | 1731 `.pd-variant-thresholds` | Flat table: right-aligned quantities, left-aligned names/status, internal scrolling on narrow screens. |
| `backend/templates/partials/admin_sidebar.html` | 38 Inventory link; Marketplace expanded conditions | Open `/admin-products/?view=inventory` and highlight the existing Inventory menu. No new URL pattern. |
| `backend/core/modules/reports/dashboard_low_stock.py` | 15 `build_low_stock_card`; 18 View All; 30 image / 31 link | Keep real individual low-variant names/images; open Inventory with low-stock/product filters. |
| `backend/core/modules/reports/dashboard_attention.py` | 56 low/out action definitions | Reuse counts; point stock actions to Inventory and the relevant status filter. |
| `backend/core/modules/marketplace/test_variant_inventory.py` | 22 `ProductVariantInventoryTests` | Twelve isolated tests for real orders, holds, exact stock edits, cancellation, validation, images, legacy records, UI and dashboard data. |
| `backend/core/modules/marketplace/tests.py` | 349 variant snapshot test | Restore the valid fixture name before testing the disabled legacy flag; turning off the flag must not bypass hold identity checks. |
| `backend/core/modules/reports/test_dashboard_low_stock.py` | 62 low variant test; 106 links; 142 markup | Expect valid sibling availability and new Inventory-view links while retaining existing shortlist/permission coverage. |
| `scratch/variant-inventory/check-variants.cjs`, `run-tests.py` | template/JS assertions; `narrowScreenshot`; regression runner | QA helpers, rendered HTML/PNG and test log artifacts, separate from application code/live records. |
| `CAMPUSHUB_CONTEXT.md`; `docs/product-low-stock-threshold.md`; `docs/product-details-status-inventory.md`; `docs/products-list-inventory.md`; this guide | latest follow-up notes | Explain current behavior and link older steps to current formulas, locations, debugging and practice. |

## 3. Changes Made

Each tracked option uses its own existing JSON stock, threshold, image and additional price. The form shows **full Price**: base ₱250 plus `extra_price` ₱20 displays ₱270. Saving converts that back to ₱20. Set Base Price to the lowest variant price so all additional amounts remain nonnegative. Changing Base Price preserves the existing additional amounts; review all full prices before saving.

The normal Products List shows, for example, `16 pcs`, `3 variants`, `1 variant Low Stock`. Summing quantity does not replace checking each option's threshold. Healthy products stay visually quiet. A zero-stock option is not included in the positive low-stock count; it has its own Out of Stock row in Inventory/Details.

Inventory now uses the existing Products URL with `view=inventory`. It shows Product, Variant, On Hand, Reserved, Available, Threshold and Status. Search/product/status filtering occurs before 30-row pagination. Product links still open existing Details. Details hides the parent grid only for tracked variants. Simple products retain product-level stock/threshold behavior.

## 4. How It Works — Fields, Functions and Data Flow

| Concept | Existing source |
| --- | --- |
| Simple quantity / threshold | `Product.stock` / `Product.low_stock_threshold` |
| Variant quantity / threshold | `Product.customization_options[group].options[option].stock` / `.low_stock_threshold` |
| Variant full price / image | `Product.price + option.extra_price` / `option.image` |
| Reserved quantity | Actual `MarketplaceOrder.quantity`, selected option JSON, active status and deducted/restored flags |

Missing old levels use `CAMPUSHUB_LOW_STOCK_THRESHOLD`; explicit zero remains zero. A parent threshold never overrides a tracked option. Choices without a `stock` key do not become fabricated zero-stock variants. Enter real quantities when converting old untracked choices into tracked inventory.

Requested formula: **Available = On Hand - Reserved**. The existing workflow already deducts reservations from stored stock, so the snapshot reconstructs the equivalent **On Hand = saved Available + actual Reserved**, without a second deduction. Stock inputs on existing variants edit Available; reservations remain recorded separately.

Annotated test example:

```python
# Large starts at 4. A real order reserves 3 from Large only.
available = 1   # Saved option.stock after the order deduction.
reserved = 3   # Actual active deducted/unrestored order units for Large.
on_hand = available + reserved  # 4; Available is still 4 - 3 = 1.
threshold = 2
# 0 < 1 <= 2 => Low Stock. Small/Medium remain at 10/5.
```

`get_variant_stock_summary(product)` takes a product and returns tracked variant/low/out counts. It does not query orders or substitute parent thresholds.

`active_inventory_reservations(product=None, product_ids=None)` returns matching order dictionaries. It uses actual **Pending**, **Processing**, **Ready for Pickup** statuses, `inventory_deducted=True`, `inventory_restored=False`. Completed, Cancelled, restored or undeducted rows are excluded. Facility booking statuses are unrelated to marketplace holds.

`get_product_inventory_snapshot(product, reservation_rows=None)` returns aggregate totals and enriched `variant_thresholds` rows, or `None` if old held selections cannot be matched truthfully. Supplied empty hold rows mean no holds, not another query. Each row has `available`, `reserved`, `on_hand`, `threshold`, `status`, `price`, `image_url` and positional `variant_key`.

`build_inventory_table(products)` takes an already authorized queryset/list and returns flattened display rows. One batch reservation query feeds all snapshots, avoiding one hold query per product. Unmatched old holds show Unavailable for On Hand/Reserved while retaining known available quantities; they never become fake healthy zeros.

`adjust_product_stock(product, selections, quantity, restore=False)` changes only selected `(group name, option name)` quantities and synchronizes the parent sum. A genuinely single-option legacy request can omit selections; an explicitly unknown selection never falls back to another variant.

`validate_inventory_option_changes(product, new_options)` blocks removing/renaming held options or switching inventory type during active holds. Complete or cancel the actual orders first. Cancellation needs the names stored in order JSON; no new variant foreign key was invented.

Data flow:

1. Form reads option JSON and displays full price, Available, level and associated image.
2. Existing save API validates values, preserves omitted saved levels/images for old clients, checks held names and saves under a product row lock.
3. Order placement validates selections/price, locks the product, calls the shared adjustment helper and records the deducted flag.
4. Inventory/Details read the same saved quantities and real holds. Products/dashboard reuse individual threshold resolution.
5. Save Stock sends an exact positional key and receives a fresh product/snapshot. List metadata and Details refresh without altering sibling quantities or levels.

## 5. Backend / API Behavior

| Existing route | Behavior |
| --- | --- |
| `/api/products/admin/save/` | Save existing fields/JSON without duplicate parent stock. Invalid quantities/thresholds, duplicate names or held-name removal return HTTP 400 and clear errors. |
| `/api/products/admin/<id>/stock/` | POST `{ "stock": 7, "variant_key": "0:2" }` changes that option's Available. If Reserved = 3, On Hand becomes 10. Multiple tracked options require a valid key. Simple/single-option legacy updates remain supported. |
| Marketplace products endpoint with `product_id` | Return the enriched existing `inventory.variant_thresholds`; no parallel inventory API. |
| Existing order placement/cancellation | Exact option deduction/restoration and existing flags preventing restoration twice. Insufficient selected stock still rejects orders. |
| `/admin-products/` | Preserve Products List search, approvals, filters, pagination and actions. |
| `/admin-products/?view=inventory` | Real variant ledger, existing module permissions/product scope; `product_id`, `search`, `inventory_status` filters. |

New variants require whole quantities and thresholds >= 0. A newly supplied threshold must be below initial stock, except safe stock 0 / threshold 0. Existing variants that have become low stock remain editable. Error: “Low Stock Threshold must be lower than the initial stock quantity.”

## 6. Database / Migration Impact

**No new migration for this update.** Existing JSON/product/order fields are reused; no ProductVariant, on-hand, reservation-total or bundle-stock column was added. Migration `0031_product_low_stock_threshold` belongs to the preceding simple-threshold task and remains applied. `makemigrations --check --dry-run` reported **No changes detected**. Verification used the isolated Django test database and temporary media; no sample production stock or orders were inserted.

## 7. Tests Performed / Manual Test Steps

Actual results:

- Broader Django regression: **73 tests, 72 passed, 1 failed**. All twelve new variant tests passed. Coverage includes exact order price/deduction, separate holds, cancellation once, exact stock selection, held rename/removal protection, validation, legacy flags/choices, stocked siblings, simple products, dashboard links, one batch hold query, permissions and image persistence.
- The remaining failure is the previously recorded `MarketplaceAdminProductAccessTests.test_listing_owner_shows_only_approved_sellers`, which expects the old literal `label="Approved Sellers"`. That markup is absent in the current template; owner selection/filter code was not changed for this task. Do not describe the whole suite as passing. Output: `scratch/variant-inventory/django-regression.log`.
- JSDOM exercised actual frontend JS/Django-generated HTML: option prices/levels, low-stock edits, save payloads, separate Details rows, exact Save Stock key and sparse image association only with Large.
- Chrome checked form/Details snippets and full Inventory at desktop 1440px, 500px and a genuine **375px CSS viewport**. Inputs fit, quantities/status align, the seven-column ledger scrolls internally with keyboard focus, and pages do not overflow. Narrow header overflow found during review was fixed only for Inventory. Desktop usable viewport was 1424px after scrollbar space.
- JavaScript syntax, Python compilation and scoped `git diff --check` passed. Django system checks reported no issues. No live Pylance/Flutter device test was run for this update.

Reproduce the broader run from the project root:

```powershell
.\backend\core\venv\Scripts\python.exe scratch/variant-inventory/run-tests.py
```

Run only the twelve new tests from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_variant_inventory --keepdb --noinput
```

Manual verification on an isolated test installation:

1. Add a Single Product with Size options Small 10/threshold 3, Medium 5/threshold 2, Large 4/threshold 2. Use base ₱250 and full prices ₱250/₱250/₱270. Parent stock/threshold should be disabled. Upload only a Large photo; save/reopen and check its association.
2. Order three Large units. Inventory should show Available 10/5/1, Reserved 0/0/3, On Hand 10/5/4, thresholds 3/2/2. Products: 16 pcs, 3 variants, 1 variant Low Stock. Dashboard should name Large.
3. In Details choose Large in Save Stock and enter Available 7. Small/Medium stay 10/5; Large becomes Reserved 3, On Hand 10, threshold 2. Try removing/renaming held Large and verify a clear rejection without losing the order association.
4. Cancel that test order; only Large receives three units back, once. Complete another test order and verify its units stop appearing in Reserved.
5. Check a simple product: parent fields and small threshold line remain, Details keeps its parent grid. Invalid negative/fractional quantities or invalid new levels should fail without writes.
6. Check Inventory's status/product/search filters and Reset; use keyboard/touch to scroll its table on a narrow screen.

## 8. Remaining Limitations / Debugging / Safe Practice

**Bundles (updated):** `BundleComponent` now references actual component products and exact JSON selections. Availability, checkout deductions, holds and cancellation use those components. No standalone bundle stock/threshold is used. “Combo Meals” remains a category; only an explicit Bundle type plus recipe defines a component bundle. See [component-bundles.md](component-bundles.md).

**Existing identities and pricing:** group/option names identify order selections, not immutable IDs. New edits protect active holds, but already corrupted old holds need investigation against actual orders. Full prices retain base + nonnegative additional price; no independent variant-price column or cross-group combination model was created. Required multiple groups retain their existing selected-option deductions and summed-option stock interpretation. The ledger batches queries but expands the filtered catalog before row pagination; a much larger catalog may eventually need database-side JSON expansion.

| Symptom | Debugging check / safe next step |
| --- | --- |
| Available appears too small | Inspect saved stock and actual deducted/restored flags. Never subtract the same hold twice. |
| Healthy Medium appears low | Check Medium's own level, including zero, in saved JSON and refreshed API data rather than using the parent/default level. |
| Save Stock changes the wrong total | Inspect POST `variant_key`; multiple tracked options require a valid exact key. |
| Cannot rename a variant | Check active reserved orders. Their stored selections need the original name for restoration; do not delete orders or bypass the guard. |
| Photo assigned to the wrong option | Check explicit `option.image`; a shorter gallery must not shift sparse photos by option index. |
| On Hand/Reserved unavailable | Compare held order selections with current names. Investigate earlier renames/removals before reconciling records. |
| Fields/menu look old | Hard-refresh assets, version `20261007-variant-inventory`; check Inventory URL includes `view=inventory`. |
| Tests fail | Read the named failure/log; distinguish the documented owner-label regression from stock/reservation failures. |

Safe practice: in the isolated `ProductVariantInventoryTests.setUp` fixture, change only Large threshold 2 to 1 and run `test_order_deducts_reserves_and_prices_only_selected_variant`. Adjust that test's expected threshold to 1. Available 1 still equals threshold 1, so it remains Low Stock. Temporarily expect In Stock and confirm a failure, then restore the assertion and rerun. Restore the fixture afterward so other tests retain their documented scenario. Do not use production rows for this exercise.

Why this approach: a boundary test teaches `<=` and the distinction between saved Available and reconstructed On Hand through the real order workflow. Invented helper examples would not verify deduction flags, actual reservations or cancellation behavior.
