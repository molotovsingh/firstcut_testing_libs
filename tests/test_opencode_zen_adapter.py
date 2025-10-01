"""
Unit tests for OpenCode Zen Event Extractor Adapter
Tests adapter functionality with mocked HTTP responses
"""

import json
import pytest
from unittest.mock import Mock, patch

from src.core.opencode_zen_adapter import OpenCodeZenEventExtractor
from src.core.config import OpenCodeZenConfig
from src.core.extractor_factory import ExtractorConfigurationError
from src.core.interfaces import EventRecord
from src.core.constants import DEFAULT_NO_DATE, DEFAULT_NO_CITATION


class TestOpenCodeZenEventExtractor:
    """Test suite for OpenCode Zen Event Extractor"""

    def test_initialization_success(self):
        """Test successful initialization with valid config"""
        config = OpenCodeZenConfig(
            api_key="test-key",
            base_url="https://api.opencode-zen.example/v1",
            model="opencode-zen/legal-extractor",
            timeout=30
        )

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            extractor = OpenCodeZenEventExtractor(config)

            assert extractor.config == config
            assert extractor.available is True
            assert extractor._http == mock_requests

    def test_initialization_missing_api_key(self):
        """Test initialization fails with missing API key"""
        config = OpenCodeZenConfig(
            api_key="",
            base_url="https://api.opencode-zen.example/v1",
            model="opencode-zen/legal-extractor",
            timeout=30
        )

        with pytest.raises(ExtractorConfigurationError) as exc_info:
            OpenCodeZenEventExtractor(config)

        assert "OpenCode Zen API key is required" in str(exc_info.value)
        assert "OPENCODEZEN_API_KEY" in str(exc_info.value)

    def test_initialization_missing_requests_library(self):
        """Test initialization with missing requests library"""
        config = OpenCodeZenConfig(
            api_key="test-key",
            base_url="https://api.opencode-zen.example/v1",
            model="opencode-zen/legal-extractor",
            timeout=30
        )

        with patch('src.core.opencode_zen_adapter.requests', side_effect=ImportError()):
            extractor = OpenCodeZenEventExtractor(config)

            assert extractor.available is False
            assert extractor._http is None

    def test_is_available_true(self):
        """Test is_available returns True when properly configured"""
        config = OpenCodeZenConfig(api_key="test-key")

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            extractor = OpenCodeZenEventExtractor(config)
            assert extractor.is_available() is True

    def test_is_available_false_no_requests(self):
        """Test is_available returns False when requests not available"""
        config = OpenCodeZenConfig(api_key="test-key")

        with patch('src.core.opencode_zen_adapter.requests', side_effect=ImportError()):
            extractor = OpenCodeZenEventExtractor(config)
            assert extractor.is_available() is False

    def test_is_available_false_no_api_key(self):
        """Test is_available returns False when API key is missing"""
        config = OpenCodeZenConfig(api_key="")

        with pytest.raises(ExtractorConfigurationError):
            OpenCodeZenEventExtractor(config)

    def test_extract_events_success(self):
        """Test successful event extraction"""
        config = OpenCodeZenConfig(api_key="test-key")

        # Mock successful API response
        mock_response_data = {
            "events": [
                {
                    "event_particulars": "On January 15, 2024, the plaintiff filed a motion for summary judgment pursuant to Federal Rule 56.",
                    "citation": "Fed. R. Civ. P. 56",
                    "date": "2024-01-15",
                    "confidence": 0.95,
                    "char_start": 100,
                    "char_end": 200
                },
                {
                    "event_particulars": "Court scheduled hearing for March 10, 2024 under Local Rule 7.1.",
                    "citation": "Local Rule 7.1",
                    "date": "2024-03-10",
                    "confidence": 0.87
                }
            ]
        }

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            # Setup mock HTTP response
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenCodeZenEventExtractor(config)

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
            assert events[0].attributes["provider"] == "opencode_zen"
            assert events[0].attributes["confidence"] == 0.95
            assert events[0].attributes["char_start"] == 100
            assert events[0].attributes["char_end"] == 200

            # Check second event
            assert events[1].number == 2
            assert events[1].date == "2024-03-10"
            assert "hearing" in events[1].event_particulars
            assert events[1].citation == "Local Rule 7.1"
            assert events[1].document_reference == "test_document.pdf"
            assert events[1].attributes["confidence"] == 0.87

    def test_extract_events_alternative_response_formats(self):
        """Test handling of alternative response field names"""
        config = OpenCodeZenConfig(api_key="test-key")

        # Mock response with alternative field names
        mock_response_data = {
            "results": [
                {
                    "description": "Alternative field name for event particulars",
                    "reference": "Alternative citation field",
                    "event_date": "2024-01-15",
                    "confidence": 0.90
                }
            ]
        }

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenCodeZenEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should successfully extract with alternative field names
            assert len(events) == 1
            assert events[0].event_particulars == "Alternative field name for event particulars"
            assert events[0].citation == "Alternative citation field"
            assert events[0].date == "2024-01-15"

    def test_extract_events_api_failure(self):
        """Test handling of API failure"""
        config = OpenCodeZenConfig(api_key="test-key")

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            # Setup mock HTTP failure
            mock_requests.post.side_effect = mock_requests.exceptions.RequestException("API Error")

            extractor = OpenCodeZenEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert isinstance(events[0], EventRecord)
            assert events[0].attributes["fallback"] is True
            assert "OpenCode Zen processing error" in events[0].event_particulars

    def test_extract_events_empty_text(self):
        """Test handling of empty text input"""
        config = OpenCodeZenConfig(api_key="test-key")

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            extractor = OpenCodeZenEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = ""

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert events[0].attributes["fallback"] is True
            assert "No text content to process" in events[0].attributes["reason"]

    def test_extract_events_not_available(self):
        """Test handling when adapter is not available"""
        config = OpenCodeZenConfig(api_key="test-key")

        with patch('src.core.opencode_zen_adapter.requests', side_effect=ImportError()):
            extractor = OpenCodeZenEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert events[0].attributes["fallback"] is True
            assert "not available" in events[0].attributes["reason"]

    def test_extract_events_empty_response(self):
        """Test handling of empty API response"""
        config = OpenCodeZenConfig(api_key="test-key")

        mock_response_data = {"events": []}

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenCodeZenEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should return fallback record
            assert len(events) == 1
            assert events[0].attributes["fallback"] is True

    def test_extract_events_single_event_object(self):
        """Test handling of single event returned as object (not array)"""
        config = OpenCodeZenConfig(api_key="test-key")

        # Mock single event response (not in array)
        mock_response_data = {
            "event_particulars": "Single event response",
            "citation": "Test Citation",
            "date": "2024-01-15",
            "confidence": 0.85
        }

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenCodeZenEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should handle single event object
            assert len(events) == 1
            assert events[0].event_particulars == "Single event response"
            assert events[0].citation == "Test Citation"
            assert events[0].date == "2024-01-15"

    def test_call_opencode_zen_api_request_format(self):
        """Test that API requests are formatted correctly"""
        config = OpenCodeZenConfig(
            api_key="test-key",
            base_url="https://api.opencode-zen.example/v1",
            model="opencode-zen/legal-extractor",
            timeout=30
        )

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = {"events": []}
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenCodeZenEventExtractor(config)
            extractor._call_opencode_zen_api("test text")

            # Verify API call was made correctly
            mock_requests.post.assert_called_once()
            args, kwargs = mock_requests.post.call_args

            # Check URL
            assert args[0] == "https://api.opencode-zen.example/v1/extract"

            # Check headers
            assert kwargs["headers"]["Authorization"] == "Bearer test-key"
            assert kwargs["headers"]["Content-Type"] == "application/json"

            # Check payload structure
            payload = kwargs["json"]
            assert payload["model"] == "opencode-zen/legal-extractor"
            assert payload["text"] == "test text"
            assert payload["task"] == "legal_event_extraction"
            assert payload["format"] == "json"
            assert payload["parameters"]["temperature"] == 0.0
            assert payload["parameters"]["max_events"] == 50

            # Check timeout
            assert kwargs["timeout"] == 30

    def test_extract_events_skip_empty_particulars(self):
        """Test that events without event_particulars are skipped"""
        config = OpenCodeZenConfig(api_key="test-key")

        # Mock response with one valid event and one without particulars
        mock_response_data = {
            "events": [
                {
                    "event_particulars": "",  # Empty particulars - should be skipped
                    "citation": "Test Citation",
                    "date": "2024-01-15"
                },
                {
                    "event_particulars": "Valid event with content",
                    "citation": "Valid Citation",
                    "date": "2024-01-16"
                }
            ]
        }

        with patch('src.core.opencode_zen_adapter.requests') as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_requests.post.return_value = mock_response

            extractor = OpenCodeZenEventExtractor(config)

            metadata = {"document_name": "test_document.pdf"}
            text = "Legal document text..."

            events = extractor.extract_events(text, metadata)

            # Should only return the valid event
            assert len(events) == 1
            assert events[0].event_particulars == "Valid event with content"
            assert events[0].citation == "Valid Citation"