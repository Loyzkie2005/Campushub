import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';

class OrderService {
  OrderService._();

  static const String _historyKey = 'campushub_order_history';

  static Future<bool> placeOrder({required Map<String, dynamic> order}) async {
    await saveOrderHistory(order);

    for (final baseUrl in ApiConfig.serverBaseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/api/orders/'),
              headers: const {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
              },
              body: jsonEncode(order),
            )
            .timeout(const Duration(seconds: 6));

        if (response.statusCode >= 200 && response.statusCode < 300) {
          ApiConfig.recordWorkingBaseUrl(baseUrl);
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
