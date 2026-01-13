"""
OpenAI embedding provider implementation.
"""
from typing import List, Dict, Any
from openai import OpenAI
from .base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding model provider.
    Supports models like text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Initialize OpenAI client
        api_key = self.api_key or config.get('api_key_encrypted')
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=api_key)

        # Get model from params or use default
        self.model = self.model_params.get('model', 'text-embedding-3-small')

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API.

        Args:
            texts: List of text strings to encode

        Returns:
            List of embedding vectors
        """
        try:
            # Batch encode (OpenAI supports multiple texts per request)
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            raise RuntimeError(f"OpenAI encoding failed: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test connection to OpenAI API.

        Returns:
            bool: True if successful
        """
        try:
            # Try to encode a test text
            result = self.encode(["test"])
            # Verify dimension matches
            return len(result) > 0 and self.validate_embedding(result[0])
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get OpenAI model information.

        Returns:
            Dictionary with model details
        """
        info = super().get_model_info()
        info.update({
            'api_model': self.model,
            'api_endpoint': 'https://api.openai.com/v1',
        })
        return info
