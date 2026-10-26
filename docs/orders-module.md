# Orders module: Pickup, Seller Delivery and payment monitoring

## One-row desktop filter bar — October 25, 2026

1. **Cause / reason:** `.orders-filters` used four grid columns, falling to three below1440px, so its seven fields plus Clear Filters occupied multiple desktop rows.
2. **Exact files changed:** `backend/static/components/css/admin_orders.css:26` defines eight intrinsic desktop tracks with contained horizontal overflow; line116 moves the three-column transition to1000px. Existing768px/two-column and576px/single-column rules remain. `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html:12` updates the CSS version; line58 gives the existing filter form an accessible name and keyboard scroll target. This guide and `CAMPUSHUB_CONTEXT.md` document the change; Seller Applications companion files are listed in its guide.
3. **Changes made:** Search, Order Status, Payment Status, Program, Major, Date, Fulfillment and Clear Filters share one row above1000px. The form can scroll horizontally when a narrow desktop cannot fit readable controls. Tablets/phones keep responsive stacking. Custom From/To controls still appear below the main row when Custom Range is selected.
4. **How it works / data flow:** CSS changes only placement. The same named inputs feed the unchanged Orders JavaScript/GET submission, then `orders_page_context(actor, params)` applies existing authorization and combined filters before pagination. Existing date inputs retain disabled/hidden handling. Example: selecting Unpaid still submits `payment=unpaid` to `/admin-orders/`; column placement never changes the query or payment records.
5. **Backend / API behavior:** No Orders Python, JavaScript, route, permission, filter calculation, status, fulfillment, payment or FIFO change. Existing tab authorization and Clear Filters destination remain unchanged.
6. **Database / migrations:** None; no working records changed. The combined before/after twelve-table fingerprints match. No live orders or profile uploads were created for visual verification.
7. **Actual tests:** Combined **68 tests passed in14.074s** for Orders, seller applications, profile media and Marketplace support. **221 browser assertions /30renders** passed at1920,1440,1280,1024,768,390,320px, checking all eight main controls, a single desktop row, contained overflow, tablet/mobile stacking, existing status/fulfillment options, custom date visibility and actual payment-filter submission. No page overflow, missing static assets or JavaScript errors; browser routes used isolated rendered fixtures only. Desktop/mobile screenshots were inspected. Django system check passed. Reproduction and logs: `scratch/seller-avatar-order-filters/run-tests.py` and `verify.cjs`.
8. **Limits / troubleshooting / safe exercise:** Keeping readable controls in one row may require scrolling the filter bar at narrower desktop widths; the page itself does not scroll horizontally. At1000px and below, filters stack to preserve usability. If a cached multi-row desktop layout remains, refresh the updated CSS asset. Safe exercise: resize to1440px and390px, tab through the controls, choose Custom Range and confirm From/To remain usable. Exercise submissions with the isolated browser fixture to avoid modifying any order.

## October 25, 2026 — current Seller Delivery implementation report

This section supersedes older pickup-only notes below. The user approved implementation and chose **Delivered separately; keep the order open until payment is confirmed**. Seller Delivery means the seller personally delivers. No courier, rider, shipping provider, tracking integration, delivery fee or online payment gateway was added.

### 1. Cause / reason

The inspected Flutter COD selector was disconnected from checkout/API storage. Django had no fulfillment fields or delivery events; admin completion was pickup-specific and mobile sellers could only read orders. A truthful solution needed stored fulfillment and authorized progress, rather than relabeling unsupported statuses. The existing order/inventory workflows were reused.

### 2. Exact files changed — current lines and anchors

Paths are relative to the repository root. Other pre-existing dirty files were preserved.

| File | Current line / anchor | Change / reason |
| --- | --- | --- |
| `backend/core/api/models.py` | 911, fulfillment fields | Add method, destination, delivery start and Delivered time. Existing order/payment status definitions remain. |
| `backend/core/api/migrations/0048_order_fulfillment.py` | 1, Migration | Four additive fields; no historical classification or stock rewrite. |
| `backend/core/modules/marketplace/services/fulfillment.py` | 10, ORDER_TRANSITIONS; 18, fulfillment_buyer_guard; 45, presentation; 59, creation_fields; 77, advance | Shared validation, scope-independent presentation, buyer guard before replay and locked delivery events. |
| `backend/core/api/views.py` | 302, serializer; 1916, marketplace_orders; 1950, verified_buyer; 2045, creation | Save/serialize fulfillment, bind modern checkout to its actual signed-in buyer and scope order reads before exposing destinations. |
| `backend/core/accounts/views.py` | 890, admin_order_update; 901, fulfillment_action; 940/965, delivered guards; 1033, completion timestamp | Separate fulfillment updates from payment; prevent cancellation after Delivered; require delivery plus existing payment confirmation for completion; do not create pickup timestamps for delivery. |
| `backend/core/modules/marketplace/mobile_seller_views.py` | 97, order rows; 126, order_progress | Include actual owned-order fulfillment; recheck active approval and ownership before progress. |
| `backend/core/core/urls.py` | 99, mobile_seller_order_progress | One narrow progress POST capability; the existing workspace endpoint was read-only. |
| `backend/core/modules/marketplace/services/orders.py` | 22, filters; 169, decoration; 193, history; 206, pickup KPI | Combine fulfillment with existing filters, show method-specific ready labels and count only recorded Pickup in the pickup-specific KPI. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html` | 55, description; 81, filter; 121, column; 132, row data; Fulfillment Information / btnModalDelivery anchors | Preserve all ten original columns, add requested Fulfillment, actual Details and manager actions. Asset version: 20261025-seller-delivery. |
| `backend/static/components/css/admin_orders.css` | 26, filters; 43–45, table | Fit the new filter/column while preserving compact spacing and contained horizontal scrolling. |
| `backend/static/components/js/admin_orders.js` | 5, filter; 180, Details; 216, delivery action; 267, confirmation; 444, shared request helper | Show appropriate actions/details, send delivery-only events, preserve explicit cash acknowledgement and make the Pickup KPI select Pickup. |
| `campushub/lib/module_app/widgets/order_summary_widgets.dart` | 108, callback; 141, locked draft; 227, Fulfillment & Payment | Replace unsupported COD selection with method plus actual destination, separate from cash payment. |
| `campushub/lib/module_app/screens/checkout_screen.dart` | 43, draft; 88, placement; 183/234, shared summary | Send selection, validate destination, preserve retry payload and show placed state only after acceptance. |
| `campushub/lib/module_app/screens/cart_screen.dart` | 468, keyed drafts; 505, placement | Send method per line order and skip confirmed lines on retry. |
| `campushub/lib/module_app/services/order_service.dart` | 14, requestKey; 23, placeOrder | Bearer plus stable UUID key, no automatic POST failover, local history only after a valid accepted order. |
| `campushub/lib/module_app/services/seller_application_service.dart` | 123, orderProgress | Reuse existing authenticated service/error decoding for seller progress. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 79, _advanceOrder; 135, _orderProgressAction; 982, raw filter; 1069, action | Show actual fulfillment, valid steps, explicit Delivered confirmation and duplicate-tap guard. Processing replaces unsupported Confirmed; Ready covers both methods. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 249/402, onOrderProgress | Pass the existing service through the seller workspace boundary. |
| `backend/core/modules/marketplace/test_order_fulfillment.py` | 16, OrderFulfillmentTests; SellerDeliveryAccessTests | Nine isolated tests for paid completion, original batches, variants/bundles, invalid data, owner/approval and replay authorization. |
| `backend/core/api/test_mobile_seller_workspace.py` | 27, fixture | Self-contained isolated Program setup for the existing seller suite. |
| `campushub/test/order_fulfillment_test.dart` | 1, new tests | Four transport/widget tests: stable authenticated retry, no automatic retry and seller delivery at two widths. |
| `campushub/test/order_summary_test.dart` | 45, summary assertions; delivery selection test | Verify actual method/destination rather than the removed disconnected COD option. |
| `campushub/test/checkout_layout_test.dart` | checkout assertions / capture test | Verify the new control and load bundled fonts for QA screenshots. |
| `AGENTS.md` | 54, Marketplace policy | Save the user's updated two-method and separate-payment rules. |
| `CAMPUSHUB_CONTEXT.md` | 3, current status | Save accepted behavior, verification and limits. |
| `docs/orders-module.md` | 3, this report | Explain cause, files, functions/data flow, migration, verification and safe practice. |

Reproducible QA helpers, isolated HTML/PNG exports, logs and JSON evidence are in `scratch/seller-delivery/`; these are not application features.

### 3. Changes made

The five existing order states remain Pending, Processing, Ready for Pickup, Completed and Cancelled. No Confirmed/Out for Delivery/Delivered order-status values were added. For a recorded Seller Delivery method, the ready state displays Ready for Seller Delivery. Separate timestamp events display Out for Seller Delivery and Delivered.

| Action | Order/payment behavior | Inventory behavior |
| --- | --- | --- |
| Place either method | Pending, default Unpaid | Existing exact-SKU/recipe FIFO reservation. |
| Process / Ready | Existing transitions, payment unchanged | No additional deduction. |
| Start Seller Delivery / Delivered | Ready state retained; separate actual events, payment unchanged | Allocations stay Reserved. |
| Complete after explicit payment confirmation | Completed + Paid; delivery must already be recorded | Existing completion consumes allocations once; available stock is not deducted again. |
| Cancel before Delivered | Existing cancellation/payment rules | Existing restoration to original batches once. |
| Cancel after Delivered | Rejected | No unsupported return/refund or stock restoration. |

Approved active owners can advance processing/readiness and delivery for their own orders. The new seller endpoint cannot record payment, complete/cancel orders, change fulfillment/destination or affect another seller. Existing admin management and academic scope remain. Historical method stays blank/Not recorded. Ready for Pickup KPI/click now includes only explicit Pickup, excluding delivery and unknown legacy methods. The original ten columns, existing filters, debounce and server pagination remain; Fulfillment is the requested eleventh column/filter. Styling remains navy/gold/white and content-driven.

### 4. How it works — functions, inputs, outputs and data flow

Flutter's shared summary calls onFulfillmentChanged(method, destination). Single/bulk checkout includes those fields in its existing order payload. requestKey creates a UUID reused for an unresolved submission. The original draft is locked after its first attempt; bulk checkout skips confirmed indexes. Failed/unconfirmed requests do not create successful local history or show Orders Placed.

The existing order endpoint receives the payload. fulfillment_buyer_guard validates modern buyer identity before FIFO cached replay. creation_fields validates the method and required destination (up to 500 characters) before stock writes. New requests snapshot the authenticated buyer's actual name/email. Existing placement, variant/bundle validation, stock reservation and FIFO attachment then run unchanged. presentation(order) produces actual method, ready label, progress, destination and timestamps.

Seller progress uses existing bearer authentication and approved_seller. The adapter locks/rechecks approval and supplies seller_order_queryset to advance. advance locks the authorized order, validates the next step, records its timestamp/status and actual actor in the existing status-history table. Repeated delivery events do not duplicate timestamps/history. It never changes payment or stock. Admin fulfillment actions use the same helper through the existing management gate. Completion checks actual Delivered for Seller Delivery plus the existing payment acknowledgement, then calls the existing completed-sale/FIFO services. Existing sales/dashboard revenue remains Completed AND Paid.

Annotated example: an isolated two-unit delivery reserves one unit from each of two batches. Delivered leaves both allocations Reserved and payment Unpaid. Cancellation is rejected. Explicit paid completion consumes both allocations without another available-stock deduction. The automated test performs this against isolated PostgreSQL records, not the working inventory.

### 5. Backend / API behavior

Fulfillment values are pickup, seller_delivery or blank for historical/legacy-client data. Stored statuses and payment choices are unchanged. Delivery events and payment updates are separate requests. The new route adds a missing seller progress capability, not a delivery subsystem.

Order GETs now require authentication before exposing destinations: administrators use existing scoped permissions; mobile buyers match their actual buyer ID plus saved email, protecting ambiguous legacy Django/mobile ID namespaces. Anonymous reads return 401. Modern fulfillment POSTs are buyer-bound before idempotent replay. Legacy POST clients omitting fulfillment retain the previous contract and create unclassified records; the prior legacy-write authentication weakness is not claimed as fixed and remains separate work. They cannot create Seller Delivery without the authenticated new method contract.

### 6. Database / migration impact

**Migration api.0048_order_fulfillment was applied only to the approved local development database.** It adds four columns. No historical fulfillment, destination, delivery/receipt dates, payment, order status, stock or opening balance was fabricated. Django was paused during activation and restarted with FIFO enabled.

A fresh custom backup was catalog-checked, restored successfully into a disposable local database and used to rehearse 0048. Existing values in nine inventory/FIFO/order/bundle tables matched before/after. Backup: `backend/backups/orders-before-fulfillment-20261025T062613Z.dump`, 227167 bytes; SHA-256 `6fde678d1082eab6af05528d29eed90ac90159a3dc3d684d095324687e70052c`; verified manifest beside it. Working activation verified the same baseline before/after. Totals remain **1 order, 14 batches, 344 available and 1 reserved unit**; the historical order's method stays blank.

An initial helper comparison used different session timezone text; direct read-only checks confirmed all nine original hashes unchanged, then the helper standardized UTC. An initial clone rehearsal held a reader transaction blocking its own DDL; only that helper/disposable database was stopped/removed and the clone connection corrected to autocommit. Neither issue migrated, restored or rolled back working data. The final backup/restore/rehearsal passed. Never restore the backup automatically over newer transactions.

### 7. Tests performed — actual results

- **72 targeted Django tests passed in 13.179s**: new fulfillment cases, existing mobile seller workspace, Orders, FIFO, real PostgreSQL concurrency and inventory report accuracy.
- **192 broader Django tests passed in 59.815s**: overlapping targeted coverage plus inventory/threshold/variant/bundle/academic/product-validation/sales/export/facility regressions. Do not add overlapping counts as distinct tests. Django checks reported no issues.
- **29 Flutter tests passed** across fulfillment transport/widgets, summary, checkout layout and seller workspace. Includes stable authenticated retry, no automatic POST failover, actual destination callback, seller confirmation at 320/844px and checkout enlarged-text layouts. No test transaction reached working records.
- Chromium: **1722/1722 checks across 63 renders** at seven widths 320–1920px; **84/84 pagination checks**; **11/11 existing action checks**; **246/246 delivery checks across 24 renders** at six widths. Delivery checks verify Delivered/Unpaid, no cancellation, explicit completion payment and no invented pickup time. All browser writes intercepted. Desktop/mobile screenshots inspected.
- Changed-file Flutter analysis: No issues found. JavaScript syntax and scoped whitespace checks passed. Migration consistency: No changes detected.
- Actual local authenticated Orders/list/details/fulfillment filters and all three inventory sections returned HTTP 200; anonymous order GET returned 401. Read-only checks match original data and protected inventory/FIFO control flow while allowing approved model/API/route/schema changes.
- Android debug APK built successfully: `campushub/build/app/outputs/flutter-apk/app-debug.apk`. No physical-device installation, production deployment or live delivery/payment demonstration was performed.

Test corrections included missing isolated academic seeds, accidental discovery of imported TestCase classes, a legacy fixture's default completion time, assertions for the removed disconnected COD selector and matching the real bounded seller viewport. Those were test/harness corrections, not FIFO changes. Readable Flutter screenshots load bundled fonts; currency glyph fallback in the test raster is not physical-device verification.

### 8. Limitations, troubleshooting and safe exercise

Cash remains the existing recording workflow; Seller Delivery does not imply COD or Paid. Delivered/unpaid intentionally holds reservations until paid completion. No Returns/Refunds or delivery integrations exist. Legacy unknown fulfillment is not converted automatically. Rebuild/install the new Flutter client to select methods; the APK was built but not installed here.

Retry drafts/keys survive within the current checkout screen only. After leaving/restarting an unresolved checkout, inspect actual orders before a new submission; persistent cross-session reconciliation is not implemented. Drafts remain locked for retry after an unconfirmed submission. Bulk checkout remains separate line orders, not a new multi-seller parent order. The prior rejected-completion Escape/focus limitation remains; use the visible Cancel control. No physical handoff, cash collection, production or full screen-reader certification is claimed.

Troubleshooting: check showmigrations and the approved deployment process if another environment lacks 0048; do not rerun FIFO initialization or bypass guards. Not recorded is correct for unknown history. Check sign-in/approval/scope on 401/403; another seller's ID should return 404. Delivered should retain Unpaid until actual payment is confirmed. Current web assets use 20261025-seller-delivery.

Safe learning exercise: use the isolated targeted runner (`backend/core/venv/Scripts/python.exe scratch/seller-delivery/tests.py targeted`). On an isolated copy, receive two batches, place a delivery order, advance the approved owner's processing/delivery steps and inspect Delivered + Unpaid, no revenue and unchanged reservation. Verify cancellation is blocked after delivery. Explicit paid completion must consume allocations once. Cancel a separate undelivered order to verify original-batch restoration. On the working app, practice with read-only filters/Details until a deliberate real transaction is intended.

## October 25, 2026 — approved Orders presentation refinements

This is the current implementation report. It supersedes older visual notes below about centered quantities, the red Cancelled exception, larger KPI icons and the fraction-only pager. Existing transaction workflows and the original implementation history remain documented below.

1. **Cause / reason.** The four KPIs, ten table columns, combined server filters, 300 ms search debounce, ten-row server pagination, eye action and separate payment values already existed. Confirmed gaps were plain-text Order IDs; centered quantities; blanket `overflow-wrap:anywhere` under a fixed table layout; a larger gold-outlined Pending icon; a `1 / 1` pager that omitted unavailable directions; the old web gold token; and Details controls that depended on order status without checking the existing management permission. The seven-column filter grid could also become too wide for the available laptop content area before its old 1280px breakpoint. No order/FIFO correctness defect requiring backend changes was found in the approved scope.

2. **Exact files changed / current lines and code anchors.** Paths are relative to the repository root.

   | File | Current line / anchor | Change and expected behavior |
   | --- | --- | --- |
   | `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html` | 12/418, asset versions; 15, `data-can-manage-orders`; 154, `order-id-link`; 182, eye label; 209, pager | Add navy Order ID links to the existing named route/deep selection; expose the existing management permission for UI visibility; identify each eye action; render `< Page X of Y >` with disabled boundaries. |
   | `backend/static/components/css/admin_orders.css` | 4, gold; 12, KPI card; 15, icon; 43, table; 49, row spacing; 51, ID link; 58, quantity; 66, statuses; 78, pager; 114, filter breakpoint | Standardize branding, borders and typography; remove KPI minimum height; use 44px icon containers; keep numeric cells intact/right-aligned; limit wrapping to text; keep scrolling inside the table; make filters fit laptop layouts. |
   | `backend/static/components/js/admin_orders.js` | 2, `canManageOrders`; 45, `detailTrigger`; 201/204/227/233, Details visibility; 455, delegated details click | Reuse the existing Details modal for ordinary link/eye activation, restore trigger focus on close, retain modified-link navigation, and hide editing controls from view-only administrators. Existing action request payloads and processing handlers are unchanged. |
   | `backend/core/modules/marketplace/test_orders_admin.py` | 22, academic setup; 236, combined links/pagination; 271, header authorization; 276, view-only access | Make isolated academic setup self-contained; add meaningful navigation/filter/permission regressions and export actual isolated pages for browser checks. |
   | `docs/orders-module.md` | 3, this report | Record cause, functions/data flow, changes, actual verification, troubleshooting, practice and limitations. |
   | `CAMPUSHUB_CONTEXT.md` | 3, current Orders entry | Preserve the current accepted behavior and test evidence for later tasks. |

   QA helpers and evidence are under `scratch/orders-polish/`: `tests.py`, `safety.py`, `browser.cjs`, `navigation.cjs`, `actions.cjs`, `error-focus.cjs`, `live-readonly.py`, isolated HTML exports, screenshots, logs and JSON results. They are not new application modules. Other existing workspace changes were preserved.

3. **Changes made.** The same four KPI cards retain real matching counts and their existing status-filter actions. Their meaningful active border and `aria-pressed` state remain; all icon outlines now match, with gold retained as the Pending icon color. Card height follows content, with consistent 16px padding and 44px icon containers. The table retains all ten columns, uses 12px vertical cell padding, and right-aligns quantities and monetary values with tabular digits. Intrinsic column sizing and a contained 1200px minimum table width protect IDs, badges, dates and numbers; long customer/item/receipt text can wrap. This minimum width controls horizontal scrolling, not card height.

   Existing status definitions remain unchanged. Completed/Paid use navy, pending/ready/unpaid retain gold accents, and Cancelled uses a neutral outlined treatment; visible text still identifies every state. Web gold is `#FCB316`, borders use `#E8EAF0`, and typography reuses bundled Inter. No chart, KPI, table column, date filter or action was added. Existing filters still apply automatically and reset the page. Only their laptop layout breakpoint moves from 1280 to 1440px; existing KPI/tablet/mobile breakpoints remain. Previous/Next are compact 36px controls with accessible labels, visible focus and disabled boundaries; the existing record count remains on the left.

4. **How it works — functions, inputs, outputs and data flow.** The unchanged `admin_orders_page` passes the user and GET parameters to `orders_page_context`; the existing `admin_order_queryset` supplies authorization, `filter_orders` intersects selected filters, and `Paginator(..., 10)` selects the page. The template uses the existing order values and `query_without_page` for pagination. No extra data query or API was introduced.

   Order ID links combine the existing `admin_orders_page` named route with Django's built-in `querystring` tag. It preserves current GET filters, removes `page`, replaces `order` with the actual selected primary key, and carries `orders_tab_token` as `__at`, including when authorization originally arrived through the supported header. It does not duplicate existing keys. The backend already intersects `?order=<id>` with the authorized queryset and the existing JavaScript already opens that selected row.

   Ordinary ID/eye clicks are handled by the existing delegated `.view-order-action` listener and `openOrderDetail(row)`. The link prevents unnecessary navigation for an ordinary activation, so the current filter/page/scroll context remains. Modified clicks retain native link behavior. `detailTrigger` remembers the activating control for focus return after Details closes. The template's `data-can-manage-orders` comes from `perms.accounts.can_manage_orders`; `openOrderDetail` combines that boolean with the existing status/payment tests to show or hide processing, cancellation, completion and receipt-edit controls. Read-only receipt/status information remains visible. This flag is presentation only: the existing backend permission remains authoritative even if a client changes its DOM.

   Example: a Ready for Pickup / Unpaid order continues to display Unpaid. A view-only administrator can open its ID or eye and read Details, but sees no processing/payment controls. A manager retains the existing collection/cash confirmation workflow. No display change marks the order Paid, reserves stock again, or alters the order's status.

5. **Backend / API behavior.** No Django view, service, API, route, permission rule, status definition, revenue calculation, payment workflow or inventory function changed. The same order-update endpoint retains its existing permission, transaction, lifecycle, pickup/cash confirmation and cancellation checks. Source comparison confirmed unchanged JavaScript request-body expressions; intercepted browser checks confirmed the original Processing, Cash on Pickup completion and cancellation payloads. FIFO allocation, bundle recipes, variant identity, completion handling and exact cancellation restoration are covered by the existing isolated regressions, without source changes in those modules.

6. **Database / migration impact.** None. No model, migration, schema change, activation/cutover, opening balance, working order or stock write was performed. Test receipts/orders were created only in PostgreSQL's isolated test database. Working-database safety checks ran under `SET TRANSACTION READ ONLY`, matching the before/after counts and hashes of nine inventory/FIFO/order/bundle tables, migration history, configuration and the protected backend source/control flow. Actual local totals remain **1 order, 14 batches, 344 available units and 1 reserved unit**; the existing reservation is unchanged. The local Django helper was restarted to load the new source/templates, retaining active FIFO and the writable local configuration. Normal authenticated GETs may update their existing session heartbeat; none submitted a transaction.

7. **Tests performed — actual final results.**

   - `backend/core/venv/Scripts/python.exe scratch/orders-polish/tests.py targeted`: **51 tests passed in 7.202s**, covering Orders filters/snapshots/details/lifecycle/permissions, FIFO and PostgreSQL concurrency, and inventory report accuracy.
   - `backend/core/venv/Scripts/python.exe scratch/orders-polish/tests.py regression`: **171 tests passed in 43.984s**. This overlapping broader run adds inventory monitor, thresholds, variants, bundles, academic inventory, product validation, sales/report exports and facility revenue. Both runs reported no Django system-check issues. These are not 222 distinct tests.
   - `node scratch/orders-polish/browser.cjs`: **1386/1386 checks passed across 49 renders** at 1920, 1440, 1366, 1024, 768, 390 and 320px, using actual isolated Django pages for populated, filtered, empty, custom dates, view-only and two paginated states. Checks cover contained horizontal scrolling/no page overflow, intact cells, right alignment, KPI borders, readable controls, ID/eye selection, keyboard focus return, modified-link handling, actual payment display, safe snapshot text rendering, view-only controls, filter debounce/combination and confirmation-checkbox behavior. Desktop/mobile screenshots were visually inspected.
   - `node scratch/orders-polish/navigation.cjs`: **84/84 checks passed** at 1366/390/320px. Actual rendered 10+1 record pages preserve search, statuses, Program/Major, custom dates and tab authorization; native Next and keyboard Previous work, row numbering continues, and boundary controls disable correctly.
   - `node scratch/orders-polish/actions.cjs`: **11/11 checks passed** for the existing step/completion/cancellation payloads, acknowledgement gating and retry controls after rejection. **All three POSTs were intercepted**; no browser transaction reached the working database. Error dialogs were dismissed using their visible Close/Cancel controls.
   - `live-readonly.py`: actual authenticated local list, selected Details and reference Search all returned **HTTP 200**; management visibility, current assets and the existing real order were verified. Literal action-payload expressions match the saved pre-change JavaScript. `safety.py after` matched the pre-change working-data/source snapshot.
   - `node --check backend/static/components/js/admin_orders.js` and scoped `git diff --check` passed.

   During verification, the reused test database lacked academic seed rows; the existing test class now creates its own isolated Program/Major fixtures. The new authorization test was corrected to use the token helper's real string return value. FIFO and Orders exports originally shared generic QA filenames; FIFO exports are now disabled in this Orders QA runner so they cannot overwrite Orders pages. The final link now explicitly includes its named route before the generated query string, which made direct route verification reliable while preserving header-supplied authorization. Browser harness selectors and modal transition/dismissal waits were corrected rather than changing order workflows to satisfy tests. The final results above followed those corrections.

8. **Remaining limitations / troubleshooting / safe practice.** No new blocker was found in the approved list/filter/navigation scope. A confirmed **pre-existing keyboard recovery limitation** remains after a rejected completion request: disabling/re-enabling the confirmation button leaves focus on `BODY`, and Escape does not dismiss that action dialog until focus returns inside it. The visible Cancel control works. `node scratch/orders-polish/error-focus.cjs` reproduced this with both the saved original JavaScript and the current script, after waiting for transitions; evidence is in `error-focus-results.json`. This task leaves the processing/error handlers unchanged. It does not affect the verified normal Details Escape/focus-return behavior, backend permissions or inventory correctness.

   There are currently only one-page results in the working database; multi-page behavior was verified with real isolated PostgreSQL records, not by inserting working demonstration orders. Legacy Completed / Unpaid records, where present, deliberately remain Unpaid; this UI does not repair historical payments. No full screen-reader certification was performed.

   Troubleshooting: refresh after the local server restart if old styles persist; current CSS/JS versions are `20261025-orders-polish`. Check all selected filters when a known order is absent; a mismatched filter should produce an honest empty state. Verify `can_manage_orders` if Details is read-only, rather than bypassing authorization. Horizontal movement belongs inside the table region, never the whole page. If an action returns an error, use the existing Close/Cancel control and inspect the actual backend response before retrying; do not assume the operation succeeded.

   Safe practice exercise: search for a real order ID, open it with Enter and compare its saved Order Status and Payment Status. Press Escape and verify focus returns to that ID. Repeat with the eye action. Change a dropdown and verify the URL/results preserve other filters while resetting pagination; use Clear Filters to restore the unfiltered view. Check the disabled pager on a one-page result. These steps require no order update or stock operation. To learn FIFO/completion/restoration behavior, run the isolated targeted suite instead of creating demonstration transactions in working inventory.

Current October 24, 2026 dashboard integration: Super Admin Recent Orders has a separate nine-column overview table, documented in the [dashboard implementation guide](dashboard-analytics-operations-update.md). Its Order ID and View Details links reuse this module's `/admin-orders/?order=<id>` selection and existing authorized details modal. `filter_orders(queryset, params)` intersects that ID with the already authorized queryset; `openOrderDetail(row)` displays the resulting authorized row. No Orders-page template, processing action, scope or payment workflow changed. The dashboard's `recent_marketplace_orders` helper adds read-only seller/unit-count presentation from existing snapshots and owners; unowned legacy multi-item arrays are labelled honestly. This integration does not create a parent multi-seller order schema. The functions, data flow and safe read-only verification exercise below remain applicable.

Updated 2026-10-08. This guide covers the existing Super Admin / authorized marketplace-admin Orders page. It does not replace checkout with a new order architecture or insert demonstration orders into the live database.

## 1. Cause / reason

Confirmed issues in the inspected implementation:

- The page loaded every authorized order, then JavaScript searched and paginated locally. KPI cards remained global while rows changed.
- Program/Major, Previous Month and Clear Filters were missing. Filters and pagination were not preserved in the URL.
- GET requests regenerated older order references if they did not match the current year-specific code format. This could change historical references simply by opening Orders.
- Details inferred payment from completion (`paid || completed`) rather than the stored payment status. It also invented fallback pickup schedules and payment recorder text.
- Status updates cleared omitted receipt/pickup fields and could revert recorded payment. Completion lacked a separate collection acknowledgement.
- Row menus crowded the table with operational actions. The stylesheet contained repeated rules, green states and unrelated action styles.

The update keeps the page for transactions, pickup and payment monitoring. UI/UX Pro Max guidance was used for contained responsive tables; CampusHub's existing Products / Inventory design determined card dimensions, typography and spacing. The October 25 refinement above supersedes the original muted-red exception: Cancelled is neutral outlined and Completed/Paid use navy, following the current web branding rules.

## 2. Exact files changed: current lines and anchors

| File | Line / nearby code anchor | Added, changed, moved or removed |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/orders.py` | 19, `filter_orders` | New read-only helper for combined search/status/payment/program/major/date filters and validation. |
| Same service | 108, `order_items`; 153, `decorate_orders`; 187, `orders_page_context` | Read transaction snapshots, batch buyer/SKU/history data, aggregate matching KPIs and paginate ten rows. No stock calculation. |
| `backend/core/modules/marketplace/services/order_access.py` | 6, `admin_order_queryset`; 17, legacy JSON guard | Reuse existing seller/product Program/Major authorization; ambiguous legacy multi-item JSON is Super Admin only. |
| `backend/core/accounts/views.py` | 323, `admin_orders_page` | Delegate the Orders GET to the new helper. Preserve tab authorization and provide real master/status options. Remove GET-time code regeneration. |
| Same views file | 837, `admin_order_update`; 907, `pickup_confirmed`; 957, receipt metadata | Validate payloads, acknowledge pickup, preserve omitted metadata, prohibit unpaying recorded payments and new payments on cancelled orders. Existing transitions and inventory helpers remain. |
| Same views file | 1027, `log_account_activity` | Log actual status/payment changes using the existing account audit service, alongside the existing order status history. No secrets in action text. |
| `backend/core/api/models.py` | 840, `MarketplaceOrder.save` | Generate the current format for new/unassigned orders; preserve populated historical references on later updates. No field changes. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html` | 23, `order-stats-grid`; 58, `ordersFilters`; 199, `ordersEmptyState`; 208, pagination | Retain four KPIs and ten columns; add labeled auto-filters and true empty states; move operational actions from rows into Details. Update Orders CSS/JS cache version. |
| Same template | 242, pickup checkbox; 326, Seller / Program; 335, Order Items; 360, Items Subtotal | Details now separates buyer and seller academics, adds exact SKU and collection timestamp, shows captured prices/subtotal/final total, and requires collection plus cash acknowledgement in the completion dialog. |
| `backend/static/components/css/admin_orders.css` | 12, KPI grid; 27, filters; 44, table; 59, statuses; 112, mobile header | Replace repeated page rules with compact styles matching Products / Inventory. Keep a contained wide table, 44px controls, restrained statuses and Orders-only narrow-header fitting. |
| `backend/static/components/js/admin_orders.js` | 134, `renderOrderItems`; 155, `openOrderDetail`; 249, modal switching; 256, completion button | Safe text rendering, true payment display, appropriate operational controls, separate acknowledgement checks and sequential modal transitions. |
| Same JavaScript | 450, GET filters; 455, `submitFilters`; 463, `syncDates` | Remove client-only filtering/pagination; debounce search 300ms, auto-submit selects, validate custom dates, update major applicability and expose selected KPI state. |
| `backend/core/modules/marketplace/test_orders_admin.py` | 1, module docstring; 19, `OrdersAdminTests` | New isolated tests for scope, snapshots, filters, dates, counts, confirmation, history, stock and browser exports. |
| `backend/core/accounts/tests.py` | 588 / 628, `pickup_confirmed=True` | Existing workflow tests now explicitly acknowledge collection during completion. |
| `backend/core/modules/marketplace/test_inventory_monitor.py` | 140, completion payload | Existing movement test explicitly confirms collection; its inventory assertions are preserved. |
| `scratch/orders-review/check.cjs` | 1, actual Django HTML verification | Chrome verification against exported actual templates/CSS/JS and local Bootstrap. Test-only artifacts. |
| `docs/orders-module.md` | 1, this guide | Implementation, data flow, troubleshooting, learning exercise and required report. |
| `CAMPUSHUB_CONTEXT.md` | 3, latest Orders reference | Save this accepted behavior for future changes. |

Other dirty files already in the workspace were preserved. The shared academic controls, checkout, bundle reservation, stock deduction, dashboard layout and report logic were inspected/reused rather than duplicated or redesigned.

## 3. Changes made / requested behavior

| Requested area | Final behavior |
| --- | --- |
| KPIs | Total Orders, Pending, Ready for Pickup, Completed. All four count the complete matching authorized dataset before pagination. Total includes the separate Cancelled branch; Completed counts only `completed`. |
| Table | `# / ORDER ID / CUSTOMER / ITEMS / QTY / TOTAL / ORDER STATUS / PAYMENT STATUS / ORDER DATE / ACTIONS`. Names left, quantity and currency right with tabular digits. |
| Ownership | Items' second line shows saved seller name and current effective Product/Seller Program-Major. Details has its own Seller / Program section. |
| Items / QTY | A single current order stays one purchased product; bundles stay one purchased bundle. Legacy saved item arrays show first name plus additional-item count and sum item quantities, not distinct product count. |
| Filters | Search, Order Status, Payment Status, Program, Major, Date, Clear Filters. No Apply button. Search debounces 300ms; selections submit immediately. |
| Program / Major | Real `Department.is_program` and linked `ProgramMajor` records. IA/HE/ICT are majors under BTLED, never standalone programs. Nonapplicable Major is disabled and labeled Not Applicable after selecting BSIT/BFPT. |
| Dates | All Dates, Today, inclusive Last 7 / Last 30 Days, This Month through today, Previous Month, Custom Range. Both custom dates are required and validated. |
| Order Status | Existing `pending -> processing -> ready_for_pickup -> completed`; eligible active states can cancel. Terminal orders cannot reopen. |
| Payment | Existing independent `unpaid / paid`; never derive Paid from Completed. Receipt metadata alone does not confirm payment. |
| Actions | Only View in the table. Start Processing / Ready for Pickup / Complete / Cancel are exposed in Details according to actual current state. No Delete action. |
| Details | Stored order reference/date/status, buyer identity/academics/contact, seller academics, product/variant/SKU/qty/unit price/subtotal, subtotal/final total, pickup state and recorded timestamps, payment record and real history. |
| Empty states | Empty authorized dataset: No orders found yet. Existing authorized orders filtered away: No orders match the selected filters, with Clear Filters. Validation errors also show their specific message. |
| Pagination | Ten rows per page, newest `created_at` then primary key descending. Query values, including tab authorization, are preserved between pages. |
| Design | White, navy and gold; same 100px minimum KPI height, 52px outlined icon container, 8px radius, 18px/20px padding, 2rem value and 16px spacing as existing Products cards. Cancelled uses the requested muted red without a large badge. |

## 4. How it works: functions, inputs / outputs and data flow

The read path is:

```text
GET /admin-orders/ with query parameters
  -> admin_order_queryset(user): authorized Product/Seller ownership
  -> filter_orders(queryset, params): all filters combined with AND
  -> aggregate Count(): matching totals for every KPI
  -> Paginator(..., 10): only one page of rows
  -> decorate_orders(): batch identities, academic labels, SKUs and history
  -> Django template: table, true empty state and pagination links
  -> admin_orders.js: opens Details and submits later filter requests
```

`filter_orders` receives an already authorized queryset and GET values, and returns a filtered queryset, selected values and a validation message. Authorization is applied first: choosing another program can produce no results, never expand permission. Product's own Program/Major takes priority; the seller supplies the inherited scope only when the Product has no assigned program. Customer Program does not control seller-side access.

Search uses case-insensitive stored references/customer/product names, saved legacy item names and persistent inventory SKU identities. Blank legacy customer names can use existing buyer records. SKU matching uses the registry's real prefix/variant/sequence format in SQL; exact variant selections are required for a variant SKU. A second variant's SKU must not match the first variant's purchased order. Legacy item-name search deliberately does not search item prices or quantities.

`order_items` accepts a stored order and outputs dictionaries for the Details table. It reads saved unit prices, quantities and subtotals, never current Product.price. When a single-row subtotal is not separately stored, it uses the captured `order.unit_price * order.quantity`. Final Total always remains `order.total_price`. A stored bundle component recipe is for inventory consumption, not additional purchased items.

`decorate_orders` works on one page and queries buyer namespaces in batches. If a legacy numeric ID exists in both web/mobile namespaces, a saved matching email resolves it; ambiguous identities do not disclose another account's contact or academics. Missing data stays Not recorded / Unassigned. Related Product/Seller Program/Major, SKUs and status history are selected/prefetched; queries do not grow per rendered row.

For the frontend, `submitFilters()` receives control values and submits the existing GET form. Program changes reuse `CampusHubAcademic.sync()` and reset an incompatible Major. Custom date selection exposes two inputs and waits for both dates. Pagination remains backend-generated, so the table and counts cannot disagree because of browser-only filtering.

`renderOrderItems()` creates cells with `textContent`. This makes a product name containing HTML characters appear as text rather than execute as markup. `openOrderDetail()` takes one rendered authorized row and displays its real metadata. `switchFromDetails()` waits for Bootstrap's hidden event before showing another modal, preventing overlapping backdrops.

The write path is:

```text
Details action + CSRF-protected POST to the existing admin_order_update route
  -> existing permission and Program/Major query, locked in a transaction
  -> transition / payment / pickup validation
  -> existing cancellation restoration or completion movement helper
  -> save actual order fields
  -> existing status history + actual account audit event
  -> refresh the same filtered Orders URL
```

Completion checks:

- The browser requires both Buyer has collected the order and Cash payment received.
- The payload sends boolean `pickup_confirmed: true` and `cash_confirmed: true`.
- The backend requires collection acknowledgement plus valid payment confirmation. An already recorded Paid transaction can complete with explicit collection acknowledgement; existing staff payment recording via an explicit Paid update is preserved.
- For compatibility, the earlier combined boolean `cash_confirmed: true` represents Cash on Pickup collection/payment acknowledgement when `pickup_confirmed` is absent. An explicit false collection value is always rejected. Strings such as `"false"` are not treated as true.
- Receipt-only editing does not create payment. Missing payload fields preserve saved metadata. Existing paid timestamp/recorder and completion/collection timestamps survive later receipt edits.

Inventory remains the original source of truth. Checkout already reduces saved Available and records a hold; it is not deducted a second time on completion. Completion uses `record_completed_sale` to finalize physical On Hand movement. Cancellation restores the exact saved selections or purchased bundle component snapshot, once, using `inventory_restored` protection. No stock arithmetic was added to this template or service.

## 5. Backend / API behavior

Existing routes are retained:

- `admin_orders_page`: `/admin-orders/`, permission `accounts.can_manage_orders`.
- `admin_order_update`: existing order-ID POST route, same permission and scope. JSON validation returns 400, invalid lifecycle/payment/collection operations return 409, out-of-scope orders return 404, unauthorized users remain denied.
- `marketplace_orders`: existing checkout route; not replaced. One sellable product per order, exact selected options and purchased bundle snapshot remain unchanged.

The existing status history captures status, actor, notes and timestamps. Its ordered display now includes Created from the actual order.created_at. The existing account activity service records status/payment changes with the authenticated actor and order reference. Receipt-only updates do not invent another status-change event.

Multi-seller handling: the current checkout has no parent Order / OrderItem / seller-suborder architecture. No new one was introduced. Ambiguous historical JSON arrays with multiple items have no enforceable item-owner relations, so non-super admins cannot see or manage those records; Super Admin retains their full saved history. A future multi-seller checkout needs explicit per-item ownership/payment/stock design, not a client-side filter.

## 6. Database / migration impact

No new model, field, status, payment method or migration. `makemigrations --check --dry-run` reported No changes detected. No live orders were seeded, deleted, rewritten or completed during verification. Fixtures were created in Django's isolated test database, then discarded.

Actual operational use will update the existing order/status-history/inventory-movement/account-activity records, as intended. A normal Orders GET only reads transaction records. Existing populated historical order references are preserved; new orders retain the existing code generator.

## 7. Tests performed and manual verification

Final checks actually run:

- 128 Django tests passed across the new Orders tests, existing admin workflow/access, variants, bundles, inventory monitoring, Program inventory, Sales Overview and dashboard marketplace suites. System check reported no issues.
- Chrome: seven cases passed at 1440px expanded, 1440px compact, 1024px tablet, 375px mobile, filtered, empty and custom-date states. Checked viewport containment, table cell fit, 44px controls, backend-rendered pagination/rows, true filtered empty state, Details, safe HTML-character rendering, unpaid legacy completion display, collection/payment checkbox gating, debounce, major applicability and custom-date submission.
- Browser POST was intercepted only in the offline fixture to verify acknowledgement payload and visible API rejection. Actual successful/failed database operations were verified by Django tests. No browser POST targeted production data.
- `node --check backend/static/components/js/admin_orders.js` passed.
- `makemigrations --check --dry-run`: No changes detected.
- Targeted `git diff --check` passed.

The first regression run exposed an invalid test fixture code longer than the existing 12-character column. The final model keeps new-code validation while preserving existing historic references; the legacy test now simulates a valid-length saved legacy reference. The first mobile review found the existing header-right group exceeded the viewport; an Orders-only wrapping/shrink rule corrected it. Final runs above passed after corrections.

Manual tests (use a development/test database for stock-changing actions):

1. Ctrl+F5 on Orders. Confirm four familiar KPI cards, labeled filters, the ten requested columns and only View per row.
2. Search an actual order reference, customer, product and exact variant SKU. Wait briefly; verify rows and all four KPI values agree. Search nonsense and check the filtered-results message and Clear Filters.
3. Select BTLED and a real Major. Switch to BSIT/BFPT: Major becomes Not Applicable and cannot keep the old Major value. Try the same URL under an HE admin: IA/BSIT seller orders must remain inaccessible even if the buyer is HE.
4. Test Previous Month and a custom range, including an order on the final day. Incomplete/reversed custom dates must not silently apply.
5. When more than ten orders match, use Next/Previous and reload. Search, statuses, Program/Major/date values must persist; row numbering continues on the next page.
6. Open Details. Verify the captured variant/SKU and prices against checkout, not today's product price. Buyer and seller programs are separate. Old Completed/Unpaid records must still display Unpaid.
7. Use a development order: Pending -> Processing -> Ready for Pickup. Completion must remain disabled with only one checkbox selected. Confirm both only after actual collection/payment; check Paid and recorded times/history.
8. Cancel a development variant/bundle order with a reason. Confirm only the purchased stock pools are restored, once, and the historical order remains. Inspect existing Inventory and dashboard/report results.
9. Test 375px width: the wide table scrolls inside its own keyboard-focusable region without making the entire page wider.

## 8. Remaining limitations, debugging and safe practice

- No true multi-seller parent order schema was invented. Ambiguous legacy multi-item records are deliberately Super Admin only.
- The current Order model has no voucher/discount transaction fields. The page preserves saved subtotal/final-total values without attributing their difference to a fictional voucher. If checkout later saves a discount/OR snapshot, expose that explicit source rather than recalculate old transactions from current products.
- Buyer numeric IDs use separate web/mobile namespaces. If historical identity cannot be reliably resolved, contact/academic details remain unassigned/not recorded. Seller/Product academic ownership shown is the current real relationship; old program membership was not snapshotted by the existing model.
- Exact variant SKU comes from the persistent identity or an explicit stored item SKU; missing retired/deleted identities are not fabricated.
- This is the web Orders module. Flutter UI and a physical Android phone were not changed/tested in this task. Every authenticated live admin page was not opened; browser checks used actual exported Django HTML with the final shared code.
- Production historical records with no pickup/payment timestamps remain honest; opening Details does not backfill fictional dates or payments.

Troubleshooting:

| Symptom | Confirmed design / where to inspect |
| --- | --- |
| Filtered count looks low | `orders_page_context`, line 187: all KPIs deliberately use the selected filters. Clear Filters restores the authorized base, not another program's access. |
| A program admin cannot see an order | `admin_order_queryset`, line 6: inspect Product's effective seller/program/major and whether this is ambiguous multi-item JSON. Buyer Program is not the scope. |
| Completion returns 409 | `admin_order_update`, line 837: inspect lifecycle, boolean pickup acknowledgement and recorded/confirmed payment. Do not force Completed in the browser. |
| Receipt edit changes payment unexpectedly | It should not. Inspect the actual POST and payment_status field, not status badge color. Omitted metadata is preserved. |
| SKU search finds nothing | Check the persisted InventorySKU and saved exact `customization.selections` group/option. Product ID is not SKU. |
| Major remains selected after changing Program | Confirm `admin_academic_controls.js` loads before `admin_orders.js`, and inspect `CampusHubAcademic.sync`. |
| Custom dates do not submit | Both are required, start <= end; inspect native field validity and `submitFilters`. |
| Older design persists | Hard refresh and verify Orders CSS/JS version is `20261008-order-monitor`. |

Small safe practice exercise:

In browser DevTools only, inspect `.orders-filters` and change its gap from `14px 12px` to `18px 12px`. Predict that the vertical separation increases by 4px while filter behavior remains unchanged. Resize to mobile and verify each input still has a visible label and a 44px height. Reload to discard the experiment. If you later edit CSS locally, change one rule at a time, check desktop/mobile, and use `git diff` to confirm only your intended line changed.

Annotated backend example:

```python
stats = filtered.aggregate(
    total=Count("pk"),  # Every matching authorized transaction, before pagination.
    pending=Count("pk", filter=Q(status="pending")),  # Only matching Pending rows.
)
page = Paginator(filtered.order_by("-created_at", "-pk"), 10).get_page(page_number)
# Paginating after counting keeps the KPI from becoming just this page's row count.
```

Learning takeaway: authorization narrows what a user may read; filters narrow what they choose to inspect; pagination controls how much is displayed. Apply these in that order and share the same queryset so UI counts cannot contradict the table.
