import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../routes/app_routes.dart';
import '../services/auth_service.dart';
import '../session/session_service.dart';

class ProfileSetupScreen extends StatefulWidget {
  const ProfileSetupScreen({super.key});

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  static const _navy = Color(0xFF1A1851);

  final _institutionalIdFormKey = GlobalKey<FormState>();
  final _contactFormKey = GlobalKey<FormState>();
  final _institutionalIdController = TextEditingController();
  final _contactController = TextEditingController();

  int _section = 0;
  String? _userType;
  String? _error;
  bool _submitting = false;

  @override
  void dispose() {
    _institutionalIdController.dispose();
    _contactController.dispose();
    super.dispose();
  }

  bool get _requiresInstitutionalId =>
      _userType == 'student' || _userType == 'faculty';

  Future<void> _handleBack() async {
    if (_submitting) return;
    if (_section > 0) {
      setState(() {
        _section -= 1;
        _error = null;
      });
      return;
    }
    await SessionService.clearUser();
    if (!mounted) return;
    Navigator.of(
      context,
    ).pushNamedAndRemoveUntil(AppRoutes.login, (_) => false);
  }

  void _next() {
    if (_userType == null) {
      setState(() => _error = 'Select an account type to continue.');
      return;
    }
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() {
      _section = 1;
      _error = null;
      if (!_requiresInstitutionalId) {
        _institutionalIdController.clear();
      }
    });
  }

  void _nextToContact() {
    if (!(_institutionalIdFormKey.currentState?.validate() ?? false)) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() {
      _section = 2;
      _error = null;
    });
  }

  Future<void> _finish() async {
    if (_submitting || !(_contactFormKey.currentState?.validate() ?? false)) {
      return;
    }

    final token = await SessionService.loadChatToken();
    if (!mounted) return;
    if (token == null || token.isEmpty) {
      setState(() => _error = 'Your login expired. Please log in again.');
      return;
    }

    FocusManager.instance.primaryFocus?.unfocus();
    setState(() {
      _submitting = true;
      _error = null;
    });

    final result = await AuthService.completeProfile(
      token: token,
      userType: _userType!,
      institutionalId: _institutionalIdController.text,
      contactNumber: _contactController.text,
    );
    if (!mounted) return;

    final user = result.user;
    if (!result.success || user == null) {
      setState(() {
        _submitting = false;
        _error = result.message ?? 'Unable to save your profile.';
      });
      return;
    }

    await SessionService.updateUser(user, chatToken: result.chatToken);
    if (!mounted) return;
    Navigator.of(
      context,
    ).pushNamedAndRemoveUntil(AppRoutes.dashboard, (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final surface = isDark ? const Color(0xFF24215F) : Colors.white;
    final foreground = isDark ? Colors.white : _navy;
    final muted = isDark ? Colors.white70 : const Color(0xFF64748B);

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) _handleBack();
      },
      child: Scaffold(
        backgroundColor: surface,
        appBar: AppBar(
          backgroundColor: surface,
          surfaceTintColor: Colors.transparent,
          leading: IconButton(
            onPressed: _submitting ? null : _handleBack,
            icon: Icon(Icons.arrow_back, color: foreground),
            tooltip: 'Back',
          ),
          title: Text(
            'Additional Information',
            style: TextStyle(color: foreground, fontWeight: FontWeight.w700),
          ),
          centerTitle: true,
        ),
        body: SafeArea(
          top: false,
          child: ColoredBox(
            color: surface,
            child: LayoutBuilder(
              builder: (context, constraints) => SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(22, 16, 22, 28),
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minWidth: constraints.maxWidth - 44,
                    minHeight: constraints.maxHeight - 44,
                  ),
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 180),
                    child: _section == 0
                        ? _buildTypeSection(
                            foreground,
                            muted,
                            isDark,
                            constraints.maxHeight - 44,
                          )
                        : _requiresInstitutionalId && _section == 1
                        ? _buildInstitutionalIdSection(
                            foreground,
                            muted,
                            isDark,
                            constraints.maxHeight - 44,
                          )
                        : _buildContactSection(
                            foreground,
                            muted,
                            isDark,
                            constraints.maxHeight - 44,
                          ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTypeSection(
    Color foreground,
    Color muted,
    bool isDark,
    double availableHeight,
  ) {
    return SizedBox(
      key: const ValueKey('account-type-section'),
      height: availableHeight,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Tell us more about you',
            style: TextStyle(
              color: foreground,
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Select how you will use CampusHub.',
            style: TextStyle(color: muted, fontSize: 14),
          ),
          const SizedBox(height: 24),
          DropdownButtonFormField<String>(
            initialValue: _userType,
            decoration: _inputDecoration(
              hint: 'Select account type',
              icon: Icons.person_outline,
              isDark: isDark,
            ),
            items: const [
              DropdownMenuItem(value: 'student', child: Text('Student')),
              DropdownMenuItem(value: 'faculty', child: Text('Faculty')),
              DropdownMenuItem(value: 'guest', child: Text('Guest / Visitor')),
            ],
            onChanged: (value) => setState(() {
              _userType = value;
              _error = null;
            }),
          ),
          if (_error != null) _InlineError(message: _error!),
          const Spacer(),
          const SizedBox(height: 26),
          SizedBox(
            height: 52,
            child: FilledButton(
              onPressed: _next,
              style: FilledButton.styleFrom(
                backgroundColor: _navy,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              child: const Text(
                'Next',
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInstitutionalIdSection(
    Color foreground,
    Color muted,
    bool isDark,
    double availableHeight,
  ) {
    return SizedBox(
      key: const ValueKey('institutional-id-section'),
      height: availableHeight,
      child: Form(
        key: _institutionalIdFormKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              _userType == 'faculty'
                  ? 'Enter your faculty ID'
                  : 'Enter your student ID',
              style: TextStyle(
                color: foreground,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _userType == 'faculty'
                  ? 'Provide your current faculty ID.'
                  : 'Provide your current student ID.',
              style: TextStyle(color: muted, fontSize: 14),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: _institutionalIdController,
              textInputAction: TextInputAction.done,
              decoration: _inputDecoration(
                hint: _userType == 'faculty' ? 'Faculty ID' : 'Student ID',
                icon: Icons.badge_outlined,
                isDark: isDark,
              ),
              onFieldSubmitted: (_) => _nextToContact(),
              validator: (value) {
                final id = value?.trim() ?? '';
                if (id.isEmpty) return 'This ID is required.';
                if (id.length < 5) return 'Enter a valid ID.';
                return null;
              },
            ),
            if (_error != null) _InlineError(message: _error!),
            const Spacer(),
            const SizedBox(height: 26),
            SizedBox(
              height: 52,
              child: FilledButton(
                onPressed: _nextToContact,
                style: FilledButton.styleFrom(
                  backgroundColor: _navy,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: const Text(
                  'Next',
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContactSection(
    Color foreground,
    Color muted,
    bool isDark,
    double availableHeight,
  ) {
    return SizedBox(
      key: const ValueKey('contact-section'),
      height: availableHeight,
      child: Form(
        key: _contactFormKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Enter your phone number',
              style: TextStyle(
                color: foreground,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Provide your current contact number.',
              style: TextStyle(color: muted, fontSize: 14),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: _contactController,
              keyboardType: TextInputType.phone,
              textInputAction: TextInputAction.done,
              inputFormatters: [
                FilteringTextInputFormatter.allow(RegExp(r'[0-9+ -]')),
                LengthLimitingTextInputFormatter(16),
              ],
              decoration: _inputDecoration(
                hint: 'Phone number',
                icon: Icons.phone_outlined,
                isDark: isDark,
              ),
              onFieldSubmitted: (_) => _finish(),
              validator: (value) {
                final contact = (value ?? '').replaceAll(RegExp(r'[\s-]'), '');
                if (!RegExp(r'^(?:\+63|0)9\d{9}$').hasMatch(contact)) {
                  return 'Enter a valid Philippine mobile number.';
                }
                return null;
              },
            ),
            if (_error != null) _InlineError(message: _error!),
            const Spacer(),
            const SizedBox(height: 26),
            SizedBox(
              height: 52,
              child: FilledButton.icon(
                onPressed: _submitting ? null : _finish,
                style: FilledButton.styleFrom(
                  backgroundColor: _navy,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                icon: _submitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.check, size: 19),
                label: Text(
                  _submitting ? 'Saving...' : 'Finish',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecoration({
    String? hint,
    required IconData icon,
    required bool isDark,
  }) {
    final borderColor = isDark ? Colors.white38 : const Color(0xFFCBD5E1);
    const radius = BorderRadius.all(Radius.circular(14));
    return InputDecoration(
      hintText: hint,
      floatingLabelBehavior: FloatingLabelBehavior.never,
      prefixIcon: Icon(icon),
      filled: true,
      fillColor: isDark ? Colors.white.withValues(alpha: 0.05) : Colors.white,
      border: OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: borderColor),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: borderColor),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: radius,
        borderSide: const BorderSide(color: _navy, width: 1.5),
      ),
      errorBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: Color(0xFFDC2626)),
      ),
      focusedErrorBorder: const OutlineInputBorder(
        borderRadius: radius,
        borderSide: BorderSide(color: Color(0xFFDC2626), width: 1.5),
      ),
    );
  }
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFDC2626), size: 18),
          const SizedBox(width: 7),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: Color(0xFFDC2626), fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
