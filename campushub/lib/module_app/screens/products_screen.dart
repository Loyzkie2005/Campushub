import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:lucide_icons/lucide_icons.dart';

import '../config/api_config.dart';
import '../models/product_item.dart';
import '../services/cart_service.dart';
import '../services/favorite_service.dart';
import '../services/product_service.dart';
import '../session/session_service.dart';
import '../utils/form_suggestion_samples.dart';
import '../utils/local_autocomplete.dart';
import '../widgets/cart_icon_button.dart';
import '../widgets/product_image.dart';
import 'product_details_screen.dart';

class ProductsScreen extends StatefulWidget {
  const ProductsScreen({super.key});

  static const Color primaryNavy = Color(0xFF142B47);
  static const Color primaryBlue = Color(0xFF1A56DB);
  static const Color webBrandBlue = Color(0xFF0175C2);
  static const Color campusGold = Color(0xFFFCB316);
  static const Color pageBackground = Color(0xFFF8FAFD);
  static const Color borderBlue = Color(0xFFBFD7FF);
  static String get apiBaseUrl => ApiConfig.baseUrl;
  static List<String> get apiBaseUrls => ApiConfig.serverBaseUrls;

  /// Institutional modal bottom sheet to submit a product for marketplace approval.
  static Future<bool?> showAddProductSheet(BuildContext context) {
    return showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => const _AddProductForm(),
    );
  }

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  bool _isLoadingProducts = true;
  String? _productsError;
  List<ProductItem> _approvedProducts = const [];
  int? _currentUserId;

  void _openDashboard(BuildContext context) {
    if (Navigator.canPop(context)) Navigator.pop(context);
  }

  @override
  void initState() {
    super.initState();
    _loadCurrentUser();
    _fetchApprovedProducts();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _refreshPage() async {
    await _fetchApprovedProducts();
  }

  Future<void> _loadCurrentUser() async {
    final user = await SessionService.loadUser();
    if (!mounted) return;
    setState(() => _currentUserId = user?.id);
  }

  Future<void> _fetchApprovedProducts() async {
    if (mounted) {
      setState(() {
        _isLoadingProducts = true;
        _productsError = null;
      });
    }

    for (final baseUrl in ProductsScreen.apiBaseUrls) {
      try {
        final response = await http
            .get(
              Uri.parse('$baseUrl/api/products/approved/'),
              headers: const {'Accept': 'application/json'},
            )
            .timeout(const Duration(seconds: 5));

        if (response.statusCode < 200 || response.statusCode >= 300) {
          continue;
        }

        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        final rows = decoded['products'] as List<dynamic>? ?? const [];
        final products = rows
            .whereType<Map>()
            .map(
              (row) => ProductItem.fromJson(
                row.map((key, value) => MapEntry(key.toString(), value)),
              ),
            )
            .toList(growable: false);

        if (!mounted) return;
        setState(() {
          _approvedProducts = products;
          _isLoadingProducts = false;
        });
        return;
      } catch (_) {}
    }

    if (!mounted) return;
    setState(() {
      _productsError =
          'Start Django with: python manage.py runserver 0.0.0.0:8000';
      _isLoadingProducts = false;
    });
  }

  List<ProductItem> get _visibleApprovedProducts => _approvedProducts;

  List<ProductItem> get _recentlyAddedProducts =>
      _visibleApprovedProducts.take(4).toList(growable: false);

  List<ProductItem> get _popularApprovedProducts {
    final visible = _visibleApprovedProducts;
    if (visible.length <= 4) return const [];
    return visible.skip(4).toList(growable: false);
  }

  Future<void> _openProduct(ProductItem product) async {
    if (product.id != null && _currentUserId != null) {
      unawaited(
        ProductService.trackInteraction(
          userId: _currentUserId!,
          productId: product.id!,
          interactionType: 'view',
        ),
      );
    }

    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProductDetailsScreen(
          id: product.id,
          userId: _currentUserId,
          sellerId: product.sellerId,
          name: product.name,
          priceLabel: product.price,
          imageUrl: product.imageUrl,
          images: product.images,
          category: product.category,
          seller: product.seller,
          sellerContact: product.sellerContact,
          stock: product.stock,
          description: product.description,
          expiryDate: product.expiryDate,
          inventoryStatus: product.inventoryStatus,
          inventoryStatusLabel: product.inventoryStatusLabel,
          isPurchasable: product.isPurchasable,
          soldCount: product.soldCount,
          customization: product.customization,
        ),
      ),
    );
  }

  Widget _buildProductsSection({
    required List<ProductItem> products,
    required String emptyMessage,
    required bool isPrimary,
  }) {
    if (_isLoadingProducts && isPrimary) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 28),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (_productsError != null && isPrimary) {
      return _ProductsMessageCard(
        icon: Icons.cloud_off_outlined,
        title: 'Unable to load products',
        message: _productsError!,
        actionLabel: 'Retry',
        onAction: _fetchApprovedProducts,
      );
    }
    if (products.isEmpty) {
      // Hide the secondary section entirely when empty to avoid two empty
      // cards stacked on top of each other.
      if (!isPrimary) return const SizedBox.shrink();
      return _ProductsMessageCard(
        icon: Icons.shopping_bag_outlined,
        title: 'No products yet',
        message: emptyMessage,
        actionLabel: 'Refresh',
        onAction: _fetchApprovedProducts,
      );
    }
    return _ProductGrid(products: products, onProductTap: _openProduct);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ProductsScreen.pageBackground,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        backgroundColor: Colors.white,
        elevation: 0,
        toolbarHeight: 56,
        titleSpacing: 16,
        title: Row(
          children: [
            Image.asset(
              'assets/img/logo.png',
              width: 34,
              height: 34,
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  width: 34,
                  height: 34,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: Color(0xFFEAF1FF),
                  ),
                  child: const Icon(
                    Icons.school_outlined,
                    color: ProductsScreen.primaryBlue,
                  ),
                );
              },
            ),
            const SizedBox(width: 10),
            RichText(
              text: const TextSpan(
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
                children: [
                  TextSpan(
                    text: 'Campus',
                    style: TextStyle(color: ProductsScreen.campusGold),
                  ),
                  TextSpan(
                    text: 'Hub',
                    style: TextStyle(color: ProductsScreen.primaryNavy),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          CartIconButton(
            iconColor: ProductsScreen.primaryNavy,
            badgeKey: CartService.cartIconKey,
          ),
          IconButton(
            onPressed: () {},
            icon: const Icon(
              Icons.notifications_none,
              color: ProductsScreen.primaryNavy,
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: CircleAvatar(
              radius: 16,
              backgroundColor: const Color(0xFFEAF1FF),
              child: Icon(
                Icons.person,
                color: ProductsScreen.primaryNavy.withValues(alpha: 0.8),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: RefreshIndicator(
          onRefresh: _refreshPage,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
            children: [
              const Text(
                'Recently Added',
                style: TextStyle(
                  color: Colors.black,
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 14),
              _buildProductsSection(
                products: _recentlyAddedProducts,
                isPrimary: true,
                emptyMessage: 'Approved admin products will appear here.',
              ),
              const SizedBox(height: 24),
              const Text(
                'Popular Products',
                style: TextStyle(
                  color: Colors.black,
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 14),
              _buildProductsSection(
                products: _popularApprovedProducts,
                isPrimary: false,
                emptyMessage:
                    'Popular products will appear here once more are approved.',
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 1,
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        selectedItemColor: ProductsScreen.primaryBlue,
        unselectedItemColor: Colors.black87,
        selectedFontSize: 11,
        unselectedFontSize: 11,
        showUnselectedLabels: true,
        onTap: (index) {
          if (index == 0) _openDashboard(context);
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(LucideIcons.home),
            activeIcon: Icon(LucideIcons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(LucideIcons.shoppingBag),
            activeIcon: Icon(LucideIcons.shoppingBag),
            label: 'Marketplace',
          ),
          BottomNavigationBarItem(
            icon: Icon(LucideIcons.building2),
            label: 'Facilities',
          ),
          BottomNavigationBarItem(
            icon: Icon(LucideIcons.user),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

class _AddProductForm extends StatefulWidget {
  const _AddProductForm();

  @override
  State<_AddProductForm> createState() => _AddProductFormState();
}

class _AddProductFormState extends State<_AddProductForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  final _stockController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _imageUrlController = TextEditingController();

  static const List<String> _categories = [
    'Rice Meals',
    'Snacks',
    'Desserts',
    'Beverages',
    'Combo Meals',
    'Breakfast',
  ];

  String? _selectedCategory;
  DateTime? _expiryDate;
  bool _isSubmitting = false;

  bool get _showExpiryField =>
      ProductItem.isPerishableCategory(_selectedCategory);

  @override
  void dispose() {
    _nameController.dispose();
    _priceController.dispose();
    _stockController.dispose();
    _descriptionController.dispose();
    _imageUrlController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedCategory == null) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Please select a category')));
      return;
    }

    setState(() => _isSubmitting = true);

    final expiryIso = _showExpiryField && _expiryDate != null
        ? '${_expiryDate!.year.toString().padLeft(4, '0')}-'
              '${_expiryDate!.month.toString().padLeft(2, '0')}-'
              '${_expiryDate!.day.toString().padLeft(2, '0')}'
        : null;

    final saved = await ProductService.submitProduct(
      name: _nameController.text.trim(),
      price: _priceController.text.trim(),
      category: _selectedCategory!,
      stock: int.parse(_stockController.text.trim()),
      description: _descriptionController.text.trim(),
      expiryDate: expiryIso,
      imageUrl: _imageUrlController.text.trim(),
    );

    if (!mounted) return;
    setState(() => _isSubmitting = false);

    if (saved == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Could not submit product. Admin approval uses the web panel when mobile auth is unavailable.',
          ),
        ),
      );
      return;
    }

    Navigator.pop(context, true);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          '${_nameController.text.trim()} submitted for marketplace review.',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 18,
        right: 18,
        top: 18,
        bottom: MediaQuery.of(context).viewInsets.bottom + 18,
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Add Product',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const Text(
                'Submit a new product for marketplace approval.',
                style: TextStyle(color: Colors.black54, fontSize: 13),
              ),
              const SizedBox(height: 18),
              _ProductNameAutocompleteField(controller: _nameController),
              _ProductFormField(
                controller: _priceController,
                label: 'Price',
                icon: Icons.attach_money_outlined,
                hint: 'e.g. 60.00',
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Price is required';
                  }
                  final parsed = double.tryParse(value.trim());
                  if (parsed == null || parsed < 0) {
                    return 'Enter a valid price';
                  }
                  return null;
                },
              ),
              _CategoryDropdown(
                value: _selectedCategory,
                items: _categories,
                onChanged: (value) => setState(() {
                  _selectedCategory = value;
                  if (!ProductItem.isPerishableCategory(value)) {
                    _expiryDate = null;
                  }
                }),
              ),
              _ProductFormField(
                controller: _stockController,
                label: 'Stock',
                icon: Icons.inventory_2_outlined,
                hint: 'Enter available stock',
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Stock is required';
                  }
                  final parsed = int.tryParse(value.trim());
                  if (parsed == null || parsed < 0) {
                    return 'Enter a valid stock count';
                  }
                  return null;
                },
              ),
              if (_showExpiryField) ...[
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(
                    Icons.event_outlined,
                    color: ProductsScreen.primaryNavy,
                  ),
                  title: const Text(
                    'Expiry Date (Optional)',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(
                    _expiryDate == null
                        ? 'Tap to set date for FIFO tracking'
                        : 'Expires ${_expiryDate!.year}-${_expiryDate!.month.toString().padLeft(2, '0')}-${_expiryDate!.day.toString().padLeft(2, '0')}',
                  ),
                  trailing: _expiryDate != null
                      ? IconButton(
                          icon: const Icon(Icons.close, size: 18),
                          onPressed: () => setState(() => _expiryDate = null),
                        )
                      : null,
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: DateTime.now().add(const Duration(days: 7)),
                      firstDate: DateTime.now(),
                      lastDate: DateTime.now().add(const Duration(days: 365)),
                    );
                    if (picked != null) {
                      setState(() => _expiryDate = picked);
                    }
                  },
                ),
              ],
              _ProductFormField(
                controller: _descriptionController,
                label: 'Description',
                icon: Icons.description_outlined,
                hint:
                    'Describe the taste, ingredients, serving size, or special notes',
                required: false,
                maxLines: 3,
              ),
              _ProductFormField(
                controller: _imageUrlController,
                label: 'Image URL',
                icon: Icons.image_outlined,
                hint: 'https://...',
                required: false,
              ),
              const SizedBox(height: 6),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: ProductsScreen.primaryBlue,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    _isSubmitting ? 'Saving...' : 'Save Product',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProductNameAutocompleteField extends StatefulWidget {
  const _ProductNameAutocompleteField({required this.controller});

  final TextEditingController controller;

  @override
  State<_ProductNameAutocompleteField> createState() =>
      _ProductNameAutocompleteFieldState();
}

class _ProductNameAutocompleteFieldState
    extends State<_ProductNameAutocompleteField> {
  late final FocusNode _focusNode = FocusNode();

  @override
  void dispose() {
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: RawAutocomplete<String>(
        textEditingController: widget.controller,
        focusNode: _focusNode,
        optionsBuilder: (value) {
          return LocalAutocomplete.suggest<String>(
            items: FormSuggestionSamples.productNames,
            query: value.text,
            textOf: (item) => item,
            limit: 8,
          );
        },
        onSelected: (value) => widget.controller.text = value,
        fieldViewBuilder: (context, textController, focusNode, onSubmit) {
          return TextFormField(
            controller: textController,
            focusNode: focusNode,
            validator: (value) => value == null || value.trim().isEmpty
                ? 'Product Name is required'
                : null,
            decoration: InputDecoration(
              labelText: 'Product Name',
              hintText: 'Enter the product name',
              prefixIcon: const Icon(
                Icons.label_outline,
                color: ProductsScreen.primaryNavy,
              ),
              filled: true,
              fillColor: const Color(0xFFF8FAFD),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: const BorderSide(color: Color(0xFFD4DAE3)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: const BorderSide(color: ProductsScreen.primaryBlue),
              ),
            ),
          );
        },
        optionsViewBuilder: (context, onSelected, optionsIterable) {
          final opts = optionsIterable.toList(growable: false);
          if (opts.isEmpty) return const SizedBox.shrink();
          return Align(
            alignment: Alignment.topLeft,
            child: Material(
              elevation: 4,
              borderRadius: BorderRadius.circular(8),
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxHeight: 220,
                  maxWidth: 420,
                ),
                child: ListView.builder(
                  padding: EdgeInsets.zero,
                  shrinkWrap: true,
                  itemCount: opts.length,
                  itemBuilder: (context, index) {
                    final option = opts[index];
                    return ListTile(
                      dense: true,
                      title: Text(option),
                      onTap: () => onSelected(option),
                    );
                  },
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _ProductFormField extends StatelessWidget {
  const _ProductFormField({
    required this.controller,
    required this.label,
    required this.icon,
    this.hint,
    this.required = true,
    this.maxLines = 1,
    this.keyboardType,
    this.validator,
  });

  final TextEditingController controller;
  final String label;
  final IconData icon;
  final String? hint;
  final bool required;
  final int maxLines;
  final TextInputType? keyboardType;
  final String? Function(String?)? validator;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        maxLines: maxLines,
        keyboardType: keyboardType,
        validator:
            validator ??
            (value) {
              if (!required) return null;
              return value == null || value.trim().isEmpty
                  ? '$label is required'
                  : null;
            },
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          prefixIcon: Icon(icon, color: ProductsScreen.primaryNavy),
          filled: true,
          fillColor: const Color(0xFFF8FAFD),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: Color(0xFFD4DAE3)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: ProductsScreen.primaryBlue),
          ),
        ),
      ),
    );
  }
}

class _CategoryDropdown extends StatelessWidget {
  const _CategoryDropdown({
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final String? value;
  final List<String> items;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<String>(
        initialValue: value,
        items: items
            .map(
              (category) => DropdownMenuItem<String>(
                value: category,
                child: Text(category),
              ),
            )
            .toList(),
        onChanged: onChanged,
        validator: (value) =>
            value == null ? 'Food Category is required' : null,
        decoration: InputDecoration(
          labelText: 'Food Category',
          prefixIcon: const Icon(
            Icons.restaurant_menu_outlined,
            color: ProductsScreen.primaryNavy,
          ),
          filled: true,
          fillColor: const Color(0xFFF8FAFD),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: Color(0xFFD4DAE3)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: ProductsScreen.primaryBlue),
          ),
        ),
      ),
    );
  }
}

class _ProductGrid extends StatelessWidget {
  const _ProductGrid({required this.products, required this.onProductTap});

  final List<ProductItem> products;
  final ValueChanged<ProductItem> onProductTap;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: products.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 14,
        crossAxisSpacing: 14,
        childAspectRatio: 0.68,
      ),
      itemBuilder: (context, index) {
        return _ProductCard(
          product: products[index],
          onTap: () => onProductTap(products[index]),
        );
      },
    );
  }
}

class _ProductsMessageCard extends StatelessWidget {
  const _ProductsMessageCard({
    required this.icon,
    required this.title,
    required this.message,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ProductsScreen.borderBlue),
      ),
      child: Column(
        children: [
          Icon(icon, color: ProductsScreen.primaryNavy, size: 34),
          const SizedBox(height: 10),
          Text(
            title,
            style: const TextStyle(
              color: ProductsScreen.primaryNavy,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.black54, fontSize: 12),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: onAction,
            child: Text(
              actionLabel,
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProductCard extends StatefulWidget {
  const _ProductCard({required this.product, required this.onTap});

  final ProductItem product;
  final VoidCallback onTap;

  @override
  State<_ProductCard> createState() => _ProductCardState();
}

class _ProductCardState extends State<_ProductCard> {
  String get _favoriteKey =>
      favoriteKeyForProduct(id: widget.product.id, name: widget.product.name);

  @override
  void initState() {
    super.initState();
    FavoriteService.instance.load();
  }

  Future<void> _toggleFavorite() =>
      FavoriteService.instance.toggle(_favoriteKey);

  Future<void> _handleQuickAdd() async {
    if (!widget.product.isPurchasable) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('This product is unavailable.'),
          duration: Duration(seconds: 1),
        ),
      );
      return;
    }

    await CartService.instance.quickAdd(
      context: context,
      product: widget.product,
    );
  }

  @override
  Widget build(BuildContext context) {
    final product = widget.product;
    final isHot = product.soldCount > 0;
    final badgeLabel = isHot ? 'Hot' : 'New';

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1A1851).withValues(alpha: 0.05),
            blurRadius: 14,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      foregroundDecoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: GestureDetector(
              onTap: widget.onTap,
              behavior: HitTestBehavior.opaque,
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(17),
                ),
                child: Container(
                  color: const Color(0xFFF4F5F7),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
                        child: ProductImage(
                          imageUrl: product.imageUrl,
                          fallbackIcon: product.icon,
                          fit: BoxFit.contain,
                        ),
                      ),
                      Positioned(
                        top: 8,
                        left: 8,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 7,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: isHot
                                ? const Color(0xFFFCB316)
                                : const Color(0xFF1A1851),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            badgeLabel,
                            style: TextStyle(
                              color: isHot
                                  ? const Color(0xFF1A1851)
                                  : Colors.white,
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.2,
                            ),
                          ),
                        ),
                      ),
                      Positioned(
                        top: 8,
                        right: 8,
                        child: ListenableBuilder(
                          listenable: FavoriteService.instance,
                          builder: (context, _) {
                            final isFav = FavoriteService.instance.isFavorite(
                              _favoriteKey,
                            );
                            return Material(
                              color: Colors.white.withValues(alpha: 0.9),
                              shape: const CircleBorder(),
                              elevation: 0.5,
                              child: InkWell(
                                customBorder: const CircleBorder(),
                                onTap: _toggleFavorite,
                                child: Padding(
                                  padding: const EdgeInsets.all(6),
                                  child: Icon(
                                    isFav
                                        ? Icons.favorite
                                        : Icons.favorite_border,
                                    size: 16,
                                    color: isFav
                                        ? const Color(0xFFDC2626)
                                        : const Color(0xFF64748B),
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          GestureDetector(
            onTap: widget.onTap,
            behavior: HitTestBehavior.opaque,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.seller.trim().isNotEmpty
                        ? product.seller.trim()
                        : 'Campus Marketplace',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 10.5,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    product.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Color(0xFF1A1851),
                      fontSize: 13.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  if (product.category.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      product.category,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF94A3B8),
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 4, 12, 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: GestureDetector(
                    onTap: widget.onTap,
                    behavior: HitTestBehavior.opaque,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          product.price,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Color(0xFF1A1851),
                            fontSize: 15,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        if (product.hasReviews) ...[
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              for (int i = 1; i <= 5; i++)
                                Icon(
                                  i <= (product.rating ?? 0).floor()
                                      ? Icons.star
                                      : (i - (product.rating ?? 0) < 1 &&
                                                (product.rating ?? 0) -
                                                        (product.rating ?? 0)
                                                            .floor() >=
                                                    0.3
                                            ? Icons.star_half
                                            : Icons.star_border),
                                  size: 12,
                                  color: const Color(0xFFFCB316),
                                ),
                              const SizedBox(width: 3),
                              Text(
                                '(${product.reviewsCount})',
                                style: const TextStyle(
                                  fontSize: 10,
                                  color: Color(0xFF94A3B8),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                Material(
                  color: const Color(0xFF1A1851),
                  borderRadius: BorderRadius.circular(10),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: _handleQuickAdd,
                    child: const Padding(
                      padding: EdgeInsets.all(7),
                      child: Icon(
                        LucideIcons.shoppingBag,
                        color: Colors.white,
                        size: 17,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
