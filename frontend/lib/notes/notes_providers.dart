import 'dart:async';

import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

import '../shared/models.dart';
import '../shared/providers.dart';

class NotesFilter {
  final String query;
  final List<String> tags;
  const NotesFilter({this.query = '', this.tags = const []});

  String get tagsCsv => tags.join(',');

  NotesFilter copyWith({String? query, List<String>? tags}) => NotesFilter(
        query: query ?? this.query,
        tags: tags ?? this.tags,
      );
}

final notesFilterProvider = StateProvider<NotesFilter>((ref) => const NotesFilter());

final notesListProvider = FutureProvider.autoDispose<List<Note>>((ref) async {
  final repo = ref.read(notesRepositoryProvider);
  final filter = ref.watch(notesFilterProvider);
  return repo.listNotes(
    tagsCsv: filter.tags.isEmpty ? null : filter.tagsCsv,
    q: filter.query.isEmpty ? null : filter.query,
  );
});

class SearchDebouncer {
  final void Function(String) onValue;
  final Duration delay;
  Timer? _timer;
  SearchDebouncer({required this.onValue, this.delay = const Duration(milliseconds: 400)});
  void call(String value) {
    _timer?.cancel();
    _timer = Timer(delay, () => onValue(value));
  }
  void dispose() => _timer?.cancel();
}

SearchDebouncer useSearchDebouncer(void Function(String) onValue, {Duration delay = const Duration(milliseconds: 400)}) {
  return useMemoized(() => SearchDebouncer(onValue: onValue, delay: delay), [onValue, delay]);
}


