import { getDatabase } from './index';
import { EmbeddingRow } from '../types/note';

export async function upsertEmbedding(noteId: string, vector: number[]): Promise<void> {
  const db = await getDatabase();
  await db.runAsync(
    `INSERT INTO embeddings (note_id, vector) VALUES (?, ?)
     ON CONFLICT(note_id) DO UPDATE SET vector=excluded.vector`,
    [noteId, JSON.stringify(vector)]
  );
}

export async function getEmbedding(noteId: string): Promise<EmbeddingRow | null> {
  const db = await getDatabase();
  const row = await db.getFirstAsync<{ note_id: string; vector: string }>(
    `SELECT * FROM embeddings WHERE note_id = ?`,
    [noteId]
  );
  if (!row) return null;
  return { noteId: row.note_id, vector: JSON.parse(row.vector || '[]') };
}


