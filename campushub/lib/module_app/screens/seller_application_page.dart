import 'package:flutter/material.dart';

import '../widgets/home/home_preview_cards.dart';

/// Explains seller access before the user starts the application form.
class SellerApplicationPage extends StatelessWidget {
  const SellerApplicationPage({super.key, required this.onStart});

  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) => SellerApplicationTheme(
    child: Scaffold(
      backgroundColor: HomeAppColors.appBackground,
      appBar: AppBar(
        backgroundColor: HomeAppColors.white,
        foregroundColor: HomeAppColors.navy,
        surfaceTintColor: HomeAppColors.white,
        title: const Text('Seller Application'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: HomeAppColors.gold.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.storefront_outlined,
                  size: 28,
                  color: HomeAppColors.navy,
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Apply to sell products on CampusHub',
                style: TextStyle(
                  color: HomeAppColors.navy,
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 12),
              const _Description(
                'CampusHub allows approved users to list and manage products '
                'within the campus marketplace.',
              ),
              const SizedBox(height: 28),
              const Text(
                'Before you apply:',
                style: TextStyle(
                  color: HomeAppColors.navy,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              for (final text in const [
                'Make sure your account information is complete',
                'Provide accurate selling information',
                'Upload any required verification document',
                'Agree to the CampusHub Seller Terms and Conditions',
              ])
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: HomeAppColors.navy,
                          ),
                          child: SizedBox.square(dimension: 5),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(child: _Description(text)),
                    ],
                  ),
                ),
              const SizedBox(height: 16),
              const _Description(
                'Your application will be reviewed by the Marketplace '
                'Administrator before seller access is activated.',
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(16, 12, 16, 20),
        child: FilledButton(
          key: const ValueKey('start-seller-application'),
          onPressed: onStart,
          style: FilledButton.styleFrom(
            backgroundColor: HomeAppColors.navy,
            foregroundColor: HomeAppColors.white,
            minimumSize: const Size.fromHeight(52),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
          child: const Text('Start Application'),
        ),
      ),
    ),
  );
}

class _Description extends StatelessWidget {
  const _Description(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Text(
    text,
    style: const TextStyle(
      color: HomeAppColors.secondaryText,
      fontSize: 14,
      height: 1.55,
    ),
  );
}

/// Scoped seller-flow typography and brand colors; other screens keep their theme.
class SellerApplicationTheme extends StatelessWidget {
  const SellerApplicationTheme({super.key, required this.child});
  final Widget child;
  TextTheme _textTheme(TextTheme base) {
    TextStyle? face(TextStyle? style) =>
        style?.copyWith(fontFamily: 'Poppins', color: const Color(0xFF17172A));
    return base.copyWith(
      bodyLarge: face(base.bodyLarge),
      bodyMedium: face(base.bodyMedium),
      bodySmall: face(base.bodySmall),
      labelLarge: face(base.labelLarge),
      labelMedium: face(base.labelMedium),
      labelSmall: face(base.labelSmall),
      titleLarge: face(base.titleLarge),
      titleMedium: face(base.titleMedium),
      titleSmall: face(base.titleSmall),
      headlineLarge: face(base.headlineLarge),
      headlineMedium: face(base.headlineMedium),
      headlineSmall: face(base.headlineSmall),
      displayLarge: face(base.displayLarge),
      displayMedium: face(base.displayMedium),
      displaySmall: face(base.displaySmall),
    );
  }

  @override
  Widget build(BuildContext context) {
    final base = Theme.of(context);
    return Theme(
      data: base.copyWith(
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: HomeAppColors.navy,
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),
        textTheme: _textTheme(base.textTheme),
        appBarTheme: base.appBarTheme.copyWith(
          titleTextStyle: _textTheme(base.textTheme).titleLarge?.copyWith(
            color: HomeAppColors.navy,
            fontWeight: FontWeight.w700,
          ),
        ),
        primaryTextTheme: base.primaryTextTheme.apply(fontFamily: 'Poppins'),
        colorScheme: base.colorScheme.copyWith(
          primary: HomeAppColors.navy,
          onPrimary: HomeAppColors.white,
          secondary: HomeAppColors.gold,
          onSecondary: HomeAppColors.navy,
          surface: HomeAppColors.white,
          onSurface: const Color(0xFF17172A),
          error: const Color(0xFFDC2626),
          onError: HomeAppColors.white,
        ),
      ),
      child: child,
    );
  }
}
