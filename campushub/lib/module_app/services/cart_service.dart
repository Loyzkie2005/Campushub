import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/cart_item.dart';
import '../models/product_customization.dart';
import '../models/product_item.dart';
import '../widgets/add_to_cart_feedback.dart';

class CartService extends ChangeNotifier {
  CartService._();

  static final CartService instance = CartService._();

  /// Attach to the app-bar cart icon for badge positioning.
  static final GlobalKey cartIconKey = GlobalKey();

  static const String _storageKey = 'campushub_cart_items';

  final List<CartItem> _items = [];
  bool _loaded = false;

  List<CartItem> get items => List.unmodifiable(_items);

  int get lineCount => _items.length;

  int get itemCount => _items.fold(0, (sum, item) => sum + item.quantity);

  double get subtotal =>
      _items.fold(0, (sum, item) => sum + item.totalPrice);

  bool get isEmpty => _items.isEmpty;

  Future<void> load() async {
    if (_loaded) return;
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw != null && raw.isNotEmpty) {
      _items
        ..clear()
        ..addAll(CartItem.decodeList(raw));
    }
    _loaded = true;
    notifyListeners();
  }

  Future<void> quickAdd({
    required BuildContext context,
    required ProductItem product,
    BuySelection? selection,
  }) async {
    if (!product.isPurchasable) return;

    final unitPrice = selection?.unitPrice ?? product.basePrice;
    final buySelection = selection ??
        BuySelection(
          quantity: 1,
          selections: const [],
          summary: '',
          unitPrice: unitPrice,
        );

    await addFromProduct(
      productId: product.id,
      productName: product.name,
      imageUrl: product.imageUrl,
      category: product.category,
      sellerName: product.seller,
      sellerContact: product.sellerContact,
      basePrice: product.basePrice,
      selection: buySelection,
    );

    if (!context.mounted) return;
    AddToCartFeedback.show(context);
  }

  Future<void> addFromProduct({
    required int? productId,
    required String productName,
    required String imageUrl,
    required String category,
    required String sellerName,
    required String sellerContact,
    required double basePrice,
    required BuySelection selection,
  }) async {
    final incoming = CartItem.fromProduct(
      productId: productId,
      productName: productName,
      imageUrl: imageUrl,
      category: category,
      sellerName: sellerName,
      sellerContact: sellerContact,
      basePrice: basePrice,
      selection: selection,
    );

    final index = _items.indexWhere((item) => item.id == incoming.id);
    if (index >= 0) {
      final existing = _items[index];
      _items[index] = existing.copyWith(
        quantity: existing.quantity + incoming.quantity,
      );
    } else {
      _items.insert(0, incoming);
    }

    await _persist();
    notifyListeners();
  }

  Future<void> updateQuantity(String id, int quantity) async {
    final index = _items.indexWhere((item) => item.id == id);
    if (index < 0) return;
    if (quantity <= 0) {
      await removeItem(id);
      return;
    }
    _items[index] = _items[index].copyWith(quantity: quantity);
    await _persist();
    notifyListeners();
  }

  Future<void> removeItem(String id) async {
    _items.removeWhere((item) => item.id == id);
    await _persist();
    notifyListeners();
  }

  Future<void> clear() async {
    _items.clear();
    await _persist();
    notifyListeners();
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, CartItem.encodeList(_items));
  }
}
