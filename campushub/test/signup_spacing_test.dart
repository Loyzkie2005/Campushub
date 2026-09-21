import 'package:campushub/module_app/screens/signup_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final brightness in Brightness.values) {
    testWidgets('signup fields have spacing in $brightness', (tester) async {
      await tester.binding.setSurfaceSize(const Size(360, 800));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData(brightness: brightness),
          home: const SignUpScreen(),
        ),
      );

      final fields = find.byType(TextFormField);
      expect(fields, findsNWidgets(6));
      for (var index = 2; index < 4; index++) {
        final current = tester.getRect(fields.at(index));
        final next = tester.getRect(fields.at(index + 1));
        expect(next.top - current.bottom, greaterThanOrEqualTo(16));
      }
      final input = tester.widget<TextField>(find.byType(TextField).first);
      expect(
        input.decoration!.contentPadding,
        const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      );

      tester.state<FormState>(find.byType(Form)).validate();
      await tester.pumpAndSettle();
      final submit = find.widgetWithText(FilledButton, 'SIGN UP');
      await tester.ensureVisible(submit);
      await tester.pumpAndSettle();
      expect(submit.hitTestable(), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}
