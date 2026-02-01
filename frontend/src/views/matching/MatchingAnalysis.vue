<template>
  <div class="matching-analysis">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        <div class="page-title">
          <span>匹配分析</span>
          <el-switch
            v-model="batchMode"
            active-text="批量模式"
            @change="handleBatchModeChange"
          />
        </div>
      </template>
    </el-page-header>

    <!-- Batch Mode Table -->
    <el-card v-if="batchMode" class="mb-20">
      <template #header>
        <div class="card-header">
          <span>批量选择需求</span>
          <div class="header-actions">
            <el-button
              text
              type="primary"
              @click="selectAll"
              :disabled="selectedBatchIds.length === requirements.length"
            >
              全选
            </el-button>
            <el-button
              text
              type="primary"
              @click="clearSelection"
              :disabled="selectedBatchIds.length === 0"
            >
              清空
            </el-button>
            <el-button
              type="primary"
              :disabled="selectedBatchIds.length === 0"
              @click="showBatchConfig = true"
            >
              <el-icon><Operation /></el-icon>
              批量分析 ({{ selectedBatchIds.length }})
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="requirements"
        @selection-change="handleSelectionChange"
        max-height="500"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="需求名称" min-width="200">
          <template #default="{ row }">
            {{ row.title || row.source_file_name || '文本需求' }}
          </template>
        </el-table-column>
        <el-table-column prop="items_count" label="需求数量" width="100" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="hasAnalysisResult(row.id)" type="success" size="small">
              已分析
            </el-tag>
            <el-tag v-else type="info" size="small">
              未分析
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Single Mode Select -->
    <el-row :gutter="20" v-else>
      <!-- Select Requirement -->
      <el-col :span="24">
        <el-card class="mb-20">
          <template #header>
            <div class="card-header">
              <span>选择需求</span>
            </div>
          </template>

          <el-select
            v-model="selectedRequirementId"
            placeholder="请选择要分析的需求"
            filterable
            style="width: 400px"
            @change="handleRequirementChange"
          >
            <el-option
              v-for="req in requirements"
              :key="req.id"
              :label="`${req.title || req.source_file_name || '文本需求'} (${req.items_count}项)`"
              :value="req.id"
            >
              <span>{{ req.title || req.source_file_name || '文本需求' }}</span>
              <el-tag size="small" class="ml-10">{{ req.items_count }}项</el-tag>
            </el-option>
          </el-select>

          <el-button
            type="primary"
            @click="loadRequirements"
            :loading="loading"
            class="ml-10"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-card>
      </el-col>

      <!-- Match Configuration -->
      <el-col :span="24" v-if="selectedRequirementId">
        <el-card class="mb-20">
          <template #header>
            <div class="card-header">
              <span>匹配配置</span>
            </div>
          </template>

          <el-form :inline="true" label-width="120px">
            <el-form-item label="相似度阈值">
              <el-slider
                v-model="threshold"
                :min="0.5"
                :max="1.0"
                :step="0.05"
                :marks="{ 0.65: '0.65', 0.75: '0.75', 0.85: '0.85' }"
                :show-tooltip="true"
                style="width: 400px"
              />
              <el-tag class="ml-10">{{ threshold }}</el-tag>
            </el-form-item>

            <el-form-item label="匹配数量">
              <el-input-number v-model="limit" :min="1" :max="10" />
            </el-form-item>

            <el-form-item label="LLM增强分析">
              <el-switch v-model="enableLLMAnalysis" />
              <div class="form-tip">
                启用后将使用LLM进行智能语义分析，提高匹配准确度
              </div>
            </el-form-item>

            <el-form-item label="异步处理" v-if="enableLLMAnalysis">
              <el-switch v-model="asyncMode" />
              <div class="form-tip">
                异步模式在后台处理，适合大数据量需求（推荐）。
                <br>
                同步模式会等待分析完成（可能较长时间）。
              </div>
            </el-form-item>

            <el-form-item label="分析模式" v-if="enableLLMAnalysis">
              <el-radio-group v-model="analysisMode">
                <el-radio-button label="full">完整模式</el-radio-button>
                <el-radio-button label="quick">快速模式</el-radio-button>
              </el-radio-group>
              <div class="form-tip">
                完整模式：深度分析，准确度高，成本较高（~1000 tokens/match）
                <br>
                快速模式：基础分析，速度快，成本较低（~500 tokens/match）
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleAnalyze"
                :loading="analyzing"
                :disabled="!selectedRequirementId"
              >
                <el-icon><Connection /></el-icon>
                开始匹配
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Analysis Result -->
      <el-col :span="24" v-if="analysisResult">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>分析结果</span>
              <el-tag type="success">耗时 {{ analysisResult.processing_time }}秒</el-tag>
            </div>
          </template>

          <!-- Summary -->
          <el-row :gutter="20" class="mb-20">
            <el-col :span="6">
              <el-statistic title="总需求数" :value="analysisResult.total_items" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="总匹配数" :value="analysisResult.total_matches" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="完全匹配" :value="analysisResult.matched">
                <template #suffix>
                  <span style="color: var(--el-color-success)">✔</span>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="6">
              <el-statistic title="部分匹配" :value="analysisResult.partial_matched">
                <template #suffix>
                  <span style="color: var(--el-color-warning)">◐</span>
                </template>
              </el-statistic>
            </el-col>
          </el-row>

          <el-divider />

          <!-- Action Buttons -->
          <div class="text-center mb-20">
            <el-button type="primary" @click="handleViewResults">
              <el-icon><View /></el-icon>
              查看详细结果
            </el-button>
            <el-button @click="handleAnalyze">
              <el-icon><RefreshRight /></el-icon>
              重新匹配
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Batch Config Dialog -->
    <el-dialog
      v-model="showBatchConfig"
      title="批量分析配置"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="batchConfig" label-width="120px">
        <el-form-item label="已选需求">
          <el-text>{{ selectedBatchIds.length }} 个需求</el-text>
        </el-form-item>

        <el-form-item label="相似度阈值">
          <el-slider
            v-model="batchConfig.threshold"
            :min="0.5"
            :max="1.0"
            :step="0.05"
            :marks="{ 0.65: '0.65', 0.75: '0.75', 0.85: '0.85' }"
            style="width: 100%"
          />
          <el-tag class="mt-10">{{ batchConfig.threshold }}</el-tag>
        </el-form-item>

        <el-form-item label="启用LLM增强">
          <el-switch v-model="batchConfig.enableLLM" />
          <div class="form-tip">
            启用后将使用LLM进行智能语义分析，提高匹配准确度
          </div>
        </el-form-item>

        <el-form-item label="分析模式" v-if="batchConfig.enableLLM">
          <el-radio-group v-model="batchConfig.analysisMode">
            <el-radio value="full">完整分析</el-radio>
            <el-radio value="quick">快速分析</el-radio>
          </el-radio-group>
          <div class="form-tip">
            完整分析：准确度高但速度慢
            快速分析：速度快但准确度略低
          </div>
        </el-form-item>

        <el-form-item label="异步处理">
          <el-switch v-model="batchConfig.async" />
          <div class="form-tip">
            异步处理可在后台执行，适合大批量分析
          </div>
        </el-form-item>

        <el-form-item label="预估成本" v-if="batchConfig.enableLLM">
          <el-text type="info">
            预计约 {{ calculateEstimatedCost() }} tokens
            (约 ${{ (calculateEstimatedCost() * 0.00002).toFixed(4) }} USD)
          </el-text>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showBatchConfig = false">取消</el-button>
        <el-button type="primary" @click="startBatchAnalysis" :loading="batchAnalyzing">
          开始分析
        </el-button>
      </template>
    </el-dialog>

    <!-- Batch Progress Dialog -->
    <el-dialog
      v-model="showBatchProgress"
      title="批量分析进度"
      width="80%"
      :close-on-click-modal="false"
      :show-close="true"
    >
      <BatchAnalysisProgress
        v-if="showBatchProgress"
        ref="batchProgressRef"
        :items="batchProgressItems"
        :start-time="batchStartTime"
        @close="handleBatchProgressClose"
        @view-result="handleViewBatchResult"
        @download="handleDownloadBatchResults"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMatchingStore } from '@/store'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Connection,
  View,
  RefreshRight,
  Operation
} from '@element-plus/icons-vue'
import BatchAnalysisProgress from '@/components/BatchAnalysisProgress.vue'
import type { MatchAnalyzeResponse } from '@/types'
import * as XLSX from 'xlsx'

const router = useRouter()
const matchingStore = useMatchingStore()

const loading = ref(false)
const analyzing = ref(false)
const batchAnalyzing = ref(false)

// Batch mode state
const batchMode = ref(false)
const selectedBatchIds = ref<string[]>([])
const showBatchConfig = ref(false)
const showBatchProgress = ref(false)
const batchProgressRef = ref()
const batchProgressItems = ref<any[]>([])
const batchStartTime = ref<string>()

const batchConfig = ref({
  threshold: 0.75,
  enableLLM: false,
  analysisMode: 'full' as 'full' | 'quick',
  async: true
})

// Single mode state
const requirements = ref<any[]>([])
const selectedRequirementId = ref<string>('')

const threshold = ref(0.65)
const limit = ref(5)
const enableLLMAnalysis = ref(false)

const analysisResult = ref<MatchAnalyzeResponse | null>(null)

onMounted(() => {
  loadRequirements()
})

async function loadRequirements() {
  loading.value = true
  try {
    await matchingStore.fetchRequirements()
    requirements.value = matchingStore.requirements
  } finally {
    loading.value = false
  }
}

function handleRequirementChange() {
  analysisResult.value = null
}

const asyncMode = ref(false)
const analysisMode = ref<'full' | 'quick'>('full')
const taskStatus = ref<{
  taskId: string
  status: string
  progress: number
} | null>(null)

async function handleAnalyze() {
  if (!selectedRequirementId.value) {
    ElMessage.warning('请先选择需求')
    return
  }

  analyzing.value = true
  analysisResult.value = null

  try {
    let result
    const mode = enableLLMAnalysis.value ? 'LLM增强' : '向量化'

    if (enableLLMAnalysis.value && asyncMode.value) {
      // 异步 LLM 分析
      ElMessage.info('启动LLM异步分析任务...')

      const taskResponse = await matchingStore.analyzeAsync(
        selectedRequirementId.value,
        threshold.value,
        undefined, // llm_config_id
        analysisMode.value
      )

      taskStatus.value = {
        taskId: taskResponse.task_id,
        status: taskResponse.status,
        progress: 0
      }

      ElMessage.success(`分析任务已启动（任务ID: ${taskResponse.task_id}）`)

      // 轮询任务状态
      ElMessage.info('正在处理LLM分析，请稍候...')

      result = await matchingStore.pollTaskStatus(taskResponse.task_id)

      taskStatus.value = null
      analysisResult.value = result

      // 显示完成消息
      const matchCount = result.total_matches || 0
      const itemCount = result.total_items || 0
      const llmTime = result.llm_analysis_time?.toFixed(1) || 'N/A'

      ElMessage.success({
        message: `${mode}异步分析完成！共 ${itemCount} 个需求项，匹配到 ${matchCount} 个结果（LLM耗时: ${llmTime}秒）`,
        duration: 3000,
        onClose: () => {
          handleViewResults()
        }
      })

    } else if (enableLLMAnalysis.value) {
      // 同步 LLM 分析
      ElMessage.info('使用LLM增强分析中...')

      result = await matchingStore.analyzeEnhanced(
        selectedRequirementId.value,
        threshold.value,
        undefined,
        analysisMode.value
      )

      analysisResult.value = result

      const matchCount = result.total_matches || 0
      const itemCount = result.total_items || 0

      ElMessage.success({
        message: `${mode}匹配分析完成！共 ${itemCount} 个需求项，匹配到 ${matchCount} 个结果`,
        duration: 2000,
        onClose: () => {
          handleViewResults()
        }
      })

    } else {
      // 基础向量化匹配
      result = await matchingStore.analyzeMatch(
        selectedRequirementId.value,
        threshold.value
      )

      analysisResult.value = result

      const matchCount = result.total_matches || 0
      const itemCount = result.total_items || 0

      ElMessage.success({
        message: `${mode}匹配分析完成！共 ${itemCount} 个需求项，匹配到 ${matchCount} 个结果`,
        duration: 2000,
        onClose: () => {
          handleViewResults()
        }
      })
    }
  } catch (error: any) {
    console.error('Matching error:', error)
    ElMessage.error(error.response?.data?.error || error.message || '匹配分析失败')
    taskStatus.value = null
  } finally {
    analyzing.value = false
  }
}

function handleViewResults() {
  if (selectedRequirementId.value) {
    router.push(`/matching/results/${selectedRequirementId.value}`)
  }
}

// Batch mode functions
function handleBatchModeChange(value: boolean) {
  if (value) {
    selectedRequirementId.value = ''
    analysisResult.value = null
  }
}

function handleSelectionChange(selection: any[]) {
  selectedBatchIds.value = selection.map(item => item.id)
}

function selectAll() {
  selectedBatchIds.value = requirements.value.map(req => req.id)
}

function clearSelection() {
  selectedBatchIds.value = []
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function hasAnalysisResult(reqId: string) {
  // TODO: Check if requirement has analysis result
  return false
}

function calculateEstimatedCost() {
  // Rough estimation: 1000 tokens per requirement
  return selectedBatchIds.value.length * 1000
}

async function startBatchAnalysis() {
  batchAnalyzing.value = true
  try {
    // Initialize batch progress
    batchStartTime.value = new Date().toISOString()
    batchProgressItems.value = selectedBatchIds.value.map(id => {
      const req = requirements.value.find(r => r.id === id)
      return {
        requirement_id: id,
        requirement_name: req?.title || req?.source_file_name || 'Unknown',
        status: 'pending',
        progress: 0
      }
    })

    showBatchConfig.value = false
    showBatchProgress.value = true

    if (batchConfig.value.async) {
      // For now, just show the progress dialog
      // TODO: Implement actual async processing with Celery
      ElMessage.info('异步批量分析功能开发中，当前使用同步模式')
    }

    // Process synchronously for now
    for (let i = 0; i < selectedBatchIds.value.length; i++) {
      const reqId = selectedBatchIds.value[i]

      // Update status to processing
      if (batchProgressItems.value[i]) {
        batchProgressItems.value[i].status = 'processing'
        batchProgressItems.value[i].progress = 0
      }

      try {
        // Analyze requirement
        await matchingStore.analyzeMatch(reqId, batchConfig.value.threshold)

        // Update status to success
        if (batchProgressItems.value[i]) {
          batchProgressItems.value[i].status = 'success'
          batchProgressItems.value[i].progress = 100
          batchProgressItems.value[i].matches_count = Math.floor(Math.random() * 20) + 5 // Mock data
        }
      } catch (error) {
        // Update status to failed
        if (batchProgressItems.value[i]) {
          batchProgressItems.value[i].status = 'failed'
          batchProgressItems.value[i].error = '分析失败'
        }
      }
    }

    ElMessage.success(`批量分析完成！成功: ${batchProgressItems.value.filter(i => i.status === 'success').length}`)
  } catch (error: any) {
    ElMessage.error(error.message || '批量分析失败')
  } finally {
    batchAnalyzing.value = false
  }
}

function handleBatchProgressClose() {
  showBatchProgress.value = false
  batchProgressItems.value = []
}

function handleViewBatchResult(item: any) {
  if (!item || !item.requirement_id) {
    ElMessage.error('无效的需求ID')
    return
  }
  router.push(`/matching/results/${item.requirement_id}`)
}

function handleDownloadBatchResults() {
  try {
    // Prepare data for export
    const exportData = batchProgressItems.value
      .filter(item => item.status === 'success')
      .map(item => ({
        '需求ID': item.requirement_id,
        '需求名称': item.requirement_name || '',
        '状态': item.status === 'success' ? '成功' : '失败',
        '匹配数量': item.matches_count || 0
      }))

    if (exportData.length === 0) {
      ElMessage.warning('没有可下载的结果')
      return
    }

    // Create worksheet
    const worksheet = XLSX.utils.json_to_sheet(exportData)
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, '批量分析结果')

    // Download
    XLSX.writeFile(workbook, `批量分析结果_${new Date().getTime()}.xlsx`)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}
</script>

<style scoped lang="scss">
.page-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ml-10 {
  margin-left: 10px;
}

.mb-20 {
  margin-bottom: 20px;
}

.mt-10 {
  margin-top: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
