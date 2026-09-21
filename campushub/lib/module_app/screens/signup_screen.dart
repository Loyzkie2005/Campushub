import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/auth_service.dart';
import '../validation/password_policy.dart';
import 'components/auth_theme_toggle.dart';
import 'components/campus_legal_dialog.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key});

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _studentIdController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirm = true;
  bool _isSubmitting = false;
  bool _agreedToTerms = false;
  String? _firstNameError;
  String? _lastNameError;
  String? _usernameError;
  String? _emailError;
  String? _passwordError;
  String? _confirmPasswordError;
  String? _termsError;
  String? _generalError;

  static const Color primaryNavy = Color(0xFF1A1851);
  static const Color accentGold = Color(0xFFFCB316);

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _studentIdController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _signUp(BuildContext formContext) async {
    if (_isSubmitting) return;

    setState(_clearServerErrors);
    if (!Form.of(formContext).validate()) return;
    if (!_agreedToTerms) {
      setState(() {
        _termsError =
            'Please agree to the Terms and Conditions and Privacy Policy.';
      });
      return;
    }

    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _isSubmitting = true);

    final result = await AuthService.signUp(
      firstName: _firstNameController.text,
      lastName: _lastNameController.text,
      studentId: _studentIdController.text,
      email: _emailController.text,
      password: _passwordController.text,
      confirmPassword: _confirmPasswordController.text,
    );

    if (!mounted) return;

    if (!result.success) {
      _showSignUpError(result.message ?? 'Account creation failed.');
      return;
    }

    setState(() => _isSubmitting = false);

    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const _AccountCreatedDialog(),
    );

    if (!mounted) return;

    Navigator.pop(
      context,
      result.user?.studentId ?? _studentIdController.text.trim(),
    );
  }

  void _clearServerErrors() {
    _firstNameError = null;
    _lastNameError = null;
    _usernameError = null;
    _emailError = null;
    _passwordError = null;
    _confirmPasswordError = null;
    _termsError = null;
    _generalError = null;
  }

  void _showSignUpError(String message) {
    final normalized = message.toLowerCase();

    setState(() {
      _isSubmitting = false;
      _clearServerErrors();

      if (normalized.contains('username') && normalized.contains('email')) {
        _usernameError = message;
        _emailError = message;
      } else if (normalized.contains('username') ||
          normalized.contains('student id')) {
        _usernameError = message;
      } else if (normalized.contains('email')) {
        _emailError = message;
      } else if (normalized.contains('do not match') ||
          normalized.contains('confirm password')) {
        _confirmPasswordError = message;
      } else if (normalized.contains('password')) {
        _passwordError = message;
      } else if (normalized.contains('first name')) {
        _firstNameError = message;
      } else if (normalized.contains('last name')) {
        _lastNameError = message;
      } else {
        _generalError = message;
      }
    });
  }

  void _clearFieldError(VoidCallback clearError) {
    setState(() {
      clearError();
      _generalError = null;
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

  Future<void> _handleTermsChanged(bool shouldAgree) async {
    if (!shouldAgree) {
      setState(() {
        _agreedToTerms = false;
        _termsError = null;
      });
      return;
    }

    final accepted = await showCampusLegalDialog(context);
    if (!mounted) return;

    setState(() {
      _agreedToTerms = accepted;
      if (accepted) _termsError = null;
    });
  }

  Future<void> _openTermsAndPrivacy() async {
    final accepted = await showCampusLegalDialog(context);
    if (!mounted || !accepted) return;

    setState(() {
      _agreedToTerms = true;
      _termsError = null;
    });
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
    final mutedForeground = subtextColor;

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
          key: const Key('signup-background-surface'),
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
                    key: const Key('signup-form-scroll'),
                    physics: const ClampingScrollPhysics(),
                    child: Column(
                      children: [
                        Container(
                          key: const Key('signup-header-surface'),
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
                              SafeArea(
                                bottom: false,
                                child: Padding(
                                  padding:
                                      const EdgeInsets.fromLTRB(16, 10, 16, 0),
                                  child: Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceBetween,
                                    children: [
                                      IconButton(
                                        icon: const Icon(
                                          Icons.arrow_back_ios_new_rounded,
                                          color: Colors.white,
                                          size: 20,
                                        ),
                                        onPressed: () => Navigator.pop(context),
                                        tooltip: 'Back to login',
                                      ),
                                      const Spacer(),
                                      const AuthThemeToggle(),
                                    ],
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
                              key: const Key('signup-form-surface'),
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
                                      key: const Key('signup-form-outline'),
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
                                          // Create Account header with CampusHub on top
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
                                                  'Create Account',
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
                                                  'Create your account to get started.',
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
                                          const SizedBox(height: 24),

                                          // First Name & Last Name Row
                                          Row(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Expanded(
                                                child: _buildField(
                                                  controller:
                                                      _firstNameController,
                                                  label: 'First Name',
                                                  hintText: 'First Name',
                                                  icon: Icons.person_outline,
                                                  serverError: _firstNameError,
                                                  onChanged: (_) {
                                                    if (_firstNameError !=
                                                        null) {
                                                      _clearFieldError(
                                                        () => _firstNameError =
                                                            null,
                                                      );
                                                    }
                                                  },
                                                  textCapitalization:
                                                      TextCapitalization.words,
                                                  inputFormatters: const [
                                                    _InitialUppercaseFormatter(),
                                                  ],
                                                  validator: (v) =>
                                                      (v ?? '').trim().isEmpty
                                                      ? 'Required'
                                                      : null,
                                                ),
                                              ),
                                              const SizedBox(width: 12),
                                              Expanded(
                                                child: _buildField(
                                                  controller:
                                                      _lastNameController,
                                                  label: 'Last Name',
                                                  hintText: 'LastName',
                                                  icon: Icons.person_outline,
                                                  serverError: _lastNameError,
                                                  onChanged: (_) {
                                                    if (_lastNameError !=
                                                        null) {
                                                      _clearFieldError(
                                                        () => _lastNameError =
                                                            null,
                                                      );
                                                    }
                                                  },
                                                  textCapitalization:
                                                      TextCapitalization.words,
                                                  inputFormatters: const [
                                                    _InitialUppercaseFormatter(),
                                                  ],
                                                  validator: (v) =>
                                                      (v ?? '').trim().isEmpty
                                                      ? 'Required'
                                                      : null,
                                                ),
                                              ),
                                            ],
                                          ),

                                          // Username Field
                                          _buildField(
                                            controller: _studentIdController,
                                            label: 'Username',
                                            icon: Icons.badge_outlined,
                                            serverError: _usernameError,
                                            onChanged: (_) {
                                              if (_usernameError != null) {
                                                _clearFieldError(
                                                  () => _usernameError = null,
                                                );
                                              }
                                            },
                                            validator: (v) {
                                              final value = v?.trim() ?? '';
                                              if (value.isEmpty) {
                                                return 'Please enter a username';
                                              }
                                              if (value.length < 3) {
                                                return 'At least 3 characters';
                                              }
                                              return null;
                                            },
                                          ),

                                          // Email Field
                                          _buildField(
                                            controller: _emailController,
                                            label: 'Email',
                                            icon: Icons.email_outlined,
                                            serverError: _emailError,
                                            onChanged: (_) {
                                              if (_emailError != null) {
                                                _clearFieldError(
                                                  () => _emailError = null,
                                                );
                                              }
                                            },
                                            keyboardType:
                                                TextInputType.emailAddress,
                                            validator: (v) {
                                              if (v == null || v.isEmpty) {
                                                return 'Please enter your email';
                                              }
                                              if (!v.contains('@')) {
                                                return 'Enter a valid email';
                                              }
                                              return null;
                                            },
                                          ),

                                          // Password Field
                                          _buildField(
                                            controller: _passwordController,
                                            label: 'Password',
                                            icon: Icons.lock_outline,
                                            serverError: _passwordError,
                                            onChanged: (_) {
                                              if (_passwordError != null) {
                                                _clearFieldError(
                                                  () => _passwordError = null,
                                                );
                                              }
                                            },
                                            obscure: _obscurePassword,
                                            keyboardType:
                                                TextInputType.visiblePassword,
                                            supporting: _PasswordChecklist(
                                              controller: _passwordController,
                                            ),
                                            onToggleObscure: () => setState(
                                              () => _obscurePassword =
                                                  !_obscurePassword,
                                            ),
                                            validator: PasswordPolicy.validate,
                                          ),

                                          // Confirm Password Field
                                          _buildField(
                                            controller:
                                                _confirmPasswordController,
                                            label: 'Confirm Password',
                                            icon: Icons.lock_outline,
                                            serverError: _confirmPasswordError,
                                            onChanged: (_) {
                                              if (_confirmPasswordError !=
                                                  null) {
                                                _clearFieldError(
                                                  () => _confirmPasswordError =
                                                      null,
                                                );
                                              }
                                            },
                                            obscure: _obscureConfirm,
                                            keyboardType:
                                                TextInputType.visiblePassword,
                                            onToggleObscure: () => setState(
                                              () => _obscureConfirm =
                                                  !_obscureConfirm,
                                            ),
                                            validator: (v) {
                                              if (v == null || v.isEmpty) {
                                                return 'Please confirm your password';
                                              }
                                              if (v !=
                                                  _passwordController.text) {
                                                return 'Passwords do not match';
                                              }
                                              return null;
                                            },
                                          ),

                                          const SizedBox(height: 4),

                                          // Terms and Conditions Row
                                          Row(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.center,
                                            children: [
                                              SizedBox(
                                                width: 20,
                                                height: 20,
                                                child: Checkbox(
                                                  value: _agreedToTerms,
                                                  onChanged: _isSubmitting
                                                      ? null
                                                      : (value) =>
                                                            _handleTermsChanged(
                                                              value ?? false,
                                                            ),
                                                  activeColor: isLightMode
                                                      ? primaryNavy
                                                      : accentGold,
                                                  checkColor: isLightMode
                                                      ? Colors.white
                                                      : primaryNavy,
                                                  side: BorderSide(
                                                    color: mutedForeground,
                                                  ),
                                                  shape: RoundedRectangleBorder(
                                                    borderRadius:
                                                        BorderRadius.circular(
                                                          4,
                                                        ),
                                                  ),
                                                ),
                                              ),
                                              const SizedBox(width: 8),
                                              Expanded(
                                                child: GestureDetector(
                                                  onTap: _isSubmitting
                                                      ? null
                                                      : _openTermsAndPrivacy,
                                                  child: Text.rich(
                                                    TextSpan(
                                                      text: 'I agree to the ',
                                                      style: TextStyle(
                                                        fontSize: 13,
                                                        color: mutedForeground,
                                                      ),
                                                      children: [
                                                        TextSpan(
                                                          text:
                                                              'Terms and Conditions',
                                                          style: TextStyle(
                                                            color: accentGold,
                                                            fontWeight:
                                                                FontWeight.w700,
                                                            decoration:
                                                                TextDecoration
                                                                    .underline,
                                                          ),
                                                        ),
                                                        const TextSpan(
                                                          text: ' and ',
                                                        ),
                                                        TextSpan(
                                                          text:
                                                              'Privacy Policy',
                                                          style: TextStyle(
                                                            color: accentGold,
                                                            fontWeight:
                                                                FontWeight.w700,
                                                            decoration:
                                                                TextDecoration
                                                                    .underline,
                                                          ),
                                                        ),
                                                      ],
                                                    ),
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),
                                          if (_termsError != null)
                                            _buildInlineError(_termsError!),
                                          if (_generalError != null)
                                            _buildInlineError(_generalError!),

                                          const SizedBox(height: 22),

                                          // Sign Up button with Gold hover and click
                                          SizedBox(
                                            width: double.infinity,
                                            height: 52,
                                            child: FilledButton(
                                              onPressed: _isSubmitting
                                                  ? null
                                                  : () => _signUp(formContext),
                                              style: ButtonStyle(
                                                backgroundColor:
                                                    WidgetStateProperty.resolveWith((
                                                      states,
                                                    ) {
                                                      if (states.contains(
                                                            WidgetState.pressed,
                                                          ) ||
                                                          states.contains(
                                                            WidgetState.hovered,
                                                          )) {
                                                        return accentGold; // #FCB316 on click and hover
                                                      }
                                                      return isLightMode
                                                          ? primaryNavy
                                                          : accentGold;
                                                    }),
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
                                              child: _isSubmitting
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
                                                      'SIGN UP',
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

                                          // Already have an account? Log In footer
                                          Center(
                                            child: Wrap(
                                              alignment: WrapAlignment.center,
                                              crossAxisAlignment:
                                                  WrapCrossAlignment.center,
                                              children: [
                                                Text(
                                                  'Already have an account? ',
                                                  style: TextStyle(
                                                    color: subtextColor,
                                                    fontSize: 13,
                                                  ),
                                                ),
                                                TextButton(
                                                  onPressed: _isSubmitting
                                                      ? null
                                                      : () {
                                                          FocusManager
                                                              .instance
                                                              .primaryFocus
                                                              ?.unfocus();
                                                          Navigator.pop(
                                                            context,
                                                          );
                                                        },
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
                                                    'Log In',
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

                            // Centered Floating Circle Logo
                            Positioned(
                              top: -36,
                              child: Container(
                                key: const Key('signup-logo-circle'),
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

class _InitialUppercaseFormatter extends TextInputFormatter {
  const _InitialUppercaseFormatter();

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    if (newValue.text.isEmpty) return newValue;

    final formatted =
        newValue.text[0].toUpperCase() + newValue.text.substring(1);
    return newValue.copyWith(text: formatted, composing: TextRange.empty);
  }
}

class _PasswordChecklist extends StatelessWidget {
  const _PasswordChecklist({required this.controller});

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<TextEditingValue>(
      valueListenable: controller,
      builder: (context, value, _) {
        final password = value.text;
        return AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          transitionBuilder: (child, animation) => SizeTransition(
            sizeFactor: animation,
            axisAlignment: -1,
            child: FadeTransition(opacity: animation, child: child),
          ),
          child: password.isEmpty
              ? const SizedBox.shrink(key: ValueKey('password-rules-hidden'))
              : Column(
                  key: const ValueKey('password-rules-visible'),
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _PasswordRequirement(
                      label: '8+ characters and no spaces',
                      isMet:
                          password.length >= 8 &&
                          !RegExp(r'\s').hasMatch(password),
                    ),
                    _PasswordRequirement(
                      label: 'Uppercase and lowercase letters',
                      isMet:
                          RegExp(r'[A-Z]').hasMatch(password) &&
                          RegExp(r'[a-z]').hasMatch(password),
                    ),
                    _PasswordRequirement(
                      label: 'Number and special character',
                      isMet:
                          RegExp(r'[0-9]').hasMatch(password) &&
                          RegExp(r'[^A-Za-z0-9]').hasMatch(password) &&
                          !RegExp(r'\s').hasMatch(password),
                    ),
                  ],
                ),
        );
      },
    );
  }
}

class _PasswordRequirement extends StatelessWidget {
  const _PasswordRequirement({required this.label, required this.isMet});

  final String label;
  final bool isMet;

  @override
  Widget build(BuildContext context) {
    final isLightMode = Theme.of(context).brightness == Brightness.light;
    final textColor = isMet
        ? (isLightMode ? _SignUpScreenState.primaryNavy : Colors.white)
        : const Color(0xFFDC2626);
    return Padding(
      padding: const EdgeInsets.only(bottom: 3),
      child: Row(
        children: [
          Semantics(
            label: '$label: ${isMet ? 'complete' : 'incomplete'}',
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut,
              width: 18,
              height: 18,
              decoration: BoxDecoration(
                color: isMet
                    ? _SignUpScreenState.accentGold
                    : (isLightMode ? Colors.transparent : Colors.white),
                shape: BoxShape.circle,
                border: Border.all(
                  color: isMet
                      ? _SignUpScreenState.accentGold
                      : const Color(0xFFDC2626),
                  width: 1.4,
                ),
              ),
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 260),
                transitionBuilder: (child, animation) => ScaleTransition(
                  scale: animation,
                  child: FadeTransition(opacity: animation, child: child),
                ),
                child: Icon(
                  isMet ? Icons.check_rounded : Icons.close_rounded,
                  key: ValueKey(isMet),
                  size: 13,
                  color: isMet
                      ? _SignUpScreenState.primaryNavy
                      : const Color(0xFFDC2626),
                ),
              ),
            ),
          ),
          const SizedBox(width: 7),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                color: textColor,
                fontSize: 11,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AccountCreatedDialog extends StatefulWidget {
  const _AccountCreatedDialog();

  @override
  State<_AccountCreatedDialog> createState() => _AccountCreatedDialogState();
}

class _AccountCreatedDialogState extends State<_AccountCreatedDialog> {
  bool _animate = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      setState(() => _animate = true);
    });

    Future<void>.delayed(const Duration(milliseconds: 1300), () {
      if (!mounted) return;
      Navigator.of(context).pop();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 36),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 30),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedScale(
              scale: _animate ? 1 : 0.2,
              duration: const Duration(milliseconds: 420),
              curve: Curves.elasticOut,
              child: AnimatedOpacity(
                opacity: _animate ? 1 : 0,
                duration: const Duration(milliseconds: 220),
                child: Container(
                  width: 82,
                  height: 82,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: Color(0xFF22C55E),
                  ),
                  child: const Icon(
                    Icons.check_rounded,
                    color: Colors.white,
                    size: 54,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 22),
            const Text(
              'Account Created Successfully',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: _SignUpScreenState.primaryNavy,
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
