"""
Serializers for Requirements app.
"""
from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from .models import CapabilityRequirement, RequirementItem
from apps.matching.serializers import CapabilityRequirementSerializer


class RequirementUploadSerializer(serializers.Serializer):
    """Serializer for requirement file upload."""

    file = serializers.FileField()
    created_by = serializers.CharField(required=False, allow_blank=True)

    def validate_file(self, value):
        """Validate uploaded file."""
        if not value:
            raise serializers.ValidationError("File is required.")

        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB.")

        # Check file extension
        import os
        ext = os.path.splitext(value.name)[1].lower()
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.docx']

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
            )

        return value


class RequirementItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating requirement items."""

    class Meta:
        model = RequirementItem
        fields = ['item_text', 'item_order']


class RequirementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating requirements."""

    items = RequirementItemCreateSerializer(many=True)

    class Meta:
        model = CapabilityRequirement
        fields = [
            'session_id',
            'requirement_text',
            'requirement_type',
            'source_file_name',
            'status',
            'created_by',
            'items',
        ]
        read_only_fields = ['session_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create requirement with items."""
        items_data = validated_data.pop('items')
        requirement = CapabilityRequirement.objects.create(**validated_data)

        # Create items
        items = [
            RequirementItem(requirement=requirement, **item_data)
            for item_data in items_data
        ]
        RequirementItem.objects.bulk_create(items)

        return requirement


class RequirementListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for requirement lists."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = CapabilityRequirement
        fields = [
            'id',
            'session_id',
            'requirement_type',
            'source_file_name',
            'status',
            'status_display',
            'items_count',
            'created_by',
            'created_at',
        ]

    def get_items_count(self, obj):
        """Get items count."""
        return obj.items.count()


class RequirementDetailSerializer(CapabilityRequirementSerializer):
    """Detailed serializer for requirement."""

    matches_summary = serializers.SerializerMethodField()

    class Meta(CapabilityRequirementSerializer.Meta):
        fields = CapabilityRequirementSerializer.Meta.fields + ['matches_summary']

    def get_matches_summary(self, obj):
        """Get matches summary."""
        from apps.matching.models import MatchRecord
        from django.db.models import Count, Avg

        summary = MatchRecord.objects.filter(requirement=obj).aggregate(
            total_matches=Count('id'),
            avg_similarity=Avg('similarity_score')
        )

        return {
            'total_matches': summary['total_matches'] or 0,
            'avg_similarity': float(summary['avg_similarity']) if summary['avg_similarity'] else 0.0,
        }
