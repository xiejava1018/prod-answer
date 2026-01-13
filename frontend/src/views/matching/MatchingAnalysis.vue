<template>
  <div class="matching-analysis">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        匹配分析
      </template>
    </el-page-header>

    <el-row :gutter="20">
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
              <el-statistic title="总需求数" :value="analysisResult.summary.total_items" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="总匹配数" :value="analysisResult.summary.total_matches" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="完全匹配" :value="analysisResult.summary.matched">
                <template #suffix>
                  <span style="color: var(--el-color-success)">✔</span>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="6">
              <el-statistic title="部分匹配" :value="analysisResult.summary.partial_matched">
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
  RefreshRight
} from '@element-plus/icons-vue'
import type { MatchAnalyzeResponse } from '@/types'

const router = useRouter()
const matchingStore = useMatchingStore()

const loading = ref(false)
const analyzing = ref(false)

const requirements = ref<any[]>([])
const selectedRequirementId = ref<string>('')

const threshold = ref(0.65)  // 降低默认阈值以提高匹配率
const limit = ref(5)

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

async function handleAnalyze() {
  if (!selectedRequirementId.value) {
    ElMessage.warning('请先选择需求')
    return
  }

  analyzing.value = true
  try {
    const result = await matchingStore.analyzeMatch(
      selectedRequirementId.value,
      threshold.value
    )

    analysisResult.value = result
    ElMessage.success('匹配分析完成')
  } catch (error) {
    ElMessage.error('匹配分析失败')
  } finally {
    analyzing.value = false
  }
}

function handleViewResults() {
  if (selectedRequirementId.value) {
    router.push(`/matching/results/${selectedRequirementId.value}`)
  }
}
</script>

<style scoped lang="scss">
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.ml-10 {
  margin-left: 10px;
}

.mb-20 {
  margin-bottom: 20px;
}
</style>
