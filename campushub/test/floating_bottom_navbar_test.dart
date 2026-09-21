import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final width in [320.0, 390.0, 768.0]) {
    testWidgets('Floating navbar fits and switches tabs at width $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 800);
      tester.view.devicePixelRatio = 1;
      tester.view.viewPadding = const FakeViewPadding(bottom: 24);
      tester.view.padding = const FakeViewPadding(bottom: 24);
      addTearDown(tester.view.reset);
      var selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(brightness: Brightness.dark),
          home: StatefulBuilder(
            builder: (context, setState) => Scaffold(
              backgroundColor: Colors.white,
              body: const SizedBox.expand(key: Key('page-body')),
              bottomNavigationBar: FloatingBottomNavbar(
                currentIndex: selectedIndex,
                onTap: (index) => setState(() => selectedIndex = index),
              ),
            ),
          ),
        ),
      );

      final pillFinder = find.byKey(const Key('floating-navbar-pill'));
      final initialRect = tester.getRect(pillFinder);
      expect(initialRect.left, 0.0);
      expect(initialRect.right, width);
      expect(initialRect.bottom, 800.0);
      expect(
        tester.getRect(find.byKey(const Key('page-body'))).bottom,
        lessThanOrEqualTo(initialRect.top),
      );

      // Verify text labels are shown
      const labels = ['Home', 'Products', 'Facilities', 'Messages', 'Profile'];
      for (final label in labels) {
        expect(find.text(label), findsOneWidget);
      }

      // Verify tapping each icon switches tabs
      for (var index = 0; index < 5; index++) {
        await tester.tap(find.byKey(ValueKey('navbar-item-$index')));
        await tester.pumpAndSettle();
        expect(selectedIndex, index);
        expect(tester.getRect(pillFinder), initialRect);
        expect(tester.takeException(), isNull);
      }
    });
  }
}
