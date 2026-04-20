# FastAPI app — register routers per PRD Section 12.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import applications, answers, auth, autofill, feedback, health, resume, users

app = FastAPI(title="Job Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api/users")
app.include_router(applications.router, prefix="/api/applications")
app.include_router(resume.router, prefix="/api/resume")
app.include_router(answers.router, prefix="/api")
app.include_router(autofill.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
