# AI Job Application Assistant

Production-grade AI co-pilot for job seekers: resume scoring, tailored answers, autofill preview, and application tracking. See [PRD + Status/PRD.md](PRD%20+%20Status/PRD.md) for full product and technical specification.

## Architecture overview

High-level diagrams and request flows: [docs/architecture.md](docs/architecture.md).

## Prerequisites

- **Node.js** (LTS) — for the Next.js frontend
- **Python 3.11+** — for the FastAPI backend
- **Supabase** account — PostgreSQL, Auth, Storage ([supabase.com](https://supabase.com))

## Repository layout

- `frontend/` — Next.js 14 (App Router), Tailwind, shadcn/ui (run `npx shadcn@latest init` in `frontend/` when ready)
- `backend/` — FastAPI, agents, tools, prompts
- `docs/` — architecture notes and API outline
- `supabase/migrations/` — SQL aligned with PRD Section 10 (run in Supabase SQL Editor or via CLI)

## How to run (after implementation)

**Frontend:** `cd frontend && npm install && npm run dev` → [http://localhost:3000](http://localhost:3000)

**Backend:** `cd backend && pip install -r requirements.txt` and configure `.env`, then `uvicorn main:app --reload --host 0.0.0.0 --port 8000` → [http://localhost:8000](http://localhost:8000)

Environment variables: copy [.env.example](.env.example) to `.env` (backend) and `frontend/.env.local` from [frontend/.env.local.example](frontend/.env.local.example). See PRD Section 27 for key descriptions.

## External services (accounts & API keys)

Step-by-step: [docs/setup-external-services.md](docs/setup-external-services.md) (Supabase, Gemini, optional Groq, env file mapping).

## Project status

Track progress in [status.md](status.md) and [Agent_Status.md](Agent_Status.md) (per PRD workflow).
