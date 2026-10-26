# Flutter mobile Services tab and live catalog

Updated October19,2026. Regular-user navigation remains Home | Marketplace | Services | Facilities | Profile. Approved sellers retain their existing Add Product center action.

## Banner swipe, centered dots and compact gradient action - October 19, 2026

This follow-up supersedes the earlier visible Previous/Next/Pause controls and IndexedStack described below. The user's explicit request permits a gradient on this banner button; the photograph retains its solid navy tint.

### 1. Cause / reason

The user requested centered dots instead of arrows/playback controls, a real automatic swipe, a slightly taller photo and a smaller button at the lower left with a smooth gradient. The earlier implementation changed IndexedStack pages instantly and displayed a count plus three icon buttons.

### 2. Exact files, current lines and anchors

| File | Current line / anchor | What changed |
|---|---|---|
| `campushub/lib/module_app/widgets/home/campus_home_banners.dart` |49 `_slideDuration`,61 `_buttonGradient`,104 `_schedule`,134 `_move`,159 `_bannerHeight`,187 `_action`,292 `PageView.builder`,302 indicator Semantics | Native horizontal swipe, centered dots, stable taller layout and compact lower-left gradient button. |
| `campushub/test/campus_home_banners_test.dart` |47 rotation test,57 banner/button bounds,82 fractional page position,101 lifecycle/actions test,151 narrow/large-text cases | Verify a real animated transition, looping, dots, button position, retained48dp hit area, manual swipes, accessibility pause, lifecycle and destinations. |
| `campushub/test/dashboard_search_appbar_test.dart` |27 `final tabs` | Select the outer PageView in the existing test; the nested banner may swipe while bottom-navigation tabs retain NeverScrollableScrollPhysics. |
| `docs/mobile-services-navigation.md`, `campushub/DESIGN.md`, `CAMPUSHUB_CONTEXT.md` |this section / campus-home-banner / latest entry | Record current presentation, functions/data flow, user-authorized gradient exception, checks and safe practice. |

The photo, banner wording, Home placement, seller KPI/filter logic, backend and API are unchanged.

### 3. Changes made / expected UI

The photo now slides horizontally every five seconds using a450ms easeInOutCubic transition. Three small dots stay centered beneath it, with the current dot gold and outlined in navy. Remove the visible counter, arrow buttons and Play/Pause buttons. Users can also swipe just the banner. The button is anchored at the lower left: its gold-to-soft-gold background is visually34dp tall, with readable navy12sp text and a full48dp touch area. This uses only the existing gold/white/navy palette. Reserve24dp additional photo space and a minimum188dp card height, growing for larger text. No extra shadows or decorative panels.

### 4. Functions, inputs/outputs and data flow

The same `CampusHomeBanners` inputs remain the three tab callbacks and `active`. `_schedule()` owns the existing five-second timer. It now calls `_move(1)`, which animates the dedicated PageController to the next physical page. `onPageChanged` updates `_page`; `_page % 3` identifies the visible copy and dot. The builder starts at a multiple of three, lazily constructing nearby pages so forward looping and backward manual swipes work without reversing the last-to-first animation. Example: five seconds -> swipe Marketplace to Facilities -> second dot selected -> View Facilities calls the unchanged Home callback for tab3.

`_bannerHeight(context, width)` measures the longest slide text with the current Poppins style/text scaler, reserving padding, button target and extra photo space. Each page uses Spacer above `_action(index)` so the button stays at the same lower-left position across different messages. `_action` paints a small gradient plate behind an existing semantic TextButton; the entire48dp button remains tappable. The background image is still the same local asset and decoded-width limit.

Manual drag cancels the timer until scrolling ends, then starts a fresh interval. Background/inactive Home, focus, hover, covering routes and reduced motion retain their existing pause behavior. Reduced motion also uses an instant manual page change for accessibility actions. The passive dots expose current/next/previous values and a screen-reader Pause/Resume action without adding visible playback buttons. `dispose()` releases the PageController, timer and lifecycle observer.

### 5. Backend / API behavior

Unchanged. The three buttons reuse the existing Marketplace/Facilities/Services tab callbacks. No additional requests, product records, sales calculations, seller permissions or catalog behavior.

### 6. Database / migration / running app

No migration, model, dependency or asset change. No app/phone/backend/worker launch, reload, restart, APK build or installation was performed; the user retains control of Ctrl+F5.

### 7. Verification results

All22 focused Flutter tests passed:9 in campus_home_banners_test/home_page_test and13 in dashboard_search_appbar_test/seller_home_entry_test. Three-file analysis returned No issues found; formatting passed. The tests confirm movement through a fractional PageController position halfway through the transition, looping, dot alignment/selection, lower-left button geometry,48dp target, manual swipe destinations, reduced motion, lifecycle,320dp at1x/2x, existing Home dark/landscape cases and retained regular tabs/search/seller approval behavior. The first verification exposed a missing explicit semantics import and Flutter's requirement for next/previous values on adjustable controls; both were corrected before the passing run. No backend tests rerun for this presentation-only follow-up.

Native production-widget previews inspected: `scratch/mobile-home-banners/swipe-dots/banner-320-1.0.png`, `banner-320-2.0.png`, `shared-home-seller-sections.png`. Checked centered dots, exact photo crop, readable text wrapping, compact gradient/button alignment and clearance from header/bottom navigation. The data in the full-Home preview is isolated fixture data. Existing peso-font fallback in the test renderer is outside this change. Verification commands: `flutter analyze --no-pub lib/module_app/widgets/home/campus_home_banners.dart test/campus_home_banners_test.dart test/dashboard_search_appbar_test.dart`; `flutter test --no-pub test/campus_home_banners_test.dart test/home_page_test.dart`; `flutter test --no-pub test/dashboard_search_appbar_test.dart test/seller_home_entry_test.dart`. There is no browser URL: this is native Flutter widget rendering, preserving the user's instruction not to run/restart the app.

### 8. Troubleshooting, limitations and safe practice

No new physical-phone/browser run or platform screen-reader test. Dots are position indicators, with manual navigation available through swiping and accessibility actions. Automatic rotation intentionally stops under reduced motion or when Home is inactive. The local Flutter skill searches returned no verified animation-specific match; the implementation uses native PageView and existing app tokens as the fallback, tested directly.

Safe exercise: from `campushub`, run `flutter test --no-pub test/campus_home_banners_test.dart test/dashboard_search_appbar_test.dart`. Confirm the first banner stays for four seconds, begins sliding at five, reaches the second dot, and loops after the third. Manually swipe the banner and confirm the regular selected bottom tab remains Home. To learn animation timing, temporarily change `_slideDuration`450ms to600ms, inspect the transition, then restore450ms and rerun the tests. Do not change the five-second timer or launch the user's running app to perform the isolated tests; mocks/callbacks write no live records.

## Campus photo banners below Welcome - October 19, 2026

### 1. Cause / reason

The user supplied the USTP Oroquieta Campus Entrance photo and three exact promotional messages, asking for banners below Welcome that switch every five seconds. Inspection confirmed that Home already receives working callbacks for Marketplace, Facilities and Services; no new route, catalog API or fabricated listing is needed. The associated visible Daily/Weekly/Monthly sales selector is documented in the newest section of `docs/mobile-seller-application.md`.

### 2. Exact files, current lines and anchors

| File | Current line / anchor | Change / reason |
|---|---|---|
| `campushub/lib/module_app/widgets/home/campus_home_banners.dart` |10 `CampusHomeBanners`,28 `_slides`,78 `_schedule`,90 five-second timer,134 white Material,160 `IndexedStack` | One reusable banner widget containing the requested copy, supplied photo, existing tab callbacks, controls and lifecycle handling. |
| `campushub/lib/module_app/screens/home_page.dart` |35 `active`,214 `CampusHomeBanners` | Insert directly after Welcome, before seller sections and the normal catalogs. Pass the existing three navigation callbacks. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` |438 `active: _currentIndex == 0` | Tell the existing Home when its bottom tab is visible, so hidden Home does not rotate. |
| `campushub/assets/img/ustp_oroquieta_entrance.png` |Bundled photo | Copy the supplied `Downloads/USTP Oroquieta Campus Entrance.png` unchanged. File hashes match. Existing pubspec assets/img directory registration includes it. |
| `campushub/test/campus_home_banners_test.dart` |47 rotation,72 pause/lifecycle/actions,106 narrow/large-text layout | New meaningful timer/lifecycle/action/reduced-motion checks and optional rendered previews. |
| `campushub/test/home_page_test.dart` |56 banner-placement assertion | Existing Home tests now verify the banner is below Welcome, retaining catalog loads/search/error states. |
| `campushub/test/seller_home_entry_test.dart` |`workspace`, approved-Home renderer | Mock the requested period correctly; load actual Poppins/Iconsax fonts and precache the banner photo for the existing full-Home preview. |
| `docs/mobile-services-navigation.md`, `campushub/DESIGN.md`, `CAMPUSHUB_CONTEXT.md` |this section / component specification / latest entry | Record implementation, design, verification and safe practice. |

Other changed selector/backend files are listed in `docs/mobile-seller-application.md`; no unrelated sidebar or product-form source was changed.

### 3. Changes made / expected UI

All Home users see the three banners in order: Shop on Campus / Browse Products; Explore Campus Facilities / View Facilities; Campus Services Made Easy / View Services. The descriptions are exactly those provided by the user. Each uses the same real campus photograph with a solid navy tint, white Poppins text and a gold button; no gradient or stock image. Below the photo are the current slide count, Previous, Next and Pause/Play controls. Approved sellers still see Sales Overview beneath the banners and retain their normal navigation/catalogs.

### 4. Functions, inputs/outputs and data flow

`CampusHomeBanners` takes `onMarketplace`, `onFacilities`, `onServices` and `active`, and returns the banner/control UI. `_slides` stores only the user-authored promotional copy, not products, availability, sales or recommendations. `_open(index)` calls the corresponding existing Home callback. Example: Browse Products -> Home.onMarketplace -> DashboardScreen._goToTab(1); Facilities uses tab3 and Services tab2. Existing seller Add Product navigation remains separate.

`_schedule()` cancels any previous timer, then starts one five-second periodic timer when allowed. It pauses for inactive Home, background lifecycle, keyboard focus, pointer hover, a covering route, disabled ticker or reduced-motion preference. Each tick skips content changes when the banner is outside the screen. `_move(step)` provides manual wraparound and resets the interval; Pause/Play controls explicit playback. `dispose()` cancels the timer and removes the lifecycle observer. The IndexedStack sizes to the tallest slide, avoiding vertical jumps and allowing larger text to grow naturally. The photo is a local asset decoded at a bounded1280px width, not fetched from the network. Its neutral fallback retains readable copy/actions if loading fails.

### 5. Backend / API behavior

Banners call no new API and write no records. They open the existing catalog tabs, whose existing real-data eligibility, permissions and loading/errors remain authoritative. This is promotional navigation, not a claim that a particular product, service or reservation slot is available.

### 6. Database / migration / running app

No migration, model, package or pubspec change. The supplied photo is the only new production asset. No phone/app/backend/worker launch, reload, restart, APK build or installation was performed; the user retains control of Ctrl+F5.

### 7. Verification results

Nine-file scoped Flutter analysis returned No issues found. All37 focused tests passed across campus_home_banners_test, home_page_test, seller_workspace_test, seller_home_entry_test, dashboard_header_test and dashboard_search_appbar_test. Coverage includes exact five-second cycling/wraparound, stable height, pause/resume, background/inactive Home, three callback destinations, reduced motion,320dp at1x/2x, placement below Welcome, retained authentication/seller gates/search/tab state. All23 isolated Django seller tests also passed; see the sales-selector guide for Philippine midnight/week/month boundaries. A final explicit white Material surface keeps the control row readable under dark device settings and the banner button minimum is48dp; all9 affected banner/Home tests passed again and final banner analysis was clean.

Visual review: `scratch/mobile-home-banners/banner-320-1.0.png`, `banner-320-2.0.png` and `shared-home-seller-sections.png`. The final full-Home render preloads actual fonts/photo; the first capture lacked that test preparation. Initial analysis/test compilation also exposed a test-only ResizeImage getter typo and three source lint findings; these were corrected before the final clean run. Fixture names/sales remain test-only. The existing renderer's peso fallback glyph is outside this banner change; no live monetary values were changed.

### 8. Troubleshooting / limitations / safe learning exercise

No new physical-phone test. With reduced motion enabled, banners stay manual; this is intentional. A paused or hidden banner also does not auto-advance. If the photo is missing, verify its exact asset path and existing assets/img registration; the original photo remains in Downloads. Do not change catalog APIs to fix an asset issue.

Safe exercise: from `campushub`, run `flutter test --no-pub test/campus_home_banners_test.dart`. Verify slide1 persists for four seconds, changes at five, reaches slide3 then loops; Pause stops it, and all three buttons call the expected tab callbacks. To learn the timing, temporarily change the timer from five to six seconds, observe the timing test fail, then restore five and rerun. These tests use callbacks/fixtures and create no live records. When ready to inspect the running source, confirm the same banners appear between Welcome and Sales Overview without changing the regular bottom navigation.

## Header Search and Notifications swapped - October 19, 2026

1. **Cause / reason:** the user requested swapping the two existing header icons. The previous order was Notifications then Search.
2. **Exact files / current anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:235,298` `HeaderSearchButton` in Messages/shared header; `campushub/lib/module_app/screens/seller_dashboard_page.dart:286` seller-header `HeaderSearchButton`; `campushub/test/dashboard_header_test.dart:110` `searchButton` geometry; `campushub/test/seller_workspace_test.dart:305` header order assertion; this guide and `CAMPUSHUB_CONTEXT.md` latest note.
3. **Changes made:** place Search first and Notifications at the far right in all three existing headers. Keep their current icons, tooltips, sizes, white/SugarPie styling and actions.
4. **How it works:** reorder existing children in the header Row and AppBar.actions lists. Inputs are the same `_openSearch`, `_openNotifications` and seller callbacks; outputs remain the existing Search route and notification panel. Example: tapping the left action opens Search; tapping the right bell opens Notifications. No new state, routes or copied handlers.
5. **Backend / API behavior:** unchanged; existing search/catalog and notification flows remain.
6. **Database / migration impact:** none. No app/device launch, reload, restart, build or installation performed.
7. **Tests performed:** five-file analysis clean; all26 tests in dashboard_header_test, seller_workspace_test and seller_home_entry_test passed, including updated responsive non-overlap/order and existing action callbacks. Seller375dp fixture preview visually confirms Search left of Notifications. The associated Sales Overview filter follow-up is documented in mobile-seller-application.md.
8. **Troubleshooting / limitations / safe practice:** hot reload when ready if the old order remains. No native phone check for this source-only swap. Run `flutter test --no-pub test/dashboard_header_test.dart`; verify the brand ends before Search, Search ends before the bell and the bell retains its48dp target at320dp/2x text. This uses fixtures and writes no records.

## Search replaces the header profile action — October19,2026

This supersedes the historical below-greeting Search placement described later in this guide.

### 1. Cause / reason

The user requested removing Profile from the shared mobile header and moving Search into that position. Before this change, the shared Home, Messages and seller-tool headers used HeaderProfileButton, while the read-only catalog search entry lived below the Home greeting. Removing the header avatar also needed to preserve sellers' existing access to their personal profile.

### 2. Exact files, current lines and nearby anchors

| File | Line / anchor | What changed and why |
|---|---|---|
| `campushub/lib/module_app/widgets/navigation/header_search_button.dart` |8 `HeaderSearchButton` | Shared compact Iconsax Search action with a48dp minimum touch target, navy icon and Search tooltip; default opens the existing SearchPage. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` |69 `_homeKey`,160 `_openSearch`,213 `onSearch`,240 and307 `HeaderSearchButton`,337 drawer `onProfile`,437 keyed HomePage | Replace header Profile in the regular shell and Messages; connect seller tools to the same Search handler; keep cached catalog reuse and a working fallback before Home is mounted. Drawer avatar opens the existing Profile tab. |
| `campushub/lib/module_app/screens/home_page.dart` |48 `HomePageState`,108 `openSearch`,194 `home-scroll` | Expose the existing cached Search navigation to the shell and remove the search TextField below the greeting. Catalog loaders, previews, refresh, sorting and error states remain. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` |27 `onSearch`,139 `_openProfile`,254 drawer `onProfile`,288 `HeaderSearchButton` | Seller-tool header uses Search, retains white SugarPie branding and bell, and moves the existing profile callback to the drawer avatar. |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` |65 `onProfile`,193 avatar IconButton | Existing identity avatar becomes a56dp Profile action; no new menu row or duplicate Profile screen. |
| `campushub/test/dashboard_header_test.dart` |15 responsive cases,99 Search expectations | Header geometry, no header Profile, five widths/scales and optional headless captures with bundled Poppins/SugarPie/Iconsax fonts. |
| `campushub/test/dashboard_search_appbar_test.dart` |55 header Search tap,104 direct-tab regression | Existing tab/drawer/search return test updated; new regression checks Search before Home has been visited. |
| `campushub/test/home_page_test.dart` |19 section layout,121 cached openSearch | Verify no duplicate Home input while retaining sections/data and cached Search/autofocus/query/Back behavior. |
| `campushub/test/home_card_background_test.dart` |29 removed search assertion | Keep the existing surface test aligned with the new location. |
| `campushub/test/seller_workspace_test.dart` |285 `onSearch`,310 Search tap,372 persistent header,699 and755 drawer-avatar visibility | Preserve seller sections, header callbacks, drawer Profile return, center Add Product and retained regular Home navigation. |
| `docs/mobile-services-navigation.md`, `CAMPUSHUB_CONTEXT.md` |this section / latest header entry | Record current behavior, functions/data flow, verification and limitations. |

### 3. Changes made / expected behavior

The white shared header is now menu/back, the existing CampusHub SugarPie wordmark, a compact outlined Search icon, and Notifications at the far right (latest icon-swap follow-up). The header Profile avatar is removed from the regular shell, seller tools and Messages. The search input below the Home welcome is removed, making the catalog/seller content begin sooner. Tapping Search opens the current dedicated Search page with its full input automatically focused. Navy/gold#FCB315/white styling, labels, notifications, bottom navigation and seller data remain intact.

Profile stays reachable: regular users retain the Profile bottom tab and drawer entry; approved sellers tap their existing seller-drawer avatar. Its current identity information and menu structure remain. This reuses the existing root Profile page rather than introducing another account screen.

### 4. How it works / functions, inputs and outputs

`HeaderSearchButton(onPressed?)` renders a native IconButton. With a supplied callback it delegates to the shell; without one, a standalone seller page pushes the existing SearchPage. It owns no query state and makes no API call itself. Its tooltip supplies an accessible name; touch bounds stay at least48dp even though the icon is smaller.

`_DashboardScreenState._openSearch()` checks the keyed HomePageState. If Home is mounted, `HomePageState.openSearch()` passes Home's existing products/facilities/services futures and loaders to SearchPage, preserving loaded data and avoiding another catalog read. If a direct launch starts at another retained tab before Home is built, the handler opens the same SearchPage with the shell's existing injected loaders/catalog; the button is never silently inactive.

The seller-tool page receives that same `_openSearch` callback from the root shell. Search is pushed over the current route, so Back returns to the same seller tool/tab. The Messages header uses the same callback. SearchPage still owns its own input, matching, recommendations, filters, loading/errors and detail navigation; none of that business logic was copied into a header.

`SellerDrawer.onProfile` is a navigation callback only. The root closes the drawer and selects its existing tab4. In a seller-tool page, `_openProfile()` closes the drawer and invokes the existing root Profile callback; standalone usage keeps its existing ProfilePage fallback. No sign-out or account/seller status change occurs.

Annotated example: after Home loads products once, tap the header Search and type a matching product name. Search receives the same product future, focuses the current Search input and shows the real matching record. Back returns to Home without replacing its retained state. Starting directly at Services uses the loader fallback and returns to Services after Back. Both paths are covered by isolated fixtures.

### 5. Backend / API behavior

Unchanged. Reuse current ProductService, FacilityService, ServiceCatalog and SearchPage recommendation/search behavior. No endpoint, permission, eligibility, recommendation algorithm, API payload or live record was changed. The injected-loader fallback only supplies existing catalog reads when no Home cache exists yet.

### 6. Database / migration / running app

No migration, dependency or database change. No APK build/install, phone operation, app launch, reload or restart was performed for this header update. The user's Ctrl+F5 session remains under their control; hot reload when ready to view these source changes.

### 7. Tests performed and results

-  Scoped Flutter analysis of five source and five updated test files: No issues found.
- 29 headless tests passed across dashboard_header_test, dashboard_search_appbar_test, home_page_test, home_card_background_test, seller_workspace_test, seller_drawer_test and dashboard_center_add_button_test.
-  Covered header Search/autofocus/query/Back, catalog reuse, Search before Home is mounted, retained tab navigation without swipes, regular five-tab navigation, approved seller Add Product, seller drawer Profile, unchanged shell and approval checks.
-  Header renders exercised320/375/390/844dp widths and2x text; Home also covers landscape and dark theme; seller tests cover320dp/landscape at2x text. Optional captured PNGs are in scratch/mobile-header-search. The375dp and320dp/2x header previews were visually inspected with bundled fonts. Images and product records in captures are isolated test fixtures, not live dashboard values.
-  The first run had25 passes and one failure while an existing Add Product heading changed during concurrent edits. Current files were preserved; the rerun against the current Information heading passed all29. No Add Product production code was changed by this task.

### 8. Troubleshooting, safe practice and limitations

If the old avatar or Home search remains visible, hot reload the current Flutter source when ready and confirm DashboardScreen uses HeaderSearchButton. The compact header control is a search icon; the full search input stays on SearchPage. Native keyboard/device presentation was not rerun for this source-only update. Existing fixture captures can show fallback product images or font glyph differences outside the header; they are not evidence of a new live catalog issue.

Safe exercise: run `flutter test --no-pub test/dashboard_search_appbar_test.dart test/home_page_test.dart` from campushub. Verify that Search works from a directly opened Services tab, auto-focuses the existing input, and Back restores Services. Then test from Home and confirm mocked product call count stays1. To practice icon sizing, temporarily set the header icon size to22 while retaining48dp constraints; verify no overflow at320dp, then restore. These tests use mocks and do not write records.

## Compact Home search and white Search background - October 18, 2026

1. **Cause / reason:** user requested removing the Home filter, a smaller search entry, and white Search/Profile backgrounds. Confirmed sources: Home's52dp search row and `_HomeFilter` controls; Search's explicit #F7F8FC Scaffold; Profile's shared light background token.
2. **Exact files / current anchors:** `campushub/lib/module_app/screens/home_page.dart:105` `_openSearch`,120 `_section`,209 `ConstrainedBox(minHeight: 48)`,224 `isDense`; `campushub/lib/module_app/screens/search_page.dart:332` `backgroundColor: Colors.white`; `campushub/lib/module_app/widgets/profile/profile_widgets.dart:8` `ProfileStyle.background`. Existing tests updated: `test/home_page_test.dart` compact search/all sections, `test/search_page_test.dart` discovery background, `test/profile_page_test.dart` Profile/Personal Information white surfaces. Documentation: this guide, `docs/mobile-profile.md`, `CAMPUSHUB_CONTEXT.md`, `campushub/DESIGN.md` search component and `campushub/.impeccable/design.json` search excerpt.
3. **Changes made:** remove Home-only filter enum/state/modal/button/Reset and conditional section visibility. All real Marketplace/Facilities/Services previews remain visible. Simplify `_section` to its actual loading/error/empty/data states because it no longer filters. Search now has48dp minimum height instead of52, a12sp hint,20dp icon and10dp vertical padding. Keep its pill outline, exact placeholder and below-welcome position. Search and shared Profile page backgrounds are white; Profile behavior is described in its existing guide. Submitted Search result category filters remain supported.
4. **How it works:** `HomePage.build(context)` renders greeting, compact read-only search entry and the three catalog sections. `_openSearch()` still passes the existing catalog futures/loaders to the same dedicated SearchPage. `_section<T>()` takes a title, future, navigation/retry callbacks, empty text and content builder; it returns loading, recoverable error, real empty state or catalog content. Removing the obsolete `matches` input eliminates dead Home-only filtering. SearchPage still matches typed queries and routes to existing details; only its Scaffold surface changed.
5. **Backend / API behavior:** unchanged. No additional calls per keystroke, recommendation algorithm changes, catalog visibility changes, seller/business changes or live writes.
6. **Database / migration impact:** none; no dependencies, migration, rebuilt APK or installation for this follow-up. Hot reload to see the updated source.
7. **Verification:** all31 targeted Home/Search/Profile/header/navigation widget tests passed. Six-file Dart analysis returned No issues found; scoped git diff --check passed. Log: `scratch/mobile-navbar/white-search-profile-tests.log`. Test-only fixtures remain isolated. An initial Profile background assertion expected an explicit Scaffold color, but detail pages inherit it from ProfileTheme; the assertion now checks the effective theme fallback correctly.
8. **Remaining limitations:** no new native screenshot/physical-phone run. Minimum height allows the entry to grow with large text; it is not clipped to48dp. White surfaces retain readable navy/gold content and thin neutral boundaries. This removes Home's filter control, not the Search page's existing result categories.

**Troubleshooting:** if the old button or gray surface persists, hot reload/restart the current Flutter build. Do not edit backend filters or catalog eligibility to change a visual surface. Profile details use `ProfileStyle.background`, not a separate color per page.

**Safe practice exercise:** temporarily change the search hint font from12 to13, preview at normal and2x system text, then restore12. Run `flutter test test/home_page_test.dart test/search_page_test.dart` and verify the same real search route still opens, all Home catalog headings remain and no filter button appears. This exercise does not write database records.

## Welcome text top spacing - October 18, 2026

1. **Cause / reason:** user approved reducing the Home top gap so the welcome sits higher below the shared header.
2. **Exact files / anchors:** `campushub/lib/module_app/screens/home_page.dart:276`, `EdgeInsets.fromLTRB(16, 8, 16, 32)` inside `HomePage.build`; this guide, `CAMPUSHUB_CONTEXT.md` latest note and `campushub/DESIGN.md` Layout paragraph.
3. **Changes made:** reduce only ListView top padding from20 to8 logical pixels; welcome and following Home content move12dp higher. Keep existing horizontal/bottom padding, font, section gaps and search below the welcome.
4. **How it works:** `HomePage.build(context)` receives the existing first name/catalog state and returns the same RefreshIndicator/ListView. `fromLTRB(left, top, right, bottom)` applies the four edge insets; the second input controls the space before the first welcome Text. This is layout only; catalog functions and routes do not change.
5. **Backend / API behavior:** unchanged; no new requests or data writes.
6. **Database / migration impact:** none. Hot reload to see the change; no new APK build or install for this small follow-up.
7. **Tests performed:** `dart analyze lib/module_app/screens/home_page.dart` returned No issues found; scoped `git diff --check` passed. No new tests for this reversible single-value spacing adjustment.
8. **Remaining limitations:** no new device/screenshot verification. If the greeting is scrolled away, return Home to the top before comparing.

**Debugging and safe practice:** if the old gap remains, verify the running source is home_page.dart and hot reload. Temporarily try a top inset of12, observe the welcome move4dp lower, then restore8. Confirm left/right margins and search still match their previous layout; this exercise changes no records.

## Notification bell left inset - October 18, 2026

1. **Cause / reason:** the user requested moving the bell left. The shared header's Expanded brand region previously pushed the button against the normal right padding. Interpreted as a small inset toward the wordmark, preserving the menu and brand order.
2. **Exact files / anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:265`, `SizedBox(width: 12)` immediately after the Notifications IconButton; `campushub/test/dashboard_header_test.dart:84`, `notificationButton`; `CAMPUSHUB_CONTEXT.md` latest note; this guide. DESIGN.md's header description also clarifies the existing Messages location.
3. **Changes made:** add 12 logical pixels of trailing space. The button moves left by 12dp, with its full 48dp target retained; no negative transform or overlap.
4. **How it works:** `_DashboardScreenState.build(context)` lays out menu, Expanded brand, Notifications and the new spacer in a Row. The spacer takes 12dp from the flexible brand region, leaving the button 16dp from the safe content edge (existing 4dp padding plus new 12dp). Pressing the same button still calls `_openNotifications()` and opens the same honest availability notice.
5. **Backend / API behavior:** unchanged; no new requests, data or notification feed.
6. **Database / migration impact:** none. Hot reload shows this layout-only change; no APK rebuild or installation was performed for this follow-up.
7. **Tests performed:** all3 header widget tests passed at320/390dp widths including2x text, and two-file Dart analysis returned No issues found. Log: `scratch/mobile-navbar/notification-inset-tests.log`. The first geometry assertion measured the inner Tooltip instead of the full IconButton; the finder was corrected to validate the actual touch target.
8. **Remaining limitations:** no new native screenshots/device run. This small inset does not move the bell to the far-left menu position. Other tabs share this same header.

**Debugging and safe practice:** if the bell does not move, hot reload the running app and confirm it is using this shared dashboard header. Do not reduce IconButton constraints to move only the artwork. For practice, temporarily change the spacer from12 to16, verify the button shifts4dp without overlap, then restore12 and run `flutter test test/dashboard_header_test.dart`. This modifies no database records.

## Dedicated catalog Search and header actions - October 18, 2026

### 1. Cause / reason

Confirmed: Home previously filtered its previews inline. The project has Navigator/PageController/retained tabs, not GetX, and no standalone catalog Search page or search-query popularity store. Existing TF-IDF recommendations use recorded product interactions but also fall back to general catalog products. That fallback must not be labeled personalized in Search. The latest instruction keeps Search below the greeting; it supersedes the earlier request to put Search in the header. The preceding request to simplify the header and improve the bell is retained: Messages remains accessible in drawer/Profile.

### 2. Exact files and current anchors

| File | Approximate current line and nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/search_page.dart` | 26 `SearchPage`; 73 `initState`; 93 `_submit`; 124 `_catalog`; 247 `_productContent`; 313 `build` | Dedicated Search, autofocus/Back, discovery, suggestions, submitted results and catalog filters; independent loading/errors/Retry. |
| `campushub/lib/module_app/screens/home_page.dart` | 116 `_openSearch`; 298 `home-search` | Read-only search entry below greeting opens Search with the already-loaded futures. Existing Home category filter and preview ordering remain. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 263 `LucideIcons.bell`; 103 `_openMessages` | Refined outlined bell, remove Messages from header only; existing drawer/Profile navigation and notifications behavior remain. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 108 `openMarketplaceProduct`; 150 `MarketplacePreviewCard` | Extract the existing details-navigation/tracking handler for reuse by suggestions; preserve existing cart/favorites/product details. |
| `campushub/lib/module_app/models/product_item.dart` | 27/96/122 `submittedAt` | Parse existing `submitted_at` for chronological recent-product sorting. |
| `campushub/lib/module_app/services/product_service.dart` | 110 `personalizedOnly`; 147 `fetchSearchRecommendations` | Opt into history-only results using existing session and recommendation endpoint. |
| `backend/core/modules/marketplace/services/recommendation.py` | 46 `get_recommended_products`; 106 `if personalized_only` | Optional flag returns no personal results when history/similarity is insufficient, preserving default legacy fallback. Explicit detail-page seed is ignored in this opt-in mode. |
| `backend/core/api/views.py` | 1746 `personalized_only` | Forward opt-in query flag to the same helper; no new endpoint. |
| `backend/core/api/test_search_recommendations.py` | `SearchRecommendationTests` | History/no-history, no-similarity, legacy fallback, opt-in endpoint and eligibility regressions. |
| `campushub/test/search_page_test.dart` | `openSearch`, `captureSearch`, `void main` | Search behavior, independent errors/retry, honest labels, details navigation and responsive layouts. Optional widget PNG capture uses isolated test fixtures only. |
| `campushub/test/home_page_test.dart` | `Home opens focused dedicated search` | Entry placement, autofocus, cached catalog reuse and return to Home; retain loading/filter tests. |
| `campushub/test/dashboard_header_test.dart` | `discovery header` | Updated header expectations and spacing. |
| `campushub/test/dashboard_search_appbar_test.dart` | `drawer routes` | Search entry/return plus retained tab/drawer regressions. |
| `campushub/test/dashboard_center_add_button_test.dart` | `retains Messages` | Messages via drawer, five unchanged tabs and no visible plus. |
| `campushub/DESIGN.md`, `campushub/.impeccable/design.json`, `CAMPUSHUB_CONTEXT.md`, this guide | `Dedicated Search`, `refersTo: search`, latest context note | Record current UI, sources and learning guide. |

### 3. Changes made

- Home retains the exact placeholder **Search products, facilities, services...** below the greeting, in the existing pill outline beside the Home filter. Tapping opens a full page with Back and a focused input.
- Empty input shows qualified **Recommended for You** or honest **Recently Added Products**, then **Explore Available Products**. Cards reuse real image/name/price/seller, favorites and cart behavior. Recent sorting uses saved submission timestamps, not sales. Missing dates sort last; no invented dates.
- Typing replaces discovery with compact query-matching product suggestions (image, name, price). Selecting a suggestion opens existing Product Details. Search all categories or keyboard Search submits the query; All/Products/Facilities/Services chips then filter the submitted results.
- Keep white Home/header, navy and mobile gold; only the requested Search page gets #F7F8FC background. Compact white rows/cards, Montserrat, no gradients/new dependencies.

### 4. Functions, inputs/outputs and data flow

`HomePage._openSearch()` takes the current loaded Product/Facility/Service futures and pushes `MaterialPageRoute(SearchPage(...))`. Search observes them without refetching on entry. For standalone use or Retry, injected loaders default to the existing catalog services. Failures are observed even if a section is hidden, avoiding unhandled asynchronous errors.

`SearchPage.initState()` stores those futures and starts an independent personal-recommendation read. `_matches(value)` compares a trimmed, case-insensitive query against real names and existing category/seller/description/location fields. Typing updates only local state; no HTTP request per character and no new search records. `_submit()` closes the keyboard and switches to result mode. Clearing restores discovery and focus. `_catalog<T>()` renders loading, load failure/Retry or the actual data, with failures independent per catalog.

`ProductService.fetchSearchRecommendations()` loads the current saved account ID and calls the existing `/api/products/recommended/?user_id=<id>&personalized_only=1` flow. The existing helper seeds similarity from the same ProductInteraction history (view/click/purchase). The server acknowledges `personalized_only: true` in its response; if an older server omits that acknowledgment, Flutter rejects the potentially generic list and uses recent products. Search intersects returned IDs with the current public product catalog before displaying cards. If none survive, history is missing, similarity is unavailable, or the existing client returns no recommendations on connection failure, show Recently Added Products. No interest fields, fake recommendations, popularity statistics, synthetic rows or duplicate recommendation algorithm are introduced. This update does not change Apriori bundles or seller dashboards.

`openMarketplaceProduct(context, product)` is the previous card handler moved into one shared function: load current session, record the existing view interaction when IDs exist, then push the existing ProductDetailsScreen with the same saved product fields. FacilityDetailsScreen and ServiceDetailsScreen remain the destinations for their result rows; service-specific guidance stays unchanged.

**Annotated example:** query `cho` checks `name.toLowerCase().contains('cho')` (as well as the existing other searchable product fields). A matching saved product becomes a suggestion, without creating a product. `personalized_only=1` stops before the helper's general popularity/catalog fallback; old callers omit this parameter and keep their original behavior.

### 5. Backend / API behavior

Reuse GET `/api/products/approved/`, GET `/api/facilities/?resource_type=facility`, GET `/api/mobile/services/` and existing GET `/api/products/recommended/`. Products remain subject to server approval/archive/expiry/availability eligibility. The Search page receives only this public catalog; recommended IDs are rejoined to it to exclude stale/unavailable results. Services remain active-only. Physical facilities keep existing catalog visibility/status rules, not invented free-slot promises. No Seller Dashboard, order, inventory, pricing, permission, authentication or transaction writes changed. Existing product view tracking is reused, not duplicated.

### 6. Database / migration impact

No model/schema change or migration. No live records created, edited or deleted by implementation/testing. `submitted_at` already exists in the product response. Restart Django if automatic reload is disabled so it recognizes the optional recommendation flag, and rebuild/restart Flutter to install the new screen. Normal debug APK: `campushub/build/app/outputs/flutter-apk/app-debug.apk` (not automatically installed on the phone).

### 7. Verification and manual testing

- **37 Flutter tests passed** across Search, Home, header, drawer/tab navigation, five-item navbar, ProductItem and Services. **7 Django tests passed** for the opt-in helper/API and existing recommendation endpoint. Initial retry callback failure was corrected with synchronous setState block callbacks; lazy-list checks now scroll before finding offscreen sections. No claim that the first test run passed.
- Targeted **11-file Dart analysis: No issues found**. Normal `flutter build apk --debug --target lib/main.dart` succeeded; Gradle 18.4 seconds. Logs: `scratch/mobile-navbar/search-flutter-tests.log`, `search-django-tests.log`, `search-main-build.log`.
- Three additional screenshot/layout checks passed after the final visual refinements. Layout widget checks cover 375x812, 320x844 at 2x text under dark app theme, 844x390 landscape at 2x text, reduced motion and scrolling. This Search surface intentionally remains light/navy in both theme settings. Optional fixture-only PNGs for discovery/suggestions are saved in `scratch/mobile-search/`; the phone-size discovery/suggestions and 2x-text portrait images were inspected. The initial capture used the square test font; the capture helper now preloads the bundled typeface before building. These are widget renders, not native keyboard screenshots.

Manual checks:

1. Open Home: greeting is above search; no header search. Tap search and confirm Back plus focused input/keyboard. Back returns to unchanged Home/tab state.
2. With a real public catalog, verify images/names/prices/sellers. With no interaction history, verify Recently Added Products and no Popular Searches. With qualifying existing history, verify Recommended for You contains only currently available approved records.
3. Type part of an actual product name: discovery disappears and matching suggestions appear. Tap one and check existing Product Details/cart/favorites behavior.
4. Submit an actual facility/service term using keyboard Search or Search all categories. Switch all four filters and verify real results; open Facility/Service Details. Services retain their own workflow guidance.
5. Try a term absent from the catalogs. Expect explicit no-match text. Disconnect Django and retry a failed catalog; expect error then recovery, while other successful catalogs remain usable. Clear search to restore discovery.
6. Test small phone, landscape, 2x text, keyboard open, screen reader Back/Clear/filters and returning from details. No real purchase/application is needed.

### 8. Limitations, debugging and practice

- Local matching covers the fetched public catalogs. There is no new paginated/server full-text/fuzzy search; large catalogs may eventually need that extension. Existing APIs remain authoritative and are reused.
- Popular Searches is intentionally omitted: no recorded search-popularity source was found. A purchase/interest model was not invented. Personalization uses the existing interaction helper only; missing/ineligible seeds or unavailable similarity produce recent products instead.
- No real phone keyboard/network/personalized-account flow was exercised in this change. Widget fixtures never enter production. Optional widget images do not prove native keyboard behavior.
- If products cannot load, inspect the existing approved-products request/connection and use Retry, not fabricated rows. If personalization is unexpectedly absent, check saved account ID, existing ProductInteraction rows, scikit-learn availability and matching currently public product IDs. If recommendations remain absent against an older server, deploy/reload the updated opt-in backend; the client safely rejects responses without the history-only acknowledgment.

**Safe practice exercise:** add a temporary test-only product with a distinctive name and saved submission timestamp in `search_page_test.dart`, then type part of that name. Verify suggestions contain that record, nonmatches are absent and Clear restores discovery. Restore the fixture and run `flutter test test/search_page_test.dart test/home_page_test.dart`. Do not add demonstration products to the live database.

## Full-width bottom navigation and navy tap feedback - October 18, 2026

This follow-up supersedes the floating geometry and gold feedback described in the earlier reference implementation below.

1. **Cause / reason:** the user requested that the bar fill the bottom, left and right edges and remove the light-yellow click color. Confirmed sources were the outside padding/maximum-width floating wrapper and gold default selection feedback.
2. **Exact files / current anchors:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart:51` (`selectionColor` default), line211 (`splashColor`), line213 (`focusColor`), line343 (`floating-navbar-pill`), line350 (`SafeArea`). `campushub/test/floating_bottom_navbar_test.dart:181` (`pillFinder`) checks edge alignment and line190 checks navy feedback. `campushub/DESIGN.md:68` (`bottom-navigation`), `campushub/.impeccable/design.json` (`refersTo: bottom-navigation`), `CAMPUSHUB_CONTEXT.md:3` and this guide record the current design.
3. **Changes made:** removed outside insets, width cap, rounded floating corners and shadow. The white surface fills the viewport width and bottom safe area, with a thin top separator. Replaced yellow press/focus colors with translucent navy. Kept labels, icons and selection animation.
4. **How it works / data flow:** `build(context)` receives the selected index, items and callback from the existing dashboard. It builds a full-width white Container, then SafeArea around the controls. SafeArea keeps controls above system gestures while the outer white surface reaches the bottom. `_buildNavItem(context, index, item)` derives selected appearance and invokes the existing `onTap(index)` callback. Dashboard changes its existing tab state; no records are fetched by this widget. The existing reduced-motion behavior remains.
5. **Backend / API behavior:** unchanged. No new requests, endpoints, seller data, authentication or permissions.
6. **Database / migration impact:** none. No package installation or migration command is needed. Hot reload should show this widget-only adjustment; use the rebuilt APK for installation.
7. **Tests performed:** all **11** tests passed across `floating_bottom_navbar_test.dart`, `dashboard_center_add_button_test.dart` and `system_navigation_surface_test.dart`. Coverage includes five labels, selection, rapid interrupted animation, reduced motion, safe-area alignment at narrow/wide sizes, navy feedback, hidden plus and dashboard integration. `dart analyze` for the changed widget and test returned **No issues found**. Log: `scratch/mobile-navbar/docked-nav-tests.log`. `flutter build apk --debug --target lib/main.dart` succeeded (Gradle 27.2 seconds); output: `campushub/build/app/outputs/flutter-apk/app-debug.apk`, build log: `scratch/mobile-navbar/docked-main-build.log`. Scoped `git diff --check` reported no whitespace errors.
8. **Remaining limitations:** native device screenshots were not repeated for this small follow-up; the emulator screenshots in the earlier section show the earlier floating geometry. This does not install the APK on the physical phone. The public widget name and existing test key retain `floating` for compatibility, even though the surface is now flush.

**Troubleshooting:** if yellow feedback persists, check whether a caller explicitly supplies `selectionColor`; this change sets the default to navy. If old outer gaps persist after hot reload, restart the app and confirm the current build is installed. Do not change the OS gesture inset to zero: keep controls safely above it.

**Annotated example:** `selectionColor.withValues(alpha: 0.08)` means the navy input color supplies an 8%-opacity tap ripple; it does not change the selected tab or navigation callback. `SafeArea(top: false)` adds device clearance around the controls inside the painted surface.

**Safe practice exercise:** temporarily change ripple opacity from `0.08` to `0.06`, tap several destinations and observe only the feedback change. Restore `0.08`, then run `flutter test test/floating_bottom_navbar_test.dart`; verify all assertions pass and labels/tab order remain unchanged. This exercise changes no backend records.

## Floating navigation reference, refined icons and selection motion - October 18, 2026

1. **Cause / reason:** user supplied a white rounded floating-bar photo and requested refined icons/animation while explicitly preserving every existing label. The prior component was full-width with a top separator and immediate icon swaps. This is a scoped navigation refinement, not a new dashboard or routing system.
2. **Exact files/current anchors:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart:70`, default5Items; line179 `_buildNavItem`; line186 reduced-motion duration; line219 TweenAnimationBuilder; line255 AnimatedDefaultTextStyle; line330 adaptive height; line351 floating-navbar-pill. `campushub/test/floating_bottom_navbar_test.dart`, motion/rapid-interruption, icon pairs, contrast, labels/semantics, inset/width and safe-area assertions. `campushub/DESIGN.md` bottom-navigation component and overview; `campushub/.impeccable/design.json` bottom-navigation label excerpt; this guide and CAMPUSHUB_CONTEXT.md. QA-only `scratch/mobile-navbar/verify_reference_nav.py` exercises the existing `campushub/tool/qa/navbar_preview.dart` on emulator-5554; no application source imports that script/preview.
3. **Changes made:** a white floating surface,24dp reference-specific corner radius,12dp horizontal inset,8dp bottom gap above system safe area,68dp minimum content height and640dp maximum width. One restrained offset shadow replaces the top separator; no border/shadow stacking. Default labels remain exactly Home, Marketplace, Services, Facilities, Profile. Icons use consistent rounded Material outline/filled pairs: home, shopping bag, briefcase, campus building and person. Navy selected icon/text replaces the reference's purple to preserve CampusHub branding; gold remains pressed/focus feedback. No always-visible dot, extra pill or chart icon was added. Legacy reusable center-action code remains dormant and is not enabled on Dashboard.
4. **How it works / functions and data flow:** existing Dashboard currentIndex → FloatingBottomNavbar → _buildNavItem(index,item). onTap(index) still invokes the original parent callback/PageController immediately. The selected state chooses item.effectiveActiveIcon rather than the idle outline. TweenAnimationBuilder animates the icon2dp upward and to1.08x over220ms easeOutCubic; AnimatedSwitcher crossfades glyphs over140ms; label weight/color transitions share the220ms duration. Values retarget from their current position on a rapid tap; there is no idle animation, navigation delay or new animation package. Reduced Motion sets durations to zero and keeps the selected state legible. Outer bounds stay stable while only the icon transforms. Labels retain the existing Material-style noScaling convention, with complete names in scalable tooltips and selected/button semantics; FittedBox prevents a long Marketplace label from turning into an ellipsis on narrow phones.
5. **Backend/API behavior:** none changed. All five destinations, labels, order, tab state, saved session, seller permissions, existing Messages and Services routing remain. No network request or record is created by icon animation. No plus/FAB was restored. No new icon/font dependency; Material is already available and the existing Lucide plus helper is retained for compatibility.
6. **Database / migration / commands:** no migration or backend command. Hot reload can show the source change; install the final normal `campushub/build/app/outputs/flutter-apk/app-debug.apk` to update a separately installed app. Native QA used a copied fixture preview APK only on the emulator; the final standard output was rebuilt from lib/main.dart and is the normal app, not that fixture target. Physical phone app/data/settings were untouched by this navbar task.
7. **Tests / actual evidence:** `flutter test test/floating_bottom_navbar_test.dart test/dashboard_center_add_button_test.dart test/system_navigation_surface_test.dart test/services_screen_test.dart --reporter expanded` passed **19 tests**, log `scratch/mobile-navbar/reference-nav-tests.log`. Checks include exact labels, outline/filled glyphs, navy contrast, one selected accessible destination, instant reduced-motion state,48dp touch height, body clearance,320/390/768px widths, dark host, large text, rapid interrupted selection, Services state retention and dormant center-action compatibility. Two-file targeted Dart analysis reported No issues found. Preview APK build passed; final main.dart APK build passed (23.3s Gradle task), log `reference-main-build.log`. **Nine Pixel10a Android emulator scenes passed:** all five selected destinations, dark Services, dark/2x-text Services, successive Marketplace→Profile taps, and landscape/large Profile. UI Automator verified unchanged labels and exactly one selected clickable destination in each scene. PNG/XML/JSON evidence is in `scratch/mobile-navbar/reference-native/`, with results in verification.json and reference-native-verification.log. Home, dark-large Services and landscape-large Profile images were visually inspected together for shape, spacing, contrast, glyphs, labels, selection and system-bar clearance. A cold-boot System UI busy dialog was dismissed with Wait before the capture batch; it was not an app crash or accepted screenshot. No UI defects were observed in that bounded pass; no further cosmetic iteration/rebuild was performed. The task-started headless emulator was closed afterward, rotation unlocked, and normal app APK output retained.
8. **Remaining limitations / debugging:** the supplied picture is the structural/icon reference, not permission to rename tabs or use purple. Profile/campus records and routes stay existing. Desktop-style animations, decorative artwork, gradients and physics libraries do not belong in this small Operate surface. Icon glyphs are from the included Material family, not a paid external asset set. Current nav labels keep existing native fixed-size behavior while full accessibility names remain. No native iPhone/tablet hardware or live account workflow was tested for this UI-only change. Old app installations require the rebuilt APK. Earlier sections below describe historical navbar appearances and are superseded here.

**Skills and rationale:** ui-ux-pro-max's two narrowly scoped motion searches returned no database matches; motion guidance therefore comes from the supplied Impeccable Android/animate playbooks and existing Flutter primitives, not a claimed search result. Frontend-design-codex and design-taste-frontend preserve-brand guidance informed the compact typography/spacing and restrained state feedback. An existing brand and explicit photo dictated the answer, so no generated image, marketing layout, React dependency or alternate label was introduced.

**Annotated example:** tapping Services still sends index2 to the parent. Its existing page is selected immediately; the briefcase fills/navy label strengthens while the icon travels2dp. Quickly tapping Profile retargets the transitions and ends with only Profile selected. Backend state is not involved.

**Safe learning exercise:** in floating_bottom_navbar_test.dart only, shorten the pump interval in the interrupted-selection test and verify the final selected semantics still match Profile and the bar rectangle stays unchanged. Restore your test edit and rerun the file. Follow currentIndex → isSelected → tween end → Transform in the production source to understand why the bar itself does not jump. Never rename a production tab to mimic the sample photo.

## Preview import diagnostics fix - October 18, 2026

1. **Cause / reason (confirmed):** all seven reported diagnostics were reproduced by running `dart analyze scratch/mobile-home/native_preview.dart`. That temporary preview lived outside the Flutter package, so the analyzer could not find `package:flutter/material.dart` or `package:campushub/...`. Missing runApp, MaterialApp, ThemeData, Color and DashboardScreen were consequences of those unresolved imports. The actual `lib/main.dart` and DashboardScreen analyzed cleanly before this fix; Flutter was installed and the app package configuration already existed. This was not a missing-widget implementation.
2. **Exact files/current lines/anchors:** move `scratch/mobile-home/native_preview.dart` to `campushub/tool/qa/home_preview.dart:2` (Flutter import), line4 (fixture import), line6 (`main`). Move the analogous scratch navbar preview to `campushub/tool/qa/navbar_preview.dart:2`, with `main` at5 and NavbarPreview at7. This guide and CAMPUSHUB_CONTEXT.md record the corrected locations. Older screenshot sections below refer to the locations used at the time of capture; these new paths supersede those paths for future runs.
3. **Changes made:** preserve both QA entry points inside the existing app package, update Home's fixture import to `../../test/home_test_fixtures.dart`, and apply Dart formatting. Keep previews outside production `lib/`. No fake SDK files, duplicate dependency setup or suppressed diagnostics.
4. **How it works / functions, inputs and outputs:** Dart resolves package imports using the containing package's `.dart_tool/package_config.json`, generated from pubspec.yaml. Inside `campushub/tool/qa`, both previews inherit the existing campushub/Flutter dependencies. Home preview `main()` passes isolated HomeTestCatalog/homeProducts/homeFacilities loaders to the real DashboardScreen and runApp displays that widget. Navbar preview `main()` displays NavbarPreview; its local state selects a tab, theme and text scale for QA. These preview inputs are test fixtures/local controls, not live catalog changes. Normal app startup remains `campushub/lib/main.dart`.
5. **Backend / API behavior:** no backend, authenticated workflow or API changes. The relocated files are optional QA launch targets, not new application routes. Existing fixtures/production widgets remain unchanged.
6. **Database / migration impact:** none. No new package or pubspec change; package configuration was already valid. Run normal development from `campushub`. Optional QA commands from that folder are `flutter run -t tool/qa/home_preview.dart` or `flutter run -t tool/qa/navbar_preview.dart`; normal app run is `flutter run -t lib/main.dart`. Do not distribute a preview APK as the normal app.
7. **Verification:** before relocation, the original Home preview produced the exact seven reported errors; normal main/dashboard analysis reported No issues found. After relocation, `dart analyze lib/main.dart lib/module_app/screens/dashboard_screen.dart tool/qa/home_preview.dart tool/qa/navbar_preview.dart` reported **No issues found**. Both relocated files were formatted. No widget tests, APK rebuild, emulator or physical-phone run was performed for this source relocation and import-path correction.
8. **Remaining limits / debugging:** VS Code may retain a diagnostic for a now-moved file until its old editor tab is closed and Dart: Restart Analysis Server is run from the Command Palette. Open the new path or the actual `lib/main.dart`. If unresolved imports occur in production later, check the nearest pubspec and run `C:\flutter\bin\flutter.bat pub get` from `campushub`; do not create a replacement material.dart or change Flutter APIs to silence the errors. This fix does not alter an unrelated SDK installation or global PATH.

**Safe learning exercise:** open `home_preview.dart`, follow `package:flutter/material.dart` to its SDK definition, then follow the fixture import to the existing test data. Compare with `lib/main.dart`, which loads the real session/router. Run `C:\flutter\bin\dart.bat analyze tool/qa/home_preview.dart tool/qa/navbar_preview.dart lib/main.dart` from `campushub`. The expected result is resolved imports and no undefined widget names. Use the existing fixture data only; no database edit is needed.

## 1. Cause / reason and scope

The mobile shell used four PageView pages plus a center Add Product action. Services had an existing Django catalog/editor and service-configured Facility records, but no mobile catalog/detail screen or mobile service request endpoint. The project uses MaterialApp, AppRouter, Navigator and PageController, not GetX routes/controllers, so this change preserves that actual architecture. No GetX dependency or parallel routing system was added.

The user clarified that this update should show service-specific requirements and contact-office guidance rather than build submission workflows. The drawer was already removed in the preceding request; it remains removed. No new Quick Actions are introduced.

## 2. Exact files changed, current lines and code anchors

The following table includes all application and test files changed in this feature. Line numbers refer to the final source at verification time; use the anchor if subsequent edits move them.

| File | Current lines / anchors |
| --- | --- |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 23: `class DashboardScreen`; 79: `void _goToTab`; 340: `ServicesPage(catalog`; 359: `bottomNavigationBar:` |
| `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` | 65: `default5Items =`; 144: `Widget _buildNavItem`; 93: `buildCenterAddButton` |
| `campushub/lib/module_app/widgets/navigation/retained_tab.dart` | 4: `class RetainedTab` |
| `campushub/lib/module_app/routes/app_routes.dart` | 7: `static const String services` |
| `campushub/lib/module_app/routes/app_router.dart` | 24: `AppRoutes.services` |
| `campushub/lib/module_app/models/service_item.dart` | 5: `class ServiceItem` |
| `campushub/lib/module_app/services/service_catalog.dart` | 14: `class ServiceCatalog {`; 24: `Future<Map<String, dynamic>> _get`; 75: `fetchServices`; 83: `fetchService(String` |
| `campushub/lib/module_app/services/facility_service.dart` | 29: `resource_type=facility` |
| `campushub/lib/module_app/screens/services_screen.dart` | 9: `class ServicesPage`; 27: `Future<void> _load`; 48: `Widget build` |
| `campushub/lib/module_app/screens/service_details_screen.dart` | 7: `class ServiceDetailsScreen`; 27: `void _requirements`; 98: `Widget build` |
| `backend/core/modules/facilities/mobile_services.py` | 13: `def active_services`; 20: `def serialize_service`; 85: `def service_list`; 90: `def service_detail` |
| `backend/core/core/urls.py` | 193: `path("api/mobile/services/` |
| `backend/core/api/views.py` | 1470: `def facilities_list` |
| `backend/core/modules/facilities/test_mobile_services.py` | 8: `class MobileServiceCatalogTests` |
| `campushub/test/service_catalog_test.dart` | 9: `void main` |
| `campushub/test/services_screen_test.dart` | 51: `void main` |
| `campushub/test/dashboard_center_add_button_test.dart` | 7: `void main` |
| `campushub/test/dashboard_search_appbar_test.dart` | 8: `void main` |
| `campushub/test/floating_bottom_navbar_test.dart` | 6: `void main` |

Documentation: this guide (`docs/mobile-services-navigation.md`), the current preference in `CAMPUSHUB_CONTEXT.md`, and a follow-up pointer in `docs/sidebar-navigation-white-all.md`.

## 3. Changes made

- Five ordinary, consistently styled Lucide navigation items replace the visible center action. Services uses the briefcase icon and its own selected state at index 2. Facilities moves to index 3 and Profile to index 4; the Home facility shortcut was adjusted to index 3.
- The reusable center-action builder, center-action widget branch and `ProductsScreen.showAddProductSheet` remain. Dashboard no longer supplies the center callback, and its now-unused private callback/import were removed. No visible + or floating replacement exists.
- `RetainedTab` keeps visited screens alive, preserving loaded data, search and scroll state while tabs change. Services also has a PageStorageKey. Reduced-motion settings use immediate tab changes and suppress the nav icon scale animation.
- Services has a search field, active real-record cards, loading, honest empty/search-miss, error/Retry and pull-to-refresh states. Card names, descriptions and categories come from the backend, not the example service names in the request.
- Details reload the selected service before enabling its request action. The page displays actual images, description, office/location, configured rate information, office availability, requirements, terms and applicable laboratory/assessment/lease information. Removed/inactive services have no enabled request action.
- Request Service / Request Assessment / Apply for Lease open different guidance based on the actual configured service workflow. They explicitly state that no request has been submitted. Message Office reuses the existing authenticated Facilities Admin contact/chat path. No generic physical-booking form is used for service intake.
- The Facilities client explicitly requests physical resources via an optional existing-list filter. This stops service resources appearing in the mobile physical-facility list/Home preview without breaking the original unfiltered API response contract.

## 4. Functions, inputs/outputs and data flow

### Navigation

`DashboardScreen(initialTab: 0, serviceCatalog: ...)` accepts an initial tab and an injectable catalog for tests. In production the default catalog reads Django. AppRouter maps `/services` to `DashboardScreen(initialTab: 2)`. `/services/details` identifies the MaterialPageRoute pushed by a service card, with the selected record ID in route settings; it is not a separately implemented deep-link parser. This follows the existing facility detail pattern.

`_goToTab(index)` updates `_currentIndex` and the same PageController. It closes the header search, dismisses keyboard focus and either animates or jumps according to reduced-motion settings. The existing PageView-to-selected-index callback remains. `RetainedTab.build` calls `super.build(context)` with `wantKeepAlive = true`, so leaving a visited page does not destroy its state. The bottom icon is chosen by `currentIndex`, not by a second controller.

```dart
// Index order must agree in the page list and navbar configuration.
// 0 Home, 1 Marketplace, 2 Services, 3 Facilities, 4 Profile
_goToTab(2); // Selects Services without replacing the navigator stack.
```

### Catalog transport and model

`ServiceCatalog._get(path)` sends read-only GET requests using the existing `ApiConfig.serverBaseUrls`. Fallback hosts are attempted concurrently with a four-second timeout per host, so old addresses do not add a long sequential delay. The first valid response wins, updates the working-host cache, and late results cannot replace it. An owned HTTP client is closed; an injected test client remains caller-owned. Invalid/missing JSON and API failures throw rather than fabricate an empty success.

`fetchServices()` returns `Future<List<ServiceItem>>` from the `services` array and excludes non-active rows defensively. `fetchService(id)` returns a freshly validated selected record from the `service` object. `ServiceItem.fromJson` reuses FacilityItem's image URL handling and catalog fields, including multiple images, without sending a service to the normal facility reservation UI. It derives action wording from the stored category or legacy service mode; those are classification labels, not hard-coded service records or prices.

### Django source and public projection

`active_services()` reads the existing Facility model, uses the existing `service_resources_q()` type/mode condition, excludes archives, and requires stored `available` (the service editor's Active status). Laboratory, training/assessment, lease and legacy service modes share that existing classification. `Count('rooms')` supplies the shared serializer's count in the same query, avoiding per-record room queries.

`serialize_service(resource)` reuses `serialize_facility` and existing `service_labels`/`service_pricing_label`, then publishes only allowed catalog fields and customer-facing configured information. Raw workflow JSON, internal notes, staff configuration and inactive analysis rates are excluded. `online_requests_available` is false because this change does not implement intake. Output names, amounts, units and schedules remain recorded values; missing office arrangements use contact-office guidance rather than invented hours.

Data flow:

`Django Facility + configured workflow ? active_services ? serialize_service ? GET JSON ? ServiceCatalog ? ServiceItem ? ServicesPage ? ServiceDetailsScreen ? requirements / Message Office`.

Example: an existing active laboratory with an active saved Moisture rate returns that rate; an inactive rate is omitted. Archiving the laboratory removes it from the catalog and makes its detail endpoint return 404. Nothing is copied into a new services table.

## 5. Backend / API behavior

| Endpoint | Behavior |
| --- | --- |
| `GET /api/mobile/services/` | Public active catalog, consistent with existing public facility browsing. Returns `{services: [...]}`. |
| `GET /api/mobile/services/<id>/` | Same eligibility checks; returns `{service: {...}}` or 404. |
| `GET /api/facilities/?resource_type=facility` | Existing endpoint with optional physical-resource filtering. Without this parameter, its existing contract remains. |

New catalog endpoints are GET-only; POST returns 405. No mutation, request creation, approval, payment, document, stock or booking API behavior changed. Existing administrator RBAC and authenticated chat remain in force. Message Office uses the existing contact selection (active Facilities Admin, with the existing Super Admin fallback); it does not invent assigned personnel. Messaging requires the normal login/chat connection and shows existing errors if no contact is available.

Deploy the updated Django code alongside the updated app. There is no existing mobile service intake API to reuse; authenticated application submission, sample acceptance, resource checks, assessment allocation and lease processing remain separate future work, as explicitly selected by the user.

## 6. Database / migration impact

No new tables, models, stock fields, service records, rates, schedules, migrations, dependencies or live database writes. Existing Facility service settings remain authoritative. No operational or research sample data was installed. Test records exist only in isolated test fixtures.

## 7. Tests performed and manual checks

Actual successful verification:

- **23 Flutter tests passed** across dashboard header, tab/search behavior, dormant center-action reuse, five-item navigation, catalog transport and service screens.
- **26 Django tests passed** across `modules.facilities.test_mobile_services`, `modules.facilities.test_service_navigation` and `api.test_mobile_facility_booking`; Django system checks reported no issues. The catalog test confirmed one database query, active/archive/physical exclusions, real configured pricing, no private workflow exposure, legacy modes, honest empty results, GET-only behavior, and compatibility of the original facility endpoint.
- `flutter analyze` on all ten changed application files and five changed/new test files reported **No issues found**.
- Widget checks cover 320/390px phone widths, 844x390 landscape, five selected tab states, retained Services search/data, service detail revalidation/failure/Retry, distinct guidance for all three workflows, no drawer, no visible quick action, existing Messages navigation, error versus empty versus search miss, 1.5x text and reduced-motion behavior on Services. Navbar checks also include 768px and bottom safe-area insets.
- Services review images: `scratch/mobile-services-review/services-320.png` and `services-390.png`. The 390px capture was visually inspected. They are widget fixtures, not live catalog screenshots; screenshot-only Material icon font rendering is incomplete. The in-app icons use the existing icon assets. There was no physical Android or live authenticated end-to-end test.
- Initial checks found outdated drawer/center-action expectations, an ambiguous test finder matching search text as well as a card title, a retry callback returning a Future to setState, and a reduced-motion helper missing its BuildContext parameter. These were corrected before the successful final runs.

Repeat from `campushub`:

```powershell
flutter test test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart test/floating_bottom_navbar_test.dart test/service_catalog_test.dart test/services_screen_test.dart
```

Repeat from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_mobile_services modules.facilities.test_service_navigation api.test_mobile_facility_booking --keepdb --noinput
```

Manual verification:

1. Restart the Flutter app (or rebuild/deploy the APK) and deploy/reload Django. Confirm the exact five-tab order and no + button, FAB or drawer.
2. Tap every tab and swipe between pages; confirm selection follows the actual page. Tap Home's facility shortcut and confirm Facilities, not Services.
3. In Services, search for an actual configured active record, switch to another tab and return; check query, loaded results and scroll position remain.
4. Open its details. Verify recorded images, description, location, rates, availability, requirements and terms. Open its service-specific request action and verify no submission/approval is claimed.
5. Use Message Office while signed in, or verify the existing honest login/contact/chat error. Do not assume a successful live conversation from widget tests.
6. Check an empty catalog and stop the server temporarily in development to distinguish empty from error; restore the server and Retry. Never add fake service cards to hide an error.
7. In an isolated development database, deactivate or archive a service after opening the list, then open its details. Its request action must not remain enabled.

## 8. Debugging, remaining limitations and safe practice

Confirmed limitation outside this feature: switching into the existing Home carousel with 1.5x text exposed a fixed-height carousel overflow (60px at 320 width, 20px at 390). Normal-size Home header/navigation regression checks pass. The final large-text tests focus on the new Services tab; this update does not claim the entire existing app supports every dynamic-text size. No unrelated Home carousel redesign was performed.

If Services is empty, first verify an actual unarchived service exists and its stored status is `available`; the record must match the existing service category/mode classifier. Inactive, unavailable and maintenance resources are intentionally excluded. Category labels are not automatic seeded records.

If loading fails, verify the PC address in ApiConfig, Django listening on `0.0.0.0:8000`, phone/PC network access and the new API routes. A successful old facility API does not prove the newly deployed Services endpoint exists. If detail stops working, the service may have been archived/deactivated; Retry must not create a booking or restore the service.

If a price is absent, correct its actual configured service pricing in the authorized admin editor. Do not hard-code a mobile fee. If office hours are absent, contact-office guidance is intentional; office hours never confirm an assessment date, sample acceptance or lease approval.

Safe learning exercise: modify only an isolated test fixture's laboratory name, then run `flutter test test/service_catalog_test.dart`. Update the expected fixture value and rerun. Trace how the JSON `name` flows into ServiceItem and the card title. Next change the fixture status to inactive and verify it is filtered out. Restore the fixture afterward; no production request or service record is needed.


## Bottom-navigation selection styling - October 18, 2026

1. **Reason:** the user requested a clearer CampusHub palette and filled icons after selecting a tab. Previously the same Lucide outline glyph was merely recolored, so selection had little shape difference.
2. **Files:** `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` (constructor palette, `default5Items`, `_buildNavItem`, adaptive bar height and decoration); `campushub/test/floating_bottom_navbar_test.dart` (outline/filled pairs, selection, contrast and large-text/reduced-motion checks); `campushub/lib/module_app/screens/services_screen.dart` (the View Service label can wrap inside its row at large text sizes). This guide and `CAMPUSHUB_CONTEXT.md` record the change. Current anchors: constructor palette at lines 49-51; `default5Items` at 68; `_buildNavItem` at 177; `AnimatedContainer` at 204; adaptive `navHeight` at 304; bar separator at 320. The test entry is `void main` near line 5, and the wrapping label is the `Flexible` around View Service in `services_screen.dart` near line 175.
3. **Changes:** white flat bar; navy filled selected icon over a compact gold `#FCB316` indicator; quieter navy outline idle icons and navy labels. The main bar shadow was removed, leaving its subtle separator. One consistent Material icon family supplies real outline/filled variants; Lucide has no matching solid font variants in the current package. The existing five labels/order and hidden reusable center-action branch remain. Focus/hover/splash colors use the same palette.
4. **How it works:** `FloatingBottomNavbarItem.icon` supplies the idle outline and its existing `activeIcon` field supplies the filled glyph. `_buildNavItem(context, index, item)` receives the current index and renders the filled glyph plus gold indicator only when `index == currentIndex`. `onTap(index)` still calls the same Dashboard/PageController navigation. `selectionColor` is a reusable constructor parameter; default gold remains the existing Flutter color, independent of the changed web-only shade. The 180ms indicator transition and small icon scale honor reduced motion. Bar height follows scaled label height with a 60px minimum; SafeArea still protects the system inset. Example: selecting Services sets index 2, fills its briefcase icon and moves the gold selection treatment there; no record or API request is created by this styling code. Shape, label weight and selected semantics accompany color, so selection is not color-only. The outer Semantics node supplies a single full label and accessible onTap; child icon/text semantics are excluded to prevent duplicate announcements.
5. **Backend / API:** unchanged. No route, state-controller, service data source, authentication, permission or request-submission logic changed.
6. **Database / migration:** none. No dependency or image asset was added; built-in Material icons are already available. No web gold or Flutter service rates changed.
7. **Verification:** 20 Flutter tests passed across navbar, dashboard header/search, dormant center action and Services UI. They exercise all five selected states at 320/390/768px, filled/outline glyphs, gold indicators, preserved layout, content clearance, dark-theme context, bottom safe-area insets, 2x label text and reduced motion. Computed palette contrast checks passed at least 4.5:1 for selected navy on gold and idle navy-on-white after alpha blending. The existing Services large-text test exposed an over-wide View Service text row with Flutter's test font; making only that label Flexible resolved it. Targeted Flutter analysis of the component, Services label and navbar test reported No issues found. Native verification also passed seven Pixel 10a Android emulator scenes: Home, Marketplace, Services, Facilities and Profile selected in light context, then Services in dark context and at 2x text. UI Automator confirmed exactly one accessible name per destination and the correct selected flag. The first native inspection exposed duplicate label semantics; the final component excludes duplicate child semantics while preserving a labelled accessible tap action. An emulator System UI busy dialog during cold boot was dismissed with Wait; it was not an application crash. Native captures and machine-readable results are in `scratch/mobile-navbar/` (`native-verification.json`). Home and dark/large Services captures were visually inspected. These screenshots use `scratch/mobile-navbar/native_preview.dart`, which imports the actual production widget and never loads accounts, catalog records or APIs. They verify the component rather than a signed-in full app workflow. The normal `lib/main.dart` debug APK was rebuilt successfully after the temporary preview build, so `build/app/outputs/flutter-apk/app-debug.apk` is the normal app artifact, not the preview. The connected physical phone was left untouched.
8. **Limitations / debugging / safe exercise:** the bar intentionally remains branded white in the existing light and dark screen contexts; this is not a whole-app dark-theme redesign. Very large labels may ellipsize horizontally, while full labels remain available to accessibility/tooltip output. Original navigation and screen state are covered by existing widget checks. To learn safely, change only `selectionColor` temporarily in a local widget-test fixture and rerun `flutter test test/floating_bottom_navbar_test.dart`; observe that the icon shape still follows currentIndex and the gold default assertions stay unchanged. Restore the fixture; no database or server interaction is needed. Restart/rebuild the mobile app to see the updated component.


Final verification commands for the October 18 selection styling:

```powershell
# From campushub:
flutter test test/floating_bottom_navbar_test.dart test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart test/services_screen_test.dart
flutter analyze lib/module_app/widgets/navigation/floating_bottom_navbar.dart lib/module_app/screens/services_screen.dart test/floating_bottom_navbar_test.dart
flutter build apk --debug --target lib/main.dart
```

The complete 20-test run passed after the application changes. The navbar tests were rerun after replacing a deprecated test-only semantics accessor and passed again; final analyzer output reported No issues found with that rerun. Targeted whitespace checks passed. The first semantics-test run needed its test handle disposed before Flutter's end-of-test checks; that test harness cleanup is now explicit. Existing web, API and mobile submission limitations described above remain unchanged.

## Mobile header and discovery Home - October 18, 2026

This update supersedes the earlier drawer-removal, rotating Home banner, separate Home facility model, and service request-button wording in this guide. The five bottom destinations and their current icon-selection styling remain; compact labels now follow native Material text-scaling behavior.

### Reason and confirmed causes

The old Home started with a large rotating promotional carousel and had no Services preview. Header search switched to Marketplace without passing its query. The drawer had been removed in an earlier update. A separate private Home facility model displayed different status/rating information from the existing FacilityItem. The Notifications button had an empty callback: this checkout has no mobile notification feed, model, API client or notification screen. This is a confirmed implementation limitation, not evidence of zero unread notifications.

### Files, current lines and nearby anchors

Paths below are relative to the repository root. Lines describe this implementation; use the named anchor if later edits move a line.

| File | Current line / nearby anchor | Change |
|---|---|---|
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 25 `class DashboardScreen`; 82 `_goToTab`; 101 `_openMessages`; 130 `_openNotifications`; 166 `_drawerDestination`; 182 `dashboard-brand-header`; 356 `HomePage`; 919 `_compactCard` | Reuse the existing shell, restore drawer, replace header search with one Home search, real chat badge, compact product presentation |
| `campushub/lib/module_app/screens/home_page.dart` | 20 `class HomePage`; 58 `_observed`; 64 `_load`; 70 `_readProducts`; 82 `_readFacilities`; 89 `_readServices`; 95 `_refresh`; 112 `_matches`; 115 `_section`; 253 `home-search`; 399 `_FacilityDiscoveryCard`; 502 `_ServiceDiscoveryRow` | New focused Home implementation using existing catalog services, models and detail screens |
| `campushub/lib/module_app/models/facility_item.dart` | 24 `this.capacityLabel`; 61 `capacity_label`; 85 `final String capacityLabel` | Read the existing backend's formatted capacity range; optional constructor field preserves existing callers |
| `campushub/lib/module_app/models/service_item.dart` | 37 `actionLabel` | Use `How to Request This Service`; no submission implied |
| `campushub/test/dashboard_header_test.dart` | `void main` | Phone widths 320/390, double-size text, real production card layout, header controls, notification limitation |
| `campushub/test/dashboard_search_appbar_test.dart` | `drawer routes to existing tabs` | Drawer destinations, selected tab and retained Home search |
| `campushub/test/home_page_test.dart` | `search covers all three catalogs` | Full fetched-catalog search, capacity/status rendering, service details navigation, loading/empty/error/Retry |
| `campushub/test/home_test_fixtures.dart` | `HomeTestCatalog` | Isolated test data and loaders; never imported by production screens |
| `campushub/test/dashboard_center_add_button_test.dart` | `dashboard uses five tabs` | Expect the restored drawer while keeping the center action hidden |
| `campushub/test/service_catalog_test.dart`, `campushub/test/services_screen_test.dart` | `actionLabel`, `details revalidate active state` | Match truthful guidance wording and preserve category-specific instructions |

### What changed and how it works

1. **Header:** white surface, navy Material icons, existing logo and Montserrat wordmark. Menu opens the restored drawer. Messages opens the existing MessagesPage from both header and drawer. An AnimatedBuilder listens to the existing ChatService singleton and sums actual conversation `unreadCount` values; only a positive count displays a badge. No alternate chat connection/service was created. Notifications opens an honest availability sheet without a fabricated unread badge.
2. **Navigation:** existing MaterialApp/AppRouter/Navigator/PageController and RetainedTab remain. This checkout does not use GetX for this shell; no GetX package/controller was added. Drawer indexes: Home 0, Marketplace 1, Facilities Booking 3, Services 2, Profile & Account 4. Messages and My Cart push their existing screens. Back uses the existing Navigator behavior. The bottom bar remains Home, Marketplace, Services, Facilities, Profile; no center plus or quick actions.
3. **Home:** greeting reads the logged-in first name through SessionService. An unknown/missing name produces `Welcome to CampusHub`. The promotional carousel, its timer, duplicate private facility model and obsolete Home preview classes were removed. My Activity and Recent Activity were already absent; their backend records/pages were not deleted. Seller-specific screens and permissions are unchanged.
4. **Marketplace:** ProductService.fetchApproved supplies actual products. Home stably sorts by real `soldCount`, preserving API order for ties; no Hot/New/Recommended label is added. Up to six cards appear in the normal preview. The compact branch of the existing product card reuses its favorite, product-details interaction tracking and CartService.quickAdd methods. Existing Marketplace card presentation remains the default outside Home.
5. **Facilities:** FacilityService.fetchFacilities still requests physical resources through `/api/facilities/?resource_type=facility`. Results are parsed by the existing FacilityItem; no new facility model. Home shows the recorded image, name, backend capacity_label and operational status. For older responses without a range, a positive recorded capacity is shown; absent capacity is omitted. Open for Booking does not claim a selected time slot is conflict-free. Tapping opens FacilityDetailsScreen with that exact record. Home omits rates and empty review stars.
6. **Services:** the existing ServiceCatalog and ServiceItem provide actual active service records. Up to three show in the normal Home preview. A row opens the existing ServiceDetailsScreen, which revalidates its active state. The guidance action now says `How to Request This Service` and retains different sample-analysis, assessment and lease instructions, actual requirements/location and Message Office. There is no new submission workflow.
7. **Search:** TextEditingController supplies a trimmed, case-insensitive query. `_matches(text)` returns true when the query occurs in the product name/seller/category, facility name/category/location or service name/category/description. All fetched rows are searched, including those outside the normal preview limit. Typing updates local results and does not call another API. This is catalog discovery, not a new server-wide search endpoint. See All opens the existing unfiltered destination tab; tapping a result opens its actual details.
8. **States:** each catalog has its own FutureBuilder. A failed service catalog does not hide working products. Loading shows a small navy progress indicator; successful empty catalogs use the requested exact copy; failed loads show Unable to load plus Retry. Search misses are different from empty catalogs. Pull-to-refresh starts each existing catalog read once and reloads the greeting. `_observed(future)` attaches an immediate error handler so an offscreen section can safely attach its FutureBuilder later; the original future still exposes its error to that section.
9. **Layout:** navy `#1A1851`, mobile gold `#FCB316`, white/light surfaces and restrained navy-derived borders/text. No gradients or decorative shadows. Sections use 20px side spacing and 24px separation. Horizontal lists scroll naturally. At larger text sizes section headings and See All stack, and card heights follow TextScaler so titles/status do not overflow. Icon actions keep tooltips and Material touch behavior.

### Function inputs, outputs and data flow

```text
DashboardScreen -> SessionService -> firstName -> compact greeting
                -> existing ChatService -> conversation unread counts -> Messages badge
HomePage._load()
  -> ProductService.fetchApproved() -> List<ProductItem> -> sort -> product cards
  -> FacilityService.fetchFacilities() -> FacilityServiceResult
       -> FacilityItem.fromJson() -> capacityLabel/status -> facility cards
  -> ServiceCatalog.fetchServices() -> List<ServiceItem> -> active rows -> service rows
TextEditingController.text -> _matches(record text) -> filtered existing rows
Tap result -> existing detail screen; cart/favorite -> existing services
```

`_readProducts()` returns a Future of real ProductItems; `_readFacilities()` converts a failed transport result into an error instead of a fake empty success; `_readServices()` retains active rows. `_section<T>` receives a future, matching function, empty message, Retry callback and content builder, then chooses the correct visible state. Each Retry callback uses a block inside setState: assigning a Future with an arrow callback returns that Future and triggers Flutter's debug assertion. Tests caught that issue during implementation; the callbacks now synchronously assign state and let FutureBuilder observe completion.

Annotated example: if the backend sends `capacity: 500` and `capacity_label: "300-500 pax"`, FacilityItem stores the label, and the Home card uses that label rather than concatenating or inventing a range. Search `court` tests the recorded facility text and shows the matching card. No booking is created by search or by opening its details.

### Backend, database and deployment

No Django/FastAPI endpoint, permission, model, migration, payment, order or reservation workflow changed. Products use `/api/products/approved/`; physical facilities use `/api/facilities/?resource_type=facility`; Services uses existing `/api/mobile/services/` and `/api/mobile/services/<id>/`; Messages uses existing authenticated chat APIs/WebSocket. Capacity label was already in the facility payload. No new package or generated image was added. Rebuild/restart Flutter to see this UI; no migration command is required. The app still needs the configured reachable Django server and existing Services APIs.

### Verification and manual checks

27 Flutter tests passed across header, drawer/search, discovery, dormant center action, bottom navigation, ServiceCatalog and Services UI. Targeted analysis of the changed application/test Dart files reported `No issues found!`. Tests cover 320/390px phones, double text, existing 844px service landscape checks, retained tab state, search beyond the preview limit, actual formatted capacity, loading/empty/error/Retry and category-specific contact guidance. Fixtures are test-only; these checks do not claim successful live authenticated transactions, unread-message delivery or physical-phone performance.

Commands from `campushub/`:

```powershell
flutter test test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/home_page_test.dart test/dashboard_center_add_button_test.dart test/floating_bottom_navbar_test.dart test/service_catalog_test.dart test/services_screen_test.dart
flutter analyze lib/module_app/screens/dashboard_screen.dart lib/module_app/screens/home_page.dart lib/module_app/models/facility_item.dart lib/module_app/models/service_item.dart test/home_page_test.dart test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/home_test_fixtures.dart test/service_catalog_test.dart test/services_screen_test.dart test/dashboard_center_add_button_test.dart
flutter build apk --debug --target lib/main.dart
```

Manual checks:

1. Sign in as an existing normal user. Verify the actual first name, menu/brand/Messages/bell header and absence of the top-right search icon and rotating banner.
2. Search a real product, facility and service in turn. Open each result. Clear search; switch tabs and return to confirm retained state. See All should activate the corresponding bottom tab.
3. Open drawer destinations and Messages from both entry points. Open My Cart. On actual unread chat data verify the badge changes; with zero unread messages there is no badge.
4. Verify facility capacity ranges/status against saved records; no Home pricing formula or invented rating should appear.
5. Open each active service and its How to Request guidance. Check actual requirements and contact/visit-office instructions; no request should be submitted.
6. Test an empty catalog, stop/restart a development server and Retry, then pull to refresh. Distinguish no records from connection failure. Increase the phone text size and scroll all three Home sections.

### Debugging, limitations and safe learning exercise

If the UI is unchanged, restart/rebuild the running Flutter application; a Django refresh alone cannot update Dart code. If a section cannot load, check the existing ApiConfig address, Django binding/firewall/network and the real API response; do not replace it with sample rows. If a service disappears, check its real active/archived state. If a capacity range is missing, inspect `capacity_label`; do not infer a minimum from the maximum. Products without recorded sales keep the server order, without claiming to be popular or recently added. Mobile notifications remain unavailable, and service intake remains office guidance. Home stays white in a dark-theme app context by this brand-specific scope; other screens are not a whole-app dark-theme redesign.

Safe exercise: in `test/home_test_fixtures.dart` only, change the laboratory description. Run `flutter test test/home_page_test.dart`, then search a word from that description in an isolated widget test and verify it finds that service without increasing `catalog.calls`. Next set the fixture service inactive and verify it is excluded. Restore the fixture. This teaches JSON-to-model-to-filter-to-widget data flow without creating or changing real service records.

Native verification: five valid Pixel 10a Android emulator captures show the top Home, facility/service section, drawer, and top/lower Home at OS night mode with 1.3x system text. Captures are in `.impeccable/review/mobile-home/`; `scratch/mobile-home/native_preview.dart` imports the production DashboardScreen with test-only catalog loaders. The preview reads the emulator's existing saved greeting but does not create accounts, submit requests or mutate live catalogs. There is no synthetic production fallback. A cold-boot System UI busy dialog and transient theme-change/launcher frames were excluded and recaptured only after the expected Home semantics were present. This does not establish real handset performance, a signed-in live transaction, a complete dark-theme app or iOS/tablet verification. The connected physical phone was not modified. The final default debug APK was rebuilt from `lib/main.dart`, not the scratch preview.

Reviewer correction: the independent design review found crowded bottom labels at 320px with 2x text. Only the destination Text now uses `TextScaler.noScaling`, matching Flutter SDK Material NavigationBar behavior (`C:/flutter/packages/flutter/lib/src/material/navigation_bar.dart`, navigation-label and height documentation). All five names remain visible at normal native label size; full tooltip text still follows system scaling and Semantics preserves every full destination name, selected flag and tap action. Home content continues to honor the user's text size. Files: `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart`, near `Text(item.label)` / `textScaler`; `campushub/test/floating_bottom_navbar_test.dart`, large-text test. The working tree received separate navbar icon/indicator edits during this task; this Home update preserves the current appearance rather than restoring an older pill or indicator. Only destination-label scaling was changed here. Existing tap callbacks, order and safe-area behavior remain. The Services reduced-motion test checks any implicit animations actually present inside a destination; a static destination also honors reduced motion without requiring a removed AnimatedScale or indicator widget.


## Revert latest Home search refinement - October 18, 2026

- **Reason:** user requested Revert. Undo only the immediately preceding greeting/search/filter refinement; keep the broader discovery redesign and unrelated concurrent header/navbar/card changes.
- **Files:** `campushub/lib/module_app/screens/home_page.dart` (`Greeting section`, `fontSize: 22`, `Search input field`, `home-search`); `campushub/lib/module_app/widgets/home/home_preview_cards.dart` (`HomeSectionHeader`, `View service`); `campushub/test/home_page_test.dart` (`void main`).
- **Restored:** the previous GoogleFonts welcome at 22sp, existing greeting/supporting copy, 16dp spacing and original full-width 52dp search container. Removed the new filter icon/button, filter sheet, filter state, section gating, explicit font-variation additions and the filter-specific test. The small shared heading/action layout edits from that refinement were also undone to restore its prior implementation.
- **Functions/data flow:** `_section<T>` once again shows each existing catalog without an extra scope condition. `_matches` still receives the current search query and record text and returns the existing case-insensitive match. Catalog futures, actual records and existing routes/actions remain. No new controller or replacement search logic is added by the revert.
- **Backend/API/database:** unchanged; no migration or server command. The real catalog data and permissions were not reset.
- **Verification:** formatted affected Dart files; targeted analysis of the two source files and discovery test reported No issues found. The full widget suite was not rerun for this restoration; earlier compact/filter test results do not describe the reverted UI. Prior shared-card large-text limitations are restored with the previous layout.
- **Safe exercise:** search an existing product name, clear the query and confirm all three catalog sections return. Verify no Filter search button or sheet exists. Restart/hot-reload Flutter to load the restored source; no database change is needed.

Final revert anchors: `home_page.dart:194` Greeting section, `:213` fontSize22, `:231` Search input field, `:247` home-search; `home_preview_cards.dart:41` HomeSectionHeader and `:556` View service. The normal `flutter build apk --debug --target lib/main.dart` succeeded after the revert. Whitespace checks passed. The temporary emulator preview was restarted with the restored source, then closed; the connected physical phone was untouched.


## White mobile header and welcome-only greeting - October 18, 2026

1. **Reason:** the user requested the mobile header return to white and removal of Good morning and What are you looking for today. This is a small presentation change after the prior search/filter revert.
2. **Exact files/anchors:** `campushub/lib/module_app/screens/dashboard_screen.dart:203` (`dashboard-brand-header`) and `:303` (`statusBarColor`); `campushub/lib/module_app/screens/home_page.dart:194` (welcome Text), `:200` (`fontSize: 22`) and `:223` (`home-search`). This guide and CAMPUSHUB_CONTEXT.md record the change.
3. **Changes:** header background and status bar are white; menu, message and notification icons use navy. Campus uses navy and Hub keeps the existing gold accent, so the wordmark is visible on white. Android status icons use dark brightness; the corresponding iOS status-bar brightness is light. Removed the two extra greeting/supporting Text widgets and their internal gaps. Existing welcome size, full-width search and catalog sections remain.
4. **How it works:** DashboardScreen.build supplies header and SystemUiOverlayStyle colors. HomePage.build still receives the saved first name from DashboardScreen; for example, a recorded first name of Ana renders Welcome Back, Ana, while a missing name keeps Welcome to CampusHub. No new text controller, search filter, route or data calculation was added. The search controller and matching flow are unchanged.
5. **Backend/API:** unchanged; the same session, catalog, messages and navigation handlers remain.
6. **Database/migrations:** none. Hot-reload/restart Flutter to load the source change; no Django command or data edit is required. No APK rebuild was performed for this small follow-up.
7. **Verification:** Dart formatting and targeted analysis of both modified source files succeeded with No issues found. Source inspection confirmed white header/status colors, navy foregrounds and removal of both requested strings. The existing 390px normal-text dashboard widget check was run and failed with a RenderFlex right overflow of 10px. The same overflow had also been observed before this follow-up. Its exact child was not isolated here; this is not claimed as a passing render check. No physical-device or new native screenshot check was performed.
8. **Limits/debugging/practice:** remaining layout overflow is separate pending verification work, not hidden by zero/fake data or weakened assertions. To verify this presentation, restart Flutter and check the white header, visible navy controls, welcome and search. Safe learning exercise: inspect the header color and SystemUiOverlayStyle together; changing a header surface without matching status-icon brightness can make system icons unreadable. Try color changes only in an isolated preview and restore the recorded white/navy values. No production account or database change is needed.


## Light container palette - October 18, 2026

1. **Reason:** the user requested a better light/light-gray container treatment. White cards on a very light neutral page give clear separation without heavy shadows or gray text blending into gray cards.
2. **Files/current anchors:** `campushub/lib/module_app/widgets/home/home_preview_cards.dart:18` HomeAppColors; `:25` appBackground; `:26` surfaceTint; `:171` first cardBorder and equivalent facility/service card decorations. `campushub/lib/module_app/screens/home_page.dart:207` Search input field. This guide, CAMPUSHUB_CONTEXT.md and scoped mobile design files record the palette.
3. **Changes:** page background `#F8FAFC`; cards/search/header white `#FFFFFF`; image/fallback containers `#F1F5F9`; subtle shared borders `#E2E8F0`; primary text CampusHub navy `#1A1851`; secondary text `#475569`; quieter metadata token `#64748B`. Removed the three catalog-card shadows and the search shadow for a flat resting surface. Existing geometry, content, navigation and real-data states remain.
4. **How it works:** HomeAppColors is the shared constant palette consumed by DashboardScreen.build, HomePage.build and the three preview-card build methods. `appBackground` colors the page; `white` colors the card body; `surfaceTint` colors the recorded-image region/fallback container; `cardBorder` aliases `border` so all cards share the same outline. Inputs are existing record/image/text fields; output is the same widgets rendered with the updated palette. Example: a product without a saved image shows its existing navy fallback icon on the light-gray image container, while its real price/seller remain on the white card body. No sample record is introduced.
5. **Backend/API:** unchanged. Catalog requests, search, cart, favorites, facility/service details and permissions keep the existing implementations.
6. **Database/migrations:** none. No dependency, image asset or server command required. Hot-reload Flutter to load the new constants; no APK rebuild performed for this color-only change.
7. **Verification:** formatted both edited Dart files; targeted Dart analysis including DashboardScreen reported No issues found. Computed sRGB contrast: navy on white 16.24:1; secondary text on white 7.58:1 and page 7.24:1; metadata on white 4.76:1 and page 4.55:1. Navy fallback icons on image tint are 14.82:1. The metadata token is not intended for body text on the darker image tint (4.34:1); use secondary/navy there. No new widget tests were written for constant palette/shadow changes, and the full UI suite/native render was not rerun. The previously recorded 10px layout overflow remains outside this color-only verification.
8. **Debugging/learning exercise:** if a container still looks unchanged, restart Flutter and inspect which HomeAppColors token it uses before adding local colors. Safely change only a test-preview surfaceTint to white, compare fallback image separation against card bodies, then restore `#F1F5F9`. Verify the actual data and tap destinations remain identical. Keep secondary/body text dark enough for its actual surface; a light border is separation, not a text color.


## Smaller Home welcome - October 18, 2026

1. **Reason:** user requested a smaller Welcome Back heading.
2. **Exact files/anchors:** `campushub/lib/module_app/screens/home_page.dart:200`, `fontSize` beneath `Welcome Back`; `campushub/DESIGN.md:18`, `greeting`; `CAMPUSHUB_CONTEXT.md:3`, latest welcome sizing; this guide, `Smaller Home welcome`.
3. **Changes:** reduce only the welcome's base font size from22sp to20sp; align its documented typography with the existing Montserrat family. Color, weight, wording and spacing remain.
4. **How it works:** `HomePage.build` reads `widget.firstName`, trims it and renders the personalized welcome or existing generic fallback. Its `GoogleFonts.montserrat` style now uses20sp; Flutter still applies device text scaling. Example: saved name Ana renders Welcome Back, Ana at the smaller base size. No user-data calculation changes.
5. **Backend/API:** unchanged; no endpoint, controller or permission changes.
6. **Database/migrations:** none. Hot reload Flutter to see this source-only style change; no dependency command required.
7. **Tests performed:** `dart analyze lib/module_app/screens/home_page.dart` passed with No issues found. No new tests, APK build or device screenshot for this reversible font-size adjustment.
8. **Limitations/debugging/exercise:** the previously documented Home card overflow is not claimed fixed. If the heading is unchanged, confirm the running Flutter app uses this checkout and hot reload/restart. Safe exercise: in a disposable preview, compare20sp and22sp with the phone's larger-text setting enabled, verify the real first name remains visible, then restore20sp. Keep system text scaling enabled.

## Sugar Pie header wordmark - October 18, 2026

1. **Reason:** the user supplied Sugar-Pie-W00-Regular.ttf and requested that exact typeface for CampusHub in the mobile header. Earlier attempts could not apply it because only Montserrat was present.
2. **Files/current anchors:** new `campushub/assets/fonts/Sugar-Pie-W00-Regular.ttf`; `campushub/pubspec.yaml:75` (`family: SugarPie`) and `:77` (asset path); `campushub/lib/module_app/screens/dashboard_screen.dart:246` (`dashboard-brand-name`) and `:248` (`fontFamily: 'SugarPie'`); `campushub/test/dashboard_header_test.dart:44` (`FontLoader('SugarPie')`). This guide, CAMPUSHUB_CONTEXT.md and the scoped mobile design documents record the font.
3. **Changes:** copy the user-provided font unchanged into Flutter assets, register its SugarPie family alias, then use that family only on the shared header Text.rich wordmark. Keep the current navy Campus/gold Hub spans, white header, logo and navigation. Set regular weight400 and natural letterSpacing0 at the existing24sp size; the supplied font is Regular, so synthetic extra-bold weight/tight Montserrat tracking is inappropriate for its brush lettering. Existing FittedBox.scaleDown and Flexible still protect narrow headers. Drawer, welcome/body text, cards and other screens keep their configured fonts.
4. **How it works:** the pubspec family declaration maps SugarPie to the local TTF. Flutter bundles that asset, TextStyle selects its family alias, and both colored TextSpans inherit it. The internal font name is SugarPieW00-Regular; the alias does not have to match the internal name, but TextStyle and pubspec must match each other exactly. Example: `fontFamily: 'SugarPie'` selects the bundled file rather than downloading a Google Font. The existing FontLoader capture helper also loads the asset when dashboard screenshot captures are requested, preventing test screenshots from silently showing a fallback face.
5. **Backend/API:** unchanged. This is local asset/text styling, with no new network request, controller, route, data or permissions.
6. **Database/migration/deployment:** none. `flutter pub get` was run to refresh Flutter's asset configuration. A new bundled font requires stopping and running/rebuilding Flutter; hot reload alone may keep the old asset/font manifest. No additional package was installed or upgraded for this task. The normal debug APK build is verified separately below.
7. **Verification:** a standard-library SFNT/name-table check recognized the file as a TrueType/OpenType font, read family/style SugarPieW00-Regular/Regular and OS/2 weight400. Dart formatting and targeted analysis of DashboardScreen and its existing header test reported No issues found. `flutter build apk --debug --target lib/main.dart` passed (39.9 seconds); the normal APK is `campushub/build/app/outputs/flutter-apk/app-debug.apk`. The two existing Services-tab large-text/reduced-motion widget checks passed at320px and390px (`flutter test test/services_screen_test.dart --plain-name 'Services tab fits large text and reduced motion' --reporter expanded`). An APK ZIP check verified the SugarPie FontManifest entry and confirmed its129,796-byte TTF exactly matches the copied source (SHA-256 `524e3773576cba2df7fa3cb687be96e6fba592770c947c615b23c4dc68a8b5c7`). The full Home suite/physical phone was not used to claim the earlier unrelated10px layout issue fixed. No new native screenshot was taken for this font change.
8. **Limits/debugging/safe exercise:** if Montserrat still appears, confirm the TTF path, exact SugarPie alias and a full app restart after pub get. Do not change the global app theme to apply a wordmark-only font. In an isolated preview or disposable branch, try wordmark fontSize26, check that menu/Messages/bell remain visible at320px, then restore24. This teaches local typography scope and FittedBox behavior without changing accounts or records. Keep the supplied font file in source assets for other checkouts/builds; it is not ignored by Git.


## Simple Home naming and pill search - October 18, 2026

1. **Cause / reason:** user requested simpler file names, a search bar with fully rounded ends (50% radius appearance), and a contained filter icon to its right. Inspection also found an existing16sp welcome, which this change preserves. Initial tests confirmed unbounded Home section headings and service action text overflowed on narrow/large-text layouts; these were layout issues, not API failures.
2. **Exact files / current anchors:**
   - Rename `campushub/lib/module_app/screens/home_discovery_page.dart` to `campushub/lib/module_app/screens/home_page.dart:29` (`HomePage`); enum at18; `_showFilters` at125; scaled service width at262; search row at285; filter button at352; Showing/Reset at376; conditional catalog sections at394/420/447.
   - `campushub/lib/module_app/screens/dashboard_screen.dart:16` imports the new file; `:407` instantiates `HomePage`.
   - `campushub/lib/module_app/widgets/home/home_preview_cards.dart:54` (`HomeSectionHeader.build`) uses flexible heading/action widths; `:542` makes View service text flexible.
   - Rename `campushub/test/home_discovery_test.dart` to `campushub/test/home_page_test.dart:16` (new responsive filter tests); existing search and loading/error/empty checks remain at94 and156.
   - `campushub/test/dashboard_header_test.dart:115` and125 use renamed `home-scroll` key.
   - This guide, `CAMPUSHUB_CONTEXT.md` latest entry, `campushub/DESIGN.md` greeting/search/Reading Space Rule and `campushub/.impeccable/design.json` source/homeSearch metadata. Earlier guide references now point to the renamed source/test; earlier visual descriptions remain historical.
3. **Changes made:** renamed the class/state alongside the source, with no duplicate Home implementation. Search uses an OutlineInputBorder with a large clamped radius so the ends form a pill at any field height; it can grow with system text size. Beside it is a52dp white container with navy tune icon and8dp gap. It turns gold for an active category filter and exposes selected semantics. A visible Showing label and Reset communicate selection without color alone. The sheet has All/Marketplace/Facilities/Services ChoiceChips, accessible native controls, a close button, safe areas and scrolling for landscape/large text. Selecting applies and closes; dismissing preserves current selection. Responsive shared-heading/CTA fixes keep full labels wrapping, and service-card height/width accommodates scaled text.
4. **How it works / inputs and outputs:** `_showFilters()` removes keyboard focus and awaits an optional `_HomeFilter` result from the native modal sheet. A selection updates `_filter` only while the widget is mounted. Cancel returns null and changes nothing. `build()` shows the chosen catalog sections; existing `_matches(String)` continues searching actual record text using `_search`. `_load` and `_readProducts`/`_readFacilities`/`_readServices` keep their existing futures and API calls; choosing a filter never calls them again. Example: type Chocolate, choose Marketplace; only matching loaded products display. Choose Services and the same query is retained; Reset shows all catalogs without erasing the query. Clear search remains a separate action. Existing RetainedTab/PageController navigation continues preserving this state while tabs change.
5. **Backend / API behavior:** unchanged. Approved products, physical facilities and active service catalogs use their existing endpoints and permission rules. Filtering is local to records already fetched; it is not a new server-wide paginated search. No fake products or services are introduced; fixture records are test-only. See All still opens its existing destination.
6. **Database / migration impact:** none. No dependency or asset changes. Fully restart the running Flutter app after the source/class rename; no Django or migration command required. No new APK was built for this update.
7. **Tests performed / results:** final `flutter test test/home_page_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart test/dashboard_header_test.dart --reporter expanded` passed all11 tests. New filter cases cover375px,320px with2x text/dark theme/reduced motion, and844x390 landscape; they verify search preservation, selected state, reset, dismiss, non-overlapping controls,48dp minimum button target and unchanged catalog request counts. Existing tests cover catalog failure/Retry, empty states, drawer/retained search, all-catalog search beyond preview limits, native destinations and production-card layouts at320/390px and2x text. Targeted Dart analysis of source, Dashboard, shared cards and both changed tests reported No issues found. First runs exposed actual heading/CTA overflows; final successful run followed their fixes. A separate390px widget capture test passed; its screenshot confirms pill/button geometry and SugarPie brand, but GoogleFonts test loading emitted font-fetch warnings and body text used test glyphs, so it is not evidence of final native typography. No physical phone/emulator run or live transaction test was performed.
8. **Debugging / remaining limits / safe practice:** if an editor still shows the old file, close that stale tab and open home_page.dart; saving the old tab can recreate the obsolete source. Check Dashboard imports the new file before restarting. If a result seems missing, inspect both the search query and Showing label, then Reset and clear search. Filters cover catalog type only; they do not add price, availability or service-request submission rules. Practice safely with existing test fixtures: in home_page_test.dart choose Facilities instead of Services and assert Showing Facilities plus the same one-call counts. Run that test, restore the assertion, and manually check320px/large text without editing real records.


## White mobile surfaces - October 18, 2026

1. **Reason:** user requested white backgrounds and containers instead of gray on the recently updated mobile interface.
2. **Files/current anchors:** `campushub/lib/module_app/widgets/home/home_preview_cards.dart:25`, appBackground, and26, surfaceTint. Supporting palette/reference changes: `campushub/DESIGN.md` colors.light/image-surface; `campushub/.impeccable/design.json` surfacePalette and component preview backgrounds; `CAMPUSHUB_CONTEXT.md` latest white mobile surfaces; this guide and mobile-seller-application.md follow-up.
3. **Changes:** both shared surface constants now alias the existing white constant. This changes the Dashboard/Home background (also hosting Profile), seller introduction/form backgrounds, and Home product/facility/service image fallbacks to white. Existing white fields/cards remain white. Thin boundaries and readable navy/gold content remain.
4. **How it works:** DashboardScreen and SellerApplicationPage/Form read appBackground; preview cards read surfaceTint for image/fallback regions. Changing their shared inputs updates those rendered surfaces without local overrides or duplicate color logic. Example: a service without a saved image now has its existing navy icon on white instead of gray; its record and tap destination stay identical.
5. **Backend/API:** unchanged; no request or seller submission behavior changes.
6. **Database/migrations:** none. Hot reload Flutter; no package/server command needed.
7. **Verification:** targeted Dart analysis of shared cards, HomePage, DashboardScreen and both seller screens reported No issues found. No new widget tests, native screenshot, phone check or APK build for this reversible two-constant style change. Prior functional test results do not constitute new visual verification.
8. **Limits/debugging/practice:** this is scoped to shared Home surfaces and seller pages; unrelated modules with independent palettes are not a whole-app theme rewrite. If gray persists, inspect whether that widget consumes these shared tokens before adding overrides. Safe exercise: inspect one no-image fixture and confirm its fallback icon remains visible against white, then compare a recorded image; never replace a real image with a white rectangle. No live data change is needed.


## Marketplace category and seller names - October 18, 2026

1. **Reason:** user requested the category above the seller name and removal of the Seller: prefix from Home marketplace cards.
2. **Exact files/current anchors:** `campushub/lib/module_app/widgets/home/home_preview_cards.dart:270`, conditional product.category, and287, product.seller; `campushub/lib/module_app/screens/home_page.dart:248`, productHeight; `campushub/test/home_test_fixtures.dart:41` and51, test-only categories. Supporting documents: this guide, CAMPUSHUB_CONTEXT.md latest note and campushub/DESIGN.md Layout.
3. **Changes:** card order is product name -> price -> category -> seller name. Category uses a small plain-text line with no label or badge. Seller name keeps the existing secondary text style but loses the Seller: prefix. Removed the unsupported Campus seller fallback; absent seller data stays blank, and missing category does not produce a fake category. White surfaces, card actions and navigation remain.
4. **How it works:** ProductItem.fromJson already maps the real category and seller fields from approved products. MarketplacePreviewCard.build consumes those existing strings; it adds no query or category lookup. The Home productHeight formula now reserves two scaled metadata lines plus their gap so the new category does not overflow the fixed-height horizontal preview. Example: a real category of School Supplies and seller of Ana Student render as two separate lines, in that order. Test fixture category values are isolated rendering inputs, not production catalog rows.
5. **Backend/API:** unchanged. No serializer, endpoint, stock, favorite/cart, seller identity or product-detail logic changed.
6. **Database/migrations:** none. Hot reload Flutter; no server command, dependency or APK rebuild required.
7. **Verification:** `flutter test test/dashboard_header_test.dart test/home_page_test.dart test/dashboard_search_appbar_test.dart --reporter expanded` passed all9 existing tests, including production-card layout at320/390px and2x text, search/filter/retained navigation and empty/error states. Existing isolated fixtures now include categories to exercise the extra line. Targeted Dart analysis of shared cards, HomePage and fixtures reported No issues found. No new test case or physical-device screenshot was created for this small presentation update.
8. **Limitations/debugging/learning:** the change targets Home's MarketplacePreviewCard, not every unrelated product-list/detail layout. Long category/seller strings retain one-line ellipsis; opening product details still shows existing recorded information. If category is absent, inspect the actual API category field instead of adding sample text. Safe exercise: temporarily use a longer category in the existing test fixture, rerun dashboard_header_test.dart and verify no overflow at2x text, then restore the fixture. No real product data needs editing.
