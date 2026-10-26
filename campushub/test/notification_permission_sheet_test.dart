import 'package:campushub/module_app/services/push_notification_service.dart';
import 'package:campushub/module_app/widgets/notification_permission_sheet.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _Push extends Fake implements PushNotificationService {
  @override
  final stateChanges = ValueNotifier<int>(0);
  @override
  bool hasSession = true;
  @override
  bool isSupported = true;
  @override
  bool isRegistered = false;
  @override
  AuthorizationStatus? authorizationStatus;
  @override
  String? lastError;
  int requests = 0;
  int settingsOpens = 0;
  bool settingsAvailable = true;

  @override
  Future<bool> openNotificationSettings() async {
    settingsOpens++;
    return settingsAvailable;
  }

  @override
  Future<void> requestPermissionFromUser() async {
    requests++;
    isRegistered = true;
    stateChanges.value++;
  }
}

void main() {
  testWidgets(
    'allowed permission shows the actual setup failure instead of generic sign-in advice',
    (tester) async {
      final service = _Push()
        ..authorizationStatus = AuthorizationStatus.authorized
        ..lastError =
            'Firebase could not register this device for notifications. Check the phone’s internet connection, then retry.';
      addTearDown(service.stateChanges.dispose);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: NotificationPermissionSheet(service: service)),
        ),
      );
      expect(find.text(service.lastError!), findsOneWidget);
      expect(find.text('Retry connection'), findsOneWidget);
      expect(find.textContaining('sign in again'), findsNothing);
    },
  );
  testWidgets(
    'already allowed permission offers registration retry instead of a new prompt',
    (tester) async {
      final service = _Push()
        ..authorizationStatus = AuthorizationStatus.authorized;
      addTearDown(service.stateChanges.dispose);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: NotificationPermissionSheet(service: service)),
        ),
      );
      expect(
        find.textContaining('permission is already allowed'),
        findsOneWidget,
      );
      expect(find.text('Retry connection'), findsOneWidget);
    },
  );

  testWidgets('bell panel enables notifications and reports actual readiness', (
    tester,
  ) async {
    final service = _Push();
    addTearDown(service.stateChanges.dispose);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NotificationPermissionSheet(service: service)),
      ),
    );
    expect(
      find.text('Mobile notifications are not available yet.'),
      findsNothing,
    );
    await tester.tap(find.text('Enable notifications'));
    await tester.pumpAndSettle();
    expect(service.requests, 1);
    expect(
      find.text('Notifications are enabled on this device.'),
      findsOneWidget,
    );
    expect(find.text('Enable notifications'), findsNothing);
  });

  testWidgets('denied permission explains the Android settings fallback', (
    tester,
  ) async {
    final service = _Push()..authorizationStatus = AuthorizationStatus.denied;
    addTearDown(service.stateChanges.dispose);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NotificationPermissionSheet(service: service)),
      ),
    );
    expect(
      find.textContaining('Phone Settings → Apps → CampusHub → Notifications'),
      findsOneWidget,
    );
    expect(find.text('Enable notifications'), findsOneWidget);
  });

  testWidgets('signed-out users cannot bind a notification device', (
    tester,
  ) async {
    final service = _Push()..hasSession = false;
    addTearDown(service.stateChanges.dispose);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NotificationPermissionSheet(service: service)),
      ),
    );
    expect(
      find.text('Sign in to enable notifications on this device.'),
      findsOneWidget,
    );
    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
      isNull,
    );
    expect(service.requests, 0);
  });

  testWidgets('permanent denial opens settings instead of repeating a prompt', (
    tester,
  ) async {
    final service = _Push()
      ..authorizationStatus = AuthorizationStatus.deniedPermanently;
    addTearDown(service.stateChanges.dispose);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NotificationPermissionSheet(service: service)),
      ),
    );
    expect(
      find.textContaining('Android will not show another'),
      findsOneWidget,
    );
    expect(find.text('Enable notifications'), findsNothing);
    await tester.tap(find.text('Open notification settings'));
    await tester.pumpAndSettle();
    expect(service.settingsOpens, 1);
    expect(service.requests, 0);
  });

  testWidgets('no-popup fallback opens settings even without a denied status', (
    tester,
  ) async {
    final service = _Push();
    addTearDown(service.stateChanges.dispose);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: NotificationPermissionSheet(service: service)),
      ),
    );
    await tester.tap(find.text('Open notification settings'));
    await tester.pumpAndSettle();
    expect(service.settingsOpens, 1);
    expect(service.requests, 0);
  });

  testWidgets(
    'unavailable native settings keeps manual recovery instructions',
    (tester) async {
      final service = _Push()..settingsAvailable = false;
      addTearDown(service.stateChanges.dispose);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: NotificationPermissionSheet(service: service)),
        ),
      );
      await tester.tap(find.text('Open notification settings'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Open Phone Settings → Apps'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
