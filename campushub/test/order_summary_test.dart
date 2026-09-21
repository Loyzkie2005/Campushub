import 'package:campushub/module_app/models/product_customization.dart';
import 'package:campushub/module_app/widgets/order_summary_widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('order summary shows item details and accepts a seller message', (
    tester,
  ) async {
    final messageController = TextEditingController();
    addTearDown(messageController.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: OrderSummaryCard(
              items: const [
                OrderSummaryLineItem(
                  productName: 'Hotdog',
                  sellerName: 'Campus Store',
                  imageUrl: '',
                  quantity: 1,
                  unitPrice: 65,
                  selections: [
                    SelectedCustomization(
                      group: 'Size',
                      option: 'Medium',
                      extraPrice: 25,
                    ),
                  ],
                ),
              ],
              subtotal: 65,
              sellerMessageController: messageController,
            ),
          ),
        ),
      ),
    );

    expect(find.text('Hotdog'), findsOneWidget);
    expect(find.text('Size: Medium (+\u20b125.00)'), findsOneWidget);
    expect(find.text('x1'), findsOneWidget);
    expect(find.text('Payment Methods'), findsOneWidget);
    expect(find.text('Cash on Pickup'), findsOneWidget);
    expect(find.text('Cash on Delivery'), findsOneWidget);
    expect(find.text('Order Summary'), findsOneWidget);
    expect(find.text('Delivery Fee'), findsNothing);
    expect(find.text('Platform Fee'), findsNothing);
    expect(find.text('Add note'), findsOneWidget);

    final msgRect = tester.getRect(find.text('Add note'));
    final payRect = tester.getRect(find.text('Payment Methods'));
    final orderSummaryRect = tester.getRect(find.text('Order Summary'));
    final subtotalRect = tester.getRect(find.text('Subtotal'));

    expect(payRect.top, greaterThan(msgRect.bottom));
    expect(orderSummaryRect.top, greaterThan(payRect.bottom));
    expect(subtotalRect.top, greaterThan(orderSummaryRect.bottom));

    await tester.tap(find.text('Add note'));
    await tester.pumpAndSettle();

    expect(find.text('Add an optional note for the seller'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'No ketchup, please.');
    expect(messageController.text, 'No ketchup, please.');
  });

  testWidgets('quantity controller responds to plus and minus taps', (
    tester,
  ) async {
    var changedQty = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: OrderSummaryCard(
            items: const [
              OrderSummaryLineItem(
                productName: 'Hotdog',
                imageUrl: '',
                quantity: 2,
                unitPrice: 65,
                selections: [],
              ),
            ],
            subtotal: 130,
            onQuantityChanged: (_, qty) => changedQty = qty,
          ),
        ),
      ),
    );

    expect(find.text('x2'), findsOneWidget);
    expect(find.byIcon(Icons.remove_rounded), findsOneWidget);
    expect(find.byIcon(Icons.add_rounded), findsOneWidget);

    await tester.tap(find.byIcon(Icons.add_rounded));
    await tester.pump();
    expect(changedQty, 3);

    await tester.tap(find.byIcon(Icons.remove_rounded));
    await tester.pump();
    expect(changedQty, 1);
  });

  testWidgets('payment method radio toggles to Cash on Delivery', (
    tester,
  ) async {
    String? selected;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: OrderSummaryCard(
            items: const [
              OrderSummaryLineItem(
                productName: 'Hotdog',
                imageUrl: '',
                quantity: 1,
                unitPrice: 65,
                selections: [],
              ),
            ],
            subtotal: 65,
            onPaymentMethodChanged: (method) => selected = method,
          ),
        ),
      ),
    );

    expect(find.text('Cash on Delivery'), findsOneWidget);
    await tester.tap(find.text('Cash on Delivery'));
    await tester.pump();
    expect(selected, 'Cash on Delivery');
  });
}
