# Local validation — 15 October 2026

The completed MVP was verified on macOS with Node.js 24.19.0, Python 3.12.14 and installed Google Chrome.

| Check | Result |
| --- | --- |
| Backend tests (`python -m pytest -q`) | **43 passed** |
| Production build (`next build --webpack`) | **Passed**, pages and API route generated |
| TypeScript (`pnpm typecheck`) | **Passed** |
| Browser tests (`playwright test`) | **8 passed**, isolated services and database |
| Dependency consistency (`python -m pip check`) | **Passed** |
| Launcher (`bash scripts/dev.sh`) | **Passed**, page returned 200 and default search returned 4 matches |
| Desktop and mobile screenshots | Visually reviewed; no horizontal overflow in mobile test |
| Git whitespace check | Passed |

The browser journeys exercise default matching, detailed evidence and local briefs, saved state across reload, filters/search/sorting, hiding examples, unsupported-source errors, same-origin request handling, JSON import/re-import and mobile interaction.

The first browser run exposed an origin-comparison bug caused by Next.js normalizing an internal URL to localhost. The proxy now compares the browser origin with the incoming Host header, and a regression test verifies both valid same-origin access and rejected cross-origin access. All final browser tests passed.

## Verification boundaries

- All built-in event records are fictional. No real event was preloaded or verified.
- Public-page importer parsing, robots behavior, redirects, size limits and provenance were tested using HTTP fixtures. Availability of any specific live provider page is not guaranteed.
- Grok success/failure handling was tested with mocked Responses API output. A live call was not made because no user API key/model was configured.
- Supabase is not used; the implemented persistent store is SQLite.
- The source is published at [ln-lai/hackradar-ai](https://github.com/ln-lai/hackradar-ai). The 45 uploaded files, including screenshots and executable script modes, were verified against the local Git tree. Remote CI results are tracked separately in [GitHub Actions](https://github.com/ln-lai/hackradar-ai/actions); the passing checks listed above are local results.
- The preview services are stopped after validation. Use the included launcher to start the demo again.
