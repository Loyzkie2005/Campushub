import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:campushub/module_app/screens/profile_page.dart';
import 'package:campushub/module_app/screens/seller_application_form.dart';
import 'package:campushub/module_app/screens/seller_application_page.dart';
import 'package:campushub/module_app/services/auth_service.dart';
import 'package:campushub/module_app/services/seller_application_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final userData = <String, dynamic>{
    'id': 1,
    'username': 'ana',
    'student_id': '2026001234',
    'first_name': 'Ana',
    'last_name': 'Student',
    'full_name': 'Ana Student',
    'email': 'ana@example.com',
    'user_type': 'student',
    'role': 'User',
    'contact_number': '09171234567',
    'profile_completed': true,
    'program_id': 1,
    'program': 'BSIT',
  };
  final applicant = {...userData, 'user_id': 1};
  Map<String, dynamic> state(
    String status, [
    Map<String, dynamic>? application,
  ]) => {
    'status': status,
    'is_approved_seller': status == 'approved',
    'applicant': applicant,
    'seller_request': application,
    'categories': ['School Supplies', 'Snacks'],
    'programs': [
      {'id': 1, 'code': 'BSIT', 'name': 'Information Technology'},
    ],
    'majors': [],
    'supporting_document_required': false,
  };
  Map<String, dynamic> saved(String status) => {
    'id': 4,
    'status': status,
    'category': 'Snacks',
    'contact_number': '09171234567',
    'course_section': '2A',
    'message': 'Campus snacks',
    'revision_notes': 'Describe which snacks.',
    'rejection_reason': 'Ineligible category.',
    'application_data': {
      ...applicant,
      'products_intended': 'Baked snacks',
      'confirmations': {'accuracy': true, 'rules': true, 'approval': true},
    },
  };
  setUp(
    () => SharedPreferences.setMockInitialValues({
      'campushub_logged_user': jsonEncode(userData),
      'campushub_chat_token': 'test-login-token',
    }),
  );
  Future<void> tap(WidgetTester tester, String label) async {
    final target = find.text(label).last;
    await tester.ensureVisible(target);
    await tester.pumpAndSettle();
    await tester.tap(target);
    await tester.pumpAndSettle();
  }

  testWidgets(
    'Profile starts an unsubmitted draft and submits only after review and terms',
    (tester) async {
      tester.view.physicalSize = const Size(375, 812);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      var posts = 0;
      var status = 'none';
      final captureKey = GlobalKey();
      final captureDir = Platform.environment['SELLER_REVIEW_DIR'];
      Future<void> capture(String name) async {
        if (captureDir == null) return;
        await tester.pumpAndSettle();
        await tester.runAsync(() async {
          final boundary =
              captureKey.currentContext!.findRenderObject()!
                  as RenderRepaintBoundary;
          final shot = await boundary.toImage(pixelRatio: 2);
          final bytes = await shot.toByteData(format: ui.ImageByteFormat.png);
          Directory(captureDir).createSync(recursive: true);
          File(
            '$captureDir/$name.png',
          ).writeAsBytesSync(bytes!.buffer.asUint8List());
          shot.dispose();
        });
      }

      if (captureDir != null) {
        await tester.runAsync(() async {
          await (FontLoader('Montserrat')..addFont(
                rootBundle.load(
                  'assets/fonts/Montserrat-VariableFont_wght.ttf',
                ),
              ))
              .load();
          await (FontLoader('MaterialIcons')
                ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf')))
              .load();
        });
      }
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            RepaintBoundary(
              key: captureKey,
              child: const MaterialApp(home: Scaffold(body: ProfilePage())),
            ),
          );
          await tester.pumpAndSettle();
          await tap(tester, 'Apply to Sell');
          expect(find.text('Before you apply:'), findsOneWidget);
          await capture('seller-introduction');
          await tap(tester, 'Start Application');
          expect(find.text('Applicant Information'), findsOneWidget);
          expect(find.text('Application not approved'), findsNothing);
          expect(find.text('Rejected'), findsNothing);
          expect(find.text('2026001234'), findsOneWidget);
          await capture('seller-applicant');
          await tester.enterText(
            find.byKey(const ValueKey('seller-Year Level / Section')),
            '2A',
          );
          await tap(tester, 'Continue');
          expect(posts, 0);
          expect(find.text('Selling Information'), findsOneWidget);
          final category = find.byType(DropdownButtonFormField<String>);
          await tester.ensureVisible(category);
          await tester.tap(category);
          await tester.pumpAndSettle();
          await tap(tester, 'Snacks');
          await tester.enterText(
            find.byKey(const ValueKey('seller-Products Intended to Sell *')),
            'Baked snacks',
          );
          await tap(tester, 'Continue');
          await tap(tester, 'Review Application');
          expect(
            find.textContaining('Check all three confirmations'),
            findsOneWidget,
          );
          expect(posts, 0);
          for (final key in ['accuracy', 'rules', 'approval']) {
            final checkbox = find.byKey(ValueKey('seller-term-$key'));
            await tester.ensureVisible(checkbox);
            await tester.tap(checkbox);
            await tester.pumpAndSettle();
          }
          await tap(tester, 'Review Application');
          expect(find.text('Review Application'), findsOneWidget);
          expect(find.text('Baked snacks'), findsOneWidget);
          expect(posts, 0);
          await capture('seller-review');
          await tap(tester, 'Submit Application');
          expect(posts, 1);
          expect(find.text('Application Submitted'), findsOneWidget);
          expect(find.text('Status: Pending Review'), findsOneWidget);
          await capture('seller-submitted');
          await tap(tester, 'View Application');
          expect(find.text('Baked snacks'), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
        () => MockClient((request) async {
          expect(request.headers['Authorization'], 'Bearer test-login-token');
          expect(
            request.url.queryParameters.containsKey('student_id'),
            isFalse,
          );
          if (request.method == 'GET') {
            return http.Response(
              jsonEncode(
                state(status, status == 'none' ? null : saved(status)),
              ),
              200,
            );
          }
          posts++;
          final body = jsonDecode(request.body) as Map;
          expect(body.containsKey('student_id'), isFalse);
          expect(body['category'], 'Snacks');
          expect(body['products_intended'], 'Baked snacks');
          expect(body['confirmations'], {
            'accuracy': true,
            'rules': true,
            'approval': true,
          });
          status = 'pending';
          return http.Response(
            jsonEncode({'seller_request': saved(status)}),
            201,
          );
        }),
      );
    },
  );

  for (final status in [
    'pending',
    'approved',
    'suspended',
    'rejected',
    'needs_revision',
  ]) {
    testWidgets('$status is displayed only from a saved server application', (
      tester,
    ) async {
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            MaterialApp(
              home: SellerApplicationForm(user: AuthUser.fromJson(userData)),
            ),
          );
          await tester.pumpAndSettle();
          expect(find.text('Submit Application'), findsNothing);
          expect(find.byType(TextFormField), findsNothing);
          if (status == 'needs_revision') {
            expect(find.text('Describe which snacks.'), findsOneWidget);
            await tap(tester, 'Edit Application');
            expect(find.text('Applicant Information'), findsOneWidget);
          }
          expect(tester.takeException(), isNull);
        },
        () => MockClient(
          (request) async =>
              http.Response(jsonEncode(state(status, saved(status))), 200),
        ),
      );
    });
  }

  testWidgets('approved Profile has no seller dashboard or application entry', (
    tester,
  ) async {
    await http.runWithClient(
      () async {
        await tester.pumpWidget(
          const MaterialApp(home: Scaffold(body: ProfilePage())),
        );
        await tester.pumpAndSettle();
        expect(
          find.byKey(const ValueKey('profile-apply-to-sell')),
          findsNothing,
        );
        expect(find.text('Seller Dashboard'), findsNothing);
        expect(find.text('Apply to Sell'), findsNothing);
        expect(tester.takeException(), isNull);
      },
      () => MockClient(
        (request) async => http.Response(
          jsonEncode(state('approved', saved('approved'))),
          200,
        ),
      ),
    );
  });

  test('Submission transport failure never retries POST', () async {
    var posts = 0;
    await http.runWithClient(
      () async {
        await expectLater(
          const SellerApplicationService().submit({'category': 'Snacks'}),
          throwsA(isA<SellerApplicationException>()),
        );
        expect(posts, 1);
      },
      () => MockClient((request) async {
        posts++;
        throw http.ClientException('offline');
      }),
    );
  });

  testWidgets(
    'returning to the retained Profile tab refreshes approval status',
    (tester) async {
      final active = ValueNotifier(true);
      addTearDown(active.dispose);
      var status = 'pending';
      var homeRefreshes = 0;
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            MaterialApp(
              home: Scaffold(
                body: ValueListenableBuilder<bool>(
                  valueListenable: active,
                  builder: (_, value, _) => ProfilePage(
                    active: value,
                    onSellerAccessChanged: () async {
                      homeRefreshes++;
                    },
                  ),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(find.text('Pending Review'), findsOneWidget);
          active.value = false;
          await tester.pumpAndSettle();
          status = 'approved';
          active.value = true;
          await tester.pumpAndSettle();
          expect(find.text('Seller Dashboard'), findsNothing);
          expect(find.text('Apply to Sell'), findsNothing);
          expect(homeRefreshes, 1);
          expect(tester.takeException(), isNull);
        },
        () => MockClient(
          (request) async =>
              http.Response(jsonEncode(state(status, saved(status))), 200),
        ),
      );
    },
  );
  testWidgets('failed status does not become a rejected application', (
    tester,
  ) async {
    var reads = 0;
    await http.runWithClient(
      () async {
        await tester.pumpWidget(
          MaterialApp(
            home: SellerApplicationForm(user: AuthUser.fromJson(userData)),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text('Rejected'), findsNothing);
        expect(find.text('Submit Application'), findsNothing);
        await tap(tester, 'Check Application Status');
        expect(find.text('Applicant Information'), findsOneWidget);
        expect(reads, 2);
      },
      () => MockClient((request) async {
        reads++;
        return http.Response(
          jsonEncode(
            reads == 1 ? {'error': 'Unable to load status.'} : state('none'),
          ),
          reads == 1 ? 503 : 200,
        );
      }),
    );
  });

  for (final (size, scale) in [
    (const Size(375, 812), 1.0),
    (const Size(320, 844), 2.0),
    (const Size(844, 390), 1.0),
  ]) {
    testWidgets('Seller introduction and applicant form fit $size/$scale', (
      tester,
    ) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      var starts = 0;
      await tester.pumpWidget(
        MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: SellerApplicationPage(onStart: () => starts++),
        ),
      );
      await tester.pumpAndSettle();
      expect(starts, 0);
      await tap(tester, 'Start Application');
      expect(starts, 1);
      expect(tester.takeException(), isNull);
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            MaterialApp(
              builder: (context, child) => MediaQuery(
                data: MediaQuery.of(
                  context,
                ).copyWith(textScaler: TextScaler.linear(scale)),
                child: child!,
              ),
              home: SellerApplicationForm(user: AuthUser.fromJson(userData)),
            ),
          );
          await tester.pumpAndSettle();
          await tap(tester, 'Continue');
          expect(find.text('Selling Information'), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
        () => MockClient(
          (request) async => http.Response(jsonEncode(state('none')), 200),
        ),
      );
    });
  }
}
