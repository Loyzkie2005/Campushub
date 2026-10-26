import 'dart:convert';
import 'package:campushub/module_app/screens/profile_setup_screen.dart';
import 'package:campushub/module_app/services/auth_service.dart';
import 'package:campushub/module_app/session/session_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final masters = {
    'programs': [
      {'id': 1, 'code': 'BSIT', 'name': 'Information Technology'},
      {'id': 2, 'code': 'BTLED', 'name': 'Technology and Livelihood Education'},
    ],
    'majors': [
      {'id': 3, 'program_id': 2, 'code': 'HE', 'name': 'Home Economics'},
    ],
  };
  final savedUser = {
    'id': 1,
    'username': 'student',
    'user_type': 'student',
    'program_id': 2,
    'major_id': 3,
    'program': 'BTLED',
    'major': 'Home Economics',
    'profile_completed': true,
  };

  test(
    'Profile sends real numeric academic identifiers and persists them',
    () async {
      SharedPreferences.setMockInitialValues({});
      await http.runWithClient(
        () async {
          final result = await AuthService.completeProfile(
            token: 'test-token',
            userType: 'student',
            institutionalId: '2026001234',
            contactNumber: '09171234567',
            programId: 2,
            majorId: 3,
          );
          expect(result.success, true);
          await SessionService.updateUser(result.user!);
          final loaded = await SessionService.loadUser();
          expect(loaded!.programId, 2);
          expect(loaded.majorId, 3);
          expect(loaded.major, 'Home Economics');
        },
        () => MockClient((request) async {
          final body = jsonDecode(request.body) as Map<String, dynamic>;
          expect(body['program_id'], 2);
          expect(body['major_id'], 3);
          expect(request.headers['Authorization'], 'Bearer test-token');
          return http.Response(jsonEncode({'user': savedUser}), 200);
        }),
      );
    },
  );

  testWidgets(
    'Student must choose Program and BTLED Major on a phone viewport',
    (tester) async {
      tester.view.physicalSize = const Size(375, 812);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            const MaterialApp(home: ProfileSetupScreen()),
          );
          await tester.pumpAndSettle();
          await tester.tap(find.byType(DropdownButtonFormField<String>));
          await tester.pumpAndSettle();
          await tester.tap(find.text('Student').last);
          await tester.pumpAndSettle();
          await tester.tap(find.text('Next'));
          await tester.pumpAndSettle();
          await tester.enterText(find.byType(TextFormField), '2026001234');
          await tester.tap(find.byType(DropdownButtonFormField<int>).first);
          await tester.pumpAndSettle();
          await tester.tap(find.text('BTLED').last);
          await tester.pumpAndSettle();
          expect(find.byType(DropdownButtonFormField<int>), findsNWidgets(2));
          await tester.ensureVisible(find.text('Next'));
          await tester.tap(find.text('Next'));
          await tester.pumpAndSettle();
          expect(find.text('Select your BTLED major.'), findsOneWidget);
          await tester.ensureVisible(
            find.byType(DropdownButtonFormField<int>).last,
          );
          await tester.tap(find.byType(DropdownButtonFormField<int>).last);
          await tester.pumpAndSettle();
          await tester.tap(find.text('Home Economics').last);
          await tester.pumpAndSettle();
          await tester.ensureVisible(find.text('Next'));
          await tester.tap(find.text('Next'));
          await tester.pumpAndSettle();
          expect(find.text('Enter your phone number'), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
        () => MockClient(
          (request) async => http.Response(jsonEncode(masters), 200),
        ),
      );
    },
  );

  testWidgets('Academic API failure offers Retry instead of fake programs', (
    tester,
  ) async {
    await http.runWithClient(() async {
      await tester.pumpWidget(const MaterialApp(home: ProfileSetupScreen()));
      await tester.pumpAndSettle();
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Student').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('Next'));
      await tester.pumpAndSettle();
      expect(find.text('Retry'), findsOneWidget);
      expect(
        find.text('Unable to load programs. Check your connection and retry.'),
        findsOneWidget,
      );
      expect(find.text('BSIT'), findsNothing);
      expect(tester.takeException(), isNull);
    }, () => MockClient((request) async => http.Response('Unavailable', 503)));
  });
}
