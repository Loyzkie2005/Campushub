abstract final class PasswordPolicy {
  static const String requirements =
      'Use 8+ characters with uppercase, lowercase, number, and special character.';

  static String? validate(String? rawValue) {
    final value = rawValue ?? '';

    if (value.isEmpty) return 'Please enter a password';
    if (value.length < 8) return 'Use at least 8 characters';
    if (RegExp(r'\s').hasMatch(value)) return 'Password cannot contain spaces';
    if (!RegExp(r'[A-Z]').hasMatch(value)) {
      return 'Add at least one uppercase letter';
    }
    if (!RegExp(r'[a-z]').hasMatch(value)) {
      return 'Add at least one lowercase letter';
    }
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      return 'Add at least one number';
    }
    if (!RegExp(r'[^A-Za-z0-9]').hasMatch(value)) {
      return 'Add at least one special character';
    }

    return null;
  }
}
