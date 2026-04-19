# External services setup (before Phase 2)

Use this checklist so credentials land in the right files. **Never commit real values**—only `.env.example` is in git.

| Service | What it’s for | Where keys go |
|--------|----------------|----------------|
| **Supabase** | PostgreSQL, Auth, Storage | Backend `.env` + `frontend/.env.local` (public URL + anon key only on frontend) |
| **Google AI (Gemini)** | Resume / answers / autofill LLM | Backend `.env` only |
| **Groq** (optional) | LLM fallback if Gemini rate-limits | Backend `.env` only |

---

## 1. Supabase

1. Go to [https://supabase.com](https://supabase.com) → sign in → **New project**.
2. Choose org, **name** the project, set a **database password** (save it somewhere safe—you rarely need it if you use the dashboard).
3. Wait until the project is **healthy**.

### Get API values (Dashboard)

**Settings → API**

- **Project URL** → `SUPABASE_URL` (backend) and `NEXT_PUBLIC_SUPABASE_URL` (frontend).
- **anon public** key → `SUPABASE_ANON_KEY` (backend) and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (frontend). Same anon key value in both apps.
- **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` (backend only; server-side; never in Next public env).

**Settings → API → JWT Settings**

- **JWT Secret** → `SUPABASE_JWT_SECRET` (backend only; used by FastAPI to verify user JWTs).

### Database schema

In **SQL Editor**, run the files in [`supabase/migrations/`](../supabase/migrations/) **in order** (`001` → `006`), or paste from [PRD + Status/PRD.md](../PRD%20+%20Status/PRD.md) Section 10.

### Storage

**Storage → New bucket** → name: `resumes` → **Private** (PRD Section 10).

### Local env files

Copy from repo [`.env.example`](../.env.example):

- **Backend:** create `backend/.env` (or a single root `.env` if you prefer—keep one convention). Fill:
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- **Frontend:** copy [`frontend/.env.local.example`](../frontend/.env.local.example) to `frontend/.env.local`. Fill:
  - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` (e.g. `http://localhost:8000`)

---

## 2. Google Gemini (Gemini API key)

1. Open [Google AI Studio](https://aistudio.google.com) (or Google Cloud console if you use Vertex—PRD assumes AI Studio key).
2. **Get API Key** → create a key for this project.
3. Put it only in **backend** `.env`:

```bash
GOOGLE_GEMINI_API_KEY=your-key-here
```

Do **not** put this in `NEXT_PUBLIC_*` (never expose LLM keys to the browser).

---

## 3. Groq (optional fallback)

1. [https://console.groq.com](https://console.groq.com) → API Keys → create key.
2. Backend `.env` only:

```bash
GROQ_API_KEY=your-key-here
```

---

## Quick copy-paste map

| Variable | File |
|----------|------|
| `SUPABASE_URL` | `backend/.env` |
| `SUPABASE_ANON_KEY` | `backend/.env` |
| `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env` |
| `SUPABASE_JWT_SECRET` | `backend/.env` |
| `GOOGLE_GEMINI_API_KEY` | `backend/.env` |
| `GROQ_API_KEY` | `backend/.env` |
| `ENVIRONMENT`, `LOG_LEVEL` | `backend/.env` |
| `NEXT_PUBLIC_SUPABASE_URL` | `frontend/.env.local` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `frontend/.env.local` |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` |

After filling secrets, confirm `.env` and `.env.local` are **gitignored** (they are in this repo’s `.gitignore`).
