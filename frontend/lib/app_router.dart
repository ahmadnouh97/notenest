import 'package:go_router/go_router.dart';

import 'chat/chat_screen.dart';
import 'notes/notes_screens.dart';
import 'settings/settings_screen.dart';
import 'shared/models.dart';

GoRouter createRouter() {
  return GoRouter(
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const NotesListScreen(),
      ),
      GoRoute(
        path: '/add',
        builder: (context, state) {
          final note = state.extra is Note ? state.extra as Note : null;
          final url = state.uri.queryParameters['url'];
          final title = state.uri.queryParameters['title'];
          final desc = state.uri.queryParameters['text'] ?? state.uri.queryParameters['description'];
          return AddEditNoteScreen(existing: note, prefillUrl: url, prefillTitle: title, prefillDescription: desc);
        },
      ),
      GoRoute(
        path: '/chat',
        builder: (context, state) => const ChatScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
    ],
  );
}


