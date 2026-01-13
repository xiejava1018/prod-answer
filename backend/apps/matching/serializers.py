"""
Serializers for Matching models.
"""
from rest_framework import serializers
from .models import CapabilityRequirement, RequirementItem, MatchRecord


class RequirementItemSerializer(serializers.ModelSerializer):
    """Serializer for RequirementItem model."""

    class Meta:
        model = RequirementItem
        fields = [
            'id',
            'item_text',
            'item_order',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CapabilityRequirementSerializer(serializers.ModelSerializer):
    """Serializer for CapabilityRequirement model."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requirement_type_display = serializers.CharField(source='get_requirement_type_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    items = RequirementItemSerializer(many=True, read_only=True)

    class Meta:
        model = CapabilityRequirement
        fields = [
            'id',
            'title',
            'session_id',
            'requirement_text',
            'requirement_type',
            'requirement_type_display',
            'source_file_name',
            'status',
            'status_display',
            'created_by',
            'items_count',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']

    def get_items_count(self, obj):
        """Get the count of requirement items."""
        return obj.items.count()


class CapabilityRequirementCreateSerializer(serializers.Serializer):
    """Serializer for creating requirements from text."""

    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    requirement_text = serializers.CharField(required=False, allow_blank=True)
    requirement_type = serializers.ChoiceField(
        choices=['text', 'file'],
        default='text'
    )
    created_by = serializers.CharField(required=False, allow_blank=True)

    def validate_requirement_text(self, value):
        """Validate requirement text for text-type requirements."""
        if self.initial_data.get('requirement_type') == 'text':
            if not value or not value.strip():
                raise serializers.ValidationError(
                    "Requirement text cannot be empty for text-type requirements."
                )
        return value


class MatchRecordSerializer(serializers.ModelSerializer):
    """Serializer for MatchRecord model."""

    match_status_display = serializers.CharField(source='get_match_status_display', read_only=True)
    requirement_item_text = serializers.CharField(source='requirement_item.item_text', read_only=True)
    feature_name = serializers.CharField(source='feature.feature_name', read_only=True)
    feature_description = serializers.CharField(source='feature.description', read_only=True)
    product_name = serializers.CharField(source='feature.product.name', read_only=True)

    class Meta:
        model = MatchRecord
        fields = [
            'id',
            'requirement',
            'requirement_item',
            'requirement_item_text',
            'feature',
            'feature_name',
            'feature_description',
            'product_name',
            'similarity_score',
            'match_status',
            'match_status_display',
            'threshold_used',
            'rank',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class MatchAnalyzeSerializer(serializers.Serializer):
    """Serializer for match analysis request."""

    requirement_id = serializers.UUIDField()
    threshold = serializers.FloatField(default=0.75, min_value=0.0, max_value=1.0)
    product_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    limit = serializers.IntegerField(default=5, min_value=1, max_value=20)

    def validate_requirement_id(self, value):
        """Validate that requirement exists."""
        if not CapabilityRequirement.objects.filter(id=value).exists():
            raise serializers.ValidationError("Requirement not found.")
        return value


class MatchResultSerializer(serializers.Serializer):
    """Serializer for match analysis results."""

    requirement_id = serializers.UUIDField()
    status = serializers.CharField()
    summary = serializers.DictField()
    processing_time = serializers.FloatField()


class MatchResultDetailSerializer(serializers.Serializer):
    """Serializer for detailed match results."""

    requirement_id = serializers.UUIDField()
    results = serializers.DictField()
    statistics = serializers.DictField()


class MatchSummarySerializer(serializers.Serializer):
    """Serializer for match summary."""

    total_items = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    matched = serializers.IntegerField()
    partial_matched = serializers.IntegerField()
    unmatched = serializers.IntegerField()
    avg_similarity = serializers.FloatField()
    max_similarity = serializers.FloatField()
    min_similarity = serializers.FloatField()


class RequirementListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for requirement list views."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = CapabilityRequirement
        fields = [
            'id',
            'title',
            'session_id',
            'requirement_type',
            'source_file_name',
            'status',
            'status_display',
            'created_by',
            'items_count',
            'created_at',
        ]

    def get_items_count(self, obj):
        """Get the count of requirement items."""
        return obj.items.count()
