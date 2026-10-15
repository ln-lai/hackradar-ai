from datetime import date, datetime, timedelta

import pytest
from pydantic import ValidationError

from backend.app.models import EventInput, Preferences
from backend.app.scoring import LONDON, score_event
from backend.app.seed import demo_events

TODAY = date(2026, 10, 15)


def test_default_scores_are_explainable_and_bounded():
    for event in demo_events(TODAY):
        score = score_event(event, Preferences(), TODAY)
        assert 0 <= score.total <= 10
        assert score.total == round(sum(d.earned for d in score.dimensions), 1)
        assert all(0 <= d.earned <= d.possible and d.evidence for d in score.dimensions)
    assert score_event(demo_events(TODAY)[0], Preferences(), TODAY).total == 10


@pytest.mark.parametrize("offset,eligible", [(-1, False), (0, True), (30, True), (31, False)])
def test_inclusive_calendar_window(offset, eligible):
    event = demo_events(TODAY)[0].model_copy(update={"start_at": datetime(2026, 10, 15, 10, tzinfo=LONDON) + timedelta(days=offset)})
    assert score_event(event, Preferences(), TODAY).eligible is eligible


def test_location_is_hard_filter_even_when_score_passes():
    event = next(e for e in demo_events(TODAY) if e.city == "Manchester")
    score = score_event(event, Preferences(), TODAY)
    assert score.total >= 7
    assert not score.eligible


def test_online_opt_in_and_discount():
    event = next(e for e in demo_events(TODAY) if e.format == "online")
    assert not score_event(event, Preferences(), TODAY).eligible
    score = score_event(event, Preferences(include_online=True), TODAY)
    assert score.eligible and score.total == 9.5


def test_examples_never_leak_into_real_only_results():
    assert not score_event(demo_events(TODAY)[0], Preferences(include_examples=False), TODAY).eligible


def test_london_date_conversion_across_midnight():
    event = demo_events(TODAY)[0].model_copy(update={"start_at": datetime.fromisoformat("2026-10-14T23:30:00Z")})
    assert score_event(event, Preferences(), TODAY).eligible


def test_london_dst_cutoff():
    event = demo_events(TODAY)[0].model_copy(update={"start_at": datetime.fromisoformat("2026-10-25T00:30:00Z")})
    assert score_event(event, Preferences(days=10), TODAY).eligible
    event.start_at = datetime.fromisoformat("2026-10-25T23:30:00Z")
    assert score_event(event, Preferences(days=10), TODAY).eligible


def test_phrase_boundaries_and_interest_reweighting():
    event = demo_events(TODAY)[0].model_copy(update={"title": "Different event", "description": "An OSSify and FDEngine talk.", "tags": []})
    assert score_event(event, Preferences(interests=["FDE", "Open Source"]), TODAY).dimensions[0].earned == 0
    event.description = "Learn customer engineering at an open-source hackathon."
    assert score_event(event, Preferences(interests=["FDE", "Open Source"]), TODAY).dimensions[0].earned == 5


def test_empty_preferences_and_naive_dates_are_rejected():
    with pytest.raises(ValidationError):
        Preferences(interests=[])
    with pytest.raises(ValidationError):
        Preferences(city="  ")
    event = demo_events(TODAY)[0].model_dump()
    event["start_at"] = "2026-10-22T10:00:00"
    with pytest.raises(ValidationError):
        EventInput.model_validate(event)


def test_duplicate_interests_do_not_distort_score():
    assert Preferences(interests=["FDE", "FDE"]).interests == ["FDE"]
