import 'package:hooks_riverpod/hooks_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'repository.dart';

// Repositories
final notesRepositoryProvider = Provider<NotesRepository>(
  (ref) => NotesRepository(),
);
final searchRepositoryProvider = Provider<SearchRepository>(
  (ref) => SearchRepository(),
);

// Local storage for provider/model settings
class SettingsState {
  final String provider;
  final String model;
  const SettingsState({
    this.provider = 'groq',
    this.model = 'openai/gpt-oss-120b',
  });

  SettingsState copyWith({String? provider, String? model}) => SettingsState(
    provider: provider ?? this.provider,
    model: model ?? this.model,
  );
}

class SettingsController extends StateNotifier<SettingsState> {
  SettingsController() : super(const SettingsState());

  static const _kProvider = 'provider';
  static const _kModel = 'model';

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final provider = prefs.getString(_kProvider) ?? state.provider;
    final model = prefs.getString(_kModel) ?? state.model;
    state = state.copyWith(provider: provider, model: model);
  }

  Future<void> setProvider(String provider) async {
    state = state.copyWith(provider: provider);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kProvider, provider);
  }

  Future<void> setModel(String model) async {
    state = state.copyWith(model: model);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kModel, model);
  }
}

final settingsControllerProvider =
    StateNotifierProvider<SettingsController, SettingsState>((ref) {
      return SettingsController();
    });
