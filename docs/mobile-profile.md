# Regular-user mobile Profile

## Floating navbar: remove rectangular backing strip - November 4, 2026

### 1. Cause / reason

User clarified that the unwanted rectangle was the strip behind the floating navbar, not the rounded white pill. The previous tap-feedback update did not address that strip. Confirmed cause: the root Scaffold used its default `extendBody=false`, ending page content above the entire bottomNavigationBar slot and leaving the Scaffold surface across the reserved bottom rectangle.

### 2. Exact files changed / current lines and anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/dashboard_screen.dart` |362 `extendBody`;744 Marketplace list padding | Extend root content behind the dock; add the framework-provided bottom inset to Marketplace's existing24dp scroll padding. |
| `campushub/lib/module_app/screens/home_page.dart` |221 `home-scroll` padding | Add the measured bottom inset to existing32dp padding so final Home sections can scroll clear of the dock. |
| `campushub/lib/module_app/screens/services_screen.dart` |68 list padding | Existing24dp plus measured bottom inset. |
| `campushub/lib/module_app/screens/facility_screen.dart` |74 list padding | Same clearance for Facilities without changing its cards/data. |
| `campushub/lib/module_app/screens/profile_page.dart` |386 SafeArea bottom flag;396 scroll padding | Move bottom clearance into the scroll content instead of shrinking its viewport. Retain existing32dp padding plus inset. |
| `campushub/test/dashboard_center_add_button_test.dart` |23 root/viewport/padding checks | Verify actual Dashboard extends behind the dock, reserves clearance inside the scroll content, and retains a fixed dock while scrolling. |
| `campushub/test/floating_bottom_navbar_test.dart` |461 capture Scaffold;466 alternating test sections | Render extended content behind the actual dock to expose any opaque strip in the rest/press/scroll captures. |
| `campushub/test/profile_page_test.dart` |156 Personal Information font expectation | Align the old Poppins expectation with the unchanged current AppTypography font; no production typography change. |
| This guide, `docs/mobile-seller-application.md`, `CAMPUSHUB_CONTEXT.md` | Latest navigation entries | Record clarified scope, measured checks, functions/data flow and safe exercise. |

### 3. Changes made

The white rounded floating pill, its border/shadow, gold center action, icons, labels, tap behavior and fixed position remain. Page content now paints behind the pill and its surrounding gaps, removing the reserved rectangular backing strip. All five root destinations retain bottom scroll clearance; their final rows can scroll above the dock. Existing no-tap-box behavior remains.

### 4. How it works / functions, inputs, outputs and data flow

`DashboardScreen.build` sets `Scaffold.extendBody=true`. Flutter extends its body viewport under the bottomNavigationBar and supplies the bar's measured height through the body's MediaQuery bottom padding. Each root list uses `basePadding + MediaQuery.paddingOf(context).bottom`; this is space at the end of scroll content, not an opaque fixed container. Profile's bottom SafeArea is disabled so that same inset is applied once through its scroll padding. Its surrounding page surface still fills the viewport.

Example: Home retains its original32dp bottom spacing and adds the current dock inset. The visible list reaches the screen bottom behind the pill, while scrolling to its end moves the final content above the pill. Changes in seller configuration, text scale and system-safe-area size use the framework's actual measured inset rather than a hardcoded navbar height. Inputs remain the same selected root tab, seller access, real content and callbacks; outputs are layout only.

### 5. Backend / API behavior

Unchanged. No navigation destination, authentication, seller permission, data load, product action, service/facility workflow or API contract changed. No duplicate navbar or screen was created.

### 6. Database / migration impact

None. No working records, models, migrations, environment or server settings changed. Verification used existing isolated Flutter fixtures.

### 7. Tests performed

- **70/70 targeted Flutter tests passed in21 seconds**, covering actual Dashboard geometry/scrolling, Home, Services, Profile, floating navbar, system navigation, header/search and existing resource cards. The navbar capture case was explicitly enabled. Command from `campushub/`: `flutter test --no-pub --dart-define=CAPTURE_FLOATING_NAV=true test/dashboard_center_add_button_test.dart test/home_page_test.dart test/services_screen_test.dart test/profile_page_test.dart test/floating_bottom_navbar_test.dart test/system_navigation_surface_test.dart test/dashboard_search_appbar_test.dart test/dashboard_header_test.dart test/resource_catalog_cards_test.dart`.
- Whole-app `flutter analyze --no-pub`: **No issues found in27.6 seconds**. Dart formatting completed. Initial broader tests exposed one obsolete Profile-font assertion; its expectation was updated to the existing theme token, preserving runtime typography.
- Twelve actual regular/seller rest/pressed/scrolled widget captures generated under `scratch/floating-navbar-background-20261104/renders/`. Inspected390dp seller and844dp landscape scrolled renders. Alternating colored Section rows are test-only content used to show the page continuing behind/outside the real white pill. Root integration tests independently assert `extendBody`, actual Home viewport overlap and measured bottom padding. Evidence log: `final-tests.log` in the same scratch folder.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device, deployed-session or full-project-suite result is claimed. The rounded white pill is intentionally retained; only its rectangular backing region is removed. The dock remains visible while scrolling. Separate detail/form routes keep their current navigation. Hot-restart if an older root Scaffold persists. Safe exercise: scroll each root tab, inspect content behind the dock's side/bottom gaps, and scroll to the final item to verify it clears the pill. Do not submit products or modify working records to test layout.

## Floating navbar: no tap box, visible while scrolling - November 4, 2026

### 1. Cause / reason

User confirmed removing the tapped-item box and keeping the floating navbar visible during section scrolling. The shared widget already had no persistent selected-background box, but its InkResponse configured a bounded splash with a rounded-rectangle border. The Dashboard already mounts the navbar outside page scroll content as `Scaffold.bottomNavigationBar`; no scroll-hide controller exists on that path.

### 2. Exact files changed / current lines and anchors

| File relative to project root | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` |179–184 standalone action;237–243 tabs;340–345 embedded center action | NoSplash, transparent touch/hover/highlight paint and circular keyboard-focus shape. Preserve the nonzero keyboard focus color. |
| `campushub/test/floating_bottom_navbar_test.dart` |280 scrollable sections;308 feedback checks;318 scroll checks;464 preview sections;488 `captureDock` | Extend existing component tests for scrolling up/down, fixed position, actual clickable tabs and rest/pressed/scrolled captures. |
| This guide, `docs/mobile-seller-application.md`, `CAMPUSHUB_CONTEXT.md` | Current navigation entries | Record implementation, data flow, checks and safe exercise. |

Inspected, unchanged: `campushub/lib/module_app/screens/dashboard_screen.dart:464`, its unconditional existing bottomNavigationBar. No root-page or scroll-controller change was needed to preserve visibility.

### 3. Changes made

Tapping a destination or Add Product no longer paints a temporary rectangular background. Selected destinations retain their filled icon/navy text and subtle icon movement; no replacement selection box was added. The white rounded floating dock, inset spacing, gold center circle, original dimensions/targets and responsive geometry remain. Circular keyboard-focus feedback remains. The dock stays mounted while sections scroll, without a hide/reappear animation.

### 4. How it works / functions, inputs, outputs and data flow

`FloatingBottomNavbar(currentIndex, onTap, onCenterActionTap)` still receives the actual selected tab and original callbacks. `_buildNavItem` compares its index with currentIndex, renders the selected glyph/text and invokes `onTap(index)`. Only ink feedback changed: `NoSplash.splashFactory` prevents ripples, transparent splash/highlight/hover colors prevent touch boxes, and CircleBorder shapes the retained focus feedback. Both center-action builders follow that treatment while preserving their callback.

The root Scaffold keeps the component in its separate bottomNavigationBar slot. Scroll events change content ScrollPosition, not navbar visibility or selection. Example: scrolling Marketplace leaves the dock rectangle unchanged; tapping Services selects that root page; Add Product still opens the original form instead of selecting a page. No duplicate navbar, page, visibility state or gesture handler was introduced.

### 5. Backend / API behavior

Unchanged. Destinations, seller access, session, product creation, data loading, Messages and API calls retain their behavior. No permission or business-logic change.

### 6. Database / migration impact

None. No models, migrations or working records changed. Widget tests do not submit working products.

### 7. Tests performed

- **16/16 navigation/dashboard/system-navigation tests passed in5 seconds**, with the optional capture case explicitly enabled. Coverage includes seller action-vs-page behavior, selected glyph/semantics, stable geometry, target sizes/reduced motion, tab callbacks, scrolling both directions at320/390/768dp and system safe areas. The first new hit-test assertion targeted the decorative background; it was corrected to test the actual tab, retaining the fixed-position assertion.
- Scoped Flutter analysis: **No issues found in2.5 seconds**. Dart formatting completed.
- **Twelve actual widget captures**: regular/seller390dp, seller320dp/200% and regular844dp landscape/200%, each at rest, held press and after scrolling. Inspected seller390dp pressed and seller320dp/200% scrolled captures: no tap rectangle and visible floating dock. Evidence: `scratch/floating-navbar-tap-20261104/renders/`. Surrounding Section labels are isolated test content around the actual production navbar, not working app data or generated images.

Reproduce from `campushub/` with `flutter test --no-pub --dart-define=CAPTURE_FLOATING_NAV=true test/floating_bottom_navbar_test.dart test/dashboard_center_add_button_test.dart test/system_navigation_surface_test.dart`. Set `FLOATING_NAV_REVIEW_DIR` to an absolute scratch output directory to retain captures separately.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-device, deployed-session or full-app-suite result is claimed. This applies to the shared root navbar; separate detail/form routes retain their existing navigation design. Keyboard navigation may still show the intentional circular focus highlight. Hot-restart if an older build still shows the tap box. Safe exercise: scroll sections down/up on a root tab, confirm the dock stays visible, and tap each destination to verify selection without a box. Approved sellers can open and cancel Add Product without submitting. Do not modify permissions or working data just to inspect navigation.

## Persistent diagnostics across scratch copies - November 2, 2026

1. **Cause / reason:** The latest paste contains 25,046 lines of diagnostics, including unresolved Flutter/application imports and cascading undefined classes from authentication and seller copies. A workspace inventory found 177 readable Dart files under `scratch/`, including historical checkouts; removing one selected backup cannot stop analysis of the others. The previously selected `scratch/mobile-auth-theme-20261102/before-login.dart` is already absent, as are the two old `before-shell.dart` paths shown in the tabs. Open deleted buffers and terminal history can outlive their files. The exact paths/command behind every pasted message were not included, so their individual provenance is not proven.
2. **Exact files changed:** `.vscode/settings.json:5` (`dart.analysisExcludedFolders`) excludes the workspace-relative `scratch` folder from Dart project discovery/analysis; `:8` (`files.associations`) maps `**/scratch/**/*.dart` to `plaintext`. This report is at `docs/mobile-profile.md:3`. Verification evidence is in `scratch/dart-backup-diagnostics-20261102/`. No further backup was deleted during this follow-up.
3. **Changes made:** Apply one archive-wide editor boundary instead of modifying imports in every historical copy. Keep all pre-existing settings and real Flutter source intact. Remaining scratch Dart snapshots open as readable plain text, without Flutter completion, formatting or diagnostics; real application files retain Dart language support. A trial `scratch/analysis_options.yaml` exclusion did not prevent explicitly requested backup diagnostics and was removed; it is not part of the final configuration.
4. **How it works / inputs, outputs and data flow:** These are editor settings, with no new runtime function. Dart Code resolves the relative folder `scratch` against the open workspace and excludes that archive from project discovery/analysis. VS Code matches the full normalized file path against the association glob and chooses the `plaintext` language for matching backups. Example: `C:/Users/leste/Desktop/CAMPUSHUB/scratch/mobile-auth-theme-20261102/before-shell.dart` matches; `C:/Users/leste/Desktop/CAMPUSHUB/campushub/lib/module_app/screens/login_screen.dart` does not. Existing Login/Sign Up controllers, shared form rendering and seller APIs/data flows are unchanged. This uses the documented [Dart Code exclusion setting](https://dartcode.org/docs/settings/#dartanalysisexcludedfolders) and [VS Code path-based file associations](https://code.visualstudio.com/docs/languages/overview#_common-questions).
5. **Backend / API behavior:** Unchanged. No authentication, seller ownership, navigation, permissions, inventory, order workflow or request/response code changed.
6. **Database / migration impact:** None. No database, schema, migration, dependency, environment, account or session changes; no deployment or device run.
7. **Tests performed:** Direct Dart analysis of six real files (`login_screen.dart`, `signup_screen.dart`, `auth_form_shell.dart`, `auth_theme_toggle.dart`, `seller_workspace_content.dart`, `seller_recent_orders.dart`) passed with `No issues found!`, exit 0; see `application-analyze.log`. JSON parsing, unchanged-existing-settings comparison, three positive/three negative association-path checks, and eight protected source/configuration hashes passed; see `settings-verification.log`. Deliberate backup analysis reproduced 901 diagnostics for two explicit files and 418 for an explicitly selected archive folder; those checks failed as expected and are retained as diagnostic evidence, not passing application checks. Widget tests were not rerun for editor-only settings. The live editor panel/language mode was not inspected.
8. **Remaining limitations / troubleshooting / safe practice:** Run `Developer: Reload Window` once if already-open buffers retain their old language/diagnostics; close deleted backup tabs without saving them back to their old paths. Use `cls` in PowerShell to clear previously printed terminal output: settings do not erase history. Manually invoking Dart analysis on a scratch file/folder can still produce errors; these settings govern VS Code, not arbitrary terminal commands. If fresh errors appear under `campushub/lib/`, keep them visible and investigate that real source. Safe exercise: after reloading, open one remaining scratch `.dart` and verify its status-bar language is Plain Text; open the real Login screen and verify Dart. From `campushub/`, run `dart analyze lib/module_app/screens/login_screen.dart lib/module_app/screens/signup_screen.dart` and check the new result. Do not submit credentials or alter workflows for this check.

## Scratch backup import diagnostics - November 2, 2026

1. **Cause / reason:** The open `scratch/mobile-auth-compact-20261102/before-shell.dart` was an isolated historical copy, outside the Flutter package in `campushub/`. Its folder has neither package configuration nor the adjacent `auth_theme_toggle.dart`. The pasted missing-import errors cause the subsequent undefined `Color`, `TextStyle` and widget errors. Keeping the backup open with a `.dart` extension allowed the editor to keep checking it; explaining the cause alone did not change that file.
2. **Exact files changed:** Rename that backup to `scratch/mobile-auth-compact-20261102/before-shell.dart.bak:1` (first import); this guide at the `Scratch backup import diagnostics` heading. Verification output is `scratch/mobile-auth-compact-20261102/backup-diagnostics-analyze.log:1`. No application source or editor settings changed.
3. **Changes made:** Preserve the complete snapshot under a backup extension instead of leaving it as ordinary Dart source. SHA-256 before and after is `2F69A762EBFADA7A29C0D7DC678BFEDB39EC1812AAB2EF85E9B2C45FEDC65E5C`. No dependency was installed, imports rewritten or diagnostics globally suppressed.
4. **How it works / functions and data flow:** This is a file-name correction, with no new function or runtime input/output. The historical file remains readable as evidence. Actual Login/Sign Up continue using `campushub/lib/module_app/screens/components/auth_form_shell.dart:1`, whose Flutter imports resolve through `campushub/.dart_tool/package_config.json` and whose relative theme import resolves to the existing adjacent file. Example: `Color` comes from Flutter in the real component; it should not be recreated as a custom class to repair an isolated snapshot.
5. **Backend / API behavior:** Unchanged. Authentication requests, form validation, navigation, sessions and permissions are unaffected.
6. **Database / migration impact:** None. No backend, schema, migration, account, session, package or working-data changes.
7. **Tests performed:** Direct Dart analysis of the actual `auth_form_shell.dart` and `auth_theme_toggle.dart` completed successfully with `No issues found!` (exit 0). File checks confirmed the old backup path is absent, the new backup has identical contents, and both real component hashes remain unchanged. Widget/device tests were not rerun for a backup-only rename. The live editor's Problems panel was not inspected.
8. **Remaining limitations / troubleshooting / safe practice:** An already-open editor buffer may retain diagnostics until the old tab closes; do not save it back to the old `.dart` path. Open the actual component linked above. If stale errors remain after closing the old tab, run `Dart: Restart Analysis Server` from the command palette. This change addresses this specific backup; other historical `.dart` copies outside the Flutter package may have the same independent issue. Safe exercise: open the `.dart.bak` copy to read its first imports, then open the real component and run `dart analyze lib/module_app/screens/components/auth_form_shell.dart lib/module_app/screens/components/auth_theme_toggle.dart` from `campushub/`; verify analysis succeeds without changing or submitting credentials.

## Compact auth inputs from the supplied reference - November 2, 2026

1. **Cause / reason:** After radius 50 was applied, the user supplied an image requesting smaller fields. The previous 64dp minimum and 20dp vertical padding produced tall pills. The initial compact version used 48dp/12dp; the latest request to increase it a bit now uses 52dp minimum height and 14dp vertical padding. Only input sizing changed in this follow-up.
2. **Exact files changed:** `campushub/lib/module_app/screens/components/auth_form_shell.dart:352` (value text), `:359` (`isDense`), `:376` (current 52dp minimum), `:393` (current 14dp vertical padding), `:400`/`:402`/`:413` (retained icon sizes/leading width); `campushub/test/signup_spacing_test.dart:27` (padding expectation); `campushub/test/auth_form_responsive_test.dart:116` (52-56dp normal-size bound); this guide and `CAMPUSHUB_CONTEXT.md` (current dimensions/results).
3. **Changes made:** Slightly enlarge the compact fields from 48dp to 52dp, with 2dp more padding above/below the value. Radius 50, compact value/hint/icon sizes, floating labels, input order, side-by-side names, colors, states and all surrounding controls remain.

| Before | After | Why |
| --- | --- | --- |
| Initial compact 48dp minimum; 12dp vertical padding | 52dp minimum; 14dp vertical padding; dense layout retained | Implements the latest small increase without returning to the original tall fields. |
| 14dp value / 13dp hint | 13dp value / 12dp hint | Matches the smaller reference text scale. |
| 20dp icons; 46dp leading slot | 16dp leading icon, 18dp eye, 40dp leading slot | Keeps icon proportions consistent with the compact field. |

4. **How it works / data flow:** Both unchanged page files still call the shared `AuthFormField` with the same controllers, labels, formatters, validators and callbacks. Its native InputDecoration uses `isDense: true`, `minHeight: 52` and 14dp vertical content padding; native text/error layout can grow when necessary because no maximum height was imposed. The existing border helper still returns radius 50 for every state. Example: a normal empty field measures within 52-56dp in the checked layouts; large text/validation may expand rather than clip. Compact glyph sizes and existing button/callbacks are retained.
5. **Backend / API behavior:** None changed. Fourteen protected page/service/asset files, the shared non-input code, field interface and controller/validation/keyboard binding checks passed. Django auth, legal acceptance, recovery, navigation and sessions remain as before.
6. **Database / migration impact:** None. No backend, schema, migration, package, asset binary, working account/preference/session change or device action.
7. **Tests performed:** **31/31** focused layout/spacing/responsive/theme/navigation tests passed after the small increase, with actual renders enabled. A height assertion verifies normal-size fields in phone/landscape layouts; existing 2x-text, simulated keyboard, error, mode-persistence and route checks passed. Three-file static analysis reported no issues (3.1 seconds). The actual updated light Login render was visually inspected. Current evidence: `scratch/mobile-auth-input52-20261102/tests.log`, `analyze.log`, `renders/`; earlier compact evidence remains in `scratch/mobile-auth-compact-20261102/`. Protected-source evidence uses `scratch/mobile-auth-inputs-20261102/verify_scope.cjs`.
8. **Remaining limitations / safe practice:** Reference sizing is interpreted in Flutter logical pixels; exact physical screenshot dimensions vary by device density. Field height is a minimum, so accessibility text/errors can grow. Shorter fields naturally reduce form content height; surrounding page code is untouched. No physical Android/IME or live login/signup was performed. Safe exercise: compare the 390px normal-size capture with the reference, then run the 320px/2x-text tests and confirm fields/buttons remain usable. Change sizing only in the shared field, not separately in each page or authentication code.

## Auth input corner radius 50 - November 2, 2026

1. **Cause / reason:** The user requested radius 50 for the new Login/Sign Up input design. This supersedes the earlier 10dp input corner choice only.
2. **Exact files changed:** `campushub/lib/module_app/screens/components/auth_form_shell.dart:330` (`border` helper radius); `campushub/test/login_layout_test.dart:89` and `:190` (existing border assertions); this guide and `CAMPUSHUB_CONTEXT.md` (current value/results).
3. **Changes made:** Change `BorderRadius.circular(10)` to `BorderRadius.circular(50)` in the shared input border helper. Keep all other input styling and page controls as before.

| Before | After | Why |
| --- | --- | --- |
| 10dp input corners | 50dp input corners | Gives both forms the requested capsule-shaped fields. |

4. **How it works / data flow:** Both unchanged page files pass their fields to `AuthFormField`. Its existing local `border(color, width)` returns an OutlineInputBorder with the new radius; normal, focused, disabled and error states all reuse it. Controllers, keyboard settings, label/hint text, focus colors and validation callbacks are unchanged. Example: Password gets the same radius 50 before focus, during gold focus and when displaying a real validation error.
5. **Backend / API behavior:** None changed. Authentication, validation, recovery, consent, routing and sessions remain. Fourteen protected page/service/asset files and the non-input shared source/interface/binding comparisons passed.
6. **Database / migration impact:** None. No backend, schema, dependency, asset, account, preference or deployed/running-session change.
7. **Tests performed:** **31/31** focused layout/spacing/responsive/theme/navigation tests passed with real-widget capture enabled. Two-file static analysis reported no issues (4.2 seconds). The actual light Sign Up render was visually inspected; evidence is `scratch/mobile-auth-radius50-20261102/tests.log`, `analyze.log`, `renders/`. The first test command did not start because its log folder was relative to the Flutter folder; the corrected command produced the reported passing result.
8. **Remaining limitations / safe practice:** Flutter fits large corner radii to the actual control bounds, producing a capsule at these field heights. No physical Android/live account submission was performed. Safe exercise: inspect the shared border and existing two radius assertions, then compare empty/focused fields in both themes. Keep radius 50 in the one helper rather than changing each page or individual state separately.

## Alternative Login/Sign Up inputs only - November 2, 2026

The user explicitly invoked `emil-design-eng` and `frontend-design` for a different input-field design and prohibited other application changes. Only the existing shared `AuthFormField` implementation changed in production. Both page files, all other shared-shell/theme/heading code, logos, buttons, single-line recovery/consent and authentication remain untouched.

### 1. Cause / reason

This is the requested visual alternative, not a new authentication workflow. Existing inputs used external captions, pale filled surfaces and 14dp corners. The selected direction uses a fixed floating caption in an outlined field, a clean selected-theme surface, tighter corners and precise focus feedback. Actual validation-state review also showed the native inherited helper text needed clearer weight in dark mode, so the input now supplies its own theme-aware error text style.

The design plan retains Montserrat and existing navy `#1A1851`, gold `#FCB315`, white `#FFFFFF`, dark navy `#16153B` and gray `#667085`. Labels/value text remain left-aligned. Component structure is `label above [icon value]` -> `[-- label --] / [icon value eye]`. The notched label is the one deliberate change in structure; the existing page design is retained. Labels are permanently floated rather than animated when typing. No custom entrance, keyboard or password-toggle motion was added.

### 2. Exact files changed, current lines and nearby anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/components/auth_form_shell.dart` | 287 `AuthFormField`; 322 `build`; 328 `border`; 336 field padding | Restyle only this existing shared field widget, using theme-derived outline colors, 10dp corners and space for the fixed label. Everything before this class matches the pre-task snapshot. |
| Same file | 358 `labelText`; 359 `FloatingLabelBehavior.always`; 382 `errorStyle`; 416 focus border | Associate the original label with the native input, keep it in the outline, use a 2dp gold focus border in both themes and consistent validation borders/readable error text. Controller/validation/keyboard bindings and field interface match the original. |
| `campushub/test/login_layout_test.dart` | Existing input-border assertions in both page cases | Update the previous 14dp expectation to 10dp and assert the permanent floating-label design. |
| `campushub/test/signup_spacing_test.dart` | Existing content-padding expectation | Update the input's vertical content padding to 20dp; retain spacing, field-count, validation and reachable-button checks. |
| `campushub/test/auth_form_responsive_test.dart` | Optional actual-form render test, `save('focused')` / `save('validation')` | Capture the new focused/error states in both themes using the existing test harness and actual widgets/fonts. |
| `docs/mobile-profile.md`; `CAMPUSHUB_CONTEXT.md` | Current input-only entry | Document design decisions, exact scope, data flow, checks, limits and safe practice. |

### 3. Changes made / design review

| Before | After | Why |
| --- | --- | --- |
| Caption above a soft filled field | Native caption permanently set into the outline | Offers a distinct alternative without new content or moving labels during entry. |
| 14dp corners and pale field fill | 10dp outline on the current form surface | Gives the credential controls a more restrained institutional shape. |
| Focus border varies by theme | 2dp gold focus border in both modes | Keeps interaction feedback consistent with CampusHub's existing accent. |
| Native inherited error-text styling | Explicit 12dp medium-weight theme error text and matching shaped borders | Keeps actual validation messages legible in the inspected dark state. |

The value text, hint copy, icons, password visibility control, field order, side-by-side names, selected theme, form text scaling and existing supporting checklist remain. Top padding reserves space for the notched caption; the minimum control height and bottom gap keep the field footprint close to the prior design. No other product element was restyled.

### 4. How it works / functions, inputs, outputs and data flow

`AuthFormField(controller, label, icon, validator, onChanged, ...)` receives the same screen-owned values/callbacks as before and returns one native TextFormField plus its existing optional supporting widget. Its local `border(color, width)` helper returns a consistent 10dp OutlineInputBorder with a label gap. Normal outline color is blended from the existing selected-theme secondary text and surface; focus uses existing gold; error uses the existing error color. Floating-label state styling changes color for actual errors, with no new validation rule.

```text
Unchanged Login/Sign Up _buildField arguments
  -> unchanged AuthFormField constructor/interface
  -> unchanged controller / keyboard / formatter / validator bindings
  -> new InputDecoration and field-only spacing
  -> same native input edits, validation results and password callback
  -> unchanged screen submit handler / DRF / SessionService
```

Example: `label: 'Password'` becomes `InputDecoration.labelText`, always visible at the field outline. `obscure` and `onToggleObscure` still come from the existing screen state; tapping the same eye control calls the same callback. A server error is displayed unchanged, using the updated error text/border presentation. The 16dp floating-label style is rendered at the native floating-label scale; field values keep their existing Montserrat style.

### 5. Backend / API behavior

None changed. Login/Sign Up source files themselves match their pre-task SHA256 values. AuthService, SessionService, ThemeService, router, legal/recovery/theme components, app root, pubspec and all campus/logo assets also match: **14 protected files unchanged**. Shared non-input shell/theme/heading source, the AuthFormField interface and controller/validator/keyboard binding block matched independent before/after comparisons. No field, rule, endpoint, navigation or session behavior was added or removed.

### 6. Database / migration impact

None. No backend, schema, migrations, dependencies, assets or working records/preferences changed. No deployment, emulator/hardware input, forced app restart or live submission was performed.

### 7. Tests performed

**43/43 existing focused Flutter tests passed** after the final input error-style adjustment, covering both pages/themes, small/landscape screens, 2x text, keyboard/validation, saved-theme switching, draft retention, typed routes, password policy, recovery controls and existing system-navigation behavior. Static analysis of the four changed source/test Dart files reported **no issues** (1.5 seconds). Formatting was applied with the installed SDK.

The enabled real-widget capture produced 16 images across Login/Sign Up, light/dark and empty/action/focused/validation states. Light Login empty/focused and dark Sign Up action/validation views were visually inspected; dark error text was adjusted and inspected again before completion. Evidence: `scratch/mobile-auth-inputs-20261102/tests-final.log`, `analyze-final.log`, `renders/`, `protected.json`, `verify_scope.cjs`. The scope verifier checks actual file hashes and source ranges rather than assuming unchanged behavior from a passing screenshot. The shared skill kit remains unavailable, so these checks do not claim a kit-wide accessibility certification.

Reproduce from `campushub/` using the focused command in the theme entry below; set `AUTH_LAYOUT_CAPTURE_DIR=../scratch/mobile-auth-inputs-20261102/renders` to include actual empty/focus/error renders. Run static analysis on `lib/module_app/screens/components/auth_form_shell.dart`, `test/login_layout_test.dart`, `test/signup_spacing_test.dart` and `test/auth_form_responsive_test.dart`.

### 8. Remaining limitations / troubleshooting / safe practice

Checks use real Flutter widgets with simulated keyboard insets, not physical Android/IME or live login/signup. Input-specific geometry naturally reflows as part of this field design; the surrounding page implementation and controls were not edited. Existing consent scale-down behavior on narrow screens is unchanged.

If a label moves when focus changes, verify `FloatingLabelBehavior.always` remains. If dark validation appears too faint, inspect the field's explicit error style/weight and selected error color rather than changing global typography. Safe exercise: temporarily change only the local field corner radius from 10dp to 12dp, render both focused themes and run the existing field tests; their current 10dp expectation should catch the change. Restore 10dp and rerun. Do not modify the page files, authentication or validators to change an input's appearance.

## Sign Up consent in one straight row - November 2, 2026

1. **Cause / reason:** The previous consent layout deliberately stacked the introduction above the legal links. The user clarified that the entire agreement must be one straight row beside the checkbox; this entry supersedes that stacked arrangement.
2. **Exact files changed:** `campushub/lib/module_app/screens/signup_screen.dart:376` (`signup-terms-row`), `:379` (compact checkbox area), `:401` (scale-down fitting), `:406` (continuous agreement span), `:431` (`signup-terms-label`); `campushub/test/auth_form_responsive_test.dart:171` (single-line/full-copy/checkbox alignment assertions); this guide and `CAMPUSHUB_CONTEXT.md` (current requirement/results).
3. **Changes made:** Show I agree to the Terms and Conditions and Privacy Policy as one uninterrupted line beside the checkbox. Keep normal word spaces and underlined legal titles, selected-theme colors and the existing legal action. Remove the separate introduction line and grouped Wrap.
4. **How it works / data flow:** Sign Up `build` keeps one centered Row: a 32dp checkbox area, 4dp gap and the remaining-width TextButton. Its single Text.rich joins the existing consent words with styled legal spans, using `maxLines: 1` and `softWrap: false`. A FittedBox only scales down when the sentence exceeds the available width, so the full copy remains visible without clipping. The text still calls `_openTermsAndPrivacy`; the checkbox still calls `_handleTermsChanged`. Accepted dialog results update the existing `_agreedToTerms` guard before `_signUp` can proceed. No acceptance is inferred from a layout change.
5. **Backend / API behavior:** None changed. Authentication, validation, existing legal document/dialog, explicit acceptance and signup submission remain as before.
6. **Database / migration impact:** None. No backend, schema, dependencies, asset binaries, working accounts/preferences or session records changed; no installation, device action or restart was performed.
7. **Tests performed:** **34/34 focused layout/spacing/navigation/theme widget tests passed** with actual render capture enabled. Updated assertions check the full sentence, one-line configuration, matching vertical checkbox center and form-width bounds at 320px, 390px and landscape in both themes. Existing 2x-text, keyboard, mode persistence and route checks passed. Both changed Dart files passed static analysis (2.0 seconds). Actual light/dark Sign Up action screenshots were visually inspected. Evidence: `scratch/mobile-terms-one-row-20261102/tests.log`, `analyze.log`, `renders/`. Reproduce with `flutter test --no-pub test/login_layout_test.dart test/signup_spacing_test.dart test/auth_form_responsive_test.dart test/widget_test.dart` from the Flutter folder.
8. **Remaining limitations / safe practice:** The sentence scales down on narrow screens to honor the explicit one-row request, so its visual size may be smaller than other helper copy. Keyboard/theme verification uses widget tests, not physical Android/live signup. Safe exercise: compare 320px/390px cases, confirm the full TextSpan sentence and the aligned checkbox remain visible, then open the legal dialog without submitting account data. Keep actual acceptance guards unchanged while adjusting presentation.

## Single-line recovery and arranged terms consent - November 2, 2026

1. **Cause / reason:** The right-side recovery action still wrapped onto two lines. Sign Up consent was one flowing paragraph, which made its checkbox and legal links look uneven. The user requested straight recovery text without extra spacing and a better-arranged terms area.
2. **Exact files changed:** `campushub/lib/module_app/screens/login_screen.dart:155` (`_buildLoginOptions`), `:167` (single recovery string), `:181` (`fitsRow`), `:220` (single-line fitting), `:304` (existing form includes options); `campushub/lib/module_app/screens/signup_screen.dart:376` (`signup-terms-row`), `:390` (legal action), `:403` (agreement introduction), `:412` (grouped links); `campushub/test/auth_form_responsive_test.dart` (`main`, recovery/terms geometry assertions and added 390px cases); this guide and `CAMPUSHUB_CONTEXT.md` (current layout/result).
3. **Changes made:** Use the unchanged full Forgot Username or Password? copy as one line, with normal word spaces, zero extra letter spacing and compact 12dp typography. Keep it gold/right-aligned beside Remember me when both fit. At narrow widths/enlarged text, place the full link on its own right-aligned row without an extra vertical gap. Sign Up now presents I agree to the above grouped Terms and Conditions / and / Privacy Policy text, aligned after the checkbox. Preserve the circular logo, selected theme, fields and primary buttons.
4. **How it works / data flow:** `_buildLoginOptions(formContext)` returns the existing checkbox/recovery controls. A local `textWidth(value, style)` uses TextPainter with the actual font, direction and text scaling, then disposes it. The measured label widths plus the compact checkbox and 8dp gap decide Row versus Column. Text uses `maxLines: 1`, `softWrap: false` and no extra letter spacing; a scale-down fit only protects the full-width fallback from clipping at extreme text sizes. Remember me still changes `_rememberMe`; recovery still calls `_showAccountRecoveryDialog`. The terms TextButton now contains a short introduction and Wrap of complete link labels. The whole legal text area still calls `_openTermsAndPrivacy`; its checkbox still calls `_handleTermsChanged`, so actual dialog acceptance is required as before. Example: at 390px normal text the two Login controls share one row; at 320px the full recovery label can move below rather than breaking in half.
5. **Backend / API behavior:** None changed. Existing DRF auth, validation, account recovery, session/Remember me, password rules, consent acceptance and navigation remain. No legal document content or acceptance rule was changed.
6. **Database / migration impact:** None. No backend, schema, asset, dependency, working account, real preference or session record changed; no device/install/restart action was performed.
7. **Tests performed:** **43/43 focused Flutter tests passed**, including enabled actual renders, light/dark switching and persisted preference, draft retention, routes, password/recovery inputs, small/landscape screens, 2x text and simulated keyboard. Updated geometry checks verify single-line recovery configuration/right edge, inline controls at normal 390px/wider layouts, narrow fallback and aligned legal groups within the form width. All three changed Dart files passed static analysis (2.0 seconds). The actual light Login and light/dark Sign Up action captures were visually inspected. Evidence: `scratch/mobile-auth-inline-20261102/tests.log`, `analyze.log`, `renders/`. Existing eleven protected-file/action/helper checks remain applicable.
8. **Remaining limitations / safe practice:** No physical Android/IME or live account/recovery submission was performed. Very narrow screens or enlarged text intentionally use the right-aligned fallback; at extreme scale the full-width label can scale down to remain one line. Safe exercise: compare the 390px and 320px geometry cases, confirm the same full recovery string appears once, then inspect the legal link rectangles against the input edge in both themes. Keep the actual scaling/direction measurement and consent handlers; do not remove text or bypass acceptance to change spacing. Reproduce with the focused Flutter command in the theme entry below, adding `AUTH_LAYOUT_CAPTURE_DIR=../scratch/mobile-auth-inline-20261102/renders` when actual images are needed.

## Login/Sign Up theme switching and logo-only heading - November 2, 2026

This latest request supersedes the earlier fixed-white form and CampusHub-wordmark decisions below. Keep the circular original logo and current layout; selected light mode has a white form, and selected dark mode has a dark navy form. Gold is now `#FCB315`, including the right-side recovery link.

### 1. Cause / reason

Confirmed: the existing theme toggle and ThemeService correctly changed/saved the app's selected mode, and `CampusHubApp` already listened for changes. The shared authentication style introduced in the white-panel request explicitly forced `Brightness.light`, white surfaces and navy field text. That local override prevented the forms from reflecting the selected dark theme. This was a presentation override, not a failed preference service or authentication defect. The user also requested removing the CampusHub text and changing gold to `#FCB315`.

### 2. Exact files changed, current lines and nearby anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/components/auth_form_shell.dart` | 9 `gold`; 14 dark colors; 44 `linkButton`; 52 `theme` | Use the requested gold, resolve readable selected-theme colors and preserve inherited brightness instead of forcing light mode. |
| Same file | 101 `formTheme`; 112 navigation-bar colors; 228 `logo_dark`; 248 `AuthFormHeading`; 287 `AuthFormField` | Apply selected surfaces/icons/text/borders, use the existing light/dark logo asset and remove visible CampusHub text while retaining the centered circle/heading. Fields consume the local color scheme. |
| `campushub/lib/module_app/screens/login_screen.dart` | 225 checkbox colors; 239 Remember me text; 255 recovery-link style; 297 footer text; 302 account link | Adapt controls/text to the current form theme; set the recovery link explicitly gold while keeping its existing right-side position/callback. |
| `campushub/lib/module_app/screens/signup_screen.dart` | 383 checkbox colors; 389 terms link; 400 terms text; 451 footer; 461 Log In link | Keep terms/footer/checkbox text readable in both modes using the scoped color scheme. Submission and legal acceptance handlers are unchanged. |
| `campushub/test/auth_form_responsive_test.dart` | 22 `followSavedTheme`; 97 selected text/gold checks; 273 render loop; 324 toggle integration tests | Exercise actual form changes, saved preference, retained input, dark-mode navigation, both layouts/themes and actual themed renders. |
| `campushub/test/login_layout_test.dart` | 7 `main`, selected-theme surfaces/logo and absent-wordmark assertions | Update fixed-white/wordmark expectations to the requested selected-theme behavior. |
| `campushub/test/widget_test.dart` | 30 named Login route; 46 Sign Up route | Update old Welcome Back/Signup/SIGN UP/wordmark expectations to the current existing labels and requested logo-only layout; retain keyboard, capitalization and password-checklist coverage. |
| `docs/mobile-profile.md`; `docs/mobile-typography.md`; `CAMPUSHUB_CONTEXT.md` | Current November 2 theme entries | Explain this override, functions/data flow, verification, troubleshooting and safe practice. |

### 3. Changes made

The form panel, input fill/borders, labels, helper text, checkbox colors, account/terms links and Android navigation-bar icon contrast now follow the selected theme. Light retains white/navy; dark uses the existing navy direction with light text. Both keep gold buttons and navy button labels. Forgot Username or Password? is explicitly `#FCB315` on the right beside Remember me. CampusHub text is removed from both form headings; the original light/dark logo remains in the 72dp circular container at the photo/panel boundary. The logo has an accessible image label even without visible brand text. The original photo, Montserrat, fields, responsive layout, keyboard handling and current routes remain.

### 4. How it works / functions, inputs, outputs and data flow

`AuthFormStyle.theme(base)` receives the inherited app ThemeData and returns a scoped copy with the **same selected brightness**. It selects white/navy or dark-navy/light-text surfaces and applies bundled Montserrat. `linkButton(context, color: ...)` returns a readable text-button style from the form's color scheme unless an explicit color is supplied; Login supplies the requested gold for recovery. `AuthFormShell.build` derives its panel/logo/navigation colors from that theme. `AuthFormHeading` renders only the existing Login/Create Account title and subtitle. `AuthFormField` forwards the same controller/validator/callback inputs while choosing field presentation from the local scheme.

```text
Existing AuthThemeToggle tap
  -> existing ThemeService.setLightMode(value)
  -> existing notifyListeners + saved SharedPreferences choice
  -> existing CampusHubApp AnimatedBuilder / MaterialApp.themeMode
  -> inherited light/dark ThemeData
  -> AuthFormStyle.theme(base) preserves brightness
  -> panel, fields, labels, logo and navigation icons update
```

Example: type an identifier, tap Switch to dark mode -> the panel becomes navy and the same identifier stays in its controller; entering Sign Up and returning retains the selected dark theme. Switching back restores white. Theme switching does not submit credentials or replace the existing controllers.

### 5. Backend / API behavior

Unchanged. Login/Sign Up validation, error mapping, recovery, terms, password checklist, DRF requests, session/Remember me, typed signup return value and post-login permissions/routes remain. ThemeService, the actual toggle, app root and router were already working and were not rewritten. Nine current protected theme/auth/navigation/asset hashes matched; the prior eleven protected files/assets and original action-handler/signup-helper comparisons also matched.

### 6. Database / migration impact

None. No backend, models, migration, package, asset binary or real account/session data changed. The existing theme preference is still the only setting saved when a user taps the toggle. Tests use mocked SharedPreferences; no physical-device preference was changed or app reset/install performed.

### 7. Tests performed

**39/39 focused Flutter tests passed** across layout/spacing/responsive, actual theme switching, named routes, password policy, recovery inputs and existing system-navigation wrapper coverage. Two new integration checks tap light -> dark -> light on the real form widgets with the existing ThemeService/MaterialApp wiring, assert the persisted preference, verify entered text remains and check dark theme carries through Login -> Sign Up -> Login. Existing small/landscape/2x-text/simulated-keyboard, circle geometry and right-side recovery alignment checks pass in both themes. Stale tests expecting the removed wordmark/old button labels were updated to the new requested presentation; no production auth behavior was changed for them.

Static analysis of all six changed source/test files reported **no issues** (2.8 seconds). Actual bundled-font Flutter captures were produced for Login/Sign Up, light/dark and top/scrolled-action views; both Login themes and the dark Sign Up action view were visually inspected. This is actual widget rendering, not an AI mockup or a universal accessibility certification. Evidence: `scratch/mobile-auth-theme-20261102/verified-tests.log`, `analyze.log`, `renders/`, `protected.json`; existing action/asset checks remain in `scratch/mobile-auth-white-panels-20261102/verify_scope.cjs`.

Scoped whitespace checks passed for all nine changed source/test/document files; tracked-file `git diff --check` also passed.

Reproduce from `campushub/`:

```powershell
flutter test --no-pub test/login_layout_test.dart test/signup_spacing_test.dart test/auth_form_responsive_test.dart test/widget_test.dart test/password_policy_test.dart test/recovery_code_input_test.dart test/system_navigation_surface_test.dart
flutter analyze --no-pub lib/module_app/screens/components/auth_form_shell.dart lib/module_app/screens/login_screen.dart lib/module_app/screens/signup_screen.dart test/auth_form_responsive_test.dart test/login_layout_test.dart test/widget_test.dart
# Optional actual render evidence for both themes.
$env:AUTH_LAYOUT_CAPTURE_DIR = '../scratch/mobile-auth-theme-20261102/renders'
flutter test --no-pub test/auth_form_responsive_test.dart
```

### 8. Remaining limitations / troubleshooting / safe practice

The tests simulate keyboard/system insets and mock preferences; no physical Android session or live account submission/recovery was performed. The screenshot harness's optional render test runs only when its capture environment variable is set; the final regression was run without that variable, while themed captures were produced and inspected during the earlier enabled run. No deployment, forced hot reload or device input was performed.

If the icon changes but a form remains light, inspect whether a descendant reintroduces `Brightness.light` or a hardcoded white surface. If the icon and app disagree, verify the normal app's existing ThemeService listener is active before changing storage or auth. Safe practice: type a non-secret draft identifier, switch modes twice without submitting, confirm it remains, then open Sign Up and return. In a widget test, inspect the mocked `campushub_light_theme` value and selected surface after each tap. Do not clear real saved sessions or change route/auth code to fix a visual theme issue.

## Login recovery link beside Remember me - November 2, 2026

1. **Cause / reason:** The existing Wrap moved the full recovery link to a separate left-aligned line. The user requested it on the right beside Remember me.
2. **Exact files changed:** `campushub/lib/module_app/screens/login_screen.dart:209` (`LayoutBuilder`/Row), `:217` (`login-remember-control`), `:243` (`login-recovery-link`); `campushub/test/auth_form_responsive_test.dart:99` (control geometry assertions); this guide and `CAMPUSHUB_CONTEXT.md` (current behavior/results).
3. **Changes made:** Keep Remember me on the left and the existing Forgot Username or Password? action on the right in the same row. Right-align its full text, allowing it to wrap within the right-hand space. Preserve the circle logo, photo, fields and primary button.
4. **How it works / data flow:** Login `build` receives the form width through `LayoutBuilder`. A `ConstrainedBox` caps the Remember me control at half that width; its label can wrap when enlarged. An Expanded right-hand TextButton receives the remaining width after an 8dp gap, aligns content to the right and calls the unchanged `_showAccountRecoveryDialog()`. Example: on a narrow phone the recovery text can occupy two lines beside the checkbox rather than creating a new row. Checkbox/label taps still update `_rememberMe`, which the existing login action passes to SessionService.
5. **Backend / API behavior:** None changed. Login validation, recovery requests, Remember me persistence, authentication and navigation retain their existing handlers/services.
6. **Database / migration impact:** None. No backend, schema, asset, dependency, working account, preference or session record was changed.
7. **Tests performed:** **23/23** focused Login/layout/responsive/navigation tests passed. Existing geometry checks now confirm the link sits to the right, shares the control row's vertical center and aligns with the form-field right edge. Small/landscape views, both app themes, 2x text and simulated keyboard checks passed. Two-file analysis reported no issues (2.6 seconds). The actual Flutter Login PNG was visually inspected. Evidence is `scratch/mobile-auth-white-panels-20261102/recovery-right-tests-final.log`, `recovery-right-analysis.log`, `recovery-right-renders/login-top.png`. The initial landscape assertion incorrectly used full panel width instead of the existing 440dp maximum form width; only the test expectation was corrected.
8. **Remaining limitations / safe practice:** Widget tests simulate the keyboard; no physical-device/live recovery request was performed. Safe exercise: inspect the existing geometry assertions, resize between 320px and landscape, and verify both control centers remain level and the recovery link stays at the field edge. Preserve text wrapping and scaling; do not add ellipsis or change recovery/session code to adjust alignment.

## Circular Login/Sign Up logo restored - November 2, 2026

1. **Cause / reason:** The white-panel refinement placed the existing logo beside the brand text. The user requested its circular container back.
2. **Exact files changed:** `campushub/lib/module_app/screens/components/auth_form_shell.dart:155` (panel Stack), `:180` (top content padding), `:193` (`Positioned` logo), `:228` (`AuthFormHeading`); `campushub/test/auth_form_responsive_test.dart:80` (circle geometry checks); this guide and `CAMPUSHUB_CONTEXT.md` (current request/result). No Login/Sign Up action file changed in this follow-up.
3. **Changes made:** Restore a centered 72dp white circle with a subtle full border and the original `assets/img/logo.png`. Place it across the photo/white-panel boundary on both screens. Move the brand text below the circle; retain white panels, campus photo, fields, colors and typography.
4. **How it works:** `AuthFormShell(page, child, onBack)` still accepts screen-owned form content. Its panel now uses an unclipped Stack with `Positioned(top: -36)` for the 72dp circle, so its midpoint matches panel top. The form has 56dp top padding to leave the lower half of the circle plus a readable gap. `AuthFormHeading(title, subtitle)` renders centered brand/heading text without a second logo. Both pages inherit this shared presentation; the asset is loaded once per screen. Example: circle center y equals panel top y, while its upper/lower halves sit above/below that boundary.
5. **Backend / API behavior:** None changed. Existing validation, DRF calls, recovery/terms, navigation and session handling remain in their original screen/services.
6. **Database / migration impact:** None. No assets, dependencies, backend files, records or deployed/running sessions were changed.
7. **Tests performed:** All **25/25** focused layout/spacing/responsive tests passed, including small/landscape screens, both app themes, 2x text, simulated keyboard and navigation. Added checks verify a circular decoration centered horizontally and across panel top. Static analysis of both changed Dart files reported no issues (2.1 seconds); both updated actual Flutter top-screen renders were visually inspected. Evidence: `scratch/mobile-auth-white-panels-20261102/circle-tests.log`, `circle-analysis.log`, `circle-renders/`.
8. **Remaining limitations / safe practice:** This is widget-render verification, not a physical Android installation or live sign-in test. For a safe exercise, inspect `login-logo-circle` / `signup-logo-circle` in the responsive test and confirm center y matches panel top. If changing circle size, update its negative half-height offset and form top padding together, then rerun the same tests; leave controllers/authentication unchanged.

## Login and Sign Up white form panels - November 2, 2026

This entry is scoped to the two existing authentication layouts. It supersedes older dark-form layout descriptions for Login/Sign Up only. Profile, Home, startup, Django authentication, navigation destinations and the app-wide Poppins theme remain as before. The user explicitly requested Montserrat and gold `#FCB316` on these forms.

### 1. Cause / reason

Confirmed from the existing implementation: each screen duplicated its photo/form layout and chose a dark form surface when the app used dark mode. The light-mode primary button was navy. The form started below the photo rather than actually overlapping it, and the Login recovery link was restricted to one ellipsized line. The user requested a white panel with rounded upper corners over the existing campus photo, gold buttons, centered branding/headings and usable small-screen keyboard behavior. No authentication defect or need for an OAuth provider was inferred.

No reference image was visible in the current request; the implementation follows the written layout description and preserves the original bundled assets. No generated image or replacement logo was introduced.

### 2. Exact files changed, current lines and nearby anchors

Paths are relative to the repository root. Use the named anchor if later edits move lines.

| File | Current line / anchor | Change and reason |
| --- | --- | --- |
| `campushub/lib/module_app/screens/components/auth_form_shell.dart` | 7 `AuthFormStyle`; 47 `theme`; 67 `AuthFormShell` | New presentation-only shared styling/shell for the two forms. Centralizes their explicit navy/gold/white/Montserrat choices and actual photo/panel overlap. It does not own authentication state. |
| Same file | 82 `photoHeight`; 101 `resizeToAvoidBottomInset`; 105 `SingleChildScrollView`; 124/171 `SafeArea` | Size the photo from the full view rather than the keyboard-reduced body; overlap the panel by 28dp; keep header controls/form clear of system insets; allow the whole form to scroll. |
| Same file | 198 `AuthFormHeading`; 258 `AuthFormField` | Reuse the original `bg.png` and `logo.png`, center the CampusHub brand/heading and share rounded bordered inputs. Forward existing controllers, formatters, validators, errors, password controls and callbacks. |
| `campushub/lib/module_app/screens/login_screen.dart` | 7 shell import; 123 `_buildField`; 156 `build`; 243 submit | Replace duplicated layout with the shared shell, use the Login heading/Log In button, keep a wrapping recovery/Remember me area and retain the Sign Up action. Existing `_login`, recovery and return-identifier actions are unchanged. |
| `campushub/lib/module_app/screens/signup_screen.dart` | 6 shell import; 193 `_buildField`; 226 `build`; 239 names row; 375 terms row; 425 submit | Use the same white shell and gold Sign Up button. Preserve all six fields, name capitalization, password checklist, terms acceptance and account-created navigation. Names remain side by side; remove only their prefix icons to leave typing space and correct the `LastName` placeholder to `Last Name`. |
| `campushub/test/login_layout_test.dart` | 6 `main`; 87 Log In; 163 name assertions | Update existing layout expectations for the requested fixed white panel, original logo, title/label changes and reachable primary actions in both app themes. |
| `campushub/test/signup_spacing_test.dart` | 5 `main` | Retain six-field spacing/validation/button reachability coverage with the new Sign Up label. |
| `campushub/test/auth_form_responsive_test.dart` | 13 `openForm`; 53 `main`; 110 keyboard tests; 156/179 route tests; 201 render evidence | Add geometry, small/landscape screens, real bundled-font/2x text, keyboard, validation and real typed-router checks, plus optional actual Flutter PNG capture. |
| `docs/mobile-profile.md`; `docs/mobile-typography.md`; `CAMPUSHUB_CONTEXT.md` | Current November 2 authentication entries | Record the explicit font/color scope, functions/data flow, checks, troubleshooting and safe learning exercise. |

Scratch evidence and one-time edit/verification helpers are in `scratch/mobile-auth-white-panels-20261102/`: before-screen copies, `protected.json`, `verify_scope.cjs`, test/analysis logs and `renders/`. These helpers are not app startup targets or deployed assets.

### 3. Changes made

Both screens now present the existing USTP Oroquieta photo above a white form panel with 32dp upper corners and a genuine 28dp overlap. The original CampusHub logo is beside its centered brand text, with Login or Create Account directly underneath. Headings/input text use navy `#1A1851`; primary buttons use gold `#FCB316` with navy labels. The light form presentation is deliberate in both selected app themes. The existing theme toggle remains available and continues to update the user's app-wide choice; it does not recolor these two explicitly white form panels.

Inputs share 14dp rounding, subtle gray outlines, pale neutral fill, 16dp field spacing and visible password controls. First/Last Name stay side by side; other inputs use the available full form width. Recovery, terms and account links use readable navy text and wrap instead of clipping. Button height is a minimum rather than a fixed constraint, allowing enlarged text. The layout retains the existing password checklist/error feedback and uses no new social-authentication buttons.

### 4. How it works: functions, inputs/outputs and data flow

`AuthFormStyle.text(size, weight, color)` returns a bundled Montserrat `TextStyle` with matching variable-font weight. `theme(base)` returns a local light copy of the inherited theme, used only below `AuthFormShell`; it does not write the user's theme preference or modify `main.dart`. Shared `primaryButton` and `linkButton` getters return visual styles, including disabled/loading-compatible colors and minimum targets.

`AuthFormShell(page, child, onBack)` accepts a page identifier for stable keys, the existing screen-owned form and an optional back callback. Its scroll content uses a Stack: the photo occupies the top, and the white panel starts at `photoHeight - 28`. A minimum panel height fills a tall view without forcing fields into a fixed height. The viewport resizes with the keyboard; the photo's full-view-based height stays stable, and the scroll view can expose any field/button. Header and form SafeAreas protect system edges, with bottom breathing room and a 440dp maximum inner width for wider devices.

`AuthFormHeading(title, subtitle)` draws the original asset and existing brand text plus a semantic heading. `AuthFormField(...)` receives the same controller, keyboard type, capitalization formatter, validator, server error, supporting widget and password callback from `_buildField`. It supplies consistent presentation and forwards those inputs into `TextFormField`; it does not validate or submit independently. Next/Done keyboard actions and field scroll padding improve movement through the existing form.

```text
Login field/controller -> existing Form validation -> unchanged _login
  -> unchanged AuthService.login -> existing Django REST endpoint
  -> unchanged SessionService.saveUser -> AppRoutes.forUser

Sign Up six controllers + existing accepted terms -> unchanged _signUp
  -> unchanged AuthService.signUp -> existing Django validation
  -> existing success dialog -> typed route returns the username to Login
```

Annotated example: at a 320x568 view with a 280dp keyboard inset, the viewport becomes shorter while the photo height stays 180dp. Scroll to Log In/Sign Up; pressing an empty form shows the original field errors and remains scrollable. Neither test nor layout creates an account to demonstrate this.

### 5. Backend / API behavior

None changed. DRF endpoints, payloads, error mapping, name capitalization, password policy, terms acceptance, session persistence/Remember me, recovery, signup return-value prefill and authorized post-login destinations are retained. `_login`/`_signUp` and adjacent action methods match their original source after whitespace normalization; signup formatter/checklist/success-dialog helpers also match. Eleven protected files/assets matched their pre-task SHA256 values, including AuthService, SessionService, routes, password policy, recovery/legal/theme components, main, pubspec and the campus/logo images. No Apple/Google authentication was added.

### 6. Database / migration impact

None. No Django/backend files, database models, migrations, dependencies, endpoint settings, working accounts, session records or stored preferences were modified. Tests use isolated widget state and existing mock/test infrastructure. No app installation, emulator/hardware action, running-session reset or deployment was performed.

### 7. Tests performed

- **32/32 focused Flutter tests passed**, including existing layout/spacing, password-policy and recovery-input coverage. New checks cover 320x568, 360x640, 412x915 and 640x360 layouts across selected light/dark themes; actual panel overlap; original assets; Montserrat; gold primary buttons; side-by-side names/full-width remaining fields; 280dp simulated keyboard; 2x text; original empty-field validation; reachable buttons; real typed Sign Up routing and returned-identifier prefill.
- **Static analysis of all six changed source/test Dart files reported no issues** (9.2 seconds). Formatting was applied with the installed SDK; scoped whitespace checks passed for all nine source/test/document files, and tracked-file `git diff --check` passed. The first run found an unused removed-layout color alias and stale/test-only assumptions (old LastName text, Ahem metrics, password wording and an untyped mock route); these were corrected before the passing run. Production routing and password policy were not changed to satisfy the tests.
- Four actual Flutter PNGs were captured with the bundled Montserrat/Material icon fonts and original image assets: `renders/login-top.png`, `login-submit.png`, `signup-top.png`, `signup-submit.png`. Both top views and the scrolled signup action view were visually inspected. These are rendered app widgets, not generated mockups.
- Source verification passed for all eleven protected files/assets, original Login/Sign Up action methods and signup helper classes. The design skill's shared external kit was missing, so no kit gate or universal accessibility certification is claimed.

Reproduce the focused checks from the Flutter folder:

```powershell
flutter test --no-pub test/login_layout_test.dart test/signup_spacing_test.dart test/auth_form_responsive_test.dart test/password_policy_test.dart test/recovery_code_input_test.dart
flutter analyze --no-pub lib/module_app/screens/login_screen.dart lib/module_app/screens/signup_screen.dart lib/module_app/screens/components/auth_form_shell.dart test/login_layout_test.dart test/signup_spacing_test.dart test/auth_form_responsive_test.dart
# Optional real-widget renders; directory is local evidence only.
$env:AUTH_LAYOUT_CAPTURE_DIR = '../scratch/mobile-auth-white-panels-20261102/renders'
flutter test --no-pub test/auth_form_responsive_test.dart
```

### 8. Remaining limitations, troubleshooting and safe practice

The keyboard is simulated in widget tests; no physical Android/IME session or successful live account submission was performed. Exact reference-image matching cannot be claimed because no reference image was attached. These layout-only checks do not independently prove Django/network availability or change an existing session. The user can view the changes with their normal Flutter hot reload/run workflow; no restart or device action was forced.

If an old navy form remains, confirm the running target uses the updated Login/Sign Up sources and reload the app. If a real keyboard covers an action, inspect the screen's existing Scaffold resize flag and shared scroll view before adding keyboard padding: adding the full inset again would double-count it. If a label/font looks different in a capture, load the bundled font rather than relying on Flutter test Ahem text metrics. Long recovery/terms copy is intended to wrap.

Safe practice: edit only the shared `overlap` value from 28dp to 24dp, run the focused responsive test and inspect that panel top remains above photo bottom and the primary button is reachable at 320x568 with 2x text. Restore 28dp and rerun. Then open Sign Up and return with Log In without entering/submitting real account data; Login's earlier identifier should remain. Never change AuthService, route types or session storage to adjust visual spacing.

## App bar uses the signed-in profile photo and name — October 30, 2026

### 1. Cause / reason

The user requested replacing the CampusHub logo/wordmark in the Flutter app bar with their profile picture and name. Confirmed: the main dashboard, seller shell and dashboard Messages route used `CampusHubBrand`. An existing unused `HeaderProfileButton` only showed an initial and did not display the saved photo or name. No missing-picture URL was invented.

### 2. Exact files changed — current lines and anchors

| File / current line | Nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/navigation/header_profile_button.dart:9` | `class HeaderProfileButton` | Reused the existing header control for real photo/name, fallback, accessible profile action and responsive text. |
| `campushub/lib/module_app/screens/dashboard_screen.dart:239` | `title: HeaderProfileButton(` | Replaced the Messages brand title; the main header replacement is at HeaderProfileButton in build. Existing actions remain. |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart:156` | `void _openProfile()` | Made profile navigation work from both the drawer and header; seller AppBar now shows the authenticated identity. |
| `campushub/lib/module_app/screens/profile_page.dart:37` | `final ValueChanged<AuthUser>? onUserChanged;` | Added an optional notification after existing profile refresh/photo upload persists the authenticated user. |
| `campushub/test/header_profile_button_test.dart:7` | `void main()` | New focused coverage for real-photo URL/failure fallback, name fallback, tapping and narrow/large-text layouts. |
| `campushub/test/dashboard_header_test.dart:15` | `void main()` | Updated identity expectations and profile navigation; screenshot harness now loads actual bundled Inter/Montserrat. |
| `campushub/test/seller_workspace_test.dart:361` | `profile seller header and six home sections` | Updated profile-name/avatar expectations and verified the seller header opens Profile without popping its own route. |
| `campushub/test/profile_photo_test.dart:74` | `Future<void> open(` | Verified successful upload notifies the parent with the saved photo URL. |

This existing guide and `CAMPUSHUB_CONTEXT.md` record the change. `scratch/profile-header-20261030/renders/` contains actual Flutter captures; its `update_tests.py` and `update_docs.py` are one-time edit/report helpers. Existing brand assets/component were retained for other uses; no login/startup redesign or asset deletion.

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Logo plus CampusHub wordmark in the three headers | Stored profile photo plus authenticated full name | Implements the requested personal identity in the existing space. |
| An initial-only unused header icon | 36dp circular photo with an initial/person fallback | Uses an actual saved photo when available and handles missing or failed images. |
| Brand typography | Existing Montserrat identity style, navy, 14dp/600 weight | Matches the profile/drawer identity styling without changing app-wide fonts. |
| Seller profile helper always popped the current route | Close the drawer only when it is open, then use the existing Profile destination | Makes the new header action safe when no drawer is open. |
| Profile upload updated its own screen/session only | Optional callback updates the visible header after the existing save | Reflects the changed photo without another login or a polling loop. |

Menu, search (including My Products search), notifications, bottom navigation, drawer destinations and seller access checks remain. Name can wrap over two lines and ellipsize when necessary; the tooltip and accessibility label retain the full name. The header control has at least a 48dp hit height and native InkWell focus/press feedback. Normal AppBars remain at least 56dp high and grow for enlarged text. No new animation was added.

### 4. How it works — functions, inputs/outputs and data flow

`HeaderProfileButton(user, onPressed, avatarKey, nameKey)` takes the already-loaded `AuthUser` and the existing profile-navigation callback. `build()` uses `fullName`, then actual first/last name parts if full name is empty. An absent identity shows the neutral Profile label and person icon. It reads `resolvedProfilePhotoUrl`, which resolves the stored account photo path against the existing configured API base URL. `CircleAvatar.foregroundImage` loads it; the child initial/person icon remains available if the URL is missing or the image fails. The name and avatar share one accessible View profile action rather than separate duplicate buttons.

`DashboardScreen._loadUserName()` still retrieves session identity through the existing session service. The main header passes `_user` to the shared widget. Tapping it selects the existing Profile tab. Messages uses the same identity and closes its own route before selecting Profile. The existing menu/search/notification handlers are unchanged.

`SellerDashboardPage` passes its existing authenticated user, or the profile identity returned after its standalone Profile save. `_openProfile()` closes an open drawer only; it then calls the existing parent `onProfile` callback or pushes the existing standalone Profile screen. It does not pop the seller page just because the header was tapped. Parent-provided user changes clear the temporary identity override.

`ProfilePage.onUserChanged` is optional, so existing callers continue to work. `_refreshProfile()` and `_setProfilePhoto()` keep their existing authenticated API/session updates and notify the parent only after obtaining/saving the current user's returned identity. Dashboard/seller parent callbacks check matching user IDs and mounted state before updating the header.

Annotated example: an account with `full_name: "Actual Student"` and `profile_photo_url: "/media/profile-photos/account/photo.jpg"` displays that stored image and name. If the image cannot load, A appears in the same circle. No student ID/email is added to the header, and a missing account is not given a fabricated person name.

### 5. Backend / API behavior

No endpoint, authentication, seller approval, permission or upload contract changed. The header uses existing authenticated account fields and the existing profile-photo read/upload flow. The new callback is an in-memory UI notification, not an API write or new request. Existing seller access checks still control seller tools.

### 6. Database / migration impact

None. No model/migration, database setting, stock/order data, stored identity or live photo was modified for this UI task. No localhost/online runtime switch or remote deployment was performed.

### 7. Tests performed

- All 49 affected Flutter tests passed together: header component, dashboard header/navigation, seller workspace, profile-photo flow and Profile page.
- After improving the screenshot font loader, all five dashboard header cases passed again with bundled Inter and Montserrat: 320, 375, 390 and 844dp, including 320dp at 2× text. Actual captures were inspected; the first screenshot harness lacked Inter, which was corrected in the test harness rather than changing product styling.
- After increasing AppBar allowance for two lines of enlarged identity text, both 320dp portrait and 844dp landscape seller cases at 2× text passed.
- Component coverage includes 280, 320, 414 and 768dp at 2× text, long names, button taps, real saved URL selection, failed-image fallback, and missing identity/name parts. Existing profile upload tests now check that the parent receives the newly saved URL. Navigation tests check header-to-Profile, search/notifications, unchanged seller sections and drawer access.
- Final scoped Flutter analysis passed with no issues across the four changed production files and four affected/new test files. No backend test run was needed for this presentation/callback-only change. Test records/HTTP responses remain isolated fixtures; no real account photo was uploaded.

### 8. Remaining limitations, debugging and safe practice

No physical-device interaction, full screen-reader audit or APK deployment was performed. Hot reload/restart the running Flutter development app to load the new header. Older guide sections describing a brand header are historical; this section is the current direction.

If an initial is shown, check the existing account's profile picture in Profile. Missing pictures and image-load failures intentionally use the fallback. A failing photo request uses the same API/media configuration as Profile; do not hardcode a replacement URL. If a name is abbreviated, use its tooltip/accessibility label or open Profile to read it in full. Profile updates only notify the matching mounted user, preventing a late upload from replacing another account's header.

Safe practice: run `flutter test --no-pub test/header_profile_button_test.dart` from `campushub/`. Change only the local test account's full name to a longer Unicode name and verify all widths still fit and tapping the header calls the test callback once. Restore the fixture and run `flutter test --no-pub test/dashboard_header_test.dart test/profile_photo_test.dart`. Confirm header-to-Profile navigation and saved-photo callback still pass. These tests do not change a working account or database.

## Navbar selection without a background box — October 30, 2026

### 1. Cause / reason

Alongside the Product Details reference-layout request, the user asked to remove the navbar container when clicked. Confirmed: `_buildNavItem` painted a persistent7% navy rounded `DecoratedBox` behind the selected glyph. The request is applied to that selected-item background on the existing shared navbar.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` |198 `_buildNavItem`;259 `SizedBox`;262 `Center` | Removed only the selected-background `DecoratedBox`/decoration, keeping its36×28dp layout slot and original icon/switcher. |
| `campushub/test/floating_bottom_navbar_test.dart` |213 large-text/reduced-motion;262 switching;328 `navbar-indicator` absence;474 new capture output | Updated existing tests to require no indicator or nested decorated box for every selected index, preserving glyph/state/callback/geometry checks. |
| `campushub/DESIGN.md` |161 `bottom-navigation`;285 floating-navigation section | Recorded the current floating geometry and unboxed selection. |
| `CAMPUSHUB_CONTEXT.md` |3 reference-layout/nav summary | Saved current direction and actual verification. |
| `docs/mobile-profile.md` | This section | Current learning/debugging report; Product Details' companion report lists its related files. |

### 3. Changes made

| Before | After | Why |
| --- | --- | --- |
| Selected glyph inside a navy-tinted rounded box | Same filled/navy glyph directly on the dock | Removes the persistent clicked-item container as requested. |
| Tests required the tint | Tests require no selected-item decoration and still verify selected semantics/icons | Checks the requested visual change together with functioning navigation. |

The floating white dock, neutral outline/shadow, labels, native press/focus feedback, selected semantics, tooltips, existing restrained selection motion and safe-area geometry remain. Regular users retain five destinations. Approved sellers retain the four surrounding destinations and existing gold Add Product action. This revision preserves the recent photo/name app-bar work documented above.

### 4. How it works — functions, inputs/outputs and data flow

`FloatingBottomNavbar(currentIndex, onTap, items, onCenterActionTap, colors)` receives existing parent state/callbacks. `_buildNavItem(context, index, item)` compares index to currentIndex and returns the same semantic button/InkResponse, selected glyph and label. Its icon slot now contains `Center(AnimatedSwitcher(...))` directly, without a `DecoratedBox`. Tapping still invokes `onTap(index)`; the parent selects the original root page and rebuilds the navbar. The selected state continues to drive filled/outline glyphs, navy/muted color and accessibility. The seller center action still invokes its separate callback, not a page index.

Annotated example: tap Marketplace(index1) → parent selects1 → Marketplace uses the filled shop icon/navy label and selected semantics → its slot has no background container. Tap Services(index2) → the same behavior follows2 without moving/resizing the dock. The36×28dp visual icon slot does not reduce the existing full-height48dp+ tap region.

### 5. Backend / API behavior

No route destination, authentication, seller eligibility, permissions or API changed. Removing a decoration does not fetch or write data. Profile/header and seller Add Product workflows retain their original callbacks.

### 6. Database / migration impact

None; no model/migration/configuration/dependency/record change or deployment.

### 7. Tests performed

Final combined **43/43 Flutter tests passed in11seconds** across Product Details, navbar, ProductItem, notification-product and dashboard center-action suites. Command and product evidence are in [the companion guide](product-details-status-inventory.md). Existing navbar tests exercise every tab, normal/seller configurations, rapid selection, filled icons, selected semantics, preserved outer bounds/safe-bottom/body clearance and48dp+ touch targets at320/390/768dp,844dp landscape,2×/3× text and reduced motion. Five changed Dart files passed analysis with no issues. Final format check reported5 files,0 changed in0.11seconds; scoped `git diff --check` passed.

Four actual-font navbar captures were produced with `--dart-define=CAPTURE_FLOATING_NAV=true` in `scratch/floating-navbar-no-selection-20261030/`; normal and seller390dp renders were inspected. Capture location was changed so the previous October29 evidence remains. No physical-device render or app build/install is claimed.

### 8. Remaining limitations / debugging / safe practice

Temporary native tap ripple/hover/focus feedback remains; it is not the removed persistent selection box. The outer floating dock and gold seller action retain their containers. No app/device/server launch/restart/hot reload was performed; the user controls Ctrl+F5. Full physical-device/screen-reader verification is pending.

Safe exercise: run `flutter test --no-pub test/floating_bottom_navbar_test.dart`. Change the isolated test's initial selected index to another valid destination and confirm the matching filled icon/selected semantics follow it while no `navbar-indicator-*` decoration exists. Restore the test value and rerun. This exercises only local widget state and does not alter accounts or permissions.

## Shared floating bottom navigation — October 29, 2026

Current request: make the existing mobile navbar float. This supersedes the old full-width/flush-edge navigation treatment for both regular accounts and approved sellers, while preserving their existing destinations and action permissions.

Design direction: a quiet white navigation dock, navy #1A1851 icons/text, existing gold #FCB315 seller action, neutral border #E2E4EC and a7% navy selected background. Keep bundled Inter11 labels and existing Iconsax/custom Home/plus artwork. One rounded surface, subtle downward shadow, no gradients/blur, no entrance/bounce or additional navigation steps.

    regular:  [ Home | Marketplace | Services | Facilities | Profile ]
    seller:   [ Home | Marketplace | raised Add Product | Services | Facilities ]
               12dp side gaps       12dp above system bottom inset

| Before | After | Why |
|---|---|---|
| White bar flush with all edges | Inset rounded dock, max620dp | Clear floating shape on phones and wide layouts |
| Full-width top rule | Rounded neutral outline and soft shadow | Separate navigation from the page |
| Selected glyph only | Filled glyph plus quiet rounded indicator | Make current location easier to identify |
| Tight narrow-screen labels |4dp internal label inset | Keep Marketplace and Add Product visually separate |

### 1. Cause / reason

Confirmed: FloatingBottomNavbar previously rendered a full-width background with only a top border. SafeArea was inside that surface, so the background extended to the screen bottom. Existing tests explicitly required flush edges. The latest user request authorizes replacing that geometry with a floating dock.

### 2. Exact files changed

Repository-relative paths; line numbers describe this revision and anchors remain stable.

| Folder / file | Current line / nearby anchor | Change |
|---|---|---|
| campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart |72 layout constants;198 _buildNavItem;333 _buildCenterActionButton;396 build | Floating dock, selected background, narrow-label spacing, outer safe area |
| campushub/test/floating_bottom_navbar_test.dart |19 seller fit;213 large-text/reduced-motion;262 geometry/tab switching;406 optional captures | Floating bounds, safe-area/body clearance, selected state, seller action, label separation and renders |
| docs/mobile-profile.md |3 Shared floating bottom navigation | Current eight-part guide, functions/data flow, debugging and exercise |
| docs/mobile-seller-application.md | Shared floating navigation cross-reference | Explain preserved seller mapping/action and verification |
| CAMPUSHUB_CONTEXT.md |3 latest floating-navbar record | Current direction and checks |
| campushub/DESIGN.md | Floating bottom navigation | Current geometry/palette/interaction specification |

### 3. Changes made

The white dock has28dp corners,12dp minimum side gaps, a620dp maximum width and12dp below it in addition to the device bottom inset. A neutral outline and low-opacity navy shadow replace the full-width top rule. The system-navigation color request is transparent; actual OS handling remains device-dependent.

The selected destination retains its filled icon and gets a7% navy rounded background within a36x28dp icon layout area. Supporting glyphs remain20dp. Existing labels, variable-font weights, tooltips, semantics, native ink/focus feedback,220ms selection motion,140ms glyph switch and reduced-motion behavior remain. No new decorative animation was added.

The seller56dp gold circle still rises16dp above the dock surface. Its full hit area remains inside floating-navbar-frame, without a separate overlay/FAB. Four surrounding destinations retain the same indices and Add Product remains an action. Ordinary accounts keep five destinations including Profile. Labels now have4dp side padding before existing scale-down behavior, protecting separation on narrow screens.

### 4. How it works: functions, inputs/outputs and data flow

DashboardScreen reads the existing authenticated seller state and passes currentIndex, _goToTab and (for approved sellers only) _openAddProduct to FloatingBottomNavbar at dashboard_screen.dart:434. No dashboard routing/authentication code was edited.

- effectiveItems returns the existing five-destination set or four seller destinations around the action.
- build takes those items and the existing callbacks/color inputs. It wraps the measured dock in SafeArea, centered Align, max-width ConstrainedBox and padding. floating-navbar-pill marks the rounded surface; floating-navbar-frame includes the seller action's reserved rise.
- _buildNavItem takes index/item and optional seller topInset. It returns the same semantic destination and InkResponse, now with a quiet selected background and4dp label inset.
- _buildCenterActionButton takes measured navHeight and uses the original seller callback. It keeps the56dp circle, existing icon and full slot tap area; extra bar height aligns labels at enlarged text settings.
- _goToTab at dashboard_screen.dart:154 still changes the existing root page; _openAddProduct at184 still opens the original product form. Center action never selects a destination index.

Scaffold.bottomNavigationBar reserves the entire footer height. The body therefore ends above the dock/frame, so the dock does not hide the last page content. No extendBody or new Stack overlay was added to DashboardScreen.

Annotated geometry example: on a390dp viewport the12dp side gaps give a366dp dock. With a24dp bottom system inset, its lower edge is36dp above the viewport bottom (24+12). On a768dp viewport the dock caps at620dp and centers. Seller rise is included in layout height rather than painted outside the hit region.

### 5. Backend / API behavior

Unchanged. No endpoint calls, role/access changes, account/session changes or new seller status logic. The existing Dashboard decides whether to supply the center action. This is presentation of the original navigation and callbacks only.

### 6. Database / migration impact

None. No models, schema, migrations, records, dependencies or image assets changed.

### 7. Tests performed

Final result:16/16 tests passed4s across floating_bottom_navbar_test.dart, dashboard_center_add_button_test.dart and home_card_background_test.dart, including the optional capture harness. Two-file analysis reported No issues found3.2s. Final formatting checked2 files with0 changes; scoped git whitespace check passed.

Existing coverage verifies role item sets, action-vs-page behavior, routes, selected semantics, stable bounds during rapid selection,48dp+ targets, large text up to3x and reduced motion. Updated geometry checks cover320/390/768dp,24dp bottom inset, centered max width and body clearance. Seller tests also cover844x390 landscape and the reserved rise/hit area. Each tab's selected background follows the current index.

Four actual Flutter RepaintBoundary captures are in ignored scratch/floating-navbar-20261029:390dp regular/seller,320dp2x seller and844x3902x regular. Inspected these in one review batch, corrected narrow label separation, then confirmed normal/seller/narrow captures. The preview contains only a test-harness label and real navigation widgets, without fake catalog metrics or records.

The first run contained an obsolete test expecting no selected indicator. Updated it for the requested indicator. The capture harness also needed to restore debugDisableShadows in finally before Flutter's invariant check; no production behavior was changed for that test-only cleanup. Rendering with real shadows avoids Flutter tests' default hard-shadow approximation. Exact installed Iconsax font metadata was read locally; no package was installed.

Commands from campushub:

    flutter test --no-pub test/floating_bottom_navbar_test.dart test/dashboard_center_add_button_test.dart test/home_card_background_test.dart --dart-define=CAPTURE_FLOATING_NAV=true
    flutter analyze --no-pub lib/module_app/widgets/navigation/floating_bottom_navbar.dart test/floating_bottom_navbar_test.dart
    dart format lib/module_app/widgets/navigation/floating_bottom_navbar.dart test/floating_bottom_navbar_test.dart

### 8. Remaining limitations / troubleshooting / safe practice

Respected the saved user preference to control Ctrl+F5: no app run/build/install/restart or native device commands were performed. Widget captures do not prove physical Android/iOS system-bar behavior, TalkBack/VoiceOver or touch performance. The inherited compact labels stay unscaled visually, with full names available in semantics/tooltips; no full accessibility certification is claimed.

If navigation still appears flush after a user-chosen reload, inspect FloatingBottomNavbar.build and the actual shared component import. If the raised seller button clips, verify floating-navbar-frame includes the16dp topInset and no external clip/height overrides it. If content is obscured, retain Scaffold.bottomNavigationBar rather than placing this widget over the page.

Safe exercise: in the isolated width test, change its test viewport from390 to414dp and run the named navbar fit tests. Expected dock width is390dp (414-24); bottom clearance remains system inset+12dp and selected index remains correct. Restore the test viewport afterward. Do not change real roles or submit a product to test the center action.

## Home category highlights removed - October 29, 2026

The user's latest request removes the preferred-category ActionChips from Home, including Snacks/Beverages highlights. Preference editing, saved values and Marketplace category filters retain their existing inputs/outputs and persistence. `HomePageState.build` now renders greeting -> banner without mapping `preferredCategories` into chip widgets. This supersedes only the Home shortcut rendering described in historical sections below. Exact files/lines, eight-part implementation report, data flow, debugging, verification and safe practice are recorded in [the existing mobile seller/Home guide](mobile-seller-application.md#home-category-shortcuts-and-sales-period-menu-placement---october-29-2026). Safe check: inspect Home with existing saved preferences and confirm the chip row is absent while Profile preferences still show those saved selections; use `home_page_test.dart` without writing real preference records. Combined validation passed 74 tests; physical-device behavior was not inspected.

## Drawer render test import diagnostics - October 28, 2026

1. **Cause / reason:** confirmed package-location problem. The screenshot test was in `scratch/home-sidebar-20261028/drawer_render_test.dart`, outside the Flutter package rooted at `campushub/pubspec.yaml`. Neither the repository root nor its scratch ancestors has a `pubspec.yaml`. The pasted 36 diagnostics comprise eight unresolved imports and 28 dependent symbol/type errors. `shared_preferences` and `flutter_test` are already declared, and `campushub/.dart_tool/package_config.json` resolves them, Flutter and CampusHub. The selected import was not a missing dependency. The file's location also prevented the editor from associating it with the Flutter SDK needed for `dart:ui`.
2. **Exact files changed / current anchors:** moved the scratch Dart file to `campushub/test/drawer_render_test.dart:1` (imports); formatted its existing code. Key anchors are `:11` (`main`), `:15` (`setMockInitialValues`), `:31` (`AuthUser.fromJson`), `:47` (`CampusHubDrawer`), `:59` (expectations), and `:71` (`File`). Updated this guide at line 2 and `CAMPUSHUB_CONTEXT.md:3`. Running the existing harness refreshed `regular-light.png`, `regular-dark.png`, `seller-light.png` and `seller-dark.png` in `scratch/home-sidebar-20261028/`.
3. **Changes made:** relocated the test into the existing Flutter `test/` directory so package imports and test-only APIs receive the correct context. Preserved all imports, assertions, role/theme combinations, synthetic identity and relative screenshot destination; no dependency additions or diagnostic suppression. A temporary placement under `tool/qa/` resolved imports and ran successfully but produced `invalid_use_of_visible_for_testing_member` for the preferences mock; the final standard test location resolves that warning too.
4. **How it works / functions, inputs, outputs and data flow:** `main()` registers one `testWidgets` case. `SharedPreferences.setMockInitialValues({})` supplies isolated preferences. The test loads existing font assets, passes an in-memory `AuthUser`, role and theme to the real `CampusHubDrawer`, checks its Home labels and captures the `RepaintBoundary` as PNG bytes. Its two role values multiplied by two theme values produce four files. There is no real login or backend request in this harness. Example: `seller=false, dark=true` renders the regular-user drawer inside a dark surrounding theme and writes `regular-dark.png`; the actual drawer remains white. The `../scratch/...` destination is resolved from the Flutter package working directory, so moving the source does not change the output path. Using the conventional test directory lets the existing package configuration and Flutter tooling work without duplicating dependencies.
5. **Backend / API behavior:** unchanged. No application source, Django service, authentication, permission, navigation or API changes; `backend/core/modules/facilities/mobile_services.py` was not edited.
6. **Database / migration impact:** none. No dependencies, models, migrations, saved sessions or working records changed. The sample identity exists only in the widget test.
7. **Tests performed:** final `dart format --output=none --set-exit-if-changed test/drawer_render_test.dart` reported one file, zero changes; `flutter analyze --no-pub test/drawer_render_test.dart` reported **No issues found** (1.3s); `flutter test --no-pub test/drawer_render_test.dart` passed its one test, covering all four renders. The first sandboxed format attempt stalled and was cancelled; a direct Dart attempt reported denied access to the user analytics configuration. Completed checks used outside-sandbox execution for the installed SDK/user cache. No full application suite, backend test, device installation or hot reload was run for this test relocation.
8. **Remaining limitations / troubleshooting / safe exercise:** close the old scratch editor tab and open `campushub/test/drawer_render_test.dart`. If old diagnostics persist, run **Dart: Restart Analysis Server**. Existing screenshot output requires the `scratch/home-sidebar-20261028/` directory and running from `campushub/`; these conditions were present during verification. This run verifies rendering/assertions, not pixel equality with a golden image. Safe exercise: follow `AuthUser.fromJson -> CampusHubDrawer -> RepaintBoundary -> PNG` at the anchors above, then run the commands below without editing account data. Verify analysis has no issues and the test reports one pass; four PNG timestamps should update. This is a local render fixture, not an alternate app startup.

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\campushub
flutter analyze --no-pub test/drawer_render_test.dart
flutter test --no-pub test/drawer_render_test.dart
```

## White sidebar clarification - October 28, 2026

The user clarified **white**, not wide. This supersedes the earlier theme-dependent drawer surface; the Home-first navigation below remains current.

1. **Cause / reason:** `CampusHubDrawer.build()` inherited dark-theme surface/text colors. The requested sidebar should stay white, including when the surrounding app uses dark mode.
2. **Exact files changed / anchors:** `campushub/lib/module_app/widgets/navigation/seller_drawer.dart:188` (`build`, palette at 190, system overlay at 214); `campushub/test/seller_drawer_test.dart:95` (white surface), `:133` (system icons), `:171` (navy menu text); this existing guide and `CAMPUSHUB_CONTEXT.md:3` (newest context entry). Four files for this clarification; one runtime file.
3. **Changes made:** use existing white surface, navy primary text/icons, secondary text and border tokens for both roles in either app theme. Keep the existing subtle navy selected surface and gold indicator. Use dark system-bar icons against the white drawer. Existing width, Montserrat weights, Home-first ordering, seller-only tools and bottom navigation remain unchanged.
4. **How it works / inputs, outputs and data flow:** `CampusHubDrawer.build(context)` still consumes the real user, approval, selected destination and callbacks. Its local colors now use existing `HomeAppColors` constants and `Colors.white` rather than `Theme.of(context).brightness`; its output is the same native Drawer with a consistently white surface. The existing `SellerDrawer` wrapper uses that shared component, so seller tools inherit the same appearance. Example: switching the surrounding app to dark mode leaves the drawer white and its Home label navy; Home still calls the existing tab/return handler. This keeps the correction local to navigation without changing the app-wide theme.
5. **Backend / API behavior:** unchanged. No route, request, authentication, seller approval or other permission/business-logic changes in this color correction.
6. **Database / migration impact:** none. No models, schema, saved sessions, dependencies or working records changed.
7. **Tests performed:** all **41 Flutter tests passed** in 12 seconds across drawer, shared Home, seller workspace, search and the local render harness. Updated assertions verify white background, navy menu text and dark system icons under light/dark app themes for both roles; existing responsive, font, selection, Home navigation and Logout coverage remains. Two-file Flutter analysis reported **No issues found** (1.8s); Dart formatting and scoped whitespace checks passed. Refreshed four Flutter screenshots under `scratch/home-sidebar-20261028/`; visually inspected seller/non-seller renders under a dark surrounding theme and confirmed white drawers. No web-kit gate score or native-device rendering claim.
8. **Remaining limitations / troubleshooting / safe exercise:** no emulator/device installation, restart or hot reload was performed. Apply your own Flutter Hot Reload and reopen the menu. Safe exercise: switch the app to dark mode, open the sidebar and verify white background/navy Home text, then tap Home and confirm existing role-aware content; no account or marketplace edits are needed. On shorter screens, scroll to later groups; fixed Logout remains accessible. The former `seller-dark.png`/`regular-dark.png` filenames mean dark surrounding app theme, not a dark drawer.

## Home first under Overview for both roles - October 28, 2026

This supersedes the earlier shared-sidebar decision to omit Home. Keep the existing shared, role-aware Home; do not add a duplicate Seller Dashboard menu.

1. **Cause / reason:** the shared drawer omitted Home, so users could not return to the existing Home from the sidebar. The retained internal `SellerDestination.overview` also had a Dashboard label. The user explicitly requested **OVERVIEW > Home** first for both sellers and non-sellers, preserving other groups and bottom navigation.
2. **Exact files changed / current anchors:**

   | File | Current line and anchor | Change |
   | --- | --- | --- |
   | `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 22 `overview`; 68 `destinations`; 424 `onSelected` | Home label/icon, first shared destination, seller-drawer return callback |
   | `campushub/lib/module_app/screens/dashboard_screen.dart` | 265 `_openDrawerDestination`; 343 `selected: switch` | Both roles select the existing Home tab; highlight Home when tab 0 is active |
   | `campushub/test/seller_drawer_test.dart` | 27 `role drawer` | Home ordering, heading/font/selection and role/size/theme coverage; scroll to lazy headings/header before inspection |
   | `campushub/test/seller_home_entry_test.dart` | 76 `personal drawer routes` | Services-to-Home and already-on-Home navigation retain the same shell, role-aware content and session |
   | `campushub/test/seller_workspace_test.dart` | 140 `standalone seller Home`; existing `seller additions share Home` | Existing named-route fallback and seller-tools-to-Home callback are both exercised |
   | `campushub/test/dashboard_search_appbar_test.dart` | 10 `drawer keeps Home` | Expect Home in the drawer while preserving the other primary tabs and search behavior |
   | `docs/mobile-profile.md` | 2 this section | Implementation report, functions/data flow, verification and learning exercise |
   | `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Current navigation requirement and verified outcome |

   Eight project files changed; two application files. The ignored `scratch/home-sidebar-20261028/drawer_render_test.dart` is a local screenshot harness with visual fixtures only, not an app entry point.
3. **Changes made:** the shared drawer now starts with OVERVIEW / Home, then My Activity, conditional Seller Management, Communication, Account and bottom Logout. The existing `overview` enum value is reused; its display label becomes Home and its icon uses the existing outline Home symbol. No separate Seller Dashboard row is introduced. Existing Montserrat weights, width, spacing, navy/gold selection, photo/profile actions, theme, scrolling, SafeArea and bottom navigation remain as implemented.
4. **How it works / functions, inputs and outputs:** `CampusHubDrawer.destinations` takes the existing `sellerApproved` input and produces the common Home-first list plus approved-only tools. `_openDrawerDestination(destination)` closes the drawer; for `overview`, `_goToTab(0)` selects the already-existing Home page rather than pushing a new dashboard. Its output is the existing tab/shell state, so Home keeps the same role-aware seller highlights, catalogs and session. The selected input maps tab 0 to `overview`, tab 4 to Account Settings and other tabs to no selected drawer row. In a seller tool, `SellerDrawer` handles only the sidebar Home action with the supplied `onBackToCampusHub` callback after closing the drawer. Existing `_backHome()` then returns to the owning DashboardScreen, or uses existing `AppRoutes.dashboard` when opened standalone. The seller workspace's internal Back action and other destinations retain their original handlers.

   Annotated example: `Services tab (index 2) -> menu -> Home (overview) -> _goToTab(0)`. The Home tab is now selected; an approved seller still sees the existing seller additions, and a non-seller does not gain seller tools. Selecting Home again closes the drawer without adding a route or replacing the shell.
5. **Backend / API behavior:** unchanged. Existing session/status checks and role-aware Home loads run through their current services. Home is common navigation; seller tools still depend on existing approval checks and Django authorization. No authentication, marketplace/order/payment, booking, analytics, FIFO or Apriori behavior changed.
6. **Database / migration impact:** none. No model, schema, dependency, working record, saved session or app-data changes. Screenshot identities and workspace responses exist only in local test fixtures.
7. **Tests performed:** final Flutter run passed **41 tests** in 15 seconds across the four affected suites plus the local screenshot harness. Coverage includes both roles; light/dark; 375x812, 320x640 at 2x text, 844x390 landscape at 2x and 768x1024 at 1.3x; menu callbacks/48dp targets/typography/Logout; Home tab selection and stable shell; seller-tool callback and standalone `/dashboard` route; approval/revocation, search and retained bottom-navigation workflows. Six-file analysis reported **No issues found** (6.6s). Final format check reported **6 files, 0 changed**; scoped whitespace checks passed. Reviewed actual Flutter renders for seller/non-seller in both themes at 390x844, saved under `scratch/home-sidebar-20261028/`. The final renders show Home first with the existing active style; the longer seller list scrolls to Account Settings. Initial landscape tests required scrolling because adding a section moved lazy-built headings/header out of the viewport; final checks exercise those real scroll paths. The sandboxed test runner stalled, so the completed run used the authorized outside-sandbox execution. The optional design skill's token/gate scripts are absent; no web-kit gate score is claimed.
8. **Remaining limitations / troubleshooting / safe exercise:** no physical device, emulator, hot reload/restart, native installation or backend regression run was performed for this navigation-only change. Use your own Flutter Hot Reload action, reopen the menu, and verify OVERVIEW / Home appears first. From Services, tap Home and check that the bottom Home tab becomes active. For an approved seller, open My Products, then its sidebar Home and verify the shared Home/catalogs and seller additions return; a non-seller must not see Seller Management. At large text/landscape sizes, scroll the drawer to reach later groups; Logout remains at the bottom. Safe exercise: follow the `overview -> _openDrawerDestination -> _goToTab(0)` anchors above, then run `flutter test --no-pub test/seller_drawer_test.dart test/seller_home_entry_test.dart test/seller_workspace_test.dart test/dashboard_search_appbar_test.dart` without editing account or permission data. The shared role-aware Home is reused intentionally to avoid duplicate state and navigation destinations.

## Ctrl+F5 follows the selected device - October 28, 2026

This supersedes the forced Pixel 10a launch settings in the earlier emulator correction below. Normal login startup remains current.

1. **Cause / reason:** confirmed configuration issue: both default app launch entries contained `emulatorId: Pixel_10a`. The installed Dart Code 3.144.0 schema (`package.json:3386`, `deviceId`; `:3390`, `emulatorId`) explicitly says that `emulatorId` overrides the device selected in the status bar. The user wants Ctrl+F5 to follow that selection.
2. **Exact files changed / anchors:** `.vscode/launch.json:9` (`name: campushub`); `campushub/.vscode/launch.json:5` (`name: CampusHub (selected device)`); this guide's newest section; `CAMPUSHUB_CONTEXT.md:3` (latest context entry). Four configuration/documentation files; no application source changes.
3. **Changes made:** removed the fixed `emulatorId` from both entries and renamed the Flutter-folder entry from `CampusHub (Android emulator)` to `CampusHub (selected device)`. Kept the explicit `lib/main.dart` entry points, working directories, debug mode, existing phone/debug/release entries and root prelaunch task.
4. **How it works / inputs, outputs and data flow:** VS Code reads the chosen Run and Debug entry, takes the selected device from Flutter's status-bar picker, resolves the existing `program` and `cwd`, then launches the real app on that device. No new function is added. Example: choose the connected phone in the status bar, select `campushub` and press Ctrl+F5; the configuration no longer substitutes Pixel 10a. Select the emulator instead to run there. The root prelaunch task still calls `connect_android.py.main()` to discover an authorized physical Android phone and configure existing Django/chat port forwarding; it does not choose Flutter's run target.
5. **Backend / API behavior:** unchanged. This controls the development launch destination only; existing Django endpoints, authentication, seller permissions and normal startup remain as implemented.
6. **Database / migration impact:** none. No schema, records, dependencies, saved sessions, uninstall or app-data clearing.
7. **Tests performed:** PowerShell parsed both JSON-with-comments configuration files, checked their versions, confirmed every app entry point exists and verified that no launch entry contains `emulatorId` or `deviceId`; both passed. Scoped `git diff --check` passed. The installed extension schema confirms the selected-device fallback. Initial Python validation could not start because its underlying interpreter was inaccessible; the completed checks used PowerShell. An optional `flutter devices --machine` discovery stalled and was cancelled. No Flutter app tests, build, installation, device switch or actual Ctrl+F5 keypress was performed for this configuration-only fix.
8. **Troubleshooting / limitations / safe practice:** select the target in VS Code's bottom status bar (or `Flutter: Select Device`), select `campushub` in Run and Debug, then press Ctrl+F5. When only the Flutter folder is open, select `CampusHub (selected device)`. Stop an existing run first when switching devices: hot reload stays attached to the device already running. An offline or unauthorized phone must be reconnected/authorized; this fix does not repair device connectivity. Safe exercise: inspect the selected device label and launch configuration with a test editor tab open, run the app, and verify the launch output names the same device and `lib/main.dart`; do not submit any account or marketplace changes. Actual device launch remains for the user to verify.

## Sidebar Montserrat weight correction - October 28, 2026

1. **Cause / reason:** the preceding drawer used 700 for section headings/profile name, 600 for selected menu labels and 500 for academic metadata. The user specified a lighter, consistent four-role hierarchy.
2. **Exact files changed:** `campushub/lib/module_app/widgets/navigation/seller_drawer.dart:149` (menu labels), `:286` (profile name), `:296` (academic secondary text), `:332` (section headings); `campushub/test/seller_drawer_test.dart` (existing role/size/theme matrix assertions); this guide and `CAMPUSHUB_CONTEXT.md`. Four files, one runtime styling file.
3. **Changes made:** headings use Montserrat SemiBold **600**; every menu label, including the selected row and Logout, uses Montserrat Medium **500**; profile name uses Montserrat SemiBold **600**; program/year secondary text uses Montserrat Regular **400**. Existing font sizes, colors, spacing and selection tint/gold indicator remain.
4. **How it works / functions and data flow:** `_DrawerStyle.text(size, color, weight)` continues to call existing `ProfileStyle.identityText`, which returns the bundled Montserrat family, matching FontWeight and variable-font `wght` axis. Only role-specific arguments changed. Example: selecting My Products still updates its selected semantics/tint/indicator, while its label remains 500 instead of becoming 600. The shared component applies the same rules to seller and non-seller drawers.
5. **Backend / API behavior:** unchanged. No navigation, authentication/session, seller permissions, counts, requests or source data changes.
6. **Database / migration impact:** none. No working records, application data, dependencies or schema changes.
7. **Actual verification:** all **10 drawer tests passed** after the correction, covering both roles, light/dark, phone/landscape/tablet sizes, 2x text, actual color contrast, selected callbacks and Logout. Updated existing assertions check both FontWeight and Montserrat variable-font axis for the four requested roles. Scoped Flutter analysis of the two Dart files: **No issues found** (2.9s). Dart formatting and scoped whitespace checks passed. Mechanical type scan returned no findings; its limited Dart coverage is not considered visual proof. No fresh native screenshot or device interaction was performed for this weight-only correction, respecting the user's choice to control hot reload/emulator personally.
8. **How to test / limitations / safe exercise:** use your own Flutter Hot Reload action and compare the profile/section headings with medium menu labels and regular academic text. Tap My Products to confirm the gold/tint active state remains while label weight stays 500. Existing responsive tests are retained; actual appearance follows the bundled Montserrat variable font and device text scale. Safe exercise: locate the four call-site weights above, match them to these roles, and run `flutter test --no-pub test/seller_drawer_test.dart` without changing any account/permission data. Evidence: `scratch/mobile-sidebar-20261028/typography-tests.log` and `typography-analysis.log`.



## Shared student and seller sidebar - October 28, 2026

### 1. Cause / reason and design direction

The regular Home drawer repeated bottom-navigation destinations, while the separate seller drawer had a tall avatar/name/email header and unrelated section groups. Both hardcoded a white surface. Seller Orders was ambiguous beside personal purchases; the sidebar did not directly expose existing personal booking/order-history pages. No new seller authority or workflow was needed.

The approved direction is compact institutional navigation: one horizontal identity header, clear activity/management/communication/account groups, existing outline Iconsax symbols, Montserrat drawer typography, subtle dividers and the existing navy/gold identity. Existing Poppins/SugarPie elsewhere remain unchanged. The reference's black background is not forced: light uses white and dark inherits the actual theme surface. Mobile gold retains the established `#FCB315` token.

| Before | After | Reason |
| --- | --- | --- |
| Separate regular and seller presentation | Shared CampusHubDrawer with approved-only seller rows | Keep identity and navigation consistent |
| Tall identity, separate program/year lines and email | Actual photo/initials, name and joined academic line | Compact identity without unnecessary personal details |
| Duplicate Home/Marketplace/Services/Facilities rows | Existing bottom navigation remains their primary access | Reduce duplicate paths |
| Seller Orders | Orders Received | Distinguish incoming seller orders from My Purchases |
| Hardcoded light drawer/system icons | Effective theme surface and matching system-bar contrast | Readable light/dark navigation |

### 2. Exact files changed

| Repository-relative file | Current anchor | Purpose |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 21 `SellerDestination`; 44 `CampusHubDrawer`; 76 `_logout`; 191 `build`; 405 `SellerDrawer` | Shared grouped drawer, actual identity, theme/selection/scroll/footer and compatible seller wrapper |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 265 `_openDrawerDestination`; 338 `drawer` | Use the shared drawer for both roles and existing personal destinations |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 166 `_select` | Open personal purchases/bookings from the approved workspace without changing workspace permissions |
| `campushub/test/seller_drawer_test.dart` | Role/size/theme matrix; fallback and logout tests | Identity, hiding seller rows, actual contrast, safe areas, 48dp targets, selected callbacks and confirmation behavior |
| `campushub/test/seller_home_entry_test.dart` | `personal drawer routes and Android Back preserve Home` | Both roles use existing history pages and retain Home/session on Back |
| `campushub/test/seller_workspace_test.dart` | `menu` helper and shared Home navigation assertions | Preserve existing feature coverage through retained Home See All, primary navigation and Back paths |
| `campushub/test/dashboard_search_appbar_test.dart` | Duplicate-primary-route regression | Test preserved bottom navigation rather than removed duplicate drawer entries |
| `docs/mobile-profile.md` | This section | Current behavior, data flow, troubleshooting and verification |
| `CAMPUSHUB_CONTEXT.md` | Latest October 28 entry | Final role-specific sidebar behavior |

Nine files changed; no additional production screen or navigation framework.

### 3. Changes made

Both roles receive **MY ACTIVITY** (My Purchases, My Bookings), **COMMUNICATION** (Messages), **ACCOUNT** (Account Settings), and a separate bottom Logout action. Approved sellers additionally receive **SELLER MANAGEMENT**: My Products, Inventory, Orders Received, My Bundles and **Sales Analytics**. The user explicitly confirmed retaining Sales Analytics because its owner-only units sold, average order value and product rankings are not all exposed on Home.

Dashboard/Home and the redundant primary-catalog shortcuts are removed from the drawer only. Existing bottom navigation and authorized Add Product remain unchanged. The Saved Product Bundles shortcut is removed from the drawer; its existing Home **See All >** action still reaches the same saved suggestions, dismissal and bundle workflows. Recommendations and analytics pages/algorithms are retained. Apply to Sell and My Cart remain accessible in their existing Profile area, reached from the profile header; they were not deleted.

The header uses actual `AuthUser.fullName`, then recorded first/last name or username when needed. Program/year are joined only when present. Email, Student Account and Seller Access labels are absent. A saved photo uses its existing resolved URL; initials remain available when absent/failed. No real person's name, academic details or avatar is hardcoded.

The drawer uses 52dp minimum rows (at least 48dp touch targets), 22dp outline icons, 16dp panel insets, navy-tinted selection and a gold left indicator. Longer/scaled labels grow naturally. The header/content scroll while Logout remains reachable at the bottom; SafeArea protects system insets. Native Drawer retains its standard opening, closing and Android Back behavior. The dark-drawer status-bar icon contrast found in the first native pass was fixed with a drawer-scoped AnnotatedRegion; Home/header styling is not changed.

### 4. Functions, inputs/outputs and data flow

```text
Existing saved authenticated AuthUser + existing seller-status GET
  -> DashboardScreen._loadUserName (unchanged verification)
  -> CampusHubDrawer(user, sellerApproved, selected, onSelected, onProfile)
  -> actual identity + common rows + approved-only management rows
  -> _openDrawerDestination closes drawer and reuses an existing destination
```

`CampusHubDrawer` returns a native Material Drawer. `sellerApproved` comes from the existing verified boolean, not account type, client editing or a new permission. `selected` controls only row presentation. `SellerDrawer` remains a compatibility wrapper inside the existing workspace, which renders it only after `_approved` passes its existing server check. Backend authorization remains authoritative.

`_openDrawerDestination` opens `ProfileOrdersPage` for My Purchases and `FacilityBookingHistoryScreen` for My Bookings, using existing MaterialPageRoute conventions. Messages reuses the existing messages handler. Regular Account Settings opens its existing Profile tab; approved sellers retain their existing Account & Security workspace destination. The profile header still opens full Profile. Other seller tools go through the unchanged `_openSellerTool` approval guard. `SellerDashboardPage._select` similarly opens personal history only after its existing approved check, leaving the underlying selected workspace available on Back.

Example: a student with pending seller status can see My Purchases but cannot see My Products; changing a display label or account-type text cannot grant seller access. A verified seller selecting Orders Received opens the exact existing `SellerDestination.orders` workflow, not a new order API.

`_logout` confirms intent, disconnects the existing ChatService, calls existing `SessionService.clearUser()` and navigates to the existing login route, matching Profile's established logout sequence. Cancel leaves the session intact. The actual unread-message count still comes from ChatService; no new counter or fabricated activity is introduced.

### 5. Backend / API behavior

No Django/API, seller approval, authentication/registration, owner/Program/Major scope, order processing, booking, FIFO, Apriori or report calculations changed. Existing personal-history and workspace requests retain their existing authentication and filtering. Eight protected source fingerprints confirm unchanged main startup, auth/session/seller services, Home, bottom navbar, seller workspace content and Django mobile-seller view. No new dependency.

### 6. Database / migration impact

None. No model, migration, account, seller approval or production record changes. Test users and API responses exist only in isolated Flutter fixtures; native screenshots show the actual signed-in account. No application-data clear, uninstall, login bypass or local-preview startup was introduced.

### 7. Actual verification

- **61 Flutter tests passed** after the final style correction (19s): shared drawer, seller Home/workspace, seller application, center Add Product, shared header/search and navigation surface suites. Existing recommendations, seller actions, ownership/revocation and all primary-tab coverage remain.
- Eight role/size/theme combinations include 375x812, 320x640 at 2x text, 844x390 landscape at 2x text, and 768x1024 at 1.3x. Both seller/non-seller states, missing academic fields, readable metadata contrast (at least 4.5:1), system icon brightness, minimum targets, selected callbacks, scrolling, Logout cancel/confirm and session-preserving Android Back pass.
- **Scoped Flutter analysis: no issues** across all seven runtime/test files (2.6s final); Dart formatting and scoped whitespace checks pass.
- Native **Pixel 10a / Android x64 emulator**: actual dark Home drawer and light workspace drawer screenshots inspected. Verified saved photo/name/academic line, Montserrat/outline icons, white/light and inherited dark surfaces, spacing/dividers, bottom Logout/safe areas, absent duplicate navigation and corrected system-bar contrast. Selecting My Products opened its existing page, retained Add and Back controls, and the reopened drawer reported `selected=true` with the navy tint/gold marker. No native Logout was submitted.
- One native inspection batch found the system-bar issue; one fix batch and final native confirmation completed. No open-ended polish loop. Mechanical layout scan returned no findings before/after, but its limited Dart analysis is not treated as proof of layout.
- Hot reload used Flutter Tools' already-registered `reloadSources` VM service and returned Success, preserving the user's VS Code session without restart. No private service URI was written to evidence. The user subsequently chose to handle hot reload/emulator control personally; no further emulator input/reload was made after that instruction.
- Initial failures were outdated test expectations (removed duplicate menu entries, the former SellerDrawer-only type, and offscreen lazy rows). Tests were updated to the approved navigation paths; coverage was retained rather than removed.

Evidence: ignored `scratch/mobile-sidebar-20261028/` contains before snapshots, design brief, native PNG/XML observations, reload success, test/analysis logs and protected-source checks. This is a native Flutter change: no web URL or browser-based mobile preview is claimed.

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\campushub
flutter test --no-pub test/seller_drawer_test.dart test/seller_home_entry_test.dart test/seller_workspace_test.dart test/dashboard_center_add_button_test.dart test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/system_navigation_surface_test.dart test/seller_application_test.dart
```

### 8. Remaining limits, troubleshooting and safe learning exercise

Native visual evidence is from an emulator and the existing approved seller account, not physical hardware or a native tablet. Non-seller, landscape, tablet-size and large-text breadth are verified by real Flutter widget tests. The existing workspace's ProfileTheme still deliberately uses its white shell; global dark-mode redesign is outside scope. No seller permissions were changed to manufacture a native non-seller screenshot.

If changes appear stale, use your own active session's Flutter Hot Reload action; normal Ctrl+F5 still targets `lib/main.dart` and Pixel 10a. The standalone QA target is not involved. If seller rows are missing, inspect the existing status request and approved boolean; never force the drawer flag to true. If no academic information is recorded, a shorter header is correct. If suggestions are absent from the drawer, use the unchanged Home panel's See All action.

Safe exercise: temporarily change only `_DrawerStyle.rowHeight` from 52 to 56, hot reload and compare vertical rhythm, then restore 52. Keep at least 48dp and verify Logout remains reachable at 320px/large text. Do not change `sellerApproved`, authentication or backend records to practice styling. Verify My Purchases and Orders Received remain distinct, and cancel Logout to confirm the session stays active.



## Restore normal login startup - October 28, 2026

This supersedes the temporary debug-preview switch described below.

1. **Cause / reason:** `main()` unconditionally selected the local preview in debug mode, so normal flutter run / Ctrl+F5 could not reach the real login flow. The user requested removal of this automatic preview.
2. **Exact files changed:** `campushub/lib/main.dart:12` (`main`) removes the preview import, debug constant and early-return branch; `campushub/lib/dev/onboarding_preview.dart:1` and `campushub/tool/qa/onboarding_preview.dart:1` correct now-obsolete comments only; this guide and `CAMPUSHUB_CONTEXT.md`. Five files; one runtime behavior change.
3. **Changes made:** normal Flutter startup now always uses the real CampusHubApp and existing StartupGate. LOCAL PREVIEW no longer appears in an ordinary app launch. The isolated standalone QA target remains available only if explicitly selected. The fixed Pixel 10a Ctrl+F5 launch configuration is retained.
4. **How it works / data flow:** `main()` initializes Flutter, loads the existing cart/theme, launches CampusHubApp and starts the existing optional push service after the first frame. StartupGate resolves the real stored session, then opens Login when signed out or the existing authorized destination when already signed in. Example: a signed-out emulator shows the existing splash followed by Login, not Additional Information with a mock session. No authentication branch or stored session is reset to force an outcome.
5. **Backend / API behavior:** normal existing services resume; there is no new endpoint, login bypass or onboarding change. The preview's mocked HTTP and memory preferences are no longer loaded by main. Existing signed-in accounts retain normal session restoration.
6. **Database / migration impact:** none. No schema, account, booking, payment or saved preference changes. No uninstall or application-data clearing is used.
7. **Tests performed:** all 18 existing login/sign-up routing, standalone QA and food-onboarding tests passed; main.dart analysis was clean (26.7s), and scoped whitespace checks passed. Source comparison confirms main matches its pre-preview implementation except the explicit Future<void> return type. Android x64 debug build succeeded (102.4s), installed normally (3.4s) and launched on Pixel 10a. Actual screenshots show the normal app with no LOCAL PREVIEW banner. A normal Login form was observed through the existing UI; the app can also restore a real saved session to Home. No forced-login route or manual preference deletion was introduced. Existing expired-token/push-registration HTTP 401 and unavailable chat-service messages were observed during restoration; those services were not modified in this startup-only task. A restart/rebuild is required because hot reload alone does not rerun main.
8. **Use / limitations / safe practice:** select **campushub** and press Ctrl+F5 (or the existing emulator configuration when opening only the Flutter folder). For a terminal-owned running app, uppercase R restarts startup; lowercase r only reloads UI. If a real saved session exists, normal startup can restore Home instead of Login; use the existing Logout action to sign out rather than changing authentication or clearing app data. Safe exercise: launch the ordinary main target and verify the preview banner is absent; navigate from Login to Sign Up and back without submitting any account data. The optional QA entry remains separate and does not affect normal startup.


## Ctrl+F5 Android emulator launch correction - October 28, 2026

Historical configuration: the selected-device correction at the top of this guide replaces the fixed emulator setting described here. The normal-login correction above also supersedes this section's preview-startup instructions.

1. **Cause / reason:** Flutter correctly detects the booted Pixel 10a (`emulator-5554`, Android x64), but the VS Code Flutter daemon log records the previously selected wireless Infinix device as disconnected. The root launch configuration depended on that selected device and did not specify a program. This also made the intended app entry ambiguous while `test/food_preferences_test.dart` was active. No emulator app crash was found. The physical-phone forwarding task already skips emulators successfully; it was not the blocker.
2. **Exact files changed:** `.vscode/launch.json:9` (`campushub`) now selects `emulatorId: Pixel_10a`, debug mode, explicit workspace-relative app directory and `lib/main.dart`; the existing profile/release entries also get explicit main paths. `campushub/.vscode/launch.json:5` adds `CampusHub (Android emulator)` for users opening only the Flutter folder; existing phone/debug/release configurations remain. This section and `CAMPUSHUB_CONTEXT.md` document the correction. Four files for this correction; seven distinct runtime/configuration/documentation files across the preceding phone-preview setup and this correction.
3. **Changes made:** Ctrl+F5's configured app target is now independent of the active test editor and a stale physical-device selection. The installed Dart Code 3.144.0 launch schema confirms that `emulatorId` starts the named emulator if stopped and overrides the status-bar/deviceId selection. This reuses the existing Pixel 10a AVD; no emulator, SDK, plugin or dependency was added.
4. **How it works / data flow:** VS Code Run Without Debug reads the selected launch entry, resolves `${workspaceFolder}`, selects/starts the existing Pixel 10a using `emulatorId`, then launches the explicit `lib/main.dart` in Flutter debug mode. The existing root prelaunch task still invokes `connect_android.py`; its current no-phone path returns success without changing emulator networking. The current debug preview switch opens the isolated Additional Information UI. No test file is used as the app entry. This fix changes configuration, not an application function or backend request.
5. **Backend / API behavior:** unchanged. The current onboarding preview remains memory-only/fail-closed. Real Django authentication, booking, marketplace, push and role behavior remain as before; normal app mode remains available through the documented debug switch. No emulator networking/security checks were bypassed.
6. **Database / migration impact:** none. No backend records or schema changes. The existing Android package was updated normally on the emulator without uninstalling or clearing its application data. No phone data was cleared.
7. **Actual verification:** both launch JSON files parse; both emulator entries use the real AVD name, existing main path and debug mode. Installed extension schema supports `emulatorId`. `flutter devices --machine` identifies the booted Android x64 emulator; ADB reports boot complete and `Pixel_10a`. The prelaunch task returns success with no physical phone. Equivalent CLI launch `flutter run --no-pub -d emulator-5554 -t lib/main.dart` built successfully (44.5s), installed (1.816s), launched the actual preview and exposed the VM service. Emulator screenshot visually inspected. Hot reload completed in 590ms; hot restart completed in 3,381ms. Scoped whitespace checks passed. The preceding startup change's 18 Flutter tests and clean scoped analysis remain valid; configuration-only changes did not require rerunning them. No actual Ctrl+F5 keypress is claimed: the Windows computer-use helper failed with `native pipe is unavailable` after the prescribed retry/reset, so GUI automation was stopped. Configuration and equivalent launch were verified directly.
8. **Use / troubleshooting / safe practice:** in the repository-root VS Code window select **campushub** under Run and Debug, then press **Ctrl+F5**. If only the `campushub/` folder is open, choose **CampusHub (Android emulator)**. The emulator configuration deliberately overrides a disconnected phone in the status bar. Keep debug mode for emulator/hot reload; do not select the profile/release entry for this preview. The CLI verification session is detached after checks, leaving the app visible and allowing VS Code to own the next launch. Use VS Code's Flutter Hot Reload action while it owns the session; lowercase r/uppercase R apply to a terminal-owned flutter run session. Safe exercise: keep the test editor open, select the app configuration and run; verify Additional Information opens rather than the test runner. Restart through the existing Flutter action after changing the startup switch. No account is needed for this preview.

Evidence: ignored `scratch/emulator-ctrl-f5-20261028/` contains before-config copies, JSON validation and the actual emulator screenshot. The earlier physical Infinix launch also built/installed successfully, but its UI/hot-reload check was interrupted when the user switched to emulator troubleshooting.


## Phone preview with normal flutter run ? October 28, 2026

This supersedes the earlier requirement to select the standalone Chrome target for visual QA. The actual onboarding components and normal authenticated routes remain unchanged.

1. **Cause / reason:** ordinary `flutter run` launches `lib/main.dart`; the previous visual preview existed only in `tool/qa/onboarding_preview.dart`. Hot reload changes widget code but does not rerun `main()`, so it could not switch an already running normal app into that standalone target.
2. **Exact files / anchors:** `campushub/lib/main.dart:16` (`debugOnboardingPreview`), `:18` (`main`); new `campushub/lib/dev/onboarding_preview.dart:12` (`runOnboardingPreview`), `:35` (`initializeMemoryOnly`), `:58` (`client`), `:127` (`OnboardingPreviewApp`); `campushub/tool/qa/onboarding_preview.dart:7` (compatible optional entry point); this guide and `CAMPUSHUB_CONTEXT.md`. Five files changed. Existing tests still use the compatible tool export.
3. **Changes made:** normal debug startup now opens Additional Information immediately, without signup/login, followed by the existing food preferences and Welcome screens. The local `debugOnboardingPreview = true` switch is explicitly guarded by `kDebugMode`. Setting it to false and hot restarting restores the normal app. Profile/release startup always retains the normal application branch. The preview implementation moved into `lib/dev/` so the normal entry can reuse it; the old tool file delegates and re-exports it rather than duplicating UI or mock behavior.
4. **How it works / functions and data flow:** `main()` checks the debug-only switch **before** loading real cart/theme or starting push registration. `runOnboardingPreview()` initializes the Flutter binding and `runApp` inside the same `http.runWithClient` zone. `initializeMemoryOnly()` replaces only the current Dart isolate's preference store with an in-memory preview, not the phone's persisted session. The same real onboarding screens call the same service methods, while `client()` answers their known requests locally and denies unexpected requests. The persistent LOCAL PREVIEW banner remains. Example: preview Finish updates only the temporary user map, then opens Personalize; no Django profile is saved. Restarting with the switch false creates a fresh normal isolate and uses the device's real store again.
5. **Backend / API behavior:** no Django changes, real login/signup, new credentials, permission bypass or real marketplace navigation. The existing preview fails closed on unexpected HTTP endpoints. This validates UI, not real authentication or saved backend preferences. Normal production services/screens/routes are unchanged, confirmed by seven protected source fingerprints.
6. **Database / migration impact:** none. No working records, backend categories, real stored sessions or schema are modified by the preview. The debug install uses the existing package/update path; it does not clear application data.
7. **Tests performed:** 18 existing onboarding/food-preference/widget tests passed, including normal login/signup navigation, in-memory preview completion, blocked unexpected requests, selection/skip/back, validation/keyboard and 320px/large text. Scoped Flutter analysis of main, moved preview, tool entry and preview tests: no issues. Dart formatting made no additional changes. Native verification is now complete: default main built/installed/launched on the connected Infinix; after the user switched to Pixel 10a, the same entry launched there and hot reload (590ms) and hot restart (3,381ms) passed. Actual emulator screenshot inspected; see the newer Ctrl+F5 correction above.
8. **How to use / limitations / safe practice:** from `campushub/`, run `flutter run` and select the connected phone if Flutter offers multiple devices. If an earlier normal-app run is already active, press uppercase **R** once to hot restart into the new entry point. Then edit the existing `profile_setup_screen.dart` or `food_preferences_screen.dart` and press lowercase **r** for hot reload. Screen state is normally preserved. To return to actual login/Home, set `debugOnboardingPreview` to false and press **R**. Do not remove the `kDebugMode` guard. Preview selections/contact values disappear on restart. Use test-only form input; nothing is sent to Django. Safe exercise: change a label temporarily in the actual profile-setup widget, press r, confirm it changes on the phone without account creation, then restore it and reload.

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\campushub
flutter run
# r = hot reload UI edits; R = hot restart after changing the startup switch
```

Evidence: ignored `scratch/phone-onboarding-preview-20261028/`. The standalone target remains available for earlier QA scripts, but is no longer required for ordinary debug phone preview.


## Compact horizontal food cards and centered Personalize header — October 27, 2026

1. **Cause / reason:** category cards used vertical icon/name stacks with a 112px minimum and uniformly navy icons. The long onboarding/editor title also did not match the user's requested centered Personalize heading.
2. **Exact files changed:** `campushub/lib/module_app/screens/food_preferences_screen.dart:38` (`_FoodStyle.emoji`), `:155` (`centerTitle`), `:167` (`Personalize`) and `_card`/48px minimum; `campushub/test/food_preferences_test.dart` (title expectations and compact row/center/large-text assertions); `campushub/test/onboarding_preview_test.dart` (same header expectation); this guide and `CAMPUSHUB_CONTEXT.md`. No profile-information heading, Profile menu label or other production screen was renamed.
3. **Changes made:** shared food onboarding/editor header is centered and reads Personalize. Each selectable card now has a natural-color food emoji beside the name, with compact padding and content-driven height. A 48px minimum retains a usable hit area, replacing the 112px minimum. The two-column layout, navy selected border and gold checkmark remain. The checkmark slot stays reserved so selection does not shift the label. Text wraps when necessary at narrow widths/large accessibility sizes; emoji artwork is not enlarged with text scaling.
4. **How it works / functions and data flow:** `_FoodStyle.emoji(id)` maps only the six existing canonical IDs to rice, popcorn, cake, drink, bento and egg emojis. `_card(category)` renders the emoji and an expanded name in a Row; the name determines extra height when needed. Emoji semantics are excluded so the named selectable control remains the relevant interaction. Existing `_selected`, `_save`, service requests and stage routing are unchanged. Example: selecting Rice Meals changes its existing selected state/checkmark; the saved ID is still Rice Meals, never the emoji.
5. **Backend / API:** unchanged. No new taxonomy, preferences rules, role permissions, routes, Apriori inputs, counters or required selections. All six selections, empty Continue, Skip, Profile editing and Welcome still use the existing service. The local preview still intercepts all backend requests.
6. **Database / migrations:** none for this refinement. No working records or account/session data were changed.
7. **Actual verification:** all 15 food-onboarding/isolated-preview tests passed. Added assertions check horizontal emoji/name alignment, compact normal-text sizing and centered header while retaining 320px/200%-text coverage. Scoped Flutter analysis reports No issues found. A fresh standalone web build was exercised through real Additional Information -> food preferences and visually reviewed at 390x844 and 844x390; a 320x640 screenshot was also captured. No browser JavaScript errors or backend requests occurred. The Android debug APK was also rebuilt successfully without installation. The earlier debug server did not reload reliably; the preview now serves the compiled QA bundle on loopback port 8087. A Windows relative-output shader build failed; using an absolute output path produced the verified successful web build. Logs/evidence are retained in ignored `scratch/compact-food-preferences-20261027/`.
8. **Limits / safe practice:** emoji appearance follows platform fonts. At narrow widths or large text, long category names may wrap rather than being truncated. The real Additional Information/Edit Profile headings remain appropriate to their own forms; only the food step's header changed. Refresh `http://127.0.0.1:8087/?v=compact` for the updated isolated preview; choose a preview Guest, enter a test-only contact and continue to the food cards. Select/deselect all six and rotate/resize, then compare their saved text identifiers in the existing tests. No signup or real records are needed. Native device installation was not performed.

The current compiled preview can be served again from the workspace root with:

```powershell
backend/core/venv/Scripts/python.exe -B -m http.server 8087 --bind 127.0.0.1 --directory C:/Users/leste/Desktop/CAMPUSHUB/scratch/compact-food-preferences-20261027/web
```

## Preview Additional Information without signup/login — October 27, 2026

1. **Cause / reason:** the real onboarding correctly requires authentication, but the user needs to inspect its UI without creating or signing into an account. Keep that production requirement intact and use an isolated visual target.
2. **Exact files:** new `campushub/tool/qa/onboarding_preview.dart:12` (`main`), `:35` (`initializeMemoryOnly`), `:58` (`client`) and `:127` (`OnboardingPreviewApp`); new `campushub/test/onboarding_preview_test.dart`; this guide and `CAMPUSHUB_CONTEXT.md`. No production `lib/` or Django files changed.
3. **Changes made:** a separate target opens the real `ProfileSetupScreen` directly, then the real food-preference and Welcome screens. A persistent LOCAL PREVIEW banner identifies fixtures. The final page is Preview complete with a restart action, not the real marketplace. Program/major identities are negative preview-only values; no real academic or account records are created.
4. **How it works / functions and data flow:** `main()` installs a local `http.runWithClient` zone and initializes the Flutter binding in that same zone. `initializeMemoryOnly()` redirects SharedPreferences to its in-memory mock store before seeding a non-authentic preview token/user. It never loads or overwrites the device's real store. The production screens and their existing validation/navigation run normally; their academic/profile/preference HTTP requests are answered by `client()` from memory. Unexpected endpoints/methods return 403 with no network passthrough. Example: tapping Finish changes the preview map's profile flag, then the existing destination helper opens Food Preferences; Django is never called. FCM startup from the real `main.dart` is not used.
5. **Backend / API:** no real signup, login or backend requests. No real JWT is issued and authentication rules/routes remain unchanged. The target is never imported by the production app. It is a UI demonstration, not an authorization/payment/stock test.
6. **Database / migrations:** none. Preview state disappears on restart; no working data, real sessions or schema are changed.
7. **Actual verification:** 15 preview/onboarding widget/service tests passed; scoped analysis of the two new files reports no issues. Actual compiled Flutter Web opened Additional Information at 390px without a login screen, with zero backend requests or browser JavaScript errors; screenshot inspected. Nineteen existing onboarding implementation/test files matched the prior feature's fingerprints. No physical-device installation was performed.
8. **How to use / limitations / safe practice:** from `campushub/`, run `flutter run -d chrome -t tool/qa/onboarding_preview.dart` for a browser, or select an emulator/device with that same target. The loopback Web Server preview is available while its process runs at `http://127.0.0.1:8087`. To restart that server use the command below. Use a clearly fictitious ID such as PREVIEW12345 and test-only contact input. Inspect Student/Faculty/Guest, Back, validation, food selection/Skip and Welcome. Nothing from this target demonstrates an actual registered user, saved preference or authorized transaction. Running ordinary `flutter run` still opens the normal authenticated app.

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\campushub
flutter run -d web-server --web-hostname 127.0.0.1 --web-port 8087 -t tool/qa/onboarding_preview.dart
```

Evidence: ignored `scratch/onboarding-preview-20261027/`. Safe exercise verification: reach Preview complete and restart, then confirm no signup/login request is recorded by the mock and the previous preferences-store fixture remains unchanged in `onboarding_preview_test.dart`.

## Personalized food onboarding — October 27, 2026

### 1. Cause / reason

Inspection found no persisted food preferences or preferences endpoint. First profile completion navigated directly to Home. Product categories are text identifiers, not rows in a numeric Category model; the six food identifiers already exist in `modules/marketplace/services/customization.py::FOOD_CATEGORIES`. Additional Information used viewport-height panels, `Spacer`s and a 560px student minimum, causing blank gaps and cramped keyboard layouts. Forms did not revalidate corrected input automatically.

The implemented flow is **Signup -> First Login -> Additional Information -> Food Preferences -> Welcome -> Home**. Existing completed accounts retain their existing Home destination and can opt in through Profile -> Preferences. No historical users are marked as new and no category/product records are manufactured.

### 2. Exact files changed / current anchors

| File | Anchor | Purpose |
|---|---|---|
| `backend/core/api/models.py:74` | `MobileFoodPreference` | One optional per-user sidecar with canonical category IDs, onboarding stage and update time. |
| `backend/core/api/migrations/0049_mobile_food_preferences.py:7` | `Migration` | Add only `campushub_food_preference`; no user/product backfill. |
| `backend/core/api/food_preferences.py:16` | `preference_data`; line 24 `mobile_food_preferences` | Private read/save/skip/finish API, validation, owner locking and legacy fallbacks. |
| `backend/core/api/views.py:134` | `serialize_campushub_user`; line 680 locked `previous` | Return optional metadata; first successful required-profile completion starts preferences exactly once. |
| `backend/core/core/urls.py:196` | `mobile_food_preferences` | Existing mobile profile namespace, `/api/mobile/profile/preferences/`. |
| `backend/core/api/test_food_preferences.py` | `FoodPreferenceTests` | Real PostgreSQL tests of owner scope, inputs, completion, login, skip, editing and account cleanup. |
| `campushub/lib/module_app/services/auth_service.dart:28` | `AuthUser.onboardingStage`, `preferredCategoryIds`, `fromJson` | Parse optional metadata; missing legacy stage defaults to complete. |
| `campushub/lib/module_app/session/session_service.dart:35` | `_encodeUser` | Persist those values with the existing signed-in account cache. |
| `campushub/lib/module_app/services/food_preferences_service.dart:23` | `FoodPreferencesService` | Reuse existing API configuration/bearer session; load/save/skip/finish, reject changed/mismatched sessions, update cached user. |
| `campushub/lib/module_app/routes/app_routes.dart:16` | `forUser` | Shared required-profile/preferences/welcome/Home destination calculation. |
| `campushub/lib/module_app/routes/app_router.dart` | `AppRoutes.foodPreferences`, `AppRoutes.welcome` | Wire the two screens into existing routing. |
| `campushub/lib/module_app/screens/login_screen.dart` | `_handleLogin`, `AppRoutes.forUser` | Use the saved server stage after login. |
| `campushub/lib/module_app/screens/startup_gate.dart` | `_resolveDestination` | Resume the cached stage after app restart. |
| `campushub/lib/main.dart` | `_scheduleNotificationOpen` blocked-route list | Hold notification navigation during the two initial onboarding routes. |
| `campushub/lib/module_app/screens/profile_setup_screen.dart:59` | `_clearError`; line 198 finish routing; `Align`/forms | Intrinsic scrollable panels, editing remains a pop, live validation clearing, responsive app bar. |
| `campushub/lib/module_app/screens/food_preferences_screen.dart:48` | `FoodPreferencesScreen`; `CampusWelcomeScreen`; `_FoodStyle` | Shared onboarding/Profile editor, actual six API choices, multi-selection, skip, accessible selection state, variable-font weights and resumable Welcome. |
| `campushub/lib/module_app/screens/profile_page.dart:410` | Preferences row | Open the shared editor; reload the existing Profile afterward. |
| `campushub/lib/module_app/screens/home_page.dart:218` | `preferredCategories`, `onCategory` | Render saved shortcuts without replacing the existing catalogs. |
| `campushub/lib/module_app/screens/dashboard_screen.dart:444` | Home callbacks; `_MarketplacePage.didUpdateWidget` | Select a preferred category in the existing Marketplace tab; all category choices and recommendations remain. |
| `campushub/test/food_preferences_test.dart` | routing/service/widget tests and isolated render | First login, all six, no required choice, skip, editor, back, Welcome, session isolation, keyboard, small/large text, actual font/icon render. |
| `campushub/test/home_page_test.dart` | saved food shortcuts test | Verify the canonical shortcut ID and preserved catalog navigation. |
| `docs/mobile-profile.md`, `docs/mobile-typography.md`, `CAMPUSHUB_CONTEXT.md` | newest sections | Feature behavior, approved typography scope, verification and practice. |

There are **24 source/test/documentation files**, including the one new migration. Existing source/manifests outside this scope were not staged or reset. Generated APK/build/evidence files are separate.

### 3. Changes made

The white Montserrat screen uses two responsive columns for Rice Meals, Snacks, Desserts, Beverages, Combo Meals and Breakfast. Cards have relevant existing Material icons, navy selected outlines, gold checkmarks on navy, subtle selected fill, semantic selected state and 160ms feedback that respects reduced motion. All six may be selected; there is no counter, maximum-five rule or required minimum. Continue accepts an empty selection; Skip for Now discards unsaved local choices and preserves any previously saved preferences. Profile editing reuses the same screen with Save Preferences and no onboarding skip control.

Welcome uses the requested message and Get Started action. It checks saved state on entry, resumes correctly, and marks completion only after the backend acknowledges Get Started. Back opens the shared editor. Back from the preference onboarding step opens the existing profile editor without dropping pending choices or clearing the session. If loading fails, Back can use the current cached owner rather than becoming inactive.

Additional Information panels now size to their content, scroll inside the keyboard-reduced viewport and revalidate after input changes. Required account type, student/faculty IDs, program/major restrictions and contact validation remain. Optional Year / Section and the existing Profile-edit return behavior remain.

### 4. How it works / functions, inputs, outputs and data flow

`MobileFoodPreference` is a one-to-one record keyed to the real mobile account. Missing records mean **complete** for legacy finished profiles. `mobile_complete_profile()` locks the real owner; only a false -> true profile-completion transition creates the preference stage. Re-editing a completed profile does not restart onboarding or erase food choices.

`preference_data(user)` reads that user's record. The existing user serializer includes `preferred_category_ids` and `onboarding_stage` in login/profile responses. `AuthUser.fromJson` and `SessionService` retain them. `AppRoutes.forUser(user)` always checks required profile completion before choosing the saved optional stage.

```text
Existing authenticated mobile user
 -> required profile save -> stage preferences
 -> existing canonical food IDs from authenticated GET
 -> Continue/save or Skip -> stage welcome
 -> Get Started/finish -> stage complete -> existing Home
 -> saved Home shortcut -> existing Marketplace category filter
```

Example authorized save body:

```json
{"action":"save","category_ids":["Rice Meals","Beverages"]}
```

These are actual existing text identifiers, not invented numeric database IDs. The server normalizes duplicates/order and stores only those identifiers. A later Profile save changes the identifiers without replaying Welcome. The UI service checks the response owner and current session before caching the returned user. Purchase baskets, Apriori inputs and recommendation algorithms never consume these preferences.

### 5. Backend / API behavior and security

`GET /api/mobile/profile/preferences/` returns six verified taxonomy choices plus the authenticated user's existing serialized profile/stage. GET never creates a preference record. POST accepts only `action` and `category_ids`: `save`, `skip`, or `finish`. Unknown categories/types, forged owner fields and malformed requests are rejected. Anonymous/expired/wrong-source tokens cannot use cookie authentication as a substitute; inactive/suspended accounts remain denied through the existing bearer helper. An unfinished required profile receives 409.

Save/skip/finish serialize on the existing owner row, preserve distinct account types/permissions, and never trust a posted account ID. Finish cannot jump directly past the preferences decision. Repeated finish is safe. Normal ORM account deletion cleans up its own optional sidecar. No changes were made to orders, payments, FIFO, seller approval, purchases, Apriori or registration permissions.

### 6. Database / migration impact

Migration **0049_mobile_food_preferences** was tested in disposable PostgreSQL and applied to the **local development database only** after verifying the plan contained exactly this one additive migration. It adds the sidecar table and standard Django model metadata; it does not add fields to or backfill `campushub_user` and does not initialize preferences for existing users. Source changes require this migration before deployment; no production activation occurred.

Read-only working-database verification returned 200 for a legacy completed owner, six taxonomy identifiers and complete stage without inserting a row. The preference table remained empty. Before/after fingerprints of the six stored users and fifteen products match. Migration SQL and fingerprint evidence are in ignored `scratch/personalized-onboarding-20261027/`; no private row contents are exported in those reports.

### 7. Actual verification

- **23 targeted Django tests passed**: preferences, profile photos and existing account-field validation. Includes first required-profile completion, all six choices, empty/duplicate/invalid input, owner isolation, login resumption, legacy users, editing, skip, finish and isolated account cleanup.
- **402 broader Django regressions passed in 152.606 seconds** across API, accounts, user management and bundle workflows. Three additional preference tests added afterward passed in the final targeted run; counts overlap and are not summed.
- **60 Flutter regression tests passed** across onboarding, academic setup, login/signup spacing, Profile, Home and seller Home entry. The new onboarding file contains 13 tests, including actual first-login profile-save routing, skip, all six, back/edit, Welcome, session checks, keyboard validation, 320px width and 200% text.
- Scoped Flutter analysis reports **No issues found**. Node/HTML design-kit gates are not measurements of native Flutter controls; no full WCAG/device certification is claimed.
- Actual widget render loaded bundled Montserrat and Material icons, then rendered selected cards at 390px; the resulting PNG was inspected. The font's variable `wght` axis defaults to 100, so this new flow explicitly maps body/labels/headings to 400/600/700. See the typography guide.
- Android **debug APK built successfully**. Django system checks and `makemigrations --check --dry-run` are clean. The APK was not installed on a device.
- Initial verification exposed stale test-path names, missing legacy unmanaged test tables and a render-harness asynchronous capture issue. These were corrected in isolated test setup/harnesses. Application fixes include live validation, intrinsic panels, explicit variable-font weights and responsive title height. Earlier failing logs remain alongside final results.

### 8. Remaining limitations, troubleshooting and safe practice

Saving, skipping and completing Welcome require a backend connection so that success is never falsely reported without persistence. Retry retains pending selections. Category IDs are existing text identifiers because the current marketplace has no separate numeric category model. Home reads the existing per-account cache, refreshed by login/Profile/preference saves; no cross-device live preference subscription is introduced. No physical-device/iOS installation or production deployment was performed. Existing finished users intentionally do not replay onboarding; use Profile -> Preferences.

If the screen does not appear on an installed app, use the updated build and confirm migration 0049 is applied to its backend. A completed returning user's absence from onboarding is expected. An authorized fresh account must still finish all required Additional Information first. Do not reset real users' profile flags to demonstrate it.

Safe practice exercise: run `flutter test test/food_preferences_test.dart test/home_page_test.dart` from `campushub/`. Select all six in the isolated fixture, continue to Welcome, go back to edit, then Get Started. Compare Skip and the completed-user case. Inspect the backend test's save/skip/finish payloads and verify the same canonical IDs reach the existing Marketplace filter. Use disposable test databases and mock sessions, never real account deletion or fake live product records.

## Remove mobile email verification UI - October 27, 2026

## Remove mobile email verification UI - October 27, 2026

**Android build follow-through:** `flutter build apk --debug` succeeded, producing `campushub/build/app/outputs/flutter-apk/app-debug.apk` (189,869,562 bytes), SHA-256 `59c8a2197828860592f1b25314a85fa12ea27f10ce58aba1912b462a4c4d6984`. This is the existing default local-development configuration, not a rebuilt public-server release. No device installation, launch, live login, password reset or server deployment was performed. The earlier no-build statements below describe the initial verification stage and are superseded by this successful build. Scoped tracked-file `git diff --check` also passed. Keep the pre-existing Git lock and unrelated user changes intact.

**Scope correction after checking weak points:** The initial implementation interpreted the short request as only the Account & Security control. Re-reading "remove verify email in mobile" and tracing every `verificationToken:` caller revealed two automatic prompts as well. The implemented interpretation is now removal of standalone mobile email-verification experiences throughout login, initial profile completion, and security settings. Password-recovery email-code verification is deliberately retained as an identity check, not treated as permission to weaken backend security. This distinction is an interpretation of the short request, not additional user wording.

**Additional exact changes and data flow:** `campushub/lib/module_app/screens/login_screen.dart:68` (`_handleLogin`, navigation after `SessionService.saveUser`) no longer opens a blocking verification dialog after successful login. Existing `profileCompleted` routing still selects dashboard or profile setup. `campushub/lib/module_app/screens/profile_setup_screen.dart:186` (`_submit`, following `SessionService.updateUser`) no longer opens verification after initial profile completion and proceeds to the existing dashboard route. Editing still returns the updated user to its caller. Removed that file's unused recovery-dialog import. These are presentation/navigation changes only, with unchanged API requests and persisted verification flags.

**Final verification:** All 31 tests passed across `profile_page_test.dart`, `recovery_code_input_test.dart`, `login_layout_test.dart`, and `profile_academic_test.dart`. Analysis of the three changed production Dart files plus `profile_page_test.dart` reported no issues. Formatting of login/setup reported no changes. Source tracing confirmed no production screen now supplies `verificationToken:` to `AccountRecoveryDialog`. The reusable dialog's unused standalone mode and its isolated test remain for compatibility, but no mobile screen enters it. Login layout and academic form tests are not end-to-end successful unverified-login/onboarding network tests, so those paths are verified by source inspection and analysis rather than a physical-device or live-account claim. No backend, database, build, installation or deployment changes were added.

1. **Cause / reason:** The user requested removing Verify Email in mobile. Account & Security exposed a separate verification action and verified/unverified status. This update removes that presentation, not password-recovery identity checks.
2. **Exact files changed:** `campushub/lib/module_app/screens/profile_details_pages.dart:124` (`_recover`) and `:137` (`build`), `campushub/test/profile_page_test.dart:67` (verified/unverified regression loop) and `:338` (existing security assertion), and this guide. Earlier verification-row guidance is superseded.
3. **Changes made:** Removed the Verify Email Address row, Email verified / Email not verified text, and the unused verification-token branch of `_recover`. Kept the actual email and Reset Password row. Tests cover both saved verification states and the existing recovery dialog.
4. **How it works:** `AccountSecurityPage` receives an `AuthUser`. `build` displays its email without reading `emailVerified` for presentation. `_recover()` takes no arguments and returns `Future<void>`: it opens `AccountRecoveryDialog(initialEmail: _user.email)` without a verification token, then reloads the saved user through `SessionService.loadUser()` and updates mounted state. Example: tapping Reset Password for `ana@example.test` supplies that saved address to the existing recovery dialog, not to a standalone verification flow. Reusing recovery avoids duplicating authentication logic.
5. **Backend / API behavior:** No backend or API changes. Existing password recovery, its email-code verification, and the shared dialog's verification capability remain intact. This does not automatically verify users or disable server security checks.
6. **Database / migration impact:** None. No saved verification flags or account records changed.
7. **Tests performed:** `flutter test test/profile_page_test.dart test/recovery_code_input_test.dart` passed all 20 tests. The new two-state tests confirm the email remains, verification controls/status are absent, and Reset Password opens recovery with a null verification token. `flutter analyze lib/module_app/screens/profile_details_pages.dart test/profile_page_test.dart` reported no issues. Dart formatting ran. The first test run found an obsolete existing Email verified assertion, which was updated before the successful rerun.
8. **Remaining limitations:** No APK build, installation, physical-device verification, deployment or real password reset was performed. An installed release needs an updated build to show source changes. Existing Git index.lock prevents safe ordinary staging/commit, so it was left untouched along with pre-existing work.

**Troubleshooting:** If Verify Email Address still appears, confirm the running app uses this source/build. Email-code checks inside Reset Password are intentionally retained and are not the removed standalone action.

**Safe practice exercise:** Inspect the new test loop at `profile_page_test.dart:67`. It varies only the fixture's `email_verified` boolean and checks the same visible behavior. Run the two test files above from `campushub/` to verify both states without changing a real user or sending a recovery email.

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
