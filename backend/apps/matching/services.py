"""
Matching service for processing requirements and finding matches.
"""
import uuid
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.core.cache import cache
from apps.matching.models import CapabilityRequirement, RequirementItem, MatchRecord
from apps.matching.algorithms import MatchingAlgorithm
from apps.embeddings.services import EmbeddingServiceFactory


class MatchingService:
    """
    Service class for processing requirements and performing matching.
    """

    def __init__(self, threshold: float = 0.75):
        """
        Initialize the matching service.

        Args:
            threshold: Similarity threshold for matching
        """
        self.threshold = threshold
        self.algorithm = MatchingAlgorithm(threshold)
        # Use EmbeddingServiceFactory directly for static method calls

    @transaction.atomic
    def process_requirement(
        self,
        requirement_id: str,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Process a requirement and perform matching.

        Args:
            requirement_id: UUID of the requirement to process
            generate_embeddings: Whether to generate embeddings for items

        Returns:
            Dictionary with processing results
        """
        # Get requirement
        requirement = CapabilityRequirement.objects.get(id=requirement_id)

        # Update status
        requirement.status = 'processing'
        requirement.save()

        try:
            # Get requirement items
            requirement_items = RequirementItem.objects.filter(
                requirement_id=requirement_id
            )

            # Delete old match records for this requirement to avoid duplicates
            MatchRecord.objects.filter(requirement_id=requirement_id).delete()
            print(f"Deleted old match records for requirement {requirement_id}")

            # Generate embeddings if needed
            if generate_embeddings:
                self._generate_embeddings_for_items(requirement_items)

            # Perform matching
            results = self._perform_matching(requirement, requirement_items)

            # Update status to completed
            requirement.status = 'completed'
            requirement.save()

            return results

        except Exception as e:
            # Update status to failed
            requirement.status = 'failed'
            requirement.save()
            raise e

    def _generate_embeddings_for_items(self, items: List[RequirementItem]):
        """
        Generate embeddings for requirement items in batches.

        Args:
            items: List of RequirementItem objects
        """
        # Process items without embeddings
        items_need_embedding = [item for item in items if not item.embedding]

        if not items_need_embedding:
            return

        # Truncate text to avoid token limits (SiliconFlow has 512 token limit)
        # Approximate: 1 token ≈ 0.75 Chinese characters, so ~300 chars is safe (~400 tokens)
        max_length = 300
        texts = []
        for item in items_need_embedding:
            text = item.item_text
            if len(text) > max_length:
                text = text[:max_length]
                print(f"Truncated item text from {len(item.item_text)} to {max_length} chars")
            texts.append(text)

        # Use batch encoding to process multiple items at once
        # SiliconFlow has a 512 token limit, so we use moderate batch size
        # Each text is already truncated to 300 chars (~400 tokens) to stay within limits
        embeddings = EmbeddingServiceFactory.encode_batch_text(texts, batch_size=10)

        # Store embeddings
        success_count = 0
        failed_count = 0
        for item, embedding in zip(items_need_embedding, embeddings):
            if embedding:  # Only save if embedding was successfully generated
                item._embedding_vector = embedding
                item.save()
                success_count += 1
            else:
                failed_count += 1
                print(f"Failed to generate embedding for item: {item.item_text[:50]}...")

        print(f"Embedding generation complete: {success_count} succeeded, {failed_count} failed")

    def _perform_matching(
        self,
        requirement: CapabilityRequirement,
        items: List[RequirementItem]
    ) -> Dict[str, Any]:
        """
        Perform matching for all requirement items.

        Args:
            requirement: Requirement object
            items: List of RequirementItem objects

        Returns:
            Dictionary with matching results
        """
        all_matches = []
        item_count = items.count()

        for item in items:
            # Get embedding (either from database or generated)
            if hasattr(item, '_embedding_vector'):
                query_embedding = item._embedding_vector
            else:
                # Generate on-the-fly with text truncation (max 300 chars for ~400 tokens)
                text = item.item_text
                if len(text) > 300:
                    text = text[:300]
                query_embedding = EmbeddingServiceFactory.encode_single_text(text)

            # Find matches
            matches = self.algorithm.find_matches_using_pgvector(
                query_embedding,
                limit=5  # Top 5 matches per requirement
            )

            # Save match records
            from apps.products.models import Feature
            for match in matches:
                match_record = MatchRecord.objects.create(
                    requirement=requirement,
                    requirement_item=item,
                    feature=Feature.objects.get(id=match['feature_id']),
                    similarity_score=match['similarity'],
                    match_status=match['match_status'],
                    threshold_used=self.threshold,
                    rank=match['rank'],
                    metadata=match
                )
                all_matches.append(match_record)

        # Calculate summary
        summary = {
            'requirement_id': str(requirement.id),
            'total_items': item_count,
            'total_matches': len(all_matches),
            'matched': len([m for m in all_matches if m.match_status == 'matched']),
            'partial_matched': len([m for m in all_matches if m.match_status == 'partial_matched']),
            'unmatched': len([m for m in all_matches if m.match_status == 'unmatched']),
        }

        return summary

    def get_match_results(self, requirement_id: str) -> Dict[str, Any]:
        """
        Get match results for a requirement.

        Args:
            requirement_id: UUID of the requirement

        Returns:
            Dictionary with match results grouped by status
        """
        matches = MatchRecord.objects.filter(
            requirement_id=requirement_id
        ).select_related(
            'requirement_item__requirement',
            'feature__product'
        ).order_by('-similarity_score')

        # Group by status
        results = {
            'matched': [],
            'partial_matched': [],
            'unmatched': [],
        }

        for match in matches:
            results[match.match_status].append({
                'id': str(match.id),
                'requirement_item_text': match.requirement_item.item_text,
                'feature_name': match.feature.feature_name,
                'feature_description': match.feature.description,
                'product_name': match.feature.product.name,
                'similarity_score': match.similarity_score,
                'rank': match.rank,
            })

        return results

    @staticmethod
    def get_statistics(requirement_id: str) -> Dict[str, Any]:
        """
        Get statistics for a requirement's matches.

        Args:
            requirement_id: UUID of the requirement

        Returns:
            Dictionary with statistics
        """
        from .models import CapabilityRequirement

        # Get requirement to count total items
        try:
            requirement = CapabilityRequirement.objects.get(id=requirement_id)
            total_items = requirement.items.count()
        except CapabilityRequirement.DoesNotExist:
            total_items = 0

        matches = MatchRecord.objects.filter(requirement_id=requirement_id)

        from django.db.models import Avg, Max, Min, Count

        stats = matches.aggregate(
            total_matches=Count('id'),
            avg_similarity=Avg('similarity_score'),
            max_similarity=Max('similarity_score'),
            min_similarity=Min('similarity_score'),
        )

        # Count by status
        status_counts = {}
        for status in ['matched', 'partial_matched', 'unmatched']:
            count = matches.filter(match_status=status).count()
            status_counts[status] = count

        stats['status_counts'] = status_counts
        stats['total_items'] = total_items
        stats['matched'] = status_counts.get('matched', 0)
        stats['partial_matched'] = status_counts.get('partial_matched', 0)
        stats['unmatched'] = status_counts.get('unmatched', 0)

        return stats
