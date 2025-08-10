## notenest — Implementation Tasks (Flutter + FastAPI + Supabase)

This task list implements the plan in `PLAN.md`, using a Python FastAPI backend. Organized by milestones with checklists and acceptance criteria.

Note on hosting: keep the Flutter Web app on Vercel; deploy the FastAPI backend to a free-tier host (Render/Fly/Railway). Configure strict CORS allowlist so the web app can call the backend without CORS issues.

---

### M0 — Repo bootstrap and project scaffolding
- [x] Create mono-repo structure
  - `frontend/` (Flutter app)
  - `backend/` (FastAPI service)
  - `supabase/` (SQL schema, migration scripts)
  - `.gitignore`, `README.md`, `.env.example` at repo root
  - Acceptance: repo cloned fresh yields clear structure; `README` points to setup steps

- [x] Add `.env.example` with placeholders
  - `SUPABASE_DB_URL=postgresql://...` (Supabase database connection string)
  - `SUPABASE_REST_URL=https://<project>.supabase.co` (optional if using REST/RPC)
  - `SUPABASE_SERVICE_ROLE=...` (optional if using REST/RPC)
  - `ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app,http://localhost:5173,http://localhost:3000`
  - Optional: `EMBED_PROVIDER=hf` and `HF_API_KEY=...`
  - Acceptance: backend boots locally with `.env` copied from example

---

### M1 — Supabase setup (pgvector schema)
- [ ] Create `supabase/schema.sql` with the SQL from `PLAN.md` (extensions, table, trigger, indexes, RLS)
  - Acceptance: running in Supabase SQL editor completes without errors

- [ ] Validate pgvector and trigram extensions enabled in the Supabase project
  - Acceptance: `vector` and `pg_trgm` show as enabled in the dashboard

- [ ] Create a tiny seed script (optional) to insert 2–3 example notes (without embeddings)
  - Acceptance: records visible in `public.notes`

---

### M2 — Backend foundation (FastAPI)
- [ ] Scaffold FastAPI app in `backend/`
  - Files: `main.py`, `settings.py`, `db.py`, `models.py`, `routers/` directory
  - Dependencies (`backend/requirements.txt`):
    - `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `python-dotenv`
    - `asyncpg` (Postgres), `httpx` (HTTP client), `tenacity` (retries)
    - `sse-starlette` (SSE streaming), `beautifulsoup4` or `selectolax` (OG scraping)
    - `orjson` (fast JSON), `loguru` (logging, optional)
  - Acceptance: `uvicorn main:app --reload` starts locally

- [ ] Implement settings and secrets loading (`settings.py`)
  - Read `.env`; strongly type config (Supabase URL/key, allowed origins, optional embedding defaults)
  - Acceptance: invalid/missing env fails fast with clear error

- [ ] Database connection pool (`db.py`)
  - `asyncpg.create_pool()` using `SUPABASE_DB_URL` (Postgres connection string)
  - Ensure SSL enabled (`ssl=require`); connection tested on startup
  - Acceptance: startup connects; simple health query works

- [ ] CORS middleware
  - `fastapi.middleware.cors` with exact allowlist from `ALLOWED_ORIGINS`
  - Allow: `GET, POST, PUT, DELETE, OPTIONS`; headers: `Content-Type, Authorization`
  - Acceptance: preflight `OPTIONS` returns 204; origins restricted to allowlist

- [ ] Health endpoint
  - `GET /api/health` returns `{ ok: true, version }`
  - Acceptance: returns 200; included in CI smoke test

---

### M3 — Embedding and provider abstraction
- [ ] Define embedding interface (`services/embeddings.py`)
  - `get_embedding(text: str, provider: str|None, api_key: str|None) -> list[float]`
  - Support at least HF Inference API (BAAI bge-m3); pluggable for others
  - Normalize output vector (L2) server-side
  - Acceptance: unit tests cover English/Arabic text; vector length 1024; norm≈1.0

- [ ] Provider-agnostic chat client (`services/chat_providers.py`)
  - Map `{ provider, model, apiKey }` into an OpenAI-compatible POST request
  - Stream tokens (SSE or chunked) from provider → emit SSE to client
  - Acceptance: mock provider test streams tokens; no API key logged

- [ ] Rate limiting (simple)
  - In-memory per-IP token bucket to protect embedding/search/chat endpoints
  - Acceptance: exceeding limit returns 429 with `Retry-After`

---

### M4 — Notes CRUD endpoints
- [ ] Data models (`models.py`) and pydantic schemas (`schemas.py`)
  - Note: `id`, `url`, `title`, `description`, `tags: list[str]`, timestamps, `embedding`
  - Acceptance: validation errors return 422

- [ ] `POST /api/notes`
  - Input: `{ url, title?, description?, tags? }`
  - If title/description missing → call OG scraper; embed `title + "\n\n" + description`; insert row
  - Acceptance: returns created note; DB row has normalized `embedding`

- [ ] `GET /api/notes`
  - Query: `tags` (comma), `q` (keyword), `limit`, `offset`
  - Acceptance: tag filter uses AND (`@>`); keyword uses trigram; pagination works

- [ ] `PUT /api/notes/{id}`
  - If `title/description` changed → recompute embedding
  - Acceptance: `updated_at` changes; new embedding stored

- [ ] `DELETE /api/notes/{id}`
  - Acceptance: 200 `{ ok: true }`; row removed

- [ ] OG scraper `GET /api/og-scrape?url=...`
  - Parse `<title>`, `og:title`, `og:description`, meta description; sanitize text
  - Acceptance: returns best-effort fields for common sites

---

### M5 — Search and RAG chat
- [ ] `POST /api/search`
  - Body: `{ query, tags?, topK?, hybridWeight? }`
  - Compute query embedding; SQL orders by cosine distance with optional hybrid trigram boost
  - Acceptance: returns `[ { note, score } ]` ordered by relevance

- [ ] `POST /api/chat` (SSE)
  - Body: `{ messages, topK?, tags?, provider, model, apiKey? }`
  - Embed latest user message; retrieve topK notes; craft prompt with numbered citations
  - Stream tokens to client via `sse-starlette` `EventSourceResponse`
  - Acceptance: browser receives streaming tokens; final message includes citations metadata

---

### M6 — Flutter app (frontend)
- [ ] Scaffold Flutter project in `frontend/`
  - Add packages: `hooks_riverpod`, `go_router`, `dio`, `flutter_secure_storage`, `shared_preferences`, `receive_sharing_intent`, `url_launcher`, `intl`
  - Env config: `BACKEND_BASE_URL`
  - Acceptance: app builds for Android and Web locally

- [ ] App architecture
  - Create feature folders: `notes/`, `chat/`, `settings/`, `shared/`
  - Data models and API clients (with `dio` interceptors, timeouts, error mapping)
  - Acceptance: compile-time clean; basic navigation works

- [ ] Notes list & search
  - Search bar (debounced), tag chips (multi-select AND), list with title/domain/tags
  - Swipe to delete; tap to edit
  - Acceptance: list reflects CRUD ops; search + tags filter correctly

- [ ] Add/Edit note screen (`/add`)
  - Fields: url, title, description, tags (create-on-type)
  - Prefill from share target (web query params and Android intent)
  - Acceptance: create/update triggers backend embedding; UI shows results

- [ ] Chat screen
  - Provider/model selector; API key stored locally; stream rendering with citations
  - Acceptance: can switch providers/models; streaming stable; citation chips open note

- [ ] Settings screen
  - Enter and locally persist provider, apiKey, model; test connection button
  - Acceptance: saved across sessions; never uploaded to backend

---

### M7 — Share-to-app (Android) and Web PWA Share Target
- [ ] Android: intent filter in `AndroidManifest.xml` for `SEND text/plain`
  - Integrate `receive_sharing_intent` to capture URL/text → navigate to `/add?url=...`
  - Acceptance: sharing from Chrome/Twitter/etc. opens add screen with prefilled URL

- [ ] Web: PWA share target in `web/manifest.json`
  - Add share target mapping `{ title, text, url }` to `/add`
  - Acceptance: sharing in Chrome desktop/mobile opens PWA `/add` with fields prefilled

---

### M8 — Deployment, CORS, and CI
- [ ] Deploy backend (FastAPI) to free-tier host (Render recommended)
  - Configure `PYTHON_VERSION`, `START_CMD="uvicorn main:app --host 0.0.0.0 --port 10000"`
  - Set env vars; add health check; enable auto-deploy on push
  - Acceptance: backend public URL reachable; SSE stable on chat endpoint

- [ ] Deploy Flutter Web to Vercel
  - Build `flutter build web --release`; set Vercel output to `frontend/build/web`
  - Rewrites for SPA routes (`/add`, `/chat`)
  - Acceptance: web app live; connects to backend without CORS issues

- [ ] Configure CORS allowlist
  - Add Vercel production and preview domains to `ALLOWED_ORIGINS`
  - Acceptance: preflight passes; blocked from non-allowed origins

- [ ] CI (GitHub Actions)
  - Backend: lint, type-check (optional `ruff`, `mypy`), test, build
  - Frontend: flutter format/analyze, web build artifact
  - Acceptance: CI green on main branch; preview deploys on PRs

---

### M9 — Testing and quality
- [ ] Backend unit tests (`pytest`)
  - Embedding normalizer; provider adapters; OG scraper; CORS handler
  - Acceptance: >80% coverage on services; no secrets in logs

- [ ] Backend integration tests
  - Use `httpx.AsyncClient` against running app; seed temporary notes; validate CRUD/search/chat
  - Acceptance: all endpoints pass; SSE parsing verified

- [ ] Flutter tests
  - Unit: view models/providers; validators
  - Widget: notes list, add/edit, tag chips, chat streaming UI
  - Acceptance: green test run locally and in CI

- [ ] Performance checks
  - Tune `ivfflat.probes` and `lists`; measure p95 latency for search and topK=8 retrieval
  - Acceptance: search < 300ms (warm), chat retrieval < 400ms (warm) on free tier (approximate)

---

### Implementation details per endpoint (reference)
- Notes SQL inserts/updates must maintain normalized `embedding` (L2 norm ≈ 1.0)
- Search ordering combines cosine score and trigram similarity (hybrid, weight default 0.8)
- Tag filtering uses `tags @> '{...}'` (AND semantics)
- Chat prompt: include numbered snippets and URLs; instruct model to cite as `[n]`
- Never persist or log user-supplied provider API keys

---

### Optional enhancements
- [ ] Backfill job to compute embeddings for legacy rows with `embedding is null`
- [ ] CSV import/export of notes
- [ ] Offline caching for the app (Web: service worker tweaks; Android: local cache)
- [ ] Dark mode polish and empty states

---

### Definition of Done (overall)
- All milestones complete; CI green; web app live on Vercel; backend live (Render/Fly/Railway)
- CRUD + search + chat function on Android and Web; share-to-app works on both
- CORS strictly enforced; secrets in `.env` only; no sensitive logs


