import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';

import '../../theme/app_typography.dart';
import 'home_preview_cards.dart';

/// Campus information only; buttons reuse Home's existing catalog-tab callbacks.
class CampusHomeBanners extends StatefulWidget {
  const CampusHomeBanners({
    super.key,
    required this.onMarketplace,
    required this.onFacilities,
    required this.onServices,
    this.active = true,
  });

  final VoidCallback onMarketplace, onFacilities, onServices;
  final bool active;

  @override
  State<CampusHomeBanners> createState() => _CampusHomeBannersState();
}

class _CampusHomeBannersState extends State<CampusHomeBanners>
    with WidgetsBindingObserver {
  static const _slides = [
    (
      title: 'Shop on Campus',
      description: 'Discover and shop products available in CampusHub.',
      action: 'Browse Products',
    ),
    (
      title: 'Explore Campus Facilities',
      description: 'Find available spaces for your activities and events.',
      action: 'View Facilities',
    ),
    (
      title: 'Campus Services Made Easy',
      description:
          'Explore university services and find the information you need.',
      action: 'View Services',
    ),
  ];
  // A multiple of three permits backward swiping from the first logical slide.
  static const _initialPage = 3000;
  static const _slideDuration = Duration(milliseconds: 450);
  static final _titleStyle = AppTypography.text(
    color: Colors.white,
    fontSize: 18,
    fontWeight: FontWeight.w700,
    height: 1.3,
  );
  static final _descriptionStyle = AppTypography.text(
    color: Colors.white,
    fontSize: 12,
    height: 1.5,
  );
  static final _buttonGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color.lerp(HomeAppColors.gold, HomeAppColors.white, .28)!,
      HomeAppColors.gold,
    ],
  );

  final _pages = PageController(initialPage: _initialPage);
  Timer? _timer;
  int _page = _initialPage;
  bool _paused = false, _focused = false, _hovered = false;
  bool _dragging = false, _resumed = true;

  int get _index => _page % _slides.length;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    final state = WidgetsBinding.instance.lifecycleState;
    _resumed = state == null || state == AppLifecycleState.resumed;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _schedule();
  }

  @override
  void didUpdateWidget(covariant CampusHomeBanners oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.active != widget.active) _schedule();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _resumed = state == AppLifecycleState.resumed;
    _schedule();
  }

  void _schedule() {
    _timer?.cancel();
    if (!widget.active ||
        !_resumed ||
        _paused ||
        _focused ||
        _hovered ||
        _dragging ||
        MediaQuery.disableAnimationsOf(context) ||
        !TickerMode.of(context) ||
        ModalRoute.of(context)?.isCurrent == false) {
      return;
    }
    _timer = Timer.periodic(const Duration(seconds: 5), (_) {
      final box = context.findRenderObject();
      if (box is! RenderBox ||
          !box.hasSize ||
          !_pages.hasClients ||
          _pages.position.isScrollingNotifier.value) {
        return;
      }
      final bounds = box.localToGlobal(Offset.zero) & box.size;
      if (!bounds.overlaps(Offset.zero & MediaQuery.sizeOf(context)) ||
          ModalRoute.of(context)?.isCurrent == false) {
        return;
      }
      _move(1, restartTimer: false);
    });
  }

  void _move(int step, {bool restartTimer = true}) {
    if (!_pages.hasClients) return;
    final target = math.max(0, _page + step);
    if (MediaQuery.disableAnimationsOf(context)) {
      _pages.jumpToPage(target);
    } else {
      _pages.animateToPage(
        target,
        duration: _slideDuration,
        curve: Curves.easeInOutCubic,
      );
    }
    if (restartTimer) _schedule();
  }

  void _togglePlayback() {
    setState(() => _paused = !_paused);
    _schedule();
  }

  void _open(int index) {
    _timer?.cancel();
    [widget.onMarketplace, widget.onFacilities, widget.onServices][index]();
  }

  double _bannerHeight(BuildContext context, double width) {
    double measure(String text, TextStyle style) {
      final painter = TextPainter(
        text: TextSpan(
          text: text,
          style: DefaultTextStyle.of(context).style.merge(style),
        ),
        textDirection: Directionality.of(context),
        textScaler: MediaQuery.textScalerOf(context),
        locale: Localizations.maybeLocaleOf(context),
      )..layout(maxWidth: math.max(1.0, width - 32));
      final height = painter.height;
      painter.dispose();
      return height;
    }

    final tallest = _slides
        .map(
          (slide) =>
              measure(slide.title, _titleStyle) +
              8 +
              measure(slide.description, _descriptionStyle),
        )
        .reduce(math.max);
    // Preserve all scaled text, the 48dp button target and 24dp extra photo space.
    return math.max(188.0, tallest + 32 + 12 + 48 + 24);
  }

  Widget _action(int index) => Stack(
    alignment: Alignment.centerLeft,
    children: [
      Positioned.fill(
        top: 7,
        bottom: 7,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: _buttonGradient,
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      TextButton(
        onPressed: () => _open(index),
        style: TextButton.styleFrom(
          foregroundColor: HomeAppColors.navy,
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 12),
          textStyle: AppTypography.text(
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        child: Text(_slides[index].action),
      ),
    ],
  );

  Widget _slide(int index) => Stack(
    fit: StackFit.expand,
    children: [
      Image.asset(
        'assets/img/ustp_oroquieta_entrance.png',
        fit: BoxFit.cover,
        cacheWidth: 1280,
        excludeFromSemantics: true,
        errorBuilder: (_, _, _) => const ColoredBox(color: HomeAppColors.navy),
      ),
      ColoredBox(color: HomeAppColors.navy.withValues(alpha: .78)),
      Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_slides[index].title, style: _titleStyle),
            const SizedBox(height: 8),
            Text(_slides[index].description, style: _descriptionStyle),
            const Spacer(),
            _action(index),
          ],
        ),
      ),
    ],
  );

  @override
  void dispose() {
    _timer?.cancel();
    _pages.dispose();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Focus(
    onFocusChange: (focused) {
      _focused = focused;
      _schedule();
    },
    child: MouseRegion(
      onEnter: (_) {
        _hovered = true;
        _schedule();
      },
      onExit: (_) {
        _hovered = false;
        _schedule();
      },
      child: Material(
        color: HomeAppColors.white,
        child: Column(
          key: const ValueKey('home-campus-banners'),
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LayoutBuilder(
              builder: (context, constraints) => SizedBox(
                key: const ValueKey('home-banner-paper'),
                height: _bannerHeight(context, constraints.maxWidth),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: NotificationListener<ScrollNotification>(
                    onNotification: (notification) {
                      if (notification is ScrollStartNotification &&
                          notification.dragDetails != null) {
                        _dragging = true;
                        _timer?.cancel();
                      } else if (notification is ScrollEndNotification &&
                          _dragging) {
                        _dragging = false;
                        _schedule();
                      }
                      return false;
                    },
                    child: PageView.builder(
                      key: const ValueKey('home-banner-pages'),
                      controller: _pages,
                      onPageChanged: (page) => setState(() => _page = page),
                      itemBuilder: (_, page) => _slide(page % _slides.length),
                    ),
                  ),
                ),
              ),
            ),
            Semantics(
              label: 'Campus banners',
              value: 'Banner ${_index + 1} of ${_slides.length}',
              increasedValue:
                  'Banner ${(_index + 1) % _slides.length + 1} of ${_slides.length}',
              decreasedValue:
                  'Banner ${(_index + _slides.length - 1) % _slides.length + 1} of ${_slides.length}',
              onIncrease: () => _move(1),
              onDecrease: () => _move(-1),
              customSemanticsActions: {
                CustomSemanticsAction(
                  label: _paused
                      ? 'Resume automatic banners'
                      : 'Pause automatic banners',
                ): _togglePlayback,
              },
              child: ExcludeSemantics(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      for (var i = 0; i < _slides.length; i++)
                        AnimatedContainer(
                          key: ValueKey('home-banner-dot-$i'),
                          duration: MediaQuery.disableAnimationsOf(context)
                              ? Duration.zero
                              : const Duration(milliseconds: 180),
                          margin: const EdgeInsets.symmetric(horizontal: 4),
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: i == _index
                                ? HomeAppColors.gold
                                : HomeAppColors.navy.withValues(alpha: .35),
                            border: i == _index
                                ? Border.all(
                                    color: HomeAppColors.navy,
                                    width: 1,
                                  )
                                : null,
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
