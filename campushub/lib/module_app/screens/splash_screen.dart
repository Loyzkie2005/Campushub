import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../routes/app_routes.dart';

/// Full institutional Navy Blue splash screen with centered logo,
/// brand typography, and smooth zoom-in animation.
class CampusHubIntroScreen extends StatefulWidget {
  const CampusHubIntroScreen({
    super.key,
    this.onFinished,
    this.autoNavigate = false,
  });

  final VoidCallback? onFinished;
  final bool autoNavigate;

  static const Color primaryNavy = Color(0xFF1A1851);
  static const Color campusGold  = Color(0xFFFCB316);

  @override
  State<CampusHubIntroScreen> createState() => _CampusHubIntroScreenState();
}

typedef SplashScreen = CampusHubIntroScreen;

class _CampusHubIntroScreenState extends State<CampusHubIntroScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  /// The whole content group zooms in from small to full size.
  late final Animation<double> _zoomIn;

  /// Fades in alongside the zoom.
  late final Animation<double> _fadeIn;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    _zoomIn = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Curves.easeOutCubic,
      ),
    );

    _fadeIn = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.50, curve: Curves.easeIn),
      ),
    );

    _controller.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        if (widget.onFinished != null) {
          widget.onFinished!();
        } else if (widget.autoNavigate && mounted) {
          Navigator.of(context).pushReplacementNamed(AppRoutes.login);
        }
      }
    });

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
        systemNavigationBarColor: CampusHubIntroScreen.primaryNavy,
        systemNavigationBarIconBrightness: Brightness.light,
      ),
      child: Scaffold(
        backgroundColor: CampusHubIntroScreen.primaryNavy,
        body: Center(
          child: AnimatedBuilder(
            animation: _controller,
            builder: (context, _) {
              return Opacity(
                opacity: _fadeIn.value.clamp(0.0, 1.0),
                child: Transform.scale(
                  scale: _zoomIn.value,
                  alignment: Alignment.center,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Image.asset(
                        'assets/img/logo_dark.png',
                        width: 120,
                        height: 120,
                        fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) =>
                            const Icon(
                              Icons.school_outlined,
                              color: Colors.white,
                              size: 80,
                            ),
                      ),
                      const SizedBox(height: 28),
                      RichText(
                        text: const TextSpan(
                          style: TextStyle(
                            fontFamily: 'Montserrat',
                            fontSize: 34,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.5,
                          ),
                          children: [
                            TextSpan(
                              text: 'Campus',
                              style: TextStyle(
                                  color: CampusHubIntroScreen.campusGold),
                            ),
                            TextSpan(
                              text: 'Hub',
                              style: TextStyle(color: Colors.white),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
