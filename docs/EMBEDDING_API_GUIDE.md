# Embedding API 配置指南

本系统已集成硅基流动API作为默认Embedding服务，支持灵活切换到智谱AI、通义千问等其他OpenAI兼容的API。

## 🎯 已支持的API提供商

| 提供商 | 模型 | 维度 | 状态 | 推荐场景 |
|--------|------|------|------|----------|
| **硅基流动 SiliconFlow** | BGE-large-zh-v1.5 | 1024 | ✅ 默认 | **中文语义匹配（推荐）** |
| **智谱AI ZhipuAI** | embedding-2 | 1024 | ✅ 已集成 | 商业应用 |
| **阿里通义 Qwen** | text-embedding-v3 | 1536 | ✅ 已集成 | 企业级应用 |

## 📋 快速开始

### 1. 获取API密钥

#### 硅基流动（推荐，免费额度）
- 官网：https://siliconflow.cn/
- 注册账号并创建API Key
- 新用户有免费调用额度

#### 智谱AI（有免费额度）
- 官网：https://open.bigmodel.cn/
- 注册并获取 API Key
- 新用户有免费额度

#### 阿里通义千问
- 官网：https://dashscope.aliyuncs.com/
- 阿里云账号登录
- 开通灵积平台服务

### 2. 配置环境变量

```bash
# 生成加密密钥（首次配置时）
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 设置环境变量
export ENCRYPTION_KEY="your-generated-encryption-key"
export SILICONFLOW_API_KEY="sk-your-siliconflow-key"
```

### 3. 初始化配置

```bash
cd backend
python manage.py init_embedding_config
```

这会创建3个预配置的模型：
- `siliconflow-bge-large-zh` （默认，已激活）
- `zhipuai-embedding-2`
- `qwen-embedding-v1`

### 4. 配置API Key

#### 方法1：通过Web界面（推荐）
访问 http://localhost:8000/admin
1. 登录管理后台
2. 进入 "Embedding Model Configs"
3. 点击对应的配置
4. 填入 API Key
5. 保存

#### 方法2：通过API
```bash
curl -X PUT http://localhost:8000/api/v1/configs/{config_id}/ \
  -H "Content-Type: application/json" \
  -d '{
    "api_key_encrypted": "sk-your-api-key"
  }'
```

#### 方法3：通过测试脚本
```bash
export SILICONFLOW_API_KEY="sk-your-key"
python test_embedding.py siliconflow
```

### 5. 测试连接

```bash
# 方法1：使用测试脚本
python test_embedding.py siliconflow

# 方法2：通过API
curl -X POST http://localhost:8000/api/v1/configs/{config_id}/test_connection/

# 方法3：通过Django shell
python manage.py shell
>>> from apps.embeddings.services import EmbeddingService
>>> service = EmbeddingService()
>>> service.test_connection()
```

## 🔄 切换API提供商

### 切换到智谱AI

```bash
# 1. 设置智谱API Key
export ZHIPUAI_API_KEY="your-zhipuai-key"

# 2. 测试连接
python test_embedding.py zhipuai

# 3. 在数据库中设置为默认
python manage.py shell
>>> from apps.embeddings.models import EmbeddingModelConfig
>>> siliconflow = EmbeddingModelConfig.objects.get(model_name='siliconflow-bge-large-zh')
>>> zhipuai = EmbeddingModelConfig.objects.get(model_name='zhipuai-embedding-2')
>>> siliconflow.is_default = False
>>> zhipuai.is_default = True
>>> siliconflow.save()
>>> zhipuai.save()
```

### 切换到阿里通义千问

```bash
# 1. 设置通义API Key
export DASHSCOPE_API_KEY="sk-your-qwen-key"

# 2. 通过API配置
curl -X PUT http://localhost:8000/api/v1/configs/qwen-embedding-v1-id/ \
  -H "Content-Type: application/json" \
  -d '{"api_key_encrypted": "sk-your-key", "is_default": true}'
```

## 🧪 测试API功能

### 测试文本编码
```bash
python manage.py shell
>>> from apps.embeddings.services import EmbeddingServiceFactory
>>> provider = EmbeddingServiceFactory.get_default_provider()
>>> embeddings = provider.encode(['产品能力匹配', '智能推荐'])
>>> print(f"维度: {len(embeddings[0])}")
>>> print(f"向量: {embeddings[0][:5]}")
```

### 计算相似度
```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

sim = cosine_similarity(embeddings[0], embeddings[1])
print(f"相似度: {sim:.4f}")
```

### 测试产品功能匹配
```bash
curl -X POST http://localhost:8000/api/v1/features/generate_embeddings_batch/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "your-product-id"
  }'
```

## 📊 API提供商对比

### 硅基流动 SiliconFlow
**优点：**
- ✅ 新用户免费额度大
- ✅ 完全兼容OpenAI API
- ✅ 响应速度快
- ✅ 支持BGE模型（中文效果好）

**缺点：**
- ❌ 需要注册账号

**适用场景：**
- 中小规模应用
- 对成本敏感的项目
- 中文语义匹配

### 智谱AI ZhipuAI
**优点：**
- ✅ 国产大模型厂商
- ✅ 稳定可靠
- ✅ 有免费额度
- ✅ 技术支持好

**缺点：**
- ❌ 价格稍高
- ❌ API调用有频率限制

**适用场景：**
- 商业项目
- 需要技术支持
- 生产环境

### 阿里通义千问
**优点：**
- ✅ 阿里云生态完善
- ✅ 企业级稳定性
- ✅ 多语言支持

**缺点：**
- ❌ 价格较高
- ❌ 需要阿里云账号

**适用场景：**
- 企业级应用
- 已使用阿里云服务
- 对稳定性要求高

## 🔧 高级配置

### 自定义其他OpenAI兼容API

```python
from apps.embeddings.models import EmbeddingModelConfig

# 创建自定义配置
config = EmbeddingModelConfig.objects.create(
    model_name='my-custom-embeddings',
    model_type='openai-compatible',
    provider='openai-compatible',
    provider_name='other',
    base_url='https://your-api-endpoint.com/v1',
    dimension=768,
    model_params={'model': 'your-model-name'},
    is_active=True
)

# 设置API Key
config.set_api_key('sk-your-key')
config.save()
```

### 批量生成产品功能嵌入

```bash
# 生成所有产品的功能嵌入
python manage.py shell
>>> from apps.products.models import Product, Feature
>>> from apps.embeddings.services import EmbeddingService
>>>
>>> service = EmbeddingService()
>>> product = Product.objects.first()
>>>
>>> for feature in product.features.all():
>>>     embedding = service.generate_embedding(feature.description)
>>>     # 保存嵌入...
```

## 📝 配置参考

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `ENCRYPTION_KEY` | API密钥加密密钥 | ✅ 是 |
| `SILICONFLOW_API_KEY` | 硅基流动API密钥 | ⚠️ 可选 |
| `ZHIPUAI_API_KEY` | 智谱AI API密钥 | ⚠️ 可选 |
| `DASHSCOPE_API_KEY` | 通义千问API密钥 | ⚠️ 可选 |

### 数据库配置字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `model_name` | String | 模型名称（唯一） |
| `model_type` | Choice | openai-compatible |
| `provider_name` | Choice | siliconflow/zhipuai/qwen/other |
| `base_url` | URL | API基础URL |
| `api_key_encrypted` | Text | 加密的API密钥 |
| `dimension` | Integer | 嵌入向量维度 |
| `model_params` | JSON | 模型参数 |
| `is_active` | Boolean | 是否激活 |
| `is_default` | Boolean | 是否默认 |

## ❓ 常见问题

### Q1: 如何获取硅基流动的免费额度？
A: 访问 https://siliconflow.cn/ 注册账号，新用户会获得免费调用额度。

### Q2: 可以同时使用多个API提供商吗？
A: 可以！系统支持配置多个提供商，通过 `is_default` 字段指定默认使用哪个。

### Q3: 如何监控API调用次数？
A: 可以在各个提供商的控制台查看API调用统计。

### Q4: 本地部署的BGE模型和API有什么区别？
A: 本地部署完全免费但需要服务器资源；API方式按调用次数收费但无需维护。

### Q5: 切换API会影响已有数据吗？
A: 不会。已生成的嵌入向量会保留，新数据使用新的API生成。

## 🎉 下一步

配置完成后，你可以：
1. ✅ 批量生成产品功能嵌入
2. ✅ 使用智能匹配功能
3. ✅ 通过API添加新的匹配需求
4. ✅ 导出匹配结果报告

详细使用方法请参考：[PROJECT_DELIVERY.md](PROJECT_DELIVERY.md)
