import 'package:campushub/module_app/validation/password_policy.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('accepts a password that satisfies every requirement', () {
    expect(PasswordPolicy.validate('CampusHub1!'), isNull);
  });

  test('rejects passwords missing any required character type', () {
    const weakPasswords = [
      'Short1!',
      'campushub1!',
      'CAMPUSHUB1!',
      'CampusHub!',
      'CampusHub1',
      'Campus Hub1!',
    ];

    for (final password in weakPasswords) {
      expect(
        PasswordPolicy.validate(password),
        isNotNull,
        reason: '$password should be rejected',
      );
    }
  });
}
