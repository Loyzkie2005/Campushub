import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../session/session_service.dart';

class OrderService {
  OrderService._();

  static const String _historyKey = 'campushub_order_history';
  static String requestKey() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }

  static Future<bool> placeOrder({
    required Map<String, dynamic> order,
    String? operationKey,
  }) async {
    final key = operationKey ?? requestKey();
    final token = await SessionService.loadChatToken();
    // A POST timeout may follow a committed order; retry only explicitly with the same key.
    for (final baseUrl in [ApiConfig.effectiveBaseUrl]) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/api/orders/'),
              headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Idempotency-Key': key,
                if (token != null && token.isNotEmpty)
                  'Authorization': 'Bearer $token',
              },
              body: jsonEncode(order),
            )
            .timeout(const Duration(seconds: 6));

        if (response.statusCode >= 200 && response.statusCode < 300) {
          final decoded = jsonDecode(response.body);
          if (decoded is! Map ||
              decoded['order'] is! Map ||
              decoded['order']['id'] == null) {
            return false;
          }
          ApiConfig.recordWorkingBaseUrl(baseUrl);
          await saveOrderHistory(order);
          return true;
        }
      } catch (_) {}
    }
    return false;
  }

  static Future<void> saveOrderHistory(Map<String, dynamic> order) async {
    final prefs = await SharedPreferences.getInstance();
    final history = await loadOrderHistory();
    history.insert(0, {
      ...order,
      'created_at': DateTime.now().toIso8601String(),
    });
    await prefs.setString(_historyKey, jsonEncode(history.take(30).toList()));
  }

  static Future<List<Map<String, dynamic>>> loadOrderHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_historyKey);
    if (raw == null || raw.isEmpty) return [];
    try {
      final decoded = jsonDecode(raw) as List<dynamic>;
      return decoded
          .whereType<Map>()
          .map((row) => row.map((key, value) => MapEntry('$key', value)))
          .toList(growable: false);
    } catch (_) {
      return [];
    }
  }
}
