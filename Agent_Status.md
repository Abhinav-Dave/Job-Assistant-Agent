# Agent action log

Append a new entry after each agent task or phase. PRD reference: Section 20 (Agent Status Tracking Protocol).

---

| # | Date | Phase | Scope | Summary | Status |
|---|------|-------|-------|---------|--------|
| 1 | 2026-04-19 | 1 | Repo root + `frontend/` + `backend/` + `docs/` + `supabase/` | Initial PRD Section 9 scaffold: Next.js 14 app, FastAPI tree, prompts, migrations, status templates | Done |
| 2 | 2026-04-19 | 1 | Git / GitHub | Pre-push audit (gitignore fix for `frontend/lib/`), commit `493174d`, push to `origin/main` | Done |
| 3 | 2026-04-19 | 2 | `backend/` | Supabase client (`settings.py`, `services/supabase.py`), JWT `verify_jwt` + `get_current_user` in `middleware/auth.py`, protected routes wired on all API routers + `feedback.py`, public `GET /api/health`, helper `verify_db.py`; unit test `tests/unit/test_auth.py` | Done |
| 4 | 2026-04-19 | 2 | `backend/` + status | Dual-path `.env` loading (`backend/` + repo root), `verify_phase2.py` end-to-end checks (DB + JWT + health), `status.md` / `Agent_Status.md` updated for Phase 2 closure; pre-push audit (no secrets in tracked files, `.env` gitignored); pushed `92e32be` | Done |
| 5 | 2026-04-19 | 3 | `backend/schemas/` + `backend/tests/unit/test_schemas.py` | Pydantic v2 models: `user.py` (UserPreferences, WorkHistoryItem, EducationItem, UserProfile, UpdateUserRequest), `resume.py`, `answer.py` (model validator for jd_text/jd_url), `application.py` (ApplicationStatus enum), `autofill.py`, `common.py`; package exports in `schemas/__init__.py`; unit tests for ValidationError + happy paths; `backend/requirements.txt` → `pydantic[email]` for EmailStr | Done |
| 6 | 2026-04-20 | 4 | `backend/` (no `frontend/`) | Phase 4: `main.py` CORS + `StructuredLoggingMiddleware` + `JsonHttpError` handler; `middleware/logging.py` structured JSON (stdout + `logs/app.log`); `services/llm.py` Gemini ping for health; `routers/*` mock responses wired to Phase 3 schemas + `mock_data.py`; `GET /api/health` → `HealthCheckResult` (DB + LLM); protected routes use `get_current_user`; `requirements.txt` + `python-multipart`; `test_schemas.py` updated for `HealthCheckResult.degraded`; pytest 17 passed; verified `/api/health` + 401 without Bearer | Done |
| 7 | 2026-04-20 | 4 | `backend/` verification + DX fixes | Final acceptance verification with live uvicorn and `/docs`: verified protected routes with Bearer JWT, `POST /api/auth/verify`, `POST /api/resume/analyze`, `GET /api/health`, and request logs in `backend/logs/app.log`. Resolved blockers: `uvicorn` PATH issue (`python -m uvicorn`), accidental `backend/backend` directory navigation, root 404 (`GET /` helper route), Swagger auth 401 (migrated to `HTTPBearer`), JWT confusion (added `mint_dev_jwt.py`), and LLM model mismatch/deprecation warning (`gemini-2.5-flash` default + `GEMINI_MODEL` override). | Done |
| 8 | 2026-04-20 | 5 | `backend/tools/*.py` + `backend/tests/unit/test_scraper.py` + `backend/tests/unit/test_pdf_parser.py` | Implemented `scrape_job_description(url)` and `scrape_form_fields(url)` via `httpx` + `BeautifulSoup` with selector fallbacks, non-fatal failures, and normalized `FormField` output; implemented `extract_text_from_pdf(file_bytes)` via `PyMuPDF` with clean handling for empty/scanned/invalid PDFs; added deterministic unit tests with mocked HTTP/PDF inputs for success and failure paths; verified with `python -m pytest backend/tests/unit/test_scraper.py backend/tests/unit/test_pdf_parser.py -v` (8 passed). | Done |
| 9 | 2026-04-20 | 6 | `backend/services/llm.py` + `backend/tests/unit/test_llm_service.py` | Implemented Phase 6 LLM service: `load_prompt(filename)` with path safety, `call_gemini(prompt,max_tokens)` with env model override (`GEMINI_MODEL`), timeout handling (`LLM_TIMEOUT_SECONDS`), structured `LLMError` mapping, optional `call_groq(prompt,max_tokens)` fallback (env/library gated), `parse_json_from_response(raw)` for direct/fenced/preamble JSON, and `check_llm_reachable()` using real call path. Added deterministic unit tests for JSON extraction and failure paths; validated with `python -m pytest backend/tests/unit/test_llm_service.py backend/tests/unit/test_schemas.py -v` (16 passed). | Done |
| 10 | 2026-04-20 | 7 | `backend/agents/resume_scorer.py` + `backend/tests/unit/test_resume_scorer.py` + status files | Implemented `analyze_resume_and_jd(resume_source, jd_source, user_id)` per PRD with source resolution (PDF/text + URL/text), expected structured `AgentError` outcomes (`pdf_no_text`, `jd_scrape_failed`, `resume_too_short`, `jd_too_short`), context-length truncation, prompt load from `resume_score_v1.txt`, Gemini call, JSON parse + `ResumeScoreResult` validation, and one correction retry on JSON/schema failure. Added integration-compatible logging hooks (agent/user/duration/score/token placeholders/success) and targeted unit coverage for success, retry, and expected failures; verified with `python -m pytest backend/tests/unit/test_resume_scorer.py -v` (6 passed). | Done |
| 11 | 2026-04-20 | 8 | `backend/agents/answer_generator.py` + `backend/tests/unit/test_answer_gen.py` + status files | Implemented `generate_tailored_answer(question, user_profile, jd_text)` per PRD with compact profile summarization from `UserProfile`, prompt load from `answer_gen_v1.txt`, JD truncation guard, Gemini call, output cleanup via `clean_answer` (preamble/meta/markdown stripping), minimum quality checks (length + banned phrase + first-person validation), and structured `AnswerResult` return with `word_count`. Added structured `AgentError` for expected failures and Phase 7-style logging hooks (`agent_name`, `user_id`, `duration_ms`, `word_count`, success/failure). Added focused unit tests for success/cleanup and expected failures; verified with `python -m pytest backend/tests/unit/test_answer_gen.py -v` (4 passed). | Done |
| 12 | 2026-04-20 | 7–8 + routes | `answer_generator.py`, `llm.py`, `routers/resume.py`, prompts, `test_answer_gen.py`, `test_llm_service.py`, `status.md`, `Agent_Status.md` | Answer-gen hardening: 300-word default cap, `answer_too_long` retries, `resolve_word_limits` + `ANSWER_MAX_WORDS`, Gemini→Groq→fallback chain, `llm_provider` logging + `LAST_PROVIDER_USED`. **`POST /api/resume/analyze` wired to real `analyze_resume_and_jd`** (PDF + text/Markdown file detection, `jd_url` scrape). Fixed `test_llm_service` to mock `_build_gemini_clients`. Added this detailed reference section below. | Done |
| 13 | 2026-04-20 | 6–8 + scraper + answers | `llm.check_llm_reachable`, `resume_scorer._call_llm_json`, `tools/scraper.py`, `routers/resume.py`, `routers/answers.py`, `schemas/answer.py` | **Operational fixes:** Health LLM ping switched to short prose (`expect_json=False`) + **Groq second** so `/api/health` is not false-negative when Gemini returns empty JSON ping. **Resume scorer** uses same **Gemini→Groq JSON** failover as answer gen on `llm_unavailable` / `llm_empty_response`. **JD:** `best_effort_jd_text` (URL then pasted fallback), JSON-LD `JobPosting` + `data-automation` selectors + longer HTTP timeout for ATS pages; resume + answer routes use merged JD. **`POST /api/generate/answer`** calls real `generate_tailored_answer` with optional `profile` body field (defaults to mock profile). Tests: `test_analyze_resume_and_jd_falls_back_to_groq_when_gemini_overloaded`, JSON-LD scrape test, `best_effort_jd_text` test. | Done |
| 14 | 2026-04-20 | 6–8 + schemas + docs | `schemas/user.py`, `services/llm.py`, `settings.py`, `tests/unit/test_schemas.py`, `tests/unit/test_llm_service.py`, `.env.example`, `status.md`, this file | **Integration hardening (manual API / Swagger / Gemini):** (1) **`WorkHistoryItem` dates** — Pydantic required `YYYY-MM`; OpenAPI/Swagger prefilled `"string"` → 422. **Fix:** `mode="before"` validators `_coerce_year_month` / `_coerce_end_date`: accept `YYYY-MM-DD` → month; treat `end_date` placeholders (`"string"`, `"null"`, empty) as `None`; explicit error for `start_date` mentioning Swagger. (2) **`POST /api/generate/answer` contract** — users sent `UserProfile` at JSON root → `missing question`, `extra_forbidden` on profile fields. **Doc:** body is `AnswerRequest`: `question`, `jd_text` and/or `jd_url`, optional nested `profile`. (3) **Malformed JSON** — single `}` at end closed only `profile`, not root → `json_invalid` / “Expecting ',' delimiter”. **Doc:** closing `}` for `profile` plus `}` for root; avoid smart quotes; no trailing commas. (4) **`jd_url: "string"`** — use `null` or omit. (5) **Gemini** — `503 UNAVAILABLE` / high demand is **Google-side**, not local hardware. (6) **`gemini-2.0-flash` fallback 404** — “no longer available to new users”. **Fix:** default `GEMINI_MODEL_FALLBACK` → `gemini-2.5-flash-lite`; `_extend_gemini_model_chain` appends `gemini-2.5-flash-lite` when any chain model is `gemini-2.0-flash*`; `_gemini_retryable` treats `NO LONGER AVAILABLE` like overload so third hop runs; log line “failed … retrying”. Tests: schema coercion + Swagger string error; `test_call_gemini_retries_on_overload_when_fallback_set`, `test_call_gemini_retries_after_deprecated_gemini20_404`. **47** unit tests passing at closure. | Done |

---

## Phase 8 — Issue & fix reference (answer generator + LLM)

Use this when debugging similar failures in other projects.

### 1. JSON response mode broke plain-text answers

- **Symptom:** Answer generation returned empty, malformed, or validation errors; prose prompts still forced `application/json` / structured output on Gemini.
- **Root cause:** `call_gemini` always set `response_mime_type: application/json`, which is correct for resume scoring (JSON schema) but wrong for free-form interview answers.
- **Fix:** Added `expect_json: bool` (default `True` for backward compatibility). Answer generator calls `call_gemini(..., expect_json=False)` so the model returns natural language.

### 2. Frequent `answer_too_short`, 503/504, long hangs

- **Symptom:** Smoke and integration runs failed validation after Gemini timeouts or short replies; users waited on a single provider.
- **Root cause:** No in-provider retries for transient failures; no secondary model; strict minimum word count without rewrite loop.
- **Fix:** Up to `_MAX_GENERATION_ATTEMPTS` per provider; on `answer_too_short`, `answer_too_long`, or `answer_quality_failed`, rebuild prompt with `REWRITE INSTRUCTIONS` and prior output. Chain: **Gemini → Groq** (`call_groq` with same timeout/token patterns). **Deterministic `_build_fallback_answer`** only when both providers raise serious codes (`llm_unavailable`, `llm_empty_response`) — not for generic quality failure alone.

### 3. Groq “not configured” despite `.env`

- **Symptom:** Fallback never ran or raised `groq_not_configured`.
- **Root cause:** API key only in environment variable name variants; `Settings` model had no `groq_api_key` field.
- **Fix:** Added `groq_api_key` to `settings.py`; `call_groq` checks `GROQ_API_KEY`, `groq_api_key` env, and `settings.groq_api_key`.

### 4. Answers too long (smoke ~325+ words)

- **Symptom:** Recruiter-facing copy was detailed but tedious; no upper bound in validation.
- **Root cause:** Prompt asked for “250–350” style length without enforcement; `max_output_tokens` generous.
- **Fix:** `_validate_answer_quality` enforces `max_words` (default **300**, overridable via `ANSWER_MAX_WORDS`); regex on question (e.g. “in 80 words”) lowers cap and min; `answer_too_long` triggers compression rewrite; prompt text targets **220–280**, never exceed 300; `_MAX_TOKENS` reduced (~480) for prose path; fallback answer truncated to `max_words`.

### 5. No visibility into Gemini vs Groq vs fallback

- **Symptom:** Smoke test could not tell which backend produced the answer.
- **Root cause:** Success path only logged generic `agent_success`.
- **Fix:** Log `extra={"llm_provider": "gemini"|"groq"|"fallback", "word_limit_max": ...}`; module-level `LAST_PROVIDER_USED`, `LAST_WORD_LIMIT_MAX` for scripts; `smoke_answer_gen.py` prints them.

### 6. Unit test `test_call_gemini_returns_text_from_mocked_client` failed

- **Symptom:** `AttributeError: module 'services.llm' has no attribute '_build_gemini_model'`.
- **Root cause:** Phase 6+ refactor introduced `_build_gemini_clients` returning either `google.genai` or `google.generativeai` legacy tuple; test still patched old symbol.
- **Fix:** Patch `_build_gemini_clients` and return legacy-shaped tuple `("google.generativeai", fake_model, model_name, fake_legacy_module)`.

### 7. `POST /api/resume/analyze` was still Phase 4 mock

- **Symptom:** Real scorer agent existed but HTTP always returned fixed `match_score=74`, etc.
- **Root cause:** Router never imported `analyze_resume_and_jd`.
- **Fix:** Router reads upload bytes, classifies PDF vs text (extension or `%PDF` magic), builds `resume_source` / `jd_source`, calls agent; maps `ResumeAgentError` → 422 flat JSON; `LLMError` → 503.

### 8. `422` on `profile.work_history[].start_date` / `end_date` with `input: "string"`

- **Symptom:** `POST /api/generate/answer` with nested `profile` failed validation: *Value error, start_date must be "YYYY-MM"* even when the user thought they filled dates.
- **Root cause:** OpenAPI / Swagger UI defaults string fields to the literal **`"string"`**, which is not a valid month. `WorkHistoryItem` validators required strict `YYYY-MM` only.
- **Fix (`schemas/user.py`):** `field_validator(..., mode="before")` with `_coerce_year_month` / `_coerce_end_date`: trim ISO dates to first 7 chars (`2022-06-15` → `2022-06`); map `end_date` placeholders (`"string"`, `"null"`, empty) → `None`; for `start_date` if value is `"string"`, raise `ValueError` that names Swagger explicitly. `Field(examples=...)` on dates for better docs.

### 9. `422` on `POST /api/generate/answer`: `question` missing, `extra_forbidden` on `id`, `email`, …

- **Symptom:** FastAPI `detail` listed `question` as required and every profile field as forbidden extra at `body.*`.
- **Root cause:** Request body must match **`AnswerRequest`**, not `UserProfile`. Callers pasted the profile JSON at the **root** instead of under **`"profile"`**, and omitted **`question`** (and often `jd_text` / `jd_url`).
- **Fix:** Documentation only (no schema change): correct JSON shape is `{ "question": "...", "jd_text": "...", "jd_url": null | "<url>", "profile": { ...UserProfile... } }`. Omit `profile` entirely to use server mock profile (`routers/answers.py`). JWT `sub` overwrites `profile.id` when profile is supplied.

### 10. `422` `json_invalid` — “Expecting ',' delimiter” (character offset ~end of body)

- **Symptom:** Raw `curl -d '{ ... }'` or Swagger body failed JSON parse before Pydantic.
- **Root cause:** **Unclosed root object**: one trailing `}` closed `profile` but the outer object opened by the first `{` was never closed; or trailing comma after last property; or curly/smart quotes breaking strings.
- **Fix:** Document valid closing: `… "updated_at": "…Z" } }` — inner `}` ends `profile`, outer `}` ends `AnswerRequest`. Validate JSON in jsonlint or `python -c "import json,sys; json.load(sys.stdin)"` before sending.

### 11. `jd_url` set to Swagger placeholder `"string"`

- **Symptom:** Unintended URL fetch or confusing JD merge behavior; not always JSON parse failure.
- **Root cause:** Copy-paste from OpenAPI example.
- **Fix:** Use **`null`** or **omit** `jd_url` when only pasted `jd_text` is intended. Server uses `best_effort_jd_text` (URL first, then text if scrape is thin).

### 12. Gemini `503 UNAVAILABLE` / “high demand” — local vs Google?

- **Symptom:** Logs show Gemini overload; user unsure if laptop or code is at fault.
- **Root cause:** **Google API capacity / transient availability** for the configured model (not local CPU, not FastAPI bugs). Distinguished from `401`/`403` (key), `404` (model id / deprecation), `429` (quota).
- **Fix:** Operational guidance only: retry later, keep **`GROQ_API_KEY`** for failover (answer + resume paths already chain providers), optional `GEMINI_MODEL` / `GEMINI_MODEL_FALLBACK` in `.env`.

### 13. Primary `gemini-2.5-flash` `503` then fallback `gemini-2.0-flash` → `404 NOT_FOUND` (“no longer available to new users”)

- **Symptom:** Health ping and `call_gemini` logged second failure; new Google AI Studio / API projects could not use `gemini-2.0-flash`. Smoke still eventually succeeded via Groq or other path.
- **Root cause:** Default **`GEMINI_MODEL_FALLBACK`** was `gemini-2.0-flash`, deprecated / blocked for new users while overload retry was intended for capacity only.
- **Fix (`settings.py`, `.env.example`):** Default fallback → **`gemini-2.5-flash-lite`**. **`services/llm.py`:** `_extend_gemini_model_chain` — if any model id in the chain starts with `gemini-2.0-flash`, append **`gemini-2.5-flash-lite`** when not already present (safety net for envs still pointing at 2.0). **`_gemini_retryable`:** treat errors containing **`NO LONGER AVAILABLE`** as retryable so the chain advances past 404 to Flash-Lite. `call_gemini` log: *“Gemini model X failed (…), retrying with Y”*. Tests: `test_call_gemini_retries_on_overload_when_fallback_set`, `test_call_gemini_retries_after_deprecated_gemini20_404` (503 → 404 deprecated → lite).

### 14. `POST /api/resume/analyze` multipart: `resume_text=string`

- **Symptom:** Accidental literal resume text “string” sent alongside PDF.
- **Root cause:** Swagger / curl placeholder.
- **Fix:** Omit `resume_text` when uploading `resume_file`, or paste real text — not the word `string`.

---

## Entry template (copy below)

```
| # | Date | Phase | Scope | Summary | Status |
|---|------|-------|-------|---------|--------|
| N | YYYY-MM-DD | X | backend/ / frontend/ / ... | What changed | Done |
```
