import 'dart:io';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

/// Utility class for handling app permissions.
class AppPermissions {
  // ── Camera Permission ────────────────────────────────────────

  /// Request camera permission and return the result.
  static Future<bool> requestCamera() async {
    // On Android 13+, use restricted camera permission
    if (Platform.isAndroid) {
      final status = await Permission.camera.request();
      return status.isGranted;
    }

    // iOS
    final status = await Permission.camera.request();
    return status.isGranted;
  }

  /// Check if camera permission is granted without prompting.
  static Future<bool> hasCamera() async {
    return await Permission.camera.isGranted;
  }

  // ── Storage Permission (for gallery access) ──────────────────

  /// Request storage / photos permission.
  static Future<bool> requestStorage() async {
    if (Platform.isAndroid) {
      // Android 13+ uses granular media permissions
      if (await Permission.photos.status.isGranted) {
        return true;
      }
      final status = await Permission.photos.request();
      return status.isGranted;
    }

    // iOS
    final status = await Permission.photos.request();
    return status.isGranted;
  }

  // ── UI Helper ────────────────────────────────────────────────

  /// Show a dialog if permission is permanently denied.
  static Future<void> showPermissionDeniedDialog(
    BuildContext context, {
    String title = 'Permission Required',
    String message = 'Camera permission is needed to scan Quran pages.',
  }) async {
    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              openAppSettings();
            },
            child: const Text('Open Settings'),
          ),
        ],
      ),
    );
  }
}
