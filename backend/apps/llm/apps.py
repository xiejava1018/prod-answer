"""
Django app configuration for LLM application.
"""
from django.apps import AppConfig


class LLMConfig(AppConfig):
    """Configuration for LLM application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.llm'
    verbose_name = 'LLM Enhanced Matching'
