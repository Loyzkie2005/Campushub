import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

/// ML product recommendations and interaction tracking.
class ProductService {
  ProductService._();

  static List<String> get _baseUrls => ApiConfig.serverBaseUrls;

  /// GET /api/products/recommended/ — scikit-learn TF-IDF recommendations.
  static Future<List<Map<String, dynamic>>> fetchRecommended({
    int? userId,
    int limit = 8,
    int? seedProductId,
  }) async {
    for (final baseUrl in _baseUrls) {
      try {
        final query = <String, String>{
          'limit': '$limit',
          if (userId != null) 'user_id': '$userId',
          if (seedProductId != null) 'product_id': '$seedProductId',
        };
        final uri = Uri.parse('$baseUrl/api/products/recommended/')
            .replace(queryParameters: query);

        final response = await http
            .get(uri, headers: const {'Accept': 'application/json'})
            .timeout(const Duration(seconds: 6));

        if (response.statusCode >= 200 && response.statusCode < 300) {
          ApiConfig.recordWorkingBaseUrl(baseUrl);
          final decoded = jsonDecode(response.body) as Map<String, dynamic>;
          final rows = decoded['products'] as List<dynamic>? ?? [];
          return rows.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
        }
      } catch (_) {}
    }
    return [];
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

  /// POST /api/seller/products/submit/ — seller listing with optional expiry.
  static Future<Map<String, dynamic>?> submitProduct({
    required String name,
    required String price,
    required String category,
    required int stock,
    String description = '',
    String? expiryDate,
    String imageUrl = '',
  }) async {
    for (final baseUrl in _baseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/api/seller/products/submit/'),
              headers: const {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
              },
              body: jsonEncode({
                'name': name,
                'price': price,
                'category': category,
                'stock': stock,
                'description': description,
                if (expiryDate != null && expiryDate.isNotEmpty)
                  'expiry_date': expiryDate,
                if (imageUrl.isNotEmpty) 'image_url': imageUrl,
              }),
            )
            .timeout(const Duration(seconds: 8));

        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        if (response.statusCode >= 200 && response.statusCode < 300) {
          ApiConfig.recordWorkingBaseUrl(baseUrl);
          final product = decoded['product'];
          if (product is Map<String, dynamic>) return product;
          return decoded;
        }
      } catch (_) {}
    }
    return null;
  }
}
