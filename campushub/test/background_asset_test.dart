import 'package:campushub/module_app/screens/splash_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('intro renders cleanly without background image', (tester) async {
    final manifest = await AssetManifest.loadFromAssetBundle(rootBundle);
    expect(
      manifest.listAssets(),
      isNot(contains('assets/img/background_image.png')),
    );
    expect(manifest.listAssets(), isNot(contains('assets/img/background.png')));

    await tester.pumpWidget(const MaterialApp(home: CampusHubIntroScreen()));
    await tester.pumpAndSettle();
    expect(find.byType(Image), findsOneWidget); // Only logo.png
    expect(tester.takeException(), isNull);
  });
}
