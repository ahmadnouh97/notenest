import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'app_router.dart';
import 'shared/providers.dart';

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

  @override
  void initState() {
    super.initState();
    _router = createRouter();
    // Load settings from storage on app start
    Future(() => ref.read(settingsControllerProvider.notifier).load());
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'notenest',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      routerConfig: _router,
    );
  }
}
