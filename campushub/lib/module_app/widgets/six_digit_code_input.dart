import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Six visible boxes with one canonical value; pasted codes are distributed.
class SixDigitCodeInput extends StatefulWidget {
  const SixDigitCodeInput({
    super.key,
    required this.onChanged,
    this.enabled = true,
  });
  final ValueChanged<String> onChanged;
  final bool enabled;

  @override
  State<SixDigitCodeInput> createState() => _SixDigitCodeInputState();
}

class _SixDigitCodeInputState extends State<SixDigitCodeInput> {
  final _controllers = List.generate(6, (_) => TextEditingController());
  final _focus = List.generate(6, (_) => FocusNode());

  @override
  void dispose() {
    for (final controller in _controllers) {
      controller.dispose();
    }
    for (final node in _focus) {
      node.dispose();
    }
    super.dispose();
  }

  void _changed(int index, String value) {
    final digits = value.replaceAll(RegExp(r'[^0-9]'), '');
    if (digits.length > 1) {
      final start = digits.length == 6 ? 0 : index;
      for (var i = 0; i < digits.length && start + i < 6; i++) {
        _controllers[start + i].text = digits[i];
      }
      _focus[(start + digits.length).clamp(0, 5)].requestFocus();
    } else {
      _controllers[index].text = digits;
      if (digits.isNotEmpty && index < 5) _focus[index + 1].requestFocus();
      if (digits.isEmpty && index > 0) _focus[index - 1].requestFocus();
    }
    widget.onChanged(_controllers.map((c) => c.text).join());
  }

  @override
  Widget build(BuildContext context) => Row(
    children: List.generate(
      6,
      (index) => Expanded(
        child: Padding(
          padding: EdgeInsets.only(right: index < 5 ? 6 : 0),
          child: Focus(
            onKeyEvent: (_, event) {
              if (event is KeyDownEvent &&
                  event.logicalKey == LogicalKeyboardKey.backspace &&
                  _controllers[index].text.isEmpty &&
                  index > 0) {
                _focus[index - 1].requestFocus();
                _controllers[index - 1].clear();
                widget.onChanged(_controllers.map((c) => c.text).join());
                return KeyEventResult.handled;
              }
              return KeyEventResult.ignored;
            },
            child: Semantics(
              label: 'Verification code digit ${index + 1} of 6',
              child: TextField(
                controller: _controllers[index],
                focusNode: _focus[index],
                autofocus: index == 0,
                enabled: widget.enabled,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                autofillHints: const [AutofillHints.oneTimeCode],
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(6),
                ],
                style: const TextStyle(
                  color: Color(0xFF1A1851),
                  fontSize: 20,
                  fontWeight: FontWeight.w600,
                ),
                decoration: const InputDecoration(
                  contentPadding: EdgeInsets.symmetric(vertical: 12),
                  border: OutlineInputBorder(),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFFFCB315), width: 2),
                  ),
                ),
                onChanged: (value) => _changed(index, value),
              ),
            ),
          ),
        ),
      ),
    ),
  );
}
