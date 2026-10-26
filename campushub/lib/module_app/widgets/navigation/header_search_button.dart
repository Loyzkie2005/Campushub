import 'package:flutter/material.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';

import '../../screens/search_page.dart';
import '../home/home_preview_cards.dart';

/// Compact entry to the existing catalog Search page from the shared header.
class HeaderSearchButton extends StatelessWidget {
  const HeaderSearchButton({super.key, this.onPressed});

  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: 'Search',
    constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
    icon: const Icon(Iconsax.search_normal_1_copy, color: HomeAppColors.navy),
    onPressed:
        onPressed ??
        () => Navigator.of(
          context,
        ).push(MaterialPageRoute<void>(builder: (_) => const SearchPage())),
  );
}
