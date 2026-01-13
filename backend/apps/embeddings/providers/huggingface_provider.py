"""
Sentence-Transformers embedding provider implementation.
"""
from typing import List, Dict, Any
import numpy as np
from .base import BaseEmbeddingProvider


class SentenceTransformersProvider(BaseEmbeddingProvider):
    """
    Sentence-Transformers embedding model provider.
    Supports local and HuggingFace models.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Lazy loading of model (load it when first used)
        self._model = None
        self.model_path = self.model_params.get('model_path', 'all-MiniLM-L6-v2')
        self.device = self.model_params.get('device', 'cpu')

    def _load_model(self):
        """
        Lazy load the sentence-transformers model.
        """
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_path)
                if self.device:
                    self._model.to(self.device)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Install it with: pip install sentence-transformers"
                )

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using sentence-transformers.

        Args:
            texts: List of text strings to encode

        Returns:
            List of embedding vectors
        """
        try:
            self._load_model()

            # Encode texts
            embeddings = self._model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            # Convert to list of lists
            return embeddings.tolist()

        except Exception as e:
            raise RuntimeError(f"Sentence-Transformers encoding failed: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test if model can be loaded and used.

        Returns:
            bool: True if successful
        """
        try:
            result = self.encode(["test"])
            return len(result) > 0 and self.validate_embedding(result[0])
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.

        Returns:
            Dictionary with model details
        """
        info = super().get_model_info()
        info.update({
            'model_path': self.model_path,
            'device': self.device,
        })
        return info
