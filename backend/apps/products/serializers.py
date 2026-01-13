"""
Serializers for Product and Feature models.
"""
from rest_framework import serializers
from .models import Product, Feature, FeatureEmbedding


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    features_count = serializers.SerializerMethodField()
    subsystem_type_display = serializers.CharField(source='get_subsystem_type_display', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'version',
            'description',
            'vendor',
            'category',
            'subsystem_type',
            'subsystem_type_display',
            'spec_metadata',
            'is_active',
            'features_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_features_count(self, obj):
        """Get the count of features for this product."""
        return obj.features.filter(is_active=True).count()

    def validate_name(self, value):
        """Validate product name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Product name cannot be empty.")
        return value.strip()


class ProductDetailSerializer(ProductSerializer):
    """Detailed serializer for Product with features."""

    features = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['features']

    def get_features(self, obj):
        """Get all active features for this product."""
        features = obj.features.filter(is_active=True)
        return FeatureSerializer(features, many=True).data


class FeatureSerializer(serializers.ModelSerializer):
    """Serializer for Feature model."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    has_embedding = serializers.SerializerMethodField()
    indicator_type_display = serializers.CharField(source='get_indicator_type_display', read_only=True)

    class Meta:
        model = Feature
        fields = [
            'id',
            'product',
            'product_name',
            'feature_code',
            'feature_name',
            'description',
            'category',
            'subcategory',
            'level1_function',
            'level2_function',
            'indicator_type',
            'indicator_type_display',
            'importance_level',
            'metadata',
            'is_active',
            'has_embedding',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'product': {'required': False}  # Will be set in the view
        }

    def get_has_embedding(self, obj):
        """Check if feature has an embedding."""
        return obj.embeddings.exists()

    def validate_feature_name(self, value):
        """Validate feature name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Feature name cannot be empty.")
        return value.strip()

    def validate_description(self, value):
        """Validate feature description."""
        if not value or not value.strip():
            raise serializers.ValidationError("Feature description cannot be empty.")
        return value.strip()

    def validate_importance_level(self, value):
        """Validate importance level is between 1 and 10."""
        if not 1 <= value <= 10:
            raise serializers.ValidationError("Importance level must be between 1 and 10.")
        return value

    def validate_feature_code(self, value):
        """Convert empty string to None for feature_code."""
        if value == '':
            return None
        return value


class FeatureEmbeddingSerializer(serializers.ModelSerializer):
    """Serializer for FeatureEmbedding model."""

    feature_name = serializers.CharField(source='feature.feature_name', read_only=True)
    feature_description = serializers.CharField(source='feature.description', read_only=True)

    class Meta:
        model = FeatureEmbedding
        fields = [
            'id',
            'feature',
            'feature_name',
            'feature_description',
            'embedding',
            'model_name',
            'model_version',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'embedding': {'write_only': True}  # Don't expose full embeddings in API responses
        }


class FeatureListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for feature lists."""

    has_embedding = serializers.SerializerMethodField()
    indicator_type_display = serializers.CharField(source='get_indicator_type_display', read_only=True)

    class Meta:
        model = Feature
        fields = [
            'id',
            'feature_code',
            'feature_name',
            'description',
            'category',
            'subcategory',
            'level1_function',
            'level2_function',
            'indicator_type',
            'indicator_type_display',
            'importance_level',
            'is_active',
            'has_embedding',
        ]

    def get_has_embedding(self, obj):
        """Check if feature has an embedding."""
        return obj.embeddings.exists()


class BatchFeatureSerializer(serializers.Serializer):
    """Serializer for batch feature creation."""

    product_id = serializers.UUIDField()
    features = FeatureSerializer(many=True)

    def validate_product_id(self, value):
        """Validate that product exists."""
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found.")
        return value

    def create(self, validated_data):
        """Create multiple features for a product."""
        product_id = validated_data['product_id']
        features_data = validated_data['features']

        product = Product.objects.get(id=product_id)
        features = []

        for feature_data in features_data:
            feature_data['product'] = product
            features.append(Feature(**feature_data))

        Feature.objects.bulk_create(features)
        return features


class FeatureUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating features."""

    class Meta:
        model = Feature
        fields = [
            'feature_code',
            'feature_name',
            'description',
            'category',
            'subcategory',
            'level1_function',
            'level2_function',
            'indicator_type',
            'importance_level',
            'metadata',
            'is_active',
        ]
