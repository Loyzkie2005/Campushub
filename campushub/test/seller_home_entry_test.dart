import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/screens/home_page.dart';
import 'package:campushub/module_app/screens/seller_dashboard_page.dart';
import 'package:campushub/module_app/screens/seller_application_form.dart';
import 'package:campushub/module_app/services/seller_application_service.dart';
import 'package:campushub/module_app/session/session_service.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'home_test_fixtures.dart';
import 'seller_test_fixtures.dart';

// Only test fixtures; production approval always comes from Django.
class HomeAccessService extends SellerApplicationService {
  String state = 'none';
  bool fail = false, malformed = false;
  int reads = 0;
  @override
  Future<Map<String, dynamic>> status([String? ignoredLegacyId]) async {
    reads++;
    if (fail) throw const SellerApplicationException('Status offline');
    return {
      'status': state,
      if (!malformed) 'is_approved_seller': state == 'approved',
    };
  }

  @override
  Future<Map<String, dynamic>> workspace({
    String period = '30',
    int ordersPage = 1,
  }) async {
    final data = sellerWorkspaceFixture();
    (data['analytics'] as Map)['period'] = period;
    return data;
  }
}

DashboardScreen home(HomeAccessService service, {int initialTab = 0}) =>
    DashboardScreen(
      initialTab: initialTab,
      sellerService: service,
      serviceCatalog: HomeTestCatalog(),
      loadHomeProducts: homeProducts,
      loadHomeFacilities: homeFacilities,
    );

void main() {
  setUp(
    () => SharedPreferences.setMockInitialValues({
      'campushub_logged_user': jsonEncode({
        'id': 1,
        'username': 'test-home',
        'first_name': 'Ana',
        'full_name': 'Ana Test',
        'user_type': 'student',
        'role': 'User',
        'profile_completed': true,
      }),
    }),
  );

  testWidgets(
    'render approved seller additions with the original Home navbar',
    (tester) async {
      final directory = Platform.environment['SELLER_SHARED_HOME_CAPTURE'];
      if (directory == null) return;
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.runAsync(() async {
        final poppins = FontLoader('Poppins');
        for (final face in ['Regular', 'Medium', 'SemiBold', 'Bold']) {
          poppins.addFont(
            rootBundle.load('assets/fonts/poppins/Poppins-$face.ttf'),
          );
        }
        await poppins.load();
        for (final font in {
          'Montserrat': 'assets/fonts/Montserrat-VariableFont_wght.ttf',
          'SugarPie': 'assets/fonts/Sugar-Pie-W00-Regular.ttf',
          'MaterialIcons': 'fonts/MaterialIcons-Regular.otf',
          'packages/iconsax_flutter/FlutterIconsax':
              'packages/iconsax_flutter/fonts/FlutterIconsax.ttf',
        }.entries) {
          await (FontLoader(
            font.key,
          )..addFont(rootBundle.load(font.value))).load();
        }
      });
      final capture = GlobalKey();
      final service = HomeAccessService()..state = 'approved';
      await tester.pumpWidget(
        MaterialApp(
          home: RepaintBoundary(key: capture, child: home(service)),
        ),
      );
      await tester.pumpAndSettle();
      await tester.runAsync(() async {
        final context = tester.element(find.byType(DashboardScreen));
        await precacheImage(
          const AssetImage('assets/img/logo_light.png'),
          context,
        );
        await precacheImage(
          const ResizeImage(
            AssetImage('assets/img/ustp_oroquieta_entrance.png'),
            width: 1280,
          ),
          context,
        );
      });
      await tester.pumpAndSettle();
      Future<void> save(String name) => tester.runAsync(() async {
        final boundary =
            capture.currentContext!.findRenderObject()!
                as RenderRepaintBoundary;
        final rendered = await boundary.toImage(pixelRatio: 2);
        final bytes = await rendered.toByteData(format: ui.ImageByteFormat.png);
        Directory(directory).createSync(recursive: true);
        File(
          '$directory/$name.png',
        ).writeAsBytesSync(bytes!.buffer.asUint8List());
        rendered.dispose();
      });
      await save('shared-home-seller-sections');
      await tester.scrollUntilVisible(
        find.text('Test Chocolate'),
        240,
        scrollable: find
            .descendant(
              of: find.byType(HomePage),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await tester.pumpAndSettle();
      await save('shared-home-marketplace');
      expect(find.byType(FloatingBottomNavbar), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  for (final status in [
    'none',
    'pending',
    'needs_revision',
    'rejected',
    'suspended',
  ]) {
    testWidgets('$status access keeps regular Home and its five tabs', (
      tester,
    ) async {
      final service = HomeAccessService()..state = status;
      await tester.pumpWidget(MaterialApp(home: home(service)));
      await tester.pumpAndSettle();
      expect(find.byType(SellerDashboardPage), findsNothing);
      expect(find.byType(FloatingBottomNavbar), findsOneWidget);
      expect(find.text('Welcome Back, Ana'), findsOneWidget);
      await tester.tap(find.byTooltip('Open menu'));
      await tester.pumpAndSettle();
      expect(find.text('Seller Dashboard'), findsNothing);
      expect(service.reads, 1);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }

  testWidgets(
    'approval and revocation add or remove seller sections on the same Home',
    (tester) async {
      final service = HomeAccessService()..state = 'pending';
      await tester.pumpWidget(MaterialApp(home: home(service)));
      await tester.pumpAndSettle();
      service.state = 'approved';
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pumpAndSettle();
      expect(find.byType(SellerDashboardPage), findsOneWidget);
      expect(find.byTooltip('Open seller menu'), findsNothing);
      expect(find.byTooltip('Open menu'), findsOneWidget);
      expect(find.byType(FloatingBottomNavbar), findsOneWidget);
      expect(find.text('Total Sales'), findsOneWidget);
      expect(find.byKey(const Key('navbar-center-add-button')), findsOneWidget);
      expect((await SessionService.loadUser())!.id, 1);
      service.state = 'suspended';
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pumpAndSettle();
      expect(find.byType(SellerDashboardPage), findsNothing);
      expect(find.byType(FloatingBottomNavbar), findsOneWidget);
      expect(find.byTooltip('Open seller menu'), findsNothing);
      expect(find.byKey(const Key('navbar-center-add-button')), findsNothing);
      expect(find.text('Profile'), findsWidgets);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  testWidgets(
    'approval while viewing an application returns to shared Home with seller sections',
    (tester) async {
      final service = HomeAccessService()..state = 'pending';
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            MaterialApp(home: home(service, initialTab: 4)),
          );
          await tester.pumpAndSettle();
          // Chat initializes without credentials; the existing status HTTP then uses a test token.
          final preferences = await SharedPreferences.getInstance();
          await preferences.setString('campushub_chat_token', 'test-token');
          final entry = find.byKey(const ValueKey('profile-apply-to-sell'));
          await tester.ensureVisible(entry);
          await tester.tap(entry);
          await tester.pumpAndSettle();
          expect(find.byType(SellerApplicationForm), findsOneWidget);
          service.state = 'approved';
          tester.binding.handleAppLifecycleStateChanged(
            AppLifecycleState.inactive,
          );
          tester.binding.handleAppLifecycleStateChanged(
            AppLifecycleState.resumed,
          );
          await tester.pumpAndSettle();
          expect(find.byType(SellerApplicationForm), findsNothing);
          expect(find.byType(SellerDashboardPage), findsOneWidget);
          expect(find.byType(FloatingBottomNavbar), findsOneWidget);
          expect(tester.takeException(), isNull);
          await tester.pumpWidget(const SizedBox.shrink());
        },
        () => MockClient(
          (request) async => http.Response(
            jsonEncode({
              'status': service.state,
              'is_approved_seller': service.state == 'approved',
              'seller_request': {'application_data': {}},
            }),
            200,
          ),
        ),
      );
    },
  );

  testWidgets('failed status is retryable and never grants seller access', (
    tester,
  ) async {
    final service = HomeAccessService()..fail = true;
    await tester.pumpWidget(MaterialApp(home: home(service)));
    await tester.pumpAndSettle();
    expect(find.text('Status offline'), findsOneWidget);
    expect(find.byType(SellerDashboardPage), findsNothing);
    service.fail = false;
    service.state = 'approved';
    await tester.tap(find.text('Status offline'));
    await tester.pumpAndSettle();
    expect(find.byType(SellerDashboardPage), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets('unreadable status allows public browsing but no seller menu', (
    tester,
  ) async {
    final service = HomeAccessService()..malformed = true;
    await tester.pumpWidget(MaterialApp(home: home(service)));
    await tester.pumpAndSettle();
    expect(find.text('Unable to verify seller access. Retry.'), findsOneWidget);
    expect(find.byType(FloatingBottomNavbar), findsOneWidget);
    expect(find.byType(SellerDashboardPage), findsNothing);
    await tester.pumpWidget(const SizedBox.shrink());
  });

  testWidgets(
    'explicit Services entry remains a Services deep link for sellers',
    (tester) async {
      final service = HomeAccessService()..state = 'approved';
      await tester.pumpWidget(MaterialApp(home: home(service, initialTab: 2)));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
            .currentIndex,
        2,
      );
      await tester.tap(find.text('Home').last);
      await tester.pumpAndSettle();
      expect(find.byType(SellerDashboardPage), findsOneWidget);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}
