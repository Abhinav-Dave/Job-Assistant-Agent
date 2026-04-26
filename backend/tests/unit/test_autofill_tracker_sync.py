from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from routers import autofill as autofill_router


class _FakeQuery:
    def __init__(self, supabase: "_FakeSupabase", table_name: str, operation: str):
        self.supabase = supabase
        self.table_name = table_name
        self.operation = operation
        self.filters: list[tuple[str, object]] = []
        self.insert_payload: dict | None = None
        self.update_payload: dict | None = None

    def select(self, _cols: str):
        return self

    def eq(self, key: str, value: object):
        self.filters.append((key, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.operation == "select":
            rows = [row for row in self.supabase.tables[self.table_name] if self._matches(row)]
            return type("Resp", (), {"data": deepcopy(rows)})
        if self.operation == "insert":
            assert self.insert_payload is not None
            now = datetime.now(timezone.utc).isoformat()
            row = {
                "id": self.insert_payload.get("id", str(uuid4())),
                "user_id": self.insert_payload["user_id"],
                "company": self.insert_payload["company"],
                "role": self.insert_payload["role"],
                "jd_url": self.insert_payload.get("jd_url"),
                "jd_text": self.insert_payload.get("jd_text"),
                "status": self.insert_payload["status"],
                "notes": self.insert_payload.get("notes"),
                "date_applied": self.insert_payload.get("date_applied"),
                "last_score": self.insert_payload.get("last_score"),
                "created_at": now,
                "updated_at": now,
            }
            self.supabase.tables[self.table_name].append(row)
            return type("Resp", (), {"data": [deepcopy(row)]})
        if self.operation == "update":
            assert self.update_payload is not None
            updated: list[dict] = []
            for row in self.supabase.tables[self.table_name]:
                if self._matches(row):
                    row.update(self.update_payload)
                    row["updated_at"] = datetime.now(timezone.utc).isoformat()
                    updated.append(deepcopy(row))
            return type("Resp", (), {"data": updated})
        raise AssertionError(f"Unsupported operation: {self.operation}")

    def insert(self, payload: dict):
        self.insert_payload = payload
        self.operation = "insert"
        return self

    def update(self, payload: dict):
        self.update_payload = payload
        self.operation = "update"
        return self

    def _matches(self, row: dict) -> bool:
        for key, value in self.filters:
            if row.get(key) != value:
                return False
        return True


class _FakeSupabase:
    def __init__(self, rows: list[dict] | None = None):
        self.tables = {"applications": deepcopy(rows or [])}

    def table(self, table_name: str):
        return _FakeQuery(self, table_name, "select")


def _build_application(*, user_id: str, jd_url: str, status: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(uuid4()),
        "user_id": user_id,
        "company": "Acme",
        "role": "Engineer",
        "jd_url": jd_url,
        "jd_text": None,
        "status": status,
        "notes": None,
        "date_applied": None,
        "last_score": None,
        "created_at": now,
        "updated_at": now,
    }


def test_mapping_preview_creates_in_progress_application_when_absent(monkeypatch) -> None:
    user_id = str(uuid4())
    fake = _FakeSupabase([])
    monkeypatch.setattr(autofill_router, "get_supabase", lambda: fake)

    sync_status, app_id, _ = autofill_router._upsert_application_from_mapping_preview(
        user_id=user_id,
        page_url="https://jobs.example.com/apply?ref=abc",
    )

    assert sync_status == "created"
    created = fake.tables["applications"][0]
    assert created["id"] == app_id
    assert created["status"] == "in_progress"
    assert created["jd_url"] == "https://jobs.example.com/apply?ref=abc"


def test_mapping_preview_is_idempotent_for_same_normalized_url(monkeypatch) -> None:
    user_id = str(uuid4())
    existing = _build_application(
        user_id=user_id,
        jd_url="https://jobs.example.com/apply/?b=2&a=1",
        status="saved",
    )
    fake = _FakeSupabase([existing])
    monkeypatch.setattr(autofill_router, "get_supabase", lambda: fake)

    sync_status, app_id, _ = autofill_router._upsert_application_from_mapping_preview(
        user_id=user_id,
        page_url="https://jobs.example.com/apply?a=1&b=2",
    )

    assert sync_status == "updated"
    assert app_id == existing["id"]
    assert len(fake.tables["applications"]) == 1
    assert fake.tables["applications"][0]["status"] == "in_progress"


def test_mapping_preview_does_not_downgrade_completed_status(monkeypatch) -> None:
    user_id = str(uuid4())
    existing = _build_application(
        user_id=user_id,
        jd_url="https://jobs.example.com/apply",
        status="submitted",
    )
    fake = _FakeSupabase([existing])
    monkeypatch.setattr(autofill_router, "get_supabase", lambda: fake)

    sync_status, app_id, _ = autofill_router._upsert_application_from_mapping_preview(
        user_id=user_id,
        page_url="https://jobs.example.com/apply",
    )

    assert sync_status == "unchanged"
    assert app_id == existing["id"]
    assert len(fake.tables["applications"]) == 1
    assert fake.tables["applications"][0]["status"] == "submitted"
