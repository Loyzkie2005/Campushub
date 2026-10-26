package com.ustp.campushub

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "campushub/notification_settings")
            .setMethodCallHandler { call, result ->
                if (call.method != "open") {
                    result.notImplemented()
                    return@setMethodCallHandler
                }
                try {
                    startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).apply {
                        putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
                    })
                    result.success(true)
                } catch (_: ActivityNotFoundException) {
                    try {
                        startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                            data = Uri.parse("package:$packageName")
                        })
                        result.success(true)
                    } catch (_: ActivityNotFoundException) {
                        result.success(false)
                    } catch (_: SecurityException) {
                        result.success(false)
                    }
                } catch (_: SecurityException) {
                    result.success(false)
                }
            }
    }
}
