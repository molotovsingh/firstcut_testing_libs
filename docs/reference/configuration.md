# Configuration Reference

Central place for environment variables that control provider selection and behavior. Copy `.env.example` to `.env` and set values locally.

## Core Selection
- `DOC_EXTRACTOR`: Document extractor key. Default: `docling`.
- `EVENT_EXTRACTOR`: Event extractor key. Default: `langextract`.

## LangExtract (Gemini)
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Required for LangExtract.
- `GEMINI_MODEL_ID`: Overrides default model (see `src/core/constants.py`).
- `LANGEXTRACT_TEMPERATURE`: Float, default `0.0`.
- `LANGEXTRACT_MAX_WORKERS`: Int, default `10`.

## OpenRouter
- `OPENROUTER_API_KEY`: Required to enable OpenRouter adapter.
- `OPENROUTER_BASE_URL`: Default `https://openrouter.ai/api/v1`.
- `OPENROUTER_MODEL`: Model identifier to use.
- `OPENROUTER_TIMEOUT`: Seconds (optional), request timeout.

## OpenCode Zen
- `OPENCODEZEN_API_KEY`: Required to enable OpenCode Zen adapter.
- `OPENCODEZEN_BASE_URL`: API endpoint.
- `OPENCODEZEN_MODEL`: Model identifier to use.
- `OPENCODEZEN_TIMEOUT`: Seconds (optional), request timeout.

## Docling
- `DOCLING_DO_OCR`: Bool, default `true`.
- `DOCLING_DO_TABLE_STRUCTURE`: Bool, default `true`.
- `DOCLING_TABLE_MODE`: `FAST` or `ACCURATE`. Default `FAST`.
- `DOCLING_BACKEND`: `default` or `v2`. Default `default`.
- `DOCLING_ACCELERATOR_DEVICE`: `cuda` | `mps` | `cpu`. Default `cpu`.
- `DOCLING_ACCELERATOR_THREADS`: Int, default `4`.

Notes
- Keep secrets out of commits. `.env` must not be versioned.
- Prefer toggles and config over hard-coded literals. See `AGENTS.md` for coding practices.
