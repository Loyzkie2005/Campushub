import 'package:campushub/module_app/models/product_notification_target.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'valid approval/rejection target round-trips without arbitrary routes',
    () {
      for (final type in ['product_approved', 'product_rejected']) {
        final data = {
          'type': type,
          'product_id': '12',
          'recipient_id': '3',
          'delivery_id': '41',
        };
        final target = ProductNotificationTarget.fromJson(data)!;
        expect(target.productId, 12);
        expect(target.toJson(), data);
      }
    },
  );
  test('malformed IDs and unrelated notification types are ignored', () {
    final valid = {
      'type': 'product_approved',
      'product_id': '12',
      'recipient_id': '3',
      'delivery_id': '41',
    };
    for (final change in [
      {'product_id': '-1'},
      {'recipient_id': 'missing'},
      {'type': '/admin'},
      {'delivery_id': 'private arbitrary payload'},
      {'delivery_id': ''},
    ]) {
      expect(ProductNotificationTarget.fromJson({...valid, ...change}), isNull);
    }
  });
}
