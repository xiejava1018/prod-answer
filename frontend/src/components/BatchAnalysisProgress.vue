<template>
  <div class="batch-analysis-progress">
    <!-- Header -->
    <div class="progress-header">
      <div class="header-title">
        <el-icon size="20"><Loading /></el-icon>
        <h3>批量分析进度</h3>
      </div>
      <div class="header-actions">
        <el-button
          v-if="canPause"
          :loading="actionLoading"
          :icon="isPaused ? 'VideoPlay' : 'VideoPause'"
          @click="togglePause"
        >
          {{ isPaused ? '继续' : '暂停' }}
        </el-button>
        <el-button
          v-if="canCancel"
          type="danger"
          :loading="actionLoading"
          :icon="CloseBold"
          @click="cancelTask"
        >
          取消任务
        </el-button>
        <el-button
          v-if="canDownload"
          type="primary"
          :loading="actionLoading"
          :icon="Download"
          @click="downloadResults"
        >
          下载结果
        </el-button>
        <el-button
          :icon="Close"
          @click="handleClose"
        >
          关闭
        </el-button>
      </div>
    </div>

    <!-- Overall Progress -->
    <el-card class="progress-card" shadow="never">
      <div class="overall-progress">
        <div class="progress-info">
          <span class="label">总体进度</span>
          <span class="count">{{ completedCount }} / {{ totalCount }}</span>
          <span class="percentage">{{ overallPercentage }}%</span>
        </div>
        <el-progress
          :percentage="overallPercentage"
          :status="progressStatus"
          :stroke-width="20"
          :show-text="false"
        />
        <div class="progress-stats">
          <div class="stat-item">
            <el-icon color="#67c23a"><CircleCheck /></el-icon>
            <span>成功: {{ successCount }}</span>
          </div>
          <div class="stat-item">
            <el-icon color="#f56c6c"><CircleClose /></el-icon>
            <span>失败: {{ failedCount }}</span>
          </div>
          <div class="stat-item">
            <el-icon color="#409eff"><Loading /></el-icon>
            <span>处理中: {{ processingCount }}</span>
          </div>
          <div class="stat-item">
            <el-icon color="#909399"><Clock /></el-icon>
            <span>等待中: {{ pendingCount }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Individual Items -->
    <el-card class="items-card" shadow="never">
      <template #header>
        <div class="items-header">
          <span>详细状态</span>
          <el-select
            v-model="statusFilter"
            placeholder="全部状态"
            size="small"
            style="width: 150px"
          >
            <el-option label="全部" value="" />
            <el-option label="处理中" value="processing" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
      </template>

      <div class="items-list" v-loading="loading">
        <div
          v-for="item in filteredItems"
          :key="item.requirement_id"
          class="item-row"
          :class="`status-${item.status}`"
        >
          <!-- Status Icon -->
          <div class="item-status">
            <el-icon v-if="item.status === 'success'" color="#67c23a" size="20">
              <CircleCheck />
            </el-icon>
            <el-icon v-else-if="item.status === 'failed'" color="#f56c6c" size="20">
              <CircleClose />
            </el-icon>
            <el-icon v-else-if="item.status === 'processing'" color="#409eff" size="20" class="rotating">
              <Loading />
            </el-icon>
            <el-icon v-else color="#909399" size="20">
              <Clock />
            </el-icon>
          </div>

          <!-- Item Info -->
          <div class="item-info">
            <div class="item-name">{{ item.requirement_name || item.requirement_id }}</div>
            <div class="item-id">{{ item.requirement_id }}</div>
          </div>

          <!-- Progress -->
          <div class="item-progress" v-if="item.status === 'processing'">
            <el-progress
              :percentage="item.progress || 0"
              :stroke-width="6"
              :show-text="true"
              style="width: 150px"
            />
          </div>

          <!-- Result Summary -->
          <div class="item-result" v-if="item.status === 'success'">
            <el-tag size="small" type="success">
              {{ item.matches_count || 0 }} 个匹配
            </el-tag>
          </div>

          <!-- Error Message -->
          <div class="item-error" v-if="item.status === 'failed'">
            <el-text type="danger" size="small">{{ item.error || '分析失败' }}</el-text>
          </div>

          <!-- Actions -->
          <div class="item-actions">
            <el-button
              v-if="item.status === 'success'"
              link
              type="primary"
              size="small"
              @click="viewResult(item)"
            >
              查看结果
            </el-button>
            <el-button
              v-if="item.status === 'failed'"
              link
              type="primary"
              size="small"
              @click="retryItem(item)"
            >
              重试
            </el-button>
          </div>
        </div>

        <el-empty
          v-if="filteredItems.length === 0"
          description="暂无数据"
          :image-size="80"
        />
      </div>
    </el-card>

    <!-- Time Info -->
    <div class="time-info">
      <el-text size="small" type="info">
        <el-icon><Timer /></el-icon>
        开始时间: {{ formatTime(startTime) }}
        <span v-if="elapsedTime"> | 已用时: {{ elapsedTime }}</span>
        <span v-if="estimatedTime && !isComplete"> | 预计剩余: {{ estimatedTime }}</span>
      </el-text>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Loading,
  CloseBold,
  Download,
  Close,
  CircleCheck,
  CircleClose,
  Clock,
  Timer
} from '@element-plus/icons-vue'

// Props
interface BatchItem {
  requirement_id: string
  requirement_name?: string
  status: 'pending' | 'processing' | 'success' | 'failed'
  progress?: number
  matches_count?: number
  error?: string
  result?: any
}

interface Props {
  taskId?: string
  items?: BatchItem[]
  startTime?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 2000
})

// Emits
const emit = defineEmits<{
  close: []
  'view-result': [item: BatchItem]
  'retry-item': [item: BatchItem]
  'pause': []
  'resume': []
  'cancel': []
  'download': []
}>()

// State
const loading = ref(false)
const actionLoading = ref(false)
const isPaused = ref(false)
const statusFilter = ref('')
const items = ref<BatchItem[]>(props.items || [])
const startTime = ref<string>(props.startTime || new Date().toISOString())
let refreshTimer: number | null = null

// Computed
const totalCount = computed(() => items.value.length)

const completedCount = computed(() =>
  items.value.filter(item => item.status === 'success' || item.status === 'failed').length
)

const successCount = computed(() =>
  items.value.filter(item => item.status === 'success').length
)

const failedCount = computed(() =>
  items.value.filter(item => item.status === 'failed').length
)

const processingCount = computed(() =>
  items.value.filter(item => item.status === 'processing').length
)

const pendingCount = computed(() =>
  items.value.filter(item => item.status === 'pending').length
)

const overallPercentage = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((completedCount.value / totalCount.value) * 100)
})

const progressStatus = computed(() => {
  if (failedCount.value > 0 && completedCount.value === totalCount.value) {
    return 'exception'
  }
  if (completedCount.value === totalCount.value && totalCount.value > 0) {
    return 'success'
  }
  return undefined
})

const isComplete = computed(() =>
  completedCount.value === totalCount.value && totalCount.value > 0
)

const canPause = computed(() =>
  processingCount.value > 0 || pendingCount.value > 0
)

const canCancel = computed(() =>
  !isComplete.value
)

const canDownload = computed(() =>
  successCount.value > 0
)

const filteredItems = computed(() => {
  if (!statusFilter.value) return items.value
  return items.value.filter(item => item.status === statusFilter.value)
})

const elapsedTime = computed(() => {
  if (!startTime.value) return ''
  const start = new Date(startTime.value).getTime()
  const now = Date.now()
  const seconds = Math.floor((now - start) / 1000)
  return formatDuration(seconds)
})

const estimatedTime = computed(() => {
  if (completedCount.value === 0 || isComplete.value) return ''
  const avgTimePerItem = Date.now() - new Date(startTime.value).getTime() / completedCount.value
  const remainingItems = totalCount.value - completedCount.value
  const estimatedMs = avgTimePerItem * remainingItems
  return formatDuration(Math.floor(estimatedMs / 1000))
})

// Methods
const formatDuration = (seconds: number) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}小时${minutes}分`
}

const formatTime = (timeStr?: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const togglePause = async () => {
  actionLoading.value = true
  try {
    if (isPaused.value) {
      emit('resume')
      ElMessage.success('任务已继续')
      isPaused.value = false
    } else {
      emit('pause')
      ElMessage.info('任务已暂停')
      isPaused.value = true
    }
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    actionLoading.value = false
  }
}

const cancelTask = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消当前任务吗？已完成的处理结果将被保留。',
      '确认取消',
      {
        confirmButtonText: '取消任务',
        cancelButtonText: '继续执行',
        type: 'warning'
      }
    )

    actionLoading.value = true
    emit('cancel')
    ElMessage.success('任务已取消')
    stopAutoRefresh()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    actionLoading.value = false
  }
}

const downloadResults = () => {
  emit('download')
}

const viewResult = (item: BatchItem) => {
  emit('view-result', item)
}

const retryItem = (item: BatchItem) => {
  emit('retry-item', item)
}

const handleClose = () => {
  if (!isComplete.value && processingCount.value > 0) {
    ElMessageBox.confirm(
      '任务仍在进行中，确定要关闭吗？',
      '确认关闭',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      emit('close')
    }).catch(() => {
      // User cancelled
    })
  } else {
    emit('close')
  }
}

const startAutoRefresh = () => {
  if (!props.autoRefresh || !props.taskId) return

  refreshTimer = window.setInterval(async () => {
    if (isPaused.value || isComplete.value) return

    try {
      // Fetch status from API
      // TODO: Implement API call
      // const response = await fetchBatchStatus(props.taskId)
      // items.value = response.items
    } catch (error) {
      console.error('Failed to refresh status:', error)
    }
  }, props.refreshInterval)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const updateItems = (newItems: BatchItem[]) => {
  items.value = newItems
}

// Lifecycle
onMounted(() => {
  startAutoRefresh()
})

onBeforeUnmount(() => {
  stopAutoRefresh()
})

// Expose methods
defineExpose({
  updateItems,
  stopAutoRefresh,
  startAutoRefresh
})
</script>

<style scoped>
.batch-analysis-progress {
  padding: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.progress-card {
  margin-bottom: 20px;
}

.overall-progress {
  padding: 10px 0;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.progress-info .label {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.progress-info .count {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}

.progress-info .percentage {
  font-size: 20px;
  font-weight: 600;
  color: #67c23a;
  margin-left: auto;
}

.progress-stats {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #606266;
}

.items-card {
  margin-bottom: 20px;
}

.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.items-list {
  max-height: 500px;
  overflow-y: auto;
}

.item-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  transition: background-color 0.2s;
}

.item-row:hover {
  background-color: #f5f7fa;
}

.item-row:last-child {
  border-bottom: none;
}

.item-status {
  flex-shrink: 0;
  width: 32px;
  display: flex;
  justify-content: center;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-id {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

.item-progress {
  flex-shrink: 0;
}

.item-result {
  flex-shrink: 0;
}

.item-error {
  flex-shrink: 0;
  max-width: 200px;
}

.item-actions {
  flex-shrink: 0;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.time-info {
  text-align: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* Scrollbar styling */
.items-list::-webkit-scrollbar {
  width: 6px;
}

.items-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.items-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.items-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
