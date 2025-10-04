#!/usr/bin/env python3
"""List all PDF files with page counts and sizes"""
import pymupdf
from pathlib import Path

pdf_root = Path("sample_pdf")
pdfs = sorted(pdf_root.rglob("*.pdf"))

print(f"{'Pages':>5} | {'Size (KB)':>9} | Path")
print("-" * 70)

for pdf_path in pdfs:
    try:
        doc = pymupdf.open(pdf_path)
        pages = len(doc)
        size_kb = pdf_path.stat().st_size // 1024
        doc.close()
        print(f"{pages:>5} | {size_kb:>9} | {pdf_path}")
    except Exception as e:
        print(f"ERROR | ERROR | {pdf_path} ({e})")
