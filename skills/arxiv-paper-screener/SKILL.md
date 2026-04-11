---
name: arxiv-paper-screener
description: Search and screen arXiv papers for a target field and time window, filter by institution allowlists, then rank open-source papers by GitHub stars and non-open-source papers by citation count. Use when Codex needs to retrieve recent arXiv papers for a field such as spatial intelligence, world model, or agents, and narrow them to papers from top universities, major AI/internet companies, or field-specific leading institutions.
---

# arXiv Paper Screener

Use this skill when the user wants to search arXiv for a field and a recent time window, then filter and rank papers by institution and impact signals.

## Inputs

Normalize the user request into two required parameters:

- `field`: a field name such as `spatial intelligence`, `agent`, `world model`
- `window`: a recent time window such as `7d`, `14d`, `30d`, `90d`, or a Chinese phrase like `一个月以内`

Optional parameters:

- `max_results`: how many arXiv candidates to fetch before filtering, default `100`
- `outdir`: where to write outputs; default to a subfolder under `/Users/ursula/Documents/Playground/arxiv_search`

## Workflow

1. Load the field profile from `references/field_profiles.json`.
2. Search arXiv using the configured keywords for that field and sort by submitted date descending.
3. Filter papers to the requested time window on the client side.
4. Enrich each paper with:
   - institutions and citation count from OpenAlex
   - GitHub repository link and star count when code is available
5. Filter out papers whose author institutions are not in the allowlist file:
   - global `qs100_universities_snapshot`
   - global `major_ai_and_internet_companies`
   - the field-specific institutions for the current field
6. Rank the filtered papers:
   - if code is available, prefer GitHub stars
   - if code is not available, use citation count
7. Write both:
   - a machine-readable `results.json`
   - a readable `results.md`

## Important Notes

- arXiv itself does not provide a stable public per-paper citation metric in the paper metadata API. For the no-code fallback ranking, use OpenAlex `cited_by_count`.
- arXiv metadata does not reliably expose author affiliations. Institution filtering in this skill depends on OpenAlex authorship/institution metadata.
- The institution allowlists are conservative by design. Papers from institutions outside the allowlist are filtered out even if they may still be good.
- Treat `references/institution_allowlists.json` as a curated snapshot. Update it periodically.

## Outputs

Prefer writing outputs to:

`/Users/ursula/Documents/Playground/arxiv_search/<field-slug>_<window>/`

The markdown output should include:

- search field and time window
- total arXiv candidates
- total filtered papers
- ranking rule summary
- one row per paper with:
  - title
  - date
  - institutions
  - code link if present
  - GitHub stars if present
  - citation count
  - ranking metric actually used
  - arXiv link

## Resources

- `references/field_profiles.json`: keyword profiles by field
- `references/institution_allowlists.json`: QS100 university snapshot, major companies, field-specific institution allowlists
- `scripts/search_and_rank_arxiv.py`: end-to-end search, enrich, filter, and rank script

## Quick Start

```bash
python3 /Users/ursula/.codex/skills/arxiv-paper-screener/scripts/search_and_rank_arxiv.py \
  --field "spatial intelligence" \
  --window "30d" \
  --outdir /Users/ursula/Documents/Playground/arxiv_search
```

## Validation

Before finishing:

- Confirm the field resolved to a known profile or a reasonable keyword fallback.
- Confirm the time window was parsed correctly.
- Confirm institution filtering actually used the allowlist file.
- Confirm papers with GitHub links were ranked by stars.
- Confirm papers without code were ranked by citation count.
- If very few papers survive filtering, say so clearly and mention the allowlist may be too restrictive.
