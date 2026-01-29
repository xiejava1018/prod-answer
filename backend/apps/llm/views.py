"""
API views for LLM configuration and services.
"""
import time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import LLMModelConfig, LLMAnalysisResult
from .serializers import (
    LLMModelConfigSerializer,
    LLMTestSerializer,
    LLMAnalysisResultSerializer,
)
from .services import LLMProviderFactory


class LLMConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LLMModelConfig management.

    list: List all LLM model configurations (authenticated users)
    retrieve: Get configuration details (authenticated users)
    create: Create a new configuration (admin only)
    update: Update a configuration (admin only)
    partial_update: Partially update a configuration (admin only)
    destroy: Delete a configuration (admin only)
    """

    queryset = LLMModelConfig.objects.all()
    serializer_class = LLMModelConfigSerializer

    def get_permissions(self):
        """
        Set permissions based on action.
        - Read operations: Any authenticated user
        - Write operations: Admin only
        """
        if self.action in ['list', 'retrieve', 'test']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
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

    list: List all LLM analysis results
    retrieve: Get analysis result details
    """

    queryset = LLMAnalysisResult.objects.all()
    serializer_class = LLMAnalysisResultSerializer
    permission_classes = [IsAuthenticated]

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
