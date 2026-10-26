import 'package:flutter_test/flutter_test.dart';
import 'package:campushub/module_app/config/api_config.dart';
import 'package:campushub/module_app/services/product_service.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  group('local development', () {
    test('chat URLs do not contain an empty query before the route', () {
      expect(ApiConfig.chatHttpUrl, 'http://${ApiConfig.hostIp}:8001');
      expect(ApiConfig.chatWebSocketUrl, 'ws://${ApiConfig.hostIp}:8001/ws');

      final conversationsUri = Uri.parse(
        '${ApiConfig.chatHttpUrl}/conversations',
      );
      expect(conversationsUri.path, '/conversations');
      expect(conversationsUri.hasQuery, isFalse);
    });

    test('keeps current Wi-Fi and previous hotspot API addresses', () {
      expect(ApiConfig.serverBaseUrls.first, ApiConfig.baseUrl);
      expect(
        ApiConfig.serverBaseUrls,
        containsAll([
          'http://192.168.1.187:8000',
          'http://192.168.0.122:8000',
          'http://192.168.137.100:8000',
          'http://192.168.137.1:8000',
          'http://127.0.0.1:8000',
          'http://10.0.2.2:8000',
        ]),
      );
      expect(
        ApiConfig.serverBaseUrls.toSet().length,
        ApiConfig.serverBaseUrls.length,
      );
    });
  }, skip: ApiConfig.usesPublicServer);

  group('online build', () {
    final origin = ApiConfig.usesPublicServer
        ? Uri.parse(ApiConfig.publicBaseUrl.trim()).origin
        : null;

    test('catalog, authentication and chat use one HTTPS origin', () {
      expect(ApiConfig.baseUrl, origin);
      expect(ApiConfig.serverBaseUrls, [origin]);
      expect(ApiConfig.mobileApiUrls, ['$origin/api/mobile']);
      expect(ApiConfig.chatHttpUrl, '$origin/chat');
      expect(
        ApiConfig.chatWebSocketUrl,
        Uri.parse(origin!).replace(scheme: 'wss', path: '/chat/ws').toString(),
      );
    });

    test(
      'remembered servers cannot switch online requests to LAN or another host',
      () {
        for (final candidate in [
          'http://127.0.0.1:8000',
          'http://192.168.1.187:8000',
          'https://another-server.invalid',
          '$origin?redirect=1',
        ]) {
          ApiConfig.recordWorkingBaseUrl(candidate);
          expect(ApiConfig.effectiveBaseUrl, origin);
          expect(ApiConfig.serverBaseUrls, [origin]);
        }
        ApiConfig.recordWorkingBaseUrl('$origin/');
        expect(ApiConfig.effectiveBaseUrl, origin);
      },
    );

    test('existing marketplace loader requests the public catalog', () async {
      final rows = await ProductService.fetchApproved(
        client: MockClient((request) async {
          expect(request.url.toString(), '$origin/api/products/approved/');
          return http.Response('{"products":[]}', 200);
        }),
      );
      expect(rows, isEmpty);
    });

    test(
      'failed online catalog request never falls back to a PC address',
      () async {
        final requested = <Uri>[];
        await expectLater(
          ProductService.fetchApproved(
            client: MockClient((request) async {
              requested.add(request.url);
              throw http.ClientException('offline');
            }),
          ),
          throwsA(isA<ProductLoadException>()),
        );
        expect(requested, [Uri.parse('$origin/api/products/approved/')]);
        expect(
          ProductService.connectionMessage,
          contains('internet connection'),
        );
        expect(ProductService.connectionMessage, isNot(contains('0.0.0.0')));
      },
    );
  }, skip: !ApiConfig.usesPublicServer);
}
