"""
Unit tests for OpenRouter Event Extractor Adapter
Tests adapter functionality with mocked HTTP responses
"""

import json
import pytest
from unittest.mock import Mock, patch

from src.core.openrouter_adapter import OpenRouterEventExtractor
from src.core.config import OpenRouterConfig
from src.core.extractor_factory import ExtractorConfigurationError
from src.core.interfaces import EventRecord
from src.core.constants import DEFAULT_NO_DATE, DEFAULT_NO_CITATION


class TestOpenRouterEventExtractor:
    """Test suite for OpenRouter Event Extractor"""

    def test_initialization_success(self):
        """Test successful initialization with valid config"""
        config = OpenRouterConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-3-haiku",
            timeout=30
        )

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            extractor = OpenRouterEventExtractor(config)

            assert extractor.config == config
            assert extractor.available is True
            assert extractor._http == mock_requests

    def test_initialization_missing_api_key(self):
        """Test initialization fails with missing API key"""
        config = OpenRouterConfig(
            api_key="",
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-3-haiku",
            timeout=30
        )

        with pytest.raises(ExtractorConfigurationError) as exc_info:
            OpenRouterEventExtractor(config)

        assert "OpenRouter API key is required" in str(exc_info.value)
        assert "OPENROUTER_API_KEY" in str(exc_info.value)

    def test_initialization_missing_requests_library(self):
        """Test initialization with missing requests library"""
        config = OpenRouterConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-3-haiku",
            timeout=30
        )

        with patch('src.core.openrouter_adapter.requests', side_effect=ImportError()):
            extractor = OpenRouterEventExtractor(config)

            assert extractor.available is False
            assert extractor._http is None

    def test_is_available_true(self):
        """Test is_available returns True when properly configured"""
        config = OpenRouterConfig(api_key="test-key")

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            extractor = OpenRouterEventExtractor(config)
            assert extractor.is_available() is True

    def test_is_available_false_no_requests(self):
        """Test is_available returns False when requests not available"""
        config = OpenRouterConfig(api_key="test-key")

        with patch('src.core.openrouter_adapter.requests', side_effect=ImportError()):
            extractor = OpenRouterEventExtractor(config)
            assert extractor.is_available() is False

    def test_is_available_false_no_api_key(self):
        """Test is_available returns False when API key is missing"""
        config = OpenRouterConfig(api_key="")

        with pytest.raises(ExtractorConfigurationError):
            OpenRouterEventExtractor(config)

    def test_extract_events_success(self):
        """Test successful event extraction"""
        config = OpenRouterConfig(api_key="test-key")

        # Mock successful API response
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "event_particulars": "On January 15, 2024, the plaintiff filed a motion for summary judgment.",
                            "citation": "Fed. R. Civ. P. 56",
                            "date": "2024-01-15",
                            "document_reference": ""
                        },
                        {
                            "event_particulars": "Court scheduled hearing for March 10, 2024.",
                            "citation": "",
                            "date": "2024-03-10",
                            "document_reference": ""
                        }
                    ])
                }
            }]
        }

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            # Setup mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenRouterEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text with events..."

            events = extractor.extract_events(text, metadata)

            # Verify results
            assert len(events) == 2
            assert all(isinstance(event, EventRecord) for event in events)

            # Check first event
            assert events[0].number == 1
            assert events[0].date == "2024-01-15"
            assert "summary judgment" in events[0].event_particulars
            assert events[0].citation == "Fed. R. Civ. P. 56"
            assert events[0].document_reference == "test_document.pdf"
            assert events[0].attributes["provider"] == "openrouter"

            # Check second event
            assert events[1].number == 2
            assert events[1].date == "2024-03-10"
            assert "hearing" in events[1].event_particulars
            assert events[1].citation == DEFAULT_NO_CITATION
            assert events[1].document_reference == "test_document.pdf"

    def test_extract_events_api_failure(self):
        """Test handling of API failure"""
        config = OpenRouterConfig(api_key="test-key")

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            # Setup mock HTTP failure
            mock_requests.post.side_effect = mock_requests.exceptions.RequestException("API Error")

            extractor = OpenRouterEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert isinstance(events[0], EventRecord)
            assert events[0].attributes["fallback"] is True
            assert "OpenRouter processing error" in events[0].event_particulars

    def test_extract_events_empty_text(self):
        """Test handling of empty text input"""
        config = OpenRouterConfig(api_key="test-key")

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            extractor = OpenRouterEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = ""

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert events[0].attributes["fallback"] is True
            assert "No text content to process" in events[0].attributes["reason"]

    def test_extract_events_not_available(self):
        """Test handling when adapter is not available"""
        config = OpenRouterConfig(api_key="test-key")

        with patch('src.core.openrouter_adapter.requests', side_effect=ImportError()):
            extractor = OpenRouterEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert events[0].attributes["fallback"] is True
            assert "not available" in events[0].attributes["reason"]

    def test_extract_events_invalid_json_response(self):
        """Test handling of invalid JSON response"""
        config = OpenRouterConfig(api_key="test-key")

        # Mock response with invalid JSON
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": "invalid json content"
                }
            }]
        }

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenRouterEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should return fallback record for invalid JSON
            assert len(events) == 1
            assert events[0].attributes["fallback"] is True

    def test_extract_events_empty_response(self):
        """Test handling of empty API response"""
        config = OpenRouterConfig(api_key="test-key")

        mock_response_data = {"choices": []}

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenRouterEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert events[0].attributes["fallback"] is True

    def test_call_openrouter_api_request_format(self):
        """Test that API requests are formatted correctly"""
        config = OpenRouterConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-3-haiku",
            timeout=30
        )

        with patch('src.core.openrouter_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = {"choices": [{"message": {"content": "[]"}}]}
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenRouterEventExtractor(config)
            extractor._call_openrouter_api("test text")

            # Verify API call was made correctly
            mock_requests.post.assert_called_once()
            args, kwargs = mock_requests.post.call_args

            # Check URL
            assert args[0] == "https://openrouter.ai/api/v1/chat/completions"

            # Check headers
            assert kwargs["headers"]["Authorization"] == "Bearer test-key"
            assert kwargs["headers"]["Content-Type"] == "application/json"

            # Check payload structure
            payload = kwargs["json"]
            assert payload["model"] == "anthropic/claude-3-haiku"
            assert payload["temperature"] == 0.0
            assert payload["response_format"]["type"] == "json_object"
            assert len(payload["messages"]) == 2
            assert payload["messages"][0]["role"] == "system"
            assert payload["messages"][1]["role"] == "user"

            # Check timeout
            assert kwargs["timeout"] == 30