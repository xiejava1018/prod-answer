# 产品能力匹配系统

一个基于语义相似度的智能产品能力匹配系统,支持将产品功能特性录入知识库,通过AI语义匹配自动分析用户需求是否能够被产品满足。

## 功能特性

- **知识库管理**: 录入和管理产品功能特性
- **多格式支持**: 支持Excel、CSV、Word文件上传解析需求
- **语义匹配**: 基于Embedding向量的智能语义相似度匹配
- **多模型支持**: 可配置OpenAI、Sentence-Transformers等多种Embedding模型
- **可视化结果**: 直观展示满足项、部分满足项和不满足项

## 技术栈

### 后端
- Django 4.2
- Django REST Framework
- PostgreSQL + pgvector (向量存储)
- OpenAI API / Sentence-Transformers
- Celery (异步任务)

### 前端
- Vue3 + TypeScript
- Element Plus
- Pinia (状态管理)
- Axios

## 项目结构

```
prod-answer/
├── backend/                    # Django后端
│   ├── config/                 # Django配置
│   ├── apps/                   # 应用模块
│   │   ├── core/              # 核心应用
│   │   ├── products/          # 产品管理
│   │   ├── embeddings/        # Embedding服务
│   │   ├── matching/          # 匹配引擎
│   │   ├── requirements/      # 需求管理
│   │   └── reports/           # 报告导出
│   ├── manage.py
│   └── requirements.txt
├── frontend/                   # Vue3前端
└── README.md
```

## 快速开始

### 1. 环境准备

确保已安装以下软件:
- Python 3.9+
- PostgreSQL 12+ (with pgvector extension)
- Node.js 16+
- Redis (可选,用于Celery)

### 2. 数据库配置

```bash
# 创建PostgreSQL数据库
createdb prod_answer

# 启用pgvector扩展
psql -d prod_answer -c "CREATE EXTENSION vector;"
```

### 3. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件,配置数据库和API密钥

# 运行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

### 4. 配置Embedding模型

访问Django Admin管理后台 (http://localhost:8000/admin):

1. 创建Embedding模型配置:
   - OpenAI: 填写API Key
   - Sentence-Transformers: 配置本地模型路径

2. 设置默认模型

### 5. 使用API

#### 创建产品

```bash
POST /api/v1/products/
{
  "name": "产品名称",
  "version": "1.0.0",
  "description": "产品描述",
  "category": "分类"
}
```

#### 添加功能特性

```bash
POST /api/v1/products/{product_id}/features/
{
  "feature_name": "功能名称",
  "description": "功能描述",
  "category": "功能分类"
}
```

#### 创建需求并匹配

```bash
POST /api/v1/requirements/
{
  "requirement_text": "需求1\n需求2\n需求3",
  "requirement_type": "text"
}

POST /api/v1/matching/analyze
{
  "requirement_id": "uuid",
  "threshold": 0.75
}
```

## 核心模块说明

### Embedding服务

支持多种Embedding模型提供商:

- **OpenAI**: `text-embedding-3-small`, `text-embedding-3-large`
- **Sentence-Transformers**: 本地开源模型如 `all-MiniLM-L6-v2`

配置方式:
```python
# 通过Django Admin或API配置
{
  "model_name": "openai-3-small",
  "model_type": "openai",
  "provider": "openai",
  "dimension": 1536,
  "is_default": true
}
```

### 匹配算法

使用余弦相似度计算需求与功能的匹配度:

- **完全匹配**: 相似度 ≥ 0.85
- **部分匹配**: 0.75 ≤ 相似度 < 0.85
- **不匹配**: 相似度 < 0.75

阈值可配置。

### 文件解析器

支持多种文件格式:

- **Excel** (.xlsx, .xls)
- **CSV** (.csv)
- **Word** (.docx)

自动提取需求文本,支持表格和段落。

## API接口文档

详细的API文档请参考: [API.md](docs/API.md)

主要端点:

```
产品管理:
- GET    /api/v1/products/
- POST   /api/v1/products/
- GET    /api/v1/products/{id}/features/
- POST   /api/v1/products/{id}/features/

需求管理:
- POST   /api/v1/requirements/
- GET    /api/v1/requirements/{id}/

匹配分析:
- POST   /api/v1/matching/analyze
- GET    /api/v1/matching/results/{req_id}/

Embedding配置:
- GET    /api/v1/embeddings/configs/
- POST   /api/v1/embeddings/configs/
- POST   /api/v1/embeddings/test-connection/{id}/
```

## 开发指南

### 添加新的Embedding Provider

1. 创建新的provider类继承 `BaseEmbeddingProvider`:
```python
from apps.embeddings.providers.base import BaseEmbeddingProvider

class MyProvider(BaseEmbeddingProvider):
    def encode(self, texts):
        # 实现编码逻辑
        pass

    def test_connection(self):
        # 实现测试逻辑
        pass
```

2. 注册到工厂:
```python
from apps.embeddings.services import EmbeddingServiceFactory

EmbeddingServiceFactory.register_provider('my-provider', MyProvider)
```

### 添加新的文件解析器

1. 继承 `BaseFileParser`:
```python
from apps.requirements.parsers.base import BaseFileParser

class MyParser(BaseFileParser):
    def parse(self, file_path):
        # 实现解析逻辑
        pass
```

2. 注册到服务:
```python
from apps.requirements.services import FileParserService

FileParserService.PARSERS['mime/type'] = MyParser
```

## 部署

### 生产环境配置

1. 设置环境变量:
```bash
export DEBUG=False
export ALLOWED_HOSTS=yourdomain.com
export DB_PASSWORD=secure_password
```

2. 收集静态文件:
```bash
python manage.py collectstatic
```

3. 使用WSGI服务器 (Gunicorn):
```bash
gunicorn config.wsgi:application
```

4. 配置Nginx作为反向代理

### Docker部署

TODO: 添加Docker配置

## 性能优化

- 使用pgvector的IVFFlat索引加速向量搜索
- 配置Celery异步处理耗时的embedding生成
- 使用Redis缓存频繁访问的配置
- 批量处理提高效率

## 故障排查

### pgvector相关问题

确保PostgreSQL安装了pgvector扩展:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Embedding生成失败

检查API密钥配置和网络连接:
```bash
# 测试OpenAI连接
curl https://api.openai.com/v1/embeddings
```

## 贡献指南

欢迎提交Issue和Pull Request!

## 许可证

MIT License

## 联系方式

项目维护者: [Your Name]
Email: [Your Email]

---

**注意**: 本系统需要配置OpenAI API密钥或本地Embedding模型才能正常使用语义匹配功能。
