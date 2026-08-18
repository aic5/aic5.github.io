#!/usr/bin/env bash
# Create a blank draft post in content/posts/.
#
# Usage:  scripts/new-post.sh
#
# Prompts for a title and a slug (suggesting one derived from the title),
# then creates content/posts/YYYY-MM-DD-<slug>.md with draft: true so it
# won't be published until you flip it.

set -euo pipefail
cd "$(dirname "$0")/.."

PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

read -r -p "Title: " TITLE
if [ -z "$TITLE" ]; then
  echo "A title is required." >&2
  exit 1
fi

# Reuse the generator's own slugify() so the suggestion matches the build.
SUGGESTED="$("$PY" -c "import build, sys; print(build.slugify(sys.argv[1]))" "$TITLE")"

read -r -p "Slug [$SUGGESTED]: " SLUG
SLUG="${SLUG:-$SUGGESTED}"

# Validate the slug the same way the build will.
"$PY" -c "
import build, sys
slug = sys.argv[1]
if not slug or slug != build.slugify(slug):
    print(f'Slug {slug!r} is not URL-safe. Try: {build.slugify(slug)!r}', file=sys.stderr)
    sys.exit(1)
" "$SLUG"

TODAY="$(date +%F)"
FILE="content/posts/${TODAY}-${SLUG}.md"

if [ -e "$FILE" ]; then
  echo "Refusing to overwrite existing file: $FILE" >&2
  exit 1
fi

cat > "$FILE" << EOF
---
title: "${TITLE}"
date: ${TODAY}
description: ""
tags: []
# image: /assets/images/${SLUG}/cover.jpg   # uncomment for social-share preview
slug: ${SLUG}
draft: true
---

Write your article here.
EOF

echo "Created $FILE  (draft: true — flip to false when ready to publish)"

# Open it in your editor if one is configured.
if [ -n "${EDITOR:-}" ]; then
  "$EDITOR" "$FILE"
fi
