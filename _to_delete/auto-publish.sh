#!/usr/bin/env bash
# Interactive publish: shows what changed, asks for a commit message,
# then runs scripts/publish.sh (tests → build → commit → push → deploy).
#
# Usage:  ./auto-publish.sh

set -euo pipefail
cd "$(dirname "$0")"

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
exec scripts/publish.sh "$MSG"
