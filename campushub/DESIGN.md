---
name: CampusHub Mobile Discovery
description: Scoped visual system for the Flutter shared header, regular-user Home and full-width bottom navigation with accessible selection feedback.
colors:
  navy: "#1A1851"
  gold: "#FCB315"
  white: "#FFFFFF"
  light: "#FFFFFF"
  image-surface: "#FFFFFF"
  marketplace-card-surface: "#FFFFFF"
  marketplace-image-surface: "#FFFFFF"
  muted: "#475569"
  metadata: "#64748B"
  line: "#E2E8F0"
typography:
  brand:
    fontFamily: "SugarPie"
    fontSize: "24sp"
    fontWeight: 400
  greeting:
    fontFamily: "Poppins"
    fontSize: "16sp"
    fontWeight: 700
    lineHeight: 1.25
  section:
    fontFamily: "Poppins"
    fontSize: "20sp"
    fontWeight: 700
  body:
    fontFamily: "Poppins"
    fontSize: "14sp"
  metadata:
    fontFamily: "Poppins"
    fontSize: "12sp"
  navigation:
    fontFamily: "Poppins"
    fontSize: "11sp"
    lineHeight: 1.15
    letterSpacing: "-0.1sp"
  identity:
    fontFamily: "Montserrat"
    fontSize: "13sp"
    fontWeight: 600
rounded:
  field-row: "12dp"
  catalog-card: "14dp"
spacing:
  inline: "4dp"
  small: "8dp"
  card-gap: "12dp"
  row: "16dp"
  page: "20dp"
  section: "24dp"
components:
  product-details:
    purpose: "Existing marketplace product detail route; actual Django product/options"
    surface: "White (#FFFFFF) Scaffold body, collapsed SliverAppBar and below-image indicator strip; cream (#F9FDE7) background only on the top hero image container; white option chips, circular controls and related cards; #E8EAF0 1px borders/hairlines; #667085 secondary text; no Divider widgets"
    header: "Titleless gallery header (no 'Product Details' text); circular 48dp Back/Cart/Favorite controls with #E8EAF0 border over top-filling photo; favorite heart is always #1A1851 navy blue (outline when unselected, filled when favorited)"
    gallery: "Full-bleed BoxFit.cover product photos filling the top hero stage (capped 240..340dp) on #F9FDE7 cream image surface with 1px #E8EAF0 bottom border, supporting up to 6 swipeable images; 26dp #FFFFFF white strip directly below image renders compact tappable pill/dot page indicators (18x6 active #1A1851 pill, 6x6 #D0D5DD inactive dots)"
    typography: "Poppins UI; product name 22sp/600, navy price 26sp/700 with Roboto peso glyph, section heading 16sp/600, body 13.5sp (#667085), secondary label 12sp, buttons 14.5sp/600"
    heading: "6dp top inset, compact tappable review summary on top, 4dp then horizontal row with conditional New/Hot badge on left (8dp right gap) + Expanded product name, 4dp then price, 12dp then saved options (when present), 12dp then full Description, 12dp then hairline-bordered seller row (36dp photo, 13.5sp/600 name, 12sp Online/Offline, right chevron to chat)"
    reviews: "Ratings & Reviews header with right-aligned 12sp See All; customer summary uses five fractional gold #FCB315 stars or #D0D5DD outline stars + No reviews yet when unrated; never fabricates ratings"
    related-products: "Left-aligned You May Also Like heading; 140dp #FFFFFF MarketplaceColors.cardSurface cards with #E8EAF0 border, 10dp rounded #FFFFFF MarketplaceColors.imageSurface image with top-right 28dp circular #1A1851 navy Favorite heart toggle, product name and navy price"
    badge: "Left of product name (with 8dp gap): 6dp rounded navy New for a saved submission within 7 days; gold Hot only with positive supplied soldCount; no fabricated fallback"
    description: "Always-visible Description heading (16sp/600), 6dp gap and full saved text (13.5sp #667085); followed by hairline-bordered seller row and conditional Expiry Date top hairline row"
    choices: "No generic Variants heading, no 'Select color'/'Select ...' prompt text, and no inline 'Please choose ...' text below variants; saved web groups only with clean headings ('Colors' or group name); two groups appear left/right with 16dp gap when content width>=320dp and 13sp scales<=18dp, otherwise stack; all options in color groups use 38x38 circular color swatch targets (34x34 rings, 28x28 color circles resolved from exact/compound color names or photos without text inside), while non-color options use shrinkWrap/compact 10dp rounded white/#1A1851 FilterChips with #E8EAF0 border; preserve payloads"
    empty-variants: "Hide the entire option area when saved enabled options are absent; no heading, empty message, samples or forced size/color values"
    purchase: "Inline selection; no quantity sheet/stepper; existing cart/checkout receive quantity 1 and actual selected price/payload"
    actions: "Top-bordered (#E8EAF0) white bottom bar with SafeArea; left 48dp Chat action (messageSquare icon on top + 'Chat' text below) + 1x32dp #E8EAF0 vertical divider ('|') + 48dp Add to Cart action (shoppingCart icon on top + 'Add to Cart' text below, without button outline/container) followed by an Expanded 48dp height, 12dp radius solid navy Buy Now button"
    data: "Existing ProductItem/ProductCustomizationConfig and Django customization_options; serializer adds seller_photo_url from actual owner.profile_photo when present; no new endpoint/controller/schema"
  seller-my-products:
    purpose: "Owned seller product management; UI-only refinement, no sample data"
    header: "Existing white CampusHub header; local Search icon toggles to X; fixed Back/My Products/Add row"
    search: "Initially hidden; autofocus Search my products; X clears/collapses; existing local workspace query"
    filters: "All, Single, Bundles, Pending, Approved, Rejected, Archived; compact scrollable chips; navy/white selected state"
    row: "White with thin outline, 12dp radius/padding, 76dp product image, name/category/type/status, price and stock"
    typography: "Poppins; 18sp section title,14sp product name,12sp metadata and stock,13sp price"
    actions: "Add popup: existing single-product form or bundle-suggestions flow; vertical dots: existing details/inventory"
    data: "Existing owner-scoped workspace serializer; no new endpoint/model/controller or production fixtures"
  campus-home-banner:
    placement: "Directly below Welcome, above seller sections and catalogs"
    photo: "assets/img/ustp_oroquieta_entrance.png; user-supplied campus entrance"
    backgroundColor: "{colors.navy}; solid 78% navy tint over photo, no gradient"
    textColor: "{colors.white}"
    actionColor: "Gold to soft gold gradient (gold/white blend); navy text; explicit user exception"
    typography: "Poppins; 18sp title / 12sp description and action"
    rounded: "14dp"
    padding: "16dp"
    playback: "5-second automatic horizontal swipe; 450ms easeInOutCubic; centered dots, no arrow/play buttons"
    layout: "Measure tallest scaled text; add24dp photo space, minimum188dp; lower-left compact button with48dp target"
    interaction: "Manual banner swipe; retained tab callbacks; stop in background/inactive Home and for reduced motion; accessible pause action"
  seller-sales-period:
    placement: "Right of Sales Overview"
    options: "Daily (today), Weekly (last 7 days, default), Monthly (this month)"
    appearance: "Selected text and chevron, white surface, navy text, thin outline, 48dp minimum height"
    data: "Existing authenticated workspace API and canonical Django period helper"
  search:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.body}"
    rounded: "pill (half-height end caps)"
    padding: "14dp horizontal, 10dp vertical"
    height: "48dp minimum; no adjacent Home filter button"
  catalog-card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    rounded: "{rounded.catalog-card}"
  service-row:
    backgroundColor: "{colors.light}"
    textColor: "{colors.navy}"
    rounded: "{rounded.field-row}"
    padding: "16dp"
  cart-action:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.navy}"
  bottom-navigation:
    backgroundColor: "{colors.white}"
    textColor: "{colors.navy}"
    typography: "{typography.navigation}"
    rounded: "0dp; flush with viewport edges"
    padding: "No outside inset; system safe area inside the white surface"
    height: "68dp minimum content height, full width, plus system safe area"
    motion: "220ms easeOutCubic, 2dp icon lift, 1.08x selected scale, 140ms glyph crossfade; immediate with Reduce Motion"
---

# Design System: CampusHub Mobile Discovery

## Overview

**Creative North Star: "Compact campus discovery"**

This document records the Flutter shared header, regular-user Home discovery and current five-destination bottom navigation. It is scoped to those surfaces, rather than every existing mobile screen or the Django web interface. Navigation retains the reference-inspired rounded outline/filled Material icon pairs and selection motion, with the latest requested full-width white surface flush to the viewport edges. Navy selection and subtle navy tap/focus feedback preserve unchanged labels; there is no floating shadow or outside gap. Real campus records carry the visual interest, with navy structure and a small gold accent.

The shared header leads into the actual user's first-name greeting, a search entry below the greeting that opens the dedicated catalog Search page, horizontal Marketplace products, horizontal Facilities cards, and active Services rows. The first viewport gives space to discovery rather than a promotional hero. Existing imagery and honest image fallbacks are part of the system. [PRODUCT.md](../PRODUCT.md) supplies the durable identity and real-data commitments; [the feature guide](../docs/mobile-services-navigation.md#mobile-header-and-discovery-home---october-18-2026) owns implementation, data flow, troubleshooting, tests, and the safe practice exercise.

**Key Characteristics:**

- White and light surfaces, navy information, restrained mobile gold.
- Compact scanning with explicit catalog headings and familiar Material interactions.
- Real records and distinct loading, error, empty, and no-match states.
- Scalable Home content and complete accessible action names.

## Colors

The palette is institutional navy, mobile gold, and white/light, with navy-derived muted text and separators.

### Primary

- **Campus Navy** (`navy`): headings, readable content, icons, focus borders, and navigation selection.
- **Campus Gold** (`gold`): the Campus portion of the wordmark, actual unread-message badge, compact cart action, and facility status marker. It is an accent rather than a large surface fill.

### Neutral

Current Home container treatment: white card/search/header surfaces on the light page; image/fallback areas use `image-surface`. Separate containers with `line`; resting card and search shadows are removed. Secondary text uses `muted`. Metadata uses `metadata` only on white/page, with measured contrast at least 4.5:1.

- **White** (`white`): header, catalog cards, bottom navigation, and favorite control.
- **Campus Light** (`light`): search field, service rows, catalog messages, and image fallbacks.
- **Muted Navy** (`muted`): seller names, descriptions, capacity, and secondary instructions.
- **Quiet Line** (`line`): card and search outlines.

**The Mobile Gold Rule.** This scoped Flutter system retains its mobile gold token; the web palette is maintained separately.

**The Honest State Rule.** A color or marker never supplies evidence of availability, popularity, unread counts, or completion. Use recorded text and actual state.

## Typography

**Display Font:** bundled Sugar Pie for the shared header wordmark only; retain configured fonts elsewhere.
**Body Font:** bundled Poppins, inherited from the root light/dark theme and shared AppTypography helper. Profile identity name/program/year-section retain Montserrat.

The header wordmark uses the supplied brush script at regular weight and natural spacing; the content hierarchy uses readable mixed-case labels. No display-sized hero text or invented eyebrow labels are needed on this Home surface.

### Hierarchy

- **Brand:** the bold `brand` role; the header scales its wordmark down when horizontal space requires it.
- **Greeting:** the `greeting` role; actual first name with a generic welcome fallback.
- **Section:** the `section` role; Marketplace, Facilities, Services.
- **Titles:** product names use medium weight at 15sp; facility names use bold at 16sp; service names use bold body size. These are component-specific roles, not a new global type scale.
- **Body and metadata:** the `body` and `metadata` roles; longer supporting text uses comfortable line height and bounded previews.
- **Navigation:** the `navigation` role; selected labels are bold and idle labels medium weight.

**The Reading Space Rule.** Home text follows the device TextScaler. Card heights grow from scaled text measurements; section titles and actions share flexible width and wrap when necessary. Service cards gain width (up to 1.5x) with larger text to preserve their action labels. Only bottom destination labels use `TextScaler.noScaling`, matching the compact native Material navigation convention; full semantic names and scalable tooltips remain.

## Layout

Home marketplace cards show product name, price, recorded category, then the plain seller name. Category has no badge; seller has no Seller: prefix. Missing category/seller data is not replaced with an invented Campus seller. Shared card height reserves both metadata lines at device text scale.

Flutter values in this file use logical pixels (`dp`) and text sizes (`sp`); they are not CSS measurements. Home currently uses16dp horizontal,8dp top and32dp bottom ListView padding; the smaller top inset raises the welcome below the shared header. Section blocks use the section spacing token; horizontal cards use the card-gap token.

The content is one vertically scrollable, refreshable page. Products are 184dp wide with a 138dp image region. Facilities are 238dp wide with a 126dp image region. Their text regions adapt to TextScaler. Services use full-width rows with flexible text and a trailing chevron. Normal previews show up to six products, six facilities, and three services; a nonempty search exposes every matching fetched record.

The header is a compact row: menu, existing logo and wordmark, then an outlined Notifications bell. Messages remains in the drawer and Profile. Flexible brand space preserves the action controls. Bottom navigation has five equal full-height touch regions, SafeArea clearance, and a minimum content height of 68dp. Its height can grow with the device text scale even though its compact visual labels remain unscaled.

## Elevation & Depth

The scoped surfaces are flat at rest: no card or navigation shadow, no gradient, and no glass effect. White/light contrast, thin boundaries, image clipping, and spacing separate content. Native Material ink, focus, tooltip, and dialog behavior remain legitimate interaction materials.

**The Flat Surface Rule.** Keep resting catalog and navigation surfaces flat; preserve visible native feedback for interaction and focus.

## Shapes

Fields, service rows, and catalog messages share the gently rounded `field-row` shape. Product and facility cards use the slightly larger `catalog-card` shape and a thin quiet outline. Images clip within card boundaries. Circular favorite/cart actions remain recognizable Material icon controls; circular controls are not a general pill-container rule.

## Components

### Seller workspace drawer

Scoped to the existing SellerDashboardPage; regular Home and five-tab navigation remain separate. White scrollable drawer, width88% clamped to280–360dp, SafeArea,16dp horizontal inset and no elevation. Keep actual seller name, Program and Year/Section; no Approved Seller badge. AuthUser has no uploaded photo field; retain the existing default avatar. Final SETTINGS group contains only Account Settings, reusing existing Account & Security; no My Profile entry.

Use drawer-local Montserrat roles: seller name16sp/700/1.3, metadata12sp/1.4, Program12sp/600, section11sp/700/1.4 with0.8sp tracking, row/Back14sp/500/1.35 and selected row600. Secondary information uses72% navy and decorative lines12% navy on white; no unrelated gray accent. Keep outlined icons22dp, chevrons20dp and minimum52dp row height. Align section headings and Back with the row icon gutter; section spacing24dp above/8dp below. Selected rows use6% navy, a3dp Flutter gold #FCB315 left edge and selected semantics; no gradients or random status colors. Expand/wrap text instead of clipping at large font scales. Headings are OVERVIEW, PRODUCT MANAGEMENT, ORDER MANAGEMENT, RECOMMENDATIONS, REPORTS, SETTINGS; Back to CampusHub sits after a thin divider. Messages/Notifications belong in the seller header only. Decorative icons do not repeat visible labels to assistive technology.

Seller header: navy #1A1851, existing white/gold logo_dark, shared CampusHubBrand with white Campus/gold Hub and the same bundled SugarPie wordmark as regular Home. White outlined header actions, actual ChatService unread badge only when positive; no fake notification indicator. Keep destination title below the header in Montserrat20sp/700. Seller content background #F7F8FC and white flat cards. Home order: Sales Overview, Suggested Product Bundles, My Bundle Suggestions, Sales Trend, Inventory Attention, Recent Orders. Compact previews/See All reuse existing destinations/data; no technical Apriori metrics, global search or Quick Actions. The regular Home header and five-tab styling remain unchanged.

Seller content uses white, thin boundaries, compact rows and 48dp action targets. Overview has two columns with equal-height row cards, collapsing to one at large text. Inventory displays the server's actual variant rows/derived bundles. Loading, access denial, connection errors and genuine empty results remain distinct. No synthetic recommendation rows or visible research metrics. Existing Profile/Settings and Add Product components are reused. Implementation/data-flow/testing guide: `docs/mobile-seller-application.md` (from repository root).

Seller Home refinement: greet the actual first name, then Total Sales, Total Orders, Active Products and Pending Orders in the compact2-column grid. Only Total Sales follows the labeled sales period; orders/products/pending counts are current/all seller records. Product-pair cards use equal image/name columns separated by a plus icon, with View Suggestion and Create Bundle below. See All > opens existing seller destinations. My Bundle Suggestions contains actual owned bundle listings with normal Product review statuses, not saved pairs with invented approval. Sales Trend exposes the existing period filter and safe baseline. The dedicated seller route's drawer has the accessible name Seller navigation; regular Home and its five tabs remain separate. Recipe editor uses the existing Montserrat form style, real categories/variant choices and required quantities; never show a standalone bundle stock/threshold input.

### Buttons

Actions are concise and familiar: navy text for See All and Retry, a white favorite icon control, and a gold cart icon control. Preserve each action's tooltip, disabled state, native focus/ink feedback, and existing business action. A disabled cart control uses light/muted treatment when a product cannot be purchased.

### Cards / Containers

Product cards combine an actual image or honest fallback, favorite action, name, seller, price, and cart action. The compact Home variant uses the catalog-card shape and flat outline. It reuses the existing favorite, cart, and product-detail methods. Do not inherit the separate legacy product-card decoration into this scoped Home pattern.

Facility cards use the same flat outlined form, a larger horizontal width, actual imagery, name, recorded capacity where present, recorded status, a small gold marker, and an arrow. `capacity_label` takes precedence; a positive numeric capacity is the fallback. A marker does not promise that a time slot is free. Tapping opens the existing facility detail route.

Service rows are light rounded surfaces with an existing facility-type icon, name, description/category fallback, and chevron. They show active catalog services and open real service details. The existing details action says **How to Request This Service** and explains the type-specific requirements/contact guidance; it is not an online intake form.

### Inputs / Fields

The single labeled Home search uses a light fill, quiet outline, navy search icon/cursor, and navy focus border. The clear action appears only with input. Search matches fetched product names/sellers/categories, facility names/types/locations, and service names/categories/descriptions without creating sample results. Its field label remains visible above the hint.

### Navigation

The shared header provides drawer access and an outlined Notifications bell, inset by an additional12dp from the right. Messages remains available through the drawer and Profile. Notifications opens an honest explanation that mobile notifications are not yet available; there is no fabricated badge or feed.

The bottom destinations remain **Home, Marketplace, Services, Facilities, Profile**, in that order. The compact-label correction changes label scaling only. Incumbent icon artwork and selection styling in `floating_bottom_navbar.dart` are outside this redesign; this document does not freeze either into a future visual rule. Every destination exposes its full name and selected state through one semantics node, a tooltip, and a full-height tappable region. Existing Navigator, PageController, and retained-tab behavior remain the interaction model. There is no visible center add action on this configuration.

### Catalog feedback

Each catalog owns its loading indicator, error with Retry, empty message, and no-match message. One failed catalog does not hide the others. Pull-to-refresh reloads real catalogs while retaining search input. Feedback uses the same quiet surfaces and typography as content.

## Do's and Don'ts

### Do:

- **Do** keep this document scoped to the shared header, regular-user Home discovery, and current bottom navigation.
- **Do** use real names, imagery, prices, capacity, status, and unread counts, with explicit fallbacks when records are missing.
- **Do** preserve scalable Home content, full accessible action names, visible focus feedback, and native Material tooltips.
- **Do** reuse the current routes, retained tabs, image helpers, favorite/cart methods, and catalog models.

### Don't:

- **Don't** add a promotional carousel, oversized hero, fake Hot/New labels, or seller/admin analytics to this Home surface.
- **Don't** introduce extra badge colors, gradients, glass, or resting card/navigation shadows into these scoped surfaces.
- **Don't** interpret Open for Booking as evidence that every schedule is free, or service guidance as online request submission.
- **Don't** turn the bottom-label scaling exception into a rule that prevents Home content from scaling.


### Dedicated Search

Home retains its white surface and compact48dp-minimum pill search entry below the greeting, with no Home filter button. Tapping pushes SearchPage with Back and an automatically focused input; the shared CampusHub header contains no search field. SearchPage uses white behind white product cards and compact suggestion rows, navy text, gold selected category filters and bundled Montserrat styling. Empty input shows history-based Recommended for You only when qualified results remain in the current public catalog; otherwise Recently Added Products, sorted by saved submitted_at, plus Explore Available Products. There is no Popular Searches section without real popularity data. Typing replaces discovery with query matches; submitting exposes All/Products/Facilities/Services results. See the dedicated Search section in the feature guide for data flow and limitations.


### Approved seller Home selection

The existing dashboard root chooses the existing SellerDashboardPage/SellerDrawer for approved seller access, using Django's boolean rather than account type. Seller Home has its own navy brand header and six sales sections; no regular five-tab navigation. Other accounts keep regular Home and menu. Profile retains Apply to Sell for non-approved users, with status subtitle, and has no seller-management destination. Back to CampusHub is an explicit public-browsing mode without logout; Home/regular drawer Seller Dashboard returns approved users to seller Home. Startup/resume access checks have loading/error/retry and never invent approval. Current gold is #FCB315. No new navigation framework or screen design.


### Correction: one shared Home, seller additions only

Supersedes the earlier approved-seller root-page replacement. Everyone retains the same normal white header, greeting/search, Marketplace/Facilities/Services and five-tab navbar. Approved sellers get compact Sales Overview and Suggested Product Bundles between Search and Marketplace. Render existing seller workspace data inline as a Column inside Home's scroll; no new initial page, nested Scaffold or seller header replaces regular Home. Existing seller tools are explicit module navigation from the drawer/See All; Profile has no seller-dashboard shortcut. Gold remains #FCB315.


### White header / Sugar Pie correction

Shared Home and existing seller module headers are white with navy icons. CampusHubBrand uses the existing bundled SugarPie24/w400 wordmark, navy Campus and #FCB315 Hub. Regular labels retain existing Montserrat/system typography. Seller Home remains inline additions on regular Home with the same five-tab navigation; this header-only correction must not create another initial page or change drawer structure.


### Poppins mobile UI and sharp drawer

Current mobile UI uses bundled Poppins weights400/500/600/700/800/900 for labels, forms, cards, navigation and seller tools. AppTypography replaces runtime GoogleFonts requests; all six faces ship offline. CampusHub header retains SugarPie. Profile identity name/program/year-section and seller drawer identity retain Montserrat. Drawer is an opaque white surface (light) or campus navy (dark), no blur filter or translucent surface. Menu Poppins14/500 (selected600), section11/700 with0.6tracking, 52dp minimum growing rows,22dp outline icons, readable navy-derived secondary text and consistent gutter. Full identity text can wrap at large font settings; retain all existing menu labels/actions/RBAC. No business, backend or regular five-tab navigation changes.

### Seller navigation hierarchy and header profile

Current header right-side order is Notifications then a34dp initials/default avatar inside a48dp Profile action; Messages moves into Communication in the approved seller drawer with its existing real unread count. Keep the white SugarPie header. Drawer identity is full-width name (Montserrat17/700), program/year-section (Montserrat12/500), saved email (Poppins12),24dp lower spacing and a thin divider. No duplicate drawer avatar. Six groups: Overview/Dashboard; Seller Management/My Products/Inventory/My Bundles/Orders; Recommendations/Suggested Product Bundles/My Bundle Suggestions; Reports/Sales Analytics; Communication/Messages; Settings/Account Settings. Section padding20dp top/8dp bottom, consistent52dp growing navigation rows and gold selected edge. Dashboard returns shared Home; Profile opens existing tab4. No new seller root, account system or bottom-navigation changes. Account API currently has no photo URL; keep initials fallback until a real field exists. Implementation/functions/verification guide: `docs/mobile-seller-application.md`, latest section.

### White sidebar destinations and direct tab selection

Latest user preference overrides the older dark seller surfaces: drawer and seller destination page are always white with navy text and the existing gold selected edge. Keep the same CampusHub header throughout top-level sidebar selection, including existing Messages and embedded Account Settings content. Other account settings pages retain their standalone layout by default. Root five-tab navigation is tap-only with immediate page selection; horizontal swipes do not move between tabs. Keep state retention and independent inner horizontal catalog/gallery scrolling. Do not change global saved theme, API logic or introduce a separate seller Home. See `docs/mobile-seller-application.md` latest section for functions, checks and limitations.

### Seller center Add Product action and Iconsax

Approved sellers: Home | Marketplace | Add Product | Services | Facilities. The middle position is an action with an Iconsax box-add outline in a small gold container, not a page or floating overlay. Non-sellers keep Home | Marketplace | Services | Facilities | Profile. All nav/header/drawer glyphs use locally bundled Iconsax; inactive outlines, selected filled variants, existing restrained motion. Preserve48dp+ touch targets, Poppins11 labels, white/navy/gold palette and the header Profile avatar. Profile remains existing page4 and may have no selected seller-bar destination. Root tabs stay tap-only. Remove My Bundle Suggestions entry/preview; keep Suggested Product Bundles and My Bundles. Route successful suggested bundle creation to My Bundles. Existing APIs/data and form/body iconography remain. Package attribution/license: `THIRD_PARTY_NOTICES.md`; implementation and verification: `docs/mobile-seller-application.md` latest section.

### Reference-layout raised seller action

Latest layout request supersedes the small inline center container above. Use a56dp circle in existing gold#FCB315 with a navy28dp Iconsax box-add, raised16dp relative to the supporting white bar. Reserve that16dp inside the actual navbar layout and hit region; normal seller row84dp before safe area. Four supporting24dp icons sit lower with11dp Poppins labels,4dp icon/label rhythm and the existing selected Home silhouette/motion. Keep equal slots, all labels/routes and white surface flush with bottom/side edges. Non-seller bar stays flat and unchanged. No dark reference recolor, new shadow, notch, separate FAB or business change. User controls Ctrl+F5: no automatic app run/build/install/restart for visual verification; report source-only limits.

### User-supplied navigation glyphs (October 19, 2026)

Replace the box-add glyph above with the supplied filled rounded-square-plus vector, preserving the28dp navy glyph inside the same raised gold56dp circle. Inactive Home uses the supplied house outline/door stroke, while selected Home retains the earlier supplied filled house. Both use the existing muted/selected navy tints; preserve labels, animation, semantics and layout. These exact vectors are local CustomPaint paths, not downloaded replacements. Other navigation glyphs retain Iconsax. Source-only checks while the user's Ctrl+F5 session is active.

Latest glyph correction: Add Product now uses the user's outlined circle-plus SVG instead of the rounded-square plus, at the same size/tint inside the raised gold circle. The shared and seller header drawer controls use the three-horizontal-line Iconsax `menu_1_copy`, replacing the four-dot `menu_copy`. Preserve existing tooltip, touch region and drawer callback. Home glyphs and all layouts/colors stay unchanged.

Latest simplification: remove the plus glyph's outline ring, keeping a plain rounded plus inside the same raised gold button. The seller sidebar now has a56dp actual-name initial avatar (blank-name user-outline fallback) above identity with16dp gap; no real photo exists in the current account API. Keep Montserrat identity and Poppins controls. Profile divider spacing is24dp above/16dp below, named in `_SellerDrawerStyle`, with the existing1dp line. Keep the whole sidebar scrollable and current user/session/routes unchanged.

### Seller Add Product: one continuous page (October 19, 2026)

Operate mode, scoped to `SellerAddProductPage`; preserve existing Home, public catalogs, seller tools and navigation. A fixed56dp white AppBar has Back and Add Product in Poppins20/600, campus navy, thin bottom divider, no shadow. One vertically scrolling Form has16dp gutters, max640dp width,24dp section gaps and12dp input/container corners on#F7F8FC. White sections use16dp padding,16dp/600 headings,13dp/500 visible field labels with8dp separation and16dp field gaps. Inputs grow with content/text scaling; minimum52dp submission button stays at the end of the scroll. No stepper, horizontal page switching, draggable sheet, sample autocomplete or seller selector.

Exact hierarchy: Product Information(Name, realCategory, requiredDescription), Pricing & Inventory(positivePrice, nonnegativeQuantity, existing optional perishableExpiry), Product Images, Product Review, Submit for Approval. Stack price/quantity at360–390dp. One image follows the existing mobile API contract; outlined image-plus picker,96dp preview and Replace/Remove controls, honest empty/error state. Review text is supporting13dp copy; full-width navy/white submit has loading and duplicate-tap protection. Retain the shared navy/white palette, Poppins and existing institutional gold token; no new status color. Inline error copy uses the same restrained navy with live-region semantics.

The actual project uses StatefulWidget/Navigator, not GetX. Reuse current seller approval/category read and authenticated submission services; server ownership and Pending review stay authoritative. Shared image_picker and ProductImage are reused; no new package or backend. Verified with isolated Flutter captures at360px/390px/1.3x text and keyboard insets,19 headless tests and scoped static analysis. Native app session remains untouched. Implementation/report: `docs/mobile-seller-application.md`, first section.
