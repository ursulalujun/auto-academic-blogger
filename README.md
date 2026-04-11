# auto-academic-blogger

[中文](./README.zh-CN.md) | **English**

Reusable Codex skills for building an academic content agent: discover papers, screen them, draft social posts, prepare assets, and publish Xiaohongshu notes.

This repo is intentionally small and composable. Most detail lives in the dedicated docs below.

## What Is Included

- `arxiv-paper-screener`
  - search arXiv by field and time window
  - filter by institution rules
  - rank by GitHub stars or citation count
- `huggingface-weekly-paper-digest`
  - turn one Hugging Face weekly papers page into a themed digest
- `xiaohongshu-post-preparer`
  - draft overview posts and single-paper analysis posts
  - prepare covers, PDF first pages, and teaser/framework images
- `xiaohongshu-image-note-publisher`
  - publish prepared Xiaohongshu image notes from Safari
  - deduplicate single-paper posts and update the publish log

## Read This Next

- Setup and environment requirements: [SETUP.md](./SETUP.md)
- Prompt examples and end-to-end workflows: [TUTORIAL.md](./TUTORIAL.md)

Chinese versions:

- [README.zh-CN.md](./README.zh-CN.md)
- [SETUP.zh-CN.md](./SETUP.zh-CN.md)
- [TUTORIAL.zh-CN.md](./TUTORIAL.zh-CN.md)

## Quick Start

1. Clone the repo.
2. Install the Python dependencies from [SETUP.md](./SETUP.md).
3. Symlink the skills you want into `$CODEX_HOME/skills`.
4. If you plan to publish, log into Xiaohongshu creator center in Safari and enable the required Safari/macOS permissions.

Example:

```bash
git clone https://github.com/ursulalujun/auto-academic-blogger.git
cd auto-academic-blogger
python3 -m pip install --user PyMuPDF Pillow pypdf

ln -sfn /path/to/auto-academic-blogger/skills/arxiv-paper-screener ~/.codex/skills/arxiv-paper-screener
ln -sfn /path/to/auto-academic-blogger/skills/huggingface-weekly-paper-digest ~/.codex/skills/huggingface-weekly-paper-digest
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-post-preparer ~/.codex/skills/xiaohongshu-post-preparer
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-image-note-publisher ~/.codex/skills/xiaohongshu-image-note-publisher
```

## Typical Flow

1. Find papers with `arxiv-paper-screener` or `huggingface-weekly-paper-digest`
2. Draft post copy and assets with `xiaohongshu-post-preparer`
3. Preview or publish through `xiaohongshu-image-note-publisher`

Example prompts:

```text
Use $arxiv-paper-screener to search spatial intelligence papers from the last 30 days and save the results to ./daily_paper/arxiv_march
```

```text
Use $xiaohongshu-post-preparer to turn these papers into a Xiaohongshu overview post, write the body first, then finalize the title, and prepare PDF first-page screenshots
```

```text
Use $xiaohongshu-image-note-publisher to load the prepared post into Xiaohongshu creator center and stop before publishing so I can preview it
```

## Notes

- Single-paper posts use a dedup log under `daily_paper/` to avoid reposting the same paper.
- The publisher workflow is Safari-based and assumes a normal logged-in Safari window.
- The skills are meant to be edited for your own fields, institution lists, writing style, and output folders.
