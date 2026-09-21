import 'package:campushub/module_app/screens/login_screen.dart';
import 'package:campushub/module_app/screens/signup_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final brightness in Brightness.values) {
    for (final size in [const Size(360, 640), const Size(412, 915)]) {
      testWidgets(
        'login renders pure navy top, white card with centered logo circle at $size in $brightness',
        (tester) async {
          tester.view.devicePixelRatio = 1;
          tester.view.physicalSize = size;
          addTearDown(tester.view.resetDevicePixelRatio);
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetViewInsets);

          await tester.pumpWidget(
            MaterialApp(
              theme: ThemeData(brightness: brightness),
              home: const LoginScreen(),
            ),
          );

          final surface = find.byKey(const Key('login-form-surface'));
          final scaffold = tester.widget<Scaffold>(find.byType(Scaffold));
          final header = tester.widget<Container>(
            find.byKey(const Key('login-header-surface')),
          );
          final decoration =
              tester.widget<Container>(surface).decoration! as BoxDecoration;
          final isLight = brightness == Brightness.light;
          const navyBackground = Color(0xFF1A1851);
          final expectedCardColor =
              isLight ? Colors.white : const Color(0xFF16153B);

          // Top section is pure navy blue
          expect(scaffold.backgroundColor, navyBackground);
          expect(header.color, navyBackground);

          // 2nd container is white card with rounded top corners
          expect(decoration.color, expectedCardColor);
          expect(
            decoration.borderRadius,
            const BorderRadius.only(
              topLeft: Radius.circular(32),
              topRight: Radius.circular(32),
            ),
          );
          expect(decoration.boxShadow, isNotNull);

          // Centered logo circle
          final logoCircleFinder = find.byKey(const Key('login-logo-circle'));
          expect(logoCircleFinder, findsOneWidget);
          final logoDecoration =
              tester.widget<Container>(logoCircleFinder).decoration
                  as BoxDecoration?;
          expect(logoDecoration?.shape, BoxShape.circle);

          // Form outline and labeled fields
          final outline = find.byKey(const Key('login-form-outline'));
          expect(
            find.descendant(
              of: outline,
              matching: find.text('CampusHub', findRichText: true),
            ),
            findsOneWidget,
          );
          expect(
            find.descendant(of: outline, matching: find.text('Welcome Back!')),
            findsOneWidget,
          );
          expect(find.text('Username or Email'), findsOneWidget);
          expect(find.text('Password'), findsOneWidget);
          expect(find.text('Signup'), findsOneWidget);

          // Input field borders are rounded with radius 14
          final inputField = tester.widget<TextField>(
            find.byType(TextField).first,
          );
          final inputBorder =
              inputField.decoration?.border as OutlineInputBorder?;
          expect(inputBorder?.borderRadius, BorderRadius.circular(14));

          // Login button
          final loginButton = find.widgetWithText(FilledButton, 'Login');
          await tester.ensureVisible(loginButton);
          await tester.pumpAndSettle();
          expect(loginButton.hitTestable(), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  for (final brightness in Brightness.values) {
    for (final size in [const Size(360, 640), const Size(412, 915)]) {
      testWidgets(
        'signup renders pure navy top, white card with centered logo circle at $size in $brightness',
        (tester) async {
          tester.view.devicePixelRatio = 1;
          tester.view.physicalSize = size;
          addTearDown(tester.view.resetDevicePixelRatio);
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetViewInsets);

          await tester.pumpWidget(
            MaterialApp(
              theme: ThemeData(brightness: brightness),
              home: const SignUpScreen(),
            ),
          );

          final surface = find.byKey(const Key('signup-form-surface'));
          final scaffold = tester.widget<Scaffold>(find.byType(Scaffold));
          final header = tester.widget<Container>(
            find.byKey(const Key('signup-header-surface')),
          );
          final decoration =
              tester.widget<Container>(surface).decoration! as BoxDecoration;
          final isLight = brightness == Brightness.light;
          const navyBackground = Color(0xFF1A1851);
          final expectedCardColor =
              isLight ? Colors.white : const Color(0xFF16153B);

          // Top section is pure navy blue
          expect(scaffold.backgroundColor, navyBackground);
          expect(header.color, navyBackground);

          // 2nd container is white card with rounded top corners
          expect(decoration.color, expectedCardColor);
          expect(
            decoration.borderRadius,
            const BorderRadius.only(
              topLeft: Radius.circular(32),
              topRight: Radius.circular(32),
            ),
          );
          expect(decoration.boxShadow, isNotNull);

          // Centered logo circle
          final logoCircleFinder = find.byKey(const Key('signup-logo-circle'));
          expect(logoCircleFinder, findsOneWidget);
          final logoDecoration =
              tester.widget<Container>(logoCircleFinder).decoration
                  as BoxDecoration?;
          expect(logoDecoration?.shape, BoxShape.circle);

          // Form outline and labeled fields
          final outline = find.byKey(const Key('signup-form-outline'));
          expect(
            find.descendant(
              of: outline,
              matching: find.text('CampusHub', findRichText: true),
            ),
            findsOneWidget,
          );
          expect(
            find.descendant(of: outline, matching: find.text('Create Account')),
            findsOneWidget,
          );
          expect(find.text('First Name'), findsWidgets);
          expect(find.text('Last Name'), findsOneWidget);
          expect(find.text('LastName'), findsOneWidget);
          expect(find.text('Username'), findsOneWidget);
          expect(find.text('Email'), findsOneWidget);
          expect(find.text('Password'), findsOneWidget);
          expect(find.text('Confirm Password'), findsOneWidget);
          expect(find.text('Log In'), findsOneWidget);

          // Input field borders are rounded with radius 14
          final inputField = tester.widget<TextField>(
            find.byType(TextField).first,
          );
          final inputBorder =
              inputField.decoration?.border as OutlineInputBorder?;
          expect(inputBorder?.borderRadius, BorderRadius.circular(14));

          // Sign Up button
          final signUpButton = find.widgetWithText(FilledButton, 'SIGN UP');
          await tester.ensureVisible(signUpButton);
          await tester.pumpAndSettle();
          expect(signUpButton.hitTestable(), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }
}
