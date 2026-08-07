import os
import re
import glob
import html
import shutil
import datetime
import email.utils

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "posts")
TEMPLATES_DIR = os.path.join(ROOT, "templates")
STATIC_DIR = os.path.join(ROOT, "static")
OUTPUT_DIR = os.path.join(ROOT, "output")

SITE = {
    "title": "serbianknifefight's blog",
    "description": "writing about whatever is on my mind at the moment, updated whenever",
    # Trailing slash matters — used to build absolute URLs for RSS.
    "base_url": "https://serbianknifefight.net/blog/",
}

FRONTMATTER_RE = re.compile(r"\s*<!--(.*?)-->\s*(.*)", re.S)
PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def parse_post(path):
    text = open(path, encoding="utf-8").read()
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path}: missing a <!-- ... --> frontmatter block at the top of the file")
    meta_block, body = m.group(1), m.group(2)

    meta = {}
    for line in meta_block.strip().splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip().lower()] = val.strip()

    for required in ("title", "date"):
        if required not in meta or not meta[required]:
            raise ValueError(f"{path}: missing required '{required}:' field")

    try:
        meta["date_obj"] = datetime.datetime.strptime(meta["date"], "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"{path}: date '{meta['date']}' must be YYYY-MM-DD") from e

    meta["type"] = meta.get("type", "post").strip().lower()
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["excerpt"] = meta.get("excerpt", "")
    meta["slug"] = os.path.splitext(os.path.basename(path))[0]
    meta["body"] = body.strip()

    word_count = len(re.sub(r"<[^>]+>", " ", body).split())
    meta["reading_time"] = max(1, round(word_count / 200))

    return meta


def render(template_text, ctx):
    def repl(m):
        key = m.group(1)
        return str(ctx.get(key, ""))
    return PLACEHOLDER_RE.sub(repl, template_text)


def build_archive_nav(posts, active_slug=None, prefix=""):
    """Sidebar tree: grouped by year, newest year first."""
    years = {}
    for p in posts:
        years.setdefault(p["date_obj"].year, []).append(p)

    lines = []
    lines.append(f'  <a href="{prefix}index.html" class="nav-top{" active" if active_slug is None else ""}">'
                  f'<span class="tc">├── </span>index</a>')
    sorted_years = sorted(years.keys(), reverse=True)
    for yi, year in enumerate(sorted_years):
        is_last_year = yi == len(sorted_years) - 1
        branch = "└── " if is_last_year else "├── "
        lines.append(f'  <a href="{prefix}index.html#{year}" class="nav-top">'
                      f'<span class="tc">{branch}</span>{year}/</a>')
        year_posts = sorted(years[year], key=lambda p: p["date_obj"], reverse=True)
        for pi, p in enumerate(year_posts):
            is_last = pi == len(year_posts) - 1
            sub_prefix = "    " if is_last_year else "│   "
            sub_branch = "└── " if is_last else "├── "
            active = " active" if p["slug"] == active_slug else ""
            href = f'{prefix}posts/{p["slug"]}.html'
            lines.append(f'  <a href="{href}" class="nav-sub{active}">'
                         f'<span class="tc">{sub_prefix}{sub_branch}</span>{html.escape(p["title"])}</a>')
    return "\n".join(lines)


def build_tag_nav(posts, prefix=""):
    tags = {}
    for p in posts:
        for t in p["tags"]:
            tags.setdefault(t, 0)
            tags[t] += 1
    if not tags:
        return ""
    parts = [f'<a href="{prefix}index.html?tag={t}">{html.escape(t)}</a> ({c})'
             for t, c in sorted(tags.items())]
    return "    " + "<br>\n    ".join(parts)


def build_post_row(p, now):
    date_str = p["date_obj"].strftime("%Y-%m-%d")
    tags_attr = html.escape(" ".join(p["tags"]))
    is_new = (now - p["date_obj"]).days <= 7
    new_badge = '<span class="new-badge">new</span>' if is_new else ""
    excerpt_html = (f'<span class="thread-excerpt">{html.escape(p["excerpt"])}</span>'
                     if p["excerpt"] else "")
    return (
        f'      <tr data-tags="{tags_attr}">'
        f'<td class="col-topic"><a class="post-title" href="posts/{p["slug"]}.html">'
        f'{html.escape(p["title"])}</a>{new_badge}{excerpt_html}</td>'
        f'<td class="col-type">{html.escape(p["type"])}</td>'
        f'<td class="col-date">{date_str}</td>'
        '</tr>'
    )


def build_tags_html(p, prefix="../"):
    if not p["tags"]:
        return ""
    return "".join(f'<a href="{prefix}index.html?tag={t}">{html.escape(t)}</a>' for t in p["tags"])


def rss_escape(text):
    return html.escape(text, quote=False)


def build_rss(posts):
    now = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))
    items = []
    for p in posts:
        link = SITE["base_url"] + f'posts/{p["slug"]}.html'
        pub_date = email.utils.format_datetime(p["date_obj"].replace(tzinfo=datetime.timezone.utc))
        items.append(f"""  <item>
    <title>{rss_escape(p['title'])}</title>
    <link>{link}</link>
    <guid isPermaLink="true">{link}</guid>
    <pubDate>{pub_date}</pubDate>
    <category>{rss_escape(p['type'])}</category>
    <description>{rss_escape(p['excerpt'])}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{rss_escape(SITE['title'])}</title>
  <link>{SITE['base_url']}</link>
  <description>{rss_escape(SITE['description'])}</description>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
"""


def main():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(os.path.join(OUTPUT_DIR, "posts"))

    post_paths = sorted(glob.glob(os.path.join(POSTS_DIR, "*.html")))
    if not post_paths:
        print("No posts found in posts/ — nothing to build.")
        return

    posts = [parse_post(p) for p in post_paths]
    posts.sort(key=lambda p: p["date_obj"], reverse=True)

    for p in posts:
        for css in glob.glob(os.path.join(STATIC_DIR, "*.css")):
            shutil.copy(css, OUTPUT_DIR)

    index_tpl = open(os.path.join(TEMPLATES_DIR, "index.html"), encoding="utf-8").read()
    index_ctx = {
        "SITE_TITLE": SITE["title"],
        "SITE_DESC": SITE["description"],
        "ARCHIVE_NAV": build_archive_nav(posts),
        "TAG_NAV": build_tag_nav(posts),
        "POST_COUNT": len(posts),
        "POST_ROWS": "\n".join(build_post_row(p, datetime.datetime.now()) for p in posts),
    }
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render(index_tpl, index_ctx))

    post_tpl = open(os.path.join(TEMPLATES_DIR, "post.html"), encoding="utf-8").read()
    for i, p in enumerate(posts):
        prev_p = posts[i + 1] if i + 1 < len(posts) else None  # older
        next_p = posts[i - 1] if i > 0 else None               # newer
        prev_link = (f'<a href="{prev_p["slug"]}.html">&larr; {html.escape(prev_p["title"])}</a>'
                     if prev_p else "")
        next_link = (f'<a href="{next_p["slug"]}.html">{html.escape(next_p["title"])} &rarr;</a>'
                     if next_p else "")
        ctx = {
            "TITLE": html.escape(p["title"]),
            "DATE_DISPLAY": p["date_obj"].strftime("%B %-d, %Y") if os.name != "nt"
                             else p["date_obj"].strftime("%B %d, %Y"),
            "TYPE": html.escape(p["type"]),
            "READING_TIME": p["reading_time"],
            "TAGS_HTML": build_tags_html(p),
            "EXCERPT": html.escape(p["excerpt"]),
            "BODY": p["body"],
            "ARCHIVE_NAV": build_archive_nav(posts, active_slug=p["slug"], prefix="../"),
            "PREV_LINK": prev_link,
            "NEXT_LINK": next_link,
        }
        out_path = os.path.join(OUTPUT_DIR, "posts", f'{p["slug"]}.html')
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render(post_tpl, ctx))

    with open(os.path.join(OUTPUT_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(build_rss(posts))

    print(f"Built {len(posts)} post(s) into {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
