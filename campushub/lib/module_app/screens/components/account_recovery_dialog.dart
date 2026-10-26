import 'dart:async';
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../../session/session_service.dart';
import '../../validation/password_policy.dart';
import '../../widgets/six_digit_code_input.dart';

/// Owner-only recovery. A login token fixes initial verification to the saved email.
class AccountRecoveryDialog extends StatefulWidget {
  const AccountRecoveryDialog({
    super.key,
    this.initialEmail = '',
    this.verificationToken,
  });
  final String initialEmail;
  final String? verificationToken;
  @override
  State<AccountRecoveryDialog> createState() => _AccountRecoveryDialogState();
}

enum _RecoveryStep { email, code, password, complete }

class _AccountRecoveryDialogState extends State<AccountRecoveryDialog> {
  static const _navy = Color(0xFF1A1851);
  final _formKey = GlobalKey<FormState>();
  late final _email = TextEditingController(
    text: widget.initialEmail.contains('@') ? widget.initialEmail : '',
  );
  final _password = TextEditingController(),
      _confirmation = TextEditingController();
  late String _purpose = widget.verificationToken == null
      ? 'password'
      : 'email_verification';
  _RecoveryStep _step = _RecoveryStep.email;
  String _code = '', _masked = '', _username = '';
  String? _grant, _error;
  bool _busy = false, _showPassword = false, _showConfirmation = false;
  int _cooldown = 0, _codeVersion = 0;
  Timer? _timer;

  @override
  void dispose() {
    _timer?.cancel();
    _email.dispose();
    _password.dispose();
    _confirmation.dispose();
    super.dispose();
  }

  String get _maskedEmail {
    if (_masked.isNotEmpty) return _masked;
    final parts = _email.text.trim().split('@');
    return parts.length == 2
        ? '${parts.first.substring(0, parts.first.length.clamp(0, 2))}***@${parts.last}'
        : '';
  }

  void _startCooldown() {
    _timer?.cancel();
    _cooldown = 60;
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() => _cooldown--);
      if (_cooldown <= 0) timer.cancel();
    });
  }

  Future<void> _send({bool existingCode = false}) async {
    if (_busy ||
        (_step == _RecoveryStep.email &&
            !(_formKey.currentState?.validate() ?? false))) {
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final result = existingCode
        ? null
        : await AuthService.sendRecoveryCode(
            email: _email.text,
            purpose: _purpose,
            token: widget.verificationToken,
          );
    if (!mounted) return;
    setState(() {
      _busy = false;
      if (result != null && !result.success) {
        _error = result.message;
        return;
      }
      _masked = result?.maskedEmail ?? '';
      _code = '';
      _grant = null;
      _codeVersion++;
      _step = _RecoveryStep.code;
      if (!existingCode) _startCooldown();
    });
  }

  Future<void> _verify() async {
    if (_busy || _code.length != 6) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final result = await AuthService.verifyRecoveryCode(
      email: _email.text,
      code: _code,
      purpose: _purpose,
      token: widget.verificationToken,
    );
    if (!mounted) return;
    if (result.success && result.user != null) {
      await SessionService.updateUser(result.user!);
    }
    if (!mounted) return;
    setState(() {
      _busy = false;
      if (!result.success) {
        _error = result.message ?? 'Invalid verification code.';
        return;
      }
      _code =
          ''; // The code has been consumed. Never reuse it for password completion.
      _grant = result.recoveryGrant;
      _username = result.recoveredUsername ?? '';
      _step = _purpose == 'password'
          ? _RecoveryStep.password
          : _RecoveryStep.complete;
    });
  }

  Future<void> _save() async {
    if (_busy ||
        _grant == null ||
        !(_formKey.currentState?.validate() ?? false)) {
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final result = await AuthService.confirmPasswordReset(
      email: _email.text,
      recoveryGrant: _grant!,
      newPassword: _password.text,
      confirmPassword: _confirmation.text,
    );
    if (!mounted) return;
    setState(() {
      _busy = false;
      if (!result.success) {
        _error = result.message;
        return;
      }
      _grant = null;
      _password.clear();
      _confirmation.clear();
      _step = _RecoveryStep.complete;
    });
  }

  String get _title => switch (_step) {
    _RecoveryStep.email =>
      widget.verificationToken != null ? 'Verify Email' : 'Account Recovery',
    _RecoveryStep.code => 'Verify Your Account',
    _RecoveryStep.password => 'Create New Password',
    _RecoveryStep.complete =>
      _purpose == 'password'
          ? 'Password Updated Successfully'
          : _purpose == 'username'
          ? 'Username Recovered'
          : 'Email Verified',
  };

  @override
  Widget build(BuildContext context) => Theme(
    data: ThemeData.light().copyWith(
      colorScheme: const ColorScheme.light(
        primary: _navy,
        secondary: Color(0xFFFCB315),
      ),
      textTheme: ThemeData.light().textTheme.apply(
        fontFamily: 'Poppins',
        bodyColor: _navy,
        displayColor: _navy,
      ),
    ),
    child: AlertDialog(
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.transparent,
      insetPadding: const EdgeInsets.all(16),
      title: Text(
        _title,
        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
      ),
      content: SizedBox(
        width: 360,
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_step == _RecoveryStep.email) ...[
                  if (widget.verificationToken == null) ...[
                    const Text(
                      'Use your recorded, verified email. Request a code here, then enter it on your own device.',
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      isExpanded: true,
                      initialValue: _purpose,
                      decoration: const InputDecoration(
                        labelText: 'Recovery action',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'password',
                          child: Text('Reset Password'),
                        ),
                        DropdownMenuItem(
                          value: 'username',
                          child: Text('Recover Username'),
                        ),
                        DropdownMenuItem(
                          value: 'email_verification',
                          child: Text('Verify Email'),
                        ),
                      ],
                      onChanged: _busy
                          ? null
                          : (value) => setState(() => _purpose = value!),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _email,
                      enabled: !_busy,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Recorded Email',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) =>
                          value != null &&
                              RegExp(
                                r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                              ).hasMatch(value.trim())
                          ? null
                          : 'Enter a valid email address.',
                    ),
                    TextButton(
                      onPressed: _busy ? null : () => _send(existingCode: true),
                      child: const Text('I already have a code'),
                    ),
                  ] else ...[
                    const Text(
                      'Verify the email already recorded during sign up.',
                    ),
                    const SizedBox(height: 12),
                    Text(_maskedEmail),
                    TextButton(
                      onPressed: _busy ? null : () => _send(existingCode: true),
                      child: const Text('I already have a code'),
                    ),
                  ],
                ],
                if (_step == _RecoveryStep.code) ...[
                  Text(
                    'Enter the 6-digit verification code sent to:\n$_maskedEmail',
                  ),
                  const SizedBox(height: 20),
                  const Text('Verification Code'),
                  const SizedBox(height: 8),
                  SixDigitCodeInput(
                    key: ValueKey(_codeVersion),
                    enabled: !_busy,
                    onChanged: (value) => setState(() => _code = value),
                  ),
                  const SizedBox(height: 12),
                  const Text('Code expires in 15 minutes.'),
                  const SizedBox(height: 12),
                  const Text("Didn't receive the code?"),
                  TextButton(
                    onPressed: _busy || _cooldown > 0 ? null : () => _send(),
                    child: Text(
                      _cooldown > 0
                          ? 'Resend Code (${_cooldown}s)'
                          : 'Resend Code',
                    ),
                  ),
                  TextButton(
                    onPressed: _busy
                        ? null
                        : () => setState(() {
                            _step = _RecoveryStep.email;
                            _grant = null;
                            _error = null;
                          }),
                    child: const Text('Change recovery action or email'),
                  ),
                ],
                if (_step == _RecoveryStep.password) ...[
                  TextFormField(
                    controller: _password,
                    obscureText: !_showPassword,
                    enabled: !_busy,
                    validator: PasswordPolicy.validate,
                    decoration: InputDecoration(
                      labelText: 'New Password *',
                      border: const OutlineInputBorder(),
                      helperText: PasswordPolicy.requirements,
                      helperMaxLines: 4,
                      suffixIcon: IconButton(
                        tooltip: _showPassword
                            ? 'Hide password'
                            : 'Show password',
                        onPressed: () =>
                            setState(() => _showPassword = !_showPassword),
                        icon: Icon(
                          _showPassword
                              ? Icons.visibility_off
                              : Icons.visibility,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _confirmation,
                    obscureText: !_showConfirmation,
                    enabled: !_busy,
                    validator: (value) => value == _password.text
                        ? null
                        : 'Passwords do not match.',
                    decoration: InputDecoration(
                      labelText: 'Confirm New Password *',
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        tooltip: _showConfirmation
                            ? 'Hide confirmation'
                            : 'Show confirmation',
                        onPressed: () => setState(
                          () => _showConfirmation = !_showConfirmation,
                        ),
                        icon: Icon(
                          _showConfirmation
                              ? Icons.visibility_off
                              : Icons.visibility,
                        ),
                      ),
                    ),
                  ),
                ],
                if (_step == _RecoveryStep.complete) ...[
                  if (_purpose == 'username') ...[
                    const Text('Username / School ID'),
                    const SizedBox(height: 8),
                    SelectableText(_username),
                  ] else
                    Text(
                      _purpose == 'password'
                          ? 'Your password has been changed.'
                          : 'Your recorded email is now verified.',
                    ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Semantics(
                    liveRegion: true,
                    child: Text(_error!, style: const TextStyle(color: _navy)),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
      actions: [
        if (_step != _RecoveryStep.complete)
          TextButton(
            onPressed: _busy ? null : () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
        FilledButton(
          onPressed: _busy || (_step == _RecoveryStep.code && _code.length != 6)
              ? null
              : () {
                  switch (_step) {
                    case _RecoveryStep.email:
                      _send();
                    case _RecoveryStep.code:
                      _verify();
                    case _RecoveryStep.password:
                      _save();
                    case _RecoveryStep.complete:
                      Navigator.pop(context, true);
                  }
                },
          child: _busy
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : Text(switch (_step) {
                  _RecoveryStep.email => 'Send Verification Code',
                  _RecoveryStep.code => 'Verify Code',
                  _RecoveryStep.password => 'Update Password',
                  _RecoveryStep.complete =>
                    widget.verificationToken == null
                        ? 'Back to Login'
                        : 'Continue',
                }),
        ),
      ],
    ),
  );
}
