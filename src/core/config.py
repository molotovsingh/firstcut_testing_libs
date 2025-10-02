"""
Configuration module for Docling and LangExtract settings
Provides strongly-typed configuration with environment variable overrides
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Literal, Tuple, Any

from .constants import DEFAULT_MODEL


# Helper functions for environment variable parsing
def env_bool(var_name: str, default: bool) -> bool:
    """Parse environment variable as boolean"""
    value = os.getenv(var_name)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def env_int(var_name: str, default: int) -> int:
    """Parse environment variable as integer"""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_float(var_name: str, default: float) -> float:
    """Parse environment variable as float"""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def env_str(var_name: str, default: str) -> str:
    """Parse environment variable as string"""
    return os.getenv(var_name, default)


def env_optional_str(var_name: str) -> Optional[str]:
    """Parse environment variable as optional string"""
    value = os.getenv(var_name)
    return value if value else None


@dataclass
class DoclingConfig:
    """Configuration for Docling document processing"""

    # OCR and processing options
    do_ocr: bool = field(default_factory=lambda: env_bool("DOCLING_DO_OCR", True))
    do_table_structure: bool = field(default_factory=lambda: env_bool("DOCLING_DO_TABLE_STRUCTURE", True))
    table_mode: Literal["FAST", "ACCURATE"] = field(default_factory=lambda: env_str("DOCLING_TABLE_MODE", "FAST"))
    do_cell_matching: bool = field(default_factory=lambda: env_bool("DOCLING_DO_CELL_MATCHING", True))

    # Backend and acceleration
    backend: Literal["default", "v2"] = field(default_factory=lambda: env_str("DOCLING_BACKEND", "default"))
    accelerator_device: Literal["cuda", "mps", "cpu"] = field(default_factory=lambda: env_str("DOCLING_ACCELERATOR_DEVICE", "cpu"))
    accelerator_threads: int = field(default_factory=lambda: env_int("DOCLING_ACCELERATOR_THREADS", 4))

    # Paths and timeouts
    artifacts_path: Optional[str] = field(default_factory=lambda: env_optional_str("DOCLING_ARTIFACTS_PATH"))
    document_timeout: int = field(default_factory=lambda: env_int("DOCLING_DOCUMENT_TIMEOUT", 300))


@dataclass
class LangExtractConfig:
    """Configuration for LangExtract operations"""

    # Model and API settings
    model_id: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL_ID", DEFAULT_MODEL))
    temperature: float = field(default_factory=lambda: env_float("LANGEXTRACT_TEMPERATURE", 0.0))
    max_workers: int = field(default_factory=lambda: env_int("LANGEXTRACT_MAX_WORKERS", 10))
    debug: bool = field(default_factory=lambda: env_bool("LANGEXTRACT_DEBUG", False))


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API operations"""

    # API settings
    api_key: str = field(default_factory=lambda: env_str("OPENROUTER_API_KEY", ""))
    base_url: str = field(default_factory=lambda: env_str("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
    model: str = field(default_factory=lambda: env_str("OPENROUTER_MODEL", "anthropic/claude-3-haiku"))
    timeout: int = field(default_factory=lambda: env_int("OPENROUTER_TIMEOUT", 30))


@dataclass
class OpenCodeZenConfig:
    """Configuration for OpenCode Zen API operations"""

    # API settings
    api_key: str = field(default_factory=lambda: env_str("OPENCODEZEN_API_KEY", ""))
    base_url: str = field(default_factory=lambda: env_str("OPENCODEZEN_BASE_URL", "https://api.opencode-zen.example/v1"))
    model: str = field(default_factory=lambda: env_str("OPENCODEZEN_MODEL", "opencode-zen/legal-extractor"))
    timeout: int = field(default_factory=lambda: env_int("OPENCODEZEN_TIMEOUT", 30))


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API operations"""

    # API settings
    api_key: str = field(default_factory=lambda: env_str("OPENAI_API_KEY", ""))
    base_url: str = field(default_factory=lambda: env_str("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = field(default_factory=lambda: env_str("OPENAI_MODEL", "gpt-4o-mini"))
    timeout: int = field(default_factory=lambda: env_int("OPENAI_TIMEOUT", 60))


@dataclass
class AnthropicConfig:
    """Configuration for Anthropic API operations"""

    # API settings
    api_key: str = field(default_factory=lambda: env_str("ANTHROPIC_API_KEY", ""))
    base_url: str = field(default_factory=lambda: env_str("ANTHROPIC_BASE_URL", "https://api.anthropic.com"))
    model: str = field(default_factory=lambda: env_str("ANTHROPIC_MODEL", "claude-3-haiku-20240307"))
    timeout: int = field(default_factory=lambda: env_int("ANTHROPIC_TIMEOUT", 60))


@dataclass
class ExtractorConfig:
    """Configuration for extractor selection"""

    # Extractor type selection
    doc_extractor: str = None
    event_extractor: str = None

    def __post_init__(self):
        """Initialize fields with environment variables after instance creation"""
        if self.doc_extractor is None:
            self.doc_extractor = env_str("DOC_EXTRACTOR", "docling")
        if self.event_extractor is None:
            self.event_extractor = env_str("EVENT_EXTRACTOR", "langextract")


def load_config() -> Tuple[DoclingConfig, LangExtractConfig, ExtractorConfig]:
    """
    Load configuration for Docling, LangExtract, and extractor selection

    Returns:
        Tuple of (DoclingConfig, LangExtractConfig, ExtractorConfig) instances
    """
    docling_config = DoclingConfig()
    langextract_config = LangExtractConfig()
    extractor_config = ExtractorConfig()

    return docling_config, langextract_config, extractor_config


def load_provider_config(
    provider: str,
    docling_config: Optional[DoclingConfig] = None,
    extractor_config: Optional[ExtractorConfig] = None
) -> Tuple[DoclingConfig, Any, ExtractorConfig]:
    """Load configuration with provider-specific event extractor config.

    Args:
        provider: Event extractor provider type.
        docling_config: Optional pre-loaded Docling configuration instance.
        extractor_config: Optional extractor configuration instance to update.

    Returns:
        Tuple of (DoclingConfig, provider_specific_config, ExtractorConfig) instances.
    """
    docling_config = docling_config or DoclingConfig()
    extractor_config = extractor_config or ExtractorConfig()

    provider_key = (provider or extractor_config.event_extractor or "langextract").strip().lower()
    extractor_config.event_extractor = provider_key

    if provider_key == "openrouter":
        event_config = OpenRouterConfig()
    elif provider_key == "opencode_zen":
        event_config = OpenCodeZenConfig()
    elif provider_key == "openai":
        event_config = OpenAIConfig()
    elif provider_key == "anthropic":
        event_config = AnthropicConfig()
    else:
        event_config = LangExtractConfig()
        extractor_config.event_extractor = "langextract"

    return docling_config, event_config, extractor_config
