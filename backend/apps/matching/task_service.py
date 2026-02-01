"""
Background task service for LLM analysis.

Provides async task processing for long-running LLM analysis
without blocking HTTP requests.
"""
import uuid
import threading
import time
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """
    Service for managing background tasks.

    Stores task status in Django cache for simplicity.
    For production, consider using Celery or_rq.
    """

    # Task status cache timeout (1 hour)
    TASK_CACHE_TIMEOUT = 3600

    @staticmethod
    def create_task_id() -> str:
        """Generate a unique task ID."""
        return str(uuid.uuid4())

    @staticmethod
    def set_task_status(task_id: str, status: str, progress: int = 0,
                        result: Optional[Dict] = None, error: Optional[str] = None):
        """
        Set task status in cache.

        Args:
            task_id: Task ID
            status: Status (pending, processing, completed, failed)
            progress: Progress percentage (0-100)
            result: Task result data
            error: Error message if failed
        """
        task_data = {
            'task_id': task_id,
            'status': status,
            'progress': progress,
            'result': result,
            'error': error,
            'updated_at': datetime.now().isoformat()
        }

        cache_key = f'task:{task_id}'
        cache.set(cache_key, task_data, timeout=BackgroundTaskService.TASK_CACHE_TIMEOUT)

        logger.info(f"Task {task_id} status: {status}, progress: {progress}%")

    @staticmethod
    def get_task_status(task_id: str) -> Optional[Dict]:
        """Get task status from cache."""
        cache_key = f'task:{task_id}'
        task_data = cache.get(cache_key)

        if task_data:
            # Parse cached data (it might be a string)
            if isinstance(task_data, str):
                import json
                task_data = json.loads(task_data)
            elif isinstance(task_data, bytes):
                import json
                task_data = json.loads(task_data.decode())

        return task_data

    @staticmethod
    def run_llm_analysis_task(requirement_id: str, llm_config_id: Optional[str] = None,
                               llm_analysis_mode: str = 'full', threshold: float = 0.75) -> str:
        """
        Run LLM analysis in a background thread.

        Args:
            requirement_id: Requirement ID
            llm_config_id: LLM configuration ID
            llm_analysis_mode: Analysis mode (full/quick)
            threshold: Similarity threshold

        Returns:
            Task ID for tracking
        """
        task_id = BackgroundTaskService.create_task_id()

        # Set initial status
        BackgroundTaskService.set_task_status(task_id, 'pending', 0)

        def run_analysis():
            try:
                # Add a small delay to ensure the main transaction has completed
                # This is critical for SQLite to avoid "database is locked" errors
                import time
                time.sleep(1)  # Wait 1 second for transaction to complete

                # Import here to avoid circular imports
                import asyncio
                from .services import EnhancedMatchingService

                # Update status to processing
                BackgroundTaskService.set_task_status(task_id, 'processing', 0)

                # Run async function in new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # Run LLM enhanced matching
                    service = EnhancedMatchingService(
                        threshold=threshold,
                        llm_config_id=llm_config_id
                    )

                    start_time = time.time()
                    result = service.process_requirement_with_llm(
                        requirement_id=requirement_id,
                        llm_config_id=llm_config_id,
                        analysis_mode=llm_analysis_mode,
                        generate_embeddings=True,
                        task_id=task_id  # Pass task_id for real-time progress updates
                    )
                    processing_time = time.time() - start_time

                    # Progress is already updated by process_requirement_with_llm during processing
                    # No need to set 50% here anymore

                    # Add task ID to result
                    result['task_id'] = task_id
                    result['processing_mode'] = 'async'

                    # Mark as completed
                    BackgroundTaskService.set_task_status(
                        task_id,
                        'completed',
                        100,
                        result=result
                    )

                    logger.info(f"Background LLM analysis task {task_id} completed in {processing_time:.2f}s")

                finally:
                    # Always close the loop
                    loop.close()

            except Exception as e:
                logger.error(f"Background LLM analysis task {task_id} failed: {e}", exc_info=True)
                BackgroundTaskService.set_task_status(
                    task_id,
                    'failed',
                    0,
                    error=str(e)
                )

        # Start background thread after transaction commits
        # This is critical for SQLite to avoid "database is locked" errors
        from django.db.transaction import on_commit

        def start_thread():
            thread = threading.Thread(target=run_analysis, daemon=True)
            thread.start()
            logger.info(f"Started background LLM analysis task {task_id}")

        # Use on_commit to ensure the thread starts AFTER the main transaction completes
        on_commit(start_thread)

        logger.info(f"Scheduled background LLM analysis task {task_id} to start after transaction commit")

        return task_id


# Singleton instance
background_task_service = BackgroundTaskService()
