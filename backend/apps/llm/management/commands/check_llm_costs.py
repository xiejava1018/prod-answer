"""
Django management command to check LLM costs and send alerts.

Usage:
    python manage.py check_llm_costs --period=daily
    python manage.py check_llm_costs --period=weekly --send-alerts
    python manage.py check_llm_costs --provider=openai --model=gpt-4o-mini
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.llm.services import LLMCostAlertService


class Command(BaseCommand):
    help = 'Check LLM costs and send alerts if thresholds are exceeded'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--period',
            type=str,
            default='daily',
            choices=['daily', 'weekly', 'monthly'],
            help='Time period to check (default: daily)'
        )
        parser.add_argument(
            '--warning-threshold',
            type=float,
            help='Warning threshold in USD (default: 10.0 for daily)'
        )
        parser.add_argument(
            '--critical-threshold',
            type=float,
            help='Critical threshold in USD (default: 2x warning threshold)'
        )
        parser.add_argument(
            '--provider',
            type=str,
            help='Filter by provider (e.g., openai, zhipuai)'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Filter by model (e.g., gpt-4o-mini)'
        )
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Send alert notifications if thresholds are exceeded'
        )
        parser.add_argument(
            '--channels',
            type=str,
            default='log',
            help='Notification channels (comma-separated: log,email,webhook)'
        )
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Show alert summary for the past 7 days'
        )

    def handle(self, *args, **options):
        """Handle the command."""
        try:
            if options.get('summary'):
                self._show_summary()
                return

            # Get command options
            period = options['period']
            warning_threshold = options.get('warning_threshold')
            critical_threshold = options.get('critical_threshold')
            provider = options.get('provider')
            model = options.get('model')
            send_alerts = options.get('send_alerts')
            channels_str = options.get('channels', 'log')
            channels = [c.strip() for c in channels_str.split(',')]

            # Build thresholds dictionary
            thresholds = None
            if warning_threshold or critical_threshold:
                thresholds = {}
                if warning_threshold:
                    thresholds['warning'] = warning_threshold
                if critical_threshold:
                    thresholds['critical'] = critical_threshold
                else:
                    # Default critical = 2x warning
                    thresholds['critical'] = warning_threshold * 2

            # Check costs
            service = LLMCostAlertService()
            alert_result = service.check_cost_thresholds(
                period=period,
                thresholds=thresholds,
                provider=provider,
                model=model
            )

            # Display results
            self._display_alert_result(alert_result, period, provider, model)

            # Send alerts if requested
            if send_alerts and alert_result['exceeded']:
                success = service.send_alert(alert_result, notification_channels=channels)
                if success:
                    self.stdout.write(self.style.SUCCESS(f'\nAlert sent via: {", ".join(channels)}'))
                else:
                    self.stdout.write(self.style.WARNING('\nAlert was on cooldown or failed to send'))

        except Exception as e:
            raise CommandError(f'Error checking costs: {e}')

    def _display_alert_result(self, alert_result, period, provider, model):
        """Display alert results."""
        # Header
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'LLM Cost Check - {period.upper()}')
        if provider:
            self.stdout.write(f'Provider: {provider}')
        if model:
            self.stdout.write(f'Model: {model}')
        self.stdout.write(f'{"="*60}\n')

        # Current status
        current_cost = alert_result['current_cost']
        threshold = alert_result['threshold']
        exceeded = alert_result['exceeded']
        alert_level = alert_result['alert_level']

        if exceeded:
            if alert_level == 'critical':
                style = self.style.ERROR
            elif alert_level == 'warning':
                style = self.style.WARNING
            else:
                style = self.style.NOTICE

            self.stdout.write(style(f'Status: THRESHOLD EXCEEDED ({alert_level.upper()})'))
            self.stdout.write(style(f'Current Cost: ${current_cost:.6f}'))
            self.stdout.write(style(f'Threshold: ${threshold:.6f}'))
            self.stdout.write(style(f'Over Budget: ${current_cost - threshold:.6f}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Status: OK - Threshold not exceeded'))
            self.stdout.write(f'Current Cost: ${current_cost:.6f}')
            if threshold:
                self.stdout.write(f'Threshold: ${threshold:.6f}')
                self.stdout.write(f'Remaining: ${threshold - current_cost:.6f}')

        # Breakdown
        self.stdout.write(f'\nTop Cost Drivers:')
        breakdown = alert_result['details']['breakdown_by_model']
        if breakdown:
            for item in breakdown[:5]:
                provider = item['provider']
                model = item['model']
                cost = item['cost']
                requests = item['requests']
                self.stdout.write(f'  - {provider}/{model}: ${cost:.6f} ({requests} requests)')
        else:
            self.stdout.write('  No cost data for this period')

        self.stdout.write(f'\n{"="*60}\n')

    def _show_summary(self):
        """Show alert summary for the past 7 days."""
        summary = LLMCostAlertService.get_alert_summary(days=7)

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'LLM Cost Alert Summary - Last 7 Days')
        self.stdout.write(f'{"="*60}\n')

        # Period status
        for period, alert_result in summary['periods'].items():
            current_cost = alert_result['current_cost']
            threshold = alert_result['threshold']
            exceeded = alert_result['exceeded']
            alert_level = alert_result['alert_level']

            self.stdout.write(f'{period.upper()}:')
            self.stdout.write(f'  Current Cost: ${current_cost:.6f}')
            if threshold:
                self.stdout.write(f'  Threshold: ${threshold:.6f}')

            if exceeded:
                if alert_level == 'critical':
                    style = self.style.ERROR
                else:
                    style = self.style.WARNING
                self.stdout.write(style(f'  Status: EXCEEDED ({alert_level.upper()})'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  Status: OK'))
            self.stdout.write('')

        # Daily breakdown
        self.stdout.write(f'\nDaily Breakdown:')
        for daily in summary['daily_costs']:
            date = daily['date']
            cost = daily['current_cost']
            exceeded = daily['exceeded']

            if exceeded:
                style = self.style.WARNING
                status = '⚠️'
            else:
                style = self.stdout
                status = '✓'

            style.write(f'  {status} {date}: ${cost:.6f}')

        self.stdout.write(f'\n{"="*60}\n')
