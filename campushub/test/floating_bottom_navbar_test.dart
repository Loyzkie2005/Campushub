import 'package:iconsax_flutter/iconsax_flutter.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:campushub/module_app/widgets/navigation/home_navigation_icon.dart';
import 'package:campushub/module_app/widgets/navigation/add_product_navigation_icon.dart';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final (size, scale) in [
    (const Size(320, 812), 2.0),
    (const Size(320, 812), 3.0),
    (const Size(390, 844), 1.0),
    (const Size(844, 390), 2.0),
  ]) {
    testWidgets('seller action fits $size/$scale and never selects a page', (
      tester,
    ) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      var selected = 2, added = 0;
      await tester.pumpWidget(
        MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: StatefulBuilder(
            builder: (_, update) => Scaffold(
              bottomNavigationBar: FloatingBottomNavbar(
                currentIndex: selected,
                onTap: (index) => update(() => selected = index),
                onCenterActionTap: () => added++,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final add = find.byKey(const Key('navbar-center-add-button'));
      expect(tester.getSize(add).shortestSide, greaterThanOrEqualTo(48));
      final circle = find.byKey(const Key('navbar-center-add-circle'));
      expect(find.byType(AddProductNavigationIcon), findsOneWidget);
      expect(tester.getSize(circle), const Size(56, 56));
      expect(
        (tester.widget<Container>(circle).decoration! as BoxDecoration).shape,
        BoxShape.circle,
      );
      final bar = tester.getRect(find.byKey(const Key('floating-navbar-pill')));
      expect(tester.getRect(circle).top, greaterThanOrEqualTo(bar.top));
      expect(
        tester.getRect(circle).top,
        lessThan(
          tester.getRect(find.byKey(const ValueKey('navbar-icon-0'))).top,
        ),
      );
      expect(
        (tester.getRect(find.text('Add Product')).top -
                tester.getRect(find.text('Home')).top)
            .abs(),
        lessThan(2),
      );
      expect(find.text('Profile'), findsNothing);
      for (final label in [
        'Home',
        'Marketplace',
        'Add Product',
        'Services',
        'Facilities',
      ]) {
        expect(find.text(label), findsOneWidget);
      }
      expect(
        tester.getCenter(find.text('Add Product')).dx,
        greaterThan(tester.getCenter(find.text('Marketplace')).dx),
      );
      expect(
        tester.getCenter(find.text('Add Product')).dx,
        lessThan(tester.getCenter(find.text('Services')).dx),
      );
      await tester.tap(add);
      await tester.pumpAndSettle();
      expect(added, 1);
      expect(selected, 2);
      for (var index = 0; index < 4; index++) {
        await tester.tap(find.byKey(ValueKey('navbar-item-$index')));
        await tester.pumpAndSettle();
        expect(selected, index);
      }
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'selection animation remains interruptible without moving the bar or renaming tabs',
    (tester) async {
      var selected = 0;
      await tester.pumpWidget(
        MaterialApp(
          home: StatefulBuilder(
            builder: (_, setState) => Scaffold(
              bottomNavigationBar: FloatingBottomNavbar(
                currentIndex: selected,
                onTap: (index) => setState(() => selected = index),
              ),
            ),
          ),
        ),
      );
      final bar = find.byKey(const Key('floating-navbar-pill'));
      final bounds = tester.getRect(bar);
      await tester.tap(find.byKey(const ValueKey('navbar-item-1')));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 60));
      final transform = tester.widget<Transform>(
        find.byKey(const ValueKey('navbar-shift-1')),
      );
      expect(transform.transform.storage[13], lessThan(0));
      expect(transform.transform.storage[13], greaterThan(-2));
      await tester.tap(find.byKey(const ValueKey('navbar-item-4')));
      await tester.pumpAndSettle();
      expect(selected, 4);
      expect(tester.getRect(bar), bounds);
      expect(
        tester.widget<Icon>(find.byKey(const ValueKey('navbar-icon-4'))).icon,
        Iconsax.user,
      );
      expect(
        tester
            .widget<Transform>(find.byKey(const ValueKey('navbar-shift-1')))
            .transform
            .storage[13],
        0,
      );
      expect(
        tester
            .widget<Transform>(find.byKey(const ValueKey('navbar-shift-4')))
            .transform
            .storage[13],
        -2,
      );
      expect(find.text('Marketplace'), findsOneWidget);
      expect(find.text('Services'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  test('navbar destinations pair outline icons with filled active icons', () {
    expect(FloatingBottomNavbar.default5Items.map((item) => item.icon), [
      Iconsax.home_copy,
      Iconsax.shop_copy,
      Iconsax.briefcase_copy,
      Iconsax.building_copy,
      Iconsax.user_copy,
    ]);
    expect(FloatingBottomNavbar.default5Items.map((item) => item.activeIcon), [
      Iconsax.home,
      Iconsax.shop,
      Iconsax.briefcase,
      Iconsax.building,
      Iconsax.user,
    ]);
    expect(
      FloatingBottomNavbar.defaultCenterActionItems.map((item) => item.icon),
      [
        Iconsax.home_copy,
        Iconsax.shop_copy,
        Iconsax.briefcase_copy,
        Iconsax.building_copy,
      ],
    );
  });
  test('navy text and icons retain readable palette contrast', () {
    double contrast(Color a, Color b) {
      final x = a.computeLuminance(), y = b.computeLuminance();
      return ((x > y ? x : y) + 0.05) / ((x < y ? x : y) + 0.05);
    }

    expect(
      contrast(const Color(0xFF1A1851), Colors.white),
      greaterThanOrEqualTo(4.5),
    );
    expect(
      contrast(
        Color.alphaBlend(const Color(0x9E1A1851), Colors.white),
        Colors.white,
      ),
      greaterThanOrEqualTo(4.5),
    );
  });
  testWidgets(
    'large text and reduced motion preserve selected indicator and touch targets',
    (tester) async {
      tester.view.physicalSize = const Size(320, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          home: MediaQuery(
            data: const MediaQueryData(
              textScaler: TextScaler.linear(2),
              disableAnimations: true,
            ),
            child: Scaffold(
              bottomNavigationBar: FloatingBottomNavbar(
                currentIndex: 2,
                onTap: (_) {},
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      // No top indicator line any more; active state is the filled icon.
      expect(find.byKey(const ValueKey('navbar-indicator-2')), findsNothing);
      expect(
        tester.widget<Icon>(find.byKey(const ValueKey('navbar-icon-2'))).icon,
        Iconsax.briefcase,
      );
      for (final item in FloatingBottomNavbar.default5Items) {
        final label = tester.widget<Text>(find.text(item.label));
        expect(label.textScaler, TextScaler.noScaling);
        expect(find.byTooltip(item.label), findsOneWidget);
      }
      expect(
        tester.getSize(find.byKey(const ValueKey('navbar-item-2'))).height,
        greaterThanOrEqualTo(48),
      );
      expect(
        tester
            .widget<TweenAnimationBuilder<double>>(
              find.byKey(const ValueKey('navbar-motion-2')),
            )
            .duration,
        Duration.zero,
      );
      expect(tester.takeException(), isNull);
    },
  );
  for (final width in [320.0, 390.0, 768.0]) {
    testWidgets('Floating navbar fits and switches tabs at width $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 800);
      tester.view.devicePixelRatio = 1;
      tester.view.viewPadding = const FakeViewPadding(bottom: 24);
      tester.view.padding = const FakeViewPadding(bottom: 24);
      addTearDown(tester.view.reset);
      final semantics = tester.ensureSemantics();
      var selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(brightness: Brightness.dark),
          home: StatefulBuilder(
            builder: (context, setState) => Scaffold(
              backgroundColor: Colors.white,
              body: const SizedBox.expand(key: Key('page-body')),
              bottomNavigationBar: FloatingBottomNavbar(
                currentIndex: selectedIndex,
                onTap: (index) => setState(() => selectedIndex = index),
              ),
            ),
          ),
        ),
      );

      final pillFinder = find.byKey(const Key('floating-navbar-pill'));
      final initialRect = tester.getRect(pillFinder);
      expect(initialRect.width, width);
      expect(initialRect.left, 0);
      expect(initialRect.right, width);
      expect(initialRect.bottom, 800);
      final ink = tester.widget<InkResponse>(
        find.byKey(const ValueKey('navbar-item-0')),
      );
      expect(ink.splashColor, const Color(0xFF1A1851).withValues(alpha: 0.08));
      expect(ink.focusColor, const Color(0xFF1A1851).withValues(alpha: 0.12));
      expect(
        tester.getRect(find.byKey(const Key('page-body'))).bottom,
        lessThanOrEqualTo(initialRect.top),
      );

      // Verify text labels are shown
      const labels = [
        'Home',
        'Marketplace',
        'Services',
        'Facilities',
        'Profile',
      ];
      for (final label in labels) {
        expect(find.text(label), findsOneWidget);
      }

      // Verify tapping each icon switches tabs
      for (var index = 0; index < 5; index++) {
        await tester.tap(find.byKey(ValueKey('navbar-item-$index')));
        await tester.pumpAndSettle();
        expect(selectedIndex, index);
        for (var itemIndex = 0; itemIndex < 5; itemIndex++) {
          if (itemIndex == 0) {
            final home = find.descendant(
              of: find.byKey(const ValueKey('navbar-item-0')),
              matching: find.byType(HomeNavigationIcon),
            );
            expect(home, findsOneWidget);
            expect(
              IconTheme.of(tester.element(home)).color,
              index == 0 ? const Color(0xFF1A1851) : const Color(0x9E1A1851),
            );
            expect(
              tester.widget<HomeNavigationIcon>(home).outlined,
              index != 0,
            );
            continue;
          }
          final icon = tester.widget<Icon>(
            find.descendant(
              of: find.byKey(ValueKey('navbar-item-$itemIndex')),
              matching: find.byType(Icon),
            ),
          );
          expect(
            icon.icon,
            itemIndex == index
                ? FloatingBottomNavbar
                      .default5Items[itemIndex]
                      .effectiveActiveIcon
                : FloatingBottomNavbar.default5Items[itemIndex].icon,
          );
          expect(
            icon.color,
            itemIndex == index
                ? const Color(0xFF1A1851)
                : const Color(0x9E1A1851),
          );
        }
        for (var itemIndex = 0; itemIndex < 5; itemIndex++) {
          final semanticsData = tester
              .getSemantics(find.byKey(ValueKey('navbar-semantics-$itemIndex')))
              .getSemanticsData();
          expect(
            semanticsData.label,
            FloatingBottomNavbar.default5Items[itemIndex].label,
          );
          expect(
            semanticsData.flagsCollection.isSelected == ui.Tristate.isTrue,
            itemIndex == index,
          );
        }
        expect(tester.getRect(pillFinder), initialRect);
        expect(tester.takeException(), isNull);
      }
      semantics.dispose();
    });
  }
}
