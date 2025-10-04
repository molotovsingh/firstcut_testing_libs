#!/usr/bin/env python3
"""Extract scanned PDF with OCR auto-detection and save text"""
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from src.core.config import DoclingConfig
from src.core.docling_adapter import DoclingDocumentExtractor

def main():
    # Test document
    test_pdf = PROJECT_ROOT / "sample_pdf" / "famas_dispute" / "Transaction_Fee_Invoice.pdf"
    output_dir = PROJECT_ROOT / "test_results" / "ocr_comparison_2025-10-03"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"SCANNED PDF OCR EXTRACTION TEST")
    print(f"{'='*70}")
    print(f"Document: {test_pdf.name}")
    print(f"Size: {test_pdf.stat().st_size // 1024}KB")
    print(f"OCR Auto-Detection: Enabled")
    print(f"{'='*70}\n")

    # Extract with OCR auto-detection
    start_time = time.perf_counter()

    config = DoclingConfig()
    extractor = DoclingDocumentExtractor(config)

    print("🔄 Extracting document (OCR may trigger automatically)...\n")
    extracted = extractor.extract(test_pdf)

    elapsed = time.perf_counter() - start_time

    # Display results
    print(f"\n{'='*70}")
    print(f"EXTRACTION RESULTS")
    print(f"{'='*70}")
    print(f"⏱️  Processing Time: {elapsed:.2f}s")
    print(f"📝 Text Length: {len(extracted.plain_text)} chars")
    print(f"🔍 OCR Detected: {extracted.metadata.get('needs_ocr', False)}")
    print(f"🔧 OCR Auto-Used: {extracted.metadata.get('ocr_auto_detected', False)}")
    print(f"✅ Extraction Method: {extracted.metadata.get('extraction_method')}")
    print(f"{'='*70}\n")

    # Save extracted text
    text_file = output_dir / "scanned_extracted_text.txt"
    text_file.write_text(extracted.plain_text)
    print(f"💾 Saved extracted text to: {text_file}")

    # Save metadata
    import json
    meta_file = output_dir / "extraction_metadata.json"
    with open(meta_file, 'w') as f:
        json.dump({
            "document": str(test_pdf.relative_to(PROJECT_ROOT)),
            "processing_time": round(elapsed, 2),
            "text_length": len(extracted.plain_text),
            "needs_ocr": extracted.metadata.get('needs_ocr', False),
            "ocr_auto_detected": extracted.metadata.get('ocr_auto_detected', False),
            "extraction_method": extracted.metadata.get('extraction_method'),
            "docling_config": {
                "do_ocr": config.do_ocr,
                "auto_ocr_detection": config.auto_ocr_detection,
                "table_mode": config.table_mode
            }
        }, f, indent=2)

    print(f"💾 Saved metadata to: {meta_file}\n")

    # Display text preview
    print(f"{'='*70}")
    print(f"TEXT PREVIEW (first 500 chars)")
    print(f"{'='*70}")
    print(extracted.plain_text[:500])
    if len(extracted.plain_text) > 500:
        print(f"\n... ({len(extracted.plain_text) - 500} more chars)\n")

    print(f"{'='*70}\n")
    print("✅ OCR extraction complete - ready for provider testing\n")

if __name__ == "__main__":
    main()
