import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../screens/cart_screen.dart';
import '../services/cart_service.dart';

class CartIconButton extends StatelessWidget {
  const CartIconButton({
    super.key,
    this.iconColor = const Color(0xFF142B47),
    this.badgeKey,
    this.onPressed,
  });

  final Color iconColor;
  final GlobalKey? badgeKey;
  final VoidCallback? onPressed;

  void _openCart(BuildContext context) {
    if (onPressed != null) {
      onPressed!();
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const CartScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: CartService.instance,
      builder: (context, _) {
        final count = CartService.instance.itemCount;
        return Stack(
          clipBehavior: Clip.none,
          children: [
            IconButton(
              key: badgeKey ?? CartService.cartIconKey,
              onPressed: () => _openCart(context),
              icon: Icon(LucideIcons.shoppingBag, color: iconColor),
            ),
            if (count > 0)
              Positioned(
                right: 4,
                top: 4,
                child: IgnorePointer(
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    constraints: const BoxConstraints(minWidth: 18, minHeight: 18),
                    decoration: const BoxDecoration(
                      color: Color(0xFFFCB316),
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      count > 99 ? '99+' : '$count',
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF142B47),
                      ),
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
