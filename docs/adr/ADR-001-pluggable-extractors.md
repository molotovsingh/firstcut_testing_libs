# ADR-001: Pluggable Document and Event Extractors

- **Status:** Proposed
- **Date:** 2025-09-24
- **Owner:** Codex assistant
- **Related Docs:** `docs/pluggable_extractors_prd.md`, `README.md`, `src/core/interfaces.py`

## Context
The legal events pipeline currently wires Docling for document ingestion and LangExtract (Gemini) for event extraction. While interfaces exist, concrete implementations are hardcoded, forcing code edits to evaluate other providers (PyPDF, OpenRouter, OpenAI, Anthropic, in-house tools). Product needs the ability to mix and match extractors through configuration so teams can pick providers based on latency, security, and cost without touching pipeline orchestration.

Constraints and observations:
- `src/core/interfaces.py` already defines `DocumentExtractor` and `EventExtractor` protocols with `is_available()` hooks.
- `src/core/config.py` loads environment variables but returns monolithic config objects geared toward Docling + LangExtract.
- `src/core/extractor_factory.py` currently instantiates Docling and LangExtract directly.
- Tests and Streamlit UI assume the baseline providers but can be extended to surface provider names.

## Decision
Implement a provider registry architecture that maps configuration keys to adapter factories on both sides of the pipeline.

1. **Provider Registries**
   - Introduce dictionaries `DOCUMENT_PROVIDER_REGISTRY` and `EVENT_PROVIDER_REGISTRY` inside `extractor_factory` (or companion module).
   - Keys correspond to values supplied via `DOC_EXTRACTOR` and `EVENT_EXTRACTOR` env vars.
   - Registry values are callables that accept provider-specific config and return an adapter instance.

2. **Provider-Specific Configs**
   - Extend `config.py` to expose typed dataclasses per provider (e.g., `DoclingConfig`, `PyPdfConfig`, `LangExtractConfig`, `OpenRouterConfig`, etc.).
   - Add a light-weight `ProviderSettings` structure that resolves only the configs required for the selected providers to avoid importing unused SDKs.

3. **Factory Flow**
   - `create_default_extractors()` reads the registry, validates keys, calls the matching factory, and returns the adapters.
   - If a provider is missing or `is_available()` fails, raise a descriptive `ExtractorConfigurationError` with remediation guidance.

4. **Capabilities Contract**
   - Require adapters to expose an optional `capabilities()` method (or property) returning a dict of feature flags (e.g., `supports_tables`, `supports_batch`, `max_page_count`).
   - Pipeline reads these to adjust downstream behavior instead of hardcoding Docling assumptions.

5. **Documentation & Tests**
   - Document supported providers and environment variables in README/CLAUDE.
   - Add smoke tests that iterate over the supported matrix (skipping providers lacking credentials) to ensure registry wiring works.

## Alternatives Considered
1. **Hardcode additional `if/elif` branches** in the factory for each provider.
   - *Rejected* because it scales poorly and still requires code edits for every addition.

2. **Dynamic plugin loading via entry points or importlib**.
   - *Rejected for now* due to added complexity and security review burden. Keeping providers in-repo via registries is sufficient.

3. **Separate pipelines per provider**.
   - *Rejected*; would duplicate orchestration code and reduce comparability across providers.

## Consequences
- **Positive**
  - Adding a provider requires only implementing an adapter and registering it.
  - Easier experimentation with different LLM/document services.
  - Configuration errors surface early with actionable messages.
  - Capability metadata makes feature gaps explicit.

- **Negative / Mitigations**
  - Registry must stay updated; missing keys result in runtime errors (mitigated with tests and clear docs).
  - More configuration permutations increase testing workload (mitigate with targeted smoke matrix and optional CI skips).
  - Provider-specific dependencies may bloat the environment (mitigate by lazy-importing heavy SDKs inside adapters and documenting optional extras).

## Implementation Plan
1. Publish the incremental execution order (`docs/orders/event-extractor-001.json`) and tag backlog items with its task IDs.
2. Refactor `extractor_factory.py` to introduce `EVENT_PROVIDER_REGISTRY`, keeping LangExtract as the default and preserving existing behaviour.
3. Add provider-specific config dataclasses plus the OpenRouter adapter, covered by mocked HTTP tests and credential validation.
4. Implement the OpenCode Zen adapter mirroring the OpenRouter pattern, including availability checks and registry wiring.
5. Expand documentation, `.env.example`, and smoke tests so provider selection is discoverable and validated when credentials exist.

## Open Questions
- Should registries live in `extractor_factory` or a new `providers.py` module to avoid circular imports?
- Do we enforce capability schema (e.g., TypedDict) or keep it free-form initially?
- How do we gate experimental providers that require external dependencies not vendored in `pyproject.toml`?

## Next Steps
- Socialize the ADR and confirm the `event-extractor-001` order as the authoritative rollout plan.
- Start with the registry bootstrap task, landing the change behind the existing LangExtract default before wiring additional providers.
