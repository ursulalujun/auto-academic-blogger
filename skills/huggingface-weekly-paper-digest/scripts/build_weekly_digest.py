#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple


PRESET_THEMES = {
    "spatial intelligence": [
        "spatial",
        "3d",
        "geometry",
        "geometric",
        "localization",
        "viewpoint",
        "layout",
        "scene understanding",
        "scene reconstruction",
        "monocular",
        "gaussian splatting",
        "stereo",
        "embodied spatial reasoning",
    ],
    "world model": [
        "world model",
        "world simulation",
        "forecasting",
        "future forecasting",
        "world-action",
        "city-scale world",
        "interactive world",
        "embodied simulation",
        "stereo video generation",
    ],
    "video understanding": [
        "video reasoning",
        "video understanding",
        "long video",
        "audio-video",
        "streaming video",
        "event prediction",
        "temporal reasoning",
        "omni-modal",
        "multimodal video",
        "video llm",
    ],
    "tool-use agent": [
        "tool use",
        "tool-using",
        "agentic planning",
        "planning",
        "search agent",
        "tool chaining",
        "rollout",
        "enterprise",
        "skills",
        "text-to-sql",
        "tool-integrated",
        "computer-use",
    ],
}


def fetch_text(url: str, accept: str = "text/html", retries: int = 4) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": accept,
        },
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt >= retries:
                raise
            retry_after = exc.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                delay = int(retry_after)
            else:
                delay = min(60, 5 * (2**attempt))
            time.sleep(delay)
    raise RuntimeError(f"Failed to fetch {url}")


def fetch_json(url: str):
    return json.loads(fetch_text(url, accept="application/json"))


def parse_wid(raw_wid: str) -> Tuple[str, int, int]:
    text = raw_wid.strip()
    current_year = dt.date.today().isocalendar().year
    if re.fullmatch(r"\d{4}-W\d{1,2}", text):
        year, week = text.split("-W")
        return text, int(year), int(week)
    if re.fullmatch(r"W\d{1,2}", text, re.I):
        week = int(text[1:])
        return f"{current_year}-W{week:02d}", current_year, week
    if re.fullmatch(r"\d{1,2}", text):
        week = int(text)
        return f"{current_year}-W{week:02d}", current_year, week
    raise ValueError(f"Unsupported wid format: {raw_wid}")


def iso_week_dates(year: int, week: int) -> List[dt.date]:
    return [dt.date.fromisocalendar(year, week, day) for day in range(1, 8)]


def slugify(name: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "", name).strip()
    return cleaned or "untitled"


def title_case_theme(theme: str) -> str:
    return " ".join(part.capitalize() for part in theme.split())


def parse_themes(raw_themes: List[str]) -> Dict[str, List[str]]:
    themes: Dict[str, List[str]] = {}
    for raw in raw_themes:
        theme = raw.strip()
        if not theme:
            continue
        lower = theme.lower()
        if lower in PRESET_THEMES:
            themes[theme] = PRESET_THEMES[lower]
            continue
        if "=" in theme:
            name, keywords = theme.split("=", 1)
            themes[name.strip()] = [k.strip().lower() for k in keywords.split(",") if k.strip()]
            continue
        auto_keywords = [lower] + [w for w in re.split(r"[\s/-]+", lower) if len(w) > 2]
        themes[theme] = sorted(set(auto_keywords))
    if not themes:
        raise ValueError("At least one theme is required.")
    return themes


def fetch_week_papers(year: int, week: int) -> List[dict]:
    papers = []
    seen = set()
    for date_value in iso_week_dates(year, week):
        url = f"https://huggingface.co/api/daily_papers?date={date_value.isoformat()}&p=0"
        try:
            day_items = fetch_json(url)
        except urllib.error.HTTPError as exc:
            if exc.code in {400, 404}:
                continue
            raise
        for item in day_items:
            pid = (item.get("id") or item.get("paper", {}).get("id") or "").split("v")[0]
            if not pid or pid in seen:
                continue
            seen.add(pid)
            papers.append(
                {
                    "id": pid,
                    "title": item.get("title") or item.get("paper", {}).get("title") or pid,
                    "upvotes": item.get("upvotes")
                    or item.get("paper", {}).get("upvotes")
                    or item.get("num_upvotes")
                    or item.get("paper", {}).get("num_upvotes")
                    or 0,
                    "date": date_value.isoformat(),
                    "hf_url": f"https://huggingface.co/papers/{pid}",
                    "arxiv_url": f"https://arxiv.org/abs/{pid}",
                }
            )
    return papers


def fetch_arxiv_abstracts(paper_ids: List[str]) -> Dict[str, str]:
    summaries = {}
    chunk_size = 10
    for i in range(0, len(paper_ids), chunk_size):
        chunk = paper_ids[i : i + chunk_size]
        url = "https://export.arxiv.org/api/query?id_list=" + ",".join(chunk)
        xml_text = fetch_text(url, accept="application/atom+xml")
        entries = re.findall(
            r"<entry>.*?<id>http://arxiv.org/abs/([^<]+)</id>.*?<summary>(.*?)</summary>.*?</entry>",
            xml_text,
            re.S,
        )
        for paper_id, summary in entries:
            clean_id = paper_id.split("v")[0]
            clean_summary = html.unescape(re.sub(r"\s+", " ", summary)).strip()
            summaries[clean_id] = clean_summary
        time.sleep(4.0)
    return summaries


def keyword_pattern(keyword: str) -> re.Pattern:
    pieces = [re.escape(piece) for piece in keyword.lower().split()]
    if len(pieces) == 1:
        return re.compile(rf"(?<!\w){pieces[0]}(?!\w)")
    return re.compile(r"(?<!\w)" + r"\s+".join(pieces) + r"(?!\w)")


def theme_score(title: str, abstract: str, keywords: List[str]) -> Tuple[int, List[str]]:
    title_text = title.lower()
    abstract_text = abstract.lower()
    score = 0
    matched = []
    for keyword in keywords:
        pattern = keyword_pattern(keyword)
        title_hit = bool(pattern.search(title_text))
        abstract_hit = bool(pattern.search(abstract_text))
        if title_hit or abstract_hit:
            if title_hit:
                score += 4 if " " in keyword else 2
            if abstract_hit:
                score += 2 if " " in keyword else 1
            matched.append(keyword)
    return score, matched


def assign_primary_theme(papers: List[dict], themes: Dict[str, List[str]]) -> Dict[str, List[dict]]:
    grouped = {theme: [] for theme in themes}
    for paper in papers:
        scored = []
        for theme, keywords in themes.items():
            score, matched = theme_score(paper["title"], paper.get("abstract", ""), keywords)
            scored.append((score, len(matched), theme, matched))
        best = max(scored, key=lambda item: (item[0], item[1]))
        if best[0] < 2:
            continue
        paper["primary_theme"] = best[2]
        paper["matched_keywords"] = best[3]
        grouped[best[2]].append(paper)
    for theme in grouped:
        grouped[theme].sort(key=lambda item: (-int(item["upvotes"]), item["title"].lower()))
    return grouped


def fetch_first_figure(arxiv_id: str) -> str:
    try:
        html_text = fetch_text(f"https://arxiv.org/html/{arxiv_id}")
    except Exception:
        return ""
    matches = re.findall(r'<img[^>]+src="([^"]+)"', html_text)
    for src in matches:
        lower_src = src.lower()
        if any(bad in lower_src for bad in ["arxiv-logo", "cornell", "icon", "logo", "github.png"]):
            continue
        if src.startswith("http"):
            return src
        return "https://arxiv.org/html/" + src.lstrip("/")
    return ""


def fetch_paper_page_links(paper_id: str) -> Dict[str, str]:
    try:
        page = fetch_text(f"https://huggingface.co/papers/{paper_id}")
    except Exception:
        return {}
    data = {}
    patterns = {
        "project_page": r'&quot;projectPage&quot;:&quot;([^"]+?)&quot;',
        "github_repo": r'&quot;githubRepo&quot;:&quot;([^"]+?)&quot;',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, page)
        if match:
            data[key] = html.unescape(match.group(1))
    dataset_match = re.search(r"(https://huggingface\.co/datasets/[^<\\\" ),]+)", page)
    if dataset_match:
        data["dataset"] = html.unescape(dataset_match.group(1))
    return data


def first_sentences(text: str, count: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:count]).strip()


def split_sentences(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def select_sentences(text: str, cues: List[str], limit: int = 2) -> List[str]:
    sentences = split_sentences(text)
    picked = []
    lowered = [cue.lower() for cue in cues]
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(cue in sentence_lower for cue in lowered):
            picked.append(sentence)
        if len(picked) >= limit:
            break
    return picked


def fallback_sentence_block(text: str, preferred: List[str], sentence_count: int = 2) -> str:
    picked = select_sentences(text, preferred, limit=sentence_count)
    if not picked:
        picked = split_sentences(text)[:sentence_count]
    return " ".join(picked).strip()


def detect_traits(items: List[dict]) -> Dict[str, int]:
    buckets = {
        "benchmark_eval": ["benchmark", "evaluation", "evaluate"],
        "memory": ["memory", "retrieval", "cache"],
        "rl_planning": ["reinforcement learning", "planning", "policy", "rollout"],
        "generation": ["generation", "diffusion", "autoregressive", "synthesize"],
        "grounding": ["grounding", "grounded", "localization", "geometry", "3d", "spatial"],
        "streaming_long_context": ["streaming", "long", "multi-turn", "long-horizon"],
    }
    counts = {key: 0 for key in buckets}
    for item in items:
        text = f"{item['title']} {item.get('abstract', '')}".lower()
        for key, keywords in buckets.items():
            if any(keyword in text for keyword in keywords):
                counts[key] += 1
    return counts


def theme_summary_lines(theme: str, items: List[dict]) -> List[str]:
    if not items:
        return ["- 这一主题在本周没有筛出高置信度论文。"]
    top_titles = "、".join(item["title"] for item in items[:3])
    traits = detect_traits(items)
    summary = []
    summary.append(
        f"- 本周这一主题的高关注论文集中在 `{top_titles}`，整体上都在推进 `{theme}` 从单点能力走向更可部署、更长时程、或更强结构约束的建模。"
    )
    if traits["benchmark_eval"] >= max(1, len(items) // 3):
        summary.append("- 一个明显共性是很多工作不只提出新模型，也在补更接近真实应用的 benchmark 或 evaluation setting，说明社区开始更重视可验证性和真实场景对齐。")
    if traits["memory"] >= max(1, len(items) // 3):
        summary.append("- 记忆、检索或状态保持是反复出现的设计点，说明这类任务的核心瓶颈往往不只是瞬时推理，而是如何把历史上下文以结构化方式保留下来。")
    elif traits["grounding"] >= max(1, len(items) // 3):
        summary.append("- 这批论文普遍强调 grounding：不是只做表层相关性，而是希望模型在几何、空间、工具状态或外部证据上有更稳的对齐。")
    if traits["generation"] >= max(1, len(items) // 3):
        summary.append("- 在方法层面，一个高频趋势是把生成模型当成结构先验或世界先验来复用，而不是只把生成当成最终任务本身。")
    elif traits["rl_planning"] >= max(1, len(items) // 3):
        summary.append("- 在方法层面，规划、策略学习和过程级优化出现频率很高，说明研究重点正从“会不会做”转向“能不能稳定完成长链过程”。")
    else:
        summary.append("- 从方法上看，这一主题的创新更偏向结构化表示、任务分解和更贴合目标任务的数据组织，而不是单纯扩大模型规模。")
    return summary


def build_top_paper_analysis(paper: dict, theme: str) -> Dict[str, str]:
    abstract = paper.get("abstract", "")
    motivation = fallback_sentence_block(
        abstract,
        [
            "however",
            "despite",
            "remain",
            "struggle",
            "limited",
            "bottleneck",
            "challenge",
            "gap",
        ],
        2,
    )
    method = fallback_sentence_block(
        abstract,
        [
            "we propose",
            "we present",
            "we introduce",
            "our approach",
            "specifically",
            "framework",
            "model",
        ],
        3,
    )
    insights_lines = []
    insights_lines.append(
        f"这篇论文之所以能成为本周 `{theme}` 里 upvote 最高的一篇，核心在于它不只是把任务做得更强，而是给出了一个更有代表性的研究方向。"
    )
    if "benchmark" in abstract.lower() or "evaluate" in abstract.lower():
        insights_lines.append("它的价值很大一部分来自 evaluation 设计：作者把问题放进更接近真实部署的环境里，因此结论更容易外推到实际系统。")
    if any(word in abstract.lower() for word in ["memory", "retrieval", "cache"]):
        insights_lines.append("论文强调结构化记忆或检索，说明这一方向的真正难点不只是单步推理，而是跨时间保持可用状态。")
    if any(word in abstract.lower() for word in ["diffusion", "generation", "generative", "synthesize"]):
        insights_lines.append("它也反映出一个很强的趋势：生成模型内部的结构先验正在被重新解释和复用，用来提升理解、控制或世界建模能力。")
    if any(word in abstract.lower() for word in ["planning", "policy", "rollout", "agent"]):
        insights_lines.append("从 agent 角度看，它把关注点从单次动作质量推进到了过程质量、规划质量或长链行为稳定性。")
    if len(insights_lines) == 1:
        insights_lines.append("从研究趋势上看，这篇工作代表了本周这个主题里最清晰的主线：通过更结构化的建模方式，把能力从 demo 推向更稳定、更可迁移的系统表现。")
    return {
        "motivation": motivation,
        "method": method,
        "insights": "\n".join(f"- {line}" for line in insights_lines),
    }


def write_main_markdown(
    out_path: Path,
    week_label: str,
    themes: Dict[str, List[str]],
    grouped: Dict[str, List[dict]],
) -> None:
    lines = [
        "# Hugging Face Weekly Papers Digest",
        "",
        f"来源：",
        f"- https://huggingface.co/papers/week/{week_label}",
        "",
        "筛选主题：",
    ]
    for theme in themes:
        lines.append(f"- {theme}")
    lines.append("")
    for theme in themes:
        lines.append(f"## {title_case_theme(theme)}")
        lines.append("")
        lines.append("| title | upvote | link | keyword | summary |")
        lines.append("| --- | --- | --- | --- | --- |")
        for paper in grouped.get(theme, []):
            summary = first_sentences(paper.get("abstract", ""), 2)
            if paper.get("figure_url"):
                summary += f"  ![]({paper['figure_url']})"
            keywords = "; ".join(paper.get("matched_keywords", []))
            lines.append(
                f"| {paper['title']} | {paper['upvotes']} | {paper['arxiv_url']} | {keywords} | {summary} |"
            )
        if not grouped.get(theme):
            lines.append("| No strongly matched papers | - | - | - | - |")
        lines.append("")
        lines.append("**Summary**")
        lines.append("")
        lines.extend(theme_summary_lines(theme, grouped.get(theme, [])))
        lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_top_paper_file(out_dir: Path, paper: dict, theme: str) -> None:
    links = paper.get("page_links", {})
    analysis = build_top_paper_analysis(paper, theme)
    lines = [
        f"# {paper['title']}",
        "",
        f"- 领域：{title_case_theme(theme)}",
        f"- Hugging Face upvote：{paper['upvotes']}",
        f"- 原文：<{paper['arxiv_url']}>",
        f"- Hugging Face 论文页：<{paper['hf_url']}>",
    ]
    if links.get("project_page"):
        lines.append(f"- Project：<{links['project_page']}>")
    if links.get("github_repo"):
        lines.append(f"- GitHub：<{links['github_repo']}>")
    if links.get("dataset"):
        lines.append(f"- Hugging Face Dataset：<{links['dataset']}>")
    lines.extend(
        [
            "",
            "## Motivation",
            "",
            analysis["motivation"],
            "",
            "## Method",
            "",
            analysis["method"],
            "",
            "## Insights",
            "",
            analysis["insights"],
            "",
        ]
    )
    filename = slugify(paper["title"]) + ".md"
    (out_dir / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a weekly Hugging Face papers digest scaffold.")
    parser.add_argument("--wid", required=True, help="Week id, e.g. W12, 12, or 2026-W12")
    parser.add_argument("--themes", required=True, nargs="+", help="Theme names or name=kw1,kw2 entries")
    parser.add_argument("--outdir", default="/Users/ursula/Documents/Playground/daily_paper", help="Output parent directory")
    args = parser.parse_args()

    week_label, year, week = parse_wid(args.wid)
    themes = parse_themes(args.themes)
    papers = fetch_week_papers(year, week)
    abstracts = fetch_arxiv_abstracts([paper["id"] for paper in papers])
    for paper in papers:
        paper["abstract"] = abstracts.get(paper["id"], "")
    grouped = assign_primary_theme(papers, themes)

    normalized_week = week_label
    out_dir = Path(args.outdir).expanduser().resolve() / normalized_week
    out_dir.mkdir(parents=True, exist_ok=True)

    top_papers = {}
    for theme, items in grouped.items():
        for paper in items[: min(5, len(items))]:
            paper["figure_url"] = fetch_first_figure(paper["id"])
        if items:
            top = items[0]
            top["page_links"] = fetch_paper_page_links(top["id"])
            top_papers[theme] = top
        time.sleep(0.2)

    main_md = out_dir / f"{week_label}.md"
    write_main_markdown(main_md, week_label, themes, grouped)

    for theme, paper in top_papers.items():
        write_top_paper_file(out_dir, paper, theme)

    missing_theme_summaries = [theme for theme, items in grouped.items() if items and not theme_summary_lines(theme, items)]
    missing_top_papers = [theme for theme, items in grouped.items() if items and theme not in top_papers]
    if missing_theme_summaries or missing_top_papers:
        raise RuntimeError(
            f"Incomplete digest output: missing summaries={missing_theme_summaries}, missing top papers={missing_top_papers}"
        )
    for theme, paper in top_papers.items():
        top_file = out_dir / (slugify(paper["title"]) + ".md")
        if not top_file.exists():
            raise RuntimeError(f"Missing top-paper markdown for theme: {theme}")
        content = top_file.read_text(encoding="utf-8")
        required_markers = ["## Motivation", "## Method", "## Insights"]
        if any(marker not in content for marker in required_markers):
            raise RuntimeError(f"Incomplete top-paper markdown for theme: {theme}")
        if "TODO:" in content:
            raise RuntimeError(f"Unresolved placeholder in top-paper markdown for theme: {theme}")
    main_content = main_md.read_text(encoding="utf-8") if main_md.exists() else ""
    for theme, items in grouped.items():
        if items and f"## {title_case_theme(theme)}" not in main_content:
            raise RuntimeError(f"Missing theme section in main markdown: {theme}")
        if items and "**Summary**" not in main_content:
            raise RuntimeError("Missing Summary block in main markdown")

    artifacts = {
        "week_label": week_label,
        "themes": list(themes.keys()),
        "main_markdown": str(main_md),
        "folder": str(out_dir),
        "normalized_week": week_label,
        "top_papers": {
            theme: {
                "title": paper["title"],
                "upvotes": paper["upvotes"],
                "file": str(out_dir / (slugify(paper["title"]) + ".md")),
            }
            for theme, paper in top_papers.items()
        },
        "paper_count": len(papers),
        "selected_count": sum(len(items) for items in grouped.values()),
    }
    (out_dir / "artifacts.json").write_text(json.dumps(artifacts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "papers.json").write_text(json.dumps(papers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(artifacts, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
