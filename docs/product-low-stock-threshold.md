# Product Low Stock Threshold — form, inventory and alerts

Current bundle behavior (2026-10-07): [component-bundles.md](component-bundles.md) supersedes this guide's earlier unsupported-bundle notes. Bundles hide standalone stock/threshold fields; real ingredient products/variants retain their own levels and alerts. The linked guide explains new fields, functions, exact-stock deductions, debugging, tests and a safe practice exercise.

Latest variant follow-up (2026-10-07): [variant-inventory.md](variant-inventory.md) is the current file/line map, functions and debugging guide. Inventory now opens `/admin-products/?view=inventory` with individual rows. Tracked list summaries show aggregate quantity / variant count / low variant count; the parent threshold line remains only for simple stock. Details shows individual On Hand, Reserved, Available, Threshold and Status instead of the older parent Per variant grid. The shared snapshot reads actual holds and each option's own level; no new migration was required for that follow-up. Its inputs/outputs/data flow, actual tests, manual checks and safe boundary-test exercise explain how to work independently. Earlier locations/results below describe the threshold step, not another current test run.

Updated 2026-10-07. This is the current threshold implementation guide. It supersedes the global-only classification described in earlier Products List and Product Details updates. The user confirmed that the threshold should be a small line in the existing Inventory cell; the table still has nine columns.

## 1. Cause / Reason

Confirmed by inspecting the models and services: products had no saved individual warning level. `CAMPUSHUB_LOW_STOCK_THRESHOLD` was the only threshold. Variants are stored in `Product.customization_options` JSON, not a separate Product Variant or Inventory table. The Inventory sidebar already opens `/admin-products/`.

The change lets different products and separately tracked options have different warning levels while preserving the existing stock, reservation, permission, expiry and approval workflows. No second Inventory page or duplicate stock store was created.

## 2. Exact Files Changed / Current Lines / Nearby Anchors

Paths are relative to `C:\Users\leste\Desktop\CAMPUSHUB`. Lines are current starting points; search the anchor when later edits move them. Only the changes described here belong to this feature; the working tree contains earlier work as well.

| File / folder | Approximate line / anchor | Added, changed or removed |
| --- | --- | --- |
| `backend/core/api/models.py` | 86 `low_stock_threshold =` | Add one nullable, nonnegative product threshold field for simple inventory. |
| `backend/core/api/migrations/0031_product_low_stock_threshold.py` | 12 `operations` | Add that column to `campushub_product`; existing rows remain NULL. |
| `backend/core/modules/marketplace/services/inventory.py` | 41 `low_stock_threshold`; 51 `validate_low_stock_threshold` | Resolve saved/default levels and validate explicit inputs in one shared service. |
| Same inventory service | 97 `flatten_customization_inventory`; 125 `iter_product_low_stock`; 146 `low_stock_inventory_rows` | Attach each option's level; classify individual rows; shortlist against their own levels without related-object queries. |
| Same inventory service | 291 `get_product_quantity_status`; 352 `get_product_inventory_snapshot`; 390 `variant_thresholds` | Reuse aggregate available stock for the three UI states and expose actual per-option levels to Details. |
| `backend/core/modules/marketplace/services/customization.py` | 67 `if "low_stock_threshold" in opt` | Preserve and validate the threshold key when normalizing existing option JSON. |
| `backend/core/api/views.py` | 193 `serialize_product`; 232 threshold response; 760 `admin_save_product`; 809 `old_options`; 853 threshold fields; 947 error handler | Save product/option levels; retain omitted existing option values; enforce creation validation; return field-specific HTTP 400 errors. Reject unsupported standalone bundle creation. |
| `backend/core/accounts/views.py` | 170 `admin_products_page`; 196 `admin_quantity_status`; 197 `admin_threshold` | Supply the same quantity state and threshold to the initial table. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 179 `inventory-threshold`; 504 `productLowStockThreshold`; 581 `Stock / Threshold`; 598 option threshold; 805 `pdVariantThresholds` | Add a secondary threshold line, required form field and helper, individual option inputs and a flat Details breakdown. Refresh the existing CSS/JS asset versions. |
| `backend/static/components/js/admin_products.js` | 321 `computeInventoryStatus`; 511 `computeProductQuantityStatus`; 521 `renderInventorySummary` | Mirror backend levels for immediate UI/filter updates and preserve the compact Inventory cell after saves. |
| Same JavaScript file | 997 `createCustomizationGroupElement`; 1051 `toggleStockExpiryFields`; 1076 `validateThresholdForm`; 1123 `readCustomizationFromForm`; 2012 `openEditProductForm`; 2106 `const threshold` | Load each saved value, validate before sending, move threshold entry to options when stock is tracked there, and send it in the existing save request. |
| Same JavaScript file | 3279 `populateInventoryKpis`; 3305 `pdVariantThresholds`; 3758 row threshold metadata | Show “Per variant” with actual individual levels and keep row metadata synchronized after stock updates. |
| `backend/static/components/css/admin_products.css` | 1251 `.create-product-threshold-field`; 1253 option inputs; 1272 `.inventory-threshold`; 3865 variant grid | Place threshold directly below Stock Quantity, use small secondary text and fit both option inputs inside a 120px desktop column. Narrow layouts retain the existing stacked form. |
| `backend/static/components/css/admin_product_details.css` | 1731 `.pd-variant-thresholds` | Style the flat per-variant breakdown; align Available and Threshold numbers right. |
| `backend/core/modules/reports/dashboard_attention.py` | 23 `inventory_attention_counts` | Count simple products against saved/default levels in SQL and reuse option classification for variants. |
| `backend/core/modules/marketplace/services/analytics.py` | 274 `_product_inventory`; 304 quantity classification | Use saved levels for inventory analytics and its existing seller low-stock counts. |
| `backend/core/modules/reports/reporting.py` | 210 `_product_report`; 225 `_quantity_state`; 233 display label | Reuse the same parent quantity state in product/low-stock reports and summaries. Keep expiry as a separate date column. |
| `backend/core/modules/marketplace/test_thresholds.py` | 24 `ProductLowStockThresholdTests` | Add ten isolated tests for saving, validation, reservations, variants, defaults, UI data, dashboard ranking, analytics and reports. |
| `backend/core/modules/marketplace/tests.py` | 329 snapshot tests; 349 variant snapshot; 429 Inventory column | Update existing snapshot expectations for the new fields and the per-option warning rule. |
| `scratch/product-thresholds/check-form.cjs` | form save assertions; `snapshot`; `measure` | Test the actual frontend functions with isolated Django fixtures and render current form sections in Chrome. HTML/JSON/PNG files in this directory are QA artifacts. |
| `docs/products-list-inventory.md`, `docs/product-details-status-inventory.md`, `CAMPUSHUB_CONTEXT.md` | latest threshold note | Link the current guide and identify the earlier global-only behavior as historical. |

## 3. Changes Made

The existing Pricing & Inventory section now places **Low Stock Threshold*** directly below Stock Quantity. Its helper says: “You will be alerted when available stock reaches this amount or lower.” The default comes from the existing setting, and a saved individual value overrides it.

The Inventory cell keeps quantity as the strongest information. A second small line shows `Threshold: 3`, or `Threshold: per variant` for separately tracked options. Existing variant counts, gold Low Stock text/dot, muted red Out of Stock text/dot and `1 pc` grammar remain. Healthy stock still has no status dot or In Stock badge. Other columns, filters and actions retain their layout.

Tracked variants each have Stock and Low Stock Threshold inputs. The standalone parent inputs are hidden and disabled; no misleading parent threshold is stored. Product Details shows **Per variant**, followed by a compact flat table of each option's Available and Threshold. Simple items show their numeric threshold in the existing grid.

No separate threshold column, large card, new page, approval status or stock mutation workflow was added.

## 4. How It Works — functions, inputs, outputs and data flow

### Saving the form

1. `readCustomizationFromForm()` reads named option rows into the existing grouped JSON shape.
2. `validateThresholdForm(customizationData)` returns true only when the visible stock/threshold inputs are valid. It uses native number constraints and the initial-stock comparison. Invalid input prevents the save request and shows the relevant validation message.
3. The existing save handler sends `low_stock_threshold` for a simple product, or includes it in each tracked option. The parent value is NULL for tracked variants.
4. `admin_save_product(request)` verifies existing manage permission and product scope, normalizes inputs, validates them again, saves through Django and returns the serialized product. Browser validation improves feedback; server validation is what protects the data.
5. `serialize_product(product)` returns the effective simple threshold or NULL for variants, plus the existing option JSON and an additive `quantity_status`. The list renderer updates the cell and its filter metadata from this response.

Example of a simple product's save input:

```json
{"name": "Practice item", "category": "Clothing", "price": "250", "stock": 10, "low_stock_threshold": 3}
```

Example of an option inside the existing JSON, not a new table:

```json
{"name": "Medium", "stock": 10, "low_stock_threshold": 3, "extra_price": "0.00"}
```

`low_stock_threshold(product=None, option=None)` returns a saved numeric level if present; otherwise it returns `CAMPUSHUB_LOW_STOCK_THRESHOLD`. Passing an option resolves that option's own value or the configured default, not a parent override. Zero is a real value: use an explicit NULL check, not `value or default`, because the latter would replace zero.

`validate_low_stock_threshold(value, stock=None, initial=False)` returns an integer or raises `InventoryThresholdError`. It rejects empty values, booleans, negatives and decimals. With `initial=True`, the level must be strictly below initial stock. The safe empty-product exception is stock 0 / threshold 0. The error for stock 5 / threshold 10 is:

> Low Stock Threshold must be lower than the initial stock quantity.

Existing products/options can have remaining stock below their saved level. Edits therefore check nonnegative whole numbers without requiring a level below the remaining quantity. Otherwise a correctly low-stock item could no longer be edited. Adding a new option still uses initial-stock validation. Older clients that omit the field retain the saved/default value; the web form requires it.

### Reading inventory

The existing order workflow already deducts reservations from `Product.stock` or option `stock`. Those saved values are **Available**, not the pre-reservation On Hand amount. Reuse `get_product_total_stock()`; never subtract reserved orders a second time.

`get_product_inventory_snapshot(product)` outputs On Hand, Reserved, Available, effective threshold, quantity status and `variant_thresholds`. It reconstructs On Hand as Available + actual active deducted/unrestored holds. Thus the requested relationship remains:

```text
Available = On Hand - Reserved
10 on hand - 7 reserved = 3 available
threshold 3 -> Low Stock
```

Simple classification is:

| Available | Result |
| --- | --- |
| 0 or below | Out of Stock |
| Above 0 and at/below that item's threshold | Low Stock |
| Above threshold | In Stock / normal |

`get_product_quantity_status(product)` returns one of those three states. For tracked variants, it sums all tracked quantities and shows Low Stock if any positive option is at/below its own level. A sold-out option does not make the entire product Out of Stock while another option has stock. All options at zero means Out of Stock. An empty option is not also classified as Low Stock.

`flatten_customization_inventory()` adds each effective option level to its stock/expiry metadata. `iter_product_low_stock()` produces only positive low-stock product/option rows and retains the existing expiry exclusions. The broader `get_product_inventory_status()` still supports the existing expiry and partial-availability workflow; it is distinct from the three-state quantity display.

### Dashboard, analytics and reports

`low_stock_inventory_rows(products, limit=5)` outputs actual product/variant rows with Available and Threshold. It uses two database queries and bounded selection memory. The simple query compares saved stock with `Coalesce(saved_threshold, configured_default)`. The option query streams JSON inventory without fetching sellers or orders per product.

Rows are ranked by Available / Threshold, then available quantity and stable IDs. This matters now that thresholds differ: 8 remaining against 80 is more depleted than 1 against 1. The SQL shortlist uses the same ratio before limiting; zero denominators are protected and zero-threshold products cannot be positive low-stock rows.

`inventory_attention_counts(today)` counts a low-stock product once even if multiple options are low. Existing Attention Required routes and filters remain. The dashboard's existing Low Stock Products builder needs no duplicate implementation: it already calls the shared shortlist.

Analytics `_product_inventory()` and report `_product_report()` reuse the quantity classifier. Their existing seller performance counters and low-stock report therefore respect individual levels. Expiry dates remain separate report data. No existing seller-specific low-stock push/email delivery function was found; this change does not create one.

Why this approach: one shared Django resolver/validator owns the rules, one column stores simple levels, and existing JSON stores option levels beside the stock they describe. JavaScript mirrors the rule only for immediate rendering; it does not become the stock source of truth.

## 5. Backend / API Behavior

Existing routes are reused:

| Route | Behavior |
| --- | --- |
| `/admin-products/` (`admin_products_page`) | Products and existing Inventory sidebar destination; small threshold line in the same cell. |
| `/api/products/admin/save/` (`admin_save_product`) | POST creates/edits the saved simple/option levels. HTTP 201 on create, 200 on edit, 400 with `field: "low_stock_threshold"` for invalid explicit values. Existing manage permissions remain. |
| `/api/marketplace/products/?product_id=<id>` (`seller_products_monitor`) | Existing protected Details fetch returns that product's inventory snapshot and variant levels. |
| `/api/products/admin/<id>/stock/` | Existing stock-only update preserves levels and returns a fresh snapshot. |

Approval Status and Listing Status remain independent. Current active reservation statuses are Pending, Processing and Ready for Pickup with actual deduction flags; Completed, Cancelled, restored and undeducted orders do not inflate reserved stock. FastAPI chat and Flutter screens were not modified. Additive product fields and fallback behavior preserve older callers that omit thresholds.

## 6. Database / Migration Impact

Migration **0031_product_low_stock_threshold** has been applied to the configured database. `showmigrations api` reports `[X] 0031_product_low_stock_threshold`. It adds only `Product.low_stock_threshold` as a nullable `PositiveIntegerField`; it does not rewrite products, orders, option JSON or the configured default.

Older simple products and options without a saved level use the existing default. Newly saved tracked options store levels in the existing JSON. No duplicate variant table or threshold field was created. On another checkout/database, activate the existing virtual environment and run `python manage.py migrate` from `backend/core` before serving the changed application.

## 7. Tests Performed / How to Test

Actually run on the final implementation:

- **47 Django tests passed** in the retained isolated PostgreSQL test database: ten threshold tests, existing stock deduction/restore and inventory/pricing tests, five list/Details tests, the dashboard low-stock suite, the inventory analytics regression and Admin Report tests. Django system checks found no issues.
- `node --check backend/static/components/js/admin_products.js` and Python compilation of the changed Python modules passed.
- `manage.py makemigrations --check --dry-run` reported **No changes detected**.
- Targeted `git diff --check` passed for the changed tracked code and reference documents.
- `node scratch/product-thresholds/check-form.cjs` passed actual form functions, payload values, creation error blocking, allowed low-stock editing, variant persistence/display and unsupported bundle blocking. Fetch responses were mocked from isolated Django fixtures; this is not a production browser save test.
- Headless Chrome passed 1440px and 500px form-section previews: field below stock, nine table columns, no page overflow, individual values 3/2, and variant input widths contained in their column. Screenshots were visually inspected.

The first desktop preview exposed a confirmed CSS cause: nesting inputs in a grid cell left their intrinsic width unconstrained, overlapping Additional Price. Setting the input width to 100%, minimum width to zero and the shared header/row stock column to 120px fixed it. The browser check now verifies containment. An older variant test expected healthy parent stock even with a positive low option; that expectation was updated to the newly requested per-option rule.

Quick repeatable backend check in PowerShell, from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.marketplace.test_thresholds --keepdb --noinput
```

Manual checks in a development/test database:

1. Refresh Products; open Add Product. Enter stock 10 / threshold 3 and save an otherwise valid item. Reopen Edit and verify 3 was retained. Its Inventory cell should show 10 pcs / Threshold: 3 without a healthy badge.
2. Try stock 5 / threshold 10, an empty level, a negative level and a decimal. Saving must be blocked with a clear message; bypassing the browser and posting an invalid explicit value must return HTTP 400 without creating a record.
3. Reduce available stock to 3 through the existing test stock/order workflow. The list and Details should show Low Stock, and the dashboard Low Stock Products row should show Available 3 / Threshold 3. At 0, show Out of Stock, not a positive low-stock row.
4. Add Medium stock 10 / threshold 3 and Large stock 5 / threshold 2. Parent inputs should hide. Details should show Per variant and both levels. Lower Large to 2; the parent summary should warn while keeping the total across options.
5. Edit an already low-stock product without raising stock. Its existing threshold must remain valid. Change stock to 1 / threshold 0 and verify healthy stock; change stock to 0 / threshold 0 and verify Out of Stock safely.
6. Follow the Inventory sidebar and dashboard low-stock action. They should use the existing Products page/filter. Check a low-stock report and inventory analytics against the same real levels. Approval status, search, pagination and View/Edit/Archive should still work independently.

### Debugging / troubleshooting

| Symptom | What to check before changing code |
| --- | --- |
| Database says column does not exist | Verify `[X] 0031_product_low_stock_threshold` in the same database used by Django. This is a schema issue, not a CSS issue. |
| New field is missing or still uses old rendering | Refresh the page and inspect asset version `20261007-stock-threshold`. Confirm the canonical marketplace template is loaded. |
| Saved zero becomes the default | Inspect NULL checks in the resolver and `??` in JS. Zero must not use a truthiness fallback. |
| Variant parent says Per variant | Expected: inspect `pdVariantThresholds` and each JSON option rather than inventing a parent level. |
| A high parent total still shows Low Stock | Compare each option's available quantity with its own level. One positive low option is enough to warn. |
| Available appears too small after ordering | Verify actual stock deduction flags and the snapshot. Do not subtract active orders again from the stored available quantity. |
| A variant is renamed while an order holds it | The existing snapshot can show Unavailable when old selections no longer match. It refuses to invent reservation quantities; reconcile names/holds through the real workflow. |
| Item not in the five-row dashboard shortlist | Check archive/expiry exclusions, each effective level and relative depletion. The list is a shortlist, not every low-stock record. |
| No seller email arrives | No low-stock email/push pipeline was found. This feature updates existing UI/analytics counts only. |

### Safe learning exercise

Use the isolated test file, not production rows. In `test_create_persists_threshold_and_all_status_boundaries`, change `self.save()` to `self.save(low_stock_threshold=2)` and update that test's saved-value assertions and expected comparison from 3 to 2. Leave the shared `save()` helper unchanged so other tests retain their fixtures. Run that single test and verify available 3 becomes normal, 2/1 are low and 0 is out. Restore the test afterward.

This teaches you to trace one rule through input, persistence and output: the form sends a number, Django validates/stores it, the inventory service compares stock to it, and the frontend displays that result. If the test fails, read the first assertion difference and inspect the matching function before changing CSS or adding a second calculation.

## 8. Remaining Limitations

- Component-derived bundle inventory is **not implemented in the current models/workflow**. The existing form already blocked bundle saving; the backend now also rejects explicit bundle/combo creation rather than inventing standalone stock. A real component relationship and shared availability service are needed for that future feature.
- No new seller push/email stock alert system was added. Existing counters, filters, dashboard warnings and reports are connected.
- Existing grouped options remain the current inventory structure; this does not introduce a separate SKU/variant table or change optional-selection stock semantics.
- Browser checks used the actual markup/functions with isolated fixtures and mocked fetch. A logged-in production create/edit session and Flutter device testing were not performed for this web-form change.

Related guides: [Products List Inventory](products-list-inventory.md), [Product Details statuses/inventory](product-details-status-inventory.md).

## Follow-up: Pylance optional snapshot warnings — 2026-10-07

1. **Cause / Reason:** `get_product_inventory_snapshot(product)` can legitimately return a dictionary or `None` when reservation selections cannot be matched. The two valid-fixture tests immediately read `inventory["..."]` without first establishing that the result is a dictionary. Pylance therefore reported seven `reportOptionalSubscript` diagnostics. This was a missing test precondition, not evidence of wrong threshold calculations.
2. **Exact Files Changed:** `backend/core/modules/marketplace/test_thresholds.py`, line **87** in `test_reserved_stock_uses_saved_level_without_second_subtraction`, and line **113** in `test_variants_store_separate_levels_and_ignore_parent_level`; this guide's follow-up section records the fix.
3. **Changes Made:** Add `assert inventory is not None` immediately after both snapshot calls, with a fixture-specific failure message. Keep the existing expected quantities and thresholds. No diagnostic suppression or invented empty dictionary was added.
4. **How It Works:** The function reads a real test product and its actual reservation records, then returns a snapshot or `None`. The assertion fails the test clearly if the expected snapshot is missing. On the remaining path, Pylance knows that `inventory` cannot be `None`, so reading dictionary keys is safe. This is called **type narrowing**: a check reduces the possible types of a variable.
5. **Backend / API Behavior:** Unchanged. The shared snapshot function still returns `None` for genuinely unreconcilable selections; the application can keep its honest Unavailable state. Only tests gained explicit preconditions.
6. **Database / Migration Impact:** None. No new migrations or production records were changed by this fix. Fixtures run in the isolated test database.
7. **Tests Performed:** All **10 threshold tests passed** using `manage.py test modules.marketplace.test_thresholds --keepdb --noinput`; Django system checks found no issues. This follow-up does not claim another 47-test run or a live VS Code Pylance recheck.
8. **Remaining Limitations / Manual Verification:** Save the test file and inspect VS Code's Problems panel for this file. The seven optional-subscript warnings should clear after Pylance analyzes the guards. The editor's live diagnostics were not accessed during this fix. Assertions here are test preconditions under the normal test command; production input validation remains in the existing validator.

Annotated example from the reserved-stock test:

```python
inventory = get_product_inventory_snapshot(product)  # Dictionary or None.
assert inventory is not None, "Expected an inventory snapshot for the valid reserved-stock fixture."
# Only a dictionary reaches this point; the test can now check actual values.
self.assertEqual(inventory["available"], 3)
```

Why this approach: these fixtures expect a valid snapshot, so assert that expectation before inspecting its contents. Returning `{}` as a fallback would conceal the real failure; disabling the warning would remove a useful check. A normal `self.assertIsNotNone(...)` assertion is useful at runtime, but a native `assert ... is not None` directly supplies the narrowing condition to the type checker.

Safe practice: in a temporary unsaved editor edit, remove one guard and observe which key reads Pylance highlights. Undo the edit, save the file and rerun the ten-test command above. Verify that the warnings clear and the tests still pass. This helps distinguish static analysis (possible values) from a passing test (the values produced by a particular fixture).

