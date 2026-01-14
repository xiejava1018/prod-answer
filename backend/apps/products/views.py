"""
API views for Product and Feature management.
"""
import os
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import Product, Feature
from .serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    FeatureSerializer,
    FeatureListSerializer,
    FeatureUpdateSerializer,
    BatchFeatureSerializer,
)
from .import_service import ProductImportService
from apps.embeddings.services import EmbeddingServiceFactory
import time


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product model.

    list: List all products
    retrieve: Get product details
    create: Create a new product
    update: Update a product
    partial_update: Partially update a product
    destroy: Delete a product
    """

    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'vendor', 'is_active']
    search_fields = ['name', 'description', 'vendor']
    ordering_fields = ['name', 'created_at', 'category']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft delete product."""
        product = self.get_object()
        product.is_active = False
        product.save()
        return Response({'status': 'Product deleted successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def features(self, request, pk=None):
        """
        Get all features for a product.

        GET /api/v1/products/{id}/features/
        """
        product = self.get_object()
        features = product.features.filter(is_active=True)

        # Filter by category if provided
        category = request.query_params.get('category')
        if category:
            features = features.filter(category=category)

        serializer = FeatureListSerializer(features, many=True)
        return Response({
            'product_id': str(product.id),
            'product_name': product.name,
            'features_count': features.count(),
            'features': serializer.data
        })

    @action(detail=True, methods=['post'])
    def add_feature(self, request, pk=None):
        """
        Add a single feature to a product.

        POST /api/v1/products/{id}/add_feature/
        Body: { feature_name, description, category, ... }
        """
        product = self.get_object()
        serializer = FeatureSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def batch_import(self, request):
        """
        Batch import features for a product.

        POST /api/v1/products/batch_import/
        Body: { product_id, features: [...] }
        """
        serializer = BatchFeatureSerializer(data=request.data)

        if serializer.is_valid():
            features = serializer.save()
            return Response({
                'status': 'success',
                'count': len(features),
                'features': FeatureSerializer(features, many=True).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def import_subsystem_data(self, request):
        """
        Import subsystem products from JSON file.

        POST /api/v1/products/import_subsystem_data/
        Body: { json_file_path: str, vendor: str }
        """
        json_file_path = request.data.get('json_file_path')
        vendor = request.data.get('vendor', '默认厂商')

        if not json_file_path:
            return Response({
                'error': 'json_file_path is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查文件是否存在
        if not os.path.exists(json_file_path):
            return Response({
                'error': f'File not found: {json_file_path}'
            }, status=status.HTTP_404_NOT_FOUND)

        # 执行导入
        results = ProductImportService.import_from_json(json_file_path, vendor)

        if results['success']:
            return Response({
                'status': 'success',
                'message': 'Products imported successfully',
                'products_created': results['products_created'],
                'features_created': results['features_created']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'errors': results['errors']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def clear_subsystem_data(self, request):
        """
        Clear all subsystem products and features.

        POST /api/v1/products/clear_subsystem_data/
        """
        results = ProductImportService.clear_subsystem_products()

        if results['success']:
            return Response({
                'status': 'success',
                'message': 'Subsystem data cleared successfully',
                'products_deleted': results['products_deleted'],
                'features_deleted': results['features_deleted']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'errors': results['errors']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Feature model.

    list: List all features
    retrieve: Get feature details
    create: Create a new feature
    update: Update a feature
    partial_update: Partially update a feature
    destroy: Delete a feature
    """

    queryset = Feature.objects.filter(is_active=True)
    serializer_class = FeatureSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'category', 'subcategory', 'importance_level']
    search_fields = ['feature_name', 'description', 'feature_code']
    ordering_fields = ['feature_name', 'importance_level', 'created_at']
    ordering = ['product', 'category', 'subcategory', 'feature_name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['update', 'partial_update']:
            return FeatureUpdateSerializer
        return FeatureSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft delete feature."""
        feature = self.get_object()
        feature.is_active = False
        feature.save()
        return Response({'status': 'Feature deleted successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def generate_embedding(self, request, pk=None):
        """
        Generate embedding for a single feature.

        POST /api/v1/features/{id}/generate_embedding/
        Body: { config_id? }
        """
        feature = self.get_object()
        config_id = request.data.get('config_id')

        try:
            # Get embedding service
            if config_id:
                provider = EmbeddingServiceFactory.get_provider_by_id(config_id)
            else:
                provider = EmbeddingServiceFactory.get_default_provider()

            # Generate embedding - emphasize description for better matching
            # Use description twice to give it more weight in semantic matching
            text = f"{feature.feature_name}。功能描述：{feature.description}。详细说明：{feature.description}"
            embedding = provider.encode_single(text)

            # Save embedding
            from apps.products.models import FeatureEmbedding

            FeatureEmbedding.objects.update_or_create(
                feature=feature,
                model_name=provider.model_name,
                defaults={
                    'embedding': embedding,
                    'model_version': provider.model_params.get('model', 'unknown')
                }
            )

            return Response({
                'status': 'success',
                'feature_id': str(feature.id),
                'model_name': provider.model_name,
                'dimension': len(embedding)
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def generate_embeddings_batch(self, request):
        """
        Generate embeddings for multiple features.

        POST /api/v1/features/generate_embeddings_batch/
        Body: { feature_ids?, product_id?, config_id?, regenerate? }
        """
        from apps.products.models import FeatureEmbedding

        feature_ids = request.data.get('feature_ids')
        product_id = request.data.get('product_id')
        config_id = request.data.get('config_id')
        regenerate = request.data.get('regenerate', False)

        # Get features to process
        if feature_ids:
            features = Feature.objects.filter(id__in=feature_ids, is_active=True)
        elif product_id:
            features = Feature.objects.filter(product_id=product_id, is_active=True)
        else:
            return Response({
                'error': 'Either feature_ids or product_id must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get embedding service
            if config_id:
                provider = EmbeddingServiceFactory.get_provider_by_id(config_id)
            else:
                provider = EmbeddingServiceFactory.get_default_provider()

            results = {
                'success': [],
                'failed': [],
                'skipped': []
            }

            for feature in features:
                try:
                    # Check if embedding already exists
                    existing = FeatureEmbedding.objects.filter(
                        feature=feature,
                        model_name=provider.model_name
                    ).first()

                    if existing and not regenerate:
                        results['skipped'].append(str(feature.id))
                        continue

                    # Generate embedding - emphasize description for better matching
                    # Use description twice to give it more weight in semantic matching
                    text = f"{feature.feature_name}。功能描述：{feature.description}。详细说明：{feature.description}"
                    embedding = provider.encode_single(text)

                    # Save or update embedding
                    FeatureEmbedding.objects.update_or_create(
                        feature=feature,
                        model_name=provider.model_name,
                        defaults={
                            'embedding': embedding,
                            'model_version': provider.model_params.get('model', 'unknown')
                        }
                    )

                    results['success'].append(str(feature.id))

                except Exception as e:
                    results['failed'].append({
                        'feature_id': str(feature.id),
                        'error': str(e)
                    })

            return Response({
                'status': 'completed',
                'summary': {
                    'total': len(features),
                    'success': len(results['success']),
                    'failed': len(results['failed']),
                    'skipped': len(results['skipped'])
                },
                'results': results
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
