"""
OpenAI LLM provider implementation.
"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider.
    Supports models: GPT-4o, GPT-4o-mini, GPT-3.5-turbo, GPT-4-turbo

    NOTE: Streaming support (流式响应) is intentionally deferred to a future task.
    The current implementation uses non-streaming requests for simplicity and reliability.
    Streaming can be added by implementing analyze_matches_stream() using OpenAI's
    stream=True parameter and yielding chunks as they arrive.
    """

    # Model pricing (per 1K tokens, in USD)
    PRICING = {
        'gpt-4o': {'input_per_1k': 0.005, 'output_per_1k': 0.015},
        'gpt-4o-mini': {'input_per_1k': 0.00015, 'output_per_1k': 0.0006},
        'gpt-3.5-turbo': {'input_per_1k': 0.0005, 'output_per_1k': 0.0015},
        'gpt-4-turbo': {'input_per_1k': 0.01, 'output_per_1k': 0.03},
        'gpt-4': {'input_per_1k': 0.03, 'output_per_1k': 0.06},
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Initialize OpenAI client
        api_key = self.api_key or config.get('api_key_encrypted')
        if not api_key:
            raise ValueError("OpenAI API key is required")

        client_kwargs = {'api_key': api_key}
        if self.base_url:
            client_kwargs['base_url'] = self.base_url

        self.client = AsyncOpenAI(**client_kwargs)

        # Get model from config or use default
        self.model = self.model_params.get('model', self.model_name or 'gpt-4o-mini')

        # Set default parameters
        self.timeout = config.get('timeout', 60)
        self.max_retries = config.get('max_retries', 3)

    def get_model_pricing(self) -> Dict[str, float]:
        """Get pricing for the current model."""
        model_key = self.model.lower()
        for key, pricing in self.PRICING.items():
            if key in model_key:
                return pricing
        # Default to gpt-4o-mini pricing if model not found
        return self.PRICING.get('gpt-4o-mini',
                               {'input_per_1k': 0.00015, 'output_per_1k': 0.0006})

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((asyncio.TimeoutError, Exception))
    )
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Call OpenAI API with retry logic.

        Args:
            messages: List of message dictionaries
            response_format: Optional response format (e.g., {"type": "json_object"})

        Returns:
            OpenAI API response

        Raises:
            Exception: If API call fails after retries
        """
        kwargs = {
            'model': self.model,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'timeout': self.timeout,
        }

        if response_format:
            kwargs['response_format'] = response_format

        try:
            response = await self.client.chat.completions.create(**kwargs)
            return response
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")

    async def analyze_match(
        self,
        requirement_text: str,
        feature_name: str,
        feature_description: str,
        similarity_score: float
    ) -> Dict[str, Any]:
        """
        Analyze a single requirement-feature match using OpenAI.

        Args:
            requirement_text: User requirement text
            feature_name: Feature name
            feature_description: Feature description
            similarity_score: Vector similarity score

        Returns:
            Dictionary with:
                - is_valid_match: bool
                - confidence_score: float
                - match_reason: str
                - keywords_from_requirement: list
                - keywords_from_feature: list
                - similarity_assessment: str
                - suggested_status: str
                - tokens_used: dict
                - estimated_cost: dict
        """
        from ..prompts import SingleMatchAnalysisPrompts

        # Sanitize inputs
        requirement_text = self.sanitize_input(requirement_text)
        feature_description = self.sanitize_input(feature_description)

        # Prepare prompts
        system_prompt = SingleMatchAnalysisPrompts.SYSTEM_PROMPT
        user_prompt = SingleMatchAnalysisPrompts.format_user_prompt(
            requirement_text=requirement_text,
            feature_name=feature_name,
            feature_description=feature_description,
            similarity_score=similarity_score
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Call API with JSON response format
            response = await self._call_api(messages, response_format={"type": "json_object"})

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Add metadata
            result['tokens_used'] = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
            }

            # Estimate cost
            cost = self.estimate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            result['estimated_cost'] = cost

            # Validate response
            template = SingleMatchAnalysisPrompts.get_prompt_template()
            if not template.validate_output(result):
                raise ValueError("LLM response validation failed: missing required fields")

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"OpenAI single match analysis failed: {str(e)}")

    async def analyze_matches_batch(
        self,
        matches_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch analyze multiple requirement-feature matches in a single API call.

        This is MUCH more efficient than calling analyze_match() multiple times:
        - Single API call instead of N calls
        - Better context understanding
        - Reduced network latency
        - Lower cost (fewer prompt tokens overhead)

        Args:
            matches_data: List of dictionaries, each containing:
                - requirement_text: str
                - feature_name: str
                - feature_description: str
                - similarity_score: float

        Returns:
            Dictionary with:
                - results: list of analysis results for each match
                - total_analyzed: int
                - tokens_used: dict
                - estimated_cost: dict
        """
        from ..prompts import BatchMatchAnalysisPrompts

        # Prepare batch prompt
        system_prompt = BatchMatchAnalysisPrompts.SYSTEM_PROMPT
        user_prompt = BatchMatchAnalysisPrompts.format_user_prompt(matches_data)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Call API with JSON response format
            response = await self._call_api(messages, response_format={"type": "json_object"})

            # Parse response
            content = response.choices[0].message.content

            # Try to extract JSON from response (in case there's extra text)
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group(0)

            result = json.loads(content)

            # Add metadata
            result['tokens_used'] = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
            }

            # Estimate cost
            cost = self.estimate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            result['estimated_cost'] = cost

            # Validate response
            if 'results' not in result:
                raise ValueError("LLM response missing 'results' field")

            # Allow small tolerance in result count (LLM might make minor mistakes)
            result_count = len(result.get('results', []))
            expected_count = len(matches_data)
            if abs(result_count - expected_count) > 2:
                raise ValueError(
                    f"LLM returned {result_count} results, "
                    f"expected {expected_count} (tolerance exceeded)"
                )

            # Log warning if counts don't match exactly
            if result_count != expected_count:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"LLM returned {result_count} results, expected {expected_count}. "
                    f"Using available results (tolerance within limit)."
                )

            # Index results by match_index for easy lookup
            indexed_results = {}
            for r in result['results']:
                idx = r.get('match_index')
                if idx is not None:
                    indexed_results[idx] = r

            result['indexed_results'] = indexed_results

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Batch LLM analysis failed: {str(e)}")

    async def analyze_matches(
        self,
        requirement: str,
        matches: List[Dict[str, Any]],
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Analyze matching results using OpenAI.

        Args:
            requirement: User requirement text
            matches: List of match results
            threshold: Similarity threshold used

        Returns:
            Analysis dictionary
        """
        # Sanitize inputs
        requirement = self.sanitize_input(requirement)

        # Prepare prompt
        system_prompt = self._get_analysis_system_prompt()
        user_prompt = self._get_analysis_user_prompt(requirement, matches, threshold)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Call API with JSON response format
            response = await self._call_api(messages, response_format={"type": "json_object"})

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Add metadata
            result['tokens_used'] = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
            }

            # Estimate cost
            cost = self.estimate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            result['estimated_cost'] = cost

            # Validate response
            self.validate_response(result)

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"OpenAI analysis failed: {str(e)}")

    async def generate_explanation(
        self,
        requirement: str,
        feature: Dict[str, Any],
        similarity_score: float
    ) -> str:
        """
        Generate explanation for why a feature matches.

        Args:
            requirement: User requirement text
            feature: Feature dictionary
            similarity_score: Similarity score

        Returns:
            Natural language explanation
        """
        system_prompt = """You are an expert at explaining technical requirements and features.
Provide clear, concise explanations in Chinese."""

        feature_name = feature.get('feature_name', 'Unknown')
        feature_desc = feature.get('feature_description', 'No description')

        user_prompt = f"""请解释为什么以下产品特征与用户需求相匹配：

用户需求：
{requirement}

产品特征：
名称：{feature_name}
描述：{feature_desc}

相似度分数：{similarity_score:.3f}

请提供一个简明的解释（50-100字），说明为什么这个特征匹配或部分匹配用户需求。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self._call_api(messages)
            explanation = response.choices[0].message.content.strip()
            return explanation
        except Exception as e:
            return f"生成解释失败: {str(e)}"

    async def suggest_improvements(
        self,
        requirement: str,
        unmatched_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest improvements for requirement and features.

        Args:
            requirement: User requirement text
            unmatched_features: Features that didn't match

        Returns:
            Dictionary with suggestions
        """
        system_prompt = """You are an expert at refining technical requirements and feature descriptions.
Provide actionable suggestions for improving matching accuracy."""

        features_text = "\n".join([
            f"- {f.get('feature_name', 'Unknown')}: {f.get('feature_description', 'No description')}"
            for f in unmatched_features[:10]
        ])

        user_prompt = f"""以下用户需求未能很好地匹配一些产品特征，请提供改进建议：

用户需求：
{requirement}

未匹配或低分匹配的特征：
{features_text}

请以JSON格式返回：
{{
    "requirement_suggestions": ["建议1", "建议2"],
    "feature_suggestions": {{
        "feature_id_1": ["建议1", "建议2"],
        "feature_id_2": ["建议1"]
    }},
    "general_advice": ["通用建议1", "通用建议2"]
}}

请确保所有建议都具体且可操作。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self._call_api(messages, response_format={"type": "json_object"})
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {
                'requirement_suggestions': [],
                'feature_suggestions': {},
                'general_advice': [f"生成建议失败: {str(e)}"]
            }

    def _get_analysis_system_prompt(self) -> str:
        """Get system prompt for match analysis."""
        return """你是一个专业的产品需求分析专家。你的任务是分析用户需求与产品特征的匹配结果。

请对匹配结果进行深入分析，包括：
1. 整体评估：需求是否得到满足
2. 详细分析：每个匹配的特征如何满足需求
3. 匹配质量：相似度分数是否合理
4. 改进建议：如何提高需求描述的准确性

请始终以JSON格式返回分析结果，包含以下字段：
{
    "summary": "整体分析摘要（1-2句话）",
    "detailed_analysis": [
        {
            "feature_id": "特征ID",
            "feature_name": "特征名称",
            "match_quality": "high/medium/low",
            "explanation": "为什么匹配或不匹配",
            "confidence": 0.95
        }
    ],
    "recommendations": ["建议1", "建议2"],
    "confidence": 0.85
}

评估标准：
- 完全匹配 (similarity >= 0.85): 特征完全满足需求
- 部分匹配 (0.75 <= similarity < 0.85): 特征部分满足需求
- 不匹配 (similarity < 0.75): 特征不满足需求
"""

    def _get_analysis_user_prompt(
        self,
        requirement: str,
        matches: List[Dict[str, Any]],
        threshold: float
    ) -> str:
        """Get user prompt for match analysis."""
        matches_text = self.format_matches_for_prompt(matches)

        return f"""请分析以下用户需求与产品特征的匹配结果：

【用户需求】
{requirement}

【匹配阈值】
{threshold}

【匹配结果】
{matches_text}

【统计信息】
- 总匹配数：{len(matches)}
- 完全匹配：{sum(1 for m in matches if m.get('status') == 'full_match')}
- 部分匹配：{sum(1 for m in matches if m.get('status') == 'partial_match')}
- 不匹配：{sum(1 for m in matches if m.get('status') == 'no_match')}

请提供详细的分析和改进建议。"""

    def count_tokens(self, text: str) -> int:
        """
        More accurate token counting for OpenAI models.
        Uses tiktoken if available, otherwise falls back to estimate.

        Args:
            text: Input text

        Returns:
            Token count
        """
        try:
            import tiktoken
            try:
                encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            # Fall back to parent class estimate
            return super().count_tokens(text)

    async def test_connection(self) -> bool:
        """
        Test connection to OpenAI API.

        Returns:
            bool: True if successful
        """
        try:
            # Use a minimal request for testing
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return bool(response.choices)
        except Exception:
            return False
