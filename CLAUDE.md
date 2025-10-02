# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **proof-of-concept testing environment** for evaluating combinations of Docling (document processing) + pluggable event extractors (legal event extraction) for paralegal applications. The core pipeline: Documents In → Legal Events Out.

**Event Extractors Supported**: LangExtract (Gemini), OpenRouter (unified API with 11+ models), OpenCode Zen (legal AI). The `ExtractorFactory` (`src/core/extractor_factory.py`) selects between providers based on user selection or environment configuration.

**Key Goal**: Test which parser+extractor combination can reliably extract legal events from various document types.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Create environment file from template
cp .env.example .env
# Then edit .env with real GEMINI_API_KEY
```

### Running Applications
```bash
# Main Streamlit app (primary interface)
uv run streamlit run app.py

# Alternative apps for different testing scenarios
uv run streamlit run examples/legal_events_app.py
uv run streamlit run examples/simple_legal_table_app.py
uv run streamlit run examples/guaranteed_table_app.py

# Command-line interface
uv run python src/main.py
```

### Testing
```bash
# Run all tests
uv run python tests/run_all_tests.py

# Run acceptance tests
uv run python -m pytest tests/test_acceptance_criteria.py -v

# Run performance integration tests
uv run python -m pytest tests/test_performance_integration.py -v
```

### Development Utilities
```bash
# Verify LangExtract examples and configuration
uv run python scripts/verify_langextract_examples.py

# Test LangExtract API directly
uv run python test_langextract_api.py

# Run individual test files
uv run python -m pytest tests/test_acceptance_criteria.py -v
uv run python -m pytest tests/test_performance_integration.py -v

# Quick tests without performance benchmarks
uv run python tests/run_all_tests.py --quick

# Test without generating reports
uv run python tests/run_all_tests.py --no-report
```

## Core Architecture

### Modular Pipeline Design
The system uses **adapter interfaces** to enable swapping of components:

- **DocumentExtractor** (`src/core/interfaces.py`): Interface for text extraction (currently Docling)
- **EventExtractor** (`src/core/interfaces.py`): Interface for legal events extraction (currently LangExtract)
- **ExtractorFactory** (`src/core/extractor_factory.py`): Creates configured extractors

### Key Components

#### Document Processing Pipeline
- **DoclingAdapter** (`src/core/docling_adapter.py`): Extracts text from PDF, DOCX, TXT, PPTX, HTML
- **LangExtractAdapter** (`src/core/langextract_adapter.py`): Extracts legal events using Gemini 2.0 Flash
- **LegalPipeline** (`src/core/legal_pipeline_refactored.py`): Orchestrates the complete pipeline

#### Standardized Output Format
All legal events must conform to the **Five-Column Table** format defined in `src/core/constants.py`:
1. **No** (Event number)
2. **Date** (Extracted date or empty string)
3. **Event Particulars** (2-8 sentences with comprehensive legal context)
4. **Citation** (Legal reference or empty string)
5. **Document Reference** (Source filename)

#### Prompt Contract
The `LEGAL_EVENTS_PROMPT` in `src/core/constants.py` enforces consistent JSON schema for all extractions:
```json
{
  "event_particulars": "Complete 2-8 sentence description with legal context",
  "citation": "Legal citation or empty string",
  "document_reference": "Automatically filled with filename",
  "date": "Specific date or empty string"
}
```

### Configuration System

Environment variables control behavior without code changes:

#### LangExtract Configuration
- `GEMINI_API_KEY`: **Required** - Google API key for Gemini access
- `GEMINI_MODEL_ID`: Override default model (default: `gemini-2.0-flash`)
- `LANGEXTRACT_TEMPERATURE`: Model temperature (default: `0.0`)
- `LANGEXTRACT_MAX_WORKERS`: Parallel workers (default: `10`)

#### Docling Configuration
- `DOCLING_DO_OCR`: Enable/disable OCR (default: `true`)
- `DOCLING_TABLE_MODE`: `FAST` or `ACCURATE` (default: `FAST`)
- `DOCLING_BACKEND`: `default` or `v2` (default: `default`)
- `DOCLING_ACCELERATOR_DEVICE`: `cpu`, `cuda`, or `mps` (default: `cpu`)

#### Extractor Selection
- `DOC_EXTRACTOR`: Document extractor type (default: `docling`)
- `EVENT_EXTRACTOR`: Event extractor type (default: `langextract`)

## Development Guidelines

### Core Principles
1. **Proof-of-Concept Focus**: Stay within "documents in → legal events out" scope
2. **No Fake LangExtract**: Never mock LangExtract success without real API calls
3. **Respect Configuration**: Honor Streamlit toggles and environment variables
4. **Guard Sample Data**: Use small test snippets, avoid large synthetic documents
## Thinking Mode
- Always use deep reasoning for complex problems
- For architectural decisions, performance optimization, or unfamiliar codebase analysis, apply maximum thinking budget
- When uncertain about approach, think through alternatives thoroughly
  
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
- **`src/extractors/`**: Individual extractor implementations (legacy)
- **`src/ui/`**: Shared Streamlit UI components
- **`src/utils/`**: File handling utilities
- **`tests/`**: Acceptance criteria and performance tests

### Adding New Extractors
1. Implement `DocumentExtractor` or `EventExtractor` interface
2. Register in `src/core/extractor_factory.py`
3. Add environment variable configuration
4. Update factory selection logic

This architecture enables A/B testing, gradual migrations, and vendor flexibility without changing core application logic.

## Important File Paths and Resources

### API Configuration
- API keys are stored in `.env` - if missing, advise user to edit `.env` with real `GEMINI_API_KEY`
- Use `.env.example` as template for environment setup

### Test Resources
- Sample PDFs for testing: `/Users/aks/docling_langextract_testing/sample_pdf/`
- Test documents directory: `tests/test_documents/` (for HTML test files)
- Use these sample files for testing document processing functionality

### Key Configuration Files
- **Core constants**: `src/core/constants.py` - Contains `LEGAL_EVENTS_PROMPT` and `FIVE_COLUMN_HEADERS`
- **Interface definitions**: `src/core/interfaces.py` - Abstract interfaces for all extractors
- **Factory pattern**: `src/core/extractor_factory.py` - Creates configured extractors
- **Main pipeline**: `src/core/legal_pipeline_refactored.py` - Orchestrates full document processing