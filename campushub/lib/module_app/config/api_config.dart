/// Shared API configuration for local development and online builds.
/// Set CAMPUSHUB_API_BASE_URL to an HTTPS origin for an online APK.
/// Without it, existing PC/LAN development addresses remain available.
class ApiConfig {
  ApiConfig._();

  static const String publicBaseUrl = String.fromEnvironment(
    'CAMPUSHUB_API_BASE_URL',
  );
  static const bool usesPublicServer = publicBaseUrl != '';
  static final String? _onlineBaseUrl = _readPublicBaseUrl();

  static String? _readPublicBaseUrl() {
    if (!usesPublicServer) return null;
    final uri = Uri.tryParse(publicBaseUrl.trim());
    if (uri == null ||
        uri.scheme != 'https' ||
        uri.host.isEmpty ||
        uri.userInfo.isNotEmpty ||
        (uri.path.isNotEmpty && uri.path != '/') ||
        uri.hasQuery ||
        uri.hasFragment) {
      throw ArgumentError(
        'CAMPUSHUB_API_BASE_URL must be an HTTPS origin without credentials, '
        'a path, query, or fragment.',
      );
    }
    return uri.origin;
  }

  /// Default PC address for the current Wi-Fi connection.
  /// Override it at launch with `--dart-define=CAMPUSHUB_HOST_IP=<IP>`.
  static const String hostIp = String.fromEnvironment(
    'CAMPUSHUB_HOST_IP',
    defaultValue: '192.168.1.187',
  );

  /// Previous laptop addresses, mobile hotspot, and ADB reverse loopback.
  /// 127.0.0.1 = ADB reverse tethering (adb reverse tcp:8000 tcp:8000)
  /// 192.168.137.1 = Windows Mobile Hotspot default gateway (PC-to-phone tethering).
  static const List<String> fallbackHostIps = [
    '127.0.0.1', // ADB reverse loopback
    '192.168.0.122', // Previous PC Wi-Fi address
    '192.168.137.1', // Windows Mobile Hotspot
    '192.168.0.159', // Previous Wi-Fi address
    '192.168.1.187', // Current PC Wi-Fi address
    '192.168.137.100', // Current PC address on the hotspot network
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
    if (usesPublicServer) {
      // Online builds stay on their configured origin, including after errors.
      if (trimmed == ApiConfig.baseUrl) _activeBaseUrl = ApiConfig.baseUrl;
      return;
    }
    if (trimmed.isNotEmpty) {
      _activeBaseUrl = trimmed;
    }
  }

  static String get effectiveBaseUrl => _activeBaseUrl ?? baseUrl;

  static String get baseUrl => _onlineBaseUrl ?? 'http://$hostIp:$port';

  static String get mobileApi => '$effectiveBaseUrl/api/mobile';

  static String get chatHttpUrl {
    if (usesPublicServer) return '$baseUrl/chat';
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
    if (usesPublicServer) {
      return Uri.parse(
        baseUrl,
      ).replace(scheme: 'wss', path: '/chat/ws').toString();
    }
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
    if (usesPublicServer) return [baseUrl];
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
