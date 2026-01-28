# LLM增强的智能匹配系统设计方案

**日期:** 2025-01-28
**状态:** 设计阶段
**优先级:** 高

---

## 1. 背景与目标

### 1.1 当前问题
- **误匹配/漏匹配**: 纯向量相似度匹配在某些场景下不够准确
- **缺乏解释性**: 用户无法理解为什么匹配某个功能
- **难以审核**: 没有足够的上下文信息支持人工判断

### 1.2 设计目标
1. **提高匹配精度**: 减少误匹配和漏匹配
2. **增强可解释性**: 提供匹配原因说明和关键词高亮
3. **支持误配纠正**: LLM能发现并纠正向量匹配的错误
4. **智能重排序**: 基于语义理解优化结果顺序

---

## 2. 系统架构

### 2.1 整体流程

系统采用**两阶段匹配架构**，结合向量检索的速度和LLM的智能理解能力。

```
┌─────────────────────────────────────────────────────────────┐
│                        用户需求输入                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段1: 向量检索 (Vector Search - 现有)                     │
│  - 快速检索 Top-20 候选功能                                 │
│  - 基于余弦相似度初步排序                                   │
│  - 输出: 候选匹配列表 (相似度分数)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段2: LLM智能分析 (NEW)                                   │
│  1. 匹配原因生成: 自然语言解释匹配合理性                    │
│  2. 关键词提取: 需求和功能的关键匹配词                      │
│  3. 误配检测: 标记不合理匹配, 补充遗漏功能                  │
│  4. 结果重排序: 基于语义理解重新排序                        │
│  - 输出: 结构化分析结果 (JSON)                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段3: 结果融合 (Result Fusion)                            │
│  - 合并向量分数和LLM评估                                    │
│  - 计算最终置信度 (加权融合)                                │
│  - 返回增强的匹配结果                                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术架构

```
Backend (Django)
├── Matching Service
│   ├── Vector Search (pgvector)
│   ├── LLM Analysis Service (NEW)
│   │   ├── LLM Provider Factory
│   │   ├── Prompt Templates
│   │   ├── Response Parser
│   │   └── Cache Manager
│   └── Result Fusion
│
├── LLM Integration Layer
│   ├── OpenAI Provider
│   ├── ZhipuAI Provider
│   ├── Qwen Provider
│   └── SiliconFlow Provider
│
└── Celery Tasks
    ├── Async LLM Analysis
    ├── Batch Processing
    └── Result Caching

Frontend (Vue 3)
├── Match Results Display
│   ├── Match Reason Card
│   ├── Keyword Highlighting
│   ├── Confidence Badge
│   └── Mismatch Alert
│
└── Comparison View
    ├── Side-by-side Comparison
    └── Diff Highlighter
```

---

## 3. 数据模型设计

### 3.1 新增模型

#### 3.1.1 LLMAnalysisResult
```python
class LLMAnalysisResult(TimeStampedModel):
    """LLM分析结果模型"""

    requirement_item = models.ForeignKey(
        'RequirementItem',
        on_delete=models.CASCADE,
        related_name='llm_analyses'
    )

    feature = models.ForeignKey(
        'products.Feature',
        on_delete=models.CASCADE,
        related_name='llm_analyses'
    )

    # LLM分析内容
    match_reason = models.TextField(help_text="匹配原因说明")
    keywords_from_requirement = models.JSONField(
        default=list,
        help_text="需求文本中的关键词"
    )
    keywords_from_feature = models.JSONField(
        default=list,
        help_text="功能描述中的关键词"
    )

    # LLM评估
    is_valid_match = models.BooleanField(default=True)
    confidence_score = models.FloatField(
        default=0.0,
        help_text="LLM置信度 (0-1)"
    )

    # 元数据
    llm_provider = models.CharField(max_length=50)
    llm_model = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)

    class Meta:
        db_table = 'llm_analysis_results'
        unique_together = [['requirement_item', 'feature']]
```

#### 3.1.2 LLMCache
```python
class LLMCache(TimeStampedModel):
    """LLM结果缓存"""

    cache_key = models.CharField(max_length=255, unique=True)
    requirement_text = models.TextField()
    feature_ids = models.JSONField()

    # 缓存的LLM响应
    response_json = models.JSONField()

    # 统计
    hit_count = models.IntegerField(default=0)
    last_hit_at = models.DateTimeField(null=True, blank=True)

    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'llm_cache'
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
        ]
```

### 3.2 模型修改

#### 3.2.1 MatchRecord 扩展
```python
# 新增字段
class MatchRecord(TimeStampedModel):
    # ... 现有字段 ...

    # LLM增强字段
    llm_analysis = models.ForeignKey(
        'LLMAnalysisResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='match_record'
    )

    final_confidence = models.FloatField(
        default=0.0,
        help_text="融合后的最终置信度"
    )

    is_llm_corrected = models.BooleanField(
        default=False,
        help_text="是否被LLM纠正"
    )
```

---

## 4. LLM Provider设计

### 4.1 LLM Provider接口

```python
class BaseLLMProvider(ABC):
    """LLM Provider基类"""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def analyze_matches(
        self,
        requirement_text: str,
        candidates: List[Dict],
        analysis_config: Dict
    ) -> Dict:
        """
        分析匹配结果

        Args:
            requirement_text: 需求文本
            candidates: 候选功能列表
            analysis_config: 分析配置

        Returns:
            LLM分析结果 (结构化JSON)
        """
        pass

    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """估算调用成本"""
        pass
```

### 4.2 支持的Provider

1. **OpenAI** (GPT-4o, GPT-4o-mini)
2. **ZhipuAI** (GLM-4-Flash, GLM-4-Plus)
3. **Qwen** (qwen-plus, qwen-turbo)
4. **SiliconFlow** (多种模型代理)

### 4.3 Provider配置

```python
class LLMProviderConfig(TimeStampedModel):
    """LLM Provider配置"""

    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('zhipuai', 'ZhipuAI'),
        ('qwen', 'Qwen'),
        ('siliconflow', 'SiliconFlow'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model_name = models.CharField(max_length=100)
    api_key_encrypted = models.CharField(max_length=255)

    # 配置参数
    temperature = models.FloatField(default=0.3)
    max_tokens = models.IntegerField(default=2000)
    top_p = models.FloatField(default=0.9)

    # 成本控制
    max_candidates_per_request = models.IntegerField(default=20)
    enable_cache = models.BooleanField(default=True)
    cache_ttl_hours = models.IntegerField(default=24)

    # 默认标记
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'llm_provider_configs'
        verbose_name = 'LLM Provider Configuration'
```

---

## 5. Prompt设计

### 5.1 匹配分析Prompt模板

```python
MATCH_ANALYSIS_PROMPT = """你是一个专业的产品功能匹配分析专家。

## 任务
分析用户需求与产品功能的匹配程度，并提供详细的解释和建议。

## 用户需求
{requirement_text}

## 候选功能列表
{candidates_list}

## 分析要求

对每个候选功能，请提供以下分析：

1. **匹配程度** (matched/partial_matched/unmatched)
   - matched: 功能完全满足需求
   - partial_matched: 功能部分满足需求
   - unmatched: 功能不满足需求

2. **匹配原因** (2-3句话)
   - 说明为什么这个功能能/不能匹配需求
   - 强调核心的匹配点或不匹配点

3. **关键词提取**
   - 从需求中提取 3-5 个关键需求词
   - 从功能描述中提取 3-5 个关键特征词
   - 这些词是匹配的核心依据

4. **置信度评分** (0.0-1.0)
   - 基于你的分析，给出匹配的可信程度

5. **补充建议** (可选)
   - 是否有遗漏的重要功能？
   - 是否有某些候选明显不合适？

## 输出格式 (JSON)
请严格按照以下JSON格式输出：

```json
{{
  "analysis_results": [
    {{
      "feature_id": "UUID",
      "match_status": "matched|partial_matched|unmatched",
      "match_reason": "匹配原因说明",
      "keywords_from_requirement": ["关键词1", "关键词2", ...],
      "keywords_from_feature": ["关键词1", "关键词2", ...],
      "confidence_score": 0.95,
      "is_valid_match": true
    }}
  ],
  "suggestions": {{
    "missed_features": ["功能A", "功能B"],
    "should_exclude": ["feature_id_X"]
  }}
}}
```

请开始分析："""
```

### 5.2 简化版Prompt（低成本场景）

```python
QUICK_MATCH_PROMPT = """分析需求与功能的匹配度。

需求: {requirement_text}

功能: {feature_name} - {feature_description}

请提供:
1. 匹配原因 (一句话)
2. 需求关键词 (2-3个)
3. 功能关键词 (2-3个)
4. 是否合理匹配 (yes/no)

输出JSON格式。"""
```

---

## 6. API设计

### 6.1 新增API端点

#### 6.1.1 LLM配置管理
```
GET    /api/v1/llm/configs/              # 列出所有配置
POST   /api/v1/llm/configs/              # 创建配置
PUT    /api/v1/llm/configs/{id}/         # 更新配置
DELETE /api/v1/llm/configs/{id}/         # 删除配置
POST   /api/v1/llm/configs/{id}/test/    # 测试连接
```

#### 6.1.2 LLM分析
```
POST /api/v1/llm/analyze/                # 执行LLM分析
GET  /api/v1/llm/analyses/{id}/          # 获取分析结果
POST /api/v1/llm/batch-analyze/          # 批量分析
```

#### 6.1.3 增强的匹配API
```
POST /api/v1/matching/analyze-enhanced/  # LLM增强匹配
```

### 6.2 请求/响应示例

#### 6.2.1 增强匹配请求
```json
POST /api/v1/matching/analyze-enhanced/

{
  "requirement_id": "uuid",
  "enable_llm_analysis": true,
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "max_candidates": 10
  },
  "matching_params": {
    "threshold": 0.75,
    "top_k": 20
  }
}
```

#### 6.2.2 增强匹配响应
```json
{
  "requirement_id": "uuid",
  "matches": [
    {
      "feature_id": "uuid",
      "feature_name": "资产发现",
      "similarity_score": 0.87,
      "match_status": "matched",
      "rank": 1,

      // LLM增强信息
      "llm_analysis": {
        "match_reason": "该功能提供自动化的资产发现能力，支持多种资产类型（主机、网络设备、数据库等），完全满足需求中提到的'资产管理'和'自动发现'要求。",
        "keywords_from_requirement": ["资产管理", "自动发现", "资产拓扑"],
        "keywords_from_feature": ["资产发现", "自动扫描", "资产识别", "拓扑映射"],
        "confidence_score": 0.95,
        "is_valid_match": true
      },

      // 融合分数
      "final_confidence": 0.91
    }
  ],

  // LLM建议
  "llm_suggestions": {
    "missed_features": ["漏洞扫描", "配置审计"],
    "should_exclude": ["feature_id_123"]
  },

  "metadata": {
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "llm_latency_ms": 1234,
    "cost_estimate_usd": 0.002
  }
}
```

---

## 7. 前端设计

### 7.1 匹配结果卡片组件

```vue
<template>
  <el-card class="match-card">
    <!-- 基本信息 -->
    <div class="match-header">
      <el-tag :type="getStatusType(match.match_status)">
        {{ match.match_status }}
      </el-tag>
      <span class="similarity">
        相似度: {{ (match.similarity_score * 100).toFixed(1) }}%
      </span>
      <el-badge
        v-if="match.llm_analysis"
        :value="(match.llm_analysis.confidence_score * 100).toFixed(0) + '%'"
        class="confidence-badge"
      >
        LLM置信度
      </el-badge>
    </div>

    <!-- 功能信息 -->
    <h3>{{ match.feature_name }}</h3>
    <p class="description">{{ match.feature_description }}</p>

    <!-- LLM分析结果 -->
    <div v-if="match.llm_analysis" class="llm-analysis">
      <el-divider content-position="left">
        <el-icon><ChatDotSquare /></el-icon>
        AI分析
      </el-divider>

      <!-- 匹配原因 -->
      <div class="match-reason">
        <el-icon class="reason-icon"><InfoFilled /></el-icon>
        <span>{{ match.llm_analysis.match_reason }}</span>
      </div>

      <!-- 关键词高亮 -->
      <div class="keywords-section">
        <div class="keyword-group">
          <span class="label">需求关键词:</span>
          <el-tag
            v-for="word in match.llm_analysis.keywords_from_requirement"
            :key="word"
            type="primary"
            size="small"
            effect="plain"
          >
            {{ word }}
          </el-tag>
        </div>
        <div class="keyword-group">
          <span class="label">功能关键词:</span>
          <el-tag
            v-for="word in match.llm_analysis.keywords_from_feature"
            :key="word"
            type="success"
            size="small"
            effect="plain"
          >
            {{ word }}
          </el-tag>
        </div>
      </div>

      <!-- 误配警告 -->
      <el-alert
        v-if="!match.llm_analysis.is_valid_match"
        type="warning"
        :closable="false"
        show-icon
      >
        AI认为此匹配可能不准确，建议人工审核
      </el-alert>
    </div>

    <!-- 操作按钮 -->
    <div class="actions">
      <el-button size="small" @click="viewDetails">
        查看详情
      </el-button>
      <el-button
        v-if="match.llm_analysis"
        size="small"
        type="primary"
        @click="compareWithRequirement"
      >
        对比分析
      </el-button>
    </div>
  </el-card>
</template>
```

### 7.2 对比分析视图

```vue
<template>
  <div class="comparison-view">
    <el-row :gutter="20">
      <!-- 需求文本 -->
      <el-col :span="12">
        <el-card header="用户需求">
          <div class="text-with-highlight">
            {{ requirementText }}
            <el-tooltip
              v-for="keyword in requirementKeywords"
              :key="keyword"
              :content="keyword"
              placement="top"
            >
              <mark class="highlight-req">{{ keyword }}</mark>
            </el-tooltip>
          </div>
        </el-card>
      </el-col>

      <!-- 功能描述 -->
      <el-col :span="12">
        <el-card header="功能描述">
          <div class="text-with-highlight">
            {{ featureDescription }}
            <el-tooltip
              v-for="keyword in featureKeywords"
              :key="keyword"
              :content="keyword"
              placement="top"
            >
              <mark class="highlight-feat">{{ keyword }}</mark>
            </el-tooltip>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 匹配原因 -->
    <el-card header="AI匹配分析" class="analysis-card">
      <p>{{ llmAnalysis.match_reason }}</p>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="匹配状态">
          <el-tag :type="getStatusType(llmAnalysis.match_status)">
            {{ llmAnalysis.match_status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="置信度">
          <el-progress
            :percentage="llmAnalysis.confidence_score * 100"
            :color="getConfidenceColor(llmAnalysis.confidence_score)"
          />
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>
```

---

## 8. 实现计划

### 8.1 开发阶段

#### Phase 1: 基础设施 (3-4天)
- [ ] 创建LLM Provider抽象层
- [ ] 实现OpenAI Provider
- [ ] 实现ZhipuAI Provider
- [ ] 数据库迁移（新模型）
- [ ] LLM配置管理API

#### Phase 2: 核心功能 (4-5天)
- [ ] LLM分析服务实现
- [ ] Prompt模板设计
- [ ] 响应解析器
- [ ] 缓存机制
- [ ] Celery异步任务

#### Phase 3: API集成 (2-3天)
- [ ] 增强匹配API端点
- [ ] 批量分析接口
- [ ] 错误处理和重试
- [ ] 成本追踪

#### Phase 4: 前端开发 (3-4天)
- [ ] 匹配结果卡片组件
- [ ] 关键词高亮组件
- [ ] 对比分析视图
- [ ] LLM配置管理界面

#### Phase 5: 测试与优化 (2-3天)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 成本优化

### 8.2 时间估算

| 阶段 | 工作量 | 说明 |
|-----|--------|------|
| Phase 1: 基础设施 | 3-4天 | LLM Provider层、数据模型 |
| Phase 2: 核心功能 | 4-5天 | LLM分析服务、Prompt工程 |
| Phase 3: API集成 | 2-3天 | RESTful API、异步处理 |
| Phase 4: 前端开发 | 3-4天 | UI组件、交互优化 |
| Phase 5: 测试优化 | 2-3天 | 测试、性能调优 |
| **总计** | **14-19天** | 约2.5-3.5周 |

**关键路径:**
- 后端开发 (Phase 1-3): 9-12天
- 前端开发 (Phase 4): 3-4天（可与Phase 3并行）
- 测试优化 (Phase 5): 2-3天

**风险因素:**
- Prompt调优可能需要额外2-3天
- LLM API限流可能需要实现更多优化
- 多Provider集成可能增加复杂度

---

## 9. 成本估算

### 9.1 LLM调用成本

假设使用GPT-4o-mini:
- 输入: ~800 tokens (需求 + 20个功能)
- 输出: ~1500 tokens (结构化分析)
- 单次成本: ~$0.002

使用GPT-4o:
- 单次成本: ~$0.01

使用ZhipuAI GLM-4-Flash:
- 单次成本: ~¥0.001 (约$0.00014)

### 9.2 月度成本估算

| 场景 | 每日分析 | 月度成本 (GPT-4o-mini) | 月度成本 (GLM-4-Flash) |
|-----|---------|----------------------|----------------------|
| 低频 | 50次 | $3 | $0.21 |
| 中频 | 200次 | $12 | $0.84 |
| 高频 | 1000次 | $60 | $4.20 |

### 9.3 成本优化建议

1. **使用缓存**: 相同需求复用结果，节省30-50%成本
2. **选择模型**: 非关键场景使用低成本模型
3. **批量处理**: 合并多个需求减少调用次数
4. **按需开启**: 用户可选是否使用LLM分析

---

## 10. 风险与挑战

### 10.1 技术风险

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| LLM输出不稳定 | 高 | 多轮Prompt调优、输出验证 |
| API限流 | 中 | 实现队列、重试机制、多Provider |
| 成本过高 | 中 | 缓存、模型选择、批量优化 |
| 响应延迟 | 中 | 异步处理、进度反馈 |

### 10.2 产品风险

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| LLM分析质量不稳定 | 高 | A/B测试、人工审核反馈 |
| 用户体验不一致 | 中 | 提供开关、渐进式发布 |
| 依赖外部服务 | 中 | 多Provider支持、降级方案 |

---

## 11. 成功指标

### 11.1 质量指标
- **误配率降低**: 目标从当前15%降至5%以下
- **漏配率降低**: 目标从当前10%降至3%以下
- **用户满意度**: 通过反馈评分，目标4.5/5.0

### 11.2 性能指标
- **响应时间**: LLM分析 < 3秒 (90th percentile)
- **缓存命中率**: > 40%
- **可用性**: > 99.5%

### 11.3 成本指标
- **单次分析成本**: < $0.005 (使用缓存和优化)
- **月度成本控制**: 可预测、可监控

---

## 12. 后续优化方向

### 12.1 短期优化 (1-3个月)
- 引入更多LLM模型支持
- Prompt自动调优
- 用户反馈学习循环

### 12.2 中期优化 (3-6个月)
- 微调专属模型
- 多模态输入（图片、表格）
- 历史匹配分析

### 12.3 长期优化 (6-12个月)
- 端到端神经网络匹配
- 主动学习机制
- 个性化匹配策略

---

## 13. 附录

### 13.1 相关文档
- [EMBEDDING_API_GUIDE.md](../EMBEDDING_API_GUIDE.md) - Embedding配置指南
- [API.md](../API.md) - API文档
- [improvement-plan.md](../improvement-plan.md) - 系统改进计划

### 13.2 参考资料
- OpenAI API文档
- ZhipuAI API文档
- LangChain Prompt工程指南

---

**文档版本:** 1.0
**最后更新:** 2025-01-28
**作者:** Claude Code
**审核状态:** 待审核
