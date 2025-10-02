# Repository Guidelines

## Project Structure & Module Organization
- `src/core/` steers the Docling→legal-events pipeline with pluggable extractors; `src/core/extractor_factory.py` switches among registered providers (LangExtract, OpenRouter, OpenCode Zen). Legacy `extractors/` wraps vendor APIs, while shared helpers sit in `utils/`, `ui/`, and `visualization/` for Streamlit rendering.
- Top-level `app.py` launches the primary Streamlit UI, and `examples/` houses alternative demos such as `examples/legal_events_app.py`.
- CLI entry points live in `src/main.py`; generated artifacts and logs land in `output/` for manual review.
- Supporting references stay in `docs/`, troubleshooting scripts in `scripts/`, and tests plus fixtures in `tests/`.

## Build, Test, and Development Commands
- `uv sync` installs project dependencies pinned in `pyproject.toml` and `uv.lock`.
- `uv run streamlit run app.py` starts the main UI; swap in an `examples/*.py` path to explore focused demos.
- `uv run python src/main.py` executes the CLI harness for scripted LangExtract runs.
- `uv run python tests/run_all_tests.py --quick` runs the smoke suite; drop `--quick` for full coverage or target pytest modules (e.g., `uv run python -m pytest tests/test_acceptance_criteria.py -v`).

## Coding Style & Naming Conventions
- Use 4-space indentation, type hints, and descriptive docstrings consistent with `src/core/interfaces.py`.
- Favor `snake_case` for functions, ALL_CAPS for module constants, and `PascalCase` for classes.
- Keep event schema constants centralized in `src/core/constants.py` and expose new configuration through existing dataclasses, not literals.
- Break complex Streamlit callbacks into helper functions to preserve readability and reuse.

## Multi-Provider Event Extraction System
- **Provider Selection**: Set `EVENT_EXTRACTOR` environment variable to choose between `langextract` (default), `openrouter`, or `opencode_zen`.
- **Configuration**: Each provider requires its own API key and configuration (see `.env.example` for all options).
- **Registry Pattern**: New providers are registered in `src/core/extractor_factory.py` via `EVENT_PROVIDER_REGISTRY`.
- **Testing**: Provider-specific tests automatically skip when credentials are unavailable; use mocked responses for unit tests.

### Provider Setup Examples:
```bash
# LangExtract (default)
export EVENT_EXTRACTOR=langextract
export GEMINI_API_KEY=your_key_here

# OpenRouter
export EVENT_EXTRACTOR=openrouter
export OPENROUTER_API_KEY=your_key_here

# OpenCode Zen
export EVENT_EXTRACTOR=opencode_zen
export OPENCODEZEN_API_KEY=your_key_here
```

## Testing Guidelines
- Most suites require provider-specific API keys in `.env`; copy `.env.example` as a starting point.
- Name tests `test_*.py` and echo acceptance IDs (e.g., `AC-00X`) in logs for traceability.
- Store sample documents in `tests/test_documents/` and document any mocked provider flows inside the test module.
- Capture JSON evidence with `uv run python tests/run_all_tests.py --report` when preparing verification artifacts.

## Security & Configuration Tips
- Keep secrets out of version control and prefer environment variables or `ExtractorConfig` toggles over hard-coded switches.
- Adjust performance via variables like `DOCLING_TABLE_MODE` and `LANGEXTRACT_MAX_WORKERS` instead of modifying vendor adapters.
- Review `SECURITY.md` before introducing new dependencies or telemetry pathways.

## Commit & Pull Request Guidelines
- Write present-tense, task-focused commits (e.g., "Add Docling adapter metrics") and group related pipeline edits together.
- Reference acceptance IDs, executed scripts, or test commands in commit bodies and PR descriptions.
- Summarize behavioral changes, attach screenshots or terminal captures for UI updates, and link tracking issues when available.
- Remove temporary debug assets before requesting review to keep diffs clean.
