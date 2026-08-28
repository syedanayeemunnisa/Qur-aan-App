import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_config.dart';
import '../providers/quran_provider.dart';
import '../widgets/language_selector.dart';
import '../widgets/verse_card.dart';
import 'camera_screen.dart';
import 'result_screen.dart';

/// Main home screen with options to scan, search, and browse history.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<QuranProvider>(
      builder: (context, provider, _) {
        return Scaffold(
          backgroundColor: AppConfig.backgroundColor,
          body: SafeArea(
            child: CustomScrollView(
              slivers: [
                // ── Header ───────────────────────────────
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // App title
                        Row(
                          children: [
                            // Logo / Icon
                            Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                color: AppConfig.primaryColor,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Center(
                                child: Icon(
                                  Icons.menu_book_rounded,
                                  color: Colors.white,
                                  size: 24,
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  AppConfig.appName,
                                  style: const TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.w700,
                                    color: AppConfig.textPrimary,
                                  ),
                                ),
                                Text(
                                  AppConfig.appTagline,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: AppConfig.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                            const Spacer(),

                            // Settings / Night mode
                            IconButton(
                              icon: Icon(
                                provider.nightMode
                                    ? Icons.dark_mode
                                    : Icons.light_mode,
                                color: AppConfig.textSecondary,
                              ),
                              onPressed: provider.toggleNightMode,
                              tooltip: 'Toggle theme',
                            ),
                          ],
                        ),
                        const SizedBox(height: 20),

                        // ── Quick scan card ─────────────
                        Container(
                          padding: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                AppConfig.primaryColor,
                                AppConfig.primaryColor
                                    .withValues(alpha: 0.7),
                              ],
                            ),
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [
                              BoxShadow(
                                color: AppConfig.primaryColor
                                    .withValues(alpha: 0.3),
                                blurRadius: 20,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Icon(Icons.camera_alt,
                                      color: Colors.white, size: 28),
                                  SizedBox(width: 12),
                                  Text(
                                    'Scan Quran Page',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 20,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                'Point your camera at any Quran page\nto instantly read translations.',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 14,
                                  height: 1.4,
                                ),
                              ),
                              const SizedBox(height: 20),
                              SizedBox(
                                width: double.infinity,
                                height: 48,
                                child: ElevatedButton.icon(
                                  onPressed: () {
                                    Navigator.of(context).push(
                                      MaterialPageRoute(
                                        builder: (_) => const CameraScreen(),
                                      ),
                                    );
                                  },
                                  icon: const Icon(Icons.camera_alt),
                                  label: const Text(
                                    'Open Camera Scanner',
                                    style: TextStyle(fontSize: 15),
                                  ),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.white,
                                    foregroundColor:
                                        AppConfig.primaryColor,
                                    shape: RoundedRectangleBorder(
                                      borderRadius:
                                          BorderRadius.circular(14),
                                    ),
                                    elevation: 0,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 24),

                        // ── Language selector ───────────
                        Row(
                          children: [
                            const Text(
                              'Translation Language',
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                                color: AppConfig.textPrimary,
                              ),
                            ),
                            const Spacer(),
                            GestureDetector(
                              onTap: () {
                                showModalBottomSheet(
                                  context: context,
                                  shape: const RoundedRectangleBorder(
                                    borderRadius: BorderRadius.vertical(
                                      top: Radius.circular(20),
                                    ),
                                  ),
                                  builder: (_) => LanguageSheet(
                                    selectedLanguage:
                                        provider.selectedLanguage,
                                    onChanged: (lang) {
                                      provider.setLanguage(lang);
                                    },
                                  ),
                                );
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 14,
                                  vertical: 8,
                                ),
                                decoration: BoxDecoration(
                                  border: Border.all(
                                      color: AppConfig.borderColor),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.translate,
                                        size: 16,
                                        color: AppConfig.primaryColor),
                                    const SizedBox(width: 6),
                                    Text(
                                      AppConfig.supportedLanguages[
                                              provider.selectedLanguage] ??
                                          provider.selectedLanguage,
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: AppConfig.primaryColor,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(width: 4),
                                    Icon(Icons.arrow_drop_down,
                                        size: 18,
                                        color: AppConfig.primaryColor),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Translations will appear in your selected language',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppConfig.textSecondary
                                .withValues(alpha: 0.7),
                          ),
                        ),
                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),

                // ── Recent history ──────────────────────
                if (provider.history.isNotEmpty) ...[
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
                      child: Row(
                        children: [
                          const Text(
                            'Recently Read',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: AppConfig.textPrimary,
                            ),
                          ),
                          const Spacer(),
                          GestureDetector(
                            onTap: provider.clearHistory,
                            child: Text(
                              'Clear all',
                              style: TextStyle(
                                fontSize: 13,
                                color: AppConfig.textSecondary,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final verse = provider.history[index];
                        return VerseCard(
                          verse: verse,
                          onTap: () {
                            provider.lookupVerse(
                              verse.surah,
                              verse.ayah,
                            );
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => const ResultScreen(),
                              ),
                            );
                          },
                        );
                      },
                      childCount: provider.history.length.clamp(0, 20),
                    ),
                  ),
                ] else ...[
                  // Empty state
                  SliverFillRemaining(
                    hasScrollBody: false,
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.all(40),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.menu_book_rounded,
                              size: 80,
                              color: AppConfig.primaryColor
                                  .withValues(alpha: 0.2),
                            ),
                            const SizedBox(height: 20),
                            const Text(
                              'Start Reading',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.w600,
                                color: AppConfig.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Scan any Quran page to see\ntranslations and transliterations.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 14,
                                color: AppConfig.textSecondary
                                    .withValues(alpha: 0.7),
                                height: 1.5,
                              ),
                            ),
                            const SizedBox(height: 24),
                            OutlinedButton.icon(
                              onPressed: () {
                                Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        const CameraScreen(),
                                  ),
                                );
                              },
                              icon: const Icon(Icons.camera_alt),
                              label: const Text('Scan Now'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}
