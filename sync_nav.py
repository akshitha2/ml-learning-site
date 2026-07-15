#!/usr/bin/env python3
"""Sync the shared site-header (breadcrumb + "Jump to" dropdown) into every
sub-page in this folder.

Reuses build_index.py's collect_pages()/ACCENTS as the single source of
truth for categories, icons, colors, and page titles, so the dropdown is
always in sync with index.html.

Run this after adding/removing/renaming a .html file (in addition to
build_index.py):
    python3 sync_nav.py

Safe to re-run: the header block is delimited by explicit HTML comment
markers (SITE-NAV:START / SITE-NAV:END) and fully replaced on each run —
nothing below the block is ever touched.
"""
import html
import re
from pathlib import Path

from build_index import ACCENTS, FOLDER, SKIP, collect_pages, slugify

START = "<!-- SITE-NAV:START -->"
END = "<!-- SITE-NAV:END -->"

# Matches the plain (pre-dropdown) site-header block from the earlier
# dark-theme pass, e.g. in hypothesis_testing.html / regularization_deep_dive.html,
# so re-running this script upgrades them instead of duplicating a second header.
LEGACY_HEADER_RE = re.compile(
    r'<header class="site-header">.*?</header>\s*', re.DOTALL
)


def build_panel(categories, current_file):
    groups = []
    for c in categories:
        accent = ACCENTS[c["color"]]
        links = []
        for p in c["pages"]:
            active = " active" if p["file"] == current_file else ""
            links.append(
                f'      <a class="nav-group-link{active}" href="{html.escape(p["file"])}">{html.escape(p["topic"])}</a>'
            )
        groups.append(
            f'''    <div class="nav-group">
      <div class="nav-group-label" style="--accent:{accent}">{c['icon']} {html.escape(c['name'])}</div>
{chr(10).join(links)}
    </div>'''
        )
    return "\n".join(groups)


def build_header(categories, current_file, current_category):
    name, icon, color = current_category
    accent = ACCENTS[color]
    panel = build_panel(categories, current_file)
    return f'''{START}
<header class="site-header">
  <div class="site-header-inner">
    <a class="site-breadcrumb" href="index.html">&larr; ML Learning Notes</a>
    <span class="site-header-sep">/</span>
    <div class="nav-dropdown" id="siteNav">
      <span class="badge nav-dropdown-trigger" style="--accent:{accent}" onclick="document.getElementById('siteNav').classList.toggle('open')">{icon} {html.escape(name)}</span>
      <div class="nav-dropdown-panel">
{panel}
      </div>
    </div>
  </div>
</header>
<script>
  document.addEventListener('click', function(e) {{
    var nav = document.getElementById('siteNav');
    if (nav && !nav.contains(e.target)) nav.classList.remove('open');
  }});
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
      var nav = document.getElementById('siteNav');
      if (nav) nav.classList.remove('open');
    }}
  }});
</script>
{END}'''


def main():
    categories = collect_pages()

    file_category = {}
    for c in categories:
        for p in c["pages"]:
            file_category[p["file"]] = (c["name"], c["icon"], c["color"])

    updated, skipped = [], []
    for path in sorted(FOLDER.glob("*.html")):
        if path.name in SKIP:
            continue
        if path.name not in file_category:
            skipped.append(path.name)
            continue

        text = path.read_text(encoding="utf-8", errors="surrogateescape")
        text = LEGACY_HEADER_RE.sub("", text, count=1)

        # The dropdown's CSS lives in assets/style.css — make sure every
        # page actually loads it (most of the 26 pages predate that file
        # and only have their own bespoke inline <style> block). Insert it
        # right after <title>, i.e. *before* the page's own <style> block,
        # so a handful of pages that happen to reuse generic class names
        # (.card, .badge) keep their own look — their own rules load later
        # and win the cascade. Our nav-specific classes are uniquely
        # prefixed (site-/nav-) so they never collide either way.
        title_match = re.search(r"</title>", text)
        if "assets/style.css" not in text and title_match:
            insert_at = title_match.end()
            text = (
                text[:insert_at]
                + '\n<link rel="stylesheet" href="assets/style.css">'
                + text[insert_at:]
            )

        header = build_header(categories, path.name, file_category[path.name])

        if START in text and END in text:
            pre, _, rest = text.partition(START)
            _, _, post = rest.partition(END)
            new_text = pre + header + post
        else:
            marker = "<body>"
            idx = text.find(marker)
            if idx == -1:
                skipped.append(path.name)
                continue
            insert_at = idx + len(marker)
            new_text = text[:insert_at] + "\n" + header + text[insert_at:]

        if new_text != text:
            path.write_text(new_text, encoding="utf-8", errors="surrogateescape")
            updated.append(path.name)

    print(f"Updated {len(updated)} files.")
    for n in updated:
        print(" -", n)
    if skipped:
        print("Skipped:", skipped)


if __name__ == "__main__":
    main()
