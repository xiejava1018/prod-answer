"""
Admin configuration for Matching models.
"""
from django.contrib import admin
from .models import CapabilityRequirement, RequirementItem, MatchRecord


class RequirementItemInline(admin.TabularInline):
    """Inline admin for requirement items."""

    model = RequirementItem
    extra = 0
    readonly_fields = ['item_text', 'item_order', 'created_at']
    can_delete = False


@admin.register(CapabilityRequirement)
class CapabilityRequirementAdmin(admin.ModelAdmin):
    """Admin interface for CapabilityRequirement model."""

    list_display = [
        'session_id',
        'requirement_type',
        'source_file_name',
        'status',
        'items_count',
        'created_by',
        'created_at'
    ]
    list_filter = ['status', 'requirement_type', 'created_at']
    search_fields = ['session_id', 'source_file_name', 'requirement_text']
    ordering = ['-created_at']
    inlines = [RequirementItemInline]

    def items_count(self, obj):
        """Display count of items."""
        return obj.items.count()
    items_count.short_description = 'Items'


class MatchRecordInline(admin.TabularInline):
    """Inline admin for match records."""

    model = MatchRecord
    extra = 0
    readonly_fields = [
        'requirement_item',
        'feature',
        'similarity_score',
        'match_status',
        'threshold_used',
        'rank'
    ]
    can_delete = False


@admin.register(RequirementItem)
class RequirementItemAdmin(admin.ModelAdmin):
    """Admin interface for RequirementItem model."""

    list_display = [
        'item_text_preview',
        'requirement',
        'item_order',
        'matches_count',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['item_text', 'requirement__session_id']
    ordering = ['requirement', 'item_order']
    inlines = [MatchRecordInline]

    def item_text_preview(self, obj):
        """Display preview of item text."""
        return obj.item_text[:50] + '...' if len(obj.item_text) > 50 else obj.item_text
    item_text_preview.short_description = 'Item Text'

    def matches_count(self, obj):
        """Display count of matches."""
        return obj.matches.count()
    matches_count.short_description = 'Matches'


@admin.register(MatchRecord)
class MatchRecordAdmin(admin.ModelAdmin):
    """Admin interface for MatchRecord model."""

    list_display = [
        'requirement_item_preview',
        'feature_name',
        'product_name',
        'similarity_score',
        'match_status',
        'rank',
        'created_at'
    ]
    list_filter = ['match_status', 'threshold_used', 'created_at']
    search_fields = [
        'requirement_item__item_text',
        'feature__feature_name',
        'feature__product__name'
    ]
    ordering = ['-similarity_score']
    readonly_fields = [
        'requirement',
        'requirement_item',
        'feature',
        'similarity_score',
        'match_status',
        'threshold_used',
        'rank',
        'metadata',
        'created_at'
    ]

    def requirement_item_preview(self, obj):
        """Display preview of requirement item."""
        text = obj.requirement_item.item_text
        return text[:30] + '...' if len(text) > 30 else text
    requirement_item_preview.short_description = 'Requirement'

    def feature_name(self, obj):
        """Display feature name."""
        return obj.feature.feature_name

    def product_name(self, obj):
        """Display product name."""
        return obj.feature.product.name

    def has_add_permission(self, request):
        """Disable manual adding through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make match records read-only."""
        return False
