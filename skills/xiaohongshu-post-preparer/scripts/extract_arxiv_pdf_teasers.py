#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Iterable

import fitz
from PIL import Image, ImageDraw


def parse_paper(value: str) -> tuple[str, str, str]:
    parts = value.split(":", 2)
    if len(parts) < 2:
        raise ValueError("Use --paper slug:arxiv_id:title, for example hydra:2603.25716:HyDRA")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", parts[0]).strip("_").lower()
    arxiv_id = parts[1].strip()
    title = parts[2].strip() if len(parts) == 3 and parts[2].strip() else slug
    if not slug or not arxiv_id:
        raise ValueError(f"Invalid paper spec: {value}")
    return slug, arxiv_id, title


def parse_manual_crop(value: str) -> tuple[str, int, fitz.Rect]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise ValueError("Use --manual-crop slug:page:x0,y0,x1,y1")
    slug = parts[0].strip().lower()
    page = int(parts[1])
    coords = [float(item) for item in parts[2].split(",")]
    if len(coords) != 4:
        raise ValueError("Manual crop must have four coordinates: x0,y0,x1,y1")
    return slug, page, fitz.Rect(*coords)


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


def choose_crop(
    doc: fitz.Document,
    slug: str,
    manual_crops: dict[str, tuple[int, fitz.Rect]],
    max_pages: int,
    figure_number: int,
) -> tuple[int, fitz.Rect, str]:
    if slug in manual_crops:
        page_number, rect = manual_crops[slug]
        page_index = page_number - 1
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(f"Manual crop page out of range for {slug}: {page_number}")
        return page_index, rect & doc[page_index].rect, "manual-crop"

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


def make_contact_sheet(items: Iterable[tuple[str, Path]], out_path: Path) -> None:
    pairs = list(items)
    if not pairs:
        return
    thumb_w, thumb_h = 520, 360
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
    parser = argparse.ArgumentParser(description="Download arXiv PDFs and crop teaser/framework images.")
    parser.add_argument("--paper", action="append", required=True, help="Paper spec: slug:arxiv_id:title")
    parser.add_argument("--outdir", required=True, help="Output asset directory")
    parser.add_argument("--max-pages", type=int, default=5, help="Pages to scan for candidate figures")
    parser.add_argument("--figure-number", type=int, default=1, help="Fallback caption figure number")
    parser.add_argument("--manual-crop", action="append", default=[], help="Manual crop: slug:page:x0,y0,x1,y1")
    parser.add_argument("--zoom", type=float, default=2.5)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    outdir = Path(args.outdir).expanduser().resolve()
    pdf_dir = outdir / "pdfs"
    teaser_dir = outdir / "teasers"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    teaser_dir.mkdir(parents=True, exist_ok=True)

    papers = [parse_paper(value) for value in args.paper]
    manual_crops = {}
    for value in args.manual_crop:
        slug, page, rect = parse_manual_crop(value)
        manual_crops[slug] = (page, rect)

    manifest = {}
    for slug, arxiv_id, title in papers:
        pdf_path = pdf_dir / f"{slug}_{arxiv_id}.pdf"
        teaser_path = teaser_dir / f"{slug}_teaser.png"
        download_pdf(arxiv_id, pdf_path, timeout=args.timeout)
        doc = fitz.open(pdf_path)
        page_index, rect, reason = choose_crop(
            doc,
            slug=slug,
            manual_crops=manual_crops,
            max_pages=args.max_pages,
            figure_number=args.figure_number,
        )
        render_crop(doc, page_index, rect, teaser_path, zoom=args.zoom)
        manifest[slug] = {
            "title": title,
            "arxiv_id": arxiv_id,
            "pdf": str(pdf_path),
            "teaser": str(teaser_path),
            "page": page_index + 1,
            "reason": reason,
            "rect": [round(v, 2) for v in rect],
        }

    contact_sheet = teaser_dir / "contact_sheet.png"
    make_contact_sheet(
        ((data["title"], Path(data["teaser"])) for data in manifest.values()),
        contact_sheet,
    )
    manifest["contact_sheet"] = str(contact_sheet)
    manifest_path = outdir / "teaser_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
