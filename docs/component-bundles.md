# Component bundles: implementation, debugging and practice

Current October25,2026: [FIFO guide](fifo-inventory.md) documents the new, separately gated stock ledger. Existing `reserve_bundle` and `restore_bundle` still use the purchased component selections/quantities; the central save hook now allocates/releases those exact SKU batches when FIFO is activated. Bundle availability and price formulas are unchanged. No working-database cutover occurred. The linked report covers functions/inputs/outputs, exact lines, backup/reconciliation, PostgreSQL race tests and limits. Safe exercise: run the isolated shared-component FIFO bundle test and verify summed demand against the original batch, then cancel once and check full restoration.

## Current Program/Major and catalog batching follow-up ? 2026-10-08

See [variant-inventory.md](variant-inventory.md) for the current complete report. The bundle stock formula, exact selected component variants, purchased recipe snapshots and one sellable order/analytics identity are retained. Earlier catalog query-count notes below are superseded: catalog serialization now uses three batched reads including real SKU metadata; bundle inventory uses four including active holds.

Functions/data flow: `bundles.py:109` (`prime_bundle_inventory`) takes Product querysets/lists and returns products with academic labels, stable SKU identities and recipes batch-loaded. `api/views.py:792` (`admin_save_product`) takes the existing bundle form payload, validates a real matching owner/Program/Major and retains the existing recipe validation/availability/deduction workflow. Its saved response is merged into the row at `admin_products.js:2297`; the form check now verifies the saved row's actual SKU and Program/Major.

Why/debugging: adding those labels initially caused one metadata query per row; joining/prefetching them avoids N+1 queries. No duplicate bundle stock or threshold was added, and a bundle's own movement list can be empty because components own its stock. The current migration preserved stock, orders, SKU and movement fingerprints. The 209-test regression, final overlapping follow-ups and existing single/bundle picker/save/edit/retry/browser checks passed; legacy-history limits are in the linked guide.

Safe practice: run `modules.marketplace.test_bundles.BundleProductTests.test_batch_inventory_and_catalog_have_constant_queries` against the isolated test database. Increase its number of fixture bundles by one, predict that the query count remains three/four, and verify it before undoing the practice edit. Extra rows should not add one database read each. Component quantities and historical purchased selections must remain unchanged.

---

Updated 2026-10-08. This guide supersedes the older “bundles unsupported” notes in the product and variant guides. The main bundle implementation below describes the 2026-10-07 form/workflow; its test totals and Inventory query counts are historical.

Current Inventory follow-up: [variant-inventory.md](variant-inventory.md#inventory-monitoring-update--2026-10-08) contains the complete eight-part report, files/lines/anchors, filters, formulas, migration and learning/debugging guide. Bundles now have an independent `BND` SKU identity through `api/models.py:865` (`InventorySKU`), while quantities still derive from components. `bundles.py:166` (`reserve_bundle`) returns the existing purchased component snapshot and collects the actual component movement IDs; `inventory_records.py:58` (`attach_reservation_movements`) receives the saved bundle/order and links those events to that single order. `bundles.py:190` (`restore_bundle`) uses the purchased snapshot and actual actor for cancellation releases. No standalone bundle stock, threshold or duplicate component deductions were introduced. Existing Inventory reads now use four batched queries including SKUs; catalog query behavior remains unchanged.

Debugging: a bundle's own empty movement list is expected, because component pools hold the stock. Follow its component Inventory links instead of inventing parent restocks. Applied migration 0033 adds metadata/audit tables only; quantities/orders were verified unchanged. The current targeted run passed 92 Django tests, nine Inventory viewport/state checks and the existing single/bundle form browser checks. Old unrecorded component restocks cannot be reconstructed; see the linked guide for other limits.

Safe practice in isolated test data: open a bundle's View Details, note its component SKU, then place/cancel one bundle order through the existing workflow. Verify one Reservation and one Reservation released on the exact selected component, no standalone bundle movement, and restored derived availability. Search `order_allocations` at `inventory_records.py:65` and explain how saved selections/required quantities become those component changes. Do not try this against production customer orders.

## 1. Cause / Reason

Confirmed by inspection: CampusHub had no ProductVariant, Inventory, OrderItem or bundle-component model. Variants use `Product.customization_options` JSON. `MarketplaceOrder` already represents one sellable product. The form offered a Bundle radio but both JavaScript and the save endpoint refused it. A category called Combo Meals did not define a recipe.

The implementation adds a recipe relationship while retaining those existing inventory and order structures. It does not add an independent bundle stock or threshold. The Department and Tags inputs previously did not persist their values; listing metadata is now stored on Product. The listing Department references the existing Department model, independently of the owner's account department.

## 2. Exact files / current lines / nearby anchors

Paths below are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Search the named anchor when later edits move a line. The working tree contains earlier unrelated work.

| File | Approximate line / anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/api/models.py` | 62 `Product`; 84 `product_type`; 712 `BundleComponent` | Add an explicit Single/Bundle type, listing Department and Tags, and actual component product/selection/quantity references. Reuse Product.price and existing variant JSON. |
| `backend/core/api/migrations/0032_product_component_bundles.py` | 8 `Migration` | Additive schema changes; existing products default to Single. Component quantities have a database constraint of at least one. |
| `backend/core/modules/marketplace/services/bundles.py` | 24 `component_inventory`; 64 `describe_bundle` | Calculate exact selected stock, current regular price, savings and derived availability. |
| Same bundle service | 109 `prime_bundle_inventory`; 123 `validate_recipe` | Batch-load recipes; lock and validate owner, approval, listing, quantities and selections on the server. |
| Same bundle service | 166 `reserve_bundle`; 189 `restore_bundle` | Lock actual component products and deduct/restore their precise stock. Save the purchased recipe in the existing order JSON. |
| `backend/core/modules/marketplace/services/inventory.py` | 137 `iter_product_low_stock`; 162 `low_stock_inventory_rows`; 268 `get_product_total_stock`; 315 `get_product_quantity_status` | Derive bundle quantity; leave component alerts on their own products/variants, with no bundle low-stock threshold. |
| Same inventory service | 389 `active_inventory_reservations`; 416 `validate_inventory_option_changes`; 445 `get_product_inventory_snapshot`; 508 `build_inventory_table`; 536 `adjust_product_stock` | Include component holds from purchased snapshots, protect reserved/referenced variants, expose derived inventory, and refuse normal parent stock mutations for a bundle. |
| `backend/core/api/views.py` | 200 `serialize_product`; 696 `approved_products` | Return product type, metadata, actual bundle breakdown and derived available quantity. Public listings exclude bundles with no valid available components. |
| Same API file | 775 `admin_save_product`; 1050 `admin_update_product_stock`; 1234 `seller_products_monitor` | Save real recipes atomically, refuse standalone bundle stock updates, and reuse the existing catalog endpoint for the owner-filtered selection modal. |
| Same API file | 1843 `marketplace_orders`; search `reserve_bundle` | Place one bundle order at Product.price and reserve its ingredients. No extra ingredient orders are created. |
| `backend/core/accounts/views.py` | 172 `admin_products_page`; 953 `admin_order_update`; 1092 `restore_bundle` | Batch-load bundle list data; cancellation uses the saved purchase recipe and the existing one-time restoration flag. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 149 `data-product-type`; 430 `CampusHub-owned listing`; 527 `bundleComponentsSection`; 1044 `bundleProductModal` | Persist editable row metadata, allow the actual admin owner, add flat component rows/read-only summary and reuse Bootstrap's product selection modal. |
| `backend/static/components/js/admin_bundle_products.js` | 12 `info`; 35 `totals`; 54 `paintTotals`; 71 `syncType`; 106 `fetchCatalog`; search `CampusHubBundles` | Preview API-backed stock/price calculations, selection and quantity changes; handle loading, missing data, errors and Retry. |
| `backend/static/components/js/admin_products.js` | 522 `renderInventorySummary`; 1070 `toggleStockExpiryFields`; 1719 `renderProductRow`; 2028 `getProductFromRow`; 2066 `openEditProductForm`; 2135 `bundleMode`; 2210 `bundle_components` | Connect the new controller to Add/Edit/Save; hide standalone controls; render bundles as derived bundles rather than pieces. |
| Same product JavaScript | 3277 `populateInventoryHistory`; 3353 `populateInventoryKpis` | Show component inventory and read-only bundle availability. Hide Update Stock and avoid inventing standalone stock movements. Existing recent orders retain the bundle identity. |
| `backend/static/components/css/admin_products.css` | 4859 `Bundle rows`; `.bundle-table-scroll` | Reuse the existing flat form and table styles, with navy text, compact numeric inputs, gold keyboard focus and an internally scrolling narrow table. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 47 `item.derived` | Derived bundle rows show bundles available and em dashes for inapplicable On Hand/Reserved/Threshold. Components retain their real individual rows. |
| `backend/core/modules/marketplace/services/analytics.py` | 274 `_product_inventory` | Batch-prime derived stock for the existing inventory analytics. No sales identity changes. |
| `backend/core/modules/reports/reporting.py` | 210 `_product_report` | Use derived quantities in reports; exclude bundles from separate component low-stock alerts. |
| `backend/core/modules/reports/dashboard_attention.py` | 22 `inventory_attention_counts` | Inspect actual Single/component stock. Do not interpret the unused bundle stock column as another out-of-stock alert. |
| `backend/core/modules/marketplace/test_bundles.py` | 22 `BundleProductTests` | Isolated database integration tests for recipes, orders, exact variants, shared stock, cancellation, permissions and analytics. |
| `scratch/component-bundles/` | `run-tests.py`; `check-form.cjs` | Reproducible regression log, actual Django test HTML/API exports, UI behavior checks and Chrome screenshots. These are review artifacts, not production fixtures. |

Also updated the current notes in `CAMPUSHUB_CONTEXT.md`, `docs/variant-inventory.md`, `docs/product-low-stock-threshold.md`, `docs/product-details-status-inventory.md` and `docs/products-list-inventory.md` to point to this guide.

## 3. Changes made

Single Product retains its existing price, stock, threshold, variants, description and image controls. Combo / Bundle relabels the name and price, hides/disabled standalone stock and threshold controls, hides the normal Variants section and parent expiry, and displays Bundle Components. Description and images remain available.

The component table displays the actual product and chosen variant, unit price, component subtotal, available stock and required quantity. The existing `+ Add Products` action opens a compact selector; no new page is created. Changing owner clears previous selections so components cannot silently follow another seller.

Regular Combined Price, Customer Savings and Available Bundles are text outputs, not editable stock fields. A loading or failed catalog request shows Loading/Unavailable/— with Retry instead of made-up zero prices or stock. Saving still checks the current database independently of the preview.

Products List shows `10 bundles available` and `Derived from components`. Product Details shows a component table and Derived Availability. Its Update Stock action is hidden for bundles; the stock endpoint also rejects direct bundle updates. Inventory shows a derived row alongside the normal real component rows.

## 4. How functions and data flow work

### Recipe data

Each `BundleComponent` contains:

- `bundle`: the sellable Product;
- `product`: an existing Single Product belonging to that owner;
- `selections`: existing group/option names, such as Size / Large;
- `required_quantity`: how many units of that selection one bundle consumes.

The selected ProductVariant is not a separate new table: it is identified inside the existing Product JSON. Product.price is the bundle selling price. Component unit prices are recalculated as base price plus the selected options' actual extra prices; a client cannot supply a different extra price.

### Read and preview path

`seller_products_monitor` receives `bundle_owner_id` through the existing authorized catalog route → filters real approved, non-archived Single Products with active owners and valid stock → `serialize_product` returns their prices/options → `fetchCatalog` loads them → `info` chooses exact option stock → `totals` combines required stock demands → `paintTotals` displays read-only results.

`prime_bundle_inventory(products)` accepts product objects, batch-loads their related recipes/components and returns a list with request-local derived data. It is a read optimization, not a persisted stock cache. Checkout obtains fresh locked components and does not trust an earlier catalog value.

### Save path

The existing Save action sends `product_type`, metadata and `bundle_components` to `admin_save_product` → `validate_recipe` resolves actual products and canonical variant prices/selections → the existing atomic save writes Product and its recipe. No standalone threshold or variant JSON is created for a bundle. The shared stock column remains unused at zero for bundles; every public quantity read derives actual availability.

Selections must be approved, active, from the same seller and sufficient to make at least one bundle. Pending/rejected/archived/inactive-owner/out-of-stock/expired components are refused. Nested bundles, self-components, duplicate identical product/variant rows and nonpositive/fractional required quantities are refused. Add duplicate quantities to the same row instead.

The requested formulas are:

```python
regular_price = sum(component_unit_price * required_quantity)
customer_savings = regular_price - bundle_price
available_bundles = min(component_available // required_quantity)
# // is whole-number division: 30 // 3 means 10 complete bundles.
```

For recipes sharing the same tracked option, required quantities are added for that stock pool before dividing. Example: two different flavor combinations both use Large; if Large has five units and the recipe needs two plus one Large, availability is `5 // 3 = 1`, not two. This prevents overselling the shared selection.

The 20 / 30 / 12 stock and 1 / 3 / 1 quantity example is an **isolated test fixture**. It produces `min(20, 10, 12) = 10` bundles; regular price ₱75 at actual test prices ₱30/₱10/₱15, selling price ₱65 and savings ₱10. Production calculates from the selected real records.

### Purchase and cancellation path

`marketplace_orders` locks the bundle → `reserve_bundle` locks all distinct component products in ID order → verifies every pooled demand → uses the existing `adjust_product_stock` for each exact selection → saves each component once → creates **one** MarketplaceOrder for the bundle.

For a quantity of one, ingredient deductions are 1 / 3 / 1. Component stock becomes 19 / 27 / 11 in that test fixture, and derived availability becomes nine. The order uses the bundle price; it does not bill ingredients separately.

The order's existing customization JSON stores `bundle_components`, including original product IDs, selected names, required quantities and prices. `restore_bundle(order)` accepts that order and restores `required_quantity × order.quantity` from this purchased snapshot. It does not restore a later edited recipe. `inventory_restored` prevents a second restoration.

Active holds remain Pending / Processing / Ready for Pickup with inventory deducted and not restored. Completed/Cancelled orders are not reservations. On Hand is reconstructed as saved Available plus those real holds: CampusHub already deducted held stock, so Available must not subtract it again.

Recipe/type/owner changes are blocked while relevant reservations exist. Held or referenced variant names cannot be removed or renamed. Component holds are protected even if their bundle was archived. Administrative available-stock edits retain the existing behavior.

## 5. Backend / API behavior, identity and Apriori

| Existing route | Input / output |
| --- | --- |
| `/api/marketplace/products/?bundle_owner_id=<id>` | Authorized admin catalog; returns eligible component products only. Owner/type/approval checks are repeated on save, preventing tampered cross-seller IDs. |
| `/api/products/admin/save/` | Existing POST; validates and persists recipe, prices and metadata. Missing/invalid components return HTTP 400. |
| `/api/products/approved/` | Actual available sellable products; bundle `stock` means derived available bundles for compatibility with existing consumers. No components available → bundle is excluded. |
| `/api/marketplace/products/?product_id=<id>` | Existing detail response; includes actual bundle breakdown and derived inventory when applicable. |
| `/api/products/admin/<id>/stock/` | Rejects direct bundle stock changes with HTTP 400. Update its component inventory instead. |
| `/api/orders/` | Existing checkout POST; insufficient bundle stock returns HTTP 409 and rolls back all deductions. Successful purchase returns one sellable bundle order. |
| Existing `admin_order_update` route | Cancellation restores exact component snapshots once. Unreconcilable original inventory returns HTTP 409; it does not silently change another variant. |

The existing order keeps bundle product ID, saved product name, quantity, unit price, total and recipe. Top Selling Products counts the bundle's quantity and revenue. Ingredient consumption is an inventory movement, not an organic separate product sale.

Existing Apriori `_market_basket` uses the sellable order product ID/name, and never expands customization components. Its output receives Super Meal as one item. **Existing limitation:** current orders have unique per-product order codes, not a shared checkout basket identifier. This change does not fabricate a Super Meal + Iced Tea pair by grouping unrelated orders; a future genuine checkout grouping feature is needed for those associations.

## 6. Database / migration impact

Applied **api migration 0032_product_component_bundles** to the configured database. Added Product.product_type (default Single), Product.department (nullable FK to existing Department), Product.tags (JSON list), and the `campushub_bundle_component` relation table. Existing products and quantities remain intact.

No ProductVariant, Inventory, OrderItem, bundle-stock, bundle-threshold or duplicate bundle-price column was created. Purchase snapshots reuse MarketplaceOrder.customization. No production example products, ingredients or orders were inserted by this task.

## 7. Tests performed and manual test steps

Automated verification is recorded in `scratch/component-bundles/django-regression.log`. The bundle tests exercise actual isolated PostgreSQL records and the existing Django APIs; preview fixtures are exported from this test database only. Frontend fetches in `check-form.cjs` are mocked from those exports; they are not a live production browser save test.

- Twenty-one bundle integration tests cover creation/metadata/price, component eligibility, self/nested/duplicate/quantity validation, inactive owner and expiry, exact variant deductions/holds/restore, shared stock demand, insufficient-order rollback, active edit guards (including archived bundle holds), derived lists/details/inventory, quiet bundle thresholds, route access, constant query counts, bundle-only sales and Apriori identity. The added reconciliation test verifies unavailable selection prices stay unknown and failed cancellation never restores another variant.
- Batch catalog reads use two SQL queries and the inventory ledger uses three in the tested mixed-product fixture; the query-count checks are assertions, not timing claims.
- JavaScript syntax checks and the actual form/controller behavior checks passed: mode switching, selection, Large variant price/stock, quantity math, save payload, edit persistence, read-only details, error/Retry, and returning to Single Product.
- Chrome screenshots were produced at desktop and narrow sizes. The true 375px viewport has a 360px document width because of the vertical scrollbar, with no horizontal page overflow. The component table remains internally scrollable.
- Django system checks, migration application and migration drift checks were run. See the verification results below for the final regression outcome and outstanding prior test failure.

Manual tests:

1. Hard-refresh the Products page after the asset version update. Add Product → Combo / Bundle. Verify stock, threshold, parent expiry and normal Variants are hidden; name/price become Bundle Name/Bundle Price.
2. Select the actual owner, then Add Products. Confirm only that owner's approved available Single Products appear. Search; choose the precise variant where required; enter a positive whole required quantity.
3. Add components, change a quantity and verify each subtotal, regular combined price, savings and available bundle count. Preview values must use real selected stock, not the documentation fixture numbers unless working in the isolated test environment.
4. Attempt save without ingredients, with an unavailable variant, with a duplicate selected SKU, or with quantity zero. Verify the visible validation and no invalid product creation. A tampered cross-seller payload must also fail server-side.
5. Save a valid bundle. Reload the list and reopen Edit. Verify type, components, quantities, price, selected Department, Tags and images remain attached to it.
6. Open Details and Inventory. Verify derived availability, exact component names/variants, no standalone threshold, and no direct Update Stock action for the bundle.
7. In a disposable test database, place one bundle order. Verify one bundle order row, component deductions of recipe quantity × purchased quantity, exact variants unchanged elsewhere, component Reserved quantities, and recalculated availability.
8. Cancel that test order with a reason. Verify exact restoration once; a repeated cancellation must not add stock again. Editing a reserved recipe/type/owner must be refused.
9. Complete and record payment for a test bundle through the normal Cash on Pickup workflow. Verify Top Selling Products/revenue show the bundle, without new ingredient sales rows.
10. Narrow the browser to 375px; scroll only inside the component table. Use Tab to open the selector, choose options and close the Bootstrap modal. Simulate an offline catalog request; Retry must restore real data, with no fabricated zero availability on failure.

### Debugging / confirmed causes / verification

| Symptom | Confirmed cause or next inspection | Fix / check |
| --- | --- | --- |
| Original Bundle save refusal | Confirmed JavaScript and backend guard with no recipe model | Real component model/service and form payload now replace the refusal. |
| Unexpected low-stock query increase | Confirmed `product_type` was deferred by `.only()` when the shared classifier read it | Include type in the two streamed product queries. Existing bounded-query regression now passes. |
| Narrow page extends beyond the viewport | Confirmed absolutely positioned screen-reader header text escaped the table's scrolling ancestor | Make `.bundle-table-scroll` positioned and constrain its grid column. Chrome now verifies no page overflow. |
| Available Bundles is Unavailable | Check catalog load/Retry and whether a selected ingredient is now archived/expired/out of stock or its selection is invalid | Replace/replenish the actual component and reload. Do not type a standalone bundle quantity. |
| Save says reserved orders/components prevent a change | Expected inventory protection, not a missing UI update | Complete/cancel the relevant orders first; do not rename stock selections holding reservations. |
| Cancellation reports original inventory unavailable | Exact purchased selections cannot be reconciled after out-of-band data edits | Inspect order.customization.bundle_components and component JSON. Reconcile original inventory; never restore another variant as a guess. |
| Owner-dropdown label test fails | Previously recorded before this feature: the test expects `label="Approved Sellers"`, while the current UI lacks that label | Separate existing UI/test mismatch; not represented as a successful check. Component owner validation and selector tests pass. |

Final regression: **138 tests run, 137 passed, one previously recorded owner-dropdown label failure** (`modules.marketplace.tests.MarketplaceAdminProductAccessTests.test_listing_owner_shows_only_approved_sellers`). No bundle, variant, threshold, low-stock query, order workflow, dashboard sales or report test failed. The 20 bundle tests pass within that run. `node scratch/component-bundles/check-form.cjs` passed, both JavaScript syntax checks passed, `manage.py check` reported no issues and `makemigrations --check --dry-run` reported No changes detected. Migration 0032 applied successfully. Do not treat a screenshot as proof of payment behavior or mobile device testing.

After the final recipe-lock/validation and unavailable-selection refinements, **all 43 targeted bundle, variant and threshold tests passed** (21 bundle, 12 variant, 10 threshold). The frontend checks were rerun, including unavailable price/stock output on a catalog error. The broader result above is the recorded full run, not a claim that its existing owner-label failure was fixed.

## 8. Remaining limitations and safe practice

Nested bundles are intentionally disallowed. Components must have enough valid stock to make one bundle when a recipe is saved. If an ingredient later becomes unavailable, the existing bundle honestly derives zero availability and cannot be purchased; replace/replenish components before saving that recipe again. Current regular combined prices follow current ingredient prices; purchased snapshots preserve historical prices for restoration/audit. The formula can show negative savings if bundle price exceeds regular combined price; no discount is invented.

Existing images and gallery handling are reused; no new component photo assets were fabricated. A live Flutter/device checkout, a live production browser purchase and Pylance were not run. Existing APIs still expose compatible sellable price/stock values. The existing owner-dropdown label regression and missing shared Apriori checkout identifier are separate limitations.

Practice without changing production data:

1. Read `test_create_price_metadata_and_derived_availability` and the fixtures in `test_bundles.py`. Explain why Siomai limits 20/30/12 stock at 1/3/1 quantities to ten complete bundles.
2. Copy that test under a new name **in the isolated test suite**, change Siomai's required quantity from 3 to 2, and expect `min(20, 15, 12) = 12` bundles and regular price ₱65. Leave production records alone.
3. Run `venv/Scripts/python.exe manage.py test modules.marketplace.test_bundles --keepdb --noinput` from `backend/core`. If the assertion fails, print the service output inside that temporary test, compare required quantities and selected option names, then remove the temporary print.
4. Add one test purchase: stocks become 19/28/11, availability `min(19, 14, 11) = 11`; cancel and confirm it returns to 12. Explain each input/output before editing the calculation itself.

This exercise teaches division, shared service calls, saved snapshots and regression assertions while keeping real stock safe.
