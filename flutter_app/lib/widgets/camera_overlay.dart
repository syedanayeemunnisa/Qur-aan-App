import 'package:flutter/material.dart';
import '../config/app_config.dart';

/// Overlay widget displayed on top of the camera preview.
///
/// Shows:
/// - A scanning frame / viewfinder
/// - Bounding boxes around detected text regions
/// - Detection status indicator
class CameraOverlay extends StatelessWidget {
  final List<TextRegion> detectedRegions;
  final bool isDetecting;
  final bool hasResult;
  final VoidCallback? onCaptureTap;

  const CameraOverlay({
    super.key,
    this.detectedRegions = const [],
    this.isDetecting = false,
    this.hasResult = false,
    this.onCaptureTap,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // ── Scanning frame ──────────────────────────────────
        Positioned.fill(
          child: CustomPaint(
            painter: _ScanFramePainter(
              detectedRegions: detectedRegions,
              isDetecting: isDetecting,
              hasResult: hasResult,
            ),
          ),
        ),

        // ── Corner brackets ────────────────────────────────
        Positioned.fill(
          child: IgnorePointer(
            child: Padding(
              padding: const EdgeInsets.all(40),
              child: CustomPaint(
                painter: _CornerBracketPainter(),
              ),
            ),
          ),
        ),

        // ── Top bar ─────────────────────────────────────────
        Positioned(
          top: MediaQuery.of(context).padding.top + 8,
          left: 0,
          right: 0,
          child: SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  // Back button
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.black38,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: IconButton(
                      icon: const Icon(Icons.arrow_back,
                          color: Colors.white),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ),
                  const Spacer(),
                  // Status indicator
                  if (isDetecting)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.black38,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: AppConfig.accentColor,
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'Scanning...',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  if (hasResult)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: AppConfig.successColor.withValues(alpha: 0.8),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.check_circle,
                              color: Colors.white, size: 16),
                          SizedBox(width: 6),
                          Text(
                            'Verse Found',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),

        // ── Bottom hint ─────────────────────────────────────
        Positioned(
          bottom: MediaQuery.of(context).padding.bottom + 120,
          left: 0,
          right: 0,
          child: Center(
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 8,
              ),
              decoration: BoxDecoration(
                color: Colors.black45,
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Text(
                'Align Quran page in the frame',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ),
        ),

        // ── Capture button ──────────────────────────────────
        Positioned(
          bottom: MediaQuery.of(context).padding.bottom + 40,
          left: 0,
          right: 0,
          child: Center(
            child: GestureDetector(
              onTap: onCaptureTap,
              child: Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white,
                    width: 4,
                  ),
                  color: Colors.white24,
                ),
                child: Container(
                  margin: const EdgeInsets.all(6),
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ),

        // ── Gallery button ──────────────────────────────────
        Positioned(
          bottom: MediaQuery.of(context).padding.bottom + 50,
          right: 32,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.black38,
              borderRadius: BorderRadius.circular(12),
            ),
            child: IconButton(
              icon: const Icon(Icons.photo_library_outlined,
                  color: Colors.white, size: 28),
              onPressed: () {
                // Gallery pick — handled by parent
              },
            ),
          ),
        ),

        // ── Flash toggle ────────────────────────────────────
        Positioned(
          bottom: MediaQuery.of(context).padding.bottom + 50,
          left: 32,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.black38,
              borderRadius: BorderRadius.circular(12),
            ),
            child: IconButton(
              icon: const Icon(Icons.flash_on,
                  color: Colors.white, size: 28),
              onPressed: () {
                // Flash toggle — handled by parent
              },
            ),
          ),
        ),
      ],
    );
  }
}

/// Data class for a detected text region on the camera preview.
class TextRegion {
  final double x, y, width, height;
  final String text;
  final double confidence;

  const TextRegion({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.text,
    this.confidence = 1.0,
  });
}

/// Paints the scanning frame and bounding boxes.
class _ScanFramePainter extends CustomPainter {
  final List<TextRegion> detectedRegions;
  final bool isDetecting;
  final bool hasResult;

  _ScanFramePainter({
    this.detectedRegions = const [],
    this.isDetecting = false,
    this.hasResult = false,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // ── Detect regions ──
    final boxPaint = Paint()
      ..color = AppConfig.accentColor.withValues(alpha: 0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final fillPaint = Paint()
      ..color = AppConfig.accentColor.withValues(alpha: 0.1)
      ..style = PaintingStyle.fill;

    for (final region in detectedRegions) {
      final rect = Rect.fromLTWH(
        region.x * size.width,
        region.y * size.height,
        region.width * size.width,
        region.height * size.height,
      );
      canvas.drawRect(rect, fillPaint);
      canvas.drawRect(rect, boxPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _ScanFramePainter oldDelegate) {
    return oldDelegate.detectedRegions != detectedRegions ||
        oldDelegate.isDetecting != isDetecting ||
        oldDelegate.hasResult != hasResult;
  }
}

/// Paints corner brackets for the scanning area.
class _CornerBracketPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppConfig.accentColor.withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round;

    const bracketLength = 30.0;

    // Top-left
    canvas.drawLine(
        const Offset(0, bracketLength), const Offset(0, 0), paint);
    canvas.drawLine(
        const Offset(0, 0), const Offset(bracketLength, 0), paint);

    // Top-right
    canvas.drawLine(
        Offset(size.width - bracketLength, 0), Offset(size.width, 0), paint);
    canvas.drawLine(
        Offset(size.width, 0), Offset(size.width, bracketLength), paint);

    // Bottom-left
    canvas.drawLine(
        const Offset(0, size.height - bracketLength),
        const Offset(0, size.height),
        paint);
    canvas.drawLine(
        const Offset(0, size.height),
        const Offset(bracketLength, size.height),
        paint);

    // Bottom-right
    canvas.drawLine(
        Offset(size.width - bracketLength, size.height),
        Offset(size.width, size.height),
        paint);
    canvas.drawLine(
        Offset(size.width, size.height - bracketLength),
        Offset(size.width, size.height),
        paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
