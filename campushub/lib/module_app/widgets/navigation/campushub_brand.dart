import 'package:flutter/material.dart';
import '../home/home_preview_cards.dart';

/// The same bundled mark and wordmark on regular Home and seller headers.
class CampusHubBrand extends StatelessWidget {
  const CampusHubBrand({
    super.key,
    this.onNavy = false,
    this.logoKey,
    this.wordmarkKey,
  });
  final bool onNavy;
  final Key? logoKey, wordmarkKey;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Image.asset(
        onNavy ? 'assets/img/logo_dark.png' : 'assets/img/logo_light.png',
        key: logoKey,
        width: 26,
        height: 30,
        fit: BoxFit.contain,
        semanticLabel: 'CampusHub logo',
      ),
      const SizedBox(width: 8),
      Flexible(
        child: FittedBox(
          fit: BoxFit.scaleDown,
          alignment: Alignment.centerLeft,
          child: Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: 'Campus',
                  style: TextStyle(
                    color: onNavy ? Colors.white : HomeAppColors.navy,
                  ),
                ),
                const TextSpan(
                  text: 'Hub',
                  style: TextStyle(color: HomeAppColors.gold),
                ),
              ],
            ),
            key: wordmarkKey,
            style: const TextStyle(
              fontFamily: 'SugarPie',
              fontSize: 24,
              fontWeight: FontWeight.w400,
              letterSpacing: 0,
            ),
          ),
        ),
      ),
    ],
  );
}
