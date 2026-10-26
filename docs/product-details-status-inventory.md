# Product Details — approval, listing and inventory

## Top-filling hero gallery on cream `#F9FDE7` image background, white Product Details section & marketplace cards, removed quantity, navy blue `#1A1851` heart, `Chat | Add to Cart` bottom bar, seller below Description, circular color swatches without select prompt text, and review stars above `[Badge] Product Name` — October 20, 2026

1. **Cause / reason:** Following the user's request (`"/emil-design-eng /frontend-design redesign my products detailsremove the products details text =fill image in te top apply the cream color to the bg  then in marketplace card change to white then remove quantity yjrm change color o he heart to navyblue"`), their surface clarification (`"change back to white the section facility details"`, `"i mean product details got cream color remove that only bg on the image"`), their layout follow-up (`"can youbadd chat behind add to cart then has Chat | add to cart then move the seller below of the description"`, `"then insrtead add to cart button or container can you same as chat top is icon then buttom is text"`), their variant follow-up (`"remove text message please seklect colorsdo rvariants below of the variants can you do the colors variants cvircle color instead of texct? /emil-design-eng"`), and their heading hierarchy follow-up (`"can you move the review star top of product name then badge put left behind poduct name"`):
   - Removed the `"Product Details"` header text (`SliverAppBar.title = null`) and restored the full-bleed top-filling `FlexibleSpaceBar` hero image (`_ProductHeroImage` with `BoxFit.cover` and below-image pagination dots).
   - Restored the Product Details lower content section (`Scaffold.backgroundColor`), collapsed `SliverAppBar.backgroundColor`, and the `26dp` below-image pagination indicator strip (`_ProductHeroImage` outer `ColoredBox`) to `Colors.white` (`#FFFFFF`), keeping the cream `#F9FDE7` background **only on the top hero image container** (`_ProductHeroImage` inner `DecoratedBox` and `ProductImage`).
   - Changed Marketplace product cards (`MarketplaceColors.cardSurface` and `MarketplaceColors.imageSurface`, consumed by `MarketplacePreviewCard`, `ProductsScreen`, `DashboardScreen`, and `_RelatedProductCard`) to `Colors.white` (`#FFFFFF`).
   - Moved the review star summary (`_ProductReviewSummary`, `product-review-summary`) **above** the product name row, and placed the conditional `New` / `Hot` badge (`product-listing-badge`) on the **left** before (`8dp` gap) the `Expanded` product name (`product-heading-name`) in the same horizontal `Row`, followed by the price (`product-selected-price`) `4dp` below.
   - Removed the `Quantity` selector (`_ProductQuantitySelector`, `'Quantity'` label, and `_quantity` stepper) from `ProductDetailsScreen`, keeping inline selection with quantity `1`.
   - Removed the `"Select color"` / `"Select <variant>"` prompt text (`variant-placeholder-${groups[i].name}`) and the inline `"Please choose <group>."` (`_selectionError`) text message below `_ProductVariantChoices`, leaving clean variant group headings (`Colors`, `Size`, etc.).
   - Rendered **all** options in color variant groups (`_isColor(groups[i]) == true`, including compound color names such as `'RED Cream'` in `Hot Coffee`) as circular color swatches (`_ColorVariantChoice` with `BoxShape.circle` and `_lookupColor` token/hex matching) instead of text `FilterChip`s or letter initials.
   - Moved `_SellerIdentity` **below** `_ProductDescription` (`price` → `options` → `Description` → `seller` → `reviews` → `related`, with `12dp` spacing between sections).
   - Added a separate `Chat` action (`LucideIcons.messageSquare` icon on top + `"Chat"` label below, `product-bottom-chat-button`), a vertical divider `"|"` (`1x32dp` `#E8EAF0`, `product-bottom-chat-divider`), and a matching top-icon + bottom-text `Add to Cart` action (`LucideIcons.shoppingCart` icon on top + `"Add to Cart"` label below, `product-bottom-add-to-cart-button`, without an outlined button container) to the left of the `Expanded` solid `Buy Now` button in `_ProductBottomBar`.
   - Changed all Favorite heart icons (`ProductDetailsScreen` header button, `_RelatedProductCard`, `MarketplacePreviewCard`, `ProductsScreen`, and `DashboardScreen`) to Navy Blue (`#1A1851`) in both unselected (outline) and selected (filled) states.

2. **Exact files changed / current anchors (10 files):**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/theme/marketplace_colors.dart` | 5 `cardSurface = Colors.white`; 6 `imageSurface = cardSurface` | Changed shared Marketplace card and image surfaces to `Colors.white`. |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 290 `BuySelection(quantity: 1)`; 461 `Scaffold(backgroundColor: Colors.white)`; 465 `SliverAppBar(backgroundColor: Colors.white, expandedHeight: ..., flexibleSpace: FlexibleSpaceBar(background: _ProductHeroImage(...)))`; 588 `onChat: _openSellerChat`; 632 `_ProductHeroImage` | Removed `"Product Details"` title, `_ProductQuantitySelector`, and `_selectionError` inline text state, restored top-filling `FlexibleSpaceBar` hero gallery with `#F9FDE7` cream background **only on the image area** while keeping the `Scaffold`, collapsed `SliverAppBar`, and below-image pagination strip `Colors.white`, wired `onChat: _openSellerChat` to `_ProductBottomBar`, and set top-right Favorite heart icon to `#1A1851` Navy Blue. |
| Same screen | 802 `_ProductInfoContainer` (854 `_ProductReviewSummary`, 864 `Row(children: [badge, Expanded(name)])`, 948 `_ProductDescription`, 950 `_SellerIdentity`); 1048 `_ProductVariantChoices` & 1195 `_ColorVariantChoice`; 1530 `_ProductBottomBar` & 1618 `_BottomIconTextAction` (`product-bottom-chat-button`, `product-bottom-chat-divider`, `product-bottom-add-to-cart-button`); 1950 `_RelatedProductCard` | Moved `_ProductReviewSummary` above the product name, placed `badge` (`product-listing-badge`) left of `Expanded` `name` (`product-heading-name`) in a `Row`, removed `"Select color"`/`"Select ..."` placeholder text and inline `selectionError` text below variants, rendered all color group options as circular color swatches (`_ColorVariantChoice` with token-based `_lookupColor` for names like `'RED Cream'`), moved `_SellerIdentity` below `_ProductDescription` (`12dp` spacing), rendered both `Chat` and `Add to Cart` as matching top-icon + bottom-text actions (`_BottomIconTextAction`) separated by `|` (`product-bottom-chat-divider`) before the `Expanded` `Buy Now` button in `_ProductBottomBar`, and wired `_RelatedProductCard` to `MarketplaceColors.cardSurface` / `imageSurface` (`Colors.white`) and `#1A1851` navy heart icon. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 239 `color: HomeAppColors.navy` | Changed `MarketplacePreviewCard` favorite heart icon color from red (`HomeAppColors.error`) to `HomeAppColors.navy` (`#1A1851`). |
| `campushub/lib/module_app/screens/products_screen.dart` | 596 `color: const Color(0xFF1A1851)` | Changed Marketplace grid card favorite heart icon color from red/slate to `#1A1851` Navy Blue. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 1122 `color: const Color(0xFF1A1851)` | Changed legacy Dashboard product card favorite heart icon color from red/slate to `#1A1851` Navy Blue. |
| `campushub/test/product_details_layout_test.dart` | 160 `Colors.white` `SliverAppBar`/`Scaffold` & `#F9FDE7` hero `ProductImage` assertions; 220 `summary` above `name` and `name` above `price` assertions; 352 navy `#1A1851` heart icon assertion; 417 `badge` left of `'Campus Shirt'` assertion; 537 & 808 circular color swatch (`RED Cream`, `Custom shade`) and absence of `'Select color'`/`'Select size'` assertions; 626 `options` → `Description` → `seller` (`+ 12dp`) & `Chat | Add to Cart` bottom bar assertions | Verified titleless white `SliverAppBar` + `Scaffold`, `#F9FDE7` cream background on the hero `ProductImage`, review summary above `[badge] + name` and `price`, absence of `'Product Details'`, `'Quantity'`, and `'Select color'`/`'Select size'` text, circular color swatches for all color group options, `#1A1851` favorite heart color in both states, `Description` above `seller`, and `Chat | Add to Cart` icon+text bottom bar geometry. |
| `campushub/test/dashboard_header_test.dart` | 112 `Colors.white`; 121 `Colors.white` | Updated `MarketplacePreviewCard` surface and image background assertions to `Colors.white`. |
| `campushub/DESIGN.md` | 10 `marketplace-card-surface: "#FFFFFF"`; 55 `components.product-details` | Recorded white Product Details body/indicator strip, cream `#F9FDE7` hero-image-only backing, review summary on top and badge left of product name, circular color swatches without select prompt text, seller below Description, `Chat | Add to Cart` icon+text bottom bar, and white marketplace card tokens. |
| `CAMPUSHUB_CONTEXT.md` | 9 `Latest Product Details top-filling hero on cream #F9FDE7 image bg, white details section...` | Saved latest design and verification summary. |

3. **Changes made:**
   - **Titleless Top-Filling Hero Gallery (`#F9FDE7` Image Only) & White Product Details Section (`ProductDetailsScreen`)**: `SliverAppBar` removes `title` and uses `expandedHeight: MediaQuery.sizeOf(context).width.clamp(240.0, 340.0)` with `FlexibleSpaceBar(background: _ProductHeroImage(...))` so the product image fills the top of the screen, with circular `48x48` `Back` (top-left) and `Cart` + `Favorite` (top-right) controls floating over the photo and the `26dp` pagination strip directly below the photo. Only the hero image box (`_ProductHeroImage`'s `Expanded` `DecoratedBox` and `ProductImage`) uses the cream `#F9FDE7` background; `Scaffold.backgroundColor`, `SliverAppBar.backgroundColor`, and the outer `ColoredBox` behind the pagination dots are `Colors.white` (`#FFFFFF`).
   - **Review Stars Above `[Badge] Product Name` (`_ProductInfoContainer`)**: `_ProductReviewSummary` (`product-review-summary`) now appears first at the top of `_ProductInfoContainer` (when `!ownerView`), followed `4dp` below by a horizontal `Row` containing the conditional `New` / `Hot` badge (`product-listing-badge`, with `8dp` right spacing) on the left and the `Expanded` `22sp/600` product name (`product-heading-name`) on the right, followed `4dp` below by the `26sp/700` price (`product-selected-price`).
   - **Circular Color Swatches & Removed Variant Prompt Text (`_ProductVariantChoices` & `_ColorVariantChoice`)**: Removed the `"Select color"` / `"Select <variant>"` text beside the variant group heading and removed the inline `"Please choose <group>."` (`_selectionError`) text widget below `_ProductVariantChoices`. Every option inside a color group (`_isColor(groups[i]) == true`) now renders as `_ColorVariantChoice` (`BoxShape.circle`) instead of falling back to a text `FilterChip`, with `_ColorVariantChoice._lookupColor` matching exact color names, hex codes, and compound color words (such as `'RED Cream'` -> `#DC2626`).
   - **Seller Moved Below Description (`_ProductInfoContainer`)**: `_ProductDescription` now sits `12dp` below `_ProductVariantChoices` (or `price`), and `_SellerIdentity` sits `12dp` below `_ProductDescription`.
   - **`Chat | Add to Cart` Icon+Text Bottom Bar (`_ProductBottomBar` & `_BottomIconTextAction`)**: Both `Chat` (`LucideIcons.messageSquare` icon on top + `"Chat"` text below) and `Add to Cart` (`LucideIcons.shoppingCart` icon on top + `"Add to Cart"` text below, without an outlined button container) use `_BottomIconTextAction` separated by a `1x32dp` `#E8EAF0` vertical divider (`product-bottom-chat-divider`), followed by the `Expanded` solid `#1A1851` `Buy Now` button.
   - **White Marketplace Cards (`MarketplaceColors`)**: `MarketplaceColors.cardSurface` and `MarketplaceColors.imageSurface` are now `Colors.white`, turning Marketplace grid cards, Home/Search preview cards, legacy Dashboard product tiles, and `You May Also Like` related cards crisp white.
   - **Removed Quantity Selector**: `_ProductQuantitySelector` and `'Quantity'` were removed from `_ProductInfoContainer`; `BuySelection` passes `quantity: 1` directly to `CartService` and `CheckoutScreen`.
   - **Navy Blue Heart Icons (`#1A1851`)**: Every favorite heart icon in `ProductDetailsScreen`, `_RelatedProductCard`, `MarketplacePreviewCard`, `ProductsScreen`, and `DashboardScreen` uses `const Color(0xFF1A1851)` (Navy Blue), switching between outline (`LucideIcons.heart` / `Icons.favorite_border`) and filled (`Icons.favorite_rounded` / `Icons.favorite`) while remaining strictly within the institutional Navy palette.

4. **How it works — functions, inputs/outputs and data flow:**
   - `MarketplaceColors.cardSurface` (`Colors.white`) and `MarketplaceColors.imageSurface` (`Colors.white`) feed all marketplace card containers and image wrappers, keeping card backgrounds white while `ProductDetailsScreen` uses `Colors.white` for its page/indicator surfaces and scopes `const Color(0xFFF9FDE7)` exclusively to the hero image container inside `_ProductHeroImage`.
   - `_ProductInfoContainer` builds its top stack in the order: `_ProductReviewSummary` → `SizedBox(height: 4)` → `Row(children: [if (badge != null) ...[badge, SizedBox(width: 8)], Expanded(child: Text(name))])` → `SizedBox(height: 4)` → `price`. Wrapping `Text(name)` in `Expanded` guarantees long product names wrap cleanly beside the `[New]` / `[Hot]` badge without horizontal overflow even at `320dp` width and `2.0x` text scale.
   - `_ProductVariantChoices` checks `_isColor(groups[i])` for each saved group. When `true`, it renders `"Colors"` as the heading and renders every option as `_ColorVariantChoice`, which calls `_ColorVariantChoice._lookupColor(option.name)` (matching exact names, `#RRGGBB` hex strings, or individual color tokens like `'red'` in `'RED Cream'`) to paint a circular color swatch without text labels.
   - Tapping the Favorite button triggers `FavoriteService.instance.toggle(_favoriteKey)`. The `ListenableBuilder(listenable: FavoriteService.instance, ...)` rebuilds the button icon between `LucideIcons.heart` (unselected) and `Icons.favorite_rounded` (selected), both rendered in `const Color(0xFF1A1851)`.
   - `_purchaseSelection()` validates required customization groups and returns `BuySelection(quantity: 1, selections: _selections, summary: ..., unitPrice: _unitPrice)`.

5. **Backend / API behavior:** Unchanged.

6. **Database / migration impact:** None.

7. **Tests performed / results:**
   - `dart format` across all modified Dart source and test files completed cleanly.
   - `dart analyze` across all modified Dart files passed with `No issues found!`.
   - `flutter test test/product_details_layout_test.dart test/dashboard_header_test.dart test/product_item_test.dart test/notification_product_page_test.dart test/search_page_test.dart` passed all **40 / 40 tests**, and regenerated the 5 native layout previews (`product-details-entry.png`, `product-details.png`, `product-details-web-variants.png`, `product-details-small-text.png`, `product-details-landscape.png`) in `scratch/product-details-review/`.

8. **Limitations / troubleshooting / safe exercise:**
   - **Limitations:** No running app, phone session, or backend server was launched or restarted (`Ctrl+F5` remains user-controlled).
   - **Troubleshooting:** Initially applying `const Color(0xFFF9FDE7)` to `Scaffold.backgroundColor` and `_ProductHeroImage`'s outer `ColoredBox` tinted the entire Product Details information section and pagination strip cream; restoring `Colors.white` on `Scaffold`, `SliverAppBar`, and the outer `ColoredBox` while keeping `Color(0xFFF9FDE7)` on the inner `DecoratedBox` and `ProductImage` isolated the cream backdrop strictly to the product image area.
   - **Safe practice exercise:** Temporarily change `backgroundColor: const Color(0xFFF9FDE7)` on `ProductImage` in `campushub/lib/module_app/screens/product_details_screen.dart` (line 655) to `Colors.white` and run `C:\flutter\bin\flutter.bat test test/product_details_layout_test.dart`; observe that `titleless gallery header uses circular controls and a readable collapsed surface` catches the changed hero image background color, then restore `const Color(0xFFF9FDE7)` and rerun.

## Modern Product Details Mobile UI (10-section minimalist e-commerce redesign) — October 20, 2026

1. **Cause / reason:** The user provided a complete 10-section specification (`# CampusHub — Modern Product Details Mobile UI`) inspired by the clean iPhone clothing product details reference (`media_1792425416525_592be7c1.jpg`) and invoked `/frontend-design` and `/ui-ux-pro-max`. The redesign replaces the previous titleless cream `#F9FDE7` gallery header and boxed seller/expiry cards with a clean `#FFFFFF` flat minimalist e-commerce layout, a centered `"Product Details"` header, a `#95754F` rounded (`14px`) `BoxFit.contain` image gallery with a bottom-right circular Favorite button and below-image pagination dots, a compact `[−] 1 [+]` quantity selector, a hairline-bordered seller row with right chevron (`>`), a `"See All"` label in `Ratings & Reviews`, a Favorite heart toggle on `You May Also Like` cards, and a two-button (`Add to Cart` + `Buy Now`) fixed bottom action bar.

2. **Exact files changed / current anchors (5 files):**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 91 `_quantity`; 118 `_galleryImages` (`.take(6)`); 233 `_maxQuantity`; 237 `_setQuantity`; 378 `BuySelection(quantity: _quantity)` | Added `_quantity` state and `_maxQuantity` bound (`widget.stock > 0 ? widget.stock : 1`), capped `_galleryImages` at 6 images, and passed `_quantity` into `BuySelection` for both `Add to Cart` and `Buy Now`. |
| Same screen | 476 `Scaffold(backgroundColor: Colors.white)`; 479 `SliverAppBar(centerTitle: true, title: Text('Product Details'))`; 510 `ListenableBuilder` + `_ProductHeroImage`; 624 `_ProductHeroImage.build` | Replaced titleless `FlexibleSpaceBar` header with a minimal white pinned `SliverAppBar` (`Back` on left, `"Product Details"` centered at `17sp/600` `#1A1851`, `Cart` on right) followed by `_ProductHeroImage` (`14dp` rounded `#95754F` container, `BoxFit.contain`, bottom-right `48x48` circular Favorite button, and `24dp` below-image `#1A1851` / `#D0D5DD` pagination strip). |
| Same screen | 871 `_ProductInfoContainer`; 1094 `_ProductQuantitySelector`; 1435 `_DetailLine`; 1485 `_SellerIdentity`; 1598 `_ProductBottomBar`; 1796 `_ProductReviewsSection`; 1861 `_YouMayAlsoLikeSection`; 1919 `_RelatedProductCard` | Updated typography (`22sp/600` name, `26sp/700` price, `16sp/600` headings, `13.5sp` `#667085` body, `12sp` secondary labels), added `_ProductQuantitySelector` (`product-quantity-selector`, `[−] 1 [+]`), restyled `_SellerIdentity` and `_DetailLine` with `1px` `#E8EAF0` hairline borders and right chevron (`LucideIcons.chevronRight` wired to `_openSellerChat`), added `"See All"` (`product-reviews-see-all`) to `_ProductReviewsSection`, added `#95754F` `BoxFit.contain` + top-right circular Favorite heart to `_RelatedProductCard`, and updated `_ProductBottomBar` to two equal-width `48dp` buttons (`Add to Cart` and `Buy Now`). |
| `campushub/test/product_details_layout_test.dart` | 155 header & quantity assertions; 468 quantity increment/decrement + cart test; 642 section vertical spacing (`+ 16dp`) | Updated header assertions for centered `'Product Details'` on `Colors.white` (`header.flexibleSpace == null`), verified `_ProductQuantitySelector` increments/decrements within stock, and verified `options` → `quantity` (`+ 16dp`) → `sellerSection` (`+ 16dp`) → `description` (`+ 16dp`) spacing. |
| `campushub/DESIGN.md` | 55 `components.product-details` | Recorded the 10-section minimalist e-commerce specification, `#FFFFFF` / `#95754F` / `#1A1851` / `#FCB315` / `#667085` / `#E8EAF0` palette, quantity selector, and 2-button bottom bar. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest Modern Product Details Mobile UI (10-section e-commerce redesign)` | Saved current implementation, design tokens, quantity flow, and verification summary. |
| `docs/product-details-status-inventory.md` | this section | Documented cause, functions/data flow, verification results, troubleshooting, and safe exercise. |

3. **Changes made:**
   - **Header (`SliverAppBar`)**: Minimal white pinned header (`56dp` height) with circular `48x48` `Back` button on left (`#E8EAF0` border), `"Product Details"` centered (`17sp` SemiBold `#1A1851`), and circular `48x48` `Cart` button with badge on right.
   - **Product Image Gallery (`_ProductHeroImage`)**: `16dp` horizontal inset, `14dp` rounded `#95754F` container using `BoxFit.contain` to preserve original product aspect ratio without cropping, up to 6 swipeable images (`PageView.builder`), a `48x48` circular Favorite heart button at `Positioned(right: 10, bottom: 10)` wrapped in `ListenableBuilder(listenable: FavoriteService.instance)`, and a `24dp` indicator strip directly **below** the image (`18x6` `#1A1851` active pill, `6x6` `#D0D5DD` inactive dots).
   - **Product Information & Variants**: Conditional `New` (`#1A1851`) or `Hot` (`#FCB315`) badge above `22sp` SemiBold product name, honest review summary (`#D0D5DD` outline stars + `No reviews yet` when unrated, `#FCB315` fractional stars when rated), `26sp` Bold `#1A1851` price with `Roboto` `₱` glyph, and dynamic saved variants (`Colors`, `Size`, `Flavor`, etc.) that update price and hide completely when `customization.hasOptions` is `false`.
   - **Quantity (`_ProductQuantitySelector`)**: Compact horizontal row (`Quantity` label on left, `[−] 1 [+]` pill control on right with `#E8EAF0` border) clamped between `1` and `_maxQuantity` (`widget.stock`), passing `_quantity` into `BuySelection` for cart and checkout.
   - **Seller Information (`_SellerIdentity`)**: Flat horizontal row with `1px` `#E8EAF0` top and bottom hairline borders (`vertical: 12` padding), `36x36` circular seller photo, seller full name (`13.5sp` SemiBold), `Online`/`Offline` dot + label (`12sp` `#667085`), and right chevron (`LucideIcons.chevronRight`) opening seller chat (`_openSellerChat`).
   - **Product Details, Reviews & Recommendations**: Flat `Description` (`16sp` SemiBold heading + `13.5sp` `#667085` body), conditional `Expiry Date` with top `#E8EAF0` hairline, `Ratings & Reviews` header with right-aligned `"See All"` (`12sp` `#667085`) and compact `"No reviews yet"` empty state, and `You May Also Like` horizontal cards (`140dp` wide, `#95754F` `BoxFit.contain` image with top-right `28x28` circular Favorite toggle).
   - **Fixed Bottom Actions (`_ProductBottomBar`)**: Fixed white bottom bar (`1px` `#E8EAF0` top border, `SafeArea`) with two equal-width (`Expanded`), equal-height (`48dp`) buttons (`12dp` radius, `12dp` gap): `Add to Cart` (white background, `#1A1851` outline) and `Buy Now` (solid `#1A1851` background, white text).

4. **How it works — functions, inputs/outputs and data flow:**
   - `_setQuantity(int next)` clamps `next` to `1.._maxQuantity` (`widget.stock > 0 ? widget.stock : 1`) and updates `_quantity` via `setState`.
   - `_buildCurrentSelection()` reads `_selectedOptions`, `_unitPrice`, and `_quantity`, returning a `BuySelection(quantity: _quantity, unitPrice: _unitPrice, selections: selections)` consumed by both `_handleAddToCart()` (`CartService.instance.addOrIncrement`) and `_openBuyOptions()` (`CheckoutScreen`).
   - Annotated example: Opening a product with `stock: 5` and `Size: M (+₱10)` starts at `_quantity = 1` and `₱250`. Selecting `M` updates `_unitPrice` to `260` (`₱260`). Tapping `+` (`Increase quantity`) calls `_setQuantity(2)`, updating `product-quantity-value` to `2`. Tapping `Add to Cart` or `Buy Now` passes `quantity: 2, unitPrice: 260` to `CartService` or `CheckoutScreen`.

5. **Backend / API behavior:** Unchanged. All existing Django product, variant, stock, seller photo, presence, cart, and checkout contracts remain untouched.

6. **Database / migration impact:** None.

7. **Tests performed / results:**
   - `dart format lib/module_app/screens/product_details_screen.dart test/product_details_layout_test.dart` completed with 0 formatting issues.
   - `dart analyze lib/module_app/screens/product_details_screen.dart test/product_details_layout_test.dart` passed with `No issues found!`.
   - `flutter test test/product_details_layout_test.dart test/product_item_test.dart test/notification_product_page_test.dart test/search_page_test.dart` passed all 35 tests (`00:27 +35: All tests passed!`).
   - Five native layout previews (`product-details-entry.png`, `product-details.png`, `product-details-web-variants.png`, `product-details-small-text.png`, `product-details-landscape.png`) were generated and visually verified in `scratch/product-details-review/`.

8. **Limitations / troubleshooting / safe exercise:**
   - **Limitations:** Bundled `Poppins` is retained as the active `AppTypography` font family per `AGENTS.md` Section 3 (`Flutter mobile uses bundled Poppins for UI`) and the existing font test (`all product detail text uses Poppins including owner review status`), while applying the exact requested font sizes (`17sp`, `22sp`, `26sp`, `16sp`, `13.5sp`, `12sp`, `14.5sp`) and weights. No running app, phone session, or server was launched or restarted (`Ctrl+F5` remains user-controlled).
   - **Troubleshooting:** Originally, `_ProductQuantitySelector` passed `tapTargetSize: MaterialTapTargetSize.shrinkWrap` directly to `IconButton`, which failed compilation; moving `tapTargetSize` inside `IconButton.styleFrom(...)` resolved the compiler error. Additionally, wrapping `_ProductHeroImage` in `ListenableBuilder(listenable: FavoriteService.instance, ...)` ensured `isFavorite` and its tooltip (`Remove from favorites` / `Add to favorites`) rebuild immediately when toggled.
   - **Safe practice exercise:** In `campushub/lib/module_app/screens/product_details_screen.dart` at line 668 (`_ProductHeroImage`), temporarily change `color: const Color(0xFF95754F)` to `color: const Color(0xFFF8FAFC)` and run `C:\flutter\bin\flutter.bat test test/product_details_layout_test.dart` with `PRODUCT_DETAILS_REVIEW_DIR` set to inspect how the gallery container background changes in `product-details-entry.png`, then restore `0xFF95754F` and rerun the test suite.

## Pale background `#F9FDE7` — October 20, 2026

1. **Reason:** user requests `#F9FDE7` for Product Details background and mobile marketplace cards, superseding the previous white-body/orange-image palette for these surfaces.
2. **Exact files and anchors:** `campushub/lib/module_app/theme/marketplace_colors.dart:5` sets `cardSurface` to the requested color and line 6 aliases `imageSurface` to it. `campushub/lib/module_app/screens/product_details_screen.dart:462` sets the scaffold surface; line 468 applies the same collapsed header backing; line 638 colors the gallery/indicator strip; lines 647/656 apply its image backing. Existing related cards at 1859/1872 already consume the shared colors. `campushub/test/dashboard_header_test.dart:110–122` updates actual card/image expectations; `campushub/test/product_details_layout_test.dart:161–165` checks the collapsed header and scaffold. `campushub/DESIGN.md` records both surface tokens and current Product Details usage. This guide and `CAMPUSHUB_CONTEXT.md` record the scoped palette choice.
3. **Changes:** pale card bodies and image backings across Marketplace, shared Home/Search previews, legacy Dashboard and related-product cards. Product Details content/gallery backgrounds match. White action controls and existing seller/expiry framing preserve contrast and hierarchy.
4. **How it works:** existing card widgets read `MarketplaceColors.cardSurface`; image wrappers read `imageSurface`. Both now resolve to the same constant, so one palette edit updates all existing consumers. Product Details also reads those tokens for page/gallery surfaces. Existing uploaded image pixels are unchanged; an opaque photo covers its backing naturally. No product data or selection behavior changes.
5. **Backend/API:** unchanged; existing image URLs, product records, variants, prices, stock and seller data remain.
6. **Database/migrations:** none.
7. **Verification:** 37 existing Flutter tests passed across `product_details_layout_test.dart`, `dashboard_header_test.dart`, `search_page_test.dart` and `product_item_test.dart`, including actual surface assertions, variants/cart behavior and narrow/large-text layouts. Four-file Dart analysis reports no issues; formatting reports no changes; scoped whitespace checks passed. Log: `scratch/product-details-review/cream-surface-tests.log`. Restricted SDK commands stalled and were stopped; the checks completed with SDK access. No app/phone/server restart or installation. Existing tests were updated rather than adding an implementation-mirroring suite.
8. **Limitations / safe exercise:** physical-device visual verification is pending. Open Marketplace and Search, then a product detail; check pale card backgrounds and matching page/indicator backing. Try a transparent or missing image to see the backing; a photo with a saved white background retains those actual pixels. If a surface differs, inspect whether its widget consumes the shared token before changing backend image processing.

## Reference-aligned Product Details layout, below-image swiping dots, and compact vertical spacing — October 20, 2026

1. **Cause / reason:** Comparing the live mobile screenshot against the commerce reference and the user's follow-up (`"the swping dot in details move below of the image fixed the spacing because so much space"`) confirmed six visual/layout issues:
   - `_ProductHeroImage` previously overlaid its page indicator dots inside a `Stack` on top of the bottom of the image (`Positioned(bottom: 10)`), and wrapped each dot in a wide `48x48` box.
   - `_ProductHeroImage` used `BoxFit.contain` on `Colors.white`, causing portrait product photos to shrink into a narrow vertical column with blank white side bars.
   - `FilterChip` in `_ProductVariantChoices` defaulted to `MaterialTapTargetSize.padded`, injecting `~16dp` of invisible vertical padding above and below option rows, while `_ProductReviewSummary` had extra vertical padding and `20dp`/`24dp`/`16dp` section spacers created excessive vertical whitespace between sections.
   - Empty rating stars used a washed-out `40%` navy outline (`#1A1851`), making unrated products look disabled.
   - `_SellerIdentity` and `_DetailLine` (`Expiry Date`) floated in bare white space without surface framing, and `_ProductBottomBar` lacked a top border or framed `Chat` control.
   - `_YouMayAlsoLikeSection` centered its title in `#222222` and `_RelatedProductCard` used `#EE4D2D` (off-palette orange-red) for prices instead of institutional navy `#1A1851`.

2. **Exact files changed / current anchors (5 files):**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 473 `expandedHeight`; 635 `_ProductHeroImage.build`; 662 `product-image-indicators`; 730 `_ProductHeaderButton` | Synced `SliverAppBar.expandedHeight` and `_ProductHeroImage` to `clamp(240.0, 340.0)`; replaced `Stack` overlay with a `Column` placing the `#F8FAFC` `BoxFit.cover` `PageView` above a `26dp` below-image indicator strip (`20x6` active pill / `6x6` dot, `horizontal: 4` padding). |
| Same screen | 857 `EdgeInsets.fromLTRB(16, 6, 16, 16)`; 863 `product-listing-badge`; 883 `product-heading-name`; 901 `product-selected-price`; 940–1015 section spacers; 1026 `_ProductDescription`; 1059 `_ProductVariantChoices`; 1255 `_ColorVariantChoice` | Tightened vertical rhythm (`6dp` top inset, `4dp` after badge, `2dp` to review summary, `4dp` to price, `12dp` between price/options/seller/description/reviews/related, `10dp` before status/expiry), set `FilterChip` to `MaterialTapTargetSize.shrinkWrap` + `VisualDensity.compact`, and tightened color swatch targets to `38x38` (`34x34` ring, `28x28` swatch). |
| Same screen | 1349 `_DetailLine`; 1401 `_SellerIdentity`; 1504 `_ProductBottomBar`; 1613 `_ProductReviewSummary`; 1685 `_ProductRatingStars`; 1727 `_ProductReviewsSection`; 1792 `_YouMayAlsoLikeSection`; 1844 `_RelatedProductCard` | Framed `#F8FAFC` seller card and expiry row with `#E2E8F0` borders (`vertical: 8` padding), compact `22dp` min-height review button at `1x` (expanding `>=48dp` at `2x` wrap), gold `#FCB315` star outlines, left-aligned `#1A1851` `You May Also Like` and related cards, and top-bordered bottom action bar (`fromLTRB(16, 10, 16, 10)`) with a `48x48` framed `Chat` button. |
| `campushub/test/product_details_layout_test.dart` | 186 `product-image-indicators` below `PageView`; 208 summary-to-price `+ 4`; 635 options-to-seller `+ 12`; 655 seller-to-description `+ 12` | Assert swiping indicator strip sits below the `PageView` gallery and verify tightened `4dp` / `12dp` / `12dp` vertical section spacing. |
| `campushub/DESIGN.md` | 55 `components.product-details` | Record below-image indicator strip, `340dp` capped header height, shrink-wrapped chips, and tightened vertical rhythm. |
| `CAMPUSHUB_CONTEXT.md` | 5 `Latest reference-aligned Product Details visual craft` | Save current implementation, below-image dot placement, tightened spacing, and verification notes. |
| `docs/product-details-status-inventory.md` | this section | Document cause, functions/data flow, verification results, troubleshooting, and safe exercise. |

3. **Changes made:** All existing texts, reading order (`badge` → `name` → `reviews` → `price` → `saved options` → `seller` → `Description` → `Expiry Date` → `Ratings & Reviews` → `You May Also Like`), widget keys, and business logic are preserved unchanged. `_ProductHeroImage` now uses a `Column` with an `Expanded` `#F8FAFC` `PageView.builder` (`BoxFit.cover` + `1px` `#E2E8F0` bottom border) followed by a `26dp` `SizedBox(key: ValueKey('product-image-indicators'))` strip directly **below** the image, so the swiping indicator dots sit outside the photo and never overlap the product or leave a tall gap. `_ProductInfoContainer` and its child sections use compact vertical gaps (`6dp` top padding, `4dp` badge-to-name, `2dp` name-to-reviews, `4dp` reviews-to-price, `12dp` between price, saved options, seller card, description, reviews, and related products) and `FilterChip` uses `MaterialTapTargetSize.shrinkWrap` with `VisualDensity.compact` to eliminate hidden vertical padding above and below option rows.

4. **How it works / functions, inputs, outputs and data flow:**
   - `ProductDetailsScreen` receives the same `ProductItem` fields (`name`, `priceLabel`, `imageUrl`, `images`, `seller`, `sellerPhotoUrl`, `rating`, `reviewsCount`, `expiryDate`, `customization`, `ownerView`) and computes `_galleryImages`, `_unitPrice`, and `_formatPriceDisplay()`.
   - `_ProductHeroImage(images, currentIndex, controller, onPageChanged, onImageSelected)` renders inside a `ColoredBox(color: Colors.white)` with `height: MediaQuery.sizeOf(context).width.clamp(240.0, 340.0)` matching `SliverAppBar.expandedHeight`. Its `Column` places the `Expanded` `#F8FAFC` `PageView.builder` on top and the `26dp` `product-image-indicators` strip underneath. Tapping an indicator calls `onImageSelected(index)` (`_selectImage`), animating `_imagePageController` to that page; swiping the `PageView` calls `onPageChanged` (`_onImagePageChanged`), updating `_currentImageIndex` so the active `20x6` navy pill moves in sync.
   - `_ProductInfoContainer` receives the formatted price, rating, customization groups, and seller state. It renders `_ProductReviewSummary` (`minimumSize: const Size(48, 22)`, `tapTargetSize: MaterialTapTargetSize.shrinkWrap`, `padding: EdgeInsets.symmetric(vertical: 2)`) and `_ProductVariantChoices` (`MaterialTapTargetSize.shrinkWrap`, `VisualDensity.compact`) so neither widget injects invisible vertical padding around its visual border.
   - Annotated example: Opening a product with options (`customization.hasOptions == true`) renders the `#F8FAFC` hero photo → `26dp` indicator strip below the photo → `6dp` top inset → `New` badge → `4dp` → `Campus Shirt` → `2dp` → `_ProductReviewSummary` → `4dp` → `₱250` → `12dp` → `_ProductVariantChoices` → `12dp` → `#F8FAFC` `_SellerIdentity` card → `12dp` → `_ProductDescription` → `12dp` → `_ProductReviewsSection` → `12dp` → `_YouMayAlsoLikeSection`.

5. **Backend / API behavior:** Unchanged. No endpoints, serializers, models, or payloads were modified.

6. **Database / migration impact:** None.

7. **Tests performed / results:**
   - `dart format lib/module_app/screens/product_details_screen.dart test/product_details_layout_test.dart` completed cleanly.
   - `dart analyze lib/module_app/screens/product_details_screen.dart test/product_details_layout_test.dart` passed with `No issues found!`.
   - `flutter test --no-pub test/product_details_layout_test.dart test/product_item_test.dart` passed all 23 tests (21 widget/layout tests including the new below-image indicator assertion and updated `4dp` / `12dp` / `12dp` spacing checks + 2 model tests).
   - Native preview captures (`product-details-entry.png`, `product-details.png`, `product-details-web-variants.png`, `product-details-small-text.png`, `product-details-landscape.png`) were generated with bundled `Poppins` and `Roboto` currency fonts in `scratch/product-details-review/` and visually inspected to confirm the indicator pill sits cleanly below the hero image and the excessive vertical gaps are gone.

8. **Limitations / troubleshooting / safe exercise:**
   - **Limitations:** No running app, phone session, backend server, or worker was launched, reloaded, or restarted (preserving the user's `Ctrl+F5` workflow). Physical device visual confirmation awaits the user's next hot reload/run. Because `_ProductHeroImage` uses `BoxFit.cover` to eliminate portrait side bars, very tall portrait photos crop slightly at the top/bottom edges to fill the hero stage cleanly.
   - **Troubleshooting:** If a vertical gap ever reappears between the hero indicator strip and the `New` badge or product title, verify that `SliverAppBar.expandedHeight` (line 473) and `_ProductHeroImage`'s outer `SizedBox.height` (line 640) use the exact same `clamp(240.0, 340.0)` formula.
   - **Safe practice exercise:** In `campushub/lib/module_app/screens/product_details_screen.dart` at line 962 (inside `_ProductInfoContainer`), temporarily change `const SizedBox(height: 12)` above `_SellerIdentity` to `const SizedBox(height: 16)`, then run `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart` from `campushub`. Observe that the `price follows reviews and saved options precede seller above description` test catches the `4dp` offset (`expected 12, actual 16`), then restore `const SizedBox(height: 12)` and rerun to confirm all 21 tests pass.

## Gradient revert — October 19, 2026

The latest experimental gradient was reverted at the user's request. The eight affected files are `campushub/lib/module_app/theme/marketplace_colors.dart` (line 6, `imageSurface`), `widgets/product_image.dart` (line 60, `build`), `widgets/home/home_preview_cards.dart` (line 207, image background), `screens/products_screen.dart` (line 534), `screens/dashboard_screen.dart` (line 1060), `screens/product_details_screen.dart` (line 1817), and the existing `campushub/test/dashboard_header_test.dart` (line 119) and `product_image_memory_test.dart` (line 92). Widget/screen paths are under `campushub/lib/module_app/`.

Removed the gradient token and widget parameter; restored solid `imageSurface` backgrounds and the original fallback assertions. The shared color flows into existing card image wrappers; URL resolution, bounded image decoding and white card bodies remain. No backend/API, database or migration change. Dart formatting completed for all eight files. The attempted test run was interrupted and its log is empty, so no new test pass is claimed. Safe practice: inspect a product with a transparent image or missing-image fallback in Marketplace and Search; its backing should be solid `#FFD4A5`, with a white text area. Opaque image pixels naturally cover this backing. Device visual verification remains pending.

## Current light-gold image backgrounds with white card bodies — October 19, 2026

1. **Cause / reason:** the user clarifies that the color belongs behind product images, rather than across the entire card. The supplied `ffd4a5a` is seven hex digits; the assistant explicitly stated the interpretation `#FFD4A5` (remove the extra final a). This supersedes the earlier full-card orange treatment and keeps the marketplace text area white.

2. **Exact files changed / current anchors (9 files):**

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/theme/marketplace_colors.dart` | 5 `cardSurface`; 6 `imageSurface` | White card body plus shared light-gold `#FFD4A5` image backing. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 186 card; 207 image | Existing Home/Search product previews split body/image surfaces. |
| `campushub/lib/module_app/screens/products_screen.dart` | 507 card; 534 image | Existing Marketplace grid image wrapper uses imageSurface. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 1033 card; 1060 image | Same split for the existing legacy product tile. |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 1805 related card; 1817 related image | White related-card body and light-gold image backing. |
| `campushub/test/dashboard_header_test.dart` | 110 white body assertion; 119 image background assertion | Test the actual production preview widget's separate surfaces. |
| `campushub/DESIGN.md` | `colors.marketplace-card-surface`, `.marketplace-image-surface`; `components.product-details.related-products` | Record the clarified surface roles. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest light-gold product-image backing only` | Save interpretation, implementation and verification. |
| `docs/product-details-status-inventory.md` | this section | Current cause, functions/data flow, tests and safe exercise. |

3. **Changes made:** marketplace product-card bodies/text areas are white again; their image backings use `#FFD4A5`. This applies to existing Marketplace, Home/Search/shared previews, the legacy Dashboard tile and related-product cards. The main Product Details gallery and seller avatar keep their existing treatments. The recently requested name→reviews→price→options→seller→Description order and adjacent score remain unchanged.

4. **How it works / inputs, outputs and data flow:** `MarketplaceColors.cardSurface` and `imageSurface` are presentation-only Color constants. Existing product data still feeds the same card widgets. The card's BoxDecoration reads the white token; its ProductImage background or existing image-wrapper Container reads the gold token. ProductImage keeps the same image URL/loading/error behavior. No data/controller duplication, extra API call or image conversion is introduced.

   Annotated example: Home/Search product → MarketplacePreviewCard → white card decoration + ProductImage(backgroundColor:imageSurface). A transparent or missing image reveals the light-gold backing. An opaque uploaded photo remains the same photo; painting behind it does not recolor pixels embedded in the file.

5. **Backend / API behavior:** unchanged catalog, image URLs, seller ownership, pricing, inventory, favorites/cart, navigation and rating-summary behavior. This update only changes local Flutter surface colors.

6. **Database / migration impact:** none. No records, models, migrations, dependencies, settings or backups changed.

7. **Tests performed / results:**14 Flutter tests passed in `dashboard_header_test.dart` and `search_page_test.dart`. The existing production-card test now asserts both a white body and `#FFD4A5` image backing across normal-text widths; large-text layout and Search loading/error/retry/query/results/navigation checks remain covered. Six changed source/test files passed scoped analysis with no issues. Dart formatting and whitespace checks passed. Logs: `scratch/product-details-review/image-background-tests.log` and `analyze.log`. No new duplicate test card or fabricated live data was created.

8. **Limitations / troubleshooting / safe exercise:** no app, phone, server or worker was launched/restarted, built or installed. Physical-device verification is pending. Original photo backgrounds are preserved; image backing cannot make an opaque white image transparent. If the intended color differs from the stated `#FFD4A5` interpretation, change the one imageSurface token rather than editing every card.

   Safe practice: temporarily change only `imageSurface` to another pale gold and run `C:\flutter\bin\flutter.bat test --no-pub test/dashboard_header_test.dart` from `campushub`. The image-color expectation should fail while the white-body expectation still passes. Restore `#FFD4A5` and rerun to verify the separate roles. No live data changes are needed.

## Current reference-inspired order: reviews, price, options, seller, description — October 19, 2026

1. **Cause / reason:** the user supplies a compact product-page reference and asks to move the price below reviews and the seller above Description. The old order placed seller metadata between reviews and price. This update changes reading order and spacing within the existing design; it keeps the actual photo/status and current product workflows.

2. **Exact files changed / current anchors (5 files):**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 893 reviews/price gap; 912 `product-selected-price`; 954 seller separation; 956 `product-seller-section`; 962 `_ProductDescription` | Price directly after reviews; seller row after actual options and directly above Description. |
| Same screen | 1371 `_SellerIdentity` | Accept the normal widget key used to verify whole-row spacing without changing identity or presence logic. |
| `campushub/test/product_details_layout_test.dart` | 209 reviews→price spacing; 595 reordered hierarchy test; 629 options→seller; 650 seller→description | Verify exact spacing and final order at375dp and320dp/2x text, preserving existing functional tests. |
| `campushub/DESIGN.md` | `components.product-details.heading` | Save final order and4/8/16/20/24dp spacing rhythm. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest reference-inspired Product Details order and spacing` | Save the current correction and verification. |
| `docs/product-details-status-inventory.md` | this section | Current cause, functions/data flow, checks, limitations and exercise. |

3. **Changes made:** the content now reads product name → reviews → price → saved options → seller → Description. The score remains8dp after the last star. The gap after the review control is8dp, before configured options20dp, before the seller24dp, and between seller and Description16dp. The seller's actual circular photo, name and lower Online/Offline line are kept together. When no saved options exist, price is followed by the seller with24dp separation. The reference informs the compact spacing, while the current colors, fonts and functional purchase buttons are retained.

4. **How it works / functions, inputs and outputs:** `_ProductInfoContainer` receives the same computed price, validated rating/count, saved customization groups and actual seller photo/name/presence values. Only the order of its Column children and SizedBox spacing changes. `_SellerIdentity(name, photoUrl, online)` still produces the same identity row; its optional key lets tests measure the entire row, including its photo and status, instead of just the first text line. No second seller widget or data fetch was introduced.

   Annotated example: selecting an existing Size M option still flows `_toggleOption` → `_unitPrice` → formatted selected price → Cart/Checkout with the same saved group/option and quantity1. That price is now positioned immediately below the same working review summary. The existing seller data is rendered once, after the choices and16dp above Description. Empty options remain hidden, and the full description remains expanded as previously requested.

5. **Backend / API behavior:** unchanged product data, seller-photo/presence source, rating/count validation, review-section jump, required-option checks, stock, permissions and cart/checkout payloads. Review submission/storage remains outside the user's previously confirmed summary-only scope; absent real ratings still show `No reviews yet`.

6. **Database / migration impact:** none. No model, migration, dependency, record, backup or connection change.

7. **Tests performed / results:**26 focused Flutter tests passed in product-details layout, notification-product and ProductItem suites. Updated layout assertions verify reviews→price8dp, options→seller24dp and seller→Description16dp at375dp and320dp/2x text. Existing fractional rating, accessible review jump, avatar fallback/status, saved color/text options, option-image gallery selection, required/single/multiple selections, cart/checkout pricing, no-options flow and owner restrictions remain covered. Scoped analysis of the screen and layout test reported no issues; formatting and whitespace checks passed.

   Five native actual-font previews were inspected in one batch: entry, scrolled detail,320dp/2x text, landscape and saved color/size fixture. Checks covered the name/review/price hierarchy, choice arrangement and selection, seller placement/photo/status, Description separation and fixed purchase actions with scrolling. These are isolated mock-backed native renders, not phone screenshots or live product edits. Current logs and PNGs are in `scratch/product-details-review/`.

8. **Limitations / troubleshooting / safe exercise:** no app/phone/server/worker was launched/restarted, built or installed; physical-device verification remains pending. Small landscape screens still require normal vertical scrolling. The image reference's quantity stepper is not added because the user previously removed purchase quantity; the existing quantity-one behavior stays intact.

   Safe practice: temporarily change only the seller→Description gap from16 to20 in `_ProductInfoContainer`, then run `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart` from `campushub`. The geometry assertion should identify the changed gap. Restore16 and rerun; confirm the seller remains above Description with no product data changes. This demonstrates how Column order and spacing map directly to the measured UI.

## Current light-orange marketplace cards and adjacent rating — October 19, 2026

1. **Cause / reason:** marketplace product cards used separate white/gray backgrounds, and the product review score was pushed to the far right by WrapAlignment.spaceBetween. The user explicitly requests light orange for mobile marketplace cards and the score immediately after the last star. This is a scoped color override from the user's current request.

2. **Exact files changed / current anchors (10 files):**

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/theme/marketplace_colors.dart` | 4 `MarketplaceColors`; 5 `cardSurface` | Shared light-orange product-card surface `#FFF3E6`. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 186 card; 207 image backing | Apply shared color to actual Home/Search/shared preview cards. |
| `campushub/lib/module_app/screens/products_screen.dart` | 507 card; 534 image backing | Apply same surface to Marketplace grid cards. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 1033 card; 1060 image backing | Keep the existing legacy product tile consistent. |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 1592 WrapAlignment.start; 1594 spacing8; 1803 related card; 1815 related image | Score follows the stars; related product cards reuse the same orange token. |
| `campushub/test/product_details_layout_test.dart` | 213 `closeTo(...stars... + 8)` | Verify actual rating sits8dp after the star group, while preserving tap/data tests. |
| `campushub/test/dashboard_header_test.dart` | 101 `productCard`; 111 expected surface | Verify production preview-card color at normal text across tested widths. |
| `campushub/DESIGN.md` | `colors.marketplace-card-surface`; `components.product-details.reviews`, `.related-products` | Record scoped surface and adjacent-score rule. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest light-orange mobile marketplace cards` | Save current request, implementation and checks. |
| `docs/product-details-status-inventory.md` | this section | Current functions/data flow, results and safe exercise. |

3. **Changes made:** product-card and image backings now use pale orange `#FFF3E6` in mobile Marketplace, Home/Search previews, the existing Dashboard tile and related products. Related cards have the same rounded surface with8dp content padding. Actual uploaded image pixels are preserved. The rating summary remains one48dp accessible action, but its score/count now follows the fifth star with an8dp gap rather than occupying the far-right edge. Narrow/large-text wrapping remains available.

4. **How it works / functions and data flow:** `MarketplaceColors.cardSurface` is a presentation-only Color constant. Existing product data → existing card widget → BoxDecoration/ProductImage background using that token; no new product model, fetch or controller is involved. `_ProductReviewSummary(rating, reviewsCount, onTap)` still receives the existing validated aggregate. Its Wrap alignment is start and its spacing is8, so `five stars → 8dp → actual score/count` stays a compact group; when content no longer fits, Wrap can put the label on the next line. All validation, fractional fill and scroll-to-reviews behavior remain as documented below.

   Annotated example: an actual supplied4.8 with12 reviews still appears as `4.8 (12)`; only its position changes. Missing rating data continues to show empty stars followed by `No reviews yet`, never an invented score.

5. **Backend / API behavior:** unchanged. Same catalog sources, ownership, search, favorites, quick-add, navigation and review-summary-only scope. No new requests or writes. Current Django still has no marketplace review storage/API, so live products remain honestly unrated until real aggregate data exists.

6. **Database / migration impact:** none. No database records, models, migrations, dependencies, backup or connection settings were changed.

7. **Tests performed / results:**40 Flutter tests passed across product-details layout, dashboard header, Search, notification-product and ProductItem suites. Assertions cover real preview-card decoration at multiple normal-text widths, exact8dp rating adjacency, missing/invalid scores, review jump, responsive text, seller photo, saved choices, cart/checkout and search/navigation regressions. At320dp/2x, the existing header viewport has lazy product cards below the fold: the color assertion is intentionally limited to normal-text cases, while the large-text header/layout checks still run. An initial test tried to locate that offscreen unbuilt card and failed; the targeted guard fixed the test, and the final full run passed. Seven changed source/test files passed scoped analysis with no issues; formatting/whitespace checks passed. Product Details native preview was inspected to confirm the rating/empty label is beside the final star. Logs and existing headless captures remain under `scratch/product-details-review/`.

8. **Limitations / troubleshooting / safe exercise:** no app, phone, server or worker was launched/restarted, built or installed; physical-device verification is pending. Photos with opaque white backgrounds retain those original white pixels; card backing color does not recolor the actual photograph. This update styles mobile marketplace product cards; it introduces no new review or sales data.

   Safe practice: temporarily change only `MarketplaceColors.cardSurface` to another pale orange and rerun `C:\flutter\bin\flutter.bat test --no-pub test/dashboard_header_test.dart`. The explicit color expectation should fail, showing that the test checks the production card rather than a duplicate test-only layout. Restore `#FFF3E6` and rerun to verify the expected surface. Do not change live catalog records for this exercise.

## Current functional review summary and spacing — October 19, 2026

1. **Cause / reason and agreed scope:** the user requests five stars below the product name, numeric rating on the right, and better spacing. Inspection confirmed ProductItem already parses optional `rating`/`reviewsCount`, but ProductDetails did not receive them; its lower review block was an empty static list with an unsupported invitation to post a review. Django has no marketplace review storage/API (its existing feedback rating belongs to facilities). The user explicitly selected **Working summary only**; building buyer-review submission/storage is outside this update.

2. **Exact files changed / current anchors (10 files):**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 41 constructor rating/count; 91 `_reviewsKey`; 226 related opener; 438 `reviewRating` | Receive existing values, reject invalid aggregate data and preserve them between related products. |
| Same screen | 564 rating props; 567 `onShowReviews`; 889 summary | Share aggregate values with both sections and scroll to the existing review destination. |
| Same screen | 1552 `_ProductReviewSummary`; 1623 `_ProductRatingStars`; 1665 `_ProductReviewsSection` | Five fractional stars, numeric score/count, accessible tap action, honest empty state and shared aggregate; remove dead static review data/tiles. |
| `campushub/lib/module_app/screens/products_screen.dart` | 176 `rating: product.rating` | Forward existing aggregate from Marketplace products. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 1000 `rating: product.rating` | Forward it through the existing Dashboard opener. |
| `campushub/lib/module_app/screens/notification_product_page.dart` | 122 `rating: product.rating` | Retain aggregate when opening owned review notifications. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 144 `rating: product.rating` | Forward it from the shared Home/Search opener. |
| `campushub/test/product_details_layout_test.dart` | 191 supplied average/jump; 249 invalid values; 297 narrow reflow | Test actual function, fractional fill, accessibility and responsive geometry using isolated fixtures. |
| `campushub/test/notification_product_page_test.dart` | 61 `screen.rating`; 62 `screen.reviewsCount` | Confirm the existing route preserves both fields. |
| `campushub/DESIGN.md` | `components.product-details.heading`, `.reviews` | Save current grouping, typography and review action rules. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest functional Product Details rating summary` | Save user-confirmed scope and checks. |
| `docs/product-details-status-inventory.md` | this section | Explain functions, data flow, tests, limits and safe exercise. |

3. **Changes made / UX rules applied:** proximity places the review summary directly with the product name, then separates the seller/payment/options groups. The existing spacing scale is retained:4dp after the name,12dp before seller and before price,20dp before saved options and24dp between lower content sections. Fitts's law informs the single48dp-minimum summary target: the five16dp stars are decorative output within one action, not five tiny buttons. Familiar five-star notation keeps the interaction recognizable, and a textual numeric average/count prevents color alone from carrying the information. Wrap preserves reading order at narrow widths and large text without horizontal scrolling. Existing seller avatar/name/Online Offline, actual saved variants, full description, cart/checkout and owner restrictions are retained.

4. **How it works — functions, inputs/outputs and data flow:** existing API JSON → `ProductItem.fromJson` optional rating/count → existing product opener → `ProductDetailsScreen(rating, reviewsCount)` → one validated `reviewRating` → summary and lower review section. Valid means finite, greater than0, no greater than5, with positive review count; anything else becomes an unrated state. Validation does not manufacture a score or clamp an invalid6 into5.

   `_ProductReviewSummary(rating, reviewsCount, onTap)` produces five stars at left and the supplied one-decimal rating/count at right, or empty stars plus `No reviews yet`. `_ProductRatingStars` calculates each fill as `(rating - starIndex).clamp(0,1)`, so a genuine4.8 is four full stars and an80%-filled fifth star, not a perfect five. The whole control has a screen-reader label, button role and tap action. `onShowReviews` uses `_reviewsKey` and `Scrollable.ensureVisible` to bring the Ratings & Reviews heading into view; movement takes250ms, or no animation with the system reduced-motion preference.

   `_ProductReviewsSection` receives the same validated aggregate. It displays `No reviews yet` when absent. If a genuine aggregate is supplied but individual records are unavailable, it displays the aggregate and says individual reviews are not available yet. It does not invent authors/comments or offer an unwired posting button. The old private empty review list/data/tile classes were removed.

   Annotated example **only in isolated tests**: JSON `rating:4.8,reviews_count:12` → visible `4.8 (12)` → tap → lower `4.8 / 5 (12 reviews)`. An actual response with no rating stays unrated. Nothing is written to Django by this control.

5. **Backend / API behavior:** unchanged. The existing optional mobile fields are wired through; no new endpoint, review service/controller, serializer score, review submission or storage was introduced. Current Django marketplace responses have no genuine review source, so the normal live catalog shows empty stars and `No reviews yet`. Facility feedback is not reused as product feedback. This is the user's confirmed summary-only scope, not a claim that buyer reviews are implemented.

6. **Database / migration impact:** none. No model, migration, dependency, database record, connection or background worker changed. No backend tests were needed for this frontend-only update; existing backend photo support is untouched.

7. **Tests performed / results:**26 focused Flutter tests passed across `product_details_layout_test.dart`, `notification_product_page_test.dart` and `product_item_test.dart`. New cases verify supplied rating/count placement below name,80% last-star fill, accessible tap semantics, jump to a visible lower heading, consistent lower aggregate, honest missing/zero-count/negative/out-of-range/NaN/infinite states and320dp/2x reflow with a long name/large count. The existing routes, seller photo/presence, variants, cart/checkout pricing and owner guards still pass. Seven changed source/test files passed scoped analysis with no issues; Dart formatting and whitespace checks passed. The first accessibility test exposed that the semantic label belonged to a different node from the button; the final summary has one explicit labeled button node/tap action, and the final full focused run passed.

   Independent source layout assessment and local mechanical scans were completed; before/after `--scope layout` scans returned empty finding lists. Five existing actual-font native previews were inspected in one batch (initial/scrolled portrait,320dp2x,landscape,saved color/size): summary placement/grouping, seller/price hierarchy, section rhythm, empty state, wrapping and bottom actions. These are mock-backed native renders, not emulator/device sessions or real review records. Evidence remains in `scratch/product-details-review/`: `tests.log`, `analyze.log`, `layout-scan-before.json`, `layout-scan-after.json` and the current PNGs.

8. **Limitations / troubleshooting / safe exercise:** buyer-review submission, storage and individual-review APIs remain outside confirmed scope. No app/phone/server/worker was launched/restarted, built or installed. Physical-device verification remains pending. To debug a missing score, inspect the existing response for both a valid rating and positive review count; do not hard-code a fallback4.8 or borrow facility feedback.

   Safe practice: change the isolated rating fixture in the test from4.8 to3.5 and its count from12 to1. Update that fixture's assertions to `3.5 (1)` and a50%-filled fourth star, then run `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart`. Confirm the summary, accessible label and lower section agree, then restore the fixture. This demonstrates how one source value reaches the screen and tap destination without creating live reviews.

## Current seller photo and status beneath name — October 19, 2026

1. **Cause / reason:** the user requests a seller photo beside the name and visible Online/Offline underneath. Inspection confirmed Product Details only displayed a name and dot, while its existing product response/model did not carry the seller's saved profile photo. Mobile owners already have `profile_photo`; the current web User model does not. This update uses the real owner and keeps an honest fallback rather than substituting the browsing user's photo.

2. **Exact files changed / current anchors (13 files):**

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/api/views.py` | 214 `serialize_product`; 242 `seller_photo_url` | Add actual owner's saved profile-photo URL or an empty string to the existing response. |
| `backend/core/api/test_mobile_seller_application.py` | 132 `test_public_products_use_actual_owner_profile_photo_or_empty_fallback` | Test public response photo/owner mapping and web empty fallback in an isolated test database. |
| `campushub/lib/module_app/models/product_item.dart` | 18 `sellerPhotoUrl`; 86 JSON parsing; 115 field | Carry optional saved seller photo; older responses default to empty. |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 32 constructor; 212 related-product route; 541 info props; 1316 `_SellerIdentity` | Forward actual photo, show36dp circular avatar, name and lower status line. |
| `campushub/lib/module_app/screens/products_screen.dart` | 167 `sellerPhotoUrl` | Forward photo from Marketplace results. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 991 `sellerPhotoUrl` | Forward photo through the existing Dashboard route. |
| `campushub/lib/module_app/screens/notification_product_page.dart` | 113 `sellerPhotoUrl` | Preserve owner photo when opening product review notifications. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 135 `sellerPhotoUrl` | Forward photo through the shared Home/Search product opener. |
| `campushub/test/product_details_layout_test.dart` | `seller photo, name and lower status`; `seller avatar uses saved photo` | Verify picture/fallbacks, lower visible status and responsive identity geometry. |
| `campushub/test/product_item_test.dart` | 24 empty default; 34 saved photo fixture; 58 parsed URL | Verify both backward compatibility and saved URL parsing. |
| `campushub/DESIGN.md` | `components.product-details.heading`, `.data` | Record current identity hierarchy and data source. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest seller photo and visible lower presence line` | Preserve the latest implementation and checks. |
| `docs/product-details-status-inventory.md` | this section | Current cause, behavior, data flow, verification and exercise. |

3. **Changes made:** below the product name, a36dp circular photo appears to the left of the actual seller's name. Online or Offline is displayed below that name, beside the existing small status dot. The photo has an accessible image label, and status is readable text so color is not the only indicator. Missing, invalid or unreachable photos use the reused ProductImage person-icon fallback. Price and configured options remain below this row.

4. **How it works — inputs/outputs/functions/data flow:** `serialize_product(product, request, include_inventory)` reads the existing `product.owner` abstraction, which resolves the mobile or web owner. `getattr(owner, 'profile_photo', None)` reads only an existing photo field; a nonempty saved field returns its storage URL, otherwise the new JSON field is `''`. No photo is uploaded or copied during product reads.

   `ProductItem.fromJson` accepts `seller_photo_url` and produces `sellerPhotoUrl`. Every existing ProductDetails opener forwards the value to `_ProductInfoContainer` and `_SellerIdentity(name, photoUrl, online)`. The latter passes photoUrl to the existing ProductImage widget inside ClipOval. ProductImage already resolves relative `/media/` paths against the mobile API host and handles invalid images, so no second downloader/cache or photo system was introduced. Existing `_refreshSellerPresence` and15-second polling supply `online`; the widget uses it for both Online/Offline text and the dot.

   Annotated example: backend `seller_photo_url: /media/profile-photos/actual-owner.jpg` → ProductItem.sellerPhotoUrl → existing product route → ProductImage → circular seller image. An empty old response becomes a person placeholder. The photo and seller name always belong to product.owner, never the shopper's account.

5. **Backend / API behavior:** additive `seller_photo_url` in the existing serializer used for public and owned products; no new route, auth flow or controller. Existing seller identities/names, presence API, permissions, approval, inventory and purchases remain unchanged. No profile field is added to web accounts: they correctly return an empty photo URL until a saved photo feature exists for that account model.

6. **Database / migration impact:** no schema/model/dependency change or migration is needed. No live data was edited. Backend validation ran in the explicitly named `test_campushub_seller_photo` database, never the live catalog; the saved photo path was a test string, with no real file upload.

7. **Tests performed / results:**23 Flutter tests passed across `product_details_layout_test.dart`, `notification_product_page_test.dart` and `product_item_test.dart`. New coverage checks saved/missing/invalid avatar sources and fallback behavior,36dp image size, visible Offline beneath the smaller seller name, price below status and parser defaults. Existing gallery, saved variant selection, two-column responsiveness, cart/checkout and owner guards still pass. Two targeted Django tests passed: public real-owner photo/web empty fallback and the existing mobile product ownership/inventory workflow. Django system checks reported no issues; scoped Dart analysis across all eight changed source/test files reported no issues. Formatting and whitespace checks were clean. Native entry, saved color/size and320dp2x previews were inspected; logs/captures remain in `scratch/product-details-review/`, including `seller-photo-django.log`, `tests.log` and `analyze.log`.

8. **Limitations / troubleshooting / safe exercise:** the app, phone, backend and worker were not restarted, launched, built or installed. Phone verification remains pending. An old cached response or an account without a saved photo shows the placeholder; reload the current product data after the backend code is available through the user's normal development workflow. The existing presence service still treats failed checks as Offline; this update preserves that behavior and does not invent Online results. Native previews use isolated fixtures, not live records.

   Safe practice: add `seller_photo_url: ''` to `productRow()` in the layout test and confirm the person fallback, then use the existing tiny GIF data URL from the avatar test to verify a saved image is rendered. Run `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart test/product_item_test.dart` from `campushub`, inspect the new avatar test and restore your fixture. This teaches the response→model→route→widget path without editing real users or uploading files.

## Current bold peso and conditional option columns — October 19, 2026

1. **Cause / reason:** the user now requests the peso symbol at the same size/weight as the price, removal of the generic Variants heading, left/right layout for two configured groups, and no option section for products without admin/seller-created variants. This supersedes the lighter-peso styling and no-options message described below.

2. **Exact files changed / current anchors:**

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 858 `product-selected-price`; 880 `product-variant-choices` | Peso matches the amount23sp/600; mount saved choices only when customization.hasOptions is true; remove generic heading and empty-options message. |
| Same screen | 982 `_ProductVariantChoices`; 1000 `sideBySide`; 1004 `groupWidth` | Exactly two groups use equal left/right columns with20dp gap when readable; narrow screens/large text stack them. |
| `campushub/test/product_details_layout_test.dart` | 425 no-saved-variants; 458 heading/price order; 517 two-saved-groups | Verify hidden absent options, matching peso styling, two-column/stacked geometry and unchanged checkout selections. |
| `campushub/DESIGN.md` | `components.product-details.typography`, `.choices`, `.empty-variants` | Update current visual and visibility rules. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest bold peso and conditional side-by-side saved options` | Save the current request and verification. |
| `docs/product-details-status-inventory.md` | this section | Current cause, functions/data flow, checks and safe exercise. |

3. **Changes made:** price remains below the seller and uses the existing computed amount. The Roboto peso glyph now matches the Poppins numerals'23sp size and600 weight. The generic Variants label and `No variants available.` message were removed. Saved group labels, such as Colors or Size, remain. Two groups share one horizontal row when each has enough space; other cases use a full-width vertical layout. No fake controls or saved data were added.

4. **How it works — functions, inputs/outputs and data flow:** `_ProductInfoContainer(customization, priceText, selectedOptions, ...)` uses the existing `customization.hasOptions` getter to decide whether to build the option area at all. The getter reflects enabled saved configuration from the existing ProductItem/customization parser. `_ProductVariantChoices(groups, selectedOptions, onSelected)` receives those saved groups and uses LayoutBuilder's available width plus the system text scaler. Exactly two groups with at least320dp content width and13sp text scaling to no more than18dp receive `(availableWidth - 20) / 2` each; otherwise each receives the full width. Wrap lets options flow inside each group. Inputs and callback names remain the original saved names.

   Annotated example: a375dp screen has343dp after its16dp side paddings. Saved Colors and Size therefore each get161.5dp with a20dp gap. At320dp/2x text they stack instead. Selecting saved `Color:Navy` and `Size:L` still feeds `_toggleOption` → `_unitPrice`/`_selections` → quantity-one Cart/Checkout → Django validation. Layout never creates additional variants or changes prices.

5. **Backend / API behavior:** unchanged APIs, serializer, permissions, option classification, required-option checks, inventory rules and cart/checkout payloads. The app displays only the configured saved groups from the existing backend response. No separate admin/seller source or new controller is required.

6. **Database / migration impact:** none. No records, models, migrations, dependencies or connection settings changed.

7. **Tests performed / results:**22 focused Flutter tests passed across `product_details_layout_test.dart`, `notification_product_page_test.dart` and `product_item_test.dart`. New geometry coverage checks left/right groups at375dp and stacked groups at320dp/2x text; both preserve actual Color/Size selections through checkout. Existing no-saved-options coverage now checks complete hiding and still verifies add/buy with empty selections. Price tests assert symbol/amount size and weight match. Existing header, full description, saved group classification, gallery, cart and owner restrictions remain covered. Native entry, saved-web color/size and320dp/2x previews were inspected; formatting and scoped analysis are recorded in `scratch/product-details-review/` alongside final tests/analyzer logs.

8. **Limitations / troubleshooting / safe exercise:** no app, phone, server or worker was launched/restarted, built or installed. Physical-device checking is pending. Stacking on narrow screens/large text is intentional to preserve readable controls. Only exactly two saved groups use two columns; one or three-plus groups stay full width. If choices are missing, inspect the actual product's enabled customization and saved groups through the existing admin/seller editor, then reload/reopen the product; the UI does not synthesize missing choices.

   Safe practice: in the isolated `variantSampleRow()` test fixture, rename Size to Fit and update that test's group keys/payload expectations; run `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart` from `campushub`. Confirm the right column uses the saved Fit label and checkout receives Fit, then restore the fixture. This demonstrates how data labels flow through presentation and checkout without editing live products.

## Current minimal photo header and purchase hierarchy — October 19, 2026

This section supersedes the right-aligned price and description-before-variants layout below. Earlier sections remain as implementation history.

1. **Cause / reason:** the existing screen had a separate title toolbar, plain top icons, a price beside the title and a separate presence caption. The user now wants a quieter product-led screen with circular top controls, seller/status together, price underneath and variants immediately afterward. Native preview review also confirmed that an entirely transparent pinned toolbar allowed scrolling text behind its icons; the final collapsed toolbar has a white backing.

2. **Exact files changed / current anchors:**

| File | Current line / nearby anchor | What changed and why |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 445 `SliverAppBar` | Remove visible Product Details title; reuse the same gallery inside FlexibleSpaceBar, with circular controls over the photo and readable white backing when collapsed. |
| Same screen | 671 `_ProductHeaderButton`; 706 `_ProductDetailsCartButton` | One shared circular48dp icon treatment, Lucide shopping-cart outline, real count badge and reactive persisted favorite state. Existing destinations/actions remain. |
| Same screen | 765 `_ProductInfoContainer`; 829 `product-heading-name`; 858 `product-selected-price`; 917 `_ProductDescription` | Reorder to name → seller → price → variants → full description. Use a smaller lighter peso glyph with Poppins numerals; the amount calculation remains unchanged. |
| Same screen | 1300 `_SellerIdentity`; 1328 `product-seller-status-dot` | Compact actual seller name with a6dp presence dot, tooltip and semantic status instead of a separate visible Online/Offline line. |
| `campushub/test/product_details_layout_test.dart` | 151 titleless header; 187 favorite/cart; 385 full description; 451 vertical hierarchy; 642 native captures | Check circular targets, saved favorite/count feedback, semantic price and peso font, section geometry, and existing product flows. |
| `campushub/DESIGN.md` | 56 `components.product-details.header`, `.typography`, `.heading` | Record the current header, price typography and content order. |
| `CAMPUSHUB_CONTEXT.md` | 3 `Latest minimal Product Details photo header` | Save the current correction, checks and scope. |
| `docs/product-details-status-inventory.md` | this section | Explain the implementation, verification and safe practice. |

3. **Changes made:** three outlined circular controls replace the title toolbar's plain icons. Each has a48dp target and an existing tooltip; the cart retains its actual count. Favorites now rebuild from the existing FavoriteService notifier so the gold selected heart and accessible selected state follow persisted changes. Owner review still hides customer purchase/cart/favorite controls. The same product gallery retains paging and saved variant-image selection. Below it, the small seller caption precedes the selected price; real saved variants follow the price and full Description follows the variants. Existing Chat, Add to Cart and Buy Now remain in the safe-area bottom bar.

4. **How it works — functions, inputs/outputs and data flow:** `_ProductHeaderButton(tooltip, onPressed, icon, selected)` produces only the shared visual/accessibility treatment; it owns no route or account state. `_ProductDetailsCartButton` listens to `CartService.itemCount` and opens the existing CartScreen. The favorite ListenableBuilder listens to `FavoriteService` and calls the same `_toggleFavorite` persistence method. No second favorite store was introduced.

   `_SellerIdentity(name, online)` receives the existing logged seller string and presence result. The name remains Poppins12sp; a gold dot means online and a muted navy dot means offline, with text available to assistive technology and a tooltip. The underlying15-second presence polling is unchanged.

   `_ProductInfoContainer(priceText, customization, selectedOptions, ...)` takes already-calculated display values and lays them out vertically. `Text.rich` styles only the `₱` glyph in Roboto19sp/400 while the amount stays Poppins23sp/600. Its semantic label is the complete unchanged price string. Example: `_unitPrice = 250 + 10` after selecting the saved Size M option still formats as `₱260`; the richer text changes its appearance, not the number or payload. Flow: Django saved product/options → existing ProductItem parser → `_toggleOption`/`_unitPrice` → display → existing quantity-one Cart/Checkout → Django validation.

5. **Backend / API behavior:** unchanged endpoints, seller identity/presence source, saved group/option names, stock rules, required selections and permissions. No new controller, search system, product data or runtime examples. An item without saved enabled choices still shows `No variants available.` A seller name unavailable in the response still shows `Seller unavailable`.

6. **Database / migration impact:** none. No database writes, models, migrations, dependencies, Neon/backup settings or records were changed.

7. **Tests performed / results:** final run passed all21 tests in `product_details_layout_test.dart`, `notification_product_page_test.dart` and `product_item_test.dart`. Checks include circular48dp controls, title removal, favorite persistence feedback, actual cart count, semantic price/glyph styling, vertical seller/price/variants placement at375dp and320dp2x text, full description, saved color/text choices and unchanged cart/checkout/owner restrictions. Scoped analysis of the screen and layout test returned **No issues found**; Dart formatting made no remaining changes. Early failures were outdated test assumptions about Tooltip/IconButton lookup and plain Text.data after changing price to Text.rich; those assertions were corrected and the final full focused run passed.

   Five native previews with actual bundled fonts were inspected: initial portrait, scrolled portrait,320dp2x text, landscape and saved-web color/size fixture. Reviewed header readability, circular controls, lighter peso/amount baseline, seller/status spacing, choice state, large-text wrapping and bottom actions. Files and final logs are in `scratch/product-details-review/` (`product-details-entry.png`, `product-details.png`, `product-details-small-text.png`, `product-details-landscape.png`, `product-details-web-variants.png`, `tests.log`, `analyze.log`). These are isolated mock-backed native renders, not real catalog records or phone screenshots.

8. **Remaining limitations / troubleshooting / safe exercise:** the app, phone, backend and worker were not launched/restarted, hot-reloaded, built or installed. Physical-device verification is pending. Missing product photos in isolated fixtures deliberately show the existing honest image placeholder. Presence retains the existing service behavior: failed checks currently produce offline; this update does not add a new unknown/presence API. Exact physical color hues still require saved color metadata/photos, as documented below. The common API's existing Hot/sold-count limitation is unchanged.

   To test safely, use only the fixture in `campushub/test/product_details_layout_test.dart`: change the saved Size M extra price from10 to12 and its matching expected formatted price from260 to262, then run `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart` from `campushub`. Confirm required selection, semantic/display price and checkout tests agree; restore the fixture afterward. This demonstrates that styling is separate from numeric data without touching live products. After applying changes in your normal development session, check a real saved product: top controls, seller dot, price, variants, full description and Cart/Buy Now; scroll to confirm text does not appear behind the collapsed controls.

## Current saved-web variants, seller caption and right-aligned price — October 19, 2026

1. **Cause / reason:** the user now wants color/text controls determined from the web/system variants, the smaller seller name directly below the product name and the price on the right. This supersedes the previous visible demo fallback. Inspection confirmed the existing Django customization schema supplies group names, option names and optional images, but no dedicated color-type/RGB field. The change must therefore interpret saved values conservatively and preserve order identities.

2. **Exact files changed / current anchors:**

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 725 `_ProductInfoContainer`; 797 `product-heading-name`; 866 `product-no-variants` | Adaptive name/seller-left and selected-price-right row; saved variants only with honest no-options state. |
| Same screen | 966 `_ProductVariantChoices`; 1084 `_isColor` | Detect circles versus text from saved group/option values without changing names in the purchase payload. |
| Same screen | 1268 `_SellerIdentity`; 1279 `product-heading-seller` | Reuse as compact seller caption beneath the name; 12sp actual seller and 11sp presence. Remove duplicate lower seller/avatar/chat block. |
| `campushub/test/product_details_layout_test.dart` | 378 no-variants test; 406 seller/price test; 444 saved-group classification; 495 saved color/size; 684 native preview | Replace runtime-sample expectations, verify geometry/data classification and preserve real variant payloads. |
| `campushub/DESIGN.md` | `components.product-details.heading`, `.choices`, `.empty-variants` | Record the current hierarchy and saved-data rules. |
| `CAMPUSHUB_CONTEXT.md` | `Latest saved-web variants and compact seller/right-price heading` | Preserve the latest correction and validation. |
| `docs/product-details-status-inventory.md` | this section | Current files/functions/data flow, verification, troubleshooting and safe practice. |

3. **Changes made:** the product name stays left, its actual seller name is smaller below it, and the selected price is aligned right. The right column is constrained to 42% of content width while the left column flexes for long names/large text. Presence remains under the seller; existing bottom Chat remains the functional chat action. The previous large lower seller identity block was removed so the seller is shown once. A missing seller name shows an honest unavailable message, not a fictional account.

   Runtime example groups and their state were deleted. Enabled, saved variants continue below the full Description. Products without them show `No variants available.` The system does not force Navy/White/Gold or L into product details. Test fixtures and QA examples remain isolated and never enter the live catalog.

4. **How it works / functions, inputs and outputs:** unchanged Django `normalize_customization_options` and `serialize_product` provide the saved customization JSON. The unchanged mobile customization parser feeds `_ProductVariantChoices`. `_isColor(group)` first respects explicit non-color group names (size/flavor/print/portion/serving). Otherwise color/shade labels qualify, or a generic group qualifies when every actual option is an exact recognized standard color name. Known named colors or saved images use circular controls; an unknown hue without an image is a text choice. Non-color options are always text.

   For example, saved `Variant = [Navy, White]` can display as color circles, but choosing Navy still sends `group: Variant, option: Navy`. Saved `Flavor = [Green, Brown]` remains text because its group explicitly describes flavors. Saved `Size = [M, L]` remains text. `Color = [Custom shade]` without a photo stays readable text; the app does not invent a shade.

   `_ProductInfoContainer` now positions the existing selected price alongside the product-name column, with compact `_SellerIdentity` below the name. `_toggleOption`, `_selections`, `_unitPrice` and `_purchaseSelection` retain their existing inputs/outputs and quantity-one purchase path. Data flow remains web-saved product → Django serializer → ProductItem/customization model → inferred presentation → unchanged saved group/option selection → Cart/Checkout → Django validation.

5. **Backend / API behavior:** unchanged. No new endpoint, controller, color-picker field, server price/inventory rule or product workflow was introduced. Saved names are not renamed by visible labels. Existing seller presence polling, bottom Chat, owner/unavailable purchase guards, category data and required-option validation remain. Real web edits appear through the existing catalog reload/reopen flow, not a new real-time subscription.

6. **Database / migration impact:** none. No models, migrations, dependencies, records or Neon/backup settings changed. Runtime samples were removed from UI code only; no existing database variants were removed or edited.

7. **Tests performed / results:** 20 focused Flutter tests passed across the product-layout, notification-product and product-model test files. New checks cover small seller geometry below the name, price aligned to the right at 375dp and 320dp/2x text, exactly one seller name, inferred color circles versus text and original checkout group/option names. No-variant products show no sample controls and still add/buy with empty customization. Existing full-description, Poppins, badges, required/single/multiple options, image-gallery link, cart/checkout pricing and owner/notification restrictions pass. Scoped screen/test analysis completed with no issues; formatting/whitespace checks passed.

   Native screenshots were regenerated with bundled fonts. The current web-shaped color/size fixture preview is `scratch/product-details-review/product-details-web-variants.png`; header placement, compact seller, price alignment, color circles, text size control and purchase actions were inspected. Small-text/landscape renders and test/analyzer logs remain in the same folder. These are mock-backed native UI checks, not live product edits or a physical device session.

8. **Remaining limitations / troubleshooting / safe exercise:** no phone app/server/worker was started, restarted, built, installed or hot reloaded. A normal user-controlled reload is needed to view edited Dart code. No backend tests were run because backend code is unchanged. Named swatches are representative colors; exact physical shades require actual photos or future saved color metadata. Missing/disabled customization correctly shows no options. For unusual group labels, unrecognized/mixed values safely remain text rather than guessing.

   Safe exercise: change only the isolated classification test's generic `Variant` options from `[Navy, White]` to `[Small, Large]`, predict text buttons and unchanged `Variant` group in the checkout payload, update its expected control type and run the focused test. Restore the exercise edits afterward. Never rename live options or create test orders merely to inspect the UI.

---

## Current always-visible description and in-app sample variants — October 19, 2026

1. **Cause / reason:** the user now removes expand/collapse and asks to see variant samples on every Product Details page. The confirmed visibility issue was that the previous example existed only in the QA test/screenshot; runtime rendered its entire Variants section only when the product had saved, enabled customization. This latest explicit request supersedes both the collapsible description and preview-only sample behavior described in older sections below.

2. **Exact files changed / current anchors:**

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 840 sample condition; 852 `sample-variants-label`; 863 actual versus sample branch | Always render Variants; retain genuine options or show an explicitly labelled sample when no enabled saved options exist. |
| Same screen | 939 `_ProductDescription` | Stateless heading/full text; remove preview limit, chevron, expanded state and animation. |
| Same screen | 971 `_SampleProductVariants`; 978 state; 997 `_previewChoices`; 1004 explanatory copy | Reuse existing color/text option widgets for a separate, local demonstration with Navy/White/Gold and one L. |
| `campushub/test/product_details_layout_test.dart` | 340 full-description test; 378 runtime-sample isolation test; 601 sample capture | Replace the obsolete expand/collapse tests and verify runtime visibility without affecting purchases. |
| `campushub/DESIGN.md` | `components.product-details.description` / `.sample` | Update current behavior and the explicit sample boundary. |
| `CAMPUSHUB_CONTEXT.md` | `Latest visible Product Details sample and full description correction` | Preserve the user correction and verified behavior for future work. |
| `docs/product-details-status-inventory.md` | this section | Current implementation, inputs/outputs, verification and safe exercise. |

3. **Changes made:** Description is immediately readable in full with no expander, arrow, truncation or animation. Variants is always below Description. Products with genuine enabled variants keep their current working choices and purchase validation. Other products now show `Variants` with a `Sample` label and `Sample only. Not included in orders.` The example contains circular Navy/White/Gold choices and a text L size; it is visible within the app, not just the screenshot. Poppins and the compact design remain.

4. **How it works / functions and data flow:** `_ProductDescription(description)` receives saved text and renders it directly, or the existing honest no-description message. `_ProductInfoContainer` branches on `customization.hasOptions`: true passes the existing real map and `_toggleOption` callback into `_ProductVariantChoices`; false renders `_SampleProductVariants`.

   `_SampleProductVariantsState` owns its own `_previewChoices` map and fixed, explicitly labelled demonstration groups. Its callback changes only that local map. It reuses `_ProductVariantChoices` and the circular color widget, so the sample matches real controls visually without writing sample values into the product or introducing another product controller. For example, selecting sample Gold changes `Colors: Gold` locally; the saved product's price remains unchanged. Selecting sample L does not add an L order selection to a product that does not sell sizes.

   Flow: existing product API/model → always-visible details/Variants heading → genuine saved choices **or** labelled local sample. Only the genuine selection map reaches `_purchaseSelection()` → existing CartService/CheckoutScreen. Sample state has no path into the product, gallery, stock, price calculation, order payload or API.

5. **Backend / API behavior:** unchanged. The sample is not reported as real availability and does not create/save variants. Existing actual variant requirements, inventory validation, order pricing, seller permissions, owner-view purchase restrictions and quantity-one initial purchase behavior remain. No live products or sample orders were inserted. The earlier API sales-count limitation for Hot is unchanged.

6. **Database / migration impact:** none. No schema, model, migration, record, dependency, asset or Neon/backup configuration changed. The demonstration uses local UI state only.

7. **Tests performed / results:** 18 focused Flutter tests passed across the existing product-layout, notification-product and product-model test files. The replacement description test verifies full long text, no toggle and Variants below the complete body. The new runtime-sample test opens a no-variant product at 320dp/2x text, verifies the Sample explanation, selects Gold/L, then confirms the displayed price is unchanged and both Cart and Checkout receive quantity one with **no** sample customization selections. Actual configured products do not get the Sample label and their existing selection/price tests still pass. Existing owner/unavailable, badges, Poppins, image-gallery and layout checks passed. Scoped analyzer and formatting/whitespace checks passed.

   Updated native render `scratch/product-details-review/product-details-variant-sample.png` now captures the actual runtime fallback on a product without customization. It was inspected for full Description, no chevron, clear Sample label, selected circular color, plain L and safe purchase actions. Logs remain in `scratch/product-details-review/tests.log` and `analyze.log`. Tests use isolated fixtures/preferences and a mock GET catalog, not live product writes.

8. **Remaining limitations / troubleshooting / safe practice:** no phone app/server/worker was run, installed, built, restarted or hot reloaded. Load the edited Dart code with the user's normal hot reload/run before checking the phone. The section is below Description in the vertical page, so long descriptions require scrolling. A product with genuine variants displays those rather than the fallback; the sample is not a substitute for configuring sellable options through existing admin/seller workflows.

   Safe exercise: run only the test named `every non-variant product shows a labelled sample that cannot enter cart or checkout`. Identify the separate preview map and explain why selecting Gold leaves the test checkout's selections empty and price 250. Change only the isolated test fixture's base price and update its expected price, verify the test, then undo the exercise. Do not edit live orders or insert fake catalog variants to practice the UI.

---

## Current compact description, circular colors and single-size sample — October 19, 2026

1. **Cause / reason:** the user asks for a smaller product detail layout, Description with expand/collapse chevron, variant placeholders immediately below it, `Colors:` with circular choices and an example containing one L size. This supersedes the earlier flat description and rectangular color-option presentation below. Sample content belongs to an isolated preview, preserving the project's no-fake-live-records rule.

2. **Exact files changed and current code anchors:**

| File | Current line / anchor | What changed |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 596 hero height; 794 name size; 810 price size; 829 Variants | Compact hero capped at 360dp, 16dp content gutters, 19sp name/21sp price/13sp description and smaller badge. Keep existing 48dp action targets. |
| Same screen | 911 `_ProductDescription`; 919 state; 948 `product-description-toggle` | New reusable private description disclosure: two-line preview, full text on tap, right/down chevron and expanded semantics. |
| Same screen | 994 `_ProductVariantChoices`; 1031 `Select color` | Render Variants after Description, then Colors:/saved group labels and selection hints, replaced by actual selected names. |
| Same screen | 1114 `_ColorVariantChoice`; 1129 `_namedColors` | Circular saved-color choices, visible check/ring, tooltip, button/selected semantics and 48dp tap area. Non-color options remain saved text chips. |
| `campushub/test/product_details_layout_test.dart` | 55 `variantSampleRow`; 89 `reduceMotion`; 293 saved-color test; 337 description tests; 383 isolated sample; 572 sample capture | Add preview-only Navy/White/Gold and one-L fixture; cover description motion, swatch selection, placeholders, size and existing gallery/purchase behavior. |
| `campushub/DESIGN.md` | `components.product-details` | Update compact sizes, Description, choice and sample specifications. |
| `CAMPUSHUB_CONTEXT.md` | `Latest compact Product Details description/variant refinement` | Record the current user decision, saved-data behavior, test result and remaining limits. |
| `docs/product-details-status-inventory.md` | this section | Extend the existing guide rather than adding a duplicate feature guide. |

3. **Changes made:** badge and product content are smaller while retaining Poppins and the white/navy/gold application theme. Description starts with two lines and an ellipsis when needed; tapping its 48dp header expands the complete saved text and rotates the right chevron downward. Tapping again restores the preview. The actual variant section sits below the description, even when it expands. Empty descriptions retain the honest existing message.

   The variant header shows the saved group plus selection hint: `Colors: Select color`, `Size: Select size`, then actual selected names after a choice. Colors have a small circle with a selected outline/check; sizes/flavors/other options remain text. The single-L example is a test/preview fixture only. Live products show precisely their saved options, not a forced L or invented default sizes.

4. **How it works: functions, inputs/outputs and data flow:** `_ProductDescription(description)` receives saved text and owns only a local expanded flag. The output is preview/full text plus accessible expanded state; no controller/API/database write is involved. Normal transitions use 160ms; reduced motion removes the size-animation wrapper entirely. This avoids the observed Flutter zero-duration `RenderAnimatedSize` re-layout assertion, rather than hiding that test failure.

   `_ProductVariantChoices(groups, selectedOptions, onSelected)` receives the existing parsed Django customization groups and selection map. It determines color-group presentation from the saved group name; visible `Colors:` does not rename the group in the order payload. Hints change to the actual selected option names. The existing `_toggleOption` still enforces single/multiple selection, updates the saved-image gallery index and price, and creates the same cart/checkout payload with quantity one.

   `_ColorVariantChoice` receives one actual saved option and selection callback. Exact standard names such as Navy/White/Gold map to conventional display colors. These circles represent product attributes, not new application theme colors. They are representative UI colors, not measured fabric shades. An unfamiliar/compound shade is not assigned an invented hue: it uses a saved option photo in a circle when available, otherwise a neutral circle with the saved name's initial. Its tooltip and accessible label always retain the actual name.

   Flow: existing Django option → existing customization model → variant group/placeholder → circle or text choice → existing selection state → existing price/gallery/cart/checkout. Annotated example: saved `Color/Navy` selects a navy circle and makes the header `Colors: Navy`; saved `Size/L` selects the L button and makes the header `Size: L`. Those exact group/option names, not RGB colors or placeholders, remain the purchase data.

5. **Backend / API behavior:** unchanged. No color picker or color-code field was added to the web admin, and no existing variant names were changed. Current saved names/images are reused. Required-choice validation, seller/owner permissions, catalog source, actual stock checks, price calculation, cart merging, checkout, category data and prior New/Hot eligibility remain. Missing sales-count data still cannot create Hot badges. No product record was created for the sample.

6. **Database / migration impact:** none. No models, migrations, data writes, dependencies, application assets or Neon/backup configuration changed. The sample is local Dart test data and a generated QA screenshot only.

7. **Tests performed / results:** 18 focused Flutter tests passed across `product_details_layout_test.dart`, `notification_product_page_test.dart` and `product_item_test.dart`. New/updated checks cover Description preview/full/collapse and correct ordering in both normal and reduced motion, circular saved-color selection with existing image-gallery linkage, placeholder replacement, single-L fixture at 320dp/2x text and prior Poppins/badge/category/variant/owner/unavailable/cart/checkout behavior. Scoped analysis of the screen and its test reported no issues. Formatting and scoped whitespace checks passed.

   Native captures were generated using bundled Poppins, with the existing preview currency fallback, and inspected for compact hierarchy, Description chevron, circle selection ring/check, plain L text, placeholder placement and safe purchase controls. Sample preview: `scratch/product-details-review/product-details-variant-sample.png`; current test/analyzer logs and the other portrait/landscape captures remain in the same folder. No browser or physical-device session was started for this native Flutter update.

   Repeat from `campushub/`: `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart test/notification_product_page_test.dart test/product_item_test.dart`. The optional `PRODUCT_DETAILS_REVIEW_DIR` environment value enables local screenshot output, not live sample data.

8. **Remaining limitations / troubleshooting / safe exercise:** no phone app, Django backend or worker was restarted, built, installed or hot reloaded. Exact material colors cannot be inferred from a name; use the actual product photos when shade accuracy matters. Unknown names intentionally use the photo/neutral fallback. A product with only an L choice must have only L saved in Django; the preview does not alter any live product. If variants do not appear, check the existing saved customization-enabled flag and option names/API data.

   Safe exercise: edit only `variantSampleRow()` in the test to replace its L option with XL. Predict the resulting `Select size` → `XL` header and text button; adjust the sample-only expectation, run the focused test and verify it. Then undo the exercise edit. Do not change a production listing or insert a sample product into Django to practice this layout.

---

## Current mobile Poppins, category removal and listing badge — October 19, 2026

1. **Cause / reason:** the user requests consistent Poppins text, removal of the visible category and a small New/Hot badge at the top of Product Details. This follow-up supersedes the category display in the earlier mobile layout report below. It is scoped to this product-detail experience, preserving other screens' branding fonts.

2. **Exact files changed:**

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 40/65 `submittedAt`; 218 related-product mapping; 376 `_listingBadge`; 437 `primaryTextTheme`; 527 `badge`; 726 `_ProductInfoContainer`; 773 `product-listing-badge` | Forward the existing timestamp, compute honest eligibility, use Poppins in primary/body themes and owner status, replace visible category with a compact badge above the product name. |
| `campushub/lib/module_app/screens/dashboard_screen.dart` | 999 `submittedAt: product.submittedAt` | Pass existing product timestamp through the legacy dashboard-card detail route. |
| `campushub/lib/module_app/screens/products_screen.dart` | 175 same mapping | Pass timestamp from Marketplace into existing details. |
| `campushub/lib/module_app/widgets/home/home_preview_cards.dart` | 143 same mapping | Pass timestamp through the shared Home/Search detail destination. |
| `campushub/lib/module_app/screens/notification_product_page.dart` | 121 same mapping | Preserve timestamp in existing owner-view details; owner view does not display a promotional badge. |
| `campushub/test/product_details_layout_test.dart` | 27 `submitted_at` fixture; 95 sales/timestamp mapping; 128 original layout test; 150 badge test; 193 effective-font test | Extend existing isolated tests and previews. |
| `campushub/DESIGN.md` | `components.product-details.surface`, `.badge` | Record the scoped visual behavior. |
| `CAMPUSHUB_CONTEXT.md` | `Latest Product Details typography/badge follow-up` | Preserve the current instruction and backend-data limitation. |
| `docs/product-details-status-inventory.md` | this section | Current report, functions/data flow, verification, troubleshooting and safe exercise. |

3. **Changes made:** all product-detail text uses Poppins, including owner review status and primary-theme text. The existing native fallback remains only for glyphs absent from bundled Poppins, such as the peso sign. Category is hidden visually but retained in product, cart and checkout data. A single compact badge replaces its former position above the name: navy/white New or gold/navy Hot. No horizontal separator, new card, gradient, fabricated discount or extra recommendation badge was added.

4. **How it works:** unchanged `ProductItem.fromJson` already reads `submitted_at` and optional `sold`/`sold_count`/`units_sold`. Existing navigation now forwards its `submittedAt` into `ProductDetailsScreen` on every current entry path, including related products. `_listingBadge` takes the screen's owner/availability state, supplied sales count and saved timestamp and returns either `Hot`, `New` or null. It first suppresses promotion in owner/unavailable views, then uses the existing positive-sales signal for Hot. Otherwise it compares UTC instants and shows New only when the saved timestamp is not in the future and is less than seven days old. `_ProductInfoContainer` receives that optional label and renders it above the actual product name. There is no permanent New fallback for an old or unknown date.

   Annotated example: `submitted_at = now minus 1 day` and no sales yields New; a positive supplied sales count yields Hot; `now minus 8 days`, an absent timestamp or a future timestamp with no sales yields no badge. These are UI classifications derived from supplied data, not fake product records or new order statistics.

   Data flow: existing Django serializer → `ProductItem` → existing navigation's `submittedAt`/`soldCount` → `_listingBadge` → one Poppins badge. Category still travels separately into Cart/Checkout. Why this approach: reuse the current product model/API values and keep the requested visual change small.

5. **Backend / API behavior:** unchanged. Confirmed `backend/core/api/views.py:214`, `serialize_product`, supplies `submitted_at`; the inspected common serializer does **not** supply a sales-count field. Therefore its products can qualify as New, while Hot remains hidden unless an existing data source actually supplies a positive count. This update does not invent counts, reinterpret page views as sales, add an unrequested order query or change the existing catalog-card badge rules. No API route, product approval, seller permission, inventory or purchase logic changed.

6. **Database / migration impact:** none. No records, tables, migrations, Neon configuration, dependencies or fonts/assets were added or changed. The previous database backup remains untouched.

7. **Tests performed / results:** 15 focused Flutter tests passed across `product_details_layout_test.dart`, `notification_product_page_test.dart` and `product_item_test.dart`. The added checks cover effective Poppins styles in public/owner details, category hidden but still passed to cart/checkout, badge placement above the name, positive supplied sales, recent/old/missing/future dates and no badge for owner/unavailable products. Existing variant selection, displayed price, cart/checkout quantity-one payload, actual image/gallery synchronization, notification ownership and 320dp/landscape large-text checks still pass. The native screenshot capture ran with actual bundled fonts and reduced motion; the updated New badge and white layout were visually inspected. Scoped six-file Flutter analysis completed without issues. No backend tests were run because backend code did not change.

   Repeat from `campushub/`: `C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart test/notification_product_page_test.dart test/product_item_test.dart`. Logs and native previews remain in `scratch/product-details-review/`.

8. **Remaining limitations / troubleshooting / safe practice:** no phone app, server or worker was run/restarted, built, installed or hot reloaded. Live admin-to-phone synchronization was not tested. An old/unknown listing correctly has no New badge; Hot requires genuine supplied sales data as explained above. Device clock accuracy affects the seven-day age display; it does not change saved product data. The currency symbol can use a native glyph fallback while the text's primary font remains Poppins.

   Safe exercise: change only the isolated `productRow()` test fixture timestamp from one day ago to eight days ago and verify that New disappears. Then add `sold_count: 3` in the same isolated fixture and check Hot. Explain the input/output differences, run the focused tests and undo the exercise edits. Do not change a live product date or invent live orders to force a badge.

---

## Mobile product details layout and inline variants — October 19, 2026

### 1. Cause / reason

The mobile page repeated the word Details in its toolbar and description section, used horizontal section separators and red pricing, and opened a second selection/quantity sheet for purchases. The user supplied a compact product-detail reference, requested text choices for non-color variants, and explicitly confirmed removing the purchase quantity selector as well.

The existing Django product/variant connection already exists. This is a Flutter presentation and interaction update, not a new product source, API, controller or variant storage system. The design uses the project's white/navy/gold and bundled Poppins, with whitespace separating sections.

### 2. Exact files changed and current anchors

| File | Current line / anchor | Change and expected behavior |
| --- | --- | --- |
| `campushub/lib/module_app/screens/product_details_screen.dart` | 225 `_selections`; 237 `_unitPrice`; 244 `_toggleOption`; 262 `_purchaseSelection` | Move the former sheet's option selection and price/payload handling into the existing screen state; check required groups and use quantity one. |
| Same screen | 446 `Product Details`; 530 `bottomNavigationBar`; 563 `_ProductHeroImage` | One pinned toolbar, adaptable large-text title, contained image gallery capped at 420dp, tappable 48dp page indicators, and actions reserved by Scaffold. |
| Same screen | 711 `_ProductInfoContainer`; 892 `_ProductVariantChoices` | Continuous white name/category/price/description content, saved inline options and selection feedback; remove repeated Details heading, horizontal rules, image-thumbnail strip and quantity sheet/helpers. |
| Same screen | 1027 `_SellerIdentity`; 1095 `_ProductBottomBar` | Compact seller information with outlined chat icon; safe-area Chat, outlined Add to Cart and filled Buy Now. No separator or excessive shadow. |
| `campushub/test/product_details_layout_test.dart` | 19 `productRow`; 59 `showProduct`; 102 `choose`; 121 first `testWidgets` | New isolated API-shaped fixtures and tests for interaction, permissions, adaptive layout and optional native screenshots. No catalog records are created. |
| `campushub/DESIGN.md` | `components.product-details` | Record the local product detail component specifications. |
| `CAMPUSHUB_CONTEXT.md` | `Latest mobile Product Details refinement` | Preserve the user's quantity decision, data connection, checks and limitations for later work. |
| `docs/product-details-status-inventory.md` | this section | Extend the existing product-details guide; earlier web-admin material below remains applicable to the web interface. |

### 3. Changes made

The photo and details remain on the existing `ProductDetailsScreen` route. A single Product Details toolbar keeps Back, Cart and Favorites; the extra body Details heading is removed. The hero uses `BoxFit.contain`, so whole product photos remain visible. Its saved-image gallery still supports swiping and now has tappable, selected-state image indicators with reduced-motion support.

Name, category, navy price and description flow into actual variant groups. Each non-color option is a text button using the exact saved name, such as S, M or L. These labels do not include stock quantities. No S/M/L options are invented for products without them. Color groups may use a saved option image with its text label; the backend has no color-swatch metadata, so colors are not guessed from names. Selecting an option with an image also selects its gallery image.

The obsolete buy-options sheet and quantity-only helper widgets were removed. Selection stays inline and each Add to Cart/Buy Now action starts with one item. Existing cart merging and quantity editing in Cart/Checkout remain unchanged. Required options must be selected before either action proceeds. The current selected price, single/multiple-choice behavior, group names, option names and extra prices are preserved in the purchase payload.

The bottom actions are in `Scaffold.bottomNavigationBar`, keeping the native error snackbar above them. The small-screen seller identity row uses flexible text and an icon instead of a wide text-button row. Large text can wrap the toolbar title onto two lines. Price text adds the native Roboto fallback for the Philippine peso glyph; the UI still uses Poppins.

### 4. How it works: inputs, outputs and data flow

Unchanged `backend/core/api/views.py:214`, `serialize_product(product, request, include_inventory=...)`, returns permitted saved product metadata including `images`, `customization_enabled` and `customization_options`. Both web admin and mobile ultimately read/write these existing Django fields.

Unchanged `ProductItem.fromJson` in `campushub/lib/module_app/models/product_item.dart:33` consumes the API row. `ProductCustomizationConfig.fromJson` at `product_customization.dart:71` and `ProductCustomizationGroup.fromJson` at line 34 read saved groups/options, required/single/multiple rules, extra prices and images. The existing navigation passes these values into `ProductDetailsScreen`.

Within that screen, `_toggleOption(group, name)` updates its existing local selection map and image index. `_selections` converts that map to existing `SelectedCustomization` values; `_unitPrice` adds their saved extra prices to the existing parsed base price. `_purchaseSelection()` validates required groups and outputs a `BuySelection(quantity: 1, ...)`, or returns null with clear feedback. `_handleAddToCart` then uses the existing `CartService.addFromProduct`; Buy Now uses the existing `CheckoutScreen`. No new order endpoint or calculation service was introduced.

```text
Admin/web saved product -> existing Django serializer -> ProductItem/customization
 -> existing ProductDetailsScreen -> inline choices -> BuySelection(quantity=1)
 -> existing CartService or CheckoutScreen -> existing Django order validation
```

Annotated example (test data only): a saved Size group contains `M` with `extra_price: "10"`; a product base price is 250. Selecting M displays 260 and sends `{"group":"Size","option":"M","extra_price":"10.00"}` with quantity one. The UI displays the saved option rather than replacing its identity with a new size ID. Django still validates the actual saved options, prices and stock at order submission.

### 5. Backend / API behavior

No backend code changed. Existing approved-product APIs, seller ownership/approval checks, server-side stock and selection validation, cash-on-pickup workflow, cart/checkout routes, related-product source and notification owner-view protection remain. An owner viewing a rejected/pending product still has no purchase actions. Out-of-stock or expired products keep disabled purchase actions.

Admin changes are read on the next existing catalog load/reopen. This update does not add real-time product-detail subscriptions or a second search/product controller. Existing reviews/related-section data behavior is retained; no ratings, suggestions or products were fabricated.

### 6. Database / migration impact

None. No model, migration, database record, Neon configuration, dependency or asset registration changed. No live product/order was created, edited or purchased during verification. The earlier local database backup is untouched.

### 7. Tests performed / results

- Formatting passed for the screen and its new test file.
- Scoped Flutter analysis of those two files: no issues found.
- Thirteen focused Flutter tests passed across `product_details_layout_test.dart`, `notification_product_page_test.dart` and `product_item_test.dart`.
- Covered one header/no HR/no quantity UI, actual API-shaped S/M/L labels, text-only non-color options, required-group blocking, single/multiple selections, displayed selected price, exact checkout payload and quantity one, cart payload/quantity, actual color-photo selection/gallery synchronization, unavailable/owner restrictions, existing notification ownership/deletion handling, image parsing, 320dp and landscape layouts with 2x text and reduced motion.
- Native screenshots using actual bundled fonts were generated at 375dp, 320dp/2x text and 812x375 landscape. Inspected hierarchy/white surface, single toolbar, selected versus unselected options, price glyph/update, seller wrapping, action alignment and safe bottom space. A preview-only Roboto font load supplies the currency glyph in the headless renderer; it adds no application asset.

Evidence: `scratch/product-details-review/tests.log`, `analyze.log`, `product-details-entry.png`, `product-details.png`, `product-details-small-text.png`, and `product-details-landscape.png`. Screenshot products are clearly isolated fixtures, never inserted into the live catalog. Fixture photo absence uses the existing honest fallback.

The first tests exposed a narrow seller-row overflow and an error snackbar covering actions; both were fixed before the final passing run. The screenshot harness was adjusted to repaint retained layers before each capture, and the selected-price assertion confirms the actual displayed value. Earlier failing attempts are not counted as passing checks.

Repeat from `campushub/`:

```powershell
C:\flutter\bin\flutter.bat analyze --no-pub lib/module_app/screens/product_details_screen.dart test/product_details_layout_test.dart
C:\flutter\bin\flutter.bat test --no-pub test/product_details_layout_test.dart test/notification_product_page_test.dart test/product_item_test.dart
```

### 8. Limitations, troubleshooting and safe practice

This is native Flutter verification, not a live browser/device session. No phone app, Django server or worker was started, restarted, installed, built or hot reloaded. Backend regression tests and a live admin-edit-to-phone roundtrip were not run because no backend code changed. Final device appearance and live photo/network delivery should be checked during the user's normal run.

If an expected size is missing, verify the actual saved `customization_enabled` and `customization_options` returned by the approved-product API and reload the catalog. A group or option without a valid saved name is intentionally not manufactured by the UI. If a color has no saved image, it remains a text option. If purchase is blocked, read the missing-group message or the existing unavailable status. The quantity selector was deliberately removed from this page; cart/checkout quantity editing remains available.

Safe exercise: in `productRow()` in the isolated test, change the M extra price from 10 to 12. Explain why selecting M should display 262 and why the checkout test total must change from 273 to 275 when the two print options are also selected. Run only the focused tests, observe the expected old-value failures, update expectations, verify the new values, then undo the exercise edits. Do not edit a live product or place a real order merely to test the layout.

---

## Current shared inventory/history update - 2026-10-08

Current behavior supersedes the earlier history-link-only implementation below. Product Details now renders seven actual movement columns and separates Product ID, actual SKU, Program, Major, Approval Status, Listing Status and Inventory Status. Exact files/lines, migration and tests are in [variant-inventory.md](variant-inventory.md).

Functions/data flow: `api/views.py:200` (`serialize_product`, with `include_inventory=True`) receives the permitted Product and returns saved identifiers/assignments, the shared stock snapshot and recorded movements. `inventory_monitor.py:108` (`inventory_movements`) receives a SKU and outputs audit/verifiable-order events with date, action, quantity, before/after when known, reference and actor. `admin_products.js:3298` (`populateInventoryHistory`) consumes that array and renders seven columns; `:3316` (`populateInventoryKpis`) consumes the same snapshot as Inventory. Tracked variants keep exact SKUs; bundle rows link to their component stock pools.

Why/debugging: current Available cannot prove historical initial stock. Unknown legacy balances stay as a dash. API failures show Unavailable and an explicit history error, not zero or endless Loading. Archive/Restore reuses list helpers through the shared object rather than calling inaccessible functions from another JavaScript scope. This preserves the existing order/history records and refreshes action buttons and summary counts. The 209-test regression plus final overlapping follow-up tests and browser save/archive/restore/error checks passed; the full guide explains remaining legacy/audit limits.

Safe practice: read `test_stock_history_and_sku_are_shared_between_detail_and_inventory` in `test_program_inventory.py`. Identify its input product/SKU and compare the returned quantity/reference in both views. Run that single isolated test and confirm equal outputs; then change its expected reference to an incorrect value to observe a failure and undo it. Never estimate an opening balance from current stock.

---

Current recorded-history update (2026-10-08): `backend/static/components/js/admin_products.js:3277`, anchor `populateInventoryHistory(product)`, now receives the actual product ID and outputs a link to `/admin-products/?view=inventory&product_id=<id>`. The old estimated initial-stock/restock rows were removed because they could not prove a real movement. `backend/core/modules/marketplace/services/inventory_monitor.py:101`, anchor `inventory_movements(sku)`, produces actual audit/order events for that exact SKU; the Inventory template renders those records. Existing Product Details metadata/sections/actions and API contracts remain; asset versions in `admin_products.html:14` and `:1054` ensure browsers load this change. Applied migration 0033 stores separate SKU/movement metadata, without changing existing stock/orders or fabricating past restocks.

The complete cause/files/changes/function data flow/backend/database/tests/limits report is in [variant-inventory.md](variant-inventory.md#inventory-monitoring-update--2026-10-08). Current checks passed 92 targeted Django tests and Inventory/Product-form browser checks. Troubleshooting: hard-refresh if estimated rows still appear; check the script version `20261008-inventory-history`. No recorded stock movements is an honest result when evidence does not exist. Raw SQL/bulk writes bypass the Product.save audit hook.

Safe practice: in isolated development data, open Product Details, follow the recorded-history link, and locate the matching product/variant SKU. Make one authorized test stock adjustment through the existing editor. Verify the exact signed delta, time and actor appear once; explain why a positive delta is Stock adjustment rather than an inferred historic restock. The linked guide includes repeatable commands and file/line anchors.

Current bundle behavior (2026-10-07): [component-bundles.md](component-bundles.md) supersedes the earlier unsupported-bundle note. Details displays read-only derived bundle availability and actual component/variant rows, hides Update Stock and does not fabricate standalone movements. The linked guide explains the functions, input/output data flow, changed files/lines, debugging, tests and safe practice.

Latest variant follow-up (2026-10-07): [variant-inventory.md](variant-inventory.md) documents the individual tracked-option rows replacing the parent grid. The snapshot reads actual selected-order holds and returns On Hand = Available + Reserved, own level and status; the UI shows those rows and Save Stock submits an exact variant_key. Simple-product information and independent status concepts remain. See that guide for current lines/anchors, function inputs/outputs/data flow, verification, troubleshooting and isolated-fixture practice. Its richer breakdown supersedes the older Per variant grid below; no additional migration was required.

Latest threshold update (2026-10-07): simple Details now reads the saved effective product threshold. Tracked inventory shows **Per variant** in the existing grid and a flat breakdown of each option's actual Available and Threshold. Both parent quantity-status labels use the shared per-option-aware classifier. Earlier global-only threshold descriptions, no-migration statements and line maps below describe the original Details step. See [product-low-stock-threshold.md](product-low-stock-threshold.md) for the current map, functions, inputs/outputs/data flow, applied migration 0031, tests, troubleshooting and safe learning exercise. The existing On Hand/Reserved/Available reconstruction and independent approval/listing fields remain.

Updated 2026-10-07. This guide covers the Product Information and Inventory Information cards on the existing Super Admin Products page. It preserves the gallery, description, Sales Summary, Customer Reviews, Recent Orders, Activity Log, edit action and navigation.

## 1. Cause / Reason

Confirmed in the old implementation:

- `populateProductDetails` displayed **Active** when `approval_status` was approved, and displayed **Archived** instead of the actual approval value when archived. Neither had a clear approval/listing label.
- The generic **Status** row displayed inventory state, and gallery navigation replaced it with the selected option's state.
- `populateInventoryKpis` treated saved stock as On Hand and subtracted reservations again. Actual order placement already calls `adjust_product_stock` to deduct those units, so this could understate Available.
- The frontend reservation helper counted only pending orders, ignoring Processing and Ready for Pickup and whether stock was actually deducted/restored.
- The serializer did not return `updated_at`; the initial row only supplied a date, and the formatter invented noon for date-only values.

These are inspected causes, not guesses. The fix labels each concept and obtains the inventory snapshot from the existing Django inventory service.

## 2. Exact Files Changed / Current Lines / Anchors

Lines are current approximate starting points. Search the named anchor after later edits move them.

| Folder / file relative to project root | Line / code anchor | What changed and why |
| --- | --- | --- |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 148 `data-product-base-price`; 692 `Approval Status:`; 773 `On Hand`; 793 `pdInventoryFeedback`; 15/1012 asset versions | Supply real price/timestamps/department to the initial view. Move the existing approval badge into its own labelled row, add neutral Listing Status, rename the inventory row, remove redundant Stock Quantity, add Threshold and Inventory Status to the existing inventory grid, and refresh cached assets. |
| `backend/static/components/js/admin_products.js` | 61 `fetchProductByIdFromServer`; 1643 row metadata; 1925 `submitted_at: row`; 2917 `formatPdDateTime` | Request one authorized product with its inventory snapshot. Preserve metadata after edit/save. Format actual timestamps in Asia/Manila without inventing a time. |
| Same JavaScript file | 3042 `updateHeroVariantDisplay`; 3195 `populateInventoryKpis`; 3415 `populateProductDetails`; 3477 `loadOrdersAndSales`; 3657 `const saved`; 3842 `syncDetailsFromServer` | Keep Product ID stable across images; stop one variant overriding parent stock state; render the snapshot in both cards; separate approval/listing; remove the second reservation subtraction; refresh all inventory fields after Save Stock; show loading/unavailable feedback. Existing orders/sales/history/activity functions remain in place. |
| `backend/static/components/css/admin_product_details.css` | 1708 `#pdInventoryStatus`; 1713 `.pd-listing-status`; 1722 warning states; 1725 feedback | Use compact plain navy listing/healthy inventory text, gold Low Stock and muted-red Out of Stock, without inventory badges. Keep the existing approval styles and inventory grid responsiveness. |
| `backend/core/modules/marketplace/services/inventory.py` | 293 `_selected_stock_options`; 314 `get_product_inventory_snapshot`; 356 `adjust_product_stock` | Add one shared snapshot using the existing total/threshold/status helpers and actual held orders. Extract the existing option-selection code so deduction and its displayed reserved units follow the same selections and single-option fallback. |
| `backend/core/api/views.py` | 189 `serialize_product`; 237 `updated_at`; 973 stock response; 1117 `seller_products_monitor` | Add real Last Updated and an optional inventory snapshot. Reuse the existing protected product route with `product_id`; archived details can be inspected while the unfiltered list still excludes archived products. Save Stock returns the fresh snapshot. |
| `backend/core/modules/marketplace/tests.py` | 329 `test_details_snapshot_counts_only_actual_active_holds_without_double_deduction`; 349 variant test; 370 endpoint test; 389 stock-save test | Cover real holds, threshold boundaries, aggregate variants, multiple stock-bearing selections, independent status fields, access control, dates and snapshot refresh. Optional exports contain isolated test records only. |
| `scratch/product-details/check-details.cjs` | `rowFor`, snapshot assertions, gallery/failure/save checks, `measure` | Run the actual page JavaScript with isolated backend fixtures; check current card CSS in headless Chrome. Generated HTML/JSON/screenshots in this folder are QA artifacts, not application sample data. |
| This guide, `docs/products-list-inventory.md`, `CAMPUSHUB_CONTEXT.md` | Product Details cross-reference / latest context note | Record accepted behaviour and explain investigation, functions, testing and safe practice. |

## 3. Changes Made

Product Information now contains Product ID, Category, Department, Seller, Price, Approval Status, Listing Status, Inventory Status, Created Date and Last Updated. The old standalone Active/Archived badge is now the labelled Approval Status badge, displaying Pending/Approved/Rejected independently of listing archival.

Inventory Information now contains **On Hand**, **Reserved**, **Available**, **Low Stock Threshold** and **Inventory Status** using the existing compact grid. Exactly one unit reads `1 pc`; other quantities use `pcs`. Both cards use the same backend inventory state. Healthy text is navy `#1A1851`; Low Stock is gold `#FCB316`; Out of Stock is the explicitly requested muted red `#B42318`. Listing is plain neutral/navy text; existing approved/pending/rejected badge styling is reused.

## 4. How It Works — functions, inputs and outputs

### Three independent fields

| UI label | Existing source | Display rule |
| --- | --- | --- |
| Approval Status | `Product.approval_status` | Pending, Approved or Rejected. Archiving does not replace this value. |
| Listing Status | `Product.is_archived` | True → Archived; False → Active. Active means not archived, not automatic approval/public visibility. |
| Inventory Status | `get_inventory_status(stock=available)` | Zero → Out of Stock; positive at/below configured threshold → Low Stock; above threshold → In Stock. |

The existing broader variant/expiry `inventory_status` field remains available for purchasing and option-level checks. These two parent-card inventory labels intentionally follow the requested quantity-only three-state rules, just like the Products List quantity summary.

### Inventory functions

- `get_product_total_stock(product)` returns remaining available quantity. It sums all stock-tracked options, including the existing legacy tracked-option structure. Untracked choices do not create stock; their product uses the stored parent quantity.
- `_selected_stock_options(options, selections)` returns the actual tracked option objects selected by an order, with the existing fallback when only one tracked option exists. Both `adjust_product_stock` and the snapshot reuse it. An order selecting two stocked options reserves quantity in both, matching actual deduction.
- `get_product_inventory_snapshot(product)` reads that available total and queries only this product's actual outstanding holds. Its output is a dictionary with `on_hand`, `reserved`, `available`, `low_stock_threshold`, `status`, and `status_label`. One order query reads quantity/customization; no per-order product query is made. If an active order's selected options cannot be reconciled with current options, it returns `None`; the API sends `inventory: null` and the UI shows Unavailable instead of guessing held stock.
- `low_stock_threshold()` reads existing `CAMPUSHUB_LOW_STOCK_THRESHOLD` from settings (default 5); no new product field or hardcoded UI threshold was added.
- `get_inventory_status(stock=available)` reuses the existing threshold comparison. Available 0 is checked before Low Stock.

The database currently stores remaining stock, not separate On Hand and Reserved columns. Therefore **On Hand is reconstructed as Available + Reserved**. The requested relationship still holds: `Available = On Hand - Reserved`. Do not subtract reservations from saved available stock again.

Annotated example for learning; these numbers are not application records:

```python
# Suppose actual remaining stock is 13 and actual active holds total 7.
available = get_product_total_stock(product)  # already 13 after order deduction
on_hand = available + reserved               # 13 + 7 = 20
# Display: On Hand 20, Reserved 7, Available 13.
# Incorrect: product.stock - reserved -> 13 - 7 -> 6 (double deduction).
```

### Data flow

1. The existing table row supplies real approval, archive flag, price and full timestamps for initial Product Information.
2. `fetchProductByIdFromServer(id)` requests `/api/marketplace/products/?product_id=<id>` with the existing session.
3. `seller_products_monitor` enforces the existing login and `accounts.can_manage_products` permission, uses the existing product access queryset and selects related seller/department.
4. `serialize_product(..., include_inventory=True)` adds the shared snapshot and actual `updated_at`. General list/public/mobile serialization defaults to no reservation query.
5. `syncDetailsFromServer` checks the open product ID before applying the response. `populateProductDetails` renders independent approval/listing fields; `populateInventoryKpis` copies backend values and applies their small status styles. It does not recalculate stock.
6. Before the response, inventory fields say Loading. On failure/missing inventory, they say Unavailable and explain how to retry by reopening. A failed request is not presented as zero stock.
7. Save Stock's existing response supplies a fresh snapshot; the handler refreshes both inventory states, all four quantities and Last Updated. Other sales/history/review functions remain untouched.

## 5. Backend / API Behavior

Reserved stock includes only existing MarketplaceOrder statuses **Pending**, **Processing** and **Ready for Pickup**, with `inventory_deducted=True` and `inventory_restored=False`. These are stock holds, so Pending belongs here even though it does not belong in completed-sales analytics.

Completed and Cancelled orders are excluded; restored/undeducted records are excluded even if still marked pending. No status names, approval workflow or stock mutation rules were invented. The existing single-option selection fallback and insufficient-stock checks remain in `adjust_product_stock`.

The existing GET route accepts an optional numeric `product_id`. With it, at most one accessible product is serialized with inventory, including an archived record. Without it, the current active-product list is preserved and no per-product reservation queries are added. Invalid IDs return HTTP 400. The existing Save Stock endpoint returns `product.inventory`; public/mobile product responses only gain the additive `updated_at` timestamp.

## 6. Database / Migration Impact

No model fields, tables or migrations added. No production product/order records changed during this work. Automated fixtures use the isolated Django test database; preview data is never injected into the application.

## 7. Tests Performed

Actually run:

- **14 distinct Django tests passed**: four new details tests, three existing stock deduction/restoration tests, and seven existing inventory/pricing tests. The stock-save test was rerun to export the updated isolated QA fixtures; do not count a repeated test as a new test.
- Current `admin_products.js` passed `node --check`.
- `node scratch/product-details/check-details.cjs` passed: Pending/Approved/Rejected, independent Active/Archived, quantity status in both locations, actual snapshot display, `pc`/`pcs`, stable Product ID, parent totals while switching images, loading/failure without fake zeros, and Save Stock refresh.
- Headless Chrome checked the two changed cards at **1440×900**, **500×1100** and **900×500**: ten Product Information rows, five inventory fields, exact status colors, no card/page overflow. Desktop and narrow screenshots were visually inspected.
- The existing `node scratch/products-inventory/check-column.cjs` regression also passed edit/save for simple and variant products, Save Stock's list-row update, quantity grammar, and nine-column layouts at 1440px and 500px.
- `git diff --check` passed for the six application/test files. Git reported only its existing LF-to-CRLF notice for the test file.

These are scoped backend and local UI checks, not a full-system/mobile certification. The unrelated pre-existing `test_listing_owner_shows_only_approved_sellers` label failure recorded in the Products List guide was not fixed or rerun here.

### Manual test steps

1. Refresh Products with **Ctrl+F5**, then use its existing View action. Confirm all ten labelled fields; only approval uses the existing badge.
2. Check one Pending, Approved and Rejected product. An archived product should keep its original approval and separately show Archived. Existing edit/archive/restore permissions must behave as before.
3. Check healthy, low and zero stock against the configured threshold. Both Inventory Status locations must match; Low Stock is gold and Out of Stock muted red.
4. In a safe test account/database, place a real order against a product with 20 units for 7 units. Reopen Details: On Hand 20 / Reserved 7 / Available 13. Advance to Processing/Ready for Pickup; held units remain reserved. Complete/cancel using the normal workflow; reopen to verify reserved units leave the hold and cancellation restores available stock.
5. Check a multi-variant product. Available must equal all tracked remaining quantities, not the first option. Switch gallery images; the two parent inventory statuses/totals must remain unchanged.
6. Use the existing stock action for a simple/single-option product. Its response must update On Hand, Reserved, Available, threshold, both states and Last Updated. Use Edit Product for separately tracked multi-option quantities as before.
7. Block the scoped product request in browser DevTools or test offline, then reopen Details. Inventory must say Unavailable, not zero. Restore the network and reopen to retry.
8. Confirm the gallery, description, Sales Summary, Reviews, Recent Orders, Activity Log and existing navigation still work.

## 8. Remaining Limitations / Debugging

- **Bundles:** the inspected Product model has no bundle-component relation or derived bundle availability; the existing form blocks bundle saving. No fake standalone bundle stock or new bundle feature was added. A category named Combo Meals alone is not a component-tracked bundle.
- **On Hand:** this is a reconstruction from current available quantities and current valid holds, not a stock-movement ledger. Imported historical orders without `inventory_deducted` are not assumed to reserve stock. Deleting/renaming options while tracked orders are active can prevent matching historical selections; the snapshot then returns unavailable, so reconcile these records before expecting an On Hand/Reserved total. The renamed-option safeguard was run in the variant regression test.
- Existing Inventory History is still the pre-existing reconstructed order display, not a verified stock ledger; it was not rewritten as part of these two cards. Sales/order/activity/review data paths are preserved.
- The existing stock action updates parent/single-option stock; independently tracked multi-option stock must continue to be edited through its existing option fields. The displayed total always uses the canonical backend return, not the quantity typed into a parent-only field.
- UI checks used isolated fixture responses and a minimum narrow Chrome window of 500px; they did not exercise a signed-in live browser session or mobile Flutter app.

Troubleshooting order:

1. Find `get_product_inventory_snapshot` and inspect the product's actual `customization_options`, remaining stock and matching order flags/statuses. Do not start by changing CSS or entering random numbers.
2. Inspect the scoped GET response in DevTools Network. `inventory.available` must match the canonical total; verify `on_hand - reserved == available`, the configured threshold and both timestamps.
3. If values are correct in JSON but wrong on screen, inspect `populateInventoryKpis`, its element IDs and stale cached assets. Refresh and verify `v=20261007-details-status` is loaded.
4. If approval and listing disagree, inspect `approval_status` and `is_archived` separately; an archived approved product is valid. Avoid replacing one with the other.
5. If the parent state changes when switching images, check `updateHeroVariantDisplay`: it must not write `pdInventoryStatus` or calculate one-option parent stock.
6. If network failure displays zero, inspect `syncDetailsFromServer` and the loading/unavailable branch. Record actual request status and response before deciding the cause.

### Safe practice exercise

In a temporary branch, change only the UI label **On Hand** to **Stock on Hand** in the template. Predict that the JSON key stays `on_hand`; no database/API change is needed because only the displayed wording changes. Refresh Details, inspect Network to confirm identical quantities, verify `On Hand - Reserved = Available`, then restore the original label. Run the targeted stock-save/markup test and read any failure before editing calculations. This practices locating a display change without accidentally changing business logic.

For the general investigation process, see [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md). For the quantity-first list column, see [products-list-inventory.md](products-list-inventory.md).

