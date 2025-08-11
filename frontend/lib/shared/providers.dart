import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'repository.dart';

// Repositories
final notesRepositoryProvider = Provider<NotesRepository>((ref) => NotesRepository());
final searchRepositoryProvider = Provider<SearchRepository>((ref) => SearchRepository());

// Local storage for provider/model/apiKey (never sent to backend except in chat requests)
class SettingsState {
  final String provider;
  final String model;
  final String apiKey; // stored locally only
  const SettingsState({this.provider = 'openrouter', this.model = 'gpt-4o-mini', this.apiKey = ''});

  SettingsState copyWith({String? provider, String? model, String? apiKey}) => SettingsState(
        provider: provider ?? this.provider,
        model: model ?? this.model,
        apiKey: apiKey ?? this.apiKey,
      );
}

class SettingsController extends StateNotifier<SettingsState> {
  SettingsController(this._secureStorage) : super(const SettingsState());

  final FlutterSecureStorage _secureStorage;

  static const _kProvider = 'provider';
  static const _kModel = 'model';
  static const _kApiKey = 'apiKey';

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final provider = prefs.getString(_kProvider) ?? state.provider;
    final model = prefs.getString(_kModel) ?? state.model;
    final apiKey = await _secureStorage.read(key: _kApiKey) ?? state.apiKey;
    state = state.copyWith(provider: provider, model: model, apiKey: apiKey);
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

  Future<void> setApiKey(String apiKey) async {
    state = state.copyWith(apiKey: apiKey);
    await _secureStorage.write(key: _kApiKey, value: apiKey);
  }
}

final secureStorageProvider = Provider((ref) => const FlutterSecureStorage());
final settingsControllerProvider = StateNotifierProvider<SettingsController, SettingsState>((ref) {
  return SettingsController(ref.read(secureStorageProvider));
});


