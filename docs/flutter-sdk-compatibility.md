# Flutter SDK compatibility

## Deprecated widget APIs - November 11, 2026

### 1. Cause / reason

The installed SDK is Flutter 3.47.9 with Dart 3.13.7. It deprecates the two numeric `cacheExtent` usages, `SizeTransition.axisAlignment`, and `TickerMode.of`. Inspection found exactly these four usages in the application library. They are framework API migrations; the warnings do not indicate a Django, database or network failure.

The replacements were checked against the installed framework sources and the official [scroll-cache API](https://api.flutter.dev/flutter/widgets/ScrollView/scrollCacheExtent.html), [SizeTransition implementation](https://api.flutter.dev/flutter/widgets/SizeTransition/build.html), and [TickerMode.valuesOf API](https://api.flutter.dev/flutter/widgets/TickerMode/valuesOf.html).

### 2. Exact files changed / current lines and anchors

| File relative to repository root | Current line / nearby code | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facility_screen.dart` | 2, rendering import; 73, `ListView` in `_FacilitiesPageState.build` | Import only `ScrollCacheExtent` and replace the numeric cache argument with `scrollCacheExtent: const ScrollCacheExtent.pixels(700)`. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 3, rendering import; 866, catalog `ListView` | Make the identical typed cache replacement, retaining the existing 700 logical pixels. |
| `campushub/lib/module_app/screens/signup_screen.dart` | 525, `SizeTransition` inside `_PasswordChecklist.build` | Replace `axisAlignment: -1` with `alignment: AlignmentDirectional.topStart`. |
| `campushub/lib/module_app/widgets/home/campus_home_banners.dart` | 113, `_schedule` pause guard | Replace `!TickerMode.of(context)` with `!TickerMode.valuesOf(context).enabled`. |
| `docs/flutter-sdk-compatibility.md`, `CAMPUSHUB_CONTEXT.md` | Current compatibility report/reference | Record the API mapping, behavior, actual verification, known unrelated failures and safe practice. |

### 3. Changes made

The two lists keep their existing cache distance, padding, scroll physics, data and refresh behavior. The signup checklist keeps its duration, fade and top/start expansion. Home banners still respect the enabled ticker setting along with the existing lifecycle, route, active-tab, user-pause and reduced-motion guards. No visual redesign, timing adjustment, dependency upgrade or new business rule was introduced.

### 4. How it works / functions, inputs, outputs and data flow

`_FacilitiesPageState.build(context)` builds the existing `RefreshIndicator` and `ListView`. `_fetchFacilities()` still calls the injected `loadFacilities` function, maps successful records through `FacilityItem.fromJson`, and updates the existing loading/error/data states. The catalog build method in `dashboard_screen.dart` still receives the same loaded products and recommendation state. The new cache argument affects only Flutter's off-screen layout distance; it does not fetch additional API records. The installed framework itself converts the old numeric argument to `ScrollCacheExtent.pixels`, making this an equivalent explicit representation.

`_PasswordChecklist.build(context)` listens to the existing text controller through `ValueListenableBuilder`. It passes the existing animation to `SizeTransition` and `FadeTransition` when switching between the hidden and visible checklist. The default axis is vertical. The old `axisAlignment: -1` resolves in the SDK to `AlignmentDirectional(-1, -1)`, so `AlignmentDirectional.topStart` preserves both the top edge and reading-direction-aware start edge. Using a centered cross-axis alignment would not be the exact mapping.

`_CampusHomeBannersState._schedule()` cancels any previous timer and checks the existing pause conditions. `TickerMode.valuesOf(context)` supplies `TickerModeData`, containing both `enabled` and `forceFrames`. Reading `.enabled` preserves the old Boolean guard and inherited dependency. This timer does not use `forceFrames`; it must not use that field to bypass a disabled ticker mode or request forced rendering. The five-second rotation timer and navigation callbacks remain unchanged.

Annotated example:

```dart
// Same 700-logical-pixel off-screen layout distance; explicit typed API.
scrollCacheExtent: const ScrollCacheExtent.pixels(700),

// Exact mapping of vertical axisAlignment: -1, including RTL start alignment.
alignment: AlignmentDirectional.topStart,

// Preserve the original enabled/disabled pause decision.
!TickerMode.valuesOf(context).enabled
```

### 5. Backend / API behavior

Unchanged. No Django/FastAPI source, HTTP method, API parameter, permission, booking workflow, product calculation, signup validation or saved-session behavior changed. The added import exposes a Flutter rendering type; it adds no dependency.

### 6. Database / migration impact

None. No models, migrations, working records, account settings, SDK installation, dependency declarations or lockfiles were modified by this fix.

### 7. Tests performed

- `dart format --output=none --set-exit-if-changed` on the four changed Dart files: **4 files checked, 0 formatting changes**.
- `flutter analyze --no-pub` on the four changed files: **No issues found**, in 28.7 seconds. A library search found no remaining `cacheExtent`, `axisAlignment` or `TickerMode.of` usages.
- `flutter test --no-pub test/campus_home_banners_test.dart test/signup_spacing_test.dart test/resource_catalog_cards_test.dart`: **22 passed, 2 failed**. Banner rotation, lifecycle/pause/manual navigation/reduced-motion and facility/card tests passed. Both failures are the signup spacing assertions at `signup_spacing_test.dart:25`, for light and dark themes: expected vertical padding 14px, received 16px.
- Reproduced both spacing failures using an isolated copy of the signup screen with the original `axisAlignment: -1` restored. Only local import paths were rewritten so the baseline copy could run from `scratch/flutter-deprecations-20261111/`; production code and the existing test were not reverted or changed. The same expected/actual padding mismatch proves these failures are not introduced by the API replacement. The underlying spacing discrepancy was not investigated or changed.
- No permanent tests were added for these direct replacements. A native app build, physical-device UI review and the full application analyzer/test suite were not run. Do not interpret the targeted clean analysis as a claim about the full app.

### 8. Remaining limitations / troubleshooting / safe practice

The two existing signup spacing tests remain failing, as documented above. The replacement APIs require a compatible Flutter SDK; older SDK versions were not tested, and no minimum-version constraint was changed. If an IDE still shows the old warnings, confirm it uses `C:\flutter` and the same SDK as `flutter --version`, then restart its Dart analysis server. Do not suppress deprecation diagnostics or upgrade unrelated dependencies to conceal them.

Safe practice exercise: open the facility list's cache argument and trace `ScrollCacheExtent.pixels(700)` into the installed SDK's `ScrollView.buildViewport` conversion. Compare it with the former numeric argument without changing production values. Run the four-file analyzer command, then the banner/card tests separately. Confirm that the typed cache retains the same logical-pixel unit and the ticker pause guard still reads `.enabled`. Use a disposable test copy for alignment experiments; do not change real facilities, users or signup rules.
