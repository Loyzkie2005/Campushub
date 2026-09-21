import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../routes/app_routes.dart';
import '../services/auth_service.dart';
import '../session/session_service.dart';
import '../validation/password_policy.dart';
import 'components/auth_theme_toggle.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _studentIdOrEmailController = TextEditingController();
  final _passwordController = TextEditingController();
  String _studentIdOrEmail = '';
  bool _obscurePassword = true;
  bool _isNavigating = false;
  bool _rememberMe = true;
  String? _loginError;

  static const Color primaryNavy = Color(0xFF1A1851);
  static const Color accentGold = Color(0xFFFCB316);

  @override
  void dispose() {
    _studentIdOrEmailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login(BuildContext formContext) async {
    if (_isNavigating) return;
    if (!Form.of(formContext).validate()) return;

    FocusManager.instance.primaryFocus?.unfocus();
    setState(() {
      _isNavigating = true;
      _loginError = null;
    });

    final result = await AuthService.login(
      studentIdOrEmail: _studentIdOrEmailController.text.trim(),
      password: _passwordController.text,
    );

    if (!mounted) return;

    final user = result.user;
    if (!result.success || user == null) {
      setState(() {
        _isNavigating = false;
        _loginError = result.message ?? 'Unable to log in.';
      });
      return;
    }

    await SessionService.saveUser(
      user,
      chatToken: result.chatToken,
      remember: _rememberMe,
    );
    if (!mounted) return;

    Navigator.of(context).pushReplacementNamed(
      user.profileCompleted ? AppRoutes.dashboard : AppRoutes.profileSetup,
    );
  }

  Future<void> _showForgotPasswordDialog() async {
    final success = await showDialog<bool>(
      context: context,
      builder: (_) => _ForgotPasswordDialog(initialEmail: _studentIdOrEmail),
    );

    if (!mounted || success != true) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Password updated. You can log in with your new password.',
        ),
        backgroundColor: primaryNavy,
      ),
    );
  }

  Future<void> _openSignUp() async {
    if (_isNavigating) return;

    FocusManager.instance.primaryFocus?.unfocus();
    final createdIdentifier = await Navigator.of(
      context,
    ).pushNamed<String>(AppRoutes.signup);

    if (!mounted || createdIdentifier == null || createdIdentifier.isEmpty) {
      return;
    }

    setState(() {
      _studentIdOrEmail = createdIdentifier;
      _studentIdOrEmailController.text = createdIdentifier;
    });
  }

  Widget _buildInlineError(String message) {
    return Padding(
      padding: const EdgeInsets.only(top: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFEF4444), size: 16),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: Color(0xFFEF4444), fontSize: 11),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool obscure = false,
    VoidCallback? onToggleObscure,
    TextInputType keyboardType = TextInputType.text,
    TextCapitalization textCapitalization = TextCapitalization.none,
    List<TextInputFormatter>? inputFormatters,
    Widget? supporting,
    String? serverError,
    String? hintText,
    ValueChanged<String>? onChanged,
    String? Function(String?)? validator,
  }) {
    final isLightMode = Theme.of(context).brightness == Brightness.light;
    final labelColor = isLightMode ? const Color(0xFF1E293B) : Colors.white;
    final fieldTextColor = isLightMode ? const Color(0xFF0F172A) : Colors.white;
    final fieldMutedColor = isLightMode
        ? const Color(0xFF94A3B8)
        : Colors.white54;
    final fieldFillColor = isLightMode
        ? const Color(0xFFF8FAFC)
        : Colors.white.withValues(alpha: 0.06);
    final fieldBorderColor = isLightMode
        ? const Color(0xFFE2E8F0)
        : Colors.white24;
    final fieldFocusBorder = isLightMode ? primaryNavy : accentGold;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: labelColor,
          ),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          keyboardType: keyboardType,
          textCapitalization: textCapitalization,
          inputFormatters: inputFormatters,
          obscureText: obscure,
          autocorrect: !obscure,
          enableSuggestions: !obscure,
          onChanged: onChanged,
          style: TextStyle(
            color: fieldTextColor,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
          cursorColor: fieldFocusBorder,
          decoration: InputDecoration(
            hintText: hintText ?? 'Enter your $label',
            hintStyle: TextStyle(color: fieldMutedColor, fontSize: 13),
            errorText: serverError,
            errorMaxLines: 2,
            filled: true,
            fillColor: fieldFillColor,
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 14,
            ),
            prefixIcon: Icon(icon, color: fieldMutedColor, size: 20),
            prefixIconConstraints: const BoxConstraints(minWidth: 46),
            suffixIcon: onToggleObscure != null
                ? IconButton(
                    icon: Icon(
                      obscure
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                      color: fieldMutedColor,
                      size: 20,
                    ),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(
                      minWidth: 36,
                      minHeight: 36,
                    ),
                    onPressed: onToggleObscure,
                  )
                : null,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: fieldBorderColor, width: 1.2),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: fieldBorderColor, width: 1.2),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: fieldFocusBorder, width: 1.8),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(color: Colors.redAccent, width: 1.2),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(color: Colors.redAccent, width: 1.8),
            ),
          ),
          validator: validator,
        ),
        if (supporting != null) ...[const SizedBox(height: 6), supporting],
        const SizedBox(height: 16),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final isLightMode = Theme.of(context).brightness == Brightness.light;
    const navyBackground = Color(0xFF1A1851);
    final cardBackground = isLightMode ? Colors.white : const Color(0xFF16153B);
    final headingColor = isLightMode ? primaryNavy : Colors.white;
    final subtextColor = isLightMode ? const Color(0xFF64748B) : Colors.white70;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
        statusBarBrightness: Brightness.dark,
      ),
      child: Scaffold(
        resizeToAvoidBottomInset: true,
        backgroundColor: navyBackground,
        body: Container(
          key: const Key('login-background-surface'),
          width: double.infinity,
          height: double.infinity,
          color: navyBackground,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final screenHeight = constraints.maxHeight;
              final topHeight = (screenHeight * 0.28).clamp(180.0, 240.0);
              final minFormHeight = screenHeight - topHeight;
              final bottomPadding = MediaQuery.paddingOf(context).bottom;

              return Stack(
                children: [
                  Positioned(
                    top: topHeight,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    child: Container(color: cardBackground),
                  ),

                  SingleChildScrollView(
                    key: const Key('login-form-scroll'),
                    physics: const ClampingScrollPhysics(),
                    child: Column(
                      children: [
                        Container(
                          key: const Key('login-header-surface'),
                          height: topHeight,
                          width: double.infinity,
                          color: navyBackground,
                          child: Stack(
                            fit: StackFit.expand,
                            children: [
                              Positioned.fill(
                                child: Image.asset(
                                  'assets/img/bg.png',
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, _, _) =>
                                      const SizedBox.shrink(),
                                ),
                              ),
                              Positioned.fill(
                                child: Container(
                                  color: navyBackground.withValues(alpha: 0.55),
                                ),
                              ),
                              const SafeArea(
                                bottom: false,
                                child: Padding(
                                  padding: EdgeInsets.fromLTRB(16, 10, 16, 0),
                                  child: Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    mainAxisAlignment: MainAxisAlignment.end,
                                    children: [AuthThemeToggle()],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),

                        Stack(
                          clipBehavior: Clip.none,
                          alignment: Alignment.topCenter,
                          children: [
                            Container(
                              key: const Key('login-form-surface'),
                              width: double.infinity,
                              constraints: BoxConstraints(
                                minHeight: minFormHeight,
                              ),
                              decoration: BoxDecoration(
                                color: cardBackground,
                                borderRadius: const BorderRadius.only(
                                  topLeft: Radius.circular(32),
                                  topRight: Radius.circular(32),
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withValues(alpha: 0.12),
                                    blurRadius: 22,
                                    offset: const Offset(0, -6),
                                  ),
                                ],
                              ),
                              child: Form(
                                child: Builder(
                                  builder: (formContext) {
                                    return Container(
                                      key: const Key('login-form-outline'),
                                      padding: EdgeInsets.fromLTRB(
                                        24,
                                        46,
                                        24,
                                        28 + bottomPadding,
                                      ),
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Center(
                                            child: Column(
                                              children: [
                                                RichText(
                                                  text: TextSpan(
                                                    style: const TextStyle(
                                                      fontSize: 22,
                                                      fontWeight:
                                                          FontWeight.w800,
                                                      letterSpacing: -0.3,
                                                    ),
                                                    children: [
                                                      TextSpan(
                                                        text: 'Campus',
                                                        style: TextStyle(
                                                          color: headingColor,
                                                        ),
                                                      ),
                                                      const TextSpan(
                                                        text: 'Hub',
                                                        style: TextStyle(
                                                          color: accentGold,
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                                const SizedBox(height: 30),
                                                Text(
                                                  'Welcome Back!',
                                                  textAlign: TextAlign.center,
                                                  style: TextStyle(
                                                    fontSize: 22,
                                                    fontWeight: FontWeight.w800,
                                                    color: headingColor,
                                                    letterSpacing: -0.3,
                                                  ),
                                                ),
                                                const SizedBox(height: 6),
                                                Text(
                                                  'Sign in to your account to continue.',
                                                  textAlign: TextAlign.center,
                                                  style: TextStyle(
                                                    fontSize: 13,
                                                    color: subtextColor,
                                                    fontWeight: FontWeight.w400,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                          const SizedBox(height: 28),

                                          // Username or Email field
                                          _buildField(
                                            controller:
                                                _studentIdOrEmailController,
                                            label: 'Username or Email',
                                            hintText:
                                                'Enter your username or email',
                                            icon: Icons.person_outline,
                                            onChanged: (value) {
                                              _studentIdOrEmail = value.trim();
                                              if (_loginError != null) {
                                                setState(
                                                  () => _loginError = null,
                                                );
                                              }
                                            },
                                            validator: (v) {
                                              if ((v ?? '').trim().isEmpty) {
                                                return 'Please enter your username or email';
                                              }
                                              return null;
                                            },
                                          ),

                                          _buildField(
                                            controller: _passwordController,
                                            label: 'Password',
                                            hintText: 'Enter your password',
                                            icon: Icons.lock_outline,
                                            obscure: _obscurePassword,
                                            onToggleObscure: () => setState(
                                              () => _obscurePassword =
                                                  !_obscurePassword,
                                            ),
                                            onChanged: (_) {
                                              if (_loginError != null) {
                                                setState(
                                                  () => _loginError = null,
                                                );
                                              }
                                            },
                                            validator: (v) {
                                              if (v == null || v.isEmpty) {
                                                return 'Please enter your password';
                                              }
                                              return null;
                                            },
                                          ),

                                          if (_loginError != null)
                                            _buildInlineError(_loginError!),

                                          const SizedBox(height: 8),

                                          Row(
                                            mainAxisAlignment:
                                                MainAxisAlignment.spaceBetween,
                                            children: [
                                              Flexible(
                                                child: GestureDetector(
                                                  onTap: () => setState(
                                                    () => _rememberMe =
                                                        !_rememberMe,
                                                  ),
                                                  child: Row(
                                                    mainAxisSize:
                                                        MainAxisSize.min,
                                                    children: [
                                                      SizedBox(
                                                        width: 18,
                                                        height: 18,
                                                        child: Checkbox(
                                                          value: _rememberMe,
                                                          materialTapTargetSize:
                                                              MaterialTapTargetSize
                                                                  .shrinkWrap,
                                                          visualDensity:
                                                              VisualDensity
                                                                  .compact,
                                                          activeColor:
                                                              isLightMode
                                                              ? primaryNavy
                                                              : accentGold,
                                                          checkColor:
                                                              isLightMode
                                                              ? Colors.white
                                                              : primaryNavy,
                                                          side: BorderSide(
                                                            color: subtextColor,
                                                          ),
                                                          shape: RoundedRectangleBorder(
                                                            borderRadius:
                                                                BorderRadius.circular(
                                                                  4,
                                                                ),
                                                          ),
                                                          onChanged: (v) =>
                                                              setState(
                                                                () =>
                                                                    _rememberMe =
                                                                        v ??
                                                                        false,
                                                              ),
                                                        ),
                                                      ),
                                                      const SizedBox(width: 6),
                                                      Flexible(
                                                        child: Text(
                                                          'Remember me',
                                                          maxLines: 1,
                                                          overflow: TextOverflow
                                                              .ellipsis,
                                                          style: TextStyle(
                                                            color: subtextColor,
                                                            fontSize: 12,
                                                          ),
                                                        ),
                                                      ),
                                                    ],
                                                  ),
                                                ),
                                              ),
                                              const SizedBox(width: 8),
                                              Flexible(
                                                child: Align(
                                                  alignment:
                                                      Alignment.centerRight,
                                                  child: GestureDetector(
                                                    onTap:
                                                        _showForgotPasswordDialog,
                                                    child: const Text(
                                                      'Forgot password?',
                                                      maxLines: 1,
                                                      overflow:
                                                          TextOverflow.ellipsis,
                                                      textAlign:
                                                          TextAlign.right,
                                                      style: TextStyle(
                                                        color: accentGold,
                                                        fontSize: 12,
                                                        fontWeight:
                                                            FontWeight.w600,
                                                      ),
                                                    ),
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),

                                          const SizedBox(height: 24),

                                          SizedBox(
                                            width: double.infinity,
                                            height: 52,
                                            child: FilledButton(
                                              onPressed: _isNavigating
                                                  ? null
                                                  : () => _login(formContext),
                                              style: ButtonStyle(
                                                backgroundColor:
                                                    WidgetStateProperty.resolveWith(
                                                      (states) {
                                                        if (states.contains(
                                                              WidgetState
                                                                  .pressed,
                                                            ) ||
                                                            states.contains(
                                                              WidgetState
                                                                  .hovered,
                                                            )) {
                                                          return accentGold;
                                                        }
                                                        return isLightMode
                                                            ? primaryNavy
                                                            : accentGold;
                                                      },
                                                    ),
                                                foregroundColor:
                                                    WidgetStateProperty.resolveWith(
                                                      (states) {
                                                        if (states.contains(
                                                              WidgetState
                                                                  .pressed,
                                                            ) ||
                                                            states.contains(
                                                              WidgetState
                                                                  .hovered,
                                                            )) {
                                                          return primaryNavy;
                                                        }
                                                        return isLightMode
                                                            ? Colors.white
                                                            : primaryNavy;
                                                      },
                                                    ),
                                                overlayColor:
                                                    WidgetStateProperty.resolveWith(
                                                      (states) {
                                                        if (states.contains(
                                                              WidgetState
                                                                  .pressed,
                                                            ) ||
                                                            states.contains(
                                                              WidgetState
                                                                  .hovered,
                                                            )) {
                                                          return accentGold
                                                              .withValues(
                                                                alpha: 0.2,
                                                              );
                                                        }
                                                        return null;
                                                      },
                                                    ),
                                                shape:
                                                    const WidgetStatePropertyAll(
                                                      RoundedRectangleBorder(
                                                        borderRadius:
                                                            BorderRadius.all(
                                                              Radius.circular(
                                                                26,
                                                              ),
                                                            ),
                                                      ),
                                                    ),
                                                elevation:
                                                    const WidgetStatePropertyAll(
                                                      0,
                                                    ),
                                              ),
                                              child: _isNavigating
                                                  ? SizedBox(
                                                      width: 22,
                                                      height: 22,
                                                      child:
                                                          CircularProgressIndicator(
                                                            strokeWidth: 2.4,
                                                            color: isLightMode
                                                                ? Colors.white
                                                                : primaryNavy,
                                                          ),
                                                    )
                                                  : const Text(
                                                      'Login',
                                                      style: TextStyle(
                                                        fontSize: 15,
                                                        fontWeight:
                                                            FontWeight.w700,
                                                        letterSpacing: 1.0,
                                                      ),
                                                    ),
                                            ),
                                          ),

                                          const SizedBox(height: 18),

                                          Center(
                                            child: Wrap(
                                              alignment: WrapAlignment.center,
                                              crossAxisAlignment:
                                                  WrapCrossAlignment.center,
                                              children: [
                                                Text(
                                                  "Don't have an account? ",
                                                  style: TextStyle(
                                                    color: subtextColor,
                                                    fontSize: 13,
                                                  ),
                                                ),
                                                TextButton(
                                                  onPressed: _isNavigating
                                                      ? null
                                                      : _openSignUp,
                                                  style: TextButton.styleFrom(
                                                    foregroundColor: isLightMode
                                                        ? primaryNavy
                                                        : accentGold,
                                                    padding:
                                                        const EdgeInsets.symmetric(
                                                          horizontal: 4,
                                                          vertical: 8,
                                                        ),
                                                    minimumSize: Size.zero,
                                                    tapTargetSize:
                                                        MaterialTapTargetSize
                                                            .shrinkWrap,
                                                  ),
                                                  child: const Text(
                                                    'Signup',
                                                    style: TextStyle(
                                                      fontSize: 13,
                                                      fontWeight:
                                                          FontWeight.w700,
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  },
                                ),
                              ),
                            ),
                            Positioned(
                              top: -36,
                              child: Container(
                                key: const Key('login-logo-circle'),
                                width: 72,
                                height: 72,
                                decoration: BoxDecoration(
                                  color: isLightMode
                                      ? Colors.white
                                      : const Color(0xFF16153B),
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: isLightMode
                                        ? const Color(0xFFE2E8F0)
                                        : Colors.white.withValues(alpha: 0.18),
                                    width: 3,
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withValues(
                                        alpha: 0.14,
                                      ),
                                      blurRadius: 16,
                                      offset: const Offset(0, 4),
                                    ),
                                  ],
                                ),
                                alignment: Alignment.center,
                                padding: const EdgeInsets.all(12),
                                child: Image.asset(
                                  isLightMode
                                      ? 'assets/img/logo.png'
                                      : 'assets/img/logo_dark.png',
                                  width: 44,
                                  height: 44,
                                  fit: BoxFit.contain,
                                  errorBuilder: (_, _, _) => Icon(
                                    Icons.school,
                                    color: isLightMode
                                        ? primaryNavy
                                        : Colors.white,
                                    size: 32,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}

class _ForgotPasswordDialog extends StatefulWidget {
  const _ForgotPasswordDialog({required this.initialEmail});

  final String initialEmail;

  @override
  State<_ForgotPasswordDialog> createState() => _ForgotPasswordDialogState();
}

enum _ResetStep { email, code, newPassword }

class _ForgotPasswordDialogState extends State<_ForgotPasswordDialog> {
  late final TextEditingController _resetEmailController =
      TextEditingController(text: widget.initialEmail);
  late final List<TextEditingController> _codeControllers = List.generate(
    6,
    (_) => TextEditingController(),
  );
  late final List<FocusNode> _codeFocusNodes = List.generate(
    6,
    (_) => FocusNode(),
  );
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  _ResetStep _step = _ResetStep.email;
  bool _isLoading = false;
  String? _verifiedCode;

  @override
  void dispose() {
    _resetEmailController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    for (final controller in _codeControllers) {
      controller.dispose();
    }
    for (final focusNode in _codeFocusNodes) {
      focusNode.dispose();
    }
    super.dispose();
  }

  String get _email => _resetEmailController.text.trim();

  String get _code =>
      _codeControllers.map((controller) => controller.text).join();

  Future<void> _sendLink(BuildContext formContext) async {
    if (!Form.of(formContext).validate()) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _isLoading = true);

    final result = await AuthService.sendPasswordResetCode(email: _email);

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (!result.success) {
      _showError(result.message ?? 'Failed to send reset code.');
      return;
    }

    if (!result.emailSent) {
      _showError(
        result.message ??
            'Gmail did not send. Add App Password in gmail_local.py and restart Django.',
      );
      return;
    }

    for (final controller in _codeControllers) {
      controller.clear();
    }

    setState(() => _step = _ResetStep.code);

    _showSuccess(
      result.message ?? 'Check your Gmail inbox for the 6-digit code.',
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _codeFocusNodes.first.requestFocus();
    });
  }

  Future<void> _verifyCode() async {
    if (_code.length < 6) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _isLoading = true);

    final result = await AuthService.verifyPasswordResetCode(
      email: _email,
      code: _code,
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (!result.success) {
      _showError(result.message ?? 'Invalid code.');
      return;
    }

    setState(() {
      _verifiedCode = _code;
      _step = _ResetStep.newPassword;
    });
  }

  Future<void> _confirmNewPassword(BuildContext formContext) async {
    if (!Form.of(formContext).validate()) return;
    if (_verifiedCode == null) return;

    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _isLoading = true);

    final result = await AuthService.confirmPasswordReset(
      email: _email,
      code: _verifiedCode!,
      newPassword: _newPasswordController.text,
      confirmPassword: _confirmPasswordController.text,
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (!result.success) {
      _showError(result.message ?? 'Could not update password.');
      return;
    }

    Navigator.of(context).pop(true);
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: _LoginScreenState.primaryNavy,
      ),
    );
  }

  String _titleForStep() {
    switch (_step) {
      case _ResetStep.email:
        return 'Step 1 — Email';
      case _ResetStep.code:
        return 'Step 2 — 6-Digit Code';
      case _ResetStep.newPassword:
        return 'Step 3 — New Password';
    }
  }

  Widget _stepIndicator() {
    final stepIndex = switch (_step) {
      _ResetStep.email => 1,
      _ResetStep.code => 2,
      _ResetStep.newPassword => 3,
    };
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (i) {
        final n = i + 1;
        final active = n <= stepIndex;
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4),
          child: Container(
            width: 28,
            height: 28,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: active
                  ? _LoginScreenState.primaryNavy
                  : Colors.grey.shade300,
            ),
            child: Text(
              '$n',
              style: TextStyle(
                color: active ? Colors.white : Colors.black54,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        );
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      child: Builder(
        builder: (formContext) {
          return AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            title: Text(
              _titleForStep(),
              style: const TextStyle(
                color: _LoginScreenState.primaryNavy,
                fontWeight: FontWeight.w700,
              ),
            ),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _stepIndicator(),
                  const SizedBox(height: 16),
                  if (_step == _ResetStep.email) ...[
                    const Text(
                      'Enter the email you used when you signed up (any address — '
                      'Gmail, Yahoo, school email, etc.). We will send a 6-digit code there.',
                      style: TextStyle(color: Colors.black54, fontSize: 14),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _resetEmailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.email_outlined),
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Please enter your email';
                        }
                        if (!value.contains('@')) return 'Enter a valid email';
                        return null;
                      },
                    ),
                  ] else if (_step == _ResetStep.code) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE8F5E9),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFF81C784)),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.mark_email_read_outlined,
                            color: Color(0xFF2E7D32),
                            size: 22,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Open Gmail app for $_email.\n'
                              'Subject: CampusHub Password Reset Code\n'
                              '(Also check Spam folder.)',
                              style: const TextStyle(
                                color: Color(0xFF2E7D32),
                                fontSize: 13,
                                height: 1.35,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: List.generate(6, (index) {
                        return SizedBox(
                          width: 38,
                          height: 48,
                          child: TextField(
                            controller: _codeControllers[index],
                            focusNode: _codeFocusNodes[index],
                            keyboardType: TextInputType.number,
                            textAlign: TextAlign.center,
                            maxLength: 1,
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                            ),
                            decoration: const InputDecoration(
                              counterText: '',
                              contentPadding: EdgeInsets.zero,
                              border: OutlineInputBorder(),
                            ),
                            onChanged: (value) {
                              if (value.isNotEmpty && index < 5) {
                                _codeFocusNodes[index + 1].requestFocus();
                              }
                              if (value.isEmpty && index > 0) {
                                _codeFocusNodes[index - 1].requestFocus();
                              }
                              setState(() {});
                            },
                          ),
                        );
                      }),
                    ),
                  ] else ...[
                    const Text(
                      'Choose a new password for your account.',
                      style: TextStyle(color: Colors.black54, fontSize: 14),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _newPasswordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: 'New password',
                        helperText: PasswordPolicy.requirements,
                        helperMaxLines: 2,
                        border: OutlineInputBorder(),
                      ),
                      validator: PasswordPolicy.validate,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _confirmPasswordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: 'Confirm password',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) {
                        if (v != _newPasswordController.text) {
                          return 'Passwords do not match';
                        }
                        return null;
                      },
                    ),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: _isLoading
                    ? null
                    : () => Navigator.of(context).pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: _isLoading
                    ? null
                    : () {
                        switch (_step) {
                          case _ResetStep.email:
                            _sendLink(formContext);
                          case _ResetStep.code:
                            _verifyCode();
                          case _ResetStep.newPassword:
                            _confirmNewPassword(formContext);
                        }
                      },
                style: ElevatedButton.styleFrom(
                  backgroundColor: _LoginScreenState.primaryNavy,
                  foregroundColor: Colors.white,
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Text(
                        _step == _ResetStep.email
                            ? 'Send Code'
                            : _step == _ResetStep.code
                            ? 'Verify'
                            : 'Save Password',
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}
