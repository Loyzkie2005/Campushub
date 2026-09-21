import 'package:flutter_test/flutter_test.dart';
import 'package:campushub/module_app/models/product_item.dart';

void main() {
  test('parses product and variant image lists without duplicates', () {
    final product = ProductItem.fromJson({
      'id': 7,
      'name': 'Campus Shirt',
      'price': '250.00',
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
