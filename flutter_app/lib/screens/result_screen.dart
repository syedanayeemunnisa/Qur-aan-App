import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_config.dart';
import '../models/verse.dart';
import '../providers/quran_provider.dart';
import '../widgets/verse_card.dart';

/// Detailed view of a detected verse with full Arabic, transliteration,
/// translation, and alternatives.
class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<QuranProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) {
          return const Scaffold(
            body: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Identifying verse...'),
                ],
              ),
            ),
          );
        }

        if (!provider.hasVerse) {
          return Scaffold(
            appBar: AppBar(
              title: const Text('No Verse Found'),
            ),
            body: const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.search_off, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text(
                    'Could not identify the verse.',
                    style: TextStyle(fontSize: 18),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Try re-scanning with better lighting\nor clearer focus.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            ),
          );
        }

        final verse = provider.currentVerse!;
        return Scaffold(
          body: CustomScrollView(
            slivers: [
              // ── App bar ────────────────────────────────
              SliverAppBar(
                expandedHeight: 100,
                pinned: true,
                flexibleSpace: FlexibleSpaceBar(
                  title: Text(
                    'Surah ${verse.surah}:${verse.ayah}',
                    style: const TextStyle(fontSize: 16),
                  ),
                  background: Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          AppConfig.primaryColor,
                          AppConfig.primaryColor.withValues(alpha: 0.7),
                        ],
                      ),
                    ),
                  ),
                ),
                actions: [
                  IconButton(
                    icon: const Icon(Icons.bookmark_border),
                    onPressed: () {},
                    tooltip: 'Bookmark',
                  ),
                  IconButton(
                    icon: const Icon(Icons.share),
                    onPressed: () {},
                    tooltip: 'Share',
                  ),
                ],
              ),

              // ── Main content ───────────────────────────
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Arabic text (full)
                      Container(
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: AppConfig.primaryColor
                              .withValues(alpha: 0.04),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: AppConfig.primaryColor
                                .withValues(alpha: 0.1),
                          ),
                        ),
                        child: Directionality(
                          textDirection: TextDirection.rtl,
                          child: Text(
                            verse.arabic,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 28,
                              fontWeight: FontWeight.w600,
                              height: 2.0,
                              color: AppConfig.textPrimary,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Transliteration (only if not already the selected translation)
                      if (verse.hasRoman && verse.translationLanguage != 'roman')
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.grey[50],
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            verse.roman!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 16,
                              fontStyle: FontStyle.italic,
                              color: AppConfig.textSecondary,
                              height: 1.5,
                            ),
                          ),
                        ),
                      if (verse.hasRoman && verse.translationLanguage != 'roman') const SizedBox(height: 16),

                      // Translation
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppConfig.accentColor
                              .withValues(alpha: 0.06),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: AppConfig.accentColor
                                .withValues(alpha: 0.15),
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.translate,
                                    size: 16,
                                    color: AppConfig.accentColor),
                                const SizedBox(width: 6),
                                Text(
                                  AppConfig.supportedLanguages[
                                          verse.translationLanguage] ??
                                      verse.translationLanguage,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: AppConfig.accentColor,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            Text(
                              verse.translation,
                              style: const TextStyle(
                                fontSize: 16,
                                height: 1.6,
                                color: AppConfig.textPrimary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),

                      // ── Action buttons ──────────────────
                      Row(
                        children: [
                          Expanded(
                            child: _ActionButton(
                              icon: Icons.volume_up,
                              label: 'Recitation',
                              onTap: () {},
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _ActionButton(
                              icon: Icons.menu_book,
                              label: 'Tafsir',
                              onTap: () {},
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _ActionButton(
                              icon: Icons.auto_stories,
                              label: 'Word by Word',
                              onTap: () {},
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // ── Alternative matches ─────────────
                      if (provider.alternatives.isNotEmpty) ...[
                        const Text(
                          'Alternative Matches',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: AppConfig.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        ...provider.alternatives.map(
                          (alt) => VerseCard(verse: alt),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // ── Last detected text ──────────────
                      if (provider.lastDetectedText != null) ...[
                        const Divider(),
                        const SizedBox(height: 8),
                        Text(
                          'Detected Text:',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppConfig.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          provider.lastDetectedText!,
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppConfig.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // ── Scan again button ───────────────
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton.icon(
                          onPressed: () {
                            provider.resetDetection();
                            Navigator.of(context).pop();
                          },
                          icon: const Icon(Icons.camera_alt),
                          label: const Text('Scan Another Verse'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppConfig.primaryColor,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// A styled action button.
class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
        side: BorderSide(color: AppConfig.borderColor),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      child: Column(
        children: [
          Icon(icon, color: AppConfig.primaryColor, size: 22),
          const SizedBox(height: 6),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color: AppConfig.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}
