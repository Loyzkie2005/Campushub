import 'dart:async';

import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../config/api_config.dart';
import '../theme/marketplace_colors.dart';
import '../models/product_item.dart';
import '../services/cart_service.dart';
import '../services/favorite_service.dart';
import '../services/product_service.dart';
import '../services/seller_application_service.dart';
import '../session/session_service.dart';
import '../widgets/cart_icon_button.dart';
import '../widgets/product_image.dart';
import 'product_details_screen.dart';
import 'seller_add_product_page.dart';

class ProductsScreen extends StatefulWidget {
  const ProductsScreen({super.key, this.favoritesOnly = false});
  final bool favoritesOnly;

  static const Color primaryNavy = Color(0xFF142B47);
  static const Color primaryBlue = Color(0xFF1A56DB);
  static const Color webBrandBlue = Color(0xFF0175C2);
  static const Color campusGold = Color(0xFFFCB315);
  static const Color pageBackground = Color(0xFFF8FAFD);
  static const Color borderBlue = Color(0xFFBFD7FF);
  static String get apiBaseUrl => ApiConfig.baseUrl;
  static List<String> get apiBaseUrls => ApiConfig.serverBaseUrls;

  /// Rechecks seller access before opening the existing listing workflow.
  static Future<bool?> showAddProductPage(BuildContext context) async {
    Map<String, dynamic> state;
    try {
      state = await const SellerApplicationService().status();
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Unable to verify seller access. Please retry.'),
          ),
        );
      }
      return null;
    }
    if (!context.mounted) return null;
    if (state['is_approved_seller'] != true) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Approved active seller access is required.'),
        ),
      );
      return null;
    }
    final categories = (state['categories'] as List? ?? [])
        .whereType<String>()
        .toList();
    return Navigator.of(context).push<bool>(
      MaterialPageRoute(
        settings: const RouteSettings(name: '/seller/add-product'),
        builder: (_) => SellerAddProductPage(categories: categories),
      ),
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
    if (!mounted) return;
    setState(() {
      _isLoadingProducts = true;
      _productsError = null;
    });
    try {
      final products = await ProductService.fetchApproved();
      if (!mounted) return;
      await FavoriteService.instance.load();
      if (!mounted) return;
      setState(
        () => _approvedProducts = widget.favoritesOnly
            ? products
                  .where(
                    (product) => FavoriteService.instance.isFavorite(
                      favoriteKeyForProduct(id: product.id, name: product.name),
                    ),
                  )
                  .toList()
            : products,
      );
    } catch (_) {
      if (!mounted) return;
      setState(() => _productsError = ProductService.connectionMessage);
    } finally {
      if (mounted) setState(() => _isLoadingProducts = false);
    }
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
          sellerRef: product.sellerRef,
          name: product.name,
          priceLabel: product.price,
          imageUrl: product.imageUrl,
          images: product.images,
          category: product.category,
          seller: product.seller,
          sellerPhotoUrl: product.sellerPhotoUrl,
          sellerContact: product.sellerContact,
          stock: product.stock,
          description: product.description,
          expiryDate: product.expiryDate,
          inventoryStatus: product.inventoryStatus,
          inventoryStatusLabel: product.inventoryStatusLabel,
          isPurchasable: product.isPurchasable,
          soldCount: product.soldCount,
          rating: product.rating,
          reviewsCount: product.reviewsCount,
          submittedAt: product.submittedAt,
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
        color: MarketplaceColors.cardSurface,
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
                  color: MarketplaceColors.imageSurface,
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
                                ? const Color(0xFFFCB315)
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
                                    color: const Color(0xFF1A1851),
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
                                  color: const Color(0xFFFCB315),
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
