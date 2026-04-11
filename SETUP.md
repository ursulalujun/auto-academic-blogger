# Setup Guide

This document gives a practical setup path for using the skills in this repository.

## 1. Clone The Repo

```bash
git clone https://github.com/ursulalujun/auto-academic-blogger.git
cd auto-academic-blogger
```

## 2. Install Python Dependencies

The helper scripts rely on a few Python packages:

```bash
python3 -m pip install --user PyMuPDF Pillow pypdf
```

These cover:

- PDF rendering
- PDF text extraction
- image contact sheets and asset generation

## 3. Link Skills Into Codex

If you use local Codex skills via `$CODEX_HOME/skills`, create symlinks for the skills you want.

Example:

```bash
ln -sfn /path/to/auto-academic-blogger/skills/arxiv-paper-screener ~/.codex/skills/arxiv-paper-screener
ln -sfn /path/to/auto-academic-blogger/skills/huggingface-weekly-paper-digest ~/.codex/skills/huggingface-weekly-paper-digest
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-post-preparer ~/.codex/skills/xiaohongshu-post-preparer
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-image-note-publisher ~/.codex/skills/xiaohongshu-image-note-publisher
```

## 4. Prepare Local Output Folders

By default, the workflows in this repo expect generated files under a local workspace such as:

```text
/Users/<you>/Documents/Playground/daily_paper
```

If you use a different workspace root, adjust the output paths in your prompts or scripts.

## 5. Browser Setup For Xiaohongshu Publishing

The Xiaohongshu publisher depends on macOS + Safari.

Required:

- use a normal Safari window
- log in to [小红书创作服务平台](https://creator.xiaohongshu.com)
- keep the creator page accessible during publishing

Enable in Safari:

- `Allow JavaScript from Apple Events`

You may need to:

1. enable the Safari Develop menu
2. then enable `Allow JavaScript from Apple Events`

## 6. macOS Permissions

Depending on your environment, grant permissions to Terminal / Codex for:

- Automation
  - so Apple Events can control Safari
- Screen Recording
  - so preview screenshots can be captured

## 7. Logs For Single-Paper Deduplication

Single-paper Xiaohongshu posts use two log files:

- `daily_paper/xiaohongshu_single_paper_log_full.json`
- `daily_paper/xiaohongshu_single_paper_dedup_index.json`

The publish skill checks the dedup index before posting a single-paper analysis note and updates both files after a successful publish.

## 8. Recommended First Test

Try a dry run before real publishing:

1. prepare one single-paper markdown
2. prepare its assets with `xiaohongshu-post-preparer`
3. run the publisher with `--stop-before-publish`

That verifies:

- title/body constraints
- image upload order
- preview rendering
- browser permissions

without sending a real post.

## 9. Optional Customization

You will probably want to adapt:

- arXiv field keywords
- institution allowlists
- output directory roots
- post writing style
- title conventions

Those live mostly inside the skill folders and are meant to be edited.
