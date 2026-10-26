import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:campushub/module_app/config/api_config.dart';
import 'package:campushub/module_app/services/product_service.dart';

void main() {
  tearDown(() => ApiConfig.recordWorkingBaseUrl(ApiConfig.baseUrl));
  http.Response catalog(List<Map<String, dynamic>> rows) =>
      http.Response(jsonEncode({'products': rows}), 200);

  test('preferred server returns real rows and is remembered', () async {
    final requested = <String>[];
    final rows = await ProductService.fetchApproved(
      baseUrls: ['http://current:8000', 'http://old:8000'],
      client: MockClient((request) async {
        requested.add(request.url.host);
        expect(request.url.path, '/api/products/approved/');
        return catalog([
          {'id': 7, 'name': 'Actual row', 'price': '25', 'stock': 3},
        ]);
      }),
    );
    expect(rows.single.id, 7);
    expect(requested, ['current']);
    expect(ApiConfig.effectiveBaseUrl, 'http://current:8000');
  });

  test('valid empty response is success, not a connection failure', () async {
    expect(
      await ProductService.fetchApproved(
        baseUrls: ['http://current:8000'],
        client: MockClient((_) async => catalog([])),
      ),
      isEmpty,
    );
  });

  test(
    'hanging preferred and slow fallback do not block a working host',
    () async {
      final requested = <String>[];
      final rows = await ProductService.fetchApproved(
        baseUrls: [
          'http://old:8000',
          'http://slow:8000',
          'http://working:8000',
        ],
        preferredTimeout: const Duration(milliseconds: 10),
        fallbackTimeout: const Duration(milliseconds: 40),
        client: MockClient((request) {
          requested.add(request.url.host);
          if (request.url.host != 'working') {
            return Completer<http.Response>().future;
          }
          return Future.value(
            catalog([
              {'id': 8, 'name': 'Working row'},
            ]),
          );
        }),
      );
      expect(rows.single.id, 8);
      expect(requested, ['old', 'slow', 'working']);
      expect(ApiConfig.effectiveBaseUrl, 'http://working:8000');
    },
  );

  test('all unreachable hosts finish with a retryable error', () async {
    await expectLater(
      ProductService.fetchApproved(
        baseUrls: [
          'http://old:8000',
          'http://slow:8000',
          'http://offline:8000',
        ],
        preferredTimeout: const Duration(milliseconds: 10),
        fallbackTimeout: const Duration(milliseconds: 20),
        client: MockClient((_) => Completer<http.Response>().future),
      ).timeout(const Duration(seconds: 1)),
      throwsA(isA<ProductLoadException>()),
    );
  });

  test(
    'HTTP failure and malformed JSON are not fabricated empty catalogs',
    () async {
      for (final response in [
        http.Response('error', 500),
        http.Response('<html>', 200),
        http.Response('{}', 200),
      ]) {
        await expectLater(
          ProductService.fetchApproved(
            baseUrls: ['http://current:8000'],
            client: MockClient((_) async => response),
          ),
          throwsA(isA<ProductLoadException>()),
        );
      }
    },
  );

  test('late successful fallback cannot overwrite the winning host', () async {
    await ProductService.fetchApproved(
      baseUrls: ['http://old:8000', 'http://late:8000', 'http://winner:8000'],
      client: MockClient((request) async {
        if (request.url.host == 'old') return http.Response('offline', 503);
        if (request.url.host == 'late') {
          await Future<void>.delayed(const Duration(milliseconds: 15));
        }
        return catalog([]);
      }),
    );
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(ApiConfig.effectiveBaseUrl, 'http://winner:8000');
  });
}
