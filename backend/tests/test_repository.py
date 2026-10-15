from concurrent.futures import ThreadPoolExecutor
from datetime import date

from backend.app.repository import Repository, canonical_url, make_id
from backend.app.models import Event
from backend.app.seed import demo_events


def event(url="https://lu.ma/one", **updates):
    return Event.model_validate({**demo_events(date(2026, 10, 15))[0].model_dump(), "id": make_id(url), "url": url, "provenance": "user_import", "source_urls": [url], "end_at": None, **updates})


def test_canonical_url_preserves_meaningful_query_parameters():
    assert canonical_url("https://LU.MA/event/?utm_source=test&b=2&a=1#tickets") == "https://lu.ma/event?a=1&b=2"
    assert canonical_url("https://lu.ma/?event=1") != canonical_url("https://lu.ma/?event=2")


def test_deduplication_merges_sources_and_url_aliases(tmp_path):
    repo = Repository(str(tmp_path / "events.db"))
    first = event()
    second = event("https://www.eventbrite.com/other", title="THE AGENT FOUNDRY!")
    result = repo.import_events([first, second, event("https://lu.ma/one?utm_source=email")])
    assert result == {"added": 1, "duplicates": 2, "received": 3}
    assert repo.import_events([second])["duplicates"] == 1
    assert len(repo.all()) == 1
    assert "https://www.eventbrite.com/other" in repo.all()[0].source_urls
    assert repo.all()[0].provenance == "user_import"


def test_persistence_and_distinct_dates(tmp_path):
    path = str(tmp_path / "events.db")
    repo = Repository(path)
    repo.import_events([event(), event("https://lu.ma/two", start_at=demo_events(date(2026, 10, 16))[0].start_at)])
    assert len(Repository(path).all()) == 2


def test_concurrent_duplicate_imports_are_atomic(tmp_path):
    repo = Repository(str(tmp_path / "events.db"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: repo.import_events([event()]), range(8)))
    assert sum(r["added"] for r in results) == 1
    assert len(repo.all()) == 1
