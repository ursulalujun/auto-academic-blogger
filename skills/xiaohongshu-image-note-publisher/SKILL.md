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
- For paper-analysis posts, use an objective explanatory voice. Do not use first-person phrasing such as `我认为`、`我觉得`、`提醒我`、`在我看来`; prefer `这篇工作表明`、`关键在于`、`启发是`、`目标是`.
- Add topic tags at the end of every Xiaohongshu note. Use `#topic` style tags, for example `#AI论文 #HuggingFace #WorldModel #Agent #多模态`.

### Single-Paper Analysis Template

For `单篇论文解析帖`, use this body structure by default:

```text
HF upvote：<count>
PDF：<pdf link>
代码：<code link or 未公开>

❓问题：...

📚 背景：...

🎯 动机：...

🧠 方法：...

💡 启发：...

#AI论文 #HuggingFace #...
```

Guidance for each section:

- `❓问题`: state the core bottleneck or research question in concrete terms.
- `📚 背景`: explain the field context and why the problem appears in realistic settings.
- `🎯 动机`: explain what the paper is trying to change or enable.
- `🧠 方法`: give the most detailed section, naming the method modules, data, training/evaluation design, framework, or pipeline.
- `💡 启发`: summarize the broader research implication without first-person language.

### Title Rules

- Split title writing into two cases:
  - `总览帖`:
    - Start from the week or topic, then directly summarize the trend of that field instead of using `XX领域看什么`.
    - Prefer titles such as `HF14：Agent走向安全与系统能力提升` rather than `HF14：Agent看什么`.
    - The reader should know the field immediately, for example `世界模型` / `多模态` / `Agent`.
  - `单篇论文解析帖`:
    - The title should make the field clear at a glance, not just mention the paper name.
    - Prefer `方法名：方法亮点概括（可选）+ 领域/核心贡献`, while keeping the title within 20 characters.
    - If space permits, include the method highlight before the field contribution, such as `MoT`、`流式提示`、`执行反馈`、`多Agent`.
    - If the paper proposes a new task, benchmark, or setting, the title can directly summarize that new task or setting.
    - If the paper improves an existing task, the title should state the motivation, method, or key capability, not only the task name.
    - Avoid unexplained jargon when a simpler phrase works. For example, prefer `利用游戏数据建模真实世界` over `G-buffer建模真实世界`.
    - Good examples:
      - `HY-Embodied：MoT具身模型`
      - `HyDRA：让世界模型记住离屏目标`
      - `世界渲染器：利用游戏数据建模真实世界`
      - `ShotStream：流式提示长视频生成`
      - `InCoder：执行反馈世界模型`

### Cover Rules

- `总览帖`:
  - Use `文字配图` generated inside Xiaohongshu.
  - Do not replace it with an external paper thumbnail by default.
  - The cover text should usually be a compact weekly-summary phrase such as `第14周huggingface daily paper小结`.
- `单篇论文解析帖`:
  - Use the cover image from the corresponding Hugging Face Daily Paper page.
  - Do not use a plain text cover for single-paper analysis when the HF paper cover is available.
  - Prefer downloading the cover with the helper script in `scripts/fetch_hf_paper_cover.py`.
  - Use two images for every single-paper analysis post:
    1. the Hugging Face Daily Paper cover;
    2. a teaser/framework image cropped from the paper PDF.
  - The teaser/framework crop must be manually inspected before publishing. Confirm that the figure is complete, readable enough, and not dominated by unintended body text, page margins, headers, footers, or clipped captions.
  - Prefer framework/pipeline/teaser figures over pure result tables when the paper has a suitable figure.

## Workflow

1. Prepare the content locally.
   - Determine whether the note is a `总览帖` or a `单篇论文解析帖`.
   - Finalize the title, body, and cover source according to the rules above.
   - For single-paper notes, fetch the Hugging Face Daily Paper cover before opening the publish flow.
   - For single-paper notes, download the arXiv PDF and crop one teaser/framework image. Use `scripts/extract_arxiv_pdf_teasers.py` as the reusable helper, then inspect the generated contact sheet or individual crops.
2. Open the publish page in Safari.
   - Open the Xiaohongshu publish page in the current normal Safari tab.
   - Switch from `上传视频` to `上传图文`.
3. Set up the cover.
   - For `总览帖`, use `文字配图`, enter the cover text, click `生成图片`, and wait until the page returns to `图片编辑`.
   - For `单篇论文解析帖`, inject the downloaded HF paper cover and the PDF teaser/framework image through the page's image file input with `File` + `DataTransfer`. The HF cover should be the first image.
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

python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/extract_arxiv_pdf_teasers.py \
  --paper hydra:2603.25716:HyDRA \
  --outdir /tmp/hydra_assets

python3 /Users/ursula/.codex/skills/xiaohongshu-image-note-publisher/scripts/publish_image_note.py \
  --title "HyDRA：让世界模型记住离屏目标" \
  --body-file /tmp/hydra_body.txt \
  --cover /tmp/2603.25716.png \
  --extra-image /tmp/hydra_assets/teasers/hydra_teaser.png \
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
- For `单篇论文解析帖`, confirm the second image is a complete teaser/framework crop from the paper PDF, not an accidental body-text crop or page-margin crop.
- Confirm the body editor contains the intended text.
- Confirm the title is present, within 20 characters, and actually summarizes the note.
- Confirm the title follows the relevant title rule for `总览帖` or `单篇论文解析帖`.
- Confirm paper-analysis body sections are present in order: `HF upvote / PDF / 代码 / ❓问题 / 📚 背景 / 🎯 动机 / 🧠 方法 / 💡 启发 / #topic tags`.
- Confirm the note does not use first-person explanatory language such as `我认为` or `我觉得`.
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

### scripts/extract_arxiv_pdf_teasers.py

Use this helper script to download arXiv PDFs, crop candidate teaser/framework images, and generate a contact sheet for manual inspection before publishing single-paper notes.
