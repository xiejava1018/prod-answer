"""
LLM service factory and management.
"""
import hashlib
import json
import logging
import asyncio
from datetime import timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .providers.base import BaseLLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.zhipuai_provider import ZhipuAIProvider
from .providers.qwen_provider import QwenProvider

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory class for creating and managing LLM providers.
    Supports multiple LLM providers (OpenAI, ZhipuAI, Qwen, SiliconFlow).
    """

    # Registry of available providers
    _providers = {
        'openai': OpenAIProvider,
        'zhipuai': ZhipuAIProvider,
        'qwen': QwenProvider,
        'siliconflow': OpenAIProvider,  # SiliconFlow uses OpenAI-compatible API
    }

    # Cache for provider instances
    _provider_cache = {}

    @classmethod
    def register_provider(cls, provider_type: str, provider_class):
        """
        Register a new LLM provider type.

        Args:
            provider_type: Type identifier (e.g., 'openai', 'zhipuai')
            provider_class: Provider class (must inherit from BaseLLMProvider)

        Raises:
            ValueError: If provider_class doesn't inherit from BaseLLMProvider
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(
                f"Provider class must inherit from BaseLLMProvider. "
                f"Got: {provider_class.__name__}"
            )

        cls._providers[provider_type] = provider_class

    @classmethod
    def create_provider(cls, config: Any, use_cache: bool = True) -> BaseLLMProvider:
        """
        Create a provider instance from configuration.

        Args:
            config: Configuration object (LLMModelConfig or dict)
                If dict, must contain: provider, model_name, api_key
            use_cache: Whether to cache and reuse provider instances

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is not supported or config is invalid
        """
        # Handle both dict and config object
        if isinstance(config, dict):
            config_id = config.get('id', hash(str(config)))
            provider_type = config.get('provider')
            config_dict = config
        else:
            # Assume it's a model config object
            config_id = config.id
            provider_type = config.provider
            config_dict = {
                'provider': config.provider,
                'model_name': config.model_name,
                'api_key': config.get_api_key() if hasattr(config, 'get_api_key') else config.api_key_encrypted,
                'base_url': getattr(config, 'base_url', None),
                'max_tokens': getattr(config, 'max_tokens', 2000),
                'temperature': getattr(config, 'temperature', 0.7),
                'model_params': getattr(config, 'model_params', {}),
            }

        # Check cache first
        if use_cache and config_id in cls._provider_cache:
            return cls._provider_cache[config_id]

        # Get provider class
        provider_class = cls._providers.get(provider_type)

        if not provider_class:
            supported_types = list(cls._providers.keys())
            raise ValueError(
                f"Unsupported LLM provider type: {provider_type}. "
                f"Supported types: {supported_types}"
            )

        # Validate required fields
        required_fields = ['provider', 'model_name']
        for field in required_fields:
            if field not in config_dict:
                raise ValueError(f"Missing required config field: {field}")

        # Create provider instance
        try:
            provider = provider_class(config_dict)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create {provider_type} provider: {str(e)}"
            )

        # Cache instance
        if use_cache:
            cls._provider_cache[config_id] = provider

        return provider

    @classmethod
    def get_default_provider(cls) -> BaseLLMProvider:
        """
        Get the default LLM provider.

        Returns:
            Default provider instance

        Raises:
            ValueError: If no default configuration is found

        Note:
            This method requires LLMModelConfig model to be imported.
            Call this method only after the models are defined.
        """
        try:
            from .models import LLMModelConfig
        except ImportError:
            raise ValueError(
                "LLMModelConfig model not found. "
                "Make sure the LLM app is properly configured."
            )

        # Try to get default config
        config = LLMModelConfig.objects.filter(
            is_default=True,
            is_active=True
        ).first()

        if not config:
            # If no default, use first active config
            config = LLMModelConfig.objects.filter(
                is_active=True
            ).first()

        if not config:
            raise ValueError(
                "No active LLM model configuration found. "
                "Please create and activate a model configuration."
            )

        return cls.create_provider(config)

    @classmethod
    def get_provider_by_id(cls, config_id: str) -> BaseLLMProvider:
        """
        Get a provider by configuration ID.

        Args:
            config_id: UUID of the configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If config not found
        """
        try:
            from .models import LLMModelConfig
        except ImportError:
            raise ValueError(
                "LLMModelConfig model not found. "
                "Make sure the LLM app is properly configured."
            )

        try:
            config = LLMModelConfig.objects.get(id=config_id)
            return cls.create_provider(config)
        except LLMModelConfig.DoesNotExist:
            raise ValueError(
                f"LLM configuration not found: {config_id}"
            )

    @classmethod
    def get_all_active_configs(cls) -> List[Any]:
        """
        Get all active model configurations.

        Returns:
            List of active LLMModelConfig instances
        """
        try:
            from .models import LLMModelConfig
        except ImportError:
            return []

        return LLMModelConfig.objects.filter(is_active=True)

    @classmethod
    def clear_cache(cls):
        """
        Clear the provider cache.
        Useful when configurations are updated.
        """
        cls._provider_cache.clear()

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        Get list of available provider types.

        Returns:
            List of provider type names
        """
        return list(cls._providers.keys())


class LLMService:
    """
    High-level service for LLM operations.

    This service provides a simplified interface for common LLM tasks
    in the matching system.
    """

    def __init__(self, config_id: Optional[str] = None):
        """
        Initialize the service.

        Args:
            config_id: Optional configuration ID (uses default if not provided)
        """
        self.factory = LLMProviderFactory
        self.config_id = config_id

    async def analyze_matches(
        self,
        requirement: str,
        matches: List[Dict[str, Any]],
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Analyze matching results using LLM.

        Args:
            requirement: User requirement text
            matches: List of match results
            threshold: Similarity threshold used

        Returns:
            Analysis dictionary
        """
        provider = self._get_provider()
        return await provider.analyze_matches(requirement, matches, threshold)

    async def generate_explanation(
        self,
        requirement: str,
        feature: Dict[str, Any],
        similarity_score: float
    ) -> str:
        """
        Generate explanation for a match.

        Args:
            requirement: User requirement text
            feature: Feature dictionary
            similarity_score: Similarity score

        Returns:
            Natural language explanation
        """
        provider = self._get_provider()
        return await provider.generate_explanation(requirement, feature, similarity_score)

    async def suggest_improvements(
        self,
        requirement: str,
        unmatched_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest improvements for matching.

        Args:
            requirement: User requirement text
            unmatched_features: Features that didn't match

        Returns:
            Dictionary with suggestions
        """
        provider = self._get_provider()
        return await provider.suggest_improvements(requirement, unmatched_features)

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the LLM provider connection.

        Returns:
            Dictionary with test results
        """
        try:
            provider = self._get_provider()
            is_connected = await provider.test_connection()
            model_info = provider.get_model_info()

            return {
                'status': 'success' if is_connected else 'failed',
                'is_connected': is_connected,
                'model_info': model_info,
            }
        except Exception as e:
            return {
                'status': 'error',
                'is_connected': False,
                'error': str(e),
            }

    def _get_provider(self) -> BaseLLMProvider:
        """Get provider instance."""
        if self.config_id:
            return self.factory.get_provider_by_id(self.config_id)
        else:
            return self.factory.get_default_provider()

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        provider = self._get_provider()
        return provider.get_model_info()


# =============================================================================
# PHASE 2: LLM Analysis Service with Caching, Retry, and Concurrency Control
# =============================================================================

class LLMAnalysisService:
    """
    High-level service for LLM-based analysis of requirement-feature matches.

    Features:
    - Caching mechanism to reduce API calls and costs
    - Automatic retry with exponential backoff
    - Concurrency control to avoid API rate limits
    - Token counting and cost estimation
    - Response validation and error handling

    Usage:
        service = LLMAnalysisService(config_id="uuid")
        results = await service.analyze_requirement_matches(
            requirement_text="Need data export",
            candidates=[...],
            mode="full"
        )
    """

    # Concurrency limit for simultaneous LLM calls
    MAX_CONCURRENT_CALLS = 5
    _semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)

    # Cache expiration time (default: 7 days)
    CACHE_EXPIRY_DAYS = 7

    def __init__(self, config_id: Optional[str] = None, use_cache: bool = True):
        """
        Initialize the LLM analysis service.

        Args:
            config_id: Optional LLM configuration ID (uses default if not provided)
            use_cache: Whether to use caching mechanism
        """
        self.config_id = config_id
        self.use_cache = use_cache
        self._provider = None

    def _get_provider(self) -> BaseLLMProvider:
        """Get or create provider instance."""
        if self._provider is None:
            if self.config_id:
                self._provider = LLMProviderFactory.get_provider_by_id(self.config_id)
            else:
                self._provider = LLMProviderFactory.get_default_provider()
        return self._provider

    def _generate_cache_key(
        self,
        requirement_text: str,
        feature_ids: List[str],
        mode: str = "full"
    ) -> str:
        """
        Generate a unique cache key from input parameters.

        Args:
            requirement_text: The requirement text
            feature_ids: List of feature IDs being analyzed
            mode: Analysis mode ("full" or "quick")

        Returns:
            SHA-256 hash as hexadecimal string
        """
        # Create a deterministic string from inputs
        key_data = {
            'requirement': requirement_text,
            'features': sorted(feature_ids),
            'mode': mode,
            'provider': self._get_provider().config.get('provider'),
            'model': self._get_provider().config.get('model_name')
        }
        key_string = json.dumps(key_data, sort_keys=True)

        # Generate SHA-256 hash
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def _get_cached_result(self, cache_key: str):
        """
        Retrieve cached result if available and not expired.

        Args:
            cache_key: Cache key to look up

        Returns:
            Cached response JSON if found and valid, None otherwise
        """
        if not self.use_cache:
            return None

        try:
            from .models import LLMCache

            cache_entry = await LLMCache.objects.aget(cache_key=cache_key)

            # Check if expired
            if LLMCache.is_expired(cache_entry):
                await cache_entry.adelete()
                logger.info(f"Cache entry expired: {cache_key[:16]}...")
                return None

            # Increment hit count
            await cache_entry.aincrement_hit_count()

            logger.info(f"Cache hit: {cache_key[:16]}... (hits: {cache_entry.hit_count})")
            return cache_entry.response_json

        except LLMCache.DoesNotExist:
            logger.debug(f"Cache miss: {cache_key[:16]}...")
            return None
        except Exception as e:
            logger.warning(f"Error retrieving cache: {e}")
            return None

    async def _save_to_cache(
        self,
        cache_key: str,
        requirement_text: str,
        feature_ids: List[str],
        response_json: Dict[str, Any]
    ):
        """
        Save LLM response to cache.

        Args:
            cache_key: Cache key
            requirement_text: Original requirement text
            feature_ids: List of feature IDs
            response_json: LLM response to cache
        """
        if not self.use_cache:
            return

        try:
            from .models import LLMCache

            provider = self._get_provider()
            expires_at = timezone.now() + timedelta(days=self.CACHE_EXPIRY_DAYS)

            cache_entry = LLMCache(
                cache_key=cache_key,
                requirement_text=requirement_text,
                feature_ids=feature_ids,
                response_json=response_json,
                expires_at=expires_at,
                llm_provider=provider.config.get('provider'),
                llm_model=provider.config.get('model_name')
            )

            await cache_entry.asave()
            logger.info(f"Saved to cache: {cache_key[:16]}...")

        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    async def _call_llm_with_retry(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Call LLM API with automatic retry on failure.

        Note: This is a placeholder method that wraps the provider's analyze_matches.
        For production use with custom prompts, providers should implement call_api method.

        Args:
            system_prompt: System prompt (currently not used, kept for future)
            user_prompt: User prompt text

        Returns:
            LLM response text

        Raises:
            ConnectionError: If connection fails after retries
            TimeoutError: If request times out after retries
        """
        provider = self._get_provider()

        # Use semaphore to limit concurrent calls
        async with self._semaphore:
            logger.debug(f"Calling LLM: {provider.config.get('model_name')}")

            # For now, create a minimal match structure to use analyze_matches
            # In production, providers should implement a generic call_api method
            try:
                # Try to use call_api if provider implements it
                if hasattr(provider, 'call_api'):
                    response = await provider.call_api(system_prompt, user_prompt)
                    # Return raw response text
                    if isinstance(response, dict):
                        return response.get('raw_response', json.dumps(response))
                    return response
                else:
                    # Fallback: analyze_matches returns structured data
                    # We'll extract the raw response
                    test_requirement = user_prompt[:500]  # Truncate for safety
                    test_matches = [{
                        'feature_id': 'dummy',
                        'feature_name': 'Analysis Request',
                        'feature_description': user_prompt[:2000],
                        'similarity_score': 0.8,
                        'status': 'partial_match'
                    }]

                    result = await provider.analyze_matches(test_requirement, test_matches)
                    return result.get('raw_response', json.dumps(result))

            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                raise

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response text into structured JSON.

        Args:
            response_text: Raw LLM response text

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If response is not valid JSON
        """
        # Try to extract JSON from response
        # LLMs sometimes wrap JSON in markdown code blocks
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {text[:200]}")

    def _validate_response(
        self,
        response: Dict[str, Any],
        output_schema: Dict[str, Any]
    ) -> bool:
        """
        Validate LLM response against expected schema.

        Args:
            response: Parsed LLM response
            output_schema: Expected JSON schema

        Returns:
            True if valid, False otherwise
        """
        required_fields = output_schema.get("required", [])
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field in LLM response: {field}")
                return False
        return True

    async def analyze_requirement_matches(
        self,
        requirement_text: str,
        candidates: List[Dict[str, Any]],
        mode: str = "full",
        use_enhanced_prompts: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze requirement-feature matches using LLM.

        Args:
            requirement_text: User requirement text
            candidates: List of candidate feature dictionaries
            mode: Analysis mode ("full" or "quick")
            use_enhanced_prompts: Whether to use enhanced prompts (Task 2.1)

        Returns:
            Analysis results dictionary with:
                - analysis_summary: Overall summary
                - match_details: List of per-feature analyses
                - overall_assessment: Overall metrics
                - cached: Whether result came from cache
                - tokens_used: Token usage statistics

        Raises:
            ValueError: If response validation fails
            ConnectionError: If LLM API fails after retries
        """
        # Generate cache key
        feature_ids = [c.get('feature_id', c.get('id', '')) for c in candidates]
        cache_key = self._generate_cache_key(requirement_text, feature_ids, mode)

        # Check cache first
        cached_result = await self._get_cached_result(cache_key)
        if cached_result is not None:
            cached_result['cached'] = True
            return cached_result

        # Import prompt templates
        if use_enhanced_prompts:
            from .prompts import EnhancedMatchAnalysisPrompts

            # Format prompts using enhanced templates
            system_prompt = EnhancedMatchAnalysisPrompts.SYSTEM_PROMPT
            user_prompt = EnhancedMatchAnalysisPrompts.format_user_prompt(
                requirement=requirement_text,
                candidates=candidates,
                mode=mode
            )
        else:
            from .prompts import MatchAnalysisPrompts

            # Use legacy prompts
            system_prompt = MatchAnalysisPrompts.SYSTEM_PROMPT
            user_prompt = MatchAnalysisPrompts.format_user_prompt(
                requirement=requirement_text,
                matches=candidates,
                threshold=0.75  # Default threshold
            )

        # Call LLM with retry
        response_text = await self._call_llm_with_retry(system_prompt, user_prompt)

        # Parse response
        try:
            response_data = self._parse_llm_response(response_text)
        except ValueError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise

        # Validate response
        if use_enhanced_prompts:
            template = EnhancedMatchAnalysisPrompts.get_prompt_template(mode=mode)
            if not self._validate_response(response_data, template.output_schema):
                raise ValueError("LLM response validation failed")

        # Add metadata
        response_data['cached'] = False
        response_data['tokens_used'] = response_data.get('tokens_used', {})

        # Save to cache
        await self._save_to_cache(
            cache_key,
            requirement_text,
            feature_ids,
            response_data
        )

        logger.info(f"Analysis complete: {len(candidates)} candidates, mode={mode}")
        return response_data

    async def batch_analyze(
        self,
        requirements: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        mode: str = "quick",
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze multiple requirements in batch with concurrency control.

        Args:
            requirements: List of requirement dictionaries
            candidates: List of candidate features
            mode: Analysis mode ("full" or "quick")
            max_concurrent: Maximum concurrent analyses

        Returns:
            Dictionary mapping requirement IDs to analysis results
        """
        results = {}

        # Process in batches to control concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_one(req_dict):
            async with semaphore:
                req_id = req_dict.get('id', req_dict.get('requirement_id'))
                req_text = req_dict.get('text', req_dict.get('item_text', ''))

                try:
                    result = await self.analyze_requirement_matches(
                        requirement_text=req_text,
                        candidates=candidates,
                        mode=mode
                    )
                    return req_id, result
                except Exception as e:
                    logger.error(f"Failed to analyze requirement {req_id}: {e}")
                    return req_id, {'error': str(e)}

        # Create tasks
        tasks = [analyze_one(req) for req in requirements]

        # Execute with progress tracking
        completed = 0
        total = len(tasks)

        for coro in asyncio.as_completed(tasks):
            req_id, result = await coro
            results[req_id] = result
            completed += 1
            logger.info(f"Batch analysis progress: {completed}/{total}")

        return results

    async def extract_keywords(
        self,
        requirement: str,
        feature_description: str
    ) -> Dict[str, Any]:
        """
        Extract keywords from requirement and feature descriptions.

        Args:
            requirement: Requirement text
            feature_description: Feature description text

        Returns:
            Dictionary with extracted keywords
        """
        from .prompts import KeywordExtractionPrompts

        # Generate cache key
        cache_key = self._generate_cache_key(
            requirement,
            [feature_description[:50]],  # Use partial description as ID
            mode="keywords"
        )

        # Check cache
        cached_result = await self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result

        # Format prompts
        system_prompt = KeywordExtractionPrompts.SYSTEM_PROMPT
        user_prompt = KeywordExtractionPrompts.format_user_prompt(
            requirement=requirement,
            feature_description=feature_description
        )

        # Call LLM
        response_text = await self._call_llm_with_retry(system_prompt, user_prompt)
        response_data = self._parse_llm_response(response_text)

        # Validate
        template = KeywordExtractionPrompts.get_prompt_template()
        if not self._validate_response(response_data, template.output_schema):
            raise ValueError("Keyword extraction response validation failed")

        # Cache result
        await self._save_to_cache(
            cache_key,
            requirement,
            [feature_description[:50]],
            response_data
        )

        return response_data

    async def detect_mismatch(
        self,
        requirement: str,
        feature_name: str,
        feature_description: str,
        similarity_score: float,
        original_status: str
    ) -> Dict[str, Any]:
        """
        Detect if a match is a false positive.

        Args:
            requirement: Requirement text
            feature_name: Feature name
            feature_description: Feature description
            similarity_score: Vector similarity score
            original_status: Original match status

        Returns:
            Dictionary with mismatch detection results
        """
        from .prompts import MismatchDetectionPrompts

        # Generate cache key
        cache_key = self._generate_cache_key(
            requirement,
            [feature_name, str(similarity_score)],
            mode="mismatch"
        )

        # Check cache
        cached_result = await self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result

        # Format prompts
        system_prompt = MismatchDetectionPrompts.SYSTEM_PROMPT
        user_prompt = MismatchDetectionPrompts.format_user_prompt(
            requirement=requirement,
            feature_name=feature_name,
            feature_description=feature_description,
            similarity_score=similarity_score,
            original_status=original_status
        )

        # Call LLM
        response_text = await self._call_llm_with_retry(system_prompt, user_prompt)
        response_data = self._parse_llm_response(response_text)

        # Validate
        template = MismatchDetectionPrompts.get_prompt_template()
        if not self._validate_response(response_data, template.output_schema):
            raise ValueError("Mismatch detection response validation failed")

        # Cache result
        await self._save_to_cache(
            cache_key,
            requirement,
            [feature_name],
            response_data
        )

        return response_data

    @classmethod
    async def clear_expired_cache(cls):
        """Remove all expired cache entries."""
        try:
            from .models import LLMCache
            from django.utils import timezone

            expired_count = await LLMCache.objects.filter(
                expires_at__lt=timezone.now()
            ).adelete()

            logger.info(f"Cleared {expired_count} expired cache entries")
            return expired_count

        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            from .models import LLMCache
            from django.utils import timezone
            from django.db.models import Sum, Count, Avg

            total_entries = LLMCache.objects.count()
            total_hits = LLMCache.objects.aggregate(
                total_hits=Sum('hit_count')
            )['total_hits'] or 0

            active_entries = LLMCache.objects.filter(
                expires_at__gte=timezone.now()
            ).count()

            avg_hits = LLMCache.objects.aggregate(
                avg_hits=Avg('hit_count')
            )['avg_hits'] or 0

            return {
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': total_entries - active_entries,
                'total_hits': total_hits,
                'avg_hits_per_entry': round(avg_hits, 2),
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


class LLMCostAlertService:
    """
    Service for monitoring LLM costs and sending alerts when thresholds are exceeded.

    Supports:
    - Daily, weekly, monthly cost thresholds
    - Per-model and per-provider thresholds
    - Multiple notification channels (logging, email, webhook)
    - Alert history and cooldown periods
    """

    # Alert levels
    ALERT_LEVEL_INFO = 'info'
    ALERT_LEVEL_WARNING = 'warning'
    ALERT_LEVEL_CRITICAL = 'critical'

    # Time periods
    PERIOD_DAILY = 'daily'
    PERIOD_WEEKLY = 'weekly'
    PERIOD_MONTHLY = 'monthly'

    # Default thresholds (in USD)
    DEFAULT_THRESHOLDS = {
        PERIOD_DAILY: 10.0,
        PERIOD_WEEKLY: 50.0,
        PERIOD_MONTHLY: 200.0,
    }

    # Alert cooldown (in seconds) - prevent duplicate alerts
    ALERT_COOLDOWN = 3600  # 1 hour

    def __init__(self):
        """Initialize cost alert service."""
        self._alert_cache_key = "llm_cost_alerts:{alert_type}:{period}"

    def check_cost_thresholds(
        self,
        period: str = PERIOD_DAILY,
        thresholds: Dict[str, float] = None,
        provider: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Check if costs have exceeded thresholds for the given period.

        Args:
            period: Time period to check (daily, weekly, monthly)
            thresholds: Dictionary of thresholds for different alert levels
            provider: Optional provider to filter by
            model: Optional model to filter by

        Returns:
            Alert result with:
                - exceeded: bool, whether threshold was exceeded
                - current_cost: float, actual cost
                - threshold: float, threshold value
                - alert_level: str, info/warning/critical
                - details: dict, additional breakdown
        """
        from .models import LLMUsageLog
        from django.utils import timezone
        from datetime import timedelta, datetime

        if thresholds is None:
            thresholds = {
                self.ALERT_LEVEL_WARNING: self.DEFAULT_THRESHOLDS.get(period, 10.0),
                self.ALERT_LEVEL_CRITICAL: self.DEFAULT_THRESHOLDS.get(period, 10.0) * 2,
            }

        # Calculate date range
        if period == self.PERIOD_DAILY:
            since = timezone.now() - timedelta(days=1)
        elif period == self.PERIOD_WEEKLY:
            since = timezone.now() - timedelta(weeks=1)
        elif period == self.PERIOD_MONTHLY:
            since = timezone.now() - timedelta(days=30)
        else:
            since = timezone.now() - timedelta(days=1)

        # Get cost for the period
        queryset = LLMUsageLog.objects.filter(
            timestamp__gte=since,
            status='success'
        )

        if provider:
            queryset = queryset.filter(provider=provider)
        if model:
            queryset = queryset.filter(model=model)

        from django.db.models import Sum
        result = queryset.aggregate(total_cost=Sum('cost_usd'))
        current_cost = result['total_cost'] or 0.0

        # Check thresholds
        warning_threshold = thresholds.get(self.ALERT_LEVEL_WARNING, float('inf'))
        critical_threshold = thresholds.get(self.ALERT_LEVEL_CRITICAL, float('inf'))

        alert_level = None
        exceeded = False
        threshold_value = None

        if current_cost >= critical_threshold:
            alert_level = self.ALERT_LEVEL_CRITICAL
            exceeded = True
            threshold_value = critical_threshold
        elif current_cost >= warning_threshold:
            alert_level = self.ALERT_LEVEL_WARNING
            exceeded = True
            threshold_value = warning_threshold

        # Get detailed breakdown
        provider_model_stats = queryset.values('provider', 'model').annotate(
            cost=Sum('cost_usd'),
            requests=Count('id')
        ).order_by('-cost')

        details = {
            'period': period,
            'since': since.isoformat(),
            'provider': provider,
            'model': model,
            'breakdown_by_model': list(provider_model_stats),
        }

        alert_result = {
            'exceeded': exceeded,
            'current_cost': round(current_cost, 6),
            'threshold': round(threshold_value, 6) if threshold_value else None,
            'alert_level': alert_level,
            'details': details,
        }

        return alert_result

    def send_alert(
        self,
        alert_result: Dict[str, Any],
        notification_channels: List[str] = None
    ) -> bool:
        """
        Send alert notification through specified channels.

        Args:
            alert_result: Result from check_cost_thresholds
            notification_channels: List of channels (log, email, webhook)

        Returns:
            True if alert was sent successfully
        """
        if not alert_result['exceeded']:
            return False

        if notification_channels is None:
            notification_channels = ['log']

        # Check cooldown
        alert_key = f"{alert_result['details']['period']}:{alert_result['alert_level']}"
        if self._is_on_cooldown(alert_key):
            logger.info(f"Alert on cooldown: {alert_key}")
            return False

        # Format alert message
        message = self._format_alert_message(alert_result)

        # Send through each channel
        success = False
        for channel in notification_channels:
            try:
                if channel == 'log':
                    self._send_log_alert(alert_result, message)
                    success = True
                elif channel == 'email':
                    self._send_email_alert(alert_result, message)
                    success = True
                elif channel == 'webhook':
                    self._send_webhook_alert(alert_result, message)
                    success = True
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")

        # Set cooldown
        if success:
            self._set_cooldown(alert_key)

        return success

    def _format_alert_message(self, alert_result: Dict[str, Any]) -> str:
        """Format alert message for notification."""
        level = alert_result['alert_level'].upper()
        cost = alert_result['current_cost']
        threshold = alert_result['threshold']
        period = alert_result['details']['period']

        lines = [
            f"LLM Cost Alert - {level}",
            f"Period: {period}",
            f"Current Cost: ${cost:.6f}",
            f"Threshold: ${threshold:.6f}",
            f"Over Budget by: ${cost - threshold:.6f}" if cost > threshold else "",
            "",
            "Top Cost Drivers:",
        ]

        for item in alert_result['details']['breakdown_by_model'][:5]:
            provider = item['provider']
            model = item['model']
            cost = item['cost']
            requests = item['requests']
            lines.append(f"  - {provider}/{model}: ${cost:.6f} ({requests} requests)")

        return "\n".join(lines)

    def _send_log_alert(self, alert_result: Dict[str, Any], message: str):
        """Send alert to logger."""
        level = alert_result['alert_level']

        if level == self.ALERT_LEVEL_CRITICAL:
            logger.error(f"\n{message}\n")
        elif level == self.ALERT_LEVEL_WARNING:
            logger.warning(f"\n{message}\n")
        else:
            logger.info(f"\n{message}\n")

    def _send_email_alert(self, alert_result: Dict[str, Any], message: str):
        """Send alert via email (placeholder for implementation)."""
        # TODO: Implement email notification
        logger.info(f"Email alert would be sent: {alert_result['alert_level']}")
        pass

    def _send_webhook_alert(self, alert_result: Dict[str, Any], message: str):
        """Send alert via webhook (placeholder for implementation)."""
        # TODO: Implement webhook notification
        logger.info(f"Webhook alert would be sent: {alert_result['alert_level']}")
        pass

    def _is_on_cooldown(self, alert_key: str) -> bool:
        """Check if alert is on cooldown."""
        from django.core.cache import cache
        cache_key = self._alert_cache_key.format(alert_type=alert_key, period='cooldown')
        return cache.get(cache_key, False)

    def _set_cooldown(self, alert_key: str):
        """Set alert cooldown."""
        from django.core.cache import cache
        cache_key = self._alert_cache_key.format(alert_type=alert_key, period='cooldown')
        cache.set(cache_key, True, timeout=self.ALERT_COOLDOWN)

    @classmethod
    def get_alert_summary(cls, days: int = 7) -> Dict[str, Any]:
        """
        Get summary of cost alerts for the past N days.

        Args:
            days: Number of days to look back

        Returns:
            Summary with costs by period and alert status
        """
        from .models import LLMUsageLog
        from django.utils import timezone
        from datetime import timedelta

        service = cls()
        summary = {
            'days': days,
            'periods': {}
        }

        # Check each period
        for period in [cls.PERIOD_DAILY, cls.PERIOD_WEEKLY]:
            alert_result = service.check_cost_thresholds(period=period)
            summary['periods'][period] = alert_result

        # Daily breakdown
        daily_costs = []
        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).date()
            cost = LLMUsageLog.get_daily_cost(date)

            daily_alert = service.check_cost_thresholds(
                period=cls.PERIOD_DAILY,
                thresholds={cls.ALERT_LEVEL_WARNING: service.DEFAULT_THRESHOLDS[cls.PERIOD_DAILY]}
            )

            # Override current_cost for this specific date
            daily_alert['current_cost'] = round(cost, 6)
            daily_alert['date'] = date.isoformat()
            daily_costs.append(daily_alert)

        summary['daily_costs'] = list(reversed(daily_costs))

        return summary
