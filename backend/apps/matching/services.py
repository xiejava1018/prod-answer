"""
Matching service for processing requirements and finding matches.
"""
import uuid
import time
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


class EnhancedMatchingService(MatchingService):
    """
    Enhanced matching service with LLM analysis support.

    Extends MatchingService to add LLM-powered analysis of match results.
    """

    def __init__(self, threshold: float = 0.75, llm_config_id: Optional[str] = None):
        """
        Initialize the enhanced matching service.

        Args:
            threshold: Similarity threshold for matching
            llm_config_id: LLM configuration ID to use (None for default)
        """
        super().__init__(threshold)
        self.llm_config_id = llm_config_id

    @transaction.atomic
    def process_requirement_with_llm(
        self,
        requirement_id: str,
        llm_config_id: Optional[str] = None,
        analysis_mode: str = 'full',
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Process a requirement with LLM-enhanced matching analysis.

        Implements graceful degradation: if LLM analysis fails,
        returns vector-only matching results.

        Args:
            requirement_id: UUID of the requirement to process
            llm_config_id: LLM configuration ID to use
            analysis_mode: 'full' or 'quick' analysis mode
            generate_embeddings: Whether to generate embeddings for items

        Returns:
            Dictionary with processing results including LLM analysis
        """
        import logging
        import signal
        from contextlib import contextmanager

        logger = logging.getLogger(__name__)

        # Timeout handler for LLM calls
        class TimeoutError(Exception):
            pass

        def timeout_handler(signum, frame):
            raise TimeoutError("LLM analysis timed out")

        @contextmanager
        def time_limit(seconds):
            """Context manager to limit execution time."""
            def signal_handler(signum, frame):
                raise TimeoutError("Timed out")
            signal.signal(signal.SIGALRM, signal_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)

        # First, perform standard matching (always works)
        start_time = time.time()
        try:
            result = super().process_requirement(
                requirement_id=requirement_id,
                generate_embeddings=generate_embeddings
            )
            vector_time = time.time() - start_time
            vector_success = True
        except Exception as e:
            logger.error(f"Vector matching failed: {e}", exc_info=True)
            # If vector matching fails, we cannot proceed
            raise

        # Then perform LLM analysis on top matches (with degradation)
        llm_analysis_performed = False
        llm_analysis_failed = False
        llm_analysis_timeout = False
        llm_analysis_time = 0
        llm_timeout_limit = 10  # 10 seconds timeout for LLM analysis

        if llm_config_id:
            try:
                from apps.llm.services import LLMProviderFactory
                from apps.llm.models import LLMAnalysisResult

                # Get LLM provider
                llm_provider = LLMProviderFactory.create_provider_by_config_id(
                    llm_config_id,
                    use_cache=True
                )

                # Get top matches for analysis
                top_matches = MatchRecord.objects.filter(
                    requirement_id=requirement_id
                ).select_related(
                    'requirement_item',
                    'feature__product'
                ).order_by('-similarity_score')[:10]  # Analyze top 10 matches

                # Perform LLM analysis for each match with timeout
                for match_record in top_matches:
                    try:
                        # Prepare analysis request
                        requirement_text = match_record.requirement_item.item_text
                        feature_description = match_record.feature.description
                        feature_name = match_record.feature.feature_name

                        # Call LLM for analysis with timeout
                        llm_start = time.time()

                        try:
                            with time_limit(llm_timeout_limit):
                                analysis_result = llm_provider.analyze_match(
                                    requirement_text=requirement_text,
                                    feature_name=feature_name,
                                    feature_description=feature_description,
                                    similarity_score=match_record.similarity_score
                                )
                        except TimeoutError:
                            logger.warning(f"LLM analysis timed out for match {match_record.id}")
                            llm_analysis_timeout = True
                            continue  # Skip this match and continue with next

                        llm_time = time.time() - llm_start
                        llm_analysis_time += llm_time

                        # Save or update LLM analysis result
                        llm_result, created = LLMAnalysisResult.objects.update_or_create(
                            requirement_item=match_record.requirement_item,
                            feature=match_record.feature,
                            defaults={
                                'is_valid_match': analysis_result.get('is_valid_match'),
                                'confidence_score': analysis_result.get('confidence_score', 0.5),
                                'match_reason': analysis_result.get('match_reason', ''),
                                'keywords_from_requirement': analysis_result.get('keywords_from_requirement', []),
                                'keywords_from_feature': analysis_result.get('keywords_from_feature', []),
                                'llm_provider': llm_provider.provider,
                                'llm_model': llm_provider.model_name,
                                'prompt_tokens': analysis_result.get('prompt_tokens', 0),
                                'completion_tokens': analysis_result.get('completion_tokens', 0),
                                'total_tokens': analysis_result.get('total_tokens', 0),
                                'analysis_metadata': analysis_result.get('metadata', {})
                            }
                        )

                        # Calculate final confidence (fusion of vector and LLM)
                        final_confidence = self._calculate_final_confidence(
                            vector_score=match_record.similarity_score,
                            llm_confidence=llm_result.confidence_score
                        )

                        # Update match record with LLM analysis
                        match_record.llm_analysis = llm_result
                        match_record.final_confidence = final_confidence

                        # Check if LLM corrected the match status
                        if llm_result.is_valid_match is False and match_record.match_status == 'matched':
                            match_record.is_llm_corrected = True
                            match_record.original_match_status = match_record.match_status
                            match_record.match_status = 'partial_matched'  # Downgrade
                        elif llm_result.is_valid_match is True and match_record.match_status == 'unmatched':
                            match_record.is_llm_corrected = True
                            match_record.original_match_status = match_record.match_status
                            match_record.match_status = 'partial_matched'  # Upgrade

                        match_record.save()
                        llm_analysis_performed = True

                    except Exception as e:
                        logger.warning(f"LLM analysis failed for match {match_record.id}: {e}")
                        llm_analysis_failed = True
                        # Continue with next match (graceful degradation)
                        continue

            except Exception as e:
                logger.error(f"LLM analysis failed completely: {e}", exc_info=True)
                # Vector matching already succeeded, so we can still return results
                llm_analysis_failed = True

        # Update result with LLM information
        result['llm_analysis_performed'] = llm_analysis_performed
        result['llm_analysis_failed'] = llm_analysis_failed
        result['llm_analysis_timeout'] = llm_analysis_timeout
        result['llm_analysis_time'] = round(llm_analysis_time, 2)
        result['total_processing_time'] = round(vector_time + llm_analysis_time, 2)
        result['vector_matching_time'] = round(vector_time, 2)

        # Add degradation notice
        if llm_analysis_failed or llm_analysis_timeout:
            result['degradation_notice'] = {
                'message': 'LLM analysis unavailable, showing vector-only results',
                'llm_failed': llm_analysis_failed,
                'llm_timeout': llm_analysis_timeout
            }

        return result

    def _calculate_final_confidence(
        self,
        vector_score: float,
        llm_confidence: float
    ) -> float:
        """
        Calculate final confidence score by fusing vector and LLM scores.

        Uses weighted average:
        - Vector score: 40% weight
        - LLM confidence: 60% weight

        Args:
            vector_score: Similarity score from vector matching
            llm_confidence: Confidence score from LLM analysis

        Returns:
            Final fused confidence score (0.0 to 1.0)
        """
        if llm_confidence is None:
            return vector_score

        # Weighted fusion
        final_confidence = (vector_score * 0.4) + (llm_confidence * 0.6)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, final_confidence))
