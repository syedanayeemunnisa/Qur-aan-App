/// Data model representing a single Quranic verse with translations.
class Verse {
  final int surah;
  final int ayah;
  final String verseKey;
  final String arabic;
  final String normalized;
  final String translation;
  final String translationLanguage;
  final String? roman;
  final int? juz;
  final int? page;
  final double confidence;

  const Verse({
    required this.surah,
    required this.ayah,
    required this.verseKey,
    required this.arabic,
    required this.normalized,
    required this.translation,
    required this.translationLanguage,
    this.roman,
    this.juz,
    this.page,
    this.confidence = 1.0,
  });

  /// Create from JSON response from the API.
  factory Verse.fromJson(Map<String, dynamic> json) {
    return Verse(
      surah: json['surah'] as int,
      ayah: json['ayah'] as int,
      verseKey: json['verse_key'] as String? ?? '${json['surah']}:${json['ayah']}',
      arabic: json['arabic'] as String? ?? '',
      normalized: json['normalized'] as String? ?? '',
      translation: json['translation'] as String? ?? '',
      translationLanguage: json['translation_language'] as String? ?? 'english',
      roman: json['roman'] as String?,
      juz: json['juz'] as int?,
      page: json['page'] as int?,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
    );
  }

  /// Convert to JSON map.
  Map<String, dynamic> toJson() {
    return {
      'surah': surah,
      'ayah': ayah,
      'verse_key': verseKey,
      'arabic': arabic,
      'normalized': normalized,
      'translation': translation,
      'translation_language': translationLanguage,
      'roman': roman,
      'juz': juz,
      'page': page,
      'confidence': confidence,
    };
  }

  /// Display-friendly surah and ayah reference.
  String get reference => '$surah:$ayah';

  /// Whether this verse has a valid translation.
  bool get hasTranslation => translation.isNotEmpty;

  /// Whether this verse has transliteration.
  bool get hasRoman => roman != null && roman!.isNotEmpty;

  @override
  String toString() => 'Verse($reference): $arabic';
}

/// Response from the /detect endpoint.
class DetectResponse {
  final bool success;
  final String? detectedText;
  final Verse? matchedVerse;
  final List<Verse> alternatives;
  final String language;
  final String? error;

  const DetectResponse({
    required this.success,
    this.detectedText,
    this.matchedVerse,
    this.alternatives = const [],
    this.language = 'english',
    this.error,
  });

  factory DetectResponse.fromJson(Map<String, dynamic> json) {
    return DetectResponse(
      success: json['success'] as bool? ?? false,
      detectedText: json['detected_text'] as String?,
      matchedVerse: json['matched_verse'] != null
          ? Verse.fromJson(json['matched_verse'] as Map<String, dynamic>)
          : null,
      alternatives: (json['alternatives'] as List<dynamic>?)
              ?.map((e) => Verse.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      language: json['language'] as String? ?? 'english',
      error: json['error'] as String?,
    );
  }
}
