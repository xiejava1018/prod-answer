<template>
  <div class="match-result-detail">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        匹配结果详情
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
            <el-statistic title="完全匹配" :value="statistics.matched">
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
            <el-statistic title="部分匹配" :value="statistics.partial_matched">
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
            <el-statistic title="不匹配" :value="statistics.unmatched">
              <template #prefix>
                <el-icon style="vertical-align: -0.125em; color: var(--el-color-danger)">
                  <CircleClose />
                </el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
      </el-row>

      <!-- Tabs -->
      <el-card>
        <el-tabs v-model="activeTab">
          <!-- Matched Items -->
          <el-tab-pane label="完全匹配" name="matched">
            <template #label>
              <span>
                <el-icon><SuccessFilled /></el-icon>
                完全匹配 ({{ statistics.matched }})
              </span>
            </template>
            <el-table :data="matchResults.results.matched" border>
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="requirement_item_text" label="需求内容" min-width="200" show-overflow-tooltip />
              <el-table-column label="匹配功能" min-width="300">
                <template #default="{ row }">
                  <div>
                    <div style="font-weight: 600; margin-bottom: 4px;">{{ row.feature_name }}</div>
                    <div style="color: #606266; font-size: 13px;">{{ row.feature_description }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="产品" width="150" show-overflow-tooltip />
              <el-table-column prop="similarity_score" label="相似度" width="120">
                <template #default="{ row }">
                  <el-tag type="success" size="large">
                    {{ (row.similarity_score * 100).toFixed(1) }}%
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="rank" label="排名" width="80" />
            </el-table>

            <el-empty
              v-if="matchResults.results.matched.length === 0"
              description="没有完全匹配的结果"
            />
          </el-tab-pane>

          <!-- Partial Matched Items -->
          <el-tab-pane label="部分匹配" name="partial_matched">
            <template #label>
              <span>
                <el-icon><WarningFilled /></el-icon>
                部分匹配 ({{ statistics.partial_matched }})
              </span>
            </template>
            <el-table :data="matchResults.results.partial_matched" border>
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="requirement_item_text" label="需求内容" min-width="200" show-overflow-tooltip />
              <el-table-column label="匹配功能" min-width="300">
                <template #default="{ row }">
                  <div>
                    <div style="font-weight: 600; margin-bottom: 4px;">{{ row.feature_name }}</div>
                    <div style="color: #606266; font-size: 13px;">{{ row.feature_description }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="产品" width="150" show-overflow-tooltip />
              <el-table-column prop="similarity_score" label="相似度" width="120">
                <template #default="{ row }">
                  <el-tag type="warning" size="large">
                    {{ (row.similarity_score * 100).toFixed(1) }}%
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="rank" label="排名" width="80" />
            </el-table>

            <el-empty
              v-if="matchResults.results.partial_matched.length === 0"
              description="没有部分匹配的结果"
            />
          </el-tab-pane>

          <!-- Unmatched Items -->
          <el-tab-pane label="不匹配" name="unmatched">
            <template #label>
              <span>
                <el-icon><CircleClose /></el-icon>
                不匹配 ({{ statistics.unmatched }})
              </span>
            </template>
            <el-table :data="matchResults.results.unmatched" border>
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="requirement_item_text" label="需求内容" min-width="200" show-overflow-tooltip />
              <el-table-column label="最佳匹配功能" min-width="300">
                <template #default="{ row }">
                  <div>
                    <div style="font-weight: 600; margin-bottom: 4px;">{{ row.feature_name }}</div>
                    <div style="color: #606266; font-size: 13px;">{{ row.feature_description }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="similarity_score" label="相似度" width="120">
                <template #default="{ row }">
                  <el-tag type="danger" size="large">
                    {{ (row.similarity_score * 100).toFixed(1) }}%
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="rank" label="排名" width="80" />
            </el-table>

            <el-empty
              v-if="matchResults.results.unmatched.length === 0"
              description="没有不匹配的结果"
            />
          </el-tab-pane>
        </el-tabs>
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
            <el-statistic title="平均相似度" :value="(statistics.avg_similarity * 100).toFixed(2) + '%'">
              <template #suffix>
                <el-icon style="vertical-align: -0.125em">
                  <TrendCharts />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="8">
            <el-statistic title="最高相似度" :value="(statistics.max_similarity * 100).toFixed(2) + '%'">
              <template #suffix>
                <el-icon style="vertical-align: -0.125em; color: var(--el-color-success)">
                  <Top />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="8">
            <el-statistic title="最低相似度" :value="(statistics.min_similarity * 100).toFixed(2) + '%'">
              <template #suffix>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMatchingStore } from '@/store'
import { ElMessage } from 'element-plus'
import {
  Document,
  CircleCheck,
  Warning,
  CircleClose,
  SuccessFilled,
  WarningFilled,
  TrendCharts,
  Top,
  Bottom,
  Download
} from '@element-plus/icons-vue'

const route = useRoute()
const matchingStore = useMatchingStore()

const loading = ref(true)
const activeTab = ref('matched')

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
  ElMessage.info('导出功能开发中...')
  // TODO: Implement export functionality
}
</script>

<style scoped lang="scss">
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
</style>
