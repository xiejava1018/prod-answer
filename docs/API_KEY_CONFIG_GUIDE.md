# API密钥配置说明

## ✅ 已修复

**问题**：之前保存API密钥时出现500错误
**原因**：缺少 `ENCRYPTION_KEY` 环境变量
**解决**：系统现在会自动生成并管理加密密钥

---

## 🎯 如何配置API密钥

### 方法1：通过Web界面（推荐）

1. **访问配置页面**
   ```
   http://localhost:5173/embedding-settings
   ```

2. **编辑配置**
   - 找到 `siliconflow-bge-large-zh` 配置
   - 点击"编辑"按钮

3. **填写API密钥**
   - 在"API密钥"字段填入你的密钥
   - 格式类似：`sk-xxxxxxxxxxxxx`
   - 点击"保存"

4. **验证配置**
   - 保存后，列表中的"API密钥"列会显示"已配置"
   - 点击"测试连接"按钮验证是否可用

### 方法2：通过API（开发者）

```bash
# 更新API密钥
curl -X PUT http://localhost:8000/api/v1/configs/{config_id}/ \
  -H "Content-Type: application/json" \
  -d '{
    "api_key_encrypted": "sk-your-api-key-here"
  }'

# 响应示例
{
  "id": "2bca02d9-...",
  "model_name": "siliconflow-bge-large-zh",
  "has_api_key": true,
  ...
}
```

### 方法3：通过测试脚本

```bash
cd backend

# 使用测试脚本（会自动配置密钥）
export SILICONFLOW_API_KEY="sk-your-key"
python test_embedding.py siliconflow
```

---

## 🔐 安全说明

### API密钥加密存储

- ✅ API密钥会自动加密存储在数据库中
- ✅ 加密密钥保存在 `backend/.env` 文件中
- ✅ 即使数据库泄露，API密钥也是加密的

### 自动生成的加密密钥

系统首次运行时会自动生成 `ENCRYPTION_KEY`：

```bash
# 位置
backend/.env

# 内容示例
ENCRYPTION_KEY=_hpu7JIG-KETZJ9i1aYLHK5OllPs2QJkAW7lB3aSHm4=
```

**重要提示**：
- ⚠️ 不要将 `.env` 文件提交到版本控制
- ⚠️ 生产环境应使用环境变量设置 `ENCRYPTION_KEY`
- ⚠️ 丢失 `ENCRYPTION_KEY` 会导致所有已保存的API密钥无法解密

---

## 🔧 故障排除

### 问题1：保存API密钥时报错

**错误信息**：
```
更新失败: Request failed with status code 500
```

**解决方法**：
1. 确保后端服务正在运行
2. 检查后端日志：`tail -f /tmp/django_backend.log`
3. 如果是加密问题，删除 `backend/.env` 文件，重启后端让其自动生成

### 问题2：测试连接失败

**可能原因**：
- API密钥错误
- 网络问题
- API服务异常

**解决方法**：
1. 验证API密钥是否正确
2. 检查网络连接：`curl https://api.siliconflow.cn`
3. 查看后端日志了解详细错误

### 问题3：前端显示"未配置"但实际已配置

**原因**：缓存问题

**解决方法**：
1. 刷新页面
2. 退出并重新登录
3. 检查后端数据库：`python manage.py shell`
   ```python
   from apps.embeddings.models import EmbeddingModelConfig
   config = EmbeddingModelConfig.objects.get(model_name='siliconflow-bge-large-zh')
   print(f"API Key exists: {bool(config.api_key_encrypted)}")
   ```

---

## 📋 支持的API提供商

### 硅基流动 SiliconFlow（推荐）

**获取API密钥**：
1. 访问 https://siliconflow.cn/
2. 注册/登录账号
3. 进入"API密钥"页面
4. 创建新密钥

**配置参数**：
- 类型：`OpenAI-Compatible`
- 提供商：`硅基流动 SiliconFlow`
- Base URL：`https://api.siliconflow.cn/v1`
- 模型：`BAAI/bge-large-zh-v1.5`
- 维度：`1024`

**免费额度**：新用户有免费调用额度

### 智谱AI ZhipuAI

**获取API密钥**：
1. 访问 https://open.bigmodel.cn/
2. 注册并获取API Key

**配置参数**：
- 类型：`OpenAI-Compatible`
- 提供商：`智谱AI ZhipuAI`
- Base URL：`https://open.bigmodel.cn/api/paas/v4`
- 模型：`embedding-2`
- 维度：`1024`

### 阿里通义千问 Qwen

**获取API密钥**：
1. 访问 https://dashscope.aliyuncs.com/
2. 阿里云账号登录

**配置参数**：
- 类型：`OpenAI-Compatible`
- 提供商：`阿里通义千问 Qwen`
- Base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- 模型：`text-embedding-v3`
- 维度：`1536`

---

## 🎉 下一步

配置API密钥后，你可以：

1. ✅ 生成产品功能嵌入向量
2. ✅ 执行智能需求匹配
3. ✅ 使用语义相似度搜索
4. ✅ 导出匹配结果报告

详细使用方法请参考：
- [EMBEDDING_QUICKSTART.md](EMBEDDING_QUICKSTART.md) - 5分钟快速启动
- [EMBEDDING_API_GUIDE.md](EMBEDDING_API_GUIDE.md) - 完整配置指南
