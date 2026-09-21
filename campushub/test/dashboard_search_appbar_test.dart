import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/widgets/cart_icon_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lucide_icons/lucide_icons.dart';

void main() {
  testWidgets(
    'DashboardScreen swaps search and notification icons and shows back arrow in search mode',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        const MaterialApp(
          home: DashboardScreen(),
        ),
      );

      // Verify CartIconButton is NOT present on the screen
      expect(find.byType(CartIconButton), findsNothing);

      // Verify Notification icon and Search icon are present
      expect(find.byIcon(LucideIcons.search), findsOneWidget);
      expect(find.byIcon(LucideIcons.bell), findsOneWidget);

      // Verify Search icon is placed before Notification icon (swapped order)
      final searchOffset = tester.getTopLeft(find.byTooltip('Search'));
      final notifOffset = tester.getTopLeft(find.byTooltip('Notifications'));
      expect(searchOffset.dx, lessThan(notifOffset.dx));

      // Verify search text field and back arrow are NOT visible initially
      expect(find.byType(TextField), findsNothing);
      expect(find.byIcon(LucideIcons.arrowLeft), findsNothing);

      // Verify Hamburger menu icon is present
      expect(find.byIcon(LucideIcons.menu), findsOneWidget);
      expect(find.byTooltip('Menu'), findsOneWidget);

      // Verify hamburger icon is placed at the leading edge (before logo)
      final menuOffset = tester.getTopLeft(find.byTooltip('Menu'));
      expect(menuOffset.dx, lessThan(searchOffset.dx));

      // Tap the search icon
      await tester.tap(find.byTooltip('Search'));
      await tester.pumpAndSettle();

      // In search mode, menu icon is replaced by back arrow
      expect(find.byIcon(LucideIcons.menu), findsNothing);

      // Verify the search TextField is now visible with the appropriate hint
      expect(find.byType(TextField), findsOneWidget);
      expect(find.text('Search products, facilities...'), findsOneWidget);

      // Verify back arrow is present instead of X
      expect(find.byIcon(LucideIcons.arrowLeft), findsOneWidget);
      expect(find.byTooltip('Back'), findsOneWidget);
      expect(find.byIcon(Icons.close), findsNothing);

      // Tap back arrow to exit search mode
      await tester.tap(find.byTooltip('Back'));
      await tester.pumpAndSettle();

      // Verify search TextField and back arrow are closed, and menu/search icons are restored
      expect(find.byType(TextField), findsNothing);
      expect(find.byIcon(LucideIcons.arrowLeft), findsNothing);
      expect(find.byIcon(LucideIcons.menu), findsOneWidget);
      expect(find.byTooltip('Search'), findsOneWidget);
      expect(find.byTooltip('Notifications'), findsOneWidget);
    },
  );

  testWidgets(
    'tapping hamburger icon opens the institutional dashboard navigation drawer',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(
        const MaterialApp(
          home: DashboardScreen(),
        ),
      );

      // Open drawer via hamburger icon
      await tester.tap(find.byTooltip('Menu'));
      await tester.pumpAndSettle();

      // Verify Drawer is displayed with navigation items
      expect(find.byType(Drawer), findsOneWidget);
      expect(
        find.descendant(of: find.byType(Drawer), matching: find.text('Facilities Booking')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: find.byType(Drawer), matching: find.text('Messages')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: find.byType(Drawer), matching: find.text('Profile & Account')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: find.byType(Drawer), matching: find.text('My Cart')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: find.byType(Drawer), matching: find.text('USTP Oroquieta Campus')),
        findsOneWidget,
      );
    },
  );
}
