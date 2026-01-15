# 产品能力匹配系统 - 改进计划

## 📋 项目概述

**项目名称：** 产品能力匹配系统 (Product Capability Matching System)
**当前版本：** v1.0
**最后更新：** 2026-01-15
**GitHub：** https://github.com/xiejava1018/prod-answer

---

## 🎯 改进优先级

### 🔴 高优先级（立即执行）

#### 1. LLM 增强匹配分析
**状态：** 📝 计划中
**预计工作量：** 2-3 天
**负责人：** 待定

**背景：**
当前使用基于 pgvector 的向量相似度匹配，虽然速度快，但在理解深层逻辑和隐含需求方面有局限性。

**方案：两阶段混合匹配**

##### 阶段 1：向量快速初筛（保留现有）
```python
# 使用 SiliconFlow Embedding API
# 相似度阈值：0.75
# 返回：Top 20 候选功能
# 处理时间：30秒（183条需求）
```

##### 阶段 2：DeepSeek LLM 精确分析（新增）
```python
# 对 Top 20 候选进行深度分析
# 提供详细的匹配理由和置信度
# 处理时间：~20分钟（受 QPS 限制）
```

**技术方案：**

1. **创建 LLM 分析器**
```python
# backend/apps/matching/llm_analyzer.py
class DeepSeekAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )

    def analyze_match(self, requirement_text: str, feature: dict) -> dict:
        """分析需求与功能的匹配度"""
        prompt = f"""请分析以下需求与产品功能的匹配度：

需求描述：{requirement_text}

功能信息：
- 功能名称：{feature['feature_name']}
- 功能描述：{feature['description']}
- 产品名称：{feature['product_name']}

请从以下维度分析：
1. 完全满足：功能完全符合需求要求
2. 部分满足：功能部分符合，但有局限性
3. 不满足：功能不符合需求

返回格式（JSON）：
{{
    "satisfaction_level": "完全满足/部分满足/不满足",
    "confidence_score": 0.95,
    "reason": "详细分析理由",
    "limitations": ["局限性1", "局限性2"],
    "suggestions": "改进建议"
}}"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的产品需求分析专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        return json.loads(response.choices[0].message.content)
```

2. **集成到匹配服务**
```python
# backend/apps/matching/services.py
class MatchingService:
    def __init__(self, threshold=0.75, use_llm_enhancement=False):
        self.threshold = threshold
        self.use_llm_enhancement = use_llm_enhancement
        if use_llm_enhancement:
            self.llm_analyzer = DeepSeekAnalyzer()

    def _perform_matching(self, requirement, items):
        # 阶段1：向量快速初筛
        vector_matches = self._vector_matching(items)

        # 阶段2：LLM 精确分析（可选）
        if self.use_llm_enhancement:
            enhanced_matches = self._llm_enhancement(vector_matches)
            return enhanced_matches

        return vector_matches
```

**成本估算：**

| 方案 | 183条需求成本 | 处理时间 | 匹配质量 |
|------|--------------|---------|---------|
| 纯向量（当前） | ¥0.05 | 30秒 | ⭐⭐⭐ |
| 向量+LLM(top5) | ¥0.15 | 5分钟 | ⭐⭐⭐⭐ |
| 向量+LLM(top20) | ¥0.50 | 20分钟 | ⭐⭐⭐⭐⭐ |

**实施步骤：**

1. **Phase 1: 小规模测试**（1天）
   - [ ] 选择 10 条需求进行对比测试
   - [ ] 实现基础的 LLM 分析器
   - [ ] 对比向量 vs LLM 匹配效果
   - [ ] 评估效果提升是否值得成本

2. **Phase 2: 集成开发**（1天）
   - [ ] 添加 LLM 增强开关（use_llm_enhancement）
   - [ ] 实现两阶段匹配逻辑
   - [ ] 优化批量处理和错误重试
   - [ ] 添加进度反馈和日志

3. **Phase 3: 前端集成**（1天）
   - [ ] 添加匹配模式选择（快速/平衡/深度）
   - [ ] 显示 LLM 分析结果（理由、置信度）
   - [ ] 优化用户体验（进度提示、错误处理）
   - [ ] 更新导出报告（包含 LLM 分析）

**决策标准：**
- 如果小规模测试显示效果提升 > 30%，则继续实施
- 如果效果提升 < 20%，建议保持当前向量方案
- 考虑提供两种模式供用户选择

**依赖条件：**
- [ ] 申请 DeepSeek API Key
- [ ] 评估 API QPS 限制
- [ ] 确认预算支持（¥0.5/次，183条需求）

**风险：**
- API 调用可能超时或失败
- QPS 限制导致处理时间长
- 成本可能超出预期
- LLM 结果稳定性问题

**缓解措施：**
- 添加重试机制和超时处理
- 实现异步任务队列（Celery）
- 提供"快速模式"和"深度模式"切换
- 缓存 LLM 分析结果

---

### 🟡 中优先级（2-4周内）

#### 2. 数据库迁移到 PostgreSQL
**状态：** 📝 计划中
**预计工作量：** 3-5 天

**目标：**
- 从 SQLite 迁移到 PostgreSQL（生产环境）
- 优化 pgvector 索引性能
- 支持多用户并发访问

**方案选择：**

| 方案 | 适用场景 | 成本 | 推荐度 |
|------|---------|------|--------|
| 自建 PostgreSQL | 企业内部部署 | 服务器成本 | ⭐⭐⭐⭐⭐ |
| Supabase | SaaS 产品 | $25/月起 | ⭐⭐⭐⭐ |
| 继续 SQLite | 开发/测试 | 免费 | ⭐⭐⭐⭐⭐ |

**当前建议：**
- 开发/测试：继续使用 SQLite
- 生产部署：自建 PostgreSQL
- SaaS 产品：使用 Supabase

#### 3. 性能优化
**状态：** 📝 计划中
**预计工作量：** 2-3 天

**优化项：**
- [ ] 实现异步任务队列（Celery + Redis）
- [ ] 添加 Redis 缓存（嵌入向量缓存）
- [ ] 优化数据库查询（索引优化）
- [ ] 批量 API 调用优化
- [ ] 前端分页和虚拟滚动

#### 4. 用户体验改进
**状态：** 📝 计划中
**预计工作量：** 2-3 天

**改进项：**
- [ ] 添加实时进度反馈
- [ ] 优化错误提示和容错机制
- [ ] 支持需求批量导入
- [ ] 添加历史记录和版本对比
- [ ] 改进移动端适配

---

### 🟢 低优先级（未来迭代）

#### 5. 高级分析功能
**状态：** 💡 构思中
**预计工作量：** 5-7 天

**功能：**
- [ ] 需求聚类分析
- [ ] 产品能力图谱
- [ ] 差距分析和建议
- [ ] 趋势分析和预测
- [ ] 自动生成需求文档

#### 6. 多租户支持
**状态：** 💡 构思中
**预计工作量：** 7-10 天

**功能：**
- [ ] 用户权限管理
- [ ] 组织隔离
- [ ] 配额管理
- [ ] 审计日志

#### 7. 国际化支持
**状态：** 💡 构思中
**预计工作量：** 3-5 天

**功能：**
- [ ] 多语言界面（中英文）
- [ ] 多语言需求分析
- [ ] 本地化适配

---

## 📊 版本规划

### v1.1 (2026 Q1) - LLM 增强版
- ✅ 两阶段混合匹配
- ✅ LLM 分析结果展示
- ✅ 匹配模式选择
- ✅ 性能优化

### v1.2 (2026 Q2) - 生产就绪版
- ✅ PostgreSQL 迁移
- ✅ 异步任务队列
- ✅ 用户权限管理
- ✅ API 文档完善

### v1.3 (2026 Q3) - 企业版
- ✅ 多租户支持
- ✅ 高级分析功能
- ✅ 国际化支持
- ✅ 移动端优化

### v2.0 (2026 Q4) - 智能版
- ✅ AI 驱动的需求推荐
- ✅ 自动化测试生成
- ✅ 智能报告生成
- ✅ 实时协作功能

---

## 🔗 相关链接

- **GitHub 仓库：** https://github.com/xiejava1018/prod-answer
- **DeepSeek API：** https://platform.deepseek.com/
- **pgvector 文档：** https://github.com/pgvector/pgvector
- **Supabase 文档：** https://supabase.com/docs

---

## 📝 更新日志

### 2026-01-15
- ✅ 完成基础匹配功能（向量相似度）
- ✅ 实现文件上传和解析
- ✅ 添加 Excel 导出功能
- ✅ 修复分页和 URL 冲突问题
- ✅ 代码合并到 main 分支
- 📝 添加 LLM 增强匹配计划

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues: https://github.com/xiejava1018/prod-answer/issues
- Email: xiejava1018@qq.com

---

*本文档会随着项目进展持续更新*
