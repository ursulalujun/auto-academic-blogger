---
name: xiaohongshu-image-note-publisher
description: Publish a Xiaohongshu image note from a normal Safari window that is already logged into the creator platform. Use when Codex already has the final title, body, and image assets, and needs to post one 图文 note through the validated Safari creator flow.
---

# Xiaohongshu Image Note Publisher

Use this skill only for the successful Safari path that has already been validated.

This skill is only for the final publish step.

- drafting the copy
- deciding post structure
- fetching HF covers
- rendering arXiv first pages
- cropping teaser/framework figures

should be done first with [$xiaohongshu-post-preparer](../xiaohongshu-post-preparer/SKILL.md).

## Preconditions

- Use a normal Safari window, not a Safari WebDriver automation window.
- The user must already be logged into `https://creator.xiaohongshu.com/publish/publish` in Safari.
- Safari must have `Allow JavaScript from Apple Events` enabled.
- The note must be an image note, not a video note.
- The title must be at most 20 characters.
- The body must be at most 1000 characters.

If any precondition is missing, stop and ask the user to fix that first.

## Inputs

Use one of these input styles:

- Direct fields: `title`, `body`, `cover_path`
- Markdown source: `markdown_path`, `cover_path`
- Weekly-summary override: `cover_text`

For markdown input, extract the first top-level article:

- Title: first `# ...`
- Body: lines until the next top-level `# ...`
- Remove the first image line like `![...] (...)`

Then rewrite or compress the content if needed so it satisfies Xiaohongshu limits.

## Input Expectations

This skill expects the content and image choices to already be finalized.

Typical prepared inputs:

- `title`
- `body`
- `cover_path`
- optional `extra_image`
- optional `cover_text` for overview posts that use Xiaohongshu `文字配图`
- for `单篇论文解析帖`, also provide the original `paper_title` used for duplicate checking and log registration

## Single-Paper Log Rules

For `单篇论文解析帖`, this skill must use the split log files under `./daily_paper/`:

- full registry: `xiaohongshu_single_paper_log_full.json`
- dedupe index: `xiaohongshu_single_paper_dedup_index.json`

Before publishing a single-paper post:

- look up the original paper title in the dedupe index
- if the paper has already been published, stop and report the existing Xiaohongshu link instead of publishing again

After publishing a single-paper post:

- open `笔记管理`
- locate the newly published note by its Xiaohongshu title
- record the public link, note id, markdown path, cover image, teaser image, and status in the full registry
- rebuild the dedupe index

## Workflow

1. Confirm the prepared assets and text are final.
2. If this is a `单篇论文解析帖`, check the split single-paper logs before publishing to avoid duplicates.
3. Open the publish page in Safari.
   - Open the Xiaohongshu publish page in the current normal Safari tab.
   - Switch from `上传视频` to `上传图文`.
4. Set up images.
   - For prepared `总览帖`, use `文字配图`, enter the provided cover text, click `生成图片`, then upload the prepared article images.
   - For prepared `单篇论文解析帖`, inject the prepared cover image and, if provided, the prepared teaser/framework image through the page's image file input with `File` + `DataTransfer`. The cover should be the first image.
   - Wait until the image editor view appears.
5. Fill the content.
   - Fill the正文 through the Tiptap / ProseMirror editor instance with `editor.commands.setContent(...)`.
   - After filling the正文, do not publish immediately. Wait with a human-like delay before continuing.
   - Fill the标题 through the normal title `input` using the page-accepted text insertion path.
   - After filling the标题, pause again before the final preview check so the flow does not look machine-timed.
6. Review and publish.
   - Capture a real screenshot of the preview/editor window and inspect it.
   - Keep a final wait window between finishing content input and clicking `发布`. Prefer a randomized pause rather than a fixed delay.
   - Click `发布`.
   - Verify success by checking that the page URL contains `published=true`.
   - If this is a `单篇论文解析帖`, register it into the split single-paper logs after success.
7. When publishing multiple notes in sequence:
   - Keep a cooldown gap between posts.
   - Do not send several notes back-to-back with identical timing.

## Operational Notes

- Do not use Safari WebDriver, GUI coordinate clicking, or accessibility-tree-only control for this skill. Those were exploratory paths and are not part of the final workflow.
- In multi-monitor setups, prefer locking to a specific Safari window id:
  - Get it with `python3 ./skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py --print-window-id`
  - Reuse it with `--window-id <ID>` for all later publish actions
  - This avoids drifting back to a different Safari window or screen when multiple windows are open.

## Quick Start

Direct fields:

```bash
python3 ./skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --title "HF W13论文周报：四方向速览" \
  --body-file /tmp/xhs_body.txt \
  --cover ./daily_paper/2026-W13/covers/weekly_cover.png
```

Markdown source:

```bash
python3 ./skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --markdown ./daily_paper/2026-W13/2026-W13_小红书贴文草稿.md \
  --title "HF W13论文周报：四方向速览" \
  --window-id 17400
```

Weekly summary with text-generated cover:

```bash
python3 ./skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --markdown ./daily_paper/2026-W13/2026-W13_小红书贴文草稿.md \
  --title "HF W13论文周报：四方向速览" \
  --cover-text "第13周huggingface daily paper小结" \
  --window-id 17400
```

Publish a prepared single-paper note:

```bash
python3 ./skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --title "HyDRA：让世界模型记住离屏目标" \
  --post-type single_paper_analysis \
  --paper-title "Out of Sight but Not Out of Mind" \
  --body-file /tmp/hydra_body.txt \
  --cover /tmp/hydra_cover.png \
  --extra-image /tmp/hydra_teaser.png \
  --window-id 17400
```

Human-like pacing:

- The helper script now waits with jitter by default:
  - after body fill: about `3.5-7.5` seconds
  - after title fill: about `2-5` seconds
  - before publish: about `12-28` seconds
  - after successful publish, before the script returns: about `45-90` seconds
- Override these windows only when necessary with:
  - `--body-settle-min/--body-settle-max`
  - `--title-settle-min/--title-settle-max`
  - `--pre-publish-min/--pre-publish-max`
  - `--post-publish-min/--post-publish-max`
- Prefer leaving the jitter enabled for normal posting workflows so the interaction rhythm is less uniform.

## Validation

Before clicking `发布`:

- Confirm the page is in `图片编辑` mode.
- Confirm the cover image is present in the preview area.
- For `总览帖`, confirm the generated cover contains the intended week text.
- For posts with uploaded images, confirm the prepared images appear in the intended order.
- For `单篇论文解析帖`, if a second image is provided, confirm it is the intended teaser/framework crop rather than an accidental body-text crop or page-margin crop.
- For `单篇论文解析帖`, confirm duplicate-checking ran against the split log files before publishing.
- Confirm the body editor contains the intended text.
- Confirm the title is present, within 20 characters, and actually summarizes the note.
- Confirm the `发布` button is enabled.
- Capture a real screenshot of the editor/preview window before publishing.
- Check the screenshot for乱码、异常字符、错误链接换行、段落过密、空行异常、以及手机预览里是否明显不美观.
- If the content still looks crowded, prefer splitting into multiple notes rather than aggressively deleting important information.

After clicking `发布`:

- Success condition: current page URL contains `published=true`
- For `单篇论文解析帖`, confirm the full log and dedupe index were updated after success.
- If success is not observed, do not claim the note was posted

## Resources

### scripts/publish_image_note.py

Use this helper script for the end-to-end Safari publishing flow, single-paper duplicate checking, and post-publish log registration.

All drafting and asset-preparation helpers now belong to [$xiaohongshu-post-preparer](../xiaohongshu-post-preparer/SKILL.md).
