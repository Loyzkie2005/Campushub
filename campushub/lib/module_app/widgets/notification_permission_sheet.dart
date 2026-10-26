import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

import '../services/push_notification_service.dart';

/// Existing bell panel: real permission/registration status, not a fake inbox.
class NotificationPermissionSheet extends StatefulWidget {
  const NotificationPermissionSheet({super.key, this.service});
  final PushNotificationService? service;

  @override
  State<NotificationPermissionSheet> createState() =>
      _NotificationPermissionSheetState();
}

class _NotificationPermissionSheetState
    extends State<NotificationPermissionSheet> {
  static const navy = Color(0xFF1A1851);
  bool _busy = false;
  bool _settingsFailed = false;
  PushNotificationService get _service =>
      widget.service ?? PushNotificationService.instance;
  bool get _permanentlyDenied =>
      _service.authorizationStatus == AuthorizationStatus.deniedPermanently;

  String get _message {
    if (!_service.isSupported) {
      return 'Push notifications are available in the Android app.';
    }
    if (!_service.hasSession) {
      return 'Sign in to enable notifications on this device.';
    }
    if (_service.isRegistered) {
      return 'Notifications are enabled on this device.';
    }
    if (_settingsFailed) {
      return 'Open Phone Settings → Apps → CampusHub → Notifications and allow notifications.';
    }
    if (_permanentlyDenied) {
      return 'Android will not show another permission prompt. Open notification settings and allow CampusHub notifications, then return to the app.';
    }
    if (_service.lastError != null) {
      return _service.lastError!;
    }
    if (_service.authorizationStatus == AuthorizationStatus.denied) {
      return 'Notifications are turned off. Tap Enable notifications. If Android does not show a prompt, open Phone Settings → Apps → CampusHub → Notifications and turn them on.';
    }
    if (_service.authorizationStatus == AuthorizationStatus.authorized ||
        _service.authorizationStatus == AuthorizationStatus.provisional) {
      return 'Notification permission is already allowed. Tap Retry connection to register this device.';
    }
    return 'Allow CampusHub to notify you when your products are approved.';
  }

  Future<void> _enable() async {
    setState(() => _busy = true);
    try {
      await _service.requestPermissionFromUser();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openSettings() async {
    setState(() {
      _busy = true;
      _settingsFailed = false;
    });
    final opened = await _service.openNotificationSettings();
    if (mounted) {
      setState(() {
        _busy = false;
        _settingsFailed = !opened;
      });
    }
  }

  @override
  Widget build(BuildContext context) => SafeArea(
    child: SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: ValueListenableBuilder<int>(
        valueListenable: _service.stateChanges,
        builder: (context, _, child) => Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Notifications',
              style: TextStyle(
                color: navy,
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _message,
              style: const TextStyle(color: navy, fontSize: 14, height: 1.5),
            ),
            const SizedBox(height: 20),
            if (!_service.isRegistered)
              FilledButton(
                onPressed:
                    _busy || !_service.hasSession || !_service.isSupported
                    ? null
                    : _permanentlyDenied
                    ? _openSettings
                    : _enable,
                style: FilledButton.styleFrom(
                  backgroundColor: navy,
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(48),
                ),
                child: Text(
                  _busy
                      ? 'Connecting…'
                      : _permanentlyDenied
                      ? 'Open notification settings'
                      : _service.authorizationStatus ==
                                AuthorizationStatus.authorized ||
                            _service.authorizationStatus ==
                                AuthorizationStatus.provisional
                      ? 'Retry connection'
                      : 'Enable notifications',
                ),
              ),
            if (!_service.isRegistered &&
                !_permanentlyDenied &&
                _service.isSupported &&
                _service.hasSession)
              TextButton(
                onPressed: _busy ? null : _openSettings,
                style: TextButton.styleFrom(foregroundColor: navy),
                child: const Text('Open notification settings'),
              ),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                style: TextButton.styleFrom(foregroundColor: navy),
                child: const Text('Close'),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
