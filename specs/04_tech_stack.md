## Tech Stack (Python backend)

### Frontend

- **FastAPI** + **Jinja2** templates (server-rendered)
- **HTMX** for progressive enhancement (minimal JS)
- **Tailwind CSS** for styling

### Backend (Python)

- **FastAPI** for REST endpoints: `summarize`, `rephrase`, `embed`, `chat`
- **Uvicorn** ASGI server
- **Supabase** (Postgres + Auth + Realtime) free tier
- **pgvector** extension for vector embeddings
- **OpenAI** Python SDK
- **python-dotenv** for environment configuration

### Storage

- **Supabase Postgres** with RLS; `note_embeddings` table storing vectors

### Search

- Local cosine similarity (fallback)
- Cloud vector similarity using Supabase `pgvector`

### Auth

- **Supabase Auth** (email/password, social)

### Tooling

- pytest, mypy, ruff

### Targets

- **Web** (PWA-ready)