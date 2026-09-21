import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class FacilityServiceResult {
  const FacilityServiceResult({
    required this.success,
    this.facilities = const [],
    this.message,
  });

  final bool success;
  final List<Map<String, dynamic>> facilities;
  final String? message;
}

class FacilityService {
  FacilityService._();

  static List<String> get _baseUrls => ApiConfig.serverBaseUrls;

  static Future<FacilityServiceResult> fetchFacilities() async {
    for (final baseUrl in _baseUrls) {
      try {
        final response = await http
            .get(
              Uri.parse('$baseUrl/api/facilities/'),
              headers: const {'Accept': 'application/json'},
            )
            .timeout(const Duration(seconds: 4));

        final decoded = _decodeJson(response.body);
        if (response.statusCode >= 200 && response.statusCode < 300) {
          final rows = (decoded['facilities'] as List<dynamic>? ?? [])
              .whereType<Map>()
              .map(
                (row) =>
                    row.map((key, value) => MapEntry(key.toString(), value)),
              )
              .toList(growable: false);
          return FacilityServiceResult(success: true, facilities: rows);
        }
      } catch (_) {}
    }

    return const FacilityServiceResult(
      success: false,
      message:
          'Connection error. Start Django with: python manage.py runserver 0.0.0.0:8000',
    );
  }

  static Map<String, dynamic> _decodeJson(String body) {
    try {
      return jsonDecode(body) as Map<String, dynamic>;
    } catch (_) {
      return <String, dynamic>{};
    }
  }
}
