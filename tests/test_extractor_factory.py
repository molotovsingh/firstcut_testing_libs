"""Tests for the extractor factory registry bootstrap."""

import pytest

from src.core import extractor_factory
from src.core.config import (
    DoclingConfig, LangExtractConfig, ExtractorConfig,
    OpenRouterConfig, OpenCodeZenConfig
)


class DummyDoclingExtractor:
    """Lightweight stand-in for DoclingDocumentExtractor."""

    def __init__(self, config: DoclingConfig):
        self.config = config

    def get_supported_types(self):  # pragma: no cover - interface stub
        return ["pdf"]


class DummyLangExtractEventExtractor:
    """Lightweight stand-in for LangExtractEventExtractor."""

    def __init__(self, config: LangExtractConfig):
        self.config = config

    def is_available(self):  # pragma: no cover - interface stub
        return True


class DummyOpenRouterEventExtractor:
    """Lightweight stand-in for OpenRouterEventExtractor."""

    def __init__(self, config: OpenRouterConfig):
        self.config = config

    def is_available(self):  # pragma: no cover - interface stub
        return True


class DummyOpenCodeZenEventExtractor:
    """Lightweight stand-in for OpenCodeZenEventExtractor."""

    def __init__(self, config: OpenCodeZenConfig):
        self.config = config

    def is_available(self):  # pragma: no cover - interface stub
        return True


@pytest.fixture(autouse=True)
def patch_default_extractors(monkeypatch):
    """Replace heavy adapters with light stubs for tests."""
    monkeypatch.setattr(extractor_factory, "DoclingDocumentExtractor", DummyDoclingExtractor)
    monkeypatch.setattr(extractor_factory, "LangExtractEventExtractor", DummyLangExtractEventExtractor)
    monkeypatch.setattr(extractor_factory, "OpenRouterEventExtractor", DummyOpenRouterEventExtractor)
    monkeypatch.setattr(extractor_factory, "OpenCodeZenEventExtractor", DummyOpenCodeZenEventExtractor)
    yield


def test_build_extractors_uses_langextract_by_default():
    """Default configuration should resolve the LangExtract adapter via the registry."""
    doc_config = DoclingConfig()
    lang_config = LangExtractConfig()
    extractor_config = ExtractorConfig()

    doc_extractor, event_extractor = extractor_factory.build_extractors(
        doc_config,
        lang_config,
        extractor_config,
    )

    assert isinstance(doc_extractor, DummyDoclingExtractor)
    assert isinstance(event_extractor, DummyLangExtractEventExtractor)


def test_build_extractors_openrouter_provider():
    """OpenRouter configuration should resolve the OpenRouter adapter via the registry."""
    doc_config = DoclingConfig()
    openrouter_config = OpenRouterConfig(api_key="test-key")
    extractor_config = ExtractorConfig(event_extractor="openrouter")

    doc_extractor, event_extractor = extractor_factory.build_extractors(
        doc_config,
        openrouter_config,
        extractor_config,
    )

    assert isinstance(doc_extractor, DummyDoclingExtractor)
    assert isinstance(event_extractor, DummyOpenRouterEventExtractor)


def test_build_extractors_opencode_zen_provider():
    """OpenCode Zen configuration should resolve the OpenCode Zen adapter via the registry."""
    doc_config = DoclingConfig()
    opencode_zen_config = OpenCodeZenConfig(api_key="test-key")
    extractor_config = ExtractorConfig(event_extractor="opencode_zen")

    doc_extractor, event_extractor = extractor_factory.build_extractors(
        doc_config,
        opencode_zen_config,
        extractor_config,
    )

    assert isinstance(doc_extractor, DummyDoclingExtractor)
    assert isinstance(event_extractor, DummyOpenCodeZenEventExtractor)


def test_build_extractors_unknown_event_provider_raises():
    """An invalid event provider key should raise an ExtractorConfigurationError."""
    doc_config = DoclingConfig()
    lang_config = LangExtractConfig()
    extractor_config = ExtractorConfig(event_extractor="unknown")

    with pytest.raises(extractor_factory.ExtractorConfigurationError) as exc:
        extractor_factory.build_extractors(
            doc_config,
            lang_config,
            extractor_config,
        )

    assert "unknown" in str(exc.value)
    assert "langextract" in str(exc.value)
    assert "openrouter" in str(exc.value)
    assert "opencode_zen" in str(exc.value)


def test_registry_contains_all_providers():
    """Verify that all expected providers are registered."""
    registry = extractor_factory.EVENT_PROVIDER_REGISTRY

    assert "langextract" in registry
    assert "openrouter" in registry
    assert "opencode_zen" in registry
    assert len(registry) == 3
