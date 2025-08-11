import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

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
    final settingsCtrl = ref.read(settingsControllerProvider.notifier);
    final isStreaming = useState(false);
    final citations = useState<List<Map<String, dynamic>>>([]);

    Future<void> send() async {
      final text = inputController.text.trim();
      if (text.isEmpty || isStreaming.value) return;
      final messenger = ScaffoldMessenger.of(context);
      messages.value = [...messages.value, ChatMessage(role: 'user', content: text)];
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
            if (settings.apiKey.isNotEmpty) 'apiKey': settings.apiKey,
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
              final c = (obj['citations'] as List?)?.cast<Map<String, dynamic>>() ?? [];
              citations.value = c;
            } catch (_) {}
            break;
          }
          // Try parse as JSON; otherwise, take as token
          try {
            final _ = jsonDecode(ev.data) as Map<String, dynamic>;
          } catch (_) {
            assistant += ev.data;
            if (!hasAssistant && (messages.value.isEmpty || messages.value.last.role != 'assistant')) {
              messages.value = [
                ...messages.value,
                ChatMessage(role: 'assistant', content: assistant),
              ];
              hasAssistant = true;
            } else {
              // Update last assistant message
              final list = List<ChatMessage>.from(messages.value);
              if (list.isNotEmpty) {
                list[list.length - 1] = ChatMessage(role: 'assistant', content: assistant);
                messages.value = list;
              }
            }
          }
        }
      } catch (e) {
        messenger.showSnackBar(
          SnackBar(content: Text('Chat error: $e')),
        );
      } finally {
        isStreaming.value = false;
      }
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Chat')),
      body: Column(
        children: [
          // Provider/model selectors
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: useTextEditingController(text: settings.provider),
                    decoration: const InputDecoration(labelText: 'Provider', border: OutlineInputBorder()),
                    onSubmitted: settingsCtrl.setProvider,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: useTextEditingController(text: settings.model),
                    decoration: const InputDecoration(labelText: 'Model', border: OutlineInputBorder()),
                    onSubmitted: settingsCtrl.setModel,
                  ),
                ),
              ],
            ),
          ),
          if (citations.value.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              child: Wrap(
                spacing: 8,
                children: [
                  for (final c in citations.value)
                    ActionChip(
                      label: Text(c['title']?.toString() ?? 'Source'),
                      onPressed: () async {
                        final url = c['url']?.toString();
                        if (url != null && url.isNotEmpty) {
                          final uri = Uri.tryParse(url);
                          if (uri != null) {
                            await launchUrl(uri, mode: LaunchMode.externalApplication);
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
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.blue.shade100 : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(m.content),
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


