#!/usr/bin/env python3
"""Quick provider test using pre-extracted text"""
import os
import sys
from pathlib import Path
import time
import pandas as pd
from dataclasses import asdict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from src.core.config import load_provider_config
from src.core.extractor_factory import build_extractors

# Pre-extracted text (from Docling run)
test_text = """<< Will use actual text from file >>"""

def test_provider(provider_name: str, text: str):
    print(f"\n{'='*60}")
    print(f"Testing: {provider_name.upper()}")
    print(f"{'='*60}")

    try:
        start = time.perf_counter()

        # Load config and build extractor
        _, event_config, _ = load_provider_config(provider_name)

        # Get the extractor class directly
        if provider_name == "openai":
            from src.core.openai_adapter import OpenAIEventExtractor
            extractor = OpenAIEventExtractor(event_config)
        elif provider_name == "anthropic":
            from src.core.anthropic_adapter import AnthropicEventExtractor
            extractor = AnthropicEventExtractor(event_config)
        else:
            print(f"Unknown provider: {provider_name}")
            return None

        if not extractor.is_available():
            print(f"⚠️  Provider not configured")
            return None

        # Extract events
        events = extractor.extract_events(text, {"filename": "Amrapali Builder Buyer Agreement.pdf"})

        elapsed = time.perf_counter() - start

        print(f"✅ {len(events)} events in {elapsed:.2f}s")

        if events:
            df = pd.DataFrame([asdict(e) for e in events])
            output_file = PROJECT_ROOT / "test_results" / "manual_comparison_2025-10-03" / f"{provider_name}_events.csv"
            df.to_csv(output_file, index=False)
            print(f"📁 Saved to {output_file.name}")

        return {
            "provider": provider_name,
            "events_count": len(events),
            "time": round(elapsed, 2),
            "cost": round(extractor._total_cost, 4) if hasattr(extractor, '_total_cost') else 0
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Read pre-extracted text
    text_file = PROJECT_ROOT / "test_results" / "manual_comparison_2025-10-03" / "extracted_text.txt"

    if not text_file.exists():
        print("Creating extracted text file...")
        # Extract once with Docling
        from src.core.config import DoclingConfig
        from src.core.docling_adapter import DoclingDocumentExtractor

        test_pdf = PROJECT_ROOT / "sample_pdf" / "amrapali_case" / "Amrapali Builder Buyer Agreement.pdf"
        extractor = DoclingDocumentExtractor(DoclingConfig())
        doc = extractor.extract(test_pdf)

        text_file.write_text(doc.plain_text)
        print(f"✅ Saved text to {text_file}")
        text = doc.plain_text
    else:
        text = text_file.read_text()
        print(f"✅ Loaded text from {text_file} ({len(text)} chars)")

    # Test remaining providers
    providers = ["openai", "anthropic"]
    results = []

    for provider in providers:
        result = test_provider(provider, text)
        if result:
            results.append(result)

    # Print summary
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}\n")
    for r in results:
        print(f"{r['provider']:<15} | {r['events_count']:>3} events | {r['time']:>6.2f}s | ${r['cost']:.4f}")
