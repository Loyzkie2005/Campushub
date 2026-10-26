import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/service_item.dart';

class ServiceCatalogException implements Exception {
  const ServiceCatalogException(this.message);
  final String message;
  @override
  String toString() => message;
}

class ServiceCatalog {
  const ServiceCatalog({
    this.client,
    this.baseUrls,
    this.timeout = const Duration(seconds: 4),
  });
  final http.Client? client;
  final List<String>? baseUrls;
  final Duration timeout;

  Future<Map<String, dynamic>> _get(String path) async {
    final urls = baseUrls ?? ApiConfig.serverBaseUrls;
    final result = Completer<Map<String, dynamic>>();
    var failures = 0;
    if (urls.isEmpty) {
      throw const ServiceCatalogException(
        'Unable to load services. Please retry.',
      );
    }
    final connection = client ?? http.Client();
    try {
      // Parallel read-only fallbacks have one bounded wait, not one wait per old host.
      for (final base in urls) {
        Future<void>(() async {
          try {
            final response = await connection
                .get(
                  Uri.parse('$base/api/mobile/services/$path'),
                  headers: const {'Accept': 'application/json'},
                )
                .timeout(timeout);
            final body = jsonDecode(response.body);
            if (response.statusCode != 200 || body is! Map<String, dynamic>) {
              throw const FormatException();
            }
            if ((path.isEmpty && body['services'] is! List) ||
                (path.isNotEmpty && body['service'] is! Map)) {
              throw const FormatException();
            }
            if (!result.isCompleted) {
              ApiConfig.recordWorkingBaseUrl(base);
              result.complete(body);
            }
          } catch (_) {
            failures++;
            if (failures == urls.length && !result.isCompleted) {
              result.completeError(
                const ServiceCatalogException(
                  'Unable to load services. Check your connection and retry.',
                ),
              );
            }
          }
        });
      }
      return await result.future;
    } finally {
      if (client == null) connection.close();
    }
  }

  Future<List<ServiceItem>> fetchServices() async {
    final body = await _get('');
    return (body['services'] as List)
        .map((row) => ServiceItem.fromJson(Map<String, dynamic>.from(row)))
        .where((row) => row.active)
        .toList();
  }

  Future<ServiceItem> fetchService(String id) async {
    final body = await _get('${Uri.encodeComponent(id)}/');
    return ServiceItem.fromJson(Map<String, dynamic>.from(body['service']));
  }
}
