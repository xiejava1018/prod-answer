"""
Serializers for Embedding models and services.
"""
from rest_framework import serializers
from .models import EmbeddingModelConfig


class EmbeddingModelConfigSerializer(serializers.ModelSerializer):
    """Serializer for EmbeddingModelConfig model."""

    model_type_display = serializers.CharField(source='get_model_type_display', read_only=True)
    provider_name_display = serializers.CharField(source='get_provider_name_display', read_only=True)
    has_api_key = serializers.SerializerMethodField()

    class Meta:
        model = EmbeddingModelConfig
        fields = [
            'id',
            'model_name',
            'model_type',
            'model_type_display',
            'provider',
            'provider_name',
            'provider_name_display',
            'base_url',
            'api_endpoint',
            'api_key_encrypted',
            'has_api_key',
            'dimension',
            'model_params',
            'is_active',
            'is_default',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key_encrypted': {'write_only': True, 'required': False}
        }

    def get_has_api_key(self, obj):
        """Check if API key is configured."""
        return bool(obj.api_key_encrypted)

    def validate_model_name(self, value):
        """Validate model name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Model name cannot be empty.")
        return value.strip()

    def validate_dimension(self, value):
        """Validate dimension is positive."""
        if value <= 0:
            raise serializers.ValidationError("Dimension must be a positive integer.")
        return value

    def validate(self, data):
        """Validate configuration consistency."""
        model_type = data.get('model_type')

        # OpenAI requires API key
        if model_type == 'openai':
            api_key = data.get('api_key_encrypted') or (
                self.instance.api_key_encrypted if self.instance else None
            )
            if not api_key:
                raise serializers.ValidationError({
                    'api_key_encrypted': 'API key is required for OpenAI models.'
                })

        # OpenAI-compatible requires base_url and API key
        if model_type == 'openai-compatible':
            base_url = data.get('base_url') or (
                getattr(self.instance, 'base_url', None) if self.instance else None
            )
            api_key = data.get('api_key_encrypted') or (
                self.instance.api_key_encrypted if self.instance else None
            )
            if not base_url:
                raise serializers.ValidationError({
                    'base_url': 'Base URL is required for OpenAI-compatible models.'
                })
            if not api_key:
                raise serializers.ValidationError({
                    'api_key_encrypted': 'API key is required for OpenAI-compatible models.'
                })

        return data

    def create(self, validated_data):
        """Create a new embedding configuration."""
        # Handle API key encryption
        api_key = validated_data.pop('api_key_encrypted', None)

        instance = EmbeddingModelConfig(**validated_data)

        if api_key:
            instance.set_api_key(api_key)

        instance.save()
        return instance

    def update(self, instance, validated_data):
        """Update an existing embedding configuration."""
        # Handle API key encryption
        api_key = validated_data.pop('api_key_encrypted', None)

        if api_key is not None:
            instance.set_api_key(api_key)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class EmbeddingTestSerializer(serializers.Serializer):
    """Serializer for testing embedding connection."""

    status = serializers.CharField()
    is_connected = serializers.BooleanField()
    model_info = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class EmbeddingEncodeSerializer(serializers.Serializer):
    """Serializer for encoding texts."""

    texts = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=100
    )
    config_id = serializers.UUIDField(required=False)

    def validate_texts(self, value):
        """Validate texts list."""
        if not all(text.strip() for text in value):
            raise serializers.ValidationError("Texts cannot be empty.")
        return [text.strip() for text in value]


class EmbeddingGenerateSerializer(serializers.Serializer):
    """Serializer for generating embeddings for features."""

    feature_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
        required=False
    )
    product_id = serializers.UUIDField(required=False)
    config_id = serializers.UUIDField(required=False)
    regenerate = serializers.BooleanField(default=False)

    def validate(self, data):
        """Validate that either feature_ids or product_id is provided."""
        feature_ids = data.get('feature_ids')
        product_id = data.get('product_id')

        if not feature_ids and not product_id:
            raise serializers.ValidationError(
                "Either feature_ids or product_id must be provided."
            )

        return data
