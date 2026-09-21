import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:campushub/module_app/routes/app_router.dart';
import 'package:campushub/module_app/routes/app_routes.dart';
import 'package:campushub/module_app/screens/components/auth_theme_toggle.dart';
import 'package:campushub/module_app/services/theme_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('theme button switches from sun to moon', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    await ThemeService.instance.setLightMode(true);

    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: AuthThemeToggle())),
    );

    expect(find.byIcon(Icons.light_mode_outlined), findsOneWidget);
    expect(find.byIcon(Icons.dark_mode_outlined), findsNothing);

    await tester.tap(find.byTooltip('Switch to dark mode'));
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.light_mode_outlined), findsNothing);
    expect(find.byIcon(Icons.dark_mode_outlined), findsOneWidget);
  });

  testWidgets('named login route opens the login screen', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        initialRoute: AppRoutes.login,
        onGenerateRoute: AppRouter.onGenerateRoute,
      ),
    );

    expect(find.text('Welcome Back!'), findsOneWidget);
    expect(find.text('Login'), findsOneWidget);
  });

  testWidgets('Sign Up button opens the account creation screen', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(360, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    addTearDown(tester.view.resetViewInsets);

    await tester.pumpWidget(
      MaterialApp(
        initialRoute: AppRoutes.login,
        onGenerateRoute: AppRouter.onGenerateRoute,
      ),
    );

    final signUpButton = find.widgetWithText(TextButton, 'Signup');
    expect(signUpButton, findsOneWidget);

    await tester.ensureVisible(signUpButton);
    await tester.pumpAndSettle();
    await tester.tap(signUpButton);
    await tester.pumpAndSettle();

    expect(find.text('Create Account'), findsOneWidget);
    expect(find.text('Create your account to get started.'), findsOneWidget);
    expect(find.text('SIGN UP'), findsOneWidget);
    expect(find.text('Username'), findsOneWidget);
    expect(find.textContaining('Privacy Policy'), findsOneWidget);

    expect(find.byKey(const Key('signup-form-scroll')), findsOneWidget);

    await tester.tap(find.byType(TextFormField).first);
    await tester.pump();
    expect(tester.testTextInput.isVisible, isTrue);

    tester.view.viewInsets = const FakeViewPadding(bottom: 300);
    await tester.pumpAndSettle();
    expect(find.text('CampusHub', findRichText: true), findsOneWidget);
    expect(tester.testTextInput.isVisible, isTrue);
    expect(tester.takeException(), isNull);

    tester.view.resetViewInsets();
    await tester.pumpAndSettle();
    expect(find.text('CampusHub', findRichText: true), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).first, 'lester');
    expect(find.text('Lester'), findsOneWidget);

    expect(find.text('8+ characters and no spaces'), findsNothing);
    expect(find.text('Uppercase and lowercase letters'), findsNothing);
    expect(find.text('Number and special character'), findsNothing);

    await tester.enterText(find.byType(TextFormField).at(4), 'a');
    await tester.pumpAndSettle();

    expect(find.text('8+ characters and no spaces'), findsOneWidget);
    expect(find.text('Uppercase and lowercase letters'), findsOneWidget);
    expect(find.text('Number and special character'), findsOneWidget);
    expect(find.byIcon(Icons.close_rounded), findsNWidgets(3));

    await tester.enterText(find.byType(TextFormField).at(4), 'CampusHub1!');
    await tester.pump();

    expect(find.byIcon(Icons.check_rounded), findsNWidgets(3));
  });
}
