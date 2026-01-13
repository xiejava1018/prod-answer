"""
API views for Requirements management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import CapabilityRequirement
from .serializers import RequirementUploadSerializer
from .services import FileParserService, RequirementService


class RequirementUploadViewSet(viewsets.ViewSet):
    """
    ViewSet for requirement file uploads.

    upload: Upload and parse a requirement file
    """

    parser_classes = (MultiPartParser, FormParser)

    def create(self, request):
        """
        Upload a requirement file and parse it.

        POST /api/v1/requirements/upload/
        Form: { file, created_by? }
        """
        serializer = RequirementUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        created_by = serializer.validated_data.get('created_by', '')

        try:
            service = FileParserService()
            requirement = service.process_uploaded_file(
                file=uploaded_file,
                user=created_by,
                auto_create_requirement=True
            )

            from apps.matching.serializers import CapabilityRequirementSerializer
            result_serializer = CapabilityRequirementSerializer(requirement)

            return Response({
                'status': 'success',
                'message': 'File uploaded and parsed successfully',
                'requirement': result_serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': f'Failed to process file: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def parse_text(self, request):
        """
        Parse text requirements.

        POST /api/v1/requirements/parse_text/
        Body: { requirement_text, created_by? }
        """
        requirement_text = request.data.get('requirement_text', '')
        created_by = request.data.get('created_by', '')

        if not requirement_text or not requirement_text.strip():
            return Response({
                'error': 'Requirement text cannot be empty'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            requirement = RequirementService.create_text_requirement(
                requirement_text=requirement_text,
                user=created_by
            )

            from apps.matching.serializers import CapabilityRequirementSerializer
            serializer = CapabilityRequirementSerializer(requirement)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def supported_formats(self, request):
        """
        Get list of supported file formats.

        GET /api/v1/requirements/supported_formats/
        """
        formats = {
            'excel': {
                'extensions': ['.xlsx', '.xls'],
                'mime_types': [
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.ms-excel'
                ],
                'description': 'Microsoft Excel files'
            },
            'csv': {
                'extensions': ['.csv'],
                'mime_types': ['text/csv'],
                'description': 'Comma-separated values'
            },
            'word': {
                'extensions': ['.docx'],
                'mime_types': [
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ],
                'description': 'Microsoft Word documents'
            }
        }

        return Response({
            'supported_formats': formats,
            'max_file_size': '10MB'
        })
