import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:campushub/module_app/screens/facilities/facility_booking_screen.dart';
import 'fixtures/facility_booking_fixture.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  Future<TestBookingService> open(WidgetTester tester, {double scale = 1}) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final service = TestBookingService();
    await tester.pumpWidget(MaterialApp(builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context).copyWith(textScaler: TextScaler.linear(scale)), child: child!),
      home: FacilityBookingScreen(facility: testFacility, service: service)));
    await tester.pumpAndSettle();
    return service;
  }

  Future<void> select(WidgetTester tester) async {
    await tester.scrollUntilVisible(find.text('1:00 PM - 5:00 PM'), 220, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text('1:00 PM - 5:00 PM'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next: Booking Details'));
    await tester.pumpAndSettle();
  }

  testWidgets('live conflict prevents advancing; blocked slot is disabled', (tester) async {
    final service = await open(tester);
    final blocked = tester.widget<OutlinedButton>(find.ancestor(of: find.text('8:00 AM - 12:00 PM'), matching: find.byType(OutlinedButton)).first);
    expect(blocked.onPressed, isNull);
    service.conflict = true;
    await select(tester);
    expect(find.text('Select Schedule'), findsOneWidget);
    expect(find.textContaining('no longer available'), findsOneWidget);
    expect(service.submissions, 0);
    expect(tester.takeException(), isNull);
  });

  testWidgets('request form validates, retains values, reviews and submits once', (tester) async {
    final service = await open(tester);
    await select(tester);
    await tester.tap(find.text('Next: Review Booking'));
    await tester.pumpAndSettle();
    expect(service.submissions, 0);
    final values = {'Full Name': 'Test Requestor', 'Organization / Office': 'Test Office',
      'Contact Number': '09171234567', 'Email Address': 'test@example.edu',
      'Event / Activity Name': 'Practice', 'Purpose': 'Sports practice', 'Expected Number of Attendees': '20'};
    for (final entry in values.entries) {
      final field = find.byWidgetPredicate((w) => w is TextField && w.decoration?.labelText == entry.key);
      await tester.ensureVisible(field);
      await tester.enterText(field, entry.value);
    }
    await tester.tap(find.text('Next: Review Booking'));
    await tester.pumpAndSettle();
    expect(find.text('Review Booking'), findsOneWidget);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Test Requestor'), findsOneWidget);
    await tester.tap(find.text('Next: Review Booking'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Submit Booking Request'));
    await tester.pumpAndSettle();
    expect(find.text('Booking Request Submitted!'), findsOneWidget);
    expect(service.submissions, 1);
    expect(service.submitted!['purpose'], 'Sports practice');
    expect(service.submitted!['request_key'], isNotEmpty);
    expect(tester.takeException(), isNull);
  });

  testWidgets('schedule and form fit a phone with enlarged text', (tester) async {
    await open(tester, scale: 1.3);
    expect(tester.takeException(), isNull);
    await select(tester);
    expect(tester.takeException(), isNull);
  });
}
