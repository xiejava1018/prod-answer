# GitHub Actions 快速配置清单

## 🚀 5 分钟配置自动化部署

### 步骤 1: 准备 SSH 密钥（本地执行）

```bash
# 生成密钥
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_deploy_rsa

# 复制公钥到服务器
ssh-copy-p -i ~/.ssh/github_deploy_rsa.pub -p 46579 root@43.248.187.44
```

### 步骤 2: 添加 GitHub Secrets

访问：`https://github.com/<你的仓库>/settings/secrets/actions`

点击 **New repository secret**，依次添加：

| Name | Secret |
|------|--------|
| `SSH_HOST` | `43.248.187.44` |
| `SSH_PORT` | `46579` |
| `SSH_USERNAME` | `root` |
| `SSH_PRIVATE_KEY` | `cat ~/.ssh/github_deploy_rsa` 的完整输出 |
| `DEPLOY_PATH` | `/var/www/prod-answer` |

### 步骤 3: 测试部署

```bash
# 推送任意代码改动触发部署
git add .
git commit -m "test: trigger deployment"
git push origin main
```

或者：
1. 打开 GitHub 仓库 → Actions
2. 选择 "Deploy to Production Server"
3. 点击 "Run workflow"

### 步骤 4: 验证

访问 http://43.248.187.44:11080/ 确认应用正常运行

---

## ✅ 配置检查清单

- [ ] SSH 密钥已生成并添加到服务器
- [ ] GitHub Secrets 已配置（5 个）
- [ ] 服务器 Git 仓库指向正确的远程地址
- [ ] 服务器虚拟环境已创建
- [ ] systemd 服务 (prod-answer) 已配置
- [ ] nginx 已配置并运行

---

## 🔄 部署流程

```
推送代码 → GitHub Actions 触发 → SSH 连接服务器
    ↓
备份数据库 → 拉取代码 → 安装依赖 → 构建前端
    ↓
运行迁移 → 收集静态文件 → 重启服务 → 健康检查
    ↓
部署完成 ✅
```

---

## 🛠️ 故障排查

| 问题 | 解决方案 |
|------|---------|
| SSH 认证失败 | 检查 `SSH_PRIVATE_KEY` 是否完整（包含 BEGIN/END 行） |
| 权限错误 | 确保 root 用户可以无密码执行 systemctl |
| 部署失败 | 查看 Actions 日志，检查具体错误步骤 |
| 服务未启动 | SSH 到服务器检查 `journalctl -u prod-answer -n 50` |

---

## 📝 常用命令

```bash
# 查看 GitHub Actions 状态
gh run list --repo <owner>/<repo>

# 手动触发部署
gh workflow run deploy.yml --repo <owner>/<repo>

# 查看最新部署日志
gh run view --repo <owner>/<repo> --log

# SSH 查看服务器日志
ssh -p 46579 root@43.248.187.44
tail -f /var/www/prod-answer/backend/logs/error.log
```

---

## 🔐 安全提醒

- ⚠️ **不要**将 `SSH_PRIVATE_KEY` 提交到代码仓库
- ⚠️ **不要**在代码中硬编码服务器 IP、端口等
- ✅ 定期轮换 SSH 密钥
- ✅ 使用专用的部署账户（而非 root）提高安全性
