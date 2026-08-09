#!/usr/bin/env bash
# Test, build, commit, and push to GitHub — which triggers the Pages deploy.
#
# Usage:  scripts/publish.sh ["commit message"]
#
# Runs the test suite and a full build first, so a broken post never even
# gets committed. The push to main is what kicks off GitHub Actions.

set -euo pipefail
cd "$(dirname "$0")/.."

PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This folder is not a git repository yet. One-time setup:" >&2
  echo "  git init -b main" >&2
  echo "  git add -A && git commit -m 'Initial commit'" >&2
  echo "  git remote add origin git@github.com:YOUR-USERNAME/YOUR-REPO.git" >&2
  echo "  git push -u origin main" >&2
  exit 1
fi

echo "Running tests..."
"$PY" -m unittest discover -s tests

echo "Verifying build..."
"$PY" build.py

if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "Nothing to publish — working tree is clean."
  exit 0
fi

MSG="${1:-Publish $(date +%F)}"

git add -A
git commit -m "$MSG"
git push origin main

echo "Pushed. GitHub Actions is now building and deploying the site."
echo "Watch progress in your repository's Actions tab."
