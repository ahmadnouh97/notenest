-- notenest Supabase schema (M1)
-- Run this file in the Supabase SQL editor.

-- Extensions
create extension if not exists pgcrypto; -- for gen_random_uuid()
create extension if not exists vector;   -- pgvector
create extension if not exists pg_trgm;  -- trigram for keyword fallback

-- Notes table
create table if not exists public.notes (
  id uuid primary key default gen_random_uuid(),
  url text not null,
  title text not null,
  description text not null,
  tags text[] not null default '{}',
  embedding vector(1024), -- bge-m3 default dimension
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- updated_at trigger
create or replace function public.set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_set_updated_at on public.notes;
create trigger trg_set_updated_at
before update on public.notes
for each row execute function public.set_updated_at();

-- Indexes
-- For ivfflat, consider running ANALYZE after populating the table to optimize lists.
create index if not exists notes_embedding_ivfflat
  on public.notes using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create index if not exists notes_tags_gin on public.notes using gin (tags);

create index if not exists notes_text_trgm
  on public.notes using gin ((coalesce(title,'') || ' ' || coalesce(description,'')) gin_trgm_ops);

-- RLS (enabled; no policies so only service role can access)
alter table public.notes enable row level security;


