import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:campushub/module_app/screens/seller_dashboard_page.dart';
import 'package:campushub/module_app/screens/messages_screen.dart';
import 'package:campushub/module_app/screens/seller_bundle_form.dart';
import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/screens/home_page.dart';
import 'package:campushub/module_app/screens/seller_workspace_content.dart';
import 'package:campushub/module_app/screens/profile_details_pages.dart';
import 'package:campushub/module_app/services/auth_service.dart';
import 'package:campushub/module_app/services/theme_service.dart';
import 'package:campushub/module_app/services/seller_application_service.dart';
import 'package:campushub/module_app/session/session_service.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:campushub/module_app/widgets/navigation/seller_drawer.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'home_test_fixtures.dart';
import 'seller_test_fixtures.dart';

final user = AuthUser.fromJson({
  'id': 1,
  'username': 'test-seller',
  'full_name': 'Test Student Seller',
  'first_name': 'Test',
  'email': 'student.seller@example.edu',
  'program': 'BSIT',
  'year_section': '2-A',
  'user_type': 'student',
  'role': 'User',
  'profile_completed': true,
});

class WorkspaceService extends SellerApplicationService {
  bool approved = true, fail = false;
  int loads = 0;
  String period = '30';
  final data = sellerWorkspaceFixture();
  String? choice;
  @override
  Future<Map<String, dynamic>> status([String? ignoredLegacyId]) async => {
    'is_approved_seller': approved,
  };
  @override
  Future<Map<String, dynamic>> workspace({
    String period = '30',
    int ordersPage = 1,
  }) async {
    loads++;
    if (fail) throw const SellerApplicationException('Workspace offline');
    this.period = period;
    (data['analytics'] as Map)['period'] = period;
    return data;
  }

  Map<String, dynamic>? lastProduct;
  @override
  Future<Map<String, dynamic>> createProduct(
    Map<String, dynamic> fields,
  ) async {
    lastProduct = fields;
    final row = {
      'id': 9,
      'name': fields['name'],
      'price': fields['price'],
      'category': fields['category'],
      'product_type': 'bundle',
      'approval_status': 'pending',
    };
    data['bundle_submissions'] = [row];
    (data['products'] as List).add(row);
    return {'product': row};
  }

  @override
  Future<void> suggestionChoice(String pairId, String action) async {
    choice = '$pairId:$action';
    if (action == 'save') data['saved_suggestions'] = [sellerPairFixture()];
    if (action == 'remove') {
      data['saved_suggestions'] = <Map<String, dynamic>>[];
    }
    if (action == 'dismiss') {
      (data['recommendations'] as Map)['rows'] = <Map<String, dynamic>>[];
    }
  }
}

Future<void> menu(WidgetTester tester, String label) async {
  await tester.tap(find.byTooltip('Open seller menu'));
  await tester.pumpAndSettle();
  final item = find.descendant(
    of: find.byType(SellerDrawer),
    matching: find.text(label),
  );
  await tester.scrollUntilVisible(
    item,
    150,
    scrollable: find
        .descendant(
          of: find.byType(SellerDrawer),
          matching: find.byType(Scrollable),
        )
        .first,
  );
  await Scrollable.ensureVisible(tester.element(item), alignment: .5);
  await tester.pumpAndSettle();
  await tester.tap(item);
  await tester.pumpAndSettle();
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  testWidgets(
    'capture seller overview and drawer when SELLER_REVIEW_DIR is provided',
    (tester) async {
      final directory = Platform.environment['SELLER_REVIEW_DIR'];
      if (directory == null) return;
      tester.view.physicalSize = const Size(375, 812);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.runAsync(() async {
        final poppins = FontLoader('Poppins');
        for (final face in [
          'Regular',
          'Medium',
          'SemiBold',
          'Bold',
          'ExtraBold',
          'Black',
        ]) {
          poppins.addFont(
            rootBundle.load('assets/fonts/poppins/Poppins-$face.ttf'),
          );
        }
        await poppins.load();
        await (FontLoader('packages/iconsax_flutter/FlutterIconsax')..addFont(
              rootBundle.load(
                'packages/iconsax_flutter/fonts/FlutterIconsax.ttf',
              ),
            ))
            .load();
        await (FontLoader('packages/lucide_icons/Lucide')..addFont(
              rootBundle.load('packages/lucide_icons/assets/lucide.ttf'),
            ))
            .load();
        await (FontLoader('Montserrat')..addFont(
              rootBundle.load('assets/fonts/Montserrat-VariableFont_wght.ttf'),
            ))
            .load();
        await (FontLoader(
          'MaterialIcons',
        )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
        await (FontLoader('SugarPie')..addFont(
              rootBundle.load('assets/fonts/Sugar-Pie-W00-Regular.ttf'),
            ))
            .load();
      });
      await ThemeService.instance.setLightMode(true);
      final capture = GlobalKey();
      final service = WorkspaceService();
      await tester.pumpWidget(
        MaterialApp(
          home: RepaintBoundary(
            key: capture,
            child: SellerDashboardPage(
              user: user,
              service: service,
              onMessages: () {},
              onNotifications: () {},
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.runAsync(
        () => precacheImage(
          const AssetImage('assets/img/logo_light.png'),
          tester.element(find.byType(SellerDashboardPage)),
        ),
      );
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
      await save('seller-overview');
      await tester.scrollUntilVisible(find.text('Recent Orders'), 200);
      await tester.pumpAndSettle();
      await save('seller-overview-bottom');
      await tester.tap(find.byTooltip('Open seller menu'));
      await tester.pumpAndSettle();
      await save('seller-drawer-top');
      await tester.scrollUntilVisible(
        find.text('Account Settings'),
        120,
        scrollable: find
            .descendant(
              of: find.byType(SellerDrawer),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await Scrollable.ensureVisible(
        tester.element(find.text('Account Settings')),
        alignment: .5,
      );
      await tester.pumpAndSettle();
      await save('seller-drawer-bottom');
      tester.state<ScaffoldState>(find.byType(Scaffold)).closeDrawer();
      await tester.pumpAndSettle();
      await menu(tester, 'My Products');
      await save('seller-my-products');
      await tester.tap(find.byTooltip('Search my products'));
      await tester.pumpAndSettle();
      await save('seller-my-products-search');
      await tester.tap(find.byTooltip('Close search'));
      await tester.pumpAndSettle();
      (service.data['products'] as List).clear();
      await menu(tester, 'Inventory');
      await menu(tester, 'My Products');
      await save('seller-my-products-empty');
      expect(tester.takeException(), isNull);
    },
  );
  test(
    'seller workspace transport keeps bearer auth and never retries writes',
    () async {
      SharedPreferences.setMockInitialValues({
        'campushub_chat_token': 'test-token',
      });
      var posts = 0;
      await http.runWithClient(
        () async {
          final service = SellerApplicationService();
          await service.workspace(period: '7', ordersPage: 2);
          await service.suggestionChoice('1|2', 'save');
          expect(posts, 1);
        },
        () => MockClient((request) async {
          expect(request.headers['authorization'], 'Bearer test-token');
          if (request.method == 'POST') {
            posts++;
            expect(jsonDecode(request.body), {'action': 'save'});
            return http.Response('{"message":"Saved"}', 200);
          }
          expect(request.url.path, '/api/mobile/seller/workspace/');
          expect(request.url.queryParameters, {
            'period': '7',
            'orders_page': '2',
          });
          return http.Response(jsonEncode(sellerWorkspaceFixture()), 200);
        }),
      );
      await http.runWithClient(
        () async {
          await expectLater(
            SellerApplicationService().workspace(),
            throwsA(
              isA<SellerApplicationException>().having(
                (error) => error.statusCode,
                'status',
                403,
              ),
            ),
          );
        },
        () => MockClient(
          (_) async =>
              http.Response('{"error":"Seller access suspended"}', 403),
        ),
      );
    },
  );
  testWidgets(
    'branded seller header and six home sections preserve actions and See All',
    (tester) async {
      var messages = 0, notifications = 0, searches = 0;
      await tester.pumpWidget(
        MaterialApp(
          home: SellerDashboardPage(
            user: user,
            service: WorkspaceService(),
            onSearch: () => searches++,
            onMessages: () => messages++,
            onNotifications: () => notifications++,
          ),
        ),
      );
      await tester.pumpAndSettle();
      final appBar = tester.widget<AppBar>(find.byType(AppBar));
      expect(appBar.backgroundColor, Colors.white);
      expect(appBar.foregroundColor, const Color(0xFF1A1851));
      expect(find.byKey(const ValueKey('seller-brand-logo')), findsOneWidget);
      expect(find.byKey(const ValueKey('seller-brand-name')), findsOneWidget);
      expect(
        tester
            .widget<Text>(find.byKey(const ValueKey('seller-brand-name')))
            .style
            ?.fontFamily,
        'SugarPie',
      );
      expect(find.byTooltip('Messages'), findsNothing);
      expect(
        tester.getCenter(find.byTooltip('Search')).dx,
        lessThan(tester.getCenter(find.byTooltip('Notifications')).dx),
      );
      expect(find.byTooltip('Open Profile'), findsNothing);
      await tester.tap(find.byTooltip('Search'));
      expect(searches, 1);
      await menu(tester, 'Messages');
      await tester.tap(find.byTooltip('Notifications'));
      expect(messages, 0);
      expect(find.byType(MessagesPage), findsOneWidget);
      expect(find.byKey(const ValueKey('seller-brand-name')), findsOneWidget);
      expect(find.byType(Scaffold), findsOneWidget);
      await menu(tester, 'Dashboard');
      expect(notifications, 1);
      for (final section in [
        'Sales Overview',
        'Suggested Product Bundles',
        'Sales Trend',
        'Inventory Attention',
        'Recent Orders',
      ]) {
        await tester.scrollUntilVisible(find.text(section), 200);
        expect(find.text(section), findsOneWidget);
        expect(tester.takeException(), isNull);
      }
      final section = find.byKey(
        const ValueKey('seller-section-recommendations'),
      );
      await tester.scrollUntilVisible(section, -200);
      await Scrollable.ensureVisible(tester.element(section), alignment: .5);
      await tester.pumpAndSettle();
      await tester.tap(
        find.descendant(of: section, matching: find.text('See All >')),
      );
      await tester.pumpAndSettle();
      expect(find.text('Suggested Product Bundles'), findsOneWidget);
      expect(
        find.byKey(const ValueKey('seller-section-recommendations')),
        findsNothing,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'all seller sections keep a white shell and the same branded header',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark(),
          home: SellerDashboardPage(user: user, service: WorkspaceService()),
        ),
      );
      await tester.pumpAndSettle();
      final shell = tester.state(find.byType(Scaffold));
      for (final destination in SellerDrawer.drawerDestinations) {
        await menu(tester, destination.label);
        expect(tester.state(find.byType(Scaffold)), same(shell));
        expect(
          tester.widget<Scaffold>(find.byType(Scaffold)).backgroundColor,
          Colors.white,
        );
        expect(find.byKey(const ValueKey('seller-brand-name')), findsOneWidget);
        expect(find.byType(AppBar), findsOneWidget);
        expect(find.byTooltip('Notifications'), findsOneWidget);
        expect(find.byTooltip('Open Profile'), findsNothing);
        expect(
          find.byTooltip(
            destination == SellerDestination.products
                ? 'Search my products'
                : 'Search',
          ),
          findsOneWidget,
        );
        expect(tester.takeException(), isNull);
      }
    },
  );

  for (final size in [const Size(320, 812), const Size(844, 390)]) {
    testWidgets('seller branded header and zero sales fit $size at 2x text', (
      tester,
    ) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final service = WorkspaceService();
      (service.data['analytics'] as Map)['trend'] = {
        'labels': ['Oct 18'],
        'sales': [0],
      };
      await tester.pumpWidget(
        MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(2),
              disableAnimations: true,
            ),
            child: child!,
          ),
          home: SellerDashboardPage(user: user, service: service),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('seller-brand-name')), findsOneWidget);
      await tester.scrollUntilVisible(find.text('Sales Trend'), 250);
      await tester.pumpAndSettle();
      expect(
        find.text('No completed paid sales in this period.'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'seller sections use real workspace shape and Add Product belongs only to products',
    (tester) async {
      final service = WorkspaceService();
      await tester.pumpWidget(
        MaterialApp(
          home: SellerDashboardPage(user: user, service: service),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Suggested Product Bundles'), findsOneWidget);
      expect(find.text('Add Product'), findsNothing);
      expect(find.byType(FloatingBottomNavbar), findsNothing);
      await menu(tester, 'My Products');
      expect(find.text('Add'), findsOneWidget);
      expect(find.text('Test Notebook'), findsOneWidget);
      await menu(tester, 'Inventory');
      expect(find.text('Large · SKU: TST-L-001'), findsOneWidget);
      expect(find.text('On Hand'), findsOneWidget);
      expect(find.text('Reserved'), findsOneWidget);
      await menu(tester, 'My Bundles');
      expect(find.text('Test Bundle'), findsOneWidget);
      expect(find.text('Derived Availability'), findsOneWidget);
      expect(find.text('Add Product'), findsNothing);
      await menu(tester, 'Orders');
      expect(find.text('TEST-ORDER'), findsOneWidget);
      await tester.tap(find.text('TEST-ORDER'));
      await tester.pumpAndSettle();
      expect(find.text('Cash on Pickup'), findsOneWidget);
      await tester.pageBack();
      await tester.pumpAndSettle();
      expect(service.loads, 1);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'My Products search is local, collapsible and preserves status/type filters',
    (tester) async {
      final service = WorkspaceService();
      final products = service.data['products'] as List;
      (products[1] as Map)['approval_status'] = 'pending';
      (products[2] as Map)['is_archived'] = true;
      var globalSearches = 0;
      await tester.pumpWidget(
        MaterialApp(
          home: SellerDashboardPage(
            user: user,
            service: service,
            initialDestination: SellerDestination.products,
            onSearch: () => globalSearches++,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(TextField), findsNothing);
      expect(find.byKey(const ValueKey('seller-product-1')), findsOneWidget);
      final headerTop = tester.getTopLeft(find.text('My Products')).dy;
      await tester.tap(find.byTooltip('Search my products'));
      await tester.pumpAndSettle();
      final search = find.widgetWithText(TextField, 'Search my products');
      expect(tester.widget<TextField>(search).autofocus, isTrue);
      await tester.enterText(search, 'Notebook');
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('seller-product-1')), findsOneWidget);
      expect(find.byKey(const ValueKey('seller-product-2')), findsNothing);
      expect(globalSearches, 0);
      expect(service.loads, 1);
      await tester.tap(find.byTooltip('Close search'));
      await tester.pumpAndSettle();
      expect(find.byType(TextField), findsNothing);
      expect(find.byKey(const ValueKey('seller-product-2')), findsOneWidget);
      expect(tester.getTopLeft(find.text('My Products')).dy, headerTop);
      Future<void> filter(String label) async {
        final chip = find.widgetWithText(ChoiceChip, label);
        await tester.ensureVisible(chip);
        await tester.pumpAndSettle();
        await tester.tap(chip);
        await tester.pumpAndSettle();
      }

      await filter('Bundles');
      expect(find.byKey(const ValueKey('seller-product-3')), findsOneWidget);
      expect(find.byKey(const ValueKey('seller-product-1')), findsNothing);
      await filter('Single');
      expect(find.byKey(const ValueKey('seller-product-3')), findsNothing);
      await filter('Pending');
      expect(find.byKey(const ValueKey('seller-product-2')), findsOneWidget);
      expect(find.byKey(const ValueKey('seller-product-1')), findsNothing);
      await filter('Approved');
      expect(find.byKey(const ValueKey('seller-product-1')), findsOneWidget);
      expect(find.byKey(const ValueKey('seller-product-3')), findsNothing);
      await filter('Rejected');
      expect(find.text('No matching products'), findsOneWidget);
      await tester.tap(find.text('Clear search and filters'));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('seller-product-1')), findsOneWidget);
      await filter('Archived');
      expect(find.byKey(const ValueKey('seller-product-3')), findsOneWidget);
      await tester.tap(find.byTooltip('Product actions'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('View Details'));
      await tester.pumpAndSettle();
      expect(find.text('Approval Status'), findsOneWidget);
      expect(find.text('Bundle Components'), findsOneWidget);
      await tester.pageBack();
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('Product actions'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('View Inventory'));
      await tester.pumpAndSettle();
      expect(find.text('On Hand'), findsOneWidget);
      expect(service.loads, 1);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'empty My Products keeps working Add menu callbacks without sample records',
    (tester) async {
      var singles = 0;
      final destinations = <SellerDestination>[];
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SellerWorkspaceContent(
              destination: SellerDestination.products,
              data: sellerWorkspaceFixture(products: []),
              onNavigate: destinations.add,
              onAddProduct: () => singles++,
              onCreateBundle: (_) {},
              onReload: () {},
              onPeriod: (_) {},
              onOrdersPage: (_) {},
              sellerFirstName: '',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.textContaining('No products yet.'), findsOneWidget);
      expect(find.byType(TextField), findsNothing);
      await tester.tap(find.byKey(const ValueKey('seller-add-product')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Add Single Product'));
      await tester.pumpAndSettle();
      expect(singles, 1);
      await tester.tap(find.byKey(const ValueKey('seller-add-product')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Create Bundle Product'));
      await tester.pumpAndSettle();
      expect(destinations, [SellerDestination.recommendations]);
      expect(find.textContaining('No products yet.'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  for (final (size, scale) in [
    (const Size(320, 812), 2.0),
    (const Size(844, 390), 2.0),
  ]) {
    testWidgets('My Products fixed header and search fit $size at ${scale}x', (
      tester,
    ) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: SellerDashboardPage(
            user: user,
            service: WorkspaceService(),
            initialDestination: SellerDestination.products,
          ),
        ),
      );
      await tester.pumpAndSettle();
      final headingTop = tester.getTopLeft(find.text('My Products')).dy;
      await tester.tap(find.byTooltip('Search my products'));
      await tester.pumpAndSettle();
      expect(
        find.widgetWithText(TextField, 'Search my products'),
        findsOneWidget,
      );
      await tester.drag(
        find.byKey(const PageStorageKey('seller-products')),
        const Offset(0, -180),
      );
      await tester.pumpAndSettle();
      expect(tester.getTopLeft(find.text('My Products')).dy, headingTop);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'qualifying pair opens existing Product workflow and shows actual review status',
    (tester) async {
      final service = WorkspaceService();
      await tester.pumpWidget(
        MaterialApp(
          home: SellerDashboardPage(user: user, service: service),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Welcome back, Test!'), findsOneWidget);
      for (final label in [
        'Total Sales',
        'Total Orders',
        'Completed Orders',
        'Pending Orders',
      ]) {
        expect(find.text(label), findsOneWidget);
      }
      expect(find.byIcon(Iconsax.wallet_2_copy), findsOneWidget);
      expect(find.byIcon(Iconsax.bag_2_copy), findsOneWidget);
      expect(find.byIcon(Iconsax.tick_circle_copy), findsOneWidget);
      expect(find.byIcon(Iconsax.clock_copy), findsOneWidget);
      await menu(tester, 'Suggested Product Bundles');
      for (final label in ['Support', 'Confidence', 'Lift', 'SYNTHETIC']) {
        expect(find.text(label), findsNothing);
      }
      await tester.tap(find.text('View Suggestion'));
      await tester.pumpAndSettle();
      expect(find.text('Bundle Suggestion'), findsOneWidget);
      await tester.pageBack();
      await tester.pumpAndSettle();
      await tester.tap(find.text('Create Bundle'));
      await tester.pumpAndSettle();
      expect(find.byType(SellerBundleForm), findsOneWidget);
      expect(find.text('Stock Quantity'), findsNothing);
      final bundleScroll = find
          .descendant(
            of: find.byType(SellerBundleForm),
            matching: find.byType(Scrollable),
          )
          .first;
      await tester.scrollUntilVisible(
        find.text('Submit for Review'),
        150,
        scrollable: bundleScroll,
      );
      await Scrollable.ensureVisible(
        tester.element(find.text('Submit for Review')),
        alignment: .5,
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Submit for Review'));
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.widgetWithText(TextFormField, 'Bundle Price (₱)'),
        -150,
        scrollable: bundleScroll,
      );
      await tester.pumpAndSettle();
      expect(
        find.text('Enter a valid price with at most two decimal places.'),
        findsOneWidget,
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Bundle Price (₱)'),
        '25',
      );
      tester.testTextInput.hide();
      await tester.pumpAndSettle();
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('School Supplies').last);
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Submit for Review'),
        150,
        scrollable: bundleScroll,
      );
      await Scrollable.ensureVisible(
        tester.element(find.text('Submit for Review')),
        alignment: .5,
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Submit for Review'));
      await tester.pumpAndSettle();
      expect(service.lastProduct?['product_type'], 'bundle');
      expect(service.lastProduct?['stock'], isNull);
      expect(find.text('My Bundles'), findsOneWidget);
      expect(find.textContaining('Pending Review'), findsWidgets);
      expect(find.text('My Bundle Suggestions'), findsNothing);
      expect(tester.takeException(), isNull);
      await menu(tester, 'Sales Analytics');
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Weekly').last);
      await tester.pumpAndSettle();
      expect(service.period, '7');
      await menu(tester, 'Account Settings');
      expect(find.byType(AccountSecurityPage), findsOneWidget);
      expect(find.byType(Scaffold), findsOneWidget);
      expect(find.byKey(const ValueKey('seller-brand-name')), findsOneWidget);
    },
  );

  testWidgets(
    'unapproved seller cannot open navigation; transient failure retries; revocation hides drawer',
    (tester) async {
      final service = WorkspaceService()..approved = false;
      await tester.pumpWidget(
        MaterialApp(
          home: SellerDashboardPage(user: user, service: service),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byTooltip('Open seller menu'), findsNothing);
      expect(find.byType(SellerDrawer), findsNothing);
      expect(service.loads, 0);
      service.approved = true;
      service.fail = true;
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();
      expect(find.text('Workspace offline'), findsOneWidget);
      service.fail = false;
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();
      expect(find.text('Suggested Product Bundles'), findsOneWidget);
      service.approved = false;
      await tester.drag(find.byType(ListView).first, const Offset(0, 300));
      await tester.pumpAndSettle();
      expect(find.byTooltip('Open seller menu'), findsNothing);
      expect(
        find.text('Approved active seller access is required.'),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    'seller additions share Home and navbar; existing tools return without hiding catalogs',
    (tester) async {
      final service = WorkspaceService();
      SharedPreferences.setMockInitialValues({
        'campushub_logged_user': jsonEncode({
          'id': 1,
          'username': 'test-seller',
          'first_name': 'Ana',
          'full_name': 'Ana Seller',
          'user_type': 'student',
          'role': 'User',
          'profile_completed': true,
        }),
      });
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            MaterialApp(
              home: DashboardScreen(
                sellerService: service,
                serviceCatalog: HomeTestCatalog(),
                loadHomeProducts: homeProducts,
                loadHomeFacilities: homeFacilities,
              ),
            ),
          );
          await tester.pumpAndSettle();
          // Keep this navigation test isolated from ChatService's WebSocket.
          final preferences = await SharedPreferences.getInstance();
          await preferences.setString('campushub_chat_token', 'test-token');
          expect(find.byType(FloatingBottomNavbar), findsOneWidget);
          expect(find.byTooltip('Open menu'), findsOneWidget);
          expect(find.byTooltip('Open seller menu'), findsNothing);
          expect(find.text('Sales Overview'), findsOneWidget);
          expect(find.textContaining('Total Sales ·'), findsNothing);
          expect(find.byType(DropdownButtonFormField<String>), findsNothing);
          final previousLoads = service.loads;
          await tester.tap(find.byTooltip('Filter sales period'));
          await tester.pumpAndSettle();
          expect(
            tester
                .widget<CheckedPopupMenuItem<String>>(
                  find.widgetWithText(CheckedPopupMenuItem<String>, 'Weekly'),
                )
                .checked,
            isTrue,
          );
          await tester.tap(
            find.widgetWithText(CheckedPopupMenuItem<String>, 'Daily'),
          );
          await tester.pumpAndSettle();
          expect(service.period, 'day');
          expect(service.loads, previousLoads + 1);
          await tester.tap(find.byTooltip('Filter sales period'));
          await tester.pumpAndSettle();
          expect(
            tester
                .widget<CheckedPopupMenuItem<String>>(
                  find.widgetWithText(CheckedPopupMenuItem<String>, 'Daily'),
                )
                .checked,
            isTrue,
          );
          await tester.tap(
            find.widgetWithText(CheckedPopupMenuItem<String>, 'Monthly'),
          );
          await tester.pumpAndSettle();
          expect(service.period, 'month');
          expect(find.byType(FloatingBottomNavbar), findsOneWidget);
          await tester.tap(find.byKey(const Key('navbar-center-add-button')));
          await tester.pumpAndSettle();
          expect(find.text('Product Information'), findsOneWidget);
          expect(find.byType(FloatingBottomNavbar), findsNothing);
          await tester.tap(find.byType(BackButton));
          await tester.pumpAndSettle();
          expect(
            tester
                .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
                .currentIndex,
            0,
          );
          await tester.tap(find.byKey(const ValueKey('navbar-item-2')));
          await tester.pumpAndSettle();
          expect(
            tester
                .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
                .currentIndex,
            2,
          );
          await tester.tap(find.byKey(const ValueKey('navbar-item-3')));
          await tester.pumpAndSettle();
          expect(
            tester
                .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
                .currentIndex,
            3,
          );
          await tester.tap(find.byKey(const ValueKey('navbar-item-0')));
          await tester.pumpAndSettle();
          expect(find.byKey(const ValueKey('home-search')), findsNothing);
          expect(find.byTooltip('Search'), findsOneWidget);
          await tester.tap(find.byTooltip('Open menu'));
          await tester.pumpAndSettle();
          expect(find.byType(SellerDrawer), findsOneWidget);
          expect(
            find.descendant(
              of: find.byType(SellerDrawer),
              matching: find.text('Marketplace'),
            ),
            findsNothing,
          );
          expect(
            find.descendant(
              of: find.byType(SellerDrawer),
              matching: find.text('Facilities Booking'),
            ),
            findsNothing,
          );
          expect(
            find.descendant(
              of: find.byType(SellerDrawer),
              matching: find.text('My Cart'),
            ),
            findsNothing,
          );
          final productTool = find.descendant(
            of: find.byType(Drawer),
            matching: find.text('My Products'),
          );
          await tester.scrollUntilVisible(
            productTool,
            180,
            scrollable: find
                .descendant(
                  of: find.byType(Drawer),
                  matching: find.byType(Scrollable),
                )
                .first,
          );
          await tester.tap(productTool);
          await tester.pumpAndSettle();
          expect(find.text('Add'), findsOneWidget);
          // Profile remains reachable through the drawer avatar, not the header.
          await tester.tap(find.byTooltip('Open seller menu'));
          await tester.pumpAndSettle();
          await tester.ensureVisible(
            find.byKey(const ValueKey('seller-profile-avatar')),
          );
          await tester.pumpAndSettle();
          await tester.tap(find.byTooltip('Open Profile'));
          await tester.pumpAndSettle();
          expect(
            tester
                .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
                .currentIndex,
            4,
          );
          expect(find.byTooltip('Open seller menu'), findsNothing);
          tester
              .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
              .onTap(0);
          await tester.pumpAndSettle();
          await tester.tap(find.byTooltip('Open menu'));
          await tester.pumpAndSettle();
          await tester.tap(find.text('My Products'));
          await tester.pumpAndSettle();
          await tester.tap(find.byTooltip('Open seller menu'));
          await tester.pumpAndSettle();
          final back = find.descendant(
            of: find.byType(SellerDrawer),
            matching: find.text('Dashboard'),
          );
          await tester.scrollUntilVisible(
            back,
            -160,
            scrollable: find
                .descendant(
                  of: find.byType(SellerDrawer),
                  matching: find.byType(Scrollable),
                )
                .first,
          );
          await Scrollable.ensureVisible(tester.element(back), alignment: .5);
          await tester.pumpAndSettle();
          await tester.tap(back);
          await tester.pumpAndSettle();
          expect(find.byTooltip('Open seller menu'), findsNothing);
          final nav = tester.widget<FloatingBottomNavbar>(
            find.byType(FloatingBottomNavbar),
          );
          expect(nav.currentIndex, 0);
          expect(nav.effectiveItems.map((item) => item.label), [
            'Home',
            'Marketplace',
            'Services',
            'Facilities',
          ]);
          expect((await SessionService.loadUser())!.id, 1);
          expect(find.text('Welcome Back, Ana'), findsOneWidget);
          await tester.tap(find.byTooltip('Open menu'));
          await tester.pumpAndSettle();
          await tester.ensureVisible(
            find.byKey(const ValueKey('seller-profile-avatar')),
          );
          await tester.pumpAndSettle();
          await tester.tap(find.byTooltip('Open Profile'));
          await tester.pumpAndSettle();
          expect(
            find.byKey(const ValueKey('profile-apply-to-sell')),
            findsNothing,
          );
          expect(find.text('Seller Dashboard'), findsNothing);
          tester
              .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
              .onTap(0);
          await tester.pumpAndSettle();
          expect(find.byType(FloatingBottomNavbar), findsOneWidget);
          expect(find.byTooltip('Open menu'), findsOneWidget);
          expect(find.text('Sales Overview'), findsOneWidget);
          // Mount the lazy catalog section, then let its FutureBuilder resolve.
          await tester.scrollUntilVisible(
            find.descendant(
              of: find.byType(HomePage),
              matching: find.text('Marketplace'),
            ),
            240,
            scrollable: find
                .descendant(
                  of: find.byType(HomePage),
                  matching: find.byType(Scrollable),
                )
                .first,
          );
          await tester.pumpAndSettle();
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
          expect(find.text('Test Chocolate'), findsWidgets);
          expect(find.byType(FloatingBottomNavbar), findsOneWidget);

          expect(tester.takeException(), isNull);
        },
        () => MockClient(
          (request) async => http.Response(
            jsonEncode(
              request.url.path.contains('/workspace/')
                  ? sellerWorkspaceFixture()
                  : request.url.path.contains('/access-status/')
                  ? {'status': 'approved', 'is_approved_seller': true}
                  : {'products': [], 'facilities': []},
            ),
            200,
          ),
        ),
      );
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    },
  );
}
