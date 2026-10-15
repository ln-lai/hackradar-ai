from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.seed import demo_events

TODAY = date(2026, 10, 15)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("HACKRADAR_API_TOKEN", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    return TestClient(create_app(str(tmp_path / "events.db"), lambda: TODAY))


def test_default_search_and_inclusive_minimum(client):
    data = client.post("/v1/search", json={}).json()
    assert data["matching"] == 4
    assert data["timezone"] == "Europe/London" and data["as_of"] == "2026-10-15"
    assert all(item["event"]["provenance"] == "example" for item in data["results"])
    assert client.post("/v1/search", json={"preferences": {"min_score": 10}}).json()["matching"] == 1
    assert client.post("/v1/search", json={"preferences": {"include_examples": False}}).json()["matching"] == 0


def test_import_search_details_and_repeat(client):
    event = demo_events(TODAY)[0].model_dump(mode="json")
    # An untrusted JSON payload cannot promote itself to public-import status.
    event["provenance"] = "public_import"
    assert client.post("/v1/import/json", json={"events": [event]}).json()["added"] == 1
    assert client.post("/v1/import/json", json={"events": [event]}).json()["duplicates"] == 1
    result = client.post("/v1/search", json={"preferences": {"include_examples": False}}).json()["results"][0]
    assert result["event"]["provenance"] == "user_import"
    assert result["event"]["retrieved_at"] is None
    assert client.get(f"/v1/events/{result['event']['id']}").status_code == 200


def test_invalid_bulk_import_is_atomic(client):
    valid = demo_events(TODAY)[0].model_dump(mode="json")
    invalid = {**valid, "start_at": "not-a-date"}
    assert client.post("/v1/import/json", json={"events": [valid, invalid]}).status_code == 422
    assert client.get("/v1/status").json()["imported_events"] == 0


def test_search_sort_and_bad_inputs(client):
    items = client.post("/v1/search", json={"sort": "date"}).json()["results"]
    assert [r["event"]["start_at"] for r in items] == sorted(r["event"]["start_at"] for r in items)
    assert client.post("/v1/search", json={"query": "zero to one"}).json()["matching"] == 1
    assert client.post("/v1/search", json={"preferences": {"days": 0}}).status_code == 422
    assert client.get("/v1/events/nonexistent").status_code == 404


def test_api_token_covers_read_and_write(client, monkeypatch):
    monkeypatch.setenv("HACKRADAR_API_TOKEN", "test-only-token")
    assert client.post("/v1/search", json={}).status_code == 401
    assert client.get("/v1/status").status_code == 401
    assert client.post("/v1/search", json={}, headers={"X-API-Token": "test-only-token"}).status_code == 200
    assert client.get("/health").status_code == 200


def test_size_limit_without_content_length(client):
    response = client.post("/v1/import/json", content=iter([b" " * 600_000, b" " * 600_000]), headers={"content-type": "application/json"})
    assert response.status_code == 413


def test_grok_absence_falls_back_without_changing_score(client):
    response = client.post("/v1/events/demo-agent-foundry/brief", json={"use_grok": True})
    assert response.status_code == 200
    assert response.json()["provider"] == "local"
    assert "not configured" in response.json()["notice"]
    assert "[your relevant skills" in response.json()["application_pitch"]
