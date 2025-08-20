# Supabase

This directory will hold SQL schema and migration scripts.

Files:
- `schema.sql` — main schema (extensions, table, trigger, indexes, RLS)
- `seed.sql` — optional seed records to quickly test

How to apply (Supabase SQL Editor):
1. Open your Supabase project → SQL Editor.
2. Paste the contents of `schema.sql` and run it. Ensure it completes without errors.
3. Optionally paste `seed.sql` to insert a few example notes.

Verify extensions:
- In Database → Extensions, confirm `vector` and `pg_trgm` show as Enabled.

Notes:
- `embedding` is `vector(1024)` to match bge-m3 embeddings.
- RLS is enabled with no policies; access is intended via backend service role only.


