# Provider Integration Guide

This guide shows how to add and validate new event extractor providers (e.g., OpenRouter, OpenCode Zen) with small, incremental steps. Use it alongside the active orders under `docs/orders/`.

## Overview
- Selection is controlled via env var `EVENT_EXTRACTOR` (e.g., `langextract`, `openrouter`, `opencode_zen`) **OR** via the Streamlit UI provider selector.
- The factory routes through a registry; add new providers without touching pipeline code: see `src/core/extractor_factory.py:30`.

## Using The Streamlit Provider Selector

The main Streamlit application (`app.py`) includes an **interactive provider selector** that allows switching between event extraction providers without restarting the app:

### How To Use:
1. Launch the Streamlit app: `uv run streamlit run app.py`
2. In the **Processing** panel (right column), find the **Event Provider** radio group
3. Select your desired provider:
   - **LangExtract (Google Gemini)** - Requires `GEMINI_API_KEY` in `.env`
   - **OpenRouter (Unified API)** - Requires `OPENROUTER_API_KEY` in `.env`
   - **OpenCode Zen (Legal AI)** - Requires `OPENCODEZEN_API_KEY` in `.env`
4. Upload documents and click **Process Files**

### Features:
- **Session Persistence**: Selected provider is cached in Streamlit session state
- **Auto-Invalidation**: Changing providers clears the cached pipeline and reinitializes with the new adapter
- **Credential Tooltip**: Hover over the help icon to see which API key is required for each provider
- **Result Clearing**: Previous results are automatically cleared when switching providers

### Technical Details:
- UI state stored in `st.session_state.selected_provider`
- Pipeline cache invalidated when provider changes (see `src/ui/streamlit_common.py:get_pipeline()`)
- Provider parameter flows through: `app.py` → `streamlit_common.py` → `LegalEventsPipeline` → `extractor_factory.py`
- Default provider from `EVENT_EXTRACTOR` env var, falls back to `'langextract'`

## Steps To Add A Provider
1. Configuration
   - Define env vars in `.env.example` (API key, base URL, model, timeout).
   - If needed, add a small config dataclass (e.g., `OpenRouterConfig`) inside `src/core/config.py`.
2. Adapter
   - Create `src/core/<provider>_adapter.py` that implements the `EventExtractor` protocol (see `src/core/interfaces.py:41`).
   - Lazy-import heavy SDKs inside methods to avoid import-time failures.
   - Implement `is_available()` to check credentials and prerequisites early.
3. Registry Wiring
   - Register a factory function in `EVENT_PROVIDER_REGISTRY` within `src/core/extractor_factory.py:30`.
   - Keep `langextract` as default; ensure unknown keys raise `ExtractorConfigurationError`.
4. Tests
   - Unit: mock HTTP/SDK calls; confirm adapter maps responses to `EventRecord` and handles error paths.
   - Factory: verify the registry instantiates the right adapter; invalid keys raise.
5. Docs & Smoke
   - Update README quick-starts and AGENTS.md if usage changes.
   - Add credential-gated smoke steps; skip gracefully when keys are missing.

## OpenRouter Quick Notes
- Env vars: `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`), `OPENROUTER_MODEL`, `OPENROUTER_TIMEOUT`.
- Minimal HTTP example (pseudo):
  - Headers: `Authorization: Bearer $OPENROUTER_API_KEY`, `Content-Type: application/json`.
  - POST to `${OPENROUTER_BASE_URL}/chat/completions` with `{ model, messages, temperature }`.
  - Parse response, normalize into `EventRecord` list; include `attributes.model_id` and any offsets when available.

## OpenCode Zen Quick Notes
- Env vars: `OPENCODEZEN_API_KEY`, `OPENCODEZEN_BASE_URL`, `OPENCODEZEN_MODEL`, `OPENCODEZEN_TIMEOUT`.
- Follow the same adapter/registry/testing pattern as OpenRouter; ensure clear fallback records when unavailable.
- See the dedicated troubleshooting checklist: `docs/guides/opencode_zen_troubleshooting.md` for header/endpoint/payload details and a minimal probe.

## Troubleshooting

### Common Issues and Solutions

#### Provider Configuration Errors

**Symptom**: When selecting a provider in the Streamlit UI, you see an error like:
```
Provider Configuration Error: openrouter

OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable.
```

**Root Cause**: The selected provider's adapter initialization failed due to missing or invalid API credentials.

**Solution**:
1. Check your `.env` file for the required API key:
   - **OpenRouter**: `OPENROUTER_API_KEY=your_key_here`
   - **OpenCode Zen**: `OPENCODEZEN_API_KEY=your_key_here`
   - **LangExtract**: `GEMINI_API_KEY=your_key_here`

2. Ensure the API key is not empty or commented out

3. Restart the Streamlit app to load the new environment variables:
   ```bash
   # Stop the current app (Ctrl+C)
   uv run streamlit run app.py
   ```

4. After restart, select your provider again in the UI

**Why This Happens**: The system performs two-level validation:
1. **Pipeline-level** (`LegalEventsPipeline._validate_environment()`): Checks provider-specific credentials before adapter initialization
2. **Adapter-level** (`EventExtractor.__init__()`): Secondary validation during adapter creation

The pipeline uses a provider-aware credential mapping to validate only the required API key for your selected provider:
- LangExtract → `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- OpenRouter → `OPENROUTER_API_KEY`
- OpenCode Zen → `OPENCODEZEN_API_KEY`

This means **you only need the API key for the provider you're using** - not all keys at once.

#### Provider Cache Issues

**Symptom**: After fixing credentials, the provider still shows errors or uses stale configuration.

**Root Cause**: Streamlit session state caches pipeline instances to avoid re-initialization on every interaction.

**Solution**:
1. **Recommended**: Switch to a different provider in the UI, then switch back
   - This triggers cache invalidation automatically
   - Session state is cleared for the new provider selection

2. **Alternative**: Restart the Streamlit app
   - Stops the current session: `Ctrl+C`
   - Relaunch: `uv run streamlit run app.py`

**Implementation Note**: The cache invalidation logic is in `src/ui/streamlit_common.py:get_pipeline()` at lines 36-42, which checks if `pipeline_provider` changed and deletes cached instances.

#### Provider-Aware Validation (New in Provider Selection Update)

**Feature**: The pipeline now validates **only the credentials required for your selected provider**, not all provider keys.

**How It Works**:
- `LegalEventsPipeline.PROVIDER_CREDENTIALS` mapping defines required env vars per provider
- `_validate_environment()` checks the appropriate key based on `self.event_extractor_type`
- Error messages specify exactly which key is missing for your provider

**Example Validation Flow**:
```
User selects OpenRouter
  ↓
LegalEventsPipeline(event_extractor="openrouter")
  ↓
_validate_environment() checks OPENROUTER_API_KEY
  ↓
If missing → ValueError: "OPENROUTER_API_KEY required for OpenRouter unified API"
  ↓
If present → Continue to adapter initialization
```

**Benefits**:
- ✅ No need to configure all API keys upfront
- ✅ Clear error messages showing which key to configure
- ✅ Can use OpenRouter without Gemini key, and vice versa
- ✅ Reduces cognitive load for users

**Implementation Location**: `src/core/legal_pipeline_refactored.py:29-109`

### General Troubleshooting Steps

- **Missing credentials**: `is_available()` should return False and surface a helpful message
- **SDK/network not present**: guard imports and provide actionable logs; prefer mocking in tests
- **Skipped smoke tests**: record skip reason and which provider was unavailable
- **Rate limiting**: If API calls fail with 429 errors, wait before retrying to avoid account lockouts

## Verification Checklist
- `EVENT_EXTRACTOR=<provider>` yields the correct adapter via the registry.
- Adapter validates credentials and returns `EventRecord` objects for happy-path mock responses.
- README/AGENTS mention how to select providers and set env vars.
