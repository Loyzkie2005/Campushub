import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class FavoriteService extends ChangeNotifier {
  FavoriteService._();

  static final FavoriteService instance = FavoriteService._();
  static const _storageKey = 'campushub_favorite_products';

  final Set<String> _favoriteKeys = <String>{};
  bool _loaded = false;

  bool get loaded => _loaded;

  Future<void> load() async {
    if (_loaded) return;
    final preferences = await SharedPreferences.getInstance();
    _favoriteKeys
      ..clear()
      ..addAll(preferences.getStringList(_storageKey) ?? const <String>[]);
    _loaded = true;
    notifyListeners();
  }

  bool isFavorite(String key) => _favoriteKeys.contains(key);

  Future<void> toggle(String key) async {
    if (isFavorite(key)) {
      _favoriteKeys.remove(key);
    } else {
      _favoriteKeys.add(key);
    }
    notifyListeners();
    final preferences = await SharedPreferences.getInstance();
    await preferences.setStringList(_storageKey, _favoriteKeys.toList());
  }
}

String favoriteKeyForProduct({int? id, required String name}) {
  return id == null ? 'name:$name' : 'id:$id';
}
