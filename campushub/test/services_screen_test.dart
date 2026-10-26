import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:campushub/module_app/models/service_item.dart';
import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/screens/services_screen.dart';
import 'package:campushub/module_app/services/service_catalog.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

ServiceItem record(String kind, String name) => ServiceItem.fromJson({
  'id': kind,
  'name': name,
  'facility_type': kind,
  'status': 'active',
  'category_label': 'Configured category',
  'description': 'Recorded service description',
  'location': 'Configured office',
  'requirements': 'Recorded requirements',
  'terms_conditions': 'Recorded terms',
  'information': [
    {'label': 'Pricing', 'value': 'Recorded rate'},
  ],
});

class FakeCatalog extends ServiceCatalog {
  FakeCatalog(this.rows);
  List<ServiceItem> rows;
  int loads = 0;
  bool fail = false;
  bool detailFail = false;
  Completer<List<ServiceItem>>? pending;
  @override
  Future<List<ServiceItem>> fetchServices() async {
    loads++;
    if (fail) throw const ServiceCatalogException('offline');
    return pending != null ? pending!.future : rows;
  }

  @override
  Future<ServiceItem> fetchService(String id) async {
    if (detailFail) throw const ServiceCatalogException('no longer active');
    return rows.firstWhere((row) => row.id == id);
  }
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  for (final width in [320.0, 390.0, 844.0]) {
    testWidgets('service details and distinct guidance fit at $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, width == 844 ? 390 : 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final rows = [
        record('food_analysis', 'Configured Lab'),
        record('training_kitchen', 'Configured BPP'),
        record('lease_space', 'Configured Lease'),
      ];
      final catalog = FakeCatalog(rows);
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(brightness: Brightness.dark),
          home: Scaffold(body: ServicesPage(catalog: catalog)),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Available Services'), findsOneWidget);
      for (final row in rows) {
        await tester.enterText(
          find.byKey(const ValueKey('service-search')),
          row.name,
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(row.name).last);
        await tester.pumpAndSettle();
        expect(find.text('Service Details'), findsOneWidget);
        await tester.tap(find.text(row.actionLabel));
        await tester.pumpAndSettle();
        expect(
          find.text(
            'Online submission is not available yet. No request has been submitted.',
          ),
          findsOneWidget,
        );
        expect(find.text('Message Office'), findsOneWidget);
        expect(
          find.textContaining(switch (row.kind) {
            'laboratory' => 'sample quantity',
            'assessment' => 'assessment eligibility',
            _ => 'available commercial spaces',
          }),
          findsOneWidget,
        );
        await tester.ensureVisible(find.text('Close'));
        await tester.tap(find.text('Close'));
        await tester.pumpAndSettle();
        await tester.pageBack();
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
      }
    });
  }
  testWidgets('loading, empty, search miss, error and retry remain distinct', (
    tester,
  ) async {
    final catalog = FakeCatalog([])..pending = Completer<List<ServiceItem>>();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ServicesPage(catalog: catalog)),
      ),
    );
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    catalog.pending!.complete([]);
    await tester.pumpAndSettle();
    expect(find.text('No services are currently available.'), findsOneWidget);
    await tester.pumpWidget(const SizedBox.shrink());
    catalog.pending = null;
    catalog.fail = true;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ServicesPage(catalog: catalog)),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('No services are currently available.'), findsNothing);
    expect(find.text('Retry'), findsOneWidget);
    catalog.fail = false;
    catalog.rows = [record('food_analysis', 'Configured Lab')];
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('service-search')),
      'nonmatching search',
    );
    await tester.pumpAndSettle();
    expect(find.text('No services match your search.'), findsOneWidget);
  });
  testWidgets(
    'details revalidate active state and hide request action on failure',
    (tester) async {
      final catalog = FakeCatalog([record('food_analysis', 'Configured Lab')])
        ..detailFail = true;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: ServicesPage(catalog: catalog)),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Configured Lab'));
      await tester.pumpAndSettle();
      expect(find.text('How to Request This Service'), findsNothing);
      expect(find.text('Retry'), findsOneWidget);
      catalog.detailFail = false;
      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();
      expect(find.text('How to Request This Service'), findsOneWidget);
    },
  );
  testWidgets('Services search and loaded state survive switching tabs', (
    tester,
  ) async {
    final catalog = FakeCatalog([record('food_analysis', 'Configured Lab')]);
    await tester.pumpWidget(
      MaterialApp(
        home: DashboardScreen(initialTab: 2, serviceCatalog: catalog),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('service-search')), 'Lab');
    await tester.tap(find.byKey(const ValueKey('navbar-item-4')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('navbar-item-2')));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<EditableText>(
            find.descendant(
              of: find.byKey(const ValueKey('service-search')),
              matching: find.byType(EditableText),
            ),
          )
          .controller
          .text,
      'Lab',
    );
    expect(find.text('Configured Lab'), findsOneWidget);
    expect(catalog.loads, 1);
    expect(
      tester
          .widget<FloatingBottomNavbar>(find.byType(FloatingBottomNavbar))
          .currentIndex,
      2,
    );
    await tester.pumpWidget(const SizedBox.shrink());
  });
  for (final width in [320.0, 390.0]) {
    testWidgets('Services tab fits large text and reduced motion at $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final catalog = FakeCatalog([
        record('food_analysis', 'Configured Laboratory Service'),
      ]);
      final capture = GlobalKey();
      final directory = Platform.environment['SERVICES_REVIEW_DIR'];
      if (directory != null) {
        await tester.runAsync(() async {
          final font = FontLoader('Roboto')
            ..addFont(
              Future.value(
                ByteData.sublistView(
                  File(
                    'C:/flutter/bin/cache/artifacts/material_fonts/roboto-regular.ttf',
                  ).readAsBytesSync(),
                ),
              ),
            );
          await font.load();
          final icons = FontLoader('packages/lucide_icons/Lucide')
            ..addFont(
              rootBundle.load('packages/lucide_icons/assets/lucide.ttf'),
            );
          await icons.load();
        });
      }
      await tester.pumpWidget(
        RepaintBoundary(
          key: capture,
          child: MaterialApp(
            theme: ThemeData(fontFamily: 'Roboto'),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(
                textScaler: TextScaler.linear(1.5),
                disableAnimations: true,
              ),
              child: child!,
            ),
            home: DashboardScreen(initialTab: 2, serviceCatalog: catalog),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final tab = find.byKey(const ValueKey('navbar-item-2'));
      expect(tester.getSize(tab).height, greaterThanOrEqualTo(44));
      // The navbar implementation may use implicit animation or a static icon.
      // Any animation inside this destination must honor reduced motion.
      for (final animation in tester.widgetList<ImplicitlyAnimatedWidget>(
        find.descendant(
          of: tab,
          matching: find.byWidgetPredicate(
            (widget) => widget is ImplicitlyAnimatedWidget,
          ),
        ),
      )) {
        expect(animation.duration, Duration.zero);
      }
      expect(find.text('Configured Laboratory Service'), findsOneWidget);
      expect(tester.takeException(), isNull);
      if (directory != null) {
        await tester.runAsync(() async {
          final boundary =
              capture.currentContext!.findRenderObject()!
                  as RenderRepaintBoundary;
          final image = await boundary.toImage(pixelRatio: 1);
          final data = await image.toByteData(format: ui.ImageByteFormat.png);
          Directory(directory).createSync(recursive: true);
          File(
            '$directory/services-${width.toInt()}.png',
          ).writeAsBytesSync(data!.buffer.asUint8List());
          image.dispose();
        });
      }
      await tester.pumpWidget(const SizedBox.shrink());
    });
  }
}
