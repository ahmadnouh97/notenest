// Supabase Postgres: notes (RLS enabled by user_id)
id UUID PK
user_id UUID
url TEXT
title TEXT
summary TEXT
tags TEXT          -- JSON string
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()

// Supabase Postgres: note_embeddings (RLS enabled)
note_id UUID PK REFERENCES notes(id) ON DELETE CASCADE
embedding VECTOR   -- pgvector
