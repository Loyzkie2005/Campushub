# Regular-user mobile Profile

Updated October 19, 2026. The newest section supersedes older default-photo and main-header Edit Profile descriptions. Earlier feature history is retained below.

## Seller preview callback compatibility fix - October 19, 2026

1. **Cause / reason:** The isolated seller drawer QA target still passed `onEdit` to `ProfileIdentityHeader`. The current constructor requires `onChangePhoto` instead, producing both named-parameter diagnostics.
2. **Exact files / line / anchor:** `campushub/tool/qa/seller_drawer_preview.dart:67`, `ProfileIdentityHeader`, with `onChangePhoto` at70; this guide records the fix. The production constructor is in `lib/module_app/widgets/profile/profile_widgets.dart:203`.
3. **Change:** Replace the obsolete callback name with `onChangePhoto: () {}` and explain that the preview never opens a picker or uploads. Keep its explicitly isolated fixture and existing drawer/profile layout.
4. **How it works:** The preview builds the actual production header with its fixture `AuthUser` and a valid `VoidCallback`. Pressing the preview pencil invokes that empty callback and returns without side effects. Production Profile continues passing its real photo-change handler; no widget compatibility alias or duplicate header is added.
5. **Backend / API:** Unchanged; the QA target performs no account/photo requests or writes.
6. **Database / migration:** None.
7. **Verification:** Dart formatting reported no change; direct analysis of `tool/qa/seller_drawer_preview.dart` reported no issues; scoped `git diff --check` passed. Initial sandbox checks could not access Dart/package caches; the same static commands completed after approved cache access with analytics suppressed. No app/test run, build, install, restart, reload or device command was performed.
8. **Remaining limitations:** The preview pencil intentionally has no photo workflow; validate uploads only through the existing production Profile flow. No visual/runtime claim is made for this callback-only fix.

**Safe learning exercise:** Use Go to Definition on `ProfileIdentityHeader`, compare its required named parameters with the preview call, and find `VoidCallback` on `onChangePhoto`. Changing the caller to match the constructor resolves both diagnostics. Run `dart --suppress-analytics analyze tool/qa/seller_drawer_preview.dart` in a user-controlled static-check session; this need not launch the app or edit real accounts.

## Profile picture edit icon and working upload - October 19, 2026

### 1. Cause / reason

The user requested an edit icon on the Profile picture and removal of the separate Edit Profile button, then explicitly chose working uploads saved to Django. Inspection confirmed that the header only drew a default person icon: neither `CampusHubUser` nor `AuthUser` had a photo field, and there was no photo picker or upload endpoint. Moving the existing Edit Profile callback onto a pencil would still open the academic/contact form, so it would not change a picture. This change adds the complete photo path instead.

### 2. Exact files changed and code anchors

Paths below are relative to the repository root. Line numbers refer to this implementation; search the named anchor if later changes move them.

| File / current line | Anchor and change |
| --- | --- |
| `campushub/lib/module_app/widgets/profile/profile_widgets.dart:202` | `ProfileIdentityHeader`: replace `onEdit` with `onChangePhoto` and `changingPhoto`; at285 add the 48dp gold pencil button over the avatar. Remove the separate header Edit Profile button. Render the actual URL with a circular crop and default fallback; `_DefaultProfilePhoto` at370 keeps missing/broken images honest. |
| `campushub/lib/module_app/screens/profile_page.dart:61` | `_load` / `_refreshProfile` at77 refresh the actual account while retaining cached identity on connection failure. `_savePhoto` at198, `_changePhoto` at220, `_recoverPhoto` at258 handle selection, ownership, upload, progress and Android recovery. The header is wired at389. Remove the obsolete `_edit` route/import; Personal Information still opens the existing profile-editing form. |
| `campushub/lib/module_app/services/profile_photo_service.dart:14` | New `ProfilePhotoService`: `load(token)` at18 fetches the current profile; `upload(token, bytes)` at28 sends one multipart request; `_user(response)` at57 checks status/JSON and returns `AuthUser` or a readable exception. |
| `campushub/lib/module_app/services/auth_service.dart:27` | Optional `profilePhotoUrl`, empty for old accounts/sessions; getter `resolvedProfilePhotoUrl` at50 resolves relative media paths against the working Django server. JSON mapping at78. |
| `campushub/lib/module_app/session/session_service.dart:31` | `_encodeUser` persists `profile_photo_url` alongside the existing account details. Updating the photo does not replace the login token or remember-login preference. |
| `backend/core/api/models.py:38` | `CampusHubUser.profile_photo`: optional ImageField storing a file path, not image bytes. |
| `backend/core/api/migrations/0042_mobile_profile_photo.py:4` | `add_profile_photo`: guarded physical-column addition for the existing unmanaged mobile-account table, plus matching migration state. |
| `backend/core/api/profile_photos.py:13` | New `normalize_profile_photo(upload)` verifies actual image contents and returns a small metadata-free JPEG. |
| `backend/core/api/views.py:130` | `serialize_campushub_user` adds the saved media URL at151. `mobile_profile_photo` at691 implements the authenticated read/upload flow, row lock, image save and commit-time cleanup. |
| `backend/core/core/urls.py:36` and175 | Import and register `mobile_profile_photo` at `/api/mobile/profile/photo/`. |
| `campushub/pubspec.yaml:43` and48; `campushub/pubspec.lock` | Add image_picker 1.2.3 and the 2.11.1 platform test interface, with resolved transitive packages. The 1.2.4 resolution attempt was incompatible with this project's Dart 3.10.1; Flutter itself was not upgraded. Existing dependency versions were retained. |
| `campushub/ios/Runner/Info.plist:27` | Add the photo-library purpose string for choosing a profile picture. No camera feature was added. |
| `campushub/windows/flutter/generated_plugin_registrant.cc:9`; `campushub/windows/flutter/generated_plugins.cmake:6` | Flutter-generated file-selector registration needed by the desktop photo picker. |
| `campushub/linux/flutter/generated_plugin_registrant.cc:9`; `campushub/linux/flutter/generated_plugins.cmake:6`; `campushub/macos/Flutter/GeneratedPluginRegistrant.swift:8` | Matching Flutter-generated desktop file-selector registration. These are generated dependency outputs, not manually authored account logic. |
| `campushub/test/profile_photo_test.dart:19` | Test picker plus eight checks for cancellation, one authenticated multipart upload, server rejection/permission failure, oversize input, disabled repeated taps, same-owner Android recovery, other-owner discard and legacy sessions. |
| `campushub/test/profile_page_test.dart:103`,177,213 | Assert the main-header button is removed and photo action exists. Existing edit tests now open Personal Information and scroll its ListView to Edit Profile. The optional capture loads bundled Poppins as well. |
| `backend/core/api/test_profile_photos.py:25` | Six isolated backend tests for authentication/active status, ownership, saved-file normalization, replacement cleanup, invalid input, save failure cleanup and empty/transparency behavior. |
| `docs/mobile-profile.md`; `CAMPUSHUB_CONTEXT.md` | This implementation report, deployment/debugging guidance and current project context. |

### 3. Changes made / expected behavior

On Profile, tap the gold pencil at the lower-right edge of the picture. The system gallery opens. Cancel leaves the picture unchanged. Selecting an image disables repeat taps and shows progress until the server accepts or rejects it. A successful response updates the displayed photo and saved session; reopening/refreshing Profile fetches its current Django account. The existing name, account type, program, year/section and email layout stays in place. Personal Information retains its own Edit Profile control for academic/contact fields.

### 4. How it works: functions, inputs/outputs and data flow

`_changePhoto()` takes a gallery selection from `ImagePicker.pickImage`, following the [Flutter image_picker documentation](https://pub.dev/packages/image_picker/versions/1.2.3). It requests a 1024px maximum side and 85 quality without full metadata. `_savePhoto(XFile, owner)` checks the file length and verifies that the session still belongs to that owner, then passes bytes and the existing bearer token to `ProfilePhotoService.upload`. One POST is sent to the working Django origin; a timeout is not automatically retried because the server may already have saved the photo.

`mobile_profile_photo(request)` resolves the authenticated mobile account using the existing bearer helper. It never selects the owner from submitted IDs. `normalize_profile_photo(upload)` accepts JPEG/PNG/WebP contents up to5MiB and20 million pixels; missing, corrupt, unsupported and animated inputs produce400. It applies EXIF orientation, preserves aspect ratio within512x512, uses white behind transparency and encodes a fresh JPEG without source metadata. The endpoint writes a UUID filename under `profile-photos/<owner-id>/`, saves its path under a row lock, and returns the actual serialized account. The previous file is deleted only after database commit; failed database saves clean up the newly written file. Cleanup failure is logged rather than breaking an accepted update.

`AuthUser.fromJson` reads `profile_photo_url`; `SessionService.updateUser` preserves it across app restarts. `ProfileIdentityHeader` resolves the media path, clips it to the existing circle and bounds image decoding to256px width without stretching its aspect ratio. An empty or failed image uses the original person placeholder. Version checks prevent an older profile refresh from overwriting a just-selected photo. On Android, a pending picker result can be recovered after activity destruction only for the saved original owner; another account's pending selection is discarded.

Annotated example (test data only): a multipart field named `photo` contains real PNG bytes. Django stores a normalized JPEG, then returns a value shaped like `/media/profile-photos/<actual-user-id>/<generated-name>.jpg`. Flutter resolves that relative path using the same server reached during login. No sample URL or picture is inserted into a real account.

### 5. Backend / API behavior

- GET `/api/mobile/profile/photo/`: bearer token required; returns `{ "user": ... }`, including a blank photo URL when none is saved.
- POST to the same route: multipart field `photo`; returns200 and the updated user after acceptance,400 for invalid files,401 for missing/invalid login,403 for inactive/suspended accounts. Other methods return405. Caller-supplied owner/role/contact fields do not change account identity or permissions.
- Responses disable caching. Login and existing profile-completion responses also include the new optional photo URL through their shared serializer. Actual media files use the project's existing media storage/serving configuration; the photo upload/read-account route is authenticated, while media URLs follow existing media visibility.
- Marketplace, seller approval, bookings and FastAPI chat responsibilities remain as before. A photo upload does not grant seller access or change an account type.

### 6. Database / migration impact and activation

Migration `api.0042_mobile_profile_photo` was applied successfully to the local PostgreSQL database. Its reviewed plan contained only the new optional photo field and the unmanaged-table guard. Existing accounts start blank; no real user's picture or other profile values were changed during verification. The reverse operation conservatively retains the physical column/data, matching the earlier unmanaged-table migration approach.

For another environment, apply `python manage.py migrate api 0042` before serving the updated model. Ensure configured media storage is writable and media files are served by that environment. The app now includes a native plugin, so **a full app stop and run/rebuild is required when the user is ready**; hot reload alone cannot register the new photo picker. No app run, restart, build, install or device interaction was performed during this task, preserving the user's active Ctrl+F5 session.

### 7. Tests performed and troubleshooting

Confirmed results: 24 focused Flutter tests passed across `profile_photo_test.dart`, `profile_page_test.dart` and `profile_academic_test.dart`; 14 Django tests passed across `api.test_profile_photos` and `api.test_mobile_seller_application`. The existing edit tests initially failed because they still targeted the removed main-header button, then because the Personal Information page contains multiple scrollables; they now target that page's outer ListView and pass. This was a test-route adjustment, not a removal of contact editing. Django system checks passed during the test runs, and `makemigrations --check --dry-run` reported no changes. Seven-file Dart analysis returned No issues found; source formatting was checked.

Rendered widget preview inspected: `scratch/profile-photo-review/profile-top.png` (375x812 logical phone size, rendered at2x). It shows the avatar pencil, missing main-header Edit Profile button and preserved real-field layout. These are test fixtures/widget renders, not native-device or live-account upload evidence. Responsive tests cover320px with2x text,375px, landscape844x390 and tablet768px with1.5x text.

| Symptom | Confirmed checks / next step |
| --- | --- |
| Picker unavailable after a hot reload | The native dependency needs a full stop/run. This was not automatically performed. |
| Login/profile requests mention a missing profile_photo column | Apply api.0042 to that database before running the updated backend. |
| File rejected | Use a still JPEG/PNG/WebP up to5MiB; backend validates contents, not just extension. Choose a smaller image when its pixel count is too large. |
| Upload times out | Refresh Profile first to check whether Django saved it. Automatic POST replay is deliberately absent. Then check phone-to-Django connectivity. |
| URL saved but avatar shows the placeholder | Check the actual media URL, working server origin, media-server configuration and file availability. The placeholder alone does not prove that saving failed. |
| Permission denied | Allow photo access in device Settings and try again. Cancellation requires no permission change. |
| Edit Profile no longer appears under the picture | Expected. Open Personal Information and scroll to its existing Edit Profile button for contact/academic editing. |

Safe practice exercise: in `profile_photo_test.dart` only, make the fake picker return `null` and run `flutter test test/profile_photo_test.dart`. Verify no POST occurs, the existing session remains and the pencil is enabled again. Then inspect the oversize fixture and its zero-POST assertion. Restore any experimental fixture changes. This teaches why cancellation is distinct from an upload error without changing live user data.

### 8. Remaining limitations

The native phone/gallery/permission flow, real device process-death recovery, iOS and desktop builds were not exercised. Gallery selection is supported; camera capture, a crop editor and a remove-photo command were not requested or added. HEIC is not accepted directly by the backend; it works only if the picker supplies a supported converted format. The circular profile display crops the saved image visually. Shared-header and seller-drawer initials retain their existing presentation; this request changes the Profile picture. Photo persistence is stored in Django, but cached image bytes can still be unavailable offline. No full-project test-suite success or deployment verification is claimed.

## White Profile surfaces - October 18, 2026

1. **Cause / reason:** user requested a white Profile background. The confirmed light-gray source was the shared `ProfileStyle.background` token.
2. **Exact files / anchors:** `campushub/lib/module_app/widgets/profile/profile_widgets.dart:8`, `static const background = Colors.white`; `campushub/test/profile_page_test.dart`, identity/Personal Information assertions. This guide and the latest section in `docs/mobile-services-navigation.md` record the coordinated Home/Search changes; `CAMPUSHUB_CONTEXT.md` preserves the preference.
3. **Changes made:** replace #F7F8FC with white. Main Profile, themed detail pages and default avatar surface inherit white. Existing identity cover, navy/gold text/icons, thin borders, account/seller/navigation actions and saved information remain.
4. **Functions / data flow:** `ProfilePage.build` paints its outer ColoredBox from the shared token. `ProfileTheme.build(child)` supplies the same token as `scaffoldBackgroundColor`. `ProfileDetailScaffold.build` uses that theme around its Scaffold; a null explicit Scaffold background correctly resolves to this inherited white value. Inputs remain the existing child/account state, output is the same widgets with white surfaces. No new profile fields or requests.
5. **Backend / API behavior:** unchanged, including profile editing and seller-access queries.
6. **Database / migration impact:** none. Hot reload; no APK rebuild or native installation for this color follow-up.
7. **Tests performed:** all31 coordinated Profile/Home/Search/header/navigation widget tests passed. Six-file targeted Dart analysis returned No issues found; scoped whitespace check passed. Log: `scratch/mobile-navbar/white-search-profile-tests.log`. Assertions cover the main surface and effective themed Personal Information surface. No new screenshot/device run.
8. **Remaining limitations:** the navy identity cover remains a branding element; white applies to page/avatar surfaces. Existing unsupported-policy notices, device-local order history and account workflows retain their prior documented limitations.

**Safe practice / debugging:** inspect the shared constant before changing an individual page. Temporarily set it to a different neutral in development, observe Main Profile and Personal Information both inherit it, then restore white. Run `flutter test test/profile_page_test.dart` and verify edit/back/session behavior still passes. No live profile data needs changing to test the palette.

## Year / Section and separate program lines - October 18, 2026

1. **Reason:** user requested a saved Year / Section and separate account type/program text. Previously the header joined Student and the actual program, and only SellerRequest had an application-specific course_section. That application field is not a profile record and was not repurposed or used as a fake fallback.
2. **Files/current anchors:** `backend/core/api/models.py:37`, CampusHubUser.year_section; `api/views.py:149`, serializer, and624/661/670, mobile_complete_profile validation/save; new `api/migrations/0040_mobile_profile_year_section.py`, add_year_section; `api/test_mobile_seller_application.py:55`, optional-profile-field test. Flutter: `campushub/lib/module_app/services/auth_service.dart:26/46/69/137/148`, yearSection model/parsing/POST; `session/session_service.dart:30`, local persistence; `screens/profile_setup_screen.dart:25/48/87/168/554`, controller/prefill/dispose/submit/field; `screens/profile_details_pages.dart:55`, Personal Information; `widgets/profile/profile_widgets.dart:270/282/294`, separate header lines; `test/profile_page_test.dart`, position and saved-value assertions. This guide/context updated. The accompanying catalog recovery also changes api_config.dart/api_config_test.dart; see docs/mobile-product-loading.md.
3. **Change / expected behavior:** name → account type → actual program on its own line → saved Year / Section for students → email. BFPT is shown only when it is the user's recorded program; BSIT/BTLED/other actual values use the same widget. Year / Section is optional in Edit Profile's contact step and displayed in Personal Information. Hide the header line while blank rather than invent a year/section. Non-students do not see the student-specific field/header line.
4. **Functions/data flow:** AuthService.completeProfile accepts optional yearSection, sends trimmed year_section through the existing authenticated API, Django validates a string of at most120 characters and saves it on the same mobile account. serialize_campushub_user returns it; AuthUser.fromJson maps it and SessionService._encodeUser persists it for app restart. Existing Profile edit-mode pop/reload updates the header. Program and account-type fields/permissions remain separate.
5. **API compatibility:** existing POST `/api/mobile/profile/complete/` reused. Missing year_section preserves a previously saved value for old clients; an explicit empty string clears it. Invalid types or overlong text produce400 before saving. No new route or profile/controller duplicate. Name/email and academic validation remain existing behavior.
6. **Migration:** api.0040 is applied locally. CampusHubUser is unmanaged, so follow the existing0037 migration pattern: AddField updates migration state, guarded RunPython adds the column to the existing table only when needed. Existing account values default blank; no example values were inserted. On other environments apply checked-in migrations **before serving the updated model**, restart Django, then rebuild/run the app. Reverse follows the existing conservative pattern and retains the physical column/data.
7. **Verification:** 35 Django tests passed (`api.test_mobile_seller_application accounts.test_user_management`, log `scratch/mobile-home/profile-year-backend.log`); cover trim/save/response, omitted old-client preservation, explicit clearing and invalid/overlong values. 37 Flutter tests passed across Profile, academic form, seller flow, API configuration and product loading (`scratch/mobile-home/profile-year-mobile.log`), including separate vertical positions and saved year/session payload. Eight-file targeted Dart analysis clean; Django check clean; makemigrations check found no changes. Actual rendered Profile PNG inspected in `scratch/mobile-home/profile-year-review/profile-top.png`. Normal main.dart debug APK built successfully, log `profile-year-apk.log` (39.9s Gradle task).
8. **Limits/troubleshooting:** existing accounts have no year value until edited; no inferred year from Student ID/Program/seller application. Old installed APKs ignore the new JSON field, so install the updated app for the new input/lines. Expired login still requires sign-in. The field is free text because no configured academic year/section master exists; it does not enforce an invented format. No live user profile was modified for verification. The following earlier report describes the initial redesign before this follow-up.

**Annotated example (test-only):** a mocked student's program is BSIT and year_section is2-A. Header shows Student, then BSIT, then Year / Section:2-A on three lines. Editing it to3-B sends year_section with the existing token; the mocked backend result is persisted and the updated header appears. No BFPT/year value is hardcoded in the widget.

**Safe practice:** in profile_page_test.dart only, change the mocked program to BFPT and year_section to a longer class label. Rerun its responsive test and check both lines wrap without overflow. Restore the fixture afterward. For backend learning, inspect the test's omitted-year request: it demonstrates why data.get('year_section', user.year_section) preserves old clients' existing data.

## Cause / reason and design decision

The old Profile showed detailed identity/contact fields, a role badge, Marketplace rows and order cards together. It used older blue tokens and did not have the requested account/navigation hierarchy. The replacement keeps the real session and seller state while moving details and saved orders to their own destinations.

Design read: a calm university account page, preserving CampusHub's Flutter/Material controls, navy #1A1851, gold #FCB316, Montserrat and flat surfaces. A 128dp navy cover and overlapping 96dp avatar establish identity; grouped white navigation cards provide the requested hierarchy. Gold is limited to the wordmark and actual unread counts. Profile uses the requested #F7F8FC light page background, even when the surrounding app has a dark theme; it does not rewrite the global theme or bottom navigation.

Applied ui-ux-pro-max for Flutter text scaling, safe areas and touch targets, frontend-design-codex for local tokens/component reuse/visual verification, and the applicable preserve-brand/audit guidance from design-taste-frontend. The latter's marketing-page/React defaults do not fit this existing Flutter account page and were not imposed. Existing brand/specification dictated the design, so no generated artwork or stock images were needed.

## Required implementation report

### 1–3. Exact files, current locations and nearby anchors

Paths are relative to the project root. Search anchors if later edits shift line numbers.

| File | Current approximate line / anchor | What changed and why |
| --- | --- | --- |
| `campushub/lib/module_app/screens/profile_page.dart` | 17 ProfilePage; 49 `_load`; 59 `_refreshSeller`; 85 `_openSeller`; 120 `_edit`; 130 `_confirmLogout`; search section titles | Replace detailed main-page fields/orders with profile header and grouped navigation. Preserve exact seller-state flow, retained-tab refresh, session and logout. Clear stale seller state after a failed refresh rather than present old approval as current. |
| `campushub/lib/module_app/widgets/profile/profile_widgets.dart` | 5 ProfileStyle; 22 ProfileTheme; 63 ProfileSection; 116 ProfileNavRow; 183 profileAccountType; 191 ProfileIdentityHeader; 300 ProfileDetailScaffold | Shared scoped tokens/theme, reusable grouped rows/chevrons, actual identity summary and compact destination scaffold. Explicit variable-font weights preserve Montserrat hierarchy. |
| `campushub/lib/module_app/screens/profile_details_pages.dart` | 11 ProfileInformationPage; 35 PersonalInformationPage; 109 AccountSecurityPage; 179 ProfileOrdersPage; 271 ProfileAppSettingsPage; 300 ProfileFaqPage; 335 ProfileProblemPage; 421 ProfileAboutPage | Minimal destinations required by the supplied specification; reuse current account recovery, order history, theme preference, logo and actual profile data. Honest messages where backend/configuration is absent. |
| `campushub/lib/module_app/screens/profile_setup_screen.dart` | 11 `editingUser`; 36 initState; 92 `_handleBack`; 185 edit-mode return; 406 program key; search major key and Save Changes | Optional edit mode on existing form/API. Prefill real institutional/contact/academic values, keep account type, return after saving; Back does not log out. Dropdowns wait for matching master options before selecting prefilled IDs, preventing a loading-time assertion. Onboarding behavior remains the default. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 425 `onMessages`; 426 `onNotifications` | Pass existing dashboard handlers into Profile; retain the same Messages screen and Notifications notice. |
| `campushub/test/profile_page_test.dart` | search test names, PROFILE_REVIEW_DIR | Functional/route, edit persistence, logout, honest unsupported states, local report copy, responsive tests and optional rendered PNG capture. Fixtures stay in tests. |
| `scratch/mobile-home/inspect_seller_cleanup.py` | SellerRequest inspection | One-time read-only status/link inspection, without printing applicant names/contact details. |
| `scratch/mobile-home/remove_requested_seller_application.py` | transaction.atomic / requests.delete | One-time user-authorized removal of the inspected rejected record, exact ID/status/count guards and protected record-count verification. Not an application feature or deployment command; do not rerun it. |
| `docs/mobile-profile.md`; `CAMPUSHUB_CONTEXT.md` | this guide / latest Profile note | Current behavior, functions/data flow, actual cleanup, evidence, limitations and practice exercise. |

### 4. Existing widgets/services reused

AuthUser and SessionService, HomeAppColors, SellerApplicationService, SellerApplicationPage/Form/DashboardPage, ProductsScreen Favorites filter, CartScreen, MessagesPage, AccountRecoveryDialog, ProfileSetupScreen, OrderService, ThemeService and the existing app logo. No new account, repository, authentication mechanism, product logic or seller approval API.

### 5. New UI components

ProfileStyle/ProfileTheme scope the screen's existing brand values. ProfileSection groups rows once per section; ProfileNavRow supplies a consistent icon/title/subtitle/chevron/touch target and optional real unread count. ProfileIdentityHeader displays current user data; ProfileDetailScaffold provides reusable, scrollable destination pages capped at 640dp. Main page gutters are 16dp, group spacing 24dp, minimum row height 60dp and controls at least 48dp.

### 6. Profile header

128dp navy cover, existing CampusHub wordmark colors, 96dp circular default avatar with white border, real full name, account type/program where present, actual email and outlined Edit Profile. Inspection found no mobile profile-photo/cover fields or upload API in AuthUser/CampusHubUser, so use the required fallback user icon and simple banner, without fabricating images or creating upload fields. Detailed ID/contact/major fields are absent from the main header.

### 7. Account

Personal Information reads the actual AuthUser, displays available fields and hides missing/inapplicable Major. Missing expected Student Program shows Unassigned; no invented year/section field. Edit Profile reuses ProfileSetupScreen and AuthService.completeProfile. Name/email stay display-only because the existing profile API edits institutional/contact/academic information, not those fields. Account & Security reuses the actual email verification and owner email/code password-reset dialog; it does not add a direct password override or fabricated security features.

### 8. Shopping & Selling

Exact title SHOPPING & SELLING; My Orders opens saved order history, Favorites opens ProductsScreen(favoritesOnly: true), My Cart opens existing CartScreen. Seller row appears only for regular accounts. Main Profile no longer embeds order cards or a product grid. Existing saved order options/customizations/quantity/total are retained in My Orders.

### 9. Seller state

No application → Apply to Sell / Sell products on CampusHub. Pending/Needs Revision/Rejected/Suspended → Seller Application with real state. Approved → Seller Dashboard / Manage products and sales. Never show Apply and Dashboard together. Failed/unknown status has retry guidance, not a fake rejection or permission. Existing guarded flow remains authoritative; returning to Profile reloads saved user/current seller state.

### 10. Communication

Messages invokes the same Dashboard handler and real MessagesPage. AnimatedBuilder listens to existing ChatService conversations; count is the sum of actual unreadCount values and is omitted when zero. No extra chat polling/API is introduced. Notifications invokes the existing honest mobile-unavailable notice; there is no mobile notification feed or unread source to invent. Standalone Profile has equivalent fallback navigation/notice for tests and direct embedding.

### 11. Settings & Privacy

App Settings changes the existing ThemeService light-mode preference, persisted under its existing key; no new settings repository. Profile remains intentionally light per the supplied palette. Privacy & Data and Terms & Conditions open minimal, selectable information explaining that official policy text is not available in the mobile app and referring to the campus office. No legal policy or acceptance history was invented. These are honest informational destinations, not claims that formal policy publishing is complete.

### 12. Help & Support

Four distinct rows: Frequently Asked Questions, Contact Support, Report a Problem, About CampusHub. FAQ answers derive only from existing verified behavior: seller approval, cash on pickup, Facilities/Services navigation and expired-token sign-in. Contact Support does not invent an email/phone number when none is configured. Report a Problem validates category/description and copies a report to the clipboard for sharing through an official channel; it explicitly sends nothing, has no Submit button, and makes no API call. About uses the existing logo and project/institution names; version is omitted because no runtime version provider exists.

### 13. Logout

Separate restrained red Log Out control below the groups, with no chevron. Existing confirmation → disconnect ChatService → clear SessionService user/token/remember flag → remove old routes and open AppRoutes.login. Cancel preserves the session. Existing cart/favorite/order storage policy is unchanged; this task does not redefine cross-account local-storage retention.

### 14. Existing routes/controllers

The project uses Navigator/MaterialPageRoute, AppRouter, PageController and retained tabs, not GetX. Keep them. Profile's active prop and dashboard callbacks remain. No bottom-nav item/order change: Home, Marketplace, Services, Facilities, Profile. No Facilities/Services section was added to Profile.

### 15. Backend/API behavior

No production Python/API file changed. Existing GET seller status and guarded application/product workflows remain; editing uses existing authenticated POST `/api/mobile/profile/complete/`. Profile detail pages do not submit new applications or support tickets. Email actions use existing owner verification/code APIs. A token-expiration error still requires sign-in; this redesign does not implement token refresh or silently extend token lifetime.

### 16. Database impact and actual cleanup

**No migration.** Before deletion the database contained one rejected SellerRequest, ID 2. Inspection found zero linked Products. Within one transaction the cleanup rechecked the exact ID/status and total application count; deletion returned exactly `{'api.SellerRequest': 1}`. It asserted unchanged CampusHubUser, accounts.User, Product, MarketplaceOrder and AccountActivity counts. SellerRequest count afterward: **0**. User accounts, products, orders and audit history were preserved. No sample records, replacement applicants or approvals were inserted. This was explicitly requested data deletion, not a schema migration or automatic behavior of opening Profile.

### 17. Commands

No Django migration/dependency command. Stop/restart Flutter or install the rebuilt normal debug APK from `campushub/build/app/outputs/flutter-apk/app-debug.apk`. From the app directory:

```powershell
C:\flutter\bin\flutter.bat run -t lib/main.dart
```

Do not rerun the one-time cleanup script; it is guarded for the already-deleted original row and will fail its precondition now. If testing the application again, submit a genuine authorized test application through the normal flow rather than populating a sample status.

### 18. Responsive / visual verification

Real Profile widgets tested at 320×812/2x text, 375×812, 844×390 landscape and 768×1024/1.5x, with long names/emails, reduced motion and a dark host theme. No overflow exceptions; main Profile is vertically scrollable with safe-area handling and bottom-nav architecture preserved. Screenshots of actual widgets with isolated mocked session/API data were rendered at 375px using bundled Montserrat/Material icons and visually inspected: `scratch/mobile-home/profile-review/profile-top.png` and `profile-bottom.png`. They are QA fixtures, not production sample users. No browser URL applies to this Flutter widget verification. No new emulator/iPhone/physical-phone run or live email delivery was performed.

### 19. Functional tests and results

Final command from campushub:

```powershell
C:\flutter\bin\flutter.bat test test/profile_page_test.dart test/seller_application_test.dart test/profile_academic_test.dart test/dashboard_header_test.dart test/home_page_test.dart --reporter expanded
```

**37 tests passed**, including 13 Profile tests and 24 existing seller/profile-academic/Home regressions. Log: `scratch/mobile-home/profile-final-tests.log`. Profile coverage includes full grouping/concise identity, personal details, prefilled edit/back preserving login, exact authenticated edit POST/saved session/new token/return to Profile, saved orders, existing owner recovery, communication callbacks without fake badges, persisted theme preference, honest terms content, report validation/clipboard without POST, logout Cancel/confirm and responsive cases. Targeted analysis of five changed production files plus the new test reported **No issues found**. Normal `flutter build apk --debug --target lib/main.dart` succeeded (15.2s Gradle task), log `scratch/mobile-home/profile-apk.log`. Django system check found no issues and scoped git diff whitespace checking passed. No claim is made that the entire repository test suite or a live physical-device workflow was run.

## Function inputs/outputs and data flow

```text
SessionService.loadUser() → ProfilePage._load() → AuthUser header/details
SellerApplicationService.status() → _refreshSeller() → one dynamic seller row
row tap → existing callback or MaterialPageRoute → destination
Edit Profile → existing ProfileSetupScreen(editingUser)
  → completeProfile(token, institutional/contact/academic values)
  → Django validates/saves → updated user + token
  → SessionService.updateUser() → Navigator.pop(user) → Profile reload
ChatService ChangeNotifier → current unread sum → visible count only if positive
logout confirmation → existing disconnect/clear → existing login route
```

Example (test-only): saved Ana Student/BSIT is displayed once in the header; Student ID and phone are inside Personal Information. Editing contact sends the existing account's bearer token and actual Program ID to completeProfile. Its returned user replaces local session data, its returned token is persisted, and the form pops to Profile instead of running onboarding navigation. Test fixtures never create live accounts.

Why this approach: the new hierarchy removes duplicated fields and long order content from the main page, while shared rows/styles prevent inconsistent cards. Extending the existing profile form avoids a duplicate validation/API path. Explicit unavailable states prevent fake policies, contacts, notifications and support submissions.

## Debugging, manual checks and remaining limitations

1. Restart/install the normal app; open Profile. Confirm identity, exact five group labels and separate logout. There should be no Facilities/Services group, KPI, order grid or role badge.
2. Personal Information → Edit Profile: verify prefilled academic/contact values. Back must return while still signed in. Save an authorized change and verify persisted values; server validation still owns academic relationships/ID uniqueness.
3. After the requested cleanup, an eligible signed-in user with no request should see Apply to Sell. Complete a real test application only when authorized; pending/approved/revision labels must come from Django. Invalid/expired token means sign in again, not application rejection.
4. Check Messages opens the existing screen and only real unread counts appear. Notifications currently gives the existing unavailable notice.
5. My Orders is **the pre-existing device-local saved history**, not a newly connected authoritative server-order API. It can include locally stored attempts; this redesign does not change that existing behavior. Do not claim backend order synchronization from this page.
6. Official policy content, verified support contacts, mobile notification feed, photo/cover upload and report submission backend remain absent. Current rows explain these limits honestly; Copy Report is a local preparation action. Name/email editing and year-level data are not invented.
7. If academic dropdowns are empty, check existing academic-options API/loading/error first. Prefilled IDs are only selected once matching options exist. An unrelated SMTP/network error is not a Profile layout problem.
8. Test large text/landscape on your physical phone; logout Cancel keeps the session, confirm removes it. The agent did not verify physical-device navigation, real email verification/password reset or live edit submission in this step.

## Safe practice exercise

In `test/profile_page_test.dart`, lengthen only the mock full_name/email and rerun the responsive tests. Verify no RenderFlex overflow and that Logout remains reachable by scrolling; restore your fixture edit. Next change the mocked seller status from none to pending and assert Seller Application/Pending Review appears while Apply to Sell does not. This teaches service data → UI state without editing real applicants.

To learn form reuse, follow editingUser from ProfilePage._edit to ProfileSetupScreen.initState and _finish. Compare the edit branch (pop updated user) with default onboarding (verification/dashboard flow). Add a test-only assertion that returning with Back keeps SessionService.loadUser non-null; run the test and restore your exercise. Never test cleanup by rerunning the deletion script against live data.
