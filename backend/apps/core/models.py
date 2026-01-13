"""
Core models for prod_answer project.
"""
from django.db import models
import uuid


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ''created'' and ''modified'' fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SystemConfig(TimeStampedModel):
    """System configuration model."""
    config_key = models.CharField(max_length=100, unique=True)
    config_value = models.JSONField()
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'system_configs'
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'

    def __str__(self):
        return self.config_key

    @classmethod
    def get_config(cls, key: str, default=None):
        """Get configuration value by key."""
        try:
            config = cls.objects.get(config_key=key)
            return config.config_value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, key: str, value, description: str = None):
        """Set configuration value."""
        config, created = cls.objects.get_or_create(
            config_key=key,
            defaults={
                'config_value': value,
                'description': description or ''
            }
        )
        if not created:
            config.config_value = value
            if description:
                config.description = description
            config.save()
        return config
