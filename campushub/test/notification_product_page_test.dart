import 'dart:convert';
import 'package:campushub/module_app/models/product_notification_target.dart';
import 'package:campushub/module_app/screens/notification_product_page.dart';
import 'package:campushub/module_app/screens/product_details_screen.dart';
import 'package:campushub/module_app/services/seller_application_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _Products extends SellerApplicationService {
  int calls = 0;
  List<Map<String, dynamic>> rows = [
    {
      'id': 7,
      'name': 'Reviewed Item',
      'price': '25',
      'approval_status': 'rejected',
      'rejection_reason': 'Please update the photo.',
      'stock': 10,
      'rating': 4.5,
      'reviews_count': 2,
    },
  ];
  @override
  Future<List<Map<String, dynamic>>> products() async {
    calls++;
    return rows;
  }
}

void main() {
  const target = ProductNotificationTarget(
    productId: 7,
    recipientId: 1,
    type: 'product_rejected',
    deliveryId: '22',
  );
  void session(int id) => SharedPreferences.setMockInitialValues({
    'campushub_logged_user': jsonEncode({
      'id': id,
      'username': 'isolated-owner',
    }),
    'campushub_chat_token': 'isolated-bearer',
  });
  testWidgets(
    'tap loads actual owned rejected product using existing details without checkout',
    (tester) async {
      session(1);
      final products = _Products();
      await tester.pumpWidget(
        MaterialApp(
          home: NotificationProductPage(target: target, service: products),
        ),
      );
      await tester.pumpAndSettle();
      final screen = tester.widget<ProductDetailsScreen>(
        find.byType(ProductDetailsScreen),
      );
      expect(screen.id, 7);
      expect(screen.name, 'Reviewed Item');
      expect(screen.rating, 4.5);
      expect(screen.reviewsCount, 2);
      expect(screen.ownerView, isTrue);
      expect(screen.isPurchasable, isFalse);
      expect(find.text('Please update the photo.'), findsOneWidget);
      expect(find.text('Buy Now'), findsNothing);
      expect(products.calls, 1);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
  testWidgets('different account never fetches private product details', (
    tester,
  ) async {
    session(2);
    final products = _Products();
    await tester.pumpWidget(
      MaterialApp(
        home: NotificationProductPage(target: target, service: products),
      ),
    );
    await tester.pumpAndSettle();
    expect(
      find.text('This notification belongs to another account.'),
      findsOneWidget,
    );
    expect(products.calls, 0);
  });
  testWidgets('deleted/absent owned product shows honest unavailable state', (
    tester,
  ) async {
    session(1);
    final products = _Products()..rows = [];
    await tester.pumpWidget(
      MaterialApp(
        home: NotificationProductPage(target: target, service: products),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('This product is no longer available.'), findsOneWidget);
  });
}
