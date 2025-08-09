import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, Button, ScrollView } from 'react-native';
import { useEffect, useState } from 'react';
import { getDatabase } from './src/database';
import { listNotes, upsertNote } from './src/database/notes';
import { uuidv4 } from './src/utils/uuid';

export default function App() {
  const [ready, setReady] = useState(false);
  const [notes, setNotes] = useState<Array<{ id: string; title: string | null; url: string }>>([]);

  useEffect(() => {
    (async () => {
      await getDatabase();
      const n = await listNotes();
      setNotes(n.map((x) => ({ id: x.id, title: x.title, url: x.url })));
      setReady(true);
    })();
  }, []);

  const addSampleNote = async () => {
    const id = uuidv4();
    await upsertNote({ id, url: 'https://example.com', title: 'Example', tags: [] });
    const n = await listNotes();
    setNotes(n.map((x) => ({ id: x.id, title: x.title, url: x.url })));
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>NoteNest</Text>
      <Button title="Add sample note" onPress={addSampleNote} />
      <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
        {notes.map((n) => (
          <View key={n.id} style={styles.card}>
            <Text style={styles.cardTitle}>{n.title ?? '(Untitled)'}</Text>
            <Text style={styles.cardUrl}>{n.url}</Text>
          </View>
        ))}
      </ScrollView>
      <StatusBar style="auto" />
      {!ready && <Text>Initializing database…</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 22,
    marginBottom: 12,
  },
  list: {
    alignSelf: 'stretch',
    paddingHorizontal: 16,
    marginTop: 12,
  },
  listContent: {
    paddingBottom: 40,
  },
  card: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
  },
  cardTitle: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  cardUrl: {
    color: '#555',
  },
});
