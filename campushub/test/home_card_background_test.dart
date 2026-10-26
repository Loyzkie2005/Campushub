import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/screens/home_page.dart';
import 'package:campushub/module_app/widgets/home/home_preview_cards.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'home_test_fixtures.dart';

void main() {
  for (final width in [360.0, 390.0]) {
    testWidgets(
      'Home catalog cards and navigation remain usable at width $width',
      (tester) async {
        SharedPreferences.setMockInitialValues({});
        tester.view.physicalSize = Size(width, 844);
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
        expect(find.byKey(const ValueKey('home-search')), findsNothing);
        expect(find.text('Test Chocolate'), findsWidgets);
        expect(
          find.byKey(const ValueKey('home-card-campus-image')),
          findsNothing,
        );
        final marketplace = find.byType(HomeSectionHeader).first;
        await tester.tap(
          find.descendant(of: marketplace, matching: find.text('See All')),
        );
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
              .currentIndex,
          1,
        );
        await tester.tap(find.text('Home').last);
        await tester.pumpAndSettle();
        expect(find.byType(HomePage), findsOneWidget);
        expect(find.byType(FloatingBottomNavbar), findsOneWidget);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
      },
    );
  }
}
