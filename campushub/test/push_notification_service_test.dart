import 'dart:async';
import 'dart:convert';

import 'package:campushub/module_app/services/push_notification_service.dart';
import 'package:campushub/module_app/services/push_device_api.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _Settings extends Fake implements NotificationSettings {
  _Settings(this.authorizationStatus);

  @override
  final AuthorizationStatus authorizationStatus;
}

class _Messaging extends Fake implements FirebaseMessaging {
  AuthorizationStatus status = AuthorizationStatus.authorized;
  int permissionRequests = 0;
  int registrations = 0;
  int unregistrations = 0;
  bool failRegistration = false;
  Object? registrationError;
  bool failPermission = false;
  AuthorizationStatus permissionResult = AuthorizationStatus.authorized;
  Completer<void>? permissionGate;
  final registered = StreamController<String>.broadcast(sync: true);
  final unregistered = StreamController<String>.broadcast(sync: true);

  @override
  Stream<String> get onRegistered => registered.stream;

  @override
  Stream<String> get onUnregistered => unregistered.stream;

  @override
  Future<NotificationSettings> getNotificationSettings() async =>
      _Settings(status);

  @override
  Future<RemoteMessage?> getInitialMessage() async => null;

  @override
  Future<NotificationSettings> requestPermission({
    bool alert = true,
    bool announcement = false,
    bool badge = true,
    bool carPlay = false,
    bool criticalAlert = false,
    bool provisional = false,
    bool sound = true,
    bool providesAppNotificationSettings = false,
  }) async {
    permissionRequests++;
    await permissionGate?.future;
    if (failPermission) throw StateError('Isolated permission channel failure');
    status = permissionResult;
    return _Settings(status);
  }

  @override
  Future<void> register({
    String? vapidKey,
    String? serviceWorkerScriptPath,
  }) async {
    registrations++;
    if (registrationError != null) throw registrationError!;
    if (failRegistration) throw StateError('Isolated registration failure');
    registered.add('isolated-installation-id');
  }

  @override
  Future<void> unregister() async {
    unregistrations++;
    unregistered.add('isolated-installation-id');
  }

  Future<void> close() async {
    await registered.close();
    await unregistered.close();
  }
}

class _DeviceApi extends Fake implements PushDeviceApi {
  final operations = <String>[];
  Completer<void>? bindGate;
  Object? bindError;

  @override
  Future<bool> bind(PushSession session, String fid) async {
    operations.add('bind:${session.userId}:$fid');
    await bindGate?.future;
    if (bindError != null) throw bindError!;
    return true;
  }

  @override
  Future<bool> unbind(PushSession session, String fid) async {
    operations.add('unbind:${session.userId}:$fid');
    return true;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _Messaging messaging;
  late StreamController<RemoteMessage> messages;
  late PushNotificationService service;
  late _DeviceApi deviceApi;
  var initializations = 0;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    initializations = 0;
    messaging = _Messaging();
    messages = StreamController<RemoteMessage>.broadcast(sync: true);
    deviceApi = _DeviceApi();
    service = PushNotificationService(
      messaging: messaging,
      foregroundMessages: messages.stream,
      initializeFirebase: () async => initializations++,
      supportsPlatform: () => true,
      deviceApi: deviceApi,
    );
    service.setSession(const PushSession(userId: 1, token: 'isolated-session'));
  });

  tearDown(() async {
    await service.dispose();
    await messaging.close();
    await messages.close();
  });

  test(
    'granted permission registers once, receives messages and clears ID',
    () async {
      final received = <RemoteMessage>[];
      expect(await service.start(onMessage: received.add), isTrue);
      expect(service.registrationId.value, 'isolated-installation-id');
      expect(await service.start(onMessage: received.add), isTrue);
      expect(initializations, 1);
      expect(messaging.registrations, 1);
      expect(messaging.permissionRequests, 0);
      messages.add(
        const RemoteMessage(
          messageId: 'isolated-message',
          data: {'recipient_id': '1'},
        ),
      );
      expect(received.single.messageId, 'isolated-message');
      messaging.unregistered.add('different-installation');
      expect(service.registrationId.value, isNotNull);
      messaging.unregistered.add('isolated-installation-id');
      expect(service.registrationId.value, isNull);
      await service.syncSession();
      expect(deviceApi.operations.first, startsWith('bind:1:'));
    },
  );

  test('new permission is requested before registration', () async {
    messaging.status = AuthorizationStatus.notDetermined;
    expect(await service.start(), isTrue);
    expect(messaging.permissionRequests, 1);
    expect(messaging.registrations, 1);
  });

  test('denied permission does not prompt again or register', () async {
    SharedPreferences.setMockInitialValues({
      PushNotificationService.permissionRequestedKey: true,
    });
    messaging.status = AuthorizationStatus.denied;
    expect(await service.start(), isTrue);
    expect(service.authorizationStatus, AuthorizationStatus.denied);
    expect(messaging.permissionRequests, 0);
    expect(messaging.registrations, 0);
  });

  test(
    'Android first-request denied state still asks for permission',
    () async {
      messaging.status = AuthorizationStatus.denied;
      expect(await service.start(), isTrue);
      expect(messaging.permissionRequests, 1);
      expect(messaging.registrations, 1);
      final prefs = await SharedPreferences.getInstance();
      expect(
        prefs.getBool(PushNotificationService.permissionRequestedKey),
        isTrue,
      );
    },
  );

  test(
    'registration failure is nonfatal and retry does not duplicate listeners',
    () async {
      messaging.failRegistration = true;
      expect(await service.start(), isTrue);
      expect(service.lastError, isNotNull);
      expect(messaging.registered.hasListener, isTrue);
      messaging.failRegistration = false;
      await service.syncSession();
      expect(service.lastError, isNull);
      expect(service.registrationId.value, 'isolated-installation-id');
    },
  );

  test('unsupported platforms skip native Firebase entirely', () async {
    await service.dispose();
    service = PushNotificationService(
      messaging: messaging,
      supportsPlatform: () => false,
      initializeFirebase: () async => throw StateError('Must not run'),
    );
    expect(await service.start(), isFalse);
    expect(messaging.registrations, 0);
  });

  test(
    'initialization failure does not attempt messaging registration',
    () async {
      await service.dispose();
      service = PushNotificationService(
        messaging: messaging,
        supportsPlatform: () => true,
        initializeFirebase: () async => throw StateError('No native Firebase'),
      );
      expect(await service.start(), isFalse);
      expect(messaging.registrations, 0);
    },
  );

  test('logout unbinds Django and unregisters FCM', () async {
    await service.start();
    await service.syncSession();
    await service.clearSession();
    expect(deviceApi.operations.last, startsWith('unbind:1:'));
    expect(service.registrationId.value, isNull);
    expect(messaging.unregistrations, greaterThan(0));
  });

  test(
    'account switch serializes an in-flight old bind and filters messages',
    () async {
      deviceApi.bindGate = Completer<void>();
      final received = <RemoteMessage>[];
      final starting = service.start(onMessage: received.add);
      while (deviceApi.operations.isEmpty) {
        await Future<void>.delayed(Duration.zero);
      }
      service.setSession(
        const PushSession(userId: 2, token: 'new-isolated-session'),
      );
      messages.add(const RemoteMessage(data: {'recipient_id': '1'}));
      expect(received, isEmpty);
      deviceApi.bindGate!.complete();
      await starting;
      await service.syncSession();
      expect(
        deviceApi.operations.map((op) => op.split(':').take(2).join(':')),
        ['bind:1', 'unbind:1', 'bind:2'],
      );
      messages.add(const RemoteMessage(data: {'recipient_id': '2'}));
      expect(received, hasLength(1));
    },
  );

  test(
    'already allowed signed-out startup neither prompts nor binds',
    () async {
      service.setSession(null);
      expect(await service.start(), isTrue);
      expect(messaging.permissionRequests, 0);
      expect(messaging.registrations, 0);
      expect(messaging.unregistrations, 1);
      expect(deviceApi.operations, isEmpty);
    },
  );

  test('first launch asks before login and waits for login to bind', () async {
    service.setSession(null);
    messaging.status = AuthorizationStatus.notDetermined;
    await service.start();
    expect(messaging.permissionRequests, 1);
    expect(service.authorizationStatus, AuthorizationStatus.authorized);
    expect(messaging.registrations, 0);
    expect(deviceApi.operations, isEmpty);
    service.setSession(const PushSession(userId: 1, token: 'isolated-session'));
    await service.syncSession();
    expect(messaging.permissionRequests, 1);
    expect(service.isRegistered, isTrue);
  });

  test(
    'first Android denied-as-undetermined state asks before login once',
    () async {
      service.setSession(null);
      messaging.status = AuthorizationStatus.denied;
      await service.start();
      expect(messaging.permissionRequests, 1);
      expect(messaging.registrations, 0);
      expect(deviceApi.operations, isEmpty);
    },
  );

  test('previous denial is respected before login across resume', () async {
    SharedPreferences.setMockInitialValues({
      PushNotificationService.permissionRequestedKey: true,
    });
    service.setSession(null);
    messaging.status = AuthorizationStatus.denied;
    await service.start();
    service.didChangeAppLifecycleState(AppLifecycleState.resumed);
    await service.syncSession();
    expect(messaging.permissionRequests, 0);
    expect(messaging.registrations, 0);
    expect(deviceApi.operations, isEmpty);
  });

  test(
    'declining the first-launch prompt is not followed by another automatic prompt',
    () async {
      service.setSession(null);
      messaging.status = AuthorizationStatus.notDetermined;
      messaging.permissionResult = AuthorizationStatus.denied;
      await service.start();
      expect(service.authorizationStatus, AuthorizationStatus.denied);
      service.didChangeAppLifecycleState(AppLifecycleState.resumed);
      await service.syncSession();
      expect(messaging.permissionRequests, 1);
      expect(messaging.registrations, 0);
      expect(deviceApi.operations, isEmpty);
    },
  );

  test(
    'sign-in during first-launch prompt binds only after the choice',
    () async {
      service.setSession(null);
      messaging.status = AuthorizationStatus.notDetermined;
      messaging.permissionGate = Completer<void>();
      final starting = service.start();
      while (messaging.permissionRequests == 0) {
        await Future<void>.delayed(Duration.zero);
      }
      service.setSession(
        const PushSession(userId: 2, token: 'new-isolated-session'),
      );
      expect(deviceApi.operations, isEmpty);
      messaging.permissionGate!.complete();
      await starting;
      await service.syncSession();
      expect(messaging.permissionRequests, 1);
      expect(deviceApi.operations.single, startsWith('bind:2:'));
    },
  );

  test('logout during permission prompt prevents later registration', () async {
    messaging.status = AuthorizationStatus.notDetermined;
    messaging.permissionGate = Completer<void>();
    final starting = service.start();
    while (messaging.permissionRequests == 0) {
      await Future<void>.delayed(Duration.zero);
    }
    final logout = service.clearSession();
    messaging.permissionGate!.complete();
    await starting;
    await logout;
    await service.syncSession();
    expect(messaging.registrations, 0);
    expect(deviceApi.operations, isEmpty);
    expect(messaging.unregistrations, greaterThan(0));
  });

  test(
    'failed permission request stays retryable instead of marking asked',
    () async {
      messaging.status = AuthorizationStatus.denied;
      messaging.failPermission = true;
      await service.start();
      final prefs = await SharedPreferences.getInstance();
      expect(
        prefs.getBool(PushNotificationService.permissionRequestedKey),
        isNot(true),
      );
      expect(messaging.registrations, 0);
      messaging.failPermission = false;
      await service.requestPermissionFromUser();
      expect(messaging.permissionRequests, 2);
      expect(service.isRegistered, isTrue);
    },
  );

  test(
    'explicit permission action retries a previously denied request',
    () async {
      SharedPreferences.setMockInitialValues({
        PushNotificationService.permissionRequestedKey: true,
      });
      messaging.status = AuthorizationStatus.denied;
      await service.start();
      expect(messaging.permissionRequests, 0);
      await service.requestPermissionFromUser();
      expect(messaging.permissionRequests, 1);
      expect(service.isRegistered, isTrue);
    },
  );

  test('initialization retry retains the foreground callback', () async {
    await service.dispose();
    var fail = true;
    final received = <RemoteMessage>[];
    service = PushNotificationService(
      messaging: messaging,
      deviceApi: deviceApi,
      foregroundMessages: messages.stream,
      supportsPlatform: () => true,
      initializeFirebase: () async {
        if (fail) throw StateError('Isolated init failure');
      },
    );
    service.setSession(const PushSession(userId: 1, token: 'isolated-session'));
    expect(await service.start(onMessage: received.add), isFalse);
    fail = false;
    await service.requestPermissionFromUser();
    expect(service.isRegistered, isTrue);
    messages.add(const RemoteMessage(data: {'recipient_id': '1'}));
    expect(received, hasLength(1));
  });

  test(
    'permanent denial waits for settings and resume binds after grant',
    () async {
      messaging.status = AuthorizationStatus.deniedPermanently;
      await service.start();
      await service.requestPermissionFromUser();
      expect(
        service.authorizationStatus,
        AuthorizationStatus.deniedPermanently,
      );
      expect(messaging.permissionRequests, 0);
      expect(deviceApi.operations, isEmpty);
      messaging.status = AuthorizationStatus.authorized;
      service.didChangeAppLifecycleState(AppLifecycleState.resumed);
      await service.syncSession();
      expect(service.isRegistered, isTrue);
      expect(messaging.permissionRequests, 0);
    },
  );

  test(
    'settings uses only the fixed native notification settings channel',
    () async {
      const channel = MethodChannel('campushub/notification_settings');
      final messenger =
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
      final calls = <MethodCall>[];
      messenger.setMockMethodCallHandler(channel, (call) async {
        calls.add(call);
        return true;
      });
      addTearDown(() => messenger.setMockMethodCallHandler(channel, null));
      expect(await service.openNotificationSettings(), isTrue);
      expect(calls.single.method, 'open');
      expect(calls.single.arguments, isNull);
      expect(deviceApi.operations, isEmpty);
    },
  );

  test(
    'missing native handler returns false without breaking the panel',
    () async {
      expect(await service.openNotificationSettings(), isFalse);
    },
  );

  test(
    'Firebase unknown is identified at registration without leaking native details',
    () async {
      final originalPrint = debugPrint;
      final logs = <String>[];
      debugPrint = (String? message, {int? wrapWidth}) =>
          logs.add(message ?? '');
      addTearDown(() => debugPrint = originalPrint);
      messaging.registrationError = FirebaseException(
        plugin: 'firebase_messaging',
        code: 'unknown',
        message:
            'java.io.IOException: SERVICE_NOT_AVAILABLE private-device-value',
      );
      await service.start();
      expect(service.authorizationStatus, AuthorizationStatus.authorized);
      expect(service.lastError, contains('Firebase could not register'));
      expect(
        logs.join(),
        contains(
          'firebase-registration/FirebaseException/unknown/service-unavailable',
        ),
      );
      expect(logs.join(), isNot(contains('private-device-value')));
      expect(deviceApi.operations, isEmpty);
      messaging.registrationError = null;
      await service.requestPermissionFromUser();
      expect(service.isRegistered, isTrue);
      expect(service.lastError, isNull);
    },
  );

  test(
    'Firebase configuration and Play services failures give relevant recovery',
    () async {
      messaging.registrationError = FirebaseException(
        plugin: 'firebase_messaging',
        code: 'unknown',
        message: 'FIS_AUTH_ERROR',
      );
      await service.start();
      expect(service.lastError, contains('Firebase configuration'));
      messaging.registrationError = FirebaseException(
        plugin: 'firebase_messaging',
        code: 'unknown',
        message: 'MISSING_INSTANCEID_SERVICE',
      );
      await service.requestPermissionFromUser();
      expect(service.lastError, contains('Google Play services'));
    },
  );

  test(
    'Django rejection distinguishes expired authentication from server failure',
    () async {
      deviceApi.bindError = const PushRegistrationException(401);
      await service.start();
      expect(service.lastError, contains('login has expired'));
      expect(service.isRegistered, isFalse);
      deviceApi.bindError = const PushRegistrationException(500);
      await service.syncSession();
      expect(service.lastError, contains('could not save this device'));
      deviceApi.bindError = StateError('Isolated network failure');
      await service.syncSession();
      expect(service.lastError, contains('Cannot reach CampusHub'));
    },
  );

  group('Android phone notifications', () {
    const channel = MethodChannel('dexterous.com/flutter/local_notifications');
    final native =
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
    late List<MethodCall> calls;

    setUp(() {
      // Plain unit tests run on the host OS and do not run Android's generated
      // Dart plugin registrant. Exercise its real Android method-channel path.
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      AndroidFlutterLocalNotificationsPlugin.registerWith();
      calls = [];
      native.setMockMethodCallHandler(channel, (call) async {
        calls.add(call);
        if (call.method == 'initialize') return true;
        if (call.method == 'getNotificationAppLaunchDetails') {
          return {'notificationLaunchedApp': false};
        }
        return null;
      });
    });
    tearDown(() {
      native.setMockMethodCallHandler(channel, null);
      debugDefaultTargetPlatformOverride = null;
    });

    const message = RemoteMessage(
      messageId: 'isolated-message',
      notification: RemoteNotification(
        title: 'Product Approved!',
        body: 'Your Test listing has been approved.',
      ),
      data: {
        'product_id': '7',
        'recipient_id': '1',
        'type': 'product_approved',
        'delivery_id': '13',
      },
    );

    test(
      'foreground renders once on high channel with actual routing IDs only',
      () async {
        await service.start();
        messages.add(message);
        messages.add(message);
        await Future<void>.delayed(Duration.zero);
        final shown = calls.where((c) => c.method == 'show').toList();
        expect(shown, hasLength(1));
        final args = Map<String, dynamic>.from(shown.single.arguments as Map);
        expect(args['title'], 'Product Approved!');
        expect(jsonDecode(args['payload'] as String), message.data);
        final details = args['platformSpecifics'] as Map;
        expect(details['channelId'], 'campushub_approvals_v1');
        expect(details['importance'], 4);
        expect(details['priority'], 1);
        expect(details['fullScreenIntent'], isFalse);
        expect(service.isRegistered, isTrue);
      },
    );

    test(
      'signed-out, wrong-recipient and data-only events never display',
      () async {
        await service.start();
        expect(
          await service.presentForegroundNotification(
            const RemoteMessage(
              notification: RemoteNotification(title: 'Other'),
              data: {
                'product_id': '7',
                'recipient_id': '2',
                'type': 'product_approved',
                'delivery_id': '14',
              },
            ),
          ),
          isFalse,
        );
        expect(
          await service.presentForegroundNotification(
            RemoteMessage(data: message.data),
          ),
          isFalse,
        );
        await service.clearSession();
        expect(await service.presentForegroundNotification(message), isFalse);
        expect(calls.where((c) => c.method == 'show'), isEmpty);
      },
    );

    test(
      'background tap queues only navigation and never displays a second notification',
      () async {
        await service.dispose();
        final taps = StreamController<RemoteMessage>.broadcast(sync: true);
        addTearDown(taps.close);
        service = PushNotificationService(
          messaging: messaging,
          deviceApi: deviceApi,
          foregroundMessages: messages.stream,
          openedMessages: taps.stream,
          initializeFirebase: () async {},
          supportsPlatform: () => true,
        );
        service.setSession(
          const PushSession(userId: 1, token: 'isolated-session'),
        );
        await service.start();
        taps.add(message);
        final target = service.takePendingProductNotification();
        expect(target?.productId, 7);
        taps.add(message);
        expect(service.takePendingProductNotification(), isNull);
        expect(calls.where((c) => c.method == 'show'), isEmpty);
      },
    );

    test(
      'cold-start tap waits for login and never opens under another account',
      () async {
        await service.dispose();
        service = PushNotificationService(
          messaging: messaging,
          deviceApi: deviceApi,
          foregroundMessages: messages.stream,
          initialMessage: () async => message,
          initializeFirebase: () async {},
          supportsPlatform: () => true,
        );
        await service.start();
        expect(service.pendingProductNotification.value?.productId, 7);
        expect(service.takePendingProductNotification(), isNull);
        service.setSession(
          const PushSession(userId: 2, token: 'other-isolated-session'),
        );
        expect(service.takePendingProductNotification(), isNull);
        expect(service.pendingProductNotification.value, isNull);
      },
    );

    test('local notification tap uses same validated destination', () async {
      await service.start();
      await native.handlePlatformMessage(
        channel.name,
        const StandardMethodCodec().encodeMethodCall(
          MethodCall('didReceiveNotificationResponse', {
            'notificationResponseType': 0,
            'notificationId': 0,
            'payload': jsonEncode(message.data),
          }),
        ),
        (_) {},
      );
      expect(service.takePendingProductNotification()?.productId, 7);
    });

    test('OS presentation error leaves valid device binding intact', () async {
      await service.start();
      native.setMockMethodCallHandler(channel, (call) async {
        if (call.method == 'show') throw PlatformException(code: 'blocked');
        return null;
      });
      expect(await service.presentForegroundNotification(message), isFalse);
      expect(service.isRegistered, isTrue);
      expect(service.lastError, isNull);
    });
  });
}
