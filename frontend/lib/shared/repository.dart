import 'dart:async';

import 'package:dio/dio.dart';

import 'http_client.dart';
import 'models.dart';

class ApiError implements Exception {
  final String message;
  final int? statusCode;
  ApiError(this.message, {this.statusCode});
  @override
  String toString() => 'ApiError($statusCode): $message';
}

class NotesRepository {
  final Dio _dio = HttpClient().dio;

  Future<Note> createNote({
    required String url,
    String? title,
    String? description,
    List<String>? tags,
  }) async {
    try {
      final res = await _dio.post(
        '/api/notes',
        data: {
          'url': url,
          if (title != null) 'title': title,
          if (description != null) 'description': description,
          if (tags != null) 'tags': tags,
        },
      );
      return Note.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiError(e.response?.data?.toString() ?? 'Failed to create note',
          statusCode: e.response?.statusCode);
    }
  }

  Future<List<Note>> listNotes({
    String? tagsCsv,
    String? q,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final res = await _dio.get('/api/notes', queryParameters: {
        if (tagsCsv != null && tagsCsv.isNotEmpty) 'tags': tagsCsv,
        if (q != null && q.isNotEmpty) 'q': q,
        'limit': limit,
        'offset': offset,
      });
      final data = res.data as List;
      return data.map((e) => Note.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiError(e.response?.data?.toString() ?? 'Failed to list notes',
          statusCode: e.response?.statusCode);
    }
  }

  Future<Note> updateNote(
    String id, {
    String? url,
    String? title,
    String? description,
    List<String>? tags,
  }) async {
    try {
      final res = await _dio.put('/api/notes/$id', data: {
        if (url != null) 'url': url,
        if (title != null) 'title': title,
        if (description != null) 'description': description,
        if (tags != null) 'tags': tags,
      });
      return Note.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiError(e.response?.data?.toString() ?? 'Failed to update note',
          statusCode: e.response?.statusCode);
    }
  }

  Future<void> deleteNote(String id) async {
    try {
      await _dio.delete('/api/notes/$id');
    } on DioException catch (e) {
      throw ApiError(e.response?.data?.toString() ?? 'Failed to delete note',
          statusCode: e.response?.statusCode);
    }
  }
}

class SearchRepository {
  final Dio _dio = HttpClient().dio;

  Future<List<SearchResultItem>> search({
    required String query,
    List<String>? tags,
    int topK = 10,
    double? hybridWeight,
  }) async {
    try {
      final res = await _dio.post('/api/search', data: {
        'query': query,
        if (tags != null) 'tags': tags,
        'topK': topK,
        if (hybridWeight != null) 'hybridWeight': hybridWeight,
      });
      final list = res.data as List;
      return list
          .map((e) => SearchResultItem.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiError(e.response?.data?.toString() ?? 'Search failed',
          statusCode: e.response?.statusCode);
    }
  }
}


