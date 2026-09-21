import 'package:campushub/main.dart';
import 'package:campushub/module_app/services/theme_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  for (final lightMode in [true, false]) {
    testWidgets('System inset does not cover route surface: light=$lightMode', (
      tester,
    ) async {
      SharedPreferences.setMockInitialValues({
        'campushub_light_theme': lightMode,
      });
      await ThemeService.instance.load();
      tester.view.viewPadding = const FakeViewPadding(bottom: 24);
      addTearDown(tester.view.resetViewPadding);

      await tester.pumpWidget(const CampusHubApp());
      final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
      const surface = ColoredBox(color: Colors.white);

      // Exercise the production app wrapper without auth or network requests.
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(builder: (context) => app.builder!(context, surface)),
        ),
      );
      final region = tester.widget<AnnotatedRegion<SystemUiOverlayStyle>>(
        find.byType(AnnotatedRegion<SystemUiOverlayStyle>),
      );
      expect(region.child, same(surface));
      expect(region.value.systemNavigationBarColor, Colors.transparent);
      expect(find.byType(Positioned), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }
}
