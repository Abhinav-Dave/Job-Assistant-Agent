"""TEMP smoke test for answer generator.

Usage (from repo root):
  $env:PYTHONPATH = "backend"
  python backend/scripts/smoke_answer_gen.py

Delete this script before final production commit if desired.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from agents.answer_generator import (
    AgentError,
    generate_tailored_answer,
    LAST_PROVIDER_USED,
    LAST_WORD_LIMIT_MAX,
)
from services.llm import LLMError
from schemas.user import EducationItem, UserPreferences, UserProfile, WorkHistoryItem


def build_demo_profile() -> UserProfile:
    now = datetime.now(timezone.utc)
    return UserProfile(
        id=uuid4(),
        email="jane@example.com",
        full_name="Jane Smith",
        phone="416-555-0100",
        location="Toronto, ON",
        linkedin_url="https://linkedin.com/in/janesmith",
        portfolio_url="https://github.com/janesmith",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "CI/CD", "AWS"],
        preferences=UserPreferences(
            desired_roles=["Backend Engineer"],
            target_industries=["Fintech", "SaaS"],
            remote_preference="hybrid",
            salary_min=90000,
        ),
        work_history=[
            WorkHistoryItem(
                id=uuid4(),
                company="Acme Corp",
                role="Software Engineer",
                start_date="2022-01",
                end_date=None,
                is_current=True,
                bullets=[
                    "Built REST APIs with FastAPI and PostgreSQL serving 50K requests/day.",
                    "Reduced p95 API latency by 40% via indexing and query optimization.",
                    "Improved release reliability by implementing CI/CD guardrails.",
                ],
                display_order=0,
            ),
            WorkHistoryItem(
                id=uuid4(),
                company="Beta Labs",
                role="Junior Developer",
                start_date="2020-06",
                end_date="2021-12",
                is_current=False,
                bullets=[
                    "Maintained internal Python services and bug-fix backlog.",
                    "Improved unit test coverage for backend modules.",
                ],
                display_order=1,
            ),
        ],
        education=[
            EducationItem(
                id=uuid4(),
                institution="University of Toronto",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                graduation_year=2020,
                gpa="3.8",
                display_order=0,
            )
        ],
        onboarding_complete=True,
        created_at=now,
        updated_at=now,
    )


def main() -> None:
    profile = build_demo_profile()
    jd_text = """
    About the role:
    We are hiring a Backend Engineer to join our Platform team supporting a high-growth SaaS product used by
    100,000+ monthly active users. You will design and implement backend services that power critical workflows
    across onboarding, billing, and analytics.

    Responsibilities:
    - Build and maintain production REST APIs using Python and FastAPI.
    - Design efficient PostgreSQL schemas and queries for high-throughput, low-latency systems.
    - Improve reliability through observability, logging, alerting, and proactive incident response.
    - Partner with frontend, product, and design teams to deliver end-to-end features.
    - Own CI/CD pipelines, release processes, and deployment quality.
    - Contribute to architecture decisions for service boundaries and scaling strategies.
    - Mentor junior developers through code reviews and technical guidance.

    Required qualifications:
    - 3+ years of backend engineering experience.
    - Strong Python experience in production systems.
    - Hands-on FastAPI (or comparable API framework) experience.
    - Strong SQL fundamentals and PostgreSQL optimization experience.
    - Experience with Docker-based development and deployment workflows.
    - Familiarity with AWS services used in modern backend stacks.
    - Experience with CI/CD and automated testing.
    - Ability to communicate technical tradeoffs clearly to cross-functional stakeholders.

    Nice to have:
    - Experience reducing latency and improving reliability at scale.
    - Experience in SaaS or fintech environments.
    - Experience improving developer productivity and operational excellence.
    """
    question = (
        "Could you explain, in a detailed but conversational way, why your background makes you a strong fit for "
        "this Backend Engineer role? Please reference concrete projects and outcomes from your recent experience, "
        "describe how you approach API design, database performance, and CI/CD quality, and include an example of "
        "cross-functional collaboration that improved product delivery."
    )

    max_attempts = 3
    print("Running smoke test for generate_tailored_answer...")
    print(f"Max attempts: {max_attempts}\n")

    result = None
    last_error: AgentError | LLMError | None = None
    for attempt in range(1, max_attempts + 1):
        started_at = time.perf_counter()
        print(f"Attempt {attempt}/{max_attempts}...")
        try:
            result = generate_tailored_answer(
                question=question, user_profile=profile, jd_text=jd_text
            )
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            print(f"  Success in {elapsed_ms} ms\n")
            break
        except AgentError as err:
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            last_error = err
            print(f"  AgentError after {elapsed_ms} ms: {err.error} -> {err.message}")
            if err.error != "answer_too_short" or attempt == max_attempts:
                break
            print("  Retrying due to short answer...\n")
            time.sleep(1)
        except LLMError as err:
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            last_error = err
            print(f"  LLMError after {elapsed_ms} ms: {err.code} -> {err}")
            if attempt == max_attempts:
                break
            print("  Retrying due to transient LLM issue...\n")
            time.sleep(1)

    if result is None:
        print("\nSmoke test failed after retries.")
        if isinstance(last_error, AgentError):
            print("\nExpected-style agent failure:")
            print(f"  error:   {last_error.error}")
            print(f"  message: {last_error.message}")
            print(f"  detail:  {last_error.detail}")
        elif isinstance(last_error, LLMError):
            print("\nLLM failure:")
            print(f"  code:    {last_error.code}")
            print(f"  message: {last_error}")
        return

    print("\nSuccess:")
    print(f"  question:       {result.question}")
    print(f"  word_count:     {result.word_count}")
    print(f"  word_limit_max: {LAST_WORD_LIMIT_MAX}")
    print(
        f"  llm_provider:   {LAST_PROVIDER_USED} "
        f"(gemini is tried first; groq runs if Gemini fails; fallback is deterministic)"
    )
    print("\nAnswer preview:\n")
    print(result.answer)


if __name__ == "__main__":
    main()
