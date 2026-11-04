# Mobile typography: shared Inter UI styles

## App-wide Inter and Add Product roles - November 3, 2026

### 1. Cause / reason

The app previously used Inter mainly for Home/navigation, while the root theme and explicit screen overrides selected Poppins, Montserrat or a Roboto currency glyph. The latest instruction standardizes ordinary mobile UI on Inter and supersedes the older scoped font decisions recorded below. Inter is already bundled and registered, so no font download or new package is needed. SugarPie remains only for the CampusHub wordmark, a deliberate branding exception.

### 2. Exact files changed and current anchors

All paths below are relative to `campushub/` unless marked otherwise. These are existing files; no duplicate typography system or new application file was created.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `lib/module_app/theme/app_typography.dart` | 51 `AppTypography`; 54–107 named roles; 128 `textTheme`; 145 `theme` | One Inter family and shared role styles; existing InterTypography family now aliases the same source. |
| `lib/main.dart` | 111 light theme; 118 dark theme | Applies the shared typography to both existing color schemes. |
| `lib/module_app/screens/seller_add_product_page.dart` | 294 category input/menu; 479 progress; 491 review labels; 607 button style; 626 decoration; 679 section title; 873 scoped theme; 910 header; 1125 threshold help | Applies consistent styles to all four existing steps and adds threshold help through the existing widget. |
| `lib/module_app/widgets/seller/product_inventory_fields.dart` | 61 field label; 86 configurable ProductInventoryInfo; 97–102 explanations; 173 icon key; 198 selector build; 433 date text | Shared label/input/card/description/tooltip styles, both stock help icons and reusable threshold explanation. |
| `lib/module_app/widgets/seller/product_expiry_field.dart` | 149 value style; `_ExpiryHelpState` tooltip textStyle | Uses shared 16sp input and 13sp tooltip styles. |
| `lib/module_app/widgets/seller/product_tag_input.dart` | 144 chip label; TextFormField `style`; ProductTagsHelp `textStyle` | Shared chip/helper, input, placeholder and tooltip styles. |
| `lib/module_app/widgets/profile/profile_widgets.dart` | 14 text; 25 identityText; ProfileTheme `data` | Profile/identity now use Inter; the scoped theme reuses AppTypography.theme. |
| `lib/module_app/screens/components/auth_form_shell.dart` | 19 family; primaryButton; AuthFormField `style`/label/hint/error | Inter with shared 16sp input, 14sp medium label, placeholder/error and semibold button roles. |
| `lib/module_app/screens/components/account_recovery_dialog.dart` | 183 theme | Applies the same roles to the existing light recovery dialog. |
| `lib/module_app/screens/food_preferences_screen.dart` | 15 theme | Reuses global roles and the existing Inter family. |
| `lib/module_app/screens/facility_details_screen.dart` | 97 scoped font; 515 text style | Replaces the explicit Montserrat overrides with the central family. |
| `lib/module_app/widgets/facilities/booking_widgets.dart` | 39 currency; 49 amount; existing scoped theme and text styles | Inter for booking text and peso amounts, preserving existing colors and geometry. |
| `lib/module_app/screens/product_details_screen.dart` | 1061 peso style | Uses Inter for the currency symbol; other product text already uses AppTypography. |
| `lib/module_app/widgets/order_summary_widgets.dart` | 19 text; 30 `_font` | Existing CheckoutTypography interface retains its purpose-specific styles while using the shared family. |
| `lib/module_app/screens/seller_application_page.dart` | 142 `_textTheme`; 193 primary theme | Removes its explicit Poppins override. |
| `lib/module_app/screens/seller_dashboard_page.dart` | 377 text style | Uses the shared family for its explicit text override. |
| `lib/module_app/screens/seller_workspace_content.dart` | 404 text; 576,580,639 explicit styles | Uses Inter instead of Poppins in the existing workspace styles. |
| `lib/module_app/screens/splash_screen.dart` | 118 status text | Uses the central family. |
| `lib/module_app/widgets/navigation/floating_bottom_navbar.dart` | 212 and 369 label styles | Existing Inter labels now reference the central constant. |
| `lib/module_app/widgets/home/home_preview_cards.dart` | 283 font fallback | Removes the Montserrat fallback in favor of the central family. |
| `lib/module_app/widgets/facilities/resource_catalog_card.dart` | 110 font fallback | Uses the same family fallback as other cards. |
| `lib/dev/onboarding_preview.dart` | 135 theme | Existing development preview follows production's shared font roles. |
| `docs/mobile-typography.md`, `docs/mobile-seller-application.md`, `CAMPUSHUB_CONTEXT.md` | Current entry | Records the new global decision, exact changes, data flow and verification limits. |

### 3. Changes made

The existing `AppTypography` now supplies these named logical-pixel roles. They set font size/weight without suppressing system scaling:

| Role | Size / weight |
| --- | --- |
| screenHeader | 20 / 600 |
| sectionTitle | 18 / 600 |
| cardTitle | 14 / 600 (TextTheme titleMedium uses 16) |
| fieldLabel | 14 / 500 |
| input | 16 / 400 |
| helper | 13 / 400 |
| placeholder | 14 / 400 |
| progress | 13 / 500 |
| button | 16 / 600 (existing auth primary uses 15) |
| tooltip | 13 / 400 |
| error | 13 / 500 |

Add Product now shares these roles across information fields, stock cards/batches, date fields, image instructions/labels, Review, approval text and submission. Stock titles stay 14/600 and exact requested descriptions remain 13/400, aligned below them. Their icons are positioned against the scaled first title line; both reserve the independent 48dp help target. The existing unboxed form, four steps, horizontal progress/step-label arrangement, cards, colors and controls remain.

The final supplied paragraphs are treated as tooltip explanations: Standard Stock says “Enter and manage your stock as one total quantity.”; Batch Tracking says “Track stock separately each time you restock. The system uses the oldest stock first when processing orders.”; Low Stock Threshold says “Set when you want to receive a low-stock alert. For example, enter 5 to get notified when 5 or fewer items remain.” Existing stock descriptions remain unchanged. All three use the same existing tooltip widget rather than separate copies.

Purpose-specific existing sizes, such as hero text, metrics and compact navigation, remain where explicit custom styles exist; this is a font/default-role migration, not a layout redesign. Existing Poppins/Montserrat asset registrations remain in pubspec for compatibility, but ordinary app source no longer requests those families.

### 4. How it works / functions, inputs, outputs and data flow

`AppTypography.family` is the single ordinary UI font name. `textTheme(base)` receives an existing TextTheme, applies Inter and merges the shared roles into the matching slots while retaining foreground colors. `theme(base)` receives the existing light/dark ThemeData and returns a copy with those text roles plus app-bar, button, input-decoration and tooltip defaults. Colors, component padding, shapes and controllers are not replaced. Existing `InterTypography`, `ProfileStyle`, `AuthFormStyle` and `CheckoutTypography` callers retain their APIs, but their family resolves to the same Inter asset.

```dart
// Reads the role centrally, then keeps this screen's existing text color.
Text('Available Quantity',
  style: AppTypography.fieldLabel.copyWith(color: existingNavy));
// A future weight/size adjustment belongs in fieldLabel, not every field.
```

`ProductInventoryInfo(id, contentKey, title, message)` is the existing batch tooltip made configurable. Default arguments preserve existing batch call sites and keys. The standard-stock and threshold instances provide their own explanation and accessible label. Their native Tooltip, tap-to-show callback, long press/hover, viewport constraints and outside-dismissal regions stay shared. The explanation uses the original context's text scaler once; only the surrounding WidgetSpan scale is neutralized to prevent double scaling. No tooltip callback invokes stock-method selection or changes threshold values.

Data flow remains: theme/role -> rendered text; user input -> existing controllers -> existing validation -> existing services -> Django. Typography and tooltip changes do not transform submitted values. Date, stock, photo and approval behavior is preserved.

### 5. Backend / API behavior

Unchanged. No endpoint, payload, authentication, seller permission, approval, FIFO calculation, expiry persistence, booking or reporting business logic changed.

### 6. Database / migration impact

None. No schemas, migrations, dependencies, pubspec edits, font downloads or new assets were needed. The existing `InterVariable.ttf` and license remain the source. No production records or deployment changed.

### 7. Checks performed

- Requested whole-project `flutter analyze --no-pub`: **No issues found**, final run 7.8 seconds.
- Dart formatting completed for changed source files.
- Source inspection found no remaining Poppins/Montserrat/Roboto family requests in `lib/`; SugarPie remains the CampusHub wordmark exception. Navigation's existing Inter literals now use the same family constant.
- Read the bundled font's cmap/fvar tables using Python's standard library: peso U+20B1 is present; variable weight range is 100–900, which includes all requested 400–700 weights. No font-inspection package was installed.
- **No Flutter tests, render sessions or device checks were run**, honoring the earlier instruction against further testing while carrying out the newly requested analysis. Previous typography test results below are historical and do not verify this migration. Existing snapshots/font-specific assertions may require updating before a future test run.

### 8. Remaining limitations / troubleshooting / safe practice

Analysis confirms source consistency, not visual fit on every device. Small-screen/large-text behavior has not been visually rechecked for this app-wide change. Text scaling remains enabled; existing wrapping, scrolling and field minimum-height behavior remain. Do not reduce text scaling to hide an overflow. Physical-device/TalkBack and hosted workflows were not exercised or deployed.

Safe manual practice, without submitting records: restart the app so Flutter reloads the bundled font; inspect Login, Home, Profile, a product, a facility and the four Add Product steps in light/dark modes. Increase system text size and check buttons, dialogs and tooltips. On Step 2, open each info icon and confirm the method/value stays unchanged. If a surface has a different font, find its explicit fontFamily/locally rebuilt ThemeData and point it at AppTypography; keep the SugarPie wordmark exception. Make any role adjustment in `app_typography.dart`, then run `flutter analyze --no-pub` from `campushub/`.

## Login/Sign Up Montserrat override - November 2, 2026

The user's explicit authentication-layout request uses the existing bundled Montserrat variable font only for Login/Sign Up. `campushub/lib/module_app/screens/components/auth_form_shell.dart:7` (`AuthFormStyle`) centralizes the role styles; `text(size, weight, color)` returns a font style with the matching weight axis, and `theme(base)` returns a scoped theme that follows the selected light/dark brightness. The latest request removes visible CampusHub text and uses gold `#FCB315`; the circular original logo remains. Screen-owned controllers/validators feed the shared fields, then continue through unchanged AuthService/SessionService/Django code. The original campus photo/logo and other pages' fonts remain intact; no pubspec, backend, dependency or migration changed.

All 39 current focused form/theme/validation/recovery tests passed, with clean six-file analysis and actual bundled-font renders in both themes. Font-family assertions and 2x-text/keyboard checks remain in `campushub/test/auth_form_responsive_test.dart` (`main`); actual persisted-mode/input-retention checks start at line 324. This is a scoped font override, not an app-wide typography migration. Safe exercise: inspect a form field's `TextStyle.fontFamily` and confirm Montserrat while an unchanged Home label still uses its existing Inter role; switch modes and verify both remain readable. Run the focused test before/after any style adjustment. Do not suppress text scaling to make a label fit. The [full layout report](mobile-profile.md:3) records exact files/lines, functions/data flow, troubleshooting, evidence and remaining device/reference limits.

## Inter roles for Home and menus - October 28, 2026

This is the current scoped override for Home and navigation. Older Poppins/Montserrat UI records below are historical for these surfaces; the app-wide Poppins default, SugarPie CampusHub wordmark and Montserrat profile identity remain unchanged.

### 1. Cause / reason

The user explicitly requested Inter SemiBold 600 headings, Inter Medium 500 menu labels, Inter Bold 700 KPI numbers and Inter Regular 400 descriptions. Confirmed inspection showed Home mixed Poppins/Montserrat and the shared drawer used Montserrat throughout. Flutter had no registered Inter font. The web font was WOFF2, so it was not reused as a native Flutter asset. No business-logic defect was inferred.

### 2. Exact files changed, current lines and code anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/theme/app_typography.dart` | 4 `InterTypography`; 23 `sized`; 34 `theme` | Shared scoped Inter styles with explicit weight axes; existing AppTypography/Poppins retained |
| `campushub/pubspec.yaml` | 79 `family: Inter`; 81 TTF asset; 104 OFL asset | Register bundled Inter and its license |
| `campushub/assets/fonts/inter/InterVariable.ttf` | binary font asset | Official Inter variable TrueType font, 879708 bytes |
| `campushub/assets/fonts/inter/OFL.txt` | 1 copyright | Copy of the project's existing full SIL Open Font License notice |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 47 `_homeTypography`; 51 `_text`; 1325 `homeHighlights`; 1461 `_overviewMetricCard`; 1523 `sectionHeader`; 1640 `build` | Scope Home styles/theme, 600 headings, 700 KPI numbers, 500 controls, 400 descriptions; keep other seller tools on existing styles |
| `campushub/lib/module_app/screens/home_page.dart` | 179 `build`; 219 welcome; 256 Explore label | Inter Home welcome, section caption and feedback copy |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 43 `HomeSectionHeader`; 160 `MarketplacePreviewCard`; 354 `FacilityPreviewCard`; 479 `ServicePreviewCard` | Inter preview headings/labels/descriptions and See All labels; shared Search cards inherit this font too |
| `campushub/lib/module_app/widgets/home/campus_home_banners.dart` | 50 `_titleStyle`; 56 `_descriptionStyle`; 206 action text | Inter 600 banner headings, 400 descriptions and 500 action labels |
| `campushub/lib/module_app/widgets/seller/seller_recent_orders.dart` | 51 `style`; 59 `_height` | Inter order cards and matching text measurement; buyer descriptions 400 and action labels 500 |
| `campushub/lib/module_app/widgets/seller/seller_sales_trend.dart` | 48 unavailable; 65 summary; 96 dates | Inter actual-data labels/feedback; chart data/painter/interaction unchanged |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 17 `_DrawerStyle.text`; 189 `build` | Inter 600 group headings and 500 menu/Logout labels for both roles; retain explicit Montserrat avatar/name/program/year identity styles |
| `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` | 207 `fontFamily`; 210 weight axis; 354 central label | Inter 500 selected/unselected tab and Add Product labels |
| `campushub/test/seller_home_layout_test.dart` | 77 / 514 Inter FontLoader; 134 requested-role test | Assert family, FontWeight and real wght axis; render with bundled Inter |
| `campushub/test/seller_drawer_test.dart` | 114 role-aware family assertions; 177 menu weight | Verify Inter heading/menu roles while preserving Montserrat identity assertions |
| `campushub/test/floating_bottom_navbar_test.dart` | 79 family/weight assertions | Assert Inter 500 for all five labels, including the selected tab and center action |
| `campushub/test/drawer_render_test.dart` | 22 Inter FontLoader | Refresh four drawer renders with the actual local font |
| `campushub/THIRD_PARTY_NOTICES.md` | 1 bundled Inter notice | Record font origin and redistributed license |
| `docs/mobile-typography.md` | 3 this section | Current report, functions/data flow, debugging and exercise |
| `CAMPUSHUB_CONTEXT.md` | 3 newest entry | Current scope and verified result |

Nineteen project files: nine runtime Dart files, four test files, pubspec, two font/license assets, the third-party notice and two existing documents. No application entry point or global Poppins family was replaced.

### 3. Changes made

| Role | Family | Weight |
| --- | --- | --- |
| Home/banner/section headings | Inter | SemiBold 600 |
| Sidebar groups | Inter | SemiBold 600 |
| Menu, tab and action labels | Inter | Medium 500, including selected labels |
| Four Sales Overview KPI numbers | Inter | Bold 700 |
| Descriptions and supporting copy | Inter | Regular 400 |

The existing sizes, colors, layout, text scaling, wrapping, carousel dimensions/interaction, routes and role visibility are retained. Font metrics naturally affect text wrapping; the existing measured KPI/carousel heights use the new styles. Profile identity remains Montserrat 600/400 and the CampusHub wordmark remains SugarPie, preserving the standing identity exceptions. Other app pages remain on their existing fonts; the shared product card in Search uses Inter because it is the same Home component.

Inter is bundled from the [official font source](https://github.com/rsms/inter/blob/master/docs/font-files/InterVariable.ttf). SHA256 of the downloaded TTF is `4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf`. Binary table inspection confirmed a `wght` range of 100–900 with default 400 and optical-size range 14–32. There is no runtime font download and no added package dependency. The existing local OFL notice is copied into the Flutter assets and referenced by the third-party notice.

### 4. How it works: functions, inputs/outputs and data flow

```text
pubspec Inter asset -> Flutter asset bundle -> InterVariable.ttf
component text role -> InterTypography.text/sized(size, weight, color)
  -> TextStyle(fontFamily: Inter, FontWeight, FontVariation wght)
  -> TextPainter and Text use matching Inter styles
  -> existing responsive Home/card/navigation layouts
```

`InterTypography.text` accepts the existing size/color/weight/line-height/spacing inputs and returns a TextStyle with a matching `wght` variation. `sized` adapts existing positional-size/integer-weight callers, preserving their usual 1.45 line height. `theme(base)` returns a copy of the current theme that changes text family and button-label typography while preserving its colors, shapes and other behavior. `SellerWorkspaceContent._homeTypography` selects the inline Home or overview destination; `_text` uses Inter there and the original ProfileStyle in other seller tools. `build` supplies the scoped theme to default button labels. Four explicit KPI value styles still use 700; heading call sites explicitly choose 600. Drawer and navbar use 500 for menu labels regardless of selected state.

Annotated example:

```dart
// Section title: SemiBold heading; local font, no HTTP request.
InterTypography.sized(16, weight: 600);
// Existing backend total: Bold KPI number; no total is recalculated here.
InterTypography.sized(22, weight: 700);
// Supporting explanation: Regular.
InterTypography.sized(12); // defaults to 400
```

The approach keeps one shared Inter style definition, supports accurate variable weights offline, and avoids changing the root theme or unrelated Profile/tool typography. User/order/inventory/recommendation data still flows from existing services; no data field determines fonts and no font code changes API results.

### 5. Backend / API behavior

Unchanged. No Django/FastAPI/API/authentication, approval, ownership, order/payment, inventory, analytics or Apriori code changed. The same actual values and callbacks are presented. `inventory_views.py` and `mobile_services.py` were not edited.

### 6. Database / migration impact

None. No migrations, accounts, saved sessions or working-record writes. The only new delivery assets are the local Inter TTF and OFL text. FontTools inspection was attempted but the optional Python module was absent; no Python package was installed. The official native TTF was downloaded instead. No app dependency or lockfile change was required.

### 7. Tests performed

- **94 Flutter tests passed in 15 seconds** across twelve Home/workspace/lifecycle/banner/navigation/Search/drawer/fulfillment/render suites. The first focused typography run passed 39 tests; the final run includes those tests rather than adding their counts.
- Explicit assertions verify Inter family and exact 400/500/600/700 FontWeight and `wght` values, selected/unselected menu labels, all five bottom labels, and preserved Montserrat identity. Existing long-text, empty/error, 280–600px Home, 2x text, portrait/landscape/tablet drawer and up-to-3x navbar checks still pass.
- Scoped analysis of all thirteen changed Dart files reported **No issues found** (2.1s). Final formatting reported **13 files, 0 changed** (0.12s); all thirteen Dart files and the new guide section passed whitespace checks. The generated Flutter `FontManifest.json` contains the registered Inter TTF asset.
- The render environment variable was supplied: fourteen refreshed Home/Explore PNGs are under `scratch/inter-home-20261028/`; the drawer harness refreshed four PNGs under `scratch/home-sidebar-20261028/`. Visually inspected representative Inter overview, 320px/2x facility layout and seller drawer in a dark surrounding theme. These are widget-test fixtures, not production records or native-device screenshots.
- Logs: `scratch/inter-home-20261028/tests-final.log` and `analysis-final.log`. No full app build, installation, emulator/device operation, hot reload/restart, backend tests or web-kit gate score is claimed.

### 8. Remaining limitations, troubleshooting and safe exercise

Stop and rerun the app through your normal Flutter workflow to rebuild/load the newly registered font assets; an already-running session can retain its old font manifest after hot reload. No automatic device action was taken. If Inter looks unchanged, confirm the `pubspec.yaml` asset path, that `InterVariable.ttf` exists, and that the relevant style says Inter; unrelated pages intentionally still use Poppins. A newly pulled checkout must contain the font asset as well as its registration.

Safe exercise: inspect the new role test at `seller_home_layout_test.dart:134`, temporarily change only its expected heading weight from 600 to 500, and run `flutter test --no-pub test/seller_home_layout_test.dart`; the assertion should fail. Restore 600 and rerun to verify success. Then inspect `InterTypography.sized(22, weight: 700)` at the KPI style without editing real totals or services. This demonstrates that typography is a presentation input, independent of database data.

---

October 27, 2026 approved exception: the new optional food-onboarding and Profile Preferences screens use **Montserrat** as explicitly requested, with a white surface, navy `#1A1851` and gold `#FCB316`. Other mobile surfaces retain existing Poppins and `#FCB315`. `_FoodStyle.theme` and heading/card styles in `food_preferences_screen.dart` set the bundled variable font's `wght` axis explicitly to 400/600/700; its file default is 100, which otherwise produced thin text in actual rendering. Preferences state still flows through Django -> `FoodPreferencesService` -> shared screen; typography changes no stored data. The full eight-part change report, exact file map, data flow and actual verification are in the newest section of [mobile-profile.md](mobile-profile.md). Safe practice: run its render test, inspect `scratch/personalized-onboarding-20261027/preferences-390.png` and compare selected/unselected cards at normal and 200% text without changing real users or global theme fonts.

## 1. Cause / reason

The user requested Poppins throughout mobile UI, with exceptions for CampusHub header branding and the profile identity name/program/year-section. Existing mobile source mixed root Roboto, explicit Montserrat overrides, GoogleFonts runtime calls and profile themes. Confirmed source inspection found no BackdropFilter/ImageFilter blur in either drawer. Therefore a literal blur filter was not the cause established here. Inconsistent font delivery and thin variable-font weights were visible; the native preview showed drawer identity text much lighter than its configured weight. Fix delivery and correct weight-axis mapping while preserving the identity face.

The visual direction is compact institutional navigation: solid white light surface / navy dark surface, readable menu roles, aligned outline icons, restrained gold selection, no new navigation structure. #1A1851 / #FCB315 / white remain authoritative. SugarPie header remains. This task does not replace shared Home or the five-tab navbar.

## 2-3. Files changed, current approximate lines and anchors

| File | Current line / nearby anchor |
| --- | --- |
| `campushub/lib/main.dart` | 32 `fontFamily: 'Poppins',`; 37 `fontFamily: 'Poppins',` |
| `campushub/lib/module_app/screens/cart_screen.dart` | 548 `style: AppTypography.text(fontWeight: FontWeight.w600),`; 553 `textTheme: AppTypography.textTheme(Theme.of(context).textTheme),` |
| `campushub/lib/module_app/screens/checkout_screen.dart` | 129 `style: AppTypography.text(fontWeight: FontWeight.w600),`; 134 `textTheme: AppTypography.textTheme(Theme.of(context).textTheme),`; 223 `style: AppTypography.text(` |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 233 `style: AppTypography.text(`; 242 `style: AppTypography.text(`; 258 `style: AppTypography.text(` |
| `campushub/lib/module_app/screens/home_page.dart` | 201 `style: AppTypography.text(`; 219 `style: AppTypography.text(`; 230 `hintStyle: AppTypography.text(` |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 256 `textTheme: AppTypography.textTheme(Theme.of(context).textTheme),`; 426 `textTheme: AppTypography.textTheme(Theme.of(context).textTheme),`; 452 `style: AppTypography.text(` |
| `campushub/lib/module_app/screens/search_page.dart` | 319 `textTheme: AppTypography.textTheme(theme.textTheme).apply(`; 349 `style: AppTypography.text(`; 419 `labelStyle: AppTypography.text(` |
| `campushub/lib/module_app/screens/seller_application_page.dart` | 141 `style?.copyWith(fontFamily: 'Poppins', color: const Color(0xFF17172A));`; 189 `primaryTextTheme: base.primaryTextTheme.apply(fontFamily: 'Poppins'),` |
| `campushub/lib/module_app/screens/seller_dashboard_page.dart` | 310 `fontFamily: 'Poppins',` |
| `campushub/lib/module_app/screens/seller_workspace_content.dart` | 49 `fontFamily: 'Poppins',`; 205 `style: const TextStyle(fontFamily: 'Poppins', fontSize: 13),`; 209 `fontFamily: 'Poppins',` |
| `campushub/lib/module_app/screens/splash_screen.dart` | 117 `fontFamily: 'Poppins',` |
| `campushub/lib/module_app/widgets/add_to_cart_feedback.dart` | 174 `style: AppTypography.text(` |
| `campushub/lib/module_app/widgets/order_summary_widgets.dart` | 190 `style: AppTypography.text(`; 200 `style: AppTypography.text(`; 226 `style: AppTypography.text(` |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 61 `style: AppTypography.text(`; 85 `style: AppTypography.text(`; 256 `style: AppTypography.text(` |
| `campushub/lib/module_app/widgets/navigation/floating_bottom_navbar.dart` | 190 `fontFamily: 'Poppins',` |
| `campushub/lib/module_app/widgets/navigation/seller_drawer.dart` | 10 `static const rowHeight = 52.0;`; 15 `fontFamily: 'Poppins',`; 27 `fontFamily: 'Poppins',` |
| `campushub/lib/module_app/widgets/profile/profile_widgets.dart` | 13 `fontFamily: 'Poppins',`; 19 `static TextStyle identityText(`; 29 `fontVariations: [FontVariation('wght', weight.toDouble())],` |
| `campushub/lib/module_app/screens/components/account_recovery_dialog.dart` | 188 `fontFamily: 'Poppins',` |
| `campushub/lib/module_app/screens/seller_application_form.dart` | existing seller font-weight styles |
| `campushub/lib/module_app/theme/app_typography.dart` | 4 `abstract final class AppTypography {`; 5 `static const family = 'Poppins';` |
| `campushub/pubspec.yaml` | 72 `- family: Poppins`; 74 `- asset: assets/fonts/poppins/Poppins-Regular.ttf`; 76 `- asset: assets/fonts/poppins/Poppins-Medium.ttf` |
| `campushub/test/seller_drawer_test.dart` | 85 `expect(tester.widget<Text>(label).style?.fontFamily, 'Poppins');`; 86 `expect(tester.widget<Text>(label).style?.fontVariations, isNull);` |
| `campushub/test/profile_page_test.dart` | 124 `'Poppins',` |
| `campushub/tool/qa/seller_drawer_preview.dart` | 47 `theme: ThemeData(fontFamily: 'Poppins', brightness: Brightness.light),`; 48 `darkTheme: ThemeData(fontFamily: 'Poppins', brightness: Brightness.dark),` |
| `campushub/assets/fonts/poppins/Poppins-{Regular,Medium,SemiBold,Bold,ExtraBold,Black}.ttf` | Existing Poppins400/500/600/700/800/900 source files, bundled locally |
| `campushub/assets/fonts/poppins/OFL.txt` | Font copyright and redistribution license |
| `campushub/DESIGN.md`; `campushub/.impeccable/design.json` | Poppins UI / Montserrat identity / SugarPie brand roles |
| `AGENTS.md`; `CAMPUSHUB_CONTEXT.md`; `docs/mobile-seller-application.md`; this guide | Current font rules and feature report |

### Changes made

- Root light/dark themes use Poppins. Explicit old Roboto/Montserrat UI styles and scoped text themes use Poppins too, including Home/Search, marketplace/product/checkout/cart, order summaries, bottom navigation, recovery, seller workspace/forms and normal labels.
- `AppTypography.text()` and `textTheme()` replace runtime GoogleFonts calls. Fonts ship offline; no new package or font network request is needed. Existing google_fonts dependency is left intact for compatibility rather than editing unrelated dependencies.
- `ProfileStyle.text()` becomes Poppins; `identityText()` explicitly retains Montserrat for name/program/year-section and the existing profile banner identity typography. Profile account-type/email/actions use Poppins. Header CampusHubBrand stays SugarPie. Seller drawer identity retains Montserrat and explicitly supplies its variable wght axis, so700/500 render at their actual requested weight.
- Seller menu uses Poppins14/500, selected600,11/700 sections with0.6tracking, 52dp minimum expanding rows,22dp outline icons and consistent gutters. Navy-derived secondary colors improve legibility; background stays opaque white/navy. Full identity text wraps instead of clipping at one line. The existing section names, destinations, profile data, selected state and RBAC are preserved.
- Regular drawer remains opaque white with no tonal tint/elevation; its existing CampusHub heading retains SugarPie. Native QA target extends only the existing isolated production-widget preview with light/dark/Poppins themes and a profile identity preview. It has no backend/login and never ships through main.dart.

## 4. Functions, inputs/outputs and data flow

`CampusHubApp.build()` selects the existing light/dark ThemeData with fontFamily Poppins. Flutter resolves each FontWeight against the six registered pubspec assets. No HTTP, account field or database record decides the font. Explicit content styles call `AppTypography.text(color/fontSize/fontWeight/height/letterSpacing)` to return a local TextStyle; scoped page themes call `AppTypography.textTheme(existingTheme)` to preserve the existing role sizes/colors and change only the family.

```dart
// Existing component color/size/weight stay in the component; font is local Poppins.
AppTypography.text(fontSize: 14, fontWeight: FontWeight.w500);
// Explicit identity exception: same Montserrat face and a real variable weight.
ProfileStyle.identityText(13, weight: 600);
```

`ProfileIdentityHeader` routes only name/program/year-section to identityText; normal Profile rows remain Poppins. `SellerDrawer` reads the same real AuthUser and selected destination; only the returned presentation changes. `onSelected` still goes through the existing host and APIs. The dark surface derives from the existing theme selection rather than fake server state. Scrolling and MediaQuery text scaling remain enabled.

Six weights are bundled because those are the actual400-900 weights used in source. Static Poppins faces use normal FontWeight; old Montserrat-specific variation-axis declarations are removed from ordinary seller UI. Variable-axis settings remain only for the retained Montserrat identity. The Poppins source and OFL are from the [official Google Fonts directory](https://github.com/google/fonts/tree/main/ofl/poppins); redistribution notice is bundled in the app.

## 5. Backend / API behavior

Unchanged. Django remains the authority for approvals, ownership, stock, paid sales and Apriori; FastAPI remains chat-only. No auth, routes, REST endpoints, messages, inventory, orders or recommendation logic changed. No synthetic UI recommendations or live fixture records were added.

## 6. Database / migration impact

None. No model, migrations or stored data changes. Run `flutter pub get` after pulling the added font assets/pubspec registration, then rebuild the app; installing a normal updated APK requires no database command. The preview APK is for the emulator only and must not be delivered as the production app.

## 7. Verification

- 71 Flutter tests passed across drawer/Profile/Home/search/navbar/order summary/checkout/seller application/login layouts. Log: `scratch/mobile-navbar/poppins-tests.log`.
- 16 Profile/drawer tests reran with additional family/opacity assertions: identity Montserrat, menu Poppins, no variable axis on Poppins, opaque Drawer background, original actions, portrait/landscape and2x text. Log: `poppins-identity-tests.log`.
- 23-file targeted Flutter analysis passed with no issues after source changes (`poppins-analysis-final.log`). Source scan found no runtime GoogleFonts/Roboto remaining; Montserrat only in the explicit identity roles. Impeccable scan of the key Dart files returned[] after the documented roles were updated (`poppins-type-scan.json`); the regex scan is not a substitute for native rendering.
- Native Pixel_10a emulator screenshots inspected: `scratch/seller-sidebar/poppins/drawer-light.png`, `drawer-selected.png`, `drawer-dark.png`, `drawer-large-text.png`, `drawer-large-bottom.png`. Confirmed opaque surfaces, real font weight, retained Montserrat identity, Poppins menu, aligned outline icons/chevrons, visible selected state, readable dark contrast and long-label/name wrapping at1.5x. Existing widget tests cover2x, short landscape and Profile tablet sizing. Isolated preview data never entered the production database.
- The initial emulator pass encountered an Android System UI not responding dialog; screenshots behind that dialog were not used as success evidence. Emulator-only launch extras disabled Impeller and enabled software rendering; final light/dark/large-text scenes rendered successfully. No production renderer setting changed. Native Profile/tablet follow-up could not locate its QA action; those layouts are covered by widget tests, not claimed as completed native screenshots.
- Preview debug builds passed (91.8s initial/52.5s after the identity weight correction). Emulator font scale/theme/size overrides were reset and only the task emulator was closed. Physical phone/session/data were untouched. Normal `lib/main.dart` debug APK build passed in31.8seconds (`scratch/mobile-navbar/poppins-app-build.log`). Its FontManifest and ZIP entries were checked: all six Poppins weights plus retained Montserrat/SugarPie are bundled. Normal APK was built, not installed on the phone. No backend tests rerun for typography-only changes.

Manual checks: approved Home keeps its header/search/seller additions/public catalogs/five tabs. Open the seller drawer; verify solid surface, actual identity, Poppins menu/section labels, readable selection, all original destinations and scrolling. Try enlarged text and dark theme; inspect the long identity and Suggested Product Bundles row. Open regular Profile; name/program/year-section must retain Montserrat while Personal Information/Account & Security use Poppins. Airplane/offline launch must still render the bundled fonts (network-dependent business data may show its normal error state).

## 8. Remaining limitations and safe practice

No blur filter was found, so this report does not claim a confirmed Gaussian-blur defect. Existing raster logo art is unchanged. Font rasterization can vary with device scaling and accessibility settings. Current bottom-nav scaling convention and existing business/UI availability limitations remain. No live data was modified for visual testing.

Safe exercise: open `AppTypography.text` and predict the family returned for a product card. Trace `ProfileStyle.identityText` and explain why a program label retains Montserrat. In an isolated widget fixture use a longer name and2x TextScaler; run `flutter test test/seller_drawer_test.dart test/profile_page_test.dart` and confirm navigation stays reachable. Restore fixture changes without editing a real user's record.
