# Mobile product loading and Django Wi-Fi connection

Updated 2026-10-08. Scope: physical Android product loading; no marketplace business logic moved out of Django.

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
