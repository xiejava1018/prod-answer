"""
API views for Matching operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import CapabilityRequirement, RequirementItem, MatchRecord
from .serializers import (
    CapabilityRequirementSerializer,
    CapabilityRequirementCreateSerializer,
    RequirementListSerializer,
    MatchRecordSerializer,
    MatchAnalyzeSerializer,
    MatchResultSerializer,
    MatchResultDetailSerializer,
    MatchSummarySerializer,
)
from .services import MatchingService
import time


class MatchingViewSet(viewsets.ViewSet):
    """
    ViewSet for matching operations.

    analyze: Perform matching analysis for a requirement
    results: Get match results for a requirement
    summary: Get match summary statistics
    export: Export match results
    """

    def create(self, request):
        """
        Perform matching analysis.

        POST /api/v1/matching/analyze
        Body: { requirement_id, threshold?, product_ids?, limit? }
        """
        serializer = MatchAnalyzeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        requirement_id = serializer.validated_data['requirement_id']
        threshold = serializer.validated_data['threshold']
        product_ids = serializer.validated_data.get('product_ids')
        limit = serializer.validated_data['limit']

        try:
            # Get requirement
            requirement = CapabilityRequirement.objects.get(id=requirement_id)

            # Perform matching
            service = MatchingService(threshold=threshold)
            start_time = time.time()

            result = service.process_requirement(
                requirement_id=str(requirement_id),
                generate_embeddings=True
            )

            processing_time = time.time() - start_time

            result['processing_time'] = round(processing_time, 2)

            # Wrap result in summary for frontend compatibility
            return Response({
                'summary': result,
                'processing_time': result['processing_time']
            }, status=status.HTTP_200_OK)

        except CapabilityRequirement.DoesNotExist:
            return Response({
                'error': 'Requirement not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='results/(?P<requirement_id>[^/.]+)')
    def results(self, request, requirement_id=None):
        """
        Get match results for a requirement.

        GET /api/v1/matching/results/{requirement_id}/
        """
        try:
            service = MatchingService()
            results = service.get_match_results(requirement_id)

            serializer = MatchResultDetailSerializer({
                'requirement_id': requirement_id,
                'results': results,
                'statistics': service.get_statistics(requirement_id)
            })

            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='results/(?P<requirement_id>[^/.]+)/summary')
    def summary(self, request, requirement_id=None):
        """
        Get match summary for a requirement.

        GET /api/v1/matching/results/{requirement_id}/summary/
        """
        try:
            service = MatchingService()
            stats = service.get_statistics(requirement_id)

            serializer = MatchSummarySerializer(stats)
            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='export/(?P<requirement_id>[^/.]+)')
    def export(self, request, requirement_id=None):
        """
        Export match results.

        POST /api/v1/matching/export/{requirement_id}/
        Body: { format: 'excel'|'pdf', include_unmatched: true }
        """
        # TODO: Implement export functionality
        return Response({
            'message': 'Export functionality will be implemented',
            'requirement_id': requirement_id
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class RequirementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CapabilityRequirement model.

    list: List all requirements
    retrieve: Get requirement details
    create: Create a new requirement
    update: Update a requirement
    partial_update: Partially update a requirement
    destroy: Delete a requirement
    """

    queryset = CapabilityRequirement.objects.all()
    filterset_fields = ['status', 'requirement_type']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return RequirementListSerializer
        elif self.action == 'create':
            return CapabilityRequirementCreateSerializer
        return CapabilityRequirementSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a requirement from text.

        POST /api/v1/requirements/
        Body: { title?, requirement_text, requirement_type, created_by? }
        """
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.requirements.services import RequirementService

            title = serializer.validated_data.get('title', '')
            requirement_text = serializer.validated_data.get('requirement_text', '')
            requirement_type = serializer.validated_data.get('requirement_type', 'text')
            created_by = serializer.validated_data.get('created_by', '')

            if requirement_type == 'text':
                requirement = RequirementService.create_text_requirement(
                    title=title,
                    requirement_text=requirement_text,
                    user=created_by
                )
            else:
                return Response({
                    'error': 'Use file upload endpoint for file-type requirements'
                }, status=status.HTTP_400_BAD_REQUEST)

            result_serializer = CapabilityRequirementSerializer(requirement)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Get requirement items.

        GET /api/v1/requirements/{id}/items/
        """
        try:
            requirement = self.get_object()
            items = requirement.items.all().order_by('item_order')

            from apps.matching.serializers import RequirementItemSerializer
            serializer = RequirementItemSerializer(items, many=True)

            return Response({
                'requirement_id': str(requirement.id),
                'items': serializer.data,
                'total_items': items.count()
            })

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Process requirement and generate embeddings.

        POST /api/v1/requirements/{id}/process/
        """
        try:
            requirement = self.get_object()

            # Update status
            requirement.status = 'processing'
            requirement.save()

            # Generate embeddings for items
            from apps.embeddings.services import EmbeddingServiceFactory
            from apps.products.models import FeatureEmbedding

            provider = EmbeddingServiceFactory.get_default_provider()

            for item in requirement.items.all():
                text = item.item_text
                embedding = provider.encode_single(text)

                # Create or update embedding record
                FeatureEmbedding.objects.update_or_create(
                    feature_id=item.id,  # Temporary: using item.id
                    model_name=provider.model_name,
                    defaults={
                        'embedding': embedding,
                        'model_version': provider.model_params.get('model', 'unknown')
                    }
                )

            requirement.status = 'pending'  # Ready for matching
            requirement.save()

            return Response({
                'status': 'success',
                'message': 'Requirement processed successfully'
            })

        except Exception as e:
            requirement.status = 'failed'
            requirement.save()
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
