# Architecture

Source: PRD Section 6 (System Architecture).

## High-level diagram

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
│   └────────────┬─────────────────────────────┬──────────────────────┘    │
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
│       │ pdf_parser │   │    via supabase-py       │  └─────────────────────┘ │
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

## Resume analyze flow (summary)

See PRD Section 6 — Request lifecycle for Resume Score: frontend → FastAPI → auth → `resume_scorer` → PDF/JD tools → Gemini → validated JSON response.
