#!/usr/bin/env bash
# Double-click to publish (macOS opens .command files in Terminal).
# Shows what changed, asks for a commit message, then runs
# scripts/publish.sh (tests → build → commit → push → deploy).
#
# Also runnable from a terminal:  ./auto-publish.command

cd "$(dirname "$0")"

# Keep the window open at the end so results stay visible when launched
# by double-click, whether the run succeeded or failed.
finish() {
  echo
  read -r -n 1 -s -p "Press any key to close..."
  echo
}
trap finish EXIT

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository. See scripts/publish.sh for one-time setup." >&2
  exit 1
fi

# Nothing to do? Say so and stop before asking anything.
if git diff --quiet && git diff --cached --quiet \
   && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "Nothing to publish — working tree is clean."
  exit 0
fi

echo "Changes to be published:"
git status --short
echo

DEFAULT_MSG="Update blog $(date +%F)"
read -r -p "Commit message [$DEFAULT_MSG]: " MSG
MSG="${MSG:-$DEFAULT_MSG}"

echo
scripts/publish.sh "$MSG"
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "Done — deployment is running (Actions tab opened in your browser)."
else
  echo "Publish failed (exit $STATUS). Nothing was pushed. See the messages above." >&2
fi
exit "$STATUS"
