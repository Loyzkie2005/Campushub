import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/auth_service.dart';
import '../services/push_device_api.dart';
import '../services/push_notification_service.dart';

/// Persists the logged-in user across app restarts.
class SessionService {
  SessionService._();

  static const String _userKey = 'campushub_logged_user';
  static const String _chatTokenKey = 'campushub_chat_token';
  static const String _rememberKey = 'campushub_remember_login';

  static String _encodeUser(AuthUser user) {
    return jsonEncode({
      'id': user.id,
      'username': user.studentId,
      'email': user.email,
      'first_name': user.firstName,
      'last_name': user.lastName,
      'full_name': user.fullName,
      'role': user.role,
      'user_type': user.userType,
      'program_id': user.programId,
      'major_id': user.majorId,
      'program': user.program,
      'major': user.major,
      'student_id': user.profileStudentId,
      'institutional_id': user.institutionalId,
      'contact_number': user.contactNumber,
      'year_section': user.yearSection,
      'profile_photo_url': user.profilePhotoUrl,
      'profile_completed': user.profileCompleted,
      'email_verified': user.emailVerified,
    });
  }

  /// Save the user after successful login.
  static Future<void> saveUser(
    AuthUser user, {
    String? chatToken,
    bool remember = true,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userKey, _encodeUser(user));
    if (chatToken != null && chatToken.isNotEmpty) {
      await prefs.setString(_chatTokenKey, chatToken);
    } else {
      // A new login must never inherit another account's bearer token.
      await prefs.remove(_chatTokenKey);
    }
    await prefs.setBool(_rememberKey, remember);
    _syncPushSession(user, prefs.getString(_chatTokenKey));
  }

  static Future<String?> loadChatToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_chatTokenKey);
  }

  static Future<void> updateUser(AuthUser user, {String? chatToken}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userKey, _encodeUser(user));
    if (chatToken != null && chatToken.isNotEmpty) {
      await prefs.setString(_chatTokenKey, chatToken);
    }
    _syncPushSession(user, prefs.getString(_chatTokenKey));
  }

  /// Load the user (returns null if not logged in).
  static Future<AuthUser?> loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_userKey);
    if (data == null) return null;
    try {
      final map = jsonDecode(data) as Map<String, dynamic>;
      return AuthUser.fromJson(map);
    } catch (_) {
      return null;
    }
  }

  /// Clear the user session (logout).
  static Future<void> clearUser() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userKey);
    await prefs.remove(_chatTokenKey);
    await prefs.remove(_rememberKey);
    await PushNotificationService.instance.clearSession();
  }

  /// Quick check.
  static Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    final shouldRemember = prefs.getBool(_rememberKey) ?? false;
    if (!shouldRemember) {
      await clearUser();
      return false;
    }
    final user = await loadUser();
    _syncPushSession(user, prefs.getString(_chatTokenKey));
    return user != null;
  }

  static void _syncPushSession(AuthUser? user, String? token) {
    PushNotificationService.instance.setSession(
      user != null && token != null && token.isNotEmpty
          ? PushSession(userId: user.id, token: token)
          : null,
    );
  }
}
