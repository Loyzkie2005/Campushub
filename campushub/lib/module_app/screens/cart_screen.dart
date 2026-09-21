import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../models/cart_item.dart';
import '../services/cart_service.dart';
import '../services/order_service.dart';
import '../session/session_service.dart';
import '../widgets/order_summary_widgets.dart';
import '../widgets/product_image.dart';
import 'checkout_screen.dart';

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});

  static const Color navy = Color(0xFF1A1851);
  static const Color gold = Color(0xFFFCB316);
  static const Color pageBg = Color(0xFFF5F7FB);

  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  @override
  void initState() {
    super.initState();
    unawaited(CartService.instance.load());
  }

  Future<void> _checkoutItem(CartItem item) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => CheckoutScreen(
          productId: item.productId,
          productName: item.productName,
          basePrice: item.basePrice,
          selection: item.buySelection,
          imageUrl: item.imageUrl,
          category: item.category,
          sellerName: item.sellerName,
          sellerContact: item.sellerContact,
          onOrderPlaced: () => CartService.instance.removeItem(item.id),
        ),
      ),
    );
  }

  Future<void> _checkoutAll() async {
    final items = List<CartItem>.from(CartService.instance.items);
    if (items.isEmpty) return;

    final placed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => _CartBulkCheckoutScreen(items: items)),
    );

    if (placed == true && mounted) {
      await CartService.instance.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: CartScreen.pageBg,
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: CartScreen.navy,
        elevation: 0,
        centerTitle: true,
        title: const Text(
          'Cart',
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
        actions: [
          ListenableBuilder(
            listenable: CartService.instance,
            builder: (context, _) {
              if (CartService.instance.isEmpty) return const SizedBox.shrink();
              return TextButton(
                onPressed: () => CartService.instance.clear(),
                child: const Text(
                  'Clear',
                  style: TextStyle(
                    color: Color(0xFFDC2626),
                    fontWeight: FontWeight.w800,
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: CartService.instance,
        builder: (context, _) {
          final items = CartService.instance.items;
          if (items.isEmpty) return const _EmptyCartView();

          return Column(
            children: [
              Expanded(
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return _CartItemCard(
                      item: item,
                      onQuantityChanged: (qty) =>
                          CartService.instance.updateQuantity(item.id, qty),
                      onRemove: () => CartService.instance.removeItem(item.id),
                      onCheckout: () => _checkoutItem(item),
                    );
                  },
                ),
              ),
              _CartSummaryBar(
                subtotal: CartService.instance.subtotal,
                itemCount: CartService.instance.itemCount,
                onCheckoutAll: _checkoutAll,
              ),
            ],
          );
        },
      ),
    );
  }
}

class _EmptyCartView extends StatelessWidget {
  const _EmptyCartView();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 96,
              height: 96,
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFFE6EBF2)),
              ),
              child: const Icon(
                LucideIcons.shoppingBag,
                size: 42,
                color: Color(0xFF94A3B8),
              ),
            ),
            const SizedBox(height: 18),
            const Text(
              'Your cart is empty',
              style: TextStyle(
                color: Color(0xFF0F172A),
                fontSize: 18,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Browse marketplace products and add items to your cart.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFF64748B), height: 1.4),
            ),
            const SizedBox(height: 22),
            OutlinedButton(
              onPressed: () => Navigator.of(context).pop(),
              style: OutlinedButton.styleFrom(
                foregroundColor: CartScreen.navy,
                side: const BorderSide(color: CartScreen.navy),
                padding: const EdgeInsets.symmetric(
                  horizontal: 22,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              child: const Text(
                'Continue Shopping',
                style: TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CartItemCard extends StatelessWidget {
  const _CartItemCard({
    required this.item,
    required this.onQuantityChanged,
    required this.onRemove,
    required this.onCheckout,
  });

  final CartItem item;
  final ValueChanged<int> onQuantityChanged;
  final VoidCallback onRemove;
  final VoidCallback onCheckout;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE6EBF2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: SizedBox(
                  width: 72,
                  height: 72,
                  child: ProductImage(imageUrl: item.imageUrl),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.productName,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF0F172A),
                        fontWeight: FontWeight.w900,
                        fontSize: 15,
                      ),
                    ),
                    if (item.summary.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        item.summary,
                        style: const TextStyle(
                          color: Color(0xFF64748B),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                    const SizedBox(height: 6),
                    Text(
                      item.unitPriceLabel,
                      style: const TextStyle(
                        color: Color(0xFF1A56DB),
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                onPressed: onRemove,
                icon: const Icon(Icons.delete_outline_rounded),
                color: const Color(0xFFDC2626),
                tooltip: 'Remove',
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _CartQuantityStepper(
                quantity: item.quantity,
                onMinus: () => onQuantityChanged(item.quantity - 1),
                onPlus: () => onQuantityChanged(item.quantity + 1),
              ),
              const Spacer(),
              Text(
                item.totalPriceLabel,
                style: const TextStyle(
                  color: Color(0xFF0F172A),
                  fontWeight: FontWeight.w900,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: onCheckout,
              style: OutlinedButton.styleFrom(
                foregroundColor: CartScreen.navy,
                side: const BorderSide(color: Color(0xFFCBD5E1)),
                padding: const EdgeInsets.symmetric(vertical: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              child: const Text(
                'Checkout Item',
                style: TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CartQuantityStepper extends StatelessWidget {
  const _CartQuantityStepper({
    required this.quantity,
    required this.onMinus,
    required this.onPlus,
  });

  final int quantity;
  final VoidCallback onMinus;
  final VoidCallback onPlus;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _StepperButton(icon: LucideIcons.minus, onTap: onMinus),
          SizedBox(
            width: 36,
            child: Text(
              '$quantity',
              textAlign: TextAlign.center,
              style: const TextStyle(fontWeight: FontWeight.w900),
            ),
          ),
          _StepperButton(icon: LucideIcons.plus, onTap: onPlus),
        ],
      ),
    );
  }
}

class _StepperButton extends StatelessWidget {
  const _StepperButton({required this.icon, required this.onTap});

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: SizedBox(
        width: 34,
        height: 32,
        child: Icon(icon, size: 16, color: const Color(0xFF142B47)),
      ),
    );
  }
}

class _CartSummaryBar extends StatelessWidget {
  const _CartSummaryBar({
    required this.subtotal,
    required this.itemCount,
    required this.onCheckoutAll,
  });

  final double subtotal;
  final int itemCount;
  final VoidCallback onCheckoutAll;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFE6EBF2))),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Text(
                  'Subtotal ($itemCount item${itemCount == 1 ? '' : 's'})',
                  style: const TextStyle(
                    color: Color(0xFF64748B),
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const Spacer(),
                Text(
                  '₱${subtotal.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: Color(0xFF0F172A),
                    fontWeight: FontWeight.w900,
                    fontSize: 18,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: onCheckoutAll,
                style: ElevatedButton.styleFrom(
                  backgroundColor: CartScreen.navy,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  'Checkout All',
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CartBulkCheckoutScreen extends StatefulWidget {
  const _CartBulkCheckoutScreen({required this.items});

  final List<CartItem> items;

  @override
  State<_CartBulkCheckoutScreen> createState() =>
      _CartBulkCheckoutScreenState();
}

class _CartBulkCheckoutScreenState extends State<_CartBulkCheckoutScreen> {
  bool _showPlacedOrders = false;
  bool _isPlacing = false;
  final _sellerMessageController = TextEditingController();
  late final List<CartItem> _items = List.of(widget.items);

  double get _subtotal =>
      _items.fold(0, (sum, item) => sum + item.totalPrice);

  @override
  void dispose() {
    _sellerMessageController.dispose();
    super.dispose();
  }

  List<OrderSummaryLineItem> get _summaryItems => _items
      .map(
        (item) => OrderSummaryLineItem(
          productName: item.productName,
          imageUrl: item.imageUrl,
          quantity: item.quantity,
          unitPrice: item.unitPrice,
          sellerName: item.sellerName,
          selections: item.buySelection.selections,
        ),
      )
      .toList(growable: false);

  void _updateItemQuantity(int index, int newQty) {
    if (newQty < 1 || index >= _items.length) return;
    setState(() {
      _items[index] = _items[index].copyWith(quantity: newQty);
    });
  }

  Future<void> _placeAllOrders() async {
    if (_isPlacing || _showPlacedOrders) return;
    setState(() => _isPlacing = true);
    final user = await SessionService.loadUser();

    for (final item in _items) {
      await OrderService.placeOrder(
        order: {
          'product_id': item.productId,
          'product_name': item.productName,
          'category': item.category,
          'buyer_user_id': user?.id,
          'buyer_name': user?.fullName ?? user?.studentId ?? '',
          'buyer_email': user?.email ?? '',
          'seller_name': item.sellerName,
          'seller_contact': item.sellerContact,
          'message_to_seller': _sellerMessageController.text.trim(),
          'option': item.summary,
          'customization': item.buySelection.customizationPayload,
          'quantity': item.quantity,
          'unit_price': item.unitPrice,
          'total_price': item.totalPrice,
          'image_url': item.imageUrl,
        },
      );
    }

    if (!mounted) return;
    setState(() {
      _isPlacing = false;
      _showPlacedOrders = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _showPlacedOrders
          ? OrderSummaryConstants.pageBg
          : OrderSummaryConstants.checkoutBg,
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: CartScreen.navy,
        elevation: 0,
        automaticallyImplyLeading: !_showPlacedOrders,
        centerTitle: true,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
        title: Text(
          _showPlacedOrders ? 'Review' : 'Checkout',
          style: GoogleFonts.notoSans(
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      body: Theme(
        data: Theme.of(context).copyWith(
          textTheme: GoogleFonts.notoSansTextTheme(Theme.of(context).textTheme),
        ),
        child: SafeArea(
          top: false,
          child: Padding(
            padding: _showPlacedOrders
                ? const EdgeInsets.all(16)
                : EdgeInsets.zero,
            child: _showPlacedOrders
                ? PlacedOrdersReviewView(
                    items: _summaryItems,
                    subtotal: _subtotal,
                    successTitle: 'Orders Placed',
                    successMessage:
                        'Your cart items were sent to the admin orders section.',
                    onDone: () => Navigator.of(context).pop(true),
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: ListView(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          children: [
                            const CheckoutBuyerDetails(),
                            OrderSummaryCard(
                              showCheckoutHeader: true,
                              items: _summaryItems,
                              subtotal: _subtotal,
                              sellerMessageController: _sellerMessageController,
                              onQuantityChanged: _updateItemQuantity,
                            ),
                          ],
                        ),
                      ),
                      Container(
                        color: Colors.white,
                        padding: const EdgeInsets.all(16),
                        child: OrderSummaryPrimaryButton(
                          label: 'Place Order',
                          isLoading: _isPlacing,
                          onPressed: _placeAllOrders,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}
