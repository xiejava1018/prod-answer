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

      <!-- Main Table with Filter -->
      <el-card>
        <template #header>
          <div class="card-header">
            <span>需求规格满足度分析</span>
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
          </div>
        </template>

        <el-table :data="filteredResults" border stripe>
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="requirement_item_text" label="需求规格" min-width="300" />
          <el-table-column label="需求规格满足度" width="150" align="center">
            <template #default="{ row }">
              <el-tag
                :type="getSatisfactionType(row.match_status)"
                size="large"
              >
                {{ getSatisfactionText(row.match_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="规格满足度详细描述" min-width="400">
            <template #default="{ row }">
              <div class="satisfaction-detail">
                <div class="detail-header">
                  <el-tag :type="getSatisfactionType(row.match_status)" size="small">
                    相似度: {{ (row.similarity_score * 100).toFixed(1) }}%
                  </el-tag>
                  <el-tag type="info" size="small" class="ml-10">
                    排名: {{ row.rank }}
                  </el-tag>
                </div>
                <div class="detail-content">
                  <div class="feature-info">
                    <span class="label">匹配功能:</span>
                    <span class="value">{{ row.feature_name }}</span>
                  </div>
                  <div class="feature-desc">
                    <span class="label">功能描述:</span>
                    <span class="value">{{ row.feature_description }}</span>
                  </div>
                  <div v-if="row.product_name" class="product-info">
                    <span class="label">产品:</span>
                    <span class="value">{{ row.product_name }}</span>
                  </div>
                </div>
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
import * as XLSX from 'xlsx'
import {
  Document,
  CircleCheck,
  Warning,
  CircleClose,
  TrendCharts,
  Top,
  Bottom,
  Download
} from '@element-plus/icons-vue'

const route = useRoute()
const matchingStore = useMatchingStore()

const loading = ref(true)
const filterStatus = ref('')

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

// 合并所有匹配结果到一个数组
const allResults = computed(() => {
  const results = matchResults.value?.results
  if (!results) return []

  return [
    ...(results.matched || []).map((item: any) => ({ ...item, match_status: 'matched' })),
    ...(results.partial_matched || []).map((item: any) => ({ ...item, match_status: 'partial_matched' })),
    ...(results.unmatched || []).map((item: any) => ({ ...item, match_status: 'unmatched' }))
  ]
})

// 根据筛选条件过滤结果
const filteredResults = computed(() => {
  if (!filterStatus.value) {
    return allResults.value
  }
  return allResults.value.filter((item: any) => item.match_status === filterStatus.value)
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
    // 设置列宽
    wsSummary['!cols'] = [{ wch: 20 }, { wch: 30 }]
    XLSX.utils.book_append_sheet(wb, wsSummary, '汇总统计')

    // 5. 添加详情表
    const wsDetail = XLSX.utils.aoa_to_sheet(detailData)
    // 设置列宽
    wsDetail['!cols'] = [
      { wch: 8 },   // 序号
      { wch: 50 },  // 需求规格
      { wch: 15 },  // 需求规格满足度
      { wch: 12 },  // 相似度
      { wch: 10 },  // 排名
      { wch: 30 },  // 匹配功能
      { wch: 50 },  // 功能描述
      { wch: 20 }   // 产品
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

.satisfaction-detail {
  .detail-header {
    margin-bottom: 8px;
  }

  .detail-content {
    .feature-info,
    .feature-desc,
    .product-info {
      margin-bottom: 6px;

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
      }
    }

    .feature-desc {
      .label {
        margin-left: 0;
      }
    }
  }
}
</style>
