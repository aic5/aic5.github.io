#!/usr/bin/env bash
# Rebuild the site and serve it locally for preview.
#
# Usage:  scripts/serve.sh [-kill] [port]      (default port: 8010)
#
#   -kill   If something is already listening on the port, kill it first
#           instead of refusing to start.
#
# Rebuilds dist/, opens your browser, and serves until you press Ctrl+C.

set -euo pipefail
cd "$(dirname "$0")/.."

PORT=8010
KILL=0

for arg in "$@"; do
  case "$arg" in
    -kill|--kill|-k)
      KILL=1
      ;;
    *[!0-9]*|'')
      echo "Unknown argument: $arg" >&2
      echo "Usage: scripts/serve.sh [-kill] [port]" >&2
      exit 1
      ;;
    *)
      PORT="$arg"
      ;;
  esac
done

# Prefer the project venv's Python if it exists.
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

if lsof -i ":$PORT" >/dev/null 2>&1; then
  if [ "$KILL" -eq 1 ]; then
    PIDS="$(lsof -ti ":$PORT")"
    echo "Killing process(es) on port $PORT: $PIDS"
    kill $PIDS 2>/dev/null || true
    sleep 1
    if lsof -i ":$PORT" >/dev/null 2>&1; then
      echo "Still busy after kill; forcing (kill -9)..."
      kill -9 $(lsof -ti ":$PORT") 2>/dev/null || true
      sleep 1
    fi
    if lsof -i ":$PORT" >/dev/null 2>&1; then
      echo "Could not free port $PORT." >&2
      exit 1
    fi
  else
    echo "Port $PORT is already in use:"
    lsof -i ":$PORT" | tail -n +2 | awk '{print "  " $1 " (pid " $2 ")"}' | sort -u
    echo "Kill it and serve:    scripts/serve.sh -kill"
    echo "Or pick another port: scripts/serve.sh 8020"
    exit 1
  fi
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
