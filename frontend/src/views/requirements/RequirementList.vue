<template>
  <div class="requirement-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>需求列表</h2>
          <el-button type="primary" @click="goToCreate">
            <el-icon><Plus /></el-icon>
            创建需求
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="fetchRequirements">
            <el-option label="全部" value="" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部" clearable @change="fetchRequirements">
            <el-option label="全部" value="" />
            <el-option label="文本" value="text" />
            <el-option label="文件" value="file" />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 需求列表 -->
      <el-table
        v-loading="loading"
        :data="requirements"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="title" label="需求名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="id" label="ID" width="220" show-overflow-tooltip />
        <el-table-column prop="requirement_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.requirement_type === 'text' ? 'success' : 'info'" size="small">
              {{ row.requirement_type === 'text' ? '文本' : '文件' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_file_name" label="来源文件" min-width="150">
          <template #default="{ row }">
            {{ row.source_file_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="items_count" label="需求数量" width="120" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="showDetailDialog(row)"
            >
              查看详情
            </el-button>
            <el-button
              type="success"
              size="small"
              link
              @click="goToMatching(row)"
            >
              匹配分析
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="deleteRequirement(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchRequirements"
        @current-change="fetchRequirements"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentRequirement?.title || '需求详情'"
      width="800px"
    >
      <el-descriptions :column="2" border v-if="currentRequirement">
        <el-descriptions-item label="需求名称">
          {{ currentRequirement.title || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="currentRequirement.requirement_type === 'text' ? 'success' : 'info'" size="small">
            {{ currentRequirement.requirement_type === 'text' ? '文本' : '文件' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentRequirement.status)" size="small">
            {{ getStatusText(currentRequirement.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="需求数量">
          {{ currentRequirement.items_count }} 项
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ currentRequirement.created_by || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(currentRequirement.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="来源文件" :span="2">
          {{ currentRequirement.source_file_name || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">需求文本</el-divider>
      <div class="requirement-text-box">
        <pre>{{ currentRequirement?.requirement_text || '-' }}</pre>
      </div>

      <el-divider content-position="left">需求项列表</el-divider>
      <el-table :data="requirementItems" border max-height="300" size="small">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="item_text" label="需求内容" show-overflow-tooltip />
        <el-table-column prop="item_order" label="序号" width="80" />
      </el-table>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleGoToMatchingFromDialog">
          <el-icon><Connection /></el-icon>
          前往匹配分析
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection } from '@element-plus/icons-vue'
import axios from 'axios'
import dayjs from 'dayjs'

const router = useRouter()

// 状态
const loading = ref(false)
const requirements = ref<any[]>([])

// 筛选条件
const filters = ref({
  status: '',
  type: ''
})

// 分页
const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0
})

// 详情对话框
const detailDialogVisible = ref(false)
const currentRequirement = ref<any>(null)
const requirementItems = ref<any[]>([])

// 获取需求列表
const fetchRequirements = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/requirements/', {
      params: {
        page: pagination.value.page,
        page_size: pagination.value.pageSize,
        status: filters.value.status || undefined,
        requirement_type: filters.value.type || undefined
      }
    })

    requirements.value = response.data.results || response.data
    pagination.value.total = response.data.count || response.data.length
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取需求列表失败')
  } finally {
    loading.value = false
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, any> = {
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

// 格式化日期
const formatDate = (date: string) => {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-'
}

// 跳转到创建页面
const goToCreate = () => {
  router.push('/requirements/create')
}

// 显示详情对话框
const showDetailDialog = async (row: any) => {
  try {
    const response = await axios.get(`/api/v1/requirements/${row.id}/`)
    currentRequirement.value = response.data
    requirementItems.value = response.data.items || []
    detailDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取需求详情失败')
  }
}

// 前往匹配分析
const goToMatching = (row: any) => {
  router.push(`/matching/results/${row.id}`)
}

// 从对话框前往匹配分析
const handleGoToMatchingFromDialog = () => {
  detailDialogVisible.value = false
  if (currentRequirement.value) {
    router.push(`/matching/results/${currentRequirement.value.id}`)
  }
}

// 删除需求
const deleteRequirement = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个需求吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.delete(`/api/v1/requirements/${row.id}/`)
    ElMessage.success('删除成功')
    fetchRequirements()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchRequirements()
})
</script>

<style scoped>
.requirement-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.filter-form {
  margin-bottom: 20px;
}

.requirement-text-box {
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  margin: 12px 0;
}

.requirement-text-box pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', Courier, monospace;
  font-size: 14px;
  color: #303133;
}
</style>
