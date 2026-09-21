import 'dart:convert';

import 'product_customization.dart';

class CartItem {
  const CartItem({
    required this.id,
    this.productId,
    required this.productName,
    required this.imageUrl,
    required this.category,
    required this.sellerName,
    required this.sellerContact,
    required this.basePrice,
    required this.quantity,
    required this.selections,
    required this.summary,
    required this.unitPrice,
  });

  factory CartItem.fromJson(Map<String, dynamic> json) {
    final rawSelections = json['selections'];
    final selections = rawSelections is List
        ? rawSelections
              .whereType<Map>()
              .map(
                (row) => SelectedCustomization(
                  group: (row['group'] as String? ?? '').trim(),
                  option: (row['option'] as String? ?? '').trim(),
                  extraPrice:
                      double.tryParse('${row['extra_price'] ?? '0'}') ?? 0,
                ),
              )
              .toList(growable: false)
        : const <SelectedCustomization>[];

    final rawId = json['product_id'];
    return CartItem(
      id: (json['id'] as String? ?? '').trim(),
      productId: rawId is int ? rawId : int.tryParse('$rawId'),
      productName: (json['product_name'] as String? ?? '').trim(),
      imageUrl: (json['image_url'] as String? ?? '').trim(),
      category: (json['category'] as String? ?? '').trim(),
      sellerName: (json['seller_name'] as String? ?? '').trim(),
      sellerContact: (json['seller_contact'] as String? ?? '').trim(),
      basePrice: double.tryParse('${json['base_price'] ?? '0'}') ?? 0,
      quantity: int.tryParse('${json['quantity'] ?? '1'}') ?? 1,
      selections: selections,
      summary: (json['summary'] as String? ?? '').trim(),
      unitPrice: double.tryParse('${json['unit_price'] ?? '0'}') ?? 0,
    );
  }

  factory CartItem.fromProduct({
    required int? productId,
    required String productName,
    required String imageUrl,
    required String category,
    required String sellerName,
    required String sellerContact,
    required double basePrice,
    required BuySelection selection,
  }) {
    final mergeKey = _mergeKey(productId, productName, selection.summary);
    return CartItem(
      id: mergeKey,
      productId: productId,
      productName: productName,
      imageUrl: imageUrl,
      category: category,
      sellerName: sellerName,
      sellerContact: sellerContact,
      basePrice: basePrice,
      quantity: selection.quantity,
      selections: selection.selections,
      summary: selection.summary,
      unitPrice: selection.unitPrice,
    );
  }

  final String id;
  final int? productId;
  final String productName;
  final String imageUrl;
  final String category;
  final String sellerName;
  final String sellerContact;
  final double basePrice;
  final int quantity;
  final List<SelectedCustomization> selections;
  final String summary;
  final double unitPrice;

  double get totalPrice => unitPrice * quantity;

  String get unitPriceLabel => '₱${unitPrice.toStringAsFixed(2)}';

  String get totalPriceLabel => '₱${totalPrice.toStringAsFixed(2)}';

  BuySelection get buySelection => BuySelection(
    quantity: quantity,
    selections: selections,
    summary: summary,
    unitPrice: unitPrice,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'product_id': productId,
    'product_name': productName,
    'image_url': imageUrl,
    'category': category,
    'seller_name': sellerName,
    'seller_contact': sellerContact,
    'base_price': basePrice.toStringAsFixed(2),
    'quantity': quantity,
    'selections': selections.map((row) => row.toJson()).toList(),
    'summary': summary,
    'unit_price': unitPrice.toStringAsFixed(2),
  };

  CartItem copyWith({int? quantity}) {
    return CartItem(
      id: id,
      productId: productId,
      productName: productName,
      imageUrl: imageUrl,
      category: category,
      sellerName: sellerName,
      sellerContact: sellerContact,
      basePrice: basePrice,
      quantity: quantity ?? this.quantity,
      selections: selections,
      summary: summary,
      unitPrice: unitPrice,
    );
  }

  static String _mergeKey(int? productId, String productName, String summary) {
    final base = productId?.toString() ?? productName.toLowerCase().trim();
    final variant = summary.toLowerCase().trim();
    return base.isEmpty ? variant : '$base|$variant';
  }

  static String encodeList(List<CartItem> items) =>
      jsonEncode(items.map((item) => item.toJson()).toList());

  static List<CartItem> decodeList(String raw) {
    try {
      final decoded = jsonDecode(raw) as List<dynamic>;
      return decoded
          .whereType<Map>()
          .map((row) => CartItem.fromJson(row.map((k, v) => MapEntry('$k', v))))
          .toList(growable: false);
    } catch (_) {
      return [];
    }
  }
}
