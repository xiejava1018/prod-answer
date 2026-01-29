# LLM Module Installation Notes

## Required Dependencies

Add the following to `backend/requirements.txt`:

```
# LLM Provider Dependencies
openai>=1.0.0
aiohttp>=3.8.0
tenacity>=8.2.0
tiktoken>=0.5.0
```

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

The LLM module will require a database model (`LLMModelConfig`) to be created in Task 1.2. Until then, you can use dict-based configuration:

```python
from apps.llm.services import LLMProviderFactory

config = {
    'provider': 'openai',
    'model_name': 'gpt-4o-mini',
    'api_key': 'your-api-key',
    'max_tokens': 2000,
    'temperature': 0.7,
}

provider = LLMProviderFactory.create_provider(config)
```

## API Keys

You'll need API keys for the providers you want to use:

- **OpenAI**: Get from https://platform.openai.com/api-keys
- **ZhipuAI**: Get from https://open.bigmodel.cn/
- **Qwen**: Get from https://dashscope.aliyun.com/

Store API keys in `.env` file:
```
OPENAI_API_KEY=sk-...
ZHIPUAI_API_KEY=...
QWEN_API_KEY=sk-...
```

## Next Steps

1. Wait for Task 1.2 to create the `LLMModelConfig` database model
2. Configure LLM providers via Django admin or API
3. Integrate with matching system in Task 1.4
