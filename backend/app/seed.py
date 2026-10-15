"""Fictional demo fixtures, always labeled and dated relative to the London day."""
from datetime import date, datetime, time, timedelta

from .models import Event
from .scoring import LONDON


def demo_events(today: date) -> list[Event]:
    rows = [
        ("agent-foundry", "The Agent Foundry", 7, "London", "Shoreditch · fictional venue", ["AI Agents", "FDE", "Startups"], "hackathon", "in_person", "Build useful AI agents for real customer deployment. Pair with startup founders and forward deployed engineers for a weekend of shipping, feedback and demos.", "Free · example"),
        ("zero-to-one", "Zero to One: AI Build Weekend", 12, "London", "King’s Cross · fictional venue", ["AI Agents", "Startups"], "hackathon", "in_person", "An AI agents hackathon for founders. Turn a startup idea into a working prototype with product mentors and a final demo showcase.", "£15 · example"),
        ("deployed", "Deployed / Customer Engineering Lab", 18, "London", "South Bank · fictional venue", ["FDE", "AI Agents"], "hackathon", "in_person", "A hands-on FDE challenge: build agentic workflows for customer engineering scenarios using realistic synthetic business data.", "Free · example"),
        ("founder-lab", "Founders × Agents Lab", 23, "London", "White City · fictional venue", ["AI Agents", "FDE", "Startups"], "workshop", "in_person", "A small startup workshop with founders, AI agents prototyping and forward deployed engineering exercises. Bring a laptop and a customer problem.", "£10 · example"),
        ("open-build", "Open Build: Maintainers Weekend", 9, "London", "Hackney · fictional venue", ["Open Source"], "hackathon", "in_person", "Contribute to open source developer tools with maintainers. A welcoming weekend of documentation, bug fixes and community demos.", "Free · example"),
        ("climate", "Climate / Code", 16, "London", "Bermondsey · fictional venue", ["Climate Tech", "Startups"], "hackathon", "in_person", "Help climate startups prototype sustainability and decarbonisation tools with community data and practical mentors.", "Free · example"),
        ("global-agents", "Global Agents Sprint", 5, "Online", "Remote · fictional event", ["AI Agents", "FDE", "Startups", "Open Source"], "hackathon", "online", "A remote open source AI agents sprint for startup founders and FDE practitioners, focused on real customer deployment challenges.", "Free · example"),
        ("manchester", "Northern Builders", 10, "Manchester", "Fictional venue", ["AI Agents", "FDE", "Startups"], "hackathon", "in_person", "Build AI agents with startup founders and forward deployed engineers in Manchester.", "Free · example"),
        ("later", "Future Foundry", 45, "London", "Fictional venue", ["AI Agents", "FDE", "Startups"], "hackathon", "in_person", "An AI agents and FDE startup hackathon deliberately outside the default date window.", "Free · example"),
    ]
    events = []
    for slug, title, offset, city, venue, tags, kind, mode, description, cost in rows:
        start = datetime.combine(today + timedelta(days=offset), time(10), tzinfo=LONDON)
        events.append(Event(id=f"demo-{slug}", title=title, description=description, start_at=start,
                            end_at=start + timedelta(hours=8), city=city, venue=venue, tags=tags,
                            kind=kind, format=mode, cost=cost, organizer="HackRadar fictional demo",
                            url=f"https://example.com/hackradar/{slug}", provenance="example", source_urls=[]))
    return events
