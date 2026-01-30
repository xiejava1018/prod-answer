"""
Admin configuration for LLM models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import LLMModelConfig, LLMAnalysisResult, LLMCache, LLMUsageLog


@admin.register(LLMModelConfig)
class LLMModelConfigAdmin(admin.ModelAdmin):
    """Admin interface for LLMModelConfig model."""

    list_display = [
        'provider',
        'model_name',
        'is_active',
        'is_default',
        'max_tokens',
        'temperature',
        'created_at'
    ]
    list_filter = ['provider', 'is_active', 'is_default', 'created_at']
    search_fields = ['provider', 'model_name', 'base_url']
    ordering = ['-is_default', 'provider', 'model_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('provider', 'model_name', 'base_url')
        }),
        ('认证配置', {
            'fields': ('api_key_encrypted',)
        }),
        ('模型参数', {
            'fields': ('max_tokens', 'temperature', 'model_params')
        }),
        ('状态', {
            'fields': ('is_active', 'is_default')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_configs', 'deactivate_configs', 'set_as_default']

    def activate_configs(self, request, queryset):
        """Activate selected configurations."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} 个配置已激活')
    activate_configs.short_description = '激活选中的配置'

    def deactivate_configs(self, request, queryset):
        """Deactivate selected configurations."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} 个配置已停用')
    deactivate_configs.short_description = '停用选中的配置'

    def set_as_default(self, request, queryset):
        """Set selected configuration as default."""
        if queryset.count() > 1:
            self.message_user(request, '只能选择一个配置作为默认配置', level='error')
            return

        config = queryset.first()
        # Unset other defaults for the same provider
        LLMModelConfig.objects.filter(
            provider=config.provider,
            is_default=True
        ).exclude(id=config.id).update(is_default=False)
        # Set this as default
        config.is_default = True
        config.save()
        self.message_user(request, f'{config.model_name} 已设置为 {config.provider} 的默认配置')
    set_as_default.short_description = '设置为默认配置'


class LLMAnalysisResultInline(admin.TabularInline):
    """Inline admin for LLM analysis results."""

    model = LLMAnalysisResult
    extra = 0
    readonly_fields = [
        'feature',
        'is_valid_match',
        'confidence_score',
        'llm_provider',
        'llm_model',
        'match_reason_preview',
        'total_tokens'
    ]
    can_delete = False

    def match_reason_preview(self, obj):
        """Display preview of match reason."""
        if obj.match_reason:
            return obj.match_reason[:100] + '...' if len(obj.match_reason) > 100 else obj.match_reason
        return '-'
    match_reason_preview.short_description = '匹配原因'


@admin.register(LLMAnalysisResult)
class LLMAnalysisResultAdmin(admin.ModelAdmin):
    """Admin interface for LLMAnalysisResult model."""

    list_display = [
        'requirement_item_preview',
        'feature_name',
        'product_name',
        'is_valid_match',
        'confidence_score',
        'llm_provider',
        'llm_model',
        'total_tokens',
        'created_at'
    ]
    list_filter = [
        'is_valid_match',
        'llm_provider',
        'llm_model',
        'created_at'
    ]
    search_fields = [
        'requirement_item__item_text',
        'feature__feature_name',
        'feature__product__name',
        'match_reason'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'requirement_item',
        'feature',
        'match_reason',
        'keywords_from_requirement',
        'keywords_from_feature',
        'is_valid_match',
        'confidence_score',
        'llm_provider',
        'llm_model',
        'prompt_tokens',
        'completion_tokens',
        'total_tokens',
        'analysis_metadata',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('匹配对象', {
            'fields': ('requirement_item', 'feature')
        }),
        ('分析结果', {
            'fields': (
                'is_valid_match',
                'confidence_score',
                'match_reason',
                'keywords_from_requirement',
                'keywords_from_feature'
            )
        }),
        ('LLM 信息', {
            'fields': (
                'llm_provider',
                'llm_model',
                'prompt_tokens',
                'completion_tokens',
                'total_tokens'
            )
        }),
        ('元数据', {
            'fields': ('analysis_metadata',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def requirement_item_preview(self, obj):
        """Display preview of requirement item."""
        text = obj.requirement_item.item_text
        return text[:30] + '...' if len(text) > 30 else text
    requirement_item_preview.short_description = '需求项'

    def feature_name(self, obj):
        """Display feature name."""
        return obj.feature.feature_name
    feature_name.short_description = '功能特性'

    def product_name(self, obj):
        """Display product name."""
        return obj.feature.product.name
    product_name.short_description = '产品'

    def has_add_permission(self, request):
        """Disable manual adding through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make analysis results read-only."""
        return False

    def get_queryset(self, request):
        """Annotate queryset with additional info."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'requirement_item__requirement',
            'feature__product'
        )


@admin.register(LLMCache)
class LLMCacheAdmin(admin.ModelAdmin):
    """Admin interface for LLMCache model."""

    list_display = [
        'cache_key_preview',
        'requirement_text_preview',
        'llm_provider',
        'llm_model',
        'hit_count',
        'expires_at',
        'is_expired',
        'created_at'
    ]
    list_filter = ['llm_provider', 'llm_model', 'created_at', 'expires_at']
    search_fields = ['cache_key', 'requirement_text']
    ordering = ['-hit_count', '-created_at']
    readonly_fields = [
        'cache_key',
        'requirement_text',
        'feature_ids',
        'response_json',
        'hit_count',
        'expires_at',
        'llm_provider',
        'llm_model',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('缓存键', {
            'fields': ('cache_key', 'requirement_text', 'feature_ids')
        }),
        ('LLM 响应', {
            'fields': ('response_json', 'llm_provider', 'llm_model')
        }),
        ('缓存统计', {
            'fields': ('hit_count', 'expires_at')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['clear_expired_cache', 'clear_all_cache', 'increment_hit_counts']

    def cache_key_preview(self, obj):
        """Display preview of cache key."""
        return obj.cache_key[:20] + '...'
    cache_key_preview.short_description = '缓存键'

    def requirement_text_preview(self, obj):
        """Display preview of requirement text."""
        text = obj.requirement_text
        return text[:50] + '...' if len(text) > 50 else text
    requirement_text_preview.short_description = '需求文本'

    def is_expired(self, obj):
        """Display whether cache entry is expired."""
        from django.utils import timezone
        expired = obj.expires_at < timezone.now()
        color = 'red' if expired else 'green'
        status = '已过期' if expired else '有效'
        return format_html('<span style="color: {};">{}</span>', color, status)
    is_expired.short_description = '状态'

    def clear_expired_cache(self, request, queryset):
        """Clear expired cache entries."""
        from django.utils import timezone
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f'已清除 {count} 个过期缓存条目')
    clear_expired_cache.short_description = '清除过期缓存'

    def clear_all_cache(self, request, queryset):
        """Clear all selected cache entries."""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'已清除 {count} 个缓存条目')
    clear_all_cache.short_description = '清除选中缓存'

    def increment_hit_counts(self, request, queryset):
        """Increment hit counts for selected entries (for testing)."""
        for entry in queryset:
            entry.increment_hit_count()
        self.message_user(request, f'已增加 {queryset.count()} 个条目的命中次数')
    increment_hit_counts.short_description = '增加命中次数'

    def has_add_permission(self, request):
        """Disable manual adding through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make cache entries read-only."""
        return False


@admin.register(LLMUsageLog)
class LLMUsageLogAdmin(admin.ModelAdmin):
    """Admin interface for LLMUsageLog model."""

    list_display = [
        'REQUEST_ID_preview',
        'timestamp',
        'provider',
        'model',
        'request_type',
        'total_tokens',
        'cost_usd',
        'status',
        'cache_hit',
        'response_time_ms'
    ]
    list_filter = [
        'provider',
        'model',
        'request_type',
        'status',
        'cache_hit',
        'timestamp'
    ]
    search_fields = [
        'REQUEST_ID',
        'requirement_id',
        'error_message'
    ]
    ordering = ['-timestamp']
    readonly_fields = [
        'REQUEST_ID',
        'timestamp',
        'provider',
        'model',
        'prompt_tokens',
        'completion_tokens',
        'total_tokens',
        'cost_usd',
        'request_type',
        'requirement_id',
        'feature_count',
        'cache_hit',
        'response_time_ms',
        'status',
        'error_message',
        'metadata',
        'created_at'
    ]

    fieldsets = (
        ('请求信息', {
            'fields': ('REQUEST_ID', 'timestamp', 'request_type', 'requirement_id')
        }),
        ('模型信息', {
            'fields': ('provider', 'model')
        }),
        ('Token 使用', {
            'fields': ('prompt_tokens', 'completion_tokens', 'total_tokens')
        }),
        ('成本信息', {
            'fields': ('cost_usd', 'cache_hit', 'feature_count')
        }),
        ('性能', {
            'fields': ('response_time_ms', 'status', 'error_message')
        }),
        ('元数据', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['export_to_csv']

    def REQUEST_ID_preview(self, obj):
        """Display preview of REQUEST_ID."""
        return obj.REQUEST_ID[:16] + '...'
    REQUEST_ID_preview.short_description = '请求ID'

    def has_add_permission(self, request):
        """Disable manual adding through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make usage logs read-only."""
        return False

    def get_queryset(self, request):
        """Annotate queryset with additional info."""
        qs = super().get_queryset(request)
        return qs.select_related()

    def export_to_csv(self, request, queryset):
        """Export selected logs to CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="llm_usage_logs.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'REQUEST_ID', 'Timestamp', 'Provider', 'Model',
            'Prompt Tokens', 'Completion Tokens', 'Total Tokens',
            'Cost (USD)', 'Request Type', 'Cache Hit',
            'Response Time (ms)', 'Status'
        ])

        for log in queryset:
            writer.writerow([
                log.REQUEST_ID,
                log.timestamp.isoformat(),
                log.provider,
                log.model,
                log.prompt_tokens,
                log.completion_tokens,
                log.total_tokens,
                log.cost_usd,
                log.request_type,
                log.cache_hit,
                log.response_time_ms,
                log.status
            ])

        return response
    export_to_csv.short_description = '导出选中的使用日志为 CSV'
