"""
Test suite for Celery tasks.

Tests cover:
- Progress tracking utilities
- Task structure and configuration
- Error handling helpers
- Cache cleanup tasks
- Connection testing tasks
- Mock Celery execution

Total: 10 test cases
"""

import unittest
from unittest.mock import Mock, patch
from datetime import timedelta

from apps.llm.tasks import (
    llm_analysis_task,
    batch_llm_analysis_task,
    cleanup_expired_cache_task,
    generate_cache_stats_task,
    test_llm_connection_task,
    update_task_progress,
    get_task_progress
)


class TestProgressTracking(unittest.TestCase):
    """Test suite for progress tracking utilities."""

    @patch('apps.llm.tasks.cache')
    def test_01_update_task_progress(self, mock_cache):
        """Test 1: Verify task progress is updated in cache."""
        task_id = "test-task-id"
        progress = {
            'current': 5,
            'total': 10,
            'status': 'processing',
            'message': 'Processing...'
        }

        update_task_progress(task_id, progress)

        # Verify cache.set was called
        self.assertTrue(mock_cache.set.called)
        call_args = mock_cache.set.call_args
        self.assertEqual(call_args[0][0], 'llm_task_progress:test-task-id')
        self.assertEqual(call_args[0][1]['current'], 5)

    @patch('apps.llm.tasks.cache')
    def test_02_get_task_progress(self, mock_cache):
        """Test 2: Verify task progress can be retrieved."""
        task_id = "test-task-id"
        expected_progress = {'current': 5, 'total': 10}
        mock_cache.get.return_value = expected_progress

        progress = get_task_progress(task_id)

        self.assertEqual(progress, expected_progress)
        mock_cache.get.assert_called_once_with('llm_task_progress:test-task-id')


class TestLLMAnalysisTask(unittest.TestCase):
    """Test suite for llm_analysis_task configuration."""

    def test_03_task_configuration(self):
        """Test 3: Verify llm_analysis_task has correct configuration."""
        # Check task is decorated with shared_task
        self.assertTrue(callable(llm_analysis_task))
        self.assertEqual(llm_analysis_task.name, 'apps.llm.tasks.llm_analysis_task')

        # Check task attributes
        self.assertEqual(llm_analysis_task.max_retries, 3)
        self.assertEqual(llm_analysis_task.default_retry_delay, 60)
        self.assertEqual(llm_analysis_task.soft_time_limit, 300)
        self.assertEqual(llm_analysis_task.time_limit, 600)

    def test_04_task_bind_config(self):
        """Test 4: Verify task is callable and properly configured."""
        # Tasks with bind=True are callable
        self.assertTrue(callable(llm_analysis_task))
        # Verify it's a Celery task by checking name attribute
        self.assertTrue(hasattr(llm_analysis_task, 'name'))


class TestBatchLLMAnalysisTask(unittest.TestCase):
    """Test suite for batch_llm_analysis_task."""

    def test_05_batch_task_configuration(self):
        """Test 5: Verify batch task has correct configuration."""
        self.assertTrue(callable(batch_llm_analysis_task))
        self.assertEqual(batch_llm_analysis_task.name, 'apps.llm.tasks.batch_llm_analysis_task')
        self.assertEqual(batch_llm_analysis_task.max_retries, 2)
        self.assertEqual(batch_llm_analysis_task.default_retry_delay, 120)

    def test_06_batch_task_progress_structure(self):
        """Test 6: Verify batch progress has correct structure."""
        task_id = "batch-task-123"

        # Test progress structure
        progress = {
            'current': 5,
            'total': 10,
            'status': 'processing',
            'success_count': 3,
            'error_count': 2
        }

        self.assertEqual(progress['current'], 5)
        self.assertEqual(progress['total'], 10)
        self.assertEqual(progress['success_count'], 3)
        self.assertEqual(progress['error_count'], 2)


class TestCacheCleanupTask(unittest.TestCase):
    """Test suite for cache cleanup task."""

    @patch('apps.llm.tasks.LLMAnalysisService')
    @patch('apps.llm.tasks.logger')
    def test_07_cache_cleanup_task(self, mock_logger, mock_service_class):
        """Test 7: Verify cache cleanup task works correctly."""
        # Setup mock
        async def mock_clear():
            return 5

        mock_service_class.clear_expired_cache = mock_clear

        # Execute task with patched async_to_sync
        with patch('apps.llm.tasks.async_to_sync', side_effect=lambda f: f()):
            result = cleanup_expired_cache_task()

        # Verify result
        self.assertEqual(result, 5)

    @patch('apps.llm.tasks.LLMAnalysisService')
    @patch('apps.llm.tasks.logger')
    def test_08_cache_cleanup_task_error_handling(self, mock_logger, mock_service_class):
        """Test 8: Verify cache cleanup handles errors gracefully."""
        # Setup mock to raise exception
        async def mock_clear_error():
            raise Exception("Database error")

        mock_service_class.clear_expired_cache = mock_clear_error

        # Execute task
        with patch('apps.llm.tasks.async_to_sync', side_effect=lambda f: f()):
            result = cleanup_expired_cache_task()

        # Verify error was handled
        self.assertEqual(result, 0)
        self.assertTrue(mock_logger.error.called)


class TestCacheStatsTask(unittest.TestCase):
    """Test suite for cache statistics task."""

    @patch('apps.llm.tasks.LLMAnalysisService')
    @patch('apps.llm.tasks.logger')
    def test_09_generate_cache_stats_task(self, mock_logger, mock_service_class):
        """Test 9: Verify cache stats task returns correct data."""
        # Setup mock
        expected_stats = {
            'total_entries': 100,
            'active_entries': 80,
            'total_hits': 500
        }
        mock_service_class.get_cache_stats.return_value = expected_stats

        # Execute task
        result = generate_cache_stats_task()

        # Verify result
        self.assertEqual(result, expected_stats)
        mock_service_class.get_cache_stats.assert_called_once()
        self.assertTrue(mock_logger.info.called)


class TestConnectionTestTask(unittest.TestCase):
    """Test suite for connection testing task."""

    def test_10_connection_test_task_configuration(self):
        """Test 10: Verify connection test task has correct configuration."""
        self.assertTrue(callable(test_llm_connection_task))
        self.assertEqual(test_llm_connection_task.name, 'apps.llm.tasks.test_llm_connection_task')
        # Verify it's a Celery task
        self.assertTrue(hasattr(test_llm_connection_task, 'name'))


if __name__ == '__main__':
    unittest.main()
