"""
Matching models.
"""
from django.db import models
from apps.core.models import TimeStampedModel
from apps.products.models import Feature


class CapabilityRequirement(TimeStampedModel):
    """Capability requirement model."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    REQUIREMENT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('file', 'File'),
    ]

    title = models.CharField(max_length=255, blank=True, default='', verbose_name='需求名称')
    session_id = models.UUIDField(db_index=True)
    requirement_text = models.TextField(blank=True)
    requirement_type = models.CharField(
        max_length=20,
        choices=REQUIREMENT_TYPE_CHOICES,
        default='text'
    )
    source_file_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    created_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'capability_requirements'
        verbose_name = 'Capability Requirement'
        verbose_name_plural = 'Capability Requirements'
        ordering = ['-created_at']

    def __str__(self):
        if self.title:
            return self.title
        return f"Requirement {self.session_id}"


class RequirementItem(TimeStampedModel):
    """Requirement item model."""

    requirement = models.ForeignKey(
        CapabilityRequirement,
        on_delete=models.CASCADE,
        related_name='items',
        db_index=True
    )
    item_text = models.TextField()
    item_order = models.IntegerField(default=0)
    embedding = models.ForeignKey(
        'products.FeatureEmbedding',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )

    class Meta:
        db_table = 'requirement_items'
        verbose_name = 'Requirement Item'
        verbose_name_plural = 'Requirement Items'
        ordering = ['requirement', 'item_order']

    def __str__(self):
        return f"Item {self.item_order}: {self.item_text[:50]}..."


class MatchRecord(TimeStampedModel):
    """Match record model."""

    MATCH_STATUS_CHOICES = [
        ('matched', 'Matched'),
        ('partial_matched', 'Partial Matched'),
        ('unmatched', 'Unmatched'),
    ]

    requirement = models.ForeignKey(
        CapabilityRequirement,
        on_delete=models.CASCADE,
        related_name='matches',
        db_index=True
    )
    requirement_item = models.ForeignKey(
        RequirementItem,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    similarity_score = models.FloatField(db_index=True)
    match_status = models.CharField(
        max_length=20,
        choices=MATCH_STATUS_CHOICES
    )
    threshold_used = models.FloatField()
    rank = models.IntegerField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'match_records'
        verbose_name = 'Match Record'
        verbose_name_plural = 'Match Records'
        ordering = ['-similarity_score']

    def __str__(self):
        return f"Match: {self.requirement_item.item_text[:30]} -> {self.feature.feature_name} ({self.similarity_score:.2f})"
