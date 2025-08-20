export const CREATE_TABLE_NOTES = `
CREATE TABLE IF NOT EXISTS notes (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  tags TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  sync_status TEXT DEFAULT 'synced',
  version INTEGER DEFAULT 1,
  is_deleted INTEGER DEFAULT 0,
  deleted_at TEXT
);
`;

export const CREATE_TABLE_EMBEDDINGS = `
CREATE TABLE IF NOT EXISTS embeddings (
  note_id TEXT PRIMARY KEY,
  vector TEXT NOT NULL,
  FOREIGN KEY (note_id) REFERENCES notes(id)
);
`;

export const CREATE_INDEXES = `
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);
`;


