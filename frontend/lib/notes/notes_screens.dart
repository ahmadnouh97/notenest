import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../shared/models.dart';
import '../shared/providers.dart';
import 'notes_providers.dart';

class NotesListScreen extends HookConsumerWidget {
  const NotesListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notesAsync = ref.watch(notesListProvider);
    final filter = ref.watch(notesFilterProvider);
    final setFilter = ref.read(notesFilterProvider.notifier);

    final controller = useTextEditingController(text: filter.query);
    final debouncer = useMemoized(
      () => SearchDebouncer(onValue: (value) => setFilter.state = filter.copyWith(query: value)),
      [filter, setFilter],
    );
    useEffect(() {
      return debouncer.dispose;
    }, [debouncer]);

    final selectedIds = useState<Set<String>>({});
    final isProcessing = useState<bool>(false);
    final isSelecting = selectedIds.value.isNotEmpty;
    final currentNotes = notesAsync.value ?? const <Note>[];

    void toggleSelection(String id) {
      final next = Set<String>.from(selectedIds.value);
      if (next.contains(id)) {
        next.remove(id);
      } else {
        next.add(id);
      }
      selectedIds.value = next;
    }

    Future<void> deleteSelected() async {
      if (selectedIds.value.isEmpty) return;
      final messenger = ScaffoldMessenger.of(context);
      isProcessing.value = true;
      try {
        final repo = ref.read(notesRepositoryProvider);
        // Delete in parallel but not too many at once; simple Future.wait is fine for small sets
        await Future.wait(selectedIds.value.map(repo.deleteNote));
        selectedIds.value = {};
        ref.invalidate(notesListProvider);
        messenger.showSnackBar(const SnackBar(content: Text('Deleted selected notes')));
      } catch (e) {
        messenger.showSnackBar(SnackBar(content: Text('Delete failed: $e')));
      } finally {
        isProcessing.value = false;
      }
    }

    return Scaffold(
      appBar: AppBar(
        leading: isSelecting
            ? IconButton(
                icon: const Icon(Icons.close),
                onPressed: isProcessing.value
                    ? null
                    : () {
                        selectedIds.value = {};
                      },
              )
            : null,
        title: isSelecting
            ? Text('${selectedIds.value.length} selected')
            : const Text('Notes'),
        actions: [
          if (isSelecting) ...[
            IconButton(
              tooltip: 'Select all',
              onPressed: isProcessing.value
                  ? null
                  : () {
                      final allVisibleIds = currentNotes.map((e) => e.id).toSet();
                      final next = Set<String>.from(selectedIds.value);
                      if (next.length == allVisibleIds.length) {
                        selectedIds.value = {};
                      } else {
                        selectedIds.value = allVisibleIds;
                      }
                    },
              icon: const Icon(Icons.select_all),
            ),
            IconButton(
              tooltip: 'Delete selected',
              onPressed: isProcessing.value ? null : deleteSelected,
              icon: const Icon(Icons.delete_outline),
            ),
          ] else ...[
            IconButton(
              onPressed: () => context.push('/settings'),
              icon: const Icon(Icons.settings),
            ),
            IconButton(
              onPressed: () => context.push('/chat'),
              icon: const Icon(Icons.chat_bubble_outline),
            ),
          ],
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/add'),
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Search notes...',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
              onChanged: debouncer.call,
            ),
          ),
          // Tag chips (multi-select AND) based on tags present in current list
          notesAsync.maybeWhen(
            data: (notes) {
              final allTags = <String>{};
              for (final n in notes) {
                allTags.addAll(n.tags);
              }
              final tags = allTags.toList()..sort();
              if (tags.isEmpty) return const SizedBox.shrink();
              return SizedBox(
                height: 48,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemBuilder: (context, index) {
                    final t = tags[index];
                    final selected = filter.tags.contains(t);
                    return FilterChip(
                      label: Text(t),
                      selected: selected,
                      onSelected: (_) {
                        final next = [...filter.tags];
                        if (selected) {
                          next.remove(t);
                        } else {
                          next.add(t);
                        }
                        setFilter.state = filter.copyWith(tags: next);
                      },
                    );
                  },
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemCount: tags.length,
                ),
              );
            },
            orElse: () => const SizedBox.shrink(),
          ),
          Expanded(
            child: notesAsync.when(
              data: (notes) => ListView.separated(
                itemCount: notes.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, index) {
                  final n = notes[index];
                  final selected = selectedIds.value.contains(n.id);
                  return Dismissible(
                    key: ValueKey(n.id),
                    direction: isSelecting ? DismissDirection.none : DismissDirection.endToStart,
                    background: Container(
                      color: Colors.red,
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: const Icon(Icons.delete, color: Colors.white),
                    ),
                    confirmDismiss: (_) async {
                      return await showDialog<bool>(
                            context: context,
                            builder: (_) => AlertDialog(
                              title: const Text('Delete note?'),
                              content: Text(n.title.isEmpty ? n.url : n.title),
                              actions: [
                                TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
                                FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
                              ],
                            ),
                          ) ??
                          false;
                    },
                    onDismissed: (_) async {
                      await ref.read(notesRepositoryProvider).deleteNote(n.id);
                      ref.invalidate(notesListProvider);
                    },
                    child: ListTile(
                      leading: isSelecting
                          ? Checkbox(
                              value: selected,
                              onChanged: isProcessing.value ? null : (_) => toggleSelection(n.id),
                            )
                          : null,
                      title: Text(n.title.isEmpty ? n.url : n.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(_domainOf(n.url), maxLines: 1, overflow: TextOverflow.ellipsis),
                          if (n.tags.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Wrap(
                                spacing: 6,
                                runSpacing: -8,
                                children: n.tags
                                    .map((t) => Chip(label: Text(t), visualDensity: VisualDensity.compact))
                                    .toList(),
                              ),
                            ),
                        ],
                      ),
                      onTap: () {
                        if (isSelecting) {
                          toggleSelection(n.id);
                        } else {
                          context.push('/add', extra: n);
                        }
                      },
                      onLongPress: () {
                        if (!isSelecting) {
                          selectedIds.value = {n.id};
                        }
                      },
                    ),
                  );
                },
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, st) => Center(child: Text('Error: $e')),
            ),
          ),
        ],
      ),
    );
  }

  String _domainOf(String url) {
    try {
      final uri = Uri.parse(url);
      return uri.host;
    } catch (_) {
      return url;
    }
  }
}

class AddEditNoteScreen extends HookConsumerWidget {
  final Note? existing;
  final String? prefillUrl;
  final String? prefillTitle;
  final String? prefillDescription;
  const AddEditNoteScreen({super.key, this.existing, this.prefillUrl, this.prefillTitle, this.prefillDescription});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final title = useTextEditingController(text: existing?.title ?? prefillTitle ?? '');
    final url = useTextEditingController(text: existing?.url ?? prefillUrl ?? '');
    final description = useTextEditingController(text: existing?.description ?? prefillDescription ?? '');
    final tagText = useTextEditingController(text: existing?.tags.join(',') ?? '');

    // Android share intent prefill (best-effort; requires intent filter configured later)
    // Web prefill handled via router query params; Android share handled in M7.

    Future<void> submit() async {
      final tags = tagText.text
          .split(',')
          .map((e) => e.trim())
          .where((e) => e.isNotEmpty)
          .toList();
      if (existing == null) {
        await ref.read(notesRepositoryProvider).createNote(
              url: url.text.trim(),
              title: title.text.trim().isEmpty ? null : title.text.trim(),
              description: description.text.trim().isEmpty ? null : description.text.trim(),
              tags: tags.isEmpty ? null : tags,
            );
      } else {
        await ref.read(notesRepositoryProvider).updateNote(
              existing!.id,
              url: url.text.trim(),
              title: title.text.trim(),
              description: description.text.trim(),
              tags: tags,
            );
      }
      ref.invalidate(notesListProvider);
      if (context.mounted) Navigator.pop(context);
    }

    return Scaffold(
      appBar: AppBar(title: Text(existing == null ? 'Add note' : 'Edit note')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: url,
              decoration: const InputDecoration(labelText: 'URL', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: title,
              decoration: const InputDecoration(labelText: 'Title', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: description,
              maxLines: 6,
              decoration: const InputDecoration(labelText: 'Description', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: tagText,
              decoration: const InputDecoration(labelText: 'Tags (comma separated)', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: submit,
                child: Text(existing == null ? 'Create' : 'Update'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}


