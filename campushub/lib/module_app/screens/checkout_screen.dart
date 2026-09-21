import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../models/product_customization.dart';
import '../services/order_service.dart';
import '../session/session_service.dart';
import '../widgets/order_summary_widgets.dart';

class CheckoutScreen extends StatefulWidget {
  const CheckoutScreen({
    super.key,
    required this.productId,
    required this.productName,
    required this.basePrice,
    required this.selection,
    required this.imageUrl,
    required this.category,
    required this.sellerName,
    required this.sellerContact,
    this.onOrderPlaced,
  });

  final int? productId;
  final String productName;
  final double basePrice;
  final BuySelection selection;
  final String imageUrl;
  final String category;
  final String sellerName;
  final String sellerContact;
  final VoidCallback? onOrderPlaced;

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  bool _showPlacedOrders = false;
  bool _isPlacing = false;
  final _sellerMessageController = TextEditingController();

  late int _quantity = widget.selection.quantity;

  late List<OrderSummaryLineItem> _lineItems = [
    OrderSummaryLineItem(
      productName: widget.productName,
      sellerName: widget.sellerName,
      imageUrl: widget.imageUrl,
      quantity: _quantity,
      unitPrice: widget.selection.unitPrice,
      selections: widget.selection.selections,
    ),
  ];

  double get _subtotal => widget.selection.unitPrice * _quantity;

  double get _grandTotal => _subtotal;

  void _updateQuantity(int newQty) {
    if (newQty < 1) return;
    setState(() {
      _quantity = newQty;
      _lineItems = [
        OrderSummaryLineItem(
          productName: widget.productName,
          sellerName: widget.sellerName,
          imageUrl: widget.imageUrl,
          quantity: newQty,
          unitPrice: widget.selection.unitPrice,
          selections: widget.selection.selections,
        ),
      ];
    });
  }

  @override
  void dispose() {
    _sellerMessageController.dispose();
    super.dispose();
  }

  Future<void> _placeOrder() async {
    if (_isPlacing || _showPlacedOrders) return;
    setState(() => _isPlacing = true);
    final user = await SessionService.loadUser();
    await OrderService.placeOrder(
      order: {
        'product_id': widget.productId,
        'product_name': widget.productName,
        'category': widget.category,
        'buyer_user_id': user?.id,
        'buyer_name': user?.fullName ?? user?.studentId ?? '',
        'buyer_email': user?.email ?? '',
        'seller_name': widget.sellerName,
        'seller_contact': widget.sellerContact,
        'message_to_seller': _sellerMessageController.text.trim(),
        'option': widget.selection.summary,
        'customization': widget.selection.customizationPayload,
        'quantity': _quantity,
        'unit_price': widget.selection.unitPrice,
        'total_price': _grandTotal,
        'image_url': widget.imageUrl,
      },
    );
    if (!mounted) return;
    widget.onOrderPlaced?.call();
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
        foregroundColor: OrderSummaryConstants.navy,
        elevation: 0,
        centerTitle: true,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
        automaticallyImplyLeading: !_showPlacedOrders,
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
                    items: _lineItems,
                    subtotal: _subtotal,
                    onDone: () => Navigator.of(context).pop(),
                  )
                : _CheckoutSummaryView(
                    items: _lineItems,
                    subtotal: _subtotal,
                    sellerMessageController: _sellerMessageController,
                    isPlacing: _isPlacing,
                    onPlaceOrder: _placeOrder,
                    onQuantityChanged: _updateQuantity,
                  ),
          ),
        ),
      ),
    );
  }
}

class _CheckoutSummaryView extends StatelessWidget {
  const _CheckoutSummaryView({
    required this.items,
    required this.subtotal,
    required this.sellerMessageController,
    required this.isPlacing,
    required this.onPlaceOrder,
    this.onQuantityChanged,
  });

  final List<OrderSummaryLineItem> items;
  final double subtotal;
  final TextEditingController sellerMessageController;
  final bool isPlacing;
  final VoidCallback onPlaceOrder;
  final ValueChanged<int>? onQuantityChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.symmetric(vertical: 12),
            children: [
              const CheckoutBuyerDetails(),
              OrderSummaryCard(
                showCheckoutHeader: true,
                items: items,
                subtotal: subtotal,
                sellerMessageController: sellerMessageController,
                onQuantityChanged: onQuantityChanged != null
                    ? (_, qty) => onQuantityChanged!(qty)
                    : null,
              ),
            ],
          ),
        ),
        Container(
          color: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              // Left: Total Amount label + price
              Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Total Amount',
                    style: GoogleFonts.googleSansFlex(
                      color: OrderSummaryConstants.secondaryText,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    formatCurrency(subtotal),
                    style: GoogleFonts.googleSansFlex(
                      color: OrderSummaryConstants.navy,
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 16),
              // Right: Place Order button
              Expanded(
                child: SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: isPlacing ? null : onPlaceOrder,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: OrderSummaryConstants.gold,
                      foregroundColor: OrderSummaryConstants.navy,
                      disabledBackgroundColor: OrderSummaryConstants.gold,
                      disabledForegroundColor: OrderSummaryConstants.navy,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    child: isPlacing
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: OrderSummaryConstants.navy,
                            ),
                          )
                        : Text(
                            'Place Order',
                            style: GoogleFonts.googleSansFlex(
                              fontWeight: FontWeight.w700,
                              fontSize: 15,
                            ),
                          ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
