"""
Admin configuration for Product and Feature models.
"""
from django.contrib import admin
from .models import Product, Feature, FeatureEmbedding


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model."""

    list_display = [
        'name',
        'version',
        'category',
        'vendor',
        'is_active',
        'features_count',
        'created_at'
    ]
    list_filter = ['category', 'vendor', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'vendor']
    ordering = ['-created_at']

    def features_count(self, obj):
        """Display count of features."""
        return obj.features.filter(is_active=True).count()
    features_count.short_description = 'Features'


class FeatureEmbeddingInline(admin.TabularInline):
    """Inline admin for feature embeddings."""

    model = FeatureEmbedding
    extra = 0
    readonly_fields = ['model_name', 'model_version', 'created_at']
    can_delete = False


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """Admin interface for Feature model."""

    list_display = [
        'feature_name',
        'product',
        'category',
        'subcategory',
        'importance_level',
        'is_active',
        'has_embedding',
        'created_at'
    ]
    list_filter = ['category', 'subcategory', 'importance_level', 'is_active', 'created_at']
    search_fields = ['feature_name', 'description', 'feature_code']
    ordering = ['product', 'category', 'subcategory', 'feature_name']
    inlines = [FeatureEmbeddingInline]

    def has_embedding(self, obj):
        """Check if feature has embedding."""
        return obj.embeddings.exists()
    has_embedding.boolean = True
    has_embedding.short_description = 'Has Embedding'


@admin.register(FeatureEmbedding)
class FeatureEmbeddingAdmin(admin.ModelAdmin):
    """Admin interface for FeatureEmbedding model."""

    list_display = [
        'feature',
        'model_name',
        'model_version',
        'created_at'
    ]
    list_filter = ['model_name', 'created_at']
    search_fields = ['feature__feature_name', 'model_name']
    readonly_fields = ['feature', 'model_name', 'embedding', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        """Disable manual adding through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make embeddings read-only."""
        return False
