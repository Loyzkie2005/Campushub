import 'package:flutter/material.dart';
import 'package:campushub/module_app/screens/facilities/facility_booking_screen.dart';
import 'package:campushub/module_app/screens/facility_details_screen.dart';
import 'fixtures/facility_booking_fixture.dart';

// Emulator-only visual fixture, separate from the production entry point.
void main() => runApp(MaterialApp(debugShowCheckedModeBanner: false,
  home: const String.fromEnvironment('PREVIEW') == 'schedule'
    ? FacilityBookingScreen(facility: testFacility, service: TestBookingService())
    : FacilityDetailsScreen(facility: testFacility, service: TestBookingService())));
