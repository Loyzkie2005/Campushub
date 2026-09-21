import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeService extends ChangeNotifier {
  ThemeService._();

  static final ThemeService instance = ThemeService._();
  static const _preferenceKey = 'campushub_light_theme';

  bool _isLightMode = false;

  bool get isLightMode => _isLightMode;
  ThemeMode get themeMode => _isLightMode ? ThemeMode.light : ThemeMode.dark;

  Future<void> load() async {
    final preferences = await SharedPreferences.getInstance();
    _isLightMode = preferences.getBool(_preferenceKey) ?? false;
  }

  Future<void> setLightMode(bool value) async {
    if (_isLightMode == value) return;
    _isLightMode = value;
    notifyListeners();

    final preferences = await SharedPreferences.getInstance();
    await preferences.setBool(_preferenceKey, value);
  }
}
