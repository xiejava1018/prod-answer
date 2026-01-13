"""
Matching algorithms for semantic similarity.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from django.conf import settings

# Conditional pgvector import
try:
    from pgvector.django import CosineDistance
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

from apps.products.models import FeatureEmbedding, Feature


class MatchingAlgorithm:
    """
    Matching algorithm class for calculating semantic similarity
    between requirements and features using vector embeddings.
    """

    # Similarity thresholds
    THRESHOLDS = {
        'matched': 0.85,           # Excellent match
        'partial_matched': 0.75,   # Good match
        'unmatched': 0.0,          # Below threshold
    }

    def __init__(self, threshold: float = 0.75):
        """
        Initialize the matching algorithm.

        Args:
            threshold: Minimum similarity score for a match (default: 0.75)
        """
        self.threshold = threshold
        self.THRESHOLDS['partial_matched'] = threshold

    def calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vector1: First embedding vector
            vector2: Second embedding vector

        Returns:
            Similarity score between 0 and 1
        """
        try:
            arr1 = np.array(vector1)
            arr2 = np.array(vector2)

            # Cosine similarity
            dot_product = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Ensure result is in [0, 1]
            return float(max(0.0, min(1.0, similarity)))

        except Exception as e:
            raise RuntimeError(f"Similarity calculation failed: {str(e)}")

    def determine_match_status(self, similarity_score: float) -> str:
        """
        Determine match status based on similarity score.

        Args:
            similarity_score: Similarity score

        Returns:
            Match status: 'matched', 'partial_matched', or 'unmatched'
        """
        if similarity_score >= self.THRESHOLDS['matched']:
            return 'matched'
        elif similarity_score >= self.THRESHOLDS['partial_matched']:
            return 'partial_matched'
        else:
            return 'unmatched'

    def find_matches_using_pgvector(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Find matching features using pgvector vector search or fallback to pure Python.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            min_score: Minimum similarity score (uses threshold if not specified)

        Returns:
            List of match results with feature info and similarity scores
        """
        if min_score is None:
            min_score = self.threshold

        try:
            if HAS_PGVECTOR:
                # Use pgvector for efficient similarity search
                embeddings = FeatureEmbedding.objects.annotate(
                    similarity=1 - CosineDistance('embedding', query_embedding)
                ).filter(
                    similarity__gte=min_score,
                    feature__is_active=True,
                    feature__product__is_active=True
                ).select_related(
                    'feature__product'
                ).order_by('-similarity')[:limit]

                # Build results
                results = []
                for idx, emb in enumerate(embeddings):
                    results.append({
                        'feature_id': str(emb.feature.id),
                        'feature_name': emb.feature.feature_name,
                        'feature_description': emb.feature.description,
                        'product_id': str(emb.feature.product.id),
                        'product_name': emb.feature.product.name,
                        'similarity': float(emb.similarity),
                        'match_status': self.determine_match_status(float(emb.similarity)),
                        'rank': idx + 1,
                        'model_name': emb.model_name,
                    })

                return results
            else:
                # Fallback: Load all embeddings and calculate similarity in Python
                embeddings = FeatureEmbedding.objects.filter(
                    feature__is_active=True,
                    feature__product__is_active=True
                ).select_related(
                    'feature__product'
                ).all()

                # Calculate similarities
                results = []
                for emb in embeddings:
                    similarity = self.calculate_similarity(query_embedding, emb.embedding)
                    if similarity >= min_score:
                        results.append({
                            'feature_id': str(emb.feature.id),
                            'feature_name': emb.feature.feature_name,
                            'feature_description': emb.feature.description,
                            'product_id': str(emb.feature.product.id),
                            'product_name': emb.feature.product.name,
                            'similarity': similarity,
                            'match_status': self.determine_match_status(similarity),
                            'rank': 0,  # Will be set after sorting
                            'model_name': emb.model_name,
                        })

                # Sort by similarity and assign ranks
                results.sort(key=lambda x: x['similarity'], reverse=True)
                results = results[:limit]
                for idx, result in enumerate(results):
                    result['rank'] = idx + 1

                return results

        except Exception as e:
            raise RuntimeError(f"Vector search failed: {str(e)}")

    def batch_match(
        self,
        requirement_embeddings: List[Tuple[str, List[float]]],
        limit: int = 5,
        product_ids: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Match multiple requirements against features.

        Args:
            requirement_embeddings: List of (requirement_id, embedding) tuples
            limit: Max matches per requirement
            product_ids: Optional list of product IDs to filter by

        Returns:
            Dictionary mapping requirement IDs to match results
        """
        results = {}

        for req_id, req_embedding in requirement_embeddings:
            try:
                matches = self.find_matches_using_pgvector(
                    req_embedding,
                    limit=limit
                )

                # Filter by products if specified
                if product_ids:
                    matches = [
                        m for m in matches
                        if m['product_id'] in product_ids
                    ]

                results[req_id] = matches

            except Exception as e:
                # Store error for this requirement
                results[req_id] = {
                    'error': str(e)
                }

        return results

    def calculate_match_summary(self, matches: List[Dict]) -> Dict[str, int]:
        """
        Calculate summary statistics for a set of matches.

        Args:
            matches: List of match results

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total': len(matches),
            'matched': 0,
            'partial_matched': 0,
            'unmatched': 0,
            'avg_similarity': 0.0,
        }

        if matches:
            similarity_scores = []

            for match in matches:
                status = match.get('match_status', 'unmatched')
                if status in summary:
                    summary[status] += 1

                similarity = match.get('similarity', 0.0)
                similarity_scores.append(similarity)

            # Calculate average similarity
            if similarity_scores:
                summary['avg_similarity'] = float(np.mean(similarity_scores))

        return summary


class MatchingConfig:
    """
    Configuration for matching algorithm parameters.
    """

    @staticmethod
    def get_thresholds() -> Dict[str, float]:
        """Get current matching thresholds."""
        return MatchingAlgorithm.THRESHOLDS.copy()

    @staticmethod
    def set_threshold(matched: float = 0.85, partial_matched: float = 0.75):
        """
        Update matching thresholds.

        Args:
            matched: Threshold for 'matched' status
            partial_matched: Threshold for 'partial_matched' status
        """
        MatchingAlgorithm.THRESHOLDS['matched'] = matched
        MatchingAlgorithm.THRESHOLDS['partial_matched'] = partial_matched
