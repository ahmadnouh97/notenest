// SQLite table: notes
id: number (PK)
url: string
title: string
summary: string
tags: string[]
created_at: string

// SQLite table: embeddings
note_id: number (FK -> notes.id)
vector: number[]  // JSON array of floats
