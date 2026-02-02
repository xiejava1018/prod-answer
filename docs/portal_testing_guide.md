# 产品门户联调测试文档

## 测试环境准备

### 1. 数据库迁移

```bash
# 进入后端目录
cd /home/xiejava/prod-answer/backend

# 激活虚拟环境（如果存在）
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 创建迁移文件
python manage.py makemigrations portal

# 执行迁移
python manage.py migrate
```

### 2. 启动后端服务

```bash
# 启动Django开发服务器
python manage.py runserver 0.0.0.0:8000
```

### 3. 启动前端服务

```bash
# 进入前端目录
cd /home/xiejava/prod-answer/frontend

# 安装依赖（如果尚未安装）
npm install

# 启动开发服务器
npm run dev
```

## 功能测试清单

### 1. 门户首页测试

#### 1.1 页面加载
- [ ] 访问 `http://localhost:5173/portal`（或前端实际端口）
- [ ] 检查页面是否正常加载
- [ ] 检查Hero区域是否显示
- [ ] 检查产品分类是否显示
- [ ] 检查热门产品是否显示
- [ ] 检查解决方案轮播是否显示

#### 1.2 快速匹配功能
- [ ] 在输入框中输入需求文本
- [ ] 点击"立即匹配"按钮
- [ ] 检查是否跳转到匹配页面
- [ ] 检查URL是否包含需求参数

#### 1.3 产品分类导航
- [ ] 点击任意产品分类卡片
- [ ] 检查是否跳转到产品列表页
- [ ] 检查筛选条件是否正确应用

#### 1.4 热门产品推荐
- [ ] 点击任意产品卡片
- [ ] 检查是否跳转到产品详情页
- [ ] 检查产品信息是否正确显示

### 2. 产品列表页测试

#### 2.1 页面加载
- [ ] 访问 `http://localhost:5173/portal/products`
- [ ] 检查产品列表是否正常显示
- [ ] 检查分页功能是否正常

#### 2.2 搜索功能
- [ ] 在搜索框中输入关键词
- [ ] 检查搜索结果是否正确
- [ ] 检查搜索结果数量是否显示

#### 2.3 筛选功能
- [ ] 选择子系统类型筛选
- [ ] 检查筛选结果是否正确
- [ ] 选择产品分类筛选
- [ ] 检查筛选结果是否正确
- [ ] 选择厂商筛选
- [ ] 检查筛选结果是否正确

#### 2.4 排序功能
- [ ] 切换不同的排序方式
- [ ] 检查排序结果是否正确

#### 2.5 视图切换
- [ ] 切换到列表视图
- [ ] 检查列表视图是否正常显示
- [ ] 切换回网格视图
- [ ] 检查网格视图是否正常显示

#### 2.6 产品卡片操作
- [ ] 点击"查看详情"按钮
- [ ] 检查是否跳转到产品详情页
- [ ] 点击"加入对比"按钮
- [ ] 检查是否添加到对比列表

### 3. 产品详情页测试

#### 3.1 页面加载
- [ ] 访问产品详情页（如 `/portal/products/{id}`）
- [ ] 检查产品基本信息是否正确显示
- [ ] 检查产品描述是否正确显示

#### 3.2 功能特性树
- [ ] 点击一级功能标题
- [ ] 检查二级功能是否正确展开
- [ ] 点击二级功能标题
- [ ] 检查三级功能是否正确展开
- [ ] 在搜索框中输入关键词
- [ ] 检查功能树是否正确过滤

#### 3.3 技术规格
- [ ] 切换到"技术规格"标签页
- [ ] 检查技术规格是否正确分组显示
- [ ] 检查规格参数是否正确显示

#### 3.4 统计信息
- [ ] 切换到"统计信息"标签页
- [ ] 检查统计图表是否正确显示
- [ ] 检查功能分布图表是否正确显示

#### 3.5 相关产品
- [ ] 切换到"相关产品"标签页
- [ ] 检查相关产品列表是否正确显示
- [ ] 点击相关产品卡片
- [ ] 检查是否跳转到对应产品详情页

### 4. API接口测试

#### 4.1 产品列表API
```bash
# 测试获取产品列表
curl http://localhost:8000/api/v1/portal/products/

# 测试搜索
curl "http://localhost:8000/api/v1/portal/products/?search=安全"

# 测试筛选
curl "http://localhost:8000/api/v1/portal/products/?subsystem_type=asset_mapping"

# 测试排序
curl "http://localhost:8000/api/v1/portal/products/?ordering=-view_count"

# 测试分页
curl "http://localhost:8000/api/v1/portal/products/?page=2&page_size=12"
```

#### 4.2 产品详情API
```bash
# 测试获取产品详情
curl http://localhost:8000/api/v1/portal/products/{product_id}/
```

#### 4.3 推荐产品API
```bash
# 测试获取推荐产品
curl http://localhost:8000/api/v1/portal/products/featured/
```

#### 4.4 产品统计API
```bash
# 测试获取产品统计信息
curl http://localhost:8000/api/v1/portal/products/statistics/
```

#### 4.5 产品对比API
```bash
# 测试产品对比
curl -X POST http://localhost:8000/api/v1/portal/products/compare/ \
  -H "Content-Type: application/json" \
  -d '{"product_ids": ["id1", "id2", "id3"]}'
```

## 常见问题及解决方案

### 1. 数据库迁移失败

**问题描述**：执行 `python manage.py migrate` 时报错

**解决方案**：
```bash
# 1. 检查数据库连接是否正常
# 2. 检查是否有未执行的迁移文件
python manage.py showmigrations

# 3. 如果有冲突，可以重置迁移
# 注意：这会删除数据库中的所有数据
python manage.py flush
python manage.py migrate

# 4. 或者手动删除迁移文件重新创建
rm -rf apps/portal/migrations/0*.py
python manage.py makemigrations portal
python manage.py migrate
```

### 2. 前端页面空白或报错

**问题描述**：访问页面时显示空白或控制台有错误

**解决方案**：
```bash
# 1. 检查前端依赖是否安装完整
cd frontend
npm install

# 2. 检查是否有语法错误
npm run type-check

# 3. 清除缓存并重新启动
rm -rf node_modules/.vite
npm run dev
```

### 3. API请求失败

**问题描述**：前端无法获取数据，控制台显示API请求失败

**解决方案**：
```bash
# 1. 检查后端服务是否正常运行
curl http://localhost:8000/api/v1/portal/products/

# 2. 检查CORS配置是否正确
# 查看 backend/config/settings/base.py 中的 CORS_ALLOWED_ORIGINS

# 3. 检查前端API基础URL配置
# 查看 frontend/src/api/portal.ts 中的 baseURL
```

### 4. 图片或静态文件无法加载

**问题描述**：图片、CSS等静态文件无法加载

**解决方案**：
```bash
# 1. 检查Django的静态文件配置
# 确保 backend/config/settings/base.py 中有正确的 STATIC_URL 和 MEDIA_URL

# 2. 收集静态文件（生产环境）
python manage.py collectstatic

# 3. 检查文件路径是否正确
```

### 5. 缓存问题

**问题描述**：数据更新后页面没有变化

**解决方案**：
```bash
# 1. 清除浏览器缓存
# 2. 清除Redis缓存（如果使用）
redis-cli FLUSHALL

# 3. 重启后端服务
```

## 性能测试建议

### 1. 数据库查询优化
- [ ] 检查是否有N+1查询问题
- [ ] 使用 Django Debug Toolbar 分析查询性能
- [ ] 确保相关字段已建立索引

### 2. 前端性能优化
- [ ] 检查组件渲染性能
- [ ] 使用 Vue DevTools 分析组件性能
- [ ] 检查图片懒加载是否正常工作

### 3. API性能测试
```bash
# 使用 ab (Apache Bench) 进行压力测试
ab -n 1000 -c 10 http://localhost:8000/api/v1/portal/products/

# 使用 wrk 进行更高级的压力测试
wrk -t12 -c400 -d30s http://localhost:8000/api/v1/portal/products/
```

## 测试数据准备

### 1. 创建测试产品
```bash
# 使用 Django shell 创建测试数据
python manage.py shell
```

```python
from apps.products.models import Product
from apps.products.models import Feature
import uuid

# 创建测试产品
product = Product.objects.create(
    id=uuid.uuid4(),
    name='测试产品',
    version='1.0.0',
    vendor='测试厂商',
    description='这是一个测试产品',
    subsystem_type='asset_mapping',
    category='security',
    is_featured=True,
    is_on_portal=True,
    sort_weight=100,
    view_count=0,
    download_count=0
)

# 创建测试功能
feature = Feature.objects.create(
    product=product,
    level1_function='核心功能',
    level2_function='子功能',
    level3_function='具体功能',
    description='功能描述',
    indicator_type='product_function',
    importance_level=8
)
```

### 2. 创建测试解决方案
```python
from apps.portal.models import Solution

solution = Solution.objects.create(
    name='测试解决方案',
    solution_type='industry',
    category='金融',
    summary='测试解决方案概述',
    pain_points=['痛点1', '痛点2'],
    benefits=['收益1', '收益2'],
    is_featured=True
)

solution.products.add(product)
```

## 测试报告模板

### 测试概述
- 测试日期：
- 测试人员：
- 测试环境：
- 测试范围：

### 测试结果汇总
- 总测试用例数：
- 通过用例数：
- 失败用例数：
- 通过率：

### 详细测试结果
| 功能模块 | 测试用例 | 预期结果 | 实际结果 | 状态 | 备注 |
|---------|---------|---------|---------|------|------|
| 门户首页 | 页面加载 | 正常显示 | | | |
| | 快速匹配 | 跳转匹配页 | | | |
| 产品列表 | 搜索功能 | 正确筛选 | | | |
| | 筛选功能 | 正确筛选 | | | |
| 产品详情 | 功能树 | 正确展开 | | | |
| | 技术规格 | 正确显示 | | | |

### 问题列表
| 问题ID | 问题描述 | 严重程度 | 状态 | 解决方案 |
|-------|---------|---------|------|---------|
| | | | | |

### 性能测试结果
- 页面加载时间：
- API响应时间：
- 并发用户数：
- 吞吐量：

### 测试结论
- [ ] 测试通过，可以上线
- [ ] 测试通过，但需修复已知问题
- [ ] 测试不通过，需重新测试

### 建议和改进
1. 
2. 
3.