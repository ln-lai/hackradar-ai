import asyncio
import hmac
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from .briefs import generate_brief
from .importers import ALLOWED_HOSTS, import_public_url
from .models import BriefRequest, Event, ImportRequest, RankedEvent, SearchRequest, SearchResult, URLImportRequest
from .repository import Repository, make_id
from .scoring import LONDON, score_event
from .seed import demo_events

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def create_app(database_path: str | None = None, today_provider=None) -> FastAPI:
    app = FastAPI(title="HackRadar AI", version="0.1.0", description="Evidence-first hackathon matching. Fictional demo data is always labeled.")
    repo = Repository(database_path or os.getenv("DATABASE_PATH", "backend/data/hackradar.sqlite3"))
    today = today_provider or (lambda: datetime.now(LONDON).date())

    async def authorize(x_api_token: str | None = Header(default=None)):
        token = os.getenv("HACKRADAR_API_TOKEN", "")
        if token and not hmac.compare_digest(x_api_token or "", token):
            raise HTTPException(401, "Invalid API token")

    @app.middleware("http")
    async def size_limit(request: Request, call_next):
        # Check the actual stream as well as Content-Length (which may be absent or false).
        if request.method in ("POST", "PUT", "PATCH"):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 1_000_000:
                    return JSONResponse({"detail": "Request exceeds 1 MB"}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    def catalog():
        return repo.all() + demo_events(today())

    def find_event(event_id):
        event = next((e for e in catalog() if e.id == event_id), None)
        if not event:
            raise HTTPException(404, "Event not found")
        return event

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/v1/status", dependencies=[Depends(authorize)])
    def status():
        return {"grok_configured": bool(os.getenv("XAI_API_KEY") and os.getenv("XAI_MODEL")),
                "storage": "sqlite", "imported_events": len(repo.all()), "allowed_hosts": sorted(ALLOWED_HOSTS)}

    @app.post("/v1/search", response_model=SearchResult, dependencies=[Depends(authorize)])
    def search(body: SearchRequest):
        events = catalog()
        ranked = [RankedEvent(event=e, score=score_event(e, body.preferences, today())) for e in events]
        query = body.query.strip().casefold()
        results = [r for r in ranked if r.score.eligible and r.score.total >= body.preferences.min_score and
                   (not query or query in f"{r.event.title} {r.event.description} {' '.join(r.event.tags)}".casefold())]
        results.sort(key=(lambda r: (r.event.start_at, -r.score.total, r.event.id)) if body.sort == "date" else
                     (lambda r: (-r.score.total, r.event.start_at, r.event.id)))
        return SearchResult(results=results, total_scanned=len(events), matching=len(results),
                            examples=sum(e.provenance == "example" for e in events), imported=len(repo.all()), as_of=today())

    @app.get("/v1/events/{event_id}", response_model=Event, dependencies=[Depends(authorize)])
    def detail(event_id: str):
        return find_event(event_id)

    @app.post("/v1/import/json", dependencies=[Depends(authorize)])
    def import_json(body: ImportRequest):
        events = [Event(**e.model_dump(), id=make_id(str(e.url)), provenance="user_import", source_urls=[str(e.url)], retrieved_at=None) for e in body.events]
        return repo.import_events(events)

    @app.post("/v1/import/url", dependencies=[Depends(authorize)])
    async def import_url(body: URLImportRequest):
        try:
            events = await asyncio.wait_for(import_public_url(str(body.url)), timeout=45)
            return repo.import_events(events)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except (httpx.HTTPError, TimeoutError) as exc:
            raise HTTPException(502, "The public source could not be read. It may block automated access or be unavailable. Try an authorized JSON export.") from exc

    @app.post("/v1/events/{event_id}/brief", dependencies=[Depends(authorize)])
    async def brief(event_id: str, body: BriefRequest):
        event = find_event(event_id)
        return await generate_brief(event, body.preferences, score_event(event, body.preferences, today()), body.use_grok)

    return app


app = create_app()
