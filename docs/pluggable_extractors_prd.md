# Pluggable Extractors PRD

> **Status:** Draft

> **Last Updated:** 2025-10-01

> **Author:** Codex assistant

## 1. Background
- Current proof-of-concept relies on Docling for document parsing and LangExtract (Gemini) for legal event extraction.
- Early validation (event-extractor-002, event-extractor-003, streamlit-provider-selector-001) proved the adapter interfaces work and shipped three working providers: LangExtract, OpenRouter, and OpenCode Zen.
- Product aims to evaluate multiple vendor combinations (e.g., Docling vs. PyPDF; LangExtract vs. OpenRouter/OpenAI/Anthropic) without rewriting pipeline code.

## 2. Problem Statement
Legal ops teams want to plug in different document processors and LLM-backed event extractors depending on data sensitivity, cost, latency, and availability. Today the pipeline hardcodes Docling + LangExtract, forcing code changes to trial alternatives and making it difficult to compare providers or deploy to environments without Gemini access.

## 3. Goals & Success Metrics
### Goals
- Allow users to select any supported document extractor and event extractor combination via configuration only.
- Ship with at least two concrete implementations per side (Docling + 1 alternative, LangExtract + 1 LLM provider).
- Surface clear validation/availability checks before running the pipeline.
- Document setup for each combination, including environment variables and expected capabilities.

### Success Metrics
- ✅ 100% of supported combinations can be launched by setting `DOC_EXTRACTOR` and `EVENT_EXTRACTOR` environment variables plus provider-specific credentials.
- ✅ Smoke tests cover every officially supported pairing.
- ✅ README quick-start lists at least two documented configurations.
- ✅ Users can add a new provider by implementing an adapter and registering it without modifying pipeline orchestration code.

## 4. Non-Goals
- Solving credential storage or secret management beyond environment variables.
- ~~Providing UI-based configuration switching (CLI/env only for this phase).~~ ✅ **COMPLETED** - See streamlit-provider-selector-001
- Guaranteeing support for arbitrary third-party libraries without adapter work.
- Handling hybrid orchestration (multiple providers per run) in this iteration.

## 5. User Stories
1. **Evaluation Engineer** wants to benchmark Docling vs. a lightweight PDF parser by toggling `DOC_EXTRACTOR=pypdf` while keeping LangExtract for events.
2. **Security-Constrained Admin** needs to run the pipeline with an in-house document parser and Anthropic models because Gemini access is restricted.
3. **Cost Manager** switches `EVENT_EXTRACTOR=openrouter` for bulk processing to use cheaper models without code changes.
4. **Contributor** implements a new adapter and registers it so QA can smoke test within a day.

## 6. Functional Requirements
- FR1. System must load extractor configuration from env (`DOC_EXTRACTOR`, `EVENT_EXTRACTOR`) with defaults preserved.
- FR2. For each configured provider, the factory must instantiate the corresponding adapter and pass provider-specific config objects.
- FR3. Adapters must expose `is_available()` to validate credentials, dependencies, and fail fast with actionable errors.
- FR4. Pipeline must emit capability metadata (e.g., table support) so downstream features can adjust behavior.
- FR5. Repository must include documentation describing how to enable each provider combination.
- FR6. Provide smoke test entry points verifying that each supported combination runs end-to-end on sample documents.

## 7. Non-Functional Requirements
- NFR1. Adding a new provider must not require modifying pipeline orchestration code (factory registration only).
- NFR2. Configuration should degrade gracefully: if a provider key is missing, the system warns and falls back to defaults where safe.
- NFR3. Maintain current security posture—no credentials committed, clear redaction guidance in docs.
- NFR4. Adapter modules should stay lightweight and mockable for testing (no heavy imports at module import time).

## 8. Scope
### In Scope
- Refactoring factory/config modules to support provider registries.
- Implementing at least one alternative adapter per side.
- Documentation and examples for supported combinations.
- Tests validating the adapter selection matrix.

### Out of Scope
- Building a full plugin marketplace or dynamic runtime loading.
- Advanced orchestration (multi-provider fallback, cascading).
- UI changes beyond current Streamlit toggles showing active providers (optional improvement).

## 9. Milestones
1. **Execution Order Published** – Capture the phased rollout in `docs/orders/event-extractor-001.json` so contributors share a single backlog.
2. **Registry Bootstrap** – Ship the event extractor registry with LangExtract as the default provider plus compatibility tests.
3. **OpenRouter Pilot** – Introduce OpenRouter configuration and adapter behind credential-gated availability checks.
4. **OpenCode Zen Pilot** – Replicate the adapter pattern for OpenCode Zen with clear fallbacks when credentials are absent.
5. **Docs & Smoke Tests** – Update contributor docs, `.env.example`, and provider-aware smoke harness to surface the new options.
6. **Release Candidate** – Validate the matrix, refresh README quick-starts, and mark ADR-001 as accepted.

## 10. Risks & Mitigations
- **R1. Provider credential sprawl** – Mitigate via per-provider config sections and documentation of required env vars.
- **R2. Uneven capability support** – Capture differences via capability metadata and note limitations in docs.
- **R3. Increased test matrix size** – Automate smoke tests and treat unsupported combos as experimental.
- **R4. Third-party dependency conflicts** – Lazy-load heavy SDKs within adapters to avoid import-time failures.

## 11. Dependencies
- Availability of alternative document/LLM providers (PyPDF, OpenAI, Anthropic, OpenRouter, etc.).
- Team agreement on supported providers for initial release.
- Access to sample documents and test harness to validate outputs.

## 12. Open Questions
- Which alternative document extractor will we ship first (PyPDF? Unstructured?)
- What is the minimum acceptable event extractor alternative (OpenRouter wrapper? Direct OpenAI client?)
- Do we need per-provider rate limiting or batching abstractions in v1?
- Should capability metadata feed into Streamlit UI immediately or remain internal?

## 13. Appendix
- Related docs: `README.md`, `CLAUDE.md`, existing ADR `docs/adr/ADR-001-pluggable-extractors.md`.
- Prior verification log: `~/claude-conversations/docling_langextract_testing/2025-09-23_111500_docling_verification_conversation.md`.
