import 'dart:async';
import 'dart:convert';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../firebase_options.dart';
import '../models/product_notification_target.dart';
import 'push_device_api.dart';

/// FCM reception and authenticated Django device ownership share one lifecycle.
class PushNotificationService with WidgetsBindingObserver {
  PushNotificationService({
    FirebaseMessaging? messaging,
    Future<void> Function()? initializeFirebase,
    bool Function()? supportsPlatform,
    Stream<RemoteMessage>? foregroundMessages,
    PushDeviceApi? deviceApi,
    FlutterLocalNotificationsPlugin? localNotifications,
    Stream<RemoteMessage>? openedMessages,
    Future<RemoteMessage?> Function()? initialMessage,
  }) : _messagingOverride = messaging,
       _initializeFirebase = initializeFirebase ?? _initializeAndroidFirebase,
       _supportsPlatform = supportsPlatform ?? _isAndroid,
       _foregroundMessages = foregroundMessages,
       _deviceApi = deviceApi ?? PushDeviceApi(),
       _localNotifications =
           localNotifications ?? FlutterLocalNotificationsPlugin(),
       _openedMessages = openedMessages,
       _initialMessage = initialMessage;

  static final instance = PushNotificationService();
  static const permissionRequestedKey = 'campushub_push_permission_requested';
  static const approvalsChannel = AndroidNotificationChannel(
    'campushub_approvals_v1',
    'Product Approvals',
    description: 'Product approval and rejection updates',
    importance: Importance.high,
    playSound: true,
    enableVibration: true,
  );
  static const _settingsChannel = MethodChannel(
    'campushub/notification_settings',
  );
  final FirebaseMessaging? _messagingOverride;
  final Future<void> Function() _initializeFirebase;
  final bool Function() _supportsPlatform;
  final Stream<RemoteMessage>? _foregroundMessages;
  final PushDeviceApi _deviceApi;
  final FlutterLocalNotificationsPlugin _localNotifications;
  final Stream<RemoteMessage>? _openedMessages;
  final Future<RemoteMessage?> Function()? _initialMessage;
  final pendingProductNotification = ValueNotifier<ProductNotificationTarget?>(
    null,
  );
  final Set<String> _presented = {}, _opened = {};
  bool _localReady = false;
  final List<StreamSubscription<dynamic>> _subscriptions = [];
  final registrationId = ValueNotifier<String?>(null);
  final stateChanges = ValueNotifier<int>(0);
  AuthorizationStatus? authorizationStatus;
  String? lastError;
  String _operation = 'initialization';
  FirebaseMessaging? _messaging;
  PushSession? _session, _boundSession;
  String? _boundId;
  int _generation = 0;
  bool _started = false;
  bool _enabled = false,
      _observing = false,
      _forcePermission = false,
      _disposed = false;
  void Function(RemoteMessage)? _onMessage;
  Future<bool>? _starting;
  Future<void> _sessionWork = Future.value();

  bool get hasSession => _session != null;
  int? get currentUserId => _session?.userId;
  bool get isSupported => _supportsPlatform();
  bool get isRegistered =>
      _boundId != null &&
      _boundId == registrationId.value &&
      (_boundSession?.matches(_session) ?? false);

  void _notify() {
    if (!_disposed) stateChanges.value++;
  }

  static bool _isAndroid() =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

  static Future<void> _initializeAndroidFirebase() async {
    await Firebase.initializeApp(options: DefaultFirebaseOptions.android);
  }

  /// Called by the existing SessionService after save/restore/update/logout.
  void setSession(PushSession? session) {
    if (session == null || !session.matches(_session)) _generation++;
    _session = session;
    final pending = pendingProductNotification.value;
    if (session != null &&
        pending != null &&
        pending.recipientId != session.userId) {
      pendingProductNotification.value = null;
    }
    _notify();
    if (_started) unawaited(syncSession());
    if (_enabled && !_started && _starting == null && session != null) {
      unawaited(start());
    }
  }

  Future<void> clearSession() async {
    setSession(null);
    // A permission prompt/network request must not trap the logout screen.
    await _sessionWork.timeout(const Duration(seconds: 6), onTimeout: () {});
  }

  Future<bool> start({void Function(RemoteMessage)? onMessage}) {
    _enabled = true;
    _onMessage = onMessage ?? _onMessage;
    if (_started) return Future.value(true);
    return _starting ??= _start().whenComplete(() => _starting = null);
  }

  Future<bool> _start() async {
    if (!_supportsPlatform()) return false;
    if (!_observing) {
      WidgetsBinding.instance.addObserver(this);
      _observing = true;
    }
    try {
      _operation = 'firebase-initialization';
      await _initializeFirebase().timeout(const Duration(seconds: 10));
      final messaging = _messaging =
          _messagingOverride ?? FirebaseMessaging.instance;
      await _prepareSystemNotifications();
      _subscriptions.add(
        (_openedMessages ?? FirebaseMessaging.onMessageOpenedApp).listen(
          (message) => _queueTap(message.data),
          onError: (Object _) {
            debugPrint('FCM notification tap data is unavailable.');
          },
        ),
      );
      try {
        final initial =
            await (_initialMessage?.call() ?? messaging.getInitialMessage());
        if (initial != null) _queueTap(initial.data);
      } catch (_) {
        debugPrint('FCM notification launch data is unavailable.');
      }
      _subscriptions.add(
        messaging.onRegistered.listen(
          (id) {
            registrationId.value = id;
            _notify();
            if (_started) unawaited(syncSession());
          },
          onError: (Object error) =>
              _recordError(error, operation: 'firebase-events'),
        ),
      );
      _subscriptions.add(
        messaging.onUnregistered.listen(
          (id) {
            if (registrationId.value == id) {
              registrationId.value = null;
              _notify();
              if (_started) unawaited(syncSession());
            }
          },
          onError: (Object error) =>
              _recordError(error, operation: 'firebase-events'),
        ),
      );
      _subscriptions.add(
        (_foregroundMessages ?? FirebaseMessaging.onMessage).listen(
          (message) {
            // Ignore private foreground messages from a previous login.
            final recipient = message.data['recipient_id'];
            if (_session != null &&
                recipient?.toString() == '${_session!.userId}') {
              unawaited(presentForegroundNotification(message));
              _onMessage?.call(message);
            }
          },
          onError: (Object error) =>
              _recordError(error, operation: 'firebase-events'),
        ),
      );
      _started = true;
      _notify();
      await syncSession();
      return true;
    } catch (error) {
      _recordError(error);
      for (final subscription in _subscriptions) {
        await subscription.cancel();
      }
      _subscriptions.clear();
      _started = false;
      return false;
    }
  }

  Future<void> syncSession() {
    if (!_started) return Future.value();
    // Serialize detach/bind so an old response cannot win an account switch.
    return _sessionWork = _sessionWork
        .then((_) => _syncSession())
        .catchError((Object error) => _recordError(error));
  }

  /// Explicit bell-panel action. Android decides whether it can show a dialog;
  /// a prior permanent denial still requires the phone's app settings.
  Future<void> requestPermissionFromUser() async {
    if (!_supportsPlatform() || !hasSession) return;
    _forcePermission = true;
    if (!_started) {
      await start();
    } else {
      await syncSession();
    }
  }

  /// Opens this app's normal notification controls, not notification-listener
  /// access. Permission is still granted only by the user in Android Settings.
  Future<bool> openNotificationSettings() async {
    if (!_supportsPlatform()) return false;
    try {
      return await _settingsChannel.invokeMethod<bool>('open') ?? false;
    } on PlatformException {
      return false;
    } on MissingPluginException {
      return false;
    }
  }

  Future<void> _prepareSystemNotifications() async {
    try {
      final android = _localNotifications
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >();
      if (android == null) {
        throw StateError('Android notification plugin is not registered.');
      }
      final initialized = await _localNotifications.initialize(
        settings: const InitializationSettings(
          android: AndroidInitializationSettings('ic_stat_campushub'),
        ),
        onDidReceiveNotificationResponse: (response) {
          try {
            final decoded = jsonDecode(response.payload ?? '');
            if (decoded is Map<String, dynamic>) _queueTap(decoded);
          } catch (_) {
            /* Ignore malformed/unrelated notification payloads. */
          }
        },
      );
      if (initialized != true) return;
      await android.createNotificationChannel(approvalsChannel);
      _localReady = true;
      final launch = await _localNotifications
          .getNotificationAppLaunchDetails();
      if (launch?.didNotificationLaunchApp == true) {
        final payload = launch?.notificationResponse?.payload;
        if (payload != null) {
          final decoded = jsonDecode(payload);
          if (decoded is Map<String, dynamic>) _queueTap(decoded);
        }
      }
    } catch (error) {
      debugPrint(
        'Android notification presentation setup is unavailable (${error.runtimeType}).',
      );
    }
  }

  void _queueTap(Map<String, dynamic> data) {
    final target = ProductNotificationTarget.fromJson(data);
    if (_disposed ||
        target == null ||
        _opened.contains(target.key) ||
        (_session != null && target.recipientId != _session!.userId)) {
      return;
    }
    _opened.add(target.key);
    if (_opened.length > 100) _opened.remove(_opened.first);
    pendingProductNotification.value = target;
  }

  ProductNotificationTarget? takePendingProductNotification() {
    final target = pendingProductNotification.value;
    if (target == null ||
        _session == null ||
        target.recipientId != _session!.userId) {
      return null;
    }
    pendingProductNotification.value = null;
    return target;
  }

  /// Preserve an already validated tap while the existing login screen is used.
  void deferProductNotification(ProductNotificationTarget target) {
    pendingProductNotification.value = target;
  }

  /// Foreground only. FCM/Android renders background payloads; no duplicate handler.
  Future<bool> presentForegroundNotification(RemoteMessage message) async {
    final target = ProductNotificationTarget.fromJson(message.data);
    if (!_supportsPlatform() ||
        !_localReady ||
        target == null ||
        target.recipientId != _session?.userId ||
        message.notification == null ||
        ![
          AuthorizationStatus.authorized,
          AuthorizationStatus.provisional,
        ].contains(authorizationStatus) ||
        _presented.contains(target.key)) {
      return false;
    }
    _presented.add(target.key);
    if (_presented.length > 100) _presented.remove(_presented.first);
    try {
      await _localNotifications.show(
        id: 0,
        title: message.notification!.title,
        body: message.notification!.body,
        notificationDetails: NotificationDetails(
          android: AndroidNotificationDetails(
            approvalsChannel.id,
            approvalsChannel.name,
            channelDescription: approvalsChannel.description,
            icon: 'ic_stat_campushub',
            importance: Importance.high,
            priority: Priority.high,
            playSound: true,
            enableVibration: true,
            visibility: NotificationVisibility.private,
            tag: 'product-review-${target.productId}',
            color: const Color(0xFF1A1851),
            autoCancel: true,
          ),
        ),
        payload: jsonEncode(target.toJson()),
      );
      return true;
    } catch (_) {
      _presented.remove(target.key);
      debugPrint('Android foreground notification could not be displayed.');
      return false;
    }
  }

  Future<void> _syncSession() async {
    final session = _session;
    final generation = _generation;
    final messaging = _messaging!;
    if (_boundId != null &&
        (!(_boundSession?.matches(session) ?? false) ||
            _boundId != registrationId.value)) {
      try {
        _operation = 'server-unbind';
        await _deviceApi.unbind(_boundSession!, _boundId!);
      } catch (error) {
        _recordError(error);
      }
      _boundId = null;
      _boundSession = null;
    }
    if (generation != _generation) return;
    // Ask on first launch even before login. Permission belongs to the app;
    // Firebase registration and Django ownership still require a session.
    _operation = 'permission-check';
    var settings = await messaging.getNotificationSettings();
    final prefs = await SharedPreferences.getInstance();
    final askedBefore = prefs.getBool(permissionRequestedKey) ?? false;
    final forcePermission = _forcePermission;
    _forcePermission = false;
    if (settings.authorizationStatus == AuthorizationStatus.notDetermined ||
        (settings.authorizationStatus == AuthorizationStatus.denied &&
            (!askedBefore || forcePermission))) {
      _operation = 'permission-request';
      settings = await messaging.requestPermission();
      // A plugin/platform failure must not suppress every later attempt.
      await prefs.setBool(permissionRequestedKey, true);
    }
    if (generation != _generation) return;
    authorizationStatus = settings.authorizationStatus;
    _notify();
    if (session == null) {
      registrationId.value = null;
      _notify();
      _operation = 'firebase-unregister';
      await messaging.unregister().timeout(const Duration(seconds: 5));
      return;
    }
    if (authorizationStatus != AuthorizationStatus.authorized &&
        authorizationStatus != AuthorizationStatus.provisional) {
      if (_boundId != null) {
        _operation = 'server-unbind';
        await _deviceApi.unbind(_boundSession!, _boundId!);
      }
      _boundId = null;
      _boundSession = null;
      registrationId.value = null;
      _operation = 'firebase-unregister';
      await messaging.unregister().timeout(const Duration(seconds: 5));
      return;
    }
    if (registrationId.value == null) {
      _operation = 'firebase-registration';
      await messaging.register().timeout(const Duration(seconds: 10));
    }
    if (generation != _generation) return;
    final fid = registrationId.value;
    if (fid == null || (_boundId == fid && session.matches(_boundSession))) {
      return;
    }
    _operation = 'server-registration';
    if (!await _deviceApi.bind(session, fid)) {
      throw StateError('Device registration was not accepted');
    }
    _boundId = fid;
    _boundSession = session;
    lastError = null;
    _notify();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      if (_started) {
        unawaited(syncSession());
      } else if (_enabled) {
        unawaited(start());
      }
    }
  }

  void _recordError(Object error, {String? operation}) {
    final step = operation ?? _operation;
    // Match known reasons only. Never log the original native exception text:
    // it may contain configuration details, URLs or identifiers.
    final nativeText =
        (error is FirebaseException
                ? error.message ?? ''
                : error is PlatformException
                ? error.message ?? ''
                : '')
            .toUpperCase();
    final reason =
        nativeText.contains('FIS_AUTH_ERROR') ||
            nativeText.contains('API_KEY_INVALID') ||
            nativeText.contains('API KEY NOT VALID') ||
            nativeText.contains('INVALID_API_KEY')
        ? 'firebase-configuration'
        : nativeText.contains('MISSING_INSTANCEID_SERVICE') ||
              nativeText.contains('GOOGLE PLAY SERVICES')
        ? 'play-services'
        : nativeText.contains('SERVICE_NOT_AVAILABLE')
        ? 'service-unavailable'
        : nativeText.contains('AUTHENTICATION_FAILED')
        ? 'firebase-authentication'
        : nativeText.contains('TOO_MANY_REGISTRATIONS')
        ? 'registration-limit'
        : error is TimeoutException
        ? 'timeout'
        : 'unclassified';
    if (error is PushRegistrationException) {
      lastError = error.statusCode == 401
          ? 'Your notification login has expired. Sign out and sign in again.'
          : error.statusCode == 403
          ? 'This account cannot register for notifications. Contact the administrator.'
          : 'CampusHub could not save this device for notifications. Please try again later.';
    } else if (step == 'server-registration' || step == 'server-unbind') {
      lastError =
          'Cannot reach CampusHub to connect notifications. Check your connection to the Django server, then retry.';
    } else if (reason == 'play-services') {
      lastError =
          'Firebase needs working Google Play services. Update Google Play services, then retry.';
    } else if (reason == 'firebase-configuration' ||
        reason == 'firebase-authentication') {
      lastError =
          'Firebase could not verify this app. Contact the administrator to check the Firebase configuration.';
    } else if (step == 'firebase-registration' || step == 'firebase-events') {
      lastError =
          'Firebase could not register this device for notifications. Check the phone’s internet connection, then retry.';
    } else if (step == 'permission-check' || step == 'permission-request') {
      lastError =
          'Cannot read notification permission. Check CampusHub’s notification settings, then retry.';
    } else {
      lastError = 'Firebase notification setup could not finish. Please retry.';
    }
    final code = error is FirebaseException ? error.code : '';
    final suffix = RegExp(r'^[A-Za-z0-9_/-]{1,80}$').hasMatch(code)
        ? '/$code'
        : '';
    debugPrint(
      'Firebase notification setup failed ($step/${error.runtimeType}$suffix/$reason${error is PushRegistrationException ? '/http-${error.statusCode}' : ''}).',
    );
    _notify();
  }

  Future<void> dispose() async {
    WidgetsBinding.instance.removeObserver(this);
    for (final subscription in _subscriptions) {
      await subscription.cancel();
    }
    _subscriptions.clear();
    _started = false;
    _enabled = false;
    _disposed = true;
    registrationId.dispose();
    stateChanges.dispose();
    pendingProductNotification.dispose();
  }
}
