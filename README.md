# AI Job Application Assistant

Production-ready MVP for AI-assisted job applications:

- Next.js control plane (auth, profile, tracker, mapping preview)
- FastAPI backend (agents, APIs, scoring, persistence)
- Supabase (Auth + Postgres + RLS)
- Browser extension bridge for in-tab autofill execution

Architecture reference:

- [docs/architecture.md](docs/architecture.md)

## Prerequisites

- Node.js LTS
- Python 3.11+
- Supabase project (database + auth configured)

## Repo Layout

- `frontend/` - Next.js 14 App Router control plane
- `backend/` - FastAPI API + agents + tests
- `extension/` - Chrome MV3 extension bridge
- `supabase/migrations/` - SQL migrations
- `docs/` - project architecture docs

## Local Setup

### 1) Install dependencies

Frontend:

`cd frontend && npm install`

Backend:

`cd backend && pip install -r requirements.txt`

### 2) Configure environment variables

Backend:

- Copy `.env.example` -> `.env` (repo root or `backend/.env`)
- Required keys for full functionality:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_JWT_SECRET`
  - `GOOGLE_GEMINI_API_KEY`
- Optional:
  - `GROQ_API_KEY`
  - `GEMINI_MODEL`
  - `GEMINI_MODEL_FALLBACK`
  - `LLM_TIMEOUT_SECONDS`
  - `ANSWER_MAX_WORDS`

Frontend:

- Copy `frontend/.env.local.example` -> `frontend/.env.local`
- Required:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_API_URL` (usually `http://127.0.0.1:8000`)

### 3) Apply Supabase migrations

Run all SQL files in `supabase/migrations/` (SQL editor or Supabase CLI), including `008_application_score_reports.sql`.

### 4) Start services

Backend:

`cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`

Frontend:

`cd frontend && npm run dev`

Open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Extension Install and Use

1. Open `chrome://extensions`
2. Enable Developer mode
3. Load unpacked extension from `extension/`
4. In app (`localhost:3000`), log in and run mapping preview at least once
5. Open target application page and click **Execute fill in browser tab** from extension popup

If needed, set the web app origin in extension options (`http://localhost:3000` by default).

## Troubleshooting

- **Backend unreachable in frontend**
  - Confirm `NEXT_PUBLIC_API_URL` points to backend (`127.0.0.1:8000`)
  - Confirm backend health: `GET /api/health`
- **`/api/users/me` returns 401**
  - Session token may be stale; sign out and sign in again
- **Autofill returns `jd_scrape_failed` or `ats_page_not_ready`**
  - Many ATS pages block scraping without full page/session state; paste JD text or proceed on page first
- **Extension says bridge context missing**
  - Keep dashboard tab open and logged in, refresh it, then retry popup action
- **Gemini transient failures (`503`)**
  - Retry request; keep Groq fallback key configured for resilience

## Known Limitations

- Some ATS flows are heavily dynamic and may require manual progression before useful fields become fillable
- Mapping quality can vary by custom employer form semantics
- Extension execution depends on current tab/session state and available editable controls

