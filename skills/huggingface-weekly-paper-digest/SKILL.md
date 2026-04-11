---
name: huggingface-weekly-paper-digest
description: Build a weekly Hugging Face papers digest for a specified week id (`wid`) and a set of themes. Use when Codex needs to collect papers from a weekly Hugging Face papers page, filter them into primary themes, sort by upvotes, generate a themed summary table with key images when available, summarize cross-paper common ideas for each theme, and write one standalone markdown analysis for the highest-upvoted paper in each theme.
---

# Huggingface Weekly Paper Digest

## Overview

Use this skill to turn one Hugging Face weekly papers page into a structured research digest folder.
The skill accepts two parameters:

- `wid`: week id such as `W12`, `12`, or `2026-W12`
- `themes`: one or more theme names, usually `spatial intelligence`, `world model`, `video understanding`, `tool-use agent`

## Workflow

1. Run the helper script to fetch the week's papers, enrich them with arXiv abstracts, assign each paper to one primary theme, sort each theme by upvotes, add the first arXiv figure when available, and create an output folder named after `wid`.
2. Review the generated themed table markdown and fix any misclassified papers or weak matches. The helper script is a first-pass classifier and must be manually checked before final delivery.
3. Ensure every theme section includes a non-empty `Summary` block that synthesizes recurring motivation, method patterns, and shared novelty across the papers in that theme. Do not leave placeholder text.
4. Ensure the highest-upvoted paper in every theme has a standalone markdown file with non-empty `Motivation`, `Method`, and `Insights` sections. Do not leave placeholder text.
5. Keep one paper in one primary theme only. If a paper spans multiple themes, place it in the theme that best matches its main contribution.
6. Unless the user explicitly says not to write files, always deliver the result under `./daily_paper/2026-W{wid}`. Do not invent alternative output locations unless the user explicitly overrides the path.

## Quick Start

Run the helper script and write to the normalized weekly folder path:

```bash
python3 ./skills/huggingface-weekly-paper-digest/scripts/build_weekly_digest.py \
  --wid W12 \
  --themes "spatial intelligence" "world model" "video understanding" "tool-use agent" \
  --outdir ./daily_paper
```

This creates:

- `./daily_paper/2026-W12/2026-W12.md`: themed main digest markdown
- `./daily_paper/2026-W12/papers.json`: normalized paper metadata
- `./daily_paper/2026-W12/artifacts.json`: output manifest
- `./daily_paper/2026-W12/<Top Paper Title>.md`: one top-paper note per theme

These files are not optional. If the user asks for the weekly digest, the expected deliverable is the full weekly folder under `./daily_paper`, with the main markdown plus one standalone top-paper markdown per theme, unless the user explicitly narrows the request.

## Theme Handling

Prefer the four common themes below unless the user requests a different set:

- `spatial intelligence`
- `world model`
- `video understanding`
- `tool-use agent`

For custom themes:

- Pass the theme name directly if simple keyword matching is sufficient.
- Pass `name=kw1,kw2,...` if the theme needs custom keywords.
- Always review custom-theme results manually before finalizing the digest.

## Review Rules

- Sort each themed table by `upvote` descending.
- Keep the table columns ordered as `title | upvote | link | keyword | summary`.
- Include a homepage or method image in `summary` when an arXiv HTML figure is available. If no figure is available, keep the summary text-only.
- Use the weekly source link format: `https://huggingface.co/papers/week/<year-week>`.
- Do not stop after producing only the table. A complete run must include: the themed table markdown, one `Summary` block per theme, and one standalone top-paper markdown per theme.
- By default, place every weekly digest under `./daily_paper/2026-W{wid}`.
- If any generated output is missing a theme `Summary` or a top-paper analysis file, add it manually before finishing.

## Resources

### scripts/build_weekly_digest.py

Use this script to fetch the weekly paper list, fetch arXiv abstracts, assign one primary theme per paper, sort by upvotes, and scaffold the output folder.

If the script misses a relevant paper or misclassifies one, fix the markdown manually instead of forcing the script to be perfect.

Update the script if the Hugging Face paper metadata format changes.
