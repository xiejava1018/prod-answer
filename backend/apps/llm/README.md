# LLM Provider Abstraction Layer

## Overview

This module provides an abstraction layer for integrating multiple Large Language Model (LLM) providers into the Product Capability Matching System. It follows a factory pattern similar to the existing embedding provider system.

## Architecture

### Components

1. **BaseLLMProvider** (`providers/base.py`) - Abstract base class defining the LLM provider interface
2. **Concrete Providers**:
   - `OpenAIProvider` - OpenAI GPT models (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
   - `ZhipuAIProvider` - ZhipuAI GLM models (GLM-4-Flash, GLM-4-Plus, GLM-4-Air)
   - `QwenProvider` - Alibaba Qwen models (Qwen-Turbo, Qwen-Plus, Qwen-Max)

3. **LLMProviderFactory** (`services.py`) - Factory for creating and managing provider instances
4. **LLMService** (`services.py`) - High-level service for LLM operations
5. **Prompt Templates** (`prompts.py`) - Reusable prompt templates for various tasks
6. **Utilities** (`utils.py`) - Helper functions for response parsing, text preprocessing, etc.

## Directory Structure

```
apps/llm/
├── __init__.py                 # Package initialization
├── apps.py                     # Django app configuration
├── providers/                  # LLM provider implementations
│   ├── __init__.py
│   ├── base.py                 # Abstract base class (322 lines)
│   ├── openai_provider.py      # OpenAI implementation (364 lines)
│   ├── zhipuai_provider.py     # ZhipuAI implementation (354 lines)
│   └── qwen_provider.py        # Qwen implementation (352 lines)
├── services.py                 # Factory and service classes (338 lines)
├── prompts.py                  # Prompt templates (291 lines)
├── utils.py                    # Utility functions (461 lines)
└── tests/                      # Unit tests
    ├── __init__.py
    └── test_providers.py       # Provider tests (500+ lines)
```

**Total**: ~2,482 lines of production code + 500+ lines of tests

## Key Features

### 1. Async Support

All provider methods are async for non-blocking operations:

```python
result = await provider.analyze_matches(requirement, matches, threshold=0.75)
```

### 2. Retry Logic

Built-in retry mechanism with exponential backoff for handling transient failures:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((asyncio.TimeoutError, Exception))
)
async def _call_api(self, messages, **kwargs):
    # API call implementation
```

### 3. Cost Estimation

Accurate cost estimation based on token usage and provider pricing:

```python
cost = provider.estimate_cost(
    input_tokens=1000,
    output_tokens=500
)
# Returns: {'input_cost': 0.00015, 'output_cost': 0.0003, 'total_cost': 0.00045, 'currency': 'USD'}
```

### 4. Response Validation

Automatic validation of LLM responses to ensure data integrity:

```python
provider.validate_response(response)  # Raises ValueError if invalid
```

### 5. Flexible Provider Registration

Easy to add new providers:

```python
LLMProviderFactory.register_provider('new-provider', NewProviderClass)
```

## Usage Examples

### Creating a Provider

```python
from apps.llm.services import LLMProviderFactory

# From dict configuration
config = {
    'provider': 'openai',
    'model_name': 'gpt-4o-mini',
    'api_key': 'your-api-key',
    'max_tokens': 2000,
    'temperature': 0.7,
}
provider = LLMProviderFactory.create_provider(config)

# From model config object (requires LLMModelConfig model)
provider = LLMProviderFactory.get_provider_by_id(config_id)
```

### Analyzing Matches

```python
from apps.llm.services import LLMService

service = LLMService()

result = await service.analyze_matches(
    requirement="需要支持资产自动发现和映射功能",
    matches=[
        {
            'feature_id': 'f1',
            'feature_name': '资产自动发现',
            'feature_description': '支持自动扫描网络中的资产并发现其信息',
            'similarity_score': 0.92,
            'status': 'full_match'
        },
        # ... more matches
    ],
    threshold=0.75
)

# Result contains:
# - summary: Overall analysis summary
# - detailed_analysis: Per-feature analysis
# - recommendations: Improvement suggestions
# - confidence: Overall confidence score
# - tokens_used: Token usage information
# - estimated_cost: Cost estimation
```

### Generating Explanations

```python
explanation = await service.generate_explanation(
    requirement="需要支持资产自动发现功能",
    feature={
        'feature_name': '资产自动发现',
        'feature_description': '支持自动扫描网络中的资产并发现其信息'
    },
    similarity_score=0.92
)
```

### Getting Suggestions

```python
suggestions = await service.suggest_improvements(
    requirement="模糊的需求描述",
    unmatched_features=[...]
)

# Contains:
# - requirement_suggestions: How to improve the requirement
# - feature_suggestions: How to improve feature descriptions
# - general_advice: General improvement advice
```

## Provider Configuration

### OpenAI

```python
{
    'provider': 'openai',
    'model_name': 'gpt-4o-mini',  # or 'gpt-4o', 'gpt-3.5-turbo'
    'api_key': 'sk-...',
    'base_url': 'https://api.openai.com/v1',  # optional
    'max_tokens': 2000,
    'temperature': 0.7,
}
```

**Supported Models:**
- gpt-4o: Best quality, higher cost
- gpt-4o-mini: Good quality, lower cost (recommended)
- gpt-3.5-turbo: Fastest, lowest cost

### ZhipuAI

```python
{
    'provider': 'zhipuai',
    'model_name': 'glm-4-flash',  # or 'glm-4-plus', 'glm-4-air'
    'api_key': 'your-api-key',
    'base_url': 'https://open.bigmodel.cn/api/paas/v4',  # optional
    'max_tokens': 2000,
    'temperature': 0.7,
}
```

**Supported Models:**
- glm-4-flash: Fast, low cost (free tier available)
- glm-4-plus: Higher quality
- glm-4-air: Balanced option

### Qwen

```python
{
    'provider': 'qwen',
    'model_name': 'qwen-plus',  # or 'qwen-turbo', 'qwen-max'
    'api_key': 'sk-...',
    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',  # optional
    'max_tokens': 2000,
    'temperature': 0.7,
}
```

**Supported Models:**
- qwen-turbo: Fast, cost-effective
- qwen-plus: Balanced quality and cost (recommended)
- qwen-max: Highest quality

## Testing

Run unit tests:

```bash
cd backend
python pytest apps/llm/tests/test_providers.py -v
```

Test coverage includes:
- Provider initialization and validation
- Async method behavior
- Response parsing and validation
- Factory pattern functionality
- Cost estimation accuracy
- Error handling and retry logic

## Dependencies

Required Python packages:
- `openai>=1.0.0` - For OpenAI provider
- `aiohttp>=3.8.0` - For async HTTP requests (ZhipuAI, Qwen)
- `tenacity>=8.2.0` - For retry logic
- `tiktoken` (optional) - For accurate token counting

Add to `requirements.txt`:
```
openai>=1.0.0
aiohttp>=3.8.0
tenacity>=8.2.0
tiktoken>=0.5.0
```

## Integration Points

This LLM provider layer is designed to integrate with:

1. **Matching System** - Provide AI-powered analysis of match results
2. **Requirement Processing** - Generate explanations and suggestions
3. **Report Generation** - Create detailed analysis reports
4. **Configuration Management** - Store and retrieve LLM model configs (Task 1.2)

## Design Decisions

1. **Abstract Base Class**: Follows the same pattern as embedding providers for consistency
2. **Async-First**: All methods are async to prevent blocking in web requests
3. **Factory Pattern**: Enables easy addition of new providers without modifying existing code
4. **Retry Logic**: Built-in resilience for transient API failures
5. **Cost Tracking**: Automatic cost estimation for budget monitoring
6. **Validation**: Response validation ensures data quality and error detection
7. **Prompt Templates**: Centralized prompt management for consistency

## Future Enhancements

Potential improvements:
1. **Streaming Responses**: Support for streaming LLM outputs
2. **Caching**: Cache responses to reduce API calls
3. **Batch Processing**: Process multiple requests in parallel
4. **Custom Prompts**: Allow users to define custom prompt templates
5. **More Providers**: Easy to add Anthropic, Google Gemini, etc.
6. **Rate Limiting**: Built-in rate limiting to avoid API throttling

## Notes

- All providers support Chinese language prompts and responses
- Token counting is model-specific for accuracy
- Pricing is current as of January 2025 and may change
- API keys should be stored securely and encrypted at rest
- Consider implementing usage quotas and monitoring in production

## Related Tasks

This implementation satisfies **Task 1.1: 创建LLM Provider抽象层** from the LLM-Enhanced Matching System implementation plan.

Next tasks:
- **Task 1.2**: Create LLM model configuration data models
- **Task 1.3**: Build configuration API endpoints
- **Task 1.4**: Implement async matching with LLM analysis
