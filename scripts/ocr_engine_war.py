#!/usr/bin/env python3
"""
OCR Engine War

Compares OCR engines on a set of PDFs/images and writes timing + text length
metrics, plus per-engine extracted text for manual review.

Engines supported (auto-skips if deps are unavailable):
- docling (via DoclingDocumentExtractor)
- tesseract (via tesserocr)
- paddleocr (via PaddleOCR)

Usage:
  uv run python scripts/ocr_engine_war.py \
    --input-dir sample_pdf \
    --output-dir test_results/ocr_engine_war_2025-10-03 \
    --engines docling tesseract paddleocr \
    --page-limit 2 --dpi 300

Notes:
- Tesseract requires native Tesseract to be installed and `TESSDATA_PREFIX` set.
- PaddleOCR can leverage GPU if available; otherwise runs on CPU.
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import fitz  # PyMuPDF
import pandas as pd

# Optional imports guarded at runtime
try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore


# ---- Project imports (Docling adapter) ----
try:
    from src.core.config import DoclingConfig
    from src.core.docling_adapter import DoclingDocumentExtractor
except Exception:
    DoclingConfig = None  # type: ignore
    DoclingDocumentExtractor = None  # type: ignore


@dataclass
class OCREntry:
    document: str
    engine: str
    seconds: float
    pages_processed: int
    text_length: int
    notes: str = ""


def list_input_files(input_dir: Path) -> List[Path]:
    exts = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    files = []
    for p in sorted(input_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return files


def render_pdf_to_images(pdf_path: Path, dpi: int, page_limit: Optional[int]) -> List["np.ndarray"]:
    """Render a PDF to RGB numpy arrays using PyMuPDF (fitz)."""
    if np is None:
        raise RuntimeError("numpy not available; cannot render images")

    doc = fitz.open(pdf_path)
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    images: List["np.ndarray"] = []
    try:
        total = len(doc)
        pages = min(total, page_limit) if page_limit else total
        for i in range(pages):
            page = doc[i]
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8)
            img = img.reshape(pix.h, pix.w, 3)
            images.append(img)
        return images
    finally:
        doc.close()


def run_docling(pdf_path: Path) -> Tuple[str, float, int]:
    """Run DoclingDocumentExtractor and return (text, seconds, pages_processed=doc pages)."""
    if DoclingDocumentExtractor is None or DoclingConfig is None:
        return "", 0.0, 0
    cfg = DoclingConfig()  # start from env-configured settings
    # For digital PDF baseline, disable OCR to avoid engine requirements
    try:
        cfg.do_ocr = False
        cfg.auto_ocr_detection = False
    except Exception:
        pass
    extractor = DoclingDocumentExtractor(cfg)
    start = time.perf_counter()
    result = extractor.extract(pdf_path)
    seconds = time.perf_counter() - start
    # Use plain text for OCR comparison
    text = result.plain_text or ""
    # Count pages via PyMuPDF quickly
    try:
        with fitz.open(pdf_path) as d:
            pages_processed = len(d)
    except Exception:
        pages_processed = 0
    return text, seconds, pages_processed


def run_tesseract_on_images(images: List["np.ndarray"], langs: str, oem: int, psm: int) -> Tuple[str, float, int, str]:
    """Run Tesseract via tesserocr on list of numpy images."""
    try:
        import tesserocr  # type: ignore
        from PIL import Image  # lazy
    except Exception as e:  # pragma: no cover
        return "", 0.0, 0, f"tesserocr unavailable: {e}"

    # Map OEM/PSM safely
    oem_enum = getattr(tesserocr.OEM, "DEFAULT", 3)
    try:
        oem_enum = tesserocr.OEM(oem)
    except Exception:
        pass
    psm_enum = getattr(tesserocr.PSM, "AUTO", 3)
    try:
        psm_enum = tesserocr.PSM(psm)
    except Exception:
        pass

    text_parts: List[str] = []
    start = time.perf_counter()
    try:
        with tesserocr.PyTessBaseAPI(lang=langs, oem=oem_enum, psm=psm_enum) as api:
            for arr in images:
                img = Image.fromarray(arr)
                api.SetImage(img)
                text_parts.append(api.GetUTF8Text() or "")
        seconds = time.perf_counter() - start
        return "\n".join(text_parts), seconds, len(images), ""
    except Exception as e:  # pragma: no cover
        seconds = time.perf_counter() - start
        return "", seconds, 0, f"tesseract run error: {e}"


def run_paddleocr_on_images(images: List["np.ndarray"], lang: str, use_angle_cls: bool) -> Tuple[str, float, int, str]:
    """Run PaddleOCR on list of numpy images and concatenate recognized text lines."""
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as e:  # pragma: no cover
        return "", 0.0, 0, f"paddleocr unavailable: {e}"

    try:
        # Avoid "show_log" arg for compatibility across versions
        ocr = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang)
    except Exception as e:  # pragma: no cover
        return "", 0.0, 0, f"paddle init error: {e}"

    text_lines: List[str] = []
    start = time.perf_counter()
    try:
        for arr in images:
            # PaddleOCR expects BGR or file path; convert RGB->BGR
            bgr = arr[:, :, ::-1]
            result = ocr.ocr(bgr, cls=use_angle_cls)
            # result is list per image; each item is [ [bbox, (text, conf)], ... ]
            if result and result[0]:
                for item in result[0]:
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        _, rec = item
                        if isinstance(rec, (list, tuple)) and rec:
                            text_lines.append(str(rec[0]))
        seconds = time.perf_counter() - start
        return "\n".join(text_lines), seconds, len(images), ""
    except Exception as e:  # pragma: no cover
        seconds = time.perf_counter() - start
        return "", seconds, 0, f"paddle run error: {e}"


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def save_text(output_root: Path, engine: str, doc_name: str, text: str) -> None:
    safe_engine = engine.replace("/", "_")
    out_dir = output_root / "texts" / safe_engine
    ensure_dir(out_dir)
    out_file = out_dir / f"{doc_name}.txt"
    out_file.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="OCR Engine War - speed + text length comparison")
    parser.add_argument("--input-dir", type=Path, default=Path("sample_pdf"), help="Directory with PDFs/images")
    parser.add_argument("--output-dir", type=Path, default=Path("test_results/ocr_engine_war_2025-10-03"), help="Output directory")
    parser.add_argument("--engines", nargs="+", default=["docling", "tesseract", "paddleocr"], help="Engines to run")
    parser.add_argument("--page-limit", type=int, default=int(os.getenv("OCR_ENGINE_PAGE_LIMIT", "2")), help="Max pages per PDF")
    parser.add_argument("--dpi", type=int, default=int(os.getenv("OCR_ENGINE_DPI", "300")), help="Rasterization DPI for OCR engines")
    args = parser.parse_args()

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    engines: List[str] = [e.lower() for e in args.engines]
    page_limit: Optional[int] = args.page_limit
    dpi: int = args.dpi

    ensure_dir(output_dir)
    (output_dir / "texts").mkdir(exist_ok=True)
    summary_csv = output_dir / "summary.csv"

    files = list_input_files(input_dir)
    if not files:
        print(f"No input files found in {input_dir}")
        return 0

    # Engine config from env
    tesseract_langs = os.getenv("TESSERACT_LANGS", "eng")
    tesseract_oem = int(os.getenv("TESSERACT_OEM", "1"))  # LSTM-only
    tesseract_psm = int(os.getenv("TESSERACT_PSM", "6"))  # Assume block of text

    paddle_lang = os.getenv("PADDLEOCR_LANG", "en")
    paddle_use_angle_cls = os.getenv("PADDLEOCR_USE_ANGLE_CLS", "true").lower() in ("1", "true", "yes", "on")

    rows: List[OCREntry] = []

    for path in files:
        doc_name = path.name
        # PDF: render pages once for image-based engines
        images: List["np.ndarray"] = []
        if path.suffix.lower() == ".pdf":
            try:
                images = render_pdf_to_images(path, dpi=dpi, page_limit=page_limit)
            except Exception as e:
                images = []
                print(f"[warn] Failed to render {doc_name}: {e}")
        else:
            # Single image file
            try:
                if np is None:
                    raise RuntimeError("numpy not available")
                import cv2  # type: ignore
                img = cv2.imread(str(path))
                if img is not None:
                    images = [img[:, :, ::-1]]  # BGR->RGB
            except Exception:
                images = []

        # Run engines
        if "docling" in engines and path.suffix.lower() == ".pdf":
            text, seconds, pages = run_docling(path)
            rows.append(OCREntry(document=doc_name, engine="docling", seconds=seconds, pages_processed=pages, text_length=len(text)))
            save_text(output_dir, "docling", doc_name, text)

        if "tesseract" in engines and images:
            text, seconds, pages, note = run_tesseract_on_images(images, tesseract_langs, tesseract_oem, tesseract_psm)
            rows.append(OCREntry(document=doc_name, engine="tesseract", seconds=seconds, pages_processed=pages, text_length=len(text), notes=note))
            if text:
                save_text(output_dir, "tesseract", doc_name, text)

        if "paddleocr" in engines and images:
            text, seconds, pages, note = run_paddleocr_on_images(images, paddle_lang, paddle_use_angle_cls)
            rows.append(OCREntry(document=doc_name, engine="paddleocr", seconds=seconds, pages_processed=pages, text_length=len(text), notes=note))
            if text:
                save_text(output_dir, "paddleocr", doc_name, text)

    # Write summary CSV
    df = pd.DataFrame([asdict(r) for r in rows])
    df.to_csv(summary_csv, index=False)
    print(f"✅ Wrote summary: {summary_csv}")
    print(f"✅ Text outputs under: {output_dir / 'texts'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
