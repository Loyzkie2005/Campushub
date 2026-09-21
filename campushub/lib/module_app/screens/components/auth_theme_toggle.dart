import 'package:flutter/material.dart';

import '../../services/theme_service.dart';

class AuthThemeToggle extends StatelessWidget {
  const AuthThemeToggle({super.key});

  static const _navy = Color(0xFF1A1851);
  static const _gold = Color(0xFFFCB316);

  @override
  Widget build(BuildContext context) {
    final controller = ThemeService.instance;

    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final isLightMode = controller.isLightMode;

        return IconButton(
          tooltip: isLightMode ? 'Switch to dark mode' : 'Switch to light mode',
          onPressed: () => controller.setLightMode(!isLightMode),
          icon: AnimatedSwitcher(
            duration: const Duration(milliseconds: 180),
            transitionBuilder: (child, animation) => RotationTransition(
              turns: animation,
              child: FadeTransition(opacity: animation, child: child),
            ),
            child: Icon(
              isLightMode
                  ? Icons.light_mode_outlined
                  : Icons.dark_mode_outlined,
              key: ValueKey(isLightMode),
              size: 22,
            ),
          ),
          color: _navy,
          style: IconButton.styleFrom(
            backgroundColor: isLightMode ? Colors.white : _gold,
            side: BorderSide(
              color: isLightMode ? _navy.withValues(alpha: 0.28) : _gold,
            ),
            shape: const CircleBorder(),
            minimumSize: const Size(40, 40),
            maximumSize: const Size(40, 40),
            padding: EdgeInsets.zero,
          ),
        );
      },
    );
  }
}
