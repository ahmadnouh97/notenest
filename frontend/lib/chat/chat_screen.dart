import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../shared/http_client.dart';
import '../shared/models.dart';
import '../shared/providers.dart';
import '../shared/sse_client.dart';
import 'package:url_launcher/url_launcher.dart';

class ChatScreen extends HookConsumerWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final messages = useState<List<ChatMessage>>([]);
    final inputController = useTextEditingController();
    final settings = ref.watch(settingsControllerProvider);
    final isStreaming = useState(false);
    final citations = useState<List<Map<String, dynamic>>>([]);

    Future<void> send() async {
      final text = inputController.text.trim();
      if (text.isEmpty || isStreaming.value) return;
      final messenger = ScaffoldMessenger.of(context);
      messages.value = [
        ...messages.value,
        ChatMessage(role: 'user', content: text),
      ];
      inputController.clear();

      isStreaming.value = true;
      final client = HttpClient().dio;

      try {
        final req = await client.post(
          '/api/chat',
          data: {
            'messages': messages.value.map((m) => m.toJson()).toList(),
            'provider': settings.provider,
            'model': settings.model,
          },
          options: Options(responseType: ResponseType.stream),
        );

        final stream = req.data.stream as Stream<List<int>>;
        final sse = SseClient(stream);
        String assistant = '';
        bool hasAssistant = false;
        citations.value = [];
        await for (final ev in sse.events()) {
          if (ev.event == 'done') {
            try {
              final obj = jsonDecode(ev.data) as Map<String, dynamic>;
              final c =
                  (obj['citations'] as List?)?.cast<Map<String, dynamic>>() ??
                  [];
              citations.value = c;
            } catch (_) {}
            break;
          }
          // Try parse as JSON; otherwise, take as token
          try {
            final _ = jsonDecode(ev.data) as Map<String, dynamic>;
          } catch (_) {
            assistant += ev.data;
            if (!hasAssistant &&
                (messages.value.isEmpty ||
                    messages.value.last.role != 'assistant')) {
              messages.value = [
                ...messages.value,
                ChatMessage(role: 'assistant', content: assistant),
              ];
              hasAssistant = true;
            } else {
              // Update last assistant message
              final list = List<ChatMessage>.from(messages.value);
              if (list.isNotEmpty) {
                list[list.length - 1] = ChatMessage(
                  role: 'assistant',
                  content: assistant,
                );
                messages.value = list;
              }
            }
          }
        }
      } catch (e) {
        messenger.showSnackBar(SnackBar(content: Text('Chat error: $e')));
      } finally {
        isStreaming.value = false;
      }
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Chat')),
      body: Column(
        children: [
          if (citations.value.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              child: Wrap(
                spacing: 8,
                children: [
                  for (final c in citations.value)
                    ActionChip(
                      label: Text(
                        c['title']?.toString() ?? 'Source',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onTertiary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      backgroundColor: Theme.of(context).colorScheme.tertiary,
                      elevation: 2,
                      onPressed: () async {
                        final url = c['url']?.toString();
                        if (url != null && url.isNotEmpty) {
                          final uri = Uri.tryParse(url);
                          if (uri != null) {
                            await launchUrl(
                              uri,
                              mode: LaunchMode.externalApplication,
                            );
                          }
                        }
                      },
                    ),
                ],
              ),
            ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: messages.value.length,
              itemBuilder: (context, index) {
                final m = messages.value[index];
                final isUser = m.role == 'user';
                return Align(
                  alignment: isUser
                      ? Alignment.centerRight
                      : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isUser
                          ? Theme.of(
                              context,
                            ).colorScheme.secondary.withValues(alpha: 0.3)
                          : Theme.of(
                              context,
                            ).colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: _MessageContent(content: m.content, isUser: isUser),
                  ),
                );
              },
            ),
          ),
          SafeArea(
            child: Row(
              children: [
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: TextField(
                      controller: inputController,
                      onSubmitted: (_) => send(),
                      decoration: const InputDecoration(
                        hintText: 'Ask something...',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: isStreaming.value ? null : send,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageContent extends StatelessWidget {
  const _MessageContent({required this.content, required this.isUser});

  final String content;
  final bool isUser;

  @override
  Widget build(BuildContext context) {
    // User messages are displayed as plain text
    if (isUser) {
      return Text(content, style: const TextStyle(fontSize: 16));
    }

    // Assistant messages are rendered as markdown
    return MarkdownBody(
      data: content,
      styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
        p: Theme.of(context).textTheme.bodyLarge,
        h1: Theme.of(context).textTheme.headlineSmall,
        h2: Theme.of(context).textTheme.titleLarge,
        h3: Theme.of(context).textTheme.titleMedium,
        code: TextStyle(
          backgroundColor: Theme.of(
            context,
          ).colorScheme.tertiary.withValues(alpha: 0.1),
          color: Theme.of(context).colorScheme.tertiary,
          fontFamily: 'monospace',
          fontSize: 14,
        ),
        codeblockDecoration: BoxDecoration(
          color: Theme.of(context).colorScheme.tertiary.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: Theme.of(
              context,
            ).colorScheme.tertiary.withValues(alpha: 0.3),
            width: 1,
          ),
        ),
        codeblockPadding: const EdgeInsets.all(12),
        a: TextStyle(
          color: Theme.of(context).colorScheme.primary,
          decoration: TextDecoration.underline,
        ),
        blockquoteDecoration: BoxDecoration(
          color: Theme.of(context).colorScheme.secondary.withValues(alpha: 0.1),
          border: Border(
            left: BorderSide(
              color: Theme.of(context).colorScheme.secondary,
              width: 4,
            ),
          ),
        ),
      ),
      onTapLink: (text, href, title) async {
        if (href != null) {
          final uri = Uri.tryParse(href);
          if (uri != null) {
            await launchUrl(uri, mode: LaunchMode.externalApplication);
          }
        }
      },
    );
  }
}
