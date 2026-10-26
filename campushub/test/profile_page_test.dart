import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:campushub/module_app/routes/app_routes.dart';
import 'package:campushub/module_app/screens/profile_page.dart';
import 'package:campushub/module_app/screens/profile_setup_screen.dart';
import 'package:campushub/module_app/screens/components/account_recovery_dialog.dart';
import 'package:campushub/module_app/session/session_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

final user = <String, dynamic>{
  'id': 1,
  'username': '2026001234',
  'student_id': '2026001234',
  'first_name': 'Ana',
  'last_name': 'Student',
  'full_name': 'Ana Student',
  'email': 'ana@example.test',
  'user_type': 'student',
  'role': 'User',
  'program_id': 1,
  'program': 'BSIT',
  'profile_completed': true,
  'contact_number': '09171234567',
  'email_verified': true,
  'year_section': '2-A',
};
final masters = {
  'programs': [
    {'id': 1, 'code': 'BSIT', 'name': 'Information Technology'},
  ],
  'majors': [],
};
http.Client client() => MockClient((request) async {
  expect(request.method, 'GET');
  return http.Response(
    jsonEncode(
      request.url.path.contains('academic-options')
          ? masters
          : {
              'status': 'none',
              'seller_request': null,
              'is_approved_seller': false,
            },
    ),
    200,
  );
});

Future<void> tap(WidgetTester tester, String label) async {
  final finder = find.text(label).last;
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  setUp(
    () => SharedPreferences.setMockInitialValues({
      'campushub_logged_user': jsonEncode(user),
      'campushub_chat_token': 'test-token',
    }),
  );

  testWidgets(
    'identity is concise, groups are complete and detail fields stay in Personal Information',
    (tester) async {
      await http.runWithClient(() async {
        await tester.pumpWidget(
          const MaterialApp(home: Scaffold(body: ProfilePage())),
        );
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<ColoredBox>(
                find
                    .descendant(
                      of: find.byType(ProfilePage),
                      matching: find.byType(ColoredBox),
                    )
                    .first,
              )
              .color,
          Colors.white,
        );
        for (final title in [
          'ACCOUNT',
          'SHOPPING & SELLING',
          'COMMUNICATION',
          'SETTINGS & PRIVACY',
          'HELP & SUPPORT',
        ]) {
          expect(find.text(title), findsOneWidget);
        }
        expect(find.text('Student'), findsOneWidget);
        expect(find.text('Edit Profile'), findsNothing);
        expect(find.byTooltip('Change profile picture'), findsOneWidget);
        expect(find.text('BSIT'), findsOneWidget);
        expect(
          tester.widget<Text>(find.text('Ana Student')).style?.fontFamily,
          'Montserrat',
        );
        expect(
          tester.widget<Text>(find.text('BSIT')).style?.fontFamily,
          'Montserrat',
        );
        expect(
          tester
              .widget<Text>(find.byKey(const ValueKey('profile-year-section')))
              .style
              ?.fontFamily,
          'Montserrat',
        );
        expect(
          tester
              .widget<Text>(find.text('Personal Information'))
              .style
              ?.fontFamily,
          'Poppins',
        );
        expect(find.text('Student · BSIT'), findsNothing);
        expect(
          tester.getTopLeft(find.byKey(const ValueKey('profile-program'))).dy,
          greaterThan(
            tester
                .getBottomLeft(
                  find.byKey(const ValueKey('profile-account-type')),
                )
                .dy,
          ),
        );
        expect(
          tester
              .getTopLeft(find.byKey(const ValueKey('profile-year-section')))
              .dy,
          greaterThan(
            tester
                .getBottomLeft(find.byKey(const ValueKey('profile-program')))
                .dy,
          ),
        );
        expect(find.text('Student ID'), findsNothing);
        expect(find.text('Facilities'), findsNothing);
        expect(find.text('Order History'), findsNothing);
        await tap(tester, 'Personal Information');
        expect(find.text('Student ID'), findsOneWidget);
        expect(
          tester.widget<Scaffold>(find.byType(Scaffold).last).backgroundColor ??
              Theme.of(
                tester.element(find.byType(Scaffold).last),
              ).scaffoldBackgroundColor,
          Colors.white,
        );
        expect(find.text('2026001234'), findsNWidgets(2));
        expect(find.text('Contact Number'), findsOneWidget);
        expect(tester.takeException(), isNull);
      }, client);
    },
  );

  testWidgets(
    'Edit Profile preloads real academic fields and Back preserves login',
    (tester) async {
      await http.runWithClient(() async {
        await tester.pumpWidget(
          const MaterialApp(home: Scaffold(body: ProfilePage())),
        );
        await tester.pumpAndSettle();
        await tap(tester, 'Personal Information');
        await tester.scrollUntilVisible(
          find.text('Edit Profile'),
          300,
          scrollable: find
              .descendant(
                of: find.byType(ListView).last,
                matching: find.byType(Scrollable),
              )
              .first,
        );
        await tap(tester, 'Edit Profile');
        expect(find.byType(ProfileSetupScreen), findsOneWidget);
        expect(find.text('2026001234'), findsOneWidget);
        expect(find.text('BSIT'), findsOneWidget);
        expect(tester.takeException(), isNull);
        await tester.tap(find.byTooltip('Back'));
        await tester.pumpAndSettle();
        await tester.pageBack();
        await tester.pumpAndSettle();
        expect((await SessionService.loadUser())!.id, 1);
        expect(find.text('Ana Student'), findsOneWidget);
      }, client);
    },
  );

  testWidgets(
    'editing saves through existing profile API and returns to Profile',
    (tester) async {
      var posts = 0;
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            const MaterialApp(home: Scaffold(body: ProfilePage())),
          );
          await tester.pumpAndSettle();
          await tap(tester, 'Personal Information');
          await tester.scrollUntilVisible(
            find.text('Edit Profile'),
            300,
            scrollable: find
                .descendant(
                  of: find.byType(ListView).last,
                  matching: find.byType(Scrollable),
                )
                .first,
          );
          await tap(tester, 'Edit Profile');
          await tap(tester, 'Next');
          await tester.enterText(
            find.byType(TextFormField).first,
            '09991234567',
          );
          await tester.enterText(
            find.byKey(const ValueKey('profile-year-section-input')),
            '3-B',
          );
          await tap(tester, 'Save Changes');
          expect(posts, 1);
          expect(find.byType(ProfileSetupScreen), findsNothing);
          await tester.pageBack();
          await tester.pumpAndSettle();
          expect(
            (await SessionService.loadUser())!.contactNumber,
            '09991234567',
          );
          expect(await SessionService.loadChatToken(), 'renewed-token');
          expect((await SessionService.loadUser())!.yearSection, '3-B');
          expect(find.text('Year / Section: 3-B'), findsOneWidget);
          expect(find.text('Ana Student'), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
        () => MockClient((request) async {
          if (request.method == 'POST') {
            posts++;
            expect(request.url.path, '/api/mobile/profile/complete/');
            expect(request.headers['Authorization'], 'Bearer test-token');
            expect((jsonDecode(request.body) as Map)['program_id'], 1);
            expect((jsonDecode(request.body) as Map)['year_section'], '3-B');
            return http.Response(
              jsonEncode({
                'user': {
                  ...user,
                  'contact_number': '09991234567',
                  'year_section': '3-B',
                },
                'chat_token': 'renewed-token',
              }),
              200,
            );
          }
          return http.Response(
            jsonEncode(
              request.url.path.contains('academic-options')
                  ? masters
                  : {
                      'status': 'none',
                      'seller_request': null,
                      'is_approved_seller': false,
                    },
            ),
            200,
          );
        }),
      );
    },
  );

  testWidgets(
    'My Orders reuses saved order history and security opens existing owner recovery',
    (tester) async {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
        'campushub_order_history',
        jsonEncode([
          {
            'product_name': 'Saved notebook',
            'quantity': 2,
            'total_price': '50.00',
          },
        ]),
      );
      await http.runWithClient(() async {
        await tester.pumpWidget(
          const MaterialApp(home: Scaffold(body: ProfilePage())),
        );
        await tester.pumpAndSettle();
        await tap(tester, 'My Orders');
        expect(find.text('Saved notebook'), findsOneWidget);
        expect(find.text('₱50.00'), findsOneWidget);
        await tester.pageBack();
        await tester.pumpAndSettle();
        await tap(tester, 'Account & Security');
        expect(find.text('Email verified'), findsOneWidget);
        await tap(tester, 'Reset Password');
        expect(find.byType(AccountRecoveryDialog), findsOneWidget);
        expect(tester.takeException(), isNull);
      }, client);
    },
  );

  testWidgets('Communication reuses callbacks without fabricated badges', (
    tester,
  ) async {
    var messages = 0, notifications = 0;
    await http.runWithClient(() async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProfilePage(
              onMessages: () => messages++,
              onNotifications: () => notifications++,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tap(tester, 'Messages');
      await tap(tester, 'Notifications');
      expect(messages, 1);
      expect(notifications, 1);
      expect(find.text('99+'), findsNothing);
    }, client);
  });

  testWidgets(
    'settings saves existing theme preference and unsupported policies stay honest',
    (tester) async {
      await http.runWithClient(() async {
        await tester.pumpWidget(
          const MaterialApp(home: Scaffold(body: ProfilePage())),
        );
        await tester.pumpAndSettle();
        await tap(tester, 'App Settings');
        final before = tester
            .widget<SwitchListTile>(find.byType(SwitchListTile))
            .value;
        await tester.tap(find.byType(SwitchListTile));
        await tester.pumpAndSettle();
        expect(
          (await SharedPreferences.getInstance()).getBool(
            'campushub_light_theme',
          ),
          !before,
        );
        await tester.pageBack();
        await tester.pumpAndSettle();
        await tap(tester, 'Terms & Conditions');
        expect(
          find.text(
            'The official Terms and Conditions are not available in the mobile app yet.',
          ),
          findsOneWidget,
        );
      }, client);
    },
  );

  testWidgets(
    'problem report validates and copies locally, without a submit API',
    (tester) async {
      String? copied;
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform,
        (call) async {
          if (call.method == 'Clipboard.setData') {
            copied = (call.arguments as Map)['text'] as String;
          }
          return null;
        },
      );
      addTearDown(
        () => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
          SystemChannels.platform,
          null,
        ),
      );
      await http.runWithClient(() async {
        await tester.pumpWidget(
          const MaterialApp(home: Scaffold(body: ProfilePage())),
        );
        await tester.pumpAndSettle();
        await tap(tester, 'Report a Problem');
        await tap(tester, 'Copy Report');
        expect(find.text('Select a category.'), findsOneWidget);
        await tester.tap(find.byType(DropdownButtonFormField<String>));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Account').last);
        await tester.pumpAndSettle();
        await tester.enterText(
          find.byType(TextFormField),
          'Cannot update my contact number.',
        );
        await tap(tester, 'Copy Report');
        expect(copied, contains('Cannot update my contact number.'));
        expect(find.text('Report submitted'), findsNothing);
        expect(tester.takeException(), isNull);
      }, client);
    },
  );

  testWidgets(
    'Log Out Cancel preserves session, confirmation clears session and opens login',
    (tester) async {
      await http.runWithClient(() async {
        await tester.pumpWidget(
          MaterialApp(
            home: const Scaffold(body: ProfilePage()),
            routes: {
              AppRoutes.login: (_) =>
                  const Scaffold(body: Text('Login destination')),
            },
          ),
        );
        await tester.pumpAndSettle();
        await tap(tester, 'Log Out');
        await tap(tester, 'Cancel');
        expect(await SessionService.loadChatToken(), 'test-token');
        await tap(tester, 'Log Out');
        await tester.tap(find.widgetWithText(FilledButton, 'Log Out'));
        await tester.pumpAndSettle();
        expect(await SessionService.loadUser(), isNull);
        expect(await SessionService.loadChatToken(), isNull);
        expect(find.text('Login destination'), findsOneWidget);
      }, client);
    },
  );

  for (final config in [
    (const Size(320, 812), 2.0),
    (const Size(375, 812), 1.0),
    (const Size(844, 390), 1.0),
    (const Size(768, 1024), 1.5),
  ]) {
    testWidgets(
      'Profile fits ${config.$1} at ${config.$2} with reduced motion and dark host',
      (tester) async {
        tester.view.physicalSize = config.$1;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(
          'campushub_logged_user',
          jsonEncode({
            ...user,
            'full_name': 'Ana Maria Student With A Long Family Name',
            'email': 'long.student.email.address@example.test',
          }),
        );
        await http.runWithClient(() async {
          await tester.pumpWidget(
            MaterialApp(
              theme: ThemeData.dark(),
              builder: (context, child) => MediaQuery(
                data: MediaQuery.of(context).copyWith(
                  textScaler: TextScaler.linear(config.$2),
                  disableAnimations: true,
                ),
                child: child!,
              ),
              home: const Scaffold(body: ProfilePage()),
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          await tester.ensureVisible(find.text('Log Out'));
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
        }, client);
      },
    );
  }

  testWidgets(
    'capture actual Profile widgets when PROFILE_REVIEW_DIR is provided',
    (tester) async {
      final dir = Platform.environment['PROFILE_REVIEW_DIR'];
      if (dir == null) return;
      tester.view.physicalSize = const Size(375, 812);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.runAsync(() async {
        await (FontLoader('Montserrat')..addFont(
              rootBundle.load('assets/fonts/Montserrat-VariableFont_wght.ttf'),
            ))
            .load();
        await (FontLoader(
          'MaterialIcons',
        )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
        await (FontLoader('Poppins')..addFont(
              rootBundle.load('assets/fonts/poppins/Poppins-Regular.ttf'),
            ))
            .load();
      });
      final key = GlobalKey();
      Future<void> capture(String name) async {
        await tester.pumpAndSettle();
        await tester.runAsync(() async {
          final shot =
              await (key.currentContext!.findRenderObject()!
                      as RenderRepaintBoundary)
                  .toImage(pixelRatio: 2);
          final data = await shot.toByteData(format: ui.ImageByteFormat.png);
          Directory(dir).createSync(recursive: true);
          File('$dir/$name.png').writeAsBytesSync(data!.buffer.asUint8List());
          shot.dispose();
        });
      }

      await http.runWithClient(() async {
        await tester.pumpWidget(
          RepaintBoundary(
            key: key,
            child: const MaterialApp(home: Scaffold(body: ProfilePage())),
          ),
        );
        await capture('profile-top');
        await tester.ensureVisible(find.text('Log Out'));
        await capture('profile-bottom');
      }, client);
    },
  );
}
