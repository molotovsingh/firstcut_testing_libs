#!/usr/bin/env python3
"""
Phase 2 Manual Quality Evaluation - Automated Benchmark Runner
Processes test document with all 6 providers, captures timing/cost/output for comparison
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.core.extractor_factory import create_default_extractors
from src.core.interfaces import EventRecord

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise from dependencies
logging.getLogger('langextract').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


class BenchmarkRunner:
    """Automated benchmark runner for Phase 2 evaluation"""

    def __init__(self, test_doc_path: Path, output_dir: Path):
        self.test_doc_path = test_doc_path
        self.output_dir = output_dir
        self.results = []

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_with_provider(self, provider_name: str) -> Dict[str, Any]:
        """Process document with a single provider and capture metrics"""

        logger.info(f"\n{'='*70}")
        logger.info(f"Processing with provider: {provider_name}")
        logger.info(f"{'='*70}\n")

        result = {
            "provider": provider_name,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "timing": {},
            "cost": {},
            "events": [],
            "event_count": 0
        }

        try:
            # Create extractors for this provider
            start_total = time.time()

            logger.info(f"📦 Creating extractors for {provider_name}...")
            doc_extractor, event_extractor = create_default_extractors(
                event_extractor_override=provider_name
            )

            # Check availability
            if not event_extractor.is_available():
                result["error"] = f"{provider_name} extractor not available (missing API key?)"
                logger.error(f"❌ {result['error']}")
                return result

            # Extract document text
            logger.info(f"📄 Extracting document text with Docling...")
            start_doc = time.time()

            extracted_doc = doc_extractor.extract(self.test_doc_path)

            doc_time = time.time() - start_doc
            result["timing"]["document_extraction"] = round(doc_time, 2)
            logger.info(f"   ✅ Document extracted in {doc_time:.2f}s")
            logger.info(f"   Text length: {len(extracted_doc.plain_text)} chars")

            # Extract events
            logger.info(f"🔍 Extracting legal events with {provider_name}...")
            start_events = time.time()

            events = event_extractor.extract_events(
                extracted_doc.plain_text,
                {"document_name": self.test_doc_path.name}
            )

            events_time = time.time() - start_events
            result["timing"]["event_extraction"] = round(events_time, 2)
            result["timing"]["total"] = round(time.time() - start_total, 2)

            logger.info(f"   ✅ Events extracted in {events_time:.2f}s")
            logger.info(f"   Events found: {len(events)}")

            # Get stats if available
            if hasattr(event_extractor, 'get_stats'):
                stats = event_extractor.get_stats()
                result["cost"]["total_tokens"] = stats.get("total_tokens", 0)
                result["cost"]["total_cost"] = stats.get("total_cost", 0.0)
                result["cost"]["model"] = stats.get("model", "unknown")

                logger.info(f"   💰 Cost: ${result['cost']['total_cost']:.4f}")
                logger.info(f"   🎫 Tokens: {result['cost']['total_tokens']}")

            # Convert events to serializable format
            result["events"] = [
                {
                    "number": e.number,
                    "date": e.date,
                    "event_particulars": e.event_particulars,
                    "citation": e.citation,
                    "document_reference": e.document_reference
                }
                for e in events
            ]
            result["event_count"] = len(events)
            result["success"] = True

            logger.info(f"\n✅ {provider_name} completed successfully!")
            logger.info(f"   Total time: {result['timing']['total']}s")
            logger.info(f"   Events: {result['event_count']}")
            logger.info(f"   Cost: ${result['cost'].get('total_cost', 0):.4f}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Error processing with {provider_name}: {e}")
            import traceback
            logger.debug(traceback.format_exc())

        return result

    def run_all_providers(self, providers: List[str]) -> List[Dict[str, Any]]:
        """Process document with all providers"""

        logger.info(f"\n🚀 Starting Phase 2 Benchmark")
        logger.info(f"   Test document: {self.test_doc_path.name}")
        logger.info(f"   Providers: {', '.join(providers)}")
        logger.info(f"   Output directory: {self.output_dir}")
        logger.info("")

        results = []
        for provider in providers:
            result = self.process_with_provider(provider)
            results.append(result)

            # Small delay between providers to avoid rate limiting
            if provider != providers[-1]:  # Not last provider
                logger.info(f"\n⏸️  Waiting 2 seconds before next provider...\n")
                time.sleep(2)

        return results

    def save_results(self, results: List[Dict[str, Any]]):
        """Save results in multiple formats"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw JSON
        json_path = self.output_dir / f"benchmark_results_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\n💾 Saved raw results: {json_path}")

        # Save summary CSV
        summary_data = []
        for r in results:
            summary_data.append({
                "Provider": r["provider"],
                "Success": r["success"],
                "Events": r["event_count"],
                "Doc Time (s)": r["timing"].get("document_extraction", 0),
                "Event Time (s)": r["timing"].get("event_extraction", 0),
                "Total Time (s)": r["timing"].get("total", 0),
                "Tokens": r["cost"].get("total_tokens", 0),
                "Cost ($)": r["cost"].get("total_cost", 0),
                "Model": r["cost"].get("model", "unknown"),
                "Error": r["error"] or ""
            })

        summary_df = pd.DataFrame(summary_data)
        summary_path = self.output_dir / f"benchmark_summary_{timestamp}.csv"
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"💾 Saved summary CSV: {summary_path}")

        # Save individual provider Excel files with events
        for r in results:
            if r["success"] and r["events"]:
                provider = r["provider"]
                events_df = pd.DataFrame(r["events"])

                # Reorder columns to match five-column standard
                events_df = events_df[["number", "date", "event_particulars", "citation", "document_reference"]]
                events_df.columns = ["No", "Date", "Event Particulars", "Citation", "Document Reference"]

                excel_path = self.output_dir / f"{provider}_events_{timestamp}.xlsx"
                events_df.to_excel(excel_path, index=False, sheet_name="Legal Events")
                logger.info(f"💾 Saved {provider} events: {excel_path}")

        # Print summary table
        logger.info(f"\n{'='*70}")
        logger.info("📊 BENCHMARK SUMMARY")
        logger.info(f"{'='*70}\n")
        print(summary_df.to_string(index=False))
        logger.info("")

        # Identify quick champions (preliminary)
        successful = [r for r in results if r["success"]]
        if successful:
            logger.info(f"\n🏆 PRELIMINARY CHAMPIONS (before manual review):\n")

            # Quality = most events extracted (rough proxy)
            quality_champion = max(successful, key=lambda x: x["event_count"])
            logger.info(f"   📈 Most Events: {quality_champion['provider']} ({quality_champion['event_count']} events)")

            # Cost champion
            with_cost = [r for r in successful if r["cost"].get("total_cost", 0) > 0]
            if with_cost:
                cost_champion = min(with_cost, key=lambda x: x["cost"]["total_cost"])
                logger.info(f"   💰 Lowest Cost: {cost_champion['provider']} (${cost_champion['cost']['total_cost']:.4f})")

            # Speed champion
            speed_champion = min(successful, key=lambda x: x["timing"]["total"])
            logger.info(f"   ⚡ Fastest: {speed_champion['provider']} ({speed_champion['timing']['total']}s)")

        logger.info(f"\n{'='*70}")
        logger.info("✅ Benchmark complete! Next step: Manual quality review")
        logger.info(f"{'='*70}\n")


def main():
    """Main entry point"""

    # Configuration
    test_doc = Path("config/benchmarks/test_document.pdf")
    output_dir = Path("config/benchmarks/results")

    providers = [
        "langextract",
        "openrouter",
        "opencode_zen",
        "openai",
        "anthropic",
        "deepseek"
    ]

    # Verify test document exists
    if not test_doc.exists():
        logger.error(f"❌ Test document not found: {test_doc}")
        logger.error("   Run setup first to copy test document")
        sys.exit(1)

    # Run benchmark
    runner = BenchmarkRunner(test_doc, output_dir)
    results = runner.run_all_providers(providers)
    runner.save_results(results)

    # Exit code based on success
    failed = [r for r in results if not r["success"]]
    if failed:
        logger.warning(f"\n⚠️  {len(failed)} provider(s) failed - check errors above")
        sys.exit(1)
    else:
        logger.info(f"\n✅ All {len(results)} providers completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
