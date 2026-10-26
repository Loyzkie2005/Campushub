import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../routes/app_routes.dart';
import '../services/auth_service.dart';
import '../session/session_service.dart';
import 'components/account_recovery_dialog.dart';
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
  static const Color accentGold = Color(0xFFFCB315);

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

    if (user.profileCompleted &&
        !user.emailVerified &&
        result.chatToken != null) {
      await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (_) => AccountRecoveryDialog(
          initialEmail: user.email,
          verificationToken: result.chatToken,
        ),
      );
      if (!mounted) return;
    }
    Navigator.of(context).pushReplacementNamed(
      user.profileCompleted ? AppRoutes.dashboard : AppRoutes.profileSetup,
    );
  }

  Future<void> _showAccountRecoveryDialog() async {
    final success = await showDialog<bool>(
      context: context,
      builder: (_) => AccountRecoveryDialog(initialEmail: _studentIdOrEmail),
    );

    if (!mounted || success != true) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Account recovery complete. You can return to login.'),
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
                                                        _showAccountRecoveryDialog,
                                                    child: const Text(
                                                      'Forgot Username or Password?',
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
