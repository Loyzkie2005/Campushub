import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/widgets/home/home_preview_cards.dart';
import 'package:campushub/module_app/widgets/product_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'home_test_fixtures.dart';

void main() {
  for (final (width, scale) in [
    (320.0, 1.0),
    (375.0, 1.0),
    (390.0, 1.0),
    (320.0, 2.0),
    (844.0, 1.0),
  ]) {
    testWidgets('discovery header and production cards fit $width at $scale', (
      tester,
    ) async {
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
      final output = Platform.environment['DASHBOARD_REVIEW_DIR'];
      final font = Platform.environment['CHECKOUT_REVIEW_FONT'];
      if (output != null && font != null) {
        await tester.runAsync(() async {
          await (FontLoader('Roboto')..addFont(
                Future.value(
                  ByteData.sublistView(File(font).readAsBytesSync()),
                ),
              ))
              .load();
          await (FontLoader('Montserrat')..addFont(
                rootBundle.load(
                  'assets/fonts/Montserrat-VariableFont_wght.ttf',
                ),
              ))
              .load();
          await (FontLoader('SugarPie')..addFont(
                rootBundle.load('assets/fonts/Sugar-Pie-W00-Regular.ttf'),
              ))
              .load();
          final poppins = FontLoader('Poppins');
          for (final weight in ['Regular', 'Medium', 'SemiBold', 'Bold']) {
            poppins.addFont(
              rootBundle.load('assets/fonts/poppins/Poppins-$weight.ttf'),
            );
          }
          await poppins.load();
          await (FontLoader('MaterialIcons')
                ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf')))
              .load();
          await (FontLoader('packages/iconsax_flutter/FlutterIconsax')..addFont(
                rootBundle.load(
                  'packages/iconsax_flutter/fonts/FlutterIconsax.ttf',
                ),
              ))
              .load();
          await (FontLoader('packages/lucide_icons/Lucide')..addFont(
                rootBundle.load('packages/lucide_icons/assets/lucide.ttf'),
              ))
              .load();
        });
      }
      final capture = GlobalKey();
      await tester.pumpWidget(
        MaterialApp(
          debugShowCheckedModeBanner: false,
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: RepaintBoundary(
            key: capture,
            child: DashboardScreen(
              serviceCatalog: HomeTestCatalog(),
              loadHomeProducts: homeProducts,
              loadHomeFacilities: homeFacilities,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Welcome Back, Lester'), findsOneWidget);
      // At 2x text, this header-only viewport leaves lazy cards below the fold.
      if (scale == 1) {
        final productCard = tester.widget<Container>(
          find
              .descendant(
                of: find.byType(MarketplacePreviewCard).first,
                matching: find.byType(Container),
              )
              .first,
        );
        expect((productCard.decoration! as BoxDecoration).color, Colors.white);
        final image = tester.widget<ProductImage>(
          find
              .descendant(
                of: find.byType(MarketplacePreviewCard).first,
                matching: find.byType(ProductImage),
              )
              .first,
        );
        expect(image.backgroundColor, Colors.white);
      }
      expect(find.byKey(const ValueKey('home-carousel')), findsNothing);
      expect(find.byTooltip('Search'), findsOneWidget);
      expect(find.byKey(const ValueKey('home-search')), findsNothing);
      expect(find.byTooltip('Open menu'), findsOneWidget);
      expect(find.byTooltip('Messages'), findsNothing);
      expect(find.byTooltip('Notifications'), findsOneWidget);
      final notificationButton = find
          .ancestor(
            of: find.byTooltip('Notifications'),
            matching: find.byType(IconButton),
          )
          .first;
      final searchButton = find
          .ancestor(
            of: find.byTooltip('Search'),
            matching: find.byType(IconButton),
          )
          .first;
      expect(find.byTooltip('Open Profile'), findsNothing);
      expect(
        tester.getRect(searchButton).right,
        lessThanOrEqualTo(tester.getRect(notificationButton).left),
      );
      expect(
        tester.getSize(notificationButton).shortestSide,
        greaterThanOrEqualTo(48),
      );
      expect(
        tester
            .getRect(find.byKey(const ValueKey('dashboard-brand-name')))
            .right,
        lessThanOrEqualTo(tester.getRect(searchButton).left),
      );
      expect(find.text('Hot'), findsNothing);
      expect(find.text('New'), findsNothing);
      expect(tester.takeException(), isNull);
      if (output != null) {
        await tester.runAsync(
          () => precacheImage(
            const AssetImage('assets/img/logo_light.png'),
            capture.currentContext!,
          ),
        );
        await tester.pumpAndSettle();
        await tester.runAsync(() async {
          final boundary =
              capture.currentContext!.findRenderObject()!
                  as RenderRepaintBoundary;
          final image = await boundary.toImage(pixelRatio: 2);
          final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
          Directory(output).createSync(recursive: true);
          File(
            '$output/home-${width.toInt()}-$scale.png',
          ).writeAsBytesSync(bytes!.buffer.asUint8List());
          image.dispose();
        });
      }
      await tester.drag(
        find.byKey(const PageStorageKey('home-scroll')),
        const Offset(0, -560),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.scrollUntilVisible(
        find.text('Test Laboratory'),
        220,
        scrollable: find
            .descendant(
              of: find.byKey(const PageStorageKey('home-scroll')),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.tap(find.byTooltip('Notifications'));
      await tester.pumpAndSettle();
      expect(find.text('Enable notifications'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }
}
