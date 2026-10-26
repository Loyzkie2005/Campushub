import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:campushub/module_app/models/product_item.dart';
import 'package:campushub/module_app/screens/search_page.dart';
import 'package:campushub/module_app/screens/product_details_screen.dart';
import 'package:campushub/module_app/services/facility_service.dart';
import 'package:campushub/module_app/widgets/home/home_preview_cards.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'home_test_fixtures.dart';

Future<List<ProductItem>> noRecommendations() async => [];

Future<void> openSearch(
  WidgetTester tester, {
  Future<List<ProductItem>> Function() products = homeProducts,
  Future<List<ProductItem>> Function() recommendations = noRecommendations,
  Future<FacilityServiceResult> Function() facilities = homeFacilities,
  HomeTestCatalog? catalog,
  double scale = 1,
  Brightness brightness = Brightness.light,
}) async {
  if (Platform.environment['SEARCH_REVIEW_DIR'] != null) {
    await tester.runAsync(() async {
      // Widget tests otherwise use the square Ahem test font. Register the real
      // bundled typeface under the test/default and Google Fonts variant names.
      for (final family in [
        'Ahem',
        'Montserrat',
        'Montserrat_regular',
        'Montserrat_500',
        'Montserrat_600',
        'Montserrat_700',
      ]) {
        await (FontLoader(family)..addFont(
              rootBundle.load('assets/fonts/Montserrat-VariableFont_wght.ttf'),
            ))
            .load();
      }
      await (FontLoader(
        'MaterialIcons',
      )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
    });
  }
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
      home: RepaintBoundary(
        key: const ValueKey('search-review'),
        child: SearchPage(
          loadProducts: products,
          loadFacilities: facilities,
          loadRecommendations: recommendations,
          catalog: catalog ?? HomeTestCatalog(),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> captureSearch(WidgetTester tester, String name) async {
  final directory = Platform.environment['SEARCH_REVIEW_DIR'];
  if (directory == null) return;
  await tester.pumpAndSettle();
  await tester.runAsync(() async {
    final boundary = tester.renderObject<RenderRepaintBoundary>(
      find.byKey(const ValueKey('search-review')),
    );
    final image = await boundary.toImage(pixelRatio: 2);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    Directory(directory).createSync(recursive: true);
    File('$directory/$name.png').writeAsBytesSync(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  final input = find.byKey(const ValueKey('catalog-search-input'));

  testWidgets(
    'discovery is honest, recent ordering uses saved submission date',
    (tester) async {
      await openSearch(
        tester,
        products: () async => [
          ProductItem.fromJson({
            'id': 1,
            'name': 'Older product',
            'submitted_at': '2026-10-01T00:00:00Z',
          }),
          ProductItem.fromJson({
            'id': 2,
            'name': 'New product',
            'submitted_at': '2026-10-18T00:00:00Z',
          }),
        ],
      );
      expect(
        tester.widget<Scaffold>(find.byType(Scaffold).first).backgroundColor,
        Colors.white,
      );
      expect(tester.widget<TextField>(input).focusNode!.hasFocus, isTrue);
      expect(find.text('Recently Added Products'), findsOneWidget);
      expect(find.text('Recommended for You'), findsNothing);
      expect(find.text('Popular Searches'), findsNothing);
      final cards = tester.widgetList<MarketplacePreviewCard>(
        find.byType(MarketplacePreviewCard),
      );
      expect(cards.first.product.name, 'New product');
      await tester.scrollUntilVisible(
        find.text('Explore Available Products'),
        180,
        scrollable: find
            .descendant(
              of: find.byType(ListView).first,
              matching: find.byType(Scrollable),
            )
            .first,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'only history results that still exist in public catalog are personalized',
    (tester) async {
      final product = ProductItem.fromJson({
        'id': 9,
        'name': 'Real eligible product',
      });
      await openSearch(
        tester,
        products: () async => [product],
        recommendations: () async => [
          ProductItem.fromJson({
            'id': 999,
            'name': 'Stale unavailable product',
          }),
          product,
        ],
      );
      expect(find.text('Recommended for You'), findsOneWidget);
      expect(find.text('Stale unavailable product'), findsNothing);
      expect(find.text('Recently Added Products'), findsNothing);
    },
  );

  testWidgets(
    'typing gives query suggestions, submit searches all catalogs without refetch',
    (tester) async {
      var calls = 0;
      final catalog = HomeTestCatalog();
      await openSearch(
        tester,
        products: () {
          calls++;
          return homeProducts();
        },
        catalog: catalog,
      );
      await tester.enterText(input, 'choc');
      await tester.pumpAndSettle();
      expect(find.text('Search Suggestions'), findsOneWidget);
      expect(find.text('Test Chocolate'), findsOneWidget);
      expect(find.text('Test Notebook'), findsNothing);
      expect(find.text('Recently Added Products'), findsNothing);
      await tester.enterText(input, 'Test');
      await tester.testTextInput.receiveAction(TextInputAction.search);
      await tester.pumpAndSettle();
      expect(find.text('Search Results'), findsOneWidget);
      await tester.tap(find.widgetWithText(ChoiceChip, 'Facilities'));
      await tester.pumpAndSettle();
      expect(find.text('Test Covered Court'), findsOneWidget);
      expect(find.text('Test Chocolate'), findsNothing);
      await tester.tap(find.widgetWithText(ChoiceChip, 'Services'));
      await tester.pumpAndSettle();
      expect(find.text('Test Laboratory'), findsOneWidget);
      await tester.tap(find.text('Test Laboratory'));
      await tester.pumpAndSettle();
      expect(find.text('Service Details'), findsOneWidget);
      expect(find.text('How to Request This Service'), findsOneWidget);
      expect(calls, 1);
      expect(catalog.calls, 1);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'suggestion opens existing product details and clearing restores discovery',
    (tester) async {
      await openSearch(tester);
      await tester.enterText(input, 'Chocolate');
      await tester.pumpAndSettle();
      await tester.tap(find.text('Test Chocolate'));
      await tester.pumpAndSettle();
      expect(find.byType(ProductDetailsScreen), findsOneWidget);
      Navigator.of(tester.element(find.byType(ProductDetailsScreen))).pop();
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('Clear search'));
      await tester.pumpAndSettle();
      expect(find.text('Recently Added Products'), findsOneWidget);
      expect(tester.widget<TextField>(input).focusNode!.hasFocus, isTrue);
    },
  );

  testWidgets('loading, failure, retry and no results remain distinct', (
    tester,
  ) async {
    final pending = Completer<List<ProductItem>>();
    var calls = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: SearchPage(
          loadProducts: () {
            calls++;
            return calls == 1 ? pending.future : homeProducts();
          },
          loadFacilities: homeFacilities,
          catalog: HomeTestCatalog(),
          loadRecommendations: noRecommendations,
        ),
      ),
    );
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    pending.completeError(StateError('offline'));
    await tester.pumpAndSettle();
    expect(
      find.text('Unable to load products. Check your connection and retry.'),
      findsOneWidget,
    );
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('Recently Added Products'), findsOneWidget);
    await tester.enterText(input, 'no matching item');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ChoiceChip, 'Products'));
    await tester.pumpAndSettle();
    expect(
      find.text('No matching products. Try another name or category.'),
      findsOneWidget,
    );
    expect(calls, 2);
    expect(tester.takeException(), isNull);
  });

  testWidgets('catalog failures remain independent from product results', (
    tester,
  ) async {
    final catalog = HomeTestCatalog()..fail = true;
    await openSearch(
      tester,
      catalog: catalog,
      facilities: () async => const FacilityServiceResult(success: false),
    );
    await tester.enterText(input, 'Test');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ChoiceChip, 'Facilities'));
    await tester.pumpAndSettle();
    expect(
      find.text('Unable to load facilities. Check your connection and retry.'),
      findsOneWidget,
    );
    await tester.tap(find.widgetWithText(ChoiceChip, 'Services'));
    await tester.pumpAndSettle();
    expect(
      find.text('Unable to load services. Check your connection and retry.'),
      findsOneWidget,
    );
    await tester.tap(find.widgetWithText(ChoiceChip, 'Products'));
    await tester.pumpAndSettle();
    expect(find.text('Test Chocolate'), findsOneWidget);
  });

  for (final (size, scale, brightness) in [
    (const Size(375, 812), 1.0, Brightness.light),
    (const Size(320, 844), 2.0, Brightness.dark),
    (const Size(844, 390), 2.0, Brightness.dark),
  ]) {
    testWidgets('search fits $size at text scale $scale', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await openSearch(tester, scale: scale, brightness: brightness);
      await captureSearch(tester, '${size.width.toInt()}-discovery');
      await tester.scrollUntilVisible(
        find.text('Explore Available Products'),
        180,
        scrollable: find
            .descendant(
              of: find.byType(ListView).first,
              matching: find.byType(Scrollable),
            )
            .first,
      );
      expect(tester.takeException(), isNull);
      await tester.enterText(input, 'Test');
      await tester.pumpAndSettle();
      await captureSearch(tester, '${size.width.toInt()}-suggestions');
      await tester.testTextInput.receiveAction(TextInputAction.search);
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Test Laboratory'),
        150,
        scrollable: find
            .descendant(
              of: find.byType(ListView).first,
              matching: find.byType(Scrollable),
            )
            .first,
      );
      expect(tester.takeException(), isNull);
    });
  }
}
