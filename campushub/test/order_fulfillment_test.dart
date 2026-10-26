import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:campushub/module_app/screens/seller_workspace_content.dart';
import 'package:campushub/module_app/services/order_service.dart';
import 'package:campushub/module_app/widgets/navigation/seller_drawer.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'seller_test_fixtures.dart';

void main() {
  setUpAll(() async {
    if (Platform.environment['SELLER_DELIVERY_REVIEW_DIR'] != null) {
      final bytes = ByteData.sublistView(
        File('assets/fonts/poppins/Poppins-Regular.ttf').readAsBytesSync(),
      );
      for (final family in ['Poppins', 'Roboto']) {
        await (FontLoader(family)..addFont(Future.value(bytes))).load();
      }
      await (FontLoader(
        'MaterialIcons',
      )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
    }
  });
  setUp(
    () => SharedPreferences.setMockInitialValues({
      'campushub_chat_token': 'isolated-token',
    }),
  );

  test(
    'fulfillment request carries authentication and stable retry key; only accepted orders enter history',
    () async {
      final requests = <http.Request>[];
      final payload = {
        'buyer_user_id': 1,
        'product_id': 2,
        'quantity': 1,
        'fulfillment_method': 'seller_delivery',
        'delivery_destination': 'Actual isolated destination',
      };
      final key = OrderService.requestKey();
      final client = MockClient((request) async {
        requests.add(request);
        return http.Response(
          jsonEncode(
            requests.length == 1
                ? {'error': 'Isolated rejection'}
                : {
                    'order': {'id': 1},
                  },
          ),
          requests.length == 1 ? 409 : 201,
        );
      });
      await http.runWithClient(() async {
        expect(
          await OrderService.placeOrder(order: payload, operationKey: key),
          isFalse,
        );
        expect(await OrderService.loadOrderHistory(), isEmpty);
        expect(
          await OrderService.placeOrder(order: payload, operationKey: key),
          isTrue,
        );
        expect(await OrderService.loadOrderHistory(), hasLength(1));
      }, () => client);
      expect(requests, hasLength(2));
      expect(requests.map((r) => r.headers['Idempotency-Key']).toSet(), {key});
      expect(
        requests.every(
          (r) => r.headers['Authorization'] == 'Bearer isolated-token',
        ),
        isTrue,
      );
      expect(jsonDecode(requests.last.body), payload);
      expect(payload.containsKey('payment_status'), isFalse);
    },
  );

  test(
    'an ambiguous POST failure is not automatically retried at another address',
    () async {
      var count = 0;
      await http.runWithClient(
        () async {
          expect(
            await OrderService.placeOrder(
              order: {'fulfillment_method': 'pickup'},
              operationKey: OrderService.requestKey(),
            ),
            isFalse,
          );
        },
        () => MockClient((_) async {
          count++;
          throw http.ClientException('Isolated connection failure');
        }),
      );
      expect(count, 1);
      expect(await OrderService.loadOrderHistory(), isEmpty);
    },
  );

  for (final width in [320.0, 844.0]) {
    testWidgets(
      'seller can confirm owned delivery without a payment action at $width',
      (tester) async {
        tester.view.physicalSize = Size(width, 950);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final data = sellerWorkspaceFixture();
        data['orders'] = [
          {
            'id': 51,
            'code': 'ISOLATED-51',
            'product_name': 'Actual test item',
            'buyer_name': 'Actual isolated buyer',
            'status': 'Ready for Seller Delivery',
            'status_key': 'ready_for_pickup',
            'payment_status': 'Unpaid',
            'quantity': 1,
            'total': '20.00',
            'created_at': '2026-10-25T08:00:00Z',
            'items': <Map<String, dynamic>>[],
            'fulfillment_method': 'seller_delivery',
            'fulfillment_label': 'Seller Delivery',
            'fulfillment_progress': 'Out for Seller Delivery',
            'delivery_destination': 'Actual isolated destination',
            'delivery_started_at': '2026-10-25T09:00:00Z',
            'delivered_at': null,
            'pickup_location': '',
          },
        ];
        String? recorded;
        var reloads = 0;
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: SellerWorkspaceContent(
                destination: SellerDestination.orders,
                data: data,
                onNavigate: (_) {},
                onAddProduct: () {},
                onCreateBundle: (_) {},
                onReload: () {
                  reloads++;
                },
                onPeriod: (_) {},
                onOrdersPage: (_) {},
                sellerFirstName: 'Test',
                onOrderProgress: (id, action) async {
                  expect(id, 51);
                  recorded = action;
                },
              ),
            ),
          ),
        );
        await tester.tap(find.text('ISOLATED-51'));
        await tester.pumpAndSettle();
        expect(find.text('Actual isolated destination'), findsOneWidget);
        expect(find.text('Pickup Location'), findsNothing);
        final button = find.text('Confirm Delivered');
        await tester.ensureVisible(button);
        final directory = Platform.environment['SELLER_DELIVERY_REVIEW_DIR'];
        if (directory != null) {
          await tester.pumpAndSettle();
          await tester.runAsync(() async {
            final boundary = tester.renderObject<RenderRepaintBoundary>(
              find.byType(RepaintBoundary).first,
            );
            final image = await boundary.toImage(pixelRatio: 1);
            final bytes = await image.toByteData(
              format: ui.ImageByteFormat.png,
            );
            Directory(directory).createSync(recursive: true);
            File(
              '$directory/seller-delivery-${width.toInt()}.png',
            ).writeAsBytesSync(bytes!.buffer.asUint8List());
            image.dispose();
          });
        }
        await tester.tap(button);
        await tester.pumpAndSettle();
        expect(
          find.textContaining('Payment remains unchanged'),
          findsOneWidget,
        );
        await tester.tap(find.text('Confirm').last);
        await tester.pumpAndSettle();
        expect(recorded, 'delivered');
        expect(reloads, 1);
        expect(tester.takeException(), isNull);
      },
    );
  }
}
