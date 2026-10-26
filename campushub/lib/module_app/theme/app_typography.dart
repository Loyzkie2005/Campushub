import 'package:flutter/material.dart';

/// Bundled UI fonts: no network request or Google Fonts cache is required.
abstract final class AppTypography {
  static const family = 'Poppins';

  static TextStyle text({
    Color? color,
    double? fontSize,
    FontWeight? fontWeight,
    double? height,
    double? letterSpacing,
  }) => TextStyle(
    fontFamily: family,
    color: color,
    fontSize: fontSize,
    fontWeight: fontWeight,
    height: height,
    letterSpacing: letterSpacing,
  );

  static TextTheme textTheme(TextTheme base) => base.apply(fontFamily: family);
}
