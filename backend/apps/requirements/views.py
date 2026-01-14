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

    create: Upload and parse a requirement file
    parse_text: Parse text requirements
    supported_formats: Get list of supported file formats
    """

    parser_classes = (MultiPartParser, FormParser)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        Upload a requirement file and parse it.

        POST /api/v1/requirements/upload/
        Form: { file, created_by?, title? }
        """
        serializer = RequirementUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        created_by = serializer.validated_data.get('created_by', '')
        title = serializer.validated_data.get('title', '')

        try:
            service = FileParserService()
            requirement = service.process_uploaded_file(
                file=uploaded_file,
                user=created_by,
                auto_create_requirement=True
            )

            # Update title if provided
            if title:
                requirement.title = title
                requirement.save()

            from apps.matching.serializers import CapabilityRequirementSerializer
            result_serializer = CapabilityRequirementSerializer(requirement)

            return Response({
                'status': 'success',
                'message': 'File uploaded and parsed successfully',
                'requirement': result_serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            error_msg = str(e)
            # Provide more detailed error information
            if 'Unsupported file type' in error_msg:
                error_msg = (
                    f"{error_msg}\n\n"
                    f"Upload file name: {uploaded_file.name}\n"
                    f"Supported formats: Excel (.xlsx, .xls), CSV (.csv), Word (.docx)"
                )
            elif 'No requirements found' in error_msg:
                error_msg = (
                    f"{error_msg}\n\n"
                    f"Upload file: {uploaded_file.name}\n"
                    f"Please ensure the file contains valid requirement data.\n"
                    f"For Excel/CSV files, ensure there are columns with headers like "
                    f"'requirement', 'feature', 'description', 'content', or 'name'."
                )
            elif 'Failed to parse file' in error_msg:
                error_msg = (
                    f"{error_msg}\n\n"
                    f"Upload file: {uploaded_file.name}\n"
                    f"The file may be corrupted or in an invalid format."
                )

            return Response({
                'error': error_msg
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
        Body: { requirement_text, created_by?, title? }
        """
        requirement_text = request.data.get('requirement_text', '')
        created_by = request.data.get('created_by', '')
        title = request.data.get('title', '')

        if not requirement_text or not requirement_text.strip():
            return Response({
                'error': 'Requirement text cannot be empty'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            requirement = RequirementService.create_text_requirement(
                title=title,
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
