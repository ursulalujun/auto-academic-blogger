---
name: xiaohongshu-post-preparer
description: Prepare Xiaohongshu post copy and image assets for either overview posts or single-paper analysis posts. Use when Codex needs to draft the post, choose titles, prepare markdown, and collect the right cover/figure images before any Safari publishing step.
---

# Xiaohongshu Post Preparer

Use this skill when the task is to organize a Xiaohongshu post before publishing.

This skill does not click `发布`. It prepares:

- post title and body
- markdown drafts
- image assets
- per-post asset manifests

Use [$xiaohongshu-image-note-publisher](../xiaohongshu-image-note-publisher/SKILL.md) only after the content and assets are ready.

## Post Types

Split work into two post types early:

1. `总览帖`
2. `单篇论文解析帖`

The copy rules and image rules are different.

## General Writing Rules

- The title must be at most `20` characters.
- The body must be at most `1000` characters.
- Keep an objective explanatory voice.
- Do not use first-person phrasing such as `我认为`、`我觉得`、`提醒我`、`在我看来`.
- Add topic tags at the end of every post using `#topic` style, for example `#AI论文 #arXiv #SpatialIntelligence`.
- If needed, add a few neutral emojis to section headers, but keep the tone academic and restrained.

## Overview Posts

For `总览帖`:

- Use `文字配图` as the cover when publishing in Xiaohongshu.
- Prepare a compact `cover_text`, usually a week/topic summary phrase.
- Attach the `arXiv PDF` first-page screenshot for every paper mentioned in the post.
- The first page screenshot should be rendered locally before the publish flow so it can be uploaded as normal images.

Recommended workflow:

1. Write the overview title and body.
2. Render the first page of each paper PDF as an image.
3. Save a markdown draft plus an asset manifest.
4. Later, publish with a text-generated cover and the rendered PDF first-page images.

## Single-Paper Analysis Posts

For `单篇论文解析帖`, use this body structure by default:

```text
HF upvote：<count or 未收录>
PDF：<pdf link>
代码：<code link or 未公开>

❓问题：...

📚 背景：...

🎯 动机：...

🧠 方法：...

💡 启发：...

#AI论文 #arXiv #...
```

Guidance:

- `❓问题`: the concrete bottleneck or research question.
- `📚 背景`: field context and why the problem matters in realistic settings.
- `🎯 动机`: what the paper is trying to unlock or fix.
- `🧠 方法`: the most detailed section; explain the pipeline, modules, data, training design, or benchmark setup.
- `💡 启发`: broader implication stated objectively.

### Single-Paper Image Rules

Prepare images in this priority order:

1. Cover:
   - First, fetch the Hugging Face paper page cover if the paper exists on Hugging Face.
   - If no Hugging Face paper page is available, use the `arXiv PDF` first-page screenshot as the cover.
2. Second image:
   - Try to use a teaser/framework figure cropped from the paper PDF.
   - If the first page already clearly contains the teaser/framework figure, do not upload a second image.

The teaser/framework crop must be checked before publishing:

- confirm the figure is complete
- avoid large body-text regions
- avoid page margins, headers, footers
- avoid clipped captions

## Title Rules

- The title should be the last core writing step, because it needs to summarize the completed post rather than constrain it too early.
- `总览帖`: 
  - start from the week/topic and directly summarize the trend of that field.
  - Good examples:
    - For week 14: `HF14：Agent走向安全与系统能力`
    - For week 15: `HF15：世界模型开始追求连续和一致性`
- Keep the title within `20` characters.
- `单篇论文解析帖`: 
  - prefer `方法名：方法亮点概括（可选）+ 领域/核心贡献`.
  - The title should clearly represent the field the article focuses on
  - The title should summarize the whole analysis post, not only the paper name or one local method trick.
  - Good examples:
    - `HY-Embodied：MoT具身基础大模型`
    - `ShotStream：流式提示长视频生成`

## Workflow

1. Decide whether the note is `总览帖` or `单篇论文解析帖`.
2. Draft the body first and finish the main structure before naming the post.
3. Finalize the title only after the body is stable.
4. Write or update the markdown with the finished title.
5. Prepare images:
   - `总览帖`: text cover plan + arXiv first-page screenshots for all mentioned papers.
   - `单篇论文解析帖`: HF cover if available, otherwise arXiv first page; then teaser/framework only when needed.
6. Write an asset manifest so the publish step can consume the prepared files directly.

## Scripts

### `scripts/prepare_xhs_post_assets.py`

Use this helper to prepare image assets for either overview posts or single-paper posts.

Capabilities:

- download arXiv PDFs
- render PDF first pages
- fetch Hugging Face paper covers when available
- crop teaser/framework figures from PDFs
- decide whether a single-paper post needs one image or two
- write a JSON manifest for the publish step

Example: overview assets

```bash
python3 ./skills/xiaohongshu-post-preparer/scripts/prepare_xhs_post_assets.py \
  --mode overview \
  --paper omniroam:2603.30045:OmniRoam \
  --paper mv_roma:2603.27542:MV-RoMa \
  --outdir ./daily_paper/arxiv_march/spatial-intelligence/xhs_assets
```

Example: single-paper assets

```bash
python3 ./skills/xiaohongshu-post-preparer/scripts/prepare_xhs_post_assets.py \
  --mode single \
  --paper hydra:2603.25716:HyDRA \
  --hf-paper-url hydra:https://huggingface.co/papers/2603.25716 \
  --outdir /tmp/hydra_assets
```

## Validation

Before finishing:

- Confirm titles are within `20` characters.
- Confirm bodies are within `1000` characters.
- Confirm tags are present.
- For overview posts, confirm every mentioned paper has a rendered arXiv first-page image.
- For single-paper posts, confirm the cover choice follows:
  - HF paper cover first
  - otherwise arXiv first page
- For single-paper posts, confirm the second image is omitted when the first page already contains a clear teaser/framework figure.
- Confirm the asset manifest points to real files.
