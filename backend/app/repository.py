"""SQLite persistence with transactional URL and title/date/place deduplication."""
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import Event
from .scoring import LONDON


def canonical_url(value: str) -> str:
    parts = urlsplit(value)
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                   if not k.casefold().startswith("utm_") and k.casefold() not in {"fbclid", "gclid", "mc_cid", "mc_eid"})
    host = (parts.hostname or "").casefold()
    port = parts.port
    if port and not (port == 443 and parts.scheme == "https" or port == 80 and parts.scheme == "http"):
        host += f":{port}"
    return urlunsplit((parts.scheme.casefold(), host, parts.path.rstrip("/") or "/", urlencode(query), ""))


def normalized(value: str) -> str:
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", value).casefold())


def fingerprint(event: Event) -> str:
    return "|".join([normalized(event.title), event.start_at.astimezone(LONDON).date().isoformat(), normalized(event.city)])


def make_id(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()[:20]


class Repository:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS urls (url TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id))")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def all(self) -> list[Event]:
        with self.connect() as db:
            return [Event.model_validate_json(row[0]) for row in db.execute("SELECT payload FROM events ORDER BY id")]

    def import_events(self, events: list[Event]) -> dict:
        added = duplicates = 0
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for event in events:
                url = canonical_url(str(event.url))
                row = db.execute("SELECT events.id, payload FROM events JOIN urls ON urls.event_id=events.id WHERE urls.url=?", (url,)).fetchone()
                if not row:
                    row = db.execute("SELECT id, payload FROM events WHERE fingerprint=?", (fingerprint(event),)).fetchone()
                if row:
                    existing = Event.model_validate_json(row[1])
                    # Preserve prior details; a duplicate is not silently treated as a trusted update.
                    existing.source_urls = list(dict.fromkeys(existing.source_urls + event.source_urls))
                    db.execute("UPDATE events SET payload=? WHERE id=?", (existing.model_dump_json(), existing.id))
                    db.execute("INSERT OR IGNORE INTO urls VALUES (?, ?)", (url, existing.id))
                    duplicates += 1
                else:
                    db.execute("INSERT INTO events VALUES (?, ?, ?)", (event.id, fingerprint(event), event.model_dump_json()))
                    db.execute("INSERT INTO urls VALUES (?, ?)", (url, event.id))
                    added += 1
        return {"added": added, "duplicates": duplicates, "received": len(events)}
