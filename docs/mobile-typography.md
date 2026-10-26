# Mobile Poppins typography and sidebar

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
