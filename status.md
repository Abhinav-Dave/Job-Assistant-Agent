# Project status

**Last updated:** 2026-04-20

**Current phase:** Phase 5 — Scraper & PDF parser tools (PRD Section 21)

---

## Phases (PRD Section 21)

Complete Phase N before starting Phase N+1. Update this file and `Agent_Status.md` after each phase.

- [x] **Phase 1** — Repo scaffold (folder structure, env templates, status files)
- [x] **Phase 2** — Supabase + auth (backend): Python client, JWT middleware, protected routes, health + verification scripts. *Dashboard:* migrations, RLS, `resumes` bucket per [docs/setup-external-services.md](docs/setup-external-services.md) if not already applied. *Automated checks:* `cd backend` → `python verify_db.py` → `python verify_phase2.py` → `python -m pytest tests/ -v`.
- [x] **Phase 3** — Pydantic schemas + unit tests (`backend/schemas/*`, `backend/tests/unit/test_schemas.py`). *Check:* `python -m pytest backend/tests/unit/test_schemas.py -v`. *Deps:* `pydantic[email]` in `backend/requirements.txt` for `EmailStr`.
- [x] **Phase 4** — FastAPI routes (full mock data), structured logging, CORS, `GET /api/health` (DB + LLM ping), Pydantic response models, `JsonHttpError` for PRD-shaped 422s, `middleware/logging.py` → stdout + `backend/logs/app.log`
- [ ] **Phase 5** — Scraper & PDF parser tools
- [ ] **Phase 6** — Gemini LLM service
- [ ] **Phase 7** — Resume scorer agent
- [ ] **Phase 8** — Answer generator agent
- [ ] **Phase 9** — Autofill agent
- [ ] **Phase 10** — Frontend static UI with mock data
- [ ] **Phase 11** — Auth + frontend integration
- [ ] **Phase 12** — QA, polish & docs

---

## Notes

- **Phase 2 (backend) done:** `settings.py` loads `backend/.env` then repo root `.env`. `services/supabase.py`, `middleware/auth.py` (`verify_jwt`, `get_current_user`), all protected routes under `/api`, `verify_db.py` / `verify_phase2.py` for acceptance checks.
- **Phase 4 (backend) done:** Routers return PRD-shaped mocks with `response_model` from `schemas/`; `StructuredLoggingMiddleware` (JSON lines); `services/llm.check_llm_reachable()` for health when `GOOGLE_GEMINI_API_KEY` is set; `exceptions.JsonHttpError` for flat JSON errors on resume validation.

### Phase 4 verification issues and fixes (for future reference)

- **PowerShell `uvicorn` not found:** `uvicorn` command was not on PATH.  
  **Fix:** run `python -m uvicorn main:app --reload` from `backend/`.
- **Wrong directory (`backend/backend`) error:** running `cd backend` while already inside `backend`.  
  **Fix:** check prompt path first; run server directly if already in `...\backend`.
- **`/` returning `{"detail":"Not Found"}`:** no root route existed, only `/api/*`.  
  **Fix:** added `GET /` in `main.py` with links to `/docs`, `/openapi.json`, and `/api/health`.
- **401 in Swagger despite valid JWT:** `Authorization` header was not consistently sent from `/docs` with plain header dependency.  
  **Fix:** switched auth dependency to `HTTPBearer` in `middleware/auth.py` so `/docs` Authorize works correctly.
- **JWT confusion (`SUPABASE_ANON_KEY` vs Bearer token):** API keys were being treated like user JWTs.  
  **Fix:** documented distinction and added `backend/mint_dev_jwt.py` for local Bearer token generation.
- **`llm: error` in health + SDK warning:** health ping failed and `google.generativeai` showed deprecation warning.  
  **Fix:** default model changed to `gemini-2.5-flash` with `GEMINI_MODEL` override; warning is non-blocking for Phase 4 and migration to `google.genai` is tracked for Phase 6.
