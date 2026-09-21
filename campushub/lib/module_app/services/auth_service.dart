import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class AuthUser {
  const AuthUser({
    required this.id,
    required this.studentId,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.fullName,
    required this.role,
    required this.userType,
    required this.profileStudentId,
    required this.institutionalId,
    required this.contactNumber,
    required this.profileCompleted,
  });

  final int id;
  final String studentId;
  final String email;
  final String firstName;
  final String lastName;
  final String fullName;
  final String role;
  final String userType;
  final String profileStudentId;
  final String institutionalId;
  final String contactNumber;
  final bool profileCompleted;

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    final rawId = json['id'];
    return AuthUser(
      id: rawId is int ? rawId : int.tryParse('$rawId') ?? 0,
      studentId:
          json['username'] as String? ?? json['student_id'] as String? ?? '',
      email: json['email'] as String? ?? '',
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      role: json['role'] as String? ?? '',
      userType: json['user_type'] as String? ?? '',
      profileStudentId: json['student_id'] as String? ?? '',
      institutionalId: json['institutional_id'] as String? ?? '',
      contactNumber: json['contact_number'] as String? ?? '',
      profileCompleted: json['profile_completed'] == true,
    );
  }
}

class AuthResult {
  const AuthResult({
    required this.success,
    this.user,
    this.chatToken,
    this.message,
    this.emailSent = false,
  });

  final bool success;
  final AuthUser? user;
  final String? chatToken;
  final String? message;

  final bool emailSent;
}

class AuthService {
  AuthService._();

  static List<String> get _baseUrls => ApiConfig.mobileApiUrls;

  static Future<AuthResult> login({
    required String studentIdOrEmail,
    required String password,
  }) async {
    return _post('login/', {
      'student_id_or_email': studentIdOrEmail.trim(),
      'password': password,
    }, expectUser: true);
  }

  static Future<AuthResult> signUp({
    required String firstName,
    required String lastName,
    required String studentId,
    required String email,
    required String password,
    required String confirmPassword,
  }) async {
    return _post('signup/', {
      'first_name': firstName.trim(),
      'last_name': lastName.trim(),
      'student_id': studentId.trim(),
      'email': email.trim(),
      'password': password,
      'confirm_password': confirmPassword,
    }, expectUser: true);
  }

  static Future<AuthResult> completeProfile({
    required String token,
    required String userType,
    required String institutionalId,
    required String contactNumber,
  }) async {
    return _post(
      'profile/complete/',
      {
        'user_type': userType,
        'student_id': userType == 'student' ? institutionalId.trim() : '',
        'institutional_id': userType == 'faculty' ? institutionalId.trim() : '',
        'contact_number': contactNumber.trim(),
      },
      expectUser: true,
      authorizationToken: token,
    );
  }

  static Future<AuthResult> sendPasswordResetCode({
    required String email,
  }) async {
    return _post('password-reset/', {'email': email.trim().toLowerCase()});
  }

  static Future<AuthResult> verifyPasswordResetCode({
    required String email,
    required String code,
  }) async {
    return _post('password-reset/verify/', {
      'email': email.trim().toLowerCase(),
      'code': code.trim(),
    });
  }

  static Future<AuthResult> confirmPasswordReset({
    required String email,
    required String code,
    required String newPassword,
    required String confirmPassword,
  }) async {
    return _post('password-reset/confirm/', {
      'email': email.trim().toLowerCase(),
      'code': code.trim(),
      'new_password': newPassword,
      'confirm_password': confirmPassword,
    });
  }

  static Future<AuthResult> _post(
    String path,
    Map<String, String> body, {
    bool expectUser = false,
    String? authorizationToken,
  }) async {
    String? lastError;

    for (final baseUrl in _baseUrls) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/$path'),
              headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                if (authorizationToken != null)
                  'Authorization': 'Bearer $authorizationToken',
              },
              body: jsonEncode(body),
            )
            .timeout(const Duration(seconds: 5));

        final decoded = _decodeJson(response.body);

        if (response.statusCode >= 200 && response.statusCode < 300) {
          ApiConfig.recordWorkingBaseUrl(
            baseUrl.replaceFirst(RegExp(r'/api/mobile/?$'), ''),
          );
          AuthUser? user;
          if (expectUser && decoded['user'] is Map<String, dynamic>) {
            user = AuthUser.fromJson(decoded['user'] as Map<String, dynamic>);
          }
          return AuthResult(
            success: true,
            user: user,
            chatToken: decoded['chat_token'] as String?,
            message: decoded['message'] as String?,
            emailSent: decoded['email_sent'] == true,
          );
        }

        return AuthResult(
          success: false,
          message:
              decoded['error'] as String? ??
              'Request failed (${response.statusCode}).',
        );
      } catch (e) {
        // Keep the primary server in the error instead of showing the last
        // historical fallback address that also failed.
        lastError ??= 'Could not reach $baseUrl';
      }
    }

    return AuthResult(
      success: false,
      message:
          lastError ??
          'Cannot reach server. Use the same Wi-Fi or hotspot. '
              'Django: runserver 0.0.0.0:8000\n'
              'Set IP in lib/module_app/config/api_config.dart → ${ApiConfig.hostIp}',
    );
  }

  static Map<String, dynamic> _decodeJson(String responseBody) {
    try {
      return jsonDecode(responseBody) as Map<String, dynamic>;
    } catch (_) {
      return {'error': 'Server returned an invalid response.'};
    }
  }
}
