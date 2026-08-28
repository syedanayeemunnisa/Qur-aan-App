import 'package:flutter/material.dart';
import '../config/app_config.dart';
import '../models/verse.dart';

/// A compact card displaying a verse reference, Arabic text, and translation.
class VerseCard extends StatelessWidget {
  final Verse verse;
  final bool showFullArabic;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;

  const VerseCard({
    super.key,
    required this.verse,
    this.showFullArabic = false,
    this.onTap,
    this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        onLongPress: onLongPress,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Header: Reference ────────────────────────────
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 3,
                    ),
                    decoration: BoxDecoration(
                      color: AppConfig.primaryColor.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      verse.reference,
                      style: TextStyle(
                        fontSize: 12,
                        color: AppConfig.primaryColor,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const Spacer(),
                  if (verse.confidence < 1.0)
                    Text(
                      '${(verse.confidence * 100).toInt()}%',
                      style: TextStyle(
                        fontSize: 11,
                        color: AppConfig.textSecondary,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),

              // ── Arabic text ─────────────────────────────────
              Directionality(
                textDirection: TextDirection.rtl,
                child: Text(
                  verse.arabic,
                  textAlign: TextAlign.center,
                  maxLines: showFullArabic ? null : 2,
                  overflow: showFullArabic
                      ? TextOverflow.visible
                      : TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w500,
                    height: 1.6,
                    color: AppConfig.textPrimary,
                  ),
                ),
              ),
              const SizedBox(height: 8),

              // ── Roman transliteration ───────────────────────
              if (verse.hasRoman)
                Text(
                  verse.roman!,
                  style: TextStyle(
                    fontSize: 13,
                    fontStyle: FontStyle.italic,
                    color: AppConfig.textSecondary.withValues(alpha: 0.7),
                  ),
                ),
              if (verse.hasRoman) const SizedBox(height: 6),

              // ── Translation ─────────────────────────────────
              Text(
                verse.translation,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 14,
                  color: AppConfig.textPrimary.withValues(alpha: 0.85),
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A shimmer placeholder for when verses are loading.
class VerseCardShimmer extends StatelessWidget {
  const VerseCardShimmer({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Reference shimmer
            Container(
              width: 80,
              height: 22,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            const SizedBox(height: 12),

            // Arabic shimmer
            Container(
              width: double.infinity,
              height: 32,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            const SizedBox(height: 12),

            // Translation shimmer
            Container(
              width: double.infinity,
              height: 20,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(6),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
