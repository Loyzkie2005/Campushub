import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class PushSession {
  const PushSession({required this.userId, required this.token});
  final int userId;
  final String token;

  bool matches(PushSession? other) =>
      other != null && userId == other.userId && token == other.token;
}

/// Carries only a response status, never a bearer token or response body.
class PushRegistrationException implements Exception {
  const PushRegistrationException(this.statusCode);
  final int statusCode;
}

/// Device ownership always comes from Django's existing bearer authentication.
class PushDeviceApi {
  PushDeviceApi({http.Client? client, Uri Function()? endpoint})
    : _client = client ?? http.Client(),
      _endpoint =
          endpoint ?? (() => Uri.parse('${ApiConfig.mobileApi}/push/device/'));

  final http.Client _client;
  final Uri Function() _endpoint;

  Future<bool> bind(PushSession session, String fid) =>
      _send('POST', session, fid);
  Future<bool> unbind(PushSession session, String fid) =>
      _send('DELETE', session, fid);

  Future<bool> _send(String method, PushSession session, String fid) async {
    final request = http.Request(method, _endpoint())
      ..headers.addAll({
        'Authorization': 'Bearer ${session.token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      })
      ..body = jsonEncode({'installation_id': fid});
    return (() async {
      final response = await _client.send(request);
      await response.stream.drain<void>();
      if (method == 'POST' && response.statusCode != 200) {
        throw PushRegistrationException(response.statusCode);
      }
      return response.statusCode == 200 ||
          (method == 'DELETE' && response.statusCode == 401);
    })().timeout(const Duration(seconds: 5));
  }
}
