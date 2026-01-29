# LLM Configuration Management API Documentation

## Base URL
```
http://localhost:8000/api/v1/llm/
```

## Authentication
All endpoints require authentication. Use token-based authentication.

```bash
# Set token in headers
Authorization: Token <your_token_here>
```

## Endpoints

### 1. List LLM Configurations
```http
GET /api/v1/llm/configs/
```

**Query Parameters:**
- `is_active` (optional): Filter by active status (`true`/`false`)
- `provider` (optional): Filter by provider type (`openai`, `zhipuai`, `qwen`)

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "provider": "openai",
      "provider_display": "OpenAI",
      "model_name": "gpt-4o-mini",
      "base_url": "",
      "has_api_key": true,
      "api_key_masked": "****wxyz",
      "max_tokens": 2000,
      "temperature": 0.7,
      "model_params": {},
      "is_active": true,
      "is_default": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Permission:** Any authenticated user

---

### 2. Create LLM Configuration
```http
POST /api/v1/llm/configs/
```

**Request Body:**
```json
{
  "provider": "openai",
  "model_name": "gpt-4o-mini",
  "api_key_encrypted": "sk-your-api-key-here",
  "base_url": "",
  "max_tokens": 2000,
  "temperature": 0.7,
  "model_params": {},
  "is_active": true,
  "is_default": false
}
```

**Field Validations:**
- `provider`: Must be one of `openai`, `zhipuai`, `qwen`
- `model_name`: Required, non-empty string
- `api_key_encrypted`: Required
- `temperature`: Must be between 0.0 and 2.0
- `max_tokens`: Must be positive integer

**Permission:** Admin only

---

### 3. Get LLM Configuration Details
```http
GET /api/v1/llm/configs/{id}/
```

**Response:** Same as list endpoint (single object)

**Permission:** Any authenticated user

---

### 4. Update LLM Configuration
```http
PUT /api/v1/llm/configs/{id}/
```

**Request Body:** Same as create endpoint

**Permission:** Admin only

---

### 5. Partial Update LLM Configuration
```http
PATCH /api/v1/llm/configs/{id}/
```

**Request Body:** Partial fields to update

**Permission:** Admin only

---

### 6. Delete LLM Configuration
```http
DELETE /api/v1/llm/configs/{id}/
```

**Permission:** Admin only

---

### 7. Test LLM Connection
```http
POST /api/v1/llm/configs/{id}/test/
```

**Response (Success):**
```json
{
  "status": "success",
  "is_connected": true,
  "response_time_ms": 1234,
  "model_info": {
    "model_name": "gpt-4o-mini",
    "provider": "OpenAIProvider",
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

**Response (Failure):**
```json
{
  "status": "failed",
  "is_connected": false,
  "response_time_ms": 567,
  "error": "Connection test failed - please check API key and model name"
}
```

**Permission:** Any authenticated user

---

### 8. Set Default Configuration
```http
POST /api/v1/llm/configs/{id}/set_default/
```

**Response:**
```json
{
  "status": "success",
  "message": "gpt-4o-mini is now the default model for openai",
  "config": { ... }
}
```

**Permission:** Admin only

---

### 9. Get Active Providers
```http
GET /api/v1/llm/configs/active_providers/
```

**Response:**
```json
{
  "count": 2,
  "providers": [ ... ]
}
```

**Permission:** Any authenticated user

---

### 10. Get Default Provider
```http
GET /api/v1/llm/configs/default_provider/
```

**Response:** Single configuration object (default for any provider)

**Permission:** Any authenticated user

---

### 11. List Analysis Results
```http
GET /api/v1/llm/analysis-results/
```

**Query Parameters:**
- `requirement_item_id` (optional): Filter by requirement item
- `feature_id` (optional): Filter by feature
- `is_valid` (optional): Filter by validity (`true`/`false`/`null`)
- `min_confidence` (optional): Minimum confidence score (0-1)

**Response:**
```json
{
  "count": 100,
  "results": [
    {
      "id": "uuid",
      "requirement_item": "uuid",
      "requirement_text": "User requirement text",
      "feature": "uuid",
      "feature_name": "Feature name",
      "match_reason": "Explanation...",
      "keywords_from_requirement": ["key1", "key2"],
      "keywords_from_feature": ["key1", "key2"],
      "is_valid_match": true,
      "confidence_score": 0.95,
      "llm_provider": "openai",
      "provider_display": "OpenAI",
      "llm_model": "gpt-4o-mini",
      "prompt_tokens": 100,
      "completion_tokens": 50,
      "total_tokens": 150,
      "analysis_metadata": {},
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Permission:** Any authenticated user

---

### 12. Get Analysis Result Details
```http
GET /api/v1/llm/analysis-results/{id}/
```

**Response:** Same as list endpoint (single object)

**Permission:** Any authenticated user

---

### 13. Get Analysis Statistics
```http
GET /api/v1/llm/analysis-results/stats/
```

**Response:**
```json
{
  "total_results": 1000,
  "valid_matches": 700,
  "invalid_matches": 200,
  "inconclusive": 100,
  "average_confidence": 0.82,
  "provider_distribution": [
    {"llm_provider": "openai", "count": 600},
    {"llm_provider": "zhipuai", "count": 400}
  ]
}
```

**Permission:** Any authenticated user

---

## Security Features

### API Key Masking
- API keys are never returned in API responses
- Only `api_key_masked` field shows last 4 characters
- Use `has_api_key` boolean to check if key is configured

### Encryption
- API keys are encrypted at rest using Fernet encryption
- Encryption key stored in `.env` file (`ENCRYPTION_KEY`)
- Decryption only happens in-memory when needed

### Permission Control
- **Read operations** (GET): Any authenticated user
- **Write operations** (POST, PUT, PATCH, DELETE): Admin only
- **Test connection**: Any authenticated user (safe operation)

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"],
  "non_field_errors": ["General error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "error": "Error message details"
}
```

---

## Testing with curl

### Create a config (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/llm/configs/ \
  -H "Authorization: Token <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4o-mini",
    "api_key_encrypted": "sk-your-key-here",
    "max_tokens": 2000,
    "temperature": 0.7
  }'
```

### List configs (Any user)
```bash
curl -X GET http://localhost:8000/api/v1/llm/configs/ \
  -H "Authorization: Token <user_token>"
```

### Test connection (Any user)
```bash
curl -X POST http://localhost:8000/api/v1/llm/configs/<id>/test/ \
  -H "Authorization: Token <user_token>"
```

---

## Integration with Matching System

Once LLM configs are created, they can be used in the matching workflow:

1. **Configure default LLM model** in Admin or via API
2. **Match analysis** will automatically use the default model
3. **Results are cached** in `LLMAnalysisResult` for audit trail
4. **Cost tracking** via token usage in analysis results

---

## Notes

- **Provider Support**: OpenAI, ZhipuAI (智谱AI), Qwen (通义千问)
- **Custom Providers**: Can be registered via `LLMProviderFactory.register_provider()`
- **Caching**: Provider instances are cached for performance
- **Model Parameters**: Additional params can be passed via `model_params` JSON field
- **Multi-provider**: Different providers can be configured simultaneously
