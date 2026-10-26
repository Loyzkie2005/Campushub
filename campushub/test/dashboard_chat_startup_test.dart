import 'dart:convert';

import 'package:campushub/module_app/screens/dashboard_screen.dart';
import 'package:campushub/module_app/services/chat_service.dart';
import 'package:campushub/module_app/services/seller_application_service.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'home_test_fixtures.dart';

class _BuyerAccess extends SellerApplicationService {
  @override
  Future<Map<String, dynamic>> status([String? ignoredLegacyId]) async => {
    'is_approved_seller': false,
  };
}

void main() {
  testWidgets(
    'offline optional chat does not escape Home startup; chat still reports errors',
    (tester) async {
      SharedPreferences.setMockInitialValues({
        'campushub_logged_user': jsonEncode({
          'id': 1,
          'first_name': 'Ana',
          'full_name': 'Ana Test',
          'user_type': 'student',
          'profile_completed': true,
        }),
        'campushub_chat_token': 'test-only-token',
      });
      addTearDown(() => ChatService.instance.disconnect());
      await http.runWithClient(
        () async {
          await tester.pumpWidget(
            MaterialApp(
              home: DashboardScreen(
                sellerService: _BuyerAccess(),
                serviceCatalog: HomeTestCatalog(),
                loadHomeProducts: homeProducts,
                loadHomeFacilities: homeFacilities,
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(find.text('Welcome Back, Ana'), findsOneWidget);
          expect(find.byType(FloatingBottomNavbar), findsOneWidget);
          expect(tester.takeException(), isNull);
          // Only the optional Home caller handles it; explicit chat requests must
          // continue to fail visibly in Messages instead of fabricating success.
          await expectLater(
            ChatService.instance.initialize(),
            throwsA(isA<ChatException>()),
          );
          await tester.pumpWidget(const SizedBox.shrink());
        },
        () => MockClient((request) async {
          if (request.url.port == 8001) throw http.ClientException('offline');
          return http.Response('{"products":[]}', 200);
        }),
      );
    },
  );
}
