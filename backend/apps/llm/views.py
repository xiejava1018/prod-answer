"""
API views for LLM configuration and services.
"""
import time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import LLMModelConfig, LLMAnalysisResult, LLMUsageLog
from .serializers import (
    LLMModelConfigSerializer,
    LLMTestSerializer,
    LLMAnalysisResultSerializer,
    LLMUsageLogSerializer,
    DailyCostSerializer,
    ModelStatsSerializer,
    UsageSummarySerializer,
)
from .services import LLMProviderFactory


class LLMConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LLMModelConfig management.

    DEVELOPMENT MODE: No authentication required for easier testing

    list: List all LLM model configurations
    retrieve: Get configuration details
    create: Create a new configuration
    update: Update a configuration
    partial_update: Partially update a configuration
    destroy: Delete a configuration
    """

    queryset = LLMModelConfig.objects.all()
    serializer_class = LLMModelConfigSerializer

    def get_permissions(self):
        """
        Set permissions based on action.
        DEVELOPMENT MODE: Allow all actions without authentication
        """
        # TODO: Restore authentication for production
        # if self.action in ['list', 'retrieve', 'test']:
        #     permission_classes = [IsAuthenticated]
        # else:
        #     permission_classes = [IsAdminUser]
        permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Filter by active status if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by provider if requested
        provider = self.request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(provider=provider)

        return queryset.order_by('-is_default', 'provider', 'model_name')

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test the connection to an LLM provider.

        POST /api/v1/llm/configs/{id}/test/

        Returns:
            - success: boolean indicating if test passed
            - response_time_ms: time taken for the test
            - model_info: information about the model
            - error: error message if test failed
        """
        config = self.get_object()

        try:
            # Create provider instance (don't use cache to ensure fresh test)
            provider = LLMProviderFactory.create_provider(config, use_cache=False)

            # Measure response time
            start_time = time.time()

            # Test connection using provider's test_connection method
            is_connected = provider.test_connection()

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            if is_connected:
                model_info = provider.get_model_info()
                serializer = LLMTestSerializer({
                    'status': 'success',
                    'is_connected': True,
                    'response_time_ms': response_time_ms,
                    'model_info': model_info
                })
                return Response(serializer.data)
            else:
                serializer = LLMTestSerializer({
                    'status': 'failed',
                    'is_connected': False,
                    'response_time_ms': response_time_ms,
                    'error': 'Connection test failed - please check API key and model name'
                })
                return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            serializer = LLMTestSerializer({
                'status': 'error',
                'is_connected': False,
                'response_time_ms': response_time_ms,
                'error': str(e)
            })
            return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def active_providers(self, request):
        """
        Get list of active LLM provider configurations.

        GET /api/v1/llm/active_providers/
        """
        configs = LLMModelConfig.objects.filter(is_active=True)
        serializer = self.get_serializer(configs, many=True)
        return Response({
            'count': configs.count(),
            'providers': serializer.data
        })

    @action(detail=False, methods=['get'])
    def default_provider(self, request):
        """
        Get the default LLM provider configuration.

        GET /api/v1/llm/default_provider/
        """
        try:
            config = LLMModelConfig.objects.filter(is_default=True, is_active=True).first()

            if not config:
                # If no default, use first active config
                config = LLMModelConfig.objects.filter(is_active=True).first()

            if not config:
                return Response({
                    'error': 'No active LLM configuration found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = self.get_serializer(config)
            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set a configuration as the default.

        POST /api/v1/llm/configs/{id}/set_default/
        """
        config = self.get_object()

        # Remove default from all configs of the same provider
        LLMModelConfig.objects.filter(
            is_default=True,
            provider=config.provider
        ).update(is_default=False)

        # Set this config as default
        config.is_default = True
        config.save()

        # Clear provider cache
        LLMProviderFactory.clear_cache()

        serializer = self.get_serializer(config)
        return Response({
            'status': 'success',
            'message': f'{config.model_name} is now the default model for {config.provider}',
            'config': serializer.data
        })


class LLMAnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for LLMAnalysisResult (read-only).

    DEVELOPMENT MODE: No authentication required for easier testing

    list: List all LLM analysis results
    retrieve: Get analysis result details
    """

    queryset = LLMAnalysisResult.objects.all()
    serializer_class = LLMAnalysisResultSerializer
    permission_classes = [AllowAny]  # TODO: Restore IsAuthenticated for production

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        # Filter by requirement_item
        requirement_item_id = self.request.query_params.get('requirement_item_id')
        if requirement_item_id:
            queryset = queryset.filter(requirement_item_id=requirement_item_id)

        # Filter by feature
        feature_id = self.request.query_params.get('feature_id')
        if feature_id:
            queryset = queryset.filter(feature_id=feature_id)

        # Filter by match validity
        is_valid = self.request.query_params.get('is_valid')
        if is_valid is not None:
            if is_valid.lower() == 'true':
                queryset = queryset.filter(is_valid_match=True)
            elif is_valid.lower() == 'false':
                queryset = queryset.filter(is_valid_match=False)
            else:
                queryset = queryset.filter(is_valid_match=None)

        # Filter by confidence score threshold
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            try:
                queryset = queryset.filter(confidence_score__gte=float(min_confidence))
            except ValueError:
                pass

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about LLM analysis results.

        GET /api/v1/llm/analysis-results/stats/
        """
        total_results = LLMAnalysisResult.objects.count()

        # Count by validity
        valid_count = LLMAnalysisResult.objects.filter(is_valid_match=True).count()
        invalid_count = LLMAnalysisResult.objects.filter(is_valid_match=False).count()
        inconclusive_count = LLMAnalysisResult.objects.filter(is_valid_match=None).count()

        # Count by provider
        from django.db.models import Count
        provider_stats = LLMAnalysisResult.objects.values('llm_provider').annotate(
            count=Count('id')
        ).order_by('-count')

        # Average confidence
        avg_confidence = LLMAnalysisResult.objects.filter(
            confidence_score__isnull=False
        ).values_list('confidence_score', flat=True)

        if avg_confidence:
            from django.db.models import Avg
            avg_confidence_value = LLMAnalysisResult.objects.aggregate(
                avg_conf=Avg('confidence_score')
            )['avg_conf']
        else:
            avg_confidence_value = None

        return Response({
            'total_results': total_results,
            'valid_matches': valid_count,
            'invalid_matches': invalid_count,
            'inconclusive': inconclusive_count,
            'average_confidence': round(avg_confidence_value, 3) if avg_confidence_value else None,
            'provider_distribution': list(provider_stats)
        })


class LLMUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for LLMUsageLog (read-only).

    DEVELOPMENT MODE: No authentication required for easier testing

    list: List all LLM usage logs
    retrieve: Get usage log details
    """

    queryset = LLMUsageLog.objects.all()
    serializer_class = LLMUsageLogSerializer
    permission_classes = [AllowAny]  # TODO: Restore IsAuthenticated for production

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()

        # Filter by provider
        provider = self.request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(provider=provider)

        # Filter by model
        model = self.request.query_params.get('model')
        if model:
            queryset = queryset.filter(model=model)

        # Filter by request type
        request_type = self.request.query_params.get('request_type')
        if request_type:
            queryset = queryset.filter(request_type=request_type)

        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by cache hit
        cache_hit = self.request.query_params.get('cache_hit')
        if cache_hit is not None:
            queryset = queryset.filter(cache_hit=cache_hit.lower() == 'true')

        # Filter by date range
        from django.utils import timezone
        from datetime import datetime, timedelta

        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if date_from:
            try:
                datetime_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=datetime_from)
            except ValueError:
                pass

        if date_to:
            try:
                datetime_to = datetime.strptime(date_to, '%Y-%m-%d')
                # Include the entire end date
                datetime_to = datetime_to + timedelta(days=1)
                queryset = queryset.filter(timestamp__lt=datetime_to)
            except ValueError:
                pass

        return queryset.order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get overall usage summary.

        GET /api/v1/llm/usage/summary/

        Query parameters:
            - days: Number of days to include (default: 7)
        """
        from django.db.models import Sum, Avg, Count, Q
        from django.utils import timezone
        from datetime import timedelta

        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)

        # Base queryset for the date range
        queryset = LLMUsageLog.objects.filter(timestamp__gte=since)

        # Total statistics
        total_stats = queryset.aggregate(
            total_requests=Count('id'),
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost_usd'),
            avg_response_time=Avg('response_time_ms')
        )

        # Cache statistics
        cache_stats = queryset.aggregate(
            cache_hits=Count('id', filter=Q(cache_hit=True)),
            cache_misses=Count('id', filter=Q(cache_hit=False))
        )

        total_requests = total_stats['total_requests'] or 0
        cache_hits = cache_stats['cache_hits'] or 0
        cache_misses = cache_stats['cache_misses'] or 0
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0

        # Success rate
        success_count = queryset.filter(status='success').count() or 0
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0

        # Most used provider and model
        most_used = queryset.values('provider', 'model').annotate(
            count=Count('id')
        ).order_by('-count').first()

        most_used_provider = most_used['provider'] if most_used else None
        most_used_model = most_used['model'] if most_used else None

        # Daily costs for the period
        daily_costs_data = []
        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).date()
            daily_cost = LLMUsageLog.get_daily_cost(date)

            daily_queryset = queryset.filter(timestamp__date=date)
            daily_stats = daily_queryset.aggregate(
                requests=Count('id'),
                tokens=Sum('total_tokens'),
                avg_response=Avg('response_time_ms')
            )

            if daily_stats['requests'] > 0:
                daily_cache_hits = daily_queryset.filter(cache_hit=True).count()
                daily_cache_hit_rate = (daily_cache_hits / daily_stats['requests'] * 100)

                daily_costs_data.append({
                    'date': date,
                    'total_cost': round(daily_cost, 6),
                    'total_requests': daily_stats['requests'],
                    'total_tokens': daily_stats['tokens'] or 0,
                    'cache_hit_rate': round(daily_cache_hit_rate, 2),
                    'avg_response_time_ms': int(daily_stats['avg_response'] or 0)
                })

        # Model statistics for top providers/models
        provider_model_stats = queryset.values('provider', 'model').annotate(
            total_requests=Count('id'),
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost_usd'),
            avg_cost=Avg('cost_usd'),
            avg_tokens=Avg('total_tokens')
        ).order_by('-total_cost')[:10]

        model_stats_data = []
        for stat in provider_model_stats:
            model_stats_data.append({
                'provider': stat['provider'],
                'model': stat['model'],
                'days': days,
                'total_requests': stat['total_requests'],
                'total_tokens': stat['total_tokens'] or 0,
                'total_cost': round(stat['total_cost'] or 0, 6),
                'avg_cost': round(stat['avg_cost'] or 0, 6),
                'avg_tokens': round(stat['avg_tokens'] or 0, 1)
            })

        return Response({
            'total_requests': total_requests,
            'total_tokens': total_stats['total_tokens'] or 0,
            'total_cost': round(total_stats['total_cost'] or 0, 6),
            'cache_hit_count': cache_hits,
            'cache_miss_count': cache_misses,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'success_rate': round(success_rate, 2),
            'avg_response_time_ms': int(total_stats['avg_response_time'] or 0),
            'most_used_provider': most_used_provider,
            'most_used_model': most_used_model,
            'daily_costs': list(reversed(daily_costs_data)),
            'model_stats': model_stats_data
        })

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """
        Get daily cost summary.

        GET /api/v1/llm/usage/daily/

        Query parameters:
            - date: Date in YYYY-MM-DD format (default: today)
        """
        from django.utils import timezone

        date_str = request.query_params.get('date')
        if date_str:
            try:
                from datetime import datetime
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': f'Invalid date format: {date_str}. Use YYYY-MM-DD.'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            date = timezone.now().date()

        total_cost = LLMUsageLog.get_daily_cost(date)

        # Get additional statistics for this date
        from django.db.models import Sum, Count, Avg
        from datetime import datetime, timedelta
        import django.utils.timezone as tz

        datetime_start = tz.make_aware(
            datetime.combine(date, datetime.min.time())
        )
        datetime_end = tz.make_aware(
            datetime.combine(date, datetime.max.time())
        )

        queryset = LLMUsageLog.objects.filter(
            timestamp__range=[datetime_start, datetime_end]
        )

        stats = queryset.aggregate(
            total_requests=Count('id'),
            total_tokens=Sum('total_tokens'),
            avg_response_time=Avg('response_time_ms')
        )

        # Cache hit rate
        total_requests = stats['total_requests'] or 0
        cache_hits = queryset.filter(cache_hit=True).count()
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0

        return Response({
            'date': date,
            'total_cost': round(total_cost, 6),
            'total_requests': total_requests,
            'total_tokens': stats['total_tokens'] or 0,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'avg_response_time_ms': int(stats['avg_response_time'] or 0)
        })

    @action(detail=False, methods=['get'])
    def by_model(self, request):
        """
        Get usage statistics grouped by provider and model.

        GET /api/v1/llm/usage/by_model/

        Query parameters:
            - provider: Filter by provider (optional)
            - model: Filter by model (optional)
            - days: Number of days to look back (default: 7)
        """
        from django.db.models import Sum, Avg, Count
        from django.utils import timezone
        from datetime import timedelta

        provider = request.query_params.get('provider')
        model = request.query_params.get('model')
        days = int(request.query_params.get('days', 7))

        since = timezone.now() - timedelta(days=days)

        queryset = LLMUsageLog.objects.filter(
            timestamp__gte=since,
            status='success'
        )

        if provider:
            queryset = queryset.filter(provider=provider)
        if model:
            queryset = queryset.filter(model=model)

        # Group by provider and model
        stats = queryset.values('provider', 'model').annotate(
            total_requests=Count('id'),
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost_usd'),
            avg_cost=Avg('cost_usd'),
            avg_tokens=Avg('total_tokens')
        ).order_by('-total_cost')

        results = []
        for stat in stats:
            results.append({
                'provider': stat['provider'],
                'model': stat['model'],
                'days': days,
                'total_requests': stat['total_requests'],
                'total_tokens': stat['total_tokens'] or 0,
                'total_cost': round(stat['total_cost'] or 0, 6),
                'avg_cost': round(stat['avg_cost'] or 0, 6),
                'avg_tokens': round(stat['avg_tokens'] or 0, 1)
            })

        return Response({
            'days': days,
            'count': len(results),
            'results': results
        })

    @action(detail=False, methods=['get'])
    def top_costs(self, request):
        """
        Get requests with highest costs.

        GET /api/v1/llm/usage/top_costs/

        Query parameters:
            - limit: Number of results to return (default: 20)
        """
        limit = int(request.query_params.get('limit', 20))

        queryset = LLMUsageLog.objects.filter(
            status='success'
        ).order_by('-cost_usd')[:limit]

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'limit': limit,
            'count': queryset.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def errors(self, request):
        """
        Get failed or timed out requests.

        GET /api/v1/llm/usage/errors/

        Query parameters:
            - limit: Number of results to return (default: 50)
        """
        limit = int(request.query_params.get('limit', 50))

        queryset = LLMUsageLog.objects.filter(
            status__in=['error', 'timeout']
        ).order_by('-timestamp')[:limit]

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'limit': limit,
            'count': queryset.count(),
            'results': serializer.data
        })
