"""
LLM model configuration.

STUB IMPLEMENTATION - This file will be completed in Task 1.2
Currently provides minimal structure to prevent ImportError in services.py
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
import os
from cryptography.fernet import Fernet


class LLMModelConfig(TimeStampedModel):
    """
    LLM model configuration.

    FULL IMPLEMENTATION PENDING - Task 1.2
    This stub provides the minimum structure needed for services.py to work.
    """

    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('zhipuai', '智谱AI ZhipuAI'),
        ('qwen', '阿里通义千问 Qwen'),
        ('other', '其他'),
    ]

    # Basic fields - will be expanded in Task 1.2
    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default='openai'
    )
    model_name = models.CharField(
        max_length=100,
        help_text="Model identifier (e.g., 'gpt-4o-mini', 'glm-4-flash')"
    )
    api_key_encrypted = models.TextField(
        blank=True,
        help_text="Encrypted API key"
    )
    base_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Custom base URL for API (optional)"
    )
    max_tokens = models.IntegerField(
        default=2000,
        help_text="Maximum tokens in LLM response"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Temperature for text generation (0.0-2.0)"
    )
    model_params = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional model parameters"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is active"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default configuration"
    )

    class Meta:
        db_table = 'llm_model_configs'
        verbose_name = 'LLM Model Config'
        verbose_name_plural = 'LLM Model Configs'
        ordering = ['-is_default', 'provider', 'model_name']

    def __str__(self):
        return f"{self.provider}/{self.model_name}"

    def clean(self):
        """Validate configuration."""
        if self.is_default:
            # Ensure only one default config per provider
            if LLMModelConfig.objects.filter(
                is_default=True,
                provider=self.provider
            ).exclude(id=self.id).exists():
                raise ValidationError(
                    f"只能有一个默认的{self.get_provider_display()}配置"
                )

        # Validate temperature range
        if not 0 <= self.temperature <= 2:
            raise ValidationError("Temperature必须在0.0到2.0之间")

        # Validate max_tokens
        if self.max_tokens <= 0:
            raise ValidationError("Max tokens必须大于0")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_encryption_key(self):
        """Get or generate encryption key."""
        # Try environment variable first
        key = os.environ.get('ENCRYPTION_KEY')
        if key:
            return key

        # Try loading from .env file
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            '.env'
        )
        if os.path.exists(env_file):
            from dotenv import load_dotenv
            load_dotenv(env_file)
            key = os.environ.get('ENCRYPTION_KEY')
            if key:
                return key

        # Generate and save a new key
        key = Fernet.generate_key().decode()

        # Save to .env file
        try:
            with open(env_file, 'a') as f:
                f.write(f'\n# Auto-generated encryption key for API keys\nENCRYPTION_KEY={key}\n')
            os.environ['ENCRYPTION_KEY'] = key
        except Exception:
            # If we can't save to .env, just set it for this session
            os.environ['ENCRYPTION_KEY'] = key

        return key

    def get_api_key(self):
        """Get decrypted API key."""
        if not self.api_key_encrypted:
            return None

        try:
            key = self.get_encryption_key()
            f = Fernet(key.encode())
            return f.decrypt(self.api_key_encrypted.encode()).decode()
        except Exception as e:
            # If decryption fails, might be stored as plain text
            if self.api_key_encrypted and not self.api_key_encrypted.startswith('gAAA'):
                return self.api_key_encrypted
            raise ValueError(f"Failed to decrypt API key: {str(e)}")

    def set_api_key(self, api_key: str):
        """Encrypt and set API key."""
        if not api_key:
            self.api_key_encrypted = ''
            return

        try:
            key = self.get_encryption_key()
            f = Fernet(key.encode())
            self.api_key_encrypted = f.encrypt(api_key.encode()).decode()
        except Exception as e:
            # If encryption fails, store as plain text (fallback)
            import warnings
            warnings.warn(f"Failed to encrypt API key, storing as plain text: {str(e)}")
            self.api_key_encrypted = api_key


# TODO (Task 1.2): Add the following features:
# - More provider choices (Anthropic, Google Gemini, etc.)
# - Rate limiting configuration
# - Budget/cost tracking fields
# - Usage statistics tracking
# - API version selection
# - Custom prompt templates per model
# - Admin interface customization
# - Migration to create database table
