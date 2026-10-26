import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../session/session_service.dart';

class SellerApplicationException implements Exception {
  const SellerApplicationException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
}

/// Uses the existing Django seller request contract; never activates access.
class SellerApplicationService {
  const SellerApplicationService();

  Future<Map<String, String>> _headers() async {
    final token = await SessionService.loadChatToken();
    if (token == null || token.isEmpty) {
      throw const SellerApplicationException(
        'Sign in again to manage your seller application.',
        statusCode: 401,
      );
    }
    return {
      'Authorization': 'Bearer $token',
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
  }

  Future<Map<String, dynamic>> status([String? ignoredLegacyId]) async {
    for (final base in ApiConfig.serverBaseUrls) {
      try {
        final uri = Uri.parse('$base/api/seller/access-status/');
        final response = await http
            .get(uri, headers: await _headers())
            .timeout(const Duration(seconds: 5));
        final data = _decode(response);
        ApiConfig.recordWorkingBaseUrl(base);
        return data;
      } on SellerApplicationException {
        rethrow;
      } catch (_) {
        // Only a read request may fail over to another configured address.
      }
    }
    throw const SellerApplicationException(
      'Unable to load your application status. Check your connection and retry.',
    );
  }

  Future<Map<String, dynamic>> submit(Map<String, dynamic> fields) async {
    try {
      // Do not automatically retry a POST: a timeout may follow a saved request.
      final response = await http
          .post(
            Uri.parse(
              '${ApiConfig.effectiveBaseUrl}/api/seller/access-request/',
            ),
            headers: await _headers(),
            body: jsonEncode(fields),
          )
          .timeout(const Duration(seconds: 15));
      return _decode(response);
    } on SellerApplicationException {
      rethrow;
    } catch (_) {
      throw const SellerApplicationException(
        'Unable to confirm submission. Check your application status before trying again.',
      );
    }
  }

  Future<List<Map<String, dynamic>>> products() async {
    final response = await http
        .get(
          Uri.parse(
            '${ApiConfig.effectiveBaseUrl}/api/seller/products/submit/',
          ),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 15));
    final data = _decode(response);
    return (data['products'] as List? ?? [])
        .whereType<Map>()
        .map((row) => Map<String, dynamic>.from(row))
        .toList();
  }

  Future<Map<String, dynamic>> workspace({
    String period = '30',
    int ordersPage = 1,
  }) async {
    final response = await http
        .get(
          Uri.parse(
            '${ApiConfig.effectiveBaseUrl}/api/mobile/seller/workspace/',
          ).replace(
            queryParameters: {'period': period, 'orders_page': '$ordersPage'},
          ),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 20));
    return _decode(response);
  }

  Future<void> suggestionChoice(String pairId, String action) async {
    // As with product submission, a POST must never be automatically retried.
    final response = await http
        .post(
          Uri.parse(
            '${ApiConfig.effectiveBaseUrl}/api/mobile/seller/suggestions/${Uri.encodeComponent(pairId)}/',
          ),
          headers: await _headers(),
          body: jsonEncode({'action': action}),
        )
        .timeout(const Duration(seconds: 15));
    _decode(response);
  }

  Future<void> orderProgress(int orderId, String action) async {
    final response = await http
        .post(
          Uri.parse(
            '${ApiConfig.effectiveBaseUrl}/api/mobile/seller/orders/$orderId/progress/',
          ),
          headers: await _headers(),
          body: jsonEncode({'action': action}),
        )
        .timeout(const Duration(seconds: 15));
    _decode(response);
  }

  Future<Map<String, dynamic>> createProduct(
    Map<String, dynamic> fields,
  ) async {
    try {
      final response = await http
          .post(
            Uri.parse(
              '${ApiConfig.effectiveBaseUrl}/api/seller/products/submit/',
            ),
            headers: await _headers(),
            body: jsonEncode(fields),
          )
          .timeout(const Duration(seconds: 15));
      return _decode(response);
    } on SellerApplicationException {
      rethrow;
    } catch (_) {
      throw const SellerApplicationException(
        'Unable to confirm product submission. Refresh My Products before trying again.',
      );
    }
  }

  Map<String, dynamic> _decode(http.Response response) {
    final dynamic data;
    try {
      data = jsonDecode(response.body);
    } catch (_) {
      throw const SellerApplicationException(
        'The server returned an unreadable response. Retry the status check.',
      );
    }
    if (data is! Map<String, dynamic>) {
      throw const SellerApplicationException(
        'The server returned an unreadable response. Retry the status check.',
      );
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw SellerApplicationException(
        data['error'] is String
            ? data['error'] as String
            : 'Unable to process the application. Please retry.',
        statusCode: response.statusCode,
      );
    }
    return data;
  }
}
