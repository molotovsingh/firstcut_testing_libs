# Project-Wide Documentation Accuracy Review - 2025-10-04 (Revised)

## 1. Introduction

This report summarizes a project-wide documentation accuracy review. The analysis was expanded beyond the initial `README.md` check to cover other key project documents and compare them against the current state of the codebase. The review covered:
1.  The main `README.md` file.
2.  The Streamlit application UI (`app.py`).
3.  Architecture documents (`docs/adr/ADR-001-pluggable-extractors.md`).
4.  Core implementation files (`src/core/config.py`, `src/core/extractor_factory.py`).

## 2. High-Level Summary

The consistent finding across all areas of the review is that **project documentation is not being updated as the codebase evolves.** Critical documents, including the main README and architecture records, are out of sync with the implementation, leading to missing information about new features and providers.

## 3. Detailed Findings

### 3.1. `README.md` vs. Code (`config.py`, `app.py`)

- **Undocumented `DeepSeek` Provider:** The `README.md` completely fails to mention the `DeepSeek` provider, which is present in the `app.py` UI and implemented in the core factory.
- **Incomplete Environment Variables:** The `README.md`'s configuration reference is missing numerous variables that are actively used in `src/core/config.py`.

**Undocumented Variables:**
*   `DOCLING_AUTO_OCR_DETECTION`
*   `DOCLING_OCR_ENGINE`
*   `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_TIMEOUT`
*   `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`, `ANTHROPIC_TIMEOUT`
*   `DEEPSEEK_API_KEY` (and likely other related `DEEPSEEK_*` variables)

### 3.2. Architecture Document vs. Implementation (`ADR-001` vs. `extractor_factory.py`)

- **Outdated Provider List:** `ADR-001` states that three event extractor providers are supported (`LangExtract`, `OpenRouter`, `OpenCode Zen`).
- **Actual Implementation:** The `EVENT_PROVIDER_REGISTRY` in `src/core/extractor_factory.py` shows that **six** providers are implemented. `OpenAI`, `Anthropic`, and `DeepSeek` are not mentioned in the ADR.

### 3.3. Link and Code Example Integrity

- **No Broken Links:** All internal file links in `README.md` were checked and found to be valid.
- **Code Examples Appear Valid:** The Python code snippets in the `README.md` use dependencies (`langextract`, `python-dotenv`) that are correctly listed in `pyproject.toml`.

## 4. Recommendations

1.  **Update `README.md` for All Missing Providers:**
    *   Add the `DeepSeek` provider to the list of available providers.
    *   Update the "Environment Variables Quick Reference" table to be a complete and accurate list, including all variables for `OpenAI`, `Anthropic`, and `DeepSeek`.
    *   Add dedicated configuration sections for `OpenAI`, `Anthropic`, and `DeepSeek`.

2.  **Update Architecture Documents:**
    *   Revise `docs/adr/ADR-001-pluggable-extractors.md` to reflect the current state of the `EVENT_PROVIDER_REGISTRY`, listing all six supported providers.

3.  **Establish a Documentation Update Process:**
    *   Recommend a new process for contributors: when a new provider or significant configuration change is added, updating the `README.md` and relevant ADRs should be a required part of the pull request.
