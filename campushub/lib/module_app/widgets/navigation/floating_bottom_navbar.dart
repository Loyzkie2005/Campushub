import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';
import 'home_navigation_icon.dart';
import 'add_product_navigation_icon.dart';

class FloatingBottomNavbarItem {
  const FloatingBottomNavbarItem({
    required this.label,
    required this.icon,
    this.activeIcon,
    this.activeIconWidget,
    this.iconWidget,
  });

  final String label;
  final IconData icon;
  final IconData? activeIcon;
  final Widget? activeIconWidget;
  final Widget? iconWidget;

  IconData get effectiveActiveIcon => activeIcon ?? icon;
}

class CenterElevatedNavbarLocation extends StandardFabLocation
    with FabCenterOffsetX, FabFloatOffsetY {
  const CenterElevatedNavbarLocation({this.offsetAboveNavbar = 12.0});

  final double offsetAboveNavbar;

  @override
  double getOffsetY(
    ScaffoldPrelayoutGeometry scaffoldGeometry,
    double adjustment,
  ) {
    final double contentBottom = scaffoldGeometry.contentBottom;
    final double fabHeight = scaffoldGeometry.floatingActionButtonSize.height;
    return contentBottom - fabHeight - offsetAboveNavbar;
  }

  @override
  String toString() => 'FloatingBottomNavbar.centerElevatedLocation';
}

class FloatingBottomNavbar extends StatelessWidget {
  const FloatingBottomNavbar({
    super.key,
    required this.currentIndex,
    required this.onTap,
    this.onCenterActionTap,
    this.centerActionTooltip = 'Add Product',
    this.items,
    this.activeColor = const Color(0xFF1A1851),
    this.inactiveColor = const Color(0x9E1A1851),
    this.backgroundColor = Colors.white,
    this.selectionColor = const Color(0xFF1A1851),
  });

  final int currentIndex;
  final ValueChanged<int> onTap;
  final VoidCallback? onCenterActionTap;
  final String centerActionTooltip;
  final List<FloatingBottomNavbarItem>? items;
  final Color activeColor;
  final Color inactiveColor;
  final Color backgroundColor;
  final Color selectionColor;

  static const double _centerActionRise = 16;
  static const double _centerActionDiameter = 56;

  static const FloatingActionButtonLocation centerElevatedLocation =
      CenterElevatedNavbarLocation(offsetAboveNavbar: 12.0);

  /// Default 5 items when no center action button is embedded.
  /// Iconsax outline/filled pairs keep selected navigation visually consistent.
  static const List<FloatingBottomNavbarItem> default5Items = [
    FloatingBottomNavbarItem(
      label: 'Home',
      icon: Iconsax.home_copy,
      activeIcon: Iconsax.home,
      activeIconWidget: HomeNavigationIcon(),
      iconWidget: HomeNavigationIcon(outlined: true),
    ),
    FloatingBottomNavbarItem(
      label: 'Marketplace',
      icon: Iconsax.shop_copy,
      activeIcon: Iconsax.shop,
    ),
    FloatingBottomNavbarItem(
      label: 'Services',
      icon: Iconsax.briefcase_copy,
      activeIcon: Iconsax.briefcase,
    ),
    FloatingBottomNavbarItem(
      label: 'Facilities',
      icon: Iconsax.building_copy,
      activeIcon: Iconsax.building,
    ),
    FloatingBottomNavbarItem(
      label: 'Profile',
      icon: Iconsax.user_copy,
      activeIcon: Iconsax.user,
    ),
  ];

  /// Seller destinations surround an action; indices still match root pages0-3.
  static const List<FloatingBottomNavbarItem> defaultCenterActionItems = [
    FloatingBottomNavbarItem(
      label: 'Home',
      icon: Iconsax.home_copy,
      activeIcon: Iconsax.home,
      activeIconWidget: HomeNavigationIcon(),
      iconWidget: HomeNavigationIcon(outlined: true),
    ),
    FloatingBottomNavbarItem(
      label: 'Marketplace',
      icon: Iconsax.shop_copy,
      activeIcon: Iconsax.shop,
    ),
    FloatingBottomNavbarItem(
      label: 'Services',
      icon: Iconsax.briefcase_copy,
      activeIcon: Iconsax.briefcase,
    ),
    FloatingBottomNavbarItem(
      label: 'Facilities',
      icon: Iconsax.building_copy,
      activeIcon: Iconsax.building,
    ),
  ];

  static const List<FloatingBottomNavbarItem> defaultItems = default5Items;

  List<FloatingBottomNavbarItem> get effectiveItems =>
      items ??
      (onCenterActionTap != null ? defaultCenterActionItems : default5Items);

  /// Institutional center add button with white circle background and deep navy plus icon.
  static Widget buildCenterAddButton({
    required VoidCallback onTap,
    String tooltip = 'Add Product',
    Color backgroundColor = Colors.white,
    Color foregroundColor = const Color(0xFF1A1851),
    double size = 44,
  }) {
    return Semantics(
      button: true,
      label: tooltip,
      child: Tooltip(
        message: tooltip,
        child: Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: backgroundColor,
            shape: BoxShape.circle,
            border: Border.all(color: foregroundColor, width: 2.0),
            boxShadow: const [
              BoxShadow(
                color: Color(0x1F1A1851),
                blurRadius: 6,
                offset: Offset(0, 2),
                spreadRadius: 0,
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            shape: const CircleBorder(),
            child: InkWell(
              key: const Key('navbar-center-add-button'),
              customBorder: const CircleBorder(),
              splashColor: foregroundColor.withValues(alpha: 0.12),
              highlightColor: Colors.black.withValues(alpha: 0.04),
              onTap: onTap,
              child: Center(
                child: IconTheme(
                  data: IconThemeData(
                    color: foregroundColor,
                    size: size * 0.54,
                  ),
                  child: const AddProductNavigationIcon(),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(
    BuildContext context,
    int index,
    FloatingBottomNavbarItem item, {
    double topInset = 0,
  }) {
    final isSelected = index == currentIndex;
    final customIcon = isSelected ? item.activeIconWidget : item.iconWidget;
    final reduceMotion = MediaQuery.disableAnimationsOf(context);
    final duration = reduceMotion
        ? Duration.zero
        : const Duration(milliseconds: 220);
    final labelStyle = TextStyle(
      fontFamily: 'Poppins',
      fontSize: 11,
      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
      color: isSelected ? activeColor : inactiveColor,
      letterSpacing: -0.1,
      height: 1.15,
    );
    return Expanded(
      child: Semantics(
        key: ValueKey('navbar-semantics-$index'),
        button: true,
        selected: isSelected,
        label: item.label,
        excludeSemantics: true,
        onTap: () => onTap(index),
        child: Tooltip(
          message: item.label,
          child: InkResponse(
            key: ValueKey('navbar-item-$index'),
            onTap: () => onTap(index),
            containedInkWell: true,
            splashColor: selectionColor.withValues(alpha: 0.08),
            hoverColor: activeColor.withValues(alpha: 0.04),
            focusColor: selectionColor.withValues(alpha: 0.12),
            highlightColor: Colors.transparent,
            child: Padding(
              padding: EdgeInsets.only(top: topInset),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  TweenAnimationBuilder<double>(
                    key: ValueKey('navbar-motion-$index'),
                    tween: Tween<double>(end: isSelected ? 1 : 0),
                    duration: duration,
                    curve: Curves.easeOutCubic,
                    builder: (context, amount, child) => Transform.translate(
                      key: ValueKey('navbar-shift-$index'),
                      offset: Offset(0, -2 * amount),
                      child: Transform.scale(
                        scale: 1 + .08 * amount,
                        child: child,
                      ),
                    ),
                    child: SizedBox(
                      width: 28,
                      height: 28,
                      child: AnimatedSwitcher(
                        duration: reduceMotion
                            ? Duration.zero
                            : const Duration(milliseconds: 140),
                        switchInCurve: Curves.easeOutCubic,
                        switchOutCurve: Curves.easeInCubic,
                        child: KeyedSubtree(
                          key: ValueKey('navbar-glyph-$index-$isSelected'),
                          child: customIcon != null
                              ? IconTheme(
                                  key: ValueKey('navbar-icon-$index'),
                                  data: IconThemeData(
                                    size: 20,
                                    color: isSelected
                                        ? activeColor
                                        : inactiveColor,
                                  ),
                                  child: customIcon,
                                )
                              : Icon(
                                  isSelected
                                      ? item.effectiveActiveIcon
                                      : item.icon,
                                  key: ValueKey('navbar-icon-$index'),
                                  size: 20,
                                  color: isSelected
                                      ? activeColor
                                      : inactiveColor,
                                ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                  AnimatedDefaultTextStyle(
                    duration: duration,
                    style: labelStyle,
                    child: FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        item.label,
                        // As in Material NavigationBar, full scalable names remain
                        // available in tooltips and semantics on narrow phones.
                        textScaler: TextScaler.noScaling,
                        maxLines: 1,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCenterActionButton(double navHeight) => Expanded(
    child: Semantics(
      button: true,
      label: centerActionTooltip,
      excludeSemantics: true,
      onTap: onCenterActionTap,
      child: Tooltip(
        message: centerActionTooltip,
        child: InkResponse(
          key: const Key('navbar-center-add-button'),
          onTap: onCenterActionTap,
          containedInkWell: true,
          highlightColor: Colors.transparent,
          splashColor: activeColor.withValues(alpha: .08),
          child: Padding(
            // Follow extra bar height at large text settings so all labels
            // retain the same baseline instead of leaving the action higher.
            padding: EdgeInsets.only(top: math.max(0.0, (navHeight - 68) / 2)),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                Container(
                  key: const Key('navbar-center-add-circle'),
                  width: _centerActionDiameter,
                  height: _centerActionDiameter,
                  decoration: BoxDecoration(
                    color: const Color(0xFFFCB315),
                    shape: BoxShape.circle,
                  ),
                  child: IconTheme(
                    data: IconThemeData(color: activeColor, size: 16),
                    child: const AddProductNavigationIcon(),
                  ),
                ),
                const SizedBox(height: 4),
                FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    centerActionTooltip,
                    textScaler: TextScaler.noScaling,
                    maxLines: 1,
                    style: TextStyle(
                      fontFamily: 'Poppins',
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      height: 1.15,
                      color: activeColor,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final list = effectiveItems;
    final hasCenterAction = onCenterActionTap != null && list.length == 4;
    // Reserve the raised action in the actual layout, including its hit area.
    // Regular accounts retain their existing flat five-destination bar.
    final topInset = hasCenterAction ? _centerActionRise : 0.0;
    final navHeight = math.max(
      68.0,
      45 + MediaQuery.textScalerOf(context).scale(11) * 1.15,
    );

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle(
        systemNavigationBarColor: backgroundColor,
        systemNavigationBarIconBrightness: Brightness.dark,
        systemNavigationBarDividerColor: Colors.transparent,
        systemNavigationBarContrastEnforced: false,
      ),
      child: Container(
        key: const Key('floating-navbar-pill'),
        child: Stack(
          children: [
            Positioned.fill(
              top: topInset,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: backgroundColor,
                  border: const Border(
                    top: BorderSide(color: Color(0xFFECEEF3)),
                  ),
                ),
              ),
            ),
            Material(
              type: MaterialType.transparency,
              child: SafeArea(
                top: false,
                child: SizedBox(
                  height: navHeight + topInset,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    // Stretch so each tab fills the full bar height and the whole
                    // column is tappable.
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: hasCenterAction
                        ? [
                            _buildNavItem(
                              context,
                              0,
                              list[0],
                              topInset: topInset,
                            ),
                            _buildNavItem(
                              context,
                              1,
                              list[1],
                              topInset: topInset,
                            ),
                            _buildCenterActionButton(navHeight),
                            _buildNavItem(
                              context,
                              2,
                              list[2],
                              topInset: topInset,
                            ),
                            _buildNavItem(
                              context,
                              3,
                              list[3],
                              topInset: topInset,
                            ),
                          ]
                        : List.generate(
                            list.length,
                            (index) =>
                                _buildNavItem(context, index, list[index]),
                          ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
