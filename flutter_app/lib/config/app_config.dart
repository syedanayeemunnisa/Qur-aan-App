/// Application configuration and constants.
class AppConfig {
  AppConfig._();

  // ── API ─────────────────────────────────────────────────────────
  /// Base URL of the FastAPI backend.
  /// Change to your server IP/domain in production.
  static const String apiBaseUrl = 'http://10.0.2.2:8000'; // Android emulator (10.0.2.2 = host machine)
  // static const String apiBaseUrl = 'http://localhost:8000'; // iOS simulator / desktop
  // static const String apiBaseUrl = 'http://192.168.x.x:8000'; // Physical device — use your PC's LAN IP
  // static const String apiBaseUrl = 'https://api.quranapp.com'; // Production

  static const String apiVersion = '/api/v1';
  static String get apiUrl => '$apiBaseUrl$apiVersion';

  // ── OCR ─────────────────────────────────────────────────────────
  static const double ocrConfidenceThreshold = 0.4;
  static const Duration ocrDebounce = Duration(milliseconds: 800);

  // ── Camera ──────────────────────────────────────────────────────
  static const double cameraAspectRatio = 9.0 / 16.0;
  static const ResolutionPreset resolutionPreset =
      ResolutionPreset.medium;

  // ── Languages ───────────────────────────────────────────────────
  static const String defaultLanguage = 'english';

  static const Map<String, String> supportedLanguages = {
    'english': 'English',
    'urdu': 'اردو (Urdu)',
    'hindi': 'हिन्दी (Hindi)',
    'telugu': 'తెలుగు (Telugu)',
    'roman': 'Roman English',
  };

  // ── UI ──────────────────────────────────────────────────────────
  static const String appName = 'Quranic';
  static const String appTagline = 'Read. Understand. Reflect.';

  // Colors - Islamic-inspired palette
  static const Color primaryColor = Color(0xFF1B5E20); // Dark green
  static const Color accentColor = Color(0xFFC8A951); // Gold
  static const Color backgroundColor = Color(0xFFF5F5F0);
  static const Color darkBackground = Color(0xFF121212);
  static const Color cardColor = Color(0xFFFFFFFF);
  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color overlayColor = Color(0x80000000);
  static const Color successColor = Color(0xFF10B981);
  static const Color errorColor = Color(0xFFEF4444);
  static const Color borderColor = Color(0xFFE5E7EB);

  // ── Storage ─────────────────────────────────────────────────────
  static const String prefLanguage = 'preferred_language';
  static const String prefNightMode = 'night_mode';
  static const String prefOfflineMode = 'offline_mode';
}
