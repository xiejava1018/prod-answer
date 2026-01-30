"""
API views for Matching operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import logging

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
from .services import MatchingService, EnhancedMatchingService
import time

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class MatchingViewSet(viewsets.ViewSet):
    """
    ViewSet for matching operations.

    analyze: Perform matching analysis for a requirement
    results: Get match results for a requirement
    summary: Get match summary statistics
    export: Export match results
    """

    # Disable authentication for development
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request):
        """
        Perform matching analysis with optional LLM enhancement.

        POST /api/v1/matching/analyze
        Body: {
            requirement_id,
            threshold?,
            product_ids?,
            limit?,
            enable_llm_analysis?,
            llm_config_id?,
            llm_analysis_mode?
        }
        """
        serializer = MatchAnalyzeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        requirement_id = serializer.validated_data['requirement_id']
        threshold = serializer.validated_data['threshold']
        enable_llm_analysis = serializer.validated_data.get('enable_llm_analysis', False)
        llm_config_id = serializer.validated_data.get('llm_config_id')
        llm_analysis_mode = serializer.validated_data.get('llm_analysis_mode', 'full')

        try:
            # Choose service based on LLM analysis flag
            if enable_llm_analysis:
                service = EnhancedMatchingService(
                    threshold=threshold,
                    llm_config_id=llm_config_id
                )
                logger.info(f"Using enhanced matching with LLM config: {llm_config_id}")
            else:
                service = MatchingService(threshold=threshold)

            start_time = time.time()

            # Perform matching
            if enable_llm_analysis:
                result = service.process_requirement_with_llm(
                    requirement_id=str(requirement_id),
                    llm_config_id=llm_config_id,
                    analysis_mode=llm_analysis_mode,
                    generate_embeddings=True
                )
            else:
                result = service.process_requirement(
                    requirement_id=str(requirement_id),
                    generate_embeddings=True
                )

            processing_time = time.time() - start_time
            result['processing_time'] = round(processing_time, 2)

            # Wrap result for frontend compatibility
            return Response(result, status=status.HTTP_200_OK)

        except CapabilityRequirement.DoesNotExist:
            return Response({
                'error': 'Requirement not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Matching analysis failed: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='results/(?P<requirement_id>[^/.]+)', permission_classes=[AllowAny])
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

    @action(detail=False, methods=['get'], url_path='results/(?P<requirement_id>[^/.]+)/summary', permission_classes=[AllowAny])
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

    @action(detail=False, methods=['post'], url_path='analyze-enhanced', permission_classes=[AllowAny])
    def analyze_enhanced(self, request):
        """
        Perform enhanced matching analysis with LLM (always enabled).

        POST /api/v1/matching/analyze-enhanced/
        Body: {
            requirement_id,
            threshold?,
            llm_config_id?,
            llm_analysis_mode?
        }
        """
        serializer = MatchAnalyzeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        requirement_id = serializer.validated_data['requirement_id']
        threshold = serializer.validated_data['threshold']
        llm_config_id = serializer.validated_data.get('llm_config_id')
        llm_analysis_mode = serializer.validated_data.get('llm_analysis_mode', 'full')

        try:
            # Use EnhancedMatchingService (LLM always enabled)
            service = EnhancedMatchingService(
                threshold=threshold,
                llm_config_id=llm_config_id
            )

            start_time = time.time()

            result = service.process_requirement_with_llm(
                requirement_id=str(requirement_id),
                llm_config_id=llm_config_id,
                analysis_mode=llm_analysis_mode,
                generate_embeddings=True
            )

            processing_time = time.time() - start_time
            result['processing_time'] = round(processing_time, 2)

            return Response(result, status=status.HTTP_200_OK)

        except CapabilityRequirement.DoesNotExist:
            return Response({
                'error': 'Requirement not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Enhanced matching analysis failed: {e}", exc_info=True)
            return Response({
                'error': str(e),
                'llm_analysis_failed': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='batch-analyze-enhanced', permission_classes=[AllowAny])
    def batch_analyze_enhanced(self, request):
        """
        Batch analyze multiple requirements with LLM enhancement.

        POST /api/v1/matching/batch-analyze-enhanced/
        Body: {
            requirement_ids: ["uuid1", "uuid2", ...],
            threshold?,
            llm_config_id?,
            async: true
        }
        """
        requirement_ids = request.data.get('requirement_ids', [])
        threshold = request.data.get('threshold', 0.75)
        llm_config_id = request.data.get('llm_config_id')
        async_mode = request.data.get('async', True)

        if not requirement_ids:
            return Response({
                'error': 'requirement_ids is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate all requirements exist
        from django.shortcuts import get_object_or_404
        for req_id in requirement_ids:
            if not CapabilityRequirement.objects.filter(id=req_id).exists():
                return Response({
                    'error': f'Requirement {req_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)

        try:
            if async_mode:
                # Return task_id for async processing
                # TODO: Implement Celery task in Phase 2
                return Response({
                    'message': 'Async batch processing will be implemented with Celery',
                    'requirement_ids': requirement_ids,
                    'count': len(requirement_ids)
                }, status=status.HTTP_501_NOT_IMPLEMENTED)
            else:
                # Synchronous batch processing
                results = []
                service = EnhancedMatchingService(
                    threshold=threshold,
                    llm_config_id=llm_config_id
                )

                total_start = time.time()
                for req_id in requirement_ids:
                    try:
                        result = service.process_requirement_with_llm(
                            requirement_id=str(req_id),
                            llm_config_id=llm_config_id,
                            analysis_mode='full',
                            generate_embeddings=True
                        )
                        results.append({
                            'requirement_id': str(req_id),
                            'status': 'success',
                            'result': result
                        })
                    except Exception as e:
                        logger.error(f"Failed to process requirement {req_id}: {e}")
                        results.append({
                            'requirement_id': str(req_id),
                            'status': 'failed',
                            'error': str(e)
                        })

                total_time = time.time() - total_start

                return Response({
                    'total_requirements': len(requirement_ids),
                    'successful': len([r for r in results if r['status'] == 'success']),
                    'failed': len([r for r in results if r['status'] == 'failed']),
                    'total_time': round(total_time, 2),
                    'results': results
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Batch analysis failed: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='batch-status/(?P<task_id>[^/.]+)', permission_classes=[AllowAny])
    def batch_status(self, request, task_id=None):
        """
        Get batch processing status.

        GET /api/v1/matching/batch-status/{task_id}/

        TODO: Implement with Celery in Phase 2
        """
        return Response({
            'message': 'Batch status tracking will be implemented with Celery',
            'task_id': task_id
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=False, methods=['post'], url_path='export/(?P<requirement_id>[^/.]+)', permission_classes=[AllowAny])
    def export(self, request, requirement_id=None):
        """
        Export match results.

        POST /api/v1/matching/export/{requirement_id}/
        Body: { format: 'excel'|'pdf', include_unmatched: true }
        """
        try:
            # Get export parameters
            export_format = request.data.get('format', 'excel')
            include_unmatched = request.data.get('include_unmatched', False)

            # Validate format
            if export_format not in ['excel', 'pdf']:
                return Response({
                    'error': 'Unsupported format. Use excel or pdf'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Export results
            service = MatchingService()
            file_content = service.export_results(
                requirement_id=requirement_id,
                format=export_format,
                include_unmatched=include_unmatched
            )

            # Set appropriate content type and headers
            if export_format == 'excel':
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = f'match_results_{requirement_id}.xlsx'
            elif export_format == 'pdf':
                content_type = 'application/pdf'
                filename = f'match_results_{requirement_id}.pdf'

            # Return file response
            from django.http import HttpResponse
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
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

    # Disable authentication for development
    authentication_classes = []
    permission_classes = [AllowAny]

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

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
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

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
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
