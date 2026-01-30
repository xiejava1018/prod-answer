<template>
  <div class="match-result-detail-enhanced">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        <div class="page-title">
          <span>匹配结果详情</span>
          <el-tag v-if="hasLLMAnalysis" type="success" class="ml-10">
            <el-icon><MagicStick /></el-icon>
            LLM增强分析
          </el-tag>
        </div>
      </template>
    </el-page-header>

    <!-- Loading -->
    <div v-if="loading" class="text-center">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- Results -->
    <div v-else-if="matchResults">
      <!-- Summary Cards -->
      <el-row :gutter="20" class="mb-20">
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="总需求数" :value="statistics.total_items">
              <template #prefix>
                <el-icon style="vertical-align: -0.125em">
                  <Document />
                </el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="完全满足" :value="statistics.matched">
              <template #prefix>
                <el-icon style="vertical-align: -0.125em; color: var(--el-color-success)">
                  <CircleCheck />
                </el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="部分满足" :value="statistics.partial_matched">
              <template #prefix>
                <el-icon style="vertical-align: -0.125em; color: var(--el-color-warning)">
                  <Warning />
                </el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="不满足" :value="statistics.unmatched">
              <template #prefix>
                <el-icon style="vertical-align: -0.125em; color: var(--el-color-danger)">
                  <CircleClose />
                </el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
      </el-row>

      <!-- LLM Analysis Summary (if available) -->
      <el-card v-if="hasLLMAnalysis" class="mb-20 llm-summary-card">
        <template #header>
          <div class="card-header">
            <span>
              <el-icon><MagicStick /></el-icon>
              LLM分析摘要
            </span>
            <el-tag type="info">
              分析了 {{ totalLLMAnalyses }} 个匹配项
            </el-tag>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="llm-stat">
              <span class="label">有效匹配</span>
              <span class="value">{{ llmStats.validMatches }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="llm-stat">
              <span class="label">无效匹配</span>
              <span class="value">{{ llmStats.invalidMatches }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="llm-stat">
              <span class="label">平均置信度</span>
              <span class="value">{{ (llmStats.avgConfidence * 100).toFixed(1) }}%</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- Main Table with Filter -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span>需求规格满足度分析</span>
            <el-space>
              <el-select
                v-model="filterStatus"
                placeholder="全部"
                clearable
                style="width: 200px"
                @change="handleFilterChange"
              >
                <el-option label="全部" value="" />
                <el-option label="完全满足" value="matched" />
                <el-option label="部分满足" value="partial_matched" />
                <el-option label="不满足" value="unmatched" />
              </el-select>
              <el-checkbox v-model="showLLMOnly" v-if="hasLLMAnalysis">
                仅显示LLM分析
              </el-checkbox>
            </el-space>
          </div>
        </template>

        <el-table :data="filteredResults" border stripe>
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="requirement_item_text" label="需求规格" min-width="300">
            <template #default="{ row }">
              <div class="requirement-text-with-highlight">
                <span v-html="highlightKeywords(row.requirement_item_text, row.matches?.[0]?.llm_analysis?.keywords_from_requirement)"></span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="需求规格满足度" width="150" align="center">
            <template #default="{ row }">
              <el-space direction="vertical" :size="4">
                <el-tag
                  :type="getSatisfactionType(row.match_status)"
                  size="large"
                >
                  {{ getSatisfactionText(row.match_status) }}
                </el-tag>
                <el-tag v-if="row.matches?.[0]?.is_llm_corrected" type="warning" size="small">
                  <el-icon><Refresh /></el-icon>
                  LLM纠正
                </el-tag>
              </el-space>
            </template>
          </el-table-column>
          <el-table-column label="规格满足度详细描述" min-width="500">
            <template #default="{ row }">
              <div v-if="row.matches && row.matches.length > 0" class="satisfaction-detail">
                <!-- 只显示排名第一的最佳匹配 -->
                <div
                  v-for="(match, index) in row.matches.slice(0, 1)"
                  :key="index"
                  class="match-item-enhanced is-best"
                >
                  <!-- Header: Status badges and confidence -->
                  <div class="detail-header">
                    <el-space>
                      <el-tag
                        :type="getSatisfactionType(row.match_status)"
                        size="small"
                      >
                        相似度: {{ (match.similarity_score * 100).toFixed(1) }}%
                      </el-tag>
                      <el-tag type="info" size="small">
                        排名: {{ match.rank }}
                      </el-tag>
                      <el-tag v-if="index === 0" type="success" size="small">
                        最佳匹配
                      </el-tag>
                      <!-- Final confidence (fused score) -->
                      <el-tag v-if="match.final_confidence" type="primary" size="small">
                        融合置信度: {{ (match.final_confidence * 100).toFixed(1) }}%
                      </el-tag>
                      <!-- Comparison button -->
                      <el-button
                        link
                        type="primary"
                        size="small"
                        @click="openComparisonDialog(row.requirement_item_text, match)"
                      >
                        <el-icon><DocumentCopy /></el-icon>
                        对比分析
                      </el-button>
                    </el-space>
                  </div>

                  <!-- LLM Analysis Section -->
                  <div v-if="match.llm_analysis" class="llm-analysis-section">
                    <el-divider content-position="left">
                      <el-icon><MagicStick /></el-icon>
                      AI分析结果
                    </el-divider>

                    <!-- Match validity and confidence -->
                    <div class="llm-metrics">
                      <div class="metric-item">
                        <span class="label">匹配有效性:</span>
                        <el-tag v-if="match.llm_analysis.is_valid_match === true" type="success" size="small">
                          ✓ 有效匹配
                        </el-tag>
                        <el-tag v-else-if="match.llm_analysis.is_valid_match === false" type="danger" size="small">
                          ✗ 无效匹配
                        </el-tag>
                        <el-tag v-else type="info" size="small">
                          未确定
                        </el-tag>
                      </div>

                      <div class="metric-item">
                        <span class="label">AI置信度:</span>
                        <el-progress
                          :percentage="match.llm_analysis.confidence_score * 100"
                          :color="getConfidenceColor(match.llm_analysis.confidence_score)"
                          :stroke-width="8"
                          style="width: 150px"
                        />
                      </div>
                    </div>

                    <!-- Match reason -->
                    <div v-if="match.llm_analysis.match_reason" class="match-reason">
                      <div class="reason-header">
                        <el-icon><ChatLineRound /></el-icon>
                        <span>匹配原因</span>
                      </div>
                      <p class="reason-text">{{ match.llm_analysis.match_reason }}</p>
                    </div>

                    <!-- Keywords from requirement -->
                    <div v-if="match.llm_analysis.keywords_from_requirement?.length" class="keywords-section">
                      <div class="keywords-header">
                        <el-icon><PriceTag /></el-icon>
                        <span>需求关键词</span>
                      </div>
                      <div class="keywords-list">
                        <el-tag
                          v-for="(keyword, idx) in match.llm_analysis.keywords_from_requirement"
                          :key="idx"
                          type="primary"
                          size="small"
                          class="keyword-tag"
                          effect="plain"
                        >
                          {{ keyword }}
                        </el-tag>
                      </div>
                    </div>

                    <!-- Keywords from feature -->
                    <div v-if="match.llm_analysis.keywords_from_feature?.length" class="keywords-section">
                      <div class="keywords-header">
                        <el-icon><PriceTag /></el-icon>
                        <span>功能关键词</span>
                      </div>
                      <div class="keywords-list">
                        <el-tag
                          v-for="(keyword, idx) in match.llm_analysis.keywords_from_feature"
                          :key="idx"
                          type="success"
                          size="small"
                          class="keyword-tag"
                          effect="plain"
                        >
                          {{ keyword }}
                        </el-tag>
                      </div>
                    </div>

                    <!-- Token usage -->
                    <div class="token-usage">
                      <el-text size="small" type="info">
                        Token使用: {{ match.llm_analysis.total_tokens }}
                        ({{ match.llm_analysis.llm_provider }}/{{ match.llm_analysis.llm_model }})
                      </el-text>
                    </div>
                  </div>

                  <!-- Feature details -->
                  <div class="detail-content">
                    <div class="feature-info">
                      <span class="label">匹配功能:</span>
                      <span class="value">{{ match.feature_name }}</span>
                    </div>
                    <div class="feature-desc">
                      <span class="label">功能描述:</span>
                      <span
                        class="value"
                        v-html="highlightKeywords(match.feature_description, match.llm_analysis?.keywords_from_feature)"
                      ></span>
                    </div>
                    <div v-if="match.product_name" class="product-info">
                      <span class="label">产品:</span>
                      <span class="value">{{ match.product_name }}</span>
                    </div>
                  </div>

                  <el-divider v-if="index < (row.matches?.length || 1) - 1" />
                </div>
              </div>
              <div v-else class="no-match">
                <el-text type="info">未找到匹配的功能</el-text>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <el-empty
          v-if="filteredResults.length === 0"
          description="暂无数据"
        />
      </el-card>

      <!-- Statistics -->
      <el-card class="mt-20">
        <template #header>
          <div class="card-header">
            <span>统计信息</span>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="平均相似度" :value="statistics.avg_similarity * 100" :precision="2">
              <template #suffix>
                <span>%</span>
                <el-icon style="vertical-align: -0.125em">
                  <TrendCharts />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="8">
            <el-statistic title="最高相似度" :value="statistics.max_similarity * 100" :precision="2">
              <template #suffix>
                <span>%</span>
                <el-icon style="vertical-align: -0.125em; color: var(--el-color-success)">
                  <Top />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="8">
            <el-statistic title="最低相似度" :value="statistics.min_similarity * 100" :precision="2">
              <template #suffix>
                <span>%</span>
                <el-icon style="vertical-align: -0.125em; color: var(--el-color-info)">
                  <Bottom />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>
      </el-card>

      <!-- Export -->
      <div class="mt-20 text-center">
        <el-button type="primary" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
        <el-button @click="$router.back()">返回</el-button>
      </div>
    </div>

    <!-- Error State -->
    <el-card v-else>
      <el-empty description="未找到匹配结果">
        <el-button type="primary" @click="$router.push('/matching')">
          前往匹配分析
        </el-button>
      </el-empty>
    </el-card>

    <!-- Comparison Dialog -->
    <el-dialog
      v-model="comparisonDialogVisible"
      title="匹配对比分析"
      width="90%"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <MatchingComparison
        v-if="selectedMatch"
        :requirement-text="selectedRequirementText"
        :feature-description="selectedMatch.feature_description || ''"
        :match-data="selectedMatch"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMatchingStore } from '@/store'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import MatchingComparison from '@/components/MatchingComparison.vue'
import {
  Document,
  CircleCheck,
  Warning,
  CircleClose,
  TrendCharts,
  Top,
  Bottom,
  Download,
  MagicStick,
  Refresh,
  ChatLineRound,
  PriceTag
} from '@element-plus/icons-vue'

const route = useRoute()
const matchingStore = useMatchingStore()

const loading = ref(true)
const filterStatus = ref('')
const showLLMOnly = ref(false)

// Comparison dialog state
const comparisonDialogVisible = ref(false)
const selectedMatch = ref<any>(null)
const selectedRequirementText = ref('')

const requirementId = computed(() => route.params.id as string)

const matchResults = computed(() => matchingStore.matchResults)
const statistics = computed(() => matchResults.value?.statistics || {
  total_items: 0,
  total_matches: 0,
  matched: 0,
  partial_matched: 0,
  unmatched: 0,
  avg_similarity: 0,
  max_similarity: 0,
  min_similarity: 0
})

// Check if any results have LLM analysis
const hasLLMAnalysis = computed(() => {
  const results = matchResults.value?.results
  if (!results) return false

  const allMatches = [
    ...(results.matched || []),
    ...(results.partial_matched || []),
    ...(results.unmatched || [])
  ]

  return allMatches.some((match: any) => match.llm_analysis)
})

// LLM Statistics
const totalLLMAnalyses = computed(() => {
  const results = matchResults.value?.results
  if (!results) return 0

  const allMatches = [
    ...(results.matched || []),
    ...(results.partial_matched || []),
    ...(results.unmatched || [])
  ]

  return allMatches.filter((m: any) => m.llm_analysis).length
})

const llmStats = computed(() => {
  const results = matchResults.value?.results
  if (!results) return { validMatches: 0, invalidMatches: 0, avgConfidence: 0 }

  const allMatches = [
    ...(results.matched || []),
    ...(results.partial_matched || []),
    ...(results.unmatched || [])
  ]

  const analyzedMatches = allMatches.filter((m: any) => m.llm_analysis)

  const valid = analyzedMatches.filter((m: any) => m.llm_analysis.is_valid_match === true).length
  const invalid = analyzedMatches.filter((m: any) => m.llm_analysis.is_valid_match === false).length

  const confidenceSum = analyzedMatches.reduce((sum: number, m: any) =>
    sum + (m.llm_analysis?.confidence_score || 0), 0
  )
  const avgConfidence = analyzedMatches.length > 0 ? confidenceSum / analyzedMatches.length : 0

  return {
    validMatches: valid,
    invalidMatches: invalid,
    avgConfidence: avgConfidence
  }
})

// 合并所有匹配结果到一个数组
const allResults = computed(() => {
  const results = matchResults.value?.results
  if (!results) return []

  const flatResults = [
    ...(results.matched || []).map((item: any) => ({ ...item, match_status: 'matched' })),
    ...(results.partial_matched || []).map((item: any) => ({ ...item, match_status: 'partial_matched' })),
    ...(results.unmatched || []).map((item: any) => ({ ...item, match_status: 'unmatched' }))
  ]

  // 按需求规格分组
  const grouped = new Map<string, any[]>()

  flatResults.forEach((item: any) => {
    const key = item.requirement_item_id || item.requirement_item_text
    if (!grouped.has(key)) {
      grouped.set(key, [])
    }
    grouped.get(key)!.push(item)
  })

  // 为每组创建一条记录，包含所有匹配的功能
  return Array.from(grouped.entries()).map(([, items]) => {
    // 按相似度排序
    const sortedItems = items.sort((a, b) => (b.similarity_score || 0) - (a.similarity_score || 0))

    // 取相似度最高的作为该组的满足度状态
    const bestMatch = sortedItems[0]

    return {
      requirement_item_id: bestMatch.requirement_item_id,
      requirement_item_text: bestMatch.requirement_item_text,
      match_status: bestMatch.match_status,
      similarity_score: bestMatch.similarity_score,
      rank: bestMatch.rank,
      final_confidence: bestMatch.final_confidence,
      is_llm_corrected: bestMatch.is_llm_corrected,
      // 保存所有匹配的功能用于展示
      matches: sortedItems
    }
  })
})

// 根据筛选条件过滤结果
const filteredResults = computed(() => {
  let results = allResults.value

  if (filterStatus.value) {
    results = results.filter((item: any) => item.match_status === filterStatus.value)
  }

  if (showLLMOnly.value && hasLLMAnalysis.value) {
    results = results.filter((item: any) =>
      item.matches?.some((m: any) => m.llm_analysis)
    )
  }

  return results
})

// 获取满足度类型
const getSatisfactionType = (status: string) => {
  const typeMap: Record<string, any> = {
    matched: 'success',
    partial_matched: 'warning',
    unmatched: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取满足度文本
const getSatisfactionText = (status: string) => {
  const textMap: Record<string, string> = {
    matched: '完全满足',
    partial_matched: '部分满足',
    unmatched: '不满足'
  }
  return textMap[status] || status
}

// 获取置信度颜色
const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

// 高亮关键词
const highlightKeywords = (text: string, keywords?: string[]) => {
  if (!text || !keywords || !keywords.length) {
    return text
  }

  let highlightedText = text
  keywords.forEach((keyword) => {
    const regex = new RegExp(`(${keyword})`, 'gi')
    highlightedText = highlightedText.replace(
      regex,
      '<mark style="background: #fff3cd; padding: 2px 4px; border-radius: 3px; font-weight: 600;">$1</mark>'
    )
  })

  return highlightedText
}

// 打开对比分析对话框
const openComparisonDialog = (requirementText: string, match: any) => {
  selectedRequirementText.value = requirementText
  selectedMatch.value = match
  comparisonDialogVisible.value = true
}

// 筛选条件变化处理
const handleFilterChange = () => {
  // 筛选逻辑已在 computed 中处理
}

onMounted(async () => {
  await loadResults()
})

async function loadResults() {
  loading.value = true
  try {
    await matchingStore.fetchMatchResults(requirementId.value)
  } catch (error) {
    ElMessage.error('加载匹配结果失败')
  } finally {
    loading.value = false
  }
}

function handleExport() {
  try {
    // 获取需求标题
    const requirementTitle = matchResults.value?.requirement?.title || '需求匹配报告'

    // 1. 创建汇总表
    const summaryData = [
      ['需求匹配分析报告'],
      ['需求名称', requirementTitle],
      [''],
      ['统计项', '数值'],
      ['总需求数', statistics.value.total_items],
      ['完全满足', statistics.value.matched],
      ['部分满足', statistics.value.partial_matched],
      ['不满足', statistics.value.unmatched],
      ['平均相似度', (statistics.value.avg_similarity * 100).toFixed(2) + '%'],
      ['最高相似度', (statistics.value.max_similarity * 100).toFixed(2) + '%'],
      ['最低相似度', (statistics.value.min_similarity * 100).toFixed(2) + '%']
    ]

    // 2. 创建详情表
    const detailData = [
      ['序号', '需求规格', '需求规格满足度', '相似度', '排名', '匹配功能', '功能描述', '产品']
    ]

    allResults.value.forEach((item: any, index: number) => {
      detailData.push([
        index + 1,
        item.requirement_item_text,
        getSatisfactionText(item.match_status),
        (item.similarity_score * 100).toFixed(1) + '%',
        item.rank,
        item.feature_name,
        item.feature_description,
        item.product_name || ''
      ])
    })

    // 3. 创建工作簿
    const wb = XLSX.utils.book_new()

    // 4. 添加汇总表
    const wsSummary = XLSX.utils.aoa_to_sheet(summaryData)
    wsSummary['!cols'] = [{ wch: 20 }, { wch: 30 }]
    XLSX.utils.book_append_sheet(wb, wsSummary, '汇总统计')

    // 5. 添加详情表
    const wsDetail = XLSX.utils.aoa_to_sheet(detailData)
    wsDetail['!cols'] = [
      { wch: 8 },
      { wch: 50 },
      { wch: 15 },
      { wch: 12 },
      { wch: 10 },
      { wch: 30 },
      { wch: 50 },
      { wch: 20 }
    ]
    XLSX.utils.book_append_sheet(wb, wsDetail, '详细结果')

    // 6. 导出文件
    const fileName = `${requirementTitle}_匹配报告_${new Date().getTime()}.xlsx`
    XLSX.writeFile(wb, fileName)

    ElMessage.success('导出成功！')
  } catch (error) {
    console.error('Export error:', error)
    ElMessage.error('导出失败，请检查是否已安装 xlsx 库')
  }
}
</script>

<style scoped lang="scss">
.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.mb-20 {
  margin-bottom: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.ml-10 {
  margin-left: 10px;
}

// LLM Summary Card
.llm-summary-card {
  border: 2px solid var(--el-color-success);
  background: linear-gradient(135deg, #f0f9ff 0%, #fff 100%);
}

.llm-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: white;
  border-radius: 8px;

  .label {
    font-size: 14px;
    color: #606266;
    font-weight: 500;
  }

  .value {
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
}

// Enhanced Match Items
.satisfaction-detail {
  .match-item-enhanced {
    padding: 16px;
    margin-bottom: 12px;
    border-radius: 8px;
    border: 1px solid #e4e7ed;
    background-color: #fafafa;
    transition: all 0.3s;

    &.is-best {
      border-color: #67c23a;
      background: linear-gradient(135deg, #f0f9ff 0%, #e8f5e9 100%);
    }

    &:hover {
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    }

    &:last-child {
      margin-bottom: 0;
    }
  }

  .detail-header {
    margin-bottom: 12px;
  }

  .detail-content {
    .feature-info,
    .feature-desc,
    .product-info {
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }

      .label {
        font-weight: 600;
        color: #606266;
        margin-right: 8px;
      }

      .value {
        color: #303133;
        line-height: 1.6;
      }
    }

    .feature-desc {
      .label {
        margin-left: 0;
      }
    }
  }
}

// LLM Analysis Section
.llm-analysis-section {
  margin-top: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;

  .llm-metrics {
    display: flex;
    gap: 24px;
    margin-bottom: 16px;
    flex-wrap: wrap;

    .metric-item {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .label {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .match-reason {
    margin-bottom: 16px;
    padding: 12px;
    background: #f4f4f5;
    border-radius: 6px;

    .reason-header {
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    .reason-text {
      margin: 0;
      color: #606266;
      line-height: 1.6;
    }
  }

  .keywords-section {
    margin-bottom: 12px;

    &:last-child {
      margin-bottom: 0;
    }

    .keywords-header {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    .keywords-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;

      .keyword-tag {
        margin: 0;
      }
    }
  }

  .token-usage {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed #e4e7ed;
  }
}

.no-match {
  padding: 12px;
  text-align: center;
  color: #909399;
}

// Keyword highlighting
:deep(mark) {
  background: #fff3cd;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
}

.requirement-text {
  line-height: 1.8;
}
</style>
