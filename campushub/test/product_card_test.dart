import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:campushub/module_app/models/product_item.dart';

void main() {
  testWidgets('renders soft product card container with Hot and New badges cleanly without overflow', (tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 2.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    const hotProduct = ProductItem(
      'Nike Air Zoom Pegasus',
      '₱119.99',
      Icons.shopping_bag_outlined,
      Color(0xFF1A1851),
      id: 1,
      category: 'Top Picks',
      seller: 'Campus Store',
    );

    const newProduct = ProductItem(
      'Adidas Predator Elite',
      '₱149.99',
      Icons.shopping_bag_outlined,
      Color(0xFF1A1851),
      id: 2,
      category: 'Footwear',
      seller: 'Campus Store',
      rating: 4.8,
      reviewsCount: 124,
    );

    Widget buildCard(ProductItem product) {
      final isHot = product.soldCount > 0 ||
          ((product.id ?? product.name.hashCode.abs()) % 2 == 1);
      final badgeLabel = isHot ? 'Hot' : 'New';

      return Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF1A1851).withValues(alpha: 0.05),
              blurRadius: 14,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        foregroundDecoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(17),
                ),
                child: Container(
                  color: const Color(0xFFF4F5F7),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Positioned(
                        top: 8,
                        left: 8,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                          decoration: BoxDecoration(
                            color: isHot ? const Color(0xFFFCB316) : const Color(0xFF1A1851),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            badgeLabel,
                            style: TextStyle(
                              color: isHot ? const Color(0xFF1A1851) : Colors.white,
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.seller.trim().isNotEmpty
                        ? product.seller.trim()
                        : 'Campus Marketplace',
                  ),
                  const SizedBox(height: 2),
                  Text(product.name),
                  if (product.category.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(product.category),
                  ],
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 4, 12, 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(product.price),
                        if (product.hasReviews) ...[
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              for (int i = 1; i <= 5; i++)
                                Icon(
                                  i <= (product.rating ?? 0).floor()
                                      ? Icons.star
                                      : (i - (product.rating ?? 0) < 1 &&
                                              (product.rating ?? 0) -
                                                      (product.rating ?? 0)
                                                          .floor() >=
                                                  0.3
                                          ? Icons.star_half
                                          : Icons.star_border),
                                  size: 12,
                                  color: const Color(0xFFFCB316),
                                ),
                              const SizedBox(width: 3),
                              Text(
                                '(${product.reviewsCount})',
                                style: const TextStyle(
                                  fontSize: 10,
                                  color: Color(0xFF94A3B8),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                  const Icon(LucideIcons.shoppingBag),
                ],
              ),
            ),
          ],
        ),
      );
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Padding(
            padding: const EdgeInsets.all(16),
            child: GridView.count(
              crossAxisCount: 2,
              mainAxisSpacing: 14,
              crossAxisSpacing: 14,
              childAspectRatio: 0.68,
              children: [
                buildCard(hotProduct),
                buildCard(newProduct),
              ],
            ),
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Campus Store'), findsNWidgets(2));
    expect(find.text('Nike Air Zoom Pegasus'), findsOneWidget);
    expect(find.text('Adidas Predator Elite'), findsOneWidget);
    expect(find.text('Top Picks'), findsOneWidget);
    expect(find.text('Footwear'), findsOneWidget);
    expect(find.text('Hot'), findsOneWidget);
    expect(find.text('New'), findsOneWidget);
    expect(find.byIcon(LucideIcons.shoppingBag), findsNWidgets(2));
    // Verify no fake review placeholder for product without reviews
    expect(find.text('(5.0)'), findsNothing);
    // Verify reviews only shown when product has reviews
    expect(find.text('(124)'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('card with foregroundDecoration allows taps on card and action buttons', (tester) async {
    var cardTapped = false;
    var cartTapped = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Center(
            child: SizedBox(
              width: 180,
              height: 240,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
                ),
                foregroundDecoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
                ),
                child: Column(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        key: const ValueKey('card_tap'),
                        onTap: () => cardTapped = true,
                        child: Container(color: Colors.white),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(LucideIcons.shoppingBag),
                      onPressed: () => cartTapped = true,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('card_tap')));
    expect(cardTapped, isTrue);

    await tester.tap(find.byType(IconButton));
    expect(cartTapped, isTrue);
  });

  test('ProductItem.fromJson formats price using Philippine peso symbol ₱', () {
    final itemNumeric = ProductItem.fromJson({
      'name': 'Test Item',
      'price': 150,
      'category': 'Snacks',
    });
    expect(itemNumeric.price, '₱150.00');
    expect(itemNumeric.basePrice, 150.0);

    final itemWithDisplay = ProductItem.fromJson({
      'name': 'Variant Item',
      'price': 50,
      'price_display': '₱50.00 – ₱70.00',
      'category': 'Apparel',
    });
    expect(itemWithDisplay.price, '₱50.00 – ₱70.00');
    expect(itemWithDisplay.basePrice, 50.0);
  });
}

