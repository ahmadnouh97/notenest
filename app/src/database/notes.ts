import { getDatabase } from './index';
import { Note } from '../types/note';

function nowIso(): string {
  return new Date().toISOString();
}

export async function upsertNote(note: Partial<Note> & Pick<Note, 'id' | 'url'>): Promise<void> {
  const db = await getDatabase();
  const createdAt = note.createdAt ?? nowIso();
  const updatedAt = nowIso();
  const title = note.title ?? null;
  const summary = note.summary ?? null;
  const tagsJson = JSON.stringify(note.tags ?? []);
  const syncStatus = note.syncStatus ?? 'pending';
  const version = note.version ?? 1;
  const isDeleted = note.isDeleted ?? 0;
  const deletedAt = note.deletedAt ?? null;

  await db.runAsync(
    `INSERT INTO notes (id, url, title, summary, tags, created_at, updated_at, sync_status, version, is_deleted, deleted_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       url=excluded.url,
       title=excluded.title,
       summary=excluded.summary,
       tags=excluded.tags,
       updated_at=excluded.updated_at,
       sync_status=excluded.sync_status,
       version=excluded.version,
       is_deleted=excluded.is_deleted,
       deleted_at=excluded.deleted_at
    `,
    [
      note.id,
      note.url,
      title,
      summary,
      tagsJson,
      createdAt,
      updatedAt,
      syncStatus,
      version,
      isDeleted,
      deletedAt,
    ]
  );
}

export async function listNotes(): Promise<Note[]> {
  const db = await getDatabase();
  const rows = await db.getAllAsync<{
    id: string;
    url: string;
    title: string | null;
    summary: string | null;
    tags: string;
    created_at: string;
    updated_at: string;
    sync_status: string;
    version: number;
    is_deleted: number;
    deleted_at: string | null;
  }>(`SELECT * FROM notes WHERE is_deleted = 0 ORDER BY updated_at DESC`);
  return rows.map((r) => ({
    id: r.id,
    url: r.url,
    title: r.title,
    summary: r.summary,
    tags: JSON.parse(r.tags || '[]'),
    createdAt: r.created_at,
    updatedAt: r.updated_at,
    syncStatus: (r.sync_status as Note['syncStatus']) ?? 'synced',
    version: r.version,
    isDeleted: r.is_deleted,
    deletedAt: r.deleted_at,
  }));
}


