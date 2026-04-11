# Tutorial

[中文](./TUTORIAL.zh-CN.md) | **English**

This tutorial shows how to go from installed skills to a finished academic-sharing post workflow in Codex.

The goal is practical:

1. trigger the right skill with the right prompt
2. control the workflow with a few clear parameters
3. review before publishing
4. publish without duplicating single-paper posts

## Before You Start

Make sure you have already:

- cloned this repo
- linked the skills into `$CODEX_HOME/skills`
- installed the Python dependencies in [SETUP.md](/Users/ursula/Documents/Playground/academic_blogger/SETUP.md)
- logged into Xiaohongshu creator center in Safari if you want to publish

## The Main Skills

For Xiaohongshu academic posting, the workflow is usually:

1. find papers
   - use `arxiv-paper-screener`
   - or `huggingface-weekly-paper-digest`
2. prepare the post
   - use `xiaohongshu-post-preparer`
3. publish the post
   - use `xiaohongshu-image-note-publisher`

## How To Trigger A Skill In Prompt

The simplest way is to name the skill in your prompt.

Examples:

- `用 $arxiv-paper-screener 检索最近一个月的 spatial intelligence 论文`
- `用 $huggingface-weekly-paper-digest 整理 2026-W15 的 HF daily papers`
- `用 $xiaohongshu-post-preparer 把这 6 篇论文整理成小红书单篇解析帖`
- `用 $xiaohongshu-image-note-publisher 发布刚才准备好的单篇论文帖`

You do not need to provide every detail every time. The skills work best when the prompt tells Codex:

- which skill to use
- what the input set is
- where to write outputs
- whether this is an overview post or a single-paper post
- whether to stop before publishing

## What You Can Control In Prompt

These are the most useful parameters to mention directly in natural language prompts.

### For `arxiv-paper-screener`

Useful parameters:

- `field`
- `time window`
- `max results`
- `output directory`

Prompt example:

```text
用 $arxiv-paper-screener 检索 spatial intelligence 方向 2026 年 3 月的 arXiv 论文，
最多保留 20 篇，输出到 /Users/ursula/Documents/Playground/daily_paper/arxiv_march
```

Another example:

```text
用 $arxiv-paper-screener 检索最近 30 天的 world model 论文，
按 skill 里的机构规则筛选，输出 markdown 和 json
```

### For `huggingface-weekly-paper-digest`

Useful parameters:

- `week id`
- `themes`
- `output directory`
- whether to create standalone notes for top papers

Prompt example:

```text
用 $huggingface-weekly-paper-digest 整理 2026-W15 的 Hugging Face daily papers，
主题分成 spatial intelligence、agent、world model，
输出到 /Users/ursula/Documents/Playground/daily_paper/2026-W15
```

### For `xiaohongshu-post-preparer`

Useful parameters:

- `post type`
  - `总览帖`
  - `单篇论文解析帖`
- source papers or source markdown
- output directory
- whether to prepare assets only or both markdown and assets
- title style constraints
- tag style

Prompt example for overview post:

```text
用 $xiaohongshu-post-preparer 把这周的 spatial intelligence 论文整理成小红书总览帖，
先写正文再定标题，标题控制在 20 字以内，
使用文字生成图片作为封面，
并给每篇论文准备 arXiv PDF 首页截图，
输出到 /Users/ursula/Documents/Playground/daily_paper/2026-W15
```

Prompt example for single-paper post:

```text
用 $xiaohongshu-post-preparer 为 OmniRoam 整理一篇小红书单篇论文解析帖，
按 HF upvote / PDF / 代码 / 问题 / 背景 / 动机 / 方法 / 启发 的结构写，
保留 emoji 小标题，保持客观口吻，不使用第一人称，
正文写完后再定标题，
标题要以方法名开头，并尽量概括整篇解析，
输出到 /Users/ursula/Documents/Playground/daily_paper/arxiv_march/spatial-intelligence
```

Useful things you can constrain in the prompt:

- body structure
- title style
- whether to include emoji section headers
- whether to include `#topic` tags
- whether to keep the tone objective
- where markdown should be saved
- where assets should be saved

### For `xiaohongshu-image-note-publisher`

Useful parameters:

- whether to publish now or stop before publish
- `post type`
- original paper title for dedup
- markdown path or direct title/body
- cover image path
- optional second image path
- Xiaohongshu cover text for overview posts

Prompt example for preview first:

```text
用 $xiaohongshu-image-note-publisher 打开小红书发布页面，
加载这篇单篇论文解析帖，
先不要发布，停在预览页等我确认。
论文原始标题是 OmniRoam: World Wandering via Long-Horizon Panoramic Video Generation，
markdown 在 /Users/ursula/Documents/Playground/daily_paper/arxiv_march/spatial-intelligence/xhs_single_01_omniroam.md
```

Prompt example for actual publish:

```text
用 $xiaohongshu-image-note-publisher 发布刚才确认过的 OmniRoam 单篇论文帖，
发布前先查重，
如果之前已经发过就不要重复发布，
发布成功后更新 single-paper log
```

## Full Workflow Examples

## Example A: Overview Post

Goal: turn a weekly paper set into one Xiaohongshu overview post.

### Step 1: build the weekly digest

```text
用 $huggingface-weekly-paper-digest 整理 2026-W15 的 HF daily papers，
聚焦 spatial intelligence、agent、world model，
输出到 /Users/ursula/Documents/Playground/daily_paper/2026-W15
```

### Step 2: turn one theme into a Xiaohongshu overview post

```text
用 $xiaohongshu-post-preparer 把 W15 的 spatial intelligence 论文整理成一篇小红书总览帖，
列出全部论文并按 upvote 排序，
最后再写总结，
标题 20 字以内，
使用文字生成图片作为封面，
并准备每篇论文的 arXiv PDF 首页截图
```

### Step 3: preview in Xiaohongshu

```text
用 $xiaohongshu-image-note-publisher 把刚才的总览帖填到小红书创作中心，
先不要发布，停在预览页让我看一下
```

### Step 4: publish

```text
用 $xiaohongshu-image-note-publisher 发布刚才确认过的总览帖
```

## Example B: Single-Paper Analysis Post

Goal: take one paper from search to a published single-paper note.

### Step 1: screen papers

```text
用 $arxiv-paper-screener 检索 2026 年 3 月的 spatial intelligence 论文，
最多保留 20 篇，输出到 /Users/ursula/Documents/Playground/daily_paper/arxiv_march
```

### Step 2: prepare one single-paper note

```text
用 $xiaohongshu-post-preparer 为 MV-RoMa 整理单篇论文解析帖，
按 skill 里的单篇模板写，
方法和动机尽量详细，
标题先不要抢写，等正文完成后再定，
封面优先用 HF paper 首页，
如果没有 HF 就用 arXiv PDF 首页，
再检查首页是否已经包含 teaser figure，
如果没有再补第二张 teaser 图
```

### Step 3: preview but do not publish yet

```text
用 $xiaohongshu-image-note-publisher 打开小红书发布页并填好 MV-RoMa 这篇帖子，
这是单篇论文解析帖，
原始论文标题是 MV-RoMA: Multi-View Reconstruction-Oriented Matching Anything，
发布前先查重，
停在预览页，不要发布
```

### Step 4: publish and register it

```text
用 $xiaohongshu-image-note-publisher 发布刚才预览过的 MV-RoMa 单篇帖子，
发布成功后把链接写回 single-paper log
```

## Prompt Templates You Can Reuse

## Template 1: Search Papers

```text
用 $arxiv-paper-screener 检索 <领域> 方向 <时间段> 的 arXiv 论文，
最多保留 <N> 篇，输出到 <输出目录>
```

Examples of `<时间段>`:

- `最近 7 天`
- `最近 30 天`
- `2026-03`

## Template 2: Build A Weekly Digest

```text
用 $huggingface-weekly-paper-digest 整理 <week id> 的 Hugging Face daily papers，
聚焦 <theme1>、<theme2>、<theme3>，
输出到 <输出目录>
```

## Template 3: Prepare An Overview Post

```text
用 $xiaohongshu-post-preparer 把 <论文集合> 整理成小红书总览帖，
正文先写完再定标题，
标题控制在 20 字以内，
使用文字生成图片作为封面，
并准备每篇论文的 arXiv PDF 首页截图，
输出到 <输出目录>
```

## Template 4: Prepare A Single-Paper Post

```text
用 $xiaohongshu-post-preparer 为 <论文名> 整理单篇论文解析帖，
按 HF upvote / PDF / 代码 / 问题 / 背景 / 动机 / 方法 / 启发 的结构写，
保留 emoji 小标题，
加 #topic 标签，
保持客观口吻，
正文写完后再定标题，
标题以方法名开头，并尽量概括整篇解析，
输出到 <输出目录>
```

## Template 5: Preview Before Publish

```text
用 $xiaohongshu-image-note-publisher 打开小红书发布页面并填入准备好的内容，
先不要发布，停在预览页让我确认
```

## Template 6: Publish A Single-Paper Note Safely

```text
用 $xiaohongshu-image-note-publisher 发布这篇单篇论文解析帖，
论文原始标题是 <paper title>，
发布前先查重，
如果已经发过就直接告诉我链接，
如果成功发布，就把结果登记到 single-paper log
```

## Notes On What The Prompt Should Include

When the task is ambiguous, these details help a lot:

- exact field name
- exact month or rolling time window
- output directory
- post type
- paper title in its original form
- whether this is preview-only or real publish
- whether the post is a single-paper note that requires dedup

If you omit them, Codex may infer them from your workspace, but explicit is better when you want reproducible behavior.

## Recommended First End-To-End Test

If you want to validate the setup safely, use this path:

1. run `arxiv-paper-screener`
2. prepare one single-paper note with `xiaohongshu-post-preparer`
3. run `xiaohongshu-image-note-publisher` in preview-only mode
4. check the Safari preview manually
5. publish only after confirmation

That gives you one clean loop covering:

- search
- writing
- assets
- preview
- dedup
- publish
- log update
