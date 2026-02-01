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

        # Calculate summary - count by requirement items, not match records
        # Get unique requirement item IDs with matches
        items_with_matched = set()
        items_with_partial = set()
        items_with_unmatched = set()

        for match in all_matches:
            item_id = match.requirement_item_id
            if match.match_status == 'matched':
                items_with_matched.add(item_id)
            elif match.match_status == 'partial_matched':
                items_with_partial.add(item_id)
            elif match.match_status == 'unmatched':
                items_with_unmatched.add(item_id)

        # Items with only partial matches (excluding those with matched)
        items_only_partial = items_with_partial - items_with_matched - items_with_unmatched
        # Items with only unmatched records (excluding those with better matches)
        items_only_unmatched = items_with_unmatched - items_with_matched - items_with_partial

        # Items with any match (for calculating truly unmatched items)
        items_with_any_match = items_with_matched | items_with_partial | items_with_unmatched
        truly_unmatched = item_count - len(items_with_any_match)

        summary = {
            'requirement_id': str(requirement.id),
            'total_items': item_count,
            'total_matches': len(all_matches),
            'matched': len(items_with_matched),
            'partial_matched': len(items_only_partial),
            'unmatched': truly_unmatched,  # Items with no matches at all
        }

        return summary

    def get_match_results(self, requirement_id: str) -> Dict[str, Any]:
        """
        Get match results for a requirement, including LLM analysis if available.

        Args:
            requirement_id: UUID of the requirement

        Returns:
            Dictionary with match results grouped by status, including LLM data
            Includes requirement items with no matches in 'unmatched' list
        """
        from .models import CapabilityRequirement

        matches = MatchRecord.objects.filter(
            requirement_id=requirement_id
        ).select_related(
            'requirement_item__requirement',
            'feature__product',
            'llm_analysis'
        ).order_by('-similarity_score')

        # Group by status
        results = {
            'matched': [],
            'partial_matched': [],
            'unmatched': [],
        }

        # Track requirement items that have matches
        items_with_matches = set()

        for match in matches:
            match_data = {
                'id': str(match.id),
                'requirement_item_id': str(match.requirement_item.id),
                'requirement_item_text': match.requirement_item.item_text,
                'feature_id': str(match.feature.id),
                'feature_name': match.feature.feature_name,
                'feature_description': match.feature.description,
                'product_name': match.feature.product.name,
                'similarity_score': match.similarity_score,
                'rank': match.rank,
                'match_status': match.match_status,
            }

            # Add LLM enhancement data if available
            if match.llm_analysis:
                match_data['llm_analysis'] = {
                    'is_valid_match': match.llm_analysis.is_valid_match,
                    'confidence_score': match.llm_analysis.confidence_score,
                    'match_reason': match.llm_analysis.match_reason,
                    'keywords_from_requirement': match.llm_analysis.keywords_from_requirement,
                    'keywords_from_feature': match.llm_analysis.keywords_from_feature,
                }

                # Add fusion data if available
                if match.final_confidence is not None:
                    match_data['final_confidence'] = match.final_confidence

                if match.is_llm_corrected:
                    match_data['is_llm_corrected'] = match.is_llm_corrected
                    match_data['original_match_status'] = match.original_match_status

            results[match.match_status].append(match_data)
            items_with_matches.add(match.requirement_item_id)

        # Add requirement items with no matches to 'unmatched' list
        try:
            requirement = CapabilityRequirement.objects.get(id=requirement_id)
            for item in requirement.items.all():
                if item.id not in items_with_matches:
                    # This item has no matches at all
                    results['unmatched'].append({
                        'id': None,  # No match record
                        'requirement_item_id': str(item.id),
                        'requirement_item_text': item.item_text,
                        'feature_id': None,
                        'feature_name': None,
                        'feature_description': None,
                        'product_name': None,
                        'similarity_score': 0.0,
                        'rank': None,
                        'match_status': 'unmatched',
                        'no_match': True,  # Flag to indicate this item has no matches
                    })
        except CapabilityRequirement.DoesNotExist:
            pass

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

        # Count by requirement items, not match records
        # Get requirement item IDs that have matches
        items_with_matches = matches.values_list('requirement_item_id').distinct()

        # Count items with 'matched' status (highest priority - if item has any matched match)
        items_with_matched = MatchRecord.objects.filter(
            requirement_id=requirement_id,
            match_status='matched'
        ).values_list('requirement_item_id').distinct().count()

        # Count items with only 'partial_matched' status (exclude items that have 'matched')
        items_with_partial = MatchRecord.objects.filter(
            requirement_id=requirement_id,
            match_status='partial_matched'
        ).exclude(
            requirement_item_id__in=MatchRecord.objects.filter(
                requirement_id=requirement_id,
                match_status='matched'
            ).values_list('requirement_item_id')
        ).values_list('requirement_item_id').distinct().count()

        # Count items with only 'unmatched' status (failed matches)
        items_with_unmatched = MatchRecord.objects.filter(
            requirement_id=requirement_id,
            match_status='unmatched'
        ).exclude(
            requirement_item_id__in=MatchRecord.objects.filter(
                requirement_id=requirement_id,
                match_status__in=['matched', 'partial_matched']
            ).values_list('requirement_item_id')
        ).values_list('requirement_item_id').distinct().count()

        # Calculate truly unmatched items (no matches at all)
        items_with_any_match = items_with_matches.count()
        truly_unmatched = total_items - items_with_any_match

        status_counts = {
            'matched': items_with_matched,
            'partial_matched': items_with_partial,
            'unmatched': truly_unmatched,  # Items with no matches
            'unmatched_records': items_with_unmatched,  # Items with failed matches
        }

        stats['status_counts'] = status_counts
        stats['total_items'] = total_items
        stats['matched'] = items_with_matched
        stats['partial_matched'] = items_with_partial
        stats['unmatched'] = truly_unmatched

        return stats

    def export_results(self, requirement_id: str, format: str = 'excel', include_unmatched: bool = False) -> bytes:
        """
        Export match results to Excel or PDF format.

        Args:
            requirement_id: UUID of the requirement
            format: 'excel' or 'pdf'
            include_unmatched: Whether to include unmatched items

        Returns:
            Bytes of the exported file
        """
        import pandas as pd
        from io import BytesIO

        # Get match results
        matches = MatchRecord.objects.filter(
            requirement_id=requirement_id
        ).select_related(
            'requirement_item__requirement',
            'feature__product'
        ).order_by('-similarity_score')

        # Create DataFrame
        data = []
        for match in matches:
            data.append({
                '需求项': match.requirement_item.item_text,
                '功能名称': match.feature.feature_name,
                '功能描述': match.feature.description,
                '产品名称': match.feature.product.name,
                '相似度': match.similarity_score,
                '匹配状态': match.match_status,
                '排名': match.rank,
            })

        # Add unmatched items if requested
        if include_unmatched:
            from .models import RequirementItem
            matched_item_ids = [match.requirement_item.id for match in matches]
            unmatched_items = RequirementItem.objects.filter(
                requirement_id=requirement_id
            ).exclude(id__in=matched_item_ids)

            for item in unmatched_items:
                data.append({
                    '需求项': item.item_text,
                    '功能名称': '',
                    '功能描述': '',
                    '产品名称': '',
                    '相似度': 0,
                    '匹配状态': 'unmatched',
                    '排名': '',
                })

        df = pd.DataFrame(data)

        # Export to Excel or PDF
        output = BytesIO()

        if format == 'excel':
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='匹配结果', index=False)
            output.seek(0)
            return output.getvalue()
        elif format == 'pdf':
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib import colors

            doc = SimpleDocTemplate(output, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Add title
            title = Paragraph("产品能力匹配结果", styles['Title'])
            elements.append(title)

            # Add table
            table_data = [df.columns.tolist()] + df.values.tolist()
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

            doc.build(elements)
            output.seek(0)
            return output.getvalue()
        else:
            raise ValueError("Unsupported format: {}".format(format))


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
        generate_embeddings: bool = True,
        task_id: Optional[str] = None
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
        import threading
        from contextlib import contextmanager

        logger = logging.getLogger(__name__)

        # Timeout handler for LLM calls
        class TimeoutError(Exception):
            pass

        @contextmanager
        def time_limit(seconds):
            """Context manager to limit execution time (thread-safe)."""
            timeout_raised = [False]

            def timeout_handler():
                timeout_raised[0] = True
                raise TimeoutError("LLM analysis timed out")

            timer = threading.Timer(seconds, timeout_handler)
            timer.start()
            try:
                yield
            except TimeoutError:
                raise
            finally:
                timer.cancel()
                # Wait a bit for timer thread to finish
                if timer.is_alive():
                    timer.join(timeout=0.1)

        # First, perform standard matching (always works)
        start_time = time.time()
        try:
            result = super().process_requirement(
                requirement_id=requirement_id,
                generate_embeddings=generate_embeddings
            )
            vector_time = time.time() - start_time
            vector_success = True

            # Update task progress after vector matching (30%)
            if task_id:
                from .task_service import BackgroundTaskService
                BackgroundTaskService.set_task_status(task_id, 'processing', 30)

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

        # Import asyncio for running async functions
        import asyncio

        # Get LLM provider (use default if not specified)
        from apps.llm.services import LLMProviderFactory
        from apps.llm.models import LLMAnalysisResult

        try:
            # Get LLM provider (use default config if llm_config_id is not provided)
            if llm_config_id:
                llm_provider = LLMProviderFactory.get_provider_by_id(llm_config_id)
            else:
                logger.info("No llm_config_id provided, using default LLM configuration")
                import asyncio
                llm_provider = asyncio.run(LLMProviderFactory.get_default_provider())

            # Get matches for analysis (only matched and partial_matched, skip unmatched to save cost)
            top_matches = MatchRecord.objects.filter(
                requirement_id=requirement_id,
                match_status__in=['matched', 'partial_matched']
            ).select_related(
                'requirement_item',
                'feature__product'
            ).order_by('-similarity_score')  # Analyze all valid matches

            if not top_matches:
                logger.info(f"No valid matches found for requirement {requirement_id}, skipping LLM analysis")
            else:
                logger.info(f"Performing BATCH LLM analysis on {len(top_matches)} valid matches (matched and partial_matched only)")

            # BATCH ANALYSIS: Process in chunks of 20 matches each
            BATCH_SIZE = 20  # Process 20 matches per batch to avoid token limits

            if top_matches:
                # Split into batches
                match_batches = []
                for i in range(0, len(top_matches), BATCH_SIZE):
                    batch = top_matches[i:i + BATCH_SIZE]
                    match_batches.append(batch)

                logger.info(f"Split {len(top_matches)} matches into {len(match_batches)} batches of max {BATCH_SIZE} each")

                total_llm_time = 0
                total_batches_processed = 0
                total_batches_failed = 0

                for batch_idx, batch_matches in enumerate(match_batches):
                    logger.info(f"Processing batch {batch_idx + 1}/{len(match_batches)} with {len(batch_matches)} matches")

                    # Prepare batch data
                    matches_data = []
                    match_records_list = []

                    for match_record in batch_matches:
                        matches_data.append({
                            'requirement_text': match_record.requirement_item.item_text,
                            'feature_name': match_record.feature.feature_name,
                            'feature_description': match_record.feature.description,
                            'similarity_score': match_record.similarity_score
                        })
                        match_records_list.append(match_record)

                    # Call LLM for batch analysis with timeout
                    llm_start = time.time()

                    try:
                        with time_limit(llm_timeout_limit * 3):  # 3x timeout per batch (30 seconds)
                            # Run async batch analysis function in sync context
                            batch_result = asyncio.run(llm_provider.analyze_matches_batch(matches_data))

                        llm_time = time.time() - llm_start
                        total_llm_time += llm_time
                        total_batches_processed += 1

                        # Update task progress after each batch (30% to 90%)
                        if task_id:
                            from .task_service import BackgroundTaskService
                            # Calculate progress: 30% (vector done) + (batch_progress * 60%)
                            batch_progress = (batch_idx + 1) / len(match_batches)
                            current_progress = int(30 + (batch_progress * 60))
                            BackgroundTaskService.set_task_status(
                                task_id,
                                'processing',
                                current_progress
                            )
                            logger.info(f"Updated task progress to {current_progress}%")

                        logger.info(f"Batch {batch_idx + 1} LLM analysis completed in {llm_time:.2f}s for {len(matches_data)} matches")
                        logger.info(f"Tokens used: {batch_result.get('tokens_used', {})}")
                        logger.info(f"Estimated cost: ${batch_result.get('estimated_cost', {}).get('total_cost', 0):.6f} USD")

                        # Process batch results and save to database
                        indexed_results = batch_result.get('indexed_results', {})

                        for idx, match_record in enumerate(match_records_list):
                            if idx not in indexed_results:
                                logger.warning(f"No LLM result for match {match_record.id} at index {idx} in batch {batch_idx + 1}")
                                continue

                            analysis_result = indexed_results[idx]

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
                                    'prompt_tokens': batch_result.get('tokens_used', {}).get('prompt_tokens', 0) // len(matches_data),
                                    'completion_tokens': batch_result.get('tokens_used', {}).get('completion_tokens', 0) // len(matches_data),
                                    'total_tokens': batch_result.get('tokens_used', {}).get('total_tokens', 0) // len(matches_data),
                                    'analysis_metadata': {
                                        'batch_index': idx,
                                        'batch_number': batch_idx + 1,
                                        'total_batches': len(match_batches),
                                        'batch_total': len(matches_data),
                                        'batch_tokens': batch_result.get('tokens_used', {})
                                    }
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

                    except TimeoutError:
                        logger.warning(f"Batch {batch_idx + 1} LLM analysis timed out after {llm_timeout_limit * 3}s")
                        llm_analysis_timeout = True
                        total_batches_failed += 1
                        continue  # Skip to next batch

                    except Exception as e:
                        logger.error(f"Batch {batch_idx + 1} LLM analysis failed: {e}", exc_info=True)
                        llm_analysis_failed = True
                        total_batches_failed += 1
                        # Try individual analysis for this batch as fallback
                        logger.info(f"Attempting individual analysis for batch {batch_idx + 1}")

                        for match_record in batch_matches[:5]:  # Limit to 5 per failed batch
                            try:
                                requirement_text = match_record.requirement_item.item_text
                                feature_description = match_record.feature.description
                                feature_name = match_record.feature.feature_name

                                llm_start = time.time()
                                analysis_result = asyncio.run(llm_provider.analyze_match(
                                    requirement_text=requirement_text,
                                    feature_name=feature_name,
                                    feature_description=feature_description,
                                    similarity_score=match_record.similarity_score
                                ))
                                llm_time = time.time() - llm_start
                                total_llm_time += llm_time

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
                                        'analysis_metadata': {
                                            'fallback_analysis': True,
                                            'failed_batch': batch_idx + 1
                                        }
                                    }
                                )

                                final_confidence = self._calculate_final_confidence(
                                    vector_score=match_record.similarity_score,
                                    llm_confidence=llm_result.confidence_score
                                )

                                match_record.llm_analysis = llm_result
                                match_record.final_confidence = final_confidence

                                if llm_result.is_valid_match is False and match_record.match_status == 'matched':
                                    match_record.is_llm_corrected = True
                                    match_record.original_match_status = match_record.match_status
                                    match_record.match_status = 'partial_matched'
                                elif llm_result.is_valid_match is True and match_record.match_status == 'unmatched':
                                    match_record.is_llm_corrected = True
                                    match_record.original_match_status = match_record.match_status
                                    match_record.match_status = 'partial_matched'

                                match_record.save()
                                llm_analysis_performed = True

                            except Exception as e:
                                logger.warning(f"Fallback LLM analysis failed for match {match_record.id}: {e}")
                                continue

                # After processing all batches
                llm_analysis_time = total_llm_time
                logger.info(f"Batch LLM analysis summary: {total_batches_processed}/{len(match_batches)} batches succeeded, {total_batches_failed} failed")
                logger.info(f"Total LLM analysis time: {total_llm_time:.2f}s")

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
