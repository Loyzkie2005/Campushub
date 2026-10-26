import 'package:flutter/material.dart';
import '../theme/app_typography.dart';

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
  String _fulfillmentMethod = 'pickup';
  String _deliveryDestination = '';
  final _requestKey = OrderService.requestKey();
  Map<String, dynamic>? _submittedOrder;

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
    if (_submittedOrder == null &&
        _fulfillmentMethod == 'seller_delivery' &&
        _deliveryDestination.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter the seller delivery destination.')),
      );
      return;
    }
    setState(() => _isPlacing = true);
    final user = await SessionService.loadUser();
    _submittedOrder ??= {
      'fulfillment_method': _fulfillmentMethod,
      'delivery_destination': _fulfillmentMethod == 'seller_delivery'
          ? _deliveryDestination.trim()
          : '',
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
    };
    final success = await OrderService.placeOrder(
      operationKey: _requestKey,
      order: _submittedOrder!,
    );
    if (!mounted) return;
    if (!success) {
      setState(() => _isPlacing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Unable to confirm this order. Retry to check the same submission; your original details are preserved.',
          ),
        ),
      );
      return;
    }
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
          style: AppTypography.text(fontWeight: FontWeight.w600),
        ),
      ),
      body: Theme(
        data: Theme.of(context).copyWith(
          textTheme: AppTypography.textTheme(Theme.of(context).textTheme),
        ),
        child: SafeArea(
          top: false,
          bottom: false,
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
                    locked: _submittedOrder != null,
                    onPlaceOrder: _placeOrder,
                    onQuantityChanged: _updateQuantity,
                    onFulfillmentChanged: (method, destination) {
                      _fulfillmentMethod = method;
                      _deliveryDestination = destination;
                    },
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
    required this.locked,
    required this.onPlaceOrder,
    this.onQuantityChanged,
    this.onFulfillmentChanged,
  });

  final List<OrderSummaryLineItem> items;
  final double subtotal;
  final TextEditingController sellerMessageController;
  final bool isPlacing;
  final bool locked;
  final VoidCallback onPlaceOrder;
  final ValueChanged<int>? onQuantityChanged;
  final void Function(String, String)? onFulfillmentChanged;

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
                locked: locked,
                showCheckoutHeader: true,
                items: items,
                subtotal: subtotal,
                onFulfillmentChanged: onFulfillmentChanged,
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
          child: SafeArea(
            top: false,
            child: MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: const TextScaler.linear(1.0)),
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 8,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Total Amount',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.text(
                          color: OrderSummaryConstants.navy,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      formatCurrency(subtotal),
                      style: AppTypography.text(
                        color: OrderSummaryConstants.navy,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      height: 46,
                      child: ElevatedButton(
                        onPressed: isPlacing ? null : onPlaceOrder,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: OrderSummaryConstants.gold,
                          foregroundColor: OrderSummaryConstants.navy,
                          disabledBackgroundColor: OrderSummaryConstants.gold,
                          disabledForegroundColor: OrderSummaryConstants.navy,
                          elevation: 0,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 15,
                            vertical: 11,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: isPlacing
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: OrderSummaryConstants.navy,
                                ),
                              )
                            : Text(
                                'Place Order',
                                style: AppTypography.text(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 14,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
