import 'dart:convert';

import 'package:campushub/module_app/services/push_device_api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const session = PushSession(userId: 3, token: 'isolated-bearer');

  test('bind uses bearer and FID only at the existing Django server', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(
        request.url.toString(),
        'http://localhost/api/mobile/push/device/',
      );
      expect(request.headers['Authorization'], 'Bearer isolated-bearer');
      expect(jsonDecode(request.body), {
        'installation_id': 'isolated_installation_12345',
      });
      return http.Response('{"ok":true}', 200);
    });
    final api = PushDeviceApi(
      client: client,
      endpoint: () => Uri.parse('http://localhost/api/mobile/push/device/'),
    );
    expect(await api.bind(session, 'isolated_installation_12345'), isTrue);
  });

  test(
    'expired logout is harmless but rejected binding stays unsuccessful',
    () async {
      final api = PushDeviceApi(
        client: MockClient((_) async => http.Response('{}', 401)),
        endpoint: () => Uri.parse('http://localhost/api/mobile/push/device/'),
      );
      expect(await api.unbind(session, 'isolated_installation_12345'), isTrue);
      await expectLater(
        api.bind(session, 'isolated_installation_12345'),
        throwsA(
          isA<PushRegistrationException>().having(
            (error) => error.statusCode,
            'status',
            401,
          ),
        ),
      );
    },
  );

  test(
    'network errors propagate to the nonfatal lifecycle error handler',
    () async {
      final api = PushDeviceApi(
        client: MockClient(
          (_) async => throw http.ClientException('Isolated failure'),
        ),
        endpoint: () => Uri.parse('http://localhost/api/mobile/push/device/'),
      );
      await expectLater(
        api.bind(session, 'isolated_installation_12345'),
        throwsA(isA<http.ClientException>()),
      );
    },
  );

  test(
    'server rejection retains status without exposing the response body',
    () async {
      final api = PushDeviceApi(
        client: MockClient(
          (_) async => http.Response('private server diagnostic', 500),
        ),
        endpoint: () => Uri.parse('http://localhost/api/mobile/push/device/'),
      );
      await expectLater(
        api.bind(session, 'isolated_installation_12345'),
        throwsA(
          isA<PushRegistrationException>().having(
            (error) => error.statusCode,
            'status',
            500,
          ),
        ),
      );
    },
  );
}
