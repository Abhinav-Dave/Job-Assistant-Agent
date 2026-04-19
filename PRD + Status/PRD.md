# 🧠 PRD: AI-Powered Job Application Assistant

**Product:** AI Job Application Assistant (Web App)
**Version:** 2.0 — Final Build-Ready
**Status:** Approved — Ready for Development
**Author:** Solo Dev — Internship Assignment (Weeks 1–3)
**Timeline:** ~7 days (1 week)
**Stack:** Next.js 14 + FastAPI + Supabase (PostgreSQL + Auth) + Gemini 2.5 Flash
**Reference:** Simplify.jobs (UI/UX inspiration)
**Future Vision:** Full career ops platform (multi-agent, job board integrations, analytics)

> Build a production-grade AI co-pilot for job seekers. It autofills applications, scores resumes against job descriptions, generates tailored answers, and tracks every application — all behind a secure login, all powered by Gemini 2.5 Flash.

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [Target Users & Personas](#4-target-users--personas)
5. [Core Features (MVP)](#5-core-features-mvp)
6. [System Architecture](#6-system-architecture)
7. [Agent Design & Workflows](#7-agent-design--workflows)
8. [Tech Stack & Justification](#8-tech-stack--justification)
9. [File & Folder Structure](#9-file--folder-structure)
10. [Database Schema (Supabase / PostgreSQL)](#10-database-schema-supabase--postgresql)
11. [Authentication Design](#11-authentication-design)
12. [API Design](#12-api-design)
13. [Frontend: Screens & Components](#13-frontend-screens--components)
14. [State Management Strategy](#14-state-management-strategy)
15. [Prompt Engineering](#15-prompt-engineering)
16. [Security Considerations](#16-security-considerations)
17. [Logging & Observability](#17-logging--observability)
18. [Edge Cases & Failure Handling](#18-edge-cases--failure-handling)
19. [Testing Strategy](#19-testing-strategy)
20. [Agent Status Tracking Protocol](#20-agent-status-tracking-protocol)
21. [Milestone & Phase Breakdown](#21-milestone--phase-breakdown)
22. [Sub-Agent Windows (Cursor Parallelization)](#22-sub-agent-windows-cursor-parallelization)
23. [Future Features Roadmap (Post-MVP)](#23-future-features-roadmap-post-mvp)
24. [Risks & Tradeoffs](#24-risks--tradeoffs)
25. [Open Questions](#25-open-questions)
26. [Appendix: Prompt Templates](#26-appendix-prompt-templates)
27. [Appendix: Environment Variables](#27-appendix-environment-variables)

---

## 1. Executive Summary

### What is this?

The AI Job Application Assistant is a web application that acts as a personal career co-pilot. A user creates a profile once — their work history, education, skills, and preferences — and the system uses that data across four AI-powered agents to help them apply faster and better.

### The four agents:
| Agent | What it does |
|-------|-------------|
| **Resume Scorer** | Compares a resume against a job description, returns a 0–100 match score and specific improvement suggestions |
| **Tailored Answer Generator** | Takes any application question + the JD + the user's profile, writes a personalized first-person answer |
| **Autofill Mapper** | Scrapes a job application form, maps every field to the user's stored profile data, shows confidence per field |
| **Application Dashboard** | Tracks every job application the user adds, with a full status pipeline |

### Why this stack?
- **Supabase** = PostgreSQL + Auth + File Storage in one free account. No separate auth service needed.
- **FastAPI (Python)** = Best framework for AI/agent work. Native async. Pydantic validation baked in.
- **Next.js 14** = Frontend with App Router. Deployed on Vercel in minutes. No separate server.
- **Gemini 2.5 Flash** = Already on user's Google billing account. 1M token context window. Cheap at low volume (~$0.15/1M input tokens). No new account setup needed.
- **BeautifulSoup + httpx** = Free, sufficient for MVP scraping. Covers LinkedIn, Indeed, Greenhouse.

### What this is NOT (for now):
- Not a browser extension (web app only for MVP; extension is future phase)
- Not multi-user enterprise software (single authenticated user per account)
- Not connected to LinkedIn API or any job board API
- Not auto-submitting applications on behalf of the user

---

## 2. Problem Statement

### The core pain

Job seekers applying to multiple roles face three compounding problems that compound each other:

**Problem 1: Repetitive data entry kills momentum.**
The average job seeker fills out the same personal information — name, contact, work history, education — dozens of times per week across different ATS systems (Greenhouse, Lever, Workday, iCIMS). Every form is slightly different. There is no standard. This is pure wasted time.

**Problem 2: Resume-to-JD fit is invisible.**
Applicants send resumes without knowing if they match the job description. They don't know which keywords are missing, which skills are in demand for this specific role, or how their experience compares to what the JD is asking for. The result: low-quality applications that never make it past ATS screening.

**Problem 3: Application essay questions produce blank-page paralysis.**
"Why are you a good fit for this role?" is asked thousands of times per day. Most applicants write generic, template-sounding answers that fail to reference the specific JD or connect their specific experience. This is a solvable problem with the right context and a good LLM.

**Problem 4: No single place to track everything.**
Applications go into a black hole. Spreadsheets get out of date. Applicants forget which companies they applied to, what stage they're at, and when they last heard back.

### Why existing tools don't fully solve it

| Tool | What it does | What it misses |
|------|-------------|----------------|
| Simplify | Autofill + job tracking | No resume scoring, no AI answer generation |
| Jobscan | Resume-JD scoring | No autofill, no answer gen, subscription required |
| ChatGPT | Can do answer gen | No profile memory, no scoring, no dashboard |
| Spreadsheets | Job tracking | No AI, all manual |

**This system combines all four into one tool, backed by the user's actual stored profile, not a generic AI.**

---

## 3. Goals & Success Metrics

### MVP Goals (Week 1)

1. User can register, log in, and log out securely
2. User can create and update a full professional profile
3. User can upload a resume PDF + provide a JD → receive a scored, structured analysis
4. User can ask any application question → receive a personalized, non-generic answer
5. User can paste a job application URL → see a field-by-field autofill preview
6. User can track all applications with status pipeline updates
7. App runs locally (`localhost`) with zero paid cost during development

### Success Metrics

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Auth flow | Register → Login → Protected routes work | Manual QA |
| Profile completeness | All 4 sections saveable and retrievable | API test |
| Resume score latency | Result returned in ≤15 seconds | Manual timing |
| Resume score relevance | Score references JD-specific skills | Manual review of 5 test runs |
| Answer personalization | Answer contains user's actual company/role names | Manual review |
| Answer length | 250–400 words, clean first-person | Manual review |
| Autofill field detection | ≥80% of standard fields detected and mapped | Test on 3 real job forms |
| Dashboard CRUD | Create, update status, delete all work | Manual QA |
| Health check | `GET /api/health` returns 200 in <500ms | Automated test |
| Agent status log | Both `status.md` and `Agent_Status.md` updated after every phase | Dev discipline check |

---

## 4. Target Users & Personas

### Primary User: The Active Job Seeker

| Attribute | Detail |
|-----------|--------|
| Who | College students, recent grads, early-to-mid career professionals, career switchers |
| Goal | Apply to more jobs faster, with higher-quality, personalized applications |
| Frequency | Actively applying — 5–20 applications per week |
| Pain points | Repeating form data endlessly; unsure if resume is good enough; blank-page anxiety on essay questions; no visibility into their own pipeline |
| Tech comfort | Moderate — comfortable with web apps, browser extensions, Google Drive |
| What they already use | LinkedIn, Indeed, Glassdoor, Google Sheets (for tracking), ChatGPT (ad hoc) |
| What success looks like | Gets more interview callbacks; spends <30 min per application instead of 90 min |

### Secondary User: The Internship Evaluator

| Attribute | Detail |
|-----------|--------|
| Who | Pronexus AI hiring team (Erica + team) |
| Goal | Evaluate technical depth, product thinking, code quality, and AI/agent design |
| What they need | Run the app locally in <5 minutes, click through all features, immediately understand what was built and why |
| What impresses them | Clean architecture, real AI output (not mocked), thoughtful UX, documented decision-making |

---

## 5. Core Features (MVP)

### Feature 1: Authentication

**What:** Secure email/password auth powered by Supabase Auth. All routes protected. JWT tokens handled automatically.

**Flows:**
- Register: email + password → Supabase creates user → redirect to onboarding
- Login: email + password → JWT issued → stored in Supabase session → redirect to dashboard
- Logout: session cleared → redirect to login
- Protected routes: any route other than `/login` and `/register` redirects to `/login` if no valid session

**Why Supabase Auth:** It uses PostgreSQL under the hood, issues JWTs that FastAPI can verify with `python-jose`, and eliminates ~4 hours of building auth middleware from scratch. It also unlocks Google OAuth in 10 minutes if desired later.

---

### Feature 2: User Profile (Onboarding)

**What:** A multi-step profile creation wizard. Collected once, used by all agents as their "ground truth" about the user.

**Why this matters:** Every AI agent in this system is only as good as the profile data it has access to. A half-filled profile means generic AI output. A complete profile means highly personalized, accurate output.

**Profile sections:**

| Section | Fields |
|---------|--------|
| Personal Info | Full name, email (auto-filled from auth), phone, location, LinkedIn URL, portfolio/GitHub URL |
| Work History | Array of jobs: company name, job title, start date, end date, is_current (bool), bullet points (array of strings describing responsibilities/achievements) |
| Education | Array: institution name, degree type, field of study, graduation year, GPA (optional) |
| Skills & Preferences | Skills (tag input, array of strings), desired roles (array), target industries (array), preferred location, remote preference (remote/hybrid/onsite), salary expectation min |

**UX behavior:**
- Multi-step wizard: 4 steps with progress bar
- Each step auto-saves to backend on "Continue" — never lose data on refresh
- User can return to profile settings and edit any section at any time
- Work history and education support dynamic add/remove rows

---

### Feature 3: Resume Scorer Agent

**What:** User provides their resume (PDF upload or paste text) + a job description (URL or paste text). Agent returns a structured match analysis.

**Why this matters:** Most applicants have no idea which skills are missing from their resume for a specific role. This agent makes the invisible visible — here's your score, here's exactly what's missing, here's how to fix it.

**Input options (both flexible):**
- Resume: PDF upload (parsed server-side) OR paste plain text
- JD: URL (scraped server-side) OR paste plain text

**Output — `ResumeScoreResult`:**
```json
{
  "match_score": 74,
  "grade": "B",
  "summary": "Your resume is a strong technical match but is missing keywords around infrastructure and deployment that appear prominently in this JD.",
  "matched_skills": ["Python", "REST APIs", "SQL", "React"],
  "missing_skills": ["Kubernetes", "Terraform", "CI/CD pipelines"],
  "suggestions": [
    "Add a bullet point about any CI/CD experience (GitHub Actions, Jenkins, etc.) to your most recent role",
    "Mention cloud platform experience (AWS/GCP/Azure) explicitly — the JD calls it out 3 times",
    "Quantify your backend work: instead of 'built APIs', say 'built 12 REST API endpoints serving 50K requests/day'",
    "Add a Skills section if you don't have one — ATS systems scan for keyword density"
  ],
  "jd_key_requirements": ["Python", "Kubernetes", "SQL", "REST APIs", "CI/CD", "Terraform"],
  "ats_risk": "medium",
  "ats_risk_reason": "Missing 3 of 6 high-frequency JD keywords. ATS may filter before human review."
}
```

**UX behavior:**
- Three-stage loading indicator: "Fetching job description...", "Analyzing your resume...", "Building your report..."
- Score displayed as large circular gauge (0–100) with grade badge
- Matched skills shown as green tags, missing skills as red tags
- Suggestions shown as numbered list, each actionable and specific
- ATS risk badge (low / medium / high) with tooltip explanation
- Thumbs up / thumbs down feedback per result (logged)

---

### Feature 4: Tailored Answer Generator

**What:** User selects or types an application question. Agent generates a first-person, personalized answer using the user's actual profile data and the job description.

**Why this matters:** Generic AI answers are obvious and ineffective. This agent grounds every answer in the user's real work history, real skills, and the specific JD — making the output sound like the user wrote it, not an AI.

**Common question presets (selectable from dropdown):**
1. "Why are you a good fit for this role?"
2. "What is your greatest professional strength?"
3. "Describe a challenge you overcame at work."
4. "Why do you want to work at [company]?"
5. "Where do you see yourself in 5 years?"
6. "Tell me about a time you worked in a team."
7. Custom (free text input)

**Input:**
- Selected or typed question
- Current user profile (auto-loaded)
- JD text (from last scored JD, or user pastes fresh)

**Output:**
- Generated answer: 250–400 words, first-person, references specific user experience
- Word count badge
- "Copy to clipboard" button
- Inline editable text area (user can edit before copying)
- "Regenerate" button (uses same inputs, produces a new variation)
- Thumbs up / thumbs down feedback

**What the answer must NOT do (enforced in prompt):**
- Use phrases like "As an AI...", "Certainly!", "I am a highly motivated..."
- Be generic / could apply to any candidate
- Invent experience the user does not have in their profile

---

### Feature 5: Autofill Mapper

**What:** User pastes a job application form URL. Agent scrapes the form fields, maps each one to the corresponding value from the user's profile, and presents a preview with confidence scores.

**Why this matters:** Every ATS form is slightly different. The same concept ("first name") appears as 20 different HTML labels across systems. This agent handles the mapping logic so the user can see exactly what would be filled in and correct any low-confidence matches before they copy/paste.

**MVP scope (web preview — not browser extension):**
The web app version shows a preview table — what fields were detected, what value would be filled, confidence level. User reviews and corrects. Browser extension that actually injects values into forms is Phase 2.

**Confidence tiers:**
| Tier | Confidence | Color | Behavior |
|------|-----------|-------|---------|
| Auto-fill | ≥85% | Green | Show value, no action needed |
| Suggest | 50–84% | Yellow | Show value, prompt user to confirm |
| Unknown | <50% | Red | Show blank, user must fill manually |

**Output — `AutofillResult`:**
```json
{
  "fill_rate": 0.82,
  "mappings": [
    {
      "field_id": "input_firstname",
      "field_label": "First Name",
      "field_type": "text",
      "profile_key": "full_name (first)",
      "suggested_value": "Jane",
      "confidence": 0.97
    },
    {
      "field_id": "input_coverletter",
      "field_label": "Cover Letter",
      "field_type": "textarea",
      "profile_key": null,
      "suggested_value": null,
      "confidence": 0.12
    }
  ],
  "unfilled_fields": ["cover_letter", "custom_question_1"],
  "total_fields": 17,
  "mapped_fields": 14
}
```

---

### Feature 6: Application Dashboard

**What:** A Kanban-style or table-view tracker for every job the user has applied to or is considering. Full CRUD. Status pipeline.

**Why this matters:** Job searching is a project. Without a system to track where things stand, applicants miss follow-up windows, forget to prepare for interviews, and lose momentum. This dashboard is the user's mission control.

**Application status pipeline:**
```
saved → submitted → response_received → interview_requested →
interview_completed → onsite_requested → offer_received → rejected / withdrawn
```

| Status | Color | Meaning |
|--------|-------|---------|
| `saved` | Gray | Saved to track, not yet applied |
| `submitted` | Blue | Application sent |
| `response_received` | Purple | Company responded (any response) |
| `interview_requested` | Yellow | Phone/video screen scheduled |
| `interview_completed` | Orange | Interview done, awaiting decision |
| `onsite_requested` | Teal | Final round / onsite scheduled |
| `offer_received` | Green | Offer extended |
| `rejected` | Red | Application declined at any stage |
| `withdrawn` | Dark gray | User withdrew |

**Dashboard fields per application:**
- Company name
- Role/job title
- Job description URL (optional)
- Date applied
- Current status
- Notes (free text, e.g., recruiter name, next steps)
- Last updated timestamp

**Dashboard UI:**
- Default view: table with sortable columns
- Status can be updated inline via dropdown — no page reload
- Add new application via modal form
- Delete with confirmation dialog
- Filter by status (show only "interview_requested", etc.)
- Summary cards at top: Total applied | Active (non-rejected) | Interviews | Offers

---

## 6. System Architecture

### High-Level Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                    Next.js 14 Web App                            │    │
│   │              (React + Tailwind + App Router)                     │    │
│   │                                                                   │    │
│   │  /login  /register  /onboarding  /dashboard  /resume             │    │
│   │  /answers  /autofill  /profile                                   │    │
│   └───────────────────────────┬─────────────────────────────────────┘    │
└───────────────────────────────┼──────────────────────────────────────────┘
                                │
                                │ HTTP REST (Authorization: Bearer <JWT>)
                                │
┌───────────────────────────────┼──────────────────────────────────────────┐
│                           API LAYER                                       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                  FastAPI (Python 3.11)                           │    │
│   │                  localhost:8000                                   │    │
│   │                                                                   │    │
│   │  Auth middleware: verifies Supabase JWT on every protected route │    │
│   │  Routers: /users  /resume  /generate  /applications  /autofill  │    │
│   │           /health                                                 │    │
│   └────────────┬─────────────────────────────┬────────────────────--┘    │
└────────────────┼─────────────────────────────┼───────────────────────────┘
                 │                             │
    ┌────────────┘                             └─────────────────┐
    │                                                             │
    ▼                                                             ▼
┌────────────────────────┐                         ┌─────────────────────────┐
│      AGENT LAYER       │                         │    EXTERNAL SERVICES     │
│  (backend/agents/)     │                         │                          │
│                        │                         │  ┌─────────────────────┐ │
│  resume_scorer.py      │──────────────────────▶ │  │  Google Gemini API  │ │
│  answer_generator.py   │    LLM calls via         │  │  (gemini-2.5-flash) │ │
│  autofill_mapper.py    │    services/llm.py       │  └─────────────────────┘ │
│                        │                         │                          │
│       ┌────────────┐   │                         │  ┌─────────────────────┐ │
│       │  TOOLS     │   │                         │  │   Supabase          │ │
│       │            │   │──────────────────────▶ │  │   (PostgreSQL DB    │ │
│       │ scraper.py │   │    DB reads/writes       │  │    + Auth + Storage)│ │
│       │ pdf_parser │   │    via supabase-py        │  └─────────────────────┘ │
│       └────────────┘   │                         │                          │
└────────────────────────┘                         │  ┌─────────────────────┐ │
                                                   │  │   Job Sites          │ │
                                                   │  │   (LinkedIn, Indeed, │ │
                                                   │  │    Greenhouse, etc.) │ │
                                                   │  │   scraped via httpx  │ │
                                                   │  │   + BeautifulSoup    │ │
                                                   │  └─────────────────────┘ │
                                                   └─────────────────────────┘
```

### Request lifecycle — Resume Score (most complex flow)

```
1. User clicks "Analyze" in Next.js frontend
2. Frontend: POST /api/resume/analyze (multipart: PDF file + jd_url, Authorization: Bearer JWT)
3. FastAPI auth middleware: verify JWT with python-jose against Supabase JWT secret → extract user_id
4. Router calls: agents/resume_scorer.analyze_resume_and_jd(resume_text, jd_text, user_id)
   4a. If PDF: tools/pdf_parser.extract_text_from_pdf(file) → resume_text
   4b. If JD URL: tools/scraper.scrape_job_description(url) → jd_text
   4c. services/llm.call_gemini(prompt) → raw_response
   4d. parse_and_validate(raw_response) → ResumeScoreResult (Pydantic)
   4e. If invalid JSON: retry once with error-correction prompt
5. FastAPI returns ResumeScoreResult JSON (200)
6. Frontend renders score gauge, skill tags, suggestions
```

---

## 7. Agent Design & Workflows

### Design Principles (apply to all agents)

1. **Pure functions** — each agent function takes typed inputs, returns typed outputs. No shared state.
2. **Pydantic-validated output** — every LLM response is parsed and validated before returning. If invalid, retry once.
3. **Fail gracefully** — if an agent fails, return a structured error with enough context for the frontend to show a helpful message.
4. **Prompt versioning** — all prompts live in `/backend/prompts/` as versioned text files. Never hardcode prompts in Python.
5. **Tool separation** — scraping, PDF parsing, and LLM calls are separate tool functions. Agents compose tools; tools don't call agents.

---

### Agent 1: Resume Scorer (`agents/resume_scorer.py`)

**Entry function:** `analyze_resume_and_jd(resume_source, jd_source, user_id) → ResumeScoreResult`

```
INPUT:
  resume_source: ResumeSource  {type: "pdf" | "text", data: bytes | str}
  jd_source:     JDSource      {type: "url" | "text", data: str}
  user_id:       str           (UUID from JWT — for logging only, not used in prompt)

STEP 1 — Resolve resume text:
  if resume_source.type == "pdf":
    resume_text = tools.pdf_parser.extract_text_from_pdf(resume_source.data)
    if len(resume_text) < 100:
      raise AgentError("pdf_no_text", "PDF appears to be a scanned image. Please paste text instead.")
  else:
    resume_text = resume_source.data

STEP 2 — Resolve JD text:
  if jd_source.type == "url":
    jd_text = tools.scraper.scrape_job_description(jd_source.data)
    if len(jd_text) < 100:
      raise AgentError("jd_scrape_failed", "Could not read this URL. Please paste the job description text.")
  else:
    jd_text = jd_source.data

STEP 3 — Input validation:
  if len(resume_text) < 100:  raise AgentError("resume_too_short")
  if len(jd_text) < 100:      raise AgentError("jd_too_short")
  # Truncate if too long (context window protection):
  resume_text = resume_text[:6000]
  jd_text     = jd_text[:4000]

STEP 4 — Build prompt:
  prompt = load_prompt("resume_score_v1.txt")
  prompt = prompt.format(resume=resume_text, jd=jd_text)

STEP 5 — Call LLM:
  raw = services.llm.call_gemini(prompt, max_tokens=1500)

STEP 6 — Parse and validate:
  try:
    result = parse_json_from_response(raw)
    validated = ResumeScoreResult(**result)   # Pydantic validation
    return validated
  except (JSONDecodeError, ValidationError):
    # Retry once with error-correction prompt
    correction_prompt = build_correction_prompt(raw, "ResumeScoreResult schema")
    raw2 = services.llm.call_gemini(correction_prompt, max_tokens=1500)
    result2 = parse_json_from_response(raw2)
    return ResumeScoreResult(**result2)       # If this fails, let exception propagate → 500

LOGGING: log agent_name, user_id, duration_ms, score, input_tokens, output_tokens, success/failure
```

---

### Agent 2: Tailored Answer Generator (`agents/answer_generator.py`)

**Entry function:** `generate_tailored_answer(question, user_profile, jd_text) → AnswerResult`

```
INPUT:
  question:     str          (the application question)
  user_profile: UserProfile  (full profile from DB)
  jd_text:      str          (job description text)

STEP 1 — Build profile summary for prompt injection:
  profile_summary = {
    "name": profile.full_name,
    "most_recent_role": profile.work_history[0].role + " at " + profile.work_history[0].company,
    "key_experience": [first 3 work history bullets from most recent 2 roles],
    "skills": profile.skills[:15],
    "education": profile.education[0].degree + " from " + profile.education[0].institution
  }
  # Why summarize? Full profile is too long for context. We extract what's most relevant for answers.

STEP 2 — Build prompt:
  prompt = load_prompt("answer_gen_v1.txt")
  prompt = prompt.format(
    question=question,
    profile=json.dumps(profile_summary),
    jd=jd_text[:3000]
  )

STEP 3 — Call LLM:
  raw = services.llm.call_gemini(prompt, max_tokens=600)

STEP 4 — Post-process:
  answer = clean_answer(raw)
  # clean_answer strips: preamble like "Here is an answer:", markdown formatting,
  # meta-commentary like "This answer highlights...", any "As an AI" phrases

STEP 5 — Validate:
  if len(answer.split()) < 100:
    raise AgentError("answer_too_short", "Generated answer was too short. Please try again.")

RETURN: AnswerResult { answer: str, word_count: int, question: str }

LOGGING: log agent_name, user_id, question_type, duration_ms, word_count, success/failure
```

---

### Agent 3: Autofill Mapper (`agents/autofill_mapper.py`)

**Entry function:** `map_fields_to_profile(page_url, user_profile) → AutofillResult`

```
INPUT:
  page_url:     str          (URL of job application form)
  user_profile: UserProfile  (full profile from DB)

STEP 1 — Scrape form fields:
  fields = tools.form_scraper.scrape_form_fields(page_url)
  # Returns list[FormField]: {field_id, label_text, field_type, placeholder, is_required}
  if len(fields) == 0:
    raise AgentError("no_fields_detected", "No form fields found on this page.")

STEP 2 — Rule-based mapping (fast path, no LLM):
  FIELD_MAP = {
    # Normalized label → profile key + value extractor
    "first name":         ("full_name", extract_first_name),
    "last name":          ("full_name", extract_last_name),
    "email":              ("email",     lambda p: p.email),
    "phone":              ("phone",     lambda p: p.phone),
    "city":               ("location",  extract_city),
    "linkedin":           ("linkedin_url", lambda p: p.linkedin_url),
    "github":             ("portfolio_url", lambda p: p.portfolio_url),
    "years of experience":("work_history", calculate_years_experience),
    "resume":             (None,        None),   # File upload — skip
    "cover letter":       (None,        None),   # Agent can't fill this
  }
  
  for field in fields:
    normalized = field.label_text.lower().strip()
    if normalized in FIELD_MAP:
      key, extractor = FIELD_MAP[normalized]
      mapping = FieldMapping(
        field_id=field.field_id,
        field_label=field.label_text,
        profile_key=key,
        suggested_value=extractor(user_profile) if extractor else None,
        confidence=0.95   # Rule-based = high confidence
      )
    else:
      unmapped_fields.append(field)

STEP 3 — LLM fallback for ambiguous fields (only for unmapped):
  if len(unmapped_fields) > 0:
    prompt = load_prompt("autofill_v1.txt")
    prompt = prompt.format(
      fields=json.dumps([f.dict() for f in unmapped_fields]),
      profile_keys=json.dumps(profile_key_descriptions)
    )
    raw = services.llm.call_gemini(prompt, max_tokens=800)
    llm_mappings = parse_json_from_response(raw)
    # LLM returns: [{field_id, profile_key, suggested_value, confidence}]
    # Merge into mappings list

STEP 4 — Confidence filtering:
  auto_fill  = [m for m in mappings if m.confidence >= 0.85]
  suggest    = [m for m in mappings if 0.50 <= m.confidence < 0.85]
  unknown    = [m for m in mappings if m.confidence < 0.50]

RETURN: AutofillResult {
  mappings: all_mappings,
  unfilled_fields: [f.field_label for f in unknown],
  fill_rate: len(auto_fill + suggest) / len(fields),
  total_fields: len(fields),
  mapped_fields: len(auto_fill + suggest)
}
```

---

### Agent 4: Dashboard (no LLM — pure CRUD)

The dashboard does not use an LLM. It is a standard CRUD API backed by Supabase PostgreSQL. Documented fully in the API Design section.

---

## 8. Tech Stack & Justification

Every choice below is deliberate. No cargo-culting.

| Component | Choice | Version | Why This, Not Something Else |
|-----------|--------|---------|-------------------------------|
| **Frontend framework** | Next.js | 14 (App Router) | Built-in routing, SSR, API routes, deploys to Vercel in one command. React ecosystem = massive component availability. App Router is the current standard. |
| **Frontend styling** | Tailwind CSS | 3.x | Utility-first, fast to build with, no CSS file management. Pairs perfectly with shadcn/ui components. |
| **Component library** | shadcn/ui | Latest | Radix UI primitives + Tailwind. Accessible, unstyled by default, copy-paste into your project. No import from node_modules. |
| **Backend framework** | FastAPI | 0.128+ | Best Python framework for AI projects. Native async. Pydantic v2 built-in. Auto-generates OpenAPI docs at `/docs`. Type-safe everywhere. |
| **Backend language** | Python | 3.11 | Required for the AI/data science ecosystem. All LLM SDKs, scrapers, PDF parsers are Python-first. |
| **Database** | Supabase (PostgreSQL) | Latest | Real PostgreSQL — not a proprietary DB. Comes with Auth, file storage, and auto-generated REST API. Free tier: 500MB, 50K auth users. Zero infra to manage. |
| **Auth** | Supabase Auth | Built-in | JWT-based. Email/password built in. Google OAuth available in 10 min. FastAPI verifies JWTs with `python-jose`. Saves 4+ hours vs rolling custom auth. |
| **LLM** | Google Gemini 2.5 Flash | gemini-2.5-flash | User already has Google AI billing. 1M token context window. $0.15/1M input tokens = nearly free at dev/prototype volume. Strong structured JSON output. |
| **LLM SDK** | `google-generativeai` | Latest Python SDK | Official Google SDK. Simple `GenerativeModel.generate_content()` interface. |
| **LLM fallback** | Groq (Llama 3.3 70B) | Free tier | If Gemini has rate limit issues, Groq is instant setup, free, and extremely fast (~500 tok/sec). Same API pattern. |
| **Web scraping** | httpx + BeautifulSoup4 | Latest | httpx = async HTTP client (faster than requests). BS4 = battle-tested HTML parser. No browser overhead needed for MVP. |
| **PDF parsing** | PyMuPDF (fitz) | Latest | Best Python PDF text extractor for resume formats. Handles multi-column layouts better than pdfplumber. |
| **Data validation** | Pydantic | v2 | Native to FastAPI. Defines the JSON contract between LLM output and API response. Strict validation = no bad data reaches the frontend. |
| **File storage** | Supabase Storage | Built-in | Resume PDF uploads stored in Supabase Storage bucket. Free 1GB. Direct URL access. No separate S3 needed. |
| **Frontend deployment** | Vercel | Free hobby tier | Zero-config Next.js deployment. URL in 2 minutes. |
| **Backend deployment** | Local (`localhost:8000`) | MVP | Per assignment spec. Phase 2: Railway or Render for hosted backend. |
| **Env management** | python-dotenv | Latest | Loads `.env` for backend. Vercel handles env vars for frontend. |

### Why NOT these alternatives:

| Rejected Option | Reason |
|----------------|--------|
| SQLite | Doesn't include auth. Adding Supabase later would require migration. Since we need auth, Supabase from day one is cleaner. |
| OpenAI GPT | More expensive than Gemini. User already has Google billing. |
| Azure AI Foundry | 30–60 min setup risk on a 1-week timeline. No pre-existing account. |
| Express/Node.js backend | Python is superior for AI agent code. All LLM/scraping/PDF libraries are Python-first. |
| Redux (state management) | Overkill for MVP. React Context + useState is sufficient for a single-user app. |
| Prisma ORM | Adds complexity. Supabase Python client + raw SQL via supabase-py is sufficient and faster to set up. |

---

## 9. File & Folder Structure

```
job-assistant/
│
├── README.md                        # How to run, env setup, architecture overview
├── status.md                        # 🔴 PROJECT STATUS — updated after every phase
├── Agent_Status.md                  # 🤖 AGENT ACTION LOG — updated after every agent task
├── .env.example                     # All required env var keys (no values committed)
├── .gitignore                       # Excludes: .env, __pycache__, .next, node_modules, *.db
│
│
├── frontend/                        # ─────────────── NEXT.JS APP ───────────────
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── components.json              # shadcn/ui config
│   │
│   ├── app/                         # Next.js App Router pages
│   │   ├── layout.tsx               # Root layout: global nav, auth check
│   │   ├── page.tsx                 # Root: redirect to /dashboard if logged in, else /login
│   │   │
│   │   ├── (auth)/                  # Auth route group — no nav bar
│   │   │   ├── login/
│   │   │   │   └── page.tsx         # Login form
│   │   │   └── register/
│   │   │       └── page.tsx         # Registration form
│   │   │
│   │   ├── (app)/                   # Protected route group — requires auth
│   │   │   ├── layout.tsx           # Checks Supabase session; redirects if not logged in
│   │   │   ├── onboarding/
│   │   │   │   └── page.tsx         # Multi-step profile wizard (shown once after register)
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx         # Application tracker dashboard
│   │   │   ├── resume/
│   │   │   │   └── page.tsx         # Resume scorer
│   │   │   ├── answers/
│   │   │   │   └── page.tsx         # Tailored answer generator
│   │   │   ├── autofill/
│   │   │   │   └── page.tsx         # Autofill preview tool
│   │   │   └── profile/
│   │   │       └── page.tsx         # Edit profile (same wizard, pre-filled)
│   │
│   ├── components/
│   │   │
│   │   ├── ui/                      # shadcn/ui base components (auto-generated via CLI)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── dialog.tsx           # Modal
│   │   │   ├── input.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── select.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── tooltip.tsx
│   │   │   └── skeleton.tsx         # Loading placeholder
│   │   │
│   │   ├── shared/                  # Reusable non-ui components
│   │   │   ├── Spinner.tsx          # Animated loading spinner
│   │   │   ├── AgentLoadingSteps.tsx  # Multi-step progress message during agent calls
│   │   │   ├── FeedbackButtons.tsx  # Thumbs up / thumbs down
│   │   │   ├── ScoreGauge.tsx       # Circular score gauge (0–100) with grade
│   │   │   ├── SkillTag.tsx         # Green (matched) or Red (missing) skill pill
│   │   │   └── EmptyState.tsx       # Empty state illustration + CTA
│   │   │
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   │
│   │   ├── profile/
│   │   │   ├── OnboardingWizard.tsx     # Container for all 4 steps + progress bar
│   │   │   ├── Step1PersonalInfo.tsx
│   │   │   ├── Step2WorkHistory.tsx     # Dynamic add/remove job rows
│   │   │   ├── Step3Education.tsx       # Dynamic add/remove education rows
│   │   │   └── Step4SkillsPrefs.tsx     # Tag input for skills + preference dropdowns
│   │   │
│   │   ├── resume/
│   │   │   ├── ResumeInput.tsx          # PDF upload OR paste text toggle
│   │   │   ├── JDInput.tsx              # URL OR paste text toggle
│   │   │   ├── ScoreReport.tsx          # Full score result display
│   │   │   ├── MatchedSkillsSection.tsx # Green/red skill tags
│   │   │   └── SuggestionList.tsx       # Numbered suggestion items
│   │   │
│   │   ├── answers/
│   │   │   ├── QuestionSelector.tsx     # Preset dropdown + custom text input
│   │   │   ├── AnswerDisplay.tsx        # Editable textarea with generated answer
│   │   │   └── JDContextInput.tsx       # JD text for answer context
│   │   │
│   │   ├── autofill/
│   │   │   ├── URLInput.tsx             # Job application URL input
│   │   │   ├── FieldMappingTable.tsx    # Table of all detected fields
│   │   │   └── ConfidenceBadge.tsx      # Color-coded confidence pill
│   │   │
│   │   └── dashboard/
│   │       ├── ApplicationTable.tsx     # Full application list table
│   │       ├── ApplicationRow.tsx       # Single row with inline status dropdown
│   │       ├── AddApplicationModal.tsx  # Modal form for adding new application
│   │       ├── StatusBadge.tsx          # Color-coded status pill
│   │       └── DashboardStats.tsx       # Summary cards (total, active, interviews, offers)
│   │
│   ├── services/
│   │   └── api.ts                   # ALL fetch calls to FastAPI backend (single file)
│   │                                # Pattern: one function per endpoint, typed inputs/outputs
│   │
│   ├── lib/
│   │   ├── supabase.ts              # Supabase client (browser) — createBrowserClient()
│   │   └── utils.ts                 # cn() utility for Tailwind class merging
│   │
│   ├── context/
│   │   ├── UserContext.tsx          # Global: current user + profile, loaded on app mount
│   │   └── ApplicationContext.tsx   # Global: applications list + CRUD actions
│   │
│   ├── hooks/
│   │   ├── useUser.ts               # Returns current user from UserContext
│   │   └── useApplications.ts       # Returns applications + actions from ApplicationContext
│   │
│   └── types/
│       └── index.ts                 # All shared TypeScript interfaces (UserProfile, Application, etc.)
│
│
├── backend/                         # ─────────────── FASTAPI APP ───────────────
│   ├── requirements.txt
│   ├── main.py                      # App entry point: create app, register routers, CORS, logging middleware
│   │
│   ├── routers/
│   │   ├── auth.py                  # POST /api/auth/verify — validate JWT, return user_id
│   │   ├── users.py                 # GET/POST/PATCH /api/users
│   │   ├── resume.py                # POST /api/resume/analyze
│   │   ├── answers.py               # POST /api/generate/answer
│   │   ├── applications.py          # CRUD /api/applications
│   │   ├── autofill.py              # POST /api/autofill
│   │   └── health.py                # GET /api/health
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── resume_scorer.py         # analyze_resume_and_jd() — full workflow
│   │   ├── answer_generator.py      # generate_tailored_answer() — full workflow
│   │   └── autofill_mapper.py       # map_fields_to_profile() — full workflow
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── scraper.py               # scrape_job_description(url) → str
│   │   │                            # scrape_form_fields(url) → list[FormField]
│   │   └── pdf_parser.py            # extract_text_from_pdf(file_bytes) → str
│   │
│   ├── prompts/                     # All LLM prompts as versioned text files
│   │   ├── resume_score_v1.txt
│   │   ├── answer_gen_v1.txt
│   │   └── autofill_v1.txt
│   │
│   ├── schemas/                     # Pydantic v2 models — the "contracts"
│   │   ├── __init__.py
│   │   ├── user.py                  # UserProfile, WorkHistoryItem, EducationItem
│   │   ├── resume.py                # ResumeScoreRequest, ResumeScoreResult
│   │   ├── answer.py                # AnswerRequest, AnswerResult
│   │   ├── application.py           # Application, CreateApplicationRequest, UpdateApplicationRequest
│   │   ├── autofill.py              # FormField, FieldMapping, AutofillResult
│   │   └── common.py                # AgentError, HealthCheckResult
│   │
│   ├── services/
│   │   ├── llm.py                   # call_gemini(prompt, max_tokens) → str
│   │   │                            # call_groq(prompt, max_tokens) → str (fallback)
│   │   │                            # parse_json_from_response(raw) → dict
│   │   │                            # load_prompt(filename) → str
│   │   └── supabase.py              # Supabase Python client setup, verify_jwt(token) → user_id
│   │
│   ├── middleware/
│   │   ├── auth.py                  # get_current_user() FastAPI dependency
│   │   │                            # Extracts Bearer token, calls verify_jwt(), returns user_id
│   │   └── logging.py               # Request/response logging middleware
│   │
│   └── tests/
│       ├── unit/
│       │   ├── test_scraper.py
│       │   ├── test_pdf_parser.py
│       │   ├── test_resume_scorer.py
│       │   ├── test_answer_gen.py
│       │   ├── test_autofill.py
│       │   └── test_schemas.py
│       └── integration/
│           ├── test_resume_api.py
│           ├── test_users_api.py
│           └── test_applications_api.py
│
│
└── docs/
    ├── architecture.md              # System diagram (text-based)
    └── api_reference.md             # All endpoints, request/response examples
```

---

## 10. Database Schema (Supabase / PostgreSQL)

All tables live in the `public` schema in Supabase. Supabase Auth manages the `auth.users` table separately — our `users` table references it via foreign key.

### Setup Note

In Supabase dashboard → SQL Editor, run these CREATE TABLE statements in order. Then enable Row Level Security (RLS) on each table and add policies (user can only read/write their own rows).

---

### `users` table

Stores the user's profile data. Links to `auth.users` via `id`.

```sql
CREATE TABLE users (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  -- WHY: id matches Supabase auth user ID so we can join them trivially
  email           TEXT UNIQUE NOT NULL,
  full_name       TEXT NOT NULL,
  phone           TEXT,
  location        TEXT,                    -- "Toronto, ON" or "Remote"
  linkedin_url    TEXT,
  portfolio_url   TEXT,                    -- GitHub, personal site, etc.
  skills          TEXT[] DEFAULT '{}',     -- PostgreSQL array of strings
  -- WHY TEXT[] not JSON: native array type is queryable and indexable
  preferences     JSONB DEFAULT '{}',
  -- preferences shape: { desired_roles: [], target_industries: [],
  --   remote_preference: "remote|hybrid|onsite", salary_min: int }
  -- WHY JSONB: flexible structure, no need for separate preferences table at MVP
  onboarding_complete BOOLEAN DEFAULT FALSE,
  -- WHY: lets the app know to redirect to /onboarding on first login
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: users can only read/write their own row
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON users FOR INSERT WITH CHECK (auth.uid() = id);
```

---

### `work_history` table

Normalized from `users` because a user can have multiple jobs and we want to query/update them independently.

```sql
CREATE TABLE work_history (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company         TEXT NOT NULL,
  role            TEXT NOT NULL,
  start_date      TEXT NOT NULL,           -- "2022-06" format (YYYY-MM)
  end_date        TEXT,                    -- NULL if is_current = TRUE
  is_current      BOOLEAN DEFAULT FALSE,
  bullets         TEXT[] DEFAULT '{}',     -- Array of responsibility strings
  display_order   INTEGER DEFAULT 0,       -- For ordering in UI
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE work_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own work history" ON work_history
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
```

---

### `education` table

```sql
CREATE TABLE education (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  institution     TEXT NOT NULL,
  degree          TEXT NOT NULL,           -- "Bachelor of Science", "Master of Arts", etc.
  field_of_study  TEXT,                    -- "Computer Science"
  graduation_year INTEGER,
  gpa             DECIMAL(3,2),            -- Optional, e.g. 3.85
  display_order   INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE education ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own education" ON education
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
```

---

### `applications` table

Tracks every job application the user has added to their pipeline.

```sql
CREATE TABLE applications (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company         TEXT NOT NULL,
  role            TEXT NOT NULL,
  jd_url          TEXT,
  jd_text         TEXT,                    -- Cached scraped JD (avoid re-scraping)
  status          TEXT NOT NULL DEFAULT 'saved'
                  CHECK (status IN (
                    'saved', 'submitted', 'response_received',
                    'interview_requested', 'interview_completed',
                    'onsite_requested', 'offer_received',
                    'rejected', 'withdrawn'
                  )),
  notes           TEXT,                    -- Free-form notes (recruiter name, next steps)
  date_applied    DATE,
  last_score      INTEGER,                 -- Most recent resume match score (0–100), optional
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own applications" ON applications
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Index for common queries
CREATE INDEX idx_applications_user_status ON applications(user_id, status);
CREATE INDEX idx_applications_updated ON applications(user_id, updated_at DESC);
```

---

### `agent_feedback` table

Stores thumbs up/down feedback on AI outputs. Used for future quality improvement.

```sql
CREATE TABLE agent_feedback (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  agent_type      TEXT NOT NULL            -- 'resume_scorer' | 'answer_generator' | 'autofill'
                  CHECK (agent_type IN ('resume_scorer', 'answer_generator', 'autofill')),
  rating          INTEGER NOT NULL CHECK (rating IN (1, -1)),  -- 1 = thumbs up, -1 = thumbs down
  context         JSONB DEFAULT '{}',      -- Optional: store question asked, score received, etc.
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE agent_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can insert own feedback" ON agent_feedback
  FOR INSERT WITH CHECK (auth.uid() = user_id);
```

---

### Supabase Storage Bucket

In Supabase dashboard → Storage, create a private bucket named `resumes`.

```sql
-- Storage bucket policy: users can only access their own files
-- File path convention: {user_id}/resume_{timestamp}.pdf
```

---

### Trigger: auto-update `updated_at`

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 11. Authentication Design

### How it works (end-to-end)

```
REGISTRATION:
  1. User fills register form (email + password)
  2. Frontend calls: supabase.auth.signUp({ email, password })
  3. Supabase creates auth.users entry → sends confirmation email (optional)
  4. Supabase returns: { user: {id, email}, session: {access_token, refresh_token} }
  5. Frontend stores session (Supabase SDK handles this automatically in localStorage)
  6. Frontend calls: POST /api/users with { id: user.id, email, full_name: "" }
     → creates empty users row linked to auth.users.id
  7. Frontend redirects to /onboarding

LOGIN:
  1. User fills login form
  2. Frontend calls: supabase.auth.signInWithPassword({ email, password })
  3. Supabase returns session with JWT access_token (expires in 1 hour)
  4. Frontend: Supabase SDK auto-refreshes token via refresh_token
  5. Frontend redirects to /dashboard

PROTECTED API CALLS:
  1. Frontend: services/api.ts gets current session
     const { data: { session } } = await supabase.auth.getSession()
  2. Frontend adds header: Authorization: Bearer {session.access_token}
  3. FastAPI middleware (middleware/auth.py):
     async def get_current_user(authorization: str = Header(...)):
       token = authorization.replace("Bearer ", "")
       payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"],
                            audience="authenticated")
       return payload["sub"]  # This is the user_id (UUID)
  4. All protected routes use: user_id: str = Depends(get_current_user)

LOGOUT:
  1. Frontend calls: supabase.auth.signOut()
  2. Supabase clears session from localStorage
  3. Frontend redirects to /login

SESSION PERSISTENCE:
  - Supabase SDK stores session in localStorage automatically
  - On app mount: supabase.auth.getSession() returns existing session if not expired
  - On expiry: SDK uses refresh_token to get new access_token transparently
```

### FastAPI auth middleware (`backend/middleware/auth.py`)

```python
from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError
import os

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

async def get_current_user(authorization: str = Header(...)) -> str:
    """
    FastAPI dependency. Extracts and validates the Supabase JWT.
    Returns the user_id (UUID string) from the token payload.
    Raises 401 if token is missing, expired, or invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user ID")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")

# Usage in any router:
# @router.get("/protected")
# async def protected_route(user_id: str = Depends(get_current_user)):
#     ...
```

---

## 12. API Design

**Base URL (local):** `http://localhost:8000`
**All protected routes require:** `Authorization: Bearer <supabase_jwt>`
**All responses:** `Content-Type: application/json`
**All error responses follow:**
```json
{ "error": "<error_code>", "message": "<human-readable message>", "detail": "<optional debug info>" }
```

---

### Health

#### `GET /api/health` — Public
Returns system status. No auth required. Used to verify the backend is running.

**Response (200):**
```json
{
  "status": "ok",
  "database": "connected",
  "llm": "reachable",
  "version": "1.0.0",
  "timestamp": "2026-04-19T10:00:00Z"
}
```

---

### Users

#### `POST /api/users` — Protected
Create user profile row after registration. Called once, immediately after Supabase auth signup.

**Request:**
```json
{
  "id": "uuid-from-supabase-auth",
  "email": "jane@example.com",
  "full_name": "Jane Smith"
}
```

**Response (201):** Minimal `UserProfile` with `onboarding_complete: false`

---

#### `GET /api/users/me` — Protected
Get the current user's full profile (all sections).

**Response (200):**
```json
{
  "id": "uuid",
  "email": "jane@example.com",
  "full_name": "Jane Smith",
  "phone": "416-555-0100",
  "location": "Toronto, ON",
  "linkedin_url": "https://linkedin.com/in/janesmith",
  "portfolio_url": "https://github.com/janesmith",
  "skills": ["Python", "React", "SQL", "FastAPI"],
  "preferences": {
    "desired_roles": ["Backend Engineer", "ML Engineer"],
    "remote_preference": "hybrid",
    "salary_min": 85000
  },
  "work_history": [
    {
      "id": "uuid",
      "company": "Acme Corp",
      "role": "Software Engineer",
      "start_date": "2022-06",
      "end_date": null,
      "is_current": true,
      "bullets": [
        "Built REST API endpoints serving 50K requests/day using FastAPI and PostgreSQL",
        "Reduced query latency by 40% via database indexing and query optimization"
      ],
      "display_order": 0
    }
  ],
  "education": [
    {
      "id": "uuid",
      "institution": "University of Toronto",
      "degree": "Bachelor of Science",
      "field_of_study": "Computer Science",
      "graduation_year": 2022,
      "gpa": 3.8,
      "display_order": 0
    }
  ],
  "onboarding_complete": true,
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-10T14:30:00Z"
}
```

---

#### `PATCH /api/users/me` — Protected
Update any subset of profile fields. Used by both onboarding wizard and profile edit page.

**Request:** Any subset of `UserProfile` fields. For nested arrays (work_history, education), the full array is replaced on each PATCH — frontend sends the complete updated array, not a delta.

**Response (200):** Updated `UserProfile`

---

### Resume Scorer

#### `POST /api/resume/analyze` — Protected
Run the resume scorer agent. Accepts PDF file upload or text.

**Request (`multipart/form-data`):**
```
# Option A: PDF upload
resume_file: <PDF binary>
jd_url:      "https://greenhouse.io/jobs/12345"   (OR jd_text: "...")

# Option B: Text input
resume_text: "Jane Smith\nSoftware Engineer..."
jd_text:     "We are looking for a backend engineer..."
```

**Response (200):**
```json
{
  "match_score": 74,
  "grade": "B",
  "summary": "Strong technical match, but missing infrastructure/deployment keywords that appear 4+ times in the JD.",
  "matched_skills": ["Python", "REST APIs", "SQL", "React"],
  "missing_skills": ["Kubernetes", "Terraform", "CI/CD"],
  "suggestions": [
    "Add any CI/CD experience (GitHub Actions, Jenkins) to your most recent role",
    "Mention cloud platform explicitly — the JD references AWS 4 times",
    "Quantify achievements: 'built APIs' → 'built 12 REST endpoints serving 50K req/day'"
  ],
  "jd_key_requirements": ["Python", "Kubernetes", "SQL", "REST APIs", "CI/CD", "AWS"],
  "ats_risk": "medium",
  "ats_risk_reason": "Missing 3 of 6 high-frequency JD keywords. ATS may filter before human review."
}
```

**Response (422) — Validation error:**
```json
{ "error": "invalid_input", "message": "Must provide either resume_file or resume_text" }
```

**Response (503) — LLM unavailable:**
```json
{ "error": "llm_unavailable", "message": "AI service temporarily unavailable. Please try again in 30 seconds." }
```

---

### Answer Generator

#### `POST /api/generate/answer` — Protected

**Request:**
```json
{
  "question": "Why are you a good fit for this role?",
  "jd_text": "We're looking for a backend engineer with Python experience...",
  "jd_url": null
}
```

**Note:** `user_id` is NOT passed in the request body — it is extracted from the JWT by FastAPI middleware. The backend fetches the full profile from Supabase using `user_id`.

**Response (200):**
```json
{
  "answer": "Throughout my two years at Acme Corp, I've built...",
  "word_count": 287,
  "question": "Why are you a good fit for this role?"
}
```

---

### Applications

#### `GET /api/applications` — Protected
Returns all applications for the authenticated user, sorted by `updated_at` descending.

**Query params:** `?status=interview_requested` (optional filter)

**Response (200):** `list[Application]`

---

#### `POST /api/applications` — Protected
Add a new application to the tracker.

**Request:**
```json
{
  "company": "Stripe",
  "role": "Backend Engineer",
  "jd_url": "https://stripe.com/jobs/123",
  "status": "submitted",
  "notes": "Applied via LinkedIn. Recruiter is Sarah Chen.",
  "date_applied": "2026-04-19"
}
```

**Response (201):** `Application`

---

#### `PATCH /api/applications/{id}` — Protected
Update status, notes, or other fields.

**Request:**
```json
{ "status": "interview_requested", "notes": "Phone screen scheduled for April 25 at 2pm" }
```

**Response (200):** Updated `Application`

---

#### `DELETE /api/applications/{id}` — Protected
Remove an application.

**Response (204):** No content.

---

### Autofill

#### `POST /api/autofill` — Protected

**Request:**
```json
{ "page_url": "https://jobs.greenhouse.io/acmecorp/apply" }
```

**Note:** `user_id` from JWT → backend fetches profile automatically.

**Response (200):**
```json
{
  "fill_rate": 0.82,
  "total_fields": 17,
  "mapped_fields": 14,
  "mappings": [
    {
      "field_id": "FirstName",
      "field_label": "First Name",
      "field_type": "text",
      "profile_key": "full_name",
      "suggested_value": "Jane",
      "confidence": 0.97
    }
  ],
  "unfilled_fields": ["cover_letter", "salary_expectation_text"]
}
```

---

### Feedback

#### `POST /api/feedback` — Protected
Log thumbs up/down on any agent output.

**Request:**
```json
{
  "agent_type": "resume_scorer",
  "rating": 1,
  "context": { "match_score": 74, "jd_url": "https://..." }
}
```

**Response (201):** `{ "status": "logged" }`

---

## 13. Frontend: Screens & Components

### Screen 1: Login (`/login`)

Simple centered card. Email + password fields. "Sign in" button. Link to Register.

**Behavior:**
- On submit: `supabase.auth.signInWithPassword()`
- On success: redirect to `/dashboard`
- On error: show inline error ("Invalid email or password")
- If already logged in: redirect to `/dashboard` immediately

---

### Screen 2: Register (`/register`)

Email + password + confirm password. "Create account" button. Link to Login.

**Behavior:**
- On submit: `supabase.auth.signUp()` → `POST /api/users` to create profile row
- On success: redirect to `/onboarding`
- Password validation: min 8 chars, must match confirm password (client-side)

---

### Screen 3: Onboarding Wizard (`/onboarding`)

**Only shown once** — when `user.onboarding_complete === false`. After completion, `PATCH /api/users/me` sets `onboarding_complete: true`.

Progress bar at top showing step 1/4, 2/4, etc.

| Step | Title | Key Interactions |
|------|-------|-----------------|
| 1 | Personal Info | Standard form fields. Auto-fills email from auth. |
| 2 | Work History | Dynamic list — "Add Job" button appends a new row. Each row: company, title, dates, bullet points textarea. "Remove" button per row. |
| 3 | Education | Same dynamic pattern as work history. |
| 4 | Skills & Preferences | Skill tags: type a skill, press Enter to add pill. Remove via ✕ on pill. Dropdowns for remote preference, desired roles. |

Each step: "Save & Continue" button → calls `PATCH /api/users/me` with that step's data → navigates to next step.

Final step: "Complete Profile" → sets `onboarding_complete: true` → redirects to `/dashboard`.

---

### Screen 4: Dashboard (`/dashboard`)

**Layout:** Two sections stacked vertically.

**Section A: Summary Cards (row of 4)**
- Total Applications | Active (non-rejected/withdrawn) | Interviews | Offers
- Each card shows a number and a label. Clicking filters the table below.

**Section B: Quick Actions (row of buttons)**
- "Score My Resume" → navigates to `/resume`
- "Generate Answer" → navigates to `/answers`
- "Autofill Preview" → navigates to `/autofill`
- "Add Application" → opens `AddApplicationModal`

**Section C: Application Table**

Columns: Company | Role | Date Applied | Status | Last Updated | Actions

- **Status column:** Inline `<StatusDropdown>` — clicking opens a select, change auto-saves via `PATCH /api/applications/{id}`
- **Actions column:** "View JD" (opens URL in new tab) | "Edit" (opens edit modal) | "Delete" (confirm dialog)
- **Sorting:** Click column header to sort ascending/descending
- **Filtering:** Tab bar above table: All | Active | Interviews | Offers | Rejected
- **Empty state:** "You haven't added any applications yet. Start by adding your first one!"

---

### Screen 5: Resume Scorer (`/resume`)

**Layout:** Two-column on desktop, stacked on mobile.

**Left column: Inputs**
1. Resume input: Toggle between "Upload PDF" and "Paste Text". PDF upload uses drag-and-drop zone with file type validation.
2. JD input: Toggle between "Paste URL" and "Paste Text".
3. "Analyze Resume" button → disabled until both inputs have content.

**Loading state:**
`<AgentLoadingSteps>` component cycles through messages:
- "Fetching job description..." (if URL provided)
- "Extracting resume text..." (if PDF)
- "Analyzing keyword match..."
- "Generating suggestions..."

**Right column: Results** (appears after analysis)
1. `<ScoreGauge>` — large circular dial, animated fill to score, grade badge in center
2. ATS Risk badge (low/medium/high) with tooltip
3. Summary paragraph
4. "Matched Skills" section — green `<SkillTag>` per matched skill
5. "Missing Skills" section — red `<SkillTag>` per gap
6. "How to Improve" numbered list — each suggestion is a card with copy button
7. `<FeedbackButtons>` at bottom

---

### Screen 6: Answer Generator (`/answers`)

**Layout:** Single column, centered, max-width 700px.

1. **JD context:** Small text area or URL input (optional — "Add job description for better results")
2. **Question selector:** Dropdown with 6 presets + "Custom" option. Custom shows a text area.
3. **"Generate Answer" button** → disabled until question is selected.
4. **Loading state:** Single spinner + "Writing your answer..."
5. **Result:**
   - Editable `<textarea>` pre-populated with generated answer
   - Word count badge (live updates as user edits)
   - Action row: "Copy to Clipboard" | "Regenerate" | feedback buttons
   - Note: "This answer was written using your profile. Edit it to add personal touches before submitting."

---

### Screen 7: Autofill Preview (`/autofill`)

1. URL input + "Detect Fields" button
2. Loading: "Scraping application form..." → "Mapping your profile..."
3. Results:
   - Fill rate progress bar ("82% of fields mapped")
   - `<FieldMappingTable>` with rows:
     | Field Label | Detected Type | Mapped Value | Confidence |
     Each row color-coded by confidence tier (green/yellow/red)
   - Red rows show placeholder "Review needed — click to edit"
   - "Unfilled Fields" list below table
4. Instructional note: "Review these mappings, then copy the values to your application form. Browser autofill is coming in a future update."

---

### Screen 8: Profile (`/profile`)

Same `<OnboardingWizard>` component, but pre-filled with existing data. All 4 steps accessible via tabs (not linear).

"Save Changes" per step → calls `PATCH /api/users/me`.

---

### Agentic UX Principles (from assignment)

| Principle | How it's implemented in this app |
|-----------|----------------------------------|
| **Show the work** | `<AgentLoadingSteps>` shows step-by-step progress during every agent call. Never just a spinner. |
| **Allow intervention** | Every AI output is editable before use. No auto-submission. User is always in control. |
| **Collect feedback** | Thumbs up/down on every AI result screen. Posted to `/api/feedback` and stored in DB. |
| **Graceful degradation** | If scraping fails → show paste-text fallback. If LLM fails → show specific error + retry button. |
| **Confidence display** | Autofill shows per-field confidence with color coding. User knows exactly what to trust. |
| **AI as co-pilot, not pilot** | All agent outputs are suggestions. App never takes irreversible action on user's behalf. |

---

## 14. State Management Strategy

### Frontend

**`UserContext`** (`context/UserContext.tsx`):
- Stores: current auth session, user profile (from `GET /api/users/me`)
- Populated on: app mount via `useEffect` that calls `supabase.auth.getSession()` + `GET /api/users/me`
- Accessible via: `useUser()` hook from anywhere in the app
- Updates when: profile is saved in onboarding or profile edit page

**`ApplicationContext`** (`context/ApplicationContext.tsx`):
- Stores: applications array
- Populated on: dashboard mount via `GET /api/applications`
- Actions: `addApplication()`, `updateApplication()`, `deleteApplication()` — each calls the API and updates local state optimistically
- Why optimistic updates: status changes on the dashboard should feel instant. If the API call fails, roll back and show an error toast.

**Page-level state** (via `useState`):
- Form values, loading states, error messages, agent results
- Not shared globally — scoped to the page component

### Backend

**Stateless.** Every request is fully self-contained.
- `user_id` extracted from JWT on every request — no server-side session
- Profile data fetched from Supabase on each agent call that needs it
- No in-memory caching for MVP (add Redis in Phase 2 if latency becomes an issue)

---

## 15. Prompt Engineering

### Principles applied

1. **Persona framing** — system prompt sets the model's role explicitly
2. **Few-shot examples** — one complete input/output example in the prompt dramatically improves JSON reliability
3. **Explicit output format** — exact JSON schema specified in the prompt, not left to inference
4. **Banned phrases** — explicitly listed phrases the model must not use
5. **Constraint-first** — constraints stated before the task, not after
6. **Prompt versioning** — all prompts in `/backend/prompts/` as `v1.txt`, `v2.txt`, etc.

### Calling Gemini from Python

```python
# backend/services/llm.py

import google.generativeai as genai
import os
import json
import re
import logging

genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def call_gemini(prompt: str, max_tokens: int = 1500) -> str:
    """
    Send a prompt to Gemini 2.5 Flash.
    Returns raw response text.
    Raises LLMError on timeout or API failure.
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,       # Low temp for structured output reliability
                response_mime_type="application/json"  # Forces JSON output mode
            )
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini API error: {str(e)}")
        raise LLMError("llm_unavailable", str(e))

def parse_json_from_response(raw: str) -> dict:
    """
    Safely extract JSON from LLM response.
    Handles: clean JSON, JSON wrapped in ```json fences, JSON with preamble text.
    """
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    
    # Try stripping markdown code fences
    cleaned = re.sub(r"```json\n?|```\n?", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try finding JSON object/array anywhere in the response
    match = re.search(r'\{.*\}|\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    raise JSONParseError(f"Could not extract valid JSON from response: {raw[:200]}")

def load_prompt(filename: str) -> str:
    """Load a prompt template from /backend/prompts/"""
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", filename)
    with open(path, "r") as f:
        return f.read()
```

---

## 16. Security Considerations

| Risk | Severity | Mitigation |
|------|----------|------------|
| API key in client-side code | Critical | All keys in `.env` (backend) and Vercel env vars (frontend). Never in source code. `.env` in `.gitignore`. |
| JWT forged or replayed | High | FastAPI middleware validates JWT signature against Supabase JWT secret. Token expiry enforced (1 hour). |
| User accesses another user's data | High | Supabase RLS policies enforce at DB level. FastAPI middleware enforces at API level. Double protection. |
| Prompt injection via JD text | Medium | JD text is sanitized before prompt injection: strip HTML tags, limit to 4000 chars, no special tokens. |
| PDF malware upload | Medium | Validate MIME type server-side (`application/pdf`). Use PyMuPDF in read-only mode (no execution). Store in Supabase Storage (isolated). |
| CORS abuse | Medium | FastAPI CORS middleware: `allow_origins=["http://localhost:3000"]` in dev. Change to Vercel URL in prod. |
| LLM cost runaway | Low | Gemini Flash is cheap. Add rate limiting on `/api/resume/analyze` (max 20 calls/hour/user) to prevent abuse. |
| Scraper fetching malicious URLs | Low | Validate URL format before scraping. Timeout after 10 seconds. Only scrape HTTP/HTTPS. |

---

## 17. Logging & Observability

### Log format (structured JSON — every line)

```json
{
  "timestamp": "2026-04-19T10:00:00.000Z",
  "level": "INFO",
  "module": "resume_scorer",
  "event": "analyze_complete",
  "user_id": "uuid",
  "duration_ms": 4821,
  "details": {
    "match_score": 74,
    "input_tokens": 2841,
    "output_tokens": 412,
    "jd_source": "url",
    "resume_source": "pdf"
  }
}
```

### What is logged

| Event | Level | Details |
|-------|-------|---------|
| Incoming API request | INFO | method, path, user_id, timestamp |
| Agent start | INFO | agent_name, user_id, input sizes |
| LLM call | INFO | model, input_tokens, output_tokens, duration_ms |
| Agent complete | INFO | agent_name, duration_ms, success |
| Scrape attempt | INFO | url, success/failure, content_length |
| JSON parse failure | WARN | raw_response (first 200 chars), retry attempt number |
| LLM retry | WARN | reason, retry_count |
| Auth failure | WARN | reason, request_path |
| Any exception | ERROR | full stack trace, user_id, endpoint |
| Agent failure after retries | ERROR | agent_name, error_code, user_id |

### Where logs go

- **Development:** stdout (visible in terminal)
- **Persistent:** `backend/logs/app.log` (structured JSON, one line per event)
- **Future:** integrate Sentry or LogTail for error alerting (Phase 2)

### Health check implementation

```python
# backend/routers/health.py

@router.get("/api/health")
async def health_check():
    # Check DB connection
    try:
        supabase.table("users").select("id").limit(1).execute()
        db_status = "connected"
    except Exception:
        db_status = "error"
    
    # Check LLM reachability (simple ping)
    try:
        call_gemini("respond with 'ok'", max_tokens=10)
        llm_status = "reachable"
    except Exception:
        llm_status = "error"
    
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "llm": llm_status,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

---

## 18. Edge Cases & Failure Handling

Every agent failure surfaces a human-readable message in the frontend. Never show a raw error.

| Scenario | Agent | Response | Frontend Display |
|----------|-------|----------|-----------------|
| JD URL returns 403/blocked | Resume Scorer | `{"error": "jd_scrape_failed"}` | "We couldn't access that URL. Please paste the job description text instead." + show paste input |
| PDF is a scanned image (no text layer) | Resume Scorer | `{"error": "pdf_no_text"}` | "This PDF appears to be a scanned image. Please paste your resume text instead." |
| LLM returns invalid JSON after 2 attempts | All agents | `{"error": "parse_failed"}` | "Something went wrong with the AI response. Please try again." + retry button |
| LLM API timeout (>30s) | All agents | `{"error": "llm_timeout"}` | "The AI is taking too long. Please try again in a moment." |
| Gemini rate limit hit | All agents | Switch to Groq fallback; if Groq also fails → `{"error": "llm_unavailable"}` | "AI service is temporarily busy. Try again in 30 seconds." |
| User profile is empty (no work history) | Answer Generator | Proceed with partial data; flag in prompt | Generated answer includes note: "Add work history to your profile for more personalized answers" |
| Resume text too long (>8000 chars) | Resume Scorer | Truncate to last 6000 chars + log warning | No user-facing message (transparent truncation) |
| Autofill URL requires JavaScript rendering | Autofill | Returns partial/no fields | "We detected [N] fields. Some fields may have been missed — this page uses JavaScript rendering." |
| User submits empty form | All | 422 Pydantic validation error | Per-field validation messages inline in form |
| Application status update fails | Dashboard | Roll back optimistic update | Toast: "Failed to update status. Please try again." |
| Auth token expired mid-session | All | 401 from FastAPI middleware | Frontend catches 401 → calls `supabase.auth.refreshSession()` → retries request once |

---

## 19. Testing Strategy

### Unit Tests (`/backend/tests/unit/`)

| Test File | Coverage |
|-----------|---------|
| `test_scraper.py` | `scrape_job_description()` returns >100 chars for 3 test URLs (LinkedIn job page, Indeed, direct Greenhouse). Returns empty string gracefully when URL is blocked. |
| `test_pdf_parser.py` | `extract_text_from_pdf()` returns non-empty string for sample_resume.pdf. Returns empty string for scanned PDF. Rejects non-PDF bytes. |
| `test_resume_scorer.py` | `analyze_resume_and_jd()` returns valid `ResumeScoreResult` for mock LLM response. Score is int 0–100. Grade is one of A/B/C/D/F. Suggestions is non-empty list. |
| `test_answer_gen.py` | `generate_tailored_answer()` returns >100 word answer. Does not contain banned phrases. Does not start with "Certainly!" or "As an AI". |
| `test_autofill.py` | Rule-based mapper correctly maps "First Name" → `first_name`, "Email" → `email`, "LinkedIn" → `linkedin_url`. Unknown field returns `confidence < 0.5`. |
| `test_schemas.py` | `ResumeScoreResult` rejects score > 100. Rejects missing required fields. Accepts valid data. |
| `test_llm_service.py` | `parse_json_from_response()` correctly parses: raw JSON, JSON in code fences, JSON with preamble text. Raises `JSONParseError` on garbage input. |
| `test_auth.py` | `get_current_user()` returns user_id for valid JWT. Raises 401 for expired JWT. Raises 401 for missing header. |

### Integration Tests (`/backend/tests/integration/`)

| Test | What it verifies |
|------|-----------------|
| `test_resume_api.py` | `POST /api/resume/analyze` with mock LLM response → 200 + valid `ResumeScoreResult` shape |
| `test_users_api.py` | Create user → fetch user → update user → verify all fields round-trip correctly |
| `test_applications_api.py` | Create → read all → update status → delete → verify deletion |
| `test_health.py` | `GET /api/health` returns 200 with `status: "ok"` |

### Frontend Manual QA Checklist

Run this before any submission. Check each item:

**Auth:**
- [ ] Register with new email → redirects to /onboarding
- [ ] Login with same email → redirects to /dashboard
- [ ] Unauthenticated visit to /dashboard → redirects to /login
- [ ] Logout → session cleared → /login page

**Onboarding:**
- [ ] Complete all 4 steps → data persists to backend
- [ ] Refresh mid-wizard → previous step data still present
- [ ] Skip to /dashboard after onboarding → profile shows correct data

**Resume Scorer:**
- [ ] PDF upload → analyze → receive score
- [ ] Text paste → URL → analyze → receive score
- [ ] Invalid PDF → helpful error message
- [ ] Blocked URL → paste fallback shown
- [ ] Score gauge animates to correct value
- [ ] Green/red skill tags display correctly

**Answer Generator:**
- [ ] Select preset question → generate → receive personalized answer
- [ ] Custom question → generate → receive answer
- [ ] Answer contains user's actual company/role name (not generic)
- [ ] Edit answer inline → copy to clipboard works

**Autofill:**
- [ ] Paste Greenhouse URL → detect fields → show mapping table
- [ ] Confidence colors display correctly (green/yellow/red)

**Dashboard:**
- [ ] Add application → appears in table
- [ ] Change status inline → updates without page reload
- [ ] Filter by status → shows correct applications
- [ ] Delete application → confirm dialog → removed from table
- [ ] Summary cards show correct counts

**General:**
- [ ] No API keys visible in browser DevTools → Network tab
- [ ] `GET /api/health` returns 200
- [ ] `status.md` and `Agent_Status.md` are up to date

---

## 20. Agent Status Tracking Protocol

**This is non-negotiable.** Every Cursor agent window or AI coding session MUST update both files after completing any task. This enables seamless handoff between sessions, between AI tools (Cursor → Claude Code → GPT), and between work days.

---

### `status.md` — Project Health File

**Location:** `/status.md` (project root)
**Purpose:** Anyone (human or AI) picking up this project reads this first. It answers: "Where are we? What works? What's next?"

**Template:**
```markdown
# Project Status

**Last Updated:** YYYY-MM-DD HH:MM UTC
**Updated By:** <Agent Window Name / Developer>
**Current Phase:** Phase X — <Phase Name>
**Progress:** X of 12 phases complete

## ✅ Completed Phases
- [x] Phase 1: Repo scaffold + folder structure
- [x] Phase 2: Supabase project setup + DB schema

## 🔄 In Progress
- [ ] Phase 3: FastAPI app + Supabase client (50% done — routers not yet wired)

## ⏳ Not Started
- Phases 4–12

## 🚨 Current Blockers
- None / <describe blocker>

## ⚠️ Known Issues
- Gemini JSON parse sometimes fails on resume score — added retry logic (see Phase 7 notes)

## 🔗 How to Run (always keep this accurate)
\`\`\`bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
# → http://localhost:3000
\`\`\`

## 🔑 Env Vars Needed
See .env.example — copy to .env and fill in:
- GOOGLE_GEMINI_API_KEY
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_JWT_SECRET
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY
```

---

### `Agent_Status.md` — Granular Agent Action Log

**Location:** `/Agent_Status.md` (project root)
**Purpose:** Logs every task completed by every agent. Enables any AI to pick up exactly where the last one left off. This is the memory layer between sessions.

**Rule: APPEND a new entry after EVERY completed task. Never delete old entries.**

**Entry template:**
```markdown
---

## Entry [N]
**Timestamp:** YYYY-MM-DD HH:MM UTC
**Agent:** <Cursor Window 1: Backend-DB / Claude Code / Developer>
**Phase:** Phase X — <Phase Name>
**Task:** <One-line description of what was done>

### Actions Taken
- Created `backend/services/supabase.py` with Supabase Python client setup
- Implemented `verify_jwt(token)` function using python-jose
- Tested with a manually generated Supabase JWT — works correctly

### Files Created or Modified
| File | Action | Notes |
|------|--------|-------|
| `backend/services/supabase.py` | Created | Supabase client + JWT verification |
| `backend/middleware/auth.py` | Created | FastAPI `get_current_user` dependency |
| `backend/requirements.txt` | Modified | Added: supabase, python-jose[cryptography] |

### Current State of This Thread
- Supabase Python client initialized and working
- JWT verification tested with valid token → returns user_id correctly
- JWT verification tested with expired token → raises 401 correctly

### Next Step for This Thread
- Wire `get_current_user` dependency into all protected routers
- Test with actual frontend JWT (Phase 11)

### Assumptions Made
- Supabase project URL and anon key are in .env (see .env.example)
- JWT algorithm is HS256 (Supabase default)

### Watch Out For
- JWT secret is in Supabase dashboard → Settings → API → JWT Settings
- Do NOT use the anon key as the JWT secret — they are different values
```

---

### Cursor Window Starter Prompts

Use these verbatim to start each Cursor agent window. The preamble forces the agent to read context before touching code.

**All windows — opening instruction:**
```
BEFORE DOING ANYTHING ELSE:
1. Read /status.md — understand the current project state
2. Read /Agent_Status.md — read the last 3 entries to understand recent changes
3. Read /README.md — understand the project setup
Only then proceed with your assigned task.
When you complete your task, update /Agent_Status.md (append new entry) and /status.md (update progress).
```

**Window: Backend-Foundation (Phase 2–4)**
```
[Read context first per above instructions]
Your scope: backend/ directory only.
Your task: Phase 2 — Set up Supabase Python client, run SQL schema in Supabase dashboard, create FastAPI app skeleton with all routers returning mock data.
Do not touch: frontend/ directory.
```

**Window: Backend-Agents (Phase 7–9)**
```
[Read context first per above instructions]
Phases 5 and 6 must show as complete in Agent_Status.md before you begin.
Your scope: backend/agents/, backend/tools/, backend/prompts/, backend/services/llm.py
Your task: Build the resume scorer agent, scraper tool, and PDF parser tool.
Do not touch: frontend/, backend/routers/ (those are already wired).
```

**Window: Frontend-Static (Phase 10)**
```
[Read context first per above instructions]
Your scope: frontend/ directory only.
Your task: Phase 10 — Build ALL static React components with hardcoded mock data. Do NOT make any API calls. Use mock JSON objects for all data.
Goal: Every screen should be visually complete and navigable before backend integration.
Do not touch: backend/ directory.
```

**Window: Integration (Phase 11)**
```
[Read context first per above instructions]
All of Phases 1–10 must show as complete in Agent_Status.md before you begin.
Your scope: frontend/services/api.ts, frontend/context/, frontend/app/(app)/
Your task: Replace all mock data with real API calls. Wire every page to its backend endpoint.
```

---

## 21. Milestone & Phase Breakdown

12 small phases. Each phase is completable in 2–4 hours. Designed so each Cursor window handles one phase at a time.

**Rule:** Do not start Phase N+1 until Phase N is checked off and `Agent_Status.md` is updated.

---

### Phase 1 — Repo Scaffold (Day 1 AM, ~1.5 hours)

**Window: Setup**

- [ ] Create GitHub repo (public or private)
- [ ] Initialize Next.js 14: `npx create-next-app@latest frontend --typescript --tailwind --app`
- [ ] Initialize backend: `mkdir backend && cd backend && pip install fastapi uvicorn python-dotenv`
- [ ] Create complete folder structure per Section 9 (all dirs and empty `__init__.py` files)
- [ ] Create `.env.example` with all keys listed but no values (see Section 27)
- [ ] Create `/status.md` with initial entry
- [ ] Create `/Agent_Status.md` with Entry 1
- [ ] Verify: `cd frontend && npm run dev` → localhost:3000 loads
- [ ] Verify: `cd backend && uvicorn main:app --reload` → localhost:8000 loads

**✅ Done when:** Both apps run, folder structure matches Section 9, status files exist.

---

### Phase 2 — Supabase Setup (Day 1 AM, ~1.5 hours)

**Window: Backend-DB**

- [ ] Create Supabase project at supabase.com (free tier)
- [ ] Run all SQL from Section 10 in Supabase SQL Editor (in order: users → work_history → education → applications → agent_feedback → triggers)
- [ ] Enable RLS + add policies per Section 10
- [ ] Create `resumes` Storage bucket (private)
- [ ] Get credentials from Supabase dashboard: URL, anon key, JWT secret
- [ ] Create `.env` from `.env.example` and fill in Supabase values
- [ ] Install: `pip install supabase python-jose[cryptography]`
- [ ] Create `backend/services/supabase.py` — initialize Supabase Python client
- [ ] Test: simple `supabase.table("users").select("*").execute()` returns empty list (not an error)
- [ ] Create `backend/middleware/auth.py` — `get_current_user()` dependency (Section 11)
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** Supabase tables exist, RLS enabled, Python client connects, `verify_jwt()` works.

---

### Phase 3 — Pydantic Schemas (Day 1 PM, ~1 hour)

**Window: Backend-Schemas**

- [ ] Create all schemas in `backend/schemas/` per Section 10 and API Design section
- [ ] `user.py`: `WorkHistoryItem`, `EducationItem`, `UserProfile`, `UpdateUserRequest`
- [ ] `resume.py`: `ResumeScoreRequest`, `ResumeScoreResult`
- [ ] `answer.py`: `AnswerRequest`, `AnswerResult`
- [ ] `application.py`: `Application`, `CreateApplicationRequest`, `UpdateApplicationRequest`
- [ ] `autofill.py`: `FormField`, `FieldMapping`, `AutofillResult`
- [ ] `common.py`: `AgentError`, `HealthCheckResult`
- [ ] Write `tests/unit/test_schemas.py`: validate that bad data raises `ValidationError`, good data passes
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** All schemas defined, unit tests pass.

---

### Phase 4 — FastAPI Routes (Mock Data) (Day 1 PM, ~2 hours)

**Window: Backend-API**

- [ ] Build `backend/main.py`: create FastAPI app, register all routers, add CORS (`localhost:3000`), add request logging middleware
- [ ] Build all 7 routers per Section 12, initially returning mock/hardcoded data
- [ ] Every protected route uses `user_id: str = Depends(get_current_user)`
- [ ] Build `GET /api/health` fully functional (actually pings DB)
- [ ] Add structured logging to every route (Section 17 format)
- [ ] Test every endpoint with curl or FastAPI's auto-generated `/docs` UI
- [ ] Verify auth middleware rejects requests without Bearer token
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** All endpoints return 200 with correct mock shapes. `/api/health` returns real DB status. Auth middleware blocks unauthed requests.

---

### Phase 5 — Scraper & PDF Parser Tools (Day 2 AM, ~2 hours)

**Window: Backend-Tools**

- [ ] Install: `pip install httpx beautifulsoup4 pymupdf`
- [ ] Build `tools/scraper.py`:
  - `scrape_job_description(url: str) → str`
    - httpx GET with 10s timeout, User-Agent header
    - BS4: extract `<main>`, `<article>`, or `<body>` text; strip nav/footer/scripts/styles
    - Return clean text, max 4000 chars
  - `scrape_form_fields(url: str) → list[FormField]`
    - Extract all `<input>`, `<textarea>`, `<select>` elements
    - Capture: id, name, label text (from `<label for="">` or parent label), type, placeholder
- [ ] Build `tools/pdf_parser.py`:
  - `extract_text_from_pdf(file_bytes: bytes) → str`
    - Use `fitz.open(stream=file_bytes, filetype="pdf")`
    - Extract text from all pages, join with newline
    - Return empty string if no text (scanned PDF)
- [ ] Write unit tests: `tests/unit/test_scraper.py` and `tests/unit/test_pdf_parser.py`
- [ ] Test scraper on: Indeed job posting, Greenhouse application, any public JD URL
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** Scraper returns >200 chars of clean text from 3 different job sites. PDF parser extracts text from sample resume PDF.

---

### Phase 6 — Gemini LLM Service (Day 2 AM, ~1.5 hours)

**Window: Backend-LLM**

- [ ] Install: `pip install google-generativeai`
- [ ] Get Gemini API key from Google AI Studio (aistudio.google.com) → add to `.env`
- [ ] Build `backend/services/llm.py` per Section 15:
  - `call_gemini(prompt, max_tokens) → str`
  - `parse_json_from_response(raw) → dict`
  - `load_prompt(filename) → str`
  - `call_groq(prompt, max_tokens) → str` (fallback — install `groq` package, get free API key)
- [ ] Test: send "respond with valid JSON: {\"status\": \"ok\"}" → verify parsed correctly
- [ ] Test: send garbage → verify `JSONParseError` raised, not crash
- [ ] Test timeout handling: 30s timeout → raises `LLMError`
- [ ] Write `tests/unit/test_llm_service.py`
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** `call_gemini()` sends a prompt and receives a response. `parse_json_from_response()` handles the 3 JSON formats (clean, fenced, with preamble).

---

### Phase 7 — Resume Scorer Agent (Day 2 PM, ~3 hours)

**Window: Agent-Resume**

- [ ] Write `prompts/resume_score_v1.txt` per Section 26
- [ ] Build `agents/resume_scorer.py` — full workflow per Section 7
- [ ] Connect to `POST /api/resume/analyze` router (replace mock data)
- [ ] Handle file upload in router: receive `UploadFile`, read bytes, pass to agent
- [ ] End-to-end test: paste resume text + real LinkedIn JD URL → receive valid `ResumeScoreResult`
- [ ] Verify: `match_score` is 0–100, `grade` is A/B/C/D/F, `suggestions` is non-empty
- [ ] Write `tests/unit/test_resume_scorer.py` (mock LLM call)
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** Full pipeline works end-to-end with real inputs. Pydantic validation passes on output.

---

### Phase 8 — Answer Generator Agent (Day 3 AM, ~2 hours)

**Window: Agent-Answer**

- [ ] Write `prompts/answer_gen_v1.txt` per Section 26
- [ ] Build `agents/answer_generator.py` — full workflow per Section 7
- [ ] Connect to `POST /api/generate/answer` router
- [ ] Test with 3 different questions + same profile → all answers are different and personalized
- [ ] Verify: no banned phrases, >100 words, first-person voice
- [ ] Write `tests/unit/test_answer_gen.py`
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** Generated answers reference user's actual company/role names. Not generic.

---

### Phase 9 — Autofill Agent (Day 3 AM, ~2 hours)

**Window: Agent-Autofill**

- [ ] Write `prompts/autofill_v1.txt` per Section 26
- [ ] Build `agents/autofill_mapper.py` — full workflow per Section 7 (rule-based + LLM fallback)
- [ ] Connect to `POST /api/autofill` router
- [ ] Test on a real Greenhouse apply page and an Indeed apply page
- [ ] Verify: `fill_rate` > 0.5 on standard forms, confidence levels are set correctly
- [ ] Write `tests/unit/test_autofill.py`
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** Common fields (name, email, phone, LinkedIn) map correctly with confidence ≥0.85.

---

### Phase 10 — Frontend Static Components (Day 3 PM – Day 4, ~4 hours)

**Window: Frontend-Components** *(can start Day 2 in parallel with backend phases)*

- [ ] Install shadcn/ui: `npx shadcn@latest init` + add components: button, card, badge, dialog, input, textarea, select, progress, tooltip, skeleton
- [ ] Build all components in `components/` per Section 13 using **hardcoded mock data only**
- [ ] Build all 8 screens in `app/(app)/` with mock data
- [ ] Implement `(app)/layout.tsx` auth guard (placeholder redirect for now — real auth in Phase 11)
- [ ] Build `<AgentLoadingSteps>` with mock cycling messages
- [ ] Build `<ScoreGauge>` with animated fill
- [ ] Build `<OnboardingWizard>` — all 4 steps navigable
- [ ] Build `<ApplicationTable>` with mock applications data
- [ ] Implement light/dark mode toggle (Tailwind dark: classes)
- [ ] Verify: every screen renders without errors, all interactive elements are clickable
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** All 8 screens render with mock data. No console errors. Responsive on mobile viewport.

---

### Phase 11 — Auth + Frontend Integration (Day 5, ~4 hours)

**Window: Integration**

- [ ] Install: `npm install @supabase/supabase-js`
- [ ] Create `frontend/lib/supabase.ts` — `createBrowserClient()`
- [ ] Build `/login` and `/register` pages with real Supabase auth calls
- [ ] Build `(app)/layout.tsx` auth guard — real session check, real redirect
- [ ] Build `UserContext` — loads `GET /api/users/me` on mount
- [ ] Build `services/api.ts` — all fetch functions with JWT header injection
- [ ] Wire each page to its API call (replace all mock data)
- [ ] Wire `ApplicationContext` to `/api/applications`
- [ ] Test: register → onboarding → dashboard → all features end-to-end
- [ ] Handle 401 responses: auto-refresh token, retry once
- [ ] Update `Agent_Status.md` + `status.md`

**✅ Done when:** Full user journey works: register → profile → score resume → generate answer → track application → logout → login again.

---

### Phase 12 — QA, Polish & Docs (Day 6–7, ~3 hours)

**Window: QA**

- [ ] Run full manual QA checklist from Section 19
- [ ] Fix all failing checklist items
- [ ] Write `docs/api_reference.md` with all endpoints + example curl commands
- [ ] Write `README.md` with: project description, setup instructions, env vars, how to run
- [ ] Run all unit tests: `pytest backend/tests/unit/`
- [ ] Final `status.md` update: mark MVP complete
- [ ] Final `Agent_Status.md` entry: Phase 12 complete, known issues, next steps

**✅ Done when:** QA checklist passes. README lets someone run the project in <10 minutes.

---

## 22. Sub-Agent Windows (Cursor Parallelization)

### Which phases can run in parallel

```
Day 1:
  Window 1: Phase 1 (Scaffold) → Phase 2 (Supabase) → Phase 3 (Schemas)
  [Sequential — each depends on the previous]

Day 2:
  Window 1: Phase 4 (API Routes) → Phase 5 (Scraper Tools)
  Window 2: Phase 10 START (Frontend Static) ← fully independent of backend

Day 3:
  Window 1: Phase 6 (LLM Service) → Phase 7 (Resume Agent)
  Window 2: Phase 10 CONTINUE (Frontend Static)

Day 4:
  Window 1: Phase 8 (Answer Agent) + Phase 9 (Autofill Agent) [can overlap]
  Window 2: Phase 10 FINISH (Frontend Static)

Day 5:
  Window 1: Phase 11 (Auth + Integration) — requires all backend phases
  [Frontend Phase 10 must be complete before integration]

Day 6–7:
  Window 1: Phase 12 (QA + Docs)
```

### Key parallelization rules

1. **Read `Agent_Status.md` before starting** — confirms your prerequisites are done
2. **Update `Agent_Status.md` when done** — signals to other windows
3. **Frontend window (Phase 10) starts Day 2** — it has zero backend dependencies until Phase 11
4. **Never two windows editing the same file** — check `Agent_Status.md` for file ownership per phase
5. **Backend windows stay in `/backend/`** — frontend window stays in `/frontend/`

---

## 23. Future Features Roadmap (Post-MVP)

These features are explicitly OUT OF SCOPE for this MVP but are designed for in the architecture (no major refactoring needed to add them).

### Phase 2 (First post-MVP sprint)

| Feature | What it is | Why it matters |
|---------|-----------|----------------|
| **Browser Extension** | Chrome/Firefox extension that actually injects autofill values into application forms | Makes the autofill feature actually useful in practice. MVP only previews. |
| **Google OAuth** | "Sign in with Google" button | Reduces friction for users who don't want email/password |
| **Resume PDF storage** | Save uploaded resumes to Supabase Storage; reuse across sessions | User shouldn't have to re-upload their resume every session |
| **JD caching** | Cache scraped JDs in the `applications` table; don't re-scrape | Saves time + avoids getting blocked by rate limiting |
| **Vendor changelog ingestion** | RSS feed scraping for Anthropic/OpenAI release notes | Keep trend content fresh for career advice |

### Phase 3 (Career ops platform vision)

| Feature | Description |
|---------|------------|
| **Cover letter generator** | Full cover letter from profile + JD, not just individual answers |
| **Interview prep agent** | Generates likely interview questions for a given JD; user can practice answers |
| **LinkedIn profile optimizer** | Analyzes user's LinkedIn profile against a target role; suggests improvements |
| **Job board scraper** | Automatically finds relevant open roles from Indeed/LinkedIn based on user preferences |
| **Email tracking** | Detects job-related emails in Gmail (with OAuth); auto-updates application status |
| **Resume builder** | Generate a tailored resume version for each application (not just score the existing one) |
| **Analytics dashboard** | Response rate, interview conversion rate, time-to-response by company/industry |
| **Multi-resume support** | User maintains multiple resume versions; choose which one to score/use |
| **Referral tracker** | Log who referred you to each job; track outcomes |
| **Networking agent** | Drafts cold outreach messages for informational interviews |

### Architecture changes needed for Phase 3

- Swap SQLite → Supabase is already done ✅
- Add job queue (BullMQ or Celery) for long-running scrape + email jobs
- Add Redis for caching frequently-accessed profiles and JD text
- Add background job scheduler (cron or Inngest) for automated job scraping
- Consider moving to a multi-service architecture (separate scraping service) if scraping volume grows

---

## 24. Risks & Tradeoffs

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LinkedIn/Indeed blocks scraper | High | Medium | Use Indeed instead of LinkedIn for JD scraping tests (more permissive). Always have paste-text fallback. Apify upgrade available in Phase 2 for $1–2/100 scrapes. |
| Gemini returns inconsistent JSON | Medium | Medium | `response_mime_type="application/json"` forces JSON output. `parse_json_from_response()` handles 3 formats. Retry with correction prompt on failure. |
| Gemini rate limit on free tier (250 req/day on Flash) | Low for MVP | Low | 250 requests/day is plenty for a 1-week dev cycle. If hit: switch to Groq fallback (free, fast). |
| Supabase RLS misconfiguration | Medium | High | Follow Section 10 exactly. Test each policy: confirm user A cannot read user B's data before Phase 12. |
| Auth token expiry mid-session | Low | Medium | Frontend catches 401 → `supabase.auth.refreshSession()` → retry request. Supabase SDK handles refresh automatically. |
| Phase 11 integration takes longer than expected | Medium | High | Phase 10 (static components) starts Day 2 — provides buffer. Integration is mostly wiring, not building. |
| Supabase free tier pauses after 1 week of inactivity | Low | Low | Keep the project active. Or upgrade to $25/mo Pro for the demo. |

### Key Tradeoffs Made

**No browser extension in MVP:**
Building a Chrome extension adds 8–12 hours of setup (manifest.json, content scripts, popup UI, separate build pipeline). For a 1-week timeline, a web app that previews autofill is 80% of the value at 20% of the effort. Extension is Phase 2.

**Supabase over raw PostgreSQL:**
Raw Postgres gives more control but requires setting up auth, connection pooling, and migrations from scratch. Since auth was a requirement, Supabase is strictly better for this project — it IS Postgres, just with a platform on top.

**Single LLM (Gemini) with Groq fallback over multi-model routing:**
Multi-model routing (Gemini for some tasks, GPT for others) adds complexity with minimal benefit at MVP scale. One model, well-prompted, is simpler and easier to debug.

---

## 25. Open Questions

| Question | Priority | Notes |
|----------|---------|-------|
| Should resume PDFs be stored in Supabase Storage between sessions? | Medium | Recommended — saves re-upload friction. Add in Phase 11. Storage bucket setup in Phase 2. |
| Should the app support multiple resumes per user (targeting different roles)? | Low (MVP) | Current schema supports one profile. Multi-resume is Phase 3. |
| Should feedback (thumbs up/down) affect prompt selection? | Low (MVP) | Currently just stored. Use to A/B test prompts in Phase 3. |
| Is Google OAuth needed for the internship demo? | Low | Email/password is sufficient. Google OAuth adds 30 min — add if time permits. |
| Should the `jd_text` in applications table be auto-populated when user scores a resume? | Medium | Yes — a small quality-of-life improvement in Phase 11. Store scraped JD on `PATCH /api/applications/{id}`. |

---

## 26. Appendix: Prompt Templates

All prompts live in `/backend/prompts/`. When modifying, create a new versioned file (`v2.txt`) — never overwrite the working version.

### Resume Score Prompt (`resume_score_v1.txt`)

```
You are an expert technical recruiter and career coach with 15 years of experience screening resumes for software engineering and data science roles. You have deep expertise in ATS systems and know exactly what keywords and signals they look for.

Your task: Analyze the provided resume against the provided job description. Return a detailed match analysis.

BANNED: Do not use phrases like "Great resume!", "I noticed that", "As an AI", "Certainly!", or any conversational preamble. Return JSON only.

--- RESUME ---
{resume}

--- JOB DESCRIPTION ---
{jd}

--- INSTRUCTIONS ---
Analyze the resume against the job description and return a JSON object with EXACTLY this schema:

{{
  "match_score": <integer 0-100>,
  "grade": "<A|B|C|D|F>",
  "summary": "<1-2 sentences: overall assessment focusing on biggest strength and biggest gap>",
  "matched_skills": ["<skill from JD that appears in resume>", ...],
  "missing_skills": ["<skill from JD that does NOT appear in resume>", ...],
  "suggestions": [
    "<specific, actionable suggestion — reference actual resume content and JD requirements>",
    "<suggestion 2>",
    "<suggestion 3>",
    "<suggestion 4 if applicable>"
  ],
  "jd_key_requirements": ["<top 5-7 skills/requirements from JD>", ...],
  "ats_risk": "<low|medium|high>",
  "ats_risk_reason": "<one sentence: why this ATS risk level>"
}}

Scoring guide:
- 90-100 (A): Highly qualified. Meets all key requirements. Would likely pass ATS and impress a recruiter.
- 75-89 (B): Good match. Meets most requirements. Minor gaps. Likely passes ATS.
- 60-74 (C): Moderate match. Meets some requirements. Notable gaps. May fail ATS keyword scan.
- 45-59 (D): Weak match. Meets few key requirements. Significant reskilling or reframing needed.
- 0-44 (F): Poor match. Fundamentally misaligned with the role requirements.

Return ONLY the JSON object. No preamble. No explanation. No markdown code fences.

--- EXAMPLE OUTPUT (do not copy — use for format reference only) ---
{{
  "match_score": 72,
  "grade": "C",
  "summary": "Strong Python and API experience, but the role heavily emphasizes Kubernetes and cloud infrastructure which are absent from the resume.",
  "matched_skills": ["Python", "REST APIs", "PostgreSQL"],
  "missing_skills": ["Kubernetes", "AWS", "Terraform"],
  "suggestions": [
    "Add any Kubernetes experience to your most recent role, even if minor (e.g., 'deployed services to Kubernetes cluster')",
    "Mention your cloud platform experience explicitly — the JD references AWS 5 times",
    "Quantify your API work: 'built REST APIs' → 'built 8 REST API endpoints serving 30K daily requests'"
  ],
  "jd_key_requirements": ["Python", "Kubernetes", "AWS", "REST APIs", "PostgreSQL", "Terraform"],
  "ats_risk": "medium",
  "ats_risk_reason": "Missing 3 of 6 high-frequency JD keywords, increasing risk of ATS filtering before human review."
}}
```

---

### Answer Generator Prompt (`answer_gen_v1.txt`)

```
You are a career coach writing a job application answer on behalf of your client. You have access to their professional profile and the job description. Your goal is to write a compelling, specific, first-person answer that sounds authentically human.

CRITICAL RULES:
- Write in first person ("I built...", "My experience at...")
- Reference specific details from the user's profile (company names, role titles, achievements)
- Reference specific requirements from the job description
- Do NOT be generic — any answer that could apply to any candidate is a failure
- Do NOT use: "I am a highly motivated...", "I am passionate about...", "I excel at...", "I am a team player"
- Do NOT start with "Certainly!", "Great question!", or any preamble
- Do NOT mention that you are an AI or that this is AI-generated
- Length: 250–350 words
- Tone: professional but conversational — sounds like a real person, not a corporate template

--- USER PROFILE ---
{profile}

--- JOB DESCRIPTION ---
{jd}

--- APPLICATION QUESTION ---
{question}

Write the answer now. Return only the answer text. No preamble, no explanation, no formatting.
```

---

### Autofill LLM Fallback Prompt (`autofill_v1.txt`)

```
You are a form field analyst. Given a list of HTML form fields and a user profile schema, determine which profile field each form field corresponds to.

--- FORM FIELDS (JSON) ---
{fields}

--- USER PROFILE KEYS AND DESCRIPTIONS ---
{profile_keys}

For each form field, determine:
1. Which profile key it corresponds to (or null if no match)
2. What value to suggest from the profile (or null)
3. Your confidence (0.0 to 1.0)

Return a JSON array with EXACTLY this schema:
[
  {{
    "field_id": "<from input>",
    "profile_key": "<profile key name or null>",
    "suggested_value": "<value from profile or null>",
    "confidence": <float 0.0-1.0>
  }}
]

Rules:
- confidence >= 0.85: you are certain this is the correct mapping
- confidence 0.5-0.84: you believe this is correct but are not certain
- confidence < 0.5: you are guessing or no good match exists
- For file upload fields (resume, cover letter): always return null for both profile_key and suggested_value, confidence 0.0
- Return JSON array only. No preamble. No markdown.
```

---

## 27. Appendix: Environment Variables

**Backend `.env` file** (copy from `.env.example`, fill in values):

```bash
# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-from-supabase-dashboard
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key          # For admin ops only — keep secret
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-settings
# HOW TO GET: Supabase Dashboard → Settings → API → JWT Settings → JWT Secret

# ── LLM ───────────────────────────────────────────────────
GOOGLE_GEMINI_API_KEY=your-gemini-api-key
# HOW TO GET: aistudio.google.com → Get API Key → Create API Key

GROQ_API_KEY=your-groq-api-key                           # Fallback LLM — free tier
# HOW TO GET: console.groq.com → API Keys → Create Key

# ── App ───────────────────────────────────────────────────
ENVIRONMENT=development                                   # development | production
LOG_LEVEL=INFO
```

**Frontend `.env.local` file** (Next.js — `NEXT_PUBLIC_` prefix = safe to expose to browser):

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-from-supabase-dashboard
# These two are safe to expose — they are designed to be public
# The anon key only has read access + respects RLS policies

NEXT_PUBLIC_API_URL=http://localhost:8000
# Change to your deployed backend URL when deploying to production
```

**Where to find each value:**

| Variable | Location |
|---------|---------|
| `SUPABASE_URL` | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Supabase Dashboard → Settings → API → Project API Keys → anon public |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Settings → API → Project API Keys → service_role |
| `SUPABASE_JWT_SECRET` | Supabase Dashboard → Settings → API → JWT Settings → JWT Secret |
| `GOOGLE_GEMINI_API_KEY` | aistudio.google.com → Get API Key |
| `GROQ_API_KEY` | console.groq.com → API Keys |

---

*End of Document — v2.0 Final*
*Start with Phase 1. Always read `status.md` and `Agent_Status.md` before any session.*
*Questions? The Open Questions section (Section 25) tracks everything unresolved.*
