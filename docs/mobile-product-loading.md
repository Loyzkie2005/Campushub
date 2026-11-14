# Mobile product loading and Django Wi-Fi connection

## Part 4: discovery labels and removal of fake sections - November 14, 2026

### 1. Cause / reason

Confirmed by reading the code before editing: Home used the old personal/popular titles and always rendered a subtitle. The active Marketplace tab repeated a first-four "Recently Added" grid and a "Recommended For You" grid that could fall back to `skip(4)` products. `ProductsScreen` also called its `skip(4)` rows popular without popularity data. Search already obtains personal results from the real recommendation endpoint, so its personal label can safely be changed.

Reachability was checked first: `profile_page.dart:462` constructs `ProductsScreen(favoritesOnly: true)` from Profile > Favorites. Dashboard and Seller Dashboard additionally use its static `showAddProductPage()` helper. The screen is therefore used, and its fake popularity section was removed. Its primary grid now receives all loaded visible products, preserving favorites after the fourth item.

Before editing, the `lib/` audit found Home's "Recommended for you" / "Popular on campus", Marketplace's "Recommended For You" and personal-recommendation empty-state sentence, Products' "Popular Products" and popular-products empty-state sentence, Search's "Recommended for You", and two "Recommended by Marketplace Admin" strings in `widgets/seller/seller_bundle_carousel.dart:70,219`. The last two describe separate seller functionality and were retained. API route strings, identifiers, storage keys and recommendation service methods were retained. This section supersedes the older Home label details in the report below.

### 2. Exact files changed / current lines and code anchors

Paths are relative to the repository root. The Flutter application is a nested Git repository; earlier unrelated changes were preserved. Task-start snapshots live under `scratch/recommendation-labels-20261114/*.before` for comparison.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/home_page.dart` | 228 title; 231 `if (personalized)`; 233 subtitle | Use "Picked for you" / "Popular now" and create the subtitle Text only for a personal feed. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 638 `_MarketplacePageState`; 833 `_fetchApprovedProducts`; 852 `build`; 895 `_buildProductsSection` | Remove the two extra Marketplace sections, their variables, recommendation state/loaders, unused `_PageTitle`, and secondary-section-only helper flag. Keep category filtering, refresh, error handling, full grid and ownership behavior. |
| `campushub/lib/module_app/screens/products_screen.dart` | 146 `_visibleApprovedProducts`; 190 `_buildProductsSection`; 313 `products: _visibleApprovedProducts` | Remove fake popularity and the first-four split; render every loaded favorite in the single remaining grid. Remove the secondary-section-only helper flag. |
| `campushub/lib/module_app/screens/search_page.dart` | 303 personal/recent heading | Rename only real personal suggestions to "Picked for you"; retain "Recently Added Products" for its existing fallback. |
| `campushub/test/home_recommendations_test.dart` | 64 titles; 68 subtitle | Update label assertions and verify the personal subtitle is absent for a popular feed. |
| `campushub/test/search_page_test.dart` | 119 no-history label; 157 personal label | Preserve real-recommendation vs. recent-fallback expectations with the new personal wording. |
| `campushub/test/home_product_ownership_test.dart` | 113 one-grid assertion | Verify Marketplace has one grid and neither deleted heading while retaining the existing ownership checks. |
| `campushub/test/product_discovery_sections_test.dart` | 11 Favorites regression | New isolated widget test with six saved products: one grid, no Popular Products heading, sixth favorite still reachable by scrolling. |
| `docs/mobile-product-loading.md` | 3 this Part 4 report | Document the source audit, removal, functions, data flow, testing and practice steps. |

### 3. Changes made

Home now shows "Picked for you" and "Based on your activity" when `feed.personalized` is true. Otherwise it shows "Popular now" without constructing a subtitle Text. Its key, placement, shared card builder, colors, typography and loading/empty/error behavior stay the same.

Marketplace no longer constructs "Recently Added" or "Recommended For You" sections. The `recentlyAdded` / `popular` local variables had no other uses. Its `_recommended` field and `_fetchRecommended()` / `_loadCurrentUserRecommendations()` methods only served the removed section, so those were removed too; the now-unused `_PageTitle` widget was removed. The active tab has category filtering and a product grid; a separate Filter button did not exist in this implementation, and no new filter behavior was added.

Products retains the existing page and primary section. Removing its second grid would otherwise strand rows after the first four, so the single grid receives `_visibleApprovedProducts` rather than a four-item subset. Unused `_recentlyAddedProducts` and `_popularApprovedProducts` getters were removed. Loading, Retry, Refresh, favorite filtering, product detail navigation and seller add-product access remain.

### 4. How it works / functions, inputs, outputs and data flow

- Home: `fetchRecommendedFeed(userId:)` still produces `RecommendedFeed(products, personalized)`. `_recommendedSection()` reads the boolean as its input and outputs the appropriate heading. The collection `if (personalized)` controls whether a subtitle widget exists; false creates no subtitle Text. It does not insert a blank text placeholder.
- Marketplace: `_fetchApprovedProducts()` reads the real approved-products endpoint, stores `_products`, and ends loading without an extra recommendation request. `_filteredCategoryProducts` uses the selected category to produce the grid input. `_buildProductsSection()` produces the existing loading, error, empty or grid state. The grid still passes `viewerRef` to its product cards. Home's recommendation request remains independent and unchanged.
- Favorites: the existing `_fetchApprovedProducts()` loads the approved catalog and reads persisted favorite keys. With `favoritesOnly`, it stores only matching rows in `_approvedProducts`. `_visibleApprovedProducts` exposes that full list; the single `_ProductGrid` renders it. Example: saved IDs 1 through 6 now all belong to the same six-item grid; IDs 5 and 6 no longer depend on a second section with a misleading popularity label.
- Search: `SearchPage.loadRecommendations` defaults to `ProductService.fetchSearchRecommendations()`, which calls `fetchRecommended(userId:, personalizedOnly: true)` at `/api/products/recommended/`. Search rejoins returned IDs to its current public catalog. A nonempty eligible recommendation list gets "Picked for you". Otherwise existing submission-date-sorted discovery gets "Recently Added Products". Only the heading text changed.

This approach removes misleading presentation and redundant requests while retaining the existing data sources and interactions. No ranking algorithm was modified in Part 4.

### 5. Backend / API behavior

No backend code or API contracts changed. Home, Search and product detail keep their existing recommendation calls. Only the removed Marketplace secondary section stops making its own recommendation request. Approved catalog loading, interaction tracking, authentication, ownership checks, permissions, purchase/payment and stock calculations are unchanged.

### 6. Database / migration impact

None: no models, migrations, dependencies or working records changed. Widget tests use mock HTTP and local in-memory preferences. Updated files preserve CRLF line endings.

### 7. Tests performed / troubleshooting and safe practice

Measured verification for this Part 4 change:

- `flutter analyze --no-pub`: **No issues found**, final run 9.8 seconds, exit 0. The earlier 70.8-second analysis also passed; final analysis followed removal of the obsolete section flags.
- Focused Flutter regression command: `flutter test --no-pub test/home_recommendations_test.dart test/home_page_test.dart test/search_page_test.dart test/home_product_ownership_test.dart test/dashboard_search_appbar_test.dart test/product_discovery_sections_test.dart`: **38 passed**, 8 seconds, exit 0. This includes personal/popular subtitle behavior, real personal vs. recent Search, one Marketplace grid with ownership protection, and access to the sixth saved favorite.
- Existing production-card render harness copied into the task's scratch directory: **1 passed**, 2 seconds, exit 0. It captured personal/popular Home in both app themes, using Dashboard's real white surface. The personal and popular captures were visually inspected: "Picked for you" has the short subtitle; "Popular now" has no subtitle line and cards follow directly below the header. The fixture harness is not imported by the application.
- Scoped `git diff --check` in the main and nested Flutter repositories: passed. All nine changed application/test/guide files were verified to contain CRLF line endings only, with no byte-order mark.
- Post-change search: only Home's actual "Popular now" and the separate seller attribution "Recommended by Marketplace Admin" remain as matching user-facing Popular/Recommended labels. Endpoint paths, service identifiers and Home storage/widget keys remain unchanged.
- The optional design token kit and web accuracy gate are absent from this installation; no token/accessibility score is claimed. No backend tests or full Flutter suite were rerun for this UI-only change. The previous full-suite results below belong to the earlier recommendation implementation, not this Part 4 run.

Verification logs, task-start snapshots and PNGs are stored in `scratch/recommendation-labels-20261114/`: `analyze-final.log`, `tests.log`, `render.log`, `light-personal.png`, `dark-popular.png` and the other two theme/feed combinations.

Troubleshooting: a missing personal heading can reflect an empty or failed optional recommendation result, so inspect the existing GET and account first. "Recently Added Products" in Search is intentional when no eligible personal results exist. Favorites loads only approved products with saved favorite keys; removing its popularity heading does not bypass that filter. If a removed heading is still visible after reload, check the running target and rebuild/hot restart the updated application.

Safe exercise: from `campushub/`, run `flutter test --no-pub test/product_discovery_sections_test.dart`. Its fixture stores six favorite IDs and returns six approved mock rows; verify it reports one six-item grid and can scroll to item six. Temporarily change the mocked response to five rows and observe the count assertion fail, then restore it and rerun. This changes test data only. Run `test/home_recommendations_test.dart` to verify that changing the fixture's `personalized` flag switches the title and removes the subtitle. Do not create working orders or artificial popularity records to test labels.

### 8. Remaining limitations

Part 4 changes labels and removes redundant sections only. The existing recommendation service still has the previously identified stock/popularity-window/mode-model gaps; those are not changed here. The seller-admin recommendation attribution is intentionally retained. A separate Filter button is absent from the current Marketplace implementation. Native signed-in device verification and a new full backend/full Flutter suite run are outside this focused UI change.

## Home recommendations with weighted history - November 14, 2026

### 1. Cause / reason

Confirmed in the previous implementation: all interaction types counted equally, history had no age cutoff, recommendations did not exclude the requesting mobile seller, and the endpoint returned no feed-source metadata. Home had no recommendation section. Confirmed environment issue during verification: the project virtual environment lacked scikit-learn despite its existing requirements entry, so the service always used its popularity fallback. The already-declared dependency was installed locally; requirements did not change.

### 2. Exact files changed / current lines and anchors

Paths are relative to the repository root. Lines refer to this update; anchors are more durable when nearby code changes.

| File | Line / code anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/modules/marketplace/services/recommendation.py` | 16 `INTERACTION_WEIGHTS`; 23 `_weighted_history`; 74 `get_recommendations`; 159 `get_recommended_products` | Weight recent behavior, exclude own products before ranking, report the source, retain the list-only interface. Empty vocabulary falls back safely at 67. |
| `backend/core/api/views.py` | 63 import; 2006 `products, mode`; 2017 `"mode"` | Call the richer service and add source metadata while retaining all previous JSON fields. Existing unrelated edits are preserved. |
| `backend/core/modules/marketplace/tests/test_recommendation_weights.py` | 17 `WeightedRecommendationTests`; 82 ownership/popularity-limit case | Add real TF-IDF, history, owner exclusion, fallback, wrapper and API regression tests. |
| `campushub/lib/module_app/services/product_service.dart` | 19 `RecommendedFeed`; 192 `fetchRecommendedFeed` | Add a typed optional feed without changing `fetchRecommended`. |
| `campushub/lib/module_app/screens/home_page.dart` | 32 `loadRecommended`; 74 `didUpdateWidget`; 96 `_recommended`; 197 `_catalogLoader`; 210 `_recommendedSection`; 318 insertion | Load and refresh optional data, start after async account loading, share the catalog loader, and insert the strip after banners. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 490 `loadRecommended: _user == null` | Enable the feed for the loaded account and pass its real mobile ID. |
| `campushub/test/home_recommendations_test.dart` | 16 `main`; 50 label tests; 218 service mapping | Test personal/popular titles, subtitles, order, See All, hidden failure/empty data, delayed account loading, refresh, large text and HTTP handling. |
| `docs/mobile-product-loading.md` | 3 this report | Explain the implementation, verification and troubleshooting. |

### 3. Changes made

Added purchase/click/view weights of 3/2/1. Interactions from the last 30 days receive a multiplier of 2; records older than 180 days do not seed recommendations. The five highest total product scores become seeds, with product ID breaking ties. Removed own products from eligible results before TF-IDF and popularity ranking. Candidate similarity is multiplied by each seed's accumulated weight, added across seeds, and sorted descending with ID ties. Seed products and nonpositive similarity are excluded from personal results.

Added `mode` and `personalized` to the existing response. Home uses the flag for its title/subtitle, shows up to six cards in the existing horizontal Marketplace layout, and sends See All to Marketplace. The API defaults to eight recommendations. Optional feed errors or empty results hide the whole section. The existing Marketplace, Facilities and Services behavior remains. Source files retain CRLF; no files were deleted.

### 4. How it works / functions, inputs, outputs and data flow

1. `DashboardScreen` passes a loader only when `_user` is loaded. Input is the existing mobile user ID; no account type or seller approval changes are involved.
2. `HomePage._load()` starts catalog futures and `_readRecommended()`. `_observed()` attaches an error observer for futures whose section may still be below the viewport. `didUpdateWidget()` starts the feed when the loader changes from absent to present after async account loading. Pull-to-refresh replaces the feed future without waiting for optional recommendations before ending the catalog refresh.
3. `ProductService.fetchRecommendedFeed(userId:, limit:)` sends a read-only GET with `user_id` when present and `limit`. It tries the existing configured server list, maps response `products` through `ProductItem.fromJson`, and outputs `RecommendedFeed(products, personalized)`. Only literal JSON `true` selects the personal label. Failed hosts, invalid JSON and HTTP errors eventually output an empty nonpersonal feed. `fetchRecommended()` and search callers retain their old interfaces.
4. Django `recommended_products()` parses the existing parameters and calls `get_recommendations()`. The service reads approved, unarchived products, excludes `mobile_seller_id == user_id`, and uses `_weighted_history(user_id)` to read `(product_id, interaction_type, created_at)` rows from the last 180 days. The helper outputs at most five `(product ID, weighted total)` pairs; seeds absent from the eligible catalog are then discarded.
5. TF-IDF uses the existing name/category/description text. Positive cosine similarity times seed weight accumulates into each candidate score. Outputs are `(products, "personalized")`, explicit-seed `(products, "similar")`, popularity `(products, "popular")`, or `([], "none")` for personal-only requests without scores or an empty catalog. `get_recommended_products(**kwargs)` returns only element zero for existing callers.
6. `HomePage._recommendedSection()` selects the label and reuses the exact same product-card builder, width, spacing and loader as Marketplace. It preserves the server's recommendation order rather than re-sorting by sales.

Annotated example with equally similar candidate products: one purchase of rice from 10 days ago contributes `3 * 2 = 6`; two noodle views from 10 days ago contribute `2 * (1 * 2) = 4`. If each candidate has cosine similarity 0.8 to its respective seed, rice scores `4.8` and noodles `3.2`. Different product descriptions can change the similarities, so a purchase alone does not guarantee a particular real product ranks first.

### 5. Backend / API behavior

`GET /api/products/recommended/?user_id=73&limit=8` retains `products`, `engine`, `user_id`, `seed_product_id` and `personalized_only`, and adds `mode` and `personalized`. Example metadata for actual personal results: `"mode": "personalized", "personalized": true`. Without usable positive similarity, normal requests use `"popular"` and false; `personalized_only=1` returns an empty list with `"none"` and false. Explicit seed behavior remains separate and does not claim personalization. Existing method handling and limit parsing remain unchanged.

Popularity still uses interaction counts and catalog fill; counts are restricted to eligible products before applying the limit so highly popular own/unapproved products cannot displace eligible popular items. This endpoint reads records only; purchase completion, payment, fulfillment, authentication, permissions, stock and other modules remain untouched.

### 6. Database / migration impact

No models, migrations or working business records changed. The service reads existing products and interactions. Tests use isolated temporary local PostgreSQL databases through the existing guarded QA runner. The declared scikit-learn dependency and its transitive dependencies were installed into `backend/core/venv`; no dependency manifest was edited.

### 7. Tests performed / troubleshooting and safe practice

Measured verification:

- Focused Django: **15 passed**, including all nine new weighted-history tests and the six existing search recommendation tests. Final rerun completed in 9.940 seconds. Both ranking cases execute real scikit-learn TF-IDF/cosine. The popularity-limit case confirms that a highly popular own product cannot displace the highest-ranked eligible item.
- Full Django `api modules.marketplace` labels, executed through the existing local PostgreSQL QA runner: **711 run, 25 failures, 10 errors, 1 skipped**, 537.377 seconds (675 successful tests). This is not a full-suite pass. Failed tests belong to facility rental configuration, admin orders, bundle monitoring/products, low-stock thresholds, variant/hybrid inventory and FIFO concurrency. Several order tests receive 401 where their fixtures expect successful order creation; no authentication/order fixture changes were made here. All recommendation/search cases passed in the full run. No pre-change full-suite comparison was run, so this report does not establish when the other failures began. Django system checks reported no issues.
- Full Flutter analysis: **No issues found** (`flutter analyze --no-pub`, 22.4 seconds).
- Focused Flutter: **24 passed** across `home_recommendations_test.dart`, `home_page_test.dart` and `product_loading_test.dart`.
- Full Flutter suite: **695 passed, 41 failed, 5 skipped**, 8 minutes 51 seconds. This is not a full-suite pass. The failure list contains authentication form/spacing, checkout/workflow, facility capture, order summary, product-detail, seller-form and seller-order tests. No Home, dashboard, product-loading or new recommendation test appears in that failure list. No pre-change full-suite comparison was run, so these results do not establish when the other failures began.
- Production-card render harness: **1 passed**, capturing four combinations (personal/popular, light/dark app theme), with the real Dashboard white surface and bundled Inter/icon fonts. The personal and popular section layouts were visually inspected. The initial harness used a generic dark Scaffold rather than Dashboard's actual surface; correcting that harness required no app style change.
- Scoped `git diff --check`: passed in both the main and nested Flutter repositories. Changed source/test/guide files were normalized to CRLF without a byte-order mark. No files were deleted.
- The design skill's token kit and `scripts/accuracy_report.mjs` are absent; no score or accessibility-gate pass is claimed. Signed-in device/manual order verification was not performed.

Logs use the `scratch/home-recommendations-` prefix. The optional production-card render harness is `scratch/home-recommendations/render_test.dart`; its `main()` builds real Home/cards around isolated `HomeTestCatalog`/product fixtures and saves four PNGs through `RenderRepaintBoundary.toImage()`. These remain test artifacts, never app data. Final Django structured results are written by the existing guarded runner under `scratch/user-summary-20261113/home-recommendations-*-results.json`.

Troubleshooting:

- Always popular despite history: verify scikit-learn imports in the server's actual virtual environment; restart an already-running server if needed. Check the interactions belong to the same mobile `user_id`, lie within 180 days, reference eligible products, and have positive text similarity to a different product. History alone is insufficient to claim personalization.
- No section: sign in, check the recommendation GET, then refresh Home. An empty/error optional feed intentionally disappears. A missing backend `personalized` field is treated as false by the new client.
- Slow optional data: each configured host has the existing six-second read timeout. The recommendation request runs independently of catalog requests and does not keep pull-to-refresh waiting, but the optional section can remain loading while hosts are tried.
- Unexpected seed order: sum all recorded rows, apply type weight and 30-day multiplier per row, then take the five strongest before filtering unavailable seeds. Popularity fallback still counts historical interactions according to the existing behavior.

Safe practice exercise: run `modules.marketplace.tests.test_recommendation_weights` in a temporary test database. In the fixture only, change the single rice purchase to a view; rerun the ranking case and observe its failure because two noodle views now outweigh one rice view. Restore the fixture and confirm the test passes. For mobile, run `flutter test --no-pub test/home_recommendations_test.dart` from `campushub/`; change the fixture flag from true to false to observe the title switch, then restore it. Do not seed example purchases into the working database.

### 8. Remaining limitations

This remains the existing TF-IDF/cosine engine, using name/category/description and a full catalog similarity matrix. It does not guarantee rice meals first for every real description. Only existing recorded interactions influence ranking; this task does not change when purchase events are recorded. Requests retain the existing `user_id` parameter contract. An in-place switch between two nonnull loader callbacks is picked up on refresh; normal Dashboard account arrival from null is handled immediately. Manual signed-in device verification has not been performed. The full suites have the Django failures/errors and 41 Flutter failures recorded above; this feature's focused checks pass. Broader failure diagnosis remains separate from this recommendation change.

Updated 2026-11-11. Scope: shared mobile API connectivity and physical Android product loading; business logic remains in Django.

## Current: add the missing Ethernet IP - November 11, 2026

### 1. Cause / reason

Confirmed: the PC's active gateway connection is now Ethernet 3 at `192.168.1.11`. The app still preferred `192.168.0.116`, and the current Ethernet address was missing from its fallback list. Wi-Fi currently has only a link-local address; it is not the previous working Wi-Fi connection. A read-only PC request to `http://192.168.1.11:8000/api/mobile/academic-options/` returned HTTP 200 with JSON. The phone's route has not been verified in this follow-up.

### 2. Exact files changed / current lines and anchors

| File relative to repository root | Current line / anchor | Change and reason |
| --- | --- | --- |
| `campushub/lib/module_app/config/api_config.dart` | 31, LAN comment; 35, `hostIp.defaultValue`; 43, `fallbackHostIps` | Prefer the verified Ethernet IP and include it in fallback candidates; retain previous addresses. |
| `campushub/test/api_config_test.dart` | 20, local address test; 25, `containsAll` | Extend the existing check to require the newly added IP. |
| `docs/mobile-product-loading.md` | 5, this current report | Explain the cause, data flow, checks and recovery. The earlier Wi-Fi report below is historical. |
| `CAMPUSHUB_CONTEXT.md` | 3, missing Ethernet IP note | Record the current verified address for future work. |

### 3. Changes made

Changed the local default from `192.168.0.116` to `192.168.1.11`, added the new IP to `fallbackHostIps`, and kept the old Wi-Fi IP. Updated the existing configuration test. No signup or seller-form changes are needed because they already use the shared configuration.

### 4. How it works / functions and data flow

`ApiConfig.hostIp` takes the compile-time `CAMPUSHUB_HOST_IP` input or the saved default. `baseUrl` outputs `http://<host>:8000`. `serverBaseUrls` supplies the remembered/default address followed by deduplicated fallback URLs; `mobileApiUrls` adds `/api/mobile`. `AuthService._post()` tries those URLs for signup/login and remembers a successful server using `recordWorkingBaseUrl()`. Existing services then use that shared origin. This small configuration change fixes the missing candidate without changing retry or account logic.

Example: default `192.168.1.11` -> `http://192.168.1.11:8000` -> read-only `http://192.168.1.11:8000/api/mobile/academic-options/`. A public build with `CAMPUSHUB_API_BASE_URL` still uses its HTTPS origin exclusively.

### 5. Backend / API behavior

Existing Django endpoints, permissions and business rules are unchanged. The connectivity check used only the academic-options GET; no signup or seller application was submitted. No server was started or restarted.

### 6. Database / migration impact

None: no schema, migrations, dependencies or business records changed.

### 7. Tests performed / troubleshooting and safe exercise

- Local `flutter test --no-pub test/api_config_test.dart`: **2 passed**, 4 online-only cases skipped as intended.
- HTTPS variant with `--dart-define=CAMPUSHUB_API_BASE_URL=https://campushub.example`: **4 passed**, 2 local-only cases skipped. The existing mock client prevents requests to the example domain.
- PC academic-options GET: HTTP 200 with `application/json` at the new IP.
- Targeted Git whitespace checks: no errors. Existing line-ending warnings are informational.
- Targeted `dart analyze lib/module_app/config/api_config.dart test/api_config_test.dart`: **No issues found**.
- Initial sandboxed Flutter/test and Dart-analysis commands produced no output and were interrupted; tests and analysis succeeded when run outside the sandbox.

To use the new default, stop and run the Flutter app again in VS Code; an existing APK must be rebuilt/reinstalled. Keep Django listening on `0.0.0.0:8000`. From the phone browser, open the academic-options URL above and confirm that JSON loads before retrying signup. If the PC succeeds but the phone fails, check that the phone can reach the PC's current network and that port 8000 is allowed; the phone-side cause is not yet confirmed. Do not create an account just to test transport.

Safe practice: inspect the active adapter IPv4 using `Get-NetIPConfiguration`. For a future temporary address, launch from `campushub/` with `flutter run --dart-define=CAMPUSHUB_HOST_IP=<verified-PC-IP>`. Verify the read-only GET first. Remove a stale launch override when returning to the saved default; it takes precedence over source defaults.

### 8. Remaining limitations

This is a saved development IP, not automatic discovery. Network/DHCP changes can require another update or launch override. No physical-phone request, app restart, APK build/install, signup or seller submission was performed in this follow-up. Historical verification below belongs to earlier work.

## Previous: mobile cannot reach a running Django server - November 11, 2026

### 1. Cause / reason

Confirmed: the laptop Wi-Fi IPv4 changed to `192.168.0.116`, while `ApiConfig.hostIp` still defaulted to `192.168.1.187`. The new address was absent from the app's fallback list. Signup uses that shared configuration through AuthService, so the signup screen can show Could not reach even when Django runs correctly on the laptop. The connected Infinix phone was `192.168.0.120:36595`; its initial ADB reverse list was also empty. Duplicate ADB transports were verified as the same physical phone by matching hardware serials; the existing connection helper already handles that case.

### 2. Exact files changed / current lines and anchors

| File relative to repository root | Current line / anchor | Change and reason |
| --- | --- | --- |
| `campushub/lib/module_app/config/api_config.dart` | 35, `hostIp.defaultValue`; 43, `fallbackHostIps` | Set the default to the observed Wi-Fi address and retain it among fallbacks when a build override is used. Keep the previous address as a historical fallback. |
| `campushub/test/api_config_test.dart` | 25, `containsAll` | Extend the existing configuration regression to require the current address alongside the existing development routes. |
| `docs/mobile-product-loading.md` | 5, this current report | Record the confirmed cause, exact files, functions/data flow, checks, recovery steps and safe exercise. |
| `CAMPUSHUB_CONTEXT.md` | 3, current mobile connection note | Preserve the new verified address and limitations for future work. |

Flutter has its own Git repository inside `campushub/`; its edits appear in `git -C campushub status`, separately from the parent Django repository. Existing user edits to other Flutter files were preserved.

### 3. Changes made

Updated the shared local development host and extended its existing test. Restored the connected phone's existing port-forward rules with `connect_android.py --device 192.168.0.120:36595`; the helper and VS Code tasks themselves were unchanged. No additional server was started, app data cleared or real account submitted.

### 4. How it works / functions, inputs, outputs and data flow

`ApiConfig.hostIp` reads the optional compile-time `CAMPUSHUB_HOST_IP`; without an override it now uses `192.168.0.116`. `baseUrl` produces `http://<host>:8000` for local builds. `serverBaseUrls` returns the preferred/remembered host plus deduplicated fallback hosts; `mobileApiUrls` appends `/api/mobile`. `SignUpScreen._signUp()` passes the existing form fields to `AuthService.signUp()`, whose `_post()` tries those mobile API URLs. A successful response is remembered through `recordWorkingBaseUrl()` for subsequent requests. Product and other shared mobile services use this same host configuration.

Annotated example: the new local base `http://192.168.0.116:8000` becomes the signup endpoint under `/api/mobile/` and the read-only academic endpoint `http://192.168.0.116:8000/api/mobile/academic-options/`. The latter can verify transport without creating an account. Online builds still use their explicitly configured HTTPS origin exclusively, without LAN fallback.

### 5. Backend / API behavior

Existing Django URLs, authentication, validation and permissions remain. PC loopback and Wi-Fi academic-options GETs both returned HTTP 200 with JSON. A direct request from the actual phone to the Wi-Fi endpoint returned `HTTP/1.1 200 OK`. No signup POST, credentials, email delivery, order or booking was used to test connectivity. Forwarding maps development ports only; it does not supply a missing Django or chat process.

### 6. Database / migration impact

None. No schema, migration, dependency-version or business-record changes. Flutter resolved the existing locked dependencies while running tests; no package upgrade was performed. The only device change was the existing development port mappings.

### 7. Tests performed / recovery steps

- Local `flutter test test/api_config_test.dart`: **2 passed**, 4 HTTPS-only cases skipped as intended.
- HTTPS variant with `--dart-define=CAMPUSHUB_API_BASE_URL=https://campushub.example`: **4 passed**, 2 local-only cases skipped. Tests use the existing mock client; no request was sent to that example origin.
- Existing connection-helper suite: **10/10 Python tests passed**.
- Targeted Dart analysis: no issues. Dart format check: two files, zero changes. Django `manage.py check`: no issues.
- PC GETs to both `127.0.0.1:8000` and `192.168.0.116:8000` academic-options endpoints: HTTP 200. Physical-phone direct Wi-Fi GET: HTTP 200.
- ADB reverse list after restoration contains 8000 and 8001. A phone loopback probe produced no HTTP response, so this session verifies the direct Wi-Fi route, not a working loopback HTTP route.

In the running VS Code Flutter session, use **Flutter: Hot Restart**, or stop and run the app again, then retry signup. A compiled default address cannot update an already-running build merely because the source file changed. Keep Django running on `0.0.0.0:8000`, and keep phone/laptop on the same Wi-Fi. A previously built APK must be rebuilt/reinstalled to embed the new default.

Re-run the relevant checks:

```powershell
# From campushub/
C:/flutter/bin/flutter.bat test --no-pub test/api_config_test.dart
C:/flutter/bin/flutter.bat test --no-pub --dart-define=CAMPUSHUB_API_BASE_URL=https://campushub.example test/api_config_test.dart
C:/flutter/bin/dart.bat analyze lib/module_app/config/api_config.dart test/api_config_test.dart
# From the repository root
backend/core/venv/Scripts/python.exe -B -m unittest discover -s campushub/scripts -p test_connect_android.py
```

Safe practice exercise: inspect the actual Wi-Fi IPv4 with `Get-NetIPAddress -AddressFamily IPv4`, then test `/api/mobile/academic-options/` from the phone browser before changing a host. For a temporary launch override, use `flutter run -d <actual-device-id> --dart-define=CAMPUSHUB_HOST_IP=<verified-PC-IP>` from `campushub/`. Confirm the GET succeeds; do not create a real signup just to test networking. Remove that override on the next normal launch if the saved default is correct.

### 8. Remaining limitations

The connected phone's real HTTP route was verified; signup creation/email delivery and a restarted app UI were not exercised. The default address remains network-specific: a future DHCP/network change requires a verified build override or the corresponding configuration update. Existing ADB forwarding is a development convenience and was not verified as a working HTTP path in this session. No firewall settings were changed. Chat forwarding is present but chat availability was not tested. Changes are local, not committed or deployed.

## App disappears during wireless development - October 18, 2026

### 1. Cause / reason: confirmed evidence and uncertainty

The physical Infinix X6873 initially had no active ADB transport. Reconnecting its advertised `192.168.1.169:33175` address succeeded later; the other advertised port refused connection. ADB disconnection alone does not prove an app crash.

Read-only Android `dumpsys activity exit-info com.example.campushub` showed a historical system kill with `Background clean scene memory high` / `process_mem_abnormal`, at background importance 400 and 351 MB PSS. The crash buffer separately held an earlier native `SIGABRT` in `mali-event-hand`, with a destroyed mutex and stack frames in the vendor `libGLES_mali.so`. These are two different recorded events; neither establishes that every later disappearance has the same cause. At investigation, the current app process was still alive, while Settings was in the foreground, with approximately 464 MiB PSS and 202 MiB GL tracking. During the updated phone run, logcat then captured a real unhandled `Chat service timed out` exception: Home called `unawaited(ChatService.instance.initialize())` without handling expected transport failures. The app PID remained alive during that observation, so the log alone does not establish a process-ending crash.

Confirmed application memory risk: public API product41's real image is4096x4096 (approximately64MiB for RGBA pixels). Two real facility images measured2048x1536 (12MiB) and3968x2976 (45MiB). `ProductImage` and the separate facility thumbnail helper previously decoded originals without size hints, even for small cards. Encoded file size is not decoded memory size. This fix reduces that risk; it does not claim to repair vendor GPU firmware or prove that the most recently reported exit has been reproduced.

### 2. Exact files / current lines / anchors

- `campushub/lib/module_app/widgets/product_image.dart:14`, `fallbackSize`; `:70`, `LayoutBuilder`; `:75`, `decodeExtent`; `:92`, `_buildImage`: size the existing shared image decoder to layout and physical screen pixels.
- `campushub/lib/module_app/screens/facility_screen.dart:368`, `_buildFacilityImage`; `:378`, `ProductImage`: reuse that bounded loader instead of a second full-resolution decoder. Preserve its44dp fallback icon.
- `campushub/lib/module_app/screens/dashboard_screen.dart:83`, optional startup call; `:86`, `_initializeChat`: handle expected ChatException only at the Home caller.
- `campushub/test/dashboard_chat_startup_test.dart:1`: offline-chat startup test, also confirming explicit service initialization still throws for Messages.
- `campushub/test/product_image_memory_test.dart:1`: isolated camera-size image fixture, actual decoded-size/aspect/memory assertion, network/inline sizing and fallback checks.
- This guide and `CAMPUSHUB_CONTEXT.md`: diagnosis, data flow, verification and limitations.

### 3. Changes made

Shared product/Home/Search/service/detail images now use `ResizeImage` with aspect-preserving `ResizeImagePolicy.fit`. Layout width/height are multiplied by device pixel ratio, rounded up to64px buckets, and capped at2048px per dimension. Unbounded dimensions also get the2048 cap. Network and base64 sources receive the same bound. Existing cover/contain presentation, URL resolution, loading and failure behavior remain. No originals, database images, catalogs or user data are resized/deleted. Facility list thumbnails reuse the same implementation and retain their icon/color/size. Home also handles the expected typed ChatException from optional startup, logging its existing error message; it does not swallow unexpected exceptions or change Messages error/Retry behavior.

### 4. Functions / inputs / outputs / data flow

`ProductImage.build(context)` resolves the existing backend URL, then `LayoutBuilder` receives the parent's display constraints. `decodeExtent(logicalExtent)` converts a positive finite logical size to a bounded physical-pixel hint, or returns null for an unbounded size. `_buildImage(resolved, width, height)` wraps the existing `NetworkImage` or decoded-byte `MemoryImage` provider in an aspect-preserving `ResizeImage`. Its output is the same Flutter Image widget with a smaller decoded bitmap. `_buildFacilityImage(imageUrl)` keeps existing source validation and delegates valid sources to this shared component.

Annotated example: a100dp square thumbnail on a1x display requests128px after rounding. The regression test decodes a real4096px fixture to no more than128x128 pixels, below100KiB of RGBA storage, instead of64MiB. On a3x phone, resolution follows the actual physical pixel requirement rather than forcing a blurry1x thumbnail. Large detail views retain a higher decode resolution, bounded at2048. Similar network card sizes share bucketed cache keys. Base64 bytes still use Flutter's existing memory-provider cache behavior; this change does not claim to deduplicate separately decoded byte arrays.

`DashboardScreen._initializeChat()` awaits the existing ChatService initializer and handles only ChatException at the optional Home boundary. It leaves cached conversations and authenticated session alone. Opening Messages still awaits the same initializer through its existing try/catch and visible error/Retry. Chat business logic/API remains in its existing service.

Flutter documents decode-size control as an image-cache memory technique: [ResizeImage API](https://api.flutter.dev/flutter/painting/ResizeImage-class.html). The vendor crash is separate; renderer options are documented in [Flutter Impeller guidance](https://docs.flutter.dev/perf/impeller). No renderer setting was changed based only on an old crash record.

### 5. Backend / API behavior

Unchanged. Django remains the source of products, facilities, services, inventory, authentication and permissions. Read-only public catalog/image GETs were used for dimension checks. The existing `connect_android.py --device` helper restored only development ports8000/8001 on the connected phone. No duplicate endpoint or revenue/booking logic was introduced.

### 6. Database / migration impact

None. No new package, migration, schema update, account deletion, app uninstall or app-data clearing. Existing login/cart storage remains unchanged. These source changes require rebuilding/rerunning the app.

### 7. Verification performed

- 46 Flutter tests passed across `product_image_memory_test.dart`, `dashboard_chat_startup_test.dart`, shared seller Home, Home, product loading, Search, Services and facility booking flow (`scratch/mobile-navbar/app-exit-image-tests.log`). The decoder test inspects actual image pixels and preserved aspect ratio, not only constructor parameters. A first test run incorrectly assumed1x while the test view used3x; explicitly setting/restoring test pixel ratio corrected the expectation without changing production sizing.
- Five-file Dart analysis: no issues (`scratch/mobile-navbar/app-exit-image-analysis.log`).
- Normal main.dart debug APK built successfully in 20.8 seconds after the chat fix (`scratch/mobile-navbar/app-exit-image-build.log`). Installed with ADB `install -r -t`, preserving existing app data; no uninstall or data clear. The earlier image-only process was intentionally replaced by this package update, not a spontaneous crash.
- Final physical-phone process PID21251 remained the same for more than203 seconds. Its log contained zero `Unhandled Exception` and zero `FATAL` lines; the unavailable chat server produced the handled diagnostic instead. Exit history showed only the intentional PACKAGE UPDATED events for the replaced builds. Evidence: `scratch/mobile-navbar/app-exit-native-check.json`. Home and Marketplace captures, including the4096px Adidas source rendered as a thumbnail, were inspected; saved login was still present. Facility navigation was not conclusively captured on-device; facility decoder reuse and booking behavior are covered by analysis/tests.
- This is a short foreground/navigation observation, not proof of permanent immunity to Android background cleanup or an old vendor-driver defect. No controlled before/after RAM benchmark is claimed. Scoped whitespace validation passed.

### 8. Remaining limitations / safe manual checks

Android can still stop background apps, and the earlier vendor-native graphics fault may recur independently. Debug-mode process overhead and other apps also contribute to memory. Do not globally suppress unexpected exceptions or disable Android cleanup, clear login data or claim Ctrl+F5 itself caused the crash. If another closure occurs, capture its new exit reason and app-specific crash log before changing renderer flags. Keep wireless debugging connected or use USB to retain diagnostics; the development port forwarding depends on that connection too.

Manual check: rebuild/run the normal `lib/main.dart` app, browse Home/Marketplace and Facilities including the large-image records, open product details, then switch away/back after several minutes. Confirm the image still looks correct, saved login/cart remain, and whether the PID survives. Compare memory only under comparable screens; old background and new foreground measurements are not a controlled benchmark.

Safe learning exercise: in the memory test only, change the displayed thumbnail width from100 to150 and inspect the expected physical decode bound. Run `flutter test test/product_image_memory_test.dart`; verify it still stays well below the original4096px allocation and preserves aspect ratio. Restore the fixture/expectation afterward. Do not modify real product images to run this exercise.

## Lost Android forwarding and automatic development reconnect - October 18, 2026

### 1. Cause / reason

Confirmed during this incident: Django listened on0.0.0.0:8000; PC Wi-Fi remained192.168.1.187, matching the Flutter default. PC GETs returned200 with6 public products,2 facilities and1 active service. The connected physical phone was192.168.1.169:33175. Its `adb reverse --list` was empty, and a direct phone-to-PC request to192.168.1.187:8000 timed out. Restoring the existing ADB route made all three catalog GETs return200 from the phone through127.0.0.1:8000.

The missing forwarding is confirmed; why direct Wi-Fi times out remains unconfirmed. No firewall restriction was inferred, no firewall settings were changed and no new IP guess was saved. ADB forwarding can disappear when the development/device connection restarts; the precise event that removed it was not observed.

### 2. Exact files / anchors

- `campushub/scripts/connect_android.py:9`, `find_adb`; line18 `adb_command`; line25 `main`: new small standard-library development helper.
- `.vscode/tasks.json:6`, `CampusHub: connect Android to Django`: process task using the existing Django virtual-environment Python.
- `.vscode/launch.json:10`, `preLaunchTask`: attach that task to the existing CampusHub debug/profile/release configurations only; leave the standalone Dart scripts configuration alone.
- This guide and `CAMPUSHUB_CONTEXT.md` latest connection note.

### 3. Changes made

Restored tcp8000 and tcp8001 forwarding on the actual connected phone. Added automatic restoration before VS Code starts the existing Flutter app configurations. The helper uses one authorized physical Android device, or an explicit `--device` serial. It skips when none/ambiguous phones are connected and rejects an invalid explicit serial. It never broadcasts forwarding to every attached device, installs software, clears app data or restarts the app/server.

### 4. Functions / inputs / outputs / data flow

`find_adb()` checks PATH then the already-installed Android SDK under LOCALAPPDATA; output is an existing executable path or None. `adb_command(adb, *arguments)` uses a literal argument array with `subprocess.run`, a12-second timeout, checked exit status and captured text; it returns stdout or raises a handled subprocess error. It does not invoke a shell.

`main()` accepts optional `--device`, reads `adb devices`, selects a single authorized physical phone, then sends `reverse tcp:8000 tcp:8000` and `reverse tcp:8001 tcp:8001` to that exact serial. It returns0 for successful forwarding or a clear skip,1 for an invalid explicit phone/command failure. VS Code's preLaunchTask calls this helper before Flutter launches. On retry, existing ApiConfig fallbacks include127.0.0.1; the phone forwards that local request to the existing PC Django listener, and the unchanged loaders parse the actual catalog response. A winning app request records the working URL in the existing process-local cache.

**Annotated example:** `adb -s <actual-serial> reverse tcp:8000 tcp:8000` means phone port8000 connects to PC port8000. It does not make127.0.0.1 a public production server and does not bypass login. Existing product/service/facility APIs and their real availability/approval logic still decide which records are returned.

### 5. Backend / API behavior

No Flutter UI, loader, API route, authentication, recommendation, stock or backend code changed. Verified GETs: `/api/products/approved/`, `/api/facilities/?resource_type=facility`, `/api/mobile/services/`. The Python helper is development tooling only. Django was already running and was not started a second time. The chat8001 mapping is restored, but no chat listener was found during this check; chat still requires its own FastAPI process to be running.

### 6. Database / migration impact

None. No production records changed, app uninstall/data-clear, migrations, dependency installation or APK rebuild. Existing logged-in app data remains untouched. The helper depends on the current workspace's existing backend/core/venv and installed Android SDK; update the task Python path if that environment is deliberately moved.

### 7. Verification performed

- Three PC requests: HTTP200, real catalog counts6/2/1 at investigation time.
- Direct phone Wi-Fi GET: timed out. Original forwarding list: empty.
- Restore and execute the new helper with the connected phone's explicit serial: successful; forwarding list includes8000 and8001.
- Three independent phone loopback GETs after restoration: **HTTP/1.1 200 OK** for Products, Facilities and Services.
- Python compilation succeeded. Isolated in-memory mock checks passed for no phone, multiple phones and invalid explicit serial, proving no port mutation is attempted in those cases. VS Code task JSON and all three preLaunchTask references validated.
- No Flutter/business-logic tests rerun because application code did not change. No authenticated purchase/profile request or phone screenshot was captured; HTTP200 confirms transport/catalog availability, not every screen's full workflow.

### 8. Remaining limitations / troubleshooting

Tap Retry or pull to refresh because an already-rendered failed Future does not automatically rerun when ADB forwarding returns. For Search inheriting failed Home futures, refresh Home or use Search's Retry. For retained Services/Profile tabs, use their existing refresh/retry controls. Invalid/expired-login messages require the existing sign-in flow separately.

The forwarding requires the phone's authorized USB/wireless-debugging connection to remain active. VS Code preLaunchTask runs on launch, not hot reload or a later device reconnection. If launching from a terminal or reconnecting mid-session, run the helper manually:

```powershell
& backend/core/venv/Scripts/python.exe campushub/scripts/connect_android.py
# For multiple phones, use the exact connected serial from adb devices:
& backend/core/venv/Scripts/python.exe campushub/scripts/connect_android.py --device <actual-serial>
```

For standalone installed-app use without debugging, the direct LAN/server connectivity still needs investigation. This fix restores the verified development connection; it does not claim the Wi-Fi timeout is resolved or silently alter Windows firewall/security.

**Safe practice exercise:** inspect `adb devices` and `adb reverse --list`, run the helper against your actual development phone, then inspect the forwarding list again and retry Home. Verify the three public catalog URLs return JSON through the phone's127.0.0.1:8000 route. Do not delete products or relax authentication to test connectivity. Read each function in the helper and identify which step discovers a device, which modifies only forwarding, and which returns a status to VS Code.

## Catalog recovery and current network - October 18, 2026

1. **Cause/reason:** during the in-progress Year / Section change, the updated CampusHubUser model was served before api.0040 ran. Products HTTP endpoint returned500 with that migration pending; after applying it the same endpoint returned200. Product owner joins now select the profile column, so completing the database step was necessary. Separately, observed PC Wi-Fi IPv4 is192.168.1.187, not the old app default192.168.0.122. Requests from the physical phone directly to the LAN address timed out. Python firewall rule details report **Allow**, so a firewall/router cause for that timeout is **not confirmed**; do not describe those rules as Block or change them based on that guess.
2. **Files/current anchors:** `campushub/lib/module_app/config/api_config.dart:13`, hostIp/defaultValue; fallback comments at23/26; `campushub/test/api_config_test.dart:16`, current/previous address and dedup checks. Related schema/API/profile files are listed in docs/mobile-profile.md Year / Section follow-up, especially `backend/core/api/migrations/0040_mobile_profile_year_section.py`. This guide and CAMPUSHUB_CONTEXT.md record the verified recovery.
3. **Changes made:** apply pending migration0040 locally; set current default host to observed192.168.1.187, retain previous/default/loopback addresses and CAMPUSHUB_HOST_IP override. Update stale configuration test to verify first-host preference, necessary fallback addresses and deduplication rather than an obsolete exact array. Reuse existing development loopback fallback, no duplicate catalog API or fabricated data.
4. **How it works:** Django model/schema consistency lets actual Product/owner queries succeed. Existing ProductService/FacilityService/ServiceCatalog send GETs through ApiConfig and cache a working address. For the connected Android device, enable existing ADB reverse forwarding for8000 and8001. A mobile127.0.0.1 request is forwarded through the active debugging connection to the PC's same local port. This is a development connection, not a permanent LAN/firewall fix.
5. **Backend/API verification:** PC loopback and LAN approved-products endpoint return200. LAN Facilities (`/api/facilities/?resource_type=facility`) and Services (`/api/mobile/services/`) return200 from the PC. Actual read-only HTTP GETs issued **from the connected phone** through127.0.0.1 ADB reverse returned `HTTP/1.1 200 OK` for all three catalogs. These probes verify transport/backend responses, not visual refresh of the installed app or authenticated profile submission. No catalog records were added/deleted.
6. **Database/deployment:** api.0040 applied successfully; no further migration required on this local database. Other checkouts need the checked-in migration before serving updated code. Current debug APK includes the new default address/Profile field and built successfully. Do not delete .dart_tool, clear accounts or fabricate catalog rows to fix a server500.
7. **Tests:** 37 focused Flutter tests passed, including API configuration/product loading and profile/seller flows;35 Django account/seller/profile tests passed. See `scratch/mobile-home/profile-year-mobile.log` and `profile-year-backend.log`. Targeted Dart analysis/Django check/migration drift check clean. See docs/mobile-profile.md for the new field's precise validation and result coverage.
8. **Remaining limits:** direct phone→LAN access remains unverified/timed out. The working route depends on the debugging connection/reverse rules; disconnecting it can make127.0.0.1 unreachable again. No firewall rules were modified. Chat port forwarding is configured, but no real chat exchange was tested. Existing catalogs can be genuinely empty;200 with empty arrays is a success, not a loading error. Current phone network was192.168.1.0/24; a future DHCP/network change requires checking the real PC address again or using the existing build override.

### Current recovery/manual steps

Pull to refresh or tap Retry in the installed app while Django and the debug connection are active. To reestablish the verified development route, use Android SDK adb against your currently connected device:

```powershell
& "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe" devices
& "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe" reverse tcp:8000 tcp:8000
& "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe" reverse tcp:8001 tcp:8001
```

If multiple devices are attached, pass `-s <the actual device serial>` before reverse. These commands create port forwarding only; they do not clear app data or log anyone in. Run Django as usual on0.0.0.0:8000 for LAN use; current server listener was verified on0.0.0.0. If the app reports an invalid/expired token for protected features, sign in again separately from catalog troubleshooting.

**Safe learning exercise:** in the existing product-loading test only, return500 from the mock server and confirm Retry/error rather than a fake empty catalog. Then return200 with an empty products list and confirm the legitimate empty result. Run that test and restore the mock. This separates backend failure, network transport and actual no-data states without editing production rows.

## 1. Cause / reason

Confirmed: Windows Wi-Fi IPv4 was `192.168.0.159`; the connected Infinix phone was `192.168.0.154`. The app default still pointed to `192.168.1.187`, and the current PC address was absent from the fallback list. Three catalog loaders tried eight old addresses sequentially, each with a five-second timeout. That could keep the spinner visible for roughly 40 seconds. It was not evidence of an infinite loop.

Django was verified running during investigation. The current PC endpoint returned two products in about 660ms, and a read-only HTTP request from the phone returned `HTTP/1.1 200 OK`. Do not infer that an empty catalog or stock calculation caused this failure.

## 2. Exact files changed

| File | Current line / nearby anchor | Purpose |
| --- | --- | --- |
| `campushub/lib/module_app/config/api_config.dart` | 13, `defaultValue` | Use observed PC Wi-Fi address; preserve previous address as a fallback. Existing `CAMPUSHUB_HOST_IP` build override stays supported. |
| `campushub/lib/module_app/services/product_service.dart` | 9, `ProductLoadException`; 24, `fetchApproved`; 98, `connectionMessage` | Shared bounded catalog loader, response validation, first-success fallback and actionable error. |
| `campushub/lib/module_app/screens/products_screen.dart` | 80, `_fetchApprovedProducts` | Reuse the shared loader; clear loading in `finally`; keep existing Retry/empty UI. Remove unused HTTP/JSON imports. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 398, `_fetchProducts`; 474, `_DashboardProductsPreview` | Home preview shares loader and shows a connection error plus Retry instead of silently hiding a failed request. |
| Same dashboard file | 1341, `_fetchApprovedProducts`; 1361, `_loadCurrentUserRecommendations` | Products tab shares loader. Optional recommendation/user lookup no longer delays catalog loading or pull-to-refresh. Remove unused HTTP import. |
| `campushub/test/api_config_test.dart` | 5, chat URLs; 16, API addresses | Update assertions to the configured address and preserved fallbacks. |
| `campushub/test/product_loading_test.dart` | 1, `void main` | Six meaningful loader regression tests with controlled HTTP responses/timeouts. |
| `docs/mobile-product-loading.md` | 1 | This implementation, debugging and learning guide. |

## 3. Changes made

Replaced the three repeated sequential catalog loops with one reusable service. The current/last working address gets a two-second attempt. If that fails, remaining read-only requests run concurrently, each limited to five seconds. The first valid catalog wins; an empty `products` list is a valid success. If all fail, the service throws a retryable error after approximately seven seconds of network waiting, rather than adding a timeout for every host.

Only the winner updates the cached address. Late responses cannot overwrite it. A service-created HTTP client closes in `finally` to cancel losing requests. Screens also clear their loading flag in `finally` and check `mounted` before updating widgets. Injected clients are caller-owned, for tests; production creates/closes its own client.

## 4. Functions, inputs, outputs and data flow

`ApiConfig.serverBaseUrls` outputs the last known working address first, then the configured address and deduplicated legacy fallbacks. `ProductService.fetchApproved` accepts optional client/address/timeouts for isolated tests; normal screens call it without arguments. It returns `Future<List<ProductItem>>` or throws `ProductLoadException`.

Inside `fetchApproved`, `load(baseUrl, timeout)` sends GET `/api/products/approved/`, validates HTTP success and a JSON `products` list, then uses existing `ProductItem.fromJson` to convert rows. Non-JSON, malformed rows and HTTP errors do not become fabricated empty catalogs.

```dart
try {
  final products = await ProductService.fetchApproved(); // Real Django records.
  // Screen stores products and rebuilds its existing cards.
} catch (_) {
  // Show the existing Retry UI with a connection explanation.
} finally {
  // Always stop the spinner when this attempt finishes.
}
```

Flow: screen -> API configuration -> bounded HTTP loader -> existing Django approved-products endpoint -> database eligibility/stock serialization -> ProductItem -> existing product cards. Recommendations remain a separate optional task; their failure does not erase the successfully loaded catalog.

## 5. Backend / API behavior

No backend views, permissions or routes changed. `backend/core/api/views.py:713`, `approved_products`, still selects approved, unarchived, unexpired, marketplace-available products and serializes actual variant/bundle inventory. No fake products or stock were introduced. Fallback concurrency is only used for this read-only catalog request, never checkout or other writes.

## 6. Database / migration impact

None. No schema migrations, order/stock changes, account resets or new production records. Replacing the Android app uses an update installation, not uninstall/data clearing.

## 7. Verification and manual tests

Completed during implementation:

- PC GET of the current Django catalog: two real products, approximately 660ms.
- Phone-to-PC GET via the connected phone's shell: `HTTP/1.1 200 OK`.
- `flutter test test/product_loading_test.dart test/api_config_test.dart test/product_item_test.dart`: 9 tests passed.
- Loader tests cover preferred host, real empty response, stale/hanging hosts, all hosts offline, malformed JSON/HTTP errors and late-response cache protection.

- Targeted `flutter analyze` on the four changed application files and both tests: no issues found after removing unused imports and fixing braces.
- `flutter build apk --debug --dart-define=CAMPUSHUB_HOST_IP=192.168.0.159`: succeeded; output `campushub/build/app/outputs/flutter-apk/app-debug.apk`.
- Re-ran all nine targeted tests after the final style corrections: all passed.
- `adb -s 192.168.0.154:45315 install -r .../app-debug.apk`: succeeded on the connected Infinix phone. The app was launched afterward; no uninstall or data-clear command was used.
- Visually verified the installed app's Home screen: both real products (Adidas and USTP Uniform), prices and uploaded images loaded. Phone screenshot: `scratch/mobile-product-review.png` (local review artifact only).
- Opened Marketplace on the installed phone app and visually verified `2 items`, both product images/prices and Recently Added. Screenshot: `scratch/mobile-marketplace-review.png`. The original stuck-loading condition was not present in either verified screen.

Manual verification:

1. Keep Django bound to the network: from `backend/core`, run `venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000` if it is not already running. Do not start a second instance on the same port.
2. Connect phone and PC to the same Wi-Fi. From the phone browser, visit `http://192.168.0.159:8000/api/products/approved/` and verify JSON appears.
3. Open CampusHub Home and Products. Real catalog rows should appear; retry/pull-to-refresh should finish.
4. For a controlled local test, stop your development server and refresh. A connection explanation and Retry should replace the spinner within roughly seven seconds of network waiting. Restart the server and Retry.
5. A real empty catalog should show the existing empty state, not a connection error. Do not delete production products to test this; the empty-response unit test covers it safely.

## 8. Limitations, troubleshooting and safe practice

A private Wi-Fi address can change. This fix does not discover arbitrary new networks automatically. If the PC address changes, use `ipconfig` and rebuild with the observed PC address:

```powershell
cd campushub
flutter run -d <phone-device-id> --dart-define=CAMPUSHUB_HOST_IP=<PC-WIFI-IP>
```

Use the PC address, not the phone address. A physical phone cannot reach the PC using its own `127.0.0.1`; emulator loopback `10.0.2.2` applies to the Android emulator. Merely running Django on `127.0.0.1` does not expose it to Wi-Fi. Compile-time `--dart-define` changes require a rebuild/full restart; refreshing the UI cannot update an already installed build.

If the phone browser cannot reach JSON, check server binding, same Wi-Fi, Windows network access and the actual IP before modifying parsing or stock code. If JSON loads but the app fails, verify the installed APK/configuration, then run the loader tests. Detailed error categories currently share one user-facing retry message. Other services retain their existing fallback/retry behavior; they were not refactored in this product-loading fix.

Safe practice: read the hanging-host unit test and predict which address wins. Add one additional hanging fallback inside that test only, rerun `flutter test test/product_loading_test.dart`, and verify the working host still wins without waiting through every failed address. Undo the extra test address afterward. This teaches asynchronous recovery without editing production records or disabling access controls.
