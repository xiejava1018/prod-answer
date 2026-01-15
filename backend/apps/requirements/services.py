"""
Requirements service for file processing and requirement management.
"""
import os
import uuid
from typing import List, Dict
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Q
from apps.matching.models import CapabilityRequirement, RequirementItem
from apps.requirements.parsers.excel_parser import ExcelParser
from apps.requirements.parsers.csv_parser import CSVParser
from apps.requirements.parsers.word_parser import WordParser


class FileParserService:
    """
    Service for parsing uploaded files and extracting requirements.
    """

    # Supported file types and their parsers
    PARSERS = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ExcelParser,
        'application/vnd.ms-excel': ExcelParser,
        'text/csv': CSVParser,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': WordParser,
    }

    # File extensions for type detection
    EXTENSION_MAP = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.csv': 'text/csv',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    def __init__(self, upload_dir: str = None):
        """
        Initialize the file parser service.

        Args:
            upload_dir: Directory to store uploaded files (default: media/uploads/requirements)
        """
        if upload_dir is None:
            from django.conf import settings
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'requirements')

        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def get_upload_path(self, filename: str) -> str:
        """
        Generate a unique upload path for a file.

        Args:
            filename: Original filename

        Returns:
            Full path where file will be saved
        """
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        return os.path.join(self.upload_dir, unique_filename)

    def save_uploaded_file(self, file: UploadedFile) -> tuple:
        """
        Save an uploaded file to disk.

        Args:
            file: UploadedFile object

        Returns:
            Tuple of (file_path, unique_filename)
        """
        file_path = self.get_upload_path(file.name)

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return file_path, os.path.basename(file_path)

    def detect_file_type(self, file_path: str, original_filename: str = None) -> str:
        """
        Detect file type from extension.

        Args:
            file_path: Path to the file
            original_filename: Original filename (optional)

        Returns:
            MIME type string
        """
        # Try original filename first
        if original_filename:
            ext = os.path.splitext(original_filename)[1].lower()
            if ext in self.EXTENSION_MAP:
                return self.EXTENSION_MAP[ext]

        # Try file path
        ext = os.path.splitext(file_path)[1].lower()
        return self.EXTENSION_MAP.get(ext, 'application/octet-stream')

    def parse_file(self, file_path: str, file_type: str = None) -> List[str]:
        """
        Parse a file and extract requirements.

        Args:
            file_path: Path to the file
            file_type: MIME type (will auto-detect if not provided)

        Returns:
            List of requirement texts

        Raises:
            ValueError: If file type is not supported
        """
        # Auto-detect file type if not provided
        if file_type is None:
            file_type = self.detect_file_type(file_path)

        # Get parser for this file type
        parser_class = self.PARSERS.get(file_type)

        if not parser_class:
            supported_types = list(self.PARSERS.keys())
            raise ValueError(
                f"Unsupported file type: {file_type}. "
                f"Supported types: {supported_types}"
            )

        # Parse file
        parser = parser_class()
        parsed_data = parser.parse(file_path)
        requirements = parser.extract_requirements(parsed_data)

        return requirements

    def process_uploaded_file(
        self,
        file: UploadedFile,
        user: str = None,
        auto_create_requirement: bool = True
    ) -> CapabilityRequirement:
        """
        Process an uploaded file and create requirement records.

        Args:
            file: UploadedFile object
            user: Username (optional)
            auto_create_requirement: Whether to automatically create a CapabilityRequirement

        Returns:
            CapabilityRequirement object
        """
        # Save file
        file_path, unique_filename = self.save_uploaded_file(file)

        # Detect file type
        file_type = self.detect_file_type(file_path, file.name)

        # Parse file
        try:
            requirements = self.parse_file(file_path, file_type)
        except Exception as e:
            # Clean up file if parsing fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ValueError(f"Failed to parse file: {str(e)}")

        if not requirements:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ValueError("No requirements found in file")

        # Create requirement record
        if auto_create_requirement:
            # 从文件名生成默认标题（去除扩展名）
            default_title = os.path.splitext(file.name)[0] if file.name else 'Uploaded File'

            requirement = CapabilityRequirement.objects.create(
                session_id=uuid.uuid4(),
                title=default_title,
                requirement_type='file',
                source_file_name=file.name,
                status='pending',
                created_by=user
            )

            # Create requirement items
            items = [
                RequirementItem(
                    requirement=requirement,
                    item_text=req_text,
                    item_order=index
                )
                for index, req_text in enumerate(requirements)
            ]
            RequirementItem.objects.bulk_create(items)

            return requirement
        else:
            # Just return the requirements list
            return requirements


class RequirementService:
    """
    Service for managing requirements.
    """

    @staticmethod
    def create_text_requirement(title: str = '', requirement_text: str = '', user: str = None) -> CapabilityRequirement:
        """
        Create a requirement from text input.

        Args:
            title: Requirement name/title (optional)
            requirement_text: Requirement text (can contain multiple lines)
            user: Username (optional)

        Returns:
            CapabilityRequirement object
        """
        # Split text into lines and filter empty ones
        lines = [line.strip() for line in requirement_text.split('\n') if line.strip()]

        if not lines:
            raise ValueError("Requirement text cannot be empty")

        # Create requirement record
        requirement = CapabilityRequirement.objects.create(
            title=title,
            session_id=uuid.uuid4(),
            requirement_text=requirement_text,
            requirement_type='text',
            status='pending',
            created_by=user
        )

        # Create requirement items (one per line)
        items = [
            RequirementItem(
                requirement=requirement,
                item_text=line,
                item_order=index
            )
            for index, line in enumerate(lines)
        ]
        RequirementItem.objects.bulk_create(items)

        return requirement

    @staticmethod
    def get_requirement_with_items(requirement_id: str) -> Dict:
        """
        Get requirement with all items.

        Args:
            requirement_id: UUID of the requirement

        Returns:
            Dictionary with requirement and items
        """
        try:
            requirement = CapabilityRequirement.objects.get(id=requirement_id)
            items = requirement.items.all().order_by('item_order')

            return {
                'requirement': requirement,
                'items': items,
                'total_items': items.count(),
            }
        except CapabilityRequirement.DoesNotExist:
            raise ValueError(f"Requirement not found: {requirement_id}")

    @staticmethod
    def search_requirements(query: str) -> List[CapabilityRequirement]:
        """
        Search requirements by text.

        Args:
            query: Search query

        Returns:
            List of matching requirements
        """
        return CapabilityRequirement.objects.filter(
            Q(requirement_text__icontains=query) |
            Q(source_file_name__icontains=query)
        ).order_by('-created_at')
