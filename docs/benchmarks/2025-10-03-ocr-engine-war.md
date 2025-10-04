# OCR Engine War – 2025-10-03

This benchmark compares OCR engines for speed and text yield on a shared set of PDF pages. It is designed to be simple, reproducible, and safe (no network calls).

Engines included:
- Docling (pipeline baseline; auto OCR when needed)
- Tesseract (tesserocr)
- PaddleOCR (PP-OCR)

Scope and goals:
- Measure latency per document and pages processed
- Compare rough text yield (character count) as a proxy for recall
- Produce per-engine text files for spot QC

Important: This is an OCR-only benchmark. It does not score semantic correctness, layout fidelity, or downstream extraction quality. Use the golden dataset process to measure CER/WER and extraction fidelity.

## How to run

```bash
# Ensure dependencies installed (see pyproject.toml)
# Tesseract requires native install + TESSDATA_PREFIX configured.

uv run python scripts/ocr_engine_war.py \
  --input-dir sample_pdf \
  --output-dir test_results/ocr_engine_war_2025-10-03 \
  --engines docling tesseract paddleocr \
  --page-limit 2 --dpi 300
```

Outputs:
- Summary CSV: `test_results/ocr_engine_war_2025-10-03/summary.csv`
- Extracted text: `test_results/ocr_engine_war_2025-10-03/texts/{engine}/{doc}.txt`

Environment variables (optional):
```bash
# Rasterization and page budget
export OCR_ENGINE_DPI=300
export OCR_ENGINE_PAGE_LIMIT=2

# Tesseract runtime
export TESSERACT_LANGS=eng
export TESSERACT_OEM=1      # LSTM-only
export TESSERACT_PSM=6      # Assume a block of text
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata  # adjust per OS

# PaddleOCR
export PADDLEOCR_LANG=en
export PADDLEOCR_USE_ANGLE_CLS=true
```

## Reading the results

- `seconds`: wall-clock runtime per engine and document
- `pages_processed`: number of rasterized pages processed (image engines)
- `text_length`: characters in concatenated text (coarse recall proxy)
- `notes`: any engine initialization/runtime issues

Interpretation guidance:
- Larger `text_length` generally implies better recall on scanned pages, but may also reflect duplicated headers/footers. Manual spot-checks recommended.
- Docling often dominates total time when OCR is triggered; for pure OCR speed, compare image engines (Tesseract, PaddleOCR).
- For digital PDFs, OCR engines should be skipped; Docling may obtain text from the embedded text layer.

## Known limitations

- Requires native Tesseract install for `tesserocr` to function
- Uses character count as a coarse proxy for recall; use a golden dataset for CER/WER
- Does not evaluate layout structure or tables
- Page limit defaults to 2 for quick runs; increase for thorough tests

## Next steps

- Add CER/WER evaluation against a small golden set (see `docs/datasets/` plan)
- Include RapidOCR or ABBYY (if licensing available) for broader comparison
- Report p50/p95 latency and per-page throughput across larger batches

