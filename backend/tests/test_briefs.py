import asyncio
import json
from datetime import date

import httpx
import pytest

from backend.app import briefs
from backend.app.models import Preferences
from backend.app.scoring import score_event
from backend.app.seed import demo_events


@pytest.mark.parametrize("valid", [True, False])
def test_grok_response_and_invalid_output_fallback(monkeypatch, valid):
    event = demo_events(date(2026, 10, 15))[0]
    preferences = Preferences()
    score = score_event(event, preferences, date(2026, 10, 15))
    monkeypatch.setenv("XAI_API_KEY", "test-not-a-real-key")
    monkeypatch.setenv("XAI_MODEL", "test-model")
    def handler(request):
        body = json.loads(request.content)
        assert body["store"] is False
        assert "untrusted" in body["instructions"]
        assert body["text"]["format"]["type"] == "json_schema"
        text = json.dumps({"summary": "An illustrative match.", "application_pitch": "I bring [your skills].", "preparation": ["Confirm the real listing."]}) if valid else "Not JSON"
        return httpx.Response(200, json={"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}, request=request)
    original = httpx.AsyncClient
    monkeypatch.setattr(briefs.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    result = asyncio.run(briefs.generate_brief(event, preferences, score, True))
    assert result["provider"] == ("grok" if valid else "local")
    assert score.total == 10
