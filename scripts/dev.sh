#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Codex desktop bundles Node; use it only when Node isn't already installed.
runtime="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies"
if ! command -v node >/dev/null 2>&1 && [ -x "$runtime/node/bin/node" ]; then
  export PATH="$runtime/node/bin:$runtime/bin/fallback:$PATH"
fi
if [ ! -x .venv/bin/python ]; then
  echo 'Set up the Python environment first; see README.md.' >&2
  exit 1
fi
if ! command -v pnpm >/dev/null 2>&1; then
  echo 'Install Node.js 24 and pnpm 11.25.0; see README.md.' >&2
  exit 1
fi
cleanup() {
  kill "${backend_pid:-}" "${frontend_pid:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
backend_pid=$!
pnpm dev &
frontend_pid=$!
echo 'HackRadar → http://127.0.0.1:3000  |  API docs → http://127.0.0.1:8000/docs'
while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
  sleep 2
done
echo 'One service stopped. Stopping the other service.' >&2
exit 1
