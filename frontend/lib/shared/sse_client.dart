import 'dart:async';
import 'dart:convert';

// no external imports

/// Minimal SSE parsing utility for dio ResponseType.stream.
class SseClient {
  final Stream<List<int>> byteStream;

  SseClient(this.byteStream);

  Stream<SseEvent> events() async* {
    final decoder = utf8.decoder;
    String buffer = '';
    await for (final chunk in byteStream) {
      buffer += decoder.convert(chunk);
      final lines = buffer.split(RegExp(r'\r?\n'));
      if (!buffer.endsWith('\n')) {
        buffer = lines.removeLast();
      } else {
        buffer = '';
      }
      String? eventName;
      String data = '';
      for (final line in lines) {
        if (line.startsWith('event:')) {
          eventName = line.substring(6).trim();
        } else if (line.startsWith('data:')) {
          // Do not trim spaces from data; leading spaces are meaningful tokens
          final d = line.startsWith('data: ')
              ? line.substring(6)
              : line.substring(5);
          data = data.isEmpty ? d : '$data\n$d';
        } else if (line.isEmpty) {
          // dispatch
          if (data.isNotEmpty) {
            yield SseEvent(event: eventName, data: data);
            eventName = null;
            data = '';
          }
        }
      }
    }
  }
}

class SseEvent {
  final String? event;
  final String data;
  SseEvent({this.event, required this.data});
}


