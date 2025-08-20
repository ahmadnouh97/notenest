import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';

import 'app_router.dart';
import 'shared/providers.dart';
import 'shared/theme.dart';

void main() {
  runApp(const ProviderScope(child: NotenestApp()));
}

class NotenestApp extends ConsumerStatefulWidget {
  const NotenestApp({super.key});

  @override
  ConsumerState<NotenestApp> createState() => _NotenestAppState();
}

class _NotenestAppState extends ConsumerState<NotenestApp> {
  late final GoRouter _router;
  StreamSubscription<List<SharedMediaFile>>? _sharedMediaSub;
  bool _handledInitialShare = false;

  @override
  void initState() {
    super.initState();
    _router = createRouter();
    // Load settings from storage on app start
    Future(() => ref.read(settingsControllerProvider.notifier).load());

    // Android-only: listen for share intents
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      _sharedMediaSub = ReceiveSharingIntent.instance.getMediaStream().listen(
        (List<SharedMediaFile> items) {
          _handleSharedItems(items);
        },
        onError: (_) {},
        cancelOnError: false,
      );

      // Handle the case where the app was launched via a share intent
      ReceiveSharingIntent.instance.getInitialMedia().then((
        List<SharedMediaFile> items,
      ) async {
        if (_handledInitialShare) return;
        _handledInitialShare = true;
        if (items.isNotEmpty) {
          _handleSharedItems(items);
          // consume the initial callback so it doesn't get delivered again
          await ReceiveSharingIntent.instance.reset();
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'notenest',
      theme: createAppTheme(),
      routerConfig: _router,
    );
  }

  @override
  void dispose() {
    _sharedMediaSub?.cancel();
    super.dispose();
  }

  void _handleSharedItems(List<SharedMediaFile> items) {
    if (items.isEmpty) return;
    // Prefer first URL, else text
    String? url;
    String? text;
    for (final item in items) {
      if (item.type == SharedMediaType.url && (item.path).isNotEmpty) {
        url ??= item.path;
      } else if (item.type == SharedMediaType.text && (item.path).isNotEmpty) {
        text ??= item.path;
      }
    }
    // Fallback: try to extract a URL from text
    url ??= text != null ? _extractFirstUrl(text) : null;
    final titleOrText = text ?? '';
    final encodedTitle = Uri.encodeComponent(
      titleOrText.length <= 200 ? titleOrText : titleOrText.substring(0, 200),
    );
    if (url != null && url.isNotEmpty) {
      final encodedUrl = Uri.encodeComponent(url);
      _router.push('/add?url=$encodedUrl&text=$encodedTitle');
    } else {
      _router.push('/add?text=$encodedTitle');
    }
  }

  String? _extractFirstUrl(String text) {
    final regex = RegExp(r'(https?:\/\/[^\s]+)', multiLine: true);
    final match = regex.firstMatch(text);
    if (match != null) {
      final candidate = match.group(0);
      try {
        if (candidate != null && Uri.parse(candidate).hasScheme) {
          return candidate;
        }
      } catch (_) {
        // ignore parse errors
      }
    }
    return null;
  }
}
