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

## OpenAI (Direct API)
- `OPENAI_API_KEY`: Required for OpenAI direct access
- `OPENAI_BASE_URL`: Default `https://api.openai.com/v1`
- `OPENAI_MODEL`: Model identifier (default: `gpt-4o-mini`)
- `OPENAI_TIMEOUT`: Request timeout in seconds (default: `60`)

## Future Providers (Phase 1 Implementation)

### Anthropic Direct API
- `ANTHROPIC_API_KEY`: Required for Anthropic direct access
- `ANTHROPIC_BASE_URL`: Default `https://api.anthropic.com/v1`
- `ANTHROPIC_MODEL`: Model identifier (default: `claude-3-haiku-20240307`)
- `ANTHROPIC_TIMEOUT`: Request timeout in seconds (default: `60`)

### DeepSeek Direct API
- `DEEPSEEK_API_KEY`: Required for DeepSeek direct access
- `DEEPSEEK_BASE_URL`: Default `https://api.deepseek.com/v1`
- `DEEPSEEK_MODEL`: Model identifier (default: `deepseek-chat`)
- `DEEPSEEK_TIMEOUT`: Request timeout in seconds (default: `60`)

### Moonshot AI (Kimi K2)
- `MOONSHOT_API_KEY`: Required for Moonshot access
- `MOONSHOT_BASE_URL`: Default `https://api.moonshot.cn/v1`
- `MOONSHOT_MODEL`: Model identifier (default: `moonshot-v1-128k`)
- `MOONSHOT_TIMEOUT`: Request timeout in seconds (default: `60`)

### Zhipu AI (ChatGLM)
- `ZHIPU_API_KEY`: Required for Zhipu access
- `ZHIPU_BASE_URL`: Default `https://open.bigmodel.cn/api/paas/v4`
- `ZHIPU_MODEL`: Model identifier (default: `glm-4`)
- `ZHIPU_TIMEOUT`: Request timeout in seconds (default: `60`)

---

## Provider Comparison

### Implemented Providers (4/8)

#### LangExtract (Google Gemini) - Default
- **Status**: ✅ Implemented
- **Model**: `gemini-2.0-flash`
- **Quality**: 9/10
- **Cost**: Varies by Gemini pricing
- **Best For**: Default choice, reliable performance

#### OpenRouter (Unified Multi-Provider API)
- **Status**: ✅ Implemented
- **Models Tested**: 11+ (2025-10-01)
- **Quality**: Up to 10/10
- **Best For**: Cost optimization, model flexibility

**Tested OpenRouter Models**:
| Model | Quality | Cost ($/M tokens) | Best For |
|-------|---------|-------------------|----------|
| `deepseek/deepseek-r1-distill-llama-70b` | 10/10 | $0.03 | **Budget Champion** |
| `openai/gpt-4o-mini` | 9/10 | $0.15 | **Recommended Default** |
| `anthropic/claude-3-haiku` | 10/10 | $0.25 | Balanced performance |
| `openai/gpt-3.5-turbo` | 10/10 | $0.50 | Legacy option |
| `openai/gpt-4o` | 10/10 | $3.00 | Premium quality |
| `anthropic/claude-3-5-sonnet` | 10/10 | $3.00 | Premium quality |
| `openai/gpt-4-turbo` | 10/10 | $10.00 | Top tier |

All models scored 10/10 for quality and reliability with `response_format` support.

**Test Results**: `scripts/fallback_models_test.log`
**Validation Scripts**: `scripts/test_openrouter.py`, `scripts/test_fallback_models.py`

#### OpenCode Zen (Legal AI Gateway)
- **Status**: ✅ Implemented
- **Models Tested**: 2 (2025-10-02)
- **Quality**: 8/10
- **Best For**: Legal-specialized models, free tier

**Tested OpenCode Zen Models**:
| Model | Quality | Cost ($/M tokens) | Best For |
|-------|---------|-------------------|----------|
| `code-supernova` | 8/10 | **FREE** | **Free Tier Champion** |
| `grok-code` | 8/10 | $0.50 | Affordable legal AI |

**Test Results**: `scripts/opencode_zen_models_test.log`
**Validation Scripts**: `scripts/test_opencode_zen.py`, `scripts/test_opencode_zen_models.py`

#### OpenAI (Direct API) ⭐ NEW
- **Status**: ✅ Implemented (2025-10-02)
- **Models**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- **Quality**: 10/10 (validated with diagnostic script)
- **Best For**: Standard choice, native JSON mode, reliable

**Model Pricing & Features**:
| Model | Cost ($/M in + out) | JSON Mode | Rate Limits | Best For |
|-------|---------------------|-----------|-------------|----------|
| `gpt-4o-mini` | $0.15 + $0.60 | ✅ Native | 10K req/200K tok | **Recommended Default** |
| `gpt-4o` | $2.50 + $10.00 | ✅ Native | Tier-based | Premium quality |
| `gpt-4-turbo` | $10.00 + $30.00 | ✅ Native | Tier-based | Top tier |
| `gpt-3.5-turbo-1106` | $0.50 + $1.50 | ✅ Native | High volume | Legacy option |

**Setup Guide**:
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`: `OPENAI_API_KEY=sk-...`
3. Set provider: `EVENT_EXTRACTOR=openai`
4. Optionally set model: `OPENAI_MODEL=gpt-4o-mini`

**JSON Mode Support**:
- ✅ GPT-4o, GPT-4-turbo, GPT-3.5-turbo-1106+ support native `response_format={"type": "json_object"}`
- ⚠️  Older models (GPT-3.5-turbo base) may not support JSON mode - adapter will log warning

**Troubleshooting**:
- **401 Unauthorized**: Invalid API key → verify at https://platform.openai.com/api-keys
- **429 Rate Limit**: Exponential backoff retry (3 attempts) built-in → check tier limits
- **400 Bad Request (JSON mode)**: Model doesn't support `response_format` → use compatible model
- **Timeout**: Increase `OPENAI_TIMEOUT` from default 60s

**Diagnostic Script**: Run `uv run python scripts/test_openai.py` for 10-level validation
**Test Results**: ✅ 10/10 diagnostic checks passed (2025-10-02)

### Planned Providers (4/8) - Phase 1 Implementation

#### Anthropic Direct API
- **Status**: ⏳ Planned (Week 2)
- **Models**: Claude 3.5 Sonnet, Opus, Haiku
- **Expected Quality**: 10/10
- **Expected Cost**: $0.25/M (Haiku) to $75.00/M (Opus output)

| Model | Cost ($/M in + out) | Expected Quality | Notes |
|-------|---------------------|------------------|-------|
| `claude-3-haiku-20240307` | $0.25 + $1.25 | 10/10 | Fastest, affordable |
| `claude-3-5-sonnet-20241022` | $3.00 + $15.00 | 10/10 | Highest intelligence |
| `claude-3-opus-20240229` | $15.00 + $75.00 | 10/10 | Most capable |

#### DeepSeek Direct API
- **Status**: ⏳ Planned (Week 3)
- **Models**: DeepSeek R1, DeepSeek V3, DeepSeek Chat
- **Expected Quality**: 9-10/10
- **Expected Cost**: $0.14/M to TBD

| Model | Cost ($/M in + out) | Expected Quality | Notes |
|-------|---------------------|------------------|-------|
| `deepseek-chat` | $0.14 + $0.28 | 9/10 | General purpose |
| `deepseek-reasoner` | TBD | 10/10 | R1 reasoning model |

#### Moonshot AI (Kimi K2)
- **Status**: ⏳ Planned (Week 4) - **HIGH RISK**
- **Models**: Kimi K2 (1T params, 256K context)
- **Expected Quality**: 8-9/10
- **Expected Cost**: $0.084/M to $0.84/M

| Model | Cost ($/M tokens) | Expected Quality | Context | Notes |
|-------|-------------------|------------------|---------|-------|
| `moonshot-v1-8k` | $0.084 | 8/10 | 8K | Minimal context |
| `moonshot-v1-32k` | $0.24 | 9/10 | 32K | Reduced context |
| `moonshot-v1-128k` | $0.84 | 9/10 | 128K | Standard context |

**Risks**: Mainland China API, Chinese phone verification, JSON support uncertain, Chinese documentation

#### Zhipu AI (ChatGLM)
- **Status**: ⏳ Planned (Week 4) - **HIGH RISK**
- **Models**: GLM-4, GLM-4.5 (200K context)
- **Expected Quality**: 7-9/10
- **Expected Cost**: $0.01/M to $0.50/M

| Model | Cost ($/M tokens) | Expected Quality | Context | Notes |
|-------|-------------------|------------------|---------|-------|
| `glm-4-flash` | $0.01 | 7/10 | 200K | Ultra-fast |
| `glm-4-air` | $0.05 | 8/10 | 200K | Lightweight |
| `glm-4` | $0.50 | 9/10 | 200K | Latest generation |

**Risks**: Mainland China API, account approval required, JSON support uncertain, special auth formatting

---

## Champion Recommendations

### By Use Case

| Use Case | Champion | Provider | Model | Reason |
|----------|----------|----------|-------|--------|
| **High-Stakes Legal Work** | Quality | Anthropic | Claude 3.5 Sonnet | Best accuracy, 10/10 quality |
| **High-Volume Processing** | Cost | OpenRouter | DeepSeek R1 Distill | $0.03/M, 10/10 quality |
| **Real-Time Applications** | Speed | OpenRouter | GPT-4o-mini | Fast response, low latency |
| **Prototype/Testing** | Free Tier | OpenCode Zen | code-supernova | FREE, 8/10 quality |
| **Production Default** | Balanced | OpenRouter | GPT-4o-mini | $0.15/M, 9/10, reliable |

### Provider Selection Guide

**Start with**: LangExtract (Gemini) - Pre-configured, reliable
**For cost optimization**: OpenRouter with DeepSeek R1 Distill ($0.03/M)
**For free tier**: OpenCode Zen code-supernova (FREE, 8/10 quality)
**For premium quality**: OpenRouter with GPT-4o or Claude 3.5 Sonnet
**For legal-specific**: OpenCode Zen grok-code ($0.50/M, 8/10)

---

## Notes
- Keep secrets out of commits. `.env` must not be versioned.
- Prefer toggles and config over hard-coded literals.
- See `docs/plans/REVISION-2025-10-02.md` for provider implementation timeline.
- Model quality scores based on legal event extraction testing (2025-10-01 to 2025-10-02).
