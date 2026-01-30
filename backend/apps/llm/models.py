"""
LLM model configuration.

STUB IMPLEMENTATION - This file will be completed in Task 1.2
Currently provides minimal structure to prevent ImportError in services.py
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
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
        ('siliconflow', '硅基流动 SiliconFlow'),
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
        constraints = [
            models.UniqueConstraint(
            fields=['provider', 'model_name'],
            name='unique_provider_model'
            )
        ]

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


class LLMAnalysisResult(TimeStampedModel):
    """
    LLM analysis result for requirement-feature matching.

    Stores detailed analysis from LLM about whether a requirement
    item matches a feature, including reasoning and confidence scores.
    """

    requirement_item = models.ForeignKey(
        'matching.RequirementItem',
        on_delete=models.CASCADE,
        related_name='llm_analyses',
        db_index=True,
        help_text="The requirement item being analyzed"
    )
    feature = models.ForeignKey(
        'products.Feature',
        on_delete=models.CASCADE,
        related_name='llm_analyses',
        db_index=True,
        help_text="The feature being compared"
    )
    match_reason = models.TextField(
        blank=True,
        help_text="LLM's reasoning for the match decision"
    )
    keywords_from_requirement = models.JSONField(
        default=list,
        blank=True,
        help_text="Key phrases extracted from requirement"
    )
    keywords_from_feature = models.JSONField(
        default=list,
        blank=True,
        help_text="Key phrases extracted from feature"
    )
    is_valid_match = models.BooleanField(
        null=True,
        blank=True,
        help_text="LLM judgment: True=valid, False=invalid, Null=not analyzed or inconclusive"
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="LLM's confidence score (0.0-1.0)"
    )
    llm_provider = models.CharField(
        max_length=50,
        help_text="Provider used for analysis (e.g., 'openai', 'zhipuai')"
    )
    llm_model = models.CharField(
        max_length=100,
        help_text="Model used for analysis (e.g., 'gpt-4o-mini')"
    )
    prompt_tokens = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of tokens in the prompt"
    )
    completion_tokens = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of tokens in the completion"
    )
    total_tokens = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total tokens used (prompt + completion)"
    )
    analysis_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata from the analysis"
    )

    class Meta:
        db_table = 'llm_analysis_results'
        verbose_name = 'LLM Analysis Result'
        verbose_name_plural = 'LLM Analysis Results'
        ordering = ['-created_at']
        unique_together = ['requirement_item', 'feature']
        indexes = [
            models.Index(fields=['requirement_item', 'feature']),
            models.Index(fields=['llm_provider', 'llm_model']),
            models.Index(fields=['is_valid_match']),
            models.Index(fields=['confidence_score']),
        ]

    def __str__(self):
        return f"LLM Analysis: {self.requirement_item.item_text[:30]} -> {self.feature.feature_name}"

    def save(self, *args, **kwargs):
        # Calculate total tokens if not provided
        if self.prompt_tokens and self.completion_tokens and not self.total_tokens:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)


class LLMCache(TimeStampedModel):
    """
    Cache for LLM responses to avoid redundant API calls.

    Uses a hash of the input text and feature IDs as the cache key.
    Supports automatic expiration and hit counting.
    """

    cache_key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of the input parameters"
    )
    requirement_text = models.TextField(
        help_text="The requirement text that was analyzed"
    )
    feature_ids = models.JSONField(
        help_text="List of feature IDs that were analyzed"
    )
    response_json = models.JSONField(
        help_text="Cached LLM response"
    )
    hit_count = models.IntegerField(
        default=0,
        help_text="Number of times this cache entry has been used"
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="When this cache entry should expire"
    )
    llm_provider = models.CharField(
        max_length=50,
        help_text="Provider that generated this response"
    )
    llm_model = models.CharField(
        max_length=100,
        help_text="Model that generated this response"
    )

    class Meta:
        db_table = 'llm_cache'
        verbose_name = 'LLM Cache'
        verbose_name_plural = 'LLM Cache'
        ordering = ['-hit_count', '-created_at']
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['llm_provider', 'llm_model']),
        ]

    def __str__(self):
        return f"Cache: {self.cache_key[:16]}... ({self.hit_count} hits)"

    @classmethod
    def is_expired(cls, cache_entry):
        """Check if a cache entry has expired."""
        from django.utils import timezone
        return cache_entry.expires_at < timezone.now()

    def increment_hit_count(self):
        """Increment the hit count for this cache entry."""
        self.hit_count += 1
        self.save(update_fields=['hit_count'])


class LLMUsageLog(TimeStampedModel):
    """
    LLM API usage log for cost tracking and monitoring.

    Records token usage and costs for each LLM API call.
    Used for monitoring, cost analysis, and budget management.
    """

    REQUEST_ID = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique request identifier (UUID)"
    )
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When the request was made"
    )
    provider = models.CharField(
        max_length=50,
        db_index=True,
        help_text="LLM provider (e.g., 'openai', 'zhipuai')"
    )
    model = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Model name (e.g., 'gpt-4o-mini', 'glm-4-flash')"
    )
    prompt_tokens = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of tokens in the prompt"
    )
    completion_tokens = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of tokens in the completion"
    )
    total_tokens = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Total tokens used"
    )
    cost_usd = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Estimated cost in USD"
    )
    request_type = models.CharField(
        max_length=50,
        help_text="Type of request (e.g., 'analysis', 'batch_analysis', 'keyword_extraction')"
    )
    requirement_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Associated requirement ID (if applicable)"
    )
    feature_count = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Number of features analyzed"
    )
    cache_hit = models.BooleanField(
        default=False,
        help_text="Whether result came from cache"
    )
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Response time in milliseconds"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', '成功'),
            ('error', '错误'),
            ('timeout', '超时'),
        ],
        default='success',
        help_text="Request status"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if request failed"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (config_id, mode, etc.)"
    )

    class Meta:
        db_table = 'llm_usage_logs'
        verbose_name = 'LLM Usage Log'
        verbose_name_plural = 'LLM Usage Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['provider', 'model']),
            models.Index(fields=['request_type']),
            models.Index(fields=['requirement_id']),
            models.Index(fields=['status']),
            models.Index(fields=['cache_hit']),
        ]

    def __str__(self):
        return f"{self.provider}/{self.model} - {self.total_tokens} tokens (${self.cost_usd:.6f})"

    @classmethod
    def get_daily_cost(cls, date=None):
        """
        Get total cost for a specific day.

        Args:
            date: Date to query (defaults to today)

        Returns:
            Total cost in USD
        """
        from django.utils import timezone
        from django.db.models import Sum

        if date is None:
            date = timezone.now().date()

        datetime_start = timezone.make_aware(
            timezone.datetime.combine(date, timezone.datetime.min.time())
        )
        datetime_end = timezone.make_aware(
            timezone.datetime.combine(date, timezone.datetime.max.time())
        )

        result = cls.objects.filter(
            timestamp__range=[datetime_start, datetime_end],
            status='success'
        ).aggregate(total_cost=Sum('cost_usd'))

        return result['total_cost'] or 0.0

    @classmethod
    def get_model_stats(cls, provider, model, days=7):
        """
        Get usage statistics for a specific model over N days.

        Args:
            provider: Provider name
            model: Model name
            days: Number of days to look back

        Returns:
            Dictionary with stats (total_requests, total_tokens, total_cost, avg_cost)
        """
        from django.utils import timezone
        from django.db.models import Sum, Avg, Count
        from datetime import timedelta

        since = timezone.now() - timedelta(days=days)

        stats = cls.objects.filter(
            provider=provider,
            model=model,
            timestamp__gte=since,
            status='success'
        ).aggregate(
            total_requests=Count('id'),
            total_tokens=Sum('total_tokens'),
            total_cost=Sum('cost_usd'),
            avg_cost=Avg('cost_usd')
        )

        # Calculate avg_tokens manually to avoid aggregate conflict
        total_requests = stats['total_requests'] or 0
        total_tokens = stats['total_tokens'] or 0
        avg_tokens = round(total_tokens / total_requests, 1) if total_requests > 0 else 0

        return {
            'provider': provider,
            'model': model,
            'days': days,
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_cost': round(stats['total_cost'] or 0.0, 6),
            'avg_cost': round(stats['avg_cost'] or 0.0, 6),
            'avg_tokens': avg_tokens,
        }
