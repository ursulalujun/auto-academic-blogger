#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "references"
ARXIV_API = "https://export.arxiv.org/api/query"
GITHUB_API = "https://api.github.com/repos/"
OPENALEX_WORKS = "https://api.openalex.org/works"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


FIELD_PROFILES = load_json(REF_DIR / "field_profiles.json")
ALLOWLISTS = load_json(REF_DIR / "institution_allowlists.json")


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned or "unknown"


def parse_window(value: str) -> int:
    raw = value.strip().lower()
    mapping = {
        "7d": 7,
        "14d": 14,
        "30d": 30,
        "90d": 90,
        "一周以内": 7,
        "两周以内": 14,
        "一个月以内": 30,
        "一月以内": 30,
        "一个月": 30,
        "三个月以内": 90
    }
    if raw in mapping:
        return mapping[raw]
    if raw.endswith("d") and raw[:-1].isdigit():
        return int(raw[:-1])
    if raw.endswith("天") and raw[:-1].isdigit():
        return int(raw[:-1])
    if raw.endswith("个月") and raw[:-2].isdigit():
        return int(raw[:-2]) * 30
    raise ValueError(f"Unsupported window format: {value}")


def resolve_field(field: str) -> tuple[str, dict]:
    field_lower = field.strip().lower()
    if field_lower in FIELD_PROFILES:
        return field_lower, FIELD_PROFILES[field_lower]
    return field_lower, {"keywords": [field_lower], "field_institutions_key": field_lower}


def http_get(url: str, timeout: float = 30.0, accept: str | None = None) -> bytes:
    headers = {"User-Agent": "Mozilla/5.0 academic_blogger/1.0"}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def build_arxiv_query(keywords: list[str]) -> str:
    parts = [f'all:"{keyword}"' for keyword in keywords[:8]]
    return " OR ".join(parts)


def search_arxiv(keywords: list[str], max_results: int) -> list[dict]:
    params = {
        "search_query": build_arxiv_query(keywords),
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    xml_bytes = http_get(url, accept="application/atom+xml")
    root = ET.fromstring(xml_bytes)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    papers = []
    for entry in root.findall("atom:entry", ns):
        entry_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").rsplit("/", 1)[-1]
        if not entry_id:
            continue
        pdf_link = ""
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("title") == "pdf":
                pdf_link = link.attrib.get("href", "")
                break
        papers.append(
            {
                "arxiv_id": entry_id.split("v")[0],
                "title": re.sub(r"\s+", " ", entry.findtext("atom:title", default="", namespaces=ns)).strip(),
                "summary": re.sub(r"\s+", " ", entry.findtext("atom:summary", default="", namespaces=ns)).strip(),
                "published": entry.findtext("atom:published", default="", namespaces=ns),
                "updated": entry.findtext("atom:updated", default="", namespaces=ns),
                "authors": [author.findtext("atom:name", default="", namespaces=ns) for author in entry.findall("atom:author", ns)],
                "arxiv_url": f"https://arxiv.org/abs/{entry_id.split('v')[0]}",
                "pdf_url": pdf_link or f"https://arxiv.org/pdf/{entry_id.split('v')[0]}",
            }
        )
    return papers


def within_days(date_text: str, days: int) -> bool:
    if not date_text:
        return False
    published = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return published >= cutoff


def normalize_name(text: str) -> str:
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_openalex_record(title: str, arxiv_id: str) -> dict:
    params = {"search": title, "per-page": 8}
    url = f"{OPENALEX_WORKS}?{urllib.parse.urlencode(params)}"
    try:
        data = json.loads(http_get(url, accept="application/json").decode("utf-8"))
    except Exception:
        return {}
    candidates = data.get("results", [])
    norm_title = normalize_name(title)
    best = None
    best_score = -1
    for item in candidates:
        score = 0
        item_title = normalize_name(item.get("title", ""))
        if item_title == norm_title:
            score += 100
        elif norm_title and norm_title in item_title:
            score += 50
        for location in item.get("locations", []) or []:
            landing = (location.get("landing_page_url") or "")
            pdf_url = (location.get("pdf_url") or "")
            if arxiv_id in landing or arxiv_id in pdf_url:
                score += 100
        if item.get("publication_year") and str(item["publication_year"]) in title:
            score += 5
        if score > best_score:
            best = item
            best_score = score
    if best_score < 50:
        return {}
    institutions = []
    raw_affiliations = []
    for authorship in best.get("authorships", []) or []:
        for institution in authorship.get("institutions", []) or []:
            name = institution.get("display_name")
            if name:
                institutions.append(name)
        for raw in authorship.get("raw_affiliation_strings", []) or []:
            if raw:
                raw_affiliations.append(raw)
    best["_institutions"] = sorted(set(institutions))
    best["_raw_affiliations"] = sorted(set(raw_affiliations))
    return best


GITHUB_RE = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def find_github_repo(arxiv_url: str) -> str:
    try:
        html = http_get(arxiv_url, accept="text/html").decode("utf-8", errors="ignore")
    except Exception:
        return ""
    matches = GITHUB_RE.findall(html)
    seen = []
    for owner, repo in matches:
        repo = repo.rstrip(").,/")
        url = f"https://github.com/{owner}/{repo}"
        if url not in seen:
            seen.append(url)
    return seen[0] if seen else ""


def fetch_github_stars(repo_url: str) -> int | None:
    if not repo_url:
        return None
    match = GITHUB_RE.match(repo_url)
    if not match:
        return None
    owner, repo = match.groups()
    url = f"{GITHUB_API}{owner}/{repo}"
    try:
        data = json.loads(http_get(url, accept="application/json").decode("utf-8"))
    except Exception:
        return None
    if isinstance(data, dict) and "stargazers_count" in data:
        return int(data["stargazers_count"])
    return None


def allowed_institution_names(field_key: str) -> list[str]:
    names = []
    names.extend(ALLOWLISTS.get("qs100_universities_snapshot", []))
    names.extend(ALLOWLISTS.get("major_ai_and_internet_companies", []))
    names.extend(ALLOWLISTS.get("field_specific_institutions", {}).get(field_key, []))
    return sorted(set(names))


def institution_allowed(candidate_names: list[str], raw_affiliations: list[str], allowlist: list[str]) -> bool:
    normalized_allow = [normalize_name(name) for name in allowlist]
    haystacks = [normalize_name(name) for name in candidate_names + raw_affiliations if name]
    for hay in haystacks:
        for allowed in normalized_allow:
            if allowed and (allowed in hay or hay in allowed):
                return True
    return False


def ranking_metric(paper: dict) -> tuple[int, str]:
    stars = paper.get("github_stars")
    citations = paper.get("citation_count") or 0
    if stars is not None:
        return int(stars), "github_stars"
    return int(citations), "citation_count"


def write_outputs(outdir: Path, metadata: dict, papers: list[dict]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": metadata, "papers": papers}
    (outdir / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# arXiv Paper Screening Results",
        "",
        f"- field: {metadata['field']}",
        f"- window_days: {metadata['window_days']}",
        f"- arxiv_candidates: {metadata['arxiv_candidates']}",
        f"- filtered_papers: {len(papers)}",
        f"- ranking_rule: code papers use GitHub stars; non-code papers use citation count",
        "",
        "| rank | title | date | institutions | code | stars | citations | ranking metric | arxiv |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for idx, paper in enumerate(papers, start=1):
        metric_value, metric_name = ranking_metric(paper)
        institutions = "; ".join(paper.get("institutions", [])[:4])
        code = paper.get("github_repo") or "-"
        lines.append(
            f"| {idx} | {paper['title']} | {paper['published'][:10]} | {institutions} | {code} | "
            f"{paper.get('github_stars', '-')} | {paper.get('citation_count', 0)} | {metric_name}:{metric_value} | {paper['arxiv_url']} |"
        )
    (outdir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search and rank recent arXiv papers by field and institution.")
    parser.add_argument("--field", required=True)
    parser.add_argument("--window", required=True, help="Examples: 7d, 30d, 90d, 一个月以内")
    parser.add_argument("--max-results", type=int, default=100)
    parser.add_argument("--outdir", default="/Users/ursula/Documents/Playground/arxiv_search")
    args = parser.parse_args()

    field_key, profile = resolve_field(args.field)
    window_days = parse_window(args.window)
    allowlist = allowed_institution_names(profile.get("field_institutions_key", field_key))
    candidates = search_arxiv(profile["keywords"], max_results=args.max_results)
    recent = [paper for paper in candidates if within_days(paper["published"], window_days)]

    filtered = []
    for paper in recent:
        openalex = fetch_openalex_record(paper["title"], paper["arxiv_id"])
        institutions = openalex.get("_institutions", [])
        raw_affiliations = openalex.get("_raw_affiliations", [])
        if not institution_allowed(institutions, raw_affiliations, allowlist):
            continue
        github_repo = find_github_repo(paper["arxiv_url"])
        github_stars = fetch_github_stars(github_repo) if github_repo else None
        citation_count = int(openalex.get("cited_by_count", 0)) if openalex else 0
        metric_value, metric_name = ranking_metric(
            {"github_stars": github_stars, "citation_count": citation_count}
        )
        enriched = {
            **paper,
            "institutions": institutions,
            "raw_affiliations": raw_affiliations,
            "github_repo": github_repo,
            "github_stars": github_stars,
            "citation_count": citation_count,
            "ranking_metric": metric_name,
            "ranking_value": metric_value,
        }
        filtered.append(enriched)
        time.sleep(0.2)

    filtered.sort(key=lambda item: (item["github_stars"] is None, -item["ranking_value"], item["published"]), reverse=False)
    outdir = Path(args.outdir).expanduser().resolve() / f"{slugify(field_key)}_{window_days}d"
    write_outputs(
        outdir,
        metadata={
            "field": field_key,
            "window_days": window_days,
            "arxiv_candidates": len(candidates),
            "profile_keywords": profile["keywords"],
        },
        papers=filtered,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "field": field_key,
                "window_days": window_days,
                "arxiv_candidates": len(candidates),
                "filtered_papers": len(filtered),
                "outdir": str(outdir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
