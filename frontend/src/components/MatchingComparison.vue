<template>
  <div class="matching-comparison">
    <!-- Header -->
    <div class="comparison-header">
      <h3>
        <el-icon><DocumentCopy /></el-icon>
        匹配对比分析
      </h3>
      <div class="header-info">
        <el-tag v-if="matchData.llm_analysis" :type="getMatchValidityType(matchData.llm_analysis.is_valid_match)">
          {{ getMatchValidityLabel(matchData.llm_analysis.is_valid_match) }}
        </el-tag>
        <el-tag type="info">相似度: {{ (matchData.similarity_score * 100).toFixed(1) }}%</el-tag>
        <el-tag v-if="matchData.final_confidence !== undefined" type="warning">
          最终置信度: {{ (matchData.final_confidence * 100).toFixed(1) }}%
        </el-tag>
      </div>
    </div>

    <!-- Comparison Panels -->
    <div class="comparison-panels" @scroll="handleScroll">
      <!-- Left Panel: Requirement -->
      <div class="panel requirement-panel" ref="requirementPanel">
        <div class="panel-header">
          <el-icon><ChatDotSquare /></el-icon>
          <span>需求描述</span>
        </div>
        <div class="panel-content">
          <div
            class="text-content"
            v-html="highlightedRequirement"
            @click="handleTextClick('requirement', $event)"
          ></div>
        </div>
        <div v-if="matchData.llm_analysis?.keywords_from_requirement" class="keywords-panel">
          <div class="keywords-title">
            <el-icon><PriceTag /></el-icon>
            <span>提取关键词</span>
          </div>
          <div class="keywords-list">
            <el-tag
              v-for="keyword in matchData.llm_analysis.keywords_from_requirement"
              :key="keyword"
              :type="isKeywordSelected(keyword) ? 'primary' : ''"
              :class="{ 'keyword-selected': isKeywordSelected(keyword) }"
              size="small"
              @click="selectKeyword(keyword)"
            >
              {{ keyword }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- Divider -->
      <div class="panel-divider">
        <el-icon><Right /></el-icon>
      </div>

      <!-- Right Panel: Feature -->
      <div class="panel feature-panel" ref="featurePanel">
        <div class="panel-header">
          <el-icon><Box /></el-icon>
          <span>功能特性</span>
        </div>
        <div class="panel-content">
          <div
            class="text-content"
            v-html="highlightedFeature"
            @click="handleTextClick('feature', $event)"
          ></div>
        </div>
        <div v-if="matchData.llm_analysis?.keywords_from_feature" class="keywords-panel">
          <div class="keywords-title">
            <el-icon><PriceTag /></el-icon>
            <span>匹配关键词</span>
          </div>
          <div class="keywords-list">
            <el-tag
              v-for="keyword in matchData.llm_analysis.keywords_from_feature"
              :key="keyword"
              :type="isKeywordSelected(keyword) ? 'success' : ''"
              :class="{ 'keyword-selected': isKeywordSelected(keyword) }"
              size="small"
              @click="selectKeyword(keyword)"
            >
              {{ keyword }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Analysis Section -->
    <div v-if="matchData.llm_analysis" class="ai-analysis-section">
      <el-divider content-position="left">
        <el-icon><MagicStick /></el-icon>
        AI 智能分析
      </el-divider>

      <div class="analysis-grid">
        <!-- Confidence Score -->
        <div class="analysis-item">
          <div class="item-label">
            <el-icon><TrendCharts /></el-icon>
            <span>AI 置信度</span>
          </div>
          <div class="item-value">
            <el-progress
              :percentage="matchData.llm_analysis.confidence_score * 100"
              :color="getConfidenceColor(matchData.llm_analysis.confidence_score)"
              :stroke-width="12"
              :show-text="true"
            />
          </div>
        </div>

        <!-- Match Reason -->
        <div v-if="matchData.llm_analysis.match_reason" class="analysis-item full-width">
          <div class="item-label">
            <el-icon><ChatLineSquare /></el-icon>
            <span>匹配原因</span>
          </div>
          <div class="item-content">
            <p>{{ matchData.llm_analysis.match_reason }}</p>
          </div>
        </div>

        <!-- Token Usage -->
        <div v-if="matchData.llm_analysis.total_tokens" class="analysis-item">
          <div class="item-label">
            <el-icon><Coin /></el-icon>
            <span>Token 使用量</span>
          </div>
          <div class="item-value">
            <span class="token-count">{{ matchData.llm_analysis.total_tokens }}</span>
          </div>
        </div>

        <!-- LLM Model Info -->
        <div v-if="matchData.llm_analysis.llm_provider" class="analysis-item">
          <div class="item-label">
            <el-icon><Cpu /></el-icon>
            <span>使用模型</span>
          </div>
          <div class="item-value">
            <el-tag size="small" type="info">
              {{ matchData.llm_analysis.llm_provider }} / {{ matchData.llm_analysis.llm_model }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import {
  DocumentCopy,
  ChatDotSquare,
  Box,
  PriceTag,
  Right,
  MagicStick,
  TrendCharts,
  ChatLineSquare,
  Coin,
  Cpu
} from '@element-plus/icons-vue'

// Props
interface Props {
  requirementText: string
  featureDescription: string
  matchData: any
}

const props = defineProps<Props>()

// State
const requirementPanel = ref<HTMLElement>()
const featurePanel = ref<HTMLElement>()
const selectedKeywords = ref<Set<string>>(new Set())

// Computed
const highlightedRequirement = computed(() => {
  return highlightText(
    props.requirementText,
    props.matchData.llm_analysis?.keywords_from_requirement || [],
    selectedKeywords.value
  )
})

const highlightedFeature = computed(() => {
  return highlightText(
    props.featureDescription,
    props.matchData.llm_analysis?.keywords_from_feature || [],
    selectedKeywords.value
  )
})

// Methods
const highlightText = (text: string, keywords: string[], selectedKeywords: Set<string>) => {
  if (!text || !keywords.length) return text

  let highlighted = text

  // Sort keywords by length (longest first) to avoid overlapping replacements
  const sortedKeywords = [...keywords].sort((a, b) => b.length - a.length)

  sortedKeywords.forEach((keyword) => {
    const regex = new RegExp(`(${escapeRegex(keyword)})`, 'gi')
    const isSelected = selectedKeywords.has(keyword.toLowerCase())

    highlighted = highlighted.replace(regex, (match) => {
      const style = isSelected
        ? 'background: #409eff; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;'
        : 'background: #fff3cd; padding: 2px 4px;'
      return `<mark style="${style}" data-keyword="${keyword.toLowerCase()}">${match}</mark>`
    })
  })

  return highlighted
}

const escapeRegex = (str: string) => {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const handleScroll = (event: UIEvent) => {
  const target = event.target as HTMLElement
  const scrollRatio = target.scrollTop / (target.scrollHeight - target.clientHeight)

  // Sync scroll position to other panel
  if (target === requirementPanel.value && featurePanel.value) {
    const maxScroll = featurePanel.value.scrollHeight - featurePanel.value.clientHeight
    featurePanel.value.scrollTop = scrollRatio * maxScroll
  } else if (target === featurePanel.value && requirementPanel.value) {
    const maxScroll = requirementPanel.value.scrollHeight - requirementPanel.value.clientHeight
    requirementPanel.value.scrollTop = scrollRatio * maxScroll
  }
}

const handleTextClick = (panel: 'requirement' | 'feature', event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (target.tagName === 'MARK') {
    const keyword = target.getAttribute('data-keyword')
    if (keyword) {
      selectKeyword(keyword)
    }
  }
}

const selectKeyword = (keyword: string) => {
  const keywordLower = keyword.toLowerCase()

  if (selectedKeywords.value.has(keywordLower)) {
    selectedKeywords.value.delete(keywordLower)
  } else {
    selectedKeywords.value.add(keywordLower)
  }

  // Force re-render
  nextTick(() => {
    // Highlight all occurrences of this keyword in both panels
    highlightAllOccurrences(keywordLower)
  })
}

const highlightAllOccurrences = (keyword: string) => {
  const markElements = document.querySelectorAll(`mark[data-keyword="${keyword}"]`)
  markElements.forEach((el) => {
    if (selectedKeywords.value.has(keyword)) {
      el.setAttribute('style', 'background: #409eff; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;')
    } else {
      el.setAttribute('style', 'background: #fff3cd; padding: 2px 4px;')
    }
  })
}

const isKeywordSelected = (keyword: string) => {
  return selectedKeywords.value.has(keyword.toLowerCase())
}

const getMatchValidityLabel = (isValid: boolean | null) => {
  if (isValid === true) return '有效匹配'
  if (isValid === false) return '无效匹配'
  return '待确定'
}

const getMatchValidityType = (isValid: boolean | null) => {
  if (isValid === true) return 'success'
  if (isValid === false) return 'danger'
  return 'warning'
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.matching-comparison {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.comparison-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
}

.header-info {
  display: flex;
  gap: 8px;
}

.comparison-panels {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  min-height: 400px;
}

.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.panel-header {
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.panel-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: white;
}

.text-content {
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
}

.text-content :deep(mark) {
  cursor: pointer;
  transition: all 0.2s;
}

.text-content :deep(mark:hover) {
  filter: brightness(0.95);
}

.keywords-panel {
  padding: 12px 16px;
  background: #f5f7fa;
  border-top: 1px solid #dcdfe6;
}

.keywords-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.keywords-list .el-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.keywords-list .el-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.keyword-selected {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.panel-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 20px;
}

.ai-analysis-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.analysis-item {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.analysis-item.full-width {
  grid-column: 1 / -1;
}

.item-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 600;
}

.item-value {
  display: flex;
  align-items: center;
  gap: 12px;
}

.token-count {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.item-content {
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.item-content p {
  margin: 0;
  line-height: 1.6;
  color: #303133;
  font-size: 14px;
}

/* Scrollbar styling */
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
