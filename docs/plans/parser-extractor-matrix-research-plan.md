# Parser-Extractor Matrix Research Plan

**Plan ID**: `parser-extractor-matrix-001`
**Created**: 2025-10-01
**Status**: Draft
**Focus**: Pure R&D - finding optimal parser+extractor combinations

---

## 🎯 Goal

Systematically test parser+extractor combinations to find optimal configuration for legal event extraction, using config externalization to track and reproduce experiments.

**NOT in scope**: User billing, multi-tenancy, production deployment
**IN scope**: Research, benchmarking, finding best combo

---

## 📊 The Matrix

### Parsers to Test (Document → Text)
- **Docling** (current baseline)
- Unstructured.io (future)
- LlamaParse (future)
- PyMuPDF (future)
- Marker (future)

### Extractor Types to Test (Text → Events)
- **LangExtract** (Gemini 2.0 Flash) - Default provider
- **OpenRouter** (Unified API gateway) - 11+ tested models
- **OpenCode Zen** (Legal AI gateway) - 2 tested models

**Note**: OpenRouter and OpenCode Zen are single extractor types with multiple **model configurations**, not separate extractors per model.

### OpenRouter Model Configurations (tested 2025-10-01)
- `openai/gpt-4o-mini` (9/10 quality, $0.15/M)
- `deepseek/deepseek-r1-distill-llama-70b` (10/10 quality, $0.03/M) - Budget champion
- `anthropic/claude-3-haiku` (10/10 quality, $0.25/M)
- `openai/gpt-3.5-turbo` (10/10 quality, $0.50/M)
- +7 more models with 10/10 scores

### OpenCode Zen Model Configurations (tested 2025-10-02)
- `grok-code` (8/10 quality, $0.50/M)
- `code-supernova` (8/10 quality, FREE) - Free tier champion

### Initial Matrix Size
5 parsers × 3 extractor types = **15 baseline combinations**
(Expandable to 50+ with model configuration variations)

---

## 🏗️ Architecture

### Config Directory Structure
```
config/
├── parsers/
│   ├── docling.json          # Docling configuration
│   ├── unstructured.json     # Unstructured.io configuration
│   ├── llamaparse.json       # LlamaParse configuration
│   └── pymupdf.json          # PyMuPDF configuration
│
├── extractors/
│   ├── langextract.json      # Gemini via LangExtract
│   └── openrouter.json       # OpenRouter defaults
│
├── models/
│   └── openrouter-models.json  # Tested OpenRouter models with scores
│       {
│         "primary": "openai/gpt-4o-mini",
│         "fallbacks": [
│           "deepseek/deepseek-r1-distill-llama-70b",
│           "anthropic/claude-3-haiku"
│         ],
│         "tested": {
│           "openai/gpt-4o-mini": {
│             "quality_score": 9,
│             "reliability_score": 9,
│             "cost_per_million": 0.15
│           }
│         }
│       }
│
├── combinations/
│   ├── baseline.json         # Shipped default: Docling + LangExtract (Gemini)
│   ├── openrouter-gpt4o.json # Docling + OpenRouter (GPT-4o Mini)
│   ├── fast-cheap.json       # Docling + OpenRouter (DeepSeek R1 Distill)
│   ├── free-tier.json        # Docling + OpenCode Zen (code-supernova)
│   └── experimental/         # Testing new combos
│
└── benchmarks/
    ├── 2025-10-01_baseline.json      # Baseline test results
    └── 2025-10-15_parser-comparison.json
```

### Code Structure
```
src/core/
├── interfaces.py             # Enhanced DocumentParser protocol
├── config_loader.py          # NEW: Load JSON configs
├── parser_factory.py         # NEW: Create parsers from config
├── extractor_factory.py      # EXISTING: Already has this pattern
├── docling_adapter.py        # REFACTOR: Make config-driven
└── combination_registry.py   # NEW: Load full parser+extractor combos

scripts/
├── benchmark_combinations.py # NEW: Main benchmarking script
└── test_*.py                 # EXISTING: Model testing scripts
```

---

## 📋 Implementation Phases

### Phase 1: Config Externalization Foundation

**Goal**: Move settings from `.env` to tracked config files

**Tasks**:
1. Design config directory structure
2. Create `src/core/config_loader.py`
   - Load JSON config files
   - Support environment variable overrides (API keys only)
   - Validation and error handling
   - **Migration Strategy**: config_loader.py will supplement existing `src/core/config.py` dataclasses by loading JSON files and using them to populate the existing Config objects (DoclingConfig, OpenRouterConfig, etc.). This preserves backward compatibility while enabling tracked configuration.
3. Migrate current setup:
   - Docling settings → `config/parsers/docling.json`
   - LangExtract settings → `config/extractors/langextract.json`
   - OpenRouter settings → `config/extractors/openrouter.json`
   - Baseline combo → `config/combinations/baseline.json`
4. Update `.env.example` to show only API keys

**Deliverables**:
- `config/` directory with initial configs
- `src/core/config_loader.py`
- Updated `.env.example`

---

### Phase 2: Parser Abstraction

**Goal**: Make parsers swappable like extractors

**Tasks**:
1. Formalize `DocumentParser` protocol in `src/core/interfaces.py`
2. Define standard `ParsedDocument` dataclass
3. Refactor `DoclingAdapter` to be config-driven
4. Create `src/core/parser_factory.py` (registry pattern)
5. Ensure backward compatibility

**Deliverables**:
- Enhanced parser interface
- Config-driven DoclingAdapter
- Parser factory with registry

---

### Phase 3: Benchmark Harness

**Goal**: Systematically test combinations

**Tasks**:
1. Create `scripts/benchmark_combinations.py`:
   - Load combination configs
   - Run tests on sample documents
   - Collect metrics: quality, cost, speed
2. Implement quality evaluation framework:
   - Define ground truth format
   - Quality scoring algorithm
   - Compare extracted events vs ground truth
3. Results reporting:
   - Save to `config/benchmarks/`
   - Generate comparison reports
   - Identify winners by metric

**Deliverables**:
- Benchmark runner script
- Quality evaluation framework
- Results storage format

---

### Phase 4: Baseline Testing

**Goal**: Establish current performance metrics

**Tasks**:
1. Prepare test dataset:
   - Select 10-20 representative legal documents
   - Create ground truth annotations
   - Document expected events
2. Benchmark current combinations:
   - Docling + LangExtract (Gemini 2.0 Flash) - Shipped default
   - Docling + OpenRouter (GPT-4o Mini)
   - Docling + OpenRouter (DeepSeek R1 Distill)
   - Docling + OpenCode Zen (grok-code)
   - Docling + OpenCode Zen (code-supernova) - Free tier
3. Document results and identify champion

**Deliverables**:
- Test dataset with ground truth
- Baseline benchmark results
- Champion configuration identified

---

### Phase 5: Alternative Parsers (Future)

**Goal**: Expand the matrix with new parsers

**Tasks**:
1. Research Unstructured.io, LlamaParse, PyMuPDF
2. Implement parser adapters
3. Add to parser factory registry
4. Create config files
5. Run full matrix benchmark

**Deliverables**:
- New parser adapters
- Full matrix benchmark results
- Updated champion configuration

---

## 🎯 Success Criteria

- ✅ Can run benchmark with single command: `uv run python scripts/benchmark_combinations.py`
- ✅ Results are reproducible (same config = same results)
- ✅ Easy to add new parsers (config file + adapter class)
- ✅ Easy to test new models (just config change)
- ✅ All configs version-controlled (track experiments)
- ✅ Clear winner identified for quality, cost, and speed

---

## 📊 Example Config Files

### `config/parsers/docling.json`
```json
{
  "type": "docling",
  "description": "Current baseline parser",
  "settings": {
    "do_ocr": true,
    "do_table_structure": true,
    "table_mode": "FAST",
    "do_cell_matching": true,
    "backend": "default",
    "accelerator_device": "cpu",
    "accelerator_threads": 4,
    "document_timeout": 300
  },
  "cost_model": {
    "type": "free",
    "notes": "Open source, no API costs"
  }
}
```

### `config/extractors/openrouter.json`
```json
{
  "type": "openrouter",
  "description": "OpenRouter with tested models",
  "api_key_env": "OPENROUTER_API_KEY",
  "base_url": "https://openrouter.ai/api/v1",
  "default_model": "openai/gpt-4o-mini",
  "settings": {
    "temperature": 0.0,
    "timeout": 60,
    "max_tokens": 2000
  }
}
```

### `config/combinations/baseline.json`
```json
{
  "combination_id": "baseline",
  "description": "Shipped default configuration (Docling + LangExtract)",
  "parser": {
    "type": "docling",
    "config_file": "config/parsers/docling.json"
  },
  "extractor": {
    "type": "langextract",
    "config_file": "config/extractors/langextract.json",
    "model": "gemini-2.0-flash"
  },
  "metadata": {
    "created_by": "research",
    "created_date": "2025-10-01",
    "tested_date": null,
    "status": "active",
    "notes": "This is the actual shipped default (EVENT_EXTRACTOR=langextract)"
  }
}
```

### `config/benchmarks/2025-10-01_baseline.json`
```json
{
  "benchmark_id": "baseline-001",
  "date": "2025-10-01",
  "test_documents": ["doc1.pdf", "doc2.pdf", "doc3.pdf"],
  "combination_tested": "baseline",
  "results": {
    "quality_score": 9.2,
    "avg_cost_per_doc": 0.018,
    "avg_time_seconds": 12.5,
    "total_events_found": 47,
    "precision": 0.95,
    "recall": 0.89
  },
  "detailed_results": [
    {
      "document": "doc1.pdf",
      "quality": 9.5,
      "cost": 0.020,
      "time": 13.2,
      "events_found": 15
    }
  ]
}
```

---

## 🚀 Getting Started

### Prerequisites
- OpenRouter API key (for extractor testing)
- Gemini API key (for LangExtract testing)
- Test dataset of legal documents

### Quick Start
```bash
# 1. Set up config structure
mkdir -p config/{parsers,extractors,models,combinations,benchmarks}

# 2. Run baseline benchmark
uv run python scripts/benchmark_combinations.py --config config/combinations/baseline.json

# 3. View results (benchmark script creates timestamped file + latest symlink)
cat config/benchmarks/2025-10-0X_baseline.json
# Or use the latest symlink:
cat config/benchmarks/latest.json
```

---

## 📈 Metrics Tracked

### Quality Metrics
- **Precision**: % of extracted events that are correct
- **Recall**: % of actual events that were found
- **F1 Score**: Harmonic mean of precision and recall
- **Overall Quality Score**: 0-10 rating

### Cost Metrics
- **Per Document**: Average API cost per document
- **Per Event**: Cost per extracted event
- **Total Cost**: Full benchmark run cost

### Speed Metrics
- **Parse Time**: Document → text conversion time
- **Extract Time**: Text → events extraction time
- **Total Time**: End-to-end processing time

---

## 🔄 Iteration Workflow

1. **Create Config**: Define new parser or extractor config
2. **Add Combination**: Create combination config file
3. **Run Benchmark**: Execute benchmark script
4. **Analyze Results**: Review metrics in benchmark output
5. **Update Champion**: If new combo wins, update baseline
6. **Commit Config**: Version control the winning config

---

## 📝 Notes

### Why Config Externalization?
- **Reproducibility**: Re-run exact experiments months later
- **Shareability**: Send config to collaborators
- **Tracking**: Git history shows all experiments
- **Flexibility**: Swap components without code changes

### Why Parser Abstraction?
- **Modularity**: Test different parsers easily
- **Fair Comparison**: Same interface = apples-to-apples comparison
- **Future-Proof**: Add new parsers without refactoring

### Why Benchmark Harness?
- **Systematic**: Test all combos consistently
- **Automated**: No manual testing
- **Comparable**: Standard metrics across all tests

---

## 🎯 Related Orders

- `provider-config-externalization-001` - Original inspiration
- `streamlit-provider-selector-001` - UI provider switching (completed)
- `provider-env-validation-001` - Provider-specific validation (completed)

---

## 📚 References

### Tested OpenRouter Models (2025-10-01)
See `scripts/test_fallback_models.py` results:
- 11 models tested with perfect 10/10 score
- Full results: `scripts/fallback_models_test.log`

### Diagnostic Scripts Created (2025-10-01 to 2025-10-02)
- `scripts/test_openrouter.py` - OpenRouter validation (10 checks)
- `scripts/test_deepseek.py` - DeepSeek-specific testing (10 checks)
- `scripts/test_all_models.py` - Multi-model comparison (5 models)
- `scripts/test_fallback_models.py` - Comprehensive testing (18 OpenRouter models)
- `scripts/test_opencode_zen.py` - OpenCode Zen validation (10 checks)
- `scripts/test_opencode_zen_models.py` - Comprehensive testing (4 OpenCode Zen models)
