import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'module_app/routes/app_router.dart';
import 'module_app/routes/app_routes.dart';
import 'module_app/services/cart_service.dart';
import 'module_app/services/theme_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await CartService.instance.load();
  await ThemeService.instance.load();
  runApp(const CampusHubApp());
}

class CampusHubApp extends StatelessWidget {
  const CampusHubApp({super.key});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: ThemeService.instance,
      builder: (context, _) {
        final isLightMode = ThemeService.instance.isLightMode;

        return MaterialApp(
          title: 'CampusHub',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            brightness: Brightness.light,
            colorSchemeSeed: const Color(0xFF1A1851),
            fontFamily: 'Roboto',
          ),
          darkTheme: ThemeData(
            brightness: Brightness.dark,
            colorSchemeSeed: const Color(0xFFFCB316),
            fontFamily: 'Roboto',
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
