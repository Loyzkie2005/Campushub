import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Brief centered loading spinner, then check + label after add to cart.
class AddToCartFeedback {
  AddToCartFeedback._();

  static void show(
    BuildContext context, {
    String message = 'Add to Cart',
  }) {
    final overlay = Overlay.of(context, rootOverlay: true);
    late final OverlayEntry entry;

    entry = OverlayEntry(
      builder: (_) => _AddToCartCheckOverlay(
        message: message,
        onComplete: () => entry.remove(),
      ),
    );

    overlay.insert(entry);
  }
}

class _AddToCartCheckOverlay extends StatefulWidget {
  const _AddToCartCheckOverlay({
    required this.message,
    required this.onComplete,
  });

  final String message;
  final VoidCallback onComplete;

  @override
  State<_AddToCartCheckOverlay> createState() => _AddToCartCheckOverlayState();
}

class _AddToCartCheckOverlayState extends State<_AddToCartCheckOverlay>
    with TickerProviderStateMixin {
  static const double _iconSize = 96;

  /// Timeline ends loading and starts check reveal.
  static const double _loadingEndAt = 0.54;

  /// Check finishes drawing.
  static const double _checkDoneAt = 0.78;

  late final AnimationController _timeline;
  late final AnimationController _spinner;

  @override
  void initState() {
    super.initState();
    _spinner = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 850),
    )..repeat();

    _timeline = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1700),
    );

    _timeline.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _spinner.stop();
        widget.onComplete();
      }
    });

    _timeline.addListener(() {
      if (_timeline.value >= _loadingEndAt && _spinner.isAnimating) {
        _spinner.stop();
      }
    });

    _timeline.forward();
  }

  @override
  void dispose() {
    _spinner.dispose();
    _timeline.dispose();
    super.dispose();
  }

  double get _t => _timeline.value;

  double get _overlayOpacity {
    if (_t < 0.05) return _t / 0.05;
    if (_t > 0.9) return (1 - _t) / 0.1;
    return 1;
  }

  double get _loaderOpacity {
    if (_t >= _loadingEndAt) {
      final fade = 1 - ((_t - _loadingEndAt) / 0.08).clamp(0.0, 1.0);
      return fade;
    }
    return 1;
  }

  double get _checkOpacity {
    if (_t < _loadingEndAt) return 0;
    return ((_t - _loadingEndAt) / 0.10).clamp(0.0, 1.0);
  }

  double get _checkDrawProgress {
    if (_t < _loadingEndAt) return 0;
    return ((_t - _loadingEndAt) / (_checkDoneAt - _loadingEndAt))
        .clamp(0.0, 1.0);
  }

  double get _textOpacity {
    if (_t < _loadingEndAt + 0.06) return 0;
    if (_t < _loadingEndAt + 0.16) {
      return (_t - (_loadingEndAt + 0.06)) / 0.10;
    }
    if (_t > 0.9) return (1 - _t) / 0.1;
    return 1;
  }

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Material(
        type: MaterialType.transparency,
        child: SizedBox.expand(
          child: Center(
            child: AnimatedBuilder(
              animation: Listenable.merge([_timeline, _spinner]),
              builder: (context, _) {
                return Opacity(
                  opacity: _overlayOpacity.clamp(0.0, 1.0),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SizedBox(
                        width: _iconSize,
                        height: _iconSize,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            Opacity(
                              opacity: _loaderOpacity.clamp(0.0, 1.0),
                              child: CustomPaint(
                                size: const Size(_iconSize, _iconSize),
                                painter: _LoadingSpinnerPainter(
                                  rotation: _spinner.value,
                                ),
                              ),
                            ),
                            Opacity(
                              opacity: _checkOpacity.clamp(0.0, 1.0),
                              child: CustomPaint(
                                size: const Size(_iconSize, _iconSize),
                                painter: _CheckPainter(
                                  progress: Curves.easeOutCubic.transform(
                                    _checkDrawProgress,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      Opacity(
                        opacity: _textOpacity.clamp(0.0, 1.0),
                        child: Text(
                          widget.message,
                          style: const TextStyle(
                            color: Color(0xFF1A1851),
                            fontSize: 18,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 0.2,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

/// Navy indeterminate loading ring (spins continuously).
class _LoadingSpinnerPainter extends CustomPainter {
  _LoadingSpinnerPainter({required this.rotation});

  final double rotation;

  static const Color _navyColor = Color(0xFF1A1851);
  static const double _strokeWidth = 4;
  static const double _sweep = math.pi * 1.55;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - _strokeWidth;
    final rect = Rect.fromCircle(center: center, radius: radius);

    final trackPaint = Paint()
      ..color = _navyColor.withValues(alpha: 0.12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = _strokeWidth;

    canvas.drawCircle(center, radius, trackPaint);

    final spinPaint = Paint()
      ..color = _navyColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = _strokeWidth
      ..strokeCap = StrokeCap.round;

    final startAngle = rotation * math.pi * 2 - math.pi / 2;
    canvas.drawArc(rect, startAngle, _sweep, false, spinPaint);
  }

  @override
  bool shouldRepaint(covariant _LoadingSpinnerPainter oldDelegate) {
    return oldDelegate.rotation != rotation;
  }
}

/// Navy check drawn after loading finishes.
class _CheckPainter extends CustomPainter {
  _CheckPainter({required this.progress});

  final double progress;

  static const Color _navyColor = Color(0xFF1A1851);
  static const double _strokeWidth = 6;

  @override
  void paint(Canvas canvas, Size size) {
    if (progress <= 0) return;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - _strokeWidth;

    final checkPath = Path()
      ..moveTo(center.dx - radius * 0.42, center.dy + radius * 0.04)
      ..lineTo(center.dx - radius * 0.08, center.dy + radius * 0.36)
      ..lineTo(center.dx + radius * 0.46, center.dy - radius * 0.30);

    final metric = checkPath.computeMetrics().first;
    final drawLength = metric.length * progress;
    final animatedCheck = metric.extractPath(0, drawLength);

    final checkPaint = Paint()
      ..color = _navyColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = _strokeWidth
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    canvas.drawPath(animatedCheck, checkPaint);
  }

  @override
  bool shouldRepaint(covariant _CheckPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}
