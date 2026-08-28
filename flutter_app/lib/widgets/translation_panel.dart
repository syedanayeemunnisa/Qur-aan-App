import 'package:flutter/material.dart';
import '../config/app_config.dart';
import '../models/verse.dart';

/// Bottom panel displaying the detected verse with Arabic, translation,
/// and Roman transliteration.
class TranslationPanel extends StatelessWidget {
  final Verse verse;
  final VoidCallback? onDismiss;
  final VoidCallback? onBookmark;
  final bool isBookmarked;

  const TranslationPanel({
    super.key,
    required this.verse,
    this.onDismiss,
    this.onBookmark,
    this.isBookmarked = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppConfig.cardColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.15),
            blurRadius: 20,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Handle ─────────────────────────────────────
            Center(
              child: Container(
                margin: const EdgeInsets.only(top: 10),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppConfig.borderColor,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            // ── Header: Reference + Actions ────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 14, 12, 4),
              child: Row(
                children: [
                  // Surah and Ayah reference
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppConfig.primaryColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      'Surah ${verse.surah}:${verse.ayah}',
                      style: TextStyle(
                        color: AppConfig.primaryColor,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Confidence badge
                  if (verse.confidence < 1.0)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: verse.confidence > 0.7
                            ? AppConfig.successColor.withValues(alpha: 0.1)
                            : Colors.orange.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Text(
                        '${(verse.confidence * 100).toInt()}% match',
                        style: TextStyle(
                          color: verse.confidence > 0.7
                              ? AppConfig.successColor
                              : Colors.orange,
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),

                  const Spacer(),

                  // Bookmark button
                  IconButton(
                    icon: Icon(
                      isBookmarked
                          ? Icons.bookmark
                          : Icons.bookmark_border,
                      color: isBookmarked
                          ? AppConfig.accentColor
                          : AppConfig.textSecondary,
                      size: 22,
                    ),
                    onPressed: onBookmark,
                    tooltip: 'Bookmark',
                  ),

                  // Dismiss button
                  IconButton(
                    icon: const Icon(
                      Icons.keyboard_arrow_down,
                      color: AppConfig.textSecondary,
                      size: 24,
                    ),
                    onPressed: onDismiss,
                    tooltip: 'Close',
                  ),
                ],
              ),
            ),

            // ── Arabic text ────────────────────────────────
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppConfig.primaryColor.withValues(alpha: 0.04),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: AppConfig.primaryColor.withValues(alpha: 0.1),
                ),
              ),
              child: Directionality(
                textDirection: TextDirection.rtl,
                child: Text(
                  verse.arabic,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.w600,
                    height: 1.8,
                    color: AppConfig.textPrimary,
                    fontFamily: 'Scheherazade', // Quranic font
                  ),
                ),
              ),
            ),

            // ── Transliteration (only if not already the selected translation) ──
            if (verse.hasRoman && verse.translationLanguage != 'roman')
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Text(
                  verse.roman!,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 15,
                    fontStyle: FontStyle.italic,
                    color: AppConfig.textSecondary.withValues(alpha: 0.8),
                    height: 1.5,
                    letterSpacing: 0.3,
                  ),
                ),
              ),

            // ── Translation ─────────────────────────────────
            Container(
              margin: const EdgeInsets.fromLTRB(20, 10, 20, 16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppConfig.accentColor.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppConfig.accentColor.withValues(alpha: 0.15),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Language label
                  Row(
                    children: [
                      Icon(
                        Icons.translate,
                        size: 14,
                        color: AppConfig.accentColor,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        AppConfig.supportedLanguages[
                                verse.translationLanguage] ??
                            verse.translationLanguage,
                        style: TextStyle(
                          fontSize: 11,
                          color: AppConfig.accentColor,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    verse.translation,
                    style: TextStyle(
                      fontSize: 16,
                      color: AppConfig.textPrimary.withValues(alpha: 0.9),
                      height: 1.6,
                      letterSpacing: 0.2,
                    ),
                  ),
                ],
              ),
            ),

            // ── Quick action buttons ────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
              child: Row(
                children: [
                  _ActionChip(
                    icon: Icons.volume_up_outlined,
                    label: 'Recite',
                    onTap: () {},
                  ),
                  const SizedBox(width: 8),
                  _ActionChip(
                    icon: Icons.menu_book_outlined,
                    label: 'Tafsir',
                    onTap: () {},
                  ),
                  const SizedBox(width: 8),
                  _ActionChip(
                    icon: Icons.share_outlined,
                    label: 'Share',
                    onTap: () {},
                  ),
                ],
              ),
            ),

            const SizedBox(height: 4),
          ],
        ),
      ),
    );
  }
}

/// Small action chip for the bottom panel.
class _ActionChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionChip({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 16),
      label: Text(
        label,
        style: const TextStyle(fontSize: 12),
      ),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppConfig.textSecondary,
        side: BorderSide(color: AppConfig.borderColor),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
    );
  }
}
