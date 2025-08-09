export type SyncStatus = 'synced' | 'pending' | 'conflict';

export interface Note {
  id: string;
  url: string;
  title: string | null;
  summary: string | null;
  tags: string[]; // stored as JSON string in SQLite
  createdAt: string; // ISO 8601 UTC
  updatedAt: string; // ISO 8601 UTC
  syncStatus: SyncStatus;
  version: number;
  isDeleted: number; // 0 | 1
  deletedAt: string | null; // ISO 8601 UTC or null
}

export interface EmbeddingRow {
  noteId: string;
  vector: number[]; // stored as JSON string in SQLite
}


