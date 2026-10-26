import 'package:flutter/material.dart';

/// The supplied 24x24, 1.5-unit rounded-stroke plus SVG.
class AddProductNavigationIcon extends StatelessWidget {
  const AddProductNavigationIcon({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = IconTheme.of(context);
    return SizedBox.square(
      dimension: theme.size ?? 24,
      child: CustomPaint(
        painter: _AddProductPainter(theme.color ?? const Color(0xFF1A1851)),
      ),
    );
  }
}

class _AddProductPainter extends CustomPainter {
  const _AddProductPainter(this.color);

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 24, size.height / 24);
    canvas.clipRect(const Rect.fromLTWH(0, 0, 24, 24));
    final horizontal = Path()
      ..moveTo(6, 12)
      ..lineTo(18, 12);
    final vertical = Path()
      ..moveTo(12, 18)
      ..lineTo(12, 6);
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(horizontal, paint);
    canvas.drawPath(vertical, paint);
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _AddProductPainter oldDelegate) =>
      color != oldDelegate.color;
}
