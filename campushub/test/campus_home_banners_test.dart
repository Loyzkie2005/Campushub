import 'dart:io';
import 'dart:ui' as ui;

import 'package:campushub/module_app/widgets/home/campus_home_banners.dart';
import 'package:campushub/module_app/widgets/home/home_preview_cards.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Future<void> mount(
    WidgetTester tester, {
    bool active = true,
    bool reducedMotion = false,
    double scale = 1,
    List<int>? visits,
    GlobalKey? capture,
  }) => tester.pumpWidget(
    MaterialApp(
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(
          disableAnimations: reducedMotion,
          textScaler: TextScaler.linear(scale),
        ),
        child: child!,
      ),
      home: Scaffold(
        body: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: RepaintBoundary(
              key: capture,
              child: CampusHomeBanners(
                active: active,
                onMarketplace: () => visits?.add(1),
                onFacilities: () => visits?.add(3),
                onServices: () => visits?.add(2),
              ),
            ),
          ),
        ),
      ),
    ),
  );

  testWidgets(
    'banner rotates every five seconds, loops and keeps the same height',
    (tester) async {
      await mount(tester);
      await tester.pumpAndSettle();
      final bounds = tester.getSize(
        find.byKey(const ValueKey('home-campus-banners')),
      );
      expect(find.text('Shop on Campus'), findsOneWidget);
      expect(find.byType(IconButton), findsNothing);
      final paper = tester.getRect(
        find.byKey(const ValueKey('home-banner-paper')),
      );
      final button = tester.getRect(
        find.widgetWithText(TextButton, 'Browse Products'),
      );
      expect(paper.height, greaterThanOrEqualTo(188));
      expect(button.left, closeTo(paper.left + 16, .5));
      expect(button.bottom, closeTo(paper.bottom - 16, .5));
      expect(button.height, greaterThanOrEqualTo(48));
      final firstDot = find.byKey(const ValueKey('home-banner-dot-0'));
      final lastDot = find.byKey(const ValueKey('home-banner-dot-2'));
      expect(
        (tester.getCenter(firstDot).dx + tester.getCenter(lastDot).dx) / 2,
        closeTo(
          tester
              .getCenter(find.byKey(const ValueKey('home-campus-banners')))
              .dx,
          .5,
        ),
      );
      await tester.pump(const Duration(seconds: 4));
      expect(find.text('Shop on Campus'), findsOneWidget);
      await tester.pump(const Duration(seconds: 1));
      await tester.pump(const Duration(milliseconds: 225));
      final pager = tester.widget<PageView>(find.byType(PageView)).controller!;
      expect(pager.page, greaterThan(3000));
      expect(pager.page, lessThan(3001));
      await tester.pumpAndSettle();
      expect(find.text('Explore Campus Facilities'), findsOneWidget);
      expect(
        tester.getSize(find.byKey(const ValueKey('home-campus-banners'))),
        bounds,
      );
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
      expect(find.text('Campus Services Made Easy'), findsOneWidget);
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
      expect(find.text('Shop on Campus'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'dots-only carousel supports accessible pause, lifecycle, manual swipes and existing tabs',
    (tester) async {
      final visits = <int>[];
      await mount(tester, visits: visits);
      await tester.pumpAndSettle();
      final indicator = find.byWidgetPredicate(
        (widget) =>
            widget is Semantics && widget.properties.label == 'Campus banners',
      );
      tester
          .widget<Semantics>(indicator)
          .properties
          .customSemanticsActions!
          .values
          .single();
      await tester.pump(const Duration(seconds: 15));
      expect(find.text('Shop on Campus'), findsOneWidget);
      tester
          .widget<Semantics>(indicator)
          .properties
          .customSemanticsActions!
          .values
          .single();
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
      expect(find.text('Explore Campus Facilities'), findsOneWidget);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
      await tester.pump(const Duration(seconds: 10));
      expect(find.text('Explore Campus Facilities'), findsOneWidget);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
      expect(find.text('Campus Services Made Easy'), findsOneWidget);
      await tester.tap(find.text('View Services'));
      await tester.drag(find.byType(PageView), const Offset(650, 0));
      await tester.pumpAndSettle();
      await tester.tap(find.text('View Facilities'));
      await tester.drag(find.byType(PageView), const Offset(650, 0));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Browse Products'));
      expect(visits, [2, 3, 1]);
      await mount(tester, active: false);
      await tester.pump(const Duration(seconds: 10));
      expect(find.text('Shop on Campus'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  for (final scale in [1.0, 2.0]) {
    testWidgets(
      'photo banners fit 320dp at ${scale}x and respect reduced motion',
      (tester) async {
        tester.view.physicalSize = const Size(320, 900);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final directory = Platform.environment['HOME_BANNER_REVIEW_DIR'];
        if (directory != null) {
          await tester.runAsync(() async {
            for (final face in ['Regular', 'Medium', 'SemiBold', 'Bold']) {
              await (FontLoader('Poppins')..addFont(
                    rootBundle.load('assets/fonts/poppins/Poppins-$face.ttf'),
                  ))
                  .load();
            }
            await (FontLoader('packages/iconsax_flutter/FlutterIconsax')
                  ..addFont(
                    rootBundle.load(
                      'packages/iconsax_flutter/fonts/FlutterIconsax.ttf',
                    ),
                  ))
                .load();
          });
        }
        final capture = GlobalKey();
        await mount(
          tester,
          reducedMotion: true,
          scale: scale,
          capture: capture,
        );
        await tester.pumpAndSettle();
        await tester.pump(const Duration(seconds: 15));
        expect(find.text('Shop on Campus'), findsOneWidget);
        final image = tester.widget<Image>(find.byType(Image).first);
        expect(
          (image.image as ResizeImage).imageProvider,
          const AssetImage('assets/img/ustp_oroquieta_entrance.png'),
        );
        if (directory != null) {
          await tester.runAsync(() async {
            await precacheImage(
              image.image,
              tester.element(find.byType(CampusHomeBanners)),
            );
          });
          await tester.pumpAndSettle();
          await tester.runAsync(() async {
            final boundary =
                capture.currentContext!.findRenderObject()!
                    as RenderRepaintBoundary;
            final rendered = await boundary.toImage(pixelRatio: 2);
            final bytes = await rendered.toByteData(
              format: ui.ImageByteFormat.png,
            );
            Directory(directory).createSync(recursive: true);
            File(
              '$directory/banner-320-$scale.png',
            ).writeAsBytesSync(bytes!.buffer.asUint8List());
            rendered.dispose();
          });
        }
        for (final (index, action) in [
          'View Facilities',
          'View Services',
          'Browse Products',
        ].indexed) {
          await tester.drag(find.byType(PageView), const Offset(-260, 0));
          await tester.pumpAndSettle();
          expect(find.text(action), findsOneWidget);
          final selected =
              tester
                      .widget<AnimatedContainer>(
                        find.byKey(
                          ValueKey('home-banner-dot-${(index + 1) % 3}'),
                        ),
                      )
                      .decoration!
                  as BoxDecoration;
          expect(selected.color, HomeAppColors.gold);
          expect(tester.takeException(), isNull);
        }
      },
    );
  }
}
