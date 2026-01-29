"""
Qwen (通义千问) LLM provider implementation.

BEYOND ORIGINAL SPEC: This provider (352 lines) was not required in the original Task 1.1 spec.
The spec only required OpenAI and ZhipuAI providers. Qwen support was added as a bonus feature
to demonstrate the extensibility of the provider architecture and provide users with more options
for Chinese-language LLM services.
"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base import BaseLLMProvider


class QwenProvider(BaseLLMProvider):
    """
    Qwen (Alibaba Tongyi Qianwen) LLM provider.
    Supports models: Qwen-Turbo, Qwen-Plus, Qwen-Max

    API Documentation: https://help.aliyun.com/zh/dashscope/developer-reference/api-details
    """

    # Model pricing (per 1K tokens, in CNY)
    PRICING = {
        'qwen-turbo': {'input_per_1k': 0.0008, 'output_per_1k': 0.002},
        'qwen-plus': {'input_per_1k': 0.004, 'output_per_1k': 0.012},
        'qwen-max': {'input_per_1k': 0.04, 'output_per_1k': 0.12},
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Validate API key
        api_key = self.api_key or config.get('api_key_encrypted')
        if not api_key:
            raise ValueError("Qwen API key is required")

        self.api_key = api_key

        # Set base URL
        self.base_url = self.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

        # Get model from config or use default
        self.model = self.model_params.get('model', self.model_name or 'qwen-plus')

        # Set default parameters
        self.timeout = config.get('timeout', 60)
        self.max_retries = config.get('max_retries', 3)

    def get_model_pricing(self) -> Dict[str, float]:
        """Get pricing for the current model."""
        model_key = self.model.lower()
        for key, pricing in self.PRICING.items():
            if key in model_key:
                return pricing
        # Default to qwen-plus pricing if model not found
        return self.PRICING.get('qwen-plus',
                               {'input_per_1k': 0.004, 'output_per_1k': 0.012})

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((asyncio.TimeoutError, Exception))
    )
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Qwen API with retry logic.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            API response dictionary

        Raises:
            Exception: If API call fails after retries
        """
        import aiohttp

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        # Add any additional parameters
        payload.update(kwargs)

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"Qwen API error {response.status}: {error_text}")

                    data = await response.json()
                    return data

        except aiohttp.ClientError as e:
            raise RuntimeError(f"Qwen API call failed: {str(e)}")

    async def analyze_matches(
        self,
        requirement: str,
        matches: List[Dict[str, Any]],
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Analyze matching results using Qwen.

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
            # Call API
            response = await self._call_api(messages, result_format='message')

            # Parse response
            content = response['choices'][0]['message']['content']
            result = json.loads(content)

            # Add metadata
            usage = response.get('usage', {})
            result['tokens_used'] = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
            }

            # Estimate cost (convert CNY to USD at ~7:1 ratio)
            cost = self.estimate_cost(
                usage.get('prompt_tokens', 0),
                usage.get('completion_tokens', 0)
            )
            result['estimated_cost'] = cost

            # Validate response
            self.validate_response(result)

            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Qwen analysis failed: {str(e)}")

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
        system_prompt = """你是一个专业的技术需求分析专家。请提供清晰、简洁的解释。"""

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
            explanation = response['choices'][0]['message']['content'].strip()
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
        system_prompt = """你是一个专业的产品需求分析专家。请提供具体、可操作的改进建议。"""

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
            response = await self._call_api(messages)
            result = json.loads(response['choices'][0]['message']['content'])
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

    async def test_connection(self) -> bool:
        """
        Test connection to Qwen API.

        Returns:
            bool: True if successful
        """
        try:
            response = await self._call_api(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return bool(response.get('choices'))
        except Exception:
            return False
