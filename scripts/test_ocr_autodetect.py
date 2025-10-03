#!/usr/bin/env python3
"""
Test OCR auto-detection with digital PDF
Verifies: fast path (~2-3s), no OCR processor created, correct metadata
"""
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import DoclingConfig
from src.core.docling_adapter import DoclingDocumentExtractor

def test_digital_pdf():
    """Test digital PDF processing with auto-detection enabled"""

    # Use known digital PDF from benchmarks
    test_pdf = Path("sample_pdf/famas_dispute/Answer to Request for Arbitration.pdf")

    if not test_pdf.exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        return

    print("=" * 80)
    print("Testing OCR Auto-Detection with Digital PDF")
    print("=" * 80)
    print(f"📄 Test file: {test_pdf.name}")
    print(f"📊 File size: {test_pdf.stat().st_size / 1024 / 1024:.1f} MB")
    print()

    # Create config with OCR disabled but auto-detection enabled
    config = DoclingConfig(
        do_ocr=False,  # OCR disabled by default
        auto_ocr_detection=True,  # But auto-detection enabled
        table_mode="FAST"
    )

    print("⚙️  Configuration:")
    print(f"   - DOCLING_DO_OCR: {config.do_ocr}")
    print(f"   - DOCLING_AUTO_OCR_DETECTION: {config.auto_ocr_detection}")
    print(f"   - DOCLING_TABLE_MODE: {config.table_mode}")
    print()

    # Create extractor
    print("🔧 Creating DoclingDocumentExtractor...")
    extractor = DoclingDocumentExtractor(config)
    print()

    # Time the extraction
    print("⏱️  Starting extraction (expecting ~2-3s for digital PDF)...")
    start_time = time.perf_counter()

    result = extractor.extract(test_pdf)

    elapsed = time.perf_counter() - start_time

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"⏱️  Processing time: {elapsed:.2f}s")
    print()

    # Check metadata
    metadata = result.metadata
    print("📊 Metadata:")
    print(f"   - extraction_method: {metadata.get('extraction_method')}")
    print(f"   - needs_ocr: {metadata.get('needs_ocr')}")
    print(f"   - ocr_auto_detected: {metadata.get('ocr_auto_detected')}")
    print(f"   - config.do_ocr: {metadata.get('config', {}).get('do_ocr')}")
    print()

    # Check text extraction
    text_length = len(result.plain_text)
    print(f"📝 Extracted text length: {text_length:,} characters")
    print(f"   First 200 chars: {result.plain_text[:200]!r}...")
    print()

    # Verify expectations
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    checks = []

    # Check 1: Fast processing time (< 5s for digital PDF)
    if elapsed < 5.0:
        checks.append(("✅", f"Processing time {elapsed:.2f}s < 5s (fast path)"))
    else:
        checks.append(("❌", f"Processing time {elapsed:.2f}s >= 5s (expected < 5s)"))

    # Check 2: OCR not auto-detected for digital PDF
    if not metadata.get('ocr_auto_detected', False):
        checks.append(("✅", "OCR not auto-detected (correct for digital PDF)"))
    else:
        checks.append(("❌", "OCR auto-detected (should not happen for digital PDF)"))

    # Check 3: needs_ocr should be False
    if not metadata.get('needs_ocr', True):
        checks.append(("✅", "needs_ocr=False (correct)"))
    else:
        checks.append(("❌", "needs_ocr=True (should be False for digital PDF)"))

    # Check 4: Text extracted successfully
    if text_length > 1000:
        checks.append(("✅", f"Text extracted successfully ({text_length:,} chars)"))
    else:
        checks.append(("❌", f"Text extraction may have failed ({text_length:,} chars)"))

    # Check 5: Extraction method is docling
    if metadata.get('extraction_method') == 'docling':
        checks.append(("✅", "Extraction method is 'docling'"))
    else:
        checks.append(("❌", f"Unexpected extraction method: {metadata.get('extraction_method')}"))

    for icon, message in checks:
        print(f"{icon} {message}")

    print()
    print("=" * 80)

    # Check if ocr_processor was created (should not be)
    if hasattr(extractor, 'ocr_processor'):
        if extractor.ocr_processor is None:
            print("✅ OCR processor cache is None (not initialized - correct!)")
        else:
            print("⚠️  OCR processor cache is initialized (unexpected for digital-only test)")

    print()

    # Overall verdict
    passed = all(check[0] == "✅" for check in checks)
    if passed:
        print("🎉 ALL CHECKS PASSED - OCR auto-detection working correctly!")
    else:
        print("❌ SOME CHECKS FAILED - Review results above")

    return passed

if __name__ == "__main__":
    success = test_digital_pdf()
    sys.exit(0 if success else 1)
