# API reference (outline)

**Base URL (local):** `http://localhost:8000`  
**Auth:** `Authorization: Bearer <supabase_jwt>` on protected routes.

Full contracts: PRD Section 12.

| Method | Path | Auth | Request / response |
|--------|------|------|-------------------|
| GET | `/api/health` | Public | Response: status, database, llm, version, timestamp — TBD implementation |
| POST | `/api/auth/verify` | — | TBD |
| POST | `/api/users` | Protected | Create profile row — TBD |
| GET | `/api/users/me` | Protected | Full `UserProfile` — TBD |
| PATCH | `/api/users/me` | Protected | Partial update — TBD |
| POST | `/api/resume/analyze` | Protected | multipart: resume + JD — TBD |
| POST | `/api/generate/answer` | Protected | question + JD context — TBD |
| POST | `/api/autofill` | Protected | URL + profile — TBD |
| GET/POST/PATCH/DELETE | `/api/applications` | Protected | Application CRUD — TBD |

**Error shape (all errors):**

```json
{
  "error": "<error_code>",
  "message": "<human-readable message>",
  "detail": "<optional debug info>"
}
```
