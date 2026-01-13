# 快速安装指南

## 系统要求

- Python 3.9+
- PostgreSQL 12+ (with pgvector)
- Redis (可选,用于Celery)
- 8GB+ RAM

## 第一步: 安装PostgreSQL和pgvector

### macOS
```bash
brew install postgresql@14
brew install pgvector

# 或手动安装pgvector
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Ubuntu/Debian
```bash
sudo apt install postgresql-14 postgresql-contrib-pgvector
```

### Windows
下载并安装PostgreSQL,然后使用WSL2安装pgvector

## 第二步: 创建数据库

```bash
# 启动PostgreSQL服务
brew services start postgresql@14  # macOS
sudo systemctl start postgresql   # Linux

# 创建数据库
createdb prod_answer

# 启用pgvector扩展
psql -d prod_answer -c "CREATE EXTENSION vector;"
```

## 第三步: 配置后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 编辑.env文件
nano .env
```

**必需的环境变量:**
```bash
# 数据库
DB_NAME=prod_answer
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-django-secret-key
DEBUG=True

# OpenAI (可选,或使用本地模型)
OPENAI_API_KEY=sk-your-openai-key

# 加密密钥 (生成: from cryptography.fernet import Fernet; Fernet.generate_key())
ENCRYPTION_KEY=your-fernet-key
```

## 第四步: 初始化数据库

```bash
# 运行迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 创建测试数据 (可选)
python manage.py shell << EOF
from apps.embeddings.models import EmbeddingModelConfig
from apps.products.models import Product, Feature

# 创建OpenAI配置
config = EmbeddingModelConfig.objects.create(
    model_name='openai-3-small',
    model_type='openai',
    provider='openai',
    dimension=1536,
    is_default=True,
    is_active=True
)
config.set_api_key('sk-your-key')

# 创建测试产品
product = Product.objects.create(
    name='测试产品',
    version='1.0',
    category='测试'
)

# 创建测试功能
Feature.objects.create(
    product=product,
    feature_name='用户管理',
    description='支持用户注册、登录、权限管理等功能',
    category='基础功能'
)
EOF
```

## 第五步: 启动服务

```bash
# 启动Django开发服务器
python manage.py runserver

# 访问Admin后台
# http://localhost:8000/admin/
```

## 第六步: 测试API

```bash
# 获取产品列表
curl http://localhost:8000/api/v1/products/

# 创建需求
curl -X POST http://localhost:8000/api/v1/requirements/ \
  -H "Content-Type: application/json" \
  -d '{"requirement_text": "用户登录\n权限管理", "requirement_type": "text"}'
```

## 常见问题

### 1. pgvector扩展未安装
```bash
psql -d prod_answer
CREATE EXTENSION vector;
\q
```

### 2. 数据库连接失败
检查.env中的数据库配置是否正确

### 3. OpenAI API调用失败
- 检查API密钥是否正确
- 确认网络可以访问OpenAI
- 或使用本地Sentence-Transformers模型

### 4. 使用本地模型
```python
# 在Admin后台创建配置
{
    "model_name": "local-st-model",
    "model_type": "sentence-transformers",
    "provider": "sentence-transformers",
    "dimension": 384,
    "model_params": {
        "model_path": "all-MiniLM-L6-v2"
    }
}
```

## 下一步

1. 配置Embedding模型 (OpenAI或本地)
2. 录入产品功能到知识库
3. 创建需求并测试匹配
4. (可选) 开发前端界面

## 生产部署建议

1. 使用Gunicorn + Nginx部署
2. 配置Celery处理异步任务
3. 使用Redis做缓存
4. 配置HTTPS
5. 设置定时备份
