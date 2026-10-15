# Publish the repository

The project's GitHub repository is [ln-lai/hackradar-ai](https://github.com/ln-lai/hackradar-ai). The instructions below explain how to publish your own copy or configure a hosted demo.

## Using GitHub CLI

From the project directory, after reviewing the source and checking that `.env*`, local databases and dependencies are ignored:

```bash
gh auth login
# Skip initialization if already initialized.
git init -b main
git add .
git commit -m "Build HackRadar AI MVP"

# Creates a PUBLIC repository; use --private if you want private review first.
gh repo create hackradar-ai --public --source=. --remote=origin --push
```

If Git requests author configuration, set your own name and email before committing. Do not use an API key as a Git credential.

## Using the GitHub website

1. Create a new empty repository under your GitHub account. Choose visibility intentionally. Do not pre-create a README or license because this project includes them.
2. Copy that repository's HTTPS or SSH URL.
3. From this project directory, run:

```bash
# If working from the source ZIP, initialize Git first.
git init -b main
git add .
git commit -m "Build HackRadar AI MVP"
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

If a remote is already configured, inspect it before changing anything. If a first commit already exists, skip the commit step. GitHub authentication is handled by your Git credential manager or SSH, not this application.

Suggested description: **Explainable hackathon discovery for builders. Next.js + FastAPI, transparent scoring, source-aware imports and optional Grok preparation briefs.**

Suggested topics: `hackathon`, `nextjs`, `fastapi`, `grok`, `ai-agents`, `developer-tools`.

## A hosted demo

The complete app needs two processes: Next.js and Python/FastAPI. It is not a static website. Deploy the frontend to a Next.js-compatible host and the backend to a Python host with a persistent disk, or run both on a controlled server.

- Set server-only `BACKEND_URL` for the frontend.
- Set a matching `HACKRADAR_API_TOKEN` on both services to protect the backend endpoint.
- Keep the backend private where possible; the shared API token is not frontend-user authentication.
- Set `DATABASE_PATH` to a persistent path. Stateless/ephemeral deployments lose imports.
- Add login/access control and quotas before allowing public imports or paid Grok calls. This MVP is single-user and does not implement these controls.
- Use HTTPS on the public origin. Keep provider secrets out of all browser bundles and repository files.
- Build with `pnpm build`; serve with `pnpm start` (the local script binds loopback; configure the host binding explicitly on the hosting platform).
- Run `uvicorn backend.app.main:app` behind the host's private networking/reverse proxy.

Run the supplied tests before publishing. Actual cloud deployment and real provider calls need their own environment checks; local checks do not prove a remote deployment works.
