import 'package:flutter/material.dart';

import '../screens/dashboard_screen.dart';
import '../screens/login_screen.dart';
import '../screens/profile_setup_screen.dart';
import '../screens/signup_screen.dart';
import '../screens/startup_gate.dart';
import 'app_routes.dart';

abstract final class AppRouter {
  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    if (settings.name == AppRoutes.signup) {
      return MaterialPageRoute<String>(
        builder: (_) => const SignUpScreen(),
        settings: settings,
      );
    }

    final Widget page = switch (settings.name) {
      AppRoutes.startup => const StartupGate(),
      AppRoutes.login => const LoginScreen(),
      AppRoutes.profileSetup => const ProfileSetupScreen(),
      AppRoutes.dashboard => const DashboardScreen(),
      _ => const LoginScreen(),
    };

    return MaterialPageRoute<dynamic>(builder: (_) => page, settings: settings);
  }
}
