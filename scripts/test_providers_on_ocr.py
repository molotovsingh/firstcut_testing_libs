#!/usr/bin/env python3
"""Test all 5 providers on OCR-extracted scanned PDF"""
import os
import sys
from pathlib import Path
import time
import pandas as pd
import json
from dataclasses import asdict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from src.core.config import load_provider_config

def test_provider(provider_name: str, text: str, output_dir: Path):
    """Test a single provider on OCR-extracted text"""
    print(f"\n{'='*70}")
    print(f"Testing: {provider_name.upper()}")
    print(f"{'='*70}")

    try:
        start = time.perf_counter()

        # Load config
        _, event_config, _ = load_provider_config(provider_name)

        # Create extractor
        if provider_name == "langextract":
            from src.core.langextract_adapter import LangExtractEventExtractor
            extractor = LangExtractEventExtractor(event_config)
        elif provider_name == "openrouter":
            from src.core.openrouter_adapter import OpenRouterEventExtractor
            extractor = OpenRouterEventExtractor(event_config)
        elif provider_name == "opencode_zen":
            from src.core.opencode_zen_adapter import OpenCodeZenEventExtractor
            extractor = OpenCodeZenEventExtractor(event_config)
        elif provider_name == "openai":
            from src.core.openai_adapter import OpenAIEventExtractor
            extractor = OpenAIEventExtractor(event_config)
        elif provider_name == "anthropic":
            from src.core.anthropic_adapter import AnthropicEventExtractor
            extractor = AnthropicEventExtractor(event_config)
        else:
            print(f"❌ Unknown provider: {provider_name}")
            return None

        if not extractor.is_available():
            print(f"⚠️  Provider not configured (missing API key)")
            return {
                "provider": provider_name,
                "status": "not_configured",
                "events_count": 0,
                "time": 0,
                "cost": 0
            }

        # Extract events
        events = extractor.extract_events(text, {"filename": "Transaction_Fee_Invoice.pdf"})

        elapsed = time.perf_counter() - start

        # Display results
        print(f"✅ {len(events)} events extracted in {elapsed:.2f}s")

        if hasattr(extractor, '_total_cost'):
            cost = extractor._total_cost
            print(f"💰 Cost: ${cost:.4f}")
        else:
            cost = 0

        # Save events
        if events:
            df = pd.DataFrame([asdict(e) for e in events])
            output_file = output_dir / f"{provider_name}_ocr_events.csv"
            df.to_csv(output_file, index=False)
            print(f"📁 Saved to {output_file.name}")

            # Display sample
            print(f"\n[Sample Event]")
            first = events[0]
            print(f"Date: {first.date}")
            print(f"Particulars: {first.event_particulars[:150]}...")
            print(f"Citation: {first.citation}")

        return {
            "provider": provider_name,
            "status": "success",
            "events_count": len(events),
            "time": round(elapsed, 2),
            "cost": round(cost, 4) if cost > 0 else 0,
            "tokens": extractor._total_tokens if hasattr(extractor, '_total_tokens') else 0
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "provider": provider_name,
            "status": "error",
            "error": str(e),
            "events_count": 0,
            "time": 0,
            "cost": 0
        }

def main():
    # Load OCR-extracted text
    results_dir = PROJECT_ROOT / "test_results" / "ocr_comparison_2025-10-03"
    text_file = results_dir / "scanned_extracted_text.txt"

    if not text_file.exists():
        print(f"❌ OCR-extracted text not found: {text_file}")
        print("Run: uv run python scripts/extract_scanned_pdf.py first")
        return

    text = text_file.read_text()

    print(f"\n{'='*70}")
    print(f"5-PROVIDER OCR COMPARISON TEST")
    print(f"{'='*70}")
    print(f"Document: Transaction_Fee_Invoice.pdf (scanned)")
    print(f"OCR Text: {len(text)} chars")
    print(f"Providers: LangExtract, OpenRouter, OpenAI, Anthropic, OpenCode Zen")
    print(f"{'='*70}\n")

    # Test all providers
    providers = ["langextract", "openrouter", "openai", "anthropic", "opencode_zen"]
    results = []

    for provider in providers:
        result = test_provider(provider, text, results_dir)
        if result:
            results.append(result)

    # Save summary
    summary = {
        "test_type": "ocr_scanned_pdf",
        "document": "Transaction_Fee_Invoice.pdf",
        "ocr_text_length": len(text),
        "ocr_processing_time": 41.17,  # From extraction step
        "providers_tested": providers,
        "results": results
    }

    summary_file = results_dir / "ocr_comparison_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary table
    print(f"\n{'='*70}")
    print(f"OCR COMPARISON RESULTS")
    print(f"{'='*70}\n")

    print(f"{'Provider':<15} | {'Status':<12} | {'Events':>7} | {'Time':>8} | {'Cost':>10}")
    print("-" * 70)

    for r in results:
        status = r['status']
        events = r.get('events_count', 0)
        time_val = f"{r.get('time', 0):.2f}s"
        cost = f"${r.get('cost', 0):.4f}" if r.get('cost', 0) > 0 else "N/A"
        print(f"{r['provider']:<15} | {status:<12} | {events:>7} | {time_val:>8} | {cost:>10}")

    print(f"\n{'='*70}")
    print(f"Summary saved to: {summary_file}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
