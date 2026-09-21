import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:campushub/module_app/screens/facility_details_screen.dart';
import 'package:campushub/module_app/screens/facilities/facility_booking_screen.dart';
import 'package:campushub/module_app/screens/facilities/facility_booking_status_screen.dart';
import 'fixtures/facility_booking_fixture.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  Future<void> capture(
    WidgetTester tester,
    GlobalKey key,
    String fileName,
  ) async {
    await tester.runAsync(() async {
      final boundary =
          key.currentContext?.findRenderObject() as RenderRepaintBoundary?;
      if (boundary == null) return;
      final image = await boundary.toImage(pixelRatio: 2.0);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      if (byteData == null) return;
      final pngBytes = byteData.buffer.asUint8List();
      final dir = Directory('c:/Users/leste/Desktop/CAMPUSHUB/scratch/screenshots');
      if (!dir.existsSync()) dir.createSync(recursive: true);
      File('${dir.path}/$fileName').writeAsBytesSync(pngBytes);
    });
  }

  Widget wrap(Widget child, GlobalKey key) => MaterialApp(
    debugShowCheckedModeBanner: false,
    home: RepaintBoundary(
      key: key,
      child: child,
    ),
  );

  testWidgets('capture facility booking screens', (tester) async {
    tester.view.physicalSize = const Size(390 * 2, 844 * 2);
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final service = TestBookingService();

    // 1. Facility Details Screen
    final key1 = GlobalKey();
    await tester.pumpWidget(
      wrap(
        FacilityDetailsScreen(facility: testFacility, service: service),
        key1,
      ),
    );
    await tester.pumpAndSettle();
    await capture(tester, key1, '1_facility_details.png');

    // 2. Select Schedule Screen (Step 0)
    final key2 = GlobalKey();
    await tester.pumpWidget(
      wrap(
        FacilityBookingScreen(facility: testFacility, service: service),
        key2,
      ),
    );
    await tester.pumpAndSettle();
    // Select the 1:00 PM slot
    await tester.scrollUntilVisible(
      find.text('1:00 PM - 5:00 PM'),
      220,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('1:00 PM - 5:00 PM'));
    await tester.pumpAndSettle();
    await capture(tester, key2, '2_select_schedule.png');

    // 3. Booking Details Screen (Step 1)
    await tester.tap(find.text('Next: Booking Details'));
    await tester.pumpAndSettle();
    final values = {
      'Full Name': 'Lester Bulay',
      'Organization / Office': 'College of Information Technology',
      'Contact Number': '0912 345 6789',
      'Email Address': 'lesterbulay@ustp.edu.ph',
      'Event / Activity Name': 'Basketball Practice',
      'Purpose': 'Intramurals Practice',
      'Expected Number of Attendees': '40',
    };
    for (final entry in values.entries) {
      final field = find.byWidgetPredicate(
        (w) => w is TextField && w.decoration?.labelText == entry.key,
      );
      await tester.ensureVisible(field);
      await tester.enterText(field, entry.value);
    }
    await tester.ensureVisible(find.text('Sound System'));
    await tester.tap(find.text('Sound System'));
    await tester.pumpAndSettle();
    await capture(tester, key2, '3_booking_details.png');

    // 4. Review Booking Screen (Step 2)
    await tester.tap(find.text('Next: Review Booking'));
    await tester.pumpAndSettle();
    await capture(tester, key2, '4_review_booking.png');

    // 5. Booking Submitted Screen (Step 3)
    await tester.tap(find.text('Submit Booking Request'));
    await tester.pumpAndSettle();
    await capture(tester, key2, '5_booking_submitted.png');

    // 6. Booking Status (Pending)
    final key6 = GlobalKey();
    final pendingBooking = {
      'id': 'BK-2026-0002',
      'facility': {
        'id': testFacility.id,
        'name': testFacility.name,
        'facility_type': testFacility.facilityType,
        'status': testFacility.status,
        'capacity': testFacility.capacity,
        'rate': testFacility.rate,
        'price_type': testFacility.priceType,
        'booking_mode': testFacility.bookingMode,
        'image_url': testFacility.imageUrl,
        'location': testFacility.location,
        'description': testFacility.description,
        'amenities': testFacility.amenities,
        'terms_conditions': testFacility.termsConditions,
      },
      'date': '2026-08-30',
      'start': '13:00',
      'end': '17:00',
      'status': 'pending',
      'created_at': '2026-05-31T10:30:00Z',
      'total_amount': '2500.00',
      'paid_amount': '0.00',
      'payment_status': 'unpaid',
      'can_cancel': true,
      'can_view_slip': false,
      'details': {
        'full_name': 'Lester Bulay',
        'organization': 'College of Information Technology',
        'contact_number': '0912 345 6789',
        'email': 'lesterbulay@ustp.edu.ph',
        'event_name': 'Basketball Practice',
        'purpose': 'Intramurals Practice',
        'attendees': 40,
        'additional_requirements': ['Sound System'],
        'notes': 'We will also need a scoreboard.',
      },
      'receipts': [],
    };
    await tester.pumpWidget(
      wrap(
        FacilityBookingStatusScreen(booking: pendingBooking, service: service),
        key6,
      ),
    );
    await tester.pumpAndSettle();
    await capture(tester, key6, '6_booking_status_pending.png');

    // 7. Booking Status (Approved)
    final key7 = GlobalKey();
    final approvedBooking = {
      ...pendingBooking,
      'id': 'BK-APPROVED-0002',
      'status': 'approved',
      'can_cancel': false,
      'can_view_slip': true,
    };
    await tester.pumpWidget(
      wrap(
        FacilityBookingStatusScreen(booking: approvedBooking, service: service),
        key7,
      ),
    );
    await tester.pumpAndSettle();
    await capture(tester, key7, '7_booking_status_approved.png');

    await capture(tester, key7, '7_booking_status_approved.png');
  });
}
