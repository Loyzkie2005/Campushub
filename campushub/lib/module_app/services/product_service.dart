import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import 'seller_application_service.dart';
import '../models/product_item.dart';
import '../session/session_service.dart';

class ProductLoadException implements Exception {
  const ProductLoadException(this.message);
  final String message;
  @override
  String toString() => message;
}

/// ML product recommendations and interaction tracking.
class ProductService {
  ProductService._();

  static List<String> get _baseUrls => ApiConfig.serverBaseUrls;

  /// Prefer the configured/last working server, then race read-only fallbacks.
  /// One failed host cannot hold the spinner for every old address in sequence.
  static Future<List<ProductItem>> fetchApproved({
    http.Client? client,
    List<String>? baseUrls,
    Duration preferredTimeout = const Duration(seconds: 2),
    Duration fallbackTimeout = const Duration(seconds: 5),
  }) async {
    final urls = baseUrls ?? _baseUrls;
    final connection = client ?? http.Client();
    Future<List<ProductItem>> load(String baseUrl, Duration timeout) async {
      final response = await connection
          .get(
            Uri.parse('$baseUrl/api/products/approved/'),
            headers: const {'Accept': 'application/json'},
          )
          .timeout(timeout);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw const ProductLoadException(
          'The product server returned an error.',
        );
      }
      final decoded = jsonDecode(response.body);
      if (decoded is! Map || decoded['products'] is! List) {
        throw const FormatException('Invalid product response');
      }
      final products = (decoded['products'] as List)
          .map((row) {
            if (row is! Map) throw const FormatException('Invalid product row');
            return ProductItem.fromJson(Map<String, dynamic>.from(row));
          })
          .toList(growable: false);
      return products;
    }

    try {
      if (urls.isNotEmpty) {
        try {
          final products = await load(urls.first, preferredTimeout);
          ApiConfig.recordWorkingBaseUrl(urls.first);
          return products;
        } catch (_) {
          // A stale cached address must not prevent recovery on another host.
        }
      }
      final remaining = urls.skip(1).toList(growable: false);
      if (remaining.isEmpty) {
        throw const ProductLoadException(connectionMessage);
      }
      final result = Completer<List<ProductItem>>();
      var failures = 0;
      for (final baseUrl in remaining) {
        load(baseUrl, fallbackTimeout).then(
          (products) {
            if (!result.isCompleted) {
              ApiConfig.recordWorkingBaseUrl(baseUrl);
              result.complete(products);
            }
          },
          onError: (Object error, StackTrace stack) {
            failures++;
            if (failures == remaining.length && !result.isCompleted) {
              result.completeError(
                const ProductLoadException(connectionMessage),
              );
            }
          },
        );
      }
      return await result.future;
    } finally {
      // Close this call's client to cancel requests to losing/unreachable hosts.
      if (client == null) connection.close();
    }
  }

  static const connectionMessage = ApiConfig.usesPublicServer
      ? 'Cannot reach CampusHub online. Check your internet connection and retry.'
      : 'Cannot reach the product server. Check that your phone and PC are on '
            'the same Wi-Fi, Django is running on 0.0.0.0:8000, and the app uses '
            'your PC\'s current IP address. Then retry.';

  /// GET /api/products/recommended/ — scikit-learn TF-IDF recommendations.
  static Future<List<Map<String, dynamic>>> fetchRecommended({
    int? userId,
    int limit = 8,
    int? seedProductId,
    bool personalizedOnly = false,
  }) async {
    for (final baseUrl in _baseUrls) {
      try {
        final query = <String, String>{
          'limit': '$limit',
          if (userId != null) 'user_id': '$userId',
          if (seedProductId != null) 'product_id': '$seedProductId',
          if (personalizedOnly) 'personalized_only': '1',
        };
        final uri = Uri.parse(
          '$baseUrl/api/products/recommended/',
        ).replace(queryParameters: query);

        final response = await http
            .get(uri, headers: const {'Accept': 'application/json'})
            .timeout(const Duration(seconds: 6));

        if (response.statusCode >= 200 && response.statusCode < 300) {
          ApiConfig.recordWorkingBaseUrl(baseUrl);
          final decoded = jsonDecode(response.body) as Map<String, dynamic>;
          // An older server may ignore the new flag and return general items.
          if (personalizedOnly && decoded['personalized_only'] != true) {
            return [];
          }
          final rows = decoded['products'] as List<dynamic>? ?? [];
          return rows
              .whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .toList();
        }
      } catch (_) {}
    }
    return [];
  }

  /// No general-catalog fallback: only the existing account's interaction seeds.
  static Future<List<ProductItem>> fetchSearchRecommendations() async {
    final user = await SessionService.loadUser();
    if (user == null) return [];
    final rows = await fetchRecommended(
      userId: user.id,
      personalizedOnly: true,
    );
    return rows.map(ProductItem.fromJson).toList(growable: false);
  }

  /// POST /api/products/interaction/ — record view/click for ML training.
  static Future<void> trackInteraction({
    required int userId,
    required int productId,
    String interactionType = 'view',
  }) async {
    for (final baseUrl in _baseUrls) {
      try {
        await http
            .post(
              Uri.parse('$baseUrl/api/products/interaction/'),
              headers: const {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
              },
              body: jsonEncode({
                'user_id': userId,
                'product_id': productId,
                'interaction_type': interactionType,
              }),
            )
            .timeout(const Duration(seconds: 4));
        return;
      } catch (_) {}
    }
  }

  /// POST /api/seller/products/submit/ — seller listing with optional expiry, threshold, and tags.
  static Future<Map<String, dynamic>> submitProduct({
    required String name,
    required String price,
    required String category,
    required int stock,
    int? lowStockThreshold,
    String? tags,
    String description = '',
    String? expiryDate,
    String imageUrl = '',
    List<String> images = const [],
  }) async {
    final result = await const SellerApplicationService().createProduct({
      'name': name,
      'price': price,
      'category': category,
      'stock': stock,
      'low_stock_threshold': ?lowStockThreshold,
      if (tags != null && tags.trim().isNotEmpty) 'tags': tags.trim(),
      'description': description,
      'expiry_date': ?expiryDate,
      if (images.isNotEmpty)
        'images': images
      else if (imageUrl.isNotEmpty)
        'image_url': imageUrl,
    });
    final product = result['product'];
    if (product is! Map<String, dynamic>) {
      throw const SellerApplicationException(
        'Unable to confirm submission. Check My Products before trying again.',
      );
    }
    return product;
  }
}
