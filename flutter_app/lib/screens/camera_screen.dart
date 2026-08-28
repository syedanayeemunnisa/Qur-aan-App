import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_config.dart';
import '../models/verse.dart';
import '../providers/quran_provider.dart';
import '../services/camera_service.dart';
import '../utils/permissions.dart';
import '../widgets/camera_overlay.dart';
import '../widgets/translation_panel.dart';
import 'result_screen.dart';

/// Full-screen camera view for scanning Quran pages.
class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen>
    with WidgetsBindingObserver {
  final CameraService _cameraService = CameraService();
  bool _isInitializing = true;
  bool _isCapturing = false;
  bool _hasPermission = false;
  bool _showResult = false;

  // Detected text regions (for overlay)
  final List<TextRegion> _detectedRegions = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cameraService.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _initCamera();
    } else if (state == AppLifecycleState.paused) {
      _cameraService.dispose();
    }
  }

  Future<void> _initCamera() async {
    setState(() => _isInitializing = true);

    // Request permission
    final granted = await AppPermissions.requestCamera();
    if (!granted) {
      if (mounted) {
        AppPermissions.showPermissionDeniedDialog(context);
        setState(() => _isInitializing = false);
      }
      return;
    }

    // Initialize camera
    try {
      await _cameraService.initialize(
        resolution: AppConfig.resolutionPreset,
      );
      setState(() {
        _isInitializing = false;
        _hasPermission = true;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Camera error: $e')),
        );
        setState(() => _isInitializing = false);
      }
    }
  }

  Future<void> _captureAndDetect() async {
    if (_isCapturing) return;
    setState(() => _isCapturing = true);

    try {
      // Capture frame
      final String? base64Image =
          await _cameraService.captureFrameBase64();

      if (base64Image != null && mounted) {
        final provider = context.read<QuranProvider>();
        await provider.detectFromImage(base64Image);

        if (provider.hasVerse && mounted) {
          setState(() => _showResult = true);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Detection error: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isCapturing = false);
    }
  }

  void _dismissResult() {
    setState(() => _showResult = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // ── Camera preview ────────────────────────────────
          if (_hasPermission && _cameraService.isInitialized)
            SizedBox(
              width: double.infinity,
              height: double.infinity,
              child: CameraPreview(_cameraService.controller!),
            )
          else if (_isInitializing)
            const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(color: Colors.white),
                  SizedBox(height: 16),
                  Text(
                    'Initializing camera...',
                    style: TextStyle(color: Colors.white70),
                  ),
                ],
              ),
            )
          else
            const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.no_photography,
                      color: Colors.white54, size: 48),
                  SizedBox(height: 12),
                  Text(
                    'Camera not available',
                    style: TextStyle(color: Colors.white54),
                  ),
                ],
              ),
            ),

          // ── Overlay ───────────────────────────────────────
          if (_hasPermission && _cameraService.isInitialized)
            CameraOverlay(
              detectedRegions: _detectedRegions,
              isDetecting: _isCapturing,
              hasResult: _showResult,
              onCaptureTap: _captureAndDetect,
            ),

          // ── Result panel ─────────────────────────────────
          if (_showResult)
            Consumer<QuranProvider>(
              builder: (context, provider, _) {
                if (!provider.hasVerse) return const SizedBox.shrink();

                return Positioned(
                  left: 0,
                  right: 0,
                  bottom: 0,
                  child: TranslationPanel(
                    verse: provider.currentVerse!,
                    onDismiss: () {
                      _dismissResult();
                      provider.resetDetection();
                    },
                    onBookmark: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Verse bookmarked!'),
                          duration: Duration(seconds: 2),
                        ),
                      );
                    },
                  ),
                );
              },
            ),

          // ── Error snackbar ────────────────────────────────
          if (!_showResult)
            Consumer<QuranProvider>(
              builder: (context, provider, _) {
                if (provider.hasError) {
                  WidgetsBinding.instance.addPostFrameCallback((_) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(provider.errorMessage!),
                        backgroundColor: Colors.red[700],
                        action: SnackBarAction(
                          label: 'Retry',
                          textColor: Colors.white,
                          onPressed: _captureAndDetect,
                        ),
                      ),
                    );
                    provider.resetDetection();
                  });
                }
                return const SizedBox.shrink();
              },
            ),
        ],
      ),
    );
  }
}
