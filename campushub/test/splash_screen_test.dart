import 'package:campushub/module_app/screens/splash_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'CampusHub splash screen has full navy blue background, centered logo, name below, and runs popup animation',
    (tester) async {
      await tester.pumpWidget(const MaterialApp(home: CampusHubIntroScreen()));

      // Initial frame: verify background color is institutional navy blue (#1A1851)
      final scaffoldFinder = find.byType(Scaffold);
      expect(scaffoldFinder, findsOneWidget);
      final scaffold = tester.widget<Scaffold>(scaffoldFinder);
      expect(scaffold.backgroundColor, const Color(0xFF1A1851));

      // Centered logo image
      final logoFinder = find.byType(Image);
      expect(logoFinder, findsOneWidget);
      final image = tester.widget<Image>(logoFinder);
      expect((image.image as AssetImage).assetName, 'assets/img/logo.png');

      // Brand text below logo
      expect(find.text('CampusHub', findRichText: true), findsOneWidget);
      expect(find.text('USTP OROQUIETA CAMPUS'), findsOneWidget);

      // Advance animation halfway (pop-up spring and radiant flash)
      await tester.pump(const Duration(milliseconds: 700));
      expect(tester.takeException(), isNull);

      // Advance animation to completion
      await tester.pump(const Duration(milliseconds: 750));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('SplashScreen alias renders identical institutional splash screen', (
    tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: SplashScreen()));
    await tester.pumpAndSettle();

    final scaffold = tester.widget<Scaffold>(find.byType(Scaffold));
    expect(scaffold.backgroundColor, const Color(0xFF1A1851));
    expect(find.byType(Image), findsOneWidget);
    expect(find.text('CampusHub', findRichText: true), findsOneWidget);
  });
}
