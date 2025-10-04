# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Mantras

- **Start small, scale smart** - Land the simplest working version before expanding scope
- **Prove value fast** - Deliver end-user gains ahead of infrastructure rewrites
- **Design for the next plug** - Every new chunk should snap into the existing pipeline with minimal glue
- **Keep it boring** - Favor clear, well-understood patterns over clever abstractions
- **Own the blast radius** - Guardrails belong near the upload—fail fast and document why
- **Surface reality** - Log classification scores, extraction outcomes, and review warnings so humans stay in the loop
- **Respect the prompt contract** - One prompt (`LEGAL_EVENTS_PROMPT`), one schema; change it deliberately and update every consumer
- **Measure before you optimize** - Let data expose bottlenecks or costs before re-architecting
- **Leave breadcrumbs** - Docstrings, comments, and docs explain why a choice exists, not just how it works
- **Ship with toggles** - Feature flags and environment switches let us test without breaking the happy path
## Project Overview

This is a **proof-of-concept testing environment** for evaluating combinations of Docling (document processing) + pluggable event extractors (legal event extraction) for paralegal applications. The core pipeline: Documents In → Legal Events Out.

**Event Extractors Supported**:
- **LangExtract** (Gemini) - Default, uses Google's Gemini 2.0 Flash
- **OpenRouter** (Unified API) - 11+ tested models from OpenAI, Anthropic, DeepSeek
- **OpenCode Zen** (Legal AI) - Specialized legal extraction models
- **OpenAI** (Direct API) - GPT-4o, GPT-4o-mini via OpenAI SDK

**Provider Selection**: Use Streamlit UI dropdown (overrides environment) or set `EVENT_EXTRACTOR` environment variable.

**Architecture**: Registry pattern in `extractor_factory.py` - add new providers by implementing `EventExtractor` interface and registering in `EVENT_PROVIDER_REGISTRY`.

**Key Goal**: Test which parser+extractor combination can reliably extract legal events from various document types.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Install Tesseract OCR (recommended - 3x faster than EasyOCR)
# macOS
brew install tesseract
export TESSDATA_PREFIX=/usr/local/opt/tesseract/share/tessdata

# OR Linux (Ubuntu/Debian)
sudo apt install tesseract-ocr libtesseract-dev
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Create environment file from template
cp .env.example .env
# Then edit .env with real API keys:
#   - GEMINI_API_KEY (required for LangExtract)
#   - OPENROUTER_API_KEY (optional, for OpenRouter)
#   - OPENCODEZEN_API_KEY (optional, for OpenCode Zen)
```

### Running Applications
```bash
# Main app (provider selector, supports LangExtract/OpenRouter/OpenCode Zen/OpenAI)
uv run streamlit run app.py

# Legacy examples for specific scenarios
uv run streamlit run examples/legal_events_app.py
uv run streamlit run examples/simple_legal_table_app.py
```

### Testing
```bash
# Complete test suite with detailed reporting
uv run python tests/run_all_tests.py

# Quick tests (skip performance benchmarks)
uv run python tests/run_all_tests.py --quick

# Individual test suites
uv run python -m pytest tests/test_acceptance_criteria.py -v
uv run python -m pytest tests/test_performance_integration.py -v

# Single test case (useful for debugging)
uv run python -m pytest tests/test_acceptance_criteria.py::AcceptanceCriteriaTests::test_docling_extraction -v
```

### Diagnostic Scripts
```bash
# Provider connectivity checks (quick validation)
uv run python scripts/check_langextract.py
uv run python scripts/check_openrouter.py
uv run python scripts/check_opencode_zen.py

# Comprehensive provider testing (10-level validation)
uv run python scripts/test_openrouter.py
uv run python scripts/test_opencode_zen.py

# Model comparison and benchmarking
uv run python scripts/test_all_models.py          # Side-by-side 5-model comparison
uv run python scripts/test_fallback_models.py     # 18 OpenRouter models test
uv run python scripts/test_opencode_zen_models.py # OpenCode Zen models test
uv run python scripts/test_deepseek.py            # DeepSeek R1 specific testing

# Verification utilities
uv run python scripts/verify_langextract_examples.py
uv run python scripts/probe_opencode_zen.py
```

## Core Architecture

### Pipeline Flow
```
Document Upload → DoclingAdapter → Text Extraction → EventExtractor → Five-Column Table
                                                            ↓
                                                    Provider Registry
                                                    (langextract, openrouter, etc.)
```

### Protocol-Based Design
The system uses **Protocol interfaces** (PEP 544) for swappable components:

- **`DocumentExtractor`** (`src/core/interfaces.py`) - Returns `ExtractedDocument(markdown, plain_text, metadata)`
- **`EventExtractor`** (`src/core/interfaces.py`) - Returns `List[EventRecord]` with five-column schema

### Provider Registry Pattern
New extractors are added via **registry pattern** in `extractor_factory.py`:

```python
EVENT_PROVIDER_REGISTRY: Dict[str, Callable] = {
    "langextract": _create_langextract_event_extractor,
    "openrouter": _create_openrouter_event_extractor,
    "opencode_zen": _create_opencode_zen_event_extractor,
    "openai": _create_openai_event_extractor,
}
```

To add a new provider:
1. Create adapter implementing `EventExtractor` protocol
2. Add factory function to registry
3. Add config dataclass to `config.py`
4. Update `load_provider_config()` to handle new provider type

### The Prompt Contract
**Critical**: `LEGAL_EVENTS_PROMPT` in `src/core/constants.py` defines the extraction schema. All providers must return this exact JSON structure:

```json
{
  "event_particulars": "2-8 sentence description with legal context",
  "citation": "Legal reference or empty string (NO hallucinations)",
  "document_reference": "Source filename (auto-populated)",
  "date": "Specific date or empty string"
}
```

These map to the **Five-Column Table**:
1. No (sequence number)
2. Date
3. Event Particulars
4. Citation
5. Document Reference

**When modifying the prompt**:
- Update `LEGAL_EVENTS_PROMPT` in `constants.py` (single source of truth)
- All adapters use this same prompt via import
- Test with all providers before committing changes

### Configuration System

#### Provider Selection
- `EVENT_EXTRACTOR`: Choose provider (`langextract`|`openrouter`|`opencode_zen`|`openai`)
- Streamlit UI selector overrides environment variable
- Each provider requires provider-specific API key (see `.env.example`)

#### Key Environment Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | _(required for LangExtract)_ | Google Gemini access |
| `GEMINI_MODEL_ID` | `gemini-2.0-flash` | Override default model |
| `OPENROUTER_API_KEY` | _(required for OpenRouter)_ | Multi-provider unified API |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Budget: `deepseek/deepseek-r1-distill-llama-70b` ($0.03/M) |
| `OPENAI_API_KEY` | _(required for OpenAI)_ | Direct OpenAI API access |
| `OPENAI_MODEL` | `gpt-4o-mini` | GPT-4o or GPT-4o-mini |
| `DOCLING_DO_OCR` | `true` | Enable/disable OCR |
| `DOCLING_TABLE_MODE` | `FAST` | `FAST` or `ACCURATE` |
| `DOCLING_ACCELERATOR_DEVICE` | `cpu` | `cpu`, `cuda`, or `mps` |

**Tested Model Recommendations** (2025-10-01):
- Budget champion: `deepseek/deepseek-r1-distill-llama-70b` via OpenRouter ($0.03/M, 10/10 quality)
- Recommended default: `openai/gpt-4o-mini` via OpenRouter ($0.15/M, 10/10 quality)
- See `.env.example` for 11+ tested models with quality scores

## Development Guidelines

### Core Principles
1. **Proof-of-Concept Focus**: Stay within "documents in → legal events out" scope
2. **No Fake Extractors**: Never mock extractor success without real API calls - if a provider fails, report it clearly
3. **Respect Configuration**: Honor Streamlit toggles and environment variables
4. **Guard Sample Data**: Use small test snippets, avoid large synthetic documents

### Thinking Mode
- Always use deep reasoning for complex problems
- For architectural decisions, performance optimization, or unfamiliar codebase analysis, apply maximum thinking budget
- When uncertain about approach, think through alternatives thoroughly

### Test Data Guidelines
**Real legal documents are already in the repo** - use existing files for testing:

#### Case-Based Test Files (Organized by Legal Matter)

- **`sample_pdf/amrapali_case/`** (34MB, 9 PDFs)
  - Real estate transaction in India with buyer agreements, bank statements, affidavits
  - Large documents (one is 17MB) - good for stress testing
  - Use `Amrapali Allotment Letter.pdf` (1.4MB) for quick real-world tests

- **`sample_pdf/famas_dispute/`** (2.3MB, 7 files: 2 PDF + 4 EML + 1 DOCX)
  - International arbitration case (Famas GmbH vs Elcomponics Sales)
  - **Best for manual quality evaluation**: `Answer to Request for Arbitration.pdf` (930KB, ~15 pages)
  - Mix of document formats - tests parser versatility
  - Recommended for Phase 2 provider comparison testing

- **`tests/test_documents/`** (28KB, 6 files)
  - Synthetic HTML files with edge cases (ambiguous dates, multiple events, no dates)
  - Small PDF for quick unit tests
  - Use for automated testing, not manual review

**When to use what**:
- Quick adapter test → `sample_pdf/famas_dispute/Answer to Request for Arbitration.pdf` (~15 pages, real legal events)
- Provider comparison → Same Famas arbitration PDF (medium complexity, not overwhelming)
- Stress test → `sample_pdf/amrapali_case/Amrapali Builder Buyer Agreement.pdf` (17MB)
- Edge case validation → `tests/test_documents/*.html` files

All sample files are tracked in git for reproducible testing across environments.

### Testing Legal Events Extraction
When testing LangExtract integration, use this minimal example from the README:

```python
import os
from dotenv import load_dotenv
import langextract as lx

load_dotenv()

legal_text = """
This Lease Agreement is entered into on September 21, 2025. The lease begins on
October 1, 2025 and rent is due on the 5th of every month.
""".strip()

examples = [
    lx.data.ExampleData(
        text="This contract was signed on March 15, 2024 and becomes effective on April 1, 2024.",
        extractions=[
            lx.data.Extraction(
                extraction_class="contract_date",
                extraction_text="March 15, 2024",
                attributes={"normalized_date": "2024-03-15", "type": "signing_date"},
            ),
        ],
    )
]

response = lx.extract(
    text_or_documents=legal_text,
    prompt_description="Extract every legally meaningful date and provide a normalized ISO date.",
    examples=examples,
    model_id="gemini-2.0-flash",
    api_key=os.environ["GEMINI_API_KEY"],
)
```

### File Structure Understanding
- **Root level**: Multiple Streamlit apps for different testing scenarios
- **`src/core/`**: Core pipeline logic, interfaces, and configuration
- **`src/extractors/`**: Individual extractor implementations (legacy - do not add new extractors here)
- **`src/ui/`**: Shared Streamlit UI components
- **`src/utils/`**: File handling utilities
- **`tests/`**: Acceptance criteria and performance tests
- **`docs/`**: Design documents, architecture decisions, and project orders
- **`scripts/`**: Development utilities and troubleshooting guides

### Adding New Event Extractors
1. Create adapter in `src/core/` (not `src/extractors/` - that's legacy) implementing `EventExtractor` protocol:
   ```python
   class MyProviderAdapter:
       def extract_events(self, text: str, metadata: Dict) -> List[EventRecord]:
           # Must return EventRecord with five-column schema

       def is_available(self) -> bool:
           # Check API key exists
   ```

2. Add factory function and register in `extractor_factory.py`:
   ```python
   def _create_myprovider_event_extractor(doc_config, event_config, extractor_config):
       return MyProviderAdapter(event_config)

   EVENT_PROVIDER_REGISTRY["myprovider"] = _create_myprovider_event_extractor
   ```

3. Add config class to `config.py` and update `load_provider_config()`

4. Test with real legal PDF using diagnostic script pattern (see `scripts/test_openrouter.py`)

This architecture enables A/B testing, gradual migrations, and vendor flexibility without changing core application logic.

## Key Files Reference

### Critical Architecture Files
| File | Purpose |
|------|---------|
| `src/core/constants.py` | **LEGAL_EVENTS_PROMPT** (single source of truth for extraction schema) |
| `src/core/interfaces.py` | Protocol definitions for DocumentExtractor and EventExtractor |
| `src/core/extractor_factory.py` | **EVENT_PROVIDER_REGISTRY** (add new providers here) |
| `src/core/config.py` | Configuration dataclasses and environment loading |
| `src/core/legal_pipeline_refactored.py` | Main pipeline orchestration |

### Adapter Implementations
- `src/core/docling_adapter.py` - Document text extraction (PDF/DOCX/HTML/PPTX)
- `src/core/langextract_adapter.py` - Gemini 2.0 Flash event extraction
- `src/core/openrouter_adapter.py` - Multi-provider unified API (11+ models)
- `src/core/opencode_zen_adapter.py` - Legal AI specialized extraction
- `src/core/openai_adapter.py` - Direct OpenAI API integration

### Testing Infrastructure
- `tests/run_all_tests.py` - Master test suite runner with reporting
- `tests/test_acceptance_criteria.py` - Core functionality validation
- `tests/test_performance_integration.py` - Performance benchmarks
- `scripts/test_fallback_models.py` - Provider comparison framework (18 models tested)
- when planning try to be updated on api and library documentation by researching the internet