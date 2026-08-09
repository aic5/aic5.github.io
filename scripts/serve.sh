#!/usr/bin/env bash
# Rebuild the site and serve it locally for preview.
#
# Usage:  scripts/serve.sh [port]     (default port: 8010)
#
# Rebuilds dist/, opens your browser, and serves until you press Ctrl+C.

set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${1:-8010}"

# Prefer the project venv's Python if it exists.
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

# Refuse early (with a helpful message) if the port is already taken.
if lsof -i ":$PORT" >/dev/null 2>&1; then
  echo "Port $PORT is already in use:"
  lsof -i ":$PORT" | tail -n +2 | awk '{print "  " $1 " (pid " $2 ")"}' | sort -u
  echo "Stop that process, or pick another port: scripts/serve.sh 8020"
  exit 1
fi

"$PY" build.py

URL="http://localhost:$PORT"
echo "Serving at $URL  (Ctrl+C to stop)"

# Open the browser once the server is up (macOS: open, Linux: xdg-open).
( sleep 1
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
  fi
) &

exec "$PY" -m http.server "$PORT" --directory dist
