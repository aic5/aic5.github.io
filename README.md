# Personal Blog

A minimal static blog: Markdown files in, static HTML out. Built by a
single Python script (`build.py`), deployed automatically to GitHub Pages
by GitHub Actions. No database, no backend, no JavaScript, no framework.

The publishing workflow is the whole point:

1. Write an article as a Markdown file in `content/posts/`.
2. Commit and push to `main`.
3. GitHub Actions builds the site and deploys it to GitHub Pages.

## Initial setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then edit `config.py` and set `SITE_NAME`, `SITE_URL`, `SITE_DESCRIPTION`,
`AUTHOR_NAME`, and (optionally) `CUSTOM_DOMAIN`. `SITE_URL` must be the
final public URL of the site — it is used for canonical URLs, Open Graph
tags, the RSS feed, and the sitemap.

## Everyday workflow (helper scripts)

Three small scripts in `scripts/` cover the routine tasks:

```bash
scripts/new-post.sh    # create a blank draft (prompts for title + slug)
scripts/serve.sh       # rebuild and preview locally (optional port arg)
scripts/publish.sh     # test + build + commit + push (deploys via Actions)
```

`new-post.sh` creates `content/posts/YYYY-MM-DD-<slug>.md` with `draft: true`
so it stays unpublished while you write. `serve.sh` rebuilds, opens your
browser, and serves `dist/` until Ctrl+C (default port 8010; pass another
as an argument if it's busy). `publish.sh` refuses to push if the tests or
build fail, so a broken post can't reach GitHub.

## Writing a new article

Create a Markdown file in `content/posts/` (or let `scripts/new-post.sh`
do it for you). The file name doesn't affect
the URL (the `slug` does), but `YYYY-MM-DD-title.md` keeps the folder tidy:

```markdown
---
title: "Why AI Changes Financial Analysis"
date: 2026-08-10
description: "A short description of the article."
tags:
  - AI
  - Finance
slug: why-ai-changes-financial-analysis
draft: false
---

Article content begins here.
```

Field notes:

* `title` and `date` are **required**; the build fails without them.
* `slug` is optional — if omitted, a URL-safe slug is generated from the
  title. The article is published at `/articles/<slug>/`.
* `tags` is optional. Each tag gets its own page at `/tags/<tag>/`.
  Tags are grouped case-insensitively ("AI" and "ai" share a page).
* `description` is optional but recommended — it appears on the homepage,
  in search-engine snippets, and in the RSS feed.
* `draft: true` keeps a post out of the build entirely. Flip it to
  `false` (or delete the line) to publish.

Duplicate slugs, malformed YAML, invalid dates, and missing required
fields all fail the build with a message naming the offending file.

### Images

Put images in `static/assets/images/`, ideally in a folder named after the
post's slug, and reference them by absolute path:

```markdown
![Alt text](/assets/images/my-post-slug/photo.jpg)
```

Everything under `static/` is copied verbatim into the site root, so
`static/assets/...` is served at `/assets/...`.

## Local preview

```bash
python build.py
python -m http.server 8010 --directory dist
```

Then open <http://localhost:8010>. Rebuild after each change (the build
takes well under a second).

Run the tests with:

```bash
python -m unittest discover -s tests
```

## Publishing

Pushing to `main` triggers `.github/workflows/deploy.yml`, which installs
dependencies, runs the tests, runs `python build.py`, and deploys `dist/`
to GitHub Pages using the official Pages actions (no `gh-pages` branch).

One-time repository setup: in **Settings → Pages**, set **Source** to
**GitHub Actions**. That's it — the next push to `main` deploys.

## Custom domain

1. In `config.py`, set `SITE_URL = "https://blog.example.com"` and
   `CUSTOM_DOMAIN = "blog.example.com"`. The build then emits a `CNAME`
   file into `dist/`, which keeps the domain configured across deploys.
2. At your DNS provider, add a record pointing at GitHub Pages:
   * subdomain (e.g. `blog.example.com`): a `CNAME` record to
     `<your-github-username>.github.io`
   * apex domain (e.g. `example.com`): `A` records to GitHub Pages' IPs
     (185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153)
3. In the repository's **Settings → Pages**, enter the custom domain and
   enable **Enforce HTTPS** once the certificate is issued (this can take
   a few minutes after DNS propagates).

## Reader stats

The site ships with zero JavaScript. If you want basic view counts, set
`ANALYTICS_HTML` in `config.py` to a lightweight analytics snippet —
[GoatCounter](https://www.goatcounter.com) is free for personal use,
requires no cookie banner, and gives per-page view counts. The snippet is
injected at the end of every page.

## Architecture

```text
content/posts/*.md ──┐
content/about.md ────┤
                     ├── build.py ──► dist/  ──► GitHub Pages
templates/*.html ────┤
static/** ───────────┘
```

`build.py` runs top to bottom in one pass:

1. **Clean** — `dist/` is deleted and recreated, so every build is
   reproducible from scratch.
2. **Copy static** — `static/` is copied into `dist/` (CSS, images).
3. **Load posts** — every `content/posts/*.md` is split into YAML front
   matter + Markdown body, validated (required fields, date format,
   URL-safe slug, duplicate-slug check), drafts are dropped, and the rest
   are sorted newest-first.
4. **Render** — Markdown becomes HTML via `python-markdown` (with
   `fenced_code` and `tables`), then Jinja2 templates (autoescaping on)
   produce: one page per article (`/articles/<slug>/`), the homepage,
   `/archive/` grouped by year, one page per tag (`/tags/<slug>/`),
   `/about/`, `feed.xml` (RSS 2.0), `sitemap.xml`, and `404.html`.
5. **Housekeeping** — a `.nojekyll` file is written, plus `CNAME` if
   `CUSTOM_DOMAIN` is set.

Every page is a directory with an `index.html`, which is how the site
gets clean URLs (`/articles/foo/` instead of `/articles/foo.html`)
without any server configuration.

Dependencies are deliberately few: `Jinja2` (templating + escaping),
`Markdown` (Markdown → HTML), `PyYAML` (front matter). The tests use
only the standard library (`unittest`).

## Repository layout

```text
├── content/
│   ├── posts/            # one .md file per article
│   ├── about.md          # standalone pages: every content/*.md
│   └── projects.md       #   becomes /<name>/ on the site
├── templates/            # Jinja2 templates (base, index, article, ...)
├── static/
│   ├── css/style.css     # the entire design
│   └── assets/images/    # images referenced by posts
├── build.py              # the whole generator
├── config.py             # site name, URL, author, options
├── scripts/              # new-post.sh, serve.sh, publish.sh
├── tests/                # unit tests for the generator
└── .github/workflows/deploy.yml
```
