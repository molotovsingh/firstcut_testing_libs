#!/usr/bin/env python3
"""
Validate 3-Judge Panel Against Phase 2 Manual Evaluation

Runs GPT-5, Claude Opus 4.1, and Gemini 2.5 Pro judges on baseline results
and validates that consensus matches Phase 2 manual evaluation.

Expected Results (from Phase 2):
- OpenAI: 10/10 (user preference: "i liked the openai_events result the best")
- OpenRouter: 10/10 (identical to OpenAI)
- LangExtract: 7/10 (high completeness but NO citations)

Success Criteria:
✅ Consensus winner: OpenAI or OpenRouter (both acceptable)
✅ LangExtract penalized for missing citations (score <5/10)
✅ Inter-judge agreement >0.7 (strong agreement)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables FIRST (before imports that need it)
from dotenv import load_dotenv
load_dotenv()

from src.core.judge_panel import JudgePanel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def load_baseline_results() -> Dict[str, List[Dict[str, Any]]]:
    """Load baseline extraction results from Phase 4"""
    results_file = project_root / "config/benchmarks/results/phase4_extractions_20251004_175446.json"

    if not results_file.exists():
        raise FileNotFoundError(
            f"Baseline results not found: {results_file}\n"
            "Run: uv run python scripts/benchmark_combinations.py config/benchmarks/test_set_famas_baseline.json"
        )

    with open(results_file) as f:
        data = json.load(f)

    # Format for judge: {provider_name: [events]}
    provider_outputs = {}

    for entry in data:
        provider = entry.get("provider", "unknown")
        events = entry.get("events", [])

        # Filter out fallback/error events
        valid_events = [
            e for e in events
            if "Failed to extract" not in e.get("event_particulars", "")
        ]

        provider_outputs[provider] = valid_events

    return provider_outputs


def validate_panel_consensus(panel_result):
    """Validate panel consensus against Phase 2 manual evaluation"""
    logger.info("\n" + "="*70)
    logger.info("VALIDATION: Panel Consensus vs Phase 2 Manual Evaluation")
    logger.info("="*70)

    validation_passed = True

    # Expected winners from Phase 2
    expected_winners = ["openai", "openrouter"]
    actual_winner = panel_result.consensus_winner.lower()

    # Check 1: Winner should be OpenAI or OpenRouter
    if actual_winner in expected_winners:
        logger.info(f"✅ PASS: Consensus winner '{panel_result.consensus_winner}' matches Phase 2 expectations")
        logger.info(f"   Phase 2: User preferred OpenAI/OpenRouter (both got 10/10)")
        logger.info(f"   Panel vote: {panel_result.winner_votes}")
    else:
        logger.error(f"❌ FAIL: Consensus winner '{panel_result.consensus_winner}' does not match Phase 2")
        logger.error(f"   Expected: {expected_winners}")
        logger.error(f"   Panel vote: {panel_result.winner_votes}")
        validation_passed = False

    # Check 2: OpenAI and OpenRouter should have high scores (>7.0)
    if "openai" in panel_result.consensus_scores:
        openai_score = panel_result.consensus_scores["openai"].overall_quality
        if openai_score >= 7.0:
            logger.info(f"✅ PASS: OpenAI consensus score {openai_score:.1f}/10 (expected >7.0)")
        else:
            logger.error(f"❌ FAIL: OpenAI consensus score {openai_score:.1f}/10 too low (expected >7.0)")
            validation_passed = False

    if "openrouter" in panel_result.consensus_scores:
        openrouter_score = panel_result.consensus_scores["openrouter"].overall_quality
        if openrouter_score >= 7.0:
            logger.info(f"✅ PASS: OpenRouter consensus score {openrouter_score:.1f}/10 (expected >7.0)")
        else:
            logger.error(f"❌ FAIL: OpenRouter consensus score {openrouter_score:.1f}/10 too low (expected >7.0)")
            validation_passed = False

    # Check 3: LangExtract should be penalized for missing citations (<5.0)
    if "langextract" in panel_result.consensus_scores:
        langextract_score = panel_result.consensus_scores["langextract"].overall_quality
        if langextract_score < 5.0:
            logger.info(f"✅ PASS: LangExtract penalized {langextract_score:.1f}/10 (expected <5.0 for missing citations)")
            logger.info(f"   Phase 2: LangExtract had 5 events but NO citations (fatal flaw)")
        else:
            logger.error(f"❌ FAIL: LangExtract score {langextract_score:.1f}/10 too high (expected <5.0)")
            logger.error(f"   LangExtract should be heavily penalized for missing citations")
            validation_passed = False

    # Check 4: Inter-judge agreement should be strong (>0.7)
    avg_correlation = panel_result.agreement.average_correlation
    if avg_correlation >= 0.7:
        logger.info(f"✅ PASS: Inter-judge agreement {avg_correlation:.3f} is strong (expected >0.7)")
    else:
        logger.warning(f"⚠️ WARNING: Inter-judge agreement {avg_correlation:.3f} is moderate (expected >0.7)")
        logger.warning(f"   Pairwise correlations: {panel_result.agreement.pearson_correlation}")
        # Not a hard failure, but worth noting

    # Check 5: Confidence level
    confidence = panel_result.agreement.confidence_level
    logger.info(f"\n📊 Confidence Level: {confidence}")
    logger.info(f"   Winner Consensus: {panel_result.agreement.winner_consensus_percentage:.1f}%")

    return validation_passed


def main():
    logger.info("\n" + "="*70)
    logger.info("🎯 3-JUDGE PANEL VALIDATION")
    logger.info("="*70)
    logger.info("\nValidating 3-judge panel against Phase 2 manual evaluation...")

    # Check API keys
    required_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
    }

    missing_keys = [k for k, v in required_keys.items() if not v]
    if missing_keys:
        logger.error(f"\n❌ Missing API keys: {', '.join(missing_keys)}")
        logger.error("Please set these environment variables in .env file")
        sys.exit(1)

    logger.info("\n✅ All API keys configured")

    # Load baseline results
    logger.info("\n📂 Loading baseline extraction results...")
    try:
        provider_outputs = load_baseline_results()
        logger.info(f"✅ Loaded results for {len(provider_outputs)} providers")
        for provider, events in provider_outputs.items():
            logger.info(f"   {provider}: {len(events)} events")
    except Exception as e:
        logger.error(f"❌ Failed to load baseline results: {e}")
        sys.exit(1)

    # Initialize 3-judge panel
    logger.info("\n🎯 Initializing 3-judge panel...")
    try:
        panel = JudgePanel(
            gpt5_api_key=required_keys["OPENAI_API_KEY"],
            claude_api_key=required_keys["ANTHROPIC_API_KEY"],
            gemini_api_key=required_keys["GEMINI_API_KEY"]
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize panel: {e}")
        sys.exit(1)

    # Run panel evaluation
    logger.info("\n🔍 Running 3-judge panel evaluation...")
    logger.info("⏳ This may take 30-60 seconds (3 premium models with deep thinking)...\n")

    try:
        document_name = "Answer to Request for Arbitration.pdf"
        panel_result = panel.judge_document(document_name, provider_outputs)
    except Exception as e:
        logger.error(f"❌ Panel evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Validate results
    validation_passed = validate_panel_consensus(panel_result)

    # Save results
    output_dir = project_root / "config/benchmarks/results"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = panel_result.timestamp.replace(":", "").replace(".", "_").replace("-", "")[:15]
    output_file = output_dir / f"phase4_panel_validation_{timestamp}.json"

    panel.save_results(panel_result, str(output_file))

    # Final summary
    logger.info("\n" + "="*70)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*70)

    if validation_passed:
        logger.info("🎉 VALIDATION PASSED ✅")
        logger.info(f"\n✅ 3-judge panel consensus aligns with Phase 2 manual evaluation")
        logger.info(f"✅ Consensus winner: {panel_result.consensus_winner} (expected: OpenAI or OpenRouter)")
        logger.info(f"✅ Inter-judge agreement: {panel_result.agreement.average_correlation:.3f} (expected >0.7)")
        logger.info(f"✅ Confidence level: {panel_result.agreement.confidence_level}")
    else:
        logger.error("❌ VALIDATION FAILED")
        logger.error("\nSome validation checks did not pass. Review the results above.")

    logger.info(f"\n💰 Total cost: ${panel_result.total_cost:.4f}")
    logger.info(f"💭 Total thinking tokens: {panel_result.total_thinking_tokens:,}")
    logger.info(f"\n📁 Results saved to: {output_file}")

    logger.info("\n" + "="*70 + "\n")

    sys.exit(0 if validation_passed else 1)


if __name__ == "__main__":
    main()
