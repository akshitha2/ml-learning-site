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
    ("Programming & Tools", "\U0001F4BB", "cyan", "Python, SQL, and data tooling for DS interviews", {
        "python": 1,
        "data_structure": 2,
        "oop_beginner": 3,
        "oop_interview": 4,
        "oop": 3,
        "eda": 5,
        "core_librar": 5,
        "sql": 6,
    }),
    ("Classic ML", "\U0001F4D0", "green", "Foundations, evaluation, and general ML", {
        "regulariz": 1,
        "evaluation": 2,
        "metric": 2,
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
    ("Interview Questions", "\U0001F3AF", "rose", "Case studies, system design, and general interview practice", {
        "breadth": 1,
        "case_stud": 2,
        "system_design": 3,
        "mock_interview": 4,
        "interview_question": 5,
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
    "rose": "#f472b6",
    "cyan": "#22d3ee",
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
        f'''      <a href="#{slugify(c['name'])}" class="nav-link badge badge-glass" style="--accent:{ACCENTS[c['color']]}">{c['icon']} {html.escape(c['name'])}</a>'''
        for c in categories
    )

    sections = []
    for c in categories:
        accent = ACCENTS[c["color"]]
        cards = "\n".join(
            f'''        <a class="card topic-card" href="{html.escape(p['file'])}" style="--accent:{accent}">
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
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
{cards}
      </div>
    </section>''')

    sections_html = "\n".join(sections)

    tailwind_accent_colors = ",\n".join(
        f"            {color_key}: '{hexval}'" for color_key, hexval in ACCENTS.items()
    )

    total_topics = sum(len(c["pages"]) for c in categories)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<!-- AUTO-GENERATED by build_index.py — do not edit directly, changes will be overwritten -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ML Learning Notes</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>%F0%9F%A7%A0</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {{
    theme: {{
      extend: {{
        colors: {{
            bg: '#030712',
            surface: '#0a0e1a',
            raised: '#0f1420',
{tailwind_accent_colors}
        }},
        fontFamily: {{
          heading: ['Playfair Display', 'Georgia', 'serif'],
          sans: ['Inter', 'sans-serif'],
          mono: ['JetBrains Mono', 'monospace'],
          display: ['Playfair Display', 'Georgia', 'serif'],
        }},
      }}
    }}
  }}
</script>
<link rel="stylesheet" href="assets/style.css">
<style>
  body {{ background: var(--bg); color: var(--text); font-family: var(--font-sans); min-height: 100vh; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 1.5rem 4rem; }}

  header.hero {{ padding: 5.5rem 1.5rem 3rem; text-align: center; position: relative; }}
  .hero-badge {{
    display: inline-flex; align-items: center; gap: 8px;
    font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.05em;
    padding: 7px 18px; border-radius: 999px; margin-bottom: 1.75rem;
    background: color-mix(in srgb, var(--accent-default) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent-default) 30%, transparent);
    color: var(--accent-default);
  }}
  header.hero h1 {{
    font-family: var(--font-display) !important; font-weight: 700;
    font-size: clamp(3.4rem, 9vw, 6.2rem) !important; letter-spacing: -0.03em; line-height: 1.05;
  }}
  .hero-sub {{ margin: 1.1rem auto 0; max-width: 46ch; color: var(--text-muted); font-family: var(--font-sans); font-size: 1.05rem; line-height: 1.6; }}
  .hero-rule {{
    width: 72px; height: 3px; margin: 2rem auto 0; border-radius: 3px;
    background: linear-gradient(90deg, #f5a623, #5cb85c, #2dd4a0, #60a8e0, #f07060, #a594f9);
  }}

  .hero-stat {{
    position: absolute; top: 50%; transform: translateY(-50%);
    background: color-mix(in srgb, var(--raised) 85%, transparent);
    backdrop-filter: blur(10px);
    border: 1px solid var(--hairline); border-radius: 14px;
    padding: 14px 20px; text-align: left; min-width: 130px;
  }}
  .hero-stat-label {{ font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 4px; }}
  .hero-stat-value {{ font-family: var(--font-heading); font-size: 26px; font-weight: 700; color: var(--text); }}
  .hero-stat.left {{ left: 3%; }}
  .hero-stat.right {{ right: 3%; }}
  @media (max-width: 1080px) {{ .hero-stat {{ display: none; }} }}

  nav.toc {{
    display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;
    max-width: 900px; margin: 2.25rem auto 0; padding: 0 1.5rem;
  }}
  .nav-link {{ text-decoration: none; transition: all 0.2s; }}
  .nav-link:hover {{ border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }}

  section.category {{ margin-top: 3.5rem; scroll-margin-top: 2rem; }}
  .cat-header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--hairline); }}
  .cat-icon {{
    font-size: 22px; width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: color-mix(in srgb, var(--accent) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  }}
  .cat-title {{ font-family: var(--font-heading); font-size: 1.4rem; font-weight: 700; color: var(--accent); }}
  .cat-desc {{ font-size: 12px; color: var(--text-dim); font-family: var(--font-mono); margin-top: 3px; }}

  .topic-card {{ display: flex; flex-direction: column; gap: 4px; justify-content: center; padding: 1.1rem 1.25rem; text-decoration: none; color: var(--text); }}
  .card-topic {{ font-family: var(--font-heading); font-size: 17px; font-weight: 600; line-height: 1.35; }}
  .card-subtitle {{ font-size: 11.5px; color: var(--text-dim); font-family: var(--font-mono); }}
  .topic-card:hover .card-topic {{ color: var(--accent); }}
</style>
</head>
<body>
<header class="hero glow-mesh" style="--glow:var(--accent-default)">
  <div class="hero-stat left">
    <div class="hero-stat-label">Topics</div>
    <div class="hero-stat-value">{total_topics}</div>
  </div>
  <div class="hero-stat right">
    <div class="hero-stat-label">Categories</div>
    <div class="hero-stat-value">{len(categories)}</div>
  </div>
  <div class="hero-badge">&#10022; Personal ML Interview Reference</div>
  <h1 class="gradient-text">ML Learning Notes</h1>
  <p class="hero-sub">Interview-ready deep dives across statistics, classic ML, ensembles, time series &amp; GenAI</p>
  <div class="hero-rule"></div>
  <nav class="toc">
{nav_links}
  </nav>
</header>
<div class="wrap">
{sections_html}
</div>
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
