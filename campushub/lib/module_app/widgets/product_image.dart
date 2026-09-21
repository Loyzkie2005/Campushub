import 'dart:convert';

import 'package:flutter/material.dart';

import '../config/api_config.dart';

/// Displays a product image from API URL, base64, or /media path.
class ProductImage extends StatelessWidget {
  const ProductImage({
    super.key,
    required this.imageUrl,
    this.fallbackIcon = Icons.lunch_dining_outlined,
    this.fallbackColor = const Color(0xFF94A3B8),
    this.backgroundColor,
    this.fit = BoxFit.cover,
  });

  final String imageUrl;
  final IconData fallbackIcon;
  final Color fallbackColor;
  final Color? backgroundColor;
  final BoxFit fit;

  static String resolveUrl(String raw) {
    final url = raw.trim();
    if (url.isEmpty) return '';

    if (url.startsWith('data:image/')) {
      return url;
    }

    final base = ApiConfig.effectiveBaseUrl;

    if (url.startsWith('/')) {
      return '$base$url';
    }

    if (url.startsWith('media/')) {
      return '$base/$url';
    }

    final uri = Uri.tryParse(url);
    if (uri == null) return url;

    if (uri.scheme != 'http' && uri.scheme != 'https') {
      return url;
    }

    const localHosts = {'127.0.0.1', 'localhost', '10.0.2.2'};
    if (localHosts.contains(uri.host.toLowerCase())) {
      final path = uri.hasEmptyPath ? '' : uri.path;
      final query = uri.hasQuery ? '?${uri.query}' : '';
      return '$base$path$query';
    }

    return url;
  }

  @override
  Widget build(BuildContext context) {
    final resolved = resolveUrl(imageUrl);

    return ColoredBox(
      // Keep background transparent so images have no tint.
      color: backgroundColor ?? Colors.transparent,
      child: resolved.isEmpty
          ? Center(child: _fallback())
          : _buildImage(resolved),
    );
  }

  Widget _fallback() => Icon(fallbackIcon, color: fallbackColor, size: 40);

  Widget _buildImage(String resolved) {
    if (resolved.startsWith('data:image/')) {
      final commaIndex = resolved.indexOf(',');
      if (commaIndex == -1) {
        return Center(child: _fallback());
      }
      try {
        final bytes = base64Decode(resolved.substring(commaIndex + 1));
        return Image.memory(
          bytes,
          key: ValueKey(resolved.hashCode),
          fit: fit,
          width: double.infinity,
          height: double.infinity,
          gaplessPlayback: true,
          errorBuilder: (_, _, _) => Center(child: _fallback()),
        );
      } catch (_) {
        return Center(child: _fallback());
      }
    }

    return Image.network(
      resolved,
      key: ValueKey(resolved),
      fit: fit,
      width: double.infinity,
      height: double.infinity,
      gaplessPlayback: true,
      filterQuality: FilterQuality.medium,
      loadingBuilder: (context, child, progress) {
        if (progress == null) return child;
        return Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              value: progress.expectedTotalBytes != null
                  ? progress.cumulativeBytesLoaded /
                      progress.expectedTotalBytes!
                  : null,
            ),
          ),
        );
      },
      errorBuilder: (_, _, _) => Center(child: _fallback()),
    );
  }
}
