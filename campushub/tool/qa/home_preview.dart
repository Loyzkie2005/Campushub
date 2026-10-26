// Emulator-only QA: production screen with isolated test fixtures, no live account.
import 'package:flutter/material.dart';
import 'package:campushub/module_app/screens/dashboard_screen.dart';
import '../../test/home_test_fixtures.dart';

void main() => runApp(
  MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorSchemeSeed: const Color(0xFF1A1851),
      fontFamily: 'Roboto',
    ),
    home: DashboardScreen(
      serviceCatalog: HomeTestCatalog(),
      loadHomeProducts: homeProducts,
      loadHomeFacilities: homeFacilities,
    ),
  ),
);
