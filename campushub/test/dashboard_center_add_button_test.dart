import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets(
    'Dashboard has white circle with navy + in navbar, removes messages from appbar, and moves messages to sidebar',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      const screenWidth = 390.0;
      const screenHeight = 844.0;
      tester.view.physicalSize = const Size(screenWidth, screenHeight);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(const MaterialApp(home: DashboardScreen()));
      await tester.pumpAndSettle();

      final centerButtonFinder = find.byKey(
        const Key('navbar-center-add-button'),
      );
      expect(centerButtonFinder, findsOneWidget);

      final navbarPillFinder = find.byKey(const Key('floating-navbar-pill'));
      expect(navbarPillFinder, findsOneWidget);

      final centerButtonRect = tester.getRect(centerButtonFinder);
      final navbarRect = tester.getRect(navbarPillFinder);

      expect(navbarRect.contains(centerButtonRect.center), isTrue);

      expect(centerButtonRect.center.dx, closeTo(screenWidth / 2, 2.0));

      final circleFinder = find.byKey(const Key('navbar-center-add-circle'));
      expect(circleFinder, findsOneWidget);
      final container = tester.widget<Container>(circleFinder);
      final decoration = container.decoration as BoxDecoration;
      expect(decoration.color, Colors.white);

      final icon = tester.widget<Icon>(
        find.descendant(
          of: centerButtonFinder,
          matching: find.byIcon(LucideIcons.plus),
        ),
      );
      expect(icon.color, const Color(0xFF1A1851));

      const navLabels = ['Home', 'Marketplace', 'Facilities', 'Profile'];
      for (final label in navLabels) {
        expect(
          find.descendant(of: navbarPillFinder, matching: find.text(label)),
          findsOneWidget,
        );
      }
      for (var i = 0; i < 4; i++) {
        expect(find.byKey(ValueKey('navbar-item-$i')), findsOneWidget);
      }

      expect(find.text('Want to sell on campus?'), findsNothing);
      expect(
        find.text('Request seller access for marketplace approval.'),
        findsNothing,
      );

      expect(find.byType(AppBar), findsNothing);
      expect(
        find.byKey(const ValueKey('dashboard-brand-logo')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('dashboard-brand-name')),
        findsOneWidget,
      );
      expect(find.text('Welcome Back'), findsOneWidget);
      expect(
        find.descendant(
          of: find.byKey(const ValueKey('dashboard-brand-header')),
          matching: find.textContaining('Welcome Back'),
        ),
        findsNothing,
      );
      expect(find.byTooltip('Messages'), findsNothing);

      await tester.tap(find.byKey(const ValueKey('navbar-item-1')));
      await tester.pump(const Duration(milliseconds: 350));
      expect(find.byType(AppBar), findsNothing);
      expect(
        find.byKey(const ValueKey('dashboard-brand-name')),
        findsOneWidget,
      );

      await tester.tap(centerButtonFinder);
      await tester.pumpAndSettle();

      expect(find.text('Add Product'), findsOneWidget);
      expect(
        find.text('Submit a new product for marketplace approval.'),
        findsOneWidget,
      );

      await tester.tap(find.byIcon(Icons.close));
      await tester.pumpAndSettle();

      expect(
        find.text('Submit a new product for marketplace approval.'),
        findsNothing,
      );

      await tester.tap(find.byTooltip('Menu'));
      await tester.pumpAndSettle();

      final drawerMessagesTile = find.descendant(
        of: find.byType(Drawer),
        matching: find.text('Messages'),
      );
      expect(drawerMessagesTile, findsOneWidget);

      await tester.tap(drawerMessagesTile);
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 350));

      expect(find.text('Messages'), findsWidgets);
      expect(find.byTooltip('Back'), findsOneWidget);

      await tester.tap(find.byTooltip('Back'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 350));
      expect(centerButtonFinder, findsOneWidget);
    },
  );
}
