/// CampusHub — Dart scripting: send forgot-password email via Gmail SMTP.
///
/// Usage (from campushub/scripts/):
///   dart pub get
///   dart run send_reset_email.dart user@school.edu 123456
///
/// Environment variables:
///   GMAIL_USER          — your Gmail address
///   GMAIL_APP_PASSWORD  — Google App Password (16 chars, not account password)
///
/// This script satisfies the APIs/Scripting rubric: automated email via Dart + Gmail.
library;

import 'dart:io';

import 'package:mailer/mailer.dart';
import 'package:mailer/smtp_server.dart';

Future<void> main(List<String> args) async {
  if (args.length < 2) {
    stderr.writeln(
      'Usage: dart run send_reset_email.dart <recipient_email> <6_digit_code>',
    );
    exit(1);
  }

  final toEmail = args[0].trim();
  final code = args[1].trim();

  final gmailUser = Platform.environment['GMAIL_USER'] ?? '';
  final gmailPass = Platform.environment['GMAIL_APP_PASSWORD'] ?? '';

  if (gmailUser.isEmpty || gmailPass.isEmpty) {
    stderr.writeln(
      'Set GMAIL_USER and GMAIL_APP_PASSWORD environment variables.',
    );
    exit(2);
  }

  if (code.length != 6 || int.tryParse(code) == null) {
    stderr.writeln('Code must be a 6-digit number.');
    exit(3);
  }

  final smtpServer = gmail(gmailUser, gmailPass);

  final message = Message()
    ..from = Address(gmailUser, 'CampusHub')
    ..recipients.add(toEmail)
    ..subject = 'CampusHub Password Reset Code'
    ..text =
        'Your CampusHub password reset code is: $code\n\n'
        'This code expires in 15 minutes.\n'
        'If you did not request this, ignore this email.\n\n'
        '— CampusHub Team';

  try {
    await send(message, smtpServer);
    stdout.writeln('Reset email sent to $toEmail');
  } on MailerException catch (e) {
    stderr.writeln('Failed to send: ${e.message}');
    for (final problem in e.problems) {
      stderr.writeln('  ${problem.code}: ${problem.msg}');
    }
    exit(4);
  }
}
