"""
Test suite for cost tracking functionality.

Tests cover:
- LLMUsageLog model
- Cost statistics queries
- Cost alert service
- Management command

Total: 15 test cases
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from django.db.models import Sum

from apps.llm.models import LLMUsageLog
from apps.llm.services import LLMCostAlertService


class TestLLMUsageLogModel(TestCase):
    """Test suite for LLMUsageLog model."""

    def setUp(self):
        """Set up test data."""
        self.log = LLMUsageLog.objects.create(
            REQUEST_ID='test-request-123',
            timestamp=timezone.now(),
            provider='openai',
            model='gpt-4o-mini',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0003,
            request_type='analysis',
            requirement_id='req-123',
            feature_count=5,
            cache_hit=False,
            response_time_ms=500,
            status='success',
            metadata={'config_id': 'config-1'}
        )

    def test_01_log_creation(self):
        """Test 1: Verify LLMUsageLog can be created."""
        self.assertEqual(self.log.provider, 'openai')
        self.assertEqual(self.log.model, 'gpt-4o-mini')
        self.assertEqual(self.log.total_tokens, 150)
        self.assertEqual(self.log.status, 'success')
        self.assertFalse(self.log.cache_hit)

    def test_02_total_tokens_calculation(self):
        """Test 2: Verify total_tokens can be set manually."""
        log = LLMUsageLog.objects.create(
            REQUEST_ID='test-request-456',
            timestamp=timezone.now(),
            provider='zhipuai',
            model='glm-4-flash',
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            cost_usd=0.0001,
            request_type='batch_analysis',
            status='success'
        )
        self.assertEqual(log.total_tokens, 300)

    def test_03_status_choices(self):
        """Test 3: Verify only valid status choices can be used."""
        valid_statuses = ['success', 'error', 'timeout']
        for status in valid_statuses:
            log = LLMUsageLog.objects.create(
                REQUEST_ID=f'test-{status}',
                timestamp=timezone.now(),
                provider='openai',
                model='gpt-4o-mini',
                prompt_tokens=10,
                completion_tokens=10,
                total_tokens=20,
                cost_usd=0.00001,
                request_type='test',
                status=status
            )
            self.assertEqual(log.status, status)

    def test_04_get_daily_cost(self):
        """Test 4: Verify get_daily_cost class method."""
        # Create logs for today
        today = timezone.now().date()
        LLMUsageLog.objects.create(
            REQUEST_ID='cost-test-1',
            timestamp=timezone.now(),
            provider='openai',
            model='gpt-4o-mini',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.001,
            request_type='analysis',
            status='success'
        )
        LLMUsageLog.objects.create(
            REQUEST_ID='cost-test-2',
            timestamp=timezone.now(),
            provider='zhipuai',
            model='glm-4-flash',
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            cost_usd=0.002,
            request_type='analysis',
            status='success'
        )

        daily_cost = LLMUsageLog.get_daily_cost(today)
        self.assertAlmostEqual(daily_cost, 0.0033, places=6)

    def test_05_get_model_stats(self):
        """Test 5: Verify get_model_stats class method."""
        # Clear existing logs from setUp
        LLMUsageLog.objects.all().delete()

        # Create test logs
        for i in range(5):
            LLMUsageLog.objects.create(
                REQUEST_ID=f'stats-test-{i}',
                timestamp=timezone.now() - timedelta(days=i),
                provider='openai',
                model='gpt-4o-mini',
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=0.001,
                request_type='analysis',
                status='success'
            )

        stats = LLMUsageLog.get_model_stats('openai', 'gpt-4o-mini', days=7)

        self.assertEqual(stats['provider'], 'openai')
        self.assertEqual(stats['model'], 'gpt-4o-mini')
        self.assertEqual(stats['total_requests'], 5)
        self.assertEqual(stats['total_tokens'], 750)
        self.assertAlmostEqual(stats['total_cost'], 0.005, places=6)


class TestCostAlertService(unittest.TestCase):
    """Test suite for cost alert service."""

    def setUp(self):
        """Set up test service."""
        self.service = LLMCostAlertService()

    @patch('apps.llm.models.LLMUsageLog')
    def test_06_check_cost_thresholds_no_exceed(self, mock_log_model):
        """Test 6: Verify threshold check when cost is below threshold."""
        # Mock queryset
        mock_queryset = Mock()
        mock_log_model.objects.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {'total_cost': 5.0}
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        alert_result = self.service.check_cost_thresholds(
            period='daily',
            thresholds={'warning': 10.0, 'critical': 20.0}
        )

        self.assertFalse(alert_result['exceeded'])
        self.assertAlmostEqual(alert_result['current_cost'], 5.0, places=6)
        self.assertIsNone(alert_result['alert_level'])

    @patch('apps.llm.models.LLMUsageLog')
    def test_07_check_cost_thresholds_warning_exceeded(self, mock_log_model):
        """Test 7: Verify warning threshold is triggered."""
        # Mock queryset
        mock_queryset = Mock()
        mock_log_model.objects.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {'total_cost': 15.0}
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        alert_result = self.service.check_cost_thresholds(
            period='daily',
            thresholds={'warning': 10.0, 'critical': 20.0}
        )

        self.assertTrue(alert_result['exceeded'])
        self.assertAlmostEqual(alert_result['current_cost'], 15.0, places=6)
        self.assertEqual(alert_result['alert_level'], 'warning')
        self.assertAlmostEqual(alert_result['threshold'], 10.0, places=6)

    @patch('apps.llm.models.LLMUsageLog')
    def test_08_check_cost_thresholds_critical_exceeded(self, mock_log_model):
        """Test 8: Verify critical threshold is triggered."""
        # Mock queryset
        mock_queryset = Mock()
        mock_log_model.objects.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {'total_cost': 25.0}
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        alert_result = self.service.check_cost_thresholds(
            period='daily',
            thresholds={'warning': 10.0, 'critical': 20.0}
        )

        self.assertTrue(alert_result['exceeded'])
        self.assertAlmostEqual(alert_result['current_cost'], 25.0, places=6)
        self.assertEqual(alert_result['alert_level'], 'critical')
        self.assertAlmostEqual(alert_result['threshold'], 20.0, places=6)

    def test_09_format_alert_message(self):
        """Test 9: Verify alert message formatting."""
        alert_result = {
            'alert_level': 'warning',
            'current_cost': 15.0,
            'threshold': 10.0,
            'details': {
                'period': 'daily',
                'breakdown_by_model': [
                    {'provider': 'openai', 'model': 'gpt-4o-mini', 'cost': 10.0, 'requests': 100},
                    {'provider': 'zhipuai', 'model': 'glm-4-flash', 'cost': 5.0, 'requests': 50},
                ]
            }
        }

        message = self.service._format_alert_message(alert_result)

        self.assertIn('WARNING', message)
        self.assertIn('15.000000', message)
        self.assertIn('10.000000', message)
        self.assertIn('openai/gpt-4o-mini', message)
        self.assertIn('zhipuai/glm-4-flash', message)

    @patch('apps.llm.services.logger')
    def test_10_send_log_alert(self, mock_logger):
        """Test 10: Verify log alert is sent correctly."""
        alert_result = {
            'alert_level': 'warning',
            'current_cost': 15.0,
            'threshold': 10.0,
            'details': {'breakdown_by_model': []}
        }
        message = 'Test alert message'

        self.service._send_log_alert(alert_result, message)

        # Verify warning was logged
        self.assertTrue(mock_logger.warning.called)

    @patch('django.core.cache.cache')
    def test_11_alert_cooldown(self, mock_cache):
        """Test 11: Verify alert cooldown mechanism."""
        # Set cache to return True (on cooldown)
        mock_cache.get.return_value = True

        # Check cooldown
        is_on_cooldown = self.service._is_on_cooldown('daily:warning')

        self.assertTrue(is_on_cooldown)
        mock_cache.get.assert_called_once()

        # Set cooldown
        mock_cache.reset_mock()
        self.service._set_cooldown('daily:critical')

        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        self.assertIn('llm_cost_alerts', call_args[0][0])

    @patch('apps.llm.services.logger')
    @patch('apps.llm.models.LLMUsageLog')
    def test_12_send_alert_with_cooldown(self, mock_log_model, mock_logger):
        """Test 12: Verify alert is not sent when on cooldown."""
        # Mock queryset
        mock_queryset = Mock()
        mock_log_model.objects.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {'total_cost': 15.0}
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        # Mock cache to indicate cooldown
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = True

            alert_result = self.service.check_cost_thresholds(
                period='daily',
                thresholds={'warning': 10.0, 'critical': 20.0}
            )

            success = self.service.send_alert(alert_result, notification_channels=['log'])

            self.assertFalse(success)
            # Verify log was written about cooldown
            self.assertTrue(mock_logger.info.called)

    @patch('apps.llm.models.LLMUsageLog')
    def test_13_filter_by_provider(self, mock_log_model):
        """Test 13: Verify cost check can filter by provider."""
        mock_queryset = Mock()
        mock_log_model.objects.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {'total_cost': 5.0}
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        alert_result = self.service.check_cost_thresholds(
            period='daily',
            provider='openai'
        )

        # Verify filter was called with provider
        mock_queryset.filter.assert_called_with(provider='openai')

    @patch('apps.llm.models.LLMUsageLog')
    def test_14_check_weekly_period(self, mock_log_model):
        """Test 14: Verify weekly period calculation."""
        mock_queryset = Mock()
        mock_log_model.objects.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {'total_cost': 30.0}
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        alert_result = self.service.check_cost_thresholds(
            period='weekly',
            thresholds={'warning': 50.0, 'critical': 100.0}
        )

        # Verify the timestamp filter was called for weekly period
        self.assertTrue(mock_log_model.objects.filter.called)
        call_args = mock_log_model.objects.filter.call_args
        # Check that timestamp__gte was in the filter
        self.assertIn('timestamp__gte', str(call_args))

    @patch('apps.llm.models.LLMUsageLog')
    def test_15_get_alert_summary(self, mock_log_model):
        """Test 15: Verify alert summary generation."""
        mock_queryset = Mock()
        mock_log_model.objects.filter.return_value = mock_queryset
        mock_queryset.aggregate.return_value = {'total_cost': 5.0}
        mock_log_model.get_daily_cost.return_value = 1.0
        mock_queryset.values.return_value.annotate.return_value.order_by.return_value = []

        summary = LLMCostAlertService.get_alert_summary(days=3)

        self.assertEqual(summary['days'], 3)
        self.assertIn('periods', summary)
        self.assertIn('daily_costs', summary)
        self.assertEqual(len(summary['daily_costs']), 3)


class TestManagementCommand(unittest.TestCase):
    """Test suite for check_llm_costs management command."""

    @patch('apps.llm.services.LLMCostAlertService')
    def test_16_command_basic_execution(self, mock_service_class):
        """Test 16: Verify management command can be executed."""
        from apps.llm.management.commands.check_llm_costs import Command

        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.check_cost_thresholds.return_value = {
            'exceeded': False,
            'current_cost': 5.0,
            'threshold': 10.0,
            'alert_level': None,
            'details': {'breakdown_by_model': []}
        }

        command = Command()
        command.handle(
            period='daily',
            warning_threshold=None,
            critical_threshold=None,
            provider=None,
            model=None,
            send_alerts=False,
            channels='log',
            summary=False
        )

        # Verify check was called
        mock_service.check_cost_thresholds.assert_called_once()


if __name__ == '__main__':
    unittest.main()
