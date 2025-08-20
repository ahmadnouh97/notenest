import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'config.dart';

/// Provides a pre-configured Dio HTTP client with base options and interceptors.
class HttpClient {
  HttpClient._internal() {
    final baseOptions = BaseOptions(
      baseUrl: AppConfig.backendBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: const {
        'Content-Type': 'application/json',
      },
    );

    _dio = Dio(baseOptions);

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Attach any auth headers here if needed in future
        handler.next(options);
      },
      onResponse: (response, handler) {
        handler.next(response);
      },
      onError: (error, handler) {
        if (kDebugMode) {
          // Avoid logging sensitive data
          debugPrint('HTTP error: ${error.response?.statusCode} ${error.message}');
        }
        handler.next(error);
      },
    ));
  }

  static final HttpClient _instance = HttpClient._internal();

  factory HttpClient() => _instance;

  late final Dio _dio;

  Dio get dio => _dio;
}


