import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../models/product_customization.dart';
import '../services/auth_service.dart';
import '../session/session_service.dart';
import 'product_image.dart';

class OrderSummaryConstants {
  static const gold = Color(0xFFFCB316);
  static const navy = Color(0xFF1A1851);
  static const pageBg = Colors.white;
  static const checkoutBg = Color(0xFFF5F5F5);
  static const secondaryText = Color(0xFF475569);
  static const outline = Color(0xFFCBD5E1);
}

class OrderSummaryLineItem {
  const OrderSummaryLineItem({
    required this.productName,
    required this.imageUrl,
    required this.quantity,
    required this.unitPrice,
    required this.selections,
    this.sellerName = '',
  });

  final String productName;
  final String imageUrl;
  final int quantity;
  final double unitPrice;
  final List<SelectedCustomization> selections;
  final String sellerName;

  double get lineTotal => unitPrice * quantity;

  OrderSummaryLineItem copyWith({int? quantity}) {
    return OrderSummaryLineItem(
      productName: productName,
      imageUrl: imageUrl,
      quantity: quantity ?? this.quantity,
      unitPrice: unitPrice,
      selections: selections,
      sellerName: sellerName,
    );
  }
}

List<String> formatCustomizationLines(List<SelectedCustomization> selections) {
  if (selections.isEmpty) return const [];

  final grouped = <String, List<SelectedCustomization>>{};

  for (final item in selections) {
    grouped.putIfAbsent(item.group, () => []).add(item);
  }

  return grouped.entries
      .map((entry) {
        if (entry.value.length == 1) {
          final item = entry.value.first;

          final suffix = item.extraPrice > 0
              ? ' (+₱${item.extraPrice.toStringAsFixed(2)})'
              : '';

          return '${entry.key}: ${item.option}$suffix';
        }

        final options = entry.value.map((item) => item.option).join(', ');

        return '${entry.key}: $options';
      })
      .toList(growable: false);
}

String formatCurrency(double value) {
  return '₱${value.toStringAsFixed(2)}';
}

class OrderSummaryCard extends StatefulWidget {
  const OrderSummaryCard({
    super.key,
    required this.items,
    required this.subtotal,
    this.showCheckoutHeader = false,
    this.sellerMessageController,
    this.onQuantityChanged,
    this.onPaymentMethodChanged,
  });

  final List<OrderSummaryLineItem> items;
  final double subtotal;
  final bool showCheckoutHeader;
  final TextEditingController? sellerMessageController;
  final void Function(int index, int newQuantity)? onQuantityChanged;
  final ValueChanged<String>? onPaymentMethodChanged;

  double get total => subtotal;

  @override
  State<OrderSummaryCard> createState() => _OrderSummaryCardState();
}

class _OrderSummaryCardState extends State<OrderSummaryCard> {
  String _selectedPaymentMethod = 'Cash on Pickup';
  bool _subtotalExpanded = false;

  void _selectPaymentMethod(String method) {
    setState(() {
      _selectedPaymentMethod = method;
    });

    widget.onPaymentMethodChanged?.call(method);
  }

  @override
  Widget build(BuildContext context) {
    final decoration = BoxDecoration(
      color: Colors.white,
      borderRadius: widget.showCheckoutHeader ? null : BorderRadius.circular(8),
      border: widget.showCheckoutHeader
          ? null
          : Border.all(color: OrderSummaryConstants.outline),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // =========================================================
        // PRODUCT / SELLER SECTION
        // =========================================================
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: decoration,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < widget.items.length; i++) ...[
                if (i > 0) ...[
                  const SizedBox(height: 16),
                  const Divider(
                    height: 1,
                    color: OrderSummaryConstants.outline,
                  ),
                  const SizedBox(height: 16),
                ],

                _OrderSummaryItemRow(
                  key: ValueKey('order-item-$i'),
                  item: widget.items[i],
                  sellerMessageController: i == 0
                      ? widget.sellerMessageController
                      : null,
                  onQuantityChanged: widget.onQuantityChanged != null
                      ? (newQty) {
                          widget.onQuantityChanged!(i, newQty);
                        }
                      : null,
                ),
              ],
            ],
          ),
        ),

        const SizedBox(height: 16),

        // =========================================================
        // PAYMENT METHODS
        // =========================================================
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: decoration,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Payment Methods',
                style: GoogleFonts.notoSans(
                  color: OrderSummaryConstants.navy,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),

              const SizedBox(height: 14),

              _PaymentMethodRadioOption(
                title: 'Cash on Pickup',
                iconWidget: const Icon(
                  Icons.store_outlined,
                  size: 20,
                  color: OrderSummaryConstants.navy,
                ),
                isSelected: _selectedPaymentMethod == 'Cash on Pickup',
                onTap: () {
                  _selectPaymentMethod('Cash on Pickup');
                },
              ),

              const SizedBox(height: 14),

              _PaymentMethodRadioOption(
                title: 'Cash on Delivery',
                iconWidget: Container(
                  width: 30,
                  height: 26,
                  decoration: const BoxDecoration(color: Color(0xFF16A34A)),
                  alignment: Alignment.center,
                  child: Text(
                    'COD',
                    style: GoogleFonts.googleSansFlex(
                      fontSize: 8.5,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                      height: 1.0,
                    ),
                  ),
                ),
                isSelected: _selectedPaymentMethod == 'Cash on Delivery',
                onTap: () {
                  _selectPaymentMethod('Cash on Delivery');
                },
              ),
            ],
          ),
        ),

        const SizedBox(height: 16),

        // =========================================================
        // ORDER SUMMARY
        // =========================================================
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: decoration,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Order Summary',
                style: GoogleFonts.notoSans(
                  color: OrderSummaryConstants.navy,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),

              const SizedBox(height: 14),

              // Product Subtotal Header
              InkWell(
                onTap: () {
                  setState(() {
                    _subtotalExpanded = !_subtotalExpanded;
                  });
                },
                child: Row(
                  children: [
                    Text(
                      'Product Subtotal',
                      key: const ValueKey('order-summary-heading'),
                      style: GoogleFonts.googleSansFlex(
                        color: OrderSummaryConstants.secondaryText,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),

                    const SizedBox(width: 4),

                    AnimatedRotation(
                      turns: _subtotalExpanded ? 0.25 : 0.0,
                      duration: const Duration(milliseconds: 200),
                      curve: Curves.easeOutCubic,
                      child: const Icon(
                        Icons.chevron_right_rounded,
                        size: 18,
                        color: OrderSummaryConstants.navy,
                      ),
                    ),

                    const Spacer(),

                    Text(
                      formatCurrency(widget.subtotal),
                      style: GoogleFonts.googleSansFlex(
                        color: OrderSummaryConstants.navy,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),

              // Expanded Product Breakdown
              AnimatedCrossFade(
                duration: const Duration(milliseconds: 200),
                crossFadeState: _subtotalExpanded
                    ? CrossFadeState.showSecond
                    : CrossFadeState.showFirst,
                firstChild: const SizedBox(width: double.infinity),
                secondChild: Column(
                  children: [
                    const SizedBox(height: 12),

                    for (final item in widget.items) ...[
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${item.productName}  ×${item.quantity}',
                              style: GoogleFonts.googleSansFlex(
                                color: OrderSummaryConstants.secondaryText,
                                fontSize: 13,
                                fontWeight: FontWeight.w400,
                              ),
                            ),
                          ),

                          Text(
                            formatCurrency(item.lineTotal),
                            style: GoogleFonts.googleSansFlex(
                              color: OrderSummaryConstants.secondaryText,
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 6),
                    ],
                  ],
                ),
              ),

              const Padding(
                padding: EdgeInsets.symmetric(vertical: 14),
                child: Divider(height: 1, color: OrderSummaryConstants.outline),
              ),

              // Total
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Total',
                      style: GoogleFonts.googleSansFlex(
                        color: OrderSummaryConstants.secondaryText,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),

                  Text(
                    formatCurrency(widget.total),
                    style: GoogleFonts.googleSansFlex(
                      color: OrderSummaryConstants.navy,
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _PaymentMethodRadioOption extends StatelessWidget {
  const _PaymentMethodRadioOption({
    required this.title,
    this.iconWidget,
    required this.isSelected,
    required this.onTap,
  });

  final String title;
  final Widget? iconWidget;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 8),
        child: Row(
          children: [
            if (iconWidget != null) ...[
              iconWidget!,
              const SizedBox(width: 14),
            ],

            Expanded(
              child: Text(
                title,
                style: GoogleFonts.googleSansFlex(
                  color: const Color(0xFF0F172A),
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),

            const SizedBox(width: 14),

            Container(
              width: 20,
              height: 20,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? OrderSummaryConstants.navy : Colors.white,
                border: Border.all(
                  color: isSelected
                      ? OrderSummaryConstants.navy
                      : const Color(0xFFCBD5E1),
                  width: isSelected ? 2 : 1.5,
                ),
              ),
              alignment: Alignment.center,
              child: isSelected
                  ? Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                      ),
                    )
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}

class CheckoutBuyerDetails extends StatefulWidget {
  const CheckoutBuyerDetails({super.key});

  @override
  State<CheckoutBuyerDetails> createState() => _CheckoutBuyerDetailsState();
}

class _CheckoutBuyerDetailsState extends State<CheckoutBuyerDetails> {
  late final Future<AuthUser?> _buyer = SessionService.loadUser();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<AuthUser?>(
      future: _buyer,
      builder: (context, snapshot) {
        final user = snapshot.data;

        if (user == null) {
          return const SizedBox.shrink();
        }

        final name = user.fullName.trim().isNotEmpty
            ? user.fullName.trim()
            : '${user.firstName} ${user.lastName}'.trim();

        final studentId = user.profileStudentId.trim();
        final contact = user.contactNumber.trim();

        return Container(
          key: const ValueKey('checkout-buyer-card'),
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: const BoxDecoration(color: Colors.white),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.only(top: 2, right: 10),
                child: Icon(
                  Icons.location_on_outlined,
                  size: 20,
                  color: OrderSummaryConstants.navy,
                ),
              ),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      crossAxisAlignment: WrapCrossAlignment.center,
                      spacing: 8,
                      runSpacing: 2,
                      children: [
                        if (name.isNotEmpty)
                          Text(
                            name,
                            key: const ValueKey('checkout-buyer-name'),
                            style: GoogleFonts.notoSans(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: OrderSummaryConstants.navy,
                            ),
                          ),

                        if (studentId.isNotEmpty)
                          Text(
                            studentId,
                            key: const ValueKey('checkout-buyer-student-id'),
                            style: GoogleFonts.notoSans(
                              fontSize: 12,
                              color: OrderSummaryConstants.secondaryText,
                            ),
                          ),
                      ],
                    ),

                    if (contact.isNotEmpty) ...[
                      const SizedBox(height: 4),

                      Text(
                        contact,
                        key: const ValueKey('checkout-buyer-contact'),
                        style: GoogleFonts.notoSans(
                          fontSize: 12,
                          color: OrderSummaryConstants.navy,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _OrderSummaryItemRow extends StatefulWidget {
  const _OrderSummaryItemRow({
    super.key,
    required this.item,
    this.onQuantityChanged,
    this.sellerMessageController,
  });

  final OrderSummaryLineItem item;
  final ValueChanged<int>? onQuantityChanged;
  final TextEditingController? sellerMessageController;

  @override
  State<_OrderSummaryItemRow> createState() => _OrderSummaryItemRowState();
}

class _OrderSummaryItemRowState extends State<_OrderSummaryItemRow> {
  void _openNoteSheet() {
    final controller = widget.sellerMessageController;
    if (controller == null) return;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        return Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(sheetContext).viewInsets.bottom,
          ),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
            ),
            child: SafeArea(
              top: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Bottom sheet handle
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: const Color(0xFFCBD5E1),
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                  ),

                  const SizedBox(height: 18),

                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          controller.text.trim().isNotEmpty
                              ? 'Edit note'
                              : 'Add note',
                          style: GoogleFonts.googleSansFlex(
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                            color: OrderSummaryConstants.navy,
                          ),
                        ),
                      ),

                      IconButton(
                        onPressed: () {
                          Navigator.of(sheetContext).pop();
                        },
                        icon: const Icon(
                          Icons.close_rounded,
                          color: OrderSummaryConstants.navy,
                        ),
                      ),
                    ],
                  ),

                  Text(
                    'Leave an optional message for the seller.',
                    style: GoogleFonts.googleSansFlex(
                      fontSize: 13,
                      color: OrderSummaryConstants.secondaryText,
                    ),
                  ),

                  const SizedBox(height: 16),

                  TextField(
                    controller: controller,
                    autofocus: true,
                    minLines: 3,
                    maxLines: 5,
                    maxLength: 300,
                    textCapitalization: TextCapitalization.sentences,
                    style: GoogleFonts.googleSansFlex(
                      fontSize: 13,
                      color: const Color(0xFF0F172A),
                    ),
                    decoration: InputDecoration(
                      hintText: 'Write your note here...',
                      hintStyle: GoogleFonts.googleSansFlex(
                        fontSize: 13,
                        color: OrderSummaryConstants.secondaryText,
                      ),
                      counterStyle: GoogleFonts.googleSansFlex(
                        color: OrderSummaryConstants.secondaryText,
                        fontSize: 11,
                      ),
                      filled: true,
                      fillColor: const Color(0xFFF8FAFC),
                      contentPadding: const EdgeInsets.all(14),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(
                          color: OrderSummaryConstants.outline,
                        ),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(
                          color: OrderSummaryConstants.outline,
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(
                          color: OrderSummaryConstants.navy,
                          width: 1.5,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.of(sheetContext).pop();
                        setState(() {});
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: OrderSummaryConstants.navy,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      child: Text(
                        'Done',
                        style: GoogleFonts.googleSansFlex(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;

    final lines = formatCustomizationLines(item.selections);
    final quantityStepper = Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: OrderSummaryConstants.outline),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Minus
          InkWell(
            onTap: widget.onQuantityChanged != null && item.quantity > 1
                ? () {
                    widget.onQuantityChanged!(item.quantity - 1);
                  }
                : null,
            borderRadius: const BorderRadius.horizontal(
              left: Radius.circular(7),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
              child: Icon(
                Icons.remove_rounded,
                size: 15,
                color: item.quantity > 1
                    ? OrderSummaryConstants.navy
                    : OrderSummaryConstants.secondaryText.withValues(
                        alpha: 0.35,
                      ),
              ),
            ),
          ),

          // Quantity
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
            child: Text(
              '${item.quantity}',
              style: GoogleFonts.notoSans(
                color: OrderSummaryConstants.navy,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),

          // Plus
          InkWell(
            onTap: widget.onQuantityChanged != null
                ? () {
                    widget.onQuantityChanged!(item.quantity + 1);
                  }
                : null,
            borderRadius: const BorderRadius.horizontal(
              right: Radius.circular(7),
            ),
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 7, vertical: 4),
              child: Icon(
                Icons.add_rounded,
                size: 15,
                color: OrderSummaryConstants.navy,
              ),
            ),
          ),
        ],
      ),
    );

    final hasNoteText =
        widget.sellerMessageController?.text.trim().isNotEmpty ?? false;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (item.sellerName.trim().isNotEmpty) ...[
          Row(
            children: [
              const Icon(
                Icons.storefront_outlined,
                size: 16,
                color: OrderSummaryConstants.navy,
              ),

              const SizedBox(width: 6),

              Expanded(
                child: Text(
                  item.sellerName.trim(),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.googleSansFlex(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: OrderSummaryConstants.navy,
                  ),
                ),
              ),

              // =================
              // ADD NOTE TEXT - RIGHT SIDE (SLIDE UP SHEET)
              // ===================================================
              if (widget.sellerMessageController != null)
                InkWell(
                  onTap: _openNoteSheet,
                  borderRadius: BorderRadius.circular(6),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 6,
                      vertical: 4,
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          hasNoteText ? 'Edit note' : 'Add note',
                          style: GoogleFonts.googleSansFlex(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: OrderSummaryConstants.navy,
                          ),
                        ),
                        const SizedBox(width: 2),
                        const Icon(
                          Icons.chevron_right_rounded,
                          size: 18,
                          color: OrderSummaryConstants.navy,
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),

          const SizedBox(height: 12),
        ],
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: SizedBox(
                width: 100,
                height: 100,
                child: ProductImage(imageUrl: item.imageUrl),
              ),
            ),

            const SizedBox(width: 14),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.productName,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.googleSansFlex(
                      color: const Color(0xFF0F172A),
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),

                  if (lines.isNotEmpty) ...[
                    const SizedBox(height: 4),

                    ...lines.map(
                      (line) => Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          line,
                          style: GoogleFonts.googleSansFlex(
                            color: OrderSummaryConstants.secondaryText,
                            fontSize: 12,
                            fontWeight: FontWeight.w400,
                            height: 1.35,
                          ),
                        ),
                      ),
                    ),
                  ],

                  const SizedBox(height: 8),

                  Text(
                    'x${item.quantity}',
                    style: GoogleFonts.googleSansFlex(
                      color: OrderSummaryConstants.secondaryText,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),

                  const SizedBox(height: 2),

                  Text(
                    formatCurrency(item.unitPrice),
                    style: GoogleFonts.googleSansFlex(
                      color: OrderSummaryConstants.navy,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 12),

            // Quantity stepper
            quantityStepper,
          ],
        ),

        // NOTE PREVIEW ROW IF SET
        if (hasNoteText) ...[
          const SizedBox(height: 10),
          InkWell(
            onTap: _openNoteSheet,
            borderRadius: BorderRadius.circular(8),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: OrderSummaryConstants.outline),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.edit_note_rounded,
                    size: 16,
                    color: OrderSummaryConstants.navy,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      widget.sellerMessageController!.text.trim(),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: GoogleFonts.googleSansFlex(
                        fontSize: 12,
                        color: OrderSummaryConstants.navy,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class PlacedOrdersReviewView extends StatelessWidget {
  const PlacedOrdersReviewView({
    super.key,
    required this.items,
    required this.subtotal,
    required this.onDone,
    this.successTitle = 'Order Placed',
    this.successMessage = 'Your order was sent to the admin orders section.',
    this.doneLabel = 'Done',
  });

  final List<OrderSummaryLineItem> items;
  final double subtotal;
  final VoidCallback onDone;
  final String successTitle;
  final String successMessage;
  final String doneLabel;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: OrderSummaryConstants.navy.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_rounded,
                color: OrderSummaryConstants.navy,
                size: 24,
              ),
            ),

            const SizedBox(width: 12),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    successTitle,
                    style: GoogleFonts.notoSans(
                      color: OrderSummaryConstants.navy,
                      fontSize: 20,
                      fontWeight: FontWeight.w600,
                    ),
                  ),

                  const SizedBox(height: 2),

                  Text(
                    successMessage,
                    style: GoogleFonts.notoSans(
                      color: const Color(0xFF64748B),
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),

        const SizedBox(height: 16),

        Text(
          'Your Orders',
          style: GoogleFonts.notoSans(
            color: OrderSummaryConstants.navy,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),

        const SizedBox(height: 12),

        Expanded(
          child: ListView(
            children: [OrderSummaryCard(items: items, subtotal: subtotal)],
          ),
        ),

        const SizedBox(height: 12),

        SizedBox(
          width: double.infinity,
          height: 52,
          child: ElevatedButton(
            onPressed: onDone,
            style: ElevatedButton.styleFrom(
              backgroundColor: OrderSummaryConstants.navy,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            child: Text(
              doneLabel,
              style: GoogleFonts.notoSans(
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class OrderSummaryPrimaryButton extends StatelessWidget {
  const OrderSummaryPrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.isLoading = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: isLoading ? null : onPressed,
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
        child: isLoading
            ? const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: OrderSummaryConstants.navy,
                ),
              )
            : Text(
                label,
                style: GoogleFonts.notoSans(
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
              ),
      ),
    );
  }
}
