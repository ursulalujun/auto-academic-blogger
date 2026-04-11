#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests


META_PATTERNS = [
    re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"', re.IGNORECASE),
    re.compile(r'<meta\s+name="twitter:image"\s+content="([^"]+)"', re.IGNORECASE),
]


def normalize_paper_url(paper_url: str | None, paper_id: str | None) -> str:
    if paper_url:
        return paper_url
    if not paper_id:
        raise ValueError("Provide either --paper-url or --paper-id")
    return f"https://huggingface.co/papers/{paper_id}"


def detect_ext(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".jpg") or path.endswith(".jpeg"):
        return ".jpg"
    if path.endswith(".webp"):
        return ".webp"
    return ".png"


def find_cover_url(html: str) -> str:
    for pattern in META_PATTERNS:
        match = pattern.search(html)
        if match:
            return match.group(1)
    raise RuntimeError("Could not find Hugging Face paper cover URL in page metadata")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-url")
    parser.add_argument("--paper-id")
    parser.add_argument("--out")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    paper_url = normalize_paper_url(args.paper_url, args.paper_id)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Codex/1.0",
        }
    )

    page_resp = session.get(paper_url, timeout=args.timeout)
    page_resp.raise_for_status()
    cover_url = find_cover_url(page_resp.text)

    if args.out:
        out_path = Path(args.out)
    else:
        paper_id = paper_url.rstrip("/").rsplit("/", 1)[-1]
        out_path = Path.cwd() / f"{paper_id}{detect_ext(cover_url)}"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    image_resp = session.get(cover_url, timeout=args.timeout)
    image_resp.raise_for_status()
    out_path.write_bytes(image_resp.content)

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"Cover file was not created correctly: {out_path}")

    print(out_path)
    print(cover_url)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
