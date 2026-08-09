---
title: "Hello, World: How This Blog Works"
date: 2026-08-09
description: "A first post that doubles as a tour of what this little static blog can render."
tags:
  - Meta
  - Python
slug: hello-world
draft: false
---

Welcome. This site is a handful of Markdown files, a small Python script,
and GitHub Pages — nothing else. This first post exists mostly to prove
that everything renders the way it should.

## Writing is just Markdown -

Each article is one Markdown file with a bit of YAML front matter on top.
Paragraphs, *emphasis*, **strong text**, and [links](https://www.markdownguide.org/)
all work as you'd expect.

### Lists

A few reasons a hand-rolled generator is enough for a personal blog:

* You can read the entire build in one sitting.
* There is nothing to upgrade, patch, or migrate.
* The publishing workflow is `git push`.

### Code

Inline code like `python build.py` renders in a monospace face, and fenced
code blocks keep their formatting:

```python
def slugify(text: str) -> str:
    """Turn a title into a URL-safe slug."""
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")
```

### Blockquotes and tables

> Simplicity is a feature. Every dependency you don't add is a problem
> you never have to debug.

| Step | Command                | Result                  |
|------|------------------------|-------------------------|
| 1    | write a `.md` file     | new article drafted     |
| 2    | `git push`             | site rebuilt & deployed |

### Images

Images live under `static/assets/images/` and are referenced by absolute
path, for example:

```markdown
![A diagram of the build](/assets/images/hello-world/build-diagram.png)
```

That's the whole tour. New posts go in `content/posts/`, and the rest is
automatic.
