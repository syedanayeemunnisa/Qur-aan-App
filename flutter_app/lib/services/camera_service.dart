import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

/// Service for managing the camera and capturing frames.
class CameraService {
  CameraController? _controller;
  bool _isInitialized = false;
  String? _preferredCameraLens;

  // ── Properties ────────────────────────────────────────────────

  CameraController? get controller => _controller;
  bool get isInitialized => _isInitialized;

  /// The current camera value (preview image).
  CameraImage? get currentImage => null; // Accessed via controller

  // ── Initialization ────────────────────────────────────────────

  /// Initialize the camera with the first available back camera.
  Future<void> initialize({
    ResolutionPreset resolution = ResolutionPreset.medium,
    String? cameraLens,
  }) async {
    try {
      final cameras = await availableCameras();

      if (cameras.isEmpty) {
        throw Exception('No cameras available');
      }

      // Prefer back camera
      CameraDescription selectedCamera;
      if (cameraLens != null) {
        selectedCamera = cameras.firstWhere(
          (c) => c.name == cameraLens,
          orElse: () => cameras.firstWhere(
            (c) => c.lensDirection == CameraLensDirection.back,
            orElse: () => cameras.first,
          ),
        );
      } else {
        selectedCamera = cameras.firstWhere(
          (c) => c.lensDirection == CameraLensDirection.back,
          orElse: () => cameras.first,
        );
      }

      _preferredCameraLens = selectedCamera.name;

      _controller = CameraController(
        selectedCamera,
        resolution,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await _controller!.initialize();
      _isInitialized = true;
    } catch (e) {
      _isInitialized = false;
      rethrow;
    }
  }

  // ── Frame Capture ─────────────────────────────────────────────

  /// Capture a single frame as JPEG bytes.
  Future<Uint8List?> captureFrame() async {
    if (!_isInitialized || _controller == null) return null;

    try {
      final XFile file = await _controller!.takePicture();
      return await file.readAsBytes();
    } catch (e) {
      debugPrint('Error capturing frame: $e');
      return null;
    }
  }

  /// Capture frame and return as base64 string (for API).
  Future<String?> captureFrameBase64() async {
    final bytes = await captureFrame();
    if (bytes == null) return null;
    return base64Encode(bytes);
  }

  // ── Image Selection (Gallery) ────────────────────────────────

  /// Pick an image from the gallery for OCR.
  Future<Uint8List?> pickFromGallery() async {
    try {
      final picker = ImagePicker();
      final XFile? image = await picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1080,
      );
      if (image == null) return null;
      return await image.readAsBytes();
    } catch (e) {
      debugPrint('Error picking image: $e');
      return null;
    }
  }

  // ── Camera Control ────────────────────────────────────────────

  /// Start the image stream (for real-time processing).
  Future<void> startImageStream({
    required void Function(CameraImage image) onImage,
  }) async {
    if (!_isInitialized || _controller == null) return;

    try {
      await _controller!.startImageStream(onImage);
    } catch (e) {
      debugPrint('Error starting image stream: $e');
    }
  }

  /// Stop the image stream.
  Future<void> stopImageStream() async {
    if (_controller == null || !_controller!.value.isStreamingImages) return;

    try {
      await _controller!.stopImageStream();
    } catch (e) {
      debugPrint('Error stopping image stream: $e');
    }
  }

  /// Switch between front and back camera.
  Future<void> switchCamera() async {
    if (_controller == null) return;

    final cameras = await availableCameras();
    final currentLens = _controller!.description.lensDirection;

    CameraDescription newCamera;
    if (currentLens == CameraLensDirection.back) {
      newCamera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );
    } else {
      newCamera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
    }

    final oldResolution = _controller!.resolutionPreset;
    await _controller!.dispose();

    _controller = CameraController(newCamera, oldResolution);
    await _controller!.initialize();
    _isInitialized = true;
  }

  // ── Lifecycle ─────────────────────────────────────────────────

  /// Dispose of the camera controller.
  Future<void> dispose() async {
    _isInitialized = false;
    await _controller?.dispose();
    _controller = null;
  }

  /// Pause the camera (e.g., when app goes to background).
  Future<void> pause() async {
    if (_controller != null && _controller!.value.isRecordingVideo) {
      await _controller!.pauseVideoRecording();
    }
  }

  /// Resume the camera.
  Future<void> resume() async {
    if (_controller != null && _controller!.value.isRecordingVideo) {
      await _controller!.resumeVideoRecording();
    }
  }
}
