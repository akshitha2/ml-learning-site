# ML Learning Notes — Site

Live site: https://akshitha2.github.io/ml-learning-site/

This folder is its own git repo, deployed to GitHub Pages via GitHub Actions
(`.github/workflows/deploy.yml`). It rebuilds and redeploys automatically on
every push to `main` — you never need to touch GitHub Pages settings again
under normal use.

## Adding a new topic

1. Drop your new `topic_name.html` file into this folder.
2. Make sure it's a full HTML document (`<!DOCTYPE html>`, `<head>`, `<title>Topic Name — Subtitle</title>`, `<body>...</body>`) — not a bare fragment. The title should use an em dash (`—`) to separate the plain topic name from a subtitle, e.g. `<title>Random Forest — Complete Study Guide</title>`. That's what makes the homepage show "Random Forest" big and "Complete Study Guide" small underneath it.
3. Push it:
   ```bash
   cd "/Users/apple/Downloads/Learning/ML Interview Prep/HTML Files"
   git add topic_name.html
   git commit -m "Add topic_name notes"
   git push
   ```
4. Check the **Actions** tab on GitHub — once the run turns green, your new topic is live on the homepage automatically. No manual index editing needed.

## Previewing locally before you push

```bash
cd "/Users/apple/Downloads/Learning/ML Interview Prep/HTML Files"
python3 build_index.py
open index.html
```

`build_index.py` regenerates `index.html` from whatever `.html` files currently exist in this folder. The GitHub Actions workflow runs this same script on every push, so running it locally is just for previewing — you don't have to commit the result yourself (though it's fine if you do; the workflow will just regenerate it again).

## How categorization works

Each file is auto-sorted into a category (Statistics, Classic ML, Trees &
Ensembles, Time Series, Neural Networks, GenAI & Agents, or "Other" as a
catch-all) based on keywords in the filename/title — see the `CATEGORIES`
list near the top of `build_index.py`. Within a category, pages are ordered
by a complexity rank (e.g. Decision Trees before Random Forest before
XGBoost) rather than alphabetically.

- **New topic lands in the wrong category or wrong position?** Add a keyword
  (and rank) for it to the relevant category in `CATEGORIES`, or use the
  manual override below.
- **Manual override for one file**: add this comment anywhere inside that
  HTML file, and it pins the page's sort position within its category:
  ```html
  <!-- rank: 3 -->
  ```
- **Brand new category needed** (e.g. "Neural Networks" has no files yet):
  just add matching files — the category appears on the homepage
  automatically once it has at least one page, and stays hidden while empty.

## Redeploying / troubleshooting

The workflow (`.github/workflows/deploy.yml`) triggers automatically on
every `git push` to `main`. You only need to do anything manually if a
deploy fails or Pages settings get reset:

1. Go to the repo on GitHub → **Settings → Pages**.
2. Under "Build and deployment" → **Source**, make sure it's set to
   **GitHub Actions** (not "Deploy from a branch").
3. Go to the **Actions** tab and confirm the latest "Deploy site to GitHub
   Pages" run is green. If it's red, click into it to see which step failed.
4. To manually re-trigger a deploy without changing any files:
   ```bash
   git commit --allow-empty -m "Trigger deploy"
   git push
   ```

**Common gotcha**: GitHub Pages via Actions requires the repo to be
**public** on the free plan (or GitHub Pro for private + Pages). If deploys
fail right after creating the repo, check it isn't private.
