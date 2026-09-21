import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../session/session_service.dart';

class BookingException implements Exception {
  const BookingException(this.message);
  final String message;
  @override
  String toString() => message;
}

class FacilityBookingService {
  const FacilityBookingService();

  static String newRequestKey() {
    final random = Random.secure();
    final bytes = List.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }

  Future<Map<String, dynamic>> request(
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final token = await SessionService.loadChatToken();
    if (token == null) throw const BookingException('Sign in to continue.');
    final uri = Uri.parse('${ApiConfig.effectiveBaseUrl}/api/mobile/$path');
    final headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
    try {
      final response =
          await (body == null
                  ? http.get(uri, headers: headers)
                  : http.post(uri, headers: headers, body: jsonEncode(body)))
              .timeout(const Duration(seconds: 15));
      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) throw const FormatException();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw BookingException(
          decoded['error']?.toString() ?? 'Unable to complete the request.',
        );
      }
      return decoded;
    } on BookingException {
      rethrow;
    } catch (_) {
      throw const BookingException(
        'Unable to connect. Check your connection and try again.',
      );
    }
  }

  Future<List<Map<String, dynamic>>> slots(
    String facilityId,
    DateTime date,
  ) async {
    final result = await request(
      'facilities/${Uri.encodeComponent(facilityId)}/availability/?date=${dateKey(date)}',
    );
    return (result['slots'] as List)
        .map((e) => Map<String, dynamic>.from(e))
        .toList();
  }

  static String dateKey(DateTime date) =>
      '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
}
