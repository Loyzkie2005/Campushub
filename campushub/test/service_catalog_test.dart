import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:campushub/module_app/services/service_catalog.dart';
import 'package:campushub/module_app/config/api_config.dart';

void main() {
  tearDown(() => ApiConfig.recordWorkingBaseUrl(ApiConfig.baseUrl));
  test('reads actual catalog and filters inactive rows', () async {
    final catalog = ServiceCatalog(
      baseUrls: ['http://working:8000'],
      client: MockClient((request) async {
        expect(request.url.path, '/api/mobile/services/');
        return http.Response(
          jsonEncode({
            'services': [
              {
                'id': 'real-1',
                'name': 'Configured Lab',
                'status': 'active',
                'facility_type': 'food_analysis',
              },
              {'id': 'real-2', 'name': 'Inactive Lab', 'status': 'inactive'},
            ],
          }),
          200,
        );
      }),
    );
    final rows = await catalog.fetchServices();
    expect(rows.single.name, 'Configured Lab');
    expect(rows.single.actionLabel, 'How to Request This Service');
  });
  test('empty catalog is an honest success', () async {
    final rows = await ServiceCatalog(
      baseUrls: ['http://working'],
      client: MockClient((_) async => http.Response('{"services":[]}', 200)),
    ).fetchServices();
    expect(rows, isEmpty);
  });
  test('invalid responses are errors instead of fake empty lists', () async {
    for (final response in [
      http.Response('{}', 200),
      http.Response('<html>error</html>', 500),
    ]) {
      final catalog = ServiceCatalog(
        baseUrls: ['http://bad'],
        client: MockClient((_) async => response),
      );
      await expectLater(
        catalog.fetchServices(),
        throwsA(isA<ServiceCatalogException>()),
      );
    }
  });
  test('hanging host does not block working fallback', () async {
    final catalog = ServiceCatalog(
      baseUrls: ['http://old', 'http://working'],
      timeout: const Duration(milliseconds: 20),
      client: MockClient((request) async {
        if (request.url.host == 'old') return Completer<http.Response>().future;
        return http.Response('{"services":[]}', 200);
      }),
    );
    expect(await catalog.fetchServices(), isEmpty);
    await Future<void>.delayed(const Duration(milliseconds: 25));
  });
  test('detail uses the selected record and type-specific action', () async {
    for (final entry in {
      'training_kitchen': 'How to Request This Service',
      'lease_space': 'How to Request This Service',
    }.entries) {
      final catalog = ServiceCatalog(
        baseUrls: ['http://working'],
        client: MockClient((request) async {
          expect(request.url.path, '/api/mobile/services/chosen/');
          return http.Response(
            jsonEncode({
              'service': {
                'id': 'chosen',
                'name': 'Saved service',
                'facility_type': entry.key,
                'status': 'active',
              },
            }),
            200,
          );
        }),
      );
      expect((await catalog.fetchService('chosen')).actionLabel, entry.value);
    }
  });
}
