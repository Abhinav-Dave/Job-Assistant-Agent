# Project status

**Last updated:** 2026-04-20

**Current phase:** Phase 9 — Autofill agent (PRD Section 21)

**API notes:**
- **`POST /api/resume/analyze`** is wired to the real `agents.resume_scorer.analyze_resume_and_jd` (PDF or text/Markdown upload or pasted `resume_text`, plus `jd_url` and/or `jd_text`). It is no longer a fixed mock score.
- **`POST /api/generate/answer`** expects JSON body **`AnswerRequest`**: required **`question`**; at least one of **`jd_text`** / **`jd_url`**; optional **`profile`** (`UserProfile` nested **inside** `profile`, not at root). Omit `profile` to use the server mock profile. Do not use OpenAPI placeholder **`"string"`** for URLs or dates — use real values or JSON **`null`**.

---

## Phases (PRD Section 21)

Complete Phase N before starting Phase N+1. Update this file and `Agent_Status.md` after each phase.

- [x] **Phase 1** — Repo scaffold (folder structure, env templates, status files)
- [x] **Phase 2** — Supabase + auth (backend): Python client, JWT middleware, protected routes, health + verification scripts. *Dashboard:* migrations, RLS, `resumes` bucket per [docs/setup-external-services.md](docs/setup-external-services.md) if not already applied. *Automated checks:* `cd backend` → `python verify_db.py` → `python verify_phase2.py` → `python -m pytest tests/ -v`.
- [x] **Phase 3** — Pydantic schemas + unit tests (`backend/schemas/*`, `backend/tests/unit/test_schemas.py`). *Check:* `python -m pytest backend/tests/unit/test_schemas.py -v`. *Deps:* `pydantic[email]` in `backend/requirements.txt` for `EmailStr`.
- [x] **Phase 4** — FastAPI routes (full mock data), structured logging, CORS, `GET /api/health` (DB + LLM ping), Pydantic response models, `JsonHttpError` for PRD-shaped 422s, `middleware/logging.py` → stdout + `backend/logs/app.log`
- [x] **Phase 5** — Scraper & PDF parser tools
- [x] **Phase 6** — Gemini LLM service
- [x] **Phase 7** — Resume scorer agent
- [x] **Phase 8** — Answer generator agent
- [ ] **Phase 9** — Autofill agent
- [ ] **Phase 10** — Frontend static UI with mock data
- [ ] **Phase 11** — Auth + frontend integration
- [ ] **Phase 12** — QA, polish & docs

---

## Notes

- **Phase 2 (backend) done:** `settings.py` loads `backend/.env` then repo root `.env`. `services/supabase.py`, `middleware/auth.py` (`verify_jwt`, `get_current_user`), all protected routes under `/api`, `verify_db.py` / `verify_phase2.py` for acceptance checks.
- **Phase 4 (backend) done:** Routers return PRD-shaped mocks with `response_model` from `schemas/`; `StructuredLoggingMiddleware` (JSON lines); `services/llm.check_llm_reachable()` for health when `GOOGLE_GEMINI_API_KEY` is set; `exceptions.JsonHttpError` for flat JSON errors on resume validation.
- **Phase 5 (backend tools) done:** Implemented `tools/scraper.py` (`scrape_job_description`, `scrape_form_fields`) with `httpx` + `BeautifulSoup` (selector fallbacks, cleaned text, graceful failures, normalized `FormField` output) and `tools/pdf_parser.py` (`extract_text_from_pdf`) with `PyMuPDF` handling empty/scanned/invalid PDFs safely. Added deterministic unit tests in `tests/unit/test_scraper.py` and `tests/unit/test_pdf_parser.py`; verification command passed: `python -m pytest backend/tests/unit/test_scraper.py backend/tests/unit/test_pdf_parser.py -v`.
- **Phase 6 (backend llm service) done:** Implemented `services/llm.py` production-ready helpers for `load_prompt`, `call_gemini`, optional `call_groq`, and `parse_json_from_response`, including structured errors (`LLMError`, `JSONParseError`, `PromptLoadError`), safe prompt-path loading, timeout/model env handling (`GEMINI_MODEL`, `LLM_TIMEOUT_SECONDS`), and graceful health integration via `check_llm_reachable()`. Added unit tests in `tests/unit/test_llm_service.py`; verification command passed: `python -m pytest backend/tests/unit/test_llm_service.py backend/tests/unit/test_schemas.py -v`.
- **Phase 7 (resume scorer agent) done:** Implemented `agents/resume_scorer.py` full PRD flow for `analyze_resume_and_jd(resume_source, jd_source, user_id)` with source resolution (PDF/text + URL/text), expected structured agent failures (`pdf_no_text`, `jd_scrape_failed`, `resume_too_short`, `jd_too_short`), input truncation guards, prompt loading via `resume_score_v1.txt`, Gemini invocation, JSON parsing + `ResumeScoreResult` validation, and one retry using a correction prompt on JSON/schema failure. Added logging hooks (agent_name, user_id, duration_ms, score, token placeholders, success/failure) and targeted unit tests in `tests/unit/test_resume_scorer.py`; verification command passed: `python -m pytest backend/tests/unit/test_resume_scorer.py -v`.
- **Resume analyze route:** `backend/routers/resume.py` calls the scorer agent (not mock data). Uploads: `.pdf` or magic bytes `%PDF` → PDF extraction; other files (e.g. `.md`, `.txt`) → UTF-8/Latin-1 text. If both `jd_url` and `jd_text` are sent, **URL is used** (scraped JD). Requires auth (`Authorization: Bearer`); use `python backend/mint_dev_jwt.py` locally.
- **Phase 8 (answer generator) — reliability & length (see `Agent_Status.md` for full issue log):** `generate_tailored_answer` uses Gemini first, Groq second, deterministic fallback only on serious LLM outage codes. Word limits: default max **300** (`ANSWER_MAX_WORDS` env override); optional **“N words”** in the question adjusts min/max. Regeneration retries for `answer_too_short`, `answer_too_long`, and quality failures. `LAST_PROVIDER_USED` / `LAST_WORD_LIMIT_MAX` and log field `llm_provider` record which backend succeeded. Prompt `answer_gen_v1.txt` targets 220–280 words. `call_gemini(..., expect_json=False)` for prose (JSON mime type was breaking non-JSON answers). Smoke script `backend/scripts/smoke_answer_gen.py` prints provider + limits.

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

### Phase 8 answer generator — problems and fixes (summary)

| Problem | What happened | Fix |
|--------|----------------|-----|
| Prose answers broken / empty | Gemini was called with JSON-only response settings for all paths | `expect_json=False` for answer generation; JSON mime only when parsing structured output |
| `answer_too_short` / flaky quality | Single-shot generation, 503/504 from Gemini | Retries inside provider; Groq as second provider; deterministic template only on `llm_unavailable` / `llm_empty_response` after both fail |
| Groq not used | Env key not read from `Settings` | `groq_api_key` on settings + `call_groq` reads env and settings |
| Answers too long for recruiters | No upper bound | Hard validation `answer_too_long`, rewrite prompts, `_MAX_TOKENS` ≈ 480, prompt cap 300 words |
| Unknown which model served smoke | No observability | `llm_provider` in logs; module globals + smoke script output |
| `test_llm_service` mock outdated | Refactor renamed `_build_gemini_model` → `_build_gemini_clients` | Test patches `_build_gemini_clients` with legacy-branch fake |

Full narrative copy lives in **`Agent_Status.md`** (section “Phase 8 — Issue & fix reference”).

### Integration & API correctness + Gemini fallback (2026-04-20)

Logged as **`Agent_Status.md` row #14** and **Phase 8 reference items §8–§14** (same file). Summary for commit / handoff:

| Area | Issue | Resolution |
|------|--------|------------|
| **`schemas/user.py` — `WorkHistoryItem`** | Swagger default `"string"` for dates caused 422 (`start_date` / `end_date` must be YYYY-MM). | `mode="before"` coercion: `YYYY-MM-DD` → `YYYY-MM`; `end_date` placeholders → `null`; clear error on bad `start_date` mentioning Swagger. |
| **`POST /api/generate/answer`** | Profile JSON sent at **root** → missing `question`, `extra_forbidden` on all profile keys. | Body must be `{ question, jd_text?, jd_url?, profile? }`. |
| **JSON body** | `json_invalid` / “Expecting ',' delimiter” near EOF. | Add **closing `}`** for root after `profile`’s `}`; no trailing commas; ASCII `"` only. |
| **`jd_url`** | Literal `"string"` from docs. | Use `null` or omit when using pasted `jd_text` only. |
| **Gemini `503`** | User doubt: local machine vs Google. | **`503` / high-demand messages are Google-side capacity**, not the dev PC; keep Groq + retries. |
| **`services/llm.py` + `settings.py`** | Fallback `gemini-2.0-flash` returned **404** for new API keys after primary **503**. | Default **`GEMINI_MODEL_FALLBACK=gemini-2.5-flash-lite`**; `_extend_gemini_model_chain` appends Flash-Lite when chain still contains `gemini-2.0-flash*`; **`_gemini_retryable`** includes **`NO LONGER AVAILABLE`** so 404 advances the chain. `.env.example` updated. |
| **`resume/analyze` multipart** | `-F resume_text=string` with PDF. | Omit or use real pasted text — not the placeholder word `string`. |
| **Tests** | Regression coverage for above. | `test_schemas.py` (dates + Swagger message); `test_llm_service.py` (overload retry, deprecated 2.0 → lite chain). **47** `tests/unit` passing at last run. |
