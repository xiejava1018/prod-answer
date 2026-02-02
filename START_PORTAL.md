# 产品门户启动指南

## 环境要求

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+ (with pgvector extension)
- Redis 6+

## 启动步骤

### 1. 启动后端服务

```bash
cd /home/xiejava/prod-answer/backend

# 激活虚拟环境（如果存在）
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖（如果尚未安装）
pip install -r requirements.txt

# 数据库迁移
python manage.py makemigrations portal
python manage.py migrate

# 启动Django开发服务器
python manage.py runserver 0.0.0.0:8000
```

后端服务将在 `http://localhost:8000` 启动

### 2. 启动前端服务

```bash
cd /home/xiejava/prod-answer/frontend

# 安装依赖（如果尚未安装）
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 3. 访问产品门户

打开浏览器，访问：
- 门户首页：`http://localhost:5173/portal`
- 产品列表：`http://localhost:5173/portal/products`

## 测试数据准备

### 创建测试产品

```bash
python manage.py shell
```

```python
from apps.products.models import Product, Feature
import uuid

# 创建测试产品
product = Product.objects.create(
    id=uuid.uuid4(),
    name='安全大数据平台',
    version='2.0.0',
    vendor='安全科技',
    description='基于大数据技术的安全分析平台，提供实时威胁检测和响应能力',
    subsystem_type='big_data',
    category='安全管理',
    is_featured=True,
    is_on_portal=True,
    sort_weight=100,
    tagline='智能安全分析，实时威胁检测',
    key_benefits=['实时威胁检测', '智能分析引擎', '可视化展示'],
    target_industries=['金融', '政府', '企业']
)

# 创建测试功能
Feature.objects.create(
    product=product,
    level1_function='数据采集',
    level2_function='日志采集',
    level3_function='多源日志接入',
    description='支持Syslog、Kafka、文件等多种日志接入方式',
    indicator_type='product_function',
    importance_level=9
)

Feature.objects.create(
    product=product,
    level1_function='威胁检测',
    level2_function='规则引擎',
    level3_function='内置检测规则',
    description='内置1000+威胁检测规则，覆盖常见攻击手法',
    indicator_type='security',
    importance_level=9
)

Feature.objects.create(
    product=product,
    level1_function='可视化展示',
    level2_function='仪表盘',
    level3_function='安全态势大屏',
    description='实时展示安全态势，支持自定义仪表盘',
    indicator_type='usability',
    importance_level=8
)
```

## API测试

### 获取产品列表
```bash
curl http://localhost:8000/api/v1/portal/products/
```

### 获取推荐产品
```bash
curl http://localhost:8000/api/v1/portal/products/featured/
```

### 获取产品统计
```bash
curl http://localhost:8000/api/v1/portal/products/statistics/
```

## 常见问题

### 1. 数据库连接失败

确保PostgreSQL服务已启动，并且数据库配置正确。

### 2. Redis连接失败

确保Redis服务已启动，可以在 `backend/config/settings/base.py` 中配置Redis连接信息。

### 3. 前端无法连接后端API

检查前端API配置：`frontend/src/api/portal.ts` 中的 `baseURL` 是否正确。

### 4. CORS错误

检查后端CORS配置：`backend/config/settings/base.py` 中的 `CORS_ALLOWED_ORIGINS` 是否包含前端地址。

## 性能优化建议

1. 使用Redis缓存热门产品数据
2. 配置CDN加速静态资源
3. 启用Gzip压缩
4. 使用分页和虚拟滚动优化长列表

## 监控和日志

- 后端日志：`backend/logs/`
- 前端控制台：浏览器开发者工具
- API文档：访问 `http://localhost:8000/api/docs/` (如果配置了drf-spectacular)

## 下一步计划

1. 测试所有功能模块
2. 优化性能和用户体验
3. 添加更多产品数据
4. 部署到生产环境
