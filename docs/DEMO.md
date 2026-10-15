# HackRadar AI — demo guide

## 30-second pitch

“Finding the right hackathon means checking several sites and guessing which events are worth your time. HackRadar brings listings into one personal radar, explains how each one fits your interests and calendar, and helps you prepare. The default profile is built around AI Agents, FDE and startups in London. Every score is inspectable, every source is labeled, and optional Grok turns a match into a preparation brief.”

## Walkthrough

1. **Problem:** Start at Discover. Explain that the personal profile filters noisy listings into a shortlist.
2. **Trust:** Point to the example-data banner. These are deliberately fictional, reusable fixtures.
3. **Evidence:** Open The Agent Foundry. Show the interest, location, timing and format contributions.
4. **Action:** Generate the local brief. Explain that Grok can provide a model-generated variant when configured, while scoring remains deterministic.
5. **Personalization:** Save a match. Enable online participation; the remote example appears. Try a different time window or interest.
6. **Real data path:** Import an authorized event JSON or a supported public Event JSON-LD URL. Import twice to show duplicate counts and preserved provenance.
7. **Close:** Turn off examples. Explain that the product exposes an honest empty state until real records are supplied.

## Technical points to discuss

- A single score implementation on the backend, with versioned aliases and a visible rubric.
- Explicit London timezone and inclusive calendar boundaries.
- Atomic SQLite imports with canonical URL aliases and content fingerprints.
- Browser → same-origin Next.js proxy → FastAPI; optional secrets stay server-side.
- Failures are visible: API offline, unsupported source, malformed JSON, unavailable Grok.
- Backend and browser tests cover the real workflow, including responsive layout.

## Roadmap, not current features

Add official feed adapters with source-specific licenses, scheduled refreshes, user accounts, Postgres/Supabase isolation, GitHub skill extraction with consent, and team formation. Evaluate recommendations with user feedback before replacing the baseline with semantic ranking.
