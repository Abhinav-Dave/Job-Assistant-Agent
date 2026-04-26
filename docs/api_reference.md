# API reference

**Base URL (local):** `http://localhost:8000`  
**Auth:** `Authorization: Bearer <supabase_jwt>` on protected routes.

## Routes

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/health` | Public | Service health plus DB and LLM reachability |
| POST | `/api/auth/verify` | Protected | Validates token and returns `{ user_id, valid }` |
| POST | `/api/users` | Protected | Creates/updates initial user profile row |
| GET | `/api/users/me` | Protected | Fetches authenticated `UserProfile` |
| PATCH | `/api/users/me` | Protected | Partial profile update (including work/education arrays) |
| GET | `/api/applications` | Protected | Lists user applications (optional `?status=` filter) |
| POST | `/api/applications` | Protected | Creates a new application |
| PATCH | `/api/applications/{application_id}` | Protected | Updates one application |
| DELETE | `/api/applications/{application_id}` | Protected | Deletes one application |
| GET | `/api/applications/{application_id}/score-report` | Protected | Fetches stored resume score report |
| PUT | `/api/applications/{application_id}/score-report` | Protected | Upserts resume score report |
| POST | `/api/resume/analyze` | Protected | Multipart resume + JD analyze endpoint |
| POST | `/api/generate/answer` | Protected | Generates tailored answer from question + JD context |
| POST | `/api/autofill` | Protected | Returns mapping suggestions for page form fields |
| POST | `/api/feedback` | Protected | Logs agent feedback payload |

## Error shape

Expected API errors are returned as flat JSON:

```json
{
  "error": "<error_code>",
  "message": "<human-readable message>",
  "detail": "<optional debug info>"
}
```

Validation and transient upstream failures are typically mapped as:

- `422` for invalid input, scrape gaps, or agent-quality failures.
- `503` for upstream LLM availability/empty-response failures.
