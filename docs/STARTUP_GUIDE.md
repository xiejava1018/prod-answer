# 项目启动和测试指南

**当前环境检测**:
- ✅ Python 3.14.2 (建议降级到Python 3.11或3.12)
- ✅ Node v24.12.0
- ❌ PostgreSQL未安装

---

## 🚀 方案一：完整功能启动（需要PostgreSQL）

### 1. 安装PostgreSQL

#### macOS
```bash
brew install postgresql@14
brew install pgvector
brew services start postgresql@14

# 创建数据库
createdb prod_answer
psql -d prod_answer -c "CREATE EXTENSION vector;"
```

#### Ubuntu
```bash
sudo apt install postgresql-14 postgresql-contrib-pgvector
sudo systemctl start postgresql
sudo -u postgres createdb prod_answer
sudo -u postgres psql -d prod_answer -c "CREATE EXTENSION vector;"
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐Python 3.11）
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install Django==4.2.11 djangorestframework==3.14.0
pip install psycopg2-binary==2.9.9 pgvector==0.2.5
pip install openai==1.12.0 python-dotenv==1.0.1
pip install cryptography==42.0.5
pip install django-cors-headers==4.3.1
pip install django-filter==23.5

# 配置环境变量
cp .env.example .env
# 编辑.env，配置数据库和API密钥

# 运行迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务器
python manage.py runserver
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问应用
- 前端: http://localhost:5173
- 后端API: http://localhost:8000/api/v1/
- Admin后台: http://localhost:8000/admin/

---

## 🔧 方案二：快速演示模式（SQLite + 模拟数据）

### 修改Python版本
Python 3.14太新，建议使用Python 3.11或3.12：

```bash
# macOS使用pyenv安装Python 3.11
brew install pyenv
pyenv install 3.11.9
pyenv local 3.11.9

# Ubuntu使用dead snakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11
```

### 启动后端（简化版）

```bash
cd backend

# 使用Python 3.11
python3.11 -m venv venv
source venv/bin/activate

# 安装最少依赖
pip install Django==4.2.11
pip install djangorestframework==3.14.0
pip install python-dotenv==1.0.1

# 使用SQLite配置
export USE_SQLITE=True

# 创建简化版数据库
python manage.py migrate

# 启动
python manage.py runserver
```

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 功能测试清单

### 测试1: 后端API测试

#### 1.1 测试Django Admin
```bash
# 访问
http://localhost:8000/admin/

# 使用创建的超级用户登录
# 应该能看到：产品、功能、Embedding配置等管理界面
```

#### 1.2 测试产品API
```bash
# 创建产品
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试产品",
    "version": "1.0",
    "category": "测试分类"
  }'

# 获取产品列表
curl http://localhost:8000/api/v1/products/

# 获取产品详情
curl http://localhost:8000/api/v1/products/{id}/
```

#### 1.3 测试Embedding API
```bash
# 创建Embedding配置（需要API密钥）
curl -X POST http://localhost:8000/api/v1/embeddings/configs/ \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "test-model",
    "model_type": "openai",
    "provider": "openai",
    "dimension": 1536,
    "is_default": true
  }'

# 获取配置列表
curl http://localhost:8000/api/v1/embeddings/configs/
```

### 测试2: 前端功能测试

#### 2.1 Dashboard页面
```bash
# 访问
http://localhost:5173/dashboard

# 应该看到：
- 统计卡片
- 快速操作按钮
- 系统状态
- 使用指南
```

#### 2.2 产品管理页面
```bash
# 访问
http://localhost:5173/products

# 测试操作：
1. 点击"创建产品"
2. 填写产品信息
3. 点击"创建"
4. 查看产品列表
```

#### 2.3 Embedding配置页面
```bash
# 访问
http://localhost:5173/settings/embeddings

# 测试操作：
1. 点击"添加配置"
2. 选择模型类型（OpenAI或本地）
3. 填写配置信息
4. 点击"测试连接"
```

### 测试3: 完整流程测试

```bash
# 步骤1: 配置Embedding模型
访问: http://localhost:5173/settings/embeddings
-> 添加OpenAI配置（需要API密钥）

# 步骤2: 创建产品
访问: http://localhost:5173/products/create
-> 创建产品
-> 添加功能

# 步骤3: 生成向量
在产品详情页
-> 批量生成向量

# 步骤4: 创建需求
访问: http://localhost:5173/requirements/create
-> 输入需求文本（每行一个）
-> 点击"创建"

# 步骤5: 执行匹配
访问: http://localhost:5173/matching
-> 选择需求
-> 设置阈值
-> 点击"开始匹配"

# 步骤6: 查看结果
-> 点击"查看详细结果"
-> 查看3个Tab（完全/部分/不匹配）
```

---

## 🐛 常见问题和解决方案

### 问题1: Python依赖安装失败

**原因**: Python 3.14太新，部分包不兼容

**解决方案**:
```bash
# 方案A: 使用pyenv安装Python 3.11
brew install pyenv
pyenv install 3.11.9
pyenv local 3.11.9

# 方案B: 使用conda
conda create -n prod-answer python=3.11
conda activate prod-answer

# 方案C: 使用系统Python（如果是3.11/3.12）
python3.11 -m venv venv
```

### 问题2: PostgreSQL未安装

**解决方案A**: 安装PostgreSQL
```bash
# macOS
brew install postgresql@14 pgvector

# Ubuntu
sudo apt install postgresql-14 postgresql-contrib-pgvector
```

**解决方案B**: 使用SQLite（测试用）
```bash
export USE_SQLITE=True
python manage.py migrate
python manage.py runserver
```

**注意**: SQLite不支持pgvector向量搜索，会降级为普通相似度计算

### 问题3: OpenAI API调用失败

**原因**:
1. API密钥未配置
2. 网络问题
3. 配额不足

**解决方案**:
```bash
# 检查API密钥
echo $OPENAI_API_KEY

# 测试连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 或使用本地模型（免费）
访问: http://localhost:5173/settings/embeddings
-> 选择模型类型: Sentence-Transformers
-> 模型路径: all-MiniLM-L6-v2
```

### 问题4: 前端无法连接后端

**症状**: 前端页面空白或API请求失败

**检查**:
```bash
# 1. 检查后端是否启动
curl http://localhost:8000/api/v1/

# 2. 检查CORS配置
# Django settings should have:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

### 问题5: 向量生成失败

**原因**:
1. 模型未配置
2. API调用失败
3. 功能描述为空

**解决方案**:
```bash
# 1. 检查Embedding配置
访问: http://localhost:8000/admin/
-> Embedding Model Configs
-> 确保有活跃配置

# 2. 测试连接
访问: http://localhost:5173/settings/embeddings
-> 点击"测试连接"

# 3. 检查功能描述
确保功能描述不为空
```

---

## 📊 测试检查表

### 后端检查
- [ ] Django能正常启动
- [ ] 可以访问Admin后台
- [ ] 可以创建产品
- [ ] 可以添加功能
- [ ] Embedding配置正常
- [ ] API响应正常

### 前端检查
- [ ] Vue开发服务器启动
- [ ] Dashboard页面正常显示
- [ ] 产品列表页正常
- [ ] 产品表单可正常填写和提交
- [ ] Embedding配置页面可访问
- [ ] 所有路由可正常跳转

### 功能检查
- [ ] 能创建产品
- [ ] 能添加功能
- [ ] 能配置Embedding模型
- [ ] 能创建需求（文本输入）
- [ ] 能创建需求（文件上传）
- [ ] 能执行匹配分析
- [ ] 能查看匹配结果

---

## 🎯 推荐的测试顺序

### 阶段1: 后端基础测试（5分钟）
```bash
1. 启动Django: python manage.py runserver
2. 访问Admin: http://localhost:8000/admin
3. 创建测试数据（产品和功能）
4. 使用API测试工具测试CRUD
```

### 阶段2: 前端页面测试（10分钟）
```bash
1. 启动前端: npm run dev
2. 访问Dashboard
3. 测试产品管理页面
4. 测试Embedding配置页面
```

### 阶段3: 完整流程测试（15分钟）
```bash
1. 配置Embedding模型（使用本地模型测试）
2. 创建产品和功能
3. 生成向量
4. 创建需求
5. 执行匹配
6. 查看结果
```

---

## 📝 测试数据示例

### 测试产品
```json
{
  "name": "CRM客户管理系统",
  "version": "1.0.0",
  "category": "企业管理",
  "vendor": "示例公司",
  "description": "一个完整的客户关系管理系统"
}
```

### 测试功能列表
```
1. 用户登录
2. 客户信息管理
3. 权限控制
4. 数据报表
5. 移动端支持
6. 数据导入导出
```

### 测试需求文本
```
用户登录
权限管理
客户信息查询
销售机会管理
数据统计报表
```

---

## 🚀 快启动脚本

### macOS/Linux

```bash
#!/bin/bash
# start.sh - 快速启动项目

echo "启动产品能力匹配系统..."

# 启动后端
cd backend
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!

# 启动前端
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "后端PID: $BACKEND_PID"
echo "前端PID: $FRONTEND_PID"
echo "后端: http://localhost:8000"
echo "前端: http://localhost:5173"

# 等待用户输入
read -p "按Enter停止服务..."

# 停止服务
kill $BACKEND_PID
kill $FRONTEND_PID
```

使用方法：
```bash
chmod +x start.sh
./start.sh
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看文档：README.md, INSTALL.md
2. 查看API文档：docs/API.md
3. 检查日志：Django控制台输出
4. 查看浏览器控制台（F12）

---

**提示**: 对于生产环境，建议：
- 使用PostgreSQL + pgvector
- Python 3.11或3.12
- 配置Nginx反向代理
- 使用Gunicorn + systemd

**注意**: 当前使用Python 3.14可能导致一些依赖不兼容，建议降级到Python 3.11或3.12。

---

*更新日期: 2026-01-05*
