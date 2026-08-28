import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';
import '../models/verse.dart';
import '../services/quran_api_service.dart';

/// Application state provider for the Quran app.
class QuranProvider extends ChangeNotifier {
  final QuranApiService _apiService = QuranApiService();

  // ── State ────────────────────────────────────────────────────

  bool _isLoading = false;
  bool _isBackendConnected = false;
  String _selectedLanguage = AppConfig.defaultLanguage;
  String? _lastDetectedText;
  Verse? _currentVerse;
  List<Verse> _alternatives = [];
  String? _errorMessage;
  bool _nightMode = false;
  bool _offlineMode = true;

  // History of detected verses
  final List<Verse> _history = [];

  // ── Getters ──────────────────────────────────────────────────

  bool get isLoading => _isLoading;
  bool get isBackendConnected => _isBackendConnected;
  String get selectedLanguage => _selectedLanguage;
  String? get lastDetectedText => _lastDetectedText;
  Verse? get currentVerse => _currentVerse;
  List<Verse> get alternatives => _alternatives;
  String? get errorMessage => _errorMessage;
  bool get nightMode => _nightMode;
  bool get offlineMode => _offlineMode;
  List<Verse> get history => List.unmodifiable(_history);

  bool get hasVerse => _currentVerse != null;
  bool get hasError => _errorMessage != null;

  // ── Initialization ───────────────────────────────────────────

  Future<void> initialize() async {
    final prefs = await SharedPreferences.getInstance();
    _selectedLanguage =
        prefs.getString(AppConfig.prefLanguage) ?? AppConfig.defaultLanguage;
    _nightMode = prefs.getBool(AppConfig.prefNightMode) ?? false;
    _offlineMode = prefs.getBool(AppConfig.prefOfflineMode) ?? true;

    // Check backend health (non-blocking)
    _checkBackendHealth();

    notifyListeners();
  }

  // ── Language ─────────────────────────────────────────────────

  Future<void> setLanguage(String language) async {
    if (_selectedLanguage == language) return;

    _selectedLanguage = language;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConfig.prefLanguage, language);

    notifyListeners();
  }

  // ── Theme ────────────────────────────────────────────────────

  Future<void> toggleNightMode() async {
    _nightMode = !_nightMode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(AppConfig.prefNightMode, _nightMode);
    notifyListeners();
  }

  Future<void> setOfflineMode(bool value) async {
    _offlineMode = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(AppConfig.prefOfflineMode, value);
    notifyListeners();
  }

  // ── Verse Detection ──────────────────────────────────────────

  /// Process OCR text and identify the verse.
  Future<void> detectVerse(String ocrText) async {
    if (ocrText.trim().isEmpty) return;

    _isLoading = true;
    _errorMessage = null;
    _lastDetectedText = ocrText;
    notifyListeners();

    try {
      final response = await _apiService.detectFromText(
        ocrText: ocrText,
        language: _selectedLanguage,
      );

      if (response.success && response.matchedVerse != null) {
        _currentVerse = response.matchedVerse;
        _alternatives = response.alternatives;
        _addToHistory(response.matchedVerse!);
      } else {
        _currentVerse = null;
        _alternatives = [];
        _errorMessage = response.error ?? 'Could not identify the verse.';
      }
    } catch (e) {
      _currentVerse = null;
      _alternatives = [];
      _errorMessage = 'Connection error: ${e.toString()}';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Detect verse from a base64-encoded image.
  Future<void> detectFromImage(String imageBase64) async {
    if (imageBase64.isEmpty) return;

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _apiService.detectFromImage(
        imageBase64: imageBase64,
        language: _selectedLanguage,
      );

      if (response.success && response.matchedVerse != null) {
        _currentVerse = response.matchedVerse;
        _alternatives = response.alternatives;
        _lastDetectedText = response.detectedText;
        _addToHistory(response.matchedVerse!);
      } else {
        _currentVerse = null;
        _alternatives = [];
        _errorMessage = response.error ?? 'Could not identify the verse.';
      }
    } catch (e) {
      _currentVerse = null;
      _alternatives = [];
      _errorMessage = 'Connection error: ${e.toString()}';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // ── Verse Lookup ─────────────────────────────────────────────

  /// Look up a specific verse by reference.
  Future<void> lookupVerse(int surah, int ayah) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final verse = await _apiService.getVerse(
        surah: surah,
        ayah: ayah,
        language: _selectedLanguage,
      );

      if (verse != null) {
        _currentVerse = verse;
        _alternatives = [];
      } else {
        _errorMessage = 'Verse $surah:$ayah not found.';
      }
    } catch (e) {
      _errorMessage = 'Error: ${e.toString()}';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // ── History ─────────────────────────────────────────────────

  void _addToHistory(Verse verse) {
    // Avoid duplicates
    _history.removeWhere(
      (v) => v.surah == verse.surah && v.ayah == verse.ayah,
    );
    _history.insert(0, verse);

    // Keep only last 50 entries
    if (_history.length > 50) {
      _history.removeRange(50, _history.length);
    }
  }

  void clearHistory() {
    _history.clear();
    notifyListeners();
  }

  // ── Reset ────────────────────────────────────────────────────

  void resetDetection() {
    _currentVerse = null;
    _alternatives = [];
    _lastDetectedText = null;
    _errorMessage = null;
    _isLoading = false;
    notifyListeners();
  }

  // ── Backend Health ───────────────────────────────────────────

  Future<void> _checkBackendHealth() async {
    _isBackendConnected = await _apiService.isHealthy();
    notifyListeners();
  }

  Future<void> refreshBackendConnection() async {
    await _checkBackendHealth();
  }

  // ── Cleanup ─────────────────────────────────────────────────

  @override
  void dispose() {
    _apiService.dispose();
    super.dispose();
  }
}
