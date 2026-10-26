import 'dart:async';
import 'package:campushub/module_app/models/product_item.dart';
import 'package:campushub/module_app/screens/home_page.dart';
import 'package:campushub/module_app/screens/search_page.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:campushub/module_app/services/facility_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'home_test_fixtures.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  for (final (size, scale, brightness) in [
    (const Size(375, 812), 1.0, Brightness.light),
    (const Size(320, 844), 2.0, Brightness.dark),
    (const Size(844, 390), 1.0, Brightness.light),
  ]) {
    testWidgets(
      'Home sections preserve loaded data without duplicate search at $size/$scale',
      (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final catalog = HomeTestCatalog()..rows = [];
        var productCalls = 0;
        var facilityCalls = 0;
        await tester.pumpWidget(
          MaterialApp(
            theme: ThemeData(brightness: brightness),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(
                textScaler: TextScaler.linear(scale),
                disableAnimations: true,
              ),
              child: child!,
            ),
            home: Scaffold(
              body: HomePage(
                firstName: 'Ana',
                onMarketplace: () {},
                onFacilities: () {},
                onServices: () {},
                onRefresh: () async {},
                catalog: catalog,
                loadProducts: () {
                  productCalls++;
                  return homeProducts();
                },
                loadFacilities: () async {
                  facilityCalls++;
                  return const FacilityServiceResult(success: true);
                },
                productBuilder: (product) => Text(product.name),
              ),
            ),
          ),
        );
        await tester.pumpAndSettle();
        final banner = find.byKey(const ValueKey('home-campus-banners'));
        expect(banner, findsOneWidget);
        expect(
          tester.getTopLeft(banner).dy,
          greaterThan(tester.getBottomLeft(find.text('Welcome Back, Ana')).dy),
        );
        expect(find.byKey(const ValueKey('home-search')), findsNothing);
        expect(find.byKey(const ValueKey('home-filter-button')), findsNothing);
        expect(find.byTooltip('Filter Home'), findsNothing);
        expect(find.text('Marketplace'), findsOneWidget);
        expect(find.text('Test Chocolate'), findsOneWidget);
        expect(find.text('Test Notebook'), findsOneWidget);
        await tester.scrollUntilVisible(
          find.text('Facilities'),
          180,
          scrollable: find
              .descendant(
                of: find.byKey(const PageStorageKey('home-scroll')),
                matching: find.byType(Scrollable),
              )
              .first,
        );
        expect(find.text('Facilities'), findsOneWidget);
        await tester.scrollUntilVisible(
          find.text('Services'),
          180,
          scrollable: find
              .descendant(
                of: find.byKey(const PageStorageKey('home-scroll')),
                matching: find.byType(Scrollable),
              )
              .first,
        );
        expect(find.text('Services'), findsOneWidget);
        expect(productCalls, 1);
        expect(facilityCalls, 1);
        expect(catalog.calls, 1);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets(
    'Home opens focused dedicated search and reuses loaded catalogs',
    (tester) async {
      final catalog = HomeTestCatalog();
      var calls = 0;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HomePage(
              firstName: 'User',
              onMarketplace: () {},
              onFacilities: () {},
              onServices: () {},
              onRefresh: () async {},
              catalog: catalog,
              loadProducts: () {
                calls++;
                return homeProducts();
              },
              loadFacilities: homeFacilities,
              productBuilder: (row) => Text(row.name),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      tester.state<HomePageState>(find.byType(HomePage)).openSearch();
      await tester.pumpAndSettle();
      expect(find.byType(SearchPage), findsOneWidget);
      final input = find.byKey(const ValueKey('catalog-search-input'));
      expect(tester.widget<TextField>(input).focusNode!.hasFocus, isTrue);
      await tester.enterText(input, 'Chocolate');
      await tester.pumpAndSettle();
      expect(find.text('Test Chocolate'), findsOneWidget);
      expect(find.text('Test Notebook'), findsNothing);
      expect(calls, 1);
      expect(catalog.calls, 1);
      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();
      expect(find.byType(SearchPage), findsNothing);
      expect(find.text('Test Notebook'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('loading, catalog failure and empty results remain distinct', (
    tester,
  ) async {
    final catalog = HomeTestCatalog()..rows = [];
    final pending = Completer<List<ProductItem>>();
    var fail = true;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: HomePage(
            firstName: '',
            onMarketplace: () {},
            onFacilities: () {},
            onServices: () {},
            onRefresh: () async {},
            catalog: catalog,
            loadProducts: () => pending.future,
            loadFacilities: () async => FacilityServiceResult(success: !fail),
            productBuilder: (row) => Text(row.name),
          ),
        ),
      ),
    );
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    pending.complete([]);
    await tester.pumpAndSettle();
    expect(
      find.text('No marketplace products are available right now.'),
      findsOneWidget,
    );
    expect(find.text('Unable to load facilities.'), findsOneWidget);
    expect(find.text('No facilities are currently available.'), findsNothing);
    fail = false;
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('No facilities are currently available.'), findsOneWidget);
    await tester.ensureVisible(
      find.text('No services are currently available.'),
    );
    expect(tester.takeException(), isNull);
  });
}
