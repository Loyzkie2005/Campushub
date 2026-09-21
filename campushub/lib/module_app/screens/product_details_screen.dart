import 'dart:async';

import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../models/product_customization.dart';
import '../models/product_item.dart';
import '../services/cart_service.dart';
import '../services/chat_service.dart';
import '../services/favorite_service.dart';
import '../services/product_service.dart';
import '../widgets/add_to_cart_feedback.dart';
import '../widgets/product_image.dart';
import 'cart_screen.dart';
import 'checkout_screen.dart';
import 'messages_screen.dart';

class ProductDetailsScreen extends StatefulWidget {
  const ProductDetailsScreen({
    super.key,
    this.id,
    this.userId,
    this.sellerId,
    required this.name,
    required this.priceLabel,
    required this.imageUrl,
    this.images = const [],
    this.category = '',
    this.seller = '',
    this.sellerContact = '',
    this.stock,
    this.description = '',
    this.expiryDate,
    this.inventoryStatus = 'in_stock',
    this.inventoryStatusLabel = 'In Stock',
    this.isPurchasable = true,
    this.soldCount = 0,
    this.customization = const ProductCustomizationConfig(),
  });

  final int? id;
  final int? userId;
  final int? sellerId;
  final String name;
  final String priceLabel;
  final String imageUrl;
  final List<String> images;
  final String category;
  final String seller;
  final String sellerContact;
  final int? stock;
  final String description;
  final DateTime? expiryDate;
  final String inventoryStatus;
  final String inventoryStatusLabel;
  final bool isPurchasable;
  final int soldCount;
  final ProductCustomizationConfig customization;

  @override
  State<ProductDetailsScreen> createState() => _ProductDetailsScreenState();
}

class _ProductDetailsScreenState extends State<ProductDetailsScreen> {
  bool get _isFavorite => FavoriteService.instance.isFavorite(_favoriteKey);

  String get _favoriteKey =>
      favoriteKeyForProduct(id: widget.id, name: widget.name);

  List<ProductItem> _relatedProducts = const [];
  Timer? _sellerPresenceTimer;
  bool _sellerOnline = false;
  int _selectedImageIndex = 0;
  final PageController _imagePageController = PageController();
  bool _isAddingToCart = false;
  bool _addedToCart = false;

  List<String> get _galleryImages {
    final images = <String>[];

    void addImage(String image) {
      final value = image.trim();
      if (value.isNotEmpty && !images.contains(value)) images.add(value);
    }

    addImage(widget.imageUrl);
    for (final image in widget.images) {
      addImage(image);
    }
    for (final group in widget.customization.groups) {
      for (final option in group.options) {
        addImage(option.imageUrl);
      }
    }
    return images;
  }

  List<String> get _galleryVariantNames {
    final images = _galleryImages;
    final names = List<String>.filled(images.length, '');
    for (final group in widget.customization.groups) {
      for (final option in group.options) {
        final imageUrl = option.imageUrl.trim();
        final index = images.indexOf(imageUrl);
        if (index >= 0 && option.name.trim().isNotEmpty) {
          names[index] = option.name.trim();
        }
      }
    }
    return names;
  }

  void _selectImage(int index) {
    if (index < 0 || index >= _galleryImages.length) return;
    if (index != _selectedImageIndex) {
      setState(() => _selectedImageIndex = index);
    }
    if (_imagePageController.hasClients) {
      unawaited(
        _imagePageController.animateToPage(
          index,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        ),
      );
    }
  }

  void _onImagePageChanged(int index) {
    if (index == _selectedImageIndex) return;
    setState(() => _selectedImageIndex = index);
  }

  @override
  void initState() {
    super.initState();
    FavoriteService.instance.load();
    unawaited(_loadRelatedProducts());
    unawaited(_refreshSellerPresence());
    _sellerPresenceTimer = Timer.periodic(
      const Duration(seconds: 15),
      (_) => unawaited(_refreshSellerPresence()),
    );
  }

  @override
  void dispose() {
    _sellerPresenceTimer?.cancel();
    _imagePageController.dispose();
    super.dispose();
  }

  Future<void> _refreshSellerPresence() async {
    final sellerId = widget.sellerId;
    if (sellerId == null) return;

    var online = false;
    try {
      final ready = await ChatService.instance.initialize();
      if (ready) {
        online = await ChatService.instance.isActorOnline('admin:$sellerId');
      }
    } catch (_) {
      online = false;
    }

    if (!mounted || online == _sellerOnline) return;
    setState(() => _sellerOnline = online);
  }

  Future<void> _loadRelatedProducts() async {
    final rows = await ProductService.fetchRecommended(
      userId: widget.userId,
      seedProductId: widget.id,
      limit: 8,
    );
    if (!mounted) return;
    final items = rows
        .map((row) => ProductItem.fromJson(row))
        .where((p) => p.id == null || p.id != widget.id)
        .toList();
    setState(() => _relatedProducts = items);
  }

  Future<void> _openRelatedProduct(ProductItem product) async {
    if (product.id != null && widget.userId != null) {
      unawaited(
        ProductService.trackInteraction(
          userId: widget.userId!,
          productId: product.id!,
          interactionType: 'view',
        ),
      );
    }
    if (!mounted) return;
    await Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => ProductDetailsScreen(
          id: product.id,
          userId: widget.userId,
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

  Future<void> _toggleFavorite() =>
      FavoriteService.instance.toggle(_favoriteKey);

  void _openBuyOptions() {
    _openOptionsSheet(confirmLabel: 'Buy Now', onConfirm: _openCheckout);
  }

  void _openAddToCartOptions() {
    _openOptionsSheet(
      confirmLabel: 'Add to Cart',
      onConfirm: _addSelectionToCart,
    );
  }

  void _openOptionsSheet({
    required String confirmLabel,
    required void Function(BuySelection selection) onConfirm,
  }) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      ),
      builder: (context) => _BuyOptionsSheet(
        productName: widget.name,
        basePrice: _parsePriceLabel(widget.priceLabel),
        stock: widget.stock,
        imageUrl: widget.imageUrl,
        customization: widget.customization,
        confirmLabel: confirmLabel,
        onConfirm: onConfirm,
      ),
    );
  }

  Future<void> _addSelectionToCart(BuySelection selection) async {
    if (_isAddingToCart) return;
    setState(() {
      _isAddingToCart = true;
      _addedToCart = false;
    });

    try {
      await Future.wait<void>([
        CartService.instance.addFromProduct(
          productId: widget.id,
          productName: widget.name,
          imageUrl: widget.imageUrl,
          category: widget.category,
          sellerName: widget.seller,
          sellerContact: widget.sellerContact,
          basePrice: _parsePriceLabel(widget.priceLabel),
          selection: selection,
        ),
        Future<void>.delayed(const Duration(milliseconds: 450)),
      ]);
      if (!mounted) return;
      setState(() {
        _isAddingToCart = false;
        _addedToCart = true;
      });
      AddToCartFeedback.show(context);
      await Future<void>.delayed(const Duration(milliseconds: 1200));
      if (mounted) setState(() => _addedToCart = false);
    } catch (_) {
      if (mounted) {
        setState(() {
          _isAddingToCart = false;
          _addedToCart = false;
        });
      }
      rethrow;
    }
  }

  void _handleAddToCart() {
    if (!widget.isPurchasable || _isAddingToCart) return;
    if (widget.customization.hasOptions) {
      _openAddToCartOptions();
      return;
    }
    unawaited(
      _addSelectionToCart(
        BuySelection(
          quantity: 1,
          selections: const [],
          summary: '',
          unitPrice: _parsePriceLabel(widget.priceLabel),
        ),
      ),
    );
  }

  double _parsePriceLabel(String label) {
    final firstSegment = label.split(RegExp(r'[–\-]')).first;
    final cleaned = firstSegment.replaceAll(RegExp(r'[^0-9.]'), '');
    return double.tryParse(cleaned) ?? 0;
  }

  void _openCheckout(BuySelection selection) {
    if (widget.id != null && widget.userId != null) {
      unawaited(
        ProductService.trackInteraction(
          userId: widget.userId!,
          productId: widget.id!,
          interactionType: 'purchase',
        ),
      );
    }

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => CheckoutScreen(
          productId: widget.id,
          productName: widget.name,
          basePrice: _parsePriceLabel(widget.priceLabel),
          selection: selection,
          imageUrl: widget.imageUrl,
          category: widget.category,
          sellerName: widget.seller,
          sellerContact: widget.sellerContact,
        ),
      ),
    );
  }

  String _formatPriceDisplay() {
    final value = _parsePriceLabel(widget.priceLabel);
    return '\u20b1${value.toStringAsFixed(value.truncateToDouble() == value ? 0 : 2)}';
  }

  Future<void> _openSellerChat() async {
    try {
      final ready = await ChatService.instance.initialize();
      if (!ready) {
        throw const ChatException('Please log in again to use chat.');
      }
      if (!mounted) return;

      if (widget.sellerId == null) {
        await Navigator.of(
          context,
        ).push(MaterialPageRoute(builder: (_) => const MessagesPage()));
        return;
      }

      final conversation = await ChatService.instance.createConversation(
        participantActorKey: 'admin:${widget.sellerId}',
        participantDisplayName: widget.seller.isEmpty
            ? 'CampusHub Seller'
            : widget.seller,
        contextKey: widget.id == null
            ? 'product-name:${widget.name}'
            : 'product:${widget.id}',
      );
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ChatConversationScreen(conversation: conversation),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    final stockColor = ProductItem.statusColor(
      widget.inventoryStatus,
      widget.stock,
    );
    final canPurchase = widget.isPurchasable;
    final galleryImages = _galleryImages;
    final galleryVariantNames = _galleryVariantNames;
    final displayImages = galleryImages.isEmpty
        ? <String>[widget.imageUrl]
        : galleryImages;
    final displayVariantNames = galleryImages.isEmpty
        ? const <String>['']
        : galleryVariantNames;
    final selectedImageIndex = _selectedImageIndex >= displayImages.length
        ? 0
        : _selectedImageIndex;

    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      body: Column(
        children: [
          Expanded(
            child: CustomScrollView(
              slivers: [
                SliverAppBar(
                  backgroundColor: Colors.white,
                  surfaceTintColor: Colors.white,
                  elevation: 0,
                  scrolledUnderElevation: 0,
                  floating: true,
                  centerTitle: true,
                  leading: IconButton(
                    tooltip: 'Back',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(
                      Icons.arrow_back,
                      color: Color(0xFF1A1851),
                    ),
                  ),
                  title: const Text(
                    'Details',
                    style: TextStyle(
                      color: Color(0xFF1A1851),
                      fontSize: 17,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  actions: [
                    const _ProductDetailsCartButton(),
                    IconButton(
                      tooltip: _isFavorite
                          ? 'Remove from favorites'
                          : 'Add to favorites',
                      onPressed: _toggleFavorite,
                      icon: Icon(
                        _isFavorite
                            ? Icons.favorite_rounded
                            : Icons.favorite_border_rounded,
                        color: const Color(0xFF1A1851),
                      ),
                    ),
                  ],
                ),
                SliverToBoxAdapter(
                  child: _ProductHeroImage(
                    images: displayImages,
                    currentIndex: selectedImageIndex,
                    controller: _imagePageController,
                    onPageChanged: _onImagePageChanged,
                  ),
                ),
                SliverToBoxAdapter(
                  child: _ProductInfoContainer(
                    priceText: _formatPriceDisplay(),
                    name: widget.name,
                    canPurchase: canPurchase,
                    stockColor: stockColor,
                    inventoryStatus: widget.inventoryStatus,
                    description: widget.description,
                    images: galleryImages,
                    variantNames: displayVariantNames,
                    selectedImageIndex: selectedImageIndex,
                    onImageSelected: _selectImage,
                    sellerName: widget.seller,
                    sellerOnline: _sellerOnline,
                    onChat: _openSellerChat,
                    expiryDate: widget.expiryDate,
                    formatExpiry: _formatExpiry,
                    relatedProducts: _relatedProducts,
                    onRelatedTap: _openRelatedProduct,
                    soldCount: widget.soldCount,
                  ),
                ),
              ],
            ),
          ),
          _ProductBottomBar(
            canPurchase: canPurchase,
            isAddingToCart: _isAddingToCart,
            addedToCart: _addedToCart,
            onChat: _openSellerChat,
            onAddToCart: _handleAddToCart,
            onBuyNow: _openBuyOptions,
          ),
        ],
      ),
    );
  }

  String _formatExpiry(DateTime date) {
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }
}

class _ProductHeroImage extends StatelessWidget {
  const _ProductHeroImage({
    required this.images,
    required this.currentIndex,
    required this.controller,
    required this.onPageChanged,
  });

  final List<String> images;
  final int currentIndex;
  final PageController controller;
  final ValueChanged<int> onPageChanged;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1,
      child: Stack(
        fit: StackFit.expand,
        children: [
          PageView.builder(
            controller: controller,
            itemCount: images.length,
            onPageChanged: onPageChanged,
            itemBuilder: (context, index) => ProductImage(
              imageUrl: images[index],
              backgroundColor: Colors.white,
            ),
          ),
          if (images.length > 1)
            Positioned(
              left: 0,
              right: 0,
              bottom: 12,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(images.length, (index) {
                  final isActive = index == currentIndex;
                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    width: isActive ? 18 : 7,
                    height: 7,
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    decoration: BoxDecoration(
                      color: isActive ? const Color(0xFF1A1851) : Colors.white,
                      borderRadius: BorderRadius.circular(99),
                      border: Border.all(
                        color: const Color(0xFF1A1851).withValues(alpha: 0.35),
                      ),
                    ),
                  );
                }),
              ),
            ),
        ],
      ),
    );
  }
}

class _ProductDetailsCartButton extends StatelessWidget {
  const _ProductDetailsCartButton();

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Cart',
      onPressed: () {
        Navigator.of(
          context,
        ).push(MaterialPageRoute(builder: (_) => const CartScreen()));
      },
      icon: ListenableBuilder(
        listenable: CartService.instance,
        builder: (context, _) {
          final count = CartService.instance.itemCount;
          return Stack(
            clipBehavior: Clip.none,
            alignment: Alignment.center,
            children: [
              const Icon(
                LucideIcons.shoppingBag,
                size: 20,
                color: Color(0xFF1A1851),
              ),
              if (count > 0)
                Positioned(
                  right: -4,
                  top: -4,
                  child: Container(
                    padding: const EdgeInsets.all(3),
                    constraints: const BoxConstraints(
                      minWidth: 14,
                      minHeight: 14,
                    ),
                    decoration: const BoxDecoration(
                      color: Color(0xFFFCB316),
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      count > 99 ? '99+' : '$count',
                      style: const TextStyle(
                        fontSize: 8,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF1A1851),
                      ),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _ProductInfoContainer extends StatelessWidget {
  const _ProductInfoContainer({
    required this.priceText,
    required this.name,
    required this.canPurchase,
    required this.stockColor,
    required this.inventoryStatus,
    required this.description,
    required this.images,
    required this.variantNames,
    required this.selectedImageIndex,
    required this.onImageSelected,
    required this.sellerName,
    required this.sellerOnline,
    required this.onChat,
    required this.expiryDate,
    required this.formatExpiry,
    required this.relatedProducts,
    required this.onRelatedTap,
    this.soldCount = 0,
  });

  final String priceText;
  final String name;
  final bool canPurchase;
  final Color stockColor;
  final String inventoryStatus;
  final String description;
  final List<String> images;
  final List<String> variantNames;
  final int selectedImageIndex;
  final ValueChanged<int> onImageSelected;
  final String sellerName;
  final bool sellerOnline;
  final VoidCallback onChat;
  final DateTime? expiryDate;
  final String Function(DateTime) formatExpiry;
  final List<ProductItem> relatedProducts;
  final ValueChanged<ProductItem> onRelatedTap;
  final int soldCount;

  String get soldLabel {
    if (soldCount >= 1000) {
      final k = soldCount / 1000;
      final text = (soldCount % 1000 == 0)
          ? k.toStringAsFixed(0)
          : k.toStringAsFixed(1);
      return '${text}k sold';
    }
    return '$soldCount sold';
  }

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (images.length > 1) ...[
                  _ProductImageThumbnails(
                    images: images,
                    variantNames: variantNames,
                    selectedIndex: selectedImageIndex,
                    onSelected: onImageSelected,
                  ),
                  const SizedBox(height: 12),
                ],
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: Text(
                        priceText,
                        style: const TextStyle(
                          color: Color(0xFFEE4D2D),
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                          height: 1.2,
                        ),
                      ),
                    ),
                    Text(
                      soldLabel,
                      style: const TextStyle(
                        color: Color(0xFF94A3B8),
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  name,
                  style: const TextStyle(
                    color: Color(0xFF222222),
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    height: 1.3,
                  ),
                ),
                if (!canPurchase) ...[
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEF2F2),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFFECACA)),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.warning_amber_rounded,
                          color: stockColor,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            inventoryStatus == 'expired'
                                ? 'This product has expired and is unavailable.'
                                : 'This product is out of stock.',
                            style: TextStyle(
                              color: stockColor,
                              fontWeight: FontWeight.w700,
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          const _ShopeeHr(),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Details',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                    color: Color(0xFF222222),
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  description.isEmpty
                      ? 'No description provided.'
                      : description,
                  style: TextStyle(
                    color: Colors.grey.shade700,
                    fontSize: 14,
                    height: 1.45,
                  ),
                ),
                if (expiryDate != null) ...[
                  const SizedBox(height: 14),
                  _DetailLine(
                    label: 'Expiry Date',
                    value: formatExpiry(expiryDate!),
                    valueColor: inventoryStatus == 'expiring_soon'
                        ? const Color(0xFFB45309)
                        : const Color(0xFF222222),
                  ),
                ],
                const SizedBox(height: 16),
                const Divider(height: 1, color: Color(0xFFECECEC)),
                const SizedBox(height: 14),
                _SellerIdentity(
                  name: sellerName,
                  online: sellerOnline,
                  onChat: onChat,
                ),
              ],
            ),
          ),
          const _ShopeeHr(),
          const Padding(
            padding: EdgeInsets.fromLTRB(14, 14, 14, 14),
            child: _ProductReviewsSection(),
          ),
          const _ShopeeHr(),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 14, 20),
            child: _YouMayAlsoLikeSection(
              products: relatedProducts,
              onTap: onRelatedTap,
            ),
          ),
        ],
      ),
    );
  }
}

class _ProductImageThumbnails extends StatelessWidget {
  const _ProductImageThumbnails({
    required this.images,
    required this.variantNames,
    required this.selectedIndex,
    required this.onSelected,
  });

  final List<String> images;
  final List<String> variantNames;
  final int selectedIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 68,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: images.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final selected = index == selectedIndex;
          final variantName = index < variantNames.length
              ? variantNames[index]
              : '';
          return Tooltip(
            message: variantName.isEmpty
                ? 'View image ${index + 1}'
                : variantName,
            child: InkWell(
              onTap: () => onSelected(index),
              borderRadius: BorderRadius.circular(4),
              child: SizedBox(
                width: 56,
                child: Column(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      clipBehavior: Clip.antiAlias,
                      decoration: BoxDecoration(
                        color: const Color(0xFFF8FAFC),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                          color: selected
                              ? const Color(0xFF1A1851)
                              : const Color(0xFFD8DEE9),
                          width: selected ? 2 : 1,
                        ),
                      ),
                      child: ProductImage(
                        imageUrl: images[index],
                        backgroundColor: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    SizedBox(
                      height: 14,
                      child: Text(
                        variantName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: selected
                              ? const Color(0xFF1A1851)
                              : const Color(0xFF64748B),
                          fontSize: 10,
                          fontWeight: selected
                              ? FontWeight.w800
                              : FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Full-bleed hairline divider (Shopee-style).
class _ShopeeHr extends StatelessWidget {
  const _ShopeeHr();

  @override
  Widget build(BuildContext context) {
    return const SizedBox(
      width: double.infinity,
      height: 1,
      child: ColoredBox(color: Color(0xFFECECEC)),
    );
  }
}

class _DetailLine extends StatelessWidget {
  const _DetailLine({
    required this.label,
    required this.value,
    required this.valueColor,
  });

  final String label;
  final String value;
  final Color valueColor;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          width: 90,
          child: Text(
            label,
            style: TextStyle(
              color: Colors.grey.shade600,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              color: valueColor,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }
}

class _SellerIdentity extends StatelessWidget {
  const _SellerIdentity({
    required this.name,
    required this.online,
    required this.onChat,
  });

  final String name;
  final bool online;
  final VoidCallback onChat;

  @override
  Widget build(BuildContext context) {
    final displayName = name.trim().isEmpty ? 'CampusHub Seller' : name.trim();
    final initial = displayName.characters.first.toUpperCase();

    return Row(
      children: [
        CircleAvatar(
          radius: 21,
          backgroundColor: const Color(0xFF1A1851),
          child: Text(
            initial,
            style: const TextStyle(
              color: Color(0xFFFCB316),
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                displayName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Color(0xFF222222),
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 3),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Seller',
                    style: TextStyle(
                      color: Color(0xFF64748B),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (online)
                    Tooltip(
                      message: 'Online',
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: Color(0xFF16A34A),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Text(
                            'Online',
                            style: TextStyle(
                              color: Color(0xFF16A34A),
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    )
                  else
                    const Text(
                      'Offline',
                      style: TextStyle(
                        color: Color(0xFF94A3B8),
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        TextButton.icon(
          onPressed: onChat,
          icon: const Icon(Icons.chat_bubble_outline, size: 16),
          label: const Text('Chat Now'),
          style: TextButton.styleFrom(
            foregroundColor: const Color(0xFF1A1851),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
            side: const BorderSide(color: Color(0xFF1A1851), width: 1.5),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            textStyle: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
      ],
    );
  }
}

class _ProductBottomBar extends StatelessWidget {
  const _ProductBottomBar({
    required this.canPurchase,
    required this.isAddingToCart,
    required this.addedToCart,
    required this.onChat,
    required this.onAddToCart,
    required this.onBuyNow,
  });

  final bool canPurchase;
  final bool isAddingToCart;
  final bool addedToCart;
  final VoidCallback onChat;
  final VoidCallback onAddToCart;
  final VoidCallback onBuyNow;

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.paddingOf(context).bottom;

    return Container(
      padding: EdgeInsets.fromLTRB(10, 8, 10, 8 + bottomInset),
      decoration: BoxDecoration(
        color: Colors.white,
        border: const Border(
          top: BorderSide(color: Color(0xFFE2E8F0), width: 1),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          _BottomActionIcon(
            icon: LucideIcons.messageSquare,
            label: 'Chat',
            onTap: onChat,
          ),
          const SizedBox(width: 8),
          Container(width: 1, height: 36, color: const Color(0xFFE2E8F0)),
          const SizedBox(width: 8),
          _BottomActionIcon(
            icon: LucideIcons.shoppingBag,
            label: 'Add to Bag',
            width: 72,
            loading: isAddingToCart,
            completed: addedToCart,
            onTap: canPurchase && !isAddingToCart ? onAddToCart : null,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: SizedBox(
              height: 46,
              child: ElevatedButton(
                onPressed: canPurchase ? onBuyNow : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1A1851),
                  foregroundColor: Colors.white,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                child: const Text(
                  'Buy Now',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BottomActionIcon extends StatelessWidget {
  const _BottomActionIcon({
    required this.icon,
    required this.label,
    required this.onTap,
    this.width = 52,
    this.loading = false,
    this.completed = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final double width;
  final bool loading;
  final bool completed;

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    final foregroundColor = completed
        ? const Color(0xFF16A34A)
        : enabled || loading
        ? const Color(0xFF1A1851)
        : Colors.grey.shade400;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: SizedBox(
        width: width,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (loading)
              const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2.2,
                  color: Color(0xFF1A1851),
                ),
              )
            else
              Icon(
                completed ? Icons.check_circle_rounded : icon,
                size: 22,
                color: foregroundColor,
              ),
            const SizedBox(height: 2),
            Text(
              loading
                  ? 'Adding...'
                  : completed
                  ? 'Added'
                  : label,
              maxLines: 1,
              overflow: TextOverflow.visible,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: foregroundColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.trailing});

  final String label;
  final Widget trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE6EBF2)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: Color(0xFF0F172A),
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
          trailing,
        ],
      ),
    );
  }
}

class _QuantityStepper extends StatelessWidget {
  const _QuantityStepper({
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
          _QuantityButton(icon: Icons.remove, onTap: onMinus),
          SizedBox(
            width: 38,
            child: Text(
              '$quantity',
              textAlign: TextAlign.center,
              style: const TextStyle(fontWeight: FontWeight.w900),
            ),
          ),
          _QuantityButton(icon: Icons.add, onTap: onPlus),
        ],
      ),
    );
  }
}

class _QuantityButton extends StatelessWidget {
  const _QuantityButton({required this.icon, required this.onTap});

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

class _BuyOptionsSheet extends StatefulWidget {
  const _BuyOptionsSheet({
    required this.productName,
    required this.basePrice,
    required this.stock,
    required this.imageUrl,
    required this.customization,
    required this.confirmLabel,
    required this.onConfirm,
  });

  final String productName;
  final double basePrice;
  final int? stock;
  final String imageUrl;
  final ProductCustomizationConfig customization;
  final String confirmLabel;
  final void Function(BuySelection selection) onConfirm;

  @override
  State<_BuyOptionsSheet> createState() => _BuyOptionsSheetState();
}

class _BuyOptionsSheetState extends State<_BuyOptionsSheet>
    with SingleTickerProviderStateMixin {
  int _quantity = 1;
  final Map<String, Set<String>> _selectedOptions = {};
  late final AnimationController _animController;
  late final Animation<double> _scaleAnim;
  late final Animation<double> _fadeAnim;
  bool _isAnimating = false;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _scaleAnim = Tween<double>(begin: 1.0, end: 0.3).animate(
      CurvedAnimation(parent: _animController, curve: Curves.easeInBack),
    );
    _fadeAnim = Tween<double>(
      begin: 1.0,
      end: 0.0,
    ).animate(CurvedAnimation(parent: _animController, curve: Curves.easeOut));
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  double get _extraTotal {
    if (!widget.customization.hasOptions) return 0;
    var total = 0.0;
    for (final group in widget.customization.groups) {
      final selected = _selectedOptions[group.name] ?? {};
      for (final optionName in selected) {
        final option = group.options.firstWhere(
          (item) => item.name == optionName,
          orElse: () => const ProductCustomizationOption(name: ''),
        );
        total += option.extraPrice;
      }
    }
    return total;
  }

  double get _unitPrice => widget.basePrice + _extraTotal;

  List<SelectedCustomization> get _selections {
    final rows = <SelectedCustomization>[];
    for (final group in widget.customization.groups) {
      final selected = _selectedOptions[group.name] ?? {};
      for (final optionName in selected) {
        final option = group.options.firstWhere(
          (item) => item.name == optionName,
          orElse: () => const ProductCustomizationOption(name: ''),
        );
        if (option.name.isEmpty) continue;
        rows.add(
          SelectedCustomization(
            group: group.name,
            option: option.name,
            extraPrice: option.extraPrice,
          ),
        );
      }
    }
    return rows;
  }

  void _toggleOption(ProductCustomizationGroup group, String optionName) {
    setState(() {
      final bucket = _selectedOptions.putIfAbsent(group.name, () => <String>{});
      if (group.isMultiple) {
        if (bucket.contains(optionName)) {
          bucket.remove(optionName);
        } else {
          bucket.add(optionName);
        }
      } else {
        if (bucket.contains(optionName)) {
          bucket.clear();
        } else {
          bucket
            ..clear()
            ..add(optionName);
        }
      }
    });
  }

  void _changeQuantity(int delta) {
    final maxStock = widget.stock == null || widget.stock! <= 0
        ? 99
        : widget.stock!;
    setState(() => _quantity = (_quantity + delta).clamp(1, maxStock));
  }

  void _checkout() {
    setState(() => _isAnimating = true);
    _animController.forward().then((_) {
      final selections = _selections;
      Navigator.of(context).pop();
      widget.onConfirm(
        BuySelection(
          quantity: _quantity,
          selections: selections,
          summary: buildCustomizationSummary(selections),
          unitPrice: _unitPrice,
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        16,
        12,
        16,
        16 + MediaQuery.viewInsetsOf(context).bottom,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 44,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFFCBD5E1),
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
            ),
            const SizedBox(height: 14),
            // Product name on top, then price (updates with variant)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AnimatedBuilder(
                  animation: _animController,
                  builder: (context, child) => Transform.scale(
                    scale: _isAnimating ? _scaleAnim.value : 1.0,
                    child: Opacity(
                      opacity: _isAnimating ? _fadeAnim.value : 1.0,
                      child: child,
                    ),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      width: 90,
                      height: 90,
                      color: const Color(0xFFF1F5F9),
                      child: widget.imageUrl.isNotEmpty
                          ? ProductImage(
                              imageUrl: widget.imageUrl,
                              fallbackIcon: Icons.image_outlined,
                            )
                          : const Icon(
                              Icons.image_outlined,
                              size: 32,
                              color: Color(0xFF94A3B8),
                            ),
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.productName,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Color(0xFF1e293b),
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '\u20b1${(_unitPrice * _quantity).toStringAsFixed(2)}',
                        style: const TextStyle(
                          color: Color(0xFFDC2626),
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      if (widget.stock != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          'Stock: ${widget.stock}',
                          style: const TextStyle(
                            color: Color(0xFF64748B),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
            if (widget.customization.hasOptions) ...[
              const SizedBox(height: 18),
              ...widget.customization.groups.map((group) {
                final selected = _selectedOptions[group.name] ?? {};
                return Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        group.name,
                        style: const TextStyle(
                          color: Color(0xFF1e293b),
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: group.options
                            .map((option) {
                              final isSelected = selected.contains(option.name);
                              return FilterChip(
                                label: Text(option.name),
                                selected: isSelected,
                                showCheckmark: false,
                                onSelected: (_) =>
                                    _toggleOption(group, option.name),
                                selectedColor: Colors.white,
                                backgroundColor: Colors.white,
                                labelStyle: TextStyle(
                                  color: isSelected
                                      ? const Color(0xFFFCB316)
                                      : const Color(0xFF334155),
                                  fontWeight: FontWeight.w700,
                                  fontSize: 13,
                                ),
                                side: BorderSide(
                                  color: isSelected
                                      ? const Color(0xFFFCB316)
                                      : const Color(0xFFE2E8F0),
                                  width: isSelected ? 2 : 1,
                                ),
                              );
                            })
                            .toList(growable: false),
                      ),
                    ],
                  ),
                );
              }),
            ],
            const Divider(height: 24, color: Color(0xFFE2E8F0)),
            _InfoRow(
              label: 'Quantity',
              trailing: _QuantityStepper(
                quantity: _quantity,
                onMinus: () => _changeQuantity(-1),
                onPlus: () => _changeQuantity(1),
              ),
            ),
            const SizedBox(height: 18),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: _checkout,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1A1851),
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                child: Text(
                  widget.confirmLabel,
                  style: const TextStyle(
                    fontWeight: FontWeight.w900,
                    fontSize: 15,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProductReviewsSection extends StatelessWidget {
  const _ProductReviewsSection();

  // Placeholder until review API is wired; each item is separated by an HR.
  static const _reviews = <_ReviewItemData>[];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Ratings & Reviews',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 15,
            color: Color(0xFF222222),
          ),
        ),
        const SizedBox(height: 12),
        if (_reviews.isEmpty)
          const Padding(
            padding: EdgeInsets.fromLTRB(0, 28, 0, 20),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Icon(
                    Icons.rate_review_outlined,
                    size: 36,
                    color: Color(0xFFCBD5E1),
                  ),
                  SizedBox(height: 10),
                  Text(
                    'No reviews yet',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                      color: Color(0xFF64748B),
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Be the first to review this product',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                  ),
                ],
              ),
            ),
          )
        else
          for (var i = 0; i < _reviews.length; i++) ...[
            if (i > 0) const _ShopeeHr(),
            _ReviewTile(review: _reviews[i]),
          ],
      ],
    );
  }
}

class _ReviewItemData {
  const _ReviewItemData({
    required this.author,
    required this.rating,
    required this.comment,
    required this.dateLabel,
  });

  final String author;
  final int rating;
  final String comment;
  final String dateLabel;
}

class _ReviewTile extends StatelessWidget {
  const _ReviewTile({required this.review});

  final _ReviewItemData review;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 16,
                backgroundColor: const Color(0xFFE2E8F0),
                child: Text(
                  review.author.isNotEmpty
                      ? review.author[0].toUpperCase()
                      : '?',
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 13,
                    color: Color(0xFF1A1851),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  review.author,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                    color: Color(0xFF222222),
                  ),
                ),
              ),
              Text(
                review.dateLabel,
                style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            children: List.generate(5, (index) {
              final filled = index < review.rating;
              return Icon(
                filled ? Icons.star_rounded : Icons.star_border_rounded,
                size: 14,
                color: filled
                    ? const Color(0xFFFCB316)
                    : const Color(0xFFCBD5E1),
              );
            }),
          ),
          const SizedBox(height: 8),
          Text(
            review.comment,
            style: TextStyle(
              fontSize: 13,
              height: 1.45,
              color: Colors.grey.shade700,
            ),
          ),
        ],
      ),
    );
  }
}

class _YouMayAlsoLikeSection extends StatelessWidget {
  const _YouMayAlsoLikeSection({required this.products, required this.onTap});

  final List<ProductItem> products;
  final ValueChanged<ProductItem> onTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        const SizedBox(
          width: double.infinity,
          child: Text(
            'You May Also Like',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontWeight: FontWeight.w800,
              fontSize: 15,
              color: Color(0xFF222222),
            ),
          ),
        ),
        const SizedBox(height: 12),
        if (products.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text(
              'No suggestions yet',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade500),
            ),
          )
        else
          SizedBox(
            height: 196,
            width: double.infinity,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: products.length,
              separatorBuilder: (_, _) => const SizedBox(width: 10),
              itemBuilder: (context, index) {
                final product = products[index];
                return _RelatedProductCard(
                  product: product,
                  onTap: () => onTap(product),
                );
              },
            ),
          ),
      ],
    );
  }
}

class _RelatedProductCard extends StatelessWidget {
  const _RelatedProductCard({required this.product, required this.onTap});

  final ProductItem product;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: SizedBox(
        width: 120,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: AspectRatio(
                aspectRatio: 1,
                child: ProductImage(
                  imageUrl: product.imageUrl,
                  backgroundColor: const Color(0xFFF8FAFC),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              product.name,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: Color(0xFF222222),
                height: 1.25,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              product.price,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w800,
                color: Color(0xFFEE4D2D),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
