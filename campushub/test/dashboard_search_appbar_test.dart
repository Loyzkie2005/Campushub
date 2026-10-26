import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'home_test_fixtures.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  testWidgets(
    'drawer routes to existing tabs and dedicated search returns to Home',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(
            serviceCatalog: HomeTestCatalog(),
            loadHomeProducts: homeProducts,
            loadHomeFacilities: homeFacilities,
          ),
        ),
      );
      await tester.pumpAndSettle();
      // The nested banner may swipe; the outer bottom-navigation tabs may not.
      final tabs = find.byType(PageView).first;
      await tester.drag(tabs, const Offset(-300, 0));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
            .currentIndex,
        0,
      );
      expect(find.byTooltip('Search'), findsOneWidget);
      expect(find.byTooltip('Open Profile'), findsNothing);
      await tester.tap(find.byKey(const ValueKey('navbar-item-2')));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
            .currentIndex,
        2,
      );
      await tester.drag(tabs, const Offset(-300, 0));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
            .currentIndex,
        2,
      );
      await tester.tap(find.byKey(const ValueKey('navbar-item-0')));
      await tester.pumpAndSettle();
      final search = find.byTooltip('Search');
      await tester.tap(search);
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const ValueKey('catalog-search-input')),
        'Chocolate',
      );
      await tester.pumpAndSettle();
      expect(find.text('Test Chocolate'), findsOneWidget);
      expect(find.text('Test Notebook'), findsNothing);
      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();
      for (final item in {
        'Services': 2,
        'Facilities Booking': 3,
        'Marketplace': 1,
        'Profile & Account': 4,
        'Home': 0,
      }.entries) {
        await tester.tap(find.byTooltip('Open menu'));
        await tester.pumpAndSettle();
        final drawer = find.byType(Drawer);
        await tester.tap(
          find.descendant(of: drawer, matching: find.text(item.key)),
        );
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
              .currentIndex,
          item.value,
        );
        await tester.drag(tabs, const Offset(300, 0));
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
              .currentIndex,
          item.value,
        );
        expect(tester.takeException(), isNull);
      }
      expect(find.byTooltip('Search'), findsOneWidget);
      expect(find.byKey(const ValueKey('home-search')), findsNothing);
      expect(find.text('Test Notebook'), findsOneWidget);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  testWidgets('header search works before Home has been visited', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    var productCalls = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: DashboardScreen(
          initialTab: 2,
          serviceCatalog: HomeTestCatalog(),
          loadHomeProducts: () {
            productCalls++;
            return homeProducts();
          },
          loadHomeFacilities: homeFacilities,
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(productCalls, 0);
    await tester.tap(find.byTooltip('Search'));
    await tester.pumpAndSettle();
    final input = find.byKey(const ValueKey('catalog-search-input'));
    expect(tester.widget<TextField>(input).focusNode!.hasFocus, isTrue);
    await tester.enterText(input, 'Chocolate');
    await tester.pumpAndSettle();
    expect(find.text('Test Chocolate'), findsOneWidget);
    expect(productCalls, 1);
    await tester.tap(find.byType(BackButton));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
          .currentIndex,
      2,
    );
    expect(tester.takeException(), isNull);
  });
}
