"""
Serializers for LLM models and services.
"""
from rest_framework import serializers
from .models import LLMModelConfig, LLMAnalysisResult


class LLMModelConfigSerializer(serializers.ModelSerializer):
    """Serializer for LLMModelConfig model."""

    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    has_api_key = serializers.SerializerMethodField()
    api_key_masked = serializers.SerializerMethodField()

    class Meta:
        model = LLMModelConfig
        fields = [
            'id',
            'provider',
            'provider_display',
            'model_name',
            'base_url',
            'api_key_encrypted',
            'has_api_key',
            'api_key_masked',
            'max_tokens',
            'temperature',
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

    def get_api_key_masked(self, obj):
        """Get masked API key (show only last 4 characters)."""
        if not obj.api_key_encrypted:
            return None

        try:
            api_key = obj.get_api_key()
            if len(api_key) <= 4:
                return '****'
            return '****' + api_key[-4:]
        except Exception:
            # If decryption fails, still show masked version
            return '****'

    def validate_model_name(self, value):
        """Validate model name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Model name cannot be empty.")
        return value.strip()

    def validate_temperature(self, value):
        """Validate temperature range."""
        if not 0 <= value <= 2:
            raise serializers.ValidationError("Temperature must be between 0.0 and 2.0.")
        return value

    def validate_max_tokens(self, value):
        """Validate max_tokens is positive."""
        if value <= 0:
            raise serializers.ValidationError("Max tokens must be a positive integer.")
        return value

    def validate_provider(self, value):
        """Validate provider is supported."""
        from .services import LLMProviderFactory
        available_providers = LLMProviderFactory.get_available_providers()

        if value not in available_providers:
            raise serializers.ValidationError(
                f"Unsupported provider: {value}. "
                f"Available providers: {', '.join(available_providers)}"
            )
        return value

    def validate(self, data):
        """Validate configuration consistency."""
        provider = data.get('provider')

        # If updating, get provider from instance if not in data
        if not provider and self.instance:
            provider = self.instance.provider

        # API key is required for all providers
        api_key = data.get('api_key_encrypted') or (
            self.instance.api_key_encrypted if self.instance else None
        )

        if not api_key:
            raise serializers.ValidationError({
                'api_key_encrypted': 'API key is required.'
            })

        # Validate temperature
        temperature = data.get('temperature')
        if temperature is not None:
            if not 0 <= temperature <= 2:
                raise serializers.ValidationError({
                    'temperature': 'Temperature must be between 0.0 and 2.0.'
                })

        return data

    def create(self, validated_data):
        """Create a new LLM configuration."""
        # Handle API key encryption
        api_key = validated_data.pop('api_key_encrypted', None)

        instance = LLMModelConfig(**validated_data)

        if api_key:
            instance.set_api_key(api_key)

        instance.save()
        return instance

    def update(self, instance, validated_data):
        """Update an existing LLM configuration."""
        # Handle API key encryption
        api_key = validated_data.pop('api_key_encrypted', None)

        if api_key is not None:
            instance.set_api_key(api_key)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class LLMTestSerializer(serializers.Serializer):
    """Serializer for testing LLM connection."""

    status = serializers.CharField()
    is_connected = serializers.BooleanField()
    response_time_ms = serializers.IntegerField(required=False)
    model_info = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class LLMAnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for LLMAnalysisResult model."""

    requirement_text = serializers.CharField(source='requirement_item.item_text', read_only=True)
    feature_name = serializers.CharField(source='feature.feature_name', read_only=True)
    provider_display = serializers.SerializerMethodField()

    class Meta:
        model = LLMAnalysisResult
        fields = [
            'id',
            'requirement_item',
            'requirement_text',
            'feature',
            'feature_name',
            'match_reason',
            'keywords_from_requirement',
            'keywords_from_feature',
            'is_valid_match',
            'confidence_score',
            'llm_provider',
            'provider_display',
            'llm_model',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens',
            'analysis_metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_provider_display(self, obj):
        """Get provider display name."""
        provider_map = {
            'openai': 'OpenAI',
            'zhipuai': '智谱AI',
            'qwen': '通义千问',
        }
        return provider_map.get(obj.llm_provider, obj.llm_provider)
