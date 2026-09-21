/// CampusHub API — set [hostIp] to your PC's Wi-Fi/hotspot IPv4 address.
///
/// Find it on Windows: open CMD → `ipconfig` → look for "Wireless LAN" IPv4.
/// Phone and PC must be on the **same Wi-Fi or hotspot network**.
/// Start Django: `python manage.py runserver 0.0.0.0:8000`
class ApiConfig {
  ApiConfig._();

  /// Default PC address for the current Wi-Fi connection.
  /// Override it at launch with `--dart-define=CAMPUSHUB_HOST_IP=<IP>`.
  static const String hostIp = String.fromEnvironment(
    'CAMPUSHUB_HOST_IP',
    defaultValue: '192.168.1.187',
  );

  /// Previous laptop addresses and emulator loopback are retained as automatic fallbacks.
  static const List<String> fallbackHostIps = [
    '10.0.2.2',
    '10.214.157.171',
    '10.219.142.170',
    '192.168.0.154',
    '192.168.1.103',
  ];

  static const int port = 8000;
  static const int chatPort = 8001;

  /// Set automatically when the app successfully reaches the server.
  static String? _activeBaseUrl;

  static void recordWorkingBaseUrl(String baseUrl) {
    final trimmed = baseUrl.replaceAll(RegExp(r'/+$'), '');
    if (trimmed.isNotEmpty) {
      _activeBaseUrl = trimmed;
    }
  }

  static String get effectiveBaseUrl => _activeBaseUrl ?? baseUrl;

  static String get baseUrl => 'http://$hostIp:$port';

  static String get mobileApi => '$effectiveBaseUrl/api/mobile';

  static String get chatHttpUrl {
    final uri = Uri.tryParse(effectiveBaseUrl);
    if (uri != null && uri.host.isNotEmpty) {
      return Uri(
        scheme: uri.scheme.isEmpty ? 'http' : uri.scheme,
        host: uri.host,
        port: chatPort,
      ).toString();
    }
    return 'http://$hostIp:$chatPort';
  }

  static String get chatWebSocketUrl {
    final uri = Uri.tryParse(chatHttpUrl);
    if (uri != null && uri.host.isNotEmpty) {
      return Uri(
        scheme: uri.scheme == 'https' ? 'wss' : 'ws',
        host: uri.host,
        port: uri.hasPort ? uri.port : chatPort,
        path: '/ws',
      ).toString();
    }
    return 'ws://$hostIp:$chatPort/ws';
  }

  /// Orders URLs by the platform most likely to reach Django first.
  static List<String> get serverBaseUrls {
    final hosts = [hostIp, ...fallbackHostIps];
    return <String>{
      ?_activeBaseUrl,
      ...hosts.map((host) => 'http://$host:$port'),
    }.toList(growable: false);
  }

  static List<String> get mobileApiUrls => serverBaseUrls
      .map((baseUrl) => '$baseUrl/api/mobile')
      .toList(growable: false);
}
