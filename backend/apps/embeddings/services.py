"""
Embedding service factory and management.
"""
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from .models import EmbeddingModelConfig
from .providers.openai_provider import OpenAIEmbeddingProvider
from .providers.huggingface_provider import SentenceTransformersProvider
from .providers.openai_compatible_provider import OpenAICompatibleProvider


class EmbeddingServiceFactory:
    """
    Factory class for creating and managing embedding service providers.
    Supports multiple embedding model types.
    """

    # Registry of available providers
    _providers = {
        'openai': OpenAIEmbeddingProvider,
        'sentence-transformers': SentenceTransformersProvider,
        'openai-compatible': OpenAICompatibleProvider,  # Generic OpenAI-compatible
        'siliconflow': OpenAICompatibleProvider,  # SiliconFlow (OpenAI-compatible)
        'zhipuai': OpenAICompatibleProvider,  # ZhipuAI (OpenAI-compatible)
        'qwen': OpenAICompatibleProvider,  # Qwen (OpenAI-compatible)
    }

    # Cache for provider instances
    _provider_cache = {}

    @classmethod
    def register_provider(cls, provider_type: str, provider_class):
        """
        Register a new embedding provider type.

        Args:
            provider_type: Type identifier (e.g., 'openai', 'huggingface')
            provider_class: Provider class (must inherit from BaseEmbeddingProvider)
        """
        cls._providers[provider_type] = provider_class

    @classmethod
    def create_provider(cls, config: EmbeddingModelConfig, use_cache: bool = True):
        """
        Create a provider instance from configuration.

        Args:
            config: EmbeddingModelConfig instance
            use_cache: Whether to cache and reuse provider instances

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is not supported
        """
        # Check cache first
        if use_cache and config.id in cls._provider_cache:
            return cls._provider_cache[config.id]

        # Get provider class
        provider_type = config.provider
        provider_class = cls._providers.get(provider_type)

        if not provider_class:
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported types: {list(cls._providers.keys())}"
            )

        # Prepare configuration
        config_dict = {
            'model_name': config.model_name,
            'dimension': config.dimension,
            'api_key': config.get_api_key() if config.api_key_encrypted else None,
            'model_params': config.model_params,
            'provider': config.provider,
        }

        # Add extra fields for OpenAI-compatible providers
        if hasattr(config, 'base_url') and config.base_url:
            config_dict['base_url'] = config.base_url
        if hasattr(config, 'provider_name') and config.provider_name:
            config_dict['provider_name'] = config.provider_name

        # Create provider instance
        provider = provider_class(config_dict)

        # Cache instance
        if use_cache:
            cls._provider_cache[config.id] = provider

        return provider

    @classmethod
    def get_default_provider(cls):
        """
        Get the default embedding service provider.

        Returns:
            Default provider instance

        Raises:
            ValueError: If no default configuration is found
        """
        # Try to get default config
        config = EmbeddingModelConfig.objects.filter(
            is_default=True,
            is_active=True
        ).first()

        if not config:
            # If no default, use first active config
            config = EmbeddingModelConfig.objects.filter(
                is_active=True
            ).first()

        if not config:
            raise ValueError(
                "No active embedding model configuration found. "
                "Please create and activate a model configuration."
            )

        return cls.create_provider(config)

    @classmethod
    def get_provider_by_id(cls, config_id: str):
        """
        Get a provider by configuration ID.

        Args:
            config_id: UUID of the configuration

        Returns:
            Provider instance

        Raises:
            EmbeddingModelConfig.DoesNotExist: If config not found
        """
        config = EmbeddingModelConfig.objects.get(id=config_id)
        return cls.create_provider(config)

    @classmethod
    def get_all_active_configs(cls) -> List[EmbeddingModelConfig]:
        """
        Get all active model configurations.

        Returns:
            List of active EmbeddingModelConfig instances
        """
        return EmbeddingModelConfig.objects.filter(is_active=True)

    @classmethod
    def clear_cache(cls):
        """
        Clear the provider cache.
        Useful when configurations are updated.
        """
        cls._provider_cache.clear()

    @classmethod
    def encode_texts(cls, texts: List[str], config_id: Optional[str] = None) -> List[List[float]]:
        """
        Encode texts using specified or default provider.

        Args:
            texts: List of texts to encode
            config_id: Optional configuration ID (uses default if not provided)

        Returns:
            List of embedding vectors
        """
        if config_id:
            provider = cls.get_provider_by_id(config_id)
        else:
            provider = cls.get_default_provider()

        return provider.encode(texts)

    @classmethod
    def encode_single_text(cls, text: str, config_id: Optional[str] = None) -> List[float]:
        """
        Encode a single text using specified or default provider.

        Args:
            text: Text to encode
            config_id: Optional configuration ID (uses default if not provided)

        Returns:
            Embedding vector
        """
        embeddings = cls.encode_texts([text], config_id)
        return embeddings[0] if embeddings else []

    @classmethod
    def encode_batch_text(cls, texts: List[str], config_id: Optional[str] = None, batch_size: int = 50) -> List[List[float]]:
        """
        Encode texts in batches to avoid API limits.

        Args:
            texts: List of texts to encode
            config_id: Optional configuration ID (uses default if not provided)
            batch_size: Maximum number of texts to process in each batch

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                embeddings = cls.encode_texts(batch, config_id)
                all_embeddings.extend(embeddings)
            except Exception as e:
                # If batch fails, try individual items with smaller batches
                for text in batch:
                    try:
                        embedding = cls.encode_single_text(text, config_id)
                        all_embeddings.append(embedding)
                    except Exception as item_error:
                        print(f"Error encoding text: {str(item_error)}")
                        # Add empty embedding to maintain order
                        all_embeddings.append([])

        return all_embeddings


class EmbeddingService:
    """
    High-level service for managing embeddings in the system.
    """

    def __init__(self, config_id: Optional[str] = None):
        """
        Initialize the service.

        Args:
            config_id: Optional configuration ID (uses default if not provided)
        """
        self.factory = EmbeddingServiceFactory
        self.config_id = config_id

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.factory.encode_single_text(text, self.config_id)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return self.factory.encode_texts(texts, self.config_id)

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the embedding service.

        Returns:
            Dictionary with test results
        """
        try:
            provider = self.factory.get_default_provider()
            is_connected = provider.test_connection()
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
