# API 文档

## 认证

目前使用Session认证,未来将支持JWT。

## 基础响应格式

所有API响应使用统一的JSON格式:

**成功响应:**
```json
{
  "id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  ...
}
```

**错误响应:**
```json
{
  "error": "错误信息",
  "details": {...}
}
```

---

## 产品管理 API

### 获取产品列表

```
GET /api/v1/products/
```

**查询参数:**
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `search`: 搜索关键词
- `category`: 分类过滤

**响应:**
```json
{
  "count": 100,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "产品名称",
      "version": "1.0.0",
      "description": "产品描述",
      "vendor": "厂商",
      "category": "分类",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 创建产品

```
POST /api/v1/products/
```

**请求体:**
```json
{
  "name": "产品名称",
  "version": "1.0.0",
  "description": "产品描述",
  "vendor": "厂商",
  "category": "分类"
}
```

### 获取产品详情

```
GET /api/v1/products/{id}/
```

### 更新产品

```
PUT /api/v1/products/{id}/
```

### 删除产品

```
DELETE /api/v1/products/{id}/
```

---

## 功能特性 API

### 获取产品功能列表

```
GET /api/v1/products/{product_id}/features/
```

**响应:**
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "product_id": "uuid",
      "feature_code": "FEAT-001",
      "feature_name": "功能名称",
      "description": "功能描述",
      "category": "功能分类",
      "subcategory": "子分类",
      "importance_level": 8,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 添加功能

```
POST /api/v1/products/{product_id}/features/
```

**请求体:**
```json
{
  "feature_name": "功能名称",
  "description": "功能描述",
  "category": "分类",
  "subcategory": "子分类",
  "importance_level": 8
}
```

### 批量导入功能

```
POST /api/v1/features/batch/
```

**请求体:**
```json
{
  "product_id": "uuid",
  "features": [
    {
      "feature_name": "功能1",
      "description": "描述1",
      "category": "分类1"
    },
    {
      "feature_name": "功能2",
      "description": "描述2",
      "category": "分类2"
    }
  ]
}
```

---

## 需求管理 API

### 创建需求 (文本)

```
POST /api/v1/requirements/
```

**请求体:**
```json
{
  "requirement_text": "需求1\n需求2\n需求3",
  "requirement_type": "text",
  "created_by": "用户名"
}
```

### 上传需求文件

```
POST /api/v1/requirements/upload/
```

**请求:** multipart/form-data
- `file`: 文件对象
- `created_by`: 用户名 (可选)

**响应:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "requirement_type": "file",
  "source_file_name": "requirements.xlsx",
  "status": "pending",
  "total_items": 10
}
```

### 获取需求详情

```
GET /api/v1/requirements/{id}/
```

### 获取需求明细

```
GET /api/v1/requirements/{id}/items/
```

**响应:**
```json
{
  "requirement_id": "uuid",
  "items": [
    {
      "id": "uuid",
      "item_text": "需求文本",
      "item_order": 0,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## 匹配分析 API

### 执行匹配分析

```
POST /api/v1/matching/analyze
```

**请求体:**
```json
{
  "requirement_id": "uuid",
  "threshold": 0.75,
  "product_ids": ["uuid1", "uuid2"],
  "limit": 5
}
```

**响应:**
```json
{
  "requirement_id": "uuid",
  "status": "completed",
  "summary": {
    "total_items": 10,
    "total_matches": 45,
    "matched": 20,
    "partial_matched": 15,
    "unmatched": 5
  },
  "processing_time": 2.5
}
```

### 获取匹配结果

```
GET /api/v1/matching/results/{requirement_id}/
```

**响应:**
```json
{
  "requirement_id": "uuid",
  "results": {
    "matched": [
      {
        "requirement_item": "需求文本",
        "feature": "功能名称",
        "product": "产品名称",
        "similarity_score": 0.92,
        "rank": 1
      }
    ],
    "partial_matched": [...],
    "unmatched": [...]
  }
}
```

### 获取匹配摘要

```
GET /api/v1/matching/results/{requirement_id}/summary/
```

**响应:**
```json
{
  "total_items": 10,
  "total_matches": 45,
  "matched": 20,
  "partial_matched": 15,
  "unmatched": 5,
  "avg_similarity": 0.78,
  "max_similarity": 0.95,
  "min_similarity": 0.65
}
```

### 导出匹配报告

```
POST /api/v1/matching/export/{requirement_id}/
```

**请求体:**
```json
{
  "format": "excel",  // or "pdf"
  "include_unmatched": true
}
```

**响应:** 文件下载

---

## Embedding 配置 API

### 获取模型配置列表

```
GET /api/v1/embeddings/configs/
```

**响应:**
```json
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "model_name": "openai-3-small",
      "model_type": "openai",
      "provider": "openai",
      "dimension": 1536,
      "is_active": true,
      "is_default": true
    }
  ]
}
```

### 创建模型配置

```
POST /api/v1/embeddings/configs/
```

**请求体 (OpenAI):**
```json
{
  "model_name": "openai-3-small",
  "model_type": "openai",
  "provider": "openai",
  "api_key": "sk-...",
  "dimension": 1536,
  "model_params": {
    "model": "text-embedding-3-small"
  },
  "is_default": true
}
```

**请求体 (Sentence-Transformers):**
```json
{
  "model_name": "st-mini-lm",
  "model_type": "sentence-transformers",
  "provider": "sentence-transformers",
  "dimension": 384,
  "model_params": {
    "model_path": "all-MiniLM-L6-v2",
    "device": "cpu"
  }
}
```

### 更新配置

```
PUT /api/v1/embeddings/configs/{id}/
```

### 设置默认模型

```
POST /api/v1/embeddings/set-default/{id}/
```

### 测试模型连接

```
POST /api/v1/embeddings/test-connection/{id}/
```

**响应:**
```json
{
  "status": "success",
  "is_connected": true,
  "model_info": {
    "model_name": "openai-3-small",
    "dimension": 1536,
    "provider": "OpenAIEmbeddingProvider"
  }
}
```

### 重新生成向量

```
POST /api/v1/features/generate-embeddings/
```

**请求体:**
```json
{
  "feature_ids": ["uuid1", "uuid2"],
  "config_id": "uuid"
}
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

## 分页

所有列表API支持分页:

**请求参数:**
- `page`: 页码
- `page_size`: 每页数量 (最大: 100)

**响应头:**
```
Link: <URL>; rel="next", <URL>; rel="previous"
```

---

## 限流

默认限制: 每用户每分钟100次请求

超过限制返回 429 状态码。
