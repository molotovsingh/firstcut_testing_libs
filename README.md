# ⚖️ Paralegal Date Extraction Test

**Testing docling + langextract combination for paralegal application**

## 🚨 SECURITY NOTICE

**⚠️ IMPORTANT: API Key Security**

This project requires a Google API key for LangExtract functionality. **NEVER commit API keys to version control.**

### Security Checklist:
- [ ] `.env` file contains placeholder, not real API key
- [ ] Real API key stored securely (environment variables, secret manager)
- [ ] `.env` file is properly excluded in `.gitignore`
- [ ] No API keys in commit history

### Safe Setup:
1. Copy `.env.example` to `.env`
2. Replace `your_google_api_key_here` with actual key
3. Verify `.env` is in `.gitignore` before committing

## 🎯 Purpose

**Legal Events Extraction:** Documents In → Five-Column Legal Events Table Out

This is a **proof-of-concept** to evaluate document parsing and AI-based legal event extraction for paralegal applications. The system extracts structured legal events with dates, event particulars, citations, and document references.

## 🧪 Test Scope

- **Core Pipeline:** [Docling](https://github.com/DS4SD/docling) for document parsing + Multiple AI providers for event extraction
- **Business Use Case:** Legal event extraction from court documents, contracts, correspondence, and legal filings
- **Goal:** Test parser + extractor combinations to identify optimal configurations for quality, cost, and speed
- **Provider Flexibility:** Supports LangExtract (Gemini), OpenRouter (11+ tested models), and OpenCode Zen with in-app provider switching

## 🚀 Quick Start

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Enter the project directory**:
   ```bash
   cd docling_langextract_testing
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Launch the test app**:
   ```bash
   uv run streamlit run app.py
   ```

5. **Open your browser** to: `http://localhost:8501`

## 🔄 Provider Selection

This system now supports **multiple event extraction providers** with two selection methods:

### 1. **In-App UI Selection** (Recommended)

The Streamlit application (`app.py`) includes a **provider selector** in the Processing panel that lets you switch between providers without restarting:

- **LangExtract** (Google Gemini) - Default provider
- **OpenRouter** (Unified API) - Access to multiple AI models
- **OpenCode Zen** (Legal AI) - Specialized legal extraction

**⚠️ Important**: Each provider requires **provider-specific** API keys. The pipeline validates only the key needed for your selected provider:

**Required API Keys (Provider-Specific):**
- **LangExtract**: `GEMINI_API_KEY` or `GOOGLE_API_KEY` (either one)
- **OpenRouter**: `OPENROUTER_API_KEY` (only OpenRouter key required)
- **OpenCode Zen**: `OPENCODEZEN_API_KEY` (only OpenCode Zen key required)

**How Validation Works:**
- Selecting LangExtract → Validates `GEMINI_API_KEY` only
- Selecting OpenRouter → Validates `OPENROUTER_API_KEY` only (no Gemini key needed)
- Selecting OpenCode Zen → Validates `OPENCODEZEN_API_KEY` only (no Gemini key needed)

If you switch providers, you only need the API key for that specific provider. The app will display a clear error message if the required key is missing.

The selector automatically initializes the pipeline with your chosen provider and displays required credentials in the tooltip.

### 2. **Environment Variable Override**

You can also set a default provider via the `EVENT_EXTRACTOR` environment variable:

```bash
# Use LangExtract (default)
export EVENT_EXTRACTOR=langextract
export GEMINI_API_KEY=your_google_api_key_here

# Use OpenRouter
export EVENT_EXTRACTOR=openrouter
export OPENROUTER_API_KEY=your_openrouter_api_key_here

# Use OpenCode Zen
export EVENT_EXTRACTOR=opencode_zen
export OPENCODEZEN_API_KEY=your_opencode_zen_api_key_here
```

**Note**: The Streamlit UI selector takes precedence over the environment variable during interactive sessions.

## 📊 What Gets Tested

### Core Pipeline:
1. **📄 Docling** - Extracts text from legal documents (PDF, DOCX, TXT, PPTX, HTML)
2. **🌍 Langextract** - Detects document language
3. **📅 Date Extraction** - Finds and normalizes dates (the key business value)

### Test Metrics:
- **Docling Success Rate** by file type
- **Date Extraction Results** (number of dates found)
- **Pipeline Success** (successful text extraction + date extraction)
- **Language Detection** accuracy

## 📁 Project Structure

```
docling_langextract_testing/
├── app.py               # Main Streamlit test application
├── src/main.py          # Command-line version (alternative)
├── .env.example         # Template for environment variables
├── pyproject.toml       # Project configuration
└── README.md            # This documentation
```

## 🏗️ Repository Structure

**Core Directories:**
- **`src/`** - Core pipeline logic, interfaces, and modular components
  - `core/` - Pipeline orchestration, interfaces, and configuration
  - `extractors/` - Individual extractor implementations
  - `ui/` - Shared Streamlit UI components
  - `utils/` - File handling utilities
  - `visualization/` - Data visualization components
- **`tests/`** - Comprehensive test suites and validation procedures
- **`examples/`** - Demo Streamlit applications (5 apps for different testing scenarios)
- **`docs/`** - Design documents, architecture decisions, and project orders
  - `adr/` - Architecture Decision Records
  - `orders/` - Active housekeeping orders for contributors
  - `reports/` - Completion reports and documentation
- **`scripts/`** - Development utilities and troubleshooting guides
- **`output/`** - Generated results and extracted data files

**Key Design Documents:**
- [📋 Pluggable Extractors PRD](docs/pluggable_extractors_prd.md) - Product requirements and specifications
- [🏛️ ADR-001: Pluggable Extractors](docs/adr/ADR-001-pluggable-extractors.md) - Architecture decision record

## 🔬 Test Results

The app provides:
- ✅ **Success/Failure** indicators for each library
- 📊 **Visual charts** showing performance by document type
- 📋 **Data export** of extracted dates
- 📈 **Success rate metrics**

## ⚠️ Important Notes

- This is a **TEST SCRIPT** - guaranteed five-column table output with fallback rows on failures
- **Multiple event extractors supported**: LangExtract (Gemini), OpenRouter, OpenCode Zen (select via UI)
- **Pure testing environment** to evaluate parser+extractor combinations
- Results help determine which combination suits paralegal applications

## 🤖 Assistant Guardrails

When using Claude (or any other AI helper) with this repository, keep it focused on the documented proof-of-concept scope:

- **Stay on mission:** Only propose or modify code that contributes directly to "documents in → legal events table out" testing. Skip unrelated refactors, new features, or production hardening.
- **No fake extractor usage:** Do not mark event extractors (LangExtract, OpenRouter, OpenCode Zen) as successful unless the real API is called. If API access is missing, halt and report the gap—do **not** introduce regex or other fallbacks.
- **Respect toggles and config:** Any automation must treat the Streamlit UI selections (provider choice, model selection) as the source of truth—no hard-coded overrides.
- **Guard sample data:** Avoid inventing or writing back large synthetic documents; use small snippets that illustrate test cases.
- **Document assumptions:** When APIs are mocked, call that out explicitly so downstream testing knows the difference.

## 🔌 This Is How LangExtract Can Be Pinged

The snippet below demonstrates a minimal end-to-end call against the real LangExtract extractor using the `GEMINI_API_KEY` defined in your `.env` file. It loads a short legal paragraph, supplies a concrete few-shot example, and prints the structured results returned by Gemini.

```python
import os
from dotenv import load_dotenv
import langextract as lx

load_dotenv()  # ensures GEMINI_API_KEY is available via environment

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
            lx.data.Extraction(
                extraction_class="effective_date",
                extraction_text="April 1, 2024",
                attributes={"normalized_date": "2024-04-01", "type": "effective_date"},
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

for item in response.extractions:
    attrs = item.attributes or {}
    print(item.extraction_class, "→", item.extraction_text, attrs.get("normalized_date"))
```

⚠️ Run this only when you have valid Gemini access—each invocation makes a real LLM call and may incur usage costs.

## 🚀 Gemini 2.0 Flash Model

This project now uses **Gemini 2.0 Flash** (`gemini-2.0-flash`) for enhanced legal event extraction capabilities. The newer model provides improved accuracy and better handling of complex legal document structures.

### Model Configuration

- **Default Model**: `gemini-2.0-flash` (configured in `src/core/constants.py`)
- **Environment Override**: Set `GEMINI_MODEL_ID` environment variable to use a different model
- **API Access**: Ensure your Google Cloud project has access to Gemini 2.0 Flash models

### Model Override Example

```bash
# Use a different model for testing
export GEMINI_MODEL_ID="gemini-2.0-flash"
uv run streamlit run app.py

# Use experimental model
export GEMINI_MODEL_ID="gemini-2.0-flash-exp"
uv run streamlit run app.py
```

**Note**: Different environments may require different model access. Use the environment variable override if your deployment environment has different model availability.

### ✅ Verified Active Configuration

**Current Status** (as of latest verification):
- ✅ Default model: `gemini-2.0-flash`
- ✅ Environment override: Not set (using default)
- ✅ API endpoints: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash`
- ✅ Extraction performance: 13 events extracted with 499-character descriptions

**Environment Variable Precedence:**
- If `GEMINI_MODEL_ID` is set → Uses that model (overrides default)
- If `GEMINI_MODEL_ID` is unset → Uses `DEFAULT_MODEL = "gemini-2.0-flash"`

**Troubleshooting Model Issues:**
```bash
# Check current environment
env | grep GEMINI_MODEL_ID

# Clear override to use default 2.0 Flash
unset GEMINI_MODEL_ID

# Verify model in logs
uv run python3 -c "from src.core.langextract_client import LangExtractClient; print(f'Model: {LangExtractClient().model_id}')"
```

## 📋 LangExtract Prompt Contract

This project enforces a **standardized prompt contract** for consistent legal events extraction. All LangExtract calls must return exactly four JSON keys to ensure reliable five-column table output.

### Required JSON Schema

Every extracted legal event must include these four keys:

```json
{
  "event_particulars": "Complete description (2-8 sentences) with comprehensive context, parties, procedural background, and implications",
  "citation": "Legal citation or reference (empty string if none exists)",
  "document_reference": "Source document filename (automatically set)",
  "date": "Specific date mentioned (empty string if not found)"
}
```

### Key Policies

- **Enhanced Context**: The `event_particulars` field requires 2-8 sentences as appropriate to provide comprehensive legal context for AI summarization
- **No Hallucinated Citations**: The `citation` field must remain empty (`""`) when no verbatim legal reference exists in the text
- **Anchored Document References**: The `document_reference` field is automatically populated with the source filename passed to the extraction method
- **Empty Strings for Missing Data**: Use empty strings (`""`) instead of placeholder text for missing values
- **Required Keys**: All four keys must be present in every extraction
- **Character Offsets**: When available from LangExtract, character offsets are captured in the raw payload for precise source attribution

### Implementation

The standardized prompt is defined in `src/core/constants.py` as `LEGAL_EVENTS_PROMPT` and used consistently across all LangExtract operations. This ensures:

- Consistent extraction format across the entire application
- No invented legal citations that could mislead users
- Reliable document reference tracking
- Maintainable prompt updates from a single location
- Enhanced context (2-8 sentences) for future GPT-5 integration and AI summarization
- Character offset capture when available for precise source attribution

### Example Output

```json
[
  {
    "event_particulars": "On January 15, 2024, the plaintiff filed a motion to dismiss the complaint pursuant to Rule 12(b)(6) of the Federal Rules of Civil Procedure. This motion challenges the legal sufficiency of the complaint, arguing that the plaintiff has failed to state a claim upon which relief can be granted. The filing of this motion suspends the defendant's obligation to file an answer until the court rules on the motion. If granted, the motion would result in dismissal of some or all claims without the need for further discovery or trial proceedings.",
    "citation": "Fed. R. Civ. P. 12(b)(6)",
    "document_reference": "legal_filing.pdf",
    "date": "2024-01-15"
  },
  {
    "event_particulars": "A settlement conference was scheduled for April 10, 2024, to facilitate negotiations between the parties before proceeding to trial. This judicial settlement conference will be overseen by a magistrate judge who will help the parties explore potential resolution of the dispute. The conference represents a crucial opportunity for both sides to assess the strengths and weaknesses of their positions and potentially reach a mutually agreeable resolution.",
    "citation": "",
    "document_reference": "legal_filing.pdf",
    "date": "2024-04-10"
  }
]
```

**Enhanced Context Features:**
- **Comprehensive Descriptions**: Each `event_particulars` contains 2-8 sentences with full legal context
- **Empty Citations**: The second event has an empty `citation` field since no legal reference was mentioned
- **Character Offsets**: When available, `char_start` and `char_end` attributes provide precise source location (hidden from table display)
- **GPT-5 Ready**: Rich context enables advanced AI summarization and analysis

## 🔧 Pluggable Pipeline Architecture

This project features a **modular, configurable pipeline** that allows easy swapping of document processing and event extraction components.

### Core Architecture

The system uses **adapter interfaces** to decouple processing logic from specific implementations:

- **DocumentExtractor**: Interface for text extraction (currently: Docling)
  - Returns `ExtractedDocument` with `markdown`, `plain_text`, and `metadata` fields
- **EventExtractor**: Interface for legal events extraction (currently: LangExtract)
  - Returns `EventRecord` instances with `attributes` field containing LangExtract metadata
- **ExtractorFactory**: Creates configured extractors based on environment settings

### Configuration Options

#### Docling Document Processing
Control Docling behavior via environment variables:

```bash
# OCR and table processing
DOCLING_DO_OCR=true                    # Enable/disable OCR (default: true)
DOCLING_DO_TABLE_STRUCTURE=true        # Enable table structure detection (default: true)
DOCLING_TABLE_MODE=FAST                # Table mode: FAST or ACCURATE (default: FAST)
DOCLING_DO_CELL_MATCHING=true          # Enable table cell matching (default: true)

# Backend and performance
DOCLING_BACKEND=default                # Backend: default or v2 (default: default)
DOCLING_ACCELERATOR_DEVICE=cpu         # Device: cpu, cuda, mps (default: cpu)
DOCLING_ACCELERATOR_THREADS=4          # Thread count (default: 4)
DOCLING_DOCUMENT_TIMEOUT=300           # Processing timeout in seconds (default: 300)

# Optional paths
DOCLING_ARTIFACTS_PATH=/path/to/cache  # Cache directory (optional)
```

#### LangExtract Event Processing
Configure LangExtract behavior:

```bash
# Model settings
GEMINI_MODEL_ID=gemini-2.0-flash       # Override default model (default: gemini-2.0-flash)
LANGEXTRACT_TEMPERATURE=0.0            # Model temperature (default: 0.0)
LANGEXTRACT_MAX_WORKERS=10             # Parallel workers (default: 10)
LANGEXTRACT_DEBUG=false                # Debug mode (default: false)

# Required API access
GEMINI_API_KEY=your_google_api_key_here
```

#### Extractor Selection
Choose different implementations:

```bash
# Component selection (for future extensibility)
DOC_EXTRACTOR=docling                  # Document extractor type (default: docling)
EVENT_EXTRACTOR=langextract             # Event extractor type (default: langextract)
```

These selections are now managed through the `ExtractorConfig` dataclass, providing type-safe configuration.

### Example: High-Performance Configuration

```bash
# Optimized for accuracy and performance
DOCLING_DO_OCR=true
DOCLING_TABLE_MODE=ACCURATE
DOCLING_BACKEND=v2
DOCLING_ACCELERATOR_DEVICE=cuda
DOCLING_ACCELERATOR_THREADS=8
DOCLING_DOCUMENT_TIMEOUT=600

GEMINI_MODEL_ID=gemini-2.0-flash
LANGEXTRACT_TEMPERATURE=0.0
LANGEXTRACT_MAX_WORKERS=20

uv run streamlit run app.py
```

### Adding New Extractors

The adapter pattern makes it easy to add new implementations:

1. **Implement the interface** (`DocumentExtractor` or `EventExtractor`)
2. **Register in factory** (`extractor_factory.py`)
3. **Configure via environment** variables

This design enables **A/B testing**, **gradual migrations**, and **vendor flexibility** without changing application logic.

### Environment Variables Quick Reference

| Variable | Default | Description |
|----------|---------|-------------|
| **Extractor Selection** |  |  |
| `DOC_EXTRACTOR` | `docling` | Document extractor type |
| `EVENT_EXTRACTOR` | `langextract` | Event extractor type (langextract, openrouter, opencode_zen) |
| **Docling Configuration** |  |  |
| `DOCLING_DO_OCR` | `true` | Enable/disable OCR |
| `DOCLING_DO_TABLE_STRUCTURE` | `true` | Enable table structure detection |
| `DOCLING_TABLE_MODE` | `FAST` | Table mode: FAST or ACCURATE |
| `DOCLING_DO_CELL_MATCHING` | `true` | Enable table cell matching |
| `DOCLING_BACKEND` | `default` | Backend: default or v2 |
| `DOCLING_ACCELERATOR_DEVICE` | `cpu` | Device: cpu, cuda, mps |
| `DOCLING_ACCELERATOR_THREADS` | `4` | Thread count |
| `DOCLING_DOCUMENT_TIMEOUT` | `300` | Processing timeout (seconds) |
| `DOCLING_ARTIFACTS_PATH` | _(unset)_ | Cache directory (optional) |
| **LangExtract Configuration** |  |  |
| `GEMINI_API_KEY` | _(required)_ | Google API key for Gemini |
| `GEMINI_MODEL_ID` | `gemini-2.0-flash` | Override default model |
| `LANGEXTRACT_TEMPERATURE` | `0.0` | Model temperature |
| `LANGEXTRACT_MAX_WORKERS` | `10` | Parallel workers |
| `LANGEXTRACT_DEBUG` | `false` | Debug mode |
| **OpenRouter Configuration** |  |  |
| `OPENROUTER_API_KEY` | _(required for OpenRouter)_ | OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API base URL |
| `OPENROUTER_MODEL` | `anthropic/claude-3-haiku` | OpenRouter model to use |
| `OPENROUTER_TIMEOUT` | `30` | Request timeout in seconds |
| **OpenCode Zen Configuration** |  |  |
| `OPENCODEZEN_API_KEY` | _(required for OpenCode Zen)_ | OpenCode Zen API key |
| `OPENCODEZEN_BASE_URL` | `https://api.opencode-zen.example/v1` | OpenCode Zen API base URL |
| `OPENCODEZEN_MODEL` | `opencode-zen/legal-extractor` | OpenCode Zen model to use |
| `OPENCODEZEN_TIMEOUT` | `30` | Request timeout in seconds |

**Note**: New extractors can be added by implementing the interfaces in `src/core/interfaces.py` and registering them in `src/core/extractor_factory.py`.

---

**Testing library combination for paralegal date extraction use case** ⚖️
