import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';

import '../shared/providers.dart';

class SettingsScreen extends HookConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(settingsControllerProvider);
    final controller = ref.read(settingsControllerProvider.notifier);

    final providerCtrl = useTextEditingController(text: state.provider);
    final modelCtrl = useTextEditingController(text: state.model);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: providerCtrl,
              decoration: const InputDecoration(
                labelText: 'Provider',
                border: OutlineInputBorder(),
              ),
              onChanged: controller.setProvider,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: modelCtrl,
              decoration: const InputDecoration(
                labelText: 'Model',
                border: OutlineInputBorder(),
              ),
              onChanged: controller.setModel,
            ),

            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () async {
                  await controller.setProvider(providerCtrl.text.trim());
                  await controller.setModel(modelCtrl.text.trim());
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Settings saved')),
                    );
                  }
                },
                child: const Text('Save'),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.network_check),
                onPressed: () async {
                  final messenger = ScaffoldMessenger.of(context);
                  // Minimal mock test; backend health could be called here
                  if (providerCtrl.text.isNotEmpty) {
                    messenger.showSnackBar(
                      const SnackBar(content: Text('Test: OK (mock)')),
                    );
                  } else {
                    messenger.showSnackBar(
                      const SnackBar(
                        content: Text('Test: Configure provider first'),
                      ),
                    );
                  }
                },
                label: const Text('Test connection'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
