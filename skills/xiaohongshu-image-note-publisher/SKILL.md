---
name: xiaohongshu-image-note-publisher
description: Publish a Xiaohongshu image note from a normal Safari window that is already logged into the creator platform. Use when Codex needs to post one image-based note to https://creator.xiaohongshu.com/publish/publish by switching to 图文 mode, creating a weekly-summary cover through 文字配图 or uploading a normal cover image, filling a title and body, and clicking 发布 through Apple Events JavaScript plus DOM automation.
---

# Xiaohongshu Image Note Publisher

Use this skill only for the successful Safari path that has already been validated.

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

## Content Rules

### Post Type

Decide early whether the note is a `总览帖` or a `单篇论文解析帖`, because the title and cover rules differ.

### General Writing Rules

- The title is mandatory for every note.
- The title must be at most 20 characters.
- The body must be at most 1000 characters.
- The title should summarize the note faithfully and help a reader understand what they will get from the post.
- When possible, make the title slightly more vivid or curiosity-inducing without becoming clickbait.
- If the material is too long for one note, split it into multiple posts before opening Safari. For example, a weekly digest can be split by themes or sections such as `（一）` / `（二）`.
- When splitting, keep each post internally complete and readable on its own rather than cutting mid-topic.
- If small style edits are needed for Xiaohongshu readability, a few neutral emojis such as `📝`, `📍`, `📌`, `🔎`, `🧠`, `💡`, `🎯`, or `📚` may be added sparingly.
- Keep emoji usage restrained: typically 3-5 total, avoid stacking multiple emojis together, and do not let them weaken an academic or technical tone.

### Title Rules

- Split title writing into two cases:
  - `总览帖`:
    - Start from the week or topic, then directly summarize the trend of that field instead of using `XX领域看什么`.
    - Prefer titles such as `HF14：Agent走向安全与系统能力提升` rather than `HF14：Agent看什么`.
    - The reader should know the field immediately, for example `世界模型` / `多模态` / `Agent`.
  - `单篇论文解析帖`:
    - The title should make the field clear at a glance, not just mention the paper name.
    - Prefer `方法名：一句话讲清核心贡献` and explicitly say what task or field it belongs to when needed.
    - If the paper proposes a new task, benchmark, or setting, the title can directly summarize that new task or setting.
    - If the paper improves an existing task, the title should state the motivation, method, or key capability, not only the task name.
    - Avoid unexplained jargon when a simpler phrase works. For example, prefer `利用游戏数据建模真实世界` over `G-buffer建模真实世界`.
    - Good examples:
      - `HyDRA：让世界模型记住离屏目标`
      - `世界渲染器：利用游戏数据建模真实世界`
      - `ShotStream：流式提示长视频生成`

### Cover Rules

- `总览帖`:
  - Use `文字配图` generated inside Xiaohongshu.
  - Do not replace it with an external paper thumbnail by default.
  - The cover text should usually be a compact weekly-summary phrase such as `第14周huggingface daily paper小结`.
- `单篇论文解析帖`:
  - Use the cover image from the corresponding Hugging Face Daily Paper page.
  - Do not use a plain text cover for single-paper analysis when the HF paper cover is available.
  - Prefer downloading the cover with the helper script in `scripts/fetch_hf_paper_cover.py`.

## Workflow

1. Prepare the content locally.
   - Determine whether the note is a `总览帖` or a `单篇论文解析帖`.
   - Finalize the title, body, and cover source according to the rules above.
   - For single-paper notes, fetch the Hugging Face Daily Paper cover before opening the publish flow.
2. Open the publish page in Safari.
   - Open the Xiaohongshu publish page in the current normal Safari tab.
   - Switch from `上传视频` to `上传图文`.
3. Set up the cover.
   - For `总览帖`, use `文字配图`, enter the cover text, click `生成图片`, and wait until the page returns to `图片编辑`.
   - For `单篇论文解析帖`, inject the downloaded HF paper cover through the page's image file input with `File` + `DataTransfer`.
   - Wait until the image editor view appears.
4. Fill the content.
   - Fill the正文 through the Tiptap / ProseMirror editor instance with `editor.commands.setContent(...)`.
   - After filling the正文, do not publish immediately. Wait with a human-like delay before continuing.
   - Fill the标题 through the normal title `input` using the page-accepted text insertion path.
   - After filling the标题, pause again before the final preview check so the flow does not look machine-timed.
5. Review and publish.
   - Capture a real screenshot of the preview/editor window and inspect it.
   - Keep a final wait window between finishing content input and clicking `发布`. Prefer a randomized pause rather than a fixed delay.
   - Click `发布`.
   - Verify success by checking that the page URL contains `published=true`.
6. When publishing multiple notes in sequence:
   - Keep a cooldown gap between posts.
   - Do not send several notes back-to-back with identical timing.

## Operational Notes

- Do not use Safari WebDriver, GUI coordinate clicking, or accessibility-tree-only control for this skill. Those were exploratory paths and are not part of the final workflow.
- In multi-monitor setups, prefer locking to a specific Safari window id:
  - Get it with `python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py --print-window-id`
  - Reuse it with `--window-id <ID>` for all later publish actions
  - This avoids drifting back to a different Safari window or screen when multiple windows are open.

## Quick Start

Direct fields:

```bash
python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --title "HF W13论文周报：四方向速览" \
  --body-file /tmp/xhs_body.txt \
  --cover /Users/ursula/Documents/Playground/daily_paper/2026-W13/covers/weekly_cover.png
```

Markdown source:

```bash
python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --markdown /Users/ursula/Documents/Playground/daily_paper/2026-W13/2026-W13_小红书贴文草稿.md \
  --title "HF W13论文周报：四方向速览" \
  --window-id 17400
```

Weekly summary with text-generated cover:

```bash
python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --markdown /Users/ursula/Documents/Playground/daily_paper/2026-W13/2026-W13_小红书贴文草稿.md \
  --title "HF W13论文周报：四方向速览" \
  --cover-text "第13周huggingface daily paper小结" \
  --window-id 17400
```

Fetch a Hugging Face Daily Paper cover first, then publish a single-paper note:

```bash
python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/fetch_hf_paper_cover.py \
  --paper-url https://huggingface.co/papers/2603.25716 \
  --out /tmp/2603.25716.png

python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --title "HyDRA：让世界模型记住离屏目标" \
  --body-file /tmp/hydra_body.txt \
  --cover /tmp/2603.25716.png \
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
- For `单篇论文解析帖`, confirm the cover is the Hugging Face Daily Paper cover rather than a text-only placeholder.
- Confirm the body editor contains the intended text.
- Confirm the title is present, within 20 characters, and actually summarizes the note.
- Confirm the title follows the relevant title rule for `总览帖` or `单篇论文解析帖`.
- Confirm the `发布` button is enabled.
- Capture a real screenshot of the editor/preview window before publishing.
- Check the screenshot for乱码、异常字符、错误链接换行、段落过密、空行异常、以及手机预览里是否明显不美观.
- If the content still looks crowded, prefer splitting into multiple notes rather than aggressively deleting important information.

After clicking `发布`:

- Success condition: current page URL contains `published=true`
- If success is not observed, do not claim the note was posted

## Resources

### scripts/publish_image_note.py

Use this helper script for the end-to-end Safari publishing flow. It only implements the successful path above.

### scripts/fetch_hf_paper_cover.py

Use this helper script to download the paper cover image from a Hugging Face Daily Paper page before publishing a single-paper note.
