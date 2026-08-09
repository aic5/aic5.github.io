#!/usr/bin/env python3
"""Static-site generator for the blog.

Reads Markdown posts from content/posts/, renders them through Jinja2
templates, and writes a complete static site into dist/.

Usage:
    python build.py

The build fails loudly (non-zero exit, clear message naming the offending
file) on malformed front matter, missing required fields, invalid dates,
or duplicate slugs.
"""

from __future__ import annotations

import datetime
import html
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

import config

ROOT = Path(__file__).parent.resolve()
CONTENT_DIR = ROOT / "content"
POSTS_DIR = CONTENT_DIR / "posts"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
DIST_DIR = ROOT / "dist"

MARKDOWN_EXTENSIONS = ["fenced_code", "tables", "smarty"]


class BuildError(Exception):
    """A fatal problem with the site content or configuration."""


# ---------------------------------------------------------------------------
# Parsing and validation
# ---------------------------------------------------------------------------

@dataclass
class Post:
    title: str
    date: datetime.date
    description: str
    tags: list[str]
    slug: str
    draft: bool
    body_markdown: str
    source: Path
    body_html: str = ""
    image: str = ""  # optional social/share image, site-absolute path

    @property
    def url_path(self) -> str:
        return f"/articles/{self.slug}/"


@dataclass
class Page:
    """A standalone page (e.g. About) from content/*.md."""
    title: str
    slug: str
    body_html: str
    source: Path
    description: str = ""

    @property
    def url_path(self) -> str:
        return f"/{self.slug}/"


def slugify(text: str) -> str:
    """Turn arbitrary text into a URL-safe slug.

    "Why AI Changes Financial Analysis" -> "why-ai-changes-financial-analysis"
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def split_front_matter(raw: str, source: Path) -> tuple[dict, str]:
    """Split a Markdown file into (front-matter dict, body)."""
    if not raw.startswith("---"):
        raise BuildError(f"{source}: file must start with '---' YAML front matter.")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", raw, re.DOTALL)
    if not match:
        raise BuildError(f"{source}: front matter is not closed with a '---' line.")
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise BuildError(f"{source}: malformed YAML front matter: {exc}") from exc
    if not isinstance(meta, dict):
        raise BuildError(f"{source}: front matter must be a YAML mapping.")
    body = raw[match.end():]
    return meta, body


def parse_date(value, source: Path) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip())
        except ValueError:
            pass
    raise BuildError(
        f"{source}: invalid date {value!r}. Use ISO format, e.g. 2026-08-10."
    )


def parse_post(path: Path) -> Post:
    meta, body = split_front_matter(path.read_text(encoding="utf-8"), path)

    title = meta.get("title")
    if not title or not str(title).strip():
        raise BuildError(f"{path}: missing required field 'title'.")
    title = str(title).strip()

    if "date" not in meta:
        raise BuildError(f"{path}: missing required field 'date'.")
    date = parse_date(meta["date"], path)

    description = str(meta.get("description") or "").strip()

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, list) or not all(isinstance(t, (str, int)) for t in tags):
        raise BuildError(f"{path}: 'tags' must be a list of strings.")
    tags = [str(t).strip() for t in tags if str(t).strip()]

    slug = str(meta.get("slug") or "").strip() or slugify(title)
    if not slug:
        raise BuildError(f"{path}: could not derive a slug; set 'slug' explicitly.")
    if slug != slugify(slug):
        raise BuildError(
            f"{path}: slug {slug!r} is not URL-safe. "
            f"Use lowercase letters, digits and hyphens, e.g. {slugify(slug)!r}."
        )

    draft = bool(meta.get("draft", False))

    image = str(meta.get("image") or "").strip()
    if image and not (image.startswith("/") or image.startswith("http")):
        raise BuildError(
            f"{path}: 'image' must be a site-absolute path (e.g. "
            f"/assets/images/{slug}/cover.jpg) or a full URL."
        )

    return Post(
        title=title,
        date=date,
        description=description,
        tags=tags,
        slug=slug,
        draft=draft,
        body_markdown=body,
        source=path,
        image=image,
    )


def load_posts(include_drafts: bool = False) -> list[Post]:
    """Read, validate, and sort all posts (newest first)."""
    posts = [parse_post(p) for p in sorted(POSTS_DIR.glob("*.md"))]

    published = [p for p in posts if include_drafts or not p.draft]

    seen: dict[str, Path] = {}
    for post in published:
        if post.slug in seen:
            raise BuildError(
                f"{post.source}: duplicate slug {post.slug!r} "
                f"(already used by {seen[post.slug]})."
            )
        seen[post.slug] = post.source

    published.sort(key=lambda p: (p.date, p.slug), reverse=True)
    return published


def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def site_url() -> str:
    return config.SITE_URL.rstrip("/")


def absolute_url(path: str) -> str:
    return site_url() + path


def tag_slug(tag: str) -> str:
    slug = slugify(tag)
    if not slug:
        raise BuildError(f"Tag {tag!r} cannot be turned into a URL slug.")
    return slug


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(
        site_name=config.SITE_NAME,
        site_url=site_url(),
        site_description=config.SITE_DESCRIPTION,
        author_name=config.AUTHOR_NAME,
        copyright_holder=getattr(config, "COPYRIGHT_HOLDER", config.AUTHOR_NAME),
        analytics_html=config.ANALYTICS_HTML,
        current_year=datetime.date.today().year,
        tag_slug=tag_slug,
    )
    return env


def write_page(rel_path: str, content: str) -> None:
    out = DIST_DIR / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def group_by_year(posts: list[Post]) -> list[tuple[int, list[Post]]]:
    years: dict[int, list[Post]] = {}
    for post in posts:
        years.setdefault(post.date.year, []).append(post)
    return sorted(years.items(), key=lambda item: item[0], reverse=True)


def pick_read_next(current: Post, posts: list[Post], limit: int = 3) -> list[Post]:
    """Pick up to `limit` other posts to suggest at the end of an article.

    Posts sharing a tag with the current one come first; the rest of the
    slots are filled with the most recent remaining posts. `posts` is
    assumed to be sorted newest-first, so both groups keep that order.
    """
    current_tags = {tag_slug(t) for t in current.tags}
    others = [p for p in posts if p.slug != current.slug]
    related = [p for p in others if current_tags & {tag_slug(t) for t in p.tags}]
    rest = [p for p in others if p not in related]
    return (related + rest)[:limit]


def collect_tags(posts: list[Post]) -> list[tuple[str, str, list[Post]]]:
    """Return (display_name, slug, posts) per tag, alphabetical.

    Tags are grouped case-insensitively by slug ("AI" and "ai" share a
    page); the first spelling encountered is used for display.
    """
    by_slug: dict[str, tuple[str, list[Post]]] = {}
    for post in posts:
        for tag in post.tags:
            slug = tag_slug(tag)
            name, tag_posts = by_slug.setdefault(slug, (tag, []))
            tag_posts.append(post)
    return sorted(
        [(name, slug, tag_posts) for slug, (name, tag_posts) in by_slug.items()],
        key=lambda item: item[1],
    )


# ---------------------------------------------------------------------------
# Feeds
# ---------------------------------------------------------------------------

def rfc822(date: datetime.date) -> str:
    dt = datetime.datetime(date.year, date.month, date.day, tzinfo=datetime.timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def generate_rss(posts: list[Post]) -> str:
    e = html.escape
    items = []
    for post in posts[: config.FEED_POST_COUNT]:
        link = absolute_url(post.url_path)
        items.append(
            "    <item>\n"
            f"      <title>{e(post.title)}</title>\n"
            f"      <link>{e(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{e(link)}</guid>\n"
            f"      <pubDate>{rfc822(post.date)}</pubDate>\n"
            f"      <description>{e(post.description)}</description>\n"
            "    </item>"
        )
    last_build = rfc822(posts[0].date) if posts else rfc822(datetime.date.today())
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{e(config.SITE_NAME)}</title>\n"
        f"    <link>{e(site_url() + '/')}</link>\n"
        f"    <description>{e(config.SITE_DESCRIPTION)}</description>\n"
        "    <language>en</language>\n"
        f"    <lastBuildDate>{last_build}</lastBuildDate>\n"
        f'    <atom:link href="{e(absolute_url("/feed.xml"))}" rel="self" '
        'type="application/rss+xml"/>\n'
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )


def generate_sitemap(posts: list[Post], extra_paths: list[str],
                     tags: list[tuple[str, str, list[Post]]]) -> str:
    e = html.escape
    latest = posts[0].date.isoformat() if posts else datetime.date.today().isoformat()

    entries: list[tuple[str, str]] = [(absolute_url(p), latest) for p in extra_paths]
    entries += [(absolute_url(p.url_path), p.date.isoformat()) for p in posts]
    entries += [
        (absolute_url(f"/tags/{slug}/"), max(tp.date for tp in tag_posts).isoformat())
        for _, slug, tag_posts in tags
    ]

    urls = "\n".join(
        "  <url>\n"
        f"    <loc>{e(loc)}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        "  </url>"
        for loc, lastmod in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n"
    )


# ---------------------------------------------------------------------------
# Build steps
# ---------------------------------------------------------------------------

def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)


def copy_static() -> None:
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, DIST_DIR, dirs_exist_ok=True)


def load_pages() -> list[Page]:
    """Standalone pages: every content/*.md (not in posts/) becomes /<slug>/.

    e.g. content/about.md -> /about/, content/projects.md -> /projects/.
    """
    pages = []
    for path in sorted(CONTENT_DIR.glob("*.md")):
        meta, body = split_front_matter(path.read_text(encoding="utf-8"), path)
        title = str(meta.get("title") or path.stem.replace("-", " ").title()).strip()
        slug = str(meta.get("slug") or "").strip() or slugify(path.stem)
        if slug != slugify(slug):
            raise BuildError(f"{path}: slug {slug!r} is not URL-safe.")
        pages.append(
            Page(
                title=title,
                slug=slug,
                description=str(meta.get("description") or "").strip(),
                body_html=render_markdown(body),
                source=path,
            )
        )
    return pages


def build() -> None:
    env = make_env()

    clean_dist()
    copy_static()

    posts = load_posts()
    for post in posts:
        post.body_html = render_markdown(post.body_markdown)
    # Every page's sidebar lists all published articles, newest first.
    env.globals["sidebar_posts"] = posts
    tags = collect_tags(posts)
    pages = load_pages()

    # Article pages: /articles/<slug>/
    article_tpl = env.get_template("article.html")
    for post in posts:
        write_page(
            f"articles/{post.slug}/index.html",
            article_tpl.render(
                post=post,
                canonical=absolute_url(post.url_path),
                read_next=pick_read_next(post, posts),
            ),
        )

    # Homepage: /
    write_page(
        "index.html",
        env.get_template("index.html").render(
            posts=posts[: config.HOMEPAGE_POST_COUNT],
            canonical=absolute_url("/"),
        ),
    )

    # Archive: /archive/
    write_page(
        "archive/index.html",
        env.get_template("archive.html").render(
            years=group_by_year(posts),
            canonical=absolute_url("/archive/"),
        ),
    )

    # Tag pages: /tags/<slug>/
    tag_tpl = env.get_template("tag.html")
    for name, slug, tag_posts in tags:
        write_page(
            f"tags/{slug}/index.html",
            tag_tpl.render(
                tag_name=name,
                posts=tag_posts,
                canonical=absolute_url(f"/tags/{slug}/"),
            ),
        )

    # Standalone pages: /about/, /projects/, ...
    page_tpl = env.get_template("page.html")
    extra_paths = ["/", "/archive/"]
    for page in pages:
        write_page(
            f"{page.slug}/index.html",
            page_tpl.render(page=page, canonical=absolute_url(page.url_path)),
        )
        extra_paths.append(page.url_path)

    # Feeds and machine-readable files
    write_page("feed.xml", generate_rss(posts))
    write_page("sitemap.xml", generate_sitemap(posts, extra_paths, tags))
    write_page("404.html", env.get_template("404.html").render(canonical=None))

    # GitHub Pages housekeeping
    write_page(".nojekyll", "")
    if config.CUSTOM_DOMAIN:
        write_page("CNAME", config.CUSTOM_DOMAIN.strip() + "\n")

    print(f"Built {len(posts)} article(s), {len(tags)} tag page(s) -> {DIST_DIR}")


def main() -> int:
    try:
        build()
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
