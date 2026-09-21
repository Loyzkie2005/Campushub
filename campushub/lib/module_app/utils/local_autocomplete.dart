/// Client-side autocomplete / autosuggest — no API required.
///
/// Ranking (best → weakest):
/// 1. Exact match
/// 2. Prefix match (starts with query)
/// 3. Token / word match
/// 4. Contains (substring)
/// 5. Fuzzy (Levenshtein) for short typos
class LocalAutocomplete {
  LocalAutocomplete._();

  /// Rank [items] by how well [textOf] matches [query].
  /// Returns up to [limit] items. Empty query returns the first [limit] items.
  static List<T> suggest<T>({
    required List<T> items,
    required String query,
    required String Function(T item) textOf,
    Iterable<String> Function(T item)? extraTexts,
    int limit = 8,
  }) {
    final q = query.trim().toLowerCase();
    if (items.isEmpty) return const [];
    if (q.isEmpty) return items.take(limit).toList(growable: false);

    final scored = <_Scored<T>>[];
    for (final item in items) {
      final primary = textOf(item).trim().toLowerCase();
      final extras = extraTexts == null
          ? const <String>[]
          : extraTexts(item)
                .map((e) => e.trim().toLowerCase())
                .where((e) => e.isNotEmpty)
                .toList(growable: false);

      var best = _scoreText(primary, q);
      for (final extra in extras) {
        final s = _scoreText(extra, q);
        if (s > best) best = s;
      }
      if (best > 0) {
        scored.add(_Scored(item, best, primary));
      }
    }

    scored.sort((a, b) {
      final byScore = b.score.compareTo(a.score);
      if (byScore != 0) return byScore;
      return a.sortKey.compareTo(b.sortKey);
    });

    return scored.take(limit).map((e) => e.item).toList(growable: false);
  }

  /// True if [text] matches [query] with prefix / contains / fuzzy.
  static bool matches(String text, String query) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return true;
    return _scoreText(text.trim().toLowerCase(), q) > 0;
  }

  static int _scoreText(String text, String query) {
    if (text.isEmpty || query.isEmpty) return 0;
    if (text == query) return 1000;
    if (text.startsWith(query)) return 800 + (query.length * 2);

    final tokens =
        text.split(RegExp(r'[\s\-_/.,]+')).where((t) => t.isNotEmpty);
    for (final token in tokens) {
      if (token == query) return 700;
      if (token.startsWith(query)) return 650 + query.length;
    }

    if (text.contains(query)) return 400 + query.length;

    // Fuzzy only for short queries to keep typing snappy.
    if (query.length >= 2 && query.length <= 12) {
      for (final token in tokens) {
        if ((token.length - query.length).abs() > 2) continue;
        final d = _levenshtein(token, query, maxDistance: 2);
        if (d == 1) return 280;
        if (d == 2) return 180;
      }
      if (text.length <= 16) {
        final d = _levenshtein(text, query, maxDistance: 2);
        if (d == 1) return 250;
        if (d == 2) return 150;
      }
    }

    return 0;
  }

  /// Early-exit Levenshtein; returns > [maxDistance] if too far.
  static int _levenshtein(String a, String b, {int maxDistance = 2}) {
    if (a == b) return 0;
    if (a.isEmpty) return b.length;
    if (b.isEmpty) return a.length;
    if ((a.length - b.length).abs() > maxDistance) return maxDistance + 1;

    final prev = List<int>.generate(b.length + 1, (i) => i);
    final curr = List<int>.filled(b.length + 1, 0);

    for (var i = 1; i <= a.length; i++) {
      curr[0] = i;
      var rowMin = curr[0];
      final ca = a.codeUnitAt(i - 1);
      for (var j = 1; j <= b.length; j++) {
        final cost = ca == b.codeUnitAt(j - 1) ? 0 : 1;
        final del = prev[j] + 1;
        final ins = curr[j - 1] + 1;
        final sub = prev[j - 1] + cost;
        var v = del < ins ? del : ins;
        if (sub < v) v = sub;
        curr[j] = v;
        if (v < rowMin) rowMin = v;
      }
      if (rowMin > maxDistance) return maxDistance + 1;
      for (var j = 0; j <= b.length; j++) {
        prev[j] = curr[j];
      }
    }
    return prev[b.length];
  }
}

class _Scored<T> {
  const _Scored(this.item, this.score, this.sortKey);
  final T item;
  final int score;
  final String sortKey;
}
