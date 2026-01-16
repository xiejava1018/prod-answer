# Supabase 数据库迁移指南

## 概述

本文档说明如何将产品能力匹配系统从 SQLite 迁移到 Supabase PostgreSQL 数据库。

## 为什么要迁移到 Supabase？

### Supabase vs SQLite 对比

| 特性 | SQLite | Supabase (PostgreSQL) |
|------|--------|----------------------|
| **部署** | 本地文件 | 云端托管 |
| **并发** | 有限 | 高并发支持 |
| **向量搜索** | 降级支持（无索引） | 原生 pgvector 支持 |
| **性能** | 适合小数据集 | 适合生产环境 |
| **备份** | 手动复制文件 | 自动备份 |
| **扩展性** | 受限于单机 | 水平扩展 |
| **成本** | 免费 | 有免费额度 |

## 配置步骤

### 1. 安装依赖

```bash
cd backend
./venv/Scripts/pip install psycopg2-binary pgvector python-dotenv
```

### 2. 配置环境变量

在 `backend/.env` 文件中添加：

```env
# 启用 Supabase（设置为 False 使用 Supabase）
USE_SQLITE=False

# Supabase 数据库配置
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.your-project-id
SUPABASE_DB_PASSWORD=your-password
SUPABASE_DB_HOST=aws-1-ap-southeast-1.pooler.supabase.com
SUPABASE_DB_PORT=5432
```

### 3. 创建 Supabase 设置文件

配置文件位于 `backend/config/settings/supabase.py`：

```python
# 关键配置 - 使用环境变量
os.environ['USE_SQLITE'] = 'False'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('SUPABASE_DB_NAME', 'postgres'),
        'USER': os.environ.get('SUPABASE_DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('SUPABASE_DB_PASSWORD', ''),
        'HOST': os.environ.get('SUPABASE_DB_HOST', 'aws-1-ap-southeast-1.pooler.supabase.com'),
        'PORT': os.environ.get('SUPABASE_DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,
    }
}
```

### 4. 启用 pgvector 扩展

运行迁移脚本：

```bash
cd backend
./venv/Scripts/python manage.py migrate --settings=config.settings.supabase
```

这会自动执行 `apps/core/migrations/0002_enable_pgvector.py` 迁移，启用 pgvector 扩展。

### 5. 验证 Vector 字段类型

运行验证脚本：

```bash
cd backend
./venv/Scripts/python check_db_field_type.py
```

应该看到：
```
- embedding: vector (vector)
```

如果不是 `vector` 类型，运行：

```bash
cd backend
./venv/Scripts/python alter_to_vector.py
```

### 6. 验证完整配置

```bash
cd backend
./venv/Scripts/python supabase_setup_report.py
```

所有测试应该显示 `[PASS]`。

## 使用 Supabase

### 启动后端（使用 Supabase）

```bash
cd backend
./venv/Scripts/python manage.py runserver --settings=config.settings.supabase
```

### 切换回 SQLite

如需切换回 SQLite（例如在本地开发时）：

1. 修改 `.env` 文件：
   ```env
   USE_SQLITE=True
   ```

2. 启动开发服务器（使用默认设置）：
   ```bash
   cd backend
   ./venv/Scripts/python manage.py runserver
   ```

## 数据迁移

### 从 SQLite 迁移数据到 Supabase

如果你已经在 SQLite 中有数据，可以使用 Django 的 `dumpdata` 和 `loaddata`：

```bash
# 1. 从 SQLite 导出数据
cd backend
./venv/Scripts/python manage.py dumpdata > data.json

# 2. 切换到 Supabase（修改 .env: USE_SQLITE=False）

# 3. 运行迁移
./venv/Scripts/python manage.py migrate --settings=config.settings.supabase

# 4. 导入数据
./venv/Scripts/python manage.py loaddata data.json --settings=config.settings.supabase
```

### 导入产品数据

如果使用 CSV 文件导入产品：

```bash
cd backend
./venv/Scripts/python manage.py import_products data/products.csv --settings=config.settings.supabase
```

## 性能优化

### 创建向量索引（可选）

对于大量数据（>10,000 features），可以创建 HNSW 索引来加速搜索：

```sql
-- 在 Supabase SQL Editor 中运行
CREATE INDEX embedding_hnsw_idx
ON feature_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 连接池配置

Supabase 连接器默认已启用连接池（`CONN_MAX_AGE=600`），可以根据需要调整。

## 故障排查

### 问题 1: DNS 解析失败

**错误**: `could not translate host name`

**解决方案**:
1. 检查网络连接
2. 尝试使用 VPN
3. 检查 Supabase 项目状态
4. 验证主机名是否正确

### 问题 2: 认证失败

**错误**: `password authentication failed`

**解决方案**:
1. 验证 `.env` 中的密码是否正确
2. 确认使用的是 Supabase Pooler 连接字符串
3. 在 Supabase Dashboard 中重置密码

### 问题 3: Vector 字段类型错误

**错误**: `column "embedding" is of type jsonb but expression is of type vector`

**解决方案**:
1. 运行 `alter_to_vector.py` 脚本
2. 或手动运行 SQL：
   ```sql
   ALTER TABLE feature_embeddings
   ALTER COLUMN embedding
   TYPE vector(1536)
   USING embedding::text::vector(1536);
   ```

### 问题 4: pgvector 扩展未安装

**错误**: `type "vector" does not exist`

**解决方案**:
1. 在 Supabase Dashboard > SQL Editor 中运行：
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. 或运行迁移：
   ```bash
   ./venv/Scripts/python manage.py migrate --settings=config.settings.supabase
   ```

## 验证测试

运行完整的验证测试：

```bash
cd backend
./venv/Scripts/python supabase_setup_report.py
```

期望输出：

```
[1] Database Connection        [PASS]
[2] pgvector Extension          [PASS]
[3] Database Tables            [PASS]
[4] Vector Field Configuration  [PASS]
[5] Django Settings            [PASS]
[6] Django System Check        [PASS]
```

## 配置文件总结

创建的文件：

1. **backend/config/settings/supabase.py**
   - Supabase 数据库配置
   - 环境变量设置
   - SSL 和连接池配置

2. **backend/.env**
   - 数据库连接凭据
   - USE_SQLITE 开关

3. **backend/apps/core/migrations/0002_enable_pgvector.py**
   - pgvector 扩展启用迁移

4. **backend/test_supabase_connection.py**
   - 连接测试脚本

5. **backend/check_db_field_type.py**
   - 字段类型验证脚本

6. **backend/alter_to_vector.py**
   - Vector 字段类型转换脚本

7. **backend/supabase_setup_report.py**
   - 完整配置验证报告

## 生产环境注意事项

1. **安全性**:
   - 不要将 `.env` 文件提交到 Git
   - 使用环境变量管理敏感信息
   - 配置 `ALLOWED_HOSTS` 为实际域名

2. **备份**:
   - Supabase 自动备份，但建议定期导出关键数据
   - 保留 SQLite 作为本地备份

3. **监控**:
   - 使用 Supabase Dashboard 监控数据库性能
   - 关注查询性能和慢查询

4. **扩展性**:
   - 监控 Supabase 免费额度使用情况
   - 根据需要升级计划

## 支持

如有问题，请参考：
- [Supabase 官方文档](https://supabase.com/docs)
- [pgvector 文档](https://github.com/pgvector/pgvector)
- [Django PostgreSQL 文档](https://docs.djangoproject.com/en/4.2/ref/databases/postgresql/)
