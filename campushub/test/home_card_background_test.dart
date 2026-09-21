import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  for (final width in [360.0, 390.0]) {
    testWidgets('Home cards retain buttons without images at width $width', (
      tester,
    ) async {
      SharedPreferences.setMockInitialValues({});
      tester.view.physicalSize = Size(width, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(const MaterialApp(home: DashboardScreen()));
      await tester.pumpAndSettle();

      for (final label in ['Explore Now', 'Book Now', 'Browse Product']) {
        final buttonFinder = find
            .widgetWithText(ElevatedButton, label)
            .hitTestable();
        expect(buttonFinder, findsOneWidget);
        expect(
          find.byKey(const ValueKey('home-card-campus-image')),
          findsNothing,
        );
        expect(
          tester.widget<ElevatedButton>(buttonFinder).onPressed,
          isNotNull,
        );
        expect(tester.takeException(), isNull);
        if (label != 'Browse Product') {
          await tester.drag(buttonFinder, const Offset(-320, 0));
          await tester.pumpAndSettle();
        }
      }
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    });
  }
}
