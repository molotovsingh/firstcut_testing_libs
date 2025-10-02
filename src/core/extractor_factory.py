"""
Extractor Factory - Creates document and event extractors based on configuration
Supports environment variable overrides for different implementations
"""

import logging
from typing import Tuple, Callable, Dict, Any, Optional

from .interfaces import DocumentExtractor, EventExtractor
from .config import (
    DoclingConfig, LangExtractConfig, ExtractorConfig,
    OpenRouterConfig, OpenCodeZenConfig, OpenAIConfig, AnthropicConfig,
    load_config, load_provider_config
)
from .docling_adapter import DoclingDocumentExtractor
from .langextract_adapter import LangExtractEventExtractor
from .openrouter_adapter import OpenRouterEventExtractor
from .opencode_zen_adapter import OpenCodeZenEventExtractor
from .openai_adapter import OpenAIEventExtractor
from .anthropic_adapter import AnthropicEventExtractor

logger = logging.getLogger(__name__)


class ExtractorConfigurationError(ValueError):
    """Raised when extractor provider configuration is invalid."""


def _create_langextract_event_extractor(
    _doc_config: DoclingConfig,
    event_config: Any,
    _extractor_config: ExtractorConfig
) -> EventExtractor:
    """Factory for the default LangExtract adapter."""
    return LangExtractEventExtractor(event_config)


def _create_openrouter_event_extractor(
    _doc_config: DoclingConfig,
    event_config: Any,
    _extractor_config: ExtractorConfig
) -> EventExtractor:
    """Factory for the OpenRouter adapter."""
    return OpenRouterEventExtractor(event_config)


def _create_opencode_zen_event_extractor(
    _doc_config: DoclingConfig,
    event_config: Any,
    _extractor_config: ExtractorConfig
) -> EventExtractor:
    """Factory for the OpenCode Zen adapter."""
    return OpenCodeZenEventExtractor(event_config)


def _create_openai_event_extractor(
    _doc_config: DoclingConfig,
    event_config: Any,
    _extractor_config: ExtractorConfig
) -> EventExtractor:
    """Factory for the OpenAI adapter."""
    return OpenAIEventExtractor(event_config)


def _create_anthropic_event_extractor(
    _doc_config: DoclingConfig,
    event_config: Any,
    _extractor_config: ExtractorConfig
) -> EventExtractor:
    """Factory for the Anthropic adapter."""
    return AnthropicEventExtractor(event_config)


EVENT_PROVIDER_REGISTRY: Dict[str, Callable[[DoclingConfig, Any, ExtractorConfig], EventExtractor]] = {
    "langextract": _create_langextract_event_extractor,
    "openrouter": _create_openrouter_event_extractor,
    "opencode_zen": _create_opencode_zen_event_extractor,
    "openai": _create_openai_event_extractor,
    "anthropic": _create_anthropic_event_extractor,
}


def build_extractors(
    docling_config: DoclingConfig,
    event_config: Any,
    extractor_config: ExtractorConfig
) -> Tuple[DocumentExtractor, EventExtractor]:
    """
    Build document and event extractors based on configuration

    Args:
        docling_config: Configuration for document processing
        event_config: Provider-specific configuration for event extraction
        extractor_config: Configuration for extractor selection

    Returns:
        Tuple of (DocumentExtractor, EventExtractor) instances

    Raises:
        ValueError: If an unsupported document extractor is requested.
        ExtractorConfigurationError: If the event extractor provider is not registered.
    """
    # Get extractor types from config
    doc_extractor_type = extractor_config.doc_extractor.lower()
    event_extractor_type = extractor_config.event_extractor.lower()

    logger.info(f"🏭 Building extractors: DOC={doc_extractor_type}, EVENT={event_extractor_type}")

    # Create document extractor
    if doc_extractor_type == "docling":
        doc_extractor = DoclingDocumentExtractor(docling_config)
        logger.info("✅ Created DoclingDocumentExtractor")
    else:
        raise ValueError(f"Unsupported document extractor type: {doc_extractor_type}")

    # Create event extractor
    event_factory = EVENT_PROVIDER_REGISTRY.get(event_extractor_type)
    if not event_factory:
        available = ", ".join(sorted(EVENT_PROVIDER_REGISTRY)) or "none"
        logger.error(f"❌ Unsupported event extractor type: {event_extractor_type}")
        raise ExtractorConfigurationError(
            f"Unsupported event extractor type: {event_extractor_type}. Available providers: {available}"
        )
    event_extractor = event_factory(docling_config, event_config, extractor_config)
    logger.info(f"✅ Created {event_extractor.__class__.__name__}")

    return doc_extractor, event_extractor


def create_default_extractors(
    event_extractor_override: Optional[str] = None
) -> Tuple[DocumentExtractor, EventExtractor]:
    """
    Create extractors with default configuration from environment

    Returns:
        Tuple of (DocumentExtractor, EventExtractor) instances
    """
    # First load base config to determine the event extractor type
    docling_config, _, extractor_config = load_config()

    if event_extractor_override:
        extractor_config.event_extractor = event_extractor_override

    # Load provider-specific configuration based on the event extractor type
    docling_config, event_config, extractor_config = load_provider_config(
        extractor_config.event_extractor,
        docling_config=docling_config,
        extractor_config=extractor_config
    )

    return build_extractors(docling_config, event_config, extractor_config)


def validate_extractors(doc_extractor: DocumentExtractor, event_extractor: EventExtractor) -> bool:
    """
    Validate that extractors are properly configured

    Args:
        doc_extractor: Document extractor to validate
        event_extractor: Event extractor to validate

    Returns:
        True if both extractors are valid, False otherwise
    """
    try:
        # Check document extractor
        supported_types = doc_extractor.get_supported_types()
        if not supported_types:
            logger.error("❌ Document extractor supports no file types")
            return False

        # Check event extractor
        if not event_extractor.is_available():
            logger.error("❌ Event extractor is not available")
            return False

        logger.info(f"✅ Extractors validated: {len(supported_types)} file types supported")
        return True

    except Exception as e:
        logger.error(f"❌ Extractor validation failed: {e}")
        return False
