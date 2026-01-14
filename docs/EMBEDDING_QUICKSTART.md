# 🚀 Embedding API 快速启动指南

## 5分钟快速配置硅基流动API

### 步骤1：获取API密钥（2分钟）

1. 访问 https://siliconflow.cn/
2. 注册/登录账号
3. 进入 "API密钥" 页面
4. 创建新的API密钥（格式：sk-xxxxx）
5. 复制保存密钥

### 步骤2：配置环境（1分钟）

```bash
# 1. 生成加密密钥
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. 设置环境变量（替换下面的值）
export ENCRYPTION_KEY="生成的加密密钥"
export SILICONFLOW_API_KEY="sk-你的硅基流动密钥"

# 3. 添加到 ~/.bashrc 或 ~/.zshrc 永久生效
echo 'export ENCRYPTION_KEY="你的加密密钥"' >> ~/.bashrc
echo 'export SILICONFLOW_API_KEY="sk-你的密钥"' >> ~/.bashrc
source ~/.bashrc
```

### 步骤3：初始化系统（1分钟）

```bash
cd /Users/xiejava/AIproject/prod-answer/backend

# 初始化Embedding配置
source venv/bin/activate
export USE_SQLITE=True
python manage.py init_embedding_config

# 你会看到：
# ✓ Created: siliconflow-bge-large-zh - 硅基流动 BGE中文大模型 (推荐)
# ✓ Created: zhipuai-embedding-2 - 智谱AI Embedding-2模型
# ✓ Created: qwen-embedding-v1 - 阿里通义千问 Embedding模型
```

### 步骤4：配置API密钥（1分钟）

**方法1：通过管理后台（推荐）**

```bash
# 创建超级用户（如果还没有）
python manage.py createsuperuser

# 启动服务
python manage.py runserver
```

访问 http://localhost:8000/admin
1. 登录
2. 点击 "Embedding Model Configs"
3. 点击 "siliconflow-bge-large-zh"
4. 在 "API Key (encrypted)" 字段填入：`sk-你的密钥`
5. 点击 "Save"

**方法2：通过测试脚本**

```bash
# 确保已设置环境变量
export SILICONFLOW_API_KEY="sk-你的密钥"

# 运行测试脚本（会自动配置密钥）
python test_embedding.py siliconflow
```

### 步骤5：测试验证（30秒）

```bash
# 运行测试
python test_embedding.py siliconflow

# 你会看到：
# ==============================================================================
# 测试硅基流动 API (SiliconFlow)
# ==============================================================================
#
# 1. 测试连接...
#    ✓ 连接成功
#
# 2. 测试文本编码...
#    ✓ 成功编码 3 个文本
#    ✓ 嵌入维度: 1024
#    ✓ 示例向量前5个值: [0.1234, -0.5678, ...]
#
# 3. 测试相似度计算...
#    ✓ 相似度计算成功
#    ✓ '产品能力匹配系统' 与 '智能推荐算法' 的相似度: 0.7823
#
# ==============================================================================
# ✓ 所有测试通过！硅基流动API配置正确
# ==============================================================================
```

## ✅ 完成！

现在你的系统已配置好硅基流动API，可以：
- 生成产品功能嵌入向量
- 进行智能需求匹配
- 使用语义相似度搜索

## 🔧 切换到智谱AI

如果需要切换到智谱AI：

```bash
# 1. 获取智谱AI密钥
# 访问 https://open.bigmodel.cn/

# 2. 设置环境变量
export ZHIPUAI_API_KEY="你的智谱密钥"

# 3. 测试
python test_embedding.py zhipuai

# 4. 设置为默认
python manage.py shell
>>> from apps.embeddings.models import EmbeddingModelConfig
>>> zhipuai = EmbeddingModelConfig.objects.get(model_name='zhipuai-embedding-2')
>>> zhipuai.is_default = True
>>> zhipuai.save()
```

## 📚 更多信息

详细配置指南：[EMBEDDING_API_GUIDE.md](EMBEDDING_API_GUIDE.md)
项目文档：[PROJECT_DELIVERY.md](PROJECT_DELIVERY.md)

## 💡 常见问题

**Q: 免费额度有多少？**
- 硅基流动：新用户有较大的免费额度
- 智谱AI：新用户有免费额度
- 具体数量请查看各平台官网

**Q: 如何查看API调用次数？**
- 登录各平台控制台查看使用统计

**Q: 忘记保存API密钥怎么办？**
- 需要重新生成新的API密钥
- 旧密钥无法找回（安全考虑）

**Q: 可以同时配置多个API吗？**
- 可以！系统支持配置多个提供商
- 通过 `is_default` 字段指定使用哪个

## 🆘 遇到问题？

1. 检查环境变量是否正确设置：`echo $SILICONFLOW_API_KEY`
2. 检查网络连接：`curl https://api.siliconflow.cn`
3. 查看后端日志：`tail -f /tmp/django_backend.log`
4. 查看文档：[EMBEDDING_API_GUIDE.md](EMBEDDING_API_GUIDE.md)
