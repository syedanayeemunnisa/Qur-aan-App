import 'package:flutter/material.dart';
import '../config/app_config.dart';

/// A styled dropdown for selecting the translation language.
class LanguageSelector extends StatelessWidget {
  final String selectedLanguage;
  final ValueChanged<String> onChanged;
  final bool isExpanded;

  const LanguageSelector({
    super.key,
    required this.selectedLanguage,
    required this.onChanged,
    this.isExpanded = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.black38,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: Colors.white24,
          width: 1,
        ),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: selectedLanguage,
          isDense: true,
          isExpanded: isExpanded,
          icon: const Icon(
            Icons.language,
            color: Colors.white70,
            size: 18,
          ),
          dropdownColor: const Color(0xFF1A1A2E),
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
          selectedItemBuilder: (context) {
            return AppConfig.supportedLanguages.keys.map((key) {
              return Container(
                alignment: Alignment.center,
                padding: const EdgeInsets.only(left: 8),
                child: Text(
                  AppConfig.supportedLanguages[key]!.split(' ').first,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                  ),
                ),
              );
            }).toList();
          },
          items: AppConfig.supportedLanguages.entries.map((entry) {
            return DropdownMenuItem<String>(
              value: entry.key,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    // Language flag / indicator
                    _languageIndicator(entry.key),
                    const SizedBox(width: 12),
                    Text(
                      entry.value,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                      ),
                    ),
                    if (entry.key == selectedLanguage) ...[
                      const Spacer(),
                      const Icon(
                        Icons.check,
                        color: AppConfig.accentColor,
                        size: 16,
                      ),
                    ],
                  ],
                ),
              ),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) onChanged(value);
          },
        ),
      ),
    );
  }

  Widget _languageIndicator(String code) {
    IconData icon;
    switch (code) {
      case 'english':
        icon = Icons.language;
        break;
      case 'urdu':
        icon = Icons.auto_stories;
        break;
      case 'hindi':
        icon = Icons.translate;
        break;
      case 'telugu':
        icon = Icons.auto_stories;
        break;
      case 'roman':
        icon = Icons.text_fields;
        break;
      default:
        icon = Icons.translate;
    }
    return Icon(icon, color: AppConfig.accentColor, size: 16);
  }
}

/// Helper: icon for the sheet list.
IconData _sheetIcon(String code) {
  switch (code) {
    case 'english':
      return Icons.language;
    case 'roman':
      return Icons.text_fields;
    default:
      return Icons.translate;
  }
}

/// A bottom-sheet version for the home screen.
class LanguageSheet extends StatelessWidget {
  final String selectedLanguage;
  final ValueChanged<String> onChanged;

  const LanguageSheet({
    super.key,
    required this.selectedLanguage,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle
            Center(
              child: Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),

            const Text(
              'Translation Language',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppConfig.textPrimary,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Select your preferred translation language',
              style: TextStyle(
                fontSize: 13,
                color: AppConfig.textSecondary,
              ),
            ),
            const SizedBox(height: 16),

            ...AppConfig.supportedLanguages.entries.map((entry) {
              final isSelected = entry.key == selectedLanguage;
              return Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: ListTile(
                  leading: Icon(
                    _sheetIcon(entry.key),
                    color: isSelected
                        ? AppConfig.primaryColor
                        : AppConfig.textSecondary,
                  ),
                  title: Text(
                    entry.value,
                    style: TextStyle(
                      fontWeight:
                          isSelected ? FontWeight.w600 : FontWeight.normal,
                      color: isSelected
                          ? AppConfig.primaryColor
                          : AppConfig.textPrimary,
                    ),
                  ),
                  trailing: isSelected
                      ? const Icon(
                          Icons.check_circle,
                          color: AppConfig.primaryColor,
                        )
                      : null,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  tileColor: isSelected
                      ? AppConfig.primaryColor.withValues(alpha: 0.06)
                      : null,
                  onTap: () {
                    onChanged(entry.key);
                    Navigator.of(context).pop();
                  },
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
