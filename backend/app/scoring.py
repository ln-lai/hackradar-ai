"""A versioned, reproducible score. LLM prose never changes the arithmetic."""
import re
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from .models import Dimension, Event, Preferences, Score

LONDON = ZoneInfo("Europe/London")
ALIASES = {
    "AI Agents": ["ai agent", "ai agents", "agentic", "autonomous agents", "multi-agent", "llm agents"],
    "FDE": ["fde", "forward deployed", "forward-deployed", "customer deployment", "customer engineering"],
    "Startups": ["startup", "startups", "founder", "founders", "venture", "entrepreneurship"],
    "Open Source": ["open source", "open-source", "oss"],
    "Climate Tech": ["climate", "sustainability", "decarbonisation", "decarbonization"],
}


def score_event(event: Event, prefs: Preferences, today: date) -> Score:
    text = f"{event.title} {event.description} {' '.join(event.tags)}".casefold()
    matches = {}
    for interest in prefs.interests:
        hit = next((a for a in ALIASES[interest] if re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)), None)
        if hit:
            matches[interest] = hit
    local = event.city.strip().casefold() == prefs.city.strip().casefold() and event.format != "online"
    online = prefs.include_online and event.format in ("online", "hybrid")
    event_day = event.start_at.astimezone(LONDON).date()
    in_window = today <= event_day <= today + timedelta(days=prefs.days)
    exclusions = []
    if not (local or online):
        exclusions.append("Outside your location preference")
    if not in_window:
        exclusions.append("Outside your date window")
    if event.provenance == "example" and not prefs.include_examples:
        exclusions.append("Examples are hidden")
    interest_points = 5 * len(matches) / len(prefs.interests)
    dimensions = [
        Dimension(label="Interests", earned=round(interest_points, 2), possible=5,
                  evidence="; ".join(f'{k}: “{v}”' for k, v in matches.items()) or "No selected interests found in the supplied text"),
        Dimension(label="Location", earned=2.5 if local else 2 if online else 0, possible=2.5,
                  evidence=f"{event.city} matches your city" if local else "Online attendance enabled" if online else f"{event.city} is outside your preference"),
        Dimension(label="Timing", earned=1.5 if in_window else 0, possible=1.5,
                  evidence=f"{event_day.isoformat()} · within {prefs.days} days" if in_window else "Outside your date window"),
        Dimension(label="Build format", earned={"hackathon": 1, "workshop": 0.5, "meetup": 0.25}[event.kind], possible=1,
                  evidence=f"Listed as a {event.kind}"),
    ]
    return Score(total=round(sum(d.earned for d in dimensions), 1), dimensions=dimensions,
                 matched_interests=list(matches), eligible=not exclusions, exclusions=exclusions)
