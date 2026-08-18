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

# Detect newly published articles (new files, or drafts flipped to false)
# so we can remind you to email subscribers after the push.
NEW_POSTS="$(
  for f in $(git diff --name-only HEAD -- content/posts/ ; git ls-files --others --exclude-standard content/posts/); do
    [ -f "$f" ] || continue
    grep -qiE '^draft:\s*true' "$f" && continue
    if git cat-file -e "HEAD:$f" 2>/dev/null; then
      # Existing file: only counts if it *was* a draft before this change.
      git show "HEAD:$f" | grep -qiE '^draft:\s*true' || continue
    fi
    grep -m1 -E '^title:' "$f" | sed -E 's/^title:\s*//; s/^"(.*)"$/\1/'
  done | sort -u
)"

git add -A
git commit -m "$MSG"
git push origin main

echo "Pushed. GitHub Actions is now building and deploying the site."

# Open the repository's Actions tab so the deployment can be tracked.
# Derives the URL from the origin remote (works for HTTPS and SSH remotes).
REMOTE="$(git remote get-url origin)"
ACTIONS_URL="$(echo "$REMOTE" \
  | sed -E 's#^git@github\.com:#https://github.com/#; s#\.git$##')/actions"

case "$ACTIONS_URL" in
  https://github.com/*)
    echo "Opening $ACTIONS_URL"
    if command -v open >/dev/null 2>&1; then open "$ACTIONS_URL"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$ACTIONS_URL"
    else echo "Track the deployment at: $ACTIONS_URL"
    fi
    ;;
  *)
    echo "Track the deployment in your repository's Actions tab."
    ;;
esac

# Reminder: subscribers are emailed manually (Buttondown free plan).
if [ -n "$NEW_POSTS" ]; then
  echo
  echo "New article(s) published:"
  echo "$NEW_POSTS" | sed 's/^/  - /'
  echo "Remember to email subscribers: https://buttondown.com/emails/new"
fi
