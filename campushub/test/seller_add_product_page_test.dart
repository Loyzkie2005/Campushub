import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:campushub/module_app/config/api_config.dart';
import 'package:campushub/module_app/screens/products_screen.dart';
import 'package:campushub/module_app/screens/seller_add_product_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker_platform_interface/image_picker_platform_interface.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ProductTestPicker extends ImagePickerPlatform {
  XFile? file;
  List<XFile>? files;
  int singleCalls = 0;
  final limits = <int?>[];
  @override
  Future<XFile?> getImageFromSource({
    required ImageSource source,
    ImagePickerOptions options = const ImagePickerOptions(),
  }) async {
    singleCalls++;
    expect(source, ImageSource.gallery);
    expect(options.maxWidth, 1280);
    expect(options.requestFullMetadata, isFalse);
    return file;
  }

  @override
  Future<List<XFile>> getMultiImageWithOptions({
    MultiImagePickerOptions options = const MultiImagePickerOptions(),
  }) async {
    expect(options.imageOptions.maxWidth, 1280);
    expect(options.imageOptions.requestFullMetadata, isFalse);
    limits.add(options.limit);
    return files ?? (file == null ? [] : [file!]);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final captureKey = GlobalKey();
  final reviewDir = Platform.environment['PRODUCT_FORM_REVIEW_DIR'];
  late ImagePickerPlatform originalPicker;
  late ProductTestPicker picker;
  final png = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==',
  );
  bool? result;

  setUpAll(() async {
    if (reviewDir != null) {
      final loader = FontLoader('Poppins');
      for (final face in ['Regular', 'Medium', 'SemiBold', 'Bold']) {
        loader.addFont(
          rootBundle.load('assets/fonts/poppins/Poppins-$face.ttf'),
        );
      }
      await loader.load();
      await (FontLoader(
        'MaterialIcons',
      )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
      await (FontLoader('packages/lucide_icons/Lucide')..addFont(
            rootBundle.load('packages/lucide_icons/assets/lucide.ttf'),
          ))
          .load();
      final sdkRoot = Platform.environment['FLUTTER_ROOT'];
      if (sdkRoot != null) {
        final font = File(
          '$sdkRoot/bin/cache/artifacts/material_fonts/roboto-regular.ttf',
        ).readAsBytesSync();
        await (FontLoader(
          'Roboto',
        )..addFont(Future.value(ByteData.sublistView(font)))).load();
      }
    }
  });

  setUp(() {
    result = null;
    originalPicker = ImagePickerPlatform.instance;
    picker = ProductTestPicker();
    ImagePickerPlatform.instance = picker;
    SharedPreferences.setMockInitialValues({
      'campushub_chat_token': 'test-seller-token',
    });
    ApiConfig.recordWorkingBaseUrl('http://localhost:8000');
  });
  tearDown(() => ImagePickerPlatform.instance = originalPicker);

  http.Response status({
    bool approved = true,
    List<String> categories = const ['School Supplies', 'Snacks'],
  }) => http.Response(
    jsonEncode({'is_approved_seller': approved, 'categories': categories}),
    200,
  );

  Future<void> open(
    WidgetTester tester, {
    double width = 390,
    double scale = 1,
  }) async {
    tester.view.physicalSize = Size(width, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      RepaintBoundary(
        key: captureKey,
        child: MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: ThemeData(fontFamilyFallback: const ['Roboto']),
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: Builder(
            builder: (context) => Scaffold(
              body: TextButton(
                onPressed: () async {
                  result = await ProductsScreen.showAddProductPage(context);
                },
                child: const Text('Open form'),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open form'));
    await tester.pumpAndSettle();
  }

  Future<void> field(WidgetTester tester, String key, String value) async {
    final finder = find.byKey(ValueKey(key));
    await tester.ensureVisible(finder);
    await tester.enterText(finder, value);
    await tester.pump();
  }

  Future<void> category(WidgetTester tester, String label) async {
    tester.testTextInput.hide();
    final finder = find.byKey(const ValueKey('product-category'));
    await tester.ensureVisible(finder);
    await tester.tap(finder);
    await tester.pumpAndSettle();
    await tester.tap(find.text(label).last);
    await tester.pumpAndSettle();
  }

  Future<void> valid(WidgetTester tester) async {
    await field(tester, 'product-name', 'Test Notebook');
    await category(tester, 'School Supplies');
    await field(tester, 'product-description', 'A test-only ruled notebook.');
    await field(tester, 'product-price', '25.50');
    await field(tester, 'product-quantity', '0');
  }

  Future<void> submit(WidgetTester tester) async {
    tester.testTextInput.hide();
    final button = find.byKey(const ValueKey('submit-product'));
    await tester.ensureVisible(button);
    await tester.pumpAndSettle();
    await tester.tap(button);
    await tester.pump();
  }

  Future<void> capture(WidgetTester tester, String name) async {
    if (reviewDir == null) return;
    await tester.pumpAndSettle();
    final boundary = tester.renderObject<RenderRepaintBoundary>(
      find.byKey(captureKey),
    );
    await tester.runAsync(() async {
      final image = await boundary.toImage(pixelRatio: 1);
      try {
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        await Directory(reviewDir).create(recursive: true);
        await File(
          '$reviewDir/$name.png',
        ).writeAsBytes(bytes!.buffer.asUint8List());
      } finally {
        image.dispose();
      }
    });
  }

  for (final (width, scale) in [(360.0, 1.0), (390.0, 1.3)]) {
    testWidgets(
      'one page keeps header, order and fields at $width/$scale with keyboard',
      (tester) async {
        await http.runWithClient(() async {
          await open(tester, width: width, scale: scale);
          expect(find.byType(SellerAddProductPage), findsOneWidget);
          expect(find.byType(DraggableScrollableSheet), findsNothing);
          expect(find.byType(SingleChildScrollView), findsOneWidget);
          final titles = [
            'Product Information',
            'Pricing & Inventory',
            'Upload Images',
            'Review',
            'Submit for Approval',
          ];
          expect(find.text('Enter tags'), findsOneWidget);
          expect(
            find.text(
              'Your product will be reviewed by the ADMIN before appearing in Marketplace.',
            ),
            findsOneWidget,
          );
          for (var i = 1; i < titles.length; i++) {
            expect(
              tester.getTopLeft(find.text(titles[i])).dy,
              greaterThan(tester.getTopLeft(find.text(titles[i - 1])).dy),
            );
          }
          final header = tester.getRect(find.byType(AppBar));
          await capture(tester, 'form-${width.toInt()}-top');
          await field(tester, 'product-name', 'Test retained name');
          tester.view.viewInsets = const FakeViewPadding(bottom: 280);
          await tester.pumpAndSettle();
          await tester.ensureVisible(
            find.byKey(const ValueKey('submit-product')),
          );
          await tester.pumpAndSettle();
          expect(tester.getRect(find.byType(AppBar)), header);
          expect(
            tester
                .widget<TextFormField>(
                  find.byKey(const ValueKey('product-name')),
                )
                .controller!
                .text,
            'Test retained name',
          );
          await capture(tester, 'form-${width.toInt()}-keyboard-bottom');
          tester.view.resetViewInsets();
          expect(tester.takeException(), isNull);
        }, () => MockClient((_) async => status()));
      },
    );
  }

  testWidgets(
    'inline validation rejects empty, zero, nonfinite and fractional stock without posting',
    (tester) async {
      var posts = 0;
      await http.runWithClient(
        () async {
          await open(tester);
          await submit(tester);
          await tester.pumpAndSettle();
          expect(find.text('Product name is required.'), findsOneWidget);
          expect(find.text('Description is required.'), findsOneWidget);
          expect(find.text('Select a category.'), findsOneWidget);
          await valid(tester);
          for (final price in ['0', '-1', 'NaN', 'Infinity', '1.234']) {
            await field(tester, 'product-price', price);
            await submit(tester);
            expect(
              find.text(
                'Enter a price greater than 0 with up to 2 decimal places.',
              ),
              findsOneWidget,
            );
          }
          await field(tester, 'product-price', '1.25');
          await field(tester, 'product-quantity', '1.5');
          await submit(tester);
          expect(
            find.text('Enter a whole-number stock of 0 or more.'),
            findsOneWidget,
          );
          await field(tester, 'product-quantity', '10');
          final caution = find.byKey(
            const ValueKey('caution-Low Stock Threshold *'),
          );
          expect(caution, findsOneWidget);
          expect(
            tester.getTopLeft(caution).dx,
            greaterThan(
              tester.getTopRight(find.text('Low Stock Threshold *')).dx,
            ),
          );
          expect(find.byKey(const ValueKey('low-stock-caution')), findsNothing);
          await tester.ensureVisible(caution);
          await tester.longPress(caution);
          await tester.pumpAndSettle();
          expect(
            find.descendant(
              of: find.byKey(const ValueKey('low-stock-caution')),
              matching: find.text(
                'You will be alerted when your stock reaches this quantity or lower.',
              ),
            ),
            findsOneWidget,
          );
          await tester.longPress(caution);
          await tester.pumpAndSettle();
          expect(
            find.byKey(const ValueKey('low-stock-caution')),
            findsOneWidget,
          );
          await tester.tap(find.byKey(const ValueKey('close-caution-popup')));
          await tester.pumpAndSettle();
          expect(find.byKey(const ValueKey('low-stock-caution')), findsNothing);
          await tester.tap(caution);
          await tester.pumpAndSettle();
          expect(
            find.byKey(const ValueKey('low-stock-caution')),
            findsOneWidget,
          );
          await tester.tap(caution);
          await tester.pumpAndSettle();
          expect(find.byKey(const ValueKey('low-stock-caution')), findsNothing);
          await field(tester, 'product-low-stock-threshold', '');
          await submit(tester);
          expect(find.text('Low stock threshold is required.'), findsOneWidget);
          expect(posts, 0);
          expect(result, isNull);
        },
        () => MockClient((request) async {
          if (request.method == 'POST') posts++;
          return status();
        }),
      );
    },
  );

  testWidgets(
    'single authenticated submission guards duplicates, preserves fields on error then returns success',
    (tester) async {
      var posts = 0;
      final pending = Completer<http.Response>();
      await http.runWithClient(
        () async {
          await open(tester);
          await valid(tester);
          await submit(tester);
          expect(find.text('Submitting…'), findsOneWidget);
          expect(
            tester
                .widget<FilledButton>(
                  find.byKey(const ValueKey('submit-product')),
                )
                .onPressed,
            isNull,
          );
          expect(posts, 1);
          pending.complete(
            http.Response('{"error":"Seller access suspended."}', 403),
          );
          await tester.pumpAndSettle();
          expect(find.text('Seller access suspended.'), findsOneWidget);
          expect(
            tester
                .widget<TextFormField>(
                  find.byKey(const ValueKey('product-description')),
                )
                .controller!
                .text,
            'A test-only ruled notebook.',
          );
          await submit(tester);
          await tester.pumpAndSettle();
          expect(result, isTrue);
          expect(find.byType(SellerAddProductPage), findsNothing);
          expect(
            find.text('Product submitted for marketplace review.'),
            findsOneWidget,
          );
          expect(posts, 2);
        },
        () => MockClient((request) async {
          expect(request.headers['Authorization'], 'Bearer test-seller-token');
          if (request.method != 'POST') return status();
          expect(request.url.path, '/api/seller/products/submit/');
          final body = jsonDecode(request.body) as Map<String, dynamic>;
          expect(body['stock'], 0);
          expect(body['price'], '25.50');
          expect(body['category'], 'School Supplies');
          expect(body.containsKey('seller_id'), isFalse);
          expect(body.containsKey('approval_status'), isFalse);
          posts++;
          return posts == 1
              ? pending.future
              : http.Response(
                  '{"product":{"id":71,"approval_status":"pending"}}',
                  201,
                );
        }),
      );
    },
  );

  testWidgets(
    'gallery image previews, removes, validates and submits through the gallery payload',
    (tester) async {
      await http.runWithClient(
        () async {
          await open(tester);
          await valid(tester);
          picker.file = XFile.fromData(
            png,
            mimeType: 'image/png',
            name: 'test.png',
          );
          await tester.ensureVisible(
            find.byKey(const ValueKey('add-product-image')),
          );
          await tester.tap(find.byKey(const ValueKey('add-product-image')));
          await tester.pumpAndSettle();
          expect(
            find.byKey(const ValueKey('product-image-preview-0')),
            findsOneWidget,
          );
          await capture(tester, 'form-image-preview');
          await tester.ensureVisible(
            find.byKey(const ValueKey('remove-product-image-0')),
          );
          await tester.tap(
            find.byKey(const ValueKey('remove-product-image-0')),
          );
          await tester.pumpAndSettle();
          expect(find.text('0 of 6 images'), findsOneWidget);
          picker.file = XFile.fromData(
            utf8.encode('not an image'),
            name: 'bad.png',
          );
          await tester.ensureVisible(
            find.byKey(const ValueKey('add-product-image')),
          );
          await tester.tap(find.byKey(const ValueKey('add-product-image')));
          await tester.pumpAndSettle();
          expect(
            find.text('Choose a JPEG, PNG, WebP or GIF image up to 5 MB.'),
            findsOneWidget,
          );
          picker.file = XFile.fromData(
            png,
            mimeType: 'image/png',
            name: 'test.png',
          );
          await tester.ensureVisible(
            find.byKey(const ValueKey('add-product-image')),
          );
          await tester.tap(find.byKey(const ValueKey('add-product-image')));
          await tester.pumpAndSettle();
          await submit(tester);
          await tester.pumpAndSettle();
          expect(result, isTrue);
        },
        () => MockClient((request) async {
          if (request.method == 'POST') {
            final data = jsonDecode(request.body) as Map;
            expect(data['images'], [
              'data:image/png;base64,${base64Encode(png)}',
            ]);
            expect(data.containsKey('image_url'), isFalse);
            return http.Response(
              '{"product":{"id":72,"approval_status":"pending"}}',
              201,
            );
          }
          return status();
        }),
      );
    },
  );

  testWidgets(
    'six-image limit, replacement and removal preserve the submitted gallery',
    (tester) async {
      await http.runWithClient(
        () async {
          await open(tester, width: 360);
          await valid(tester);
          final file = XFile.fromData(
            png,
            mimeType: 'image/png',
            name: 'test.png',
          );
          final add = find.byKey(const ValueKey('add-product-image'));
          await tester.ensureVisible(add);
          picker.files = List.filled(
            7,
            file,
          ); // A platform may ignore its native limit.
          await tester.tap(add);
          await tester.pumpAndSettle();
          expect(find.text('0 of 6 images'), findsOneWidget);
          expect(
            find.text('You can upload up to 6 images. Select fewer images.'),
            findsOneWidget,
          );
          picker.files = List.filled(6, file);
          await tester.tap(add);
          await tester.pumpAndSettle();
          expect(find.text('6 of 6 images'), findsOneWidget);
          expect(tester.widget<OutlinedButton>(add).onPressed, isNull);
          expect(picker.limits, [6, 6]);
          for (var i = 0; i < 6; i++) {
            expect(
              find.byKey(ValueKey('product-image-preview-$i')),
              findsOneWidget,
            );
          }
          await capture(tester, 'form-six-images');
          final remove = find.byKey(const ValueKey('remove-product-image-0'));
          await tester.ensureVisible(remove);
          await tester.tap(remove);
          await tester.pumpAndSettle();
          expect(find.text('5 of 6 images'), findsOneWidget);
          picker.file = file;
          await tester.ensureVisible(add);
          await tester.tap(
            add,
          ); // One remaining slot uses single-image selection.
          await tester.pumpAndSettle();
          expect(picker.singleCalls, 1);
          expect(find.text('6 of 6 images'), findsOneWidget);
          final replace = find.byKey(const ValueKey('product-image-slot-1'));
          await tester.ensureVisible(replace);
          await tester.tap(replace);
          await tester.pumpAndSettle();
          expect(picker.singleCalls, 2);
          expect(find.text('6 of 6 images'), findsOneWidget);
          await submit(tester);
          await tester.pumpAndSettle();
          expect(result, isTrue);
        },
        () => MockClient((request) async {
          if (request.method != 'POST') return status();
          final data = jsonDecode(request.body) as Map;
          expect(
            data['images'],
            List.filled(6, 'data:image/png;base64,${base64Encode(png)}'),
          );
          expect(data.containsKey('image_url'), isFalse);
          return http.Response(
            '{"product":{"id":73,"approval_status":"pending"}}',
            201,
          );
        }),
      );
    },
  );

  testWidgets(
    'invalid multi-selection preserves the previous gallery without partial additions',
    (tester) async {
      await http.runWithClient(() async {
        await open(tester);
        final file = XFile.fromData(
          png,
          mimeType: 'image/png',
          name: 'test.png',
        );
        picker.files = [file];
        final add = find.byKey(const ValueKey('add-product-image'));
        await tester.ensureVisible(add);
        await tester.tap(add);
        await tester.pumpAndSettle();
        picker.files = [
          file,
          XFile.fromData(utf8.encode('invalid'), name: 'bad.png'),
        ];
        await tester.tap(add);
        await tester.pumpAndSettle();
        expect(picker.limits, [6, 5]);
        expect(find.text('1 of 6 images'), findsOneWidget);
        expect(
          find.byKey(const ValueKey('product-image-preview-0')),
          findsOneWidget,
        );
        expect(
          find.byKey(const ValueKey('product-image-preview-1')),
          findsNothing,
        );
        expect(
          find.text('Choose a JPEG, PNG, WebP or GIF image up to 5 MB.'),
          findsOneWidget,
        );
      }, () => MockClient((_) async => status()));
    },
  );

  testWidgets('gallery cancel and oversized selection leave form usable', (
    tester,
  ) async {
    await http.runWithClient(() async {
      await open(tester);
      final add = find.byKey(const ValueKey('add-product-image'));
      await tester.ensureVisible(add);
      await tester.tap(add);
      await tester.pumpAndSettle();
      expect(find.text('0 of 6 images'), findsOneWidget);
      picker.file = XFile.fromData(
        Uint8List(5 * 1024 * 1024 + 1),
        name: 'huge.png',
      );
      await tester.tap(add);
      await tester.pumpAndSettle();
      expect(find.text('Choose an image no larger than 5 MB.'), findsOneWidget);
      expect(tester.widget<OutlinedButton>(add).onPressed, isNotNull);
    }, () => MockClient((_) async => status()));
  });

  testWidgets(
    'perishable expiry survives scrolling but disappears for other categories',
    (tester) async {
      await http.runWithClient(() async {
        await open(tester);
        // The category menu must open below the field, never over its label.
        final labelBottom = tester.getBottomLeft(find.text('Category *')).dy;
        final fieldBottom = tester
            .getBottomLeft(find.byKey(const ValueKey('product-category')))
            .dy;
        await tester.tap(find.byKey(const ValueKey('product-category')));
        await tester.pumpAndSettle();
        final menuTop = tester.getTopLeft(find.text('Snacks').last).dy;
        expect(menuTop, greaterThan(labelBottom));
        expect(menuTop, greaterThanOrEqualTo(fieldBottom));
        await tester.tap(find.text('Snacks').last);
        await tester.pumpAndSettle();
        expect(find.text('Expiry Date (Optional)'), findsOneWidget);
        await category(tester, 'School Supplies');
        expect(find.text('Expiry Date (Optional)'), findsNothing);
      }, () => MockClient((_) async => status()));
    },
  );

  testWidgets(
    'unapproved access never opens form and empty categories never fabricate options',
    (tester) async {
      await http.runWithClient(() async {
        await open(tester);
        expect(find.byType(SellerAddProductPage), findsNothing);
        expect(
          find.text('Approved active seller access is required.'),
          findsOneWidget,
        );
      }, () => MockClient((_) async => status(approved: false)));
      await http.runWithClient(() async {
        await tester.tap(find.text('Open form'));
        await tester.pumpAndSettle();
        expect(
          find.text(
            'No categories are available. Go back and reopen Add Product to retry.',
          ),
          findsOneWidget,
        );
        expect(
          tester
              .widget<FilledButton>(
                find.byKey(const ValueKey('submit-product')),
              )
              .onPressed,
          isNull,
        );
      }, () => MockClient((_) async => status(categories: [])));
    },
  );

  testWidgets(
    'malformed success never closes the form or reports submission success',
    (tester) async {
      await http.runWithClient(
        () async {
          await open(tester);
          await valid(tester);
          await submit(tester);
          await tester.pumpAndSettle();
          expect(result, isNull);
          expect(
            find.byKey(const ValueKey('product-submit-error')),
            findsOneWidget,
          );
          expect(find.byType(SellerAddProductPage), findsOneWidget);
        },
        () => MockClient(
          (request) async =>
              request.method == 'POST' ? http.Response('{}', 201) : status(),
        ),
      );
    },
  );
}
