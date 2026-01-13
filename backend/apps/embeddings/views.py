"""
API views for Embedding configuration and services.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EmbeddingModelConfig
from .serializers import (
    EmbeddingModelConfigSerializer,
    EmbeddingTestSerializer,
    EmbeddingEncodeSerializer,
    EmbeddingGenerateSerializer,
)
from .services import EmbeddingServiceFactory


class EmbeddingConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmbeddingModelConfig management.

    list: List all embedding model configurations
    retrieve: Get configuration details
    create: Create a new configuration
    update: Update a configuration
    partial_update: Partially update a configuration
    destroy: Delete a configuration
    """

    queryset = EmbeddingModelConfig.objects.all()
    serializer_class = EmbeddingModelConfigSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Filter by active status if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('-is_default', 'model_name')

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set a configuration as the default.

        POST /api/v1/embeddings/configs/{id}/set_default/
        """
        config = self.get_object()

        # Remove default from all configs
        EmbeddingModelConfig.objects.filter(is_default=True).update(is_default=False)

        # Set this config as default
        config.is_default = True
        config.save()

        # Clear provider cache
        EmbeddingServiceFactory.clear_cache()

        serializer = self.get_serializer(config)
        return Response({
            'status': 'success',
            'message': f'{config.model_name} is now the default model',
            'config': serializer.data
        })

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test the connection to an embedding model.

        POST /api/v1/embeddings/configs/{id}/test_connection/
        """
        config = self.get_object()

        try:
            provider = EmbeddingServiceFactory.create_provider(config, use_cache=False)
            is_connected = provider.test_connection()

            if is_connected:
                model_info = provider.get_model_info()
                serializer = EmbeddingTestSerializer({
                    'status': 'success',
                    'is_connected': True,
                    'model_info': model_info
                })
                return Response(serializer.data)
            else:
                serializer = EmbeddingTestSerializer({
                    'status': 'failed',
                    'is_connected': False,
                    'error': 'Connection test failed'
                })
                return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            serializer = EmbeddingTestSerializer({
                'status': 'error',
                'is_connected': False,
                'error': str(e)
            })
            return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def active_providers(self, request):
        """
        Get list of active embedding providers.

        GET /api/v1/embeddings/active_providers/
        """
        configs = EmbeddingModelConfig.objects.filter(is_active=True)
        serializer = self.get_serializer(configs, many=True)
        return Response({
            'count': configs.count(),
            'providers': serializer.data
        })

    @action(detail=False, methods=['get'])
    def default_provider(self, request):
        """
        Get the default embedding provider.

        GET /api/v1/embeddings/default_provider/
        """
        try:
            config = EmbeddingModelConfig.objects.filter(is_default=True, is_active=True).first()

            if not config:
                config = EmbeddingModelConfig.objects.filter(is_active=True).first()

            if not config:
                return Response({
                    'error': 'No active embedding configuration found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = self.get_serializer(config)
            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def encode(self, request):
        """
        Encode texts using specified or default embedding model.

        POST /api/v1/embeddings/encode/
        Body: { texts: [...], config_id? }
        """
        serializer = EmbeddingEncodeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            texts = serializer.validated_data['texts']
            config_id = serializer.validated_data.get('config_id')

            # Encode texts
            embeddings = EmbeddingServiceFactory.encode_texts(texts, config_id)

            return Response({
                'status': 'success',
                'count': len(embeddings),
                'dimension': len(embeddings[0]) if embeddings else 0,
                'embeddings': embeddings
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmbeddingServiceViewSet(viewsets.ViewSet):
    """
    ViewSet for Embedding service operations.
    """

    def list(self, request):
        """
        Get embedding service information.

        GET /api/v1/embeddings/service/
        """
        try:
            service_info = EmbeddingServiceFactory.get_default_provider().get_model_info()

            # Get active configs count
            active_count = EmbeddingModelConfig.objects.filter(is_active=True).count()

            return Response({
                'service': 'Embedding Service',
                'version': '1.0.0',
                'active_configs': active_count,
                'default_model': service_info
            })

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def default_provider(self, request):
        """
        Get the default embedding provider configuration.

        GET /api/v1/service/default_provider/
        """
        try:
            config = EmbeddingModelConfig.objects.filter(is_default=True, is_active=True).first()

            if not config:
                config = EmbeddingModelConfig.objects.filter(is_active=True).first()

            if not config:
                return Response({
                    'error': 'No active embedding configuration found'
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = EmbeddingModelConfigSerializer(config)
            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def health_check(self, request):
        """
        Check embedding service health.

        POST /api/v1/embeddings/health_check/
        """
        try:
            service = EmbeddingServiceFactory()
            result = service.test_connection()

            return Response(result)

        except Exception as e:
            return Response({
                'status': 'error',
                'is_connected': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
