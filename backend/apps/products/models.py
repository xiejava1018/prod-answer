"""
Product and Feature models.
"""
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.core.models import TimeStampedModel
import os

# Conditional import for pgvector
if os.environ.get('USE_SQLITE'):
    # Use JSONField for SQLite testing
    VectorField = lambda **kwargs: models.JSONField(**kwargs)
else:
    from pgvector.django import VectorField


class Product(TimeStampedModel):
    """Product model."""

    name = models.CharField(max_length=200, db_index=True)
    version = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=100, db_index=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} {self.version or ''}".strip()


class Feature(TimeStampedModel):
    """Feature model."""

    MATCH_STATUS_CHOICES = [
        ('matched', 'Matched'),
        ('partial_matched', 'Partial Matched'),
        ('unmatched', 'Unmatched'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='features',
        db_index=True
    )
    feature_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    feature_name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    category = models.CharField(max_length=100, db_index=True, blank=True)
    subcategory = models.CharField(max_length=100, blank=True)
    importance_level = models.IntegerField(default=5)  # 1-10
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'features'
        verbose_name = 'Feature'
        verbose_name_plural = 'Features'
        ordering = ['category', 'subcategory', 'feature_name']

    def __str__(self):
        return f"{self.feature_name} - {self.product.name}"


class FeatureEmbedding(TimeStampedModel):
    """Feature embedding vector storage."""

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='embeddings'
    )
    embedding = VectorField(dimensions=1536) if not os.environ.get('USE_SQLITE') else models.JSONField(default=list)  # OpenAI dimension, configurable
    model_name = models.CharField(max_length=100, db_index=True)
    model_version = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'feature_embeddings'
        verbose_name = 'Feature Embedding'
        verbose_name_plural = 'Feature Embeddings'
        unique_together = ['feature', 'model_name']
        indexes = [
            models.Index(fields=['model_name']),
        ]

    def __str__(self):
        return f"{self.feature.feature_name} - {self.model_name}"


@receiver(pre_save, sender=Feature)
def cleanup_feature_embeddings_on_soft_delete(sender, instance, **kwargs):
    """
    当功能被软删除时（is_active 从 True 变为 False），自动清理其向量数据。
    """
    if instance.pk is not None:
        try:
            old_instance = Feature.objects.get(pk=instance.pk)
            # 如果从活跃变为非活跃，删除该功能的所有向量
            if old_instance.is_active and not instance.is_active:
                embeddings = instance.embeddings.all()
                count = embeddings.count()
                if count > 0:
                    embeddings.delete()
                    print(f"[信号处理器] 已删除功能 '{instance.feature_name}' 的 {count} 个向量")
        except Feature.DoesNotExist:
            pass


@receiver(pre_save, sender=Product)
def cleanup_product_embeddings_on_soft_delete(sender, instance, **kwargs):
    """
    当产品被软删除时（is_active 从 True 变为 False），自动清理其所有功能的向量数据。
    """
    if instance.pk is not None:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            # 如果从活跃变为非活跃，删除该产品所有功能的向量
            if old_instance.is_active and not instance.is_active:
                total_count = 0
                for feature in instance.features.all():
                    embeddings = feature.embeddings.all()
                    count = embeddings.count()
                    if count > 0:
                        embeddings.delete()
                        total_count += count
                        print(f"[信号处理器] 已删除功能 '{feature.feature_name}' 的 {count} 个向量")
                if total_count > 0:
                    print(f"[信号处理器] 已删除产品 '{instance.name}' 的所有功能的 {total_count} 个向量")
        except Product.DoesNotExist:
            pass
