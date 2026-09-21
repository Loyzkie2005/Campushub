/// CampusHub — Dart scripting: call Django password-reset API.
///
/// Usage:
///   dart run call_password_reset_api.dart user@school.edu
///
/// Tries local Django servers (same hosts as the Flutter app).
library;

import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

const _bases = [
  'http://127.0.0.1:8000/api/mobile',
  'http://localhost:8000/api/mobile',
  'http://10.0.2.2:8000/api/mobile',
];

Future<void> main(List<String> args) async {
  if (args.isEmpty) {
    stderr.writeln('Usage: dart run call_password_reset_api.dart <email>');
    exit(1);
  }

  final email = args.first.trim();
  final body = jsonEncode({'email': email});

  for (final base in _bases) {
    try {
      final uri = Uri.parse('$base/password-reset/');
      final response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: body,
      );

      stdout.writeln('POST $uri → ${response.statusCode}');
      stdout.writeln(response.body);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        exit(0);
      }
    } catch (e) {
      stderr.writeln('$base failed: $e');
    }
  }

  stderr.writeln('All servers failed. Start Django: python manage.py runserver 0.0.0.0:8000');
  exit(2);
}
