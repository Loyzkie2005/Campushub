import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:campushub/module_app/models/facility_item.dart';
import 'package:campushub/module_app/screens/facility_details_screen.dart';
import 'package:campushub/module_app/screens/facilities/facility_booking_screen.dart';
import 'package:campushub/module_app/screens/facilities/facility_booking_status_screen.dart';
import 'fixtures/facility_booking_fixture.dart';

class _MockupCoveredCourtService extends TestBookingService {
  @override
  Future<List<Map<String, dynamic>>> slots(
    String facilityId,
    DateTime date,
  ) async => [
    {
      'start': '08:00',
      'end': '12:00',
      'label': '8:00 AM – 12:00 PM',
      'status': 'available',
    },
    {
      'start': '13:00',
      'end': '17:00',
      'label': '1:00 PM – 5:00 PM',
      'status': 'available',
    },
    {
      'start': '18:00',
      'end': '21:00',
      'label': '6:00 PM – 9:00 PM',
      'status': 'available',
    },
  ];
}

List<String> _loadCoveredCourtPhotoDataUrls() {
  const paths = [
    '../backend/media/upload/facilities/covered_court_CAMFACIL20261013F13A_1.jpg',
    '../backend/media/upload/facilities/covered_court_CAMFACIL20261013F13A_2.jpg',
    '../backend/media/upload/facilities/covered_court_CAMFACIL20261013F13A_3.jpg',
    '../backend/media/upload/facilities/covered_court_CAMFACIL20261013F13A_4.jpg',
    '../backend/media/upload/facilities/covered_court_CAMFACIL20261013F13A_5.jpg',
  ];
  final urls = <String>[];
  for (final p in paths) {
    final file = File(p);
    if (file.existsSync()) {
      final b64 = base64Encode(file.readAsBytesSync());
      urls.add('data:image/jpeg;base64,$b64');
    }
  }
  return urls;
}

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
      final dir = Directory(
        'c:/Users/leste/Desktop/CAMPUSHUB/scratch/screenshots',
      );
      if (!dir.existsSync()) dir.createSync(recursive: true);
      File('${dir.path}/$fileName').writeAsBytesSync(pngBytes);
    });
  }

  Widget wrap(Widget child, GlobalKey key) => MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: ThemeData(fontFamily: 'Poppins'),
    home: RepaintBoundary(key: key, child: child),
  );

  testWidgets('capture facility booking screens', (tester) async {
    late final List<String> courtPhotos;
    await tester.runAsync(() async {
      courtPhotos = _loadCoveredCourtPhotoDataUrls();
      final poppins = FontLoader('Poppins');
      for (final weight in ['Regular', 'Medium', 'SemiBold', 'Bold']) {
        poppins.addFont(
          rootBundle.load('assets/fonts/poppins/Poppins-$weight.ttf'),
        );
      }
      await poppins.load();
      final fallbackCandidates = [
        Platform.environment['FACILITY_REVIEW_ROBOTO'],
        'C:/Windows/Fonts/seguisb.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/arial.ttf',
      ];
      for (final candidate in fallbackCandidates) {
        if (candidate != null && File(candidate).existsSync()) {
          await (FontLoader('Roboto')..addFont(
                Future.value(
                  ByteData.sublistView(File(candidate).readAsBytesSync()),
                ),
              ))
              .load();
          break;
        }
      }
      await (FontLoader(
        'MaterialIcons',
      )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
    });

    final coveredCourtMockup = FacilityItem.fromJson({
      'id': 'COVERED-COURT-01',
      'name': 'Covered Court',
      'facility_type': 'covered_court',
      'facility_type_label': 'Covered Court',
      'status': 'available',
      'capacity': 500,
      'rate': '500.00',
      'price_type': 'hour',
      'booking_mode': 'slot',
      'image_url': courtPhotos.isNotEmpty ? courtPhotos.first : '',
      'images': courtPhotos,
      'location': 'Sports Complex / Multi-purpose Facility',
      'job_order_service': 'Facility Rental',
      'description':
          'A spacious multi-purpose covered court ideal for sports events, practices, student programs, school activities, and community gatherings.',
      'amenities': [
        'Basketball Court',
        'Bleachers',
        'Sound System',
        'Lighting',
        'Restrooms',
        'Parking Area',
      ],
      'terms_conditions':
          'Proper attire must be observed.\nKeep the facility clean.\nFollow schedule and booking guidelines.',
    });

    // 1A. Full-height Facility Details Mockup (390 x 1420 so all 8 sections are visible)
    tester.view.physicalSize = const Size(390 * 2, 1420 * 2);
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final mockupService = _MockupCoveredCourtService();
    final keyFull = GlobalKey();
    await tester.pumpWidget(
      wrap(
        FacilityDetailsScreen(
          facility: coveredCourtMockup,
          service: mockupService,
        ),
        keyFull,
      ),
    );
    await tester.pumpAndSettle();
    if (courtPhotos.isNotEmpty) {
      await tester.runAsync(() async {
        final ctx = keyFull.currentContext;
        if (ctx != null) {
          final bytes = base64Decode(courtPhotos.first.split(',').last);
          await precacheImage(MemoryImage(bytes), ctx);
        }
      });
      await tester.pumpAndSettle();
    }
    await capture(tester, keyFull, '1_facility_details_full.png');

    // 1B. Standard 390 x 844 phone viewport Facility Details Screen
    tester.view.physicalSize = const Size(390 * 2, 844 * 2);
    await tester.pumpAndSettle();
    await capture(tester, keyFull, '1_facility_details.png');

    final service = TestBookingService();

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
    await tester.pumpAndSettle();
    final soundSystem = find.widgetWithText(CheckboxListTile, 'Sound System');
    await tester.tap(soundSystem);
    await tester.pumpAndSettle();
    expect(tester.widget<CheckboxListTile>(soundSystem).value, isTrue);
    await tester.drag(find.byType(ListView).first, const Offset(0, 2500));
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
  });
}
