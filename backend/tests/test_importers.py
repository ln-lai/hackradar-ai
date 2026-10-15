import asyncio
import json

import httpx
import pytest

from backend.app import importers


def listing(**overrides):
    return {"@type": "Event", "name": "Agents Hackathon", "description": "Build AI agents with startup founders.", "startDate": "2026-10-23T10:00:00+01:00", "location": {"@type": "Place", "name": "Demo place", "address": {"addressLocality": "London"}}, **overrides}


def html(data):
    return '<script type="application/ld+json">' + json.dumps(data) + "</script>"


def test_graph_list_parsing_and_public_provenance():
    events = importers.parse_events(html({"@graph": [{"@type": "ItemList", "itemListElement": [{"item": listing()}]}]}), "https://lu.ma/test")
    event = events[0]
    assert event.city == "London" and event.kind == "hackathon"
    assert event.provenance == "public_import" and event.retrieved_at
    assert event.source_urls == ["https://lu.ma/test"]


def test_online_event_and_html_description():
    event = importers.parse_events(html(listing(location={"@type": "VirtualLocation"}, description="<b>Build AI agents</b> &amp; learn.")), "https://lu.ma/test")[0]
    assert event.city == "Online" and event.format == "online"
    assert event.description == "Build AI agents  & learn."


@pytest.mark.parametrize("change", [{"startDate": "2026-10-23"}, {"startDate": "2026-10-23T10:00:00"}, {"eventStatus": "https://schema.org/EventCancelled"}, {"eventStatus": "https://schema.org/EventPostponed"}, {"description": ""}])
def test_incomplete_and_cancelled_listings_not_fabricated(change):
    with pytest.raises(ValueError, match="No usable"):
        importers.parse_events(html(listing(**change)), "https://lu.ma/test")


@pytest.mark.parametrize("url", ["http://lu.ma/test", "https://localhost/test", "https://127.0.0.1/a", "https://lu.ma.evil.com/a", "https://lu.ma:8000/a", "https://user:password@lu.ma/a"])
def test_source_url_allowlist(url):
    with pytest.raises(ValueError):
        importers.validate_source_url(url)


def mock_client(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(importers.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))


def test_robots_rejection_prevents_fetch(monkeypatch):
    paths = []
    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nDisallow: /", request=request)
    mock_client(monkeypatch, handler)
    with pytest.raises(ValueError, match="robots"):
        asyncio.run(importers.import_public_url("https://lu.ma/test"))
    assert paths == ["/robots.txt"]


def test_redirect_to_private_host_is_blocked(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        return httpx.Response(302, headers={"Location": "https://127.0.0.1/secret"}, request=request)
    mock_client(monkeypatch, handler)
    with pytest.raises(ValueError, match="HTTPS event page"):
        asyncio.run(importers.import_public_url("https://lu.ma/test"))


def test_successful_fetch_records_actual_source(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /", request=request)
        return httpx.Response(200, text=html(listing()), headers={"Content-Type": "text/html"}, request=request)
    mock_client(monkeypatch, handler)
    assert asyncio.run(importers.import_public_url("https://lu.ma/test"))[0].source_urls == ["https://lu.ma/test"]


def test_import_size_cap(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        return httpx.Response(200, content=b"a" * (importers.MAX_BYTES + 1), headers={"Content-Type": "text/html"}, request=request)
    mock_client(monkeypatch, handler)
    with pytest.raises(ValueError, match="2 MB"):
        asyncio.run(importers.import_public_url("https://lu.ma/test"))
