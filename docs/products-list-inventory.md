# Products List — quantity-first Inventory column

## Professional minimalist Products catalog — October 31, 2026

### 1. Cause / reason

The current brief requests the existing Web Admin Marketplace → Products page with four real-data KPIs, a two-row filter section and a compact nine-column table. This supersedes the earlier single-row filter choice. Inspection confirmed that the previous view materialized every authorized product, then JavaScript filtered/paginated those rows and recalculated totals from the DOM. That did not provide database filtering/pagination and could not safely preserve overall totals after introducing bounded pages. Add Product was initially rendered even for read-only accounts before JavaScript hid it. The existing inventory/approval/archive/ownership services were retained.

### 2. Exact files changed — current lines and anchors

| File / current line | Nearby anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/accounts/views.py:179` | `def admin_products_page(` | Paginate the authorized filtered queryset, prepare only that page, render HTML or JSON fragments with overall KPI counts; Add permission follows the existing manage capability. |
| `backend/core/modules/marketplace/services/product_catalog.py:16` | `def catalog_selection(` | New shared read-only catalog selection: actual KPI aggregation, academic/name/SKU/category/status/listing filters, low-stock eligibility and stable ordering. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:47` | `Overall totals for your authorized product scope` | Scope explanation, permission-gated Add, restored selected values, server-pagination marker, loading/error/retry state, actual matching counts, empty-state guidance and asset versions. |
| `backend/core/modules/marketplace/templates/marketplace/partials/product_rows.html:1` | `{% for product in seller_products %}` | Extracted existing nine-column rows for identical initial/AJAX rendering; real variant price range, global row numbering, package fallback icon and per-variant low-stock warning. |
| `backend/core/modules/marketplace/templates/marketplace/partials/product_pagination.html:1` | `<button` | New server-generated page controls with previous/next bounds and current-page semantics. |
| `backend/static/components/css/admin_products_refinement.css:24` | `/* Six existing filters:` | Requested two-row grid, consistent 44px fields, restrained four KPIs, readable headers/statuses, contained table scrolling and 36px desktop/44px touch actions; existing scoped Montserrat stays. |
| `backend/static/components/js/admin_products.js:2813` | `let catalogController` | Abortable sequenced server queries, explicit All listing URL, current-page retry, authoritative counts, no redundant full-catalog hydration and retained deep links. |
| `backend/core/modules/marketplace/test_product_catalog.py:15` | `class ProductCatalogTests` | Seven real PostgreSQL tests for counts/filter/pagination/availability/scope/permissions/query bounds and isolated browser fixture export. |
| `backend/core/modules/marketplace/tests.py:626` | `def test_marketplace_admin_can_archive_and_restore_product` | Update the archived-row expectation to request the Archived selection explicitly, matching the unchanged Active default. |
| `docs/web-ui-ux-guidelines.md:13` | `### Professional Minimalist SaaS application` | Record the current scoped Products interpretation and supersede the prior one-row filters without restyling unrelated modules. |

This guide and `CAMPUSHUB_CONTEXT.md` are updated in place. Supporting helpers live under `scratch/products-module-20261031/`: one-time `edit_template.py`, `edit_script.py`, `refine_script.py`; intercepted Chromium harness `check.cjs`; guarded read-only `verify_local.py`; `fixtures/`, actual screenshots, `result.json`, and `localhost-result.json`. These helpers are not runtime app components; do not rerun the one-time edit scripts.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Six desktop filters on one row | Search/Approval/Listing at 50/25/25, then Program/Major/Category at equal thirds | Implements the latest brief using the same fields, options and per-field clear buttons. |
| Every product loaded for browser pagination | Django filters and returns ten products per page | Bounds rendered rows and keeps pagination tied to the actual authorized database query. |
| KPI values recounted from loaded DOM rows | Overall counts from Django, matching-result counts beside pagination | Prevents a filtered page or ten-row page from redefining the totals. |
| KPI click could retain unrelated filters | Card navigates to the scope it counts | Total/Pending/Approved use the full authorized listing scope; Low Stock uses existing active-listing eligibility. |
| Add button existed in the initial HTML for readers | Render only for existing manage-product capability | UI and Django authorization agree without granting another role any permission. |
| Base-only price / initial-letter missing-photo placeholder | Existing server variant price display / consistent package icon | Keeps actual prices and image fallback accurate in initial and refreshed rows. |
| Low variant could be hidden by healthy combined quantity | Explicit per-variant warning alongside available quantity | A low-stock KPI result explains which listing has an affected option. |
| Fixed widths hid Actions on normal desktop | Table fits at 1440px; narrower views scroll inside the table | Keeps all nine columns and actions accessible without widening the page. |
| Legacy important rules kept action buttons at 32px | Scoped 36px desktop and 44px touch targets, measured in the browser | Fixes the real cascade conflict instead of merely declaring an ineffective size. |

The four KPI cards retain their names and existing count definitions, compact dimensions and functional icons. Colors are restrained navy/gold/white/neutrals; approval and listing remain distinct. Headers wrap rather than losing important words. Actual uploaded images, SKU identities, seller Program/Major, dates/timezone handling and View/Edit/Approve/Reject/Archive/Restore actions remain. No Clear Filters replacement, additional filters, generated images, new status or Flutter redesign.

### 4. How it works — functions, inputs/outputs and data flow

`admin_products_page(request)` first gets `admin_product_queryset(request.user)`, preserving the existing server-enforced Program/Major scope. Inventory's existing `view=inventory` branch still runs separately. For Products, `catalog_selection(queryset, request.GET)` returns three values: filtered/stably ordered queryset, overall authorized KPI dictionary and normalized filter values. `Paginator(..., 10)` selects the requested page before seller/SKU/bundle details are primed. The same `product_rows.html` partial renders initial HTML and AJAX responses; no duplicate client version of the server catalog is required.

`catalog_selection()` uses actual approval/listing fields and inherited or explicit academic ownership for both Django and mobile sellers. Product/seller text search uses Django queries; actual SKU substring search streams the existing SKU identity objects and uses their existing `code` property, not invented product-ID identifiers. `low_stock_ids()` streams only needed active single-product fields and calls the canonical `iter_product_low_stock()`. Bundle warning thresholds belong to components, so a virtual bundle is not given its own fabricated low-stock threshold. Depleted-stock deep links use the existing quantity/bundle rules.

The Total/Pending/Approved definitions remain all authorized records with the relevant approval state, including archived records where their existing state is retained. Low Stock counts active product listings with at least one eligible low-stock item; it is not the number of individual variants or all depleted stock. The scope explanation makes those definitions visible. The normal listing default remains **Active**. Explicit All is represented as `listing_status=all` so clearing that filter can survive refresh without silently reverting to Active.

`applyInlineFilters(page)` reads the same six controls and current KPI inventory shortcut, updates the existing URL, cancels a previous read, then requests JSON from the same Products view. A sequence number prevents a late response from replacing a newer selection. Search remains debounced by 300ms; pagination/KPI activation sends one request. A bounded 15-second request timeout produces retry feedback. During a request the table is marked busy/inert. On failure, previous results remain visible with an explicit error and Retry; they are not reported as successful empty data. Retry retains the requested page.

Successful responses replace escaped server-rendered rows/page controls and update KPI values from server counts. Old image-cycle timers/listeners are stopped before replacing rows; existing authorized images/gallery behavior is reinitialized. There is no initial full-catalog image hydration request for the server-rendered page. Existing mutation handlers still use their original endpoints, then refresh the selected catalog and real KPI totals. The legacy client-only path remains for an older cached template during transition; current markup explicitly selects the server path. Authorized product-detail deep links still work when the product is not on the selected page.

Annotated read example:

```text
GET /admin-products/?format=json&listing_status=active&status=approved&page=2
    -> existing authenticated/permission-scoped view
    -> overall stats + filtered page 2
    -> rows_html, pagination_html, stats, page/pages, total, start/end
```

`stats.approved` is the overall authorized approved count. `total` is the number matching Active + Approved. `start/end` describe the ten-row page, so those values need not equal the KPI. In the isolated regression example, 15 approved records include one archived listing: normal Active/Approved matches 14, while explicit All/Approved matches 15. These numbers are test fixtures only, never production constants.

### 5. Backend / API behavior and permissions

- Added a JSON **read mode to the existing Products view**, not a new business API/framework. HTML and JSON share the same authorized queryset and row template. Responses are private/no-store under the existing stricter admin cache middleware.
- Super Admin scope stays global. Marketplace/custom-role scope and manage/review permissions remain existing Django capabilities. Facilities Admin did not receive marketplace permissions. Read-only users receive View Details without Add/Edit/Archive/approval controls; direct unauthorized mutations remain denied by Django. Student sellers retain the existing own-product API and ownership guards.
- Existing new seller submissions stay Pending where required; legitimate authorized admin creation retains its existing auto-approval behavior. Existing permission-aware edit/status handling is unchanged. No new content-change/reapproval policy was invented. Approve/reject still validate pending active state, persist the supported rejection reason, log existing audit events and invoke the existing notification outbox hooks.
- Public marketplace eligibility still requires approved, non-archived listings. Archive remains soft archive with confirmation and supported restore; existing orders/stock/audits are preserved. The browser test opens/cancels Archive and verifies that no write is made before confirmation.
- Available quantities use the same canonical value already reduced by active reservations. They are not reduced a second time. Physical On Hand remains Available + Reserved in existing inventory details. Simple/FIFO reservation/completion/cancellation services and virtual bundle component calculations were not changed.

### 6. Database / migration impact

No schema migration, dependency upgrade, data cleanup, stock movement, role grant or live product/order write. The selected database remains localhost PostgreSQL port 5432; no environment setting, service launch/restart, APK operation or remote deployment was performed. Actual database verification used an enforced READ ONLY transaction and source rendering, rather than creating demo data or claiming a restarted running server.

### 7. Tests performed

- **144 affected Django tests passed** in 25.525 seconds against disposable local PostgreSQL. Suites: `modules.marketplace.test_product_catalog`, `.tests`, `.test_product_review_images`, `.test_bundles`, `.test_inventory_monitor`, `.test_order_fulfillment`, `.test_fifo_inventory`, and `api.test_mobile_seller_application`. The test database was destroyed afterward.
- Seven new catalog tests cover all four KPI definitions, filtered-vs-overall archived approval scope, default/selected listing values, search including actual SKU and seller name, status/category/Program/Major, server pagination/global numbering, variants/bundles/reservations, Django/mobile academic inheritance, read/manage/Facilities boundaries and query growth. The archive regression now explicitly requests Archived instead of expecting hidden archived rows in the Active page's HTML.
- A larger exploratory run of 170 tests had 168 passes and **two unrelated Roles test mismatches**: `RolesWorkflowTests.test_page_batches_role_permissions_and_admins_and_exports_browser_fixture` expects Reports while the existing role configuration says Reports & Analytics (`accounts/role_permissions.py:75`); `test_history_reads_existing_role_audit_only_with_pagination_and_no_writes` expects exactly no-store while existing middleware adds the stricter private/no-cache/must-revalidate/max-age header (`accounts/middleware.py:26`). Those files/expectations were not changed as part of Products. Do not describe that broader run as fully passing.
- **263/263 Chromium checks passed** across 12 renders at ten widths, 1920 down to 280px, including a read-only role and a touch-device context. Checks cover the desktop two-row proportions, six 44px controls, scoped Montserrat, no page overflow, desktop action visibility, 44px touch action targets, actual image endpoint/fallback, long names, row/page counts, all KPI shortcuts, preserved default/selected filters, individual clearing, Program/Major, empty/error/retry, debounced requests, keyboard KPI operation, archive confirmation/cancel and zero writes. Actual desktop, tablet and phone screenshots were inspected; header truncation and the legacy important button-size conflict were corrected.
- Direct SQL execution measurement: 9 calls before versus 8 after adding 20 additional catalog records; page size stays ten. This demonstrates no per-record query growth in the checked page scenario, not a full load benchmark. Low-stock JSON/SKU substring scans remain bounded-memory reads.
- Enforced read-only source rendering against actual local PostgreSQL returned 200. Total and default Active counts matched real records, page size was bounded at ten, and an empty search kept the same overall KPI totals. `node --check backend/static/components/js/admin_products.js` and scoped whitespace checks passed. Django's test-run system checks reported no issues.

### 8. Remaining limitations, troubleshooting and safe practice

Restart your existing Django development process when ready, then refresh Products to load the new Python/templates and `20261031-product-catalog` assets. This task did not launch/restart services or deploy Kamatera. An already cached older template keeps its legacy client behavior until it is refreshed against the updated backend. No full physical-device/assistive-technology audit or production-scale benchmark was performed.

SKU substring matching streams existing generated identities; option-level low-stock eligibility streams required JSON fields. Both keep query count/memory bounded but still perform catalog-sized work. Very large catalogs may later benefit from indexed persisted search/alert projections; no stale global cache or redundant schema was introduced here. Existing reapproval rules and notification delivery configuration remain as found; live message delivery was not exercised.

If a KPI exceeds visible rows, compare the overall scope explanation, listing/approval selections and pagination count before treating it as a data defect. If a table request fails, read the error and use Retry; existing rows intentionally remain until a successful response. A missing picture intentionally uses the package icon; image authorization still follows the existing tab/cookie flow. If Add/Edit is absent, check the user's actual manage-product permission and Program/Major scope rather than enabling controls in JavaScript. Earlier single-row/green-pill guide sections below are historical.

Safe practice: run the isolated backend runner with `modules.marketplace.test_product_catalog`, then inspect its approved-archived test: Active/Approved shows 14 and All/Approved 15 while the KPI stays 15. Run `node scratch/products-module-20261031/check.cjs` after exporting its isolated fixtures to exercise filters, pagination and a simulated 503/retry without reaching the working application. Change only a test fixture's long product name and verify the page/actions still fit; restore it afterward. Never add sample listings or alter working stock simply to populate a screenshot.

# Products List — quantity-first Inventory column

## Products List Table Improvements — October 29, 2026

### 1. Cause / reason

The CampusHub Web Admin Products table (`#productsTable` on `/admin-products/`) needed refinement to improve typography hierarchy, column alignment, inventory presentation, status clarity, row actions, and responsive layout without redesigning the page or modifying the already-approved filter section.

Key defects resolved:
- **Thumbnail Sizing & Centering**: Fallback initial letters in `.product-table-image-empty` were offset due to generic `span` block display rules and flex sizing conflicts. Thumbnails are now strictly 40×40px with centered initials.
- **SKU Visibility**: Product SKU labels (`.product-id-label`) were hidden via CSS and wiped out by client-side image hydration (`applyImageToRow`). SKUs are now preserved under product names with clear secondary hierarchy.
- **Approval vs. Listing Status**: Listing status (`Active` vs. `Archived`) was previously not rendered as a badge in the table rows, making archived products look identical to active approved products. The status column now explicitly renders both Approval Status (`Approved`, `Pending`, `Rejected`) and Listing Status (`Active`, `Archived`) in a disciplined vertical stack (`.status-cell-stack`).
- **Authorized Edit Action**: The Edit action button (`.btn-edit-product` with pencil SVG) was missing from the table's action row even though the backend already supported and permissions-gated it. The Edit button is now exposed for users with `can_manage_products` permission.
- **Inventory Formatting**: Stock quantities are displayed prominently (e.g., `1 pc`, `12 pcs`, `6 bundles available`). Configured low stock thresholds appear as secondary text (`Threshold: 5`), with clear warning indicators for low stock and out-of-stock items, and derived component indicators for bundles, without redundant "In Stock" badges.
- **Table Layout & Alignment**: Header and cell alignment were aligned logically (center for index `#`, left for product/seller/category/inventory/status/date, right for price and row action buttons). Fixed table layout prevents column collision across desktop and responsive viewports.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Changes made |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/partials/product_actions.html` | lines 1–11 | Added authorized Edit button (`.btn-edit-product` with pencil SVG, `title="Edit Product"`, `aria-label="Edit product"`) inside `{% if can_manage_products %}`. Retained View, Approve, Reject, Archive, and Restore action buttons. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | line 23; line 113; line 116; line 162; line 163; line 180; line 1025 | Added `class="col-category"` to Category header and cell; updated status header to `Approval & Listing`; rendered `.status-cell-stack` with `.status-pill` and `.listing-status-pill`; added hover `title` attributes on seller, program/major, and category cells; bumped cache query strings to `?v=20261029-product-list-table`. |
| `backend/static/components/js/admin_products.js` | lines 525–550; lines 1744–1755; lines 1774–1835; lines 1850–1865; lines 2435–2445; lines 2640–2650; line 2887; lines 3980–4050 | Added `renderListingStatusPill`, `renderStatusCellContent`, and `renderSubmittedDateCell`; added Edit button in `renderProductActionsCell` when `canManageProducts` is true; set `row.dataset.isArchived` in `renderProductRow`; preserved SKU in `applyImageToRow`; updated status cell on approval/archive/restore; called `applyInlineFilters()` on save; exported helpers on `window.CampusHubAdminProducts`. |
| `backend/static/components/css/admin_products_refinement.css` | lines 30–95 | Added exact column widths for 9 columns; defined 40×40 thumbnail sizing and initial centering; ensured `.product-id-label` visibility; left-aligned inventory summary and status badges; set tabular numeric alignment on prices; styled action buttons (29×29px outline buttons) and pagination controls. |
| `backend/core/modules/marketplace/test_product_review_images.py` | lines 18–40; lines 80–90 | Updated tests to assert presence of `btn-edit-product` when `can_manage_products=True` and its absence when `can_manage_products=False`; asserted separate listing status badge rendering. |
| `docs/products-list-inventory.md` | top section | Documented changes, functions, data flow, tests, troubleshooting, and safe practice exercise. |
| `CAMPUSHUB_CONTEXT.md` | top section | Recorded completion of Product List Table improvements and updated asset versions. |

### 3. Changes made

1. **Table Structure & Typography**:
   - Preserved the existing 9-column `<colgroup>` and table markup in `#productsTable`.
   - Updated the status header to `Approval & Listing`.
   - Added `col-category` class to Category header and cells for consistent left alignment.
   - Sized thumbnails to strictly 40×40px with `border-radius: 8px` and centered fallback initials.
   - Restored `.product-id-label` visibility (`color: #667085; font-size: 0.71rem;`) below the product name.
   - Added hover `title` tooltips to product names, seller names, academic program/majors, and categories to prevent layout breaking from long strings.

2. **Inventory Presentation**:
   - Primary stock count displayed prominently (`#1A1851`, bold 0.83rem, e.g. `1 pc`, `12 pcs`, `6 bundles available`).
   - Configured threshold displayed as secondary text (`Threshold: 5`) for simple products.
   - Component-derived availability clearly indicated for bundles (`Derived from components`).
   - Out of stock (`• Out of Stock`) with navy dot and low stock (`• Low Stock`) with gold dot displayed when applicable.
   - Eliminated redundant "In Stock" badges when inventory is healthy.

3. **Status Badges & Refined Indicators**:
   - Stacked Approval Status (`Approved`, `Pending`, `Rejected`) and Listing Status (`Active`, `Archived`) in `.status-cell-stack`.
   - **Approved Pill Redesign & Clean Text**: Replaced the solid dark navy pill with an institutional, WCAG AA compliant soft green badge (`background: #ECFDF3; color: #027A48; border: 1px solid #ABEFC6; font-weight: 600;`). Removed decorative checkmark and symbol icons from all status pills to eliminate modern UI clutter and preserve a disciplined, text-first university aesthetic. Pending remains warm gold (`#FCB316`), and Rejected remains red outline (`#B91C1C` on `#FEF2F2`).
   - **Unboxed Listing Status**: Removed the bordered container/pill box from `Active` and `Archived` (`border: none; background: transparent; padding: 0; box-shadow: none;`). Listing status renders as a clean secondary text line with an indicator dot (6px gold dot `#FCB316` for Active, 6px muted gray dot `#98A2B3` for Archived) directly underneath the Approval status badge.

4. **Action Buttons**:
   - View Product (Eye icon, `.btn-view-product`, `title="View Product"`).
   - Edit Product (Pencil icon, `.btn-edit-product`, `title="Edit Product"`), exposed strictly when `can_manage_products` is true.
   - Approve / Reject buttons (Check / Cross icons) rendered for pending active products when `can_approve_products` is true.
   - Archive / Restore button (Box icon for active, circular arrow icon for archived) rendered when `can_manage_products` is true.
   - Action row uses small 29×29px outline icon buttons aligned in a single row without wrapping.

5. **Client-Side Synchronization**:
   - `applyImageToRow` preserves the SKU element during gallery image hydration.
   - Product save and edit forms re-render the table row with both approval and listing statuses, update pagination via `applyInlineFilters()`, and refresh the table footer.
   - Archiving or restoring a product immediately updates both the listing status badge (`Active` ↔ `Archived`) and the action button (`Archive` ↔ `Restore`).

### 4. How it works: functions, inputs / outputs and data flow

```text
Server Template Render (Django context: seller_products, can_manage_products, can_approve_products)
  ├── <thead>: #, Product, Seller & Program, Category, Price, Inventory, Approval & Listing, Date Added, Actions
  └── <tbody>: <tr data-product-id="..." data-is-archived="..." data-product-status="...">
        ├── .col-product-name: 40x40 thumbnail + <strong>name</strong> + .product-id-label (SKU)
        ├── .col-seller: <strong>seller</strong> + <span>program_major</span>
        ├── .col-category: category text
        ├── .col-price: ₱ price (right-aligned tabular nums)
        ├── .col-inventory: .inventory-summary-clean (quantity + threshold + warning / bundle notes)
        ├── .col-status: .status-cell-stack (.status-pill + .listing-status-pill)
        ├── .col-date: Date Added + time
        └── .col-action: .action-row (View, Review buttons if pending, Edit if authorized, Archive/Restore)

Client-Side Hydration & User Interactions (admin_products.js):
  ├── hydrateProductImagesFromServer() -> applyImageToRow() (preserves SKU, updates image)
  ├── Edit Button Click -> openEditProductForm(row) -> populates form with getProductFromRow(row)
  ├── Save Product -> saveProductToServer() -> finalizeSave() -> renderProductRow() -> applyInlineFilters()
  ├── Archive / Restore -> confirmArchive/Restore -> updates data-is-archived -> re-renders status and actions
  └── Inline Filters -> applyInlineFilters() -> shows/hides rows -> recalculates pagination and showing text
```

### 5. Backend / API behavior

- Server-side permissions enforce product operations in `backend/core/api/views.py`:
  - `admin_save_product` (`POST /api/products/admin/save/`): Requires `can_manage_products` permission and scopes to manageable products via `manageable_products_for(request.user)`.
  - `admin_archive_product` (`POST /api/products/admin/<id>/archive/`): Requires `can_manage_products` permission.
  - `admin_restore_product` (`POST /api/products/admin/<id>/restore/`): Requires `can_manage_products` permission.
  - `approve_product` / `reject_product`: Requires `can_approve_products` permission and pending active status.
- No new database fields or API endpoints were added.

### 6. Database / migration impact

- Zero schema migrations. All fields (`approval_status`, `is_archived`, `stock`, `low_stock_threshold`, `product_type`, `department_id`, `major_id`) already exist on the `Product` model.
- Live database was not modified during testing; all test executions utilized the isolated local `test_campushub` database.

### 7. Tests performed and troubleshooting

1. **Django Test Suite**:
   - Ran 92 marketplace regression tests against local `test_campushub` with `--keepdb --noinput`:
     `modules.marketplace.test_product_review_images`
     `modules.marketplace.test_product_final_validation`
     `modules.marketplace.test_program_inventory.ProgramInventoryTests`
     `modules.marketplace.test_thresholds`
     `modules.marketplace.test_variant_inventory`
     `modules.marketplace.test_bundles`
     `modules.marketplace.test_inventory_monitor.InventoryMonitorTests`
     `modules.marketplace.tests.MarketplaceAdminProductAccessTests`
   - **Result: 92 passed in 16.568s (`OK`, 0 failures, 0 errors, 0 silenced issues).**
2. **JavaScript Syntax Verification**:
   - `node --check backend/static/components/js/admin_products.js` passed with zero errors.
3. **Playwright Browser Automation Verification**:
   - Tested across viewports (1920, 1366, 1024, 768, 390px):
     - Verified 9 headers including `Approval & Listing`.
     - Verified prominent stock count, secondary threshold, low stock warning, out of stock warning, and bundle component-derived availability.
     - Verified separate `Approved`/`Pending`/`Rejected` and `Active`/`Archived` status badges.
     - Verified 40×40px thumbnail sizing and centered fallback initial.
     - Verified SKU visibility under product names.
     - Verified 5 action buttons on pending rows align horizontally without wrapping.
     - Verified Edit Product button opens edit form with matching product data.
     - Verified responsive horizontal scrolling inside `#productsTableWrap`.
   - **Result: `ALL_TABLE_CHECKS_PASSED`.**
4. **Visual Inspection**:
   - Inspected high-resolution screenshots `table-1920.png` and `table-1366.png` to confirm visual balance, typography contrast, and alignment.

### 8. Remaining limitations and safe practice exercise

- Responsive horizontal scrolling is constrained to `#productsTableWrap` for viewports under 1224px to preserve institutional data density without squishing table columns.
- The browser checks were verified using automated headless Chrome; native mobile app screens remain independent and untouched.

**Safe Practice Exercise**:
1. Navigate to `/admin-products/` in the web admin.
2. Observe the Products List table: notice the 40×40px thumbnails, visible SKUs below product names, prominent stock counts with threshold text, and distinct Approval and Listing status pills.
3. Hover over the action buttons: notice tooltips for "View Product", "Edit Product", and "Archive Product".
4. For users with product management permissions, click the pencil (Edit) icon on any active product: verify the form switches to "Edit Product" mode with prefilled values.
5. Filter by "All Listing Status": observe both active and archived products, where archived products show the "Archived" pill and the circular arrow "Restore Product" action.
6. Verify this using the automated test suite:
   ```powershell
   .\backend\core\venv\Scripts\python.exe backend/core/manage.py test modules.marketplace.test_product_review_images --keepdb --noinput
   ```

---

## Individual selected-filter clear icons - October 29, 2026

Current follow-up: show a visible **×** when a Products filter has a value, and let that action clear that individual filter. The existing six-filter desktop row and responsive wrapping remain. This authorizes individual field actions after the previous removal of the global Clear Filters button; that global button remains removed.

### 1. Cause / reason

Confirmed: the six native controls and existing filter handlers had no individual clear action after removal of the global button. Dropdown selections therefore had to be reset by choosing their existing All option. The user requested a visible x for a selected filter. A small field-specific button now provides that action without replacing the native controls or duplicating filtering logic.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change and expected behavior |
| --- | --- | --- |
| `backend/static/components/js/admin_products.js` | 2740 field enhancement; 2769 `syncFilterClearButtons`; 2778 `applyInlineFilters`; 2800 synchronization | Wrap each existing label in a positioning container, add an accessible clear button outside the label, and derive visibility from that field's current value/disabled state. Clearing dispatches the original input/change event. |
| `backend/static/components/css/admin_products_refinement.css` | 28 `.product-filter-field`; 29/30 selected-value padding; 31 `.product-filter-clear`; 33 hidden; 34/35 hover/focus; 36 native search cancel | Place a navy 28px clear target beside the select arrow, or at the search field's right edge; reserve space and preserve heights/corners/grid. Hide duplicate native WebKit search cancellation only in this filter bar. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 23 stylesheet URL; 1025 script URL | Refresh both cache keys to `20261029-product-list-table-filter-clear`, retaining the existing table-update identifier. Filter markup/options/defaults are untouched. |
| `docs/products-list-inventory.md` | 3 this report | Current behavior, data flow, verification and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | 3 current clear-icon note | Preserve the follow-up and verified scope. |

Ignored QA tools/results: `scratch/products-filter-clear-20261029/check.cjs`, `major_check.cjs`, copied isolated HTML/JSON inputs and actual render captures. These reuse previously exported Django test fixtures and current shipped scripts/styles; every browser request is intercepted. No backend test or application dependency was added.

### 3. Changes made

- Search, Approval Status, Listing Status, Program, Major and Category each get a native `type="button"` clear action. The SVG is decorative; each button has a specific accessible name, such as Clear Category filter, and a tooltip.
- The button is visible only when the control is enabled and has a nonblank value. It disappears after clearing. The default Listing Status remains **Active**, so that initially selected filter also shows its x. Empty All options and a disabled Major show no x.
- Clearing changes only the clicked field. Clearing Program can also clear/disable an incompatible Major through the existing academic dependency handler; other filters remain selected.
- The original input/select and its label remain intact. The button is a sibling of the label, avoiding a second interactive control inside the label. After activation, focus returns to the original field.
- The one-row desktop allocation, existing responsive breakpoints, 44px input heights, selected values/options and other product/table work remain. The global Clear Filters button was not restored.

### 4. How it works: functions, inputs / outputs and data flow

The enhancement at line 2740 receives the existing field references and their current captions, creates a `.product-filter-field` around each original label, and appends one clear button. It does not clone the field or save another copy of its selected value. `syncFilterClearButtons()` reads those original controls, sets each button's `hidden` flag and toggles the wrapper's `has-filter-value` class for text padding. It runs on input/change and at the end of `applyInlineFilters()`, including URL initialization, KPI changes and programmatic updates using that existing filter function.

Clicking x sets the original value to `''` and dispatches its usual event: `input` for Search or `change` for a select. Existing handlers then perform filtering, academic synchronization, URL updates, pagination and empty-state updates. Search keeps its original 300ms debounce. Selecting another dropdown value keeps the original dropdown workflow. Nothing is submitted to a product/stock write endpoint.

```text
Selected input/select -> syncFilterClearButtons -> visible field-specific x
Click x -> original field.value = '' -> original input/change event
  -> academic dependency rules where applicable -> applyInlineFilters
  -> filtered rows + existing URL state -> x visibility recalculated
```

Annotated example: select Category = Clothing while Listing Status = Active. The Category x clears Category to All Categories and dispatches its existing change event; Listing Status remains Active. Clicking Listing Status's own x chooses the existing All Listing Status value. The original fresh-page Active default and URL initialization rules are unchanged; as before, a URL without a listing-status parameter returns to Active on reload.

### 5. Backend / API behavior

No Django view, REST endpoint, authentication/permission rule, database query or response shape changed. Clearing reuses the same authorized rows, AND filtering, query keys and Program/Major options already supplied by the application. The dedicated Inventory ledger and other components were not modified.

### 6. Database / migration impact

None: no migration, model, configuration, live record, stock, pricing, approval or deployment change. This step did not run a database-writing verification or submit a product action. Browser verification used intercepted isolated fixture requests; the Program/Major check used existing exported test records only.

### 7. Tests performed and troubleshooting

- **126/126 Chrome checks passed** across 1920, 1440, 1280, 1024, 768, 600, 390 and 320px. They cover the six original fields, individual button visibility, unchanged Active default, row counts/heights/corners/containment, existing filtering and URL restoration, click and keyboard clearing, focus return, preservation of other selections, search debounce, valid labels, narrow-screen targets and zero application writes.
- **10/10 Program/Major checks passed** against the existing exported populated-major fixtures: selecting/clearing Major preserves Program/Active, while clearing Program clears/disables its dependent Major and hides both relevant icons.
- Desktop selected-state and narrow actual renders were inspected. JavaScript syntax and scoped whitespace checks passed. No new Django/Flutter suite was necessary for this frontend-only change; their earlier results below belong to their respective earlier steps.
- The first mobile hit-test checked controls outside the scrolled viewport and failed. Corrected the QA helper to scroll each button into view before measuring its hit target; no production layout change was needed for that test correction.

If x does not appear, verify the field has an enabled, nonblank value, then hard-refresh to load the new asset keys. Program without configured majors intentionally leaves Major disabled. Search clearing updates through the same debounce as typing. If an active KPI changes fields programmatically, use the existing `applyInlineFilters()` path so the filtered rows and button visibility synchronize together.

### 8. Remaining limitations and safe practice exercise

Chrome was checked at desktop/tablet/mobile viewport sizes; no physical-device or full assistive-technology audit is claimed. Long selected native-option text may still abbreviate at constrained widths, with its full label available in the dropdown. Hosted Kamatera application source was not deployed.

Safe exercise: on Products, select a category and confirm its x appears. Click that x and confirm Category becomes All Categories while Listing Status remains Active. Repeat with a program that already has majors: select a Major, clear only Major, then select it again and clear Program. Confirm only the existing dependent Major is reset. Type and clear Search, then use Tab/Enter on another visible x. These filter interactions do not submit a product or stock update; avoid Save/Archive/approval actions during this exercise. Repeat isolated verification with `node scratch/products-filter-clear-20261029/check.cjs` and `node scratch/products-filter-clear-20261029/major_check.cjs`.

---

## Products filters in one desktop row; Clear Filters removed - October 29, 2026

Scope clarification: the user explicitly selected the **Products** filter bar containing Search, Approval Status, Listing Status, Program, Major and Category. The separate Inventory ledger has a different filter set and was not changed. The final “make one row” instruction supersedes the earlier two-row percentage layout.

### 1. Cause / reason

Confirmed: the Products-specific refinement stylesheet used a four-column grid and made Search span two columns. Together with six controls and Clear Filters, this produced multiple desktop rows. The request removes that button and puts the existing six filters on one desktop row, preserving their behavior and selected values.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change and reason |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 23 stylesheet URL; 86 `.product-catalog-filters`; 89 `productsArchiveFilter`; 1025 script URL | Removed only the Clear Filters button from the existing filter block; refreshed the two asset cache keys. All six labels, IDs, options, academic attributes and the Active selected attribute remain. |
| `backend/static/components/css/admin_products_refinement.css` | 24 comment; 25 scoped grid; 26 first-label span; 84/94/101 responsive breakpoints | One wider Search column plus five equal dropdown columns on desktop. Search no longer spans two columns; existing three/two/one-column responsive rules remain. |
| `backend/static/components/js/admin_products.js` | 2780 search timer; 2784 dashboard/URL initialization after the removed listener | Removed only the click listener for the deleted `productsClearFilters` element. Search, all change handlers, URL restoration, academic pairing and filtering functions are unchanged. |
| `docs/products-list-inventory.md` | 3 this report | Current scope, implementation, data flow, tests, troubleshooting and practice guide. |
| `CAMPUSHUB_CONTEXT.md` | 3 current Products filter note | Preserve the confirmed page target and current one-row direction. |

Ignored verification helper: `scratch/products-filter-row-20261029/check.cjs`. Its HTML/JSON inputs were exported by the existing Django test suite into the same folder, using a disposable local test database. Browser requests are intercepted; it does not submit stock/product changes to localhost or Kamatera.

### 3. Changes made

Removed the Products Clear Filters button and its now-unreachable event listener. Retained shared `.catalog-clear-filters` styling because the separate Inventory ledger still uses it. No replacement button, filter, status option or unrelated component was added.

The Products-only grid is now `minmax(0, 1.75fr) repeat(5, minmax(0, 1fr))`: Search gets more room and the five dropdowns share equal widths. Existing 12px gaps, 16px/20px section padding, 44px input heights, corner styles, navy/white colors, product typography and input behavior remain. At widths up to 1279px the six filters use three columns; up to 767px they use two; up to 575px they stack in one column. The scope selector prevents this change from affecting the Inventory ledger or other pages.

### 4. How it works: functions, inputs / outputs and data flow

No new application function was needed. CSS Grid controls presentation only. Existing `applyInlineFilters()` at `admin_products.js:2706` reads Search, Approval Status, Listing Status, Program, Major and Category, combines their predicates with AND, and shows/hides authorized product rows. Its listing fallback at line 2709 remains `active`. It updates the existing URL parameters at line 2724 and removes the obsolete page parameter so pagination can recalculate filtered rows.

The existing search handler at line 2781 keeps its 300ms debounce. Select change handlers still call the same filter function. URL initialization at line 2784 restores values supplied in the query string. The unchanged `CampusHubAcademic.sync(program, major)` limits majors to the selected program, retaining the original clear/disabled behavior when a major is not valid for that program. Removing the explicit Clear button does not change those rules.

```text
Django-authorized product/master-option context -> existing Products template
  -> same six input/select elements -> existing change/debounced search handlers
  -> applyInlineFilters -> matching rows + existing URL/pagination/empty-state updates
```

Annotated layout example: the first grid track has weight 1.75 and the remaining five tracks each have weight 1. All tracks may shrink within the available page width because their minimum is zero. Below the existing breakpoints, equal responsive tracks replace that desktop allocation. This reuses the current stylesheet rather than introducing a new component or duplicated filter state.

### 5. Backend / API behavior

No Django view, REST endpoint, permission gate, query parameter, option source, product serializer or API integration changed. Listing Status still defaults to **Active**; All Listing Status and Archived remain existing choices. The dedicated Inventory ledger and its Clear Filters recovery links remain unchanged, as explicitly distinguished during clarification. Product details, stock, pricing, approvals, KPI shortcuts and academic master data retain their existing implementations.

### 6. Database / migration impact

None. No schema/migration, environment change, live record update, seed, new dependency or hosted deployment. Existing test fixtures were created in a new disposable **local** PostgreSQL test database and that database was destroyed afterward. All Chrome requests were fulfilled from local test HTML/JSON/assets, and no application-data writes were submitted.

### 7. Tests performed and troubleshooting

- Existing `modules.marketplace.test_inventory_monitor`: **19 tests passed in 7.881s**, with Django system checks reporting no issues. The isolated export uses the current template and actual test-generated product/API fixtures.
- **103/103 Chrome checks passed** at 1920, 1440, 1280, 1024, 768, 600, 390 and 320px: all six original controls/labels, no button/replacement, original Active default, expected row counts, matching 44px heights/corners, no page/filter overflow, wider Search/five equal desktop dropdowns, debounced search, approval/listing/program/category combinations, URL restoration, tab-session preservation, no script errors and no data writes.
- Desktop and 320px actual filter renders were inspected. The desktop shows six aligned controls; the mobile capture shows the same six stacked controls.
- JavaScript syntax and scoped whitespace checks passed. No new application test suite was added for this reversible presentation cleanup.
- The first browser attempt mocked the session endpoint with the wrong response and was correctly redirected to logout before the page loaded. Corrected only the test response to match the existing authenticated-session contract, then reran successfully. Authentication code was not edited or bypassed in the application.

If the button or old layout remains, hard-refresh `/admin-products/` and verify `admin_products_refinement.css` and `admin_products.js` both have the `20261029-filter-row` cache key. Below 1280px, wrapping is expected. Native selects may abbreviate long selected text at constrained widths; the full original option text remains in their dropdown menus. A disabled Major control follows the existing selected-program/master-option rules rather than this layout change.

### 8. Remaining limitations and safe practice exercise

Verified with isolated fixtures and desktop Chrome at mobile/tablet viewport sizes; a physical-device or full screen-reader audit was not performed. The hosted Kamatera application source was not deployed. Source edits are visible through the existing localhost development workflow after refreshing.

Safe exercise: open `/admin-products/` without a listing-status parameter and confirm Active is selected. Enter a known product name, wait briefly, then change an existing category/program option and confirm filtering remains combined. Reload and confirm URL-selected values return. Resize the browser below 1280, 768 and 576px to see three, two and one columns. These filter interactions do not submit a stock or product edit; leave product action/save controls untouched. To repeat the fixture-only browser verification, run `node scratch/products-filter-row-20261029/check.cjs` after exporting its isolated test fixtures.

---

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

