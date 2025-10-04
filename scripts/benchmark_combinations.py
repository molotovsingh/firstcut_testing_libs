#!/usr/bin/env python3
"""
Phase 4: Automated Benchmarking with LLM-as-Judge

Processes multiple documents with all providers in parallel,
uses LLM-as-judge to score quality, and generates comprehensive reports.

Success criteria:
- Benchmark 6 providers × 10 documents in <30 minutes
- LLM-as-judge rankings align with Phase 2 findings
- Automated reports are production-quality
- Total cost <$5 per benchmark run
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment FIRST (before imports that need it)
from dotenv import load_dotenv
load_dotenv()

from src.core.extractor_factory import create_default_extractors
from src.core.interfaces import EventRecord
from src.core.llm_judge import LLMJudge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise from dependencies
logging.getLogger('langextract').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


class AutomatedBenchmarkRunner:
    """
    Automated benchmark runner with LLM-as-judge evaluation

    Processes multiple documents with all providers, uses LLM judge
    to score quality, and generates comprehensive reports.
    """

    def __init__(
        self,
        test_set_path: Path,
        output_dir: Path,
        max_workers: int = 3
    ):
        """
        Initialize benchmark runner

        Args:
            test_set_path: Path to test_set_phase4.json
            output_dir: Directory for results
            max_workers: Max parallel providers (default 3 to respect rate limits)
        """
        self.test_set_path = test_set_path
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.results = []

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load test set
        with open(test_set_path) as f:
            self.test_set = json.load(f)

        self.test_docs = self.test_set["test_documents"]
        self.providers = self.test_set["providers_to_test"]

        logger.info(f"Initialized benchmark:")
        logger.info(f"  Test docs: {len(self.test_docs)}")
        logger.info(f"  Providers: {len(self.providers)}")
        logger.info(f"  Max parallel workers: {max_workers}")

    def process_single_provider_document(
        self,
        provider_name: str,
        doc_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process one document with one provider

        Args:
            provider_name: Name of provider (langextract, openai, etc.)
            doc_info: Document metadata from test set

        Returns:
            Dict with provider results for this document
        """
        doc_path = Path(doc_info["path"])
        doc_name = doc_info["filename"]

        result = {
            "provider": provider_name,
            "document": doc_name,
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

            doc_extractor, event_extractor = create_default_extractors(
                event_extractor_override=provider_name
            )

            # Check availability
            if not event_extractor.is_available():
                result["error"] = f"{provider_name} not available (missing API key?)"
                logger.warning(f"⚠️  {provider_name} - {doc_name}: {result['error']}")
                return result

            # Extract document text
            start_doc = time.time()
            extracted_doc = doc_extractor.extract(doc_path)
            doc_time = time.time() - start_doc
            result["timing"]["document_extraction"] = round(doc_time, 2)

            # Extract events
            start_events = time.time()
            events = event_extractor.extract_events(
                extracted_doc.plain_text,
                {"document_name": doc_name}
            )
            events_time = time.time() - start_events
            result["timing"]["event_extraction"] = round(events_time, 2)
            result["timing"]["total"] = round(time.time() - start_total, 2)

            # Get stats if available
            if hasattr(event_extractor, 'get_stats'):
                stats = event_extractor.get_stats()
                result["cost"]["total_tokens"] = stats.get("total_tokens", 0)
                result["cost"]["total_cost"] = stats.get("total_cost", 0.0)
                result["cost"]["model"] = stats.get("model", "unknown")

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

            logger.info(f"✅ {provider_name:15s} - {doc_name:50s} - {result['event_count']:2d} events, {result['timing']['total']:5.1f}s")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ {provider_name:15s} - {doc_name:50s} - ERROR: {e}")

        return result

    def process_document_with_all_providers(
        self,
        doc_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Process one document with all providers in parallel

        Args:
            doc_info: Document metadata from test set

        Returns:
            List of results, one per provider
        """
        doc_name = doc_info["filename"]
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing document: {doc_name}")
        logger.info(f"{'='*70}")

        results = []

        # Process providers in parallel (with rate limiting)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.process_single_provider_document,
                    provider,
                    doc_info
                ): provider
                for provider in self.providers
            }

            for future in as_completed(futures):
                provider = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Exception processing {provider} on {doc_name}: {e}")
                    results.append({
                        "provider": provider,
                        "document": doc_name,
                        "success": False,
                        "error": str(e),
                        "events": [],
                        "event_count": 0
                    })

        return results

    def run_all_documents(self) -> List[Dict[str, Any]]:
        """
        Process all documents with all providers

        Returns:
            List of all results (providers × documents)
        """
        logger.info("\n🚀 Starting Phase 4 Automated Benchmark")
        logger.info(f"   Total extractions: {len(self.test_docs)} docs × {len(self.providers)} providers = {len(self.test_docs) * len(self.providers)}")
        logger.info("")

        all_results = []
        start_time = time.time()

        for i, doc_info in enumerate(self.test_docs, 1):
            logger.info(f"\n📄 Document {i}/{len(self.test_docs)}")

            # Process this document with all providers
            doc_results = self.process_document_with_all_providers(doc_info)
            all_results.extend(doc_results)

            # Small delay between documents to avoid overwhelming APIs
            if i < len(self.test_docs):
                logger.info(f"\n⏸️  Waiting 2 seconds before next document...")
                time.sleep(2)

        total_time = time.time() - start_time

        logger.info(f"\n{'='*70}")
        logger.info(f"Extraction complete!")
        logger.info(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        logger.info(f"  Successful: {sum(1 for r in all_results if r['success'])}/{len(all_results)}")
        logger.info(f"{'='*70}")

        return all_results

    def format_for_judge(
        self,
        extraction_results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Format extraction results for LLM judge

        Args:
            extraction_results: List of extraction results

        Returns:
            Dict formatted for judge: {doc_name: {provider: [events]}}
        """
        formatted = {}

        for result in extraction_results:
            doc = result["document"]
            provider = result["provider"]

            if doc not in formatted:
                formatted[doc] = {}

            # Only include successful extractions
            if result["success"]:
                formatted[doc][provider] = result["events"]

        return formatted

    def save_extraction_results(
        self,
        results: List[Dict[str, Any]],
        timestamp: str
    ):
        """Save raw extraction results to JSON and CSV"""

        # Save JSON
        json_path = self.output_dir / f"phase4_extractions_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"💾 Saved extraction results: {json_path}")

        # Save summary CSV
        summary_data = []
        for r in results:
            summary_data.append({
                "Provider": r["provider"],
                "Document": r["document"],
                "Success": r["success"],
                "Events": r["event_count"],
                "Doc Time (s)": r["timing"].get("document_extraction", 0),
                "Event Time (s)": r["timing"].get("event_extraction", 0),
                "Total Time (s)": r["timing"].get("total", 0),
                "Tokens": r["cost"].get("total_tokens", 0),
                "Cost ($)": r["cost"].get("total_cost", 0),
                "Error": r["error"] or ""
            })

        summary_df = pd.DataFrame(summary_data)
        summary_path = self.output_dir / f"phase4_extraction_summary_{timestamp}.csv"
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"💾 Saved extraction summary: {summary_path}")

        # Save individual Excel files per provider (for manual review)
        for provider in self.providers:
            provider_results = [r for r in results if r["provider"] == provider and r["success"]]

            if provider_results:
                # Flatten all events from all documents for this provider
                all_events = []
                for result in provider_results:
                    for event in result["events"]:
                        event_copy = event.copy()
                        event_copy["source_document"] = result["document"]
                        all_events.append(event_copy)

                if all_events:
                    events_df = pd.DataFrame(all_events)
                    # Reorder columns
                    events_df = events_df[["source_document", "number", "date", "event_particulars", "citation", "document_reference"]]
                    events_df.columns = ["Source Document", "No", "Date", "Event Particulars", "Citation", "Document Reference"]

                    excel_path = self.output_dir / f"phase4_{provider}_all_events_{timestamp}.xlsx"
                    events_df.to_excel(excel_path, index=False, sheet_name="All Legal Events")
                    logger.info(f"💾 Saved {provider} events: {excel_path}")


def main():
    """Main entry point"""

    # Configuration - accept test set path from command line
    if len(sys.argv) > 1:
        test_set_path = Path(sys.argv[1])
    else:
        # Default to Famas dispute (quick validation)
        test_set_path = Path("config/benchmarks/test_set_famas_dispute.json")
        logger.info(f"No test set specified, using default: {test_set_path}")

    output_dir = Path("config/benchmarks/results")

    # Verify test set exists
    if not test_set_path.exists():
        logger.error(f"❌ Test set not found: {test_set_path}")
        logger.error("   Available test sets:")
        logger.error("     - config/benchmarks/test_set_famas_dispute.json (2 docs - quick)")
        logger.error("     - config/benchmarks/test_set_amrapali_case.json (8 docs - comprehensive)")
        sys.exit(1)

    # Create runner
    runner = AutomatedBenchmarkRunner(
        test_set_path=test_set_path,
        output_dir=output_dir,
        max_workers=3  # Parallel providers per document
    )

    # Run extractions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extraction_results = runner.run_all_documents()

    # Save extraction results
    runner.save_extraction_results(extraction_results, timestamp)

    # Format for judge
    logger.info("\n🔄 Formatting results for LLM judge...")
    judge_data = runner.format_for_judge(extraction_results)

    # Initialize LLM judge
    logger.info("\n⚖️  Initializing LLM judge...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not set - cannot run LLM judge")
        sys.exit(1)

    judge = LLMJudge(api_key=api_key, model="gpt-4o-mini", temperature=0.0)

    # Run judging
    logger.info("\n🔍 Running LLM-as-judge evaluation...")
    logger.info(f"   Judging {len(judge_data)} documents...")
    comparisons = judge.judge_multiple_documents(judge_data)

    # Aggregate scores
    logger.info("\n📊 Aggregating scores across documents...")
    aggregated = judge.aggregate_scores(comparisons)

    # Identify champions
    logger.info("\n🏆 Identifying champions...")
    champions = judge.identify_champions(aggregated)

    # Export judge results
    judge_output = output_dir / f"phase4_judge_results_{timestamp}.json"
    judge.export_results(
        comparisons=comparisons,
        aggregated_scores=aggregated,
        champions=champions,
        output_path=str(judge_output)
    )

    # Print summary
    logger.info(f"\n{'='*70}")
    logger.info("PHASE 4 BENCHMARK COMPLETE")
    logger.info(f"{'='*70}\n")

    logger.info("🏆 Champions by Category:")
    for category, provider in champions.items():
        logger.info(f"  {category.replace('_', ' ').title()}: {provider.upper()}")

    logger.info("\n📊 Aggregated Scores (averaged across all documents):")
    for provider in sorted(aggregated.keys()):
        scores = aggregated[provider]
        logger.info(f"\n{provider.upper()}:")
        logger.info(f"  Overall Quality:  {scores['overall_quality']:.1f}/10")
        logger.info(f"  Completeness:     {scores['completeness']:.1f}/10")
        logger.info(f"  Accuracy:         {scores['accuracy']:.1f}/10")
        logger.info(f"  Hallucinations:   {scores['hallucinations']:.1f}/10")
        logger.info(f"  Citation Quality: {scores['citation_quality']:.1f}/10")
        logger.info(f"  Win Rate:         {scores['win_rate']:.1%} ({scores['total_wins']}/{scores['total_docs']} docs)")

    logger.info(f"\n{'='*70}")
    logger.info("Next step: Generate comprehensive markdown report (Task 5)")
    logger.info(f"{'='*70}\n")

    # Calculate total cost
    total_cost = sum(
        r["cost"].get("total_cost", 0)
        for r in extraction_results
    )
    logger.info(f"💰 Total extraction cost: ${total_cost:.2f}")

    sys.exit(0)


if __name__ == "__main__":
    main()
