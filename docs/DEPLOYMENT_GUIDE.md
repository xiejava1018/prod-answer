# GitHub Actions 自动部署方案

## 项目概述
为 Product Capability Matching System（产品能力匹配系统）实现 GitHub Actions CI/CD 自动部署到服务器 43.248.187.44:46579。

**已确认的配置**：
- 数据库：使用现有 Supabase 配置
- 访问方式：通过 IP 地址（43.248.187.44）
- 协议：HTTP（暂不配置 HTTPS）
- 部署范围：完整自动化部署（代码拉取、依赖安装、构建、迁移、重启）

## 部署架构

### 服务器配置
- **服务器**: 43.248.187.44:46579 (Debian 12)
- **现有环境**: Python 3.11.2, Node.js v20.20.0, nginx 1.22.1, Git 2.39.5
- **数据库**: 外部云数据库（用户已配置 Supabase）
- **部署目录**: `/var/www/prod-answer`
- **前端静态文件**: `/var/www/prod-answer/frontend/dist`
- **后端代码**: `/var/www/prod-answer/backend`

### 部署流程
```
GitHub Push → GitHub Actions → SSH 连接服务器 →
  1. 拉取最新代码
  2. 安装 Python 依赖
  3. 安装 Node 依赖并构建前端
  4. 执行数据库迁移
  5. 收集静态文件
  6. 重启 Gunicorn 服务
  7. 重载 nginx 配置
```

---

## 实施步骤

### 1. GitHub Actions Workflow 配置

**文件路径**: `.github/workflows/deploy.yml`

创建 CI/CD 工作流，包含：
- 触发条件：推送到 main 分支时触发
- SSH 连接：使用 GitHub Secrets 存储的 SSH 密钥连接服务器
- 部署步骤：执行完整的自动化部署流程

### 2. 服务器端部署脚本

**文件路径**: `backend/scripts/deploy.sh`

创建 bash 脚本，包含：
- 拉取最新代码
- 激活虚拟环境
- 安装/更新依赖
- 构建前端
- 数据库迁移
- 收集静态文件
- 重启服务

### 3. Gunicorn Systemd 服务配置

**文件路径**: `/etc/systemd/system/prod-answer.service`

创建 systemd 服务单元文件：
- 使用 Gunicorn 作为 WSGI 服务器
- 配置工作目录和虚拟环境
- 设置环境变量文件路径
- 自动重启策略

### 4. Nginx 配置

**文件路径**: `/etc/nginx/sites-available/prod-answer`

配置 nginx 反向代理：
- 前端静态文件直接服务
- `/api` 代理到 Gunicorn (127.0.0.1:8000)
- `/static` 和 `/media` 文件服务
- SSL 配置（可选）

### 5. 环境变量配置

**文件路径**: `/var/www/prod-answer/backend/.env`

服务器端环境变量文件，包含：
- Django SECRET_KEY（生成新的强随机密钥）
- DEBUG=False
- ALLOWED_HOSTS=43.248.187.44,localhost
- **数据库配置（使用现有 Supabase 配置）**：
  - SUPABASE_DB_NAME=postgres
  - SUPABASE_DB_USER=postgres.xxxxx
  - SUPABASE_DB_PASSWORD=***
  - SUPABASE_DB_HOST=xxxxx.supabase.co
  - SUPABASE_DB_PORT=5432
- 其他生产环境配置（OPENAI_API_KEY, ENCRYPTION_KEY 等）

### 6. GitHub Secrets 配置

需要在 GitHub 仓库设置中配置以下 Secrets：

- `SSH_HOST`: 43.248.187.44
- `SSH_PORT`: 46579
- `SSH_USERNAME`: root
- `SSH_PRIVATE_KEY`: 服务器的 SSH 私钥
- `DEPLOY_PATH`: /var/www/prod-answer

### 7. 安装必要依赖

在服务器上安装：
- Gunicorn: `pip install gunicorn`
- 虚拟环境工具 (如果未安装)

---

## 详细实施清单

### Phase 1: 服务器环境准备

1. **创建部署目录和虚拟环境**
   ```bash
   mkdir -p /var/www/prod-answer
   cd /var/www/prod-answer
   git clone <repository-url> .
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   pip install gunicorn
   ```

2. **创建 systemd 服务文件**
   - 创建 `/etc/systemd/system/prod-answer.service`
   - 配置 Gunicorn 服务

3. **配置 nginx**
   - 创建 `/etc/nginx/sites-available/prod-answer`
   - 创建软链接到 `sites-enabled`
   - 测试配置并重载 nginx

4. **配置环境变量**
   - 复制 `.env.example` 到 `.env`
   - 填入生产环境配置

### Phase 2: 创建本地文件

1. **GitHub Actions Workflow**
   - 创建 `.github/workflows/deploy.yml`
   - 配置部署步骤

2. **部署脚本**
   - 创建 `backend/scripts/deploy.sh`
   - 设置可执行权限

3. **更新 .gitignore**
   - 确保敏感文件不被提交

### Phase 3: GitHub 配置

1. **添加 SSH 私钥到 GitHub Secrets**
   - 从 `~/.ssh/id_rsa` 读取私钥
   - 添加到 GitHub 仓库 Secrets

2. **配置其他 Secrets**
   - 添加 HOST, PORT, USERNAME, DEPLOY_PATH

### Phase 4: 测试部署

1. **首次手动部署**
   - 在服务器上手动执行部署脚本
   - 验证服务启动正常

2. **触发 GitHub Actions**
   - 推送代码到 main 分支
   - 观察 Actions 执行日志

3. **验证应用功能**
   - 访问前端页面
   - 测试 API 接口
   - 检查数据库连接

---

## 关键文件清单

### 需要创建的文件

| 文件路径 | 用途 |
|---------|------|
| `.github/workflows/deploy.yml` | GitHub Actions 工作流配置 |
| `backend/scripts/deploy.sh` | 服务器端自动化部署脚本 |
| `/etc/systemd/system/prod-answer.service` | Gunicorn systemd 服务（服务器） |
| `/etc/nginx/sites-available/prod-answer` | Nginx 配置（服务器） |

### 需要修改的文件

| 文件路径 | 修改内容 |
|---------|---------|
| `backend/config/settings/production.py` | 确认生产环境配置 |
| `backend/requirements.txt` | 确认包含 gunicorn |
| `.gitignore` | 确保排除敏感文件 |

---

## 验证步骤

### 1. 本地验证
- [ ] 部署脚本语法正确（bash -n deploy.sh）
- [ ] GitHub Actions workflow YAML 语法正确
- [ ] 所有必需的依赖都在 requirements.txt 中

### 2. 服务器验证
- [ ] 虚拟环境创建成功
- [ ] Gunicorn 安装成功
- [ ] Nginx 配置测试通过（nginx -t）
- [ ] systemd 服务可以启动（systemctl start prod-answer）

### 3. 部署验证
- [ ] GitHub Actions 执行成功
- [ ] 前端构建产物生成（frontend/dist/）
- [ ] 后端服务运行正常（curl http://localhost:8000/api/v1/）
- [ ] 数据库迁移成功
- [ ] 静态文件收集成功

### 4. 功能验证
- [ ] 前端页面可访问
- [ ] API 接口正常响应
- [ ] 数据库连接正常
- [ ] 静态文件加载正常

---

## 注意事项

1. **安全性**
   - SSH 私钥必须通过 GitHub Secrets 存储，不能硬编码
   - 生产环境 `.env` 文件不能提交到仓库
   - Django SECRET_KEY 应该设置强随机值

2. **数据库**
   - 确保外部云数据库（Supabase）的 pgvector 扩展已安装
   - 验证数据库连接配置正确
   - 首次部署可能需要手动创建数据库和扩展

3. **回滚策略**
   - 如果部署失败，可以通过 git checkout 回滚代码
   - systemd 服务会自动重启失败的服务
   - 保留旧的部署目录作为备份

4. **性能优化**
   - Gunicorn workers 数量根据 CPU 核心数调整
   - nginx 启用 gzip 压缩
   - 静态文件设置缓存头

---

## 预期时间

- 服务器环境准备: 15-20 分钟
- 配置文件创建: 20-30 分钟
- GitHub Secrets 配置: 5 分钟
- 测试和调试: 30-60 分钟

总计: 约 1-2 小时
