import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  for (final width in [320.0, 390.0]) {
    testWidgets('brand header and welcome slide fit at $width', (tester) async {
      tester.view.physicalSize = Size(width, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      SharedPreferences.setMockInitialValues({
        'campushub_logged_user': jsonEncode({
          'id': 1,
          'first_name': 'Lester',
          'full_name': 'Lester Bulay',
          'username': 'test-buyer',
        }),
      });
      final directory = Platform.environment['DASHBOARD_REVIEW_DIR'];
      final font = Platform.environment['CHECKOUT_REVIEW_FONT'];
      if (directory != null && font != null) {
        await tester.runAsync(() async {
          final text = FontLoader('Roboto')
            ..addFont(
              Future.value(ByteData.sublistView(File(font).readAsBytesSync())),
            );
          await text.load();
          final icons = FontLoader('packages/lucide_icons/Lucide')
            ..addFont(
              rootBundle.load('packages/lucide_icons/assets/lucide.ttf'),
            );
          await icons.load();
          final material = FontLoader('MaterialIcons')
            ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
          await material.load();
        });
      }
      final capture = GlobalKey();
      await tester.pumpWidget(
        MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: ThemeData(fontFamily: 'Roboto'),
          home: RepaintBoundary(key: capture, child: const DashboardScreen()),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(AppBar), findsNothing);
      final header = find.byKey(const ValueKey('dashboard-brand-header'));
      expect(tester.widget<Material>(header).color, Colors.white);
      final overlay = tester.widget<AnnotatedRegion<SystemUiOverlayStyle>>(
        find
            .descendant(
              of: find.byType(DashboardScreen),
              matching: find.byType(AnnotatedRegion<SystemUiOverlayStyle>),
            )
            .first,
      );
      expect(overlay.value.statusBarColor, DashboardScreen.headerTint);
      expect(overlay.value.statusBarIconBrightness, Brightness.dark);
      expect(DashboardScreen.pageBackground, Colors.white);
      final logo = find.byKey(const ValueKey('dashboard-brand-logo'));
      final brand = find.byKey(const ValueKey('dashboard-brand-name'));
      final carousel = find.byKey(const ValueKey('home-carousel'));
      expect(logo, findsOneWidget);
      expect(
        (tester.widget<Image>(logo).image as AssetImage).assetName,
        'assets/img/logo_light.png',
      );
      for (final icon in tester.widgetList<Icon>(
        find.descendant(of: header, matching: find.byType(Icon)),
      )) {
        expect(icon.color, DashboardScreen.headerNavy);
      }
      final contrast =
          (DashboardScreen.headerTint.computeLuminance() + 0.05) /
          (DashboardScreen.headerNavy.computeLuminance() + 0.05);
      expect(contrast, greaterThan(4.5));
      expect(brand, findsOneWidget);
      expect(
        find.text('Welcome Back, Lester'),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: header,
          matching: find.textContaining('Welcome Back'),
        ),
        findsNothing,
      );
      expect(
        tester.getRect(brand).right,
        lessThanOrEqualTo(tester.getRect(find.byTooltip('Search')).left),
      );
      expect(tester.takeException(), isNull);

      if (directory != null) {
        await tester.runAsync(() async {
          await precacheImage(
            tester.widget<Image>(logo).image,
            capture.currentContext!,
          );
        });
        await tester.pumpAndSettle();
        await tester.runAsync(() async {
          final boundary =
              capture.currentContext!.findRenderObject()!
                  as RenderRepaintBoundary;
          final image = await boundary.toImage(pixelRatio: 2);
          final data = await image.toByteData(format: ui.ImageByteFormat.png);
          Directory(directory).createSync(recursive: true);
          File(
            '$directory/dashboard-${width.toInt()}.png',
          ).writeAsBytesSync(data!.buffer.asUint8List());
          image.dispose();
        });
      }

      await tester.drag(carousel, const Offset(-300, 0));
      await tester.pumpAndSettle();
      expect(find.text('Book Campus Facilities\nEasily'), findsOneWidget);
      await tester.tap(find.byTooltip('Search'));
      await tester.pumpAndSettle();
      expect(find.byType(TextField), findsOneWidget);
      await tester.enterText(find.byType(TextField), 'notebook');
      await tester.tap(find.byTooltip('Back'));
      await tester.pumpAndSettle();
      expect(brand, findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }
}
