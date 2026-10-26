import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:campushub/module_app/widgets/six_digit_code_input.dart';
import 'package:campushub/module_app/screens/components/account_recovery_dialog.dart';

void main() {
  testWidgets('numeric input advances and six-digit paste fills every box', (
    tester,
  ) async {
    String value = '';
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SixDigitCodeInput(onChanged: (code) => value = code),
        ),
      ),
    );
    await tester.pump();
    final fields = find.byType(TextField);
    expect(fields, findsNWidgets(6));
    expect(tester.widget<TextField>(fields.first).focusNode!.hasFocus, isTrue);
    await tester.enterText(fields.first, 'a1');
    expect(value, '1');
    expect(tester.widget<TextField>(fields.at(1)).focusNode!.hasFocus, isTrue);
    await tester.enterText(fields.at(1), '234567');
    for (var i = 0; i < 6; i++) {
      expect(
        tester.widget<TextField>(fields.at(i)).controller!.text,
        '${i + 2}',
      );
    }
    expect(value, '234567');
    final semantics = tester.ensureSemantics();
    expect(
      find.bySemanticsLabel(RegExp('Verification code digit')),
      findsNWidgets(6),
    );
    semantics.dispose();
  });

  testWidgets('backspace in an empty box returns to the previous digit', (
    tester,
  ) async {
    String value = '';
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SixDigitCodeInput(onChanged: (code) => value = code),
        ),
      ),
    );
    final fields = find.byType(TextField);
    await tester.enterText(fields.first, '1');
    await tester.pump();
    await tester.sendKeyEvent(LogicalKeyboardKey.backspace);
    await tester.pump();
    expect(tester.widget<TextField>(fields.first).focusNode!.hasFocus, isTrue);
    expect(value, '');
  });

  testWidgets('owner can use an admin-sent code without requesting another', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      const MaterialApp(
        home: AccountRecoveryDialog(initialEmail: 'owner@example.com'),
      ),
    );
    await tester.tap(find.text('I already have a code'));
    await tester.pumpAndSettle();
    expect(find.text('Verify Your Account'), findsOneWidget);
    expect(find.textContaining('ow***@example.com'), findsOneWidget);
    expect(find.byType(TextField), findsNWidgets(6));
    expect(find.text('Verify Code'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'initial verification shows saved email without asking for it again',
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: AccountRecoveryDialog(
            initialEmail: 'owner@example.com',
            verificationToken: 'test-session-token',
          ),
        ),
      );
      expect(find.text('Verify Email'), findsOneWidget);
      expect(find.text('ow***@example.com'), findsOneWidget);
      expect(find.byType(TextFormField), findsNothing);
      await tester.tap(find.text('I already have a code'));
      await tester.pumpAndSettle();
      expect(find.byType(TextField), findsNWidgets(6));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('code boxes fit large text on a small phone', (tester) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: const MediaQueryData(
            size: Size(320, 720),
            textScaler: TextScaler.linear(2),
          ),
          child: Scaffold(
            body: Padding(
              padding: const EdgeInsets.all(24),
              child: SixDigitCodeInput(onChanged: (_) {}),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    final fields = find.byType(TextField);
    expect(tester.getRect(fields.last).right, lessThanOrEqualTo(320));
  });
}
