## notenest – Detailed Build Plan

### Requirements snapshot (agreed)
- **Platforms**: Flutter (Android + Web PWA)
- **Hosting**: Web and backend on Vercel
- **Auth**: Single-user app (no login)
- **Database**: Supabase Postgres + pgvector (you already created the project)
- **Features**: Notes CRUD; tags; semantic+keyword search; chat with notes (RAG); Android share-to-app; Web PWA Share Target; multilingual (EN/AR/TR)
- **Providers**:
  - Embeddings via backend proxy (free-tier friendly, CORS-safe)
  - Chat via backend proxy with dynamic provider/model/key (OpenRouter/OpenAI/etc.)
- **Note fields**: `url`, `title`, `description`, `tags`, `created_at`, `updated_at`, `embedding`

---

## Architecture overview
- **Flutter app** (Android + Web PWA): UI, local settings, share-target entry, calls backend.
- **Backend** on Vercel (serverless Node runtimes):
  - Notes CRUD
  - Semantic search (pgvector) and optional hybrid keyword search
  - Embedding proxy (server-side fetch to chosen embedding provider)
  - Chat proxy with retrieval-augmented generation (provider-agnostic; streams)
  - OG metadata scraper (title/description)
- **Database**: Supabase Postgres with `vector` + `pg_trgm` extensions, RLS enabled (no public policies; only service role key used server-side).

Key principles
- Client never talks directly to Supabase; only backend uses the service role key.
- All third-party API requests are proxied server-side to avoid CORS and key exposure.
- Embeddings are L2-normalized server-side before insert/search.

---

## Supabase schema and indexes

Run in Supabase SQL editor (adjust schema name if needed):

```sql
-- Extensions
create extension if not exists pgcrypto; -- for gen_random_uuid()
create extension if not exists vector;   -- pgvector
create extension if not exists pg_trgm;  -- trigram for keyword fallback

-- Table
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
-- For ivfflat, run analyze after populating to optimize lists.
create index if not exists notes_embedding_ivfflat
  on public.notes using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create index if not exists notes_tags_gin on public.notes using gin (tags);

create index if not exists notes_text_trgm
  on public.notes using gin ((coalesce(title,'') || ' ' || coalesce(description,'')) gin_trgm_ops);

-- RLS (enabled; no policies so only service role can access)
alter table public.notes enable row level security;
```

---

## Backend (Vercel) – endpoints, contracts, and behavior

### Environment variables (Vercel Project Settings)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE` (server only; never exposed)
- `ALLOWED_ORIGINS` (comma-separated; e.g., `https://notenest.vercel.app,capacitor://localhost,http://localhost:3000`)
- Optional embedding defaults: `EMBED_PROVIDER`, `HF_API_KEY` (or other provider key)

### CORS policy
- Allow: `GET, POST, PUT, DELETE, OPTIONS` and `Content-Type, Authorization`
- `Access-Control-Allow-Origin`: exact match(s) from `ALLOWED_ORIGINS` (no `*` when credentials)
- Handle preflight `OPTIONS` early and return 204

### Embedding normalization
- Normalize vectors server-side: `v_norm = v / max(1e-12, l2_norm(v))`
- Store normalized vectors; use cosine distance (`<=>`) for search

### Endpoints
- `POST /api/notes`
  - In: `{ url: string, title?: string, description?: string, tags?: string[] }`
  - Behavior: if title/description missing → scrape OG metadata; compute embedding from `title + "\n\n" + description`; normalize; insert row.
  - Out: `{ note }`

- `GET /api/notes?tags=a,b&limit=50&offset=0&q=term`
  - Filters: tags (AND via `@>`), optional keyword `q` (trigram on title+description)
  - Out: `{ notes, total }`

- `PUT /api/notes/:id`
  - In: any subset of `{ url, title, description, tags }`
  - Behavior: if description/title changed → recompute embedding; update row
  - Out: `{ note }`

- `DELETE /api/notes/:id`
  - Out: `{ ok: true }`

- `POST /api/search`
  - In: `{ query: string, tags?: string[], topK?: number, hybridWeight?: number }`
  - Behavior: embed query; SQL orders by cosine distance; optional hybrid with trigram similarity
  - Out: `{ results: [ { note, score } ] }`

- `POST /api/chat` (SSE streaming)
  - In: `{ messages: [{role, content}], topK?: number, tags?: string[], provider: string, model: string, apiKey?: string }`
  - Behavior: embed latest user message; retrieve topK notes; build prompt with citations; call selected provider via proxy; stream back tokens; do not persist apiKey
  - Out: `text/event-stream` with tokens; final message includes citations metadata

- `GET /api/og-scrape?url=...`
  - Out: `{ title, description }` (best-effort from `<title>`, `og:` and meta tags)

### Search SQL core (cosine + optional hybrid)
```sql
set ivfflat.probes = 10; -- tune 1..100 for recall/latency tradeoff

-- Assume :query_embedding is a 1024-d vector and :query_text is the raw query
select id, url, title, description, tags, created_at, updated_at,
       (1 - (embedding <=> :query_embedding)) as cosine_score
from public.notes
where embedding is not null
  and (:tags_is_null or tags @> :tags_array)
order by (
  coalesce(:hybrid_weight, 0.8) * (1 - (embedding <=> :query_embedding))
  + (1 - coalesce(:hybrid_weight, 0.8)) * similarity(title || ' ' || description, :query_text)
) desc
limit :top_k;
```

---

## Embeddings strategy (multilingual)
- Default model: **BAAI bge-m3** (multilingual; 1024 dims), good for EN/AR/TR.
- Invocation: backend-only; supports either a per-request `apiKey` or a fallback server key.
- Normalization: always L2-normalize before storage/search.
- Rate limits: implement simple in-memory throttling per IP on the backend.

---

## Chat/RAG strategy (provider-agnostic)
- Retrieve top K notes using the latest user message embedding (respect tags if provided).
- Prompt scaffold includes a short system message and a context section with numbered note snippets and URLs; instruct the model to cite as `[n]`.
- Provider mapping: request shape is unified; backend maps to OpenRouter/OpenAI/etc.; streams via SSE.
- Keys: provided by the client per request; never stored or logged.

---

## Flutter app

### Packages
- State: `riverpod` or `hooks_riverpod`
- Routing: `go_router`
- HTTP: `dio`
- Storage: `flutter_secure_storage` (Android); `shared_preferences`/`localStorage` fallback for Web
- Share: `receive_sharing_intent` (Android), `share_plus` (optional)
- PWA: default Flutter web; custom `web/manifest.json` for share target
- Utilities: `url_launcher`, `intl`, `collection`

### Routes
- `/` NotesListScreen
- `/add` AddOrEditNoteScreen (also used by share target: prefill from query params)
- `/chat` ChatScreen
- `/settings` ProviderKeyAndModelScreen

### Notes UX
- Search bar (debounced) combining semantic + keyword
- Tag chips (multi-select AND)
- List with title/domain/tags; swipe to delete; tap to edit
- FAB to add; form: `url`, `title`, `description`, `tags` (create-on-type)

### Chat UX
- Provider/model selector; API key stored locally on device/browser
- Messages with streaming output and citation chips linking to notes
- Optional tag filter applied to retrieval

### Settings
- Enter provider, API key, model; test-connection button
- Keys never sent to storage—only used to sign proxied calls per request

---

## Android: share-to-app and deep links
- `AndroidManifest.xml` intent filter for share:
```xml
<intent-filter>
  <action android:name="android.intent.action.SEND" />
  <category android:name="android.intent.category.DEFAULT" />
  <data android:mimeType="text/plain" />
  <!-- Optionally support SEND_MULTIPLE for multiple URLs/text -->
  <!-- <action android:name="android.intent.action.SEND_MULTIPLE" /> -->
  <!-- <data android:mimeType="text/*" /> -->
  <!-- <data android:mimeType="text/uri-list" /> -->
  <!-- Additional categories/actions can be added as needed -->
  
</intent-filter>
```
- Use `receive_sharing_intent` to capture shared text/URL and navigate to `/add?url=...`.
- Optional custom scheme: `notenest://add?url=...`.

---

## Web PWA share target
Add to `web/manifest.json`:
```json
{
  "share_target": {
    "action": "/add",
    "method": "GET",
    "params": { "title": "title", "text": "text", "url": "url" }
  }
}
```
Flutter route `/add` reads query params to prefill the form.

---

## Deployment and CI/CD (Vercel)
- Monorepo-friendly setup with two outputs:
  - Backend functions under `api/*`
  - Flutter Web build output served as static: `build/web`
- Build
  - Install Flutter in CI (or use a prebuilt image), then: `flutter build web --release`
  - Configure Vercel project to use `build/web` as the output directory for the web app
  - SPA rewrites to `index.html` for routes like `/add`, `/chat`
- Environment variables set in Vercel (Production/Preview/Development as needed)

---

## Testing strategy
- Backend
  - Unit: CORS handler; provider mappers; embedding normalizer; OG scraper
  - Integration: seed Supabase fixtures; CRUD; search scoring; chat retrieval; SSE streaming stability
- App
  - Unit: view models/providers; input validators
  - Widget: notes list interactions; add/edit form; tag filters; chat streaming rendering
  - Integration: Android share intent (emulator); Chrome PWA share target
- Performance
  - Tune `ivfflat.probes` and `lists`; measure p95 latency for search and chat retrieval

---

## Milestones
- **M0 – Repo bootstrap**: Flutter app scaffold; Vercel project; repo structure; `.env.example` and README
- **M1 – Supabase**: apply schema; verify extensions; create indexes
- **M2 – Backend core**: notes CRUD; embeddings proxy; search endpoint; CORS
- **M3 – Notes UI**: add/edit/delete; tag filters; combined search
- **M4 – Share flows**: Android intent + PWA share target; `/add` prefill
- **M5 – Chat (RAG)**: provider switch; SSE streaming; citations
- **M6 – Polish**: OG scrape; settings; empty states; error handling; i18n-ready strings
- **M7 – Tests & Deploy**: end-to-end tests; Vercel production release

---

## API shapes (concise reference)
- `POST /api/notes`
  - In: `{ url, title?, description?, tags? }`
  - Out: `{ note }`
- `GET /api/notes?tags=a,b&limit=50&offset=0&q=term`
  - Out: `{ notes, total }`
- `PUT /api/notes/:id` / `DELETE /api/notes/:id`
- `POST /api/search`
  - In: `{ query, tags?, topK?, hybridWeight? }`
  - Out: `{ results: [ { note, score } ] }`
- `POST /api/chat`
  - In: `{ messages, topK?, tags?, provider, model, apiKey? }`
  - Out: SSE `text/event-stream` (final payload includes citations)

---

## Security and CORS notes
- Origin allowlist via `ALLOWED_ORIGINS` (no wildcard); handle preflight requests.
- Service role key used only server-side; client cannot reach Supabase directly.
- Do not log provider API keys; reject empty/invalid keys gracefully.
- Single-user assumption: there is no auth—security relies on origin allowlisting and unguessable backend URLs. If exposure risk rises in the future, add a lightweight shared secret header.

---

## Next actions
1) Initialize repo structure (Flutter app + `api/` functions directory).
2) Apply Supabase SQL above; verify `vector` and `pg_trgm`.
3) Implement backend: CORS middleware, embedding proxy, CRUD, search, chat (SSE), OG scraper.
4) Implement Flutter notes UI + search + tags.
5) Implement share-to-app (Android) and PWA share target (Web).
6) Wire chat tab with provider switch and streaming.
7) Tests, tuning, deploy to Vercel.


