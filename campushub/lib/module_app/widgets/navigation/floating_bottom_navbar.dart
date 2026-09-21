import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:lucide_icons/lucide_icons.dart';

class FloatingBottomNavbarItem {
  const FloatingBottomNavbarItem({
    required this.label,
    required this.icon,
    this.activeIcon,
  });

  final String label;
  final IconData icon;
  final IconData? activeIcon;

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
    this.inactiveColor = const Color(0xFF64748B),
    this.backgroundColor = Colors.white,
  });

  final int currentIndex;
  final ValueChanged<int> onTap;
  final VoidCallback? onCenterActionTap;
  final String centerActionTooltip;
  final List<FloatingBottomNavbarItem>? items;
  final Color activeColor;
  final Color inactiveColor;
  final Color backgroundColor;

  static const FloatingActionButtonLocation centerElevatedLocation =
      CenterElevatedNavbarLocation(offsetAboveNavbar: 12.0);

  /// Default 5 items when no center action button is embedded.
  static const List<FloatingBottomNavbarItem> default5Items = [
    FloatingBottomNavbarItem(label: 'Home', icon: LucideIcons.home),
    FloatingBottomNavbarItem(label: 'Shop', icon: LucideIcons.shoppingBag),
    FloatingBottomNavbarItem(label: 'Facilities', icon: LucideIcons.building2),
    FloatingBottomNavbarItem(
      label: 'Messages',
      icon: LucideIcons.messageSquare,
    ),
    FloatingBottomNavbarItem(label: 'Profile', icon: LucideIcons.user),
  ];

  /// Default 4 destination items when the center action '+' is embedded inside the navbar.
  static const List<FloatingBottomNavbarItem> defaultCenterActionItems = [
    FloatingBottomNavbarItem(label: 'Home', icon: LucideIcons.home),
    FloatingBottomNavbarItem(label: 'Shop', icon: LucideIcons.shoppingBag),
    FloatingBottomNavbarItem(label: 'Facilities', icon: LucideIcons.building2),
    FloatingBottomNavbarItem(label: 'Profile', icon: LucideIcons.user),
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
                child: Icon(
                  LucideIcons.plus,
                  color: foregroundColor,
                  size: size * 0.54,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, FloatingBottomNavbarItem item) {
    final isSelected = index == currentIndex;
    return Expanded(
      child: Semantics(
        button: true,
        selected: isSelected,
        label: item.label,
        child: Tooltip(
          message: item.label,
          child: InkResponse(
            key: ValueKey('navbar-item-$index'),
            onTap: () => onTap(index),
            splashColor: activeColor.withValues(alpha: 0.10),
            highlightColor: Colors.transparent,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                AnimatedScale(
                  scale: isSelected ? 1.06 : 1.0,
                  duration: const Duration(milliseconds: 200),
                  curve: Curves.easeOutCubic,
                  child: Icon(
                    isSelected ? item.effectiveActiveIcon : item.icon,
                    size: 23,
                    color: isSelected ? activeColor : inactiveColor,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  item.label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                    color: isSelected ? activeColor : inactiveColor,
                    letterSpacing: -0.2,
                    height: 1.15,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCenterActionButton() {
    return Expanded(
      child: Semantics(
        button: true,
        label: centerActionTooltip,
        child: Tooltip(
          message: centerActionTooltip,
          child: Center(
            child: Container(
              key: const Key('navbar-center-add-circle'),
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF1A1851), width: 2.0),
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
                  splashColor: const Color(0xFF1A1851).withValues(alpha: 0.12),
                  highlightColor: Colors.black.withValues(alpha: 0.04),
                  onTap: onCenterActionTap,
                  child: const Center(
                    child: Icon(
                      LucideIcons.plus,
                      color: Color(0xFF1A1851),
                      size: 24,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final list = effectiveItems;
    final hasCenterAction = onCenterActionTap != null && list.length == 4;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle(
        systemNavigationBarColor: backgroundColor,
        systemNavigationBarIconBrightness: Brightness.dark,
        systemNavigationBarDividerColor: Colors.transparent,
        systemNavigationBarContrastEnforced: false,
      ),
      child: Container(
        key: const Key('floating-navbar-pill'),
        decoration: BoxDecoration(
          color: backgroundColor,
          border: const Border(
            top: BorderSide(color: Color(0xFFE2E8F0), width: 1),
          ),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0A1A1851),
              blurRadius: 8,
              offset: Offset(0, -2),
              spreadRadius: 0,
            ),
          ],
        ),
        child: SafeArea(
          top: false,
          child: SizedBox(
            height: 60,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: hasCenterAction
                  ? [
                      _buildNavItem(0, list[0]),
                      _buildNavItem(1, list[1]),
                      _buildCenterActionButton(),
                      _buildNavItem(2, list[2]),
                      _buildNavItem(3, list[3]),
                    ]
                  : List.generate(
                      list.length,
                      (index) => _buildNavItem(index, list[index]),
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
