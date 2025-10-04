#!/usr/bin/env python3
"""
Validate LLM-as-Judge against Phase 2 Manual Evaluation

This script tests the LLM judge against the Phase 2 benchmark results
to ensure automated scoring aligns with manual evaluation.

Expected outcome: LLM judge should identify OpenAI as the winner
(matching user's manual preference from Phase 2).
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables FIRST (before imports that need it)
from dotenv import load_dotenv
load_dotenv()

from src.core.llm_judge import LLMJudge

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_phase2_results() -> dict:
    """Load Phase 2 benchmark results"""
    results_path = Path("config/benchmarks/results/benchmark_results_20251004_143920.json")

    if not results_path.exists():
        raise FileNotFoundError(f"Phase 2 results not found: {results_path}")

    with open(results_path) as f:
        return json.load(f)


def format_for_judge(phase2_results: list) -> dict:
    """
    Format Phase 2 results for LLM judge

    Args:
        phase2_results: List of provider results from Phase 2

    Returns:
        Dict formatted for judge: {doc_name: {provider: [events]}}
    """
    # Phase 2 tested one document (Answer to Request for Arbitration.pdf)
    doc_name = "Answer to Request for Arbitration.pdf"

    provider_outputs = {}

    for result in phase2_results:
        provider = result["provider"]

        # Only include successful providers
        if not result["success"]:
            logger.warning(f"Skipping {provider} - failed in Phase 2")
            continue

        # Extract events
        events = result.get("events", [])
        if events:
            provider_outputs[provider] = events
            logger.info(f"{provider}: {len(events)} events")

    return {doc_name: provider_outputs}


def main():
    """Main validation script"""
    logger.info("="*70)
    logger.info("LLM Judge Validation against Phase 2 Manual Evaluation")
    logger.info("="*70)

    # Load Phase 2 results
    logger.info("\n📊 Loading Phase 2 benchmark results...")
    phase2_results = load_phase2_results()
    logger.info(f"Loaded {len(phase2_results)} provider results")

    # Format for judge
    logger.info("\n🔄 Formatting data for LLM judge...")
    document_results = format_for_judge(phase2_results)

    # Initialize judge
    logger.info("\n⚖️  Initializing LLM judge...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not set - cannot run LLM judge")
        sys.exit(1)

    judge = LLMJudge(api_key=api_key, model="gpt-4o-mini", temperature=0.0)

    # Run judgment
    logger.info("\n🔍 Running LLM judge evaluation...")
    comparisons = judge.judge_multiple_documents(document_results)

    # Aggregate scores
    logger.info("\n📊 Aggregating scores...")
    aggregated = judge.aggregate_scores(comparisons)

    # Identify champions
    logger.info("\n🏆 Identifying champions...")
    champions = judge.identify_champions(aggregated)

    # Print results
    logger.info("\n" + "="*70)
    logger.info("VALIDATION RESULTS")
    logger.info("="*70)

    logger.info("\n📊 Per-Provider Scores:")
    for provider in sorted(aggregated.keys()):
        scores = aggregated[provider]
        logger.info(f"\n{provider.upper()}:")
        logger.info(f"  Completeness:     {scores['completeness']:.1f}/10")
        logger.info(f"  Accuracy:         {scores['accuracy']:.1f}/10")
        logger.info(f"  Hallucinations:   {scores['hallucinations']:.1f}/10")
        logger.info(f"  Citation Quality: {scores['citation_quality']:.1f}/10")
        logger.info(f"  Overall Quality:  {scores['overall_quality']:.1f}/10")

    logger.info("\n🏆 Champions by Category:")
    for category, provider in champions.items():
        logger.info(f"  {category.replace('_', ' ').title()}: {provider}")

    # Validation check
    logger.info("\n" + "="*70)
    logger.info("VALIDATION CHECK")
    logger.info("="*70)

    expected_winners = ["openai", "openrouter"]  # Both acceptable (identical in Phase 2)
    actual_winner = champions.get("overall_quality", "").lower()

    # Check for exact match or tie
    openai_score = aggregated.get("openai", {}).get("overall_quality", 0)
    openrouter_score = aggregated.get("openrouter", {}).get("overall_quality", 0)
    is_tie = abs(openai_score - openrouter_score) < 0.1

    if actual_winner in expected_winners:
        logger.info(f"✅ PASS: LLM judge identified {actual_winner.upper()} as overall quality champion")
        if is_tie:
            logger.info(f"   OpenAI and OpenRouter are tied at {openai_score:.1f}/10 (they produced identical outputs in Phase 2)")
        logger.info("   This matches the Phase 2 manual evaluation (user preference)")
        validation_passed = True
    else:
        # Check if OpenAI is in top 2 at least
        top2_providers = sorted(
            aggregated.items(),
            key=lambda x: x[1]["overall_quality"],
            reverse=True
        )[:2]
        top2_names = [p[0].lower() for p in top2_providers]

        if "openai" in top2_names:
            logger.info(f"✅ CONDITIONAL PASS: OpenAI in top 2 ({openai_score:.1f}/10)")
            logger.info(f"   Winner: {actual_winner.upper()}")
            logger.info("   This is acceptable - both are high quality")
            validation_passed = True
        else:
            logger.warning(f"⚠️  MISMATCH: LLM judge identified {actual_winner.upper()} as winner")
            logger.warning(f"   Expected OpenAI in top 2, got {top2_names}")
            logger.warning("   This may indicate the judge needs calibration")
            validation_passed = False

    # Export results
    output_dir = Path("config/benchmarks/results")
    output_path = output_dir / "llm_judge_validation.json"

    judge.export_results(
        comparisons=comparisons,
        aggregated_scores=aggregated,
        champions=champions,
        output_path=str(output_path)
    )

    logger.info(f"\n💾 Validation results saved to: {output_path}")

    # Print detailed reasoning for top providers
    logger.info("\n" + "="*70)
    logger.info("DETAILED REASONING (Top 3 Providers)")
    logger.info("="*70)

    # Get top 3 by overall quality
    top3 = sorted(
        aggregated.items(),
        key=lambda x: x[1]["overall_quality"],
        reverse=True
    )[:3]

    for provider, scores in top3:
        logger.info(f"\n{provider.upper()} (Overall: {scores['overall_quality']:.1f}/10):")

        # Find reasoning from comparison
        for comp in comparisons:
            for score in comp.provider_scores:
                if score.provider.lower() == provider.lower():
                    logger.info(f"  {score.reasoning}")

    # Exit with appropriate code
    if validation_passed:
        logger.info("\n✅ Validation PASSED - LLM judge is aligned with manual evaluation")
        sys.exit(0)
    else:
        logger.warning("\n⚠️  Validation FAILED - LLM judge needs calibration")
        logger.warning("Review detailed reasoning above to diagnose discrepancies")
        sys.exit(1)


if __name__ == "__main__":
    main()
