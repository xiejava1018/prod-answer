"""
LLM service factory and management.
"""
from typing import Dict, List, Any, Optional
from .providers.base import BaseLLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.zhipuai_provider import ZhipuAIProvider
from .providers.qwen_provider import QwenProvider


class LLMProviderFactory:
    """
    Factory class for creating and managing LLM providers.
    Supports multiple LLM providers (OpenAI, ZhipuAI, Qwen).
    """

    # Registry of available providers
    _providers = {
        'openai': OpenAIProvider,
        'zhipuai': ZhipuAIProvider,
        'qwen': QwenProvider,
    }

    # Cache for provider instances
    _provider_cache = {}

    @classmethod
    def register_provider(cls, provider_type: str, provider_class):
        """
        Register a new LLM provider type.

        Args:
            provider_type: Type identifier (e.g., 'openai', 'zhipuai')
            provider_class: Provider class (must inherit from BaseLLMProvider)

        Raises:
            ValueError: If provider_class doesn't inherit from BaseLLMProvider
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(
                f"Provider class must inherit from BaseLLMProvider. "
                f"Got: {provider_class.__name__}"
            )

        cls._providers[provider_type] = provider_class

    @classmethod
    def create_provider(cls, config: Any, use_cache: bool = True) -> BaseLLMProvider:
        """
        Create a provider instance from configuration.

        Args:
            config: Configuration object (LLMModelConfig or dict)
                If dict, must contain: provider, model_name, api_key
            use_cache: Whether to cache and reuse provider instances

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is not supported or config is invalid
        """
        # Handle both dict and config object
        if isinstance(config, dict):
            config_id = config.get('id', hash(str(config)))
            provider_type = config.get('provider')
            config_dict = config
        else:
            # Assume it's a model config object
            config_id = config.id
            provider_type = config.provider
            config_dict = {
                'provider': config.provider,
                'model_name': config.model_name,
                'api_key': config.get_api_key() if hasattr(config, 'get_api_key') else config.api_key_encrypted,
                'base_url': getattr(config, 'base_url', None),
                'max_tokens': getattr(config, 'max_tokens', 2000),
                'temperature': getattr(config, 'temperature', 0.7),
                'model_params': getattr(config, 'model_params', {}),
            }

        # Check cache first
        if use_cache and config_id in cls._provider_cache:
            return cls._provider_cache[config_id]

        # Get provider class
        provider_class = cls._providers.get(provider_type)

        if not provider_class:
            supported_types = list(cls._providers.keys())
            raise ValueError(
                f"Unsupported LLM provider type: {provider_type}. "
                f"Supported types: {supported_types}"
            )

        # Validate required fields
        required_fields = ['provider', 'model_name']
        for field in required_fields:
            if field not in config_dict:
                raise ValueError(f"Missing required config field: {field}")

        # Create provider instance
        try:
            provider = provider_class(config_dict)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create {provider_type} provider: {str(e)}"
            )

        # Cache instance
        if use_cache:
            cls._provider_cache[config_id] = provider

        return provider

    @classmethod
    def get_default_provider(cls) -> BaseLLMProvider:
        """
        Get the default LLM provider.

        Returns:
            Default provider instance

        Raises:
            ValueError: If no default configuration is found

        Note:
            This method requires LLMModelConfig model to be imported.
            Call this method only after the models are defined.
        """
        try:
            from .models import LLMModelConfig
        except ImportError:
            raise ValueError(
                "LLMModelConfig model not found. "
                "Make sure the LLM app is properly configured."
            )

        # Try to get default config
        config = LLMModelConfig.objects.filter(
            is_default=True,
            is_active=True
        ).first()

        if not config:
            # If no default, use first active config
            config = LLMModelConfig.objects.filter(
                is_active=True
            ).first()

        if not config:
            raise ValueError(
                "No active LLM model configuration found. "
                "Please create and activate a model configuration."
            )

        return cls.create_provider(config)

    @classmethod
    def get_provider_by_id(cls, config_id: str) -> BaseLLMProvider:
        """
        Get a provider by configuration ID.

        Args:
            config_id: UUID of the configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If config not found
        """
        try:
            from .models import LLMModelConfig
        except ImportError:
            raise ValueError(
                "LLMModelConfig model not found. "
                "Make sure the LLM app is properly configured."
            )

        try:
            config = LLMModelConfig.objects.get(id=config_id)
            return cls.create_provider(config)
        except LLMModelConfig.DoesNotExist:
            raise ValueError(
                f"LLM configuration not found: {config_id}"
            )

    @classmethod
    def get_all_active_configs(cls) -> List[Any]:
        """
        Get all active model configurations.

        Returns:
            List of active LLMModelConfig instances
        """
        try:
            from .models import LLMModelConfig
        except ImportError:
            return []

        return LLMModelConfig.objects.filter(is_active=True)

    @classmethod
    def clear_cache(cls):
        """
        Clear the provider cache.
        Useful when configurations are updated.
        """
        cls._provider_cache.clear()

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        Get list of available provider types.

        Returns:
            List of provider type names
        """
        return list(cls._providers.keys())


class LLMService:
    """
    High-level service for LLM operations.

    This service provides a simplified interface for common LLM tasks
    in the matching system.
    """

    def __init__(self, config_id: Optional[str] = None):
        """
        Initialize the service.

        Args:
            config_id: Optional configuration ID (uses default if not provided)
        """
        self.factory = LLMProviderFactory
        self.config_id = config_id

    async def analyze_matches(
        self,
        requirement: str,
        matches: List[Dict[str, Any]],
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Analyze matching results using LLM.

        Args:
            requirement: User requirement text
            matches: List of match results
            threshold: Similarity threshold used

        Returns:
            Analysis dictionary
        """
        provider = self._get_provider()
        return await provider.analyze_matches(requirement, matches, threshold)

    async def generate_explanation(
        self,
        requirement: str,
        feature: Dict[str, Any],
        similarity_score: float
    ) -> str:
        """
        Generate explanation for a match.

        Args:
            requirement: User requirement text
            feature: Feature dictionary
            similarity_score: Similarity score

        Returns:
            Natural language explanation
        """
        provider = self._get_provider()
        return await provider.generate_explanation(requirement, feature, similarity_score)

    async def suggest_improvements(
        self,
        requirement: str,
        unmatched_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest improvements for matching.

        Args:
            requirement: User requirement text
            unmatched_features: Features that didn't match

        Returns:
            Dictionary with suggestions
        """
        provider = self._get_provider()
        return await provider.suggest_improvements(requirement, unmatched_features)

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the LLM provider connection.

        Returns:
            Dictionary with test results
        """
        try:
            provider = self._get_provider()
            is_connected = await provider.test_connection()
            model_info = provider.get_model_info()

            return {
                'status': 'success' if is_connected else 'failed',
                'is_connected': is_connected,
                'model_info': model_info,
            }
        except Exception as e:
            return {
                'status': 'error',
                'is_connected': False,
                'error': str(e),
            }

    def _get_provider(self) -> BaseLLMProvider:
        """Get provider instance."""
        if self.config_id:
            return self.factory.get_provider_by_id(self.config_id)
        else:
            return self.factory.get_default_provider()

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        provider = self._get_provider()
        return provider.get_model_info()
