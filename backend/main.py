# FastAPI app — register routers per PRD Section 12.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from exceptions import JsonHttpError
from middleware.logging import StructuredLoggingMiddleware
from routers import applications, answers, auth, autofill, feedback, health, resume, users

app = FastAPI(title="Job Assistant API", version="1.0.0")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Browser hits `/` by default — API routes live under `/api` (see `/docs`)."""
    return {
        "service": "Job Assistant API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/health",
    }


@app.exception_handler(JsonHttpError)
async def json_http_error_handler(_, exc: JsonHttpError) -> JSONResponse:
    """PRD Section 12 error bodies are flat JSON (no `detail` envelope)."""
    return JSONResponse(status_code=exc.status_code, content=exc.content)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLoggingMiddleware)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api/users")
app.include_router(applications.router, prefix="/api/applications")
app.include_router(resume.router, prefix="/api/resume")
app.include_router(answers.router, prefix="/api")
app.include_router(autofill.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
