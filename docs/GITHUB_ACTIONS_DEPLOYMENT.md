# GitHub Actions 自动化部署配置指南

## 概述

项目已配置 GitHub Actions CI/CD，当代码推送到 `main` 分支时自动部署到生产服务器。

## 前置条件

- ✅ 服务器已配置好运行环境（Gunicorn + Nginx）
- ✅ Git 仓库已克隆到服务器
- ✅ 服务器 SSH 密钥认证已配置

## GitHub Secrets 配置步骤

### 1. 生成 SSH 密钥（如果还没有）

在**本地机器**上执行：

```bash
# 生成 SSH 密钥对（如果已有可跳过）
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions

# 复制公钥到服务器
ssh-copy-p -i ~/.ssh/github_actions.pub -p 46579 root@43.248.187.44
```

或者手动添加公钥到服务器：

```bash
# 在本地查看公钥
cat ~/.ssh/github_actions.pub

# SSH 登录服务器，将公钥添加到 authorized_keys
ssh -p 46579 root@43.248.187.44
echo "你的公钥内容" >> ~/.ssh/authorized_keys
```

### 2. 获取私钥内容

在**本地机器**上执行：

```bash
# Windows (Git Bash)
cat ~/.ssh/github_actions

# Linux/Mac
cat ~/.ssh/github_actions
```

复制整个输出（包括 `-----BEGIN...` 和 `-----END...` 行）

### 3. 配置 GitHub Secrets

1. 打开 GitHub 仓库页面
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret** 添加以下密钥：

| Secret 名称 | 值 | 说明 |
|-------------|---|------|
| `SSH_HOST` | `43.248.187.44` | 服务器 IP 地址 |
| `SSH_PORT` | `46579` | SSH 端口 |
| `SSH_USERNAME` | `root` | SSH 用户名 |
| `SSH_PRIVATE_KEY` | *(私钥完整内容)* | 上一步复制的私钥 |
| `DEPLOY_PATH` | `/var/www/prod-answer` | 部署目录路径 |

### 4. 验证配置

在 GitHub 仓库页面：

1. 点击 **Actions** 标签
2. 选择 **Deploy to Production Server** workflow
3. 点击 **Run workflow** 按钮手动触发测试
4. 等待执行完成，检查是否成功

## 部署流程

### 自动触发

```bash
# 推送代码到 main 分支，自动触发部署
git add .
git commit -m "feat: 新功能"
git push origin main
```

### 手动触发

1. 访问 GitHub 仓库 **Actions** 页面
2. 选择 **Deploy to Production Server**
3. 点击 **Run workflow** → **Run workflow**

## 部署步骤详解

Workflow 执行以下步骤：

1. **代码检出** - Checkout 代码
2. **数据库备份** - 备份 SQLite 数据库（带时间戳）
3. **拉取代码** - Git pull 最新代码
4. **安装依赖** - 更新 Python 和 Node 依赖
5. **构建前端** - `npm run build`
6. **数据库迁移** - Django migrate
7. **收集静态文件** - Django collectstatic
8. **清理缓存** - 删除 .pyc 和 __pycache__
9. **重启服务** - systemctl restart prod-answer
10. **健康检查** - 验证 API 是否正常响应
11. **重载 Nginx** - systemctl reload nginx
12. **清理备份** - 删除 7 天前的旧备份

## 回滚策略

如果部署失败：

```bash
# SSH 登录服务器
ssh -p 46579 root@43.248.187.44

# 查看可用备份
ls -lh /var/www/prod-answer/backups/

# 恢复数据库
cp /var/www/prod-answer/backups/db.sqlite3.YYYYMMDD_HHMMSS \
   /var/www/prod-answer/backend/db.sqlite3

# 重启服务
systemctl restart prod-answer

# 回滚代码（如果需要）
cd /var/www/prod-answer
git log --oneline -10  # 查看最近提交
git checkout <commit-hash>  # 回滚到指定提交
systemctl restart prod-answer
```

## 监控和日志

### 查看 GitHub Actions 日志

1. GitHub 仓库 → **Actions** 标签
2. 点击具体的 workflow run
3. 展开各个步骤查看详细日志

### 查看服务器日志

```bash
# Django 应用日志
ssh -p 46579 root@43.248.187.44
tail -f /var/www/prod-answer/backend/logs/error.log
tail -f /var/www/prod-answer/backend/logs/access.log

# Gunicorn 服务日志
journalctl -u prod-answer -f

# Nginx 访问日志
tail -f /var/log/nginx/access.log

# Nginx 错误日志
tail -f /var/log/nginx/error.log
```

## 故障排查

### 部署失败常见原因

1. **SSH 认证失败**
   - 检查 SSH_PRIVATE_KEY 是否正确
   - 验证服务器 `~/.ssh/authorized_keys` 包含公钥

2. **权限错误**
   - 确保 GitHub Actions 使用的用户有 sudo 权限
   - 检查文件和目录权限

3. **端口访问失败**
   - 验证防火墙规则
   - 确认 nginx 已配置正确监听

4. **服务启动失败**
   - 检查 Django 日志：`tail -50 logs/error.log`
   - 验证数据库连接
   - 手动运行服务测试：`systemctl start prod-answer`

### 快速回滚命令

```bash
# 如果新版本有问题，快速回滚到上一个版本
ssh -p 46579 root@43.248.187.44 << 'EOF'
cd /var/www/prod-answer
LATEST_BACKUP=$(ls -t backups/db.sqlite3.* | head -1)
cp "$LATEST_BACKUP" backend/db.sqlite3
git checkout HEAD~1
systemctl restart prod-answer
EOF
```

## 安全建议

1. **SSH 密钥管理**
   - 使用专用的部署密钥对
   - 定期轮换密钥
   - 限制密钥权限（只读部署目录）

2. **Secrets 保护**
   - 不要在代码中硬编码密钥
   - 定期审查 GitHub Secrets
   - 使用最小权限原则

3. **备份策略**
   - 定期备份生产数据库
   - 将备份存储到远程位置
   - 测试恢复流程

## 生产环境检查清单

部署前确认：

- [ ] 代码已通过本地测试
- [ ] 数据库迁移文件已创建
- [ ] 前端构建成功
- [ ] 没有调试代码或 print 语句
- [ ] 环境变量配置正确
- [ ] 已备份数据库

部署后验证：

- [ ] 前端页面可访问
- [ ] API 接口正常响应
- [ ] 数据库连接正常
- [ ] 关键功能可用
- [ ] 查看错误日志无异常

## 相关文档

- [部署指南](./DEPLOYMENT_GUIDE.md)
- [项目 README](../README.md)
- [CLAUDE.md](../CLAUDE.md)
