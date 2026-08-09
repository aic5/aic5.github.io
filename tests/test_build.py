"""Tests for the core generator behavior in build.py.

Run with:  python -m unittest discover -s tests
"""

import datetime
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

import build  # noqa: E402
from build import BuildError, parse_post, slugify, split_front_matter  # noqa: E402


def write_post(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


VALID_POST = """---
title: "Why AI Changes Financial Analysis"
date: 2026-08-10
description: "A short description."
tags:
  - AI
  - Finance
draft: false
---

Article content begins here.
"""


class TestSlugify(unittest.TestCase):
    def test_basic_title(self):
        self.assertEqual(
            slugify("Why AI Changes Financial Analysis"),
            "why-ai-changes-financial-analysis",
        )

    def test_punctuation_and_spaces(self):
        self.assertEqual(slugify("  Hello, World!  It's Me. "), "hello-world-it-s-me")

    def test_unicode_is_transliterated(self):
        self.assertEqual(slugify("Café résumé"), "cafe-resume")


class TestFrontMatterParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_valid_post_parses(self):
        post = parse_post(write_post(self.dir, "a.md", VALID_POST))
        self.assertEqual(post.title, "Why AI Changes Financial Analysis")
        self.assertEqual(post.date, datetime.date(2026, 8, 10))
        self.assertEqual(post.description, "A short description.")
        self.assertEqual(post.tags, ["AI", "Finance"])
        self.assertFalse(post.draft)
        self.assertIn("Article content begins here.", post.body_markdown)

    def test_slug_generated_from_title_when_omitted(self):
        post = parse_post(write_post(self.dir, "a.md", VALID_POST))
        self.assertEqual(post.slug, "why-ai-changes-financial-analysis")
        self.assertEqual(post.url_path, "/articles/why-ai-changes-financial-analysis/")

    def test_explicit_slug_is_used(self):
        text = VALID_POST.replace("draft: false", "draft: false\nslug: custom-slug")
        post = parse_post(write_post(self.dir, "a.md", text))
        self.assertEqual(post.slug, "custom-slug")

    def test_missing_title_fails(self):
        path = write_post(self.dir, "bad.md", "---\ndate: 2026-01-01\n---\nBody.\n")
        with self.assertRaisesRegex(BuildError, "title"):
            parse_post(path)
        with self.assertRaisesRegex(BuildError, "bad.md"):
            parse_post(path)

    def test_missing_date_fails(self):
        path = write_post(self.dir, "bad.md", '---\ntitle: "T"\n---\nBody.\n')
        with self.assertRaisesRegex(BuildError, "date"):
            parse_post(path)

    def test_invalid_date_fails(self):
        path = write_post(
            self.dir, "bad.md", '---\ntitle: "T"\ndate: not-a-date\n---\nBody.\n'
        )
        with self.assertRaisesRegex(BuildError, "invalid date"):
            parse_post(path)

    def test_malformed_yaml_fails(self):
        path = write_post(
            self.dir, "bad.md", '---\ntitle: "T\ndate: 2026-01-01\n---\nBody.\n'
        )
        with self.assertRaisesRegex(BuildError, "malformed YAML"):
            parse_post(path)

    def test_missing_front_matter_fails(self):
        path = write_post(self.dir, "bad.md", "Just some text, no front matter.\n")
        with self.assertRaisesRegex(BuildError, "front matter"):
            parse_post(path)

    def test_unclosed_front_matter_fails(self):
        path = write_post(self.dir, "bad.md", '---\ntitle: "T"\nno closing fence\n')
        with self.assertRaisesRegex(BuildError, "not closed"):
            parse_post(path)

    def test_string_date_is_accepted(self):
        path = write_post(
            self.dir, "a.md", '---\ntitle: "T"\ndate: "2026-03-05"\n---\nBody.\n'
        )
        self.assertEqual(parse_post(path).date, datetime.date(2026, 3, 5))

    def test_image_field_parsed(self):
        text = VALID_POST.replace("draft: false", "draft: false\nimage: /assets/images/x/cover.jpg")
        post = parse_post(write_post(self.dir, "a.md", text))
        self.assertEqual(post.image, "/assets/images/x/cover.jpg")

    def test_relative_image_path_fails(self):
        text = VALID_POST.replace("draft: false", "draft: false\nimage: cover.jpg")
        with self.assertRaisesRegex(BuildError, "site-absolute"):
            parse_post(write_post(self.dir, "a.md", text))

    def test_non_urlsafe_explicit_slug_fails(self):
        path = write_post(
            self.dir,
            "bad.md",
            '---\ntitle: "T"\ndate: 2026-01-01\nslug: "Has Spaces"\n---\nBody.\n',
        )
        with self.assertRaisesRegex(BuildError, "not URL-safe"):
            parse_post(path)


def make_post(directory: Path, name: str, *, title: str, date: str,
              draft: bool = False, slug: str | None = None) -> Path:
    slug_line = f"slug: {slug}\n" if slug else ""
    return write_post(
        directory,
        name,
        f'---\ntitle: "{title}"\ndate: {date}\ndraft: {str(draft).lower()}\n'
        f"{slug_line}---\nBody.\n",
    )


class TestLoadPosts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(build, "POSTS_DIR", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_drafts_are_excluded(self):
        make_post(self.dir, "a.md", title="Published", date="2026-01-01")
        make_post(self.dir, "b.md", title="Draft", date="2026-01-02", draft=True)
        posts = build.load_posts()
        self.assertEqual([p.title for p in posts], ["Published"])

    def test_drafts_can_be_included_explicitly(self):
        make_post(self.dir, "a.md", title="Draft", date="2026-01-02", draft=True)
        self.assertEqual(len(build.load_posts(include_drafts=True)), 1)

    def test_sorted_newest_first(self):
        make_post(self.dir, "a.md", title="Oldest", date="2025-05-01")
        make_post(self.dir, "b.md", title="Newest", date="2026-08-01")
        make_post(self.dir, "c.md", title="Middle", date="2026-02-15")
        posts = build.load_posts()
        self.assertEqual([p.title for p in posts], ["Newest", "Middle", "Oldest"])

    def test_duplicate_slug_fails(self):
        make_post(self.dir, "a.md", title="Same Title", date="2026-01-01")
        make_post(self.dir, "b.md", title="Same Title", date="2026-01-02")
        with self.assertRaisesRegex(BuildError, "duplicate slug"):
            build.load_posts()

    def test_duplicate_slug_with_draft_is_allowed(self):
        # A draft may share a slug with a published post until it's published.
        make_post(self.dir, "a.md", title="Same Title", date="2026-01-01")
        make_post(self.dir, "b.md", title="Same Title", date="2026-01-02", draft=True)
        self.assertEqual(len(build.load_posts()), 1)


class TestSplitFrontMatter(unittest.TestCase):
    def test_body_preserved_exactly(self):
        meta, body = split_front_matter(
            "---\ntitle: T\n---\nLine one.\n\nLine two.\n", Path("x.md")
        )
        self.assertEqual(meta, {"title": "T"})
        self.assertEqual(body, "Line one.\n\nLine two.\n")


class TestReadNext(unittest.TestCase):
    @staticmethod
    def fake_post(slug, tags):
        p = mock.Mock()
        p.slug = slug
        p.tags = tags
        return p

    def test_related_by_tag_come_first_then_recent(self):
        current = self.fake_post("current", ["AI"])
        newest = self.fake_post("newest", ["Cooking"])
        related = self.fake_post("related", ["ai"])  # case-insensitive match
        older = self.fake_post("older", [])
        posts = [current, newest, related, older]  # newest-first order
        picks = build.pick_read_next(current, posts, limit=3)
        self.assertEqual([p.slug for p in picks], ["related", "newest", "older"])

    def test_current_post_excluded_and_limit_respected(self):
        current = self.fake_post("current", [])
        others = [self.fake_post(f"p{i}", []) for i in range(5)]
        picks = build.pick_read_next(current, [current] + others, limit=3)
        self.assertEqual(len(picks), 3)
        self.assertNotIn("current", [p.slug for p in picks])

    def test_no_other_posts_gives_empty_list(self):
        current = self.fake_post("current", ["AI"])
        self.assertEqual(build.pick_read_next(current, [current]), [])


class TestTagHelpers(unittest.TestCase):
    def test_tags_group_case_insensitively(self):
        p1 = mock.Mock(tags=["AI"])
        p2 = mock.Mock(tags=["ai", "Finance"])
        groups = build.collect_tags([p1, p2])
        slugs = [slug for _, slug, _ in groups]
        self.assertEqual(slugs, ["ai", "finance"])
        ai_group = next(g for g in groups if g[1] == "ai")
        self.assertEqual(len(ai_group[2]), 2)
        self.assertEqual(ai_group[0], "AI")  # first spelling wins


if __name__ == "__main__":
    unittest.main()
