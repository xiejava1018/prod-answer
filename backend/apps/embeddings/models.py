"""
Embedding model configuration.
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
import os
from cryptography.fernet import Fernet


class EmbeddingModelConfig(TimeStampedModel):
    """Embedding model configuration."""

    MODEL_TYPE_CHOICES = [
        ('openai', 'OpenAI'),
        ('huggingface', 'HuggingFace'),
        ('sentence-transformers', 'Sentence-Transformers'),
        ('local', 'Local Model'),
        ('openai-compatible', 'OpenAI-Compatible (硅基流动/智谱/通义等)'),
    ]

    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('siliconflow', '硅基流动 SiliconFlow'),
        ('zhipuai', '智谱AI ZhipuAI'),
        ('qwen', '阿里通义千问 Qwen'),
        ('sentence-transformers', 'Sentence-Transformers'),
        ('other', '其他'),
    ]

    model_name = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPE_CHOICES)
    provider = models.CharField(max_length=100)
    provider_name = models.CharField(
        max_length=100,
        choices=PROVIDER_CHOICES,
        default='other',
        blank=True,
        help_text="API提供商名称（用于OpenAI-compatible类型）"
    )
    base_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="API基础URL（用于OpenAI-compatible类型）"
    )
    api_endpoint = models.CharField(max_length=500, blank=True)
    api_key_encrypted = models.TextField(blank=True)
    dimension = models.IntegerField()
    model_params = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'embedding_model_configs'
        verbose_name = 'Embedding Model Config'
        verbose_name_plural = 'Embedding Model Configs'
        ordering = ['-is_default', 'model_name']

    def __str__(self):
        return self.model_name

    def clean(self):
        """Validate configuration."""
        if self.is_default:
            # Ensure only one default config
            if EmbeddingModelConfig.objects.filter(
                is_default=True
            ).exclude(id=self.id).exists():
                raise ValidationError("只能有一个默认的Embedding模型配置")

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
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
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
