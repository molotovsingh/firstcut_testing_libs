#!/usr/bin/env python3
"""
DeepSeek-OCR Testing Script

Tests DeepSeek-OCR document extractor on sample documents and compares
quality to docling baseline.

Requirements:
    - CUDA 11.8+ GPU
    - DeepSeek-OCR environment (see scripts/setup_deepseek_ocr.sh)

Usage:
    # Activate DeepSeek-OCR environment first
    conda activate deepseek-ocr

    # Run full test suite
    python scripts/test_deepseek_ocr.py

    # Quick test (single document)
    python scripts/test_deepseek_ocr.py --quick

    # Compare to docling
    python scripts/test_deepseek_ocr.py --compare
"""

import sys
import time
import argparse
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.deepseek_ocr_adapter import DeepSeekOCRDocumentExtractor
from core.docling_adapter import DoclingDocumentExtractor
from core.config import DoclingConfig


def print_header(title: str):
    """Print formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_result(label: str, value: Any, indent: int = 0):
    """Print formatted result"""
    prefix = "  " * indent
    print(f"{prefix}{label}: {value}")


def test_availability():
    """Test 1: Check if DeepSeek-OCR is available"""
    print_header("Test 1: Availability Check")

    try:
        extractor = DeepSeekOCRDocumentExtractor()
        is_available = extractor.is_available()

        if is_available:
            print("✅ DeepSeek-OCR is available")

            # Print environment details
            import torch
            print_result("CUDA available", torch.cuda.is_available())
            if torch.cuda.is_available():
                print_result("CUDA version", torch.version.cuda)
                print_result("GPU device", torch.cuda.get_device_name(0))
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
                print_result("GPU memory", f"{gpu_mem:.1f} GB")

            return True
        else:
            print("❌ DeepSeek-OCR not available")
            print("\nRequirements:")
            print("  - CUDA 11.8+ GPU")
            print("  - PyTorch 2.6.0+")
            print("  - transformers 4.46.3+")
            print("  - flash-attn 2.7.3")
            print("\nRun: bash scripts/setup_deepseek_ocr.sh")
            return False

    except Exception as e:
        print(f"❌ Availability check failed: {e}")
        return False


def test_single_image(extractor: DeepSeekOCRDocumentExtractor):
    """Test 2: Extract from single image"""
    print_header("Test 2: Single Image Extraction")

    # Find a sample image (we'll create a simple test if none exists)
    sample_files = [
        Path("sample_pdf/famas_dispute/Answer to Request for Arbitration.pdf"),
        Path("sample_pdf/amrapali_case/Amrapali Allotment Letter.pdf"),
        Path("tests/test_documents/sample_legal_brief.pdf"),
    ]

    test_file = None
    for f in sample_files:
        if f.exists():
            test_file = f
            break

    if not test_file:
        print("⚠️  No sample files found, skipping test")
        return

    print(f"📄 Processing: {test_file.name}")
    print(f"   Path: {test_file}")

    try:
        start_time = time.time()
        result = extractor.extract(test_file)
        elapsed = time.time() - start_time

        print(f"\n✅ Extraction completed in {elapsed:.2f}s")
        print_result("Extraction method", result.metadata.get("extraction_method"))
        print_result("Markdown length", len(result.markdown))
        print_result("Plain text length", len(result.plain_text))

        if "pages_processed" in result.metadata:
            print_result("Pages processed", result.metadata["pages_processed"])
            pages = result.metadata["pages_processed"]
            if pages > 0:
                print_result("Time per page", f"{elapsed / pages:.2f}s")

        # Show preview
        print("\n📄 Markdown preview (first 500 chars):")
        print("-" * 80)
        print(result.markdown[:500])
        if len(result.markdown) > 500:
            print("...")
        print("-" * 80)

        return result

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_with_docling(deepseek_extractor: DeepSeekOCRDocumentExtractor):
    """Test 3: Compare DeepSeek-OCR vs Docling"""
    print_header("Test 3: DeepSeek-OCR vs Docling Comparison")

    # Test file
    test_file = Path("sample_pdf/famas_dispute/Answer to Request for Arbitration.pdf")
    if not test_file.exists():
        print(f"⚠️  Test file not found: {test_file}")
        return

    print(f"📄 Test document: {test_file.name}")

    # Create docling extractor
    docling_config = DoclingConfig()
    docling_extractor = DoclingDocumentExtractor(docling_config)

    results = {}

    # Test DeepSeek-OCR
    print("\n🔹 Testing DeepSeek-OCR...")
    try:
        start_time = time.time()
        deepseek_result = deepseek_extractor.extract(test_file)
        deepseek_time = time.time() - start_time

        results['deepseek'] = {
            'success': deepseek_result.metadata.get("extraction_method") == "deepseek_ocr",
            'time': deepseek_time,
            'markdown_len': len(deepseek_result.markdown),
            'text_len': len(deepseek_result.plain_text),
            'method': deepseek_result.metadata.get("extraction_method"),
        }

        print(f"   ✅ Completed in {deepseek_time:.2f}s")
        print(f"   📝 Extracted {len(deepseek_result.markdown)} chars markdown")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['deepseek'] = {'success': False, 'error': str(e)}

    # Test Docling
    print("\n🔹 Testing Docling...")
    try:
        start_time = time.time()
        docling_result = docling_extractor.extract(test_file)
        docling_time = time.time() - start_time

        results['docling'] = {
            'success': docling_result.metadata.get("extraction_method") not in ["failed"],
            'time': docling_time,
            'markdown_len': len(docling_result.markdown),
            'text_len': len(docling_result.plain_text),
            'method': docling_result.metadata.get("extraction_method"),
        }

        print(f"   ✅ Completed in {docling_time:.2f}s")
        print(f"   📝 Extracted {len(docling_result.markdown)} chars markdown")

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['docling'] = {'success': False, 'error': str(e)}

    # Comparison table
    print("\n📊 Comparison Results:")
    print("-" * 80)
    print(f"{'Metric':<30} {'DeepSeek-OCR':<25} {'Docling':<25}")
    print("-" * 80)

    if results['deepseek']['success'] and results['docling']['success']:
        print(f"{'Extraction time':<30} {results['deepseek']['time']:>8.2f}s {'':<16} {results['docling']['time']:>8.2f}s")
        print(f"{'Markdown length':<30} {results['deepseek']['markdown_len']:>8,} chars {'':<8} {results['docling']['markdown_len']:>8,} chars")
        print(f"{'Plain text length':<30} {results['deepseek']['text_len']:>8,} chars {'':<8} {results['docling']['text_len']:>8,} chars")

        # Speed comparison
        speedup = results['docling']['time'] / results['deepseek']['time']
        if speedup > 1:
            print(f"\n⚡ DeepSeek-OCR is {speedup:.1f}x FASTER than Docling")
        else:
            print(f"\n⏱️  Docling is {1/speedup:.1f}x faster than DeepSeek-OCR")

    else:
        print("⚠️  Could not complete comparison (one or both extractors failed)")

    print("-" * 80)

    return results


def run_full_test_suite():
    """Run complete test suite"""
    print_header("DeepSeek-OCR Test Suite")

    # Test 1: Availability
    if not test_availability():
        print("\n❌ DeepSeek-OCR not available, cannot continue testing")
        print("   Run setup script: bash scripts/setup_deepseek_ocr.sh")
        return False

    # Create extractor
    extractor = DeepSeekOCRDocumentExtractor()

    # Test 2: Single extraction
    result = test_single_image(extractor)
    if not result:
        print("\n❌ Single image test failed")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Test DeepSeek-OCR document extractor")
    parser.add_argument("--quick", action="store_true", help="Quick test (availability only)")
    parser.add_argument("--compare", action="store_true", help="Compare with docling")
    args = parser.parse_args()

    try:
        if args.quick:
            # Quick test
            test_availability()

        elif args.compare:
            # Comparison test
            if not test_availability():
                return 1

            extractor = DeepSeekOCRDocumentExtractor()
            compare_with_docling(extractor)

        else:
            # Full test suite
            success = run_full_test_suite()

            if success:
                print("\n" + "=" * 80)
                print("  🎉 All tests passed!")
                print("=" * 80)
                return 0
            else:
                print("\n" + "=" * 80)
                print("  ❌ Some tests failed")
                print("=" * 80)
                return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
