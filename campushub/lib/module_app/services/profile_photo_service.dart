import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import 'auth_service.dart';

class ProfilePhotoException implements Exception {
  const ProfilePhotoException(this.message);
  final String message;
}

class ProfilePhotoService {
  const ProfilePhotoService();
  static const maxBytes = 5 * 1024 * 1024;

  Future<AuthUser> load(String token) async {
    final response = await http
        .get(
          Uri.parse('${ApiConfig.mobileApi}/profile/photo/'),
          headers: {'Authorization': 'Bearer $token'},
        )
        .timeout(const Duration(seconds: 10));
    return _user(response);
  }

  Future<AuthUser> upload(String token, Uint8List bytes) async {
    if (bytes.isEmpty || bytes.length > maxBytes) {
      throw const ProfilePhotoException('Choose a picture smaller than 5 MB.');
    }
    final request =
        http.MultipartRequest(
            'POST',
            Uri.parse('${ApiConfig.mobileApi}/profile/photo/'),
          )
          ..headers['Authorization'] = 'Bearer $token'
          ..files.add(
            http.MultipartFile.fromBytes(
              'photo',
              bytes,
              filename: 'profile-photo',
            ),
          );
    // Send once: a timeout must never silently replay an account mutation.
    final client = http.Client();
    try {
      final response = await (() async => http.Response.fromStream(
        await client.send(request),
      ))().timeout(const Duration(seconds: 30));
      return _user(response);
    } finally {
      client.close();
    }
  }

  AuthUser _user(http.Response response) {
    final Map<String, dynamic> data;
    try {
      data = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      throw const ProfilePhotoException(
        'Unable to read the server response. Try again.',
      );
    }
    if (response.statusCode != 200 || data['user'] is! Map<String, dynamic>) {
      throw ProfilePhotoException(
        data['error'] as String? ??
            'Unable to update your profile picture. Try again.',
      );
    }
    return AuthUser.fromJson(data['user'] as Map<String, dynamic>);
  }
}
