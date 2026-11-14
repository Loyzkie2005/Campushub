# Mobile Marketplace filters and category chip row

Flutter app, Marketplace tab (`DashboardScreen` tab 1). Last updated November 15, 2026. Parts are newest first.

## Current: filter sheet — Reset top right, bigger controls (November 15, 2026)

### 1. Cause / reason
Reset sat in the bottom row with a gold underline next to a close ✕, and the sheet controls were compact (30px chips, 13px labels, 40px fields and rows), which made them hard to tap.

### 2. Exact files changed / current lines and anchors
- `campushub/lib/module_app/widgets/marketplace/marketplace_filter_sheet.dart`
  - `:22` sheet corners 16 → 20; `:61` `_side = 18.0`, `_chipGap = 10.0`.
  - `:252` `_buildHeader()` — "Filters" 19px w600 navy; Reset `TextButton` (`marketplace-filter-reset`) on the right, no underline; close `IconButton` removed; fixed 48px height.
  - `:293` `_buildActions()` — only Apply Filters, 52px, 14px corners, 15px w600 text.
  - `:314` `_sectionLabel()` — 15px w500 navy, 20px above, 10px below.
  - `:326` `_priceField()` — wrapped in `SizedBox(height: 48)`, 12px corners, vertical padding 14, centered text.
  - `:395` switch rows 40 → 52px, 15px ink text.
  - `:451` `_FilterChip` — height 40, horizontal padding 16, `fontSize: 14`, `checkSize: 15`.
- `campushub/lib/module_app/widgets/marketplace/marketplace_pill.dart:24-25` — new optional `fontSize` (default 12) and `checkSize` (default 14), so the row chips above the grid are unchanged.
- Tests: `campushub/test/marketplace_filter_test.dart` (rewritten sheet tests), `campushub/test/home_product_ownership_test.dart` (`ensureVisible` before the switch).

### 3. Already there (not changed)
Reset only when `!_draft.isDefault`, Reset keeps the sheet open, body `SingleChildScrollView` with Apply Filters outside it, drag handle, ₱ prefix, empty/filled border colors, `#E2E8F0` divider between switches, switch colors, and drag/outside-tap/back dismissal (`showModalBottomSheet` defaults: `enableDrag`, `isDismissible`).

### 4. How it works / data flow
The sheet edits a local `_draft`. Reset → `_reset()` clears both price controllers and sets `_draft = MarketplaceFilterState.defaults`; `setState` rebuilds, `_draft.isDefault` is now true, so the header hides Reset; nothing is popped. Apply → `_apply()` pops the draft (min/max swapped if reversed). Layout: `Column(handle, header, Flexible(SingleChildScrollView(body)), actions)` inside `ConstrainedBox(maxHeight: 90% of screen)`. On 360x640 the content is taller than 576px, so only the body scrolls and Apply Filters stays at the bottom.
```dart
MarketplacePill(            // sheet chip
  height: 40, padding: EdgeInsets.symmetric(horizontal: 16),
  fontSize: 14, checkSize: 15, showCheckWhenSelected: true, ...)
```
Ripple: `TextButton.styleFrom(overlayColor: navy)` applies navy at 10% when pressed.

### 5–6. Backend / database
None.

### 7. Tests performed
- `flutter analyze` before: no issues; after: **no issues**.
- `flutter test test/marketplace_filter_test.dart test/marketplace_category_bar_test.dart test/home_product_ownership_test.dart`: **24 passed**. New/changed checks: Apply Filters 52px and fixed while the body scrolls at 360x640; sheet chips 40px/14px while default pill stays 38px/12px/14px check; no ✕; outside tap, Android back and drag down close without applying; Reset top right, no underline, restores defaults and keeps the sheet open; no gold text, gold only on 15px chip checks and switch knobs.
- Sheet height at 360x640 measured in the test: 576px (90% cap reached, body scrolls).
- Not checked on a device.

### 8. Remaining limitations / safe practice
- Gold is the project constant `#FCB315` (after the project-wide `#FCB316` → `#FCB315` change), not `#FCB316`.
- At 360x640 the switches sit below the fold until the body is scrolled.
- Practice: change `_chipGap` to 8 and rerun the 360x640 test; then look at the printed "Filter sheet height" line to see how much space it saves.

## Earlier: solid navy header and white page background

### Section 10 implementation report

1. **Cause / reason.** Confirmed in `DashboardScreen.build()`: a full-page `Positioned.fill` painted navy, radial gold and white-fade gradient layers behind the header and the content below it. The category strip's alpha mask revealed that tinted background. This was a presentation issue. This section supersedes earlier gradient-background descriptions for the main dashboard header.

2. **Exact files changed / current lines and anchors.** Paths start at the project root. Existing staged and unstaged work was preserved; task-start copies are under `scratch/mobile-solid-header/*.before`. Search the anchors if later edits move the lines.

   | File | Current line / anchor | Change and purpose |
   | --- | --- | --- |
   | `campushub/lib/module_app/screens/dashboard_screen.dart` | 353 `_NavyHeaderBackground`; 357 `MainAxisSize.min`; 416 white Scaffold; 431 body Column; 548 helper | Make the header content determine the navy background's bounds; remove the full-page background Stack and all three layers. |
   | `campushub/lib/module_app/widgets/marketplace/marketplace_category_bar.dart` | 121 `ColoredBox`; 122 `HomeAppColors.white` | Give the chip row, its fade and Filter button a white backing. |
   | `campushub/test/dashboard_header_test.dart` | 187 `navyBlock` | Check navy, no background gradient, 20px corners and 12px below Search. |
   | `campushub/test/dashboard_search_appbar_test.dart` | 145 `navyBlock`; 160 page boundary | Check header bounds and white content throughout the existing tab-navigation loop, including Marketplace. |
   | `campushub/test/seller_home_entry_test.dart` | 314 `background` | Replace the obsolete gradient-stop expectation; retain seller and navigation coverage. |
   | `campushub/test/marketplace_category_bar_test.dart` | 74 `background` | Check white backing alongside the existing 360px fade, border and Filter checks. |
   | `docs/mobile-marketplace-filters.md` | 5 this report | Document the cause, functions/data flow, measured verification and safe exercise. |

3. **Changes made / expected behavior.** The header uses `HomeAppColors.navy` (`#1A1851`) with **20px rounded bottom corners**. Its SafeArea, greeting, Search and existing 12px bottom padding determine its height; Search fits inside the block. The page and category row use `HomeAppColors.white` (`#FFFFFF`). The navy transition, radial gold glow and white fade were removed completely, along with the obsolete `extended` flag. The `seller-header-gradient` ValueKey stays on the solid navy DecoratedBox for finder compatibility. Status-bar styling and the unselected chip `#E2E8F0` border remain. Dashboard source decreased from **1,272 to 1,206 lines** relative to the task-start copy.

4. **How it works / functions, inputs, outputs and data flow.** `DashboardScreen.build()` passes the existing header widgets as the `child` input of `_NavyHeaderBackground`, then places that header above the Expanded PageView in a Column. The helper's `build()` outputs a navy DecoratedBox with rounded bottom corners; the child's measured size defines its bounds. SafeArea contributes the actual top inset, and `MainAxisSize.min` makes the inner Column follow its contents. The PageView starts at the header's bottom, so transparent content reveals the white Scaffold.

   `MarketplaceCategoryBar.build()` receives the same categories, selected values and callbacks and wraps its existing Row in a white ColoredBox. `MarketplaceEdgeFade` remains a `BlendMode.dstIn` alpha mask: it changes opacity rather than painting a visible color. Its transparent edges reveal the explicit white backing, producing a white fade without another colored overlay. Chip scrolling, selected-chip reveal, Filter opening and other uses of the shared mask keep their existing behavior.

   Annotated example: a larger device top inset or larger greeting text grows the header automatically. Search still ends **12px before** the navy block's bottom; chips begin beneath it on white. The 20px radius changes only the background shape. No product data is transformed by these layout widgets.

5. **Backend / API behavior.** No backend or endpoint changed. Catalog/filter data, ownership and seller permissions, drawer/profile actions, Search, notifications and cart behavior retain their existing code paths. This request changes the background only.

6. **Database / migration impact.** None: no model, migration, dependency, working record or stored image changed. Visual fixtures use in-memory HTTP responses and preferences; their sample products are never saved. All six edited Dart files use CRLF without a byte-order mark.

7. **Tests performed / actual results.**
   - Before editing: `flutter analyze --no-pub` reported **No issues found**; the four targeted suites below passed **36/36** tests.
   - After editing: `flutter analyze --no-pub` reported **No issues found** (5.6 seconds). A sandboxed piped attempt stalled without output and was stopped; the completed run used the installed runtime outside the sandbox. Evidence: `scratch/mobile-solid-header/analyze-after.log`.
   - `flutter test --no-pub --reporter expanded test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/marketplace_category_bar_test.dart test/seller_home_entry_test.dart`: **36/36 passed**, including updated bounds/color assertions, multiple widths/text scales, safe insets and existing drawer/navigation behavior. Evidence: `tests-after.log` in the same folder.
   - Existing seller render case at 390px: **1/1 passed**, retaining the header keys. Its Marketplace capture showed the expected offline product state, so the additional fixture render checked populated cards too.
   - Scratch-only `solid_header_render_test.dart`: **2/2 passed**, rendering actual Home and populated Marketplace widgets at 360px and 390px with bundled fonts and local HTTP fixtures. No production code imports this harness. Evidence: `render-grid.log` and `renders/home-360.png`, `home-390.png`, `marketplace-360.png`, `marketplace-390.png`.
   - Visual inspection confirmed rounded navy ending below Search and chips/cards on white. Pixel samples in all four fixture captures returned `#1A1851` in the status area and `#FFFFFF` in page margins below the header. Scoped whitespace checks passed; the six edited Dart files have zero lone LF endings.

8. **Remaining limitations / troubleshooting / safe practice.** Checks used Flutter widgets and fixtures, not a rebuilt app on a physical phone; the full unrelated suite was not rerun for this background change. Existing gold accents inside controls/content remain. If the old tint persists on a running device, hot restart or rebuild and confirm `_NavyHeaderBackground` is loaded. If a future spacing change clips Search, compare its 20px horizontal inset and 12px bottom padding with the background's 20px radius before introducing a fixed height. Safe exercise: locate those values and trace the helper's child into SafeArea, then run `flutter test --no-pub test/dashboard_header_test.dart test/marketplace_category_bar_test.dart`. Verify the tests pass and compare the saved renders; this checks the layout relationship without editing data or navigation.

## Part 4: tap a selected chip again to clear it

### 1. Cause / reason
Tapping the already-selected category chip did nothing, so the only way back to "All" was to scroll left to the All chip.

### 2. Exact files changed / current lines and anchors
- `campushub/lib/module_app/widgets/marketplace/marketplace_filter_state.dart:50` — new `selectOrClearCategory(String category)`, directly below `withSingleCategory` (line 43).
- `campushub/lib/module_app/screens/dashboard_screen.dart:669` — `_buildCategoryCards` → `onSelected` now calls `selectOrClearCategory` (was `withSingleCategory`).
- `campushub/test/marketplace_filter_test.dart` — new test `chip row: tap selects one, tapping it again returns to All`.

### 3. Changes made
`withSingleCategory` is unchanged and still used by the Home → Marketplace category shortcut (`didUpdateWidget` and `initState` in `_MarketplacePageState`), so a Home shortcut always *selects* and never clears. The filter sheet still uses `toggleCategory` (multi-select), unchanged.

### 4. How it works / functions and data flow
Input: the tapped chip name. Output: a new immutable `MarketplaceFilterState` (sort, price and toggles are copied unchanged by `copyWith`).
```dart
if (_isAll(category)) return copyWith(categories: const {});           // "All"
final isOnlySelection = categories.length == 1 &&
    categories.first.trim().toLowerCase() == wanted;                   // Snacks again
return copyWith(categories: isOnlySelection ? const {} : {category});   // else just this one
```
Tap → `MarketplaceCategoryBar.onSelected` → `setState(_filters = _filters.selectOrClearCategory(c))` → `build` → `_filters.apply(products)` → grid. Names compare case-insensitively, like `apply`. If Snacks + Desserts were chosen in the sheet, tapping Snacks in the row leaves only Snacks (it is not "the only selection", so it selects).

### 5–6. Backend / database
None. Client-side filter only; no API, migration or data change.

### 7. Tests performed
`flutter test test/marketplace_filter_test.dart` — passed (includes the new test). `flutter analyze` — no issues.

### 8. Remaining limitations / safe practice
Not verified on a device. Practice: make a second tap on a multi-selection also clear it by changing `isOnlySelection` to `categories.any(...)`; then run the test above and see the "Snacks + Desserts" expectation fail, which shows why the current rule is "only selection".

## Part 3: final polish — colors, tap tint, sheet chips

### 1. Cause / reason
- The final spec makes navy the dominant color and uses gold only as a small accent: a gold check on selected sheet chips, a gold icon on selected row chips and on the active Filter button, and a gold knob on switches that are on.
- Ripples were hidden: the fill was painted by an `AnimatedContainer` *above* a transparent `Material`, so the InkWell splash drew underneath it. Ripple colors also came from the app theme, which is seeded from navy and produces a purplish indigo.
- Sheet chips were Material `ChoiceChip`s at weight 500 with no check, and their title and labels were ink at weight 600.

### 2. Already done before this round (not changed)
- **A1–A5**: wrapped multi-select chips; content-height sheet capped at 90%; sections in the right order; Reset only when not default; changes apply only on Apply Filters; the state is applied in `_filteredCategoryProducts`; Home preselect still works.
- **B1–B3**: Row [Expanded list, 8px, Filter button]; 24px edge fade with the left side only after scrolling; list right padding 8; 38px pills, 20px radius, 12 × 8 padding, soft shadow.
- **B4**: the selected chip scrolls into view. This uses the same reveal step as `Scrollable.ensureVisible` (`getOffsetToReveal`), limited to the chip row; see Part 2 §4 for why.
- **C**: unselected chips were already white with a `#E2E8F0` border and ink text at 600, and the active Filter button was already navy with a gold icon.

### 3. Exact files changed / current lines and anchors
| File | Lines (current) | Anchor |
|---|---|---|
| `campushub/lib/module_app/widgets/marketplace/marketplace_pill.dart` | 58, 74, 98, 114 | `splashFor`, `TweenAnimationBuilder`, `clipBehavior: Clip.antiAlias`, `showCheckWhenSelected && selected` |
| `campushub/lib/module_app/widgets/marketplace/marketplace_filter_sheet.dart` | 254, 294, 312, 334, 370, 383, 418, 456, 499 | title w500, Reset `decorationColor`, Apply `circular(12)`, label w500, `'₱'`, price `enabledBorder`, `activeThumbColor`, `_FilterChip`, Filter button `unselectedLabelColor` |
| `campushub/lib/module_app/widgets/marketplace/marketplace_category_bar.dart` | 128 | `MarketplacePill.defaultHeight + 3` |
| `campushub/test/marketplace_filter_test.dart`, `campushub/test/marketplace_category_bar_test.dart` | — | color, check, tap-tint and multi-select fit tests |

### 4. Changes made / how it works
- **`MarketplacePill`** is now `DecoratedBox(shadow)` → `Material(color: fill, shape: StadiumBorder(side), clipBehavior: antiAlias)` → `InkWell` → content. The ripple now paints above the fill and is clipped to the pill.
  - The 200ms color animation is kept with a `TweenAnimationBuilder<double>`. `t` runs from 0 (unselected) to 1 (selected), and the fill, border, text and icon colors are interpolated with `Color.lerp`.
- **Tap colors** are set on every InkWell (splash, highlight, hover and focus), so nothing comes from the theme:

  | Fill | Splash | Highlight |
  |---|---|---|
  | White | navy 10% | navy 6% |
  | Navy | white 16% | white 8% |

  `MarketplacePill.splashFor` and `highlightFor` are reused by the sheet's switch rows and switch overlay.
- **Sheet chips** (`_FilterChip`) now use `MarketplacePill` with `showCheckWhenSelected: true`, at a 30px height so all sections still fit at 360×640.
  - Selected: navy, white text at 700, with a 14px gold check.
  - Unselected: white, `#E2E8F0` border, ink text at 600.
- **Filter button** passes `unselectedLabelColor: HomeAppColors.navy`. By default it has a navy icon and text, with the same `#E2E8F0` border as the chips.
- **Sheet title and section labels**: navy at weight 500, with no bar, line or icon before them.
- **Switches**:
  - On: navy track, gold knob.
  - Off: `#E2E8F0` track, white knob.
  - No outline.
- **Apply Filters** has 12px corners. **Reset** is navy text with a 2px gold underline.
- **Price fields** show a navy `₱` prefix and "Min"/"Max" hints. The border is navy once the field has a value and `#E2E8F0` while empty.
- **Gold** comes from `HomeAppColors.bundleGold`, which is exactly `#FCB315`. `HomeAppColors.gold` is `#FCB315`, which the project rules keep for Flutter, so `home_preview_cards.dart` was not edited.

### 5. Backend / API behavior
None.

### 6. Database / migration impact
None.

### 7. Tests performed
- `flutter analyze` before this round: **No issues found**. After: **No issues found**.
- 21 Marketplace tests pass (`marketplace_filter_test.dart`, `marketplace_category_bar_test.dart`, `home_product_ownership_test.dart`). They cover:
  - the 360×640 sheet (565px, scroll extent 0), including when Snacks and Desserts are selected with their checks;
  - chip taps keep the sheet open, and Apply closes it;
  - selected chips are navy with white text and a gold check or icon; unselected chips are white with ink text;
  - the Filter button and the unselected chips share the same shape, border, height and radius, and the active button matches a selected chip;
  - the Filter button is navy with a gold icon only when a filter differs from the defaults, and Reset restores the defaults;
  - the right fade and the 8px gap at 360px;
  - unselected chips and the default Filter button share the same navy 10%/6% tint, and every row InkWell has explicit colors;
  - Snacks + Desserts with Low→High.
- The 44 dashboard and home tests in the related suites also pass.
- The full suite has 43 failures. They are all in files that do not import any changed code (`auth_form_responsive`, `checkout_layout`, `order_summary`, `product_details_layout`, `seller_add_product_page`, `seller_recent_orders`, `signup_spacing`), and they come from other uncommitted work in the repo.
- **Practice**: in `marketplace_pill.dart`, change the unselected splash alpha from `.10` to `.18`. Long-press a chip in the app and the tint should be darker. Run `marketplace_category_bar_test.dart` and the tap-tint test should fail, which shows that it guards the value. Revert afterwards.

### 8. Remaining limitations — other Marketplace widgets still using the theme ripple
- `_ProductsMessageCard`'s `OutlinedButton` (Retry or Refresh) in `dashboard_screen.dart` uses the theme overlay, which is the seeded indigo.
- `MarketplacePreviewCard` / `_LargeProductCard` buttons (the add-to-cart and favorite `IconButton`s and the card `InkWell` in `home_preview_cards.dart`) use theme ripples.
- These were not changed, because the spec says not to touch unrelated files.

## Part 2: chip row polish (edge fade, shared outline, scroll into view)

### 1. Cause / reason
- Chips were cut off with a hard edge right next to the filter icon, so the last visible chip looked broken.
- The chips and the Filter button were styled in two separate places, so their borders, heights and text could drift apart. Unselected chip text used `#1E293B` instead of the ink color `#17172A`, and selected chips used the older navy `#142B47` instead of `#1A1851`.
- If a selected category was off-screen (for example, Home → "Others"), the user could not see which chip was active.

### 2. Exact files changed / current lines and anchors
| File | Lines (current) | Anchor |
|---|---|---|
| `campushub/lib/module_app/widgets/marketplace/marketplace_pill.dart` (new) | 11, 40 | `class MarketplacePill`, `static BoxDecoration decoration` |
| `campushub/lib/module_app/widgets/marketplace/marketplace_category_bar.dart` (new) | 15, 73, 85, 175 | `class MarketplaceCategoryBar`, `_onScroll`, `_revealSelected`, `class MarketplaceEdgeFade` |
| `campushub/lib/module_app/widgets/marketplace/marketplace_filter_sheet.dart` | 474 | `class MarketplaceFilterButton` now wraps `MarketplacePill` |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 32, 727, 792 | import; `Widget _buildCategoryCards() => MarketplaceCategoryBar(`; `_buildCategoryCards(),` in `build` |
| `campushub/test/marketplace_category_bar_test.dart` (new) | whole file | 3 widget tests |

### 3. Changes made
- **Added** `MarketplacePill`: the single pill used by every category chip and by the Filter button. It has a 38px height, 20px radius, 12 × 8 padding, a 1px border and a soft shadow (black 3%, blur 2, y 1).
  - Unselected: white fill, `#E2E8F0` border, ink `#17172A` text at weight 600, navy icon.
  - Selected: navy `#1A1851` fill and border, white text at weight 700, gold `#FCB315` icon.
- **Added** `MarketplaceCategoryBar`: the chip strip, an 8px gap, then the Filter button pinned on the right. The strip has `EdgeInsets.only(right: 8)` padding (plus 3px at the bottom so the shadow is not clipped).
- **Added** `MarketplaceEdgeFade`: a 24px fade at the right edge that is always on, and at the left edge once `offset > 0`.
- **Changed** `_buildCategoryCards()` in the dashboard. It used to be about 80 lines of inline chip markup; it now just configures `MarketplaceCategoryBar`. The category icon mapping (`_getCategoryIcon`) stays in the dashboard.
- **Changed** the horizontal `ListView.separated` to a `SingleChildScrollView` + `Row`. A lazy ListView does not build chips that are far off-screen, so they have nothing to scroll to. With only 11 chips, building them all costs very little.

### 4. How it works / functions, inputs, outputs and data flow
```
_MarketplacePageState._filters ──► _buildCategoryCards()
    selected = lower-case names of _filters.categories (empty = All)
    filterActive = !_filters.isDefault
        │
        ▼
MarketplaceCategoryBar
  ├─ chip tap ─► onSelected(cat) ─► _filters.withSingleCategory(cat) ─► setState
  ├─ didUpdateWidget: selected changed? ─► post-frame _revealSelected(animate: true)
  ├─ ScrollController listener _onScroll ─► _showStartFade = offset > 0
  └─ MarketplaceEdgeFade(showStart) wraps the scroll view
```
- **Fade**: `ShaderMask` with `BlendMode.dstIn` multiplies the chips' alpha by a black→transparent gradient. Because it fades the chips themselves instead of painting a colored overlay, the fade always matches whatever background sits behind the row.
- **Scroll into view**: `_revealSelected` finds the first selected chip (in category order) and asks its viewport for `getOffsetToReveal(chip, 0.5)`, which centers it. It then animates the chip row to that offset. This is the same reveal step that `Scrollable.ensureVisible` performs. It is limited to the chip row because `ensureVisible` would also scroll the vertical Marketplace page.

Annotated example (simplified from `MarketplaceEdgeFade`):
```dart
final stop = 24 / rect.width;          // 24px expressed as a 0–1 gradient stop
LinearGradient(
  colors: [showStart ? clear : black,  // left edge: fade only after scrolling
           black, black,               // fully visible middle
           clear],                     // right edge: always fades
  stops: [0, stop, 1 - stop, 1],
);
```

### 5. Backend / API behavior
None. This is visual and client-side only.

### 6. Database / migration impact
None.

### 7. Tests performed / troubleshooting and safe practice
- `flutter analyze`: **No issues found**.
- `flutter test test/marketplace_category_bar_test.dart`: all 3 tests pass.
  - At 360px, the Filter button sits exactly 8px after the strip. The chips overflow (`maxScrollExtent > 0`), so the trailing chip sits under the right fade, and the left fade appears after dragging.
  - The unselected chip and the default Filter button have the same border (`#E2E8F0`), radius, shadow and 38px height. The active button decoration equals the selected chip decoration.
  - Selecting "Others", which starts off-screen, scrolls it fully inside the strip.
- Troubleshooting:
  - If the left fade never appears, check that `_controller` is attached to the `SingleChildScrollView`.
  - If a chip doesn't scroll into view, check that its `GlobalKey` exists in `_chipKeys`.
- **Practice**: change the fade width to 32 by passing `extent: 32` to `MarketplaceEdgeFade` in `marketplace_category_bar.dart`. Run the bar test and the app. The edge should fade a little more gradually. Revert afterwards.

### 8. Remaining limitations
- The right fade is always on, as requested, so even when scrolled to the very end the last chip's trailing ~16px is faded. The 8px right padding reduces this.
- (Fixed in Part 3: ripples now paint above the fill.)

---

## Part 1: filter sheet (no scrolling) and full filter

### 1. Cause / reason
- The old sheet (`_openCategoryFilter`) was a `ListView` of `ListTile`s inside a 75% `ConstrainedBox`. Its 11 categories needed scrolling, it closed on every tap, and it only filtered by category.
- The planned Sort, Price range, In stock and Hide my products filters did not exist yet.

### 2. Exact files changed / current lines and anchors
| File | Lines (current) | Anchor |
|---|---|---|
| `campushub/lib/module_app/widgets/marketplace/marketplace_filter_state.dart` (new) | 6, 20, 43, 48, 73 | `enum MarketplaceSort`, `class MarketplaceFilterState`, `withSingleCategory`, `toggleCategory`, `apply` |
| `campushub/lib/module_app/widgets/marketplace/marketplace_filter_sheet.dart` (new) | 11, 76, 82, 114, 432 | `showMarketplaceFilterSheet`, `_reset`, `_apply`, `maxSheetHeight`, `_FilterChip` |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 643, 658, 672, 682, 740, 769 | `didUpdateWidget`, `MarketplaceFilterState _filters`, `_openCategoryFilter`, `_filteredCategoryProducts`, `initState`, `final heading` |
| `campushub/test/marketplace_filter_test.dart` (new) | whole file | 4 unit + 4 widget tests |
| `campushub/test/home_product_ownership_test.dart` | "dashboard passes ownership…" | turns off Hide my products before checking own cards |

### 3. Changes made
- **Replaced** `String _selectedCategory` with an immutable `MarketplaceFilterState _filters`. It holds the category set (empty = All), the sort, min/max price, `inStockOnly` (default on) and `hideOwnProducts` (default on).
- **New sheet**:
  - Title "Filters" in ink at weight 600, with a close button.
  - Category chips in a `Wrap(spacing: 8, runSpacing: 8)`. They are multi-select, and "All" clears the others.
  - Sort by: Newest, Price: Low to High, Price: High to Low.
  - Min ₱ and Max ₱ price fields.
  - Two switches: In stock only and Hide my products.
  - Reset (shown only when the draft differs from the defaults) and a full-width navy Apply Filters button.
  - The sheet's colors are forced to navy, so Material purple never appears.
- **Sizing**:
  - `isScrollControlled: true` and `MainAxisSize.min`, so the sheet is exactly as tall as its content.
  - The sheet is capped at 90% of the screen. The body sits in a `Flexible` `SingleChildScrollView` that only scrolls if the content is taller than that cap, for example when the keyboard is open or text is very large.
  - At 360×640 the sheet measures **565px**, below the 576px cap, so nothing scrolls.

### 4. How it works / functions, inputs, outputs and data flow
```
Filter button ─► _openCategoryFilter()
   └─ showMarketplaceFilterSheet(initial: _filters, categories)
        sheet edits a local _draft (chip taps never close the sheet)
        Apply Filters ─► Navigator.pop(_draft)   (min > max are swapped)
        close / swipe down ─► null (no change)
   └─ setState(_filters = applied)
build() ─► _filteredCategoryProducts ─► _filters.apply(_products, viewerRef)
        1. category set   2. inStockOnly → ProductItem.isPurchasable
        3. hideOwn → product.sellerRef == viewerRef
        4. min/max vs basePrice   5. stable sort
```
- `apply` uses `mergeSort`, which is stable: products with equal prices keep the API's order.
  - **Newest** sorts by `submittedAt`. Products without a date come last.
  - **Price** sorts use `basePrice`, which is the lowest price when a product has a variant price range.
- Home → Marketplace preselect still works. `didUpdateWidget` sees a new `selectionRevision` and calls `withSingleCategory`. Only the category changes; the sort, price and switches stay as they were.

### 5. Backend / API behavior
None. Filtering happens on the client over the products that `/api/products/` already returned.

### 6. Database / migration impact
None.

### 7. Tests performed
- `flutter analyze` (whole app): **No issues found**.
- `flutter test test/marketplace_filter_test.dart`: all 8 tests pass.
  - Snacks + Desserts with Low→High returns only those categories, in ascending order.
  - At 360×640 the whole sheet is visible with a scroll extent of 0.
  - Chip taps keep the sheet open, and Apply applies the filters and closes it.
  - Closing without applying keeps the old filters.
  - The Filter button is navy only when a filter differs from the defaults, and Reset restores the defaults.
- `test/home_product_ownership_test.dart` was updated, because own products are now hidden by default. It now asserts that only one card shows, turns the switch off, then checks the "Your product" badge as before.

### 8. Remaining limitations
- **Hide my products defaults to on.** Sellers no longer see their own listings in the Marketplace grid until they switch it off. This follows the request, but it changes earlier behavior.
- Filter choices are not saved between app launches.
- Tapping a chip in the row selects a single category; multi-select is available only in the sheet.
