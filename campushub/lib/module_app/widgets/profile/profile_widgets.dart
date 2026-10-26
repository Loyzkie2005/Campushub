import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../home/home_preview_cards.dart';

abstract final class ProfileStyle {
  static const navy = HomeAppColors.navy;
  static const gold = HomeAppColors.gold;
  static const background = Colors.white;
  static const border = HomeAppColors.border;
  static const secondary = HomeAppColors.secondaryText;
  static TextStyle text(double size, {int weight = 400, Color color = navy}) =>
      TextStyle(
        fontFamily: 'Poppins',
        fontSize: size,
        color: color,
        height: 1.45,
        fontWeight: FontWeight.values[(weight ~/ 100) - 1],
      );
  static TextStyle identityText(
    double size, {
    int weight = 400,
    Color color = navy,
  }) => TextStyle(
    fontFamily: 'Montserrat',
    fontSize: size,
    color: color,
    height: 1.45,
    fontWeight: FontWeight.values[(weight ~/ 100) - 1],
    fontVariations: [FontVariation('wght', weight.toDouble())],
  );
}

class ProfileTheme extends StatelessWidget {
  const ProfileTheme({super.key, required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => Theme(
    data: ThemeData.light(useMaterial3: true).copyWith(
      scaffoldBackgroundColor: ProfileStyle.background,
      colorScheme: ColorScheme.fromSeed(
        seedColor: ProfileStyle.navy,
        brightness: Brightness.light,
        surface: Colors.white,
        primary: ProfileStyle.navy,
        secondary: ProfileStyle.gold,
      ),
      textTheme: ThemeData.light().textTheme.apply(
        fontFamily: 'Poppins',
        bodyColor: ProfileStyle.navy,
        displayColor: ProfileStyle.navy,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        foregroundColor: ProfileStyle.navy,
        titleTextStyle: ProfileStyle.text(18, weight: 700),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: ProfileStyle.navy,
          minimumSize: const Size(48, 48),
          side: const BorderSide(color: ProfileStyle.navy),
          textStyle: ProfileStyle.text(13, weight: 600),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
    ),
    child: child,
  );
}

class ProfileSection extends StatelessWidget {
  const ProfileSection({
    super.key,
    required this.title,
    required this.children,
  });
  final String title;
  final List<Widget> children;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 10),
          child: Semantics(
            header: true,
            child: Text(
              title,
              style: ProfileStyle.text(
                12,
                weight: 700,
              ).copyWith(letterSpacing: .7),
            ),
          ),
        ),
        Material(
          color: Colors.white,
          clipBehavior: Clip.antiAlias,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: ProfileStyle.border),
          ),
          child: Column(
            children: [
              for (var i = 0; i < children.length; i++) ...[
                if (i > 0)
                  const Divider(
                    height: 1,
                    indent: 52,
                    color: ProfileStyle.border,
                  ),
                children[i],
              ],
            ],
          ),
        ),
      ],
    ),
  );
}

class ProfileNavRow extends StatelessWidget {
  const ProfileNavRow({
    super.key,
    required this.icon,
    required this.title,
    required this.onTap,
    this.subtitle,
    this.count = 0,
  });
  final IconData icon;
  final String title;
  final String? subtitle;
  final int count;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => ListTile(
    minTileHeight: 60,
    minVerticalPadding: 12,
    contentPadding: const EdgeInsets.symmetric(horizontal: 16),
    leading: ExcludeSemantics(
      child: Icon(icon, size: 22, color: ProfileStyle.navy),
    ),
    title: Text(title, style: ProfileStyle.text(14, weight: 600)),
    subtitle: subtitle == null
        ? null
        : Padding(
            padding: const EdgeInsets.only(top: 3),
            child: Text(
              subtitle!,
              style: ProfileStyle.text(12, color: ProfileStyle.secondary),
            ),
          ),
    trailing: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (count > 0) ...[
          Semantics(
            label: '$count unread',
            child: ExcludeSemantics(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                decoration: BoxDecoration(
                  color: ProfileStyle.gold,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  count > 99 ? '99+' : '$count',
                  style: ProfileStyle.text(11, weight: 700),
                ),
              ),
            ),
          ),
          const SizedBox(width: 6),
        ],
        const ExcludeSemantics(
          child: Icon(
            Icons.chevron_right_rounded,
            color: ProfileStyle.navy,
            size: 20,
          ),
        ),
      ],
    ),
    onTap: onTap,
  );
}

String profileAccountType(AuthUser user) => switch (user.userType) {
  'student' => 'Student',
  'faculty' => 'Faculty / Employee',
  'guest' => 'Guest / External',
  'admin' => 'Administrator',
  _ => 'User',
};

class ProfileIdentityHeader extends StatelessWidget {
  const ProfileIdentityHeader({
    super.key,
    required this.user,
    required this.onChangePhoto,
    this.changingPhoto = false,
  });
  final AuthUser user;
  final VoidCallback onChangePhoto;
  final bool changingPhoto;
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          height: 176,
          child: Stack(
            alignment: Alignment.topCenter,
            children: [
              Container(
                height: 128,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: ProfileStyle.navy,
                  borderRadius: BorderRadius.circular(16),
                ),
                alignment: Alignment.topLeft,
                padding: const EdgeInsets.all(20),
                child: Text.rich(
                  TextSpan(
                    children: [
                      const TextSpan(text: 'Campus'),
                      const TextSpan(
                        text: 'Hub',
                        style: TextStyle(color: ProfileStyle.gold),
                      ),
                    ],
                  ),
                  style: ProfileStyle.identityText(
                    17,
                    weight: 700,
                    color: Colors.white,
                  ),
                ),
              ),
              Positioned(
                top: 80,
                child: SizedBox(
                  width: 112,
                  height: 96,
                  child: Stack(
                    alignment: Alignment.topCenter,
                    children: [
                      Semantics(
                        label: user.profilePhotoUrl.isEmpty
                            ? 'Default profile photo'
                            : 'Profile photo',
                        image: true,
                        child: Container(
                          width: 96,
                          height: 96,
                          padding: const EdgeInsets.all(4),
                          decoration: const BoxDecoration(
                            color: Colors.white,
                            shape: BoxShape.circle,
                          ),
                          child: ClipOval(
                            child: user.profilePhotoUrl.isEmpty
                                ? const _DefaultProfilePhoto()
                                : Image.network(
                                    user.resolvedProfilePhotoUrl,
                                    fit: BoxFit.cover,
                                    cacheWidth: 256,
                                    errorBuilder: (_, _, _) =>
                                        const _DefaultProfilePhoto(),
                                  ),
                          ),
                        ),
                      ),
                      Positioned(
                        right: 0,
                        bottom: 0,
                        child: IconButton(
                          key: const ValueKey('profile-change-photo'),
                          tooltip: changingPhoto
                              ? 'Updating profile picture'
                              : 'Change profile picture',
                          onPressed: changingPhoto ? null : onChangePhoto,
                          style: IconButton.styleFrom(
                            backgroundColor: ProfileStyle.gold,
                            disabledBackgroundColor: ProfileStyle.gold,
                            foregroundColor: ProfileStyle.navy,
                            minimumSize: const Size(48, 48),
                            side: const BorderSide(
                              color: Colors.white,
                              width: 3,
                            ),
                          ),
                          icon: changingPhoto
                              ? const SizedBox.square(
                                  dimension: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: ProfileStyle.navy,
                                  ),
                                )
                              : const Icon(Icons.edit_outlined, size: 20),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Text(
          user.fullName.trim().isEmpty ? user.studentId : user.fullName,
          textAlign: TextAlign.center,
          style: ProfileStyle.identityText(21, weight: 700),
        ),
        const SizedBox(height: 4),
        Text(
          profileAccountType(user),
          key: const ValueKey('profile-account-type'),
          textAlign: TextAlign.center,
          style: ProfileStyle.text(
            13,
            weight: 500,
            color: ProfileStyle.secondary,
          ),
        ),
        if (user.program.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            user.program,
            key: const ValueKey('profile-program'),
            textAlign: TextAlign.center,
            style: ProfileStyle.identityText(
              13,
              weight: 600,
              color: ProfileStyle.secondary,
            ),
          ),
        ],
        if (user.userType == 'student' && user.yearSection.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            'Year / Section: ${user.yearSection}',
            key: const ValueKey('profile-year-section'),
            textAlign: TextAlign.center,
            style: ProfileStyle.identityText(12, color: ProfileStyle.secondary),
          ),
        ],
        if (user.email.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            user.email,
            textAlign: TextAlign.center,
            style: ProfileStyle.text(12, color: ProfileStyle.secondary),
          ),
        ],
      ],
    );
  }
}

class _DefaultProfilePhoto extends StatelessWidget {
  const _DefaultProfilePhoto();

  @override
  Widget build(BuildContext context) => const ColoredBox(
    color: ProfileStyle.background,
    child: Icon(
      Icons.person_outline_rounded,
      size: 44,
      color: ProfileStyle.navy,
    ),
  );
}

class ProfileDetailScaffold extends StatelessWidget {
  const ProfileDetailScaffold({
    super.key,
    required this.title,
    required this.child,
    this.embedded = false,
  });
  final String title;
  final Widget child;
  final bool embedded;
  @override
  Widget build(BuildContext context) {
    final body = SafeArea(
      top: false,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: child,
        ),
      ),
    );
    return ProfileTheme(
      child: embedded
          ? body
          : Scaffold(
              appBar: AppBar(title: Text(title)),
              body: body,
            ),
    );
  }
}
