#!/usr/bin/env python3
"""
Compare Docling OCR fallback against an optional Claude 3.7 Sonnet vision OCR attempt.

The goal is to demonstrate:
- Docling fast path (OCR disabled) is extremely quick but returns no text for scanned PDFs.
- Docling fallback with OCR recovers the text.
- Claude 3.7 Sonnet is not viable as a replacement OCR pipeline (slow, expensive, and unreliable).

Usage:
    uv run python scripts/test_ocr_llm_vs_docling.py

Optional Anthropic Vision test:
    export ANTHROPIC_API_KEY=...
    export ENABLE_CLAUDE_OCR_TEST=true
    uv run python scripts/test_ocr_llm_vs_docling.py

Requirements:
    - Docling dependencies installed (`uv sync` already covers this repo).
    - `pdf2image` if you want to try the Claude Vision path (`uv add pdf2image`), plus poppler installed locally.
    - `anthropic` Python client (`uv add anthropic`) if you actually run the Claude 3.7 Vision test.

This script will NOT run the Claude path unless `ENABLE_CLAUDE_OCR_TEST=true` and
`ANTHROPIC_API_KEY` are both present. That avoids accidental API charges.
"""

from __future__ import annotations

import base64
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import DoclingConfig
from src.core.docling_adapter import DoclingDocumentExtractor

try:
    from pdf2image import convert_from_path  # type: ignore
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    from anthropic import Anthropic  # type: ignore
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


@dataclass
class ExtractionResult:
    label: str
    seconds: float
    text_length: int
    metadata: Dict[str, str]


SAMPLE_PDFS = [
    PROJECT_ROOT / "sample_pdf" / "famas_dispute" / "Transaction_Fee_Invoice.pdf",  # scanned
    PROJECT_ROOT / "sample_pdf" / "amrapali_case" / "Amrapali Allotment Letter.pdf",  # digital
]

OUTPUT_DIR = PROJECT_ROOT / "docs" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_docling(file_path: Path, do_ocr: bool) -> ExtractionResult:
    # Disable auto-detection to test explicit OCR on/off behavior
    overrides = {
        "DOCLING_DO_OCR": "true" if do_ocr else "false",
        "DOCLING_AUTO_OCR_DETECTION": "false"
    }
    original: Dict[str, Optional[str]] = {}
    for key, value in overrides.items():
        original[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        config = DoclingConfig()
        extractor = DoclingDocumentExtractor(config)
        start = time.perf_counter()
        extracted = extractor.extract(file_path)
        elapsed = time.perf_counter() - start
        plain_text = extracted.plain_text or ""
        metadata = {
            "extraction_method": extracted.metadata.get("extraction_method", "unknown"),
            "do_ocr": str(do_ocr)
        }
        return ExtractionResult(
            label=f"Docling (OCR={'ON' if do_ocr else 'OFF'})",
            seconds=elapsed,
            text_length=len(plain_text.strip()),
            metadata=metadata,
        )
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def encode_pdf_pages_to_images(file_path: Path) -> List[str]:
    if not HAS_PDF2IMAGE:
        raise RuntimeError("pdf2image is not installed; install it to run the Claude OCR test.")
    # convert_from_path returns Pillow Images; convert to PNG bytes then b64
    images = convert_from_path(str(file_path))
    encoded_pages: List[str] = []
    for image in images:
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        encoded_pages.append(encoded)
    return encoded_pages


def run_claude_vision(file_path: Path) -> ExtractionResult:
    if not HAS_ANTHROPIC:
        raise RuntimeError("anthropic python client not installed; install it to run the Claude OCR test.")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set.")

    encoded_pages = encode_pdf_pages_to_images(file_path)
    client = Anthropic(api_key=api_key)

    start = time.perf_counter()
    messages = []
    for idx, encoded in enumerate(encoded_pages, start=1):
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Page {idx}: Extract all text verbatim."
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": encoded
                    }
                }
            ]
        })

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_output_tokens=4000,
        messages=messages
    )
    elapsed = time.perf_counter() - start
    text_chunks = []
    for item in response.content:
        if item.type == "text":
            text_chunks.append(item.text)
    text = "\n".join(text_chunks)
    return ExtractionResult(
        label="Claude 3.7 Sonnet Vision",
        seconds=elapsed,
        text_length=len(text.strip()),
        metadata={"pages": str(len(encoded_pages))}
    )


def main() -> None:
    enable_claude = os.environ.get("ENABLE_CLAUDE_OCR_TEST", "false").lower() == "true"

    rows = []
    for pdf_path in SAMPLE_PDFS:
        if not pdf_path.exists():
            print(f"⚠️  Missing sample: {pdf_path}")
            continue
        print(f"\n===== {pdf_path.name} =====")

        fast = run_docling(pdf_path, do_ocr=False)
        fallback_needed = fast.text_length < 50
        print(f"Fast pass: {fast.seconds:.3f}s, text length={fast.text_length}")

        results = [fast]
        if fallback_needed:
            fallback = run_docling(pdf_path, do_ocr=True)
            print(f"Fallback (OCR): {fallback.seconds:.3f}s, text length={fallback.text_length}")
            results.append(fallback)
        else:
            print("Fallback not needed (plaintext document).")

        if enable_claude:
            try:
                claude = run_claude_vision(pdf_path)
                print(f"Claude 3.7 Vision: {claude.seconds:.3f}s, text length={claude.text_length}")
                results.append(claude)
            except Exception as exc:
                print(f"Claude OCR test skipped: {exc}")

        for result in results:
            rows.append({
                "document": pdf_path.name,
                "scenario": result.label,
                "seconds": round(result.seconds, 3),
                "text_length": result.text_length,
                **{f"meta_{k}": v for k, v in result.metadata.items()}
            })

    if not rows:
        print("No results collected.")
        return

    import pandas as pd

    df = pd.DataFrame(rows)
    print("\n=== Summary ===")
    print(df.to_string(index=False))

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"ocr_fallback_comparison_{timestamp}.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved detailed results to {out_path}")


if __name__ == "__main__":
    main()
