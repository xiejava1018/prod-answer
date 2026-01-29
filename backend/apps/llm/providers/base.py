"""
Base class for LLM providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum


class MatchStatus(Enum):
    """Match status enumeration"""
    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    All LLM providers should inherit from this class.

    This provider is designed for analyzing matching results between
    requirements and product features using LLM capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider.

        Args:
            config: Dictionary containing configuration
                - model_name: str, Name of the model
                - api_key: str, API key (if applicable)
                - base_url: str, Base URL for API (if applicable)
                - model_params: dict, Additional model parameters
                - provider: str, Provider name
                - max_tokens: int, Maximum tokens in response
                - temperature: float, Temperature for generation
        """
        self.config = config
        self.model_name = config.get('model_name')
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.model_params = config.get('model_params', {})
        self.provider = config.get('provider', 'unknown')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)

    @abstractmethod
    async def analyze_matches(
        self,
        requirement: str,
        matches: List[Dict[str, Any]],
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Analyze matching results using LLM.

        This method should send the requirement and matched features to the LLM
        and request analysis including:
        - Overall assessment
        - Detailed explanation for each match
        - Suggestions for improvement
        - Confidence scores

        Args:
            requirement: User requirement text
            matches: List of match results with similarity scores
                Each match should contain:
                - feature_id: str
                - feature_name: str
                - feature_description: str
                - similarity_score: float
                - status: str (full_match, partial_match, no_match)
            threshold: Similarity threshold used for matching

        Returns:
            Dictionary containing:
                - summary: str, Overall analysis summary
                - detailed_analysis: List[Dict], Analysis per match
                - recommendations: List[str], List of recommendations
                - confidence: float, Overall confidence score (0-1)
                - raw_response: str, Raw LLM response for debugging
                - tokens_used: dict, Token usage information
        """
        pass

    @abstractmethod
    async def generate_explanation(
        self,
        requirement: str,
        feature: Dict[str, Any],
        similarity_score: float
    ) -> str:
        """
        Generate a natural language explanation for why a feature matches.

        Args:
            requirement: User requirement text
            feature: Feature dictionary with description
            similarity_score: Computed similarity score

        Returns:
            Natural language explanation
        """
        pass

    @abstractmethod
    async def suggest_improvements(
        self,
        requirement: str,
        unmatched_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest how to improve requirement or feature descriptions.

        Args:
            requirement: User requirement text
            unmatched_features: Features that didn't match well

        Returns:
            Dictionary containing:
                - requirement_suggestions: List[str]
                - feature_suggestions: Dict[str, List[str]] (by feature_id)
                - general_advice: List[str]
        """
        pass

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_name: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Estimate API call cost based on token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_name: Optional model name (uses self.model_name if not provided)

        Returns:
            Dictionary containing:
                - input_cost: float, Cost for input tokens
                - output_cost: float, Cost for output tokens
                - total_cost: float, Total estimated cost
                - currency: str, Currency code (default: USD)
        """
        model = model_name or self.model_name

        # Default pricing (should be overridden by subclasses)
        pricing = {
            'input_per_1k': 0.0001,  # $0.0001 per 1K input tokens
            'output_per_1k': 0.0002,  # $0.0002 per 1K output tokens
        }

        # Allow subclasses to override pricing
        pricing.update(self.get_model_pricing())

        input_cost = (input_tokens / 1000) * pricing['input_per_1k']
        output_cost = (output_tokens / 1000) * pricing['output_per_1k']

        return {
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'total_cost': round(input_cost + output_cost, 6),
            'currency': 'USD',
        }

    def get_model_pricing(self) -> Dict[str, float]:
        """
        Get pricing information for the current model.
        Subclasses should override this to provide accurate pricing.

        Returns:
            Dictionary with 'input_per_1k' and 'output_per_1k' keys
        """
        return {
            'input_per_1k': 0.0001,
            'output_per_1k': 0.0002,
        }

    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate LLM response structure and content.

        Args:
            response: Response dictionary from analyze_matches

        Returns:
            bool: True if response is valid

        Raises:
            ValueError: If response structure is invalid
        """
        required_fields = ['summary', 'detailed_analysis', 'confidence']

        for field in required_fields:
            if field not in response:
                raise ValueError(f"Missing required field in response: {field}")

        # Validate confidence is between 0 and 1
        if not isinstance(response['confidence'], (int, float)):
            raise ValueError("Confidence must be a number")

        if not 0 <= response['confidence'] <= 1:
            raise ValueError("Confidence must be between 0 and 1")

        # Validate detailed_analysis is a list
        if not isinstance(response['detailed_analysis'], list):
            raise ValueError("detailed_analysis must be a list")

        return True

    def sanitize_input(self, text: str, max_length: int = 10000) -> str:
        """
        Sanitize input text to prevent injection and limit length.

        Args:
            text: Input text
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            text = str(text)

        # Remove null bytes
        text = text.replace('\x00', '')

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + '...'

        return text.strip()

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        This is a rough estimate (should be overridden by providers with accurate tokenizers).

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token for English
        # For Chinese, ~1.5 characters per token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars

        return int(chinese_chars / 1.5 + other_chars / 4)

    def format_matches_for_prompt(
        self,
        matches: List[Dict[str, Any]],
        max_matches: int = 20
    ) -> str:
        """
        Format match results for inclusion in prompt.

        Args:
            matches: List of match dictionaries
            max_matches: Maximum number of matches to include

        Returns:
            Formatted string for prompt
        """
        formatted = []
        for i, match in enumerate(matches[:max_matches], 1):
            status = match.get('status', 'unknown')
            similarity = match.get('similarity_score', 0.0)
            feature_name = match.get('feature_name', 'Unknown Feature')
            description = match.get('feature_description', 'No description')

            formatted.append(
                f"{i}. {feature_name} (Score: {similarity:.3f}, Status: {status})\n"
                f"   Description: {description}"
            )

        return "\n\n".join(formatted)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Dictionary containing model information
        """
        return {
            'model_name': self.model_name,
            'provider': self.__class__.__name__,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'config': {k: v for k, v in self.config.items()
                      if k not in ['api_key', 'api_key_encrypted']},
        }

    async def test_connection(self) -> bool:
        """
        Test the connection to the LLM service.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Try a simple analysis request
            test_requirement = "测试需求"
            test_matches = [{
                'feature_id': 'test',
                'feature_name': 'Test Feature',
                'feature_description': 'Test description',
                'similarity_score': 0.8,
                'status': 'partial_match'
            }]

            await self.analyze_matches(test_requirement, test_matches)
            return True
        except Exception:
            return False
