import 'package:flutter/foundation.dart';

/// Global configuration for the app.
///
/// Values are read from compile-time environment via --dart-define.
/// Example:
///   flutter run -d chrome --dart-define=BACKEND_BASE_URL=http://localhost:8000
class AppConfig {
  AppConfig._();

  /// Base URL for the FastAPI backend, e.g. http://localhost:8000
  static const String backendBaseUrl =
      String.fromEnvironment('BACKEND_BASE_URL', defaultValue: 'http://localhost:8000');

  static bool get isWeb => kIsWeb;
}


