# Capital Workbench article callout

Use this callout in an article when Capital Workbench is directly relevant to
the subject being discussed. The article should remain complete and useful
without requiring the reader to follow the link.

## Copy-and-edit snippet

Paste the following HTML into the article's Markdown file, ideally after the
paragraph that creates the natural connection to Capital Workbench:

```html
<aside class="project-callout" aria-label="Capital Workbench">
  <div class="project-callout-brand">
    <span class="project-callout-mark">CW</span>
    <span class="project-callout-name">Capital<br>Workbench</span>
  </div>
  <p class="project-callout-tagline">Reasoning and Analytics</p>
  <p class="project-callout-copy">I’m building Capital Workbench to help teams move beyond financial metrics toward better questions and clearer actions.</p>
  <a class="project-callout-link" href="https://capital-workbench.com/performance-overview">Explore a public company <span aria-hidden="true">→</span></a>
</aside>
```

For each article, normally change only:

- `project-callout-copy` — connect Capital Workbench to the article's specific
  subject using concise, natural language.
- The link text — describe the most relevant next step for that article.
- The link destination — use a more specific Capital Workbench page when one
  provides a better continuation than the general public-company explorer.

Keep the brand markup and CSS class names unchanged so every callout has the
same appearance. The shared styling lives in `static/css/style.css` under
`.project-callout`.

## Editorial guidelines

- Use no more than one callout in an article.
- Place it after the reader has received useful context, close to the passage
  that makes Capital Workbench relevant.
- Prefer first-person language such as “I’m building…” so the connection is
  transparent and feels like an author's note.
- Tailor the benefit statement to the article; do not repeat the same generic
  message everywhere.
- Avoid placing the callout above the opening paragraphs or interrupting an
  unrelated article with it.

The current reference implementation is in
`content/posts/2026-08-22-ai-can-read-the-map.md`.
