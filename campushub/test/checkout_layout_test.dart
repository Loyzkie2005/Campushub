import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:campushub/module_app/models/product_customization.dart';
import 'package:campushub/module_app/screens/cart_screen.dart';
import 'package:campushub/module_app/screens/checkout_screen.dart';
import 'package:campushub/module_app/services/cart_service.dart';
import 'package:campushub/module_app/widgets/order_summary_widgets.dart';
import 'package:campushub/module_app/widgets/product_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

const selection = BuySelection(
  quantity: 2,
  selections: [],
  summary: '',
  unitPrice: 50,
);

void main() {
  setUp(() async {
    SharedPreferences.setMockInitialValues({
      'campushub_logged_user': jsonEncode({
        'id': 1,
        'username': 'login-not-student-id',
        'full_name': 'Lester Bulay',
        'student_id': '2023304615',
        'contact_number': '09123456789',
        'user_type': 'student',
      }),
    });
    await CartService.instance.clear();
  });

  Future<void> pumpCheckout(
    WidgetTester tester, {
    double width = 390,
    double scale = 1,
    bool dark = false,
    bool longText = false,
    GlobalKey? captureKey,
  }) async {
    tester.view.physicalSize = Size(width, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var imageUrl = '';
    final imagePath = Platform.environment['CHECKOUT_REVIEW_IMAGE'];
    if (imagePath != null) {
      imageUrl =
          'data:image/jpeg;base64,${base64Encode(File(imagePath).readAsBytesSync())}';
    }
    final screen = CheckoutScreen(
      productId: 1,
      productName: longText
          ? 'Milk Tea with Extra Pearls and Cream Cheese'
          : 'Milk Tea',
      basePrice: 50,
      selection: selection,
      imageUrl: imageUrl,
      category: 'Food & Drinks',
      sellerName: longText
          ? 'Campus Student Enterprise Cooperative Store'
          : 'Campus Store',
      sellerContact: '09999999999',
    );
    await tester.pumpWidget(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: dark ? Brightness.dark : Brightness.light,
          fontFamily: 'Roboto',
        ),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
        initialRoute: '/checkout',
        routes: {
          '/': (_) => const Scaffold(),
          '/checkout': (_) => RepaintBoundary(key: captureKey, child: screen),
        },
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets(
    'checkout has white surfaces, centered title and real buyer details',
    (tester) async {
      await pumpCheckout(tester);
      final appbar = tester.widget<AppBar>(find.byType(AppBar));
      expect(appbar.centerTitle, isTrue);
      expect(appbar.surfaceTintColor, Colors.transparent);
      expect(appbar.scrolledUnderElevation, 0);
      expect(
        tester.widget<Scaffold>(find.byType(Scaffold).last).backgroundColor,
        OrderSummaryConstants.checkoutBg,
      );
      expect(find.text('Order Summary'), findsOneWidget);
      expect(
        find.descendant(
          of: find.byType(OrderSummaryCard),
          matching: find.text('Order Summary'),
        ),
        findsOneWidget,
      );
      expect(find.text('Lester Bulay'), findsOneWidget);
      expect(find.text('2023304615'), findsOneWidget);
      expect(find.text('09123456789'), findsOneWidget);
      expect(find.text('login-not-student-id'), findsNothing);
      expect(find.text('Name:'), findsNothing);
      expect(find.text('Buyer Information'), findsNothing);
      final buyerCard = find.byKey(const ValueKey('checkout-buyer-card'));
      expect(buyerCard, findsOneWidget);
      for (final section in [buyerCard, find.byType(OrderSummaryCard)]) {
        final rect = tester.getRect(section);
        expect(rect.left, 0);
        expect(rect.width, 390);
      }
      expect(
        find.descendant(of: find.byType(OrderSummaryCard), matching: buyerCard),
        findsNothing,
      );
      expect(
        tester.getRect(buyerCard).bottom,
        lessThanOrEqualTo(tester.getRect(find.byType(OrderSummaryCard)).top),
      );
      final name = tester.getRect(find.text('Lester Bulay'));
      final id = tester.getRect(find.text('2023304615'));
      final phone = tester.getRect(find.text('09123456789'));
      final locIcon = tester.getRect(find.byIcon(Icons.location_on_outlined));
      expect(locIcon.left, lessThan(name.left));
      expect(id.left, greaterThan(name.left));
      expect(phone.top, greaterThan(name.top));
      final product = tester.getRect(find.text('Milk Tea'));
      final productImage = tester.getRect(find.byType(ProductImage));
      final sellerName = tester.getRect(find.text('Campus Store'));
      expect(
        productImage.right,
        lessThan(product.left),
      );
      expect(
        sellerName.top,
        lessThan(product.top),
      );
      expect(
        sellerName.top,
        lessThan(productImage.top),
      );
      expect(
        find.byIcon(Icons.store_outlined),
        findsOneWidget,
      );
      expect(
        tester.getRect(find.text('x2')).top,
        greaterThan(product.top),
      );
      expect(
        tester.getRect(find.byIcon(Icons.add_rounded)).left,
        greaterThan(product.left),
      );
      expect(find.text('\u20b1100.00'), findsNWidgets(2));
      expect(find.text('Cash on Pickup'), findsOneWidget);
      expect(find.text('Cash on Delivery'), findsOneWidget);
      expect(find.text('Delivery Fee'), findsNothing);
      expect(find.text('Platform Fee'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  for (final dark in [false, true]) {
    for (final width in [320.0, 430.0]) {
      testWidgets(
        'checkout wraps long content at $width with large text, dark=$dark',
        (tester) async {
          await pumpCheckout(
            tester,
            width: width,
            scale: 1.8,
            dark: dark,
            longText: true,
          );
          expect(tester.takeException(), isNull);
          final card = tester.widget<Container>(
            find
                .descendant(
                  of: find.byType(OrderSummaryCard),
                  matching: find.byType(Container),
                )
                .first,
          );
          expect((card.decoration as BoxDecoration).color, Colors.white);
          expect((card.decoration as BoxDecoration).border, isNull);
          expect((card.decoration as BoxDecoration).borderRadius, isNull);
          expect(tester.getSize(find.byType(OrderSummaryCard)).width, width);
          for (
            var i = 0;
            i < 20 &&
                find.text('Add note').hitTestable().evaluate().isEmpty;
            i++
          ) {
            await tester.drag(find.byType(ListView), const Offset(0, -200));
            await tester.pumpAndSettle();
          }
          expect(find.text('Add note').hitTestable(), findsOneWidget);
          await tester.tap(find.text('Add note'));
          await tester.pumpAndSettle();
          await tester.enterText(
            find.byType(TextField),
            'Please prepare for pickup.',
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  testWidgets('missing buyer fields do not invent identity placeholders', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    await pumpCheckout(tester);
    expect(find.byKey(const ValueKey('checkout-buyer-name')), findsNothing);
    expect(find.byKey(const ValueKey('checkout-buyer-card')), findsNothing);
    expect(
      find.byKey(const ValueKey('checkout-buyer-student-id')),
      findsNothing,
    );
    expect(find.byKey(const ValueKey('checkout-buyer-contact')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('cart checkout uses the same header, buyer and seller layout', (
    tester,
  ) async {
    await CartService.instance.addFromProduct(
      productId: 1,
      productName: 'Milk Tea',
      imageUrl: '',
      category: 'Food & Drinks',
      sellerName: 'Campus Store',
      sellerContact: '',
      basePrice: 50,
      selection: selection,
    );
    await tester.pumpWidget(const MaterialApp(home: CartScreen()));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Checkout All'));
    await tester.pumpAndSettle();
    expect(tester.widget<AppBar>(find.byType(AppBar).last).centerTitle, isTrue);
    expect(find.text('Lester Bulay'), findsOneWidget);
    expect(tester.getRect(find.byType(OrderSummaryCard)).left, 0);
    expect(
      tester.getSize(find.byType(OrderSummaryCard)).width,
      tester.view.physicalSize.width / tester.view.devicePixelRatio,
    );
    expect(
      tester.getRect(find.byKey(const ValueKey('checkout-buyer-card'))).bottom,
      lessThanOrEqualTo(tester.getRect(find.byType(OrderSummaryCard)).top),
    );
    expect(
      find.descendant(
        of: find.byType(OrderSummaryCard),
        matching: find.text('Campus Store'),
      ),
      findsOneWidget,
    );
    expect(find.text('Order Summary'), findsOneWidget);
    expect(find.text('x2'), findsOneWidget);
    expect(find.text('Delivery Fee'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('capture checkout on two phone sizes', (tester) async {
    final directory = Platform.environment['CHECKOUT_REVIEW_DIR'];
    if (directory == null) return;
    final fontPath = Platform.environment['CHECKOUT_REVIEW_FONT'];
    if (fontPath != null) {
      await tester.runAsync(() async {
        final loader = FontLoader('Roboto')
          ..addFont(
            Future.value(
              ByteData.sublistView(File(fontPath).readAsBytesSync()),
            ),
          );
        await loader.load();
        final icons = FontLoader('MaterialIcons')
          ..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'));
        await icons.load();
      });
    }
    for (final width in [320.0, 390.0]) {
      final key = GlobalKey();
      await pumpCheckout(tester, width: width, captureKey: key);
      await tester.runAsync(() async {
        final images = tester.widgetList<Image>(find.byType(Image));
        for (final image in images) {
          await precacheImage(image.image, key.currentContext!);
        }
      });
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.runAsync(() async {
        final boundary =
            key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
        final image = await boundary.toImage(pixelRatio: 2);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        Directory(directory).createSync(recursive: true);
        File(
          '$directory/checkout-${width.toInt()}.png',
        ).writeAsBytesSync(bytes!.buffer.asUint8List());
        image.dispose();
      });
      await tester.pumpWidget(const SizedBox.shrink());
    }
  });
}
