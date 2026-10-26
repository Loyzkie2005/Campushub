import 'package:flutter/material.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';

import '../../services/auth_service.dart';
import '../../services/chat_service.dart';
import '../profile/profile_widgets.dart';
import '../home/home_preview_cards.dart';

/// Local type roles keep this seller drawer independent from regular Profile.
abstract final class _SellerDrawerStyle {
  static const rowHeight = 52.0;
  static const iconSize = 22.0;
  static const rowRadius = 8.0;
  // Adjust these to change the breathing room around the profile divider.
  static const profileDividerTopSpace = 24.0;
  static const profileDividerBottomSpace = 16.0;

  static TextStyle section() => TextStyle(
    fontFamily: 'Poppins',
    fontSize: 11,
    fontWeight: FontWeight.w700,
    height: 1.4,
    letterSpacing: 0.6,
    color: HomeAppColors.navy.withValues(alpha: .78),
  );

  static TextStyle label({bool selected = false}) => TextStyle(
    fontFamily: 'Poppins',
    fontSize: 14,
    fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
    height: 1.4,
    color: HomeAppColors.navy,
  );
}

enum SellerDestination {
  overview('Dashboard', 'OVERVIEW', Iconsax.element_4_copy),
  products('My Products', 'SELLER MANAGEMENT', Iconsax.box_copy),
  inventory('Inventory', 'SELLER MANAGEMENT', Iconsax.box_2_copy),
  bundles('My Bundles', 'SELLER MANAGEMENT', Iconsax.box_add_copy),
  orders('Orders', 'SELLER MANAGEMENT', Iconsax.bag_2_copy),
  recommendations(
    'Suggested Product Bundles',
    'RECOMMENDATIONS',
    Iconsax.lamp_on_copy,
  ),
  analytics('Sales Analytics', 'REPORTS', Iconsax.chart_2_copy),
  messages('Messages', 'COMMUNICATION', Iconsax.message_copy),
  settings('Account Settings', 'SETTINGS', Iconsax.setting_2_copy);

  const SellerDestination(this.label, this.section, this.icon);
  final String label;
  final String section;
  final IconData icon;
}

/// The existing seller page owns approval checks and routing; this is its drawer.
class SellerDrawer extends StatelessWidget {
  const SellerDrawer({
    super.key,
    required this.user,
    required this.selected,
    required this.onSelected,
    this.onBackToCampusHub,
    this.onProfile,
  });

  final AuthUser user;
  final SellerDestination selected;
  final ValueChanged<SellerDestination> onSelected;
  final VoidCallback? onBackToCampusHub, onProfile;

  static const List<SellerDestination> drawerDestinations = [
    SellerDestination.overview,
    SellerDestination.products,
    SellerDestination.inventory,
    SellerDestination.bundles,
    SellerDestination.orders,
    SellerDestination.recommendations,
    SellerDestination.analytics,
    SellerDestination.messages,
    SellerDestination.settings,
  ];

  Widget _entry(SellerDestination destination) {
    final active = selected == destination;
    final iconColor = active
        ? HomeAppColors.navy
        : HomeAppColors.navy.withValues(alpha: .85);
    final chevronColor = HomeAppColors.navy.withValues(alpha: .64);
    final surfaceColor = active
        ? HomeAppColors.navy.withValues(alpha: .06)
        : Colors.transparent;

    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Semantics(
        selected: active,
        child: Material(
          color: surfaceColor,
          borderRadius: BorderRadius.circular(_SellerDrawerStyle.rowRadius),
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            key: ValueKey('seller-menu-${destination.name}'),
            onTap: () => onSelected(destination),
            child: Container(
              constraints: const BoxConstraints(
                minHeight: _SellerDrawerStyle.rowHeight,
              ),
              decoration: BoxDecoration(
                border: Border(
                  left: BorderSide(
                    width: 3,
                    color: active ? HomeAppColors.gold : Colors.transparent,
                  ),
                ),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  ExcludeSemantics(
                    child: Icon(
                      destination.icon,
                      size: _SellerDrawerStyle.iconSize,
                      color: iconColor,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      destination.label,
                      style: _SellerDrawerStyle.label(selected: active),
                    ),
                  ),
                  if (destination == SellerDestination.messages)
                    AnimatedBuilder(
                      animation: ChatService.instance,
                      builder: (context, _) {
                        final unread = ChatService.instance.conversations
                            .fold<int>(
                              0,
                              (sum, conversation) =>
                                  sum + conversation.unreadCount,
                            );
                        if (unread <= 0) return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(left: 8),
                          child: Badge(
                            backgroundColor: HomeAppColors.gold,
                            textColor: HomeAppColors.navy,
                            label: Text(unread > 99 ? '99+' : '$unread'),
                          ),
                        );
                      },
                    ),
                  const SizedBox(width: 8),
                  ExcludeSemantics(
                    child: Icon(
                      Iconsax.arrow_right_3_copy,
                      size: 18,
                      color: chevronColor,
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

  @override
  Widget build(BuildContext context) {
    final name = user.fullName.trim();
    return Drawer(
      semanticLabel: 'Seller navigation',
      width: (MediaQuery.sizeOf(context).width * .88).clamp(280.0, 360.0),
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: const RoundedRectangleBorder(),
      child: SafeArea(
        child: ListView(
          key: const ValueKey('seller-navigation-list'),
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    tooltip: 'Open Profile',
                    onPressed: onProfile,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(
                      minWidth: 56,
                      minHeight: 56,
                    ),
                    icon: Semantics(
                      label: name.isEmpty
                          ? 'Profile avatar'
                          : 'Profile avatar for $name',
                      image: true,
                      excludeSemantics: true,
                      child: CircleAvatar(
                        key: const ValueKey('seller-profile-avatar'),
                        radius: 28,
                        backgroundColor: HomeAppColors.navy,
                        foregroundColor: Colors.white,
                        child: name.isEmpty
                            ? const Icon(Iconsax.user_copy, size: 28)
                            : Text(
                                name.characters.first.toUpperCase(),
                                style: const TextStyle(
                                  fontFamily: 'Poppins',
                                  fontSize: 22,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    user.fullName,
                    style: ProfileStyle.identityText(
                      17,
                      weight: 700,
                      color: HomeAppColors.navy,
                    ),
                  ),
                  if (user.program.trim().isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      user.program,
                      style: ProfileStyle.identityText(
                        12,
                        weight: 500,
                        color: HomeAppColors.navy,
                      ),
                    ),
                  ],
                  if (user.yearSection.trim().isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Year / Section: ${user.yearSection}',
                      style: ProfileStyle.identityText(
                        12,
                        weight: 500,
                        color: HomeAppColors.navy.withValues(alpha: .78),
                      ),
                    ),
                  ],
                  if (user.email.trim().isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      user.email,
                      key: const ValueKey('seller-profile-email'),
                      style: TextStyle(
                        fontFamily: 'Poppins',
                        fontSize: 12,
                        height: 1.5,
                        color: HomeAppColors.navy.withValues(alpha: .78),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.only(
                top: _SellerDrawerStyle.profileDividerTopSpace,
                bottom: _SellerDrawerStyle.profileDividerBottomSpace,
              ),
              child: Divider(
                key: const ValueKey('seller-profile-divider'),
                height: 1,
                color: HomeAppColors.navy.withValues(alpha: .12),
              ),
            ),
            for (final section
                in drawerDestinations.map((item) => item.section).toSet()) ...[
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 20, 4, 8),
                child: Semantics(
                  header: true,
                  child: Text(section, style: _SellerDrawerStyle.section()),
                ),
              ),
              for (final item in drawerDestinations.where(
                (item) => item.section == section,
              ))
                _entry(item),
            ],
          ],
        ),
      ),
    );
  }
}
