#!/usr/bin/env python3
"""
Performance Timing Validation Script
Tests timing instrumentation with real PDFs and generates validation report
"""

import sys
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.legal_pipeline_refactored import LegalEventsPipeline
from src.utils.file_handler import FileHandler

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_timing_with_pdf(pdf_path: str, provider: str = "langextract"):
    """Test timing instrumentation with a specific PDF"""

    # Create pipeline
    pipeline = LegalEventsPipeline(event_extractor=provider)

    # Create mock uploaded file object
    class MockUploadedFile:
        def __init__(self, path):
            self.name = Path(path).name
            with open(path, 'rb') as f:
                self.file_content = f.read()

        def read(self):
            return self.file_content

        def seek(self, pos):
            pass

    mock_file = MockUploadedFile(pdf_path)

    # Process document
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {mock_file.name}")
    logger.info(f"Provider: {provider}")
    logger.info(f"{'='*60}")

    df, warning = pipeline.process_documents_for_legal_events([mock_file])

    # Check for timing columns
    has_timing = all(col in df.columns for col in ["Docling_Seconds", "Extractor_Seconds", "Total_Seconds"])

    results = {
        "document": mock_file.name,
        "provider": provider,
        "events_count": len(df),
        "has_timing": has_timing
    }

    if has_timing:
        results["avg_docling_seconds"] = df["Docling_Seconds"].mean()
        results["avg_extractor_seconds"] = df["Extractor_Seconds"].mean()
        results["avg_total_seconds"] = df["Total_Seconds"].mean()

        logger.info(f"\n⏱️  Timing Results:")
        logger.info(f"   Docling: {results['avg_docling_seconds']:.3f}s")
        logger.info(f"   Extractor: {results['avg_extractor_seconds']:.3f}s")
        logger.info(f"   Total: {results['avg_total_seconds']:.3f}s")
    else:
        logger.warning(f"⚠️  No timing columns found!")

    logger.info(f"\n✅ Extracted {results['events_count']} events")

    # Display first few rows
    logger.info(f"\n📊 Sample Data (first 3 rows):")
    print(df.head(3).to_string(index=False))

    return results, df


def main():
    """Run validation tests"""

    logger.info("=" * 60)
    logger.info("Performance Timing Validation")
    logger.info("=" * 60)

    # Check if timing is enabled
    timing_enabled = os.getenv("ENABLE_PERFORMANCE_TIMING", "true").lower() == "true"
    logger.info(f"\nENABLE_PERFORMANCE_TIMING: {timing_enabled}")

    if not timing_enabled:
        logger.warning("⚠️  Timing is DISABLED. Set ENABLE_PERFORMANCE_TIMING=true in .env")
        return

    # Test with sample PDFs
    test_pdfs = [
        ("sample_pdf/famas_dispute/Answer to Request for Arbitration.pdf", "Small PDF (~15 pages)"),
        ("sample_pdf/amrapali_case/Amrapali Allotment Letter.pdf", "Medium PDF"),
    ]

    all_results = []
    all_dataframes = []

    for pdf_path, description in test_pdfs:
        full_path = Path(__file__).parent.parent / pdf_path

        if not full_path.exists():
            logger.warning(f"⚠️  Skipping {pdf_path} - file not found")
            continue

        try:
            results, df = test_timing_with_pdf(str(full_path))
            all_results.append(results)
            all_dataframes.append(df)
        except Exception as e:
            logger.error(f"❌ Error testing {pdf_path}: {e}")
            import traceback
            traceback.print_exc()

    # Generate summary
    logger.info(f"\n{'='*60}")
    logger.info("VALIDATION SUMMARY")
    logger.info(f"{'='*60}\n")

    summary_df = pd.DataFrame(all_results)
    print(summary_df.to_string(index=False))

    # Save results
    output_dir = Path(__file__).parent.parent / "docs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save detailed CSV
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        csv_path = output_dir / "timing_validation_detailed.csv"
        combined_df.to_csv(csv_path, index=False)
        logger.info(f"\n💾 Saved detailed results: {csv_path}")

    # Save summary
    summary_path = output_dir / "timing_validation_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"💾 Saved summary: {summary_path}")

    logger.info(f"\n✅ Validation complete!")


if __name__ == "__main__":
    main()
