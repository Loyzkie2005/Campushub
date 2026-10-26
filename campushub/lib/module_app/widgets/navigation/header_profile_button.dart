import 'package:iconsax_flutter/iconsax_flutter.dart';
import 'package:flutter/material.dart';

import '../../services/auth_service.dart';
import '../home/home_preview_cards.dart';

/// Reuses the signed-in identity without inventing a profile image URL.
class HeaderProfileButton extends StatelessWidget {
  const HeaderProfileButton({super.key, this.user, required this.onPressed});

  final AuthUser? user;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final name = user?.fullName.trim() ?? '';
    return IconButton(
      tooltip: 'Open Profile',
      onPressed: onPressed,
      constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
      icon: CircleAvatar(
        radius: 17,
        backgroundColor: HomeAppColors.navy,
        foregroundColor: Colors.white,
        child: name.isEmpty
            ? const Icon(Iconsax.user_copy, size: 20)
            : Text(
                name.characters.first.toUpperCase(),
                style: const TextStyle(
                  fontFamily: 'Poppins',
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
      ),
    );
  }
}
