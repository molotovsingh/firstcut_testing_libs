"""
Unit tests for OpenAI Event Extractor Adapter
Tests adapter functionality with mocked OpenAI API responses
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.openai_adapter import OpenAIEventExtractor
from src.core.config import OpenAIConfig
from src.core.extractor_factory import ExtractorConfigurationError
from src.core.interfaces import EventRecord
from src.core.constants import DEFAULT_NO_DATE, DEFAULT_NO_CITATION


class TestOpenAIEventExtractor:
    """Test suite for OpenAI Event Extractor"""

    def test_initialization_success(self):
        """Test successful initialization with valid config"""
        config = OpenAIConfig(
            api_key="sk-test-key-123",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            timeout=60
        )

        with patch('src.core.openai_adapter.OpenAI') as mock_openai:
            extractor = OpenAIEventExtractor(config)

            assert extractor.config == config
            assert extractor.available is True
            assert mock_openai.called

    def test_initialization_missing_api_key(self):
        """Test initialization fails with missing API key"""
        config = OpenAIConfig(
            api_key="",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            timeout=60
        )

        with pytest.raises(ExtractorConfigurationError) as exc_info:
            OpenAIEventExtractor(config)

        assert "OpenAI API key is required" in str(exc_info.value)
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_initialization_missing_openai_library(self):
        """Test initialization with missing openai library"""
        config = OpenAIConfig(
            api_key="sk-test-key-123",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            timeout=60
        )

        with patch('src.core.openai_adapter.OpenAI', side_effect=ImportError()):
            extractor = OpenAIEventExtractor(config)

            assert extractor.available is False
            assert extractor._client is None

    def test_initialization_client_error(self):
        """Test initialization with OpenAI client creation error"""
        config = OpenAIConfig(
            api_key="sk-test-key-123",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            timeout=60
        )

        with patch('src.core.openai_adapter.OpenAI', side_effect=Exception("Client init failed")):
            extractor = OpenAIEventExtractor(config)

            assert extractor.available is False

    def test_json_mode_support_detection(self):
        """Test JSON mode support detection for different models"""
        config_gpt4o = OpenAIConfig(api_key="sk-test", model="gpt-4o")
        config_gpt4_turbo = OpenAIConfig(api_key="sk-test", model="gpt-4-turbo")
        config_gpt35 = OpenAIConfig(api_key="sk-test", model="gpt-3.5-turbo-1106")
        config_unsupported = OpenAIConfig(api_key="sk-test", model="gpt-3.5-turbo")

        with patch('src.core.openai_adapter.OpenAI'):
            extractor_4o = OpenAIEventExtractor(config_gpt4o)
            extractor_4_turbo = OpenAIEventExtractor(config_gpt4_turbo)
            extractor_35_1106 = OpenAIEventExtractor(config_gpt35)
            extractor_unsupported = OpenAIEventExtractor(config_unsupported)

            assert extractor_4o._supports_json_mode is True
            assert extractor_4_turbo._supports_json_mode is True
            assert extractor_35_1106._supports_json_mode is True
            assert extractor_unsupported._supports_json_mode is False

    def test_is_available_true(self):
        """Test is_available returns True when properly configured"""
        config = OpenAIConfig(api_key="sk-test-key")

        with patch('src.core.openai_adapter.OpenAI'):
            extractor = OpenAIEventExtractor(config)
            assert extractor.is_available() is True

    def test_is_available_false_no_client(self):
        """Test is_available returns False when client not available"""
        config = OpenAIConfig(api_key="sk-test-key")

        with patch('src.core.openai_adapter.OpenAI', side_effect=ImportError()):
            extractor = OpenAIEventExtractor(config)
            assert extractor.is_available() is False

    def test_extract_events_success(self):
        """Test successful event extraction"""
        config = OpenAIConfig(api_key="sk-test-key", model="gpt-4o-mini")

        # Mock successful API response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=json.dumps([
                {
                    "event_particulars": "On January 15, 2024, the plaintiff filed a motion for summary judgment.",
                    "citation": "Fed. R. Civ. P. 56",
                    "document_reference": "",
                    "date": "2024-01-15"
                },
                {
                    "event_particulars": "On January 20, 2024, the defendant filed an opposition to the motion.",
                    "citation": "",
                    "document_reference": "",
                    "date": "2024-01-20"
                }
            ])))
        ]
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )

        with patch('src.core.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            extractor = OpenAIEventExtractor(config)

            # Test extraction
            text = "Test legal document text"
            metadata = {"document_name": "test_document.pdf"}

            events = extractor.extract_events(text, metadata)

            # Verify results
            assert len(events) == 2
            assert isinstance(events[0], EventRecord)

            # First event
            assert events[0].date == "2024-01-15"
            assert "motion for summary judgment" in events[0].event_particulars
            assert events[0].citation == "Fed. R. Civ. P. 56"
            assert events[0].document_reference == "test_document.pdf"

            # Second event
            assert events[1].date == "2024-01-20"
            assert "opposition" in events[1].event_particulars
            assert events[1].citation == DEFAULT_NO_CITATION
            assert events[1].document_reference == "test_document.pdf"

            # Verify OpenAI API was called correctly
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o-mini"
            assert call_kwargs["temperature"] == 0.0
            assert "response_format" in call_kwargs  # JSON mode enabled
            assert call_kwargs["response_format"] == {"type": "json_object"}

    def test_extract_events_empty_text(self):
        """Test extraction with empty text returns fallback"""
        config = OpenAIConfig(api_key="sk-test-key")

        with patch('src.core.openai_adapter.OpenAI'):
            extractor = OpenAIEventExtractor(config)

            metadata = {"document_name": "empty_doc.pdf"}
            events = extractor.extract_events("", metadata)

            # Should return fallback event
            assert len(events) == 1
            assert events[0].document_reference == "empty_doc.pdf"
            assert "No text content" in events[0].event_particulars

    def test_extract_events_adapter_not_available(self):
        """Test extraction when adapter is not available"""
        config = OpenAIConfig(api_key="sk-test-key")

        with patch('src.core.openai_adapter.OpenAI', side_effect=ImportError()):
            extractor = OpenAIEventExtractor(config)

            metadata = {"document_name": "test.pdf"}
            events = extractor.extract_events("Some text", metadata)

            # Should return fallback event
            assert len(events) == 1
            assert "not available" in events[0].event_particulars.lower()

    def test_extract_events_api_error_with_retry(self):
        """Test extraction with API error and retry logic"""
        config = OpenAIConfig(api_key="sk-test-key", model="gpt-4o-mini")

        with patch('src.core.openai_adapter.OpenAI') as mock_openai_class:
            from openai import RateLimitError

            # First two calls fail with rate limit, third succeeds
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content=json.dumps([
                {"event_particulars": "Test event", "citation": "", "document_reference": "", "date": ""}
            ])))]
            mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

            mock_client.chat.completions.create.side_effect = [
                RateLimitError("Rate limit hit", response=Mock(status_code=429), body=None),
                RateLimitError("Rate limit hit", response=Mock(status_code=429), body=None),
                mock_response
            ]
            mock_openai_class.return_value = mock_client

            extractor = OpenAIEventExtractor(config)

            with patch('time.sleep'):  # Don't actually sleep in tests
                events = extractor.extract_events("Test text", {"document_name": "test.pdf"})

            # Should succeed after retries
            assert len(events) == 1
            assert mock_client.chat.completions.create.call_count == 3

    def test_extract_events_max_retries_exceeded(self):
        """Test extraction fails after max retries"""
        config = OpenAIConfig(api_key="sk-test-key")

        with patch('src.core.openai_adapter.OpenAI') as mock_openai_class:
            from openai import RateLimitError

            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = RateLimitError(
                "Rate limit",
                response=Mock(status_code=429),
                body=None
            )
            mock_openai_class.return_value = mock_client

            extractor = OpenAIEventExtractor(config)

            with patch('time.sleep'):
                events = extractor.extract_events("Test text", {"document_name": "test.pdf"})

            # Should return fallback after max retries
            assert len(events) == 1
            assert mock_client.chat.completions.create.call_count == 4  # 1 + 3 retries

    def test_cost_calculation_gpt4o(self):
        """Test cost calculation for GPT-4o"""
        config = OpenAIConfig(api_key="sk-test", model="gpt-4o")

        with patch('src.core.openai_adapter.OpenAI'):
            extractor = OpenAIEventExtractor(config)

            # GPT-4o pricing: $2.50/$10.00 per 1M tokens
            cost = extractor._calculate_cost(prompt_tokens=1000, completion_tokens=500)
            expected = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)
            assert abs(cost - expected) < 0.0001

    def test_cost_calculation_gpt4o_mini(self):
        """Test cost calculation for GPT-4o-mini"""
        config = OpenAIConfig(api_key="sk-test", model="gpt-4o-mini")

        with patch('src.core.openai_adapter.OpenAI'):
            extractor = OpenAIEventExtractor(config)

            # GPT-4o-mini pricing: $0.15/$0.60 per 1M tokens
            cost = extractor._calculate_cost(prompt_tokens=1000, completion_tokens=500)
            expected = (1000 / 1_000_000 * 0.15) + (500 / 1_000_000 * 0.60)
            assert abs(cost - expected) < 0.0001

    def test_cost_calculation_unknown_model(self):
        """Test cost calculation defaults to gpt-4o-mini for unknown models"""
        config = OpenAIConfig(api_key="sk-test", model="gpt-future-model")

        with patch('src.core.openai_adapter.OpenAI'):
            extractor = OpenAIEventExtractor(config)

            # Should default to gpt-4o-mini pricing
            cost = extractor._calculate_cost(prompt_tokens=1000, completion_tokens=500)
            expected = (1000 / 1_000_000 * 0.15) + (500 / 1_000_000 * 0.60)
            assert abs(cost - expected) < 0.0001

    def test_extract_events_invalid_json_response(self):
        """Test extraction handles invalid JSON response"""
        config = OpenAIConfig(api_key="sk-test", model="gpt-4o-mini")

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Not valid JSON"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        with patch('src.core.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            extractor = OpenAIEventExtractor(config)
            events = extractor.extract_events("Test", {"document_name": "test.pdf"})

            # Should return fallback for invalid JSON
            assert len(events) == 1
            assert "error" in events[0].event_particulars.lower() or "failed" in events[0].event_particulars.lower()

    def test_extract_events_document_name_extraction(self):
        """Test document name extraction from various metadata formats"""
        config = OpenAIConfig(api_key="sk-test", model="gpt-4o-mini")

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=json.dumps([
            {"event_particulars": "Test", "citation": "", "document_reference": "", "date": ""}
        ])))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        with patch('src.core.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            extractor = OpenAIEventExtractor(config)

            # Test with file_path containing directory
            events = extractor.extract_events("Text", {"file_path": "/path/to/document.pdf"})
            assert events[0].document_reference == "document.pdf"

            # Test with document_name directly
            events = extractor.extract_events("Text", {"document_name": "direct_name.pdf"})
            assert events[0].document_reference == "direct_name.pdf"

            # Test with no metadata
            events = extractor.extract_events("Text", {})
            assert events[0].document_reference == "Unknown document"

    def test_json_mode_disabled_for_unsupported_model(self):
        """Test that JSON mode is not used for unsupported models"""
        config = OpenAIConfig(api_key="sk-test", model="gpt-3.5-turbo")

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=json.dumps([
            {"event_particulars": "Test", "citation": "", "document_reference": "", "date": ""}
        ])))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        with patch('src.core.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            extractor = OpenAIEventExtractor(config)
            extractor.extract_events("Text", {"document_name": "test.pdf"})

            # Verify response_format was NOT included for unsupported model
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert "response_format" not in call_kwargs

    def test_fallback_record_creation(self):
        """Test fallback record creation with proper structure"""
        config = OpenAIConfig(api_key="sk-test")

        with patch('src.core.openai_adapter.OpenAI'):
            extractor = OpenAIEventExtractor(config)

            # Create fallback record
            fallback = extractor._create_fallback_record("test.pdf", "Test reason")

            assert isinstance(fallback, EventRecord)
            assert fallback.number == 1
            assert fallback.date == DEFAULT_NO_DATE
            assert "Test reason" in fallback.event_particulars
            assert fallback.citation == DEFAULT_NO_CITATION
            assert fallback.document_reference == "test.pdf"
            assert fallback.attributes["fallback"] is True
            assert fallback.attributes["reason"] == "Test reason"
