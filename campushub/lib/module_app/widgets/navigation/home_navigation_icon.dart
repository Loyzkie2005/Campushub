import 'package:flutter/material.dart';

/// The supplied 24x24 Home SVG paths, tinted by navigation's IconTheme.
class HomeNavigationIcon extends StatelessWidget {
  const HomeNavigationIcon({super.key, this.outlined = false});

  final bool outlined;

  @override
  Widget build(BuildContext context) {
    final theme = IconTheme.of(context);
    return SizedBox.square(
      dimension: theme.size ?? 24,
      child: CustomPaint(
        painter: _HomePainter(theme.color ?? const Color(0xFF1A1851), outlined),
      ),
    );
  }
}

class _HomePainter extends CustomPainter {
  const _HomePainter(this.color, this.outlined);

  final Color color;
  final bool outlined;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 24, size.height / 24);
    canvas.clipRect(const Rect.fromLTWH(0, 0, 24, 24));
    canvas.drawPath(
      outlined ? _outlinePath() : _filledPath(),
      Paint()..color = color,
    );
    canvas.restore();
  }

  Path _filledPath() => Path()
    ..fillType = PathFillType.evenOdd
    ..moveTo(20.04, 6.81969)
    ..lineTo(14.28, 2.78969)
    ..cubicTo(12.71, 1.68969, 10.3, 1.74969, 8.78999, 2.91969)
    ..lineTo(3.77999, 6.82969)
    ..cubicTo(2.77999, 7.60969, 1.98999, 9.20969, 1.98999, 10.4697)
    ..lineTo(1.98999, 17.3697)
    ..cubicTo(1.98999, 19.9197, 4.05999, 21.9997, 6.60999, 21.9997)
    ..lineTo(17.39, 21.9997)
    ..cubicTo(19.94, 21.9997, 22.01, 19.9297, 22.01, 17.3797)
    ..lineTo(22.01, 10.5997)
    ..cubicTo(22.01, 9.24969, 21.14, 7.58969, 20.04, 6.81969)
    ..close()
    ..moveTo(12.75, 17.9997)
    ..cubicTo(12.75, 18.4097, 12.41, 18.7497, 12, 18.7497)
    ..cubicTo(11.59, 18.7497, 11.25, 18.4097, 11.25, 17.9997)
    ..lineTo(11.25, 14.9997)
    ..cubicTo(11.25, 14.5897, 11.59, 14.2497, 12, 14.2497)
    ..cubicTo(12.41, 14.2497, 12.75, 14.5897, 12.75, 14.9997)
    ..lineTo(12.75, 17.9997)
    ..close();

  Path _outlinePath() => Path()
    ..fillType = PathFillType.evenOdd
    ..moveTo(17.79, 22.75)
    ..lineTo(6.21, 22.75)
    ..cubicTo(3.47, 22.75, 1.25, 20.52, 1.25, 17.78)
    ..lineTo(1.25, 10.37)
    ..cubicTo(1.25, 9.00997, 2.09, 7.29997, 3.17, 6.45997)
    ..lineTo(8.56, 2.25997)
    ..cubicTo(10.18, 0.999974, 12.77, 0.939974, 14.45, 2.11997)
    ..lineTo(20.63, 6.44997)
    ..cubicTo(21.82, 7.27997, 22.75, 9.05997, 22.75, 10.51)
    ..lineTo(22.75, 17.79)
    ..cubicTo(22.75, 20.52, 20.53, 22.75, 17.79, 22.75)
    ..close()
    ..moveTo(9.48, 3.43997)
    ..lineTo(4.09, 7.63997)
    ..cubicTo(3.38, 8.19997, 2.75, 9.46997, 2.75, 10.37)
    ..lineTo(2.75, 17.78)
    ..cubicTo(2.75, 19.69, 4.3, 21.25, 6.21, 21.25)
    ..lineTo(17.79, 21.25)
    ..cubicTo(19.7, 21.25, 21.25, 19.7, 21.25, 17.79)
    ..lineTo(21.25, 10.51)
    ..cubicTo(21.25, 9.54997, 20.56, 8.21997, 19.77, 7.67997)
    ..lineTo(13.59, 3.34997)
    ..cubicTo(12.45, 2.54997, 10.57, 2.58997, 9.48, 3.43997)
    ..close()
    ..moveTo(12, 18.75)
    ..cubicTo(11.59, 18.75, 11.25, 18.41, 11.25, 18)
    ..lineTo(11.25, 15)
    ..cubicTo(11.25, 14.59, 11.59, 14.25, 12, 14.25)
    ..cubicTo(12.41, 14.25, 12.75, 14.59, 12.75, 15)
    ..lineTo(12.75, 18)
    ..cubicTo(12.75, 18.41, 12.41, 18.75, 12, 18.75)
    ..close();

  @override
  bool shouldRepaint(covariant _HomePainter oldDelegate) =>
      color != oldDelegate.color || outlined != oldDelegate.outlined;
}
