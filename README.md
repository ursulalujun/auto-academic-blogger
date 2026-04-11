# auto-academic-blogger

Reusable Codex skills for building an academic content agent: searching papers, curating weekly digests, drafting Xiaohongshu posts, preparing post assets, and publishing them.

This repo is designed for people who want to turn paper discovery into a repeatable workflow rather than a one-off manual process.

## What This Repo Is

This repository contains a small set of local Codex skills that can be combined into an academic content pipeline:

1. search papers from arXiv or Hugging Face
2. screen and rank papers
3. organize them into weekly digests
4. turn them into Xiaohongshu-ready posts
5. prepare cover and teaser images
6. publish posts from a logged-in browser
7. maintain a deduplicated log of already-published single-paper posts

The repo is intentionally skill-first. Each skill is self-contained and can be reused or adapted in your own setup.

## Skills

### `arxiv-paper-screener`

Path: [skills/arxiv-paper-screener](/Users/ursula/Documents/Playground/academic_blogger/skills/arxiv-paper-screener)

Use this skill to search and filter arXiv papers for a topic and time window.

What it does:

- searches arXiv by field keywords
- supports rolling windows like `7d`, `30d`, `90d`
- also supports month filters like `2026-03`
- enriches papers with institution and citation metadata from OpenAlex
- falls back to reading the arXiv PDF first page when institution metadata is missing
- filters papers by institution allowlists
- ranks open-source papers by GitHub stars
- ranks non-open-source papers by citation count
- writes machine-readable and markdown outputs

Good fit for:

- “Find spatial intelligence papers from the last month”
- “Keep only papers from strong universities / labs / companies”
- “Give me the most worth-reading subset first”

### `huggingface-weekly-paper-digest`

Path: [skills/huggingface-weekly-paper-digest](/Users/ursula/Documents/Playground/academic_blogger/skills/huggingface-weekly-paper-digest)

Use this skill to turn a Hugging Face weekly papers page into a structured weekly digest folder.

What it does:

- fetches one Hugging Face weekly papers page
- groups papers by theme such as `spatial intelligence`, `agent`, `world model`
- sorts by upvotes
- writes a main digest markdown
- writes normalized metadata files
- generates one standalone analysis for the top paper in each theme

Good fit for:

- weekly paper reading
- theme-based curation
- building a base document before social media writing

### `xiaohongshu-post-preparer`

Path: [skills/xiaohongshu-post-preparer](/Users/ursula/Documents/Playground/academic_blogger/skills/xiaohongshu-post-preparer)

Use this skill to prepare Xiaohongshu content before publishing.

This skill does not publish. It is the drafting and asset-preparation stage.

What it does:

- drafts post markdown
- enforces title/body limits
- supports two post types:
  - `总览帖`
  - `单篇论文解析帖`
- prepares image assets
- writes asset manifests that the publish step can consume directly

Image rules it supports:

- for `总览帖`:
  - use text-generated cover later in Xiaohongshu
  - attach one arXiv PDF first-page screenshot per mentioned paper
- for `单篇论文解析帖`:
  - first try Hugging Face paper cover
  - if no Hugging Face paper page exists, use arXiv PDF first page as cover
  - crop a teaser/framework figure from the PDF
  - if the first page already contains a clear teaser/framework figure, skip the second image

Bundled helpers:

- `prepare_xhs_post_assets.py`
- `fetch_hf_paper_cover.py`
- `extract_arxiv_pdf_teasers.py`

Good fit for:

- converting a paper note into Xiaohongshu-ready copy
- generating reusable assets for future publishing
- building a “review first, publish later” workflow

### `xiaohongshu-image-note-publisher`

Path: [skills/xiaohongshu-image-note-publisher](/Users/ursula/Documents/Playground/academic_blogger/skills/xiaohongshu-image-note-publisher)

Use this skill only for the final publish step.

What it does:

- opens Xiaohongshu creator publish page in Safari
- switches to 图文 mode
- supports both:
  - text-generated cover for overview posts
  - uploaded cover / optional teaser image for single-paper posts
- fills title and body
- captures preview screenshots
- clicks publish
- verifies publish success
- for single-paper analysis posts:
  - checks the dedup log before publishing
  - blocks duplicate posts
  - registers the new post into the log after publish

Good fit for:

- “Publish this prepared Xiaohongshu note”
- “Stop before publish so I can preview”
- “Avoid reposting a paper that was already published”

## Typical Workflows

### Workflow A: Weekly Digest

1. Use `huggingface-weekly-paper-digest`
2. Review and fix paper/theme assignments
3. Use `xiaohongshu-post-preparer` to create overview-post copy and PDF first-page images
4. Use `xiaohongshu-image-note-publisher` to publish the overview post

### Workflow B: Single-Paper Analysis

1. Use `arxiv-paper-screener` or `huggingface-weekly-paper-digest` to find the paper
2. Write or refine the single-paper analysis markdown
3. Use `xiaohongshu-post-preparer` to:
   - finalize the Xiaohongshu copy
   - fetch HF cover or render arXiv first page
   - crop teaser/framework image if needed
4. Use `xiaohongshu-image-note-publisher` to:
   - check the single-paper dedup log
   - publish the post
   - automatically register the result into the log

## Logs and Deduplication

Single-paper Xiaohongshu posts are tracked under [daily_paper](/Users/ursula/Documents/Playground/daily_paper):

- full registry:
  [xiaohongshu_single_paper_log_full.json](/Users/ursula/Documents/Playground/daily_paper/xiaohongshu_single_paper_log_full.json)
- lightweight dedup index:
  [xiaohongshu_single_paper_dedup_index.json](/Users/ursula/Documents/Playground/daily_paper/xiaohongshu_single_paper_dedup_index.json)

The full registry stores:

- original paper title
- Xiaohongshu title
- Xiaohongshu link
- note id
- markdown path
- cover image
- teaser image
- source group

The dedup index is optimized for quick duplicate checking before publishing.

## Repo Layout

```text
academic_blogger/
├── README.md
├── skills/
│   ├── arxiv-paper-screener/
│   ├── huggingface-weekly-paper-digest/
│   ├── xiaohongshu-post-preparer/
│   └── xiaohongshu-image-note-publisher/
```

Each skill usually contains:

- `SKILL.md`: human-readable instructions
- `agents/openai.yaml`: default agent prompt metadata
- `scripts/`: helper scripts used by the skill
- optional `references/`: keyword profiles, allowlists, or other curated data

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ursulalujun/auto-academic-blogger.git
cd auto-academic-blogger
```

### 2. Link the skills into Codex

If you use local Codex skills through `$CODEX_HOME/skills`, symlink the skill folders you want.

Example:

```bash
ln -sfn /path/to/auto-academic-blogger/skills/arxiv-paper-screener ~/.codex/skills/arxiv-paper-screener
ln -sfn /path/to/auto-academic-blogger/skills/huggingface-weekly-paper-digest ~/.codex/skills/huggingface-weekly-paper-digest
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-post-preparer ~/.codex/skills/xiaohongshu-post-preparer
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-image-note-publisher ~/.codex/skills/xiaohongshu-image-note-publisher
```

For a more step-by-step setup path, see [SETUP.md](/Users/ursula/Documents/Playground/academic_blogger/SETUP.md).

## Python Dependencies

The helper scripts rely on a small set of Python packages:

- `PyMuPDF` / `fitz`
- `Pillow`
- `pypdf`

Install them with:

```bash
python3 -m pip install --user PyMuPDF Pillow pypdf
```

An example local environment file is included as [.env.example](/Users/ursula/Documents/Playground/academic_blogger/.env.example).

Notes:

- most scripts are standard-library-heavy on purpose
- if your environment already has these packages, no extra setup is needed

## Browser / System Requirements

The Xiaohongshu publishing workflow depends on macOS + Safari.

### Required browser state

- use a normal Safari window, not a WebDriver-controlled Safari window
- log in to [小红书创作服务平台](https://creator.xiaohongshu.com)
- keep the creator page accessible in Safari during the publish step

### Required Safari setting

Enable:

- `Allow JavaScript from Apple Events`

This is required because the publish skill controls the page by running JavaScript inside Safari.

Depending on your Safari version, you may need to:

1. enable the Develop menu in Safari settings
2. then enable `Allow JavaScript from Apple Events`

### Useful macOS permissions

Depending on your setup, you may need to grant Terminal / Codex access to:

- Automation
  - so it can control Safari through Apple Events
- Screen Recording
  - if you want preview screenshots during publishing

### Optional screenshot helper

If you want robust real-window screenshots during review, a window-capture helper such as the `snipaste-window-screenshot` skill can be useful.

This repo does not bundle that system skill, but the publisher can work with it when available.

## Customization

Common extension points:

- expand arXiv field keywords in `arxiv-paper-screener/references/field_profiles.json`
- update institution allowlists in `arxiv-paper-screener/references/institution_allowlists.json`
- add your own post templates in `xiaohongshu-post-preparer`
- change dedup or logging behavior in `publish_image_note.py`
- adapt the pipeline to another social platform by replacing only the final publisher skill

## What To Expect

This repo is pragmatic, not “one-command magic”.

Some parts are intentionally semi-automatic:

- paper/theme classification still benefits from manual review
- teaser/framework image crops should still be checked by eye
- browser publishing depends on your current logged-in Safari session

That tradeoff is deliberate. The goal is to make academic content production reproducible and extensible without pretending that every step is perfectly generic.

## License / Reuse

If you open-source this repo, add the license that matches how you want others to reuse the skills and scripts.

Good default options:

- `MIT` for maximum reuse
- `Apache-2.0` if you want a more explicit patent license

## Related Notes

- The Xiaohongshu pipeline is optimized for Chinese academic-content posts.
- The repo assumes a local workspace where generated markdown, images, and logs are stored under `daily_paper/`.
- The skills are modular by design, so you can reuse only the arXiv and digest parts without using the Xiaohongshu publisher at all.
