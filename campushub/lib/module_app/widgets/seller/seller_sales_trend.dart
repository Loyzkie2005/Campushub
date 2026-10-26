import 'package:flutter/material.dart';
import '../home/home_preview_cards.dart';
import '../profile/profile_widgets.dart';

/// Displays the existing Django daily sales series; never forecasts or mines.
class SellerSalesTrend extends StatelessWidget {
  const SellerSalesTrend({super.key, required this.trend});
  final Map trend;

  @override
  Widget build(BuildContext context) {
    final labels = trend['labels'];
    final sales = trend['sales'];
    if (labels is! List ||
        sales is! List ||
        labels.length != sales.length ||
        sales.isEmpty ||
        sales.any((value) => value is! num || !value.isFinite || value < 0)) {
      return Text('Sales trend is unavailable.', style: ProfileStyle.text(12));
    }
    final values = sales.cast<num>().map((value) => value.toDouble()).toList();
    final maximum = values.fold<double>(
      0,
      (value, next) => next > value ? next : value,
    );
    return Semantics(
      label:
          'Paid sales. ${List.generate(values.length, (i) => '${labels[i]}: ₱${values[i].toStringAsFixed(2)}').join('. ')}',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('₱${maximum.toStringAsFixed(2)}', style: ProfileStyle.text(12)),
          const SizedBox(height: 8),
          ExcludeSemantics(
            child: SizedBox(
              height: 120,
              child: CustomPaint(painter: _SalesLine(values)),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Text('${labels.first}', style: ProfileStyle.text(12)),
              ),
              if (labels.length > 1)
                Flexible(
                  child: Text(
                    '${labels.last}',
                    textAlign: TextAlign.right,
                    style: ProfileStyle.text(12),
                  ),
                ),
            ],
          ),
          if (maximum == 0) ...[
            const SizedBox(height: 8),
            Text(
              'No completed paid sales in this period.',
              style: ProfileStyle.text(12),
            ),
          ],
        ],
      ),
    );
  }
}

class _SalesLine extends CustomPainter {
  const _SalesLine(this.values);
  final List<double> values;
  @override
  void paint(Canvas canvas, Size size) {
    final maximum = values.fold<double>(
      0,
      (value, next) => next > value ? next : value,
    );
    final ceiling = maximum > 0 ? maximum : 1;
    final baseline = size.height - 4;
    final grid = Paint()
      ..color = HomeAppColors.navy.withValues(alpha: .12)
      ..strokeWidth = 1;
    for (var i = 0; i < 3; i++) {
      final y = 4 + (baseline - 4) * i / 2;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }
    final path = Path();
    for (var i = 0; i < values.length; i++) {
      final x = values.length == 1
          ? size.width / 2
          : size.width * i / (values.length - 1);
      final y = baseline - values[i] / ceiling * (baseline - 4);
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    final ink = Paint()
      ..color = HomeAppColors.navy
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    if (values.length == 1) {
      canvas.drawCircle(
        Offset(
          size.width / 2,
          baseline - values.first / ceiling * (baseline - 4),
        ),
        3,
        ink..style = PaintingStyle.fill,
      );
    } else {
      canvas.drawPath(path, ink);
    }
  }

  @override
  bool shouldRepaint(covariant _SalesLine oldDelegate) =>
      oldDelegate.values != values;
}
