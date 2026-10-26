import 'package:flutter/material.dart';
import '../../theme/app_typography.dart';
import '../../theme/marketplace_colors.dart';

import '../../models/facility_item.dart';
import '../../models/product_item.dart';
import '../../models/service_item.dart';
import '../../services/cart_service.dart';
import '../../services/favorite_service.dart';
import '../../services/product_service.dart';
import '../../services/service_catalog.dart';
import '../../session/session_service.dart';
import '../product_image.dart';
import '../../screens/facility_details_screen.dart';
import '../../screens/product_details_screen.dart';
import '../../screens/service_details_screen.dart';

/// Centralized institutional color palette for CampusHub mobile dashboard.
abstract class HomeAppColors {
  // Primary Brand Colors
  static const Color navy = Color(0xFF1A1851);
  static const Color gold = Color(0xFFFCB315);
  static const Color white = Color(0xFFFFFFFF);

  // Supporting Colors
  static const Color appBackground = white;
  static const Color surfaceTint = white;
  static const Color primaryText = navy;
  static const Color secondaryText = Color(0xFF475569);
  static const Color mutedText = Color(0xFF64748B);
  static const Color border = Color(0xFFE2E8F0);
  static const Color cardBorder = border;

  // Status Colors
  static const Color success = Color(0xFF16A34A);
  static const Color successBg = Color(0xFFECFDF3);
  static const Color warning = Color(0xFFD97706);
  static const Color warningBg = Color(0xFFFFF7E6);
  static const Color error = Color(0xFFDC2626);
}

/// Institutional Section Header for Home Dashboard
class HomeSectionHeader extends StatelessWidget {
  const HomeSectionHeader({
    super.key,
    required this.title,
    required this.onSeeAll,
  });

  final String title;
  final VoidCallback onSeeAll;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Text(
            title,
            style: AppTypography.text(
              fontSize: 19,
              fontWeight: FontWeight.w700,
              color: HomeAppColors.navy,
              letterSpacing: -0.3,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Flexible(
          child: TextButton(
            onPressed: onSeeAll,
            style: TextButton.styleFrom(
              foregroundColor: HomeAppColors.gold,
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
              minimumSize: const Size(48, 36),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Flexible(
                  child: Text(
                    'See All',
                    style: AppTypography.text(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: HomeAppColors.gold,
                    ),
                  ),
                ),
                const SizedBox(width: 3),
                const Icon(
                  Icons.arrow_forward_ios_rounded,
                  size: 11,
                  color: HomeAppColors.gold,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

/// Shared product destination and existing interaction tracking for Home/Search.
Future<void> openMarketplaceProduct(
  BuildContext context,
  ProductItem product,
) async {
  final user = await SessionService.loadUser();
  if (product.id != null && user != null) {
    await ProductService.trackInteraction(
      userId: user.id,
      productId: product.id!,
      interactionType: 'view',
    );
  }

  if (!context.mounted) return;
  await Navigator.of(context).push(
    MaterialPageRoute(
      builder: (_) => ProductDetailsScreen(
        id: product.id,
        userId: user?.id,
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

/// Clean, institutional Marketplace Preview Card for Home Dashboard
class MarketplacePreviewCard extends StatelessWidget {
  const MarketplacePreviewCard({
    super.key,
    required this.product,
    this.width = 158.0,
  });

  final ProductItem product;
  final double width;

  String get _favoriteKey =>
      favoriteKeyForProduct(id: product.id, name: product.name);

  Future<void> _handleQuickAdd(BuildContext context) async {
    if (!product.isPurchasable) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('This product is unavailable.'),
          duration: Duration(seconds: 1),
        ),
      );
      return;
    }
    await CartService.instance.quickAdd(context: context, product: product);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      decoration: BoxDecoration(
        color: MarketplaceColors.cardSurface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: HomeAppColors.cardBorder),
      ),
      clipBehavior: Clip.antiAlias,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => openMarketplaceProduct(context, product),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                height: 126,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    ProductImage(
                      imageUrl: product.imageUrl,
                      fallbackIcon: product.icon,
                      fallbackColor: HomeAppColors.navy,
                      backgroundColor: MarketplaceColors.imageSurface,
                    ),
                    Positioned(
                      top: 4,
                      right: 4,
                      child: AnimatedBuilder(
                        animation: FavoriteService.instance,
                        builder: (context, _) {
                          final favorite = FavoriteService.instance.isFavorite(
                            _favoriteKey,
                          );
                          return Material(
                            color: Colors.transparent,
                            child: IconButton(
                              tooltip: favorite
                                  ? 'Remove from favorites'
                                  : 'Add to favorites',
                              onPressed: () =>
                                  FavoriteService.instance.toggle(_favoriteKey),
                              style: IconButton.styleFrom(
                                backgroundColor: HomeAppColors.white.withValues(
                                  alpha: 0.9,
                                ),
                                foregroundColor: HomeAppColors.navy,
                                minimumSize: const Size(32, 32),
                                padding: EdgeInsets.zero,
                              ),
                              icon: Icon(
                                favorite
                                    ? Icons.favorite_rounded
                                    : Icons.favorite_border_rounded,
                                size: 18,
                                color: HomeAppColors.navy,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      product.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.text(
                        color: HomeAppColors.primaryText,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                        height: 1.25,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      product.price,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.text(
                        color: HomeAppColors.navy,
                        fontWeight: FontWeight.w700,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 3),
                    if (product.category.trim().isNotEmpty) ...[
                      Text(
                        product.category,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.text(
                          color: HomeAppColors.secondaryText,
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 3),
                    ],
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            product.seller,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: AppTypography.text(
                              color: HomeAppColors.secondaryText,
                              fontSize: 11,
                              fontWeight: FontWeight.w400,
                            ),
                          ),
                        ),
                        if (product.isPurchasable)
                          GestureDetector(
                            onTap: () => _handleQuickAdd(context),
                            child: Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                color: HomeAppColors.gold.withValues(
                                  alpha: 0.2,
                                ),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.add_shopping_cart_rounded,
                                size: 13,
                                color: HomeAppColors.navy,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Clean, institutional Facility Preview Card for Home Dashboard
class FacilityPreviewCard extends StatelessWidget {
  const FacilityPreviewCard({
    super.key,
    required this.facility,
    this.width = 204.0,
  });

  final FacilityItem facility;
  final double width;

  @override
  Widget build(BuildContext context) {
    final capacity = facility.capacityLabel.isNotEmpty
        ? facility.capacityLabel
        : (int.tryParse(facility.capacity) != null &&
                  int.parse(facility.capacity) > 0
              ? '${facility.capacity} pax'
              : '');

    final isOpen =
        facility.status.toLowerCase().contains('open') ||
        facility.status.toLowerCase().contains('available');

    final statusColor = isOpen ? HomeAppColors.success : HomeAppColors.warning;

    return Container(
      width: width,
      decoration: BoxDecoration(
        color: HomeAppColors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: HomeAppColors.cardBorder),
      ),
      clipBehavior: Clip.antiAlias,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => FacilityDetailsScreen(facility: facility),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                height: 118,
                child: ProductImage(
                  imageUrl: facility.resolvedImageUrl,
                  fallbackIcon: facility.icon,
                  fallbackColor: HomeAppColors.navy,
                  backgroundColor: HomeAppColors.surfaceTint,
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      facility.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.text(
                        color: HomeAppColors.navy,
                        fontWeight: FontWeight.w700,
                        fontSize: 15,
                        height: 1.25,
                      ),
                    ),
                    if (capacity.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Capacity: $capacity',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.text(
                          color: HomeAppColors.secondaryText,
                          fontSize: 12,
                          fontWeight: FontWeight.w400,
                        ),
                      ),
                    ],
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Container(
                          width: 7,
                          height: 7,
                          decoration: BoxDecoration(
                            color: statusColor,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            facility.status,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: AppTypography.text(
                              color: HomeAppColors.navy,
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                        const Icon(
                          Icons.arrow_forward_rounded,
                          color: HomeAppColors.navy,
                          size: 16,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Clean, institutional Service Preview Card for Home Dashboard
class ServicePreviewCard extends StatelessWidget {
  const ServicePreviewCard({
    super.key,
    required this.service,
    required this.catalog,
    this.width = 180.0,
  });

  final ServiceItem service;
  final ServiceCatalog catalog;
  final double width;

  @override
  Widget build(BuildContext context) {
    final hasImage = service.facility.resolvedImageUrl.isNotEmpty;

    return Container(
      width: width,
      decoration: BoxDecoration(
        color: HomeAppColors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: HomeAppColors.cardBorder),
      ),
      clipBehavior: Clip.antiAlias,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute<void>(
              settings: const RouteSettings(name: '/services/details'),
              builder: (_) =>
                  ServiceDetailsScreen(service: service, catalog: catalog),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                height: 94,
                child: hasImage
                    ? ProductImage(
                        imageUrl: service.facility.resolvedImageUrl,
                        fallbackIcon: service.facility.icon,
                        fallbackColor: HomeAppColors.navy,
                        backgroundColor: HomeAppColors.surfaceTint,
                      )
                    : Container(
                        color: HomeAppColors.surfaceTint,
                        alignment: Alignment.center,
                        child: Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: HomeAppColors.navy.withValues(alpha: 0.08),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            service.facility.icon,
                            color: HomeAppColors.navy,
                            size: 22,
                          ),
                        ),
                      ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      service.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.text(
                        color: HomeAppColors.navy,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        height: 1.25,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      service.facility.description.isNotEmpty
                          ? service.facility.description
                          : service.category,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.text(
                        color: HomeAppColors.secondaryText,
                        fontSize: 11,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            'View service',
                            style: AppTypography.text(
                              color: HomeAppColors.navy,
                              fontWeight: FontWeight.w600,
                              fontSize: 12,
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Icon(
                          Icons.arrow_forward_rounded,
                          size: 13,
                          color: HomeAppColors.navy,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
