# Floating Bottom Navbar Guide

File: `lib/module_app/widgets/navigation/floating_bottom_navbar.dart`
Test: `test/floating_bottom_navbar_test.dart`
Used by: `lib/module_app/screens/dashboard_screen.dart` (`bottomNavigationBar: FloatingBottomNavbar(`, ~line 389)

## What the widget does

`FloatingBottomNavbar` is a white bottom bar with 4 or 5 tabs (Home, Marketplace,
Services, Facilities, Profile). Data flow:

1. The screen passes `currentIndex` (which tab is active) and `onTap` (a function).
2. `build()` loops over `effectiveItems` and calls `_buildNavItem(context, index, item)`.
3. `_buildNavItem` computes `isSelected = index == currentIndex` and uses it to pick
   the icon (outline vs filled), color (navy vs faded navy), and label weight.
4. When the user taps a tab, `onTap(index)` is called; the screen updates
   `currentIndex` with `setState`, and the bar rebuilds.

## Change log

### 2026-10-18 — Filled active icons, top indicator removed

- **Reason:** User preferred a filled (color) icon for the active tab and no line.
- **Icons** (`default5Items` / `defaultCenterActionItems`, ~lines 67–119), Material
  outline → filled pairs from the same family so shapes match exactly:

  | Tab | Inactive (outline) | Active (filled navy) |
  |---|---|---|
  | Home | `Icons.home_outlined` | `Icons.home` |
  | Marketplace | `Icons.storefront_outlined` | `Icons.storefront` |
  | Services | `Icons.assignment_outlined` | `Icons.assignment` |
  | Facilities | `Icons.apartment_outlined` | `Icons.apartment` |
  | Profile | `Icons.account_circle_outlined` | `Icons.account_circle` |

- **`_buildNavItem`:** removed the `Stack` + `AnimatedContainer('navbar-indicator-$index')`.
  The tab is now a centered `Column`: `Icon(key: 'navbar-icon-$index', size 24)` +
  label. `isSelected` picks `effectiveActiveIcon` (filled) and `activeColor` navy;
  otherwise outline icon in faded navy `0x9E1A1851`.
- **Kept:** full-height tap area (`CrossAxisAlignment.stretch`), the fixed-size labels
  (`textScaler: TextScaler.noScaling`), tooltips, semantics.
- **Tests:** icon test checks both outline and filled lists; indicator checks replaced
  by "indicator not found" + active icon is `Icons.assignment` when index 2 is selected.
- The Lucide entry below is superseded by this one.

### 2026-10-18 — Professional redesign + Lucide icons (frontend-design skill)

**Design plan (brand-locked):**
- Color: navy `#1A1851` (active icon, label, indicator), navy at 62% (`0x9E1A1851`,
  inactive), white background, navy 12% hairline top border. No gold on the bar.
- Type: system/Roboto 11px; active `w700`, inactive `w500`.
- Layout:
  ```
  ────────────────────────────────────────────  hairline border
   ▀▀▀                                           3px navy bar = active tab
   [home]  [store]  [clipboard] [building] [user]
   Home  Marketplace  Services  Facilities Profile
  ```
- One bold element: the navy top-edge indicator. Everything else stays quiet,
  so the scale-up effect (`AnimatedScale 1.04`) was removed.

**Changes in `floating_bottom_navbar.dart`:**
- `default5Items` / `defaultCenterActionItems` (~lines 67–90): Material outline/filled
  pairs replaced with Lucide line icons — `home`, `store`, `clipboardList` (Services:
  service requests/job orders), `building2` (Facilities), `userCircle` (Profile).
  Lucide matches the center add button (`LucideIcons.plus`) so the bar has one icon style.
  Lucide has no filled versions, so `activeIcon` is left empty.
- `_buildNavItem` (~lines 176–250): the item is now a `Stack`:
  - `Align(topCenter)` → `AnimatedContainer(key: 'navbar-indicator-$index')`, 3px tall,
    width animates `0 → 28` and color `transparent → activeColor` when selected
    (instant when the device has reduced motion on).
  - `Column` with icon (22px) and label, centered.
  - `InkResponse(containedInkWell: true)` keeps the tap ripple inside the tab.
- `build()` Row (~line 332): `crossAxisAlignment: CrossAxisAlignment.stretch` so every
  tab fills the full bar height — the indicator touches the top edge and the whole
  column is tappable (≥ 60px).

**Tests (`test/floating_bottom_navbar_test.dart`):** first test now checks the Lucide
icon list; indicator expected navy when active, transparent otherwise.

**Not changed:** the side drawer in `dashboard_screen.dart` (~lines 289–317) still uses
the old Material icons for the same destinations.

### 2026-10-18 — Removed gold (`#FCB315`) pill behind the active tab

- **Cause / reason:** User request: no gold highlight on the active tab.
- **Where:** `_buildNavItem`, inside `AnimatedContainer(key: ValueKey('navbar-indicator-$index'), ...)`,
  around lines 212–218 (anchor: comment `// No gold pill behind the active icon.`).
- **Before:**
  ```dart
  color: isSelected ? selectionColor : Colors.transparent,
  ```
- **After:**
  ```dart
  color: Colors.transparent, // indicator never filled
  ```
- **How the active tab is still visible:** filled icon (`effectiveActiveIcon`),
  solid navy `activeColor` (`#1A1851`) instead of faded navy, bold (`w700`) label,
  and a slight 1.04 scale on the icon.
- **What was kept:** the `selectionColor` parameter still exists and is still used
  for `focusColor` (keyboard/D-pad focus highlight). No caller passes it, so no other
  file needed changes. The `AnimatedContainer` was kept so its size (52×30) and the
  test keys stay the same.
- **Tests updated** (`test/floating_bottom_navbar_test.dart`):
  - ~line 36: contrast check now navy vs white (the real background) instead of navy vs gold.
  - ~line 76 and ~line 177: indicator color now expected to be `Colors.transparent`.
- **Database / API impact:** none (UI only).

## How to test manually

1. `flutter run`, log in, reach the dashboard.
2. Tap each tab: the icon should turn filled and navy and the label bold, with
   no yellow/gold background.

## Practice exercise

Goal: make the active label slightly larger.

1. In `_buildNavItem`, find `fontSize: 11,` inside the label `TextStyle`.
2. Change it to `fontSize: isSelected ? 12 : 11,`.
3. Run `flutter test test/floating_bottom_navbar_test.dart` — the layout tests at
   widths 320/390/768 should still pass (they check for overflow exceptions).
4. Revert if you prefer the original.

## Remaining limitations

- `selectionColor` is now only used for the focus highlight; if no one needs a
  gold focus ring, it could be removed later.
