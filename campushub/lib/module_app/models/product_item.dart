import 'package:flutter/material.dart';

import 'product_customization.dart';

/// Marketplace product parsed from `/api/products/approved/` and related endpoints.
class ProductItem {
  const ProductItem(
    this.name,
    this.price,
    this.icon,
    this.color, {
    this.id,
    this.sellerId,
    this.imageUrl = '',
    this.images = const [],
    this.seller = '',
    this.sellerContact = '',
    this.category = '',
    this.description = '',
    this.stock,
    this.expiryDate,
    this.inventoryStatus = 'in_stock',
    this.inventoryStatusLabel = 'In Stock',
    this.lowStockThreshold = 5,
    this.soldCount = 0,
    this.rating,
    this.reviewsCount = 0,
    this.customization = const ProductCustomizationConfig(),
  });

  factory ProductItem.fromJson(Map<String, dynamic> json) {
    final name = (json['name'] as String? ?? 'Untitled Product').trim();
    final category = (json['category'] as String? ?? '').trim();
    final priceDisplayRaw = (json['price_display'] as String? ?? '').trim();
    String price;
    if (priceDisplayRaw.isNotEmpty) {
      price = priceDisplayRaw;
    } else {
      final priceValue = (json['price']?.toString() ?? '0').trim();
      final numericOnly = priceValue.replaceAll(RegExp(r'[^0-9.]'), '');
      final parsedPrice = double.tryParse(numericOnly);
      if (parsedPrice != null) {
        price = '₱${parsedPrice.toStringAsFixed(2)}';
      } else if (priceValue.isNotEmpty) {
        price = priceValue.startsWith('₱') ? priceValue : '₱$priceValue';
      } else {
        price = '₱0.00';
      }
    }
    final rawId = json['id'];
    final id = rawId is int ? rawId : int.tryParse('$rawId');
    final stockRaw = json['stock'];
    final stock = stockRaw is int ? stockRaw : int.tryParse('$stockRaw');
    final thresholdRaw = json['low_stock_threshold'];
    final lowStockThreshold = thresholdRaw is int
        ? thresholdRaw
        : int.tryParse('$thresholdRaw') ?? 5;
    final soldRaw = json['sold'] ?? json['sold_count'] ?? json['units_sold'];
    final soldCount = soldRaw is int
        ? soldRaw
        : int.tryParse('$soldRaw') ?? 0;
    final ratingRaw = json['rating'] ?? json['average_rating'];
    final rating = ratingRaw is num
        ? ratingRaw.toDouble()
        : double.tryParse('$ratingRaw');
    final reviewsRaw =
        json['reviews_count'] ?? json['reviews'] ?? json['total_reviews'];
    final reviewsCount = reviewsRaw is int
        ? reviewsRaw
        : (int.tryParse('$reviewsRaw') ?? 0);
    final primaryImage = (json['image_url'] as String? ?? '').trim();
    final images = _parseProductImages(json['images'], primaryImage);

    return ProductItem(
      name.isEmpty ? 'Untitled Product' : name,
      price,
      iconForProduct(category.isEmpty ? name : category),
      colorForProduct(category.isEmpty ? name : category),
      id: id,
      sellerId: _parseInt(json['seller_id']),
      imageUrl: images.isNotEmpty ? images.first : primaryImage,
      images: images,
      seller: (json['seller'] as String? ?? '').trim(),
      sellerContact: (json['seller_contact'] as String? ?? '').trim(),
      category: category,
      description: (json['description'] as String? ?? '').trim(),
      stock: stock,
      expiryDate: _parseExpiry(json['expiry_date']),
      inventoryStatus: (json['inventory_status'] as String? ?? 'in_stock')
          .trim(),
      inventoryStatusLabel:
          (json['inventory_status_label'] as String? ?? 'In Stock').trim(),
      lowStockThreshold: lowStockThreshold,
      soldCount: soldCount,
      rating: rating,
      reviewsCount: reviewsCount,
      customization: ProductCustomizationConfig.fromJson(json),
    );
  }

  final int? id;
  final int? sellerId;
  final String name;
  final String price;
  final IconData icon;
  final Color color;
  final String imageUrl;
  final List<String> images;
  final String seller;
  final String sellerContact;
  final String category;
  final String description;
  final int? stock;
  final DateTime? expiryDate;
  final String inventoryStatus;
  final String inventoryStatusLabel;
  final int lowStockThreshold;
  final int soldCount;
  final double? rating;
  final int reviewsCount;
  final ProductCustomizationConfig customization;

  bool get hasReviews => rating != null && rating! > 0 && reviewsCount > 0;

  double get basePrice {
    final firstSegment = price.split(RegExp(r'[–\-]')).first;
    final cleaned = firstSegment.replaceAll(RegExp(r'[^0-9.]'), '');
    return double.tryParse(cleaned) ?? 0;
  }

  bool get isPurchasable =>
      inventoryStatus != 'out_of_stock' &&
      inventoryStatus != 'expired' &&
      (stock ?? 0) > 0;

  String get stockDisplayLabel {
    if (inventoryStatusLabel.isNotEmpty) return inventoryStatusLabel;
    if (stock == null) return 'Available';
    return stock! > 0 ? 'In Stock' : 'Out of Stock';
  }

  Color get stockDisplayColor => statusColor(inventoryStatus, stock);

  String get expiryDisplayLabel {
    if (expiryDate == null) return 'Not set';
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
    final date = expiryDate!;
    return '${months[date.month - 1]} ${date.day}, ${date.year}';
  }

  static Color statusColor(String status, int? stock) {
    switch (status) {
      case 'low_stock':
      case 'expiring_soon':
        return const Color(0xFFB45309);
      case 'out_of_stock':
      case 'expired':
        return const Color(0xFFDC2626);
      case 'in_stock':
      default:
        if (stock != null && stock <= 0) return const Color(0xFFDC2626);
        return const Color(0xFF16A34A);
    }
  }

  static DateTime? _parseExpiry(dynamic raw) {
    if (raw == null) return null;
    final value = raw.toString().trim();
    if (value.isEmpty) return null;
    return DateTime.tryParse(value.length > 10 ? value : '${value}T00:00:00');
  }

  static int? _parseInt(dynamic raw) {
    if (raw == null) return null;
    return raw is int ? raw : int.tryParse('$raw');
  }

  static bool isPerishableCategory(String? category) {
    const perishable = {
      'Rice Meals',
      'Snacks',
      'Desserts',
      'Beverages',
      'Combo Meals',
      'Breakfast',
    };
    return perishable.contains(category?.trim());
  }
}

List<String> _parseProductImages(dynamic rawImages, String primaryImage) {
  final images = <String>[];

  void addImage(dynamic value) {
    final image = value?.toString().trim() ?? '';
    if (image.isNotEmpty && !images.contains(image)) images.add(image);
  }

  addImage(primaryImage);
  if (rawImages is List) {
    for (final image in rawImages) {
      addImage(image);
    }
  }
  return List.unmodifiable(images);
}

IconData iconForProduct(String value) {
  final lower = value.toLowerCase();
  if (lower.contains('beverage') ||
      lower.contains('coffee') ||
      lower.contains('drink') ||
      lower.contains('shake')) {
    return Icons.local_cafe_outlined;
  }
  if (lower.contains('dessert')) return Icons.icecream_outlined;
  if (lower.contains('snack') || lower.contains('fries')) {
    return Icons.fastfood_outlined;
  }
  if (lower.contains('breakfast')) return Icons.breakfast_dining_outlined;
  return Icons.lunch_dining_outlined;
}

Color colorForProduct(String value) {
  final lower = value.toLowerCase();
  if (lower.contains('beverage') ||
      lower.contains('coffee') ||
      lower.contains('drink') ||
      lower.contains('shake')) {
    return const Color(0xFFDDEBFF);
  }
  if (lower.contains('dessert')) return const Color(0xFFF3DCE6);
  if (lower.contains('snack')) return const Color(0xFFFFE0B2);
  if (lower.contains('breakfast')) return const Color(0xFFFFF4C7);
  return const Color(0xFFEAF7EE);
}
