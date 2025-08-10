# notenest

Monorepo for a notes + search + chat app.

## Structure
- `frontend/` — Flutter app (Android + Web PWA). Will be scaffolded in later milestones.
- `backend/` — FastAPI service.
- `supabase/` — SQL schema and migration scripts.

## Quickstart: Backend (FastAPI)
1) Copy environment template and edit values as needed:

```bash
cp .env.example .env
```

2) Create a virtualenv (Python 3.11+ recommended) and install dependencies:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

3) Run the dev server from the repo root:

```bash
uvicorn backend.main:app --reload --port 8000
```

4) Verify health:

```bash
curl http://localhost:8000/api/health
```

If you need to change allowed origins for CORS, edit `ALLOWED_ORIGINS` in your `.env` (comma-separated list).

## Environment
Variables are loaded from a root `.env` file. See `.env.example` for placeholders:
- `SUPABASE_DB_URL=postgresql://...`
- `SUPABASE_REST_URL=https://<project>.supabase.co`
- `SUPABASE_SERVICE_ROLE=...`
- `ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app,http://localhost:5173,http://localhost:3000`
- Optional embeddings: `EMBED_PROVIDER=hf`, `HF_API_KEY=...`

## Next milestones
- M1: Supabase schema and indexes in `supabase/schema.sql`.
- M2: Backend foundation (settings, DB pool, CORS, health, etc.).
- M6: Flutter app scaffold and features.


