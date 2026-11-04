# Mobile seller application and existing-account product ownership

## Approved application wording and one manual phone notification - November 4, 2026

1. **Cause / reason.** The user selected wording that tells an approved applicant what they can do next, then requested a phone notification without visible test wording. The earlier sentence only said that seller access was active.
2. **Exact files changed / current lines and anchors.** `campushub/lib/module_app/screens/seller_application_form.dart:496`, the `'approved'` branch in `_statusPanel()`, replaces that one sentence. `docs/mobile-seller-application.md:3` records this change; `CAMPUSHUB_CONTEXT.md:3` links this report. No backend source or test file changed.
3. **Changes made.** The approved status now says: **Your seller application is approved. You can now add products and submit them for review.** Other statuses and actions keep their existing behavior. One manually sent phone notification used the title **Seller Application Approved** and the exact new sentence, with no visible test label.
4. **How it works / functions, inputs, outputs and data flow.** `SellerApplicationService.status()` reads the authenticated `/api/seller/access-status/` response. `_load()` in `seller_application_form.dart:97` copies its saved status into `_status`. `_statusPanel()` at line 453 selects the corresponding heading and message; only its approved message changed. Its output is Flutter `Text` inside the existing status page. Existing `onSellerApproved` navigation may leave that page in normal Profile navigation. This wording describes seller access while making clear that products still require review.

   ```dart
   // Displayed only by the existing approved-status branch.
   'approved' =>
       'Your seller application is approved. You can now add products and submit them for review.',
   ```

   The separate one-time phone verification read the connected phone's saved account and Firebase installation into memory, matched its active Django device/session binding, confirmed its latest actual seller application was approved and not suspended, then sent the exact source sentence through the existing Firebase configuration. It did not modify a seller application or queue a product review. Credentials, installation IDs and session tokens were not printed or saved.
5. **Backend / API behavior.** No endpoint, permission or approval logic changed. This copy change does **not** connect `SellerRequest.approve()` to automatic push delivery. The manual notification is separate from the status page and from the product approval worker.
6. **Database / migration impact.** None. The phone verification performed read-only application/device queries and sent one external notification. No working record, outbox row, schema or migration was changed by this step.
7. **Tests performed.** `flutter test --no-pub test/seller_application_test.dart --reporter expanded` passed **13 tests**. `flutter analyze --no-pub lib/module_app/screens/seller_application_form.dart` reported **no issues in 31.1 seconds**. These existing widget tests cover saved statuses, submission, refresh, errors and responsive layouts; no new copy-only test was added. Actual phone verification confirmed the approved account, Firebase acceptance and Android receipt of the exact title/body. The received notification had `AUTO_CANCEL|SILENT`; a floating banner was **not verified for this message**. Sanitized evidence: `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261104/push-popup-20261104/seller-application-approved-result.json`. Earlier, the differently worded `CampusHub popup test` message did produce a visually verified floating banner; that does not prove this approval message popped up.
8. **Remaining limitations / troubleshooting / safe practice.** The phone can classify individual messages as unwanted and silence them even with Banners enabled and a HIGH channel. Earlier diagnostics confirmed `tran.harassment=true` on prior suppressed messages; this step confirms the new message's SILENT flag without assuming the exact classification cause. CampusHub's phone Reminder Intensity was changed from AI Reminder to Follow App during the preceding investigation; that alone did not guarantee banners. No APK rebuild, reinstall, hot reload or automatic seller-approval push implementation was performed here. Load the updated Flutter source through the user's normal development run to see the new in-app sentence. Safe exercise: find the approved branch at line 495, identify the literal sentence at line 496, and compare it with the pending/rejected branches. Run the test command above to verify the status flow without changing a real application or sending another notification.

## Seller Home: banner restored below Inventory Alerts - November 4, 2026

This supersedes only the November 2 seller-banner removal below. The banner returns after the inventory-alert content and before Suggested Product Bundles. Sales Overview, Recent Orders, the floating navbar and buyer Home keep their existing placement.

1. **Cause / reason.** The earlier approved-seller Home explicitly hid its top promotional carousel. The user now requested adding the existing banner back below Inventory Alerts. Rendering it again at the top would not satisfy that placement, so Home passes the shared component into the existing seller highlights instead.
2. **Exact files changed / current lines and anchors.** Paths are relative to the project root:

   | File | Current line / anchor | Change |
   | --- | --- | --- |
   | `campushub/lib/module_app/screens/dashboard_screen.dart` | 28 import; 414 `afterInventoryAlerts: CampusHomeBanners` | Create the existing carousel in approved seller Home and connect its existing catalog-tab callbacks and Home-active state. |
   | `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 36 constructor; 49 field; 282 forwarding | Accept an optional `afterInventoryAlerts` widget and pass it into the successful Home-section rendering. Dedicated seller pages receive no new banner. |
   | `campushub/lib/module_app/screens/seller_workspace_content.dart` | 30 constructor; 43 field; 1712 `afterInventoryAlerts` | Render the optional widget after `inventory(attention: true)`, with a 16dp preceding gap, before the existing suggestion heading. |
   | `campushub/test/seller_home_entry_test.dart` | 287 placement/navigation regression; 380 scrolling regression; 718 approval/revocation regression | Check one banner in seller content at three viewport/text-scale combinations, normal slide navigation, the Services action, active-state forwarding and retained workspace state. Replace obsolete seller-banner-absence expectations. |
   | `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md` | This entry / latest seller-banner entry | Record the current placement, implementation, checks and safe exercise. |

3. **Changes made.** Approved sellers see the same campus-photo carousel, captions, gold actions and pagination dots below inventory alerts, including the honest no-alerts state. It remains before Suggested Product Bundles. Buyer Home retains its original top carousel. The existing approved-seller top-banner suppression prevents a duplicate. No banner asset, slide content, styling or shared carousel logic changed.
4. **How it works / functions, inputs, outputs and data flow.** `DashboardScreen.build` already knows the authenticated user, approved seller state and selected root tab. It supplies `CampusHomeBanners(active: _currentIndex == 0)` through `SellerDashboardPage.afterInventoryAlerts` to `SellerWorkspaceContent.afterInventoryAlerts`. The latter is a presentation slot, not a data loader. `homeHighlights(context)` still reads actual workspace inventory and suggestions; the slot is inserted after its inventory output. While seller workspace data loads or fails, its original loading/error/retry branch remains. The carousel keeps its own lifecycle, offscreen and reduced-motion behavior. Browse Products calls `_goToTab(1)`, View Facilities calls `_goToTab(3)` and View Services calls `_goToTab(2)`; the root navbar accounts for its seller Add Product item as before. Leaving Home passes `active: false`, and returning reuses the retained seller workspace.

   ```dart
   // Existing inventory output first; the optional shared banner follows it.
   ...inventory(attention: true),
   if (widget.afterInventoryAlerts != null) ...[
     const SizedBox(height: 16),
     widget.afterInventoryAlerts!,
   ],
   // Existing Suggested Product Bundles heading and records continue below.
   ```

   A widget slot reuses the existing carousel and root navigation callbacks without copying banner rendering into the seller workspace or creating another screen.
5. **Backend / API behavior.** Unchanged. No endpoint, request payload, seller permission, approval calculation, inventory calculation, recommendation workflow or backend source changed. Scrolling to the banner and returning from Services does not trigger an extra workspace reload; the integration test retains one workspace read.
6. **Database / migration impact.** None. No model, migration, working record, analysis execution or database mutation was used for this change. Widget tests use isolated service fixtures.
7. **Tests performed.** **63 Flutter tests passed in 17 seconds** across `seller_home_entry_test.dart`, `seller_home_layout_test.dart`, `home_page_test.dart` and `campus_home_banners_test.dart`. The new root integration checks cover 280dp at 200% text, 390dp and 768dp, banner ordering/containment, exactly one banner, swiping to Services and returning, active-state forwarding and no extra workspace read. Existing tests cover approval/revocation, refresh, Home catalogs, banner callbacks/timing/lifecycle and seller layout. Three actual seller-banner captures were generated; 390dp and 280dp/200% were visually inspected. Whole-app `flutter analyze --no-pub` reported **no issues in 8.7 seconds**; Dart formatting completed. Evidence: `scratch/seller-home-banner-20261104/final-tests.log`, `analyze.log`, `renders/` and `layout-renders/`. Initial checks exposed test-harness issues: decorative dots are not buttons, retained offstage widgets require an explicit finder, and the existing layout captures require their output directory and real fonts. Those were corrected in verification; no unrelated runtime styling was altered to satisfy them.

   Reproduce from `campushub` in PowerShell:

   ```powershell
   $env:SELLER_BANNER_REVIEW_DIR = Join-Path (Get-Location) '../scratch/seller-home-banner-20261104/renders'
   $env:SELLER_HOME_REVIEW_DIR = Join-Path (Get-Location) '../scratch/seller-home-banner-20261104/layout-renders'
   New-Item -ItemType Directory -Force -Path $env:SELLER_HOME_REVIEW_DIR | Out-Null
   flutter test --no-pub test/seller_home_entry_test.dart test/seller_home_layout_test.dart test/home_page_test.dart test/campus_home_banners_test.dart
   flutter analyze --no-pub
   ```

8. **Remaining limitations / troubleshooting / safe practice.** Verification uses actual Flutter widgets and bundled assets with isolated test services, not an installed physical device or a full-project suite. At extreme 280dp/200% text the unchanged shared banner action wraps onto two lines and extends beyond its inset gold decorative paint; this placement change does not redesign that existing component. If the banner is absent, first confirm seller workspace data loaded successfully and restart the current development build after the widget-tree change. Safe exercise: sign in with an already approved seller, scroll below Inventory Alerts, verify one banner before Suggested Product Bundles, swipe to View Services, open it and return Home. Confirm the banner remains in place and no product or inventory was changed. Compare a buyer account: its original top banner remains.

## Current Seller Sidebar: exact Design B mockup matching - November 4, 2026

1. **Cause / reason:** User provided a design mockup screenshot showing the exact seller mobile sidebar layout: `MAIN`, `SELLER TOOLS`, and `MESSAGES` grouped inside pure white rounded cards (`#FFFFFF`, border `#E3E7EF`, 16dp radius), seamless card rows without internal dividers, an active `Home` row with `#F4F5F9` rounded highlight and an inset 3.5dp gold pill indicator (`#FCB316`), exact icons (`Iconsax.home_2_copy`, `Iconsax.category_2_copy`, `Iconsax.chart_21_copy`), a circular avatar with `#F1F5F9` background, navy person outline, and right chevron `>`, and an open `Logout` row directly below a full-width divider with a trailing chevron `>`.
2. **Exact files changed:**
   - `campushub/lib/module_app/widgets/navigation/seller_drawer.dart:13`: updated `_DrawerStyle` with card radius 16dp, indicator width 3.5dp, border `#E3E7EF`, selected surface `#F4F5F9`, chevron color `#A8B1BF`; line 34: configured `SellerDestination` sections (`MAIN`, `SELLER TOOLS`, `MESSAGES`) and exact icons; line 122: updated `_card` to pure white border container without inner divider lines; line 136: updated `_entry` with inset vertical gold pill indicator and non-shifting icon alignment; line 290: updated header with light-gray avatar and chevron `>`; line 395: updated bottom `Logout` as an open row below a full-width horizontal divider with right chevron `>`.
   - `campushub/test/seller_drawer_test.dart:82`: updated assertions for `My Purchases`, `SELLER TOOLS`, and `MESSAGES` groups.
   - `campushub/test/drawer_render_test.dart:60`: updated visual snapshot fixture tests.
3. **Changes made:**
   - Aligned sidebar card layout to the exact visual reference image.
   - Removed inner divider lines within cards for clean, modern cards.
   - Formatted the active item selection indicator as an inset rounded gold pill (`width: 3.5`, `height: 22`, `color: #FCB316`) positioned at `left: 8` within the `#F4F5F9` rounded item background.
   - Refined `Logout` to be an open row below the full-width divider with a trailing chevron.
   - Added trailing chevron `>` to the profile header and set avatar background to `#F1F5F9` with outline user icon fallback.
4. **How it works:**
   - `CampusHubDrawer` renders the user profile header with a trailing chevron.
   - Each section (`MAIN`, `SELLER TOOLS`, `MESSAGES`) renders its section header and a `_card` grouping without internal dividers.
   - `_entry` uses a `Stack` to display the inset gold pill on the active item without shifting leading icon alignment.
   - Below the scrollable area, a full-width divider precedes the `Logout` row.
5. **Backend / API behavior:** Unchanged; no API, database, or backend modifications.
6. **Database / migration impact:** None.
7. **Tests performed:** 59/59 Flutter tests passed across `seller_drawer_test.dart`, `drawer_render_test.dart`, `seller_workspace_test.dart`, `seller_home_entry_test.dart`, and checkout workflows; `flutter analyze --no-pub` reported 0 issues.
8. **Remaining limitations:** UI-scoped change to Flutter mobile drawer.

## Current Seller Sidebar: grouped-card layout (Design B) - November 4, 2026

1. **Cause / reason:** User requested updating the CampusHub Flutter mobile seller sidebar to the grouped-card layout (Design B) with organized sections (MAIN, SELLER MANAGEMENT, COMMUNICATION, and separate BOTTOM Logout), renaming "My Purchases" to "My Orders", pure white background (#FFFFFF), navy text and icons (#0B1F3A), gold indicator (#FCB316) for the active selection, white rounded container groups with subtle borders, right-facing chevrons, and vertical scrolling for smaller devices.
2. **Exact files changed:**
   - `campushub/lib/module_app/widgets/navigation/seller_drawer.dart:13`: added `_DrawerStyle` grouped-card tokens (card radius 12dp, indicator width 3dp, navy #0B1F3A, gold #FCB316, selected surface #F1F5F9); line 34: updated `SellerDestination` sections (`MAIN`, `SELLER MANAGEMENT`, `COMMUNICATION`) and renamed `purchases` label to `'My Orders'`; line 84: updated destinations list; line 122: added `_card` grouped container with white surface, rounded border, and anti-aliased clipping; line 136: updated `_entry` with chevron icons, selected background, and narrow gold left edge indicator; line 230: added uppercase muted section headers; line 290: updated ListView and separate bottom Logout container; line 453: updated `SellerDrawer.drawerDestinations`.
   - `campushub/lib/module_app/widgets/profile/profile_widgets.dart:25`: restored `'Montserrat'` font family for `ProfileStyle.identityText` in adherence to AGENTS.md institutional identity rules.
   - `campushub/test/seller_drawer_test.dart:82`: updated assertions for Design B grouped-card keys, renamed 'My Orders' label, gold indicators, navy #0B1F3A ink, and section groups.
   - `campushub/test/drawer_render_test.dart:60`: updated section heading and label checks and output scratch directory.
   - `campushub/test/seller_workspace_test.dart:285`: updated drawer scroll target and verified removal of standalone sidebar Account Settings row in favor of existing profile navigation.
3. **Changes made:**
   - Grouped menu items inside white rounded cards (`_card()`) with subtle `#E2E8F0` borders and 12dp border radius.
   - Organized items into three distinct sections:
     - **MAIN**: Home, My Orders (renamed from "My Purchases"), My Bookings.
     - **SELLER MANAGEMENT**: My Products, Inventory, Orders Received, My Bundles, Sales Analytics (accessible when seller status is approved).
     - **COMMUNICATION**: Messages (with dynamic badge count).
   - Bottom area retains a separate, full-width white rounded card container for **Logout** with confirmation dialog.
   - Highlighted active selection with subtle light-gray surface (`#F1F5F9`) and a 3dp narrow gold indicator (`#FCB316`) on the left edge.
   - Applied navy text and icon color (`#0B1F3A`) across all menu rows and logout.
   - Preserved profile header identity at the top with user avatar, name, and academic program info.
   - Wrapped sidebar menu items in a vertically scrollable `ListView` ensuring accessibility on compact viewports and enlarged text scales.
4. **How it works / functions, inputs, outputs and data flow:**
   - `CampusHubDrawer.destinations` returns the ordered list of `SellerDestination` values based on `sellerApproved`.
   - For each distinct section, `_sectionHeading(section)` renders small uppercase muted text (`Inter`, 11sp, letter spacing 0.6).
   - `_card()` wraps all items of that section inside a single rounded container. Between adjacent items within the container, an indented 1dp divider is drawn.
   - `_entry()` builds each row: leading 20dp Iconsax glyph in `#0B1F3A`, 14sp title, optional unread message badge (gold surface with navy text), and trailing 16dp `Iconsax.arrow_right_3_copy` chevron. When `selected == item`, the background changes to `#F1F5F9` and a narrow gold indicator (`#FCB316`) is pinned to the left edge.
   - Tapping an item invokes the existing `onSelected(item)` callback, preserving all navigation routing.
5. **Backend / API behavior:** No backend API endpoints, models, or network requests were added or modified. All existing routing and session logic remain unchanged.
6. **Database / migration impact:** None.
7. **Tests performed:**
   - `flutter test --no-pub test/seller_drawer_test.dart`: 10/10 tests passed across multiple device viewports (375x812, 320x640, 844x390, 768x1024), scaling factors (1.0x, 1.3x, 2.0x), and light/dark themes.
   - `flutter test --no-pub test/drawer_render_test.dart`: All render tests passed, verifying light and dark captures for both seller and standard buyer roles.
   - `flutter test --no-pub test/seller_workspace_test.dart`: 15/15 tests passed.
   - `flutter test --no-pub test/seller_home_entry_test.dart`: 22/22 tests passed.
   - `flutter test --no-pub test/checkout_workflow_test.dart test/order_fulfillment_test.dart test/seller_stock_receiving_test.dart`: 11/11 tests passed.
   - `flutter analyze --no-pub`: 0 issues found.
8. **Remaining limitations / troubleshooting / safe practice:**
   - Changes are scoped to the mobile Flutter seller sidebar presentation and labels.
   - Hot restart the Flutter application to ensure all cached widget tree elements reflect the new grouped-card styling.

## Current Add Product: centered Product Submitted content - November 4, 2026

1. **Cause / reason:** User requested centering Product Submitted content. The confirmation previously used `Alignment.topCenter` and a32dp leading spacer, so the success group stayed near the top even with unused space above the bottom actions.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:567`, `submitted-content-viewport` LayoutBuilder, and line582, `submitted-confirmation-content` Column; `campushub/test/seller_add_product_page_test.dart:1394`, viewport/content geometry and narrow-screen scrolling in the existing confirmation cases. This guide and `CAMPUSHUB_CONTEXT.md` record the layout change.
3. **Changes made:** Centered the success icon, heading, explanatory copy, status and returned-product summary as one group in the space above the existing bottom actions. Removed the fixed32dp top spacer. Existing16dp padding,640dp width limit, summary layout and fixed View My Products / Back to Home actions remain.
4. **How it works:** `_submissionConfirmation(product)` still receives only the validated backend response after successful submission. A LayoutBuilder measures the available content viewport, and a ConstrainedBox gives the scroll content a minimum height equal to that viewport minus its32dp vertical padding. Center positions the content group in that space; the group's Column uses `MainAxisSize.min`. When large text makes the group taller than the viewport, the scroll view expands its content and starts at the top instead of clipping it. Example: ordinary390dp content is centered vertically and horizontally;280dp/200% content can scroll to the actual product summary while actions remain visible.
5. **Backend / API behavior:** Unchanged success validation, returned product values/status, request count, callbacks, Android Back and route handling. No new request, automatic redirect, approval or notification behavior.
6. **Database / migration impact:** None. No models, migrations or working records changed; verification uses isolated existing mock-service responses.
7. **Tests performed:** Six existing confirmation/status/incomplete/malformed-response cases passed in6 seconds. The three navigation cases check actual centering when the content fits, reachable summary when it must scroll, returned server values, one POST and existing Products/Home/Android Back results. Command from `campushub/`: `flutter test --no-pub test/seller_add_product_page_test.dart --name 'confirmed product shows|returned approval status|incomplete product confirmation|malformed success'`. Scoped Flutter analysis reported no issues in4.6 seconds. Actual390dp centered and280dp/200% scrolled captures were inspected under `scratch/submitted-centered-20261104/renders/`.
8. **Remaining limitations / troubleshooting / safe practice:** Local widget verification only; no live submission, device or full-app-suite result is claimed. Large content intentionally scrolls instead of being forced into the visible height. Hot-restart if the old top alignment persists. Run the isolated confirmation tests and compare the content group's center with the viewport above the actions, then scroll the large-text fixture to its summary and use both destination buttons. Do not submit a working product solely to check this layout.

## Current Add Product: Review photo cards and Administrator approval - November 4, 2026

### 1. Cause / reason

User supplied references showing individual bordered photo cards with captions underneath and a compact Product Approval notice. Review previously overlaid Cover on the first thumbnail, left other photos uncaptioned and said Marketplace Admin. The requested Cover label has no checkmark. The follow-up removes its amber text color: Cover now uses the same muted caption color as the other photos.

### 2. Exact files changed / current lines and anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` |892 `fullWidthBody`;902 notice variant | Opt Product Approval into an icon/title row with full-width body text underneath. Existing low-stock notice retains its default layout. |
| Same screen |1053 column selection;1065 `review-photo-card`;1105 caption color | White rounded bordered cards, square photo area, captions below and no Cover checkmark. All captions use the existing muted color; Cover retains its font weight. Three columns at ordinary phone width, two when width/text scaling requires more room. |
| Same screen |1123 `review-product-approval`;1126 message;1129 variant flag | Replace Marketplace Admin with Administrator and use the reference's review-complete wording. |
| `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart` |12 gold /13 border tokens | Remove the now-unused amber Cover text token. Other form tokens remain. |
| `campushub/test/seller_add_product_page_test.dart` |1091 six-photo captions;2131 cover card;2156 approval copy;2181 capture | Check labels, original photo order, caption below thumbnail, no check glyph, full-width notice, retained editing/drafts and actual submission. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current entry | Record source, data flow, checks and safe exercise. |

### 3. Changes made

Uploaded Photos in Review now displays individual white cards with subtle borders, rounded corners and inset square images. The first card's caption is plain **Cover**, without a checkmark or special text color; the others say **Photo 2**, **Photo 3**, and so on. All use the existing muted caption color, with Cover retaining its stronger font weight. Captions sit below their photos instead of overlaying them. Selected real photos and the existing image-error fallback remain; the reference's example Photo1 placeholders are not inserted as product data.

Product Approval uses the existing muted surface, shield/title row and full-width supporting paragraph: **Your product will be reviewed by the Administrator before it appears in the marketplace. You'll be notified once the review is complete.** The Review footer retains only Submit for Approval. The separate upload-step card, X removal, picker and Cover selection remain.

### 4. How it works / functions, inputs, outputs and data flow

`_review()` reads the unchanged `_orderedImages` list, where the actual selected Cover is first. It iterates that list into `review-photo-card-$i`, passing each original image URL to `ProductImage`. Captions derive from the position, not new image records: `i == 0 ? 'Cover' : 'Photo ${i + 1}'`. A LayoutBuilder chooses available columns using content width and text scale. Existing accessible image labels remain, with duplicate child semantics excluded.

`_reviewNotice(..., fullWidthBody: true)` changes only Product Approval's arrangement. The default remains false for Low Stock Notice. Notice text is presentation only: it does not grant an Administrator permission or change who receives an approval task. The real draft, existing section Edit actions, `_submit` and Django product service continue unchanged.

### 5. Backend / API behavior

No change to approval roles/permissions, notifications, API payloads, validation, photo ordering, seller ownership, submission or database state. Administrator is the requested visible wording, not a backend role rename.

### 6. Database / migration impact

None. No model, migration, working product, uploaded file, audit or notification record was changed. Widget tests use their existing isolated service responses and photo fixtures.

### 7. Tests performed

- Follow-up Cover color removal: two existing Review/edit/draft cases passed in6 seconds at390dp/100% and280dp/200%, using `flutter test --no-pub test/seller_add_product_page_test.dart --plain-name 'review sections edit'`. No new test, screenshot or full-suite run was added for this small color change. Source search confirms no remaining `coverText` references in Flutter source/tests.
- Final six existing Review/six-photo/Cover/zero-stock widget cases passed in12 seconds at390dp/100% and280dp/200%. They cover plain Cover/no check glyph, positional captions, actual selected-photo ordering, caption placement, exact Administrator copy, full-width notice body, retained section editing/Cover and ordered submission. Command from `campushub/`: `flutter test --no-pub test/seller_add_product_page_test.dart --name 'review sections edit|six-photo gallery|required cover photo lifecycle|zero stock review'`.
- Final scoped Flutter analysis reported **No issues found** in5.4 seconds. Dart formatting completed.
- Actual six-photo desktop-sized phone render,390dp approval notice and280dp/200% Review captures were inspected under `scratch/review-photo-cards-20261104/renders/`. The first narrow render exposed Cover wrapping inside three columns; the final two-column narrow layout keeps Cover together. Local test fixtures use existing fallback images where fixture loading requires them; they are not working product uploads.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device, deployed/live API or full-app-suite result is claimed. Large text can wrap Photo labels and make cards taller; normal-width cards retain the reference's three-across presentation. Hot-restart if older overlay captions remain. Safely select photos, choose a Cover in Upload Images, open Review and compare its first card with that selection. Confirm Cover has no check and other cards have positional captions, then read Administrator in Product Approval. Use Edit to return without submitting. No working product submission is needed to verify this UI.

## Current Add Product: remove Review footer Back button - November 4, 2026

1. **Cause / reason:** User clarified that the entire Review footer Back button must be removed. The earlier icon-only interpretation was incorrect and is superseded.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:1144`, `_navigation` returns only the primary button; `campushub/test/seller_add_product_page_test.dart:250`, absent footer-back expectation, line253 Review text/tooltip absence, and line2186 existing header-back navigation; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Deleted the footer Back button, arrow and tooltip, plus its two-button responsive layout. Review now has one full-width Submit for Approval action. The header Back control and section Edit actions remain.
4. **How it works:** `_navigation` returns its existing primary button for every step: Next before Review, Submit for Approval in Review. The unchanged guards, busy/loading state and `_submit` callback still apply. Existing `_back` remains available through the header. Example: use the header Back control to return to Upload Images with photos/Cover retained; no draft data is cleared.
5. **Backend / API behavior:** Unchanged validation, requests, permissions and submission.
6. **Database / migration impact:** None; no working records changed.
7. **Tests performed:** Three existing footer/Review cases passed in5 seconds, including390dp/100% and280dp/200% Review navigation, absent footer Back button/text/tooltip, retained drafts and actual header-back action. Command from `campushub/`: `flutter test --no-pub test/seller_add_product_page_test.dart --name 'bottom actions stay visible|review sections edit'`. Actual390dp Review capture inspected under `scratch/review-no-back-20261104/renders/`; only full-width Submit for Approval remains in the footer.
8. **Remaining limitations / troubleshooting / safe practice:** Local widget verification only; no device or full-suite rerun for this presentation edit. Hot-restart if the old footer persists. Safely open Review, confirm its single footer action, then use a section Edit action or header Back and verify the retained draft. No working submission is needed.

## Current Add Product: web-style upload arrow - November 4, 2026

1. **Cause / reason:** User requested the web image-uploader arrow UI on mobile. The web reference is the existing upload SVG at `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html:190` and its58px navy square/34px glyph at `backend/static/components/css/admin_products.css:1897`. Mobile previously showed the image-plus glyph. The web reference files were read, not changed.
2. **Exact files changed:** New `campushub/lib/module_app/widgets/seller/product_upload_icon.dart:4`, `ProductUploadIcon`, line24 `paint` and line60 `shouldRepaint`; `campushub/lib/module_app/screens/seller_add_product_page.dart:17`, import, and line1454 `product-upload-arrow`; `campushub/test/seller_add_product_page_test.dart:13`, import, and lines919–934, upload-icon assertions. This guide and `CAMPUSHUB_CONTEXT.md` record the change.
3. **Changes made:** The existing upload target now contains a white upload arrow/tray in a58dp navy square, with the web glyph's34dp size and rounded1.8-unit strokes. It uses the existing mobile navy token. Existing mobile gallery wording, rounded upload target, Uploaded Photos card, X controls and Cover badge remain.
4. **How it works:** `ProductUploadIcon.build(context)` reads the surrounding white IconTheme and creates a decorative34dp CustomPaint. `_ProductUploadPainter.paint(canvas, size)` scales the web's24-by24 SVG coordinates and draws its tray, shaft and arrowhead with rounded strokes. `shouldRepaint` responds to tint changes. The parent upload button still calls `_pickImages`; its loading, busy and six-photo guards remain. Example: tapping the navy arrow invokes the same native gallery picker as tapping the surrounding upload target. This native vector avoids new image files, SVG dependencies or network requests.
5. **Backend / API behavior:** No change to picker options, validation, photo ordering, drafts, seller permissions or submission. Web behavior, background-removal settings and all Django services remain unchanged; only the visual arrow treatment is copied.
6. **Database / migration impact:** None. No working-record writes, models, migrations, routes or dependencies were changed.
7. **Tests performed:** Seven existing upload/six-photo/Cover/Review widget tests passed in10 seconds at390dp/100% and280dp/200%, including full-target gallery taps, navy58dp icon container, selection/removal/Cover and ordered submission. Scoped Flutter analysis reported no issues in2.9 seconds; Dart formatting completed. Inspected actual empty uploader captures at both widths, saved with other local fixtures under `scratch/product-upload-arrow-20261104/renders/`. Reproduce from `campushub/` with `flutter test --no-pub test/seller_add_product_page_test.dart --name 'photo upload area|six-photo gallery|required cover photo lifecycle|review sections edit'`.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device, deployed/live API or full-app-suite result is claimed. Existing large-text scrolling remains necessary at280dp/200%. Hot-restart if the former image-plus glyph persists. Safely open Add Product step3, confirm the white arrow/navy square, tap it to choose local photos, cancel or select photos, then verify the existing Uploaded Photos card and X removal. No working submission is needed.

## Current Add Product: Uploaded Photos card - November 4, 2026

1. **Cause / reason:** User requested an **Uploaded Photos** container/card while keeping X controls instead of visible Remove labels. Selected photos previously formed an unboxed grid below the existing upload button.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:1025`, Review title, and lines1480/1491/1497, `uploaded-photos-card`, label and grid; `campushub/test/seller_add_product_page_test.dart:239`, distinct step/Review titles, lines936/938, empty-card absence, and line977 onward, white bordered card and X controls. This guide and `CAMPUSHUB_CONTEXT.md` record the current presentation.
3. **Changes made:** The step heading remains Upload Images. Selected photos appear in a white, subtly bordered12dp-radius card labeled Uploaded Photos, with12dp internal padding and three thumbnail columns. The card is absent before photo selection. Existing X icons, accessible removal tooltips, Cover badge, replacement options and counter remain. Review's corresponding section is named Uploaded Photos.
4. **How it works:** `_images()` checks the actual `_imageCount > 0` and wraps the existing grid in the new container. Its inner `LayoutBuilder` measures space after card padding before calculating thumbnail sizes. `_imageSlot` still renders each retained image and its X control, whose callback calls the unchanged `_removeImage(index)` to update counts, Cover and validation. Selected-image draft values continue to flow into Review and the existing submission service. Example: remove the Cover photo with X; the next retained photo becomes Cover, and removing the final photo hides the card. Review's Edit action still opens step3 with retained photos.
5. **Backend / API behavior:** Unchanged picker, validation, payloads, permissions and submission.
6. **Database / migration impact:** None; no working records changed.
7. **Tests performed:** Seven existing upload/six-photo/Cover/Review cases passed in9 seconds at390dp/100% and280dp/200%, using `flutter test --no-pub test/seller_add_product_page_test.dart --name 'photo upload area|six-photo gallery|required cover photo lifecycle|review sections edit'` from `campushub/`. Checks include the selected-only white bordered card, X glyphs, no visible Remove text, actual removal/Cover reassignment, retained drafts and ordered submission. Two upload cases passed again in3 seconds after adjusting captures to scroll the card into view. Scoped Flutter analysis found no issues in2.9 seconds. Actual390dp and280dp/200% widget captures were inspected; evidence is under `scratch/uploaded-photos-card-20261104/renders/`. An initial helper expected the upload-step title in Review; its expectation was updated for the distinct Uploaded Photos Review heading before the passing run.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device, live API or full-suite rerun is claimed. Captures use isolated test photos, not working uploaded records. Hot-restart if the old layout remains. Safe exercise: select local photos in step3, inspect the Uploaded Photos card and X controls, remove one and verify the count/Cover, then open Review and use Edit to confirm retained photos. Remove the last photo to confirm the card disappears. No working submission is needed.

## Current Add Product: solid Stock Method surfaces and icons - November 4, 2026

### 1. Cause / reason

The screenshot and user clarification identify the Stock Method cards and icons. The selected card explicitly used a pale gray fill. Separately, Add Product forced a white screen while copying the surrounding app theme: dark mode left its pale icon theme and unselected-control color in place. Changing only `onSurface` did not update those independent colors. The dark-theme regression reproduced a white help-icon glyph on the white form before the icon-theme correction.

### 2. Exact files changed / current lines and anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` |1533 `iconTheme`;1537 `unselectedWidgetColor`;1544 scheme brightness;1550 variant text;1551/1552 outlines | Complete the existing form-local light theme using existing navy/slate/border tokens. Set icon opacity to 1. The surrounding app theme remains selected by the user. |
| `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart` |218 `ProductInventorySelector`;239 Material color | Give both stock methods an opaque white surface. Preserve the selected navy border and filled radio as the selection cues. |
| `campushub/test/seller_add_product_page_test.dart` |133 `surroundingTheme`;752 stock-card cases;810 resolved scheme;813 rendered icon;851 capture | Exercise the actual gold-seeded dark app theme as well as light mode, at390dp/100% and280dp/200%. Check the rendered icon color, white cards, selection, help and retained field switching. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current entry | Record the confirmed cause, scope, data flow, checks and safe exercise. |

### 3. Changes made

Standard Stock and Batch Tracking stay white in both selection states. Their existing navy outline and radio identify the selected method. Help icons and unselected radio outlines use solid slate `ProductFormStyle.muted` rather than inherited dark-theme colors that look transparent on white. Card dimensions, layout, descriptions, touch targets and tooltip behavior are retained. The existing pale `selectedSurface` token remains available for its other callers; only the stock cards stop using it.

### 4. How it works / functions, inputs, outputs and data flow

`SellerAddProductPage.build(context)` reads the surrounding `ThemeData`, copies it into the existing form-local `Theme`, and supplies a consistent light scheme, icon theme and unselected-control color. Flutter's existing IconButton/Radio widgets resolve their colors from that local theme. `ProductInventorySelector(value, onChanged)` still receives the real `simple`/`fifo` draft value and callback; it renders white Material cards and derives the navy border/radio selection from `value`.

```dart
// Existing selection and callbacks still decide which fields are shown.
Material(
  color: Colors.white, // Opaque surface in either selection state.
  // Existing selected border and InkWell callback remain below.
)
```

The form-local approach corrects inherited colors without changing the app-wide dark theme. Tapping Batch Tracking still updates the existing retained draft, displays the same batch fields, and eventually submits through the unchanged product service.

### 5. Backend / API behavior

No change to payloads, validation, inventory methods, seller access, submission, authentication or Django services. This is a Flutter presentation correction on the existing screen; no new route, package or request is introduced.

### 6. Database / migration impact

None. No models, migrations or working records changed. Widget tests use existing isolated/mock service responses and do not submit working products.

### 7. Tests performed

- Four focused stock-card cases passed, covering both surrounding themes and both width/text-scale combinations. They verify actual rendered help-icon color, theme resolution, white surfaces, card/radio selection and tooltip operation.
- The complete existing Add Product widget suite passed **54/54 tests in34 seconds**, including retained drafts, both stock methods, batch validation, keyboard/navigation, photos/Cover, review, guarded submission/errors and confirmation flows. Command: `flutter test --no-pub test/seller_add_product_page_test.dart` from `campushub/`.
- Final scoped `flutter analyze --no-pub` reported **No issues found** in3.5 seconds. `dart format` reported three files/zero further changes.
- Eight actual widget captures were generated under `scratch/add-product-colors-20261104/renders/`. Inspected dark-surrounding Standard Stock at390dp and selected Batch Tracking at280dp/200%; white surfaces, visible icons and selected navy outline/radio are present. These are local Flutter widget renders, not generated illustrations or physical-device screenshots.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device, live API, deployment or full-app test run is claimed. Existing280dp/200% text can wrap heavily within the narrow cards; this color change retains that layout. A hot reload may retain an older tree or app build: reopen Add Product or perform a hot restart before comparing.

Safe exercise: switch the app to dark mode, reopen Add Product, enter valid Product Information and advance to Pricing & Inventory. Confirm both stock cards are white, icons are visible, and selection moves the navy outline/radio. Open each information icon and close it, switch back to Standard Stock, and confirm its quantity draft remains. Repeat in light mode. Do not submit a product just to verify colors. Reproduce isolated checks from `campushub/` with `flutter test --no-pub test/seller_add_product_page_test.dart --plain-name "stock cards align content"`.

## Current Add Product: native Product Images upload area - November 3, 2026

This entry supersedes older six-slot rendering, immediate missing-photo feedback and photo-validation wording below. The existing Cover and submission rules still apply.

### 1. Cause / reason

The latest brief requests one tappable gallery area, selected-only thumbnails, a heading counter and validation that does not appear on first entry. Inspection confirmed the existing full-width upload button already called the real `ImagePicker` gallery API; no simulation callback existed in this step. The unwanted clutter came from rendering all six storage slots, placing the count below the grid, and showing a required-photo error whenever the count was zero.

### 2. Exact files changed and current anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` |380 `_continue`;431 `_draftIssue`;1272 `_removeImage` | Use the exact requested missing-photo message for continuation/final guards and removing the last image. |
| Same screen |1226 `_section(..., trailing:)` | Optional trailing heading widget; only Product Images supplies it. Other sections retain their existing heading layout. |
| Same screen |1323 `_imageSlot`;1326 `removeTarget` | Render uploaded photos only; retain image options/remove/Cover. Compact removal target avoids covering the image center; Cover label scales down to fit. |
| Same screen |1427 `_images`;1483 `product-image-grid`;1513 `product-image-counter` | New exact copy, heading count, selected-only three-column grid and interaction-triggered error display, all within the existing unboxed section. |
| `campushub/test/seller_add_product_page_test.dart` |207 `next` helper;863 upload-area checks;961 six-photo flow;1024 Cover lifecycle;1143 invalid/cancel/excess flow;1162 oversize case;1987 Review edits | Update Step3 count/validation expectations and add gallery-edge/counter/grid checks at390dp and280dp/200%. Preserve review/submission assertions. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current entry | Records functions/data flow, exact anchors, verification, diagnosed overlap and safe practice. |

### 3. Changes made

- Heading **Product Images** now has a live **0 of 6** / **2 of 6** counter at its right. Description: **Add at least one clear photo of your product.**
- One full-width outlined target contains the existing image icon, **Add product photos**, and **Tap to choose photos from your gallery.** Its entire surface calls the existing native gallery picker; there is no separate upload/simulation control. Busy and six-photo capacity guards remain.
- Helper text is exactly **JPEG, PNG, WebP, GIF • Max 6 photos • 5 MB each**. Selected photos alone render below it in three columns with8dp gaps. With zero selections there is no grid and no six empty placeholders.
- First valid image automatically remains Cover. Its small badge uses `IgnorePointer`; tapping a photo opens the existing Replace photo / Set as Cover sheet. Remove, cover reassignment/compaction and Cover-first submission remain. At compact thumbnail widths below96dp, Remove uses a32dp target; larger thumbnails retain48dp. This prevents the remove overlay from consuming the thumbnail-center tap in a three-column phone grid. Cover text scales down within its existing badge rather than truncating.
- Validation is now exactly **Please add at least one product photo.** It appears when appropriate, such as removing the last image or a guarded final submission, rather than on first opening Step3. Invalid/oversize gallery results retain their specific existing errors. Empty Next stays disabled; cancellation alone creates no missing-photo error.
- Existing Inter typography, navy/gold/white styling, horizontal progress and Step3 of4, footer Next, retained drafts and four-step submission workflow remain. No outer visual wrapper, duplicate route, dependency or new screen was added. Review's separate image-count wording remains unchanged.

### 4. How it works / functions, inputs, outputs and data flow

`_pickImages({int? slot})` remains the production picker entry point. With no slot it computes remaining capacity and opens `ImagePicker.pickMultiImage(limit: remaining)`; replacement or one remaining place uses `pickImage(source: ImageSource.gallery)`. It preserves the existing1280px/quality85/no-full-metadata options. Cancel returns an empty selection and leaves draft images intact. Excess results reject, even if a platform ignores its picker limit. `_readImage(XFile)` still checks size, actual encoded image type and decodability before producing a data URL. A whole chosen batch is validated before mutating draft slots, so a later invalid/oversize file cannot partially add earlier files.

The existing parent-owned `_selectedImages` storage still has six slots for compatibility. `_images()` now builds thumbnails only for non-null slots and computes their width as `(availableWidth - 16) / 3`. `_imageSlot(index, size)` receives only occupied indexes and renders the actual `ProductImage`; its null-placeholder branch is removed. `_section`'s optional trailing widget produces the Product Images heading row while its null/default branch preserves other section headings.

`_primaryImage` is still assigned on the first successful upload. `_showImageActions(index)` changes that index or invokes native replacement. `_removeImage(index)` compacts the retained data URLs and remaps Cover; deleting Cover promotes the first remaining photo, and removing all clears Cover and shows the requested validation. The32/48dp remove control is independent of the photo's options action. The non-clickable Cover badge retains its semantic description on the photo.

```text
Tap anywhere in upload area -> existing ImagePicker gallery call
  cancel -> same draft, no new required error
  invalid/excess/oversize -> specific error, same draft
  valid1-6 photos -> retained slots + first Cover -> counter and selected-only grid
Back/Next -> same parent-owned slots/Cover
Submit -> existing _draftIssue -> _orderedImages(Cover first) -> same ProductService -> Django
```

Example: choose three valid images; the header reads3 of6 and one row of three thumbnails appears. Set the third as Cover; remove the second; the remaining Cover is remapped correctly and Review/submission still puts it first. Removing both remaining images hides the grid, changes the counter to0 of6, disables Next and displays the requested message. No image is uploaded to the backend until the existing product submission runs.

### 5. Backend / API behavior

Unchanged. The same service, authentication, image data URLs, six-image cap, Cover-first `images` list and product approval submission contract remain. No image/permission/backend endpoint was added or simulated. The existing pinned `image_picker` dependency and native platform configuration remain. These widget tests replace only the platform picker during testing; the application still instantiates the real `ImagePicker`.

### 6. Database / migration impact

None. No models, migrations, dependencies, native permissions, assets or working records changed. No backend, order/inventory calculation, price validator, other screen or deployment was modified by this image-step task.

### 7. Tests performed

- Final whole-app **`flutter analyze --no-pub`: No issues found** (23.3 seconds). This is the requested Flutter analysis, using the already resolved dependencies. `dart format` completed for the screen and test file.
- Initial full Add Product run:50/52 passed in54 seconds. Two280dp/200% flows exposed a real overlap: the old48dp remove target covered a77dp thumbnail's center, so a center tap removed a photo instead of opening its options. After the scoped32dp compact-target correction, **all8 affected image/Review checks passed in18 seconds**, including both originally failing cases. No second full run was performed; all52 cases passed across the full run and affected rerun.
- Checks exercise upload-area edges calling the platform picker, count/heading alignment, no empty slots, exactly three columns, first Cover, non-clickable badge, center-tap options, cover changes/removal/reassignment, first-entry versus last-removal validation, disabled Next, native remaining limits, seven-image rejection, invalid type, an oversized file after an otherwise valid selection without partial insertion, retained drafts, Review edits, and exact Cover-first POST image order.
- Commands from `campushub/`: `flutter test --no-pub test/seller_add_product_page_test.dart`; affected rerun adds `--name 'photo upload area|six-photo gallery|required cover photo|gallery cancel|review sections edit'`. Tests used approved escalation because earlier sandboxed Flutter test runs stalled.
- Actual font-loaded empty390dp, six-photo390dp and selected280dp/200% renders were inspected. Captures are in `scratch/product-images-upload-20261103/renders/`, including `product-images-empty-390.png`, `six-photo-step-3.png`, `product-images-three-280.png` and `selected-cover-280.png`. Fixtures use tiny transparent PNGs, so these captures verify layout/controls; URL/content/order assertions verify the retained images.

### 8. Remaining limitations / troubleshooting / safe practice

No physical Android/iOS gallery was opened in this environment; native gallery wiring was inspected and picker calls were verified through the existing Flutter platform test double. A device smoke check remains necessary for OS-specific permission UI. Existing denial/error messages and configuration remain. At very narrow widths or200% text the content grows and scrolls, while all three thumbnail columns remain; compact Remove targets are32dp. No live API submission or deployment was performed.

Safe exercise: open an unsent local draft, navigate to Step3 and confirm0 of6, no placeholders/error and disabled Next. Tap an edge of the upload area, cancel, and confirm unchanged state. Select three small valid photos, verify one row and first Cover, tap a photo's center to open options, change Cover and remove another. Navigate Back/Next and confirm the draft survives. Remove all photos and verify the exact validation/disabled Next. On a real device, confirm the OS gallery opens; do not submit a working product just to test layout. If a photo tap removes it, inspect the compact `removeTarget`; if an empty grid returns, check the non-null filter rather than changing the six-slot payload storage. If an error appears on first entry, check the `_imageError != null` condition rather than enabling empty Next.

## Current Add Product: low-stock threshold placeholder - November 3, 2026

1. **Cause / reason:** The user requested **Enter low stock threshold(e.g. 5)** instead of the field's previous `5` hint.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:1759` (threshold field's `_decoration` hint); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Replaced only the placeholder string, using the user's exact wording. Label, helper text, tooltip, value, validation, spacing and styling remain.
4. **How it works / inputs, outputs and data flow:** `_decoration(String hint)` at `:1177` puts its input into `InputDecoration.hintText`. The threshold field supplies the new string; Flutter shows it when `_lowStockThreshold` is empty. The controller at `:46` still starts with the actual value `5`. Editing that controller continues through `_validateLowStockThreshold`, Review and the existing submission payload; the hint is display text and is never submitted. Example: clearing `5` reveals the requested hint, while typing `8` hides it and retains8 as the entered threshold.
5. **Backend / API behavior:** Unchanged. Threshold numeric rules, default, alerts and payload remain.
6. **Database / migration impact:** None; no model, migration, dependency, asset or working record changed.
7. **Tests performed:** Single-file `flutter analyze --no-pub lib/module_app/screens/seller_add_product_page.dart` reported **No issues found** (1.5 seconds). `dart format` applied normal wrapping to the longer decoration expression. No widget tests or rendering were run for this placeholder-only change.
8. **Remaining limitations / troubleshooting / safe practice:** The hint appears only when the field is empty; the existing default5 intentionally remains. Long text may truncate at narrow widths or large text sizes. In an unsent draft, open Pricing & Inventory, clear the threshold and confirm the new placeholder, then restore5. If the hint is invisible, check for an actual controller value before changing decoration or validation. No physical-device or live API check was performed.

## Current Add Product: required and invalid validation messages - November 3, 2026

1. **Cause / reason:** The user approved applying separate required messages for empty fields and valid-value messages for invalid entries throughout Add Product. Price and quantities previously used the same message for both cases. Product name, description and threshold already distinguished missing input; category, received-date and photo feedback used action wording rather than explicit required wording.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:97` (price empty guard), `:253` (category message), `:380` / `:431` / `:1259` / `:1483` (consistent missing-photo feedback); `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart:24` (standard/batch quantity empty guard), `:53` (received-date message); `campushub/test/seller_add_product_page_test.dart:423` (required-step checks), `:628` (batch checks), `:925` (photo checks), `:1987` (final draft checks); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Blank or whitespace-only price now reports **Selling price is required.**; standard stock reports **Stock quantity is required.**; batch quantity reports **Batch quantity is required.** Nonempty invalid input retains the existing valid-value messages, including the user's exact **Please enter a valid selling price.** and **Please enter a valid stock quantity.** Missing category says **Category is required.**; missing batch date says **Date received is required.**; missing photos say **At least one product photo is required.** Existing Product name / Description / Low stock threshold required messages remain. Tags, unit cost and expiry remain optional. Layout, tooltips, numeric/date rules and workflow do not change.
4. **How it works / inputs, outputs and data flow:** `_validatePrice(String? value)` trims input, returns the required string if empty, then runs the unchanged numeric rules and returns either the existing invalid message or null. `ProductFormStyle.quantity(String? value, {bool positive = false})` follows the same order and chooses Stock/Batch required text from its existing positive flag. `_validateStock` delegates to that helper; batch widgets use `positive: true`. `receivedDate(DateTime? value)` returns the required message for null, its existing date error for future dates, or null. `_required` and `_validateLowStockThreshold` already check trimmed emptiness. Category still checks null, and photos still check the actual image count.

   Field validators (`seller_add_product_page.dart:1654` / `:1684` / `:1765`, inventory widget `:398`) and `_draftIssue` (`seller_add_product_page.dart:390`) reuse these same rules, so Next and final Submit agree. The final guard returns the responsible step plus an error before any POST; batch errors retain their Batch1/2/etc. prefix. Existing generic product-information final feedback still reopens Step1, whose fields display their specific messages. Example: price `   ` returns the required message; price `0` returns the existing invalid-price message; price `1.25` returns null. Standard stock `0` stays valid; batch stock `0` stays invalid.
5. **Backend / API behavior:** Unchanged. Standard stock remains an integer from0 through2147483647; batch quantities remain positive integers. Price remains positive and finite with up to8 integer digits and2 fractional digits. Same fields are required as before, no new fields become required, optional blanks remain accepted, and the same service/permissions/approval/backend rules remain.
6. **Database / migration impact:** None. No model, migration, dependency, asset or working record changed.
7. **Tests performed:** Final three-file `flutter analyze --no-pub` reported **No issues found** (2.9 seconds); `dart format` applied normal test formatting. Full Add Product run exercised50 cases in52 seconds:46 passed, and4 new final-submit text assertions initially failed because the finder searched beneath a keyed Text widget rather than reading that widget's data. After correcting only that test selector, the four final-submit checks **passed4/4 in6 seconds**. Thus all50 cases passed across the full run and focused rerun; a second full run was not performed. Checks cover empty/whitespace required messages, nonempty invalid messages, valid zero standard stock/threshold, batch zero rejection/date requirement, photo requirement, unchanged optional expiry, retained drafts and zero POSTs for missing/invalid final quantities. Commands from `campushub/`: `flutter test --no-pub test/seller_add_product_page_test.dart` and then the same with `--name 'final submission rechecks'`. Tests used approved escalation because earlier sandboxed runners stalled.
8. **Remaining limitations / troubleshooting / safe practice:** No new render, physical-device or live API check was performed. Short invalid-price/stock messages still omit the precise numeric rules, which remain enforced. In an unsent local draft, leave Step1 blank and tap Next to see its required messages. On Step2, clear price/stock/threshold and verify the corresponding required text; enter negative or fractional values to verify the existing invalid text. Use price1.25/stock0/threshold0 to confirm valid continuation; switch to Batch Tracking to check empty quantity/date messages and zero rejection. Optional cost/expiry must still allow blanks. If old wording persists, validate again or hot restart; edit the shared validator's strings rather than loosening its conditions. In tests, `product-submit-error` is the Text widget itself: read its `.data` rather than searching its descendants.

## Current Add Product: centered right-side Stock Method help - November 3, 2026

1. **Cause / reason:** The earlier title Row's48dp help button created excess description spacing; the preceding change moved help to the centered outer Row and removed that gap. For the latest "move to right again" request, inspection confirmed the button was already at the right inset, but `AlignmentDirectional.centerStart` kept its visible18dp icon on the left of its48dp target. The visible glyph needed right alignment inside that existing target.
2. **Exact files changed:** `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart:115` (optional alignment input), `:119` (typed property), `:200` (IconButton consumes alignment), `:297` and `:300` (both stock cards request centerEnd); `campushub/test/seller_add_product_page_test.dart:728` (`stock cards align content and select through the card`), `:766` (visible glyph bounds); this guide and the current entry in `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Only the two stock-method help widgets now request `AlignmentDirectional.centerEnd`. This shifts the visible glyph30dp farther right inside its unchanged48dp target, placing its right edge16dp inside the card. The optional alignment defaults to the existing centerStart for other uses, including Low Stock Threshold. Centered height, zero added description gap, target size, text, styling and callbacks remain. Existing layout tests now measure the actual icon as well as its button.
4. **How it works / inputs, outputs and data flow:** `ProductInventorySelector(value, onChanged)` receives the retained `simple`/`fifo` value from the Add Product screen. Its Row still contains radio,8dp gap, Expanded title/description Column,4dp gap, and help button. `ProductInventoryInfo(alignment: AlignmentDirectional.centerEnd)` passes the optional `AlignmentGeometry` through `_ProductInventoryInfoState` to `IconButton.alignment`; it changes glyph position without moving/resizing the button. Example: omitting alignment preserves start alignment for threshold help; passing centerEnd places stock help at the right inset. Card/radio taps invoke `onChanged`; help opens its tooltip without invoking that callback. No controller, payload or calculation changed.
5. **Backend / API behavior:** Unchanged; no endpoints, inventory identifiers, FIFO rules, permissions or submission changes.
6. **Database / migration impact:** None. No models, migrations, dependencies, assets or working records changed.
7. **Tests performed:** Two-file `flutter analyze --no-pub` reported **No issues found** (3.7 seconds); `dart format` reported no formatting changes. **4/4 focused widget tests passed** (4 seconds) at390dp/100% and280dp/200%, measuring the visible glyph's16dp right inset and centered height, plus button bounds, zero added description gap, centered radios, independent help taps, method selection and batch help tap/long-press/hover/outside dismissal. Command from `campushub/`: `flutter test --no-pub test/seller_add_product_page_test.dart --name 'stock cards align|concise batch tooltip'`. Tests used approved escalation because prior sandboxed runs stalled. The actual390dp selected-card capture was inspected in `scratch/stock-tooltip-right-edge-20261103/`;280dp was checked by widget assertions.
8. **Remaining limitations / troubleshooting / safe practice:** At280dp/200%, the narrow text area can still wrap within words and increase card height; help stays centered against the complete text block. Text retains normal font line height, with no added gap. No physical-device or live API checks were performed. In a local unsent draft, open Pricing & Inventory, select Batch Tracking, and tap each help icon. Verify the tooltip appears, Batch Tracking remains selected, both icons are centered at the right edge, and descriptions begin immediately below their titles. Repeat with enlarged system text. If extra space returns, check that help remains a sibling of the Expanded text Column rather than a child of a title Row. Do not change selection callbacks to adjust spacing.

## Current Add Product: organized Review & Submit - November 3, 2026

### 1. Cause / reason

Step 4 previously displayed an ungrouped vertical list, large review photos and only a Submit footer. The attachment requests three compact editable summaries, a conditional low-stock notice, approval guidance and Back/Submit actions. Inspection also confirmed that only active step fields were mounted, so final submission needed to recheck the retained complete draft rather than relying on Review's empty set of inputs.

### 2. Exact files changed and current anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | 389 `_draftIssue`; 435 `_submit`; 790 `_reviewValue`; 810 `_reviewGroup`; 867 `_reviewDetails`; 885 `_reviewNotice`; 923 `_review`; 995 `review-batches`; 1015 low-stock notice; 1104 `_navigation`; 1144 footer Back | Replaces the existing Step 4 summary and adds only the requested supporting validation/navigation behavior. |
| `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart` | 39 `unitCost`; 47 `receivedDate`; 55 `expiryDate`; 399/451 existing validators | Extracts existing validation rules for reuse by both the editable fields and final submission. |
| `campushub/lib/module_app/widgets/seller/product_expiry_field.dart` | 62 expiry validator | Calls the same extracted optional-date rule; field/picker behavior is unchanged. |
| `campushub/test/seller_add_product_page_test.dart` | 238 Review headings; 244 footer expectation; 572 expanded batch check; 1500 tag-chip assertions; 1828 Edit/retention tests; 1941 final draft checks; 1980 zero-stock notice | Updates existing review assertions and adds five behavior checks covering normal/narrow layouts, editing, final validation and notice behavior. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current entry | Records functions/data flow, causes, verification and safe practice. |

### 3. Changes made

The existing Add Product header, gold/navy progress line and Step 4 of 4 label remain. Review & Submit now has the requested supporting sentence and three separate white rounded summaries, each with Edit:

- **Product Information:** name, category and naturally wrapping description; optional tags are compact read-only neutral chips with full-value tooltips. Empty tags omit that row.
- **Pricing & Inventory:** prominent 20sp semibold peso price; Standard Stock/Batch Tracking, total quantity, threshold, optional simple expiry and batch count. Compact detail columns become one column at narrow widths/large text. Batch details expand to show actual quantities, received dates, optional unit cost and optional expiry without inputs.
- **Product Images:** uploaded-photo count and compact square Cover-first thumbnails only, with a small non-clickable Cover indicator and no upload/removal controls. Existing images and Cover index are reused.

The nonblocking **Low Stock Notice** appears exactly when actual total stock is at or below the configured threshold, including zero stock/zero threshold. It uses a small warning icon and light-gold surface. It is absent above the threshold. The **Product Approval** panel below the summaries uses the exact requested review/notification copy, an information/shield icon and subtle neutral background.

The fixed SafeArea footer displays outlined Back and a more prominent navy Submit for Approval in a row when they fit. It stacks them at narrow widths or enlarged text; both remain accessible and use 15sp semibold text. Header Back still works. Earlier steps retain their current Next footer. No extra outer card, editable field copies, step, percentage, unrelated redesign or route was added. For large-text narrow section headers, Edit is top-right above the full-width title so words do not break awkwardly.

### 4. How it works / functions, inputs, outputs and data flow

`_review()` reads existing controllers, `_inventoryMethod`, `_batchTotal`, `_expiry`, batch drafts and `_orderedImages`. It formats those retained values without changing them. `_reviewGroup(title, step, children)` applies the shared section header/border and calls `_changeStep(step)` from Edit. Step indices0/1/2 reopen the same existing fields, so photos, Cover, tags, dates and quantities remain in their parent-owned draft. Next follows the existing step sequence back to Review; no secondary editor exists.

`_reviewValue(label, value, prominent)` provides compact gray13sp labels and navy14sp medium values; only price uses20sp semibold. `_reviewDetails(details)` uses available width and the user's text scaler to choose one/two columns. `_reviewNotice(...)` is reused for stock and approval information. `_review()` parses the configured threshold and compares it with the same Standard Stock value or computed batch total used for submission. It does not fabricate a stock status or introduce a blocking low-stock rule.

`_draftIssue()` returns either null for a valid draft or `(stepIndex, message)` for the first invalid section. It reuses existing price, required/quantity/threshold rules and the extracted batch received-date/unit-cost/optional-expiry validators. It also checks the selected category, product-name limit, batch count/total and minimum photo count. If invalid, `_submit` reopens that existing step, retains entered values and enables validation feedback before making any API request. Existing busy/loading and successful-response confirmation guards remain.

```text
Review Edit Pricing -> _changeStep(1) -> same controllers/batch drafts
Next -> existing validations -> Photos -> Review renders updated values
Submit -> _draftIssue()
  invalid -> existing responsible step + feedback, zero POSTs
  valid -> unchanged ProductService payload -> Django -> existing confirmation
```

Example using test-only values: stock5 and threshold5 show the low-stock notice, but Submit stays enabled. Edit Pricing changes stock to6; on returning, Review shows6 units and hides the notice. Two batches of3 and4 display7 total units and2 batches; expanding details reveals their own dates/costs. Editing Images returns to Step3 with the selected Cover still intact.

### 5. Backend / API behavior

Unchanged. No endpoint, field name, inventory identifier, ownership/authentication, allocation, expiry persistence, image ordering or approval/publication rule changed. Standard/Batch use the existing `simple`/`fifo` values. This adds a client-side final draft check before the same submit service. Low stock does not block submission. Failed requests still retain Review/draft and allow the existing retry action; successful submissions still show the response-based confirmation. Approval notice text does not implement a new notification system.

### 6. Database / migration impact

None. No models, schemas, migrations, dependencies, assets or working records changed. No duplicate screen/component file or deployment/server action.

### 7. Tests performed

- Whole-app final `flutter analyze --no-pub`: **No issues found**, 7.5 seconds.
- **48/48 Add Product tests passed in24 seconds.** After the final narrow-header-only adjustment, **3/3 Edit/batch-review checks passed in7 seconds**.
- New tests exercise all three Edit destinations, preserved/updated controllers/tags/dates/photos/Cover, read-only Review, exact price/quantity/image order, threshold equality/above/zero notice behavior, nonblocking Submit, footer Back and final invalid standard/batch draft rejection before POST. Existing batch totals, photo validation, failure/retry, duplicate-submit guards, returned confirmation data/status and Android Back continue to pass.
- Normal390dp and narrow280dp/200% text Review renders plus expanded Batch Tracking review were inspected. Captures: `scratch/add-product-review-20261103/renders/`. Fixtures use tiny/transparent test photos; image URL/order assertions verify data, while renders verify layout/control placement.
- Initial checks caught a non-existent Chip tooltip parameter (replaced with native Tooltip), a flow-control lint, and shell-transferred peso/separator characters (corrected before passing verification). No hosted API submission, backend test run or physical-device check was performed for this Flutter-only change.

Reproduce from `campushub/`: `flutter analyze --no-pub` and `flutter test --no-pub test/seller_add_product_page_test.dart`.

### 8. Remaining limitations / troubleshooting / safe practice

Edit returns to the selected existing step and uses the normal Next sequence, rather than adding a special return-to-review editor. Batch details are initially collapsed; expand them to inspect dates/costs/expiry. Large text can increase card height and stack footer actions; content remains scrollable. Existing backend rules remain authoritative, including approval and actual notification behavior.

Safe exercise: use the mocked test harness to review a draft with stock5/threshold5, edit stock to6 and confirm the notice disappears. Edit information and images, confirm retained values/Cover, then use footer Back. Test invalid retained quantities through the regression test and verify zero requests. Do not create a working product to check spacing. If Edit clears a field, inspect its parent-owned controller/draft; if a notice is wrong, compare `_batchTotal`/quantity against the actual parsed threshold rather than hardcoding5. For new validation rules, reuse the same function in the field and `_draftIssue` to avoid conflicting behavior.

## Current Add Product: submitted-for-approval confirmation - November 3, 2026

### 1. Cause / reason

The existing successful `_submit` immediately popped the Add Product route and showed a snackbar. This gave no durable product summary or choice of destination. The user requested an explicit submission confirmation after backend success, while keeping Marketplace Admin approval separate.

### 2. Exact files changed and current anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | 19 `ProductSubmissionDestination`; 54 `_submittedProduct`; 55 `_leavingConfirmation`; 389 `_submit`; 405 returned product; 430 response validation; 467 `_submissionConfirmation`; 503 PopScope; 582 summary; 649/668 actions; 1193 success render branch | Replaces immediate pop/snackbar with confirmed product details and a separate confirmation state inside the existing route. |
| `campushub/lib/module_app/screens/products_screen.dart` | 33 `showAddProductPage`; 35–36 optional callbacks; 63 route result; 72–77 destination handling | Dispatches the selected existing destination after closing the completed route; retains the existing nullable bool completion contract for refresh callers. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 188 Add Product call; 190 `_openSellerTool(SellerDestination.products)`; 191 `_goToTab(0)` | Connects actions to existing My Products/Home navigation and preserves post-submission refresh. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 428 Add Product call; 430 existing `_select(products)`; 432 `_backHome` | Connects the same actions when the form is opened from the seller workspace; existing reload follows completion. |
| `campushub/test/seller_add_product_page_test.dart` | 62 `successResponse`; 281 submit helper; 1093 confirmation actions; 1162 actual returned status; 1186 incomplete response | Uses realistic product response fixtures and verifies confirmation, callbacks, Back, server data and failed-request retention. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current entry | Records functions/data flow, response contract, verification and safe practice. |

### 3. Changes made

After successful submission, the existing screen displays a centered navy outlined check on a subtle gold circle, **Product Submitted!**, the requested review description and a small light-gold **Pending Approval** indicator. A bordered compact summary shows only the returned cover image, name, formatted selling price, category and status. Inter, existing navy/gold/white, 16dp screen padding, rounded borders and accessible buttons are retained. The content scrolls on small screens/large text; the actions remain below it.

**View My Products** opens the existing seller product destination; **Back to Home** uses the existing Home navigation. There is no automatic timed redirect, extra form step, progress line on the confirmation, duplicate My Products screen or new route dependency. The completed form is no longer rendered. Android Back leaves to Home rather than exposing a completed submission form. A one-shot leave guard prevents repeated action callbacks from popping additional routes.

### 4. How it works / functions, inputs, outputs and data flow

`_submit()` calls the same `ProductService.submitProduct(...)` with the same payload. It now captures the returned map instead of discarding it. Before showing confirmation, it requires a positive integer product ID, nonempty returned name/category, a finite positive returned price and a known actual approval status (`pending`, `approved`, `rejected`, `archived`). Incomplete/unreadable confirmation data stays on Review with the existing caution to check My Products before retrying; it never displays an invented Pending status.

The valid map is retained in `_submittedProduct`. `build` detects it and returns `_submissionConfirmation` instead of the form. This is a presentation state, not Step 5. The summary reads the response's `images[0]`, or its `image_url` fallback, and the returned name/price/category. It does not substitute the typed draft for server fields. Pending shows the requested review sentence; another recognized returned status shows its actual label and neutral submission-confirmed copy.

```text
Review -> unchanged submit service -> confirmed returned product
  -> validate details/status -> retained confirmation (no form progress)
  -> user chooses destination -> pop completed route with destination enum
  -> showAddProductPage dispatches existing caller callback -> returns true
  -> existing Home/workspace refresh loads actual saved products
```

`_submitting` disables form actions during the request, and `_submittedProduct != null` blocks another submission after success. No submit control exists in the confirmation. Failed requests leave the same controllers, photos, cover, inventory and dates intact; the existing Submit for Approval action becomes available for retry when the error clears/busy state ends. The tests explicitly cover a failed request followed by a successful retry. Unconfirmed responses tell the seller to check My Products first because a server may have saved the product even if a complete confirmation was not received.

`showAddProductPage(context, onViewProducts, onBackHome)` continues to verify seller access before opening the existing route. The form returns a destination enum only after the user chooses an action or uses Back; the wrapper calls the appropriate callback while mounted and still returns `true` to existing refresh callers. The production Home callback uses `_openSellerTool(products)`/`_goToTab(0)`, and the seller workspace uses `_select(products)`/`_backHome`. Both reuse existing permissions, screen state and routes.

### 5. Backend / API behavior

Unchanged. The existing POST returns `product` including `id`, `name`, `price`, `category`, `images`/`image_url` and `approval_status`; the client now uses those fields for confirmation. No extra write, approval request, publication change, fake status or change to FIFO/image/expiry behavior. Pending listings stay under the existing Marketplace Admin approval workflow and existing public-list visibility rules. The notification sentence is the requested copy; this UI change does not implement or alter notification delivery.

### 6. Database / migration impact

None. No schemas, migrations, endpoints, dependencies, assets or working records changed. No new Flutter screen file: confirmation is private rendering in the existing Add Product route. No server restart or deployment.

### 7. Tests performed

- Final whole-project `flutter analyze --no-pub`: **No issues found**, 12.3 seconds.
- **43/43 Add Product tests passed in 31 seconds.** New checks verify actual server values that differ from the form draft, returned Pending/Archived status, absence of form/progress after success, no timed redirect, both navigation callbacks, Android Back without form return, one POST, incomplete/malformed response protection and preserved error/retry behavior. Existing inventory, image order, draft, expiry, tooltip, validation and responsive tests pass.
- Actual confirmation renders inspected at390dp normal text and280dp/200% text: `scratch/product-submission-confirmation-20261103/renders/`. Large content scrolls above accessible bottom actions. Thumbnail fixtures are transparent test PNGs; tests assert the actual returned image URL, while captures verify layout rather than real photo composition.
- The first focused run exposed a test timing issue: waiting for all animations during a deliberately unresolved request advanced the mock timeout. The helper now supports immediate pumping for that pending-request check; final tests verify disabled actions while it remains in flight. Const/flow-control and test-fixture lint issues were resolved before final analysis.
- No live API submission, backend test rerun or physical-device navigation test; backend code is unchanged. Navigation destination callbacks are exercised in widget tests; the production callback wiring was inspected directly.

Reproduce from `campushub/`: `flutter analyze --no-pub` and `flutter test --no-pub test/seller_add_product_page_test.dart`.

### 8. Remaining limitations / troubleshooting / safe practice

The successful response must contain the existing complete product fields; an older/incomplete server response shows an unconfirmed-submission error instead of guessing summary data. Client busy guards prevent ordinary repeated taps but are not a new backend idempotency system; after an uncertain network result, check My Products before retrying. Existing server permissions/public visibility remain authoritative.

Safe exercise: use the mocked confirmation tests, which deliberately return **Confirmed server product**, price35.75 and categorySnacks regardless of the form fixture. Verify those server values appear, wait3 seconds and confirm the screen remains, then use View My Products/Home/Android Back. Confirm no Review form is exposed and no second POST occurs. To manually inspect without creating working products, use the same local test harness; do not submit a real listing just to verify styling. If a button lands on the wrong screen, inspect its caller callback rather than adding a duplicate destination route.

## Current Add Product: required photos, Cover controls and bold peso - November 3, 2026

### 1. Cause / reason

The attached request makes one photo required in the mobile form and replaces Primary controls with automatic Cover assignment. The old grid put a large clickable Primary/Set primary button across each uploaded photo and allowed advancing without photos. The user's message also requests arranging/bolding the Philippine peso symbol in Selling Price.

### 2. Exact files changed and current anchors

- `campushub/lib/module_app/screens/seller_add_product_page.dart:372` `_continue` image guard; `:385` `_submit` image guard; `:558` Review image semantics; `:575` Review Cover label; `:601` `_navigation` disabled Next; `:697` `_removeImage`; `:720` `_showImageActions`; `:844` non-clickable Cover badge; `:872` `_images`; `:901` upload description; `:923` formats/size helper; `:934` missing-image feedback; `:1101` Selling Price prefix style.
- `campushub/test/seller_add_product_page_test.dart:61` bundled Inter setup; `:185` existing workflow Next helper now supplies the required fixture image; `:784` six-photo/order regression; `:847` Cover lifecycle tests at 390dp and 280dp/200% text. Imports include ProductImage, and the old no-photo Review expectation now checks the required fixture image.
- This existing guide and `CAMPUSHUB_CONTEXT.md` record the implementation and verification. No new application screen or component file.

### 3. Changes made

Step 3 says **Upload at least 1 photo (maximum 6).** Next is disabled when no image exists, with **Add at least 1 product photo to continue.** visible below the grid. Defensive continuation/submission guards also block an empty gallery. Existing format checks and 5MB-per-file limit remain. The helper now says **Supported: JPEG, PNG, WebP, GIF · Max 5 MB each** and the counter updates immediately.

The first image automatically becomes Cover. Only the Cover has a small non-clickable white status label and navy thumbnail outline. Each photo keeps its top-right 48dp remove target. Tapping an uploaded thumbnail opens a small native bottom sheet containing Replace photo and, for a non-cover photo when multiple images exist, Set as Cover. No large action button covers the thumbnail; a single image never offers Set as Cover. Existing gallery picker and thumbnails remain.

Removing a non-cover preserves the cover. Removing the cover promotes the first remaining photo. Removal compacts the remaining photos into the existing six slots; empty add-photo placeholders follow them. Removing all photos clears cover and disables Next. Normal width uses three columns; the existing narrow-screen two-column fallback is retained for readable status/removal controls. No progress/header/container redesign.

The Selling Price prefix remains `₱ ` in the input decoration, now explicitly Inter16/700 navy. Using the input's 16sp size keeps it on the same text baseline as the entered amount. Price parsing and the existing label remain unchanged.

### 4. How it works / functions, inputs, outputs and data flow

`_pickImages` still validates every selected file before changing any slots; its existing `_primaryImage ??=` automatically chooses the first image. The internal variable/keys are preserved for compatibility while visible text says Cover. `_showImageActions(index)` receives the tapped occupied slot, returns a native-sheet action, then changes only `_primaryImage` or invokes the existing picker for replacement. Cancelling the sheet changes nothing. IgnorePointer makes the Cover label status text rather than a separate button.

`_removeImage(index)` computes surviving original indices and the surviving/promoted Cover. It copies the surviving image data into the existing fixed-length list using `setAll`, pads the unused slots with null and translates the cover to its new slot index. This avoids both stale cover indices and changing the six-slot list length. The first verification caught an invalid `clear()` on that fixed list; it was corrected before the passing tests.

```text
Photos [A, B, C], Cover C -> remove B -> slots [A, C, null, ...], Cover index 1
_orderedImages -> [C, A] -> existing ProductService images JSON -> Django
Remove C -> slots [A, null, ...], Cover A
Remove A -> all null -> no Cover, Next disabled
```

Draft image data and `_primaryImage` remain screen-owned, so changing steps preserves both. The footer reads `_imageCount` to disable Next on Step 3 only. `_continue` provides an additional guard; `_submit` returns to Step 3 with feedback if an empty image draft ever reaches Review. Other form validation, stock fields, approval and route behavior remain.

### 5. Backend / API behavior

Unchanged endpoints, fields and authentication. `_orderedImages` already places the selected cover first, followed by the other images; ProductService sends the same `images` array. Django's existing serializer uses `images[0]` as `image_url` for marketplace cards/search/listings (`backend/core/api/views.py:232`), so no new cover flag or renamed backend field is needed. The minimum-one-photo requirement is enforced in this mobile form; the backend's optional-image compatibility for other existing clients is unchanged. FIFO, approvals and image validation/storage services were not modified.

### 6. Database / migration impact

None. No schema, migrations, dependencies, assets, working records, new endpoints or deployment changes. Tests use in-memory photo fixtures and mocked HTTP submission.

### 7. Tests performed

- Final two-file `flutter analyze --no-pub`: **No issues found**, 4.2 seconds.
- **38/38 Add Product tests passed in 29 seconds.** Four focused gallery checks previously passed in10 seconds, including lifecycle tests at390dp and280dp with200% text.
- Covers disabled empty Next, automatic first Cover, single-photo controls, changing Cover, removing non-cover/cover/all images, counter and compact slot updates, retained Cover across Review/back, first-image submission order, six-image limit, cancelled/invalid picker selections and bold peso prefix. Existing other step/draft/expiry/permissions/submission checks pass.
- Actual normal and enlarged-text gallery renders inspected at `scratch/add-product-cover-20261103/renders/`; test thumbnails use transparent one-pixel fixtures, so these renders verify controls/layout rather than real photo composition. The complete suite now always loads bundled Inter even without screenshot capture: placeholder test glyphs caused spurious large-text failures before that setup correction. Old optional-photo assumptions were updated to provide a fixture before advancing.
- Backend tests were not rerun because backend source/contracts are unchanged; the existing serializer's first-image behavior was inspected directly.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device image permissions/gallery session or hosted upload/deployment was performed. Required images apply to this mobile form, not every API client. A disabled Next cannot receive a tap, so missing-image guidance is displayed immediately; the defensive callback guards also retain the message if invoked programmatically.

Safe exercise: from `campushub/`, run `flutter test --no-pub test/seller_add_product_page_test.dart`. In a local draft, add one photo and confirm Cover/Next, add another and tap it for Set as Cover, remove each photo and inspect promotion/count. Advance/back to confirm retention without submitting working records. If cover order is wrong, inspect `_orderedImages` and cover-index translation rather than adding a new payload field. Keep `setAll` for the fixed six-slot list; clearing/resizing it is invalid.

## Current Add Product: revised stock descriptions and explicit header color - November 3, 2026

1. **Cause / reason:** The user supplied shorter stock descriptions and reported missing Add Product header text. Inspection confirmed the title was still present; its shared style had no explicit text color. Inherited color is a possible visibility cause, not a confirmed device diagnosis.
2. **Exact files changed:** `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart:241` (radio accessibility descriptions), `:276` (visible descriptions); `campushub/lib/module_app/screens/seller_add_product_page.dart:911` (existing AppBar title), `:912` (shared header style with navy color); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Standard Stock now says **Enter the number of items available for sale.** Batch Tracking now says **Organize your items based on when you restock them.** The same wording is used by screen-reader labels. The existing centered Add Product title explicitly uses navy `#0B1F3A` on white, retaining Inter20/600. No duplicate title, divider or outer container was added.
4. **How it works / data flow:** `ProductInventorySelector(value, onChanged)` still maps `simple`/`fifo` to the same cards and callback; only the displayed/semantic descriptions changed. The existing Scaffold AppBar remains above the scrollable form on every step. `AppTypography.screenHeader.copyWith(color: ProductFormStyle.navy)` keeps the shared font role and supplies a local foreground color, avoiding reliance on inherited title color. Example: Step 2 displays Add Product at the top and the updated descriptions underneath the unchanged method names.
5. **Backend / API behavior:** Unchanged. No submitted values, validation, FIFO allocation, threshold/expiry logic, authentication, navigation or approval behavior changed.
6. **Database / migration impact:** None. No schema, migrations, dependencies, assets or new files.
7. **Checks performed:** Two-file `flutter analyze --no-pub` reported **No issues found** in2.5s. Source inspection confirmed the exact descriptions and explicit title color. No tests or app/device renders were run, following the user's earlier testing preference.
8. **Remaining limitations / troubleshooting / safe practice:** Header visibility has not been verified on the reported device. Optional manual check: hot restart the app, open Add Product, navigate to Step 2 without submitting and confirm the navy title and both descriptions. If the title is still absent, confirm that the running build uses this existing screen/route before adding another header. Existing font/copy-specific test expectations were not rerun or updated in this small edit.

## Current Add Product: shared Inter typography and stock help - November 3, 2026

1. **Cause / reason:** The latest request standardizes the mobile UI on the already bundled Inter font and supplies explanations for Standard Stock, Batch Tracking and Low Stock Threshold. It supersedes earlier Poppins/Montserrat choices.
2. **Exact files changed:** Add Product uses `campushub/lib/module_app/theme/app_typography.dart:51` (`AppTypography`, shared roles/theme), `campushub/lib/module_app/screens/seller_add_product_page.dart:479` (progress), `:491` (review), `:679` (section titles), `:873` (scoped theme), `:910` (header), `:1125` (threshold help); `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart:61` (labels), `:86` (configurable tooltip), `:97` (explanations), `:198` (stock selector); `product_expiry_field.dart:149` and `product_tag_input.dart:144` (shared roles). Global application files and their exact anchors are listed in [the typography guide](mobile-typography.md:3). This guide and `CAMPUSHUB_CONTEXT.md` record the update.
3. **Changes made:** Inter roles apply to all four steps: header20/600, section18/600, stock title14/600, labels14/500, inputs16/400, helpers/tooltips13/400, progress13/500, buttons16/600 and errors13/500. Existing navy/gold/white/red colors remain. Standard Stock now has an info icon too; Batch Tracking uses the latest supplied explanation; threshold help appears beside its label. Existing stock descriptions are retained.
4. **How it works:** `AppTypography.theme(base)` merges typography into existing colors and component settings; named const styles avoid repeating role sizes. Parent-owned drafts, fields, four-step progress and navigation remain. Existing `ProductInventoryInfo` accepts optional title/message/keys and is reused for all three explanations. Its icon only opens the bounded tap/long-press/hover tooltip and does not call selection/threshold callbacks. Example: opening Standard Stock help leaves the method `simple` and quantity unchanged. Full function/input/output and data-flow explanations are in the linked typography guide.
5. **Backend / API behavior:** Unchanged, including `simple`/`fifo` identifiers, receipt/expiry notes, approval, ownership and Django FIFO allocation.
6. **Database / migration impact:** None. No endpoints, schema, migration, dependencies or assets changed; existing Inter asset reused.
7. **Checks performed:** Whole-app `flutter analyze --no-pub` reported **No issues found**, final run7.8s; source formatted; bundled Inter inspected for peso glyph and requested weights. No tests/render/device checks were run. Earlier results below describe earlier implementations only.
8. **Remaining limitations / safe practice:** App-wide visual fit and previous font-specific test expectations are not verified by analysis. Existing text scaling is retained. Optional manual exercise: open Add Product at large text size, navigate all steps without submitting, open the three stock/threshold explanations and check unchanged inputs. Exact role table, changed-file list, limitations and troubleshooting: [mobile typography](mobile-typography.md:3).

## Current Add Product: Standard Stock and Batch Tracking cards - November 3, 2026

1. **Cause / reason:** The latest request replaces the earlier Simple Stock/Batch Inventory wording with Standard Stock/Batch Tracking. The earlier card placed the info icon beside the title in a Wrap and aligned the radio at the top. The requested layout centers the radio, keeps title/description together and places help at the right edge.
2. **Exact files changed:** `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart:13` (`selectedSurface`), `:89` (tooltip explanation), `:159` (help semantics), `:190` (`ProductInventorySelector.build`), `:224` (radio semantics), `:251` (titles), `:265` (descriptions), `:296` (12dp spacing); `campushub/lib/module_app/screens/seller_add_product_page.dart:514` (Review Stock Method wording); `campushub/test/seller_add_product_page_test.dart:515` (review expectation), `:622` (help label), `:633` (outside-dismissal location), `:671` (stock-card checks from the interrupted preceding task, updated copy). This guide and `CAMPUSHUB_CONTEXT.md` are updated; no new files were created for this request.
3. **Changes made:** Titles/descriptions are exactly **Standard Stock** / **Manage all your items using one total quantity.** and **Batch Tracking** / **Manage stock separately for each restock or delivery.** Review and screen-reader labels use the same terminology. Batch Tracking help says **Batch Tracking records stock separately for each restock or delivery. When an order is fulfilled, the system uses the oldest available batch first.** Existing `Icons.info_outline` supports tap/long press/hover. Cards have equal 16dp padding, 12dp corners, a 12dp gap, a navy selected border/radio and subtle `#F7F8FC` selected surface; unselected cards remain white with a light border and no shadows.
4. **How it works / functions and data flow:** `ProductInventorySelector(value, onChanged)` still receives `simple` or `fifo` from the screen. RadioGroup handles radio/keyboard selection; the card InkWell calls the same callback when its body is tapped. A centered Row holds the radio and Expanded text Column, with the description 4dp below the title. The batch text reserves 48dp for an independently positioned info target, preventing overlap. Its position follows the first title line's scaled height, keeping the icon aligned when text size changes. `_ProductInventoryInfoState` still opens only its tooltip; it never calls `onChanged`. The bounded/scrollable native tooltip and grouped outside-dismissal behavior remain. Example: tapping **Standard Stock** still sets `simple`, which displays the existing quantity field; tapping **Batch Tracking** sets `fifo`, which displays the existing batch fields. Review translates those values to the new labels only. Drafts, expiry and thresholds remain parent-owned.
5. **Backend / API behavior:** Unchanged. No requests, identifiers, `simple`/`fifo` constants, receipt persistence, allocation rules, ownership or approval logic changed. FIFO continues in Django.
6. **Database / migration impact:** None. No schemas, migrations, working records, dependencies or new components/screens/files were added for the latest request.
7. **Tests performed:** **No tests or analysis were run after the user's instruction to stop testing.** Source inspection confirms the latest displayed labels/descriptions and unchanged internal identifiers. Before that instruction, the interrupted preceding task's focused run completed with three passing checks and one failing narrow-tooltip assertion; it is not verification of this final wording. That assertion observed a changed selection after an outside-dismissal tap at y=60, which can land on scrolled card content; its dismissal point is now the inert header title at y=28. The existing expectations were synchronized with the renamed UI without adding further test cases or running them. Final runtime behavior is unverified.
8. **Remaining limitations / troubleshooting / safe practice:** Text wraps naturally at narrow widths or enlarged text rather than being clipped into a fixed card height. No final render/device check or deployment was performed, per the requested limited verification scope. Optional manual practice: open Step 2, tap each card body and confirm the corresponding existing fields; enter a quantity, switch methods/back and confirm retained data. Tap or long-press the info icon and confirm selection stays unchanged. Advance to Review and confirm the new method label without submitting a working product. If the API identifier changes with the wording, restore `simple`/`fifo`; only presentation text should be renamed.

## Current Add Product: optional expiry field and per-batch dates - November 3, 2026

### 1. Cause / reason

The requested interaction is a single optional date field with an explanatory info icon, not a separate expiry question. The inspected screen already had an optional product-level button (no Yes/No question), but lacked the requested field styling/help and placed that same product date below both stock methods. Initial batch payloads supported quantity, received date and unit cost, with no dedicated batch expiry column.

### 2. Exact files changed and current code anchors

| File relative to project root | Current line / anchor | Purpose |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/seller/product_expiry_field.dart` | 8 `ProductExpiryField`; 27 `format`; 59 optional FormField; 69 `choose`; 89 dialog theme; 173 `_ExpiryHelpState` | New reusable field, calendar, clear action and tooltip. |
| `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart` | 64 `ProductBatchDraft`; 68 `expiryDate`; 70 `toJson`; 422 `if (showExpiry)` | Retains each batch's optional date and renders its field only when requested by the parent. |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | 277 nonperishable-category handling; 405 batch payload; 415 simple expiry payload; 524 batch review; 528 simple review; 1107 `showExpiry`; 1183 `product-expiry` | Replaces the former date button and removes `_chooseExpiry`; selects simple/per-batch placement and reviews actual selected dates. |
| `campushub/lib/module_app/services/seller_application_service.dart` | 248 `hasExpiry`; 252 `initial_batch_expiry` | Rejects unsupported server versions before submitting selected batch dates. |
| `backend/core/modules/marketplace/services/product_initial_inventory.py` | 38 optional expiry parsing; 62 receipt notes | Validates supplied batch dates and persists them in the existing receipt notes. |
| `backend/core/api/views.py` | 774 listing GET `capabilities` | Advertises additive `initial_batch_expiry: true` on the existing authenticated endpoint. |
| `campushub/test/seller_add_product_page_test.dart` | 1243 simple selection/null; 1290 independent batch dates/compatibility; 1398 tooltip | Adds behavior, submission, retention and responsive tooltip tests; updates the old clear-date assertion for the icon. |
| `backend/core/api/test_mobile_seller_application.py` | 240 persisted expiry metadata; 276 invalid date cases | Verifies actual receipt records, optional dates and atomic rejection of malformed/past batch dates. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current entry | Records implementation, contract limits, verification and safe practice. |

### 3. Changes made

Step 2 now shows **Expiry Date (Optional)** with `Icons.info_outline` immediately after the label, a full-width rounded input, calendar icon and **Leave blank if not applicable.** helper. A selected date displays as `MMM dd, yyyy`; its X clears the nullable draft. The field itself and calendar icon open the same Material dialog, with dimmed background, Cancel/OK, white surface and navy selected date. Today and future dates are selectable; past dates are disabled. The form remains on Step 2 after selection/cancellation.

Simple Stock uses one field; Batch Inventory places one inside each batch and hides the product-level field. Existing food-category detection remains authoritative: Rice Meals, Snacks, Desserts, Beverages, Combo Meals and Breakfast. School Supplies and Clothing do not show expiry. No new category values, outer wrapper, screen or question was introduced. The four steps, progress, bottom actions, approval and other form fields remain.

### 4. How it works / functions, inputs, outputs and data flow

`ProductExpiryField(id, value, onChanged, decoration, enabled)` takes a nullable date from the existing screen or batch draft. `choose()` opens `showDatePicker` with today's date as its minimum. A past retained value cannot crash the picker: opening starts at today, while validation asks the seller to replace/clear a past date. Cancel leaves the value untouched. OK calls `state.didChange(picked)` and the parent callback; X calls both with `null`. `format()` changes display text only; network dates still use ISO `YYYY-MM-DD`.

`_ExpiryHelpState` uses the native Tooltip for long press/hover, plus `ensureTooltipVisible()` for normal tap. Its navy/white explanation is bounded by the viewport, dismisses on outside tap and uses the existing 12-second duration. The icon retains a 48dp minimum target and a screen-reader label. Large text can wrap labels and helper text.

Simple dates remain in `_expiry`; batch dates remain in `ProductBatchDraft.expiryDate`. Moving Back/Next or switching stock methods does not clear either draft. As before, changing to a nonperishable category clears incompatible expiry dates; dates cannot leak into that category's submission. Simple Stock sends the existing product `expiry_date`. Batch Inventory sends each selected date as optional `initial_batches[i].expiry_date`; it sends no product-level date, avoiding an inaccurate date applied to every batch. Unselected/cleared dates remain null in memory and are omitted from JSON, preserving the existing optional-field convention; Django stores no product expiry/no batch-expiry note. Missing expiry means unspecified, not proof that a product never expires.

Annotated example using test values:

```text
Batch 1: received 2026-11-03, expiry 2026-11-05
  -> initial_batches[0].expiry_date = "2026-11-05"
  -> Django validates ISO date >= local today
  -> that batch's receipt_movement.notes contains "Expiry date: 2026-11-05"
Batch 2: no selected expiry -> no expiry note; no 'never expires' flag
```

### 5. Backend / API behavior

The existing authenticated `/api/seller/products/submit/` route accepts an additive optional expiry key inside initial batch rows. `validate_initial_batches()` accepts missing/null/blank dates, rejects invalid ISO dates or dates before Django's local today, and combines a selected date with the existing unit-cost receipt notes. `save_initial_batches()` still performs the same atomic stock/receipt saves. Capability checking prevents an older server from silently ignoring a selected date; it leaves the review and draft available with a clear error. Old no-expiry clients remain compatible.

**Storage limitation:** InventoryBatch has no expiry column. This change preserves batch dates as receipt metadata, matching the existing cost-note approach. It does not add automatic per-batch expiry filtering, FEFO allocation, or a product-wide earliest-expiry rule. The backend's existing FIFO allocation and product expiry rules remain unchanged. ProductService, routes, authentication/ownership and approval rules are unchanged.

### 6. Database / migration impact

No model/schema changes or migrations. Uses the existing nullable Product expiry field and InventoryStockMovement notes linked to each batch. No dependencies, working records, production deployment or server restart changed.

### 7. Tests performed

- Five-file Flutter analysis: **No issues found**.
- **48/48 Flutter tests passed in 37 seconds** across Add Product, seller receiving and seller application. After the final calendar surface-only correction, **7/7 expiry tests passed in 11 seconds**.
- **46/46 Django tests passed in 7.902 seconds**, using the existing isolated PostgreSQL test runner; Django system check reported no issues. Covers selected/unknown batch dates in actual receipt notes, combined unit cost, malformed/past rejection without partial records, and existing seller workflows. The first run found a missing food-category test fixture; the fixture was corrected before this passing run.
- Flutter checks cover today-only minimum, Cancel/OK, exact display/ISO values, clear-to-null submission, per-category visibility, independent dates retained across steps/methods, no duplicate product date, old-server no-write protection, and tooltip tap/long press/hover/outside dismissal at 390dp and 280dp with 200% text. Initial new submission tests used a helper that restarted Step 1; corrected those test calls to advance from their actual step, then reran.
- Actual selected/simple, batch, narrow tooltip and dimmed white calendar renders inspected. Evidence: `scratch/add-product-expiry-20261103-tests.log`, `scratch/add-product-expiry-20261103-focused.log`, and `scratch/add-product-expiry-20261103/renders/`.

Reproduce from `campushub/`: `flutter test --no-pub test/seller_add_product_page_test.dart test/seller_stock_receiving_test.dart test/seller_application_test.dart`. From the project root: `backend/core/venv/Scripts/python.exe scratch/mobile-add-product/run_image_tests.py` (isolated test database, FCM disabled).

### 8. Remaining limitations / troubleshooting / safe practice

This existing Add Product route creates listings; it has no product-edit mode or saved-product loader. No edit workflow was invented or changed. The reusable date widget accepts a supplied nullable value, but loading an existing product into an editor remains outside this create-only route. Batch expiry notes are persisted metadata rather than a dedicated queryable expiry field. Mobile calendar boundaries use the device's local date; Django validates batch dates against its configured local date. No physical-device keyboard/TalkBack test or hosted deployment was performed.

If a selected batch date cannot submit, inspect the server capability instead of removing the compatibility guard. If the date appears twice, verify `product-expiry` is restricted to Simple Stock. If a date vanishes when switching methods, check that its value still belongs to the parent draft rather than local widget state.

Safe exercise: in the mocked test flow, choose Snacks, leave the simple expiry blank and advance/back. Select today, cancel a replacement, then clear it; verify Step 2 and the null value. Switch to Batch Inventory, enter two valid quantities/received dates, select different expiry dates, switch methods/back and inspect Review. Run the tests above and verify receipt-note assertions without creating products in the working database.

## Current Add Product: remove header divider - November 3, 2026

1. **Cause / reason:** The AppBar explicitly drew a gray bottom border. The user requested removing this header line while keeping step progress and input outlines.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:970` (AppBar, immediately after `leading: BackButton`); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Removed the AppBar's `shape: Border(bottom: BorderSide(color: _line))` property. Existing zero elevation and zero scrolled-under elevation remain; no header divider or replacement shadow is added.
4. **How it works / data flow:** The AppBar now renders its existing white surface without the custom bottom border. Its BackButton still calls `_back`; form values and navigation are untouched. `_progress()` at line 445 separately renders the step indicator from `_step`, so removing the header border does not remove the progress track. Input decoration still supplies field outlines. Example: Step 1 retains its gold progress segment and gray remaining track below the now borderless header.
5. **Backend / API behavior:** Unchanged; this single presentation-property removal adds no requests or data transformations.
6. **Database / migration impact:** None. No schema, migrations, records or dependencies changed.
7. **Tests performed:** Single-file Flutter analysis reported **No issues found**. The existing `four active sections, left progress and right label fit 390.0/844.0/1.0` test passed (**1/1**, 2 seconds), exercising all four steps. Actual Step 1 render inspected: header divider absent, progress and input outlines present. Captures: `scratch/add-product-header-20261103/renders/`.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device session or deployment was performed. Safe exercise: open Add Product and compare the white header with its separate progress track; enter sample values and use Next/Back without submitting. If a divider reappears, inspect this AppBar's shape or inherited AppBarTheme rather than removing `_progress()` or field borders.

## Current Add Product: category dropdown alignment - November 3, 2026

1. **Cause / reason:** The former popup used the field's coordinates captured once when opened. A regression test confirmed that closing the keyboard could move the form while leaving the popup at its old position, 170dp above the expected position in the test. The user requested aligning the dropdown with its field.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:32` (`_categoryLink`), `:255` (`_categoryField`), `:1018` (Category field call); `campushub/test/seller_add_product_page_test.dart:1223` (keyboard alignment regression), `:1257` (responsive menu bounds); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** The Category popup now uses Flutter's native MenuAnchor linked to the existing field. LayoutBuilder gives the menu the field's actual width. Its left/right edges match the input, with a 4dp gap below it when space permits, existing white/navy styling and rounded corners. Category titles, form spacing and other fields remain unchanged.
4. **How it works / functions and data flow:** `_categoryField(categories)` receives the existing category list and builds the same validated FormField. Tapping its InkWell dismisses typing focus and opens/closes the anchored menu. `_categoryLink` lets the menu follow the field when keyboard insets move it; width constraints come from the field rather than screen-wide guesses. MenuItemButton selection updates `_category`, clears expiry for nonperishable categories as before, and calls `state.didChange(category)` so validation receives the selected value. The menu closes after selection or an outside tap. Example: select Snacks, reopen the menu, then dismiss it outside; Snacks remains selected and flows into the existing review/submission payload. Empty-category and busy guards remain.
5. **Backend / API behavior:** Unchanged. Existing category values, requests, authentication, approval, product service and FIFO business rules remain. Six protected integration/backend source hashes match; the alignment fix makes no new API requests.
6. **Database / migration impact:** None. No schema, migrations, records, endpoints or dependencies changed.
7. **Tests performed:** **28/28 Add Product tests passed in 23 seconds.** Two-file Flutter analysis reported **No issues found**. New checks verify matching left/right edges and width at 280dp, 390dp and 640dp, selection retention, outside-tap dismissal and alignment after a simulated 280dp keyboard closes. The keyboard regression failed against the former implementation and passes with the anchor. Actual form renders were inspected, including the keyboard-close case. Evidence: `scratch/add-product-category-align-20261103-tests.log` and `scratch/add-product-category-align-20261103/renders/`.
8. **Remaining limitations / troubleshooting / safe practice:** Physical-device keyboard and screen-reader testing were not performed; no deployment or backend test run was needed for this Flutter-only fix. Flutter may move the menu vertically to fit limited screen space. If alignment regresses, check that MenuAnchor still receives `_categoryLink` and both width constraints still use `constraints.maxWidth`. From `campushub/`, run `flutter test --no-pub test/seller_add_product_page_test.dart`; safely select a category, open/close the keyboard and reopen/dismiss the menu without submitting a product. Confirm matching edges and retained selection.

## Current Add Product: compact Tags height and close help icon - November 3, 2026

1. **Cause / reason:** The shared Tags outline inherited the ordinary field's 15px top/bottom padding on top of its inner entry/chip height. This made the combined field taller than Product Name. The user requested matching normal input height and placing the info glyph immediately after the label.
2. **Exact files changed:** `campushub/lib/module_app/widgets/seller/product_tag_input.dart:107` (54dp minimum/content padding), `:111` (50dp minimum content to match the visible border), `:114` (Wrap spacing), `:152` (120dp typing width with chips), `:177` (inner entry padding), `:222` (help icon padding/alignment); `campushub/test/seller_add_product_page_test.dart:1043` (normal input-height comparison), `:1189` (4dp glyph gap); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Tags uses the same 14dp horizontal inset as ordinary inputs, 2dp outer vertical padding, 6dp inner entry padding, 6dp chip gaps and 2dp row gaps. Its empty/single-chip height matches the normal input at standard text size. The info glyph starts 4dp after Tags (Optional), with zero internal icon padding and start alignment, while its tappable button remains at least 48x48dp.
4. **How it works:** `ProductTagInput` still receives the same `tags`, `entry`, `decoration` and enabled state. Only layout values change: its shared InputDecorator and 50dp minimum content apply minimum heights rather than a fixed maximum, so multiple chip rows and larger text can grow naturally. A shorter typing area avoids wrapping a single chip onto an extra row unnecessarily. `ProductTagsHelp` keeps the same Tooltip behavior and callback; moving the glyph within its full-sized button changes visual proximity without shrinking its tap target. Example: one short tag and the Add a tag entry fit within the same compact outline; additional tags wrap as needed. Enter/comma/removal/Next -> canonical tags -> Review/API data flow is unchanged.
5. **Backend / API behavior:** Unchanged. No tag parsing, validation, payload, route, approval or FIFO business-rule changes.
6. **Database / migration impact:** None. No schema, migrations, dependencies, assets, working records or deployment changes.
7. **Tests performed:** Two-file Flutter analysis reported **No issues found**. The existing Add Product suite checks compact empty/single-chip height, comparison of both layout and visible border height with the actual Product Name border container, excluding its character counter, exact info-glyph gap, retained tag submission, tooltip access, long-tag wrapping and other form workflows. **24/24 Add Product tests passed in 18 seconds**; actual compact-field render inspected. The border-height test excludes the Product Name counter and checks the painted container rather than only overall layout height. Captures: `scratch/add-product-tags-compact-20261103/renders/`.
8. **Remaining limitations / troubleshooting / safe practice:** Multiple rows or enlarged text can still increase the field height; no content is forced into a clipped fixed box. Physical-device keyboard/TalkBack and deployment were not performed. Safe exercise: run `flutter test --no-pub test/seller_add_product_page_test.dart` from `campushub/`, enter one short tag and compare the outline with an ordinary input, then add several tags and confirm wrapping/X removal. Tap just after the label to open help. Do not alter API values or create working products to check field size.

## Current Add Product: tags inside the field and instructions in a tooltip - November 3, 2026

1. **Cause / reason:** The user requested moving the visible tag helper text into an information tooltip and placing the chips inside the input border. Previously, the text field and chip Wrap were separate children, so accepted tags appeared below the field.
2. **Exact files changed:** `campushub/lib/module_app/widgets/seller/product_tag_input.dart:95` (`build`, outer InputDecorator), `:147` (borderless inner TextFormField), `:182` (`ProductTagsHelp`); `campushub/lib/module_app/screens/seller_add_product_page.dart:671` (`_label` optional labelAction), `:681` (flexible label), `:1074` (Tags help icon); `campushub/test/seller_add_product_page_test.dart:1048` (chip containment), `:1124` (tooltip tests). This guide and `CAMPUSHUB_CONTEXT.md` record the accepted layout.
3. **Changes made:** A single rounded Tags field now encloses both removable chips and the typing area. Chips wrap inside the border. The instructions appear only when the seller taps/long-presses the information icon beside Tags (Optional), or hovers over it with a mouse. The full-tag/removal tooltips and existing X actions remain. No permanent helper paragraph is displayed underneath.
4. **How it works / inputs, outputs and data flow:** `ProductTagInput(tags, entry, decoration, enabled)` keeps the same parent-owned controllers and conversion rules. Its outer InputDecorator receives the existing field decoration, while its inner TextFormField has no border. A local FocusNode updates the shared outline when typing; tapping the field background focuses the entry. The FocusNode listener is removed and disposed with the widget. The Wrap contains accepted InputChips and a constrained typing area, growing vertically as needed. The outer hint is explicitly empty so only the inner entry draws the placeholder; `copyWith(hintText: null)` would retain the old hint and duplicate it. `ProductTagsHelp` uses the native Tooltip with a navy surface, white text, a bounded width and a 12-second display duration. `_label` accepts an optional action and lets the label wrap at large text sizes, avoiding an overflow beside the icon. Data still flows Enter/comma -> same canonical comma-separated controller -> Review -> unchanged ProductService payload; Next still commits unfinished text.

   Annotated test-only example: entering `local,` creates a local chip inside the outline; typing fresh continues alongside it when space permits. Next saves fresh as before. Removing local with X produces the existing `fresh` API value, without a separate tag endpoint or new model.
5. **Backend / API behavior:** Unchanged. Six protected route/client/backend/FIFO hashes match. Optional tags retain the established string contract; authentication, stock, approval and submission behavior are preserved.
6. **Database / migration impact:** None. No schema, migrations, dependencies, assets, working records or deployment changes. Only the two Flutter UI files and existing test/documentation files change.
7. **Tests performed:** The Add Product, receiving and seller-application suites cover the updated embedded tags plus existing workflows. Added checks measure each chip inside the field border, ensure instructions are absent until opened, and exercise tooltip tap, long press, mouse hover, outside dismissal and screen bounds at 390dp and 280dp/200% text. Three-file Flutter analysis reported **No issues found**. Actual normal/large-text chip and help renders were inspected. The first verification caught a 16px label-row overflow at 200% text; Flexible now permits wrapping. An import-order error and duplicated empty-field placeholder were also corrected. Final verification: **38/38 Flutter tests passed in 20 seconds** across the three suites. Evidence: `scratch/add-product-tags-inline-20261103-tests.log` and `scratch/add-product-tags-inline-20261103/renders/`.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device keyboard/TalkBack session or hosted API check was performed. Long chips still ellipsize with a full-tag tooltip; drafts remain in memory until the route closes. If a second outline appears, check the inner InputBorder.none settings. If the empty placeholder repeats, verify the outer decorator's hint is an empty string, not null. Safe exercise: run `flutter test --no-pub test/seller_add_product_page_test.dart` from `campushub/`; enter two test tags, remove one, open the info icon and advance/back. Confirm accepted chips remain inside the outline and no instruction paragraph remains beneath it. Use the mocked workflow; do not create working products for a layout check.

## Current Add Product: bottom actions, red validation and removable tags - November 3, 2026

### 1. Cause / reason

The user requested lower buttons, red required/error text and tags that become removable chips with understandable instructions. Confirmed causes: `_navigation` was the last child of the scrolling form, so it followed content rather than staying at the screen bottom; the form-local ColorScheme explicitly assigned navy to error; Tags was an ordinary comma-separated text field without an add/remove interaction.

### 2. Exact files changed and current anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | 37 `_tagEntry`; 75 disposal; 350 `_continue`; 659 error decoration; 676 `ProductFieldLabel`; 899 ColorScheme error; 1057 `ProductTagInput`; 1275 `product-form-navigation` | Retains a separate unfinished tag entry, commits it on Next, renders tag chips, uses red errors/required markers and places navigation below the scroll area inside SafeArea. Image/submission errors also use the scoped red. |
| `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart` | 12 `ProductFormStyle.error`; 37 `ProductFieldLabel`; 293 batch field label | Adds the form-local red `#B91C1C` and a reusable label that colors only the required asterisk. Batch quantity/date labels share it. |
| `campushub/lib/module_app/widgets/seller/product_tag_input.dart` | 7 `ProductTagInput`; 28 `_add`; 39 `commit`; 72 `_changed`; 98 helper text; 113 InputChip; 122 removal | New reusable chip input backed by the existing comma-separated tag controller, with Enter/comma addition, duplicate suppression, full-tag tooltips, accessible removal labels and responsive long-tag constraints. |
| `campushub/test/seller_add_product_page_test.dart` | 954 footer/keyboard; 979 red errors; 1029 tag submission; 1087 long tags | Adds behavior checks and updates retained-tag expectations to assert chips instead of raw input text. |
| This guide and `CAMPUSHUB_CONTEXT.md` | Current entry | Records exact changes, functions/data flow, verification, limitations and a safe exercise. |

### 3. Changes made

Next, Back and Submit remain in the existing navigation widget, now in a separate bottom area outside the Expanded scroll view. SafeArea and Scaffold keyboard resizing keep them above system insets/the keyboard. Content remains unboxed and scrollable, with 16px horizontal padding. Existing gold-to-navy progress and all four steps remain.

The scoped error color is now red. Validation messages, normal/focused error borders, required asterisks and image/submission errors use it; ordinary labels and main branding stay navy. This fixes the theme cause rather than only recoloring one required message.

Tags become neutral removable chips when the seller presses Enter or types a comma. Helper text says: Type a tag, then press Enter or a comma to add it. Tap × to remove. The placeholder supplies examples. A tag's tooltip retains its full text if its chip label is ellipsized; its X has a Remove tag [name] tooltip/semantic action. Next commits unfinished text automatically. Values survive backward navigation and continue to appear in Review.

### 4. How it works: functions, inputs, outputs and data flow

The Form now contains a Column with `Expanded(SingleChildScrollView(...))` and a bottom Padding containing `_navigation`. Scrolling therefore moves only the content; it does not move the actions. No new outer card or visible wrapper was added. The existing busy flags and callbacks still control the same buttons.

`ProductFieldLabel(label)` renders the label as TextSpan content, using the current form error color only for a trailing required marker. `_decoration` supplies red error styles and borders to ordinary inputs, the category decorator and reusable batch fields. The scoped ColorScheme is the shared error source for this screen.

`ProductTagInput` receives two parent-owned controllers: `tags` stores the established API value; `entry` holds unfinished typing. `values(tags)` parses trimmed, nonempty, unique tags in insertion order. `_changed` splits completed comma/newline entries into chips while leaving the last unfinished part editable. `commit(tags, entry)` adds every remaining nonempty part and clears only the entry field. `_continue` calls commit on Step 1 before validation, preventing loss when the seller taps Next without pressing Enter.

`_add` uses an ordered set to avoid duplicate exact tags; removing a chip rewrites the existing canonical string without that tag. The widget listens to that controller for changes and removes its listener when unmounted. The parent retains/disposes both controllers, so changing steps never loses accepted tags. No second product model or API was introduced.

```text
Typing -> entry controller -> Enter/comma -> removable chips + existing tags string
Next -> commit unfinished entry -> existing required-field validation
Review -> same tags string -> unchanged ProductService tags field -> Django
```

Annotated example, test data only: enter homemade and press Enter, then enter local, homemade,. The chips contain homemade and local once each. Remove homemade and type fresh without pressing Enter. Next commits fresh; Review and the existing POST contain `local, fresh`. The user never has to type or edit the serialized comma-separated value.

### 5. Backend / API behavior

Unchanged. The existing optional `tags` string is still sent through ProductService; Django retains its existing normalization/storage rules. Six protected route/client/backend/FIFO source hashes match. Authentication, approval, batch allocation, price/stock validation, image handling and product submission behavior remain. No requests occur merely from adding/removing a tag or scrolling the content.

### 6. Database / migration impact

None. No models, endpoints, migrations, dependencies, assets or working data changed. No physical device, server restart, app installation or production deployment was performed. The error token is scoped to this form rather than changing the global theme.

### 7. Tests performed

**36/36 Flutter tests passed in 19 seconds** across the Add Product, seller receiving and seller application suites. Four-file analysis reported **No issues found**. New tests verify footer position before/after scrolling, movement above a simulated 280dp keyboard inset, red required asterisks/error text/focused borders, Enter/comma addition, duplicate suppression, X removal, Next committing unfinished text, retained chips across steps, exact submitted tag payload and long tags at 280dp/200% text. Existing draft/approval/batch/photo/permission/navigation tests continue to pass.

Actual bundled-font renders for normal layout, red validation errors, chips and simulated keyboard insets were inspected. Captures are under `scratch/add-product-footer-tags-20261103/renders/`. A simulated keyboard inset reserves space; it is not a physical keyboard screenshot. Six protected integration hashes match. Backend tests were not rerun for this Flutter-only change.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/seller_add_product_page_test.dart test/seller_stock_receiving_test.dart test/seller_application_test.dart
flutter analyze --no-pub lib/module_app/screens/seller_add_product_page.dart lib/module_app/widgets/seller/product_inventory_fields.dart lib/module_app/widgets/seller/product_tag_input.dart test/seller_add_product_page_test.dart
```

### 8. Remaining limitations, troubleshooting and safe practice

No physical-device keyboard/TalkBack or hosted API verification was performed. Drafts remain in memory until the route closes. Existing backend tag length/count rules remain authoritative; this task does not change them. Long chip labels are ellipsized inside the available width, with their full content in the tooltip. Ordinary screen text stays navy; red is reserved for actual required/error information here.

If Next scrolls away, check that `_navigation` is the sibling of the Expanded scroll view rather than inside its Column of fields. If error text is navy, inspect both the scoped ColorScheme error and `_decoration` before overriding individual labels. If a word disappears, inspect commit and the canonical tag controller; do not send the unfinished entry controller directly to the API.

Safe exercise: run the tag test, change its test-only fresh tag to handmade and update its expected `local, handmade` payload. Verify Enter/comma, X removal and Next without Enter, then restore the fixture. Run the footer/keyboard test and confirm the same button stays at the bottom of the available content area while the fields scroll. Use mocks only; do not submit demonstration listings.

## Current Add Product: Next button label - November 3, 2026

1. **Reason:** The user requested Next instead of Continue.
2. **Files:** `campushub/lib/module_app/screens/seller_add_product_page.dart:605`, `_navigation` button Text; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Change:** Steps 1-3 now display Next. Step 4 still displays Submit for Approval.
4. **How it works:** The existing `_step == 3` condition selects the displayed label. `_continue` still validates the active fields and advances the retained draft; function names and widget keys remain unchanged.
5. **Backend/API:** Unchanged.
6. **Database/migrations:** None.
7. **Verification:** Single-file Flutter analysis passed with No issues found. No new tests or device run for this text-only change.
8. **Limits / safe practice:** Use the running app's normal reload, check Next on Steps 1-3 and Submit for Approval on Step 4 without submitting a real product. If Continue persists, confirm the app loaded the changed Text at line 605. Earlier guide references to Continue describe the same navigation action.

## Current Add Product: gold-to-navy step progress - November 3, 2026

1. **Cause / reason:** The user requested gold `#FCB316` for Steps 1-2 and a gradient into navy for Steps 3-4. This explicit request is scoped to the progress line.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:409`, `_progress`; `campushub/test/seller_add_product_page_test.dart:309`, `product-step-gradient` assertion; this guide and `CAMPUSHUB_CONTEXT.md` record the new progress styling.
3. **Changes made:** The thin rounded line stays gold through its first half, blends gold to the existing navy `#0B1F3A` between half and three-quarters, and remains navy through its final quarter. The remaining track stays light gray. Step text, unboxed sections and spacing remain.
4. **How it works:** The existing LinearProgressIndicator still receives `(_step + 1) / 4`. A ShaderMask maps a full-width LinearGradient with stops `[0, .5, .75, 1]` onto only the filled line. Its white indicator is an alpha mask, not a visible white bar; transparent remaining progress reveals the separate gray ColoredBox beneath it. Keeping the shader anchored to the whole track prevents Step 1 from showing navy prematurely. Example: Step 2 fills half the track in gold; Step 4 reveals the entire gold-to-navy line.
5. **Backend / API behavior:** Unchanged. No validation, navigation, authentication, approval, payload, photo or FIFO changes.
6. **Database / migration impact:** None. No models, migrations, dependencies, assets, working records or deployment changes.
7. **Tests performed:** **18/18 Add Product Flutter tests passed in 15 seconds**; two-file analysis reported **No issues found**. Existing progress-value/position/responsive checks remain and the paint assertion now checks the mask. Actual Step 2 and Step 4 renders were inspected; captures are in `scratch/add-product-progress-gradient-20261103/renders/`.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device or hosted-server verification was performed. Safe exercise: run `flutter test --no-pub test/seller_add_product_page_test.dart` from `campushub/`, navigate through all four steps and back, and confirm the same line changes from quarter/half gold to the navy-ending full gradient without losing entered values. If the whole remaining track changes color, check the transparent indicator background and separate gray track before changing step calculations.

## Current Add Product: remove the section card wrapper - November 3, 2026

This overrides the earlier instruction to retain an active section card. All four steps now use an unboxed heading and fields directly on the screen background.

1. **Cause / reason:** The user explicitly requested removal of the remaining container wrap. `_section` still supplied a bordered rounded white card with another 16px inset inside the screen's existing padding.
2. **Exact files changed:** `campushub/lib/module_app/screens/seller_add_product_page.dart:653`, anchor `_section`; `campushub/test/seller_add_product_page_test.dart:150`, anchor `tapKey`; this guide and `CAMPUSHUB_CONTEXT.md` record the current layout. No other application source changes.
3. **Changes made:** `_section` now uses an undecorated full-width SizedBox and Column. Removed its border, rounded decoration, background and inner padding. Retained the heading, 16px title/content and section spacing, existing 16px screen padding, gold progress and four-step controls.
4. **How it works:** `_section(title, children)` receives the same active-step title and field widgets and returns only layout. Data still flows through the same retained controllers, validation and Review step to the existing submission service. Test `tapKey` now targets the actual inventory radio instead of the whole card's center, which moved onto the information icon when the fields became wider. Example: the Product Name field now starts at the screen's 16px inset instead of the former 32px combined inset.
5. **Backend / API behavior:** Unchanged. No authentication, navigation flow, product approval, request payload, image handling or FIFO calculation changes.
6. **Database / migration impact:** None. No schema, migrations, dependencies, assets, working data, device actions or deployment changes.
7. **Tests performed:** **32/32 existing Flutter tests passed in 16 seconds** across the Add Product, seller receiving and seller application suites; two-file analysis reported **No issues found**. Formatting reported two files/zero changes. Actual unboxed widget captures are saved under `scratch/add-product-unboxed-20261103/renders/`; the 390dp Product Information render was visually inspected. The initial run exposed three test-only inventory card-center taps hitting the information icon; the helper now selects the native radio directly.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-device or hosted API test is needed to establish removal of a local decorative widget, and none is claimed. Inputs, inventory choice/batch rows and image tiles retain their own functional borders. Safe exercise: run `flutter test --no-pub test/seller_add_product_page_test.dart` from `campushub/`, compare all four steps and confirm fields align at the same 16px inset as progress/navigation. Check Back/Continue retention without submitting a working product. If the old outer border persists, verify the running app loaded the changed `_section` before altering shared input borders.

## Current Add Product: four retained form steps - November 3, 2026

This entry supersedes the continuous-form layout and separate Preview Product dialog described below. It changes the existing Flutter Add Product route, not another screen. The established Simple Stock/Batch Inventory API contract, actual FIFO backend allocation, image picker and approval workflow remain.

### 1. Cause / reason

The user's new brief requests one section at a time, a thin progress line on the left with Step X of 4 on the right, Back/Continue navigation and a final inline review. Confirmed in the prior screen: all section cards appeared together and Preview Product opened a separate dialog. The parent layout already used undecorated layout widgets; it now contains only the progress row, one active section card and navigation, without another visible wrapping card.

### 2. Exact files changed, current lines and code anchors

| File relative to the project root | Current line / anchor | Change and reason |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | 16 `SellerAddProductPage`; 31 `_scroll`; 32 `_step`; 65 disposal | Retains the existing screen/controllers and adds a scroll controller plus a zero-based active step. Both the scroll controller and existing draft controllers are disposed with the route. |
| Same screen | 312 `_validInventoryTotal`; 324 `_changeStep`; 338 `_back`; 347 `_continue`; 355 `_submit` | Validates the active step before advancing, preserves drafts, resets focus/scroll when changing steps and permits submission only from Review. Existing submission arguments and error/success handling remain. |
| Same screen | 409 `_progress`; 438 `_reviewValue`; 450 `_review`; 550 `_navigation` | Adds the left-line/right-label progress row, real entered-data summary and responsive Back/Continue/Submit controls. Removes the former separate preview dialog and its action. |
| Same screen | 653 `_section`; 880 `PopScope`; 917 scroll view; 927/1026/1190/1191 active section branches | Keeps one active bordered section card, 16px screen/major spacing, header and platform Back behavior, and a single scrollable content layout. Inactive section widgets are not displayed. |
| `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart` | 56 `ProductInventoryInfo.explanation` | Replaces only the tooltip wording with the exact shorter explanation in the new brief. Tap/long-press/hover, bounded scrolling and independent semantics remain. |
| `campushub/test/seller_add_product_page_test.dart` | 277 responsive step cases; 358 validation; 413 keyboard/header/platform Back; 447 retained batches; 645 photo review; 748 submission guards | Replaces the obsolete all-sections-visible/preview-dialog expectations with the four-step journeys while retaining gallery, validation, permissions, submission and error coverage. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md` | This entry / newest four-step entry | Records current behavior, source anchors, functions/data flow, verification, troubleshooting and a safe test exercise. |

Five project files changed: two runtime Dart files, one existing test file and two existing documents. Snapshots, protected hashes, logs and actual widget captures are under `scratch/add-product-steps-20261103/`.

### 3. Changes made

1. Product Information: Product Name, Category, Description and optional Tags.
2. Pricing & Inventory: Selling Price, stock selector, Simple quantity or retained batch rows, Low Stock Threshold and the existing optional perishable expiry field.
3. Product Images: existing gallery control, up to six previews, primary selection and removal in the existing compact responsive grid.
4. Review & Submit: actual name/category/description/tags, formatted selling price, stock method, total quantity, batch details where applicable, threshold, optional expiry and all selected images in primary-first order. The notice explains Marketplace Admin approval; Submit for Approval uses the existing service.

The progress bar shows 1/4, 2/4, 3/4 and full progress, using gold `#FCB316` against the existing light border color. Step text stays to its right, with no percentage text or outer progress container. Navy `#0B1F3A`, white, Poppins, existing inputs, thin borders and minimal shadows remain. Only the current section card is built. Header/progress/navigation have no new decorative wrappers.

Continue appears only on Steps 1-3; Back appears on Steps 2-4. Header Back and platform Back move to the previous step when applicable, preserving the draft. Back from Step 1 returns through the existing route. Buttons/focus/navigation are blocked while picking/submitting. Narrow or enlarged-text navigation stacks without compressing touch targets. No new animation is added.

### 4. How it works: functions, inputs, outputs and data flow

`_step` stores 0-3. `_progress()` derives both the LinearProgressIndicator value `(_step + 1) / 4` and the visible/semantic Step X of 4 text from that one value, preventing disagreement between line and label.

`_continue()` validates the currently mounted Form fields. Step 1 therefore cannot advance with a missing name/category/description. Step 2 uses the existing positive-price, integer quantity, nonnegative threshold, batch/date/cost validators and `_validInventoryTotal()`; empty batches and overflowing totals remain blocked. Step 3 keeps images optional, as in the existing backend/form contract. Image selection is still validated before it enters the draft, and there is no POST during Continue.

`_changeStep(next)` dismisses focus and tooltips, changes the active index, clears the current error-display flag and resets scroll to the top after layout. It does not clear any text controller, selected category/date, image slot or batch draft. Returning to a step mounts its fields from those same retained objects. The current Form registers only visible fields; invalid hidden inventory methods do not block the selected method. Required prior steps must be passed again after navigating backward to edit them.

`_back()` chooses the preceding step or the existing Navigator exit. `PopScope` intercepts platform Back within Steps 2-4 and blocks it while busy. Successful submission still returns true through the original route; tests verify the form closes only after confirmed success.

`_reviewValue(label, value)` renders labelled text. `_review()` reads the existing controllers and `_orderedImages`; it never creates product records or recalculates backend allocations. Images use the same ProductImage renderer and primary-first ordering. Actual batch dates/costs, tags and expiry remain inspectable before submission. No photo selection produces an honest No product photos selected message.

`_navigation(categoriesAvailable)` chooses Continue or Submit based on the step, with Back where appropriate. Existing loading state disables duplicate submissions and Back actions. A failed/malformed/unsupported-server result leaves Review and the original draft intact. The seller can navigate back to edit it.

```text
Existing authenticated Add Product route -> retained form controllers
  -> Step 1 validate information -> Step 2 validate inventory
  -> Step 3 existing image picker -> Step 4 read the retained draft
  -> existing ProductService.submitProduct -> existing Django listing/approval flow
Back changes the active step only; no HTTP write occurs before Submit.
```

Annotated test-only example: enter quantity 9 in Simple Stock, switch to Batch Inventory and enter batches of 3 and 4. Review displays Batch Inventory and 7 units. Back through Images to Inventory keeps both batch dates/costs; switching to Simple Stock restores quantity 9. Changing steps never copies 7 into the Simple quantity or creates a stock movement. Django remains responsible for FIFO allocation after the listing is approved and purchased.

### 5. Backend / API behavior

Unchanged in this task. `ProductService.submitProduct` receives the same arguments as before, including primary-first images and optional initial batches/cost/expiry. Six protected source hashes match: `products_screen.dart`, `product_service.dart`, `seller_application_service.dart`, the Django product submission view, initial-batch service and FIFO service. Source comparisons also confirm the image MIME/read/picker logic, slot/gallery implementation and ProductService argument block are unchanged.

The same bearer-token authentication, approved-seller access checks, pending-product approval, capability preflight for older batch servers, saved-batch confirmation, timeout handling and no automatic POST retry remain. No endpoints or database contracts were added. Step controls do not simulate or change FIFO stock deduction.

### 6. Database / migration impact

None. No backend files, models, schemas, migrations, dependencies, assets or working product records were changed. No app/emulator launch, installation, server restart or deployment was performed. All entered example names/images/amounts in verification are isolated widget fixtures, not hardcoded application data.

### 7. Tests performed

- **32/32 Flutter tests passed** in 14 seconds across `seller_add_product_page_test.dart`, `seller_stock_receiving_test.dart` and `seller_application_test.dart`. Tests cover one active section, exact progress values and horizontal alignment, all required validation, no early HTTP writes, retained values/methods/batches/dates/costs, review, all six images/primary order/removal, invalid/excess/cancelled gallery selection, keyboard scrolling, header/platform Back, guarded submission, existing auth/payload, retryable errors, malformed success, older batch servers and existing seller application/receiving flows.
- Responsive journeys passed at 280x844/200% text, 320x844/130%, 390x844, 640x900 and 844x390 landscape. The real bundled-font captures for all four 390dp steps were inspected: progress above one card, no visible outer wrapper, preserved navy/white/gold, readable review and navigation outside the card. Additional batch, six-photo, tooltip, keyboard and responsive captures are saved in the evidence folder.
- Three-file Flutter analysis reported **No issues found**. Final formatting reported three files/zero changes. The first analysis identified a non-const Semantics constructor and test/style brace warnings; these were corrected. The final test-only brace cleanup does not alter the passing test behavior.
- Six protected integration/backend hashes match; the submission argument block and unchanged image-helper/gallery source comparisons passed. Backend tests were not rerun for this Flutter-only presentation change. No native TalkBack or physical gallery session was performed, and no full accessibility compliance score is claimed. The web-only design-kit gate is not a Flutter renderer; its previously documented unavailable dependencies are not represented as a native pass.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/seller_add_product_page_test.dart test/seller_stock_receiving_test.dart test/seller_application_test.dart
flutter analyze --no-pub lib/module_app/screens/seller_add_product_page.dart lib/module_app/widgets/seller/product_inventory_fields.dart test/seller_add_product_page_test.dart
```

Set PRODUCT_FORM_REVIEW_DIR to `scratch/add-product-steps-20261103/renders` using an absolute path before the test command to regenerate captures. Logs are `flutter-tests.log` and `analyze.log`; `protected.json` records the six unchanged integration sources.

### 8. Remaining limitations, troubleshooting and safe practice

Drafts are preserved while moving between steps and after definite submission errors, but are not saved across closing the route or restarting the app. Photos remain optional to preserve the current contract. An uncertain network response still requires checking My Products before retrying; this task adds no new listing idempotency contract. Optional batch cost remains in the existing receipt-note workflow described below. Physical-device/TalkBack and hosted-server verification remain outside this local change.

If a field seems reset, inspect the controller or retained batch object rather than adding duplicate per-step models. If Continue does not advance, inspect inline errors in the active section and the batch total error; it should not validate inactive sections. If the last step crashes after another code change, first verify earlier-step validation was not bypassed. If the gallery changes, compare the protected image-helper/gallery slices and the six-photo regression before altering backend storage. Use your normal hot reload/restart workflow to show the update; this task did not control your running app.

Safe exercise: in the test named `batch drafts, dates, costs and method switches...`, change the test-only second quantity from 4 to 6, update its expected total/payload from 7 to 9, and run that test. Navigate backward and confirm Simple Stock still retains its separate 9 while both batch dates/costs remain. Restore the fixture afterward. Then run the 280dp/200% four-step case and inspect the captures; only the current section should appear, while navigation remains reachable by scrolling. Do not submit demonstration products or receive working stock for this exercise.

## Add Product: Simple Stock and Batch Inventory - November 3, 2026

This entry is the current Add Product specification. It supersedes the older dropdown/one-quantity inventory presentation below. The existing route, Product Information, Pricing & Inventory, Product Images, review notice, authentication and approval workflow remain.

### 1. Cause / reason

Confirmed in the implementation: the Flutter form displayed a stock-method dropdown and one ordinary stock input for both methods. Its submission sent only `stock` and `inventory_method`; separate received dates and costs could not be saved. Product Preview and primary-photo selection were also absent. Django already had real FIFO batch allocation and a movement ledger, but ordinary receiving correctly accepts only approved listings. A new listing starts pending, so initial receipts must be saved within listing creation rather than through the later receiving endpoint.

### 2. Exact files changed, current lines and code anchors

Paths are relative to the project root. These are current anchors for this implementation; older reports below retain historical line numbers.

| File | Current line / nearby anchor | What changed |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_add_product_page.dart` | 16 `SellerAddProductPage`; 50 `_batchTotal`; 54 `_orderedImages`; 309 `_submit`; 370 `_previewProduct`; 606 `_images`; 869 `ProductInventorySelector`; 897 `ProductBatchFields`; 943 Low Stock Alert At; 1038 preview-product | Updates the existing form, retains both inventory drafts, computes the displayed total, adds preview and primary photos, and submits only the selected method. Removes the former gradient-border class and inline low-stock caution; uses a solid focus border and ordinary helper text. |
| `campushub/lib/module_app/widgets/seller/product_inventory_fields.dart` | 7 `ProductFormStyle`; 36 `ProductBatchDraft`; 53 `ProductInventoryInfo`; 144 `ProductInventorySelector`; 244 `ProductBatchFields`; 320 date FormField; 371 optional unit cost | New reusable inventory widgets, form-scoped brand values, validators and batch draft controllers. |
| `campushub/lib/module_app/services/product_service.dart` | 186 `submitProduct`; 192 `initialBatches`; 206 initial_batches; 217 saved-count confirmation | Adds an optional batch payload and checks the server acknowledged every batch. Existing callers omit it. |
| `campushub/lib/module_app/services/seller_application_service.dart` | 224 `createProduct`; 228 capability preflight | Before a batch POST, reads the same existing endpoint and verifies initial-batch support. Keeps the current bearer-token header, timeout handling and no automatic POST retry. |
| `backend/core/api/views.py` | 756 `seller_submit_product`; 774 capabilities; 793 batch validation; 806 positive price; 861 zero-stock creation; 870 initial receipts; 887 saved count | Adds optional initial batches to the existing GET/POST contract, validates before writes and saves receipts inside the existing atomic approval/ownership transaction. |
| `backend/core/modules/marketplace/services/product_initial_inventory.py` | 14 `validate_initial_batches`; 58 `save_initial_batches` | Normalizes batch input and feeds real receipt changes through existing `Product.save` inventory hooks. |
| `campushub/test/seller_add_product_page_test.dart` | 554 batch retention/submission; 643 invalid/removal cases; 707 older-server guard; 746 tooltip/responsive/semantics; 811 primary photo | Updates former label/caution assertions and adds behavior and real widget-render coverage. |
| `backend/core/api/test_mobile_seller_application.py` | 212 persisted receipts/FIFO; 240 invalid batches; 260 rollback; 276 disabled engine/legacy; 285 price/quantity bounds | Adds database/API regressions using disposable test records. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md` | This entry / newest Add Product entry | Records the accepted behavior, integration contract, verification, limits and practice exercise. |

### 3. Changes made

- Replaces the dropdown with Simple Stock and Batch Inventory radio cards and the requested plain-language descriptions. The saved internal values remain `simple` and `fifo`. The icon sits beside the Batch Inventory title and has an independent spoken label.
- Simple Stock shows Available Quantity. Batch Inventory shows separately removable rows with positive Batch Quantity, required Date Received and optional Unit Cost, plus Add Another Batch and the live Total Available Stock. Low Stock Alert At remains common to both methods. Up to 100 initial rows are supported; quantities/totals/thresholds respect PostgreSQL's 2,147,483,647 bound.
- Hiding a method retains its controllers and dates; invalid hidden fields do not block the active method. Removing a batch updates the total and preserves the other rows' identities. Removed controllers are disposed with the page after their widgets have left the tree.
- Uses the user's requested form-local navy `#0B1F3A`, gold `#FCB316`, white, bundled Poppins, subtle full borders, solid focus feedback and rounded fields. Shared colors and unrelated screens are not changed.
- Keeps the six-photo limit, actual gallery picker, image validation, previews and removal. The first selected photo starts as primary; Set primary changes the first image sent to Django. Removing the primary chooses the next remaining image. The upload control is more compact.
- Preview Product validates and opens a scrollable local review dialog without posting. Submit for Approval uses the existing pending-product flow and busy-state duplicate guard. Existing optional perishable expiry behavior remains.

### 4. How it works: functions, inputs, outputs and data flow

`ProductBatchDraft` owns quantity/cost text controllers and the selected date. `toJson()` produces `{quantity, received_date, unit_cost?}` only after validation. `ProductFormStyle.quantity(value, positive: ...)` returns an inline error string or null: Simple Stock accepts zero; individual batches require at least one. `_batchTotal` sums positive parsed drafts for the display; it does not deduct or reserve inventory.

`ProductInventorySelector(value, onChanged)` renders the two native grouped radios; its card also responds to a tap. It uses separate semantics for the information button, avoiding merging an interactive explanation into a radio label. `ProductInventoryInfo` uses Flutter Tooltip for tap, long-press, mouse hover, keyboard activation and timed dismissal. The exact requested explanation fits a bounded, scrollable area. Grouped TapRegions dismiss on outside taps while allowing scrolling inside. The WidgetSpan's outer text scale is neutral; the user's text scale is applied once to the explanation. This prevents doubled scaling and screen overflow at 200% text. Tooltip duration is 12 seconds after release/show, with the existing native hover behavior.

`ProductBatchFields(draft, number, decoration, onChanged, onRemove, enabled)` updates its draft, reports changes for the total and renders inline quantity/date/cost errors. The date picker allows recorded dates from 1900 through today; no received date is invented for an empty row.

`_orderedImages` returns the selected primary first and all remaining actual images afterward. Both `_previewProduct` and `_submit` use that order. The preview reads the entered name/category/price/description/tags/stock/threshold/optional expiry and primary image; Back to Form keeps the same draft. Preview and the existing optional expiry picker use the Form's descendant context so Flutter captures the scoped navy/white/Poppins theme rather than the surrounding application's default dialog theme.

```text
Form controllers + selected method
  -> validate active fields -> optional local preview (no HTTP write)
  -> ProductService.submitProduct
  -> batch only: same-endpoint GET capability check
  -> authenticated existing POST /api/seller/products/submit/
  -> validate_initial_batches -> normalized rows or HTTP 400
  -> existing atomic ownership/application checks -> pending zero-stock product
  -> save_initial_batches -> Product.save -> movement ledger + real FIFO batches
  -> response confirms saved batch count -> existing success navigation
Later purchase -> existing Django FIFO allocation -> oldest received stock first
```

Annotated example, documentation/test data only:

```json
{
  "inventory_method": "fifo",
  "stock": 7,
  "initial_batches": [
    {"quantity": 3, "received_date": "2026-01-03", "unit_cost": "2.50"},
    {"quantity": 4, "received_date": "2026-01-01"}
  ]
}
```

The server checks that 3 + 4 equals 7. It saves two receipt batches, even though the older date was entered second. A purchase of five units reserves four from January 1 and one from January 3 through the existing backend allocator. The optional cost is stored as `Unit cost: PHP 2.50` in that batch's receipt movement notes. There is no new numeric cost column or cost-based accounting feature.

### 5. Backend / API behavior

The URL and auth/owner/RBAC gates are unchanged. GET adds `capabilities.initial_batches: true`; POST optionally accepts `initial_batches` and returns `initial_batches_saved` when supplied. Legacy Simple Stock and aggregate FIFO callers retain their existing request shape. The Flutter batch path refuses to POST to an older server lacking the capability, preventing unknown rows from being silently ignored. A missing saved-count acknowledgment is treated as uncertain success: check My Products before another submission.

`validate_initial_batches` requires a nonempty list of 1-100 rows, positive whole quantities, real nonfuture ISO dates, valid optional nonnegative currency amounts, and a bounded total matching stock. It returns normalized timezone-aware received timestamps and notes. Explicit null batches, Simple Stock/bundle batch payloads and inconsistent totals are rejected. Selling price must now be positive in this listing endpoint; stock and low-stock threshold remain nonnegative bounded integers.

`save_initial_batches` accepts only a new empty FIFO product. Within the caller's transaction it applies each quantity with receipt metadata using `Product.save`. Existing hooks create the actual movement and `InventoryBatch` records. A failure rolls back the listing and all receipts together. Later `fifo.receive`, its approved-product requirement, order reservation/payment/completion/cancellation behavior and `fifo.ordered_batches` are unchanged. FIFO must already be configured; this change never activates it.

### 6. Database / migration impact

No models, schema, migrations, API URLs, dependencies, assets or working records were changed. Uses existing Product stock, InventoryStockMovement notes/received_at and InventoryBatch fields. Batch cost is retained as receipt notes because the current schema has no dedicated cost field. Test data exists only in disposable databases/widget fixtures. No server restart, deployment, app installation, emulator or physical-device action was performed.

### 7. Tests performed

- **71/71 Django tests passed** in 11.337 seconds across `api.test_mobile_seller_application`, `modules.marketplace.test_hybrid_inventory` and `modules.marketplace.test_fifo_inventory`. The isolated local PostgreSQL database was destroyed; system checks reported no issues. New coverage includes exact received dates/cost notes, seller ownership/pending status, invalid/empty/overflow drafts, disabled FIFO, legacy Simple Stock, rollback after receipts were written, and oldest-date backend allocation.
- **30/30 Flutter tests passed** across `seller_add_product_page_test.dart`, `seller_stock_receiving_test.dart` and `seller_application_test.dart`. They cover retained drafts/dates/cost, total/removal, hidden ordinary quantity, preview without POST, exact batch payload, old-server guard, primary-photo ordering, six-image validation, duplicate busy guard, errors/permissions and existing receiving/application behavior. Tooltip cases check tap/long-press/hover, outside/timed dismissal, scrolling and independent semantics at 280dp/200%, 320dp/130% and 640dp. Existing keyboard/scroll cases cover 360dp and 390dp.
- Five-file Dart analysis reported **No issues found**. Dart formatting ran on changed Dart files. Actual bundled-font widget captures were generated and visually inspected. Initial review exposed vertical tooltip overflow, doubled WidgetSpan text scaling, and scroll dismissal; these were corrected and behavior/bounds covered. An initial test assumed UTC dates equaled local dates; it now checks local received dates. A semantics-test handle cleanup error was also corrected.
- The optional vendor web design-kit command was attempted and returned exactly **`RESULT: 0/52 checks passed  =  0%`**. This is a failed/unavailable web-kit gate, not a Flutter accessibility result. Its output reports missing `python3`, Playwright/sample files/modules and denied receipt writes under the read-only vendor directory. No kit pass or WCAG compliance score is claimed, and no unrelated kit installation/change was made. Full output is `scratch/add-product-batches-20261102/optional-web-kit-gate.log`.

Reproduce the application checks from the project root (Flutter commands run inside `campushub/`):

```powershell
# Disposable LOCAL PostgreSQL runner; never uses production test tables.
backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py api.test_mobile_seller_application modules.marketplace.test_hybrid_inventory modules.marketplace.test_fifo_inventory
# In campushub/:
flutter test --no-pub test/seller_add_product_page_test.dart test/seller_stock_receiving_test.dart test/seller_application_test.dart
flutter analyze --no-pub lib/module_app/screens/seller_add_product_page.dart lib/module_app/widgets/seller/product_inventory_fields.dart lib/module_app/services/product_service.dart lib/module_app/services/seller_application_service.dart test/seller_add_product_page_test.dart
```

Flutter logs/captures are in `scratch/add-product-batches-20261102/`. The reused backend runner explicitly selects localhost:5432, creates a uniquely named disposable test database, bootstraps the project's unmanaged test schema and destroys that database afterward. Do not replace it with a working-data receiving/initialization call to test this UI.

### 8. Remaining limitations, troubleshooting and safe practice

- Source changes are local. A backend with initial-batch capability is required before using Batch Inventory submission; this task did not deploy it or change FIFO configuration. Older-server blocking is intentional and leaves the form intact.
- No physical-device gallery/TalkBack session, live authenticated listing, browser build or complete WCAG audit was performed. The form preserves entered data while switching methods and after definite server errors; drafts are not persisted across closing the route or app restart. Submission timeouts still require checking My Products before retrying; no new listing idempotency scheme was added.
- Unit cost is a receipt note, not a structured cost/report field. Initial receipts use date precision in the Django timezone; same-date batches retain stable recording order. Separate future costing/report functionality would need its own explicit design and contract.
- If batch totals disagree, inspect each quantity and the posted `stock`; never fix it by directly editing batch balances. If dates appear a day earlier in raw SQL, compare timezone-local dates rather than UTC midnight. If the tooltip vanishes while reading, inspect the grouped TapRegions and timer before adding another popup implementation. The optional web-kit failure remains outside this native Flutter change.

Safe exercise: in the existing Flutter test named `batch drafts survive method switches...`, change the test-only second quantity from 4 to 6 and update its expected total/payload from 7 to 9. Run that test, switch methods and confirm the simple draft remains 9 while the batch draft keeps its own quantities/dates. Restore the fixture and rerun. Then run the tooltip test at 280dp/200% and scroll its explanation; verify it remains visible inside the screen and dismisses on an outside tap. Use test fixtures only; do not submit demonstration products or receive real stock for practice.

## Recent Orders compact pagination dot spacing - November 2, 2026

Keep pagination inside the bordered card below View Details. The latest screenshot clarifies that the remaining concern is the horizontal space between dots.

1. **Cause / reason:** Every dot occupied a48dp-wide native button, so adjacent centers were48dp apart even though the circles were only7/9dp wide. Earlier vertical spacing changes did not reduce this horizontal gap.
2. **Exact files changed:** `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart:358` (dot cell width), `:364`/`:365` (explicit native minimum/fixed size); `campushub/test/seller_home_layout_test.dart:610` (target size), `:611` (adjacent-center measurement). This guide at line3, `CAMPUSHUB_CONTEXT.md:3`, and `campushub/DESIGN.md` at Current accepted scope record the current choice. Five project files, one runtime Dart file.
3. **Changes made:** Reduce each dot cell from48dp to24dp wide and set the native button minimum/fixed size to24x44dp so Material defaults do not widen it. Keep the44dp row height, centered group,7/9dp circles, inside-card placement, colors, zero padding and all existing actions.

| Before | After | Why |
| --- | --- | --- |
| 48dp-wide cells;48dp between dot centers | 24dp-wide cells;24dp between centers | Groups the indicators closer together without changing the order content or vertical layout. |

4. **How it works / functions and data flow:** Existing authenticated workspace JSON still supplies the newest seller-owned order maps to SellerRecentOrders. The same footer for-loop renders one IconButton for each of the capped five rows. Its narrower SizedBox and explicit minimum/fixed size determine the24dp center spacing; Row keeps the whole group centered. Tapping still calls the same PageController.jumpToPage, swiping updates the same selected index, and refreshed-order selection is unchanged. No new function or data field was introduced. Example using isolated fixtures only: five orders now produce a120dp-wide group rather than240dp; zero/one order still has no dots. The prior compact vertical layout stays44dp tall with no extra bottom inset when dots exist, and8dp bottom padding for a single order without them.
5. **Backend / API behavior:** Unchanged. No requests, serializers, calculations, sorting, ownership, buyer information, order/payment statuses, permissions, inventory, fulfillment, See All or View Details changes. Nine protected hashes match. Reversing only the three pagination width/style edits reproduces the complete previous runtime source exactly.
6. **Database / migration impact:** None. No models, schema, migration, dependency, asset, working record, session, installation or deployment changes.
7. **Tests performed:** 65/65 Flutter tests passed (15s) across seller Home layout/workspace/entry suites. The existing carousel test measures24x44dp controls and24dp between adjacent centers; it retains inside-card containment, balanced vertical spacing, swipe, keyboard activation, exact details and return state. Zero/one/five records, refreshed selection, long names/IDs,280/320dp at2x text,414dp,600dp/1.3x and844x390 landscape, seller permissions and See All remain covered. Two-file static analysis reported No issues found; formatting reported2 files/0 changes. The actual bundled-font render was inspected and shows a compact centered group. Evidence: `scratch/seller-recent-orders-dot-gap-20261102/` contains flutter-tests.log, analyze.log, scope.log, protected.json, .dart.bak snapshots and renders. UI/UX Pro Max and Emil Design Engineering guidance was applied within the user's requested spacing scope; no optional web-kit score or complete accessibility audit is claimed.
8. **Remaining limitations / troubleshooting / safe practice:** Individual dot bounds are now24x44dp, narrower than before to honor the requested compact grouping; horizontal swipe remains available. Physical Android/TalkBack, live-account actions and backend tests were not run. Use your own Hot Reload. Missing dots with fewer than two orders are intentional. Safe exercise: from campushub/, run `flutter test --no-pub test/seller_home_layout_test.dart`; inspect the adjacent-center assertion, compare two/five-order fixtures, tap a dot, swipe, activate a dot with the keyboard and return from View Details. Verify selected order/data stay unchanged. Do not edit real orders or stock for this check.

## Recent Orders reference label and top pagination - November 2, 2026

This follow-up supersedes the older below-card dot placement. The user confirmed that pagination dots should move above the order card. Keep the existing buyer-first summary and all other Home sections.

1. **Cause / reason:** The card displayed the recorded order code without the requested `Order #` label, and its existing indicator row followed the PageView. This is a presentation request; no order-data or permission defect was identified.
2. **Exact files changed:** `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart:166` (`_height` reference measurement), `:225` (moved existing indicator row), `:261` (unchanged PageView), `:301` (displayed reference); `campushub/test/seller_home_layout_test.dart:170` (reference assertions), `:543` (swipe/top-dot/detail integration), `:740` (long reference), `:886` (all-status preview), `:1059` (capture the complete carousel). This guide at line3, `CAMPUSHUB_CONTEXT.md:3`, and `campushub/DESIGN.md` at `Current accepted scope` record the current choice. Five project files changed; only one runtime Dart file changed.
3. **Changes made:** Prefix the actual recorded code with `Order #` beneath the buyer's full name. Move the exact existing centered dot row above the cards, outside their border. Keep its gold selected state, 48dp targets, accessible labels, keyboard controls and zero/one-order visibility rule. All card fields, styles, compact status badges and actions remain.
4. **How it works / functions and data flow:** Django's existing owner-scoped workspace JSON provides each `row['code']`. `SellerRecentOrders.build` renders `Order #` followed by that unchanged code. `_height(context, width, row)` measures the same prefixed string with the original 11sp style and single-line ellipsis, keeping the buyer/status header safe at narrow widths. The outer Column now lays out indicators, then the same measured PageView. Its PageController, `onPageChanged`, `didUpdateWidget` selected-order preservation and exact-row View Details callback are unchanged. Illustrative fixture only: recorded code `2026ABC123` displays as `Order #2026ABC123`; the underlying code and detail map remain unchanged.
5. **Backend / API behavior:** No endpoint, serializer, sorting, reporting-period rule, buyer resolution, seller ownership, role permission, payment or fulfillment workflow changed. The existing newest-five owner list, See All -> Orders Received and full product information inside View Details remain. Nine protected source hashes, including the workspace, client service, inventory and backend read/access helpers, match their before-values; a source comparison confirms only the prefix and indicator position changed in the runtime widget.
6. **Database / migration impact:** None. No schema, migration, dependencies, assets, working records, session state, deployment or device action changed. Render fixtures stay inside tests.
7. **Tests performed:** **65/65 Flutter tests passed** (15s) across `seller_home_layout_test.dart`, `seller_workspace_test.dart` and `seller_home_entry_test.dart`. Existing checks verify top/external dots, five-order cap, swipe and keyboard controls, exact details/return state, zero/one-order empty behavior, refreshed selection, seller access and See All. Long-data cases include280/320dp with2x text,414dp,600dp/1.3x and844x390 landscape. Two-file Dart analysis reported `No issues found!`; formatting reported2 files/0 changes. Actual bundled-font light/dark-surrounding renders were inspected. The initial run exposed one test's remaining unprefixed all-status expectations; those assertions now use the requested label, with coverage retained. Evidence: `scratch/seller-recent-orders-top-20261102/{flutter-tests.log,flutter-tests-first.log,analyze.log,scope.log,protected.json,renders/}`. UI/UX Pro Max's Flutter Column/Row guidance applied; its UX searches did not return a verified carousel-placement rule, so placement follows the user's confirmed choice. The optional web token-kit gate is absent; no score from it is claimed.
8. **Remaining limitations / troubleshooting / safe practice:** No physical Android/TalkBack or live-account check, backend-test rerun, installation or deployment was performed. Use your own Flutter Hot Reload to show the update. If dots are missing, first confirm there are at least two actual orders. Keep recorded codes intact, including any existing prefix they contain; this change adds only the visible label. Safe exercise: run `flutter test --no-pub test/seller_home_layout_test.dart` from `campushub/`; compare the zero/one/five-order fixtures, use a top dot and swipe back, then open View Details and return. Confirm the selected order and full detail information remain while long IDs ellipsize rather than overflow. Do not create or edit real orders for this exercise.

## Recent Orders summary without product previews - November 2, 2026

This entry supersedes the product-preview portion of the preceding refinement. Recent Orders now shows buyer full name/status, secondary Order ID, Order Total, date/payment and View Details. Product names, photos, quantities and extra-item text appear only through the carousel's detail action. Inventory Alerts and other dashboard sections retain their current implementation.

### 1. Cause / reason

The user requested a compact monitoring summary after the preceding implementation added product information to each carousel card. Confirmed in the source: that product block also contributed image/text height to every page. The existing detail view showed product names and quantities but omitted variants/photos; a carousel-scoped detail option now keeps the requested product information behind View Details without changing other order-screen callers.

### 2. Exact files changed, current lines and nearby anchors

| File, relative to the project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart` | 61 `buyer`; 117 `_height`; 283 Order Total Wrap | Keep full-name preference, remove all product-preview helpers/widgets/image import and their height contribution, add a labelled prominent total, and right-align payment text. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 1208 `_orderDetailItem`; 1261 default `fullProductDetails = false`; 1694 carousel opt-in | Preserve item names/quantities/subtotals and optionally show recorded variants/photos only for the carousel detail action. Other callers retain their existing presentation. |
| `campushub/test/seller_home_layout_test.dart` | 138 summary absence/data preservation; 196 legacy data; 230 product-detail integration | Verify no product/image/quantity in the cards, original detail map, compact size, buyer/ID order, and product name/quantity/variant/image inside View Details and after returning. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md` | Latest summary entry / Current accepted scope | Record the current summary/detail boundary, functions/data flow, checks, limitations and safe exercise. |

Six project files: two runtime Dart files, one test file and three existing documents. Before-snapshots and evidence are in ignored `scratch/seller-recent-orders-summary-20261102/`. Older reports below retain historical line numbers.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Buyer/status, ID, product tile, total and footer | Buyer/status, ID, labelled total and footer | Removes product repetition and shortens the card. |
| Image/product/quantity/additional count in the carousel | Recorded product information behind View Details | Keeps Home focused on order monitoring. |
| Product-aware height calculation | Header/total/metadata/button height calculation | Removes the product block's reserved space rather than leaving a blank gap. |

The existing white surface, thin border, Montserrat, navy #1A1851, gold #FCB316 indicators and compact semantic status pills remain. Buyer names keep their two-line limit; the ID stays smaller/muted beneath the name. Order Total uses a 22sp/700 navy value. A Wrap places label/value on one line when space permits and stacks them at larger text sizes; the card measures the same behavior. Date and right-aligned Payment stay below, with the existing 48dp-minimum View Details button at the bottom. No screenshot example name, amount or status was copied into runtime data.

### 4. How it works / functions, inputs, outputs and data flow

`SellerRecentOrders.buyer(row)` still prefers buyer_full_name from the authenticated workspace, with its existing recorded-name/missing-name fallback. `_rows` still caps the server's newest-first list at five, and PageController/refresh selection/dots are unchanged. Removing `_product`, `_productSummary` and related text/image helpers changes presentation only; the original order map still contains items, variants, quantities, totals and thumbnail metadata.

`_height` no longer measures a product tile. Its text helper also measures label/value widths so its total-row height matches the native Wrap at the current width/font scale. It still chooses the tallest of the existing pages to avoid a page-height jump. View Details sends the original map to its existing callback without deleting or rewriting fields.

The carousel callback alone passes `fullProductDetails: true` to `_showOrderDetails`. `_orderDetailItem` uses the recorded item name/quantity/subtotal, adds the recorded variant, and displays a saved image URL when available. Image precedence is a nonempty item thumbnail/image, then the first item's existing product_preview thumbnail. It does not look up a new product or assign one item's image to unrelated items. The option defaults false; the Orders Received list and its existing calls retain their prior behavior. Status/payment/fulfillment actions are untouched.

```text
Same owner-scoped Django JSON -> original order map
  -> summary: buyer/status -> ID -> total -> date/payment -> View Details
  -> carousel View Details: original items + recorded variant/photo
  -> same workflows and server permissions
```

Annotated example, isolated fixtures only: a row includes a full buyer name, product_preview with a photo URL and items with quantity3/variant Large / Blue. The summary displays no product fields. Tapping View Details shows the saved full product name, quantity, variant and image argument; returning Home leaves those product fields out of the summary again. No order mutation or additional backend request is needed for this presentation.

### 5. Backend / API behavior

Unchanged. No request, endpoint, response, buyer resolution, product serialization, newest-first sorting, owner filtering, status rule, payment/fulfillment logic or role permission changed. Existing backend product fields remain available for details and compatibility. Fourteen protected hashes match, including the inventory widget, backend adapter/helpers/inventory/order access/fulfillment, client service, image component, header and navigation. Scope comparisons verify other Home sections are unchanged and only the carousel opts into the additional detail presentation.

### 6. Database / migration impact

None. No models, schema, migrations, dependencies, asset files, session/preferences, working records or deployment changed. UI captures use isolated fixtures only; no fake application data or replacement product image was created.

### 7. Tests performed

- **65/65 Flutter tests passed** (17s) across seller Home layout/workspace/entry suites. New/updated assertions verify product/image/quantity/extra-item absence, full-name preference, secondary ID placement, original-map callback, compact card height below260dp in the normal test, and product name/quantity/variant/image inside the actual carousel detail route.
- Existing tests retain latest-five/page cap, no auto-rotation, swipe/keyboard/indicator behavior, external dots hidden for zero/one, selection retention, status colors/alignment, all See All destinations, seller permissions, Home refresh/state and unrelated-section behavior. Narrow/long-data/large-text cases include280/320dp at2x,414dp,600dp/1.3x and844x390 landscape.
- Static analysis of the three changed Dart source/test files reported **no issues** (4.8s). Formatting completed. The actual bundled-font order-summary render was inspected in light/dark surroundings: no product tile, prominent total and external dots; existing white surfaces remain. No missed-tap warnings were suppressed.
- Backend tests were not rerun for this Flutter-only change; protected backend sources are unchanged. Evidence: `flutter-tests.log`, `analyze.log`, `protected.json`, `verify_scope.cjs`, `renders/orders-light.png` and `orders-dark.png` under `scratch/seller-recent-orders-summary-20261102/`.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/seller_home_layout_test.dart test/seller_workspace_test.dart test/seller_home_entry_test.dart
flutter analyze --no-pub lib/module_app/widgets/seller/seller_recent_orders.dart lib/module_app/screens/seller_workspace_content.dart test/seller_home_layout_test.dart
```

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device/TalkBack session, live-image-host check, app install/restart or deployment was performed. Buyer-name availability and historical seller restrictions retain their prior limits. Details display images only when the existing record supplies a URL; missing images/variants are not invented. Existing older endpoints can still omit optional photo metadata.

If a blank product-sized gap remains, check both the removed widget include and `_height` before changing padding elsewhere. If a product still appears in a summary, inspect SellerRecentOrders rather than deleting API item data. If the detail photo is missing, inspect the recorded item/preview URL and existing ProductImage resolver; do not reuse another item's image. Use your own Hot Reload to show the current layout.

Safe exercise: put long product names, quantities, variants and a photo URL only in a disposable test row, run the Flutter command and confirm none appear in the card. Tap View Details and verify the original item information, then return to the carousel and swipe. Compare Inventory Alerts to confirm its source/layout remains unchanged; do not modify working orders to test a layout.

## Inventory Alerts and purchased-order previews - November 2, 2026

This entry supersedes the earlier Inventory Attention layout and ID-first Recent Orders header. Only these two seller Home sections change. Sales KPIs, bundles, header, drawer, bottom navigation, Inventory Management, order processing and stock calculations retain their current implementations.

### 1. Cause / reason

Confirmed in the existing source: Home gave On Hand, Reserved and Available equal emphasis, placed the stock badge below the metrics, and included expired-only records. The user requested Available Stock as the primary metric with the product-specific threshold beside it and alerts limited to low/out of stock. Recent Orders showed the saved buyer_name and no product image/quantity; older buyer snapshots can contain a short name or username. The existing order model records the buyer ID/email/name and purchased product/image/quantity; canonical item snapshots are available through order_items. These sources can supply the requested presentation without modifying checkout or stock logic.

### 2. Exact files changed, current lines and nearby anchors

| File, relative to the project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/seller/seller_inventory_alert.dart` | 7 `SellerInventoryAlert` | New presentation-only compact alert: product/SKU left, content-sized badge right, Available Stock/Restock Threshold pair, neutral On Hand/Reserved row. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 1111 Home status filter; 1205 `_inventoryAttention`; 1656 identity header flag; 1734 `sectionHeader` | Limit Home to canonical low/out statuses, delegate the alert UI, keep its three-record cap and Inventory navigation, and use Montserrat only for this section's header. Full Inventory Management remains unchanged. |
| `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart` | 62 `buyer`; 69 `_product`; 118 `_productSummary`; 203 `_height`; 352 buyer key | Prefer full buyer name, put the smaller ID below it, show the first purchased product/thumbnail/quantity and additional-item count, and measure the updated two-line content. Keep the compact status and existing carousel/footer actions. |
| `backend/core/modules/marketplace/services/mobile_order_previews.py` | 8 `buyer_full_names`; 30 `product_preview` | Read-only, batched buyer resolution and immutable purchased-item preview fields. |
| `backend/core/modules/marketplace/mobile_seller_views.py` | 115 bounded order lists; 123 name lookup; 129 optional preview fields | Add buyer_full_name/product_preview to existing serialized orders while retaining old fields, owner query, dates, pagination and calculations. |
| `backend/core/api/test_mobile_seller_workspace.py` | 262 snapshot/full-name test; 282 overlapping IDs; 293 item/bundle identity; 312 query growth | Verify actual account/order/item data, snapshot precedence, source disambiguation, canonical access restrictions and bounded reads. |
| `campushub/test/seller_home_layout_test.dart` | 138 purchased preview; 190 legacy data; 224 inventory values/statuses; existing responsive/navigation cases | Verify full-name preference, product image/name/quantity, original-map details callback, two-line limits, stock values/thresholds, filtering and updated layout. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md` | Latest entry / Current accepted scope | Record the current design, functions/data flow, tests, scope limits, troubleshooting and safe exercise. |

Ten project files: five runtime files, two test files and three existing documents. The new runtime files are the inventory alert widget and read-only order-preview helper. Earlier reports below retain historical line numbers. Before-snapshots and evidence are under ignored `scratch/seller-home-order-inventory-20261102/`.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Three equal stock metrics and badge below | Product/SKU + top-right pill; larger Available Stock beside threshold | Establishes the requested stock priority with a compact flat card. |
| Expired-only rows included on Home | Only server low_stock/out_of_stock rows, at most three | Matches the alert definition without recalculating any stock. |
| Short buyer snapshot above no product preview | Full-name preference, secondary ID, actual first item/image/quantity | Uses the buyer and purchased-item information requested. |
| ID/header-only height estimate | Measurement includes two-line buyer/product names and image/item text | Keeps the PageView bounded and prevents overflow at larger text sizes. |

Inventory cards use white, a thin existing border, 14dp padding and Montserrat. Available Stock is 26sp/700 navy; threshold is 16sp/600. On Hand and Reserved are 13sp secondary values in one light neutral row. Low Stock uses the existing amber status treatment; Out of Stock uses a neutral navy pill. No duplicate stock label, fake quantity, global palette change or new inventory action was added. Null values retain the existing quantity formatter's unavailable mark, including derived records without a recorded threshold. Empty nonempty-inventory text now says No low-stock or out-of-stock alerts., rather than claiming expired-only inventory is healthy.

Recent Orders keeps its existing compact status colors/pill at top-right. The full buyer name is 14sp/600 with at most two lines; the ID is smaller muted 11sp below it. The first purchased product has a 56dp thumbnail, 13sp/600 name (at most two lines), recorded quantity and +N more item(s) when supplied. Order Total/date/payment, View Details, horizontal swiping, See All and external dots remain. Missing images use the existing ProductImage fallback; no replacement image was created.

### 4. How it works / functions, inputs, outputs and data flow

Inventory: the unchanged authenticated workspace supplies canonical inventory rows. `inventory(attention: true)` filters the recorded status keys and passes each row plus the existing quantity formatter to `SellerInventoryAlert`. The widget reads product_name, sku, available, threshold, on_hand, reserved and status_label directly. It does not subtract reservations, select a threshold, recompute availability, receive stock or write to the server. The generic section header's new identity flag defaults false; only Inventory Alerts opts in, preserving other headers' existing styles.

Orders: `workspace(request)` still starts with approved_seller and the existing seller_order_queryset. It materializes the same bounded page/recent/action lists, gathers their distinct order records, and calls `buyer_full_names` once. That helper loads mobile and web candidates in two batch queries only when recorded buyer IDs exist. A saved email is compared case-insensitively; exactly one match is required. Without an email, an overlapping ID remains ambiguous when both account namespaces contain it. A uniquely resolved account supplies its actual first/last full name; otherwise the saved order name remains. A known username snapshot is not promoted to a full name. Original buyer_name is preserved in the JSON and database.

`product_preview(order, items)` reads the canonical order_items output and its saved first item. It retains the purchased name and quantity rather than replacing them with today's product name/price. Image precedence is first-item snapshot, order image snapshot, then the actual linked product's current image if no snapshot exists. It normalizes recorded image lists and reports the count of additional canonical items. Bundle ingredients remain components of one purchased bundle, not separate purchased products. No product lookup by guessed name or foreign item ID is performed.

Optional response additions are `buyer_full_name` and `product_preview` (product_name, quantity, thumbnail_url, additional_items). `_product` supports older response shapes through existing items/product fields. `buyer` uses the new field when present, including an honest missing-name result. `_productSummary` uses the existing ProductImage URL/base64/media resolver. `_height` measures the same two-line text, image block and footer at the device's actual text scale. View Details receives the original order map.

```text
Authenticated seller -> unchanged owner/permission scope
  -> unchanged inventory snapshot -> low/out Home filter -> compact stock cards
  -> bounded order lists -> batch buyer identity + purchased-item snapshots
  -> optional preview fields -> same carousel / exact-row View Details
  -> See All -> existing Inventory Management / Orders Received
```

Annotated example, disposable tests only: an order saves a username, buyer ID/email, Purchased Full Product Name, quantity3 and an order-image URL. The linked buyer's actual full name appears on Home; renaming/repricing the current product does not change the purchased name, quantity, image snapshot or total. A stock row with Available4 and threshold7 displays those exact values; the app never substitutes the global low-stock default.

### 5. Backend / API behavior

Inventory backend logic is unchanged. Order backend changes are read-only presentation enrichment in the existing workspace GET; no endpoint, request argument, status/processing transition, stock reservation, checkout, revenue rule, date filter, owner query, pagination rule or role permission changed. Full-list page one is still reused for the five-order recent preview. Batch buyer lookup stays constant with row count; item/image reads use the already selected product and recorded snapshots. Old JSON fields remain for other consumers.

The existing seller permission rule excludes ambiguous legacy multi-item order snapshots. It remains unchanged: this task does not authorize widening access or merging independently recorded orders. The preview renderer supports permitted item arrays and +N counts, while the current guard still governs which historical records reach the endpoint. Fifteen protected hashes verify canonical inventory/order/fulfillment/checkout/model/view code, header/navigation, image widget and client transport remain unchanged. Scope comparisons also verify other SellerWorkspaceContent sections/details, sales calculations, status styling and the carousel footer/pagination.

### 6. Database / migration impact

No models, schema, migrations, dependencies, assets, real accounts/orders/stock, sessions or deployment changed. The new helper performs reads only. PostgreSQL tests create/destroy a disposable local database; Flutter records/captures are isolated fixtures. No sample names, images or quantities were added to runtime application data.

### 7. Tests performed

- **29/29 Django/PostgreSQL tests passed** (2.916s) across the seller workspace and fulfillment suites. New cases verify complete linked names, case-insensitive saved-email matching, separate web/mobile accounts sharing an ID, snapshot preservation after product rename/reprice, recorded image/quantity/total, additional items versus bundle components, unchanged legacy seller restrictions, unchanged order count/stock/name on GET and constant query growth. Existing ownership, suspension, permissions, payment, reservations and period tests pass; system checks clean and temporary database destroyed.
- **64/64 Flutter tests passed** in the final seller Home layout/workspace/entry run. New cases verify full-name preference over username, two-line name limits, smaller ID beneath buyer, actual thumbnail argument, purchased quantity/additional count, exact original-map details callback, unavailable-name fallback, primary stock font/value, per-product thresholds and exclusion of expired/healthy rows. Existing five-order carousel/dots/keyboard/state, all See All destinations, header, permissions and refresh/navigation regressions pass.
- Responsive coverage retains 280/320dp at 2x text, 375/390/414dp, 600dp/1.3x and 844x390 landscape. An old landscape assertion assumed the ID Text filled the entire first row; it now verifies that the smaller secondary ID stays clear of the top-right badge. Final rerun passed without suppressing missed taps or overflow.
- Four-file static analysis reported **no issues** (5.5s); formatting completed. Actual bundled-font captures were inspected for order/product placement and Inventory Alerts in light/dark surroundings; the existing white Home surfaces remain. Shared Home captures were refreshed. This is not a full accessibility/TalkBack audit.
- Evidence: `backend-tests.log`, `flutter-tests.log`, `analyze.log`, `protected.json`, `verify_scope.cjs`, `renders/orders-light.png`, `renders/inventory-light.png` and `renders/shared/` in `scratch/seller-home-order-inventory-20261102/`.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/seller_home_layout_test.dart test/seller_workspace_test.dart test/seller_home_entry_test.dart
flutter analyze --no-pub lib/module_app/screens/seller_workspace_content.dart lib/module_app/widgets/seller/seller_recent_orders.dart lib/module_app/widgets/seller/seller_inventory_alert.dart test/seller_home_layout_test.dart
```

Backend reproduction from the repository root uses the existing local disposable runner: `backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py api.test_mobile_seller_workspace modules.marketplace.test_order_fulfillment`.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device/TalkBack session, live-account transaction, image-host availability check, app installation/restart or hosted rollout was performed. Serve the updated Django code and refresh Home to receive the added fields; older endpoints use the existing recorded-name/item fallback. A missing or ambiguous linked buyer cannot supply an invented full name. Missing photos keep the existing neutral image fallback. Two-line limits can ellipsize exceptionally long text while preserving the original record/detail action. Existing ambiguous multi-item seller restrictions remain as described above.

If stock looks unexpected, inspect the canonical row's available/threshold/reserved/status fields; do not calculate a new quantity in the widget or change inventory workflows. If a name is short, inspect buyer_full_name, the order's buyer ID/email and saved name; never select a mobile/web identity solely because their IDs match. If a photo is missing, inspect the snapshot URL and existing ProductImage resolver/server before inserting a replacement image. Use your own Hot Reload/pull-to-refresh after the backend response is updated.

Safe exercise: in disposable fixtures only, set a threshold different from5 and verify that exact number appears. Change an order's current product name after preserving a different purchased snapshot; the preview must retain the purchased name/quantity/total. Give web/mobile test buyers the same ID with different emails and confirm only the saved-email match provides a full name. Follow See All/View Details without submitting a real stock receipt or order.

## Compact Recent Orders status pill - November 2, 2026

This refinement changes only the order-reference/status row and its height measurement in the existing Recent Orders widget. The carousel, other card fields, View Details, See All, data source and backend statuses retain their current behavior.

### 1. Cause / reason

Confirmed in the source: both the reference and status Container were wrapped in Expanded. The status therefore occupied half the row even for a short Pending label. The row also aligned children at their top edges. The requested correction is a compact, right-aligned pill with semantic status colors and safe handling of long references.

### 2. Exact files changed, current lines and nearby anchors

| File, relative to the project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart` | 65 `_statusBadge`; 99 `_height`; 179 `statusMaxWidth`; 214 order header | Add the content-sized pill, scoped semantic colors and a maximum for exceptional labels; center the header row and truncate long IDs to one line. Update only header height measurement to match. |
| `campushub/test/seller_home_layout_test.dart` | 168 semantic badge cases; 489 long-reference geometry | Verify six recorded-status cases, intrinsic width/padding/radius/colors, right edge and vertical centers, plus narrow/large-text/landscape reference behavior. Capture actual widget renders. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md` | Newest badge entry / Current accepted scope | Record the requested local status-color exception, data flow, checks, limits and safe practice. |

Five project files: one runtime Dart file, one test file and three existing documents. Before-snapshots and evidence are in ignored `scratch/seller-order-badge-20261102/`. Earlier report line numbers below are historical; use the anchors above for this correction.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Status Expanded fills half the row | Non-flex pill uses its text width plus 11dp padding per side | Removes the stretched background without a fixed badge width. |
| 8dp corners and one neutral fill | Fully rounded 999dp radius, 6dp vertical padding and semantic fill/text pairs | Matches the requested small pill and distinct recorded statuses. |
| Top-aligned, potentially wrapping reference/status | Vertically centered row; reference uses one-line ellipsis | Keeps a long ID from pushing the badge out of alignment or overflowing. |
| Height assumes wrapping header text | Header measurement uses the same one-line limits | Avoids leaving blank card space after the alignment correction. |

Only the order reference retains Expanded, so it takes remaining space. A maximum badge width reserves 48dp for that reference after card insets and the existing 12dp gap. This is a loose upper bound, not a fixed width: short labels remain content-sized. Exceptionally long labels can truncate; the existing detail view still provides the full order information. No decorative status dot or new action was added.

| Recorded status | Background | Text | Computed solid-color contrast |
| --- | --- | --- | --- |
| Pending | `#FFF3D6` | `#8C5900` | 5.37:1 |
| Processing / Ready for Pickup | `#EAF0FF` | `#24428A` | 8.29:1 |
| Completed | `#EAF6EE` | `#21643C` | 6.41:1 |
| Cancelled | `#FDECEC` | `#9F2D2D` | 6.37:1 |
| Unclassified recorded value | `#F1F1F5` | `#1A1851` | 14.41:1 |

These functional badge colors implement the user's latest explicit semantic-color request locally; they do not change the project's neutral status treatment elsewhere. Status text remains present, so color is not the only indicator. Ratios were calculated from the solid sRGB pairs; this is not a full accessibility audit.

### 4. How it works / functions, inputs, outputs and data flow

`_statusBadge(row, maxWidth)` receives an existing server order map and a responsive maximum. It reads `status_key`, falling back to the recorded display status when the key is absent. A normalized copy selects colors only. The badge Text still displays the original `row['status']`; no value is translated into a different order state or written back.

The existing LayoutBuilder supplies the available width. `_statusBadge` returns a ConstrainedBox with a loose maximum, a rounded Container and one-line Text. The header Row keeps Expanded on the ID alone, followed by the existing gap and badge. CrossAxisAlignment.center aligns their vertical centers. `_height` gains optional `maxLines` text measurement, applied only to these header labels; buyer, amount, date, payment, button and other measurements are unchanged.

```text
Existing owner-scoped Django order map -> same Recent Orders carousel
  -> status_key/display label -> local color pair
  -> original status text + content-sized rounded badge
  -> same record -> existing View Details callback
```

Annotated example: `status_key: pending`, `status: Pending` produces the requested amber pill. A long order reference uses an ellipsis in the header while its original map and existing View Details handler remain intact. Ready for Pickup stays that exact recorded label; an unknown status keeps its recorded text and neutral colors.

### 5. Backend / API behavior

Unchanged. No endpoint, serializer, status definition, seller filter, permissions, payment/fulfillment logic or API request changed. Eleven protected source hashes match, including the workspace adapter, order-access and fulfillment services, client seller service, Home/header/drawer/navigation and seller content. Before/after comparison confirms the rest of the carousel/card and non-header height calculations are unchanged.

### 6. Database / migration impact

None. No models, schema, migrations, dependencies, assets, sessions, working records or deployment changed. Rendered order labels/amounts are isolated widget fixtures only.

### 7. Tests performed

- **61/61 Flutter tests passed** (19s) across seller Home layout, workspace and entry suites. Six new cases check Pending, Processing, Completed, Cancelled, Ready for Pickup and a neutral unknown recorded status. Assertions prove badge width equals rendered label width plus 22dp, padding/radius/colors are correct, and right-edge/vertical alignment holds.
- Existing long-content cases now also verify one-line ID ellipsis, the 12dp gap and aligned header centers at 280/320dp with 2x text, 414dp, 600dp/1.3x and 844x390 landscape. Existing zero/one/five orders, swipe/keyboard dots, selected-page retention, exact-row View Details, See All, permissions, navigation and Home state tests pass.
- Two-file static analysis reported **no issues** (15.4s). Actual bundled-font Pending and Processing/Home captures were inspected; six individual badge captures and light/dark-surroundings Home captures are in `renders/`. Existing white card surfaces remain. Computed source-color contrast is recorded above.
- The first test compilation caught an untyped test-fixture map; adding its String-key type fixed the harness. The final full run is clean, without missed-tap warnings. No backend tests were rerun for this Flutter-only change; backend files match their before hashes.
- Evidence: `flutter-tests.log`, `analyze.log`, `protected.json`, `verify_scope.cjs`, `renders/badge-pending.png` and `renders/orders-light.png` under `scratch/seller-order-badge-20261102/`.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/seller_home_layout_test.dart test/seller_workspace_test.dart test/seller_home_entry_test.dart
flutter analyze --no-pub lib/module_app/widgets/seller/seller_recent_orders.dart test/seller_home_layout_test.dart
```

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device/TalkBack session, working-data transaction, app installation/restart or hosted rollout was performed. Very long references/status labels can truncate under narrow/large-text constraints; the original record and existing detail view remain available. Text scaling is respected rather than disabled.

If the pill stretches again, inspect for an Expanded/tight width around the badge Container before changing backend data. Its only width constraint should be the responsive maximum. If a color looks unexpected, inspect the recorded `status_key` and fallback label; do not change the stored order state for presentation. Use your own Hot Reload to display the local edit.

Safe exercise: change only the disposable widget fixture to Pending and lengthen its order code, run the Flutter command, and confirm the badge stays compact/right-aligned while View Details still opens the same record. Restore the fixture afterward; do not edit real orders or status enums for a color test.

## Seller Home Recent Orders - November 2, 2026

This entry supersedes the earlier Orders Requiring Action preview. Only that Home section changes: show the newest five seller-owned orders across all recorded statuses, with the requested subtitle, existing carousel/actions, and concise empty state. Sales, the identity header, inventory, bundles, buyer Home and navigation retain their current implementations.

### 1. Cause / reason

Confirmed from the source: Home selected `orders_requiring_action`, which intentionally returned the oldest open orders. That is unsuitable for the user's new Recent Orders definition because it excludes completed/cancelled records and reverses the chronology. Filtering the current Orders Received page would also produce an older preview after visiting page two. The carousel already rendered every requested field and placed its indicators outside the cards; those behaviors were preserved.

### 2. Exact files changed, current lines and nearby anchors

| File, relative to the project root | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/marketplace/mobile_seller_views.py` | 114 order pagination; 126 `recent_orders`; 140 JSON response | Add a bounded newest-first preview independent of the full list's page; use primary key as a stable timestamp tie-breaker. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 1561 `homeRecentOrders`; 1569 `_recentOrdersHeader`; 1721 carousel include | Read the recent array without status filtering, add title/subtitle and right-aligned See All, and keep Orders Received/detail callbacks. |
| `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart` | 14 empty text; 26 indicator gold; 55 `style`; 123 empty title; 243 indicator condition | Apply section-local Montserrat and gold #FCB316, show the two-part empty message, and retain the five-page manual carousel and external indicators. |
| `backend/core/api/test_mobile_seller_workspace.py` | 228 `test_recent_orders_are_newest_owner_records_of_every_status_on_every_page` | Exercise every status, equal timestamps, seller isolation, old creation dates, pagination, recorded fields/payment, and unchanged order count. |
| `campushub/test/seller_home_layout_test.dart` | 167 typography; 194 carousel/details; 281 zero/one order; 397 destinations; 474 recent-source test | Check requested text/fields/styles, dots below cards, capped pages, exact-row details, empty state, completed/cancelled inclusion, server-array precedence and legacy fallback. Add landscape coverage. |
| `campushub/test/seller_workspace_test.dart` | 275 traversal; 428 section order | Update the section label while preserving existing navigation assertions. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md` | Latest Recent Orders entry / Current accepted scope | Record this refinement, data flow, checks, troubleshooting and safe exercise. |

Nine project files: three runtime files, three test files and three existing documents. Earlier reports below retain historical line numbers. Use the current anchors above when code moves. Before-snapshots/evidence are in ignored `scratch/seller-recent-orders-20261102/`.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Orders Requiring Action / oldest open records | Recent Orders / newest five records, all statuses | Matches the new historical preview definition. |
| No section subtitle | Latest orders received from buyers. | Explains the content without adding another card. |
| One-line action-queue empty text | No Recent Orders / New customer orders will appear here. | Gives the requested honest zero-order state. |
| Shared Inter styling inside the order preview | Scoped Montserrat, navy #1A1851, white and gold #FCB316 | Applies the requested typography/accent only to this section. |

See All stays at the right of the header's first row and opens the same Orders Received destination. Its width is flexible so larger text fits narrow screens. Subtitle spans the section width. Order cards retain ID/reference, buyer, recorded status, total, creation date, recorded payment and View Details. Pagination remains below the bordered cards, uses native 48dp buttons/selected semantics, and disappears for zero or one record. No timer, new animation, icon, demo order or unrelated redesign was added.

### 4. How it works / functions, inputs, outputs and data flow

`workspace(request)` still verifies `approved_seller` and obtains `seller_order_queryset(account)` from the authenticated mobile account. It orders that same queryset by descending `created_at`, then descending primary key when times match. There is no status or sales-period filter on Recent Orders. `serialize_order_row(order)` supplies the existing real order fields and canonical fulfillment/payment labels.

The response adds `recent_orders`, containing at most five serialized orders. Page one reuses `serialized_orders[:5]`, adding no separate recent-order query. Other pages read a bounded five-row slice independently; full-list pagination stays at 30. The older `orders_requiring_action` response remains compatible with older clients but is no longer used by this Home section. Recognized-sales eligibility and all sales calculations are unchanged.

`SellerWorkspaceContent.homeRecentOrders` prefers the new array, including an authoritative empty array. An older endpoint falls back to its existing newest-first `orders` page; inline Home already requests page one. `_recentOrdersHeader()` supplies the title/subtitle and existing destination callback. `SellerRecentOrders` takes at most five rows, preserves the selected record by ID on refresh, measures the tallest card with the actual font/text scale, and passes the exact selected map into the unchanged detail handler.

```text
Existing authenticated seller workspace GET
  -> approved_seller + seller_order_queryset(account)
  -> newest-first orders, all statuses -> recent_orders[0:5]
  -> homeRecentOrders -> existing SellerRecentOrders PageView
  -> View Details: exact order / See All: existing Orders Received
```

Annotated example, isolated tests only: with 31 older completed orders plus five equally dated orders spanning pending/processing/ready/cancelled/completed, Home receives those five newer records ordered by ID descending. A newer order belonging to another seller never appears. Choosing page two or a different Sales period does not replace the recent preview with older records.

### 5. Backend / API behavior

Existing workspace GET gains one optional read-only response field; no new endpoint, request argument, client service or authorization path. The timestamp tie-breaker makes both the first full-list page and preview deterministic. Canonical statuses, payment/fulfillment transitions, recognized revenue, order details, stock, role permissions, private response caching and existing action-order compatibility are unchanged. Source comparisons verify the rest of the backend adapter and all other SellerWorkspaceContent sections/detail code remain unchanged; twelve protected source hashes also match.

### 6. Database / migration impact

No models, schema, migrations, dependencies, asset binaries, working orders/accounts/stock, device installation or deployment changed. PostgreSQL tests create/destroy a disposable local database. Flutter images use existing isolated test fixtures; no sample data is sent to the application database.

### 7. Tests performed

- **25/25 Django/PostgreSQL tests passed** (5.031s), including the new recent-order regression and existing workspace/fulfillment suites. Coverage includes all five canonical statuses, seller isolation even with a foreign seller parameter, stable tied timestamps, five-record limit, period/page independence, recorded fields/payment values, zero recognized sales for the tested date period, no extra order writes, existing authorization and bounded query growth. System checks clean; temporary database destroyed.
- **55/55 Flutter tests passed** (21s) across `seller_home_layout_test`, `seller_workspace_test` and `seller_home_entry_test`. They cover cap/swipe/manual timing/keyboard indicators, exact-row View Details and return state, external-dot geometry, no dots for zero/one, both empty lines, title/subtitle/right-side See All, all seven recorded fields, completed/cancelled source selection, old-server compatibility, section ordering, existing destination/permission flows, Home refresh/state and header behavior.
- Responsive cases include long content at 280/320dp with 2x text, 414dp, 600dp/1.3x and 844x390 landscape; existing 375dp filter and Home-header cases remain. The first run caught a 28dp right overflow in the new header at 280dp/2x text. Bounding the right action with Flexible/Align corrected it; final rerun passed. No warning was suppressed.
- Four-file static analysis reported **no issues** (6.6s). Actual bundled-font order-section captures were inspected in light/dark surroundings; the section preserves its existing white surface. Both captures show title/subtitle, recorded fields and dots below the card. UI/UX Pro Max searches informed manual carousel controls, focus and native semantics; no claim of a complete accessibility audit.
- Evidence: `flutter-tests.log`, `backend-tests.log`, `analyze.log`, `protected.json`, `verify_scope.cjs` and `renders/layout/orders-light.png` / `orders-dark.png` under `scratch/seller-recent-orders-20261102/`.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/seller_home_layout_test.dart test/seller_workspace_test.dart test/seller_home_entry_test.dart
flutter analyze --no-pub lib/module_app/screens/seller_workspace_content.dart lib/module_app/widgets/seller/seller_recent_orders.dart test/seller_home_layout_test.dart test/seller_workspace_test.dart
```

Backend reproduction from the repository root: `backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py api.test_mobile_seller_workspace modules.marketplace.test_order_fulfillment`. The existing runner enforces a local disposable PostgreSQL database; do not import test fixtures into working data.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device/TalkBack session, live-account transaction or hosted rollout was performed. The page-independent preview requires the updated Django code to be served. Older servers remain compatible through the loaded-page fallback; they cannot provide a separate newest-first preview on an arbitrary later full-list page. When fewer than five real orders exist, show the actual count; never fill missing pages with placeholders.

If Home still shows only open orders, inspect `recent_orders` and `homeRecentOrders`, not the recognized-sales filter or status workflow. If the subtitle/title appears old, use your own Hot Reload after checking the source anchors. If dots look wrong, inspect the actual array length and selected page before changing data. The indicators belong to the outer carousel Column, after its PageView, not inside any order Container.

Safe exercise: change statuses only in the disposable test fixture to completed/cancelled, run the Flutter command, and verify both remain in Recent Orders. In the backend test, give the five newest owner orders equal creation times and verify stable descending IDs on pages one and two. Test See All and View Details without submitting any real order or changing real stock.

## Seller Home profile-triggered header - November 2, 2026

This header-only refinement supersedes the separate seller Home greeting in the preceding banner-removal work. Approved seller Home now starts with the existing photo beside Welcome Back, and the authenticated full name, followed directly by Sales Overview. Buyer Home, other bottom-navigation tabs and dedicated seller-tool headers keep their existing appearance and actions.

### 1. Cause / reason

Confirmed in the existing source: the shared header provided a hamburger button plus a profile shortcut, while Home repeated Welcome Back with the first name beneath it. The user requested one compact seller Home identity area that opens the existing drawer. No authentication, seller-eligibility or reporting defect was inferred.

### 2. Exact files changed, current lines and nearby anchors

Paths are relative to the project root. Earlier sections retain historical line numbers; use these current anchors for this refinement.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 303 `isSellerHome`; 310 header padding; 313 hamburger conditional; 323 identity callback; 401 `showWelcomeGreeting` | Apply the drawer-trigger identity only to approved-seller tab 0; hide that Home's duplicate greeting. Search, Notifications, SafeArea and the existing drawer remain. |
| `campushub/lib/module_app/widgets/navigation/header_profile_button.dart` | 25 `greeting`; 28 `actionLabel`; 38 `nameText`; 90 caption | Add optional caption and action purpose while keeping defaults for other callers. Use Montserrat 12sp muted caption and 14sp/600 navy name; keep the recorded photo and initials/error fallback. |
| `campushub/lib/module_app/screens/home_page.dart` | 35 `showWelcomeGreeting`; 50 member; 219 conditional | Default true preserves buyer welcome text. False removes the seller's greeting and its trailing spacer together; existing 8dp list padding places Sales Overview directly below the header. |
| `campushub/test/seller_home_entry_test.dart` | 63 font loader; 119 responsive seller-header tests; existing retained-state/navigation checks | Verify seller-only layout, safe insets, truncation, full-name semantics, actual avatar tap, drawer return, Search, Notifications and unchanged headers on other tabs. Capture actual widgets with bundled fonts. |
| `campushub/test/header_profile_button_test.dart` | 69 photo-test variants | Verify the same stored image URL and failure fallback with and without the new greeting. Existing default identity/long-name tests remain. |
| `campushub/test/seller_workspace_test.dart` | 1088 Home greeting assertion | Expect the moved header greeting when existing seller-tool navigation returns to Home. No navigation implementation changed. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md` | Latest header entry / Current accepted scope | Record the current presentation, data flow, checks and troubleshooting without changing older historical reports. |

Nine project files: three runtime Dart files, three test files and three existing documents. Before-snapshots and evidence are under ignored `scratch/seller-home-header-20261102/`.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Separate hamburger and profile shortcut on seller Home | Existing avatar/name area opens the same drawer | One large, discoverable navigation target without a duplicate icon. |
| Standalone Welcome Back with first name below the header | Small Welcome Back, caption above the real full name beside the photo | Consolidates identity and removes the redundant heading. |
| Seller greeting plus spacing before Sales Overview | Sales Overview begins 8dp below the complete header | Keeps the first operational section close without modifying KPI cards. |

The name stays on one line with an ellipsis. The caption may wrap to two lines at large text sizes instead of losing Back. Header height grows naturally; no fixed-height clipping or text-scaling override was added. Existing minimum-48dp identity and action targets remain. Header uses its existing white/navy surface and bundled Montserrat identity styles. No new gold element or global color/font change was introduced; existing accents remain in their current components.

### 4. How it works / functions, inputs, outputs and data flow

`DashboardScreen.build` calculates `isSellerHome` from the existing server-verified seller flag, current user and selected tab index. Only approved-seller Home omits the hamburger and supplies `greeting: 'Welcome Back,'`, `actionLabel: 'Open menu'` and the existing `ScaffoldState.openDrawer()` callback to HeaderProfileButton. Other tabs retain the hamburger and profile-tab shortcut; buyer/pending/revoked Home keeps its original header and content greeting.

`HeaderProfileButton.build` reads the existing AuthUser full name, falling back to recorded first/last name parts, plus `resolvedProfilePhotoUrl`. Optional greeting changes only the label layout. Optional actionLabel changes its tooltip/spoken purpose; assistive technology receives Open menu plus the full untruncated name. The existing NetworkImage, initials and photo-error handling are unchanged. Search and Notifications keep their original callbacks and right-side order.

`HomePage.showWelcomeGreeting` is a presentation input, not a permission check. The default true retains all other callers' welcome text; Dashboard passes false for approved-seller Home. Catalog loaders, refresh/state retention, seller content and the four KPI calculations are untouched.

```text
Existing signed-in AuthUser + verified seller status + selected tab
  -> DashboardScreen.build: seller + Home?
     yes -> existing photo / caption / full name -> open existing drawer
            Home hides duplicate greeting -> Sales Overview
     no  -> existing hamburger + profile shortcut header
  -> same Search route, Notifications sheet and drawer destinations
```

Annotated example: an approved student seller sees their saved full name beside the photo; tapping the photo opens the drawer. Switching to Services restores the existing header. Returning Home restores the greeting without reloading the seller workspace or losing the Home scroll position. The name and photo come from the session, not test labels or a second account request.

### 5. Backend / API behavior

Unchanged. No endpoint, request, response, seller permission, session storage, order/product rule or data calculation changed. The existing approval check still governs seller presentation; Django continues to enforce authorization. The photo opens navigation rather than navigating directly to Profile on seller Home; Profile remains available through the existing drawer. Eleven protected source hashes include the drawer, Search, bottom navigation, seller content/service, auth/session, buyer banner, auth form and Django workspace.

### 6. Database / migration impact

None. No models, migrations, dependencies, assets, real account/order/stock records or deployment changed. Widget tests use isolated session/API-shaped fixtures; screenshot names and amounts are test fixtures only.

### 7. Tests performed

- Final related Flutter regression: **102/102 passed** across eleven files covering seller/buyer Home, profile button, seller workspace/layout, banners, dashboard header/search, seller drawer, floating navigation and center action. Includes six seller-header layouts: 280/320/390/414/768dp, with 2x text at 320/414dp and simulated top/side safe insets.
- Each new responsive integration case actually taps the avatar, returns through the existing drawer Home entry, opens Search and Notifications, changes tabs and returns Home. Assertions check minimum-48dp targets, no hamburger/duplicate greeting, single-line name truncation, full-name spoken action, right-side alignment and header-to-Sales spacing.
- Stored-image URL/error fallback and default profile behavior pass in both caption modes. Existing buyer-header profile shortcut, banner, approval/revocation, retained-state, refresh, seller permissions and tool-navigation regressions pass.
- Actual bundled-font renders reviewed at normal 390dp and narrow 320dp/2x text; the caption wraps at large text while action icons remain reachable. Six responsive header captures plus shared seller Home/catalog captures are in `renders/`. No generated image or replacement asset was used.
- Initial test development measured an IconButton's inner Tooltip instead of its full tap target and selected the outer blank semantics node. The final checks target the actual IconButtons and labelled semantics node. The long-name/2x drawer test scrolls its actual menu item into view and checks hit-testability; no missed taps are suppressed.
- Static analysis of all six changed Dart source/test files reported **no issues** (5.1 seconds); the final 102-test run finished in 33 seconds without missed-tap warnings. Eleven protected hashes and before/after comparisons confirm unchanged Dashboard code outside its header/greeting flag, Home code outside greeting visibility, and the original photo/fallback block. Logs: `flutter-tests.log`, `analyze.log`; scope evidence: `protected.json`, before-snapshots and `verify_scope.cjs` under `scratch/seller-home-header-20261102/`.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/seller_home_entry_test.dart test/header_profile_button_test.dart test/seller_home_layout_test.dart test/seller_workspace_test.dart test/home_page_test.dart test/campus_home_banners_test.dart test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/seller_drawer_test.dart test/floating_bottom_navbar_test.dart test/dashboard_center_add_button_test.dart
flutter analyze --no-pub lib/module_app/screens/dashboard_screen.dart lib/module_app/screens/home_page.dart lib/module_app/widgets/navigation/header_profile_button.dart test/seller_home_entry_test.dart test/header_profile_button_test.dart test/seller_workspace_test.dart
```

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device/TalkBack session, live-account change, app install/restart or deployment was performed. Full-name semantics and tap behavior were checked in Flutter tests; this is not a full accessibility audit. Real photo loading still depends on the existing saved URL/network; the current fallback remains available. The optional design-doctrine kit lacks its token/script files, so its external gates were not run; verification uses the actual Flutter implementation and tests.

If a seller still sees the hamburger on Home, inspect the existing verified approval state and tab index before changing permissions. A hamburger on another tab is intentional. If a name is truncated, its full value remains in the spoken menu action and drawer. A missing picture uses the existing initials fallback; inspect the saved profile URL rather than adding a replacement asset. If an old duplicate greeting remains, verify Dashboard passes `showWelcomeGreeting: false` for that approved account, then use your own Hot Reload.

Safe practice exercise: change only a disposable test fixture's full name to a longer value, run the first test command and verify the avatar still opens the drawer, both right-side actions work, and Sales Overview follows the header. Compare a pending seller: its buyer greeting/banner must remain. Never edit working users or approval records for a visual test.

## Seller Home without promotional banners - November 2, 2026

Superseded for banner visibility/placement by the November 4 restoration above: seller Home now has one existing carousel below Inventory Alerts, while its top banner remains suppressed.

This entry supersedes the older welcome/banner and bundles-first seller Home order below. Buyer Home keeps its existing campus promotional carousel. Seller Home now starts Welcome Back -> Sales Overview -> Orders Requiring Action -> Inventory Alerts -> Suggested Product Bundles. Existing Sales Trend follows these requested sections; Explore CampusHub remains afterward. No Seller Dashboard heading, subtitle or Quick Actions was introduced.

### 1. Cause / reason

Confirmed from the source: HomePage mounted the shared promotional carousel for everyone before its optional seller section. Removing the shared widget globally would also remove buyer banners. Seller Home also placed bundles before orders/inventory, and Recent Orders showed an unfiltered page of recent orders rather than an operational action queue. Filtering just that page would miss older open orders behind 30 newer completed orders. These are the specific presentation/data-boundary gaps corrected here; order workflows and metric definitions were not rebuilt.

### 2. Exact files changed, current lines and nearby anchors

Paths are relative to the project root; use the named anchor if later edits move lines.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/home_page.dart` | 34 `showPromotionalBanners`; 48 member; 230 banner conditional | Default banner visibility remains true for buyer Home. Omit the entire carousel subtree when the caller marks the approved-seller Home, removing its image/button/dots/timer together. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 393 banner flag | Pass false only when the existing approved-seller state and signed-in user are present. Header, role checks, services/catalogs and bottom navigation are unchanged. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 253 inline Home padding | Remove the extra 8dp above the existing seller section so Sales Overview starts after Home's existing 12dp greeting gap. |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 1561 `homeActionOrders`; 1692 order header; 1700 inventory header; following bundle include | Read the new server-owned open-order preview (with an older-server fallback), label operational sections as requested, and move existing bundles after inventory. Four KPI cards, period control, stock/suggestion helpers, actions and chart stay intact. |
| `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart` | 14 `emptyMessage`; 115 empty content | Reuse the existing five-order preview/detail navigation with a Home-specific honest empty message. Its default remains compatible with other callers. |
| `backend/core/modules/marketplace/mobile_seller_views.py` | 113 `order_rows`; 116 `serialize_order_row`; 126 `action_orders`; 137 response field | Add a read-only `orders_requiring_action` array of up to five oldest open owner-scoped orders, independent of recent-order pagination and Sales dates. Reuse the exact existing serialized order fields. |
| `backend/core/api/test_mobile_seller_workspace.py` | 206 action-order regression | Verify owner/status isolation, five-record limit, oldest pending history beyond a completed recent page, delivery remaining unpaid, page independence and no new order writes on reads. |
| `campushub/test/seller_home_entry_test.dart` | 84 seller/banner/greeting-gap checks; 424 regular states; 440 approval/revocation; actual render test | Verify seller-only absence, buyer/revoked presence, retained shell/nav/state and the direct greeting-to-sales placement. Capture loads actual Inter as well as existing fonts. |
| `campushub/test/seller_home_layout_test.dart` | 342 section order/actions; 419 action-preview regression; existing responsive/render cases | Update requested labels/order and verify the server preview plus old-server fallback/empty result. |
| `campushub/test/seller_workspace_test.dart` | 100 menu helper; 120 hit-test assertion; existing overview section expectations | Update order/labels and ensure See All is actually in the viewport before tapping, preserving real navigation verification. |
| `docs/mobile-seller-application.md`; `CAMPUSHUB_CONTEXT.md`; `campushub/DESIGN.md` | Current seller/buyer Home entries | Record the requested scope, data flow, checks, troubleshooting and safe practice. |

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Campus promotional carousel before seller KPIs | Sales Overview directly after Welcome Back | Removes the seller-only promotional block and its View Services/banner dots without removing buyer discovery. |
| Bundles before Recent Orders/Inventory Attention | Orders Requiring Action, Inventory Alerts, then bundles | Puts existing operational sections in the requested order. |
| Recent page used as the Home order preview | Up to five oldest open seller orders | Keeps older waiting orders visible even when newer completed records fill page one. |

The Weekly filter and four existing KPI cards remain. The actual seller's pending/processing/ready orders feed the action card. Inventory still uses the existing canonical available/reserved/threshold/status records and concise previews, including the existing expiry alert handling. Bundles keep the same eligibility, owner filtering, empty/error states, See All, View Suggestion and Create Bundle callbacks. The existing Sales Trend and later catalog previews remain, because the user requested removing the promotional banner, not those features. The order preview's own paging indicators are retained; the removed dots belong to the campus promotional carousel.

### 4. How it works / functions, inputs, outputs and data flow

`DashboardScreen.build` receives the existing asynchronously verified seller state. It passes `showPromotionalBanners: false` only for an approved seller with a current user. `HomePage(..., showPromotionalBanners: true)` defaults to the old buyer behavior; `HomePageState.build` conditionally mounts CampusHomeBanners, then the same optional seller content. This flag is independent of whether some other informational/error widget is supplied as `sellerSections`, so an ordinary buyer's status-error UI does not accidentally hide banners. Rejected, pending and revoked seller states retain regular Home.

`workspace(request)` still authenticates/authorizes with `approved_seller`, then obtains the existing `seller_order_queryset(account)`. The new open preview filters that same queryset by canonical pending, processing and ready_for_pickup states, orders by recorded creation date/ID and takes five. Delivered-but-unpaid orders remain open until the existing explicit payment/completion workflow finishes; completed/cancelled rows are not action previews. Sales period filtering remains confined to existing analytics calculations, so an older waiting order is not hidden by Weekly sales dates.

`serialize_order_row(order)` returns the same fields as the former inline serialization, including real product/buyer/items, status key, payment and fulfillment presentation. It feeds both unchanged paginated `orders` and new `orders_requiring_action`. Existing `order_count`, pagination, KPIs, recognized revenue and response cache/permission rules retain their definitions.

`SellerWorkspaceContent.homeActionOrders` reads the new array. If an older endpoint does not provide it, the compatibility path filters the existing loaded order page using its recorded status key/display value. `homeHighlights` passes the result to the existing SellerRecentOrders widget, with No orders require action right now when empty. No new endpoint, separate request, manufactured order or local revenue calculation is involved.

```text
Existing seller approval + bearer-authenticated workspace GET
  -> Django owner-scoped orders / canonical stock / eligible bundle suggestions
  -> unchanged KPIs + added bounded open-order preview
  -> same Flutter seller state and callbacks
  -> Sales -> Orders -> Inventory -> Bundles -> existing Trend

Buyer / pending / revoked account -> same Home carousel and catalogs
```

Annotated example, disposable test records only: 31 newer completed orders fill page one; a pending order from 90 days earlier still appears in `orders_requiring_action`. Another seller's pending order never appears, even if the request includes that seller's ID. Nothing is inserted or changed by the GET.

### 5. Backend / API behavior

The existing workspace GET adds one optional response key and bounded read-only queries. Existing consumers and older-server compatibility are preserved; no request contract or write endpoint changed. Fulfillment/payment transitions, stock reservation/release, seller approval/suspension, role permissions, seller service transport and navigation remain. Thirteen protected source hashes passed. Before/after comparisons also confirmed unchanged header/bottom-navigation implementation, buyer catalog/search/refresh code, stock/product/order/recommendation helpers, KPI/filter/chart code, original serialized order fields and seller authorization/write workflows.

### 6. Database / migration impact

No models, schema, migrations, dependencies, asset binaries, working records, session/preference resets or deployment. Django tests used an automatically created/destroyed local PostgreSQL database; Flutter screenshots use isolated API-shaped fixtures only. No demonstration orders/products were sent to working data.

### 7. Tests performed

- **24/24 Django/PostgreSQL tests passed** in 12.505 seconds across the mobile seller workspace and fulfillment suites; system checks were clean and the temporary database was destroyed. New coverage verifies old open orders beyond recent-page boundaries, owner isolation/ignored foreign seller parameter, open-only statuses, five-row limit, delivered-but-unpaid presentation, stable action queue across pages and unchanged order count on reads. Existing recognized-revenue, receiving, permission and constant-query-growth checks pass.
- **82/82 Flutter tests passed** in the broad seller/buyer Home, banner, header search, drawer and bottom-nav run. This includes the new server-array/fallback behavior and buyer/seller/approval-revocation banner checks, plus existing responsive, empty/error, filter, bundle/action, refresh/retained-state and permission coverage.
- The first broad run exposed a test-helper warning: it scrolled the section header into view but tapped See All below the viewport. The helper now explicitly brings the button into view and asserts hit-testability before tapping. The complete **15/15 seller workspace/navigation suite passed again** with no missed-tap warning. These 15 overlap the 82; they are not an additional unique test count.
- Static analysis of all eight changed Flutter source/test files reported **no issues** (42.0 seconds). Formatting completed. Actual Inter/bundled-font captures were reviewed for the shared header/greeting/Weekly/four-KPI/order view, inventory-to-bundles ordering and retained trend. The original buyer banner component remains unchanged and its auto-rotation/dots/navigation tests passed.
- Evidence: `scratch/seller-home-without-banner-20261102/backend-tests.log`, `flutter-tests.log`, `navigation-tests.log`, `analyze.log`, `protected.json`, `verify_scope.cjs`, `renders/shared/shared-home-seller-sections.png`, and the layout/standalone render folders. The enabled render tests produced actual Flutter widget images; no AI image was generated.

Reproduce Flutter checks from `campushub/`:

```powershell
flutter test --no-pub test/seller_home_layout_test.dart test/seller_home_entry_test.dart test/seller_workspace_test.dart test/home_page_test.dart test/campus_home_banners_test.dart test/dashboard_search_appbar_test.dart test/seller_drawer_test.dart test/floating_bottom_navbar_test.dart
flutter analyze --no-pub lib/module_app/screens/home_page.dart lib/module_app/screens/dashboard_screen.dart lib/module_app/screens/seller_dashboard_page.dart lib/module_app/screens/seller_workspace_content.dart lib/module_app/widgets/seller/seller_recent_orders.dart test/seller_home_layout_test.dart test/seller_home_entry_test.dart test/seller_workspace_test.dart
```

Backend reproduction uses the existing disposable-local runner from the repository root: `backend/core/venv/Scripts/python.exe -B scratch/operating-schedule-20261029/run_tests.py api.test_mobile_seller_workspace modules.marketplace.test_order_fulfillment`. It enforces the local test connection and destroys the timestamped database afterward; never import these fixtures into the working database.

### 8. Remaining limitations / troubleshooting / safe practice

No physical Flutter/IME session, live-account transaction, hosted Django rollout or forced app restart was performed. The complete action preview requires the updated Django workspace code to be served; an older endpoint still works through the loaded-page fallback, which cannot discover older orders outside that page. Preview limits remain five action orders and the existing three stock alerts; See All leads to the existing full tools. Buyer catalogs remain after seller operational content.

If a banner appears for a currently approved seller, inspect the existing verified approval state and the new Home flag; do not hide banners based only on an account role or any non-null sellerSections widget. If action orders look incomplete, inspect the new response array before changing frontend filters or Sales dates. If See All appears unresponsive in a test, scroll the actual button rather than only its section header; never suppress missed-tap warnings.

Safe exercise: in the disposable API test only, put an old pending owner order behind 31 completed records and verify the five-row action list still includes it on both order pages. In the Flutter tests, compare an approved seller with a pending/revoked account: the first has no `home-campus-banners`, while the latter retain the original carousel and bottom navigation. Follow bundle See All without submitting a bundle, and confirm Sales Overview/Orders/Inventory/Bundles order from widget coordinates. Leave all real accounts, orders and stock unchanged.

## Shared floating navigation — October 29, 2026

Latest November4 clarification: removed the rectangular backing strip by extending Dashboard body content behind the retained rounded pill. Root-tab scroll padding uses the measured navbar inset so final items remain reachable; Profile moves the inset into its scroll content. Seventy Flutter checks passed; whole-app analysis clean. Exact files/data flow/verification: [backing-strip report](mobile-profile.md#floating-navbar-remove-rectangular-backing-strip---november-4-2026).

November4 follow-up: tapped destinations/Add Product now have no rectangular ink splash or hover box; selected glyph/text/motion and circular keyboard-focus feedback remain. The existing root Scaffold keeps the dock visible during section scrolling. Sixteen navigation/dashboard/system tests passed with twelve enabled rest/pressed/scrolled captures. Exact files, functions/data flow and safe exercise: [current navbar report](mobile-profile.md#floating-navbar-no-tap-box-visible-while-scrolling---november-4-2026). No backend/database/seller-workflow change.

The shared FloatingBottomNavbar now uses an inset rounded dock for both account configurations. Approved sellers keep Home/Marketplace/Add Product/Services/Facilities; the gold center action remains raised16dp and calls the original DashboardScreen._openAddProduct. Its inputs are the same currentIndex, _goToTab callback and seller-only action callback; taps still select root pages or open the original form. No backend, permissions, records or approval behavior changed.

The [current floating-navbar guide](mobile-profile.md#shared-floating-bottom-navigation--october-29-2026) owns exact files/lines, eight-part report, measured geometry and checks. Sixteen focused tests passed, including seller action-vs-page behavior,48dp targets, label separation and large text. Safe exercise: use the isolated seller navbar test to tap Add Product and confirm its local action counter increments while selected index stays unchanged; never submit a live product for this layout check. App run/reload remains under the user's Ctrl+F5 control.

## Home category shortcuts and sales-period menu placement - October 29, 2026

1. **Cause / reason:** The user requested removal of Home's highlighted Snacks/category shortcuts and confirmed the Sales Overview dropdown was covering its filter/header. Home rendered saved preferences as ActionChips above its banner. The compact filter used Flutter's default over-button position and supplied `initialValue`, which aligns the selected row with the anchor instead of placing the whole menu below it.
2. **Exact files changed:** `campushub/lib/module_app/screens/home_page.dart:228` (`build`, banner now directly follows greeting spacing); `campushub/lib/module_app/screens/seller_workspace_content.dart:1540` (`salesPeriod`, under position at 1546 and 8dp offset at 1547); `campushub/test/home_page_test.dart:14` (no shortcut highlights); `campushub/test/seller_home_layout_test.dart:135` (menu bounds at 375dp and 320dp/2×); `campushub/test/seller_workspace_test.dart:893` and 920 (menu geometry plus actual period selection); `campushub/test/seller_home_entry_test.dart:104` (native drag-slop expectation); this guide at line 3; `docs/mobile-profile.md` latest note; `CAMPUSHUB_CONTEXT.md:3`; and `campushub/DESIGN.md` (`seller-sales-period`/Home). The same request also changes Facility Details rates, documented in `docs/mobile-services-navigation.md` top.
3. **Changes made:** Removed only Home's preferred-category chip row. Existing preference storage, optional Home constructor inputs, category discovery and Marketplace filters remain available. Set the compact PopupMenuButton to `PopupMenuPosition.under` with `Offset(0, 8)`; removed `initialValue` to prevent selected-row centering from pulling the menu upward. Existing checked Daily/Weekly/Monthly items still reflect the server period and call the same callback.
4. **How it works:** `HomePageState.build(context)` renders the greeting followed by CampusHomeBanners and existing catalogs/seller sections. It no longer builds buttons from `preferredCategories`. `salesPeriod(compact: true)` reads `analytics.period` for displayed text, checked item state and semantics. Selecting a menu item passes its existing `day`, `7` or `month` value through `onPeriod` to `SellerDashboardPage._changePeriod`, which reloads the authenticated workspace. Only menu placement changes; totals are still server results. Example: choosing Monthly from a Weekly overview still sends `month`, while the menu's top remains below the filter rather than over the Weekly label.
5. **Backend / API behavior:** Unchanged; preference persistence, seller ownership/RBAC, period normalization, workspace requests and all totals/calculations retain their existing implementation.
6. **Database / migration impact:** None; no records, schema, migrations or dependencies changed.
7. **Tests performed:** Combined six-file regression run passed **74 tests (15 seconds)**: `home_page_test`, `seller_home_layout_test`, `seller_workspace_test`, `seller_home_entry_test`, `facility_details_test` and `facility_booking_flow_test`. Seven changed Dart files passed analysis (2.1 seconds) and final formatting (zero changes). Menu bounds are checked for all three selected periods at normal/2× text; integration tests retain Daily/Monthly callbacks, reload counts and checked states. The initial run found a scroll expectation 20dp too large; isolated reproduction and Flutter's local controller documentation confirmed the default gesture threshold. The test now subtracts `kDragSlopDefault` from the requested 120dp movement; production scrolling was not changed. The final rerun passed.
8. **Remaining limitations:** No fresh screenshot or physical-device run. Native popup placement can still reposition to fit screen edges when there is insufficient room. No claim of live backend or full accessibility validation.

**Troubleshooting / safe exercise:** Reload through your normal workflow. Confirm Home has no Snacks/Beverages shortcut row, then open Sales Overview's filter and choose Daily, Weekly and Monthly. The menu should sit below the trigger and the selected label/totals should refresh normally. If the label changes but totals look unexpected, inspect the existing server response for that period rather than calculating totals in Flutter. Safely change only the fixture `analytics.period` in the existing menu-bounds test, run it, and trace the selection callback without writing real sales records.

## Suggested Product Bundles directly below KPIs - October 28, 2026

This user-requested placement supersedes the section order in the earlier dashboard report below. Current Home order is welcome/banner, Sales Overview KPI cards, Suggested Product Bundles, Recent Orders, Inventory Attention, Sales Trend, then Explore CampusHub. Current Inter typography remains unchanged.

1. **Cause / reason:** the existing bundle section followed Sales Trend. The user requested it immediately below the KPI cards.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/screens/seller_workspace_content.dart:1325` (`homeHighlights`), `:1438` (moved recommendations header), `:1442` (existing `suggestions(context, preview: true)`), `:1443` (Recent Orders); `campushub/test/seller_home_layout_test.dart:318` (expected section order); `campushub/test/seller_workspace_test.dart:404` (section traversal order); this guide at line 3; `CAMPUSHUB_CONTEXT.md:3` (latest entry). Five project files, one runtime file.
3. **Changes made:** moved the existing header and preview together directly after the four KPI cards. Removed their previous position below the chart, so the section still appears once. Updated the two existing ordering checks; no new test suite or replacement component was added.
4. **How it works / functions, inputs, outputs and data flow:** `homeHighlights(context)` returns the same ordered widget list with a different placement. Existing workspace JSON -> `suggestions(context, preview: true)` -> owner-filtered recommendation cards or honest empty/error state. `sectionHeader(..., SellerDestination.recommendations)` still sends See All to the same destination; View Suggestion/Create Bundle/Retry retain their callbacks. Example: an eligible pair now appears between Pending Orders' KPI row and the Recent Orders heading; its product IDs and record are unchanged. Moving the shared section preserves both inline Home and the existing standalone overview without duplicating data or navigation.
5. **Backend / API behavior:** unchanged. No service, endpoint, permissions, paid-sales, order, inventory, recommendation or Apriori changes.
6. **Database / migration impact:** none. No models, migrations, dependencies, sessions or working records changed. Screenshot data remains isolated test fixtures.
7. **Tests performed:** **45 Flutter tests passed** in 9 seconds across existing seller Home layout, workspace and Home-entry suites. These cover requested ordering, existing bundle actions and See All, responsive/empty/error states, carousel behavior and seller approval/revocation/retained Home. Three-file analysis reported **No issues found** (1.7s); format check reported **3 files, 0 changed**. Render evidence refreshed under `scratch/inter-home-20261028/`; log: `bundle-position-tests.log`. No native device action or full backend test run was performed.
8. **Remaining limitations / troubleshooting / safe exercise:** no hot reload/restart/install was performed. Use your own Hot Reload to display this order; if the earlier new Inter assets are not yet loaded, stop and rerun Flutter as described in the typography guide. Safe exercise: inspect the `sections` list at the test anchor above, run `flutter test --no-pub test/seller_home_layout_test.dart`, and verify the bundle heading is below both KPI rows and above Recent Orders. Test See All without creating a real bundle or editing records; empty recommendations should remain in the same position with their honest message.

## Compact Seller Home and swipeable Recent Orders - October 28, 2026

### 1. Cause / reason

Confirmed from the existing Flutter implementation: KPI labels used a one-line ellipsis; Home reused tall Inventory/Orders detail cards; Recent Orders showed only three vertical records; bundles preceded urgent operational sections; catalog strips relied on estimated fixed heights. The user requested a presentation refinement of the existing Home, not a replacement dashboard. Existing owner-scoped Django workspace data and shared routes were already suitable. No backend defect or accounting error was inferred.

### 2. Exact files changed and current code anchors

| File | Current line / nearby code anchor | What changed |
| --- | --- | --- |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 979 `_inventoryAttention`; 1058 `_showOrderDetails`; 1255 `suggestions`; 1336 `homeHighlights`; 1474 `_overviewMetricCard`; 1536 `sectionHeader` | Compact Home summaries, existing detail handler extracted for reuse, two-column metrics, reordered sections and existing destinations |
| `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart` | 7 `SellerRecentOrders`; 28 `didUpdateWidget`; 59 `_height`; 130 `PageView.builder` | New five-order manual carousel with identity-aware updates, measured wrapping, accessible gold indicators and exact-row detail callback |
| `campushub/lib/module_app/widgets/seller/seller_sales_trend.dart` | 6 `SellerSalesTrend`; 14 `_SellerSalesTrendState`; 114 `Slider` | Existing series/painter retained; readable date/value inspection, keyboard control and compact zero-sales state |
| `campushub/lib/module_app/screens/home_page.dart` | 130 `_section`; 185 local `strip`; 255 `EXPLORE CAMPUSHUB`; 265 catalog sections | Natural-height horizontal previews, bounded widths, shared spacing and honest facility empty wording |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 43 `HomeSectionHeader`; 160 `MarketplacePreviewCard`; 296 stock summary; 354 `FacilityPreviewCard`; 431 rate; 479 `ServicePreviewCard` | Responsive headers, stock text, accessible cart action, price font fallback, consistent 126dp images, facility capacity/rate/status and saved service descriptions |
| `campushub/lib/module_app/screens/search_page.dart` | 221 `_productCards` | Natural-height equal-height rows for the shared product card, preventing its new stock/cart content from clipping in Search |
| `campushub/test/seller_home_layout_test.dart` | 134 carousel test; 200 reorder/shrink test; 368 real Explore tests; 488 optional render test | New interaction, responsive, long-text, empty/error, keyboard and render coverage; all data is isolated test fixtures |
| `campushub/test/seller_workspace_test.dart` | 97 `menu`; 361 branded Home test; 478 zero-sales test | Explicit outer-scroll targeting for the new nested PageView, requested section sequence and current initially visible section |
| `campushub/test/home_page_test.dart` | 209 / 213 facility empty-state assertions | Expect “No facilities are currently listed.” |
| `docs/mobile-seller-application.md` | 3 this section | Implementation report, troubleshooting, data flow and safe exercise |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Current behavior and verification record |

Eleven project files: six runtime Dart files, three test files and two existing documents. Render evidence and logs are under ignored `scratch/seller-home-20261028/`; no additional preview startup entry point was added. Earlier guide line numbers below are historical snapshots; use this table for this change.

### 3. Changes made

- The four existing KPIs remain a two-column grid, including narrow/large-text layouts. Labels wrap in full. Text measurement determines a shared height for all four cards; icons align above labels. Total Sales opens existing Sales Analytics; the order counts open existing Orders Received. No unsupported status-filter route was invented.
- Recent Orders now uses one full-width PageView page per order, the newest five rows from the current owner-scoped first API page, with no timer. Cards display the actual code, status, buyer, total, payment status and date. View Details reuses the existing exact-row detail view, including its existing items and fulfillment actions. See All reuses Orders Received. Pagination controls have 48dp targets, semantic selected labels and keyboard activation; the active dot is gold with a navy outline and a larger size. Zero orders has a concise honest message; one order has no dots.
- Inventory Attention still selects the existing low-stock/out-of-stock/expired rows and caps Home at three. It now shows product/SKU, a three-column On Hand/Reserved/Available row, actual status and actual threshold. Derived bundle availability retains its existing label. The complete Inventory destination is unchanged.
- Home order is welcome/banner, Sales Overview, Recent Orders, Inventory Attention, Sales Trend, Suggested Product Bundles, then Explore CampusHub. Bundles remain owner-filtered and show at most two concise previews; existing View Suggestion/Create Bundle/See All actions remain. Empty and API-error messages are distinct; Retry uses the existing reload callback.
- Sales Trend still paints the same actual daily data. First/last dates format compactly when ISO dates are supplied. Tapping the chart selects the nearest recorded day; its exact amount is shown below. A native Slider provides tooltip, keyboard and semantic inspection when there are multiple days. Zero paid sales keeps a shorter chart and honest message; invalid series stays unavailable. Loading/error/retry remains handled by the existing seller workspace loader.
- Marketplace/Facilities/Services keep their actual loaders and detail callbacks. Preview strips now size to their tallest content instead of guessing text height, align their first card to the same 16dp Home inset, retain manual scrolling and cap widths rather than stretching cards across tablets. All three use 126dp image areas. Facility capacity can wrap, the existing rate formatter supplies its rate summary, and status is displayed as supplied by the model without inferring slot availability or using a green status dot. Service summaries use the recorded description, falling back to the actual category when none is recorded. Product cards retain category and availability, show low/zero/unpurchasable stock text, and give the existing cart action a labelled 48dp button. Montserrat fallback supports the peso glyph in the shared price style. Header actions stack below full-width titles on narrow screens at large text sizes.

The changed seller summary typography reuses `ProfileStyle.identityText` (bundled Montserrat with its weight axis); shared catalogs retain their configured bundled UI font. Existing mobile navy/gold tokens are reused, including mobile gold `#FCB315`, without changing the global palette, sidebar or bottom navigation. Native buttons retain focus/pressed/disabled behavior; no new dependency or animation package was added.

### 4. How it works: functions, inputs, outputs and data flow

```text
Authenticated user -> existing approved-seller status check
  -> SellerApplicationService.workspace(period, ordersPage)
  -> Django approved_seller + seller_order_queryset(account)
  -> existing overview / orders / inventory / analytics / recommendations JSON
  -> SellerWorkspaceContent.homeHighlights(context)
       orders -> SellerRecentOrders -> PageView -> exact-row _showOrderDetails
       inventory -> existing attention filter -> three compact rows
       analytics -> unchanged KPI values + SellerSalesTrend
       owned qualifying recommendations -> two concise previews
  -> existing HomePage catalog loaders -> natural-height horizontal strips
```

`SellerRecentOrders` takes order maps and the existing money/date/detail callbacks. `_rows` takes the first five without fetching anything or recalculating statuses/totals. Django already sorts this page newest-first. `_height(context, width, row)` uses TextPainter with the same inherited style, text scaler and available widths as the card, including wrapped button text. The largest result gives every page the same height. The PageController owns the selected page; disposal releases it. `didUpdateWidget` matches the selected order ID when a supplied list changes and moves safely to the first record if it disappears. The existing keep-alive Home section and retained tabs still preserve state when browsing away and back; no new resume/return requests were added. A deliberate full workspace reload can reconstruct the section; selection across that reconstruction is not guaranteed by the identity-update test.

`_showOrderDetails(context, row)` was moved out of the existing order-card callback so both the list and carousel open the same ProfileDetailScaffold and invoke the same fulfillment handler. It does not fetch a different order or add a new order route. Example using test fixtures only: swiping from `ORDER-100` to `ORDER-99`, then choosing View Details, opens `Order ORDER-99` with Buyer 1 and its recorded Unpaid status; returning keeps page 2 selected. No paid state or completed sale is inferred from viewing it.

`HomePage.strip` uses SingleChildScrollView + IntrinsicHeight + Row over at most six cards. Each card receives a fixed bounded width, while the row height follows real content and text scaling. Search needs the same treatment because it reuses MarketplacePreviewCard; `_productCards` now uses intrinsic rows of its existing one/two/three columns. This adds intrinsic layout work over these small rows instead of introducing a new widget library or continually increasing guessed heights. No performance benchmark is claimed.

### 5. Backend / API behavior

Unchanged. Read-only inspection of `backend/core/modules/marketplace/mobile_seller_views.py:70` (`workspace`) confirms approved active mobile-seller enforcement, owner-scoped `seller_order_queryset(account)`, and sales derived from `valid_sales_queryset` (completed and paid). The existing page at line 95 is newest-first, **30 orders per page**; it has no caller-configurable page-size parameter. Home takes five from that existing first response and does not load subsequent history pages. No new five-record server optimization was guessed. Existing Total Orders/Completed/Pending counts, period selection, paid-sales accounting, fulfillment/payment separation, inventory reservations/thresholds, saved recommendations and Apriori remain authoritative and unchanged. The seller detail screen still has no new payment action. `inventory_views.py` and `mobile_services.py` were not edited.

### 6. Database / migration impact

None. No database access was required to implement or verify these Flutter presentation changes. No schema, migration, account, role, seller approval, authentication, session, order, stock, recommendation or working-record writes. Existing dependencies and service contracts are unchanged. Synthetic names/orders are restricted to test fixtures and screenshots; production consumes the original authenticated APIs.

### 7. Tests performed

- Final **81 Flutter tests passed** across ten suites in **11 seconds** in the recorded final run: new seller Home layout, existing seller workspace, seller Home entry/lifecycle, regular Home, banners, header/search navigation, shared drawer, Search, order fulfillment and Home card/navigation tests. The render environment variable was supplied, so the optional screenshot test actually ran.
- New coverage verifies zero/one/seven source orders (five shown), manual swipe/no automatic movement after twenty simulated seconds, active indicator styling, keyboard indicator activation, exact details and return state, reorder/shrink/empty updates, existing KPI/See All destinations, three actual-threshold stock summaries and horizontal quantity alignment, honest bundle empty/error states, and keyboard inspection of exact recorded trend values. Width/text-scale cases include 280/2x, 320/2x, 414/1x and 600/1.3x; existing tests additionally cover landscape and seller/non-seller approval, revocation, retry, tabs, retained state/scroll and deliberate refresh.
- Real Explore widgets were exercised at 320px/2x and 414px/1x, with first-card bounds, manual product scrolling and all three See All callbacks. Existing navigation tests still open product/facility/service destinations, and fulfillment tests still verify separate payment behavior.
- Final scoped Flutter analysis of all nine changed Dart files reported **No issues found** (1.1s), after the final price-fallback/capacity-wrap refinement. Final `dart format --output=none --set-exit-if-changed` reported **9 files, 0 changed** (0.11s). Scoped whitespace checks passed. No web-kit N/N score, native device result or full TalkBack/WCAG certification is claimed.
- Rendered fourteen PNGs using bundled fonts: four seller-section captures in light/dark surrounding themes and Marketplace/Facilities/Services at both tested Explore widths. Visually inspected KPIs/orders/stock/trend/bundles and catalog examples, including the final large-text heading layout. Screenshots use white captured surfaces and isolated fixtures; initial transparent captures/Ahem test-font captures were replaced. Final large-text facility capacity wrap and price-font fallback are checked in the final screenshots.
- Initial verification exposed fixed Search-height clipping, a wrapped carousel button omitted from its height calculation, a narrow large-text period/header layout, and test helpers that ambiguously targeted nested scrollers. These were corrected. Outdated empty-text/section-order assertions were updated without removing existing permission or workflow coverage. Early failures/logs are retained separately from the successful final results.

Commands (from `campushub/`):

```powershell
flutter test --no-pub test/seller_home_layout_test.dart test/seller_workspace_test.dart test/seller_home_entry_test.dart test/home_page_test.dart test/campus_home_banners_test.dart test/dashboard_search_appbar_test.dart test/seller_drawer_test.dart test/search_page_test.dart test/order_fulfillment_test.dart test/home_card_background_test.dart
```

Evidence: `scratch/seller-home-20261028/tests-final.log`, `analysis-final.log`, `layout-renders.log`, and the PNGs in that directory. Test/analysis execution used outside-sandbox access to the installed Flutter SDK/user cache; it did not run, restart, install or control the user's app.

### 8. Remaining limitations, troubleshooting and safe learning exercise

No physical-device/emulator installation, hot reload/restart, backend test run or real-account order submission/payment/stock action was performed. The UI uses the last loaded authenticated snapshot until the existing deliberate refresh; it is not a new real-time order subscription. The API still returns its original 30-row page. Catalog names/descriptions use concise existing line limits; the full values remain in existing details. At extreme text lengths/scales, a complete order card can be taller than the viewport; normal vertical Home scrolling exposes the entire card without clipping its content. The chart remains the existing custom line chart, with exact-day value inspection rather than a new charting dependency. The optional design-kit gate files were absent, so native Flutter checks and rendered evidence were used instead of inventing a web gate result.

If a screen looks stale, apply your own Flutter Hot Reload/Hot Restart and reopen Home; no automatic device action was taken. If no seller sections appear, inspect the existing approved active seller status and bearer response; never force approval in the UI. If the recommendation service fails, its Retry refreshes the original workspace rather than displaying empty-success data. If only one order exists, absent pagination is intentional. Home's latest-five list is independent of its sales-period filter, matching the existing API semantics.

Safe exercise: run `flutter test --no-pub test/seller_home_layout_test.dart`, find the isolated `layoutData(orders: ...)` fixture, temporarily change its test call from seven orders to one, and observe that pagination disappears while the detail action remains. Restore the fixture and rerun; verify five page indicators return. For large text, inspect the `(320.0, 2.0)` case and confirm the KPI labels wrap, quantities remain in three columns and no RenderFlex overflow is reported. Follow `onDetails -> _showOrderDetails -> detail -> ProfileDetailScaffold` without editing API URLs, permissions or real records. This teaches layout/state changes safely outside production data.

## Stop unnecessary dashboard refresh on return and resume - October 28, 2026

This extends the offscreen-state correction below. Access verification still runs when returning to Home or resuming the app; unchanged seller access no longer reloads dashboard content.

1. **Cause / reason:** confirmed by two failing regressions: `_goToTab(0)` and `didChangeAppLifecycleState(resumed)` both called `_loadUserName()`, which incremented `_sellerRefreshRevision` every time approval was true. The inline seller page interpreted every increment as a content-refresh request and replaced its sections with loading content. Both trigger tests observed a second workspace read even though the seller remained approved.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:102` (`_loadUserName` optional input), `:129` (guarded revision increment), `:162` (`_refreshHome` explicit refresh); `campushub/test/seller_home_entry_test.dart:135` (return/resume trigger matrix), `:137` (regression names), `:178` onward (workspace/status/scroll assertions); this existing guide and `CAMPUSHUB_CONTEXT.md:3`. Four files; one runtime source file. The preceding keep-alive correction remains intact.
3. **Changes made:** add optional `refreshWorkspace = false` to `_loadUserName`. Increment the seller refresh revision only when access is approved and this input is true. `_refreshHome()` explicitly passes true; ordinary initialization, Home-tab return, app resume and seller-status callbacks keep the default access-check behavior. Initial/newly approved seller sections still load when created. Manual Retry, sales-period filters and existing data-changing actions retain their current behavior.
4. **How it works / inputs, outputs and data flow:** `_loadUserName()` still loads the saved authenticated user, calls the existing seller-status service and updates identity, approval and any access error. Its optional boolean now controls only the content-refresh revision output. Example: `_loadUserName()` verifies access without asking an unchanged seller section to reload; `_loadUserName(refreshWorkspace: true)` also increments the revision. `HomePage._refresh -> _refreshHome -> explicit true -> revision -> SellerDashboardPage.didUpdateWidget -> _load` remains the deliberate refresh path. Successful Add Product still uses `_refreshHome`. This separates access verification from refresh intent without removing either workflow.
5. **Backend / API behavior:** no endpoint, permission or server logic changes. Returning/resuming still checks seller status, so approval/revocation can update Home and its drawer. It no longer refetches the workspace merely because an unchanged approved status was verified. Django remains authoritative for all seller operations; authentication/error handling is unchanged.
6. **Database / migration impact:** none. No schema, record, token, session, order, inventory, analytics or dependency changes. All regression users/data remain test fixtures.
7. **Tests performed:** both pre-fix regressions failed with expected one workspace request / actual two. Final **43 Flutter tests passed** (18s) across seller Home/workspace, regular Home, campus banners and header search/navigation. New cases confirm Home-tab return and app resume each perform one status check, no extra workspace fetch, the same scroll offset and the same seller State. Existing browsing/pull-to-refresh, approval/revocation, retry and seller-tool cases pass. Dart formatting completed; scoped whitespace check passed. Two-file Flutter analysis completed with **No issues found** (43.6s).
8. **Remaining limitations / troubleshooting / safe exercise:** actual permission changes or a failed access check may still change visible seller content through the existing fail-closed behavior. Dashboard figures remain the last loaded snapshot until deliberate refresh or an existing data-changing action. No native device/emulator interaction, build/install, app restart or backend regression run was performed. Safe exercise: use your own Flutter Hot Restart once to load all accumulated lifecycle changes, scroll Home down, switch to Services and back, then minimize/restore the app; unchanged access should preserve the dashboard and scroll position. Pull down from the top to explicitly refresh. Reproduce safely with `flutter test --no-pub test/seller_home_entry_test.dart` without modifying real records.

## Home scrolling preserves inline seller state - October 28, 2026

1. **Cause / reason:** confirmed by a failing widget regression: Home uses a lazy vertical `ListView`. Its inline `SellerDashboardPage(homeSection: true)` was disposed after scrolling past it and recreated on the way back. Recreation reran `initState() -> _load()`, increasing workspace reads from one to two without a refresh gesture. `_load()` temporarily renders a short loading indicator instead of the seller sections; that height change can cause the reported scroll jump. Unwanted reload was reproduced; the user's exact native-device jump was not captured.
2. **Exact files changed / current anchors:** `campushub/lib/module_app/screens/seller_dashboard_page.dart:51` (`_SellerDashboardPageState`, keep-alive mixin), `:55` (`wantKeepAlive`), `:240` (`super.build(context)`); `campushub/test/seller_home_entry_test.dart:28` / `:44` (fixture request counter), `:76` (`browsing Home preserves seller state; pull-to-refresh still works`); this existing feature guide and `CAMPUSHUB_CONTEXT.md:3`. Four files, one application source file. HomePage, sidebar, bottom navigation and backend source are unchanged.
3. **Changes made:** add Flutter's `AutomaticKeepAliveClientMixin` to the seller page state and return `widget.homeSection` from `wantKeepAlive`. Call `super.build(context)` so the parent lazy list receives the keep-alive notification. Only the inline Home section asks to survive scrolling outside the viewport; standalone seller tools retain their usual lifecycle. No forced scroll-to-top, extra controller or artificial refresh timer is introduced.
4. **How it works / functions, inputs, outputs and data flow:** the existing DashboardScreen supplies the authenticated user, verified seller approval, `homeSection: true` and refresh revision. The mixin consumes `homeSection` and retains the existing State/data/filter subtree while the vertical ListView recycles other offscreen children. Scrolling back reuses that state rather than calling `initState()` again. Real refresh still uses `HomePage._refresh() -> DashboardScreen._refreshHome() -> _loadUserName() -> refreshRevision -> SellerDashboardPage.didUpdateWidget() -> _load()`. Existing authorization, error/retry and lifecycle/status refreshes remain active. Removing seller access still removes the seller section from Home.

   Annotated example: `first Home load: workspaceReads = 1 -> scroll to Services -> scroll back to Sales Overview: still 1 and the same State -> pull downward at Home's top: workspaceReads = 2`. Only deliberate refresh should cause the last request in this example. Retaining one bounded inline dashboard is narrower than rebuilding Home as an eager scroll view or disabling refresh.
5. **Backend / API behavior:** existing Django endpoints, bearer authentication, approval checks, ownership, forecasts, FIFO, Apriori and order/payment rules are unchanged. Normal browsing no longer causes the duplicate seller-status/workspace reads from widget recreation. Deliberate refresh, app-resume verification and access-revocation handling remain as before.
6. **Database / migration impact:** none. No schema, migration, account, seller permission, inventory, order, session or saved-data changes. The request counters and workspace responses are isolated widget-test fixtures.
7. **Tests performed:** reproduced the pre-fix extra request (expected one workspace read, actual two), then confirmed the same regression passes after the keep-alive change. Final **41 Flutter tests passed** in 9 seconds across `seller_home_entry_test.dart`, `seller_workspace_test.dart`, `home_page_test.dart`, `campus_home_banners_test.dart` and `dashboard_search_appbar_test.dart`. The new regression checks normal small-scroll offset, stable seller State, unchanged request counts while browsing, and a real pull-to-refresh gesture producing the second workspace request. Existing regular-user layouts, seller approval/revocation, tools/routes, banners/search and bottom navigation also pass. Two-file analysis: **No issues found** (1.8s). Formatting check: **2 files, 0 changed**. Scoped whitespace check passed. The refresh test explicitly returns to scroll offset zero before dragging; an earlier gesture away from the leading edge correctly did not refresh.
8. **Remaining limitations / troubleshooting / safe exercise:** no native-device/emulator interaction, hot reload/restart, APK installation or backend test run was performed. This fixes the reproduced inline-seller recreation; it does not establish every possible source of a device scroll jump. The retained seller subtree uses memory while offscreen and is released with its Home/route or removal after access changes. Safe exercise: apply your own Flutter Hot Reload, scroll from Sales Overview down to Services and back, and verify seller cards no longer flash a fresh loading spinner. Pull down only from the very top and verify refresh still works. Run `flutter test --no-pub test/seller_home_entry_test.dart` to repeat the isolated check without changing real account or marketplace data. When debugging another jump, distinguish ordinary scrolling from a top-edge refresh or app-resume status check before modifying their existing handlers.

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

---

## Seller Home: "See All" Now Matches Home Instead of Showing a Literal ">"

### Cause (confirmed)
- The seller dashboard section headers printed `See All >` as one text string. The `>` was a typed character, not an icon, so it looked different from Home's `HomeSectionHeader`, which renders the words `See All` plus a small `arrow_forward_ios_rounded` icon (`campushub/lib/module_app/widgets/home/home_preview_cards.dart:66-92`).
- The correct, shared pattern is **"See All" + a trailing chevron icon**, because the icon scales and aligns consistently with the other CampusHub "See All" actions.

### Exact files changed
- [campushub/lib/module_app/screens/seller_workspace_content.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_workspace_content.dart#L414-L423): added the `_seeAllLabel` getter.
- Same file, line ~1573 (`_recentOrdersHeader`) and line ~1816 (`sectionHeader`): replaced `const Text('See All >')` with `_seeAllLabel`.
- [campushub/test/seller_workspace_test.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/test/seller_workspace_test.dart#L451-L453): the tap target now finds `See All` instead of `See All >`.
- `campushub/DESIGN.md` line ~311: updated the wording to "See All (with a trailing chevron icon, matching Home)".

### How it works
1. `_seeAllLabel` returns a `Wrap` containing a `Text('See All')` and an `Icon(Icons.arrow_forward_ios_rounded, size: 11, color: ProfileStyle.navy)`.
2. `Wrap` is used instead of `Row` because `Row` gives its children unlimited width, so at 2x text scale the label overflowed by 87 px. `Wrap` lets the icon move to a second line and lets the text shrink/wrap, so the header stays inside the screen at 320 px width with 2x text.
3. Both the Recent Orders header and every `sectionHeader` (Inventory Alerts, Suggested Product Bundles, etc.) use the same getter, so the action looks identical everywhere.
4. Tapping the button still calls `widget.onNavigate(...)` with the same destination; no navigation behavior changed.

### Backend / API behavior
- Unchanged. This is presentation-only; no request, payload or endpoint was touched.

### Database / migration impact
- None.

### Tests performed
- `flutter analyze lib/module_app/screens/seller_workspace_content.dart test/seller_workspace_test.dart`: no issues.
- `flutter test test/seller_workspace_test.dart test/seller_home_layout_test.dart`: 41 passed, 2 failed. The two failures are the pre-existing `recent-order ... badge hugs its label` width assertions (`Expected: a value less than <154.5>, Actual: <201.0>` / `<190.75>`); they also fail with the original `See All >` text, so they are unrelated to this change.
- Verified the narrow/large-text cases now pass: `sales menu stays below its filter at 320.0/2.0`, `seller Home wraps long data at 320.0/844.0/2.0`, and `seller profile header and zero sales fit Size(320.0, 812.0) at 2x text`.

### Remaining limitations
- The chevron uses a fixed `size: 11`, matching Home, so it does not grow with the user's text scale. That is the existing Home convention.
- Not yet checked on a physical phone; verification was widget tests only.

### Safe practice exercise
1. Open `seller_workspace_content.dart` at `_seeAllLabel` (around line 414).
2. Change `size: 11` to `size: 16`.
3. Run `flutter test test/seller_workspace_test.dart` from the `campushub` folder and confirm the "See All" test still passes.
4. Change it back to `11` so the seller header stays visually identical to Home.

---

## Add Product: Tags Placeholder Is Centered and No Longer Clipped

### Cause (confirmed)
- The Tags field wraps its chips and text entry in a `Wrap` inside a `ConstrainedBox(minHeight: 50)`. `Wrap` places its runs at the top of that box, so the empty placeholder `e.g. homemade, snacks` sat above the vertical center of the 54 px container.
- When at least one chip existed, the text entry was forced to a fixed `120` px width. At 2x text scale on a 280 px-wide screen the hint `Add a tag` was clipped to `Add a ...`, which looked unbalanced next to the chip.

### Exact files changed
- [campushub/lib/module_app/widgets/seller/product_tag_input.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/widgets/seller/product_tag_input.dart#L110-L118): the `Wrap` is now wrapped in `Align(alignment: AlignmentDirectional.centerStart, ...)`, which centers the run vertically while keeping it left-aligned.
- Same file, line ~151 (`SizedBox` width): the entry width is now `160 * MediaQuery.textScalerOf(context).scale(1)` capped at `constraints.maxWidth`, so the hint grows with the user's text size instead of being clipped.

### How it works
1. `ConstrainedBox(minHeight: 50)` keeps the field the same height as the other single-line fields.
2. `Align` fills that height and centers its child vertically; the child `Wrap` sizes to its content height. Result: chips and the placeholder sit in the middle of the border instead of at the top.
3. When tags are empty, the entry still takes the full width (`constraints.maxWidth`).
4. When tags exist, the entry requests up to `160` logical pixels multiplied by the current text scale, never more than the available width. At 2x scale on 280 px the entry becomes the full row width, so `Add a tag` is fully visible.
5. `Wrap` still moves the entry to a new line when it does not fit beside the chips; no chip is ever clipped.

### Backend / API behavior
- Unchanged. Tags are still serialized as the same comma-separated string by `ProductTagInput.commit` / `values`.

### Database / migration impact
- None.

### Tests performed
- `dart format` and `flutter analyze lib/module_app/widgets/seller/product_tag_input.dart`: no issues.
- With bundled fonts loaded (`PRODUCT_FORM_REVIEW_DIR` set): `flutter test test/seller_add_product_page_test.dart` → 27 passed, 1 failed. The failure is `category popup stays aligned after keyboard inset changes`; it passes when run alone, so it is a pre-existing order-dependent test, unrelated to tags.
- Tag-specific tests pass both individually and in the full run: `tags become removable chips...`, `long tag chips fit a narrow large-text form...`.
- Captured renders at 390x844/1x and 280x844/2x: the placeholder is vertically centered, and `Add a tag` is no longer truncated.

### Remaining limitations
- The placeholder still does not wrap to multiple lines; very large text (for example 3x) on a very narrow screen can still clip a long hint. The 2x case requested here is fixed.
- Verified with widget renders, not a physical phone.

### Safe practice exercise
1. Open `product_tag_input.dart` around line 151.
2. Change `160` to `120`.
3. Run `flutter test test/seller_add_product_page_test.dart --plain-name "long tag chips fit a narrow large-text form and keep their remove action"` from `campushub` with `PRODUCT_FORM_REVIEW_DIR` set, then look at `tag-chips-280.png`. The `Add a tag` hint will be clipped again.
4. Change it back to `160`.

---

## Add Product: Footer "Back" Text Button Removed (Header Arrow Kept)

### Cause (confirmed)
- The Add Product footer showed an `OutlinedButton` labelled `Back` beside `Next` on steps 2-4. The header `BackButton` arrow already performs the same `_back()` action (previous step, or exit on step 1), so the footer text button was redundant.

### Exact files changed
- [campushub/lib/module_app/screens/seller_add_product_page.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_add_product_page.dart#L600-L643): `_navigation` no longer builds the `OutlinedButton` or the two-button `Row`/`Column`; it always returns the full-width primary button (`Next` / `Submit for Approval`). The header `leading: BackButton(onPressed: _busy ? null : _back)` remains.
- [campushub/test/seller_add_product_page_test.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/test/seller_add_product_page_test.dart#L181-L209): the `back` helper now taps `find.byType(BackButton)`; `expectStep` asserts the header arrow exists and `back-product-step` no longer exists; the pending-submission test checks that the header arrow is disabled while busy.

### How it works
1. The footer now contains only the primary action: `Next` on steps 1-3 and `Submit for Approval` on step 4.
2. The header arrow calls `_back()`: on steps 2-4 it calls `_changeStep(_step - 1)`; on step 1 it pops the page.
3. `PopScope` still maps the platform back action to the same behavior while the form is not busy.
4. Because there is only one button, the previous narrow-screen/large-text stacking logic for two footer buttons is no longer needed.

### Backend / API behavior
- Unchanged. No endpoint, payload or validation was touched.

### Database / migration impact
- None.

### Tests performed
- `dart format` and `flutter analyze` on the edited screen and test file: no issues.
- `flutter test test/seller_add_product_page_test.dart`: 34/34 passed with bundled fonts (`PRODUCT_FORM_REVIEW_DIR` set).
- Targeted tests also passed alone: `keyboard, header Back and platform Back retain the same draft`, `seller access and empty category guards keep their existing behavior`, `submission is authenticated, guarded while pending and retains review on error`.

### Remaining limitations
- The footer no longer shows a labelled `Back` action; previous-step navigation now relies on the header arrow or the platform back action. This matches the request.
- Not yet checked on a physical phone.

### Safe practice exercise
1. Open `seller_add_product_page.dart` at `_navigation` (around line 600).
2. Wrap the returned `SizedBox` in the previous two-button `Row` by re-adding an `OutlinedButton` with `key: ValueKey('back-product-step')` and `onPressed: _busy ? null : _back`.
3. Run `flutter test test/seller_add_product_page_test.dart --plain-name "keyboard, header Back and platform Back retain the same draft"`; the `expectStep` assertion `back-product-step` finds nothing will fail.
4. Remove the added button again to restore the requested single-button footer.

---

## Add Product: Tags Help Tooltip Copy Updated

### Cause (confirmed)
- The Tags help tooltip used the older sentence `Type a tag, then press Enter or a comma to add it. Tap × to remove. Next saves unfinished text too.` The requested copy is shorter and does not mention the Next behavior.

### Exact file changed
- [campushub/lib/module_app/widgets/seller/product_tag_input.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/widgets/seller/product_tag_input.dart#L10-L11): `ProductTagInput.instructions` is now `Type a tag and press Enter or comma to add it. Tap × to remove a tag.`

### How it works
1. The info icon (`ValueKey('product-tags-info')`) opens a `Tooltip` whose `message` is `ProductTagInput.instructions`.
2. Tests and the tooltip both read the same constant, so there is one source of truth.

### Backend / API behavior
- Unchanged. Tags are still committed as the same comma-separated string.

### Database / migration impact
- None.

### Tests performed
- `flutter analyze lib/module_app/widgets/seller/product_tag_input.dart`: no issues.
- `flutter test test/seller_add_product_page_test.dart --plain-name "tag instructions appear only from help icon at 390.0"` and `... at 280.0`: both passed.

### Remaining limitations
- The tooltip text is a single line that may wrap inside the 320 px tooltip; that behavior is unchanged.

### Safe practice exercise
1. Open `product_tag_input.dart` around line 10.
2. Change `Tap × to remove a tag.` to `Tap the × icon to remove it.`
3. Run the two `tag instructions` tests above; they should still pass because they compare against the constant.
4. Change it back.

---

## Add Product: Low Stock Threshold Help Icon Sits Next to Its Label

### Cause (confirmed)
- `ProductInventoryInfo` uses a 48x48 `IconButton` for its accessible tap target, but the icon was centered inside that box. In the `_label` row (`Flexible(label)`, `SizedBox(width: 4)`, `labelAction`), the glyph therefore appeared about 15 px farther from the label than the Tags help icon, which already used `alignment: centerStart` and `padding: zero`.

### Exact file changed
- [campushub/lib/module_app/widgets/seller/product_inventory_fields.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/widgets/seller/product_inventory_fields.dart#L172-L181): the `IconButton` now has `padding: EdgeInsets.zero` and `alignment: AlignmentDirectional.centerStart`.

### How it works
1. The `IconButton` keeps its `BoxConstraints(minWidth: 48, minHeight: 48)` tap target, so accessibility is unchanged.
2. `alignment: centerStart` places the 18 px info glyph at the left edge of the 48 px box, directly after the label's 4 px gap.
3. The same widget is used by Batch Tracking and Low Stock Threshold, so both help icons now align consistently.

### Backend / API behavior
- Unchanged. The tooltip content and the threshold value sent to `POST /api/seller/products/submit/` are untouched.

### Database / migration impact
- None.

### Tests performed
- `flutter analyze lib/module_app/widgets/seller/product_inventory_fields.dart`: no issues.
- `flutter test test/seller_add_product_page_test.dart --plain-name "four active sections, left progress and right label fit 390.0/844.0/1.0"`: passed.
- `flutter test test/seller_add_product_page_test.dart --plain-name "concise batch tooltip supports tap, long press, hover and outside dismissal at 390.0"`: passed.
- The earlier 280/2x failures came from the ongoing Inter-font test migration; the test harness now loads `assets/fonts/inter/InterVariable.ttf`, and the full `seller_add_product_page_test.dart` suite passes 36/36.

### Remaining limitations
- The visual gap still includes the label's existing 4 px `SizedBox`; reducing it further would make the icon touch the text. The 48 dp tap target is intentionally kept.
- Not yet checked on a physical phone.

### Safe practice exercise
1. Open `product_inventory_fields.dart` around line 172.
2. Change `alignment: AlignmentDirectional.centerStart` to `AlignmentDirectional.center`.
3. Run the two tests above and inspect `step-2-390.png`; the Low Stock Threshold icon will move back to the middle of its 48 px box, increasing the visible gap.
4. Change it back to `centerStart`.

---

## Add Product: Stock Method Help Icons Sit Beside Their Titles

### Cause (confirmed)
- The Standard Stock and Batch Tracking help icons were painted by a `PositionedDirectional` at the card's right edge (`end: ProductFormStyle.gap`), so the icon appeared far from the title even though the title was on the left. The body text also had to reserve `end: ProductFormStyle.target` to avoid overlapping the floating icon.

### Exact files changed
- [campushub/lib/module_app/widgets/seller/product_inventory_fields.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/widgets/seller/product_inventory_fields.dart#L199-L295): replaced the `Stack`/`PositionedDirectional` overlay with a title `Row` containing the title and `ProductInventoryInfo`; removed the `end` reservation on the description; updated the two tooltip constants.
- [campushub/test/seller_add_product_page_test.dart](file:///c:/Users/leste/Desktop/CAMPUSHUB/campushub/test/seller_add_product_page_test.dart#L704-L721): updated geometry assertions to expect the icon immediately after the title, and loaded the Inter font in `setUpAll`.
- [docs/mobile-seller-application.md](file:///c:/Users/leste/Desktop/CAMPUSHUB/docs/mobile-seller-application.md): this guide.

### Changes made
- Standard Stock tooltip now reads `Enter the total number of items you have available.`
- Batch Tracking tooltip now reads `Keep track of your stock each time you add new items. Older stock is sold first.`
- The info icon for each method now renders directly after its title (`Batch Tracking ⓘ`) instead of at the card's far right.
- The 48x48 tap target is unchanged; the title row is 48 px tall so the icon still has a full accessible target.
- The description no longer reserves 48 px of trailing space, so wrapped copy uses the full card width.

### How it works
1. Each method card lays out `Radio` + 8 px + `Expanded(Column)`.
2. The Column's first child is now `Row(Flexible(title), SizedBox(4), ProductInventoryInfo)`.
3. `Flexible` lets long titles wrap at 280 px / 2x without overflowing.
4. `ProductInventoryInfo` still uses the same tooltip, `TapRegion`, and 48 dp `IconButton`, so tap, long-press, hover, and outside-dismiss behavior are unchanged.

### Backend / API behavior
- Unchanged. The stock method value and submit payload are untouched.

### Database / migration impact
- None.

### Tests performed
- `flutter analyze lib/module_app/widgets/seller/product_inventory_fields.dart test/seller_add_product_page_test.dart`: no issues.
- `flutter test test/seller_add_product_page_test.dart --plain-name "stock cards align content and select through the card at 390.0/1.0"`: passed.
- `flutter test test/seller_add_product_page_test.dart --plain-name "stock cards align content and select through the card at 280.0/2.0"`: passed.
- Full `flutter test test/seller_add_product_page_test.dart`: 36/36 passed.
- Rendered `step-2-390.png` and `batch-tooltip-390.png` confirm the icon sits beside each title and the tooltip shows the new copy.

### Remaining limitations
- The title row is 48 px tall to preserve the tap target, so each card is slightly taller than before.
- Not yet checked on a physical phone.

### Safe practice exercise
1. Open `product_inventory_fields.dart` around line 250.
2. Change `const SizedBox(width: 4)` between the title and the info icon to `const SizedBox(width: 16)`.
3. Run the stock-card tests above and inspect `step-2-390.png`; the icon moves 12 px farther from the title.
4. Change it back to `4`.



---

## Add Product Form: Renamed Available Quantity to Available Stock

### Cause (confirmed)
- In the Add Product form, the standard stock field previously displayed the label `'Available Quantity *'` and the placeholder `'Enter available quantity'`, and the final review step displayed `'Total Available Quantity'`.
- Per user instruction and institutional inventory standards, this was renamed to `'Available Stock *'` and `'Enter available stock'`, harmonizing terminology across the mobile seller form and the web admin product modal (which previously used `'Stock Quantity'`).

### Exact files changed
- [campushub/lib/module_app/screens/seller_add_product_page.dart](file:///C:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/seller_add_product_page.dart#L987-L1685):
  - Line 987: Updated review label `_reviewValue('Total Available Stock', '$total units')`.
  - Line 1674: Updated field label `_label('Available Stock *', ...)`.
  - Line 1682: Updated field input decoration `_decoration('Enter available stock')`.
- [backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html](file:///C:/Users/leste/Desktop/CAMPUSHUB/backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html#L391):
  - Line 391: Updated form label `<label for="productStock" class="form-label">Available Stock <span class="required-asterisk">*</span></label>`.

### Changes made
1. Replaced `'Available Quantity *'` with `'Available Stock *'` on the standard stock field in `seller_add_product_page.dart`.
2. Replaced the input placeholder `'Enter available quantity'` with `'Enter available stock'`.
3. Replaced `'Total Available Quantity'` with `'Total Available Stock'` in the review step (Step 4) of `seller_add_product_page.dart`.
4. Replaced `'Stock Quantity'` with `'Available Stock'` in the web admin Add Product modal form (`admin_products.html`) for cross-platform alignment.

### How it works
- **Mobile Seller Flow**: In Step 2 (Pricing & Inventory), when the user selects "Standard Stock" (`_inventoryMethod == 'simple'`), the field label displays `Available Stock *` with hint text `Enter available stock`. When reaching Step 4 (Review), the summary row displays `Total Available Stock` alongside the formatted count (e.g. `10 units`).
- **Web Admin Flow**: When administrators open the Add Product modal, section 3 ("Pricing & Inventory") displays the field label `Available Stock *` matching the helper description directly underneath ("You will be alerted when available stock reaches this amount or lower.").
- All backend keys (`stock`), validation rules, API endpoints (`/api/seller/products/submit/`), and form controllers (`_quantity`) remain unchanged.

### Backend / API behavior
- Unchanged. The payload continues sending the parsed integer under `'stock'`.

### Database / migration impact
- None. No models, tables, columns, or migrations were touched.

### Tests performed
- `flutter test test/seller_add_product_page_test.dart`: 50/50 tests passed in 25s.
- `python manage.py test modules.marketplace.tests`: 29/29 tests passed in 19.8s.

### Remaining limitations
- Mobile batch tracking (FIFO) uses individual `'Batch Quantity *'` fields for each restock lot, while standard stock uses `'Available Stock *'`. This distinction is intentional and accurately reflects batch inventory semantics.

### Safe practice exercise
1. Open `campushub/lib/module_app/screens/seller_add_product_page.dart` around line 1674.
2. Locate the `_label('Available Stock *', ...)` widget anchor.
3. Verify that the label and hint string `'Enter available stock'` are properly synchronized.
4. Run `flutter test test/seller_add_product_page_test.dart` from the `campushub` folder to verify that widget keys and form flow remain intact.
