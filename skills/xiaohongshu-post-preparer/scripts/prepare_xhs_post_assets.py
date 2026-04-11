#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import fitz
from PIL import Image, ImageDraw


def parse_paper(value: str) -> tuple[str, str, str]:
    parts = value.split(":", 2)
    if len(parts) < 2:
        raise ValueError("Use --paper slug:arxiv_id:title")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", parts[0]).strip("_").lower()
    arxiv_id = parts[1].strip()
    title = parts[2].strip() if len(parts) == 3 and parts[2].strip() else slug
    if not slug or not arxiv_id:
        raise ValueError(f"Invalid paper spec: {value}")
    return slug, arxiv_id, title


def parse_mapping(value: str) -> tuple[str, str]:
    slug, payload = value.split(":", 1)
    return slug.strip().lower(), payload.strip()


def request_url(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def download_pdf(arxiv_id: str, out_path: Path, timeout: float) -> None:
    if out_path.exists() and out_path.stat().st_size > 100_000:
        return
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    for attempt in range(4):
        try:
            out_path.write_bytes(request_url(url, timeout))
            if out_path.stat().st_size > 100_000:
                return
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 3)
    raise RuntimeError(f"Failed to download PDF for {arxiv_id}")


def render_page(doc: fitz.Document, page_index: int, out_path: Path, zoom: float = 2.2) -> None:
    pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(out_path)


def caption_crop(page: fitz.Page, figure_number: int) -> fitz.Rect | None:
    pattern = re.compile(rf"\b(Figure|Fig\.)\s*{figure_number}\b", re.I)
    matches = [block for block in page.get_text("blocks") if pattern.search(block[4])]
    if not matches:
        return None
    x0, y0, x1, y1, *_ = min(matches, key=lambda block: block[1])
    top = max(0, y0 - page.rect.height * 0.50)
    bottom = min(page.rect.height, y0 + 8)
    rect = fitz.Rect(0, top, page.rect.width, bottom)
    return rect if rect.height > 120 else None


def best_embedded_image_crop(doc: fitz.Document, max_pages: int) -> tuple[int, fitz.Rect, str] | None:
    best: tuple[float, int, fitz.Rect] | None = None
    for page_index in range(min(max_pages, len(doc))):
        page = doc[page_index]
        page_area = page.rect.width * page.rect.height
        for info in page.get_image_info(xrefs=True):
            bbox = fitz.Rect(info["bbox"])
            area = bbox.width * bbox.height
            if area < page_area * 0.06 or bbox.width < 140 or bbox.height < 90:
                continue
            score = area / page_area - page_index * 0.06
            if best is None or score > best[0]:
                best = (score, page_index, bbox)
    if best is None:
        return None
    _, page_index, bbox = best
    page = doc[page_index]
    margin_x = page.rect.width * 0.025
    margin_y = page.rect.height * 0.025
    return page_index, (bbox + (-margin_x, -margin_y, margin_x, margin_y)) & page.rect, "embedded-image"


def choose_teaser_crop(doc: fitz.Document, max_pages: int, figure_number: int) -> tuple[int, fitz.Rect, str]:
    embedded = best_embedded_image_crop(doc, max_pages=max_pages)
    if embedded:
        return embedded
    for page_index in range(min(max_pages, len(doc))):
        rect = caption_crop(doc[page_index], figure_number=figure_number)
        if rect is not None:
            return page_index, rect, f"figure-{figure_number}-caption-crop"
    page = doc[0]
    return 0, fitz.Rect(0, page.rect.height * 0.14, page.rect.width, page.rect.height * 0.70), "first-page-fallback"


def render_crop(doc: fitz.Document, page_index: int, rect: fitz.Rect, out_path: Path, zoom: float) -> None:
    pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
    pix.save(out_path)


META_PATTERNS = [
    re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"', re.IGNORECASE),
    re.compile(r'<meta\s+name="twitter:image"\s+content="([^"]+)"', re.IGNORECASE),
]


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


def fetch_hf_cover(paper_url: str, out_path: Path, timeout: float) -> str:
    headers = {"User-Agent": "Mozilla/5.0 Codex/1.0"}
    page_req = urllib.request.Request(paper_url, headers=headers)
    with urllib.request.urlopen(page_req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    cover_url = find_cover_url(html)
    if out_path.suffix == "":
        out_path = out_path.with_suffix(detect_ext(cover_url))
    image_req = urllib.request.Request(cover_url, headers=headers)
    with urllib.request.urlopen(image_req, timeout=timeout) as resp:
        out_path.write_bytes(resp.read())
    return str(out_path)


def make_contact_sheet(items: Iterable[tuple[str, Path]], out_path: Path, thumb_w: int, thumb_h: int) -> None:
    pairs = list(items)
    if not pairs:
        return
    cols = 2 if len(pairs) > 1 else 1
    rows = (len(pairs) + cols - 1) // cols
    sheet = Image.new("RGB", (thumb_w * cols, (thumb_h + 36) * rows), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, path) in enumerate(pairs):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (thumb_w, thumb_h), "white")
        canvas.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
        ox = (idx % cols) * thumb_w
        oy = (idx // cols) * (thumb_h + 36)
        draw.text((ox + 8, oy + 6), label, fill=(0, 0, 0))
        sheet.paste(canvas, (ox, oy + 24))
    sheet.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Xiaohongshu post assets from arXiv PDFs and HF paper pages.")
    parser.add_argument("--mode", choices=["overview", "single"], required=True)
    parser.add_argument("--paper", action="append", required=True, help="Paper spec: slug:arxiv_id:title")
    parser.add_argument("--hf-paper-url", action="append", default=[], help="slug:https://huggingface.co/papers/...")
    parser.add_argument("--hf-paper-id", action="append", default=[], help="slug:2603.25716")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--figure-number", type=int, default=1)
    parser.add_argument("--zoom", type=float, default=2.5)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    outdir = Path(args.outdir).expanduser().resolve()
    pdf_dir = outdir / "pdfs"
    page_dir = outdir / "first_pages"
    cover_dir = outdir / "covers"
    teaser_dir = outdir / "teasers"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    page_dir.mkdir(parents=True, exist_ok=True)
    cover_dir.mkdir(parents=True, exist_ok=True)
    teaser_dir.mkdir(parents=True, exist_ok=True)

    hf_urls = {slug: url for slug, url in [parse_mapping(v) for v in args.hf_paper_url]}
    for slug, paper_id in [parse_mapping(v) for v in args.hf_paper_id]:
        hf_urls[slug] = f"https://huggingface.co/papers/{paper_id}"

    papers = [parse_paper(value) for value in args.paper]
    manifest = {
        "mode": args.mode,
        "asset_root": str(outdir),
        "posts": [],
    }

    first_page_items = []
    teaser_items = []
    for slug, arxiv_id, title in papers:
        pdf_path = pdf_dir / f"{slug}_{arxiv_id}.pdf"
        download_pdf(arxiv_id, pdf_path, timeout=args.timeout)
        doc = fitz.open(pdf_path)

        first_page_path = page_dir / f"{slug}_page1.png"
        render_page(doc, 0, first_page_path)
        first_page_items.append((title, first_page_path))

        if args.mode == "overview":
            manifest["posts"].append(
                {
                    "slug": slug,
                    "title": title,
                    "arxiv_id": arxiv_id,
                    "pdf": str(pdf_path),
                    "first_page_image": str(first_page_path),
                }
            )
            continue

        page_index, rect, reason = choose_teaser_crop(doc, max_pages=args.max_pages, figure_number=args.figure_number)
        teaser_path = teaser_dir / f"{slug}_teaser.png"
        render_crop(doc, page_index, rect, teaser_path, zoom=args.zoom)
        teaser_items.append((title, teaser_path))

        hf_cover_url = hf_urls.get(slug, "")
        if hf_cover_url:
            cover_path = Path(fetch_hf_cover(hf_cover_url, cover_dir / slug, timeout=args.timeout))
            cover_source = "huggingface_paper_cover"
        else:
            cover_path = cover_dir / f"{slug}_cover.png"
            render_page(doc, 0, cover_path)
            cover_source = "arxiv_pdf_first_page"

        first_page_has_teaser = page_index == 0
        manifest["posts"].append(
            {
                "slug": slug,
                "title": title,
                "arxiv_id": arxiv_id,
                "pdf": str(pdf_path),
                "cover_image": str(cover_path),
                "cover_source": cover_source,
                "first_page_image": str(first_page_path),
                "teaser_image": None if first_page_has_teaser else str(teaser_path),
                "teaser_page": page_index + 1,
                "teaser_reason": reason,
                "image_count": 1 if first_page_has_teaser else 2,
                "note": "first page already contains the teaser/framework figure" if first_page_has_teaser else "upload teaser/framework as second image",
            }
        )

    make_contact_sheet(first_page_items, page_dir / "contact_sheet.png", thumb_w=420, thumb_h=560)
    if args.mode == "single":
        make_contact_sheet(teaser_items, teaser_dir / "contact_sheet.png", thumb_w=520, thumb_h=360)

    out_path = outdir / "post_asset_manifest.json"
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
