"""Import visible Event JSON-LD only. No login, browser bypass, or private scraping."""
import json
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from .models import Event, EventInput
from .repository import make_id

ALLOWED_HOSTS = {"lu.ma", "luma.com", "www.luma.com", "www.eventbrite.com", "www.eventbrite.co.uk", "mlh.io", "www.mlh.io", "mlh.com", "www.mlh.com"}
MAX_BYTES = 2_000_000
USER_AGENT = "HackRadar/0.1 (public Event JSON-LD import)"


def validate_source_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS or parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError("Use an HTTPS event page on Luma, Eventbrite, or MLH. Other hosts and ports are not supported.")
    return url


class JSONLDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collecting = False
        self.parts: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.casefold() == "script" and dict(attrs).get("type", "").casefold() == "application/ld+json":
            self.collecting = True
            self.parts = []

    def handle_data(self, data):
        if self.collecting:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.casefold() == "script" and self.collecting:
            self.blocks.append("".join(self.parts))
            self.collecting = False


def nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from nodes(item)
    elif isinstance(value, dict):
        yield value
        for key in ("@graph", "itemListElement", "item", "mainEntity"):
            if key in value:
                yield from nodes(value[key])


def plain(value) -> str:
    return unescape(re.sub(r"<[^>]*>", " ", str(value or ""))).strip()


def parse_events(html: str, source_url: str) -> list[Event]:
    parser = JSONLDParser()
    parser.feed(html)
    results = []
    for block in parser.blocks:
        try:
            data = json.loads(block)
        except (ValueError, RecursionError):
            continue
        for node in nodes(data):
            types = node.get("@type", [])
            types = [types] if isinstance(types, str) else types
            if not isinstance(types, list) or not any(isinstance(t, str) and (t == "Event" or t.endswith("Event")) for t in types):
                continue
            status = str(node.get("eventStatus", ""))
            if any(s in status for s in ("Cancelled", "Postponed")):
                continue
            locations = node.get("location", {})
            locations = locations if isinstance(locations, list) else [locations]
            physical = next((loc for loc in locations if isinstance(loc, dict) and loc.get("address")), {})
            virtual = any(isinstance(loc, dict) and loc.get("@type") == "VirtualLocation" for loc in locations)
            attendance = str(node.get("eventAttendanceMode", ""))
            online = virtual or "OnlineEvent" in attendance
            hybrid = "MixedEvent" in attendance or bool(physical and online)
            address = physical.get("address", {})
            city = address.get("addressLocality") if isinstance(address, dict) else None
            if not city and online:
                city = "Online"
            title, description = plain(node.get("name")), plain(node.get("description"))
            content = (title + " " + description).casefold()
            kind = "hackathon" if any(w in content for w in ("hackathon", "hack day", "build weekend")) else "workshop" if "workshop" in content else "meetup"
            organizer = node.get("organizer", {})
            if isinstance(organizer, list):
                organizer = organizer[0] if organizer else {}
            try:
                payload = EventInput(title=title, description=description, city=city or "Unknown",
                                     start_at=node.get("startDate"), end_at=node.get("endDate"),
                                     venue=plain(physical.get("name")) or "See organizer page",
                                     url=urljoin(source_url, str(node.get("url") or source_url)),
                                     organizer=plain(organizer.get("name")) if isinstance(organizer, dict) and organizer.get("name") else "See organizer page",
                                     format="hybrid" if hybrid else "online" if online else "in_person", kind=kind)
            except (ValueError, TypeError):
                continue
            results.append(Event(**payload.model_dump(), id=make_id(str(payload.url)), provenance="public_import",
                                 source_urls=[source_url], retrieved_at=datetime.now(timezone.utc)))
            if len(results) >= 100:
                return results
    if not results:
        raise ValueError("No usable scheduled Event JSON-LD found. The page needs a title, description and timezone-aware start date. Try another public page or import JSON; blocked, cancelled and incomplete listings are not invented.")
    return results


async def read_public(client: httpx.AsyncClient, url: str) -> tuple[str, str, int]:
    for _ in range(4):
        validate_source_url(url)
        async with client.stream("GET", url) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers.get("location", ""))
                continue
            if response.status_code == 404:
                return "", url, 404
            response.raise_for_status()
            chunks, size = [], 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("Public page exceeds the 2 MB import limit")
                chunks.append(chunk)
            return b"".join(chunks).decode("utf-8", errors="replace"), url, response.status_code
    raise ValueError("Too many redirects; use the final supported event URL")


async def import_public_url(url: str) -> list[Event]:
    validate_source_url(url)
    async with httpx.AsyncClient(timeout=12, follow_redirects=False, trust_env=False, headers={"User-Agent": USER_AGENT}) as client:
        # Respect each destination's robots policy, including supported cross-host redirects.
        current = url
        for _ in range(4):
            parts = urlsplit(current)
            robots_url = f"https://{parts.hostname}/robots.txt"
            robots, _, status = await read_public(client, robots_url)
            if status != 404:
                rules = RobotFileParser()
                rules.parse(robots.splitlines())
                if not rules.can_fetch("HackRadar", current):
                    raise ValueError("This source's robots policy does not allow this import. Use an authorized JSON export instead.")
            # Do not follow an event redirect until its destination robots rules are checked.
            async with client.stream("GET", current) as response:
                if response.is_redirect:
                    current = validate_source_url(urljoin(current, response.headers.get("location", "")))
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "html" not in content_type:
                    raise ValueError("The URL must return an HTML event page")
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError("Public page exceeds the 2 MB import limit")
                    chunks.append(chunk)
                return parse_events(b"".join(chunks).decode("utf-8", errors="replace"), current)
        raise ValueError("Too many redirects; use the final supported event URL")
