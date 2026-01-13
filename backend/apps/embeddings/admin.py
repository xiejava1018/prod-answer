"""
Admin configuration for Embedding models.
"""
from django.contrib import admin
from .models import EmbeddingModelConfig


@admin.register(EmbeddingModelConfig)
class EmbeddingModelConfigAdmin(admin.ModelAdmin):
    """Admin interface for EmbeddingModelConfig model."""

    list_display = [
        'model_name',
        'model_type',
        'provider',
        'dimension',
        'is_active',
        'is_default',
        'created_at'
    ]
    list_filter = ['model_type', 'provider', 'is_active', 'is_default', 'created_at']
    search_fields = ['model_name', 'provider']
    ordering = ['-is_default', 'model_name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('model_name', 'model_type', 'provider', 'dimension')
        }),
        ('API Configuration', {
            'fields': ('api_endpoint', 'api_key_encrypted'),
            'classes': ('collapse',)
        }),
        ('Model Parameters', {
            'fields': ('model_params',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
    )

    def save_model(self, request, obj, form, change):
        """Handle is_default validation."""
        if obj.is_default:
            # Remove default from other configs
            EmbeddingModelConfig.objects.filter(is_default=True).update(is_default=False)
        super().save_model(request, obj, form, change)
