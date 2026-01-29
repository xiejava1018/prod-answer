"""
Unit tests for LLM providers.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from apps.llm.providers.base import BaseLLMProvider
from apps.llm.providers.openai_provider import OpenAIProvider
from apps.llm.providers.zhipuai_provider import ZhipuAIProvider
from apps.llm.providers.qwen_provider import QwenProvider
from apps.llm.services import LLMProviderFactory, LLMService


@pytest.fixture
def sample_config():
    """Sample LLM configuration."""
    return {
        'provider': 'openai',
        'model_name': 'gpt-4o-mini',
        'api_key': 'test-api-key',
        'max_tokens': 2000,
        'temperature': 0.7,
    }


@pytest.fixture
def sample_requirement():
    """Sample user requirement."""
    return "需要支持资产自动发现和映射功能"


@pytest.fixture
def sample_matches():
    """Sample match results."""
    return [
        {
            'feature_id': 'f1',
            'feature_name': '资产自动发现',
            'feature_description': '支持自动扫描网络中的资产并发现其信息',
            'similarity_score': 0.92,
            'status': 'full_match'
        },
        {
            'feature_id': 'f2',
            'feature_name': '资产映射',
            'feature_description': '将发现的资产映射到业务系统',
            'similarity_score': 0.78,
            'status': 'partial_match'
        },
        {
            'feature_id': 'f3',
            'feature_name': '漏洞扫描',
            'feature_description': '扫描资产的漏洞信息',
            'similarity_score': 0.65,
            'status': 'no_match'
        },
    ]


class TestBaseLLMProvider:
    """Test BaseLLMProvider abstract class."""

    def test_cannot_instantiate_base_class(self, sample_config):
        """Test that BaseLLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider(sample_config)

    def test_sanitize_input(self, sample_config):
        """Test input sanitization."""
        # Create a concrete implementation for testing
        class TestProvider(BaseLLMProvider):
            async def analyze_matches(self, requirement, matches, threshold=0.75):
                return {}

            async def generate_explanation(self, requirement, feature, similarity_score):
                return ""

            async def suggest_improvements(self, requirement, unmatched_features):
                return {}

        provider = TestProvider(sample_config)

        # Test null byte removal
        text = "test\x00text"
        assert provider.sanitize_input(text) == "testtext"

        # Test length truncation
        long_text = "a" * 20000
        result = provider.sanitize_input(long_text, max_length=100)
        assert len(result) <= 103  # 100 + "..."

    def test_estimate_cost(self, sample_config):
        """Test cost estimation."""
        class TestProvider(BaseLLMProvider):
            async def analyze_matches(self, requirement, matches, threshold=0.75):
                return {}

            async def generate_explanation(self, requirement, feature, similarity_score):
                return ""

            async def suggest_improvements(self, requirement, unmatched_features):
                return {}

        provider = TestProvider(sample_config)

        cost = provider.estimate_cost(1000, 500)

        assert 'input_cost' in cost
        assert 'output_cost' in cost
        assert 'total_cost' in cost
        assert 'currency' in cost
        assert cost['currency'] == 'USD'
        assert cost['total_cost'] == cost['input_cost'] + cost['output_cost']

    def test_validate_response(self, sample_config):
        """Test response validation."""
        class TestProvider(BaseLLMProvider):
            async def analyze_matches(self, requirement, matches, threshold=0.75):
                return {}

            async def generate_explanation(self, requirement, feature, similarity_score):
                return ""

            async def suggest_improvements(self, requirement, unmatched_features):
                return {}

        provider = TestProvider(sample_config)

        # Valid response
        valid_response = {
            'summary': 'Test summary',
            'detailed_analysis': [],
            'confidence': 0.85
        }
        assert provider.validate_response(valid_response) is True

        # Missing field
        invalid_response = {
            'summary': 'Test summary',
            'detailed_analysis': []
        }
        with pytest.raises(ValueError, match="Missing required field"):
            provider.validate_response(invalid_response)

        # Invalid confidence
        invalid_response = {
            'summary': 'Test summary',
            'detailed_analysis': [],
            'confidence': 1.5
        }
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            provider.validate_response(invalid_response)


class TestOpenAIProvider:
    """Test OpenAI provider."""

    def test_initialization(self, sample_config):
        """Test provider initialization."""
        provider = OpenAIProvider(sample_config)

        assert provider.model == 'gpt-4o-mini'
        assert provider.api_key == 'test-api-key'
        assert provider.max_tokens == 2000
        assert provider.temperature == 0.7

    def test_initialization_requires_api_key(self):
        """Test that API key is required."""
        config = {'provider': 'openai', 'model_name': 'gpt-4o-mini'}
        with pytest.raises(ValueError, match="API key is required"):
            OpenAIProvider(config)

    def test_get_model_pricing(self, sample_config):
        """Test model pricing."""
        provider = OpenAIProvider(sample_config)

        pricing = provider.get_model_pricing()
        assert 'input_per_1k' in pricing
        assert 'output_per_1k' in pricing
        assert pricing['input_per_1k'] == 0.00015  # gpt-4o-mini pricing
        assert pricing['output_per_1k'] == 0.0006

    @pytest.mark.asyncio
    async def test_analyze_matches(self, sample_config, sample_requirement, sample_matches):
        """Test match analysis."""
        provider = OpenAIProvider(sample_config)

        # Mock the API call
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "summary": "测试摘要",
            "detailed_analysis": [
                {
                    "feature_id": "f1",
                    "feature_name": "资产自动发现",
                    "match_quality": "high",
                    "explanation": "完全匹配",
                    "confidence": 0.95
                }
            ],
            "recommendations": ["建议1"],
            "confidence": 0.85
        }'''
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        with patch.object(provider, '_call_api', new_callable=AsyncMock, return_value=mock_response):
            result = await provider.analyze_matches(sample_requirement, sample_matches)

            assert result['summary'] == '测试摘要'
            assert len(result['detailed_analysis']) > 0
            assert 'tokens_used' in result
            assert 'estimated_cost' in result

    @pytest.mark.asyncio
    async def test_generate_explanation(self, sample_config, sample_requirement):
        """Test explanation generation."""
        provider = OpenAIProvider(sample_config)

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "这是一个完全匹配的特征"

        with patch.object(provider, '_call_api', new_callable=AsyncMock, return_value=mock_response):
            feature = {
                'feature_name': '资产自动发现',
                'feature_description': '支持自动扫描网络中的资产'
            }

            explanation = await provider.generate_explanation(sample_requirement, feature, 0.92)

            assert explanation == "这是一个完全匹配的特征"

    @pytest.mark.asyncio
    async def test_test_connection(self, sample_config):
        """Test connection testing."""
        provider = OpenAIProvider(sample_config)

        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]

        with patch.object(provider.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await provider.test_connection()
            assert result is True

        # Mock failed response
        with patch.object(provider.client.chat.completions, 'create', new_callable=AsyncMock, side_effect=Exception("API Error")):
            result = await provider.test_connection()
            assert result is False


class TestZhipuAIProvider:
    """Test ZhipuAI provider."""

    def test_initialization(self):
        """Test provider initialization."""
        config = {
            'provider': 'zhipuai',
            'model_name': 'glm-4-flash',
            'api_key': 'test-api-key',
        }
        provider = ZhipuAIProvider(config)

        assert provider.model == 'glm-4-flash'
        assert provider.api_key == 'test-api-key'
        assert 'zhipu' in provider.base_url

    def test_initialization_requires_api_key(self):
        """Test that API key is required."""
        config = {'provider': 'zhipuai', 'model_name': 'glm-4-flash'}
        with pytest.raises(ValueError, match="API key is required"):
            ZhipuAIProvider(config)

    @pytest.mark.asyncio
    async def test_analyze_matches(self):
        """Test match analysis."""
        config = {
            'provider': 'zhipuai',
            'model_name': 'glm-4-flash',
            'api_key': 'test-api-key',
        }
        provider = ZhipuAIProvider(config)

        # Mock the API call
        mock_response = {
            'choices': [{
                'message': {
                    'content': '{"summary": "测试", "detailed_analysis": [], "confidence": 0.8}'
                }
            }],
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }

        with patch.object(provider, '_call_api', new_callable=AsyncMock, return_value=mock_response):
            result = await provider.analyze_matches("测试需求", [])

            assert result['summary'] == '测试'
            assert 'tokens_used' in result


class TestQwenProvider:
    """Test Qwen provider."""

    def test_initialization(self):
        """Test provider initialization."""
        config = {
            'provider': 'qwen',
            'model_name': 'qwen-plus',
            'api_key': 'test-api-key',
        }
        provider = QwenProvider(config)

        assert provider.model == 'qwen-plus'
        assert provider.api_key == 'test-api-key'
        assert 'dashscope' in provider.base_url

    def test_initialization_requires_api_key(self):
        """Test that API key is required."""
        config = {'provider': 'qwen', 'model_name': 'qwen-plus'}
        with pytest.raises(ValueError, match="API key is required"):
            QwenProvider(config)

    @pytest.mark.asyncio
    async def test_analyze_matches(self):
        """Test match analysis."""
        config = {
            'provider': 'qwen',
            'model_name': 'qwen-plus',
            'api_key': 'test-api-key',
        }
        provider = QwenProvider(config)

        # Mock the API call
        mock_response = {
            'choices': [{
                'message': {
                    'content': '{"summary": "测试", "detailed_analysis": [], "confidence": 0.8}'
                }
            }],
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }

        with patch.object(provider, '_call_api', new_callable=AsyncMock, return_value=mock_response):
            result = await provider.analyze_matches("测试需求", [])

            assert result['summary'] == '测试'
            assert 'tokens_used' in result


class TestLLMProviderFactory:
    """Test LLM provider factory."""

    def test_register_provider(self):
        """Test provider registration."""
        class TestProvider(BaseLLMProvider):
            async def analyze_matches(self, requirement, matches, threshold=0.75):
                return {}

            async def generate_explanation(self, requirement, feature, similarity_score):
                return ""

            async def suggest_improvements(self, requirement, unmatched_features):
                return {}

        LLMProviderFactory.register_provider('test', TestProvider)

        assert 'test' in LLMProviderFactory._providers
        assert LLMProviderFactory._providers['test'] == TestProvider

    def test_register_provider_validation(self):
        """Test that invalid provider classes are rejected."""
        class InvalidProvider:
            pass

        with pytest.raises(ValueError, match="must inherit from BaseLLMProvider"):
            LLMProviderFactory.register_provider('invalid', InvalidProvider)

    def test_create_provider_from_dict(self):
        """Test creating provider from dict config."""
        config = {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'api_key': 'test-key',
        }

        provider = LLMProviderFactory.create_provider(config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.model == 'gpt-4o-mini'

    def test_create_provider_caches_instances(self):
        """Test that provider instances are cached."""
        config = {
            'id': 'test-id',
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'api_key': 'test-key',
        }

        provider1 = LLMProviderFactory.create_provider(config, use_cache=True)
        provider2 = LLMProviderFactory.create_provider(config, use_cache=True)

        assert provider1 is provider2

    def test_create_provider_without_cache(self):
        """Test creating provider without cache."""
        config = {
            'id': 'test-id',
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'api_key': 'test-key',
        }

        provider1 = LLMProviderFactory.create_provider(config, use_cache=False)
        provider2 = LLMProviderFactory.create_provider(config, use_cache=False)

        assert provider1 is not provider2

    def test_create_unsupported_provider(self):
        """Test creating unsupported provider raises error."""
        config = {
            'provider': 'unsupported',
            'model_name': 'test',
            'api_key': 'test-key',
        }

        with pytest.raises(ValueError, match="Unsupported LLM provider type"):
            LLMProviderFactory.create_provider(config)

    def test_clear_cache(self):
        """Test cache clearing."""
        config = {
            'id': 'test-id',
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'api_key': 'test-key',
        }

        LLMProviderFactory.create_provider(config)
        assert 'test-id' in LLMProviderFactory._provider_cache

        LLMProviderFactory.clear_cache()
        assert len(LLMProviderFactory._provider_cache) == 0

    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = LLMProviderFactory.get_available_providers()

        assert isinstance(providers, list)
        assert 'openai' in providers
        assert 'zhipuai' in providers
        assert 'qwen' in providers


class TestLLMService:
    """Test LLM service."""

    def test_initialization(self):
        """Test service initialization."""
        service = LLMService(config_id='test-id')
        assert service.config_id == 'test-id'

        service_no_config = LLMService()
        assert service_no_config.config_id is None

    @pytest.mark.asyncio
    async def test_analyze_matches(self):
        """Test analyze_matches method."""
        service = LLMService()

        # Mock the provider
        mock_provider = Mock()
        mock_provider.analyze_matches = AsyncMock(return_value={
            'summary': 'Test',
            'detailed_analysis': [],
            'confidence': 0.8
        })

        with patch.object(service, '_get_provider', return_value=mock_provider):
            result = await service.analyze_matches("需求", [])

            assert result['summary'] == 'Test'
            mock_provider.analyze_matches.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection(self):
        """Test test_connection method."""
        service = LLMService()

        # Mock successful connection
        mock_provider = Mock()
        mock_provider.test_connection = AsyncMock(return_value=True)
        mock_provider.get_model_info = Mock(return_value={'model': 'test'})

        with patch.object(service, '_get_provider', return_value=mock_provider):
            result = await service.test_connection()

            assert result['status'] == 'success'
            assert result['is_connected'] is True

        # Mock failed connection
        mock_provider.get_model_info = Mock(side_effect=Exception("Error"))

        with patch.object(service, '_get_provider', return_value=mock_provider):
            result = await service.test_connection()

            assert result['status'] == 'error'
            assert result['is_connected'] is False
