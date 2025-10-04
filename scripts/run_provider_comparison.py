#!/usr/bin/env python3
"""
Run 5-provider comparison on a test document
Captures: events extracted, quality metrics, cost, processing time
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from src.core.config import DoclingConfig, load_provider_config, ExtractorConfig
from src.core.extractor_factory import build_extractors

def run_single_provider(test_file: Path, provider_name: str, output_dir: Path):
    """Run extraction with a single provider and capture results"""
    print(f"\n{'='*70}")
    print(f"Testing Provider: {provider_name.upper()}")
    print(f"{'='*70}")

    start_time = time.perf_counter()

    try:
        # Load configuration
        docling_config, event_config, extractor_config = load_provider_config(provider_name)

        # Build extractors
        doc_extractor, event_extractor = build_extractors(
            docling_config, event_config, extractor_config
        )

        # Check provider availability
        if not event_extractor.is_available():
            print(f"⚠️  Provider {provider_name} not configured (missing API key)")
            return {
                "provider": provider_name,
                "status": "not_configured",
                "error": "Missing API key",
                "processing_time": 0,
                "events_count": 0
            }

        # Extract document
        doc_start = time.perf_counter()
        extracted_doc = doc_extractor.extract(test_file)
        doc_time = time.perf_counter() - doc_start

        # Extract events
        event_start = time.perf_counter()
        events = event_extractor.extract_events(
            extracted_doc.plain_text,
            {"filename": test_file.name}
        )
        event_time = time.perf_counter() - event_start

        total_time = time.perf_counter() - start_time

        # Convert events to dataframe
        if events:
            df = pd.DataFrame([asdict(e) for e in events])

            # Save to CSV
            output_file = output_dir / f"{provider_name}_events.csv"
            df.to_csv(output_file, index=False)
            print(f"✅ Saved {len(events)} events to {output_file.name}")
        else:
            df = pd.DataFrame()
            print(f"⚠️  No events extracted")

        # Capture results
        result = {
            "provider": provider_name,
            "status": "success",
            "processing_time": round(total_time, 2),
            "doc_extraction_time": round(doc_time, 2),
            "event_extraction_time": round(event_time, 2),
            "events_count": len(events),
            "text_length": len(extracted_doc.plain_text),
            "extraction_method": extracted_doc.metadata.get("extraction_method"),
            "needs_ocr": extracted_doc.metadata.get("needs_ocr", False)
        }

        # Add provider-specific metrics if available
        if hasattr(event_extractor, '_total_tokens'):
            result["total_tokens"] = event_extractor._total_tokens
        if hasattr(event_extractor, '_total_cost'):
            result["total_cost"] = round(event_extractor._total_cost, 4)

        print(f"⏱️  Total time: {result['processing_time']}s")
        print(f"📊 Events found: {result['events_count']}")
        if 'total_cost' in result:
            print(f"💰 Cost: ${result['total_cost']:.4f}")

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "provider": provider_name,
            "status": "error",
            "error": str(e),
            "processing_time": time.perf_counter() - start_time,
            "events_count": 0
        }

def main():
    # Configuration
    test_file = PROJECT_ROOT / "sample_pdf" / "amrapali_case" / "Amrapali Builder Buyer Agreement.pdf"
    output_dir = PROJECT_ROOT / "test_results" / "manual_comparison_2025-10-03"
    output_dir.mkdir(parents=True, exist_ok=True)

    providers = ["langextract", "openrouter", "opencode_zen", "openai", "anthropic"]

    print(f"\n{'='*70}")
    print(f"5-PROVIDER COMPARISON TEST")
    print(f"{'='*70}")
    print(f"Test Document: {test_file.name}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output Directory: {output_dir}")
    print(f"Providers: {', '.join(providers)}")
    print(f"{'='*70}\n")

    # Run all providers
    results = []
    for provider in providers:
        result = run_single_provider(test_file, provider, output_dir)
        results.append(result)

    # Save summary
    summary = {
        "test_date": datetime.now().isoformat(),
        "test_document": str(test_file.relative_to(PROJECT_ROOT)),
        "providers_tested": providers,
        "results": results
    }

    summary_file = output_dir / "comparison_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*70}")
    print(f"COMPARISON COMPLETE")
    print(f"{'='*70}")
    print(f"Summary saved to: {summary_file}")

    # Print summary table
    print(f"\n{'='*70}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*70}\n")

    print(f"{'Provider':<15} | {'Status':<15} | {'Time (s)':>10} | {'Events':>8} | {'Cost':>10}")
    print("-" * 70)

    for r in results:
        status = r['status']
        time_str = f"{r['processing_time']:.2f}" if 'processing_time' in r else "N/A"
        events = r.get('events_count', 0)
        cost = f"${r['total_cost']:.4f}" if 'total_cost' in r else "N/A"
        print(f"{r['provider']:<15} | {status:<15} | {time_str:>10} | {events:>8} | {cost:>10}")

    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
