# Requested product record cleanup

## Ten screenshot products archived - November 4, 2026

### 1. Cause / reason

User requested removing the ten products visible in the supplied Products-table screenshot. Read-only inspection matched all ten by exact name, owner, price and stock. Their displayed codes are fallback UI labels; stored `product_code` values are null. Permanent deletion would affect existing history: Hot Coffee has one order and Fyfyfu has two. The existing Products workflow disables permanent deletion and supports Archive/Restore, so this request was completed by archiving exactly those ten listings.

### 2. Exact files and records changed

No application source, model, migration, route or permission changed. Updated this guide and `CAMPUSHUB_CONTEXT.md`. One-off evidence/scripts are under `scratch/product-cleanup-20261104/`: `read_products.py` (read-only identity/dependency inspection), `archive_requested.py` (`transaction.atomic`, exact identity assertions and existing `Product.archive()` calls), and `verify_archive.py` (independent read-only verification).

| Product ID | Exact saved name | Result |
| --- | --- | --- |
|49|Hhahhh|Archived|
|50|Ggg|Archived|
|51|G hchc|Archived|
|52|Hhhh|Archived|
|53|Fyfyfu|Archived; two orders preserved|
|54|Hot Coffee|Archived; one order preserved|
|55|Dgxxg|Archived|
|56|Hugg|Archived|
|57|jkbjbnkj|Archived|
|58|hbgkghjb|Archived|

### 3. Changes made

All ten products now have `is_archived=True` and updated timestamps. They are absent from the default Active Products list and remain accessible through Archived. Their names, prices, stock, approval states and ownership were retained. The newer product ID59, Cjcjjc, and all other product rows were left unchanged. Eight active products remain; twenty product records remain in the database, including previously archived records.

Ten normal `PRODUCT_ARCHIVED` audit events were appended using the existing marketplace logging helper. Metadata identifies a user-requested local maintenance operation; no signed-in administrator was impersonated. Existing audit rows were preserved. No stock was removed, order cancelled, recommendation generated or file deleted.

### 4. How it works / inputs, outputs and data flow

Input was the exact ten saved identities from the screenshot, resolved to IDs49–58. The write script locked those product rows, rechecked name/owner/price/stock/approval/archive state against inspection, and called the existing `Product.archive()` method. That method saves only `is_archived` and `updated_at`; stock synchronization is not invoked for this field-limited save. Existing `log_marketplace_event` records each actual archive against the owner with explicit local-maintenance provenance.

All changes occurred in one PostgreSQL transaction. Before commit, assertions required unchanged unrelated products, unchanged prior audit rows, exactly ten new archive events and unchanged fingerprints for fifteen account/order/inventory/bundle/interaction/push tables. Unexpected changes would roll back the transaction. A second read-only process then invoked the real `catalog_selection(Product.objects.all(), {})`: its default `listing_status=active` returned none of the ten targets. Selecting Archived returned all ten.

Annotated read-only example:

```python
# Confirm archive state without modifying stock, orders or products.
Product.objects.filter(pk__in=range(49, 59), is_archived=True).count()  # 10
```

### 5. Backend / API behavior

No backend code changed. Existing active-catalog filtering now excludes these archived listings. Original permissions, Archive/Restore behavior and historical-order access remain. Archive is database state, not permanent deletion; historical and archived views can still show the records.

### 6. Database / migration impact

The configured working PostgreSQL database was updated: ten product archive flags/timestamps and ten appended audit rows. No schema/migration changes. All three existing orders, account rows and recorded inventory/bundle dependencies were preserved. Fifteen protected table fingerprints matched before/after and in the independent post-commit verification. Product count remains20.

### 7. Verification performed

The operation committed successfully. Independent read-only verification confirmed ten archived matches, zero targets in default Active Products, Cjcjjc still active, ten matching audit events, eight active products and twenty total product rows. Protected fingerprints still match. Evidence: `inspection.json`, `archive-result.json`, `verification.json` in the same scratch folder. No automated application tests were run because application code was unchanged; this was a verified working-data operation.

### 8. Remaining limitations / troubleshooting / safe practice

This was archive removal, not irreversible erasure. Refresh Products with Listing Status set to Active; Archived or an unfiltered All view intentionally retains these records. Existing in-memory mobile catalogs may need refresh. No uploaded image files or history were purged. To inspect safely, filter Archived and search an exact listed name; use the read-only count above for database verification. Restore through the existing authorized UI only if the user later requests it. Do not rerun the archive script as a general cleanup tool: it is fixed to these identities and rejects changed/already-archived targets.

## Chenchen deletion — October 18, 2026

### 1. Cause / reason

The user explicitly requested removal of Chenchen from Products and the database. This was a targeted data cleanup, not a UI bug or a request to remove the seller account.

### 2. Exact files changed

- `docs/product-record-cleanup.md:3`, anchor `Chenchen deletion`: records the operation, data flow and verification.
- `CAMPUSHUB_CONTEXT.md`, latest product-cleanup note: preserves the result for future development.
- No application source files changed. Existing models inspected: `backend/core/api/models.py:72` (`Product`), `:838` (`MarketplaceOrder.product`), `:941` (`InventorySKU`), `:963` (`InventoryStockMovement`). Line numbers are approximate; search the class/field anchor after later changes.

### 3. Changes made

One exact product matched: Product ID47, name `Chenchen`, a single product with mobile seller reference17. The seller account was preserved. The committed Django deletion removed only:

| Model | Rows removed |
| --- | ---: |
| Product | 1 |
| InventorySKU | 1 |
| InventoryStockMovement | 1 |
| ProductInteraction | 5 |
| Total | 8 |

There were no linked product orders, bundle-component dependencies or saved suggestion choices. The inventory movement was not linked to an order. Eight other Product records remained immediately afterward.

### 4. How it works / data flow

An initial read-only name lookup identified the record. Django's `Collector.collect([product])` inspected related rows and deletion policies without deleting anything. A one-off `transaction.atomic()` operation then locked the exact product and its SKU, rechecked the product identity and dependencies, and required the deletion plan to match the inspected counts. `product.delete()` used the existing Django cascade rules. Post-delete assertions ran inside the transaction; any unexpected dependency or count change would have rolled the transaction back.

Inputs were the exact saved product ID/name/owner reference and inspected related counts. Outputs were Django's per-model deletion counts and absence checks. The script ran through the configured Django environment, without exposing database credentials or changing account, order or inventory business logic. It is not installed as a reusable bulk-delete endpoint or automatic cleanup command.

### 5. Backend / API behavior

Existing product queries no longer return ID47. No routes, serializers, approval rules, seller access, stock calculations or API authentication changed. Orders and both mobile/web account counts were unchanged; existing audit history was not part of the deletion plan. A device holding an older in-memory catalog needs a normal refresh/reopen of Products.

### 6. Database / migration impact

The configured development database was changed by the explicit record deletion. No schema change, migration, seed, account deletion, filesystem image deletion or application rebuild was needed. This was permanent deletion, not archive-only hiding.

### 7. Verification performed

The transaction committed successfully and returned the eight expected deleted rows. Assertions confirmed no Product with ID47 or case-insensitive exact name Chenchen remained, all other counted model totals matched the planned changes, and orders/accounts were preserved. An independent post-commit read also checked the matching-product count. No automated application tests were run because application code and behavior were not modified.

Manual verification: refresh the web Products list and mobile Marketplace/My Products; search for Chenchen and confirm no matching product appears. Existing seller identity and unrelated listings should remain. If an old card remains visible, refresh the current catalog rather than clearing account/session data.

### 8. Remaining limitations and safe learning exercise

Previously loaded client cards or external screenshots are not live database rows; no device data was cleared. Uploaded files and historical audit text were not separately purged. The application has no undo button for this permanent deletion.

Safe exercise: in `backend/core`, use the existing Django shell for the read-only expression `Product.objects.filter(name__iexact="Chenchen").count()` after importing Product from `api.models`; the expected result is0. Compare with `Product.objects.count()` to see the remaining catalog size, which may change as users add other records. Do not practice `.delete()` on unrelated live products.
