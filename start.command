#!/bin/bash
# Double-click to start CODEX at http://127.0.0.1:8000
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/uvicorn ]; then
  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt || exit 1
fi
if [ ! -f frontend/dist/index.html ]; then
  npm install --prefix frontend && npm run build --prefix frontend || exit 1
fi
(sleep 3 && open "http://127.0.0.1:8000") &
exec .venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
