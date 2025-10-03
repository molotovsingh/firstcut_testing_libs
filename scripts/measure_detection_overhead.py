#!/usr/bin/env python3
"""
Measure PyMuPDF detection overhead
"""
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.docling_adapter import is_scanned_pdf

def measure_detection():
    """Measure detection overhead on digital and potentially scanned PDFs"""

    test_files = [
        Path("sample_pdf/famas_dispute/Answer to Request for Arbitration.pdf"),
        Path("sample_pdf/amrapali_case/Amrapali Allotment Letter.pdf"),
    ]

    print("=" * 80)
    print("Measuring PyMuPDF Detection Overhead")
    print("=" * 80)
    print()

    for pdf_path in test_files:
        if not pdf_path.exists():
            print(f"⚠️  Skipping {pdf_path.name} (not found)")
            continue

        file_size_mb = pdf_path.stat().st_size / 1024 / 1024

        # Run detection 5 times to get average
        times = []
        results = []

        for i in range(5):
            start = time.perf_counter()
            is_scanned = is_scanned_pdf(pdf_path)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            results.append(is_scanned)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"📄 {pdf_path.name}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"   Detection result: {'SCANNED' if results[0] else 'DIGITAL'}")
        print(f"   Average time: {avg_time*1000:.1f} ms")
        print(f"   Min time: {min_time*1000:.1f} ms")
        print(f"   Max time: {max_time*1000:.1f} ms")
        print()

if __name__ == "__main__":
    measure_detection()
