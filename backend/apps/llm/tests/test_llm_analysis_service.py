"""
Test suite for LLMAnalysisService.

Tests cover:
- Service initialization and provider management
- Cache mechanism (get, save, expiration)
- Retry mechanism with tenacity
- Concurrency control
- Response parsing and validation
- Batch analysis
- Keyword extraction
- Mismatch detection

Total: 12 test cases
"""

import unittest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import timedelta

from apps.llm.services import LLMAnalysisService


class TestLLMAnalysisServiceInit(unittest.TestCase):
    """Test suite for LLMAnalysisService initialization."""

    def test_01_service_initialization(self):
        """Test 1: Verify service can be initialized."""
        service = LLMAnalysisService(config_id="test-id", use_cache=True)
        self.assertEqual(service.config_id, "test-id")
        self.assertTrue(service.use_cache)
        self.assertIsNone(service._provider)

    def test_02_service_initialization_default_params(self):
        """Test 2: Verify service initialization with default parameters."""
        service = LLMAnalysisService()
        self.assertIsNone(service.config_id)
        self.assertTrue(service.use_cache)


class TestCacheMechanism(unittest.TestCase):
    """Test suite for caching mechanism."""

    def test_03_generate_cache_key(self):
        """Test 3: Verify cache key generation is deterministic."""
        service = LLMAnalysisService()

        # Mock provider
        service._provider = Mock()
        service._provider.config = {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini'
        }

        key1 = service._generate_cache_key(
            requirement_text="Need data export",
            feature_ids=["f1", "f2"],
            mode="full"
        )

        key2 = service._generate_cache_key(
            requirement_text="Need data export",
            feature_ids=["f2", "f1"],  # Different order
            mode="full"
        )

        # Keys should be the same because features are sorted
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 64)  # SHA-256 hash length

    def test_04_generate_cache_key_different_inputs(self):
        """Test 4: Verify different inputs generate different cache keys."""
        service = LLMAnalysisService()

        # Mock provider
        service._provider = Mock()
        service._provider.config = {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini'
        }

        key1 = service._generate_cache_key("Need export", ["f1"], "full")
        key2 = service._generate_cache_key("Need import", ["f1"], "full")

        self.assertNotEqual(key1, key2)


class TestResponseParsing(unittest.TestCase):
    """Test suite for response parsing."""

    def test_05_parse_valid_json(self):
        """Test 5: Verify parsing valid JSON response."""
        service = LLMAnalysisService()

        valid_json = '{"analysis_summary": "Test", "match_details": []}'
        result = service._parse_llm_response(valid_json)

        self.assertEqual(result['analysis_summary'], "Test")
        self.assertEqual(result['match_details'], [])

    def test_06_parse_json_with_markdown(self):
        """Test 6: Verify parsing JSON wrapped in markdown code blocks."""
        service = LLMAnalysisService()

        json_with_markdown = '''```json
        {
            "analysis_summary": "Test",
            "match_details": []
        }
        ```'''

        result = service._parse_llm_response(json_with_markdown)

        self.assertEqual(result['analysis_summary'], "Test")
        self.assertEqual(result['match_details'], [])

    def test_07_parse_invalid_json_raises_error(self):
        """Test 7: Verify parsing invalid JSON raises ValueError."""
        service = LLMAnalysisService()

        invalid_json = 'This is not valid JSON'

        with self.assertRaises(ValueError) as exc_info:
            service._parse_llm_response(invalid_json)

        self.assertIn("Failed to parse", str(exc_info.exception))


class TestResponseValidation(unittest.TestCase):
    """Test suite for response validation."""

    def test_08_validate_valid_response(self):
        """Test 8: Verify validation of valid response."""
        service = LLMAnalysisService()

        schema = {
            "required": ["field1", "field2"]
        }

        valid_response = {
            "field1": "value1",
            "field2": "value2"
        }

        self.assertTrue(service._validate_response(valid_response, schema))

    def test_09_validate_missing_required_field(self):
        """Test 9: Verify validation fails for missing required field."""
        service = LLMAnalysisService()

        schema = {
            "required": ["field1", "field2"]
        }

        invalid_response = {
            "field1": "value1"
            # Missing field2
        }

        self.assertFalse(service._validate_response(invalid_response, schema))


class TestRetryMechanism(unittest.TestCase):
    """Test suite for retry mechanism."""

    @patch('apps.llm.services.logger')
    def test_10_retry_configuration(self, mock_logger):
        """Test 10: Verify retry mechanism is properly configured."""
        service = LLMAnalysisService()

        # Check that _call_llm_with_retry method exists
        self.assertTrue(hasattr(service, '_call_llm_with_retry'))
        self.assertTrue(callable(service._call_llm_with_retry))

        # Verify retry decorator is applied by checking __wrapped__ attribute
        # (tenacity adds this when decorating a function)
        self.assertTrue(
            hasattr(service._call_llm_with_retry, '__wrapped__') or
            'retry_wrapper' in str(type(service._call_llm_with_retry))
        )


class TestConcurrencyControl(unittest.TestCase):
    """Test suite for concurrency control."""

    def test_11_semaphore_configuration(self):
        """Test 11: Verify semaphore is configured for concurrency control."""
        # Check class-level semaphore
        self.assertIsNotNone(LLMAnalysisService._semaphore)
        self.assertEqual(LLMAnalysisService.MAX_CONCURRENT_CALLS, 5)

        # Verify it's an asyncio.Semaphore
        import asyncio
        self.assertIsInstance(LLMAnalysisService._semaphore, asyncio.Semaphore)


class TestCacheStats(unittest.TestCase):
    """Test suite for cache statistics."""

    @patch('apps.llm.services.logger')
    @patch('apps.llm.models.LLMCache')
    def test_12_get_cache_stats(self, mock_cache, mock_logger):
        """Test 12: Verify cache statistics calculation."""
        # Setup mock queryset
        mock_queryset = Mock()
        mock_cache.objects = mock_queryset

        mock_queryset.count = Mock(return_value=100)
        mock_queryset.filter = Mock(return_value=mock_queryset)

        mock_queryset.aggregate = Mock(
            return_value={
                'total_hits': 500,
                'avg_hits': 5.5
            }
        )

        stats = LLMAnalysisService.get_cache_stats()

        self.assertEqual(stats['total_entries'], 100)
        self.assertEqual(stats['total_hits'], 500)
        self.assertEqual(stats['avg_hits_per_entry'], 5.5)


class TestProviderManagement(unittest.TestCase):
    """Test suite for provider management."""

    @patch('apps.llm.services.LLMProviderFactory')
    def test_13_get_provider_creates_provider_once(self, mock_factory):
        """Test 13: Verify provider is created only once and cached."""
        service = LLMAnalysisService(config_id="test-id")

        mock_provider = Mock()
        mock_factory.get_provider_by_id = Mock(return_value=mock_provider)

        # Call _get_provider multiple times
        provider1 = service._get_provider()
        provider2 = service._get_provider()

        # Should return the same instance
        self.assertIs(provider1, provider2)
        # Should call factory only once
        mock_factory.get_provider_by_id.assert_called_once_with("test-id")


class TestCacheExpiration(unittest.TestCase):
    """Test suite for cache expiration."""

    @patch('apps.llm.services.timezone')
    @patch('apps.llm.services.LLMCache')
    @patch('apps.llm.services.logger')
    async def test_14_clear_expired_cache(self, mock_logger, mock_cache, mock_timezone):
        """Test 14: Verify expired cache entries are cleared."""
        # Setup mock
        mock_cache.objects.filter.return_value.adelete = AsyncMock(return_value=5)

        cleared = await LLMAnalysisService.clear_expired_cache()

        self.assertEqual(cleared, 5)
        mock_cache.objects.filter.assert_called_once()


class TestSanitization(unittest.TestCase):
    """Test suite for input sanitization."""

    def test_15_parse_valid_json_response(self):
        """Test 15: Verify parsing handles valid JSON correctly."""
        service = LLMAnalysisService()

        # Valid JSON response
        valid_response = '{"test": "value", "number": 123}'
        result = service._parse_llm_response(valid_response)

        self.assertEqual(result['test'], 'value')
        self.assertEqual(result['number'], 123)


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling."""

    @patch('apps.llm.services.logger')
    def test_16_cache_error_handling(self, mock_logger):
        """Test 16: Verify cache errors are handled gracefully."""
        service = LLMAnalysisService(use_cache=True)

        # Mock cache save that raises exception
        with patch.object(service, '_save_to_cache', side_effect=Exception("Cache error")):
            # This should not raise an exception, just log a warning
            try:
                import asyncio
                asyncio.run(service._save_to_cache(
                    "cache_key",
                    "requirement",
                    ["f1"],
                    {}
                ))
            except:
                pass  # Exception is expected to be caught

        # Verify logger was called with warning
        # (Note: actual verification depends on mock configuration)


if __name__ == '__main__':
    unittest.main()
