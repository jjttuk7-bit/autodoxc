"""세션 API — POST 생성 + GET 스트리밍 + 404 동작."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.api.sessions import _test_clear_store, _test_get_input
from app.main import app


@pytest.fixture(autouse=True)
def _clear_store():
    _test_clear_store()
    yield
    _test_clear_store()


def test_create_session_returns_id() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/sessions",
        json={"user_input": "외국인 고용 계획서 좀 써줘."},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "session_id" in body
    assert len(body["session_id"]) == 16
    assert _test_get_input(body["session_id"]) == "외국인 고용 계획서 좀 써줘."


def test_create_session_rejects_empty_input() -> None:
    client = TestClient(app)
    resp = client.post("/api/sessions", json={"user_input": ""})
    assert resp.status_code == 422  # pydantic validation


def test_stream_404_when_session_missing() -> None:
    client = TestClient(app)
    resp = client.get("/api/sessions/nonexistent/stream")
    assert resp.status_code == 404


def test_stream_returns_sse_events() -> None:
    """POST → 받은 session_id로 GET stream → SSE 이벤트 도착."""
    client = TestClient(app)
    create = client.post(
        "/api/sessions",
        json={"user_input": "외국인 고용 계획서 한 명 채용."},
    )
    sid = create.json()["session_id"]

    with client.stream("GET", f"/api/sessions/{sid}/stream") as resp:
        assert resp.status_code == 200
        # 첫 이벤트 1개만 검증 (skeleton_ready)
        first_event_data: str | None = None
        for line in resp.iter_lines():
            line = line.strip()
            if line.startswith("data:"):
                first_event_data = line[5:].strip()
                break
        assert first_event_data is not None
        payload = json.loads(first_event_data)
        assert payload["kind"] == "skeleton_ready"
        assert payload["doc_type"]["id"] == "foreign-worker-employment-plan"
