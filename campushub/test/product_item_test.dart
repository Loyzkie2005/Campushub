import 'package:flutter_test/flutter_test.dart';
import 'package:campushub/module_app/models/product_item.dart';

void main() {
  test(
    'mobile seller references retain their namespace alongside web owners',
    () {
      final mobile = ProductItem.fromJson({
        'id': 10,
        'name': 'Mobile listing',
        'price': '20.00',
        'seller_id': 'mobile:42',
        'seller_ref': 'mobile:42',
      });
      final web = ProductItem.fromJson({
        'id': 11,
        'name': 'Web listing',
        'price': '20.00',
        'seller_id': 42,
        'seller_ref': 'admin:42',
      });
      expect(mobile.sellerId, isNull);
      expect(mobile.sellerRef, 'mobile:42');
      expect(mobile.sellerPhotoUrl, isEmpty);
      expect(web.sellerId, 42);
      expect(web.sellerRef, 'admin:42');
    },
  );
  test('parses product and variant image lists without duplicates', () {
    final product = ProductItem.fromJson({
      'id': 7,
      'name': 'Campus Shirt',
      'price': '250.00',
      'seller_photo_url': '/media/profile-photos/real-seller.jpg',
      'image_url': '/media/products/shirt-front.jpg',
      'images': [
        '/media/products/shirt-front.jpg',
        '/media/products/shirt-back.jpg',
      ],
      'customization_enabled': true,
      'customization_options': [
        {
          'name': 'Color',
          'selection': 'single',
          'required': true,
          'options': [
            {
              'name': 'Navy',
              'extra_price': '0',
              'image': '/media/products/shirt-navy.jpg',
            },
          ],
        },
      ],
    });

    expect(product.imageUrl, '/media/products/shirt-front.jpg');
    expect(product.sellerPhotoUrl, '/media/profile-photos/real-seller.jpg');
    expect(product.images, [
      '/media/products/shirt-front.jpg',
      '/media/products/shirt-back.jpg',
    ]);
    expect(
      product.customization.groups.single.options.single.imageUrl,
      '/media/products/shirt-navy.jpg',
    );
  });
}
