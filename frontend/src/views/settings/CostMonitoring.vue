<template>
  <div class="cost-monitoring-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <h2>LLM使用成本监控</h2>
          <el-button-group>
            <el-button :type="daysFilter === 7 ? 'primary' : ''" @click="changeDaysFilter(7)">
              最近7天
            </el-button>
            <el-button :type="daysFilter === 30 ? 'primary' : ''" @click="changeDaysFilter(30)">
              最近30天
            </el-button>
            <el-button :type="daysFilter === 90 ? 'primary' : ''" @click="changeDaysFilter(90)">
              最近90天
            </el-button>
          </el-button-group>
        </div>
      </template>
    </el-card>

    <!-- Summary Statistics -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #ecf5ff">
              <el-icon size="24" color="#409eff"><Money /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总成本</div>
              <div class="stat-value">${{ summary.total_cost?.toFixed(4) || '0.0000' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f0f9ff">
              <el-icon size="24" color="#67c23a"><DocumentCopy /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总请求数</div>
              <div class="stat-value">{{ summary.total_requests || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fef0f0">
              <el-icon size="24" color="#f56c6c"><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">平均响应时间</div>
              <div class="stat-value">{{ summary.avg_response_time_ms || 0 }}ms</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f4f4f5">
              <el-icon size="24" color="#909399"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">成功率</div>
              <div class="stat-value">{{ summary.success_rate?.toFixed(1) || 0 }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts -->
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <h3>每日成本趋势</h3>
          </template>
          <div ref="chartRef" style="height: 300px"></div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <h3>缓存命中率</h3>
          </template>
          <div class="cache-stats">
            <div class="cache-item">
              <span class="cache-label">缓存命中</span>
              <span class="cache-value">{{ summary.cache_hit_count || 0 }}</span>
            </div>
            <div class="cache-item">
              <span class="cache-label">缓存未命中</span>
              <span class="cache-value">{{ summary.cache_miss_count || 0 }}</span>
            </div>
            <div class="cache-rate">
              <span class="cache-label">命中率</span>
              <span class="cache-rate-value">{{ summary.cache_hit_rate?.toFixed(1) || 0 }}%</span>
            </div>
            <el-progress
              :percentage="summary.cache_hit_rate || 0"
              :color="cacheHitRateColor"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Model Statistics -->
    <el-card class="table-card">
      <template #header>
        <h3>模型使用统计 (Top 10)</h3>
      </template>
      <el-table :data="summary.model_stats || []" stripe>
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag :type="getProviderTagType(row.provider)" size="small">
              {{ row.provider }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="model" label="模型" />

        <el-table-column prop="total_requests" label="请求数" width="100" align="right" />

        <el-table-column prop="total_tokens" label="总Token数" width="120" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.total_tokens) }}
          </template>
        </el-table-column>

        <el-table-column prop="total_cost" label="总成本($)" width="120" align="right">
          <template #default="{ row }">
            {{ row.total_cost?.toFixed(6) }}
          </template>
        </el-table-column>

        <el-table-column prop="avg_cost" label="平均成本($)" width="120" align="right">
          <template #default="{ row }">
            {{ row.avg_cost?.toFixed(6) }}
          </template>
        </el-table-column>

        <el-table-column prop="avg_tokens" label="平均Token" width="120" align="right" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Money, DocumentCopy, Timer, SuccessFilled } from '@element-plus/icons-vue'
import { llmUsageApi, type UsageSummary } from '@/api/llm'
import * as echarts from 'echarts'

// Data
const daysFilter = ref(7)
const summary = reactive<UsageSummary>({
  total_requests: 0,
  total_tokens: 0,
  total_cost: 0,
  cache_hit_count: 0,
  cache_miss_count: 0,
  cache_hit_rate: 0,
  success_rate: 0,
  avg_response_time_ms: 0,
  most_used_provider: '',
  most_used_model: '',
  daily_costs: [],
  model_stats: []
})

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// Computed
const cacheHitRateColor = computed(() => {
  const rate = summary.cache_hit_rate || 0
  if (rate >= 50) return '#67c23a'
  if (rate >= 30) return '#e6a23c'
  return '#f56c6c'
})

// Methods
const loadSummary = async () => {
  try {
    const data = await llmUsageApi.getSummary(daysFilter.value)
    Object.assign(summary, data)
    await nextTick()
    renderChart()
  } catch (error: any) {
    ElMessage.error('加载成本数据失败')
  }
}

const changeDaysFilter = (days: number) => {
  daysFilter.value = days
  loadSummary()
}

const renderChart = () => {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const dates = summary.daily_costs.map((item: DailyCost) => item.date)
  const costs = summary.daily_costs.map((item: DailyCost) => item.total_cost)
  const requests = summary.daily_costs.map((item: DailyCost) => item.total_requests)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['成本($)', '请求数']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: [
      {
        type: 'value',
        name: '成本($)',
        position: 'left'
      },
      {
        type: 'value',
        name: '请求数',
        position: 'right'
      }
    ],
    series: [
      {
        name: '成本($)',
        type: 'bar',
        data: costs,
        itemStyle: {
          color: '#409eff'
        }
      },
      {
        name: '请求数',
        type: 'line',
        yAxisIndex: 1,
        data: requests,
        itemStyle: {
          color: '#67c23a'
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const getProviderTagType = (provider: string) => {
  const types: Record<string, any> = {
    openai: 'success',
    zhipuai: 'warning',
    qwen: 'info',
    siliconflow: ''
  }
  return types[provider] || ''
}

// Lifecycle
onMounted(() => {
  loadSummary()

  // Handle window resize
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})
</script>

<style scoped>
.cost-monitoring-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.cache-stats {
  padding: 20px 0;
}

.cache-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.cache-label {
  font-size: 14px;
  color: #606266;
}

.cache-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.cache-rate {
  display: flex;
  justify-content: space-between;
  margin: 20px 0 12px;
}

.cache-rate-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.table-card {
  margin-top: 20px;
}

.table-card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
</style>
