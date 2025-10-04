# Phase 2 Manual Quality Evaluation - Benchmark Guide

## Overview

This directory contains the Phase 2 manual quality evaluation benchmark setup for comparing 6 event extraction providers on a real legal document.

**Test Document**: `Answer to Request for Arbitration.pdf` (677KB, ~15 pages)
**Source**: International arbitration case (Famas GmbH vs Elcomponics Sales)
**Complexity**: Medium - real legal document with multiple events, dates, citations

## Providers Under Test

1. **LangExtract** (Gemini 2.0 Flash) - Google AI via LangExtract SDK
2. **OpenRouter** (Unified API) - Multi-provider aggregator (default: Claude 3 Haiku)
3. **OpenCode Zen** (Legal AI) - Legal-specialized AI gateway
4. **OpenAI** (GPT-4o-mini Direct) - Direct OpenAI API
5. **Anthropic** (Claude 3 Haiku Direct) - Direct Anthropic API
6. **DeepSeek** (Direct API) - DeepSeek-chat via OpenAI-compatible API

## Prerequisites

### Required API Keys

Ensure your `.env` file contains:

```bash
# Required for each provider you want to test
GEMINI_API_KEY=your_gemini_key_here          # For LangExtract
OPENROUTER_API_KEY=your_openrouter_key_here  # For OpenRouter
OPENCODEZEN_API_KEY=your_opencodezen_key     # For OpenCode Zen
OPENAI_API_KEY=your_openai_key_here          # For OpenAI
ANTHROPIC_API_KEY=your_anthropic_key_here    # For Anthropic
DEEPSEEK_API_KEY=your_deepseek_key_here      # For DeepSeek
```

**Note**: The benchmark will skip providers with missing API keys and report them as unavailable.

### Dependencies

All dependencies should already be installed from main project:

```bash
uv sync  # If not already done
```

## Running the Benchmark

### Automated Benchmark (Recommended)

Run the automated benchmark script to process the document with all 6 providers:

```bash
# From project root
uv run python scripts/run_benchmark_phase2.py
```

**What this does:**
1. Processes `test_document.pdf` with each provider sequentially
2. Captures timing (document extraction + event extraction)
3. Captures cost (tokens and $ if available)
4. Extracts legal events and saves to individual Excel files
5. Generates summary CSV and JSON results
6. Identifies preliminary champions (most events, lowest cost, fastest)

**Expected runtime**: 3-5 minutes total (30-60 seconds per provider)

**Output files** (in `config/benchmarks/results/`):
- `benchmark_results_YYYYMMDD_HHMMSS.json` - Raw results with full event data
- `benchmark_summary_YYYYMMDD_HHMMSS.csv` - Summary table for quick analysis
- `{provider}_events_YYYYMMDD_HHMMSS.xlsx` - Individual Excel files with events (for manual review)

### Manual Benchmark (Alternative)

If you prefer manual testing via Streamlit UI:

1. Start the app: `uv run streamlit run app.py`
2. Upload `test_document.pdf`
3. Select provider from dropdown
4. Click "Process Files"
5. Download Excel output
6. Repeat for each of 6 providers

**Advantage**: Visual inspection during processing
**Disadvantage**: More time-consuming (~15 minutes total)

## Manual Quality Review

After running the benchmark, perform manual quality review:

### Review Criteria (Score 0-10 for each)

1. **Completeness**: Are all legal events from the document extracted?
   - 10 = All events captured
   - 5 = ~50% of events captured
   - 0 = No events or only 1-2 events

2. **Accuracy**: Are dates, parties, and facts correct?
   - 10 = All facts accurate
   - 5 = Some errors but mostly correct
   - 0 = Many errors or hallucinations

3. **Hallucinations**: Are there invented facts or citations?
   - 10 = No hallucinations
   - 5 = Minor invented details
   - 0 = Many fabricated facts

4. **Citation Quality**: Are legal citations accurate and properly formatted?
   - 10 = All citations accurate
   - 5 = Some citation errors
   - 0 = Missing or incorrect citations

5. **Overall Quality**: Overall usability for legal professional
   - 10 = Production-ready, no corrections needed
   - 5 = Usable with moderate corrections
   - 0 = Not usable

### Review Process

1. Open each provider's Excel output
2. Compare against source PDF (`test_document.pdf`)
3. Score each criterion 0-10
4. Note specific issues (missing events, errors, hallucinations)
5. Record scores in comparison spreadsheet

## Champion Identification

After manual review, identify champions in each category:

### Champion Categories

1. **Quality Champion**: Highest overall quality score
   - Best for: High-stakes legal work where accuracy is critical

2. **Cost Champion**: Best price/performance ratio
   - Best for: High-volume processing where cost matters

3. **Speed Champion**: Fastest processing time
   - Best for: Real-time applications or batch processing

4. **Balanced Champion**: Best combination of quality/cost/speed
   - Best for: General-purpose legal event extraction

## Expected Results Structure

```
config/benchmarks/
├── README.md (this file)
├── test_document.pdf (test document)
├── benchmark_2025-10-04_metadata.json (benchmark metadata)
└── results/
    ├── benchmark_results_20251004_HHMMSS.json (raw results)
    ├── benchmark_summary_20251004_HHMMSS.csv (summary table)
    ├── langextract_events_20251004_HHMMSS.xlsx
    ├── openrouter_events_20251004_HHMMSS.xlsx
    ├── opencode_zen_events_20251004_HHMMSS.xlsx
    ├── openai_events_20251004_HHMMSS.xlsx
    ├── anthropic_events_20251004_HHMMSS.xlsx
    ├── deepseek_events_20251004_HHMMSS.xlsx
    └── manual_review_scores.csv (created during review)
```

## Next Steps After Benchmark

1. **Complete manual quality review** (score each provider)
2. **Create comparison report** (`docs/reports/phase2-comparison-2025-10-04.md`)
3. **Identify champions** by category
4. **Deliver recommendations**: "Which provider for which use case?"
5. **Decide**: Do results justify adding Moonshot/Zhipu providers?

## Timeline

- **Benchmark run**: 5 minutes
- **Manual review**: 1-2 hours (15-20 minutes per provider)
- **Report creation**: 1-2 hours
- **Total**: 2-4 hours to complete Phase 2

## Troubleshooting

### Provider Fails with "Not Available"
- Check API key is set in `.env`
- Run diagnostic script: `uv run python scripts/test_{provider}.py`

### Empty Events Output
- Check document is valid PDF
- Check provider logs for errors
- Verify JSON mode support for provider

### Cost Not Tracked
- Some providers may not return token usage
- Manual cost estimation possible from provider dashboards

## Questions?

See main project documentation:
- `CLAUDE.md` - Development guide
- `docs/plans/REVISION-2025-10-02.md` - Implementation plan
- Provider diagnostic scripts in `scripts/test_*.py`
