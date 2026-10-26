import 'package:campushub/module_app/services/auth_service.dart';
import 'package:campushub/module_app/widgets/navigation/seller_drawer.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';

void main() {
  for (final (size, scale) in [
    (const Size(375, 812), 1.0),
    (const Size(320, 812), 2.0),
    (const Size(844, 390), 2.0),
  ]) {
    testWidgets(
      'seller drawer labels, scrolling and selection fit $size/$scale',
      (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        var selected = SellerDestination.overview;
        await tester.pumpWidget(
          MaterialApp(
            theme: ThemeData(
              brightness: size.width > 800 ? Brightness.dark : Brightness.light,
            ),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(
                textScaler: TextScaler.linear(scale),
                disableAnimations: true,
              ),
              child: child!,
            ),
            home: StatefulBuilder(
              builder: (context, update) => Scaffold(
                body: SellerDrawer(
                  user: AuthUser.fromJson({
                    'id': 71,
                    'full_name': 'Test Student Seller',
                    'program': 'BFPT',
                    'year_section': '2-A',
                    'email': 'student.seller@example.edu',
                  }),
                  selected: selected,
                  onSelected: (destination) =>
                      update(() => selected = destination),
                ),
              ),
            ),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.text('Test Student Seller'), findsOneWidget);
        expect(find.text('BFPT'), findsOneWidget);
        expect(find.text('Year / Section: 2-A'), findsOneWidget);
        expect(
          tester
              .widget<Text>(find.text('Test Student Seller'))
              .style
              ?.fontFamily,
          'Montserrat',
        );
        expect(
          tester.widget<Text>(find.text('BFPT')).style?.fontFamily,
          'Montserrat',
        );
        expect(
          tester.widget<Drawer>(find.byType(Drawer)).backgroundColor,
          Colors.white,
        );
        expect(find.text('Approved Seller'), findsNothing);
        expect(find.text('My Profile'), findsNothing);
        expect(find.text('My Bundle Suggestions'), findsNothing);
        expect(find.text('student.seller@example.edu'), findsOneWidget);
        expect(find.byType(CircleAvatar), findsOneWidget);
        expect(
          find.descendant(
            of: find.byKey(const ValueKey('seller-profile-avatar')),
            matching: find.text('T'),
          ),
          findsOneWidget,
        );
        const labels = [
          'Dashboard',
          'My Products',
          'Inventory',
          'My Bundles',
          'Orders',
          'Suggested Product Bundles',
          'Sales Analytics',
          'Messages',
          'Account Settings',
        ];
        for (var i = 0; i < labels.length; i++) {
          final label = find.text(labels[i]);
          await tester.scrollUntilVisible(label, 100);
          await Scrollable.ensureVisible(tester.element(label), alignment: .5);
          await tester.pumpAndSettle();
          await tester.tap(label);
          await tester.pumpAndSettle();
          expect(tester.widget<Text>(label).style?.fontFamily, 'Poppins');
          expect(tester.widget<Text>(label).style?.fontVariations, isNull);
          expect(selected, SellerDrawer.drawerDestinations[i]);
          final target = find.byKey(ValueKey('seller-menu-${selected.name}'));
          expect(tester.getSize(target).height, greaterThanOrEqualTo(48));
          expect(
            find.descendant(
              of: target,
              matching: find.byIcon(Iconsax.arrow_right_3_copy),
            ),
            findsOneWidget,
          );
          expect(tester.takeException(), isNull);
        }
        await tester.scrollUntilVisible(find.text('SETTINGS'), 100);
        expect(find.text('SETTINGS'), findsOneWidget);
        expect(find.text('Back to CampusHub'), findsNothing);
        await tester.scrollUntilVisible(find.text('COMMUNICATION'), -100);
        expect(find.text('COMMUNICATION'), findsOneWidget);
        expect(find.text('Notifications'), findsNothing);
        expect(find.byType(TextField), findsNothing);
      },
    );
  }
}
