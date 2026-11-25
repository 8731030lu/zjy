#!/usr/bin/env python3
"""Extract page-numbered text from a PDF into a JSON file.

Output schema:
{
  "source": "<abs path>",
  "total_pages": 12,
  "ocr": false,
  "pages": [ {"page": 1, "text": "..."}, ... ],
  "warnings": [...]
}

Uses pypdf (or pdfplumber) when available. If neither is importable, it
reports `extraction: "unavailable"` and writes an empty page list instead of
fabricating text. This lets the caller fall back to the environment's
pdf-text-tool / ocr-tool without guessing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def extract_with_pypdf(path: str):
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(path)
    pages = []
    warnings = []
    for idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover - page-level robustness
            text = ""
            warnings.append(f"page {idx}: extraction failed: {exc}")
        pages.append({"page": idx, "text": text})
    return pages, warnings


def extract_with_pdfplumber(path: str):
    import pdfplumber  # type: ignore

    pages = []
    warnings = []
    with pdfplumber.open(path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover
                text = ""
                warnings.append(f"page {idx}: extraction failed: {exc}")
            pages.append({"page": idx, "text": text})
    return pages, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract page-numbered text from a PDF.")
    ap.add_argument("pdf", help="path to the PDF")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--min-chars", type=int, default=0,
                    help="warn when total extracted text is below this many characters")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        result = {
            "source": os.path.abspath(args.pdf),
            "total_pages": 0,
            "ocr": False,
            "pages": [],
            "warnings": [f"file not found: {args.pdf}"],
            "extraction": "unavailable",
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return 0

    pages = []
    warnings = []
    engine = None
    try:
        pages, warnings = extract_with_pypdf(args.pdf)
        engine = "pypdf"
    except Exception:
        try:
            pages, warnings = extract_with_pdfplumber(args.pdf)
            engine = "pdfplumber"
        except Exception as exc:
            warnings.append(f"no PDF text extractor available: {exc}")

    total_chars = sum(len(p["text"]) for p in pages)
    if args.min_chars and total_chars < args.min_chars:
        warnings.append(
            f"total extracted text {total_chars} chars is below --min-chars {args.min_chars}; "
            "the PDF may be a scanned image and need OCR."
        )

    result = {
        "source": os.path.abspath(args.pdf),
        "total_pages": len(pages),
        "ocr": False,
        "engine": engine,
        "total_chars": total_chars,
        "pages": pages,
        "warnings": warnings,
        "extraction": "ok" if pages else "unavailable",
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({"status": "ok", "engine": engine,
                      "total_pages": len(pages), "total_chars": total_chars,
                      "warnings": warnings}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
