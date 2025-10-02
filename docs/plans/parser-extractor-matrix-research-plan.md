# Parser-Extractor Matrix Research Plan

**Plan ID**: `parser-extractor-matrix-001`
**Created**: 2025-10-01
**Last Revised**: 2025-10-02
**Status**: Active - Phase 1 in progress
**Focus**: Pure R&D - finding optimal parser+extractor combinations
**Approach**: Value-first (providers before infrastructure)

> **⚠️ IMPORTANT**: This plan was significantly revised on 2025-10-02 after critical review.
> See `docs/plans/REVISION-2025-10-02.md` for complete details on amendments.
> Key change: **Phase ordering revised from infrastructure-first to value-first**.

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

#### Gateway APIs (Multi-Model Aggregators)
- **LangExtract** (Gemini 2.0 Flash) - Default provider, Google's Gemini API
- **OpenRouter** (Unified API gateway) - 11+ tested models, multi-provider access
- **OpenCode Zen** (Legal AI gateway) - 2 tested models, legal-focused

#### Direct APIs (Single-Vendor)
- **OpenAI Direct** - GPT-4, GPT-4o, GPT-4o-mini, GPT-3.5-turbo
- **Anthropic Direct** - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **DeepSeek Direct** - DeepSeek V3, DeepSeek R1, DeepSeek Chat
- **Moonshot/Kimi** - Kimi K2 (1T params), K2-Instruct (256K context)
- **Zhipu/ChatGLM** - GLM-4, GLM-4.5, GLM-4-Air (200K context)

**Note**: Gateway APIs aggregate multiple models under one API. Direct APIs provide single-vendor access with potential for better pricing/features.

### Gateway API Model Configurations

#### OpenRouter Models (tested 2025-10-01)
- `openai/gpt-4o-mini` (9/10 quality, $0.15/M)
- `deepseek/deepseek-r1-distill-llama-70b` (10/10 quality, $0.03/M) - Budget champion
- `anthropic/claude-3-haiku` (10/10 quality, $0.25/M)
- `openai/gpt-3.5-turbo` (10/10 quality, $0.50/M)
- +7 more models with 10/10 scores

#### OpenCode Zen Models (tested 2025-10-02)
- `grok-code` (8/10 quality, $0.50/M)
- `code-supernova` (8/10 quality, FREE) - Free tier champion

### Direct API Model Configurations (Planned)

#### OpenAI Models
- `gpt-4o` - Latest flagship (10/10 expected, $2.50/M input, $10.00/M output)
- `gpt-4o-mini` - Fast and affordable (9/10 via OpenRouter, $0.15/M input, $0.60/M output)
- `gpt-4-turbo` - Previous generation (10/10 via OpenRouter, $10.00/M input, $30.00/M output)
- `gpt-3.5-turbo` - Legacy option (10/10 via OpenRouter, $0.50/M input, $1.50/M output)

#### Anthropic Models
- `claude-3-5-sonnet-20241022` - Highest intelligence (10/10 via OpenRouter, $3.00/M input, $15.00/M output)
- `claude-3-opus-20240229` - Most capable (10/10 expected, $15.00/M input, $75.00/M output)
- `claude-3-haiku-20240307` - Fastest (10/10 via OpenRouter, $0.25/M input, $1.25/M output)

#### DeepSeek Models
- `deepseek-chat` - General purpose (9/10 expected, $0.14/M input, $0.28/M output)
- `deepseek-reasoner` - R1 reasoning model (10/10 via OpenRouter as distill, pricing TBD)
- `deepseek-coder` - Code-specialized (9/10 expected, $0.14/M input, $0.28/M output)

#### Moonshot Models (Kimi)
- `moonshot-v1-128k` - Standard context (9/10 expected, $0.84/M input, $0.84/M output)
- `moonshot-v1-32k` - Reduced context (9/10 expected, $0.24/M input, $0.24/M output)
- `moonshot-v1-8k` - Minimal context (8/10 expected, $0.084/M input, $0.084/M output)

#### Zhipu Models (ChatGLM)
- `glm-4` - Latest generation (9/10 expected, $0.50/M input, $0.50/M output)
- `glm-4-air` - Lightweight (8/10 expected, $0.05/M input, $0.05/M output)
- `glm-4-flash` - Ultra-fast (7/10 expected, $0.01/M input, $0.01/M output)

### Updated Matrix Size
5 parsers × 8 extractor types = **40 baseline combinations**
(Expandable to 100+ with model configuration variations)

---

## 🏗️ Architecture

### Config Directory Structure
```
config/
├── parsers/
│   ├── docling.json          # Docling configuration (current baseline)
│   ├── unstructured.json     # Unstructured.io configuration (future)
│   ├── llamaparse.json       # LlamaParse configuration (future)
│   ├── pymupdf.json          # PyMuPDF configuration (future)
│   └── marker.json           # Marker configuration (future)
│
├── extractors/
│   ├── gateways/             # Multi-model API gateways
│   │   ├── langextract.json  # Gemini via LangExtract
│   │   ├── openrouter.json   # OpenRouter unified API
│   │   └── opencode_zen.json # OpenCode Zen legal AI
│   │
│   └── direct/               # Single-vendor APIs
│       ├── openai.json       # OpenAI direct API
│       ├── anthropic.json    # Anthropic direct API
│       ├── deepseek.json     # DeepSeek direct API
│       ├── moonshot.json     # Moonshot/Kimi K2 API
│       └── zhipu.json        # Zhipu/ChatGLM API
│
├── models/                   # Model registries with test scores
│   ├── openrouter-models.json      # 11+ tested OpenRouter models
│   ├── opencode-zen-models.json    # 2 tested OpenCode Zen models
│   ├── openai-models.json          # OpenAI model configurations
│   ├── anthropic-models.json       # Anthropic model configurations
│   ├── deepseek-models.json        # DeepSeek model configurations
│   ├── moonshot-models.json        # Moonshot model configurations
│   └── zhipu-models.json           # Zhipu model configurations
│
│   Example registry structure:
│   {
│     "provider": "openrouter",
│     "primary": "openai/gpt-4o-mini",
│     "fallbacks": [
│       "deepseek/deepseek-r1-distill-llama-70b",
│       "anthropic/claude-3-haiku"
│     ],
│     "tested": {
│       "openai/gpt-4o-mini": {
│         "quality_score": 9,
│         "reliability_score": 9,
│         "cost_per_million": 0.15
│       }
│     }
│   }
│
├── combinations/
│   ├── baseline.json           # Shipped default: Docling + LangExtract
│   ├── openrouter-gpt4o.json   # Docling + OpenRouter (GPT-4o-mini)
│   ├── opencode-zen-free.json  # Docling + OpenCode Zen (code-supernova)
│   ├── openai-direct.json      # Docling + OpenAI (GPT-4o-mini)
│   ├── anthropic-direct.json   # Docling + Anthropic (Claude Haiku)
│   ├── deepseek-direct.json    # Docling + DeepSeek (R1)
│   ├── moonshot-k2.json        # Docling + Moonshot (Kimi K2)
│   ├── zhipu-glm4.json         # Docling + Zhipu (GLM-4)
│   └── experimental/           # Testing new combos
│
└── benchmarks/
    ├── 2025-10-XX_8provider_comparison.json  # 8-provider comparison
    ├── 2025-10-XX_baseline.json              # Baseline test results
    └── latest.json                           # Symlink to most recent
```

### Code Structure
```
src/core/
├── interfaces.py             # Enhanced DocumentParser protocol
├── config_loader.py          # NEW: Load JSON configs
├── parser_factory.py         # NEW: Create parsers from config
├── extractor_factory.py      # EXISTING: Expand to 8 providers
├── combination_registry.py   # NEW: Load full parser+extractor combos
│
├── docling_adapter.py        # REFACTOR: Make config-driven
│
├── langextract_adapter.py    # EXISTING: LangExtract/Gemini adapter
├── openrouter_adapter.py     # EXISTING: OpenRouter adapter
├── opencode_zen_adapter.py   # EXISTING: OpenCode Zen adapter
│
├── openai_adapter.py         # NEW: OpenAI direct API adapter
├── anthropic_adapter.py      # NEW: Anthropic direct API adapter
├── deepseek_adapter.py       # NEW: DeepSeek direct API adapter
├── moonshot_adapter.py       # NEW: Moonshot/Kimi K2 adapter
└── zhipu_adapter.py          # NEW: Zhipu/ChatGLM adapter

scripts/
├── benchmark_combinations.py # NEW: Main benchmarking script
│
├── test_openrouter.py        # EXISTING: OpenRouter validation (10 checks)
├── test_opencode_zen.py      # EXISTING: OpenCode Zen validation (10 checks)
├── test_fallback_models.py   # EXISTING: Comprehensive model testing
│
├── test_openai.py            # NEW: OpenAI direct API validation
├── test_anthropic.py         # NEW: Anthropic direct API validation
├── test_deepseek_direct.py   # NEW: DeepSeek direct API validation
├── test_moonshot.py          # NEW: Moonshot/Kimi validation
└── test_zhipu.py             # NEW: Zhipu/ChatGLM validation
```

---

## 🔐 API Authentication Matrix

| Provider | API Key Env Var | Base URL | Auth Method | Status |
|----------|----------------|----------|-------------|--------|
| LangExtract | `GEMINI_API_KEY` | Google Gemini API | API Key | ✅ Implemented |
| OpenRouter | `OPENROUTER_API_KEY` | https://openrouter.ai/api/v1 | Bearer Token | ✅ Implemented |
| OpenCode Zen | `OPENCODEZEN_API_KEY` | https://api.opencode-zen.com/v1 | X-API-Key | ✅ Implemented |
| OpenAI | `OPENAI_API_KEY` | https://api.openai.com/v1 | Bearer Token | ⏳ Planned |
| Anthropic | `ANTHROPIC_API_KEY` | https://api.anthropic.com/v1 | x-api-key | ⏳ Planned |
| DeepSeek | `DEEPSEEK_API_KEY` | https://api.deepseek.com/v1 | Bearer Token | ⏳ Planned |
| Moonshot | `MOONSHOT_API_KEY` | https://api.moonshot.cn/v1 | Bearer Token | ⏳ Planned |
| Zhipu | `ZHIPU_API_KEY` | https://open.bigmodel.cn/api/paas/v4 | Bearer Token | ⏳ Planned |

**Authentication Methods**:
- **Bearer Token**: `Authorization: Bearer <api_key>` (HTTP header)
- **X-API-Key**: `X-API-Key: <api_key>` (HTTP header)
- **x-api-key**: `x-api-key: <api_key>` (HTTP header, lowercase for Anthropic)
- **API Key**: Provider-specific parameter (e.g., query string or request body)

**Implementation Notes**:
- All adapters should handle auth failures gracefully with clear error messages
- API keys should NEVER be in config JSON files - only in `.env` (secrets)
- Config files reference env var names, not actual keys
- Diagnostic scripts test auth before full integration

---

## 📋 Implementation Phases

---

## ⚠️ **REVISION NOTES (2025-10-02)**

**Original Plan Issues**:
- ❌ Waterfall anti-pattern (infrastructure before value)
- ❌ Config externalization overcomplexity (YAGNI violation)
- ❌ Parser abstraction premature (N=1 problem)
- ❌ Resource underestimates (2-3x optimistic)
- ❌ Circular dependencies (benchmark needs ground truth marked TBD)

**Revised Approach**:
- ✅ Value-first: Deliver 8 providers in 4 weeks (was 5 weeks to infrastructure)
- ✅ Use existing .env + dataclass pattern (proven with 3 providers)
- ✅ Defer parser abstraction until 2nd parser exists
- ✅ Realistic estimates: 3-4 weeks for 5 providers
- ✅ Manual testing before automation

**Timeline Comparison**:
- **Original**: 9 weeks (Phases 1→2→2.5→3→3.5→4)
- **Revised**: 4 weeks to 8 providers, 6-7 weeks to full automation

---

### Phase 1: Add 5 Direct API Providers ⭐ VALUE DELIVERY

**Timeline**: 3-4 weeks | **Cost**: $50-200 testing budget | **Status**: In Progress

**Goal**: Expand from 3 → 8 working providers using proven dataclass pattern

**Strategy**: Use existing `.env` + dataclass pattern (no complex JSON configs)

**Tasks** (per provider, ~3-4 days each):

**Core Integration** (Tasks 1-8):
1. Create adapter file (follow EventExtractor protocol from `src/core/interfaces.py`)
2. Add Config dataclass to existing `src/core/config.py` (follow OpenRouterConfig pattern)
3. Register in `EVENT_PROVIDER_REGISTRY` dict in `src/core/extractor_factory.py`
4. Add factory function `_create_{provider}_event_extractor()`
5. Update `load_provider_config()` to handle new provider key
6. Create diagnostic test script (10-level validation, adapt from `test_openrouter.py` template):
   - **Reuse Strategy**: Use existing template (Steps 1-6 unchanged: env, config, network, auth)
   - **Customization**: Adapt Steps 7-10 for provider-specific JSON quirks
   - **Effort**: 2-3 hours per script (90% template reuse, not written from scratch)
7. Run model testing (quality/reliability/cost scoring, document in comments)
8. **Update Streamlit UI incrementally** (`app.py` lines 128-154):
   - Add new key to existing `provider_options` dict (already has 3 providers)
   - Update help text to include new API key requirement
   - Add status indicator function (✅ configured / ⚠️ missing key)
   - **Note**: Selector UI already exists, just adding options incrementally
   - **Cache Management**: VALIDATE existing logic (clears `legal_events_df` on provider change) works with new providers - no code changes expected unless regression found

**Operational Requirements** (Tasks 9-13):
9. Implement rate limiting with exponential backoff (handle 429 errors gracefully)
10. Add cost tracking (token counting → $/request conversion, cumulative spend logging)
11. Implement error recovery patterns (retry logic with backoff, clear error messages for auth/network failures)
12. Write unit tests (adapter initialization, config validation, error path handling)
13. Write integration test (end-to-end with real API call, verify JSON output schema)

**Documentation** (Tasks 14-15):
14. Update `.env.example` with new provider section and tested model recommendations
15. Document provider setup (auth method, base URL, JSON mode quirks, troubleshooting)

**Providers** (in order of ease):

1. **OpenAI** (Week 1) - Easiest, standard OpenAI API with documented JSON mode
   - **JSON Mode API**: Use `response_format={"type": "json_object"}` (NOT function calling)
   - **Model Compatibility**: JSON mode requires GPT-4o, GPT-4-turbo, or GPT-3.5-turbo-1106+
   - **Validation**: Check model name before enabling JSON mode (fail early if incompatible)
   - **Fallback Strategy**: If legacy model selected, use prompt engineering + manual parsing
   - **Reference**: https://platform.openai.com/docs/guides/structured-outputs
   - **Risk**: LOW (instant signup, stable API, native JSON support)
   - **Mitigation**: Set usage limits ($50 budget), monitor quota, tier-based rate limits apply

2. **Anthropic** (Week 2) - Medium difficulty, requires tool use pattern for structured JSON
   - **Risk**: LOW (1-2 day approval, stable API, high quality)
   - **Mitigation**: Apply for API access early, tier-based rate limits, monitor usage

3. **DeepSeek** (Week 3) - Medium difficulty, compare direct API to OpenRouter's distilled version
   - **Risk**: MEDIUM (instant signup, but rate limits/stability unknown)
   - **Mitigation**: Test rate limits early, have OpenRouter fallback ready, budget for testing
4. **Moonshot (Kimi)** (Week 4) - **HIGH RISK**:
   - ⚠️ Mainland China API - may require VPN for access
   - ⚠️ Signup requires Chinese phone number verification
   - ⚠️ JSON structured output not guaranteed (may need fallback parsing)
   - ⚠️ Documentation primarily in Chinese
   - **Mitigation**: Account procurement plan, manual JSON parsing fallback, extended testing time
5. **Zhipu (ChatGLM)** (Week 4) - **HIGH RISK**:
   - ⚠️ Mainland China API - may require VPN for access
   - ⚠️ Account approval process (not instant)
   - ⚠️ JSON mode support uncertain (may need response parsing)
   - ⚠️ Authentication may require special token formatting
   - **Mitigation**: Early account signup, fallback to manual review if JSON unreliable, budget extra debugging time

**Provider Risk Assessment Summary**:

| Provider   | Signup      | JSON Support      | Rate Limits    | API Stability | Risk Level | Est. Time |
|------------|-------------|-------------------|----------------|---------------|------------|-----------|
| OpenAI     | Instant     | ✅ Native (stable) | 3500 RPM       | High          | **LOW**    | 3 days    |
| Anthropic  | 1-2 day     | ✅ Tool Use       | Tier-based     | High          | **LOW**    | 3-4 days  |
| DeepSeek   | Instant     | ✅ Native (new)   | Unknown        | Medium        | **MEDIUM** | 3-4 days  |
| Moonshot   | Phone + VPN | ⚠️ Uncertain      | Unknown        | Low           | **HIGH**   | 4-5 days  |
| Zhipu      | Approval    | ⚠️ Uncertain      | Unknown        | Low           | **HIGH**   | 4-5 days  |

**Key Insights**:
- **Fast Path** (Weeks 1-2): OpenAI + Anthropic = 6-8 days for 2 reliable providers
- **Medium Risk** (Week 3): DeepSeek = good quality test, compare to OpenRouter
- **High Risk** (Week 4): Moonshot + Zhipu = budget 8-10 days, may require account procurement workarounds
- **Total Estimate**: 20-27 days (4-5 weeks realistic, not 3-4 weeks optimistic)

**Deliverables**:
- ✅ 5 new adapter files (~500 lines each)
- ✅ 5 Config dataclasses in existing config.py
- ✅ Factory updated with 8 total providers
- ✅ 5 diagnostic scripts with 10/10 validation
- ✅ Streamlit UI with 8-provider selector + status indicators
- ✅ Updated .env.example with all 8 providers
- ✅ Rate limiting & retry logic in each adapter
- ✅ Cost tracking helpers
- ✅ Error recovery patterns
- ✅ Unit tests for each adapter
- ✅ Documentation for each provider

**Success Criteria**:
- All 8 providers pass diagnostic validation
- Can process test document with each provider
- UI shows provider status (✅ configured / ⚠️ missing key)
- Clear error messages for auth failures
- Rate limits handled gracefully
- Cost tracked per request

---

### Phase 2: Manual Quality Evaluation ⭐ PROVE VALUE

**Timeline**: 2-3 days | **Cost**: $20-50 API calls | **Status**: Pending

**Goal**: Answer "which provider is best?" with real data before investing in automation

**Tasks**:
1. Select 1 representative legal document (medium complexity, ~10 pages)
2. Process with all 8 providers (run in parallel to save time)
3. Human review of outputs:
   - Quality score (0-10): Accuracy, completeness, context
   - Completeness: Events found vs expected (manual count)
   - Accuracy: False positives and false negatives
   - Format compliance: Five-Column Table structure
4. Document findings in comparison report
5. Identify obvious winners/losers by category
6. Decide if automation investment is justified

**Deliverables**:
- ✅ Test document selected (tracked in git, ~10 pages)
- ✅ 8 provider outputs (Excel files in `test_results/manual_comparison/`)
- ✅ Comparison report: `docs/benchmarks/2025-10-XX-manual-comparison.md`
- ✅ Quality rankings table (provider × quality/cost/speed)
- ✅ Cost analysis ($/document actual spend)
- ✅ Speed analysis (seconds measured)
- ✅ Recommendation matrix by use case:
  - **Quality Champion**: Best accuracy/completeness (high-stakes work)
  - **Cost Champion**: Best $/document (high-volume processing)
  - **Speed Champion**: Fastest processing (real-time apps)
  - **Free Tier Champion**: Best quality at $0 cost (prototyping)
  - **Balanced Champion**: Best quality/cost/speed tradeoff (production default)

**Success Criteria**:
- Can answer: "Which provider should we use for [use case]?"
- Have data to justify automation investment decision
- Documented methodology for future comparisons
- Clear cost/quality tradeoffs understood

---

### Phase 3: Simple Benchmark Config System (Optional)

**Timeline**: 2-3 days | **Cost**: $0 | **Status**: Pending

**Goal**: Version-control benchmark results (NOT provider configs - those use .env)

**Tasks**:
1. Create `config/benchmarks/` directory
2. Define simple JSON schema for benchmark results
3. Create script to save results: `scripts/save_benchmark.py`
4. Update .gitignore to track benchmark results

**JSON Schema Example**:
```json
{
  "benchmark_id": "manual-2025-10-02",
  "date": "2025-10-02",
  "providers_tested": ["langextract", "openrouter", "openai", "anthropic", "deepseek", "moonshot", "zhipu", "opencode_zen"],
  "test_document": "sample_pdf/famas_dispute/Award.pdf",
  "document_pages": 15,
  "results": {
    "langextract": {
      "quality_score": 9,
      "cost_usd": 0.018,
      "time_seconds": 12.5,
      "events_found": 14
    },
    "openai": {
      "quality_score": 10,
      "cost_usd": 0.015,
      "time_seconds": 8.2,
      "events_found": 15
    }
  },
  "champions": {
    "quality": "openai",
    "cost": "deepseek",
    "speed": "openrouter",
    "free_tier": "opencode_zen",
    "balanced": "openai"
  },
  "notes": "Manual evaluation by legal expert. OpenAI best overall quality, DeepSeek best cost."
}
```

**Deliverables**:
- ✅ `config/benchmarks/` directory structure
- ✅ JSON schema documented (simple, no complex infrastructure)
- ✅ `scripts/save_benchmark.py` helper script
- ✅ `.gitignore` updated to track benchmark results
- ✅ Example benchmark file with real data

**Success Criteria**:
- Benchmark results are version-controlled
- Easy to compare results across time
- No complex config_loader or provider configs needed
- Results can be manually created or script-generated

---

### Phase 3: Benchmark Harness

**Goal**: Systematically test combinations

**Tasks**:
1. Create `scripts/benchmark_combinations.py`:
   - Load combination configs from `config/combinations/`
   - Support testing specific providers: `--provider openai` or `--all` for all 8
   - Support testing specific combinations: `--config config/combinations/baseline.json`
   - Run tests on sample documents in parallel (multi-threading for speed)
   - Collect metrics: quality (precision/recall/F1), cost ($/doc), speed (seconds)
   - Progress indicators for long-running tests

2. Implement quality evaluation framework:
   - Define ground truth format (JSON schema for legal events)
   - **Quality scoring algorithm**: LLM-as-judge (recommended for legal events)
     - Use GPT-4 or Claude 3.5 Sonnet as judge
     - Compare extracted events against ground truth
     - Score on 0-10 scale for accuracy and completeness
     - Generate detailed comparison reports
   - Alternative methods:
     - Semantic similarity (embedding-based, fast but less accurate)
     - String matching with fuzzy logic (brittle, fails on paraphrasing)
     - Human evaluation (gold standard but slow and expensive)
   - Compare extracted events vs ground truth with detailed diffs

3. Results reporting:
   - Save to `config/benchmarks/YYYY-MM-DD_test-name.json` (timestamped)
   - Create `latest.json` symlink to most recent benchmark
   - Generate comparison reports (markdown tables, CSV exports)
   - Identify champions by category:
     - **Quality Champion**: Best precision/recall/F1
     - **Cost Champion**: Best $/document (lowest cost)
     - **Speed Champion**: Fastest processing time
     - **Free Tier Champion**: Best quality among free options
     - **Balanced Champion**: Best quality/cost/speed tradeoff
   - Create leaderboards for each metric
   - Generate recommendation matrix by use case (quality-focused, budget-focused, speed-focused)

**Deliverables**:
- Benchmark runner script with parallel execution
- Quality evaluation framework (LLM-as-judge + alternatives)
- Results storage format (JSON with timestamps)
- Champion identification logic
- Leaderboard generation
- Use case recommendation matrix

---

### Phase 3.2: Lawyer Review System (Ground Truth Creation) — ⏸️ **TBD**

**Status**: To Be Decided Later (depends on Phase 3 LLM-as-judge performance)

**Goal**: Enable lawyer annotations for building ground truth dataset (if needed for LLM-as-judge calibration)

**Relationship to Phase 3**:
- Phase 3's LLM-as-judge can evaluate extraction quality WITHOUT ground truth (scores quality directly)
- Phase 3.2 creates human-validated reference data IF automated evaluation needs calibration
- **Decision point**: Implement only if LLM-as-judge scores seem unreliable or require validation

**Tasks** (if implemented):
1. Create `test_results/` directory structure (tracked in git)
2. Add `src/utils/result_saver.py`:
   - save_test_result() function
   - Captures parser + extractor + model metadata
   - Saves raw Excel (5 columns)
   - Saves metadata.json with full config
3. Update Streamlit UI:
   - Add "Save to Test Results" checkbox in download section
   - Text input for case name (defaults to first filename)
   - Success message with result path
4. Create `scripts/prepare_for_review.py`:
   - Adds 7 review columns to Excel (✅/❌/⚠️, Quality 1-10, Issues, Notes, Corrections)
   - Adds data validation (dropdowns)
   - Adds conditional formatting for quality scores
5. Create `scripts/process_review.py`:
   - Reads reviewed Excel
   - Generates review.json with structured annotations
   - Updates metadata.json with review status
   - Calculates approval rate, average quality score, issue frequency
6. Update .gitignore to track test_results/

**Review Format**:
- Raw: 5 columns (No, Date, Event Particulars, Citation, Doc Ref)
- Reviewed: +7 columns (✅/❌, Quality 1-10, Issues, Notes, Fixed Date, Fixed Particulars, Fixed Citation)

**Deliverables** (if implemented):
- test_results/ directory (tracked)
- Result saver module
- Excel review template with validation
- Review processing script
- Integration with Streamlit download section
- Ground truth dataset for LLM-as-judge calibration

**Decision Criteria**:
- ✅ **Implement** if: LLM-as-judge scores are ambiguous, need human validation, or planning academic research
- ❌ **Skip** if: LLM-as-judge provides clear quality rankings without ground truth
- ⏸️ **Defer** if: Phase 3 results are good enough for initial provider comparison

**ROI Analysis**:
- Cost: ~2-3 hours lawyer time per test case (5-10 cases = 15-30 hours)
- Benefit: Enables precise automated evaluation of 40+ combinations
- Tradeoff: High upfront cost, but creates reusable reference dataset

---

### Phase 3.5: User Selection UI

**Goal**: Enable users to select parser, extractor, and model through Streamlit UI

**Tasks**:
1. **Update Streamlit provider selector** (`app.py` lines 128-154):
   - Provider options already expanded to 8 in Phase 2.5
   - Verify all 8 providers display correctly in radio buttons
   - Add provider configuration status indicators:
     ```python
     def get_provider_status(provider):
         """Check if provider API key is configured"""
         env_vars = {
             'langextract': 'GEMINI_API_KEY',
             'openrouter': 'OPENROUTER_API_KEY',
             'opencode_zen': 'OPENCODEZEN_API_KEY',
             'openai': 'OPENAI_API_KEY',
             'anthropic': 'ANTHROPIC_API_KEY',
             'deepseek': 'DEEPSEEK_API_KEY',
             'moonshot': 'MOONSHOT_API_KEY',
             'zhipu': 'ZHIPU_API_KEY',
         }
         api_key = os.getenv(env_vars[provider])
         return '✅' if api_key else '⚠️'

     # Display with status
     provider_options = {
         'langextract': f'{get_provider_status("langextract")} LangExtract (Google Gemini)',
         'openrouter': f'{get_provider_status("openrouter")} OpenRouter (Unified API)',
         # ... etc for all 8
     }
     ```

2. **Add model selector** (conditional display for multi-model providers):
   ```python
   # Show model dropdown for multi-model providers
   if selected_provider in ['openrouter', 'opencode_zen', 'openai', 'anthropic', 'deepseek', 'moonshot', 'zhipu']:
       # Load model registry for selected provider
       model_registry_path = f"config/models/{selected_provider}-models.json"

       try:
           with open(model_registry_path) as f:
               model_registry = json.load(f)

           # Extract model list with scores
           model_options = {}
           for model_id, model_data in model_registry.get('tested', {}).items():
               quality = model_data.get('quality_score', 0)
               cost = model_data.get('cost_per_million', 0)
               model_options[model_id] = f"{model_id} ({quality}/10, ${cost}/M)"

           selected_model = st.selectbox(
               "Select model:",
               options=list(model_options.keys()),
               format_func=lambda m: model_options[m],
               help="Models sorted by quality score from testing"
           )

           # Store in session state for processing
           st.session_state.selected_model = selected_model

       except FileNotFoundError:
           st.warning(f"⚠️ Model registry not found for {selected_provider}")
           st.info("Using default model from provider configuration")
   ```

3. **Add parser selector** (prepare for future parsers):
   ```python
   # In sidebar
   with st.sidebar:
       st.markdown("### Configuration")

       st.markdown("**Document Parser**")
       parser_options = {
           'docling': 'Docling (Current Baseline)',
           # Future: 'unstructured', 'llamaparse', 'pymupdf', 'marker'
       }

       selected_parser = st.radio(
           "Select parser:",
           options=list(parser_options.keys()),
           format_func=lambda x: parser_options[x],
           help="Document parsing engine (currently Docling only)\nFuture: Unstructured.io, LlamaParse, PyMuPDF, Marker",
           disabled=len(parser_options) == 1  # Disable if only one option
       )

       st.session_state.selected_parser = selected_parser
   ```

4. **Add configuration persistence**:
   ```python
   # Initialize session state defaults
   if 'selected_parser' not in st.session_state:
       st.session_state.selected_parser = 'docling'

   if 'selected_provider' not in st.session_state:
       default_provider = os.getenv('EVENT_EXTRACTOR', 'langextract').lower()
       st.session_state.selected_provider = default_provider

   if 'selected_model' not in st.session_state:
       st.session_state.selected_model = None

   # Clear results when configuration changes
   def clear_results_on_config_change():
       if 'legal_events_df' in st.session_state:
           del st.session_state.legal_events_df
           st.info("🔄 Configuration changed - previous results cleared")

   # Watch for changes
   if (st.session_state.selected_parser != selected_parser or
       st.session_state.selected_provider != selected_provider or
       st.session_state.get('selected_model') != selected_model):
       clear_results_on_config_change()
   ```

5. **Add provider health checks**:
   ```python
   def validate_provider_config(provider):
       """Quick API key validation before processing"""
       env_vars = {
           'langextract': 'GEMINI_API_KEY',
           'openrouter': 'OPENROUTER_API_KEY',
           'opencode_zen': 'OPENCODEZEN_API_KEY',
           'openai': 'OPENAI_API_KEY',
           'anthropic': 'ANTHROPIC_API_KEY',
           'deepseek': 'DEEPSEEK_API_KEY',
           'moonshot': 'MOONSHOT_API_KEY',
           'zhipu': 'ZHIPU_API_KEY',
       }

       api_key = os.getenv(env_vars[provider])
       if not api_key:
           st.error(f"❌ {provider.upper()} API key not found")
           st.info(f"Please set {env_vars[provider]} in your .env file")
           st.code(f"# Run diagnostic script to test configuration:\n"
                   f"uv run python scripts/test_{provider}.py")
           return False
       return True

   # Before processing
   if st.button("Process Files", type="primary"):
       if not validate_provider_config(st.session_state.selected_provider):
           st.stop()  # Don't proceed if provider not configured
       # ... continue with processing
   ```

6. **Add combination preset selector** (optional advanced feature):
   ```python
   # Advanced: Allow users to load preset combinations
   with st.expander("⚙️ Advanced: Load Preset Combination"):
       combination_files = glob.glob("config/combinations/*.json")
       combination_options = [os.path.basename(f).replace('.json', '')
                             for f in combination_files]

       selected_combo = st.selectbox(
           "Load combination preset:",
           options=['Custom'] + combination_options,
           help="Load a pre-tested parser+extractor combination"
       )

       if selected_combo != 'Custom':
           # Load and apply combination config
           with open(f"config/combinations/{selected_combo}.json") as f:
               combo_config = json.load(f)

           st.session_state.selected_parser = combo_config['parser']['type']
           st.session_state.selected_provider = combo_config['extractor']['type']
           st.session_state.selected_model = combo_config['extractor'].get('model')

           st.success(f"✅ Loaded preset: {combo_config['description']}")
   ```

**Deliverables**:
- Updated `app.py` with 8-provider selector (already done in Phase 2.5)
- Model selector for multi-model providers (conditional display)
- Parser selector (single option currently, prep for future)
- Configuration persistence in session state
- Provider health check UI with clear error messages
- Provider status indicators (✅ configured / ⚠️ missing API key)
- Optional: Combination preset loader for advanced users

**Acceptance Criteria**:
- ✅ UI shows all 8 providers in radio buttons with status indicators
- ✅ Model selector appears conditionally for multi-model providers
- ✅ Parser selector displays (even with single option)
- ✅ Selections persist across page actions (session state)
- ✅ Clear error messages for missing API keys
- ✅ Provider health check prevents processing with invalid config
- ✅ Results clear when configuration changes
- ✅ Combination presets loadable (optional)

---

### Phase 4: Baseline Testing

**Goal**: Establish current performance metrics

**Tasks**:
1. Prepare test dataset:
   - Select 10-20 representative legal documents
     - Document type variety: Leases, contracts, court filings, legislation
     - Complexity variety: Simple (2-page) to complex (50+ page)
     - Event density variety: Sparse (1-3 events) to dense (50+ events)
     - Format variety: PDF (native), PDF (scanned), DOCX, HTML
   - Create ground truth annotations (JSON schema for legal events)
   - Document expected events with detailed descriptions
   - Version control ground truth (track changes and corrections)

2. Benchmark 8 provider combinations (all with Docling parser):
   - **Gateway APIs**:
     - Docling + LangExtract (Gemini 2.0 Flash) — shipped default baseline
     - Docling + OpenRouter (GPT-4o-mini) — unified API baseline
     - Docling + OpenCode Zen (code-supernova) — free tier baseline

   - **Direct APIs** (NEW):
     - Docling + OpenAI Direct (GPT-4o-mini)
     - Docling + Anthropic Direct (Claude 3 Haiku)
     - Docling + DeepSeek Direct (R1)
     - Docling + Moonshot (Kimi K2)
     - Docling + Zhipu (GLM-4)

3. Expanded model variation testing (20+ combinations):
   - **OpenRouter**: Test top 5 models
     - GPT-4o-mini (9/10, $0.15/M) — recommended
     - DeepSeek R1 Distill (10/10, $0.03/M) — budget champion
     - Claude 3 Haiku (10/10, $0.25/M) — balanced
     - GPT-3.5-turbo (10/10, $0.50/M) — legacy
     - GPT-4o (10/10, $2.50/M) — premium

   - **OpenAI Direct**: Test 3 models
     - GPT-4o-mini vs GPT-4o vs GPT-3.5-turbo
     - Compare direct API vs OpenRouter pricing/performance

   - **Anthropic Direct**: Test 3 models
     - Claude 3 Haiku vs Claude 3.5 Sonnet vs Claude 3 Opus
     - Compare cost/quality tradeoff

   - **DeepSeek Direct**: Test 2 models
     - DeepSeek R1 (reasoner) vs DeepSeek V3
     - Compare direct API vs OpenRouter's distilled R1

   - **Moonshot**: Test K2 vs K2-Instruct (long-context focus)
   - **Zhipu**: Test GLM-4 vs GLM-4-Air (cost/quality tradeoff)

4. Document results and identify champions by category:
   - **Quality Champion**: Best precision/recall/F1 score across all tests
   - **Cost Champion**: Lowest $/document while maintaining quality ≥7/10
   - **Speed Champion**: Fastest processing time while maintaining quality ≥7/10
   - **Free Tier Champion**: Best quality among free options (code-supernova baseline)
   - **Balanced Champion**: Best quality/cost/speed tradeoff (weighted scoring)
   - **Use Case Recommendations**:
     - High-stakes legal work: Quality champion (regardless of cost)
     - High-volume processing: Cost champion (budget-conscious)
     - Real-time applications: Speed champion (latency-sensitive)
     - Prototype/testing: Free tier champion (no cost)
     - Production default: Balanced champion (general use)

**Deliverables**:
- Test dataset with ground truth (10-20 documents, version-controlled)
- 8-provider baseline benchmark results (Docling + all 8 extractors)
- 20+ model variation benchmark results
- Champion configurations identified for each category
- Recommendation matrix by use case
- Detailed comparison report (markdown + CSV)
- Results saved to `config/benchmarks/2025-10-XX_8provider_comparison.json`

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

### Core Infrastructure
- ✅ Can run benchmark with single command: `uv run python scripts/benchmark_combinations.py`
- ✅ Results are reproducible (same config = same results)
- ✅ Easy to add new parsers (config file + adapter class, no refactoring)
- ✅ Easy to test new models (just config change, no code change)
- ✅ All configs version-controlled (track all experiments in git)
- ✅ Clear winners identified for quality, cost, speed, and free tier

### 8-Provider Support
- ✅ **8 Provider Support**: LangExtract, OpenRouter, OpenCode Zen, OpenAI, Anthropic, DeepSeek, Moonshot, Zhipu
- ✅ **User Selection UI**: Streamlit allows parser + extractor + model selection with status indicators
- ✅ **Direct API Testing**: All 5 direct APIs pass 10/10 diagnostic validation
- ✅ **Champion Identification**: Clear winners by quality/cost/speed/free tier categories
- ✅ **Preset Combinations**: Shareable config files for winning combinations (version-controlled)

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

### `config/extractors/gateways/openrouter.json`
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
    "config_file": "config/extractors/gateways/langextract.json",
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

### Diagnostic Scripts Created and Planned

#### Gateway API Testing (Implemented: 2025-10-01 to 2025-10-02)
- `scripts/test_openrouter.py` - OpenRouter validation (10 checks, ✅ passes)
- `scripts/test_deepseek.py` - DeepSeek via OpenRouter (10 checks, ✅ passes)
- `scripts/test_all_models.py` - Multi-model comparison (5 models side-by-side)
- `scripts/test_fallback_models.py` - Comprehensive testing (18 OpenRouter models, 11 with 10/10)
- `scripts/test_opencode_zen.py` - OpenCode Zen validation (10 checks, ✅ passes)
- `scripts/test_opencode_zen_models.py` - Comprehensive testing (4 OpenCode Zen models, 2 with 8/10)

#### Direct API Testing (Planned: Phase 2.5)
- `scripts/test_openai.py` - OpenAI direct API validation (10 checks, ⏳ planned)
- `scripts/test_anthropic.py` - Anthropic direct API validation (10 checks, ⏳ planned)
- `scripts/test_deepseek_direct.py` - DeepSeek direct API validation (10 checks, ⏳ planned, distinct from OpenRouter)
- `scripts/test_moonshot.py` - Moonshot/Kimi K2 validation (10 checks, ⏳ planned)
- `scripts/test_zhipu.py` - Zhipu/ChatGLM validation (10 checks, ⏳ planned)

#### Model Testing Scripts (Planned: Phase 2.5)
- `scripts/test_openai_models.py` - Comprehensive OpenAI model testing (4+ models)
- `scripts/test_anthropic_models.py` - Comprehensive Anthropic model testing (3+ models)
- `scripts/test_deepseek_models.py` - Comprehensive DeepSeek model testing (3+ models)
- `scripts/test_moonshot_models.py` - Comprehensive Moonshot model testing (3+ models)
- `scripts/test_zhipu_models.py` - Comprehensive Zhipu model testing (3+ models)

**Total Diagnostic Scripts**: 6 implemented + 5 planned = **11 diagnostic scripts**
**Total Model Testing Scripts**: 2 implemented + 5 planned = **7 model testing scripts**
