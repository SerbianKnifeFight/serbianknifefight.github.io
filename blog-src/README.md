# blog framework

A dependency-free static blog generator, styled to match serbianknifefight.net.
Python 3 standard library only — no npm, no build service, nothing to keep
updated. You write posts as small HTML files, run one script, and get a
finished site: an index, one page per post, and a working `rss.xml`.

## What was actually broken in the old page

The uploaded `index.html` linked its stylesheet as `blog/intel.css`. If that
file lives in the *same* folder as `index.html` (which it did), that path is
wrong — it tells the browser to look for a `blog/` folder *inside* the blog
folder, gets a 404, and the page renders with zero styling: plain white
background, unstyled text. That's the "just WHITE" bug. This framework
generates correct relative paths automatically so it can't happen again.

## Folder layout

```
blog-framework/
├── build.py              the generator — run this
├── posts/                write your posts here, one file each
├── templates/            index.html + post.html, with {{placeholders}}
├── static/blog.css       the stylesheet (extends the main site's tokens)
└── output/                <- generated, this is what you deploy
    ├── index.html
    ├── rss.xml
    ├── blog.css
    └── posts/*.html
```

## Writing a post

Create a new file in `posts/`. The filename becomes the URL, so keep it
short and dash-separated, e.g. `posts/2026-02-14-on-rewriting-things.html`.
Top of the file is a frontmatter comment block, then the body as plain HTML:

```html
<!--
title: On rewriting things
date: 2026-02-14
type: essay
tags: writing, meta
excerpt: One or two sentences — shown in the index list and in RSS readers.
-->
<p>Your post, written directly in HTML. Use <h2>, <p>, <blockquote>,
<pre><code>, <ul>, <img>, whatever you need — it's all styled already.</p>
```

`type` is free text — `essay`, `project`, and `diary` are styled the same
way today (a small tag next to the date), but you can invent more. `tags`
is comma-separated and feeds the tag list in the sidebar and the `?tag=`
links (add a few lines of JS to `index.html`'s script block if you want
actual client-side filtering — right now the links are there but inert,
since the framework doesn't assume you want JS-driven filtering by default).

## Building

```bash
cd blog-framework
python3 build.py
```

This wipes and regenerates `output/` from scratch every time — never edit
files inside `output/` by hand, they'll be overwritten. Copy the contents
of `output/` into your site's `blog/` folder (or point your web server
straight at `output/`) and commit/push as usual.

## Deploying to your GitHub Pages repo, in a `blog/` folder

1. In your site's repo (the one GitHub Pages actually serves), add this
   whole `blog-framework` folder as **`blog-src/`** at the repo root —
   i.e. `blog-src/build.py`, `blog-src/posts/`, etc. Keep the source
   separate from the published output so you're never hand-editing
   generated files.
2. Run `python3 blog-src/build.py` once locally, then copy
   `blog-src/output/*` into a **`blog/`** folder at the repo root
   (`blog/index.html`, `blog/rss.xml`, `blog/posts/…`). That's the URL
   your site will actually serve: `yoursite.com/blog/`.
3. Update your main `index.html`'s topbar to point at it —
   `<a href="blog/index.html">blog</a>` instead of the old `Blog.html`.
4. Commit and push both `blog-src/` and `blog/`.

That's the manual version. This zip also includes
`.github/workflows/build-blog.yml`, which automates step 2: any push
that touches `blog-src/**` triggers a GitHub Actions run that builds
the site and commits the result straight into `blog/` for you. Drop the
whole `.github/` folder into your repo root alongside `blog-src/`, and
from then on you only ever touch files inside `blog-src/posts/` —
write a post, push, and the live `blog/` folder updates itself within
a minute or two. (It needs `contents: write` permission, which is on
by default for the built-in `GITHUB_TOKEN` on most repos — check
Settings → Actions → General → Workflow permissions if the commit step
fails.)

## Before you deploy

- `SITE["base_url"]` at the top of `build.py` is used to build the absolute
  URLs in `rss.xml`. Currently set to `https://serbianknifefight.net/blog/`
  — change it if the blog ends up somewhere else.
- Delete the three example posts in `posts/` once you've got real content
  (`2026-01-01-hello-world.html` is a real "welcome to the new format" post
  you can keep or rewrite; the other two are just placeholders showing what
  `project`- and `diary`-typed posts look like).
- The favicon path in the templates (`foldername/sitecon.ico`) matches
  what your main `index.html` already references — update both together
  if that ever moves.
- Link to the blog from your main site's topbar (`<a href="blog/index.html">blog</a>`
  instead of the old `Blog.html`), and add the RSS `<link rel="alternate">`
  tag to your main page's `<head>` too if you want feed readers to
  autodetect it from the homepage.

## Tag filtering

Clicking a tag (in the sidebar, or under a post) sends you to
`index.html?tag=name`. A small script in `templates/index.html` reads
that query param, hides every thread-table row whose `data-tags` doesn't
contain it, and shows a "showing N posts tagged X — clear filter" banner.
It's real filtering now, not just a link that goes nowhere — the example
posts each carry different tags specifically so you can click one and
see it work.

## Extending it

Everything's plain Python and string templates, so it's easy to bend:
- **Pagination** — once you have a lot of posts, slice `posts` in
  `main()` before building `index.html` and generate `page2.html`, etc.
- **Full-text tag filtering** — the tag links currently point at
  `index.html?tag=x`; add a small script to `templates/index.html` that
  reads `location.search` and hides non-matching `.post-row` elements.
- **Drafts** — give a post `draft: true` in its frontmatter and skip it
  in `parse_post`/`main` until you're ready to publish.
