"""
Celery tasks for LLM analysis.

This module defines asynchronous tasks for:
- Single requirement analysis
- Batch analysis of multiple requirements
- Progress tracking
- Error handling and retry

These tasks integrate with the LLMAnalysisService to provide
asyncious, scalable LLM-based analysis.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from celery import shared_task, group, chain, chord
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import async_to_sync

from .services import LLMAnalysisService

logger = logging.getLogger(__name__)


# Cache key patterns
PROGRESS_CACHE_KEY = "llm_task_progress:{task_id}"
PROGRESS_CACHE_TTL = 3600  # 1 hour


def update_task_progress(task_id: str, progress: Dict[str, Any]):
    """
    Update task progress in cache.

    Args:
        task_id: Celery task ID
        progress: Progress dictionary with keys:
            - current: int, current progress
            - total: int, total items
            - status: str, status (pending, processing, complete, error)
            - message: str, status message
            - result: dict, partial results (optional)
    """
    cache_key = PROGRESS_CACHE_KEY.format(task_id=task_id)
    cache.set(cache_key, progress, timeout=PROGRESS_CACHE_TTL)


def get_task_progress(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get task progress from cache.

    Args:
        task_id: Celery task ID

    Returns:
        Progress dictionary or None if not found
    """
    cache_key = PROGRESS_CACHE_KEY.format(task_id=task_id)
    return cache.get(cache_key)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    soft_time_limit=300,  # 5 minutes
    time_limit=600,  # 10 minutes hard limit
)
def llm_analysis_task(
    self,
    requirement_id: str,
    requirement_text: str,
    candidates: List[Dict[str, Any]],
    config_id: Optional[str] = None,
    mode: str = "full",
    use_enhanced_prompts: bool = True
) -> Dict[str, Any]:
    """
    Analyze a single requirement with LLM (async task).

    This task performs LLM-based analysis of a requirement against
    candidate features, with automatic retry on failure.

    Args:
        self: Celery task instance (bind=True)
        requirement_id: UUID of the requirement
        requirement_text: Requirement text
        candidates: List of candidate feature dictionaries
        config_id: Optional LLM configuration ID
        mode: Analysis mode ("full" or "quick")
        use_enhanced_prompts: Whether to use enhanced prompts

    Returns:
        Analysis result dictionary with:
            - requirement_id: str
            - analysis: dict, LLM analysis results
            - status: str, "success" or "error"
            - error: str, error message if failed
            - cached: bool, whether result came from cache
            - tokens_used: dict, token usage statistics

    Raises:
        Exception: Re-tried up to max_retries times on failure
    """
    task_id = self.request.id

    # Initialize progress
    update_task_progress(task_id, {
        'current': 0,
        'total': 1,
        'status': 'processing',
        'message': 'Starting LLM analysis...',
        'requirement_id': requirement_id
    })

    logger.info(f"Starting LLM analysis task {task_id} for requirement {requirement_id}")

    try:
        # Create service instance
        service = LLMAnalysisService(config_id=config_id, use_cache=True)

        # Run async analysis in sync context
        result = async_to_sync(service.analyze_requirement_matches)(
            requirement_text=requirement_text,
            candidates=candidates,
            mode=mode,
            use_enhanced_prompts=use_enhanced_prompts
        )

        # Update progress
        update_task_progress(task_id, {
            'current': 1,
            'total': 1,
            'status': 'complete',
            'message': 'Analysis complete',
            'requirement_id': requirement_id,
            'result': result
        })

        logger.info(f"LLM analysis task {task_id} completed successfully")

        return {
            'requirement_id': requirement_id,
            'analysis': result,
            'status': 'success',
            'cached': result.get('cached', False),
            'tokens_used': result.get('tokens_used', {}),
            'task_id': task_id
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Task {task_id} exceeded soft time limit")

        update_task_progress(task_id, {
            'current': 0,
            'total': 1,
            'status': 'error',
            'message': 'Analysis timed out',
            'requirement_id': requirement_id
        })

        return {
            'requirement_id': requirement_id,
            'status': 'error',
            'error': 'Analysis timed out after 5 minutes',
            'task_id': task_id
        }

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")

        # Update progress with error
        update_task_progress(task_id, {
            'current': 0,
            'total': 1,
            'status': 'error',
            'message': f'Analysis failed: {str(e)}',
            'requirement_id': requirement_id
        })

        # Retry if attempts remain
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id}, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e)

        # Final attempt failed, return error result
        return {
            'requirement_id': requirement_id,
            'status': 'error',
            'error': str(e),
            'task_id': task_id
        }


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,  # 2 minutes
)
def batch_llm_analysis_task(
    self,
    requirements: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    config_id: Optional[str] = None,
    mode: str = "quick",
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """
    Analyze multiple requirements in batch (async task).

    This task orchestrates parallel LLM analysis of multiple requirements,
    with concurrency control and progress tracking.

    Args:
        self: Celery task instance (bind=True)
        requirements: List of requirement dictionaries with keys:
            - id: str, requirement ID
            - text: str, requirement text
        candidates: List of candidate feature dictionaries
        config_id: Optional LLM configuration ID
        mode: Analysis mode ("full" or "quick")
        max_concurrent: Maximum concurrent analyses

    Returns:
        Batch analysis result with:
            - total_count: int, total requirements
            - success_count: int, successful analyses
            - error_count: int, failed analyses
            - results: dict, requirement_id -> analysis result
            - errors: dict, requirement_id -> error message
            - task_id: str, parent task ID
    """
    task_id = self.request.id
    total_count = len(requirements)

    # Initialize progress
    update_task_progress(task_id, {
        'current': 0,
        'total': total_count,
        'status': 'processing',
        'message': f'Starting batch analysis of {total_count} requirements...',
        'success_count': 0,
        'error_count': 0
    })

    logger.info(f"Starting batch LLM analysis task {task_id} for {total_count} requirements")

    # Create individual tasks
    individual_tasks = []
    for req in requirements:
        req_id = req.get('id', req.get('requirement_id'))
        req_text = req.get('text', req.get('item_text', ''))

        task = llm_analysis_task.s(
            requirement_id=req_id,
            requirement_text=req_text,
            candidates=candidates,
            config_id=config_id,
            mode=mode,
            use_enhanced_prompts=True
        )

        individual_tasks.append(task)

    # Execute tasks in parallel with concurrency control
    # Use Celery's chord for parallel execution with callback
    from celery.result import allow_join_result

    results = {}
    errors = {}
    success_count = 0
    error_count = 0
    completed = 0

    # Execute group of tasks
    job = group(individual_tasks)
    result = job.apply_async()

    # Wait for results with progress updates
    try:
        with allow_join_result():
            for i, task_result in enumerate(result.iterate(timeout=600)):
                completed += 1

                if task_result['status'] == 'success':
                    success_count += 1
                    req_id = task_result['requirement_id']
                    results[req_id] = task_result
                else:
                    error_count += 1
                    req_id = task_result['requirement_id']
                    errors[req_id] = task_result.get('error', 'Unknown error')

                # Update progress
                update_task_progress(task_id, {
                    'current': completed,
                    'total': total_count,
                    'status': 'processing',
                    'message': f'Completed {completed}/{total_count} analyses',
                    'success_count': success_count,
                    'error_count': error_count
                })

                logger.info(f"Batch task {task_id}: {completed}/{total_count} complete")

    except SoftTimeLimitExceeded:
        logger.error(f"Batch task {task_id} timed out")

        # Collect partial results
        for task_result in result.results:
            if task_result.ready():
                try:
                    task_result_data = task_result.get()
                    req_id = task_result_data['requirement_id']

                    if task_result_data['status'] == 'success':
                        success_count += 1
                        results[req_id] = task_result_data
                    else:
                        error_count += 1
                        errors[req_id] = task_result_data.get('error')
                except:
                    error_count += 1

    # Final progress update
    update_task_progress(task_id, {
        'current': completed,
        'total': total_count,
        'status': 'complete',
        'message': f'Batch analysis complete: {success_count} succeeded, {error_count} failed',
        'success_count': success_count,
        'error_count': error_count,
        'results': results,
        'errors': errors
    })

    logger.info(f"Batch task {task_id} completed: {success_count} succeeded, {error_count} failed")

    return {
        'total_count': total_count,
        'success_count': success_count,
        'error_count': error_count,
        'results': results,
        'errors': errors,
        'task_id': task_id
    }


@shared_task
def cleanup_expired_cache_task():
    """
    Cleanup expired LLM cache entries (scheduled task).

    This task should be run periodically (e.g., daily) to remove
    expired cache entries and free up database space.

    Returns:
        Number of cache entries cleaned up
    """
    logger.info("Starting expired cache cleanup")

    try:
        from asgiref.sync import async_to_sync
        cleaned_count = async_to_sync(LLMAnalysisService.clear_expired_cache)()

        logger.info(f"Cache cleanup complete: {cleaned_count} entries removed")
        return cleaned_count

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return 0


@shared_task
def generate_cache_stats_task() -> Dict[str, Any]:
    """
    Generate cache statistics (scheduled/monitoring task).

    This task generates statistics about cache usage for monitoring
    and analytics purposes.

    Returns:
        Cache statistics dictionary
    """
    logger.info("Generating cache statistics")

    try:
        stats = LLMAnalysisService.get_cache_stats()
        logger.info(f"Cache stats: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to generate cache stats: {e}")
        return {}


@shared_task(bind=True)
def test_llm_connection_task(self, config_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Test LLM provider connection (async task).

    This task tests the connection to the configured LLM provider
    and returns diagnostic information.

    Args:
        self: Celery task instance
        config_id: Optional LLM configuration ID

    Returns:
        Test result dictionary with:
            - status: str, "success" or "error"
            - is_connected: bool
            - model_info: dict
            - response_time_ms: int
            - error: str, if failed
    """
    task_id = self.request.id

    logger.info(f"Testing LLM connection (task {task_id})")

    try:
        import time
        from .services import LLMService

        start_time = time.time()

        # Create service and test connection
        service = LLMService(config_id=config_id)
        result = async_to_sync(service.test_connection)()

        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)

        result['response_time_ms'] = response_time_ms
        result['task_id'] = task_id

        logger.info(f"Connection test complete: {result['status']}")

        return result

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            'status': 'error',
            'is_connected': False,
            'error': str(e),
            'task_id': task_id
        }
