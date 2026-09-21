import 'package:flutter_test/flutter_test.dart';
import 'package:campushub/module_app/config/api_config.dart';

void main() {
  test('chat URLs do not contain an empty query before the route', () {
    expect(ApiConfig.chatHttpUrl, 'http://192.168.1.187:8001');
    expect(ApiConfig.chatWebSocketUrl, 'ws://192.168.1.187:8001/ws');

    final conversationsUri = Uri.parse(
      '${ApiConfig.chatHttpUrl}/conversations',
    );
    expect(conversationsUri.path, '/conversations');
    expect(conversationsUri.hasQuery, isFalse);
  });

  test('keeps current Wi-Fi and previous hotspot API addresses', () {
    expect(ApiConfig.serverBaseUrls, [
      'http://192.168.1.187:8000',
      'http://10.0.2.2:8000',
      'http://10.214.157.171:8000',
      'http://10.219.142.170:8000',
      'http://192.168.0.154:8000',
      'http://192.168.1.103:8000',
    ]);
  });
}
