import 'dart:convert';
import 'dart:ui' as ui;

import 'package:campushub/module_app/widgets/product_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late String largeImage;
  setUpAll(() async {
    // A large camera-sized fixture, isolated from the real product database.
    final recorder = ui.PictureRecorder();
    Canvas(recorder).drawColor(Colors.white, BlendMode.src);
    final picture = recorder.endRecording();
    final image = await picture.toImage(4096, 4096);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    largeImage =
        'data:image/png;base64,${base64Encode(bytes!.buffer.asUint8List())}';
    image.dispose();
    picture.dispose();
  });

  tearDown(() => PaintingBinding.instance.imageCache.clear());

  testWidgets(
    'camera image decodes to thumbnail pixels and retains aspect ratio',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        MaterialApp(
          home: Center(
            child: SizedBox(
              width: 100,
              height: 150,
              child: ProductImage(imageUrl: largeImage),
            ),
          ),
        ),
      );
      final widget = tester.widget<Image>(find.byType(Image));
      final stream = widget.image.resolve(const ImageConfiguration());
      ui.Image? decoded;
      final listener = ImageStreamListener(
        (info, _) => decoded = info.image.clone(),
      );
      stream.addListener(listener);
      await tester.runAsync(() async {
        for (var i = 0; decoded == null && i < 100; i++) {
          await Future<void>.delayed(const Duration(milliseconds: 20));
        }
      });
      stream.removeListener(listener);
      expect(decoded, isNotNull);
      expect(decoded!.width, lessThanOrEqualTo(128));
      expect(decoded!.height, decoded!.width);
      expect(decoded!.width * decoded!.height * 4, lessThan(100 * 1024));
      decoded!.dispose();
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'network and inline photos use bounded decode without changing crop',
    (tester) async {
      tester.view.devicePixelRatio = 4;
      addTearDown(tester.view.resetDevicePixelRatio);
      for (final source in ['https://example.test/photo.png', largeImage]) {
        await tester.pumpWidget(
          MaterialApp(
            home: Center(
              child: SizedBox(
                width: 3000,
                height: 3000,
                child: ProductImage(imageUrl: source, fit: BoxFit.contain),
              ),
            ),
          ),
        );
        final image = tester.widget<Image>(find.byType(Image));
        final provider = image.image as ResizeImage;
        expect(provider.width, lessThanOrEqualTo(2048));
        expect(provider.height, lessThanOrEqualTo(2048));
        expect(provider.policy, ResizeImagePolicy.fit);
        expect(image.fit, BoxFit.contain);
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
      }
    },
  );

  testWidgets('missing and malformed inline images retain the fallback', (
    tester,
  ) async {
    for (final source in ['', 'data:image/png;base64,not-valid!']) {
      await tester.pumpWidget(
        MaterialApp(
          home: SizedBox(
            width: 100,
            height: 100,
            child: ProductImage(imageUrl: source),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byIcon(Icons.lunch_dining_outlined), findsOneWidget);
      expect(tester.takeException(), isNull);
    }
  });
}
