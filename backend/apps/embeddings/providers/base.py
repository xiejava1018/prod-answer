"""
Base class for embedding providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseEmbeddingProvider(ABC):
    """
    Abstract base class for embedding model providers.
    All embedding providers should inherit from this class.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the embedding provider.

        Args:
            config: Dictionary containing configuration
                - model_name: str, Name of the model
                - dimension: int, Dimension of embeddings
                - api_key: str, API key (if applicable)
                - model_params: dict, Additional model parameters
        """
        self.config = config
        self.model_name = config.get('model_name')
        self.dimension = config.get('dimension')
        self.api_key = config.get('api_key')
        self.model_params = config.get('model_params', {})

    @abstractmethod
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to encode

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the embedding service.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    def encode_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to encode

        Returns:
            Embedding vector (list of floats)
        """
        result = self.encode([text])
        return result[0] if result else []

    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate that an embedding has the correct dimension.

        Args:
            embedding: Embedding vector to validate

        Returns:
            bool: True if dimension matches expected
        """
        return len(embedding) == self.dimension

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Dictionary containing model information
        """
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'provider': self.__class__.__name__,
        }
