import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'module_app/routes/app_router.dart';
import 'module_app/routes/app_routes.dart';
import 'module_app/services/cart_service.dart';
import 'module_app/services/push_notification_service.dart';
import 'module_app/services/theme_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await CartService.instance.load();
  await ThemeService.instance.load();
  runApp(const CampusHubApp());
  // Request first-launch notification permission after the first visible frame,
  // before login; optional push errors must not block the startup screen.
  WidgetsBinding.instance.addPostFrameCallback((_) {
    unawaited(PushNotificationService.instance.start());
  });
}

class CampusHubApp extends StatefulWidget {
  const CampusHubApp({super.key});

  @override
  State<CampusHubApp> createState() => _CampusHubAppState();
}

class _CampusHubAppState extends State<CampusHubApp> {
  final _navigatorKey = GlobalKey<NavigatorState>();
  late final _NotificationRouteObserver _notificationObserver;

  @override
  void initState() {
    super.initState();
    _notificationObserver = _NotificationRouteObserver(
      _scheduleNotificationOpen,
    );
    PushNotificationService.instance.pendingProductNotification.addListener(
      _scheduleNotificationOpen,
    );
    PushNotificationService.instance.stateChanges.addListener(
      _scheduleNotificationOpen,
    );
  }

  void _scheduleNotificationOpen() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted ||
          _navigatorKey.currentState == null ||
          const [
            AppRoutes.startup,
            AppRoutes.login,
            AppRoutes.signup,
            AppRoutes.profileSetup,
          ].contains(_notificationObserver.currentName)) {
        return;
      }
      final target = PushNotificationService.instance
          .takePendingProductNotification();
      if (target == null) return;
      final navigator = _navigatorKey.currentState!;
      if (_notificationObserver.currentName == AppRoutes.notificationProduct) {
        unawaited(
          navigator.pushReplacementNamed<void, void>(
            AppRoutes.notificationProduct,
            arguments: target,
          ),
        );
      } else {
        unawaited(
          navigator.pushNamed<void>(
            AppRoutes.notificationProduct,
            arguments: target,
          ),
        );
      }
    });
    // A native notification callback can arrive while Flutter is otherwise idle.
    WidgetsBinding.instance.ensureVisualUpdate();
  }

  @override
  void dispose() {
    PushNotificationService.instance.pendingProductNotification.removeListener(
      _scheduleNotificationOpen,
    );
    PushNotificationService.instance.stateChanges.removeListener(
      _scheduleNotificationOpen,
    );
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: ThemeService.instance,
      builder: (context, _) {
        final isLightMode = ThemeService.instance.isLightMode;

        return MaterialApp(
          navigatorKey: _navigatorKey,
          navigatorObservers: [_notificationObserver],
          title: 'CampusHub',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            brightness: Brightness.light,
            colorSchemeSeed: const Color(0xFF1A1851),
            fontFamily: 'Poppins',
          ),
          darkTheme: ThemeData(
            brightness: Brightness.dark,
            colorSchemeSeed: const Color(0xFFFCB315),
            fontFamily: 'Poppins',
          ),
          themeMode: ThemeService.instance.themeMode,
          builder: (context, child) {
            return AnnotatedRegion<SystemUiOverlayStyle>(
              value: SystemUiOverlayStyle(
                statusBarColor: Colors.transparent,
                statusBarIconBrightness: isLightMode
                    ? Brightness.dark
                    : Brightness.light,
                statusBarBrightness: isLightMode
                    ? Brightness.light
                    : Brightness.dark,
                systemNavigationBarColor: Colors.transparent,
                systemNavigationBarIconBrightness: isLightMode
                    ? Brightness.dark
                    : Brightness.light,
                systemNavigationBarDividerColor: Colors.transparent,
                systemNavigationBarContrastEnforced: false,
              ),
              child: child ?? const SizedBox.shrink(),
            );
          },
          initialRoute: AppRoutes.startup,
          onGenerateRoute: AppRouter.onGenerateRoute,
        );
      },
    );
  }
}

/// Wait for existing startup/login/profile routing before consuming a push tap.
class _NotificationRouteObserver extends NavigatorObserver {
  _NotificationRouteObserver(this.onChanged);
  final VoidCallback onChanged;
  String? currentName = AppRoutes.startup;
  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (route is! PageRoute) return;
    currentName = route.settings.name;
    onChanged();
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    if (newRoute is! PageRoute) return;
    currentName = newRoute.settings.name;
    onChanged();
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (previousRoute is! PageRoute) return;
    currentName = previousRoute.settings.name;
    onChanged();
  }
}
