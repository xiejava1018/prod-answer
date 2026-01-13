"""
OpenAI-compatible API embedding provider implementation.
Supports SiliconFlow, ZhipuAI, and other OpenAI-compatible APIs.
"""
from typing import List, Dict, Any
from openai import OpenAI
from .base import BaseEmbeddingProvider


class OpenAICompatibleProvider(BaseEmbeddingProvider):
    """
    OpenAI-compatible API embedding model provider.
    Supports SiliconFlow, ZhipuAI, Qwen, and other OpenAI-compatible APIs.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Initialize OpenAI client with custom base URL
        api_key = self.api_key or config.get('api_key_encrypted')
        if not api_key:
            raise ValueError("API key is required")

        # Get custom base URL from config
        base_url = config.get('base_url', 'https://api.openai.com/v1')

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # Get model from params or use default
        self.model = self.model_params.get('model', self.model_name)

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI-compatible API.

        Args:
            texts: List of text strings to encode

        Returns:
            List of embedding vectors
        """
        try:
            # Batch encode (OpenAI-compatible APIs support multiple texts per request)
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            raise RuntimeError(f"{self.config.get('provider_name', 'OpenAI-compatible')} encoding failed: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test connection to OpenAI-compatible API.

        Returns:
            bool: True if successful
        """
        try:
            # Try to encode a test text
            result = self.encode(["测试连接"])
            # Verify dimension matches
            return len(result) > 0 and self.validate_embedding(result[0])
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get OpenAI-compatible model information.

        Returns:
            Dictionary with model details
        """
        info = super().get_model_info()
        info.update({
            'api_model': self.model,
            'base_url': self.config.get('base_url'),
            'provider_name': self.config.get('provider_name', 'OpenAI-compatible'),
        })
        return info
