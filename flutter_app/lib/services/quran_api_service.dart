import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import '../config/app_config.dart';
import '../models/verse.dart';

/// Service for communicating with the Quran Translation API backend.
class QuranApiService {
  final String _baseUrl = AppConfig.apiUrl;
  final http.Client _client;

  QuranApiService({http.Client? client})
      : _client = client ?? http.Client();

  // ── Verse Detection (OCR + Match) ─────────────────────────────

  /// Detect a verse from a base64-encoded image.
  Future<DetectResponse> detectFromImage({
    required String imageBase64,
    String language = AppConfig.defaultLanguage,
  }) async {
    try {
      final response = await _client.post(
        Uri.parse('$_baseUrl/detect'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'image_base64': imageBase64,
          'language': language,
        }),
      );

      if (response.statusCode == 200) {
        return DetectResponse.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>,
        );
      } else {
        return DetectResponse(
          success: false,
          error: 'Server error: ${response.statusCode}',
        );
      }
    } catch (e) {
      return DetectResponse(
        success: false,
        error: 'Connection error: $e',
      );
    }
  }

  /// Detect a verse from pre-extracted OCR text.
  Future<DetectResponse> detectFromText({
    required String ocrText,
    String language = AppConfig.defaultLanguage,
  }) async {
    try {
      final response = await _client.post(
        Uri.parse('$_baseUrl/detect'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'ocr_text': ocrText,
          'language': language,
        }),
      );

      if (response.statusCode == 200) {
        return DetectResponse.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>,
        );
      } else {
        return DetectResponse(
          success: false,
          error: 'Server error: ${response.statusCode}',
        );
      }
    } catch (e) {
      return DetectResponse(
        success: false,
        error: 'Connection error: $e',
      );
    }
  }

  // ── Direct Verse Lookup ───────────────────────────────────────

  /// Fetch a specific verse by surah and ayah number.
  Future<Verse?> getVerse({
    required int surah,
    required int ayah,
    String language = AppConfig.defaultLanguage,
  }) async {
    try {
      final response = await _client.get(
        Uri.parse('$_baseUrl/verse/$surah/$ayah?language=$language'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        return Verse.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>,
        );
      }
    } catch (e) {
      // Silently fail — caller handles null
    }
    return null;
  }

  // ── Search ─────────────────────────────────────────────────────

  /// Search verses by translation text.
  Future<List<Verse>> search({
    required String query,
    String language = AppConfig.defaultLanguage,
    int limit = 10,
  }) async {
    try {
      final response = await _client.get(
        Uri.parse(
          '$_baseUrl/search?q=$query&language=$language&limit=$limit',
        ),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return (data['results'] as List<dynamic>)
            .map((e) => Verse.fromJson(e as Map<String, dynamic>))
            .toList();
      }
    } catch (e) {
      // Silently fail
    }
    return [];
  }

  // ── Languages ──────────────────────────────────────────────────

  /// Get list of supported translation languages.
  Future<List<String>> getLanguages() async {
    try {
      final response = await _client.get(
        Uri.parse('$_baseUrl/languages'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return (data['languages'] as List<dynamic>)
            .map((e) => (e as Map<String, dynamic>)['code'] as String)
            .toList();
      }
    } catch (e) {
      // Silently fail
    }
    return ['english', 'urdu', 'hindi', 'telugu'];
  }

  // ── Health Check ───────────────────────────────────────────────

  /// Check if the backend is healthy and responding.
  Future<bool> isHealthy() async {
    try {
      final response = await _client.get(
        Uri.parse('$_baseUrl/health'),
      ).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Clean up resources.
  void dispose() {
    _client.close();
  }
}
