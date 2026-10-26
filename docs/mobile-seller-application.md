# Mobile seller application and existing-account product ownership

## Applicant profile pictures and eye-only details action — October 25, 2026

This request supersedes the earlier visible View Application button label. The existing read-only drawer and approval workflows remain.

1. **Cause / reason:** The Applicant cell omitted the linked mobile account's stored `profile_photo`; the action displayed text the user now wants removed. Production catalog media also required a product listing, which would incorrectly hide a pending applicant's photo from an authorized reviewer.
2. **Exact files changed:** `backend/templates/marketplace/pages/admin_sellers.html:57` (`seller-applicant`) adds the stored picture and initials; line67 keeps only the eye with title/record-specific aria-label. `backend/static/components/css/admin_sellers.css:179` styles the 36px round avatar and 44px action. `backend/static/components/js/admin_sellers.js:2` handles missing image files without changing records. `backend/core/core/media_views.py:71` extends the existing profile-image read guard through the canonical Seller Applications scope. `backend/core/core/test_media_views.py:101` tests pending-photo permission/scope boundaries; `backend/core/api/test_mobile_seller_application.py:342` tests real stored URLs, fallback and eye-only accessibility. This guide and `CAMPUSHUB_CONTEXT.md` record the result. Companion Orders files are listed in `docs/orders-module.md`.
3. **Changes made:** Pictures appear beside applicant names without adding a column. A missing photo uses the actual name's first character, or `?` when no name exists. A missing image file hides only the broken image and leaves those initials visible. The eye retains its tooltip, accessible name, 44px target, hover/focus styling and existing drawer behavior.
4. **How it works / functions and data flow:** The existing scoped, paginated `admin_sellers_page` queryset already loads `mobile_user`; the template reads `seller.mobile_user.profile_photo.url` only when a file reference exists. No new view query or identity lookup is added. A tiny existing-script handler listens for image errors, including errors occurring before DOM initialization, and hides the failed image. Production `_is_visible(request, path)` accepts a pending-applicant image only when the requester has existing view/manage-sellers permission and `scope_seller_requests` contains an application linked to that exact stored photo. `catalog_image` retains safe raster extensions, path normalization, local-file checks and private/no-store responses. Existing catalog-visible seller avatars retain their original access rules. No new endpoint is introduced.
5. **Backend / API behavior:** Reuses existing seller read permissions and Program/Major scoping; no roles or permissions are granted. Anonymous/out-of-scope users cannot read a private pending-applicant photo. Approval/rejection, reviewed-record read-only behavior, account types, identities and uploads are unchanged. Django accounts without a stored photo field use initials; another account's picture is never substituted.
6. **Database / migration impact:** None. No stored photos, application records, working inventory or configuration changed. All 12 protected marketplace/inventory fingerprints match before/after. Tests used disposable records and temporary image files.
7. **Actual verification:** **68 tests passed in14.074s** across seller applications, Orders, production media access, profile uploads and Marketplace support. This includes anonymous denial, authorized in-scope pending-photo access, out-of-scope denial and denial after permission removal. **221 browser assertions /30renders/sevenwidths320–1920px** passed for the combined request: real fixture photo URL/loading, initials and broken-file fallback, eye-only text/tooltip/aria-label, unchanged eight columns, row height and keyboard drawer behavior, plus Orders filters. No missing static assets, JavaScript errors or working-database browser requests. Desktop/mobile screenshots were inspected. Django system check and seller JavaScript syntax check passed. Evidence: `scratch/seller-avatar-order-filters/`; reproduce with its `run-tests.py` using `api.test_mobile_seller_application modules.marketplace.test_orders_admin core.test_media_views api.test_profile_photos accounts.test_marketplace_support`, then `node scratch/seller-avatar-order-filters/verify.cjs`.
8. **Limits / troubleshooting / safe practice:** No profile upload control or fabricated photo is added. An absent/unreadable stored file remains initials. When troubleshooting a private photo404, check the actual linked application, nonblank applicant identifier and existing scope/permission; do not broaden public media access. Safe exercise: open a reviewed application with the eye using Enter, then Escape, and confirm focus returns to the same eye. Compare a photo-bearing and photo-less existing row without editing records. For image failure behavior, use the isolated browser fixture rather than removing a working profile file.

## Approved drawer refinement and actual application audit history — October 25, 2026

This section supersedes the older statement that only a latest review can be displayed. The application model stores the latest review, while existing AccountActivity rows can also record application events. The already implemented drawer was preserved rather than rebuilt.

### 1. Cause / reason

The former table-row expansion came from a native `<details>` element inside Product Type; the current template already replaces it with Bootstrap offcanvas. Remaining confirmed issues were an icon-only action, drawer color/font variables scoped only to `.seller-page` even though the drawer sits outside that element, and wording that overlooked existing application-linked audit events. The confirmation timestamp parsing and Manila formatting were already present and have been preserved and tested.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
|---|---|---|
| `backend/core/accounts/views.py` | 282 application-history preparation; 298 `_application_event_rank`; 310 `review_events` | Read only the current authorized page's recorded application events, limit to ten per application, reuse actual audit actor presentation and attach display-only history. |
| `backend/templates/marketplace/pages/admin_sellers.html` | 67 `data-seller-application`; 149 latest-event note; 150 `seller-review-events` | Visible Eye + View Application label, actual event history and consistent Manila event dates. Preserve all eight columns, three drawer sections and existing review forms. |
| `backend/static/components/css/admin_sellers.css` | 2 shared drawer tokens; 42 eye action; 160 `seller-review-events` | Make navy/gold/border/font tokens available to the outside drawer, use a 44px labelled view action and compact event presentation; remove redundant hover-only tooltip CSS. |
| `backend/core/api/test_mobile_seller_application.py` | 321 `test_application_drawer_formats_only_aware_confirmation_dates`; 341 `test_application_drawer_history_is_scoped_bounded_and_read_only` | Verify correct Manila conversion, missing/invalid/naive timestamps, escaped applicant content, per-application event limits, scope and absence of application/audit writes. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md` | This report / latest entry | Document current behavior, actual results and safe verification. |

`admin_sellers.js` remains unchanged: its existing drawer behavior passed browser checks. The inactive duplicate module seller template was not edited. The companion dashboard changes are listed in `docs/dashboard-marketplace-design.md`.

### 3. Changes made

View Application remains in the existing Actions column and uses the existing right-side drawer. It is read-only for both pending and reviewed records. Original Approve/Reject forms remain separate and permission gated. The latest decision/reviewer/date/reason are followed by up to ten actual application events, newest first. Missing actor information says Not recorded; no administrator identity, historical notes or timestamps are fabricated.

### 4. How it works — functions, inputs/outputs and data flow

`admin_sellers_page(request)` takes the authenticated actor plus existing GET search/status/page values. `scope_seller_requests` runs before pagination. The current page supplies at most ten authorized application IDs. `scope_marketplace_activity` then applies the existing audit boundary, including conflicting-resource checks. A PostgreSQL window `RowNumber`, partitioned by recorded application ID and ordered by creation date/ID descending, limits each application's audit output to ten rows. `format_activities(..., scoped=True, include_targets=False)` resolves actual actors in a batch without exposing audit metadata, network identifiers or credentials. Its sanitized action/actor/username/date fields become temporary `review_events`; nothing calls `save()`.

The template renders these values into each existing inert application `<template>`. The unchanged JavaScript selects the matching template on click, clones it into one drawer, and returns focus/scroll on close. Bootstrap supplies overlay positioning, Escape closing and focus containment. At desktop widths the drawer is 440px; at narrow widths it fills the viewport and scrolls internally.

Annotated date example: stored `2026-10-17T19:10:15.650271+00:00` parses as an aware datetime. The existing `{% timezone 'Asia/Manila' %}` block displays **Oct 18, 2026 · 3:10 AM**. The original JSON is unchanged. Invalid or timezone-free historical confirmation strings produce Not recorded instead of silently assuming a timezone.

### 5. Backend / API behavior and identity findings

No new API, approval/rejection operation, account type or permission rule was added. Existing server-side management permission, pending-only decisions, seller ownership and Program/Major scoping remain intact. History is available only for authorized applications on the current page and only for the existing application-event types; unrelated audits are not loaded into this drawer.

Read-only verification of application 3 found applicant `mobile:17` and reviewer `admin:1`, with the same display name but distinct account records. The SELLER_APPROVED event records actor administrator 1; that account currently has `can_manage_sellers`. This does not prove historical permission membership or whether the accounts belong to one person. The existing endpoint lacks an explicit same-account self-review prohibition. No new business rule was introduced; separate approval is required to change that policy. New seller application submission already excludes administrator accounts through the existing service.

### 6. Database / migration impact

No models, migrations, working application/audit records, account identities, stock or environment configuration were changed. All 12 protected table fingerprints match. Real scoped page rendering succeeds in PostgreSQL-enforced read-only transactions. The approval/rejection browser requests were intercepted, and all generated demonstration records belong to the isolated test database.

### 7. Tests performed — actual results

The final targeted run passed **88 tests in 28.664s**; the broader overlapping run passed **311 tests in 127.281s**. The initial targeted run identified an invalid new fixture violating the existing one-active-application constraint and an obsolete Seller Overview assertion; the fixtures/assertions were corrected without changing application constraints or rules.

Browser verification passed **685 assertions across 74 renders at seven widths (320–1920px)**. It checked the correct record in the drawer, unchanged row heights before/open/after, 440px/full-width sizing, navy token inheritance, read-only content, focus containment, Escape, opener focus return, scoped ten-event history, search debounce, automatic status filtering, retained pagination parameters, disabled boundaries and original failed-review recovery. Chart/layout checks cover the companion dashboard. No missing assets or browser JavaScript errors occurred. Both review POST checks were intercepted. An initial browser content-comparison assertion was corrected to compare equivalent text representations (`textContent` on both sides); application code did not need a workaround.

Evidence and reproduction: `scratch/seller-dashboard-drawer-final/run-tests.py`, `verify.cjs`, `live-read-check.py`, logs, isolated HTML and desktop/mobile screenshots. Django system check and existing seller JavaScript syntax check passed. Current Marketplace Admin actors 9 and 14 render both pages with status 200 under read-only transactions.

### 8. Remaining limitations / troubleshooting / safe practice

Only the latest model review has stored notes/reason; older event notes are not reconstructed. The drawer explicitly identifies its latest ten recorded events. Missing audit actors remain unknown, and offset-free confirmation timestamps are not presented as verified local times. This work does not add a self-approval policy or claim historical authorization was independently proven. No human-facing application reference exists, so a new reference format was not invented.

If a drawer does not open, verify the page loaded Bootstrap and that the action's `data-seller-application` matches an existing template ID; do not fetch unscoped applications as a fallback. If drawer colors disappear, check that token declarations include `.seller-details-drawer`, which is outside `.seller-page`. Preserve the active root template path; editing the inactive module duplicate will not affect this page.

Safe practice exercise: use the read-only View Application action, check Applicant Information against the selected row, press Tab to confirm focus remains inside, then Escape to verify focus returns to the same action. Open a second application and verify its content changes without changing either row's height. Run the two named regression tests in the disposable Django test database for timestamp/history changes; never edit working application records to build a demonstration.

## Approved Admin Web Seller Applications Details Drawer Improvements — October 25, 2026

### 1. Cause / reason
Previously, clicking **View Application** expanded an inline `<details>` block directly inside the table's "Product Type" column (`<td>`). Because table rows expand to match their tallest cell and other cells use `vertical-align: middle`, this caused excessive blank vertical space, distorted table alignment, and broke visual hierarchy. Furthermore, `application_data.confirmed_at` was printed as an unformatted raw ISO 8601 string (e.g. `2026-10-17T19:10:15.650271+00:00`), and applicant terms confirmations were not clearly broken down.

The inline expansion was replaced with a right-side **Application Details drawer** (`#sellerApplicationDrawer`) adopting the established CampusHub Inventory drawer pattern (Bootstrap offcanvas-end, 440px wide on desktop, 100vw on narrow viewports). Table rows now remain strictly compact and consistently aligned.

### 2. Exact files and anchors

| File | Current line / anchor | Change |
|---|---|---|
| `backend/core/accounts/views.py` | 282 `admin_sellers_page` display loop | Added read-only display attributes: `display_email`, `confirmed_at_value` (parsed aware datetime), `program_snapshot`, and `confirmation_rows` (terms checklist). No model mutations, queries, or scope changes. |
| `backend/templates/marketplace/pages/admin_sellers.html` | 60 Product Type column; 78 Actions; 106 Drawer container & per-row `<template>` | Replaced inline `<details>` with plain text cell; added 36px eye-icon button with hover/focus tooltip; added `#sellerApplicationDrawer` and per-row `<template id="sellerApplicationDetail{pk}">` with 3 sections; formatted dates with `Asia/Manila` and standard `&middot;`. |
| `backend/static/components/css/admin_sellers.css` | 33 status badges; 40 row actions; 70 drawer styling | Styled `#sellerApplicationDrawer`, 2-column description lists (`dl`), pre-wrapped messages, eye-icon button with accessible tooltip, refined institutional status badges, and mobile-responsive overrides. |
| `backend/static/components/js/admin_sellers.js` | 2 drawer setup; 40 existing filters & reviews | Added Bootstrap offcanvas event wiring: clones row template on open, sets subtitle, traps focus, restores scroll position on close with `preventScroll: true`. Preserved debounced search and review actions. |
| `backend/core/api/test_mobile_seller_application.py` | 340 `test_admin_view_only_application_controls_and_latest_review` | Updated assertion from `'Latest review:'` to `'Review Decision'` and `'Review History'`, and verified presence of `id="sellerApplicationDrawer"` and absence of `<details>`. |
| `docs/mobile-seller-application.md` | Top section | Documented root cause, architecture, data flow, verification results, and safe practice exercise. |

### 3. Changes made
1. **Compact Table Rows**: The Product Type column now renders clean text only. Row height is fixed and consistent.
2. **Accessible View Action**: Actions column includes a 36px eye-icon button (`.seller-icon-action`) with `aria-label`, `data-tooltip="View Application"`, and `aria-controls="sellerApplicationDrawer"`.
3. **Application Details Drawer**:
   - **Section A (Applicant Information)**: Full Name, Username (with Applicant ID fallback), Email, Contact Number, Department, Program (with "Recorded when applying" note), and Course / Section.
   - **Section B (Application Details)**: Product Type, Products Intended, Applicant Message, Date Applied, Seller Terms (checklist: Information Accuracy, Marketplace Rules, Approval Requirement), Terms Confirmed (Manila time), and Status.
   - **Section C (Review History)**: Review Decision, Reviewed By (with admin username), Review Date and Time, Reason / Revision Notes. Unreviewed items display "Not yet reviewed." Drawer is read-only for all applications.
4. **Philippine Timezone Formatting**: Application dates, confirmed timestamps, and review timestamps are parsed and displayed in Manila local time formatted as `M j, Y &middot; g:i A` (e.g., `Oct 18, 2026 · 3:10 AM`).
5. **Applicant vs Reviewer Verification**: Verified via database audit that the matching "Lester Bulay" display name belonged to two distinct accounts (`CampusHubUser` ID 17 and `User` ID 1), confirming no same-account self-approval occurred.

### 4. Functions, inputs/outputs and data flow
1. **View (`admin_sellers_page`)**:
   - Queryset is scoped via `scope_seller_requests(SellerRequest.objects, request.user)` and paginated.
   - For each application in the current page, temporary display attributes are attached without saving:
     - `display_email`: Linked mobile user email, falling back to Django user email or snapshot email.
     - `confirmed_at_value`: Result of `parse_datetime()` on `application_data.confirmed_at`.
     - `program_snapshot`: `program_major` or `program` from snapshot dictionary.
     - `confirmation_rows`: Tuples of `(label, agreed_boolean)` for each seller term.
2. **Template Rendering (`admin_sellers.html`)**:
   - The table renders compact rows.
   - Inside a `{% timezone 'Asia/Manila' %}` block, each row outputs an inert `<template id="sellerApplicationDetail{{ seller.pk }}">`.
3. **JavaScript (`admin_sellers.js`)**:
   - Clicking `.seller-icon-action` triggers `show.bs.offcanvas` on `#sellerApplicationDrawer`.
   - The listener finds the matching template element, extracts `trigger.dataset.applicant`, updates `#sellerApplicationSubtitle`, and uses `replaceChildren(content.content.cloneNode(true))` to mount the details cleanly into `#sellerApplicationBody`.
   - On `hidden.bs.offcanvas`, the body is emptied, the opener button receives focus with `{preventScroll: true}`, and window scroll position is restored.

### 5. Backend / API behavior
No backend business logic, approval rules, or endpoints were changed. POST endpoints `marketplace_approve_seller_request` and `marketplace_reject_seller_request` remain strictly protected by `can_manage_sellers`, `scope_seller_requests`, and `select_for_update`.

### 6. Database / migration impact
None. No schema changes, no migrations, and no existing records were modified.

### 7. Tests performed
1. `manage.py test api.test_mobile_seller_application --keepdb`: **17 passed** in 1.25s.
2. `manage.py test accounts.test_marketplace_support modules.marketplace.test_program_inventory modules.reports.test_dashboard_periods --keepdb`: **64 passed** in 32.18s.
3. Total automated tests run: **81 passed**, system check reported zero issues.
4. Python shell rendering test (`scratch/verify_sellers_render.py`): Verified drawer markup, eye icon button, Manila date-time formatting, 3 sections, and absence of inline `<details>`.

### 8. Remaining limitations and safe practice
- The drawer displays the latest recorded review stored on the `SellerRequest` model; detailed granular events remain in the `AccountActivity` audit trail.
- **Safe Practice Exercise**: To verify date rendering in an isolated environment without modifying live records, run:
  `.\venv\Scripts\python.exe manage.py test api.test_mobile_seller_application.MobileSellerApplicationTests.test_admin_view_only_application_controls_and_latest_review --keepdb`
  Observe that the test passes and confirms that `sellerApplicationDrawer` and `Review Decision` are present in the response while `<details class="seller-application-details">` is absent.

---


## Seller My Products: UI-only management layout - October 19, 2026

### 1. Cause / reason

The user requested a professional seller-management layout matching the supplied reference, explicitly **UI/layout only, no data**. Inspection confirmed that the existing screen already receives owner-scoped workspace products and has local name/category search, approval labels, details navigation, inventory and product/bundle submission flows. Its presentation used a permanent search field and generic label/value cards. The actual Flutter project uses StatefulWidget/Navigator rather than an installed GetX framework; reuse that implementation instead of adding another controller or router.

### 2. Exact files, current lines and nearby anchors

| File | Current line / anchor | Change / reason |
|---|---|---|
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` |56 `_productSearchOpen`,165 `_select`,294 search action,388 `productSearchOpen` | Make the existing shared header search local to My Products; show an X when open, dismiss focus when closed and reset visibility when changing seller destinations. Keep the branded white header, existing menu and notification action. Avoid a duplicate page title when the product pane supplies its fixed heading. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` |24 `productSearchOpen`,50 `_productSearchController`,53 `didUpdateWidget`,64 `dispose`,230 `searchField` | Reuse existing query/filter state and search helper, with one persistent UI text controller. Opening autofocuses the field; closing clears query/controller and removes it. The controller is disposed with the widget. |
| Same file |284 `filterChips`,331 `_showProductDetails`,353 `_productStatus`,358 `_productRow`,527 `_myProducts`,642 `productList` | Fixed Back/My Products/Add row and chips, compact image cards, working three-dot menus, clear no-results recovery and reused bundle-list/details behavior. Product-only solid navy selection keeps other seller filters' styling. |
| `campushub/test/seller_workspace_test.dart` |229 preview captures,389 per-destination search tooltip,473 local search/filter test,554 empty Add-menu test,597 responsive cases | Existing fixture-only previews plus meaningful local-search, X clearing, type/status filters, details/inventory actions, Add callbacks, fixed heading and320dp/landscape2x checks. Existing navigation assertions now expect Add and the scoped Search label. |
| `docs/mobile-seller-application.md`, `campushub/DESIGN.md`, `CAMPUSHUB_CONTEXT.md` |this section / seller-my-products component / latest context entry | Current UI, functions/data flow, verification, limitations and learning exercise. |

### 3. Changes made / expected behavior

My Products retains the shared CampusHub brand/menu/notification header. Its existing search position becomes **Search my products**, rather than global marketplace Search, only while this seller section is active. The page has a fixed Back/My Products/Add row; a compact search field appears beneath it only after tapping Search. The X clears and collapses it. The title, Add and chips stay fixed while rows scroll.

Chips are All, Single, Bundles, Pending, Approved, Rejected and Archived. They are one active filter at a time; the last statuses remain reachable by horizontal scrolling on narrow screens. The first five fit the375dp preview at normal text. Each card uses the existing ProductImage, actual name, plain category/type text, approval label, price, server-provided stock and optional variant count/low-stock status. Healthy stock does not add an In Stock label. Use white/navy/gold and Poppins; retain SugarPie for the shared wordmark. Approval badges follow CampusHub's restricted palette rather than copying the reference's green.

Add opens **Add Single Product** and **Create Bundle Product**. The first uses the existing form callback; the second enters the existing qualifying bundle-suggestions flow. Three dots provide **View Details** and **View Inventory**, both working existing destinations. Do not present unsupported Edit/Delete controls. Empty owned catalogs stay empty with an honest message; no-result searches/filters offer Clear search and filters.

### 4. How it works / functions, inputs, outputs and data flow

`SellerDashboardPage` supplies the current `productSearchOpen` flag to `SellerWorkspaceContent`; it owns only visibility, not a second query. The workspace's existing `_productSearch` string still filters `rows('products')` by name/category, with no new API calls per keystroke. `searchField(..., controller:, autofocus:)` reuses the existing input builder. `didUpdateWidget()` clears the query when the header closes it; `dispose()` releases its UI controller. Example: tap Search -> type Notebook -> only matching owned workspace rows remain -> tap X -> the field disappears and the unqueried rows return. Existing status/type selection is independent of clearing the query.

`_myProducts(context)` returns a fixed heading/search/chip region and an Expanded scrollable list. `productList()` applies the existing query plus the selected type or approval filter, then `_productRow()` presents those records. `_productStatus()` treats an archived flag as Archived even if the old approval field says approved, keeping the visible Approved filter honest. No model status is changed. `stock`, `variant_count`, `quantity_status`, prices and image URLs are displayed from the existing serializer; Flutter does not recalculate inventory.

The card and View Details both call the extracted `_showProductDetails()` with the same saved product fields/components as before. It uses the existing `detail()` route and ProfileDetailScaffold page, not a new details implementation. View Inventory and the Back button use existing onNavigate destinations. Add uses existing onAddProduct/onNavigate callbacks; no product is created just by opening a menu or this screen.

### 5. Backend / API behavior

Unchanged. The existing approved-seller check and authenticated `/api/mobile/seller/workspace/` remain authoritative; its product queryset already limits ownership to the logged-in account. This update does not modify that endpoint, product models, approval rules, permissions or payloads. Other seller sections retain global Search. No new business controller, search endpoint or data source.

### 6. Database / migration / running app

No migration, model, dependency, API, production fixture or database change. No sample products, prices, stock or images were inserted. All preview values come only from existing isolated test fixtures, never production screens. No phone/app/backend/worker launch, reload, restart, APK build or install was performed; the user controls Ctrl+F5.

### 7. Tests performed / results

All14 tests in `seller_workspace_test.dart` passed, including existing bearer-auth/no-write-retry, seller approval/revocation, bundle submission mocks and retained shared Home/navigation. New coverage checks default hidden search, autofocus, exact hint, local matching without a global-search callback or extra workspace fetch, X clearing/collapse, Single/Bundles/Pending/Approved/Rejected/Archived filters, no-results recovery, existing details and inventory navigation, empty-catalog Add callbacks and fixed heading at320dp/landscape with2x text. Three-file Flutter analysis returned No issues found; formatting passed. The new details test initially expected a dialog, but the current helper opens a full page; the test expectation/type reference was corrected before the passing run. Backend tests were not rerun for this UI-only change.

Commands from `campushub`: `flutter analyze --no-pub lib/module_app/screens/seller_dashboard_page.dart lib/module_app/screens/seller_workspace_content.dart test/seller_workspace_test.dart`; `flutter test --no-pub --timeout 45s test/seller_workspace_test.dart`. Optional `SELLER_REVIEW_DIR` generates native widget renders. Inspected final375dp populated/search/empty previews in `scratch/seller-sidebar/my-products-layout/`: seller-my-products.png, seller-my-products-search.png and seller-my-products-empty.png. Checked header hierarchy, compact chips, thumbnail placement, price/stock alignment, vertical dots and empty/search states. Fixtures have no photos, so they honestly use the existing image fallback. The renderer's existing missing peso fallback glyph is outside this change. This is native widget verification, with no browser URL or physical app run.

### 8. Troubleshooting, limitations and safe practice

No physical-phone or real-product write test. Edit/Archive/Delete APIs/forms are not added under the user's UI-only scope. Create Bundle Product continues through the existing suggestions/qualifying-pair workflow; it is not a new arbitrary bundle editor. Empty suggestions remain empty. If Search opens global results on My Products, check the section-specific action in SellerDashboardPage and the productSearchOpen prop. If stock appears unexpected, inspect the existing server response; do not invent a local stock calculation to fill the UI. When filters return no rows, use Clear search and filters rather than seeding records.

Safe exercise: run `flutter test --no-pub test/seller_workspace_test.dart --plain-name "My Products search is local"`. Verify the mock workspace is loaded once, typing filters only its own rows, X restores the unqueried list, and opening details/inventory makes no product write. Then run the empty My Products test to exercise both Add callbacks without creating records. For a layout exercise, temporarily change the thumbnail dimension76dp to68dp, inspect the isolated preview, then restore76dp; keep the48dp menu/search targets and avoid adding sample records to production code.

## Visible Daily / Weekly / Monthly sales selector - October 19, 2026

1. **Cause / reason:** the user asked to replace the icon-only filter with a visible period selection and Daily/Weekly/Monthly options. The previous Home popup showed only a filter icon and initially loaded30days. The shared backend supported seven days and this month but did not recognize a today-only range.
2. **Exact files / current lines / anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:40` `_salesPeriods`,894 `salesPeriod`,927 selected label; `campushub/lib/module_app/screens/seller_dashboard_page.dart:53` `_period = '7'` and existing129 `_changePeriod`; `backend/core/modules/marketplace/services/analytics.py:66` today branch inside `parse_analytics_period`; `backend/core/api/test_mobile_seller_workspace.py:72` Philippine date-boundary test; `campushub/test/seller_workspace_test.dart:545` Analytics option and625 Home period-change assertions; `campushub/test/seller_home_entry_test.dart:38` fixture workspace respects the requested period. Documentation: this guide and `CAMPUSHUB_CONTEXT.md`. The related Home/banner source, asset, tests and DESIGN.md changes are listed in `docs/mobile-services-navigation.md`.
3. **Changes made:** the right-side outlined control now displays its actual selection with a small chevron, starting at Weekly. Options are Daily, Weekly and Monthly. The Sales Analytics dropdown reuses these labels; there is no duplicate period list or separate date calculation in Flutter. Keep the smaller top spacing and no redundant subtitle.
4. **How it works:** Daily sends `period=day` and uses today in the server's configured Philippine timezone; Weekly sends `period=7` and uses today plus the previous six days; Monthly sends `period=month` and uses the first of the current month through today. `_changePeriod(value)` still calls the existing `_load()` and authenticated workspace service. `parse_analytics_period(params, today?)` returns the existing AnalyticsPeriod object: key, label, start and end. Its new day/today/daily aliases return one same-day range. Example: in Asia/Manila on October19, Daily excludes October18 at23:59 while including October19 at00:01, even though both timestamps are October18 in UTC. Revenue/trend use the returned range; other current/all-time KPI meanings remain unchanged.
5. **Backend / API behavior:** reuse `GET /api/mobile/seller/workspace/`, the canonical period parser and existing completed-and-paid owner-scoped sales queryset. No new route, duplicate datetime logic, changed ownership, approval, revenue source or marketplace workflow. Existing30/90/year/custom/etc. parsing/defaults remain available to other callers; only this mobile screen initially chooses seven days.
6. **Database / migration impact:** none. No models, dependencies, migrations or live records were changed. No app/server/worker restart, build or install was performed.
7. **Tests performed:** all37 focused Flutter tests passed and nine-file analysis was clean. Existing seller tests verify default Weekly checked, Daily triggers one request with `period=day`, selection remains checked, Monthly sends `period=month`, and Sales Analytics can select Weekly. All23 Django tests passed using the existing guarded `scratch/mobile-add-product/run_image_tests.py` runner with its named test database and FCM disabled in that test process. The new API regression fixes a local date and checks Philippine midnight, last-seven-day and first-of-month inclusion while excluding another seller's sales. System check reported no issues. Final full-Home and320dp/2x photo previews were inspected.
8. **Troubleshooting / limitations:** no live-phone or live-order verification. Daily means today, Weekly means the last seven days, Monthly means this month; these are ranges, not alternate chart-bucket grouping. If totals do not refresh, inspect the existing authenticated workspace response and selected period rather than editing totals locally. Sparse data honestly stays zero/empty. The server/API default remains30days for callers that omit the period.

**Safe practice:** run `flutter test --no-pub test/seller_workspace_test.dart --plain-name "seller additions share Home and navbar"` from `campushub`. Check the initial Weekly label, choose Daily and confirm the mock receives `day`, then choose Monthly and confirm `month`. The existing isolated backend runner can be run from the project root with `.\backend\core\venv\Scripts\python.exe .\scratch\mobile-add-product\run_image_tests.py`; it validates the date boundaries without touching live orders or sending FCM notifications. Do not seed sales just to fill the dashboard.

## Low Stock Threshold caution: hold and tap - October 19, 2026

1. **Cause / reason:** confirmed that the caution icon's existing `InkWell` only handled `onTap`. Holding it did not open the inline explanation. The user requested hold support in addition to clicking/tapping.
2. **Exact files / current lines / anchors:** `campushub/lib/module_app/screens/seller_add_product_page.dart:453` `_label`,457 `onCautionLongPress`,478 `InkWell.onLongPress`,891 threshold hold callback; `campushub/test/seller_add_product_page_test.dart:253` existing validation test,295 and306 long-press assertions,312 close and subsequent tap assertions; this guide and `CAMPUSHUB_CONTEXT.md` latest entry. Dart formatting also aligned existing line wrapping in the two edited Dart files.
3. **Changes made:** connect a long press to the same gold inline caution. Holding always opens it; a second hold leaves it open. Preserve tap-to-toggle and the existing close button. Keep the explanation below the label and above the input; no floating tooltip or new dialog.
4. **How it works:** `_label(label, field, onCautionLongPress: callback)` takes the existing field/label and an optional gesture callback, and returns the same form layout. Its `InkWell.onLongPress` calls that callback. For Low Stock Threshold, the callback sets `_showLowStockCaution = true` inside `setState`; the existing `cautionWidget` branch renders `_buildLowStockCaution()` with the existing explanation. Example: hold the icon -> state becomes true -> explanation appears. Release and hold again -> state stays true -> explanation remains. Tap toggles the same state; close sets it false. No threshold input value changes.
5. **Backend / API behavior:** unchanged. No request is made by the gesture; the existing threshold validation and eventual product submission remain intact.
6. **Database / migration impact:** none. No dependencies, models, migration or live data changes.
7. **Tests performed:** formatting passed; two-file Flutter analysis returned No issues found. The existing focused Add Product validation test passed with assertions for holding, repeated holding, exact explanation, closing, tap opening/closing, unchanged required validation and zero product POSTs. Command from `campushub`: `flutter test --no-pub --timeout 45s test/seller_add_product_page_test.dart --plain-name "inline validation rejects empty, zero, nonfinite and fractional stock without posting"`. Only this relevant test was run for this follow-up. No app/phone launch, reload, restart, build or installation was performed.
8. **Troubleshooting / limitations:** no new physical-phone verification. If holding still does nothing, check the current `onLongPress: onCautionLongPress` binding and hot reload when ready. Flutter controls the native gesture recognition delay; a quick touch remains a tap. The local UI/UX Pro Max lookup supplied no verified long-press-specific result, so this fix uses the existing Flutter gesture/state pattern as the implementation fallback.

**Safe practice:** run the focused test above; it uses mocked APIs and does not create live products. When ready, open Add Product without submitting, hold the threshold caution icon and verify the explanation stays open after release and another hold. Tap to close, tap to reopen, then use its close button. Keep the threshold value unchanged throughout; leaving the form without submitting writes no product.

## Compact Sales Overview filter and spacing - October 19, 2026

### 1. Cause / reason

The user requested removing the `Total Sales · Last 30 Days` subtitle, placing a filter to the right of Sales Overview and reducing the space above the section. Confirmed: `homeHighlights()` rendered the subtitle plus a separate full-width period dropdown below Suggested Product Bundles. Home also had a24dp wrapper and the heading's20dp top padding. Its `onPeriod` callback was empty, so changing that Home dropdown could not reload sales.

### 2. Exact files, current lines and anchors

| File | Current line / anchor | Change |
|---|---|---|
| `campushub/lib/module_app/screens/seller_workspace_content.dart` |40 `_salesPeriods`,743 `homeHighlights`,745 `seller-sales-overview-header`,894 `salesPeriod` | One list of existing periods; compact48dp outlined filter beside the title; remove subtitle and lower duplicate dropdown. Sales Analytics retains its existing full-width dropdown using the same choices. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` |129 `_changePeriod`,220 `home-seller-sections`,243 and366 `onPeriod` | Reduce Home wrapper top padding24->8dp and connect both presentations to the same existing loader. |
| `campushub/test/seller_workspace_test.dart` |588 shared-Home navigation test,625 `previousLoads` | Extend the existing test: default checked period, selecting7days makes exactly one workspace reload, current selection is retained in the menu, This Month works, bottom navigation remains. |
| `docs/mobile-seller-application.md`, `CAMPUSHUB_CONTEXT.md` |this section / latest context note | Record cause, implementation, verification and safe practice. |

The preceding icon-swap request also changed `dashboard_screen.dart:235,298`, `seller_dashboard_page.dart:286` and existing header tests; see the latest section in `docs/mobile-services-navigation.md`.

### 3. Changes made / expected behavior

Sales Overview now has a small navy outlined filter at the right, with no period subtitle. Opening it shows Last7Days, Last30Days and This Month, with a check beside the selected period. The title can wrap next to the48dp control at large text sizes. The Home wrapper uses8dp top space and this heading no longer adds the generic20dp top inset. KPI cards, bundle suggestions, trend and the remaining seller sections stay in their existing order.

### 4. How it works / functions, inputs, outputs and data flow

`salesPeriod(compact: true)` reads `analytics.period` and returns a tooltip-labelled popup with the current range also exposed to accessibility services. `salesPeriod()` returns the existing Sales Analytics dropdown. Both use `_salesPeriods` and emit the existing period value through `onPeriod`; no dates or revenue are calculated in the widget.

`_changePeriod(String value)` ignores the already-selected value; otherwise it stores `_period` and calls the existing `_load()`. `_load()` rechecks seller access, calls `SellerApplicationService.workspace(period: _period, ordersPage: _ordersPage)` and displays the returned analytics. Example: selecting Last7Days emits `'7'`, the workspace API receives `period=7`, and returned revenue/trend replace the current figures. Current/all-time order cards keep their existing meaning; selecting a period does not invent period-scoped totals for them.

### 5. Backend / API behavior

No backend code or new endpoint. Reuse the authenticated owner-scoped seller workspace API and its existing period calculation, approval guards, loading/error handling and request ordering. Fix only the previously disconnected Home callback; do not change sales, payments, orders, stock or recommendations.

### 6. Database / migration impact

None. No models, dependencies, migrations or live data writes. No app/phone/server/worker launch, reload, restart, APK build or installation was performed. The user controls their running Ctrl+F5 session.

### 7. Tests performed / results

Five-file scoped Flutter analysis returned No issues found. All26 existing focused tests in `dashboard_header_test.dart`, `seller_workspace_test.dart` and `seller_home_entry_test.dart` passed. These cover header order, seller gating, shared Home/navigation, real-shaped fixture data, period callback/reload and320dp/landscape at2x text. The new popup interactions initially produced nonfatal hit-test warnings when tapping the inner Text; targeting the actual CheckedPopupMenuItem removed them, and the affected integration test passed again without warnings. Formatting passed. The375dp fixture render at `scratch/seller-sidebar/compact-sales-filter/seller-overview.png` was visually inspected: title/filter row, no subtitle, no lower dropdown and retained section order. Fixture names/values/images are test-only; the capture's missing peso glyph is a renderer font-fallback limitation, not a live product-data change.

### 8. Troubleshooting, safe practice and remaining limitations

If the old subtitle remains, confirm the current source calls `salesPeriod(compact: true)` inside `homeHighlights()` and hot reload when ready. If the selected range fails to load, use the existing Retry and check the workspace request/response; do not alter database totals to adjust this presentation. The selected range is visible when the menu is open and announced by accessibility services. No new native-phone interaction or live sales verification was performed.

Safe practice: from `campushub`, run `flutter test --no-pub test/seller_workspace_test.dart --plain-name "seller additions share Home and navbar"`. The test uses mocks only. Check that Last30Days is initially selected, Last7Days causes one request with `period=7`, This Month sends `period=month`, and the bottom navigation remains. To learn spacing, temporarily change the Home wrapper's top8dp to12dp, observe the4dp shift, then restore8dp; keep the filter's48dp touch target.

## Mobile Add Product: inline caution container, gradient input outline, and single-row image limits — October 19, 2026

### 1. Cause / reason
The user requested three specific refinements to the mobile Add Product screen:
1. **Inline Caution Container (No Center Floating)**: The Low Stock Threshold caution text must not float to the center in a modal dialog. Instead, tapping the caution icon reveals an inline banner directly between the label and the input field (above the input, behind the label/icon) styled in brand Gold (`#FCB315`) with a clear dismissal control.
2. **Smooth Gradient Outline on Labeled Inputs**: Active/focused input fields should present a subtle, polished gradient outline transitioning smoothly between institutional Navy (`#1A1851`) and Gold (`#FCB315`).
3. **Single-Row Image Specs**: Combine the image format specification and limits into a single, clean institutional line: `Supported: JPEG, PNG, WebP, GIF · Up to 6 images · 5 MB`.

### 2. Exact files, current lines and nearby code anchors
| File | Current line / anchor | Change and purpose |
|---|---|---|
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | `GradientOutlineInputBorder`, `_decoration`, `_label`, `_buildLowStockCaution`, `_images` | Implemented custom `GradientOutlineInputBorder` using a `LinearGradient` from Navy (`#1A1851`) to Gold (`#FCB315`); updated `_label` to position an inline `cautionWidget` between label row and input field; wrapped label row in `Wrap` to eliminate `RenderFlex` overflow on narrow viewports; formatted image support text into a single row. |
| `campushub/test/seller_add_product_page_test.dart` | `caution-Low Stock Threshold *`, `low-stock-caution`, `close-caution-popup` | Verified that caution container is initially hidden, opens inline upon tapping caution icon, and dismisses when tapping close button; verified all field labels and single-row image specifications. |
| `docs/mobile-seller-application.md` | Top section | Documented UX flow, data flow, verification steps, and design system alignment. |

### 3. Changes made / expected UI behavior
- **Inline Caution Popup**: When clicking the caution icon behind "Low Stock Threshold *", an inline card appears immediately below the label and above the input field. It features background `#FCB315`, navy body text ("You will be alerted when your stock reaches this quantity or lower."), an attention icon, and an explicit close icon (`close-caution-popup`). Tapping either the caution icon again or the close button collapses the card.
- **Gradient Outline**: When any text input is focused, its outline renders a smooth 1.5dp linear gradient from Navy (`#1A1851`) to Gold (`#FCB315`) with a 12dp border radius, avoiding generic flat highlights while staying strictly within the institutional palette.
- **Single-Row Image Limits**: The image upload card now displays `Supported: JPEG, PNG, WebP, GIF · Up to 6 images · 5 MB` on a single row below the dropzone box.

### 4. How it works / functions and data flow
- `GradientOutlineInputBorder`: Extends `OutlineInputBorder` and overrides `paint(Canvas canvas, Rect rect, ...)`. It creates a `LinearGradient` across the outer rect from `HomeAppColors.navy` (`#1A1851`) to Gold (`#FCB315`), applies a `RRect` path matching `borderRadius`, and paints the stroke via `canvas.drawRRect`.
- `_label(...)`: Takes `cautionWidget` as an optional parameter. When active, it renders the label row, followed by an 8dp spacer, the caution container, and another 8dp spacer before the child input. A `Wrap(crossAxisAlignment: WrapCrossAlignment.center)` is used for the label and icon to ensure zero overflow on 320dp/360dp screens and large font scalings.
- State variable `_showLowStockCaution` toggles via `setState()` when tapping the caution icon.

### 5. Backend / API behavior
No backend endpoints or payloads were changed. `low_stock_threshold` continues to serialize as an integer in `submitProduct()` payload.

### 6. Database / migration impact
Zero database changes or migrations required.

### 7. Tests performed
- `flutter test test/seller_add_product_page_test.dart`: 11 passed (100%).
- `flutter test test/seller_workspace_test.dart`: 10 passed (100%).
- `dart analyze lib/module_app/screens/seller_add_product_page.dart`: 0 errors / 0 warnings.
- Backend Django API tests: 11 passed (`api.test_mobile_seller_workspace`).

---

## Mobile Add Product: six-image upload and copy — October19,2026

This supersedes the older one-image limitation and copy in the historical full-page form section below.

### 1. Cause / reason

The user requested a shorter Tags placeholder, the heading Upload Images, the admin-style upload box with six image slots, accurate supported formats, and this exact review text: **Your product will be reviewed by the ADMIN before appearing in Marketplace.** Inspection confirmed the mobile form picked one file and its API view saved only image_url. The admin already uses six slots and the canonical persist_product_images helper; Product.image_url already stores a JSON gallery without another model.

### 2. Exact files, current lines and nearby code anchors

| File | Current line / anchor | Change and purpose |
|---|---|---|
| `campushub/lib/module_app/screens/seller_add_product_page.dart` |27 `_maxImages`,39 `_selectedImages`,121 `_readImage`,150 `_pickImages`,290 `_submit` | Keep six local slots, validate a complete selection before changing slots, reuse the installed picker for batch/single replacement and send the selected gallery through the existing submission service. |
| Same file |415 `_imageSlot`,487 `_images`,546 Supported,551 Up to6,736 Enter tags,889 review text | Admin-inspired rectangular upload area with navy upload icon, Tap to browse and six previews; responsive two/three-column slots with accessible replace/remove controls and real selected count; exact requested wording. |
| `campushub/lib/module_app/services/product_service.dart` |185 `submitProduct`,195 `images`,207 payload | Add the optional image list to the same authenticated POST, retaining imageUrl fallback for existing callers. The nullable threshold syntax was aligned with the Dart analyzer without changing its value or behavior. |
| `backend/core/api/views.py` |805 `validate_product_images`,815 legacy-array normalization,851 `persist_product_images` | Accept/validate the gallery before creating anything, save through the admin's existing helper, keep single-image compatibility and enforce the same limit for legacy JSON-array input. |
| `backend/core/modules/marketplace/services/product_images.py` |18 image limits,22 `validate_product_images`; existing persistence now109 | Add one canonical gallery validator; leave the existing image/file writing helper shared with admin. |
| `campushub/test/seller_add_product_page_test.dart` |36 `getMultiImageWithOptions`,389 gallery payload,464 six-image limit,542 invalid multi-selection | Existing form tests updated; add meaningful count/replacement/removal/batch-preservation/actual-payload checks and optional fixture renders. |
| `backend/core/api/test_mobile_seller_application.py` |157 image fixture,171 six images,189 formats/legacy,205 invalid gallery | Real temporary image files and isolated database assertions for count/order/bytes, supported formats, old calls, owner/Pending enforcement and rejected payloads creating no product or file. |
| `scratch/mobile-add-product/run_image_tests.py` |15 `test_name`,20 test runner | Named isolated test database and FCM disabled in this test process only; existing seller regressions included. |
| `docs/mobile-seller-application.md`, `CAMPUSHUB_CONTEXT.md` |this section / latest gallery entry | Current behavior, causes, functions/data flow, verification and safe practice. |

Reference inspected, not modified: `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:247` upload box and346 supported-format helper; `backend/static/components/css/admin_products.css:1800` create-upload-dropzone and1897 navy upload-icon container. Desktop drag/drop copy becomes Tap to browse on mobile; existing admin behavior is not duplicated into another workflow.

### 3. Changes made / expected UI

Tags now says **Enter tags**, with **Separate with commas.** below it. No sample tags are inserted. Existing category, description, price, stock, low-stock threshold, expiry and validation remain.

Images is renamed **Upload Images**. The box matches the admin's white rectangular frame, navy square upload icon and outlined browse cue. Below it are six preview slots, each supporting selection/replacement and an individual remove control. The helper says **Supported: JPEG, PNG, WebP and GIF.** and **Up to 6 images · 5 MB per image.** A live selected count reflects actual form state. The main picker disables at six; existing filled slots can still be replaced or removed.

At normal widths the slots form three columns; narrow content below304dp uses two columns so48dp remove touch targets do not cover the center of the image replacement target. Fields/helper copy can grow with text scaling; the form remains one scroll. The review paragraph is exactly the user-supplied sentence above.

### 4. How it works / functions, inputs, outputs and data flow

`_pickImages(slot?)` is UI state only. With no slot it calls the installed ImagePicker.pickMultiImage using the number of empty slots as its limit. For one remaining slot or an explicit slot replacement it uses pickImage. The Dart layer checks returned count as well because a platform may ignore its picker limit. Cancellation changes nothing. It validates every chosen file into a temporary list before updating any existing slot, so a bad second image does not leave an unintended partial selection or discard previous images.

`_readImage(XFile)` returns one data URL after checking actual JPEG/PNG/WebP/GIF signatures, up to5MiB and encoded dimensions at most20MP. Existing1280px picker resize/85quality settings and bounded ProductImage preview decoding remain. This validation function is shared by batch additions and single-slot changes; there is no second picker-validation path. A failure is shown inline and the form stays editable.

`_submit()` collects nonempty slots in slot order and calls `ProductService.submitProduct(images: list, ...)`. That wrapper calls the existing SellerApplicationService.createProduct once with an images array, or uses the legacy image_url field for older single-image callers. Selecting previews is local; actual network upload happens with Submit for Approval. Seller identity and approval are not accepted from mobile form fields.

`validate_product_images(rawImages)` takes an array and returns trimmed image strings, or raises ValueError before product/file creation. It enforces0–6 entries and valid strings. For uploaded data URLs it checks the allowed format, base64 correctness,5MiB limit, actual Pillow image format/verification and20MP dimensions. Existing media/HTTP image references retain their established pass-through behavior; they are not fetched by this validator. The new validator is in the canonical image module and reaches the view through the existing API compatibility import.

`seller_submit_product` normalizes the new images array and legacy JSON galleries through that same validator. Legacy single-image image_url calls retain their previous persistence path. The view still authenticates the current account, requires an active approved seller, rechecks the locked seller application, assigns the actual owner and creates Pending products for mobile sellers. `persist_product_images` writes each data URL into the existing media upload/products folder and returns its URL. Those URLs are stored as a JSON list in the existing Product.image_url text field. Existing get_image_list and serialize_product expose the full images gallery and first-image thumbnail to current admin/mobile consumers.

Annotated example (illustrative only): a form with two selected PNG files sends `images: ["data:image/png;base64,...", "data:image/png;base64,..."]`. The backend validates both first, then saves two files in order and stores two media URLs on the Pending product. Adding a seventh entry returns400 without a product or image-file write. No new gallery model, endpoint, account or stock calculation is introduced.

### 5. Backend / API behavior

POST `/api/seller/products/submit/` now accepts the optional images array through the existing authenticated workflow. Both new galleries and legacy JSON galleries are limited to six. Existing single-image submissions and bundle callers remain compatible. Images that fail batch validation return400 before product creation; ownership, approval, tags normalization, inventory and audit behavior remain.

The admin's existing helper/model/gallery serialization are reused. No admin form markup, AI image processing, recommendation, payment, booking or chat logic changed. Validation of newly uploaded gallery bytes is server-side as well as client-side.

### 6. Database / migration / runtime impact

No migration or dependency change. Product.image_url already supports JSON galleries, and Pillow/ImagePicker are installed. No live product, seller, image or transaction was created by verification. Gallery files in API tests use TemporaryDirectory, and tests run in `test_campushub_product_gallery`, preserving the real application database. FCM is disabled only inside that test runner process.

No app build/install, ADB, hot reload, server/worker restart or phone-setting change was performed for this update. The user controls the running Ctrl+F5 app and can hot reload when ready. No manual migration command is needed.

### 7. Tests performed / results

- Scoped formatting and analysis of the two changed mobile source files and form test: **No issues found** after aligning the existing nullable-threshold map entry with the analyzer's syntax rule.
- **21 Flutter tests passed** across seller_add_product_page_test and seller_workspace_test. Coverage includes form/input retention, required fields, original single POST/error recovery, copied labels, six-image limit even when the picker returns seven, replacement/removal/reusing the last slot, invalid-batch preservation, cancellation, oversized image, actual images payload and seller navigation.
- **22 Django tests passed** in the named isolated database, including six saved images in the original order with matching bytes, all four supported formats, current owner/Pending status despite forged fields, old single-image and JSON-gallery calls, invalid type/count/base64/content/MIME/size with no product/file creation, plus existing seller/workspace/bundle regressions. The final backend run includes the legacy six-image-limit bypass check. Django system check:0 issues.
- Headless renders at360dp and390dp/1.3x text are in scratch/mobile-add-product/gallery-review. The one-image upload/review and six-image layouts were visually inspected. The selected test PNG is a white1pixel fixture, so white filled thumbnails in these captures are expected, not evidence of broken live images. No native gallery/permission/keyboard check is claimed.

### 8. Troubleshooting, learning exercise and limitations

After the user's own reload, confirm Upload Images is present, browse to intended real images, check the count and use slot remove/replace. Only submit a product when intended; submitted records still need admin approval. If a gallery error occurs, existing fields/selections remain. If an interrupted network POST is ambiguous, inspect My Products before manually retrying; no automatic POST retry was added.

Safe exercise: run `flutter test --no-pub test/seller_add_product_page_test.dart` from campushub. Read the fixture that returns seven images despite the picker limit: verify the UI adds none, then accepts six and submits an array of length6. Run `backend\core\venv\Scripts\python.exe scratch\mobile-add-product\run_image_tests.py` from the project root; expect22 passes using isolated data/temp files. Trace the count from `_selectedImages` through the JSON payload, validator, existing persistence helper and Product.image_url. Change a fixture payload to seven entries to see rejection, then restore it; never experiment against live seller records.

The form draft is still local to this route and is not persisted across OS process loss. Native Android/iOS gallery behavior depends on the installed image-picker implementation; the app-level count guard remains even if a native picker ignores its limit. Supported file types are images only (JPEG/PNG/WebP/GIF); arbitrary PDFs/documents are not advertised as image uploads. Existing remote/media references are not byte-fetched/validated by the new data-URL validator. These tests did not run the user's phone app or exercise a real upload on its network.


## Full-page seller Add Product form - October 19, 2026

### 1. Cause / reason

The attached brief requests one full-screen, continuously scrolling form. The previous implementation opened a bottom sheet, interleaved product/price/category fields, made Description optional, accepted zero/nonfinite prices, used sample autocomplete names and offered only an Image URL field. Its submission wrapper swallowed server errors and displayed a speculative web-panel/auth message. Inspection found StatefulWidget/Navigator and no GetX dependency; this update keeps the actual existing architecture rather than adding a parallel controller/router framework.

### 2. Exact files / current lines / nearby anchors

| Changed file | Current line / anchor | What changed |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | 16, `SellerAddProductPage`; 336, `build` | New presentation for the existing listing workflow: fixed white AppBar, one Form/SingleChildScrollView, Poppins, navy/white, light background,16dp gutters,12dp corners,24dp section gaps and growing controls. |
| Same page | 52, `_validatePrice`; 64, `_validateQuantity`; 165, `_submit` | Required name/category/description, positive finite price with at most2 decimals/eight integer digits, nonnegative integer quantity, guarded POST/loading/error preservation and confirmed-success return. |
| Same page | 98, `_pickImage`; 262, `_images` | Existing installed ImagePicker gallery integration, one image preview/replace/remove, bounded decode through existing ProductImage, image-content/size feedback. |
| Same page | 403, Product Information; 471, Pricing & Inventory; 550, Product Review | Exact requested section order; optional expiry remains within Pricing & Inventory for the existing perishable-category helper. |
| `campushub/lib/module_app/screens/products_screen.dart` | 32, `showAddProductPage`; 60, route settings | Retain actual seller/status/category fetch and replace bottom sheet with `/seller/add-product` MaterialPageRoute. Remove old private form/field/autocomplete helpers and their sample-name imports. Public catalog components stay intact. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 162, `_openAddProduct` call | Center Add Product opens the new page through the same approval entry point; repeated-open guard and success refresh remain. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 344, Add Product callback | My Products opens the same page and retains existing success refresh. |
| `campushub/lib/module_app/services/product_service.dart` | 185, `submitProduct`; 203, response validation | Reuse SellerApplicationService.createProduct, preserve backend error messages and require a product map before reporting success. Existing transport, token and one-POST/no-retry behavior remain. |
| `campushub/test/seller_add_product_page_test.dart` | `one page keeps header`, `single authenticated submission`, `gallery image previews` | Isolated UI/API-contract tests and optional widget captures at360px/390px, enlarged text and keyboard insets. |
| `campushub/test/seller_workspace_test.dart` | `seller additions share Home and navbar` | Existing navigation regression now checks a full page and returns with Back, then verifies the original Home/tab index. |
| This guide; `campushub/DESIGN.md`; `CAMPUSHUB_CONTEXT.md` | latest Add Product notes | Record design, functions/data flow, verification, troubleshooting and limitations. |

### 3. Changes made / expected behavior

The screen has a fixed Back / Add Product header and one vertical scroll in this order: Product Information (Name, real Category, required Description), Pricing & Inventory (Price, Available Quantity, existing optional expiry), Product Images, Product Review, Submit for Approval. Price and quantity stack at narrow widths. The same56dp header, subtle divider,16dp input spacing and readable labels provide a compact institutional form; no wizard, PageView, draggable sheet, Next/Previous or seller selector is introduced. The page is constrained to640dp on wide screens and honors SafeArea/keyboard resizing. Other screens and their color constants are not restyled.

Inputs keep their TextEditingControllers when scrolling, choosing/removing an image, or receiving validation/server errors. Submission/picker work disables competing actions and repeated taps; PopScope protects an in-flight operation. A successful, confirmed product response pops with true, shows a short review message and lets the caller refresh. New mobile listings remain Pending through the existing Django workflow.

### 4. How it works / functions / inputs and outputs

`ProductsScreen.showAddProductPage(context)` awaits current SellerApplicationService.status. Unapproved/failed access shows the existing error and opens no form. Approved status supplies only real `categories`; the route returns bool? so existing callers can distinguish confirmed creation from Back. No hard-coded names/categories are used. An empty category response disables submission and explains how to reopen/retry.

`SellerAddProductPage` owns only local form state. `_validatePrice(text)` rejects blank, zero, negative, NaN/Infinity, excessive digits and excess decimals; `_validateQuantity(text)` accepts0 and whole nonnegative numbers. `_submit()` first checks busy state and Form validation, then calls ProductService.submitProduct with name/description/price/category/stock, optional expiry and image_url. It never sends a seller/owner ID or an approval override. ProductService delegates to the existing authenticated createProduct transport, which sends exactly one JSON POST; a missing product map is treated as unconfirmed, not success. Errors leave fields/images intact and are announced inline. No automatic POST retry is added.

`_pickImage()` reuses the installed image_picker gallery pattern: max1280px sides, quality85 and no full metadata request. Cancellation changes nothing. The mobile listing endpoint accepts a single `image_url`, so the UI supports one selected image rather than silently losing extra selections. JPEG/PNG/WebP/GIF signatures and actual encoded-image dimensions are checked; a5MiB/20-megapixel client guard avoids sending oversized/corrupt content. This guard follows the existing mobile photo-size convention; it is not a claim of new backend validation. The selection becomes a data URL; current `persist_product_image` in Django writes it through the existing product-media path. ProductImage supplies the established bounded preview decoding. Replacing a failed selection preserves the prior valid image; Remove clears local image state only.

The existing ProductItem.isPerishableCategory helper controls expiry visibility. Switching to a nonperishable category clears the local expiry; the backend retains its own category check. The new form is for normal single products, as before; existing bundle recipe/variant/inventory workflows are not duplicated or replaced.

Annotated test-only payload: `name="Test Notebook"`, `category="School Supplies"`, `price="25.50"`, `stock=0`, a nonempty description and optional `image_url="data:image/png;base64,..."`. The mocked response contains a Pending product. Production ownership comes from the authenticated bearer account, not this payload.

### 5. Backend / API behavior

No backend code changed. GET `/api/seller/access-status/` still supplies approval and existing categories. POST `/api/seller/products/submit/` still derives the account from the current token/session, checks active approved seller access, validates the category, locks the application against revocation, assigns mobile_seller internally, creates Pending listings and logs PRODUCT_SUBMITTED. Current stock, expiry, academic ownership, image persistence and review behavior remain. The form does not publish listings, create real bundles or select another seller.

### 6. Database / migration / commands

No model, schema, migration, dependency or production data change. The existing image_picker dependency is reused. No package install, Django command, APK build, app install, ADB, hot reload, restart or phone-setting change was performed. The user's running Ctrl+F5 app is left untouched. Headless widget tests operate only on mocks and test preferences; no real product/photo/order was submitted.

### 7. Verification performed

- `dart --suppress-analytics format` applied to changed Dart files.
- Scoped `flutter --suppress-analytics analyze` over five source files and two test files: **No issues found**, `scratch/mobile-add-product/form-analysis.log`.
- `flutter --suppress-analytics test --timeout 45s test/seller_add_product_page_test.dart test/seller_workspace_test.dart`: **19 passed**, `scratch/mobile-add-product/form-tests.log`. Tests cover360px/390px with1.3x text, fixed header/one scroll/order, keyboard insets, retained values, empty/invalid/finite-positive price/integer stock, categories, approval denial, zero stock, image choose/remove/cancel/corrupt/oversize, single POST/loading, server-error preservation, malformed-success rejection and existing navigation.
- Widget screenshots in `scratch/mobile-add-product/review/` were inspected with bundled Poppins, Material/Lucide icons and a test-only currency fallback font. These are isolated Flutter-rendered captures, not screenshots from the running phone. The selected-image fixture is a one-pixel white PNG, so its white thumbnail is expected. Native gallery/IME/device appearance is not claimed.
- Source layout scan returned `[]`; scoped whitespace check passed. Initial capture helper needed runAsync for engine PNG encoding and the test fonts needed explicit loading; those harness issues were corrected before the final19-test result.

### 8. Remaining limitations / manual verification / troubleshooting

When the user chooses to reload their own session, open Add Product from the center action and from My Products. Confirm Back returns correctly; category choices match the backend; scroll through the exact section order; type a multiline description with the keyboard open; select/replace/remove a real gallery image; submit only an intended real product and confirm it remains Pending. Verify fields remain after an intentional validation error. Current gallery-plugin activation depends on the already installed app build; this update does not restart it.

Only one image is supported by this existing mobile API; multi-image editing needs an explicit endpoint extension. UI image/description/positive-price guards do not replace server authorization or add new global backend restrictions. A network timeout is ambiguous: check My Products before manually retrying, because the server may have saved the listing. Form state survives scrolling/errors within the route, but is not a persisted draft after OS process/activity destruction; no new Android lost-product-image recovery or draft storage is claimed. Current image helper's wider backend acceptance remains unchanged. Actual native keyboard, photo permissions and gallery behavior require a user-controlled device check.

**Safe learning exercise:** Find `_section()` and its bottom24dp padding; compare `_label()` and its16dp field gap. Change only the section gap to20dp in a test branch, run the two headless widget tests above and compare the360px/390px captures, then restore24dp. Trace `_submit()` -> ProductService.submitProduct -> SellerApplicationService.createProduct -> seller_submit_product to see how local fields become a Pending, authenticated-owner product. Do not add a seller ID or approval_status to the payload; the backend owns those decisions. This exercise needs no real product submission or phone restart.

## Exact stroked plus SVG - October 19, 2026

1. **Reason:** The user supplied a new plus SVG with two open, rounded strokes.
2. **Files / lines / anchors:** `campushub/lib/module_app/widgets/navigation/add_product_navigation_icon.dart:25`, `_AddProductPainter.paint`; `floating_bottom_navbar.dart:341`, center `IconThemeData.size` (latest reduction18dp ->16dp); this guide records the update. `CAMPUSHUB_CONTEXT.md` records the latest vector decision.
3. **Change:** Replace the previous filled plus paths and tight framing with the supplied24x24 geometry: horizontal `(6,12)` to `(18,12)` and vertical `(12,18)` to `(12,6)`, stroke width1.5, round caps/joins. The user then requested a further size reduction: use16dp themed icon size, preserving navy tint and the existing56dp gold button/touch target.
4. **How it works:** `AddProductNavigationIcon.build` reads size/color from existing IconTheme and passes the tint to its painter. `paint` scales the24-unit viewport to the current widget, clips it and draws both open paths with `PaintingStyle.stroke`. The SVG's white stroke inherits the existing navigation tint. Original SVG padding is preserved; no crop, extra ring, parser or dependency is used. `shouldRepaint` continues checking tint changes.
5. **Backend / API:** Unchanged; same form and callbacks.
6. **Database / migration:** None.
7. **Verification:** Direct Dart analysis, formatting and scoped whitespace check passed. No tests, app run/build/install/reload/restart or device commands were performed.
8. **Limitations / manual check:** Native appearance not verified. In a user-chosen reload, confirm the smaller rounded plus, same button and existing form action. Stroke width scales proportionally with the16dp icon's24-unit viewport. No backend, API or database behavior changes accompany the size adjustment.

**Safe learning exercise:** Compare `strokeWidth=1.5` with the navbar's `IconThemeData.size=16`: the former controls line thickness in SVG units; the latter scales the entire icon. Keep the path endpoints and touch target unchanged when experimenting, and verify in a session you control without submitting a product.

## Smaller supporting navigation icons - October 19, 2026

1. **Reason:** The user requested smaller other icons after reducing the plus.
2. **Files / current lines / anchors:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart:266` (`IconThemeData.size`) and line278 (`Icon.size`) inside `_buildNavItem`; this guide records the change.
3. **Change:** Reduce destination icons from24dp to20dp for both seller and ordinary navigation. Add Product stays18dp inside the existing56dp gold button. Labels,28dp icon-layout boxes, row heights and full touch targets remain unchanged.
4. **How it works:** `_buildNavItem` supplies20dp through IconTheme to custom Home vectors and directly to Icon for the remaining font glyphs. Both selected/inactive states use the same size; existing selection motion remains. This changes artwork size rather than navigation layout or behavior.
5. **Backend / API:** Unchanged; existing routes, approval checks and callbacks remain.
6. **Database / migration:** None.
7. **Verification:** Direct Dart analysis of the source reported no issues. Source inspection confirms both destination-rendering branches use20dp and the center plus remains18dp; scoped whitespace check passed. No tests, app run/build/install/reload/restart or device commands were performed.
8. **Limitations / manual check:** Runtime appearance not verified. When the user chooses to refresh their own session, compare all destination glyph sizes, switch tabs, and confirm labels and tappable areas remain unchanged.

**Safe learning exercise:** Compare the20dp Icon/IconTheme values with the surrounding28dp SizedBox. The former sets artwork size; the latter preserves alignment and spacing. In a user-controlled session only, compare20dp with22dp, then restore20dp. No real account or product changes are needed.

## Smaller Add Product plus - October 19, 2026

1. **Reason:** The user requested a smaller plus glyph, then requested another reduction.
2. **Files / current line / anchor:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart:341`, `IconThemeData(color: activeColor, size: 18)` inside `_buildCenterActionButton`; this guide records the change.
3. **Change:** Reduce the visible Add Product glyph's themed size from22dp to18dp (previously28dp). The gold button remains56dp, with the same label and tap area.
4. **How it works:** IconTheme supplies18dp to existing `AddProductNavigationIcon.build`, which sizes its CustomPaint square; the same plus paths scale proportionally. Input is the icon size/tint; output is a smaller centered glyph. No callback or layout rewrite is needed.
5. **Backend / API:** Unchanged.
6. **Database / migration:** None.
7. **Verification:** Direct Dart analysis of the changed source reported no issues; scoped whitespace check passed. No tests, app run/build/install/reload/restart or device commands were performed.
8. **Limitations / manual check:** Runtime appearance not verified. When the user chooses to refresh their session, confirm the smaller plus is centered inside the same gold button and the existing Add Product form still opens.

**Safe learning exercise:** Find this IconTheme size and compare it with `_centerActionDiameter=56`. The former changes the glyph; the latter changes the button. Adjust only the glyph value in a user-controlled session to preserve the tap target, then restore18 after comparing. No real product submission is needed.

## Plain plus, sidebar avatar and divider spacing - October 19, 2026

1. **Cause / reason:** The user requested a plain plus without its icon ring, a profile photo/avatar in the sidebar, and guidance on increasing the horizontal divider's spacing.
2. **Exact files / current lines / anchors:** `campushub/lib/module_app/widgets/navigation/add_product_navigation_icon.dart:4` (`AddProductNavigationIcon`), line27 (tight plus framing); `seller_drawer.dart:15` (`profileDividerTopSpace`), line16 (`profileDividerBottomSpace`), line199 (`seller-profile-avatar`), and line264 (divider padding); `campushub/test/seller_drawer_test.dart`, anchor `seller-profile-avatar`, updates the existing expectation for the restored avatar. This guide, `CAMPUSHUB_CONTEXT.md` and `campushub/DESIGN.md` document current behavior.
3. **Changes made:** Remove the navy outline ring from the Add Product glyph and keep the two rounded plus strokes. The existing raised gold button remains. Frame the central12x12 portion of the original SVG so the plain plus stays optically legible at the existing glyph size. Add a56dp circular navy avatar above the seller identity with16dp separation. Keep actual name/program/year-section/email and existing menu items. The profile divider has24dp above and16dp below, controlled by two named constants rather than scattered spacers.
4. **How it works / functions / data flow:** The existing `AddProductNavigationIcon` and its callers are reused; `_AddProductPainter.paint` paints only horizontal/vertical plus paths, with a translated/scaled frame. No new icon or add-product callback is required. `SellerDrawer.build(context)` reads `user.fullName`; its first Unicode character becomes the avatar initial, with an Iconsax user outline when the name is blank. The avatar is announced as a profile avatar, not a fake uploaded photograph. `_SellerDrawerStyle.profileDividerTopSpace` and `profileDividerBottomSpace` feed `Padding` around the keyed Divider. The divider's own height remains1dp; spacing does not make the line thicker. All rows remain in the existing scrollable ListView.
5. **Backend / API behavior:** Unchanged. Inspection confirms `AuthUser` and Django's mobile `CampusHubUser` have no profile-photo URL/upload field, and the current Profile uses a default avatar. Therefore this update adds a truthful initial/avatar fallback, not an invented image URL or upload service. A real personal photograph needs a separate profile-photo storage/upload/API change before it can appear here.
6. **Database / migration impact:** None; no records, fields, dependencies or migrations changed.
7. **Verification:** Direct Dart analysis of the two source files and updated drawer test reported no issues; formatting and scoped whitespace checks passed. The existing drawer test now expects one avatar with the actual fixture initial; it was not executed for this update. No app launch, test run, build, install, reload, restart, ADB, server or device changes were performed; the active Ctrl+F5 session was preserved.
8. **Remaining limitations / manual check:** Native appearance and scrolling are not runtime verified. When the user chooses to refresh their session, verify the plain plus inside the gold button, actual-name initial above the drawer identity, divider spacing, and scrolling to Account Settings on a short screen. Blank names should show the user-outline fallback. No personal photo can be displayed until the account API supports one.

**Safe learning exercise / increasing divider space:** In `_SellerDrawerStyle`, change `profileDividerTopSpace` from24 to32 for8dp more room above the line, or `profileDividerBottomSpace` from16 to24 for8dp more below. These constants flow directly into the Divider's surrounding Padding; no backend edit is needed. Reload only in a session you control, open the drawer, confirm the gap and scroll to the last menu item. Restore the values if the larger gap wastes space. To change line thickness instead, inspect `Divider.thickness`; spacing and thickness are different properties.

## Outlined circle-plus and three-line menu - October 19, 2026

1. **Cause / reason:** The user replaced the earlier rounded-square plus with a supplied outlined circle-plus SVG and asked for a three-line hamburger sidebar button instead of the four-dot menu glyph.
2. **Exact files / current lines / anchors:** `campushub/lib/module_app/widgets/navigation/add_product_navigation_icon.dart:4` (`AddProductNavigationIcon`), line29 (`ring`), line62 (separate SVG path drawing); `campushub/lib/module_app/screens/dashboard_screen.dart:318` and `seller_dashboard_page.dart:245` (`Iconsax.menu_1_copy`). This guide, `CAMPUSHUB_CONTEXT.md` and `campushub/DESIGN.md` record the icon changes.
3. **Changes made:** Add Product now uses the exact supplied circle outline and two rounded plus strokes. Its existing raised gold circle, navy tint and size remain. Both the shared Home header and approved-seller module header use the existing Iconsax three-line hamburger; their menu tooltips and callbacks remain unchanged. Home's active/inactive SVGs, labels and navigation layout are untouched.
4. **How it works / functions / data flow:** Existing Add Product controls already instantiate `AddProductNavigationIcon` inside an IconTheme. Its `build(context)` reads the current size/tint; `_AddProductPainter.paint(canvas,size)` scales/clips to the original24x24 viewport and draws the supplied ring, horizontal stroke and vertical stroke separately. Even-odd fill makes the ring interior transparent; separate plus paths keep their intersection solid. `shouldRepaint` still checks tint changes. The existing IconButton callbacks still call their respective Scaffold's `openDrawer()`; changing `menu_copy` to `menu_1_copy` changes only the glyph from four dots to three lines. No duplicate navigation or downloaded icon is introduced.
5. **Backend / API behavior:** None changed. Existing seller permissions, current Add Product form, session and drawer routes are preserved.
6. **Database / migration impact:** None. No records, schema, package or migration changes.
7. **Verification:** Direct Dart analysis of the three changed source files reported no issues; formatting and scoped `git diff --check` passed. The locally bundled Iconsax font was inspected with Pillow: `menu_1_copy` has three separate horizontal ink bands, confirming the requested hamburger shape. No Flutter run/test/build, ADB, install, hot reload, restart, server or device changes were performed. No new tests were added for this icon-only presentation change; existing runtime tests were not run during the user's active Ctrl+F5 session.
8. **Remaining limitations / manual check:** Native appearance was not rechecked. When the user chooses to reload, confirm the outlined circle-plus in the raised action and the three-line menu in shared Home and seller tools. Open/close each existing drawer; open Add Product and dismiss without submitting. This verifies the same callbacks still work without creating records. The supplied white fills inherit the existing navy tint for visibility on current surfaces.

**Safe learning exercise:** Read the three `canvas.drawPath` calls and identify why the plus strokes are painted separately from the ring. Trace the header IconButton `onPressed` to its existing Scaffold key. A future icon swap should change glyph/path only, leaving this callback and tooltip intact. Verify manually in a user-chosen session, not by replacing their running app automatically.

## Supplied Add Product and inactive Home SVGs - October 19, 2026

1. **Cause / reason:** The user supplied exact vector shapes for Add Product (filled rounded square with a plus cutout) and inactive Home (outline with door stroke). Replace those glyphs without changing the current raised-center layout or interrupting Ctrl+F5.
2. **Exact files / current lines / anchors:** `campushub/lib/module_app/widgets/navigation/add_product_navigation_icon.dart:4` (`AddProductNavigationIcon`), line25 (`paint`); `home_navigation_icon.dart:4` (`outlined` option), line62 (`_outlinePath`); `floating_bottom_navbar.dart:84` and115 (inactive Home widgets in both item lists), line201 (`customIcon` selection), line262 (tinted widget rendering), line184 (reusable add-button helper), and line342 (visible raised action). `campushub/test/floating_bottom_navbar_test.dart:46` checks the supplied Add Product renderer; the existing multi-width Home check, anchor `itemIndex == 0`, checks the active/outline choice and tint. This guide, `CAMPUSHUB_CONTEXT.md` and `campushub/DESIGN.md` record current decisions.
3. **Changes made:** Inactive Home now paints the user's supplied outline path; selected Home keeps the previously supplied filled path. Add Product paints the supplied rounded-square-plus path inside its existing56dp raised gold circle at the existing28dp glyph size. Keep navy/muted navy colors, current labels, geometry, semantics and motion. The reusable center-add helper uses the same renderer so it cannot display the previous box-add glyph if reused later.
4. **How it works / functions / data flow:** `FloatingBottomNavbarItem.iconWidget` allows an inactive custom vector alongside the existing `activeIconWidget`. `_buildNavItem()` selects the appropriate widget from the real selected page index and wraps it in the existing IconTheme, retaining the keyed AnimatedSwitcher and full navigation semantics. `HomeNavigationIcon(outlined:true)` chooses `_outlinePath()`; false retains `_filledPath()`. Both paths use the original24x24 coordinates. `AddProductNavigationIcon.build(context)` reads size/color from IconTheme, then `_AddProductPainter.paint(canvas,size)` scales and clips the supplied path to its24x24 viewport. Even-odd fill leaves the plus and Home interior transparent rather than painting a white patch. `shouldRepaint` responds to tint changes and, for Home, outline-mode changes. No SVG parser, runtime download or new package is needed. Example: tapping Marketplace changes Home to the supplied muted outline; tapping Home restores the existing navy filled shape; Add Product still invokes the current form callback.
5. **Backend / API behavior:** Unchanged. No approval, ownership, seller checks, product API or route changes; no duplicate form or navigation.
6. **Database / migration impact:** None. No schema, data, dependency or migration changes.
7. **Verification:** Direct Dart analysis of the three source files and updated navbar test reported no issues. Dart formatting and scoped `git diff --check` passed. Existing widget expectations were updated for the two supplied renderers and Home's selected/inactive tint/mode, but tests were not executed in this update. No Flutter run/test/build, ADB, install, hot reload, restart, server or device changes were performed; the active Ctrl+F5 session was left alone.
8. **Remaining limitations / manual verification:** Source-only verification; no new native screenshot or runtime-pass claim. When the user chooses to refresh their own session, switch Home -> Marketplace -> Home to inspect the supplied outline/filled shapes. Confirm the rounded-square plus sits inside the same gold circle and opens the existing Add Product sheet; dismiss without submitting. White SVG fills are intentionally tinted with the existing navigation colors for contrast. Other glyphs and sidebar Dashboard remain unchanged.

**Safe learning exercise:** Follow `iconWidget`/`activeIconWidget` from the two Home definitions into `customIcon`. Compare the two paths in `HomeNavigationIcon`, then trace `IconTheme.color` into `Paint.color`. In a future user-chosen test session, run `flutter test test/floating_bottom_navbar_test.dart` to verify state selection and geometry without creating product records.

## Reference-layout seller bottom bar - October 18, 2026

1. **Cause / reason:** The user supplied a bottom-navigation reference and requested its layout, keeping CampusHub colors. The previous center Add Product control was a small inline rounded rectangle. The user also explicitly asked not to run/restart the app because that interrupts their Ctrl+F5 session.
2. **Exact files / current lines / anchors:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart:67` (`_centerActionRise`, `_centerActionDiameter`), line191 (`topInset` in `_buildNavItem`), line300 (`_buildCenterActionButton`), line365 (seller-only inset), and line382 (`Positioned.fill`) implement the layout. `campushub/test/floating_bottom_navbar_test.dart:45` adds geometry expectations to the existing seller-size tests, including a3x text-size case. `campushub/DESIGN.md` and `CAMPUSHUB_CONTEXT.md` record the latest design/workflow decision; this guide explains implementation and limits.
3. **Changes made:** Approved sellers retain Home | Marketplace | Add Product | Services | Facilities. The gold center action is now a56dp circle, raised16dp above the supporting white bar; its existing navy Iconsax box-add glyph is28dp. Supporting icons stay24dp, labels remain11dp Poppins with4dp spacing, and the existing supplied selected Home shape is preserved. Keep the full-width bottom safe-area fill, palette, active states, tooltip/semantics and selection motion. Ordinary accounts keep their existing flat five-destination layout.
4. **How it works / data flow:** `build(context)` still derives `hasCenterAction` from the existing callback and four page destinations. For sellers only, `topInset` becomes16. The white supporting surface is positioned16dp down inside a Stack, while the real row height grows by16dp (normally68+16=84dp before the system safe area). `_buildNavItem(..., topInset:16)` moves supporting icon/label groups lower; `_buildCenterActionButton()` places its circle at the row top and its label directly below. The raised area is reserved inside the actual navbar bounds, so Scaffold places page content above it and touch handling remains inside the parent. No negatively translated or separately floating button is introduced. At320dp, five equal slots are64dp wide, leaving4dp each side of the56dp circle; each slot remains at least48dp wide. Existing callbacks still select root indices0/1/2/3 or open the existing Add Product sheet; center action never becomes a selected tab.
5. **Backend / API behavior:** None changed. Seller access, retained pages, product creation, inventory and all existing data APIs are reused unchanged.
6. **Database / migration impact:** None; no schema, record, package or migration change.
7. **Verification:** Direct Dart analysis of the source and updated test reported no issues; Dart formatting, scoped `git diff --check` and the Impeccable source layout scan passed (scan output `[]`). Independent source review checked reserved height, SafeArea, equal slots, hit bounds and ordinary navigation. It found center-label drift above2x text scaling; center contents now follow half of the extra bar height to maintain the common label line, and the test fixture includes3x. Existing widget assertions were extended for a circular56dp action, raised position within navbar bounds and supporting/center label alignment at320/390/landscape sizes. These tests were not executed for this update. No Flutter run/test/build, ADB, install, hot reload, restart, server or device-setting command was performed; the user's active app session was left untouched.
8. **Remaining limitations / manual check:** Native appearance and runtime layout are not verified in this update, because the user asked to keep their session uninterrupted. When the user chooses to reload their session, check the raised center circle, aligned labels, narrow-width fit, safe-area bottom fill and existing Add Product sheet; switch Services/Facilities to confirm their routes. Check a non-seller account still has its ordinary five tabs. Preserve native/system Back behavior and current session. The tiny reference's dark colors are intentionally not copied.

**Safe learning exercise:** Compare `topInset=0` (ordinary navigation) with16 (seller navigation) in source. Trace the same inset into both surface positioning and reserved row height; changing only the painted position would risk overlapping page content or putting a visible control outside hit-test bounds. In a future test session chosen by the user, run `flutter test test/floating_bottom_navbar_test.dart` and confirm the geometry/navigation assertions pass. This exercise needs no real product or account edits.

## Supplied Home icon - October 18, 2026

1. **Cause / reason:** The user supplied a specific filled Home SVG and asked to use its shape in the bottom navigation. Preserve the current white bar, navy selected tint and outline-to-filled interaction.
2. **Exact files / lines / anchors:** `campushub/lib/module_app/widgets/navigation/home_navigation_icon.dart:4` (`HomeNavigationIcon`) and line25 (`paint`) contain the supplied 24x24 path; `floating_bottom_navbar.dart:18` (`activeIconWidget`), lines77/107 (both Home definitions), and line248 (selected rendering) connect it to both seller and ordinary navigation. `campushub/test/floating_bottom_navbar_test.dart`, anchor `itemIndex == 0 && index == 0`, updates the existing multi-width selection check to recognize the custom Home renderer and verify its navy tint. This guide records the change.
3. **Changes made:** Use the supplied filled Home outline and rounded door cutout when Home is selected. Keep the existing Iconsax outline when inactive, labels, sizes, other icons, navigation order and animation. The SVG's white fill is replaced by the existing selected navigation color so it remains visible on white.
4. **How it works:** Each Home item passes a constant `HomeNavigationIcon` as its optional `activeIconWidget`. `_buildNavItem` renders this only when selected and supplies the current `activeColor`/24dp size through `IconTheme`. Other items use their current font icons. `HomeNavigationIcon.build(context)` reads that theme and produces a square `CustomPaint`; `_HomePainter.paint(canvas, size)` scales the original SVG coordinates from24x24, clips to its viewport and paints the exact path, including a transparent door cutout. `shouldRepaint` returns true only when tint changes. No SVG parser, network call or new dependency is needed. Example: Home selected -> navy custom shape; Marketplace selected -> Home returns to its existing muted outline. Existing AnimatedSwitcher, movement, reduced-motion preference and row semantics continue to wrap either renderer.
5. **Backend / API behavior:** No API, account, seller approval or navigation destination changes.
6. **Database / migration impact:** None; no records, model, dependency or migration changed.
7. **Verification:** Twelve existing navbar/dashboard widget tests passed (`scratch/mobile-navbar/custom-home-icon-tests.log`); two-source-file Flutter analysis reported no issues (`custom-home-icon-analysis.log`); formatting and scoped `git diff --check` passed. The existing test previously assumed every glyph was an `Icon`; it was updated because selected Home now uses `CustomPaint`. Normal debug APK built successfully in27.6seconds (`custom-home-icon-build.log`) and installed in place on the physical Android phone without clearing data. Native screenshot `scratch/mobile-navbar/custom-home-icon-native.png` was inspected: the selected Home uses the supplied silhouette/cutout in navy, with the existing seller labels and center Add Product unchanged. Saved login remained active; no product/order/database write was made. The other-account layout was checked through widget tests rather than changing the phone's account.
8. **Limitations / manual check:** Only selected bottom-navigation Home changes; sidebar Dashboard remains its existing icon. On an updated app, tap Home, Marketplace and Home again; confirm the supplied silhouette, navy tint, unchanged Home label and preserved animation. This is a presentation change, not a new Home screen.

**Safe learning exercise:** Read the two Home item definitions and trace `activeIconWidget` to `_buildNavItem`. In a test fixture, change `activeColor` and observe that the custom painter inherits it without changing the path. Restore the fixture and run `flutter test test/floating_bottom_navbar_test.dart` to verify navigation still selects the same pages. This keeps experimentation separate from real records.

## Seller Add Product center action and Iconsax navigation - October 18, 2026

This section supersedes older five-tab seller layouts and the My Bundle Suggestions navigation below. The user explicitly chose: approved sellers get **Home | Marketplace | Add Product | Services | Facilities**; other accounts keep **Home | Marketplace | Services | Facilities | Profile**. Profile remains available to sellers through the existing header avatar.

1. **Cause / reason:** The requested seller shortcut belongs in the center of the bottom bar, while the separate My Bundle Suggestions entry duplicates the existing My Bundles workflow. Navigation icons were previously mixed Material/Lucide.
2. **Exact files / current lines / anchors:**

   | File | Line / anchor | Change |
   | --- | --- | --- |
   | `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` | 69, `default5Items`; 98, `defaultCenterActionItems`; 276, `_buildCenterActionButton` | Iconsax outline/filled navigation pairs; four seller destinations around a compact gold Add Product action, with full touch target and semantics. |
   | `campushub/lib/module_app/screens/dashboard_screen.dart` | 158, `_openAddProduct`; 516, bottom bar callback; imports/header/drawer Iconsax references | Approved-only center action invokes existing form, prevents repeated opens, refreshes on successful submission; header and regular drawer use Iconsax. |
   | `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 33, `SellerDestination`; 69, `drawerDestinations` | Remove My Bundle Suggestions destination; use Iconsax for all seller menu icons/chevrons. Keep white surface, spacing, identity and gold selection. |
   | `campushub/lib/module_app/screens/seller_workspace_content.dart` | 730, `homeHighlights`; 889, destination switch | Remove submitted-suggestions preview, its unused renderer and destination; preserve Suggested Product Bundles and existing My Bundles. |
   | `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 180, bundle success navigation; 245, menu; 260, notifications | Successful suggested-bundle creation goes to My Bundles; existing branded header uses Iconsax. |
   | `campushub/lib/module_app/screens/seller_bundle_form.dart` | 83, uncertain-submission message | Point the user to My Bundles if submission outcome is uncertain. |
   | `campushub/lib/module_app/widgets/navigation/header_profile_button.dart` | 26, missing-name fallback | Iconsax user outline; actual-user initial remains unchanged. |
   | `campushub/pubspec.yaml` | 42, `iconsax_flutter: 1.0.1` | Add and lock one icon-font dependency; `pubspec.lock` records the resolved version. |
   | `campushub/THIRD_PARTY_NOTICES.md` | 1, Navigation icons | Iconsax/package attribution and the package's BSD notice; the font is bundled offline. |
   | `campushub/test/floating_bottom_navbar_test.dart` | anchor `seller action fits` | Small/large/landscape text layouts, visual order,48dp targets, action not selecting a tab, Iconsax selected glyph pairs. |
   | `campushub/test/seller_drawer_test.dart` | anchor `const labels` | Nine menu items, no removed entry, Iconsax chevrons and existing layout checks. |
   | `campushub/test/seller_workspace_test.dart` | anchors `createProduct`, `qualifying pair`, `seller additions share Home` | Bundle remains in actual products/My Bundles; center action opens existing form, other tabs retain mapping, Profile avatar still works. |
   | `campushub/test/seller_home_entry_test.dart` | anchor `approval and revocation` | Center action appears only after approval and disappears on revocation, restoring normal Profile tab. |

   This guide, `CAMPUSHUB_CONTEXT.md` and `campushub/DESIGN.md` record current decisions. Historical reports below remain historical.
3. **Changes made:** Seller bar has four page destinations and a separate center Add Product action using the Iconsax box-add outline in a small gold container. It is not a fifth content page, and does not select another tab. Non-seller labels/routes stay unchanged. All navigation icons on the bottom bar, seller sidebar, regular drawer and shared/seller header use Iconsax; body/form/catalog icons outside this navigation scope retain existing implementations. Selected page glyphs use the package's filled icons, inactive glyphs its outline variants. Existing selection motion, white surfaces, navy/gold palette, Poppins/Montserrat/SugarPie typography, tap-only root tabs and state retention remain.
4. **How it works / functions / data flow:** Existing `DashboardScreen` approval state supplies `onCenterActionTap` only for a verified approved seller with a loaded account. `FloatingBottomNavbar.effectiveItems` then chooses the existing center-action layout: Home(index0), Marketplace(1), action, Services(2), Facilities(3). The PageView still contains Profile(index4); the header avatar calls `_goToTab(4)`. No index remapping or new page is needed, and no false page highlight is shown while Profile is open.

   `_openAddProduct()` guards seller approval and repeated taps, awaits `ProductsScreen.showAddProductSheet(context)`, then refreshes shared Home access/workspace only if submission returns true. The existing form itself rechecks the actual Django seller status before opening and uses its existing submission endpoint; client visibility does not replace server permission checks. Dismissing the sheet preserves the current tab. Example: while Services(index2) is selected, Add Product opens the sheet and Services remains index2 afterward.

   Removing `SellerDestination.suggestions` removes its menu/UI only. Suggested Product Bundles still uses actual qualifying pairs. `_createBundle()` routes a successful submission to `SellerDestination.bundles`, which already lists all owned bundle Products and their real approval status. The previous submission-list renderer is no longer necessary. Existing backend `bundle_submissions`/saved-choice data are preserved; no record was deleted or algorithm changed.

   Icons are bundled through [iconsax_flutter's documented Flutter import/font](https://pub.dev/packages/iconsax_flutter), sourced from its maintained package repository. Names ending `_copy` are outline glyphs in this package; filled variants are used for selection. The interface does not fetch icon glyphs from a website at runtime.
5. **Backend / API behavior:** No backend, ownership, approval, recommendation calculation, stock, payment, order or account logic changed. Add Product reuses current seller-status and product-submission code, and My Bundles reuses the existing workspace product set. No fake bundle records, synthetic fallback or duplicate API was introduced.
6. **Database / migration impact:** None. No models/records changed; no migration. One pinned Flutter icon dependency was added and resolved with pub get. A full rebuild is needed to include its font asset; no server command is required. Do not clear app data to update an icon font.
7. **Verification performed:** 38 scoped Flutter tests passed (`scratch/mobile-navbar/iconsax-seller-nav-tests.log`): normal-user labels/no center action, seller small-screen/landscape/2x text, 48dp center target, action staying on its current page, Services/Facilities indices, header Profile, approval/revocation, existing product form opening and successful suggested bundle -> My Bundles. Eleven-file Dart analysis reported no issues (`iconsax-seller-nav-analysis.log`). Normal `flutter build apk --debug` passed in 52.6 seconds (`iconsax-seller-nav-build.log`). The APK was installed in place on the physical Android phone without clearing data, preserving the existing login. APK inspection verified the bundled `packages/iconsax_flutter/fonts/FlutterIconsax.ttf` asset. Native screenshots in `scratch/mobile-navbar/` verified the correct seller bar (`iconsax-seller-home-native.png`), center action opening the existing Add Product sheet (`iconsax-add-product-native.png`), and the updated Iconsax drawer without My Bundle Suggestions (`iconsax-seller-drawer-native.png`). The sheet was dismissed without submitting; no real product or bundle was created. Scoped `git diff --check` passed.
8. **Remaining limitations / manual checks:** No live seller/database record is removed by hiding My Bundle Suggestions. Form fields and their business validation are unchanged. Iconsax migration is scoped to navigation/header/sidebar, rather than a global rewrite of all body/form icons. Manually open approved Home, confirm the five visible positions, tap center and dismiss its existing form, test Services/Facilities, open Profile from the header, then use the sidebar My Bundles. A non-seller must retain the original five labels and have no Add Product action. Enlarged text should retain usable touch targets; existing root swipes stay disabled.

**Safe learning exercise:** In the navbar widget test fixture only, set selected index2 and tap the center action; verify the action counter increases but the selected page remains2. Then remove the callback and verify the five ordinary tabs return. Run `flutter test test/floating_bottom_navbar_test.dart test/seller_home_entry_test.dart`. This illustrates the difference between a navigation destination and an action without editing a real account or product.

## White seller sections, retained header and tap-only bottom tabs - October 18, 2026

This update supersedes older dark drawer/seller-page surfaces and separate Messages/Account Settings navigation described below.

1. **Cause / reason:** The drawer and seller page chose dark surfaces from the app theme. Messages and Account Settings also pushed independent page layouts instead of staying beneath the seller header. The root PageView allowed horizontal gestures and animated sideways on tab selection.
2. **Exact files / current lines / anchors:**

   | File | Line / anchor | Change |
   | --- | --- | --- |
   | `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 15, local text styles; 83, `_entry`; 176, Drawer background | Always white with navy identity/navigation text, existing gold selection accent; remove dark surface branches. |
   | `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 133, `_select`; 224, Scaffold; 302, section content | White seller page and existing CampusHub AppBar remain mounted; Messages and settings render below it. |
   | `campushub/lib/module_app/screens/dashboard_screen.dart` | 145, `_goToTab`; 156, `_openSellerTool`; 185, `_openMessages`; 450, root PageView physics | Root seller entries use the existing seller host; regular Messages keeps CampusHub branding; taps jump directly and root swipes are disabled. |
   | `campushub/lib/module_app/screens/profile_details_pages.dart` | 110, `AccountSecurityPage`; 149, embedded option | Reuse current account controls without adding a second settings header. |
   | `campushub/lib/module_app/widgets/profile/profile_widgets.dart` | 330, `ProfileDetailScaffold` | Optional embedded body; standalone Profile pages retain their original Scaffold by default. |
   | `campushub/test/seller_workspace_test.dart` | anchor `all seller sections keep a white shell` | Check all ten destinations, one existing Scaffold/AppBar, retained brand/actions and white surface even in a dark parent. |
   | `campushub/test/seller_drawer_test.dart` | anchor `seller drawer labels, scrolling and selection fit` | White drawer in light/dark context, narrow/landscape/enlarged text and current menu behavior. |
   | `campushub/test/dashboard_search_appbar_test.dart` | anchor `drawer routes to existing tabs` | Swiping does not switch tabs; navbar taps/drawer choices still select correctly and Search returns normally. |

   This guide, `CAMPUSHUB_CONTEXT.md` and `campushub/DESIGN.md` record the current behavior. Test and guide edits do not modify records.
3. **Changes made:** All seller drawer sections and seller destination page backgrounds are white regardless of the global app theme. Keep the exact menu, Poppins UI, Montserrat identity, SugarPie brand, gold accent, icons, spacing and real unread count. Messages and Account Settings select the existing seller screen's content instead of pushing their own outer page. Messages already contains its page heading, so a second title is not added above it. Other seller tools continue using their existing workspace renderer. The regular Messages route now reuses CampusHubBrand, Notifications and Profile actions above its existing body. Root bottom tabs remain Home, Marketplace, Services, Facilities, Profile; no sideways gesture or cross-page slide animation.
4. **How it works / functions and data flow:** `_openSellerTool(destination)` still requires verified seller access and routes non-Dashboard entries to the existing `SellerDashboardPage`. `_select(destination)` closes the drawer and changes its selected body while the same Scaffold/AppBar stays mounted. For Messages, it renders existing `MessagesPage` with its current chat loading/error/retry. For Account Settings, it renders `AccountSecurityPage(user, embedded: true)`. The embedded flag passes through to `ProfileDetailScaffold`, which returns the same constrained SafeArea body inside ProfileTheme, without another Scaffold/AppBar. The default is false, preserving Profile's existing account navigation and recovery dialogs.

   `_goToTab(index)` clears keyboard focus, updates the selection and calls the existing PageController's `jumpToPage`. Root `NeverScrollableScrollPhysics` rejects drag-based tab changes. The existing RetainedTab wrappers still preserve visited tab state. Example: tapping Services opens index2 immediately; dragging across that page leaves index2 selected; tapping Home returns index0. Catalog horizontal rows, image galleries, ordinary vertical scrolling and drawer gestures keep their own existing behavior.
5. **Backend / API behavior:** No Django/FastAPI endpoint, ownership rule, account recovery, seller approval or inventory/business logic changed. Seller tools still use existing approval/workspace APIs and backend authorization. Chat uses existing MessagesPage; no duplicate conversation service or fake unread values. Root Home retains the previous typed optional-chat failure handling and bounded image decoding.
6. **Database / migration impact:** None. No schema, record, dependency or global saved-theme changes. The white override is scoped to these surfaces, rather than overwriting the user's stored theme preference.
7. **Verification:** 41 scoped Flutter tests passed across drawer/workspace/shared seller Home, navigation, Profile and offline chat startup (`scratch/mobile-navbar/white-shell-tap-nav-tests.log`). The strengthened explicit navbar tap/swipe test passed separately (`white-shell-tap-nav-interaction.log`). Eight-file Dart analysis is clean (`white-shell-tap-nav-analysis.log`), and the normal main.dart debug APK built in32.2 seconds (`white-shell-tap-nav-build.log`). Scoped whitespace check passed. The APK was installed on the connected physical Infinix using `adb install -r -t`; normal app launch and the saved logged-in Home were captured (`scratch/mobile-navbar/white-shell-home-native.png`). A later capture still showed Home rather than the requested open drawer, so no native verification of every destination is claimed; all ten destinations and swipe/tap behavior were verified in widget interaction tests. No app data was cleared.
8. **Limitations / manual verification:** This concerns top-level sidebar destinations. Existing secondary flows, such as product editing, order details, conversations and password-recovery dialogs, keep their own working routes. The normal shared Home, seller additions, five tabs and session remain. To test manually: select each seller sidebar destination and confirm white page + CampusHub header; verify Messages error/Retry if its server is offline; open Account Settings and confirm existing recovery controls; tap each bottom tab, drag left/right and confirm only taps change the selected tab; verify a horizontal product row still scrolls. Hot restart/rebuild is required for an older installed app.

**Safe learning exercise:** Read `ProfileDetailScaffold.embedded`. In its widget test, compare standalone Account Settings (its normal AppBar) with seller Account Settings (one seller Scaffold/AppBar). Run `flutter test test/seller_workspace_test.dart test/profile_page_test.dart`. Verify both remain functional without copying password logic or changing real user data.

## Seller menu hierarchy and header profile - October 18, 2026

This section supersedes older drawer labels and header action placements below. The app still has one shared Home with approved-seller additions and the existing five bottom tabs.

1. **Cause / reason:** The seller menu omitted Overview/Dashboard and Communication/Messages. Messages occupied the header, while the identity area had an avatar but no email. The requested change is navigation presentation, not a new seller system.
2. **Exact files / current lines / anchors:**
   - `campushub/lib/module_app/widgets/navigation/header_profile_button.dart:7`, `HeaderProfileButton`: shared 48dp profile action, 34dp avatar using the actual signed-in initial (or person outline when no name exists).
   - `campushub/lib/module_app/widgets/navigation/seller_drawer.dart:37`, `SellerDestination`; `:74`, `drawerDestinations`; `:146`, Messages unread builder; `:203`, identity area; `:244`, `seller-profile-email`; `:268`, section spacing.
   - `campushub/lib/module_app/screens/dashboard_screen.dart:156`, `_openSellerTool`; `:186`, `onProfile`; `:330`, header profile action.
   - `campushub/lib/module_app/screens/seller_dashboard_page.dart:134`, `_select`; `:297`, header profile action and existing Profile fallback.
   - `campushub/test/seller_drawer_test.dart:37`, identity fixture and `:70`, exact menu labels; `campushub/test/seller_workspace_test.dart:268`, header callbacks and `:541`, shared-Home navigation; `campushub/test/dashboard_header_test.dart:84`, header geometry assertions. Capture harness in the workspace test loads bundled fonts and mounts the lazy catalog before checking its products.
   - `campushub/tool/qa/seller_drawer_preview.dart:29`: email added only to the existing isolated QA identity fixture. This target is never imported by the production app.
   - `CAMPUSHUB_CONTEXT.md` and `campushub/DESIGN.md`: current header/menu guidance; this guide records implementation and troubleshooting.
3. **Changes made:** The exact group order is Overview (Dashboard), Seller Management (My Products, Inventory, My Bundles, Orders), Recommendations (Suggested Product Bundles, My Bundle Suggestions), Reports (Sales Analytics), Communication (Messages), Settings (Account Settings). The sidebar avatar moves to the header, leaving a full-width identity block with name, program, year/section and saved email, followed by a thin divider. Blank optional identity values are omitted. Keep Poppins14 navigation, 11 uppercase headings, Montserrat17 name/12 academic metadata, 12 email, 20dp section separation, 52dp minimum growing rows, outline icons/chevrons, and gold selected edge. White/navy drawer surfaces remain opaque.
4. **How it works / functions and data flow:** `SessionService.loadUser()` supplies `AuthUser` to the existing dashboard and drawer. `HeaderProfileButton(user, onPressed)` takes identity plus a callback and returns a reusable button; it does not load accounts or images. Home's callback selects existing tab4. From a seller tool, `onProfile` pops to the owning dashboard route then selects tab4, preserving its session. `_openSellerTool(messages)` and `_select(messages)` reuse existing message callbacks; standalone seller tools reuse `MessagesPage` when no parent callback exists. The drawer's `AnimatedBuilder` listens to existing `ChatService` conversations and shows an unread count only when positive. Dashboard returns to shared Home; account settings still opens `AccountSecurityPage`.

   Annotated example: choosing Communication -> Messages calls the existing message route after closing the drawer. It never requests a second seller workspace or creates a conversation just to render navigation. Choosing the avatar from My Products returns to the existing Profile tab, rather than introducing a seller-only account page.
5. **Backend / API behavior:** No API, model, approval, RBAC, seller metrics or messaging business logic changed. Seller navigation is still gated by the existing real approval response and backend authorization. No sample user or unread counts were introduced into production.
6. **Database / migrations:** None. No accounts, products or records changed; no dependencies or font downloads added.
7. **Verification / troubleshooting:** 29 Flutter tests passed across seller drawer/workspace/shared Home, header, five-tab navigation and search AppBar tests (`scratch/mobile-navbar/seller-header-tests.log`). Tests include320dp width, landscape,2x text, menu callbacks, notification-left-of-avatar geometry, Profile access, session preservation and seller revocation. The strengthened seller-tool -> root Profile -> Home return test also passed separately (`scratch/mobile-navbar/seller-header-profile-return-test.log`). Eight-file Dart analysis reported no issues (`seller-header-analysis.log`); normal main.dart debug APK build succeeded in32.9seconds (`seller-header-build.log`). Scoped whitespace validation passed. Light/dark rendered Flutter widget captures were inspected for typography, divider/identity spacing, icons, selected highlight, lower-menu scrolling and header placement (`scratch/mobile-navbar/seller-header-light-review/`, `seller-header-review/`). These use isolated fixtures, not database data. Native emulator verification was attempted but ADB remained unauthorized; only the emulator launched for this task was stopped. No physical phone installation or native visual success is claimed. Initial test failures included stale header/menu/greeting expectations and a lazy catalog assertion that needed to mount its section and settle its FutureBuilder before locating a product. Fixes affected test synchronization/expectations, not marketplace data logic.
8. **Limitations / manual steps:** `AuthUser` has no profile-photo URL, so the header uses the existing initials/default-avatar behavior instead of inventing an image source. Mobile notifications retain the existing honest unavailable message. To check manually: open approved Home, verify white SugarPie header with Notifications then avatar; open the menu and scroll through all six groups; verify email/divider; open Messages; open My Products then avatar and confirm Profile tab; return Home and confirm normal catalogs/five tabs; repeat with enlarged device text. An updated build/hot restart is needed to see source changes.

**Safe learning exercise:** In `seller_drawer_test.dart` only, replace the fixture email with a longer address and run `flutter test test/seller_drawer_test.dart`. Verify all three size/text configurations pass without overflow, then restore the fixture. Follow `onSelected` into the existing hosts to see how presentation stays separate from navigation and backend permissions.

## Mobile font and drawer refinement - October 18, 2026

Current mobile UI is bundled Poppins; CampusHub header remains SugarPie and profile/drawer identity name/program/year-section remain Montserrat. Seller drawer keeps its existing destinations with a solid white/navy surface, stronger secondary text,52dp growing rows and22dp outline icons. No sidebar blur filter was found; font delivery/weight consistency was corrected. See [the typography guide](mobile-typography.md) for exact files/lines, functions/data flow, API/migration impact, verification, limits and safe practice. This supersedes older generic Montserrat/Roboto mobile UI styling notes; shared Home and five tabs remain.

## Remove the duplicate seller greeting - October 18, 2026

1. **Cause / reason:** Shared Home already displays the logged-in greeting. The inline seller renderer called `overview(context)`, which prepended a second Welcome back immediately above Sales Overview.
2. **Exact files / lines / anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:864`, `homeHighlightsOnly` Column children; this guide and `CAMPUSHUB_CONTEXT.md` record the correction.
3. **Changes:** Inline mode calls the existing `homeHighlights(context)` directly instead of the full overview wrapper. Only the duplicate greeting is omitted.
4. **How it works:** HomePage keeps the main greeting -> Search -> seller highlights -> normal catalogs. `homeHighlights()` returns the existing Sales Overview and seller content without adding another greeting. The standalone overview behavior is preserved. No duplicated renderer or calculation is introduced.
5. **Backend / API:** Unchanged; existing real seller data and approval checks are reused.
6. **Database / migration:** None.
7. **Verification:** Targeted Dart analysis passed with no issues (`scratch/mobile-navbar/seller-single-greeting-analysis.log`); scoped whitespace check passed. No new tests for this one-line presentation fix; manual check is to open approved shared Home and confirm exactly one greeting, with Sales Overview immediately starting the seller section.
8. **Remaining limitations:** Running apps require hot reload/restart or an updated APK to reflect the source. No APK build or phone installation is claimed for this small text/layout correction.

Safe practice: read `overview()` and `homeHighlights()` and identify which adds the greeting; trace the inline `homeHighlightsOnly` branch to see why calling the narrower helper prevents duplication without changing data.

---

## White header and Sugar Pie restored - October 18, 2026

1. **Cause / reason:** Inspection found the approved seller shared-Home header had a conditional navy background, while CampusHubBrand had been switched back to Montserrat and a hardcoded older gold. The user explicitly requested white header and Pie font. Keep the current shared Home/seller sections/navbar and drawer structure intact.
2. **Files / lines / anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:290` header Container and `:356` status bar; `campushub/lib/module_app/screens/seller_dashboard_page.dart:242` existing module AppBar; `campushub/lib/module_app/widgets/navigation/campushub_brand.dart:42` Hub color and `:48` fontFamily; `campushub/test/seller_workspace_test.dart:262` header expectation; this guide, CAMPUSHUB_CONTEXT.md and campushub/DESIGN.md for current instructions.
3. **Changes:** White header/status area for all Home accounts and existing seller module pages; navy menu/message/notification icons; shared CampusHub wordmark uses existing bundled SugarPie24/w400, navy Campus and shared #FCB315 Hub. No new fonts/downloads or Home/page changes.
4. **How it works / function/data flow:** `DashboardScreen.build()` renders the white header and existing CampusHubBrand. The brand chooses the existing light logo and Text.rich spans; SugarPie resolves through its existing pubspec font registration. Seller module AppBar reuses the same brand in light mode. Example: a seller's header resolves `HomeAppColors.gold` for Hub rather than a separate RGB constant; its inline Sales Overview stays in the same Home ListView with all five tabs. Labels and normal UI text keep their existing typography.
5. **Backend / API:** Unchanged. Seller approval, metrics, Apriori, unread messages and navigation callbacks remain the same; no new endpoint or business logic.
6. **Database / migration:** None; existing bundled font reused, no schema or record changes.
7. **Verification:** Existing branded seller header/actions test passed with updated white/navy and SugarPie assertions. Targeted Flutter analysis of three source files: no issues (`scratch/mobile-navbar/white-sugarpie-header-analysis.log`). Normal debug APK build passed in50.4seconds (`white-sugarpie-header-build.log`); scoped whitespace check passed. This update built the APK but did not install/restart it on the phone; no new native phone verification is claimed.
8. **Limitations / manual check:** A running older APK needs a rebuilt app or hot restart. Existing PNG logo artwork is unchanged. Open shared Home as an approved seller: white header, Pie wordmark and five-tab navbar must remain together. Select a seller management tool and confirm the same white brand header and working icons.

Safe practice: read CampusHubBrand's fontFamily and find its existing SugarPie registration in pubspec.yaml. Run `flutter test test/seller_workspace_test.dart --plain-name "branded seller header"` and check that changing fontFamily locally would fail the font assertion; restore it without touching real account data.

---

## Remove Duplicate Header & Navy Blue Banner, and Update Seller Sidebar — October 18, 2026

### 1. Cause / Reason
The seller workspace screen (`SellerDashboardPage`) previously featured a solid navy blue `AppBar` (`backgroundColor: HomeAppColors.navy`) rendering a `CampusHubBrand` logo and name, followed immediately inside the body by a duplicate text title `Text(_selected.label)`. In addition, in dark mode, the seller navigation drawer had icons styled in dark navy blue against pure black surfaces, creating poor contrast and visual inconsistency. Furthermore, the sidebar had not yet been updated to match the exact institutional hierarchy requested by the user: 4 clean groups (`SELLER MANAGEMENT`, `RECOMMENDATIONS`, `REPORTS`, `SETTINGS`), 8 specific tools, Lucide outline icons, and no duplicate profile card or redundant overview row.

### 2. Exact Files Changed
- `campushub/lib/module_app/screens/seller_dashboard_page.dart`: Lines 220–345
- `campushub/lib/module_app/widgets/navigation/seller_drawer.dart`: Lines 1–225
- `campushub/test/seller_workspace_test.dart`: Lines 260–330
- `campushub/test/seller_drawer_test.dart`: Lines 1–95

### 3. Changes Made
1. **Removed Duplicate Header & Navy Blue Banner in `SellerDashboardPage`**:
   - Replaced `backgroundColor: HomeAppColors.navy` and `CampusHubBrand` with a clean, single title `Text(_selected.label)` directly in the `AppBar`.
   - Used theme-aware surface colors (`isDark ? const Color(0xFF1E293B) : Colors.white` for the AppBar; `isDark ? Colors.white : HomeAppColors.navy` for icons/text).
   - Removed the duplicate `Padding(child: Text(_selected.label))` from the top of `body`.
   - Replaced the outer `Column` with `RefreshIndicator` directly as the body.
2. **Updated `SellerDrawer` Hierarchy & Icon Contrast**:
   - Organized into 4 exact sections:
     - `SELLER MANAGEMENT`: `My Products` (`LucideIcons.box`), `Inventory` (`LucideIcons.boxes`), `My Bundles` (`LucideIcons.packagePlus`), `Orders` (`LucideIcons.shoppingBag`).
     - `RECOMMENDATIONS`: `Suggested Product Bundles` (`LucideIcons.lightbulb`), `My Bundle Suggestions` (`LucideIcons.layers`).
     - `REPORTS`: `Sales Analytics` (`LucideIcons.barChart2`).
     - `SETTINGS`: `Account Settings` (`LucideIcons.settings`).
   - Trailing chevrons use `LucideIcons.chevronRight`.
   - Removed the duplicate profile card header (avatar, full name, section) from the top of the drawer.
   - Removed `overview` / `Seller Dashboard` from the drawer list so it begins immediately with `SELLER MANAGEMENT`.
   - Solved dark-mode contrast: Drawer background defaults to black `#000000` in dark mode with white icons and labels; in light mode, clean white background with navy icons/text. No dark-navy-on-black blending.
3. **Updated Test Suites**:
   - Updated `test/seller_workspace_test.dart` to assert clean AppBar background (`const Color(0xFF1E293B)`) and title `isA<Text>()` without brand logo or duplicate header text.
   - Updated `test/seller_drawer_test.dart` to assert 8 menu destinations, check `SELLER MANAGEMENT` at top, `SETTINGS` at bottom, and expect `LucideIcons.chevronRight`.

### 4. How It Works / Functions and Data Flow
- When an approved seller opens the seller workspace, `SellerDashboardPage` determines `isDark` via `Theme.of(context).brightness == Brightness.dark || !ThemeService.instance.isLightMode`.
- The `AppBar` renders `_selected.label` in 18pt Montserrat bold with theme-appropriate foreground and background, eliminating stacked headers.
- When tapping the menu button, `SellerDrawer` renders its 8 drawer destinations grouped by section (`SELLER MANAGEMENT`, `RECOMMENDATIONS`, `REPORTS`, `SETTINGS`).
- Active items are highlighted with a 3px gold (`#FCB315`) left indicator border.
- Inactive icons are crisp white (`Colors.white`) in dark mode, avoiding any dark navy blue on black surfaces.

### 5. Backend / API Behavior
No backend endpoints or payloads were changed. Django REST API remains the primary single source of truth for seller authorization, status, and workspace analytics.

### 6. Database / Migration Impact
Zero database impact. No PostgreSQL models, tables, or migrations were modified.

### 7. Tests Performed
- `flutter analyze lib/module_app/screens/seller_dashboard_page.dart lib/module_app/widgets/navigation/seller_drawer.dart test/seller_workspace_test.dart test/seller_drawer_test.dart` — passed with 0 issues.
- `flutter test test/seller_drawer_test.dart test/seller_workspace_test.dart test/seller_home_entry_test.dart test/dashboard_search_appbar_test.dart` — all 24 tests passed.

### 8. Remaining Limitations
`SellerDrawer` retains an optional `Back to CampusHub` action at the bottom of its list tile sequence so mobile users who pushed into full-screen seller tools can easily pop back to the main buyer tab without requiring system gesture navigation.

---

## Dedicated SellerDrawer in mobile DashboardScreen for approved sellers — October 18, 2026

### 1. Cause / Reason
The mobile app's main dashboard drawer previously displayed standard buyer navigation destinations (`Home`, `Marketplace`, `Facilities Booking`, `Services`, `Messages`, `Profile & Account`, `My Cart`) alongside a appended `SELLER TOOLS` section whenever a user was an approved seller. This caused duplication and clutter for sellers. The user requested removing `Home`, `Marketplace`, and the other buyer navigation items from the sidebar for sellers, replacing it with the clean, dedicated `SellerDrawer`.

### 2–3. Exact Files, Anchors, and Changes Made

| File | Approximate Line / Anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 331 `drawer: _sellerApproved && _user != null` | Conditionally render the dedicated `SellerDrawer` when `_sellerApproved && _user != null`. On selection, closes the drawer and routes to the selected seller tool via `_openSellerTool(destination)`. On `Back to CampusHub`, closes the drawer and stays on tab 0 (`Home`). For non-sellers, retains the standard buyer `Drawer` without the redundant `SELLER TOOLS` block. |
| `campushub/test/seller_workspace_test.dart` | 542 `Open menu` | Assert that opening the drawer as an approved seller renders `SellerDrawer` and does not contain `Marketplace`, `Facilities Booking`, or `My Cart`. |

### 4. How It Works / Functions and Data Flow
- When a user signs in, `_loadUserName()` checks seller status using `widget.sellerService.status()`. If approved, `_sellerApproved` is set to `true` and `_user` is populated.
- When building `DashboardScreen`, the `Scaffold.drawer` checks `_sellerApproved && _user != null`.
- If true, `SellerDrawer` is rendered with the user's details, `selected: SellerDestination.overview`, `onSelected`, and `onBackToCampusHub`.
- Inside `SellerDrawer`:
  - Profile header displays avatar, full name, academic program, and year/section.
  - Section `OVERVIEW`: `Seller Dashboard` (routes to `_goToTab(0)`).
  - Section `PRODUCT MANAGEMENT`: `My Products`, `Inventory`, `My Bundles`.
  - Section `ORDER MANAGEMENT`: `Orders`.
  - Section `RECOMMENDATIONS`: `Suggested Product Bundles`, `My Bundle Suggestions`.
  - Section `REPORTS`: `Sales Analytics`.
  - Section `SETTINGS`: `Account Settings`.
  - Bottom action: `Back to CampusHub` (closes drawer).
- Non-sellers (`_sellerApproved == false`) receive the standard buyer drawer containing `Home`, `Marketplace`, `Facilities Booking`, `Services`, `Messages`, `Profile & Account`, and `My Cart`.

### 5. Backend / API Behavior
Unchanged. All authentication, seller verification, and RBAC rules remain enforced on Django backend endpoints.

### 6. Database / Migration Impact
None. No schema, models, or migrations were modified.

### 7. Tests Performed
- Ran `flutter analyze lib/module_app/screens/dashboard_screen.dart` — passed with 0 issues.
- Ran `flutter test test/seller_workspace_test.dart test/seller_drawer_test.dart test/seller_home_entry_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart` — all 26 tests passed.

### 8. Remaining Limitations
The seller drawer is strictly shown when `_sellerApproved && _user != null`. If seller status has not finished loading asynchronously upon initial mount, the fallback is the clean buyer drawer until the profile resolves.

---

## Correction: seller sections inside the shared Home - October 18, 2026

This supersedes the previous automatic dedicated-seller-Home interpretation. The user clarified that sellers must retain the same Home, header, search, catalogs and five-tab navbar as non-sellers; only extra seller sections are added.

### 1. Cause / reason

The previous change replaced the root Home Scaffold with SellerDashboardPage for approved users. That removed the regular navbar and normal browsing content from their initial screen, which was the wrong interpretation. Remove that automatic replacement; keep the original HomePage for everyone.

### 2-3. Files / current lines / nearby anchors / changes

| File | Approximate line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 85 `_loadUserName`; 155 `_openSellerTool`; 395 SELLER TOOLS; 453 `sellerSections` | Keep the regular Scaffold/header/PageView/navbar regardless of seller status. Existing Django flag adds the inline seller component. Remove automatic seller page replacement and Home-tab interception. Existing seller tools stay accessible through the drawer; no automatic seller overview page is pushed. Status errors are inline and do not hide public browsing. |
| `campushub/lib/module_app/screens/home_page.dart` | 32 `sellerSections`; 258 insertion | Optional seller-only content below Search and above Marketplace. Same greeting, search, products, facilities and services remain. Non-sellers use the original null/default slot. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 23 `homeSection`; 58 `didUpdateWidget`; 189 inline build | Reuse the existing authenticated workspace loader, bundle creation and component state in a section-only mode: no nested Scaffold/AppBar/Drawer/ListView for shared Home. Existing module pages remain available only when explicitly selected. Refresh revision reloads actual metrics after Home refresh/resume. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 471 `homeHighlights`; 619 conditional build | Extract the existing Sales Overview/four KPI cards and Suggested Product Bundles into one reusable rendering method. Inline mode returns a Column inside Home's scroll; existing full workspace views reuse that same method. No repeated revenue or Apriori logic. |
| `campushub/test/seller_home_entry_test.dart` | approval/resume/error/application/deep-link cases | Assert the seller addition uses one Scaffold, original search and regular navbar. Approval changes add/remove sections rather than replacing Home; errors retain public navigation. |
| `campushub/test/seller_workspace_test.dart` | shared Home/navbar/catalog integration | Verify seller sections plus five tabs, explicit My Products navigation/return, approved Profile without seller-dashboard entry, and ordinary marketplace product cards below the seller sections. Scope scroll gestures to Home's vertical scroll rather than the outer horizontal PageView. |
| `campushub/test/home_card_background_test.dart` | 11 width cases | Replace obsolete carousel Explore Now/Book Now expectations with the current catalog Home: real test fixture cards, search, no decorative campus-image card, Marketplace See All and navbar return at360/390dp. The obsolete expectations did not represent the existing Home implementation. |
| `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md`; this guide | latest shared-Home correction | Supersede the incorrect root-page replacement guidance. |

### 4. Functions / inputs / outputs / data flow

Existing dashboard loads SessionService's actual account and calls existing seller-access GET. A true approved flag supplies the optional `HomePage.sellerSections` widget; false/unknown never displays seller data. Shared Home always builds the same normal header, search, catalogs and Home/Marketplace/Services/Facilities/Profile navbar. No alternate initial route or new page is created.

The existing SellerDashboardPage state is reused with `homeSection: true`. In that mode its output is a small inline section container, not a page. It loads the existing owner workspace and passes real data to `SellerWorkspaceContent(homeHighlightsOnly: true)`, which returns Sales Overview and Suggested Product Bundles as a Column in the existing Home ListView. This avoids nested scrolling and duplicate data calculations. Both products still must be owned by the current seller; research metrics and synthetic fallback remain hidden.

Example: an approved seller sees Welcome/Search -> Sales Overview -> Suggested Product Bundles -> Marketplace -> Facilities -> Services, with the same bottom tabs throughout Home. A non-seller sees Welcome/Search -> Marketplace -> Facilities -> Services. The seller can browse all normal products and use every tab. Profile still has no Seller Dashboard entry; non-approved users retain Apply to Sell.

`_openSellerTool()` opens an already-existing management view only after an explicit drawer/See All action. Existing My Products/Add Product, inventory, orders, analytics and bundle creation remain functional; Account Settings reuses AccountSecurityPage. Returning from such a tool goes back to the shared Home. This is separate from automatically replacing Home, which has been removed.

### 5. Backend / API behavior

No backend changes. Reuse existing approval, owner workspace, product submission, canonical inventory and live Apriori APIs. The inline component retains server approval checks. Workspace loading/error does not block normal catalogs. Initial identity loads independently; an access failure displays a retry action without inventing approval/counts. Home refresh/resume increments a revision so the existing component reloads actual metrics.

### 6. Database / migrations

None. No records, models, migrations, approvals, orders, stock or session tokens changed. Gold remains #FCB315.

### 7. Verification

57 Flutter tests passed across seller entry/workspace/application/Profile/drawer/navbar and regular Home/catalog tests (`scratch/mobile-navbar/seller-inline-home-tests.log`). Seven-file targeted Flutter analysis passed with no issues (`seller-inline-home-analysis.log`). Scoped diff whitespace check passed. Build/device results will be recorded after completion. Backend tests were not rerun because Django behavior was not changed.

Manual check: restart the updated app with an approved seller. Confirm normal white CampusHub header, greeting/search and five tabs; scroll to Sales Overview and Suggested Product Bundles, then further to ordinary Marketplace/Facilities/Services. Tap Marketplace, Services, Facilities and Profile; Home should return to that same combined Home, not a separate seller dashboard. Verify a non-approved account has no seller cards and retains Apply to Sell. Use existing authorized accounts; do not seed fake orders or change approvals for display testing.

### 8. Remaining limits / safe practice

Live suggestions can legitimately be empty until actual eligible transactions qualify; no samples added. Approval changes are read on normal refresh/resume, not pushed in realtime. Bundled raster logos remain existing artwork. Explicit existing management screens keep their own established navigation; this correction changes the shared Home presentation and automatic entry behavior.

Safe practice: change only HomeAccessService's isolated fixture state from pending to approved, run `flutter test test/seller_home_entry_test.dart`, and verify both cases still contain one normal navbar while only the approved case has seller sections. Restore the fixture. Trace the boolean -> optional Home slot -> existing workspace -> reusable Column flow without modifying a real account.

---

## Approved sellers open seller Home directly - October 18, 2026

This section supersedes the earlier Profile -> Seller Dashboard entry. The existing regular and seller screens remain separate.

### 1. Cause / reason

Confirmed: login/startup and dashboard routes always built regular DashboardScreen Home; Profile conditionally displayed Seller Dashboard to reach the separate seller page. Therefore an approved seller still saw the shopping Home first. The requested flow now chooses the appropriate existing Home using the authoritative Django seller-access response.

### 2-3. Exact files changed, current lines and anchors

| File | Approximate line / nearby code anchor | Change / expected behavior |
| --- | --- | --- |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 38 `sellerService`; 85 `_loadUserName`; 130 `didChangeAppLifecycleState`; 167 `_backToCampusHub`; 275 `build`; 388 drawer first destination; 480 `onSellerAccessChanged` | Existing root resolves actual seller approval and renders existing SellerDashboardPage directly for approved accounts. Keep ordinary Home/five tabs for others. Check access on resume, handle loading/error/retry, preserve explicit public browsing/deep links, and return sellers to their own Home from the regular Home navigation. |
| `campushub/lib/module_app/screens/profile_page.dart` | 28 `onSellerAccessChanged`; 62 `_refreshSeller`; 93 `_openSeller`; 100 captured `navigator`; 310 application row | Remove Seller Dashboard from Profile. Only non-approved, non-admin accounts see the Apply to Sell row, with actual pending/revision/rejected/suspended status in the subtitle. Existing application workflow remains. Notify the root about newly approved access; capture Navigator before async work so approval can safely dismiss a form after Profile is unmounted. |
| `campushub/lib/module_app/screens/seller_application_form.dart` | 24 `onSellerApproved`; 77 `initState`; 93 lifecycle; 152 approval callback; 540 existing approved action | Recheck existing status when the app resumes. A form opened through Profile returns to the root seller Home on approval. Existing standalone form fallback and application fields/submission remain. |
| `campushub/test/seller_home_entry_test.dart` | `HomeAccessService`; role-state tests; application/resume test | New isolated tests for all five non-approved states, resume approval/revocation, approval while an application is open, failed/malformed status and Services deep link. No production accounts/requests changed. |
| `campushub/test/seller_workspace_test.dart` | Back to CampusHub integration | Start an approved seller directly at existing root Home. Verify actual seller menu, Back to regular five tabs with same login, no Profile application/dashboard entry and return via regular drawer Seller Dashboard. |
| `campushub/test/seller_application_test.dart` | approved Profile test; retained Profile approval refresh | Assert approved Profile has neither seller-management link nor application row. Existing pending-to-approved refresh informs the root once. |
| `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md`; this guide | latest approved-seller Home note | Record current navigation, functions/data flow, verification and limits. |

### 4. How it works / functions, inputs, outputs and data flow

Existing startup/login -> existing dashboard route -> `DashboardScreen._loadUserName()` -> SessionService logged-in user -> existing `SellerApplicationService.status()` -> Django `is_approved_seller` boolean -> existing seller Home or existing regular Home. Approval is a separate permission, not a change to Student/Guest account type. No GetX/new router/screens are introduced.

The root accepts only an actual boolean response. It shows a small initial loading indicator while access is checked. Failure has Retry and Continue to CampusHub; public browsing never enables the seller menu. `_accessRequest` ignores older asynchronous responses, and mounted checks prevent updates after disposal. On app resume the existing status GET is repeated; ongoing approved seller screens retain their widget state during that check. A revoked/suspended result removes seller Home, while backend ownership/RBAC remains the final authority on every management API.

Approved default Home reuses `SellerDashboardPage`, its Scaffold, existing SellerDrawer, six sections, actual seller metrics and #FCB315 palette. It has no regular bottom bar. Back to CampusHub explicitly opens the normal shopping Home without logout. While browsing, a seller can tap Home or the regular drawer's Seller Dashboard row to return to seller Home. Non-sellers keep the ordinary Home row and five tabs. An explicit Services deep link still opens Services; Home subsequently opens the correct role-specific Home.

Profile no longer pushes the seller page. Its non-approved Apply to Sell action reuses existing intro/form/status screens. If a pending applicant is approved while the form is open, its resume status check invokes `onSellerApproved`; the captured root Navigator dismisses the application route, and the existing root approval refresh selects seller Home. This avoids a second seller screen or a stale form overlay. Approved users retain Profile/Edit Profile through Back to CampusHub -> Profile.

Annotated example: a real `is_approved_seller: false` pending response opens regular Home and keeps Apply to Sell / Pending Review. After the administrator approves the same account, resume/status refresh returns `true`; root displays the existing sales dashboard, Profile application row disappears, and the seller drawer provides management destinations. No seller label is inferred from a product name or cached account-type string.

### 5. Backend / API behavior

No backend edits. Reuse authenticated GET `/api/seller/access-status/`, existing seller workspace and product endpoints. No approval POST, account role mutation, duplicate seller records, synthetic recommendations or new chat auth logic. SellerDashboardPage still rechecks approval and Django still enforces approved/active/non-suspended owner access. Regular mobile accounts and live products/orders are untouched.

### 6. Database / migration impact

None. No models, records or schema changed; no migration command. SessionService token/user storage and logout logic are unchanged.

### 7. Verification

50 Flutter tests passed across `seller_home_entry_test`, `seller_workspace_test`, `seller_application_test`, `profile_page_test`, `dashboard_center_add_button_test` and `seller_drawer_test`. Includes the application-overlay approval transition, separate menus, profile removal, session preservation, pending/rejected/revision/suspended states, status error/retry, exact five regular tabs and existing bundle flow. Log: `scratch/mobile-navbar/seller-default-home-tests.log`. Six-file targeted Flutter analysis passed with no issues (`seller-default-home-analysis.log`). No Django tests rerun because backend code is unchanged. Normal debug APK build passed in65.2seconds (`seller-default-home-build.log`), and in-place installation succeeded (`seller-default-home-install.log`), preserving app data/login. After restart, the physical Android phone opened Seller Dashboard directly, with its actual first-name greeting, sales KPIs, seller hamburger and no regular bottom tabs; screenshot `scratch/seller-sidebar/default-home/seller-default-home.png` was visually inspected. A subsequent native check confirmed Back to CampusHub restored the signed-in regular Home/five tabs. Profile removal and returning from regular Home to seller Home were verified by the passing widget integration; the native follow-up stopped when its My Cart target was not visible, so it is not claimed as a completed native Profile check. Scoped diff whitespace check passed.

Manual steps: restart the app using an already approved account; seller sales Home should open directly with its own hamburger and no regular tabs. Use Back to CampusHub, then Profile: no Seller Dashboard/apply row should exist. Regular Home/drawer Home navigation returns that approved account to seller Home. With a real non-approved account, regular Home and Apply to Sell should remain; check the actual application subtitle. Approval/revocation must be performed only through normal authorized administration, not fabricated live fixtures for UI testing.

### 8. Remaining limitations / learning exercise

Approval changes are observed on opening/resuming the app, refreshing Home/Profile or an existing application status check; no realtime approval push or background polling was added. Connection errors cannot prove an approval state and require retry or public-only browsing. Existing native notifications/profile-photo limitations remain. No live account approval, product/order creation or token changes were used for testing.

Safe practice: in the isolated HomeAccessService test fixture, change state from pending to approved and run `flutter test test/seller_home_entry_test.dart`. Predict which Home/menu should render and confirm the assertion; then try suspended and confirm the seller drawer disappears. Restore fixture changes. This teaches the server-flag -> root-state -> existing-screen data flow without altering a real account.

---

## Gold corrected to #FCB315 - October 18, 2026

1. **Cause / reason:** The latest user correction specifies #FCB315. The attached seller brief and older Flutter palette rule still said #FCB316; the direct correction takes precedence. Existing seller widgets already inherit the shared color, so another seller-specific palette would duplicate it.
2. **Exact files / current lines / anchors:** All replacements below change only the RGB literal. Line numbers remain unchanged by the source edits.

| File | Approximate line(s) | Nearby anchor |
| --- | --- | --- |
| `campushub/lib/main.dart` | 36 | Existing gold color literal |
| `campushub/lib/module_app/screens/cart_screen.dart` | 19 | Existing gold color literal |
| `campushub/lib/module_app/screens/components/account_recovery_dialog.dart` | 185 | Existing gold color literal |
| `campushub/lib/module_app/screens/components/auth_theme_toggle.dart` | 9 | Existing gold color literal |
| `campushub/lib/module_app/screens/components/campus_legal_dialog.dart` | 4 | Existing gold color literal |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 44, 963, 1106 | Existing gold color literal |
| `campushub/lib/module_app/screens/facility_screen.dart` | 472 | Existing gold color literal |
| `campushub/lib/module_app/screens/login_screen.dart` | 26 | Existing gold color literal |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 636, 1032, 1643, 1650, 1838 | Existing gold color literal |
| `campushub/lib/module_app/screens/products_screen.dart` | 26, 1017, 1160 | Existing gold color literal |
| `campushub/lib/module_app/screens/signup_screen.dart` | 37, 784 | Existing gold color literal |
| `campushub/lib/module_app/screens/splash_screen.dart` | 18 | Existing gold color literal |
| `campushub/lib/module_app/widgets/cart_icon_button.dart` | 52 | Existing gold color literal |
| `campushub/lib/module_app/widgets/facilities/booking_widgets.dart` | 9 | Existing gold color literal |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 21 | Existing gold color literal |
| `campushub/lib/module_app/widgets/order_summary_widgets.dart` | 10 | Existing gold color literal |
| `campushub/lib/module_app/widgets/six_digit_code_input.dart` | 92 | Existing gold color literal |
| `campushub/test/product_card_test.dart` | 78, 142 | Existing gold color literal |
| `campushub/DESIGN.md` | 6, 161 | gold / selected drawer edge |
| `campushub/docs/floating_bottom_navbar_guide.md` | existing gold references | palette examples |
| `AGENTS.md` | 32 | Gold Accent rule |
| `CAMPUSHUB_CONTEXT.md` | latest gold note | current palette correction |
| This guide | this section | implementation and verification |

3. **Changes made:** Replace the remaining Flutter #FCB316 color literals with #FCB315, including matching product-card test colors and current design guidance. Update the project rule so later work does not restore the old mobile gold. No screen restructuring, new widgets or behavior changes.
4. **How it works / functions and data flow:** `HomeAppColors.gold` is a constant Color value, with no runtime input. `ProfileStyle.gold`, `CampusHubBrand` and SellerDrawer consume that value for existing text, controls and the selected-item edge. Example: selecting Inventory makes the existing drawer edge read `HomeAppColors.gold`, now `Color(0xFFFCB315)`. Other older screens retain their existing local constants with the same corrected RGB; no navigation or business function changed. Keeping those structures avoids a broad refactor for a color correction.
5. **Backend / API behavior:** Unchanged. Django authentication, ownership, Apriori, product approval, payments and inventory calculations are not involved in resolving a Flutter Color.
6. **Database / migration impact:** None; no schema, records or migration command.
7. **Verification:** Case-insensitive source scan found no #FCB316 occurrences remaining in Flutter lib/test/current DESIGN.md or AGENTS.md. Four-file targeted Flutter analysis passed with no issues (`scratch/mobile-navbar/gold-315-analysis.log`). Normal debug APK build passed in25.3seconds (`gold-315-build.log`); scoped diff whitespace check passed. No new tests were added or run for this literal-only correction. Existing test fixture colors were aligned; no business-test claims are made for this change. The new APK was built, not installed on the phone during this color-only update.
8. **Remaining limitations / manual check:** Bundled PNG logos are existing raster artwork and were not recolored; this correction covers app color values and the text wordmark. Open Profile -> Seller Dashboard -> hamburger and select Inventory: the accent should use the shared gold, with the same drawer layout and authenticated session. A running old APK requires the rebuilt app or a Flutter restart to use the new constants.

Safe practice: locate `HomeAppColors.gold` at line21 and trace its uses in CampusHubBrand and SellerDrawer without editing them. Run `flutter analyze lib/module_app/widgets/home/home_preview_cards.dart` to check the palette owner; verify there is no second seller-only gold constant.

---

## Actual seller route, four KPIs and bundle submission — October 18, 2026

This section supersedes the previous four sales cards and saved-pair interpretation of My Bundle Suggestions.

### 1. Cause / reason and route diagnosis

Inspection traced the actual entry to `ProfilePage._openSeller()` → `SellerDashboardPage` → its own `Scaffold.drawer: SellerDrawer`. The approved-application entry uses the same seller screen. Regular `DashboardScreen`/`HomePage` has a separate drawer and five tabs. There is no GetX implementation to update. Read-only inspection of the connected phone initially showed regular Home (`Open menu` plus Home/Marketplace/Services/Facilities/Profile), rather than the seller route. Seller-only menu changes are intentionally not visible in that regular drawer. No alternate outdated SellerDrawer implementation was found. A stale APK was not established as the cause; installed/build timestamps were close. Named route metadata now makes the dedicated seller path traceable without another screen or route controller.

Two missing behaviors were confirmed: mobile product submission only created single products, and saved pair preferences had no review status. This update reuses the existing Product/BundleComponent and normal Product approval workflow for actual bundle submissions. It does not invent approval states for saved preferences.

### 2–3. Exact files, current approximate lines, anchors and changes

| File | Line / nearby anchor | Change / expected result |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 15 `SellerDashboardPage`; 131 `_createBundle`; 164 `Scaffold`; 167 `drawer`; 268 `onCreateBundle` | Existing real seller shell and drawer retained. Create Bundle resolves both suggested IDs against the loaded owner catalog, opens the recipe form using the existing authenticated service and reloads actual submissions after success. Pass the actual logged-in first name to Home. |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 134 `build`; `Seller navigation`; `seller-navigation-list` | Add an accessible drawer name and stable list key for diagnosis. Keep the exact nine-item menu, identity fields, no badge/My Profile, existing styling and callbacks. This is the actual drawer rendered by the seller Scaffold. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | `pair`; 419 `submittedBundles`; 469 `overview`; 561 `salesPeriod` | Actual welcome; Total Sales/Total Orders/Active Products/Pending Orders; horizontal image/name pairs with View Suggestion/Create Bundle; actual bundle listing review statuses. Preserve six-section order, chart, inventory and orders. See All > uses existing destinations; sales-period dropdown is expanded to fit large text. |
| `campushub/lib/module_app/screens/seller_bundle_form.dart` | 7 `SellerBundleForm`; 45 `submit` | Focused mobile recipe editor; real pair product names/categories, bundle name/price, required quantities, existing ProductCustomizationConfig variant selections and description. Submit through existing createProduct; no standalone bundle stock/threshold. Loading, validation and uncertain-write error states; no automatic POST retry. |
| `campushub/lib/module_app/screens/profile_page.dart` | 106 `RouteSettings` | Name the existing approved route `/seller-dashboard`; preserve actual status check, session and Home return callback. |
| `campushub/lib/module_app/screens/seller_application_form.dart` | 530 `RouteSettings` | Same route name for the existing approved-application entry. |
| `campushub/lib/module_app/routes/app_routes.dart` | 7 `sellerDashboard` | Shared route-name constant for those existing MaterialPageRoute pushes. It is route metadata, not another global screen or a GetX route. |
| `backend/core/modules/marketplace/mobile_seller_views.py` | 96 `public_products`; 99 `overview`; 101 `bundle_submissions` | Add owner-scoped current active/pending counts and actual owned Product bundle submissions. Reuse the serialized catalog once. Existing sales/order querysets and authentication remain authoritative. |
| `backend/core/api/views.py` | 697 `seller_submit_product`; 721 recipe imports; 751 `validate_recipe`; 777 component creation | Extend the existing product-submission endpoint for bundle type. Reuse canonical same-owner/approved/active/exact-variant recipe validation, confirm the selected pair is still in live Apriori results, then atomically create the Product and components in normal pending approval. Reject fake standalone stock and forged/foreign pairs. |
| `backend/core/api/test_mobile_seller_workspace.py` | 162–209 mobile bundle/overview tests | Four additional tests cover real approval, derived availability, unchanged component stock, variant enforcement, forged pairs/foreign ownership and scoped counts. Existing bundle inventory keeps a BND SKU identity but creates no standalone stock pool/movement. |
| `campushub/test/seller_workspace_test.dart`; `seller_test_fixtures.dart` | qualifying-pair test; real Profile-to-Seller integration; workspace fixture | Exercise the actual Create Bundle navigation/form/submission-to-status flow with isolated transport fixtures; assert named seller route, Home return, period filter and new data contract. Fixtures never enter production source or database. |
| `campushub/DESIGN.md`; `CAMPUSHUB_CONTEXT.md`; this guide | latest seller route note | Record UI/data semantics, verification, deployment and limits. Regular `home_page.dart` and regular bottom navigation were not edited in this update. |

### 4. How it works / functions and data flow

Home receives the actual `AuthUser.firstName`; blank names show Welcome Back without an invented person. Total Sales uses existing completed-and-paid revenue for the selected sales period. Total Orders counts that seller's orders across statuses/all dates. Active Products counts approved, non-archived listings, including legitimate out-of-stock listings; Pending Orders counts actual pending orders. A label explicitly scopes the period to Total Sales. Other three cards are current/all-order counts, not fabricated period statistics.

Both recommendation products must resolve to the current owned catalog before the pair is displayed or opened. Existing live Apriori still decides qualifying product combinations; no synthetic CSV or research metrics are exposed. `_createBundle()` passes the two real product records and existing SellerApplicationService to SellerBundleForm. The editor reuses ProductCustomizationConfig's actual single/multiple groups. It sends product IDs, quantities and selected group/option names, not a client-calculated available stock or seller ID.

The existing `seller_submit_product()` authenticates and locks/rechecks the existing seller approval record. `validate_recipe()` verifies components, quantities, exact variant stock and same owner using the canonical bundle module. For mobile bundles, the submitted pair must match both recipe product IDs and a current live Apriori result. Existing Product/BundleComponent rows are saved atomically; normal seller listings stay Pending until reviewed through existing marketplace product administration. A bundle's stored stock placeholder0 is not sellable availability; canonical bundle availability remains the minimum of component availability divided by required quantity, including shared variant pools. Component quantities are not deducted merely by creating a listing.

My Bundle Suggestions now shows the owner's actual bundle Product records and existing Pending Review/Approved/Rejected/Archived presentation. It is a view of existing listing review, not a new recommendation-review model. Saved/dismissed pair preferences and their API remain preserved for compatibility but are not relabeled as reviewed submissions. Creating an actual sellable bundle continues to preserve bundle identity and component-order inventory behavior through existing order logic.

### 5. Backend / API behavior

Reuse `GET /api/mobile/seller/workspace/` (additive overview/bundle_submissions keys) and `POST /api/seller/products/submit/` (bundle type with suggestion_id and bundle_components). All ownership comes from existing authentication. The server rejects bypass attempts even if the frontend is altered. Existing single-product requests, normal Product review, order/payment lifecycle, reserved stock, real analytics and research-only synthetic CSV remain intact. The sales-period control reuses the existing workspace period parameter. No extra network/chat session or duplicate settings screen was introduced.

### 6. Database / migration impact

No schema migration, duplicate model, approval field, sample product or transaction data was needed. Existing Product.product_type/approval_status, BundleComponent required_quantity/selections and SKU identity mechanisms are reused. User-initiated bundle submission writes actual Product/components plus existing activity logging; no stock adjustment happens on submission. No live listing/order was created for verification.

### 7. Verification / testing

- 79 Django tests passed: mobile workspace/application, bundle inventory/order behavior and live bundle suggestions. Includes four new mobile bundle/overview cases. Log: `scratch/mobile-navbar/seller-home-route-django.log`.
- 40 Flutter tests passed, including real Profile → named seller route → actual drawer → existing destinations, Create Bundle with input validation and pending-review result, no technical metrics, 2× text/zero sales, period changes, denial/revocation and Back to the same regular Home/session/five tabs. Log: `seller-home-route-flutter.log`.
- Nine-file targeted Dart analysis: no issues. `manage.py check`: clean; `makemigrations --check --dry-run`: no changes. Log: `seller-home-route-analysis.log`.
- Production-widget PNGs inspected in `scratch/seller-sidebar/route-update/`: seller-overview, seller-overview-bottom, seller-drawer-top and seller-drawer-bottom. The visible test names/statistics are isolated fixtures; no synthetic production recommendations were added. The large-text check exposed a sales-period dropdown overflow; `isExpanded` fixed it. Form tests scroll to the actual visible controls and use existing Pending Review copy rather than invented status names.
- Normal `lib/main.dart` debug APK rebuilt successfully (19.8 seconds) and installed with `adb install -r`, preserving app data and login. On the physical Android phone, Profile → Seller Dashboard opened the dedicated seller screen and its hamburger opened the actual updated SellerDrawer. Native screenshots `scratch/seller-sidebar/route-update/phone-seller-home.png` and `phone-seller-drawer.png` were visually inspected. Confirmed the actual first-name greeting, four real KPI values, seller-only menu, no Approved Seller badge/My Profile and no regular bottom tabs inside the seller screen. The current account has no qualifying live pairs; the honest empty state was verified without adding production records.
- Native inspection exposed faint default text in the sales-period control. Give this seller-only dropdown explicit Montserrat 13/500 text and 12/500 label styling through the existing ProfileStyle helper; keep `isExpanded` for large-text fit. The post-adjustment workspace suite passed all nine tests and targeted analysis found no issues. Final normal APK build succeeded in40seconds (`seller-home-final-build.log`), installed successfully in place (`seller-home-final-install.log`) and actual Seller Home/drawer were reopened and captured from that final build; the dropdown text is now legible. The regular Home/shared theme was not changed. Native verification covers the real Home-to-seller entry and rendered Home/drawer; all destination, Account Settings and Back/session scenarios were verified by widget tests, not claimed as a completed native tap-through of every page.

Manual steps: launch the rebuilt normal app, keep the signed-in account, then regular Profile → Seller Dashboard. Confirm navy CampusHub header, separate seller heading, actual greeting, four compact cards and six section order. Hamburger must say Seller navigation and have the exact nine links; no regular bottom tabs, badge or My Profile. Verify all links/Account Settings and Back → regular Home. With genuinely sufficient qualifying orders, View Suggestion/Create Bundle must show only both owned products; choose exact variants/positive quantities, submit and confirm Pending Review in My Bundle Suggestions and the existing web Products review list. Verify no component stock changes until the normal order workflow allocates/sells it. Do not seed fake live orders merely to make the button appear.

### 8. Remaining limitations and safe exercise

Live Apriori still needs genuine stored multi-item transaction history; current one-item order storage commonly yields no qualifying pairs. Empty suggestions are correct and have no synthetic fallback. Mobile notification feed/count and uploaded profile-photo API remain unimplemented as documented below. Saved pair preferences are not a separate approval queue. No new seller order-processing or inventory-adjustment controls were added.

Safe practice: in the isolated workspace fixture change a bundle approval_status from pending to rejected, run `flutter test test/seller_workspace_test.dart`, and inspect the corresponding review label; then restore the fixture. For stock behavior, read `test_mobile_bundle_requires_exact_stock_variant` and predict why choosing Large permits fewer bundles than Small, then run the workspace Django tests in their test database. Never approve an account or add real orders for this exercise.

---

## Final seller header, settings and Home sections — October 18, 2026

This section supersedes the earlier drawer badge/My Profile/App Settings menu and seller-title-only header described below.

### 1. Cause / reason

The requested seller experience needs the CampusHub brand to remain in the header, a separate page heading, a simpler settings menu and six useful Home sections. Inspection found an existing Navigator/PageController implementation, existing account-security and theme settings screens, a shared ChatService conversation store and a Notifications-unavailable sheet. There is no GetX routing or mobile notification-count data source to reuse. Account Settings now reuses the existing account-security screen rather than making another seller account system.

### 2–3. Files modified, approximate lines and nearby anchors

| File | Current line / anchor | Change / reason |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 34 `SellerDestination`; 51 `Account Settings`; 60 `SellerDrawer` | Remove My Profile and the Approved Seller header row/icon/type role. Replace ACCOUNT/My Profile/Settings with SETTINGS/Account Settings. Preserve logged-in name, Program, Year/Section, default avatar, outlined icons, chevrons, selection and scrolling. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 14 `SellerDashboardPage`; 111 `_select`; 176 AppBar; 192 `AnimatedBuilder`; body `Column` | Account Settings opens existing AccountSecurityPage(user). Header stays navy with CampusHub mark/wordmark and existing message/notification callbacks. Put destination heading below it. Seller background is #F7F8FC. Returning Home from a later order page resets to page1 so Recent Orders uses the nearest records. |
| `campushub/lib/module_app/widgets/navigation/campushub_brand.dart` | 5 `CampusHubBrand` | Extract one reusable brand widget from the existing regular header. Default retains navy Campus/gold Hub and logo_light; onNavy uses white Campus/gold Hub and existing white/gold logo_dark. Preserve the established bundled SugarPie wordmark; UI labels/headings use Montserrat. Flexible/FittedBox preserves narrow-header fit. No assets added. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 219 `CampusHubBrand` | Replace only the previous inline brand subtree with the same component/default appearance and existing test keys. Regular header behavior and all five bottom tabs remain unchanged. Other pre-existing workspace edits are outside this update. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 249 `inventory`; 285 `orders`; 466 `overview`; 535 `sectionHeader` | Home now contains Sales Overview, Suggested Product Bundles, My Bundle Suggestions, Sales Trend, Inventory Attention and Recent Orders in that order. Reuse full inventory/order/pair renderers with compact previews; See All routes to existing seller destinations. Preview suggestions/saved pairs/orders are capped at3. Inventory Attention includes only actual low/out-of-stock/expired rows. |
| `campushub/lib/module_app/widgets/seller/seller_sales_trend.dart` | 6 `SellerSalesTrend`; 69 `_SalesLine` | Small line presentation of the existing daily paid-sales series; real first/last date labels, accessible value summary, finite/nonnegative validation, safe zero baseline and honest unavailable/empty messages. No forecasting, new sales calculation or chart dependency. |
| `campushub/lib/module_app/screens/profile_page.dart` | 87 `_openSeller` | Remove the unused seller My Profile callback arguments; preserve the existing owner-route Back/Home callback and message/notification destinations. Regular Profile/Edit Profile still works after Back to CampusHub. |
| `campushub/lib/module_app/screens/seller_application_form.dart` | 8 constructor; 529 `SellerDashboardPage` | Remove obsolete onProfile plumbing from the approved-application entry. Keep current application/authentication behavior. |
| `campushub/test/seller_drawer_test.dart` | identity assertions / exact label list | Assert no Approved Seller/My Profile, exact9 destinations and SETTINGS/Account Settings after scrolling. Preserve size/chevron/tap/Back checks. |
| `campushub/test/seller_workspace_test.dart` | screenshot capture; `branded seller header`; `zero sales fit`; existing suggestion/settings tests | Verify brand/header colors, real callbacks, no zero unread badge, six sections, See All navigation, existing account-security route, zero sales and 2× text portrait/landscape. Load bundled SugarPie and precache the logo for faithful optional captures. |
| `campushub/DESIGN.md`, `CAMPUSHUB_CONTEXT.md`, this guide | latest seller header note | Record current scope, function/data flow, navigation, verification and limits. |

### 4. How it works / navigation structure

The final drawer has OVERVIEW → Seller Dashboard; PRODUCT MANAGEMENT → My Products, Inventory, My Bundles; ORDER MANAGEMENT → Orders; RECOMMENDATIONS → Suggested Product Bundles, My Bundle Suggestions; REPORTS → Sales Analytics; SETTINGS → Account Settings; then Back to CampusHub. The removed text is only the visible approval badge; access approval checks remain mandatory.

`CampusHubBrand(onNavy: true)` supplies the seller mark and wordmark. SellerDashboardPage keeps hamburger/menu behavior and observes `ChatService.instance` through AnimatedBuilder. Each conversation's actual unreadCount is summed; the badge appears only when the total is positive, with99+ for larger real totals. It reuses the existing initialized chat service and does not open another WebSocket or invent a notification count. Messages/Notifications use the same callbacks supplied by regular Dashboard/Profile.

`_select(settings)` pushes the existing `AccountSecurityPage`, whose current title is Account & Security. Its email verification/reset-password logic remains shared with regular Profile. The separate App Settings/theme page still exists in regular Profile and was not duplicated. `_backHome()` still invokes the captured regular owner-route callback and selects Home; no logout or token change occurs.

`overview()` consumes the existing workspace response: analytics for sales cards/trend, recommendations for qualifying live pairs, saved_suggestions for the actual shortlist, inventory for attention and orders for recent records. `sectionHeader()` passes an existing SellerDestination through `onNavigate`; no new page or route is created. The full screens reuse the same renderers and source data. For example, a server inventory row marked low_stock appears in Inventory Attention with its exact product/variant and quantities; a healthy row stays on Inventory but is omitted from attention.

`SellerSalesTrend` accepts the server's labels/sales arrays. It validates matching lengths and finite nonnegative numbers, then passes values to `_SalesLine` solely for canvas coordinates. With all values0 the graph stays at the baseline and says no completed paid sales; a single real point is drawn as a point. Malformed/missing data shows unavailable, not a made-up series. The same backend completed/paid revenue logic still supplies every value.

### 5. Backend / API behavior

Unchanged: existing workspace, product, inventory, order, live Apriori, saved choices and server approved/active/non-suspended ownership checks remain authoritative. Support/Confidence/Lift are not displayed. No synthetic fallback, sample production data, new notification feed, parallel account settings, Quick Actions or global search was added. Seller management remains separate from the regular five-tab navigation.

### 6. Database / migration impact

None in this update. No schema changes, records, dependency packages, assets or new API endpoints; no migration command required. The earlier choice-table migration0041 remains a prerequisite only for environments that have not yet deployed the existing seller workspace.

### 7. Tests performed / how to test

- Final Flutter run:40 tests passed across seller drawer/workspace/application, regular Profile and five-tab navigation. The optional screenshot test was enabled and captured real production widgets using isolated fixtures. Log: `scratch/mobile-navbar/seller-final-header-tests.log`.
- Targeted Dart analysis of ten edited source/test files: no issues. Log: `seller-final-header-analysis.log`.
- Widget PNGs inspected at375×812: `scratch/seller-sidebar/final-header/seller-overview.png`, `seller-overview-bottom.png`, `seller-drawer-top.png`, `seller-drawer-bottom.png`. Confirmed white/gold brand on navy, independent page heading, section/See All alignment, actual rendering of the sales plot, no approval badge, final settings menu and reachable Back. Fixtures are test-only, not live database data.
- Added zero-sales/header checks at320×812 and844×390 with2× text/Reduce Motion. Existing tests cover approval denial/revocation, saved choices, real account screen, returning Home with the same session and unchanged five tabs.
- Initial three failures came from asserting an offscreen lazy SETTINGS element before scrolling. The test now checks it after navigating to that group. The first screenshot lacked the explicitly loaded wordmark font; loading SugarPie in the capture harness fixed the test artifact without changing production font delivery.
- Normal `lib/main.dart` Android debug APK build passed (assembleDebug46.2s); output `campushub/build/app/outputs/flutter-apk/app-debug.apk`, log `scratch/mobile-navbar/seller-final-header-build.log`. Scoped `git diff --check` was clean. No Django test rerun was needed for this Flutter-only update; prior backend logic is unchanged.

Manual steps: sign in with a real approved active seller → Profile → Seller Dashboard. Confirm logged-in identity with no badge, all9 menu links and SETTINGS/Account Settings. Tap Account Settings and confirm the same Account & Security screen used by regular Profile. Return to Seller Dashboard, inspect all six Home sections and tap Suggested Product Bundles → See All. Messages should open the existing inbox; its badge must reflect real conversation counts. Notifications should retain the current honest unavailable notice. Back to CampusHub must select regular Home without logout; Profile → Edit Profile remains accessible. Increase text size/rotate and scroll to Back; confirm no lost controls or clipped labels.

### 8. Remaining limitations / safe exercise

Mobile Notifications currently has no implemented feed/unread-count service. It retains the existing unavailable notice and has no fabricated badge. The existing API still exposes no uploaded avatar field, so the current default photo remains. No live physical-phone seller account flow was exercised in this update; current visual evidence is widget rendering and automated interaction checks. Existing read-only inventory/order/bundle management and real-data Apriori sparsity limitations remain as described below.

Safe exercise: edit only `sellerWorkspaceFixture()` in `campushub/test/seller_test_fixtures.dart` to set the daily trend sales to0, run `flutter test test/seller_workspace_test.dart`, inspect the baseline/empty message and restore the fixture. Inputs are the existing workspace labels/sales arrays; output is presentation only, with no inventory/order mutation. Never copy fixtures into lib/ or add sample sales to the live database for this check.

---

## Seller-only drawer typography refinement — October 18, 2026

### 1. Cause / reason

The requested exact menu and approved-seller gate were already implemented. Inspection confirmed the drawer still inherited the regular Profile's generic 1.45 line height, small 13sp navigation labels, heavier Back label and unrelated gray metadata tokens. This follow-up refines the existing drawer's hierarchy without introducing another sidebar or navigation system. The invoked Taste Skill excludes native mobile; its preserve-first approach was used while Flutter Material remains the component foundation.

### 2–3. Exact files changed and changes made

| File | Approximate current line / anchor | Change / expected behavior |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 8 `_SellerDrawerStyle`; 77 `_entry`; 137 `build`; 242 `seller-back-to-campus` | Drawer-local Montserrat roles: name 16sp/700/1.3, metadata 12sp/1.4, Program and Approved Seller 12sp/600, section labels 11sp/700/1.4 with 0.8sp tracking, menu and Back 14sp/500/1.35, selected menu 600. Navy at 72% provides secondary text, navy at 12% provides decorative dividers/avatar outline. Preserve white, navy, Flutter gold, 52dp minimum rows, consistent 22dp outlined icons, chevrons and 6% navy selected surface with gold edge. Section labels align to icon inset, with 24dp above/8dp below. Back uses the same icon/text alignment. Decorative icons are excluded from accessibility announcements; visible labels/selected semantics remain. |
| `campushub/tool/qa/seller_drawer_preview.dart` | 1 emulator-only comment; 7 `main`; 27 fixture; 47 `build` | Isolated native QA entry point renders the production SellerDrawer and local selection/return callbacks. Explicit fixture identity only; no login, API calls or database changes. It is not imported by `lib/main.dart`. |
| `campushub/DESIGN.md` | `Seller workspace drawer` | Update the scoped drawer typography/palette and alignment rules. |
| `CAMPUSHUB_CONTEXT.md` | latest seller drawer refinement note | Preserve the current choices, checks and verification limits for later work. |

### 4. How it works / reused components

`_SellerDrawerStyle` reuses `ProfileStyle.text()` to load the existing bundled Montserrat variable font and set its weight axis. Its role-specific heights, weights and palette apply only inside SellerDrawer; the regular Home, Profile and bottom navigation keep their existing styles. For example, `_SellerDrawerStyle.label(selected: true)` returns the same 14sp menu geometry with weight 600, so the current location is clearer without shrinking text or clipping long labels.

The existing enum still supplies the same ten labels, six headings and outlined Material icons. `_entry()` receives one destination, compares it to the selected enum, renders the row and calls the existing `onSelected` callback. `build()` receives the existing AuthUser and callbacks, displays the actual saved identity and keeps the whole drawer inside SafeArea/ListView. Expanded text and minimum row heights allow narrow screens and system text scaling to grow naturally. No fixed label heights, ellipsis or text-scale override was introduced. The default avatar remains because the current AuthUser API exposes no uploaded profile-photo field.

### 5. Backend / API behavior

Unchanged. The existing Profile seller-status check, SellerDashboardPage `_load()` and server `approved_seller()` still decide access. Only an approved, active, non-suspended seller can read seller workspace data or write suggestion choices. My Profile/Settings and Add Product reuse their existing destinations; Messages and Notifications stay in the header. Back to CampusHub returns to the existing Home with the same session. There is no GetX implementation in this app; existing Navigator/PageController behavior is preserved. No Store Management, Quick Actions, extra search, duplicate Messages or Notifications were added.

### 6. Database / migration impact

None for this visual follow-up. It adds no fields, packages, assets, API endpoints or records and does not require another migration. The earlier workspace migration 0041 is still part of that feature's deployment requirements below.

### 7. Tests performed

- 24 Flutter tests passed: seller drawer, seller workspace, seller application and regular five-tab navigation. These cover exact destinations, scrolling and selection at 375×812/1×, 320×812/2× and short landscape/2×; access denial/revocation; existing seller actions; Back to Home with session retained. Log: `scratch/mobile-navbar/seller-drawer-refinement-tests.log`.
- Dart analysis of the edited production drawer and isolated preview: no issues. Log: `seller-drawer-refinement-analysis.log`.
- Impeccable type detector returned `[]` before the changes; an independent read-only typography assessment identified the shared line-height, Back-weight and palette refinements. Detector evidence alone was not treated as visual verification.
- Enabled widget capture also passed (one optional capture test), producing refreshed production-widget PNGs in `scratch/seller-sidebar/refinement/`.
- Android Pixel_10a emulator: production drawer rendered in the isolated QA target, with bundled Montserrat. Inspected normal portrait, selected Suggested Product Bundles, bottom groups/Back, 2× text with system dark appearance and landscape at 2× text. Actual device screenshots: `scratch/seller-sidebar/native-top.png`, `native-selected.png`, `native-bottom.png`, `native-large-dark.png`, `native-landscape-large.png`. Checked type hierarchy, icon/text alignment, selected contrast, safe-area clearance, scroll reachability and wrapping. The pinned white ProfileTheme remains white under system dark appearance. At 2× text, long names/labels wrap and the profile header can fill the short landscape viewport; the entire drawer remains scrollable.
- The emulator's saved boot state stalled. A cold boot and QA-only software-rendering launch resolved the preview startup; the APK installation exceeded its command timeout but was confirmed installed before launch. Initial screenshots containing only Android splash were replaced with actual drawer frames and were not accepted as verification. No production renderer settings changed. Emulator font/theme/rotation settings were restored and the task-started emulator closed; the connected physical phone was untouched.
- Both preview and normal `lib/main.dart` debug APKs built successfully. The final `campushub/build/app/outputs/flutter-apk/app-debug.apk` is the normal application, not the preview. Build logs: `scratch/mobile-navbar/seller-drawer-preview-build.log` and `seller-drawer-refinement-build.log`. No current physical-phone approved-account flow was tested.
- Source color calculation: 72% navy on white composes to RGB(90,89,130), approximately 6.59:1 text contrast. Final type detector returned `[]`; scoped `git diff --check` was clean. These support, rather than replace, the native visual inspection above.

Manual verification: use an approved active seller, open Profile → Seller Dashboard → menu, inspect actual profile fields and all six groups. Tap Inventory, My Products and Sales Analytics, reopen the drawer and check the selected row. Open My Profile and Back to CampusHub; the latter must return Home without logging out and retain all five regular tabs. Increase system text size and scroll to Back; long labels must wrap rather than disappear. Pending/suspended users must still be denied seller workspace access.

### 8. Remaining limitations / troubleshooting

This is a drawer-only visual update. Existing read-only Inventory/Bundles/Orders/Analytics screens and the current live-data Apriori limitations are unchanged. An empty suggestion list is not a styling failure. For denied access, check the actual server approval/account state; do not bypass it in the drawer. The standalone preview bypasses no production authentication because it is a separate emulator-only entry point with no network access.

Safe learning exercise: change only the `metadata` height in `_SellerDrawerStyle` from 1.4 to 1.5, run `flutter test test/seller_drawer_test.dart`, inspect narrow/large-text wrapping, then restore 1.4. The input is an AuthUser, the output is a visual widget tree, and no database data changes. Do not use QA fixture identities in production source or approve an account merely to take a screenshot.

---

## Seller drawer and connected workspace — October 18, 2026

This section supersedes older statements below that Seller Dashboard contains only My Products/Add Product. The user explicitly authorized building missing Flutter screens and connecting existing Django logic.

### 1. Cause / reason

Inspection found one small SellerDashboardPage, no seller drawer, and no mobile Inventory/Bundles/Orders/Analytics screens. The app uses Navigator, a retained PageController and existing Profile routes; it does not use GetX. Extending this implementation preserves the regular five-tab navigation and avoids a second seller shell or authentication system.

### 2–3. Exact files, approximate current lines, anchors and changes

Paths are relative to the repository root. Search the named anchor when later edits move line numbers.

| File | Line / code anchor | Change and reason |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 7 `SellerDestination`; 34 `SellerDrawer`; 48 `_entry` | One scrollable seller drawer: six requested headings, ten destinations, outlined icons, right chevrons, selected navy surface/gold edge, actual account identity and Back to CampusHub. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 13 `SellerDashboardPage`; 45 `_load`; 111 `_select`; 141 `_choose`; 174 `build` | Extend the existing seller screen into the shell. Recheck approved access, read workspace, select sections, reuse account routes and submit shortlist choices. Loading/error/Retry/revocation states replace misleading zero values. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 9 `SellerWorkspaceContent`; 174 `productList`; 248 `inventory`; 270 `orders`; 417 `suggestions`; 457 `overview`; 507 `salesAnalytics` | Real owner-scoped overview, products, variant inventory, derived bundles, paginated orders, live suggestions, saved shortlist and period sales. Presentation receives server data; it does not recalculate business stock or mine transactions. |
| `campushub/lib/module_app/services/seller_application_service.dart` | 8 `SellerApplicationException`; 92 `workspace`; 109 `suggestionChoice` | Reuse bearer authentication/response decoding and the working API base. Add workspace GET and one-shot choice POST, with HTTP status retained for access revocation. |
| `campushub/lib/module_app/screens/profile_page.dart` | 24 `onHome`; 87 `_openSeller` | Capture the owning regular route; return to its existing Profile or Home without logging out or stacking another regular dashboard. Forward existing Messages/Notifications callbacks. |
| `campushub/lib/module_app/screens/seller_application_form.dart` | 14 callback arguments; 533 `onBackToCampusHub` | The approved-application entry passes the same navigation callbacks to SellerDashboardPage. Existing application validation/submission stays intact. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 393 `onHome: () => _goToTab(0)` | One callback returns to the existing Home tab. The regular five labels, screens and bottom navigation remain unchanged. |
| `backend/core/modules/marketplace/mobile_seller_views.py` | 23 `approved_seller`; 35 `live_suggestions`; 43 `saved_pairs`; 63 `workspace`; 113 `suggestion_choice` | Thin authenticated adapters reuse shared inventory, order ownership, sales and Apriori helpers. GET does not write. POST saves/dismisses/removes a qualifying owned pair and writes the existing audit log. |
| `backend/core/modules/marketplace/services/order_access.py` | 21 `seller_order_queryset` | Add active mobile-account ownership through `product__mobile_seller`; preserve the existing web seller branch. Do not trust client seller IDs or legacy multi-item JSON ownership. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py` | 104 `analyze_live`; 234 `build_bundle_suggestions` | Optional `mobile_seller` scopes the existing live mining path to the authenticated seller. Existing web callers, calculator and thresholds remain shared. |
| `backend/core/api/models.py` | 980 `SellerBundleSuggestion` | Store saved/dismissed pair choices separately from Product, inventory and orders. Canonical ordered IDs plus a seller/pair uniqueness constraint make repeated saves idempotent. |
| `backend/core/api/migrations/0041_seller_bundle_suggestions.py` | 7 `Migration` | Create only the new choice table. No duplicate account, stock, order or bundle model. |
| `backend/core/core/urls.py` | 93 `mobile_seller_workspace`; 94 `mobile_seller_suggestion_choice` | Register the two mobile endpoints below. |
| `backend/core/api/test_mobile_seller_workspace.py` | 16 `MobileSellerWorkspaceTests` | Seven database/API tests cover approval, ownership, stock, choices, pagination and stable query counts. Fixtures are isolated in the test database. |
| `campushub/test/seller_drawer_test.dart` | 12 `testWidgets` | Exact destinations, identity, selectable rows, chevrons, Back and 48dp targets; narrow/landscape/large-text checks. |
| `campushub/test/seller_workspace_test.dart` | 38 `WorkspaceService`; 95 screenshot test; 211 navigation tests; 333 Home-return test | Mock transport checks, actual widget navigation/actions, loading/error/revocation and regular Home/session preservation. Optional real-widget PNG capture uses test fixtures only. |
| `campushub/test/seller_test_fixtures.dart` | `sellerWorkspaceFixture` / `sellerPairFixture` | Isolated response fixtures; never imported into production source. |
| `campushub/test/seller_application_test.dart` | `approved profile opens Seller Dashboard` | Update the previous own-listings check to enter My Products through the new drawer. |
| `campushub/DESIGN.md`; `CAMPUSHUB_CONTEXT.md` | `Seller workspace drawer`; latest seller note | Record scoped visual rules, architecture, verification and honest limitations. |

### 4. How it works: functions, inputs, outputs and data flow

1. Existing Profile loads the authenticated application status. `_openSeller()` pushes the existing SellerDashboardPage and supplies callbacks to the current regular route. Back to CampusHub pops back and invokes `_goToTab(0)`; the token is retained.
2. `_load()` calls existing `status()` before `workspace(period, ordersPage)`. An incrementing request ID prevents an older response replacing a newer selection. Server denial clears the privileged content; a transport failure shows Retry rather than fabricated empty totals.
3. `approved_seller(request)` reads the existing bearer identity through `applicant()`, checks mobile source/account state and the latest approved, non-suspended SellerRequest. The server does not accept a seller ID as authorization.
4. `workspace()` returns actual owned products, expanded inventory rows, a 30-row order page, completed/paid sales and live product-only recommendations. It uses `prime_bundle_inventory()`, `build_inventory_table()`, `seller_order_queryset()`, `valid_sales_queryset()`, `_sales_time_series()` and `_top_products()` rather than another stock/revenue implementation. Product/inventory eager loading and order prefetching avoid per-row queries.
5. `SellerWorkspaceContent` selects the presentation for the drawer destination. PageStorageKey retains per-section scroll. My Products alone opens the existing `ProductsScreen.showAddProductSheet()`; listing approval still happens on Django.
6. `_choose(pairId, action)` sends one POST. `suggestion_choice()` checks actual product ownership, current listing eligibility and the actual live qualifying result set; it locks/rechecks seller approval before saving/dismissing/removing the choice and auditing it. It never changes component stock or creates a sellable bundle.

For example, inventory rows for separate variants stay separate. The Inventory module owns `Available = On Hand - Reserved`, thresholds and active reservations; Flutter displays its returned quantities. Bundle availability continues to use the existing minimum of `floor(component available / required quantity)`, including the exact selected variant. Bundle On Hand, Reserved and Threshold are absent/em dashes because no standalone stock is invented.

Drawer structure is exactly OVERVIEW → Seller Dashboard; PRODUCT MANAGEMENT → My Products, Inventory, My Bundles; ORDER MANAGEMENT → Orders; RECOMMENDATIONS → Suggested Product Bundles, My Bundle Suggestions; REPORTS → Sales Analytics; ACCOUNT → My Profile, Settings; then Back to CampusHub. Header Messages and Notifications use the existing callbacks and are not duplicated in the drawer.

### 5. Backend / API behavior

- `GET /api/mobile/seller/workspace/?period=30&orders_page=1`: private/no-store response; owned records only. Period choices use the existing analytics parser (7 days, 30 days, current month). Only valid completed AND paid sales contribute to revenue, units and order metrics. Current order listing is not restricted by that sales period.
- `POST /api/mobile/seller/suggestions/<productA>|<productB>/` with JSON `{"action":"save"}`, `dismiss` or `remove`: authenticated real choice persistence. Two different numeric IDs are canonically ordered. Cross-owner pairs return 404, invalid input 400, unqualified/archived pairs 409, analysis failure 503, missing/expired authentication 401 and denied seller access 403. Saved pairs can be removed even if they no longer qualify.
- No synthetic CSV fallback, visible Support/Confidence/Lift, inferred seller identities or client-side approval authority. Mining still uses the existing backend thresholds/calculations.
- Overview and recommendation screens reuse the same result set. My Bundle Suggestions means the seller's saved shortlist; My Bundles means actual Product bundle records. These are deliberately separate concepts.

### 6. Database / migration impact

Migration `api.0041_seller_bundle_suggestions` was generated and applied successfully to the local database. It creates the choice table with seller/product references and ordered/unique pair constraints; existing products, accounts, stock, orders and approvals are preserved. The CampusHubUser relation follows the existing unmanaged user-table pattern (`db_constraint=False`). Other installations must run `python manage.py migrate` from `backend/core` using their virtual environment before opening the updated workspace. No dependency package was added.

### 7. Tests performed and manual verification

- Django: 110 tests passed across mobile seller workspace/application, live bundle suggestions, bundle inventory, admin orders and inventory monitoring. After the final saved-card query optimization, all seven workspace tests passed again. Logs: `scratch/mobile-navbar/seller-workspace-django.log` and `seller-workspace-final-django.log`.
- `manage.py check`: no issues. `makemigrations --check --dry-run`: no changes detected.
- Flutter: 37 tests passed across seller drawer/workspace/application, existing Profile and regular bottom navigation. The optional screenshot case returns without capture when `SELLER_REVIEW_DIR` is absent; a separate enabled capture run passed and its three PNGs were inspected. Log: `scratch/mobile-navbar/seller-workspace-flutter.log`.
- Targeted Dart analysis of eleven edited source/test files: no issues. The earlier two test-only missing-brace lint notices were corrected. Log: `seller-sidebar-analysis.log`.
- Normal `lib/main.dart` Android debug APK built successfully (`assembleDebug`, 45.7s). Output: `campushub/build/app/outputs/flutter-apk/app-debug.apk`; log: `seller-sidebar-build.log`. It was not installed on the physical phone for an approved-seller live-flow test.
- Unauthenticated HTTP request to the running workspace endpoint returned 401 as expected. No real seller application or fake live sale was created for testing.
- A later final catalog smoke check could not connect: port 8000 had no listener and loopback returned WinError 10061 (connection refused). This is a confirmed stopped-server condition at handoff, not evidence that catalog endpoints returned application errors. Start the existing Django development configuration before live mobile testing; the database/API automated checks above ran independently of that listener.
- Widget PNGs: `scratch/seller-sidebar/seller-overview.png`, `seller-drawer-top.png`, `seller-drawer-bottom.png`. These contain isolated test data, not live catalog claims. Drawer tests cover 375×812, 320×812 at 2× text and 844×390 at 2× text.

Manual steps: sign in with an actually approved active seller; Profile → Seller Dashboard; open every drawer destination and verify only that seller's products/orders appear. Open My Products → Add Product and use existing validation; cancel without creating test live records if only checking UI. Confirm variant inventory and derived bundles match web Inventory. Change Sales Analytics period, inspect loading/empty/error states and existing Profile/Settings. Back to CampusHub must select Home with the same account and five tabs. A pending/suspended account must not get seller content. With genuine qualifying pairs, test View/Save/Dismiss/Remove and confirm none changes inventory or creates a Product bundle.

### 8. Troubleshooting and remaining limitations

- Inventory, My Bundles, Orders and Sales Analytics are functional read-only seller screens. This change does not introduce stock adjustment, order processing/payment writes or a bundle-creation editor; the existing Add Product flow remains reused. Saved suggestion actions persist preferences only.
- The current checkout stores one sellable product per order, and ambiguous legacy multi-item JSON is excluded from mobile seller access. Existing Apriori therefore commonly returns no qualifying real basket pairs. The UI shows the honest empty state; it never invents baskets from buyer/date/component recipes or substitutes synthetic CSV rows. A genuine multi-item order contract would be a separate project change.
- AuthUser currently exposes no uploaded profile-photo field. The drawer preserves the existing default avatar and actual identity fields; it does not fabricate a photo. Existing Messages/Notifications remain subject to their current implementation and chat-service availability.
- If access expires, sign in again. For 403, check actual approved/non-suspended SellerRequest and account state rather than editing Flutter to bypass the guard. A missing choice-table error means run migration 0041. For connection failures, use `docs/mobile-product-loading.md`; no firewall or networking rules were weakened here.
- Order data is paginated at 30 rows; product/inventory reads still load the current seller's complete catalog. A larger seller catalog may need future pagination. Native live account/device workflow remains unverified; automated/widget/build evidence above is the current verification boundary.

### Safe learning exercise

In `campushub/test/seller_test_fixtures.dart`, change only a fixture product label and its matching expectation, then run `flutter test test/seller_workspace_test.dart` from `campushub`. Check that the Products/Inventory/Orders screens use the intended response fields and that Home-return/session checks pass. Restore the fixture edit afterward. Never add those fixtures to `lib/`, a migration, or the live database. To capture the actual widget layout, set `SELLER_REVIEW_DIR` to a local scratch folder and run the `capture seller` test; inspect top and bottom drawer PNGs for clipping at the selected text scale.

---

Updated October 18, 2026. This replaces the earlier Student-ID-only application guide and covers the user-approved larger scope: complete applications and extend mobile product ownership without another user account.

## Cause / reason

The earlier form used a public Student-ID-based contract and six fixed product choices. It did not bind the submission to authenticated identity, store the new confirmations, support revisions or connect mobile users to Product ownership. Inspection confirmed that existing mobile CampusHubUser and Django accounts.User live in separate tables; Product previously required the latter.

The new flow reads the signed-in account on Django, collects selling details and confirmations, reviews before submission, then saves a pending SellerRequest. Approval grants access to that same account. Application submission never creates products. Only approved sellers can submit actual listings for normal marketplace review.

## Required implementation report

### 1–3. Changed folders/files, current lines and nearby anchors

Paths are relative to the project root. Line numbers are approximate current locations; search the anchor after later edits. Existing unrelated workspace changes are outside this report.

| File | Line / anchor | Change / expected behavior |
| --- | --- | --- |
| `campushub/lib/module_app/screens/profile_page.dart` | 63 `_refreshSeller`; 84 `_openSeller`; 324 `favoritesOnly`; 376 seller menu | Server-driven Apply to Sell/status/Seller Dashboard; refresh on return to retained tab; existing Favorites/Cart reused. |
| `campushub/lib/module_app/screens/seller_application_page.dart` | 9 `SellerApplicationPage`; 141 `SellerApplicationTheme` | Supplied introduction/Start; scoped Montserrat/navy/gold/white, requested light page background, variable font weights and compact 14dp buttons. |
| `campushub/lib/module_app/screens/seller_application_form.dart` | 82 `_load`; 171 `_submit`; 436 `_statusPanel`; 538 `_review` | Applicant → Selling → Terms → Review; saved application/status, revision edit/resubmit and honest connection errors. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 8 `SellerDashboardPage`; 32 `_load`; search `My Products` | Recheck approval, load own products and open existing Add Product sheet; correct category/status separator. |
| `campushub/lib/module_app/services/seller_application_service.dart` | 17 `_headers`; 31 `status`; 52 `submit`; 74 `products`; 90 `createProduct` | Existing bearer token/endpoints; only reads may fail over; no automatic POST retry after timeout. |
| `campushub/lib/module_app/screens/products_screen.dart` | 20 `favoritesOnly`; 165 `sellerRef`; 409 `_submit`; `showAddProductSheet` | Reuse browsing/Favorites/product form, actual category options and seller authorization. |
| `campushub/lib/module_app/services/product_service.dart` | 167 `submitProduct` | Shared authenticated product transport. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 423 `active`; 933 `sellerRef` | Preserve tab state/refresh and actual owner reference. |
| `campushub/lib/module_app/models/product_item.dart` | 80 `seller_ref`; 103 `sellerRef` | Preserve mobile/web identity namespace. |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 158 `sellerRef`; 383 `participantActorKey` | Actual seller identity in existing chat/presence. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 138 `sellerRef` | Forward owner reference from Home. |
| `backend/core/modules/marketplace/services/seller_applications.py` | 13 `applicant`; 31 `latest`; 45 `categories`; 50 `snapshot`; 58 `public_application`; 72 `state`; 86 `submit` | Shared auth, profile/options, validation, snapshot, duplicate protection and revision reuse. |
| `backend/core/api/models.py` | 67 `owner_ref`; 91 `mobile_seller`; 150 `owner`; 158 `owner_key`; 296 `SellerRequest`; 390 `request_revision` | Exactly one existing web/mobile Product owner; linked applicant, confirmations/snapshot, revision status/notes. |
| `backend/core/api/views.py` | 324 seller serialization; 689 `seller_submit_product`; 1202/1209 application endpoints; 1301/1318 review; 849 admin product save | Reuse routes, authenticated applications/own products, locked approval checks and actual owner serialization/admin editing. |
| `backend/core/accounts/academic.py` | 87 `scope_seller_requests`; `product_academic` | Existing Program/Major rules cover linked mobile applicants/owners; validated snapshot supports missing profile affiliation. |
| `backend/core/accounts/user_management.py` | 101 `seller_request_for`; search `mobile:` | Exact linked application lookup and status labels, with unambiguous legacy fallback. |
| `backend/core/accounts/activity_logging.py` | 86 `log_seller_event` | Existing audit attributed to actual mobile applicant. |
| `backend/core/accounts/views.py` | 190 owner joins; 239 `approved_mobile_sellers`; 923 row lock | Existing seller/admin owner choices, order audit and PostgreSQL-safe locking. |
| `backend/core/accounts/export_service.py` | 164 owner joins; 188 `owner_key`; `application_data` | Real owner/application fields in existing exports; mixed owner keys remain collision-safe. |
| `backend/core/modules/marketplace/services/inventory.py` | 519 `build_inventory_table` | Existing inventory calculations, actual owner labels/keys and eager loading. |
| `backend/core/modules/marketplace/services/inventory_monitor.py` | 38 `mobile_seller_id`; 84 mobile sellers | Existing Inventory filter supports actual mobile owners. |
| `backend/core/modules/marketplace/services/orders.py` | 200 owner joins; `product.owner` | Existing order table uses real owner without repeated owner queries. |
| `backend/core/modules/marketplace/services/bundles.py` | 51 `eligible_component`; 165 `probe` | Complete owner-key validation; exact component/variant stock stays authoritative. |
| `backend/core/modules/marketplace/services/analytics.py` | 381 approved mobile IDs; 390 `_seller_performance` | Real approved mobile owners included in existing completed/paid analytics. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py` | 122 order query; 134 `owner_key` | Existing live Apriori uses real orders/products/owners, without synthetic fallback. |
| `backend/core/modules/marketplace/services/recommendation.py` | 62 owner joins | Existing recommendation owner loading. |
| `backend/core/modules/reports/reporting.py` | 214 Product query; `product.owner` | Reports retain actual owner display. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_sellers.html` | 40 Needs Revision; 57 View Application; 65 Request Revision | Existing review page shows submitted information and revision action. |
| `backend/static/components/js/admin_sellers.js` | search `revision` | Existing prompt collects applicant-visible revision notes. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 127 `owner_key`; 378 mobile owners | Actual owner table values and approved owner options. |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 48 mobile owners | Existing seller filter supports mobile owner references. |
| `backend/core/api/migrations/0038_seller_application_mobile_owner.py` | `operations` | Compatible owner/application fields and status choices. |
| `backend/core/api/migrations/0039_seller_owner_constraints.py` | `operations` | One owner per Product; one active application per linked mobile account. |
| `backend/core/api/test_mobile_seller_application.py` | 12 test class | Auth/identity, validation, duplicate/revision, ownership/inventory and bundle boundaries. |
| `backend/core/accounts/test_user_management.py` | search `access-request` | Existing test now uses authenticated application contract. |
| `backend/core/modules/marketplace/test_inventory_monitor.py` | 281 migration test | Restore current migration leaves; historical test setup handles legacy email-verification column. |
| `backend/core/modules/marketplace/test_program_inventory.py` | 207 migration test | Use historical models for historical assertions and restore current schema. |
| `backend/core/modules/marketplace/test_bundle_suggestions.py` | 148 access tests | Required unmanaged tables created only inside isolated test database. |
| `campushub/test/seller_application_test.dart` | `testWidgets` | Form/status/auth/transport/tab refresh and responsive coverage; optional screenshots. |
| `campushub/test/product_item_test.dart` | `seller_ref` | Namespaced mobile owner parsing. |
| This guide; `CAMPUSHUB_CONTEXT.md` | current seller note | Current contract, data flow, verification, debugging and learning exercise. |

### 4. Existing models/controllers/routes reused

Reuse CampusHubUser, accounts.User, SellerRequest, Product, Inventory SKU/stock services, academic master data, existing audit and scoped administrator review. No second user, Store/Seller model, auth system, stock calculation or approval API.

Inspection found Navigator/MaterialPageRoute, PageController and retained tabs rather than GetX. Preserve those existing Flutter mechanisms.

Existing routes remain in `backend/core/core/urls.py:226`:

| Method / endpoint | Input → output |
| --- | --- |
| GET `/api/seller/access-status/` | Authenticated identity → actual application or `none`, approved access, applicant/category/program/major options. Query Student ID cannot select another person. |
| POST `/api/seller/access-request/` | Editable application fields/three confirmations → 201 new pending, 200 revision, 400 invalid, 401/403 unauthorized, 409 active duplicate. |
| GET `/api/seller/products/submit/` | Authenticated approved seller → its own real products. |
| POST `/api/seller/products/submit/` | Existing product payload/approved seller → actual owned Product, pending marketplace approval. Existing web-manager privileges preserved. |

Reuse `marketplace_approve_seller_request` and `marketplace_reject_seller_request`; Request Revision posts to the latter with `decision=needs_revision`.

### 5. Fields implemented

- Applicant: server name, Student/User ID and email; existing Program/Major read-only, missing affiliation chosen from real master records; applicable Major; optional Year/Section; required contact.
- Selling: real category, required multiline Products Intended to Sell, optional reason. No Store fields or actual product creation.
- Supporting requirement: hidden because no mandatory upload policy exists; review says Not required. No invented verification/upload claim.
- Terms: accuracy, marketplace rules and administrator approval; all true on client/backend, stored with server timestamp. No existing Terms document URL was found, so no fake link.
- Review: real values, Edit Application and final Submit. Only a successful write produces Application Submitted/Pending Review.

### 6. Status logic

No application → introduction/form without rejection. Pending → Pending Review; Approved → Seller Dashboard; Rejected → actual reason; Needs Revision → notes/edit/resubmit on the same record. Approved-but-suspended stays denied. Connection errors remain Retry/status-check states, never fake rejection/approval.

### 7. Duplicate prevention

`submit()` locks the existing account in a transaction before latest-application lookup. Pending/approved returns 409; Needs Revision updates the same row. PostgreSQL also enforces `one_active_mobile_seller_request` for linked mobile pending/needs_revision/approved applications. Existing web accounts use the account lock/lookup. UI disabling complements server checks. Sequential duplicates were tested; no separate multi-process load test was run.

### 8. Marketplace Admin approval

Existing management permission and Program/Major scoping still guard review; existing Super Admin authority remains. The Sellers page shows actual mobile applicant information and revision action. Approve/Reject/Request Revision only operate on pending requests, use existing audit, and require applicant-visible reason for revision.

### 9. Seller/profile activation

Approval updates SellerRequest, not User role/account type. It creates no duplicate account or product. Active, approved, unsuspended access enables Seller Dashboard. Profile refreshes after the flow and when returning to its retained tab.

### 10. Add Product authorization

Dashboard and product POST both check access; POST rechecks the locked application against review/suspension. Store exact authenticated owner in `Product.mobile_seller` or the existing web `Product.seller`. `owner_key` preserves integer web IDs and namespaces mobile IDs as `mobile:<id>`; equal numeric IDs cannot become the same seller. `owner_ref` uses existing chat identities `admin:<id>`/`mobile:<id>`.

New mobile listings remain Pending until existing product approval. Existing Product.save/Inventory services handle stock. Variants, reservations and bundle components retain their established calculations. Same-seller bundle checks use the full owner key. The mobile entry reuses the existing single-product form; it does not add variant/bundle editors.

### 11. Backend/API behavior, functions and data flow

```text
Existing sign-in token → _headers() → applicant(): verify active regular account
  → state(): actual profile/options/application
  → Applicant / Selling / Terms / Review (no write)
  → submit(): validate → lock account → create/update SellerRequest → existing audit
  → scoped admin review → approved access on same account
  → guarded Product submission → exact owner → existing stock/product approval
  → existing orders, reports, exports and real recommendation calculations
```

`snapshot(account)` returns authenticated display identity/academic data. `public_application(item)` returns saved applicant-facing fields. `categories()` returns distinct nonblank unarchived Product categories: this implementation has no separate category master. `resolve_academic()` validates actual Program/Major relationships. Client-sent identity/name never replaces server identity.

Annotated test-only example: a real-account fixture selects an existing category, describes intended products and checks three confirmations. Review writes nothing. Submit saves its account reference and validated snapshot. Admin approval enables Product submission; its Product references that existing account directly and gets normal Inventory SKU stock. Spoofing another name/ID in the request body cannot change the owner.

Confirmed regression causes: PostgreSQL rejects unrestricted SELECT FOR UPDATE across nullable owner outer joins. Affected existing operations now use `select_for_update(of=("self",))` to lock the business row. Historical migration tests left older schemas behind; cleanup now restores current graph leaves and assertions use historical model states. These were observed test failures, not guesses.

### 12. Database/migrations

Migrations api.0038 and api.0039 are **applied locally**. Existing web Product owners stay intact; new nullable owner column plus constraint requires exactly one owner. New snapshot/notes default empty. Existing unmanaged mobile table is reused with `db_constraint=False` relationships; no duplicate account table. Verification inserted no live sample users/products/applications.

### 13. Commands/deployment

Local migrations already ran successfully. On another environment, back up its database, inspect the plan and apply checked-in migrations:

```powershell
& backend/core/venv/Scripts/python.exe backend/core/manage.py migrate --plan
& backend/core/venv/Scripts/python.exe backend/core/manage.py migrate
& backend/core/venv/Scripts/python.exe backend/core/manage.py check
```

Restart Django. Install the rebuilt `campushub/build/app/outputs/flutter-apk/app-debug.apk` on the phone; source hot reload does not update a separately installed APK. The phone must reach the configured Django LAN address; sign in again if its token expired. No new environment variable, SMTP provider or dependency.

### 14. Tests/results

| Verification | Actual result |
| --- | --- |
| Django `test api.test_mobile_seller_application modules.marketplace accounts.test_marketplace_support accounts.test_user_management accounts.test_data_exports --noinput --keepdb` | 214 passed, 59.031s; `scratch/mobile-home/seller-all-verified.log`. |
| Final export/order regression after eager-loading changes: `test accounts.test_data_exports modules.marketplace.test_orders_admin --noinput` | 22 passed, 6.930s; `scratch/mobile-home/seller-export-order-final.log`. |
| Flutter `flutter test test/seller_application_test.dart test/profile_academic_test.dart test/dashboard_search_appbar_test.dart test/dashboard_header_test.dart test/home_page_test.dart test/product_item_test.dart --reporter expanded` | 27 passed; `scratch/mobile-home/seller-mobile-final.log`. |
| Targeted Dart analysis, 13 changed source/test files | No issues found. |
| Django check / makemigrations check | No issues / no changes detected. |
| showmigrations api | 0038 and 0039 applied. |
| `flutter build apk --debug --target lib/main.dart` | Debug APK built; `scratch/mobile-home/seller-apk-final.log`. |
| Intro/applicant/review/submitted PNG inspection | Production widgets with isolated mock responses, inspected in `scratch/mobile-home/seller-review`. |

Flutter tests cover no early POST, confirmations/review, exact authenticated payload, existing statuses, errors, single POST attempt, Profile refresh, owner parsing and 320px/2x, 375px and landscape layouts. Django tests cover identity/auth, validation, duplicates/revision reuse, approval without role replacement, pending/suspended denial, exact ownership, Inventory/admin approval and bundle boundaries.

The last category/status separator correction is presentation-only; the APK was rebuilt afterward. No physical-phone end-to-end run, live application/admin approval/email delivery, separate concurrency load test or full repository-wide suite was performed. Automated data stayed in test databases/mocks.

## Manual verification

1. Authorized test regular account with complete profile → Profile → Apply to Sell → Start. Name/ID/email read-only, no rejection/status and no request saved yet.
2. Inspect actual categories/academic choices. Missing BTLED Major/contact/intended-products/confirmations should prevent progression/submission. Existing affiliation stays read-only.
3. Review → edit → review → submit once. Expect Application Submitted/Pending Review, View Application, Back to Marketplace; no Product created.
4. Web scoped Sellers → View Application → Request Revision with notes. Refresh mobile, edit/resubmit and verify the same application ID.
5. Approve through existing admin action. Return to Profile → Seller Dashboard → Add Product. Verify exact owner, Pending Review in My Products and existing Inventory stock. Product browsing requires normal product approval.
6. Suspend seller access using existing authorized controls. Refresh and verify Product submission is denied. Restore only if authorized; ordinary account access follows existing policy.
7. Inspect existing web/mobile product owners, stock/orders/reports/bundle boundaries and seller chat. Clean up only your own disposable test data through approved workflows.
8. Disconnect Django and retry status: connection guidance, not rejection. If submission times out, check actual state/My Products before repeating.

## Troubleshooting and remaining limitations

| Symptom | Check / expected behavior |
| --- | --- |
| 401 / sign in again | Existing bearer missing/expired. Reauthenticate; do not restore public Student-ID lookup. |
| Empty category choices | Categories depend on actual unarchived catalog data. Configure genuine data, not hardcoded samples. Empty catalog cannot currently supply an application category. |
| Missing scoped application | Check exact linked identity, management permission and Program/Major/snapshot scope; do not widen permissions. |
| Duplicate 409 | Reload the active application rather than submit again. |
| Product 403 | Current approval/suspension/account eligibility failed; UI visibility is not authorization. |
| Unknown POST result | Timeout may follow a save; no automatic retry. Refresh actual state. |
| Old app cannot submit | Install this source/APK and sign in. Old public-ID contract is intentionally retired. |

Seller Dashboard currently provides My Products/Add Product, not a new mobile seller order/inventory/bundle-management suite. Supporting-upload policy and formal Terms URL are not configured. Rejected applications show their reason; mobile edit/resubmit is for Needs Revision, not an invented rejection policy. No new push/email notification delivery; refresh reads existing backend review. Existing audit/admin notification behavior is reused. The seller theme follows this request's #F7F8FC background; global white Home remains unchanged.

## Safe learning exercise

In `seller_application_test.dart`, change a mock pending state to needs_revision and add applicant-visible notes. Run the test and observe the different panel/button. Keep the mocked application ID fixed through resubmit; verify one POST and Pending Review. Restore the fixture. Then return a 503 status response: Retry should appear without rejection or a blank application form. This teaches service response → widget state → user action without changing real accounts.

For backend practice, read `submit()` in this order: identity → validation → account lock → duplicate/revision decision → snapshot → audit. Add an assertion in the existing isolated test that a spoofed client name is ignored, run `test api.test_mobile_seller_application`, then restore your exercise edit. The server owns identity; the form supplies only editable application information.

---

## Seller Dashboard Overview Metric & UI Update - October 19, 2026

### 1. Cause / Reason
The seller dashboard previously showed an `Active Products` card alongside `Total Sales`, `Total Orders`, and `Pending Orders`. The design required updating this third card to `Completed Orders` with modern university-institutional UI:
- Distinctive outline iconography in the top-right corner of each card (`Iconsax.wallet_2_copy`, `Iconsax.bag_2_copy`, `Iconsax.tick_circle_copy`, `Iconsax.clock_copy`).
- Clear visual hierarchy with a 13pt slate-gray label (`HomeAppColors.secondaryText`), rounded 16dp container corners, subtle border (`HomeAppColors.border`), and bold 22pt navy metric numbers (`HomeAppColors.navy`).
- Accurate real data derivation from database records (`orders.filter(status=MarketplaceOrder.STATUS_COMPLETED).count()`).

### 2. Exact Files & Current Lines
| File | Line Anchor | What Changed |
| --- | --- | --- |
| `backend/core/modules/marketplace/mobile_seller_views.py` | L13, L99 (`workspace`) | Imported `MarketplaceOrder`; added `"completed_orders": orders.filter(status=MarketplaceOrder.STATUS_COMPLETED).count()` to the `overview` dictionary. |
| `backend/core/api/test_mobile_seller_workspace.py` | L216 (`test_overview_counts_are_actual_and_owner_scoped`) | Updated assertion to verify `completed_orders: 1` derived from owner-scoped orders. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | L2, L70, L740, L818, L965 | Imported `iconsax_flutter`; added thousands separator in `money()`; replaced `Active Products` with `Completed Orders`; introduced `_overviewMetricCard()` and `_SellerOverviewMetric`. |
| `campushub/test/seller_test_fixtures.dart` | L72 (`sellerWorkspaceFixture`) | Added `'completed_orders': 2` to the mock fixture overview. |
| `campushub/test/seller_workspace_test.dart` | L21, L461 | Updated test expectations from `'Active Products'` to `'Completed Orders'`, and asserted presence of the 4 card icons. |

### 3. Changes Made & Expected Behavior
1. **Metric Cards Replaced**: The third overview card is now `Completed Orders` instead of `Active Products`.
2. **Icons Added**:
   - `Total Sales`: Wallet icon (`Iconsax.wallet_2_copy`)
   - `Total Orders`: Shopping bag icon (`Iconsax.bag_2_copy`)
   - `Completed Orders`: Checkmark in circle icon (`Iconsax.tick_circle_copy`)
   - `Pending Orders`: Clock/timer icon (`Iconsax.clock_copy`)
3. **Card Container Styling**:
   - 16dp border radius, crisp white background, subtle border (`#E2E8F0`).
   - Top row displays the metric title on the left and the matching navy icon on the right.
   - Large bold 22pt navy font for metric values.
4. **Data Integrity**: Uses backend-calculated completed order counts derived from `MarketplaceOrder.STATUS_COMPLETED` with owner scoping.

### 4. Functions & Data Flow
1. **Backend**: In `mobile_seller_views.py` `workspace()`:
   - `orders = seller_order_queryset(account)` scopes orders to the authenticated mobile seller.
   - `completed_orders = orders.filter(status=MarketplaceOrder.STATUS_COMPLETED).count()`.
   - Included in JSON response under `overview.completed_orders`.
2. **Frontend Flutter**: In `seller_workspace_content.dart` `homeHighlights()`:
   - Extracts `overview['completed_orders'] ?? analytics['completed_orders'] ?? 0`.
   - Passes to `_overviewMetricCard` with `Iconsax.tick_circle_copy`.
   - `_overviewMetricCard` renders a responsive, accessible card with Poppins typography adhering to the strict 3-color palette (Navy, Light/White, Accent).

### 5. Backend / API Behavior
- Endpoint: `GET /api/seller/workspace/`
- Response `overview` object:
  ```json
  {
    "active_products": 2,
    "completed_orders": 35,
    "pending_orders": 3
  }
  ```
- Maintains backward compatibility: `active_products` is retained in the payload for existing integrations while `completed_orders` is provided for the dashboard.

### 6. Database / Migration Impact
- **Zero migration impact**: Queries existing indexed `status` column on `MarketplaceOrder`. No schema changes.

### 7. Tests Performed
- Backend unit tests: `python backend/core/manage.py test api.test_mobile_seller_workspace` (11 tests passed in 1.49s).
- Mobile unit/widget tests: `flutter test test/seller_workspace_test.dart` (10 tests passed).
- Regression suite: `flutter test test/widget_test.dart test/seller_drawer_test.dart test/seller_home_entry_test.dart test/order_summary_test.dart` (20 tests passed).

### 8. Remaining Limitations & Safe Learning Practice
- **Remaining Limitations**: The dashboard cards reflect seller-scoped completed orders. Cancelled and refunded orders are excluded from completed orders.
- **Safe Learning Practice**:
  1. Open [seller_workspace_content.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_workspace_content.dart).
  2. Inspect `_overviewMetricCard`: observe how `Row` aligns `title` with `Icon` and how `ProfileStyle.text` applies `Poppins` typography with institutional navy `#1A1851`.
  3. Run `flutter test test/seller_workspace_test.dart` in terminal to verify that changes to metric labels or icons are properly caught.

---

## Add Product Mobile All-White Theme Update - October 19, 2026

### 1. Cause / Reason
The mobile `SellerAddProductPage` previously had its Scaffold background set to `const Color(0xFFF7F8FC)` (a light grayish tint), creating gray margins and gutters around the form elements. The design requirement is to make the entire Add Product mobile interface pure white (`Colors.white`) instead of gray, providing a clean, institutional, distraction-free aesthetic.

### 2. Exact Files & Current Lines
| File | Line Anchor | What Changed |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | L247, `_section` | Added `border: Border.all(color: _line)` to `BoxDecoration` to give sections clean card boundaries on the white page. |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | L275, `_images` | Added `backgroundColor: Colors.white` to `OutlinedButton.styleFrom` for the image upload button. |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | L342, `build` | Added `scaffoldBackgroundColor: Colors.white` to the scoped `ThemeData`. |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | L363, `Scaffold` | Changed `backgroundColor: const Color(0xFFF7F8FC)` to `backgroundColor: Colors.white`. |

### 3. Changes Made & Expected Behavior
1. **Scaffold Background**: Changed from `#F7F8FC` to `Colors.white`.
2. **Theme Configuration**: Explicitly sets `scaffoldBackgroundColor: Colors.white` in the `ThemeData` override.
3. **Card Section Outlines**: Added `border: Border.all(color: _line)` so sections maintain institutional visual separation without relying on gray background contrast.
4. **Action Buttons**: Ensured `OutlinedButton` (Add Image) uses a crisp white background.

### 4. Functions & Data Flow
- `SellerAddProductPage.build()` sets up the white `Theme` and `Scaffold`.
- The child `SingleChildScrollView` renders pure white background from top to bottom.
- Inputs, dropdowns, buttons, and sections render against white with disciplined 1px borders (`#E8EAF0`) and navy `#1A1851` text.

### 5. Backend / API Behavior
- No API changes. Product validation and `/api/seller/products/submit/` submission behavior remain unchanged.

### 6. Database / Migration Impact
- **Zero database impact**. No migrations or schema adjustments.

### 7. Tests Performed
- `flutter test test/seller_add_product_page_test.dart` (9/9 tests passed in 5s).
- `flutter test test/seller_workspace_test.dart test/widget_test.dart` (13/13 tests passed).

### 8. Remaining Limitations & Safe Learning Practice
- **Safe Learning Practice**:
  1. Open [seller_add_product_page.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_add_product_page.dart).
  2. Inspect line 363: see how `Scaffold(backgroundColor: Colors.white)` sets the surface color.
  3. Run `flutter test test/seller_add_product_page_test.dart` to verify that layout and keyboard scrolling continue to pass cleanly.

---

## Add Product Form Refinements: Category Dropdown, Deferred Validation, Centered Header, Tags, and Inventory Stock Fields

### 1. Cause / Reason
- The category dropdown previously used a verbose "Product Category" label, and premature validation was triggered when users simply tapped or focused into input fields (e.g. Description), generating red error alerts before the form was even submitted.
- The AppBar title was not centered, violating the centered brand header pattern.
- Section headers and field labels contained redundant occurrences of "Product" (e.g. "Product Information", "Product Images", "Product Price", "Product Description"), causing visual clutter. Per user instruction, only `'Product Name *'` should retain the "Product" qualifier.
- Sellers needed an optional tags input (`Tags (Optional)`) and a dedicated `Low Stock Threshold (Optional)` input below the stock field, with `Available Quantity` renamed to `Stock *`.

### 2. Exact Files Changed
- [backend/core/api/views.py](file:///c:/Users/leste/Desktop/CAMPUSHUB/backend/core/api/views.py#L323-L335): Line ~328, updated `seller_submit_product` view to receive and parse `tags` (as list or comma-separated string) and persist to `Product.tags`. `low_stock_threshold` was already supported by `validate_low_stock_threshold`.
- [campushub/lib/module_app/services/product_service.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/services/product_service.dart#L25-L45): Line ~29, added `lowStockThreshold` (`int?`) and `tags` (`String?`) arguments to `submitProduct`, including them in the JSON payload sent to `/api/seller/products/submit/`.
- [campushub/lib/module_app/screens/seller_add_product_page.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_add_product_page.dart#L32-L560):
  - Centered AppBar title (`centerTitle: true`).
  - Added `_tags` and `_lowStockThreshold` `TextEditingController` instances.
  - Added `bool _submitted = false;` to defer validation until the user explicitly taps "Submit for Approval". `autovalidateMode` on `Form` is set to `_submitted ? AutovalidateMode.onUserInteraction : AutovalidateMode.disabled`. Tapping on labels or inputs no longer prematurely flashes red validation errors.
  - Cleaned section headers to `'Information'`, `'Images'`, and `'Review'`.
  - Renamed `'Product Category *'` to `'Category *'`, simplified dropdown with hint `'Select category'` and keyboard arrow dropdown icon.
  - Retained `'Product Name *'` as requested.
  - Renamed `'Product Description *'` to `'Description *'`.
  - Added `'Tags (Optional)'` input field (`ValueKey('product-tags')`).
  - Renamed `'Product Price (₱) *'` to `'Price (₱) *'`.
  - Renamed `'Available Quantity *'` to `'Stock *'`.
  - Added `'Low Stock Threshold (Optional)'` directly below Stock (`ValueKey('product-low-stock-threshold')`).
- [campushub/test/seller_add_product_page_test.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/test/seller_add_product_page_test.dart#L125-L460): Updated widget tests to reflect refined section titles, streamlined labels, and empty category message.
- [campushub/test/seller_workspace_test.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/test/seller_workspace_test.dart#L620-L630): Updated section header assertion from `'Product Information'` to `'Information'`.

### 3. How It Works
1. **Deferred Validation**: The `_submitted` flag starts as `false`. `Form.autovalidateMode` remains `AutovalidateMode.disabled`. When the user taps submit (`_submit()`), `setState(() => _submitted = true)` activates `AutovalidateMode.onUserInteraction`. Any missing or invalid field then displays red error text and outline. Focusing or tapping fields beforehand no longer triggers annoying premature alerts.
2. **Category Selection**: The `DropdownButtonFormField<String>` provides a clean dropdown with white menu surface (`dropdownColor: Colors.white`), displaying university-standard navy options.
3. **Tags & Low Stock Threshold**: Optional fields parse cleanly without blocking submission if left empty. Tags are passed through to the backend JSON field, while low stock threshold validates as an integer $\ge 0$ when provided.

### 4. Verification Results
- `flutter test test/seller_add_product_page_test.dart`: 9/9 tests passed in 14s.
- `flutter test test/seller_workspace_test.dart`: 10/10 tests passed in 23s.
- `python manage.py test api.test_mobile_seller_workspace`: 11/11 tests passed in 2.3s.

### 5. Safe Practice Exercise
1. Open [seller_add_product_page.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_add_product_page.dart#L420-L425).
2. Examine `autovalidateMode: _submitted ? AutovalidateMode.onUserInteraction : AutovalidateMode.disabled`.
3. Run `flutter test test/seller_add_product_page_test.dart` from `campushub` folder to verify that validation remains strictly deferred until form submission.

---

## Add Product: Category Menu Below Field + Required Low Stock Threshold

### Cause (confirmed)
- `DropdownButtonFormField` is a Flutter widget that always opens its menu **on top of the button itself**, lined up with the selected item. So the open menu covered the `Category *` label.
- The Low Stock Threshold was marked optional, but the admin web form (`admin_products.html`, line ~457) treats it as required and shows a caution message.

### What changed
File: `campushub/lib/module_app/screens/seller_add_product_page.dart`
- Line ~36 (`_lowStockThreshold`): the controller now starts with `'5'`, the same as the backend default `CAMPUSHUB_LOW_STOCK_THRESHOLD` used in `modules/marketplace/services/inventory.py` → `low_stock_threshold()`.
- Line ~81 (`_validateLowStockThreshold`): an empty value now returns `Low stock threshold is required.`.
- Line ~182 (new `_showCategoryMenu`): finds where the field is on screen (`RenderBox.localToGlobal`). Then it calls `showMenu` with a `RelativeRect` that starts 4px **below** the field and is exactly as wide as the field. The chosen value updates `_category` and the `FormFieldState`.
- Line ~446 (`Category *`): the dropdown was replaced with `FormField<String>` → `InkWell` (key `product-category`) → `InputDecorator`. The validation message `Select a category.` and the deferred validation from the previous change both still work.
- Line ~557 (`Low Stock Threshold *`): `(Optional)` was removed. Helper text added under the field: *You will be alerted when your stock reaches this quantity or lower.*

Data flow: tap the field → `_showCategoryMenu` → `showMenu` returns the chosen string → `setState(_category)` → `state.didChange` → `validator` checks `_category`. On Submit, the threshold text → `int.tryParse` → `ProductService.submitProduct(lowStockThreshold:)` → `POST /api/seller/products/submit/` → `validate_low_stock_threshold` → `Product.low_stock_threshold`.

### Backend / Database
- No backend or database change. The server still accepts a missing threshold from other clients and then uses the default of 5. Mobile now always sends a value. No migration.

### Verification
- `flutter test test/seller_add_product_page_test.dart`: 9/9 passed. New checks: the menu's top edge is below the `Category *` label and the field; an empty threshold shows the required error; the caution text is shown.
- `flutter test test/seller_workspace_test.dart`: passed. `dart analyze` on the edited files: no issues.
- Not yet checked on a physical phone.

### Limitations
- If the field is very close to the bottom of the screen (for example, with the keyboard open), Flutter moves the menu up so it stays on screen. The keyboard is closed before the menu opens to make this less likely.
- Error text uses the page theme's `error` color, which is currently navy `#1A1851` (brand palette), not red.

### Safe practice exercise
Change the `+ 4` in `Offset(0, box.size.height + 4)` inside `_showCategoryMenu` to `+ 12`. Run the test file and check that the "perishable expiry" test still passes, because the menu is still below the field. Then change it back.

---

## Add Product: Gold (#FCB315) Caution Modal Popup & Single-Row Image Requirements

### Cause (confirmed)
- The user requested:
  1. "IT SHOULD WHEN PRESS THE CAUTION ICON IT POPUP THE TEXT" — tapping the caution circle icon next to `Low Stock Threshold *` pops up a dedicated modal card containing the caution message inside a brand gold (`#FCB315`) container with navy close button and alert icon, rather than sitting as a static inline block permanently consuming screen space.
  2. "THEN THE UP TO 6 - 5MB TO ONE ROW BEHIND SUPPORTED" — combining the two separate text rows in the images section into a single compact row: `'Supported: JPEG, PNG, WebP, GIF · Up to 6 images · 5 MB'`.

### What changed
File: [campushub/lib/module_app/screens/seller_add_product_page.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_add_product_page.dart)
- Added `_showCautionPopup(BuildContext context)`: Opens an unconstrained, non-overflowing dialog with a `#FCB315` gold container (`key: ValueKey('low-stock-caution')`), navy icon, title "Low Stock Threshold", caution message, and an accessible close button (`key: ValueKey('close-caution-popup')`).
- Simplified the `Low Stock Threshold *` field by removing the inline container. Tapping the caution icon triggers `_showCautionPopup(context)`.
- Replaced the two stacked image helper lines in `_images()` with a single row: `'Supported: JPEG, PNG, WebP, GIF · Up to 6 images · 5 MB'`.

File: [campushub/test/seller_add_product_page_test.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/test/seller_add_product_page_test.dart)
- Updated widget tests to ensure the caution popup is hidden by default, pops up on tapping the caution icon, verifies the message inside the `#FCB315` container, and closes cleanly when dismissed.

### Verification Results
- `dart analyze`: Clean, 0 issues across all screen and test files.
- `flutter test test/seller_add_product_page_test.dart`: 11/11 tests passed in 4s.
- `flutter test test/seller_workspace_test.dart`: 10/10 tests passed in 5s.
- `python manage.py test api.test_mobile_seller_workspace`: 11/11 tests passed in 0.64s.


