from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

Interest = Literal["AI Agents", "FDE", "Startups", "Open Source", "Climate Tech"]


class Preferences(BaseModel):
    city: str = Field(default="London", min_length=1, max_length=80)
    interests: list[Interest] = Field(default_factory=lambda: ["AI Agents", "FDE", "Startups"], min_length=1, max_length=5)
    days: int = Field(default=30, ge=1, le=90)
    min_score: float = Field(default=7, ge=0, le=10)
    include_online: bool = False
    include_examples: bool = True

    @field_validator("city")
    @classmethod
    def clean_city(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("City cannot be blank")
        return value.strip()

    @field_validator("interests")
    @classmethod
    def unique_interests(cls, value: list[Interest]) -> list[Interest]:
        return list(dict.fromkeys(value))


class EventInput(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=12000)
    start_at: datetime
    end_at: datetime | None = None
    city: str = Field(min_length=1, max_length=120)
    venue: str = Field(default="See organizer page", max_length=240)
    url: HttpUrl
    organizer: str = Field(default="See organizer page", max_length=180)
    tags: list[str] = Field(default_factory=list, max_length=20)
    format: Literal["in_person", "online", "hybrid"] = "in_person"
    kind: Literal["hackathon", "workshop", "meetup"] = "hackathon"
    cost: str = Field(default="See organizer page", max_length=100)

    @field_validator("title", "city")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def bounded_tags(cls, values: list[str]) -> list[str]:
        if any(len(v) > 60 for v in values):
            raise ValueError("Tags must be 60 characters or less")
        return list(dict.fromkeys(v.strip() for v in values if v.strip()))

    @field_validator("start_at", "end_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Use an ISO datetime with a UTC offset, e.g. +01:00 or Z")
        return value

    @model_validator(mode="after")
    def valid_dates(self):
        if self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must not precede start_at")
        return self


class Event(EventInput):
    id: str
    provenance: Literal["example", "public_import", "user_import"]
    source_urls: list[str] = Field(default_factory=list)
    retrieved_at: datetime | None = None


class Dimension(BaseModel):
    label: str
    earned: float
    possible: float
    evidence: str


class Score(BaseModel):
    total: float
    engine: str = "Transparent rules v1"
    dimensions: list[Dimension]
    matched_interests: list[str]
    eligible: bool
    exclusions: list[str]


class RankedEvent(BaseModel):
    event: Event
    score: Score


class SearchRequest(BaseModel):
    preferences: Preferences = Field(default_factory=Preferences)
    query: str = Field(default="", max_length=200)
    sort: Literal["score", "date"] = "score"


class SearchResult(BaseModel):
    results: list[RankedEvent]
    total_scanned: int
    matching: int
    examples: int
    imported: int
    as_of: date
    timezone: str = "Europe/London"


class ImportRequest(BaseModel):
    events: list[EventInput] = Field(min_length=1, max_length=100)


class URLImportRequest(BaseModel):
    url: HttpUrl


class BriefRequest(BaseModel):
    preferences: Preferences = Field(default_factory=Preferences)
    use_grok: bool = False
