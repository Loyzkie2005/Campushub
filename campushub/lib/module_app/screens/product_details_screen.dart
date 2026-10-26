import 'dart:async';

import 'package:flutter/material.dart';
import '../theme/app_typography.dart';
import '../theme/marketplace_colors.dart';
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
    this.sellerRef,
    required this.name,
    required this.priceLabel,
    required this.imageUrl,
    this.images = const [],
    this.category = '',
    this.seller = '',
    this.sellerPhotoUrl = '',
    this.sellerContact = '',
    this.stock,
    this.description = '',
    this.expiryDate,
    this.inventoryStatus = 'in_stock',
    this.inventoryStatusLabel = 'In Stock',
    this.isPurchasable = true,
    this.soldCount = 0,
    this.rating,
    this.reviewsCount = 0,
    this.submittedAt,
    this.customization = const ProductCustomizationConfig(),
    this.ownerView = false,
    this.approvalStatus = '',
    this.rejectionReason = '',
  });

  final int? id;
  final int? userId;
  final int? sellerId;
  final String? sellerRef;
  final String name;
  final String priceLabel;
  final String imageUrl;
  final List<String> images;
  final String category;
  final String seller;
  final String sellerPhotoUrl;
  final String sellerContact;
  final int? stock;
  final String description;
  final DateTime? expiryDate;
  final String inventoryStatus;
  final String inventoryStatusLabel;
  final bool isPurchasable;
  final int soldCount;
  final double? rating;
  final int reviewsCount;
  final DateTime? submittedAt;
  final ProductCustomizationConfig customization;
  final bool ownerView;
  final String approvalStatus, rejectionReason;

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
  final GlobalKey _reviewsKey = GlobalKey();
  bool _isAddingToCart = false;
  bool _addedToCart = false;
  final Map<String, Set<String>> _selectedOptions = {};

  List<String> get _galleryImages {
    final images = <String>[];

    void addImage(String image) {
      final value = image.trim();
      if (value.isNotEmpty && !images.contains(value) && images.length < 6) {
        images.add(value);
      }
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
    if (!widget.ownerView) {
      FavoriteService.instance.load();
      unawaited(_loadRelatedProducts());
      unawaited(_refreshSellerPresence());
      _sellerPresenceTimer = Timer.periodic(
        const Duration(seconds: 15),
        (_) => unawaited(_refreshSellerPresence()),
      );
    }
  }

  @override
  void dispose() {
    _sellerPresenceTimer?.cancel();
    _imagePageController.dispose();
    super.dispose();
  }

  Future<void> _refreshSellerPresence() async {
    final actor =
        widget.sellerRef ??
        (widget.sellerId == null ? null : 'admin:${widget.sellerId}');
    if (actor == null) return;

    var online = false;
    try {
      final ready = await ChatService.instance.initialize();
      if (ready) {
        online = await ChatService.instance.isActorOnline(actor);
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

  Future<void> _toggleFavorite() =>
      FavoriteService.instance.toggle(_favoriteKey);

  List<SelectedCustomization> get _selections => [
    if (widget.customization.hasOptions)
      for (final group in widget.customization.groups)
        for (final option in group.options)
          if (_selectedOptions[group.name]?.contains(option.name) ?? false)
            SelectedCustomization(
              group: group.name,
              option: option.name,
              extraPrice: option.extraPrice,
            ),
  ];

  double get _unitPrice =>
      _parsePriceLabel(widget.priceLabel) +
      _selections.fold<double>(
        0,
        (total, selection) => total + selection.extraPrice,
      );

  void _toggleOption(ProductCustomizationGroup group, String name) {
    setState(() {
      final selected = _selectedOptions.putIfAbsent(group.name, () => {});
      if (selected.contains(name)) {
        selected.remove(name);
      } else {
        if (!group.isMultiple) selected.clear();
        selected.add(name);
      }
    });
    final option = group.options.firstWhere((option) => option.name == name);
    if (_selectedOptions[group.name]!.contains(name) &&
        option.imageUrl.isNotEmpty) {
      _selectImage(_galleryImages.indexOf(option.imageUrl.trim()));
    }
  }

  BuySelection? _purchaseSelection() {
    if (!widget.isPurchasable) return null;
    if (widget.customization.hasOptions) {
      for (final group in widget.customization.groups) {
        if (group.required && (_selectedOptions[group.name]?.isEmpty ?? true)) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Please choose ${group.name}.')),
          );
          return null;
        }
      }
    }
    final selections = _selections;
    return BuySelection(
      quantity: 1,
      selections: selections,
      summary: buildCustomizationSummary(selections),
      unitPrice: _unitPrice,
    );
  }

  void _openBuyOptions() {
    final selection = _purchaseSelection();
    if (selection != null) _openCheckout(selection);
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
    final selection = _purchaseSelection();
    if (selection != null) unawaited(_addSelectionToCart(selection));
  }

  double _parsePriceLabel(String label) {
    final firstSegment = label.split(RegExp(r'[â€“\-]')).first;
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
    final value = _unitPrice;
    return '\u20b1${value.toStringAsFixed(value.truncateToDouble() == value ? 0 : 2)}';
  }

  String? get _listingBadge {
    if (widget.ownerView || !widget.isPurchasable) return null;
    if (widget.soldCount > 0) return 'Hot';
    final submitted = widget.submittedAt?.toUtc();
    if (submitted == null) return null;
    final age = DateTime.now().toUtc().difference(submitted);
    return !age.isNegative && age < const Duration(days: 7) ? 'New' : null;
  }

  Future<void> _openSellerChat() async {
    try {
      final ready = await ChatService.instance.initialize();
      if (!ready) {
        throw const ChatException('Please log in again to use chat.');
      }
      if (!mounted) return;

      if (widget.sellerId == null && widget.sellerRef == null) {
        await Navigator.of(
          context,
        ).push(MaterialPageRoute(builder: (_) => const MessagesPage()));
        return;
      }

      final conversation = await ChatService.instance.createConversation(
        participantActorKey: widget.sellerRef ?? 'admin:${widget.sellerId}',
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
    final canPurchase = widget.isPurchasable;
    final galleryImages = _galleryImages;
    final suppliedRating = widget.rating;
    final reviewRating =
        suppliedRating != null &&
            suppliedRating.isFinite &&
            suppliedRating > 0 &&
            suppliedRating <= 5 &&
            widget.reviewsCount > 0
        ? suppliedRating
        : null;
    final displayImages = galleryImages.isEmpty
        ? <String>[widget.imageUrl]
        : galleryImages;
    final selectedImageIndex = _selectedImageIndex >= displayImages.length
        ? 0
        : _selectedImageIndex;

    return Theme(
      data: Theme.of(context).copyWith(
        textTheme: AppTypography.textTheme(Theme.of(context).textTheme),
        primaryTextTheme: AppTypography.textTheme(
          Theme.of(context).primaryTextTheme,
        ),
      ),
      child: Scaffold(
        backgroundColor: Colors.white,
        body: CustomScrollView(
          slivers: [
            SliverAppBar(
              backgroundColor: Colors.white,
              surfaceTintColor: Colors.transparent,
              elevation: 0,
              scrolledUnderElevation: 0,
              expandedHeight: MediaQuery.sizeOf(
                context,
              ).width.clamp(240.0, 340.0),
              pinned: true,
              leadingWidth: 64,
              leading: Padding(
                padding: const EdgeInsets.only(left: 12),
                child: Center(
                  child: _ProductHeaderButton(
                    tooltip: 'Back',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(LucideIcons.arrowLeft, size: 20),
                  ),
                ),
              ),
              actions: widget.ownerView
                  ? []
                  : [
                      const _ProductDetailsCartButton(),
                      const SizedBox(width: 8),
                      ListenableBuilder(
                        listenable: FavoriteService.instance,
                        builder: (context, _) => _ProductHeaderButton(
                          tooltip: _isFavorite
                              ? 'Remove from favorites'
                              : 'Add to favorites',
                          onPressed: _toggleFavorite,
                          icon: Icon(
                            _isFavorite
                                ? Icons.favorite_rounded
                                : LucideIcons.heart,
                            size: 20,
                            color: const Color(0xFF1A1851),
                          ),
                          selected: _isFavorite,
                        ),
                      ),
                      const SizedBox(width: 12),
                    ],
              flexibleSpace: FlexibleSpaceBar(
                background: _ProductHeroImage(
                  images: displayImages,
                  currentIndex: selectedImageIndex,
                  controller: _imagePageController,
                  onPageChanged: _onImagePageChanged,
                  onImageSelected: _selectImage,
                ),
              ),
            ),
            if (widget.ownerView)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Review status: ${widget.approvalStatus}',
                        style: AppTypography.text(
                          color: const Color(0xFF1A1851),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (widget.rejectionReason.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(widget.rejectionReason),
                      ],
                    ],
                  ),
                ),
              ),
            SliverToBoxAdapter(
              child: _ProductInfoContainer(
                ownerView: widget.ownerView,
                priceText: _formatPriceDisplay(),
                name: widget.name,
                canPurchase: canPurchase,
                inventoryStatus: widget.inventoryStatus,
                badge: _listingBadge,
                description: widget.description,
                customization: widget.customization,
                selectedOptions: _selectedOptions,
                onOptionSelected: _toggleOption,
                sellerName: widget.seller,
                sellerPhotoUrl: widget.sellerPhotoUrl,
                sellerOnline: _sellerOnline,
                onSellerTap: _openSellerChat,
                expiryDate: widget.expiryDate,
                formatExpiry: _formatExpiry,
                relatedProducts: _relatedProducts,
                onRelatedTap: _openRelatedProduct,
                soldCount: widget.soldCount,
                rating: reviewRating,
                reviewsCount: reviewRating == null ? 0 : widget.reviewsCount,
                reviewsKey: _reviewsKey,
                onShowReviews: () {
                  final target = _reviewsKey.currentContext;
                  if (target == null) return;
                  unawaited(
                    Scrollable.ensureVisible(
                      target,
                      alignment: 0.15,
                      duration: MediaQuery.disableAnimationsOf(context)
                          ? Duration.zero
                          : const Duration(milliseconds: 250),
                      curve: Curves.easeOutCubic,
                    ),
                  );
                },
              ),
            ),
          ],
        ),
        bottomNavigationBar: widget.ownerView
            ? null
            : _ProductBottomBar(
                canPurchase: canPurchase,
                isAddingToCart: _isAddingToCart,
                addedToCart: _addedToCart,
                onChat: _openSellerChat,
                onAddToCart: _handleAddToCart,
                onBuyNow: _openBuyOptions,
              ),
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
    required this.onImageSelected,
  });

  final List<String> images;
  final int currentIndex;
  final PageController controller;
  final ValueChanged<int> onPageChanged;
  final ValueChanged<int> onImageSelected;

  @override
  Widget build(BuildContext context) {
    final indicatorCount = images.isEmpty ? 1 : images.length;
    return ColoredBox(
      color: Colors.white,
      child: SizedBox(
        height: MediaQuery.sizeOf(context).width.clamp(240.0, 340.0),
        width: double.infinity,
        child: Column(
          children: [
            Expanded(
              child: DecoratedBox(
                decoration: const BoxDecoration(
                  color: Color(0xFFF9FDE7),
                  border: Border(bottom: BorderSide(color: Color(0xFFE8EAF0))),
                ),
                child: PageView.builder(
                  controller: controller,
                  itemCount: images.length,
                  onPageChanged: onPageChanged,
                  itemBuilder: (context, index) => ProductImage(
                    imageUrl: images[index],
                    backgroundColor: const Color(0xFFF9FDE7),
                    fit: BoxFit.cover,
                  ),
                ),
              ),
            ),
            SizedBox(
              key: const ValueKey('product-image-indicators'),
              height: 26,
              child: Center(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: List.generate(indicatorCount, (index) {
                      final isActive = index == currentIndex;
                      return Semantics(
                        label: 'Product image ${index + 1} of $indicatorCount',
                        selected: isActive,
                        child: InkWell(
                          onTap: images.length > 1
                              ? () => onImageSelected(index)
                              : null,
                          borderRadius: BorderRadius.circular(12),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 4,
                              vertical: 8,
                            ),
                            child: AnimatedContainer(
                              duration: MediaQuery.disableAnimationsOf(context)
                                  ? Duration.zero
                                  : const Duration(milliseconds: 180),
                              width: isActive ? 18 : 6,
                              height: 6,
                              decoration: BoxDecoration(
                                color: isActive
                                    ? const Color(0xFF1A1851)
                                    : const Color(0xFFD0D5DD),
                                borderRadius: BorderRadius.circular(99),
                              ),
                            ),
                          ),
                        ),
                      );
                    }),
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

/// Shared 48dp circular controls for header and image favorite action.
class _ProductHeaderButton extends StatelessWidget {
  const _ProductHeaderButton({
    required this.tooltip,
    required this.onPressed,
    required this.icon,
    this.selected = false,
  });

  final String tooltip;
  final VoidCallback onPressed;
  final Widget icon;
  final bool selected;

  @override
  Widget build(BuildContext context) => Semantics(
    selected: selected,
    child: IconButton(
      tooltip: tooltip,
      onPressed: onPressed,
      icon: icon,
      style: IconButton.styleFrom(
        foregroundColor: const Color(0xFF1A1851),
        backgroundColor: Colors.white,
        fixedSize: const Size(48, 48),
        minimumSize: const Size(48, 48),
        padding: const EdgeInsets.all(12),
        shape: const CircleBorder(),
        side: const BorderSide(color: Color(0xFFE8EAF0)),
      ),
    ),
  );
}

class _ProductDetailsCartButton extends StatelessWidget {
  const _ProductDetailsCartButton();

  @override
  Widget build(BuildContext context) {
    return _ProductHeaderButton(
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
                LucideIcons.shoppingCart,
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
                      color: Color(0xFFFCB315),
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      count > 99 ? '99+' : '$count',
                      style: AppTypography.text(
                        fontSize: 8,
                        fontWeight: FontWeight.w800,
                        color: const Color(0xFF1A1851),
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

/// One continuous product surface; all choices come from Django.
class _ProductInfoContainer extends StatelessWidget {
  const _ProductInfoContainer({
    required this.ownerView,
    required this.priceText,
    required this.name,
    required this.badge,
    required this.canPurchase,
    required this.inventoryStatus,
    required this.description,
    required this.customization,
    required this.selectedOptions,
    required this.onOptionSelected,
    required this.sellerName,
    required this.sellerPhotoUrl,
    required this.sellerOnline,
    required this.onSellerTap,
    required this.expiryDate,
    required this.formatExpiry,
    required this.relatedProducts,
    required this.onRelatedTap,
    required this.soldCount,
    required this.rating,
    required this.reviewsCount,
    required this.reviewsKey,
    required this.onShowReviews,
  });

  final bool ownerView, canPurchase, sellerOnline;
  final String? badge;
  final String priceText, name, inventoryStatus, description, sellerName;
  final String sellerPhotoUrl;
  final ProductCustomizationConfig customization;
  final Map<String, Set<String>> selectedOptions;
  final void Function(ProductCustomizationGroup, String) onOptionSelected;
  final VoidCallback onSellerTap;
  final DateTime? expiryDate;
  final String Function(DateTime) formatExpiry;
  final List<ProductItem> relatedProducts;
  final ValueChanged<ProductItem> onRelatedTap;
  final int soldCount;
  final double? rating;
  final int reviewsCount;
  final GlobalKey reviewsKey;
  final VoidCallback onShowReviews;

  @override
  Widget build(BuildContext context) {
    const navy = Color(0xFF1A1851);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 6, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!ownerView) ...[
            _ProductReviewSummary(
              rating: rating,
              reviewsCount: reviewsCount,
              onTap: onShowReviews,
            ),
            const SizedBox(height: 4),
          ],
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              if (badge != null) ...[
                Container(
                  key: const ValueKey('product-listing-badge'),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: badge == 'Hot' ? const Color(0xFFFCB315) : navy,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    badge!,
                    style: AppTypography.text(
                      color: badge == 'Hot' ? navy : Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.2,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
              ],
              Expanded(
                child: Text(
                  name,
                  key: const ValueKey('product-heading-name'),
                  style: AppTypography.text(
                    color: navy,
                    fontSize: 22,
                    fontWeight: FontWeight.w600,
                    height: 1.25,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: priceText.startsWith('\u20b1') ? '\u20b1' : '',
                  style: const TextStyle(
                    fontFamily: 'Roboto',
                    fontSize: 26,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                TextSpan(
                  text: priceText.startsWith('\u20b1')
                      ? priceText.substring(1)
                      : priceText,
                ),
              ],
            ),
            key: const ValueKey('product-selected-price'),
            semanticsLabel: priceText,
            style: AppTypography.text(
              color: navy,
              fontSize: 26,
              fontWeight: FontWeight.w700,
              height: 1.15,
            ),
          ),
          if (soldCount > 0) ...[
            const SizedBox(height: 2),
            Text(
              '$soldCount sold',
              style: AppTypography.text(
                color: const Color(0xFF667085),
                fontSize: 12,
                fontWeight: FontWeight.w400,
              ),
            ),
          ],
          if (customization.hasOptions) ...[
            const SizedBox(height: 12),
            _ProductVariantChoices(
              key: const ValueKey('product-variant-choices'),
              groups: customization.groups,
              selectedOptions: selectedOptions,
              onSelected: onOptionSelected,
            ),
          ],
          const SizedBox(height: 12),
          _ProductDescription(description: description),
          const SizedBox(height: 12),
          _SellerIdentity(
            key: const ValueKey('product-seller-section'),
            name: sellerName,
            photoUrl: sellerPhotoUrl,
            online: sellerOnline,
            onTap: ownerView ? null : onSellerTap,
          ),
          if (!ownerView && !canPurchase) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFFCB315).withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: const Color(0xFFFCB315).withValues(alpha: 0.4),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(LucideIcons.info, color: navy, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      inventoryStatus == 'expired'
                          ? 'This product has expired and is unavailable.'
                          : 'This product is out of stock.',
                      style: AppTypography.text(color: navy, fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
          ],
          if (expiryDate != null) ...[
            const SizedBox(height: 10),
            _DetailLine(
              label: 'Expiry Date',
              value: formatExpiry(expiryDate!),
              valueColor: navy,
            ),
          ],
          if (!ownerView) ...[
            const SizedBox(height: 12),
            _ProductReviewsSection(
              key: reviewsKey,
              rating: rating,
              reviewsCount: reviewsCount,
            ),
            const SizedBox(height: 12),
            _YouMayAlsoLikeSection(
              products: relatedProducts,
              onTap: onRelatedTap,
            ),
          ],
        ],
      ),
    );
  }
}

class _ProductDescription extends StatelessWidget {
  const _ProductDescription({required this.description});
  final String description;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        'Description',
        style: AppTypography.text(
          color: const Color(0xFF1A1851),
          fontSize: 16,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.1,
        ),
      ),
      const SizedBox(height: 6),
      Text(
        description.isEmpty ? 'No description provided.' : description,
        key: const ValueKey('product-description-text'),
        style: AppTypography.text(
          color: const Color(0xFF667085),
          fontSize: 13.5,
          fontWeight: FontWeight.w400,
          height: 1.5,
        ),
      ),
    ],
  );
}

/// Uses the saved names/options only. Color groups render circular color
/// swatches; non-color groups render compact text chips.
class _ProductVariantChoices extends StatelessWidget {
  const _ProductVariantChoices({
    super.key,
    required this.groups,
    required this.selectedOptions,
    required this.onSelected,
  });

  final List<ProductCustomizationGroup> groups;
  final Map<String, Set<String>> selectedOptions;
  final void Function(ProductCustomizationGroup, String) onSelected;

  @override
  Widget build(BuildContext context) {
    const navy = Color(0xFF1A1851);
    return LayoutBuilder(
      builder: (context, constraints) {
        // Keep both groups readable at large accessibility text sizes.
        final sideBySide =
            groups.length == 2 &&
            constraints.maxWidth >= 320 &&
            MediaQuery.textScalerOf(context).scale(13) <= 18;
        final groupWidth = sideBySide
            ? (constraints.maxWidth - 16) / 2
            : constraints.maxWidth;
        return Wrap(
          spacing: 16,
          runSpacing: 12,
          children: [
            for (var i = 0; i < groups.length; i++)
              SizedBox(
                key: ValueKey('variant-group-${groups[i].name}'),
                width: groupWidth,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _isColor(groups[i]) ? 'Colors' : groups[i].name,
                      style: AppTypography.text(
                        color: navy,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final option in groups[i].options)
                          if (_isColor(groups[i]))
                            _ColorVariantChoice(
                              group: groups[i],
                              option: option,
                              selected:
                                  selectedOptions[groups[i].name]?.contains(
                                    option.name,
                                  ) ??
                                  false,
                              onTap: () => onSelected(groups[i], option.name),
                            )
                          else
                            ConstrainedBox(
                              constraints: BoxConstraints(maxWidth: groupWidth),
                              child: FilterChip(
                                key: ValueKey(
                                  'variant-${groups[i].name}-${option.name}',
                                ),
                                label: Text(option.name),
                                selected:
                                    selectedOptions[groups[i].name]?.contains(
                                      option.name,
                                    ) ??
                                    false,
                                showCheckmark: false,
                                onSelected: (_) =>
                                    onSelected(groups[i], option.name),
                                selectedColor: navy,
                                backgroundColor: Colors.white,
                                materialTapTargetSize:
                                    MaterialTapTargetSize.shrinkWrap,
                                visualDensity: VisualDensity.compact,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 4,
                                ),
                                labelStyle: AppTypography.text(
                                  color:
                                      (selectedOptions[groups[i].name]
                                              ?.contains(option.name) ??
                                          false)
                                      ? Colors.white
                                      : navy,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                side: BorderSide(
                                  color:
                                      (selectedOptions[groups[i].name]
                                              ?.contains(option.name) ??
                                          false)
                                      ? navy
                                      : const Color(0xFFE8EAF0),
                                  width: 1.2,
                                ),
                              ),
                            ),
                      ],
                    ),
                  ],
                ),
              ),
          ],
        );
      },
    );
  }

  bool _isColor(ProductCustomizationGroup group) {
    final name = group.name.trim().toLowerCase().replaceAll(
      RegExp(r'[_/\-]+'),
      ' ',
    );
    // Respect clearly non-color group labels even if an option is a color word.
    if (RegExp(
      r'\b(sizes?|sukat|flavou?rs?|prints?|portions?|servings?)\b',
    ).hasMatch(name)) {
      return false;
    }
    if (RegExp(r'\b(colou?rs?|kulay|shades?)\b').hasMatch(name)) return true;
    // A generic web group can still contain a set of saved colors.
    return group.options.isNotEmpty &&
        group.options.every(
          (option) => _ColorVariantChoice.hasKnownColor(option.name),
        );
  }
}

class _ColorVariantChoice extends StatelessWidget {
  const _ColorVariantChoice({
    required this.group,
    required this.option,
    required this.selected,
    required this.onTap,
  });

  final ProductCustomizationGroup group;
  final ProductCustomizationOption option;
  final bool selected;
  final VoidCallback onTap;

  static const _namedColors = <String, Color>{
    'navy': Color(0xFF1A1851),
    'navy blue': Color(0xFF1A1851),
    'white': Color(0xFFFFFFFF),
    'off white': Color(0xFFFAF9F6),
    'cream': Color(0xFFF5E6C8),
    'ivory': Color(0xFFFFFBEB),
    'beige': Color(0xFFE8DCC4),
    'tan': Color(0xFFD2B48C),
    'khaki': Color(0xFFC3B091),
    'black': Color(0xFF171717),
    'charcoal': Color(0xFF374151),
    'gold': Color(0xFFFCB315),
    'mustard': Color(0xFFEAB308),
    'yellow': Color(0xFFFFD600),
    'blue': Color(0xFF2563EB),
    'light blue': Color(0xFF60A5FA),
    'sky blue': Color(0xFF38BDF8),
    'royal blue': Color(0xFF1D4ED8),
    'red': Color(0xFFDC2626),
    'maroon': Color(0xFF7F1D1D),
    'burgundy': Color(0xFF881337),
    'wine': Color(0xFF722F37),
    'crimson': Color(0xFFB91C1C),
    'green': Color(0xFF16803C),
    'dark green': Color(0xFF14532D),
    'forest green': Color(0xFF166534),
    'light green': Color(0xFF4ADE80),
    'mint': Color(0xFF6EE7B7),
    'olive': Color(0xFF65A30D),
    'matcha': Color(0xFF74A12E),
    'teal': Color(0xFF0D9488),
    'turquoise': Color(0xFF06B6D4),
    'cyan': Color(0xFF06B6D4),
    'gray': Color(0xFF737373),
    'grey': Color(0xFF737373),
    'silver': Color(0xFFC0C0C0),
    'brown': Color(0xFF795548),
    'coffee': Color(0xFF6F4E37),
    'chocolate': Color(0xFF5D4037),
    'mocha': Color(0xFF6D4C41),
    'caramel': Color(0xFFC68E17),
    'orange': Color(0xFFEA580C),
    'coral': Color(0xFFF97316),
    'peach': Color(0xFFFDBA74),
    'pink': Color(0xFFEC4899),
    'rose': Color(0xFFF43F5E),
    'purple': Color(0xFF7E22CE),
    'violet': Color(0xFF8B5CF6),
    'lavender': Color(0xFFC4B5FD),
    'magenta': Color(0xFFD946EF),
  };

  static String _normalize(String raw) => raw
      .trim()
      .toLowerCase()
      .replaceAll(RegExp(r'[_/\-]+'), ' ')
      .replaceAll(RegExp(r'\s+'), ' ');

  static Color? _lookupColor(String raw) {
    final normalized = _normalize(raw);
    if (_namedColors.containsKey(normalized)) {
      return _namedColors[normalized];
    }
    final hexMatch = RegExp(r'#([0-9a-fA-F]{6})\b').firstMatch(raw);
    if (hexMatch != null) {
      return Color(0xFF000000 | int.parse(hexMatch.group(1)!, radix: 16));
    }
    for (final word in normalized.split(' ')) {
      if (_namedColors.containsKey(word)) {
        return _namedColors[word];
      }
    }
    return null;
  }

  static bool hasKnownColor(String raw) => _lookupColor(raw) != null;

  @override
  Widget build(BuildContext context) {
    const navy = Color(0xFF1A1851);
    final knownColor = _lookupColor(option.name);
    final color = knownColor ?? const Color(0xFF94A3B8);
    final hasPhoto = knownColor == null && option.imageUrl.isNotEmpty;
    final light = color.computeLuminance() > 0.4;
    return Semantics(
      key: ValueKey('variant-${group.name}-${option.name}'),
      button: true,
      selected: selected,
      label: '${group.name}: ${option.name}',
      onTap: onTap,
      excludeSemantics: true,
      child: Tooltip(
        message: option.name,
        child: InkResponse(
          onTap: onTap,
          radius: 20,
          child: SizedBox(
            width: 38,
            height: 38,
            child: Center(
              child: Container(
                width: 34,
                height: 34,
                padding: const EdgeInsets.all(2.5),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: selected ? navy : Colors.transparent,
                    width: 2,
                  ),
                ),
                child: Container(
                  key: ValueKey('color-swatch-${group.name}-${option.name}'),
                  clipBehavior: Clip.antiAlias,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: color,
                    border: Border.all(color: const Color(0xFFE8EAF0)),
                  ),
                  child: hasPhoto
                      ? Stack(
                          fit: StackFit.expand,
                          children: [
                            ProductImage(
                              imageUrl: option.imageUrl,
                              fallbackSize: 14,
                            ),
                            if (selected)
                              const Center(
                                child: Icon(
                                  LucideIcons.check,
                                  color: Colors.white,
                                  size: 14,
                                  shadows: [Shadow(blurRadius: 4)],
                                ),
                              ),
                          ],
                        )
                      : Center(
                          child: selected
                              ? Icon(
                                  LucideIcons.check,
                                  color: light ? navy : Colors.white,
                                  size: 14,
                                )
                              : null,
                        ),
                ),
              ),
            ),
          ),
        ),
      ),
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
    return Container(
      padding: const EdgeInsets.only(top: 12),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: Color(0xFFE8EAF0))),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 96,
            child: Text(
              label,
              style: AppTypography.text(
                color: const Color(0xFF667085),
                fontSize: 12,
                fontWeight: FontWeight.w400,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTypography.text(
                color: valueColor,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Minimal horizontal seller information row positioned above Description.
class _SellerIdentity extends StatelessWidget {
  const _SellerIdentity({
    super.key,
    required this.name,
    required this.photoUrl,
    required this.online,
    this.onTap,
  });
  final String name;
  final String photoUrl;
  final bool online;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(8),
    child: Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: Color(0xFFE8EAF0)),
          bottom: BorderSide(color: Color(0xFFE8EAF0)),
        ),
      ),
      child: Row(
        children: [
          Semantics(
            image: true,
            label: photoUrl.trim().isEmpty
                ? 'Seller profile placeholder'
                : 'Seller profile photo',
            child: ExcludeSemantics(
              child: Container(
                padding: const EdgeInsets.all(1),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFFE8EAF0)),
                ),
                child: ClipOval(
                  child: SizedBox(
                    width: 36,
                    height: 36,
                    child: ProductImage(
                      key: const ValueKey('product-seller-photo'),
                      imageUrl: photoUrl,
                      fallbackIcon: LucideIcons.user,
                      fallbackSize: 18,
                      fallbackColor: const Color(0xFF1A1851),
                      backgroundColor: Colors.white,
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name.trim().isEmpty ? 'Seller unavailable' : name.trim(),
                  key: const ValueKey('product-heading-seller'),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.text(
                    color: const Color(0xFF1A1851),
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Tooltip(
                  message: online ? 'Seller online' : 'Seller offline',
                  child: Row(
                    children: [
                      Container(
                        key: const ValueKey('product-seller-status-dot'),
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: online
                              ? const Color(0xFFFCB315)
                              : const Color(0xFF667085),
                        ),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        online ? 'Online' : 'Offline',
                        key: const ValueKey('product-seller-status'),
                        style: AppTypography.text(
                          color: const Color(0xFF667085),
                          fontSize: 12,
                          fontWeight: FontWeight.w400,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Icon(
            LucideIcons.chevronRight,
            size: 18,
            color: Color(0xFF667085),
          ),
        ],
      ),
    ),
  );
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

  final bool canPurchase, isAddingToCart, addedToCart;
  final VoidCallback onChat, onAddToCart, onBuyNow;

  @override
  Widget build(BuildContext context) {
    const navy = Color(0xFF1A1851);
    final shape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
    );
    final textStyle = AppTypography.text(
      fontSize: 14,
      fontWeight: FontWeight.w600,
    );
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFE8EAF0))),
      ),
      child: SafeArea(
        top: false,
        minimum: const EdgeInsets.fromLTRB(16, 10, 16, 10),
        child: Row(
          children: [
            _BottomIconTextAction(
              key: const ValueKey('product-bottom-chat-button'),
              icon: LucideIcons.messageSquare,
              label: 'Chat',
              tooltip: 'Chat',
              maxWidth: 64,
              onPressed: onChat,
            ),
            const SizedBox(width: 6),
            Container(
              key: const ValueKey('product-bottom-chat-divider'),
              width: 1,
              height: 32,
              color: const Color(0xFFE8EAF0),
            ),
            const SizedBox(width: 6),
            _BottomIconTextAction(
              key: const ValueKey('product-bottom-add-to-cart-button'),
              icon: addedToCart
                  ? Icons.check_circle_rounded
                  : LucideIcons.shoppingCart,
              label: addedToCart ? 'Added' : 'Add to Cart',
              tooltip: 'Add to Cart',
              loading: isAddingToCart,
              maxWidth: 88,
              onPressed: canPurchase && !isAddingToCart ? onAddToCart : null,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                onPressed: canPurchase && !isAddingToCart ? onBuyNow : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: navy,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  minimumSize: const Size(0, 48),
                  shape: shape,
                  textStyle: textStyle,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 12,
                  ),
                ),
                child: const Text('Buy Now', textAlign: TextAlign.center),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BottomIconTextAction extends StatelessWidget {
  const _BottomIconTextAction({
    super.key,
    required this.icon,
    required this.label,
    required this.tooltip,
    required this.maxWidth,
    required this.onPressed,
    this.loading = false,
  });

  final IconData icon;
  final String label;
  final String tooltip;
  final double maxWidth;
  final VoidCallback? onPressed;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    const navy = Color(0xFF1A1851);
    const disabledColor = Color(0xFF98A2B3);
    final fgColor = onPressed != null || loading ? navy : disabledColor;
    return Tooltip(
      message: tooltip,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          minWidth: 48,
          maxWidth: maxWidth,
          minHeight: 48,
        ),
        child: TextButton(
          onPressed: onPressed,
          style: TextButton.styleFrom(
            foregroundColor: navy,
            disabledForegroundColor: disabledColor,
            minimumSize: const Size(48, 48),
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (loading)
                const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: navy),
                )
              else
                Icon(icon, size: 18, color: fgColor),
              const SizedBox(height: 3),
              Text(
                label,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: AppTypography.text(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: fgColor,
                  height: 1.1,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// The whole row is one accessible target, not five separate rating inputs.
class _ProductReviewSummary extends StatelessWidget {
  const _ProductReviewSummary({
    required this.rating,
    required this.reviewsCount,
    required this.onTap,
  });

  final double? rating;
  final int reviewsCount;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final label = rating == null
        ? 'No reviews yet'
        : '${rating!.toStringAsFixed(1)} ($reviewsCount)';
    return Semantics(
      key: const ValueKey('product-review-summary'),
      button: true,
      onTap: onTap,
      label: rating == null
          ? 'View product reviews. No reviews yet.'
          : 'View product reviews. ${rating!.toStringAsFixed(1)} out of 5 stars from $reviewsCount ${reviewsCount == 1 ? 'review' : 'reviews'}.',
      child: ExcludeSemantics(
        child: TextButton(
          onPressed: onTap,
          style: TextButton.styleFrom(
            foregroundColor: const Color(0xFF1A1851),
            minimumSize: const Size(48, 22),
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            padding: const EdgeInsets.symmetric(vertical: 2),
            alignment: Alignment.centerLeft,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: ExcludeSemantics(
            child: SizedBox(
              width: double.infinity,
              child: Wrap(
                alignment: WrapAlignment.start,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 8,
                runSpacing: 4,
                children: [
                  _ProductRatingStars(
                    key: const ValueKey('product-summary-stars'),
                    rating: rating,
                  ),
                  Text(
                    label,
                    key: const ValueKey('product-rating-value'),
                    style: AppTypography.text(
                      color: const Color(0xFF667085),
                      fontSize: 12,
                      fontWeight: rating == null
                          ? FontWeight.w400
                          : FontWeight.w600,
                      height: 1.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Fractional fills keep an actual 4.8 distinguishable from a perfect five.
class _ProductRatingStars extends StatelessWidget {
  const _ProductRatingStars({super.key, required this.rating});
  final double? rating;

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: List.generate(5, (index) {
      final fill = ((rating ?? 0) - index).clamp(0.0, 1.0);
      return Padding(
        padding: EdgeInsets.only(right: index == 4 ? 0 : 4),
        child: SizedBox(
          width: 16,
          height: 16,
          child: Stack(
            children: [
              Icon(
                Icons.star_border_rounded,
                size: 16,
                color: rating == null
                    ? const Color(0xFFD0D5DD)
                    : const Color(0xFFFCB315),
              ),
              if (fill > 0)
                ClipRect(
                  child: Align(
                    key: ValueKey('rating-star-fill-$index'),
                    alignment: Alignment.centerLeft,
                    widthFactor: fill,
                    child: const Icon(
                      Icons.star_rounded,
                      size: 16,
                      color: Color(0xFFFCB315),
                    ),
                  ),
                ),
            ],
          ),
        ),
      );
    }),
  );
}

class _ProductReviewsSection extends StatelessWidget {
  const _ProductReviewsSection({
    super.key,
    required this.rating,
    required this.reviewsCount,
  });

  final double? rating;
  final int reviewsCount;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Text(
              'Ratings & Reviews',
              key: const ValueKey('product-reviews-heading'),
              style: AppTypography.text(
                fontWeight: FontWeight.w600,
                fontSize: 16,
                color: const Color(0xFF1A1851),
                letterSpacing: -0.1,
              ),
            ),
          ),
          Text(
            'See All',
            style: AppTypography.text(
              fontSize: 12,
              fontWeight: FontWeight.w400,
              color: const Color(0xFF667085),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      if (rating != null) ...[
        Semantics(
          label:
              '${rating!.toStringAsFixed(1)} out of 5 stars from $reviewsCount ${reviewsCount == 1 ? 'review' : 'reviews'}',
          child: ExcludeSemantics(
            child: Wrap(
              spacing: 12,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                _ProductRatingStars(rating: rating),
                Text(
                  '${rating!.toStringAsFixed(1)} / 5 ($reviewsCount ${reviewsCount == 1 ? 'review' : 'reviews'})',
                  style: AppTypography.text(
                    fontSize: 13,
                    color: const Color(0xFF1A1851),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 4),
      ],
      Text(
        rating == null
            ? 'No reviews yet'
            : 'Individual reviews are not available yet.',
        key: const ValueKey('product-review-details-state'),
        style: AppTypography.text(
          fontSize: 13,
          height: 1.5,
          color: const Color(0xFF667085),
        ),
      ),
    ],
  );
}

class _YouMayAlsoLikeSection extends StatelessWidget {
  const _YouMayAlsoLikeSection({required this.products, required this.onTap});

  final List<ProductItem> products;
  final ValueChanged<ProductItem> onTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'You May Also Like',
          style: AppTypography.text(
            fontWeight: FontWeight.w600,
            fontSize: 16,
            color: const Color(0xFF1A1851),
            letterSpacing: -0.1,
          ),
        ),
        const SizedBox(height: 10),
        if (products.isEmpty)
          Text(
            'No suggestions yet',
            style: AppTypography.text(
              fontSize: 13,
              height: 1.5,
              color: const Color(0xFF667085),
            ),
          )
        else
          SizedBox(
            height: 214,
            width: double.infinity,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: products.length,
              separatorBuilder: (_, _) => const SizedBox(width: 12),
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
    const navy = Color(0xFF1A1851);
    final favKey = favoriteKeyForProduct(id: product.id, name: product.name);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 140,
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: MarketplaceColors.cardSurface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE8EAF0)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: AspectRatio(
                aspectRatio: 1,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    ProductImage(
                      imageUrl: product.imageUrl,
                      backgroundColor: MarketplaceColors.imageSurface,
                      fit: BoxFit.cover,
                    ),
                    Positioned(
                      right: 6,
                      top: 6,
                      child: ListenableBuilder(
                        listenable: FavoriteService.instance,
                        builder: (context, _) {
                          final isFav = FavoriteService.instance.isFavorite(
                            favKey,
                          );
                          return GestureDetector(
                            onTap: () =>
                                FavoriteService.instance.toggle(favKey),
                            child: Container(
                              width: 28,
                              height: 28,
                              decoration: BoxDecoration(
                                color: Colors.white,
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: const Color(0xFFE8EAF0),
                                ),
                              ),
                              alignment: Alignment.center,
                              child: Icon(
                                isFav
                                    ? Icons.favorite_rounded
                                    : LucideIcons.heart,
                                size: 14,
                                color: navy,
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
            const SizedBox(height: 8),
            Text(
              product.name,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: AppTypography.text(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: navy,
                height: 1.25,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              product.price,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: AppTypography.text(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: navy,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
