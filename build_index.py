#!/usr/bin/env python3
"""Regenerate index.html by scanning this folder for topic pages.

Run this after adding/removing a .html file in this folder:
    python3 build_index.py

Categorization and ordering are keyword-driven (see CATEGORIES below) so new
files sort themselves in automatically. To manually pin a page's position
within its category, add an HTML comment anywhere in the file:
    <!-- rank: 3 -->
"""
import html
import re
from pathlib import Path

FOLDER = Path(__file__).parent
OUTPUT = FOLDER / "index.html"
SKIP = {"index.html"}

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
RANK_OVERRIDE_RE = re.compile(r"<!--\s*rank:\s*(-?\d+)\s*-->", re.IGNORECASE)

# Ordered categories (this list order = display order on the page, roughly
# foundational -> applied -> advanced). Each keyword maps to a
# complexity/synthesis rank used to sort pages *within* the category. Lower
# rank = earlier (more foundational). First matching category wins; a page
# falling in a category with no keyword match gets a default late rank (900)
# so it lands at the end, not an error.
CATEGORIES = [
    ("Statistics", "\U0001F4CA", "amber", "Hypothesis testing, distributions, inference", {
        "hypothesis": 1,
        "statistic": 2,
    }),
    ("Classic ML", "\U0001F4D0", "green", "Foundations, evaluation, and general ML", {
        "regulariz": 1,
        "evaluation": 2,
        "metric": 2,
        "breadth": 3,
    }),
    ("Trees & Ensembles", "\U0001F333", "teal", "Decision trees through boosted ensembles", {
        "decision_tree": 1,
        "bagging": 2,
        "random_forest": 3,
        "adaboost": 4,
        "gbm": 5,
        "gradient_boost": 5,
        "xgboost": 6,
        "xgb": 6,
        "gain": 7,
        "hyperparameter": 8,
        "advanced": 9,
        "lightgbm": 10,
        "comparison": 90,
    }),
    ("Time Series", "\U0001F4C8", "blue", "Forecasting and temporal models", {
        "arima": 1,
        "timeseries": 2,
        "time_series": 2,
    }),
    ("Neural Networks", "\U0001F9E0", "coral", "Deep learning architectures", {
        "neural": 1,
        "cnn": 2,
        "rnn": 2,
        "transformer": 3,
        "deep_learning": 1,
    }),
    ("GenAI & Agents", "\U0001F916", "purple", "LLMs, agents, and applied GenAI", {
        "agent": 1,
        "react": 2,
        "llm": 1,
        "genai": 1,
        "prompt": 3,
    }),
    ("Other", "\U0001F4C1", "grey", "Everything else", {}),
]

ACCENTS = {
    "teal": "#2dd4a0",
    "amber": "#f5a623",
    "blue": "#60a8e0",
    "coral": "#f07060",
    "purple": "#a594f9",
    "green": "#5cb85c",
    "grey": "#9898b0",
}


def prettify_filename(stem: str) -> str:
    words = re.split(r"[-_]+", stem)
    return " ".join(w.capitalize() for w in words if w)


def get_title(text: str, stem: str) -> str:
    match = TITLE_RE.search(text)
    if match:
        title = re.sub(r"\s+", " ", match.group(1)).strip()
        if title:
            return title
    return prettify_filename(stem)


def split_title(title: str):
    """Split "Topic Name — Subtitle" into (topic, subtitle | None).

    Titles in this folder consistently use an em dash to separate the plain
    topic name from a descriptive suffix ("Study Guide", "Complete Reference",
    etc). Falling back to the whole title with no subtitle keeps this safe
    for any future file that doesn't follow the convention.
    """
    if "—" in title:
        topic, _, subtitle = title.partition("—")
        return topic.strip(), subtitle.strip()
    return title.strip(), None


def classify(filename: str, title: str, text: str):
    haystack = f"{filename} {title}".lower()
    override = RANK_OVERRIDE_RE.search(text)

    for name, icon, color, desc, keywords in CATEGORIES:
        best_rank = None
        for kw, rank in keywords.items():
            if kw in haystack:
                # Prefer the most specific (highest-ranked) keyword match, since
                # specific sub-type keywords (e.g. "gain", "hyperparameter") are
                # assigned higher ranks than the generic parent keyword they
                # overlap with as a substring (e.g. "xgboost", "gbm").
                if best_rank is None or rank > best_rank:
                    best_rank = rank
        if best_rank is not None:
            rank = int(override.group(1)) if override else best_rank
            return name, icon, color, desc, rank

    # "Other" catch-all always matches (empty keyword dict) and is last in
    # CATEGORIES, so the loop above never actually falls through to here,
    # but keep as a safety net.
    name, icon, color, desc, _ = CATEGORIES[-1]
    rank = int(override.group(1)) if override else 900
    return name, icon, color, desc, rank


def collect_pages():
    by_category = {}
    for path in sorted(FOLDER.glob("*.html")):
        if path.name in SKIP:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        title = get_title(text, path.stem)
        topic, subtitle = split_title(title)
        name, icon, color, desc, rank = classify(path.name, title, text)
        by_category.setdefault(name, {"icon": icon, "color": color, "desc": desc, "pages": []})
        by_category[name]["pages"].append({
            "file": path.name, "title": title, "topic": topic, "subtitle": subtitle, "rank": rank,
        })

    ordered = []
    for name, icon, color, desc, _ in CATEGORIES:
        if name in by_category:
            pages = sorted(by_category[name]["pages"], key=lambda p: (p["rank"], p["title"].lower()))
            ordered.append({
                "name": name, "icon": icon, "color": color, "desc": desc, "pages": pages,
            })
    return ordered


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render(categories):
    nav_links = "\n".join(
        f'''      <a href="#{slugify(c['name'])}" class="nav-link" style="--accent:{ACCENTS[c['color']]}">{c['icon']} {html.escape(c['name'])}</a>'''
        for c in categories
    )

    sections = []
    for c in categories:
        accent = ACCENTS[c["color"]]
        cards = "\n".join(
            f'''        <a class="card" href="{html.escape(p['file'])}" style="--accent:{accent}">
          <span class="card-topic">{html.escape(p['topic'])}</span>
          {f'<span class="card-subtitle">{html.escape(p["subtitle"])}</span>' if p['subtitle'] else ''}
        </a>'''
            for p in c["pages"]
        )
        sections.append(f'''    <section class="category" id="{slugify(c['name'])}" style="--accent:{accent}">
      <div class="cat-header">
        <span class="cat-icon">{c['icon']}</span>
        <div>
          <h2 class="cat-title">{html.escape(c['name'])}</h2>
          <p class="cat-desc">{html.escape(c['desc'])} &middot; {len(c['pages'])} topic{'s' if len(c['pages']) != 1 else ''}</p>
        </div>
      </div>
      <div class="grid">
{cards}
      </div>
    </section>''')

    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ML Learning Notes</title>
<style>
  :root {{
    --bg: #0a0a0f; --bg2: #111118; --bg3: #18181f;
    --border: #2a2a38; --border2: #383848;
    --text: #e8e8f0; --text2: #9898b0; --text3: #5a5a70;
    --accent-default: #7c6af7;
    --mono: 'DM Mono', 'Courier New', monospace;
    --sans: 'DM Sans', -apple-system, sans-serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    background: var(--bg); color: var(--text); font-family: var(--sans);
    min-height: 100vh;
  }}
  .wrap {{ max-width: 900px; margin: 0 auto; padding: 0 1.5rem 4rem; }}

  header.hero {{
    padding: 4.5rem 1.5rem 3rem; max-width: 900px; margin: 0 auto;
    text-align: center;
  }}
  h1 {{
    font-size: clamp(2.4rem, 6vw, 3.6rem); font-weight: 300; letter-spacing: -0.03em;
    background: linear-gradient(120deg, #e8e8f0 30%, #a594f9 80%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }}
  .hero-rule {{
    width: 64px; height: 3px; margin: 1.5rem auto 0; border-radius: 3px;
    background: linear-gradient(90deg, #f5a623, #5cb85c, #2dd4a0, #60a8e0, #f07060, #a594f9);
  }}

  #search {{
    width: 100%; background: var(--bg2); border: 1px solid var(--border2);
    border-radius: 8px; padding: 12px 16px; font-family: var(--mono);
    font-size: 13px; color: var(--text); outline: none; margin: 1.5rem 0;
  }}
  #search:focus {{ border-color: var(--accent-default); }}

  nav.toc {{
    position: sticky; top: 0; z-index: 10; background: rgba(10,10,15,0.92);
    backdrop-filter: blur(8px); border-bottom: 1px solid var(--border);
    padding: 0.9rem 1.5rem; display: flex; gap: 6px; flex-wrap: wrap;
    max-width: 900px; margin: 0 auto;
  }}
  .nav-link {{
    font-family: var(--mono); font-size: 12px; padding: 5px 12px; border-radius: 20px;
    border: 1px solid var(--border2); color: var(--text2); text-decoration: none;
    transition: all 0.15s; white-space: nowrap;
  }}
  .nav-link:hover {{ border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }}

  section.category {{ margin-top: 3rem; scroll-margin-top: 5rem; }}
  .cat-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 1.25rem; padding-bottom: 0.9rem; border-bottom: 1px solid var(--border); }}
  .cat-icon {{
    font-size: 22px; width: 42px; height: 42px; border-radius: 10px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: color-mix(in srgb, var(--accent) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  }}
  .cat-title {{ font-size: 1.15rem; font-weight: 500; color: var(--accent); }}
  .cat-desc {{ font-size: 12px; color: var(--text3); font-family: var(--mono); margin-top: 2px; }}

  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }}
  .card {{
    display: flex; flex-direction: column; gap: 4px; justify-content: center;
    background: var(--bg2); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem 1.15rem; text-decoration: none; color: var(--text);
    transition: border-color 0.15s, background 0.15s, transform 0.15s;
  }}
  .card:hover {{
    border-color: var(--accent); background: var(--bg3); transform: translateY(-1px);
    box-shadow: 0 4px 20px -6px color-mix(in srgb, var(--accent) 40%, transparent);
  }}
  .card-topic {{ font-size: 16px; font-weight: 500; line-height: 1.35; }}
  .card-subtitle {{ font-size: 11.5px; color: var(--text3); font-family: var(--mono); }}
  .card:hover .card-topic {{ color: var(--accent); }}

  .empty {{ text-align: center; padding: 3rem; color: var(--text3); font-family: var(--mono); font-size: 13px; display: none; }}

  @media (max-width: 600px) {{
    .grid {{ grid-template-columns: 1fr; }}
    nav.toc {{ overflow-x: auto; flex-wrap: nowrap; }}
  }}
</style>
</head>
<body>
<nav class="toc">
{nav_links}
</nav>
<header class="hero">
  <h1>ML Learning Notes</h1>
  <div class="hero-rule"></div>
</header>
<div class="wrap">
  <input id="search" type="text" placeholder="Filter topics..." autocomplete="off">
{sections_html}
  <div class="empty" id="empty">No topics match your search.</div>
</div>
<script>
  const input = document.getElementById('search');
  const sections = Array.from(document.querySelectorAll('section.category'));
  const empty = document.getElementById('empty');
  input.addEventListener('input', () => {{
    const q = input.value.trim().toLowerCase();
    let totalVisible = 0;
    sections.forEach(section => {{
      let visibleInSection = 0;
      section.querySelectorAll('.card').forEach(card => {{
        const match = card.textContent.toLowerCase().includes(q);
        card.style.display = match ? '' : 'none';
        if (match) visibleInSection++;
      }});
      section.style.display = visibleInSection === 0 ? 'none' : '';
      totalVisible += visibleInSection;
    }});
    empty.style.display = totalVisible === 0 ? 'block' : 'none';
  }});
</script>
</body>
</html>
"""


def main():
    categories = collect_pages()
    OUTPUT.write_text(render(categories), encoding="utf-8")
    total = sum(len(c["pages"]) for c in categories)
    print(f"Wrote {OUTPUT} with {total} topics across {len(categories)} categories.")


if __name__ == "__main__":
    main()
